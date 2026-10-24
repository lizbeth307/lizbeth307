"""Production LC76G UART reader on real Linux PTYs and a temporary fake sysfs.

Synthetic NMEA at one unnamed lat/lon point only; no device, no GNSS reception
and no hardware PASS. The live udev/sysfs binding on the Q6A stays RUNTIME_ONLY.
"""
import ast
import errno
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import select
import sys
import tempfile
import termios
import time
import unittest
from unittest import mock

from srrx import gnss_uart
from srrx.gnss_uart import (GnssUartError, NmeaUartReader, bind_lc76g, configure_raw_115200,
                            open_lc76g, raw_115200)
from srrx.location import LocationTracker

PROJECT = Path(__file__).resolve().parents[2]
LAB = PROJECT / "deployment" / "module_lab"


def sentence(body):
    checksum = 0
    for byte in body.encode("ascii"):
        checksum ^= byte
    return ("$%s*%02X\r\n" % (body, checksum)).encode("ascii")


def rmc(second):
    # Unnamed synthetic point (0.125 N, 0.375 E); epochs 12:00:00 + second.
    return sentence("GNRMC,1200%02d.000,A,0007.500000,N,00022.500000,E,0.00,0.00,150626,,,A,V" % second)


def gsv(index):
    # A valid, ignored sentence type: bulk bytes that never become positions.
    return sentence("GNGSV,3,1,12,%02d,45,180,40" % (index % 100))


def open_fds():
    return len(os.listdir("/proc/self/fd"))


class PtyBase(unittest.TestCase):
    def setUp(self):
        self.master, self.slave = os.openpty()
        self.addCleanup(self._close, "slave")
        self.addCleanup(self._close, "master")
        os.set_blocking(self.master, False)
        self.path = os.ttyname(self.slave)

    def _close(self, name):
        fd = getattr(self, name)
        if fd is not None:
            setattr(self, name, None)
            os.close(fd)

    def write(self, payload, timeout=2.0):
        view, deadline = memoryview(payload), time.monotonic() + timeout
        while view:
            self.assertGreater(deadline, time.monotonic(), "PTY write deadline")
            select.select([], [self.master], [], .05)
            try:
                view = view[os.write(self.master, view):]
            except BlockingIOError:
                pass

    def reader_fd(self):
        fd = os.open(self.path, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK | os.O_CLOEXEC)
        configure_raw_115200(fd)
        return fd


