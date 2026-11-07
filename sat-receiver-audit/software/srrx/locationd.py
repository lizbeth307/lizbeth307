"""srrx-locationd: the one GNSS position reader; local snapshots on an AF_UNIX socket.

Receive only. --gnss gpsd: a GpsdClient to explicit loopback gpsd (the unit allows IP
traffic to localhost only). --gnss raw: srrx.gnss_uart.NmeaUartReader on /dev/lab/gnss,
refused while gpsd is configured for or running on that UART (the two modes are
exclusive; build/07 §18). Either way one LocationTracker; positions never reach a log,
a file or the network, and error codes never carry coordinates.

Socket protocol: one JSON request line, one JSON reply line, then close.
  {"op": "snapshot"}                       -> tracker status, qualified-fix gate, jamming
  {"op": "invalidate", "reason": "CODE"}   -> both GNSS sources invalid (gnss_reset)
Authorization is the kernel peer credential (SO_PEERCRED), as labd does: invalidate
only from the control user (labd); snapshot also from members of its group, the same
console operators who may open /run/srrx/control.sock. The socket itself is 0666 in a
directory only this service can write: a filesystem group would make this service a
member of labd's group, and with it of labd's control socket.

A lost UART ends the process (exit 3) and systemd's Restart= makes the new open, the
explicit service decision srrx.gnss_uart leaves to its owner. A gpsd disconnect is
followed by a new GpsdClient at most every RECONNECT_MS. Times are CLOCK_BOOTTIME ms.
"""
import argparse
import grp
import json
import os
from pathlib import Path
import pwd
import re
import selectors
import signal
import socket
import stat
import struct
import subprocess
import sys
import time

from .gnss_uart import DEVICE_PATH, GnssUartError, NmeaUartReader, open_lc76g
from .lc76g import JammingMonitor
from .location import MAX_GPSD_BYTES, MAX_INPUT_BYTES, GpsdClient, GpsdJSONDecoder, LocationTracker

SOCKET_PATH = "/run/srrx-loc/location.sock"
GPSD_DEFAULTS = "/etc/default/gpsd"
GNSS_GROUP = "srrx-gnss"
CONTROL_USER = "labd"
SYSTEMCTL = "/usr/bin/systemctl"
RECONNECT_MS = 5000
LOOP_S = 0.05
MAX_REQUEST, MAX_CLIENTS, CLIENT_TIMEOUT_MS = 512, 8, 2000
QUALIFIED_SATELLITES = 6  # build/07:503: 3D with >= 6 satellites
_REASON = re.compile(r"[A-Z][A-Z0-9_]{0,31}")


class LocationdError(RuntimeError):
    """A stable reason code; never a position or received bytes."""


def boottime_ms():
    """Suspend-aware CLOCK_BOOTTIME ms, as srrx.hmi feeds its tracker."""
    clock = getattr(time, "CLOCK_BOOTTIME", None)
    return time.clock_gettime_ns(clock) // 1000000 if clock is not None else int(time.monotonic() * 1000)


def _reject_constant(value):
    raise ValueError("nonfinite JSON constant")


class GpsdMixedDecoder:
    """gpsd WATCH "raw":1 interleaves the receiver's NMEA text with its JSON reports.

    '{' lines go unchanged to GpsdJSONDecoder (its bounds and error count); '$' lines
    only to the jamming monitor; other lines are dropped. Lines are bounded like the
    JSON decoder's (MAX_GPSD_BYTES); an overlong line counts as a decoder error.
    """
    def __init__(self, monitor):
        self.json, self.monitor, self.now_ms = GpsdJSONDecoder(), monitor, 0
        self._line, self._discard, self._overflow = bytearray(), False, 0

    @property
    def errors(self):
        return self.json.errors + self._overflow

    @property
    def buffered_bytes(self):
        return len(self._line) + self.json.buffered_bytes

    def reset(self):
        self._line.clear()
        self._discard = False
        self.json.reset()

    def feed(self, data):
        if isinstance(data, memoryview):
            data = data.tobytes()
        if not isinstance(data, (bytes, bytearray)) or len(data) > MAX_INPUT_BYTES:
            self._overflow += 1
            self.reset()
            return []
        frames, start = [], 0
        while True:
            end = data.find(b"\n", start)
            piece = data[start:] if end < 0 else data[start:end]
            if not self._discard:
                if len(self._line) + len(piece) >= MAX_GPSD_BYTES:
                    self._overflow += 1
                    self._line.clear()
                    self._discard = True
                else:
                    self._line.extend(piece)
            if end < 0:
                return frames
            start = end + 1
            if not self._discard:
                line = bytes(self._line)
                if line.startswith(b"{"):
                    frames.extend(self.json.feed(line + b"\n"))
                elif line.startswith(b"$"):
                    self.monitor.line(line.rstrip(b"\r"), self.now_ms)
            self._line.clear()
            self._discard = False


