"""srrx-timegate: two fixed chronyc requests for labd's peer UID only, over a real AF_UNIX socket.

chronyc is never executed here (an injected runner records the argv); selecting PPS
in a real chronyd is a QEMU guest check and, with real PPS, a Q6A gate.
"""
import ast
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time
import unittest
from unittest import mock

from srrx import timegate
from srrx.locationd import bind_socket
from srrx.timegate import Gate, argv_for, run_chronyc, serve_one

PROJECT = Path(__file__).resolve().parents[2]
BASE = ["/usr/bin/chronyc", "-n", "-h", "/run/chrony/chronyd.sock"]


class GateTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.codes = []

    def runner(self, argv):
        self.calls.append(list(argv))
        return self.codes.pop(0) if self.codes else 0

    def test_exact_fixed_argv_per_request(self):
        self.assertEqual([list(a) for a in argv_for("PPS_SELECT")],
                         [BASE + ["selectopts", "PPS", "-noselect"], BASE + ["reselect"]])
        self.assertEqual([list(a) for a in argv_for("PPS_NOSELECT")],
                         [BASE + ["selectopts", "PPS", "+noselect"], BASE + ["reselect"]])
        with self.assertRaises(KeyError):
            argv_for("PPS_SELECT;reboot")

    def test_only_the_peer_uid_and_only_two_commands(self):
        gate = Gate(1234, self.runner)
        self.assertEqual(gate.handle(1235, b"PPS_SELECT"), {"ok": False, "error": "TIMEGATE_PEER_REFUSED"})
        self.assertEqual(gate.handle(0, b"PPS_SELECT"), {"ok": False, "error": "TIMEGATE_PEER_REFUSED"})  # not even root
        for bad in (b"pps_select", b"PPS_SELECT ", b"PPS", b"selectopts PPS -noselect", b"\xff", b""):
            with self.subTest(bad=bad):
                self.assertEqual(gate.handle(1234, bad), {"ok": False, "error": "TIMEGATE_UNKNOWN_COMMAND"})
        self.assertEqual(self.calls, [])
        self.assertEqual(gate.handle(1234, b"PPS_NOSELECT"), {"ok": True, "command": "PPS_NOSELECT"})
        self.assertEqual(self.calls, [BASE + ["selectopts", "PPS", "+noselect"], BASE + ["reselect"]])
        self.assertEqual(gate.last, ("PPS_NOSELECT", True))

    def test_a_failed_selectopts_stops_before_reselect(self):
        gate = Gate(1234, self.runner)
        self.codes = [1]
        self.assertEqual(gate.handle(1234, b"PPS_SELECT"),
                         {"ok": False, "command": "PPS_SELECT", "error": "TIMEGATE_CHRONYC_SELECTOPTS_EXIT"})
        self.assertEqual(len(self.calls), 1)
        self.codes = [0, "TIMEOUT"]
        self.assertEqual(gate.handle(1234, b"PPS_SELECT")["error"], "TIMEGATE_CHRONYC_RESELECT_TIMEOUT")
        self.assertEqual(gate.last, ("PPS_SELECT", False))

    def test_runner_is_bounded_without_shell_or_inherited_environment(self):
        seen = {}
        def run(argv, **kwargs):
            seen.update(kwargs, argv=argv)
            return subprocess.CompletedProcess(argv, 0)
        with mock.patch.object(timegate.subprocess, "run", side_effect=run):
            self.assertEqual(run_chronyc(argv_for("PPS_SELECT")[0]), 0)
        self.assertEqual(seen["timeout"], timegate.CHRONYC_TIMEOUT_S)
        self.assertEqual(seen["env"], {"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
        self.assertNotIn("shell", seen)
        self.assertIs(seen["stdin"], subprocess.DEVNULL)
        with mock.patch.object(timegate.subprocess, "run", side_effect=subprocess.TimeoutExpired("chronyc", 5)):
            self.assertEqual(run_chronyc(["x"]), "TIMEOUT")
        with mock.patch.object(timegate.subprocess, "run", side_effect=FileNotFoundError("chronyc")):
            self.assertEqual(run_chronyc(["x"]), "EXEC")

    def test_source_has_no_shell_network_or_request_derived_argument(self):
        source = (PROJECT / "software/srrx/timegate.py").read_text(encoding="utf-8")
        for forbidden in ("shell=True", "AF_INET", "os.system", "Popen", "format(", "% ("):
            self.assertNotIn(forbidden, source)
        tree = ast.parse(source)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and node.func.attr == "run"]
        self.assertEqual(len(calls), 1)  # the one bounded subprocess.run


class SocketTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="srrx-timegate-test-")
        self.addCleanup(folder.cleanup)
        os.chmod(folder.name, 0o700)
        self.path = os.path.join(folder.name, "timegate.sock")
        self.listener = bind_socket(self.path, 0o666, backlog=4)
        self.listener.setblocking(True)
        self.addCleanup(self.listener.close)
        self.calls = []

    def ask(self, gate, payload, outcome=None):
        replies = []
        def client():
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                sock.connect(self.path)
                try:
                    sock.sendall(payload)
                    replies.append(sock.recv(4096))
                    if outcome is not None:
                        outcome.append("closed" if replies[-1] == b"" else "reply")
                except socket.timeout:
                    replies.append(b"")
                    if outcome is not None:
                        outcome.append("client_timeout")
                except OSError:
                    replies.append(b"")
                    if outcome is not None:
                        outcome.append("error")
        thread = threading.Thread(target=client)
        thread.start()
        served = serve_one(self.listener, gate)
        thread.join(5)
        return served, (json.loads(replies[0]) if replies and replies[0] else None)

    def gate(self, uid):
        return Gate(uid, lambda argv: self.calls.append(list(argv)) or 0)

    def test_labd_peer_gets_one_reply_per_connection(self):
        served, reply = self.ask(self.gate(os.getuid()), b"PPS_SELECT\n")
        self.assertTrue(served)
        self.assertEqual(reply, {"ok": True, "command": "PPS_SELECT"})
        self.assertEqual(self.calls[0], BASE + ["selectopts", "PPS", "-noselect"])
        self.assertEqual(len(self.calls), 2)
        # Two lines and an oversize line are answered with the framing code, never run.
        for bad in (b"PPS_SELECT\nPPS_SELECT\n", b"P" * 40 + b"\n", b"PPS_SELECT\n\n"):
            with self.subTest(bad=bad):
                served, reply = self.ask(self.gate(os.getuid()), bad)
                self.assertEqual((served, reply), (True, {"ok": False, "error": "TIMEGATE_REQUEST_FRAMING"}))
        self.assertEqual(len(self.calls), 2)  # only the first request ran chronyc

    def test_unterminated_request_is_closed_after_the_read_timeout_without_chronyc(self):
        outcome = []
        with mock.patch.object(timegate, "READ_TIMEOUT_S", 0.3):
            started = time.monotonic()
            served, reply = self.ask(self.gate(os.getuid()), b"PPS_SELECT", outcome)
            elapsed = time.monotonic() - started
        self.assertEqual((served, reply, outcome), (False, None, ["closed"]))  # closed by the server, not the client
        self.assertGreaterEqual(elapsed, 0.3)
        self.assertLess(elapsed, 2.5)  # well before the client's own 3 s timeout
        self.assertEqual(self.calls, [])

    def test_other_peers_are_closed_unread(self):
        served, reply = self.ask(self.gate(os.getuid() + 54321), b"PPS_NOSELECT\n")
        self.assertFalse(served)
        self.assertIsNone(reply)
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
