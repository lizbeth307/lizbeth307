"""Strict OMM element ingestion and SatDump export (stdlib only, no network).

Input is a CelesTrak GP/OMM file the operator copied in (home Wi-Fi or
USB/microSD, STACK.md:884): a JSON array of objects, or a CSV whose header is
the 17 OMM_FIELDS. This module never fetches anything; it has no socket/HTTP
code. Only NORAD ids from the allowlist file survive; ids are never hard-coded.

Validation fails closed for the whole file: size <= 4 MiB, UTF-8 JSON without
duplicate keys or NaN/Infinity, exactly the 17 OMM fields per record, finite
in-range values, EPHEMERIS_TYPE 0 (SGP4) and CLASSIFICATION_TYPE "U" only,
NORAD ids 1..999999 (6-digit ids accepted, STACK.md:141). One record per NORAD
id survives: the newest epoch wins, an identical duplicate is dropped, and the
same epoch with different elements is rejected as contradictory.

Age is a warning, never a refusal (STACK.md:884): > 3 days for the ISS role,
> 7 days otherwise, plus unknown age (no clock) or an epoch more than one day
after the clock. A warning or an unverified clock clears auto_pointing_allowed;
reception is never gated here. Stationary GEO: |n - 1.00274| < 0.0005 rev/day,
evaluated at 1e-12 rev/day resolution so both edges of the band are exclusive.

SatDump export writes the 17 columns in CelesTrak's CSV order with a header row
(build/07:386). Conservative note: that order is CelesTrak's documented header;
agreement with SatDump 1aedd60's CSV reader was not checked in this pass and
belongs to the BUILDER check POL-10.

Allowlist file: {"schema_version": 1, "kind": "srrx_orbit_allowlist",
"targets": [{"norad_id": int, "name": str, "role": ROLE}]}; role ISS selects the
3-day age warning, LRPT the V-dipole hint, QO100 the Es'hail-2 record (at most one).
"""
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import tempfile

OMM_FIELDS = ("OBJECT_NAME", "OBJECT_ID", "EPOCH", "MEAN_MOTION", "ECCENTRICITY", "INCLINATION",
              "RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY", "EPHEMERIS_TYPE",
              "CLASSIFICATION_TYPE", "NORAD_CAT_ID", "ELEMENT_SET_NO", "REV_AT_EPOCH",
              "BSTAR", "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT")
FLOAT_RANGES = {"MEAN_MOTION": (0.01, 20.0), "ECCENTRICITY": (0.0, 0.999999), "INCLINATION": (0.0, 180.0),
                "RA_OF_ASC_NODE": (0.0, 360.0), "ARG_OF_PERICENTER": (0.0, 360.0), "MEAN_ANOMALY": (0.0, 360.0),
                "BSTAR": (-1.0, 1.0), "MEAN_MOTION_DOT": (-1.0, 1.0), "MEAN_MOTION_DDOT": (-1.0, 1.0)}
INT_RANGES = {"EPHEMERIS_TYPE": (0, 0), "NORAD_CAT_ID": (1, 999999), "ELEMENT_SET_NO": (0, 9999),
              "REV_AT_EPOCH": (0, 9999999)}
ROLES = ("QO100", "ISS", "LRPT", "GEO", "OTHER")
MAX_OMM_BYTES = 4 * 1024 * 1024
MAX_ALLOWLIST_BYTES = 64 * 1024
MAX_RECORDS = 20000
MAX_TARGETS = 256
MAX_EXPORT_RECORDS = 1024
GEO_MEAN_MOTION = 1.00274
GEO_TOLERANCE = 0.0005
AGE_LIMIT_DAYS = {"ISS": 3.0}
DEFAULT_AGE_LIMIT_DAYS = 7.0
FUTURE_EPOCH_DAYS = 1.0
RECORD_FIELDS = frozenset(("norad_id", "name", "role", "elements", "epoch_utc", "epoch_unix_s", "age_days",
                           "age_limit_days", "age_warning", "age_warning_reason", "time_verified", "stationary",
                           "auto_pointing_allowed"))
_EPOCH = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?\Z", re.ASCII)
_COSPAR = re.compile(r"\d{4}-\d{3}[A-Z]{1,3}\Z", re.ASCII)
_NAME = re.compile(r"[\x20-\x7e]{1,64}\Z")
_FLOAT_TEXT = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d{1,3})?\Z", re.ASCII)
_INT_TEXT = re.compile(r"[+-]?\d{1,9}\Z", re.ASCII)
_UNIX0 = datetime(1970, 1, 1, tzinfo=timezone.utc)