class BindingTests(PtyBase):
    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory(prefix="srrx-gnss-test-")
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.sys = self.root / "sys"
        self.name = os.path.basename(self.path)
        self.alias = self.root / "lab" / "gnss"
        self.alias.parent.mkdir()
        self.alias.symlink_to(self.path)
        self.sysfs("998000.serial")

    def sysfs(self, parent, dev=None):
        controller = self.sys / "devices/platform/soc@0/9c0000.geniqup" / parent
        controller.mkdir(parents=True, exist_ok=True)
        node = self.sys / "class/tty" / self.name
        node.mkdir(parents=True, exist_ok=True)
        link = node / "device"
        if link.is_symlink():
            link.unlink()
        link.symlink_to(controller)
        number = os.stat(self.path).st_rdev
        (node / "dev").write_text(dev or "%d:%d\n" % (os.major(number), os.minor(number)))

    def refused(self, code, path=None, **kwargs):
        before = open_fds()
        with self.assertRaises(GnssUartError) as caught:
            open_lc76g(str(path or self.alias), sysfs_root=str(self.sys), **kwargs)
        self.assertEqual(str(caught.exception), code)
        self.assertEqual(open_fds(), before, "a refused binding leaked a descriptor")

    def test_exact_alias_opens_read_only_exclusive_raw_115200(self):
        calls = []
        def ioctl(fd, request, *args):
            calls.append(request)
            return fcntl.ioctl(fd, request, *args)
        fd = open_lc76g(str(self.alias), sysfs_root=str(self.sys), ioctl=ioctl)
        self.addCleanup(os.close, fd)
        self.assertEqual(calls, [termios.TIOCEXCL])
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        self.assertEqual(flags & 3, os.O_RDONLY)
        self.assertTrue(flags & os.O_NONBLOCK)
        self.assertFalse(os.get_inheritable(fd))  # O_CLOEXEC
        self.assertEqual(os.fstat(fd).st_rdev, os.stat(self.path).st_rdev)
        with self.assertRaises(OSError) as caught:
            os.write(fd, b"$PAIR006*3C\r\n")
        self.assertEqual(caught.exception.errno, errno.EBADF)
        iflag, oflag, cflag, lflag, ispeed, ospeed, cc = attrs = termios.tcgetattr(fd)
        self.assertTrue(raw_115200(attrs))
        self.assertEqual((iflag, oflag, lflag, ispeed, ospeed), (0, 0, 0, termios.B115200, termios.B115200))
        self.assertEqual(cflag & termios.CSIZE, termios.CS8)
        self.assertTrue(cflag & termios.CREAD and cflag & termios.CLOCAL)
        self.assertFalse(cflag & (termios.PARENB | termios.CSTOPB | termios.HUPCL | termios.CRTSCTS))
        self.assertEqual((cc[termios.VMIN], cc[termios.VTIME]), (0, 0))
        # A second reader is refused: EBUSY from TIOCEXCL, or the flock for root.
        with self.assertRaises(OSError):
            open_lc76g(str(self.alias), sysfs_root=str(self.sys))

    def test_binding_refuses_wrong_parent_tty_names_regular_files_and_sysfs_mismatch(self):
        self.refused("GNSS_PATH_NOT_ALIAS", "/dev/ttyHS1")
        self.refused("GNSS_PATH_NOT_ALIAS", self.path)  # the kernel node itself, not the alias
        self.refused("GNSS_PATH_INVALID", "lab/gnss")
        self.refused("GNSS_PARENT_INVALID", expected_parent="*")
        plain = self.root / "plain"
        plain.write_bytes(b"$GNRMC\r\n")
        fake = self.root / "lab" / "file"
        fake.symlink_to(plain)
        self.refused("GNSS_NOT_CHAR_DEVICE", fake)
        dangling = self.root / "lab" / "dangling"
        dangling.symlink_to(self.root / "missing")
        self.refused("GNSS_DEVICE_MISSING", dangling)
        self.sysfs("99c000.serial")  # UART7: the Pico port, never the GNSS
        self.refused("GNSS_PARENT_MISMATCH")
        self.sysfs("998000.serial", dev="1:3\n")
        self.refused("GNSS_SYSFS_DEV_MISMATCH")
        (self.sys / "class/tty" / self.name / "dev").unlink()
        self.refused("GNSS_SYSFS_MISSING")
        self.sysfs("998000.serial")
        real, info = bind_lc76g(str(self.alias), sysfs_root=str(self.sys))
        self.assertEqual((real, info.st_rdev), (os.path.realpath(self.path), os.stat(self.path).st_rdev))

    def test_failed_exclusive_claim_or_termios_read_back_closes_and_refuses(self):
        def busy(fd, request, *args):
            raise OSError(errno.EBUSY, "injected TIOCEXCL failure")
        before = open_fds()
        with self.assertRaises(OSError):
            open_lc76g(str(self.alias), sysfs_root=str(self.sys), ioctl=busy)
        self.assertEqual(open_fds(), before)
        real, reads = termios.tcgetattr, []
        def readback(fd):
            attrs = real(fd)
            reads.append(fd)
            if len(reads) == 2:
                attrs[2] |= termios.CSTOPB  # a driver that silently kept two stop bits
            return attrs
        with mock.patch.object(gnss_uart, "_tcgetattr", side_effect=readback):
            self.refused("GNSS_TERMIOS_MISMATCH")
        self.assertEqual(len(reads), 2)


