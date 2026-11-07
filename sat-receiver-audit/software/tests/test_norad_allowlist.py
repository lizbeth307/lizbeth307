"""NORAD allowlist builder: SATCAT name + launch date, GP cross-check, acceptance record.

Every SATCAT row and element set here is synthetic (FIXTURE names, synthetic
catalogue numbers); nothing is fetched. Only the committed STACK targets file
is real, and it holds names and launch dates, never a NORAD id.
"""
import ast
import contextlib
import io
import json
import os
from pathlib import Path
import re
import socket
import stat
import tempfile
import unittest
from unittest import mock

from srrx import norad_allowlist as na
from srrx import orbits
from srrx import scope_policy as sp

ROOT = Path(__file__).resolve().parents[2]
EPOCH = "2026-10-20T06:00:00.123456"


def satcat_row(norad, name, launch, object_id, **changes):
    row = {"OBJECT_NAME": name, "OBJECT_ID": object_id, "NORAD_CAT_ID": norad, "OBJECT_TYPE": "PAY",
           "OPS_STATUS_CODE": "+", "OWNER": "FIX", "LAUNCH_DATE": launch, "LAUNCH_SITE": "FIXS", "DECAY_DATE": "",
           "PERIOD": 101.12, "INCLINATION": 98.59, "APOGEE": 815, "PERIGEE": 808, "RCS": None,
           "DATA_STATUS_CODE": "", "ORBIT_CENTER": "EA", "ORBIT_TYPE": "ORB"}
    row.update(changes)
    return row


ROWS = (satcat_row(90010, "FIXTURE LEO 3", "2023-06-27", "2023-901A"),
        satcat_row(90011, "FIXTURE LEO 3 DEB", "2023-06-27", "2023-901C", OBJECT_TYPE="DEB", OPS_STATUS_CODE=""),
        satcat_row(90012, "FIXTURE LEO 3", "2009-09-17", "2009-901A", OPS_STATUS_CODE="-"),  # an older namesake
        satcat_row(90020, "FIXTURE STATION", "1998-11-20", "1998-901A"),
        satcat_row(90030, "FIXTURE GEO'S 2", "2018-11-15", "2018-901A"),
        satcat_row(400001, "FIXTURE SIX DIGIT", "2026-07-12", "2026-901B"))
TARGETS = {"v": 1, "kind": "srrx_orbit_targets", "targets": [
    {"satcat_name": "FIXTURE STATION", "launch_date": "1998-11-20", "role": "ISS"},
    {"satcat_name": "FIXTURE LEO 3", "launch_date": "2023-06-27", "role": "LRPT", "name": "Fixture LEO N3"},
    {"satcat_name": "FIXTURE GEO'S 2", "launch_date": "2018-11-15", "role": "QO100"},
    {"satcat_name": "FIXTURE SIX DIGIT", "launch_date": "2026-07-12", "role": "OTHER"}]}


def csv_bytes(rows, header=na.SATCAT_FIELDS):
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join("" if row[field] is None else str(row[field]) for field in header))
    return ("\r\n".join(lines) + "\r\n").encode("ascii")


def omm(norad, object_id, epoch=EPOCH, **changes):
    value = {"OBJECT_NAME": "GP NAME %d" % norad, "OBJECT_ID": object_id, "EPOCH": epoch,
             "MEAN_MOTION": 14.2412, "ECCENTRICITY": 0.00071, "INCLINATION": 98.71, "RA_OF_ASC_NODE": 120.5,
             "ARG_OF_PERICENTER": 87.25, "MEAN_ANOMALY": 272.9, "EPHEMERIS_TYPE": 0, "CLASSIFICATION_TYPE": "U",
             "NORAD_CAT_ID": norad, "ELEMENT_SET_NO": 999, "REV_AT_EPOCH": 1234, "BSTAR": 0.00012,
             "MEAN_MOTION_DOT": 1.2e-06, "MEAN_MOTION_DDOT": 0.0}
    value.update(changes)
    return value


def gp_bytes(*records):
    return json.dumps(list(records)).encode("ascii")


GP = (gp_bytes(omm(90010, "2023-901A"), omm(90020, "1998-901A", MEAN_MOTION=15.5)),
      gp_bytes(omm(90030, "2018-901A", MEAN_MOTION=1.0027), omm(400001, "2026-901B")))


def admin_lstat(owner=0):
    """lstat with the given owner for files and root-owned 0755 directories; patched as scope_policy._lstat."""
    real = os.lstat

    def fake(path):
        info = real(path)
        if stat.S_ISREG(info.st_mode):
            uid, mode = owner, stat.S_IFREG | 0o644
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

    def build(self, targets=TARGETS, rows=ROWS, gp=GP, satcat=None):
        return na.build(targets, [csv_bytes(rows)] if satcat is None else satcat, list(gp))

    def refused(self, code, call, *args):
        with self.assertRaises(na.AllowlistRefused) as caught:
            call(*args)
        self.assertEqual(str(caught.exception), code)


