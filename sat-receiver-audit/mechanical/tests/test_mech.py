"""Unit tests of the mechanical generator (run by sr-rx-mech.yml).

    python -m unittest discover -s mechanical/tests

Most tests need no CAD kernel; the Cad class is skipped when build123d is not installed.
"""
import csv
import importlib.util
import json
import math
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from srrx_mech import antennas, boards, drawings_enclosure as de, export3d, layout, report_md, rules, thermal, writers  # noqa: E402
from srrx_mech.features import face_features, seam_geometry  # noqa: E402
from srrx_mech.geom2d import fmt  # noqa: E402
from srrx_mech.params import Params  # noqa: E402

P = Params()


class Formatting(unittest.TestCase):
    def test_fmt_keeps_integer_zeros(self):
        self.assertEqual(fmt(160, 0), "160")
        self.assertEqual(fmt(1.50), "1.5")
        self.assertEqual(fmt(-0.0001), "0")
        self.assertEqual(fmt(2.0), "2")


class Params_(unittest.TestCase):
    def test_every_part_has_a_status_and_a_source(self):
        for key, part in P.parts.items():
            with self.subTest(part=key):
                self.assertIn("status", part)
                self.assertTrue(part.get("src"), key)
                self.assertRegex(part["status"], r"^(datasheet|repo|listing|assumption)(\+(assumption|listing|repo))?$")

    def test_layout_refers_to_known_parts_and_boards(self):
        for it in P.mech["layout"]["items"]:
            with self.subTest(item=it["id"]):
                if "part" in it:
                    self.assertIn(it["part"], P.parts)
                if "board" in it:
                    self.assertIn(it["board"], P.boards["boards"])

    def test_three_boards_and_the_encoder_daughterboard(self):
        # build/15: three boards (power, RF/detector, control/HMI); the encoder board is the replaceable
        # daughterboard STACK 5.8 asks for. W2 AREA / MECH-3: the power board is PWR-A plus the PWR-B mezzanine.
        self.assertEqual(set(P.boards["boards"]), {"PWR", "PWR_B", "RF", "CTRL", "ENC"})
        self.assertEqual(P.boards["stackup"]["layers"], 4)

    def test_board_domains_are_the_pcb_partition_domains(self):
        comp = HERE.parent / "pcb" / "generated" / "components.csv"
        if not comp.exists():
            self.skipTest("pcb/generated/components.csv not present")
        with comp.open(encoding="utf-8", newline="") as fh:
            domains = {r["board_candidate"] for r in csv.DictReader(fh) if r["board_candidate"]}
        mine = {d for b in P.boards["boards"].values() for d in b["domains"]}
        mine |= {d for k, b in P.boards["small_boards"].items() if not k.startswith("_") for d in b["domains"]}
        # W2 MECH-3 (CC-12): boards.json PWR_B carries the PWR-B domains of pcb/partition-spec.json before pcb/prepare.py
        # creates them (GR-3); once components.csv has them this is the plain equality again
        spec = json.loads((HERE.parent / "pcb" / "partition-spec.json").read_text(encoding="utf-8"))
        pending = set(spec["domains"]["PWR_B"]["prepare_domains"]) - domains
        self.assertEqual(set(P.boards["boards"]["PWR_B"]["domains"]), set(spec["domains"]["PWR_B"]["prepare_domains"]))
        self.assertEqual(mine, domains | pending)

    def test_vendor_models_are_pinned_and_not_committed(self):
        for m in P.vendor["models"]:
            self.assertRegex(m["sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(m["member_sha256"], r"^[0-9a-f]{64}$")
        vendor_like = [p for p in HERE.rglob("*") if p.suffix.lower() in (".stp", ".zip") and "generated" not in p.parts]
        self.assertEqual(vendor_like, [])


class ReceiveOnly(unittest.TestCase):
    def test_no_transmit_port_on_any_panel(self):
        for face, feats in face_features(P).items():
            for f in feats:
                with self.subTest(face=face, feature=f["id"]):
                    self.assertNotRegex(f["id"], r"(^|_)(TX|X1)($|_)")
        ids = [p["id"] for p in P.mech["top_face"]["ports"]] + [p["id"] for p in P.mech["right_face"]["ports"]]
        self.assertEqual(ids, ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "RX1", "RX2", "REF_IN"])

    def test_the_only_operator_controls_are_hmi_and_the_power_key(self):
        kinds = {f["kind"] for feats in face_features(P).values() for f in feats}
        self.assertNotIn("switch", kinds)
        self.assertEqual([f["id"] for f in face_features(P)["top"] if f["kind"] == "pv6"], ["PWR_KEY"])


class Seam(unittest.TestCase):
    def test_groove_lies_in_the_belt_and_wall(self):
        gk = P.mech["gasket"]
        sg = seam_geometry(P)
        self.assertGreaterEqual(sg["groove_out"], -gk["belt"] + gk["land"] - 1e-9)
        self.assertLessEqual(sg["groove_in"], P.mech["wall"] - gk["land"] + 1e-9)

    def test_closure_holes_inside_the_seal(self):
        r = [x for x in rules.evaluate(P) if x["id"] == "R-SEAM-HOLES"][0]
        self.assertTrue(r["result"].startswith("PASS"), r)

    def test_closure_spans_are_reported(self):
        cs = rules.closure_spans(P)
        self.assertEqual(cs["screws"], len(P.mech["closure"]["bosses"]))
        self.assertLess(cs["max_span_mm"], 130.0)

    def test_vents_never_face_up(self):
        self.assertTrue(P.mech["vents"])
        for v in P.mech["vents"]:
            self.assertNotEqual(v["face"], "top", v["id"])


def _inside(p, poly):
    x, y = p
    n, ins = len(poly), False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            ins = not ins
    return ins


class Plate(unittest.TestCase):
    def test_outline_stays_inside_the_rounded_interior(self):
        W, H, _ = P.outer
        t, R = P.mech["wall"], P.mech["outer"]["corner_r"]
        r = R - t - P.mech["plate"]["corner_clearance"]
        for x, y in rules.plate_outline(P):
            cx, cy = min(max(x, R), W - R), min(max(y, R), H - R)
            self.assertLessEqual(math.hypot(x - cx, y - cy), r + 1e-6, (x, y))

    def test_every_plate_hole_is_inside_the_outline(self):
        poly = rules.plate_outline(P)
        for h in rules.plate_holes(P):
            self.assertTrue(_inside(h["c"], poly), h["id"])


class Export3D(unittest.TestCase):
    def test_step_reals_are_rounded_and_zero_noise_removed(self):
        src = ("ISO-10303-21;\nHEADER;\nFILE_NAME('a','2030-01-01T00:00:00',('x'),('y'),'OCC 8.0','b','c');\nENDSEC;\nDATA;\n"
               "#1 = DIRECTION('',(1.,0.,2.22044604925E-16));\n#2 = CARTESIAN_POINT('q6a.board 1.5',(-0.,12.3456789012345,1.E+100));\nENDSEC;\n")
        out = export3d.normalise_step(src.encode()).decode()
        self.assertIn("FILE_NAME('a','2026-10-24T00:00:00'", out)
        self.assertIn("#1 = DIRECTION('',(1.,0.,0.));", out)
        self.assertIn("CARTESIAN_POINT('q6a.board 1.5',(0.,12.345678901,1.E+100));", out)
        self.assertIn("'OCC 8.0'", out)

    def test_stl_reader_checks_the_length(self):
        with self.assertRaises(ValueError):
            export3d.read_stl(b"\0" * 80 + (2).to_bytes(4, "little") + b"\0" * 50)


class Report(unittest.TestCase):
    def test_markdown_report_renders_without_cad(self):
        env = {"model": [1, 2, 3], "over_seam_belt": [1, 2, 3], "d15": [1, 2, 3], "volume_l": 1, "volume_l_d15": 1,
               "surface_m2": 1, "surface_m2_d15": 1, "front_m2": 1, "fire_bag_23x30cm": {"w_plus_d": 1, "h_plus_d": 1, "result": "PASS (model)"}}
        summ = {"collisions": 0, "outside": 0, "rule_failures": 0, "rules_open": 0, "antenna_rule_failures": 0,
                "board_area_failures": 0, "thermal_failures": 0, "thermal_open": 0, "gasket": "PASS", "vendor_fit": "NOT RUN"}
        gasket = {"cord_d": 2, "groove": [2.6, 1.55], "squeeze": 0.2, "fill": 0.7, "belt_mm": 1.9, "result": "PASS",
                  "cord_length_mm": 1, "cord_order_mm": 1, "closure": rules.closure_spans(P)}
        report = {"envelope": env, "summary": summ, "rules": rules.evaluate(P), "rf_bay_packing": rules.bay_packing(P),
                  "thermal_interfaces": {"rule": "r", "rows": thermal.interfaces(P), "cuts_per_thickness": {}},
                  "gasket": gasket, "tight_below_0_5mm": []}
        md = report_md.render(P, report, "test", boards.contract(P)).decode("utf-8")
        self.assertIn("MODEL FIT ONLY", md)
        self.assertIn("| PWR |", md)


@unittest.skipUnless(importlib.util.find_spec("build123d"), "build123d not installed")
class Cad(unittest.TestCase):
    def test_shells_are_single_solids_with_the_seam_belt(self):
        from srrx_mech import cad
        W, H, _ = P.outer
        b = P.mech["gasket"]["belt"]
        for fn in (cad.front_shell, cad.rear_shell):
            s = fn(P)
            self.assertEqual(len(s.solids()), 1, fn.__name__)
            bb = s.bounding_box()
            self.assertAlmostEqual(bb.size.X, W + 2 * b, places=3)
            self.assertAlmostEqual(bb.size.Y, H + 2 * b, places=3)

    def test_stl_writer_counts_and_bounds(self):
        from build123d import Box
        data, n = export3d.stl_bytes(Box(10, 20, 30), "box")
        self.assertEqual(n, 12)
        count, (lo, hi) = export3d.read_stl(data)
        self.assertEqual(count, 12)
        self.assertEqual([round(v, 3) for v in lo + hi], [-5, -10, -15, 5, 10, 15])
        self.assertEqual(data, export3d.stl_bytes(Box(10, 20, 30), "box")[0])


class Checks(unittest.TestCase):
    def test_envelopes_do_not_collide(self):
        coll, outside = layout.fit_checks(P)
        self.assertEqual([c for c in coll if c["gap_mm"] < 0], [])
        self.assertEqual(outside, [])

    def test_rules_have_no_failure(self):
        for r in rules.evaluate(P):
            with self.subTest(rule=r["id"]):
                self.assertFalse(r["result"].startswith("FAIL"), r)

    def test_slot_fill_counts_the_build16_wires_and_stays_open(self):
        path = HERE.parent / "build" / "16-dzhgut.csv"
        if not path.exists():
            self.skipTest("build/16-dzhgut.csv not present")
        r = rules.plate_slot_fill(P)
        self.assertFalse(r["result"].startswith("FAIL"), r)   # W2 MECH-6: wire OD and edge trim chosen, the fill is judged (SlotFillAndW2Mech6 below)
        with path.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        for sl in P.mech["plate"]["slots"]:
            n = sum(1 for w in rows if w["segment"] in sl["segments"])
            self.assertEqual(r["value_mm"][sl["id"]]["wires"], n, sl["id"])
            self.assertGreater(n, 0, sl["id"])
        # the one-piece moulded USB3 cable C-T7 never crosses the plate (Q6A J5 is at the plate rear, the T7 gland in the rear wall)
        sl2 = next(sl for sl in P.mech["plate"]["slots"] if sl["id"] == "SL2")
        self.assertNotIn("C-T7", sl2["use"].split("(build/16)")[0])

    def test_thermal_pad_choice(self):
        t, sku, lo, hi = thermal.choose(P, 0.8, 0.1)
        self.assertEqual((t, sku), (1.0, "TP-GP04-B"))
        self.assertGreaterEqual(lo, thermal.COMP_MIN - 1e-9)
        self.assertLessEqual(hi, P.parts["gelid_gp_ultimate"]["max_compression"] + 1e-9)
        self.assertIsNone(thermal.choose(P, 0.8, 0.5))

    def test_pad_cuts_fit_whole_sheets(self):
        rows = thermal.interfaces(P)
        for t, d in thermal.nest(rows, P.parts["gelid_gp_ultimate"]["sheet"]).items():
            for pc in d["pieces"]:
                self.assertIsNotNone(pc["sheet"], (t, pc))
                self.assertLessEqual(pc["at"][0] + pc["size"][0], 90.0 + 1e-9)
                self.assertLessEqual(pc["at"][1] + pc["size"][1], 50.0 + 1e-9)

    def test_antenna_parts_respect_the_size_rule(self):
        _, checks = antennas.sheets(P)
        for c in checks:
            with self.subTest(part=c["part"]):
                self.assertTrue(c["result"].startswith("PASS"), c)


class Review(unittest.TestCase):
    """Checks added after the stage-3B review (MECH-R1..R11)."""

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def test_side_cut_outs_keep_off_the_seam_belt(self):
        Q = self._copy()
        Q.mech["bottom_face"]["ports"][0]["z"] = 7.0          # the old USB-C position overlapped the belt step
        r = [x for x in rules.evaluate(Q) if x["id"] == "R-PANEL-FLAT"][0]
        self.assertTrue(r["result"].startswith("FAIL"), r)

    def test_pwr_modules_must_fit_the_board_envelope(self):
        Q = self._copy()
        Q.boards["boards"]["PWR"]["height_zones"] = []        # back to the 9.0 mm board envelope
        Q.boards["boards"]["PWR"]["max_height"] = 3.0         # W2 MECH-7: no module any more; the 4.1 mm LAB5 converter block no longer fits
        if not [b for b in ((boards.budget_candidate()[1] or {}).get("planned") or {}).get("blocks", []) if b["id"] not in boards.retired_blocks()]:
            Q.boards["boards"]["PWR"]["modules_on_board"] = [{"id": "M1", "part": "pololu_d36v50", "at": [10, 10]}]   # part 2: blocks retired with GR-5A, a module must still fit
        r = [x for x in rules.evaluate(Q) if x["id"] == "R-PWR-MODULES"][0]
        self.assertTrue(r["result"].startswith("FAIL"), r)
        r = [x for x in rules.evaluate(P) if x["id"] == "R-PWR-MODULES"][0]
        self.assertTrue(r["result"].startswith("PASS"), r)

    def test_cooler_a_is_in_the_layout_and_clears_the_headers(self):
        names = {n for _, n, _, _ in layout.item_boxes(P)}
        self.assertTrue({"cooler_a.block", "cooler_a.fins", "cooler_a.fan", "q6a.hdr2x2", "q6a.s01_idc_socket"} <= names)
        zt = layout.q6a_top_z(P)
        fan = [b for _, n, b, _ in layout.item_boxes(P) if n == "cooler_a.fan"][0]
        self.assertLessEqual(fan[5], zt - P.parts["q6a_cooler_zone"]["fan_min_above_board"] + 1e-9)

    def test_rx1_nut_clears_the_rf_bay_wall(self):
        rb = P.mech["rf_bay"]
        wall_x = rb["rect"][0] + rb["rect"][2] - rb["wall_t"]
        nut = [b for _, n, b, _ in layout.item_boxes(P) if n == "nut.RX1"][0]
        self.assertGreaterEqual(wall_x - nut[3], 0.5)
        xs = [p["x"] for p in P.mech["top_face"]["ports"]]
        self.assertEqual({round(b - a, 6) for a, b in zip(xs, xs[1:])}, {20.0})

    def test_angle_screws_sit_between_the_ports(self):
        hw = P.parts["sma_bulkhead_hw"]
        ports = [p["x"] for p in P.mech["top_face"]["ports"]]
        for xh, _ in rules.angle_holes(P, "top"):
            self.assertGreater(min(abs(xh - x) for x in ports), hw["washer_od"] / 2 + 3.0, xh)

    def test_fire_bag_uses_the_closed_depth(self):
        sys.path.insert(0, str(HERE))
        import build
        bag = build.envelope_report(P)["fire_bag_23x30cm"]
        self.assertGreater(bag["depth_mm"], P.outer[2] + 20.0)
        self.assertTrue(bag["result"].startswith("FAIL"), bag)


@unittest.skipUnless(importlib.util.find_spec("build123d"), "build123d not installed")
class ReviewCad(unittest.TestCase):
    def test_every_closure_screw_is_reachable(self):
        from srrx_mech import cad, interference
        solids = {"rear_shell": cad.rear_shell(P), "hatch_cover": cad.hatch_cover(P), "t7_holder": cad.t7_holder(P), "hood": cad.hood(P)}
        r = interference.access(P, solids)
        self.assertTrue(r["result"].startswith("PASS"), r)
        import copy
        Q = copy.deepcopy(P)
        Q.mech["rear_face"]["strap_lugs"] = [[14.0, 150.0], [216.0, 150.0]]   # the reviewed lugs buried screws 9 and 12
        solids["rear_shell"] = cad.rear_shell(Q)
        r = interference.access(Q, solids)
        self.assertTrue(r["result"].startswith("FAIL"), r)
        self.assertIn("CLOSURE_9", r["result"])
        self.assertIn("CLOSURE_12", r["result"])

    def test_rf_bay_walls_clear_the_top_angle(self):
        from srrx_mech import cad, interference
        walls, _ = cad.rf_bay(P)
        inter = walls & cad.angle_top(P)
        self.assertLessEqual(interference._vol(inter), interference.TOL_MM3)
        self.assertIn(("angle_top", "rf_bay_walls"), interference.struct_pairs({"angle_top": 1, "rf_bay_walls": 1, "plate": 1}))


class Writers(unittest.TestCase):
    def sheets(self):
        out = de.face_sheets(P) + [de.plate_sheet(P), de.rfbay_sheet(P), de.seam_sheet(P)]
        out += [boards.board_sheet(P, b) for b in P.boards["boards"]]
        for sh in out:
            sh.finish({"scale": "1:1", "params": "test", "version": "test"})
        return out

    def test_svg_and_dxf_are_reproducible(self):
        a = [(writers.to_svg(s, {"params": "t"}), writers.to_dxf(s)) for s in self.sheets()]
        b = [(writers.to_svg(s, {"params": "t"}), writers.to_dxf(s)) for s in self.sheets()]
        self.assertEqual(a, b)

    def test_board_edge_cuts_carry_only_outline_and_holes(self):
        sh = boards.board_sheet(P, "PWR")
        dxf = writers.to_dxf(sh, only=("CUT", "HOLE")).decode("ascii")
        layers = set(re.findall(r"\n8\n(\w+)\n", dxf.split("ENTITIES", 1)[1]))
        self.assertEqual(layers, {"CUT", "HOLE"})

    def test_pdf_is_reproducible(self):
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            self.skipTest("matplotlib not installed")
        sh = [de.seam_sheet(P)]
        sh[0].finish({"scale": "5:1", "params": "t", "version": "t"})
        self.assertEqual(writers.to_pdf(sh, {}), writers.to_pdf(sh, {}))


class Contract(unittest.TestCase):
    def test_contract_lists_every_board_with_its_dxf(self):
        c = boards.contract(P)
        self.assertEqual(c["status"], "MODEL_FIT_ONLY")
        for bid, b in c["boards"].items():
            self.assertEqual(b["dxf"], f"boards/{bid.lower()}-edge-cuts.dxf")
            self.assertGreater(b["area_mm2"], 0)
        json.dumps(c)


if __name__ == "__main__":
    unittest.main()


class CourtyardArea(unittest.TestCase):
    """W2 MECH-1 (A-PCB-01): board area from the vendored KiCad courtyards."""

    def test_courtyards_match_kicad(self):
        cy = boards.footprint_courtyards()
        r = cy["Resistor_SMD:R_0603_1608Metric"]
        self.assertAlmostEqual(r["w"], 2.96, places=3)
        self.assertAlmostEqual(r["h"], 1.46, places=3)
        p = cy["SR_RX_Custom:TI_RDL0020A_B3QFN-20_5x5.5mm"]      # W2 GR-5A merge: Pololu_D36V50Fx left the library with SHRINK-2; U108 TPSM63606 F.CrtYd rect +/-2.95 x +/-3.0
        self.assertAlmostEqual(p["w"], 5.9, places=3)
        self.assertAlmostEqual(p["h"], 6.0, places=3)

    def test_board_total_is_the_sum_over_its_domain_refs(self):
        path = HERE.parent / "pcb" / "generated" / "components.csv"
        if not path.exists():
            self.skipTest("pcb/generated/components.csv not present")
        cy = boards.footprint_courtyards()
        with path.open(encoding="utf-8", newline="") as fh:
            rows = [r for r in csv.DictReader(fh) if r["category"] == "bare_board_part" and r["dnp"] != "True"]
        ctrl = sum(cy[r["footprint"]]["area"] for r in rows if r["board_candidate"] == "CTRL_HMI")
        res = boards.area_check(P)
        self.assertEqual(res["boards"]["CTRL"]["courtyard_raw_mm2"], round(ctrl, 0))
        mods = sum(cy[r["footprint"]]["area"] for r in rows if r["board_candidate"] in P.boards["boards"]["PWR"]["domains"] and r["mount"] == "pcb_module")
        self.assertEqual(res["boards"]["PWR"]["modules_mm2"], round(mods, 0))
        for m in P.boards["boards"]["PWR"].get("modules_on_board", []):      # every modules_on_board part is a pcb_module ref, counted once (none since W2 MECH-7)
            self.assertEqual(m["part"], "pololu_d36v50")
        self.assertAlmostEqual(res["boards"]["PWR"]["need_1_8_mm2"], round(mods + (res["boards"]["PWR"]["courtyard_raw_mm2"] - mods) * 1.8, 0), delta=1.0)

    def test_area_rows_are_model_estimates_and_never_fail(self):
        res = boards.area_check(P)
        for bid, r in list(res["boards"].items()) + list(res["with_harness"]["boards"].items()):
            with self.subTest(board=bid):
                self.assertTrue(r["result"].startswith(("PASS (model estimate)", "OPEN")), r["result"])
        self.assertIn("MODEL ESTIMATE", res["status"])


class HarnessRoutes(unittest.TestCase):
    """W2 MECH-1 (B-00, B-06): routes, lengths, PPS budget."""

    @classmethod
    def setUpClass(cls):
        from srrx_mech import routes
        cls.routes = routes
        cls.res = routes.evaluate(P)

    def test_every_build16_segment_and_s41_has_an_entry(self):
        segs = set(self.routes.build16_wires())
        if not segs:
            self.skipTest("build/16-dzhgut.csv not present")
        self.assertTrue(segs <= set(P.mech["harness_routes"]["segments"]), sorted(segs - set(P.mech["harness_routes"]["segments"])))
        self.assertIn("S41", self.res["segments"])
        for sid, r in self.res["segments"].items():
            with self.subTest(segment=sid):
                self.assertFalse(r["status"].startswith("FAIL"), r["status"])
                if r["kind"] != "external" and r.get("length_mm") is None:
                    self.assertTrue(r["provisional"], sid)      # no length only with a named reason

    def test_every_slot_segment_is_routed_through_its_slot(self):
        for sl, v in self.res["slots"].items():
            with self.subTest(slot=sl):
                self.assertEqual(v["listed_not_routed"], [])

    def test_length_grows_when_the_far_end_moves_away(self):
        import copy
        Q = copy.deepcopy(P)
        base = self.res["segments"]["S25"]["length_mm"]
        lens = []
        for dx in (5.0, 10.0, 20.0):
            for it in Q.mech["layout"]["items"]:
                if it["id"] == "lc76g":
                    it["box"][0] = next(i for i in P.mech["layout"]["items"] if i["id"] == "lc76g")["box"][0] - dx
            lens.append(self.routes.evaluate(Q)["segments"]["S25"]["length_mm"])
        self.assertTrue(base < lens[0] < lens[1] < lens[2], (base, lens))

    def test_a_route_through_a_solid_is_reported(self):
        import copy
        Q = copy.deepcopy(P)
        Q.mech["harness_routes"]["segments"]["S28"]["via"] = [{"box": "blower", "at": [0.0, 0.5, 0.5]}, {"box": "PWR.r0", "at": [0.5, 0.5, 0.5]},
                                                             {"box": "lime", "at": [0.5, 0.5, 0.5]}]
        r = self.routes.evaluate(Q)["segments"]["S28"]
        self.assertTrue(r["crossings"], r)
        self.assertTrue(r["status"].startswith("FAIL"), r["status"])

    def test_pps_budget_has_a_number_and_a_decision(self):
        row = next(r for r in rules.evaluate(P) if r["id"] == "R-PPS-LEN")
        self.assertIsInstance(row["value_mm"]["via_segments_mm"], int)
        if row["value_mm"]["via_segments_mm"] > row["limit_mm"]:
            self.assertIn("branch_mm", row["value_mm"])
            self.assertIn("PPS", P.mech["harness_routes"]["branches"])
        self.assertFalse(row["result"].startswith("FAIL"), row["result"])

    def test_routes_never_read_the_build16_length_column(self):
        src = (HERE / "srrx_mech" / "routes.py").read_text(encoding="utf-8")
        self.assertNotIn('"length_mm"]', src.split("def build16_wires")[1].split("def ")[0])


class HeaderHeights(unittest.TestCase):
    """W2 MECH-1 (B-03): header heights and the computed height zones of CTRL and RF."""

    def test_zones_in_boards_json_equal_the_clearance_map(self):
        for bid in boards.ZONE_BOARDS:
            front, rear = boards.zones_from_map(boards.clearance_map(P, bid))
            b = P.boards["boards"][bid]
            got = [{k: z[k] for k in ("rect", "free_mm", "fits_mm", "limit")} for z in b["height_zones"]]
            with self.subTest(board=bid):
                self.assertEqual(got, front, "run python mechanical/build.py --update-zones")
                self.assertEqual(b["rear_zones"], rear, "run python mechanical/build.py --update-zones")
                self.assertTrue(all(z["max_height"] == b["max_height"] for z in b["height_zones"]))

    def test_micro_fit_vertical_height_is_read(self):
        mf = P.parts["harness_headers"]["MF_top"]
        self.assertEqual(mf["h"], 9.9)
        self.assertEqual(mf["h_status"], "datasheet")
        self.assertIn("2026-11-07", mf["h_src"])
        self.assertIn("http", mf["h_src"])

    def test_header_height_rule_is_open_not_fail(self):
        row = boards.header_height_rule(P)
        self.assertTrue(row["result"].startswith("OPEN"), row["result"])
        # a property, not a connector name: GR-3 re-types and renames the headers
        self.assertTrue(any(" MF_top " in s for s in row["value_mm"]["above_limit"]), row["value_mm"]["above_limit"])

    def test_every_family_is_judged_at_its_mated_height_where_read(self):
        hh = P.parts["harness_headers"]
        mf = hh["MF_top"]
        self.assertEqual(mf["h_mated"], 17.27)
        self.assertIn("2026-11-07", mf["h_mated_src"])
        self.assertIn("http", mf["h_mated_src"])
        self.assertIn("h_mated", hh["MF_ra"])
        row = boards.header_height_rule(P)
        for x in row["headers"]:
            c = hh.get(f"{x['family']}_{x['orientation']}", {})
            with self.subTest(connector=x["connector"]):
                if "h_mated" in c:
                    self.assertEqual((x["h_mm"], x["h_basis"]), (c["h_mated"], "mated"))
                elif x["h_mm"] is not None:
                    self.assertEqual(x["h_basis"], "body")
                    self.assertIn("mated height not read", x["verdict"])
                if x["family"] == "MF" and x["h_mm"] > x["max_height"]:
                    self.assertEqual(x["alternative"]["key"], "MF_ra")      # the right-angle 43650 is judged as the alternative


class ReviewFixes(unittest.TestCase):
    """W2 MECH-1 review fixes: per-group sums, waypoint names, --update-zones safety."""

    def test_per_group_areas_add_up_to_the_board_total(self):
        res = boards.area_check(P)
        if res.get("status") == "SKIPPED":
            self.skipTest(res["reason"])
        for bid, b in res["boards"].items():
            with self.subTest(board=bid):
                self.assertLessEqual(abs(sum(b["per_group_raw_mm2"].values()) - b["courtyard_raw_mm2"]), len(b["per_group_raw_mm2"]))
                self.assertEqual(set(b["per_group_need_mm2"]), set(b["per_group_raw_mm2"]))

    def test_a_missing_waypoint_name_is_open_not_a_crash(self):
        import copy
        from srrx_mech import routes
        Q = copy.deepcopy(P)
        Q.mech["harness_routes"]["segments"]["S25"]["via"][-1] = {"box": "no_such_envelope", "at": [1.0, 0.5, 0.5]}
        Q.mech["harness_routes"]["branches"]["PPS"]["via"][1] = {"slot": "SL99"}
        res = routes.evaluate(Q)
        for r in (res["segments"]["S25"], res["branches"]["PPS"]):
            self.assertTrue(r["status"].startswith("OPEN (end provisional)"), r["status"])
            self.assertIn("not in the model", r["status"])
            self.assertIsNone(r["length_mm"])
        self.assertFalse(any(x["result"].startswith("FAIL") for x in routes.route_rules(Q, res)))

    def test_update_zones_is_idempotent_and_never_drops_the_zones(self):
        import shutil
        import tempfile
        src = HERE / "params" / "boards.json"
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d) / "boards.json"
            shutil.copyfile(src, tmp)
            boards.write_zones(P, tmp)
            once = tmp.read_bytes()
            boards.write_zones(P, tmp)
            self.assertEqual(tmp.read_bytes(), once)
            self.assertEqual(once, src.read_bytes(), "run python mechanical/build.py --update-zones")
            bid = boards.ZONE_BOARDS[0]
            mh = json.dumps(P.boards["boards"][bid]["max_height"])
            text = once.decode("utf-8")
            start = text.index(f'    "{bid}": {{\n')
            broken = text[:start] + text[start:].replace(f'      "max_height": {mh},\n', f'      "max_height": {mh}0,\n', 1)
            tmp.write_text(broken, encoding="utf-8", newline="\n")
            with self.assertRaises(ValueError):
                boards.write_zones(P, tmp)
            self.assertEqual(tmp.read_text(encoding="utf-8"), broken)      # nothing written


