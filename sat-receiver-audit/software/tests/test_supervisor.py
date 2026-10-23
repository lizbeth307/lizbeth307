"""Executable supervisor/adapter safety boundaries without importing machine."""
import json
from pathlib import Path
import sys
import unittest

PICO = Path(__file__).resolve().parents[2] / "firmware" / "pico"
sys.path.insert(0, str(PICO))
from supervisor import Supervisor
from adapter import Hardware, TickClock, write_all
from calibration import (REVISION, commissioning_valid, crc32,
                         from_two_points, ntc_temperature, seal, validate)
from imu_relay import IMURelay
from main import hello_payload, status_payload
from srrx.wire import FrameDecoder, encode_frame


READY = {"q6a_on": True, "battery_mv": 14800, "panel_temp_c": 25.0,
         "case_temp_c": 25.0, "button_pressed": False}


class Rig:
    def __init__(self, **kwargs):
        options = {"calibration_valid": True, "hardware_commissioned": True,
                   "session_factory": lambda: 1234}
        options.update(kwargs)
        self.model = Supervisor(**options)
        self.inputs = dict(READY)
        self.now = 0
        self.seq = 0
        self.model.step(0, self.inputs)

    def advance(self, target, heartbeat=False):
        while self.now < target:
            self.now = min(target, self.now + 20)
            self.model.step(self.now, self.inputs)
            if heartbeat and self.now % 200 == 0:
                self.send("HB")

    def send(self, kind, payload=None, **overrides):
        frame = {"v": 1, "t": kind, "s": self.model.session,
                 "q": self.seq, "p": payload or {}}
        frame.update(overrides)
        self.seq += 1
        return self.model.receive(frame, self.now)

    def activate(self):
        assert self.send("ARM", {"qualified": True})
        self.advance(20)
        self.send("HB", {"soc_temp_c": 45})
        self.advance(120)
        self.send("HB", {"soc_temp_c": 45})
        assert self.model.state == "CONFIGURING"
        self.advance(140)
        assert self.send("CONFIGURED", {"safe": True})
        self.advance(200)
        self.send("HB", {"soc_temp_c": 45})
        return self