class BuildTests(Fixture):
    def test_name_and_launch_date_select_one_payload_and_the_allowlist_is_valid(self):
        result = self.build()
        accepted = orbits.allowlist(json.loads(result["allowlist"]))
        self.assertEqual(sorted(accepted), [90010, 90020, 90030, 400001])  # not the namesake or the debris
        self.assertEqual(accepted[90010], {"norad_id": 90010, "name": "Fixture LEO N3", "role": "LRPT"})
        self.assertEqual(accepted[90020]["name"], "FIXTURE STATION")  # display name defaults to the SATCAT name
        self.assertEqual([target["norad_id"] for target in json.loads(result["allowlist"])["targets"]],
                         [90010, 90020, 90030, 400001])
        self.assertEqual(result["allowlist"], self.build(rows=tuple(reversed(ROWS)), gp=tuple(reversed(GP)))["allowlist"])
        as_json = json.dumps(list(ROWS)).encode("ascii")
        self.assertEqual(self.build(satcat=[as_json])["allowlist"], result["allowlist"])  # CelesTrak JSON form
        self.assertEqual(self.build(satcat=[csv_bytes(ROWS), as_json])["allowlist"], result["allowlist"])  # overlap
        self.assertEqual(result["template"], {"v": 1, "kind": na.ACCEPTANCE_KIND, "format": na.ALLOWLIST_FORMAT,
                                              "sha256": result["sha256"], "evidence_id": na.EVIDENCE_PLACEHOLDER})
        report = result["report"]
        self.assertFalse(report["accepted"])
        target = next(item for item in report["targets"] if item["norad_id"] == 90010)
        self.assertEqual((target["object_id"], target["ops_status_code"], target["gp_object_name"],
                          target["gp_epoch_utc"]), ("2023-901A", "+", "GP NAME 90010", EPOCH + "Z"))
        self.assertEqual([source["kind"] for source in report["sources"]], ["satcat", "gp", "gp"])
        self.assertNotIn(str(self.root), json.dumps(report))

    def test_every_doubt_refuses_the_whole_build(self):
        target = TARGETS["targets"][1]
        cases = {
            "launch date": (dict(rows=[row for row in ROWS if row["NORAD_CAT_ID"] != 90010]), "SATCAT_NO_MATCH:1"),
            "two objects": (dict(rows=ROWS + (satcat_row(90013, target["satcat_name"], target["launch_date"],
                                                        "2023-901B"),)), "SATCAT_AMBIGUOUS:1"),
            "copies disagree": (dict(rows=ROWS + (dict(ROWS[0], OPS_STATUS_CODE="-"),)), "SATCAT_AMBIGUOUS:1"),
            "rocket body": (dict(rows=(dict(ROWS[0], OBJECT_TYPE="R/B"),) + ROWS[1:]), "SATCAT_NOT_PAYLOAD:1"),
            "decayed": (dict(rows=(dict(ROWS[0], DECAY_DATE="2026-01-01"),) + ROWS[1:]), "SATCAT_DECAYED:1"),
            "status D": (dict(rows=(dict(ROWS[0], OPS_STATUS_CODE="D"),) + ROWS[1:]), "SATCAT_DECAYED:1"),
            "cospar": (dict(rows=(dict(ROWS[0], OBJECT_ID="2023-91A"),) + ROWS[1:]), "SATCAT_ROW:1"),
            "norad zero": (dict(rows=(dict(ROWS[0], NORAD_CAT_ID=0),) + ROWS[1:]), "SATCAT_ROW:1"),
            "norad seven digits": (dict(rows=(dict(ROWS[0], NORAD_CAT_ID=1000000),) + ROWS[1:]), "SATCAT_ROW:1"),
            "norad not integer": (dict(satcat=[json.dumps([dict(ROWS[0], NORAD_CAT_ID=90010.0)] +
                                                          list(ROWS[1:])).encode()]), "SATCAT_ROW:1"),
            "gp missing": (dict(gp=GP[:1]), "GP_MISSING:2"),
            "gp other object": (dict(gp=(gp_bytes(omm(90010, "2023-901C"), omm(90020, "1998-901A")), GP[1])),
                                "GP_OBJECT_ID_MISMATCH:1"),
            "gp contradiction": (dict(gp=GP + (gp_bytes(omm(90010, "2023-901B", epoch="2026-10-21T06:00:00")),)),
                                 "GP_CONTRADICTION"),
            "gp same epoch": (dict(gp=GP + (gp_bytes(omm(90010, "2023-901A", MEAN_MOTION=14.5)),)), "GP_CONTRADICTION"),
            "gp classified": (dict(gp=GP + (gp_bytes(omm(90099, "2023-901D", CLASSIFICATION_TYPE="C")),)),
                              "GP_SCHEMA:2"),
            "no gp file": (dict(gp=()), "GP_FILES"),
            "satcat header": (dict(satcat=[csv_bytes(ROWS)[20:]]), "SATCAT_SCHEMA"),
            "satcat short row": (dict(satcat=[csv_bytes(ROWS) + b"FIXTURE,1\r\n"]), "SATCAT_SCHEMA"),
            "satcat boolean": (dict(satcat=[json.dumps([dict(ROWS[0], RCS=True)]).encode()]), "SATCAT_SCHEMA"),
            "satcat extra key": (dict(satcat=[json.dumps([dict(ROWS[0], URL="x")]).encode()]), "SATCAT_SCHEMA"),
            "no satcat file": (dict(satcat=[]), "SATCAT_FILES"),
        }
        for name, (kwargs, code) in cases.items():
            with self.subTest(case=name):
                self.refused(code, self.build, *(kwargs.get(key, default) for key, default in
                                                 (("targets", TARGETS), ("rows", ROWS), ("gp", GP), ("satcat", None))))
        with mock.patch.object(na, "MAX_SATCAT_BYTES", 64):
            self.refused("SATCAT_SIZE_LIMIT:0", self.build)
        with mock.patch.object(na, "MAX_SATCAT_ROWS", 3):
            self.refused("SATCAT_ROW_LIMIT", self.build)

    def test_targets_request_is_strict_and_never_carries_an_id(self):
        def request(**changes):
            entry = dict(TARGETS["targets"][1], **changes)
            return dict(TARGETS, targets=[entry] + TARGETS["targets"][2:])
        bad_entries = (request(norad_id=90010), request(launch_date="2023-02-30"), request(launch_date="27.06.2023"),
                       request(role="WEATHER"), request(name="Метеор"), request(satcat_name=" FIXTURE LEO 3"),
                       request(satcat_name="x" * 65), request(launch_date=20230627))
        for value in bad_entries:
            with self.subTest(value=value["targets"][0]):
                self.refused("TARGET_SCHEMA:0", na.targets, value)
        missing = dict(TARGETS, targets=[{"satcat_name": "FIXTURE LEO 3", "role": "LRPT"}])
        self.refused("TARGET_SCHEMA:0", na.targets, missing)
        for value in (dict(TARGETS, v=2), dict(TARGETS, kind="srrx_orbit_allowlist"), dict(TARGETS, targets=[]),
                      dict(TARGETS, extra=1), [TARGETS], dict(TARGETS, targets=[{}] * 257)):
            with self.subTest(value=str(value)[:60]):
                self.refused("TARGETS_SCHEMA", na.targets, value)
        self.refused("TARGET_DUPLICATE:1", na.targets,
                     dict(TARGETS, targets=[TARGETS["targets"][1], dict(TARGETS["targets"][1], role="OTHER")]))
        self.refused("TARGETS_QO100", na.targets,
                     dict(TARGETS, targets=TARGETS["targets"] + [dict(TARGETS["targets"][0], launch_date="1999-01-01",
                                                                      role="QO100")]))

    def test_committed_stack_targets_file_is_valid_and_holds_no_ids(self):
        path = ROOT / "software/config/orbit-targets.json"
        text = path.read_text(encoding="utf-8")
        request = na.targets(json.loads(text))
        self.assertNotIn("norad", text.lower())
        self.assertIsNone(re.search(r"\d{5}", text))  # no catalogue number of any length >= 5 digits
        roles = [target["role"] for target in request]
        self.assertEqual(roles.count("QO100"), 1)
        self.assertEqual(roles.count("ISS"), 1)
        self.assertEqual({target["name"] for target in request if target["role"] == "LRPT"},
                         {"Meteor-M N2-3", "Meteor-M N2-4"})
        self.assertEqual(len(request), 11)

    def test_resolve_lists_the_gp_query_and_fetches_nothing(self):
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network used")), \
                mock.patch.object(socket, "create_connection", side_effect=AssertionError("network used")):
            matches, sources = na.resolve(TARGETS, [csv_bytes(ROWS)])
            self.build()
        self.assertEqual([match["gp_query"] for match in matches],
                         [na.GP_QUERY % norad for norad in (90020, 90010, 90030, 400001)])
        self.assertEqual(len(sources), 1)
        tree = ast.parse(Path(na.__file__).read_text(encoding="utf-8"))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
                    for alias in node.names}
        imported |= {node.module.split(".")[0] for node in ast.walk(tree)
                     if isinstance(node, ast.ImportFrom) and node.module and node.level == 0}
        self.assertFalse(imported & {"socket", "urllib", "http", "ssl", "requests", "ftplib", "subprocess"})


