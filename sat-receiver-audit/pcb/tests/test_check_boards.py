"""pcb/check_boards.py: S-expression reader, board model and the independent checks (stdlib only).

The mutation tests run on small synthetic boards in pcb/tests/fixtures (F11); the DC_CORE routed prototype is
used only for a parser round trip and a pad-net comparison with the graph.
Run: python -m unittest discover -s pcb/tests  (from sat-receiver-audit/)
"""
import copy
import importlib.util
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

PCB = Path(__file__).resolve().parents[1]
ROOT = PCB.parent
FIX = Path(__file__).resolve().parent / 'fixtures'
PROTOTYPE = ROOT / 'build/kicad/pcb-prototype/detector-core-routed-prototype.kicad_pcb'
_spec = importlib.util.spec_from_file_location('srrx_check_boards', PCB / 'check_boards.py')
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)
NETCLASSES = json.loads((PCB / 'generated/netclasses.json').read_text(encoding='utf-8'))
OX, OY = 100.0, 100.0  # fixture KiCad position of contract (0, 0), contract y up

CONTRACT = {'boards': {
    'FIX_PWR': {'outline_mm': [[0, 0], [40, 0], [40, 20], [0, 20]], 'cutouts_mm': [], 'area_mm2': 800.0,
                'holes_mm': [[4, 4], [36, 4], [4, 16], [36, 16]], 'hole_d': 3.2, 'hole_keepout_d': 7.0, 'max_component_height': 9.0},
    'FIX_RF': {'outline_mm': [[0, 0], [60, 0], [60, 20], [0, 20]], 'cutouts_mm': [], 'area_mm2': 1200.0,
               'holes_mm': [[4, 4], [56, 4], [4, 16], [56, 16]], 'hole_d': 3.2, 'hole_keepout_d': 7.0, 'max_component_height': 5.5},
    'FIX_B2B': {'outline_mm': [[0, 0], [30, 0], [30, 20], [0, 20]], 'cutouts_mm': [], 'area_mm2': 600.0, 'holes_mm': [],
                'hole_d': 3.2, 'hole_keepout_d': 7.0, 'max_component_height': 9.0},
}}


def comp(ref, *nets):
    return {'ref': ref, 'footprint': '', 'pins': [{'number': str(i + 1), 'net': n} for i, n in enumerate(nets)]}


GRAPH = {c['ref']: c for c in (comp('J1', 'E1_SHUNT_P'), comp('J2', 'E1_SHUNT_P'), comp('TP1', 'E1_N'), comp('TP2', 'E1_N'),
                                comp('C1', 'E4_RTLA_RF1'), comp('C2', 'E4_RTLA_RF1'), comp('NT1', 'GND', 'CHASSIS'))}
PWR_SPEC = {'board_id': 'FIX_PWR', 'refs': ['J1', 'J2', 'TP1', 'TP2'], 'split_nets': {'E1_SHUNT_P': ['F.Cu', 'B.Cu']},
            'tht_pockets': [[5, 7, 6, 6], [29, 7, 6, 6]], 'tht_pocket_margin_mm': 1.0}
RF_SPEC = {'board_id': 'FIX_RF', 'refs': ['C1', 'C2', 'NT1'], 'bond_hole': {'at': [56, 16], 'net': 'CHASSIS'},
           'heights': {'C1': 0.6, 'C2': 0.6, 'NT1': 0.1}}
B2B_SPEC = {'board_id': 'FIX_B2B', 'board_only_refs': {'J1': 'fixture header'},
            'b2b': [{'ref': 'J1', 'mate_board': 'FIX_B2B_B', 'mate_ref': 'J1', 'pin_map': 'identity'}]}


def K(x, y):
    return OX + x, OY - y


def tree(name):
    return cb.parse((FIX / name).read_text(encoding='utf-8'))


