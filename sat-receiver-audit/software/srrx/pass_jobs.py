"""labd side of pass prediction: the read-only plan_passes operation (stdlib only).

labd never imports Skyfield or NumPy and never predicts inside its own cgroup
(srrx.service: MemoryMax=128M, TasksMax=8). One accepted request starts one sandboxed
oneshot, srrx-passes@<id>.service (software/systemd), with `systemctl start`; the
polkit rule from polkit_rule() lets the labd user start such instances and nothing else.

One job at a time, and at most one accepted request per RATE_LIMIT_MS:

1. request() checks the small JSON request in labd's loop: window hours, minimum
   elevation and the caller's srrx.location status. The position is reduced to the
   plan's own rounding (0.1 deg, altitude 100 m) and labelled stored, never live,
   before it is written anywhere. The configured allowlist must validate.
2. A worker thread writes request.json and the validated allowlist (0600) under
   /run/srrx/passes/<id>/ in labd's runtime directory. PID 1 hands both to the unit
   as credentials (LoadCredential=), so the unit user reads nothing of labd's.
3. `systemctl --no-ask-password start srrx-passes@<id>.service` blocks only that
   worker, never the 20 ms tick, until the oneshot ends. The unit is bounded by its
   TimeoutStartSec=120 and labd by JOB_TIMEOUT_S; the input directory is removed.
4. labd reads /var/lib/srrx/plans/<id>.json (0640, setgid group labd), runs
   passes.validate_plan and checks that the plan answers this job: start, window,
   UTC state, rounded observer, allowlisted NORAD ids and names. Anything else fails
   closed, and the previous valid plan stays current.

status() exposes the job state and a bounded summary without coordinates; errors are
stable codes (ERRORS) and never carry the position or file contents. UTC counts as
verified only through an injected utc_verified() source; none is wired yet, so labd
plans say time_verified=false. The plan is the window source of the v2.1 bounded
baseband policy: windows() returns passes.baseband_windows() for the allowlisted
LRPT targets (none without verified UTC). Nothing here records.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import threading
import time

from . import geo_look, orbits, passes

UNIT_TEMPLATE = "srrx-passes@.service"
UNIT_USER = "srrx-passes"
LABD_USER = "labd"
INPUT_ROOT = Path("/run/srrx/passes")
PLAN_ROOT = Path("/var/lib/srrx/plans")
OMM_PATH = Path("/var/lib/srrx/orbits/gp.json")
ALLOWLIST_PATH = Path("/etc/srrx/orbit-allowlist.json")
INTERPRETER = Path("/opt/srrx/passes-venv/bin/python3")
SYSTEMCTL = "/usr/bin/systemctl"
POLKIT_RULE = "etc/polkit-1/rules.d/60-srrx-passes.rules"
TMPFILES = "etc/tmpfiles.d/srrx-passes.conf"
JOB_ID = re.compile(r"[0-9a-f]{16}\Z")
RATE_LIMIT_MS = 60_000
UNIT_TIMEOUT_S = 120  # TimeoutStartSec= of srrx-passes@.service
JOB_TIMEOUT_S = 150  # systemctl and polkit slack on top of the unit's own bound
KEEP_PLANS = 8  # --keep of the unit
DEFAULT_HOURS = 24.0
MAX_UPCOMING = 8
REQUEST_KEYS = frozenset(("location", "hours", "min_el_deg"))
UPCOMING_FIELDS = ("norad_id", "name", "aos_utc", "tca_utc", "los_utc", "max_el_deg", "aos_az_deg", "tca_az_deg",
                   "los_az_deg", "v_dipole_hint", "omm_age_warning")
STATES = ("IDLE", "RUNNING", "READY", "FAILED")
ERRORS = ("PASSES_DISABLED", "PASSES_CLOSED", "PASSES_BAD_REQUEST", "PASSES_LOCATION_UNUSABLE", "PASSES_BUSY",
          "PASSES_RATE_LIMITED", "PASSES_RUNTIME_MISSING", "PASSES_OMM_MISSING", "PASSES_OMM_INVALID",
          "PASSES_ALLOWLIST_MISSING", "PASSES_ALLOWLIST_INVALID", "PASSES_PLAN_DIR_MISSING", "PASSES_CLOCK_INVALID",
          "PASSES_INPUT_FAILED", "PASSES_UNIT_START_FAILED", "PASSES_UNIT_FAILED", "PASSES_TIMEOUT",
          "PASSES_PLAN_MISSING", "PASSES_PLAN_INVALID", "PASSES_PLAN_MISMATCH", "PASSES_INTERNAL")
_SYSTEMCTL_ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "SYSTEMD_PAGER": "", "SYSTEMD_COLORS": "0"}
_O_FLAGS = getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_BINARY", 0)
_PLAN_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\Z", re.ASCII)


def unit_name(job_id):
    if type(job_id) is not str or not JOB_ID.match(job_id):
        raise ValueError("a plan job id is 16 lowercase hex digits")
    return UNIT_TEMPLATE.replace("@.", "@" + job_id + ".")


def polkit_rule():
    """/etc/polkit-1/rules.d/60-srrx-passes.rules: the labd user may start (only start) a plan instance."""
    return ("// SR-RX: srrx.pass_jobs.polkit_rule(), staged by deployment/deploy.py stage.\n"
            "// The " + LABD_USER + " user may start, and only start, srrx-passes@<16 hex digits>.service.\n"
            "// Any other action, verb, unit or user falls through to the default policy.\n"
            "polkit.addRule(function(action, subject) {\n"
            '    if (action.id == "org.freedesktop.systemd1.manage-units" &&\n'
            '            subject.user == "' + LABD_USER + '" &&\n'
            '            action.lookup("verb") == "start" &&\n'
            '            /^srrx-passes@[0-9a-f]{16}\\.service$/.test(action.lookup("unit"))) {\n'
            "        return polkit.Result.YES;\n"
            "    }\n"
            "});\n")


def tmpfiles():
    """/etc/tmpfiles.d/srrx-passes.conf: the plan directory, setgid group labd (plans are 0640)."""
    return ("# SR-RX pass plans: srrx.pass_jobs.tmpfiles(), staged by deployment/deploy.py stage.\n"
            "# Only srrx-passes@.service writes plans; the setgid group " + LABD_USER + " lets labd and the console\n"
            "# operators read them. Create the system user " + UNIT_USER + " first (software/DEPLOYMENT.md).\n"
            "d /var/lib/srrx 0755 root root -\n"
            "d /var/lib/srrx/orbits 0755 root root -\n"
            "d /var/lib/srrx/plans 2750 " + UNIT_USER + " " + LABD_USER + " -\n")


def staged_files():
    """Relative rootfs path -> text, for deploy.stage."""
    return {POLKIT_RULE: polkit_rule(), TMPFILES: tmpfiles()}


def stored_location(status):
    """The caller's srrx.location status as the snapshot a job may write, or None.

    Never live (passes.stored_observer) and rounded exactly as predict() rounds the
    observer (0.1 deg, 100 m HAE), so nothing finer than the saved plan leaves labd.
    Mode and satellite count stay: they decide the plan's qualification failures.
    """
    try:
        stored = passes.stored_observer(status)
        place, unused = geo_look.observer_from_status(stored)
    except (ValueError, TypeError, OverflowError, RecursionError):
        return None
    if place is None:
        return None
    mode, satellites = stored.get("mode"), stored.get("satellites")
    return {"available": True, "source": place["source"], "fresh": False, "live_fix": False,
            "lat": round(place["lat"], 1) + 0.0, "lon": round(place["lon"], 1) + 0.0,
            "alt_hae_m": round(place["alt_m"], -2) + 0.0 if place["alt_basis"] == "HAE" else None,
            "mode": mode if type(mode) is int and 0 <= mode <= 3 else None,
            "satellites": satellites if type(satellites) is int and 0 <= satellites <= 1000 else None,
            "age_ms": place["age_ms"], "reason": None}


def parse_request(value):
    """((hours, min_el_deg, stored location), None) or (None, stable error code)."""
    if type(value) is not dict or not set(value) <= REQUEST_KEYS or "location" not in value:
        return None, "PASSES_BAD_REQUEST"
    hours, min_el = value.get("hours", DEFAULT_HOURS), value.get("min_el_deg", 0.0)
    if (not passes._real(hours, 0, passes.MAX_HOURS) or hours == 0
            or not passes._real(min_el, 0, 90) or min_el == 90):
        return None, "PASSES_BAD_REQUEST"
    location = stored_location(value["location"])
    if location is None:
        return None, "PASSES_LOCATION_UNUSABLE"
    return (float(hours), float(min_el), location), None


def _refused(code, **extra):
    return dict({"ok": False, "error": code}, **extra)


def _result(state, job=None, error=None, unit_exit=None, completed=None):
    return {"state": state, "request_id": job["id"] if job else None, "error": error, "unit_exit": unit_exit,
            "requested_at_utc": job["requested_at_utc"] if job else None, "completed_at_utc": completed}


def _utc_text(clock, millis=False):
    try:
        moment = datetime.fromtimestamp(int(clock()), timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None
    return moment.strftime("%Y-%m-%dT%H:%M:%S") + (".000Z" if millis else "Z")


def _daemon_thread(target):
    threading.Thread(target=target, name="srrx-passes-job", daemon=True).start()


def _times_ok(plan):
    return all(_PLAN_TIME.match(item[key]) for item in plan["passes"] for key in ("aos_utc", "tca_utc", "los_utc"))


def _answers(plan, expected):
    """The plan answers this job: start, window, UTC state, rounded observer, allowlisted ids/names."""
    observer, names = plan["observer"], expected["names"]
    if (plan["start_utc"] != expected["start_utc"] or plan["hours"] != expected["hours"]
            or plan["min_el_deg"] != expected["min_el_deg"] or plan["time_verified"] is not expected["time_verified"]
            or (observer["lat_rounded"], observer["lon_rounded"], observer["alt_rounded_m"],
                observer["source"]) != expected["observer"]):
        return False
    return (all(item["norad_id"] in names and item["name"] == names[item["norad_id"]]
                and item["time_verified"] is expected["time_verified"] for item in plan["passes"])
            and all(type(item) is dict and item.get("norad_id") in names for item in plan["skipped"]))


def _summary(current, clock):
    """Bounded status view of the current plan: no coordinates, at most MAX_UPCOMING passes."""
    plan, windows = current["plan"], current["windows"]
    now = _utc_text(clock, millis=True) or ""
    upcoming = [{key: item[key] for key in UPCOMING_FIELDS} for item in plan["passes"] if item["los_utc"] > now]
    predictor = plan["predictor"]
    return {"request_id": current["job"]["id"], "start_utc": plan["start_utc"], "hours": plan["hours"],
            "min_el_deg": plan["min_el_deg"], "time_verified": plan["time_verified"],
            "observer_source": plan["observer"]["source"], "qualified_fix": plan["observer"]["qualified_fix"],
            "predictor": {"skyfield": predictor["skyfield"], "sgp4": predictor["sgp4"],
                          "reference_versions_match": predictor.get("reference_versions_match") is True},
            "passes": len(plan["passes"]), "truncated": plan["truncated"], "skipped": len(plan["skipped"]),
            "window_edge_partial_passes": plan["window_edge_partial_passes"], "upcoming": upcoming[:MAX_UPCOMING],
            "baseband": {"role": passes.BASEBAND_ROLE, "windows": len(windows["windows"]), "reason": windows["reason"],
                         "recorder_implemented": False}}


class PassPlanner:
    """labd's plan_passes job runner; see the module docstring. Thread-safe status."""

    def __init__(self, *, input_root=INPUT_ROOT, plan_root=PLAN_ROOT, omm_path=OMM_PATH,
                 allowlist_path=ALLOWLIST_PATH, interpreter=INTERPRETER, start_unit=None, wall_clock=time.time,
                 utc_verified=None, start_thread=None, job_timeout_s=JOB_TIMEOUT_S):
        self.input_root, self.plan_root = Path(input_root), Path(plan_root)
        self.omm_path, self.allowlist_path = Path(omm_path), Path(allowlist_path)
        self.interpreter = Path(interpreter)
        self.start_unit = start_unit or self._systemctl
        self.wall_clock = wall_clock
        # Verified UTC needs the GNSS/chrony time chain (GNSS-UART.md); without a source, plans say false.
        self.utc_verified = utc_verified or (lambda: False)
        self.start_thread = start_thread or _daemon_thread
        self.job_timeout_s = job_timeout_s
        self._lock = threading.Lock()
        self._job = self._process = self._current = None
        self._last_accept_ms = None
        self._closed = False
        self._result = _result("IDLE")

    def request(self, value, now_ms):
        """plan_passes: no lease and nothing switched; a refusal is a stable code, never data."""
        parsed, code = parse_request(value)
        if code:
            return _refused(code)
        now_ms = int(now_ms)
        with self._lock:
            if self._closed:
                return _refused("PASSES_CLOSED")
            if self._job is not None:
                return _refused("PASSES_BUSY", request_id=self._job["id"])
            wait = self._wait_ms(now_ms)
            if wait:
                return _refused("PASSES_RATE_LIMITED", retry_after_ms=wait)
            code, targets = self._preflight()
            if code:
                return _refused(code)
            job, code = self._new_job(parsed, targets)
            if code:
                return _refused(code)
            self._job, self._last_accept_ms = job, now_ms
            self._result = _result("RUNNING", job)
        try:
            self.start_thread(lambda: self._run(job))
        except RuntimeError:  # e.g. TasksMax reached: no thread, so no job
            self._finish(job, {"error": "PASSES_UNIT_START_FAILED", "plan": None, "unit_exit": None})
            return _refused("PASSES_UNIT_START_FAILED")
        return {"ok": True, "state": "RUNNING", "request_id": job["id"]}

    def status(self, now_ms=None):
        with self._lock:
            data, current, last = dict(self._result), self._current, self._last_accept_ms
        wait = 0 if last is None or type(now_ms) is not int else max(0, RATE_LIMIT_MS - (now_ms - last))
        data.update(enabled=True, retry_after_ms=wait,
                    plan=None if current is None else _summary(current, self.wall_clock))
        return data

    def windows(self):
        """v2.1 baseband window source: the current plan's allowlisted LRPT windows (none without verified UTC)."""
        with self._lock:
            current = self._current
        if current is None:
            return {"windows": [], "reason": "NO_PLAN", "request_id": None}
        return {"windows": [dict(window) for window in current["windows"]["windows"]],
                "reason": current["windows"]["reason"], "request_id": current["job"]["id"]}

    def close(self):
        with self._lock:
            self._closed = True
            process = self._process
        if process is not None and process.poll() is None:
            try:
                process.kill()  # the unit itself stays bounded by its TimeoutStartSec=
            except OSError:
                pass

    def _wait_ms(self, now_ms):
        return 0 if self._last_accept_ms is None else max(0, RATE_LIMIT_MS - (now_ms - self._last_accept_ms))

    def _preflight(self):
        """Cheap checks in labd's loop: stats and the <= 64 KiB allowlist. The OMM content is the unit's."""
        if not (self.interpreter.is_file() and os.access(self.interpreter, os.X_OK)):
            return "PASSES_RUNTIME_MISSING", None
        try:
            info = os.stat(self.omm_path)
        except FileNotFoundError:
            return "PASSES_OMM_MISSING", None
        except OSError:
            return "PASSES_OMM_INVALID", None
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= orbits.MAX_OMM_BYTES:
            return "PASSES_OMM_INVALID", None
        try:
            targets = orbits.load_allowlist(self.allowlist_path)
        except FileNotFoundError:
            return "PASSES_ALLOWLIST_MISSING", None
        except (OSError, ValueError, RecursionError):
            return "PASSES_ALLOWLIST_INVALID", None
        if not self.plan_root.is_dir():
            return "PASSES_PLAN_DIR_MISSING", None
        return None, targets

    def _new_job(self, parsed, targets):
        hours, min_el, location = parsed
        start = self.wall_clock()
        if type(start) not in (int, float) or not 0 <= start < 4.2e9:
            return None, "PASSES_CLOCK_INVALID"
        start = int(start)
        try:
            verified = self.utc_verified() is True
        except Exception:
            verified = False
        place = geo_look.observer_from_status(location)[0]
        if place is None:
            return None, "PASSES_LOCATION_UNUSABLE"
        job = {"id": secrets.token_hex(8),
               "request": passes.request_record(start, hours, min_el, verified, location),
               "allowlist": {"schema_version": 1, "kind": "srrx_orbit_allowlist",
                             "targets": [targets[norad] for norad in sorted(targets)]},
               "expected": {"start_utc": passes._iso(datetime.fromtimestamp(start, timezone.utc)), "hours": hours,
                            "min_el_deg": min_el, "time_verified": verified,
                            "observer": (location["lat"], location["lon"], round(place["alt_m"], -2) + 0.0,
                                         location["source"]),
                            "names": {norad: target["name"] for norad, target in targets.items()},
                            "lrpt_ids": frozenset(norad for norad, target in targets.items()
                                                  if target["role"] == passes.BASEBAND_ROLE)}}
        job["requested_at_utc"] = job["request"]["start_utc"]
        return job, None

    def _run(self, job):
        outcome = {"error": "PASSES_INTERNAL", "plan": None, "unit_exit": None}
        try:
            self._steps(job, outcome)
        except Exception:
            outcome.update(error="PASSES_INTERNAL", plan=None)
        finally:
            self._remove_inputs(job)
            self._finish(job, outcome)

    def _steps(self, job, outcome):
        try:
            self._write_inputs(job)
        except (OSError, ValueError):
            outcome["error"] = "PASSES_INPUT_FAILED"
            return
        try:
            outcome["unit_exit"] = code = self.start_unit(unit_name(job["id"]), self.job_timeout_s)
        except subprocess.TimeoutExpired:
            outcome["error"] = "PASSES_TIMEOUT"
            return
        except (OSError, ValueError, subprocess.SubprocessError):
            outcome["error"] = "PASSES_UNIT_START_FAILED"
            return
        if code != 0:
            outcome["error"] = "PASSES_UNIT_FAILED"
            return
        self._remove_inputs(job)  # PID 1 copied them at unit start; no rounded position lingers in /run
        outcome["plan"], outcome["error"] = self._read_plan(job)

    def _write_inputs(self, job):
        try:
            os.mkdir(self.input_root, 0o700)
        except FileExistsError:
            pass
        info = os.lstat(self.input_root)
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise OSError("the pass input directory must be labd's own private directory")
        directory = self.input_root / job["id"]
        os.mkdir(directory, 0o700)  # a fresh random id: an existing entry is refused
        for name, value in (("request.json", job["request"]), ("allowlist.json", job["allowlist"])):
            data = (json.dumps(value, allow_nan=False, sort_keys=True) + "\n").encode("ascii")
            descriptor = os.open(directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _O_FLAGS, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)

    def _remove_inputs(self, job):
        directory = self.input_root / job["id"]
        for name in ("request.json", "allowlist.json"):
            try:
                os.unlink(directory / name)
            except OSError:
                pass
        try:
            os.rmdir(directory)
        except OSError:
            pass

    def _read_plan(self, job):
        """(current, None) for a plan that validates and answers this job, else (None, code)."""
        try:
            descriptor = os.open(self.plan_root / (job["id"] + ".json"), os.O_RDONLY | _O_FLAGS)
        except FileNotFoundError:
            return None, "PASSES_PLAN_MISSING"
        except OSError:
            return None, "PASSES_PLAN_INVALID"
        with os.fdopen(descriptor, "rb") as stream:
            regular = stat.S_ISREG(os.fstat(stream.fileno()).st_mode)
            data = stream.read(passes.MAX_PLAN_BYTES + 1) if regular else b""
        if not data or len(data) > passes.MAX_PLAN_BYTES:
            return None, "PASSES_PLAN_INVALID"
        expected = job["expected"]
        try:
            plan = passes.validate_plan(orbits._json(data))
            if not _times_ok(plan):
                return None, "PASSES_PLAN_INVALID"
            if not _answers(plan, expected):
                return None, "PASSES_PLAN_MISMATCH"
            windows = passes.baseband_windows(plan, expected["lrpt_ids"])
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
            return None, "PASSES_PLAN_INVALID"
        return {"job": job, "plan": plan, "windows": windows}, None

    def _finish(self, job, outcome):
        completed = _utc_text(self.wall_clock)
        with self._lock:
            if self._job is job:
                self._job = None
            if outcome["plan"] is not None:
                self._current = outcome["plan"]
            self._result = _result("FAILED" if outcome["error"] else "READY", job, outcome["error"],
                                   outcome["unit_exit"], completed)

    def _systemctl(self, unit, timeout_s):
        """`systemctl start` of one plan instance; polkit_rule() authorizes the labd user."""
        process = subprocess.Popen([SYSTEMCTL, "--no-ask-password", "--quiet", "start", unit],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   env=dict(_SYSTEMCTL_ENV), cwd="/", close_fds=True)
        with self._lock:
            self._process, closed = process, self._closed
        try:
            if closed:
                process.kill()
            return process.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise
        finally:
            with self._lock:
                self._process = None
