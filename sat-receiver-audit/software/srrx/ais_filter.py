"""AIS privacy filter of the AIS-catcher engine lease (STACK.md:599, :621, :882, :2182; build/07 §16).

AIS-catcher v0.70+lab1 (deployment/recipes/ais-catcher) runs only in the lease unit
srrx-lease-aiscatcher@<alias>.service. It writes its decoded messages as JSON lines
(`-f <fifo> MSGFORMAT JSON_FULL`, the "full" key names of the pinned v0.70 Source/JSON/KeyDefs.h;
the recipe's runtime_check.py reads the same names from the built binary) into a FIFO inside the
unit's 0700 RuntimeDirectory, and nothing to stdout (`-o 0`): the raw stream exists only in a kernel
pipe buffer, never on disk or in the journal. This filter runs in the same unit and sandbox
(User=lab, ReadWritePaths=/data/products/aiscatcher-%i, IPAddressDeny=any) and keeps per-MMSI state
in memory only. Rules:

1. A vessel is published only after a static report: type 5, type 19 or type 24 part B. Its ship
   type must be known (1..99, the table of the pinned engine, Source/JSON/Keys.cpp:276) and not 35
   (military operations). Until then nothing about the MMSI is kept or written: the dynamic reports
   before the static one are dropped, not buffered.
2. A static report with type 35 deletes a published vessel from memory and from the products file
   at once, and the MMSI stays suppressed for the life of the lease (RAM only, bounded): a later
   static report with another type does not bring it back.
3. Only vessel messages count (1, 2, 3, 5, 18, 19, 24, 27); base stations, aids to navigation, SAR
   aircraft, safety and binary messages are dropped. Malformed or oversized lines are dropped.
4. Nothing is logged about any vessel, published or not: no MMSI, no count, no message text. The
   only output besides the products file is a stable error code (ERRORS) on a fatal error.

The products file is /data/products/aiscatcher-<alias>/vessels.json, a snapshot replaced
atomically (no history, so a deletion leaves nothing behind); vessels not heard for TTL_S drop out,
and a new lease starts with an empty snapshot. `prepare` (ExecStartPre) writes the receiver
selection of AIS-catcher as a response file (`-d <serial> -s <rate>`, the serial from
/etc/srrx/devices.json) and creates the FIFO, both 0600. Stdlib only; no network, no device access.
Reception on the Q6A is a device row and stays OPEN.
"""
import argparse
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import sys
import tempfile
import time

ENGINE = "aiscatcher"
RECEIVERS = ("rtla", "rtlb", "hfplus")  # srrx.engine_leases.RECEIVERS (test_ais_filter compares)
DEVICE_KEYS = {"rtla": "rtl_a", "rtlb": "rtl_b", "hfplus": "hfplus"}  # devices.json "usb" keys
# RTL-SDR at AIS-catcher's RTLSDR default rate (Source/Device/RTLSDR.h:71); HF+ at 192000, a rate of
# the airspyhf list (STACK.md:143) that the v0.70 model takes without resampling (Source/DSP/Model.cpp:128).
SAMPLE_RATES = {"rtla": 1536000, "rtlb": 1536000, "hfplus": 192000}
RTL_SERIAL = re.compile(r"LAB[A-Z]{3}")  # build/08-zbyrannia.md:273, deploy.validate_devices
# The HF+ USB serial string is "AIRSPYHF SN:" and 16 hex digits (deploy._usb); AIS-catcher lists an
# HF+ by the same number as 16 upper-case hex digits (Source/Utilities/Convert.cpp:97-101).
HFPLUS_SERIAL = re.compile(r"AIRSPYHF SN:([0-9A-Fa-f]{16})")
ARGS_FILE, FIFO_FILE, OUTPUT_FILE = "receiver.args", "ais.fifo", "vessels.json"
PRODUCTS_ROOT = "/data/products"

# Keys of AIS-catcher v0.70 JSON_FULL output that this filter reads (Source/JSON/KeyDefs.h "full").
FIELDS = ("class", "type", "mmsi", "shiptype", "partno", "lat", "lon", "speed", "course", "heading", "status",
          "shipname", "callsign")
