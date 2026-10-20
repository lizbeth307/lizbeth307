import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

from srrx.hmi import (ConsoleController, DemoTransport, EN_OUTPUTS, ReceiverSimulation,
                      create_window, load_json, load_spectrum, spectrum_columns, location_callbacks, HMINavigation,
                      channel_rows, location_summary, learning_summary)


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
        self.data = {"mode": "SIMULATION", "pico": {"state": "SAFE"},
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

    def test_ui_gap_and_backwards_clock_stop_hold(self):
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
            view["data"]["hmi"] = panel(3, presses=[0, 0, 1, 1, 0, 2, 0, 0])
            controller.snapshot = copy.deepcopy(view["data"])
            window.render_state(view)
            self.assertFalse(window.worker.locked)
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

    def test_worker_real_demo_arm_then_window_close_stops_service(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        transport = DemoTransport(timeout=1)
        controller = ConsoleController(transport)
        window = create_window(controller)
        try:
            window.show()
            deadline = time.monotonic() + 3
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