def nodes(t, head):
    out = []
    stack = [t]
    while stack:
        n = stack.pop()
        if isinstance(n, list):
            if n and n[0] == head:
                out.append(n)
            stack.extend(n[1:])
    return out


def footprint(t, ref):
    for fp in cb.kids(t, 'footprint'):
        for p in cb.kids(fp, 'property'):
            if p[1] == 'Reference' and p[2] == ref:
                return fp
    raise KeyError(ref)


def zone(t, name):
    for z in cb.kids(t, 'zone'):
        if cb.kid(z, 'name') and cb.kid(z, 'name')[1] == name:
            return z
    raise KeyError(name)


def pts_node(points):
    return ['pts'] + [['xy', '%g' % x, '%g' % y] for x, y in (K(*p) for p in points)]


def set_fills(z, layer, polys):
    z[:] = [x for x in z if not (isinstance(x, list) and x and x[0] == 'filled_polygon')]
    for p in polys:
        z.append(['filled_polygon', ['layer', cb.Q(layer)], pts_node(p)])


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def review(t, spec, mates=None, graph=GRAPH):
    return cb.review_board(cb.Board(t), spec, CONTRACT, graph, NETCLASSES, mates=mates)


def checks_failed(doc):
    return sorted({f['check'] for f in doc['findings']})


class ParserTests(unittest.TestCase):
    def test_atoms_strings_and_escapes(self):
        t = cb.parse('(a "x y" b (c "q\\"uote" "back\\\\slash") ( d ))')
        self.assertEqual(t, ['a', 'x y', 'b', ['c', 'q"uote', 'back\\slash'], ['d']])
        self.assertIsInstance(t[1], cb.Q)
        self.assertNotIsInstance(t[2], cb.Q)
        self.assertEqual(cb.parse(cb.dump(t)), t)

    def test_syntax_errors(self):
        for bad in ('(a (b)', '(a))', '(a) (b)', ''):
            with self.assertRaises(ValueError, msg=bad):
                cb.parse(bad)

    def test_prototype_round_trip(self):
        # DC_CORE routed prototype (KiCad 10.0.7, 71 parts / 187 pins / 40 nets): parser round trip only.
        t = cb.parse(PROTOTYPE.read_text(encoding='utf-8'))
        self.assertEqual(cb.parse(cb.dump(t)), t)
        b = cb.Board(t)
        self.assertEqual(len(b.footprints), 71)
        self.assertEqual(len(b.pads), 187)
        self.assertEqual(len({p['net'] for p in b.pads if p['net']}), 40)
        self.assertEqual(b.copper_layers, ['F.Cu', 'B.Cu'])
        self.assertEqual(b.holes, [])

    def test_prototype_pad_nets_match_core_input_and_graph(self):
        b = cb.load_board(PROTOTYPE)
        core = json.loads((ROOT / 'pcb/generated/detector-core-input.json').read_text(encoding='utf-8'))
        want = {(n['ref'], str(n['pin'])): net for net, ns in core['nets'].items() for n in ns}
        got = {(p['ref'], p['number']): p['net'] for p in b.pads if p['net']}
        self.assertEqual(got, want)
        graph = cb.load_graph()
        spec = {'domains': ['DC_CORE']}
        views = cb.expected_views(spec, graph)
        self.assertEqual(len(views[0][1]), 71)
        findings, info = cb.check_pad_nets(b, spec, graph, views)
        self.assertEqual(findings, [])
        self.assertEqual(info['expected_refs'], 71)

    def test_rotation_matches_kicad(self):
        # C4415 of the prototype sits at (76, 90.3, 90 deg); pad 2 (GND) at (76, 89.525) where its GND track starts.
        b = cb.load_board(PROTOTYPE)
        pad = next(p for p in b.pads if p['ref'] == 'C4415' and p['number'] == '2')
        self.assertAlmostEqual(pad['x'], 76.0, places=6)
        self.assertAlmostEqual(pad['y'], 89.525, places=6)
        self.assertEqual(pad['net'], 'GND')

    def test_net_forms(self):
        t = cb.parse('(kicad_pcb (layers (0 "F.Cu" signal) (2 "B.Cu" signal)) (net 0 "") (net 1 "GND")'
                     ' (segment (start 0 0) (end 1 0) (width 0.2) (layer "F.Cu") (net 1))'
                     ' (segment (start 0 1) (end 1 1) (width 0.2) (layer "F.Cu") (net "VCC")))')
        b = cb.Board(t)
        self.assertEqual([it.net for it in b.tracks], ['GND', 'VCC'])


