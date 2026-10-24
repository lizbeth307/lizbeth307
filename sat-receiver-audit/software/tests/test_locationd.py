"""srrx-locationd on real Linux PTYs and AF_UNIX sockets, with a socketpair standing in for gpsd.

Synthetic NMEA and gpsd JSON at one unnamed lat/lon point only; no LC76G, no gpsd
process, no GNSS reception and no hardware PASS. Internet sockets stay denied in the
host regression (tools/run_tests_offline.py): the gpsd path is driven over a socketpair.
"""
import ast
import json
import os
from pathlib import Path
import select
import socket
import tempfile
import time
import unittest
from unittest import mock

from srrx import locationd
from srrx.gnss_uart import NmeaUartReader, configure_raw_115200
from srrx.lc76g import JAMMING_HOLD_MS, JammingMonitor, sentence
from srrx.location import MAX_GPSD_BYTES, LocationTracker
from srrx.locationd import (GpsdMixedDecoder, JammingGpsdClient, LocationService, LocationdError, PeerPolicy, Server,
                            TeeTracker, bind_socket, gpsd_devices, gpsd_preflight, raw_preflight, serve)

PROJECT = Path(__file__).resolve().parents[2]


def raw(body):
    """One sentence without its line ending, as JammingMonitor.line takes it."""
    return sentence(body).encode("ascii")


def line(body):
    return raw(body) + b"\r\n"


def epoch(second, satellites=8):
    """GSA 3D + GGA + RMC of one epoch at the unnamed point 0.125 N, 0.375 E."""
    return (line("GNGSA,A,3,01,02,03,04,05,06,07,08,,,,,1.5,0.9,1.2,1")
            + line("GNGGA,1200%02d.000,0007.500000,N,00022.500000,E,1,%02d,0.90,10.0,M,0.0,M,," % (second, satellites))
            + line("GNRMC,1200%02d.000,A,0007.500000,N,00022.500000,E,0.00,0.00,150626,,,A,V" % second))


class FakeReader:
    def __init__(self):
        self.disconnected, self.polls, self.closed = False, 0, None

    def poll(self, now_ms):
        self.polls += 1
        return 0

    def status(self):
        return {"state": "RECEIVING", "disconnected": self.disconnected}

    def close(self, reason):
        self.closed = reason