class PanelPortsW2Mech2(unittest.TestCase):
    """W2 MECH-2 (B-01, B-02, C-20): panel and bottom cut-outs from the makers' drawings."""

    def _rule(self, Q, rid):
        return [x for x in rules.evaluate(Q) if x["id"] == rid][0]

    def _box(self, Q, name):
        return [b for _, n, b, _ in layout.item_boxes(Q) if n == name][0]

    def test_bottom_ports_are_modelled_or_name_a_reason(self):
        for p in P.mech["bottom_face"]["ports"]:
            with self.subTest(port=p["id"]):
                if p["kind"] == "tbd":
                    self.assertIn("2026-11-07", p.get("_tbd_reason", ""))
                    self.assertIn("http", p["_tbd_reason"])
                else:
                    self.assertIn(p["part"], P.parts)
                    self.assertTrue(P.parts[p["part"]]["status"].startswith("datasheet"))

    def test_panel_ports_model_the_parts_db_mpns(self):
        # the port model follows the MPN the parts DB holds for each port ref (W2 GR-2: P1 Adam Tech, P2/P3/P6/P8 CAB.718)
        db = json.loads((HERE.parent / "design" / "parts" / "parts.json").read_text(encoding="utf-8"))
        mpn = {r: e.get("mpn") for e in db["parts"] for r in e.get("refs", [])}
        ports = {p["id"]: p for p in P.mech["top_face"]["ports"]}
        for pid, ref in (("P1", "J401"), ("P2", "J402"), ("P3", "J403"), ("P6", "J406"), ("P8", "J408"), ("P4", "J404")):
            with self.subTest(port=pid):
                self.assertEqual(P.parts[ports[pid]["part"]]["mpn"], mpn[ref])

    def test_sma_ports_without_a_drawn_washer_stay_open(self):
        r = self._rule(P, "R-SMA-THREAD")
        for pid in ("P2", "P3", "P6", "P8"):
            # 11.4 - 0.2 - 4.5 - (1.8 + 0.3) - 3 x 0.706 = 2.48 left for the undrawn CAB.718 washer
            self.assertEqual(r["value_mm"][pid], "OPEN: washer thickness not drawn: 2.48 mm left for it after the nut and 3 threads")
        self.assertIn("2.32 mm left", r["value_mm"]["P1"])
        self.assertTrue(r["value_mm"]["P4"].startswith("PASS (model)"), r["value_mm"]["P4"])
        self.assertTrue(r["value_mm"]["P5"].startswith("OPEN"))
        self.assertTrue(r["result"].startswith("OPEN"), r["result"])

    def test_fallback_family_passes_the_thread_rule(self):
        import copy
        Q = copy.deepcopy(P)
        p2 = [p for p in Q.mech["top_face"]["ports"] if p["id"] == "P2"][0]
        p2.update({"kind": "sma_pigtail", "part": "taoglas_mhf1_sma_wp"})
        r = self._rule(Q, "R-SMA-THREAD")
        # 11.4 - 0.3 - 4.5 - (1.75 + 0.2) - (1.1 + 0.3) = 3.25 >= 3 x 0.706
        self.assertTrue(r["value_mm"]["P2"].startswith("PASS (model): 3.25 mm left"), r["value_mm"]["P2"])

    def test_a_thin_thread_fails_the_thread_rule(self):
        import copy
        Q = copy.deepcopy(P)
        Q.parts["taoglas_cab718"]["thread_len"] = 8.0      # nut alone leaves 7.8 - 4.5 - 2.1 = 1.2 < 2.12: FAIL before the washer
        r = self._rule(Q, "R-SMA-THREAD")
        self.assertTrue(r["result"].startswith("FAIL"), r["result"])
        self.assertIn("P2", r["result"])

    def test_cab718_cut_out_and_body(self):
        f = [x for x in face_features(P)["top"] if x["id"] == "P2"][0]
        self.assertEqual((f["shape"], f["d"], f["flat"]), ("dflat", 6.5, 6.0))
        nut = self._box(P, "nut.P2")
        self.assertAlmostEqual(nut[3] - nut[0], 8.0 / math.cos(math.radians(30)), places=6)
        self.assertAlmostEqual(nut[4] - nut[1], 3.4 + 0.2, places=6)

    def test_vfa340_nut_and_long_side_inside(self):
        v = P.parts["cinch_vfa340"]
        self.assertEqual((v["hex_af"], v["flange_t"], v["short_side"], v["overall"], v["nut_af"], v["nut_t"]), (11.0, 1.5, 7.6, 20.9, 11.0, 2.4))
        self.assertEqual(v["washer"], [12.0, 9.7, 0.4])
        nut = self._box(P, "nut.P4")
        self.assertAlmostEqual(nut[3] - nut[0], 11.0 / math.cos(math.radians(30)), places=6)
        self.assertAlmostEqual(nut[4] - nut[1], 20.9 - 7.6 - 1.5 - 4.5, places=6)
        r = self._rule(P, "R-SMA-THREAD")
        self.assertTrue(r["value_mm"]["P4"].startswith("PASS (model)"), r["value_mm"]["P4"])

    def test_unread_port_has_no_inner_envelope(self):
        names = {n for _, n, _, _ in layout.item_boxes(P)}
        self.assertNotIn("nut.P5", names)
        self.assertIn("nut.LAB_BUS", names)
        r = self._rule(P, "R-BULKHEAD-NUTS")
        self.assertTrue(r["result"].startswith("OPEN: no inner envelope for P5"), r["result"])
        self.assertIn("P4", r["value_mm"])

    def test_lab_bus_cut_out_is_the_drawing_d_cut(self):
        from srrx_mech.features import hole_outline
        f = [x for x in face_features(P)["bottom"] if x["id"] == "LAB_BUS"][0]
        self.assertEqual((f["shape"], f["d"], f["flat"], f["flange_d"]), ("dflat", 12.0, 11.2, 15.0))
        pts = hole_outline(f)
        self.assertAlmostEqual(max(v for _, v in pts), f["v"] + 11.2 - 6.0, places=6)
        self.assertAlmostEqual(min(v for _, v in pts), f["v"] - 6.0, places=2)

    def test_lab_bus_nut_takes_the_corners_and_clears_plate_and_seam(self):
        # the drawing's 14.60 is across flats: the envelope is 14.6 / cos 30 across the corners
        gx = P.parts["kinghelm_gx12_6p"]
        nut = self._box(P, "nut.LAB_BUS")
        self.assertAlmostEqual(nut[3] - nut[0], gx["nut_af"] / math.cos(math.radians(30)), places=6)
        self.assertLessEqual(nut[5], P.mech["stack_z"]["plate_rear"] - 0.5)
        lb = [p for p in P.mech["bottom_face"]["ports"] if p["id"] == "LAB_BUS"][0]
        keep = P.mech["gasket"]["belt_h"] + 0.5                       # R-PANEL-FLAT seam belt margin
        self.assertGreaterEqual(lb["z"] - gx["flange_d"] / 2, P.mech["split_z"] + keep)
        self.assertTrue(self._rule(P, "R-PANEL-FLAT")["result"].startswith("PASS"))
        coll, _ = layout.fit_checks(P)
        self.assertFalse([c for c in coll if "nut.LAB_BUS" in (c["a"], c["b"])], coll)

    def test_bottom_pitch_rule_fails_on_an_overlap(self):
        import copy
        r = self._rule(P, "R-BOTTOM-PITCH")
        self.assertTrue(r["result"].startswith("OPEN"), r["result"])
        Q = copy.deepcopy(P)
        a = [p for p in Q.mech["bottom_face"]["ports"] if p["id"] == "AUDIO_3V5"][0]
        a.update({"kind": "jack_3v5", "x": 195.0, "z": 30.0})
        r = self._rule(Q, "R-BOTTOM-PITCH")
        self.assertTrue(r["result"].startswith("FAIL"), r["result"])
        self.assertIn("LAB_BUS-AUDIO_3V5", r["result"])

    def test_pod_holes_come_from_read_parts(self):
        from srrx_mech.features import HOLES
        for p in P.antennas["sband_pod"]["ports"]:
            with self.subTest(port=p["id"]):
                self.assertIn(p["kind"], HOLES)
                self.assertIn(p["part"], P.parts)
        # RF_IN/RF_OUT and PWR are in the end walls, which the Hammond drawing does not dimension: worst case by difference
        hb = P.parts["hammond_1554u2gy"]
        end, _ = antennas.pod_wall_t(P, "right_end")
        self.assertAlmostEqual(end, (hb["outside"][0] - hb["inside"][0]) / 2, places=6)
        self.assertGreater(end, hb["wall"])
        self.assertLessEqual(end, P.parts["fairview_sm4955"]["panel_max"])
        gl = P.parts["lapp_skintop_st_m12"]
        self.assertGreaterEqual(gl["thread_len"] - end - gl["locknut_t"], 0.0)
        self.assertTrue(gl["uv_resistant"])                 # the pod is outdoors: black, UV-resistant variant
        lo, hi = gl["clamp"]
        self.assertTrue(lo <= 4.2 <= hi)
        r = self._rule(P, "R-POD-WALL")
        self.assertTrue(r["result"].startswith("PASS (model)"), r["result"])
        import copy
        Q = copy.deepcopy(P)
        Q.parts["lapp_skintop_st_m12"]["locknut_t"] = 4.5
        self.assertTrue(self._rule(Q, "R-POD-WALL")["result"].startswith("FAIL"))


