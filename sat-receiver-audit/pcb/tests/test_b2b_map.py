"""PWR-A/PWR-B board-to-board pair (W2 B2B): Samtec LSHM-150 mating map, GND rule and contact budget (stdlib only).

The pair is one hermaphroditic part on both boards: J208 on the PWR-A top, J209 on the PWR-B bottom. Samtec print
LSHM-1XX-XX.X-XXX-DV-A-X-X-TR Rev Z note 4: pin 01 mates contact 02 of the other LSHM-DV, so pin n of J208 meets
pin n+1 (n odd) or n-1 (n even) of J209 (pcb/prepare.py b2b_mate). These tests check that map on the vendored KiCad
10.0.7 footprint, the contact map of pcb/generated/b2b-nets.json and the graph refs of design/E2.json.
MODEL/CI checks only: no hardware gate is closed here.

Run: python -m unittest discover -s pcb/tests  (from sat-receiver-audit/)
"""
import importlib.util
import json
import math
import re
import unittest
from pathlib import Path

PCB = Path(__file__).resolve().parents[1]
ROOT = PCB.parent
_spec = importlib.util.spec_from_file_location('srrx_prepare_b2b', PCB / 'prepare.py')
prepare = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prepare)

SPEC = json.loads((PCB / 'partition-spec.json').read_text(encoding='utf-8'))['b2b']
NETS = json.loads((PCB / 'generated/b2b-nets.json').read_text(encoding='utf-8'))
E2 = {c['ref']: c for c in json.loads((ROOT / 'design/E2.json').read_text(encoding='utf-8'))['components']}
A, B = SPEC['graph_refs']['pwr_a'], SPEC['graph_refs']['pwr_b']


def footprint_pads():
    """Numbered SMD pads {number: (x, y)} and the NPTH holes [(x, y)] of the vendored footprint of the spec."""
    lib, name = SPEC['footprint'].split(':', 1)
    text = (ROOT / 'build/kicad/footprints' / f'{lib}.pretty' / f'{name}.kicad_mod').read_text(encoding='utf-8')
    pads = {n: (float(x), float(y)) for n, x, y in re.findall(r'\(pad "(\d+)" smd rect\s*\(at (-?[\d.]+) (-?[\d.]+)\)', text)}
    holes = [(float(x), float(y)) for x, y in re.findall(r'\(pad "" np_thru_hole circle\s*\(at (-?[\d.]+) (-?[\d.]+)\)', text)]
    return pads, holes


class MatingMapTests(unittest.TestCase):
    def test_note_4_pin_01_meets_contact_02(self):
        self.assertEqual(prepare.b2b_mate(1), 2)
        self.assertEqual(prepare.b2b_mate(2), 1)

    def test_map_is_an_involution_on_all_contacts(self):
        n = SPEC['contacts']
        for i in range(1, n + 1):
            m = prepare.b2b_mate(i)
            self.assertTrue(1 <= m <= n, i)
            self.assertNotEqual(m, i)
            self.assertEqual(prepare.b2b_mate(m), i)

    def test_map_holds_on_the_vendored_footprint(self):
        # J209 faces J208: seen from the PWR-A top it is J208 mirrored about the strip axis (y -> -y). Every pad of J208 must then
        # coincide with pad b2b_mate(n) of the mirrored copy, and the alignment holes sit on the pin-1 row side (Samtec Rev G).
        pads, holes = footprint_pads()
        self.assertEqual(sorted(pads, key=int), [str(i) for i in range(1, SPEC['contacts'] + 1)])
        for n, (x, y) in pads.items():
            mx, my = pads[str(prepare.b2b_mate(int(n)))]
            self.assertAlmostEqual(mx, x, places=6, msg=n)
            self.assertAlmostEqual(-my, y, places=6, msg=n)
        self.assertEqual(len(holes), 2)
        row1 = pads['1'][1]
        for hx, hy in holes:
            self.assertLess(abs(hy - row1), abs(hy + row1), 'alignment holes are on the pin-1 row side')

    def test_spec_courtyards_are_the_footprint_courtyard(self):
        lib, name = SPEC['footprint'].split(':', 1)
        text = (ROOT / 'build/kicad/footprints' / f'{lib}.pretty' / f'{name}.kicad_mod').read_text(encoding='utf-8')
        m = re.search(r'\(fp_rect\s*\(start (-?[\d.]+) (-?[\d.]+)\)\s*\(end (-?[\d.]+) (-?[\d.]+)\)(?:(?!\(fp_).)*?"F\.CrtYd"', text, re.S)
        x0, y0, x1, y1 = map(float, m.groups())
        crt = [round(abs(x1 - x0), 2), round(abs(y1 - y0), 2)]
        self.assertEqual(SPEC['courtyard_pwr_a'], crt)
        self.assertEqual(SPEC['courtyard_pwr_b'], crt)


