"""Independent location-device protocol emulators; no production parser imports.

All positions, epochs and receiver reports are synthetic laboratory inputs.
LC76G emulation covers its documented NMEA output subset, not RF acquisition,
PPS accuracy, proprietary configuration, analog behavior or physical UART.
The loopback server emulates the gpsd JSON API and is not a gpsd executable.
"""
from __future__ import annotations

import datetime as dt
import errno
import json
import os
import pty
import queue
import select
import socket
import termios
import threading
import time

SYNTHETIC_EPOCH = dt.datetime(2001, 1, 1, tzinfo=dt.timezone.utc).timestamp()
SYNTHETIC_LATITUDE = 0.125
SYNTHETIC_LONGITUDE = 0.375
SYNTHETIC_DEVICE = "module-lab-synthetic-U304"
PRIMARY_SOURCES = {
    "lc76g_nmea": "https://www.quectel.com/content/uploads/2024/04/Quectel_LC26GLC26G-TLC76GLC86G_Series_GNSS_Protocol_Specification_V1.5.pdf",
    "lc76g_board": "https://files.waveshare.com/wiki/LC76G/manual/LC76G%20GNSS%20Module.pdf",
    "gpsd_json": "https://gpsd.io/gpsd_json.html",
}


class UnsupportedEnvironment(RuntimeError):
    pass


def unsupported_os(error, capability):
    if isinstance(error, OSError) and error.errno in {
            errno.EPERM, errno.EACCES, errno.ENOSYS, errno.ENODEV,
            errno.ENOENT, errno.EAFNOSUPPORT, errno.EPROTONOSUPPORT}:
        raise UnsupportedEnvironment(capability + " unavailable: " + type(error).__name__) from error
    raise error


def nmea_sentence(body):
    """Independent NMEA XOR checksum, excluding '$' and '*', with CR/LF."""
    encoded = body.encode("ascii")
    if not encoded or b"$" in encoded or b"*" in encoded or b"\r" in encoded or b"\n" in encoded:
        raise ValueError("Invalid emulator NMEA body")
    checksum = 0
    for byte in encoded:
        checksum ^= byte
    return b"$" + encoded + ("*%02X\r\n" % checksum).encode("ascii")


def _utc(second):
    return dt.datetime.fromtimestamp(SYNTHETIC_EPOCH + second, dt.timezone.utc)


def _coordinates():
    # Generated laboratory fixture, not a city table or a real user position.
    return ["0007.500000", "N", "00022.500000", "E"]


def rmc(second=0, *, valid=True):
    instant = _utc(second)
    fields = ["GNRMC", instant.strftime("%H%M%S") + ".000", "A" if valid else "V"]
    fields += _coordinates()
    fields += ["0.00", "0.00", instant.strftime("%d%m%y"), "", "", "A", "V"]
    return nmea_sentence(",".join(fields))


def gga(second=0, *, valid=True):
    fields = ["GNGGA", _utc(second).strftime("%H%M%S") + ".000"] + _coordinates()
    fields += ["1" if valid else "0", "08", "0.90", "12.30", "M", "0.00", "M", "", ""]
    return nmea_sentence(",".join(fields))


def gsa(mode=3):
    if mode not in (1, 2, 3):
        raise ValueError("Invalid synthetic NMEA fix dimension")
    # Twelve SatID slots plus PDOP/HDOP/VDOP and NMEA4.10 system ID.
    fields = ["GNGSA", "A", str(mode), "01", "02", "03", "04"] + [""] * 8
    fields += ["1.20", "0.90", "0.80", "1"]
    return nmea_sentence(",".join(fields))


def zda(second=0):
    instant = _utc(second)
    return nmea_sentence(",".join(["GNZDA", instant.strftime("%H%M%S") + ".000",
                                   instant.strftime("%d"), instant.strftime("%m"), instant.strftime("%Y"), "00", "00"]))


