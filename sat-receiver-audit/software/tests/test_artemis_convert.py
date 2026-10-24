"""artemis-db v74 converter on synthetic SQLite files built here with the v74 schema.

No real artemis-db content is used or committed: every signal is a fixture
named "Fixture ...", built with the Peewee 4.1.1 DDL of the v74 model
(Artemis-DB models/model.py at e54d5c3). Passing proves the converter's rules,
not the real v74 file; that needs the spot checks on the home base.
"""
import ast
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import sqlite3
import stat
import tempfile
import time
import unittest
from unittest import mock

from srrx import artemis_convert as ac
from srrx import scope_policy as sp

# Peewee 4.1.1 create_tables() output for models/model.py (legacy table names, no IF NOT EXISTS in sqlite_master).
V74_DDL = (
    'CREATE TABLE "info" ("DATE" TEXT, "EDITABLE" INTEGER, "NAME" TEXT, "VERSION" INTEGER)',
    'CREATE TABLE "signals" ("SIG_ID" INTEGER NOT NULL PRIMARY KEY, "DESCRIPTION" TEXT, "NAME" TEXT, "URL" TEXT, '
    '"SINCE_VERSION" INTEGER)',
    'CREATE TABLE "acf" ("ACF_ID" INTEGER NOT NULL PRIMARY KEY, "DESCRIPTION" TEXT, "SIG_ID" INTEGER, "VALUE" REAL, '
    'FOREIGN KEY ("SIG_ID") REFERENCES "signals" ("SIG_ID"))',
    'CREATE INDEX "acf_SIG_ID" ON "acf" ("SIG_ID")',
    'CREATE TABLE "bandwidth" ("BAND_ID" INTEGER NOT NULL PRIMARY KEY, "DESCRIPTION" TEXT, "SIG_ID" INTEGER, '
    '"VALUE" INTEGER, FOREIGN KEY ("SIG_ID") REFERENCES "signals" ("SIG_ID"))',
    'CREATE INDEX "bandwidth_SIG_ID" ON "bandwidth" ("SIG_ID")',
    'CREATE TABLE "categorylabel" ("CLB_ID" INTEGER NOT NULL PRIMARY KEY, "VALUE" TEXT)',
    'CREATE TABLE "category" ("CAT_ID" INTEGER NOT NULL PRIMARY KEY, "CLB_ID" INTEGER, "SIG_ID" INTEGER, '
    'FOREIGN KEY ("CLB_ID") REFERENCES "categorylabel" ("CLB_ID"), FOREIGN KEY ("SIG_ID") REFERENCES "signals" ("SIG_ID"))',
    'CREATE INDEX "category_CLB_ID" ON "category" ("CLB_ID")',
    'CREATE INDEX "category_SIG_ID" ON "category" ("SIG_ID")',
    'CREATE TABLE "documents" ("DOC_ID" INTEGER NOT NULL PRIMARY KEY, "DESCRIPTION" TEXT, "EXTENSION" TEXT, "NAME" TEXT, '
    '"PREVIEW" INTEGER, "SIG_ID" INTEGER, "TYPE" TEXT, FOREIGN KEY ("SIG_ID") REFERENCES "signals" ("SIG_ID"))',
    'CREATE INDEX "documents_SIG_ID" ON "documents" ("SIG_ID")',
    'CREATE TABLE "frequency" ("FREQ_ID" INTEGER NOT NULL PRIMARY KEY, "DESCRIPTION" TEXT, "SIG_ID" INTEGER, '
    '"VALUE" INTEGER, FOREIGN KEY ("SIG_ID") REFERENCES "signals" ("SIG_ID"))',
    'CREATE INDEX "frequency_SIG_ID" ON "frequency" ("SIG_ID")',
) + tuple(
    'CREATE TABLE "%s" ("%s" INTEGER NOT NULL PRIMARY KEY, "DESCRIPTION" TEXT, "SIG_ID" INTEGER, "VALUE" TEXT, '
    'FOREIGN KEY ("SIG_ID") REFERENCES "signals" ("SIG_ID"))' % (table, key)
    for table, key in (("location", "LOC_ID"), ("mode", "MOD_ID"), ("modulation", "MDL_ID")))
# utils/constants.py CATEGORIES at e54d5c3 (labels only; the fixture signals are synthetic).
LABELS = ("Aviation", "Marine", "Navigation", "Amateur Radio", "Trunked Radio", "Military", "Commercial", "Utility",
          "Analogue", "Digital", "Satellite", "Radar", "Interfering", "Numbers Stations", "Time")
