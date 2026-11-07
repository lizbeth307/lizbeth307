"""Gpredict bridge: labd's OMM elements, stored location and the SDR++ radio as Gpredict files.

Standard library only, no network, no receiver access. The Gpredict +lab package (2.7+lab1,
deployment/recipes/gpredict) loads element sets only from the files written here:

- Gpredict 2.7 reads the catalogue number from TLE line columns 3-7 with atoi
  (src/sgpsdp/sgp_in.c:157-160) and names each element file <number>.sat (src/compat.c:333-339),
  so it handles five decimal digits only: no Alpha-5 and no six-digit NORAD id. CelesTrak's
  five-digit numbers ran out on 11.07.2026 (STACK.md:141); newer objects exist only as OMM. Every
  NORAD id above 99999 therefore gets a deterministic five-digit alias, kept in
  /var/lib/srrx/gpredict/aliases.json, and the displayed name carries the real id. All of
  1..99999 is assigned somewhere, so an alias always equals some real object's number; that does
  not matter because Gpredict sees only this satdata directory (the package drops the bundled
  satellites.dat and *.cat, and first-time check step 5, src/first-time.c:610-640, copies them only
  into a directory without .sat or .cat files; lab patch 0002 stops the network TLE update and
  lab patch 0004 the TLE import from local files, the only other writers of satdata/<number>.sat).
  Inside one set an alias never equals a real id of the set or another alias.
- satdata/<number>.sat holds the TLE built from labd's OMM records (srrx.orbits): the two lines
  sgp4 2.27's exporter writes for the same elements (software/tests/test_gpredict_bridge.py checks
  both equality and that Gpredict's Good_Elements rules, src/sgpsdp/sgp_in.c:122-147, accept them).
  satdata/srrx.cat lists them; every other .sat/.cat file in satdata is removed.
- srrx.qth is the stored, rounded location only (srrx.pass_jobs.stored_location: 0.1 deg, 100 m
  HAE, never a live fix); without a usable one nothing is written.
- hwconf/SDRPP-RX.rig is the one radio: Type 0 (RX only, src/radio-conf.h RIG_TYPE_RX) at the SDR++
  rigctl_server, 127.0.0.1:4532 (it resolves its host to an IPv4 socket), with no AOS/LOS and no
  IQ record signals (#371). modules/SR-RX.mod tracks the set from srrx.qth.
- gpredict.cfg is merged, not replaced: [TLE] AUTO_UPDATE_FREQ=0 (never, src/tle-update.h:40) and
  empty TLE/transponder server lists; the user's other settings stay.

CLI: python3 -m srrx.gpredict_bridge write --omm /var/lib/srrx/orbits/gp.json
--allowlist /etc/srrx/orbit-allowlist.json --location <status.json> --config-dir
~/.config/Gpredict [--aliases /var/lib/srrx/gpredict/aliases.json]. The Expert GUI runs as the
touch-session account srrx-ui, whose home /var/lib/srrx-ui gets no copy of /etc/skel
(deployment/system/system_files.py SESSION_HOME), so its config dir is
/var/lib/srrx-ui/.config/Gpredict; who runs this before Gpredict starts stays OPEN. CI model only:
no GUI and no receiver run here; the Doppler loop with SDR++ stays a device row.
"""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

from . import orbits, pass_jobs

ALIASES_PATH = Path("/var/lib/srrx/gpredict/aliases.json")
ALIAS_KIND = "srrx_gpredict_aliases"
MAX_CATALOG = 99999  # five TLE digits (Gpredict 2.7 reads no Alpha-5)
MAX_SATELLITES = orbits.MAX_TARGETS
MAX_ALIAS_BYTES = 64 * 1024
MAX_CONFIG_BYTES = 256 * 1024
MAX_LOCATION_BYTES = 16 * 1024
CATEGORY_FILE, CATEGORY_NAME = "srrx.cat", "SR-RX (labd OMM)"
MODULE_NAME, QTH_FILE, RADIO_NAME = "SR-RX", "srrx.qth", "SDRPP-RX"
# SDR++ rigctl_server of the sdrpp +lab package (8c9f5ee8 main.cpp:39-44): localhost:4532,
# which it resolves to IPv4 (core/src/utils/net.cpp:65-77), so the radio names 127.0.0.1.
RIGCTL_HOST, RIGCTL_PORT = "127.0.0.1", 4532
RADIO_CONFIG = ("[Radio]\nHost=%s\nPort=%d\nCycle=1000\nType=0\nPTT=0\n"
                "SIGNAL_AOS=false\nSIGNAL_LOS=false\nSIGNAL_AOIQ=false\nSIGNAL_LOIQ=false\n") % (RIGCTL_HOST, RIGCTL_PORT)
