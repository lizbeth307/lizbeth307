"""srrx.adsb_filter (W2 SW-ADSB): the readsb lease's privacy filter, on synthetic fixtures only.

The database, range table and aircraft.json below are made up here (no tar1090-db or readsb
output is committed: both upstream data files are fetch-only). No readsb runs, no receiver is
opened and no unit is started; the template text is parsed, not executed.
"""
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from srrx import adsb_filter as f
from srrx import decoder_policy

PROJECT = Path(__file__).resolve().parents[2]
UNIT = PROJECT / "software/systemd/srrx-lease-readsb@.service"
TODAY = datetime.date(2026, 11, 7)
COMMIT_DB, COMMIT_RANGES = "1" * 40, "2" * 40
CIVIL, INTERESTING = 0x4CA9F1, 0x4CA9F2
DB_MILITARY, DB_PIA, DB_LADD, DB_BOTH = 0x4CA9F3, 0xA1B2C3, 0xA1B2C4, 0x4CA9F5
RANGE_FIRST, RANGE_LAST = 0x43C000, 0x43CFFF  # synthetic, shaped like a tar1090-db "military" entry
OTHER_RANGE = (0xADF7C8, 0xAFFFFF)
TRUST = lambda path, code: None  # noqa: E731 - root ownership is admin_trust's own test


def trust_mine(path, code):
    f.admin_trust(path, code, uids=(0, os.getuid()))


def database(extra=()):
    rows = [(CIVIL, "00"), (INTERESTING, "01"), (DB_MILITARY, "10"), (DB_PIA, "0010"), (DB_LADD, "0001"), (DB_BOTH, "1001")]
    rows += [(0x300000 + i, "00") for i in range(1200)] + list(extra)
    text = "".join("%06X;REG%d;TYP;%s;Synthetic type;2000;Synthetic owner;\n" % (address, i, flags)
                   for i, (address, flags) in enumerate(rows))
    return gzip.compress(text.encode("ascii"), mtime=0)


def ranges():
    return json.dumps({"military": [["%06x" % RANGE_FIRST, "%06x" % RANGE_LAST], ["%06x" % OTHER_RANGE[0], "%06x" % OTHER_RANGE[1]]]},
                      indent=4).encode("ascii")


def aircraft(address, **fields):
    return dict({"hex": address if isinstance(address, str) else "%06x" % address, "type": "adsb_icao", "flight": "TEST%04d " % (hash(address) % 10000),
                 "alt_baro": 35000, "gs": 450.1, "track": 90.0, "lat": 50.1, "lon": 10.2, "seen": 0.4, "messages": 12, "rssi": -20.5,
                 "acas_ra": {"utc": "x"}, "gpsOkBefore": 1.0, "rr_lat": 1.0}, **fields)


class Fixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="srrx-adsb-")
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        self.root, self.run_dir, self.products = self.work / "adsb", self.work / "run", self.work / "products"
        for directory in (self.run_dir, self.products):
            directory.mkdir()
        (self.work / "aircraft.csv.gz").write_bytes(database())
        (self.work / "ranges.json").write_bytes(ranges())
        self.record = self.accept()
        patcher = mock.patch.dict(os.environ, {"MAINPID": ""})
        patcher.start()
        self.addCleanup(patcher.stop)

    def accept(self, data_date="2026-11-02", **kwargs):
        return f.accept(self.work / "aircraft.csv.gz", COMMIT_DB, data_date, self.work / "ranges.json", COMMIT_RANGES,
                        "2026-11-07", kwargs.pop("accepted_by", "home-base operator"), root=self.root, today=kwargs.pop("today", TODAY))

    def filter(self, today=TODAY):
        return f.load_filter(root=self.root, today=today, trust=TRUST)

    def rewrite_record(self, change):
        record = json.loads((self.root / "acceptance.json").read_text(encoding="utf-8"))
        change(record)
        (self.root / "acceptance.json").write_text(json.dumps(record), encoding="utf-8")

    def refusal(self, call):
        with self.assertRaises(f.FilterRefused) as caught:
            call()
        return caught.exception.code

    def engine_json(self, items, now=1794000000.5):
        path = self.run_dir / "json/aircraft.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps({"now": now, "messages": 99999, "aircraft": items}), encoding="utf-8")
        return path

    def published(self):
        return json.loads((self.products / "aircraft.json").read_text(encoding="utf-8"))

    def status(self):
        return json.loads((self.products / "status.json").read_text(encoding="utf-8"))


