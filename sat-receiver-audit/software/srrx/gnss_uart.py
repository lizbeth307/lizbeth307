"""Production LC76G UART6 NMEA reader: exact binding, read-only, bounded, no reopen.

Receive only. open_lc76g() opens just the explicit udev alias (default
/dev/lab/gnss, rule KERNELS=="998000.serial"); it never scans /dev, never takes
a kernel tty name (probe order numbers UART6) and has no fallback. The
descriptor is O_RDONLY: this module cannot send LC76G configuration (PAIR/PQTM
sentences), firmware or reset commands. The bounded RESET_N pulse is labd's
policy-checked gnss_reset op. Raw mode and gpsd mode are exclusive by
configuration: flock and TIOCEXCL stop other non-root openers, not root.

Bytes go only to LocationTracker.ingest_nmea; the publication gate (3D with >=6
satellites; first fix >=8 within 50 m for 5 min) is a consumer layer. Nothing
here is wired into the labd daemon loop, gpsd or chrony (out of scope). poll()
is meant for a 20 ms select loop: no threads, no sleeps, bounded reads. Times
are the caller's nonnegative monotonic integer ms, the tracker's clock domain.
Standard library only and no relative imports, so deployment/module_lab can
load this file directly. Conservative choices where the plan is silent: the
first poll flushes like a stall (bytes queued since open cannot be timed), a
host stall restarts the silence clock (the host was not observing) and reports
STARTING until a real byte arrives, and after a flush nothing reaches the
tracker before the next '$'.
"""
import errno
import fcntl
import os
import re
import select
import stat
import termios

DEVICE_PATH = "/dev/lab/gnss"
KERNEL_PARENT = "998000.serial"  # UART6, alias serial1 (build/04 pinout row 16/18)
# 8 x 2048 bytes: 16 KiB per poll. Each chunk is one ingest_nmea call, so lines of
# >=16 bytes stay within the tracker's 128-line batch; shorter garbage trips its
# NMEA_BATCH_LIMIT (fail closed). 115200 baud 8N1 is 11520 B/s (about 11.25 KiB/s).
READ_CHUNK, MAX_READS = 2048, 8
HOST_STALL_MS, QUIET_MS, SILENT_MS = 500, 2000, 10000
LOST_ERRNOS = frozenset({errno.EIO, errno.ENXIO, errno.ENODEV, errno.EBADF})
_ACCMODE = getattr(os, "O_ACCMODE", 3)  # Linux access-mode mask
_HANGUP = select.POLLHUP | select.POLLERR | select.POLLNVAL
_PARENT = re.compile(r"[0-9a-f]+\.serial")
_TTY_NAME = re.compile(r"[A-Za-z0-9_+-]{1,32}")
_CFLAG_MASK = (termios.CSIZE | termios.CSTOPB | termios.CREAD | termios.PARENB | termios.PARODD
               | termios.HUPCL | termios.CLOCAL | getattr(termios, "CRTSCTS", 0) | getattr(termios, "CMSPAR", 0))
_CFLAG_RAW = termios.CS8 | termios.CREAD | termios.CLOCAL
# Module-local syscall indirections: tests patch these names, never the
# process-wide os/termios functions that other threads may be using.
_os_open, _os_read, _os_close, _tcgetattr = os.open, os.read, os.close, termios.tcgetattr


class GnssUartError(RuntimeError):
    """A stable reason code; never carries received bytes or positions."""


def bind_lc76g(path=DEVICE_PATH, *, expected_parent=KERNEL_PARENT, sysfs_root="/sys"):
    """Return (realpath, stat) only for a udev alias to the UART6 character device.

    realpath(<sysfs>/class/tty/<name>/device) must contain the expected platform
    parent as a path segment (as deploy.doctor checks the Pico), and the sysfs
    'dev' number must equal the node's own st_rdev.
    """
    if type(path) is not str or not 1 < len(path) <= 256 or not path.startswith("/") or "\0" in path:
        raise GnssUartError("GNSS_PATH_INVALID")
    if type(expected_parent) is not str or not _PARENT.fullmatch(expected_parent):
        raise GnssUartError("GNSS_PARENT_INVALID")
    head, tail = os.path.split(path)
    if (head == "/dev" and tail.startswith("tty")) or not os.path.islink(path):
        raise GnssUartError("GNSS_PATH_NOT_ALIAS")
    real = os.path.realpath(path)
    try:
        info = os.stat(real)
    except OSError:
        raise GnssUartError("GNSS_DEVICE_MISSING") from None
    if not stat.S_ISCHR(info.st_mode):
        raise GnssUartError("GNSS_NOT_CHAR_DEVICE")
    name = os.path.basename(real)
    if not _TTY_NAME.fullmatch(name):
        raise GnssUartError("GNSS_TTY_NAME")
    node = os.path.join(sysfs_root, "class", "tty", name)
    try:
        parent = os.path.realpath(os.path.join(node, "device"), strict=True)
        with open(os.path.join(node, "dev"), "rb") as handle:
            number = handle.read(33)
    except OSError:
        raise GnssUartError("GNSS_SYSFS_MISSING") from None
    if expected_parent not in parent.split("/"):
        raise GnssUartError("GNSS_PARENT_MISMATCH")
    if number.strip() != b"%d:%d" % (os.major(info.st_rdev), os.minor(info.st_rdev)):
        raise GnssUartError("GNSS_SYSFS_DEV_MISMATCH")
    return real, info