@unittest.skipUnless(importlib.util.find_spec("build123d"), "build123d not installed")
class PanelPortsW2Mech2Cad(unittest.TestCase):
    def test_dflat_cutter_has_the_d_cut_area(self):
        from srrx_mech import cad
        f = [x for x in face_features(P)["bottom"] if x["id"] == "LAB_BUS"][0]
        L = 20.0
        c = cad.dflat_cutter(P, "bottom", f, L)
        r, h = f["d"] / 2, f["flat"] - f["d"] / 2
        seg = r * r * math.acos(h / r) - h * math.sqrt(r * r - h * h)     # circular segment beyond the flat
        self.assertAlmostEqual(c.volume, (math.pi * r * r - seg) * L, delta=0.5)
        bb = c.bounding_box()
        self.assertAlmostEqual(bb.max.Z, f["v"] + h, places=3)            # the flat is on the +v (front) side

    def test_top_face_d_cut_flat_faces_the_rear(self):
        from srrx_mech import cad
        f = [x for x in face_features(P)["top"] if x["id"] == "P2"][0]
        c = cad.dflat_cutter(P, "top", f, 20.0)
        bb = c.bounding_box()
        zc = P.mech["top_face"]["ports_z"]
        # top face +v points to -z (towards the rear): the flat is at zc - (flat - r), the arc reaches zc + r
        self.assertAlmostEqual(bb.min.Z, zc - (f["flat"] - f["d"] / 2), places=3)
        self.assertAlmostEqual(bb.max.Z, zc + f["d"] / 2, places=3)