class FilterDecisionTests(Fixture):
    def test_db_flags_military_pia_ladd_are_never_output_and_interesting_is_not_a_filter(self):
        flt = self.filter()
        hidden = [aircraft(0x400001, dbFlags=1), aircraft(0x400002, dbFlags=4), aircraft(0x400003, dbFlags=8),
                  aircraft(0x400004, dbFlags=1 | 2), aircraft(0x400005, dbFlags=4 | 8), aircraft(0x400006, dbFlags=15),
                  aircraft(0x400007, dbFlags="1"), aircraft(0x400008, dbFlags=-1)]
        shown = [aircraft(CIVIL), aircraft(0x400009, dbFlags=0), aircraft(0x40000A, dbFlags=2)]
        document = flt.document({"now": 1.5, "aircraft": hidden + shown}, "rtla")
        self.assertEqual([a["hex"] for a in document["aircraft"]], ["4ca9f1", "400009", "40000a"])
        self.assertTrue(all("dbFlags" not in a for a in document["aircraft"]))
        text = json.dumps(document)
        for item in hidden:
            self.assertNotIn(item["hex"], text)

    def test_database_flags_hide_even_when_readsb_reports_none(self):
        # STACK.md:2181: a database readsb did not load must not hide less (the filter reads it itself).
        flt = self.filter()
        items = [aircraft(a) for a in (CIVIL, INTERESTING, DB_MILITARY, DB_PIA, DB_LADD, DB_BOTH)]
        document = flt.document({"now": 2, "aircraft": items}, "rtlb")
        self.assertEqual([a["hex"] for a in document["aircraft"]], ["4ca9f1", "4ca9f2"])
        self.assertEqual(flt.flagged, {DB_MILITARY: 1, DB_PIA: 4, DB_LADD: 8, DB_BOTH: 9})

    def test_military_ranges_and_unclassifiable_addresses_are_hidden(self):
        flt = self.filter()
        hidden = [RANGE_FIRST, RANGE_LAST, RANGE_FIRST + 0x123, OTHER_RANGE[0], OTHER_RANGE[1], 0xAE1234]
        shown = [RANGE_FIRST - 1, RANGE_LAST + 1, OTHER_RANGE[0] - 1, 0xB00000]
        odd = ["~4ca9f1", "~0001ab", "4ca9f", "4ca9f1x", "", None, 123456, "zzzzzz"]
        items = [aircraft(a) for a in hidden + shown] + [aircraft(0, hex=v) for v in odd] + ["not an object", None, 7]
        document = flt.document({"now": 3, "aircraft": items}, "rtla")
        self.assertEqual([a["hex"] for a in document["aircraft"]], ["%06x" % a for a in shown])
        for address in hidden:
            self.assertFalse(flt.shown(aircraft(address)))
        self.assertTrue(flt.shown(aircraft("4CA9F1")))
        self.assertEqual(flt.publishable(aircraft("4CA9F1"))["hex"], "4ca9f1")

    def test_only_documented_fields_are_published(self):
        flt = self.filter()
        document = flt.document({"now": 4, "messages": 5, "aircraft": [aircraft(CIVIL, r="D-TEST", t="A320", dbFlags=2, desc="x", ownOp="y")]}, "rtla")
        self.assertEqual(set(document), {"schema_version", "kind", "receiver", "now", "aircraft"})
        published = document["aircraft"][0]
        self.assertLessEqual(set(published), set(f.KEEP))
        for dropped in ("dbFlags", "acas_ra", "gpsOkBefore", "rr_lat", "desc", "ownOp"):
            self.assertNotIn(dropped, published)
        self.assertEqual((published["r"], published["t"]), ("D-TEST", "A320"))

    def test_malformed_engine_documents_are_refused(self):
        flt = self.filter()
        for engine in (None, [], {"aircraft": []}, {"now": "1", "aircraft": []}, {"now": float("nan"), "aircraft": []},
                       {"now": 1, "aircraft": {}}):
            with self.subTest(engine=engine):
                self.assertEqual(self.refusal(lambda: flt.document(engine, "rtla")), "ENGINE_OUTPUT_UNREADABLE")


