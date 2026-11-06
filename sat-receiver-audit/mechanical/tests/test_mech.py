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
        mine = {d for bid in ("PWR", "RF", "CTRL") for d in P.boards["boards"][bid]["domains"]}
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
        self.assertEqual([f["id"] for f in face_features(P)["top"] if f["kind"] == "pv0"], ["PWR_KEY"])


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
        self.assertTrue({"cooler_a.block", "cooler_a.fins", "cooler_a.fan", "q6a.hdr2x2", "q6a.uart5_plug"} <= names)
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