class JammingAndMixedStreamTests(unittest.TestCase):
    def test_jamming_flag_status_two_or_malformed_and_hold(self):
        monitor = JammingMonitor()
        self.assertFalse(monitor.line(raw("GNRMC,120000.000,V,,,,,,,150626,,,N,V"), 0))  # not a jamming sentence
        self.assertTrue(monitor.line(raw("PAIRSPF,1"), 10))
        self.assertFalse(monitor.status(10)["active"])
        self.assertTrue(monitor.line(raw("PQTMJAMMINGSTATUS,1,2"), 20))
        status = monitor.status(30)
        self.assertEqual((status["active"], status["status"], status["source"]), (True, 2, "PQTMJAMMINGSTATUS"))
        self.assertTrue(monitor.status(20 + JAMMING_HOLD_MS - 1)["active"])
        self.assertFalse(monitor.status(20 + JAMMING_HOLD_MS)["active"])
        self.assertTrue(monitor.status(19)["active"])  # a backwards clock cannot age it out
        for bad in ("PAIRSPF,x", "PAIRSPF", "PQTMJAMMINGSTATUS,2,1", "PQTMJAMMINGSTATUS,1,-1"):
            with self.subTest(bad=bad):
                fresh = JammingMonitor()
                self.assertTrue(fresh.line(raw(bad), 0))
                self.assertEqual((fresh.status(0)["active"], fresh.status(0)["error"]), (True, "JAMMING_STATUS_MALFORMED"))
        bad_checksum = line("PAIRSPF,3")[:-4] + b"00\r\n"
        fresh = JammingMonitor()
        fresh.feed(bad_checksum, 0)
        self.assertEqual((fresh.status(0)["active"], fresh.reports), (False, 0))
        fresh.feed(b"garbage" + line("PAIRSPF,3")[:5], 0)
        fresh.feed(line("PAIRSPF,3")[5:], 0)
        self.assertTrue(fresh.status(1)["active"])

    def test_mixed_decoder_routes_json_and_nmea_lines(self):
        monitor = JammingMonitor()
        decoder = GpsdMixedDecoder(monitor)
        stream = (b'{"class":"VERSION","proto_major":3}\n' + line("PAIRSPF,2") + b"!AIVDM,ignored\n"
                  + b'{"class":"TPV","mode":1}\n')
        frames = []
        for index in range(len(stream)):  # every fragmentation boundary at once: one byte per feed
            frames += decoder.feed(stream[index:index + 1])
        self.assertEqual([frame["class"] for frame in frames], ["VERSION", "TPV"])
        self.assertEqual(decoder.errors, 0)
        self.assertTrue(monitor.status(0)["active"])
        self.assertEqual(decoder.feed(b"{not json}\n"), [])
        self.assertEqual(decoder.errors, 1)
        self.assertEqual(decoder.feed(b"{" + b"x" * MAX_GPSD_BYTES), [])
        self.assertEqual(decoder.errors, 2)
        self.assertEqual(decoder.feed(b'y"}\n{"class":"SKY"}\n'), [{"class": "SKY"}])  # recovered at the newline
        decoder.reset()
        self.assertEqual(decoder.buffered_bytes, 0)

    def test_gpsd_client_asks_for_raw_nmea_and_feeds_tracker_and_monitor(self):
        tracker, monitor = LocationTracker(), JammingMonitor()
        client = JammingGpsdClient(tracker, "127.0.0.1", 2947, monitor)
        self.assertIn(b'"raw":1', client.WATCH)
        self.assertIsInstance(client.decoder, GpsdMixedDecoder)
        with self.assertRaises(ValueError):
            JammingGpsdClient(tracker, "192.0.2.1", 2947, monitor)
        ours, gpsd = socket.socketpair()
        self.addCleanup(gpsd.close)
        ours.setblocking(False)
        client.sock, client.connected = ours, True
        client._started = client._last_now = 0
        gpsd.sendall(b'{"class":"VERSION","proto_major":3,"proto_minor":15}\n')
        client.poll(10)
        self.assertIn(b'"raw":1', gpsd.recv(4096))
        report = {"device": "/dev/lab/gnss", "time": "2026-06-15T12:00:00.000Z"}
        gpsd.sendall(b'{"class":"WATCH","enable":true,"json":true,"raw":1}\n'
                     + json.dumps(dict(report, **{"class": "TPV", "mode": 3, "lat": 0.125, "lon": 0.375,
                                                  "altHAE": 10.0, "altMSL": 10.0})).encode() + b"\n"
                     + json.dumps(dict(report, **{"class": "SKY", "uSat": 8})).encode() + b"\n" + line("PAIRSPF,1"))
        self.assertEqual(client.poll(20), 1)
        status = tracker.status(20)
        self.assertEqual((status["source"], status["mode"], status["satellites"]), ("gpsd", 3, 8))
        self.assertEqual((monitor.reports, monitor.status(20)["active"]), (1, False))
        client.close("GPSD_CLOSED")