# (group, key, value) the bridge enforces in gpredict.cfg; VERSION 1.4 skips the pre-1.4 TLE
# URL migration (src/sat-cfg.c:300-345), whose input would be the empty server below.
CONFIG_SETTINGS = (("VERSION", "MAJOR", "1"), ("VERSION", "MINOR", "4"), ("GLOBAL", "DEFAULT_QTH", QTH_FILE),
                   ("TLE", "AUTO_UPDATE_FREQ", "0"), ("TLE", "AUTO_UPDATE_ACTION", "1"), ("TLE", "SERVER", ""),
                   ("TLE", "URLS", ""), ("TRSP", "SERVER", ""))
# Set only where the file has no value yet (the user may open other modules too).
CONFIG_DEFAULTS = (("GLOBAL", "OPEN_MODULES", MODULE_NAME),)
_EPOCH0 = datetime(1949, 12, 31)  # sgp4.omm's day count origin
_XPDOTP = 1440.0 / (2.0 * math.pi)
_GROUP = re.compile(r"\[([^\[\]]+)\]\Z")
_KEY = re.compile(r"([A-Za-z0-9_\-]+)\s*=(.*)\Z", re.S)


class BridgeError(ValueError):
    pass


# --- TLE lines from validated OMM elements ----------------------------------------------------

def checksum(line):
    """TLE check digit: digits count as their value, '-' as 1, everything else 0 (mod 10)."""
    return sum(int(c) if c.isdigit() else 1 if c == "-" else 0 for c in line[:68]) % 10


def _rate(value, zero_exponent):
    # sgp4.exporter._abbreviate_rate: ' 12345-5 ' style, sign or space first, implied leading decimal.
    return ("{0: 4.4e} ".format(value).replace(".", "").replace("e+00", zero_exponent)
            .replace("e-0", "-").replace("e+0", "+"))


def _epoch_field(epoch_text):
    """YYDDD.DDDDDDDD the way sgp4 2.27 forms it from an OMM EPOCH (omm.initialize, then the
    epochyr/epochdays of Satrec.sgp4init): float days since 1949-12-31; the day fraction is rounded
    to 8 decimals only when the whole count has no digits beyond them; day of year plus fraction."""
    moment = datetime.strptime(epoch_text, "%Y-%m-%dT%H:%M:%S.%f")
    epoch = (moment - _EPOCH0).total_seconds() / 86400.0
    whole, fraction = divmod(epoch, 1.0)
    if round(epoch * 1e8) == epoch * 1e8:
        fraction = round(fraction * 1e8) / 1e8
    day = _EPOCH0 + timedelta(days=int(whole))
    day_of_year = (day - datetime(day.year - 1, 12, 31)).days
    return "%02d" % (day.year % 100) + "{:012.8f}".format(day_of_year + fraction)


