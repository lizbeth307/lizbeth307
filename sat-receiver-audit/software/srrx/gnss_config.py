"""srrx-gnss-config: one allowlisted LC76G configuration pass with read-back (root oneshot).

labd starts this unit through polkit (labd may only `start srrx-gnss-config.service`):
once at labd startup and after each bounded RESET pulse (srrx.gnss_orchestrator). The
LC76G loses its configuration without power, so every pass reads it back first and
writes only on a mismatch (build/07-pz-vstanovlennia.md:500). Steps:

1. stop the one UART reader: gpsd.socket + gpsd.service (gpsd mode) or srrx-locationd
   (raw mode); the receiver is written only while nobody else reads it (build/07:485);
2. open /dev/lab/gnss O_RDWR with the srrx.gnss_uart binding (udev alias, parent
   998000.serial, sysfs dev = st_rdev), flock + TIOCEXCL, raw 115200 read back;
3. wait for the first checksum-valid sentence, at most FIRST_SENTENCE_MS (after RESET
   the receiver boots first; cold TTFF is 28 s, build/09-testy.md:179);
4. $PQTMVERNO (version recorded), then read back PQTMCFGPPS, PAIR401 and PAIR411;
5. on a mismatch only: the build/07 writes and saves, then a second read-back;
6. close the UART, start the reader again (also after a failure), write result.json.

Only srrx.lc76g.ALLOWLIST bytes are ever written; $PAIR007, $PAIR752 and $PAIR753 are
refused by name and anything else by the allowlist. Exit 0 only for a matching
read-back. The result names steps and codes, never a position. labd selects PPS only
after this read-back and a qualified fix (srrx.gnss_orchestrator).

A SIGTERM (TimeoutStartSec=120 or a manual stop) during steps 1-5 ends them with
GNSS_CONFIG_TERMINATED, so step 6 still runs. Worst case without it: two systemctl
calls of SYSTEMCTL_TIMEOUT_S, 40 s for the first sentence and 15 sentences of at most
WRITE_MS + REPLY_MS each, about 108 s.
"""
import argparse
import errno
import fcntl
import json
import os
from pathlib import Path
import select
import signal
import stat
import subprocess
import termios
import time

from . import lc76g
from .gnss_uart import DEVICE_PATH, KERNEL_PARENT, GnssUartError, bind_lc76g, configure_raw_115200

UNIT = "srrx-gnss-config.service"
RESULT_PATH = "/run/srrx-gnss-config/result.json"
SYSTEMCTL = "/usr/bin/systemctl"
READERS = {"gpsd": ("gpsd.socket", "gpsd.service"), "raw": ("srrx-locationd.service",)}
FIRST_SENTENCE_MS = 40000
REPLY_MS = 1500
MAX_LINES = 400  # unrelated NMEA lines skipped while one reply is awaited
WRITE_MS = 1000
SYSTEMCTL_TIMEOUT_S = 15  # stopping or starting gpsd / srrx-locationd (TimeoutStopSec=3)
# The one UART write path, used once in Port.send after the allowlist check (tests parse this).
_uart_write = os.write


class GnssConfigError(RuntimeError):
    """A stable reason code."""


class Termination:
    """SIGTERM handler: while armed (steps 1-5) it raises GNSS_CONFIG_TERMINATED once, so the
    finally of run() still restarts the reader and writes result.json; during that cleanup a
    further SIGTERM is only recorded (systemd's SIGKILL after TimeoutStopSec stays final)."""
    def __init__(self):
        self.armed = self.received = False

    def __call__(self, signum, frame):
        self.received = True
        if self.armed:
            self.armed = False
            raise GnssConfigError("GNSS_CONFIG_TERMINATED")


TERMINATION = Termination()  # installed by main(); run() arms it around steps 1-5


def boottime_ms():
    clock = getattr(time, "CLOCK_BOOTTIME", None)
    return time.clock_gettime_ns(clock) // 1000000 if clock is not None else int(time.monotonic() * 1000)