BASE = (
    dict(name="Fixture LF time", categories=["Time", "Digital"], frequencies=[77500], bandwidths=[1300],
         modulation=[("AM", "Amplitude Modulation")], mode=[("USB", "")], location=[("Europe", "")]),
    dict(name="Fixture AIS", categories=["Marine", "Digital"], frequencies=[161975000, 162025000], bandwidths=[25000]),
    dict(name="Fixture ADS-B", categories=["Aviation", "Digital"], frequencies=[1090000000, 1030000000, 978000000],
         bandwidths=[2000000], acf=[(0.5, "Fixture frame")]),
    dict(name="Fixture military net", categories=["Military", "Digital"], frequencies=[150000000, 150100000],
         bandwidths=[3000]),
    dict(name="Fixture untagged", categories=[], frequencies=[300000000], bandwidths=[]),
    dict(name="Fixture broadcast", categories=["Analogue"], frequencies=[100000000], bandwidths=[200000],
         description="### SUMMARY\nFixture FM broadcast\n### DETAILS\n"),
    dict(name="Fixture no frequency", categories=["Utility"], frequencies=[], bandwidths=[1000]),
)
EXPECT = ["Fixture LF time=77500", "Fixture AIS=161975000", "Fixture ADS-B=1090000000"]


def build_v74(path, signals=BASE, *, ddl=V74_DDL, info=(("2026-07-18", -1, "SigID", 74),), labels=LABELS,
              after=(), journal="DELETE"):
    """Write a synthetic data.sqlite with the v74 schema; `after` SQL then models drift."""
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA journal_mode=" + journal)
        for statement in ddl:
            connection.execute(statement)
        connection.executemany('INSERT INTO "info" ("DATE", "EDITABLE", "NAME", "VERSION") VALUES (?, ?, ?, ?)', info)
        label_ids = {}
        for label in labels:
            label_ids[label] = connection.execute('INSERT INTO "categorylabel" ("VALUE") VALUES (?)', (label,)).lastrowid
        for spec in signals:
            sig_id = connection.execute(
                'INSERT INTO "signals" ("NAME", "DESCRIPTION", "URL", "SINCE_VERSION") VALUES (?, ?, ?, ?)',
                (spec["name"], spec.get("description", "### SUMMARY\n\n### DETAILS\n"),
                 "https://example.invalid/wiki/fixture", 74)).lastrowid
            for label in spec.get("categories", ()):
                connection.execute('INSERT INTO "category" ("SIG_ID", "CLB_ID") VALUES (?, ?)', (sig_id, label_ids[label]))
            for table, key in (("frequency", "frequencies"), ("bandwidth", "bandwidths")):
                for value in spec.get(key, ()):
                    connection.execute('INSERT INTO "%s" ("SIG_ID", "VALUE", "DESCRIPTION") VALUES (?, ?, ?)' % table,
                                       (sig_id, value, ""))
            for table in ("acf", "modulation", "mode", "location"):
                for value, text in spec.get(table, ()):
                    connection.execute('INSERT INTO "%s" ("SIG_ID", "VALUE", "DESCRIPTION") VALUES (?, ?, ?)' % table,
                                       (sig_id, value, text))
            connection.execute('INSERT INTO "documents" ("SIG_ID", "NAME", "DESCRIPTION", "EXTENSION", "TYPE", "PREVIEW") '
                               'VALUES (?, ?, ?, ?, ?, ?)', (sig_id, "Main", "Fixture spectrum", "png", "Image", 1))
        for statement in after:
            connection.execute(statement)
        connection.commit()
    finally:
        connection.close()
    return path


def admin_lstat():
    """lstat with root ownership and 0644/0755 modes; patched as scope_policy._lstat only."""
    real = os.lstat

    def fake(path):
        info = real(path)
        if stat.S_ISREG(info.st_mode):
            uid, mode = 0, stat.S_IFREG | 0o644
        elif stat.S_ISDIR(info.st_mode):
            uid, mode = 0, stat.S_IFDIR | 0o755
        else:
            uid, mode = info.st_uid, info.st_mode
        return mock.Mock(st_uid=uid, st_mode=mode, st_size=info.st_size, st_dev=info.st_dev, st_ino=info.st_ino)
    return fake


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.count = 0

    def db(self, signals=BASE, **kwargs):
        self.count += 1
        return build_v74(self.root / ("data%d.sqlite" % self.count), signals, **kwargs)

    def convert(self, path=None, expect=EXPECT):
        return ac.convert(self.db() if path is None else path, expect=expect)

    def refused(self, code, path, expect=EXPECT):
        with self.assertRaises(ac.ConvertRefused) as caught:
            ac.convert(path, expect=expect)
        self.assertEqual(str(caught.exception), code)
        return caught.exception


