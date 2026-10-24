"""Reference LEO pass prediction: Skyfield EarthSatellite.from_omm + find_events.

Skyfield 1.55 / sgp4 2.27 (the version pins of build/07:517 and STACK.md:900) live
in a venv of their own, never in labd: /opt/srrx/passes-venv with numpy 2.3.5 and a
hashed lock (software/DEPLOYMENT.md), not the numpy<2 lab-venv of build/07. They are
imported lazily on the first prediction and a missing install raises
PassDependencyError. labd stays stdlib-only and runs the CLI below only through the
sandboxed oneshot srrx-passes@.service (srrx.pass_jobs). There is no project-owned SGP4.

No downloads: the timescale is Skyfield's built-in table (builtin=True) and no
ephemeris file is opened; elements come only from srrx.orbits records. sgp4 2.27
accepts NORAD ids up to 339999 (Alpha-5); larger 6-digit ids are reported in
"skipped" (SATNUM_BEYOND_SGP4_ALPHA5), never guessed.

Privacy: the observer is rounded to 0.1 deg (build/07:503 export rule) BEFORE
prediction, so a saved plan holds only the rounded position and nothing finer can
be recovered from its times or azimuths (pass times move < 1 s). Each plan carries
time_verified (false unless the caller's UTC is verified) and the observer's
source/age/qualification. Coordinates read from a file (location snapshot,
manual entry, last_good record, saved plan) are never a live GNSS fix: a gpsd,
nmea or unknown label becomes last_good and the fix is not qualified, both in
predict(observer_from_file=True) and in every plan validate_plan returns or
write_plan stores. Only complete rise-culminate-set passes inside the
window are listed; passes cut by the window edge are counted, not invented.
Agreement with Gpredict within 1 s is POL-11 (BUILDER), not evidenced here.

labd jobs (srrx.pass_jobs): srrx-passes@.service runs this CLI with --request (start,
window, UTC state and the stored, already rounded location labd wrote for one job),
--group-readable (0640 in the setgid labd plan directory) and --keep (bounded
retention). baseband_windows() turns a saved plan into the windows of the v2.1
bounded baseband policy (allowlisted LRPT passes, verified UTC only); nothing here records.
"""
from datetime import datetime, timedelta, timezone
import argparse
import errno
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

from . import geo_look, orbits

REFERENCE = {"skyfield": "1.55", "sgp4": "2.27"}
MAX_HOURS = 72.0
MAX_RECORDS = 64
MAX_PASSES = 2000
MAX_PLAN_BYTES = 2 * 1024 * 1024
OBSERVER_ROUNDING_DEG = 0.1
SGP4_MAX_SATNUM = 339999
SCOPE = "Reference prediction from local OMM only; Gpredict agreement within 1 s is POL-11 (BUILDER), not evidenced here."
PASS_FIELDS = ("norad_id", "name", "aos_utc", "tca_utc", "los_utc", "max_el_deg", "aos_az_deg", "tca_az_deg",
               "los_az_deg", "duration_s", "omm_epoch_utc", "omm_age_days", "omm_age_warning", "time_verified",
               "observer_source", "observer_age_ms", "v_dipole_hint", "predictor")
PLAN_FIELDS = ("schema_version", "kind", "start_utc", "hours", "min_el_deg", "time_verified", "observer",
               "predictor", "passes", "skipped", "window_edge_partial_passes", "truncated", "scope")
REQUEST_FIELDS = ("schema_version", "kind", "start_utc", "hours", "min_el_deg", "time_verified", "location")
MAX_REQUEST_BYTES = 64 * 1024
PLAN_MODES = (0o600, 0o640)
PLAN_NAME = re.compile(r"[0-9a-f]{16}\.json\Z")  # labd job ids (srrx.pass_jobs); --keep removes no other name
MAX_KEEP = 64
# Window pre-filter of the v2.1 bounded baseband policy, which allows Meteor-M N2-3/N2-4 LRPT only
# (build/12-revision-v2.1.md). It is the operator allowlist's role label, bound to no NORAD id (none
# is hard-coded); the reviewed allowlist must give it only to those two, and the future recorder
# must enforce the Meteor-only set itself (an open item of the recorder package).
BASEBAND_ROLE = "LRPT"
_runtime = None


class PassDependencyError(RuntimeError):
    pass


class PassError(ValueError):
    pass


