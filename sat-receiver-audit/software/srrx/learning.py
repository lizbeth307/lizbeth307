"""User-annotated spectrum shapes: real few-shot CPU training, no IQ/decoding.

An annotation is a contiguous frequency-bin box in one spectrum frame. It is
not a temporal waterfall patch and cannot identify a transmitter or protocol.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import tempfile
import uuid

from .scope_policy import ScopeLatch, scope_check
from .spectrum import mask_frame, validate_frame

LABELS = ("unknown_energy", "analog_broadcast", "digital_broadcast",
          "weather_satellite", "amateur_digital", "voice_spectrogram")
# unknown_energy is also the OOD outcome; it may be annotated but never fitted as a class.
TRAINABLE_LABELS = LABELS[1:]
POLICY = "spectrum_only_safe_labels_v1"
FEATURE_VERSION, FEATURE_DIMENSION = "relative_shape_v1", 36
MAX_ANNOTATIONS, MAX_TOTAL_BINS, MAX_JSON_BYTES = 2000, 1048576, 64 * 1024 * 1024
MIN_PATCH_BINS, MAX_PATCH_BINS = 8, 4096


class LearningError(ValueError):
    pass


def _finite(value):
    return type(value) in (float, int) and math.isfinite(value)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _hash(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _seal(value):
    result = copy.deepcopy(value)
    result.pop("sha256", None)
    result["sha256"] = _hash(result)
    return result


def _check_seal(value):
    if not isinstance(value, dict) or value.get("sha256") != _seal(value)["sha256"]:
        raise LearningError("JSON integrity checksum mismatch")


def _keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise LearningError("Unexpected or missing fields")


def _utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _timestamp(value):
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise LearningError("UTC timestamp required") from None


def _digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _patch(frame, start_bin, end_bin):
    # Reapply mandatory masks even if an input file claims every bin valid.
    return _slice(validate_frame(mask_frame(frame)), start_bin, end_bin)


def _slice(checked, start_bin, end_bin):
    # Only for a frame just produced by, or proven equal to, validate_frame(mask_frame()).
    if (type(start_bin) is not int or type(end_bin) is not int or
            not 0 <= start_bin < end_bin <= checked["fft_size"] or
            not MIN_PATCH_BINS <= end_bin - start_bin <= MAX_PATCH_BINS):
        raise LearningError("Annotation must select 8..4096 consecutive bins, end exclusive")
    valid = checked["valid"][start_bin:end_bin]
    power = checked["power_dbfs"][start_bin:end_bin]
    if not all(valid) or any(value is None for value in power):
        raise LearningError("Annotation intersects a caller-invalid or mandatory-masked bin")
    return checked, power


def _quantile(values, fraction):
    values = sorted(values)
    position = (len(values) - 1) * fraction
    left = int(position)
    right = min(left + 1, len(values) - 1)
    return values[left] + (values[right] - values[left]) * (position - left)


def _features(power):
    """36 dimensionless shape features, no absolute frequency or level."""
    if not power or any(not _finite(x) for x in power):
        raise LearningError("Finite spectral power values required")
    floor, top = _quantile(power, .1), _quantile(power, .9)
    scale = max(1.0, top - floor)
    levels = [max(0.0, min(2.0, (value - floor) / scale)) / 2.0 for value in power]
    shape = []
    for index in range(32):
        position = index * (len(levels) - 1) / 31
        left = int(position)
        right = min(left + 1, len(levels) - 1)
        shape.append(levels[left] + (levels[right] - levels[left]) * (position - left))
    mean = sum(levels) / len(levels)
    occupancy = sum(x > .25 for x in levels) / len(levels)
    roughness = sum(abs(a - b) for a, b in zip(levels, levels[1:])) / (len(levels) - 1)
    variance = sum((x - mean) ** 2 for x in levels) / len(levels)
    return [round(x, 12) for x in shape + [mean, occupancy, roughness, math.sqrt(variance)]]


def extract_features(frame, start_bin, end_bin):
    _, power = _patch(frame, start_bin, end_bin)
    return _features(power)


def empty_dataset():
    return _seal({"schema_version": 1, "kind": "srrx_spectrum_annotations", "policy": POLICY,
                  "created_at_utc": _utc(), "frames": {}, "annotations": []})


def _record_id(record):
    return _hash({k: v for k, v in record.items() if k not in ("id", "created_at_utc")})


def validate_dataset(dataset):
    _keys(dataset, ("schema_version", "kind", "policy", "created_at_utc", "frames", "annotations", "sha256"))
    _check_seal(dataset)
    if type(dataset["schema_version"]) is not int or dataset["schema_version"] != 1 or dataset["kind"] != "srrx_spectrum_annotations" or dataset["policy"] != POLICY:
        raise LearningError("Unsupported annotation schema/policy")
    _timestamp(dataset["created_at_utc"])
    frames, annotations = dataset["frames"], dataset["annotations"]
    if not isinstance(frames, dict) or not isinstance(annotations, list) or len(annotations) > MAX_ANNOTATIONS:
        raise LearningError("Annotation dataset exceeds limits")
    if len(frames) > MAX_ANNOTATIONS:
        raise LearningError("Too many spectrum frames")
    total = 0
    for digest, frame in frames.items():
        # A tampered file cannot recover or use excluded bins at training time.
        canonical = validate_frame(mask_frame(frame))
        if canonical != frame or _hash(canonical) != digest:
            raise LearningError("Stored spectrum is not canonically masked or its hash changed")
        total += canonical["fft_size"]
        if total > MAX_TOTAL_BINS:
            raise LearningError("Dataset spectrum-bin limit exceeded")
    seen, patch_hashes, used_frames, frame_groups, intervals = set(), set(), set(), {}, {}
    for record in annotations:
        _keys(record, ("id", "frame_sha256", "group_sha256", "start_bin", "end_bin", "label",
                       "annotation_origin", "created_at_utc", "feature_sha256"))
        if record["label"] not in LABELS or record["annotation_origin"] != "explicit_user":
            raise LearningError("Only allowlisted, explicitly user-annotated labels are accepted")
        _timestamp(record["created_at_utc"])
        if not _digest(record["group_sha256"]) or record["frame_sha256"] not in frames:
            raise LearningError("Invalid anonymous capture group or frame reference")
        frame_hash, group = record["frame_sha256"], record["group_sha256"]
        # Every stored frame was re-masked and compared above; do not redo it per box.
        _, power = _slice(frames[frame_hash], record["start_bin"], record["end_bin"])
        feature_hash = _hash([round(x, 6) for x in _features(power)])
        if feature_hash != record["feature_sha256"] or record["id"] != _record_id(record) or record["id"] in seen:
            raise LearningError("Changed or duplicate annotation")
        # Same patch copied with a gain change must not become independent data.
        if feature_hash in patch_hashes:
            raise LearningError("Duplicate normalized spectral patch")
        if frame_hash in frame_groups and frame_groups[frame_hash] != group:
            raise LearningError("One spectrum frame cannot cross capture groups")
        for start, end in intervals.get(frame_hash, []):
            if record["start_bin"] < end and start < record["end_bin"]:
                raise LearningError("Overlapping annotation boxes are not independent")
        intervals.setdefault(frame_hash, []).append((record["start_bin"], record["end_bin"]))
        frame_groups[frame_hash] = group
        used_frames.add(frame_hash)
        seen.add(record["id"])
        patch_hashes.add(feature_hash)
    if used_frames != set(frames):
        raise LearningError("Unreferenced spectrum frames are not allowed")
    return copy.deepcopy(dataset)


def _box_spans(checked, start_bin, end_bin):
    """RF spans a box covers; bin 0 also carries the wrapped upper half-bin.

    As spectrum._checked_frame: the even-FFT Nyquist bin 0 holds energy from
    [center + rate/2 - width/2, center + rate/2] too, so a box from bin 0 is
    checked on both spans.
    """
    center, rate = checked["center_hz"], checked["sample_rate_hz"]
    width = rate / checked["fft_size"]
    spans = [(center + checked["relative_frequency_hz"][start_bin] - width / 2,
              center + checked["relative_frequency_hz"][end_bin - 1] + width / 2)]
    if start_bin == 0:
        spans.append((center + rate / 2 - width / 2, center + rate / 2))
    return spans


def _scope_guard(checked, start_bin, end_bin, scope, message="Annotation span is out of scope", *, always=True):
    """Only adds refusals: masked-band stop (unless always=False), plus the session Artemis latch if given."""
    if scope is not None and not isinstance(scope, ScopeLatch):
        raise LearningError("scope must be the session ScopeLatch")
    try:
        stopped = any((always and scope_check(*span)["stop"]) or
                      (scope is not None and scope.permits("label", span) is not True)
                      for span in _box_spans(checked, start_bin, end_bin))
    except ValueError:
        stopped = True
    if stopped:
        raise LearningError(message)  # no frequency in the message


def annotate(dataset, frame, start_bin, end_bin, label, *, group_id, user_confirmed=False, scope=None):
    """Return a new dataset; calling code must require a deliberate user action.

    scope is the session scope_policy.ScopeLatch; an Artemis stop on the box
    span refuses the label. Without it the masked-band stop still applies.
    """
    if user_confirmed is not True or label not in LABELS:
        raise LearningError("Explicit user confirmation and an allowlisted label are required")
    try:
        anonymous = uuid.UUID(str(group_id)).hex
    except (ValueError, AttributeError, TypeError):
        raise LearningError("group_id must be an anonymous UUID, never an emitter identifier") from None
    result = validate_dataset(dataset)
    checked, power = _patch(frame, start_bin, end_bin)
    _scope_guard(checked, start_bin, end_bin, scope)
    digest = _hash(checked)
    result["frames"][digest] = checked
    record = {"frame_sha256": digest, "group_sha256": _hash(anonymous),
              "start_bin": start_bin, "end_bin": end_bin, "label": label,
              "annotation_origin": "explicit_user", "created_at_utc": _utc(),
              "feature_sha256": _hash([round(x, 6) for x in _features(power)])}
    record["id"] = _record_id(record)
    result["annotations"].append(record)
    return validate_dataset(_seal(result))


def _atomic_json(path, value):
    data = _canonical(value) + b"\n"
    if len(data) > MAX_JSON_BYTES:
        raise LearningError("JSON file-size limit exceeded")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".srrx-", delete=False) as stream:
            temporary = stream.name
            os.chmod(temporary, 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        if os.name != "nt":  # Windows has no directory fsync; file data was fsynced above.
            try:
                directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            except OSError as error:
                raise OSError(error.errno, "File replaced, but directory fsync failed; durability not confirmed") from error
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def _read_json(path):
    with open(path, "rb") as stream:
        data = stream.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise LearningError("JSON file-size limit exceeded")
    def reject(value):
        raise LearningError("Non-finite JSON constant")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise LearningError("Duplicate JSON object key")
            result[key] = value
        return result
    try:
        return json.loads(data, parse_constant=reject, object_pairs_hook=unique)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise LearningError("Invalid JSON") from error


def save_dataset(path, dataset):
    _atomic_json(path, validate_dataset(dataset))


def load_dataset(path):
    return validate_dataset(_read_json(path))


def _distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / FEATURE_DIMENSION)


def _predict_features(model, feature, distances=None):
    labels = model["labels"]
    distances = distances if distances is not None else [_distance(feature, model["centroids"][label]) for label in labels]
    ranked = sorted(zip(distances, labels))
    best, label = ranked[0]
    second = ranked[1][0]
    radius = model["radii"][label]
    margin = max(0.0, (second - best) / max(second, 1e-12))
    closeness = max(0.0, 1.0 - best / (1.5 * radius))
    ood = best > radius or margin < model["min_margin"]
    return {"label": "unknown_energy" if ood else label, "nearest_label": label,
            "confidence": 0.0 if ood else round(closeness * (.5 + .5 * margin), 6),
            "distance": round(best, 9), "ood": ood}


def train(dataset, *, seed=0, validation_fraction=.25, scope=None):
    """Fit and hold-out check a model. scope (the session ScopeLatch) must permit
    'label' on every trainable box span, so a latched span never feeds a model.
    """
    dataset = validate_dataset(dataset)
    if type(seed) is not int or not _finite(validation_fraction) or not 0 < validation_fraction <= .5:
        raise LearningError("A deterministic integer seed and 0<holdout<=0.5 are required")
    # unknown_energy boxes stay in the dataset but are not a fitted class: an OOD
    # rejection must never be scored as a correct "unknown_energy" match.
    records = [record for record in dataset["annotations"] if record["label"] in TRAINABLE_LABELS]
    if scope is not None:
        # validate_dataset re-masked every frame, and annotate ran the masked-band check.
        for record in records:
            _scope_guard(dataset["frames"][record["frame_sha256"]], record["start_bin"], record["end_bin"],
                         scope, "Training annotation span is out of scope", always=False)
    labels = sorted({record["label"] for record in records})
    if len(labels) < 2:
        raise LearningError("At least two allowlisted trainable classes (not unknown_energy) are required")
    groups = {}
    label_groups = {label: set() for label in labels}
    for record in records:
        groups.setdefault(record["group_sha256"], set()).add(record["label"])
        label_groups[record["label"]].add(record["group_sha256"])
    if any(len(owned) < 2 for owned in label_groups.values()):
        raise LearningError("Every class needs at least two independent capture groups for grouped holdout")
    ordered = sorted(groups)
    random.Random(seed).shuffle(ordered)
    validation_groups = set()
    for label in labels:
        if label_groups[label] & validation_groups:
            continue
        candidates = [group for group in ordered if group in label_groups[label] and
                      all(len(label_groups[other] - validation_groups - {group}) >= 1 for other in groups[group])]
        if not candidates:
            raise LearningError("Capture groups cannot be split without class leakage; collect more independent groups")
        validation_groups.add(candidates[0])
    target = max(len(validation_groups), math.ceil(len(groups) * validation_fraction))
    for group in ordered:
        if len(validation_groups) >= target:
            break
        if all(len(label_groups[label] - validation_groups - {group}) >= 1 for label in groups[group]):
            validation_groups.add(group)
    train_records = [record for record in records if record["group_sha256"] not in validation_groups]
    validation_records = [record for record in records if record["group_sha256"] in validation_groups]
    # validate_dataset just re-masked and compared every stored frame.
    vectors = {record["id"]: _features(_slice(dataset["frames"][record["frame_sha256"]], record["start_bin"], record["end_bin"])[1])
               for record in records}
    centroids, radii = {}, {}
    for label in labels:
        points = [vectors[record["id"]] for record in train_records if record["label"] == label]
        centroids[label] = [sum(row[index] for row in points) / len(points) for index in range(FEATURE_DIMENSION)]
        radii[label] = max(.08, max(_distance(point, centroids[label]) for point in points) * 1.5)
    model = {"schema_version": 1, "kind": "srrx_nearest_centroid", "policy": POLICY,
             "feature_version": FEATURE_VERSION, "feature_dimension": FEATURE_DIMENSION,
             "labels": labels, "centroids": centroids, "radii": radii, "min_margin": .1,
             "provenance": {"trained_at_utc": _utc(), "dataset_sha256": dataset["sha256"],
                "algorithm": "nearest_centroid_euclidean_rms", "seed": seed,
                "validation_fraction": validation_fraction,
                "train_annotation_ids": [r["id"] for r in train_records],
                "validation_annotation_ids": [r["id"] for r in validation_records],
                "train_groups": sorted(set(groups) - validation_groups), "validation_groups": sorted(validation_groups),
                "source_counts": {source: sum(dataset["frames"][r["frame_sha256"]]["source"] == source for r in train_records)
                                  for source in ("SIMULATION", "HARDWARE")},
                "class_train_counts": {label: sum(r["label"] == label for r in train_records) for label in labels}},
             "validation": {}}
    correct, rejected = 0, 0
    confusion = {label: {other: 0 for other in set(labels) | {"unknown_energy"}} for label in labels}
    for record in validation_records:
        result = _predict_features(model, vectors[record["id"]])
        correct += result["label"] == record["label"]
        rejected += result["ood"]
        confusion[record["label"]][result["label"]] += 1
    model["validation"] = {"samples": len(validation_records), "correct": correct, "ood": rejected,
                           "accuracy": correct / len(validation_records), "confusion": confusion,
                           "scope": "held_out_capture_groups_only_not_field_accuracy"}
    return validate_model(_seal(model))


train_model = train


def validate_model(model):
    _keys(model, ("schema_version", "kind", "policy", "feature_version", "feature_dimension", "labels",
                  "centroids", "radii", "min_margin", "provenance", "validation", "sha256"))
    _check_seal(model)
    if (type(model["schema_version"]) is not int or model["schema_version"] != 1 or model["kind"] != "srrx_nearest_centroid" or model["policy"] != POLICY or
            model["feature_version"] != FEATURE_VERSION or type(model["feature_dimension"]) is not int or model["feature_dimension"] != FEATURE_DIMENSION):
        raise LearningError("Unsupported model format")
    labels = model["labels"]
    if not isinstance(labels, list) or len(labels) < 2 or any(type(x) is not str or x not in TRAINABLE_LABELS for x in labels) or len(labels) != len(set(labels)):
        raise LearningError("Model contains prohibited or duplicate labels")
    if not isinstance(model["centroids"], dict) or not isinstance(model["radii"], dict):
        raise LearningError("Centroids and radii must be JSON objects")
    if set(model["centroids"]) != set(labels) or set(model["radii"]) != set(labels):
        raise LearningError("Centroid classes do not match model labels")
    for label in labels:
        point, radius = model["centroids"][label], model["radii"][label]
        if not isinstance(point, list) or len(point) != FEATURE_DIMENSION or any(not _finite(x) or not 0 <= x <= 1 for x in point):
            raise LearningError("Invalid centroid feature vector")
        if not _finite(radius) or not 0 < radius <= 2:
            raise LearningError("Invalid OOD radius")
    if not _finite(model["min_margin"]) or not 0 <= model["min_margin"] <= 1:
        raise LearningError("Invalid ambiguity margin")
    provenance = model["provenance"]
    _keys(provenance, ("trained_at_utc", "dataset_sha256", "algorithm", "seed", "validation_fraction",
                       "train_annotation_ids", "validation_annotation_ids", "train_groups", "validation_groups",
                       "source_counts", "class_train_counts"))
    _timestamp(provenance["trained_at_utc"])
    if (not _digest(provenance["dataset_sha256"]) or provenance["algorithm"] != "nearest_centroid_euclidean_rms" or
            type(provenance["seed"]) is not int or not _finite(provenance["validation_fraction"]) or
            not 0 < provenance["validation_fraction"] <= .5):
        raise LearningError("Missing actual training provenance")
    for field in ("train_annotation_ids", "validation_annotation_ids", "train_groups", "validation_groups"):
        entries = provenance[field]
        if not isinstance(entries, list) or not entries or len(entries) > MAX_ANNOTATIONS or any(not _digest(x) for x in entries) or len(entries) != len(set(entries)):
            raise LearningError("Invalid training/validation provenance")
    if (set(provenance["train_annotation_ids"]) & set(provenance["validation_annotation_ids"]) or
            set(provenance["train_groups"]) & set(provenance["validation_groups"])):
        raise LearningError("Training/validation leakage")
    counts, sources = provenance["class_train_counts"], provenance["source_counts"]
    if (not isinstance(counts, dict) or not isinstance(sources, dict) or
            set(counts) != set(labels) or any(type(n) is not int or n < 1 for n in counts.values()) or
            sum(counts.values()) != len(provenance["train_annotation_ids"]) or
            set(sources) != {"SIMULATION", "HARDWARE"} or any(type(n) is not int or n < 0 for n in sources.values()) or
            sum(sources.values()) != len(provenance["train_annotation_ids"])):
        raise LearningError("Invalid actual training counts")
    metrics = model["validation"]
    _keys(metrics, ("samples", "correct", "ood", "accuracy", "confusion", "scope"))
    n = len(provenance["validation_annotation_ids"])
    if (type(metrics["samples"]) is not int or metrics["samples"] != n or type(metrics["correct"]) is not int or not 0 <= metrics["correct"] <= n or
            type(metrics["ood"]) is not int or not 0 <= metrics["ood"] <= n or
            not _finite(metrics["accuracy"]) or metrics["accuracy"] != metrics["correct"] / n or
            metrics["scope"] != "held_out_capture_groups_only_not_field_accuracy"):
        raise LearningError("Invalid validation metrics")
    confusion = metrics["confusion"]
    if not isinstance(confusion, dict) or set(confusion) != set(labels):
        raise LearningError("Invalid confusion matrix")
    if any(not isinstance(row, dict) or set(row) != set(labels) | {"unknown_energy"} or any(type(x) is not int or x < 0 for x in row.values()) for row in confusion.values()):
        raise LearningError("Invalid confusion matrix entries")
    if sum(sum(row.values()) for row in confusion.values()) != n:
        raise LearningError("Confusion matrix counts do not match validation")
    if sum(confusion[label][label] for label in labels) != metrics["correct"]:
        raise LearningError("Confusion matrix diagonal does not match validation accuracy")
    return copy.deepcopy(model)


def save_model(path, model):
    _atomic_json(path, validate_model(model))


def load_model(path):
    return validate_model(_read_json(path))


class QairtAdapter:
    """Actual optional ONNX Runtime QNN/HTP session; CPU EP fallback disabled.

    No ONNX or compiled QNN artifact is generated by this module. A separately
    qualified artifact must output RMS distances [1, number_of_labels].
    """
    def __init__(self, manifest_path, model):
        model = validate_model(model)
        manifest_path = Path(manifest_path)
        manifest = _read_json(manifest_path)
        _keys(manifest, ("schema_version", "kind", "model_sha256", "feature_version", "labels",
                         "artifact_path", "artifact_sha256", "backend_path", "backend_sha256"))
        if (manifest["schema_version"] != 1 or manifest["kind"] != "srrx_qairt_htp_distances" or
                manifest["model_sha256"] != model["sha256"] or manifest["feature_version"] != FEATURE_VERSION or
                manifest["labels"] != model["labels"]):
            raise LearningError("NPU manifest does not match this trained model")
        paths = {}
        for key in ("artifact", "backend"):
            raw = manifest[key + "_path"]
            if not isinstance(raw, str) or not raw or len(raw) > 4096:
                raise LearningError("Invalid explicit NPU artifact path")
            path = Path(raw)
            path = path if path.is_absolute() else manifest_path.parent / path
            checksum = hashlib.sha256()
            if path.stat().st_size > 1024 ** 3:
                raise LearningError("NPU artifact/backend file-size limit exceeded")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    checksum.update(chunk)
            if checksum.hexdigest() != manifest[key + "_sha256"]:
                raise LearningError("NPU artifact/backend SHA256 mismatch")
            paths[key] = path.resolve()
        if paths["backend"].name not in ("libQnnHtp.so", "QnnHtp.dll"):
            raise LearningError("Only explicit QNN HTP backend is accepted")
        from .model_export import load_ort_private
        ort = load_ort_private()
        if "QNNExecutionProvider" not in ort.get_available_providers():
            raise LearningError("Installed runtime has no QNNExecutionProvider")
        options = ort.SessionOptions()
        options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        session = ort.InferenceSession(str(paths["artifact"]), sess_options=options,
                                      providers=["QNNExecutionProvider"],
                                      provider_options=[{"backend_path": str(paths["backend"])}])
        if not session.get_providers() or session.get_providers()[0] != "QNNExecutionProvider":
            raise LearningError("QNN provider not active")
        if (len(session.get_inputs()) != 1 or session.get_inputs()[0].shape != [1, FEATURE_DIMENSION] or
                session.get_inputs()[0].type != "tensor(float)" or len(session.get_outputs()) != 1 or
                session.get_outputs()[0].shape != [1, len(model["labels"])]):
            raise LearningError("NPU artifact has incompatible feature/distance tensors")
        self.session, self.model_sha256 = session, model["sha256"]

    def __call__(self, feature):
        import numpy as np
        values = np.asarray([feature], dtype=np.float32)
        result = self.session.run(None, {self.session.get_inputs()[0].name: values})[0]
        return [float(x) for x in result[0]]


def infer(model, frame, start_bin, end_bin, *, backend="cpu", npu_manifest=None, npu_runner=None, scope=None):
    """Classify one box. With scope (the session ScopeLatch) a stopped span gives no label."""
    model = validate_model(model)
    if backend not in ("cpu", "npu", "auto"):
        raise LearningError("Backend must be cpu, npu, or auto")
    checked, power = _patch(frame, start_bin, end_bin)
    if scope is not None:
        _scope_guard(checked, start_bin, end_bin, scope, "Classification span is out of scope")
    feature = _features(power)
    distances = [_distance(feature, model["centroids"][label]) for label in model["labels"]]
    actual_backend = "CPU"
    npu = {"available": False, "reason": "not_requested"}
    if backend != "cpu":
        try:
            adapter = npu_runner if npu_runner is not None else QairtAdapter(npu_manifest, model) if npu_manifest else None
            if not isinstance(adapter, QairtAdapter) or not callable(adapter) or adapter.model_sha256 != model["sha256"]:
                raise LearningError("No matching callable QAIRT/QNN HTP runtime and manifest")
            accelerated = adapter(feature)
            if (len(accelerated) != len(distances) or any(not _finite(x) or x < 0 for x in accelerated) or
                    any(abs(a - b) > .01 + .02 * abs(b) for a, b in zip(accelerated, distances))):
                raise LearningError("NPU output does not match qualified centroid distance semantics")
            # The tolerance can straddle a radius/margin threshold. The decision always
            # comes from exact CPU distances; HTP counts only if it decides identically.
            expected, observed = _predict_features(model, feature, distances), _predict_features(model, feature, accelerated)
            if any(expected[key] != observed[key] for key in ("label", "nearest_label", "ood")):
                raise LearningError("NPU label/OOD decision disagrees with the CPU control check")
            actual_backend, npu = "QAIRT_QNN_HTP", {"available": True, "reason": "runtime_executed_cpu_ep_fallback_disabled"}
        except Exception as error:
            npu = {"available": False, "reason": type(error).__name__ + ": " + str(error)[:240]}
    result = _predict_features(model, feature, distances)
    result.update(backend=actual_backend, npu=npu, model_sha256=model["sha256"],
                  source=frame["source"], confidence_kind="heuristic_not_calibrated_probability")
    return result


def export_interchange(path, model):
    """Portable trained JSON; deliberately not an ONNX/QNN compiled model."""
    save_model(path, model)


def _demo_frame(index, family):
    rng, size = random.Random(index + family * 1000), 256
    power = []
    for index in range(size):
        x = (index - (size - 1) / 2) / (size / 2)
        if family == 0:
            signal = 35 * math.exp(-((x / .16) ** 2))
        elif family == 1:
            signal = 27 if abs(x) < .58 else 0
        else:
            signal = sum(25 * math.exp(-(((x - center) / .035) ** 2)) for center in (-.65, -.25, .25, .65))
        power.append(-100 + signal + rng.uniform(-.5, .5))
    # Toy spectral shapes only; these labels are demonstration annotations,
    # not a claim that the mathematical shapes identify real protocols.
    return {"v": 1, "kind": "spectrum", "center_hz": 137500000.0, "sample_rate_hz": 1000000.0,
            "fft_size": size, "power_dbfs": power, "valid": [True] * size,
            "relative_frequency_hz": [(i - size // 2) * 1000000.0 / size for i in range(size)],
            "source": "SIMULATION", "sample_count": size}


def demo(directory):
    directory = Path(directory)
    dataset = empty_dataset()
    for family, label in enumerate(("analog_broadcast", "digital_broadcast", "amateur_digital")):
        for index in range(4):
            dataset = annotate(dataset, _demo_frame(index, family), 0, 256, label,
                               group_id=uuid.UUID(int=1 + family * 100 + index), user_confirmed=True)
    model = train(dataset, seed=7)
    save_dataset(directory / "annotations.json", dataset)
    save_model(directory / "model.json", model)
    test_frame = validate_frame(mask_frame(_demo_frame(99, 0)))
    _atomic_json(directory / "example-spectrum.json", test_frame)
    result = infer(model, test_frame, 0, 256, backend="npu")
    return {"mode": "SIMULATION", "annotations": len(dataset["annotations"]),
            "validation": model["validation"], "prediction": result,
            "dataset": str(directory / "annotations.json"), "model": str(directory / "model.json")}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("demo")
    command.add_argument("--output", type=Path, required=True)
    command = sub.add_parser("annotate")
    command.add_argument("--dataset", type=Path, required=True)
    command.add_argument("--frame", type=Path, required=True)
    command.add_argument("--start", type=int, required=True)
    command.add_argument("--end", type=int, required=True)
    command.add_argument("--label", choices=LABELS, required=True)
    command.add_argument("--group", required=True, help="Anonymous capture-session UUID")
    command.add_argument("--user-confirmed", action="store_true")
    command = sub.add_parser("train")
    command.add_argument("--dataset", type=Path, required=True)
    command.add_argument("--model", type=Path, required=True)
    command.add_argument("--seed", type=int, default=0)
    command = sub.add_parser("infer")
    command.add_argument("--model", type=Path, required=True)
    command.add_argument("--frame", type=Path, required=True)
    command.add_argument("--start", type=int, required=True)
    command.add_argument("--end", type=int, required=True)
    command.add_argument("--backend", choices=("cpu", "npu", "auto"), default="cpu")
    command.add_argument("--npu-manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            result = demo(args.output)
        elif args.command == "annotate":
            dataset = load_dataset(args.dataset) if args.dataset.exists() else empty_dataset()
            dataset = annotate(dataset, _read_json(args.frame), args.start, args.end, args.label,
                               group_id=args.group, user_confirmed=args.user_confirmed)
            save_dataset(args.dataset, dataset)
            result = {"annotations": len(dataset["annotations"]), "dataset_sha256": dataset["sha256"]}
        elif args.command == "train":
            model = train(load_dataset(args.dataset), seed=args.seed)
            save_model(args.model, model)
            result = {"model_sha256": model["sha256"], "validation": model["validation"]}
        else:
            result = infer(load_model(args.model), _read_json(args.frame), args.start, args.end,
                           backend=args.backend, npu_manifest=args.npu_manifest)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"ok": False, "error": str(error)[:300]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