class TermiosImageTests(PtyBase):
    def test_only_the_exact_raw_image_is_accepted(self):
        fd = self.reader_fd()
        self.addCleanup(os.close, fd)
        good = termios.tcgetattr(fd)
        self.assertTrue(raw_115200(good))
        def mutate(index, value=None, cc=None):
            attrs = [list(item) if type(item) is list else item for item in good]
            if cc is not None:
                attrs[6][cc] = 1
            else:
                attrs[index] = value(attrs[index])
            return attrs
        for bad in (mutate(2, lambda v: v | termios.PARENB), mutate(2, lambda v: v | termios.CSTOPB),
                    mutate(2, lambda v: v | termios.CRTSCTS), mutate(2, lambda v: v | termios.HUPCL),
                    mutate(2, lambda v: v & ~termios.CSIZE | termios.CS7), mutate(2, lambda v: v & ~termios.CREAD),
                    mutate(3, lambda v: v | termios.ICANON), mutate(3, lambda v: v | termios.ECHO),
                    mutate(0, lambda v: v | termios.ICRNL), mutate(1, lambda v: v | termios.OPOST),
                    mutate(4, lambda v: termios.B9600), mutate(5, lambda v: termios.B921600),
                    mutate(None, cc=termios.VMIN), mutate(None, cc=termios.VTIME), None, [], good[:6]):
            self.assertFalse(raw_115200(bad), bad)