class EnvelopeW2Mech3(unittest.TestCase):
    """W2 MECH-3 (B-08, A-PCB-02 mech handoff, CC-06, CC-12, J551/W425, fastener stacks)."""

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def _spec(self):
        return json.loads((HERE.parent / "pcb" / "partition-spec.json").read_text(encoding="utf-8"))

    def test_bay_arrangement_b_passes_with_the_read_socket(self):
        bp = rules.bay_packing(P)
        self.assertEqual(bp["chosen"], "b")
        self.assertTrue(bp["result"].startswith("PASS (model)"), bp["result"])
        self.assertFalse(bp["arrangements"]["a"]["fits"])
        self.assertTrue(bp["arrangements"]["b"]["fits"])
        self.assertEqual(bp["v4l_status"], "listing")                        # V4L reserve stays the listing maximum
        self.assertTrue(P.parts["wurth_614004190021"]["status"].startswith("datasheet"))
        self.assertEqual(bp["layout_outside_bay"], [])

    def test_bay_packing_fails_at_the_old_height(self):
        Q = self._copy()
        Q.mech["rf_bay"]["rect"][3] = 60.5                                   # the bay before the joint growth
        self.assertTrue(rules.bay_packing(Q)["result"].startswith("FAIL"))

    def test_joint_growth_is_inside_the_area_caps(self):
        env = self._spec()["envelope"]
        W, H, D = P.outer
        self.assertEqual(W, 230.0)                                           # width unchanged (STACK.md:109)
        self.assertLessEqual(H - 160.0, env["cap"]["dh_max"] + 1e-9)
        self.assertAlmostEqual(D - 66.0, env["dz"], places=6)
        self.assertLessEqual(D - 66.0, env["cap"]["dz_max"] + 1e-9)

    def test_pwr_b_is_the_mezzanine_over_pwr_a(self):
        spec = self._spec()
        par = spec["parameters"]
        a, b = P.boards["boards"]["PWR"], P.boards["boards"]["PWR_B"]
        t = P.board_t("PWR")    # W2 MECH-8: the PWR-A thickness (its own 6-layer stackup), no longer the shared 1.6 mm
        self.assertAlmostEqual(b["place"]["z_bottom"], a["place"]["z_bottom"] + t + par["stack"], places=6)
        self.assertEqual(a["max_height"], par["hA"])
        self.assertEqual(b["max_height"], par["hB"])
        self.assertEqual(b["holes"], a["holes"])                             # coaxial F45 standoffs
        self.assertEqual(b["place"]["origin"], a["place"]["origin"])
        for mo in a.get("modules_on_board", []):        # none since W2 MECH-7 (SHRINK-2: PWR-B is the full L)
            mx, my = mo["at"]
            mw, mh = P.parts[mo["part"]]["size"][:2]
            self.assertTrue(any(c[0] <= mx - par["window_margin"] + 1e-9 and mx + mw + par["window_margin"] <= c[0] + c[2] + 1e-9
                                and c[1] <= my - par["window_margin"] + 1e-9 and my + mh + par["window_margin"] <= c[1] + c[3] + 1e-9
                                for c in b["cutouts"]), mo["id"])
        for g in layout.channel_check(P):
            if g["item"].startswith(("PWR", "PWR_B")):
                self.assertGreaterEqual(g["gap_to_module_mm"], spec["envelope"]["air_channel"] - 1e-9, g)

    def test_ctrl_rear_zone_over_the_bms_meets_the_gr3_rule(self):
        cap = self._spec()["ctrl"]["bottom_header_rule"]
        zones = [z for z in P.boards["boards"]["CTRL"]["rear_zones"] if z["limit"] in ("bms", "ip2368")]
        self.assertTrue(zones)
        for z in zones:
            # the tallest placed CTRL bottom header + 1.0 clearance sets dz_ctrl (W2 GR-3: right-angle Micro-Fit 6.98 -> 4.08)
            self.assertGreaterEqual(z["free_mm"], cap["gap_mm"] + self._spec()["envelope"]["dz_ctrl"] - 1e-9, z)

    def test_ina_swm_and_j551_are_in_the_collision_set(self):
        names = {n for _, n, _, _ in layout.item_boxes(P)}
        self.assertTrue({"ina228", "swm_2813", "nut.J551", "usb_socket_a", "usb_socket_b"} <= names)
        coll, outside = layout.fit_checks(P)
        self.assertEqual([c for c in coll if c["gap_mm"] < 0], [])
        r = [x for x in rules.evaluate(P) if x["id"] == "R-J551"][0]
        self.assertTrue(r["result"].startswith("PASS (model)"), r["result"])

    def test_pololu_pin_rows_are_pocketed(self):
        r = [x for x in rules.evaluate(P) if x["id"] == "R-PWR-POCKETS"][0]
        self.assertFalse(r["result"].startswith("FAIL"), r["result"])
        # W2 MECH-7: the Pololu rows PK1/PK2 are gone with the modules; the bottom-part pockets PB* take their place
        self.assertTrue(r["value_mm"])
        self.assertTrue(all(k.startswith("PB") for k in r["value_mm"]), sorted(r["value_mm"]))
        Q = self._copy()
        Q.boards["boards"]["PWR"]["tht_pockets"]["depth"] = 0.5               # below the 1.0 mm rule
        r = [x for x in rules.evaluate(Q) if x["id"] == "R-PWR-POCKETS"][0]
        self.assertTrue(r["result"].startswith("FAIL"), r["result"])

    def test_fastener_stacks_cover_every_screw_row(self):
        from srrx_mech import fasteners
        doc = fasteners.stacks(P)
        text = (HERE.parent / "tools" / "assembly_data.py").read_text(encoding="utf-8")
        start = text.index("FASTENERS = [")
        rows = set(re.findall(r'^    \("(F\d+[ab]?)",', text[start:text.index("\n]", start)], re.M))
        covered = {r.strip() for j in doc["joints"] for r in j["build17_row"].split("/")} | set(doc["nut_and_kit_rows"])
        self.assertTrue({"F45", "F46", "F06"} <= rows)
        self.assertEqual(sorted(rows - covered), [])
        self.assertEqual(doc["summary"]["FAIL"], 0)

    def test_a_short_insert_fails_the_closure_stack(self):
        from srrx_mech import fasteners
        Q = self._copy()
        Q.mech["closure"]["insert"]["len"] = 2.0
        j = [x for x in fasteners.stacks(Q)["joints"] if x["id"] == "CLOSURE"][0]
        self.assertTrue(j["result"].startswith("FAIL"), j["result"])


class EnvelopeW2Mech3Review(unittest.TestCase):
    """W2 MECH-3 review fixes: PWR-B usable area, computed depth reason, PEM shank windows, IMU screw rows, ISO lengths."""

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def _budget(self):
        d = json.loads((HERE.parent / "pcb" / "partition-budget.json").read_text(encoding="utf-8"))
        return d["candidates"][d["chosen"]]

    def test_pwr_b_area_is_judged_against_the_budget_usable_area(self):
        row = boards.area_check(P)["boards"]["PWR_B"]
        usable = self._budget()["boards"]["PWR_B"]["usable_mm2"]
        self.assertEqual(row["usable_mm2"], round(usable, 0))
        self.assertLess(row["usable_mm2"], row["area_mm2"])                    # the outline minus the Pololu windows is an upper bound
        planned = row.get("planned_budget")                                     # W2 MECH-7: pending SHRINK-2 changes judge the planned demand
        need = planned["demand_1_8_mm2"] if planned else row["need_1_8_mm2"]
        self.assertEqual(row["result"].startswith("PASS"), need <= usable, row["result"])
        self.assertIn("partition-budget.json", row["result"])

    def test_envelope_reason_is_computed_from_the_stack(self):
        import build
        sz = P.mech["stack_z"]
        dz = json.loads((HERE.parent / "pcb" / "partition-spec.json").read_text(encoding="utf-8"))["envelope"]["dz"]
        reason = build.envelope_report(P)["reason"]
        self.assertIn(f"front layer {round(sz['module_back'] - sz['plate_front'], 2):g}", reason)
        self.assertIn(f"dz {dz:g}", reason)
        self.assertNotIn("dz 2.1", reason)
        Q = self._copy()
        Q.mech["stack_z"]["module_back"] += 1.0
        self.assertIn(f"front layer {round(sz['module_back'] + 1.0 - sz['plate_front'], 2):g}", build.envelope_report(Q)["reason"])

    def test_pem_nut_windows_use_the_shank(self):
        from srrx_mech import fasteners
        pem, t = P.parts["pem_f_m3_1"], P.mech["plate"]["t"]
        J = {j["id"]: j for j in fasteners.stacks(P)["joints"]}
        for jid in ("ANGLES", "PWR_A-PLATE"):
            j = J[jid]
            self.assertEqual(j["receiver"]["thread_mm"], pem["shank"])
            self.assertEqual(j["length_window_mm"], [round(j["grip_mm"] + pem["shank"], 2), round(j["grip_mm"] + t, 2)])
            self.assertLess(j["length_window_mm"][0], j["length_window_mm"][1], jid)
        self.assertTrue(J["ANGLES"]["result"].startswith("PASS (model)"), J["ANGLES"]["result"])   # the F31 M3 x 4 fits

    def test_imu_screw_rows_are_joints_with_open_reasons(self):
        from srrx_mech import fasteners
        doc = fasteners.stacks(P)
        rows = {j["build17_row"]: j for j in doc["joints"]}
        for r in ("F24", "F36", "F37"):
            self.assertIn(r, rows)
            self.assertNotIn(r, doc["nut_and_kit_rows"])
            self.assertTrue(rows[r]["result"].startswith("OPEN: "), rows[r]["result"])
            self.assertGreater(len(rows[r]["result"]), len("OPEN: ") + 20)

    def test_pass_needs_a_named_iso_length_in_the_window(self):
        from srrx_mech import fasteners
        for j in fasteners.stacks(P)["joints"]:
            if j["result"].startswith("PASS"):
                ol = j.get("orderable_lengths", {})
                self.assertTrue(ol.get("named_in_build17"), j["id"])
                self.assertTrue(ol.get("in_window"), j["id"])
        J = {j["id"]: j for j in fasteners.stacks(P)["joints"]}
        for jid in ("CTRL", "ENC", "UFS-BOSS"):
            self.assertTrue(J[jid]["result"].startswith("OPEN"), J[jid]["result"])
        Q = self._copy()
        Q.mech["closure"]["insert"]["len"] += 1.0                                 # a deeper insert widens the window: still an ISO length
        self.assertTrue([j for j in fasteners.stacks(Q)["joints"] if j["id"] == "CLOSURE"][0]["result"].startswith("PASS"))

    def test_pocket_rule_reports_the_budget_items(self):
        r = [x for x in rules.evaluate(P) if x["id"] == "R-PWR-POCKETS"][0]
        n = len(self._budget()["pwr_a_tht_pocket_items"])
        self.assertIn(f"{n} items", r["result"])