def _skyfield():
    global _runtime
    if _runtime is None:
        try:
            from importlib.metadata import version
            from skyfield.api import EarthSatellite, load, wgs84
            versions = {"skyfield": version("skyfield"), "sgp4": version("sgp4")}
        except ImportError as error:
            raise PassDependencyError("Skyfield 1.55 and sgp4 2.27 are required for pass prediction; "
                                      "install the hashed passes lock into /opt/srrx/passes-venv "
                                      "(software/DEPLOYMENT.md)") from error
        except Exception as error:  # e.g. PackageNotFoundError or a broken native extension.
            raise PassDependencyError("Skyfield/sgp4 failed to load: " + type(error).__name__) from error
        _runtime = {"EarthSatellite": EarthSatellite, "timescale": load.timescale(builtin=True),
                    "wgs84": wgs84, "versions": versions}
    return _runtime


def _iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _real(value, low, high):
    # Range before isfinite: a codec-valid huge int (10**400) must not raise OverflowError.
    return type(value) in (int, float) and low <= value <= high and math.isfinite(value)


def _utc_seconds(value, label):
    if not _real(value, 0, 4.2e9) or value == 4.2e9:
        raise PassError(label + " must be finite Unix seconds")
    return float(value)


STORED_SOURCE = "last_good"  # a stored GNSS position: a last-good position, never a live fix
FILE_SOURCES = ("manual", STORED_SOURCE)  # the only observer labels coordinates from a file keep


def _stored_source(source):
    return source if source in FILE_SOURCES else STORED_SOURCE


def stored_observer(status):
    """A location status read from a file: never fresh or live, and gpsd/nmea become last_good."""
    if type(status) is not dict:
        return status
    return dict(status, source=_stored_source(status.get("source")), fresh=False, live_fix=False)


