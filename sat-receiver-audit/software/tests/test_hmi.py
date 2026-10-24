import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import uuid

from srrx.hmi import (ConsoleController, DemoTransport, EN_OUTPUTS, ReceiverSimulation,
                      create_window, load_json, load_spectrum, spectrum_columns, location_callbacks, HMINavigation,
                      channel_rows, location_summary, learning_summary, pointing_summary, pass_plan_summary,
                      load_pass_plan, gnss_reset_summary, LearningJob, LearningRunner, learning_diagnostics,
                      run_learning_job, console_file_bytes, LEARNING_BUSY)

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


def gnss(**changes):
    """Live NMEA status at an unnamed test point (no city table)."""
    value = {"available": True, "source": "nmea", "origin": "nmea", "fresh": True, "live_fix": True, "mode": 3,
             "satellites": 8, "lat": 50.0, "lon": 10.0, "age_ms": 400, "reason": None}
    value.update(changes)
    return value


def pass_plan(**changes):
    entry = {"norad_id": 90100, "name": "ALIAS LRPT", "aos_utc": "2026-10-20T18:16:39.113Z",
             "tca_utc": "2026-10-20T18:24:16.572Z", "los_utc": "2026-10-20T18:31:51.583Z", "max_el_deg": 69.8,
             "aos_az_deg": 12.8, "tca_az_deg": 100.0, "los_az_deg": 204.8, "duration_s": 912.5,
             "omm_epoch_utc": "2026-10-20T06:00:00.000000Z", "omm_age_days": 0.5, "omm_age_warning": False,
             "time_verified": False, "observer_source": "nmea", "observer_age_ms": 300, "v_dipole_hint": "BISECTOR_NS",
             "predictor": {"skyfield": "1.55", "sgp4": "2.27"}}
    plan = {"schema_version": 1, "kind": "srrx_pass_plan", "start_utc": "2026-10-20T18:00:00.000Z", "hours": 24.0,
            "min_el_deg": 0.0, "time_verified": False,
            "observer": {"lat_rounded": 50.0, "lon_rounded": 10.0, "alt_rounded_m": 200.0, "rounding_deg": 0.1,
                         "source": "nmea", "age_ms": 300, "qualified_fix": False, "qualification_failures": []},
            "predictor": {"skyfield": "1.55", "sgp4": "2.27", "reference_versions_match": True},
            "passes": [entry, dict(entry, aos_utc="2026-10-20T19:57:10.761Z", tca_utc="2026-10-20T20:03:16.931Z",
                                   los_utc="2026-10-20T20:09:22.709Z", max_el_deg=14.2, v_dipole_hint="TIPS_NS",
                                   omm_age_warning=True)],
            "skipped": [], "window_edge_partial_passes": 1, "truncated": False,
            "scope": "Reference prediction from local OMM only."}
    plan.update(changes)
    return plan


class SimpleProcess:
    """A running SIM capture stand-in: records termination, starts nothing."""
    terminated = False

    def poll(self):
        return 0 if self.terminated else None

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.terminated = True


class GatedJob:
    """Stand-in learning call: blocks until released (at most 20 s), polling its checkpoint."""
    def __init__(self, result=None, checkpoints=True):
        self.release, self.started = threading.Event(), threading.Event()
        self.result, self.checkpoints, self.calls, self.thread = result, checkpoints, [], None

    def __call__(self, *args, checkpoint=None, **kwargs):
        self.calls.append(kwargs)
        self.thread = threading.get_ident()
        deadline = time.monotonic() + 20
        if self.checkpoints:
            checkpoint("fake", 0, 0)
        self.started.set()
        while not self.release.wait(.005) and time.monotonic() < deadline:
            if self.checkpoints:
                checkpoint("fake", 0, 0)
        return self.result() if callable(self.result) else self.result


def trained_model():
    from srrx import learning
    dataset = learning.empty_dataset()
    for family, label in enumerate(("analog_broadcast", "digital_broadcast")):
        for index in range(3):
            dataset = learning.annotate(dataset, learning._demo_frame(index, family), 0, 256, label,
                                        group_id=uuid.UUID(int=1 + family * 100 + index), user_confirmed=True)
    return learning.train(dataset, seed=7)