def tle_lines(elements, catalog):
    """(line 1, line 2) for one normalised OMM record (srrx.orbits.elements) under the given
    five-digit catalogue number: the columns, unit conversions and rounding of sgp4 2.27
    (omm.initialize stores the elements in radians and SGP4 units, exporter.export_tle converts
    them back), so the text equals the exporter's for the same elements."""
    normal = orbits.elements(dict(elements)) if type(elements) is dict else orbits.elements(None)
    if type(catalog) is not int or not 1 <= catalog <= MAX_CATALOG:
        raise BridgeError("catalogue number must be 1..99999")
    number = "%05d" % catalog
    designator = normal["OBJECT_ID"][2:].replace("-", "")
    if len(designator) > 8:
        raise BridgeError("international designator does not fit 8 columns")
    # Stored values (sgp4.omm.initialize) ...
    ndot = normal["MEAN_MOTION_DOT"] / (1036800.0 / math.pi)
    nddot = normal["MEAN_MOTION_DDOT"] / (2985984000.0 / 2.0 / math.pi)
    no_kozai = normal["MEAN_MOTION"] / 720.0 * math.pi
    angle = {f: normal[f] * (math.pi / 180.0) for f in ("INCLINATION", "RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY")}
    # ... and their export (sgp4.exporter.export_tle).
    degrees = {f: "{0:8.4f}".format(value / (math.pi / 180.0)).rjust(8) for f, value in angle.items()}
    line1 = ("1 " + number + normal["CLASSIFICATION_TYPE"] + " " + "{0:8} ".format(designator)
             + _epoch_field(normal["EPOCH"]) + " " + "{0: 8.8f}".format(ndot * (_XPDOTP * 1440.0)).replace("0", "", 1) + " "
             + _rate(nddot * _XPDOTP * 20736000.0, "-0") + _rate(normal["BSTAR"] * 10.0, "+0")
             + "{0} {1:4}".format(normal["EPHEMERIS_TYPE"], normal["ELEMENT_SET_NO"]))
    line2 = ("2 " + number + " " + degrees["INCLINATION"] + " " + degrees["RA_OF_ASC_NODE"] + " "
             + "{0:8.7f}".format(normal["ECCENTRICITY"]).replace("0.", "") + " " + degrees["ARG_OF_PERICENTER"] + " "
             + degrees["MEAN_ANOMALY"] + " " + "{0:11.8f}".format(no_kozai * _XPDOTP).rjust(8)
             + str(normal["REV_AT_EPOCH"] % 100000).rjust(5))  # the TLE keeps five digits of the revolution count
    line1, line2 = line1 + str(checksum(line1)), line2 + str(checksum(line2))
    if len(line1) != 69 or len(line2) != 69:
        raise BridgeError("element set does not fit the 69-column TLE format")
    return line1, line2


# --- five-digit aliases -----------------------------------------------------------------------

def _candidate(norad_id, attempt):
    digest = hashlib.sha256(b"srrx-gpredict-alias/%d/%d" % (norad_id, attempt)).digest()
    return 1 + int.from_bytes(digest[:8], "big") % MAX_CATALOG


def assign_aliases(norad_ids, previous=None):
    """{norad_id: catalogue number} for one set. Ids up to 99999 keep their own number. A larger
    id keeps its stored alias while that number is still free in the set (stable across runs);
    otherwise, and for a new id, it takes the first free number of its own SHA-256 sequence, ids
    in ascending order (deterministic: the same set and store always give the same map)."""
    ids = sorted(set(norad_ids))
    if len(ids) > MAX_SATELLITES or not all(type(n) is int and 1 <= n <= orbits.INT_RANGES["NORAD_CAT_ID"][1] for n in ids):
        raise BridgeError("NORAD ids must be 1..999999, at most %d" % MAX_SATELLITES)
    previous = previous or {}
    result = {n: n for n in ids if n <= MAX_CATALOG}
    taken = set(result)
    large = [n for n in ids if n > MAX_CATALOG]
    for norad_id in large:
        alias = previous.get(norad_id)
        if alias is not None and alias not in taken:
            result[norad_id] = alias
            taken.add(alias)
    for norad_id in large:
        attempt = 0
        while norad_id not in result:
            alias = _candidate(norad_id, attempt)
            if alias not in taken:
                result[norad_id] = alias
                taken.add(alias)
            attempt += 1
    return {n: result[n] for n in ids}


def alias_document(mapping):
    """The aliases.json document: only the ids above 99999, sorted."""
    return {"schema_version": 1, "kind": ALIAS_KIND,
            "aliases": [{"norad_id": n, "catalog": c} for n, c in sorted(mapping.items()) if n > MAX_CATALOG]}


