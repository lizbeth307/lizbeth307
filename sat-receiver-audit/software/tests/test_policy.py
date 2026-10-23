import unittest
from unittest.mock import patch

from srrx.hardware import SimHardware
from srrx.policy import CAPS, SafetyPolicy


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.hardware = SimHardware()
        self.policy = SafetyPolicy(self.hardware, clock=lambda: 0)
        self.inputs = self.hardware.read_inputs()
        self.inputs.update(DCS_UHF=False, DCS_LBAND=False, DCS_HF=False,
                           PG_LNB=True, PG_BONI=True, PTC_AUX=True, OVP_LNB_N=True)
        self.policy.refresh_inputs(self.inputs, 0)
        limits = {}
        for branch, (cap, vcap) in CAPS.items():
            baseline = min(.1, cap * .5)
            limits[branch] = {"baseline_a": baseline, "max_current_a": min(cap * .8, baseline * 1.2),
                              "min_voltage_v": min(3, vcap - .2), "max_voltage_v": vcap}
        self.policy.configure_limits(limits)
        self.seed(0)

    def seed(self, now, current=0, voltage=0):
        self.policy.refresh_telemetry({branch: {"current_a": current, "voltage_v": voltage, "timestamp_ms": now}
                                       for branch in CAPS}, now)

    def arm(self, now=0):
        self.policy.set_readiness(pico_active=True, commissioned=True)
        self.assertTrue(self.policy.command("lease", {"owner": "daemon", "ttl_ms": 5000}, now)["ok"])
        self.assertTrue(self.policy.command("arm", True, now)["ok"])

    def dwell(self):
        for now in (200, 400, 500, 700, 900, 1000):
            self.policy.refresh_inputs(self.inputs, now)
        self.seed(1000)

    def test_start_disarmed_and_no_readiness_or_raw_gpio_bypass(self):
        self.assertFalse(self.policy.status()["armed"])
        self.assertFalse(self.policy.command("EN_LNA1", True, 0)["ok"])
        self.arm()
        for name, value in (("TX_ENABLE", True), ("K1_ON", True), ("SW_RTLB_A", True),
                            ("CHG_INHIBIT", False), ("E3_GNSS_RESET_GATE", True)):
            self.assertFalse(self.policy.command(name, value, 0)["ok"], name)
        self.assertTrue(self.hardware.outputs["CHG_INHIBIT"])

    def test_unknown_and_stale_telemetry_cannot_enable(self):
        self.arm()
        self.policy.telemetry.pop("LNA1")
        self.assertFalse(self.policy.command("EN_LNA1", True, 0)["ok"])
        self.policy.refresh_inputs(self.inputs, 1001)
        self.assertFalse(self.policy.command("EN_LNA4", True, 1001)["ok"])
        with self.assertRaises(ValueError):
            self.policy.configure_limits({})

    def test_dc_preflight_requires_settling_and_continuous_low_after_off(self):
        self.arm()
        self.assertFalse(self.policy.command("EN_LNA2", True, 0)["ok"])
        self.dwell()
        self.assertTrue(self.policy.command("EN_LNA2", True, 1000)["ok"])
        self.inputs["DCS_UHF"] = True  # own bias expected; no foreign-DC trip
        self.policy.refresh_inputs(self.inputs, 1001)
        self.assertIsNone(self.policy.fault)
        self.assertTrue(self.policy.command("EN_LNA2", False, 1001)["ok"])
        self.assertFalse(self.policy.command("EN_LNA2", True, 1001)["ok"])

    def test_one_high_or_missing_interval_restarts_dc_dwell(self):
        self.arm()
        self.dwell()
        self.inputs["DCS_UHF"] = True
        self.policy.refresh_inputs(self.inputs, 1001)
        self.inputs["DCS_UHF"] = False
        self.policy.refresh_inputs(self.inputs, 1002)
        self.assertFalse(self.policy.command("EN_LNA2", True, 1002)["ok"])

    def test_fault_latches_all_off_and_off_still_accepted(self):
        self.arm()
        self.assertTrue(self.policy.command("EN_LNA1", True, 0)["ok"])
        self.inputs["FAULT_LNA1"] = False
        self.policy.refresh_inputs(self.inputs, 1)
        self.assertFalse(self.hardware.outputs["EN_LNA1"])
        self.assertTrue(self.hardware.outputs["CHG_INHIBIT"])
        self.inputs["FAULT_LNA1"] = True
        self.policy.refresh_inputs(self.inputs, 2)
        self.assertFalse(self.policy.command("arm", True, 2)["ok"])
        self.assertTrue(self.policy.command("EN_LNA1", False, 2)["ok"])

    def test_i2c_exception_latches_and_calls_emergency_all_off(self):
        self.arm()
        with patch.object(self.hardware, "apply_outputs", side_effect=OSError("bus gone")):
            self.assertFalse(self.policy.command("EN_LNA1", True, 0)["ok"])
        self.assertIn("I2C", self.policy.fault)
        self.assertEqual(self.hardware.trace[-1]["event"], "all_off")

    def test_finite_single_owner_lease_and_no_late_renewal_rearms(self):
        self.arm()
        self.assertFalse(self.policy.command("lease", {"owner": "other", "ttl_ms": 1000}, 0)["ok"])
        self.assertFalse(self.policy.command("lease", {"owner": "daemon", "ttl_ms": float("inf")}, 0)["ok"])
        self.policy.tick(5000)
        self.assertFalse(self.policy.armed)
        self.assertIn("lease", self.policy.fault)
        self.policy.command("lease", {"owner": "daemon", "ttl_ms": 1000}, 5000)
        self.assertFalse(self.policy.command("arm", True, 5000)["ok"])

    def test_relay_break_before_make_and_never_11(self):
        self.arm()
        self.assertTrue(self.policy.command("relay", "HF", 10)["ok"])
        self.assertFalse(self.policy.command("relay", "VHF", 11)["ok"])
        self.assertFalse(self.hardware.outputs["K1_ON"] or self.hardware.outputs["K2_ON"])
        self.assertFalse(self.policy.command("relay", "VHF", 20)["ok"])
        self.assertTrue(self.policy.command("relay", "VHF", 21)["ok"])
        self.assertFalse(self.policy.command("relay", "11", 21)["ok"])
        self.assertFalse(any(event.get("outputs", {}).get("K1_ON") and event.get("outputs", {}).get("K2_ON")
                             for event in self.hardware.trace))

    def test_lnb_route_and_pg_timeout_duplicate_on_does_not_extend_timer(self):
        self.arm()
        self.assertFalse(self.policy.command("EN_LNB", True, 0)["ok"])
        self.assertTrue(self.policy.command("route_RTLB", "RF3", 0)["ok"])
        self.assertTrue(self.policy.command("EN_LNB", True, 0)["ok"])
        self.inputs["PG_LNB"] = False
        self.policy.refresh_inputs(self.inputs, 200)
        self.assertTrue(self.policy.command("EN_LNB", True, 200)["ok"])
        self.assertEqual(self.policy.enabled_since["LNB"], 0)
        self.policy.refresh_inputs(self.inputs, 400)
        self.seed(400, voltage=13.2)
        self.policy.refresh_inputs(self.inputs, 500)
        self.assertIn("power-good", self.policy.fault)

    def test_running_telemetry_and_inputs_expire(self):
        self.arm()
        self.assertTrue(self.policy.command("EN_LNA1", True, 0)["ok"])
        self.policy.tick(251)
        self.assertIn("GPIO", self.policy.fault)

    def test_antenna_reservation_counts_sb_once_and_lab_reserves_point83(self):
        # Direct budget checks isolate load reservation from RF preflight rules.
        self.policy.limits.update({branch: dict(self.policy.limits[branch], max_current_a=.25)
                                   for branch in ("LNA1", "LNA2", "LNA3")})
        proposed = dict(self.hardware.outputs, EN_LNA1=True, EN_LNA2=True, EN_LNA3=True,
                        EN_SB_LNA=True, EN_LABPORT=True)
        self.assertFalse(self.policy._budget_ok(proposed, 0))  # .75+.065+.83
        proposed["EN_LABPORT"] = False
        self.assertTrue(self.policy._budget_ok(proposed, 0))
        self.policy.limits["LNA4"]["max_current_a"] = .2
        proposed["EN_LNA4"] = True
        self.assertFalse(self.policy._budget_ok(proposed, 0))  #1.015, SB once

    def test_boni_needs_confirmation_hf_and_two_second_current_window(self):
        self.arm()
        self.dwell()
        self.assertFalse(self.policy.command("EN_BONI", True, 1000)["ok"])
        self.assertTrue(self.policy.command("relay", "HF", 1000)["ok"])
        self.policy.command("confirmations", {"boni_connected": True, "boni_profile": True}, 1000)
        self.assertTrue(self.policy.command("EN_BONI", True, 1000)["ok"])
        for now in range(1200, 3001, 200):
            self.policy.refresh_inputs(self.inputs, now)
            self.policy.refresh_telemetry({"BONI": {"current_a": .02, "voltage_v": 13.8, "timestamp_ms": now}}, now)
        self.assertIn("startup current", self.policy.fault)

    def test_invalid_nan_telemetry_never_becomes_accepted_adc_data(self):
        self.policy.refresh_telemetry({"LNA1": {"current_a": float("nan"), "voltage_v": 4.5, "timestamp_ms": 0}}, 0)
        self.assertIsNotNone(self.policy.fault)

    def test_unmonitored_branch_uses_reservation_and_fault_without_invented_adc(self):
        self.arm()
        self.assertNotIn("RTLA", self.policy.telemetry)
        self.assertTrue(self.policy.command("EN_RTLA", True, 0)["ok"])
        self.assertTrue(self.policy.status()["branch_observability"]["RTLA"]["current_unknown"])
        self.policy.refresh_inputs(self.inputs, 200)
        self.policy.tick(200)
        self.assertIsNone(self.policy.fault)
        self.inputs["FAULT_RTLA"] = False
        self.policy.refresh_inputs(self.inputs, 201)
        self.assertIsNotNone(self.policy.fault)

    def test_lab5_budget_includes_explicit_always_on_and_overhead(self):
        self.policy.configure_power_budget(always_on_a=3.1)
        self.arm()
        self.assertFalse(self.policy.command("EN_RTLA", True, 0)["ok"])
        self.assertFalse(self.hardware.outputs["EN_RTLA"])

    def test_invalid_calibration_removes_previously_fresh_sample(self):
        self.policy.refresh_telemetry({"LNA1": {"current_a": .1, "voltage_v": 4.5,
            "timestamp_ms": 0, "valid": False, "calibration_valid": False}}, 0)
        self.assertNotIn("LNA1", self.policy.telemetry)
        self.arm()
        self.assertFalse(self.policy.command("EN_LNA1", True, 0)["ok"])

    def test_explicit_fault_clear_remains_disarmed(self):
        self.arm()
        self.policy.trip("operator trip")
        self.assertTrue(self.policy.clear_fault(0))
        self.assertIsNone(self.policy.fault)
        self.assertFalse(self.policy.armed)
        self.assertFalse(self.policy.command("EN_LNA1", True, 0)["ok"])

    def test_integer_beyond_float_range_is_rejected_not_raised(self):
        huge = 10 ** 400  # math.isfinite(huge) raises OverflowError.
        with self.assertRaises(ValueError):
            self.policy.configure_power_budget(always_on_a=huge)
        self.arm()
        result = self.policy.command("lease", {"owner": "daemon", "ttl_ms": huge}, 0)
        self.assertFalse(result["ok"])
        self.assertTrue(self.policy.armed)
        self.assertTrue(self.policy.command("EN_LNA1", True, 0)["ok"])
        self.policy.refresh_telemetry({"LNA1": {"current_a": huge, "voltage_v": 4.5, "timestamp_ms": 0}}, 0)
        self.assertIn("ceiling", self.policy.fault)
        self.assertFalse(self.hardware.outputs["EN_LNA1"])

    def test_repeated_unconfirmed_safe_write_does_not_grow_fault(self):
        self.arm()
        with patch.object(self.hardware, "all_off", side_effect=OSError("MCP held in RESET")):
            for _ in range(1000):
                self.policy.trip("pico_TRIPPED")
        self.assertEqual(self.policy.fault, "pico_TRIPPED; safe write unconfirmed: Pico MCP RESET required")

    def test_explicit_recovery_clears_confirmations_given_before_arm(self):
        # No lease is held at boot; a statement made then must not carry into a session.
        self.assertTrue(self.policy.command("confirmations", {"bench_loads": True, "boni_connected": True}, 0)["ok"])
        self.policy.set_readiness(pico_active=True, commissioned=True)
        self.assertTrue(self.policy.clear_fault(0))
        self.assertFalse(any(self.policy.confirmations.values()))

    def test_bad_control_type_is_rejected_without_gpio_write(self):
        count = len(self.hardware.trace)
        self.assertFalse(self.policy.command(None, True, 0)["ok"])
        self.arm()
        self.assertFalse(self.policy.command("route_RTLA", {}, 0)["ok"])
        self.assertEqual(len(self.hardware.trace), count)


if __name__ == "__main__":
    unittest.main()
