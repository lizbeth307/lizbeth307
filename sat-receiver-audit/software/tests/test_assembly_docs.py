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

# Independent of the generator: ESCC 3901/001 table 1(b) Imax per AWG, its bundle rule, and the fuse
# that sits upstream of each fused harness net in the graphs (E1/E2 topology, read by hand).
ESCC_IMAX = {28: 1.5, 26: 2.5, 24: 3.5, 22: 5.0, 20: 7.5, 18: 10.0}
FUSE_OF_NET = {"E1_SHUNT_P": "F101", "E1_N": "F101", "E1_SW": "F101", "SYS12": "F101", "E1_SERVICE_P": "F103",
               "LAB5": "F102", "E3_FAN5_P": "F301", "E3_BLOWER_GND": "F102", "J21": "F201"}
PIN_RE = re.compile(r"(?:пайка: )?([A-Z][A-Z0-9]*\d)\.([^\s(]+)")


def escc_capacity(awg, n, k):
    factor = 1.0 if n <= 1 else (0.5 if n >= 15 else (29 - n) / 28)
    return ESCC_IMAX[awg] * factor * k


def fuse_amps(comp):
    m = re.search(r"(\d+(?:\.\d+)?)\s*A\b", comp["value"])
    return float(m[1])


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

    def test_wires_follow_the_exported_netlist(self):
        # validate_project ties the graphs to the KiCad export; the harness must name the same nets and contacts.
        import xml.etree.ElementTree as ET
        root = ET.parse(BASE / "verification/netlist.xml").getroot()
        nodes = {}
        for net in root.findall("./nets/net"):
            for node in net.findall("node"):
                nodes[(node.get("ref"), node.get("pin"))] = net.get("name")
        names = set(nodes.values())
        refs = {ref for ref, _ in nodes}
        checked = 0
        for wire in self.h.wires:
            self.assertIn(wire["net"], names, wire["wire"])
            for key in ("from", "to"):
                m = PIN_RE.match(wire[key])
                if not m:
                    continue
                self.assertIn(m[1], refs, f"{wire['wire']} {key}: {m[1]} is not in the netlist")
                self.assertIn((m[1], m[2]), nodes, f"{wire['wire']} {key}: {m[1]}.{m[2]} is not a netlist pin")
                self.assertEqual(nodes[(m[1], m[2])], wire["net"], f"{wire['wire']} {key}")
                checked += 1
        self.assertGreater(checked, 100)
        battery_ends = {PIN_RE.match(w[k])[0].replace("пайка: ", "") for w in self.h.wires for k in ("from", "to")
                        if PIN_RE.match(w[k]) and w["segment"] == "S05"}
        self.assertTrue({"F101.2", "U101.P-"} <= battery_ends, battery_ends)

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
                m = re.match(r"(X\d\d[JPSIF]\d-[A-Z]+)\.(\d+)", wire[key])
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

    def test_gauges_carry_the_upstream_fuse_or_are_reported(self):
        # The fuse comes from the graph (its value), not from the generator's current table.
        seen = set()
        for wire in self.h.wires:
            fuse = FUSE_OF_NET.get(wire["net"])
            if not fuse:
                continue
            seen.add(wire["net"])
            amps = fuse_amps(self.model.by_ref[fuse])
            self.assertGreaterEqual(float(wire["i_prot_a"] or 0) + 1e-9, amps, f"{wire['wire']}: sized below {fuse} {amps:g} A")
            k = int(wire["parallel"].split("/")[1])
            if escc_capacity(int(wire["awg"]), int(wire["bundle_n"]), k) + 1e-9 < amps:
                self.assertTrue(any(w.startswith(f"{wire['segment']} {wire['net']}:") for w in self.h.warnings), wire["wire"])
        self.assertTrue({"E1_SHUNT_P", "E1_N", "E1_SW", "LAB5", "J21"} <= seen)

    def test_battery_circuit_is_never_thinner_than_the_e1_fuse_note(self):
        notes = " ".join(self.model.by_ref["F101"].get("notes", []))
        floor = int(re.search(r"(\d+) AWG", notes)[1])
        self.assertEqual(self.model.unit_of["F101"], "PACK")  # every harness wire of the circuit is below F101
        families = {}
        for wire in self.h.wires:
            if wire["net"] in ("E1_SHUNT_P", "E1_N", "E1_SW"):
                self.assertLessEqual(int(wire["awg"]), floor, wire["wire"])
                families[wire["segment"]] = {wire["family_from"], wire["family_to"]} - {"SOLDER"}
                for fam in (wire["family_from"], wire["family_to"]):
                    if fam in D.FAMILIES:
                        self.assertIn(int(wire["awg"]), D.FAMILIES[fam]["awg"], wire["wire"])
        for wire in self.h.wires:
            fams = {wire["family_from"], wire["family_to"]} - {"SOLDER"}
            if wire["net"] == "GND" and wire["segment"] in families and fams & families[wire["segment"]] and float(wire["i_cont_a"]) > 1:
                self.assertLessEqual(int(wire["awg"]), floor, wire["wire"])

    def test_power_wires_in_jst_ph_use_the_rated_gauge(self):
        # JST gives 2 A only for AWG #24; a wire with a current budget in a PH contact is not thinner.
        for wire in self.h.wires:
            if "PH" in (wire["family_from"], wire["family_to"]) and float(wire["i_cont_a"]) > 0.05:
                self.assertLessEqual(int(wire["awg"]), 24, wire["wire"])

    def test_one_branch_has_one_current(self):
        # The IMU pack branch is E5_IMU5V behind U553 (W2 GR-1): the internal lead S32 and the cable S33 carry one budget.
        imu = {w["segment"]: (w["i_cont_a"], w["i_prot_a"]) for w in self.h.wires if w["net"] == "E5_IMU5V"}
        self.assertEqual(imu["S33"], imu["S32"])

    def test_partition_deviations_are_listed(self):
        text = self.files[gen.OUT["harness_md"]]
        # may become empty once pcb/prepare.py gives these refs their own domains
        for ref, _, cand, board, unit in self.model.deviations:
            self.assertTrue(D.partition_deviation(ref, unit), ref)
            self.assertIn(f"| {ref} |", text)
            self.assertNotEqual(board, unit)
        for comp in self.model.components:
            board = D.BOARD_OF_DOMAIN.get(self.model.partition.get(comp["ref"], {}).get("board_candidate", ""))
            if board and self.model.unit_of[comp["ref"]] != board:
                self.assertIn(comp["ref"], {d[0] for d in self.model.deviations})

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
            if row["net"] != "GND":
                self.assertNotIn(row["source"], ("", "—"), f"{row['tp']}: expected values need a cited setpoint")

    def test_bench_form_lists_every_gate_and_prefills_nothing(self):
        contract = json.loads((BASE / "design/readiness-contract.json").read_text(encoding="utf-8"))
        rows = self.rows(gen.OUT["form_csv"])
        gates = {r["id"] for r in rows if r["section"] == "GATE"}
        self.assertEqual(gates, set(contract["gate_results"]))
        statuses = {}
        for status in contract["gate_results"].values():
            statuses[status] = statuses.get(status, 0) + 1
        footer = self.files[gen.OUT["form_md"]]
        for status, count in statuses.items():
            self.assertIn(f"{status} — {count}", footer)
        for row in rows:
            self.assertEqual((row["measured"], row["instrument"], row["result"], row["signature_date"]), ("", "", "", ""))
        ids_09 = [r["id"].split(" ")[0] for r in rows if r["section"] == "09"]
        for wanted in ("Ж-05", "ЗБ-01", "ЗБ-07", "DC-30"):
            self.assertIn(wanted, ids_09)

    def test_bench_form_carries_full_v21_criteria(self):
        rows = {r["id"]: r for r in self.rows(gen.OUT["form_csv"]) if r["section"] == "09"}
        source = {rid: (gen.plain(p), gen.plain(t)) for rid, p, t in gen.parse_09(BASE / "build/09-testy.md")}
        self.assertEqual(set(rows), set(source))
        for rid, row in rows.items():
            text = row["what"] + " " + row["threshold"]
            for pattern, current in D.STALE:
                if re.search(pattern, text):
                    self.assertIn(D.FORM_V21_MARK, row["what"], f"{rid}: superseded value without its v2.1 reading ({current})")
            if rid not in D.FORM_V21:
                self.assertEqual((row["what"], row["threshold"]), source[rid], f"{rid}: criterion must be printed in full")
        self.assertIn("D36V50F5", rows["Ж-05"]["what"])
        self.assertIn("3.2 A", rows["Ж-05"]["threshold"])
        self.assertNotIn("D36V28F5 (LAB5)", rows["Ж-05"]["what"])

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

    def test_label_artwork_keeps_the_specified_size(self):
        import xml.etree.ElementTree as ET
        svg = ET.fromstring(self.files[gen.OUT["labels_svg"]])
        ns = "{http://www.w3.org/2000/svg}"
        rects = [r for r in svg.iter(ns + "rect") if r.get("rx")]
        specs = [r for r in self.rows(gen.OUT["labels_csv"]) if r["id"] not in ("L-WIRE", "L-CONN")]
        self.assertEqual(len(rects), len(specs))
        for rect, spec in zip(rects, specs):
            w, h = (float(v) for v in spec["size_mm"].split("×"))
            self.assertEqual((float(rect.get("width")), float(rect.get("height"))), (w, h), spec["id"])
        self.assertIsNone(gen.fit_label("x" * 200, 20, 6))

    def test_fastener_step_column_matches_the_assembly_order(self):
        used = {r: step[0] for step in D.STEPS for r in step[5]}
        for fastener in D.FASTENERS:
            self.assertEqual(fastener[9], used[fastener[0]], fastener[0])

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

    def test_every_cited_mechanical_sheet_exists(self):
        # A builder looks a sheet up by its number: every M-/A-/P-/I-/B- sheet the assembly package names is a drawing of the mechanical package.
        drawings = {p.stem for p in (BASE / "mechanical/generated/drawings").glob("*.svg")}
        cited = set()
        for rel in ("tools/assembly_data.py", "tools/build_assembly_docs.py"):
            cited |= set(re.findall(r"(?<![\w-])(?:[MAPI]-\d\d|B-[A-Z]{2,})(?![\w-])", (BASE / rel).read_text(encoding="utf-8")))
        self.assertIn("M-07", cited)
        self.assertEqual(sorted(cited - drawings), [])

    def test_superseded_v2_values_only_in_historic_clauses(self):
        for rel in ("build/02-zhyvlennia.md", "build/04-pidkliuchennia-pinout.md", "build/08-zbyrannia.md"):
            for number, line in enumerate((BASE / rel).read_text(encoding="utf-8").splitlines(), 1):
                for pattern, current in D.STALE:
                    for m in re.finditer(pattern, line):
                        # the historic mark belongs to the same clause, not just somewhere in a long table row
                        clause = line[max(0, m.start() - 120): m.end() + 120]
                        self.assertIn(D.HISTORIC_MARK, clause, f"{rel}:{number}: superseded value; v2.1 is {current}")

    def test_generated_text_claims_no_hardware_result(self):
        for rel, text in self.files.items():
            if rel not in (gen.OUT["form_md"], gen.OUT["form_csv"]):  # the form quotes 09 thresholds verbatim
                self.assertNotRegex(text, r"\bPASS\b", rel)
            # an address needs a letter domain and TLD; video modes such as 2200x1125@51.68 are not addresses
            self.assertNotRegex(text, r"[\w.+-]+@[A-Za-z][\w-]*\.[A-Za-z]{2,}", rel)


