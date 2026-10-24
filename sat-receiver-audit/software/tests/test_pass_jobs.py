"""labd plan_passes (srrx.pass_jobs), srrx-passes@.service, its polkit rule and plan directory.

Host tests only: systemd, polkit and the unit sandbox are not exercised here. An
emulated PID 1 copies the credentials and runs the unit's own ExecStart CLI with the
production paths mapped into a temporary tree. The real transient run under
MemoryMax with no sockets and the A55 timing are guest/Q6A checks (RUNTIME_ONLY).
NORAD ids, element sets and the observer are synthetic.
"""
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from srrx import cli, daemon, geo_look, orbits, pass_jobs, passes
from srrx.engine import Engine
from srrx.hardware import SimHardware
from srrx.hmi import labd_pass_plan_summary
from srrx.link import SimLink

ROOT = Path(__file__).resolve().parents[2]
UNIT = ROOT / "software/systemd" / pass_jobs.UNIT_TEMPLATE
HAVE_SKYFIELD = all(importlib.util.find_spec(name) is not None for name in ("skyfield", "sgp4", "jplephem"))
START = int(datetime(2026, 10, 24, 12, tzinfo=timezone.utc).timestamp())
EPOCH = "2026-10-24T06:00:00.000000"
LRPT, ISS = 90100, 90101


def raw(norad, **changes):
    value = {"OBJECT_NAME": "SYNTHETIC LEO %d" % norad, "OBJECT_ID": "2026-902A", "EPOCH": EPOCH,
             "MEAN_MOTION": 14.2412, "ECCENTRICITY": 0.00071, "INCLINATION": 98.71, "RA_OF_ASC_NODE": 120.5,
             "ARG_OF_PERICENTER": 87.25, "MEAN_ANOMALY": 272.9, "EPHEMERIS_TYPE": 0, "CLASSIFICATION_TYPE": "U",
             "NORAD_CAT_ID": norad, "ELEMENT_SET_NO": 999, "REV_AT_EPOCH": 4321, "BSTAR": 0.00012,
             "MEAN_MOTION_DOT": 1.2e-06, "MEAN_MOTION_DDOT": 0.0}
    value.update(changes)
    return value


def many_targets(count):
    """count allowlist targets with synthetic NORAD ids from 91000; raw() gives each an element set."""
    return [{"norad_id": 91000 + index, "name": "ALIAS %d" % index, "role": "OTHER"} for index in range(count)]


def location(**changes):
    status = {"available": True, "source": "nmea", "origin": "nmea", "fresh": True, "live_fix": True, "mode": 3,
              "satellites": 9, "lat": 50.0432109, "lon": 10.0123456, "age_ms": 300, "alt_hae_m": 263.4,
              "reason": None, "hdop": 0.8, "device": "/dev/lab/gnss"}
    status.update(changes)
    return status


def unit_settings(text):
    """[section] -> key -> [values] of a unit file; comments and blank lines skipped."""
    sections, section = {}, None
    for line in text.splitlines():
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("["):
            section = sections.setdefault(line.strip("[]"), {})
            continue
        key, value = line.split("=", 1)
        section.setdefault(key, []).append(value)
    return sections


