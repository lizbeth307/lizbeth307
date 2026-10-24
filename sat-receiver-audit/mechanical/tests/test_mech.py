"""Unit tests of the mechanical generator that need no CAD kernel (run by sr-rx-mech.yml).

    python -m unittest discover -s mechanical/tests
"""
import csv
import json
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from srrx_mech import antennas, boards, drawings_enclosure as de, layout, rules, thermal, writers  # noqa: E402
from srrx_mech.features import face_features  # noqa: E402
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
