"""ADS-B privacy filter of the readsb engine lease (stdlib only; W2 SW-ADSB).

STACK.md:621-622, :825, :2181 and build/07-pz-vstanovlennia.md §16: an aircraft whose readsb
dbFlags has bit 1 (military), 4 (PIA) or 8 (LADD), or whose ICAO address lies in a military range,
is neither shown nor logged, and the profile refuses to run (fail closed) without a pinned
aircraft.csv.gz no older than 90 days.

readsb runs only in srrx-lease-readsb@<alias>.service (software/systemd). It writes aircraft.json
into the unit's private RuntimeDirectory (0700, removed with the lease) and nowhere else: no --net
output, IPAddressDeny=any, and StandardOutput/StandardError are null because readsb's own
diagnostics may name any aircraft. This module is the only path from that file to anything shown
or stored, as four steps of the same unit:

- ``prepare`` (ExecStartPre): refuses the lease unless /var/lib/srrx/adsb/acceptance.json is a
  root-owned acceptance record whose aircraft.csv.gz (tar1090-db csv branch) and military range
  table (tar1090-db ranges.json) match their SHA-256 and size and whose database is at most 90
  days old; reads the USB serial of the leased node (/dev/lab/<alias> -> /sys/dev/char) and
  writes it into the RuntimeDirectory's readsb.env for ``readsb --device``. Only rtla and rtlb
  are accepted: readsb opens RTL-SDR receivers only.
- ``run --detach`` (ExecStartPost): loads the same record again, parses the database itself
  (every row whose flags have bit 1, 4 or 8) and the range table, detaches into the unit's
  cgroup and publishes /data/products/readsb-<alias>/aircraft.json by atomic rename (0640, group
  labd through the setgid directory). An aircraft is published only if its address is a plain
  24-bit ICAO address (readsb "~" non-ICAO and TIS-B track ids cannot be classified), neither
  readsb's dbFlags nor the database's flags have bit 1, 4 or 8 (so a database readsb failed to
  load hides nothing less: STACK.md:2181), and the address is outside every military range. Only
  the README-json.md fields of KEEP are copied; dbFlags itself is dropped ("interesting", bit 2,
  is not used). Hidden aircraft are never counted, named or written anywhere.
- ``stop`` (ExecStopPost): removes the published file, so no stale picture outlives the lease.
- ``accept`` (home base, root): validates a fetched aircraft.csv.gz and ranges.json and writes
  them with the acceptance record. Both upstream files are fetch-only: tar1090-db states no
  licence (GitHub API "license": null, read 07.11.2026), so they are never committed.

status.json next to the product says STARTING, RUNNING, WAITING, STALE, STOPPED or REFUSED with a
stable reason code; it never carries aircraft data. A fatal filter error stops readsb too
($MAINPID of ExecStartPost, checked to be readsb). CI and host tests model this with fixtures;
reception on a Q6A and the accepted database at the home base stay OPEN.
"""
import argparse
import bisect
import datetime
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import select
import signal
import stat
import sys
import tempfile
import time

