"""Strict local OMM ingestion, allowlist, ages, stationarity and SatDump CSV export.

All element sets are synthetic objects with synthetic catalogue numbers; no
element set is fetched and no real target list is implied.
"""
import ast
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from srrx import orbits
from srrx.orbits import OMM_FIELDS, OrbitError, export_satdump_csv, is_stationary, load_omm, parse_omm, satdump_csv

EPOCH = "2026-10-20T06:00:00.123456"
EPOCH_S = orbits.epoch_unix_s(EPOCH)
DAY = 86400.0


def raw(norad=90010, **changes):
    value = {"OBJECT_NAME": "SYNTHETIC LEO %d" % norad, "OBJECT_ID": "2026-901A", "EPOCH": EPOCH,
             "MEAN_MOTION": 14.2412, "ECCENTRICITY": 0.00071, "INCLINATION": 98.71, "RA_OF_ASC_NODE": 120.5,
             "ARG_OF_PERICENTER": 87.25, "MEAN_ANOMALY": 272.9, "EPHEMERIS_TYPE": 0, "CLASSIFICATION_TYPE": "U",
             "NORAD_CAT_ID": norad, "ELEMENT_SET_NO": 999, "REV_AT_EPOCH": 1234, "BSTAR": 0.00012,
             "MEAN_MOTION_DOT": 1.2e-06, "MEAN_MOTION_DDOT": 0.0}
    value.update(changes)
    return value


def allow(*entries):
    return orbits.allowlist({"schema_version": 1, "kind": "srrx_orbit_allowlist",
                             "targets": [{"norad_id": n, "name": "ALIAS %d" % n, "role": r} for n, r in entries]})


def csv_text(rows, header=OMM_FIELDS):
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(str(row[field]) for field in header))
    return ("\n".join(lines) + "\n").encode("ascii")