class BaseFixtureTests(unittest.TestCase):
    def test_fixtures_have_no_findings(self):
        self.assertEqual(review(tree('power_neck.kicad_pcb'), PWR_SPEC)['findings'], [])
        self.assertEqual(review(tree('rf_cpwg.kicad_pcb'), RF_SPEC)['findings'], [])
        mate = cb.Board(tree('b2b_b.kicad_pcb'))
        self.assertEqual(review(tree('b2b_a.kicad_pcb'), B2B_SPEC, mates={'FIX_B2B_B': mate})['findings'], [])

    def test_review_shape_and_labels(self):
        doc = review(tree('power_neck.kicad_pcb'), PWR_SPEC)
        self.assertTrue(doc['status'].startswith('MODEL_CHECK'))
        self.assertEqual(doc['result'], 'NO_FINDINGS')
        self.assertEqual(set(doc['inputs']['projection_sha256']), {'graph_refs_pins_nets', 'footprints', 'contract_board', 'netclasses', 'spec'})
        self.assertEqual(doc['frame']['origin'], [OX, OY])
        necks = doc['checks']['class_widths']['pour_necks']
        self.assertEqual({(n['net'], n['layer']) for n in necks}, {('E1_SHUNT_P', 'F.Cu'), ('E1_SHUNT_P', 'B.Cu')})
        for n in necks:
            self.assertAlmostEqual(n['neck_mm'], 6.0, delta=2 * cb.NECK_GRID)
        self.assertNotIn('PASS', json.dumps(doc))