class AcceptanceTests(Fixture):
    def test_accept_installs_both_files_and_a_bound_record(self):
        self.assertEqual(self.record["database"]["sha256"], hashlib.sha256(database()).hexdigest())
        self.assertEqual(self.record["database"]["rows"], 1206)
        self.assertEqual(self.record["ranges"]["military_ranges"], 2)
        self.assertEqual(self.record["database"]["source_url"], "https://github.com/wiedehopf/tar1090-db/raw/%s/aircraft.csv.gz" % COMMIT_DB)
        self.assertEqual(self.record["ranges"]["source_url"], "https://raw.githubusercontent.com/wiedehopf/tar1090-db/%s/ranges.json" % COMMIT_RANGES)
        self.assertEqual((self.root / "aircraft.csv.gz").read_bytes(), database())
        record, blobs = f.load_acceptance(root=self.root, today=TODAY, trust=TRUST)
        self.assertEqual(record, self.record)
        self.assertEqual(set(blobs), {"aircraft.csv.gz", "ranges.json"})

    def test_missing_stale_future_or_changed_data_is_refused(self):
        self.assertEqual(self.refusal(lambda: f.load_filter(root=self.work / "absent", today=TODAY, trust=TRUST)), "ACCEPTANCE_MISSING")
        # 90 days after the data date still loads; day 91 and a date ahead of the clock refuse.
        self.filter(today=datetime.date(2026, 11, 2) + datetime.timedelta(days=90))
        self.assertEqual(self.refusal(lambda: self.filter(today=datetime.date(2026, 11, 2) + datetime.timedelta(days=91))), "DATABASE_STALE")
        self.assertEqual(self.refusal(lambda: self.filter(today=datetime.date(2026, 10, 31))), "DATABASE_DATE_IN_FUTURE")
        self.assertEqual(self.refusal(lambda: self.accept(data_date="2026-08-01")), "DATABASE_STALE")
        (self.root / "aircraft.csv.gz").write_bytes(database(extra=[(0x123456, "10")]))
        self.assertEqual(self.refusal(self.filter), "DATABASE_DIGEST")
        self.accept()
        (self.root / "ranges.json").write_bytes(ranges().replace(b"43cfff", b"43cffe"))
        self.assertEqual(self.refusal(self.filter), "RANGES_DIGEST")
        self.accept()
        (self.root / "ranges.json").unlink()
        self.assertEqual(self.refusal(self.filter), "RANGES_MISSING")
        self.accept()
        (self.root / "aircraft.csv.gz").unlink()
        self.assertEqual(self.refusal(self.filter), "DATABASE_MISSING")

    def test_record_schema_is_exact(self):
        cases = {
            "ACCEPTANCE_NOT_ACCEPTED": lambda r: r.update(status="OPEN"),
            "ACCEPTANCE_SCHEMA": lambda r: r.update(accepted_by="@".join(("operator", "example.org"))),  # an address is refused
        }
        schema = [lambda r: r.update(extra=1), lambda r: r.pop("accepted_on"), lambda r: r.update(schema_version=2),
                  lambda r: r["database"].update(source_url="https://example.org/aircraft.csv.gz"),
                  lambda r: r["database"].update(path="/tmp/aircraft.csv.gz"), lambda r: r["database"].update(data_date="2.11.2026"),
                  lambda r: r["ranges"].update(source_commit="abc"), lambda r: r["database"].update(rows=10),
                  lambda r: r["ranges"].update(military_ranges=0), lambda r: r.update(accepted_by="")]
        for code, change in list(cases.items()) + [("ACCEPTANCE_SCHEMA", c) for c in schema]:
            with self.subTest(code=code, change=change):
                self.accept()
                self.rewrite_record(change)
                self.assertEqual(self.refusal(self.filter), code)
        self.accept()
        self.rewrite_record(lambda r: r["database"].update(rows=r["database"]["rows"] + 1))
        self.assertEqual(self.refusal(self.filter), "DATABASE_FORMAT")
        self.accept()
        text = (self.root / "acceptance.json").read_text(encoding="utf-8")
        (self.root / "acceptance.json").write_text(text.replace('"status": "ACCEPTED"', '"status": "ACCEPTED", "status": "ACCEPTED"'), encoding="utf-8")
        self.assertEqual(self.refusal(self.filter), "ACCEPTANCE_SCHEMA")

    def test_database_and_range_formats(self):
        (self.work / "small.csv.gz").write_bytes(gzip.compress(b"4CA9F1;;;00;;;;\n"))
        self.assertEqual(self.refusal(lambda: f.accept(self.work / "small.csv.gz", COMMIT_DB, "2026-11-02", self.work / "ranges.json",
                                                       COMMIT_RANGES, "2026-11-07", "operator", root=self.root, today=TODAY)), "DATABASE_FORMAT")
        self.assertEqual(self.refusal(lambda: f.parse_database(b"not gzip")), "DATABASE_FORMAT")
        rows, flagged = f.parse_database(database(extra=[(0x123456, "11"), (0x123457, "0101")]))
        self.assertEqual((rows, flagged[0x123456], flagged[0x123457]), (1208, 1, 8))
        for bad in (b"{}", b'{"military": []}', b'{"military": [["43c000"]]}', b'{"military": [["43cfff", "43c000"]]}',
                    b'{"military": [["43c00g", "43cfff"]]}', b'{"military": [[1, 2]]}', b"[", b'{"military": [["43c000", "43cfff"]], "military": []}'):
            with self.subTest(bad=bad):
                self.assertEqual(self.refusal(lambda: f.parse_ranges(bad)), "RANGES_FORMAT")
        count, merged = f.parse_ranges(b'{"military": [["000010", "00001f"], ["000000", "000010"], ["000030", "00003f"], ["000020", "00002f"]]}')
        self.assertEqual((count, merged), (4, [(0, 0x3F)]))

    @unittest.skipUnless(hasattr(os, "getuid"), "POSIX ownership and modes")
    def test_admin_trust_needs_a_file_only_its_owner_can_change(self):
        self.accept()
        for path in [self.root / name for name in ("acceptance.json", "aircraft.csv.gz", "ranges.json")] + [self.root]:
            os.chmod(path, 0o755 if path == self.root else 0o644)
        os.chmod(self.work, 0o755)
        try:
            f.load_acceptance(root=self.root, today=TODAY, trust=trust_mine)
        except f.FilterRefused as refused:
            self.skipTest("a parent of the temporary directory is writable by others: " + refused.code)
        os.chmod(self.root / "aircraft.csv.gz", 0o664)
        self.assertEqual(self.refusal(lambda: f.load_acceptance(root=self.root, today=TODAY, trust=trust_mine)), "DATABASE_NOT_TRUSTED")
        os.chmod(self.root / "aircraft.csv.gz", 0o644)
        os.chmod(self.root, 0o775)
        self.assertEqual(self.refusal(lambda: f.load_acceptance(root=self.root, today=TODAY, trust=trust_mine)), "ACCEPTANCE_NOT_TRUSTED")
        os.chmod(self.root, 0o755)
        if os.getuid() != 0:  # the default trusts root only
            self.assertEqual(self.refusal(lambda: f.load_acceptance(root=self.root, today=TODAY)), "ACCEPTANCE_NOT_TRUSTED")
        (self.work / "link.json").symlink_to(self.root / "acceptance.json")
        self.assertEqual(self.refusal(lambda: trust_mine(self.work / "link.json", "ACCEPTANCE_NOT_TRUSTED")), "ACCEPTANCE_NOT_TRUSTED")