class HarnessHeaderRefTests(unittest.TestCase):
    """W2 GR-3: board-side harness headers are graph refs (explicit mode); design data only, no hardware claim."""

    @classmethod
    def setUpClass(cls):
        cls.model, cls.h, cls.files = gen.build_all(BASE)

    def rows(self, rel):
        return list(csv.DictReader(io.StringIO(self.files[rel])))

    def test_no_synthesized_board_header(self):
        for row in self.rows(gen.OUT["connectors_csv"]):
            if row["connector"] not in self.model.by_ref:
                # only the board units that D.PENDING_BOARD_ENDS lists (with a reason) still get an X id
                self.assertIn(row["unit"], D.PENDING_BOARD_ENDS, row["connector"])
                self.assertTrue(row["board_part"].startswith("TBD"), row["connector"])
        for wire in self.h.wires:
            for key, unit in (("from", wire["from_unit"]), ("to", wire["to_unit"])):
                if self.model.is_board(unit) and unit not in D.PENDING_BOARD_ENDS:
                    m = PIN_RE.match(wire[key])
                    self.assertTrue(m and m[1] in self.model.by_ref, f"{wire['wire']} {key}: {wire[key]}")

    def test_every_header_contact_carries_one_wire_and_lands_where_headers_say(self):
        ends = {}
        for wire in self.h.wires:
            for key in ("from", "to"):
                m = PIN_RE.match(wire[key])
                if m and m[1] in D.HEADERS:
                    ends.setdefault((m[1], m[2]), []).append(wire)
        for ref, (label, segments) in D.HEADERS.items():
            comp = self.model.by_ref[ref]
            for sid, pins in segments.items():
                for pin in gen.pin_list(pins):
                    wires = ends.get((ref, pin), [])
                    self.assertEqual(len(wires), 1, f"{ref}.{pin} ({label})")
                    self.assertEqual(wires[0]["segment"], D.SEGMENT_BRANCHES.get(sid, sid), f"{ref}.{pin}")  # a branch is listed under its bundle
            listed = {p for pins in segments.values() for p in gen.pin_list(pins)}
            for pin in comp["pins"]:
                self.assertEqual(bool(pin.get("net")), str(pin["number"]) in listed, f"{ref}.{pin['number']}: a reserve contact is nc")
        self.assertEqual(sorted(k for k in ends if k[1] not in {p for v in D.HEADERS[k[0]][1].values() for p in gen.pin_list(v)}), [])

    def test_no_mpn_in_both_the_parts_list_and_the_harness_rollup(self):
        norm = lambda s: re.sub(r"[\s\-]+", "", s).upper().lstrip("0")
        bought = {norm(r["MPN"]) for r in csv.DictReader((BASE / "build/10-zakupivlia.csv").open(encoding="utf-8", newline="")) if r["MPN"]}
        rolled = {norm(r["mpn"].split(" (")[0]) for r in self.rows(gen.OUT["rollup_csv"])
                  if r["family"] != "провід" and not r["mpn"].startswith("TBD") and r["mpn"] not in ("—", "")}
        self.assertTrue(rolled)
        self.assertEqual(sorted(bought & rolled), [])

    def test_no_vertical_micro_fit_on_ctrl_or_rf(self):
        for row in self.rows(gen.OUT["connectors_csv"]):
            fp = self.model.db_part.get(row["connector"], {}).get("footprint", "")
            if row["board"] in ("CTRL", "RF") and row["family"] in ("MF", "MF2"):
                self.assertTrue(fp.endswith("_Horizontal"), f"{row['connector']} {fp}")
            if row["board"] in ("CTRL", "RF", "PWR_B") and row["family"] in ("PH", "PHD") and row["connector"] not in ("J203", "J506"):  # zone-2 top-entry pair, W2 PWR-L6-PLACE
                self.assertIn("_Horizontal", fp, row["connector"])

    def test_pps_branch_leaves_the_ribbon(self):
        branch = [w for w in self.h.wires if w["wire"].startswith("S01-PPS-")]
        self.assertEqual({w["net"] for w in branch}, {"E3_GNSS_PPS", "UART6_RX", "UART6_TX", "GND"})
        self.assertEqual({w["segment"] for w in branch} | {w["to_unit"] for w in branch}, {"S01", "GNSS"})
        self.assertEqual(sorted(w["from"].split(" ")[0] for w in branch), ["J301.16", "J301.18", "J301.6", "J301.7"])
        to_ctrl = {w["from"].split(" ")[0] for w in self.h.wires if w["segment"] == "S01" and w["to_unit"] == "CTRL"}
        self.assertFalse({"J301.6", "J301.7", "J301.16", "J301.18"} & to_ctrl)
        self.assertNotIn("E3_GNSS_PPS", {w["net"] for w in self.h.wires if w["segment"] == "S25"})


