"""PWR-A/PWR-B board-to-board pair (W2 B2B): Samtec LSHM-150 mating map, GND rule and contact budget (stdlib only).

The pair is one hermaphroditic part on both boards: J208 on the PWR-A top, J209 on the PWR-B bottom. Samtec print
LSHM-1XX-XX.X-XXX-DV-A-X-X-TR Rev Z note 4: pin 01 mates contact 02 of the other LSHM-DV, so pin n of J208 meets
pin n+1 (n odd) or n-1 (n even) of J209 (pcb/prepare.py b2b_mate). These tests check that map on the vendored KiCad
10.0.7 footprint, the contact map of pcb/generated/b2b-nets.json and the graph refs of design/E2.json, and the GND
guard rule of the map (b2b.guard_rule, W2 B2B review R2: no rail contact beside anything but GND in its row).
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

    def test_gnd_rule_gnd_return_beside_every_rail_contact(self):
        # b2b.guard_rule (W2 B2B review R2): every rail contact (power, sense/supply tap, rail node) has its GND return beside it
        # (since 11.11.2026 the next contact of its row); the other GND contacts are the guards
        self.assertEqual(SPEC['gnd_pins_per_power_contact'], 1)
        rows = NETS['contacts']
        power_nets = {r['net'] for r in NETS['nets'] if r['kind'] == 'power'}
        power = [r for r in rows if r['role'] == 'power']
        rail = [r for r in rows if r['role'] in prepare.B2B_RAIL_KINDS]
        gnd = [r for r in rows if r['net'] == 'GND']
        self.assertEqual(len(power), NETS['totals']['power_pins'])
        self.assertEqual(len(gnd), len(rail) + NETS['totals']['guard_pins'])
        self.assertEqual(NETS['totals']['gnd_pins'], len(gnd))
        self.assertEqual({r['role'] for r in gnd}, {'gnd', 'guard'})
        self.assertEqual(sum(r['role'] == 'guard' for r in gnd), NETS['totals']['guard_pins'])
        by_pin = {int(r['pwr_a_pin']): r for r in rows}
        for r in rail:
            # the GND return is the next contact of the rail contact's row
            other = by_pin[int(r['pwr_a_pin']) + 2]
            self.assertEqual(other['net'], 'GND', r)
            self.assertEqual(other['role'], 'gnd', r)
        for r in power:
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


class GuardRuleTests(unittest.TestCase):
    """b2b.guard_rule (W2 B2B review R2): pads 0.30 mm wide at 0.50 mm pitch leave 0.20 mm between neighbours of a row, so no
    contact at a supply-rail potential (rail contacts and declared sense pairs) may have a neighbour in its row other than GND."""

    HOT = prepare.B2B_RAIL_KINDS + ('sense pair',)

    def test_row_neighbours_of_hot_contacts_are_gnd_on_both_halves(self):
        n_all = SPEC['contacts']
        for half in ('pwr_a', 'pwr_b'):
            by_pin = {int(r[half + '_pin']): r for r in NETS['contacts']}
            hot = [p for p, r in by_pin.items() if r['role'] in self.HOT]
            self.assertTrue(hot)
            for p in hot:
                for q in (p - 2, p + 2):  # the same row (same parity), one column away
                    if 1 <= q <= n_all:
                        self.assertEqual(by_pin[q]['net'], 'GND', f'{half} contact {p} {by_pin[p]["net"]} beside {q} {by_pin[q]["net"]}')

    def test_graph_refs_keep_the_guard_rule(self):
        hot_nets = {r['net'] for r in NETS['contacts'] if r['role'] in self.HOT}
        for ref in (A, B):
            net = {int(p['number']): p.get('net', '') for p in E2[ref]['pins']}
            for p, n in net.items():
                if n in hot_nets:
                    for q in (p - 2, p + 2):
                        if q in net:
                            self.assertIn(net[q], ('GND',), f'{ref}.{p} {n} beside {ref}.{q} {net[q]}')

    def test_rails_follow_rail_order(self):
        # rail_order lists the rail contacts column by column (since 11.11.2026; a net listed once keeps its contacts together)
        order = SPEC['rail_order']
        self.assertEqual(order[0], '3V3_Q6A')
        rails = [r for r in sorted(NETS['contacts'], key=lambda r: int(r['pwr_a_pin'])) if r['role'] in prepare.B2B_RAIL_KINDS]
        even = set(SPEC.get('rail_row_even', []))
        want = sorted(r['net'] for r in NETS['nets'] if r['kind'] in prepare.B2B_RAIL_KINDS for _ in range(r['pins']))
        self.assertEqual(sorted(r['net'] for r in rails), want)
        self.assertEqual({r['net'] for r in rails if int(r['pwr_a_pin']) % 2 == 0}, even)
        seq = [r['net'] for r in rails if int(r['pwr_a_pin']) % 2]  # the rail row (odd), in contact order
        self.assertEqual(seq, [n for n in order if n in want and n not in even])
        # 3V3_Q6A is at the far end of the rail block from the 12-13.8 V rails of the net names
        hv = [i for i, n in enumerate(seq) if n in ('LNB13V2', 'AUX12', 'BONI13V8_PORT', 'BONI13V8')]
        self.assertEqual(seq.index('3V3_Q6A'), 0)
        self.assertEqual(hv, list(range(len(seq) - len(hv), len(seq))))

    def test_rail_nodes_are_the_low_ohm_nodes_of_the_graph(self):
        # independent scan: a resistor below rail_node_max_ohm joining a net to a net other than GND
        low = set()
        for i in range(1, 6):
            for c in json.loads((ROOT / f'design/E{i}.json').read_text(encoding='utf-8'))['components']:
                m = re.match(r'\s*(\d+(?:\.\d+)?)\s*(R|Ω|m)', c.get('value', '')) if c.get('kind') == 'resistor' else None
                nets = [p.get('net') for p in c['pins'] if p.get('net')]
                if m and float(m.group(1)) * (1e-3 if m.group(2) == 'm' else 1.0) < SPEC['rail_node_max_ohm'] \
                        and len(set(nets)) == 2 and 'GND' not in nets:
                    low |= set(nets)
        kinds = {r['net']: r['kind'] for r in NETS['nets']}
        for n, kind in kinds.items():
            if kind == 'signal':
                self.assertNotIn(n, low, n)
            if kind == 'rail node':
                self.assertIn(n, low, n)
        # W2 GR-5B (SHRINK-2): the damper capacitors of BIAS_CH1-4, VBUS_RTLB and BIAS_SB_LNA became 16SVPG47M and sit on PWR-B
        # with their 0.15 ohm resistors, so the six damper nodes (BIAS_CH1-4_DAMP, VBUS_RTLB_DAMP, E2_SB_DAMP) no longer cross
        self.assertEqual(sorted(n for n, k in kinds.items() if k == 'rail node'), [])
        self.assertTrue({'BIAS_CH1_DAMP', 'BIAS_CH4_DAMP', 'VBUS_RTLB_DAMP', 'E2_SB_DAMP'} <= low)
        self.assertFalse({'BIAS_CH1_DAMP', 'BIAS_CH4_DAMP', 'VBUS_RTLB_DAMP', 'E2_SB_DAMP', 'VBUS_LABPORT'} & set(kinds))

    def test_layout_quoted_in_pin_map_rule(self):
        # pcb/partition-spec.json b2b.pin_map_rule quotes the layout of (a); a crossing-net change must update that text
        role = {int(r['pwr_a_pin']): r['role'] for r in NETS['contacts']}
        # (sense pair at the end of the strip since 11.11.2026, for the PWR-B board of record)
        # (W2 GR-5B: 10 rail contacts instead of 17 once the six damper nodes and VBUS_LABPORT stopped crossing)
        self.assertIn('odd 1-37 the 10 rail contacts (1, 5, ... 37) with their GND returns (3, 7, ... 39), 41 guard, even 2-14 the '
                      '4 LAB5 contacts (2, 6, 10, 14) with their GND returns (4, 8, 12, 16), even 18-42 the 13 signal nets',
                      SPEC['pin_map_rule'])
        self.assertTrue({role[p] for p in range(1, 38, 4)} <= set(prepare.B2B_RAIL_KINDS))
        self.assertEqual({role[p] for p in range(3, 40, 4)} | {role[p] for p in range(4, 17, 4)}, {'gnd'})
        self.assertEqual(role[41], 'guard')
        self.assertEqual({role[p] for p in range(2, 15, 4)}, {'power'})
        # W2 PWRJ-F2C probe: 13 signal nets on the even row since the 9 E1/E5 signals of the PWR-C groups left S02
        self.assertEqual({role[p] for p in range(18, 43, 2)}, {'signal'})
        self.assertEqual({role[p] for p in list(range(44, 97, 2)) + list(range(43, 97, 2))}, {'spare'})
        self.assertEqual([role[p] for p in (97, 98, 99, 100)], ['guard', 'guard', 'sense pair', 'sense pair'])


class GraphWriterTests(unittest.TestCase):
    """pcb/write_b2b_graph.py (W2 B2B review R3) builds the map from the graphs as prepare.py main() does."""

    def test_writer_map_is_the_generated_map_and_the_graph(self):
        spec = importlib.util.spec_from_file_location('srrx_write_b2b_graph', PCB / 'write_b2b_graph.py')
        writer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(writer)
        graph = json.loads((ROOT / 'design/E2.json').read_text(encoding='utf-8'))
        res = writer.contact_map(writer.load_prepare(), graph)
        self.assertEqual(res['contacts'], NETS['contacts'])
        self.assertEqual(res['totals'], NETS['totals'])
        for half, ref in (('pwr_a', A), ('pwr_b', B)):
            self.assertEqual(writer.pins(res['contacts'], half), E2[ref]['pins'], ref)


if __name__ == '__main__':
    unittest.main()