def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def finish_learning(app, window, seconds=10):
    """Let the background learning job end and commit through the UI-thread poll."""
    deadline = time.monotonic() + seconds
    while window.learning_runner.busy:
        if time.monotonic() > deadline:
            raise AssertionError("Learning job did not finish in %g s" % seconds)
        window._poll_learning()
        app.processEvents()
        time.sleep(.01)


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

    def test_location_tracker_and_gpsd_client_share_one_suspend_aware_clock(self):
        class Socket:
            closed = False
            def setblocking(self, value): pass
            def connect_ex(self, address): return 0
            def recv(self, size): raise BlockingIOError
            def close(self): self.closed = True
        fake, now_ns, clocks = Socket(), [5_000_000_000_000], []
        def gettime_ns(clock):
            clocks.append(clock)
            return now_ns[0]
        with patch.object(time, "CLOCK_BOOTTIME", 7, create=True), \
             patch.object(time, "clock_gettime_ns", gettime_ns, create=True), \
             patch("srrx.location.socket.socket", return_value=fake):
            callbacks, close = location_callbacks("127.0.0.1", 2947)
            try:
                callbacks["manual_location"](50.0, 30.0)
                self.assertFalse(callbacks["location"]()["live_fix"])
                self.assertFalse(fake.closed)  # start() and poll() read the same clock domain.
                now_ns[0] += 3600 * 10 ** 9  # One hour of host suspend: CLOCK_BOOTTIME keeps counting.
                value = callbacks["location"]()
                self.assertEqual((value["source"], value["age_ms"]), ("manual", 3_600_000))
                self.assertTrue(fake.closed)  # The gpsd handshake deadline includes the suspend.
            finally:
                close()
        self.assertEqual(set(clocks), {7})
        with patch.object(time, "CLOCK_BOOTTIME", None, create=True):
            callbacks, close = location_callbacks()  # Fallback where CLOCK_BOOTTIME is absent.
            try:
                callbacks["manual_location"](50.0, 30.0)
                self.assertEqual(callbacks["location"]()["source"], "manual")
            finally:
                close()

    def test_numbers_beyond_float_range_are_unavailable_not_overflow(self):
        huge = 10 ** 400  # Codec-valid JSON integers; float(huge) raises OverflowError.
        data = {"policy": {"outputs": {}, "branch_observability": {"RTLA": {"reservation_a": huge}}}}
        self.assertEqual(next(row for row in channel_rows(data, True) if row[0] == "RTL-A receiver")[4], "Not set")
        summary = location_summary({"available": True, "source": "gpsd", "lat": 1.0, "lon": 2.0,
                                    "age_ms": huge, "uncertainty_m": -huge})
        self.assertEqual(summary["age"], "Unknown")
        self.assertTrue(summary["uncertainty"].startswith("Unknown"))
        text = learning_summary({"label": "unknown_energy", "confidence": huge}, "infer", {"validation": {"accuracy": huge}})
        self.assertIn("Heuristic score unavailable", text)
        self.assertNotIn("Held-out check", text)

    def test_pointing_group_text_follows_the_location_gate(self):
        text = pointing_summary(gnss(), live=True, first_fix_stable=True)
        self.assertIn("Azimuth 159.6° (true north, not magnetic) · Elevation 30.7°", text)
        self.assertIn("rotate LNB +13.1° (+ = CCW viewed from behind", text)
        self.assertIn("Position: qualified GNSS fix (3D, >=6 satellites)", text)
        self.assertIn("not confirmed — elevation ≥5° but nominal slot 25.9E; TLE not verified", text)
        self.assertIn("beacon C/N0 in 5° steps", text)
        self.assertIn("Position age: 0.4 s", text)
        self.assertNotIn("50.0", text)  # Angles only; the position stays in the Location text above.
        gated = pointing_summary(gnss(mode=2, satellites=5), live=True, first_fix_stable=True)
        self.assertIn("GNSS fix not qualified — not a 3D fix; fewer than 6 satellites", gated)
        self.assertIn("Elevation 30.7°", gated)  # Shown, but labelled.
        self.assertIn("satellite count not reported", pointing_summary(gnss(satellites=None), live=True, first_fix_stable=True))
        self.assertIn("first-run 5 min stability window not complete", pointing_summary(gnss(), live=True))
        snapshot = pointing_summary(gnss(), live=False, first_fix_stable=True)
        self.assertTrue(snapshot.startswith("QO-100 · nominal slot 25.9°E · snapshot"))
        self.assertIn("fix not fresh", snapshot)
        self.assertNotIn("qualified GNSS fix (3D", snapshot)
        manual = pointing_summary({"available": True, "source": "manual", "lat": 38.0, "lon": -9.0, "fresh": False,
                                   "live_fix": False}, live=False, first_fix_stable=True)
        self.assertTrue(manual.startswith("QO-100 · nominal slot 25.9°E · manual entry"))
        self.assertIn("Position: not a GNSS fix (manual entry)", manual)
        self.assertIn("rotate LNB +36.5°", manual)
        self.assertEqual(pointing_summary({"available": False, "source": "none"}),
                         "QO-100 pointing unavailable — no usable position")
        self.assertEqual(pointing_summary(gnss(reason="MONOTONIC_TIME_REVERSED"), live=True),
                         "QO-100 pointing unavailable — location clock fault")
        self.assertIn("undefined within 1° of the equator", pointing_summary(gnss(lat=0.5), live=True))
        polar = pointing_summary(gnss(lat=85.0), live=True)
        self.assertIn("Visible from here: no — below the horizon", polar)
        self.assertIn("not applicable", polar)
        self.assertIn("Position age: Unknown", pointing_summary(gnss(age_ms=10 ** 400), live=True))
        jumped = pointing_summary(gnss(), live=True, first_fix_stable=True, jump_unconfirmed=True)
        self.assertIn("GNSS fix not qualified — moved more than 100 km from the last good fix — confirm the move", jumped)
        self.assertNotIn("confirm the move", pointing_summary(gnss(), live=False, first_fix_stable=True, jump_unconfirmed=True))
        self.assertIn("Elevation 30.7°", pointing_summary(gnss(alt_hae_m=10 ** 400), live=True, first_fix_stable=True))

    def test_gnss_reset_status_is_read_only_text(self):
        idle = {"state": "IDLE", "last_ms": 1000, "width_ms": 200, "release_ms": 1200, "last_width_ms": 200,
                "last_error": None, "release_due_ms": None, "pulses_15min": 1}
        self.assertEqual(gnss_reset_summary(idle, True),
                         "GNSS reset pulse: idle · last release proven · last pulse 200 ms · 1/3 pulses in 15 min")
        unproven = dict(idle, state="RELEASE_UNCONFIRMED", release_ms=None, last_width_ms=None,
                        last_error="GNSS_RESET_RELEASE_UNCONFIRMED")
        self.assertEqual(gnss_reset_summary(unproven, True),
                         "GNSS reset pulse: release not proven (Pico MCP RESET required) · 1/3 pulses in 15 min · "
                         "last error GNSS_RESET_RELEASE_UNCONFIRMED")
        recovered = dict(idle, last_width_ms=None, last_error="GNSS_RESET_RELEASE_UNCONFIRMED")
        self.assertIn("last release proven · pulse width unknown", gnss_reset_summary(recovered, True))
        self.assertIn("release time unknown", gnss_reset_summary(dict(idle, release_ms=None), True))
        self.assertIn("pulse in progress", gnss_reset_summary(dict(idle, state="ASSERTED"), True))
        self.assertEqual(gnss_reset_summary({"state": "IDLE", "last_ms": None, "release_ms": None, "pulses_15min": 0}, True),
                         "GNSS reset pulse: idle · no pulse in this labd session · 0/3 pulses in 15 min")
        for value, live in ((idle, False), (None, True), ([], True)):
            self.assertEqual(gnss_reset_summary(value, live), "GNSS reset pulse: status unavailable")
        odd = gnss_reset_summary(dict(idle, state="ARMED?", last_width_ms=10 ** 400, pulses_15min=10 ** 400,
                                      last_error="bad text\nwith lines"), True)
        self.assertEqual(odd, "GNSS reset pulse: unrecognised state · last error unrecognised")

    def test_pass_plan_snapshot_is_labelled_and_strictly_loaded(self):
        text = pass_plan_summary(pass_plan())
        self.assertTrue(text.startswith("Pass plan snapshot — not live · from 2026-10-20 18:00 UTC · 24 h · above 0°"))
        self.assertIn("Predictor Skyfield 1.55 / sgp4 2.27", text)
        self.assertIn("UTC not verified — times are provisional", text)
        self.assertIn("Observer rounded to 0.1°: 50.0, 10.0 · not a qualified fix", text)
        self.assertIn("ALIAS LRPT · AOS 10-20 18:16:39 · max 70° · LOS 18:31:51 · V-dipole bisector N-S", text)
        self.assertIn("V-dipole tips N-S", text)
        self.assertIn("elements old", text)
        self.assertIn("No complete pass", pass_plan_summary(pass_plan(passes=[])))
        self.assertIn("… 1 more passes", pass_plan_summary(pass_plan(), limit=1))
        self.assertIn("not the 1.55/2.27 reference", pass_plan_summary(pass_plan(predictor={"skyfield": "1.54", "sgp4": "2.27"})))
        with tempfile.TemporaryDirectory() as directory:
            good, bad = Path(directory) / "plan.json", Path(directory) / "bad.json"
            good.write_text(json.dumps(pass_plan()))
            self.assertEqual(load_pass_plan(good)["kind"], "srrx_pass_plan")
            observer = dict(pass_plan()["observer"], lat_rounded=50.012345)
            for value in (pass_plan(observer=observer), pass_plan(kind="other"), [1]):
                bad.write_text(json.dumps(value))
                with self.assertRaises(ValueError):
                    load_pass_plan(bad)
            bad.write_text('{"schema_version": 1, "schema_version": 1}')
            with self.assertRaises(ValueError):
                load_pass_plan(bad)

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