def predict(records, observer, t0_utc, hours=24, min_el=0.0, *, time_verified=False, first_fix_stable=False,
            observer_from_file=False):
    """Return a bounded pass plan for allowlisted srrx.orbits records.

    observer_from_file=True: the status was read from a file (stored_observer); it can never be a
    live, qualified GNSS fix. A gpsd/nmea status that is not live is labelled last_good as well.
    """
    if type(records) is not list or not 0 < len(records) <= MAX_RECORDS:
        raise PassError("records must be a list of 1..64 srrx.orbits records")
    checked = [orbits.validate_record(record) for record in records]
    if len({record["norad_id"] for record in checked}) != len(checked):
        raise PassError("records must have unique NORAD ids")
    start = _utc_seconds(t0_utc, "t0_utc")
    if not _real(hours, 0, MAX_HOURS) or hours == 0:
        raise PassError("hours must be in (0, 72]")
    if not _real(min_el, 0, 90) or min_el == 90:
        raise PassError("min_el must be in [0, 90)")
    if observer_from_file is not False:
        observer, first_fix_stable = stored_observer(observer), False
    place, reason = geo_look.observer_from_status(observer, first_fix_stable)
    if place is None:
        raise PassError("no usable observer position: " + reason)
    if place["source"] in geo_look.GNSS_SOURCES and place["fresh"] is not True:
        place = dict(place, source=STORED_SOURCE)  # a stale GNSS position is not labelled as live GNSS
    runtime = _skyfield()
    ts, versions = runtime["timescale"], runtime["versions"]
    lat, lon = round(place["lat"], 1) + 0.0, round(place["lon"], 1) + 0.0
    alt = round(place["alt_m"], -2) + 0.0
    topos = runtime["wgs84"].latlon(lat, lon, elevation_m=alt)
    begin = datetime.fromtimestamp(start, timezone.utc)
    t0, t1 = ts.from_datetime(begin), ts.from_datetime(begin + timedelta(hours=hours))
    predictor = {"skyfield": versions["skyfield"], "sgp4": versions["sgp4"], "reference": dict(REFERENCE),
                 "reference_versions_match": versions == REFERENCE, "timescale": "skyfield_builtin",
                 "ephemeris_file": None}
    verified = time_verified is True
    passes, skipped, partial = [], [], 0
    for record in sorted(checked, key=lambda item: item["norad_id"]):
        if record["norad_id"] > SGP4_MAX_SATNUM:
            skipped.append({"norad_id": record["norad_id"], "reason": "SATNUM_BEYOND_SGP4_ALPHA5"})
            continue
        satellite = runtime["EarthSatellite"].from_omm(ts, record["elements"])
        relative = satellite - topos
        times, events = satellite.find_events(topos, t0, t1, altitude_degrees=min_el)
        ages = orbits.age(record["elements"]["EPOCH"], record["role"], start, verified)
        current, orphan = None, False
        for moment, event in zip(times, events):
            event = int(event)
            if event == 0:
                partial += current is not None
                current, orphan = {"aos": moment, "culminations": []}, False
            elif event == 1:
                if current is None:
                    orphan = True  # Already above the threshold at the window start.
                else:
                    current["culminations"].append(moment)
            elif current is not None and current["culminations"]:
                look = {}
                for name, when in (("aos", current["aos"]), ("los", moment)):
                    altitude, azimuth, unused = relative.at(when).altaz()
                    look[name] = (when, azimuth.degrees)
                best = None
                for when in current["culminations"]:
                    altitude, azimuth, unused = relative.at(when).altaz()
                    if best is None or altitude.degrees > best[1]:
                        best = (when, altitude.degrees, azimuth.degrees)
                aos, los = look["aos"][0].utc_datetime(), look["los"][0].utc_datetime()
                passes.append({"norad_id": record["norad_id"], "name": record["name"],
                               "aos_utc": _iso(aos), "tca_utc": _iso(best[0].utc_datetime()), "los_utc": _iso(los),
                               "max_el_deg": round(float(best[1]), 3), "aos_az_deg": round(float(look["aos"][1]), 3),
                               "tca_az_deg": round(float(best[2]), 3), "los_az_deg": round(float(look["los"][1]), 3),
                               "duration_s": round((los - aos).total_seconds(), 3),
                               "omm_epoch_utc": record["epoch_utc"], "omm_age_days": ages["age_days"],
                               "omm_age_warning": ages["age_warning"], "time_verified": verified,
                               "observer_source": place["source"], "observer_age_ms": place["age_ms"],
                               "v_dipole_hint": (geo_look.v_dipole_hint(max(0.0, min(90.0, float(best[1]))))
                                                 if record["role"] == "LRPT" else None),
                               "predictor": dict(predictor)})
                current = None
            else:
                partial += 1
                current, orphan = None, False
        partial += current is not None or orphan
    passes.sort(key=lambda item: (item["aos_utc"], item["norad_id"]))
    truncated = len(passes) > MAX_PASSES
    return {"schema_version": 1, "kind": "srrx_pass_plan", "start_utc": _iso(begin), "hours": float(hours),
            "min_el_deg": float(min_el), "time_verified": verified,
            "observer": {"lat_rounded": lat, "lon_rounded": lon, "alt_rounded_m": alt,
                         "rounding_deg": OBSERVER_ROUNDING_DEG, "source": place["source"], "age_ms": place["age_ms"],
                         "qualified_fix": place["qualified_fix"], "qualification_failures": place["qualification_failures"]},
            "predictor": predictor, "passes": passes[:MAX_PASSES], "skipped": skipped,
            "window_edge_partial_passes": int(partial), "truncated": truncated, "scope": SCOPE}


def _text(value, limit):
    return type(value) is str and 0 < len(value) <= limit and value.isprintable()


OBSERVER_FIELDS = ("lat_rounded", "lon_rounded", "alt_rounded_m", "rounding_deg", "source", "age_ms",
                   "qualified_fix", "qualification_failures")


def _stored_plan(value):
    """The plan as a file holds it: a snapshot whose observer is never a live, qualified GNSS fix."""
    observer = dict(value["observer"], source=_stored_source(value["observer"]["source"]), qualified_fix=False)
    if observer["source"] != value["observer"]["source"] or "NOT_A_GNSS_FIX" not in observer["qualification_failures"]:
        others = [item for item in observer["qualification_failures"] if item != "NOT_A_GNSS_FIX"]
        observer["qualification_failures"] = ["NOT_A_GNSS_FIX"] + others[:15]  # still <= 16 entries
    passes = [dict(item, observer_source=_stored_source(item["observer_source"])) for item in value["passes"]]
    return dict(value, observer=observer, passes=passes)