class InsertBoardBoundaryTests(unittest.TestCase):
    """W2 GR-4: the insert boards end every off-board net on a connector ref of that board (the boundary-audit rule of
    pcb/board_gen.py, applied to pcb/generated/components.csv). Design data only, no hardware claim."""

    BOARDS = ("T7_INSERT", "IMU_CARRIER", "PACK_FUSE")

    @classmethod
    def setUpClass(cls):
        cls.model, cls.h, cls.files = gen.build_all(BASE)

    def test_every_off_board_net_ends_on_a_connector_of_the_board(self):
        nodes = {}
        for comp in self.model.components:
            for pin in comp["pins"]:
                if pin.get("net"):
                    nodes.setdefault(pin["net"], set()).add(comp["ref"])
        for board in self.BOARDS:
            refs = {r for r, row in self.model.partition.items() if row["board_candidate"] == board}
            self.assertTrue(any(self.model.by_ref[r]["kind"] == "connector" for r in refs), board)
            for net in {p["net"] for r in refs for p in self.model.by_ref[r]["pins"] if p.get("net")}:
                if nodes[net] - refs:
                    ends = [r for r in refs if self.model.by_ref[r]["kind"] == "connector"
                            and any(p.get("net") == net for p in self.model.by_ref[r]["pins"])]
                    self.assertTrue(ends, f"{board}: {net} leaves the board without a connector ref")

    def test_solder_wire_pads_are_copper_with_official_footprints(self):
        for board in self.BOARDS:
            for ref, row in self.model.partition.items():
                if row["board_candidate"] == board and self.model.by_ref[ref]["kind"] == "connector" and row["mount"] == "pcb_pad":
                    self.assertTrue(row["footprint"].startswith("Connector_Wire:SolderWire-"), ref)
                    self.assertEqual(row["pad_coverage"], "PASS", ref)
                    self.assertNotIn("mpn", self.model.db_part[ref], ref)

    def test_s24_lands_on_the_insert_header(self):
        wires = [w for w in self.h.wires if w["segment"] == "S24"]
        self.assertEqual(sorted(w["to"].split(" ")[0] for w in wires), ["J514.1", "J514.2", "J514.3"])
        self.assertEqual({w["family_to"] for w in wires}, {"PH"})
        rows = {r["connector"]: r for r in csv.DictReader(io.StringIO(self.files[gen.OUT["connectors_csv"]]))}
        self.assertEqual((rows["J514"]["board"], rows["J514"]["orientation"]), ("T7_INSERT", "side"))



