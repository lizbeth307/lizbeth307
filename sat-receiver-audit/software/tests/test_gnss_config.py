"""srrx-gnss-config against a simulated LC76G on a real Linux PTY; systemctl is an injected fake.

The responder follows the reply layouts transcribed in srrx.lc76g (Quectel protocol
specification v1.5 via build/07 §18). It is not the receiver: the real reply fields,
$PQTMVERNO and the flash behaviour are GNSS-01/W-04 items on the Q6A, never claimed here.
"""
import ast
import fcntl
import json
import os
from pathlib import Path
import re
import select
import tempfile
import termios
import threading
import time
import unittest
from unittest import mock

from srrx import gnss_config, lc76g
from srrx.gnss_config import GnssConfigError, Port, configure, open_rw, run
from srrx.gnss_uart import GnssUartError, configure_raw_115200, raw_115200

PROJECT = Path(__file__).resolve().parents[2]


def clock():
    return int(time.monotonic() * 1000)


class FakeLC76G(threading.Thread):
    """Answers the allowlisted sentences on the PTY master and talks NMEA in between."""
    def __init__(self, master, **state):
        super().__init__(daemon=True)
        self.master = master
        self.state = dict(pps=("0", "0", "100", "1", "0", "0"), dgps="0", sbas="0", talking=True, replies=True,
                          sticky=False, refuse=None, received=[])
        self.state.update(state)
        self.stopping = threading.Event()
        self._buffer = bytearray()

    def send(self, body):
        os.write(self.master, (lc76g.sentence(body) + "\r\n").encode("ascii"))

    def answer(self, text):
        s = self.state
        s["received"].append(text)
        if not s["replies"]:
            return
        self.send("GNGSV,3,1,12,01,45,180,40")  # unrelated output between command and reply
        refuse = s["refuse"]
        if text == "$PQTMVERNO*58":
            self.send("PQTMVERNO,LC76GTESTVER01,2026/01/01,00:00:00")
        elif text == "$PQTMCFGPPS,R,1*6A":
            self.send("PQTMCFGPPS,OK,1," + ",".join(s["pps"][1:]))
        elif text == "$PQTMCFGPPS,W,1,1,100,3,0,0*70":
            if refuse == "pps":
                self.send("PQTMCFGPPS,ERROR,1")
                return
            if not s["sticky"]:
                s["pps"] = lc76g.PPS_FIELDS
            self.send("PQTMCFGPPS,OK")
        elif text in ("$PQTMSAVEPAR*5A",):
            self.send("PQTMSAVEPAR,OK")
        elif text == "$PQTMCFGMSGRATE,W,PQTMJAMMINGSTATUS,1,1*11":
            self.send("PQTMCFGMSGRATE,OK")
        elif text.startswith("$PAIR"):
            number = text[5:8]
            result = "2" if refuse == number else "0"
            if number in ("410", "400") and result == "0" and not s["sticky"]:
                s["sbas" if number == "410" else "dgps"] = "1" if number == "410" else "2"
            if number == "411":
                self.send("PAIR001,411,1")  # still processing: the final result follows
            self.send("PAIR001,%s,%s" % (number, result))
            if number == "401":
                self.send("PAIR401," + s["dgps"])
            elif number == "411":
                self.send("PAIR411," + s["sbas"])

    def run(self):
        last = 0
        while not self.stopping.is_set():
            ready = select.select([self.master], [], [], .02)[0]
            if ready:
                try:
                    self._buffer.extend(os.read(self.master, 4096))
                except OSError:
                    return
                while b"\n" in self._buffer:
                    raw, unused, rest = bytes(self._buffer).partition(b"\n")
                    self._buffer = bytearray(rest)
                    self.answer(raw.rstrip(b"\r").decode("ascii", "replace"))
            if self.state["talking"] and time.monotonic() - last > .1:
                last = time.monotonic()
                self.send("GNRMC,120000.000,V,,,,,,,150626,,,N,V")

    def stop(self):
        self.stopping.set()
        self.join(2)


class PtyCase(unittest.TestCase):
    def setUp(self):
        self.master, self.slave = os.openpty()
        self.addCleanup(os.close, self.master)
        self.addCleanup(os.close, self.slave)
        self.path = os.ttyname(self.slave)

    def receiver(self, **state):
        fake = FakeLC76G(self.master, **state)
        fake.start()
        self.addCleanup(fake.stop)
        return fake

    def port(self):
        fd = os.open(self.path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK | os.O_CLOEXEC)
        self.addCleanup(os.close, fd)
        configure_raw_115200(fd)
        return Port(fd, clock)


