import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from srrx.hmi import (ConsoleController, DemoTransport, EN_OUTPUTS, ReceiverSimulation,
                      create_window, load_json, load_spectrum, spectrum_columns, location_callbacks, HMINavigation,
                      channel_rows, location_summary, learning_summary)

ROOT = Path(__file__).resolve().parents[2]
LINUX = sys.platform.startswith("linux")


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


class Backend:
    def __init__(self):
        self.requests = []
        self.failure = None
        self.reject_lease = False
        self.data = {"mode": "SIMULATION", "pico": {"state": "SAFE"}, "pico_fresh": True,
                     "policy": {"armed": False, "fault": None, "mode": "field",
                                "outputs": {name: False for name in EN_OUTPUTS}},
                     "imu": {"ok": False, "fresh": False, "quaternion": None}}

    def __call__(self, request):
        self.requests.append(copy.deepcopy(request))
        if self.failure:
            raise self.failure
        op = request["op"]
        if op == "status":
            return {"ok": True, "data": copy.deepcopy(self.data)}
        if op == "lease" and self.reject_lease:
            return {"ok": False, "error": "Lease owned by another operator"}
        if op in ("arm", "recover"):
            self.data["last_error"] = None  # As labd: ARM clears last_error; a trip sets it.
        if op == "disarm":
            self.data["policy"]["armed"] = False
            self.data["policy"]["outputs"] = {name: False for name in EN_OUTPUTS}
        if op == "control":
            self.data["policy"]["outputs"][request["name"]] = request["value"]
        return {"ok": True}


def active():
    clock, backend = Clock(), Backend()
    controller = ConsoleController(backend, clock)
    controller.poll()
    assert controller.arm()["ok"]
    backend.data["policy"]["armed"] = True
    backend.data["pico"]["state"] = "ACTIVE"
    clock.now += .2
    controller.poll()
    return controller, backend, clock