class ReaderTests(PtyBase):
    def setUp(self):
        super().setUp()
        self.tracker = LocationTracker()
        self.fd = self.reader_fd()
        self.reader = NmeaUartReader(self.fd, self.tracker)
        self.addCleanup(self.reader.close)
        self.now = 1000
        self.assertEqual(self.reader.poll(self.now), 0)  # The first poll only flushes.
        self.assertEqual((self.reader.flushes, self.reader.state), (1, "STARTING"))

    def pump(self, until, step=20, timeout=2.0):
        """Poll every `step` ms of synthetic time until `until(accepted)` holds."""
        accepted, deadline = 0, time.monotonic() + timeout
        while not until(accepted):
            self.assertGreater(deadline, time.monotonic(), "PTY receive deadline")
            select.select([self.reader.fileno()], [], [], .02)
            self.now += step
            accepted += self.reader.poll(self.now)
        return accepted

    def received(self, count):
        return lambda accepted: self.reader.bytes_received >= count

    def test_reader_refuses_writable_or_blocking_descriptors(self):
        for flags in (os.O_RDWR | os.O_NONBLOCK, os.O_WRONLY | os.O_NONBLOCK, os.O_RDONLY):
            fd = os.open(self.path, flags | os.O_NOCTTY | os.O_CLOEXEC)
            self.addCleanup(os.close, fd)
            with self.assertRaises(GnssUartError):
                NmeaUartReader(fd, LocationTracker())
        with self.assertRaises(ValueError):
            NmeaUartReader(None, LocationTracker())
        with self.assertRaises(ValueError):
            self.reader.poll(-1)
        self.assertFalse(self.reader.status()["write_capable"])

    def test_sentence_fragmented_across_polls_releases_one_fix_at_lf(self):
        message = rmc(0)
        self.write(b"noise before sync," + message[:30])
        self.assertEqual(self.pump(self.received(18 + 30)), 0)
        self.assertEqual(self.reader.state, "RECEIVING")
        self.write(message[30:-1])
        self.assertEqual(self.pump(self.received(17 + len(message))), 0)
        self.write(message[-1:])
        self.assertEqual(self.pump(lambda accepted: accepted == 1), 1)
        state = self.tracker.status(self.now)
        self.assertEqual((state["source"], state["fresh"], state["lat"], state["lon"]), ("nmea", True, .125, .375))
        self.assertEqual(self.reader.bytes_received, 18 + len(message))

    def test_one_poll_reads_at_most_eight_2048_byte_chunks(self):
        chunk = b"".join(gsv(i) for i in range(200))[:gnss_uart.READ_CHUNK]
        poller = mock.Mock()
        poller.poll.return_value = [(self.fd, select.POLLIN)]
        reader = NmeaUartReader(os.dup(self.fd), LocationTracker(), poller=poller)
        self.addCleanup(reader.close)
        sizes = []
        real = reader.tracker.ingest_nmea
        reader.tracker.ingest_nmea = lambda data, now: sizes.append(len(data)) or real(data, now)
        with mock.patch.object(gnss_uart, "_os_read", return_value=chunk) as read:
            reader.poll(0)
            self.assertEqual(read.call_count, 8)
            self.assertTrue(all(call.args[1] == 2048 for call in read.call_args_list))
            reader.poll(20)
            self.assertEqual(read.call_count, 16)
        self.assertEqual(reader.bytes_received, 2 * 16384)
        self.assertEqual(len(sizes), 16)
        self.assertLessEqual(max(sizes), 2048)
        self.assertFalse(reader.tracker.status(20)["available"])  # ignored GSV bytes never become a position

    def test_64_kib_burst_is_read_in_bounded_polls(self):
        burst = b"".join(gsv(i) for i in range(4000))[:65536]
        burst = burst[:burst.rindex(b"\n") + 1]
        sent, deltas, deadline = 0, [], time.monotonic() + 20
        while self.reader.bytes_received < len(burst):
            self.assertGreater(deadline, time.monotonic(), "burst deadline")
            try:
                sent += os.write(self.master, burst[sent:sent + 16384]) if sent < len(burst) else 0
            except BlockingIOError:
                pass
            select.select([self.reader.fileno()], [], [], .02)
            before = self.reader.bytes_received
            self.now += 10
            self.reader.poll(self.now)
            deltas.append(self.reader.bytes_received - before)
        self.assertEqual(self.reader.bytes_received, len(burst))
        self.assertLessEqual(max(deltas), 16384)
        self.assertGreater(len(deltas), 3)
        self.assertFalse(self.reader.disconnected)

    def test_host_stall_flushes_queued_bytes_and_never_completes_a_stale_partial(self):
        self.write(rmc(0))
        self.assertEqual(self.pump(lambda accepted: accepted == 1), 1)
        stale = rmc(1)
        self.write(stale[:25])
        self.pump(self.received(len(rmc(0)) + 25))
        self.write(stale[25:] + rmc(1))  # Queued while the host is stalled.
        select.select([self.reader.fileno()], [], [], .5)
        time.sleep(.05)
        received = self.reader.bytes_received
        self.now += 600
        self.assertEqual(self.reader.poll(self.now), 0)
        self.assertEqual((self.reader.bytes_received, self.reader.flushes), (received, 2))
        self.assertEqual(self.reader.state, "STARTING")  # No byte since the flush: not reception.
        state = self.tracker.status(self.now)
        self.assertFalse(state["fresh"])
        self.assertEqual(state["reason"], "NMEA_HOST_STALL")
        # Mid-sentence bytes after the flush are dropped until '$'; the pre-stall
        # prefix is discarded by the tracker's resync, never completed.
        fresh = rmc(1)
        self.write(stale[25:] + fresh)
        accepted = self.pump(self.received(received + len(stale) - 25 + len(fresh)))
        self.assertEqual(accepted, 1)
        state = self.tracker.status(self.now)
        self.assertTrue(state["fresh"])
        self.assertEqual(state["utc"], "2026-06-15T12:00:01.000Z")
        self.assertEqual(self.tracker.last_error, "NMEA_RESYNC")
        # A backwards caller clock is treated like a stall, not as new data.
        self.assertEqual(self.reader.poll(self.now - 1), 0)
        self.assertEqual(self.reader.flushes, 3)
        self.assertEqual(self.tracker.last_error, "NMEA_MONOTONIC_TIME_REVERSED")

    def test_late_first_poll_never_delivers_what_was_queued_since_open(self):
        tracker = LocationTracker()
        reader = NmeaUartReader(os.dup(self.fd), tracker)
        self.addCleanup(reader.close)
        self.write(rmc(0) + rmc(1) + rmc(2))  # Queued between open and a first poll 49 s later.
        select.select([reader.fileno()], [], [], .5)
        time.sleep(.05)
        now = 50000
        self.assertEqual(reader.poll(now), 0)
        self.assertEqual((reader.bytes_received, reader.flushes, reader.state), (0, 1, "STARTING"))
        self.assertFalse(tracker.status(now)["available"])
        self.assertEqual(tracker.rejected_count, 0)  # The start flush invalidates nothing it never gave.
        self.write(rmc(3))
        accepted, deadline = 0, time.monotonic() + 2
        while not accepted:
            self.assertGreater(deadline, time.monotonic(), "PTY receive deadline")
            select.select([reader.fileno()], [], [], .02)
            now += 20
            accepted += reader.poll(now)
        state = tracker.status(now)
        self.assertEqual((accepted, state["fresh"], state["utc"]), (1, True, "2026-06-15T12:00:03.000Z"))
        self.assertEqual(reader.bytes_received, len(rmc(3)))

    def test_host_stall_after_silence_is_not_reported_as_reception(self):
        self.write(rmc(0))
        self.pump(lambda accepted: accepted == 1, step=10)
        heard = self.now
        for offset in range(100, 8100, 100):
            self.reader.poll(heard + offset)
        self.assertEqual(self.reader.state, "QUIET")
        rejected = self.tracker.rejected_count
        self.reader.poll(heard + 8700)  # A 600 ms host stall with still no byte.
        self.assertEqual((self.reader.state, self.reader.status()["last_byte_ms"]), ("STARTING", heard))
        self.assertEqual(self.tracker.status(heard + 8700)["reason"], "NMEA_HOST_STALL")
        for offset in range(8800, 10700, 100):
            self.reader.poll(heard + offset)
            self.assertEqual(self.reader.state, "STARTING")
        self.reader.poll(heard + 10700)  # The silence clock restarted at the stall.
        self.assertEqual(self.reader.state, "QUIET")
        self.assertEqual(self.tracker.rejected_count, rejected + 2)
        self.assertEqual(self.tracker.status(heard + 10700)["reason"], "NMEA_UART_SILENT")
        for offset in range(10800, 18700, 100):
            self.reader.poll(heard + offset)
        self.assertEqual(self.reader.state, "QUIET")
        self.reader.poll(heard + 18700)
        self.assertEqual((self.reader.state, self.reader.status()["reset_candidate"]), ("SILENT", True))
        self.assertEqual(self.reader.status()["last_byte_ms"], heard)

    def test_pty_hangup_disconnects_once_without_reopen(self):
        self.write(rmc(0))
        self.pump(lambda accepted: accepted == 1)
        self._close("master")
        with mock.patch.object(gnss_uart, "_os_open", side_effect=AssertionError("reopen")) as reopen:
            self.assertEqual(self.reader.poll(self.now + 20), 0)
            self.assertTrue(self.reader.disconnected)
            self.assertEqual((self.reader.state, self.reader.fileno(), self.reader.error),
                             ("DISCONNECTED", -1, "NMEA_UART_LOST"))
            rejected = self.tracker.rejected_count
            for step in range(1, 20):
                self.assertEqual(self.reader.poll(self.now + 20 + step * 20), 0)
            self.reader.close()
            self.assertEqual(reopen.call_count, 0)
        self.assertEqual(self.tracker.rejected_count, rejected)
        state = self.tracker.status(self.now + 500)
        self.assertEqual((state["fresh"], state["source"], state["reason"]), (False, "last_good", "NMEA_UART_LOST"))
        with self.assertRaises(OSError):
            os.fstat(self.fd)  # closed by its owner, the reader

    def test_silence_invalidates_once_and_marks_only_a_reset_candidate(self):
        self.write(rmc(0))
        self.pump(lambda accepted: accepted == 1, step=10)
        heard, rejected = self.now, self.tracker.rejected_count
        for offset in range(100, 2000, 100):
            self.reader.poll(heard + offset)
        self.assertTrue(self.tracker.status(heard + 1900)["fresh"])
        self.assertEqual(self.reader.state, "RECEIVING")
        self.reader.poll(heard + 2000)
        state = self.tracker.status(heard + 2000)
        self.assertEqual((state["fresh"], state["reason"], self.reader.state), (False, "NMEA_UART_SILENT", "QUIET"))
        self.assertEqual(self.tracker.rejected_count, rejected + 1)
        for offset in range(2100, 10000, 100):
            self.reader.poll(heard + offset)
        self.assertEqual((self.reader.state, self.tracker.rejected_count), ("QUIET", rejected + 1))
        self.reader.poll(heard + 10000)
        self.assertEqual(self.reader.status()["state"], "SILENT")
        self.assertTrue(self.reader.status()["reset_candidate"])
        self.assertFalse(self.reader.disconnected)
        self.now = heard + 10000
        self.write(rmc(10))
        self.pump(lambda accepted: accepted == 1)
        self.assertEqual(self.reader.state, "RECEIVING")
        self.assertTrue(self.tracker.status(self.now)["fresh"])

    def test_read_errors_and_poll_errors_disconnect_fail_closed(self):
        cases = ((OSError(errno.EIO, "io"), "NMEA_UART_LOST", True),
                 (OSError(errno.ENXIO, "gone"), "NMEA_UART_LOST", True),
                 (OSError(errno.ENODEV, "unbound"), "NMEA_UART_LOST", True),
                 (OSError(errno.EBADF, "closed elsewhere"), "NMEA_UART_LOST", False),
                 (OSError(errno.EPERM, "unexpected"), "NMEA_UART_IO_ERROR", True))
        for error, reason, closes in cases:
            with self.subTest(errno=error.errno):
                poller = mock.Mock()
                poller.poll.return_value = [(0, select.POLLIN)]
                fd = os.dup(self.fd)
                reader = NmeaUartReader(fd, LocationTracker(), poller=poller)
                with mock.patch.object(gnss_uart, "_os_read", side_effect=error), \
                        mock.patch.object(gnss_uart, "_os_close") as close:
                    self.assertEqual(reader.poll(0), 0)
                self.assertEqual((reader.disconnected, reader.error), (True, reason))
                self.assertEqual(close.call_count, int(closes))
                state = reader.tracker.status(0)
                self.assertEqual((state["available"], state["reason"], state["last_error"]), (False, reason, reason))
                os.close(fd)
        for mask in (select.POLLERR, select.POLLHUP, select.POLLNVAL | select.POLLIN):
            with self.subTest(mask=mask):
                poller = mock.Mock()
                poller.poll.return_value = [(0, mask)]
                fd = os.dup(self.fd)
                reader = NmeaUartReader(fd, LocationTracker(), poller=poller)
                with mock.patch.object(gnss_uart, "_os_read") as read, \
                        mock.patch.object(gnss_uart, "_os_close") as close:
                    self.assertEqual(reader.poll(0), 0)
                self.assertEqual(read.call_count, 0)
                self.assertEqual((reader.disconnected, reader.error), (True, "NMEA_UART_LOST"))
                self.assertEqual(close.call_count, 0 if mask & select.POLLNVAL else 1)
                os.close(fd)


