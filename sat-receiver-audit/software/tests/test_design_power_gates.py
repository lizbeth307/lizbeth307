"""Design-graph regressions for the E1-E5 power and foreign-DC gates.

These are schematic/gate-text contracts only. They never close a hardware gate.
"""
from collections import defaultdict
import json
from pathlib import Path
import re
import unittest

PROJECT = Path(__file__).resolve().parents[2]
# Standard thick-film chip ratings; a part above them needs a larger package.
RATING_W = {"0402": .0625, "0603": .1, "0805": .125, "1206": .25, "1210": .5, "2010": .75, "2512": 1.0}
SENSED_PORTS = ("E4_P2", "E4_P3", "E4_HF_CM")


def load():
    graphs = {f"E{i}": json.loads((PROJECT / f"design/E{i}.json").read_text(encoding="utf-8")) for i in range(1, 6)}
    comps = {c["ref"]: c for g in graphs.values() for c in g["components"]}
    gates = {o["id"]: o for g in graphs.values() for o in g["open_items"]}
    return graphs, comps, gates


def lcsc_power_w():
    """Rated power of each LCSC SKU in the parts-database snapshots (design/parts, tools/build_parts.py)."""
    out = {}
    for snap in sorted((PROJECT / "design/parts/snapshots").glob("*-lcsc.json")):
        for code, rec in json.loads(snap.read_text(encoding="utf-8"))["entries"].items():
            m = re.fullmatch(r"(\d+(?:\.\d+)?)(m?)W", rec.get("attributes", {}).get("Power(Watts)", ""))
            if m:
                out[code] = float(m.group(1)) * (1e-3 if m.group(2) else 1)
    return out


def nets(c):
    return [p.get("net") for p in c["pins"]]


def ohms(value):
    # Leading "10k1%"/"0.200R"/"249 Ω", else an MPN-prefixed "... 0.330 Ω"; NTCs and
    # unparsed MPN-only values are treated as high impedance.
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*(m|k|M)?", value) or re.search(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(m|k|M)?\s*(?:Ω|R\b|Ohm)", value)
    if not m or value.startswith("NTC"):
        return float("inf")
    return float(m.group(1)) * {None: 1, "m": 1e-3, "k": 1e3, "M": 1e6}[m.group(2)]


def dc_reach(comps, start, limit=100.0):
    # Low-impedance DC paths only: chokes, fuses, shunts and series sense resistors,
    # plus a bias-tee ANT->DC port. Taps, bleeds, capacitors and ICs stop the walk.
    adj = defaultdict(set)
    def link(a, b):
        if a and b:
            adj[a].add(b); adj[b].add(a)
    for c in comps.values():
        n = nets(c)
        if len(n) == 2 and (c["kind"] in ("inductor", "fuse", "net_tie") or c["kind"] == "resistor" and ohms(c["value"]) < limit):
            link(*n)
        named = {p["name"]: p.get("net") for p in c["pins"]}
        if "DC" in named and "ANT" in named:
            link(named["ANT"], named["DC"])
    seen, todo = {start}, [start]
    while todo:
        for nxt in adj[todo.pop()] - seen:
            seen.add(nxt); todo.append(nxt)
    return seen