def open_rw(path=DEVICE_PATH, *, expected_parent=KERNEL_PARENT, sysfs_root="/sys", ioctl=None):
    """The srrx.gnss_uart binding, opened O_RDWR (this tool alone writes the receiver)."""
    real, info = bind_lc76g(path, expected_parent=expected_parent, sysfs_root=sysfs_root)
    fd = os.open(real, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISCHR(opened.st_mode) or opened.st_rdev != info.st_rdev:
            raise GnssUartError("GNSS_DEVICE_CHANGED")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise GnssConfigError("GNSS_CONFIG_UART_BUSY") from None
        (ioctl or fcntl.ioctl)(fd, termios.TIOCEXCL)
        configure_raw_115200(fd)
    except BaseException as exc:
        os.close(fd)
        if isinstance(exc, termios.error):
            raise OSError(*exc.args) from exc
        raise
    return fd


class Port:
    """Bounded line I/O on the open UART; send() writes allowlisted sentences only."""
    def __init__(self, fd, clock=boottime_ms):
        self.fd, self.clock = fd, clock
        self._buffer, self._discard = bytearray(), False
        self.sent = []

    def send(self, command):
        wire = command.wire
        if lc76g.forbidden(wire):
            raise GnssConfigError("GNSS_CONFIG_FORBIDDEN_SENTENCE")
        if wire not in lc76g.ALLOWED_WIRE:
            raise GnssConfigError("GNSS_CONFIG_NOT_ALLOWLISTED")
        view, deadline = memoryview(wire), self.clock() + WRITE_MS
        while view:
            if self.clock() > deadline:
                raise GnssConfigError("GNSS_CONFIG_WRITE_TIMEOUT")
            select.select([], [self.fd], [], .05)
            try:
                view = view[_uart_write(self.fd, view):]
            except (BlockingIOError, InterruptedError):
                pass
        self.sent.append(command.key)

    def readline(self, deadline_ms):
        """The next complete line without CR/LF, or None at the deadline."""
        while True:
            index = self._buffer.find(b"\n")
            if index >= 0:
                line = bytes(self._buffer[:index]).rstrip(b"\r")
                del self._buffer[:index + 1]
                if self._discard:
                    self._discard = False
                    continue
                return line
            if len(self._buffer) > lc76g.MAX_SENTENCE + 2:
                self._buffer.clear()
                self._discard = True  # an overlong line is dropped up to its newline
            remaining = deadline_ms - self.clock()
            if remaining <= 0:
                return None
            if not select.select([self.fd], [], [], min(remaining, 100) / 1000)[0]:
                continue
            try:
                data = os.read(self.fd, 1024)
            except (BlockingIOError, InterruptedError):
                continue
            self._buffer.extend(data)  # VMIN=VTIME=0: an empty read is "nothing yet"


def transact(port, command, reply_ms=REPLY_MS):
    """Send one allowlisted sentence; return its reply fields or raise a stable code."""
    port.send(command)
    deadline = port.clock() + reply_ms
    for unused in range(MAX_LINES):
        line = port.readline(deadline)
        if line is None:
            break
        verdict = command.match(lc76g.parse(line))
        if verdict is None:
            continue
        if verdict[0] == "error":
            raise GnssConfigError("GNSS_CONFIG_REFUSED_" + command.key.upper() + ":" + verdict[1])
        return verdict[1]
    raise GnssConfigError("GNSS_CONFIG_NO_REPLY_" + command.key.upper())


def wait_first_sentence(port, timeout_ms=FIRST_SENTENCE_MS):
    deadline = port.clock() + timeout_ms
    while True:
        line = port.readline(deadline)
        if line is None:
            raise GnssConfigError("GNSS_CONFIG_NO_SENTENCE")
        if lc76g.parse(line) is not None:
            return


def read_back(port):
    state = {command.key: transact(port, command) for command in lc76g.READBACK}
    return state, all(state[key] == value for key, value in lc76g.EXPECTED.items())


def configure(port, *, jamming_message=False, first_sentence_ms=FIRST_SENTENCE_MS):
    """Steps 3-5 on an open port; the result fields of a matching read-back."""
    wait_first_sentence(port, first_sentence_ms)
    version = lc76g.version_text(transact(port, lc76g.VERSION))
    state, match = read_back(port)
    wrote = False
    if not match:
        writes = lc76g.WRITES + ((lc76g.JAMMING_RATE, lc76g.SAVE_PQTM) if jamming_message else ())
        for command in writes:
            transact(port, command)
        wrote = True
        state, match = read_back(port)
        if not match:
            raise GnssConfigError("GNSS_CONFIG_READBACK_MISMATCH")
    return {"version": version, "wrote": wrote, "readback_match": True,
            "readback": {key: ",".join(fields) for key, fields in state.items()}, "sent": list(port.sent)}


def systemctl(argv_tail):
    return subprocess.run([SYSTEMCTL, *argv_tail], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=SYSTEMCTL_TIMEOUT_S, check=False).returncode


def write_result(path, result):
    """Atomic 0644 replace: labd reads it; it holds codes and the firmware version only."""
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    data = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW | os.O_CLOEXEC, 0o644)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
        os.fchmod(handle.fileno(), 0o644)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def run(mode, *, device=DEVICE_PATH, result_path=RESULT_PATH, runner=systemctl, opener=open_rw,
        clock=boottime_ms, jamming_message=False, first_sentence_ms=FIRST_SENTENCE_MS):
    """Steps 1-6; returns the process exit code (0 only for a matching read-back)."""
    result = {"schema_version": 1, "unit": UNIT, "mode": mode, "ok": False, "error": None,
              "readback_match": False, "wrote": False, "version": None, "readback": None, "sent": [],
              "reader_restarted": None, "started_boottime_ms": clock(), "finished_boottime_ms": None}
    Path(result_path).unlink(missing_ok=True)  # never leave the previous run's verdict for this one
    units = READERS.get(mode)
    if units is None:
        result["error"] = "GNSS_CONFIG_MODE_" + str(mode).upper()[:8]
    else:
        port = None
        try:
            try:
                TERMINATION.armed = True
                if runner(["stop", *units]) != 0:
                    raise GnssConfigError("GNSS_CONFIG_READER_STOP_FAILED")
                port = Port(opener(device), clock)
                result.update(configure(port, jamming_message=jamming_message, first_sentence_ms=first_sentence_ms))
                result["ok"] = True
            finally:
                TERMINATION.armed = False
        except (GnssConfigError, GnssUartError) as exc:
            result.update(ok=False, error=str(exc))
        except (OSError, subprocess.SubprocessError) as exc:
            code = getattr(exc, "errno", None)
            result.update(ok=False, error="GNSS_CONFIG_IO_" + (errno.errorcode.get(code, "ERROR") if code
                                                                else type(exc).__name__.upper()))
        finally:
            if port is not None:
                result["sent"] = list(port.sent)
                os.close(port.fd)
            try:
                restarted = runner(["start", *units]) == 0
            except (OSError, subprocess.SubprocessError):
                restarted = False
            result["reader_restarted"] = restarted
            if not restarted and result["ok"]:
                result.update(ok=False, error="GNSS_CONFIG_READER_START_FAILED")
    if not result["ok"]:
        result["readback_match"] = False
    result["finished_boottime_ms"] = clock()
    write_result(result_path, result)
    return 0 if result["ok"] else 2


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--gnss", choices=("gpsd", "raw", "off"), required=True)
    ap.add_argument("--device", default=DEVICE_PATH)
    ap.add_argument("--result", default=RESULT_PATH)
    ap.add_argument("--jamming-status-message", action="store_true",
                    help="also enable $PQTMJAMMINGSTATUS output (build/07:498, optional)")
    args = ap.parse_args(argv)
    signal.signal(signal.SIGTERM, TERMINATION)
    code = run(args.gnss, device=args.device, result_path=args.result, jamming_message=args.jamming_status_message)
    print(Path(args.result).read_text(), end="", flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