def validate_plan(value):
    """Stdlib-only schema check for a saved plan (HMI snapshot display).

    Returns a new plan as a file holds it (_stored_plan): gpsd/nmea/unknown observer labels become
    last_good and qualified_fix is false; the input is not modified."""
    if type(value) is not dict or set(value) != set(PLAN_FIELDS) or type(value["schema_version"]) is not int \
            or value["schema_version"] != 1 \
            or value["kind"] != "srrx_pass_plan" or type(value["passes"]) is not list \
            or len(value["passes"]) > MAX_PASSES or type(value["time_verified"]) is not bool \
            or type(value["truncated"]) is not bool or not _text(value["start_utc"], 32) \
            or not _real(value["hours"], 0, MAX_HOURS) or not _real(value["min_el_deg"], 0, 90) \
            or type(value["skipped"]) is not list or len(value["skipped"]) > MAX_RECORDS \
            or type(value["window_edge_partial_passes"]) is not int or not _text(value["scope"], 400):
        raise PassError("not an srrx_pass_plan v1")
    observer, predictor = value["observer"], value["predictor"]
    # Exactly the rounded fields predict() writes: no extra (e.g. precise) position key.
    if type(observer) is not dict or set(observer) != set(OBSERVER_FIELDS) \
            or not _real(observer["lat_rounded"], -90, 90) \
            or not _real(observer["lon_rounded"], -180, 180) or observer["rounding_deg"] != OBSERVER_ROUNDING_DEG \
            or round(observer["lat_rounded"], 1) != observer["lat_rounded"] or round(observer["lon_rounded"], 1) != observer["lon_rounded"] \
            or not _real(observer["alt_rounded_m"], -1000, 20000) or observer["alt_rounded_m"] % 100 \
            or type(observer["qualified_fix"]) is not bool or not _text(observer["source"], 32) \
            or observer["age_ms"] is not None and (type(observer["age_ms"]) is not int or observer["age_ms"] < 0) \
            or type(observer["qualification_failures"]) is not list or len(observer["qualification_failures"]) > 16 \
            or not all(_text(item, 64) for item in observer["qualification_failures"]):
        raise PassError("plan observer must be rounded to 0.1 deg")
    if type(predictor) is not dict or not _text(predictor.get("skyfield"), 32) or not _text(predictor.get("sgp4"), 32):
        raise PassError("plan predictor versions missing")
    previous = ""
    for item in value["passes"]:
        if (type(item) is not dict or set(item) != set(PASS_FIELDS) or type(item["norad_id"]) is not int
                or not _text(item["name"], 64) or not all(_text(item[k], 32) for k in ("aos_utc", "tca_utc", "los_utc"))
                or not item["aos_utc"] <= item["tca_utc"] <= item["los_utc"] or item["aos_utc"] < previous
                or not _real(item["max_el_deg"], -90, 90) or not _real(item["duration_s"], 0, MAX_HOURS * 3600)
                or not all(_real(item[k], 0, 360) for k in ("aos_az_deg", "tca_az_deg", "los_az_deg"))
                or type(item["time_verified"]) is not bool or type(item["omm_age_warning"]) is not bool
                or item["v_dipole_hint"] not in (None, geo_look.BISECTOR_NS, geo_look.TIPS_NS)
                or not _text(item["omm_epoch_utc"], 40) or not _text(item["observer_source"], 32)
                or item["omm_age_days"] is not None and not _real(item["omm_age_days"], -1e6, 1e6)
                or item["observer_age_ms"] is not None and (type(item["observer_age_ms"]) is not int
                                                            or item["observer_age_ms"] < 0)
                or type(item["predictor"]) is not dict):
            raise PassError("invalid pass entry")
        previous = item["aos_utc"]
    return _stored_plan(value)


def _location_snapshot(path):
    data = orbits._read(path, 64 * 1024)
    value = orbits._json(data)
    if type(value) is not dict:
        raise PassError("location snapshot must be a JSON object")
    return value


def _start(text):
    try:
        moment = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise PassError("--start-utc must be YYYY-MM-DDTHH:MM:SSZ") from error
    return moment.timestamp()


_NO_HARD_LINKS = frozenset(getattr(errno, name) for name in ("EPERM", "ENOTSUP", "EOPNOTSUPP", "ENOSYS", "EXDEV")
                           if hasattr(errno, name))
_link = os.link  # module-local: tests patch this name, never the process-wide os.link


def _set_mode(descriptor, mode):
    if mode != 0o600 and hasattr(os, "fchmod"):  # Windows has no fchmod and no group bits
        try:
            os.fchmod(descriptor, mode)
        except BaseException:
            os.close(descriptor)
            raise


