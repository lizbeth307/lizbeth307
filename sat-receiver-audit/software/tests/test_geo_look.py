"""QO-100 look angles, skew sign and the location gate.

Fixtures are unnamed lat/lon points only (09-testy.md:81, HANDOFF D9). The
expected spherical values were recomputed independently for this test from
STACK's formulas (cos g = cos lat cos dlon, el = atan((cos g - 0.15127)/sin g),
az = 180 - atan2(tan dlon, sin lat), tan psi = sin dlon / tan lat) and agree
with the research table within 0.01 deg; the WGS84 model is required within
0.5 deg of them.
"""
import json
import math
from pathlib import Path
import tempfile
import unittest

from srrx import geo_look
from srrx.geo_look import (BISECTOR_NS, TIPS_NS, FirstFixGate, geo_look_angles, lnb_hint,
                           pointing_from_status, v_dipole_hint)
from srrx.location import LocationTracker
from srrx import orbits

# (lat, lon) -> (el, az, skew) for the spherical STACK model at 25.9E.
UNNAMED_POINTS = {(50.0, 10.0): (30.71, 159.60, 12.95), (70.0, 25.0): (11.47, 179.04, 0.33),
                  (38.0, -9.0): (32.97, 131.43, 36.22), (35.0, 33.0): (48.64, 192.25, -10.01)}


def live(**changes):
    status = {"available": True, "source": "nmea", "origin": "nmea", "fresh": True, "live_fix": True,
              "mode": 3, "satellites": 9, "lat": 50.0, "lon": 10.0, "age_ms": 400, "alt_hae_m": 250.0,
              "reason": None}
    status.update(changes)
    return status


def independent_skew(lat, lon, sat_lon=25.9):
    """Skew by basis decomposition on a WGS84 observer, written separately from srrx.geo_look."""
    a, f = 6378.137, 1 / 298.257223563
    e2 = f * (2 - f)
    p, l, s = math.radians(lat), math.radians(lon), math.radians(sat_lon)
    n = a / math.sqrt(1 - e2 * math.sin(p) ** 2)
    o = [n * math.cos(p) * math.cos(l), n * math.cos(p) * math.sin(l), n * (1 - e2) * math.sin(p)]
    g = [42164.0 * math.cos(s), 42164.0 * math.sin(s), 0.0]
    forward = [x - y for x, y in zip(g, o)]
    size = math.sqrt(sum(x * x for x in forward))
    forward = [x / size for x in forward]
    up = [math.cos(p) * math.cos(l), math.cos(p) * math.sin(l), math.sin(p)]
    k = sum(x * y for x, y in zip(up, forward))
    head = [x - k * y for x, y in zip(up, forward)]
    size = math.sqrt(sum(x * x for x in head))
    head = [x / size for x in head]
    # Viewer looking along forward with head up: right-hand side is forward x head.
    right = [forward[1] * head[2] - forward[2] * head[1], forward[2] * head[0] - forward[0] * head[2],
             forward[0] * head[1] - forward[1] * head[0]]
    k = forward[2]
    axis = [-k * forward[0], -k * forward[1], 1 - k * forward[2]]  # Earth axis seen in the view plane.
    # Counter-clockwise for that viewer turns head toward the LEFT (-right).
    angle = math.degrees(math.atan2(-sum(x * y for x, y in zip(axis, right)), sum(x * y for x, y in zip(axis, head))))
    return (angle + 90.0) % 180.0 - 90.0


def omm_record(mean_motion, role="QO100", epoch="2026-10-20T00:00:00.000000", now=None, verified=True):
    raw = {"OBJECT_NAME": "SYNTHETIC GEO", "OBJECT_ID": "2026-900A", "EPOCH": epoch, "MEAN_MOTION": mean_motion,
           "ECCENTRICITY": 0.0002, "INCLINATION": 0.05, "RA_OF_ASC_NODE": 80.0, "ARG_OF_PERICENTER": 200.0,
           "MEAN_ANOMALY": 100.0, "EPHEMERIS_TYPE": 0, "CLASSIFICATION_TYPE": "U", "NORAD_CAT_ID": 90001,
           "ELEMENT_SET_NO": 999, "REV_AT_EPOCH": 2800, "BSTAR": 0.0, "MEAN_MOTION_DOT": -3e-07, "MEAN_MOTION_DDOT": 0.0}
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "geo.json"
        path.write_text(json.dumps([raw]))
        allow = {90001: {"norad_id": 90001, "name": "SYNTHETIC GEO", "role": role}}
        now = orbits.epoch_unix_s(epoch) + 86400 if now is None else now
        return orbits.load_omm(path, allow_norad=allow, now_utc_s=now, utc_verified=verified)[0]


