"""Strict, local, unit-bound hardware acceptance records.

Missing/OPEN records are blocked. This validates record completeness, artifact
integrity and revision binding; it cannot prove that a person performed a test.
Neither a CRC nor SHA256 is a signature or a substitute for bench acceptance.
There is deliberately no environment-variable or command-line bypass here.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import zlib

PROJECT_REVISION = "SR-RX-v2.1"
GRAPH_PATHS = tuple(f"design/E{i}.json" for i in range(1, 6)) + ("design/readiness-contract.json",)
GATE_IDS = tuple([f"E1-{i:02}" for i in range(1, 8)]
                 + [f"E2-{i:02}" for i in range(1, 6)]
                 + [f"E3-{i:02}" for i in range(1, 9)]
                 + [f"E4-{i:02}" for i in (1, 3, 4, 5, 6, 7, 8)]
                 + [f"E5-{i:02}" for i in range(1, 10)])
CAL_FIELDS = ("v", "revision", "serial", "scale_mv_per_count", "offset_mv",
              "panel_offset_c", "case_offset_c", "reference_id")
PLACEHOLDERS = {"tbd", "todo", "unknown", "none", "n/a", "na", "placeholder",
                "example", "test", "sim", "simulation", "open", "pending",
                "replace_me", "changeme", "0000"}
BRANCH_CAPS = {"LNA1": (.265, 5.5), "LNA2": (.265, 5.5), "LNA3": (.265, 5.5),
               "LNA4": (.144, 5.5), "LNB": (.405, 14), "BONI": (.113, 15),
               "SB_LNA": (.065, 5.5), "RTLA": (.544, 5.5), "RTLB": (.4, 5.5),
               "HFP": (.825, 5.5), "LIME3V3": (1.8, 3.63), "T7": (1.512, 5.5),
               "LABPORT": (.678, 5.5), "AUX12": (.75, 13)}
RUNTIME_SOURCES = {"LNA1": "INA3221:0x41:1", "LNA2": "INA3221:0x41:2",
                   "LNA3": "INA3221:0x41:3", "LNA4": "INA3221:0x43:1",
                   "LNB": "INA3221:0x43:2", "BONI": "INA3221:0x43:3"}


class ValidationError(ValueError):
    """Hardware remains BLOCKED if this exception is raised."""


def _keys(obj, fields, label):
    if type(obj) is not dict or set(obj) != set(fields):
        raise ValidationError(label + " has missing or unknown fields")


def _text(value, label, minimum=1):
    if (type(value) is not str or len(value.strip()) < minimum or len(value) > 4000
            or value.strip().lower() in PLACEHOLDERS
            or re.search(r"\b(?:tbd|todo|placeholder|replace_me|changeme)\b", value, re.I)
            or "<" in value or ">" in value):
        raise ValidationError(label + " is empty or a placeholder")
    return value.strip()


def _number(value, low, high, label):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValidationError(label + " is not a finite in-range number")
    return value


def _date(value, label):
    _text(value, label)
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("timezone missing")
        result = result.astimezone(timezone.utc)
        if not datetime(2026, 1, 1, tzinfo=timezone.utc) <= result <= datetime.now(timezone.utc):
            raise ValueError("date outside current project lifetime or in future")
        return result
    except (ValueError, TypeError) as exc:
        raise ValidationError(label + " requires a real, non-future ISO8601 date with timezone") from exc


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _local_file(root, relative):
    if type(relative) is not str or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValidationError("artifact path must stay inside project")
    try:
        path = (root / relative).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file() or not 0 < path.stat().st_size <= 64 * 1024 * 1024:
            raise ValueError("invalid file")
        return path
    except (OSError, ValueError, RuntimeError) as exc:
        raise ValidationError("missing, empty, oversized or external artifact: " + relative) from exc


def _artifact(record, root):
    _keys(record, ("path", "sha256"), "artifact")
    if type(record["sha256"]) is not str or not re.fullmatch("[0-9a-f]{64}", record["sha256"]):
        raise ValidationError("artifact SHA256 must be lowercase hex")
    path = _local_file(root, record["path"])
    if _digest(path) != record["sha256"]:
        raise ValidationError("artifact SHA256 mismatch: " + record["path"])
    return path


def _evidence(record, root, accepted):
    _keys(record, ("date", "instrument", "notes", "artifacts"), "evidence")
    if _date(record["date"], "evidence date") > accepted:
        raise ValidationError("evidence postdates acceptance")
    _text(record["instrument"], "instrument identification", 3)
    _text(record["notes"], "measurement and acceptance notes", 16)
    artifacts = record["artifacts"]
    if type(artifacts) is not list or not 1 <= len(artifacts) <= 32:
        raise ValidationError("evidence requires at least one measured-log artifact")
    for artifact in artifacts:
        _artifact(artifact, root)


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValidationError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _read_json(path):
    try:
        if not 0 < path.stat().st_size <= 2 * 1024 * 1024:
            raise ValueError("size")
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValidationError("nonfinite JSON value")))
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        raise ValidationError("cannot read valid acceptance JSON: " + str(path)) from exc


def project_hashes(project_root):
    """Exact file maps; edits to any bound graph or executable source revoke it."""
    root = Path(project_root).resolve(strict=True)
    graphs = {name: _digest(_local_file(root, name)) for name in GRAPH_PATHS}
    sources = sorted(set(root.glob("software/srrx/**/*.py")) | set(root.glob("firmware/**/*.py"))
                     | set(root.glob("software/systemd/*.service")) | set(root.glob("software/pyproject.toml")))
    if not any(p.is_relative_to(root / "software/srrx") for p in sources):
        raise ValidationError("software sources missing")
    source_hashes = {p.relative_to(root).as_posix(): _digest(_local_file(root, p.relative_to(root).as_posix()))
                     for p in sources}
    contract = _read_json(_local_file(root, "design/readiness-contract.json"))
    if type(contract.get("gate_results")) is not dict or set(contract["gate_results"]) != set(GATE_IDS):
        raise ValidationError("readiness contract does not contain the exact 36 blocking gates")
    return graphs, source_hashes


def _calibration(record, serial):
    _keys(record, CAL_FIELDS + ("crc32",), "battery ADC calibration record")
    if (type(record["v"]) is not int or record["v"] != 1
            or record["revision"] != "E3-v2.1" or record["serial"] != serial):
        raise ValidationError("ADC version/revision/Pico serial mismatch")
    _number(record["scale_mv_per_count"], 0.22, 0.34, "ADC scale")
    _number(record["offset_mv"], -1000, 1000, "ADC offset")
    for key in ("panel_offset_c", "case_offset_c"):
        _number(record[key], -10, 10, key)
    _text(record["reference_id"], "ADC reference instrument/log ID", 3)
    values = []
    for key in CAL_FIELDS:
        value = record[key]
        if type(value) is float:
            value = "%.9f" % value
        elif type(value) is int:
            value = str(value)
        if type(value) is not str or "\n" in value or "\r" in value:
            raise ValidationError("invalid calibration canonical value")
        values.append(key + "=" + value)
    canonical = ("\n".join(values) + "\n").encode()
    if record["crc32"] != "%08x" % (zlib.crc32(canonical) & 0xFFFFFFFF):
        raise ValidationError("ADC coefficient CRC mismatch")


def load_acceptance(path, project_root):
    """Return a complete matching manifest or raise ValidationError (BLOCKED).

    The hardware caller must also check the live Pico serial and calibration CRC
    against this record before arming. Merely loading this file does not identify
    attached hardware or prove that deployed firmware matches recorded artifacts.
    """
    try:
        root = Path(project_root).resolve(strict=True)
        if path is None:
            raise ValidationError("acceptance file missing; hardware BLOCKED")
        data = _read_json(Path(path))
        _keys(data, ("schema_version", "project_revision", "hardware_unit_id", "pico_serial",
                     "accepted_at", "graph_sha256", "source_sha256", "gates", "battery_adc", "firmware", "branch_limits", "lab5_budget"), "acceptance")
        if type(data["schema_version"]) is not int or data["schema_version"] != 1 or data["project_revision"] != PROJECT_REVISION:
            raise ValidationError("acceptance schema/project revision mismatch")
        unit = _text(data["hardware_unit_id"], "physical hardware unit ID", 4)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{3,79}", unit):
            raise ValidationError("invalid hardware unit ID")
        if type(data["pico_serial"]) is not str or not re.fullmatch(r"[0-9a-f]{8,64}", data["pico_serial"]) or set(data["pico_serial"]) == {"0"}:
            raise ValidationError("actual Pico unique_id hex required")
        accepted = _date(data["accepted_at"], "acceptance timestamp")
        graphs, sources = project_hashes(root)
        if data["graph_sha256"] != graphs or data["source_sha256"] != sources:
            raise ValidationError("graph/software/firmware revision SHA256 mismatch")
        _keys(data["gates"], GATE_IDS, "36 blocking gates")
        for gate_id, gate in data["gates"].items():
            _keys(gate, ("status", "evidence"), gate_id)
            if gate["status"] != "PASS":
                raise ValidationError(gate_id + " is not PASS; hardware BLOCKED")
            _evidence(gate["evidence"], root, accepted)
        adc = data["battery_adc"]
        _keys(adc, ("status", "record", "points", "evidence"), "battery ADC")
        if adc["status"] != "PASS":
            raise ValidationError("ADC calibration is not accepted")
        _calibration(adc["record"], data["pico_serial"])
        _evidence(adc["evidence"], root, accepted)
        if type(adc["points"]) is not list or len(adc["points"]) != 2:
            raise ValidationError("two measured ADC calibration points required")
        for point in adc["points"]:
            _keys(point, ("raw_count", "reference_v"), "ADC point")
            if type(point["raw_count"]) is not int or not 16 < point["raw_count"] < 65519:
                raise ValidationError("ADC point must contain actual read_u16 count")
            _number(point["reference_v"], 10, 17, "ADC point reference volts")
            predicted = (point["raw_count"] * adc["record"]["scale_mv_per_count"] + adc["record"]["offset_mv"]) / 1000
            if abs(predicted - point["reference_v"]) > 0.025:
                raise ValidationError("ADC coefficients do not fit measured points")
        low, high = adc["points"]
        if high["reference_v"] - low["reference_v"] < 2 or high["raw_count"] <= low["raw_count"]:
            raise ValidationError("ADC measured points must span at least 2 V")
        _keys(data["firmware"], ("pico", "imu"), "firmware")
        for role, fw in data["firmware"].items():
            _keys(fw, ("status", "artifact", "evidence"), "firmware " + role)
            if fw["status"] != "PASS":
                raise ValidationError(role + " firmware is not commissioned")
            artifact = _artifact(fw["artifact"], root)
            if not artifact.is_relative_to(root / "firmware" / role) or artifact.suffix not in {".py", ".uf2", ".bin", ".elf"}:
                raise ValidationError(role + " firmware artifact location/type mismatch")
            _evidence(fw["evidence"], root, accepted)
        _keys(data["branch_limits"], BRANCH_CAPS, "branch limits")
        for branch, limit in data["branch_limits"].items():
            _keys(limit, ("baseline_a", "max_current_a", "min_voltage_v", "max_voltage_v",
                          "calibration", "evidence"), "branch " + branch)
            cap, vcap = BRANCH_CAPS[branch]
            baseline = _number(limit["baseline_a"], 0.000001, cap, branch + " baseline")
            maximum = _number(limit["max_current_a"], baseline, cap, branch + " current limit")
            vmin = _number(limit["min_voltage_v"], 0.001, vcap, branch + " voltage minimum")
            vmax = _number(limit["max_voltage_v"], vmin, vcap, branch + " voltage maximum")
            if vmax <= vmin or (branch.startswith("LNA") and maximum > baseline * 1.2 + 1e-12):
                raise ValidationError(branch + " voltage/current window is not allowed")
            if branch == "BONI" and not .030 <= baseline <= maximum < .113:
                raise ValidationError("BONI current window must remain 30mA..below113mA")
            cal = limit["calibration"]
            _keys(cal, ("status", "unit_id", "source", "units", "current_gain", "current_offset_a",
                        "voltage_gain", "voltage_offset_v"), "branch calibration")
            if (cal["status"] != "PASS" or cal["unit_id"] != unit or cal["units"] != "SI"
                    or cal["source"] != RUNTIME_SOURCES.get(branch, "bench_only_no_runtime_sensor")):
                raise ValidationError(branch + " calibration acceptance/unit/source mismatch")
            _number(cal["current_gain"], .8, 1.2, "current calibration gain")
            _number(cal["current_offset_a"], -.02, .02, "current calibration offset")
            _number(cal["voltage_gain"], .8, 1.2, "voltage calibration gain")
            _number(cal["voltage_offset_v"], -.2, .2, "voltage calibration offset")
            _evidence(limit["evidence"], root, accepted)
        budget = data["lab5_budget"]
        _keys(budget, ("always_on_a", "max_lab5_a", "evidence"), "LAB5 power budget")
        always = _number(budget["always_on_a"], .1, 2.5, "measured concurrent LAB5 fixed loads")
        maximum = _number(budget["max_lab5_a"], .1, 3.2, "accepted LAB5 operating ceiling")
        if always + .052 >= maximum:
            raise ValidationError("LAB5 fixed loads plus 52mA overhead exceed ceiling")
        _evidence(budget["evidence"], root, accepted)
        return data
    except ValidationError:
        raise
    except (OSError, TypeError, ValueError, KeyError, AttributeError, OverflowError) as exc:
        raise ValidationError("malformed acceptance; hardware BLOCKED") from exc


def acceptance_template(project_root):
    """Create an unaccepted template, never a synthetic PASS or nominal ADC fit."""
    graphs, sources = project_hashes(project_root)
    evidence = lambda: {"date": "", "instrument": "", "notes": "", "artifacts": []}
    return {"schema_version": 1, "project_revision": PROJECT_REVISION,
            "hardware_unit_id": "", "pico_serial": "", "accepted_at": "",
            "graph_sha256": graphs, "source_sha256": sources,
            "lab5_budget": {"always_on_a": None, "max_lab5_a": None, "evidence": evidence()},
            "gates": {gate: {"status": "OPEN", "evidence": evidence()} for gate in GATE_IDS},
            "battery_adc": {"status": "OPEN", "record": {}, "points": [], "evidence": evidence()},
            "firmware": {role: {"status": "OPEN", "artifact": {"path": "", "sha256": ""},
                                "evidence": evidence()} for role in ("pico", "imu")},
            "branch_limits": {branch: {"baseline_a": None, "max_current_a": None,
                "min_voltage_v": None, "max_voltage_v": None,
                "calibration": {"status": "OPEN", "unit_id": "", "source": RUNTIME_SOURCES.get(branch, "bench_only_no_runtime_sensor"),
                    "units": "SI", "current_gain": None, "current_offset_a": None,
                    "voltage_gain": None, "voltage_offset_v": None}, "evidence": evidence()}
                for branch in BRANCH_CAPS}}
