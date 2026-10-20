import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid

from srrx import learning as ml


def dataset(groups=None):
    result = ml.empty_dataset()
    for family, label in enumerate(("analog_broadcast", "digital_broadcast", "amateur_digital")):
        for index in range(3):
            group = uuid.UUID(int=index + 1 if groups == "shared" else family * 100 + index + 1)
            result = ml.annotate(result, ml._demo_frame(index, family), 0, 256, label,
                                 group_id=group, user_confirmed=True)
    return result


class LearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = dataset()
        cls.model = ml.train(cls.dataset, seed=7)

    def annotate(self, frame=None, **kwargs):
        options = {"group_id": uuid.UUID(int=1), "user_confirmed": True}
        options.update(kwargs)
        return ml.annotate(ml.empty_dataset(), frame or ml._demo_frame(1, 0), 0, 256,
                           "analog_broadcast", **options)

    def test_explicit_user_action_and_label_allowlist_required(self):
        with self.assertRaises(ml.LearningError):
            self.annotate(user_confirmed=False)
        for label in ("radar", "military", "drone", "FPV", "RC", "EW", "emitter_123", "decoded_private_voice"):
            with self.subTest(label=label), self.assertRaises(ml.LearningError):
                ml.annotate(ml.empty_dataset(), ml._demo_frame(1, 0), 0, 256, label,
                            group_id=uuid.uuid4(), user_confirmed=True)

    def test_no_raw_iq_location_payload_or_emitter_metadata(self):
        for key in ("iq", "latitude", "decoded_payload", "emitter_id"):
            frame = ml._demo_frame(1, 0)
            frame[key] = "not permitted"
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.annotate(frame)
        with self.assertRaises(ml.LearningError):
            self.annotate(group_id="radio-on-roof")

    def test_mandatory_mask_reapplied_and_allmasked_or_crossing_boxes_rejected(self):
        frame = ml._demo_frame(1, 0)
        frame["center_hz"] = 300_000_000
        with self.assertRaises(ml.LearningError):
            self.annotate(frame)
        frame["center_hz"] = 224_900_000
        with self.assertRaises(ml.LearningError):
            self.annotate(frame)
        # Nyquist bin0 includes the wrapped upper half-bin, also masked here.
        result = ml.annotate(ml.empty_dataset(), frame, 1, 64, "analog_broadcast",
                             group_id=uuid.uuid4(), user_confirmed=True)
        safe = next(iter(result["frames"].values()))
        self.assertTrue(any(not valid for valid in safe["valid"]))
        self.assertTrue(all(power is None for power, valid in zip(safe["power_dbfs"], safe["valid"]) if not valid))

    def test_caller_invalid_or_incomplete_capture_is_not_training_data(self):
        frame = ml._demo_frame(1, 0)
        frame["valid"][20] = False
        with self.assertRaises(ml.LearningError):
            self.annotate(frame)
        frame = ml._demo_frame(1, 0)
        frame["sample_count"] = 255
        with self.assertRaises(ml.LearningError):
            self.annotate(frame)

    def test_box_bounds_boolean_nan_and_frequency_geometry(self):
        for start, end in ((True, 256), (0, 7), (-1, 256), (100, 90), (0, 257)):
            with self.subTest(box=(start, end)), self.assertRaises(ml.LearningError):
                ml.extract_features(ml._demo_frame(1, 0), start, end)
        frame = ml._demo_frame(1, 0)
        frame["power_dbfs"][0] = float("nan")
        with self.assertRaises(ValueError):
            ml.extract_features(frame, 0, 256)
        frame = ml._demo_frame(1, 0)
        frame["relative_frequency_hz"][1] += 1
        with self.assertRaises(ValueError):
            self.annotate(frame)

    def test_features_are_gain_and_absolute_frequency_invariant(self):
        frame = ml._demo_frame(1, 0)
        changed = copy.deepcopy(frame)
        changed["center_hz"] = 435_000_000
        changed["power_dbfs"] = [power + 25 for power in changed["power_dbfs"]]
        self.assertEqual(ml.extract_features(frame, 0, 256), ml.extract_features(changed, 0, 256))

    def test_duplicate_patch_and_gain_changed_copy_cannot_inflate_dataset(self):
        result = self.annotate()
        frame = ml._demo_frame(1, 0)
        frame["power_dbfs"] = [power + 10 for power in frame["power_dbfs"]]
        with self.assertRaises(ml.LearningError):
            ml.annotate(result, frame, 0, 256, "digital_broadcast", group_id=uuid.uuid4(), user_confirmed=True)

    def test_one_frame_may_not_leak_across_capture_groups_or_overlap_boxes(self):
        frame = ml._demo_frame(1, 0)
        result = ml.annotate(ml.empty_dataset(), frame, 0, 128, "analog_broadcast",
                             group_id=uuid.UUID(int=1), user_confirmed=True)
        with self.assertRaises(ml.LearningError):
            ml.annotate(result, frame, 128, 256, "digital_broadcast", group_id=uuid.UUID(int=2), user_confirmed=True)
        with self.assertRaises(ml.LearningError):
            ml.annotate(result, frame, 100, 200, "analog_broadcast", group_id=uuid.UUID(int=1), user_confirmed=True)

    def test_training_uses_data_and_holdout_groups_are_disjoint(self):
        model = ml.train(dataset(groups="shared"), seed=8)
        provenance = model["provenance"]
        self.assertFalse(set(provenance["train_groups"]) & set(provenance["validation_groups"]))
        self.assertFalse(set(provenance["train_annotation_ids"]) & set(provenance["validation_annotation_ids"]))
        self.assertEqual(sum(provenance["source_counts"].values()), len(provenance["train_annotation_ids"]))
        self.assertEqual(provenance["source_counts"]["HARDWARE"], 0)
        self.assertEqual(model["validation"]["samples"], len(provenance["validation_annotation_ids"]))
        repeat = ml.train(dataset(groups="shared"), seed=8)
        self.assertEqual(model["centroids"], repeat["centroids"])
        self.assertNotEqual(model["centroids"]["analog_broadcast"], model["centroids"]["digital_broadcast"])

    def test_classes_without_independent_holdout_cannot_claim_validation(self):
        result = ml.empty_dataset()
        for family, label in enumerate(("analog_broadcast", "digital_broadcast")):
            result = ml.annotate(result, ml._demo_frame(1, family), 0, 256, label,
                                 group_id=uuid.UUID(int=1), user_confirmed=True)
        with self.assertRaises(ml.LearningError):
            ml.train(result)

    def test_inference_classifies_held_out_shape_and_rejects_ood(self):
        result = ml.infer(self.model, ml._demo_frame(99, 0), 0, 256)
        self.assertEqual(result["label"], "analog_broadcast")
        self.assertEqual(result["backend"], "CPU")
        self.assertGreater(result["confidence"], 0)
        self.assertEqual(result["confidence_kind"], "heuristic_not_calibrated_probability")
        frame = ml._demo_frame(99, 0)
        frame["power_dbfs"] = [-80.0] * 256
        result = ml.infer(self.model, frame, 0, 256)
        self.assertTrue(result["ood"])
        self.assertEqual(result["label"], "unknown_energy")

    def test_infer_reapplies_masks_instead_of_using_unmasked_query(self):
        frame = ml._demo_frame(99, 0)
        frame["center_hz"] = 1_600_000_000
        with self.assertRaises(ml.LearningError):
            ml.infer(self.model, frame, 0, 256)

    def test_model_and_dataset_roundtrip_and_atomic_file_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_path, model_path = Path(directory) / "annotations.json", Path(directory) / "model.json"
            ml.save_dataset(dataset_path, self.dataset)
            ml.save_model(model_path, self.model)
            self.assertEqual(ml.load_dataset(dataset_path), self.dataset)
            self.assertEqual(ml.load_model(model_path), self.model)
            original = dataset_path.read_bytes()
            with patch("srrx.learning.os.replace", side_effect=OSError("disk failure")), self.assertRaises(OSError):
                ml.save_dataset(dataset_path, self.dataset)
            self.assertEqual(dataset_path.read_bytes(), original)
            self.assertFalse(list(Path(directory).glob(".srrx-*")))

    def test_tampered_hash_labels_dimensions_or_provenance_rejected(self):
        model = copy.deepcopy(self.model)
        model["radii"][model["labels"][0]] = .1
        with self.assertRaises(ml.LearningError):
            ml.validate_model(model)
        for mutate in (
            lambda value: value["labels"].append("radar"),
            lambda value: value["centroids"][value["labels"][0]].pop(),
            lambda value: value["provenance"]["validation_groups"].append(value["provenance"]["train_groups"][0]),
            lambda value: value["provenance"].update(seed="private transcript"),
        ):
            model = copy.deepcopy(self.model)
            mutate(model)
            with self.assertRaises(ml.LearningError):
                ml.validate_model(ml._seal(model))

    def test_strict_json_rejects_duplicate_keys_nonfinite_and_extra_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            for data in ('{"v":1,"v":2}', '{"v":NaN}'):
                path.write_text(data)
                with self.assertRaises(ml.LearningError):
                    ml.load_model(path)
            value = copy.deepcopy(self.dataset)
            value["emitter_location"] = "forbidden"
            with self.assertRaises(ml.LearningError):
                ml.validate_dataset(ml._seal(value))

    def test_npu_unavailable_is_explicit_cpu_fallback_not_fake_acceleration(self):
        result = ml.infer(self.model, ml._demo_frame(99, 0), 0, 256, backend="npu")
        self.assertEqual(result["backend"], "CPU")
        self.assertFalse(result["npu"]["available"])
        result = ml.infer(self.model, ml._demo_frame(99, 0), 0, 256, backend="npu", npu_runner=lambda _: [0, 1, 1])
        self.assertEqual(result["backend"], "CPU")
        self.assertFalse(result["npu"]["available"])

    def test_npu_manifest_must_match_model_before_any_runtime_load(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "kind": "srrx_qairt_htp_distances",
                "model_sha256": "0" * 64, "feature_version": ml.FEATURE_VERSION,
                "labels": self.model["labels"], "artifact_path": "absent.onnx", "artifact_sha256": "0" * 64,
                "backend_path": "libQnnHtp.so", "backend_sha256": "0" * 64}))
            result = ml.infer(self.model, ml._demo_frame(99, 0), 0, 256, backend="npu", npu_manifest=manifest)
            self.assertEqual(result["backend"], "CPU")
            self.assertIn("manifest", result["npu"]["reason"])

    def test_cli_demo_train_infer_are_real_working_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(ml.main(["demo", "--output", directory]), 0)
            report = json.loads(output.getvalue())
            self.assertEqual(report["mode"], "SIMULATION")
            self.assertEqual(report["annotations"], 12)
            self.assertFalse(report["prediction"]["npu"]["available"])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ml.main(["train", "--dataset", str(Path(directory) / "annotations.json"),
                                          "--model", str(Path(directory) / "retrained.json"), "--seed", "2"]), 0)
                self.assertEqual(ml.main(["infer", "--model", str(Path(directory) / "retrained.json"),
                    "--frame", str(Path(directory) / "example-spectrum.json"), "--start", "0", "--end", "256"]), 0)


if __name__ == "__main__":
    unittest.main()