VESSEL_TYPES = frozenset((1, 2, 3, 5, 18, 19, 24, 27))
POSITION_TYPES = frozenset((1, 2, 3, 18, 19, 27))
MILITARY_SHIPTYPE = 35
KNOWN_SHIPTYPES = range(1, 100)
MAX_LINE = 64 * 1024
MAX_VESSELS = 2048
MAX_SUPPRESSED = 4096
TTL_S = 1800
WRITE_INTERVAL_S = 1.0
MAX_DEVICES_BYTES = 64 * 1024
ERRORS = ("AIS_FILTER_BAD_REQUEST", "AIS_FILTER_DEVICES_UNAVAILABLE", "AIS_FILTER_RECEIVER_UNBOUND",
          "AIS_FILTER_RUNTIME_UNAVAILABLE", "AIS_FILTER_OUTPUT_UNAVAILABLE", "AIS_FILTER_INPUT_UNAVAILABLE")
_TEXT = re.compile(r"[^A-Za-z0-9 .,'/()&+-]")


class FilterError(RuntimeError):
    """Stable code from ERRORS; never carries input text, a serial or an MMSI."""


def _fail(code):
    raise FilterError(code)


def _int(value, low, high):
    return value if type(value) is int and low <= value <= high else None


def _number(value, low, high):
    if type(value) not in (int, float) or value != value:  # NaN never equals itself
        return None
    return float(value) if low <= value <= high else None


def _text(value, limit):
    if type(value) is not str:
        return None
    cleaned = _TEXT.sub("", value).strip()[:limit]
    return cleaned or None


def parse_line(line):
    """One AIS-catcher JSON line -> the dict of an AIS message, or None (malformed, oversized, other class)."""
    if type(line) is bytes:
        if len(line) > MAX_LINE:
            return None
        try:
            line = line.decode("utf-8")
        except UnicodeDecodeError:
            return None
    if type(line) is not str or len(line) > MAX_LINE:
        return None
    try:
        record = json.loads(line)
    except ValueError:
        return None
    if type(record) is not dict or record.get("class") != "AIS":
        return None
    return record


def is_published_shiptype(shiptype):
    """Rule 1: a known ship type (1..99) that is not 35."""
    return type(shiptype) is int and shiptype in KNOWN_SHIPTYPES and shiptype != MILITARY_SHIPTYPE


def is_static(record):
    """Type 5, type 19 or type 24 part B (partno 1): the reports that carry the ship type."""
    kind = record.get("type")
    return kind in (5, 19) or (kind == 24 and record.get("partno") == 1)


class VesselFilter:
    """Per-MMSI state of one lease; feed() returns True when the published set changed."""

    def __init__(self, max_vessels=MAX_VESSELS, ttl_s=TTL_S):
        self.max_vessels, self.ttl_s = max_vessels, ttl_s
        self.vessels = {}  # mmsi -> published vessel, least recently heard first
        self.suppressed = {}  # mmsi -> time of its last type-35 report (memory only, bounded)

    def feed(self, record, now):
        if type(record) is not dict:
            return False
        kind, mmsi = _int(record.get("type"), 1, 27), _int(record.get("mmsi"), 1, 999_999_999)
        if kind not in VESSEL_TYPES or mmsi is None:
            return False
        static = is_static(record)
        if static and record.get("shiptype") == MILITARY_SHIPTYPE:
            self.suppressed.pop(mmsi, None)
            self.suppressed[mmsi] = now
            while len(self.suppressed) > MAX_SUPPRESSED:
                self.suppressed.pop(next(iter(self.suppressed)))
            return self.vessels.pop(mmsi, None) is not None  # rule 2: deleted at once
        if mmsi in self.suppressed:
            return False
        vessel = self.vessels.pop(mmsi, None)
        if vessel is None:
            if not (static and is_published_shiptype(record.get("shiptype"))):
                return False  # rule 1: nothing about an unpublished vessel is kept
            vessel = {"mmsi": mmsi}
        if static and is_published_shiptype(record.get("shiptype")):
            vessel["shiptype"] = record["shiptype"]
        if kind in (5, 19) or (kind == 24 and record.get("partno") == 0):
            name = _text(record.get("shipname"), 20)
            if name:
                vessel["shipname"] = name
        if kind == 5 or (kind == 24 and record.get("partno") == 1):
            callsign = _text(record.get("callsign"), 7)
            if callsign:
                vessel["callsign"] = callsign
        if kind in POSITION_TYPES:
            lat, lon = _number(record.get("lat"), -90, 90), _number(record.get("lon"), -180, 180)
            if lat is not None and lon is not None:
                vessel["lat"], vessel["lon"] = round(lat, 5), round(lon, 5)
            for key, low, high in (("speed", 0, 102.2), ("course", 0, 359.9)):
                value = _number(record.get(key), low, high)
                if value is not None:
                    vessel[key] = round(value, 1)
            heading = _int(record.get("heading"), 0, 359)
            if heading is not None:
                vessel["heading"] = heading
            status = _int(record.get("status"), 0, 15) if kind in (1, 2, 3) else None
            if status is not None:
                vessel["status"] = status
        vessel["last_seen"] = now
        self.vessels[mmsi] = vessel  # re-inserted last: eviction drops the least recently heard
        while len(self.vessels) > self.max_vessels:
            self.vessels.pop(next(iter(self.vessels)))
        return True

    def expire(self, now):
        stale = [m for m, v in self.vessels.items() if now - v["last_seen"] > self.ttl_s]
        for mmsi in stale:
            del self.vessels[mmsi]
        return bool(stale)

    def snapshot(self, receiver, wall, now, active=True):
        vessels = []
        for mmsi in sorted(self.vessels):
            vessel = dict(self.vessels[mmsi])
            vessel["age_s"] = max(0, int(now - vessel.pop("last_seen")))
            vessels.append(vessel)
        return {"schema_version": 1, "kind": "srrx_ais_vessels", "engine": ENGINE, "receiver": receiver,
                "active": active, "updated_utc": int(wall),
                "rule": "static 5/19/24B with ship type 1..99 and not 35; a late 35 deletes",
                "vessels": vessels}


