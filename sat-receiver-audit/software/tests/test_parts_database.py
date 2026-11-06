"""Parts database (design/parts/parts.json, tools/build_parts.py) in the offline host regression.

The committed database must pass its checker with current outputs, and the checker must fail
closed on the defects it exists to catch. A database entry is a procurement record, never
hardware evidence: physical gates stay OPEN.
"""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

BASE = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, BASE / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parts = load("srrx_tool_build_parts", "tools/build_parts.py")


def part(db, pid):
    return next(p for p in db["parts"] if p["id"] == pid)


class PartsDatabaseTest(unittest.TestCase):
    def errors_after(self, change):
        model = parts.Model()
        change(model.db)
        model.check()
        return model.errors

    def test_committed_database_and_outputs_are_current(self):
        run = subprocess.run([sys.executable, "tools/build_parts.py", "--check"], cwd=BASE, capture_output=True,
                             text=True, encoding="utf-8", errors="replace")
        self.assertEqual(run.returncode, 0, run.stdout[-2000:] + run.stderr[-2000:])
        self.assertIn("Parts database PASS (checked)", run.stdout)

    def test_every_ref_is_in_exactly_one_entry(self):
        model = parts.Model()
        model.check()
        self.assertEqual(model.errors, [])
        self.assertEqual(set(model.part_of), set(model.comps))
        self.assertEqual(len(model.comps), sum(len(p["refs"]) for p in model.db["parts"]))

    def test_board_parts_have_vendored_footprints(self):
        model = parts.Model()
        model.check()
        for ref, p in model.part_of.items():
            if p["mount"] in parts.PCB_MOUNTS:
                self.assertTrue(p.get("footprint"), ref)
                self.assertEqual(model.comps[ref][1].get("footprint"), p["footprint"], ref)

    def test_ref_assigned_twice_or_missing_fails(self):
        def twice(db):
            part(db, "BZ-CPT-1207-3TH")["refs"].append("ENC301")
        self.assertTrue(any("ENC301 assigned twice" in e for e in self.errors_after(twice)))

        def missing(db):
            part(db, "BZ-CPT-1207-3TH")["refs"].remove("BZ301")
        self.assertTrue(any("BZ301 has no parts-database entry" in e for e in self.errors_after(missing)))

    def test_unexplained_pad_and_missing_pin_fail(self):
        def wrong_footprint(db):
            part(db, "BZ-CPT-1207-3TH")["footprint"] = "Package_TO_SOT_SMD:SOT-23"
        errors = self.errors_after(wrong_footprint)
        self.assertTrue(any(e.startswith("BZ301: pins") or e.startswith("BZ301: pads") for e in errors), errors)

    def test_purchased_part_needs_alternate_or_single_source(self):
        def strip(db):
            p = part(db, "ENC-PEC11R-4220F-S0024")
            p.pop("alternates", None)
            p.pop("single_source", None)
        self.assertTrue(any("needs an alternate or a single_source reason" in e for e in self.errors_after(strip)))

    def test_sku_must_be_in_a_snapshot_with_the_same_mpn(self):
        def unknown(db):
            part(db, "J-BNC-PANEL")["sku"]["digikey"] = "NOT-A-SNAPSHOT-KEY"
        self.assertTrue(any("has no snapshot entry" in e for e in self.errors_after(unknown)))

        def other_mpn(db):
            part(db, "J-BNC-PANEL")["mpn"] = "999999"
        self.assertTrue(any("snapshot shows MPN" in e for e in self.errors_after(other_mpn)))

    def test_passive_value_is_compared_with_the_distributor_attributes(self):
        def wrong_value(db):
            cap = next(p for p in db["parts"] if p.get("kind") == "capacitor" and (p.get("sku") or {}).get("lcsc"))
            res = next(p for p in db["parts"] if p.get("kind") == "resistor" and (p.get("sku") or {}).get("lcsc"))
            res["sku"]["lcsc"] = cap["sku"]["lcsc"]
            res["mpn"] = cap["mpn"]
        self.assertTrue(any("resistance" in e for e in self.errors_after(wrong_value)))

    def test_unknown_key_and_mount_fail(self):
        def typo(db):
            part(db, "BZ-CPT-1207-3TH")["footprnt"] = "x"
            part(db, "J-BNC-PANEL")["mount"] = "glued"
        errors = self.errors_after(typo)
        self.assertTrue(any("unknown key footprnt" in e for e in errors))
        self.assertTrue(any("unknown mount glued" in e for e in errors))

    def test_harness_family_items_are_snapshot_listings_with_matching_footprints(self):
        model = parts.Model()
        model.check()
        items = model.family_items()
        self.assertTrue(items)
        for fam, n, role, item in items:
            self.assertIn(item["sku"]["lcsc"], model.lcsc, (fam["id"], n, role))

        def wrong_pins(db):
            db["harness_families"][0]["sizes"][0]["header_top"]["footprint"] = "Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical"
        self.assertTrue(any("is not a KiCad Lib:Name with 2 contacts" in e for e in self.errors_after(wrong_pins)))

        def no_sku(db):
            db["harness_families"][0]["sizes"][0]["housing"]["sku"] = {"lcsc": "C0"}
        self.assertTrue(any("lcsc SKU C0 has no snapshot entry" in e for e in self.errors_after(no_sku)))

    def test_tbd_needs_a_reason_and_keeps_the_part_open(self):
        model = parts.Model()
        model.check()
        cov = model.coverage(parts.prepare_module())
        for item in cov["tbd"]:
            self.assertTrue(item["reason"].strip(), item["part"])
        self.assertEqual(cov["board_refs"], cov["board_refs_with_footprint"])


if __name__ == "__main__":
    unittest.main()