class Shrink2PwrBHeaderTests(unittest.TestCase):
    """W2 GR-5B (SHRINK-2): J506 + J508 are one JST PH 9 side-entry header on PWR-B; J204 (S04) stays PH while its RF end J420 is
    PH (one wire cannot take a PHD and a PH crimp). Design data only, no hardware claim."""

    @classmethod
    def setUpClass(cls):
        cls.model, cls.h, cls.files = gen.build_all(BASE)

    def test_headers_map_s23_and_s34_onto_j506(self):
        self.assertEqual(D.HEADERS["J506"][1], {"S23": "1-3", "S34": "4-9"})
        self.assertNotIn("J508", D.HEADERS)
        self.assertNotIn("J508", self.model.by_ref)

    def test_s23_and_s34_wires_land_on_j506(self):
        ends = {}
        for w in self.h.wires:
            if w["segment"] in ("S23", "S34"):
                ref, pin = w["from"].split(" ")[0].split(".")
                self.assertEqual(ref, "J506", w["wire"])
                ends.setdefault(w["segment"], set()).add(int(pin))
        self.assertEqual(ends, {"S23": {1, 2, 3}, "S34": {4, 5, 6, 7, 8, 9}})
        rows = {r["connector"]: r for r in csv.DictReader(io.StringIO(self.files[gen.OUT["connectors_csv"]]))}
        self.assertEqual((rows["J506"]["board"], rows["J506"]["orientation"], rows["J506"]["pins"]), ("PWR_B", "top", "9"))  # top entry since W2 PWR-L6-PLACE
        self.assertNotIn("J508", rows)

    def test_s04_keeps_one_crimp_family_per_wire(self):
        # PHD (SPHD-001T, 22 AWG only) at one end and PH (AWG 30-24) at the other end cannot share a wire, so S04 stays PH-PH
        fams = {(w["family_from"], w["family_to"]) for w in self.h.wires if w["segment"] == "S04"}
        self.assertEqual(fams, {("PH", "PH")})