class ReceiveOnlySourceTests(unittest.TestCase):
    def test_reader_source_has_no_write_path_or_receiver_command(self):
        source = (PROJECT / "software/srrx/gnss_uart.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        # Every reference counts, not only calls: an alias such as `w = os.write` is a write path.
        refs = [(node.value.id, node.attr) for node in ast.walk(tree)
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)]
        self.assertFalse({("os", "write"), ("os", "writev"), ("os", "pwrite"), ("os", "sendfile"),
                          ("termios", "tcsendbreak"), ("termios", "tcdrain")} & set(refs))
        # os.open is referenced once, by the module-local alias; that alias is called once.
        self.assertEqual(refs.count(("os", "open")), 1)
        self.assertIs(gnss_uart._os_open, os.open)
        opens = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == "_os_open"]
        self.assertEqual(len(opens), 1)
        flags = {node.attr for node in ast.walk(opens[0].args[1]) if isinstance(node, ast.Attribute)}
        self.assertEqual(flags, {"O_RDONLY", "O_NOCTTY", "O_NONBLOCK", "O_CLOEXEC"})
        for forbidden in ("O_RDWR", "O_WRONLY", "$PAIR", "$PQTM", "ttyHS", "glob", "listdir", "socket"):
            self.assertNotIn(forbidden, source)
        imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        self.assertEqual(imports, {"errno", "fcntl", "os", "re", "select", "stat", "termios"})
        self.assertFalse(any(isinstance(node, ast.ImportFrom) for node in ast.walk(tree)))


class GnssUdevRuleTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("srrx_test_gnss_deploy", PROJECT / "deployment/deploy.py")
        self.deploy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.deploy)

    def devices(self):
        config = self.deploy.load(PROJECT / "deployment/devices.template.json")
        config["i2c"]["ina228"] = {"path": "/dev/i2c-7", "of_fullname": "/soc@0/test-ina228"}
        config["i2c"]["control"] = {"path": "/dev/i2c-9", "of_fullname": "/soc@0/test-control"}
        config["pico"]["kernel_parent"] = "99c000.serial"
        config["usb"]["hfplus"]["serial"] = "AIRSPYHF SN:0123456789ABCDEF"
        config["wifi_bt"]["fe11s_port4_usb_path"] = "1-1.4"
        return config

    def test_gnss_rule_binds_the_uart6_parent_read_only_and_is_staged_separately(self):
        text = self.deploy.gnss_udev_rules()
        rules = [line for line in text.splitlines() if not line.startswith("#")]
        self.assertEqual(rules, ['SUBSYSTEM=="tty", KERNELS=="998000.serial", GROUP="srrx-gnss", MODE="0640", '
                                 'ENV{ID_MM_DEVICE_IGNORE}="1", SYMLINK+="lab/gnss", TAG+="systemd"'])
        for forbidden in ("ttyHS", "uaccess", "0666", "0660", "RUN+=", "PROGRAM", "labd"):
            self.assertNotIn(forbidden, text)
        # The device-bound rules file keeps its exact contents; GNSS is never a devices.json entry.
        self.assertNotIn("lab/gnss", self.deploy.udev_rules(self.devices()))
        with tempfile.TemporaryDirectory(prefix="srrx-gnss-stage-") as folder:
            self.deploy.stage(Path(folder) / "candidate", self.devices())
            staged = Path(folder) / "candidate/rootfs/etc/udev/rules.d/71-srrx-gnss.rules"
            self.assertEqual(staged.read_text(), text)
            listed = json.loads((Path(folder) / "candidate/stage-files.json").read_text())["files"]
            self.assertIn("etc/udev/rules.d/71-srrx-gnss.rules", listed)

    def test_pico_binding_on_the_gnss_uart6_parent_is_refused(self):
        # 71-srrx-gnss.rules would re-own that tty (srrx-gnss 0640) and alias it as lab/gnss too.
        config = self.devices()
        config["pico"]["kernel_parent"] = "998000.serial"
        for build in (self.deploy.validate_devices, self.deploy.udev_rules):
            with self.subTest(build=build.__name__), self.assertRaises(self.deploy.DeploymentError) as caught:
                build(config)
            self.assertIn("998000.serial", str(caught.exception))
        with tempfile.TemporaryDirectory(prefix="srrx-gnss-stage-") as folder:
            with self.assertRaises(self.deploy.DeploymentError):
                self.deploy.stage(Path(folder) / "candidate", config)
            self.assertFalse((Path(folder) / "candidate/rootfs/etc/udev/rules.d/71-srrx-gnss.rules").exists())
        self.assertEqual(self.deploy.validate_devices(self.devices())["pico"]["kernel_parent"], "99c000.serial")