def _write_synced(descriptor, data):
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_plan(plan, path, *, mode=0o600):
    """Write a new plan file; refuses an existing path (no overwrite).

    The plan is written and fsynced in an O_EXCL temporary file next to path,
    then hard-linked to path, which fails if path exists; the temporary name is
    always removed. A failed write or fsync never leaves a partial plan at path.
    Without hard links (e.g. vfat) path is created O_EXCL and removed again on
    any write failure. mode is 0600 or 0640 (srrx-passes@.service: group-readable
    in the setgid labd plan directory), set before the plan is linked into place.
    """
    if mode not in PLAN_MODES:
        raise PassError("plan file mode must be 0600 or 0640")
    data = (json.dumps(validate_plan(plan), indent=2, allow_nan=False) + "\n").encode("ascii")
    if len(data) > MAX_PLAN_BYTES:
        raise PassError("plan exceeds 2 MiB")
    path = Path(path)
    if os.path.lexists(path):
        raise FileExistsError(errno.EEXIST, "plan output exists; it is never replaced")
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name[:64] + ".", suffix=".tmp", dir=path.parent)
    try:
        _set_mode(descriptor, mode)  # umask-independent; mkstemp created 0600
        _write_synced(descriptor, data)
        try:
            _link(temporary, path)  # atomic, and never replaces an existing path
        except FileExistsError:
            raise
        except OSError as error:
            if error.errno not in _NO_HARD_LINKS:
                raise
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
                                 | getattr(os, "O_BINARY", 0), 0o600)
            try:
                _set_mode(descriptor, mode)
                _write_synced(descriptor, data)
            except BaseException:
                path.unlink(missing_ok=True)
                raise
    finally:
        Path(temporary).unlink(missing_ok=True)
    if os.name != "nt":  # Windows has no directory fsync; the file data was fsynced above.
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        except OSError as error:
            raise OSError(error.errno, "Plan written, but directory fsync failed; durability not confirmed") from error
        finally:
            os.close(directory)
    return len(data)


def prune_plans(directory, keep, current):
    """Keep `current` and the newest keep-1 other labd plan files (16 hex digits + .json) in directory.

    Only regular files with exactly that name pattern are candidates (never a symlink or
    any other name), so --keep removes nothing a labd job did not name. The plan just
    written is kept even if a clock step made its mtime older. Returns the count removed.
    """
    if type(keep) is not int or not 1 <= keep <= MAX_KEEP:
        raise PassError("--keep must be 1..64")
    others = []
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.name != current and PLAN_NAME.match(entry.name) and entry.is_file(follow_symlinks=False):
                others.append((entry.stat(follow_symlinks=False).st_mtime_ns, entry.name))
    removed = 0
    for unused, name in sorted(others, reverse=True)[keep - 1:]:
        try:
            os.unlink(os.path.join(directory, name))
            removed += 1
        except FileNotFoundError:
            pass
    return removed