class ServiceTests(unittest.TestCase):
    def test_qualified_fix_needs_3d_six_satellites_freshness_and_no_jamming(self):
        service = LocationService("raw", reader=FakeReader())
        self.assertFalse(service.snapshot(0)["qualified_fix"])
        service.tracker.ingest_nmea(epoch(0), 1000)
        snap = service.snapshot(1000)
        self.assertTrue(snap["qualified_fix"], snap["location"])
        self.assertEqual((snap["mode"], snap["reader"]["kind"], snap["schema_version"]), ("raw", "raw", 1))
        self.assertFalse(service.snapshot(4000)["qualified_fix"])  # older than the tracker's 3 s freshness
        service.tracker.ingest_nmea(epoch(4, satellites=5), 5000)
        self.assertFalse(service.snapshot(5000)["qualified_fix"])
        service.tracker.ingest_nmea(epoch(5), 6000)
        self.assertTrue(service.snapshot(6000)["qualified_fix"])
        service.monitor.line(raw("PAIRSPF,2"), 6000)
        snap = service.snapshot(6000)
        self.assertFalse(snap["qualified_fix"])
        self.assertTrue(snap["jamming"]["active"])
        service.invalidate("GNSS_RESET")
        snap = service.snapshot(6000)
        self.assertEqual((snap["location"]["fresh"], snap["location"]["reason"], snap["resets"], snap["last_invalidate"]),
                         (False, "GNSS_RESET", 1, "GNSS_RESET"))
        self.assertEqual(snap["location"]["source"], "last_good")  # kept, but labelled stale

    def test_gpsd_reconnects_only_by_a_new_client_and_at_most_every_five_seconds(self):
        made = []

        class Client:
            def __init__(self, tracker, monitor):
                self.sock, self.connected, self.watching, self.error, self.polls = None, False, False, None, 0
                made.append(self)

            def start(self, now_ms):
                self.sock = object()

            def poll(self, now_ms):
                self.polls += 1

            def close(self, reason):
                self.sock = None

        service = LocationService("gpsd", client_factory=Client)
        service.poll(0)
        service.poll(100)
        self.assertEqual((len(made), made[0].polls), (1, 1))
        made[0].sock = None  # gpsd went away; GpsdClient itself never reconnects
        for now in (200, 4999):
            service.poll(now)
        self.assertEqual(len(made), 1)
        service.poll(5000)
        self.assertEqual((len(made), service.reader_status()["connects"]), (2, 2))
        with self.assertRaises(ValueError):
            LocationService("gpsd", reader=FakeReader())
        with self.assertRaises(ValueError):
            LocationService("raw", client_factory=Client)

    def test_lost_raw_uart_ends_the_loop_for_a_unit_restart(self):
        reader = FakeReader()
        service = LocationService("raw", reader=reader)
        server = mock.Mock()
        reader.disconnected = True
        self.assertEqual(serve(service, server, clock=lambda: 0), 3)
        self.assertEqual(serve(LocationService("raw", reader=FakeReader()), server, clock=lambda: 0,
                               running=iter([True, True, False]).__next__), 0)


class RawPtyTests(unittest.TestCase):
    def setUp(self):
        self.master, self.slave = os.openpty()
        self.addCleanup(os.close, self.master)
        self.addCleanup(os.close, self.slave)
        fd = os.open(os.ttyname(self.slave), os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK | os.O_CLOEXEC)
        configure_raw_115200(fd)
        self.tracker, self.monitor = LocationTracker(), JammingMonitor()
        self.reader = NmeaUartReader(fd, TeeTracker(self.tracker, self.monitor))
        self.addCleanup(self.reader.close)
        self.service = LocationService("raw", tracker=self.tracker, monitor=self.monitor, reader=self.reader)
        self.now = 0
        self.service.poll(self.now)  # the start flush

    def pump(self, payload, until):
        os.write(self.master, payload)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            select.select([self.reader.fd], [], [], .02)
            self.now += 20
            self.service.poll(self.now)
            if until():
                return
        self.fail("PTY data did not arrive")

    def test_uart_bytes_reach_both_the_tracker_and_the_jamming_monitor(self):
        self.pump(epoch(0) + line("PAIRSPF,1"), lambda: self.monitor.reports == 1)
        snap = self.service.snapshot(self.now)
        self.assertTrue(snap["qualified_fix"], snap)
        self.assertEqual(snap["reader"]["state"], "RECEIVING")
        self.pump(line("PQTMJAMMINGSTATUS,1,3"), lambda: self.monitor.reports == 2)
        snap = self.service.snapshot(self.now)
        self.assertEqual((snap["qualified_fix"], snap["jamming"]["status"]), (False, 3))


class PreflightTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="srrx-locationd-pre-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.defaults = self.root / "gpsd"

    def test_gpsd_defaults_parsing(self):
        self.assertIsNone(gpsd_devices(str(self.defaults)))
        self.defaults.write_text('# comment\nDEVICES="/dev/lab/gnss /dev/ttyX"\nGPSD_OPTIONS="-n -b"\n')
        self.assertEqual(gpsd_devices(str(self.defaults)), ["/dev/lab/gnss", "/dev/ttyX"])
        self.defaults.write_text("export DEVICES=''\n")
        self.assertEqual(gpsd_devices(str(self.defaults)), [])
        self.defaults.write_bytes(b"x" * 65537)
        with self.assertRaises(LocationdError):
            gpsd_devices(str(self.defaults))

    def test_raw_mode_refused_while_gpsd_owns_or_may_own_the_uart(self):
        calls = []
        def inactive(argv):
            calls.append(argv)
            return 3
        raw_preflight("/dev/lab/gnss", str(self.defaults), inactive)
        self.assertEqual(calls, [["/usr/bin/systemctl", "is-active", "--quiet", "gpsd.service"],
                                 ["/usr/bin/systemctl", "is-active", "--quiet", "gpsd.socket"]])
        self.defaults.write_text('DEVICES="/dev/lab/gnss"\n')
        with self.assertRaisesRegex(LocationdError, "LOCATIOND_GPSD_CONFIGURED_FOR_UART"):
            raw_preflight("/dev/lab/gnss", str(self.defaults), inactive)
        target = self.root / "ttyHS9"
        target.write_text("")
        alias = self.root / "alias"
        alias.symlink_to(target)
        self.defaults.write_text('DEVICES="%s"\n' % target)
        with self.assertRaisesRegex(LocationdError, "LOCATIOND_GPSD_CONFIGURED_FOR_UART"):
            raw_preflight(str(alias), str(self.defaults), inactive)  # the same node by its kernel name
        self.defaults.write_text('DEVICES=""\n')
        with self.assertRaisesRegex(LocationdError, "LOCATIOND_GPSD_ACTIVE"):
            raw_preflight("/dev/lab/gnss", str(self.defaults), lambda argv: 0 if argv[-1] == "gpsd.socket" else 3)
        def missing(argv):
            raise FileNotFoundError(argv[0])
        with self.assertRaisesRegex(LocationdError, "LOCATIOND_GPSD_STATE_UNKNOWN"):
            raw_preflight("/dev/lab/gnss", str(self.defaults), missing)

    def test_gpsd_mode_refuses_the_raw_uart_group(self):
        group = mock.Mock(gr_gid=4321)
        with mock.patch.object(locationd.grp, "getgrnam", return_value=group), \
                mock.patch.object(locationd.os, "getgroups", return_value=[100, 4321]):
            with self.assertRaisesRegex(LocationdError, "LOCATIOND_GNSS_GROUP_IN_GPSD_MODE"):
                gpsd_preflight("srrx-gnss")
        with mock.patch.object(locationd.grp, "getgrnam", return_value=group), \
                mock.patch.object(locationd.os, "getgroups", return_value=[100]), \
                mock.patch.object(locationd.os, "getegid", return_value=100):
            gpsd_preflight("srrx-gnss")
        with mock.patch.object(locationd.grp, "getgrnam", side_effect=KeyError("srrx-gnss")):
            gpsd_preflight("srrx-gnss")  # the group does not exist: nobody can hold it

    def test_off_mode_starts_nothing(self):
        with mock.patch("sys.stdout"):
            self.assertEqual(locationd.main(["--gnss", "off"]), 0)
        with mock.patch.object(locationd, "raw_preflight", side_effect=LocationdError("LOCATIOND_GPSD_ACTIVE")), \
                mock.patch.object(locationd.PeerPolicy, "for_user", return_value=PeerPolicy(os.getuid())), \
                mock.patch("sys.stderr") as err:
            self.assertEqual(locationd.main(["--gnss", "raw"]), 1)
        self.assertIn("LOCATIOND_GPSD_ACTIVE", "".join(str(call) for call in err.write.call_args_list))


class SocketTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="srrx-locationd-sock-")
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        os.chmod(self.folder, 0o700)
        self.path = str(self.folder / "location.sock")
        self.service = LocationService("raw", reader=FakeReader())
        self.service.tracker.ingest_nmea(epoch(0), 1000)

    def server(self, policy):
        server = Server(bind_socket(self.path, 0o666), self.service, policy)
        self.addCleanup(server.close)
        return server

    def exchange(self, server, payload, now=1000):
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(self.path)
        client.sendall(payload)
        client.setblocking(False)
        data = bytearray()
        try:
            for unused in range(400):
                server.step(now, .005)
                try:
                    block = client.recv(65536)
                except BlockingIOError:
                    continue
                if not block:
                    break
                data.extend(block)
        finally:
            client.close()
        return json.loads(data) if data else None

    def test_control_user_reads_snapshots_and_invalidates(self):
        server = self.server(PeerPolicy(os.getuid()))
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o666)  # authorization is SO_PEERCRED
        reply = self.exchange(server, b'{"op":"snapshot"}\n')
        self.assertTrue(reply["ok"])
        self.assertTrue(reply["data"]["qualified_fix"])
        self.assertEqual(self.exchange(server, b'{"op":"invalidate","reason":"GNSS_RESET"}\n'),
                         {"ok": True, "invalidated": "GNSS_RESET"})
        self.assertEqual(self.service.resets, 1)
        for bad, code in ((b'{"op":"invalidate","reason":"gnss reset"}\n', "LOCATIOND_UNKNOWN_REQUEST"),
                          (b'{"op":"snapshot","x":1}\n', "LOCATIOND_UNKNOWN_REQUEST"),
                          (b'{"op":"set_position","lat":1,"lon":2}\n', "LOCATIOND_UNKNOWN_REQUEST"),
                          (b"[1]\n", "LOCATIOND_REQUEST"), (b"{bad\n", "LOCATIOND_REQUEST_JSON"),
                          (b'{"op":NaN}\n', "LOCATIOND_REQUEST_JSON")):
            with self.subTest(bad=bad):
                self.assertEqual(self.exchange(server, bad), {"ok": False, "error": code})
        self.assertIsNone(self.exchange(server, b"{" + b" " * 600 + b"}\n"))  # oversize: dropped unanswered

    def test_group_members_read_only_and_strangers_are_closed_unread(self):
        server = self.server(PeerPolicy(os.getuid() + 54321, os.getgid()))
        self.assertTrue(self.exchange(server, b'{"op":"snapshot"}\n')["ok"])
        self.assertEqual(self.exchange(server, b'{"op":"invalidate","reason":"GNSS_RESET"}\n'),
                         {"ok": False, "error": "LOCATIOND_PEER_REFUSED"})
        self.assertEqual(self.service.resets, 0)
        server.close()
        server = self.server(PeerPolicy(os.getuid() + 54321, None))
        self.assertIsNone(self.exchange(server, b'{"op":"snapshot"}\n'))

    def test_socket_directory_and_stale_path_checks(self):
        os.chmod(self.folder, 0o720)
        with self.assertRaisesRegex(LocationdError, "SOCKET_DIRECTORY_NOT_PRIVATE"):
            bind_socket(self.path, 0o666)
        os.chmod(self.folder, 0o700)
        Path(self.path).write_text("not a socket")
        with self.assertRaisesRegex(LocationdError, "SOCKET_PATH_NOT_OUR_STALE_SOCKET"):
            bind_socket(self.path, 0o666)
        os.unlink(self.path)
        stale = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        stale.bind(self.path)
        stale.close()
        bind_socket(self.path, 0o666).close()  # our own stale socket is replaced


class SourceTests(unittest.TestCase):
    def test_locationd_never_opens_or_writes_a_device_itself(self):
        for name in ("locationd.py", "timegate.py", "gnss_orchestrator.py"):
            source = (PROJECT / "software/srrx" / name).read_text(encoding="utf-8")
            tree = ast.parse(source)
            refs = {(node.value.id, node.attr) for node in ast.walk(tree)
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)}
            with self.subTest(module=name):
                self.assertFalse({("os", "write"), ("os", "open"), ("os", "writev")} & refs)
                for forbidden in ("O_RDWR", "O_WRONLY", "$PAIR", "$PQTM", "shell=True", "AF_INET,"):
                    self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