PRESET = "adsb-public"
ENGINE = "readsb"
# readsb opens RTL-SDR receivers only (deployment/recipes/readsb: RTLSDR=yes, no SoapySDR/airspyhf).
RECEIVERS = ("rtla", "rtlb")
ROOT = Path("/var/lib/srrx/adsb")
ACCEPTANCE_NAME, DATABASE_NAME, RANGES_NAME = "acceptance.json", "aircraft.csv.gz", "ranges.json"
DEV_ROOT = Path("/dev/lab")
SYS_CHAR_ROOT = Path("/sys/dev/char")
PRODUCT, STATUS = "aircraft.json", "status.json"
ENV_FILE, JSON_DIR = "readsb.env", "json"
# The only upstream the record accepts (tar1090-db README: the csv branch is readsb's database).
DATABASE_URL = "https://github.com/wiedehopf/tar1090-db/raw/{commit}/aircraft.csv.gz"
RANGES_URL = "https://raw.githubusercontent.com/wiedehopf/tar1090-db/{commit}/ranges.json"
MAX_AGE_DAYS = 90
FUTURE_SLACK_DAYS = 1
# readsb README-json.md:109-116: military = dbFlags & 1, interesting = & 2, PIA = & 4, LADD = & 8.
MILITARY, INTERESTING, PIA, LADD = 1, 2, 4, 8
HIDE_FLAGS = MILITARY | PIA | LADD
MIN_DATABASE_ROWS = 1000
MAX_RECORD_BYTES = 16 * 1024
MAX_DATABASE_BYTES = 64 * 1024 * 1024
MAX_DATABASE_TEXT_BYTES = 512 * 1024 * 1024
MAX_RANGES_BYTES = 256 * 1024
MAX_AIRCRAFT_JSON_BYTES = 32 * 1024 * 1024
INTERVAL_S = 2.0  # publish period: a live picture without rewriting /data every second
STALE_S = 30.0  # readsb writes aircraft.json every second; older input is not shown as live
READY_TIMEOUT_S = 20.0  # below TimeoutStartSec=30s of the template
PARSE_ERRORS_FATAL = 3
# aircraft.json fields of readsb README-json.md:38-120 that may be published (allowlist; dbFlags,
# the experimental acas_ra/gpsOkBefore and the aggregator rr_lat/rr_lon are not among them).
KEEP = ("hex", "type", "flight", "alt_baro", "alt_geom", "gs", "ias", "tas", "mach", "track", "track_rate", "roll",
        "mag_heading", "true_heading", "baro_rate", "geom_rate", "squawk", "emergency", "category", "nav_qnh",
        "nav_altitude_mcp", "nav_altitude_fms", "nav_heading", "nav_modes", "lat", "lon", "nic", "rc", "seen_pos",
        "version", "nic_baro", "nac_p", "nac_v", "sil", "sil_type", "gva", "sda", "mlat", "tisb", "messages", "seen",
        "rssi", "alert", "spi", "wd", "ws", "oat", "tat", "r", "t", "lastPosition")
STATES = ("STARTING", "RUNNING", "WAITING", "STALE", "STOPPED", "REFUSED")
REFUSALS = ("RECEIVER_NOT_RTL", "ACCEPTANCE_MISSING", "ACCEPTANCE_NOT_TRUSTED", "ACCEPTANCE_SCHEMA",
            "ACCEPTANCE_NOT_ACCEPTED", "DATABASE_MISSING", "DATABASE_NOT_TRUSTED", "DATABASE_DIGEST", "DATABASE_FORMAT",
            "DATABASE_STALE", "DATABASE_DATE_IN_FUTURE", "RANGES_MISSING", "RANGES_NOT_TRUSTED", "RANGES_DIGEST",
            "RANGES_FORMAT", "DEVICE_SERIAL_UNAVAILABLE", "RUN_DIRECTORY_UNUSABLE", "PRODUCTS_UNUSABLE",
            "ENGINE_OUTPUT_UNREADABLE", "ACCEPT_NEEDS_ROOT", "FILTER_INTERNAL")
ICAO = re.compile(r"[0-9a-fA-F]{6}")
HEX6 = re.compile(r"[0-9a-f]{6}")
COMMIT = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
SERIAL = re.compile(r"[A-Za-z0-9._-]{1,32}")
RESULT = re.compile(r"[a-z-]{1,32}")
RECORD_KEYS = ("schema_version", "kind", "status", "accepted_by", "accepted_on", "database", "ranges")
DATABASE_KEYS = ("path", "sha256", "size", "rows", "source_url", "source_commit", "data_date")
RANGES_KEYS = ("path", "sha256", "size", "military_ranges", "source_url", "source_commit", "fetched_on")


class FilterRefused(ValueError):
    """Stable refusal code (REFUSALS); never carries file contents or aircraft data."""

    def __init__(self, code):
        assert code in REFUSALS, code
        super().__init__(code)
        self.code = code


def _refuse(code):
    raise FilterRefused(code)