class SupervisorTests(unittest.TestCase):
    def test_boot_defaults_never_release_reset(self):
        model = Supervisor()
        self.assertEqual(model.state, "SAFE")
        self.assertTrue(model.outputs["mcp_reset"])
        self.assertFalse(model.outputs["disp_en"])
        self.assertTrue(model.outputs["safe_boot"])
        self.assertTrue(model.outputs["fan_en"])
        self.assertTrue(model.outputs["blower_en"])
        self.assertFalse(model.outputs["pico_off"])

    def test_local_and_host_gates_independently_required(self):
        for flags, expected in (({"hardware_commissioned": False}, "NOT_COMMISSIONED"),
                                ({"calibration_valid": False}, "ADC_UNCALIBRATED")):
            rig = Rig(**flags)
            self.assertFalse(rig.send("ARM", {"qualified": True}))
            self.assertEqual(rig.model.reject_reason, expected)
            self.assertTrue(rig.model.outputs["mcp_reset"])
        rig = Rig()
        self.assertFalse(rig.send("ARM", {"qualified": 1}))
        self.assertEqual(rig.model.reject_reason, "HOST_NOT_QUALIFIED")

    def test_q6a_off_invalid_and_hot_sensors_block_arm(self):
        for field, value, reason in (("q6a_on", False, "Q6A_OFF"),
                                     ("battery_mv", None, "SENSOR_INVALID"),
                                     ("battery_mv", 13050, "BATTERY_LOW"),
                                     ("panel_temp_c", float("nan"), "SENSOR_INVALID"),
                                     ("case_temp_c", float("inf"), "SENSOR_INVALID"),
                                     ("panel_temp_c", 68, "PANEL_HOT"),
                                     ("case_temp_c", 61, "CASE_HOT")):
            rig = Rig()
            rig.inputs[field] = value
            rig.model.step(0, rig.inputs)
            self.assertFalse(rig.send("ARM", {"qualified": True}), field)
            self.assertEqual(rig.model.reject_reason, reason)

    def test_warm_guard_two_fresh_hbs_then_explicit_configured(self):
        rig = Rig()
        rig.send("ARM", {"qualified": True})
        rig.send("HB")
        rig.send("HB")  # Same clock tick cannot satisfy two fresh observations.
        rig.advance(100)
        self.assertEqual(rig.model.state, "WARMING")
        rig.send("HB")
        self.assertEqual(rig.model.state, "CONFIGURING")
        self.assertFalse(rig.model.outputs["mcp_reset"])
        self.assertTrue(rig.model.outputs["disp_en"])
        rig.send("CONFIGURED", {"safe": True})
        self.assertEqual(rig.model.state, "ACTIVE")
        self.assertTrue(rig.model.outputs["disp_en"])
        self.assertFalse(rig.model.outputs["safe_boot"])

    def test_single_hb_before_guard_cannot_release(self):
        rig = Rig()
        rig.send("ARM", {"qualified": True})
        rig.advance(1)
        rig.send("HB")
        rig.advance(99)
        rig.send("HB")
        self.assertTrue(rig.model.outputs["mcp_reset"])
        rig.advance(100)
        self.assertFalse(rig.model.outputs["mcp_reset"])

    def test_heartbeat_deadline_at_750_not_749(self):
        rig = Rig().activate()
        old_session = rig.model.session
        rig.advance(949)
        self.assertEqual(rig.model.state, "ACTIVE")
        rig.advance(950)
        self.assertEqual(rig.model.fault, "HEARTBEAT_TIMEOUT")
        self.assertTrue(rig.model.outputs["mcp_reset"])
        self.assertNotEqual(rig.model.session, old_session)
        self.assertTrue(rig.model.outputs["fan_en"])
        self.assertTrue(rig.model.outputs["blower_en"])

    def test_late_hb_cannot_rescue_after_deadline(self):
        rig = Rig().activate()
        old = rig.model.session
        rig.model.step(940, rig.inputs)
        self.assertFalse(rig.model.receive({"v": 1, "t": "HB", "s": old,
                                           "q": 50, "p": {}}, 950))
        self.assertEqual(rig.model.state, "TRIPPED")

    def test_no_heartbeat_during_warm_times_out(self):
        rig = Rig()
        rig.send("ARM", {"qualified": True})
        rig.advance(750)
        self.assertEqual(rig.model.fault, "HEARTBEAT_TIMEOUT")

    def test_replay_and_old_session_never_refresh_heartbeat(self):
        rig = Rig().activate()
        seq = rig.model.last_host_seq
        rig.advance(900)
        self.assertFalse(rig.send("HB", q=seq))
        rig.advance(950)
        old = rig.model.session
        self.assertTrue(rig.send("HB"))
        rig.advance(1000)
        self.assertEqual(rig.model.state, "TRIPPED")
        self.assertEqual(rig.model.session, old)
        self.assertTrue(rig.model.outputs["mcp_reset"])
        # New current-session ARM is the only recovery path.
        self.assertTrue(rig.send("ARM", {"qualified": True}))
        self.assertEqual(rig.model.state, "WARMING")

    def test_host_trip_rotates_nonce_and_rejects_delayed_configured(self):
        rig = Rig().activate()
        previous = rig.model.session
        rig.send("TRIP")
        self.assertNotEqual(rig.model.session, previous)
        self.assertFalse(rig.send("CONFIGURED", {"safe": True}, s=previous))
        self.assertEqual(rig.model.state, "TRIPPED")

    def test_no_sequence_wrap_or_boolean_fields(self):
        rig = Rig().activate()
        self.assertFalse(rig.send("HB", q=True))
        self.assertFalse(rig.send("HB", s=True))
        self.assertFalse(rig.send("HB", v=True))
        self.assertFalse(rig.send("HB", q=0xffffffff))
        self.assertEqual(rig.model.fault, "SEQUENCE_EXHAUSTED")

    def test_configured_must_be_safe_and_in_correct_phase(self):
        for phase in ("WARMING", "CONFIGURING"):
            rig = Rig()
            rig.send("ARM", {"qualified": True})
            if phase == "CONFIGURING":
                rig.advance(1)
                rig.send("HB")
                rig.advance(101)
                rig.send("HB")
            self.assertFalse(rig.send("CONFIGURED", {"safe": False}))
            self.assertEqual(rig.model.fault, "CONFIGURATION_INVALID")

    def test_configured_timeout_not_extended_by_hbs(self):
        rig = Rig()
        rig.send("ARM", {"qualified": True})
        rig.advance(20)
        rig.send("HB")
        rig.advance(120)
        rig.send("HB")
        rig.advance(1119, heartbeat=True)
        self.assertEqual(rig.model.state, "CONFIGURING")
        rig.advance(1120)
        self.assertEqual(rig.model.fault, "CONFIGURATION_TIMEOUT")

    def test_active_sensor_failure_trips_and_status_stays_json_safe(self):
        for field, value in (("panel_temp_c", None), ("case_temp_c", float("nan")),
                             ("battery_mv", float("inf"))):
            rig = Rig().activate()
            rig.inputs[field] = value
            rig.advance(220)
            self.assertEqual(rig.model.fault, "SENSOR_INVALID")
            self.assertTrue(rig.model.outputs["mcp_reset"])
            frame = {"v": 1, "t": "STATUS", "s": rig.model.session,
                     "q": 0, "p": rig.model.status()}
            self.assertEqual(FrameDecoder().feed(encode_frame(frame)), [frame])

    def test_stale_samples_and_reverse_clock_fail_closed(self):
        rig = Rig().activate()
        rig.model.receive({"v": 1, "t": "HB", "s": rig.model.session,
                           "q": 40, "p": {}}, 451)
        self.assertEqual(rig.model.fault, "SENSOR_STALE")
        rig = Rig().activate()
        rig.model.step(199, rig.inputs)
        self.assertEqual(rig.model.fault, "CLOCK_REVERSED")

    def test_q6a_loss_reset_immediate_cut_after_three_seconds(self):
        rig = Rig().activate()
        rig.inputs["q6a_on"] = False
        rig.advance(220)
        self.assertEqual(rig.model.fault, "Q6A_OFF")
        self.assertTrue(rig.model.outputs["mcp_reset"])
        self.assertFalse(rig.model.outputs["disp_en"])
        rig.advance(3219)
        self.assertNotEqual(rig.model.state, "OFF")
        rig.advance(3220)
        self.assertEqual(rig.model.state, "OFF")
        self.assertTrue(rig.model.outputs["pico_off"])
        rig.advance(3470)
        self.assertFalse(rig.model.outputs["pico_off"])

    def test_initial_q6a_off_does_not_cut_before_it_boots(self):
        model = Supervisor()
        inputs = dict(READY, q6a_on=False)
        for now in range(0, 6001, 20):
            model.step(now, inputs)
        self.assertEqual(model.state, "SAFE")
        self.assertFalse(model.outputs["pico_off"])

    def test_off_now_grace_fixed_and_requires_arm_off(self):
        rig = Rig().activate()
        self.assertFalse(rig.send("SHUTDOWN", {"phase": "OFF_NOW"}))
        self.assertTrue(rig.send("SHUTDOWN", {"phase": "ARM_OFF"}))
        self.assertEqual(rig.model.state, "SHUTTING_DOWN")
        self.assertTrue(rig.model.outputs["mcp_reset"])
        rig.advance(300)
        rig.send("SHUTDOWN", {"phase": "OFF_NOW"})
        rig.advance(2000)
        rig.send("SHUTDOWN", {"phase": "OFF_NOW"})
        rig.advance(20299)
        self.assertEqual(rig.model.state, "SHUTTING_DOWN")
        rig.advance(20300)
        self.assertEqual(rig.model.fault, "OFF_NOW_GRACE_ELAPSED")

    def test_arm_off_lost_hb_cut_after_sixty_seconds(self):
        rig = Rig().activate()
        rig.send("SHUTDOWN", {"phase": "ARM_OFF"})
        rig.advance(60199)
        self.assertEqual(rig.model.state, "SHUTTING_DOWN")
        rig.advance(60200)
        self.assertEqual(rig.model.fault, "ARM_OFF_HEARTBEAT_LOST")

    def test_uv_without_hb_exact_five_second_dwell_and_pulse(self):
        rig = Rig()
        rig.inputs["battery_mv"] = 13050
        rig.model.step(0, rig.inputs)
        rig.advance(4999)
        self.assertNotEqual(rig.model.state, "OFF")
        rig.advance(5000)
        self.assertEqual(rig.model.fault, "UNDERVOLTAGE_NO_HEARTBEAT")

    def test_uv_live_hb_is_linux_responsibility(self):
        rig = Rig().activate()
        rig.inputs["battery_mv"] = 13050
        rig.advance(8000, heartbeat=True)
        self.assertEqual(rig.model.state, "ACTIVE")
        self.assertFalse(rig.model.outputs["pico_off"])

    def test_uv_dwell_resets_on_recovery_and_invalid_calibration(self):
        rig = Rig()
        rig.inputs["battery_mv"] = 12800
        rig.advance(4000)
        rig.inputs["battery_mv"] = 13100
        rig.advance(4200)
        rig.inputs["battery_mv"] = 12800
        rig.advance(8000)
        self.assertNotEqual(rig.model.state, "OFF")
        rig = Rig(calibration_valid=False)
        rig.inputs["battery_mv"] = 12800
        rig.advance(8000)
        self.assertNotEqual(rig.model.state, "OFF")

    def test_off_requires_physical_button_and_13600_to_restart(self):
        rig = Rig()
        rig.inputs["battery_mv"] = 12800
        rig.advance(6000)
        self.assertEqual(rig.model.state, "OFF")
        self.assertFalse(rig.send("ARM", {"qualified": True}))
        rig.inputs["button_pressed"] = True
        rig.advance(6100)
        self.assertEqual(rig.model.state, "OFF")
        rig.inputs["button_pressed"] = False
        rig.advance(6200)
        rig.inputs["battery_mv"] = 13600
        rig.inputs["button_pressed"] = True
        rig.advance(6300)
        self.assertEqual(rig.model.state, "SAFE")

    def test_fan_and_blower_hysteresis_fail_safe_invalid_host_temp(self):
        rig = Rig().activate()
        self.assertFalse(rig.model.outputs["fan_en"])
        self.assertFalse(rig.model.outputs["blower_en"])
        rig.inputs["panel_temp_c"] = 45
        rig.advance(220)
        rig.send("HB", {"soc_temp_c": 60})
        self.assertTrue(rig.model.outputs["fan_en"])
        self.assertTrue(rig.model.outputs["blower_en"])
        rig.inputs["panel_temp_c"] = 42
        rig.advance(240)
        rig.send("HB", {"soc_temp_c": 55})
        self.assertTrue(rig.model.outputs["fan_en"])
        self.assertTrue(rig.model.outputs["blower_en"])
        rig.inputs["panel_temp_c"] = 40
        rig.advance(260)
        rig.send("HB", {"soc_temp_c": 50})
        self.assertFalse(rig.model.outputs["fan_en"])
        self.assertFalse(rig.model.outputs["blower_en"])
        rig.send("HB", {"soc_temp_c": None})
        self.assertTrue(rig.model.outputs["fan_en"])

    def test_panel_hot_no_unproven_dimming_output(self):
        rig = Rig().activate()
        rig.inputs["panel_temp_c"] = 60
        rig.advance(220)
        self.assertEqual(rig.model.outputs["brightness_limit_pct"], 50)
        rig.inputs["panel_temp_c"] = 68
        rig.advance(240)
        self.assertEqual(rig.model.fault, "PANEL_HOT")
        self.assertFalse(rig.model.outputs["disp_en"])
        self.assertTrue(rig.model.outputs["mcp_reset"])

    def test_battery_gate_is_13050_inclusive_on_arm_and_uv_fallback(self):
        rig = Rig()
        rig.inputs["battery_mv"] = 13051
        rig.advance(6000)
        self.assertEqual(rig.model.state, "SAFE")
        self.assertTrue(rig.send("ARM", {"qualified": True}))

    def test_low_battery_while_armed_cannot_mask_thermal_or_fan_trips(self):
        for field, value, reason in (("panel_temp_c", 80, "PANEL_HOT"),
                                     ("case_temp_c", 75, "CASE_HOT"),
                                     ("fan_stalled", True, "FAN_STALLED")):
            rig = Rig().activate()
            rig.inputs["battery_mv"] = 12800
            rig.inputs[field] = value
            rig.advance(220, heartbeat=True)
            self.assertEqual(rig.model.fault, reason, field)
            self.assertTrue(rig.model.outputs["mcp_reset"])
            self.assertTrue(rig.model.outputs["fan_en"])
            self.assertTrue(rig.model.outputs["blower_en"])
            self.assertFalse(rig.model.outputs["disp_en"], field)  # Thermal trips drop DISP12.

    def test_case_hot_and_fan_stall_trips_keep_display_off_until_new_arm(self):
        for field, value, reason in (("case_temp_c", 61, "CASE_HOT"),
                                     ("fan_stalled", True, "FAN_STALLED")):
            rig = Rig().activate()
            self.assertTrue(rig.model.outputs["disp_en"])
            rig.inputs[field] = value
            rig.advance(220, heartbeat=True)
            self.assertEqual((rig.model.state, rig.model.fault), ("TRIPPED", reason))
            self.assertFalse(rig.model.outputs["disp_en"], field)
            rig.inputs[field] = READY.get(field, False)  # Cooled / tach back: still latched.
            rig.advance(1000)
            self.assertFalse(rig.model.outputs["disp_en"], field)
            self.assertTrue(rig.send("TRIP"))  # Relabelled fault cannot relight the console.
            self.assertEqual(rig.model.fault, "HOST_TRIP")
            rig.advance(1020)
            self.assertFalse(rig.model.outputs["disp_en"], field)
            self.assertTrue(rig.send("ARM", {"qualified": True}))
            self.assertEqual(rig.model.state, "WARMING")
            self.assertTrue(rig.model.outputs["disp_en"], field)

    def test_physical_restart_after_thermal_trip_and_off_relights_console(self):
        rig = Rig().activate()
        rig.inputs["case_temp_c"] = 75
        rig.advance(220, heartbeat=True)
        self.assertEqual(rig.model.fault, "CASE_HOT")
        self.assertTrue(rig.send("SHUTDOWN", {"phase": "ARM_OFF"}))
        rig.inputs["case_temp_c"] = 25.0
        rig.advance(60220)
        self.assertEqual(rig.model.fault, "ARM_OFF_HEARTBEAT_LOST")
        self.assertFalse(rig.model.outputs["disp_en"])
        rig.inputs["button_pressed"] = True
        rig.advance(60320)
        self.assertEqual((rig.model.state, rig.model.fault), ("SAFE", None))
        self.assertTrue(rig.model.outputs["disp_en"])

    def test_shutdown_after_physical_restart_gets_full_grace(self):
        for trigger in ("host", "button"):
            rig = Rig().activate()
            rig.send("SHUTDOWN", {"phase": "ARM_OFF"})
            rig.advance(300)
            rig.send("SHUTDOWN", {"phase": "OFF_NOW"})
            rig.advance(20300)
            self.assertEqual(rig.model.fault, "OFF_NOW_GRACE_ELAPSED")
            rig.inputs["button_pressed"] = True
            rig.advance(20400)
            self.assertEqual(rig.model.state, "SAFE")
            rig.inputs["button_pressed"] = False
            rig.advance(20500)
            if trigger == "host":
                self.assertTrue(rig.send("SHUTDOWN", {"phase": "ARM_OFF"}))
                self.assertEqual(rig.model.state, "SHUTTING_DOWN")
                rig.advance(20600)
                self.assertTrue(rig.send("SHUTDOWN", {"phase": "OFF_NOW"}))
                rig.advance(40599)
                self.assertEqual(rig.model.state, "SHUTTING_DOWN")
                self.assertFalse(rig.model.outputs["pico_off"])
                rig.advance(40600)
                self.assertEqual(rig.model.fault, "OFF_NOW_GRACE_ELAPSED")
            else:
                rig.inputs["button_pressed"] = True
                rig.advance(22100)
                rig.inputs["button_pressed"] = False
                self.assertEqual((rig.model.state, rig.model.fault), ("SHUTTING_DOWN", "BUTTON"))
                rig.advance(82040)
                self.assertEqual(rig.model.state, "SHUTTING_DOWN")
                self.assertFalse(rig.model.outputs["pico_off"])
                rig.advance(82060)
                self.assertEqual(rig.model.fault, "ARM_OFF_HEARTBEAT_LOST")

    def test_display_follows_q6a_outside_active_with_panel_hysteresis(self):
        rig = Rig()
        self.assertTrue(rig.model.outputs["disp_en"])  # SAFE console: ARM + HOLD.
        self.assertTrue(rig.model.outputs["mcp_reset"])
        rig.activate()
        rig.send("TRIP")
        self.assertEqual(rig.model.state, "TRIPPED")
        self.assertTrue(rig.model.outputs["mcp_reset"])
        self.assertTrue(rig.model.outputs["disp_en"])  # Fault and RECOVER + ARM visible.
        for panel, expected in ((67.9, True), (68, False), (65, False), (60.1, False),
                                (60, True), (None, False), (65, False), (59, True)):
            rig.inputs["panel_temp_c"] = panel
            rig.advance(rig.now + 20)
            self.assertEqual(rig.model.outputs["disp_en"], expected, panel)
        rig.inputs["q6a_on"] = False
        rig.advance(rig.now + 20)
        self.assertFalse(rig.model.outputs["disp_en"])

    def test_display_off_in_shutdown_off_and_on_stale_samples(self):
        rig = Rig()
        rig.send("SHUTDOWN", {"phase": "ARM_OFF"})
        self.assertFalse(rig.model.outputs["disp_en"])
        rig = Rig()
        rig.inputs["battery_mv"] = 12800
        rig.advance(6000)
        self.assertEqual(rig.model.state, "OFF")
        self.assertFalse(rig.model.outputs["disp_en"])
        rig = Rig()
        rig.model.receive({"v": 1, "t": "HB", "s": rig.model.session, "q": 0, "p": {}}, 250)
        self.assertTrue(rig.model.outputs["disp_en"])
        rig.model.receive({"v": 1, "t": "HB", "s": rig.model.session, "q": 1, "p": {}}, 251)
        self.assertFalse(rig.model.outputs["disp_en"])