class JammingGpsdClient(GpsdClient):
    """GpsdClient that also asks gpsd for raw NMEA, for the LC76G jamming sentences only."""
    WATCH = b'?WATCH={"enable":true,"json":true,"raw":1};\n'

    def __init__(self, tracker, host, port, monitor):
        super().__init__(tracker, host, port)
        self.decoder = GpsdMixedDecoder(monitor)

    def poll(self, now_ms):
        self.decoder.now_ms = now_ms
        return super().poll(now_ms)


class TeeTracker:
    """NmeaUartReader's tracker: positions to the tracker, the same bytes to the jamming monitor."""
    def __init__(self, tracker, monitor):
        self.tracker, self.monitor = tracker, monitor

    def ingest_nmea(self, data, now_ms):
        self.monitor.feed(data, now_ms)
        return self.tracker.ingest_nmea(data, now_ms)

    def invalidate(self, source, reason):
        return self.tracker.invalidate(source, reason)


def gpsd_devices(path=GPSD_DEFAULTS):
    """DEVICES words of a Debian /etc/default/gpsd (quotes stripped); None if the file is absent."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read(65537)
    except FileNotFoundError:
        return None
    if len(raw) > 65536:
        raise LocationdError("LOCATIOND_GPSD_DEFAULTS_SIZE")
    devices = []
    for line in raw.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if line.startswith(("DEVICES=", "export DEVICES=")):
            value = line.split("=", 1)[1].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            devices = value.split()
    return devices


def run_quiet(argv):
    """Return code of a fixed argv (no shell, no output kept); bounded at 10 s."""
    return subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=10, check=False).returncode


def raw_preflight(device=DEVICE_PATH, defaults=GPSD_DEFAULTS, runner=run_quiet):
    """Raw mode only if gpsd neither lists this UART in DEVICES nor runs (unit or socket)."""
    devices = gpsd_devices(defaults)
    if devices and any(item == device or os.path.realpath(item) == os.path.realpath(device) for item in devices):
        raise LocationdError("LOCATIOND_GPSD_CONFIGURED_FOR_UART")
    for unit in ("gpsd.service", "gpsd.socket"):
        try:
            code = runner([SYSTEMCTL, "is-active", "--quiet", unit])
        except (OSError, subprocess.SubprocessError):
            raise LocationdError("LOCATIOND_GPSD_STATE_UNKNOWN") from None
        if code == 0:
            raise LocationdError("LOCATIOND_GPSD_ACTIVE")
        if code != 3:
            # Only 3 (LSB "not running": inactive, failed or no such unit) proves gpsd is off;
            # 1 (no bus connection, access denied) or anything else proves nothing (fail closed).
            raise LocationdError("LOCATIOND_GPSD_STATE_UNKNOWN")


def gpsd_preflight(group=GNSS_GROUP):
    """gpsd mode never holds the raw UART group (least privilege; build/07 §18)."""
    try:
        gid = grp.getgrnam(group).gr_gid
    except KeyError:
        return
    if gid == os.getegid() or gid in os.getgroups():
        raise LocationdError("LOCATIOND_GNSS_GROUP_IN_GPSD_MODE")


class LocationService:
    """One tracker fed by exactly one reader: gpsd (client_factory) or raw (reader)."""
    def __init__(self, mode, *, tracker=None, monitor=None, client_factory=None, reader=None):
        if mode not in ("gpsd", "raw") or (mode == "gpsd") != (client_factory is not None) \
                or (mode == "raw") != (reader is not None):
            raise ValueError("gpsd needs a client factory, raw needs a reader, never both")
        self.mode, self.client_factory, self.reader = mode, client_factory, reader
        self.tracker = tracker if tracker is not None else LocationTracker()
        self.monitor = monitor if monitor is not None else JammingMonitor()
        self.client = self.client_started_ms = None
        self.connects = self.resets = 0
        self.last_invalidate = None

    def poll(self, now_ms):
        """Advance the reader; False once a raw UART is lost (the process then exits)."""
        if self.mode == "raw":
            self.reader.poll(now_ms)
            return not self.reader.disconnected
        client = self.client
        if client is None or (client.sock is None and not 0 <= now_ms - self.client_started_ms < RECONNECT_MS):
            # GpsdClient never reconnects by itself: a new client is this service's explicit decision.
            self.client, self.client_started_ms = self.client_factory(self.tracker, self.monitor), now_ms
            self.connects += 1
            self.client.start(now_ms)
        elif client.sock is not None:
            client.poll(now_ms)
        return True

    def invalidate(self, reason):
        for source in ("gpsd", "nmea"):
            self.tracker.invalidate(source, reason)
        self.resets += reason == "GNSS_RESET"
        self.last_invalidate = reason

    def reader_status(self):
        if self.mode == "raw":
            return dict(self.reader.status(), kind="raw")
        client = self.client
        return {"kind": "gpsd", "connects": self.connects,
                "connected": bool(client and client.connected), "watching": bool(client and client.watching),
                "error": None if client is None else client.error}

    def snapshot(self, now_ms):
        location = self.tracker.status(now_ms)
        jamming = self.monitor.status(now_ms)
        qualified = (location["live_fix"] is True and location["mode"] == 3 and type(location["satellites"]) is int
                     and location["satellites"] >= QUALIFIED_SATELLITES and not jamming["active"])
        return {"schema_version": 1, "mode": self.mode, "location": location, "qualified_fix": qualified,
                "jamming": jamming, "reader": self.reader_status(), "resets": self.resets,
                "last_invalidate": self.last_invalidate}

    def close(self):
        if self.reader is not None:
            self.reader.close("NMEA_UART_CLOSED")
        if self.client is not None and self.client.sock is not None:
            self.client.close("GPSD_CLOSED")


class PeerPolicy:
    """invalidate: the control UID only. snapshot: also members (primary or listed) of reader_gid."""
    def __init__(self, control_uid, reader_gid=None):
        self.control_uid, self.reader_gid = control_uid, reader_gid

    @classmethod
    def for_user(cls, name):
        user = pwd.getpwnam(name)
        return cls(user.pw_uid, user.pw_gid)

    def connects(self, uid):
        return uid == self.control_uid or self.allows(uid, "snapshot")

    def allows(self, uid, op):
        if uid == self.control_uid:
            return True
        if op != "snapshot" or self.reader_gid is None:
            return False
        try:
            user = pwd.getpwuid(uid)
            return user.pw_gid == self.reader_gid or user.pw_name in grp.getgrgid(self.reader_gid).gr_mem
        except KeyError:
            return False


def peer_uid(sock):
    return struct.unpack("3i", sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[1]


def bind_socket(path, mode, backlog=MAX_CLIENTS):
    """Listening AF_UNIX socket in a directory this process owns and nobody else can write."""
    path = Path(path)
    info = os.lstat(path.parent)
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o022:
        raise LocationdError("SOCKET_DIRECTORY_NOT_PRIVATE")
    if os.path.lexists(path):
        old = os.lstat(path)
        if not stat.S_ISSOCK(old.st_mode) or old.st_uid != os.geteuid():
            raise LocationdError("SOCKET_PATH_NOT_OUR_STALE_SOCKET")
        path.unlink()
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.setblocking(False)
        listener.bind(str(path))
        os.chmod(path, mode)
        listener.listen(backlog)
    except BaseException:
        listener.close()
        raise
    return listener


class Server:
    """Nonblocking request/reply clients on the listener; at most MAX_CLIENTS, 2 s each."""
    def __init__(self, listener, service, policy):
        self.listener, self.service, self.policy = listener, service, policy
        self.selector = selectors.DefaultSelector()
        self.selector.register(listener, selectors.EVENT_READ, None)
        self.clients = {}

    def _drop(self, client):
        self.clients.pop(client, None)
        try:
            self.selector.unregister(client)
        except (KeyError, ValueError):
            pass
        client.close()

    def handle(self, uid, line, now_ms):
        try:
            request = json.loads(line, parse_constant=_reject_constant)
        except (ValueError, UnicodeError, RecursionError):
            return {"ok": False, "error": "LOCATIOND_REQUEST_JSON"}
        if not isinstance(request, dict):
            return {"ok": False, "error": "LOCATIOND_REQUEST"}
        op = request.get("op")
        if op == "snapshot" and set(request) == {"op"}:
            if not self.policy.allows(uid, op):
                return {"ok": False, "error": "LOCATIOND_PEER_REFUSED"}
            return {"ok": True, "data": self.service.snapshot(now_ms)}
        reason = request.get("reason")
        if op == "invalidate" and set(request) == {"op", "reason"} and type(reason) is str and _REASON.fullmatch(reason):
            if not self.policy.allows(uid, op):
                return {"ok": False, "error": "LOCATIOND_PEER_REFUSED"}
            self.service.invalidate(reason)
            return {"ok": True, "invalidated": reason}
        return {"ok": False, "error": "LOCATIOND_UNKNOWN_REQUEST"}

    def step(self, now_ms, timeout_s=LOOP_S):
        for key, events in self.selector.select(timeout_s):
            if key.data is None:
                try:
                    client, unused = self.listener.accept()
                except (BlockingIOError, InterruptedError):
                    continue
                uid = peer_uid(client)
                if len(self.clients) >= MAX_CLIENTS or not self.policy.connects(uid):
                    client.close()  # refused before any byte is read
                    continue
                client.setblocking(False)
                state = {"rx": bytearray(), "tx": None, "at": now_ms, "uid": uid}
                self.clients[client] = state
                self.selector.register(client, selectors.EVENT_READ, state)
                continue
            client, state = key.fileobj, key.data
            try:
                if events & selectors.EVENT_READ and state["tx"] is None:
                    data = client.recv(MAX_REQUEST + 1)
                    if not data:
                        self._drop(client)
                        continue
                    state["rx"].extend(data)
                    if len(state["rx"]) > MAX_REQUEST:
                        self._drop(client)
                        continue
                    if b"\n" in state["rx"]:
                        reply = self.handle(state["uid"], bytes(state["rx"]).split(b"\n", 1)[0], now_ms)
                        state["tx"] = bytearray(json.dumps(reply, allow_nan=False, separators=(",", ":")).encode() + b"\n")
                        self.selector.modify(client, selectors.EVENT_WRITE, state)
                if events & selectors.EVENT_WRITE and state["tx"]:
                    del state["tx"][:client.send(state["tx"])]
                    if not state["tx"]:
                        self._drop(client)
            except (OSError, ValueError):
                self._drop(client)
        for client, state in list(self.clients.items()):
            if not 0 <= now_ms - state["at"] <= CLIENT_TIMEOUT_MS:
                self._drop(client)

    def close(self):
        for client in list(self.clients):
            self._drop(client)
        self.selector.close()
        self.listener.close()


def serve(service, server, clock=boottime_ms, running=lambda: True):
    """Main loop: 3 when the raw UART is lost (systemd restarts the unit), else 0."""
    while running():
        now = clock()
        if not service.poll(now):
            return 3
        server.step(now)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--gnss", choices=("gpsd", "raw", "off"), required=True)
    ap.add_argument("--socket", default=SOCKET_PATH)
    ap.add_argument("--control-user", default=CONTROL_USER)
    ap.add_argument("--gpsd-host", default="127.0.0.1")
    ap.add_argument("--gpsd-port", type=int, default=2947)
    ap.add_argument("--device", default=DEVICE_PATH)
    ap.add_argument("--gpsd-defaults", default=GPSD_DEFAULTS)
    ap.add_argument("--gnss-group", default=GNSS_GROUP)
    args = ap.parse_args(argv)
    if args.gnss == "off":
        print(json.dumps({"service": "srrx-locationd", "mode": "off", "reading": False}), flush=True)
        return 0
    service = listener = None
    try:
        policy = PeerPolicy.for_user(args.control_user)
        if args.gnss == "gpsd":
            gpsd_preflight(args.gnss_group)
            host, port = args.gpsd_host, args.gpsd_port
            JammingGpsdClient(LocationTracker(), host, port, JammingMonitor())  # loopback endpoint check, never started
            service = LocationService("gpsd", client_factory=lambda tracker, monitor:
                                      JammingGpsdClient(tracker, host, port, monitor))
        else:
            raw_preflight(args.device, args.gpsd_defaults)
            tracker, monitor = LocationTracker(), JammingMonitor()
            reader = NmeaUartReader(open_lc76g(args.device), TeeTracker(tracker, monitor))
            service = LocationService("raw", tracker=tracker, monitor=monitor, reader=reader)
        listener = bind_socket(args.socket, 0o666)
    except (LocationdError, GnssUartError, OSError, KeyError, ValueError) as exc:
        if service is not None:
            service.close()
        print("srrx-locationd refused startup: " + type(exc).__name__ + ": " + str(exc)[:160], file=sys.stderr)
        return 1
    stopping = []
    signal.signal(signal.SIGTERM, lambda *unused: stopping.append(True))
    signal.signal(signal.SIGINT, lambda *unused: stopping.append(True))
    server = Server(listener, service, policy)
    print(json.dumps({"service": "srrx-locationd", "mode": args.gnss, "socket": args.socket}), flush=True)
    try:
        code = serve(service, server, running=lambda: not stopping)
    finally:
        service.close()
        server.close()
        Path(args.socket).unlink(missing_ok=True)
    if code:
        print("srrx-locationd: NMEA_UART_LOST; exiting for a fresh open by the unit restart", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