class SentenceTests(unittest.TestCase):
    def test_every_checksum_recomputes_and_parses(self):
        texts = [command.text for command in lc76g.ALLOWLIST] + list(lc76g.DOCUMENTED_NOT_SENT)
        self.assertEqual(len(set(texts)), 12)
        for text in texts:
            with self.subTest(text=text):
                body, checksum = text[1:].split("*")
                self.assertEqual("%02X" % lc76g.checksum(body), checksum)
                self.assertEqual(lc76g.sentence(body), text)
                self.assertIsNotNone(lc76g.parse(text.encode()))
                self.assertFalse(lc76g.forbidden(text.encode()))
        self.assertEqual(lc76g.sentence("PQTMCFGPPS,W,1,1,100,3,0,0"), "$PQTMCFGPPS,W,1,1,100,3,0,0*70")
        self.assertEqual(lc76g.sentence("PAIR006"), "$PAIR006*3C")

    def test_allowlist_and_forbidden_names_are_exactly_build07_section_18(self):
        text = (PROJECT / "build/07-pz-vstanovlennia.md").read_text(encoding="utf-8")
        section = text[text.index("## 18."):text.index("## 19.")]
        tokens = set(re.findall(r"\$P[A-Z0-9,]*(?:\*[0-9A-F]{2})?", section))
        sentences = {token for token in tokens if "*" in token}
        self.assertEqual(sentences, {command.text for command in lc76g.ALLOWLIST} | set(lc76g.DOCUMENTED_NOT_SENT))
        names = {token[1:].split(",")[0] for token in tokens if "*" not in token and re.match(r"\$PAIR\d", token)}
        self.assertEqual(names, set(lc76g.FORBIDDEN))
        for name in lc76g.FORBIDDEN:
            self.assertTrue(lc76g.forbidden(("$" + name + ",2,100*00").encode()))
            self.assertTrue(lc76g.forbidden(("$" + name).encode()))

    def test_parse_rejects_bad_frames(self):
        good = lc76g.sentence("PAIR001,400,0").encode()
        self.assertEqual(lc76g.parse(good), ("PAIR001", ["400", "0"]))
        self.assertEqual(lc76g.parse(lc76g.sentence("PQTMSAVEPAR").encode()), ("PQTMSAVEPAR", []))
        for bad in (good[:-1] + b"0", good + b"\r", b"PAIR001,400,0*00", good.replace(b"$", b"$$"),
                    b"$" + b"A" * 300 + b"*00", "$PAIR001,é*00".encode("utf-8"), None, "text"):
            with self.subTest(bad=bad):
                self.assertIsNone(lc76g.parse(bad))

    def test_reply_matching(self):
        dgps = lc76g.DGPS_SBAS
        self.assertIsNone(dgps.match(("GNRMC", ["x"])))
        self.assertIsNone(dgps.match(("PAIR001", ["401", "0"])))  # another command's ack
        self.assertEqual(dgps.match(("PAIR001", ["400", "0"])), ("ok", ["400", "0"]))
        self.assertIsNone(dgps.match(("PAIR001", ["400", "1"])))
        self.assertEqual(dgps.match(("PAIR001", ["400", "4"])), ("error", "LC76G_PAIR_RESULT_4"))
        read = lc76g.DGPS_READ
        self.assertIsNone(read.match(("PAIR001", ["401", "0"])))  # the ack alone does not complete a read
        self.assertEqual(read.match(("PAIR401", ["2"])), ("ok", ["2"]))
        self.assertEqual(lc76g.PPS_WRITE.match(("PQTMCFGPPS", ["ERROR", "1"])), ("error", "LC76G_REPLY_ERROR"))
        self.assertEqual(lc76g.PPS_WRITE.match(("PQTMCFGPPS", ["OK", "1"])), ("error", "LC76G_REPLY_MISMATCH"))
        self.assertEqual(lc76g.version_text(["LC76GABNR12A03S", "2024/01/01"]), "LC76GABNR12A03S")
        self.assertIsNone(lc76g.version_text(["bad version!"]))

    def test_port_sends_nothing_outside_the_allowlist(self):
        port = Port(-1, clock)  # refused before any write is attempted
        for text, code in (("$PAIR007*3D", "GNSS_CONFIG_FORBIDDEN_SENTENCE"),
                           ("$PAIR752,2,100*00", "GNSS_CONFIG_FORBIDDEN_SENTENCE"),
                           ("$PAIR006*3C", "GNSS_CONFIG_NOT_ALLOWLISTED"),
                           ("$PQTMCFGPPS,W,1,1,100,1,0,0*72", "GNSS_CONFIG_NOT_ALLOWLISTED")):
            with self.subTest(text=text), self.assertRaisesRegex(GnssConfigError, code):
                port.send(lc76g.Command("probe", text, "PAIR001"))
        self.assertEqual(port.sent, [])

    def test_the_only_uart_write_is_the_checked_send(self):
        source = (PROJECT / "software/srrx/gnss_config.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        refs = [(node.value.id, node.attr) for node in ast.walk(tree)
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)]
        self.assertEqual(refs.count(("os", "write")), 1)  # the _uart_write alias
        self.assertFalse({("os", "writev"), ("os", "pwrite"), ("termios", "tcsendbreak")} & set(refs))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == "_uart_write"]
        self.assertEqual(len(calls), 1)
        send = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "send")
        self.assertIn(calls[0], list(ast.walk(send)))
        self.assertEqual(refs.count(("os", "O_RDWR")), 1)  # open_rw only
        self.assertNotIn("shell=True", source)


