"""artemis-db v74 (SQLite) to the reviewed srrx_artemis_mirror_v1 (stdlib only, no network).

Runs on the home base or the device against a local data.sqlite taken from the
Artemis-DB v74 release archive; it never downloads anything and never writes
next to the source. Everything fails closed: any deviation from the v74 schema
or from the value rules below refuses the whole file with a stable code
(ConvertRefused; never the file's content), and labd then keeps Artemis
UNAVAILABLE with only the masked-band stop (SCOPE-POLICY.md).

Source: a regular file (lstat: no symlink, FIFO or device) of at most
MAX_SOURCE_BYTES with the SQLite header in rollback-journal format (no WAL),
hashed before and after reading (it must not change). Opened as
file:...?mode=ro&immutable=1 with an authorizer that allows only reads, typeof()
and the listed pragmas (no ATTACH, no writes), defensive mode, untrusted schema
and no triggers or views where this Python offers the switches. PRAGMA
integrity_check must be exactly "ok". The table set, each table's columns (name,
declared type, NOT NULL, default, primary key, no hidden or generated column)
and its foreign keys must equal the Peewee v74 model (Artemis-DB
models/model.py at e54d5c3, Peewee 4.1.1 legacy table names); no views or
triggers, indexes only on those tables; one info row NAME 'SigID', VERSION 74.

Values: frequency.VALUE and bandwidth.VALUE are stored integers taken as Hz
(1..1e12 and 0..1e12; text, real or NULL refuses); every child row and category
refers to an existing signal and label; signal names are non-empty text. The
units are confirmed by at least MIN_SPOT_CHECKS operator spot checks NAME=HZ of
known civil entries, each an exact frequency point of exactly one signal.

Ranges per signal are conservative (SigID stores frequency points without range
rows, and two points may be the limits of a band): the envelope
[min(F) - h, max(F) + h] plus each point [f - h, f + h], h = ceil(max(B) / 2),
clamped to 0..1e12; with no bandwidth the envelope only; more than 32 ranges
keeps the envelope only, which covers every point. A signal without frequency
rows cannot match a span; it is counted, not emitted.

Texts: categories from category -> categorylabel.VALUE; description is the
signal description plus the descriptions of its acf, bandwidth and frequency
rows; modulation, mode and location join their VALUE and DESCRIPTION texts.
Texts are cut to the mirror limits; when a cut loses a scope_policy deny term,
the description starts with "[srrx: <term>, ...]", so the stop is unchanged
(scope_policy itself re-checks every entry). Documents and URLs are not copied.

Output: deterministic sorted JSON (sorted keys and entries, UTF-8) within the
ArtemisDB limits, loaded back through scope_policy.ArtemisDB before it is
returned; an acceptance-record template with the locally computed SHA256 whose
evidence_id placeholder is refused until a person replaces it; a report with
counts, spot checks and hashes (no paths). The licence of the SigID-derived
content is unverified: keep the mirror local, never publish or commit it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import tempfile

from . import scope_policy as _sp

MIRROR_FILE = "artemis-mirror.json"
TEMPLATE_FILE = "artemis-acceptance.template.json"
REPORT_FILE = "artemis-conversion-report.json"
MAX_SOURCE_BYTES = 256 * 1024 * 1024
MAX_ROWS = 1_000_000  # per table
MAX_HZ = int(_sp.MAX_ABS_HZ)
MAX_RANGES_PER_ENTRY = 32
MAX_CATEGORIES, MAX_CATEGORY_CHARS = 32, 128
MIN_SPOT_CHECKS = 3
SOURCE_NAME, SOURCE_VERSION = "SigID", 74
UPSTREAM_MODEL = "AresValley/Artemis-DB e54d5c32de6b models/model.py (v74, 2026-07-18; Peewee 4.1.1)"
EVIDENCE_PLACEHOLDER = "REVIEW REQUIRED: replace with admin/artemis-db-v74-mirror-NNN"
LICENCE = "UNVERIFIED: SigID-derived content; keep the mirror local, never publish or commit it"
TEXT_LIMITS = dict(_sp._ENTRY_TEXT)
# Rollback journal only: header bytes 18/19 are 1 (2 would be WAL, whose -wal file immutable=1 ignores).
_LEGACY_JOURNAL = 1
_I, _T, _R = "INTEGER", "TEXT", "REAL"


def _pk(name):
    return (name, _I, 1, None, 1, 0)  # name, declared type, notnull, default, pk, hidden (PRAGMA table_xinfo)


def _column(name, kind):
    return (name, kind, 0, None, 0, 0)


def _child(key, value_type):
    return (_pk(key), _column("DESCRIPTION", _T), _column("SIG_ID", _I), _column("VALUE", value_type))


V74_COLUMNS = {
    "info": (_column("DATE", _T), _column("EDITABLE", _I), _column("NAME", _T), _column("VERSION", _I)),
    "signals": (_pk("SIG_ID"), _column("DESCRIPTION", _T), _column("NAME", _T), _column("URL", _T),
                _column("SINCE_VERSION", _I)),
    "acf": _child("ACF_ID", _R),
    "bandwidth": _child("BAND_ID", _I),
    "categorylabel": (_pk("CLB_ID"), _column("VALUE", _T)),
    "category": (_pk("CAT_ID"), _column("CLB_ID", _I), _column("SIG_ID", _I)),
    "documents": (_pk("DOC_ID"), _column("DESCRIPTION", _T), _column("EXTENSION", _T), _column("NAME", _T),
                  _column("PREVIEW", _I), _column("SIG_ID", _I), _column("TYPE", _T)),
    "frequency": _child("FREQ_ID", _I),
    "location": _child("LOC_ID", _T),
    "mode": _child("MOD_ID", _T),
    "modulation": _child("MDL_ID", _T)}
_TO_SIGNALS = ("signals", "SIG_ID", "SIG_ID", "NO ACTION", "NO ACTION", "NONE")  # PRAGMA foreign_key_list [2:8]
V74_FOREIGN_KEYS = {"info": (), "signals": (), "categorylabel": (),
                    "category": (("categorylabel", "CLB_ID", "CLB_ID", "NO ACTION", "NO ACTION", "NONE"),
                                 _TO_SIGNALS),
                    **{table: (_TO_SIGNALS,) for table in ("acf", "bandwidth", "documents", "frequency",
                                                          "location", "mode", "modulation")}}
_PRAGMAS = frozenset(("integrity_check", "table_xinfo", "foreign_key_list", "trusted_schema", "query_only",
                      "cell_size_check", "mmap_size"))
_FUNCTIONS = frozenset(("typeof",))
_CREATE_TABLE = re.compile(r"\s*CREATE\s+TABLE\s", re.I)
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z", re.ASCII)
_HZ_TEXT = re.compile(r"\d{1,13}\Z", re.ASCII)
_lstat = os.lstat  # module-local alias: tests patch this name, never os.lstat


class ConvertRefused(ValueError):
    """Stable refusal code (a table name or argument index at most); never source content."""


def _refuse(code):
    raise ConvertRefused(code)


# --- source file -------------------------------------------------------------------------
def _snapshot(path):
    """(dev, inode, size, mtime_ns, sha256) and the first 100 bytes of a regular file, streamed."""
    info = _lstat(path)
    if not stat.S_ISREG(info.st_mode):
        _refuse("NOT_REGULAR_FILE")
    if info.st_size > MAX_SOURCE_BYTES:
        _refuse("SOURCE_SIZE_LIMIT")
    descriptor = os.open(path, _sp._READ_FLAGS)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            _refuse("NOT_REGULAR_FILE")
        digest, header, size = hashlib.sha256(), b"", 0
        while True:
            block = os.read(descriptor, 1 << 20)
            if not block:
                break
            size += len(block)
            if size > MAX_SOURCE_BYTES:
                _refuse("SOURCE_SIZE_LIMIT")
            if len(header) < 100:
                header += block[:100 - len(header)]
            digest.update(block)
    finally:
        os.close(descriptor)
    return (opened.st_dev, opened.st_ino, size, opened.st_mtime_ns, digest.hexdigest()), header


def _source(path):
    try:
        return _snapshot(path)
    except ConvertRefused:
        raise
    except (OSError, TypeError, ValueError):
        _refuse("SOURCE_UNAVAILABLE")


def _check_header(header):
    if len(header) < 100 or header[:16] != _sp.SQLITE_MAGIC:
        _refuse("NOT_SQLITE")
    if header[18] != _LEGACY_JOURNAL or header[19] != _LEGACY_JOURNAL:
        _refuse("SQLITE_JOURNAL_MODE")


# --- read-only connection ----------------------------------------------------------------
def _authorize(action, first, second, database, source):
    """Reads, typeof() and the listed pragmas only; everything else (ATTACH, writes) is denied."""
    if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ):
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_PRAGMA and isinstance(first, str) and first.lower() in _PRAGMAS:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and isinstance(second, str) and second.lower() in _FUNCTIONS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _connect(path):
    uri = Path(os.path.abspath(path)).as_uri() + "?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True, isolation_level=None)
    try:
        if hasattr(connection, "setlimit"):  # Python 3.11+
            connection.setlimit(sqlite3.SQLITE_LIMIT_ATTACHED, 0)
            connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 1 << 24)
        if hasattr(connection, "setconfig"):  # Python 3.12+; older SQLite may lack a switch
            for name, value in (("SQLITE_DBCONFIG_DEFENSIVE", True), ("SQLITE_DBCONFIG_TRUSTED_SCHEMA", False),
                                ("SQLITE_DBCONFIG_ENABLE_TRIGGER", False), ("SQLITE_DBCONFIG_ENABLE_VIEW", False)):
                if hasattr(sqlite3, name):
                    connection.setconfig(getattr(sqlite3, name), value)
        connection.set_authorizer(_authorize)
        for pragma in ("trusted_schema=OFF", "query_only=ON", "cell_size_check=ON", "mmap_size=0"):
            connection.execute("PRAGMA " + pragma)
    except BaseException:
        connection.close()
        raise
    return connection


def _rows(connection, sql):
    rows = connection.execute(sql).fetchmany(MAX_ROWS + 1)
    if len(rows) > MAX_ROWS:
        _refuse("ROW_LIMIT")
    return rows


def _check_schema(connection):
    tables, indexed = set(), set()
    for kind, name, table, sql in connection.execute('SELECT "type", "name", "tbl_name", "sql" FROM "sqlite_master"'):
        if kind == "table":
            if not isinstance(sql, str) or not _CREATE_TABLE.match(sql):
                _refuse("SCHEMA_TABLE_KIND")  # virtual tables and the like
            tables.add(name)
        elif kind == "index":
            indexed.add(table)
        else:
            _refuse("SCHEMA_OBJECTS")  # views and triggers
    if tables != set(V74_COLUMNS):
        _refuse("SCHEMA_TABLES")
    if not indexed <= tables:
        _refuse("SCHEMA_OBJECTS")
    for table, expected in V74_COLUMNS.items():
        columns = connection.execute('PRAGMA table_xinfo("%s")' % table).fetchall()
        actual = [(name, (kind or "").upper(), notnull, default, pk, hidden)
                  for _, name, kind, notnull, default, pk, hidden in columns]
        if len(actual) != len(expected) or set(actual) != set(expected):
            _refuse("SCHEMA_COLUMNS:" + table)
        keys = [tuple(row[2:8]) for row in connection.execute('PRAGMA foreign_key_list("%s")' % table)]
        if len(keys) != len(V74_FOREIGN_KEYS[table]) or set(keys) != set(V74_FOREIGN_KEYS[table]):
            _refuse("SCHEMA_FOREIGN_KEYS:" + table)


def _text(kind, value, code):
    """Stored text, or "" for NULL; any other storage class refuses."""
    if kind == "null":
        return ""
    if kind != "text":
        _refuse(code)
    return value


def _owner(signals, kind, sig_id, table):
    if kind != "integer" or sig_id not in signals:
        _refuse("ORPHAN_ROW:" + table)
    return signals[sig_id]


def _contents(connection):
    info = _rows(connection, 'SELECT typeof("NAME"), "NAME", typeof("VERSION"), "VERSION", typeof("DATE"), "DATE" '
                             'FROM "info"')
    if len(info) != 1:
        _refuse("INFO_ROWS")
    name_kind, name, version_kind, version, date_kind, date = info[0]
    if name_kind != "text" or name != SOURCE_NAME:
        _refuse("INFO_NAME")
    if version_kind != "integer" or version != SOURCE_VERSION:
        _refuse("INFO_VERSION")
    date = date if date_kind == "text" and _DATE.match(date) else None
    signals = {}
    for sig_id, name_kind, name, text_kind, text in _rows(
            connection, 'SELECT "SIG_ID", typeof("NAME"), "NAME", typeof("DESCRIPTION"), "DESCRIPTION" '
                        'FROM "signals" ORDER BY "SIG_ID"'):
        if name_kind != "text" or not name.strip():
            _refuse("SIGNAL_NAME")
        signals[sig_id] = {"name": name, "description": _text(text_kind, text, "TEXT_TYPE:signals"),
                           "points": set(), "widths": [], "categories": set(), "notes": set(),
                           "modulation": set(), "mode": set(), "location": set()}
    labels = {}
    for clb_id, kind, value in _rows(connection, 'SELECT "CLB_ID", typeof("VALUE"), "VALUE" FROM "categorylabel"'):
        if kind != "text" or len(value) > MAX_CATEGORY_CHARS:
            _refuse("CATEGORY_LABEL")
        labels[clb_id] = value
    for sig_kind, sig_id, clb_kind, clb_id in _rows(
            connection, 'SELECT typeof("SIG_ID"), "SIG_ID", typeof("CLB_ID"), "CLB_ID" FROM "category"'):
        signal = _owner(signals, sig_kind, sig_id, "category")
        if clb_kind != "integer" or clb_id not in labels:
            _refuse("CATEGORY_REFERENCE")
        signal["categories"].add(labels[clb_id])
    counts = {}
    for table in ("frequency", "bandwidth", "acf", "modulation", "mode", "location"):
        rows = _rows(connection, 'SELECT typeof("SIG_ID"), "SIG_ID", typeof("VALUE"), "VALUE", typeof("DESCRIPTION"), '
                                 '"DESCRIPTION" FROM "%s"' % table)
        counts[table + "_rows"] = len(rows)
        for sig_kind, sig_id, value_kind, value, text_kind, text in rows:
            signal = _owner(signals, sig_kind, sig_id, table)
            note = _text(text_kind, text, "TEXT_TYPE:" + table)
            if table in ("modulation", "mode", "location"):
                value = _text(value_kind, value, "TEXT_TYPE:" + table)
                signal[table].update(part for part in (value, note) if part)
                continue
            if table == "acf":
                if value_kind not in ("integer", "real", "null"):
                    _refuse("ACF_VALUE")
            elif value_kind != "integer" or not (1 if table == "frequency" else 0) <= value <= MAX_HZ:
                _refuse(table.upper() + "_VALUE")  # Hz integers only: text, real or NULL may hide other units
            elif table == "frequency":
                signal["points"].add(value)
            else:
                signal["widths"].append(value)
            if note:
                signal["notes"].add(note)
    return date, signals, counts


def _read_database(path):
    try:
        connection = _connect(path)
    except sqlite3.Error:
        _refuse("SQLITE_UNREADABLE")
    try:
        if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            _refuse("SQLITE_INTEGRITY")
        _check_schema(connection)
        return _contents(connection)
    except sqlite3.Error:
        _refuse("SQLITE_UNREADABLE")  # malformed pages, undecodable text, denied statements
    finally:
        connection.close()


# --- mirror ------------------------------------------------------------------------------
def ranges_hz(points, widths):
    """Envelope plus each point +/- ceil(max(B)/2), clamped to 0..1e12; envelope only without bandwidth."""
    points = sorted(set(points))
    if not points:
        _refuse("NO_FREQUENCY")
    half = (max(widths) + 1) // 2 if widths else 0

    def clamp(value):
        return min(MAX_HZ, max(0, value))
    envelope = (clamp(points[0] - half), clamp(points[-1] + half))
    if half == 0:
        return [list(envelope)]
    ranges = sorted({envelope} | {(clamp(point - half), clamp(point + half)) for point in points})
    if len(ranges) > MAX_RANGES_PER_ENTRY:
        return [list(envelope)]  # the envelope already covers every point
    return [list(item) for item in ranges]


def _deny_terms(texts):
    folded = set()
    for text in texts:
        folded |= _sp._folds(text)
    return {term for term, key in zip(_sp.DENY_TERMS, _sp._DENY_FOLDED) if any(key in item for item in folded)}


def _entry(signal, counts):
    categories = sorted(signal["categories"])
    if len(categories) > MAX_CATEGORIES:
        _refuse("CATEGORY_LIMIT")
    description = ([signal["description"]] if signal["description"] else []) + sorted(signal["notes"])
    full = {"name": signal["name"], "description": "\n".join(description),
            "modulation": "; ".join(sorted(signal["modulation"])), "mode": "; ".join(sorted(signal["mode"])),
            "location": "; ".join(sorted(signal["location"]))}
    entry = {"categories": categories, "ranges_hz": ranges_hz(signal["points"], signal["widths"])}
    counts["envelope_only"] += (max(signal["widths"], default=0) > 0 and len(signal["points"]) > 1 and
                                len(entry["ranges_hz"]) == 1)  # more than 32 ranges collapsed
    for key, text in full.items():
        if text:
            entry[key] = text[:TEXT_LIMITS[key]]
            counts["truncated_fields"] += len(text) > TEXT_LIMITS[key]
    lost = _deny_terms(full.values()) - _deny_terms(entry.get(key, "") for key in full)
    if lost:  # a cut dropped a deny term: say so first, so scope_policy still stops on this entry
        marker = "[srrx: " + ", ".join(sorted(lost)) + "] "
        entry["description"] = marker + entry.get("description", "")[:TEXT_LIMITS["description"] - len(marker)]
        counts["deny_markers"] += 1
    try:
        checked, _ = _sp._entry(entry)
    except _sp.ScopeRefused:
        _refuse("MIRROR_ENTRY_SCHEMA")
    if _deny_terms(full.values()) and "DENY_REGEX" not in checked.reasons:
        _refuse("DENY_TERM_LOST")
    return entry


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _expectations(expect):
    """Spot checks as (name, hz): "NAME=HZ" text or a (name, hz) pair; at least MIN_SPOT_CHECKS names."""
    if isinstance(expect, (str, bytes)) or not isinstance(expect, (list, tuple)):
        _refuse("SPOT_CHECKS_REQUIRED")
    checks = []
    for index, item in enumerate(expect):
        if isinstance(item, str):
            name, separator, hz = item.rpartition("=")
            if not separator or not _HZ_TEXT.match(hz):
                _refuse("SPOT_CHECK_FORMAT:%d" % index)
            hz = int(hz)
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            name, hz = item
        else:
            _refuse("SPOT_CHECK_FORMAT:%d" % index)
        if not isinstance(name, str) or not name.strip() or type(hz) is not int or not 1 <= hz <= MAX_HZ:
            _refuse("SPOT_CHECK_FORMAT:%d" % index)
        checks.append((name, hz))
    if len({name for name, _ in checks}) < MIN_SPOT_CHECKS:
        _refuse("SPOT_CHECKS_REQUIRED")
    return checks


def convert(sqlite_path, *, expect):
    """Validate a v74 data.sqlite and return the mirror bytes, acceptance template and report."""
    checks = _expectations(expect)
    before, header = _source(sqlite_path)
    _check_header(header)
    date, signals, counts = _read_database(sqlite_path)
    if _source(sqlite_path)[0] != before:
        _refuse("SOURCE_CHANGED")
    by_name = {}
    for signal in signals.values():
        by_name.setdefault(signal["name"], []).append(signal)
    for index, (name, hz) in enumerate(checks):
        if len(by_name.get(name, ())) != 1:
            _refuse("SPOT_CHECK_NAME:%d" % index)
        if hz not in by_name[name][0]["points"]:
            _refuse("SPOT_CHECK_FREQUENCY:%d" % index)  # e.g. kHz or MHz stored instead of Hz
    counts.update(signals=len(signals), truncated_fields=0, deny_markers=0, envelope_only=0,
                  signals_without_frequency=sum(not signal["points"] for signal in signals.values()))
    entries = [_entry(signal, counts) for signal in signals.values() if signal["points"]]
    counts.update(entries=len(entries), ranges=sum(len(entry["ranges_hz"]) for entry in entries))
    if len(entries) > _sp.ArtemisDB.MAX_ENTRIES:
        _refuse("ENTRY_LIMIT")
    if counts["ranges"] > _sp.ArtemisDB.MAX_RANGES:
        _refuse("RANGE_LIMIT")
    entries.sort(key=lambda entry: (entry["name"], _canonical(entry)))
    document = {"v": 1, "kind": "srrx_artemis_mirror", "source": "artemis-db", "db_version": "v74", "entries": entries}
    data = (_canonical(document) + "\n").encode("utf-8")
    if len(data) > _sp.ArtemisDB.MAX_BYTES:
        _refuse("MIRROR_SIZE_LIMIT")
    digest = hashlib.sha256(data).hexdigest()
    with tempfile.TemporaryDirectory(prefix="srrx-artemis-") as folder:  # the same loader labd uses
        probe = Path(folder) / MIRROR_FILE
        probe.write_bytes(data)
        loaded = _sp.ArtemisDB.load(probe, digest)
    if not loaded.available or len(loaded) != len(entries):
        _refuse("MIRROR_ROUND_TRIP")
    template = {"v": 1, "kind": "srrx_artemis_acceptance", "db": "artemis-db", "db_version": "v74",
                "format": _sp.ARTEMIS_FORMAT, "sha256": digest, "evidence_id": EVIDENCE_PLACEHOLDER}
    report = {"v": 1, "kind": "srrx_artemis_conversion_report", "tool": "srrx.artemis_convert",
              "upstream_model": UPSTREAM_MODEL, "accepted": False, "licence": LICENCE,
              "source": {"sha256": before[4], "bytes": before[2], "info_name": SOURCE_NAME,
                         "info_version": SOURCE_VERSION, "info_date": date},
              "integrity_check": "ok", "units": "Hz (stored integers), confirmed by the spot checks",
              "spot_checks": [{"name": name, "hz": hz, "result": "PASS"} for name, hz in checks],
              "counts": dict(sorted(counts.items())),
              "mirror": {"file": MIRROR_FILE, "sha256": digest, "bytes": len(data)}}
    return {"mirror": data, "sha256": digest, "template": template, "report": report}


def _document(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _write_new(path, data):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags, 0o644)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(descriptor, view):]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_outputs(result, output_dir):
    """Create the mirror, template and report in an existing directory; never replaces a file."""
    folder = Path(output_dir)
    if not folder.is_dir():
        _refuse("OUTPUT_DIRECTORY")
    outputs = ((folder / MIRROR_FILE, result["mirror"]), (folder / TEMPLATE_FILE, _document(result["template"])),
               (folder / REPORT_FILE, _document(result["report"])))
    if any(os.path.lexists(path) for path, _ in outputs):
        _refuse("OUTPUT_EXISTS")
    written = []
    try:
        for path, data in outputs:
            _write_new(path, data)
            written.append(path)
    except OSError:
        for path in written:  # only this run's own partial outputs
            path.unlink(missing_ok=True)
        _refuse("OUTPUT_WRITE")
    return [str(path) for path, _ in outputs]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m srrx.artemis_convert",
                                     description="artemis-db v74 data.sqlite -> srrx_artemis_mirror_v1 (offline)")
    parser.add_argument("--sqlite", type=Path, required=True, help="data.sqlite from the Artemis-DB v74 archive")
    parser.add_argument("--output-dir", type=Path, required=True, help="existing directory; files are never replaced")
    parser.add_argument("--expect", action="append", default=[], metavar="NAME=HZ",
                        help="spot check: exact signal name and one of its frequencies in Hz (at least 3)")
    args = parser.parse_args(argv)
    try:
        result = convert(args.sqlite, expect=args.expect)
        write_outputs(result, args.output_dir)
    except ConvertRefused as error:
        print("srrx.artemis_convert: refused: " + str(error), file=sys.stderr)
        return 2
    counts = result["report"]["counts"]
    print(json.dumps({"mirror_sha256": result["sha256"], "entries": counts["entries"], "ranges": counts["ranges"],
                      "spot_checks": len(result["report"]["spot_checks"]), "accepted": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