def synthetic_plan(request, allowlist, count=3, **changes):
    """A plan that answers one labd job, built from the inputs the job wrote (no Skyfield)."""
    start = datetime.strptime(request["start_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    where, targets = request["location"], allowlist["targets"]
    entries = []
    for index in range(count):
        target = targets[index % len(targets)]
        aos = start + 3600 * (index + 1)
        text = lambda moment: datetime.fromtimestamp(moment, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        entries.append({"norad_id": target["norad_id"], "name": target["name"], "aos_utc": text(aos),
                        "tca_utc": text(aos + 300), "los_utc": text(aos + 600), "max_el_deg": 41.5,
                        "aos_az_deg": 12.5, "tca_az_deg": 80.0, "los_az_deg": 170.0, "duration_s": 600.0,
                        "omm_epoch_utc": EPOCH + "Z", "omm_age_days": 0.25, "omm_age_warning": False,
                        "time_verified": request["time_verified"], "observer_source": where["source"],
                        "observer_age_ms": where["age_ms"],
                        "v_dipole_hint": "BISECTOR_NS" if target["role"] == "LRPT" else None,
                        "predictor": {"skyfield": "1.55", "sgp4": "2.27"}})
    plan = {"schema_version": 1, "kind": "srrx_pass_plan",
            "start_utc": datetime.fromtimestamp(start, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "hours": request["hours"], "min_el_deg": request["min_el_deg"], "time_verified": request["time_verified"],
            "observer": {"lat_rounded": where["lat"], "lon_rounded": where["lon"],
                         "alt_rounded_m": where["alt_hae_m"] if where["alt_hae_m"] is not None else 0.0,
                         "rounding_deg": 0.1, "source": where["source"], "age_ms": where["age_ms"],
                         "qualified_fix": False, "qualification_failures": ["NOT_A_GNSS_FIX"]},
            "predictor": {"skyfield": "1.55", "sgp4": "2.27", "reference_versions_match": True},
            "passes": entries, "skipped": [], "window_edge_partial_passes": 0, "truncated": False,
            "scope": passes.SCOPE}
    plan.update(changes)
    return plan


class Tree:
    """The planner's production paths inside one temporary directory."""
    def __init__(self, test):
        temp = tempfile.TemporaryDirectory(prefix="srrx-pass-jobs-")
        test.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.inputs, self.plans = self.root / "run/srrx/passes", self.root / "var/lib/srrx/plans"
        self.omm, self.allowlist = self.root / "var/lib/srrx/orbits/gp.json", self.root / "etc/srrx/orbit-allowlist.json"
        self.interpreter = self.root / "opt/srrx/passes-venv/bin/python3"
        for path in (self.inputs.parent, self.plans, self.omm.parent, self.allowlist.parent, self.interpreter.parent):
            path.mkdir(parents=True)
        self.omm.write_text(json.dumps([raw(LRPT), raw(ISS, MEAN_MOTION=15.49, INCLINATION=51.64,
                                                         RA_OF_ASC_NODE=210.0, BSTAR=0.0002), raw(90999)]))
        self.write_allowlist([{"norad_id": LRPT, "name": "ALIAS LRPT", "role": "LRPT"},
                              {"norad_id": ISS, "name": "ALIAS ISS", "role": "ISS"}])
        self.interpreter.write_text("#!/bin/sh\n")
        self.interpreter.chmod(0o755)

    def write_allowlist(self, targets):
        self.allowlist.write_text(json.dumps({"schema_version": 1, "kind": "srrx_orbit_allowlist", "targets": targets}))

    def planner(self, start_unit, **kwargs):
        options = dict(input_root=self.inputs, plan_root=self.plans, omm_path=self.omm,
                       allowlist_path=self.allowlist, interpreter=self.interpreter, start_unit=start_unit,
                       wall_clock=lambda: START + 0.75, start_thread=lambda target: target())
        options.update(kwargs)
        return pass_jobs.PassPlanner(**options)

    def job_inputs(self, unit):
        job = unit[len("srrx-passes@"):-len(".service")]
        directory = self.inputs / job
        return job, directory, json.loads((directory / "request.json").read_text()), \
            json.loads((directory / "allowlist.json").read_text())


class FakeUnit:
    """Records what the unit would receive and writes a plan as srrx-passes would (no Skyfield)."""
    def __init__(self, tree, *, code=0, tamper=None, write=True):
        self.tree, self.code, self.tamper, self.write = tree, code, tamper, write
        self.calls, self.seen = [], []

    def __call__(self, unit, timeout_s):
        self.calls.append((unit, timeout_s))
        job, directory, request, allowlist = self.tree.job_inputs(unit)
        modes = {path.name: stat.S_IMODE(path.stat().st_mode) for path in directory.iterdir()}
        self.seen.append({"job": job, "request": request, "allowlist": allowlist, "modes": modes,
                          "directory_mode": stat.S_IMODE(directory.stat().st_mode)})
        if self.write:
            plan = synthetic_plan(request, allowlist)
            output = self.tree.plans / (job + ".json")
            if self.tamper is None:
                passes.write_plan(plan, output, mode=0o640)
            else:
                output.write_bytes(self.tamper(plan, request))
        return self.code


class UnitEmulator:
    """PID 1 for srrx-passes@.service: copies the credentials, then runs the unit's ExecStart CLI."""
    def __init__(self, tree):
        self.tree, self.settings = tree, unit_settings(UNIT.read_text())["Service"]
        self.calls = 0

    def mapped(self, text, job, credentials):
        text = text.replace("%i", job).replace("%d", str(credentials))
        for production, local in ((pass_jobs.INPUT_ROOT, self.tree.inputs), (pass_jobs.PLAN_ROOT, self.tree.plans),
                                  (pass_jobs.OMM_PATH, self.tree.omm)):
            text = text.replace(production.as_posix(), str(local))
        return text

    def __call__(self, unit, timeout_s):
        self.calls += 1
        job = unit[len("srrx-passes@"):-len(".service")]
        credentials = self.tree.root / "run/credentials" / unit
        credentials.mkdir(parents=True)
        try:
            for entry in self.settings["LoadCredential"]:
                name, source = entry.split(":", 1)
                shutil.copyfile(self.mapped(source, job, credentials), credentials / name)
            words = self.mapped(self.settings["ExecStart"][0], job, credentials).split()
            if words[:6] != ["/usr/bin/env", pass_jobs.INTERPRETER.as_posix(), "-I", "-B", "-m", "srrx.passes"]:
                raise AssertionError("unexpected ExecStart prefix: " + repr(words[:6]))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                return passes.main(words[6:])
        finally:
            shutil.rmtree(credentials)  # systemd removes the credentials when the unit stops


def request_value(**changes):
    value = {"location": location(), "hours": 6, "min_el_deg": 0}
    value.update(changes)
    return value


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.tree = Tree(self)
        self.unit = FakeUnit(self.tree)
        self.planner = self.tree.planner(self.unit)

    def test_import_stays_stdlib_only(self):
        code = "import sys, srrx.pass_jobs; print(sorted(m for m in ('skyfield', 'sgp4', 'numpy') if m in sys.modules))"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60,
                                env=dict(os.environ, PYTHONPATH=str(ROOT / "software")))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[]")

    def test_bad_requests_are_refused_before_anything_is_written(self):
        huge = 10 ** 400
        for value in (None, [], "plan", {}, {"hours": 6}, request_value(extra=1), request_value(hours=0),
                      request_value(hours=72.5), request_value(hours=True), request_value(hours=huge),
                      request_value(hours="6"), request_value(min_el_deg=90), request_value(min_el_deg=-1),
                      request_value(min_el_deg=-huge)):
            with self.subTest(value=str(value)[:60]):
                self.assertEqual(self.planner.request(value, 0), {"ok": False, "error": "PASSES_BAD_REQUEST"})
        for status in ({"available": False, "source": "none", "reason": "NO_LOCATION"}, "here",
                       location(reason="MONOTONIC_TIME_REVERSED"), location(lat=95.0), location(lon=True),
                       location(lat=huge)):
            with self.subTest(status=str(status)[:60]):
                self.assertEqual(self.planner.request(request_value(location=status), 0),
                                 {"ok": False, "error": "PASSES_LOCATION_UNUSABLE"})
        self.assertEqual(self.unit.calls, [])
        self.assertFalse(self.tree.inputs.exists())
        self.assertEqual(self.planner.status(0)["state"], "IDLE")
        # Defaults: 24 h above 0 deg.
        self.assertTrue(self.planner.request({"location": location()}, 0)["ok"])
        self.assertEqual((self.unit.seen[0]["request"]["hours"], self.unit.seen[0]["request"]["min_el_deg"]), (24.0, 0.0))

    def test_stored_location_is_rounded_like_the_plan_and_never_live(self):
        stored = pass_jobs.stored_location(location())
        self.assertEqual(stored, {"available": True, "source": "last_good", "fresh": False, "live_fix": False,
                                  "lat": 50.0, "lon": 10.0, "alt_hae_m": 300.0, "mode": 3, "satellites": 9,
                                  "age_ms": 300, "reason": None})
        self.assertEqual(pass_jobs.stored_location(location(source="manual"))["source"], "manual")
        flat = pass_jobs.stored_location(location(mode=2, satellites=None, lat=-0.04, lon=-179.96))
        self.assertEqual((flat["lat"], flat["lon"], flat["alt_hae_m"], flat["mode"], flat["satellites"]),
                         (0.0, -180.0, None, 2, None))
        self.assertEqual(str(flat["lat"]), "0.0")  # never "-0.0"
        # Same observer for predict() before and after the reduction: the rounding is idempotent.
        for status in (location(), location(mode=2), location(alt_hae_m=None), location(lat=-33.35, lon=151.25)):
            reduced = pass_jobs.stored_location(status)
            before = geo_look.observer_from_status(passes.stored_observer(status))[0]
            after = geo_look.observer_from_status(reduced)[0]
            for key in ("lat", "lon"):
                self.assertEqual(round(before[key], 1) + 0.0, round(after[key], 1) + 0.0)
            self.assertEqual(round(before["alt_m"], -2), round(after["alt_m"], -2))
            self.assertEqual((before["source"], before["qualification_failures"]),
                             (after["source"], after["qualification_failures"]))

    def test_rate_limit_and_one_job_at_a_time(self):
        self.assertTrue(self.planner.request(request_value(), 1000)["ok"])
        refused = self.planner.request(request_value(), 31000)
        self.assertEqual((refused["ok"], refused["error"], refused["retry_after_ms"]),
                         (False, "PASSES_RATE_LIMITED", 30000))
        self.assertEqual(self.planner.status(31000)["retry_after_ms"], 30000)
        self.assertTrue(self.planner.request(request_value(), 61000)["ok"])
        self.assertEqual(len(self.unit.calls), 2)
        # A running job refuses the next request whatever the rate.
        pending = []
        planner = self.tree.planner(self.unit, start_thread=pending.append)
        first = planner.request(request_value(), 0)
        self.assertEqual(planner.status(0)["state"], "RUNNING")
        self.assertEqual(planner.request(request_value(), 120000),
                         {"ok": False, "error": "PASSES_BUSY", "request_id": first["request_id"]})
        pending.pop()()
        self.assertEqual(planner.status(120000)["state"], "READY")
        self.assertTrue(planner.request(request_value(), 120000)["ok"])

    def test_preflight_refusals_are_stable_codes_and_keep_the_rate_slot(self):
        def expect(code):
            self.assertEqual(self.planner.request(request_value(), 0), {"ok": False, "error": code})
        self.tree.interpreter.unlink()
        expect("PASSES_RUNTIME_MISSING")
        self.tree.interpreter.write_text("#!/bin/sh\n")
        self.tree.interpreter.chmod(0o644)
        if os.name != "nt" and os.geteuid() != 0:  # root may execute any file with an x bit only
            expect("PASSES_RUNTIME_MISSING")
        self.tree.interpreter.chmod(0o755)
        self.tree.omm.unlink()
        expect("PASSES_OMM_MISSING")
        self.tree.omm.write_bytes(b"")
        expect("PASSES_OMM_INVALID")
        self.tree.omm.write_bytes(b"x" * (orbits.MAX_OMM_BYTES + 1))
        expect("PASSES_OMM_INVALID")
        self.tree.omm.write_text(json.dumps([raw(LRPT)]))
        self.tree.allowlist.unlink()
        expect("PASSES_ALLOWLIST_MISSING")
        for text in ("{", json.dumps({"schema_version": 1, "kind": "srrx_orbit_allowlist", "targets": []})):
            self.tree.allowlist.write_text(text)
            expect("PASSES_ALLOWLIST_INVALID")
        # srrx.orbits accepts up to 256 targets, the unit's predict() at most 64 records.
        self.tree.write_allowlist(many_targets(passes.MAX_RECORDS + 1))
        self.assertEqual(len(orbits.load_allowlist(self.tree.allowlist)), passes.MAX_RECORDS + 1)
        expect("PASSES_ALLOWLIST_TOO_LARGE")
        self.tree.write_allowlist([{"norad_id": LRPT, "name": "ALIAS LRPT", "role": "LRPT"}])
        self.tree.plans.rmdir()
        expect("PASSES_PLAN_DIR_MISSING")
        self.tree.plans.mkdir()
        bad_clock = self.tree.planner(self.unit, wall_clock=lambda: float("nan"))
        self.assertEqual(bad_clock.request(request_value(), 0), {"ok": False, "error": "PASSES_CLOCK_INVALID"})
        self.assertEqual(self.unit.calls, [])
        self.assertTrue(self.planner.request(request_value(), 0)["ok"])  # no refusal used the rate slot

    def test_job_inputs_plan_and_status(self):
        reply = self.planner.request(request_value(), 0)
        self.assertEqual(set(reply), {"ok", "state", "request_id"})
        job = reply["request_id"]
        self.assertTrue(pass_jobs.JOB_ID.match(job))
        self.assertEqual(self.unit.calls, [("srrx-passes@" + job + ".service", pass_jobs.JOB_TIMEOUT_S)])
        seen = self.unit.seen[0]
        if os.name != "nt":
            self.assertEqual(seen["directory_mode"], 0o700)
            self.assertEqual(seen["modes"], {"request.json": 0o600, "allowlist.json": 0o600})
        request = seen["request"]
        self.assertEqual(set(request), set(passes.REQUEST_FIELDS))
        self.assertEqual((request["start_utc"], request["time_verified"]), ("2026-10-24T12:00:00Z", False))
        self.assertEqual(request["location"]["source"], "last_good")
        self.assertEqual((request["location"]["lat"], request["location"]["lon"]), (50.0, 10.0))
        written = json.dumps(seen)
        for precise in ("50.04", "10.01", "263.4", "/dev/lab/gnss", "hdop"):
            self.assertNotIn(precise, written)  # nothing finer than the plan's own rounding is written
        self.assertEqual(orbits.allowlist(seen["allowlist"]), orbits.load_allowlist(self.tree.allowlist))
        self.assertEqual(list(self.tree.inputs.iterdir()), [])  # inputs removed after the job
        status = self.planner.status(0)
        self.assertEqual((status["state"], status["error"], status["unit_exit"], status["request_id"], status["enabled"]),
                         ("READY", None, 0, job, True))
        self.assertEqual((status["requested_at_utc"], status["completed_at_utc"]), ("2026-10-24T12:00:00Z",) * 2)
        plan = status["plan"]
        self.assertEqual((plan["request_id"], plan["passes"], plan["time_verified"], plan["observer_source"],
                          plan["qualified_fix"]), (job, 3, False, "last_good", False))
        self.assertEqual([item["norad_id"] for item in plan["upcoming"]], [LRPT, ISS, LRPT])
        self.assertEqual(tuple(plan["upcoming"][0]), pass_jobs.UPCOMING_FIELDS)
        self.assertEqual(plan["baseband"], {"role": "LRPT", "windows": 0, "reason": "UTC_NOT_VERIFIED",
                                            "recorder_implemented": False})
        text = json.dumps(status, allow_nan=False)
        for coordinate in ('"lat', '"lon', "50.0", "10.0", "alt_"):
            self.assertNotIn(coordinate, text)  # status never carries the observer position
        self.assertEqual(self.planner.windows(), {"windows": [], "reason": "UTC_NOT_VERIFIED", "request_id": job})

    def test_verified_utc_gives_lrpt_windows_only(self):
        planner = self.tree.planner(self.unit, utc_verified=lambda: True)
        self.assertEqual(planner.windows(), {"windows": [], "reason": "NO_PLAN", "request_id": None})
        job = planner.request(request_value(), 0)["request_id"]
        self.assertTrue(self.unit.seen[-1]["request"]["time_verified"])
        result = planner.windows()
        self.assertEqual((result["reason"], result["request_id"]), (None, job))
        self.assertEqual([(w["norad_id"], w["start_utc"], w["end_utc"]) for w in result["windows"]],
                         [(LRPT, "2026-10-24T13:00:00.000Z", "2026-10-24T13:10:00.000Z"),
                          (LRPT, "2026-10-24T15:00:00.000Z", "2026-10-24T15:10:00.000Z")])
        self.assertEqual(planner.status(0)["plan"]["baseband"]["windows"], 2)
        window = passes.window_at(result["windows"], START + 3600 + 1)
        self.assertEqual(window["norad_id"], LRPT)
        self.assertIsNone(passes.window_at(result["windows"], START + 2 * 3600 + 1))  # the ISS pass: no window
        self.assertIsNone(passes.window_at(result["windows"], float("nan")))
        result["windows"].clear()
        self.assertEqual(len(planner.windows()["windows"]), 2)  # callers get copies
        # A failing utc_verified source is unverified, never an exception.
        failing = self.tree.planner(self.unit, utc_verified=lambda: 1 / 0)
        failing.request(request_value(), 0)
        self.assertFalse(self.unit.seen[-1]["request"]["time_verified"])
        truthy = self.tree.planner(self.unit, utc_verified=lambda: "yes")
        truthy.request(request_value(), 0)
        self.assertFalse(self.unit.seen[-1]["request"]["time_verified"])

    def test_upcoming_is_bounded_and_follows_the_clock(self):
        now = [START]
        def unit(name, timeout_s):
            job, unused, request, allowlist = self.tree.job_inputs(name)
            passes.write_plan(synthetic_plan(request, allowlist, count=40), self.tree.plans / (job + ".json"))
            return 0
        planner = self.tree.planner(unit, wall_clock=lambda: now[0])
        planner.request(request_value(hours=72), 0)
        plan = planner.status(0)["plan"]
        self.assertEqual((plan["passes"], len(plan["upcoming"])), (40, pass_jobs.MAX_UPCOMING))
        now[0] = START + 3600 * 38 + 601  # after the 38th pass
        self.assertEqual([item["aos_utc"][11:16] for item in planner.status(0)["plan"]["upcoming"]], ["03:00", "04:00"])
        now[0] = START + 3600 * 50
        self.assertEqual(planner.status(0)["plan"]["upcoming"], [])
        self.assertLess(len(json.dumps(planner.status(0))), 8192)

    def test_unit_failures_are_stable_codes_and_keep_the_previous_plan(self):
        self.assertTrue(self.planner.request(request_value(), 0)["ok"])
        good = self.planner.status(0)["plan"]["request_id"]
        cases = [
            (FakeUnit(self.tree, code=1), "PASSES_UNIT_FAILED", 1),
            (FakeUnit(self.tree, code=0, write=False), "PASSES_PLAN_MISSING", 0),
            (lambda unit, timeout: (_ for _ in ()).throw(subprocess.TimeoutExpired("systemctl", timeout)), "PASSES_TIMEOUT", None),
            (lambda unit, timeout: (_ for _ in ()).throw(FileNotFoundError(2, "no systemctl")), "PASSES_UNIT_START_FAILED", None),
            (lambda unit, timeout: (_ for _ in ()).throw(KeyError("bug")), "PASSES_INTERNAL", None),
        ]
        now = 0
        for unit, code, exit_code in cases:
            now += pass_jobs.RATE_LIMIT_MS
            with self.subTest(code=code):
                self.planner.start_unit = unit
                self.assertTrue(self.planner.request(request_value(), now)["ok"])
                status = self.planner.status(now)
                self.assertEqual((status["state"], status["error"], status["unit_exit"]), ("FAILED", code, exit_code))
                self.assertIn(code, pass_jobs.ERRORS)
                self.assertEqual(status["plan"]["request_id"], good)  # the last valid plan stays current
                self.assertEqual(list(self.tree.inputs.iterdir()), [])
        # An input directory that is not labd's own private one refuses the job.
        now += pass_jobs.RATE_LIMIT_MS
        self.planner.start_unit = self.unit
        self.tree.inputs.chmod(0o750)
        if os.name != "nt":
            self.planner.request(request_value(), now)
            self.assertEqual(self.planner.status(now)["error"], "PASSES_INPUT_FAILED")

    def test_tampered_or_foreign_plans_fail_closed(self):
        def edit(change):
            def tamper(plan, request):
                change(plan, request)
                return json.dumps(plan).encode()
            return tamper
        def moved(plan, request):
            plan["observer"]["lat_rounded"] = 50.1
        def foreign(plan, request):
            plan["passes"][0].update(norad_id=90999, name="ALIAS LRPT")
        def renamed(plan, request):
            plan["passes"][0]["name"] = "OTHER NAME"
        def shifted(plan, request):
            plan["start_utc"] = "2026-10-24T12:00:01.000Z"
        def claimed(plan, request):
            plan["time_verified"] = True
            for item in plan["passes"]:
                item["time_verified"] = True
        def window(plan, request):
            plan["hours"] = 12.0
        def skipped(plan, request):
            plan["skipped"] = [{"norad_id": 90999, "reason": "SATNUM_BEYOND_SGP4_ALPHA5"}]
        def skipped_text(plan, request):
            plan["skipped"] = ["x"]
        def precise(plan, request):
            plan["observer"]["lat_precise"] = 50.0432109
        def times(plan, request):
            plan["passes"][0]["aos_utc"] = "2026-10-24 13:00"
        def source(plan, request):
            plan["observer"]["source"] = "manual"
        cases = [(edit(moved), "PASSES_PLAN_MISMATCH"), (edit(foreign), "PASSES_PLAN_MISMATCH"),
                 (edit(renamed), "PASSES_PLAN_MISMATCH"), (edit(shifted), "PASSES_PLAN_MISMATCH"),
                 (edit(claimed), "PASSES_PLAN_MISMATCH"), (edit(window), "PASSES_PLAN_MISMATCH"),
                 (edit(skipped), "PASSES_PLAN_MISMATCH"), (edit(skipped_text), "PASSES_PLAN_MISMATCH"),
                 (edit(source), "PASSES_PLAN_MISMATCH"), (edit(precise), "PASSES_PLAN_INVALID"),
                 (edit(times), "PASSES_PLAN_INVALID"), (lambda plan, request: b"{", "PASSES_PLAN_INVALID"),
                 (lambda plan, request: b'{"kind": 1, "kind": 2}', "PASSES_PLAN_INVALID"),
                 (lambda plan, request: json.dumps(plan).replace("41.5", "NaN").encode(), "PASSES_PLAN_INVALID"),
                 (lambda plan, request: b" " * (passes.MAX_PLAN_BYTES + 1), "PASSES_PLAN_INVALID")]
        now = 0
        for tamper, code in cases:
            with self.subTest(code=code, case=getattr(tamper, "__name__", "")):
                self.planner.start_unit = FakeUnit(self.tree, tamper=tamper)
                self.assertTrue(self.planner.request(request_value(), now)["ok"])
                status = self.planner.status(now)
                self.assertEqual((status["state"], status["error"], status["plan"]), ("FAILED", code, None))
                self.assertEqual(self.planner.windows()["reason"], "NO_PLAN")
            now += pass_jobs.RATE_LIMIT_MS
        if os.name != "nt":  # a symlinked plan is never followed
            def linked(unit, timeout):
                job = unit[len("srrx-passes@"):-len(".service")]
                target = self.tree.root / "elsewhere.json"
                target.write_text("{}")
                (self.tree.plans / (job + ".json")).symlink_to(target)
                return 0
            self.planner.start_unit = linked
            self.planner.request(request_value(), now)
            self.assertEqual(self.planner.status(now)["error"], "PASSES_PLAN_INVALID")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs are POSIX only")
    def test_a_fifo_plan_never_blocks_the_worker(self):
        # The unit user owns the plan directory: a unit that exits 0 after leaving a FIFO there
        # must not hang the job (status RUNNING and PASSES_BUSY until labd restarts).
        def fifo(unit, timeout):
            os.mkfifo(self.tree.plans / (unit[len("srrx-passes@"):-len(".service")] + ".json"), 0o640)
            return 0
        pending = []
        planner = self.tree.planner(fifo, start_thread=pending.append)
        job = planner.request(request_value(), 0)["request_id"]
        worker = threading.Thread(target=pending.pop(), daemon=True)
        worker.start()
        worker.join(10)
        if worker.is_alive():  # a blocking open(): give it a writer so that this test still ends
            os.close(os.open(self.tree.plans / (job + ".json"), os.O_WRONLY | os.O_NONBLOCK))
            worker.join(10)
            self.fail("opening a FIFO plan blocked the job worker")
        status = planner.status(0)
        self.assertEqual((status["state"], status["error"], status["unit_exit"], status["plan"]),
                         ("FAILED", "PASSES_PLAN_INVALID", 0, None))
        # The job slot is free again: the next request is only rate limited, never PASSES_BUSY.
        self.assertEqual(planner.request(request_value(), 1000)["error"], "PASSES_RATE_LIMITED")
        self.assertTrue(planner.request(request_value(), pass_jobs.RATE_LIMIT_MS)["ok"])

    def test_systemctl_runner_argv_timeout_and_close(self):
        calls = []
        class Process:
            def __init__(self, argv, **kwargs):
                calls.append((argv, kwargs))
                self.killed, self.waits = threading.Event(), 0
            def wait(self, timeout=None):
                self.waits += 1
                if behaviour == "timeout" and self.waits == 1:
                    raise subprocess.TimeoutExpired("systemctl", timeout)
                if behaviour == "block":
                    started.set()
                    self.killed.wait(10)
                    return -9
                return -9 if self.killed.is_set() else 0
            def poll(self):
                return None if not self.killed.is_set() else -9
            def kill(self):
                self.killed.set()
        behaviour, started = "ok", threading.Event()
        planner = self.tree.planner(None)
        with patch.object(pass_jobs.subprocess, "Popen", Process):
            job = planner.request(request_value(), 0)["request_id"]
            self.assertEqual(planner.status(0)["error"], "PASSES_PLAN_MISSING")  # systemctl "ran", no unit wrote
            argv, kwargs = calls[0]
            self.assertEqual(argv, ["/usr/bin/systemctl", "--no-ask-password", "--quiet", "start",
                                    "srrx-passes@" + job + ".service"])
            self.assertEqual(kwargs["env"], {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "SYSTEMD_PAGER": "", "SYSTEMD_COLORS": "0"})
            self.assertNotIn("shell", kwargs)
            self.assertEqual((kwargs["stdin"], kwargs["stdout"], kwargs["stderr"]), (subprocess.DEVNULL,) * 3)
            behaviour = "timeout"
            planner.request(request_value(), pass_jobs.RATE_LIMIT_MS)
            self.assertEqual(planner.status(0)["error"], "PASSES_TIMEOUT")
            # close() while systemctl waits: the client is killed, the job ends, later requests are refused.
            behaviour, pending = "block", []
            blocking = self.tree.planner(None, start_thread=pending.append)
            blocking.request(request_value(), 0)
            worker = threading.Thread(target=pending.pop())
            worker.start()
            self.assertTrue(started.wait(10))
            blocking.close()
            worker.join(10)
            self.assertFalse(worker.is_alive())
            self.assertEqual((blocking.status(0)["state"], blocking.status(0)["error"]), ("FAILED", "PASSES_UNIT_FAILED"))
            self.assertEqual(blocking.request(request_value(), 10 ** 9), {"ok": False, "error": "PASSES_CLOSED"})

    def test_a_thread_that_cannot_start_is_no_job(self):
        def no_thread(target):
            raise RuntimeError("can't start new thread")
        planner = self.tree.planner(self.unit, start_thread=no_thread)
        self.assertEqual(planner.request(request_value(), 0), {"ok": False, "error": "PASSES_UNIT_START_FAILED"})
        self.assertEqual((planner.status(0)["state"], planner.status(0)["error"]), ("FAILED", "PASSES_UNIT_START_FAILED"))
        self.assertEqual(planner.request(request_value(), 1)["error"], "PASSES_RATE_LIMITED")


class EngineAndClientTests(unittest.TestCase):
    def setUp(self):
        self.tree = Tree(self)
        hardware = SimHardware()
        hardware.set_inputs({n: False for n in hardware.inputs if n.startswith("DCS_")})
        self.engine = Engine(hardware, SimLink(ROOT), simulated=True)
        self.addCleanup(self.engine.close)
        self.engine.tick(0)

    def test_disabled_without_a_planner(self):
        self.assertEqual(self.engine.status()["passes"], {"enabled": False, "state": "DISABLED"})
        self.assertEqual(self.engine.request({"op": "plan_passes", "value": request_value()}, 10),
                         {"ok": False, "error": "PASSES_DISABLED"})

    def test_read_only_operation_needs_no_lease_and_status_stays_bounded(self):
        def unit(name, timeout_s):
            job, unused, request, allowlist = self.tree.job_inputs(name)
            passes.write_plan(synthetic_plan(request, allowlist, count=passes.MAX_PASSES),
                              self.tree.plans / (job + ".json"))
            return 0
        self.engine.passes = planner = self.tree.planner(unit)
        # Another local operator holds the lease; plan_passes switches nothing and is not refused for it.
        self.assertTrue(self.engine.request({"op": "lease", "value": {"ttl_ms": 5000}, "_owner": "uid:1001"}, 20)["ok"])
        before = self.engine.status()["policy"]
        reply = self.engine.request({"op": "plan_passes", "value": request_value(hours=72), "_owner": "uid:1002"}, 40)
        self.assertTrue(reply["ok"])
        status = self.engine.status()
        self.assertEqual(status["policy"]["outputs"], before["outputs"])
        self.assertEqual(status["passes"]["plan"]["passes"], passes.MAX_PASSES)
        self.assertLessEqual(len(status["passes"]["plan"]["upcoming"]), pass_jobs.MAX_UPCOMING)
        self.assertLess(len(json.dumps(status, allow_nan=False).encode()), 65536)  # labctl/HMI reply limit
        self.assertEqual(self.engine.request({"op": "plan_passes", "value": request_value()}, 60)["error"],
                         "PASSES_RATE_LIMITED")
        self.engine.close()
        self.assertEqual(planner.request(request_value(), 10 ** 9), {"ok": False, "error": "PASSES_CLOSED"})

    def test_labctl_sends_the_location_file_and_bounds_its_size(self):
        snapshot = self.tree.root / "where.json"
        snapshot.write_text(json.dumps(location()))
        sent = []
        def once(path, request, timeout=2.0):
            sent.append(request)
            return {"ok": True, "state": "RUNNING", "request_id": "0" * 16}
        with patch.object(cli, "request_once", side_effect=once), redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["plan_passes", "--location", str(snapshot), "--hours", "12"]), 0)
        # Only the reduced snapshot labd keeps crosses the socket; labd's own reduction leaves it unchanged.
        stored = pass_jobs.stored_location(location())
        self.assertEqual(sent, [{"op": "plan_passes", "value": {"location": stored, "hours": 12.0, "min_el_deg": 0.0}}])
        self.assertEqual(pass_jobs.parse_request(sent[0]["value"]), ((12.0, 0.0, stored), None))
        for precise in ("50.04", "10.01", "263.4", "/dev/lab/gnss", "hdop"):
            self.assertNotIn(precise, json.dumps(sent))
        # The 64 KiB file bound is the effective one: a large snapshot still gives a small request.
        snapshot.write_text(json.dumps(location()) + " " * 60000)
        sent.clear()
        with patch.object(cli, "request_once", side_effect=once), redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["plan_passes", "--location", str(snapshot)]), 0)
        self.assertLess(len(json.dumps(sent[0], separators=(",", ":"))) + 1, daemon.MAX_REQUEST // 4)
        snapshot.write_text(json.dumps(location(lat=95.0)))  # not usable: refused here, nothing sent
        with patch.object(cli, "request_once", side_effect=AssertionError("sent")), redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["plan_passes", "--location", str(snapshot)]), 1)
        snapshot.write_text(json.dumps(location()))
        with patch.object(cli, "request_once", return_value={"ok": False, "error": "PASSES_RATE_LIMITED"}), \
                redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli.main(["plan_passes", "--location", str(snapshot)]), 2)
        self.assertEqual(json.loads(out.getvalue())["error"], "PASSES_RATE_LIMITED")
        snapshot.write_bytes(b" " * 65537)
        with patch.object(cli, "request_once", side_effect=AssertionError("sent")), redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["plan_passes", "--location", str(snapshot)]), 1)
        snapshot.write_text('{"lat": NaN}')
        with patch.object(cli, "request_once", side_effect=AssertionError("sent")), redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["plan_passes", "--location", str(snapshot)]), 1)

    def test_console_text_is_read_only_and_tolerates_bad_status(self):
        self.assertEqual(labd_pass_plan_summary(None, True), "labd pass plan: status unavailable")
        self.assertEqual(labd_pass_plan_summary({"enabled": True}, False), "labd pass plan: status unavailable")
        self.assertIn("not provided", labd_pass_plan_summary({"enabled": False, "state": "DISABLED"}, True))
        self.assertIn("none requested", labd_pass_plan_summary({"enabled": True, "state": "IDLE", "plan": None}, True))
        failed = labd_pass_plan_summary({"enabled": True, "state": "FAILED", "error": "PASSES_PLAN_MISMATCH"}, True)
        self.assertIn("last error PASSES_PLAN_MISMATCH", failed)
        self.assertIn("last error unrecognised", labd_pass_plan_summary({"enabled": True, "state": "FAILED", "error": "x y"}, True))
        plan = {"time_verified": False, "upcoming": [
            {"name": "ALIAS LRPT", "aos_utc": "2026-10-24T13:00:00.000Z", "los_utc": "2026-10-24T13:10:00.000Z",
             "max_el_deg": 41.5}, {"name": "ALIAS ISS"}, "junk"]}
        text = labd_pass_plan_summary({"enabled": True, "state": "READY", "plan": plan}, True)
        self.assertIn("UTC not verified", text)
        self.assertIn("ALIAS LRPT · AOS 10-24 13:00:00 · max 42° · LOS 13:10:00", text)
        self.assertEqual(text.count("unreadable pass entry"), 2)
        self.assertIn("No complete pass ahead", labd_pass_plan_summary(
            {"enabled": True, "state": "READY", "plan": {"time_verified": True, "upcoming": []}}, True))