class PowerMutationTests(unittest.TestCase):
    def notch(self, neck):
        # pour 6..34 x 7..13; a notch from the bottom edge leaves `neck` mm at x 19..21
        return [(6, 7), (19, 7), (19, 13 - neck), (21, 13 - neck), (21, 7), (34, 7), (34, 13), (6, 13)]

    def test_narrowed_batt_neck_fails(self):
        t = tree('power_neck.kicad_pcb')
        set_fills(zone(t, 'BATT_L1'), 'F.Cu', [self.notch(1.0)])
        doc = review(t, PWR_SPEC)
        hits = [f for f in doc['findings'] if f['check'] == 'class_widths' and f['layer'] == 'F.Cu']
        self.assertEqual(len(hits), 1, doc['findings'])
        self.assertAlmostEqual(hits[0]['value'], 1.0, delta=2 * cb.NECK_GRID)
        self.assertEqual(hits[0]['limit'], NETCLASSES['classes']['BATT']['split_outer_per_layer_mm'])
        self.assertAlmostEqual(hits[0]['at'][0], OX + 20, delta=1.5)

    def test_split_rule_needs_the_split_declaration(self):
        t = tree('power_neck.kicad_pcb')
        set_fills(zone(t, 'BATT_L1'), 'F.Cu', [self.notch(2.5)])
        self.assertEqual(review(t, PWR_SPEC)['findings'], [])  # 2.5 >= 1.85 per layer when split on L1 + L4
        single = {k: v for k, v in PWR_SPEC.items() if k != 'split_nets'}
        doc = review(t, single)  # 2.5 < 3.2 on one layer
        self.assertEqual([f['limit'] for f in doc['findings'] if f['check'] == 'class_widths'], [3.2])

    def test_narrowed_track_fails(self):
        t = tree('power_neck.kicad_pcb')
        for seg in cb.kids(t, 'segment'):
            seg[seg.index(cb.kid(seg, 'width'))] = ['width', '1']
        doc = review(t, PWR_SPEC)
        self.assertEqual(checks_failed(doc), ['class_widths'])
        self.assertEqual(doc['findings'][0]['limit'], 3.2)

    def test_pad_escape_exemption(self):
        t = tree('power_neck.kicad_pcb')
        tp1 = K(12, 17)
        t.append(['segment', ['start', '%g' % tp1[0], '%g' % tp1[1]], ['end', '%g' % (tp1[0] + 1.5), '%g' % tp1[1]],
                  ['width', '0.5'], ['layer', cb.Q('F.Cu')], ['net', cb.Q('E1_N')]])
        self.assertEqual(checks_failed(review(t, PWR_SPEC)), ['class_widths'])
        spec = dict(PWR_SPEC, neck_exempt={'TP1': {'escape_mm': 0.5, 'reason': 'test'}})
        self.assertEqual(review(t, spec)['findings'], [])

    def test_netted_mounting_hole_fails(self):
        t = tree('power_neck.kicad_pcb')
        pad = cb.kid(footprint(t, 'H1'), 'pad')
        pad[1], pad[2] = cb.Q('1'), 'thru_hole'
        pad.append(['net', cb.Q('GND')])
        doc = review(t, PWR_SPEC)
        self.assertIn('holes', checks_failed(doc))
        self.assertTrue(any('plated or netted' in f['detail'] for f in doc['findings']))

    def test_moved_hole_fails(self):
        t = tree('power_neck.kicad_pcb')
        at = cb.kid(footprint(t, 'H2'), 'at')
        at[1] = '%g' % (float(at[1]) + 0.5)
        self.assertIn('holes', checks_failed(review(t, PWR_SPEC)))

    def test_copper_in_keepout_fails(self):
        t = tree('power_neck.kicad_pcb')
        x, y = K(5, 6)
        t.append(['via', ['at', '%g' % x, '%g' % y], ['size', '0.6'], ['drill', '0.3'], ['layers', cb.Q('F.Cu'), cb.Q('B.Cu')], ['net', cb.Q('GND')]])
        doc = review(t, PWR_SPEC)
        self.assertEqual(checks_failed(doc), ['keepouts'])
        self.assertEqual(len(doc['findings']), 4)  # the through via on each of the four copper layers

    def test_outline_change_fails(self):
        t = tree('power_neck.kicad_pcb')
        line = cb.kids(t, 'gr_line')[1]
        cb.kid(line, 'end')[1] = '141'
        cb.kid(cb.kids(t, 'gr_line')[2], 'start')[1] = '141'
        self.assertIn('outline', checks_failed(review(t, PWR_SPEC)))

    def test_wrong_pad_net_fails(self):
        t = tree('power_neck.kicad_pcb')
        pad = cb.kid(footprint(t, 'TP2'), 'pad')
        cb.kid(pad, 'net')[1] = cb.Q('E1_SW')
        self.assertIn('pad_nets', checks_failed(review(t, PWR_SPEC)))

    def test_missing_and_unexpected_refs(self):
        t = tree('power_neck.kicad_pcb')
        self.assertIn('pad_nets', checks_failed(review(t, dict(PWR_SPEC, refs=['J1', 'J2', 'TP1', 'TP2', 'C1']))))
        self.assertIn('pad_nets', checks_failed(review(t, dict(PWR_SPEC, refs=['J1', 'J2', 'TP1']))))

    def test_tht_outside_pocket_fails(self):
        t = tree('power_neck.kicad_pcb')
        spec = dict(PWR_SPEC, tht_pockets=[[5, 7, 6, 6], [30, 7, 6, 6]])
        doc = review(t, spec)
        self.assertEqual(checks_failed(doc), ['tht_pockets'])
        self.assertEqual(doc['findings'][0]['item'], 'J2.1')

    def test_height_zone(self):
        t = tree('power_neck.kicad_pcb')
        spec = dict(PWR_SPEC, heights={'J1': 9.5})
        self.assertEqual(checks_failed(review(t, spec)), ['heights'])
        spec['height_zones'] = [{'rect': [5, 7, 6, 6], 'max_height': 10.5, 'side': 'top'}]
        self.assertEqual(review(t, spec)['findings'], [])
        t2 = tree('power_neck.kicad_pcb')
        prop = next(p for p in cb.kids(footprint(t2, 'J2'), 'property') if p[1] == 'Height')
        prop[2] = cb.Q('9.2')
        self.assertEqual(checks_failed(review(t2, PWR_SPEC)), ['heights'])

    def test_bottom_side_part_fails_on_top_only_board(self):
        t = tree('power_neck.kicad_pcb')
        cb.kid(footprint(t, 'TP1'), 'layer')[1] = cb.Q('B.Cu')
        self.assertIn('heights', checks_failed(review(t, PWR_SPEC)))