def write_snapshot(directory, document):
    """vessels.json replaced atomically in the products directory (temp file, fsync, rename), 0640."""
    directory = Path(directory)
    data = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    try:
        fd, temporary = tempfile.mkstemp(prefix=".vessels-", suffix=".tmp", dir=directory)
    except OSError:
        _fail("AIS_FILTER_OUTPUT_UNAVAILABLE")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o640)
        os.replace(temporary, directory / OUTPUT_FILE)
    except OSError:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        _fail("AIS_FILTER_OUTPUT_UNAVAILABLE")


def device_args(receiver, devices):
    """AIS-catcher arguments that select one leased receiver: -d <serial> -s <rate>."""
    if receiver not in RECEIVERS:
        _fail("AIS_FILTER_BAD_REQUEST")
    try:
        serial = devices["usb"][DEVICE_KEYS[receiver]]["serial"]
    except (KeyError, TypeError):
        _fail("AIS_FILTER_RECEIVER_UNBOUND")
    if receiver == "hfplus":
        match = HFPLUS_SERIAL.fullmatch(serial) if type(serial) is str else None
        if match is None:
            _fail("AIS_FILTER_RECEIVER_UNBOUND")
        serial = match.group(1).upper()
    elif type(serial) is not str or not RTL_SERIAL.fullmatch(serial):
        _fail("AIS_FILTER_RECEIVER_UNBOUND")
    return ["-d", serial, "-s", str(SAMPLE_RATES[receiver])]


def load_devices(path):
    try:
        with open(path, "rb") as stream:
            data = stream.read(MAX_DEVICES_BYTES + 1)
        devices = json.loads(data.decode("utf-8")) if len(data) <= MAX_DEVICES_BYTES else None
    except (OSError, UnicodeDecodeError, ValueError):
        devices = None
    if type(devices) is not dict:
        _fail("AIS_FILTER_DEVICES_UNAVAILABLE")
    return devices