class RoutesW2Mech4(unittest.TestCase):
    """W2 MECH-4: HDMI FPC route, PV6 nut reserve, F101 access decision, P8 accessory row."""

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def _rule(self, Q, rid):
        return [x for x in rules.evaluate(Q) if x["id"] == rid][0]

    def test_hdmi_fpc_route_is_in_the_envelope_check(self):
        names = {n for _, n, _, _ in layout.item_boxes(P)}
        self.assertTrue(set(P.mech["hdmi_route"]["envelopes"]) <= names)
        self.assertNotIn("hdmi_plug_ra", names)
        coll, outside = layout.fit_checks(P)
        env = set(P.mech["hdmi_route"]["envelopes"])
        self.assertEqual([c for c in coll if c["gap_mm"] < 0.5 and (c["a"] in env or c["b"] in env)], [])
        r = self._rule(P, "R-HDMI-ROUTE")
        self.assertTrue(r["result"].startswith("PASS (model)"), r["result"])
        for s in r["value_mm"]["segments"].values():
            self.assertGreaterEqual(s["slack_mm"], 0.0)

    def test_hdmi_route_fails_when_an_envelope_collides_or_a_flex_is_short(self):
        Q = self._copy()
        for it in Q.mech["layout"]["items"]:
            if it["id"] == "hdmi_insert":
                it["box"][0] -= 2.0                     # into the BMS
        self.assertTrue(self._rule(Q, "R-HDMI-ROUTE")["result"].startswith("FAIL"))
        Q = self._copy()
        Q.parts["adafruit_flex"]["lengths"]["3560"] = 60.0
        self.assertTrue(self._rule(Q, "R-HDMI-ROUTE")["result"].startswith("FAIL"))

    def test_harness_anchor_of_the_hdmi_run_is_kept(self):
        box = [it for it in P.mech["layout"]["items"] if it["id"] == "hdmi_route_front_run"][0]["box"]
        self.assertAlmostEqual(box[1] + box[4], 76.8)   # waypoint y 78.0 of the CTRL harness drops (harness_routes)

    def test_pwr_key_nut_reserve_clears_and_stays_open(self):
        names = {n for _, n, _, _ in layout.item_boxes(P)}
        self.assertIn("nut.PWR_KEY", names)
        r = self._rule(P, "R-PWR-KEY-NUT")
        self.assertTrue(r["result"].startswith("OPEN"), r["result"])
        self.assertGreaterEqual(r["value_mm"]["worst"][1], 0.5)
        coll, _ = layout.fit_checks(P)
        self.assertEqual([c for c in coll if {"pwr_key_body", "plate.main"} == {c["a"], c["b"]}], [])
        Q = self._copy()
        Q.parts["pv6_button"]["nut_d"] = 26.0                # reaches the top Al angle
        self.assertTrue(self._rule(Q, "R-PWR-KEY-NUT")["result"].startswith("FAIL"))

    def test_f101_access_decision_follows_the_depth(self):
        r = self._rule(P, "R-F101-ACCESS")
        self.assertIn("seam", r["result"])
        self.assertGreater(r["value_mm"]["stack"], r["value_mm"]["free_depth"])
        Q = self._copy()
        Q.parts["littelfuse_mini_297"]["body"][2] = 1.0
        self.assertIn("fits facing the hatch", self._rule(Q, "R-F101-ACCESS")["result"])

    def test_p8_accessory_row_is_open_until_the_lna_is_measured(self):
        r = self._rule(P, "R-P8-ACCESSORY")
        self.assertTrue(r["result"].startswith("OPEN"), r["result"])
        self.assertTrue(r["value_mm"]["outside_enclosure"])


class RoutesW2Mech4Review(unittest.TestCase):
    """W2 MECH-4 review fixes: R-F101-ACCESS keeps the USB-A plug access, R-HDMI-ROUTE labels the harness centrelines and the slot."""

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def _rule(self, Q, rid):
        return [x for x in rules.evaluate(Q) if x["id"] == rid][0]

    def test_f101_place_in_front_of_the_usb_plug_bay_is_never_hatch_access(self):
        r = self._rule(P, "R-F101-ACCESS")
        self.assertTrue(r["result"].startswith("PASS (model, decision: seam)"), r["result"])
        self.assertEqual(r["value_mm"]["access_path_to"], ["usb_plug_bay"])
        Q = self._copy()
        Q.parts["littelfuse_mini_297"]["body"][2] = 1.0         # depth fits, the strip is still the USB-A plug access path
        r = self._rule(Q, "R-F101-ACCESS")
        self.assertLessEqual(r["value_mm"]["stack"], r["value_mm"]["free_depth"])
        self.assertTrue(r["result"].startswith("PASS (model, decision: seam)"), r["result"])
        for it in Q.mech["layout"]["items"]:
            if it["id"] == "usb_plug_bay":
                it["keep_clear"] = False                         # no access path behind the place: the depth decides
        r = self._rule(Q, "R-F101-ACCESS")
        self.assertTrue(r["result"].startswith("PASS (model): F101 fits facing the hatch"), r["result"])
        self.assertEqual(r["value_mm"]["access_path_to"], [])

    def test_hdmi_route_labels_harness_centrelines_and_the_slot_height(self):
        r = self._rule(P, "R-HDMI-ROUTE")
        self.assertTrue(r["result"].startswith("PASS (model)"), r["result"])
        self.assertIn("harness bundles are centrelines", r["result"])
        self.assertIn("bare flex must be <= 0.5", r["result"])
        near = r["value_mm"]["harness_near"]                     # follows the harness routes (MECH-6 may move the CTRL drops)
        sid, env, d = near["nearest_centreline"]
        self.assertIn(env, P.mech["hdmi_route"]["envelopes"])
        self.assertIn(f"the nearest, {sid}, runs {d:g} mm from {env}", r["result"])
        self.assertEqual(near["bundle_overlaps"] > 0, "reach into" in r["result"])
        Q = self._copy()
        Q.parts["adafruit_flex"]["thickness"] = 0.8               # a measured bare flex thicker than the WE-FLAT slot
        self.assertTrue(self._rule(Q, "R-HDMI-ROUTE")["result"].startswith("FAIL"))


class ModulesW2Mech5(unittest.TestCase):
    """W2 MECH-5: module envelopes with part keys, module fixing (bosses, pad, pocket, plate PEM standoffs) and the INA228 terminal side."""

    ITEMS = ("hub_ch334f", "veml7700", "t7_insert", "hdmi_insert", "pack_fuse", "boni_a406", "ina228", "swm_2813")

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def _rule(self, Q, rid):
        return [x for x in rules.evaluate(Q) if x["id"] == rid][0]

    def test_items_have_parts_with_status_and_no_collision(self):
        items = {it["id"]: it for it in P.mech["layout"]["items"]}
        for iid in self.ITEMS:
            with self.subTest(item=iid):
                self.assertIn(iid, items)
                part = P.parts[items[iid]["part"]]
                self.assertTrue(part["status"] and part["src"])
        coll, outside = layout.fit_checks(P)
        self.assertEqual([c for c in coll if c["gap_mm"] < 0 and ({c["a"], c["b"]} & set(self.ITEMS))], [])
        self.assertEqual([o for o in outside if o["item"] in self.ITEMS], [])

    def test_module_mounts_pass_and_follow_the_board_files(self):
        r = self._rule(P, "R-MODULE-MOUNTS")
        self.assertTrue(r["result"].startswith("PASS (model)"), r["result"])
        hub = P.parts["adafruit_5997"]
        self.assertEqual(len(hub["holes"]["uv"]), 4)
        mt = {m["item"]: m for m in P.mech["module_mounts"]["mounts"]}
        sx = sorted({round(c[0], 2) for c in mt["hub_ch334f"]["screws"]})
        sy = sorted({round(c[1], 2) for c in mt["hub_ch334f"]["screws"]})
        du = hub["holes"]["uv"][1][0] - hub["holes"]["uv"][0][0]
        dv = hub["holes"]["uv"][2][1] - hub["holes"]["uv"][0][1]
        self.assertEqual(sorted([round(sx[1] - sx[0], 2), round(sy[1] - sy[0], 2)]), sorted([round(du, 2), round(dv, 2)]))   # either board orientation
        self.assertEqual(P.parts["pololu_2813"]["mount_holes"], 0)
        self.assertIn("pad", mt["swm_2813"])
        self.assertGreaterEqual(r["value_mm"]["ina228"]["terminal"]["free_mm"], P.parts["adafruit_ina228_5832"]["terminal"]["wire_room"])

    def test_ina228_terminal_blocked_again_fails(self):
        Q = self._copy()
        ina = [it for it in Q.mech["layout"]["items"] if it["id"] == "ina228"][0]
        mt = [m for m in Q.mech["module_mounts"]["mounts"] if m["item"] == "ina228"][0]
        dx = 30.0                                            # module and its bosses together: the terminal edge then faces the LC76G (6.2 mm)
        ina["box"][0] += dx
        for kind in ("screws", "rests"):
            mt[kind] = [[c[0] + dx, c[1]] for c in mt[kind]]
        r = self._rule(Q, "R-MODULE-MOUNTS")
        self.assertTrue(r["result"].startswith("FAIL"), r["result"])
        self.assertIn("ina228 terminal wire side", r["result"])

    def test_pack_fuse_standoffs_are_plate_holes_with_the_pem_edge_rule(self):
        pf = [h for h in rules.plate_holes(P) if h["id"].startswith("PF")]
        self.assertEqual(len(pf), 2)
        for h in pf:
            self.assertGreaterEqual(rules.edge_distance(P, h["c"]), h["edge_min"] - 1e-9)
        for rid in ("R-HOLE-EDGE", "R-CLINCH-EDGE"):
            self.assertTrue(self._rule(P, rid)["result"].startswith("PASS"), rid)

    def test_veml_board_clears_the_front_wall_and_sits_behind_the_window(self):
        vw = P.mech["top_face"]["veml7700_window"]
        box = [b for i, n, b, it in layout.item_boxes(P) if i == "veml7700"][0]
        v = P.parts["adafruit_4162"]
        self.assertAlmostEqual(box[0] + v["sensor_uv"][0], vw["x"])
        self.assertAlmostEqual(box[2] + v["sensor_uv"][1], vw["z"])
        self.assertGreaterEqual(P.mech["stack_z"]["front_wall_inner"] - box[5], 0.5)


class SlotFillAndW2Mech6(unittest.TestCase):
    """W2 MECH-6: slot fill with the chosen wire and trim, the P7 pigtail, the PPS worst case, the VCC_3V3_MKEY tap,
    the NTC markers and the header refs at the route ends."""

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def test_slot_fill_passes_with_the_trim_and_fails_when_too_small(self):
        r = rules.plate_slot_fill(P)
        self.assertTrue(r["result"].startswith("PASS (model)"), r["result"])
        for sid, v in r["value_mm"].items():
            with self.subTest(slot=sid):
                self.assertLessEqual(v["bundle_need_mm2"], v["inner_mm2"])
                self.assertEqual(v["legs_clear"], "yes")
        self.assertEqual(r["value_mm"]["SL1"]["ribbon"]["stack_mm"], 2 * P.parts["ribbon_3m_3365_40"]["t"])
        Q = self._copy()
        sl2 = next(s for s in Q.mech["plate"]["slots"] if s["id"] == "SL2")
        sl2["rect"][3] = 5.0
        r = rules.plate_slot_fill(Q)
        self.assertTrue(r["result"].startswith("FAIL"), r["result"])

    def test_a_grommet_leg_under_a_resting_part_fails(self):
        Q = self._copy()
        sl2 = next(s for s in Q.mech["plate"]["slots"] if s["id"] == "SL2")
        sl2["trim"]["bottom"] = "grommet"                     # legs would sit under PWR-A (0.4 mm above the plate)
        r = rules.plate_slot_fill(Q)
        self.assertTrue(r["result"].startswith("FAIL"), r["result"])
        self.assertIn("PWR.r0", r["value_mm"]["SL2"]["result"])

    def test_every_slot_wire_has_a_read_od(self):
        od = P.parts["hookup_wire_ptfe"]["od"]
        path = HERE.parent / "build" / "16-dzhgut.csv"
        if not path.exists():
            self.skipTest("build/16-dzhgut.csv not present")
        with path.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        flat = set(P.mech["harness_routes"]["flat"])
        for sl in P.mech["plate"]["slots"]:
            for w in rows:
                if w["segment"] in sl["segments"] and w["segment"] not in flat:
                    self.assertIn(w["awg"], od, (sl["id"], w["wire"]))

    def test_p7_pigtail_and_thread(self):
        from srrx_mech import routes
        res = routes.evaluate(P)
        row = next(r for r in routes.route_rules(P, res) if r["id"] == "R-P7-PIGTAIL")
        self.assertTrue(row["result"].startswith("PASS (model)"), row["result"])
        fit, _ = routes.pigtail_choice(P, res, "W407")
        self.assertEqual(fit["mpn"], P.mech["harness_routes"]["coax"]["W407"]["chosen"])
        self.assertEqual(res["coax"]["W407"]["crossings"], [])
        p7 = next(p for p in P.mech["top_face"]["ports"] if p["id"] == "P7")
        self.assertEqual(p7["part"], "taoglas_mhf1_sma_wp")
        thr = next(r for r in rules.evaluate(P) if r["id"] == "R-SMA-THREAD")
        self.assertTrue(thr["value_mm"]["P7"].startswith("PASS (model)"), thr["value_mm"]["P7"])

    def test_pps_passes_at_the_worst_case_and_fails_when_the_gnss_moves_far(self):
        row = next(r for r in rules.evaluate(P) if r["id"] == "R-PPS-LEN")
        self.assertTrue(row["result"].startswith("PASS (model)"), row["result"])
        self.assertLessEqual(row["value_mm"]["branch_max_mm"], row["limit_mm"])
        Q = self._copy()
        it = next(i for i in Q.mech["layout"]["items"] if i["id"] == "lc76g")
        it["box"][0] -= 50.0
        row = next(r for r in rules.evaluate(Q) if r["id"] == "R-PPS-LEN")
        self.assertTrue(row["result"].startswith("FAIL"), row["result"])

    def test_s17_ends_on_the_mkey_tap(self):
        from srrx_mech import routes
        tap = P.parts["q6a"]["mkey_tap"]
        self.assertEqual((tap["ref"], tap["net"], tap["side"]), ("C17", "VCC_3V3_MKEY", "bottom"))
        self.assertIn("radxa_dragon_q6a_schematic_v1.21.pdf", tap["src"])
        self.assertIn("components_placement_map_v1.21.pdf", tap["src"])
        r = routes.evaluate(P)["segments"]["S17"]
        pt = routes.points(P)["q6a.mkey_tap"][1][:3]
        self.assertEqual(tuple(r["points_mm"][-1]), tuple(pt))
        self.assertEqual(r["crossings"], [])

    def test_ntc_markers_are_routed_and_in_the_collision_set(self):
        from srrx_mech import routes
        names = {n for _, n, _, _ in layout.item_boxes(P)}
        self.assertTrue({"ntc_panel", "ntc_case"} <= names)
        coll, _ = layout.fit_checks(P)
        self.assertEqual([c for c in coll if c["gap_mm"] < 0], [])
        res = routes.evaluate(P)
        for sid in ("S39", "S40"):
            with self.subTest(segment=sid):
                self.assertIsNotNone(res["segments"][sid]["length_mm"])
                self.assertEqual(res["segments"][sid]["crossings"], [])

    def test_edge_ends_name_the_header_refs(self):
        from srrx_mech import routes
        if not (HERE.parent / "build" / "16-dzhgut-rozyemy.csv").exists():
            self.skipTest("build/16-dzhgut-rozyemy.csv not present")
        res = routes.evaluate(P)
        self.assertTrue(any("J304" in p for p in res["segments"]["S01"]["provisional"]))
        self.assertTrue(any("J207" in p and "PWR_B" in p for p in res["segments"]["S20"]["provisional"]))
        self.assertTrue(any("J318" in p for p in res["segments"]["S39"]["provisional"]))