class ContractTests(unittest.TestCase):
    """The unit, the polkit rule and the plan directory agree with srrx.pass_jobs."""

    def test_unit_is_a_sandboxed_oneshot_started_only_by_labd(self):
        text = UNIT.read_text(encoding="utf-8")
        sections = unit_settings(text)
        self.assertEqual(set(sections), {"Unit", "Service"})  # no [Install]: never enabled
        service = {key: values[-1] for key, values in sections["Service"].items() if key != "LoadCredential"}
        expected = {"Type": "oneshot", "User": pass_jobs.UNIT_USER, "Group": pass_jobs.UNIT_USER,
                    "ReadWritePaths": pass_jobs.PLAN_ROOT.as_posix(), "TimeoutStartSec": str(pass_jobs.UNIT_TIMEOUT_S),
                    "MemoryMax": "512M", "CPUQuota": "100%", "CPUAffinity": "0-3", "Nice": "10", "TasksMax": "4",
                    "NoNewPrivileges": "yes", "CapabilityBoundingSet": "", "PrivateNetwork": "yes",
                    "IPAddressDeny": "any", "RestrictAddressFamilies": "none", "PrivateDevices": "yes",
                    "ProtectSystem": "strict", "ProtectHome": "yes", "PrivateTmp": "yes", "LimitCORE": "0",
                    "UMask": "0027", "SystemCallFilter": "@system-service"}
        for key, value in expected.items():
            self.assertEqual(service.get(key), value, key)
        self.assertLess(pass_jobs.UNIT_TIMEOUT_S, pass_jobs.JOB_TIMEOUT_S)
        for absent in ("RuntimeMaxSec", "IPAddressAllow", "StateDirectory", "SupplementaryGroups", "DynamicUser",
                       "ReadOnlyPaths", "BindPaths", "AmbientCapabilities=CAP", "AF_INET", "AF_UNIX", "Restart="):
            self.assertNotIn(absent, "\n".join(l for l in text.splitlines() if not l.startswith("#")))
        self.assertEqual(sections["Service"]["LoadCredential"],
                         ["request:%s/%%i/request.json" % pass_jobs.INPUT_ROOT.as_posix(),
                          "allowlist:%s/%%i/allowlist.json" % pass_jobs.INPUT_ROOT.as_posix()])
        words = service["ExecStart"].split()
        self.assertEqual(words[:6], ["/usr/bin/env", pass_jobs.INTERPRETER.as_posix(), "-I", "-B", "-m", "srrx.passes"])
        self.assertEqual(words[-3:], ["--group-readable", "--keep", str(pass_jobs.KEEP_PLANS)])
        options = dict(zip(words[6:-3:2], words[7:-3:2]))
        self.assertEqual(options, {"--omm": pass_jobs.OMM_PATH.as_posix(), "--allowlist": "%d/allowlist",
                                   "--request": "%d/request", "--output": pass_jobs.PLAN_ROOT.as_posix() + "/%i.json"})
        self.assertEqual(sections["Unit"]["CollectMode"], ["inactive-or-failed"])

    def test_polkit_rule_allows_exactly_starting_plan_instances_for_labd(self):
        rule = pass_jobs.polkit_rule()
        # The JavaScript literal /^...$/ (no flags) anchors at the whole input, like re.fullmatch.
        regex = re.compile(re.search(r"/\^(.*?)\$/\.test", rule).group(1))
        for unused in range(64):
            self.assertTrue(regex.fullmatch(pass_jobs.unit_name(os.urandom(8).hex())))
        for name in ("srrx-passes@.service", "srrx-passes@0123.service", "srrx-passes@0123456789ABCDEF.service",
                     "srrx-passes@0123456789abcdef0.service", "srrx-passes@0123456789abcdef.service.d",
                     "srrx-passes@0123456789abcdef.servicex", "srrx.service", "srrx-poweroff.service",
                     "srrx-passes@0123456789abcde\n.service", "srrx-passes@0123456789abcdef.service\n",
                     "srrx-passes@../../0123456.service", "undefined"):
            self.assertIsNone(regex.fullmatch(name), name)
        self.assertIn('action.id == "org.freedesktop.systemd1.manage-units"', rule)
        self.assertIn('subject.user == "labd"', rule)
        self.assertIn('action.lookup("verb") == "start"', rule)
        self.assertEqual(rule.count("polkit.Result."), 1)
        self.assertEqual(rule.count("return "), 1)  # anything else falls through to the default policy
        self.assertNotIn("subject.isInGroup", rule)
        for job in ("", "0123456789ABCDEF", "0123", "0123456789abcdef0", None, 7):
            with self.assertRaises(ValueError):
                pass_jobs.unit_name(job)

    def test_plan_directory_is_setgid_labd_and_only_the_unit_writes(self):
        lines = [line.split() for line in pass_jobs.tmpfiles().splitlines() if line and not line.startswith("#")]
        self.assertEqual(lines, [["d", "/var/lib/srrx", "0755", "root", "root", "-"],
                                 ["d", "/var/lib/srrx/orbits", "0755", "root", "root", "-"],
                                 ["d", pass_jobs.PLAN_ROOT.as_posix(), "2750", "srrx-passes", "labd", "-"]])
        self.assertEqual(pass_jobs.OMM_PATH.parent.as_posix(), "/var/lib/srrx/orbits")
        self.assertEqual(set(pass_jobs.staged_files()), {"etc/polkit-1/rules.d/60-srrx-passes.rules",
                                                         "etc/tmpfiles.d/srrx-passes.conf"})
        # labd needs no group of the unit: plans reach it through the setgid labd directory.
        self.assertNotIn("srrx-passes", (ROOT / "software/systemd/srrx.service").read_text())