class RfMutationTests(unittest.TestCase):
    G = 0.18 + 0.20

    def top_fills(self, upper_edge):
        g = self.G
        return [rect(9, 4.5, 51, 10 - g), rect(9, upper_edge, 51, 15.5), rect(9, 10 - g, 10, upper_edge), rect(50, 10 - g, 51, upper_edge)]

    def test_moved_cpwg_gap_fails(self):
        t = tree('rf_cpwg.kicad_pcb')
        set_fills(zone(t, 'GND_L1'), 'F.Cu', self.top_fills(10.25))  # ground edge 0.07 mm from the trace edge
        doc = review(t, RF_SPEC)
        self.assertEqual(checks_failed(doc), ['rf50'])
        self.assertTrue(any('inside the 0.2 mm CPWG gap' in f['detail'] for f in doc['findings']))

    def test_missing_coplanar_ground_fails(self):
        t = tree('rf_cpwg.kicad_pcb')
        set_fills(zone(t, 'GND_L1'), 'F.Cu', self.top_fills(10.6))  # gap 0.42 mm on one side
        doc = review(t, RF_SPEC)
        self.assertEqual(checks_failed(doc), ['rf50'])
        self.assertTrue(any('no coplanar GND' in f['detail'] for f in doc['findings']))

    def test_l2_void_fails(self):
        t = tree('rf_cpwg.kicad_pcb')
        set_fills(zone(t, 'GND_L2'), 'In1.Cu', [rect(9, 4.5, 29, 15.5), rect(31, 4.5, 51, 15.5)])
        doc = review(t, RF_SPEC)
        self.assertEqual(checks_failed(doc), ['rf50'])
        self.assertTrue(any('In1.Cu GND void' in f['detail'] for f in doc['findings']))

    def test_l2_void_outside_band_passes(self):
        t = tree('rf_cpwg.kicad_pcb')
        band = NETCLASSES['classes']['RF50']['l2_solid_band_mm']
        set_fills(zone(t, 'GND_L2'), 'In1.Cu', [rect(9, 4.5, 51, 10 - band - 0.2), rect(9, 10 - band - 0.1, 51, 15.5)])
        self.assertEqual(review(t, RF_SPEC)['findings'], [])

    def test_fence_gap_fails(self):
        t = tree('rf_cpwg.kicad_pcb')
        drop = {K(28, 10.88), K(29.5, 10.88)}
        t[:] = [n for n in t if not (isinstance(n, list) and n and n[0] == 'via'
                                     and (float(cb.kid(n, 'at')[1]), float(cb.kid(n, 'at')[2])) in drop)]
        doc = review(t, RF_SPEC)
        self.assertEqual(checks_failed(doc), ['rf50'])
        f = next(f for f in doc['findings'] if 'fence' in f['detail'])
        self.assertAlmostEqual(f['value'], 4.5, places=3)

    def test_wrong_rf_width_fails(self):
        t = tree('rf_cpwg.kicad_pcb')
        seg = next(s for s in cb.kids(t, 'segment') if cb.kid(s, 'net')[1] == 'E4_RTLA_RF1')
        cb.kid(seg, 'width')[1] = '0.3'
        self.assertEqual(checks_failed(review(t, RF_SPEC)), ['rf50'])

    def test_rf_off_l1_fails(self):
        t = tree('rf_cpwg.kicad_pcb')
        seg = next(s for s in cb.kids(t, 'segment') if cb.kid(s, 'net')[1] == 'E4_RTLA_RF1')
        cb.kid(seg, 'layer')[1] = cb.Q('B.Cu')
        self.assertIn('rf50', checks_failed(review(t, RF_SPEC)))

    def test_second_tie_fails(self):
        t = tree('rf_cpwg.kicad_pcb')
        nt2 = copy.deepcopy(footprint(t, 'NT1'))
        next(p for p in cb.kids(nt2, 'property') if p[1] == 'Reference')[2] = cb.Q('NT2')
        cb.kid(nt2, 'at')[2] = '%g' % (float(cb.kid(nt2, 'at')[2]) + 3)
        t.append(nt2)
        doc = review(t, dict(RF_SPEC, board_only_refs={'NT2': 'test'}))
        self.assertEqual(checks_failed(doc), ['gnd_chassis_ties'])
        self.assertEqual(doc['findings'][0]['refs'], ['NT1', 'NT2'])

    def test_bond_hole_rules(self):
        t = tree('rf_cpwg.kicad_pcb')
        # CHASSIS copper may enter the bond hole keepout (base fixture); GND copper may not
        x0, y0 = K(52.5, 12)
        x1, y1 = K(55, 15)
        t.append(['segment', ['start', '%g' % x0, '%g' % y0], ['end', '%g' % x1, '%g' % y1], ['width', '0.3'],
                  ['layer', cb.Q('B.Cu')], ['net', cb.Q('GND')]])
        doc = review(t, RF_SPEC)
        self.assertEqual(checks_failed(doc), ['keepouts'])
        t2 = tree('rf_cpwg.kicad_pcb')
        cb.kid(cb.kid(footprint(t2, 'HB1'), 'pad'), 'net')[1] = cb.Q('GND')
        self.assertIn('holes', checks_failed(review(t2, RF_SPEC)))