class SlotFillW2Mech6Review(unittest.TestCase):
    """W2 MECH-6 review: the Essentra MGS-2-01 legs reach the inside depth D onto each face, the loose wires must pack
    beside / on the rigid S01 ribbon, and the SL3 edge next to the BMS takes the tape."""

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def test_edging_reach_is_the_inside_depth_d(self):
        g = P.parts[P.mech["plate"]["slot_trim"]["grommet"]]
        reach, proud = rules.trim_legs(P, g)
        self.assertAlmostEqual(reach, 0.100 * 25.4, places=3)                 # D 0.100 in (catalogue p.276)
        self.assertAlmostEqual(g["overall_h"], (0.055 + 0.100) * 25.4, places=3)  # C + D
        self.assertAlmostEqual(reach, g["inside_d"], places=6)
        self.assertGreater(proud, 0.0)

    def test_loose_wires_pack_beside_and_on_the_ribbon(self):
        r = rules.plate_slot_fill(P)
        self.assertTrue(r["result"].startswith("PASS (model)"), r["result"])
        for sid, v in r["value_mm"].items():
            with self.subTest(slot=sid):
                self.assertEqual(v["packing"]["unplaced"], 0)
        sl1 = r["value_mm"]["SL1"]
        self.assertEqual(len(sl1["packing"]["regions_mm"]), 2)
        Q = self._copy()
        s = next(x for x in Q.mech["plate"]["slots"] if x["id"] == "SL1")
        s["rect"] = [168.5, 93.2, 27.5, 3.8]                                  # the first size: area passed, the third wire had no place
        v = rules.plate_slot_fill(Q)["value_mm"]["SL1"]
        self.assertLessEqual(v["bundle_need_mm2"], v["inner_mm2"])
        self.assertGreater(v["packing"]["unplaced"], 0)
        self.assertIn("wire packing", v["result"])

    def test_shelf_pack_counts_round_wires(self):
        self.assertEqual(rules._shelf_pack([1.09] * 3, 1.9, 2.3), [1.09])     # two stacked fit, the third does not
        self.assertEqual(rules._shelf_pack([1.09] * 4, 2.2, 2.2), [])
        self.assertEqual(rules._shelf_pack([2.0], 1.9, 5.0), [2.0])

    def test_sl3_bms_edge_takes_the_tape(self):
        sl3 = next(x for x in P.mech["plate"]["slots"] if x["id"] == "SL3")
        self.assertEqual(sl3["trim"]["left"], "tape")
        self.assertEqual(sl3["trim"]["right"], "grommet")
        Q = self._copy()
        s = next(x for x in Q.mech["plate"]["slots"] if x["id"] == "SL3")
        s["trim"]["left"] = "grommet"                                         # legs would sit under the BMS (0.5 mm above the plate)
        v = rules.plate_slot_fill(Q)["value_mm"]["SL3"]
        self.assertIn("bms", v["result"])


class ModulesW2Mech5Review(unittest.TestCase):
    """W2 MECH-5 review fixes: re-placement after MECH-6 (LC76G, case NTC, W407), tripod pocket clearance, insert hole depth and
    the M2.5 x 6 window, tape joints, harness-bundle clearance and the INA228 terminal room with bundles."""

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def _rule(self, Q, rid):
        return [x for x in rules.evaluate(Q) if x["id"] == rid][0]

    def test_merged_layout_has_no_collision_and_the_p7_pigtail_is_clear(self):
        coll, outside = layout.fit_checks(P)
        self.assertEqual([c for c in coll if c["gap_mm"] < 0], [])
        for rid in ("R-P7-PIGTAIL", "R-ROUTE-CLEAR"):
            self.assertFalse(self._rule(P, rid)["result"].startswith("FAIL"), rid)
        from srrx_mech import routes
        res = routes.evaluate(P)
        self.assertFalse(any("boni_a406" in c for c in res["coax"]["W407"]["crossings"]))
        self.assertFalse(any("t7_insert" in c for r in res["segments"].values() for c in r.get("crossings", [])))

    def test_insert_holes_keep_clear_of_the_tripod_pocket(self):
        from srrx_mech import interference
        self.assertEqual(interference.ALLOWED["tripod_boss"], {"rear.tripod_boss"})
        r = self._rule(P, "R-MODULE-MOUNTS")
        d = [s["to_tripod_pocket_mm"] for item in ("hub_ch334f", "ina228") for s in r["value_mm"][item]["screws"]]
        self.assertGreaterEqual(min(d), P.mech["module_mounts"]["tripod_clear"])
        Q = self._copy()
        mt = [m for m in Q.mech["module_mounts"]["mounts"] if m["item"] == "hub_ch334f"][0]
        hub = [it for it in Q.mech["layout"]["items"] if it["id"] == "hub_ch334f"][0]
        dx, dy = 6.06, 11.3                                  # hub and bosses together: a corner hole at (90.44, 68.08) as in the first MECH-5 place
        hub["box"][0] += dx
        hub["box"][1] += dy
        mt["screws"] = [[round(c[0] + dx, 2), round(c[1] + dy, 2)] for c in mt["screws"]]
        r = self._rule(Q, "R-MODULE-MOUNTS")
        self.assertTrue(r["result"].startswith("FAIL"), r["result"])
        self.assertIn("hub_ch334f screws (90.44, 68.08)", r["result"])
        self.assertLess(min(s["to_tripod_pocket_mm"] for s in r["value_mm"]["hub_ch334f"]["screws"]), 3.0)

    def test_rear_insert_joints_take_an_iso_length_with_full_engagement(self):
        from srrx_mech import fasteners
        J = {j["id"]: j for j in fasteners.stacks(P)["joints"]}
        ins = P.mech["module_mounts"]["insert"]
        self.assertGreaterEqual(ins["hole_depth"], ins["len"] + 0.5)
        for jid in ("INA228", "HUB-5997"):
            j = J[jid]
            self.assertTrue(j["result"].startswith("PASS (model)"), j["result"])
            self.assertIn(6, j["orderable_lengths"]["in_window"])
            self.assertGreaterEqual(6 - j["grip_mm"], fasteners.ENG_INSERT * 2.5)
        for g in rules.module_mount_geometry(P):
            if g["on"] == "rear_wall" and g.get("insert"):
                self.assertGreaterEqual(g["seat"] - g["hole_depth"], 1.0)    # rear-wall skin under the hole
        for jid in ("SWM-2813", "VEML7700"):
            self.assertTrue(J[jid]["result"].startswith("OPEN: tape joint"), J[jid]["result"])
            self.assertIsNone(J[jid]["length_window_mm"])
        self.assertIn("PCB-SB2", J["PACK-FUSE"]["result"])
        self.assertNotIn("fixing not designed", " ".join(J[j]["result"] for j in ("INA228", "HUB-5997", "SWM-2813", "PACK-FUSE")))

    def test_veml_is_taped_on_rests_with_locating_spigots(self):
        mt = [m for m in P.mech["module_mounts"]["mounts"] if m["item"] == "veml7700"][0]
        self.assertNotIn("screws", mt)
        holes = [(round(107.3 + u, 3), round(49.284 + v, 3)) for u, v in P.parts["adafruit_4162"]["holes"]["uv"]]
        self.assertEqual(sorted(tuple(round(c, 3) for c in r) for r in mt["rests"]), sorted(holes))
        g = [x for x in rules.module_mount_geometry(P) if x["item"] == "veml7700"]
        self.assertTrue(all(abs(x["seat"] - (mt["seat_y"] + mt["tape_t"])) < 1e-9 for x in g if x["kind"] == "rests"))
        self.assertEqual(len([x for x in g if x["kind"] == "spigot"]), 2)

    def test_terminal_room_counts_harness_bundles(self):
        ina = [b for i, n, b, it in layout.item_boxes(P) if i == "ina228"][0]
        fake = [("SX", {"ends": ["A", "B"], "bundle_od_mm": 4.0, "points_mm": [[ina[0], ina[4] + 5.0, ina[2] + 3.0], [ina[3], ina[4] + 5.0, ina[2] + 3.0]]}),
                ("S06", {"ends": ["PWR", "INA"], "bundle_od_mm": 6.0, "points_mm": [[ina[0], ina[4] + 1.0, ina[2] + 3.0], [ina[3], ina[4] + 1.0, ina[2] + 3.0]]})]
        env, room, lim = rules._terminal_room(P, ina, "+y", fake, "INA", P.mech["wall"])
        self.assertEqual((room, lim), (3.0, "SX"))                                   # its own S06 bundle is not counted
        self.assertGreater(env, room)

    def test_new_envelopes_keep_the_bundle_clearance(self):
        r = self._rule(P, "R-MODULE-MOUNTS")
        bc = r["value_mm"]["bundle_clearance"]
        self.assertTrue({"hub_ch334f", "ina228", "t7_insert", "pack_fuse", "boni_a406"} <= set(bc))
        for iid, v in bc.items():
            self.assertGreaterEqual(v["centreline_mm"], v["need_mm"] - 1e-6, iid)
        Q = self._copy()
        pf = [it for it in Q.mech["layout"]["items"] if it["id"] == "pack_fuse_board"][0]
        pf["box"][2] += 2.0                                 # carrier board raised towards the y 38.2 / z 53 trunk
        self.assertIn("pack_fuse_board", self._rule(Q, "R-MODULE-MOUNTS")["result"])

    def test_case_ntc_lies_under_the_pack_fuse_carrier_clear_of_the_standoffs(self):
        boxes = {i: b for i, n, b, it in layout.item_boxes(P)}
        pf, ntc = boxes["pack_fuse_board"], boxes["ntc_case"]
        self.assertGreaterEqual(pf[2] - ntc[5], 0.5)
        self.assertTrue(P.parts[[it for it in P.mech["layout"]["items"] if it["id"] == "pack_fuse_board"][0]["part"]]["status"])
        r = self._rule(P, "R-MODULE-MOUNTS")
        self.assertTrue(all(x["gap_mm"] >= 0.5 for x in r["value_mm"]["plate_standoffs"]["pack_fuse"]))
        coll, _ = layout.fit_checks(P)
        self.assertEqual([c for c in coll if "pack_fuse" in c["a"] + c["b"]], [])       # PM4 plate boss included (no allowance)


