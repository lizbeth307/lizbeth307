import tempfile
import json
import unittest
from pathlib import Path
from srrx.telemetry import MeasurementSnapshot
from srrx.runtime_telemetry import ProjectTelemetry, MONITORED
from srrx.commissioning import acceptance_template, ValidationError
from srrx.provision import provision

ROOT = Path(__file__).resolve().parents[2]


class Reader:
    def __init__(self, snapshot): self.snapshot = snapshot
    def poll(self): return self.snapshot


class RuntimeTelemetryTests(unittest.TestCase):
    def fixture(self, stamp=900, valid=True):
        acceptance = {"branch_limits": {b: {"calibration": {"status": "PASS", "source": "INA3221:test",
            "current_gain": 1.1, "current_offset_a": .001, "voltage_gain": 1.01, "voltage_offset_v": -.01}}
            for b in MONITORED}}
        bridge = ProjectTelemetry("not-opened", None, acceptance)
        values = {b.lower() + suffix: value for b in MONITORED for suffix, value in [("_current_a", .1), ("_bus_v", 5)]}
        snapshot = MeasurementSnapshot(stamp, values, valid)
        bridge.reader = Reader(snapshot)
        return bridge, snapshot

    def test_only_real_monitored_channels_and_explicit_coefficients(self):
        bridge, original = self.fixture()
        result = bridge.poll(1000)
        self.assertEqual(set(result), set(MONITORED))
        self.assertAlmostEqual(result["LNA1"]["current_a"], .111)
        self.assertAlmostEqual(result["LNA1"]["voltage_v"], 5.04)
        self.assertTrue(result["LNA1"]["calibration_valid"])
        self.assertFalse(original.calibration_valid)
        self.assertNotIn("SB_LNA", result)

    def test_stale_failure_and_future_time_never_relabel_data(self):
        for stamp, valid in [(0, True), (1100, True), (900, False)]:
            bridge, _ = self.fixture(stamp, valid)
            result = bridge.poll(1000)
            self.assertTrue(all(not v["valid"] for v in result.values()))
            self.assertTrue(all("current_a" not in v for v in result.values()))

    def test_bench_only_record_cannot_authorize_runtime_adc(self):
        bridge, _ = self.fixture()
        bridge.acceptance["branch_limits"]["LNA1"]["calibration"]["source"] = "bench_only_no_runtime_sensor"
        self.assertFalse(bridge.poll(1000)["LNA1"]["valid"])

    def test_open_template_cannot_provision_hardware(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            manifest = directory / "open.json"
            manifest.write_text(json.dumps(acceptance_template(ROOT)))
            output = directory / "must-not-exist"
            with self.assertRaises(ValidationError):
                provision(manifest, ROOT, output)
            self.assertFalse(output.exists())