class PwrL6ZoneTwoBranchTests(unittest.TestCase):
    """W2 PWR-L6-PLACE third pass: the J307 <-> J203 conductors of S02 are the branch S02B (J203 is the top-entry header of PWR-B
    zone 2); the harness stays straight (J307.k <-> J203.k). Design data only, no hardware claim; bend radius and fit stay OPEN."""

    @classmethod
    def setUpClass(cls):
        cls.model, cls.h, cls.files = gen.build_all(BASE)

    def test_s02b_is_a_straight_branch_of_s02(self):  # W2 PWR-L6-PLACE probe C: straight except the J202 <-> J203 pin swap
        self.assertEqual(D.SEGMENT_BRANCHES.get("S02B"), "S02")
        self.assertEqual((D.HEADERS["J203"][1], D.HEADERS["J307"][1]), ({"S02B": "1-20"}, {"S02B": "1 3-13 16 17 19 20", "S02": "2 14 15 18"}))
        branch = [w for w in self.h.wires if w["wire"].startswith("S02-S02B-")]
        self.assertEqual(len(branch), 20)
        for w in branch:
            a, b = PIN_RE.match(w["from"]), PIN_RE.match(w["to"])
            swap = {"2": "5", "14": "7", "15": "12", "18": "16"}  # J203 contact -> J306 contact (probe C)
            self.assertEqual((a[1], b[1], a[2]), ("J306" if b[2] in swap else "J307", "J203", swap.get(b[2], b[2])), w["wire"])
            self.assertEqual(w["segment"], "S02", w["wire"])
        self.assertFalse([w for w in self.h.wires if w["segment"] == "S02" and not w["wire"].startswith("S02-S02B-")
                          and "J203." in w["to"]])  # probe C: J307.2/14/15/18 run in S02 to J202

    def test_zone_two_pair_is_top_entry(self):
        rows = {r["connector"]: r for r in csv.DictReader(io.StringIO(self.files[gen.OUT["connectors_csv"]]))}
        for ref in ("J203", "J506"):
            self.assertEqual((rows[ref]["board"], rows[ref]["orientation"]), ("PWR_B", "top"), ref)
            self.assertTrue(self.model.db_part[ref]["footprint"].endswith("_Vertical"), ref)
        self.assertEqual(self.model.db_part["J307"]["footprint"], "Connector_JST:JST_PHD_S20B-PHDSS_2x10_P2.00mm_Horizontal")