class OrbitTestCase(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def write(self, name, data):
        path = self.root / name
        path.write_bytes(data if isinstance(data, bytes) else json.dumps(data).encode())
        return path

    def load(self, data, targets=None, now=EPOCH_S + DAY, verified=True):
        targets = allow((90010, "LRPT"), (90011, "ISS")) if targets is None else targets
        return load_omm(self.write("omm.json", data), allow_norad=targets, now_utc_s=now, utc_verified=verified)


class IngestTests(OrbitTestCase):
    def test_json_and_csv_round_trip_through_satdump_export(self):
        records = self.load([raw(90010), raw(90011, MEAN_MOTION=15.5), raw(90012)])
        self.assertEqual([r["norad_id"] for r in records], [90010, 90011])  # 90012 is not allowlisted.
        self.assertEqual(records[0]["name"], "ALIAS 90010")
        self.assertEqual(records[0]["elements"]["OBJECT_NAME"], "SYNTHETIC LEO 90010")
        self.assertEqual(records[0]["epoch_utc"], EPOCH + "Z")
        exported = satdump_csv(records)
        self.assertEqual(exported.splitlines()[0].decode(), ",".join(OMM_FIELDS))
        self.assertEqual(len(exported.splitlines()[1].decode().split(",")), 17)
        normal, kind = parse_omm(exported)
        self.assertEqual(kind, "csv")
        self.assertEqual(normal, [r["elements"] for r in records])
        again = load_omm(self.write("omm.csv", exported), allow_norad=allow((90010, "LRPT"), (90011, "ISS")),
                         now_utc_s=EPOCH_S + DAY, utc_verified=True)
        self.assertEqual(again, records)

    def test_csv_header_order_is_by_name_and_shape_is_strict(self):
        header = tuple(reversed(OMM_FIELDS))
        normal, kind = parse_omm(csv_text([raw()], header))
        self.assertEqual(normal[0]["NORAD_CAT_ID"], 90010)
        bad = [csv_text([raw()], OMM_FIELDS[:-1]), csv_text([raw()], OMM_FIELDS[:-1] + ("OBJECT_NAME",)),
               csv_text([raw()]).replace(b",0.0\n", b",0.0,9\n"), csv_text([raw(MEAN_MOTION="nan")]),
               csv_text([raw(MEAN_MOTION="1e999")]), csv_text([raw(NORAD_CAT_ID="9e4")]),
               "﻿".encode() + csv_text([raw()]), csv_text([raw()]).replace(b"SYNTHETIC", "SYNTHÉTIC".encode()),
               b"garbage"]
        for data in bad:
            with self.subTest(data=data[:60]), self.assertRaises(OrbitError):
                parse_omm(data)

    def test_duplicate_keys_nonfinite_and_structure_are_rejected(self):
        good = json.dumps([raw()])
        cases = [good.replace('"BSTAR": 0.00012', '"BSTAR": 0.00012, "BSTAR": 0.0'),
                 good.replace("0.00012", "NaN"), good.replace("0.00012", "Infinity"), good.replace("0.00012", "1e400"),
                 good.replace('"NORAD_CAT_ID": 90010', '"NORAD_CAT_ID": true'),
                 good.replace('"NORAD_CAT_ID": 90010', '"NORAD_CAT_ID": 90010.0'),
                 good.replace('"EPHEMERIS_TYPE": 0', '"EPHEMERIS_TYPE": 2'),
                 good.replace('"CLASSIFICATION_TYPE": "U"', '"CLASSIFICATION_TYPE": "C"'),
                 good.replace('"OBJECT_ID": "2026-901A"', '"OBJECT_ID": "26901A"'),
                 good.replace('"ECCENTRICITY": 0.00071', '"ECCENTRICITY": 1.0'),
                 good.replace('"INCLINATION": 98.71', '"INCLINATION": 181'),
                 good.replace('"MEAN_MOTION": 14.2412', '"MEAN_MOTION": 0'),
                 good.replace('"MEAN_MOTION_DDOT": 0.0}', '"MEAN_MOTION_DDOT": 0.0, "EXTRA": 1}'),
                 good.replace(', "MEAN_MOTION_DDOT": 0.0', ''), json.dumps(raw()), "[" * 100000, "[]x", "{}"]
        for epoch in ("2026-13-01T00:00:00", "2026-10-20 00:00:00", "2026-10-20T00:00:60", "2026-10-20T00:00:00Z",
                      "1950-01-01T00:00:00", "2026-10-20T00:00:00.1234567", "٢٠٢٦-10-20T00:00:00"):
            cases.append(json.dumps([raw(EPOCH=epoch)]))
        cases.append(json.dumps([raw(OBJECT_NAME="BAD\nNAME")]))
        cases.append(json.dumps([raw(MEAN_MOTION="١٤.2")]))  # Non-ASCII digits are not plain decimals.
        for text in cases:
            with self.subTest(text=text[:80]), self.assertRaises(OrbitError):
                parse_omm(text.encode())
        self.assertEqual(parse_omm(json.dumps([raw(EPOCH="2026-10-20T06:00:00")]).encode())[0][0]["EPOCH"],
                         "2026-10-20T06:00:00.000000")
        self.assertEqual(parse_omm(json.dumps([raw(MEAN_MOTION="14.2412")]).encode())[0][0]["MEAN_MOTION"], 14.2412)

    def test_size_limit_applies_before_parsing(self):
        path = self.write("big.json", b"[" + b" " * orbits.MAX_OMM_BYTES + b"]")
        with self.assertRaises(OrbitError):
            load_omm(path, allow_norad={90010}, now_utc_s=EPOCH_S, utc_verified=True)
        with self.assertRaises(OrbitError):
            parse_omm(b" " * (orbits.MAX_OMM_BYTES + 1))

    def test_allowlist_and_six_digit_ids(self):
        records = self.load([raw(270001), raw(90010)], allow((270001, "OTHER")))
        self.assertEqual([r["norad_id"] for r in records], [270001])
        self.assertEqual(self.load([raw(999999)], allow((999999, "OTHER")))[0]["norad_id"], 999999)
        for bad in (0, 1000000):
            with self.assertRaises(OrbitError):
                parse_omm(json.dumps([raw(bad)]).encode())
        self.assertEqual(self.load([raw(90010)], allow((90011, "ISS"))), [])
        self.assertEqual([r["norad_id"] for r in self.load([raw(90010)], {90010})], [90010])
        for bad in ("90010", 90010, {"90010": {}}, {90010: {"norad_id": 90011, "name": "X", "role": "OTHER"}}, [True]):
            with self.subTest(bad=bad), self.assertRaises(OrbitError):
                self.load([raw()], bad)
        with self.assertRaises(OrbitError):
            load_omm(self.write("x.json", [raw()]), allow_norad=None, now_utc_s=EPOCH_S, utc_verified=True)

    def test_one_record_per_norad_newest_epoch_wins(self):
        newer = raw(EPOCH="2026-10-21T06:00:00.000000", MEAN_MOTION=14.2413)
        records = self.load([raw(), newer, raw()], now=EPOCH_S + 2 * DAY)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["elements"]["EPOCH"], "2026-10-21T06:00:00.000000")
        with self.assertRaises(OrbitError):  # Same epoch, different elements: contradictory.
            self.load([raw(), raw(MEAN_MOTION=14.25)])
        with self.assertRaises(OrbitError):  # Even when a newer set supersedes both.
            self.load([raw(), newer, raw(INCLINATION=98.8)])


