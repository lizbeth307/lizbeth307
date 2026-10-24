"""Scope-policy tests on synthetic fixtures; no receiver, database download or field claim."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import threading
import time
import unittest
from unittest import mock
import uuid

from srrx import learning
from srrx import scope_policy as sp


def utc(day, hour, minute=0, second=0):
    return datetime(2026, 10, day, hour, minute, second, tzinfo=timezone.utc)


TUESDAY = 20  # 2026-10-20
LOG_LINE = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ out of scope")


def entry(name, categories, *ranges, **text):
    return dict(name=name, categories=list(categories), ranges_hz=[list(r) for r in ranges], **text)


def mirror(entries, **overrides):
    document = {"v": 1, "kind": "srrx_artemis_mirror", "source": "artemis-db", "db_version": "v74",
                "entries": entries}
    document.update(overrides)
    return json.dumps(document).encode("utf-8")


def admin_lstat(owner=0, file_mode=0o644, special=None):
    """lstat with root ownership; special maps a Path to (uid, mode) for refusal cases.

    Patched as scope_policy._lstat only, never the process-wide os.lstat.
    """
    real = os.lstat

    def fake(path):
        info = real(path)
        if special and Path(path) in special:
            uid, mode = special[Path(path)]
        elif stat.S_ISREG(info.st_mode):
            uid, mode = owner, stat.S_IFREG | file_mode
        elif stat.S_ISDIR(info.st_mode):
            uid, mode = 0, stat.S_IFDIR | 0o755
        else:
            uid, mode = info.st_uid, info.st_mode
        return mock.Mock(st_uid=uid, st_mode=mode, st_size=info.st_size, st_dev=info.st_dev, st_ino=info.st_ino)
    return fake


def as_root(**kwargs):
    return mock.patch.object(sp, "_lstat", side_effect=admin_lstat(**kwargs))


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def db(self, entries, name="artemis.json"):
        data = mirror(entries)
        path = self.root / name
        path.write_bytes(data)
        return sp.ArtemisDB.load(path, hashlib.sha256(data).hexdigest())

    def record(self, value, name="record.json"):
        path = self.root / name
        path.write_text(value if isinstance(value, str) else json.dumps(value))
        return path


class TdfWindowTests(Fixture):
    def status(self, moment, uncertainty=0, low=161_500.0, high=162_500.0, **kwargs):
        return sp.tdf_window_status(low, high, moment, moment, uncertainty, **kwargs)

    def test_fixture_day_is_a_tuesday(self):
        self.assertEqual(utc(TUESDAY, 0).weekday(), sp.TDF_WEEKDAY)

    def test_half_open_tuesday_window_boundaries(self):
        for moment, expected in ((utc(TUESDAY, 5, 59, 59), sp.OUT), (utc(TUESDAY, 6), sp.IN_WINDOW),
                                 (utc(TUESDAY, 11, 59, 59), sp.IN_WINDOW), (utc(TUESDAY, 12), sp.OUT)):
            with self.subTest(moment=moment):
                self.assertEqual(self.status(moment), expected)
                self.assertEqual(self.status(moment.timestamp()), expected)

    def test_other_weekdays_are_out(self):
        for day in (19, 21, 22, 23, 24, 25):
            for hour in (6, 8, 11):
                with self.subTest(day=day, hour=hour):
                    self.assertEqual(self.status(utc(day, hour)), sp.OUT)
        self.assertEqual(self.status(utc(TUESDAY, 8) + timedelta(days=7)), sp.IN_WINDOW)

    def test_unverified_utc_is_unknown_and_treated_as_in_window(self):
        self.assertEqual(self.status(utc(19, 3), None), sp.UNKNOWN_UTC)
        self.assertEqual(sp.tdf_window_status(161e3, 163e3, None, None, 30.0), sp.UNKNOWN_UTC)
        self.assertEqual(self.status(utc(19, 3), sp.clock_uncertainty_s(None)), sp.UNKNOWN_UTC)
        self.assertEqual(sp.tdf_sample_use(sp.UNKNOWN_UTC), sp.tdf_sample_use(sp.IN_WINDOW))

    def test_uncertainty_widens_both_edges(self):
        self.assertEqual(sp.clock_uncertainty_s(0), 120.0)
        self.assertAlmostEqual(sp.clock_uncertainty_s(10), 120.0 + 86.4)
        for value in (-1, float("nan"), float("inf"), True, "1"):
            with self.subTest(value=value), self.assertRaises(sp.ScopeRefused):
                sp.clock_uncertainty_s(value)
        u = sp.clock_uncertainty_s(0)
        self.assertEqual(self.status(utc(TUESDAY, 5, 58, 0), u), sp.IN_WINDOW)
        self.assertEqual(self.status(utc(TUESDAY, 5, 57, 59), u), sp.OUT)
        self.assertEqual(self.status(utc(TUESDAY, 12, 1, 59), u), sp.IN_WINDOW)
        self.assertEqual(self.status(utc(TUESDAY, 12, 2, 0), u), sp.OUT)
        self.assertEqual(self.status(utc(TUESDAY, 5, 0), sp.clock_uncertainty_s(500)), sp.IN_WINDOW)
        for value in (-0.1, float("nan"), True):
            with self.subTest(value=value), self.assertRaises(sp.ScopeRefused):
                self.status(utc(TUESDAY, 8), value)

    def test_span_without_tdf_carrier_is_unaffected(self):
        for low, high in ((77_400.0, 77_600.0), (59_900.0, 60_100.0), (163_001.0, 200_000.0), (0.0, 160_999.0)):
            with self.subTest(span=(low, high)):
                self.assertEqual(self.status(utc(TUESDAY, 8), 0, low, high), sp.OUT)
                self.assertEqual(self.status(None, None, low, high), sp.OUT)
        self.assertEqual(self.status(utc(TUESDAY, 8), 0, 150_000.0, 161_000.0), sp.IN_WINDOW)
        self.assertEqual(self.status(utc(TUESDAY, 8), 0, -163_000.0, -161_500.0), sp.IN_WINDOW)
        self.assertEqual(self.status(utc(TUESDAY, 8), 0, 0.0, 768_000.0), sp.IN_WINDOW)

    def test_intervals_and_time_inputs(self):
        self.assertEqual(sp.tdf_window_status(161e3, 163e3, utc(19, 23), utc(TUESDAY, 6, 30), 0), sp.IN_WINDOW)
        self.assertEqual(sp.tdf_window_status(161e3, 163e3, utc(TUESDAY, 12), utc(26, 5), 0), sp.OUT)
        self.assertEqual(sp.tdf_window_status(161e3, 163e3, utc(21, 13), utc(21, 13) + timedelta(days=7), 0),
                         sp.IN_WINDOW)
        naive = datetime(2026, 10, TUESDAY, 8)
        for start, end in ((naive, naive), (utc(TUESDAY, 9), utc(TUESDAY, 8)), ("2026-10-20", "x"),
                           (float("nan"), 0.0), (True, True)):
            with self.subTest(start=start), self.assertRaises(sp.ScopeRefused):
                sp.tdf_window_status(161e3, 163e3, start, end, 0)
        for low, high in ((163e3, 161e3), (True, 2.0), (float("nan"), 1.0), (0.0, 2e12)):
            with self.subTest(span=(low, high)), self.assertRaises(sp.ScopeRefused):
                sp.tdf_window_status(low, high, utc(TUESDAY, 8), utc(TUESDAY, 8), 0)

    def test_narrowing_only_from_reviewed_root_owned_record(self):
        with self.assertRaisesRegex(sp.ScopeRefused, "TDF_NARROWING_REQUIRES_REVIEWED_RECORD"):
            sp.TdfWindow(7 * 3600, 11 * 3600)
        with self.assertRaisesRegex(sp.ScopeRefused, "TDF_NARROWING_REQUIRES_REVIEWED_RECORD"):
            sp.TdfWindow(6 * 3600, 11 * 3600)
        wide = sp.DEFAULT_TDF_WINDOW.widened(5 * 3600, 13 * 3600)
        self.assertEqual(self.status(utc(TUESDAY, 5, 30), window=wide), sp.IN_WINDOW)
        with self.assertRaisesRegex(sp.ScopeRefused, "TDF_WIDENING_ONLY"):
            wide.widened(6 * 3600, 13 * 3600)
        with self.assertRaises(AttributeError):
            sp.DEFAULT_TDF_WINDOW.start_s = 7 * 3600
        record = {"v": 1, "kind": "srrx_tdf_maintenance_window", "weekday": "TUE", "start_utc": "07:00",
                  "end_utc": "11:00", "basis": "reviewed_p12_amplitude_log", "evidence_id": "p12/als162-4-tuesdays"}
        path = self.record(record)
        with as_root():
            narrow = sp.load_tdf_window(path)
        self.assertTrue(narrow.reviewed)
        self.assertEqual(narrow.evidence_id, "p12/als162-4-tuesdays")
        self.assertEqual((narrow.start_s, narrow.end_s), (7 * 3600, 11 * 3600))
        self.assertEqual(self.status(utc(TUESDAY, 6, 30), window=narrow), sp.OUT)
        self.assertEqual(self.status(utc(TUESDAY, 7, 30), window=narrow), sp.IN_WINDOW)
        self.assertEqual(self.status(utc(TUESDAY, 6, 30)), sp.IN_WINDOW)  # default untouched
        # Widening a reviewed window stays allowed; no automatic narrowing exists.
        self.assertEqual(narrow.widened(6 * 3600, 11 * 3600).start_s, 6 * 3600)
        with self.assertRaisesRegex(sp.ScopeRefused, "TDF_WIDENING_ONLY"):
            narrow.widened(8 * 3600, 11 * 3600)
        # The validated record object bounds the window: not narrower than the record itself.
        self.assertEqual(sp.TdfWindow(7 * 3600, 12 * 3600, reviewed=narrow.record).end_s, 12 * 3600)
        with self.assertRaisesRegex(sp.ScopeRefused, "TDF_NARROWING_REQUIRES_REVIEWED_RECORD"):
            sp.TdfWindow(8 * 3600, 11 * 3600, reviewed=narrow.record)
        # A public flag, a look-alike object or a hand-made record never narrows.
        for reviewed in (True, 1, "reviewed", {"start_s": 7 * 3600, "end_s": 11 * 3600}, narrow):
            with self.subTest(reviewed=reviewed), self.assertRaisesRegex(sp.ScopeRefused, "TDF_REVIEWED_RECORD_REQUIRED"):
                sp.TdfWindow(7 * 3600, 11 * 3600, reviewed=reviewed)
        with self.assertRaises(TypeError):
            sp.TdfWindow(7 * 3600, 11 * 3600, _reviewed=True)  # the old boolean keyword is gone
        for token in (object(), None, True):
            with self.subTest(token=token), self.assertRaisesRegex(sp.ScopeRefused, "TDF_REVIEWED_RECORD_REQUIRED"):
                sp.TdfReviewedRecord(token, 7 * 3600, 11 * 3600, "forged")
        with self.assertRaises(AttributeError):
            narrow.record.start_s = 8 * 3600
        for lstat, code in ((admin_lstat(owner=1000), "TRUSTED_ADMIN_RECORD_REQUIRED"),
                            (admin_lstat(file_mode=0o664), "TRUSTED_ADMIN_RECORD_REQUIRED"),
                            (admin_lstat(special={self.root: (0, stat.S_IFDIR | 0o777)}),
                             "ADMIN_OWNED_DIRECTORY_REQUIRED"),
                            (admin_lstat(special={self.root: (1000, stat.S_IFDIR | 0o755)}),
                             "ADMIN_OWNED_DIRECTORY_REQUIRED")):
            with self.subTest(code=code), mock.patch.object(sp, "_lstat", side_effect=lstat), \
                    self.assertRaisesRegex(sp.ScopeRefused, code):
                sp.load_tdf_window(path)
        with as_root(special={self.root: (0, stat.S_IFDIR | stat.S_ISVTX | 0o777)}):
            self.assertEqual(sp.load_tdf_window(path).end_s, 11 * 3600)
        for change in ({"weekday": "WED"}, {"basis": "automatic"}, {"end_utc": "06:59"},
                       {"start_utc": "7:00"}, {"evidence_id": "bad id"}, {"v": True}, {"extra": 1}):
            bad = self.record(dict(record, **change), "bad.json")
            with self.subTest(change=change), as_root(), self.assertRaises(sp.ScopeRefused):
                sp.load_tdf_window(bad)
        # A window wholly outside 06:00-12:00 is a shift, not a narrowing: refused.
        for start, end in (("13:00", "14:00"), ("00:00", "06:00"), ("12:00", "24:00")):
            shifted = self.record(dict(record, start_utc=start, end_utc=end), "shifted.json")
            with self.subTest(start=start), as_root(), \
                    self.assertRaisesRegex(sp.ScopeRefused, "TDF_RECORD_OUTSIDE_DEFAULT_WINDOW"):
                sp.load_tdf_window(shifted)
        with as_root():
            self.assertEqual(sp.load_tdf_window(self.record(dict(record, start_utc="05:00", end_utc="07:00"),
                                                            "early.json")).start_s, 5 * 3600)
        duplicate = self.record('{"v":1,"v":1}', "duplicate.json")
        with as_root(), self.assertRaisesRegex(sp.ScopeRefused, "RECORD_SCHEMA"):
            sp.load_tdf_window(duplicate)
        with self.assertRaisesRegex(sp.ScopeRefused, "ABSOLUTE_RECORD_PATH_REQUIRED"):
            sp.load_tdf_window("record.json")
        self.assertIs(sp._lstat, os.lstat)  # the module-local alias is restored after every patch

    def test_in_window_samples_are_kept_flagged_and_excluded(self):
        flagged = sp.tdf_sample_use(sp.IN_WINDOW)
        self.assertEqual(flagged, {"keep": True, "flags": ["TDF_MAINTENANCE"], "sid_baseline_allowed": False,
                                   "derived_products_allowed": False, "decoded_time_result_allowed": False})
        self.assertEqual(sp.tdf_sample_use(sp.OUT)["flags"], [])
        with self.assertRaises(sp.ScopeRefused):
            sp.tdf_sample_use("in_window")


class TimeSignalTests(unittest.TestCase):
    def test_radio_clock_decode_allowlist_and_rbu_block(self):
        for station in ("DCF77", "MSF", "TDF", "WWVB", "JJY40", "jjy 40", "JJY-40"):
            with self.subTest(station=station):
                self.assertEqual(sp.radio_clock_mode(station), "DECODE")
        self.assertEqual(sp.radio_clock_mode("JJY60"), "AMPLITUDE_ONLY")
        for station in ("RBU", "rbu"):
            with self.subTest(station=station), self.assertRaisesRegex(sp.ScopeRefused, "RBU_BLOCKED"):
                sp.radio_clock_mode(station)
        for station in ("BPC", "JJY", "PCSK-225", "", None, "X" * 40):
            with self.subTest(station=station), self.assertRaises(sp.ScopeRefused):
                sp.radio_clock_mode(station)

    def test_tdf_decoded_time_is_never_a_result_in_its_window(self):
        self.assertFalse(sp.decoded_time_usable("TDF", sp.IN_WINDOW))
        self.assertFalse(sp.decoded_time_usable("TDF", sp.UNKNOWN_UTC))
        self.assertTrue(sp.decoded_time_usable("TDF", sp.OUT))
        self.assertTrue(sp.decoded_time_usable("DCF77", sp.IN_WINDOW))
        for station in ("JJY60", "RBU", "BPC", None):
            with self.subTest(station=station):
                self.assertFalse(sp.decoded_time_usable(station, sp.OUT))

    def test_sid_targets_are_civil_lf_carriers_only(self):
        self.assertEqual(sp.sid_target("DCF77", 77_450.0, 77_550.0),
                         {"station": "DCF77", "carrier_hz": 77_500.0, "amplitude_only": True, "tdf_mask_applies": False})
        self.assertTrue(sp.sid_target("TDF", 161_900.0, 162_100.0)["tdf_mask_applies"])
        self.assertTrue(sp.sid_target("JJY60", 59_950.0, 60_050.0)["amplitude_only"])
        for args, code in ((("JJY40", 20_000.0, 45_000.0), "SID_VLF_3_30_KHZ_REFUSED"),
                           (("DCF77", 20_000.0, 80_000.0), "RBU_BLOCKED"),
                           (("MSF", 59_000.0, 67_000.0), "RBU_BLOCKED"),
                           (("RBU", 66_600.0, 66_700.0), "RBU_BLOCKED"),
                           (("NAA", 23_900.0, 24_100.0), "SID_NOT_ALLOWLISTED"),
                           (("DCF77", 60_000.0, 61_000.0), "SID_BAND_MISSES_CARRIER"),
                           (("DCF77", 77_550.0, 77_450.0), "SPAN_INVALID")):
            with self.subTest(args=args), self.assertRaisesRegex(sp.ScopeRefused, code):
                sp.sid_target(*args)


class ArtemisStopTests(Fixture):
    def assert_stop(self, decision, reason=None):
        self.assertTrue(decision["stop"])
        self.assertEqual(decision["display"], "out of scope")
        self.assertEqual(decision["identify"], "WITHHELD")
        if reason:
            self.assertIn(reason, decision["reasons"])

    def test_each_forbidden_category_stops_and_government_is_not_a_category(self):
        self.assertEqual(sp.STOP_CATEGORIES, {"Military", "Radar", "Numbers Stations"})
        self.assertNotIn("Government", sp.STOP_CATEGORIES)
        for index, category in enumerate(("Military", "Radar", "Numbers Stations", "NUMBERS-STATIONS", "radar",
                                          "Μilitary", "RАDАR")):  # Greek capital Mu; Cyrillic А
            db = self.db([entry("Fixture %d" % index, ["Utility", category], (150e6, 150.1e6))])
            with self.subTest(category=category):
                decision = sp.scope_check(150.05e6, 150.06e6, db)
                self.assert_stop(decision, "CATEGORY")
                self.assertEqual(decision["reason"], "CATEGORY")
                self.assertNotIn("Fixture", json.dumps(decision))

    def test_deny_regex_variants_stop_including_accepted_false_positives(self):
        cases = (dict(name="Fixture link-16 net"), dict(name="MIL STD 188 fixture"), dict(name="Nato fixture"),
                 dict(name="OTH radar fixture"), dict(name="Fixture", description="Link 11 data"),
                 dict(name="Fixture", modulation="ALE 4G"), dict(name="Fixture", mode="STANAG 4285"),
                 dict(name="Fixture", description="an Air-Force net"), dict(name="NАТО fixture"),  # Cyrillic А, Т, О
                 dict(name="Ｎａｖｙ fixture"), dict(name="Fixture", description="other carriers"),
                 dict(name="ΝATO fixture"), dict(name="Μilitary fixture"),  # Greek capital Nu, Mu
                 dict(name="Fixture", description="нато net"),  # Cyrillic lower-case
                 dict(name="НАТО fixture"),  # Cyrillic НАТО: transliterated, not a look-alike
                 dict(name="Fixture", mode="СТАНАГ 4285"),  # Cyrillic СТАНАГ
                 dict(name="Fixture", modulation="ΙΝΤΕLLIGENCE"))  # Greek capitals
        for index, text in enumerate(cases):
            db = self.db([dict(entry("unused", ["Utility"], (150e6, 150.1e6)), **text)], "db%d.json" % index)
            with self.subTest(text=text):
                self.assertTrue(db.available)
                decision = sp.scope_check(150e6, 150.2e6, db)
                self.assert_stop(decision, "DENY_REGEX")

    def test_look_alikes_fold_in_both_cases_before_casefold(self):
        self.assertTrue(all(len(pair) == 2 and pair[1].isascii() and pair[1].islower() for pair in sp._SHAPES))
        self.assertEqual(len(sp._TRANSLIT), 36)  # every Cyrillic letter listed has a transliteration
        for text, expected in (("ΝATO", "nato"), ("Μilitary", "military"), ("NАТО", "nato"),
                               ("НАТО", "nato"), ("нато", "nato"),
                               ("MIL-STD 188", "milstd188"), ("Ｎａｖｙ", "navy")):
            with self.subTest(text=text):
                self.assertIn(expected, sp._folds(text))
        # Shape folding keeps Cyrillic Н as H (a look-alike); NATO comes from transliteration.
        self.assertIn("hato", sp._folds("НАТО"))
        self.assertEqual(sp._folds("Broadcast FM"), {"broadcastfm"})

    def test_untagged_or_benign_entries_in_masked_bands_stop(self):
        db = self.db([entry("Fixture untagged", [], (300e6, 300.025e6))])
        decision = sp.scope_check(299.99e6, 300.01e6, db)
        self.assert_stop(decision, "UNTAGGED_MASKED")
        self.assertIn("MASKED_BAND", decision["reasons"])
        benign = self.db([entry("Fixture benign", ["Amateur"], (300e6, 300.025e6))], "benign.json")
        decision = sp.scope_check(300e6, 300.01e6, benign)
        self.assert_stop(decision, "MASKED_BAND")
        self.assertEqual(decision["reasons"], ["MASKED_BAND"])
        # Span outside the mask, untagged entry reaching into it: fail closed.
        straddle = self.db([entry("Fixture edge", [""], (224.9e6, 225.1e6))], "edge.json")
        decision = sp.scope_check(224.90e6, 224.95e6, straddle)
        self.assertEqual(decision["reasons"], ["UNTAGGED_MASKED"])
        tagged = self.db([entry("Fixture edge", ["Amateur"], (224.9e6, 225.1e6))], "tagged.json")
        self.assertFalse(sp.scope_check(224.90e6, 224.95e6, tagged)["stop"])

    def test_masked_bands_are_the_union_and_include_mirrored_frequencies(self):
        self.assertEqual(sp.MASKED_BANDS_HZ, ((3e3, 30e3), (225e6, 400e6), (406e6, 406.1e6), (1530e6, 1660e6)))
        for low, high in ((3e3, 3e3), (29e3, 31e3), (399e6, 401e6), (406.05e6, 406.06e6), (405.9e6, 406.2e6),
                          (1544.5e6, 1544.6e6), (1530e6, 1530e6), (-300e6, -299e6), (-406.05e6, -406.04e6), (-20e3, 1e3)):
            with self.subTest(span=(low, high)):
                self.assert_stop(sp.scope_check(low, high), "MASKED_BAND")
        for low, high in ((31e3, 224.99e6), (400.001e6, 405.99e6), (406.11e6, 1529.9e6), (1660.1e6, 2e9)):
            with self.subTest(span=(low, high)):
                self.assertFalse(sp.scope_check(low, high)["stop"])

    def test_stack_bands_alone_stop_the_cospas_sarsat_uplink(self):
        # The STACK copy carries 406.0-406.1 MHz itself, so a scope stop never depends on spectrum.py alone.
        self.assertEqual(sp.STACK_MASKED_BANDS_HZ, ((3e3, 30e3), (225e6, 400e6), (406e6, 406.1e6), (1544e6, 1545e6)))
        with mock.patch.object(sp, "MASKED_BANDS_HZ", sp._union(sp.STACK_MASKED_BANDS_HZ)):
            for low, high in ((406.05e6, 406.06e6), (405.95e6, 406.0e6), (406.1e6, 406.2e6), (-406.05e6, -406.04e6)):
                with self.subTest(span=(low, high)):
                    self.assert_stop(sp.scope_check(low, high), "MASKED_BAND")
            self.assertFalse(sp.scope_check(400.5e6, 405.9e6)["stop"])  # radiosonde scan up to 405.9 MHz (STACK.md:600)

    def test_trunked_radio_is_anonymous_occupancy_only(self):
        db = self.db([entry("Fixture trunk system", ["Trunked Radio"], (160e6, 160.5e6),
                            description="Fixture operator text")])
        decision = sp.scope_check(160.1e6, 160.2e6, db)
        self.assertFalse(decision["stop"])
        self.assertEqual(decision["display"], [{"occupancy": "anonymous"}])
        self.assertNotIn("Fixture", json.dumps(decision))

    def test_benign_match_or_no_match_never_claims_in_scope(self):
        db = self.db([entry("Fixture broadcast", ["Broadcast", "Analogue"], (100e6, 100.2e6)),
                      entry("Fixture beacon", ["Amateur"], (144.4e6, 144.5e6))])
        decision = sp.scope_check(100.1e6, 100.15e6, db)
        self.assertEqual(decision, {"stop": False, "reason": "NONE", "reasons": [], "identify": "MATCHED",
                                    "display": [{"name": "Fixture broadcast", "categories": ["Broadcast", "Analogue"]}]})
        self.assertEqual(sp.scope_check(120e6, 121e6, db)["identify"], "NO_MATCH")
        self.assertEqual(sp.scope_check(100.2e6, 144.4e6, db)["identify"], "MATCHED")  # edge contact counts
        for value in (decision, sp.scope_check(120e6, 121e6, db), sp.scope_check(120e6, 121e6)):
            self.assertNotIn("in scope", json.dumps(value).lower())
        decision["display"][0]["categories"].append("Military")
        self.assertEqual(sp.scope_check(100.1e6, 100.15e6, db)["display"][0]["categories"], ["Broadcast", "Analogue"])

    def test_missing_or_mismatched_database_is_unavailable_and_masked_stop_still_applies(self):
        data = mirror([entry("Fixture", ["Military"], (150e6, 150.1e6))])
        path = self.root / "artemis.json"
        path.write_bytes(data)
        for db, status in ((sp.ArtemisDB.load(path, "0" * 64), "UNAVAILABLE_SHA256_MISMATCH"),
                           (sp.ArtemisDB.load(self.root / "missing.json", "0" * 64), "UNAVAILABLE_MISSING"),
                           (sp.ArtemisDB.load(path, "A" * 64), "UNAVAILABLE_NO_ACCEPTED_SHA256"),
                           (sp.ArtemisDB.load(path, None), "UNAVAILABLE_NO_ACCEPTED_SHA256")):
            with self.subTest(status=status):
                self.assertEqual(db.status, status)
                self.assertFalse(db.available)
                decision = sp.scope_check(150e6, 150.2e6, db)
                self.assertFalse(decision["stop"])  # nothing identified: not a claim of "in scope"
                self.assertEqual((decision["identify"], decision["display"]), ("UNAVAILABLE", []))
                self.assert_stop(sp.scope_check(300e6, 300.1e6, db), "MASKED_BAND")
        self.assertEqual(sp.scope_check(150e6, 150.2e6)["identify"], "UNAVAILABLE")
        with self.assertRaisesRegex(sp.ScopeRefused, "ARTEMIS_DB_REQUIRED"):
            sp.scope_check(150e6, 150.2e6, {"entries": []})

    def test_format_detection_and_strict_schema(self):
        self.assertEqual(sp.detect_format(sp.SQLITE_MAGIC + bytes(84)), "sqlite3")
        self.assertEqual(sp.detect_format(b"{}"), sp.ARTEMIS_FORMAT)
        self.assertEqual(sp.detect_format(b"PK\x03\x04"), "unknown")
        cases = {"sqlite": (sp.SQLITE_MAGIC + bytes(84), "UNAVAILABLE_FORMAT_UNVERIFIED_SQLITE"),
                 "zip": (b"PK\x03\x04" + bytes(20), "UNAVAILABLE_FORMAT_UNKNOWN"),
                 "version": (mirror([], db_version="v73"), "UNAVAILABLE_SCHEMA"),
                 "kind": (mirror([], kind="artemis"), "UNAVAILABLE_SCHEMA"),
                 "extra": (mirror([], url="https://example.invalid"), "UNAVAILABLE_SCHEMA"),
                 "nan": (b'{"v":1,"kind":"srrx_artemis_mirror","source":"artemis-db","db_version":"v74",'
                         b'"entries":[{"name":"a","categories":[],"ranges_hz":[[NaN,1]]}]}', "UNAVAILABLE_SCHEMA"),
                 "duplicate": (b'{"v":1,"v":1}', "UNAVAILABLE_SCHEMA"),
                 "utf8": (b'{"v":"\xff"}', "UNAVAILABLE_SCHEMA")}
        bad_entries = (dict(entry("a", [], (1, 2)), url="x"), {"name": "a", "categories": []},
                       entry("", [], (1, 2)), entry("a", [3], (1, 2)), entry("a", [], (2, 1)), entry("a", [], (-1, 2)),
                       entry("a", [], (True, 2)), entry("a", []), dict(entry("a", [], (1, 2)), ranges_hz=[[1, 2, 3]]),
                       entry("a" * 300, [], (1, 2)), entry("a", [], *[(1, 2)] * 33), entry("a", [], (1, 2e12)))
        for index, value in enumerate(bad_entries):
            cases["entry%d" % index] = (mirror([value]), "UNAVAILABLE_SCHEMA")
        for name, (data, status) in cases.items():
            path = self.root / (name + ".bin")
            path.write_bytes(data)
            with self.subTest(case=name):
                self.assertEqual(sp.ArtemisDB.load(path, hashlib.sha256(data).hexdigest()).status, status)
        with mock.patch.object(sp.ArtemisDB, "MAX_BYTES", 16):
            data = mirror([])
            path = self.root / "large.json"
            path.write_bytes(data)
            self.assertEqual(sp.ArtemisDB.load(path, hashlib.sha256(data).hexdigest()).status, "UNAVAILABLE_SIZE_LIMIT")
        with mock.patch.object(sp.ArtemisDB, "MAX_ENTRIES", 1):
            self.assertEqual(self.db([entry("a", [], (1, 2))] * 2).status, "UNAVAILABLE_SCHEMA")
        good = self.db([entry("a", ["Amateur"], (1, 2), description="d", location="l")])
        self.assertEqual((good.status, len(good)), ("AVAILABLE", 1))

    def test_acceptance_record_binds_the_locally_computed_sha256(self):
        data = mirror([entry("Fixture", ["Military"], (150e6, 150.1e6))])
        path = self.root / "artemis.json"
        path.write_bytes(data)
        record = {"v": 1, "kind": "srrx_artemis_acceptance", "db": "artemis-db", "db_version": "v74",
                  "format": sp.ARTEMIS_FORMAT, "sha256": hashlib.sha256(data).hexdigest(),
                  "evidence_id": "admin/artemis-db-v74-mirror-001"}
        accepted = self.record(record)
        with as_root():
            db = sp.ArtemisDB.load_accepted(path, accepted)
        self.assertTrue(db.available)
        self.assert_stop(sp.scope_check(150e6, 150.2e6, db), "CATEGORY")
        with as_root(owner=1000):
            self.assertEqual(sp.ArtemisDB.load_accepted(path, accepted).status, "UNAVAILABLE_NO_ACCEPTANCE_RECORD")
        for change in ({"db_version": "v73"}, {"format": "sqlite3"}, {"sha256": "x"}, {"extra": True}):
            bad = self.record(dict(record, **change), "bad.json")
            with self.subTest(change=change), as_root():
                self.assertFalse(sp.ArtemisDB.load_accepted(path, bad).available)
        path.write_bytes(data + b" ")
        with as_root():
            self.assertEqual(sp.ArtemisDB.load_accepted(path, accepted).status, "UNAVAILABLE_SHA256_MISMATCH")
        # A record that is not a regular file (here a directory) is never read.
        folder = self.root / "record-dir"
        folder.mkdir()
        with as_root(special={folder: (0, stat.S_IFDIR | 0o755)}):
            self.assertEqual(sp.ArtemisDB.load_accepted(path, folder).status, "UNAVAILABLE_NO_ACCEPTANCE_RECORD")

    def test_database_path_must_be_a_regular_file_and_is_read_without_blocking(self):
        data = mirror([entry("Fixture", ["Military"], (150e6, 150.1e6))])
        digest = hashlib.sha256(data).hexdigest()
        path = self.root / "artemis.json"
        path.write_bytes(data)
        self.assertTrue(sp.ArtemisDB.load(path, digest).available)
        self.assertEqual(sp.ArtemisDB.load(self.root, digest).status, "UNAVAILABLE_NOT_REGULAR_FILE")
        special = []
        if hasattr(os, "mkfifo"):  # POSIX: a FIFO would block a plain open()/read() forever
            fifo = self.root / "artemis.fifo"
            os.mkfifo(fifo)
            special.append(fifo)
        if os.path.exists("/dev/null"):
            special.append(Path("/dev/null"))
        try:
            link = self.root / "artemis-link.json"
            os.symlink(path, link)
            special.append(link)  # a final symlink is refused, even to the accepted bytes
        except (OSError, NotImplementedError):
            pass  # Windows without the symlink privilege; the directory case above still runs
        for candidate in special:
            with self.subTest(path=str(candidate)):
                started = time.monotonic()
                self.assertEqual(sp.ArtemisDB.load(candidate, digest).status, "UNAVAILABLE_NOT_REGULAR_FILE")
                self.assertLess(time.monotonic() - started, 5)
        # A file swapped between lstat and open (another inode) is not read either.
        real = os.lstat(path)
        swapped = mock.Mock(st_mode=real.st_mode, st_dev=real.st_dev, st_ino=real.st_ino + 1, st_size=real.st_size)
        with mock.patch.object(sp, "_lstat", return_value=swapped):
            self.assertEqual(sp.ArtemisDB.load(path, digest).status, "UNAVAILABLE_NOT_REGULAR_FILE")
        with mock.patch.object(sp, "_lstat", side_effect=PermissionError("denied")):
            self.assertEqual(sp.ArtemisDB.load(path, digest).status, "UNAVAILABLE_MISSING")
        for value in (None, 3.5, "bad\0path"):
            with self.subTest(value=value):
                self.assertEqual(sp.ArtemisDB.load(value, digest).status, "UNAVAILABLE_MISSING")
        self.assertIs(sp._lstat, os.lstat)

    def test_stop_log_line_is_utc_and_out_of_scope_only(self):
        self.assertEqual(sp.stop_log_line(utc(TUESDAY, 8, 1, 2)), "2026-10-20T08:01:02Z out of scope")
        self.assertEqual(sp.stop_log_line(utc(TUESDAY, 8).timestamp() + .9), "2026-10-20T08:00:00Z out of scope")
        offset = datetime(2026, 10, TUESDAY, 10, tzinfo=timezone(timedelta(hours=2)))
        self.assertEqual(sp.stop_log_line(offset), "2026-10-20T08:00:00Z out of scope")
        for value in (datetime(2026, 10, TUESDAY, 8), "2026-10-20", None, float("nan"), True):
            with self.subTest(value=value), self.assertRaises(sp.ScopeRefused):
                sp.stop_log_line(value)

    def test_invalid_spans_are_refused(self):
        for low, high in ((2.0, 1.0), (True, 2.0), (float("nan"), 1.0), (1.0, float("inf")), ("1", 2.0), (0.0, 2e12)):
            with self.subTest(span=(low, high)), self.assertRaisesRegex(sp.ScopeRefused, "SPAN_INVALID"):
                sp.scope_check(low, high)


class ScopeLatchTests(Fixture):
    def setUp(self):
        super().setUp()
        self.military = self.db([entry("Fixture station", ["Military"], (150e6, 150.1e6)),
                                 entry("Fixture broadcast", ["Broadcast"], (160e6, 160.2e6))])
        self.latch = sp.ScopeLatch(self.military, clock=lambda: utc(TUESDAY, 8).timestamp())

    def test_latch_blocks_mark_record_label_decode_export_until_retune_away(self):
        self.assertTrue(all(self.latch.permits(op, (149.0e6, 149.5e6)) for op in sp.ScopeLatch.OPERATIONS))
        decision = self.latch.retune(149e6, 151e6)
        self.assertTrue(decision["stop"])
        self.assertEqual(decision["display"], "out of scope")
        self.assertTrue(self.latch.stopped)
        for op in ("mark", "record", "label", "decode", "export"):
            with self.subTest(op=op):
                # The box itself holds no stop entry, but its tuned span latched.
                self.assertFalse(self.latch.permits(op, (149.0e6, 149.5e6)))
                self.assertTrue(self.latch.permits(op, (160.0e6, 160.1e6)))
        self.assertEqual(self.latch.observe(149.0e6, 149.5e6)["reason"], "LATCHED")
        self.assertTrue(self.latch.retune(150.5e6, 152e6)["stop"])  # still touches the latched span
        self.assertFalse(self.latch.permits("record", (149.0e6, 149.5e6)))
        self.assertFalse(self.latch.retune(159e6, 161e6)["stop"])  # away: latch released
        self.assertFalse(self.latch.stopped)
        self.assertTrue(self.latch.permits("record", (149.0e6, 149.5e6)))
        self.assertTrue(self.latch.retune(149e6, 151e6)["stop"])  # back again: stops again

    def test_unknown_operations_and_invalid_spans_are_not_permitted(self):
        for op in ("play", "MARK", None, "transmit", ["record"], {}):
            with self.subTest(op=op):
                self.assertFalse(self.latch.permits(op, (160.0e6, 160.1e6)))
        for span in ((2.0, 1.0), (1.0,), None, "ab", (float("nan"), 1.0)):
            with self.subTest(span=span):
                self.assertFalse(self.latch.permits("record", span))
        self.assertFalse(self.latch.permits("record", (300e6, 301e6)))  # masked band latches too
        self.assertTrue(self.latch.stopped)
        with self.assertRaisesRegex(sp.ScopeRefused, "ARTEMIS_DB_REQUIRED"):
            sp.ScopeLatch(db=object())

    def test_new_stop_aborts_recordings_and_logs_without_frequency(self):
        aborted = []
        self.latch.register_abort(lambda: aborted.append(True))
        self.latch.observe(150.0e6, 150.05e6)
        self.latch.observe(150.01e6, 150.02e6)  # inside the latch: no second event
        self.assertEqual(aborted, [True])
        self.latch.stop(170e6, 171e6)  # operator stop only adds a latch
        self.assertEqual(len(aborted), 2)
        lines = self.latch.drain_log()
        self.assertEqual(lines, ["2026-10-20T08:00:00Z out of scope"] * 2)
        for line in lines:
            self.assertRegex(line, LOG_LINE)
            for forbidden in ("150", "170", "MHz", "Hz", "lat", "lon", "Fixture", "Military", "bearing"):
                self.assertNotIn(forbidden, line)
        self.assertEqual(self.latch.drain_log(), [])
        self.latch.register_abort(mock.Mock(side_effect=RuntimeError("abort failed")))
        with self.assertRaisesRegex(sp.ScopeRefused, "ABORT_CALLBACK_FAILED"):
            self.latch.observe(300e6, 300.1e6)
        self.assertFalse(self.latch.permits("record", (300e6, 300.1e6)))
        for callback in (None, "x"):
            with self.subTest(callback=callback), self.assertRaises(sp.ScopeRefused):
                self.latch.register_abort(callback)

    def test_latch_memory_is_bounded_by_merging_into_a_hull(self):
        latch = sp.ScopeLatch(clock=lambda: utc(TUESDAY, 8).timestamp())
        for index in range(sp.ScopeLatch.MAX_LATCHES + 1):
            latch.stop(100e6 + index * 1e6, 100e6 + index * 1e6 + 1e3)
        self.assertEqual(len(latch._latched), 1)
        self.assertFalse(latch.permits("record", (100.5e6, 100.6e6)))  # between former latches: fail closed
        # 65 stops, 64 journal slots: the overflow is reported, never silently lost.
        self.assertEqual(latch.log_dropped, 1)
        lines = latch.drain_log()
        self.assertEqual(len(lines), sp.ScopeLatch.MAX_LOG_LINES)
        self.assertEqual(lines[0], "2026-10-20T08:00:00Z out of scope (1 earlier lines dropped)")
        self.assertEqual(set(lines[1:]), {"2026-10-20T08:00:00Z out of scope"})
        self.assertEqual((latch.log_dropped, latch.drain_log()), (0, []))
        for index in range(200):  # each new stop elsewhere also adds a line
            latch.retune(3e9 + index * 1e6, 3e9 + index * 1e6 + 1e3)
            latch.stop(3e9 + index * 1e6, 3e9 + index * 1e6 + 1e3)
        lines = latch.drain_log()
        self.assertEqual(len(lines), 64)
        self.assertTrue(lines[0].endswith(" out of scope (136 earlier lines dropped)"))
        for line in lines:  # UTC, "out of scope" and at most the drop count: no frequency or entry text
            self.assertRegex(line, r"\A\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ out of scope(?: \(\d+ earlier lines dropped\))?\Z")

    def test_abort_callbacks_are_unregistered_when_a_recording_ends(self):
        calls = []
        for index in range(3 * sp.ScopeLatch.MAX_CALLBACKS):  # far more recordings than live slots
            token = self.latch.register_abort(lambda index=index: calls.append(index))
            self.assertTrue(self.latch.unregister_abort(token))
            self.assertFalse(self.latch.unregister_abort(token))  # a second end is a no-op
        live = self.latch.register_abort(lambda: calls.append("live"))
        self.latch.observe(150.0e6, 150.05e6)
        self.assertEqual(calls, ["live"])  # finished recordings never abort again
        tokens = [self.latch.register_abort(lambda: None) for _ in range(sp.ScopeLatch.MAX_CALLBACKS - 1)]
        with self.assertRaisesRegex(sp.ScopeRefused, "ABORT_CALLBACK_LIMIT"):
            self.latch.register_abort(lambda: None)
        self.assertTrue(self.latch.unregister_abort(tokens.pop()))
        tokens.append(self.latch.register_abort(lambda: None))  # a freed slot is reusable
        for value in (None, "token", object(), [1]):
            with self.subTest(value=value):
                self.assertFalse(self.latch.unregister_abort(value))
        self.assertTrue(self.latch.unregister_abort(live))

    def test_latch_blocks_learning_annotation(self):
        frame = learning._demo_frame(1, 0)  # 137.0-138.0 MHz synthetic shape
        db = self.db([entry("Fixture", ["Radar"], (137.4e6, 137.6e6))], "radar.json")
        latch = sp.ScopeLatch(db)
        with self.assertRaisesRegex(learning.LearningError, "out of scope") as caught:
            learning.annotate(learning.empty_dataset(), frame, 0, 256, "analog_broadcast",
                              group_id=uuid.UUID(int=1), user_confirmed=True, scope=latch)
        self.assertNotRegex(str(caught.exception), r"\d")
        self.assertTrue(latch.stopped)
        benign = sp.ScopeLatch(self.db([entry("Fixture", ["Broadcast"], (137.4e6, 137.6e6))], "benign.json"))
        result = learning.annotate(learning.empty_dataset(), frame, 0, 256, "analog_broadcast",
                                   group_id=uuid.UUID(int=1), user_confirmed=True, scope=benign)
        self.assertEqual(len(result["annotations"]), 1)

    def test_detached_copy_blocks_the_same_spans_and_stops_on_the_same_database(self):
        self.assertTrue(self.latch.retune(149e6, 151e6)["stop"])
        copy = self.latch.detached_copy()
        self.assertIsInstance(copy, sp.ScopeLatch)
        self.assertEqual(copy.base_generation, self.latch.latch_generation)
        self.assertFalse(copy.permits("label", (149.0e6, 149.5e6)))  # latched in the original
        self.assertTrue(copy.permits("label", (160.0e6, 160.1e6)))
        self.assertFalse(copy.permits("label", (300e6, 301e6)))  # masked band, no database needed
        self.latch.retune(170e6, 171e6)  # releases the original only
        self.assertFalse(copy.permits("label", (149.0e6, 149.5e6)))
        self.assertTrue(self.latch.permits("label", (149.0e6, 149.5e6)))

    def test_stop_in_a_copy_aborts_and_journals_only_at_adopt_on_the_calling_thread(self):
        calls = []
        self.latch.register_abort(lambda: calls.append(threading.get_ident()))
        copy = self.latch.detached_copy()
        found = []
        job = threading.Thread(target=lambda: found.append(copy.permits("label", (150.0e6, 150.05e6))))
        job.start(); job.join(5)
        self.assertEqual(found, [False])  # Artemis stop on the job thread
        self.assertEqual((calls, self.latch.drain_log(), self.latch.stopped), ([], [], False))
        self.assertTrue(self.latch.adopt(copy))
        self.assertEqual(calls, [threading.get_ident()])  # once, on the owner thread
        self.assertEqual(self.latch.drain_log(), ["2026-10-20T08:00:00Z out of scope"])
        self.assertFalse(self.latch.permits("record", (150.0e6, 150.05e6)))
        self.assertFalse(self.latch.adopt(copy))  # a second adopt adds nothing (and the copy is stale)
        self.assertEqual((len(calls), self.latch.drain_log()), (1, []))

    def test_adopt_reports_a_latch_added_meanwhile_but_not_a_release(self):
        self.latch.retune(149e6, 151e6)
        copy = self.latch.detached_copy()
        self.latch.retune(159e6, 161e6)  # release only: a result computed against the copy stays fail-closed
        self.assertTrue(self.latch.adopt(copy))
        copy = self.latch.detached_copy()
        self.latch.stop(170e6, 171e6)
        self.assertFalse(self.latch.adopt(copy))
        copy = self.latch.detached_copy()
        self.latch.stop(170.2e6, 170.3e6)  # inside an existing latch: nothing new
        self.assertTrue(self.latch.adopt(copy))

    def test_adopt_accepts_only_its_own_copy_and_a_copy_registers_no_abort(self):
        other = sp.ScopeLatch(self.military)
        copy = self.latch.detached_copy()
        for value in (other.detached_copy(), other, self.latch, None, object()):
            with self.subTest(value=type(value).__name__), self.assertRaisesRegex(sp.ScopeRefused, "DETACHED_COPY_INVALID"):
                self.latch.adopt(value)
        with self.assertRaisesRegex(sp.ScopeRefused, "DETACHED_COPY"):
            copy.register_abort(lambda: None)
        with self.assertRaisesRegex(sp.ScopeRefused, "DETACHED_COPY"):
            copy.detached_copy()

    def test_hull_merged_copy_is_adopted_and_failed_aborts_still_latch_every_stop(self):
        copy = self.latch.detached_copy()
        for index in range(sp.ScopeLatch.MAX_LATCHES + 1):
            copy.stop(500e6 + index * 1e6, 500e6 + index * 1e6 + 1e3)
        self.assertEqual(len(copy._latched), 1)  # the copy merged into one hull
        aborted = []
        self.latch.register_abort(mock.Mock(side_effect=RuntimeError("abort failed")))
        self.latch.register_abort(lambda: aborted.append(True))
        with self.assertRaisesRegex(sp.ScopeRefused, "ABORT_CALLBACK_FAILED"):
            self.latch.adopt(copy)
        self.assertEqual(len(aborted), sp.ScopeLatch.MAX_LATCHES + 1)
        for index in (0, sp.ScopeLatch.MAX_LATCHES):
            self.assertFalse(self.latch.permits("record", (500e6 + index * 1e6, 500e6 + index * 1e6 + 1e3)))
        self.assertFalse(self.latch.permits("record", (500.5e6, 500.6e6)))  # the original merged too
        self.assertEqual(len(self.latch.drain_log()), sp.ScopeLatch.MAX_LOG_LINES)

    def test_training_accepts_a_detached_copy_as_the_session_latch(self):
        frame = learning._demo_frame(1, 0)
        dataset = learning.empty_dataset()
        for family, label in enumerate(("analog_broadcast", "digital_broadcast")):
            for index in range(2):
                dataset = learning.annotate(dataset, learning._demo_frame(index, family), 0, 256, label,
                                            group_id=uuid.UUID(int=1 + family * 100 + index), user_confirmed=True)
        copy = sp.ScopeLatch(self.military).detached_copy()
        self.assertEqual(learning.train(dataset, seed=7, scope=copy)["labels"], ["analog_broadcast", "digital_broadcast"])
        self.assertEqual(len(learning.annotate(learning.empty_dataset(), frame, 0, 256, "analog_broadcast",
                                               group_id=uuid.UUID(int=1), user_confirmed=True, scope=copy)["annotations"]), 1)


if __name__ == "__main__":
    unittest.main()
