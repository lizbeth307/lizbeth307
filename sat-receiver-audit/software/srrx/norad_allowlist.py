"""NORAD orbit allowlist builder and checker (stdlib only, no network).

The srrx.orbits allowlist is built on the home base from local copies of
CelesTrak SATCAT and GP/OMM files the operator downloaded (STACK.md:884); this
module never fetches anything and no NORAD id is written in code. The request
is a targets file that names each satellite by its exact SATCAT OBJECT_NAME and
LAUNCH_DATE with an srrx.orbits role (software/config/orbit-targets.json holds
the STACK targets): {"v": 1, "kind": "srrx_orbit_targets", "targets":
[{"satcat_name": str, "launch_date": "YYYY-MM-DD", "role": ROLE, "name": str?}]}.

Each target must match exactly one SATCAT row by name and launch date: a payload
(OBJECT_TYPE PAY) without DECAY_DATE and not status D, with a COSPAR OBJECT_ID
and NORAD 1..999999. Its NORAD id needs a GP element set (srrx.orbits.parse_omm
rules, the newest epoch over all GP files) whose OBJECT_ID equals the SATCAT
one. Everything fails closed for the whole build (AllowlistRefused with a stable
code and at most the target index). resolve() stops after SATCAT and lists the
GP query for each id, for the operator to fetch; nothing is fetched here.

Output: deterministic allowlist bytes (sorted keys, targets by NORAD id) that
srrx.orbits.allowlist accepts; an acceptance-record template with the locally
computed SHA256 whose evidence_id placeholder is refused until a person has
reviewed the report; a report with the matched SATCAT/GP fields and input
SHA256s (no paths). On the device both files live in /etc/srrx; the record is
root-owned like the other admin records, and load_accepted() reads the
allowlist once, checks its SHA256 and returns the srrx.orbits mapping.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import re
import sys

from . import orbits
from . import scope_policy as _sp

SATCAT_FIELDS = ("OBJECT_NAME", "OBJECT_ID", "NORAD_CAT_ID", "OBJECT_TYPE", "OPS_STATUS_CODE", "OWNER",
                 "LAUNCH_DATE", "LAUNCH_SITE", "DECAY_DATE", "PERIOD", "INCLINATION", "APOGEE", "PERIGEE", "RCS",
                 "DATA_STATUS_CODE", "ORBIT_CENTER", "ORBIT_TYPE")
ALLOWLIST_FILE = "orbit-allowlist.json"
TEMPLATE_FILE = "orbit-allowlist.acceptance.template.json"
REPORT_FILE = "orbit-allowlist.report.json"
ACCEPTANCE_KIND, ALLOWLIST_FORMAT = "srrx_orbit_allowlist_acceptance", "srrx_orbit_allowlist"
EVIDENCE_PLACEHOLDER = "REVIEW REQUIRED: replace with admin/orbit-allowlist-NNN"
GP_QUERY = "https://celestrak.org/NORAD/elements/gp.php?CATNR=%d&FORMAT=json"  # text for the operator only
MAX_SATCAT_BYTES, MAX_SATCAT_ROWS, MAX_FILES = 64 * 1024 * 1024, 500_000, 16
MAX_TARGETS_BYTES = 64 * 1024
_TARGET_FIELDS = frozenset(("satcat_name", "launch_date", "role"))
_ACCEPT_FIELDS = frozenset(("v", "kind", "format", "sha256", "evidence_id"))
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z", re.ASCII)


class AllowlistRefused(ValueError):
    """Stable refusal code with at most a target or file index."""


def _refuse(code):
    raise AllowlistRefused(code)


def _name(value):
    return isinstance(value, str) and orbits._NAME.match(value) is not None and value == value.strip()


def _date(value):
    if not isinstance(value, str) or not _DATE.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def targets(value):
    """Validate a srrx_orbit_targets request; return its targets with the display name filled in."""
    if (type(value) is not dict or set(value) != {"v", "kind", "targets"} or type(value["v"]) is not int
            or value["v"] != 1 or value["kind"] != "srrx_orbit_targets" or type(value["targets"]) is not list
            or not 0 < len(value["targets"]) <= orbits.MAX_TARGETS):
        _refuse("TARGETS_SCHEMA")
    result, seen = [], set()
    for index, entry in enumerate(value["targets"]):
        if type(entry) is not dict or not _TARGET_FIELDS <= set(entry) <= _TARGET_FIELDS | {"name"}:
            _refuse("TARGET_SCHEMA:%d" % index)  # a norad_id key is never accepted: ids come from SATCAT
        name = entry.get("name", entry["satcat_name"])
        if (not _name(entry["satcat_name"]) or not _date(entry["launch_date"]) or entry["role"] not in orbits.ROLES
                or not _name(name)):
            _refuse("TARGET_SCHEMA:%d" % index)
        key = (entry["satcat_name"], entry["launch_date"])
        if key in seen:
            _refuse("TARGET_DUPLICATE:%d" % index)
        seen.add(key)
        result.append({"satcat_name": key[0], "launch_date": key[1], "role": entry["role"], "name": name})
    if sum(target["role"] == "QO100" for target in result) > 1:
        _refuse("TARGETS_QO100")
    return result


def _cell(value):
    if value is None:
        return ""
    if type(value) in (str, int, float):
        return value
    _refuse("SATCAT_SCHEMA")


def parse_satcat(data):
    """SATCAT rows (CelesTrak CSV with the 17-field header in any order, or a JSON array)."""
    if type(data) is not bytes or len(data) > MAX_SATCAT_BYTES:
        _refuse("SATCAT_SIZE_LIMIT")
    if data.lstrip(b" \t\r\n")[:1] == b"[":
        try:
            rows = orbits._json(data)
        except orbits.OrbitError:
            _refuse("SATCAT_SCHEMA")
        if type(rows) is not list or any(type(row) is not dict or set(row) != set(SATCAT_FIELDS) for row in rows):
            _refuse("SATCAT_SCHEMA")
        rows = [{field: _cell(row[field]) for field in SATCAT_FIELDS} for row in rows]
    else:
        try:
            text = data.decode("utf-8-sig")  # a spreadsheet re-save may add a BOM
            table = [row for row in csv.reader(io.StringIO(text, newline=""), strict=True) if row]
        except (UnicodeError, csv.Error):
            _refuse("SATCAT_SCHEMA")
        if not table or len(table[0]) != len(SATCAT_FIELDS) or set(table[0]) != set(SATCAT_FIELDS):
            _refuse("SATCAT_SCHEMA")
        if any(len(row) != len(SATCAT_FIELDS) for row in table[1:]):
            _refuse("SATCAT_SCHEMA")
        rows = [dict(zip(table[0], row)) for row in table[1:]]
    if len(rows) > MAX_SATCAT_ROWS:
        _refuse("SATCAT_ROW_LIMIT")
    return rows


def _satcat_match(rows, target, index):
    """The one SATCAT payload for a target; every matching copy must agree and pass, or it refuses."""
    copies = set()
    for row in rows:
        if row["OBJECT_NAME"] != target["satcat_name"] or row["LAUNCH_DATE"] != target["launch_date"]:
            continue
        try:
            norad = orbits._int(row["NORAD_CAT_ID"], "NORAD_CAT_ID")  # CSV digits or a JSON integer
        except orbits.OrbitError:
            _refuse("SATCAT_ROW:%d" % index)
        status = row["OPS_STATUS_CODE"]
        if (not isinstance(row["OBJECT_ID"], str) or not orbits._COSPAR.match(row["OBJECT_ID"])
                or not isinstance(status, str) or len(status) > 1):
            _refuse("SATCAT_ROW:%d" % index)
        if row["OBJECT_TYPE"] != "PAY":
            _refuse("SATCAT_NOT_PAYLOAD:%d" % index)
        if row["DECAY_DATE"] != "" or status == "D":
            _refuse("SATCAT_DECAYED:%d" % index)
        copies.add((norad, row["OBJECT_ID"], status))
    if not copies:
        _refuse("SATCAT_NO_MATCH:%d" % index)
    if len(copies) != 1:
        _refuse("SATCAT_AMBIGUOUS:%d" % index)  # copies of one row (overlapping downloads) count once
    norad, object_id, status = copies.pop()
    return {"norad_id": norad, "object_id": object_id, "ops_status_code": status}


def _sources(kind, blobs, limit):
    if type(blobs) not in (list, tuple) or not 0 < len(blobs) <= MAX_FILES:
        _refuse(kind.upper() + "_FILES")
    for index, blob in enumerate(blobs):
        if type(blob) is not bytes or len(blob) > limit:
            _refuse("%s_SIZE_LIMIT:%d" % (kind.upper(), index))
    return [{"kind": kind, "sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)} for blob in blobs]


def resolve(targets_value, satcat_blobs):
    """Match every target in SATCAT; return the matches and the GP query text for each id."""
    request = targets(targets_value)
    sources = _sources("satcat", satcat_blobs, MAX_SATCAT_BYTES)
    rows = [row for blob in satcat_blobs for row in parse_satcat(blob)]
    if len(rows) > MAX_SATCAT_ROWS:
        _refuse("SATCAT_ROW_LIMIT")
    matches = []
    for index, target in enumerate(request):
        match = dict(target, **_satcat_match(rows, target, index))
        match["gp_query"] = GP_QUERY % match["norad_id"]
        matches.append(match)
    if len({match["norad_id"] for match in matches}) != len(matches):
        _refuse("TARGETS_SAME_NORAD")
    return matches, sources


def _gp(gp_blobs):
    newest = {}
    for index, blob in enumerate(gp_blobs):
        try:
            records, _ = orbits.parse_omm(blob)
        except orbits.OrbitError:
            _refuse("GP_SCHEMA:%d" % index)
        for record in records:
            norad, previous = record["NORAD_CAT_ID"], newest.get(record["NORAD_CAT_ID"])
            if previous is not None and (previous["OBJECT_ID"] != record["OBJECT_ID"] or
                                         (previous["EPOCH"] == record["EPOCH"] and previous != record)):
                _refuse("GP_CONTRADICTION")
            if previous is None or record["EPOCH"] > previous["EPOCH"]:  # normalised text sorts by time
                newest[norad] = record
    return newest


def _canonical(value):
    return (json.dumps(value, sort_keys=True, indent=1) + "\n").encode("ascii")


def build(targets_value, satcat_blobs, gp_blobs):
    """Return the allowlist bytes, its SHA256, the acceptance template and the report."""
    matches, sources = resolve(targets_value, satcat_blobs)
    sources += _sources("gp", gp_blobs, orbits.MAX_OMM_BYTES)
    elements = _gp(gp_blobs)
    for index, match in enumerate(matches):
        record = elements.get(match["norad_id"])
        if record is None:
            _refuse("GP_MISSING:%d" % index)
        if record["OBJECT_ID"] != match["object_id"]:
            _refuse("GP_OBJECT_ID_MISMATCH:%d" % index)
        match.update(gp_object_name=record["OBJECT_NAME"], gp_epoch_utc=record["EPOCH"] + "Z")
        del match["gp_query"]
    document = {"schema_version": 1, "kind": ALLOWLIST_FORMAT,
                "targets": [{"norad_id": match["norad_id"], "name": match["name"], "role": match["role"]}
                            for match in sorted(matches, key=lambda item: item["norad_id"])]}
    data = _canonical(document)
    if len(data) > orbits.MAX_ALLOWLIST_BYTES:
        _refuse("ALLOWLIST_SIZE_LIMIT")
    try:
        orbits.allowlist(orbits._json(data))  # the same check labd and srrx.passes apply
    except orbits.OrbitError:
        _refuse("ALLOWLIST_SCHEMA")
    digest = hashlib.sha256(data).hexdigest()
    template = {"v": 1, "kind": ACCEPTANCE_KIND, "format": ALLOWLIST_FORMAT, "sha256": digest,
                "evidence_id": EVIDENCE_PLACEHOLDER}
    report = {"v": 1, "kind": "srrx_orbit_allowlist_report", "tool": "srrx.norad_allowlist", "accepted": False,
              "allowlist": {"file": ALLOWLIST_FILE, "sha256": digest, "bytes": len(data)},
              "sources": sources, "targets": matches,
              "review": "Check each NORAD id, COSPAR id and role against CelesTrak SATCAT before filling evidence_id"}
    return {"allowlist": data, "sha256": digest, "template": template, "report": report}


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
    """Create the allowlist, template and report in an existing directory; never replaces a file."""
    folder = Path(output_dir)
    if not folder.is_dir():
        _refuse("OUTPUT_DIRECTORY")
    outputs = ((folder / ALLOWLIST_FILE, result["allowlist"]), (folder / TEMPLATE_FILE, _canonical(result["template"])),
               (folder / REPORT_FILE, _canonical(result["report"])))
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


def load_acceptance(record_path):
    """Root-owned record binding the allowlist SHA256 (same owner/directory rules as decoder_policy)."""
    try:
        record = _sp._admin_record(record_path)
    except _sp.ScopeRefused as error:
        _refuse("ACCEPTANCE_SCHEMA" if str(error) == "RECORD_SCHEMA" else "ACCEPTANCE_RECORD_REQUIRED")
    if (type(record) is not dict or set(record) != _ACCEPT_FIELDS or type(record["v"]) is not int
            or record["v"] != 1 or record["kind"] != ACCEPTANCE_KIND or record["format"] != ALLOWLIST_FORMAT
            or not isinstance(record["sha256"], str) or not _sp._HEX.fullmatch(record["sha256"])
            or not isinstance(record["evidence_id"], str) or not _sp._EVIDENCE.fullmatch(record["evidence_id"])):
        _refuse("ACCEPTANCE_SCHEMA")
    return record


def load_accepted(allowlist_path, record_path):
    """{norad_id: target} from an allowlist whose exact bytes the acceptance record names."""
    record = load_acceptance(record_path)
    try:
        data = _sp._read_regular(allowlist_path, _sp._lstat(allowlist_path), orbits.MAX_ALLOWLIST_BYTES)
    except _sp.ScopeRefused:
        _refuse("ALLOWLIST_NOT_REGULAR_FILE")
    except (OSError, TypeError, ValueError):
        _refuse("ALLOWLIST_UNAVAILABLE")
    if len(data) > orbits.MAX_ALLOWLIST_BYTES:
        _refuse("ALLOWLIST_SIZE_LIMIT")
    if not hmac.compare_digest(hashlib.sha256(data).hexdigest(), record["sha256"]):
        _refuse("ALLOWLIST_SHA256_MISMATCH")
    try:
        return orbits.allowlist(orbits._json(data))
    except orbits.OrbitError:
        _refuse("ALLOWLIST_SCHEMA")


def _read(path, limit):
    try:
        with open(path, "rb") as stream:
            data = stream.read(limit + 1)
    except OSError:
        _refuse("INPUT_UNAVAILABLE")
    if len(data) > limit:
        _refuse("INPUT_SIZE_LIMIT")
    return data


def _targets_file(path):
    try:
        return orbits._json(_read(path, MAX_TARGETS_BYTES))
    except orbits.OrbitError:
        _refuse("TARGETS_SCHEMA")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m srrx.norad_allowlist",
                                     description="NORAD orbit allowlist from local CelesTrak SATCAT/GP copies (offline)")
    commands = parser.add_subparsers(dest="command", required=True)
    step = commands.add_parser("resolve", help="match the targets in SATCAT and print the GP query per NORAD id")
    full = commands.add_parser("build", help="write the allowlist, its acceptance template and the report")
    for command in (step, full):
        command.add_argument("--targets", type=Path, required=True)
        command.add_argument("--satcat", type=Path, action="append", required=True)
    full.add_argument("--gp", type=Path, action="append", required=True)
    full.add_argument("--output-dir", type=Path, required=True)
    check = commands.add_parser("check", help="verify an installed allowlist against its root-owned record")
    check.add_argument("--allowlist", type=Path, required=True)
    check.add_argument("--record", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            accepted = load_accepted(args.allowlist, args.record)
            roles = {}
            for target in accepted.values():
                roles[target["role"]] = roles.get(target["role"], 0) + 1
            summary = {"accepted": True, "targets": len(accepted), "roles": roles}
        else:
            request = _targets_file(args.targets)
            satcat = [_read(path, MAX_SATCAT_BYTES) for path in args.satcat[:MAX_FILES + 1]]
            if args.command == "resolve":
                matches, _ = resolve(request, satcat)
                summary = {"targets": [{key: match[key] for key in ("name", "norad_id", "object_id", "gp_query")}
                                       for match in matches]}
            else:
                result = build(request, satcat, [_read(path, orbits.MAX_OMM_BYTES)
                                                 for path in args.gp[:MAX_FILES + 1]])
                write_outputs(result, args.output_dir)
                summary = {"allowlist_sha256": result["sha256"], "targets": len(result["report"]["targets"]),
                           "accepted": False}
    except AllowlistRefused as error:
        print("srrx.norad_allowlist: refused: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