class AgeAndStationarityTests(OrbitTestCase):
    def test_age_warnings_are_warnings_never_refusals(self):
        targets = allow((90010, "LRPT"), (90011, "ISS"))
        data = [raw(90010), raw(90011)]
        at = lambda days, **kw: {r["role"]: r for r in self.load(data, targets, now=EPOCH_S + days * DAY, **kw)}
        fresh = at(2.9)
        self.assertFalse(fresh["ISS"]["age_warning"])
        self.assertTrue(fresh["ISS"]["auto_pointing_allowed"])
        middle = at(3.5)
        self.assertTrue(middle["ISS"]["age_warning"])
        self.assertEqual(middle["ISS"]["age_warning_reason"], "OLDER_THAN_3_DAYS")
        self.assertFalse(middle["ISS"]["auto_pointing_allowed"])
        self.assertFalse(middle["LRPT"]["age_warning"])
        self.assertAlmostEqual(middle["LRPT"]["age_days"], 3.5, places=9)
        old = at(7.5)
        self.assertEqual(old["LRPT"]["age_warning_reason"], "OLDER_THAN_7_DAYS")
        self.assertEqual(len(old), 2)  # Stale elements are still delivered for reception.
        ahead = at(-1.5)
        self.assertEqual(ahead["LRPT"]["age_warning_reason"], "EPOCH_AHEAD_OF_CLOCK")
        unverified = at(1.0, verified=False)
        self.assertFalse(unverified["LRPT"]["age_warning"])
        self.assertFalse(unverified["LRPT"]["time_verified"])
        self.assertFalse(unverified["LRPT"]["auto_pointing_allowed"])
        unknown = {r["role"]: r for r in self.load(data, targets, now=None)}
        self.assertIsNone(unknown["LRPT"]["age_days"])
        self.assertEqual(unknown["LRPT"]["age_warning_reason"], "AGE_UNKNOWN")
        for bad in (float("nan"), True, "now", -1.0):
            with self.assertRaises(OrbitError):
                self.load(data, targets, now=bad)

    def test_stationarity_band_edges_are_exclusive(self):
        for motion, expected in ((1.00274, True), (1.00274 + 0.00049, True), (1.00274 - 0.00049, True),
                                 (1.00274 + 0.0005, False), (1.00274 - 0.0005, False), (1.00324, False),
                                 (1.00224, False), (1.0040, False), (14.2, False)):
            with self.subTest(motion=motion):
                self.assertIs(is_stationary({"MEAN_MOTION": motion}), expected)
        geo = self.load([raw(90020, MEAN_MOTION=1.00271, ECCENTRICITY=0.0002, INCLINATION=0.05)], allow((90020, "QO100")))
        self.assertTrue(geo[0]["stationary"])
        self.assertTrue(is_stationary(geo[0]))


