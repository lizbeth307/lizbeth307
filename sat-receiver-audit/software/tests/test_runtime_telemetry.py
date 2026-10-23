import tempfile
import json
import unittest
from pathlib import Path
from srrx.hardware import SimHardware
from srrx.policy import CAPS, SafetyPolicy
from srrx.telemetry import MeasurementSnapshot
from srrx.runtime_telemetry import ProjectTelemetry, MONITORED
from srrx.commissioning import acceptance_template, ValidationError
from srrx.provision import provision

ROOT = Path(__file__).resolve().parents[2]


class Reader:
    def __init__(self, snapshot): self.snapshot = snapshot
    def poll(self): return self.snapshot


class RuntimeTelemetryTests(unittest.TestCase):
    def fixture(self, stamp=900, valid=True, acquired=1000, current=.1, bus=5,
                current_offset=.001, voltage_offset=-.01):
        acceptance = {"branch_limits": {b: {"calibration": {"status": "PASS", "source": "INA3221:test",
            "current_gain": 1.1, "current_offset_a": current_offset, "voltage_gain": 1.01,
            "voltage_offset_v": voltage_offset}} for b in MONITORED}}
        bridge = ProjectTelemetry("not-opened", None, acceptance, clock=lambda: acquired)
        values = {b.lower() + suffix: value for b in MONITORED for suffix, value in
                  [("_current_a", current), ("_shunt_v", current * .2), ("_bus_v", bus)]}
        snapshot = MeasurementSnapshot(stamp, values, valid)
        bridge.reader = Reader(snapshot)
        return bridge, snapshot

    def armed_policy(self):
        hardware = SimHardware()
        policy = SafetyPolicy(hardware, clock=lambda: 0)
        inputs = dict(hardware.read_inputs(), DCS_UHF=False, DCS_LBAND=False, DCS_HF=False,
                      PG_LNB=True, PG_BONI=True, PTC_AUX=True, OVP_LNB_N=True)
        policy.refresh_inputs(inputs, 1000)
        policy.configure_limits({b: {"baseline_a": min(.1, cap * .5), "max_current_a": min(cap * .8, min(.1, cap * .5) * 1.2),
                                     "min_voltage_v": min(3, vcap - .2), "max_voltage_v": vcap} for b, (cap, vcap) in CAPS.items()})
        policy.set_readiness(pico_active=True, commissioned=True)
        self.assertTrue(policy.command("lease", {"owner": "test", "ttl_ms": 5000}, 1000)["ok"])
        self.assertTrue(policy.command("arm", True, 1000)["ok"])
        return policy

    def test_delayed_acquisition_is_fresh_and_never_labelled_after_the_tick(self):
        # The INA reads finish after the engine tick time; that is not future data.
        bridge, _ = self.fixture(stamp=1010, acquired=1030)
        result = bridge.poll(1000)
        self.assertTrue(all(v["valid"] for v in result.values()))
        self.assertTrue(all(v["timestamp_ms"] == 1000 for v in result.values()))
        policy = self.armed_policy()
        policy.refresh_telemetry(result, 1000)
        self.assertIsNone(policy.fault)
        self.assertTrue(policy.armed)
        # Future relative to the acquisition clock, or a clock behind the tick, is rejected.
        for stamp, acquired in [(1040, 1030), (900, 990)]:
            bridge, _ = self.fixture(stamp=stamp, acquired=acquired)
            self.assertTrue(all(not v["valid"] for v in bridge.poll(1000).values()))

    def test_idle_zero_offset_never_reads_as_reversed_polarity(self):
        # All branches OFF: -1 LSB shunt, 0 V bus and the most negative accepted
        # intercepts. That is not reverse polarity and must not trip or block arming.
        bridge, _ = self.fixture(current=-40e-6 / .2, bus=0, current_offset=-.02, voltage_offset=-.2)
        result = bridge.poll(1000)
        self.assertTrue(all(v["valid"] and v["current_a"] == 0 and v["voltage_v"] == 0 for v in result.values()))
        policy = self.armed_policy()
        policy.refresh_telemetry(result, 1000)
        self.assertIsNone(policy.fault)
        self.assertTrue(policy.armed)
        # A real reversed current beyond the zero band still trips, despite the intercept.
        bridge, _ = self.fixture(current=-.05, bus=4.5, current_offset=.02)
        result = bridge.poll(1000)
        self.assertLess(result["LNA1"]["current_a"], 0)
        policy.refresh_telemetry(result, 1000)
        self.assertIn("polarity", policy.fault)
        self.assertFalse(policy.armed)

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