class ConfigureTests(PtyCase):
    def test_matching_read_back_writes_nothing(self):
        fake = self.receiver(pps=lc76g.PPS_FIELDS, dgps="2", sbas="1")
        port = self.port()
        result = configure(port, first_sentence_ms=2000)
        self.assertEqual((result["wrote"], result["readback_match"], result["version"]), (False, True, "LC76GTESTVER01"))
        self.assertEqual(port.sent, ["version", "pps_read", "dgps_read", "sbas_read"])
        self.assertEqual(result["readback"], {"pps_read": "OK,1,1,100,3,0,0", "dgps_read": "2", "sbas_read": "1"})
        self.assertFalse([text for text in fake.state["received"] if text not in
                          {command.text for command in lc76g.ALLOWLIST}])

    def test_lost_configuration_is_written_once_then_read_back(self):
        fake = self.receiver()
        port = self.port()
        result = configure(port, first_sentence_ms=2000)
        self.assertEqual((result["wrote"], result["readback_match"]), (True, True))
        self.assertEqual(port.sent, ["version", "pps_read", "dgps_read", "sbas_read",
                                     "pps_write", "save_pqtm", "jamming_detect", "sbas_enable", "dgps_sbas", "save_pair",
                                     "pps_read", "dgps_read", "sbas_read"])
        self.assertEqual(fake.state["pps"], lc76g.PPS_FIELDS)
        self.assertNotIn("$PQTMCFGMSGRATE,W,PQTMJAMMINGSTATUS,1,1*11", fake.state["received"])
        fake.state.update(pps=("0",) * 6, dgps="0")
        port = self.port()
        result = configure(port, jamming_message=True, first_sentence_ms=2000)
        self.assertEqual(port.sent[10:12], ["jamming_rate", "save_pqtm"])

    def test_refusals_and_a_read_back_that_does_not_stick(self):
        for state, code in (({"refuse": "400"}, "GNSS_CONFIG_REFUSED_DGPS_SBAS:LC76G_PAIR_RESULT_2"),
                            ({"refuse": "pps"}, "GNSS_CONFIG_REFUSED_PPS_WRITE:LC76G_REPLY_ERROR"),
                            ({"sticky": True}, "GNSS_CONFIG_READBACK_MISMATCH")):
            with self.subTest(state=state):
                self.setUp()
                self.receiver(**state)
                with self.assertRaises(GnssConfigError) as caught:
                    configure(self.port(), first_sentence_ms=2000)
                self.assertEqual(str(caught.exception), code)

    def test_silent_receiver_and_missing_reply_are_bounded(self):
        self.receiver(talking=False, replies=False)
        started = clock()
        with self.assertRaisesRegex(GnssConfigError, "GNSS_CONFIG_NO_SENTENCE"):
            configure(self.port(), first_sentence_ms=300)
        self.assertLess(clock() - started, 1500)
        self.setUp()
        self.receiver(replies=False)
        with self.assertRaisesRegex(GnssConfigError, "GNSS_CONFIG_NO_REPLY_VERSION"):
            configure(self.port(), first_sentence_ms=2000)


