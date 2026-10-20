import contextlib
import copy
import io
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from srrx import learning, model_export as export


# Static discovery only. Importing a test module must never initialize ORT.
AVAILABLE = all(importlib.util.find_spec(name) is not None for name in ("onnx", "numpy", "onnxruntime"))


class TelemetryGuardTests(unittest.TestCase):
    def remove_runtime_modules(self):
        # Full-suite launchers may already have used the real privacy guard.
        # Fake-only tests isolate that module table without reloading native ORT.
        for name in list(sys.modules):
            if name == "onnxruntime" or name.startswith("onnxruntime."):
                sys.modules.pop(name)

    def fake_runtime(self, events):
        def disable():
            self.assertEqual(os.environ.get("ORT_DISABLE_TELEMETRY"), "1")
            events.append("disable_telemetry")
        def providers():
            self.assertIn("disable_telemetry", events)
            events.append("providers")
            return ["CPUExecutionProvider"]
        return SimpleNamespace(__version__="fake-only-no-native-code", disable_telemetry_events=disable,
                               get_available_providers=providers)

    def test_opt_out_precedes_import_and_api_disable_precedes_provider_queries(self):
        events = []
        runtime = self.fake_runtime(events)
        def importer(name):
            self.assertEqual(os.environ.get("ORT_DISABLE_TELEMETRY"), "1")
            events.append("import:" + name)
            return runtime if name == "onnxruntime" else SimpleNamespace(__version__="fake")
        with patch.dict(os.environ, {"ORT_DISABLE_TELEMETRY": "0"}), patch.dict(sys.modules):
            self.remove_runtime_modules()
            with patch.object(export, "_verify_ort_privacy_support", side_effect=lambda: events.append("static_verify")), patch.object(export.importlib, "import_module", side_effect=importer):
                report = export.dependency_status()
        self.assertTrue(report["available"])
        self.assertLess(events.index("static_verify"), events.index("import:onnxruntime"))
        self.assertLess(events.index("import:onnxruntime"), events.index("disable_telemetry"))
        self.assertLess(events.index("disable_telemetry"), events.index("providers"))

    def test_unguarded_preloaded_runtime_fails_before_import_or_api(self):
        runtime = self.fake_runtime([])
        with patch.dict(sys.modules, {"onnxruntime": runtime}), patch.object(export.importlib, "import_module") as importer:
            with self.assertRaises(export.ExportPrivacyError):
                export.load_ort_private()
            importer.assert_not_called()

    def test_missing_static_support_fails_before_native_import(self):
        with patch.dict(sys.modules):
            self.remove_runtime_modules()
            with patch.object(export, "_verify_ort_privacy_support", side_effect=export.ExportPrivacyError("unsupported")), patch.object(export.importlib, "import_module") as importer:
                with self.assertRaises(export.ExportPrivacyError):
                    export.load_ort_private()
                importer.assert_not_called()

    def test_missing_or_failing_api_is_unavailable_not_a_usable_runtime(self):
        for runtime in (SimpleNamespace(), SimpleNamespace(disable_telemetry_events=lambda: (_ for _ in ()).throw(RuntimeError("failed")))):
            with self.subTest(runtime=runtime), patch.dict(sys.modules):
                self.remove_runtime_modules()
                with patch.object(export, "_verify_ort_privacy_support"), patch.object(export.importlib, "import_module", return_value=runtime):
                    with self.assertRaises(export.ExportPrivacyError):
                        export.load_ort_private()
                self.assertIsNot(getattr(runtime, "_srrx_private_import_verified", False), True)

    def test_static_proof_checks_installed_docs_and_binary_without_loading_them(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "capi").mkdir()
            (root / "Privacy.md").write_text("ORT_DISABLE_TELEMETRY=1 before ONNX Runtime initializes prevents the uploader and persistent device identifier")
            binary = root / "capi/onnxruntime_pybind11_state.test.so"
            binary.write_bytes(b"not executable test fixture ORT_DISABLE_TELEMETRY")
            spec = SimpleNamespace(origin=str(root / "__init__.py"))
            with patch.object(export.importlib.util, "find_spec", return_value=spec), patch.object(export.sys, "platform", "linux"), patch.object(export.importlib, "import_module") as importer:
                export._verify_ort_privacy_support()
                importer.assert_not_called()
                binary.write_bytes(b"no supported environment control")
                with self.assertRaises(export.ExportPrivacyError):
                    export._verify_ort_privacy_support()

    def test_unknown_platform_fails_closed_before_inspecting_or_importing_runtime(self):
        with patch.object(export.sys, "platform", "win32"), patch.object(export.importlib, "import_module") as importer:
            with self.assertRaises(export.ExportPrivacyError):
                export._verify_ort_privacy_support()
            importer.assert_not_called()