def request_record(start_utc_s, hours, min_el_deg, time_verified, location):
    """The srrx_pass_request v1 one labd job hands to srrx-passes@.service (srrx.pass_jobs)."""
    start = _utc_seconds(start_utc_s, "start_utc_s")
    if start != int(start) or type(time_verified) is not bool or type(location) is not dict:
        raise PassError("a request needs whole-second UTC, a boolean UTC state and a location status")
    return {"schema_version": 1, "kind": "srrx_pass_request",
            "start_utc": datetime.fromtimestamp(start, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "hours": hours, "min_el_deg": min_el_deg, "time_verified": time_verified, "location": location}


def load_request(path):
    """Read an srrx_pass_request v1: exact fields; predict() bounds the window and the location."""
    value = orbits._json(orbits._read(path, MAX_REQUEST_BYTES))
    if (type(value) is not dict or set(value) != set(REQUEST_FIELDS) or type(value["schema_version"]) is not int
            or value["schema_version"] != 1 or value["kind"] != "srrx_pass_request"
            or type(value["time_verified"]) is not bool or type(value["location"]) is not dict
            or not _text(value["start_utc"], 32)):
        raise PassError("not an srrx_pass_request v1")
    return {"start": _start(value["start_utc"]), "hours": value["hours"], "min_el": value["min_el_deg"],
            "time_verified": value["time_verified"], "location": value["location"]}


def _unix_s(text):
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()
    except (TypeError, ValueError) as error:
        raise PassError("pass times must be YYYY-MM-DDTHH:MM:SS.fffZ") from error


def baseband_windows(plan, norad_ids):
    """Recording windows of the v2.1 bounded baseband policy, taken from a saved plan.

    norad_ids: the allowlist targets with role BASEBAND_ROLE (LRPT). A window is exactly
    [AOS, LOS] of one complete pass of such a target in a plan that passes validate_plan;
    passes cut by the plan window are not listed, so they never give a window. Fails
    closed: a plan without verified UTC gives no window at all (UTC_NOT_VERIFIED), since
    its times are provisional. This is the window source only; no recorder exists, and
    the Meteor-only target set is not checked here (BASEBAND_ROLE).
    """
    stored = validate_plan(plan)
    if not isinstance(norad_ids, (set, frozenset, list, tuple)) or not all(
            type(norad) is int and 1 <= norad <= 999999 for norad in norad_ids):
        raise PassError("norad_ids must be a collection of NORAD ids")
    if stored["time_verified"] is not True:
        return {"windows": [], "reason": "UTC_NOT_VERIFIED"}
    ids = frozenset(norad_ids)
    windows = [{"norad_id": item["norad_id"], "name": item["name"], "start_utc": item["aos_utc"],
                "end_utc": item["los_utc"], "start_unix_s": _unix_s(item["aos_utc"]),
                "end_unix_s": _unix_s(item["los_utc"])}
               for item in stored["passes"] if item["norad_id"] in ids and item["time_verified"] is True]
    return {"windows": windows, "reason": None if windows else "NO_ALLOWLISTED_PASS"}


def window_at(windows, utc_s):
    """The baseband window that contains utc_s (verified Unix seconds), or None."""
    if not _real(utc_s, 0, 4.2e9):
        return None
    for window in windows:
        if window["start_unix_s"] <= utc_s <= window["end_unix_s"]:
            return window
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Reference pass plan from a local OMM file (no network).")
    parser.add_argument("--omm", type=Path, required=True)
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--location", type=Path, help="srrx.location status snapshot JSON")
    parser.add_argument("--start-utc")
    parser.add_argument("--hours", type=float, help="default 24")
    parser.add_argument("--min-el", type=float, help="default 0")
    parser.add_argument("--time-verified", action="store_true", help="the caller's UTC is verified")
    parser.add_argument("--request", type=Path, help="srrx_pass_request v1 of one labd job; replaces "
                        "--location, --start-utc, --hours, --min-el and --time-verified")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--group-readable", action="store_true", help="plan file mode 0640 instead of 0600")
    parser.add_argument("--keep", type=int, help="then keep this plan and the newest N-1 other labd plans (1..64)")
    args = parser.parse_args(argv)
    if args.request is not None and (args.time_verified or any(
            value is not None for value in (args.location, args.start_utc, args.hours, args.min_el))):
        parser.error("--request replaces --location, --start-utc, --hours, --min-el and --time-verified")
    if args.request is None and (args.location is None or args.start_utc is None):
        parser.error("--location and --start-utc are required without --request")
    try:
        if args.keep is not None and (not 1 <= args.keep <= MAX_KEEP or not PLAN_NAME.match(args.output.name)):
            raise PassError("--keep needs 1..64 and a labd plan name (16 hex digits + .json)")
        if args.request is not None:
            job = load_request(args.request)
        else:
            job = {"start": _start(args.start_utc), "hours": 24.0 if args.hours is None else args.hours,
                   "min_el": 0.0 if args.min_el is None else args.min_el, "time_verified": args.time_verified,
                   "location": None}
        records = orbits.load_omm(args.omm, allow_norad=orbits.load_allowlist(args.allowlist),
                                  now_utc_s=job["start"], utc_verified=job["time_verified"])
        if not records:
            raise PassError("no allowlisted element sets in the OMM file")
        location = job["location"] if args.request is not None else _location_snapshot(args.location)
        plan = predict(records, location, job["start"], job["hours"], job["min_el"],
                       time_verified=job["time_verified"], observer_from_file=True)
        write_plan(plan, args.output, mode=0o640 if args.group_readable else 0o600)
        pruned = None if args.keep is None else prune_plans(args.output.parent, args.keep, args.output.name)
    except (OSError, ValueError, PassDependencyError) as error:
        print("srrx.passes: " + str(error)[:300], file=sys.stderr)
        return 2
    result = {"status": "PLAN_WRITTEN", "passes": len(plan["passes"]), "time_verified": plan["time_verified"],
              "truncated": plan["truncated"]}
    if pruned is not None:
        result["pruned"] = pruned
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
