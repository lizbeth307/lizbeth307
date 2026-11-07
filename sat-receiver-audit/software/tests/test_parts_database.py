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

    def test_unexplained_pad_fails(self):
        # ENC301 explains the push-switch pads S1/S2 in unused_pads; without that entry they are unexplained pads.
        def drop_reason(db):
            part(db, "ENC-PEC11R-4220F-S0024")["unused_pads"].pop("S1")
        errors = self.errors_after(drop_reason)
        self.assertTrue(any(e.startswith("ENC301: pads ['S1']") and "neither graph pins nor listed in unused_pads" in e for e in errors), errors)
        self.assertFalse(any(e.startswith("ENC301: pins") for e in errors), errors)

    def test_missing_pin_fails(self):
        def wrong_footprint(db):
            # SOT-23 has pads 1-3: BZ301 pins without a pad, and no extra pad.
            part(db, "BZ-CPT-1207-3TH")["footprint"] = "Package_TO_SOT_SMD:SOT-23"
        errors = self.errors_after(wrong_footprint)
        self.assertTrue(any(e.startswith("BZ301: pins") and "have no pad" in e for e in errors), errors)

    def test_stale_unused_pad_fails(self):
        def stale(db):
            part(db, "ENC-PEC11R-4220F-S0024")["unused_pads"]["A"] = "pin A is a graph pin, not an unused pad"
        errors = self.errors_after(stale)
        self.assertTrue(any(e.startswith("ENC301: unused_pads ['A']") for e in errors), errors)

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
        prep = parts.prepare_module()
        cov = model.coverage(prep)
        self.assertTrue(cov["tbd"])
        for item in cov["tbd"]:
            self.assertTrue(item["reason"].strip(), item["part"])
        self.assertEqual(cov["board_refs"], cov["board_refs_with_footprint"])
        model.graph_texts()  # writes the part fields into the in-memory graphs
        bom = {r["part"]: r for r in model.bom(prep) if r["section"] != "extra"}
        jlc_refs = {ref for row in model.jlc_rows(prep) for ref in row["Designator"].split(",")}
        tbd_parts = [p for p in model.db["parts"] if p.get("tbd")]
        for p in tbd_parts:
            for ref in p["refs"]:
                c = model.comps[ref][1]
                # No confirmed part number reaches the graph, KiCad or the JLC assembly list.
                for field in ("mpn", "manufacturer", "lcsc", "alt_mpn"):
                    self.assertNotIn(field, c, (ref, field))
                self.assertNotIn(ref, jlc_refs)
            if p["id"] in bom:
                self.assertEqual(bom[p["id"]]["state"], "TBD", p["id"])
                self.assertEqual(bom[p["id"]]["mpn"], "", p["id"])
        live_tbd_refs = sum(1 for p in tbd_parts if p["mount"] in parts.BUY_MOUNTS for r in p["refs"] if not model.comps[r][1].get("dnp"))
        self.assertEqual(cov["purchased_refs_by_availability"].get("TBD"), live_tbd_refs)
        self.assertEqual(cov["purchased_refs_with_mpn"],
                         sum(1 for r, p in model.part_of.items() if p["mount"] in parts.BUY_MOUNTS and not model.comps[r][1].get("dnp") and p.get("mpn") and not p.get("tbd")))

    def test_snapshot_row_without_mpn_is_not_evidence(self):
        # A vendor page that answered HTTP 200 but whose row records no part number does not confirm the part.
        model = parts.Model()
        model.manual["web:adafruit-5832"] = {k: v for k, v in model.manual["web:adafruit-5832"].items() if k != "mpn"}
        model.check()
        self.assertTrue(any("web adafruit-5832 snapshot row shows no MPN" in e for e in model.errors), model.errors)
        self.assertNotEqual(model.availability(part(model.db, "U-ADAFRUIT-5832"))[0], "в наявності")

    def test_every_sku_used_as_evidence_records_an_mpn(self):
        model = parts.Model()
        model.check()
        for p in model.db["parts"]:
            for e in [p] + p.get("alternates", []) + p.get("fallbacks", []) + p.get("extras", []):
                for dist, key in (e.get("sku") or {}).items():
                    rec = model.lcsc.get(key) if dist == "lcsc" else model.manual.get(f"{dist}:{key}")
                    self.assertTrue(rec and rec.get("mpn"), (p["id"], dist, key))
                    self.assertEqual(parts.norm_mpn(rec["mpn"]), parts.norm_mpn(e["mpn"]), (p["id"], dist, key))

    def test_fallback_is_never_written_as_a_substitute(self):
        model = parts.Model()
        model.check()
        model.graph_texts()
        fallbacks = [(p, f) for p in model.db["parts"] for f in p.get("fallbacks", [])]
        self.assertTrue(any(f["mpn"] == "TPS259631DDAR" for _, f in fallbacks))  # auto-retry, not the latch-off E2 relies on
        jlc_alt = " ".join(r["LCSC alternate"] for r in model.jlc_rows(parts.prepare_module()))
        for p, f in fallbacks:
            self.assertTrue(f["note"].strip())
            for ref in p["refs"]:
                self.assertNotIn(f["mpn"], model.comps[ref][1].get("alt_mpn", ""), ref)
            self.assertNotIn(f["mpn"], jlc_alt)

        def no_note(db):
            part(db, "U-TPS259630DDAR")["fallbacks"][0]["note"] = ""
        self.assertTrue(any("fallback TPS259631DDAR needs a note" in e for e in self.errors_after(no_note)))

    def test_interface_part_must_state_what_is_open(self):
        def drop(db):
            part(db, "J-USBA-PANEL").pop("interface_open")
        self.assertTrue(any("J-USBA-PANEL: interface refs J501 need exactly one of interface_open" in e for e in self.errors_after(drop)))

        def wrong_refs(db):
            part(db, "J-Q6A-EXISTING")["interface_open"].pop("J301")
        self.assertTrue(any("J-Q6A-EXISTING: interface_open must name exactly" in e for e in self.errors_after(wrong_refs)))

        def on_board_part(db):
            part(db, "J-SMA-EDGE")["interface_open"] = "x"
        self.assertTrue(any("J-SMA-EDGE: interface_open/interface_resolved only apply" in e for e in self.errors_after(on_board_part)))

    def test_partial_v2_row_lists_only_what_is_still_bought(self):
        model = parts.Model()
        model.check()
        rows = {r["row"]: r for r in model.v2_rows()}
        for no, v in model.db["bom_v2_rows"].items():
            if v["status"] == "db":
                self.assertNotIn(no, rows)
            else:
                self.assertEqual(rows[no]["model"], v["remaining"])
                self.assertEqual((rows[no]["usd_min"], rows[no]["usd_max"]), ("", ""))
        self.assertNotIn("10 пігтейлів", rows["91"]["model"].split("Не купувати")[0])

        model = parts.Model()
        model.db["bom_v2_rows"]["91"].pop("remaining")
        model.v2_rows()
        self.assertTrue(any("bom_v2_rows 91: a partial row needs remaining" in e for e in model.errors), model.errors)