@unittest.skipUnless(HAVE_SKYFIELD, "Skyfield 1.55/sgp4 2.27 predictor is not installed (a skip is not evidence)")
class UnitChainTests(unittest.TestCase):
    """labd job -> emulated PID 1 -> the unit's real ExecStart CLI (Skyfield) -> labd validation."""

    def setUp(self):
        self.tree = Tree(self)
        self.emulator = UnitEmulator(self.tree)

    def test_real_prediction_through_the_unit_command_line(self):
        planner = self.tree.planner(self.emulator, utc_verified=lambda: True)
        job = planner.request(request_value(hours=24), 0)["request_id"]
        status = planner.status(0)
        self.assertEqual((status["state"], status["error"], status["unit_exit"]), ("READY", None, 0), status)
        plan_file = self.tree.plans / (job + ".json")
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(plan_file.stat().st_mode), 0o640)
        stored = json.loads(plan_file.read_text())
        self.assertEqual((stored["observer"]["lat_rounded"], stored["observer"]["lon_rounded"],
                          stored["observer"]["alt_rounded_m"], stored["observer"]["source"]), (50.0, 10.0, 300.0, "last_good"))
        self.assertNotIn("50.04", plan_file.read_text())
        self.assertEqual({item["norad_id"] for item in stored["passes"]}, {LRPT, ISS})  # 90999 is not allowlisted
        self.assertTrue(stored["time_verified"])
        summary = status["plan"]
        self.assertGreaterEqual(summary["passes"], 4)
        self.assertEqual(summary["predictor"]["reference_versions_match"],
                         stored["predictor"]["reference_versions_match"])
        windows = planner.windows()["windows"]
        self.assertTrue(windows)
        self.assertEqual({window["norad_id"] for window in windows}, {LRPT})
        lrpt = [(p["aos_utc"], p["los_utc"]) for p in stored["passes"] if p["norad_id"] == LRPT]
        self.assertEqual([(w["start_utc"], w["end_utc"]) for w in windows], lrpt)
        self.assertEqual(list(self.tree.inputs.iterdir()), [])
        self.assertFalse((self.tree.root / "run/credentials").exists() and any((self.tree.root / "run/credentials").iterdir()))

    def test_the_largest_allowed_allowlist_runs_through_the_unit(self):
        # Every target is in the OMM, so predict() gets exactly passes.MAX_RECORDS records.
        allowed = many_targets(passes.MAX_RECORDS)
        self.tree.omm.write_text(json.dumps([raw(target["norad_id"], RA_OF_ASC_NODE=index * 5.5)
                                             for index, target in enumerate(allowed)]))
        self.tree.write_allowlist(allowed)
        planner = self.tree.planner(self.emulator)
        planner.request(request_value(hours=6), 0)
        status = planner.status(0)
        self.assertEqual((status["state"], status["error"], status["unit_exit"]), ("READY", None, 0), status)
        self.tree.write_allowlist(many_targets(passes.MAX_RECORDS + 1))
        self.assertEqual(planner.request(request_value(hours=6), pass_jobs.RATE_LIMIT_MS),
                         {"ok": False, "error": "PASSES_ALLOWLIST_TOO_LARGE"})
        self.assertEqual(self.emulator.calls, 1)

    def test_existing_output_is_refused_and_retention_is_bounded(self):
        with patch.object(pass_jobs.secrets, "token_hex", return_value="0123456789abcdef"):
            (self.tree.plans / "0123456789abcdef.json").write_text("{}")
            planner = self.tree.planner(self.emulator)
            planner.request(request_value(hours=6), 0)
        status = planner.status(0)
        self.assertEqual((status["state"], status["error"], status["unit_exit"]), ("FAILED", "PASSES_UNIT_FAILED", 2))
        self.assertEqual((self.tree.plans / "0123456789abcdef.json").read_text(), "{}")  # never replaced
        (self.tree.plans / "0123456789abcdef.json").unlink()
        keep = self.tree.plans / "operator-notes.json"
        keep.write_text("{}")
        names, now = [], 0
        for index in range(pass_jobs.KEEP_PLANS + 3):
            now += pass_jobs.RATE_LIMIT_MS
            reply = planner.request(request_value(hours=6), now)
            names.append(reply["request_id"] + ".json")
            self.assertEqual(planner.status(now)["state"], "READY")
        remaining = sorted(path.name for path in self.tree.plans.iterdir())
        self.assertIn("operator-notes.json", remaining)  # --keep removes only labd plan names
        plans = [name for name in remaining if passes.PLAN_NAME.match(name)]
        self.assertEqual(len(plans), pass_jobs.KEEP_PLANS)
        self.assertIn(names[-1], plans)