def parse_aliases(value):
    """{norad_id: catalogue number} of a valid aliases document; anything else fails closed."""
    if (type(value) is not dict or set(value) != {"schema_version", "kind", "aliases"} or value["schema_version"] != 1
            or type(value["schema_version"]) is not int or value["kind"] != ALIAS_KIND or type(value["aliases"]) is not list
            or len(value["aliases"]) > MAX_SATELLITES):
        raise BridgeError("not a srrx_gpredict_aliases v1 document")
    mapping = {}
    for entry in value["aliases"]:
        if (type(entry) is not dict or set(entry) != {"norad_id", "catalog"} or type(entry["norad_id"]) is not int
                or type(entry["catalog"]) is not int or not MAX_CATALOG < entry["norad_id"] <= orbits.INT_RANGES["NORAD_CAT_ID"][1]
                or not 1 <= entry["catalog"] <= MAX_CATALOG or entry["norad_id"] in mapping):
            raise BridgeError("alias entries need a unique NORAD id above 99999 and a catalogue number 1..99999")
        mapping[entry["norad_id"]] = entry["catalog"]
    if len(set(mapping.values())) != len(mapping):
        raise BridgeError("two NORAD ids share one alias")
    return mapping


def load_aliases(path):
    """The stored map, or {} when the file does not exist yet."""
    try:
        with open(path, "rb") as stream:
            data = stream.read(MAX_ALIAS_BYTES + 1)
    except FileNotFoundError:
        return {}
    if len(data) > MAX_ALIAS_BYTES:
        raise BridgeError("aliases file exceeds the size limit")
    return parse_aliases(orbits._json(data))


# --- Gpredict file texts ----------------------------------------------------------------------

def _value(text):
    """A GKeyFile value: printable ASCII on one line, backslash escaped, no edge spaces."""
    if type(text) is not str or not re.fullmatch(r"[\x20-\x7e]*", text) or text != text.strip():
        raise BridgeError("Gpredict values are single-line printable ASCII without edge spaces")
    return text.replace("\\", "\\\\")


def display_names(record, catalog):
    """(NAME, NICKNAME): an alias shows the real NORAD id in both."""
    if catalog == record["norad_id"]:
        return record["name"], record["name"]
    return ("%s (NORAD %d, alias %05d)" % (record["name"], record["norad_id"], catalog),
            "%s #%d" % (record["name"], record["norad_id"]))


def sat_text(record, catalog):
    """satdata/<catalog>.sat for one srrx.orbits record (the [Satellite] layout of
    src/tle-update.c:432-440 and src/first-time.c:488-501)."""
    line1, line2 = tle_lines(record["elements"], catalog)
    name, nickname = display_names(record, catalog)
    return ("[Satellite]\nVERSION=1.1\nNAME=%s\nNICKNAME=%s\nTLE1=%s\nTLE2=%s\n"
            % (_value(name), _value(nickname), line1, line2))


def category_text(catalogs):
    return CATEGORY_NAME + "\n" + "".join("%d\n" % c for c in sorted(catalogs))


def module_text(catalogs):
    return "[GLOBAL]\nSATELLITES=%s\nQTHFILE=%s\n" % ("".join("%d;" % c for c in sorted(catalogs)), QTH_FILE)


def qth_text(location):
    """srrx.qth from srrx.pass_jobs.stored_location output (0.1 deg, 100 m HAE or none)."""
    if (type(location) is not dict or location.get("available") is not True or location.get("live_fix") is not False
            or not all(type(location.get(k)) is float and math.isfinite(location[k]) for k in ("lat", "lon"))
            or round(location["lat"], 1) != location["lat"] or round(location["lon"], 1) != location["lon"]):
        raise BridgeError("the QTH needs a stored location rounded to 0.1 deg")
    alt = location.get("alt_hae_m")
    if alt is None:
        altitude, basis = 0, "altitude unknown, 0 m assumed"
    elif type(alt) is float and math.isfinite(alt) and round(alt, -2) == alt and -1000 <= alt <= 20000:
        altitude, basis = int(alt), "HAE rounded to 100 m"
    else:
        raise BridgeError("the stored altitude must be HAE rounded to 100 m or none")
    return ("[QTH]\nDESCRIPTION=SR-RX stored location (rounded to 0.1 deg; %s)\nLOCATION=SR-RX\n"
            "LAT=%.1f\nLON=%.1f\nALT=%d\nQTH_TYPE=0\n") % (basis, location["lat"], location["lon"], altitude)