def admin_trust(path, code, uids=(0,)):
    """A root-owned regular file (no symlink) that neither group nor others may write, below
    directories that only root may change (sticky world-writable ones excepted), as
    decoder_policy._admin_directories: nobody but root can swap it between check and use."""
    path = Path(path)
    try:
        info = os.lstat(path)
        if not path.is_absolute() or not stat.S_ISREG(info.st_mode) or info.st_uid not in uids or info.st_mode & 0o022:
            _refuse(code)
        for parent in path.parents:
            info = os.lstat(parent)
            if info.st_uid not in uids or (info.st_mode & 0o022 and not info.st_mode & stat.S_ISVTX):
                _refuse(code)
    except OSError:
        _refuse(code)


def _read(path, limit, missing, untrusted, trust):
    path = Path(path)
    if not os.path.lexists(path):
        _refuse(missing)
    trust(path, untrusted)
    try:
        with open(path, "rb") as stream:
            data = stream.read(limit + 1)
    except OSError:
        _refuse(missing)
    if len(data) > limit:
        _refuse(untrusted)
    return data


def _date(value, code):
    if type(value) is not str or not DATE.fullmatch(value):
        _refuse(code)
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        _refuse(code)


def utc_today():
    return datetime.datetime.now(datetime.timezone.utc).date()


def expires_on(data_date):
    return data_date + datetime.timedelta(days=MAX_AGE_DAYS)


def check_age(data_date, today):
    """At most MAX_AGE_DAYS old by the system UTC date; a date ahead of it (a wrong clock) refuses too."""
    if data_date > today + datetime.timedelta(days=FUTURE_SLACK_DAYS):
        _refuse("DATABASE_DATE_IN_FUTURE")
    if today > expires_on(data_date):
        _refuse("DATABASE_STALE")


def parse_database(data):
    """(rows, {address: flags & HIDE_FLAGS}) of a readsb aircraft.csv.gz (hex;reg;type;flags;...).
    Flag character j sets bit j when it is '1', as readsb aircraft.c updateDetails reads it."""
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
            text = stream.read(MAX_DATABASE_TEXT_BYTES + 1)
    except (OSError, EOFError, ValueError):
        _refuse("DATABASE_FORMAT")
    if len(text) > MAX_DATABASE_TEXT_BYTES:
        _refuse("DATABASE_FORMAT")
    rows, flagged = 0, {}
    for line in text.split(b"\n"):
        fields = line.split(b";")
        if len(fields) < 4 or not ICAO.fullmatch(fields[0].decode("ascii", "replace")):
            continue
        flags = 0
        for bit, char in enumerate(fields[3][:8]):
            if char == ord("1"):
                flags |= 1 << bit
        rows += 1
        if flags & HIDE_FLAGS:
            address = int(fields[0], 16)
            flagged[address] = flagged.get(address, 0) | (flags & HIDE_FLAGS)
    if rows < MIN_DATABASE_ROWS:
        _refuse("DATABASE_FORMAT")
    return rows, flagged


def parse_ranges(data):
    """Sorted, merged [(first, last)] of tar1090-db ranges.json {"military": [["adf7c8", "afffff"], ...]}."""
    document = _strict_json(data, "RANGES_FORMAT")
    military = document.get("military") if type(document) is dict else None
    if type(military) is not list or not military:
        _refuse("RANGES_FORMAT")
    ranges = []
    for item in military:
        if (type(item) is not list or len(item) != 2 or any(type(v) is not str or not HEX6.fullmatch(v.lower()) for v in item)
                or int(item[0], 16) > int(item[1], 16)):
            _refuse("RANGES_FORMAT")
        ranges.append((int(item[0], 16), int(item[1], 16)))
    merged = []
    for first, last in sorted(ranges):
        if merged and first <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], last))
        else:
            merged.append((first, last))
    return len(ranges), merged


def _strict_json(data, code):
    """One JSON document: UTF-8, no duplicate keys, no NaN/Infinity (else the stable code)."""
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                _refuse(code)
            out[key] = value
        return out
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=lambda _: _refuse(code))
    except (UnicodeDecodeError, ValueError):
        _refuse(code)