class AcceptanceTests(Fixture):
    def outputs(self):
        folder = self.root / "out"
        folder.mkdir()
        na.write_outputs(self.build(), folder)
        return folder

    def record(self, folder, **changes):
        template = json.loads((folder / na.TEMPLATE_FILE).read_text(encoding="utf-8"))
        path = folder / "orbit-allowlist.acceptance.json"
        path.write_text(json.dumps(dict(template, evidence_id="admin/orbit-allowlist-001", **changes)),
                        encoding="utf-8")
        return path

    def test_acceptance_record_binds_the_exact_allowlist_bytes(self):
        folder = self.outputs()
        allowlist = folder / na.ALLOWLIST_FILE
        record = self.record(folder)
        with mock.patch.object(sp, "_lstat", side_effect=admin_lstat()):
            accepted = na.load_accepted(allowlist, record)
            self.assertEqual(accepted, orbits.load_allowlist(allowlist))
            self.refused("ACCEPTANCE_SCHEMA", na.load_accepted, allowlist, folder / na.TEMPLATE_FILE)  # placeholder
            for change in ({"format": "srrx_orbit_targets"}, {"sha256": "A" * 64}, {"v": True}):
                with self.subTest(change=change):
                    self.refused("ACCEPTANCE_SCHEMA", na.load_accepted, allowlist, self.record(folder, **change))
            record = self.record(folder)
            self.refused("ALLOWLIST_NOT_REGULAR_FILE", na.load_accepted, folder, record)
            self.refused("ALLOWLIST_UNAVAILABLE", na.load_accepted, folder / "missing.json", record)
            allowlist.write_bytes(allowlist.read_bytes() + b"\n")
            self.refused("ALLOWLIST_SHA256_MISMATCH", na.load_accepted, allowlist, record)
        with mock.patch.object(sp, "_lstat", side_effect=admin_lstat(owner=1000)):
            self.refused("ACCEPTANCE_RECORD_REQUIRED", na.load_accepted, allowlist, record)
        self.assertIs(sp._lstat, os.lstat)

    def test_cli_resolve_build_and_check(self):
        targets, satcat, gp = self.root / "targets.json", self.root / "satcat.csv", []
        targets.write_text(json.dumps(TARGETS), encoding="utf-8")
        satcat.write_bytes(csv_bytes(ROWS))
        for index, blob in enumerate(GP):
            gp.append(self.root / ("gp%d.json" % index))
            gp[-1].write_bytes(blob)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(na.main(["resolve", "--targets", str(targets), "--satcat", str(satcat)]), 0)
        self.assertEqual([item["norad_id"] for item in json.loads(out.getvalue())["targets"]],
                         [90020, 90010, 90030, 400001])
        folder = self.root / "out"
        folder.mkdir()
        argv = ["build", "--targets", str(targets), "--satcat", str(satcat), "--output-dir", str(folder)]
        argv += [item for path in gp for item in ("--gp", str(path))]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(na.main(argv), 0)
        self.assertEqual(sorted(p.name for p in folder.iterdir()),
                         sorted((na.ALLOWLIST_FILE, na.TEMPLATE_FILE, na.REPORT_FILE)))
        for args, code in ((argv, "OUTPUT_EXISTS"), (argv[:-2], "GP_MISSING:2"),
                           (["resolve", "--targets", str(self.root / "none.json"), "--satcat", str(satcat)],
                            "INPUT_UNAVAILABLE")):
            error = io.StringIO()
            with self.subTest(code=code), contextlib.redirect_stderr(error):
                self.assertEqual(na.main(args), 2)
                self.assertEqual(error.getvalue(), "srrx.norad_allowlist: refused: %s\n" % code)
        record = self.record(folder)
        out = io.StringIO()
        with mock.patch.object(sp, "_lstat", side_effect=admin_lstat()), contextlib.redirect_stdout(out):
            self.assertEqual(na.main(["check", "--allowlist", str(folder / na.ALLOWLIST_FILE), "--record",
                                      str(record)]), 0)
        self.assertEqual(json.loads(out.getvalue()), {"accepted": True, "targets": 4,
                                                      "roles": {"ISS": 1, "LRPT": 1, "OTHER": 1, "QO100": 1}})


if __name__ == "__main__":
    unittest.main()