def merge_config(text):
    """gpredict.cfg with CONFIG_SETTINGS enforced: each key replaced where it stands, missing keys
    appended to their group, missing groups appended; CONFIG_DEFAULTS only where missing; comments
    and other settings kept. A line that is no group, key, comment or blank fails closed (no guess
    at a GKeyFile Gpredict rejects)."""
    if type(text) is not str or len(text.encode("utf-8")) > MAX_CONFIG_BYTES:
        raise BridgeError("gpredict.cfg must be text within the size limit")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    group, groups, last_line = None, {}, {}
    for index, raw in enumerate(lines):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _GROUP.match(line)
        if match:
            group = match.group(1)
            groups.setdefault(group, index)
            last_line[group] = index
            continue
        if group is None or not _KEY.match(line):
            raise BridgeError("gpredict.cfg line %d is no group, key or comment" % (index + 1))
        last_line[group] = index
    wanted = {}
    for name, key, value in CONFIG_SETTINGS + CONFIG_DEFAULTS:
        wanted.setdefault(name, []).append((key, value))
    enforced = {(name, key) for name, key, unused in CONFIG_SETTINGS}
    group, seen = None, set()
    for index, raw in enumerate(lines):
        line = raw.strip()
        match = _GROUP.match(line) if line and not line.startswith("#") else None
        if match:
            group = match.group(1)
            continue
        key_match = _KEY.match(line) if line and not line.startswith("#") else None
        if key_match and group in wanted:
            for key, value in wanted[group]:
                if key_match.group(1) == key:
                    if (group, key) in enforced:
                        lines[index] = key + "=" + value
                    seen.add((group, key))
    inserts = {}
    for name, key, value in CONFIG_SETTINGS + CONFIG_DEFAULTS:
        if (name, key) not in seen and name in groups:
            inserts.setdefault(last_line[name], []).append(key + "=" + value)
    out = []
    for index, line in enumerate(lines):
        out.append(line)
        out.extend(inserts.get(index, []))
    for name in wanted:
        if name not in groups:
            if out and out[-1] != "":
                out.append("")
            out.append("[" + name + "]")
            out.extend(key + "=" + value for key, value in wanted[name])
    return "\n".join(out) + "\n"


# --- writing ----------------------------------------------------------------------------------