class OrbitError(ValueError):
    pass


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise OrbitError("duplicate JSON object key")
        result[key] = value
    return result


def _constant(value):
    raise OrbitError("non-finite JSON constant")


def _read(path, limit):
    with open(path, "rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise OrbitError("file exceeds the size limit")
    return data


def _json(data):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise OrbitError("invalid JSON") from error


def _float(value, field):
    if type(value) is str:
        if not _FLOAT_TEXT.match(value):
            raise OrbitError(field + " is not a plain decimal number")
        value = float(value)
    elif type(value) not in (int, float):
        raise OrbitError(field + " must be a number")
    try:
        number = float(value)
    except OverflowError as error:
        raise OrbitError(field + " must be finite") from error
    low, high = FLOAT_RANGES[field]
    if not math.isfinite(number) or not low <= number <= high:
        raise OrbitError(field + " out of range")
    return number


def _int(value, field):
    if type(value) is str:  # CSV text; JSON must carry a real integer.
        if not _INT_TEXT.match(value):
            raise OrbitError(field + " is not an integer")
        value = int(value)
    if type(value) is not int:
        raise OrbitError(field + " must be an integer")
    low, high = INT_RANGES[field]
    if not low <= value <= high:
        raise OrbitError(field + " out of range" + (" (SGP4 elements only)" if field == "EPHEMERIS_TYPE" else ""))
    return value


def _epoch(value):
    match = _EPOCH.match(value) if type(value) is str else None
    if not match:
        raise OrbitError("EPOCH must be YYYY-MM-DDTHH:MM:SS[.ffffff] UTC")
    year, month, day, hour, minute, second = (int(x) for x in match.groups()[:6])
    fraction = int((match.group(7) or "0").ljust(6, "0"))
    if not 1957 <= year <= 2099:
        raise OrbitError("EPOCH year out of range")
    try:
        moment = datetime(year, month, day, hour, minute, second, fraction, tzinfo=timezone.utc)
    except ValueError as error:
        raise OrbitError("EPOCH is not a valid UTC time") from error
    return moment


def elements(raw):
    """Validate one raw OMM mapping; return the normalised 17-field dict."""
    if type(raw) is not dict or set(raw) != set(OMM_FIELDS):
        raise OrbitError("OMM record must have exactly the 17 OMM fields")
    result = {}
    for field in ("OBJECT_NAME", "OBJECT_ID", "CLASSIFICATION_TYPE"):
        if type(raw[field]) is not str:
            raise OrbitError(field + " must be text")
    if not _NAME.match(raw["OBJECT_NAME"]) or raw["OBJECT_NAME"] != raw["OBJECT_NAME"].strip():
        raise OrbitError("OBJECT_NAME must be 1..64 printable ASCII characters")
    if not _COSPAR.match(raw["OBJECT_ID"]):
        raise OrbitError("OBJECT_ID must be a COSPAR designator YYYY-NNNA")
    if raw["CLASSIFICATION_TYPE"] != "U":
        raise OrbitError("only unclassified (U) element sets are accepted")
    for field in OMM_FIELDS:
        if field in FLOAT_RANGES:
            result[field] = _float(raw[field], field)
        elif field in INT_RANGES:
            result[field] = _int(raw[field], field)
        else:
            result[field] = raw[field]
    result["EPOCH"] = _epoch(raw["EPOCH"]).strftime("%Y-%m-%dT%H:%M:%S.%f")
    return result


def parse_omm(data):
    """Parse a whole JSON or CSV OMM file; every record must validate."""
    if type(data) is not bytes or len(data) > MAX_OMM_BYTES:
        raise OrbitError("OMM input must be bytes within the size limit")
    if data.lstrip(b" \t\r\n")[:1] in (b"[", b"{"):
        value = _json(data)
        if type(value) is not list:
            raise OrbitError("OMM JSON must be an array of records")
        rows, kind = value, "json"
    else:  # CSV: the header row must name exactly the 17 fields, in any order.
        try:
            reader = csv.reader(io.StringIO(data.decode("ascii"), newline=""), strict=True)
            table = [row for row in reader if row]
        except (UnicodeError, csv.Error) as error:
            raise OrbitError("invalid ASCII CSV") from error
        if not table or len(table[0]) != len(OMM_FIELDS) or set(table[0]) != set(OMM_FIELDS):
            raise OrbitError("CSV header must name exactly the 17 OMM fields")
        if any(len(row) != len(OMM_FIELDS) for row in table[1:]):
            raise OrbitError("every CSV row must have 17 columns")
        rows, kind = [dict(zip(table[0], row)) for row in table[1:]], "csv"
    if len(rows) > MAX_RECORDS:
        raise OrbitError("too many OMM records")
    seen, newest = {}, {}
    for raw in rows:
        record = elements(raw)
        norad, epoch = record["NORAD_CAT_ID"], record["EPOCH"]
        if seen.setdefault((norad, epoch), record) != record:
            raise OrbitError("contradictory element sets share one epoch for NORAD %d" % norad)
        if norad not in newest or epoch > newest[norad]["EPOCH"]:  # Normalised text sorts by time.
            newest[norad] = record
    return [newest[key] for key in sorted(newest)], kind


def _norad(value):
    if type(value) is not int:
        raise OrbitError("NORAD id must be an integer, not text or boolean")
    return _int(value, "NORAD_CAT_ID")


def _target(entry):
    if type(entry) is not dict or set(entry) != {"norad_id", "name", "role"}:
        raise OrbitError("allowlist target must have norad_id, name and role only")
    norad = _norad(entry["norad_id"])
    if type(entry["name"]) is not str or not _NAME.match(entry["name"]):
        raise OrbitError("allowlist name must be 1..64 printable ASCII characters")
    if entry["role"] not in ROLES:
        raise OrbitError("allowlist role must be one of " + ", ".join(ROLES))
    return {"norad_id": norad, "name": entry["name"], "role": entry["role"]}


def allowlist(value):
    """Validate an allowlist object; return {norad_id: target}."""
    if (type(value) is not dict or set(value) != {"schema_version", "kind", "targets"}
            or type(value["schema_version"]) is not int or value["schema_version"] != 1
            or value["kind"] != "srrx_orbit_allowlist" or type(value["targets"]) is not list
            or not 0 < len(value["targets"]) <= MAX_TARGETS):
        raise OrbitError("not a srrx_orbit_allowlist v1 with 1..256 targets")
    result = {}
    for entry in value["targets"]:
        target = _target(entry)
        if target["norad_id"] in result:
            raise OrbitError("duplicate NORAD id in the allowlist")
        result[target["norad_id"]] = target
    if sum(target["role"] == "QO100" for target in result.values()) > 1:
        raise OrbitError("at most one QO100 target")
    return result


def load_allowlist(path):
    return allowlist(_json(_read(path, MAX_ALLOWLIST_BYTES)))


def _allowed(allow_norad):
    if isinstance(allow_norad, dict):
        targets = {}
        for key, target in allow_norad.items():
            checked = _target(target)
            if type(key) is not int or key != checked["norad_id"]:
                raise OrbitError("allowlist mapping key differs from its norad_id")
            targets[key] = checked
        return targets
    if not isinstance(allow_norad, (set, frozenset, list, tuple)):
        raise OrbitError("allow_norad must be an allowlist mapping or a collection of NORAD ids")
    return {norad: {"norad_id": norad, "name": "NORAD %d" % norad, "role": "OTHER"}
            for norad in map(_norad, allow_norad)}


def is_stationary(record):
    """|n - 1.00274| < 0.0005 rev/day (STACK.md:187, :572); both edges exclusive."""
    source = record["elements"] if type(record) is dict and "elements" in record else record
    motion = _float(source["MEAN_MOTION"], "MEAN_MOTION")
    return round(abs(motion - GEO_MEAN_MOTION), 12) < GEO_TOLERANCE


def epoch_unix_s(epoch_text):
    return (_epoch(epoch_text) - _UNIX0).total_seconds()


def age(epoch_text, role, now_utc_s, utc_verified):
    """Age fields for one element set at now_utc_s; warnings only, never refusal."""
    limit = AGE_LIMIT_DAYS.get(role, DEFAULT_AGE_LIMIT_DAYS)
    verified = utc_verified is True
    if now_utc_s is None:
        days, reason = None, "AGE_UNKNOWN"
    else:
        if type(now_utc_s) not in (int, float) or not math.isfinite(now_utc_s) or not 0 <= now_utc_s < 4.2e9:
            raise OrbitError("now_utc_s must be finite Unix seconds or None")
        days = (now_utc_s - epoch_unix_s(epoch_text)) / 86400.0
        reason = ("EPOCH_AHEAD_OF_CLOCK" if days < -FUTURE_EPOCH_DAYS else
                  "OLDER_THAN_%g_DAYS" % limit if days > limit else None)
    return {"age_days": days, "age_limit_days": limit, "age_warning": reason is not None,
            "age_warning_reason": reason, "time_verified": verified}


def _record(normal, target, now_utc_s, utc_verified):
    record = {"norad_id": normal["NORAD_CAT_ID"], "name": target["name"], "role": target["role"],
              "elements": normal, "epoch_utc": normal["EPOCH"] + "Z", "epoch_unix_s": epoch_unix_s(normal["EPOCH"])}
    record.update(age(normal["EPOCH"], target["role"], now_utc_s, utc_verified))
    record["stationary"] = is_stationary(normal)
    record["auto_pointing_allowed"] = not record["age_warning"] and record["time_verified"]
    return record


def load_omm(path, *, allow_norad, now_utc_s, utc_verified):
    """Load a local OMM JSON/CSV file; return allowlisted records sorted by NORAD id."""
    targets = _allowed(allow_norad)
    normal, unused = parse_omm(_read(path, MAX_OMM_BYTES))
    return [_record(item, targets[item["NORAD_CAT_ID"]], now_utc_s, utc_verified)
            for item in normal if item["NORAD_CAT_ID"] in targets]


def validate_record(record):
    """Re-check a record produced by load_omm (e.g. passed between modules)."""
    if type(record) is not dict or set(record) != RECORD_FIELDS:
        raise OrbitError("not an srrx.orbits record")
    normal = elements(dict(record["elements"]) if type(record["elements"]) is dict else None)
    target = _target({"norad_id": record["norad_id"], "name": record["name"], "role": record["role"]})
    if normal["NORAD_CAT_ID"] != target["norad_id"] or record["epoch_utc"] != normal["EPOCH"] + "Z":
        raise OrbitError("record identity/epoch does not match its elements")
    days, reason = record["age_days"], record["age_warning_reason"]
    if days is not None and (type(days) not in (int, float) or not math.isfinite(days)):
        raise OrbitError("age_days must be finite or None")
    limit = AGE_LIMIT_DAYS.get(target["role"], DEFAULT_AGE_LIMIT_DAYS)
    reasons = (None, "AGE_UNKNOWN", "EPOCH_AHEAD_OF_CLOCK", "OLDER_THAN_%g_DAYS" % limit)
    if (record["age_limit_days"] != limit or reason not in reasons or (days is None) != (reason == "AGE_UNKNOWN")
            or type(record["age_warning"]) is not bool or record["age_warning"] is not (reason is not None)
            or type(record["time_verified"]) is not bool or record["stationary"] is not is_stationary(normal)
            or record["auto_pointing_allowed"] is not (not record["age_warning"] and record["time_verified"])
            or record["epoch_unix_s"] != epoch_unix_s(normal["EPOCH"])):
        raise OrbitError("record flags are inconsistent")
    return dict(record, elements=normal)


def _cell(value):
    return repr(value) if type(value) is float else str(value)


def satdump_csv(records):
    """Return the export bytes: header plus one row per record, CelesTrak order."""
    if type(records) is not list or len(records) > MAX_EXPORT_RECORDS:
        raise OrbitError("export needs a list of at most 1024 records")
    checked = [validate_record(record) for record in records]
    if len({record["norad_id"] for record in checked}) != len(checked):
        raise OrbitError("export records must have unique NORAD ids")
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(OMM_FIELDS)
    for record in sorted(checked, key=lambda item: item["norad_id"]):
        writer.writerow([_cell(record["elements"][field]) for field in OMM_FIELDS])
    return stream.getvalue().encode("ascii")


def export_satdump_csv(records, path):
    """Atomically replace path with the SatDump OMM CSV; never fetches anything."""
    data = satdump_csv(records)
    path = Path(path)
    if not path.parent.is_dir() or path.is_dir():
        raise OrbitError("export target must be a file in an existing directory")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".srrx-omm-", delete=False) as stream:
            temporary = stream.name
            os.chmod(temporary, 0o644)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        if os.name != "nt":  # Windows has no directory fsync; file data was fsynced above.
            directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)
    return {"path": str(path), "records": len(records), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