class LookAngleTests(unittest.TestCase):
    def test_unnamed_points_match_recomputed_spherical_values(self):
        for (lat, lon), (el, az, skew) in UNNAMED_POINTS.items():
            with self.subTest(lat=lat, lon=lon):
                look = geo_look_angles(lat, lon, model="sphere")
                self.assertAlmostEqual(look["el_deg"], el, delta=0.05)
                self.assertAlmostEqual(look["az_deg"], az, delta=0.05)
                self.assertAlmostEqual(look["skew_deg"], skew, delta=0.05)
                self.assertTrue(look["above_horizon"])

    def test_wgs84_model_agrees_with_sphere_within_half_degree(self):
        for (lat, lon), (el, az, skew) in UNNAMED_POINTS.items():
            with self.subTest(lat=lat, lon=lon):
                look = geo_look_angles(lat, lon)
                self.assertEqual(look["model"], "wgs84")
                self.assertAlmostEqual(look["el_deg"], el, delta=0.5)
                self.assertAlmostEqual(look["az_deg"], az, delta=0.5)
                self.assertAlmostEqual(look["skew_deg"], skew, delta=0.5)
                self.assertLess(abs(look["el_deg"] - el), 0.06)  # Ellipsoid flattening, not a different answer.
                self.assertGreater(look["range_km"], 35786)
                self.assertLess(look["range_km"], 41700)
        # 38N 9W is STACK's European skew maximum (about 36 deg).
        self.assertAlmostEqual(geo_look_angles(38.0, -9.0, model="sphere")["skew_deg"], 36.0, delta=0.5)

    def test_skew_sign_by_vector_projection_independent_of_tan_formula(self):
        points = list(UNNAMED_POINTS) + [(-30.0, 30.0), (-33.9, 18.4), (45.0, 40.0), (60.0, -5.0), (-20.0, -10.0)]
        for lat, lon in points:
            with self.subTest(lat=lat, lon=lon):
                expected = independent_skew(lat, lon)
                sphere = geo_look_angles(lat, lon, model="sphere")["skew_deg"]
                wgs84 = geo_look_angles(lat, lon)["skew_deg"]
                self.assertAlmostEqual(wgs84, expected, delta=0.01)
                self.assertEqual(math.copysign(1, sphere), math.copysign(1, expected))
                self.assertAlmostEqual(sphere, expected, delta=0.5)
        # Northern observer west of the slot: CCW from behind (+); east of it: CW (-).
        self.assertGreater(geo_look_angles(50.0, 10.0)["skew_deg"], 0)
        self.assertLess(geo_look_angles(50.0, 40.0)["skew_deg"], 0)
        # Southern hemisphere flips the sign for the same side of the slot.
        self.assertLess(geo_look_angles(-30.0, 10.0)["skew_deg"], 0)
        self.assertGreater(geo_look_angles(-30.0, 40.0)["skew_deg"], 0)

    def test_southern_hemisphere_azimuth_points_north(self):
        sphere, wgs84 = geo_look_angles(-30.0, 30.0, model="sphere"), geo_look_angles(-30.0, 30.0)
        self.assertAlmostEqual(sphere["az_deg"], 351.84, delta=0.05)
        self.assertAlmostEqual(wgs84["az_deg"], sphere["az_deg"], delta=0.5)
        # Southern form: az = atan2(tan dlon, |sin lat|) = atan(tan 5.9 / 0.5) = 11.68 deg.
        self.assertAlmostEqual(geo_look_angles(-30.0, 20.0, model="sphere")["az_deg"], 11.68, delta=0.05)

    def test_visibility_and_horizon_flags(self):
        self.assertTrue(geo_look_angles(70.0, 25.0)["visible_5deg"])
        low = geo_look_angles(0.0, 25.9 + 80.0, model="sphere")  # dlon -80: above the horizon, under 5 deg.
        self.assertTrue(low["above_horizon"])
        self.assertFalse(low["visible_5deg"])
        for lat, lon in ((0.0, 25.9 + 82.0), (0.0, 25.9 - 82.0), (82.0, 25.9), (-82.0, 25.9), (10.0, 111.0)):
            for model in ("sphere", "wgs84"):
                with self.subTest(lat=lat, lon=lon, model=model):
                    look = geo_look_angles(lat, lon, model=model)
                    self.assertFalse(look["above_horizon"])
                    self.assertFalse(look["visible_5deg"])
        hidden = geo_look_angles(82.0, 25.9)
        self.assertIsNone(hidden["skew_deg"])
        self.assertEqual(hidden["skew_reason"], "SATELLITE_BELOW_HORIZON")
        # dlon is normalised to (-180, 180]; +180 and -180 observer longitudes are one meridian.
        self.assertAlmostEqual(geo_look_angles(10.0, -170.0)["delta_lon_deg"], -164.1, delta=1e-9)
        self.assertEqual(geo_look_angles(10.0, 180.0)["delta_lon_deg"], geo_look_angles(10.0, -180.0)["delta_lon_deg"])
        self.assertAlmostEqual(geo_look_angles(10.0, -154.1)["delta_lon_deg"], 180.0, delta=1e-9)

    def test_geo_targets_hidden_west_and_shown_east_of_about_13e(self):
        west, east = ((56.0, 6.0), (52.0, -2.0)), ((50.0, 19.0), (54.0, 17.0))
        for slot in (76.05, 79.2):  # Elektro-L5 and FY-2H nominal slots (STACK.md:187).
            for model in ("sphere", "wgs84"):
                for point in west:
                    with self.subTest(slot=slot, model=model, point=point):
                        self.assertLess(geo_look_angles(*point, sat_lon_deg=slot, model=model)["el_deg"], 4.0)
                        self.assertFalse(geo_look_angles(*point, sat_lon_deg=slot, model=model)["visible_5deg"])
                for point in east:
                    with self.subTest(slot=slot, model=model, point=point):
                        self.assertGreater(geo_look_angles(*point, sat_lon_deg=slot, model=model)["el_deg"], 6.0)
                        self.assertTrue(geo_look_angles(*point, sat_lon_deg=slot, model=model)["visible_5deg"])

    def test_equator_guard_and_hint_text(self):
        for lat in (0.0, 0.5, -0.99):
            for model in ("sphere", "wgs84"):
                look = geo_look_angles(lat, 20.0, model=model)
                self.assertIsNone(look["skew_deg"])
                self.assertEqual(look["skew_reason"], "SKEW_UNDEFINED_NEAR_EQUATOR")
        self.assertIsNotNone(geo_look_angles(1.0, 20.0)["skew_deg"])
        self.assertEqual(lnb_hint(None), "LNB skew unavailable")
        self.assertTrue(lnb_hint(12.94).startswith("rotate LNB +12.9° (+ = CCW viewed from behind"))
        self.assertTrue(lnb_hint(-10.01).startswith("rotate LNB -10.0°"))
        self.assertTrue(lnb_hint(-0.04).startswith("rotate LNB +0.0°"))
        self.assertIn("beyond the ±45° neck scale", lnb_hint(52.0))
        for bad in (float("nan"), True, "12", 91.0):
            with self.assertRaises(ValueError):
                lnb_hint(bad)

    def test_inputs_are_validated(self):
        for args in ((91.0, 0.0), (0.0, 181.0), (float("nan"), 0.0), (True, 0.0), (0.0, float("inf")), ("50", 10.0),
                     (10 ** 400, 0.0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                geo_look_angles(*args)
        with self.assertRaises(ValueError):
            geo_look_angles(50.0, 10.0, model="flat")
        with self.assertRaises(ValueError):
            geo_look_angles(50.0, 10.0, alt_m=1e6)


class DipoleTests(unittest.TestCase):
    def test_v_dipole_thresholds(self):
        for elevation, expected in ((29.9, TIPS_NS), (30.0, TIPS_NS), (32.0, BISECTOR_NS), (35.0, BISECTOR_NS),
                                    (36.0, BISECTOR_NS), (0.0, TIPS_NS), (90.0, BISECTOR_NS)):
            with self.subTest(elevation=elevation):
                self.assertEqual(v_dipole_hint(elevation), expected)
        for bad in (-1.0, 90.5, float("nan"), None, True):
            with self.assertRaises(ValueError):
                v_dipole_hint(bad)


class GateTests(unittest.TestCase):
    def test_qualified_fix_needs_fresh_3d_six_satellites_and_first_fix_window(self):
        result = pointing_from_status(live(), first_fix_stable=True)
        self.assertTrue(result["available"])
        self.assertTrue(result["qualified_fix"])
        self.assertEqual(result["fix_label"], "qualified GNSS fix (3D, >=6 satellites)")
        self.assertAlmostEqual(result["el_deg"], 30.74, delta=0.05)
        self.assertTrue(result["lnb_hint"].startswith("rotate LNB +13.1°"))
        for changes, failure in (({"mode": 2}, "FIX_NOT_3D"), ({"satellites": 5}, "FEWER_THAN_6_SATELLITES"),
                                 ({"satellites": None}, "SATELLITE_COUNT_UNKNOWN"),
                                 ({"fresh": False, "live_fix": False}, "GNSS_FIX_NOT_FRESH"),
                                 ({"source": "manual", "fresh": False, "live_fix": False}, "NOT_A_GNSS_FIX")):
            with self.subTest(changes=changes):
                gated = pointing_from_status(live(**changes), first_fix_stable=True)
                self.assertTrue(gated["available"])  # Angles still shown, labelled.
                self.assertFalse(gated["qualified_fix"])
                self.assertIn(failure, gated["qualification_failures"])
                self.assertIsNotNone(gated["el_deg"])
        self.assertIn("FIRST_FIX_STABILITY_NOT_ESTABLISHED", pointing_from_status(live())["qualification_failures"])
        self.assertTrue(pointing_from_status(live(satellites=6), first_fix_stable=True)["qualified_fix"])
        jumped = pointing_from_status(live(), first_fix_stable=True, jump_unconfirmed=True)
        self.assertFalse(jumped["qualified_fix"])
        self.assertEqual(jumped["qualification_failures"], ["POSITION_JUMP_UNCONFIRMED"])
        self.assertIsNotNone(jumped["el_deg"])  # angles stay, labelled not qualified

    def test_codec_valid_huge_numbers_are_refused_or_ignored_never_overflow(self):
        huge = 10 ** 400  # a valid JSON integer; float(huge) raises OverflowError
        observer, reason = geo_look.observer_from_status(live(alt_hae_m=huge))
        self.assertIsNone(reason)
        self.assertEqual((observer["alt_m"], observer["alt_basis"]), (0.0, "ASSUMED_0M"))
        for alt in (-huge, float("inf"), float("nan"), 20001, True, "250"):
            with self.subTest(alt=alt):
                self.assertEqual(geo_look.observer_from_status(live(alt_hae_m=alt))[0]["alt_basis"], "ASSUMED_0M")
        self.assertEqual(geo_look.observer_from_status(live(alt_hae_m=20000))[0]["alt_m"], 20000.0)
        self.assertEqual(geo_look.observer_from_status(live(lat=huge)), (None, "INVALID_POSITION"))
        result = pointing_from_status(live(alt_hae_m=huge, satellites=huge, age_ms=huge), first_fix_stable=True)
        self.assertTrue(result["available"])
        self.assertIn("SATELLITE_COUNT_UNKNOWN", result["qualification_failures"])

    def test_fallbacks_are_labelled_and_missing_fix_gives_no_angles(self):
        manual = pointing_from_status({"available": True, "source": "manual", "lat": 50.0, "lon": 10.0,
                                       "fresh": False, "live_fix": False, "mode": None, "age_ms": 5})
        self.assertEqual(manual["fix_label"], "not a GNSS fix (manual entry)")
        self.assertFalse(manual["qualified_fix"])
        last = pointing_from_status(live(source="last_good", fresh=False, live_fix=False))
        self.assertEqual(last["fix_label"], "not a GNSS fix (last known position)")
        for status, reason in (({"available": False, "source": "none", "lat": None, "lon": None, "reason": "NO_LOCATION"}, "NO_LOCATION"),
                               (live(reason="MONOTONIC_TIME_REVERSED", age_ms=None), "MONOTONIC_TIME_REVERSED"),
                               (live(lat=float("nan")), "INVALID_POSITION"), (None, "NO_LOCATION"), ([], "NO_LOCATION")):
            with self.subTest(reason=reason):
                result = pointing_from_status(status)
                self.assertFalse(result["available"])
                self.assertEqual(result["reason"], reason)
                self.assertIsNone(result["el_deg"])
                self.assertEqual(result["lnb_hint"], "LNB skew unavailable")
        self.assertFalse({"lat", "lon"} & set(pointing_from_status(live(), first_fix_stable=True)))

    def test_gpsd_only_fix_qualifies_once_sky_reports_the_satellites_used(self):
        tracker = LocationTracker()
        tpv = {"class": "TPV", "device": "configured-gnss-device", "mode": 3, "time": "2026-10-20T12:00:00.000Z",
               "lat": 50.0, "lon": 10.0, "eph": 4.5, "altHAE": 250.0}
        self.assertTrue(tracker.ingest_gpsd(tpv, 0))
        self.assertIn("SATELLITE_COUNT_UNKNOWN",
                      pointing_from_status(tracker.status(10), first_fix_stable=True)["qualification_failures"])
        tracker.ingest_gpsd({"class": "SKY", "device": "configured-gnss-device", "time": tpv["time"], "uSat": 7}, 20)
        result = pointing_from_status(tracker.status(30), first_fix_stable=True)
        self.assertEqual((result["observer_source"], result["qualified_fix"]), ("gpsd", True))
        gate = FirstFixGate()
        self.assertFalse(gate.feed(tracker.status(30), 30))  # 7 used: below the first-run 8

    def test_real_tracker_manual_entry_is_never_a_gnss_fix(self):
        tracker = LocationTracker()
        status = tracker.manual(38.0, -9.0, 1000)
        result = pointing_from_status(status, first_fix_stable=True)
        self.assertTrue(result["available"])
        self.assertFalse(result["qualified_fix"])
        self.assertEqual(result["observer_source"], "manual")
        self.assertAlmostEqual(result["el_deg"], 32.99, delta=0.05)
        self.assertFalse(pointing_from_status(LocationTracker().status(0))["available"])

    def test_qo100_visible_only_with_stationary_allowlisted_elements(self):
        nominal = pointing_from_status(live(), first_fix_stable=True)
        self.assertTrue(nominal["geometry_visible_5deg"])
        self.assertFalse(nominal["visible_from_here"])
        self.assertEqual(nominal["tle_status"], "nominal slot 25.9E; TLE not verified")
        stationary = pointing_from_status(live(), first_fix_stable=True, qo100_omm=omm_record(1.00274))
        self.assertTrue(stationary["tle_verified"])
        self.assertTrue(stationary["visible_from_here"])
        self.assertTrue(stationary["auto_pointing_allowed"])
        drifting = pointing_from_status(live(), first_fix_stable=True, qo100_omm=omm_record(1.0040))
        self.assertFalse(drifting["visible_from_here"])
        stale = omm_record(1.00274, now=orbits.epoch_unix_s("2026-10-20T00:00:00") + 8 * 86400)
        aged = pointing_from_status(live(), first_fix_stable=True, qo100_omm=stale)
        self.assertTrue(aged["visible_from_here"])  # Display stays; only auto-pointing is withdrawn.
        self.assertTrue(aged["omm_age_warning"])
        self.assertFalse(aged["auto_pointing_allowed"])
        unverified = pointing_from_status(live(), first_fix_stable=True, qo100_omm=omm_record(1.00274, verified=False))
        self.assertFalse(unverified["auto_pointing_allowed"])
        hidden = pointing_from_status(live(lat=82.0, lon=25.9), first_fix_stable=True, qo100_omm=omm_record(1.00274))
        self.assertFalse(hidden["visible_from_here"])
        with self.assertRaises(ValueError):
            pointing_from_status(live(), qo100_omm=omm_record(1.00274, role="LRPT"))
        with self.assertRaises(ValueError):
            pointing_from_status(live(), qo100_omm={"elements": {}})


class FirstFixGateTests(unittest.TestCase):
    def test_stable_after_five_minutes_of_eight_satellite_3d_fixes_within_50_m(self):
        gate, now = FirstFixGate(), 1000
        for step in range(300):
            self.assertFalse(gate.feed(live(satellites=8, lat=50.0 + 0.0003 * (step % 2)), now))  # ~33 m wander.
            now += 1000
        self.assertTrue(gate.feed(live(satellites=8), now))
        self.assertTrue(gate.feed(live(source="manual", fresh=False, live_fix=False), now + 10))  # Latched for this run.

    @staticmethod
    def run_gate(gate, start, end, status, step=1000):
        """Feed one status per step in [start, end]; return the last result."""
        result = None
        for now in range(start, end + 1, step):
            result = gate.feed(status, now)
        return result

    def test_failures_restart_the_window(self):
        good = live(satellites=8)
        for bad in (live(satellites=7), live(mode=2), live(fresh=False, live_fix=False), live(source="manual"),
                    live(satellites=None), {"available": False}, None):
            with self.subTest(bad=bad):
                gate = FirstFixGate()
                self.assertFalse(self.run_gate(gate, 0, 199000, good))
                self.assertFalse(gate.feed(bad, 200000))
                self.assertFalse(self.run_gate(gate, 201000, 500000, good))  # Restarted at 201000.
                self.assertTrue(self.run_gate(gate, 501000, 501000, good))
        gate = FirstFixGate()
        self.run_gate(gate, 0, 199000, good)
        moved = live(satellites=8, lat=50.001)  # ~111 m: new anchor.
        self.assertFalse(self.run_gate(gate, 200000, 499000, moved))
        self.assertTrue(gate.feed(moved, 500000))

    def test_unobserved_gap_is_not_stable_time(self):
        gate = FirstFixGate()
        gate.feed(live(satellites=8), 0)
        self.assertFalse(gate.feed(live(satellites=8), 300000))  # 300 s gap: the window restarts here.
        self.assertFalse(self.run_gate(gate, 305000, 599000, live(satellites=8), step=5000))
        self.assertTrue(gate.feed(live(satellites=8), 600000))  # 5 s spacing is still continuous.

    def stable_gate(self, **changes):
        gate = FirstFixGate()
        self.assertTrue(self.run_gate(gate, 0, 300000, live(satellites=8, **changes)))
        return gate

    def test_jump_over_100_km_needs_explicit_confirmation(self):
        gate = self.stable_gate()
        self.assertTrue(gate.feed(live(lat=50.5), 301000))  # ~56 km: slow travel moves the last good fix
        self.assertTrue(gate.feed(live(lat=51.3), 302000))  # ~89 km from 50.5: still within 100 km
        far = live(lat=52.65)  # ~150 km (09-testy.md ПОЛ-13): a confirmation request
        self.assertFalse(gate.feed(far, 303000))
        self.assertTrue(gate.jump_pending)
        self.assertTrue(gate.stable)  # the first-run window itself is not repeated
        self.assertFalse(gate.feed(live(lat=51.3), 304000))  # coming back does not clear it
        self.assertFalse(gate.feed(far, 305000))
        self.assertFalse(gate.feed(live(source="manual", fresh=False, live_fix=False, lat=0.0), 306000))
        self.assertTrue(gate.confirm_jump())  # operator confirmation: the newest far fix is now last good
        self.assertFalse(gate.jump_pending)
        self.assertTrue(gate.feed(far, 307000))
        self.assertFalse(gate.confirm_jump())  # nothing pending
        self.assertFalse(gate.feed(live(lat=50.0), 308000))  # 294 km back: asks again
        # Non-live, 2D or position-less samples never raise or clear a jump request.
        gate = self.stable_gate()
        for sample in (live(lat=60.0, mode=2), live(lat=60.0, fresh=False, live_fix=False),
                       live(lat=60.0, source="last_good"), {"available": False}, None):
            with self.subTest(sample=sample):
                self.assertTrue(gate.feed(sample, 301000))
                self.assertFalse(gate.jump_pending)
        self.assertFalse(FirstFixGate().confirm_jump())

    def test_backwards_clock_latches_the_gate_closed(self):
        gate = FirstFixGate()
        gate.feed(live(satellites=8), 1000)
        self.assertFalse(gate.feed(live(satellites=8), 999))
        self.assertTrue(gate.clock_fault)
        self.assertFalse(gate.feed(live(satellites=8), 10 ** 9))
        for bad in (-1, 1.5, True, None):
            with self.assertRaises(ValueError):
                FirstFixGate().feed(live(), bad)


class SourceTests(unittest.TestCase):
    def test_module_has_no_network_city_or_third_party_import(self):
        import ast
        tree = ast.parse(Path(geo_look.__file__).read_text(encoding="utf-8"))
        names = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        names |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        self.assertEqual(names, {"math", "orbits"})


if __name__ == "__main__":
    unittest.main()