class RunTests(PtyCase):
    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory(prefix="srrx-gnss-config-run-")
        self.addCleanup(folder.cleanup)
        self.result = Path(folder.name) / "result.json"
        self.log = []
        self.codes = {}

    def runner(self, tail):
        self.log.append(tuple(tail))
        return self.codes.get(tail[0], 0)

    def opener(self, device):
        self.log.append(("open", device))
        fd = os.open(self.path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK | os.O_CLOEXEC)
        configure_raw_115200(fd)
        return fd

    def go(self, mode, opener=None):
        code = run(mode, result_path=self.result, runner=self.runner, opener=opener or self.opener, clock=clock,
                   first_sentence_ms=2000)
        return code, json.loads(self.result.read_text())

    def test_gpsd_is_stopped_before_the_open_and_started_again(self):
        self.receiver(pps=lc76g.PPS_FIELDS, dgps="2", sbas="1")
        self.result.write_text('{"schema_version":1,"ok":true}')  # a previous verdict never survives a run
        code, result = self.go("gpsd")
        self.assertEqual(code, 0)
        self.assertEqual(self.log, [("stop", "gpsd.socket", "gpsd.service"), ("open", "/dev/lab/gnss"),
                                    ("start", "gpsd.socket", "gpsd.service")])
        self.assertEqual((result["ok"], result["readback_match"], result["wrote"], result["reader_restarted"]),
                         (True, True, False, True))
        self.assertLessEqual(result["started_boottime_ms"], result["finished_boottime_ms"])
        self.assertEqual(self.result.stat().st_mode & 0o777, 0o644)
        for word in ("lat", "lon", "0007.5"):
            self.assertNotIn(word, self.result.read_text())

    def test_raw_mode_stops_locationd_and_failures_still_restart_the_reader(self):
        self.receiver(pps=lc76g.PPS_FIELDS, dgps="2", sbas="1")
        code, result = self.go("raw")
        self.assertEqual((code, self.log[0], self.log[-1]), (0, ("stop", "srrx-locationd.service"),
                                                             ("start", "srrx-locationd.service")))
        self.log.clear()
        self.codes = {"stop": 1}
        code, result = self.go("gpsd")
        self.assertEqual((code, result["error"]), (2, "GNSS_CONFIG_READER_STOP_FAILED"))
        self.assertEqual([entry[0] for entry in self.log], ["stop", "start"])  # never opened
        self.log.clear()
        self.codes = {}
        def refused(device):
            raise GnssUartError("GNSS_PARENT_MISMATCH")
        code, result = self.go("gpsd", opener=refused)
        self.assertEqual((code, result["error"], result["reader_restarted"]), (2, "GNSS_PARENT_MISMATCH", True))
        self.codes = {"start": 1}
        code, result = self.go("gpsd")
        self.assertEqual((code, result["ok"], result["error"]), (2, False, "GNSS_CONFIG_READER_START_FAILED"))
        self.log.clear()
        code, result = self.go("off")
        self.assertEqual((code, result["error"], self.log), (2, "GNSS_CONFIG_MODE_OFF", []))


class OpenTests(PtyCase):
    def test_read_write_exclusive_raw_open_through_the_uart6_binding(self):
        with mock.patch.object(gnss_config, "bind_lc76g", return_value=(self.path, os.stat(self.path))) as bind:
            fd = open_rw("/dev/lab/gnss")
            self.addCleanup(os.close, fd)
            bind.assert_called_once_with("/dev/lab/gnss", expected_parent="998000.serial", sysfs_root="/sys")
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            self.assertEqual(flags & 3, os.O_RDWR)
            self.assertTrue(flags & os.O_NONBLOCK)
            self.assertFalse(os.get_inheritable(fd))
            self.assertTrue(raw_115200(termios.tcgetattr(fd)))
            with self.assertRaises((OSError, GnssConfigError)):
                open_rw("/dev/lab/gnss")  # TIOCEXCL (EBUSY) or the flock

    def test_a_held_flock_refuses_without_leaking_the_descriptor(self):
        holder = os.open(self.path, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
        self.addCleanup(os.close, holder)
        fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = len(os.listdir("/proc/self/fd"))
        with mock.patch.object(gnss_config, "bind_lc76g", return_value=(self.path, os.stat(self.path))):
            with self.assertRaisesRegex(GnssConfigError, "GNSS_CONFIG_UART_BUSY"):
                open_rw("/dev/lab/gnss")
        self.assertEqual(len(os.listdir("/proc/self/fd")), before)


if __name__ == "__main__":
    unittest.main()