def gst(second=0):
    return nmea_sentence(",".join(["GNGST", _utc(second).strftime("%H%M%S") + ".000",
                                   "1.00", "2.00", "1.00", "0.00", "3.00", "4.00", "5.00"]))


def epoch_sentences(second=0, *, mode=3):
    return zda(second) + gsa(mode) + rmc(second) + gga(second) + gst(second)


def tpv(second=0, *, mode=3, **changes):
    result = {"class": "TPV", "device": SYNTHETIC_DEVICE, "mode": mode,
              "time": _utc(second).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
              "lat": SYNTHETIC_LATITUDE, "lon": SYNTHETIC_LONGITUDE,
              "eph": 5.0, "speed": 0.0, "track": 0.0, "altMSL": 12.3, "altHAE": 12.3}
    result.update(changes)
    return result


def json_line(value):
    return json.dumps(value, separators=(",", ":"), allow_nan=False).encode("ascii") + b"\r\n"


class LC76GPTY:
    """Independent GNSS output endpoint with a real Linux PTY and raw115200."""
    def __init__(self):
        self.master = self.slave = None
        original_slave = None
        self.bytes_written = 0
        try:
            self.master, original_slave = pty.openpty()
            self.path = os.ttyname(original_slave)
            if not self.path.startswith("/dev/pts/"):
                raise UnsupportedEnvironment("Expected a fresh Linux /dev/pts endpoint")
            self.slave = os.open(self.path, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
            attrs = termios.tcgetattr(self.slave)
            attrs[0] = attrs[1] = attrs[3] = 0
            attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
            attrs[4] = attrs[5] = termios.B115200
            attrs[6][termios.VMIN] = attrs[6][termios.VTIME] = 0
            termios.tcsetattr(self.slave, termios.TCSANOW, attrs)
            termios.tcflush(self.slave, termios.TCIFLUSH)
            os.set_blocking(self.master, False)
        except OSError as error:
            self.close()
            unsupported_os(error, "Linux PTY")
        finally:
            if original_slave is not None:
                os.close(original_slave)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def write(self, payload, timeout=.5):
        if self.master is None:
            raise OSError(errno.EBADF, "Emulated LC76G endpoint is disconnected")
        pending = memoryview(payload)
        deadline = time.monotonic() + timeout
        while pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([], [self.master], [], remaining)[1]:
                raise TimeoutError("LC76G PTY write deadline")
            try:
                count = os.write(self.master, pending)
                self.bytes_written += count
                pending = pending[count:]
            except BlockingIOError:
                pass

    def disconnect(self):
        if self.master is not None:
            os.close(self.master)
            self.master = None

    def close(self):
        self.disconnect()
        if self.slave is not None:
            os.close(self.slave)
            self.slave = None


class NMEAReader:
    """Fixture transport glue; parsing/freshness is the production tracker.

    The production API consumes bytes and does not itself open a raw LC76G UART.
    Disconnect invalidation here belongs to the test adapter, not a claimed
    production UART-driver implementation.
    """
    def __init__(self, emulator, tracker):
        self.emulator, self.tracker = emulator, tracker
        self.disconnected = False
        self.bytes_received = 0

    def poll(self, now_ms):
        try:
            data = os.read(self.emulator.slave, 4096)
        except BlockingIOError:
            return 0
        except OSError as error:
            if error.errno not in (errno.EIO, errno.EBADF):
                raise
            data = b""
        if not data:
            # With VMIN=VTIME=0, an empty read is not proof of disconnection.
            if self.emulator.master is None:
                self.disconnected = True
                self.tracker.invalidate("nmea", "EMULATION_TRANSPORT_DISCONNECTED")
            return 0
        self.bytes_received += len(data)
        return self.tracker.ingest_nmea(data, now_ms)


class GpsdAPIServer:
    """Independent guest-loopback GPSD JSON protocol server, never real gpsd.

    VERSION → exact WATCH request → WATCH acknowledgement, followed by explicitly
    queued synthetic reports. The only bind address is numeric127.0.0.1.
    No name lookup, non-loopback address, multicast or NIC access is requested.
    """
    def __init__(self, *, accept_watch=True, protocol_major=3):
        self.listener = self.connection = None
        self.accept_watch, self.protocol_major = accept_watch, protocol_major
        self.stopped = threading.Event()
        self.events = queue.Queue(maxsize=64)
        self.accepts = self.watch_requests = self.bytes_sent = 0
        self.error = None
        self.watched = threading.Event()
        try:
            self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener.bind(("127.0.0.1", 0))
            self.listener.listen(2)
            self.listener.settimeout(.03)
            self.port = self.listener.getsockname()[1]
        except OSError as error:
            self.close()
            unsupported_os(error, "Guest AF_INET loopback socket")
        self.thread = threading.Thread(target=self._serve, name="synthetic-gpsd-api", daemon=True)
        self.thread.start()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def enqueue(self, value, *, fragment=7):
        payload = value if isinstance(value, bytes) else json_line(value)
        if len(payload) > 16384 or type(fragment) is not int or not 1 <= fragment <= 16384:
            raise ValueError("GPSD API emulator output bound")
        self.events.put_nowait((payload, fragment))

    def disconnect(self):
        self.events.put_nowait((None, 0))

    def _send(self, connection, payload, fragment):
        for offset in range(0, len(payload), fragment):
            if self.stopped.is_set():
                return
            part = payload[offset:offset + fragment]
            connection.sendall(part)
            self.bytes_sent += len(part)
            if len(payload) > fragment:
                # Force producer writes to be fragmented independently of the
                # client parser. TCP may still coalesce individual segments.
                self.stopped.wait(.001)

    def _serve(self):
        try:
            while not self.stopped.is_set():
                try:
                    connection, peer = self.listener.accept()
                except socket.timeout:
                    continue
                if peer[0] != "127.0.0.1":
                    connection.close()
                    raise RuntimeError("Unexpected non-loopback emulator peer")
                self.connection = connection
                connection.settimeout(.03)
                self.accepts += 1
                self.watched.clear()
                try:
                    self._send(connection, json_line({"class": "VERSION", "release": "module-lab-emulator",
                                                      "rev": "synthetic", "proto_major": self.protocol_major,
                                                      "proto_minor": 15}), 11)
                    request = bytearray()
                    while not self.stopped.is_set():
                        if not self.watched.is_set():
                            try:
                                part = connection.recv(128)
                            except socket.timeout:
                                continue
                            if not part:
                                break
                            request.extend(part)
                            if len(request) > 80:
                                raise RuntimeError("GPSD emulator WATCH request size")
                            if b"\n" not in request:
                                continue
                            line = bytes(request).strip()
                            if line != b'?WATCH={"enable":true,"json":true};':
                                raise RuntimeError("GPSD emulator received an unexpected request")
                            self.watch_requests += 1
                            self._send(connection, json_line({"class": "WATCH", "enable": self.accept_watch,
                                                              "json": True}), 5)
                            if not self.accept_watch:
                                break
                            self.watched.set()
                        try:
                            payload, fragment = self.events.get(timeout=.02)
                        except queue.Empty:
                            try:
                                part = connection.recv(128)
                                if not part:
                                    break
                                raise RuntimeError("Unexpected command after WATCH")
                            except socket.timeout:
                                continue
                        if payload is None:
                            break
                        self._send(connection, payload, fragment)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    connection.close()
                    self.connection = None
                    self.watched.clear()
        except OSError as error:
            if not self.stopped.is_set():
                self.error = type(error).__name__
        except Exception as error:
            self.error = type(error).__name__ + ": " + str(error)[:200]

    def close(self):
        self.stopped.set()
        if self.connection is not None:
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        if self.listener is not None:
            self.listener.close()
            self.listener = None
        thread = getattr(self, "thread", None)
        if thread is not None:
            thread.join(.7)
            if thread.is_alive():
                raise RuntimeError("GPSD emulator thread did not stop within deadline")