def frame(center=100000000, size=16):
    return {"v": 1, "kind": "spectrum", "center_hz": center, "sample_rate_hz": 16000,
            "fft_size": size, "power_dbfs": [-70.0] * size, "valid": [True] * size,
            "relative_frequency_hz": [(index - size // 2) * 16000 / size for index in range(size)],
            "source": "SIMULATION", "sample_count": size}


def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def panel(sequence=1, presses=None, encoders=None, **changes):
    value = {"ok": True, "fresh": True, "age_ms": 100, "keys": 0,
             "presses": presses or [0] * 8, "encoders": encoders or [0, 0],
             "lux": 120.5, "lux_valid": True, "lux_age_ms": 600,
             "sequence": sequence, "generation": 0, "error": None}
    value.update(changes)
    return value


class PhysicalInputTests(unittest.TestCase):
    def test_counter_short_presses_dedupe_and_encoder_deltas(self):
        nav = HMINavigation()
        self.assertEqual(nav.consume(panel(presses=[1] * 8), 10)["events"], [])
        value = panel(2, presses=[2] * 8, encoders=[2, -1])
        result = nav.consume(value, 10)
        self.assertEqual(result["events"], list(nav.NAMES))
        self.assertEqual(result["encoders"], [2, -1])
        self.assertEqual(result["lux"], 120.5)
        self.assertEqual(nav.consume(value, 10)["events"], [])
        self.assertNotIn("arm", result["events"])

    def test_session_stale_and_sequence_reversal_rebaseline(self):
        nav = HMINavigation()
        nav.consume(panel(5), 10)
        self.assertEqual(nav.consume(panel(6, presses=[1] * 8), 11)["events"], [])
        nav.consume(panel(7, age_ms=500), 11)
        self.assertEqual(nav.consume(panel(8, presses=[3] * 8), 11)["events"], [])
        self.assertEqual(nav.consume(panel(1, presses=[4] * 8), 11)["events"], [])
        self.assertEqual(nav.consume(panel(9, presses=[10] * 8, generation=1), 11)["events"], [])
        self.assertEqual(nav.consume(panel(10, presses=[11] * 8, generation=1), 11)["events"], list(nav.NAMES))

    def test_modulo_wrap_and_implausible_jump_are_bounded(self):
        nav = HMINavigation()
        nav.consume(panel(1, presses=[65535] * 8, encoders=[2147483647, -2147483648]), 1)
        result = nav.consume(panel(2, presses=[0] * 8, encoders=[-2147483648, 2147483647]), 1)
        self.assertEqual(len(result["events"]), 8)
        self.assertEqual(result["encoders"], [1, -1])
        self.assertEqual(nav.consume(panel(3, presses=[500] * 8, encoders=[0, 0]), 1)["events"], [])
        self.assertEqual(nav.consume(panel(4, presses=[501] * 8, encoders=[0, 0]), 1)["events"], list(nav.NAMES))

    def test_bad_types_and_lux_age_never_make_gestures_or_brightness(self):
        nav = HMINavigation()
        for changes in ({"keys": True}, {"presses": [True] * 8}, {"encoders": [0, float("nan")]},
                        {"sequence": True}, {"generation": True}, {"generation": 65536},
                        {"age_ms": -1}, {"fresh": False}):
            self.assertEqual(nav.consume(panel(**changes), 1)["events"], [])
        self.assertIsNone(nav.consume(panel(lux_age_ms=2000), 1)["lux"])
        self.assertIsNone(nav.consume(panel(lux=float("nan")), 1)["lux"])

    def test_controller_advances_panel_age_and_clears_stale_counters(self):
        controller, backend, clock = active()
        backend.data["hmi"] = panel(age_ms=300)
        controller.poll()
        clock.now += .15
        self.assertGreaterEqual(controller.status()["data"]["hmi"]["age_ms"], 449)
        clock.now += .06
        value = controller.status()["data"]["hmi"]
        self.assertFalse(value["fresh"])
        self.assertNotIn("presses", value)


class ControllerTests(unittest.TestCase):
    def test_poll_and_reconnect_never_arm_or_renew(self):
        backend, clock = Backend(), Clock()
        controller = ConsoleController(backend, clock)
        self.assertFalse(controller.arm()["ok"])
        for _ in range(5):
            controller.poll()
            clock.now += .25
        self.assertEqual([r["op"] for r in backend.requests], ["status"] * 5)
        backend.failure = OSError("down")
        self.assertFalse(controller.poll()["connected"])
        backend.failure = None
        self.assertTrue(controller.poll()["connected"])
        self.assertNotIn("arm", [r["op"] for r in backend.requests])

    def test_explicit_arm_lease_every_second_and_output_mapping(self):
        controller, backend, clock = active()
        self.assertTrue(controller.status()["holding"])
        for _ in range(7):
            clock.now += .25
            controller.poll()
        leases = [r for r in backend.requests if r["op"] == "lease"]
        self.assertEqual(leases, [{"op": "lease", "value": {"ttl_ms": 3000}}] * 2)
        self.assertTrue(controller.command("control", name="EN_RTLA", value=True)["ok"])
        self.assertEqual(backend.requests[-1], {"op": "control", "name": "EN_RTLA", "value": True})
        self.assertTrue(controller.command("route", receiver="RTLA", value="RF3")["ok"])
        self.assertEqual(backend.requests[-1], {"op": "route", "receiver": "RTLA", "value": "RF3"})

    def test_fault_stops_hold_and_outputs_never_auto_rearm(self):
        controller, backend, clock = active()
        backend.data["policy"]["fault"] = "FAULT_RTLA"
        clock.now += .2
        view = controller.poll()
        self.assertFalse(view["holding"])
        self.assertEqual(backend.requests[-1], {"op": "disarm"})
        count = len([r for r in backend.requests if r["op"] == "lease"])
        backend.data["policy"]["fault"] = None
        for _ in range(8):
            clock.now += .25
            controller.poll()
        self.assertEqual(len([r for r in backend.requests if r["op"] == "lease"]), count)
        self.assertEqual(len([r for r in backend.requests if r["op"] == "arm"]), 1)
        self.assertFalse(controller.command("control", name="EN_RTLA", value=True)["ok"])

    def test_explicit_recover_discloses_arm_and_preserves_off_loads(self):
        backend, clock = Backend(), Clock()
        backend.data["policy"]["fault"] = "old fault"
        backend.data["pico"]["state"] = "TRIPPED"
        controller = ConsoleController(backend, clock)
        controller.poll()
        self.assertFalse(controller.arm()["ok"])
        self.assertTrue(controller.recover()["ok"])
        self.assertIn({"op": "recover"}, backend.requests)
        clock.now += .5
        self.assertTrue(controller.poll()["holding"])
        backend.data["policy"].update(armed=True, fault=None)
        backend.data["pico"]["state"] = "ACTIVE"
        clock.now += .5
        self.assertTrue(controller.poll()["holding"])
        self.assertFalse(any(backend.data["policy"]["outputs"].values()))
        self.assertFalse(any(r["op"] == "control" and r.get("value") for r in backend.requests))

    def test_handshake_abort_is_seen_through_first_fault_latch(self):
        # labd latches the first fault (new_pico_session) until ACTIVE; an
        # aborted ARM is visible only through last_error.
        backend, clock = Backend(), Clock()
        backend.data["policy"]["fault"] = backend.data["last_error"] = "new_pico_session"
        controller = ConsoleController(backend, clock)
        controller.poll()
        self.assertTrue(controller.arm()["ok"])
        clock.now += .25
        self.assertTrue(controller.poll()["holding"])
        backend.data["last_error"] = "pico_status_timeout"
        clock.now += .25
        self.assertFalse(controller.poll()["holding"])
        self.assertEqual(controller.error, "pico_status_timeout")
        self.assertIn("aborted", controller.notice)
        self.assertEqual(backend.requests[-1], {"op": "disarm"})

    @unittest.skipUnless(os.name == "posix", "srrx.link/srrx.hardware need POSIX termios/fcntl")
    def test_real_engine_aborted_handshake_stops_hold_within_one_poll(self):
        from srrx.engine import Engine
        from srrx.hardware import SimHardware
        from srrx.link import SimLink
        engine, clock, now = Engine(SimHardware(), SimLink(ROOT)), Clock(), [0]
        def advance(seconds):
            end = now[0] + int(seconds * 1000)
            while now[0] < end:
                now[0] += 20
                engine.tick(now[0])
            clock.now += seconds
        requests = []
        def transport(request):
            requests.append(request["op"])
            return json.loads(json.dumps(engine.request(dict(request, _owner="uid:1000")), allow_nan=False))
        controller = ConsoleController(transport, clock)
        try:
            advance(.6)
            self.assertEqual(controller.poll()["data"]["pico"]["state"], "SAFE")
            engine.link.drop_link = True  # The supervisor link dies as ARM is sent.
            self.assertTrue(controller.arm()["ok"])
            advance(.75)
            view = controller.poll()
            self.assertFalse(engine.pending_arm)
            self.assertEqual(view["data"]["last_error"], "pico_status_timeout")
            self.assertEqual(view["data"]["policy"]["fault"], controller.arm_fault)
            self.assertFalse(view["holding"])
            self.assertEqual(requests[-1], "disarm")
            self.assertEqual(requests.count("lease"), 1)
        finally:
            controller.close()
            engine.close()

    def test_hold_press_during_arm_handshake_keeps_arm(self):
        backend, clock = Backend(), Clock()
        controller = ConsoleController(backend, clock)
        controller.poll()
        self.assertTrue(controller.arm()["ok"])
        count = len(backend.requests)
        self.assertTrue(controller.hold(True)["ok"])
        self.assertTrue(controller.holding)
        self.assertIsNotNone(controller.arm_started)
        self.assertEqual(len(backend.requests), count)
        for _ in range(11):
            clock.now += .25
            controller.poll()
        self.assertFalse(controller.holding)  # The handshake deadline still applies.
        self.assertIn({"op": "disarm"}, backend.requests)

    def test_link_error_clears_only_after_fresh_disarmed_status(self):
        backend, clock = Backend(), Clock()
        controller = ConsoleController(backend, clock)
        controller.poll()
        backend.failure = OSError("timed out")
        clock.now += .25
        self.assertEqual(controller.poll()["error"], "timed out")
        backend.failure = None
        clock.now += .25
        self.assertIsNone(controller.poll()["error"])
        controller, backend, clock = active()
        backend.failure = OSError("timed out")
        clock.now += .25
        self.assertFalse(controller.poll()["holding"])
        backend.failure = None
        for _ in range(3):
            clock.now += .25
            self.assertIn("Disarm unconfirmed", controller.poll()["error"])  # labd still reports armed.
        backend.data["policy"]["armed"] = False
        clock.now += .25
        self.assertIsNone(controller.poll()["error"])
        self.assertFalse(controller.command("control", name="EN_RTLA", value=True)["ok"])
        clock.now += .25
        self.assertIsNotNone(controller.poll()["error"])  # A command rejection is not a link error.

    def test_confirmation_status_reports_only_accepted_values(self):
        controller, backend, _ = active()
        self.assertFalse(controller.command("confirmations", value={"bench_loads": True})["ok"])
        self.assertFalse(controller.status()["confirmations"]["bench_loads"])
        self.assertTrue(controller.command("confirmations", value={"boni_connected": True})["ok"])
        self.assertEqual(controller.status()["confirmations"],
                         {"bench_loads": False, "boni_connected": True, "boni_profile": False})
        controller.disarm()
        self.assertFalse(any(controller.status()["confirmations"].values()))

    def test_handshake_timeout_and_new_fault_stop_lease(self):
        for new_fault in (False, True):
            backend, clock = Backend(), Clock()
            controller = ConsoleController(backend, clock)
            controller.poll(); controller.arm()
            if new_fault:
                backend.data["policy"]["fault"] = "new fault"
                clock.now += .25
                controller.poll()
            else:
                for _ in range(11):
                    clock.now += .25
                    controller.poll()
            self.assertFalse(controller.holding)
            self.assertIn({"op": "disarm"}, backend.requests)

    def test_rejected_lease_or_timeout_stops_immediately(self):
        for failure in ("reject", "timeout", "malformed"):
            controller, backend, clock = active()
            if failure == "reject":
                backend.reject_lease = True
            elif failure == "timeout":
                backend.failure = OSError("socket timeout")
            else:
                backend.data["policy"]["armed"] = "true"
            clock.now += 1.0
            view = controller.poll()
            self.assertFalse(view["holding"])
            self.assertIn({"op": "disarm"}, backend.requests)

    def test_poll_gap_and_backwards_clock_stop_hold(self):
        controller, backend, clock = active()
        clock.now += 2
        self.assertFalse(controller.poll()["holding"])
        controller, backend, clock = active()
        clock.now -= 1
        self.assertFalse(controller.poll()["holding"])
        self.assertIn({"op": "disarm"}, backend.requests)

    def test_shutdown_close_and_stop_hold_always_disarm(self):
        controller, backend, _ = active()
        self.assertTrue(controller.command("shutdown")["ok"])
        self.assertEqual(backend.requests[-2:], [{"op": "disarm"}, {"op": "shutdown"}])
        self.assertFalse(controller.holding)
        controller, backend, _ = active()
        controller.close(); controller.close()
        self.assertEqual(backend.requests[-1], {"op": "disarm"})
        self.assertTrue(controller.closed)
        self.assertFalse(controller.arm()["ok"])

    def test_strict_whitelist_and_bool_types_no_request_leaks(self):
        controller, backend, _ = active()
        invalid = [("control", {"name": "CHG_INHIBIT", "value": False}),
                   ("control", {"name": "EN_RTLA", "value": 1}),
                   ("control", {"name": "EN_RTLA", "value": True, "_owner": "root"}),
                   ("route", {"receiver": "TX", "value": "RF1"}),
                   ("route", {"receiver": "RTLA", "value": "RF5"}),
                   ("relay", {"value": 3}), ("mode", {"value": "raw"}),
                   ("confirmations", {"value": {"bench_loads": 1}}),
                   ("sim", {"name": "drop_link", "value": True}), ("off_now", {})]
        count = len(backend.requests)
        for op, fields in invalid:
            self.assertFalse(controller.command(op, **fields)["ok"])
        self.assertEqual(len(backend.requests), count)

    def test_bench_requires_actual_lab_mode_and_explicit_confirmation(self):
        controller, backend, _ = active()
        self.assertFalse(controller.command("control", name="EN_AUX12", value=True)["ok"])
        self.assertFalse(controller.command("confirmations", value={"bench_loads": True})["ok"])
        backend.data["policy"]["mode"] = "lab"
        controller.poll()
        self.assertFalse(controller.command("route", receiver="RTLB", value="RF4")["ok"])
        self.assertTrue(controller.command("confirmations", value={"bench_loads": True})["ok"])
        self.assertTrue(controller.command("control", name="EN_AUX12", value=True)["ok"])
        self.assertTrue(controller.command("route", receiver="RTLB", value="RF4")["ok"])
        controller.disarm()
        self.assertFalse(controller.bench_confirmed)

    def test_off_park_available_without_hold(self):
        backend = Backend()
        controller = ConsoleController(backend, Clock())
        for op, fields in (("control", {"name": "EN_RTLA", "value": False}),
                           ("route", {"receiver": "RTLA", "value": "PARK"}), ("relay", {"value": "PARK"})):
            self.assertTrue(controller.command(op, **fields)["ok"])
        self.assertFalse(controller.hold()["ok"])

    def test_stale_status_and_imu_are_not_live_readouts(self):
        controller, backend, clock = active()
        backend.data["imu"] = {"ok": True, "fresh": True, "quaternion": [0., 0., 0., 1.], "age_ms": 300}
        controller.poll()
        clock.now += .21
        self.assertIsNone(controller.status()["data"]["imu"]["quaternion"])
        clock.now += 2
        self.assertTrue(controller.status()["stale"])
        self.assertFalse(controller.status()["holding"])

    def test_bad_response_during_command_stops_hold(self):
        controller, backend, _ = active()
        def bad(request):
            backend.requests.append(request)
            return {"ok": "yes"}
        controller.transport = bad
        self.assertFalse(controller.command("relay", value="HF")["ok"])
        self.assertFalse(controller.holding)
        self.assertEqual(backend.requests[-1], {"op": "disarm"})


class MetadataTests(unittest.TestCase):
    def test_product_channel_status_never_calls_reserve_a_measurement(self):
        backend = Backend()
        backend.data["policy"]["branch_observability"] = {"RTLA": {"current_unknown": True, "reservation_a": .12}}
        backend.data["policy"]["outputs"].update(EN_RTLA=True, SW_RTLA_A=False, SW_RTLA_B=True)
        row = next(row for row in channel_rows(backend.data, True) if row[0] == "RTL-A receiver")
        self.assertEqual(row, ("RTL-A receiver", "ON", "RF3", "Not measured", "120 mA"))
        self.assertEqual(next(row for row in channel_rows(backend.data, False) if row[0] == "RTL-A receiver")[1], "Unknown")

    def test_product_location_keeps_manual_and_snapshot_separate_from_live_fix(self):
        manual = location_summary({"available": True, "source": "manual", "lat": 50, "lon": 30})
        self.assertIn("50.000000° N", manual["position"])
        self.assertEqual(manual["fix"], "Manual — not a GNSS fix")
        self.assertIn("Unknown", manual["uncertainty"])
        snapshot = location_summary({"available": True, "source": "gpsd", "lat": 50, "lon": 30,
                                     "fresh": True, "live_fix": True, "age_ms": 1200}, live=False)
        self.assertNotEqual(snapshot["fix"], "Live GNSS fix")
        self.assertIn("snapshot", snapshot["source"])

    def test_product_learning_unknown_and_validation_scope_are_plain_language(self):
        model = {"provenance": {"train_groups": ["a", "b"], "validation_groups": ["c"], "source_counts": {"SIMULATION": 2}},
                 "validation": {"accuracy": .5, "samples": 2}}
        text = learning_summary({"label": "unknown_energy", "nearest_label": "amateur_digital", "confidence": 0.,
                                 "backend": "CPU", "npu": {"available": False, "reason": "not_requested"},
                                 "source": "SIMULATION"}, "infer", model)
        self.assertTrue(text.startswith("UNKNOWN"))
        self.assertIn("not a probability", text)
        self.assertIn("Training groups: 2", text)
        self.assertIn("not field accuracy", text)
        self.assertNotIn("{", text)

    def test_default_location_opens_no_socket_and_manual_is_never_gnss(self):
        callbacks, close = location_callbacks()
        try:
            self.assertFalse(callbacks["location"]()["available"])
            callbacks["manual_location"](50.4501, 30.5234)
            value = callbacks["location"]()
            self.assertEqual(value["source"], "manual")
            self.assertFalse(value["live_fix"])
            self.assertFalse(value["fresh"])
            self.assertIsNone(value["uncertainty_m"])
        finally:
            close()

    def test_json_limits_duplicates_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "meta.json"
            for content in (b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b'x' * (2 * 1024 * 1024 + 1)):
                path.write_bytes(content)
                with self.assertRaises((ValueError, UnicodeError)):
                    load_json(path)

    def test_deep_json_nesting_is_rejected_as_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "deep.json"
            path.write_text("[" * 100000 + "]" * 100000)
            for loader in (load_json, load_spectrum):
                with self.assertRaisesRegex(ValueError, "nesting"):
                    loader(path)

    def test_spectrum_json_jsonl_and_masked_pixel_remains_blank(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "frame.json"
            value = frame()
            value["valid"][2] = False
            path.write_text(json.dumps(value))
            safe = load_spectrum(path)
            self.assertIsNone(safe["power_dbfs"][2])
            self.assertIsNone(spectrum_columns(safe, 4)[0])
            self.assertEqual(spectrum_columns(safe, 4)[1:], [-70.] * 3)
            path.write_text(json.dumps(frame(250000000)) + "\n" + json.dumps(value) + "\n")
            self.assertEqual(load_spectrum(path), safe)
            self.assertEqual(spectrum_columns(frame(250000000)), [None] * 16)

    def test_receiver_simulation_whitelists_cli_and_bounded_lifetime(self):
        job = ReceiverSimulation()
        try:
            for center, rate in ((True, 1024000), (float("nan"), 1024000), (1e9, 0)):
                with self.assertRaises(ValueError):
                    job.start(center, rate)
            for rate in (47999, 56000001, 48000.5):
                with self.assertRaises(ValueError):
                    job.start(100000000, rate)
            self.assertIsNone(job.poll())
        finally:
            job.close()

    @unittest.skipUnless(LINUX, "stdio daemon pipes need Linux selectors")
    def test_demo_transport_waits_for_cold_start_then_ordinary_timeout(self):
        # Child stand-in answers each request after 1.5 s: longer than the
        # ordinary 1 s timeout, shorter than the one-off cold-start allowance.
        script = ("import sys, time\nwhile sys.stdin.readline():\n"
                  "    time.sleep(1.5)\n    sys.stdout.write('{\"ok\": true}\\n'); sys.stdout.flush()\n")
        popen = subprocess.Popen
        with patch("srrx.hmi.subprocess.Popen", side_effect=lambda args, **kw: popen([sys.executable, "-c", script], **kw)):
            transport = DemoTransport(timeout=1.0)
        try:
            self.assertEqual(transport({"op": "status"}), {"ok": True})
            with self.assertRaisesRegex(OSError, "timeout"):
                transport({"op": "status"})
            self.assertTrue(transport.closed)
            with self.assertRaisesRegex(OSError, "unavailable"):
                transport({"op": "status"})
        finally:
            transport.close()

    @unittest.skipUnless(LINUX, "stdio daemon pipes need Linux selectors")
    def test_real_stdio_demo_uses_actual_service_and_closes(self):
        transport = DemoTransport(timeout=20)
        controller = ConsoleController(transport)
        try:
            # A cold TCG interpreter can take seconds before its first reply.
            # Warm it without changing production freshness/handshake deadlines.
            initial = transport({'op': 'status'})
            self.assertTrue(initial['ok'], initial)
            self.assertEqual(initial['data']['mode'], 'SIMULATION')
            self.assertFalse(initial['data']['policy']['armed'])
            transport.timeout = 3
            view = controller.poll()
            self.assertTrue(view["connected"], view)
            self.assertEqual(view["data"]["mode"], "SIMULATION")
            self.assertFalse(view["data"]["policy"]["armed"])
            ready_at = time.monotonic() + 20
            while time.monotonic() < ready_at and (view["data"].get("session") is None or view["data"]["pico"].get("state") != "SAFE"):
                time.sleep(.05)
                view = controller.poll()
            self.assertIsNotNone(view['data'].get('session'), view)
            self.assertEqual(view['data']['pico'].get('state'), 'SAFE', view)
            armed = controller.arm()
            self.assertTrue(armed["ok"], armed)
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                time.sleep(.1)
                view = controller.poll()
                if view["data"]["policy"]["armed"]:
                    break
            self.assertTrue(view["data"]["policy"]["armed"])
            self.assertTrue(controller.holding)
            self.assertTrue(controller.disarm()["ok"])
        finally:
            controller.close()
            transport.close()
        self.assertIsNotNone(transport.process.poll())

    @unittest.skipUnless(LINUX, "labrx SIM subprocess targets the Linux host")
    def test_real_receiver_simulation_cli_produces_masked_frame(self):
        job = ReceiverSimulation()
        received = None
        try:
            job.start(100000000.0, 1024000.0)
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                value = job.poll()
                if value is not None:
                    received = value
                if job.process is None:
                    break
                time.sleep(.05)
            self.assertIsNotNone(received)
            self.assertEqual(received["source"], "SIMULATION")
            self.assertIsNone(job.process)
        finally:
            job.close()


@unittest.skipUnless(importlib.util.find_spec("PySide6"), "optional PySide6 is not installed")
class QtTests(unittest.TestCase):
    def test_panel_lock_rec_and_navigation_issue_no_power_request(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        backend, clock = Backend(), Clock()
        controller = ConsoleController(backend, clock)
        controller.poll()
        window = create_window(controller, start_worker=False)
        try:
            view = controller.status()
            view["data"].update(session=12, hmi=panel())
            controller.snapshot = copy.deepcopy(view["data"])
            window.render_state(view)
            view["data"]["hmi"] = panel(2, presses=[0, 0, 1, 1, 0, 1, 0, 0])
            controller.snapshot = copy.deepcopy(view["data"])
            before = len(backend.requests)
            window.render_state(view)
            self.assertTrue(window.worker.locked)
            self.assertFalse(window.tabs.isEnabled())
            self.assertEqual(window.mark_count, 1)
            window.worker.submit("arm")
            self.assertTrue(window.worker.commands.empty())
            self.assertEqual(len(backend.requests), before)
            self.assertFalse(any(button.isEnabled() for button in window.command_buttons.values()))
            from PySide6.QtWidgets import QMessageBox
            with patch.object(QMessageBox, "question", side_effect=AssertionError("dialog for a locked command")):
                window.action("arm")
                window.action("hold", {"enabled": True})
            self.assertIn("locked", window.input_message)
            self.assertTrue(window.worker.commands.empty())
            view["data"]["hmi"] = panel(3, presses=[0, 0, 1, 1, 0, 2, 0, 0])
            controller.snapshot = copy.deepcopy(view["data"])
            window.render_state(view)
            self.assertFalse(window.worker.locked)
            self.assertTrue(all(button.isEnabled() for button in window.command_buttons.values()))
        finally:
            window.close(); app.processEvents()

    def test_actual_offscreen_render_all_pages_and_close_disarm(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        backend = Backend()
        controller = ConsoleController(backend, Clock())
        controller.poll()
        window = create_window(controller, start_worker=False)
        try:
            window.show()
            window.accept_frame(frame())
            self.assertEqual(window.tabs.count(), 6)
            for index in range(window.tabs.count()):
                window.tabs.setCurrentIndex(index)
                app.processEvents()
                self.assertFalse(window.grab().isNull())
            self.assertIn("SIMULATION", window.banner.text())
            self.assertFalse(window.output_on_buttons["EN_RTLA"].isEnabled())
            self.assertTrue(window.overview.isHidden())
            self.assertEqual(window.channel_table.rowCount(), 14)
            window.teach_confirm.setChecked(True)
            window.learning_action("annotate")
            self.assertEqual(window.dataset["annotations"][0]["label"], "unknown_energy")
            self.assertTrue(window.learning_text.toPlainText().startswith("Dataset ready"))
            self.assertTrue(window.learning_diagnostics.isHidden())
        finally:
            window.close()
            app.processEvents()
        self.assertEqual(backend.requests[-1], {"op": "disarm"})

    def test_saved_location_stays_pinned_over_live_tracker(self):
        app = qt_app()
        from PySide6.QtWidgets import QFileDialog
        callbacks, close = location_callbacks()
        provider, calls = callbacks["location"], []
        callbacks["location"] = lambda: calls.append(1) or provider()
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        window = create_window(controller, callbacks=callbacks, start_worker=False)
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "position.json"
                path.write_text(json.dumps({"available": True, "source": "gpsd", "lat": 50.45, "lon": 30.52,
                                            "fresh": True, "live_fix": True, "age_ms": 1200}))
                with patch.object(QFileDialog, "getOpenFileName", return_value=(str(path), "")):
                    window.open_location()
            before = len(calls)
            window._heartbeat()
            window._heartbeat()
            self.assertEqual(len(calls) - before, 2)  # Still polled while pinned: gpsd keeps draining.
            self.assertIn("50.450000° N", window.location_text.text())
            self.assertIn("Saved position — no live fix", window.location_text.text())
            self.assertIn("paused", window.location_note.text())
            window.live_location()
            self.assertIn("No position available", window.location_text.text())
            window.latitude.setValue(10); window.longitude.setValue(20)
            window.manual_location()
            window._heartbeat()
            self.assertIn("10.000000° N", window.location_text.text())
            self.assertIn("Manual — not a GNSS fix", window.location_text.text())
        finally:
            window.close(); app.processEvents(); close()

    def test_location_note_follows_shown_source_and_keeps_rejections(self):
        app = qt_app()
        from PySide6.QtWidgets import QFileDialog
        state = {"value": None, "error": None}
        manual = {"available": True, "source": "manual", "lat": 10.0, "lon": 20.0, "fresh": False, "live_fix": False}
        gnss = {"available": True, "source": "gpsd", "lat": 50.0, "lon": 30.0, "fresh": True, "live_fix": True, "age_ms": 100}
        def location():
            if state["error"]:
                raise OSError(state["error"])
            return state["value"]
        callbacks = {"location": location, "manual_location": lambda lat, lon: state.update(value=dict(manual, lat=lat, lon=lon))}
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        window = create_window(controller, callbacks=callbacks, start_worker=False)
        try:
            window.latitude.setValue(10); window.longitude.setValue(20)
            window.manual_location()
            window._heartbeat()
            self.assertIn("Manual — not a GNSS fix", window.location_text.text())
            self.assertEqual(window.location_note.text(), "Manual position — not a GNSS fix")
            state["value"] = gnss  # The tracker prefers a fresh GNSS fix over the manual record.
            window._heartbeat()
            self.assertIn("Live GNSS fix", window.location_text.text())
            self.assertEqual(window.location_note.text(), "Live tracker position")
            with tempfile.TemporaryDirectory() as directory:
                bad, good = Path(directory) / "bad.json", Path(directory) / "saved.json"
                bad.write_text("{")
                good.write_text(json.dumps({"available": True, "source": "gpsd", "lat": 1.5, "lon": 2.5}))
                with patch.object(QFileDialog, "getOpenFileName", return_value=(str(bad), "")):
                    window.open_location()
                window._heartbeat(); window._heartbeat()
                self.assertIn("Position rejected", window.location_note.text())  # Unchanged live state keeps it.
                with patch.object(QFileDialog, "getOpenFileName", return_value=(str(good), "")):
                    window.open_location()
            state["error"] = "gpsd gone"
            window._heartbeat()
            self.assertIn("1.500000° N", window.location_text.text())  # A provider error keeps the pinned text.
            self.assertIn("paused", window.location_note.text())
            self.assertIn("gpsd gone", window.location_note.text())
            state["error"] = None
            window._heartbeat()
            self.assertEqual(window.location_note.text(), window.PINNED)
            window.live_location()
            self.assertIn("Live GNSS fix", window.location_text.text())
            self.assertEqual(window.location_note.text(), "Live tracker position")
        finally:
            window.close(); app.processEvents()

    def test_heartbeat_sources_fail_independently(self):
        app = qt_app()
        from PySide6.QtWidgets import QFileDialog
        calls = []
        def location():
            calls.append(1)
            if len(calls) > 2:
                raise OSError("gpsd gone")
            return {"available": True, "source": "gpsd", "lat": 1.0, "lon": 2.0,
                    "fresh": True, "live_fix": True, "age_ms": 100}
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        window = create_window(controller, callbacks={"location": location}, start_worker=False)
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "frame.json"
                path.write_text(json.dumps(frame()))
                with patch.object(QFileDialog, "getOpenFileName", return_value=(str(path), "")):
                    window.open_spectrum()
                    self.assertEqual(window.frame_file, path)
                    path.unlink()
                    window._heartbeat()
                    self.assertIsNone(window.frame_file)
                    self.assertIn("Tracked file lost", window.spec_note.text())
                    self.assertIn("Live GNSS fix", window.location_text.text())
                    window._heartbeat(); window._heartbeat()
                    self.assertEqual(len(calls), 3)
                    self.assertNotIn("Live GNSS fix", window.location_text.text())
                    self.assertIn("Location unavailable", window.location_text.text())
                    path.write_text(json.dumps(frame()))
                    window.open_spectrum()
                    with path.open("ab") as stream:
                        stream.write(b" " * (2 * 1024 * 1024))
                    window._heartbeat()
                    self.assertIsNone(window.frame_file)
                    self.assertIn("exceeds 2 MiB", window.spec_note.text())
        finally:
            window.close(); app.processEvents()

    def test_banner_and_supervisor_readouts_never_claim_unknown_state(self):
        app = qt_app()
        controller, backend, clock = active()
        backend.data["pico"].update(battery_mv=14800, case_temp_c=25.0, panel_temp_c=30.0)
        controller.poll()
        window = create_window(controller, start_worker=False)
        try:
            window.render_state(controller.status())
            self.assertEqual(window.metric_values["battery"].text(), "14.80 V")
            self.assertIn("CONTROL ARMED", window.banner.text())
            for stale in (False, None):
                if stale is None:
                    del backend.data["pico_fresh"]
                else:
                    backend.data["pico_fresh"] = stale
                clock.now += .25
                controller.poll()
                window.render_state(controller.status())
                self.assertEqual(window.metric_values["battery"].text(), "Unavailable")
                self.assertIn("Case unavailable", window.metric_values["temperature"].text())
                if stale is None:  # A labd without the field: withheld, but no stale/ARM claim.
                    self.assertIn("PICO FRESHNESS UNREPORTED", window.banner.text())
                    self.assertNotIn("STALE", window.banner.text())
                    self.assertIn("did not report Pico freshness", window.fault_text.text())
                    self.assertNotIn("ARM will be refused", window.fault_text.text())
                else:
                    self.assertIn("PICO STATUS STALE", window.banner.text())
                    self.assertIn("ARM will be refused", window.fault_text.text())
            backend.data["pico_fresh"] = True
            backend.failure = OSError("timed out")  # labd stays armed; DISARM cannot be confirmed.
            clock.now += .25
            controller.poll()
            window.render_state(controller.status())
            self.assertIn("CONTROL UNKNOWN", window.banner.text())
            self.assertIn("MODE UNKNOWN", window.banner.text())
            self.assertNotIn("CONTROL OFF", window.banner.text())
            self.assertIn("unconfirmed", window.fault_text.text())
            self.assertIn("Console: Disarm unconfirmed", window.fault_text.text())
            backend.failure = None
            backend.data["policy"].update(armed=False, fault="operator_disarm")
            clock.now += .25
            controller.poll()
            window.render_state(controller.status())
            self.assertIn("CONTROL OFF", window.banner.text())
            self.assertEqual(window.fault_text.text(), "Stopped by operator")
            for stale in (None, False):  # The labd protection fault stays visible without Pico freshness.
                backend.data.pop("pico_fresh", None)
                if stale is False:
                    backend.data["pico_fresh"] = False
                clock.now += .25
                controller.poll()
                window.render_state(controller.status())
                self.assertTrue(window.fault_text.text().endswith("\nStopped by operator"))
            backend.data["policy"]["fault"] = "new_pico_session"
            clock.now += .25
            controller.poll()
            window.render_state(controller.status())
            self.assertNotIn("ready", window.fault_text.text())  # Never "ready" without fresh Pico status.
        finally:
            window.close(); app.processEvents()

    @unittest.skipUnless(os.name == "posix", "srrx.link/srrx.hardware need POSIX termios/fcntl")
    def test_real_engine_pico_readouts_never_contradict_labd_freshness(self):
        app = qt_app()
        from srrx.engine import Engine
        from srrx.hardware import SimHardware
        from srrx.link import SimLink
        engine, clock, now = Engine(SimHardware(), SimLink(ROOT)), Clock(), [0]
        def advance(seconds):
            end = now[0] + int(seconds * 1000)
            while now[0] < end:
                now[0] += 20
                engine.tick(now[0])
            clock.now += seconds
        controller = ConsoleController(lambda request: json.loads(json.dumps(
            engine.request(dict(request, _owner="uid:1000")), allow_nan=False)), clock)
        window = create_window(controller, start_worker=False)
        try:
            for drop in (False, True):
                engine.link.drop_link = drop
                advance(.6)
                view = controller.poll()
                window.render_state(view)
                stale = engine.last_status_ms is None or engine.now_ms - engine.last_status_ms > 500  # labd's ARM refusal.
                self.assertEqual(stale, drop)
                battery, fault = window.metric_values["battery"].text(), window.fault_text.text()
                self.assertFalse("ARM will be refused" in fault and not stale)
                self.assertFalse(battery != "Unavailable" and stale)
                if "pico_fresh" in view["data"]:
                    self.assertEqual(battery == "14.80 V", not stale)
                    self.assertEqual("PICO STATUS STALE" in window.banner.text(), stale)
                else:
                    self.assertIn("PICO FRESHNESS UNREPORTED", window.banner.text())
        finally:
            window.close(); app.processEvents()
            engine.close()

    def test_streamed_frame_keeps_selection_and_annotates_confirmed_frame(self):
        app = qt_app()
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        window = create_window(controller, start_worker=False)
        try:
            window.accept_frame(frame(size=1024))
            window.bin_start.setValue(10); window.bin_end.setValue(600)
            window.teach_confirm.setChecked(True)
            newer = frame(size=1024)
            newer["power_dbfs"] = [-60.0] * 1024
            window.accept_frame(newer)  # Same geometry, as a streamed survey/SIM frame.
            self.assertEqual((window.bin_start.value(), window.bin_end.value()), (10, 600))
            self.assertTrue(window.teach_confirm.isChecked())
            window.learning_action("annotate")
            record = window.dataset["annotations"][0]
            self.assertEqual((record["start_bin"], record["end_bin"]), (10, 600))
            self.assertEqual(window.dataset["frames"][record["frame_sha256"]]["power_dbfs"][10], -70.0)
            window.teach_confirm.setChecked(True)
            window.bin_end.setValue(500)
            self.assertFalse(window.teach_confirm.isChecked())
            window.teach_confirm.setChecked(True)
            window.label.setCurrentIndex(1)
            self.assertFalse(window.teach_confirm.isChecked())
            window.teach_confirm.setChecked(True)
            window.accept_frame(frame(size=512))
            self.assertFalse(window.teach_confirm.isChecked())
            self.assertEqual((window.bin_start.value(), window.bin_end.value()), (0, 256))
        finally:
            window.close(); app.processEvents()

    def test_rejected_bench_confirmation_is_unticked(self):
        app = qt_app()
        controller, backend, _ = active()
        window = create_window(controller, start_worker=False)
        try:
            bench, boni = window.confirmation_checks[0], window.confirmation_checks[1]
            bench.setChecked(True)  # The operator's tap, rejected in field mode.
            self.assertFalse(controller.command("confirmations", value={"bench_loads": True})["ok"])
            window.render_state(controller.status())
            self.assertFalse(bench.isChecked())
            boni.setChecked(True)
            self.assertTrue(controller.command("confirmations", value={"boni_connected": True})["ok"])
            window.render_state(controller.status())
            self.assertTrue(boni.isChecked())
            controller.disarm()
            window.render_state(controller.status())
            self.assertFalse(boni.isChecked())
        finally:
            window.close(); app.processEvents()

    def test_worker_stop_warning_persists_and_commands_are_dropped(self):
        app = qt_app()
        controller, backend, _ = active()
        window = create_window(controller, start_worker=False)
        try:
            texts = [widget.text() for widget in window.tab_commands]
            for text in ("Apply route", "Apply HF relay", "Stage LAB", "OFF", "Bench loads connected and checked"):
                self.assertIn(text, texts)
            route = window.tab_commands[texts.index("Apply route")]
            route.click()  # In-tab commands go through action() while the worker is alive.
            self.assertEqual(window.worker.commands.get_nowait(), ("route", {"receiver": "RTLA", "value": "PARK"}))
            window._finished()
            window._heartbeat(); window._heartbeat()
            self.assertIn("Control worker stopped", window.banner.text())
            self.assertIn("NO CONNECTION", window.banner.text())
            self.assertIn("HOLD OFF", window.banner.text())
            self.assertFalse(any(button.isEnabled() for button in window.command_buttons.values()))
            self.assertFalse(any(widget.isEnabled() for widget in window.tab_commands))
            self.assertFalse(window.output_on_buttons["EN_RTLA"].isEnabled())
            window.worker.submit("control", {"name": "EN_RTLA", "value": True})
            window.action("hold", {"enabled": True})
            self.assertTrue(window.worker.commands.empty())
            self.assertIn("Control worker stopped", window.input_message)
            window.action("route", {"receiver": "RTLA", "value": "PARK"})
            self.assertIn("ROUTE not sent", window.input_message)
            self.assertTrue(window.worker.commands.empty())
        finally:
            window.close(); app.processEvents()

    def test_gui_heartbeat_stall_disarms_hold(self):
        # The touch-UI heartbeat (Worker.ui_at), not the controller poll gap:
        # the worker keeps polling while only the GUI thread stalls.
        app = qt_app()
        backend = Backend()
        controller = ConsoleController(backend, Clock())
        window = create_window(controller)
        try:
            def wait(predicate, seconds=10):
                deadline = time.monotonic() + seconds
                while time.monotonic() < deadline and not predicate():
                    app.processEvents(); time.sleep(.02)
            wait(lambda: controller.status()["connected"])
            window.worker.submit("arm")  # Explicit operator ARM through the running worker.
            wait(lambda: controller.holding)
            backend.data["policy"]["armed"] = True
            backend.data["pico"]["state"] = "ACTIVE"
            wait(lambda: controller.holding and controller.arm_started is None)
            wait(lambda: False, .5)  # Natural GUI heartbeats while ACTIVE.
            self.assertTrue(controller.holding)
            self.assertNotIn({"op": "disarm"}, backend.requests)
            time.sleep(2.0)  # GUI thread blocked: no heartbeat, no processEvents.
            self.assertFalse(controller.holding)
            self.assertIn({"op": "disarm"}, backend.requests)
            self.assertIn("heartbeat lost", controller.notice)
        finally:
            window.close()
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and window.worker.isRunning():
                app.processEvents(); time.sleep(.02)
            window.worker.stopping.set()
            window.worker.wait(1500)
            window.close(); app.processEvents()

    @unittest.skipUnless(LINUX, "stdio daemon pipes need Linux selectors")
    def test_worker_real_demo_arm_then_window_close_stops_service(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        transport = DemoTransport(timeout=1)
        controller = ConsoleController(transport)
        window = create_window(controller)
        try:
            window.show()
            # The first reply has the cold-start allowance; later ones keep 1 s.
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline and not controller.snapshot.get("session"):
                app.processEvents(); time.sleep(.02)
            window.worker.submit("arm")  # One explicit simulated operator action.
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and not controller.snapshot.get("policy", {}).get("armed"):
                app.processEvents(); time.sleep(.02)
            self.assertTrue(controller.holding)
            self.assertTrue(controller.snapshot["policy"]["armed"])
            window.close()
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and window.worker.isRunning():
                app.processEvents(); time.sleep(.02)
            self.assertFalse(window.worker.isRunning())
            self.assertFalse(controller.holding)
            self.assertTrue(controller.closed)
            self.assertIsNotNone(transport.process.poll())
        finally:
            window.worker.stopping.set()
            window.worker.wait(1500)
            transport.close()
            window.close(); app.processEvents()


if __name__ == "__main__":
    unittest.main()
