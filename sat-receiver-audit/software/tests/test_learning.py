import contextlib
import copy
import errno
import hashlib
import io
import json
import os
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

    def test_npu_decision_must_equal_cpu_decision_inside_distance_tolerance(self):
        class Runtime(ml.QairtAdapter):
            def __init__(self, model_sha256, values):
                self.model_sha256, self.values = model_sha256, values
            def __call__(self, feature):
                return list(self.values)
        frame = ml._demo_frame(99, 0)
        feature = ml.extract_features(frame, 32, 224)
        exact = [ml._distance(feature, self.model["centroids"][label]) for label in self.model["labels"]]
        best = min(range(len(exact)), key=exact.__getitem__)
        # Radius .004 from the CPU distance; HTP output .008 off, inside .01 + 2%.
        for side, cpu_ood in ((-1, True), (1, False)):
            with self.subTest(cpu_ood=cpu_ood):
                model = copy.deepcopy(self.model)
                model["radii"][model["labels"][best]] = exact[best] + side * .004
                model = ml.validate_model(ml._seal(model))
                cpu = ml.infer(model, frame, 32, 224)
                self.assertEqual(cpu["ood"], cpu_ood)
                shifted = [value + side * .008 if index == best else value for index, value in enumerate(exact)]
                result = ml.infer(model, frame, 32, 224, backend="npu", npu_runner=Runtime(model["sha256"], shifted))
                self.assertEqual(result["backend"], "CPU")
                self.assertFalse(result["npu"]["available"])
                self.assertIn("disagrees", result["npu"]["reason"])
                self.assertEqual({key: result[key] for key in ("label", "ood", "distance", "confidence")},
                                 {key: cpu[key] for key in ("label", "ood", "distance", "confidence")})
        # Agreeing HTP output is labelled as such, but the decision values stay exact CPU values.
        feature = ml.extract_features(frame, 0, 256)
        exact = [ml._distance(feature, self.model["centroids"][label]) for label in self.model["labels"]]
        best = min(range(len(exact)), key=exact.__getitem__)
        result = ml.infer(self.model, frame, 0, 256, backend="npu",
                          npu_runner=Runtime(self.model["sha256"], [value + .005 for value in exact]))
        self.assertEqual(result["backend"], "QAIRT_QNN_HTP")
        self.assertTrue(result["npu"]["available"])
        self.assertEqual(result["distance"], round(exact[best], 9))

    def test_unknown_energy_is_annotatable_but_reserved_as_the_ood_outcome(self):
        result = ml.empty_dataset()
        for family, label in enumerate(("analog_broadcast", "digital_broadcast", "unknown_energy")):
            for index in range(3):
                result = ml.annotate(result, ml._demo_frame(index, family), 0, 256, label,
                                     group_id=uuid.UUID(int=family * 100 + index + 1), user_confirmed=True)
        model = ml.train(result, seed=7)
        self.assertEqual(model["labels"], ["analog_broadcast", "digital_broadcast"])
        self.assertEqual(model["validation"]["samples"], len(model["provenance"]["validation_annotation_ids"]))
        used = set(model["provenance"]["train_annotation_ids"]) | set(model["provenance"]["validation_annotation_ids"])
        reserved = {record["id"] for record in result["annotations"] if record["label"] == "unknown_energy"}
        self.assertEqual(len(reserved), 3)
        self.assertFalse(used & reserved)
        # An OOD rejection can never be scored as a correct class match.
        self.assertEqual(model["validation"]["correct"],
                         sum(model["validation"]["confusion"][label][label] for label in model["labels"]))
        forged = copy.deepcopy(self.model)
        old = forged["labels"][0]
        forged["labels"][0] = "unknown_energy"
        for key in ("centroids", "radii"):
            forged[key]["unknown_energy"] = forged[key].pop(old)
        with self.assertRaises(ml.LearningError):
            ml.validate_model(ml._seal(forged))
        only = ml.empty_dataset()
        for family, label in enumerate(("analog_broadcast", "unknown_energy")):
            for index in range(2):
                only = ml.annotate(only, ml._demo_frame(index, family), 0, 256, label,
                                   group_id=uuid.UUID(int=family * 100 + index + 1), user_confirmed=True)
        with self.assertRaisesRegex(ml.LearningError, "trainable"):
            ml.train(only)

    def test_stored_frames_are_remasked_once_per_validation_not_once_per_box(self):
        result = ml.empty_dataset()
        frame = ml._demo_frame(1, 0)
        for start in range(0, 256, 32):
            result = ml.annotate(result, frame, start, start + 32, "analog_broadcast",
                                 group_id=uuid.UUID(int=1), user_confirmed=True)
        self.assertEqual((len(result["frames"]), len(result["annotations"])), (1, 8))
        with patch("srrx.learning.mask_frame", wraps=ml.mask_frame) as masked:
            self.assertEqual(ml.validate_dataset(result), result)
        self.assertEqual(masked.call_count, 1)
        with patch("srrx.learning.mask_frame", wraps=ml.mask_frame) as masked:
            ml.train(self.dataset, seed=7)
        self.assertEqual(masked.call_count, len(self.dataset["frames"]))

    def test_scope_stop_refuses_annotation_without_frequency_in_the_error(self):
        from srrx import scope_policy
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artemis.json"
            data = json.dumps({"v": 1, "kind": "srrx_artemis_mirror", "source": "artemis-db", "db_version": "v74",
                               "entries": [{"name": "Fixture", "categories": ["Military"],
                                            "ranges_hz": [[137.70e6, 137.71e6]]}]}).encode()
            path.write_bytes(data)
            db = scope_policy.ArtemisDB.load(path, hashlib.sha256(data).hexdigest())
        latch = scope_policy.ScopeLatch(db)
        before = copy.deepcopy(self.dataset)
        with self.assertRaisesRegex(ml.LearningError, "out of scope") as caught:
            ml.annotate(self.dataset, ml._demo_frame(5, 0), 0, 256, "analog_broadcast",
                        group_id=uuid.uuid4(), user_confirmed=True, scope=latch)
        self.assertNotRegex(str(caught.exception), r"\d")
        self.assertEqual(self.dataset, before)
        # A box away from the stop entry in the same (latched) tuning is refused too.
        with self.assertRaises(ml.LearningError):
            ml.annotate(ml.empty_dataset(), ml._demo_frame(5, 0), 0, 64, "analog_broadcast",
                        group_id=uuid.uuid4(), user_confirmed=True, scope=latch)
        clear = ml.annotate(ml.empty_dataset(), ml._demo_frame(5, 0), 0, 64, "analog_broadcast",
                            group_id=uuid.uuid4(), user_confirmed=True, scope=scope_policy.ScopeLatch(db))
        self.assertEqual(len(clear["annotations"]), 1)
        for scope in (object(), {"permits": True}, True):
            with self.subTest(scope=scope), self.assertRaisesRegex(ml.LearningError, "ScopeLatch"):
                ml.annotate(ml.empty_dataset(), ml._demo_frame(5, 0), 0, 256, "analog_broadcast",
                            group_id=uuid.uuid4(), user_confirmed=True, scope=scope)

    def test_masked_band_scope_check_runs_on_the_box_span_even_without_a_latch(self):
        frame = ml._demo_frame(1, 0)  # 137.0-138.0 MHz, 256 bins
        width = frame["sample_rate_hz"] / frame["fft_size"]
        stop = {"stop": True, "reason": "MASKED_BAND", "reasons": ["MASKED_BAND"], "identify": "WITHHELD",
                "display": "out of scope"}
        with patch("srrx.learning.scope_check", return_value=stop) as check:
            with self.assertRaisesRegex(ml.LearningError, "out of scope"):
                self.annotate(frame)
        check.assert_called_once_with(frame["center_hz"] - 128 * width - width / 2,
                                      frame["center_hz"] + 127 * width + width / 2)
        with patch("srrx.learning.scope_check", wraps=ml.scope_check) as check:
            self.annotate(frame)
        # Bin 0 is the even-FFT Nyquist bin: its wrapped upper half-bin is checked too.
        self.assertEqual([call.args for call in check.call_args_list],
                         [(frame["center_hz"] - 128 * width - width / 2, frame["center_hz"] + 127 * width + width / 2),
                          (frame["center_hz"] + 128 * width - width / 2, frame["center_hz"] + 128 * width)])
        with patch("srrx.learning.scope_check", wraps=ml.scope_check) as check:
            ml.annotate(ml.empty_dataset(), frame, 1, 65, "analog_broadcast", group_id=uuid.UUID(int=1), user_confirmed=True)
        self.assertEqual(check.call_count, 1)

    def scope_db(self, *entries):
        from srrx import scope_policy
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artemis.json"
            data = json.dumps({"v": 1, "kind": "srrx_artemis_mirror", "source": "artemis-db", "db_version": "v74",
                               "entries": [{"name": "Fixture %d" % index, "categories": [category], "ranges_hz": [list(span)]}
                                           for index, (category, span) in enumerate(entries)]}).encode()
            path.write_bytes(data)
            return scope_policy.ArtemisDB.load(path, hashlib.sha256(data).hexdigest())

    def test_wrapped_nyquist_half_bin_of_a_box_from_bin_zero_is_scope_checked(self):
        from srrx import scope_policy
        frame = ml._demo_frame(1, 0)  # 137.0-138.0 MHz; bin 0 also holds 137.998-138.0 MHz
        db = self.scope_db(("Military", (137.999e6, 138.0e6)))
        latch = scope_policy.ScopeLatch(db)
        with self.assertRaisesRegex(ml.LearningError, "out of scope") as caught:
            ml.annotate(ml.empty_dataset(), frame, 0, 64, "analog_broadcast", group_id=uuid.uuid4(),
                        user_confirmed=True, scope=latch)
        self.assertNotRegex(str(caught.exception), r"\d")
        self.assertTrue(latch.stopped)  # only the wrapped half-bin span latched
        result = ml.annotate(ml.empty_dataset(), frame, 1, 65, "analog_broadcast", group_id=uuid.uuid4(),
                             user_confirmed=True, scope=latch)
        self.assertEqual(len(result["annotations"]), 1)  # a box from bin 1 has no wrapped content

    def test_train_and_infer_honour_the_session_scope_latch(self):
        from srrx import scope_policy
        benign = scope_policy.ScopeLatch(self.scope_db(("Broadcast", (137.4e6, 137.6e6))))
        model = ml.train(self.dataset, seed=7, scope=benign)
        self.assertEqual(model["labels"], self.model["labels"])
        self.assertEqual(ml.infer(model, ml._demo_frame(99, 0), 0, 256, scope=benign)["label"],
                         ml.infer(model, ml._demo_frame(99, 0), 0, 256)["label"])
        stopped = scope_policy.ScopeLatch(self.scope_db(("Radar", (137.4e6, 137.6e6))))
        for call in (lambda: ml.train(self.dataset, seed=7, scope=stopped),
                     lambda: ml.infer(model, ml._demo_frame(99, 0), 0, 256, scope=stopped)):
            with self.assertRaisesRegex(ml.LearningError, "out of scope") as caught:
                call()
            self.assertNotRegex(str(caught.exception), r"\d")
        self.assertTrue(stopped.stopped)
        # A latch from a stop elsewhere in the session refuses training on those spans too.
        latch = scope_policy.ScopeLatch()
        latch.stop(137.9e6, 137.95e6)
        with self.assertRaisesRegex(ml.LearningError, "Training annotation span is out of scope"):
            ml.train(self.dataset, seed=7, scope=latch)
        latch.retune(400.5e6, 401e6)  # retuned away: the latch is released
        self.assertEqual(ml.train(self.dataset, seed=7, scope=latch)["labels"], self.model["labels"])
        for scope in (object(), True):
            with self.subTest(scope=scope), self.assertRaisesRegex(ml.LearningError, "ScopeLatch"):
                ml.train(self.dataset, seed=7, scope=scope)
            with self.subTest(scope=scope), self.assertRaisesRegex(ml.LearningError, "ScopeLatch"):
                ml.infer(model, ml._demo_frame(99, 0), 0, 256, scope=scope)

    @unittest.skipIf(os.name == "nt", "POSIX directory fsync path")
    def test_directory_fsync_failure_after_replace_is_reported_as_unconfirmed_durability(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "annotations.json"
            with patch("srrx.learning.os.fsync", side_effect=[None, OSError(errno.EIO, "I/O error")]):
                with self.assertRaisesRegex(OSError, "durability not confirmed"):
                    ml.save_dataset(path, self.dataset)
            self.assertEqual(ml.load_dataset(path), self.dataset)
            self.assertFalse(list(Path(directory).glob(".srrx-*")))

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