class UnitStepTests(Fixture):
    def fake_node(self, serial="LABRXA", devtype="usb_device"):
        attributes = {"uevent": "MAJOR=189\nMINOR=5\nDEVTYPE=%s\n" % devtype, "serial": serial + "\n"}
        if os.name == "posix":  # the real attribute reader on a /sys/dev/char-shaped tree
            sysfs = self.work / "sys/189:5"
            sysfs.mkdir(parents=True, exist_ok=True)
            for name, text in attributes.items():
                (sysfs / name).write_text(text, encoding="ascii")
        else:  # "189:5" is no valid Windows file name: the reader is replaced, the path still checked
            def sysfs_text(path, limit):
                self.assertEqual((Path(path).parent.name, Path(path).parent.parent), ("189:5", self.work / "sys"))
                return attributes[Path(path).name].strip()
            patcher = mock.patch.object(f, "_sysfs_text", sysfs_text)
            patcher.start()
            self.addCleanup(patcher.stop)
        return {"sys_char_root": self.work / "sys", "char_node": lambda path: (189, 5) if path.name in ("rtla", "rtlb") else None}

    def prepare(self, receiver="rtla", node=None, today=TODAY):
        return f.prepare(receiver, self.run_dir, self.products, root=self.root, today=today, trust=TRUST, **(node or self.fake_node()))

    def test_prepare_writes_the_serial_of_the_leased_node_and_clears_an_old_picture(self):
        (self.products / "aircraft.json").write_text("{}", encoding="utf-8")
        self.assertEqual(self.prepare(), 0)
        self.assertEqual((self.run_dir / "readsb.env").read_text(encoding="utf-8"), "SRRX_READSB_SERIAL=LABRXA\n")
        self.assertTrue((self.run_dir / "json").is_dir())
        self.assertFalse((self.products / "aircraft.json").exists())
        status = self.status()
        self.assertEqual((status["state"], status["reason"], status["receiver"]), ("STARTING", None, "rtla"))
        self.assertEqual(status["database"]["expires_on"], "2027-01-31")

    def test_prepare_refuses_fail_closed_and_says_why(self):
        cases = [("RECEIVER_NOT_RTL", lambda: self.prepare("hfplus")),
                 ("DATABASE_STALE", lambda: self.prepare(today=TODAY + datetime.timedelta(days=86))),
                 ("DEVICE_SERIAL_UNAVAILABLE", lambda: self.prepare(node=self.fake_node(serial="AIRSPYHF SN:0123"))),
                 ("DEVICE_SERIAL_UNAVAILABLE", lambda: self.prepare(node=self.fake_node(devtype="usb_interface"))),
                 ("DEVICE_SERIAL_UNAVAILABLE", lambda: self.prepare(node=dict(self.fake_node(), char_node=lambda path: None))),
                 ("ACCEPTANCE_MISSING", lambda: (os.unlink(self.root / "acceptance.json"), self.prepare())[1])]
        for code, call in cases:
            with self.subTest(code=code):
                (self.products / "aircraft.json").write_text("{}", encoding="utf-8")
                self.assertEqual(call(), 2)
                self.assertEqual((self.status()["state"], self.status()["reason"]), ("REFUSED", code))
                self.assertFalse((self.run_dir / "readsb.env").exists())
                self.assertFalse((self.products / "aircraft.json").exists())

    def test_server_publishes_atomically_and_never_shows_stale_or_hidden_aircraft(self):
        server = f.Server(self.filter(), "rtla", self.run_dir, self.products, today=lambda: TODAY)
        server.cycle()
        self.assertEqual(self.status()["state"], "WAITING")
        self.engine_json([aircraft(CIVIL), aircraft(DB_PIA), aircraft(RANGE_FIRST, dbFlags=1)])
        server.cycle()
        self.assertEqual([a["hex"] for a in self.published()["aircraft"]], ["4ca9f1"])
        self.assertEqual(self.status()["state"], "RUNNING")
        self.assertEqual(sorted(p.name for p in self.products.iterdir()), ["aircraft.json", "status.json"])  # no temporary left
        everything = (self.products / "aircraft.json").read_text(encoding="utf-8") + (self.products / "status.json").read_text(encoding="utf-8")
        for address in (DB_PIA, RANGE_FIRST):
            self.assertNotIn("%06x" % address, everything)
        self.assertNotIn("messages", self.published())  # readsb's message total counts hidden aircraft too
        # readsb stopped writing: after STALE_S the picture is withdrawn.
        server.clock = lambda: os.stat(self.run_dir / "json/aircraft.json").st_mtime + f.STALE_S + 1
        server.cycle()
        self.assertEqual(self.status()["state"], "STALE")
        self.assertFalse((self.products / "aircraft.json").exists())

    def test_serve_refuses_on_unreadable_output_or_an_expiring_database_and_stops(self):
        flt = self.filter()
        self.engine_json([aircraft(CIVIL)])
        server = f.Server(flt, "rtla", self.run_dir, self.products, today=lambda: TODAY)
        self.assertEqual(server.serve(sleep=lambda s: None, max_cycles=1), 0)
        self.assertEqual(self.status()["state"], "STOPPED")
        self.assertFalse((self.products / "aircraft.json").exists())
        days = iter([TODAY, datetime.date(2027, 2, 1)])
        server = f.Server(flt, "rtla", self.run_dir, self.products, today=lambda: next(days))
        with mock.patch.object(f, "_stop_engine") as stop_engine:
            self.assertEqual(server.serve(sleep=lambda s: self.engine_json([aircraft(CIVIL)], now=s), max_cycles=5), 2)
        stop_engine.assert_called_once()
        self.assertEqual((self.status()["state"], self.status()["reason"]), ("REFUSED", "DATABASE_STALE"))
        self.assertFalse((self.products / "aircraft.json").exists())
        bad = iter(range(10))
        server = f.Server(flt, "rtla", self.run_dir, self.products, today=lambda: TODAY)
        with mock.patch.object(f, "_stop_engine") as stop_engine:
            code = server.serve(sleep=lambda s: (self.run_dir / "json/aircraft.json").write_text("{" * next(bad), encoding="utf-8"),
                                max_cycles=6)
        self.assertEqual((code, self.status()["reason"]), (2, "ENGINE_OUTPUT_UNREADABLE"))
        stop_engine.assert_called_once()

    def test_stop_clears_the_picture_and_keeps_a_refusal_reason(self):
        self.engine_json([aircraft(CIVIL)])
        f.Server(self.filter(), "rtla", self.run_dir, self.products, today=lambda: TODAY).cycle()
        self.assertTrue((self.products / "aircraft.json").exists())
        self.assertEqual(f.stop("rtla", self.products, environ={"SERVICE_RESULT": "success"}), 0)
        self.assertFalse((self.products / "aircraft.json").exists())
        self.assertEqual((self.status()["state"], self.status()["service_result"]), ("STOPPED", "success"))
        self.assertEqual(self.prepare("hfplus"), 2)
        self.assertEqual(f.stop("hfplus", self.products, environ={"SERVICE_RESULT": "exit-code"}), 0)
        self.assertEqual((self.status()["state"], self.status()["reason"]), ("REFUSED", "RECEIVER_NOT_RTL"))
        self.assertEqual(f.stop("rtla", self.work / "absent"), 0)

    def test_run_refuses_before_serving_and_serves_with_an_accepted_record(self):
        self.assertEqual(f.run("hfplus", self.run_dir, self.products, root=self.root, today=TODAY, trust=TRUST), 2)
        self.assertEqual(self.status()["reason"], "RECEIVER_NOT_RTL")
        self.assertEqual(f.run("rtla", self.run_dir, self.products, root=self.work / "absent", today=TODAY, trust=TRUST), 2)
        self.assertEqual(self.status()["reason"], "ACCEPTANCE_MISSING")
        self.engine_json([aircraft(CIVIL), aircraft(DB_LADD)])
        self.assertEqual(f.run("rtla", self.run_dir, self.products, root=self.root, today=TODAY, trust=TRUST, interval=0, max_cycles=1), 0)
        self.assertEqual(self.status()["state"], "STOPPED")

    def test_stop_engine_signals_only_readsb(self):
        proc = self.work / "proc"
        (proc / "4242").mkdir(parents=True)
        (proc / "4242/comm").write_text("readsb\n", encoding="ascii")
        (proc / "4343").mkdir()
        (proc / "4343/comm").write_text("python3\n", encoding="ascii")
        with mock.patch.object(f.os, "kill") as kill:
            self.assertTrue(f._stop_engine({"MAINPID": "4242"}, proc))
            self.assertFalse(f._stop_engine({"MAINPID": "4343"}, proc))
            self.assertFalse(f._stop_engine({"MAINPID": "x"}, proc))
            self.assertFalse(f._stop_engine({}, proc))
        kill.assert_called_once_with(4242, f.signal.SIGTERM)

    @unittest.skipUnless(hasattr(os, "fork"), "fork")
    def test_detach_returns_once_the_child_is_ready_and_fails_if_it_dies_first(self):
        # In a fresh interpreter: the test runner itself is never forked.
        script = ("import sys; sys.path.insert(0, %r); from srrx import adsb_filter as f; import time\n"
                  "def ready_then_work(ready):\n    ready(); time.sleep(0.2); return 0\n"
                  "def dies(ready):\n    raise SystemExit(5)\n"
                  "sys.exit(f._detach(ready_then_work if sys.argv[1] == 'ready' else dies))\n") % str(PROJECT / "software")
        for mode, code in (("ready", 0), ("dies", 2)):
            with self.subTest(mode=mode):
                done = subprocess.run([sys.executable, "-c", script, mode], capture_output=True, timeout=60)
                self.assertEqual(done.returncode, code, done.stderr)


