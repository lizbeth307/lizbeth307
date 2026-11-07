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
        # daughterboard STACK 5.8 asks for.
        self.assertEqual(set(P.boards["boards"]), {"PWR", "RF", "CTRL", "ENC"})
        self.assertEqual(P.boards["stackup"]["layers"], 4)

    def test_board_domains_are_the_pcb_partition_domains(self):
        comp = HERE.parent / "pcb" / "generated" / "components.csv"
        if not comp.exists():
            self.skipTest("pcb/generated/components.csv not present")
        with comp.open(encoding="utf-8", newline="") as fh:
            domains = {r["board_candidate"] for r in csv.DictReader(fh) if r["board_candidate"]}
        mine = {d for b in P.boards["boards"].values() for d in b["domains"]}
        mine |= {d for k, b in P.boards["small_boards"].items() if not k.startswith("_") for d in b["domains"]}
        self.assertEqual(mine, domains)

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
        self.assertTrue(r["result"].startswith("OPEN"), r)   # never PASS before the wire OD and the edge trim are chosen
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
        p = cy["SR_RX_Custom:Pololu_D36V50Fx"]
        self.assertAlmostEqual(p["w"], 25.9, places=3)
        self.assertAlmostEqual(p["h"], 25.9, places=3)

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
        for m in P.boards["boards"]["PWR"]["modules_on_board"]:      # every modules_on_board part is a pcb_module ref, counted once
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

    def test_bottom_ports_are_modelled_or_name_a_reason(self):
        for p in P.mech["bottom_face"]["ports"]:
            with self.subTest(port=p["id"]):
                if p["kind"] == "tbd":
                    self.assertIn("2026-11-07", p.get("_tbd_reason", ""))
                    self.assertIn("http", p["_tbd_reason"])
                else:
                    self.assertIn(p["part"], P.parts)
                    self.assertTrue(P.parts[p["part"]]["status"].startswith("datasheet"))

    def test_taoglas_ports_pass_the_thread_rule(self):
        r = self._rule(P, "R-SMA-THREAD")
        for pid in ("P1", "P2", "P3", "P6"):
            self.assertTrue(r["value_mm"][pid].startswith("PASS (model)"), r["value_mm"][pid])
        # 11.4 - 0.3 - 4.5 - (1.75 + 0.2) - (1.1 + 0.3) = 3.25 >= 3 x 0.706
        self.assertIn("3.25 mm left", r["value_mm"]["P1"])
        self.assertTrue(r["value_mm"]["P5"].startswith("OPEN"))
        self.assertFalse(r["result"].startswith("FAIL"), r["result"])

    def test_a_thin_thread_fails_the_thread_rule(self):
        import copy
        Q = copy.deepcopy(P)
        Q.parts["taoglas_mhf1_sma_wp"]["thread_len"] = 8.0
        r = self._rule(Q, "R-SMA-THREAD")
        self.assertTrue(r["result"].startswith("FAIL"), r["result"])

    def test_vfa340_nut_and_long_side_inside(self):
        v = P.parts["cinch_vfa340"]
        self.assertEqual((v["hex_af"], v["flange_t"], v["short_side"], v["overall"], v["nut_af"], v["nut_t"]), (11.0, 1.5, 7.6, 20.9, 11.0, 2.4))
        self.assertEqual(v["washer"], [12.0, 9.7, 0.4])
        nut = [b for _, n, b, _ in layout.item_boxes(P) if n == "nut.P4"][0]
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
        sm = P.parts["fairview_sm4955"]
        self.assertLessEqual(P.parts["hammond_1554u2gy"]["wall"], sm["panel_max"])
        lo, hi = P.parts["lapp_skintop_st_m12"]["clamp"]
        self.assertTrue(lo <= 4.2 <= hi)


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