class DependencyTests(unittest.TestCase):
    def test_missing_dependencies_are_explicit_and_do_not_create_artifacts(self):
        with patch("srrx.model_export.importlib.import_module", side_effect=ImportError("not installed")):
            self.assertFalse(export.dependency_status()["available"])
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(export.main(["dependencies"]), 3)
            self.assertFalse(json.loads(output.getvalue())["available"])

    def test_module_import_and_help_do_not_require_onnx(self):
        with patch("srrx.model_export.importlib.import_module", side_effect=ImportError("not installed")):
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
                export.main(["--help"])
            self.assertEqual(result.exception.code, 0)


@unittest.skipUnless(AVAILABLE, "Real ONNX/ONNX Runtime optional dependencies unavailable; CPU artifact tests not executed")
class ModelExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory()
        directory = Path(cls.fixture.name)
        learning.demo(directory)
        cls.model = learning.load_model(directory / "model.json")
        cls.dataset = learning.load_dataset(directory / "annotations.json")

    @classmethod
    def tearDownClass(cls):
        cls.fixture.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.artifact = self.directory / "centroids.onnx"
        export.export_float(self.model, self.artifact)

    def tearDown(self):
        self.temporary.cleanup()

    def test_float_export_is_real_static_onnx_and_actual_ort_matches_heldout(self):
        import onnx
        proto = onnx.load_model(self.artifact)
        self.assertEqual(proto.ir_version, 8)
        self.assertEqual(export._shape(proto.graph.input[0]), [1, 36])
        self.assertEqual(export._shape(proto.graph.output[0]), [1, 3])
        self.assertEqual([node.op_type for node in proto.graph.node], ["Sub", "Mul", "ReduceMean", "Sqrt", "Unsqueeze"])
        report = export.validate_cpu(self.artifact, self.model, self.dataset)
        self.assertTrue(report["passed"])
        self.assertLess(report["max_absolute_error"], 2e-6)
        self.assertEqual(report["execution_provider"], "CPUExecutionProvider")
        self.assertEqual(report["label_agreements"], report["samples"])
        self.assertEqual(report["validation_annotation_ids"], self.model["provenance"]["validation_annotation_ids"])
        self.assertFalse(report["npu_qualified"] or report["qnn_compiled"])

    def test_float_extreme_and_centroid_vectors_match_actual_runtime(self):
        import numpy as np
        import onnxruntime as ort
        options = ort.SessionOptions()
        options.intra_op_num_threads = options.inter_op_num_threads = 1
        session = ort.InferenceSession(str(self.artifact), sess_options=options, providers=["CPUExecutionProvider"])
        vectors = [[0.0] * 36, [1.0] * 36] + list(self.model["centroids"].values())
        for vector in vectors:
            output = session.run(None, {"features": np.asarray([vector], dtype=np.float32)})[0][0]
            expected = [learning._distance(vector, self.model["centroids"][label]) for label in self.model["labels"]]
            self.assertTrue(np.allclose(output, expected, atol=2e-6, rtol=2e-6))

    def test_qdq_actual_nodes_int8_and_error_gate_with_disjoint_real_record_ids(self):
        import onnx
        output = self.directory / "centroids.qdq.onnx"
        report = export.quantize_static_int8(self.model, self.dataset, self.artifact, output, allow_simulation_calibration=True)
        self.assertTrue(report["passed"])
        self.assertLessEqual(report["max_normalized_error"], 1)
        self.assertEqual(report["calibration_annotation_ids"], self.model["provenance"]["train_annotation_ids"])
        self.assertFalse(set(report["calibration_annotation_ids"]) & set(report["validation_annotation_ids"]))
        self.assertFalse(set(report["calibration_groups"]) & set(report["validation_groups"]))
        self.assertEqual(report["calibration_source_counts"], {"HARDWARE": 0, "SIMULATION": 9})
        self.assertEqual(report["integer_type"], "signed_int8")
        self.assertGreater(report["quantize_nodes"], 0)
        self.assertGreater(report["dequantize_nodes"], 0)
        proto = onnx.load_model(output)
        self.assertTrue(any(tensor.data_type == onnx.TensorProto.INT8 for tensor in proto.graph.initializer))
        self.assertFalse(report["npu_qualified"] or report["qnn_compiled"])

    def test_synthetic_calibration_requires_explicit_opt_in(self):
        output = self.directory / "unaccepted.onnx"
        with self.assertRaisesRegex(export.ExportError, "Synthetic calibration"):
            export.quantize_static_int8(self.model, self.dataset, self.artifact, output)
        self.assertFalse(output.exists())

    def test_quantization_gate_failure_does_not_publish_or_overwrite(self):
        output = self.directory / "old.onnx"
        output.write_bytes(b"previous artifact")
        with patch("srrx.model_export.validate_cpu", return_value={"passed": False, "max_absolute_error": 1}), self.assertRaisesRegex(export.ExportError, "gate failed"):
            export.quantize_static_int8(self.model, self.dataset, self.artifact, output, allow_simulation_calibration=True)
        self.assertEqual(output.read_bytes(), b"previous artifact")
        self.assertFalse(list(self.directory.glob(".srrx-quant-*")))

    def test_calibration_rejects_changed_dataset_and_forged_centroid_provenance(self):
        changed = learning.empty_dataset()
        with self.assertRaisesRegex(export.ExportError, "SHA256"):
            export.validate_cpu(self.artifact, self.model, changed)
        model = copy.deepcopy(self.model)
        model["centroids"][model["labels"][0]][0] += .01
        model = learning._seal(model)
        with self.assertRaisesRegex(export.ExportError, "actual training data"):
            export.validate_cpu(self.artifact, model, self.dataset)

    def test_model_artifact_binding_and_custom_nodes_are_checked_before_runtime(self):
        import onnx
        proto = onnx.load_model(self.artifact)
        proto.metadata_props[0].value = "0" * 64
        changed = self.directory / "changed.onnx"
        changed.write_bytes(proto.SerializeToString())
        with self.assertRaises(export.ExportError):
            export.validate_cpu(changed, self.model, self.dataset)
        proto = onnx.load_model(self.artifact)
        proto.graph.node.append(onnx.helper.make_node("Identity", ["features"], ["unused"]))
        changed.write_bytes(proto.SerializeToString())
        with self.assertRaisesRegex(export.ExportError, "unsupported/custom"):
            export.validate_cpu(changed, self.model, self.dataset)

    def test_malformed_or_external_tensor_artifact_rejected(self):
        import onnx
        broken = self.directory / "broken.onnx"
        broken.write_bytes(b"not a protobuf")
        with self.assertRaises(export.ExportError):
            export.validate_cpu(broken, self.model, self.dataset)
        proto = onnx.load_model(self.artifact)
        proto.graph.initializer[0].data_location = onnx.TensorProto.EXTERNAL
        broken.write_bytes(proto.SerializeToString())
        with self.assertRaisesRegex(export.ExportError, "External tensor"):
            export.validate_cpu(broken, self.model, self.dataset)

    def test_cannot_weaken_error_gate_beyond_qairt_or_overwrite_float(self):
        with self.assertRaises(export.ExportError):
            export.validate_cpu(self.artifact, self.model, self.dataset, atol=.02)
        with self.assertRaises(export.ExportError):
            export.quantize_static_int8(self.model, self.dataset, self.artifact, self.artifact, allow_simulation_calibration=True)

    def test_atomic_float_failure_preserves_existing_artifact(self):
        previous = self.artifact.read_bytes()
        with patch("srrx.model_export.os.replace", side_effect=OSError("disk failure")), self.assertRaises(OSError):
            export.export_float(self.model, self.artifact)
        self.assertEqual(self.artifact.read_bytes(), previous)
        self.assertFalse(list(self.directory.glob(".srrx-model-*")))

    def test_manifest_requires_real_existing_backend_not_a_placeholder(self):
        destination = self.directory / "manifest.json"
        backend = self.directory / "libQnnHtp.so"
        with self.assertRaises(export.ExportError):
            export.write_qairt_manifest(self.model, self.artifact, backend, destination)
        backend.write_bytes(b"placeholder QNN library" + b"0" * 100)
        with self.assertRaises(export.ExportError):
            export.write_qairt_manifest(self.model, self.artifact, backend, destination)
        backend.write_bytes(b"\x7fELF")
        with self.assertRaises(export.ExportError):
            export.write_qairt_manifest(self.model, self.artifact, backend, destination)
        self.assertFalse(destination.exists())

    @unittest.skipUnless(os.environ.get("SRRX_QNN_HTP_LIBRARY"), "Actual QNN HTP SDK library unavailable; no real manifest was generated")
    def test_manifest_binds_actual_opted_in_backend_bytes_without_claiming_qualification(self):
        backend = Path(os.environ["SRRX_QNN_HTP_LIBRARY"])
        destination = self.directory / "manifest.json"
        report = export.write_qairt_manifest(self.model, self.artifact, backend, destination)
        manifest = json.loads(destination.read_text())
        self.assertEqual(manifest["model_sha256"], self.model["sha256"])
        self.assertEqual(manifest["backend_sha256"], export._sha256(backend, limit=1024 ** 3))
        self.assertFalse(report["npu_qualified"])

    def test_cli_export_validate_and_quantize_write_measured_reports(self):
        fixture = Path(self.fixture.name)
        output, report = self.directory / "cli.onnx", self.directory / "float-report.json"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(export.main(["float", "--model", str(fixture / "model.json"),
                "--dataset", str(fixture / "annotations.json"), "--output", str(output), "--report", str(report)]), 0)
            self.assertEqual(export.main(["validate", "--model", str(fixture / "model.json"),
                "--dataset", str(fixture / "annotations.json"), "--artifact", str(output)]), 0)
            self.assertEqual(export.main(["quantize", "--model", str(fixture / "model.json"),
                "--dataset", str(fixture / "annotations.json"), "--input", str(output),
                "--output", str(self.directory / "cli.int8.onnx"), "--allow-simulation-calibration"]), 0)
        measured = json.loads(report.read_text())
        self.assertTrue(measured["cpu_validated"])
        self.assertFalse(measured["npu_qualified"])


if __name__ == "__main__":
    unittest.main()