class CalibrationTests(unittest.TestCase):
    def record(self):
        return from_two_points("abc123", 46000, 12600, 59900, 16400,
                               0.2, -0.1, "DMM-01/log-01")

    def test_crc_known_vector_and_record_roundtrip(self):
        import struct
        self.assertEqual(crc32(b"123456789"), 0xcbf43926)
        # Parse as the single-precision RP2040 port would; integer fields keep the CRC.
        record = json.loads(json.dumps(self.record()),
                            parse_float=lambda s: struct.unpack("<f", struct.pack("<f", float(s)))[0])
        cal = validate(record, "abc123")
        self.assertEqual(cal.battery_mv(46000), 12600)
        self.assertEqual(cal.battery_mv(59900), 16400)

    def test_corruption_revision_serial_and_missing_field_rejected(self):
        for mutate in (lambda r: r.update(offset_uv=20),
                       lambda r: r.pop("scale_nv_per_count")):
            record = self.record()
            mutate(record)
            with self.assertRaises(ValueError):
                validate(record, "abc123")
        with self.assertRaises(ValueError):
            validate(self.record(), "other-pico")
        with self.assertRaises(ValueError):
            validate(self.record(), "abc123", revision="old")

    def test_no_nominal_or_missing_or_unsafe_calibration_defaults(self):
        for record in ({}, None, {"v": 1}):
            with self.assertRaises(ValueError):
                validate(record, "abc123")
        with self.assertRaises(ValueError):
            from_two_points("abc123", 46000, 12600, 47000, 13000, 0, 0, "DMM")
        for raw in (0, 16, 65519, 65535):
            self.assertIsNone(validate(self.record(), "abc123").battery_mv(raw))

    def test_ntc_actual_table_gate_points_and_open_short(self):
        for temperature, resistance_kohm in ((25, 10), (60, 2.4734), (68, 1.8623)):
            raw = round(65535 * resistance_kohm / (10 + resistance_kohm))
            self.assertAlmostEqual(ntc_temperature(raw), temperature, delta=0.01)
        for raw in (0, 10, 65535, None, -1):
            self.assertIsNone(ntc_temperature(raw))

    def test_commissioning_bound_to_calibration_and_device(self):
        calibration = self.record()
        record = seal({"v": 1, "revision": REVISION, "serial": "abc123",
                       "calibration_crc32": calibration["crc32"],
                       "hardware_commissioned": True,
                       "qualification_record": "acceptance/unit-001.json"}, commissioning=True)
        self.assertTrue(commissioning_valid(record, calibration, "abc123"))
        self.assertFalse(commissioning_valid(record, calibration, "other"))
        record["hardware_commissioned"] = False
        self.assertFalse(commissioning_valid(record, calibration, "abc123"))