class ConversionTests(Fixture):
    def test_v74_fixture_converts_to_a_deterministic_mirror_that_scope_policy_loads(self):
        result = self.convert()
        self.assertEqual(result["mirror"], self.convert()["mirror"])
        reordered = self.db(tuple(reversed(BASE)))  # other row ids and insertion order, same content
        self.assertEqual(ac.convert(reordered, expect=EXPECT)["mirror"], result["mirror"])
        document = json.loads(result["mirror"])
        self.assertEqual(list(document), sorted(document))
        self.assertEqual((document["v"], document["kind"], document["source"], document["db_version"]),
                         (1, "srrx_artemis_mirror", "artemis-db", "v74"))
        names = [entry["name"] for entry in document["entries"]]
        self.assertEqual(names, sorted(names))
        self.assertNotIn("Fixture no frequency", names)  # no range: it can never match a span
        self.assertEqual(len(names), len(BASE) - 1)
        self.assertEqual(result["mirror"], (json.dumps(document, ensure_ascii=False, sort_keys=True,
                                                       separators=(",", ":")) + "\n").encode("utf-8"))
        self.assertEqual(result["sha256"], hashlib.sha256(result["mirror"]).hexdigest())
        path = self.root / "mirror.json"
        path.write_bytes(result["mirror"])
        db = sp.ArtemisDB.load(path, result["sha256"])
        self.assertEqual((db.status, len(db)), ("AVAILABLE", len(BASE) - 1))
        lf = next(entry for entry in document["entries"] if entry["name"] == "Fixture LF time")
        self.assertEqual(lf, {"name": "Fixture LF time", "categories": ["Digital", "Time"], "ranges_hz": [[76850, 78150]],
                              "description": "### SUMMARY\n\n### DETAILS\n",
                              "modulation": "AM; Amplitude Modulation", "mode": "USB", "location": "Europe"})
        adsb = next(entry for entry in document["entries"] if entry["name"] == "Fixture ADS-B")
        self.assertIn("Fixture frame", adsb["description"])  # acf/bandwidth/frequency descriptions are deny-checked too
        self.assertNotIn("url", json.dumps(document).lower())  # URLs and documents are not copied
        report = result["report"]
        self.assertEqual((report["accepted"], report["source"]["info_version"], report["source"]["info_date"]),
                         (False, 74, "2026-07-18"))
        self.assertEqual(report["counts"]["signals"], len(BASE))
        self.assertEqual(report["counts"]["signals_without_frequency"], 1)
        self.assertEqual(report["counts"]["entries"], len(BASE) - 1)
        self.assertEqual(report["mirror"], {"file": ac.MIRROR_FILE, "sha256": result["sha256"],
                                            "bytes": len(result["mirror"])})
        self.assertEqual([check["result"] for check in report["spot_checks"]], ["PASS"] * 3)
        self.assertIn("UNVERIFIED", report["licence"])
        self.assertNotIn(str(self.root), json.dumps(report))  # hashes and counts, no paths
        self.assertEqual(result["template"]["sha256"], result["sha256"])

    def test_ranges_are_the_envelope_plus_each_point_and_stay_in_bounds(self):
        self.assertEqual(ac.ranges_hz([100, 300], [50]), [[75, 125], [75, 325], [275, 325]])
        self.assertEqual(ac.ranges_hz([300, 100, 100], [50, 10]), [[75, 125], [75, 325], [275, 325]])  # max(B)
        self.assertEqual(ac.ranges_hz([100, 300], []), [[100, 300]])  # no bandwidth: the envelope only
        self.assertEqual(ac.ranges_hz([100, 300], [0]), [[100, 300]])
        self.assertEqual(ac.ranges_hz([100], [3]), [[98, 102]])  # ceil(3 / 2) = 2: never narrower
        self.assertEqual(ac.ranges_hz([10], [100]), [[0, 60]])
        self.assertEqual(ac.ranges_hz([ac.MAX_HZ], [10]), [[ac.MAX_HZ - 5, ac.MAX_HZ]])
        many = ac.ranges_hz(range(1000, 1040), [2])
        self.assertEqual(many, [[999, 1040]])  # 41 ranges > 32: the envelope covers every point
        self.assertEqual(len(ac.ranges_hz(range(1000, 1031), [2])), 32)
        with self.assertRaisesRegex(ac.ConvertRefused, "NO_FREQUENCY"):
            ac.ranges_hz([], [1])
        military = next(entry for entry in json.loads(self.convert()["mirror"])["entries"]
                        if entry["name"] == "Fixture military net")
        self.assertEqual(military["ranges_hz"], [[149998500, 150001500], [149998500, 150101500],
                                                 [150098500, 150101500]])
        result = ac.convert(self.db(BASE + (dict(name="Fixture wide", categories=["Utility"],
                                                 frequencies=list(range(5000000, 5000040)), bandwidths=[2]),)),
                            expect=EXPECT)
        self.assertEqual(result["report"]["counts"]["envelope_only"], 1)

    def test_schema_drift_refuses_the_whole_file(self):
        frequency_text = tuple(statement.replace('"VALUE" INTEGER, FOREIGN', '"VALUE" TEXT, FOREIGN')
                               if statement.startswith('CREATE TABLE "frequency"') else statement for statement in V74_DDL)
        frequency_no_key = tuple(statement.replace(', FOREIGN KEY ("SIG_ID") REFERENCES "signals" ("SIG_ID")', "")
                                 if statement.startswith('CREATE TABLE "frequency"') else statement for statement in V74_DDL)
        frequency_not_null = tuple(statement.replace('"VALUE" INTEGER, FOREIGN', '"VALUE" INTEGER NOT NULL, FOREIGN')
                                   if statement.startswith('CREATE TABLE "frequency"') else statement
                                   for statement in V74_DDL)
        cases = {
            "extra column": (dict(after=['ALTER TABLE "signals" ADD COLUMN "EXTRA" TEXT']), "SCHEMA_COLUMNS:signals"),
            "generated column": (dict(after=['ALTER TABLE "frequency" ADD COLUMN "G" INTEGER GENERATED ALWAYS AS (1) '
                                             'VIRTUAL']), "SCHEMA_COLUMNS:frequency"),
            "column type": (dict(ddl=frequency_text), "SCHEMA_COLUMNS:frequency"),
            "not null": (dict(ddl=frequency_not_null), "SCHEMA_COLUMNS:frequency"),
            "foreign key": (dict(ddl=frequency_no_key), "SCHEMA_FOREIGN_KEYS:frequency"),
            "missing table": (dict(after=['DROP TABLE "acf"']), "SCHEMA_TABLES"),
            "extra table": (dict(after=['CREATE TABLE "extra" ("A" TEXT)']), "SCHEMA_TABLES"),
            "statistics table": (dict(after=["ANALYZE"]), "SCHEMA_TABLES"),
            "view": (dict(after=['CREATE VIEW "fixture_view" AS SELECT 1']), "SCHEMA_OBJECTS"),
            "trigger": (dict(after=['CREATE TRIGGER "fixture_trigger" AFTER INSERT ON "info" BEGIN SELECT 1; END']),
                        "SCHEMA_OBJECTS"),
            "version 73": (dict(info=(("2026-06-14", -1, "SigID", 73),)), "INFO_VERSION"),
            "version as text": (dict(after=['UPDATE "info" SET "VERSION" = CAST(\'74\' AS BLOB)']), "INFO_VERSION"),
            "other database": (dict(info=(("2026-07-18", -1, "Artemis", 74),)), "INFO_NAME"),
            "two info rows": (dict(info=(("2026-07-18", -1, "SigID", 74),) * 2), "INFO_ROWS"),
            "no info row": (dict(info=()), "INFO_ROWS"),
            "wal journal": (dict(journal="WAL"), "SQLITE_JOURNAL_MODE"),
        }
        for name, (kwargs, code) in cases.items():
            with self.subTest(case=name):
                self.refused(code, self.db(**kwargs))

    def test_value_drift_refuses_the_whole_file(self):
        insert = 'INSERT INTO "frequency" ("SIG_ID", "VALUE", "DESCRIPTION") VALUES '
        cases = {
            "frequency as text": ([insert + "(1, '137.9 MHz', '')"], "FREQUENCY_VALUE"),
            "frequency as real": ([insert + "(1, 145.8, '')"], "FREQUENCY_VALUE"),
            "frequency null": ([insert + "(1, NULL, '')"], "FREQUENCY_VALUE"),
            "frequency zero": ([insert + "(1, 0, '')"], "FREQUENCY_VALUE"),
            "frequency above 1 THz": ([insert + "(1, 1000000000001, '')"], "FREQUENCY_VALUE"),
            "bandwidth negative": (['INSERT INTO "bandwidth" ("SIG_ID", "VALUE") VALUES (1, -5)'], "BANDWIDTH_VALUE"),
            "bandwidth null": (['INSERT INTO "bandwidth" ("SIG_ID", "VALUE") VALUES (1, NULL)'], "BANDWIDTH_VALUE"),
            "orphan frequency": ([insert + "(999, 100, '')"], "ORPHAN_ROW:frequency"),
            "frequency without signal": ([insert + "(NULL, 100, '')"], "ORPHAN_ROW:frequency"),
            "orphan mode": (['INSERT INTO "mode" ("SIG_ID", "VALUE") VALUES (999, \'USB\')'], "ORPHAN_ROW:mode"),
            "dangling label": (['INSERT INTO "category" ("SIG_ID", "CLB_ID") VALUES (1, 999)'], "CATEGORY_REFERENCE"),
            "category without label": (['INSERT INTO "category" ("SIG_ID", "CLB_ID") VALUES (1, NULL)'],
                                       "CATEGORY_REFERENCE"),
            # TEXT affinity stores a number as text, so a blob is the non-text value here.
            "label not text": (['INSERT INTO "categorylabel" ("VALUE") VALUES (X\'05\')'], "CATEGORY_LABEL"),
            "label too long": (['INSERT INTO "categorylabel" ("VALUE") VALUES (\'%s\')' % ("x" * 129)], "CATEGORY_LABEL"),
            "signal without name": (['UPDATE "signals" SET "NAME" = NULL WHERE "SIG_ID" = 2'], "SIGNAL_NAME"),
            "blank signal name": (['UPDATE "signals" SET "NAME" = \'  \' WHERE "SIG_ID" = 2'], "SIGNAL_NAME"),
            "description blob": (['UPDATE "signals" SET "DESCRIPTION" = X\'00ff\' WHERE "SIG_ID" = 2'],
                                 "TEXT_TYPE:signals"),
            "mode as blob": (['INSERT INTO "mode" ("SIG_ID", "VALUE") VALUES (1, X\'07\')'], "TEXT_TYPE:mode"),
            "acf as text": (['INSERT INTO "acf" ("SIG_ID", "VALUE") VALUES (1, \'fast\')'], "ACF_VALUE"),
        }
        for name, (after, code) in cases.items():
            with self.subTest(case=name):
                self.refused(code, self.db(after=after))
        # Text columns may be NULL (no text); stored integers in REAL acf values are fine.
        result = ac.convert(self.db(after=['INSERT INTO "mode" ("SIG_ID", "VALUE", "DESCRIPTION") VALUES (1, NULL, NULL)',
                                           'INSERT INTO "acf" ("SIG_ID", "VALUE") VALUES (1, NULL)']), expect=EXPECT)
        self.assertEqual(result["report"]["counts"]["entries"], len(BASE) - 1)

    def test_files_that_are_not_a_clean_v74_sqlite_are_refused(self):
        mirror = self.root / "mirror.json"
        mirror.write_bytes(b'{"v":1,"kind":"srrx_artemis_mirror"}')
        self.refused("NOT_SQLITE", mirror)
        short = self.root / "short.sqlite"
        short.write_bytes(sp.SQLITE_MAGIC + bytes(20))
        self.refused("NOT_SQLITE", short)
        self.refused("SOURCE_UNAVAILABLE", self.root / "missing.sqlite")
        self.refused("NOT_REGULAR_FILE", self.root)
        for value in (None, 3.5, "bad\0path"):
            with self.subTest(value=value):
                self.refused("SOURCE_UNAVAILABLE", value)
        corrupt = self.db()
        data = bytearray(corrupt.read_bytes())
        page = int.from_bytes(data[16:18], "big")
        for number in range(1, len(data) // page):  # every page after the first: b-tree headers and cells
            data[number * page:number * page + 64] = b"\xa5" * 64
        corrupt.write_bytes(bytes(data))
        with self.assertRaises(ac.ConvertRefused) as caught:
            ac.convert(corrupt, expect=EXPECT)
        self.assertIn(str(caught.exception), ("SQLITE_INTEGRITY", "SQLITE_UNREADABLE"))
        with mock.patch.object(ac, "MAX_SOURCE_BYTES", 1024):
            self.refused("SOURCE_SIZE_LIMIT", self.db())
        special = []
        if hasattr(os, "mkfifo"):  # POSIX: a FIFO would block a plain open() forever
            fifo = self.root / "data.fifo"
            os.mkfifo(fifo)
            special.append(fifo)
        try:
            link = self.root / "link.sqlite"
            os.symlink(self.db(), link)
            special.append(link)  # a final symlink is refused, even to a good file
        except (OSError, NotImplementedError):
            pass  # Windows without the symlink privilege
        for candidate in special:
            with self.subTest(path=candidate.name):
                started = time.monotonic()
                self.refused("NOT_REGULAR_FILE", candidate)
                self.assertLess(time.monotonic() - started, 5)

    def test_source_is_opened_read_only_and_must_not_change(self):
        path = self.db()
        before = (path.read_bytes(), os.stat(path).st_mtime_ns, sorted(os.listdir(self.root)))
        self.convert(path)
        self.assertEqual((path.read_bytes(), os.stat(path).st_mtime_ns, sorted(os.listdir(self.root))), before)
        real = ac._snapshot
        calls = []

        def changing(source):
            identity, header = real(source)
            calls.append(identity)
            return (identity[:4] + ("0" * 64,) if len(calls) > 1 else identity), header
        with mock.patch.object(ac, "_snapshot", side_effect=changing):
            self.refused("SOURCE_CHANGED", path)
        self.assertEqual(len(calls), 2)

    def test_connection_allows_reads_only(self):
        connection = ac._connect(self.db())
        try:
            self.assertEqual(connection.execute("SELECT typeof(1)").fetchall(), [("integer",)])
            self.assertEqual(connection.execute('SELECT "NAME" FROM "info"').fetchall(), [("SigID",)])
            for statement in ("ATTACH DATABASE ':memory:' AS other", 'CREATE TABLE "z" ("a")',
                              'INSERT INTO "info" ("NAME") VALUES (\'x\')', 'DELETE FROM "signals"',
                              'UPDATE "info" SET "VERSION" = 75', "PRAGMA writable_schema=ON", "PRAGMA journal_mode=WAL",
                              "SELECT load_extension('fixture')", "SELECT upper('x')", "VACUUM"):
                with self.subTest(statement=statement), self.assertRaises(sqlite3.DatabaseError):
                    connection.execute(statement).fetchall()
        finally:
            connection.close()

    def test_spot_checks_confirm_that_values_are_hz(self):
        path = self.db()
        for expect in ([], EXPECT[:2], [EXPECT[0]] * 3, "Fixture AIS=161975000", None):
            with self.subTest(expect=expect):
                self.refused("SPOT_CHECKS_REQUIRED", path, expect)
        for index, expect in ((0, ["Fixture LF time=77"] + EXPECT[1:]),  # 77.5 kHz typed in kHz
                              (2, EXPECT[:2] + ["Fixture ADS-B=1090"])):  # MHz
            with self.subTest(expect=expect):
                self.refused("SPOT_CHECK_FREQUENCY:%d" % index, path, expect)
        self.refused("SPOT_CHECK_NAME:1", path, [EXPECT[0], "Fixture unknown=100", EXPECT[2]])
        for bad in ("Fixture AIS", "Fixture AIS=1.5", "Fixture AIS=-1", "=100", "Fixture AIS=99999999999999"):
            with self.subTest(bad=bad):
                self.refused("SPOT_CHECK_FORMAT:1", path, [EXPECT[0], bad, EXPECT[2]])
        self.assertEqual(len(ac.convert(path, expect=[("Fixture LF time", 77500), ("Fixture AIS", 162025000),
                                                     ("Fixture ADS-B", 978000000)])["report"]["spot_checks"]), 3)
        twin = self.db(BASE + (dict(BASE[0], frequencies=[60000]),))  # two signals with one name
        self.refused("SPOT_CHECK_NAME:0", twin)
        # A file whose values are kHz fails every Hz spot check, so it never becomes a mirror.
        khz = self.db(tuple(dict(spec, frequencies=[value // 1000 for value in spec["frequencies"]]) for spec in BASE))
        self.refused("SPOT_CHECK_FREQUENCY:0", khz)

    def test_a_cut_text_keeps_its_deny_stop(self):
        long_tail = dict(name="Fixture long", categories=["Utility"], frequencies=[7000000], bandwidths=[3000],
                         description="x" * 20000 + " Link-16 net")
        long_name = dict(name="Fixture " + "y" * 300 + " NATO", categories=["Utility"], frequencies=[8000000],
                         bandwidths=[3000])
        benign = dict(name="Fixture benign long", categories=["Utility"], frequencies=[9000000], bandwidths=[3000],
                      description="z" * 20000)
        result = ac.convert(self.db(BASE + (long_tail, long_name, benign)), expect=EXPECT)
        entries = {entry["name"][:19]: entry for entry in json.loads(result["mirror"])["entries"]}
        self.assertTrue(entries["Fixture long"]["description"].startswith("[srrx: Link-16] "))
        self.assertEqual(len(entries["Fixture long"]["description"]), ac.TEXT_LIMITS["description"])
        cut_name = next(entry for name, entry in entries.items() if name.startswith("Fixture yyy"))
        self.assertEqual(len(cut_name["name"]), ac.TEXT_LIMITS["name"])
        self.assertTrue(cut_name["description"].startswith("[srrx: NATO] "))
        self.assertNotIn("[srrx:", entries["Fixture benign long"]["description"])
        self.assertEqual((result["report"]["counts"]["deny_markers"], result["report"]["counts"]["truncated_fields"]),
                         (2, 3))
        path = self.root / "mirror.json"
        path.write_bytes(result["mirror"])
        db = sp.ArtemisDB.load(path, result["sha256"])
        for span in ((7.0e6, 7.0001e6), (8.0e6, 8.0001e6)):
            with self.subTest(span=span):
                self.assertEqual(sp.scope_check(*span, db)["reason"], "DENY_REGEX")
        self.assertFalse(sp.scope_check(9.0e6, 9.0001e6, db)["stop"])

    def test_limits_fail_closed(self):
        path = self.db()
        with mock.patch.object(ac, "MAX_ROWS", 2):
            self.refused("ROW_LIMIT", path)
        with mock.patch.object(sp.ArtemisDB, "MAX_ENTRIES", 2):
            self.refused("ENTRY_LIMIT", path)
        with mock.patch.object(sp.ArtemisDB, "MAX_RANGES", 4):
            self.refused("RANGE_LIMIT", path)
        with mock.patch.object(ac, "MAX_CATEGORIES", 1):
            self.refused("CATEGORY_LIMIT", path)
        with mock.patch.object(sp.ArtemisDB, "MAX_BYTES", 64):
            self.refused("MIRROR_SIZE_LIMIT", path)

    def test_no_network_and_no_network_code(self):
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network used")), \
                mock.patch.object(socket, "create_connection", side_effect=AssertionError("network used")):
            self.convert()
        tree = ast.parse(Path(ac.__file__).read_text(encoding="utf-8"))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
                    for alias in node.names}
        imported |= {node.module.split(".")[0] for node in ast.walk(tree)
                     if isinstance(node, ast.ImportFrom) and node.module and node.level == 0}
        self.assertFalse(imported & {"socket", "urllib", "http", "ssl", "requests", "ftplib", "subprocess"})


class AcceptanceTests(Fixture):
    def accepted(self, folder, evidence="admin/artemis-db-v74-mirror-001"):
        template = json.loads((folder / ac.TEMPLATE_FILE).read_text(encoding="utf-8"))
        record = folder / "artemis-acceptance.json"
        record.write_text(json.dumps(dict(template, evidence_id=evidence)), encoding="utf-8")
        with mock.patch.object(sp, "_lstat", side_effect=admin_lstat()):
            return sp.ArtemisDB.load_accepted(folder / ac.MIRROR_FILE, record)

    def test_pol09_military_and_untagged_300_mhz_entries_stop_from_converter_output(self):
        folder = self.root / "out"
        folder.mkdir()
        ac.write_outputs(self.convert(), folder)
        with mock.patch.object(sp, "_lstat", side_effect=admin_lstat()), self.assertRaises(sp.ScopeRefused):
            sp.load_artemis_acceptance(folder / ac.TEMPLATE_FILE)  # the placeholder is never an acceptance
        self.assertEqual(self.accepted(folder, ac.EVIDENCE_PLACEHOLDER).status, "UNAVAILABLE_NO_ACCEPTANCE_RECORD")
        db = self.accepted(folder)
        self.assertEqual(db.status, "AVAILABLE")
        military = sp.scope_check(150.05e6, 150.06e6, db)
        self.assertEqual((military["stop"], military["reason"], military["display"], military["identify"]),
                         (True, "CATEGORY", "out of scope", "WITHHELD"))
        self.assertNotIn("Fixture", json.dumps(military))
        untagged = sp.scope_check(299.99e6, 300.01e6, db)
        self.assertEqual(untagged["reasons"], ["UNTAGGED_MASKED", "MASKED_BAND"])
        self.assertEqual(untagged["display"], "out of scope")
        benign = sp.scope_check(100.0e6, 100.05e6, db)
        self.assertEqual((benign["stop"], benign["identify"], benign["display"]),
                         (False, "MATCHED", [{"name": "Fixture broadcast", "categories": ["Analogue"]}]))
        latch = sp.ScopeLatch(db, clock=lambda: 1792483200.0)
        self.assertFalse(latch.permits("record", (150.0e6, 150.2e6)))
        self.assertEqual(latch.drain_log(), ["2026-10-20T08:00:00Z out of scope"])
        (folder / ac.MIRROR_FILE).write_bytes((folder / ac.MIRROR_FILE).read_bytes() + b" ")
        self.assertEqual(self.accepted(folder).status, "UNAVAILABLE_SHA256_MISMATCH")

    def test_raw_sqlite_stays_unavailable_in_labd_even_with_its_sha256(self):
        path = self.db()
        self.assertEqual(sp.ArtemisDB.load(path, hashlib.sha256(path.read_bytes()).hexdigest()).status,
                         "UNAVAILABLE_FORMAT_UNVERIFIED_SQLITE")

    def test_trunked_radio_entries_stay_anonymous(self):
        trunk = dict(name="Fixture trunk system", categories=["Trunked Radio", "Digital"], frequencies=[160100000],
                     bandwidths=[12500])
        result = ac.convert(self.db(BASE + (trunk,)), expect=EXPECT)
        path = self.root / "mirror.json"
        path.write_bytes(result["mirror"])
        decision = sp.scope_check(160.1e6, 160.1e6, sp.ArtemisDB.load(path, result["sha256"]))
        self.assertEqual(decision["display"], [{"occupancy": "anonymous"}])

    def test_cli_writes_three_new_files_and_never_replaces_them(self):
        path, folder = self.db(), self.root / "out"
        folder.mkdir()
        argv = ["--sqlite", str(path), "--output-dir", str(folder)] + [item for check in EXPECT
                                                                        for item in ("--expect", check)]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ac.main(argv), 0)
        summary = json.loads(out.getvalue())
        self.assertEqual((summary["entries"], summary["spot_checks"], summary["accepted"]), (len(BASE) - 1, 3, False))
        self.assertEqual(sorted(p.name for p in folder.iterdir()), sorted((ac.MIRROR_FILE, ac.TEMPLATE_FILE,
                                                                           ac.REPORT_FILE)))
        mirror = (folder / ac.MIRROR_FILE).read_bytes()
        self.assertEqual(hashlib.sha256(mirror).hexdigest(), summary["mirror_sha256"])
        self.assertEqual(json.loads((folder / ac.REPORT_FILE).read_text(encoding="utf-8"))["mirror"]["sha256"],
                         summary["mirror_sha256"])
        for args, code in ((argv, "OUTPUT_EXISTS"), (argv[:4], "SPOT_CHECKS_REQUIRED"),
                           (["--sqlite", str(self.root / "missing"), "--output-dir", str(folder)] + argv[4:],
                            "SOURCE_UNAVAILABLE"),
                           (["--sqlite", str(path), "--output-dir", str(self.root / "absent")] + argv[4:],
                            "OUTPUT_DIRECTORY")):
            error = io.StringIO()
            with self.subTest(code=code), contextlib.redirect_stderr(error):
                self.assertEqual(ac.main(args), 2)
                self.assertEqual(error.getvalue(), "srrx.artemis_convert: refused: %s\n" % code)
        self.assertEqual((folder / ac.MIRROR_FILE).read_bytes(), mirror)


if __name__ == "__main__":
    unittest.main()