def open_lc76g(path=DEVICE_PATH, *, expected_parent=KERNEL_PARENT, sysfs_root="/sys", ioctl=None):
    """Bind, open O_RDONLY|O_NOCTTY|O_NONBLOCK|O_CLOEXEC, claim, configure; return the fd.

    Any failure closes the descriptor. termios.error is re-raised as OSError.
    """
    real, info = bind_lc76g(path, expected_parent=expected_parent, sysfs_root=sysfs_root)
    fd = _os_open(real, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISCHR(opened.st_mode) or opened.st_rdev != info.st_rdev:
            raise GnssUartError("GNSS_DEVICE_CHANGED")
        # Exclusive before any termios change or flush, as srrx.link does for the Pico.
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        (ioctl or fcntl.ioctl)(fd, termios.TIOCEXCL)
        configure_raw_115200(fd)
    except BaseException as exc:
        _os_close(fd)
        if isinstance(exc, termios.error):
            raise OSError(*exc.args) from exc
        raise
    return fd


def raw_115200(attrs):
    """True only for raw 8N1 115200, no flow control/HUPCL, VMIN=VTIME=0."""
    try:
        iflag, oflag, cflag, lflag, ispeed, ospeed, cc = attrs
        vmin, vtime = (value if type(value) is int else value[0] for value in (cc[termios.VMIN], cc[termios.VTIME]))
    except (TypeError, ValueError, IndexError):
        return False
    return (iflag == 0 and oflag == 0 and lflag == 0 and cflag & _CFLAG_MASK == _CFLAG_RAW
            and ispeed == ospeed == termios.B115200 and vmin == 0 and vtime == 0)


def configure_raw_115200(fd):
    """Set raw 115200 (TCSANOW), read it back with tcgetattr, refuse a mismatch, flush input."""
    try:
        attrs = _tcgetattr(fd)
        attrs[0] = attrs[1] = attrs[3] = 0
        attrs[2] = _CFLAG_RAW
        attrs[4] = attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = attrs[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        if not raw_115200(_tcgetattr(fd)):
            raise GnssUartError("GNSS_TERMIOS_MISMATCH")
        termios.tcflush(fd, termios.TCIFLUSH)
    except termios.error as exc:
        raise OSError(*exc.args) from exc


class NmeaUartReader:
    """Nonblocking bounded reader that owns fd and feeds one LocationTracker.

    state: STARTING (no byte since the start/stall flush), RECEIVING, QUIET
    (>=2 s without bytes; the NMEA source was invalidated once), SILENT (>=10 s;
    only a reset candidate, never an automatic reset), DISCONNECTED. A
    disconnect never reopens: a new open_lc76g() and reader are an explicit
    operator/service decision. The first poll flushes the input queue, so
    nothing queued since open (whenever that poll comes) is relabelled fresh.
    """
    def __init__(self, fd, tracker, *, poller=None):
        if type(fd) is not int or fd < 0:
            raise ValueError("explicit open descriptor required")
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        if flags & _ACCMODE != os.O_RDONLY or not flags & os.O_NONBLOCK:
            raise GnssUartError("GNSS_UART_FD_MODE")  # never write-capable, never blocking
        self.fd, self.tracker = fd, tracker
        self.bytes_received = self.flushes = 0
        self.disconnected = False
        self.state, self.error = "STARTING", None
        self._poller = poller if poller is not None else select.poll()
        self._poller.register(fd, select.POLLIN)  # POLLHUP/POLLERR/POLLNVAL are always reported
        # _last_byte: time of the last real byte (status only). _silence_from: start
        # of the current silence measurement (first poll, last byte or a stall).
        self._last_poll = self._last_byte = self._silence_from = None
        self._quiet_reported = self._heard = False  # _heard: a byte since the last flush
        # Until a '$' arrives nothing reaches the tracker, so a pre-stall partial
        # line can only be discarded (NMEA_RESYNC), never completed by new bytes.
        self._resync = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def fileno(self):
        return -1 if self.fd is None else self.fd

    def close(self, reason="NMEA_UART_CLOSED", *, close_fd=True):
        if self.disconnected:
            return
        if self.fd is not None:
            try:
                self._poller.unregister(self.fd)
            except (KeyError, ValueError, OSError):
                pass
            if close_fd:  # Not after EBADF/POLLNVAL: the number may already belong to another file.
                try:
                    _os_close(self.fd)
                except OSError:
                    pass
            self.fd = None
        self.disconnected, self.state, self.error = True, "DISCONNECTED", reason
        self.tracker.invalidate("nmea", reason)

    def _lost(self, error=None):
        code = None if error is None else error.errno
        self.close("NMEA_UART_LOST" if error is None or code in LOST_ERRNOS else "NMEA_UART_IO_ERROR",
                   close_fd=code != errno.EBADF)

    def _flush(self, reason):
        # Queued bytes were received while the host was not looking: never
        # relabel them as newly acquired (as Engine discards UART input on a gap).
        try:
            termios.tcflush(self.fd, termios.TCIFLUSH)
        except termios.error as exc:
            self._lost(OSError(*exc.args))
            return False
        except OSError as exc:
            self._lost(exc)
            return False
        self.flushes += 1
        self._resync, self._heard = True, False
        if reason is not None:  # The start flush has delivered nothing that could be stale.
            self.tracker.invalidate("nmea", reason)
        return True

    def poll(self, now_ms):
        """Read at most MAX_READS x READ_CHUNK bytes; return newly accepted positions."""
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be nonnegative monotonic integer ms")
        if self.disconnected:
            return 0
        previous, self._last_poll = self._last_poll, now_ms
        if previous is None or not 0 <= now_ms - previous <= HOST_STALL_MS:
            # The first poll is a stall start: bytes queued since open have no receipt time.
            if not self._flush(None if previous is None else "NMEA_HOST_STALL" if now_ms >= previous
                               else "NMEA_MONOTONIC_TIME_REVERSED"):
                return 0
            # The host was not observing: a stall is not evidence of receiver silence.
            self._silence_from, self._quiet_reported = now_ms, False
        try:
            events = 0
            for unused, mask in self._poller.poll(0):
                events |= mask
        except OSError as exc:
            self._lost(exc)
            return 0
        if events & _HANGUP:
            # A hung-up tty reads 0 bytes like an idle VMIN=0 one; only poll tells them apart.
            self.close("NMEA_UART_LOST", close_fd=not events & select.POLLNVAL)
            return 0
        accepted = 0
        if events & select.POLLIN:
            for unused in range(MAX_READS):
                try:
                    data = _os_read(self.fd, READ_CHUNK)
                except (BlockingIOError, InterruptedError):
                    break
                except OSError as exc:
                    self._lost(exc)
                    return accepted
                if not data:
                    break  # VMIN=VTIME=0: empty is "nothing queued", not end of file
                self.bytes_received += len(data)
                self._last_byte = self._silence_from = now_ms
                self._heard = True
                if self._resync:
                    start = data.find(b"$")
                    if start < 0:
                        continue
                    data, self._resync = data[start:], False
                accepted += int(self.tracker.ingest_nmea(data, now_ms))
        quiet = now_ms - self._silence_from
        if quiet >= QUIET_MS:
            if not self._quiet_reported:
                self._quiet_reported = True
                self.tracker.invalidate("nmea", "NMEA_UART_SILENT")
            self.state = "SILENT" if quiet >= SILENT_MS else "QUIET"
        else:
            self._quiet_reported = False
            # Only a real byte since the start/stall flush counts as reception.
            self.state = "RECEIVING" if self._heard else "STARTING"
        return accepted

    def status(self):
        return {"state": self.state, "disconnected": self.disconnected, "error": self.error,
                "bytes_received": self.bytes_received, "flushes": self.flushes,
                "last_byte_ms": self._last_byte,
                "reset_candidate": self.state == "SILENT", "write_capable": False}