class AdapterTests(unittest.TestCase):
    def test_actual_adapter_hello_status_worst_case_fit_512_bytes(self):
        model = Supervisor()
        model.step(0, {"q6a_on": True, "battery_mv": 17500,
                       "panel_temp_c": -19.999999999999996,
                       "case_temp_c": 119.99999999999999})
        model.state = "SHUTTING_DOWN"
        model.fault = "UNDERVOLTAGE_NO_HEARTBEAT"
        model.reject_reason = "CONFIGURED_UNEXPECTED_OR_UNSAFE"
        for kind, payload in (("HELLO", hello_payload(model, "0123456789abcdef", "1234abcd")),
                              ("STATUS", status_payload(model, {"panel": 65535,
                                                               "battery": 65535, "case": 65535}))):
            frame = {"v": 1, "t": kind, "s": 0xffffffff, "q": 0xfffffffe, "p": payload}
            packet = encode_frame(frame)
            self.assertLessEqual(len(packet), 512)
            self.assertEqual(FrameDecoder().feed(packet), [frame])
            self.assertIn("mcp_reset", payload)

    def test_tick_wrap_unwraps_before_state_model(self):
        ticks = iter((250, 254, 3, 8))
        diff = lambda new, old: ((new - old + 128) % 256) - 128
        clock = TickClock(lambda: next(ticks), diff)
        self.assertEqual([clock.now_ms() for _ in range(3)], [4, 9, 14])

    def test_tick_gap_outside_half_period_rejected(self):
        ticks = iter((0, 200))
        clock = TickClock(lambda: next(ticks), lambda a, b: ((a-b+128) % 256)-128)
        with self.assertRaises(RuntimeError):
            clock.now_ms()

    def test_uart_short_write_and_timeout_handled(self):
        class UART:
            def __init__(self):
                self.data = bytearray()
            def write(self, value):
                self.data.extend(value[:2])
                return min(2, len(value))
        uart = UART()
        clock = iter(range(100))
        write_all(uart, b"abcdefg", lambda: next(clock), lambda a, b: a-b, lambda n: None)
        self.assertEqual(uart.data, b"abcdefg")
        uart.write = lambda value: None
        clock = iter(range(100))
        with self.assertRaises(OSError):
            write_all(uart, b"x", lambda: next(clock), lambda a, b: a-b,
                      lambda n: None, timeout_ms=5)

    def test_gpio_order_reset_polarity_and_q6a_power_off_tx_hiz(self):
        class Pin:
            IN, OUT, IRQ_FALLING = 0, 1, 4
            instances, created = {}, []
            def __new__(cls, gpio, *args, **kwargs):
                if gpio in cls.instances:
                    return cls.instances[gpio]
                obj = super().__new__(cls)
                cls.instances[gpio] = obj
                return obj
            def __init__(self, gpio, mode=None, value=None):
                self.gpio = gpio
                if not hasattr(self, "level"):
                    self.level = 0
                self.init(mode, value=value)
                self.created.append((gpio, mode, value))
            def init(self, mode, value=None):
                self.mode = mode
                if value is not None:
                    self.level = value
            def value(self, value=None):
                if value is not None:
                    self.level = value
                return self.level
            def irq(self, **kwargs):
                self.handler = kwargs["handler"]
        class ADC:
            def __init__(self, pin):
                self.pin = pin
            def read_u16(self):
                return 32768
        class UART:
            def __init__(self, *args, **kwargs):
                self.closed = False
            def deinit(self):
                self.closed = True
        class Machine:
            pass
        Machine.Pin, Machine.ADC, Machine.UART = Pin, ADC, UART
        hardware = Hardware(machine_module=Machine)
        self.assertEqual(Pin.created[:4], [(17, Pin.OUT, 1), (16, Pin.OUT, 0),
                                         (18, Pin.OUT, 1), (19, Pin.OUT, 1)])
        hardware.link_power(True)
        self.assertEqual(hardware.safe_boot.value(), 1)
        outputs = dict(Supervisor().outputs)
        outputs["mcp_reset"] = False
        hardware.apply(outputs)
        self.assertEqual(Pin.instances[17].value(), 0)
        hardware.link_power(False)
        self.assertEqual(Pin.instances[0].mode, Pin.IN)
        self.assertEqual(Pin.instances[15].mode, Pin.IN)
        hardware.fail_safe()
        self.assertEqual(Pin.instances[17].value(), 1)