class LearningRunnerTests(unittest.TestCase):
    """The Qt-free background learning runner: one job in flight, cancel, close, outcomes."""
    def job(self, operation="train"):
        return LearningJob(operation, {"dataset": None, "scope": None}, base=(None, None))

    def test_one_job_in_flight_is_never_queued_and_is_returned_once(self):
        gate, runner = GatedJob(result="model", checkpoints=False), LearningRunner()
        with patch("srrx.learning.train", side_effect=gate), patch("srrx.hmi.learning_summary", return_value="ok"), \
                patch("srrx.hmi.learning_diagnostics", return_value=""):
            try:
                first = self.job()
                self.assertTrue(runner.submit(first))
                self.assertTrue(gate.started.wait(5))
                self.assertNotEqual(gate.thread, threading.get_ident())
                self.assertFalse(runner.submit(self.job()))
                runner.cancel()  # no checkpoint follows: the job is still finishing
                self.assertFalse(runner.submit(self.job()))
                self.assertIsNone(runner.poll())
            finally:
                gate.release.set()
            runner.thread.join(5)
            self.assertTrue(runner.busy)  # until the UI thread has polled the result
            self.assertFalse(runner.submit(self.job()))
            self.assertIs(runner.poll(), first)
            self.assertIsNone(runner.poll())
            self.assertEqual((first.outcome, first.value["result"], first.cancel.is_set()), ("ok", "model", True))
            self.assertEqual(len(gate.calls), 1)
            self.assertTrue(runner.submit(self.job()))
            runner.thread.join(5)

    def test_cancel_takes_effect_at_the_next_checkpoint_and_leaves_inputs_unchanged(self):
        from srrx import learning
        dataset = learning.annotate(learning.empty_dataset(), learning._demo_frame(1, 0), 0, 256, "analog_broadcast",
                                    group_id=uuid.UUID(int=1), user_confirmed=True)
        before = copy.deepcopy(dataset)
        job = LearningJob("annotate", {"dataset": dataset, "frame": learning._demo_frame(2, 1), "start": 0, "end": 256,
                                       "label": "digital_broadcast", "group_id": str(uuid.UUID(int=2)), "scope": None})
        job.cancel.set()
        runner = LearningRunner(start_thread=lambda target: target())  # synchronous
        self.assertTrue(runner.submit(job))
        self.assertIs(runner.poll(), job)
        self.assertEqual((job.outcome, job.value), ("cancelled", None))
        self.assertEqual(dataset, before)
        gate, runner = GatedJob(result="model"), LearningRunner()
        with patch("srrx.learning.train", side_effect=gate):
            try:
                job = self.job()
                runner.submit(job)
                self.assertTrue(gate.started.wait(5))
                self.assertEqual(job.progress(), ("fake", 0, 0))
                runner.cancel()
                runner.thread.join(5)  # ends at its next checkpoint, not at release
                self.assertFalse(runner.thread.is_alive())
            finally:
                gate.release.set()
        self.assertEqual(runner.poll().outcome, "cancelled")

    def test_progress_reports_the_latest_checkpoint(self):
        job = self.job()
        self.assertEqual(job.progress(), ("starting", 0, 0))
        job.checkpoint("dataset frames", 3, 10)
        job.checkpoint("features", 4, 9)
        self.assertEqual(job.progress(), ("features", 4, 9))
        job.cancel.set()
        from srrx.learning import LearningCancelled
        with self.assertRaises(LearningCancelled):
            job.checkpoint("holdout", 0, 1)
        self.assertEqual(job.progress(), ("features", 4, 9))

    def test_close_returns_at_once_and_the_thread_ends_when_released(self):
        gate, runner = GatedJob(checkpoints=False), LearningRunner()
        with patch("srrx.learning.train", side_effect=gate):
            try:
                runner.submit(self.job())
                self.assertTrue(gate.started.wait(5))
                started = time.monotonic()
                runner.close()
                self.assertLess(time.monotonic() - started, .1)
                self.assertTrue(runner.thread.is_alive())
                self.assertFalse(runner.submit(self.job()))
            finally:
                gate.release.set()
            runner.thread.join(2)
            self.assertFalse(runner.thread.is_alive())

    def test_unexpected_exceptions_come_back_as_error_outcomes(self):
        runner = LearningRunner(start_thread=lambda target: target())
        for error in (ZeroDivisionError("boom"), MemoryError(), ValueError("Rejected value")):
            with self.subTest(error=type(error).__name__), patch("srrx.learning.train", side_effect=error):
                job = self.job()
                runner.submit(job)
                self.assertIs(runner.poll(), job)
                self.assertEqual(job.outcome, "error")
                self.assertIs(job.error, error)
        with self.assertRaisesRegex(ValueError, "Unknown learning operation"):
            LearningJob("delete_dataset", {})
        with self.assertRaisesRegex(ValueError, "Unknown learning operation"):
            run_learning_job("transmit", {}, None)

    def test_learning_diagnostics_summarise_a_dataset_within_the_pane_limit(self):
        from srrx import learning
        dataset = learning.empty_dataset()
        for index in range(25):
            dataset = learning.annotate(dataset, learning._demo_frame(index, index % 3), 0, 256, "analog_broadcast",
                                        group_id=uuid.UUID(int=index + 1), user_confirmed=True)
        text = learning_diagnostics(dataset)
        self.assertLessEqual(len(text), 16000)
        value = json.loads(text)
        self.assertEqual((value["frames"], value["annotations"], value["sha256"]), (25, 25, dataset["sha256"]))
        self.assertEqual(value["last_annotations"], dataset["annotations"][-20:])
        self.assertNotIn("power_dbfs", text)
        model = trained_model()
        self.assertEqual(learning_diagnostics(model), json.dumps(model, indent=2, ensure_ascii=False)[:16000])


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
            finish_learning(app, window)
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

    def test_pointing_group_follows_live_gate_snapshot_manual_and_failures(self):
        app = qt_app()
        from PySide6.QtWidgets import QFileDialog
        state = {"value": gnss(), "error": None}
        def location():
            if state["error"]:
                raise OSError(state["error"])
            return dict(state["value"])
        callbacks = {"location": location, "manual_location": lambda lat, lon: state.update(
            value={"available": True, "source": "manual", "lat": lat, "lon": lon, "fresh": False, "live_fix": False})}
        clock = [1000]
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        with patch("srrx.hmi._boot_ms", side_effect=lambda: clock[0]):
            window = create_window(controller, callbacks=callbacks, start_worker=False)
            try:
                self.assertIn("unavailable", window.pointing_text.text())
                window._heartbeat()
                self.assertIn("Elevation 30.7°", window.pointing_text.text())
                self.assertIn("first-run 5 min stability window not complete", window.pointing_text.text())
                for _ in range(300):  # Five minutes of a stable live 3D, 8-satellite fix, one sample per second.
                    clock[0] += 1000
                    window._live_location()
                self.assertIn("Position: qualified GNSS fix (3D, >=6 satellites)", window.pointing_text.text())
                self.assertIn("TLE not verified", window.pointing_text.text())
                with tempfile.TemporaryDirectory() as directory:
                    saved = Path(directory) / "position.json"
                    saved.write_text(json.dumps(gnss(lat=35.0, lon=33.0)))
                    with patch.object(QFileDialog, "getOpenFileName", return_value=(str(saved), "")):
                        window.open_location()
                    window._heartbeat()  # Pinned: the provider is polled, the snapshot stays shown.
                    text = window.pointing_text.text()
                    self.assertTrue(text.startswith("QO-100 · nominal slot 25.9°E · snapshot"))
                    self.assertIn("rotate LNB -10.1°", text)
                    self.assertIn("fix not fresh", text)
                    self.assertNotIn("Position: qualified", text)
                    plan, bad = Path(directory) / "plan.json", Path(directory) / "bad.json"
                    plan.write_text(json.dumps(pass_plan()))
                    bad.write_text(json.dumps(pass_plan(observer=dict(pass_plan()["observer"], lon_rounded=10.04))))
                    with patch.object(QFileDialog, "getOpenFileName", return_value=(str(plan), "")):
                        window.open_pass_plan()
                    self.assertTrue(window.pass_plan_text.text().startswith("Pass plan snapshot — not live"))
                    with patch.object(QFileDialog, "getOpenFileName", return_value=(str(bad), "")):
                        window.open_pass_plan()
                    self.assertIn("Pass plan rejected", window.pass_plan_text.text())
                window.live_location()
                self.assertIn("Position: qualified GNSS fix", window.pointing_text.text())
                state["error"] = "gpsd gone"
                window._heartbeat()
                self.assertEqual(window.pointing_text.text(), "QO-100 pointing unavailable — location provider failed")
                state["error"] = None
                window.latitude.setValue(38.0); window.longitude.setValue(-9.0)
                window.manual_location()
                self.assertIn("Position: not a GNSS fix (manual entry)", window.pointing_text.text())
                window._heartbeat()
                self.assertIn("rotate LNB +36.5°", window.pointing_text.text())
                self.assertIn("not a GNSS fix (manual entry)", window.pointing_text.text())
            finally:
                window.close(); app.processEvents()

    def test_provider_outage_restarts_the_first_run_window_and_jumps_need_confirmation(self):
        app = qt_app()
        from PySide6.QtWidgets import QMessageBox
        state = {"value": gnss(), "error": None}
        def location():
            if state["error"]:
                raise OSError(state["error"])
            return dict(state["value"])
        clock = [1000]
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        with patch("srrx.hmi._boot_ms", side_effect=lambda: clock[0]):
            window = create_window(controller, callbacks={"location": location}, start_worker=False)
            try:
                def run(seconds):
                    for _ in range(seconds):
                        clock[0] += 1000
                        window._live_location()
                run(200)
                state["error"] = "gpsd gone"  # shorter than the 5 s gap rule, still a failed sample
                run(1)
                state["error"] = None
                run(299)  # 499 s of good samples in all, but the outage restarted the window
                self.assertIn("first-run 5 min stability window not complete", window.pointing_text.text())
                run(2)  # 300 s after the first good sample that followed the outage
                self.assertIn("Position: qualified GNSS fix", window.pointing_text.text())
                self.assertFalse(window.jump_button.isEnabled())
                state["value"] = gnss(lat=51.35)  # ~150 km from the last good fix
                run(1)
                self.assertIn("confirm the move", window.pointing_text.text())
                self.assertNotIn("Position: qualified", window.pointing_text.text())
                self.assertTrue(window.jump_button.isEnabled())
                with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No):
                    window.confirm_position_jump()
                run(1)
                self.assertIn("confirm the move", window.pointing_text.text())
                with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
                    window.confirm_position_jump()
                self.assertIn("Position: qualified GNSS fix", window.pointing_text.text())
                self.assertFalse(window.jump_button.isEnabled())
                run(1)
                self.assertIn("Position: qualified GNSS fix", window.pointing_text.text())
            finally:
                window.close(); app.processEvents()

    def test_gnss_reset_status_on_the_location_page_follows_labd(self):
        app = qt_app()
        controller, backend, clock = active()
        backend.data["policy"]["gnss_reset"] = {"state": "RELEASE_UNCONFIRMED", "last_ms": 1000, "width_ms": 200,
                                                "release_ms": None, "last_width_ms": None, "pulses_15min": 1,
                                                "release_due_ms": None, "last_error": "GNSS_RESET_RELEASE_UNCONFIRMED"}
        clock.now += .25
        controller.poll()
        window = create_window(controller, start_worker=False)
        try:
            window.render_state(controller.status())
            self.assertIn("release not proven (Pico MCP RESET required)", window.gnss_reset_text.text())
            backend.failure = OSError("timed out")
            clock.now += .25
            controller.poll()
            window.render_state(controller.status())
            self.assertEqual(window.gnss_reset_text.text(), "GNSS reset pulse: status unavailable")
            # Display only: no control on the page sends a gnss_reset request.
            from PySide6.QtWidgets import QPushButton
            self.assertFalse([b for b in window.findChildren(QPushButton) if "reset" in b.text().lower()])
            self.assertFalse(any(r.get("op") == "gnss_reset" for r in backend.requests))
        finally:
            window.close(); app.processEvents()

    def test_session_scope_latch_shows_only_out_of_scope_and_guards_learning(self):
        app = qt_app()
        from srrx import learning, scope_policy
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        with self.assertRaisesRegex(ValueError, "ScopeLatch"):
            create_window(controller, start_worker=False, scope_latch=object())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artemis.json"
            data = json.dumps({"v": 1, "kind": "srrx_artemis_mirror", "source": "artemis-db", "db_version": "v74",
                               "entries": [{"name": "Fixture", "categories": ["Military"],
                                            "ranges_hz": [[150.001e6, 150.002e6]]}]}).encode()
            path.write_bytes(data)
            latch = scope_policy.ScopeLatch(scope_policy.ArtemisDB.load(path, hashlib.sha256(data).hexdigest()))
        window = create_window(controller, start_worker=False, scope_latch=latch)
        try:
            self.assertIs(window.scope_latch, latch)
            self.assertTrue(window.accept_frame(frame()))  # 100 MHz: shown as before
            self.assertIn("centre 100000000 Hz", window.spec_note.text())
            window.teach_confirm.setChecked(True)
            # The SIM capture runs; a new stop aborts it and discards its frame file.
            window.receiver_job.path.write_text("{}")
            process = SimpleProcess()
            window.receiver_job.process = process
            for stopped in (frame(center=150000000), frame(center=300000000)):  # Artemis stop; masked band
                with self.subTest(center=stopped["center_hz"]):
                    self.assertFalse(window.accept_frame(stopped))
                    self.assertEqual(window.spec_note.text(), "out of scope")
                    self.assertIsNone(window.frame)
                    self.assertFalse(window.teach_confirm.isChecked())
                    self.assertEqual((window.plot.rows, window.plot.message), ([], "out of scope"))
                    window.learning_action("infer")
                    self.assertNotRegex(window.learning_text.toPlainText(), r"\d")
            self.assertTrue(process.terminated)
            self.assertFalse(window.receiver_job.path.exists())
            self.assertIsNone(window.receiver_job.process)
            # Starting a SIM capture on a stopped span is refused before any process starts.
            window.center.setValue(150000000)
            window.rate.setValue(48000)
            with patch("srrx.hmi.subprocess.Popen", side_effect=AssertionError("capture started")):
                window.start_capture()
            self.assertEqual(window.rx_note.text(), "out of scope")
            # Annotate, train and classify all receive the session latch.
            self.assertTrue(window.accept_frame(frame()))
            window.teach_confirm.setChecked(True)
            window.model, seen = trained_model(), []
            with contextlib.ExitStack() as stack:
                for name in ("annotate", "train", "infer"):
                    def spy(*args, _real=getattr(learning, name), _name=name, **kwargs):
                        seen.append((_name, kwargs.get("scope")))
                        return _real(*args, **kwargs)
                    stack.enter_context(patch.object(learning, name, side_effect=spy))
                for operation in ("annotate", "infer", "train"):
                    window.learning_action(operation)
                    finish_learning(app, window)
            # Each background job gets its own detached copy; the UI thread keeps the latch.
            self.assertEqual([(name, isinstance(scope, scope_policy.ScopeLatch) and scope is not latch)
                              for name, scope in seen], [("annotate", True), ("infer", True), ("train", True)])
            self.assertEqual({scope.base_generation for _, scope in seen}, {latch.latch_generation})
            self.assertEqual(len(window.dataset["annotations"]), 1)
            # A stop latched elsewhere in the session (e.g. on the tuned span) refuses the label.
            latch.stop(99.99e6, 100.01e6)
            window.teach_confirm.setChecked(True)
            before = window.dataset
            window.learning_action("annotate")
            self.assertEqual(window.learning_text.toPlainText(), "Rejected: Annotation span is out of scope")
            self.assertIs(window.dataset, before)
            window.learning_action("infer")
            self.assertEqual(window.learning_text.toPlainText(), "Rejected: Classification span is out of scope")
        finally:
            window.close(); app.processEvents()
        self.assertFalse(latch.unregister_abort(window.scope_abort))  # unregistered on close

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
            backend.data["pico"]["battery_mv"] = 10 ** 400  # Codec-valid; beyond float range.
            clock.now += .25
            controller.poll()
            window.render_state(controller.status())
            self.assertEqual(window.metric_values["battery"].text(), "Unavailable")
            backend.data["pico"]["battery_mv"] = 14800
            for stale in (False, None):
                if stale is None:
                    del backend.data["pico_fresh"]
                else:
                    backend.data.update(pico_fresh=stale, pico_age_ms=1200)
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
                    self.assertIn("last Pico status 1.2 s ago; ARM will be refused", window.fault_text.text())
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
            finish_learning(app, window)
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

    def test_long_learning_job_keeps_ui_heartbeat_and_hold(self):
        # The real worker, heartbeat and monotonic lease clock; only the learning call is a
        # 3 s pure-Python CPU loop.
        app = qt_app()
        from srrx import learning
        backend = Backend()
        controller = ConsoleController(backend)
        window = create_window(controller)
        model = trained_model()
        def busy_train(dataset, *, checkpoint=None, **kwargs):
            end, count, value = time.monotonic() + 3.0, 0, 1
            while time.monotonic() < end:
                count += 1
                value = (value * 31 + count) % 1000003
                if count % 1000 == 0:
                    checkpoint("busy", 0, 0)
            return model
        try:
            def wait(predicate, seconds=10):
                deadline = time.monotonic() + seconds
                while time.monotonic() < deadline and not predicate():
                    app.processEvents(); time.sleep(.02)
            def heartbeat(seconds):
                """Largest gap between GUI heartbeats over the period, and whether HOLD stayed on."""
                marks, held = [window.worker.ui_at], True
                end = time.monotonic() + seconds
                while time.monotonic() < end:
                    app.processEvents(); time.sleep(.02)
                    if window.worker.ui_at != marks[-1]:
                        marks.append(window.worker.ui_at)
                    held = held and controller.holding
                marks.append(time.monotonic())
                return max(b - a for a, b in zip(marks, marks[1:])), held
            wait(lambda: controller.status()["connected"])
            window.worker.submit("arm")  # Explicit operator ARM through the running worker.
            wait(lambda: controller.holding)
            backend.data["policy"]["armed"] = True
            backend.data["pico"]["state"] = "ACTIVE"
            wait(lambda: controller.holding and controller.arm_started is None)
            natural, held = heartbeat(1.0)
            self.assertTrue(held)
            leases = sum(request["op"] == "lease" for request in backend.requests)
            with patch.object(learning, "train", side_effect=busy_train):
                window.learning_action("train")
                self.assertTrue(window.learning_runner.busy)
                during, held = heartbeat(3.5)
                finish_learning(app, window)
            self.assertTrue(held)
            self.assertNotIn({"op": "disarm"}, backend.requests)
            self.assertGreaterEqual(sum(request["op"] == "lease" for request in backend.requests) - leases, 2)
            # Margin against the 1.5 s limit: under 1 s natively; a slow (emulated) host may add at most 0.5 s.
            self.assertLess(during, max(1.0, natural + .5), "heartbeat gap %.3f s, natural %.3f s" % (during, natural))
            self.assertIs(window.model, model)
            self.assertTrue(window.learning_text.toPlainText().startswith("Model ready"))
        finally:
            window.close()
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and window.worker.isRunning():
                app.processEvents(); time.sleep(.02)
            window.worker.stopping.set()
            window.worker.wait(1500)
            window.close(); app.processEvents()

    def test_learning_job_busy_state_refuses_a_second_job_and_cancels_cleanly(self):
        app = qt_app()
        from srrx import learning
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        window = create_window(controller, start_worker=False)
        gate = GatedJob(result=trained_model)
        try:
            self.assertEqual(len(window.learning_buttons), 7)
            self.assertFalse(window.learning_cancel.isEnabled())
            self.assertTrue(window.learning_progress.isHidden())
            with patch.object(learning, "train", side_effect=gate):
                window.learning_action("train")
                self.assertTrue(gate.started.wait(5))
                dataset = window.dataset
                self.assertEqual(window.learning_text.toPlainText(), "Training CPU model… — HOLD and DISARM stay available")
                self.assertFalse(any(button.isEnabled() for button in window.learning_buttons))
                self.assertTrue(window.learning_cancel.isEnabled())
                self.assertFalse(window.learning_progress.isHidden())
                window._poll_learning()
                self.assertRegex(window.learning_progress_note.text(), r"\Afake · \d+ s\Z")
                for second in (lambda: window.learning_action("infer"), lambda: window.learning_file("dataset", False)):
                    second()
                    self.assertEqual(window.learning_text.toPlainText(), LEARNING_BUSY)
                self.assertEqual(len(gate.calls), 1)
                window.learning_cancel.click()
                self.assertEqual(window.learning_text.toPlainText(), "Cancelling — the current step finishes first")
                finish_learning(app, window)
            self.assertEqual(window.learning_text.toPlainText(), "Cancelled — dataset and model unchanged")
            self.assertIs(window.dataset, dataset)
            self.assertIsNone(window.model)
            self.assertTrue(all(button.isEnabled() for button in window.learning_buttons))
            self.assertFalse(window.learning_cancel.isEnabled())
            self.assertTrue(window.learning_progress.isHidden())
        finally:
            gate.release.set()
            window.close(); app.processEvents()

    def test_scope_stop_while_a_job_runs_discards_its_result(self):
        app = qt_app()
        from srrx import learning, scope_policy
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        latch = scope_policy.ScopeLatch()
        window = create_window(controller, start_worker=False, scope_latch=latch)
        gate, real = GatedJob(checkpoints=False), learning.annotate
        def slow_annotate(*args, **kwargs):
            gate(*args, **kwargs)
            return real(*args, **kwargs)
        try:
            self.assertTrue(window.accept_frame(frame()))
            before = window.dataset = learning.empty_dataset()
            window.teach_confirm.setChecked(True)
            with patch.object(learning, "annotate", side_effect=slow_annotate):
                window.learning_action("annotate")
                self.assertTrue(gate.started.wait(5))
                latch.stop(170e6, 171e6)  # an operator stop elsewhere in the session, mid-job
                gate.release.set()
                finish_learning(app, window)
            text = window.learning_text.toPlainText()
            self.assertEqual(text, "Rejected: scope stop added while the job ran — run it again")
            self.assertNotRegex(text, r"\d")
            self.assertIs(window.dataset, before)
            # A classification of a frame that was replaced meanwhile is not shown for the new one.
            window.model, gate, real = trained_model(), GatedJob(checkpoints=False), learning.infer
            def slow_infer(*args, **kwargs):
                gate(*args, **kwargs)
                return real(*args, **kwargs)
            with patch.object(learning, "infer", side_effect=slow_infer):
                window.learning_action("infer")
                self.assertTrue(gate.started.wait(5))
                streamed = frame()
                streamed["power_dbfs"] = [-60.0] * 16
                self.assertTrue(window.accept_frame(streamed))
                gate.release.set()
                finish_learning(app, window)
            self.assertEqual(window.learning_text.toPlainText(), "Rejected: spectrum changed while classifying — run it again")
        finally:
            gate.release.set()
            window.close(); app.processEvents()

    def test_stop_found_by_background_training_latches_and_aborts_on_the_ui_thread(self):
        app = qt_app()
        from srrx import learning, scope_policy
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artemis.json"
            data = json.dumps({"v": 1, "kind": "srrx_artemis_mirror", "source": "artemis-db", "db_version": "v74",
                               "entries": [{"name": "Fixture", "categories": ["Military"],
                                            "ranges_hz": [[150.001e6, 150.002e6]]}]}).encode()
            path.write_bytes(data)
            latch = scope_policy.ScopeLatch(scope_policy.ArtemisDB.load(path, hashlib.sha256(data).hexdigest()))
        # Labelled in an earlier session without the database: only training meets the stop.
        dataset = learning.annotate(learning.empty_dataset(), frame(center=150000000), 0, 16, "analog_broadcast",
                                    group_id=uuid.uuid4(), user_confirmed=True)
        window = create_window(controller, start_worker=False, scope_latch=latch)
        class Process(SimpleProcess):
            thread = None
            def terminate(self):
                self.thread = threading.get_ident()
                super().terminate()
        try:
            window.dataset, process = dataset, Process()
            window.receiver_job.process = process  # a SIM capture is running
            window.learning_action("train")
            deadline = time.monotonic() + 10
            while not window.learning_runner.current.finished.is_set() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertEqual(window.learning_runner.current.outcome, "error")
            self.assertEqual((latch.stopped, process.terminated), (False, False))  # not until the UI thread adopts
            finish_learning(app, window)
            self.assertEqual(window.learning_text.toPlainText(), "Rejected: Training annotation span is out of scope")
            self.assertTrue(latch.stopped)
            self.assertTrue(process.terminated)
            self.assertEqual(process.thread, threading.get_ident())
            self.assertIsNone(window.model)
            self.assertIs(window.dataset, dataset)
            with contextlib.redirect_stderr(io.StringIO()) as journal:
                window._heartbeat()
            self.assertRegex(journal.getvalue(), r"\A\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ out of scope\n\Z")
        finally:
            window.close(); app.processEvents()

    def test_close_during_a_learning_job_disarms_without_waiting(self):
        app = qt_app()
        from srrx import learning
        backend = Backend()
        controller = ConsoleController(backend, Clock())
        controller.poll()
        window = create_window(controller, start_worker=False)
        gate = GatedJob(checkpoints=False)
        try:
            with patch.object(learning, "train", side_effect=gate):
                window.learning_action("train")
                self.assertTrue(gate.started.wait(5))
                thread = window.learning_runner.thread
                started = time.monotonic()
                window.close(); app.processEvents()
                self.assertLess(time.monotonic() - started, .5)
                self.assertEqual(backend.requests[-1], {"op": "disarm"})
                self.assertTrue(thread.is_alive())  # the close never waited for the job
                gate.release.set()
                thread.join(2)
                self.assertFalse(thread.is_alive())
        finally:
            gate.release.set()
            window.close(); app.processEvents()

    def test_learning_job_over_the_time_limit_is_cancelled(self):
        app = qt_app()
        from srrx import learning
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        window = create_window(controller, start_worker=False)
        gate = GatedJob(result=trained_model)
        try:
            with patch("srrx.hmi.LEARNING_JOB_MAX_S", .2), patch.object(learning, "train", side_effect=gate):
                window.learning_action("train")
                finish_learning(app, window)
            self.assertEqual(window.learning_text.toPlainText(), "Learning job exceeded 0.2 s — cancelled")
            self.assertIsNone(window.model)
        finally:
            gate.release.set()
            window.close(); app.processEvents()

    def test_dataset_and_model_files_go_through_the_runner_off_the_control_thread(self):
        app = qt_app()
        from PySide6.QtWidgets import QFileDialog
        threads = []
        class Spy(Backend):
            def __call__(self, request):
                threads.append(threading.get_ident())
                return super().__call__(request)
        controller = ConsoleController(Spy(), Clock())
        controller.poll()
        window = create_window(controller, start_worker=False)
        def file(kind, save, path):
            name = "getSaveFileName" if save else "getOpenFileName"
            with patch.object(QFileDialog, name, return_value=(str(path), "")):
                window.learning_file(kind, save)
                finish_learning(app, window)
            return window.learning_text.toPlainText()
        try:
            with tempfile.TemporaryDirectory() as directory:
                directory = Path(directory)
                window.model = model = trained_model()
                self.assertTrue(window.accept_frame(frame(size=1024)))
                window.teach_confirm.setChecked(True)
                window.learning_action("annotate")
                finish_learning(app, window)
                window.learning_action("infer")
                finish_learning(app, window)
                self.assertTrue(window.learning_text.toPlainText().startswith(("UNKNOWN", "Analog", "Digital")))
                saved = window.dataset
                self.assertEqual(file("dataset", True, directory / "dataset.json"), "Dataset saved")
                self.assertEqual(console_file_bytes(saved), (directory / "dataset.json").stat().st_size)
                self.assertEqual(file("model", True, directory / "model.json"), "Model saved")
                window.dataset = window.model = None
                self.assertTrue(file("dataset", False, directory / "dataset.json").startswith("Dataset ready"))
                self.assertEqual(window.dataset, saved)
                self.assertNotIn("power_dbfs", window.learning_diagnostics.toPlainText())
                self.assertTrue(file("model", False, directory / "model.json").startswith("Model ready"))
                self.assertEqual(window.model, model)
                # Over the console limit a save is still refused, and nothing is written.
                with patch("srrx.hmi.MAX_FILE_BYTES", console_file_bytes(saved) - 1):
                    self.assertEqual(file("dataset", True, directory / "big.json"),
                                     "Rejected: Metadata exceeds console size limit")
                self.assertFalse((directory / "big.json").exists())
                (directory / "bad.json").write_text('{"v": 1, "v": 2}')
                current = window.dataset
                self.assertEqual(file("dataset", False, directory / "bad.json"), "Rejected: Duplicate JSON key")
                self.assertIs(window.dataset, current)
        finally:
            window.close(); app.processEvents()
        self.assertEqual(set(threads), {threading.get_ident()})  # labd is only ever called from this thread

    def test_in_session_dataset_is_capped_at_the_console_file_limit(self):
        app = qt_app()
        from srrx import learning
        from PySide6.QtWidgets import QFileDialog
        controller = ConsoleController(Backend(), Clock())
        controller.poll()
        window = create_window(controller, start_worker=False)
        shaped = frame(size=1024)
        shaped["power_dbfs"] = [-90.0 + (index * 7919 % 101) / 5 for index in range(1024)]  # distinct boxes
        try:
            self.assertTrue(window.accept_frame(shaped))
            window.teach_confirm.setChecked(True)
            window.learning_action("annotate")
            finish_learning(app, window)
            limit = console_file_bytes(window.dataset) + 64  # room for one frame, not one more box
            window.dataset = learning.empty_dataset()
            with patch("srrx.hmi.MAX_FILE_BYTES", limit):
                window.teach_confirm.setChecked(True)
                window.learning_action("annotate")
                finish_learning(app, window)
                accepted = window.dataset
                self.assertEqual(len(accepted["annotations"]), 1)
                window.bin_start.setValue(300); window.bin_end.setValue(556)
                window.teach_confirm.setChecked(True)
                window.learning_action("annotate")
                finish_learning(app, window)
                self.assertEqual(window.learning_text.toPlainText(), "Rejected: Dataset would exceed the 2 MiB console "
                                 "limit — save it; larger datasets need the learning CLI")
                self.assertIs(window.dataset, accepted)
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "dataset.json"
                    with patch.object(QFileDialog, "getSaveFileName", return_value=(str(path), "")):
                        window.learning_file("dataset", True)
                        finish_learning(app, window)
                    self.assertEqual(window.learning_text.toPlainText(), "Dataset saved")
                    self.assertLessEqual(path.stat().st_size, limit)
                    self.assertEqual(learning.validate_dataset(load_json(path)), accepted)  # the console reads it back
        finally:
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