class ContractW2Mech7(unittest.TestCase):
    """W2 MECH-7 (SHRINK-2), part 1: PWR-A without modules, zones 3/4, two-sided pockets, full-L PWR-B, H-TRIM, mated heights."""

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def _rule(self, Q, rid):
        return [x for x in rules.evaluate(Q) if x["id"] == rid][0]

    def _spec(self):
        return json.loads((HERE.parent / "pcb" / "partition-spec.json").read_text(encoding="utf-8"))

    def test_pwr_a_has_no_module_and_zones_3_4_hold_the_converters(self):
        a = P.boards["boards"]["PWR"]
        self.assertNotIn("modules_on_board", a)
        self.assertFalse([z for z in a.get("height_zones", []) if z["max_height"] > a["max_height"]])
        planned = self._spec()["candidates"]["shrink2"]["pwr_a_bottom"]["thermal_bond_planned"]
        for zn, rect in planned.items():
            self.assertEqual(a["thermal_bond"][int(zn) - 1], rect, zn)
        self.assertTrue(self._rule(P, "R-PWR-ZONES")["result"].startswith("PASS (model)"))
        self.assertTrue(self._rule(P, "R-PWR-PADS")["result"].startswith("PASS (model)"))
        self.assertTrue(self._rule(P, "R-UFS-REG")["result"].startswith("PASS (model)"))
        Q = self._copy()
        Q.boards["boards"]["PWR"]["thermal_bond"][3] = [7, 73, 5, 5]                 # zone 4 smaller than U108 (part 2: graph courtyard 5.9 x 6.0)
        self.assertTrue(self._rule(Q, "R-PWR-ZONES")["result"].startswith("FAIL"))

    def test_pwr_b_is_the_full_l_with_the_new_spans(self):
        a, b = P.boards["boards"]["PWR"], P.boards["boards"]["PWR_B"]
        self.assertNotIn("cutouts", b)
        self.assertEqual(b["outline"], a["outline"])
        self.assertAlmostEqual(sum(r[2] * r[3] for r in b["rects"]), boards.poly_area([tuple(p) for p in b["outline"]]), places=6)
        spans = [(z["edge"], z["span"]) for z in b["edge_zones"]]
        self.assertTrue(any(e == "top" and s[0] <= 84 and s[1] >= 107 for e, s in spans))    # part 2: the top span holds the PHD place x 84-107
        self.assertTrue(any(e == "bottom" and s[1] - s[0] >= 20.9 for e, s in spans))
        self.assertEqual(boards.contract(P)["boards"]["PWR_B"]["cutouts_mm"], [])

    def test_bottom_pockets_keep_the_lands_and_corridors(self):
        a = P.boards["boards"]["PWR"]
        sp = P.mech["plate"]["pwr_bottom_pockets"]
        regions = rules.pwr_bottom_regions(P)
        self.assertTrue(regions)
        land = sp["bond_land"]
        for pid, (x, y, w, h) in regions:
            self.assertGreaterEqual(min(w, h), sp["min_w"] - 1e-9, pid)
            for cx, cy in ((x, y), (x + w, y), (x, y + h), (x + w, y + h)):     # inside the PWR-A L
                self.assertTrue(any(r[0] - 1e-9 <= cx <= r[0] + r[2] + 1e-9 and r[1] - 1e-9 <= cy <= r[1] + r[3] + 1e-9 for r in a["rects"]), pid)
            for z in a["thermal_bond"]:
                g = rules._rect_gap((x, y, x + w, y + h), (z[0], z[1], z[0] + z[2], z[1] + z[3]))
                self.assertGreaterEqual(g, land - 1e-6, (pid, z))
            for k in sp["keep_full"]:
                kr = k["rect"]
                self.assertGreaterEqual(rules._rect_gap((x, y, x + w, y + h), (kr[0], kr[1], kr[0] + kr[2], kr[1] + kr[3])), -1e-9, (pid, kr))
        r = self._rule(P, "R-PWR-POCKETS")
        self.assertTrue(r["result"].startswith("OPEN"), r["result"])
        Q = self._copy()
        Q.boards["boards"]["PWR"]["tht_pockets"]["depth"] = 1.6                     # web 0.4 < web_min 1.0
        self.assertTrue(self._rule(Q, "R-PWR-POCKETS")["result"].startswith("FAIL"))

    def test_bottom_room_and_area(self):
        r = self._rule(P, "R-PWR-BOTTOM")
        sp, bs = P.mech["plate"]["pwr_bottom_pockets"], P.boards["boards"]["PWR"]["bottom_side"]
        depth = P.boards["boards"]["PWR"]["tht_pockets"]["depth"]
        self.assertAlmostEqual(r["value_mm"]["h_max_mm"], P.mech["pwr_bond"]["shim"] + depth - sp["film_t"] - bs["clearance"], places=6)
        self.assertLessEqual(r["value_mm"]["budget_raw_mm2"], r["value_mm"]["pocket_area_mm2"])
        self.assertTrue(r["result"].startswith("OPEN"), r["result"])                  # per-part heights are not read
        boxes = [bx for _, n, bx, _ in layout.item_boxes(P) if n.startswith("PWR.b")]
        self.assertEqual(len(boxes), len(rules.pwr_bottom_regions(P)))
        floor = P.mech["stack_z"]["plate_front"] - depth
        for bx in boxes:                                                              # the bottom envelope sits in its pocket, above the film
            self.assertGreaterEqual(bx[2], floor + sp["film_t"] - 1e-9)
        coll, _ = layout.fit_checks(P)
        self.assertEqual([c for c in coll if c["gap_mm"] < 0], [])

    def test_h_trim_matches_the_partition_spec(self):
        r = self._rule(P, "R-H-TRIM")
        self.assertTrue(r["result"].startswith("OPEN"), r["result"])
        self.assertAlmostEqual(r["value_mm"]["clearance_mm"], self._spec()["keepouts"]["h_trim"]["clearance_mm"], places=6)
        Q = self._copy()
        Q.boards["boards"]["PWR"]["h_trim"]["zone_h_max"] = 3.5
        self.assertTrue(self._rule(Q, "R-H-TRIM")["result"].startswith("FAIL"))

    def test_mated_height_rule_covers_every_pwr_a_header(self):
        with (HERE.parent / "build" / "16-dzhgut-rozyemy.csv").open(encoding="utf-8", newline="") as fh:
            want = {row["connector"] for row in csv.DictReader(fh) if row["board"] == "PWR_A"}
        r = self._rule(P, "R-HDR-MATED")
        rows = {x["connector"]: x for x in r["headers"]}
        self.assertEqual(set(rows), want)
        self.assertAlmostEqual(r["limit_mm"], P.mech["stack_z"]["module_back"] - self._spec()["envelope"]["air_channel"], places=6)
        j104 = rows["J104"]
        self.assertTrue(j104["under_display"])
        self.assertTrue(j104["verdict"].startswith("FAIL as specified"), j104["verdict"])   # vertical 43650: 42.5 + 17.27 = 59.77
        self.assertTrue(j104["alternative"]["fits"])                                       # right-angle 43650: 49.48
        self.assertFalse(rows["J105"]["under_display"])                                    # bottom edge strip below the display
        self.assertFalse(r["result"].startswith("FAIL"))
        Q = self._copy()
        Q.mech["stack_z"]["module_back"] += 5.0                                            # a deeper display stack lets J104 pass
        rows = {x["connector"]: x for x in self._rule(Q, "R-HDR-MATED")["headers"]}
        self.assertTrue(rows["J104"]["verdict"].startswith("PASS"), rows["J104"]["verdict"])

    def test_area_rows_use_the_planned_budget_while_changes_are_pending(self):
        d = json.loads((HERE.parent / "pcb" / "partition-budget.json").read_text(encoding="utf-8"))
        cand = d["candidates"][d["chosen"]]
        pending = [c for c in (cand.get("planned") or {}).get("changes", []) if c.get("status") == "pending"]
        row = boards.area_check(P)["boards"]["PWR_B"]
        if not pending:
            self.assertNotIn("planned_budget", row)
            return
        self.assertEqual(row["planned_budget"]["pending"], len(pending))
        self.assertEqual(row["result"].startswith("PASS"), cand["boards"]["PWR_B"]["demand_1.8_mm2"] <= cand["boards"]["PWR_B"]["usable_mm2"])


class ContractW2Mech7Part2(unittest.TestCase):
    """W2 MECH-7 (SHRINK-2), part 2: real converter footprints in zones 3/4, the PWR-B exit spans after GR-5B (no PHD merge,
    no S02 FFC), the routes of S02/S04/S11/S12/S20-S23/S32/S34-S36 and the exit room in front of the PWR-B edges."""

    SHRINK2 = ("S02", "S04", "S11", "S12", "S20", "S21", "S22", "S23", "S32", "S34", "S35", "S36")

    @classmethod
    def setUpClass(cls):
        from srrx_mech import routes
        cls.res = routes.evaluate(P)

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def _rule(self, Q, rid):
        return [x for x in rules.evaluate(Q) if x["id"] == rid][0]

    def _rows16(self):
        with (HERE.parent / "build" / "16-dzhgut-rozyemy.csv").open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    def test_planned_live_follows_the_graph(self):
        live = boards.planned_live()
        graph = boards.graph_board_parts()
        spec = json.loads((HERE.parent / "pcb" / "partition-spec.json").read_text(encoding="utf-8"))
        ch = json.loads((HERE.parent / "pcb" / "partition-budget.json").read_text(encoding="utf-8"))["chosen"]
        for c in spec["candidates"][ch]["planned"]["changes"]:
            st = live[c["id"]][0]
            self.assertIn(st, ("pending", "in graph"), c["id"])                       # never half-applied in the tree
            if "while_footprint" in c:
                held = all(r in graph and graph[r]["footprint"] == c["while_footprint"][r] for r in c["refs"])
                self.assertEqual(st == "pending", held, c["id"])
        for bid, cid in boards.retired_blocks().items():
            self.assertEqual(live[cid][0], "in graph", bid)

    def test_converter_zones_hold_the_graph_parts(self):
        a = P.boards["boards"]["PWR"]
        graph = boards.graph_board_parts()
        r = self._rule(P, "R-PWR-ZONES")
        self.assertTrue(r["result"].startswith("PASS (model)"), r["result"])
        for zn, refs in a["converter_zone_refs"].items():
            self.assertIn(zn, a["converter_zones"])
            row = r["value_mm"][f"zone {zn}"]
            if all(x in graph for x in refs) and a["converter_zones"][zn] in boards.retired_blocks():
                self.assertEqual(row["basis"], "graph courtyards (GR-5A)", zn)
                self.assertEqual(set(row["refs"]), set(refs))
                self.assertGreater(row["margin_mm"], 0.0)
        Q = self._copy()
        Q.boards["boards"]["PWR"]["thermal_bond"][2] = [7, 39, 12, 12]                # zone 3 smaller than L102 (13.0 x 10.5) + U107
        self.assertTrue(self._rule(Q, "R-PWR-ZONES")["result"].startswith("FAIL"))
        self.assertTrue(self._rule(P, "R-PWR-PADS")["result"].startswith("PASS (model)"))
        self.assertTrue(self._rule(P, "R-UFS-REG")["result"].startswith("PASS (model)"))
        mods = self._rule(P, "R-PWR-MODULES")
        self.assertTrue(mods["result"].startswith("PASS (model)"), mods["result"])

    def test_pwr_b_spans_hold_their_headers(self):
        a, b = P.boards["boards"]["PWR"], P.boards["boards"]["PWR_B"]
        cy = boards.footprint_courtyards()
        graph = boards.graph_board_parts()
        pwr_b = [x["connector"] for x in self._rows16() if x["board"] == "PWR_B"]
        listed = [h for ez in b["edge_zones"] for h in ez.get("headers", [])]
        self.assertEqual(sorted(listed), sorted(pwr_b))                                  # every PWR-B header has one exit zone
        j206 = [ez for ez in a["edge_zones"] if "J206" in ez.get("headers", [])][0]
        row = a["edge_zones"][0]
        for ez in b["edge_zones"]:
            need = sum(cy[graph[h]["footprint"]]["w"] for h in ez["headers"] if h in graph)
            if ez["edge"] == "right":
                continue                                                                 # S02: no home without the FFC (OPEN)
            self.assertLessEqual(need, ez["span"][1] - ez["span"][0] + 1e-9, ez["headers"])
            if ez["edge"] == "top":
                self.assertLessEqual(ez["span"][1], j206["span"][0] - 0.5)               # window over the PWR-A J206 strip
                self.assertFalse(ez["span"][1] > j206["span"][0] and ez["span"][0] < j206["span"][1])
            if ez["edge"] == "bottom":
                self.assertGreaterEqual(ez["span"][0], row["row_end_max"])               # past the compacted PWR-A bottom row

    def test_shrink2_routes_clear_and_use_their_slots(self):
        segs = self.res["segments"]
        for sid in self.SHRINK2:
            r = segs[sid]
            self.assertTrue(r.get("points_mm"), sid)
            self.assertEqual(r.get("crossings"), [], (sid, r.get("crossings")))
        hr = P.mech["harness_routes"]["segments"]
        for sid in ("S04", "S20", "S21", "S22", "S35", "S36"):
            self.assertIn("SL2", segs[sid]["through"], sid)
            self.assertEqual((hr[sid]["via"][0]["edge"], hr[sid]["via"][0]["zone"]), ("PWR_B", 1), sid)
        for sid in ("S11", "S23", "S32", "S34"):
            self.assertIn("SL3", segs[sid]["through"], sid)
        for sid in ("S23", "S34"):
            self.assertEqual((hr[sid]["via"][0]["edge"], hr[sid]["via"][0]["zone"]), ("PWR_B", 2), sid)
        self.assertEqual((hr["S12"]["via"][0]["edge"], hr["S12"]["via"][0]["zone"]), ("PWR", 1))   # J115 on the right edge (no FFC)
        fill = self._rule(P, "R-PLATE-SLOT-FILL")
        self.assertTrue(fill["result"].startswith("PASS (model)"), fill["result"])

    def test_exit_room_is_reported_per_zone(self):
        r = self._rule(P, "R-PWRB-EXIT")
        self.assertTrue(r["result"].startswith("OPEN"), r["result"])
        zones = {z["zone"]: z for z in r["value_mm"]["zones"]}
        self.assertEqual(set(zones), set(range(len(P.boards["boards"]["PWR_B"]["edge_zones"]))))
        for z in zones.values():
            self.assertIsNotNone(z["room_mm"], z)
            self.assertGreaterEqual(z["room_mm"], 0.0)
        Q = self._copy()
        Q.boards["boards"]["PWR_B"]["exit_rule"]["plug_proud_mm"]["PH"] = 0.1
        zq = {z["zone"]: z for z in self._rule(Q, "R-PWRB-EXIT")["value_mm"]["zones"]}
        for i, z in zq.items():                    # review F2: the set-back also counts the bundle OD, so a lower housing only moves it by 1.9
            if "set_back_min_mm" in z:
                self.assertAlmostEqual(z["set_back_min_mm"], max(zones[i]["set_back_min_mm"] - 1.9, 0.0), places=6)


