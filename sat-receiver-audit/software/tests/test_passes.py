"""Reference pass prediction (Skyfield from_omm/find_events) and its stdlib guards.

The Skyfield cases need the passes-venv packages (Skyfield 1.55, sgp4 2.27,
jplephem, certifi; software/DEPLOYMENT.md, hashes in
deployment/linux_lab/wheelhouse-requirements.txt). A skip is
not evidence. Element sets and catalogue numbers are synthetic; the observer is
an unnamed lat/lon point. Gpredict agreement within 1 s is POL-11 (BUILDER).
"""
from datetime import datetime, timedelta, timezone
import errno
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from srrx import geo_look, orbits, passes
from srrx.passes import PASS_FIELDS, PassDependencyError, PassError, predict, validate_plan

ROOT = Path(__file__).resolve().parents[2]
HAVE_SKYFIELD = all(importlib.util.find_spec(name) is not None for name in ("skyfield", "sgp4", "jplephem"))
EPOCH = "2026-10-20T06:00:00.000000"
START = orbits.epoch_unix_s(EPOCH) + 43200.0


def raw(norad, **changes):
    value = {"OBJECT_NAME": "SYNTHETIC LEO %d" % norad, "OBJECT_ID": "2026-902A", "EPOCH": EPOCH,
             "MEAN_MOTION": 14.2412, "ECCENTRICITY": 0.00071, "INCLINATION": 98.71, "RA_OF_ASC_NODE": 120.5,
             "ARG_OF_PERICENTER": 87.25, "MEAN_ANOMALY": 272.9, "EPHEMERIS_TYPE": 0, "CLASSIFICATION_TYPE": "U",
             "NORAD_CAT_ID": norad, "ELEMENT_SET_NO": 999, "REV_AT_EPOCH": 4321, "BSTAR": 0.00012,
             "MEAN_MOTION_DOT": 1.2e-06, "MEAN_MOTION_DDOT": 0.0}
    value.update(changes)
    return value


def records(*entries, now=START, verified=True):
    """entries: (norad, role, overrides) for synthetic objects."""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "omm.json"
        path.write_text(json.dumps([raw(norad, **changes) for norad, role, changes in entries]))
        allow = {norad: {"norad_id": norad, "name": "ALIAS %d" % norad, "role": role} for norad, role, unused in entries}
        return orbits.load_omm(path, allow_norad=allow, now_utc_s=now, utc_verified=verified)


def observer(**changes):
    status = {"available": True, "source": "nmea", "origin": "nmea", "fresh": True, "live_fix": True, "mode": 3,
              "satellites": 9, "lat": 50.0, "lon": 10.0, "age_ms": 300, "alt_hae_m": 250.0, "reason": None}
    status.update(changes)
    return status


def minimal_plan(**changes):
    plan = {"schema_version": 1, "kind": "srrx_pass_plan", "start_utc": "2026-10-20T18:00:00.000Z", "hours": 24.0,
            "min_el_deg": 0.0, "time_verified": False,
            "observer": {"lat_rounded": 50.0, "lon_rounded": 10.0, "alt_rounded_m": 200.0, "rounding_deg": 0.1,
                         "source": "nmea", "age_ms": 300, "qualified_fix": False, "qualification_failures": []},
            "predictor": {"skyfield": "1.55", "sgp4": "2.27"}, "passes": [], "skipped": [],
            "window_edge_partial_passes": 0, "truncated": False, "scope": passes.SCOPE}
    plan.update(changes)
    return plan