class TemplateTests(unittest.TestCase):
    """The lease template runs exactly these steps; RX-12-readsb pins the same lines offline."""

    def service(self):
        lines = {}
        for line in UNIT.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith(("#", "[")):
                key, _, value = line.partition("=")
                lines.setdefault(key, []).append(value)
        return lines

    def test_readsb_writes_only_into_its_runtime_directory_and_prints_nothing_kept(self):
        service = self.service()
        self.assertEqual(len(service["ExecStart"]), 1)
        argv = service["ExecStart"][0].split()
        self.assertEqual(argv[:2], ["/usr/bin/env", "readsb"])
        self.assertEqual(argv[argv.index("--write-json") + 1], "%t/srrx-lease-readsb-%i/json")
        self.assertEqual(argv[argv.index("--db-file") + 1], (f.ROOT / f.DATABASE_NAME).as_posix())
        self.assertEqual(argv[argv.index("--device") + 1], "${SRRX_READSB_SERIAL}")
        self.assertEqual(argv[argv.index("--net-bind-address") + 1], "127.0.0.1")  # STACK.md:882; no listener without --net
        options = [a for a in argv[2:] if a.startswith("-")]
        self.assertFalse([o for o in options if o.startswith("--net") and o != "--net-bind-address"])
        self.assertFalse({"--enable-biastee", "--write-globe-history", "--write-state", "--dump-beast", "--write-prom", "--heatmap"} & set(options))
        self.assertEqual((service["StandardOutput"], service["StandardError"]), (["null"], ["null"]))
        self.assertEqual(service["EnvironmentFile"], ["-%t/srrx-lease-readsb-%i/" + f.ENV_FILE])
        self.assertEqual(service["RuntimeDirectory"], ["srrx-lease-readsb-%i"])

    def test_filter_steps_parse_with_the_module_cli_and_never_fail_open(self):
        service = self.service()
        steps = {"ExecStartPre": "prepare", "ExecStartPost": "run", "ExecStopPost": "stop"}
        for key, operation in steps.items():
            with self.subTest(key=key):
                self.assertEqual(len(service[key]), 1)
                argv = service[key][0].split()
                self.assertEqual(argv[:7], ["/usr/bin/python3", "-P", "-s", "-B", "-m", "srrx.adsb_filter", operation])
                options = argv[7:]
                self.assertEqual(options[options.index("--receiver") + 1], "%i")
                self.assertEqual(options[options.index("--products") + 1], "/data/products/readsb-%i")
                if operation != "stop":
                    self.assertEqual(options[options.index("--run-dir") + 1], "%t/srrx-lease-readsb-%i")
                calls = []
                with mock.patch.object(f, operation, lambda *a, **k: calls.append((a, k)) or 0):
                    self.assertEqual(f.main([operation] + options), 0)
                self.assertEqual(len(calls), 1)
        self.assertIn("--detach", service["ExecStartPost"][0].split())
        self.assertTrue(any(v.startswith("PYTHONPATH=/opt/srrx/software ") for v in service["Environment"]))


class DecoderPolicyTests(Fixture):
    def test_adsb_public_is_installation_gated_and_never_a_file_plan(self):
        self.assertEqual(decoder_policy.availability()["adsb-public"], "UNAVAILABLE_NO_ACCEPTED_INSTALLATION")
        with mock.patch.object(f, "admin_trust", TRUST), mock.patch.object(f, "utc_today", lambda: TODAY), \
                mock.patch.object(f, "ROOT", self.root):
            self.assertEqual(decoder_policy.availability(adsb_acceptance=self.record)["adsb-public"],
                             "ENGINE_LEASE_ACCEPTED_FILTER_CHECKS_AT_START")
            stale = json.loads(json.dumps(self.record))
            stale["database"]["data_date"] = "2026-01-01"
            self.assertEqual(decoder_policy.availability(adsb_acceptance=stale)["adsb-public"], "UNAVAILABLE_INSTALLATION_NOT_QUALIFIED")
        with mock.patch.object(decoder_policy, "_file", side_effect=AssertionError("must not inspect payload")):
            with self.assertRaisesRegex(decoder_policy.DecoderRefused, "DISABLED"):
                decoder_policy.make_plan("adsb-public", None, None, None)


if __name__ == "__main__":
    unittest.main()