class ExportTests(OrbitTestCase):
    def test_atomic_replace_and_refusals(self):
        records = self.load([raw(90010), raw(90011)])
        target = self.root / "satdump-omm.csv"
        target.write_text("old")
        result = export_satdump_csv(records, target)
        self.assertEqual(result["records"], 2)
        self.assertEqual(target.read_bytes(), satdump_csv(records))
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["omm.json", "satdump-omm.csv"])
        with patch.object(orbits.os, "replace", side_effect=OSError("disk")), self.assertRaises(OSError):
            export_satdump_csv(records, target)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["omm.json", "satdump-omm.csv"])  # No temp left.
        self.assertEqual(target.read_bytes(), satdump_csv(records))  # Old content intact after a failed replace.
        for bad_target in (self.root / "missing" / "x.csv", self.root):
            with self.assertRaises(OrbitError):
                export_satdump_csv(records, bad_target)
        tampered = dict(records[0], elements=dict(records[0]["elements"], MEAN_MOTION=1.00274))
        for bad in ([records[0], records[0]], [tampered], [dict(records[0], age_warning="no")],
                    [dict(records[0], role="ISS")], records * 600, "x"):
            with self.subTest(bad=str(bad)[:40]), self.assertRaises(OrbitError):
                satdump_csv(bad)

    def test_module_never_imports_network_code(self):
        tree = ast.parse(Path(orbits.__file__).read_text(encoding="utf-8"))
        names = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        names |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        self.assertEqual(names, {"datetime", "csv", "hashlib", "io", "json", "math", "os", "pathlib", "re", "tempfile"})


class AllowlistFileTests(OrbitTestCase):
    def test_allowlist_file_is_strict(self):
        good = {"schema_version": 1, "kind": "srrx_orbit_allowlist",
                "targets": [{"norad_id": 90010, "name": "ALIAS A", "role": "LRPT"},
                            {"norad_id": 270001, "name": "ALIAS B", "role": "QO100"}]}
        loaded = orbits.load_allowlist(self.write("allow.json", good))
        self.assertEqual(sorted(loaded), [90010, 270001])
        def changed(**kw):
            value = json.loads(json.dumps(good))
            value.update(kw)
            return value
        bad = [changed(schema_version=True), changed(kind="other"), changed(targets=[]),
               changed(targets=good["targets"] + [{"norad_id": 90010, "name": "DUP", "role": "OTHER"}]),
               changed(targets=good["targets"] + [{"norad_id": 90030, "name": "Q2", "role": "QO100"}]),
               changed(targets=[{"norad_id": 90010, "name": "A", "role": "TX"}]),
               changed(targets=[{"norad_id": "90010", "name": "A", "role": "LRPT"}]),
               changed(targets=[{"norad_id": 90010, "name": "A", "role": "LRPT", "frequency": 1}]),
               changed(targets=[{"norad_id": 90010, "name": "", "role": "LRPT"}]), changed(extra=1)]
        for value in bad:
            with self.subTest(value=str(value)[:80]), self.assertRaises(OrbitError):
                orbits.load_allowlist(self.write("bad.json", value))
        with self.assertRaises(OrbitError):
            orbits.load_allowlist(self.write("dup.json", b'{"schema_version":1,"schema_version":1}'))


if __name__ == "__main__":
    unittest.main()