def view_renderer():
    spec = importlib.util.spec_from_file_location("srrx_tool_render_hmi_views", ROOT / "tools/render_hmi_views.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ViewRendererTests(unittest.TestCase):
    """tools/render_hmi_views.py gates; the full render itself runs only as the Linux tool."""
    def test_refuses_to_write_when_targeted_tests_fail(self):
        renderer = view_renderer()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "views"
            with patch.object(renderer.sys, "platform", "linux"), \
                 patch.object(renderer, "targeted_tests", side_effect=renderer.RenderFailure("1 failed")), \
                 patch.object(renderer, "render", side_effect=AssertionError("rendered after failed tests")), \
                 patch("builtins.print"):
                self.assertEqual(renderer.main(["--output", str(output)]), 1)
            self.assertFalse(output.exists())

    def test_targeted_summary_must_show_every_test_passing(self):
        renderer = view_renderer()
        good = {"total": 52, "passed": 52, "skipped": 0, "failed": 0, "qt_render": True, "real_qt_worker_close": True}
        for change, accepted in (({}, True), ({"failed": 1, "passed": 51}, False), ({"skipped": 2, "passed": 50}, True),
                                 ({"qt_render": False}, False), ({"real_qt_worker_close": False}, False),
                                 ({"total": 0, "passed": 0}, False), ({"passed": 51}, False)):
            with self.subTest(change=change):
                summary = dict(good, **change)
                completed = subprocess.CompletedProcess([], 0, stdout=b"noise\n" + json.dumps(summary).encode() + b"\n")
                with patch.object(renderer.subprocess, "run", return_value=completed):
                    if accepted:
                        self.assertEqual(renderer.targeted_tests(), {key: summary[key] for key in
                                         ("total", "passed", "skipped", "qt_render", "real_qt_worker_close")})
                    else:
                        with self.assertRaises(renderer.RenderFailure):
                            renderer.targeted_tests()
        with patch.object(renderer.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, stdout=b"")):
            with self.assertRaises(renderer.RenderFailure):
                renderer.targeted_tests()

    def test_report_keeps_the_committed_hmi_views_schema(self):
        renderer = view_renderer()
        committed = json.loads((ROOT / "verification/hmi-views/report.json").read_text(encoding="utf-8"))
        views = [{"page": page, "file": "%02d-%s.png" % (index, page), "width": 1100, "height": 800,
                  "bytes": 1, "sha256": "0" * 64} for index, page in enumerate(renderer.PAGES, 1)]
        value = renderer.report(views, {"pyside6": "6", "qt": "6", "qt_platform": "offscreen", "backend": "SIMULATION"},
                                {"total": 1, "passed": 1, "skipped": 0, "qt_render": True, "real_qt_worker_close": True},
                                "0" * 64, ROOT / "verification/hmi-views")
        self.assertEqual(list(value), list(committed))
        self.assertEqual(set(value["targeted_tests"]), set(committed["targeted_tests"]))
        self.assertEqual([(v["page"], v["path"]) for v in value["views"]],
                         [(v["page"], v["path"]) for v in committed["views"]])
        self.assertEqual([set(v) for v in value["views"]], [set(v) for v in committed["views"]])
        self.assertEqual((value["status"], value["physical_tests_performed"], value["hardware_devices_opened"]),
                         ("PASS_OFFSCREEN_SIMULATION", False, False))


if __name__ == "__main__":
    unittest.main()