class ModuleLabProductionReaderTests(unittest.TestCase):
    def test_location_scenarios_run_the_production_reader(self):
        modules = (LAB / "location_modules.py").read_text(encoding="utf-8")
        scenarios = (LAB / "location_scenarios.py").read_text(encoding="utf-8")
        self.assertNotIn("class NMEAReader", modules)
        self.assertNotIn("tcsetattr", modules)  # the host line discipline is production code
        self.assertNotIn("Production raw-UART reader", scenarios)
        loaded = set(sys.modules)
        try:
            with mock.patch.object(sys, "path", [str(LAB)] + sys.path):
                spec = importlib.util.spec_from_file_location("srrx_test_location_scenarios", LAB / "location_scenarios.py")
                lab = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(lab)
                api = lab._production(PROJECT)
                status, results = lab._run_cases(lab.NMEA_CASES, api)
        finally:
            # The lab's own modules (location_modules, imported by plain name) must not
            # stay in sys.modules for later tests; stdlib modules it imported stay.
            for name in set(sys.modules) - loaded:
                origin = getattr(sys.modules[name], "__file__", None)
                if origin and Path(origin).resolve().parent == LAB.resolve():
                    del sys.modules[name]
        self.assertEqual(status, "EMULATION_PASS", results)
        drop = next(item for item in results if item["scenario"] == "nmea_drop_and_explicit_reopen")
        self.assertEqual(drop["observed"]["disconnect_detection_owner"], "production_gnss_uart_NmeaUartReader_pollhup")
        self.assertFalse(drop["observed"]["automatic_reopen"])


if __name__ == "__main__":
    unittest.main()