def _keys(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        _refuse("ACCEPTANCE_SCHEMA")


def _accepted_by(value):
    if type(value) is not str or not value.strip() or len(value) > 128 or "@" in value or not value.isprintable():
        _refuse("ACCEPTANCE_SCHEMA")  # a name or role, never an e-mail address


def check_record(record, *, root=None, today=None, trust=None):
    """The schema of an acceptance record and the database and range files it names (path, SHA-256,
    size, age). Returns the bytes of both files, read once and hashed as read. root, trust and
    today default to ROOT, admin_trust and the UTC date at call time."""
    root, trust = Path(root or ROOT), trust or admin_trust
    _keys(record, RECORD_KEYS)
    if record["schema_version"] != 1 or record["kind"] != "srrx_adsb_acceptance":
        _refuse("ACCEPTANCE_SCHEMA")
    if record["status"] != "ACCEPTED":
        _refuse("ACCEPTANCE_NOT_ACCEPTED")
    _accepted_by(record["accepted_by"])
    _date(record["accepted_on"], "ACCEPTANCE_SCHEMA")
    database, ranges = record["database"], record["ranges"]
    _keys(database, DATABASE_KEYS)
    _keys(ranges, RANGES_KEYS)
    for entry, name, url in ((database, DATABASE_NAME, DATABASE_URL), (ranges, RANGES_NAME, RANGES_URL)):
        if (entry["path"] != str(root / name) or type(entry["sha256"]) is not str or not SHA256.fullmatch(entry["sha256"])
                or type(entry["size"]) is not int or entry["size"] <= 0 or type(entry["source_commit"]) is not str
                or not COMMIT.fullmatch(entry["source_commit"]) or entry["source_url"] != url.format(commit=entry["source_commit"])):
            _refuse("ACCEPTANCE_SCHEMA")
    if type(database["rows"]) is not int or database["rows"] < MIN_DATABASE_ROWS:
        _refuse("ACCEPTANCE_SCHEMA")
    if type(ranges["military_ranges"]) is not int or ranges["military_ranges"] < 1:
        _refuse("ACCEPTANCE_SCHEMA")
    _date(ranges["fetched_on"], "ACCEPTANCE_SCHEMA")
    check_age(_date(database["data_date"], "ACCEPTANCE_SCHEMA"), today or utc_today())
    blobs = {}
    for entry, name, limit, prefix in ((database, DATABASE_NAME, MAX_DATABASE_BYTES, "DATABASE"),
                                       (ranges, RANGES_NAME, MAX_RANGES_BYTES, "RANGES")):
        data = _read(root / name, limit, prefix + "_MISSING", prefix + "_NOT_TRUSTED", trust)
        if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            _refuse(prefix + "_DIGEST")
        blobs[name] = data
    return blobs


def load_acceptance(*, root=None, today=None, trust=None):
    """(record, file bytes) of the root-owned acceptance record and the files it accepts."""
    root, trust = Path(root or ROOT), trust or admin_trust
    data = _read(root / ACCEPTANCE_NAME, MAX_RECORD_BYTES, "ACCEPTANCE_MISSING", "ACCEPTANCE_NOT_TRUSTED", trust)
    record = _strict_json(data, "ACCEPTANCE_SCHEMA")
    return record, check_record(record, root=root, today=today, trust=trust)


class Filter:
    """Decides, for one readsb aircraft object, whether it may be shown (shown) and what of it (publishable)."""

    def __init__(self, record, flagged, ranges):
        self.record, self.flagged, self.ranges = record, flagged, ranges
        self.starts = [first for first, _ in ranges]
        self.data_date = datetime.date.fromisoformat(record["database"]["data_date"])

    def military_range(self, address):
        index = bisect.bisect_right(self.starts, address) - 1
        return index >= 0 and address <= self.ranges[index][1]

    def shown(self, aircraft):
        if type(aircraft) is not dict:
            return False
        code = aircraft.get("hex")
        if type(code) is not str or not ICAO.fullmatch(code):
            return False  # "~" non-ICAO, TIS-B track ids, malformed: unclassifiable, hidden
        address, flags = int(code, 16), aircraft.get("dbFlags", 0)
        if type(flags) is not int or flags < 0:
            return False
        return not (flags & HIDE_FLAGS or self.flagged.get(address, 0) & HIDE_FLAGS or self.military_range(address))

    @staticmethod
    def publishable(aircraft):
        out = {key: aircraft[key] for key in KEEP if key in aircraft}
        out["hex"] = out["hex"].lower()
        return out

    def document(self, engine, receiver):
        """The published aircraft.json of one readsb aircraft.json document."""
        if type(engine) is not dict or type(engine.get("aircraft")) is not list:
            _refuse("ENGINE_OUTPUT_UNREADABLE")
        now = engine.get("now")
        if type(now) not in (int, float) or not math.isfinite(now):
            _refuse("ENGINE_OUTPUT_UNREADABLE")
        aircraft = [self.publishable(a) for a in engine["aircraft"] if self.shown(a)]
        return {"schema_version": 1, "kind": "srrx_adsb_aircraft", "receiver": receiver, "now": now, "aircraft": aircraft}


def load_filter(*, root=None, today=None, trust=None):
    record, blobs = load_acceptance(root=root, today=today, trust=trust)
    rows, flagged = parse_database(blobs[DATABASE_NAME])
    count, ranges = parse_ranges(blobs[RANGES_NAME])
    if rows != record["database"]["rows"]:
        _refuse("DATABASE_FORMAT")
    if count != record["ranges"]["military_ranges"]:
        _refuse("RANGES_FORMAT")
    return Filter(record, flagged, ranges)


# ---------------------------------------------------------------- unit steps

def _char_node(path):
    info = os.stat(path)  # follows the udev alias to the USB device node
    if not stat.S_ISCHR(info.st_mode):
        return None
    return os.major(info.st_rdev), os.minor(info.st_rdev)


def _sysfs_text(path, limit):
    with open(path, "rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("sysfs attribute too long")
    return data.decode("ascii").strip()


def device_serial(receiver, *, dev_root=DEV_ROOT, sys_char_root=SYS_CHAR_ROOT, char_node=_char_node):
    """The USB serial of the device /dev/lab/<receiver> resolves to (the node DeviceAllow= grants;
    labd checked it against devices.json before the start: engine_leases.reenumeration_check)."""
    try:
        node = char_node(Path(dev_root) / receiver)
        if node is None:
            _refuse("DEVICE_SERIAL_UNAVAILABLE")
        sysfs = Path(sys_char_root) / ("%d:%d" % node)
        if "DEVTYPE=usb_device" not in _sysfs_text(sysfs / "uevent", 4096).splitlines():
            _refuse("DEVICE_SERIAL_UNAVAILABLE")
        serial = _sysfs_text(sysfs / "serial", 256)
    except (OSError, ValueError, TypeError) as exc:
        if isinstance(exc, FilterRefused):
            raise
        _refuse("DEVICE_SERIAL_UNAVAILABLE")
    if not SERIAL.fullmatch(serial):
        _refuse("DEVICE_SERIAL_UNAVAILABLE")
    return serial


def _atomic_write(directory, name, text, mode):
    """Write directory/name by rename from a temporary file in the same directory."""
    descriptor, temporary = tempfile.mkstemp(prefix="." + name + ".", dir=str(directory))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            if hasattr(os, "fchmod"):
                os.fchmod(stream.fileno(), mode)
            stream.write(text)
        os.replace(temporary, Path(directory) / name)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _products(products):
    products = Path(products)
    if not products.is_absolute() or products.is_symlink() or not products.is_dir():
        _refuse("PRODUCTS_UNUSABLE")
    return products


def write_status(products, receiver, state, reason=None, **extra):
    assert state in STATES and (reason is None or reason in REFUSALS)
    document = dict({"schema_version": 1, "kind": "srrx_adsb_status", "preset": PRESET, "receiver": receiver,
                     "state": state, "reason": reason, "updated_at": int(time.time())}, **extra)
    _atomic_write(products, STATUS, json.dumps(document, sort_keys=True) + "\n", 0o640)


def read_status(products):
    try:
        with open(Path(products) / STATUS, "rb") as stream:
            value = json.loads(stream.read(MAX_RECORD_BYTES).decode("utf-8"))
        return value if type(value) is dict else {}
    except (OSError, ValueError):
        return {}


def unpublish(products):
    try:
        os.unlink(Path(products) / PRODUCT)
    except FileNotFoundError:
        pass


def _summary(record):
    data_date = datetime.date.fromisoformat(record["database"]["data_date"])
    return {"database": {"sha256": record["database"]["sha256"], "data_date": record["database"]["data_date"],
                         "expires_on": expires_on(data_date).isoformat()},
            "ranges": {"sha256": record["ranges"]["sha256"], "military_ranges": record["ranges"]["military_ranges"]}}


def _receiver(receiver):
    if receiver not in RECEIVERS:
        _refuse("RECEIVER_NOT_RTL")


def prepare(receiver, run_dir, products, *, root=None, today=None, trust=None, dev_root=DEV_ROOT,
            sys_char_root=SYS_CHAR_ROOT, char_node=_char_node):
    """ExecStartPre: 0 with readsb.env written, or 2 with status REFUSED (readsb never starts)."""
    products = _products(products)
    unpublish(products)
    try:
        _receiver(receiver)
        record, _ = load_acceptance(root=root, today=today, trust=trust)
        serial = device_serial(receiver, dev_root=dev_root, sys_char_root=sys_char_root, char_node=char_node)
        run_dir = Path(run_dir)
        if not run_dir.is_absolute() or run_dir.is_symlink() or not run_dir.is_dir():
            _refuse("RUN_DIRECTORY_UNUSABLE")
        try:
            (run_dir / JSON_DIR).mkdir(mode=0o700, exist_ok=True)
            _atomic_write(run_dir, ENV_FILE, "SRRX_READSB_SERIAL=" + serial + "\n", 0o600)
        except OSError:
            _refuse("RUN_DIRECTORY_UNUSABLE")
    except FilterRefused as refused:
        write_status(products, receiver if receiver in RECEIVERS else None, "REFUSED", refused.code)
        return 2
    write_status(products, receiver, "STARTING", **_summary(record))
    return 0


def _stop_engine(environ=os.environ, proc=Path("/proc")):
    """SIGTERM to the unit's main process ($MAINPID of ExecStartPost) when it is readsb."""
    value = environ.get("MAINPID", "")
    if not value.isdigit():
        return False
    try:
        if (proc / value / "comm").read_text(encoding="ascii").strip() != ENGINE:
            return False
        os.kill(int(value), signal.SIGTERM)
        return True
    except (OSError, ValueError):
        return False


class Server:
    """The publish loop of ``run``: one cycle every INTERVAL_S until stopped or refused."""

    def __init__(self, flt, receiver, run_dir, products, *, interval=INTERVAL_S, stale_s=STALE_S, clock=time.time,
                 today=utc_today):
        self.filter, self.receiver = flt, receiver
        self.input, self.products = Path(run_dir) / JSON_DIR / PRODUCT, Path(products)
        self.interval, self.stale_s, self.clock, self.today = interval, stale_s, clock, today
        self.last, self.errors, self.state, self.stopping = None, 0, None, False

    def status(self, state):
        """status.json only on a change of state: the product itself carries readsb's "now"."""
        if state != self.state:
            write_status(self.products, self.receiver, state, **_summary(self.filter.record))
            self.state = state

    def cycle(self):
        check_age(self.filter.data_date, self.today())
        try:
            info = os.stat(self.input)
        except FileNotFoundError:
            unpublish(self.products)
            return self.status("WAITING")
        key = (info.st_ino, info.st_mtime_ns, info.st_size)
        if key == self.last:
            if self.clock() - info.st_mtime > self.stale_s:
                unpublish(self.products)
                self.status("STALE")
            return None
        if info.st_size > MAX_AIRCRAFT_JSON_BYTES:
            _refuse("ENGINE_OUTPUT_UNREADABLE")
        try:
            with open(self.input, "rb") as stream:
                engine = _strict_json(stream.read(MAX_AIRCRAFT_JSON_BYTES + 1), "ENGINE_OUTPUT_UNREADABLE")
            document = self.filter.document(engine, self.receiver)
        except (OSError, ValueError) as exc:  # FilterRefused is a ValueError
            self.errors += 1
            if self.errors >= PARSE_ERRORS_FATAL:
                raise FilterRefused("ENGINE_OUTPUT_UNREADABLE") from exc
            return None
        self.errors, self.last = 0, key
        _atomic_write(self.products, PRODUCT, json.dumps(document, sort_keys=True, allow_nan=False) + "\n", 0o640)
        return self.status("RUNNING")

    def serve(self, ready=None, sleep=time.sleep, max_cycles=None):
        """0 after a stop request, 2 after a refusal (readsb is stopped too)."""
        cycles = 0
        try:
            self.status("RUNNING")
            if ready is not None:
                ready()
            while not self.stopping and (max_cycles is None or cycles < max_cycles):
                self.cycle()
                cycles += 1
                if not self.stopping and (max_cycles is None or cycles < max_cycles):
                    sleep(self.interval)
        except FilterRefused as refused:
            unpublish(self.products)
            write_status(self.products, self.receiver, "REFUSED", refused.code, **_summary(self.filter.record))
            _stop_engine()
            return 2
        except Exception:  # noqa: BLE001 - nothing may keep publishing after an unexpected error
            unpublish(self.products)
            write_status(self.products, self.receiver, "REFUSED", "FILTER_INTERNAL")
            _stop_engine()
            return 2
        unpublish(self.products)
        write_status(self.products, self.receiver, "STOPPED", **_summary(self.filter.record))
        return 0


def _detach(work):
    """Fork; the child leaves the session, runs work(ready) and stays in the unit's cgroup (the unit
    kills it with readsb). The parent (the ExecStartPost process) returns 0 once the child is
    ready, 2 if it died first or did not report within READY_TIMEOUT_S."""
    read_end, write_end = os.pipe()
    pid = os.fork()
    if pid:
        os.close(write_end)
        try:
            ready, _, _ = select.select([read_end], [], [], READY_TIMEOUT_S)
            return 0 if ready and os.read(read_end, 1) == b"1" else 2
        finally:
            os.close(read_end)
    os.close(read_end)
    os.setsid()
    os.chdir("/")

    def ready():
        os.write(write_end, b"1")
        os.close(write_end)
    try:
        code = work(ready)
    except BaseException:  # noqa: BLE001
        code = 2
    os._exit(code)


def run(receiver, run_dir, products, *, detach=False, root=None, today=None, trust=None, interval=INTERVAL_S,
        max_cycles=None):
    products = _products(products)
    try:
        _receiver(receiver)
        flt = load_filter(root=root, today=today, trust=trust)
    except FilterRefused as refused:
        unpublish(products)
        write_status(products, receiver if receiver in RECEIVERS else None, "REFUSED", refused.code)
        return 2
    server = Server(flt, receiver, run_dir, products, interval=interval,
                    today=(lambda: today) if today is not None else utc_today)

    def work(ready=None):
        def stop(_signum, _frame):
            server.stopping = True
        previous = {number: signal.signal(number, stop) for number in (signal.SIGTERM, signal.SIGINT)}
        try:
            return server.serve(ready=ready, max_cycles=max_cycles)
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)
    return _detach(work) if detach else work()


def stop(receiver, products, environ=os.environ):
    """ExecStopPost: never leaves a published picture; a REFUSED status keeps its reason."""
    try:
        products = _products(products)
    except FilterRefused:
        return 0
    unpublish(products)
    previous = read_status(products)
    if previous.get("state") != "REFUSED":
        result = environ.get("SERVICE_RESULT", "")
        write_status(products, receiver if receiver in RECEIVERS else None, "STOPPED",
                     service_result=result if RESULT.fullmatch(result) else None)
    return 0


def accept(database, database_commit, data_date, ranges, ranges_commit, fetched_on, accepted_by, *, root=None,
           today=None):
    """Home base: validate the fetched files, install them and write the acceptance record. Run as
    root (load_acceptance trusts only root-owned files); the files stay out of git (fetch-only)."""
    for commit in (database_commit, ranges_commit):
        if type(commit) is not str or not COMMIT.fullmatch(commit):
            _refuse("ACCEPTANCE_SCHEMA")
    _accepted_by(accepted_by)
    check_age(_date(data_date, "ACCEPTANCE_SCHEMA"), today or utc_today())
    _date(fetched_on, "ACCEPTANCE_SCHEMA")
    blobs = {}
    for path, limit, code in ((database, MAX_DATABASE_BYTES, "DATABASE_FORMAT"), (ranges, MAX_RANGES_BYTES, "RANGES_FORMAT")):
        try:
            with open(path, "rb") as stream:
                blobs[path] = stream.read(limit + 1)
        except OSError:
            _refuse(code)
        if len(blobs[path]) > limit:
            _refuse(code)
    rows, _ = parse_database(blobs[database])
    count, _ = parse_ranges(blobs[ranges])
    root = Path(root or ROOT)
    root.mkdir(mode=0o755, parents=True, exist_ok=True)
    record = {"schema_version": 1, "kind": "srrx_adsb_acceptance", "status": "ACCEPTED", "accepted_by": accepted_by,
              "accepted_on": (today or utc_today()).isoformat(),
              "database": {"path": str(root / DATABASE_NAME), "sha256": hashlib.sha256(blobs[database]).hexdigest(),
                           "size": len(blobs[database]), "rows": rows, "source_url": DATABASE_URL.format(commit=database_commit),
                           "source_commit": database_commit, "data_date": data_date},
              "ranges": {"path": str(root / RANGES_NAME), "sha256": hashlib.sha256(blobs[ranges]).hexdigest(),
                         "size": len(blobs[ranges]), "military_ranges": count, "source_url": RANGES_URL.format(commit=ranges_commit),
                         "source_commit": ranges_commit, "fetched_on": fetched_on}}
    for name, path in ((DATABASE_NAME, database), (RANGES_NAME, ranges)):
        descriptor, temporary = tempfile.mkstemp(prefix="." + name + ".", dir=str(root))
        with os.fdopen(descriptor, "wb") as stream:
            if hasattr(os, "fchmod"):
                os.fchmod(stream.fileno(), 0o644)
            stream.write(blobs[path])
        os.replace(temporary, root / name)
    _atomic_write(root, ACCEPTANCE_NAME, json.dumps(record, indent=2, sort_keys=True) + "\n", 0o644)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    commands = parser.add_subparsers(dest="operation", required=True)
    for name in ("prepare", "run", "stop"):
        step = commands.add_parser(name)
        step.add_argument("--receiver", required=True)
        step.add_argument("--products", type=Path, required=True)
        if name != "stop":
            step.add_argument("--run-dir", type=Path, required=True)
        if name == "run":
            step.add_argument("--detach", action="store_true")
    commands.add_parser("status")
    accepting = commands.add_parser("accept", help="home base, as root: install a fetched database and range table")
    for name in ("--database", "--ranges"):
        accepting.add_argument(name, type=Path, required=True)
    for name in ("--database-commit", "--data-date", "--ranges-commit", "--fetched-on", "--accepted-by"):
        accepting.add_argument(name, required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == "prepare":
            return prepare(args.receiver, args.run_dir, args.products)
        if args.operation == "run":
            return run(args.receiver, args.run_dir, args.products, detach=args.detach)
        if args.operation == "stop":
            return stop(args.receiver, args.products)
        if args.operation == "status":
            record, _ = load_acceptance()
            print(json.dumps(dict({"preset": PRESET, "status": "ACCEPTED"}, **_summary(record)), sort_keys=True))
            return 0
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            _refuse("ACCEPT_NEEDS_ROOT")
        record = accept(args.database, args.database_commit, args.data_date, args.ranges, args.ranges_commit,
                        args.fetched_on, args.accepted_by)
        print(json.dumps(dict({"preset": PRESET, "status": "ACCEPTED"}, **_summary(record)), sort_keys=True))
        return 0
    except FilterRefused as refused:
        print(json.dumps({"preset": PRESET, "status": "REFUSED", "reason": refused.code}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