class ContactMapTests(unittest.TestCase):
    def test_every_crossing_net_meets_itself_in_the_generated_map(self):
        rows = NETS['contacts']
        self.assertEqual(len(rows), SPEC['contacts'])
        a_net = {r['pwr_a_pin']: r['net'] for r in rows}
        b_net = {r['pwr_b_pin']: r['net'] for r in rows}
        for r in rows:
            self.assertEqual(int(r['pwr_b_pin']), prepare.b2b_mate(int(r['pwr_a_pin'])))
        for pin, net in a_net.items():
            self.assertEqual(b_net[str(prepare.b2b_mate(int(pin)))], net, pin)
        crossing = {r['net'] for r in NETS['nets']}
        self.assertEqual({net for net in a_net.values() if net} - {'GND'}, crossing)

    def test_graph_refs_carry_the_map_pin_for_pin(self):
        # design/E2.json: each crossing net is the same net on both halves at the mating contacts; spares are nc on both
        a = {str(p['number']): p for p in E2[A]['pins']}
        b = {str(p['number']): p for p in E2[B]['pins']}
        self.assertEqual(len(a), SPEC['contacts'])
        self.assertEqual(len(b), SPEC['contacts'])
        for n, pa in a.items():
            pb = b[str(prepare.b2b_mate(int(n)))]
            self.assertEqual(pa.get('net'), pb.get('net'), n)
            self.assertEqual(bool(pa.get('nc')), bool(pb.get('nc')), n)
        rows = {r['pwr_a_pin']: r['net'] for r in NETS['contacts']}
        self.assertEqual({n: p.get('net', '') for n, p in a.items()}, rows)
        self.assertEqual(E2[A]['footprint'], SPEC['footprint'])
        self.assertEqual(E2[B]['footprint'], SPEC['footprint'])

    def test_gnd_rule_one_gnd_contact_per_power_contact(self):
        k = SPEC['gnd_pins_per_power_contact']
        rows = NETS['contacts']
        power_nets = {r['net'] for r in NETS['nets'] if r['kind'] == 'power'}
        power = [r for r in rows if r['role'] == 'power']
        gnd = [r for r in rows if r['net'] == 'GND']
        self.assertEqual(len(power), NETS['totals']['power_pins'])
        self.assertEqual(len(gnd), len(power) * k)
        self.assertEqual(NETS['totals']['gnd_pins'], len(power) * k)
        by_pin = {int(r['pwr_a_pin']): r for r in rows}
        for r in power:
            # the GND return shares the column (pins 2c-1 and 2c) of its power contact
            other = by_pin[prepare.b2b_mate(int(r['pwr_a_pin']))]
            self.assertEqual(other['net'], 'GND', r)
            self.assertIn(r['net'], power_nets)
        for row in NETS['nets']:
            got = sum(1 for r in rows if r['net'] == row['net'])
            self.assertEqual(got, row['pins'], row['net'])
            if row['kind'] == 'power':
                self.assertEqual(row['pins'], math.ceil(row['prot_A'] / NETS['i_pin_A'] - 1e-9), row['net'])

    def test_declared_sense_pairs_share_one_column(self):
        by_net = {r['net']: int(r['pwr_a_pin']) for r in NETS['contacts'] if r['net']}
        for pair in SPEC['declared_sense_pairs']:
            first, second = (by_net[n] for n in pair['nets'])
            self.assertEqual(prepare.b2b_mate(first), second, pair['nets'])

    def test_totals_fit_the_100_contacts(self):
        t = NETS['totals']
        self.assertEqual(NETS['contacts_available'], 100)
        self.assertEqual(t['contacts_needed'], t['power_pins'] + t['signal_pins'] + t['gnd_pins'])
        self.assertEqual(t['contacts_with_spare'], math.ceil(t['contacts_needed'] * (1 + SPEC['spare_fraction']) - 1e-9))
        self.assertLessEqual(t['contacts_needed'], 100)
        self.assertLessEqual(t['contacts_with_spare'], 100)
        self.assertTrue(t['fits'])
        self.assertTrue(t['meets_spare_rule'])
        used = [r for r in NETS['contacts'] if r['net']]
        self.assertEqual(len(used), t['contacts_needed'])
        self.assertEqual(NETS['errors'], [])
        self.assertEqual(SPEC['budget_chosen']['contacts_needed'], t['contacts_needed'])


if __name__ == '__main__':
    unittest.main()
