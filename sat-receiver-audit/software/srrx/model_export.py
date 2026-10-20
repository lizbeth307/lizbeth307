"""Actual ONNX centroid-distance export and measured CPU/QDQ validation.

Exported/quantized ONNX is not a compiled QNN blob or an HTP qualification.
All calibration features come from the model's validated training annotations.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile

# Microsoft documents that an API call after import can miss an initialization
# event. Set the process-lifetime 1DS opt-out before any optional dependency.
# A preloaded, unguarded runtime is rejected below; this assignment cannot undo
# an event that another caller may already have emitted.
os.environ["ORT_DISABLE_TELEMETRY"] = "1"

from . import learning

MAX_ARTIFACT_BYTES = 4 * 1024 * 1024
ALLOWED_OPS = {"Sub", "Mul", "ReduceMean", "Sqrt", "Unsqueeze", "QuantizeLinear", "DequantizeLinear"}


class ExportError(ValueError):
    pass


class ExportDependencyError(ExportError):
    pass


class ExportPrivacyError(ExportDependencyError):
    pass


def _verify_ort_privacy_support():
    """Inspect installed files only, before loading any native ORT code.

    Audited primary reference: microsoft/onnxruntime docs/Privacy.md, shipped
    with ORT1.31.0 and https://github.com/microsoft/onnxruntime/blob/main/docs/Privacy.md.
    The documented pre-init variable suppresses the uploader, all 1DS events,
    and persistent identifier; disable_telemetry_events alone is insufficient.
    Unknown/legacy providers fail closed instead of guessing opt-out support.
    """
    if not sys.platform.startswith("linux"):
        raise ExportPrivacyError("ORT privacy guard is audited for Linux 1DS only; use an independently audited telemetry-free build on this platform")
    spec = importlib.util.find_spec("onnxruntime")
    if spec is None or not spec.origin:
        raise ExportDependencyError("Optional onnxruntime dependency unavailable")
    root = Path(spec.origin).parent
    privacy = root / "Privacy.md"
    try:
        with privacy.open("rb") as stream:
            documentation = stream.read(65537)
        required = (b"ORT_DISABLE_TELEMETRY=1", b"before ONNX Runtime initializes",
                    b"prevents the uploader", b"persistent device identifier")
        if len(documentation) > 65536 or any(text not in documentation for text in required):
            raise ExportPrivacyError("Installed ORT does not document the required pre-initialization 1DS opt-out")
        # Corroborate the installed binary actually includes the documented
        # environment control. Reading bytes does not import/dlopen the library.
        candidates = sorted((root / "capi").glob("onnxruntime_pybind11_state*.so"))
        needle = b"ORT_DISABLE_TELEMETRY"
        supported = False
        for binary in candidates:
            if not 0 < binary.stat().st_size <= 512 * 1024 * 1024:
                continue
            tail = b""
            with binary.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    if needle in tail + chunk:
                        supported = True
                        break
                    tail = chunk[-len(needle):]
            if supported:
                break
        if not supported:
            raise ExportPrivacyError("Installed ORT binary lacks the audited pre-init telemetry control; runtime import blocked")
    except OSError as error:
        raise ExportPrivacyError("Unable to verify installed ORT privacy controls before import") from error


def load_ort_private():
    """Import ORT with documented pre-init opt-out, then suppress API events.

    Call this instead of importing ORT directly. A runtime loaded elsewhere
    without this guard cannot be retroactively declared private.
    """
    os.environ["ORT_DISABLE_TELEMETRY"] = "1"
    preloaded = sys.modules.get("onnxruntime")
    if preloaded is not None and getattr(preloaded, "_srrx_private_import_verified", False) is not True:
        raise ExportPrivacyError("ORT was imported outside the privacy guard; restart the process before using model tools")
    if preloaded is None:
        if any(name.startswith("onnxruntime.") for name in sys.modules):
            raise ExportPrivacyError("Native ORT modules were loaded before privacy verification; restart required")
        _verify_ort_privacy_support()
    try:
        runtime = importlib.import_module("onnxruntime")
        disable = getattr(runtime, "disable_telemetry_events", None)
        if not callable(disable):
            raise ExportPrivacyError("ORT lacks the documented disable_telemetry_events API; runtime use blocked")
        disable()
        if os.environ.get("ORT_DISABLE_TELEMETRY") != "1":
            raise ExportPrivacyError("ORT telemetry opt-out changed during import; runtime use blocked")
        runtime._srrx_private_import_verified = True
        return runtime
    except ExportPrivacyError:
        raise
    except Exception as error:
        raise ExportPrivacyError("ORT import/API telemetry suppression failed; runtime use blocked") from error


def _dependencies(*, runtime=False):
    try:
        # The guarded import must precede version/provider/session queries and
        # quantization helpers, not merely precede InferenceSession creation.
        ort = load_ort_private() if runtime else None
        onnx = importlib.import_module("onnx")
        np = importlib.import_module("numpy")
        return onnx, np, ort
    except (ImportError, OSError) as error:
        raise ExportDependencyError("Optional model export dependencies unavailable; install onnx, numpy and onnxruntime in an isolated environment") from error


def dependency_status():
    try:
        onnx, np, ort = _dependencies(runtime=True)
        return {"available": True, "onnx": onnx.__version__, "onnxruntime": ort.__version__,
                "numpy": np.__version__, "providers": ort.get_available_providers(),
                "telemetry": {"disabled_before_import": True, "api_disabled": True}}
    except ExportDependencyError as error:
        return {"available": False, "error": str(error)}


def _sha256(path, limit=MAX_ARTIFACT_BYTES):
    path = Path(path)
    if not path.is_file() or not 0 < path.stat().st_size <= limit:
        raise ExportError("Artifact is missing, empty, or oversized")
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def _atomic_bytes(path, data):
    if not 0 < len(data) <= MAX_ARTIFACT_BYTES:
        raise ExportError("Artifact exceeds export size limit")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".srrx-model-", delete=False) as stream:
            temporary = stream.name
            os.chmod(temporary, 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def _metadata(model, kind):
    return {"srrx.model_sha256": model["sha256"], "srrx.feature_version": learning.FEATURE_VERSION,
            "srrx.labels": json.dumps(model["labels"], separators=(",", ":")),
            "srrx.export_kind": kind, "srrx.npu_qualified": "false"}


def _shape(value):
    return [dimension.dim_value for dimension in value.type.tensor_type.shape.dim]


def _load_bound_artifact(path, model):
    model = learning.validate_model(model)
    onnx, _, _ = _dependencies()
    digest = _sha256(path)
    try:
        proto = onnx.load_model(str(path), load_external_data=False)
    except Exception as error:
        raise ExportError("Unreadable ONNX artifact") from error
    if proto.functions or len(proto.graph.input) != 1 or len(proto.graph.output) != 1:
        raise ExportError("Artifact must be a self-contained static distance graph")
    if any(tensor.external_data or tensor.data_location == onnx.TensorProto.EXTERNAL for tensor in proto.graph.initializer):
        raise ExportError("External tensor files are not permitted")
    if any(node.domain not in ("", "ai.onnx") or node.op_type not in ALLOWED_OPS for node in proto.graph.node):
        raise ExportError("Artifact has unsupported/custom graph operations")
    if (proto.graph.input[0].name != "features" or proto.graph.output[0].name != "distances" or
            _shape(proto.graph.input[0]) != [1, learning.FEATURE_DIMENSION] or
            _shape(proto.graph.output[0]) != [1, len(model["labels"])] or
            proto.graph.input[0].type.tensor_type.elem_type != onnx.TensorProto.FLOAT or
            proto.graph.output[0].type.tensor_type.elem_type != onnx.TensorProto.FLOAT):
        raise ExportError("Artifact input/output contract mismatch")
    properties = {entry.key: entry.value for entry in proto.metadata_props}
    if properties.get("srrx.export_kind") not in ("float32", "qdq_int8"):
        raise ExportError("Unknown artifact representation")
    for name, value in _metadata(model, properties["srrx.export_kind"]).items():
        if properties.get(name) != value:
            raise ExportError("Artifact metadata does not match trained model")
    try:
        onnx.checker.check_model(proto, full_check=True)
    except Exception as error:
        raise ExportError("ONNX artifact fails graph validation") from error
    return proto, digest, properties["srrx.export_kind"]


def export_float(model, output):
    """Write a real static ONNX float32[1,36] -> RMS distances[1,C]."""
    model = learning.validate_model(model)
    onnx, np, _ = _dependencies()
    helper = onnx.helper
    centroids = np.asarray([model["centroids"][label] for label in model["labels"]], dtype=np.float32)
    nodes = [helper.make_node("Sub", ["features", "centroids"], ["delta"], name="centered_difference"),
             helper.make_node("Mul", ["delta", "delta"], ["squared"], name="squared_difference"),
             helper.make_node("ReduceMean", ["squared"], ["mean_square"], axes=[1], keepdims=0, name="mean_over_features"),
             helper.make_node("Sqrt", ["mean_square"], ["rms"], name="rms_distance"),
             helper.make_node("Unsqueeze", ["rms", "output_axis"], ["distances"], name="static_output_batch")]
    graph = helper.make_graph(nodes, "srrx_centroid_distances",
        [helper.make_tensor_value_info("features", onnx.TensorProto.FLOAT, [1, learning.FEATURE_DIMENSION])],
        [helper.make_tensor_value_info("distances", onnx.TensorProto.FLOAT, [1, len(model["labels"])])],
        [onnx.numpy_helper.from_array(centroids, "centroids"),
         onnx.numpy_helper.from_array(np.asarray([0], dtype=np.int64), "output_axis")])
    proto = helper.make_model(graph, producer_name="srrx-model-export", producer_version="1",
                              opset_imports=[helper.make_opsetid("", 13)], ir_version=8)
    helper.set_model_props(proto, _metadata(model, "float32"))
    proto = onnx.shape_inference.infer_shapes(proto, strict_mode=True)
    onnx.checker.check_model(proto, full_check=True)
    _atomic_bytes(output, proto.SerializeToString())
    return {"artifact": str(output), "artifact_sha256": _sha256(output), "model_sha256": model["sha256"],
            "format": "ONNX_FLOAT32", "input_shape": [1, learning.FEATURE_DIMENSION],
            "output_shape": [1, len(model["labels"])], "opset": 13, "ir_version": 8,
            "cpu_validated": False, "npu_qualified": False, "qnn_compiled": False}


def _dataset_features(model, dataset):
    model, dataset = learning.validate_model(model), learning.validate_dataset(dataset)
    provenance = model["provenance"]
    if dataset["sha256"] != provenance["dataset_sha256"]:
        raise ExportError("Calibration/validation dataset SHA256 does not match training")
    records = {record["id"]: record for record in dataset["annotations"]}
    train_ids, validation_ids = provenance["train_annotation_ids"], provenance["validation_annotation_ids"]
    if set(train_ids) | set(validation_ids) != set(records):
        raise ExportError("Dataset does not contain the exact recorded training/holdout annotations")
    if (set(records[identifier]["group_sha256"] for identifier in train_ids) != set(provenance["train_groups"]) or
            set(records[identifier]["group_sha256"] for identifier in validation_ids) != set(provenance["validation_groups"])):
        raise ExportError("Dataset capture groups do not match recorded split")
    sources = Counter(dataset["frames"][records[identifier]["frame_sha256"]]["source"] for identifier in train_ids)
    counts = Counter(records[identifier]["label"] for identifier in train_ids)
    if any(counts[label] != provenance["class_train_counts"][label] for label in model["labels"]) or any(sources[source] != provenance["source_counts"][source] for source in ("HARDWARE", "SIMULATION")):
        raise ExportError("Training counts do not match source annotation records")
    vectors = {identifier: learning.extract_features(dataset["frames"][record["frame_sha256"]], record["start_bin"], record["end_bin"])
               for identifier, record in records.items()}
    for label in model["labels"]:
        points = [vectors[identifier] for identifier in train_ids if records[identifier]["label"] == label]
        recomputed = [sum(point[index] for point in points) / len(points) for index in range(learning.FEATURE_DIMENSION)]
        if any(abs(actual - saved) > 1e-10 for actual, saved in zip(recomputed, model["centroids"][label])):
            raise ExportError("Model centroid does not match its recorded actual training data")
    return model, dataset, vectors, train_ids, validation_ids


def validate_cpu(artifact, model, dataset, *, atol=None, rtol=None):
    """Execute the actual ONNX artifact on held-out annotations, never calibrate."""
    model, dataset, vectors, _, validation_ids = _dataset_features(model, dataset)
    _, digest, kind = _load_bound_artifact(artifact, model)
    _, np, ort = _dependencies(runtime=True)
    atol = (0.01 if kind == "qdq_int8" else 2e-6) if atol is None else atol
    rtol = (0.02 if kind == "qdq_int8" else 2e-6) if rtol is None else rtol
    if (type(atol) not in (int, float) or type(rtol) not in (int, float) or
            not math.isfinite(atol) or not math.isfinite(rtol) or not 0 < atol <= .01 or not 0 <= rtol <= .02):
        raise ExportError("Error limits must not exceed the QAIRT adapter tolerance")
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(artifact), sess_options=options, providers=["CPUExecutionProvider"])
    if session.get_providers() != ["CPUExecutionProvider"]:
        raise ExportError("Validation must execute on explicit CPUExecutionProvider")
    maximum_abs = maximum_relative = maximum_normalized = 0.0
    squared, values, agreements, ood_agreements, within = 0.0, 0, 0, 0, True
    for identifier in validation_ids:
        vector = vectors[identifier]
        expected = [learning._distance(vector, model["centroids"][label]) for label in model["labels"]]
        observed_array = session.run(["distances"], {"features": np.asarray([vector], dtype=np.float32)})[0]
        if observed_array.shape != (1, len(model["labels"])) or not np.isfinite(observed_array).all() or np.any(observed_array < 0):
            raise ExportError("Invalid ONNX distance output")
        observed = [float(value) for value in observed_array[0]]
        for value, reference in zip(observed, expected):
            error, allowed = abs(value - reference), atol + rtol * abs(reference)
            maximum_abs = max(maximum_abs, error)
            maximum_relative = max(maximum_relative, error / max(abs(reference), 1e-12))
            maximum_normalized = max(maximum_normalized, error / allowed)
            squared, values = squared + error * error, values + 1
            within = within and error <= allowed
        cpu_result = learning._predict_features(model, vector, expected)
        onnx_result = learning._predict_features(model, vector, observed)
        agreements += cpu_result["label"] == onnx_result["label"]
        ood_agreements += cpu_result["ood"] == onnx_result["ood"]
    passed = within and agreements == len(validation_ids) and ood_agreements == len(validation_ids)
    return {"artifact_sha256": digest, "model_sha256": model["sha256"], "dataset_sha256": dataset["sha256"],
            "format": "ONNX_QDQ_INT8" if kind == "qdq_int8" else "ONNX_FLOAT32",
            "execution_provider": "CPUExecutionProvider", "samples": len(validation_ids), "distance_values": values,
            "validation_annotation_ids": list(validation_ids), "validation_groups": list(model["provenance"]["validation_groups"]),
            "max_absolute_error": maximum_abs, "max_relative_error": maximum_relative,
            "max_normalized_error": maximum_normalized, "rms_error": math.sqrt(squared / values),
            "atol": atol, "rtol": rtol, "label_agreements": agreements, "ood_agreements": ood_agreements,
            "passed": passed, "scope": "recorded_heldout_capture_groups_only", "versions": dependency_status(),
            "npu_qualified": False, "qnn_compiled": False}


def quantize_static_int8(model, dataset, float_artifact, output, *, allow_simulation_calibration=False):
    """Calibrate signed INT8 QDQ from training IDs; gate before publishing."""
    model, dataset, vectors, train_ids, validation_ids = _dataset_features(model, dataset)
    _, original_hash, kind = _load_bound_artifact(float_artifact, model)
    if kind != "float32":
        raise ExportError("Static quantization requires the original float32 artifact")
    if Path(float_artifact).resolve() == Path(output).resolve():
        raise ExportError("Quantized output must not overwrite the float32 source")
    source_counts = model["provenance"]["source_counts"]
    if source_counts["SIMULATION"] and allow_simulation_calibration is not True:
        raise ExportError("Synthetic calibration requires explicit allow_simulation_calibration=True; no physical qualification is implied")
    onnx, np, _ = _dependencies(runtime=True)
    from onnxruntime.quantization import CalibrationDataReader, CalibrationMethod, QuantFormat, QuantType, quantize_static
    from onnxruntime.quantization.shape_inference import quant_pre_process

    class Reader(CalibrationDataReader):
        def __init__(self):
            self.rewind()

        def get_next(self):
            identifier = next(self.identifiers, None)
            return None if identifier is None else {"features": np.asarray([vectors[identifier]], dtype=np.float32)}

        def rewind(self):
            self.identifiers = iter(train_ids)

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".srrx-quant-", dir=output.parent) as directory:
        prepared, quantized = Path(directory) / "prepared.onnx", Path(directory) / "quantized.onnx"
        quant_pre_process(input_model=str(float_artifact), output_model_path=str(prepared),
                          skip_optimization=True, skip_symbolic_shape=True)
        quantize_static(str(prepared), str(quantized), Reader(), quant_format=QuantFormat.QDQ,
                        activation_type=QuantType.QInt8, weight_type=QuantType.QInt8,
                        op_types_to_quantize=["Sub", "Mul", "ReduceMean", "Sqrt", "Unsqueeze"],
                        calibrate_method=CalibrationMethod.MinMax, calibration_providers=["CPUExecutionProvider"],
                        extra_options={"ActivationSymmetric": True, "WeightSymmetric": True})
        proto = onnx.load_model(str(quantized), load_external_data=False)
        q_nodes = sum(node.op_type == "QuantizeLinear" for node in proto.graph.node)
        dq_nodes = sum(node.op_type == "DequantizeLinear" for node in proto.graph.node)
        if not q_nodes or not dq_nodes:
            raise ExportError("Runtime produced no actual QuantizeLinear/DequantizeLinear nodes")
        onnx.helper.set_model_props(proto, _metadata(model, "qdq_int8"))
        proto = onnx.shape_inference.infer_shapes(proto, strict_mode=True)
        onnx.checker.check_model(proto, full_check=True)
        quantized.write_bytes(proto.SerializeToString())
        report = validate_cpu(quantized, model, dataset)
        report.update(calibration_annotation_ids=list(train_ids),
                      calibration_groups=list(model["provenance"]["train_groups"]),
                      calibration_source_counts=dict(source_counts),
                      calibration_method="MinMax", calibration_scope="recorded_training_annotations_only",
                      simulation_calibration_opt_in=allow_simulation_calibration is True,
                      float_artifact_sha256=original_hash, quantize_nodes=q_nodes, dequantize_nodes=dq_nodes,
                      integer_type="signed_int8", mixed_float_ops=True)
        if set(train_ids) & set(validation_ids):
            raise ExportError("Calibration/validation leakage")
        if not report["passed"]:
            raise ExportError("QDQ held-out CPU error/label/OOD gate failed; artifact was not published: " + json.dumps(report, sort_keys=True))
        _atomic_bytes(output, quantized.read_bytes())
    report["artifact"] = str(output)
    return report


def write_qairt_manifest(model, artifact, backend_library, output):
    """Bind real files, not placeholders; does not run/qualify the HTP backend."""
    model = learning.validate_model(model)
    _, artifact_hash, _ = _load_bound_artifact(artifact, model)
    backend = Path(backend_library)
    if backend.name not in ("libQnnHtp.so", "QnnHtp.dll") or backend.resolve().name not in ("libQnnHtp.so", "QnnHtp.dll"):
        raise ExportError("An actual explicit QNN HTP library path is required")
    backend_hash = _sha256(backend, limit=1024 ** 3)
    if backend.stat().st_size < 64:
        raise ExportError("Backend is too small to be a real ELF/PE library")
    with backend.open("rb") as stream:
        header = stream.read(4)
    if not (header == b"\x7fELF" if backend.suffix == ".so" else header[:2] == b"MZ"):
        raise ExportError("Backend is not an ELF/PE library; placeholder files are not accepted")
    manifest = {"schema_version": 1, "kind": "srrx_qairt_htp_distances", "model_sha256": model["sha256"],
                "feature_version": learning.FEATURE_VERSION, "labels": list(model["labels"]),
                "artifact_path": str(Path(artifact).resolve()), "artifact_sha256": artifact_hash,
                "backend_path": str(backend.resolve()), "backend_sha256": backend_hash}
    learning._atomic_json(output, manifest)
    return {"manifest": str(output), "manifest_sha256": _sha256(output),
            "artifact_sha256": artifact_hash, "backend_sha256": backend_hash,
            "npu_qualified": False, "qnn_compiled": False, "scope": "file_binding_only_not_runtime_or_ABI_qualification"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("dependencies")
    command = sub.add_parser("float")
    command.add_argument("--model", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command.add_argument("--dataset", type=Path)
    command.add_argument("--report", type=Path)
    command = sub.add_parser("validate")
    command.add_argument("--model", type=Path, required=True)
    command.add_argument("--dataset", type=Path, required=True)
    command.add_argument("--artifact", type=Path, required=True)
    command.add_argument("--report", type=Path)
    command = sub.add_parser("quantize")
    command.add_argument("--model", type=Path, required=True)
    command.add_argument("--dataset", type=Path, required=True)
    command.add_argument("--input", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command.add_argument("--report", type=Path)
    command.add_argument("--allow-simulation-calibration", action="store_true")
    command = sub.add_parser("manifest")
    command.add_argument("--model", type=Path, required=True)
    command.add_argument("--artifact", type=Path, required=True)
    command.add_argument("--backend-library", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "dependencies":
            result = dependency_status()
            code = 0 if result["available"] else 3
        else:
            model = learning.load_model(args.model)
            if args.command == "float":
                result = export_float(model, args.output)
                if args.dataset:
                    result["validation"] = validate_cpu(args.output, model, learning.load_dataset(args.dataset))
                    result["cpu_validated"] = result["validation"]["passed"]
                code = 0 if result.get("cpu_validated", True) or not args.dataset else 2
            elif args.command == "validate":
                result = validate_cpu(args.artifact, model, learning.load_dataset(args.dataset))
                code = 0 if result["passed"] else 2
            elif args.command == "quantize":
                result = quantize_static_int8(model, learning.load_dataset(args.dataset), args.input, args.output,
                                             allow_simulation_calibration=args.allow_simulation_calibration)
                code = 0
            else:
                result = write_qairt_manifest(model, args.artifact, args.backend_library, args.output)
                code = 0
            if getattr(args, "report", None):
                learning._atomic_json(args.report, result)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return code
    except ExportDependencyError as error:
        print(json.dumps({"ok": False, "available": False, "error": str(error)}))
        return 3
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)[:1000]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