class ContractW2Mech7Review(unittest.TestCase):
    """W2 MECH-7 review fixes: F1 (the area cost of the passing right-angle Micro-Fit against the SHRINK-2 fill margin, and
    the runs of the exit edges outside the display) and F2 (S23/S34 leave the 0.55 mm slot in front of the PWR-B bottom
    edge; R-PWRB-EXIT counts the bundle OD and checks each exit leg with its bundle)."""

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def _rule(self, Q, rid):
        return [x for x in rules.evaluate(Q) if x["id"] == rid][0]

    def test_mated_alternative_is_costed_against_the_fill_margin(self):
        r = self._rule(P, "R-HDR-MATED")
        v = r["value_mm"]
        rows = {x["connector"]: x for x in r["headers"]}
        cy = boards.footprint_courtyards()
        hh = P.parts["harness_headers"]["MF_ra"]
        with (HERE.parent / "pcb" / "generated" / "components.csv").open(encoding="utf-8", newline="") as fh:
            fps = {row["ref"]: row["footprint"] for row in csv.DictReader(fh)}
        for ref in v["alternative_passes"]:
            c = cy[fps[ref]]
            pins = round((max(c["w"], c["h"]) - hh["b"]) / hh["a"]) + 1
            want = (hh["a"] * (pins - 1) + hh["b"]) * hh["d"] - c["w"] * c["h"]
            self.assertAlmostEqual(rows[ref]["alternative"]["area_delta_mm2"], round(want, 1), places=6, msg=ref)
        d = json.loads((HERE.parent / "pcb" / "partition-budget.json").read_text(encoding="utf-8"))
        pa = d["candidates"][d["chosen"]]["boards"]["PWR_A"]
        self.assertAlmostEqual(v["pwr_a_margin_mm2"], round(rules.FILL_TRIGGER * pa["usable_mm2"] - pa["demand_1_mm2"], 1), places=6)
        self.assertEqual(v["all_within_margin"], v["alternative_area_total_mm2"] <= v["pwr_a_margin_mm2"])
        if not v["all_within_margin"]:
            self.assertIn("F2-C", r["result"])
        for s in v["largest_sets_within_margin"]:
            self.assertLessEqual(sum(v["alternative_area_delta_mm2"][x] for x in s), v["pwr_a_margin_mm2"] + 1e-9)
        self.assertNotIn("alternative", rows["J206"])                                        # MF2: no passing part read
        self.assertIn("J206", r["result"].split("no passing part read for", 1)[1])
        right = rows["J104"]["off_display_run_mm"]                                         # the right edge below the display
        disp = [bx for i, _, bx, _ in layout.item_boxes(P) if i == "display"][0]
        self.assertAlmostEqual(right["run_mm"], disp[1] - (P.boards["boards"]["PWR"]["place"]["origin"][1]), places=2)
        self.assertEqual(rows["J206"]["off_display_run_mm"]["run_mm"], 0.0)                 # the SL2 span lies under the display

    def test_s23_s34_leave_the_slot_in_front_of_the_bottom_edge(self):
        from srrx_mech import routes
        res = routes.evaluate(P)
        named = routes.boxes(P)
        tray = named["battery_tray"][1]
        for sid in ("S23", "S34"):
            r = res["segments"][sid]
            self.assertEqual(r["crossings"], [], sid)
            self.assertIn("SL3", r["through"], sid)
            rad = r["bundle_od_mm"] / 2
            pts = r["points_mm"]
            for a, b in zip(pts, pts[1:]):
                piece = tuple(min(a[i], b[i]) for i in range(3)) + tuple(max(a[i], b[i]) for i in range(3))
                self.assertGreaterEqual(layout.gap(piece, tray), rad - 1e-6, (sid, a, b))    # the bundle, not only its centreline
        legs = rules._pwr_b_exit_legs(P)
        for sid in ("S23", "S34"):
            self.assertGreaterEqual(legs[sid]["clear_mm"], 0.0, (sid, legs[sid]))

    def test_exit_rule_counts_the_bundle_od(self):
        r = self._rule(P, "R-PWRB-EXIT")
        ex = P.boards["boards"]["PWR_B"]["exit_rule"]
        legs = rules._pwr_b_exit_legs(P)
        for z in r["value_mm"]["zones"]:
            if z["room_mm"] is None or z["plug_proud_mm"] is None:
                continue
            od = max(v["bundle_od_mm"] for v in legs.values() if v["zone"] == z["zone"])
            self.assertEqual(z["bundle_od_max_mm"], od)
            need = z["plug_proud_mm"] + od + ex["bundle_clearance_mm"]
            self.assertAlmostEqual(z["set_back_min_mm"], round(max(need - z["room_mm"], 0.0), 2), places=6)
            if od > z["room_mm"]:
                self.assertIn("cannot turn in front of the edge", z["verdict"])
        self.assertNotIn("the wires turn within the room", r["result"])
        Q = self._copy()
        hr = Q.mech["harness_routes"]["segments"]
        for sid in ("S23", "S34"):                                                         # the part-2 route: along y 38.2 in the slot
            hr[sid]["via"][0:5] = [{"edge": "PWR_B", "zone": 2, "s": 10.75},
                                   {"box": "PWR.r0", "at": [0.5, 0.0, 0.5], "off": [0, -0.3, 0], "keep": "xz"}]
        zq = [z for z in self._rule(Q, "R-PWRB-EXIT")["value_mm"]["zones"] if z["zone"] == 2][0]
        self.assertTrue(any(v["clear_mm"] < 0 for v in zq["legs"].values()), zq["legs"])


class ContractW2Mech8(unittest.TestCase):
    """W2 MECH-8: PWR-A and PWR-B on 6 layers JLC06161H-2116 with 2 oz outer copper (1.664 mm MODEL) in the mechanical
    contract, the mated stack re-checked (R-PWR-STACK); every other board keeps the shared 4-layer 1.6 mm stackup."""

    def _copy(self):
        import copy
        return copy.deepcopy(P)

    def _rule(self, Q):
        return [x for x in rules.evaluate(Q) if x["id"] == "R-PWR-STACK"][0]

    def _spec(self):
        return json.loads((HERE.parent / "pcb" / "partition-spec.json").read_text(encoding="utf-8"))

    def test_power_boards_have_the_6_layer_stackup(self):
        for bid in ("PWR", "PWR_B"):
            st = P.boards["boards"][bid]["stackup"]
            self.assertEqual(st["layers"], 6, bid)
            self.assertAlmostEqual(st["t"], 1.664, places=6)
            self.assertEqual(st["status"], "MODEL")
            self.assertIn("JLC06161H-2116", st["fab"])
            self.assertIn("https://jlcpcb.com/impedance", st["source"])
            self.assertIn("2026-11-13", st["source"])
            self.assertAlmostEqual(st["order_t"] * (1 + st["order_tol"]), 1.76, places=6)
            self.assertEqual(P.board_t(bid), st["t"])

    def test_thickness_is_the_layer_table_with_2_oz_outer_copper(self):
        # the same JLC06161H-2116 table as pcb/generated/stackup-6l.json (pcb/stackup.py), outer foil of copper_option outer_2oz
        path = HERE.parent / "pcb" / "generated" / "stackup-6l.json"
        if not path.exists():
            self.skipTest("pcb/generated/stackup-6l.json not present")
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(doc["stackup"]["id"], "JLC06161H-2116")
        opt = doc["copper_options"]["outer_2oz"]
        total = 0.0
        for layer in doc["stackup"]["layers"]:
            if layer.get("kicad") in ("F.Cu", "B.Cu"):
                total += opt["outer_copper_mm"]
            elif "kicad" in layer:
                total += layer["copper_mm"]
            else:
                total += layer["thickness_mm"]
        self.assertAlmostEqual(total, 1.6644, places=6)
        for bid in ("PWR", "PWR_B"):
            self.assertAlmostEqual(P.board_t(bid), round(total, 3), places=6)

    def test_other_boards_keep_the_shared_stackup(self):
        self.assertEqual(P.boards["stackup"]["t"], 1.6)
        self.assertEqual(P.boards["stackup"]["layers"], 4)
        for bid in ("RF", "CTRL", "ENC"):
            self.assertNotIn("stackup", P.boards["boards"][bid], bid)
            self.assertEqual(P.board_t(bid), 1.6, bid)
        c = boards.contract(P)
        self.assertEqual(c["stackup"], P.boards["stackup"])                      # the top-level contract stackup is unchanged
        for bid in ("RF", "CTRL", "ENC"):
            self.assertNotIn("stackup", c["boards"][bid], bid)
        for bid in ("PWR", "PWR_B"):
            st = c["boards"][bid]["stackup"]
            self.assertEqual((st["layers"], st["t"]), (6, 1.664), bid)
            self.assertIn("source", st)
            self.assertFalse([k for k in st if k.startswith("_")], bid)

    def test_pwr_b_follows_the_thicker_pwr_a(self):
        a, b = P.boards["boards"]["PWR"], P.boards["boards"]["PWR_B"]
        stack = b["b2b"]["stack"]
        self.assertEqual(stack, self._spec()["parameters"]["stack"])
        self.assertAlmostEqual(b["place"]["z_bottom"], a["place"]["z_bottom"] + P.board_t("PWR") + stack, places=6)
        self.assertAlmostEqual(b["place"]["z_bottom"], 47.564, places=6)
        tops = [bx[5] for name, bx in layout.board_boxes(P, "PWR_B")]
        self.assertAlmostEqual(max(tops), 47.564 + 1.664 + b["max_height"], places=6)
        tops_a = [bx[5] for name, bx in layout.board_boxes(P, "PWR") if not name.startswith("PWR.b")]
        self.assertAlmostEqual(min(tops_a), a["place"]["z_bottom"] + 1.664 + a["max_height"], places=6)

    def test_stack_rule_reports_the_margin(self):
        r = self._rule(P)
        self.assertTrue(r["result"].startswith("PASS (model)"), r["result"])
        self.assertIn("proof-fit gate (OPEN)", r["result"])
        v = r["value_mm"]
        sz = P.mech["stack_z"]
        floor = sz["module_back"] - self._spec()["envelope"]["air_channel"]
        top = v["pwr_b"]["parts_top_z"]
        self.assertAlmostEqual(top, 40.9 + 1.664 + 5.0 + 1.664 + 5.5, places=6)
        self.assertAlmostEqual(v["margin_mm"], round(floor - top, 3), places=6)
        self.assertGreaterEqual(v["margin_mm"], 0.0)
        self.assertAlmostEqual(v["margin_with_shared_t_mm"] - v["margin_mm"], 2 * (1.664 - 1.6), places=6)
        ob = v["order_band_mm"]
        self.assertEqual(ob["PWR"], [1.44, 1.76])
        self.assertAlmostEqual(ob["margin_min_mm"], round(floor - (40.9 + 1.76 + 5.0 + 1.76 + 5.5), 3), places=6)
        self.assertGreaterEqual(ob["margin_min_mm"], 0.0)
        self.assertTrue(v["dz_mezz_mm"]["dz_unchanged"], v["dz_mezz_mm"])     # D-ENV: the CTRL bottom still sets dz
        self.assertAlmostEqual(v["channel_to_module_back_mm"], round(sz["module_back"] - top, 3), places=6)
        rows = [g for g in layout.channel_check(P) if g["item"].startswith("PWR_B")]
        for g in rows:                                                        # the channel rows use the same envelope
            self.assertAlmostEqual(g["top_z"], round(top, 2), places=6)

    def test_stack_rule_fails_when_pwr_b_does_not_follow(self):
        Q = self._copy()
        Q.boards["boards"]["PWR_B"]["place"]["z_bottom"] = 47.5                # the 1.6 mm position with the 1.664 mm PWR-A
        self.assertTrue(self._rule(Q)["result"].startswith("FAIL"))
        Q = self._copy()
        Q.mech["stack_z"]["module_back"] -= 2.0                               # display stack 2 mm lower: margin negative
        self.assertTrue(self._rule(Q)["result"].startswith("FAIL"))
        Q = self._copy()
        for bid in ("PWR", "PWR_B"):
            Q.boards["boards"][bid]["stackup"]["order_tol"] = 0.8              # a band so wide that its upper end does not fit
        self.assertTrue(self._rule(Q)["result"].startswith("FAIL"))

    def test_h_trim_clearance_does_not_depend_on_the_board_thickness(self):
        r = [x for x in rules.evaluate(P) if x["id"] == "R-H-TRIM"][0]
        self.assertAlmostEqual(r["value_mm"]["pwr_a_face_z"], 40.9 + 1.664, places=6)
        self.assertAlmostEqual(r["value_mm"]["clearance_mm"], self._spec()["keepouts"]["h_trim"]["clearance_mm"], places=6)

    def test_fastener_stacks_use_the_board_thickness(self):
        from srrx_mech import fasteners
        J = {j["id"]: j for j in fasteners.stacks(P)["joints"]}
        self.assertEqual(J["PWR_A-PLATE"]["stack_mm"][0], ["PWR-A", round(1.664, 2)])
        self.assertEqual(J["PWR_B-STANDOFF"]["stack_mm"], [["PWR-B", round(1.664, 2)]])
        self.assertIn("z 42.564", J["PWR_A-PLATE"]["seat"])
        self.assertIn("z 49.228", J["PWR_B-STANDOFF"]["seat"])
        self.assertTrue(J["PWR_B-STANDOFF"]["result"].startswith("PASS (model)"), J["PWR_B-STANDOFF"]["result"])
        self.assertEqual(J["RF-STANDOFF"]["stack_mm"], [["RF board", 1.6]])  # the 4-layer boards are unchanged

    def test_board_sheet_names_the_stackup(self):
        def text(bid):
            return json.dumps(boards.board_sheet(P, bid).__dict__, ensure_ascii=False, default=str)
        self.assertIn("6 шарів, 1.664 мм", text("PWR_B"))
        self.assertIn("TBD при замовленні", text("PWR"))
        self.assertIn("FR-4, 4 шари, 1.6 мм (build/15)", text("RF"))