class DesignPowerGateTest(unittest.TestCase):
    def setUp(self):
        self.graphs, self.comps, self.gates = load()

    def test_ina228_alert_has_one_fitted_pullup(self):
        fitted = sorted(r for r, c in self.comps.items() if c["kind"] == "resistor" and not c.get("dnp") and "INA228_ALERT" in nets(c))
        self.assertEqual(fitted, ["R301"])
        self.assertEqual(set(nets(self.comps["R301"])), {"INA228_ALERT", "3V3_Q6A"})
        # The duplicate E1 R102 pull-up was removed in v2.1; a reserved place may only return as DNP.
        self.assertTrue("R102" not in self.comps or self.comps["R102"].get("dnp"))

    def test_resistor_rating_fits_vendored_package(self):
        manifest = json.loads((PROJECT / "build/kicad/footprints/manifest.json").read_text(encoding="utf-8"))
        vendored = {f["footprint"] for f in manifest["footprints"]}
        rated = lcsc_power_w()
        for ref, c in self.comps.items():
            size = re.search(r"R_(\d{4})_", c.get("footprint", ""))
            watt = re.search(r"(\d+(?:\.\d+)?)\s*W\b", c["value"])
            if c["kind"] == "resistor" and size and watt:
                # A higher-rated part in the same package (e.g. an anti-surge 0603 at 0.25 W) counts
                # only through the LCSC SKU that the parts database writes into the graph.
                rating = max(RATING_W[size.group(1)], rated.get(c.get("lcsc"), 0.0))
                self.assertGreaterEqual(rating, float(watt.group(1)), (ref, c["value"], c["footprint"], c.get("lcsc")))
        self.assertEqual(self.comps["R512"]["footprint"], "Resistor_SMD:R_1210_3225Metric")
        self.assertIn(self.comps["R512"]["footprint"], vendored)

    def test_software_cutoff_window_stays_above_hardware_uv_trip(self):
        hw = re.search(r"trip (\d+(?:\.\d+)?)±(\d+(?:\.\d+)?) V", self.gates["E1-04"]["resolve"])
        sw = re.search(r"physical\s*(\d+(?:\.\d+)?)\s*V software cutoff.*?within\s*\+/-(\d+(?:\.\d+)?)\s*V", self.gates["E3-07"]["resolve"])
        hw_max = round(float(hw.group(1)) + float(hw.group(2)), 3)
        sw_min = round(float(sw.group(1)) - float(sw.group(2)), 3)
        self.assertEqual(float(sw.group(1)), 13.05)
        self.assertGreater(sw_min, hw_max)
        # Windows alone leave 50 mV; each unit must also prove the measured order.
        for gid in ("E1-04", "E3-07"):
            self.assertRegex(self.gates[gid]["resolve"], r"(?:>=|≥)\s*0\.10\s*V", gid)

    def test_dc_walk_follows_real_paths(self):
        self.assertIn("E2_LNA_IN", dc_reach(self.comps, "LAB5"))
        self.assertIn("E2_LNA2_SW", dc_reach(self.comps, "E2_LNA2_SHUNT"))
        self.assertNotIn("GND", dc_reach(self.comps, "E4_P2"))
        # Each sensed port reaches its E2 port node through the injector/bias-tee, and each
        # protected node reaches its switch OUT (TPS2553 U207/U208, TPS2596 U214); the
        # E4-06 blocking element (a FET) stops the walk between the two.
        for port, port_node, protected, out in (("E4_P2", "BIAS_CH2_PORT", "BIAS_CH2", "E2_LNA2_SW"),
                                                ("E4_P3", "BIAS_CH3_PORT", "BIAS_CH3", "E2_LNA3_SW"),
                                                ("E4_HF_CM", "BONI13V8_PORT", "BONI13V8", "E2_BONI_EF")):
            self.assertIn(port_node, dc_reach(self.comps, port), port)
            self.assertIn(out, dc_reach(self.comps, protected), protected)

    def test_foreign_dc_gate_matches_exposed_bias_switches(self):
        outs = {p["net"] for c in self.comps.values() if c["value"].startswith(("TPS2553", "TPS2596"))
                for p in c["pins"] if p["name"] == "OUT"}
        exposed = [port for port in SENSED_PORTS if dc_reach(self.comps, port) & outs]
        e4 = self.graphs["E4"]
        resolve = self.gates["E4-06"]["resolve"]
        # v2.1: a back-to-back P-MOSFET pair, held open by the branch EN, separates every
        # sensed port from its bias-switch OUT. A walk regression must fail here, not skip
        # the gate text; removing an element must change this list and the E4-06 text together.
        self.assertEqual(exposed, [])
        for port, protected, en in (("BIAS_CH2_PORT", "BIAS_CH2", "EN_LNA2"), ("BIAS_CH3_PORT", "BIAS_CH3", "EN_LNA3"),
                                    ("BONI13V8_PORT", "BONI13V8", "EN_BONI")):
            pair = [c for c in self.comps.values() if c["kind"] == "pfet" and {port, protected} <= set(nets(c))]
            self.assertEqual(len(pair), 1, port)
            pins = {p["name"]: p["net"] for p in pair[0]["pins"]}
            source, gate = pins["S1"], pins["G1"]
            self.assertEqual((pins["S2"], pins["G2"], pins["D1"], pins["D2"]), (source, gate, protected, port))
            # Gate held to source (R_GS plus the 100 nF fast-edge capacitor), sunk only by the branch EN.
            between = [c for c in self.comps.values() if set(nets(c)) - {None} == {source, gate}]
            self.assertEqual(sorted(c["kind"] for c in between), ["capacitor", "diode", "resistor"], port)
            self.assertTrue(any(c["kind"] == "capacitor" and c["value"].startswith("100nF 50V") for c in between), port)
            sink = [c for c in self.comps.values() if c["kind"] == "nfet" and en in nets(c)
                    and any(gate in nets(r) and set(nets(r)) & set(nets(c)) for r in self.comps.values() if r["kind"] == "resistor")]
            self.assertEqual(len(sink), 1, port)
        # The gate demands the assembled-port test, including the fast-edge hot plug,
        # and no longer offers an eFuse whose OUT pin cannot take −30 V.
        self.assertIn("at each assembled port", resolve)
        self.assertIn("fast-edge hot plug", resolve)
        self.assertNotIn("TPS2660", resolve)
        self.assertNotIn("Hardware redesign required", resolve)
        self.assertFalse(any(n.startswith("Foreign DC design envelope is ±30 V") for n in e4["notes"]))
        self.assertTrue(any("design target until the E4-06" in n for n in e4["notes"]))


if __name__ == "__main__":
    unittest.main()
