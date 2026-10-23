"""Shutdown bridge: OFF_NOW only when qualified, clean OS poweroff on any HARDWARE shutdown."""
import unittest
from unittest.mock import patch

from srrx import poweroff


class Stop(Exception):
    pass


def status(state="SHUTTING_DOWN", qualified=True, mode="HARDWARE"):
    return {"ok": True, "data": {"mode": mode, "hardware_qualified": qualified, "pico": {"state": state}}}


class PoweroffBridgeTests(unittest.TestCase):
    def bridge(self, reply, execute=True, off_now=None):
        calls = []

        def request(socket, message):
            calls.append(message["op"])
            return reply if message["op"] == "status" else (off_now or {"ok": True})
        with patch("srrx.poweroff.request_once", side_effect=request), \
                patch("srrx.poweroff.subprocess.run") as run, \
                patch("srrx.poweroff.time.sleep", side_effect=Stop):
            try:
                code = poweroff.main(["--socket", "/run/test.sock"] + (["--execute"] if execute else []))
            except Stop:
                code = None  # still polling
        return code, calls, run

    def test_qualified_shutdown_requests_off_now_then_poweroff(self):
        code, calls, run = self.bridge(status())
        self.assertEqual((code, calls), (0, ["status", "off_now"]))
        run.assert_called_once_with(["/usr/bin/systemctl", "poweroff"], check=True)

    def test_unqualified_shutdown_powers_os_off_without_off_now(self):
        # HB stops when labd exits, so the Pico cuts on Q6A off / heartbeat loss.
        code, calls, run = self.bridge(status(qualified=False))
        self.assertEqual((code, calls), (0, ["status"]))
        run.assert_called_once_with(["/usr/bin/systemctl", "poweroff"], check=True)

    def test_refused_off_now_dry_run_simulation_and_running_state_take_no_os_action(self):
        for reply, execute, off_now, expected in ((status(), True, {"ok": False}, ["status", "off_now"]),
                                                  (status(qualified=False), False, None, ["status"]),
                                                  (status(mode="SIMULATION"), True, None, ["status"]),
                                                  (status(state="ACTIVE"), True, None, ["status"])):
            with self.subTest(reply=reply, execute=execute):
                code, calls, run = self.bridge(reply, execute, off_now)
                self.assertEqual(calls, expected)
                self.assertEqual(code, 0 if not execute else None)
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