class StdlibGuardTests(unittest.TestCase):
    def test_import_does_not_load_skyfield_or_numpy(self):
        code = "import sys, srrx.passes, srrx.orbits, srrx.geo_look; print(sorted(m for m in ('skyfield', 'sgp4', 'numpy') if m in sys.modules))"
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60,
                                env=dict(os.environ, PYTHONPATH=str(ROOT / "software")))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[]")

    def test_missing_skyfield_raises_dependency_error_after_validation(self):
        sets = records((90100, "LRPT", {}))
        with patch.dict(sys.modules, {"skyfield": None, "skyfield.api": None}), patch.object(passes, "_runtime", None):
            with self.assertRaises(ValueError):
                predict([{"norad_id": 1}], observer(), START)  # Inputs are checked before any import.
            with self.assertRaises(PassDependencyError):
                predict(sets, observer(), START)
            with self.assertRaises(PassDependencyError):
                passes._skyfield()

    def test_arguments_are_bounded_before_prediction(self):
        good = [{"x": 1}]
        for args in (([], observer(), START), ("x", observer(), START), ([{}] * 65, observer(), START)):
            with self.assertRaises(PassError):
                predict(*args)
        with self.assertRaises(ValueError):
            predict(good, observer(), START)
        sets = records((90100, "LRPT", {}))
        with patch.object(passes, "_skyfield", side_effect=AssertionError("predictor loaded before validation")):
            for kwargs in ({"hours": 0}, {"hours": 73}, {"hours": float("nan")}, {"min_el": 90}, {"min_el": -1},
                           {"t0_utc": float("inf")}, {"t0_utc": True}):
                arguments = dict({"records": sets, "observer": observer(), "t0_utc": START}, **kwargs)
                with self.subTest(kwargs=kwargs), self.assertRaises(PassError):
                    predict(**arguments)
            for status in ({"available": False, "reason": "NO_LOCATION"}, observer(reason="MONOTONIC_TIME_REVERSED"), None):
                with self.assertRaises(PassError):
                    predict(sets, status, START)
            with self.assertRaises(PassError):
                predict(sets + sets, observer(), START)

    def test_saved_plan_schema_is_checked_without_skyfield(self):
        self.assertEqual(validate_plan(minimal_plan())["kind"], "srrx_pass_plan")
        entry = {"norad_id": 90100, "name": "ALIAS", "aos_utc": "2026-10-20T19:00:00.000Z", "tca_utc": "2026-10-20T19:05:00.000Z",
                 "los_utc": "2026-10-20T19:10:00.000Z", "max_el_deg": 40.0, "aos_az_deg": 10.0, "tca_az_deg": 80.0,
                 "los_az_deg": 170.0, "duration_s": 600.0, "omm_epoch_utc": EPOCH + "Z", "omm_age_days": 0.5,
                 "omm_age_warning": False, "time_verified": False, "observer_source": "nmea", "observer_age_ms": 300,
                 "v_dipole_hint": "BISECTOR_NS", "predictor": {"skyfield": "1.55", "sgp4": "2.27"}}
        validate_plan(minimal_plan(passes=[entry]))
        later = dict(entry, aos_utc="2026-10-20T18:30:00.000Z")
        bad = [minimal_plan(schema_version=True), minimal_plan(kind="other"), minimal_plan(extra=1),
               minimal_plan(observer=dict(minimal_plan()["observer"], lat_rounded=50.123456)),
               minimal_plan(passes=[entry, later]), minimal_plan(passes=[dict(entry, v_dipole_hint="UP")]),
               minimal_plan(passes=[dict(entry, tca_utc="2026-10-20T19:20:00.000Z")]),
               minimal_plan(passes=[dict(entry, extra=1)]), minimal_plan(passes=[entry] * 2001), "plan"]
        place = minimal_plan()["observer"]
        for changes in ({"lat_precise": 50.123456}, {"lon_precise": 10.98}, {"alt_rounded_m": 250.0},
                        {"alt_rounded_m": 10 ** 400}, {"source": ""}, {"age_ms": -1}, {"age_ms": 1.5},
                        {"qualification_failures": "FIX_NOT_3D"}, {"qualification_failures": [1]}):
            bad.append(minimal_plan(observer=dict(place, **changes)))
        bad.append(minimal_plan(observer={key: value for key, value in place.items() if key != "source"}))
        huge = 10 ** 400  # codec-valid JSON integers must be refused, never raise OverflowError
        bad += [minimal_plan(hours=huge), minimal_plan(min_el_deg=-huge),
                minimal_plan(observer=dict(place, lat_rounded=huge)),
                minimal_plan(passes=[dict(entry, max_el_deg=huge)]), minimal_plan(passes=[dict(entry, duration_s=huge)]),
                minimal_plan(passes=[dict(entry, omm_age_days=huge)]), minimal_plan(passes=[dict(entry, observer_age_ms=-1)]),
                minimal_plan(passes=[dict(entry, observer_source=None)]), minimal_plan(passes=[dict(entry, predictor=[])])]
        for plan in bad:
            with self.subTest(plan=str(plan)[:60]), self.assertRaises(PassError):
                validate_plan(plan)
        validate_plan(minimal_plan(observer=dict(place, age_ms=None, qualification_failures=["FIX_NOT_3D"])))
        validate_plan(minimal_plan(passes=[dict(entry, omm_age_days=None, observer_age_ms=None)]))
        sets = records((90100, "LRPT", {}))
        with patch.object(passes, "_skyfield", side_effect=AssertionError("predictor loaded")):
            for kwargs in ({"t0_utc": huge}, {"hours": huge}, {"min_el": -huge}):
                with self.subTest(kwargs=kwargs), self.assertRaises(PassError):
                    predict(**dict({"records": sets, "observer": observer(), "t0_utc": START}, **kwargs))
            # A huge altitude is ignored (0 m assumed), not an OverflowError: validation reaches the predictor.
            with self.assertRaisesRegex(AssertionError, "predictor loaded"):
                predict(sets, observer(alt_hae_m=huge), START)

    def test_coordinates_from_files_never_carry_a_live_gnss_label(self):
        entry = {"norad_id": 90100, "name": "ALIAS", "aos_utc": "2026-10-20T19:00:00.000Z", "tca_utc": "2026-10-20T19:05:00.000Z",
                 "los_utc": "2026-10-20T19:10:00.000Z", "max_el_deg": 40.0, "aos_az_deg": 10.0, "tca_az_deg": 80.0,
                 "los_az_deg": 170.0, "duration_s": 600.0, "omm_epoch_utc": EPOCH + "Z", "omm_age_days": 0.5,
                 "omm_age_warning": False, "time_verified": False, "observer_source": "gpsd", "observer_age_ms": 300,
                 "v_dipole_hint": "BISECTOR_NS", "predictor": {"skyfield": "1.55", "sgp4": "2.27"}}
        place = dict(minimal_plan()["observer"], source="gpsd", qualified_fix=True, qualification_failures=[])
        for source in ("gpsd", "nmea", "GPSD", "satellite"):
            plan = minimal_plan(observer=dict(place, source=source), passes=[dict(entry, observer_source=source)])
            original = json.dumps(plan, sort_keys=True)
            with self.subTest(source=source):
                stored = validate_plan(plan)
                self.assertEqual(json.dumps(plan, sort_keys=True), original)  # the input is not modified
                self.assertEqual((stored["observer"]["source"], stored["observer"]["qualified_fix"]), ("last_good", False))
                self.assertEqual(stored["observer"]["qualification_failures"], ["NOT_A_GNSS_FIX"])
                self.assertEqual([p["observer_source"] for p in stored["passes"]], ["last_good"])
                self.assertEqual(validate_plan(stored), stored)  # a stored plan re-validates unchanged
        manual = validate_plan(minimal_plan(observer=dict(place, source="manual", qualification_failures=["FIX_NOT_3D"] * 16)))
        self.assertEqual(manual["observer"]["source"], "manual")
        self.assertEqual(len(manual["observer"]["qualification_failures"]), 16)
        self.assertEqual(manual["observer"]["qualification_failures"][0], "NOT_A_GNSS_FIX")
        self.assertEqual(validate_plan(manual), manual)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "plan.json"
            passes.write_plan(minimal_plan(observer=place, passes=[entry]), output)
            text = output.read_text()
        self.assertNotIn('"gpsd"', text)
        self.assertNotIn('"qualified_fix": true', text)
        # A location snapshot read from a file: last_good, never fresh or live, never qualified.
        for source in ("gpsd", "nmea"):
            stored = passes.stored_observer(observer(source=source, origin=source))
            self.assertEqual((stored["source"], stored["fresh"], stored["live_fix"]), ("last_good", False, False))
            place_from_file, unused = geo_look.observer_from_status(stored, True)
            self.assertEqual((place_from_file["source"], place_from_file["qualified_fix"]), ("last_good", False))
        self.assertEqual(passes.stored_observer(observer(source="manual"))["source"], "manual")
        sets = records((90100, "LRPT", {}))
        for status, kwargs in ((observer(), {"observer_from_file": True}), (observer(source="gpsd", fresh=False, live_fix=False), {})):
            with self.subTest(kwargs=kwargs), patch.object(passes.geo_look, "observer_from_status", wraps=geo_look.observer_from_status) as seen, \
                    patch.object(passes, "_skyfield", side_effect=AssertionError("predictor loaded")):
                with self.assertRaisesRegex(AssertionError, "predictor loaded"):
                    predict(sets, status, START, first_fix_stable=True, **kwargs)
                handed, stable = seen.call_args[0]
                if kwargs:
                    self.assertEqual((handed["source"], handed["fresh"], stable), ("last_good", False, False))
                    self.assertEqual(geo_look.observer_from_status(handed, stable)[0]["qualified_fix"], False)

    def test_plan_is_published_atomically_and_never_replaces_or_leaves_a_partial_file(self):
        plan = minimal_plan()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "plan.json"
            def broken(descriptor, data):  # ENOSPC halfway through the temporary file
                os.write(descriptor, data[:10])
                os.close(descriptor)
                raise OSError(28, "No space left on device")
            with patch.object(passes, "_write_synced", side_effect=broken), self.assertRaises(OSError):
                passes.write_plan(plan, output)
            self.assertEqual(os.listdir(directory), [])  # no partial plan and no temporary file
            size = passes.write_plan(plan, output)  # a retry is not blocked by a leftover
            self.assertEqual(json.loads(output.read_text()), validate_plan(plan))  # the stored (file) form
            self.assertEqual(size, output.stat().st_size)
            before = output.read_bytes()
            (root / "existing.json").write_text("{}")
            for target in (output, root / "existing.json"):
                with self.subTest(target=target.name), self.assertRaises(FileExistsError):
                    passes.write_plan(plan, target)
            self.assertEqual(output.read_bytes(), before)
            self.assertEqual((root / "existing.json").read_text(), "{}")
            self.assertEqual(sorted(os.listdir(directory)), ["existing.json", "plan.json"])
            with patch.object(passes, "_link", side_effect=FileExistsError(17, "raced")), \
                    self.assertRaises(FileExistsError):
                passes.write_plan(plan, root / "raced.json")
            self.assertFalse((root / "raced.json").exists())
            # A filesystem without hard links (vfat): exclusive create, removed again if the write fails.
            real, calls = passes._write_synced, []
            def second_fails(descriptor, data):  # the temporary file is fine, the final O_EXCL write fails
                calls.append(1)
                if len(calls) == 2:
                    os.write(descriptor, data[:10])
                    os.close(descriptor)
                    raise OSError(errno.EIO, "I/O error")
                real(descriptor, data)
            with patch.object(passes, "_link", side_effect=OSError(errno.EPERM, "no hard links")):
                passes.write_plan(plan, root / "vfat.json")
                self.assertEqual(json.loads((root / "vfat.json").read_text()), validate_plan(plan))
                with patch.object(passes, "_write_synced", side_effect=second_fails), self.assertRaises(OSError):
                    passes.write_plan(plan, root / "vfat-broken.json")
            self.assertEqual(len(calls), 2)
            self.assertFalse((root / "vfat-broken.json").exists())
            self.assertEqual(sorted(os.listdir(directory)), ["existing.json", "plan.json", "vfat.json"])
            with patch.object(passes, "_link", side_effect=OSError(errno.EIO, "other")), self.assertRaises(OSError):
                passes.write_plan(plan, root / "io.json")
            self.assertFalse((root / "io.json").exists())
            self.assertIs(passes._link, os.link)


