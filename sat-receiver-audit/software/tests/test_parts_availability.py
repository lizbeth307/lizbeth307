"""LCSC availability snapshots (tools/check_parts_availability.py) in the offline host regression.

The JLCPCB search is stubbed: no test opens a socket (tools/run_tests_offline.py denies Internet
sockets as well). The full re-read must stay byte-identical to the snapshot committed at 72ee71b,
and a partial snapshot (--codes/--out) must hold only the listed codes, with distributor LCSC and
the same row schema, under its enforced name. A snapshot is a dated distributor reading, never
hardware evidence: physical gates stay OPEN.
"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

BASE = Path(__file__).resolve().parents[2]
# Written by the full re-read (no --codes) before the partial option existed.
COMMITTED = "design/parts/snapshots/2026-11-06-lcsc.json"
PARTIAL = "design/parts/snapshots/2026-11-08-w2-parts-tool-lcsc.json"


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, BASE / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


avail = load("srrx_tool_check_parts_availability", "tools/check_parts_availability.py")
parts = load("srrx_tool_build_parts_for_snapshots", "tools/build_parts.py")
# JLC library class of a snapshot row -> (componentLibraryType, preferredComponentFlag) of the search API.
LIBRARY = {"basic": ("base", False), "extended": ("expand", False), "preferred": ("expand", True)}


def committed():
    return json.loads((BASE / COMMITTED).read_text(encoding="utf-8"))


def api_hit(code, row):
    """The search-API component that record() turns back into this snapshot row."""
    lib, preferred = LIBRARY.get(row["jlc_library"], (row["jlc_library"], False))
    return {"componentCode": code, "componentModelEn": row["mpn"], "componentBrandEn": row["manufacturer"],
            "componentSpecificationEn": row["package"], "describe": row["description"],
            "attributes": [{"attribute_name_en": k, "attribute_value_name": v} for k, v in row["attributes"].items()]
            + [{"attribute_name_en": "Empty", "attribute_value_name": "-"}],
            "stockCount": row["stock"], "componentLibraryType": lib, "preferredComponentFlag": preferred,
            "componentPrices": [{"startNumber": n, "productPrice": p} for n, p in row["price_usd"]],
            "lcscGoodsUrl": row["url"], "dataManualUrl": row["datasheet"]}


class FakeSearch:
    """Stands in for query(): answers from snapshot rows and records every code asked for."""

    def __init__(self, rows):
        self.rows, self.asked = rows, []

    def query(self, code):
        self.asked.append(code)
        return api_hit(code, self.rows[code]) if code in self.rows else None

    def utc_now(self):
        return self.rows[self.asked[-1]]["fetched_utc"]


def database(code_list):
    """A parts.json that names the codes in every place codes() reads them from, with one duplicate."""
    family = {"id": "FAM", "sizes": []}
    db = {"parts": [{"id": "NO-SKU", "sku": {}}], "harness_families": [family]}
    for i, code in enumerate(code_list):
        slot = i % 5
        if slot == 0:
            db["parts"].append({"id": f"P{i}", "sku": {"lcsc": code, "digikey": "X-ND"}})
        elif slot == 1:
            db["parts"][-1].setdefault("alternates", []).append({"mpn": "ALT", "sku": {"lcsc": code}})
        elif slot == 2:
            db["parts"][-1].setdefault("extras", []).append({"item": "extra", "sku": {"lcsc": code}})
        elif slot == 3:
            family["sizes"].append({"header_top": {"sku": {"lcsc": code}}, "housing": {"sku": {}}})
        elif "terminal" not in family:
            family["terminal"] = {"sku": {"lcsc": code}}
        else:
            family["sizes"].append({"header_side": {"sku": {"lcsc": code}}})
    if code_list:
        db["parts"].append({"id": "DUP", "sku": {"lcsc": code_list[0]}})
    return db


class SnapshotCase(unittest.TestCase):
    def project(self, code_list):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name).resolve() / "sat-receiver-audit"
        (root / "design/parts").mkdir(parents=True)
        (root / "design/parts/parts.json").write_text(json.dumps(database(code_list)), encoding="utf-8")
        return root

    def run_tool(self, root, search, *argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(avail, "ROOT", root), mock.patch.object(avail, "query", search.query), \
                mock.patch.object(avail, "utc_now", search.utc_now), mock.patch.object(avail, "PAUSE_S", 0), \
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("network used")), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = avail.main(list(argv))
            except SystemExit as stop:
                code = stop.code
        return code, stdout.getvalue(), stderr.getvalue()

    @staticmethod
    def written(root):
        return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


class FullSnapshotTest(SnapshotCase):
    def test_default_run_reproduces_the_committed_snapshot_byte_for_byte(self):
        golden = (BASE / COMMITTED).read_bytes()
        snap = json.loads(golden)
        root = self.project(sorted(snap["entries"], reverse=True))
        search = FakeSearch(snap["entries"])
        code, out, err = self.run_tool(root, search, "--date", snap["date"])
        self.assertEqual(code, 0, err)
        self.assertEqual((root / COMMITTED).read_bytes(), golden)
        self.assertEqual(search.asked, sorted(snap["entries"]))
        self.assertEqual(out, f"{len(snap['entries'])} LCSC SKUs written to {COMMITTED}; not found: []\n")
        self.assertEqual(self.written(root), ["design/parts/parts.json", COMMITTED])

    def test_default_run_lists_codes_the_search_does_not_return(self):
        rows = committed()["entries"]
        found = sorted(rows)[:3]
        root = self.project(["C1"] + found)
        code, out, err = self.run_tool(root, FakeSearch(rows), "--date", "2026-11-09")
        self.assertEqual(code, 1, err)
        snap = json.loads((root / "design/parts/snapshots/2026-11-09-lcsc.json").read_text(encoding="utf-8"))
        self.assertEqual(snap["not_found"], ["C1"])
        self.assertEqual(snap["entries"], {c: rows[c] for c in found})
        self.assertEqual(set(snap), set(committed()))
        self.assertIn("not found: ['C1']", out)


class PartialSnapshotTest(SnapshotCase):
    def test_codes_reads_and_writes_only_the_listed_codes(self):
        full = committed()
        rows = full["entries"]
        names = sorted(rows)[:6]
        wanted = sorted([names[3], names[1]])
        root = self.project(names)
        search = FakeSearch(rows)
        code, out, err = self.run_tool(root, search, "--date", "2026-11-08", "--codes", f" {wanted[1]},{wanted[0]} ,{wanted[1]}",
                                       "--out", str(root / PARTIAL))
        self.assertEqual(code, 0, err)
        self.assertEqual(search.asked, wanted)
        text = (root / PARTIAL).read_text(encoding="utf-8")
        snap = json.loads(text)
        self.assertEqual(text, json.dumps(snap, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
        self.assertEqual((snap["distributor"], snap["date"], snap["scope"]), ("LCSC", "2026-11-08", "partial"))
        self.assertEqual(snap["requested_codes"], wanted)
        self.assertEqual(snap["not_found"], [])
        # Same row schema and values as the full re-read of the same search answers.
        self.assertEqual(snap["entries"], {c: rows[c] for c in wanted})
        self.assertEqual(set(snap) - {"scope", "requested_codes"}, set(full))
        for key in ("schema", "source", "tool"):
            self.assertEqual(snap[key], full[key], key)
        self.assertEqual(self.written(root), ["design/parts/parts.json", PARTIAL])
        self.assertIn(f"2 LCSC SKUs written to {PARTIAL}; not found: []", out)
        self.assertNotIn("not yet named", out)

    def test_codes_not_in_the_database_are_read_and_named(self):
        rows = committed()["entries"]
        names = sorted(rows)
        root = self.project(names[:2])
        code, out, err = self.run_tool(root, FakeSearch(rows), "--date", "2026-11-08", "--codes", f"{names[0]},{names[5]},C1",
                                       "--out", str(root / PARTIAL))
        self.assertEqual(code, 1, err)
        snap = json.loads((root / PARTIAL).read_text(encoding="utf-8"))
        self.assertEqual(set(snap["entries"]), {names[0], names[5]})
        self.assertEqual(snap["not_found"], ["C1"])
        self.assertIn(f"not yet named by any parts.json entry: {sorted(['C1', names[5]])}", out)

    def test_out_resolves_against_the_current_directory(self):
        rows = committed()["entries"]
        code_ = sorted(rows)[0]
        root = self.project([code_])
        for cwd, rel in ((root, PARTIAL), (root.parent, "sat-receiver-audit/" + PARTIAL)):
            with self.subTest(cwd=cwd.name), contextlib.chdir(cwd):
                (root / PARTIAL).unlink(missing_ok=True)
                code, out, err = self.run_tool(root, FakeSearch(rows), "--date", "2026-11-08", "--codes", code_, "--out", rel)
                self.assertEqual(code, 0, err)
                self.assertEqual(set(json.loads((root / PARTIAL).read_text(encoding="utf-8"))["entries"]), {code_})
                self.assertIn(f"written to {PARTIAL}", out)

    def test_out_name_is_enforced_before_any_read(self):
        code_ = sorted(committed()["entries"])[0]
        refused = ("design/parts/snapshots/2026-11-08-lcsc.json",                 # the full re-read's name
                   "design/parts/snapshots/2026-11-08-w2--lcsc.json",
                   "design/parts/snapshots/2026-11-08-w2-lcsc.json",
                   "design/parts/snapshots/2026-11-08-w2-gr-1-manual.json",
                   "design/parts/snapshots/2026-11-08-w2-gr_1-lcsc.json",
                   "design/parts/snapshots/2026-11-08-w3-gr-1-lcsc.json",
                   "design/parts/snapshots/2026-11-09-w2-gr-1-lcsc.json",          # not the --date
                   "design/parts/snapshots/sub/2026-11-08-w2-gr-1-lcsc.json",
                   "design/parts/2026-11-08-w2-gr-1-lcsc.json",
                   "build/2026-11-08-w2-gr-1-lcsc.json",
                   "../2026-11-08-w2-gr-1-lcsc.json")
        root = self.project([code_])
        for rel in refused:
            with self.subTest(out=rel):
                search = FakeSearch(committed()["entries"])
                code, out, err = self.run_tool(root, search, "--date", "2026-11-08", "--codes", code_, "--out", str(root / rel))
                self.assertEqual(code, 2)
                self.assertEqual(search.asked, [])
                self.assertIn("error: --out ", err)
        self.assertEqual(self.written(root.parent), ["sat-receiver-audit/design/parts/parts.json"])

    def test_partial_date_must_be_iso(self):
        code_ = sorted(committed()["entries"])[0]
        root = self.project([code_])
        for date in ("20261108", "2026-11-8", "2026-02-30", "08.11.2026"):
            with self.subTest(date=date):
                search = FakeSearch(committed()["entries"])
                code, out, err = self.run_tool(root, search, "--date", date, "--codes", code_,
                                               "--out", str(root / f"design/parts/snapshots/{date}-w2-gr-1-lcsc.json"))
                self.assertEqual(code, 2)
                self.assertEqual(search.asked, [])
                self.assertIn("error: --date", err)
                self.assertIn("YYYY-MM-DD", err)
        self.assertEqual(self.written(root), ["design/parts/parts.json"])

    def test_codes_must_be_lcsc_codes_and_go_with_out(self):
        root = self.project(["C1"])
        for codes in ("", "C1,,C2", "X123", "c123", "C12a", "C 12", "C1;C2"):
            with self.subTest(codes=codes):
                search = FakeSearch({})
                code, out, err = self.run_tool(root, search, "--date", "2026-11-08", "--codes", codes, "--out", str(root / PARTIAL))
                self.assertEqual(code, 2)
                self.assertEqual(search.asked, [])
                self.assertIn("error: --codes: not an LCSC C-code", err)
        for extra in (("--codes", "C1"), ("--out", str(root / PARTIAL))):
            with self.subTest(alone=extra[0]):
                search = FakeSearch({})
                code, out, err = self.run_tool(root, search, "--date", "2026-11-08", *extra)
                self.assertEqual(code, 2)
                self.assertEqual(search.asked, [])
                self.assertIn("error: --codes and --out go together", err)
        self.assertEqual(self.written(root), ["design/parts/parts.json"])

    def test_build_parts_takes_partial_rows_as_lcsc_and_the_later_list_entry_wins(self):
        rows = committed()["entries"]
        code_ = sorted(rows)[0]
        root = self.project([code_])
        partial_rows = {code_: dict(rows[code_], stock=5)}
        full_rows = {code_: dict(rows[code_], stock=7)}
        self.assertEqual(self.run_tool(root, FakeSearch(partial_rows), "--date", "2026-11-08", "--codes", code_,
                                       "--out", str(root / PARTIAL))[0], 0)
        self.assertEqual(self.run_tool(root, FakeSearch(full_rows), "--date", "2026-11-09")[0], 0)
        full = "design/parts/snapshots/2026-11-09-lcsc.json"
        with mock.patch.object(parts, "ROOT", root):
            lcsc, manual, dates = parts.load_snapshots({"snapshots": [PARTIAL]})
            self.assertEqual((lcsc[code_]["stock"], manual, dates), (5, {}, ["2026-11-08"]))
            lcsc, manual, dates = parts.load_snapshots({"snapshots": [PARTIAL, full]})
            self.assertEqual((lcsc[code_]["stock"], dates), (7, ["2026-11-08", "2026-11-09"]))
            # List order, not the date, decides: INT appends its full re-read last.
            lcsc, manual, dates = parts.load_snapshots({"snapshots": [full, PARTIAL]})
            self.assertEqual(lcsc[code_]["stock"], 5)


if __name__ == "__main__":
    unittest.main()