class B2BMutationTests(unittest.TestCase):
    def test_pin_swap_fails(self):
        mate_tree = tree('b2b_b.kicad_pcb')
        fp = footprint(mate_tree, 'J1')
        pads = {p[1]: p for p in cb.kids(fp, 'pad')}
        n9, n10 = cb.kid(pads['9'], 'net'), cb.kid(pads['10'], 'net')
        n9[1], n10[1] = n10[1], n9[1]
        doc = review(tree('b2b_a.kicad_pcb'), B2B_SPEC, mates={'FIX_B2B_B': cb.Board(mate_tree)})
        self.assertEqual(checks_failed(doc), ['b2b'])
        self.assertEqual(sorted(f['item'] for f in doc['findings']), ['J1.10', 'J1.9'])

    def test_pin_map_and_missing_mate(self):
        a, b = tree('b2b_a.kicad_pcb'), cb.Board(tree('b2b_b.kicad_pcb'))
        mapped = dict(B2B_SPEC, b2b=[dict(B2B_SPEC['b2b'][0], pin_map={str(i): str(i) for i in range(1, 11)})])
        self.assertEqual(review(a, mapped, mates={'FIX_B2B_B': b})['findings'], [])
        self.assertEqual(checks_failed(review(a, B2B_SPEC, mates={})), ['b2b'])

    def test_instances_map_template_nets(self):
        # one template board, two graph instances (as ENC301/ENC302 are one design built twice)
        nets = ['LAB5', 'LAB5', 'GND', 'GND', 'SYS12', 'SYS12', 'GND', 'GND', 'I2C0_SDA', 'I2C0_SCL']
        graph = {'X1': {'ref': 'X1', 'footprint': '', 'pins': [{'number': str(i + 1), 'net': n} for i, n in enumerate(nets)]},
                 'X2': {'ref': 'X2', 'footprint': '', 'pins': [{'number': str(i + 1), 'net': n.replace('I2C0', 'I2C2')} for i, n in enumerate(nets)]}}
        spec = {'board_id': 'FIX_B2B', 'instances': [{'id': 'a', 'ref_map': {'J1': 'X1'}, 'net_map': {}},
                                                     {'id': 'b', 'ref_map': {'J1': 'X2'}, 'net_map': {'I2C0_SDA': 'I2C2_SDA', 'I2C0_SCL': 'I2C2_SCL'}}]}
        self.assertEqual(review(tree('b2b_a.kicad_pcb'), spec, graph=graph)['findings'], [])
        bad = json.loads(json.dumps(spec))
        bad['instances'][1]['net_map'] = {}
        doc = review(tree('b2b_a.kicad_pcb'), bad, graph=graph)
        self.assertEqual(sorted(f['item'] for f in doc['findings']), ['J1.10', 'J1.9'])