@unittest.skipUnless(HAVE_SKYFIELD, "Skyfield 1.55/sgp4 2.27 passes-venv predictor is not installed (a skip is not evidence)")
class SkyfieldPassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from skyfield.api import EarthSatellite, load, wgs84
        cls.EarthSatellite, cls.wgs84, cls.ts = EarthSatellite, wgs84, load.timescale(builtin=True)
        cls.sets = records((90100, "LRPT", {}), (90101, "ISS", {"MEAN_MOTION": 15.49, "INCLINATION": 51.64,
                                                               "RA_OF_ASC_NODE": 210.0, "BSTAR": 0.0002}))
        cls.plan = predict(cls.sets, observer(), START, hours=24, min_el=0.0, time_verified=False)

    def elevation(self, record, when):
        satellite = self.EarthSatellite.from_omm(self.ts, record["elements"])
        place = self.plan["observer"]
        topos = self.wgs84.latlon(place["lat_rounded"], place["lon_rounded"], elevation_m=place["alt_rounded_m"])
        return (satellite - topos).at(self.ts.from_datetime(when)).altaz()[0].degrees

    @staticmethod
    def moment(text):
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

    def test_plan_is_ordered_complete_and_labelled(self):
        plan = self.plan
        # In memory the plan records the live nmea fix; its stored (file) form never claims live GNSS.
        stored = validate_plan(plan)
        self.assertEqual({k: v for k, v in stored.items() if k not in ("observer", "passes")},
                         {k: v for k, v in plan.items() if k not in ("observer", "passes")})
        self.assertEqual(stored["passes"], [dict(p, observer_source="last_good") for p in plan["passes"]])
        self.assertEqual((stored["observer"]["source"], stored["observer"]["qualified_fix"]), ("last_good", False))
        self.assertGreaterEqual(len(plan["passes"]), 4)
        self.assertEqual([p["aos_utc"] for p in plan["passes"]], sorted(p["aos_utc"] for p in plan["passes"]))
        start, end = datetime.fromtimestamp(START, timezone.utc), datetime.fromtimestamp(START + 86400, timezone.utc)
        for item in plan["passes"]:
            self.assertEqual(tuple(item), PASS_FIELDS)
            aos, tca, los = (self.moment(item[k]) for k in ("aos_utc", "tca_utc", "los_utc"))
            self.assertTrue(start <= aos < tca < los <= end)
            self.assertAlmostEqual(item["duration_s"], (los - aos).total_seconds(), places=2)
            self.assertFalse(item["time_verified"])
            self.assertEqual((item["observer_source"], item["observer_age_ms"]), ("nmea", 300))
            self.assertEqual(item["predictor"]["timescale"], "skyfield_builtin")
            self.assertIsNone(item["predictor"]["ephemeris_file"])
        self.assertEqual({p["norad_id"] for p in plan["passes"]}, {90100, 90101})
        self.assertEqual(plan["predictor"]["reference"], {"skyfield": "1.55", "sgp4": "2.27"})
        self.assertEqual((plan["observer"]["lat_rounded"], plan["observer"]["lon_rounded"]), (50.0, 10.0))
        self.assertFalse(plan["observer"]["qualified_fix"])  # No first-run window was supplied.
        self.assertFalse(plan["truncated"])

    def test_tca_is_a_local_maximum_and_matches_max_elevation(self):
        lookup = {r["norad_id"]: r for r in self.sets}
        for item in self.plan["passes"]:
            record, tca = lookup[item["norad_id"]], self.moment(item["tca_utc"])
            peak = self.elevation(record, tca)
            self.assertAlmostEqual(peak, item["max_el_deg"], delta=0.01)
            for offset in (1, 10, 60):
                self.assertGreaterEqual(peak + 1e-6, self.elevation(record, tca - timedelta(seconds=offset)))
                self.assertGreaterEqual(peak + 1e-6, self.elevation(record, tca + timedelta(seconds=offset)))

    def test_aos_and_los_cross_the_threshold_within_one_second(self):
        lookup = {r["norad_id"]: r for r in self.sets}
        for threshold in (0.0, 10.0):
            plan = self.plan if threshold == 0.0 else predict(self.sets, observer(), START, min_el=threshold)
            self.assertTrue(plan["passes"])
            for item in plan["passes"]:
                record = lookup[item["norad_id"]]
                aos, los = self.moment(item["aos_utc"]), self.moment(item["los_utc"])
                second = timedelta(seconds=1)
                self.assertLess(self.elevation(record, aos - second), threshold)
                self.assertGreater(self.elevation(record, aos + second), threshold)
                self.assertGreater(self.elevation(record, los - second), threshold)
                self.assertLess(self.elevation(record, los + second), threshold)
                self.assertGreaterEqual(item["max_el_deg"], threshold)

    def test_dipole_hint_only_for_lrpt_and_follows_maximum_elevation(self):
        for item in self.plan["passes"]:
            if item["norad_id"] == 90100:
                expected = "TIPS_NS" if item["max_el_deg"] <= 30 else "BISECTOR_NS"
                self.assertEqual(item["v_dipole_hint"], expected)
            else:
                self.assertIsNone(item["v_dipole_hint"])

    def test_ages_time_label_and_observer_rounding(self):
        plan = predict(self.sets, observer(lat=50.123456, lon=10.987654), START, hours=12, time_verified=True,
                       first_fix_stable=True)
        self.assertEqual((plan["observer"]["lat_rounded"], plan["observer"]["lon_rounded"]), (50.1, 11.0))
        self.assertTrue(plan["observer"]["qualified_fix"])
        self.assertNotIn("50.123456", json.dumps(plan))
        self.assertNotIn("10.987654", json.dumps(plan))
        for item in plan["passes"]:
            self.assertTrue(item["time_verified"])
            self.assertAlmostEqual(item["omm_age_days"], 0.5, places=6)  # Age at the prediction start.
            self.assertFalse(item["omm_age_warning"])
        stale = predict(self.sets, observer(), START + 3.5 * 86400, hours=24)
        warnings = {item["norad_id"]: item["omm_age_warning"] for item in stale["passes"]}
        self.assertEqual(warnings, {90101: True, 90100: False})  # ISS role warns after 3 days, others after 7.
        # A GNSS status that is not live, or any status read from a file, is labelled last_good, never qualified.
        for status, kwargs in ((observer(source="gpsd", fresh=False, live_fix=False), {}), (observer(), {"observer_from_file": True})):
            plan = predict(self.sets, status, START, hours=6, first_fix_stable=True, **kwargs)
            self.assertEqual((plan["observer"]["source"], plan["observer"]["qualified_fix"]), ("last_good", False))
            self.assertTrue(all(item["observer_source"] == "last_good" for item in plan["passes"]))

    def test_window_edge_passes_are_counted_not_invented(self):
        first = self.plan["passes"][0]
        middle = self.moment(first["tca_utc"]).timestamp()
        clipped = predict(self.sets, observer(), middle, hours=24)
        self.assertGreaterEqual(clipped["window_edge_partial_passes"], 1)
        self.assertTrue(all(p["aos_utc"] >= clipped["start_utc"] for p in clipped["passes"]))
        self.assertNotIn(first["tca_utc"], [p["tca_utc"] for p in clipped["passes"]])

    def test_sgp4_alpha5_limit_is_reported(self):
        sets = records((400001, "OTHER", {}), (90100, "LRPT", {}))
        plan = predict(sets, observer(), START, hours=12)
        self.assertEqual(plan["skipped"], [{"norad_id": 400001, "reason": "SATNUM_BEYOND_SGP4_ALPHA5"}])
        self.assertTrue(all(p["norad_id"] == 90100 for p in plan["passes"]))

    def test_prediction_opens_no_socket_and_writes_no_file(self):
        import socket
        with tempfile.TemporaryDirectory() as directory:
            cwd = os.getcwd()
            os.chdir(directory)
            try:
                with patch.object(passes, "_runtime", None), \
                     patch.object(socket, "socket", side_effect=AssertionError("network used")), \
                     patch("skyfield.iokit.urlopen", side_effect=AssertionError("download attempted")):
                    plan = predict(self.sets, observer(), START, hours=6)
            finally:
                os.chdir(cwd)
            self.assertEqual(os.listdir(directory), [])
        self.assertEqual(plan["predictor"]["timescale"], "skyfield_builtin")

    def test_cli_writes_a_new_bounded_plan_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "omm.json").write_text(json.dumps([raw(90100), raw(90999)]))
            (root / "allow.json").write_text(json.dumps({"schema_version": 1, "kind": "srrx_orbit_allowlist",
                                                         "targets": [{"norad_id": 90100, "name": "ALIAS", "role": "LRPT"}]}))
            (root / "where.json").write_text(json.dumps(observer(lat=50.04321, lon=10.01234)))
            output = root / "plan.json"
            argv = ["--omm", str(root / "omm.json"), "--allowlist", str(root / "allow.json"), "--location",
                    str(root / "where.json"), "--start-utc", "2026-10-20T18:00:00Z", "--hours", "12", "--output", str(output)]
            with patch("builtins.print"):
                self.assertEqual(passes.main(argv), 0)
                plan = validate_plan(json.loads(output.read_text()))
                self.assertEqual({p["norad_id"] for p in plan["passes"]}, {90100})
                self.assertFalse(plan["time_verified"])
                self.assertNotIn("50.04321", output.read_text())
                # The --location file said nmea/live: the stored plan is last_good and unqualified.
                self.assertEqual(json.loads(output.read_text())["observer"]["source"], "last_good")
                self.assertNotIn('"nmea"', output.read_text())
                self.assertFalse(plan["observer"]["qualified_fix"])
                self.assertEqual(passes.main(argv), 2)  # Existing output is never replaced.
                self.assertEqual(passes.main(argv[:-2] + ["--output", str(root / "b.json"), "--hours", "100"]), 2)
                self.assertFalse((root / "b.json").exists())


if __name__ == "__main__":
    unittest.main()