class IMURelayTests(unittest.TestCase):
    def hello(self, session=50, seq=0):
        return {"v": 1, "t": "HELLO", "s": session, "q": seq,
                "p": {"role": "imu", "protocol": 1}}

    def event(self, session=50, seq=1, **overrides):
        imu = {"ok": True, "fresh": True, "quaternion": [0., 0., 0., 1.],
               "report_id": 5, "status": 3, "heading_accuracy_rad": 0.1,
               "at_ms": 100, "sample_seq": 1, "age_ms": 0}
        imu.update(overrides)
        return {"v": 1, "t": "EVENT", "s": session, "q": seq, "p": {"imu": imu}}

    def test_only_hello_then_fresh_valid_quaternion_forwarded(self):
        relay = IMURelay()
        bad = relay.receive(self.event(), 0)
        self.assertFalse(bad["imu"]["ok"])
        relay.receive(self.hello(), 10)
        value = relay.receive(self.event(), 20)
        self.assertTrue(value["imu"]["ok"])
        self.assertEqual(value["imu"]["pack_session"], 50)
        self.assertEqual(value["imu"]["pack_q"], 1)
        self.assertIsNone(relay.step(519))
        stale = relay.step(520)
        self.assertFalse(stale["imu"]["fresh"])
        self.assertIsNone(stale["imu"]["quaternion"])

    def test_gap_replay_and_new_session_need_new_hello(self):
        for message, error in ((self.event(seq=3), "IMU_SEQUENCE_GAP"),
                               (self.event(seq=0), "IMU_REPLAY"),
                               (self.event(session=51), "IMU_SESSION_NEEDS_HELLO")):
            relay = IMURelay()
            relay.receive(self.hello(), 0)
            relay.receive(self.event(), 20)
            self.assertEqual(relay.receive(message, 30)["imu"]["error"], error)
            self.assertFalse(relay.receive(self.event(seq=4), 40)["imu"]["ok"])
            relay.receive(self.hello(seq=5), 50)
            self.assertTrue(relay.receive(self.event(seq=6), 60)["imu"]["ok"])

    def test_stale_recovery_hello_is_given_fresh_report_window(self):
        relay = IMURelay()
        relay.receive(self.hello(), 0)
        relay.receive(self.event(), 20)
        relay.step(600)
        relay.receive(self.hello(seq=2), 1000)
        self.assertIsNone(relay.step(1010))
        self.assertTrue(relay.receive(self.event(seq=3), 1020)["imu"]["ok"])

    def test_invalid_report_does_not_poison_encoder_or_pass_cached_quaternion(self):
        for override in ({"quaternion": [float("nan"), 0, 0, 1]},
                         {"at_ms": "not-a-time"}, {"age_ms": 500},
                         {"status": 0},
                         {"ok": False, "error": "BNO_RESET"}):
            relay = IMURelay()
            relay.receive(self.hello(), 0)
            payload = relay.receive(self.event(**override), 20)
            self.assertFalse(payload["imu"]["ok"])
            frame = {"v": 1, "t": "EVENT", "s": 1, "q": 1, "p": payload}
            self.assertEqual(FrameDecoder().feed(encode_frame(frame)), [frame])

    def test_source_rx_and_forward_age_accumulate_without_reset(self):
        relay = IMURelay()
        relay.receive(self.hello(), 0)
        payload = relay.receive(self.event(age_ms=200), 20, rx_age_ms=100)
        self.assertEqual(payload["imu"]["age_ms"], 300)
        payload = relay.forwarding(payload, 20, 120)
        self.assertEqual(payload["imu"]["age_ms"], 400)
        self.assertTrue(payload["imu"]["fresh"])
        # The source/RX age also shortens the subsequent no-new-report deadline.
        self.assertIsNone(relay.step(219))
        self.assertFalse(relay.step(220)["imu"]["fresh"])

    def test_forward_age_exhaustion_cannot_emit_valid_attitude(self):
        relay = IMURelay()
        relay.receive(self.hello(), 0)
        payload = relay.receive(self.event(age_ms=200), 20, rx_age_ms=100)
        payload = relay.forwarding(payload, 20, 220)
        self.assertFalse(payload["imu"]["fresh"])
        self.assertIsNone(payload["imu"]["quaternion"])

    def test_loop_gap_requires_hello_before_resuming_reports(self):
        relay = IMURelay()
        relay.receive(self.hello(), 0)
        relay.receive(self.event(), 20)
        relay.invalidate("IMU_RX_SCHEDULING_GAP", 200)
        self.assertFalse(relay.receive(self.event(seq=2), 220)["imu"]["ok"])
        relay.receive(self.hello(seq=3), 300)
        self.assertTrue(relay.receive(self.event(seq=4), 320)["imu"]["ok"])


if __name__ == "__main__":
    unittest.main()