def prepare(receiver, devices_path, runtime):
    """ExecStartPre: the response file AIS-catcher reads as @<file> and the FIFO, both 0600 in the
    unit's own RuntimeDirectory (0700, owned by the lease user)."""
    args = device_args(receiver, load_devices(devices_path))
    runtime = Path(runtime)
    try:
        info = os.lstat(runtime)
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
            _fail("AIS_FILTER_RUNTIME_UNAVAILABLE")
        fd = os.open(runtime / ARGS_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(fd, "w", encoding="ascii", newline="\n") as stream:
            stream.write("".join(item + "\n" for item in args))
        os.mkfifo(runtime / FIFO_FILE, 0o600)
    except OSError:
        _fail("AIS_FILTER_RUNTIME_UNAVAILABLE")
    return args


def run(read, receiver, output, clock=time.monotonic, wall=time.time, stop=lambda: False):
    """read(timeout_s) -> bytes, b"" at the end of the stream or None after the timeout. Feeds every
    complete JSON line and keeps vessels.json current: a deletion at once, other changes at most
    once per WRITE_INTERVAL_S. The last snapshot says active false."""
    filt, buffer, pending = VesselFilter(), b"", False
    write_snapshot(output, filt.snapshot(receiver, wall(), clock()))  # a new lease never shows old vessels
    last_write = clock()
    while not stop():
        chunk = read(WRITE_INTERVAL_S)
        now, urgent = clock(), False
        if chunk == b"":
            break
        if chunk:
            lines = (buffer + chunk).split(b"\n")
            buffer = lines.pop()
            if len(buffer) > MAX_LINE:
                buffer = b""  # an oversized line is dropped; the stream resynchronises at the next newline
            for line in lines:
                record = parse_line(line)
                if record is None:
                    continue
                known = record.get("mmsi") in filt.vessels
                if filt.feed(record, now):
                    pending = True
                    urgent = urgent or (known and record.get("mmsi") not in filt.vessels)
        pending = filt.expire(now) or pending
        if pending and (urgent or now - last_write >= WRITE_INTERVAL_S):
            write_snapshot(output, filt.snapshot(receiver, wall(), now))
            last_write, pending = now, False
    write_snapshot(output, filt.snapshot(receiver, wall(), clock(), active=False))
    return filt


def fifo_reader(fd):
    """read() for run(): select with a timeout, then one os.read of the FIFO."""
    def read(timeout_s):
        ready, _, _ = select.select([fd], [], [], timeout_s)
        return os.read(fd, 65536) if ready else None
    return read


def serve(receiver, fifo, output, detach=False, products_root=PRODUCTS_ROOT):
    """ExecStartPost: read the FIFO that AIS-catcher writes. The FIFO is opened read-write (Linux,
    fifo(7)): the open never blocks, and the filter keeps reading until systemd stops the unit,
    which it does when AIS-catcher, the main process, exits. With detach the parent returns at once
    and the child stays in the unit's cgroup (systemd.service(5) kills forked processes of
    ExecStartPre=, not of ExecStartPost=); if the child ends, AIS-catcher's next write fails and the
    engine stops, so no output ever passes unfiltered."""
    if receiver not in RECEIVERS or Path(output) != Path(products_root) / (ENGINE + "-" + receiver):
        _fail("AIS_FILTER_BAD_REQUEST")
    try:
        info = os.lstat(fifo)
        if not stat.S_ISFIFO(info.st_mode):
            _fail("AIS_FILTER_INPUT_UNAVAILABLE")
        fd = os.open(fifo, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        _fail("AIS_FILTER_INPUT_UNAVAILABLE")
    if detach and os.fork() != 0:
        os.close(fd)
        return None
    stopping = []
    signal.signal(signal.SIGTERM, lambda *_: stopping.append(True))
    try:
        run(fifo_reader(fd), receiver, output, stop=lambda: bool(stopping))
    finally:
        os.close(fd)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="AIS privacy filter of the AIS-catcher engine lease")
    sub = parser.add_subparsers(dest="op", required=True)
    first = sub.add_parser("prepare", help="ExecStartPre: response file and FIFO in the RuntimeDirectory")
    first.add_argument("--receiver", required=True)
    first.add_argument("--devices", type=Path, required=True)
    first.add_argument("--runtime", type=Path, required=True)
    second = sub.add_parser("serve", help="ExecStartPost: FIFO -> /data/products/aiscatcher-<alias>/vessels.json")
    second.add_argument("--receiver", required=True)
    second.add_argument("--fifo", type=Path, required=True)
    second.add_argument("--output", type=Path, required=True)
    second.add_argument("--detach", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.op == "prepare":
            prepare(args.receiver, args.devices, args.runtime)
        else:
            serve(args.receiver, args.fifo, args.output, args.detach)
    except FilterError as exc:
        print(str(exc), file=sys.stderr)  # a stable code only
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