prepare = parts.prepare_module()


class PcbPreparationBlockersTest(unittest.TestCase):
    """pcb/prepare.py keeps a blocking record for every connector/feed that is not a board part until it is resolved."""

    def setUp(self):
        self.model = parts.Model()
        self.db = {r: p for p in self.model.db["parts"] for r in p["refs"]}
        self.by_ref = {r: {**c, "_sheet": s, "_mount": self.db[r]["mount"]} for r, (s, c) in self.model.comps.items()}

    def issues(self, ref, db=None):
        c = self.by_ref[ref]
        return prepare.interface_issues(c, prepare.category(c)[0], db or self.db, self.by_ref)

    def test_selected_panel_and_existing_interfaces_stay_blocking(self):
        for ref in ("J501", "J301", "J408", "J541"):
            issues = self.issues(ref)
            self.assertEqual([(i["type"], i["blocking"]) for i in issues], [("interface_mounting_unresolved", True)], ref)
        self.assertIn("2×20", self.issues("J301")[0]["detail"])

    def test_resolved_interface_clears_and_tbd_interface_stays_open(self):
        db = dict(self.db)
        db["J501"] = {**self.db["J501"], "interface_resolved": "mating plug and panel cutout fixed", "interface_open": None}
        self.assertEqual(self.issues("J501", db), [])
        for ref in ("J402", "J403", "J406", "J401"):
            # W2 GR-2: the panel pigtails are selected (MPN + interface_open), so they block as unresolved mounting; a tbd entry stays TBD.
            self.assertEqual([i["type"] for i in self.issues(ref)], ["interface_mounting_unresolved"], ref)
            tbd = {**db, ref: {**self.db[ref], "tbd": "pigtail not chosen", "interface_open": None}}
            self.assertEqual([i["type"] for i in self.issues(ref, tbd)], ["physical_interface_or_rework_unresolved"], ref)
        db.pop("J501")
        self.assertEqual([i["type"] for i in self.issues("J501", db)], ["physical_interface_or_rework_unresolved"])

    def test_virtual_contact_without_host_net_blocks(self):
        for ref in ("SW308", "SW309"):
            issues = self.issues(ref)
            self.assertEqual([i["type"] for i in issues], ["host_pads_unconnected"], ref)
            self.assertIn("PRESS", issues[0]["detail"])

    def test_committed_unresolved_records_keep_the_interface_blockers(self):
        import csv
        with (BASE / "pcb/generated/unresolved.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        by_ref = {}
        for r in rows:
            by_ref.setdefault(r["ref"], set()).add(r["type"])
        interface_refs = [r for r, c in self.by_ref.items() if prepare.category(c)[0] == "physical_interface_boundary"]
        self.assertTrue(interface_refs)
        for ref in interface_refs:
            self.assertTrue(by_ref.get(ref, set()) & {"interface_mounting_unresolved", "physical_interface_or_rework_unresolved"}, ref)
        self.assertIn("host_pads_unconnected", by_ref["SW308"])


if __name__ == "__main__":
    unittest.main()
