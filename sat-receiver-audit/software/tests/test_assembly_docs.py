"""Assembly documents (build/16-21) stay consistent with the design graphs.

Design data only: no wire, torque or voltage here is a measurement, and no
hardware gate is closed by these checks."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import re
import unittest

BASE = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, BASE / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = load("srrx_asm_build_assembly_docs", "tools/build_assembly_docs.py")
D = gen.D


class AssemblyDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.h, cls.files = gen.build_all(BASE)

    def rows(self, rel):
        return list(csv.DictReader(io.StringIO(self.files[rel])))

    def test_committed_documents_match_the_generator(self):
        stale = [rel for rel, text in self.files.items() if (BASE / rel).read_text(encoding="utf-8") != text]
        self.assertEqual(stale, [], "run python tools/build_assembly_docs.py")

    def test_every_component_has_a_physical_place(self):
        refs = {c["ref"] for c in self.model.components}
        self.assertEqual(refs, set(self.model.unit_of))
        for ref, unit in D.UNIT_OF_REF.items():
            if ref in refs:
                self.assertIn(unit, self.model.unit_info, ref)

    def test_unplaced_component_is_refused(self):
        model = gen.Model.__new__(gen.Model)
        model.components = [{"ref": "U999", "value": "x", "kind": "ic", "_sheet": "E3", "pins": []}]
        model.partition = {}
        model.unit_info = {u[0]: {"kind": u[1], "name": u[2], "place": u[3]} for u in D.UNITS}
        with self.assertRaises(SystemExit):
            model.allocate()

    def test_every_cross_unit_net_reaches_all_its_places(self):
        reached = {}
        for wire in self.h.wires:
            reached.setdefault(wire["net"], set()).update((wire["from_unit"], wire["to_unit"]))
        for net, units in self.h.routed.items():
            joined = set(reached.get(net, set()))
            for a, b in self.h.internal.get(net, ()):
                joined.update((a, b))
            self.assertTrue(set(units) <= joined, f"{net}: {sorted(set(units) - joined)} not wired")

    def test_high_speed_and_rf_nets_are_never_loose_wires(self):
        wired = {w["net"] for w in self.h.wires}
        for nets in self.h.assemblies.values():
            self.assertFalse(wired & set(nets))
        self.assertFalse(wired & set(self.h.coax))
        self.assertNotIn("CHASSIS", wired)

    def test_connector_contacts_carry_one_wire_each(self):
        ends = {}
        for wire in self.h.wires:
            for key in ("from", "to"):
                m = re.match(r"([A-Z][A-Z0-9]*\d)\.([A-Za-z0-9_+\-]+)\b", wire[key])
                if m and m[1] in gen.EXPLICIT_SEGMENTS:
                    ends.setdefault((wire["segment"], m[1], m[2]), []).append(wire["wire"])
                m = re.match(r"(X\d\d[PSIF]\d-[A-Z]+)\.(\d+)", wire[key])
                if m:
                    ends.setdefault((wire["segment"], m[1], m[2]), []).append(wire["wire"])
        doubled = {k: v for k, v in ends.items() if len(v) > 1}
        self.assertEqual(doubled, {})

    def test_existing_harness_connectors_are_fully_wired(self):
        for ref, segments in gen.EXPLICIT_SEGMENTS.items():
            comp = self.model.by_ref[ref]
            for pin in comp["pins"]:
                net = pin.get("net")
                if not net or net == "CHASSIS":
                    continue
                for sid in segments:
                    seg = self.h.segments[sid]
                    if self.model.unit_of[ref] not in seg[1:3] or (net != "GND" and net not in self.h.seg_nets[sid]):
                        continue
                    if net == "GND" and sid in D.NO_GND:
                        continue
                    hit = [w for w in self.h.wires if w["segment"] == sid and f"{ref}.{pin['number']}" in (w["from"].split(" ")[0], w["to"].split(" ")[0])]
                    self.assertTrue(hit, f"{ref}.{pin['number']} ({net}) has no wire in {sid}")

    def test_gauges_carry_the_protection_or_are_reported(self):
        for wire in self.h.wires:
            awg, n = int(wire["awg"]), int(wire["bundle_n"])
            k = int(wire["parallel"].split("/")[1])
            limit = float(wire["i_prot_a"] or wire["i_cont_a"])
            capacity = D.ESCC_IMAX[awg] * gen.bundle_factor(n) * k
            if capacity + 1e-9 < limit:
                self.assertTrue(any(w.startswith(f"{wire['segment']} {wire['net']}:") for w in self.h.warnings), wire["wire"])

    def test_family_wire_ranges_are_respected(self):
        for wire in self.h.wires:
            for fam in (wire["family_from"], wire["family_to"]):
                if fam in ("PH", "MF", "IDC"):
                    self.assertIn(int(wire["awg"]), D.FAMILIES[fam]["awg"], wire["wire"])

    def test_every_test_point_has_expected_values(self):
        tps = [c for c in self.model.components if c["kind"] == "testpoint"]
        rows = self.rows(gen.OUT["bringup_csv"])
        self.assertEqual(sorted(r["tp"] for r in rows), sorted(c["ref"] for c in tps))
        for row in rows:
            if row["s4_enable"] != "—":
                self.assertIn(row["s4_enable"], self.model.nets, row["tp"])

    def test_bench_form_lists_every_gate_and_prefills_nothing(self):
        contract = json.loads((BASE / "design/readiness-contract.json").read_text(encoding="utf-8"))
        rows = self.rows(gen.OUT["form_csv"])
        gates = {r["id"] for r in rows if r["section"] == "GATE"}
        self.assertEqual(gates, set(contract["gate_results"]))
        self.assertTrue(all(v == "OPEN" for v in contract["gate_results"].values()))
        for row in rows:
            self.assertEqual((row["measured"], row["instrument"], row["result"], row["signature_date"]), ("", "", "", ""))
        ids_09 = [r["id"].split(" ")[0] for r in rows if r["section"] == "09"]
        for wanted in ("Ж-05", "ЗБ-01", "ЗБ-07", "DC-30"):
            self.assertIn(wanted, ids_09)

    def test_labels_cover_panel_ports_and_never_mark_transmit(self):
        panel = {c["ref"] for c in self.model.components if re.fullmatch(r"J4(0[1-8]|1[3-5])", c["ref"])}
        self.assertEqual(panel, set(D.PORT_LABELS))
        for row in self.rows(gen.OUT["labels_csv"]):
            if row["id"] == "L-LIME-X1":
                self.assertIn("усередині", row["place"])
                continue
            self.assertNotRegex(row["text"], r"\bTX\b", row["id"])
        markers = [r for r in self.rows(gen.OUT["labels_csv"]) if r["id"] == "L-WIRE"]
        self.assertIn(str(len(self.h.wires)), markers[0]["text"])

    def test_lime_transmit_port_stays_on_its_internal_load(self):
        units = set(self.h.coax["E4_LIME_TX"]) | set(self.h.coax["E4_TX_LOAD"])
        self.assertFalse({u for u in units if u.startswith("J4")}, "X1 must never reach a panel connector")
        self.assertEqual(units, {"LIME", "W406", "A410"})

    def test_assembly_order_uses_every_segment_fastener_label_and_cable(self):
        refs = {r for step in D.STEPS for r in step[5]}
        needed = set(self.h.segments) | {f[0] for f in D.FASTENERS} | {a[0] for a in D.ASSEMBLIES}
        needed |= {r["id"] for r in self.rows(gen.OUT["labels_csv"])}
        self.assertEqual(sorted(needed - refs), [])
        self.assertEqual(sorted(refs - needed), [])

    def test_catalogue_values_name_a_source_that_was_read(self):
        for fam in D.FAMILIES.values():
            if fam["source"]:
                self.assertIn(fam["source"], D.SOURCES)
        for fastener in D.FASTENERS:
            if fastener[7] not in ("—", "") and not fastener[7].startswith("STACK"):
                self.assertIn(fastener[7], D.SOURCES, fastener[0])
        for key, (url, note) in D.SOURCES.items():
            self.assertTrue(url.startswith("https://"), key)
            self.assertTrue(note)

    def test_superseded_v2_values_only_in_historic_clauses(self):
        for rel in ("build/02-zhyvlennia.md", "build/04-pidkliuchennia-pinout.md", "build/08-zbyrannia.md"):
            for number, line in enumerate((BASE / rel).read_text(encoding="utf-8").splitlines(), 1):
                for pattern, current in D.STALE:
                    if re.search(pattern, line):
                        self.assertIn(D.HISTORIC_MARK, line, f"{rel}:{number}: superseded value; v2.1 is {current}")

    def test_generated_text_claims_no_hardware_result(self):
        for rel, text in self.files.items():
            if rel not in (gen.OUT["form_md"], gen.OUT["form_csv"]):  # the form quotes 09 thresholds verbatim
                self.assertNotRegex(text, r"\bPASS\b", rel)
            self.assertNotRegex(text, r"[\w.+-]+@[\w-]+\.[\w.]+", rel)


if __name__ == "__main__":
    unittest.main()