class NeckRasterTests(unittest.TestCase):
    def test_strip_width(self):
        for w in (0.5, 1.0, 1.85, 3.2):
            strip = cb.Poly([(0, 0), (10, 0), (10, w), (0, w)])
            a, b = cb.Poly([(-1, -1), (0.2, -1), (0.2, w + 1), (-1, w + 1)]), cb.Poly([(9.8, -1), (11, -1), (11, w + 1), (9.8, w + 1)])
            items = [cb.Item('zone', 'N', 'F.Cu', strip)]
            necks = cb.raster_neck(items, [a, b], (-1.5, -1.5, 11.5, w + 1.5), entry=w / 2)
            self.assertEqual(len(necks), 1)
            self.assertAlmostEqual(necks[0][0], w, delta=2 * cb.NECK_GRID, msg=w)

    def test_end_terminal_without_entry_is_a_false_neck(self):
        # documents why entry > 0: a terminal at the very end of a strip sees the strip end as a neck
        strip = cb.Poly([(0, 0), (10, 0), (10, 2), (0, 2)])
        a, b = cb.Poly([(0, 0), (0.2, 0), (0.2, 2), (0, 2)]), cb.Poly([(9.8, 0), (10, 0), (10, 2), (9.8, 2)])
        items = [cb.Item('zone', 'N', 'F.Cu', strip)]
        self.assertLess(cb.raster_neck(items, [a, b], (-1, -1, 11, 3))[0][0], 1.0)
        self.assertAlmostEqual(cb.raster_neck(items, [a, b], (-1, -1, 11, 3), entry=1.0)[0][0], 2.0, delta=2 * cb.NECK_GRID)

    def test_mid_strip_neck_is_found(self):
        poly = cb.Poly([(0, 0), (4.5, 0), (4.5, 1.2), (5.5, 1.2), (5.5, 0), (10, 0), (10, 3), (0, 3)])
        a, b = cb.Poly([(0, 0), (0.3, 0), (0.3, 3), (0, 3)]), cb.Poly([(9.7, 0), (10, 0), (10, 3), (9.7, 3)])
        necks = cb.raster_neck([cb.Item('zone', 'N', 'F.Cu', poly)], [a, b], (-1, -1, 11, 4), entry=1.5)
        self.assertAlmostEqual(necks[0][0], 1.8, delta=2 * cb.NECK_GRID)

    def test_dead_end_spur_is_not_a_neck(self):
        body = cb.Poly([(0, 0), (10, 0), (10, 4), (0, 4)])
        spur = cb.Poly([(4, 4), (5, 4), (5, 9), (4, 9)])  # 1 mm finger without a terminal
        a, b = cb.Poly([(-1, 0), (0.5, 0), (0.5, 4), (-1, 4)]), cb.Poly([(9.5, 0), (11, 0), (11, 4), (9.5, 4)])
        necks = cb.raster_neck([cb.Item('zone', 'N', 'F.Cu', body), cb.Item('zone', 'N', 'F.Cu', spur)], [a, b], (-1.5, -1.5, 11.5, 10.5), entry=2.0)
        self.assertAlmostEqual(necks[0][0], 4.0, delta=2 * cb.NECK_GRID)


class ReviewFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.saved = (cb.BOARDS_DIR, cb.OUT_DIR, cb.CONTRACT, cb.ROOT)
        cb.ROOT = base
        cb.BOARDS_DIR = base / 'pcb/boards'
        cb.OUT_DIR = base / 'build/kicad/boards'
        cb.CONTRACT = base / 'contract.json'
        cb.CONTRACT.write_text(json.dumps(CONTRACT), encoding='utf-8')

    def tearDown(self):
        cb.BOARDS_DIR, cb.OUT_DIR, cb.CONTRACT, cb.ROOT = self.saved
        self.tmp.cleanup()

    def run_main(self, *args):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            rc = cb.main(list(args))
        return rc, out.getvalue()

    def test_no_boards_is_not_an_error(self):
        rc, out = self.run_main('--all', '--check')
        self.assertEqual(rc, 0)
        self.assertIn('0 boards', out)

    def test_write_then_check(self):
        cb.BOARDS_DIR.mkdir(parents=True)
        (cb.BOARDS_DIR / 'FIX_PWR.json').write_text(json.dumps(dict(PWR_SPEC, refs=[], board_only_refs={r: 'fixture' for r in PWR_SPEC['refs']})), encoding='utf-8')
        target = cb.OUT_DIR / 'FIX_PWR' / 'FIX_PWR.kicad_pcb'
        target.parent.mkdir(parents=True)
        target.write_text((FIX / 'power_neck.kicad_pcb').read_text(encoding='utf-8'), encoding='utf-8')
        rc, _ = self.run_main('--all', '--check')
        self.assertEqual(rc, 1)  # no review.json yet: stale
        rc, out = self.run_main('--board', 'FIX_PWR')
        self.assertEqual(rc, 0, out)
        review_path = cb.OUT_DIR / 'FIX_PWR' / 'review.json'
        doc = json.loads(review_path.read_text(encoding='utf-8'))
        self.assertEqual(doc['inputs']['board_file']['path'], 'build/kicad/boards/FIX_PWR/FIX_PWR.kicad_pcb')
        self.assertEqual(self.run_main('--all', '--check')[0], 0)
        target.write_text(target.read_text(encoding='utf-8').replace('(width 3.3)', '(width 1)'), encoding='utf-8')
        self.assertEqual(self.run_main('--all', '--check')[0], 1)


class ProjectionTests(unittest.TestCase):
    def test_unrelated_graph_edit_keeps_hashes(self):
        b = cb.Board(tree('power_neck.kicad_pcb'))
        views = cb.expected_views(PWR_SPEC, GRAPH)
        cbd = CONTRACT['boards']['FIX_PWR']
        base = cb.projections(b, PWR_SPEC, cbd, GRAPH, views, NETCLASSES)
        other = dict(GRAPH, C1=dict(GRAPH['C1'], footprint='Lib:Changed', mpn='X'))
        self.assertEqual(cb.projections(b, PWR_SPEC, cbd, other, views, NETCLASSES), base)
        moved = dict(GRAPH, J1=comp('J1', 'E1_SW'))
        changed = cb.projections(b, PWR_SPEC, cbd, moved, views, NETCLASSES)
        self.assertNotEqual(changed['graph_refs_pins_nets'], base['graph_refs_pins_nets'])
        self.assertEqual(changed['contract_board'], base['contract_board'])


if __name__ == '__main__':
    unittest.main()