def _atomic_write(path, data, mode=0o644):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".srrx-gpredict-", delete=False) as stream:
            temporary = stream.name
            os.chmod(temporary, mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def _directory(path):
    path = Path(path)
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise BridgeError("not a plain directory: " + str(path))
    path.mkdir(mode=0o755, parents=True, exist_ok=True)
    return path


def plan(records, location, previous_aliases=None):
    """Every file text of one bridge run, keyed by its path below the Gpredict config directory,
    the alias map and the records left out (an element set the 69-column TLE cannot carry, e.g. a
    second derivative below 1e-10: listed with its NORAD id, never silently). Pure: nothing is
    read or written here."""
    if type(records) is not list or not 0 < len(records) <= MAX_SATELLITES:
        raise BridgeError("the bridge needs 1..%d srrx.orbits records" % MAX_SATELLITES)
    checked = [orbits.validate_record(record) for record in records]
    if len({record["norad_id"] for record in checked}) != len(checked):
        raise BridgeError("records must have unique NORAD ids")
    usable, skipped = [], []
    for record in checked:
        try:
            sat_text(record, 1)  # the TLE columns and the GKeyFile values both fit
            usable.append(record)
        except BridgeError as error:
            skipped.append({"norad_id": record["norad_id"], "reason": str(error)})
    if not usable:
        raise BridgeError("no record fits the TLE format")
    mapping = assign_aliases([record["norad_id"] for record in usable], previous_aliases)
    files = {"satdata/%d.sat" % mapping[record["norad_id"]]: sat_text(record, mapping[record["norad_id"]]) for record in usable}
    catalogs = sorted(mapping.values())
    files["satdata/" + CATEGORY_FILE] = category_text(catalogs)
    files["modules/" + MODULE_NAME + ".mod"] = module_text(catalogs)
    files[QTH_FILE] = qth_text(location)
    files["hwconf/" + RADIO_NAME + ".rig"] = RADIO_CONFIG
    return files, mapping, skipped


def write(config_dir, records, location, aliases_path=ALIASES_PATH):
    """Write one bridge run into config_dir (~/.config/Gpredict) and the alias store. satdata keeps
    only this run's .sat files and srrx.cat. Returns a summary without coordinates."""
    config = _directory(config_dir)
    previous = load_aliases(aliases_path)
    files, mapping, skipped = plan(records, location, previous)
    for sub in ("satdata", "satdata/cache", "modules", "hwconf", "trsp"):
        _directory(config / sub)
    cfg_path = config / "gpredict.cfg"
    if cfg_path.is_symlink():
        raise BridgeError("gpredict.cfg is a symbolic link")
    try:
        with open(cfg_path, "rb") as stream:
            raw = stream.read(MAX_CONFIG_BYTES + 1)
        existing = raw.decode("utf-8")
    except FileNotFoundError:
        existing = ""
    except UnicodeError as error:
        raise BridgeError("gpredict.cfg is not UTF-8") from error
    files["gpredict.cfg"] = merge_config(existing)
    _directory(Path(aliases_path).parent)
    _atomic_write(aliases_path, (json.dumps(alias_document(mapping), indent=2) + "\n").encode("ascii"))
    for relative, text in sorted(files.items()):
        _atomic_write(config / relative, text.encode("ascii"))
    keep = {Path(relative).name for relative in files if relative.startswith("satdata/")}
    removed = []
    for entry in sorted((config / "satdata").iterdir()):
        if entry.suffix in (".sat", ".cat") and entry.name not in keep and (entry.is_file() or entry.is_symlink()):
            entry.unlink()
            removed.append(entry.name)
    return {"status": "GPREDICT_FILES_WRITTEN", "satellites": len(mapping), "aliased": sum(n != c for n, c in mapping.items()),
            "aliases": {str(n): c for n, c in sorted(mapping.items()) if n != c}, "skipped": skipped, "removed": removed,
            "radio": "%s:%d RX only" % (RIGCTL_HOST, RIGCTL_PORT), "hardware_ready": False}


def _read_json(path, limit):
    try:
        return orbits._json(orbits._read(path, limit))
    except OSError as error:
        raise BridgeError("cannot read " + str(path)) from error


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write Gpredict files from labd's OMM, allowlist and stored location.")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("write", help="satdata, category, module, QTH, RX-only radio and gpredict.cfg")
    run.add_argument("--omm", type=Path, default=pass_jobs.OMM_PATH)
    run.add_argument("--allowlist", type=Path, default=pass_jobs.ALLOWLIST_PATH)
    run.add_argument("--location", type=Path, required=True, help="srrx.location status JSON (stored and rounded before use)")
    run.add_argument("--config-dir", type=Path, required=True, help="the Gpredict user directory, e.g. ~/.config/Gpredict")
    run.add_argument("--aliases", type=Path, default=ALIASES_PATH)
    args = parser.parse_args(argv)
    try:
        targets = orbits.load_allowlist(args.allowlist)
        records = orbits.load_omm(args.omm, allow_norad=targets, now_utc_s=None, utc_verified=False)
        location = pass_jobs.stored_location(_read_json(args.location, MAX_LOCATION_BYTES))
        if location is None:
            raise BridgeError("LOCATION_UNUSABLE: no stored location for the QTH")
        result = write(args.config_dir, records, location, args.aliases)
    except (BridgeError, orbits.OrbitError, OSError) as error:
        print(json.dumps({"status": "BLOCKED", "error": str(error)[:200], "hardware_ready": False}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