class PassesCliTests(unittest.TestCase):
    """The --request/--keep/--group-readable additions of srrx.passes (stdlib parts)."""

    def test_request_records_and_their_validation(self):
        record = passes.request_record(START, 6.0, 0.0, False, pass_jobs.stored_location(location()))
        self.assertEqual(set(record), set(passes.REQUEST_FIELDS))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request"
            path.write_text(json.dumps(record))
            job = passes.load_request(path)
            self.assertEqual((job["start"], job["hours"], job["min_el"], job["time_verified"]), (START, 6.0, 0.0, False))
            for change in ({"kind": "other"}, {"schema_version": True}, {"time_verified": 1}, {"location": []},
                           {"start_utc": "2026-10-24 12:00"}, {"extra": 1}):
                with self.subTest(change=change):
                    path.write_text(json.dumps(dict(record, **change)))
                    with self.assertRaises(ValueError):
                        passes.load_request(path)
            path.write_text(json.dumps(record) + " " * passes.MAX_REQUEST_BYTES)
            with self.assertRaises(ValueError):
                passes.load_request(path)
        for args in ((START + 0.5, 6.0, 0.0, False, {}), (START, 6.0, 0.0, None, {}), (START, 6.0, 0.0, False, None),
                     (-1, 6.0, 0.0, False, {})):
            with self.assertRaises(ValueError):
                passes.request_record(*args)

    def test_cli_option_combinations(self):
        base = ["--omm", "o", "--allowlist", "a", "--output", "p.json"]
        for extra in (["--request", "r", "--location", "l"], ["--request", "r", "--hours", "6"],
                      ["--request", "r", "--time-verified"], ["--location", "l"], ["--start-utc", "2026-10-24T12:00:00Z"]):
            with self.subTest(extra=extra), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                passes.main(base + extra)
        with tempfile.TemporaryDirectory() as directory, redirect_stderr(io.StringIO()):
            output = str(Path(directory) / "0123456789abcdef.json")
            for keep, name in (("0", output), ("65", output), ("8", str(Path(directory) / "plan.json"))):
                self.assertEqual(passes.main(["--omm", "o", "--allowlist", "a", "--request", "r", "--output", name,
                                              "--keep", keep]), 2)
            self.assertEqual(os.listdir(directory), [])

    def test_the_unit_refuses_more_records_than_labd_allows(self):
        # Why labd bounds the allowlist before a job: with every target in the OMM, the unit's own
        # predict() refuses more than passes.MAX_RECORDS records (exit 2, before Skyfield is imported).
        count = passes.MAX_RECORDS + 1
        record = passes.request_record(START, 6.0, 0.0, False, pass_jobs.stored_location(location()))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "gp.json").write_text(json.dumps([raw(target["norad_id"]) for target in many_targets(count)]))
            (root / "allowlist").write_text(json.dumps({"schema_version": 1, "kind": "srrx_orbit_allowlist",
                                                        "targets": many_targets(count)}))
            (root / "request").write_text(json.dumps(record))
            output = root / "0123456789abcdef.json"
            with redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(passes.main(["--omm", str(root / "gp.json"), "--allowlist", str(root / "allowlist"),
                                              "--request", str(root / "request"), "--output", str(output)]), 2)
            self.assertIn("1..64", errors.getvalue())
            self.assertFalse(output.exists())

    def test_group_readable_plans_and_pruning(self):
        plan = synthetic_plan(passes.request_record(START, 6.0, 0.0, False, pass_jobs.stored_location(location())),
                              {"targets": [{"norad_id": LRPT, "name": "ALIAS LRPT", "role": "LRPT"}]})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                passes.write_plan(plan, root / "a.json", mode=0o644)
            self.assertEqual(os.listdir(directory), [])
            names = ["%016x.json" % index for index in range(5)]
            for index, name in enumerate(names):
                passes.write_plan(plan, root / name, mode=0o640 if index % 2 else 0o600)
                os.utime(root / name, ns=(index * 10 ** 9, index * 10 ** 9))
            if os.name != "nt":
                self.assertEqual([stat.S_IMODE((root / n).stat().st_mode) for n in names[:2]], [0o600, 0o640])
            (root / "notes.json").write_text("{}")
            (root / "0123456789ABCDEF.json").write_text("{}")
            if os.name != "nt":
                (root / "fedcba9876543210.json").symlink_to(root / "notes.json")
            os.utime(root / names[0], ns=(10 ** 12, 10 ** 12))  # a clock step: the oldest name looks newest
            self.assertEqual(passes.prune_plans(root, 2, names[4]), 3)
            left = sorted(os.listdir(directory))
            self.assertIn(names[4], left)  # the plan just written survives whatever its mtime
            self.assertIn(names[0], left)  # newest other by mtime
            self.assertIn("notes.json", left)
            self.assertIn("0123456789ABCDEF.json", left)
            for bad in (0, 65, True):
                with self.assertRaises(ValueError):
                    passes.prune_plans(root, bad, names[4])

    def test_baseband_windows_fail_closed(self):
        record = passes.request_record(START, 6.0, 0.0, True, pass_jobs.stored_location(location()))
        targets = {"targets": [{"norad_id": LRPT, "name": "ALIAS LRPT", "role": "LRPT"},
                               {"norad_id": ISS, "name": "ALIAS ISS", "role": "ISS"}]}
        plan = synthetic_plan(record, targets, count=4)
        result = passes.baseband_windows(plan, {LRPT})
        self.assertEqual([w["start_utc"] for w in result["windows"]], ["2026-10-24T13:00:00.000Z", "2026-10-24T15:00:00.000Z"])
        self.assertEqual(result["windows"][0]["end_unix_s"] - result["windows"][0]["start_unix_s"], 600.0)
        self.assertEqual(passes.baseband_windows(plan, set()), {"windows": [], "reason": "NO_ALLOWLISTED_PASS"})
        unverified = synthetic_plan(dict(record, time_verified=False), targets)
        self.assertEqual(passes.baseband_windows(unverified, {LRPT}), {"windows": [], "reason": "UTC_NOT_VERIFIED"})
        mixed = dict(plan, passes=[dict(plan["passes"][0], time_verified=False)] + plan["passes"][1:])
        self.assertEqual(len(passes.baseband_windows(mixed, {LRPT})["windows"]), 1)
        for ids in ({"90100"}, [True], None, {0}):
            with self.assertRaises(ValueError):
                passes.baseband_windows(plan, ids)
        with self.assertRaises(ValueError):
            passes.baseband_windows(dict(plan, kind="other"), {LRPT})
        broken = dict(plan, passes=[dict(plan["passes"][0], aos_utc="2026-10-24T13:00", tca_utc="2026-10-24T13:05")])
        with self.assertRaises(ValueError):
            passes.baseband_windows(broken, {LRPT})


if __name__ == "__main__":
    unittest.main()