class PwrL6ProbeCPinSwapTests(unittest.TestCase):
    """W2 PWR-L6-PLACE fourth pass, probe C (connector lever on PWR-B only): the four innermost J202-bound J209 lower-row nets
    EN_HFP / EN_LIME3V3 / EN_LNB / FAULT_HFP land on J203.2 / .14 / .15 / .18 (harness branch S02B), and the arm-local
    PG_BONI / PTC_AUX / PG_LNB / FAULT_RTLA land on J202.5 / .7 / .12 / .16 (S02); the CTRL J306 / J307 pin maps do not
    change, so these eight wires cross between the two CTRL headers. Design data only, no hardware claim."""

    SWAP = {"EN_HFP": ("J306.5", "J203.2"), "EN_LIME3V3": ("J306.7", "J203.14"), "EN_LNB": ("J306.12", "J203.15"),
            "FAULT_HFP": ("J306.16", "J203.18"), "PG_BONI": ("J307.14", "J202.5"), "PTC_AUX": ("J307.18", "J202.7"),
            "PG_LNB": ("J307.15", "J202.12"), "FAULT_RTLA": ("J307.2", "J202.16")}

    @classmethod
    def setUpClass(cls):
        cls.model, cls.h, cls.files = gen.build_all(BASE)

    def test_swapped_wires(self):
        for net, (ctrl, pwr) in self.SWAP.items():
            rows = [w for w in self.h.wires if w["net"] == net and w["segment"] == "S02"]
            self.assertEqual(len(rows), 1, net)
            a, b = PIN_RE.match(rows[0]["from"]), PIN_RE.match(rows[0]["to"])
            self.assertEqual((f"{a[1]}.{a[2]}", f"{b[1]}.{b[2]}"), (ctrl, pwr), net)
            self.assertEqual(rows[0]["wire"].startswith("S02-S02B-"), pwr.startswith("J203."), net)

    def test_s02b_nets_are_the_j203_nets(self):
        graph = json.loads((BASE / "design/E2.json").read_text(encoding="utf-8"))
        j203 = next(c for c in graph["components"] if c["ref"] == "J203")
        self.assertEqual(D.SEGMENT_NETS["S02B"], {p["net"] for p in j203["pins"] if p.get("net")})
        self.assertEqual(D.HEADERS["J306"][1], {"S02": "1-4 6 8-11 13-15 17-20", "S02B": "5 7 12 16"})


if __name__ == "__main__":
    unittest.main()
