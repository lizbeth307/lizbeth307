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


# ---------------------------------------------------------------- review fixes (W2 PCB-RULES review PR-01 .. PR-11)
import math  # noqa: E402

ENC_SPEC = ROOT / 'pcb/boards/ENC.json'
ENC_BOARD = ROOT / 'build/kicad/boards/ENC/ENC.kicad_pcb'


def v1_spec(**extra):
    """A srrx-board-spec-v1 spec in the shape of pcb/boards/ENC.json (PCB-PIPE), on the B2B fixture board:
    template ref J1 built as X1 and X2, placeholder P1 with a spec pin map."""
    spec = {
        'schema': 'srrx-board-spec-v1', 'board_id': 'FIX_B2B', 'status': 'PILOT_NOT_FOR_FABRICATION',
        'contract': {'file': 'mechanical/generated/contract/boards.json', 'board': 'FIX_B2B'},
        'domains': ['FIX'], 'layers': {'copper': 2}, 'project': 'build/kicad/boards/FIX_B2B/FIX_B2B.kicad_pro',
        'instances': {'template_nets': ['LAB5', 'GND', 'SYS12', 'I2C0_SDA', 'I2C0_SCL'], 'list': [
            {'id': 'a', 'qty': 1, 'refs': {'J1': 'X1', 'P1': None},
             'nets': {'LAB5': 'LAB5', 'GND': 'GND', 'SYS12': 'SYS12', 'I2C0_SDA': 'I2C0_SDA', 'I2C0_SCL': 'I2C0_SCL'}},
            {'id': 'b', 'qty': 1, 'refs': {'J1': 'X2', 'P1': None},
             'nets': {'LAB5': 'LAB5', 'GND': 'GND', 'SYS12': 'SYS12', 'I2C0_SDA': 'I2C2_SDA', 'I2C0_SCL': 'I2C2_SCL'}}]},
        'parts': [{'ref': 'J1', 'source': 'graph', 'anchor': {'at': [15, 10]}},
                  {'ref': 'P1', 'source': 'pilot_placeholder', 'pins': {'1': 'GND'}, 'replaced_by': 'test'}],
        'holes': {'from_contract': True, 'ref_prefix': 'H', 'keepout_layers': ['F.Cu', 'B.Cu'], 'keepout_blocks': ['tracks']},
        'height_zones': [{'region': 'board', 'max_height_mm_from_contract': 'max_component_height', 'checked': False, 'why': 'test'}],
        'router': {'tool': 'freerouting'}, 'drc_policy': {'warning_checks': {}},
    }
    spec.update(extra)
    return spec


B2B_NETS = ['LAB5', 'LAB5', 'GND', 'GND', 'SYS12', 'SYS12', 'GND', 'GND', 'I2C0_SDA', 'I2C0_SCL']
B2B_GRAPH = {'X1': {'ref': 'X1', 'footprint': '', 'pins': [{'number': str(i + 1), 'net': n} for i, n in enumerate(B2B_NETS)]},
             'X2': {'ref': 'X2', 'footprint': '', 'pins': [{'number': str(i + 1), 'net': n.replace('I2C0', 'I2C2')} for i, n in enumerate(B2B_NETS)]}}


def b2b_with_placeholder(net='GND'):
    t = tree('b2b_a.kicad_pcb')
    x, y = K(26, 4)
    t.append(['footprint', cb.Q('Fixture:PAD_SMD'), ['layer', cb.Q('F.Cu')], ['at', '%g' % x, '%g' % y],
              ['property', cb.Q('Reference'), cb.Q('P1')],
              ['pad', cb.Q('1'), 'smd', 'rect', ['at', '0', '0'], ['size', '1', '1'], ['layers', cb.Q('F.Cu')], ['net', cb.Q(net)]]])
    return t


def seg(t, a, b, width, layer, net):
    (x0, y0), (x1, y1) = K(*a), K(*b)
    t.append(['segment', ['start', '%g' % x0, '%g' % y0], ['end', '%g' % x1, '%g' % y1], ['width', '%g' % width],
              ['layer', cb.Q(layer)], ['net', cb.Q(net)]])


def smd_footprint(t, ref, at, net, size=1.0):
    x, y = K(*at)
    t.append(['footprint', cb.Q('Fixture:PAD_SMD'), ['layer', cb.Q('F.Cu')], ['at', '%g' % x, '%g' % y],
              ['property', cb.Q('Reference'), cb.Q(ref)], ['property', cb.Q('Height'), cb.Q('0.5')],
              ['pad', cb.Q('1'), 'smd', 'rect', ['at', '0', '0'], ['size', '%g' % size, '%g' % size], ['layers', cb.Q('F.Cu')], ['net', cb.Q(net)]]])


class SpecFormTests(unittest.TestCase):
    """PR-01: pcb/boards/<B>.json is shared with board_gen (srrx-board-spec-v1)."""

    def test_v1_shape_translates(self):
        s = cb.normalize_spec(v1_spec())
        self.assertEqual(s['contract_board'], 'FIX_B2B')
        self.assertEqual(s['board_file'], 'build/kicad/boards/FIX_B2B/FIX_B2B.kicad_pcb')
        self.assertEqual([i['ref_map'] for i in s['instances']], [{'J1': 'X1'}, {'J1': 'X2'}])
        self.assertEqual(s['instances'][1]['net_map']['I2C0_SDA'], 'I2C2_SDA')
        self.assertIn('P1', s['board_only_refs'])
        self.assertEqual(s['board_only_pins'], {'P1': {'1': 'GND'}})
        self.assertEqual(s['hole_ref_prefixes'], ['H'])
        self.assertEqual(s['height_zones'], [{'side': 'top', 'board': True, 'max_height_from_contract': 'max_component_height', 'spec_checked': False}])
        self.assertNotIn('router', s)
        self.assertEqual(cb.normalize_spec(s), s)  # idempotent

    def test_board_gen_only_keys_do_not_stale_the_review(self):
        b = cb.Board(b2b_with_placeholder())
        base = review(b2b_with_placeholder(), v1_spec(), graph=B2B_GRAPH)
        other = review(b2b_with_placeholder(), v1_spec(router={'tool': 'freerouting', 'max_passes': 99}), graph=B2B_GRAPH)
        self.assertEqual(base['inputs']['projection_sha256'], other['inputs']['projection_sha256'])
        self.assertTrue(b.footprints)

    def test_v1_spec_reviews_a_template_board(self):
        doc = review(b2b_with_placeholder(), v1_spec(), graph=B2B_GRAPH)
        self.assertEqual(doc['findings'], [])
        self.assertTrue(any(u['check'] == 'heights' for u in doc['unverified']))
        bad = v1_spec()
        bad['instances']['list'][1]['nets']['I2C0_SDA'] = 'I2C0_SDA'
        bad['instances']['list'][1]['nets']['I2C0_SCL'] = 'I2C0_SCL'
        self.assertEqual(sorted(f['item'] for f in review(b2b_with_placeholder(), bad, graph=B2B_GRAPH)['findings']), ['J1.10', 'J1.9'])

    def test_placeholder_pins_are_checked(self):
        doc = review(b2b_with_placeholder('LAB5'), v1_spec(), graph=B2B_GRAPH)
        self.assertEqual([(f['check'], f['item']) for f in doc['findings']], [('pad_nets', 'P1.1')])

    def test_unknown_shapes_stop_with_a_message(self):
        for bad in (v1_spec(schema='srrx-board-spec-v9'), v1_spec(instances=['J1']), v1_spec(instances={'list': [{'id': 'a', 'refs': ['J1']}]}),
                    v1_spec(contract='ENC'), v1_spec(height_zones=[{'region': 'left', 'max_height_mm': 3}]), v1_spec(holes=['H1']),
                    {'board_id': 'FIX_PWR', 'instances': ['x']}, {'board_id': 'FIX_PWR', 'split_nets': ['E1_SHUNT_P']}):
            with self.assertRaises(SystemExit, msg=json.dumps(bad)[:120]) as ctx:
                review(tree('b2b_a.kicad_pcb'), bad, graph=B2B_GRAPH)
            self.assertIn('check_boards:', str(ctx.exception))

    @unittest.skipUnless(ENC_SPEC.is_file() and ENC_BOARD.is_file(), 'ENC pilot (PCB-PIPE) not on this branch')
    def test_enc_pilot_spec_and_board(self):
        # the shared spec and the KiCad-filled pilot board: no crash, and the KiCad knockout polygons pass the keepout check
        spec = json.loads(ENC_SPEC.read_text(encoding='utf-8'))
        doc = cb.review_board(cb.load_board(ENC_BOARD), spec, json.loads(cb.CONTRACT.read_text(encoding='utf-8')),
                              cb.load_graph(), NETCLASSES, {})
        self.assertEqual(doc['checks']['keepouts']['findings'], 0, doc['findings'])
        self.assertGreater(doc['checks']['pad_nets']['expected_refs'], 0)
        self.assertEqual(doc['checks']['pth_annular']['fab_floor'], 'jlc_2l_1oz')
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            rc = cb.main(['--all', '--check'])  # a missing review.json is stale (rc 1), never a traceback
        self.assertIn(rc, (0, 1))
        self.assertIn('ENC', out.getvalue())


def knockout_fill(cx, cy, r, n=32, outer=3.9):
    """Fractured fill (square with a zero-width slit into a hole): the hole is the n-gon circumscribed about radius r,
    vertices on the 1 nm grid, as a KiCad fill around a rule-area keepout. Contract mm."""
    rr = r / math.cos(math.pi / n)
    ring = [(round(cx + rr * math.cos(2 * math.pi * k / n), 6), round(cy + rr * math.sin(2 * math.pi * k / n), 6)) for k in range(n)]
    return [(cx + outer, cy), (cx + outer, cy + outer), (cx - outer, cy + outer), (cx - outer, cy - outer), (cx + outer, cy - outer),
            (cx + outer, cy), ring[0]] + ring[:0:-1] + [ring[0]]


class KeepoutToleranceTests(unittest.TestCase):
    """PR-02: KiCad knockouts sit a few nm inside the keepout radius."""

    def add_fill(self, t, r):
        t.append(['zone', ['net', cb.Q('GND')], ['layer', cb.Q('F.Cu')], ['name', cb.Q('GND_KO')],
                  ['filled_polygon', ['layer', cb.Q('F.Cu')], pts_node(knockout_fill(4, 4, r))]])

    def test_knockout_at_the_keepout_radius_passes(self):
        t = tree('power_neck.kicad_pcb')
        self.add_fill(t, 3.5 - 2e-6)  # edge midpoints 2 nm inside r 3.5 (ENC pilot: 2.9999987 against 3.0)
        doc = review(t, PWR_SPEC)
        self.assertEqual([f for f in doc['findings'] if f['check'] == 'keepouts'], [])

    def test_copper_20um_inside_fails(self):
        t = tree('power_neck.kicad_pcb')
        self.add_fill(t, 3.5 - 0.02)
        self.assertIn('keepouts', checks_failed(review(t, PWR_SPEC)))


def drop_zone(t, name):
    t[:] = [n for n in t if not (isinstance(n, list) and n and n[0] == 'zone' and cb.kid(n, 'name') and cb.kid(n, 'name')[1] == name)]


class SplitVerificationTests(unittest.TestCase):
    """PR-03: a split_nets declaration is verified, not trusted."""

    def test_split_with_missing_l4_pour_fails(self):
        t = tree('power_neck.kicad_pcb')
        drop_zone(t, 'BATT_L4')
        set_fills(zone(t, 'BATT_L1'), 'F.Cu', [PowerMutationTests().notch(2.0)])
        doc = review(t, PWR_SPEC)
        split = [f for f in doc['findings'] if f['item'] == 'split E1_SHUNT_P']
        self.assertEqual(len(split), 1, doc['findings'])
        self.assertIn('no B.Cu pour or track', split[0]['detail'])
        necks = [f for f in doc['findings'] if f['item'] == 'pour E1_SHUNT_P']
        self.assertEqual([f['limit'] for f in necks], [NETCLASSES['classes']['BATT']['outer_min_width_mm']])
        self.assertFalse(doc['checks']['class_widths']['split_nets']['E1_SHUNT_P']['verified'])

    def test_split_with_broken_l4_pour_fails(self):
        t = tree('power_neck.kicad_pcb')
        set_fills(zone(t, 'BATT_L4'), 'B.Cu', [rect(6, 7, 19, 13), rect(21, 7, 34, 13)])
        doc = review(t, PWR_SPEC)
        self.assertEqual([f['item'] for f in doc['findings']], ['split E1_SHUNT_P'])
        self.assertIn('different groups', doc['findings'][0]['detail'])

    def test_intact_split_is_verified(self):
        doc = review(tree('power_neck.kicad_pcb'), PWR_SPEC)
        self.assertTrue(doc['checks']['class_widths']['split_nets']['E1_SHUNT_P']['verified'])


class InnerPowerTrackTests(unittest.TestCase):
    """PR-04: BATT/PWR3A inner copper is not a current path; an inner track of these classes is a finding."""

    def test_batt_track_on_inner_layer_fails(self):
        t = tree('power_neck.kicad_pcb')
        seg(t, (10, 10), (30, 10), 0.15, 'In2.Cu', 'E1_SHUNT_P')
        doc = review(t, PWR_SPEC)
        hits = [f for f in doc['findings'] if f['check'] == 'class_widths']
        self.assertEqual(len(hits), 1, doc['findings'])
        self.assertEqual(hits[0]['layer'], 'In2.Cu')
        self.assertIn('inner copper not counted', hits[0]['detail'])

    def test_inner_pour_stays_unverified(self):
        t = tree('power_neck.kicad_pcb')
        t.append(['zone', ['net', cb.Q('E1_SHUNT_P')], ['layer', cb.Q('In2.Cu')], ['name', cb.Q('BATT_L3')],
                  ['filled_polygon', ['layer', cb.Q('In2.Cu')], pts_node(rect(6, 7, 34, 13))]])
        doc = review(t, PWR_SPEC)
        self.assertEqual(doc['findings'], [])
        self.assertTrue(any(u['item'] == 'E1_SHUNT_P pour on In2.Cu' for u in doc['unverified']))


class NpthPegTests(unittest.TestCase):
    """PR-05: parts with NPTH locating pegs stay in the height and THT-pocket checks; mounting holes do not."""

    def peg(self, t, local_y):
        footprint(t, 'J1').append(['pad', cb.Q(''), 'np_thru_hole', 'circle', ['at', '0', '%g' % local_y], ['size', '1.2', '1.2'],
                                   ['drill', '1.2'], ['layers', cb.Q('*.Cu'), cb.Q('*.Mask')]])

    def test_tall_part_with_peg_fails_heights(self):
        t = tree('power_neck.kicad_pcb')
        self.peg(t, 1.0)
        doc = review(t, dict(PWR_SPEC, heights={'J1': 20.0}))
        self.assertEqual(checks_failed(doc), ['heights'])
        self.assertEqual(doc['findings'][0]['item'], 'J1')

    def test_peg_outside_pocket_fails(self):
        t = tree('power_neck.kicad_pcb')
        self.peg(t, 3.0)
        doc = review(t, PWR_SPEC)
        self.assertEqual(checks_failed(doc), ['tht_pockets'])
        self.assertEqual(doc['findings'][0]['item'], 'J1.NPTH')
        self.assertEqual(doc['checks']['tht_pockets']['npth_pegs'], 1)

    def test_mounting_holes_are_left_out(self):
        b = cb.Board(tree('power_neck.kicad_pcb'))
        self.assertEqual(cb.mounting_refs(b, PWR_SPEC), {'H1', 'H2', 'H3', 'H4'})
        doc = review(tree('power_neck.kicad_pcb'), PWR_SPEC)
        self.assertEqual(doc['checks']['tht_pockets']['tht_pads'], 2)


class AnnularFloorTests(unittest.TestCase):
    """PR-06: the PTH annular floor follows the copper layer count (JLC 0.15 multilayer, 0.18 two-layer)."""

    def test_two_layer_floor(self):
        t = tree('b2b_a.kicad_pcb')
        pad = next(p for p in cb.kids(footprint(t, 'J1'), 'pad') if p[1] == '1')
        cb.kid(pad, 'size')[1:] = ['1.34', '1.34']  # ring 0.17
        doc = review(t, B2B_SPEC, mates={'FIX_B2B_B': cb.Board(tree('b2b_b.kicad_pcb'))})
        hits = [f for f in doc['findings'] if f['check'] == 'pth_annular']
        self.assertEqual([(f['item'], f['limit']) for f in hits], [('J1.1', NETCLASSES['fab_floor']['jlc_2l_1oz']['pth_annular_min'])])

    def test_four_layer_floor(self):
        t = tree('power_neck.kicad_pcb')
        cb.kid(cb.kid(footprint(t, 'J1'), 'pad'), 'size')[1:] = ['1.64', '1.64']  # ring 0.17 >= 0.15
        doc = review(t, PWR_SPEC)
        self.assertEqual([f for f in doc['findings'] if f['check'] == 'pth_annular'], [])
        self.assertEqual(doc['checks']['pth_annular']['floor_mm'], NETCLASSES['fab_floor']['jlc_4l_1oz']['pth_annular_min'])


class BranchAndTaperTests(unittest.TestCase):
    """PR-07: low-current branches of power nets and RF50 tapers into IC pins."""

    def sense_line(self):
        t = tree('power_neck.kicad_pcb')  # a 0.2 mm Kelvin line from TP1 (E1_N, BATT) to the sense pin of U1
        smd_footprint(t, 'U1', (12, 5), 'E1_N')
        seg(t, (12, 5), (12, 17), 0.2, 'F.Cu', 'E1_N')
        return t

    def test_sense_line_fails_without_exemption(self):
        doc = review(self.sense_line(), dict(PWR_SPEC, board_only_refs={'U1': 'sense amplifier'}))
        self.assertEqual(checks_failed(doc), ['class_widths'])

    def test_branch_exempt_sense_line(self):
        spec = dict(PWR_SPEC, board_only_refs={'U1': 'sense amplifier'},
                    branch_exempt={'U1': {'max_mm': 13.0, 'min_width_mm': 0.15, 'reason': 'Kelvin sense line'}})
        doc = review(self.sense_line(), spec)
        self.assertEqual(doc['findings'], [])
        self.assertTrue(any(u['item'] == 'U1 branch on E1_N' for u in doc['unverified']))
        spec['branch_exempt'] = {'U1': {'max_mm': 5.0, 'min_width_mm': 0.15, 'reason': 'too short'}}
        self.assertEqual(checks_failed(review(self.sense_line(), spec)), ['class_widths'])
        spec['branch_exempt'] = {'U1': {'max_mm': 13.0, 'min_width_mm': 0.25, 'reason': 'too wide a minimum'}}
        self.assertEqual(checks_failed(review(self.sense_line(), spec)), ['class_widths'])

    def test_decoupling_stub_into_a_pour(self):
        t = tree('power_neck.kicad_pcb')  # C9 on the BATT pour edge through a 0.3 mm stub
        smd_footprint(t, 'C9', (20, 15.5), 'E1_SHUNT_P', size=0.8)
        seg(t, (20, 15.5), (20, 12.5), 0.3, 'F.Cu', 'E1_SHUNT_P')
        spec = dict(PWR_SPEC, board_only_refs={'C9': 'decoupling'})
        doc = review(t, spec)
        self.assertEqual(sorted({f['item'] for f in doc['findings']}), ['pour E1_SHUNT_P', 'track E1_SHUNT_P'])
        spec['branch_exempt'] = {'C9': {'max_mm': 3.0, 'min_width_mm': 0.25, 'reason': 'decoupling stub'}}
        self.assertEqual(review(t, spec)['findings'], [])

    def taper(self):
        t = tree('rf_cpwg.kicad_pcb')
        s = next(x for x in cb.kids(t, 'segment') if cb.kid(x, 'net')[1] == 'E4_RTLA_RF1')
        cb.kid(s, 'start')[1] = '112.8'
        seg(t, (12, 10), (12.8, 10), 0.25, 'F.Cu', 'E4_RTLA_RF1')
        return t

    def test_rf50_taper(self):
        self.assertEqual(checks_failed(review(self.taper(), RF_SPEC)), ['rf50'])
        spec = dict(RF_SPEC, rf50_taper={'C1': {'max_len_mm': 1.0, 'min_width_mm': 0.2, 'reason': 'QFN pin'}})
        doc = review(self.taper(), spec)
        self.assertEqual(doc['findings'], [])
        self.assertTrue(any(u['item'] == 'C1 taper on E4_RTLA_RF1' for u in doc['unverified']))
        spec['rf50_taper'] = {'C1': {'max_len_mm': 1.0, 'min_width_mm': 0.3, 'reason': 'min above the taper'}}
        self.assertEqual(checks_failed(review(self.taper(), spec)), ['rf50'])


class ExemptionPolicyTests(unittest.TestCase):
    """W2 PWR-L6-SCRIPT: with exemption_policy, branch_exempt is kept only for test points, resistors of 100 ohm or more and sense
    or logic pins, and a neck only at a pad that is no power-path part, at least that pad's narrow side wide and no longer than
    its long side. MODEL classification from the graph value, footprint and pin names."""
    POLICY = {'why': 'W2 PWR-L6-SCRIPT unit test'}

    def graph(self, ref, value='', pin_name='', other=None):
        g = dict(GRAPH)
        pins = [{'number': '1', 'name': pin_name, 'net': 'E1_N'}]
        if other:
            pins.append({'number': '2', 'name': '', 'net': other})
        g[ref] = {'ref': ref, 'value': value, 'footprint': 'Fixture:PAD_SMD', 'pins': pins}
        g['U90'] = {'ref': 'U90', 'value': 'LM61460', 'footprint': '', 'pins': [{'number': '1', 'name': 'VIN', 'net': 'E1_N'}]}
        return g

    def branch(self, ref, value='', pin_name='', policy=True, other=None):
        t = tree('power_neck.kicad_pcb')  # a 0.2 mm line from TP1 (E1_N, BATT) to the pad of `ref`
        smd_footprint(t, ref, (12, 5), 'E1_N')
        if other:
            x, y = K(12, 3.5)
            fp = cb.kids(t, 'footprint')[-1]
            fp.append(['pad', cb.Q('2'), 'smd', 'rect', ['at', '0', '%g' % (y - K(12, 5)[1])], ['size', '1', '1'],
                       ['layers', cb.Q('F.Cu')], ['net', cb.Q(other)]])
        seg(t, (12, 5), (12, 17), 0.2, 'F.Cu', 'E1_N')
        spec = dict(PWR_SPEC, board_only_refs={ref: 'policy fixture'},
                    branch_exempt={ref: {'max_mm': 13.0, 'min_width_mm': 0.15, 'reason': 'test'}})
        if policy:
            spec['exemption_policy'] = self.POLICY
        return review(t, spec, graph=self.graph(ref, value, pin_name, other))

    def test_allowed_branch_roles(self):
        for ref, value, pin, other in (('U1', 'INA228', 'IN+', None), ('R1', '100k 1%', '', 'E1_SENSE'),
                                       ('C1', '4.7pF', '', 'E1_FF'), ('U2', 'LM61460', 'BIAS', None)):
            doc = self.branch(ref, value, pin, other=other)
            self.assertEqual(doc['findings'], [], ref)
            self.assertIn('exemption_policy', doc['checks']['class_widths'])

    def test_refused_branch_roles(self):
        for ref, value, pin, other, role in (('F1', '4A fuse', '', None, 'fuse'), ('D1', 'SMBJ17A', '', None, 'tvs'),
                                             ('Q1', 'DMT6007', '', None, 'power_switch'), ('R2', '0.22R 1%', '', None, 'shunt'),
                                             ('J3', 'header', '', None, 'connector'), ('U3', 'TPS259470', 'IN', None, 'efuse_in_out'),
                                             ('U4', 'TPS2553', 'OUT', None, 'power_switch'), ('C2', '10uF', '', 'GND', 'converter_capacitor'),
                                             ('R3', '10.0R', '', 'E1_X', 'resistor_lt_100'), ('U5', 'LM61460', 'SW', None, 'converter_power_pin')):
            doc = self.branch(ref, value, pin, other=other)
            hits = [f for f in doc['findings'] if 'exemption_policy' in f['detail']]
            self.assertEqual(len(hits), 1, (ref, doc['findings']))
            self.assertIn(role, hits[0]['detail'])
            self.assertEqual(checks_failed(doc), ['class_widths'])
            self.assertEqual(self.branch(ref, value, pin, policy=False, other=other)['findings'], [], ref)  # without the policy: as before

    def test_branch_exempt_pads(self):
        t = tree('power_neck.kicad_pcb')  # U6: pad 1 BIAS (sense) and pad 2 SW on the same net; only pad 1 is exempted
        smd_footprint(t, 'U6', (12, 5), 'E1_N')
        seg(t, (12, 5), (12, 17), 0.2, 'F.Cu', 'E1_N')
        g = dict(GRAPH, U6={'ref': 'U6', 'value': 'LM61460', 'footprint': '', 'pins': [{'number': '1', 'name': 'BIAS', 'net': 'E1_N'},
                                                                                         {'number': '2', 'name': 'SW', 'net': 'E1_N'}]})
        spec = dict(PWR_SPEC, board_only_refs={'U6': 'policy fixture'}, exemption_policy=self.POLICY,
                    branch_exempt={'U6': {'max_mm': 13.0, 'min_width_mm': 0.15, 'reason': 'BIAS line', 'pads': ['1']}})
        self.assertEqual(review(t, spec, graph=g)['findings'], [])
        spec['branch_exempt']['U6']['pads'] = ['1', '2']
        g['U6']['pins'][0]['name'] = 'SW'
        self.assertEqual(checks_failed(review(t, spec, graph=g)), ['class_widths'])

    def neck(self, ref, value, length, width, size=0.4):
        t = tree('power_neck.kicad_pcb')
        smd_footprint(t, ref, (20, 5), 'E1_N', size=size)
        seg(t, (20, 5), (20, 5 + length), width, 'F.Cu', 'E1_N')
        spec = dict(PWR_SPEC, board_only_refs={ref: 'policy fixture'}, exemption_policy=self.POLICY,
                    neck_exempt={ref: {'escape_mm': length + 0.2, 'reason': 'test'}})
        return review(t, spec, graph=self.graph(ref, value, 'FB'))

    def entry(self, declare=None):
        t = tree('power_neck.kicad_pcb')  # U8: a 0.3 mm pad on E1_N (BATT 3.2), an entry pour (0.75 mm strip, 3.2 mm landing), a track on
        smd_footprint(t, 'U8', (20, 5), 'E1_N', size=0.3)
        outline = [(19.85, 4.85), (20.15, 4.85), (20.15, 5.9), (21.6, 5.9), (21.6, 9.1), (18.4, 9.1), (18.4, 5.9), (19.85, 5.9)]
        t.append(['zone', ['net', cb.Q('E1_N')], ['layer', cb.Q('F.Cu')], ['name', cb.Q('PE-U8')], ['polygon', pts_node(outline)],
                  ['filled_polygon', ['layer', cb.Q('F.Cu')], pts_node(outline)]])
        seg(t, (20, 7.5), (20, 17), 3.2, 'F.Cu', 'E1_N')
        spec = dict(PWR_SPEC, board_only_refs={'U8': 'policy fixture'}, exemption_policy=self.POLICY)
        if declare is not None:
            spec['pin_entry_pours'] = declare
        return review(t, spec, graph=self.graph('U8', 'TPS259470', 'IN'))

    def test_pin_entry_pour(self):
        doc = self.entry()
        self.assertEqual(checks_failed(doc), ['class_widths'])  # the raster sees the strip end as a neck
        self.assertTrue(any(f['item'] == 'pour E1_N' for f in doc['findings']), doc['findings'])
        ok = {'PE-U8': {'pad': 'U8.1', 'strip_mm': 0.75, 'landing_mm': [3.2, 3.2]}}
        doc = self.entry(ok)
        self.assertEqual(doc['findings'], [])
        self.assertEqual(doc['checks']['class_widths']['exemption_policy']['pin_entry_pours'], {'declared': 1, 'accepted': 1})
        for bad in ({'PE-U8': {'pad': 'U8.1', 'strip_mm': 1.7, 'landing_mm': [3.2, 3.2]}},
                    {'PE-U8': {'pad': 'U8.1', 'strip_mm': 0.75, 'landing_mm': [3.2, 2.0]}},
                    {'PE-XX': {'pad': 'U8.1', 'strip_mm': 0.75, 'landing_mm': [3.2, 3.2]}}):
            doc = self.entry(bad)
            self.assertTrue(any(f['item'].startswith('pin entry') for f in doc['findings']), (bad, doc['findings']))

    def test_neck_rule(self):
        self.assertEqual(self.neck('U7', 'LM61460', 0.3, 0.4)['findings'], [])            # at pad width, within the pad length
        for ref, value, length, width, why in (('U7', 'LM61460', 1.0, 0.4, 'pin stem'), ('U7', 'LM61460', 0.3, 0.3, 'narrower than the pad'),
                                               ('F7', 'fuse', 0.3, 0.4, 'no neck on a fuse'), ('D7', 'SMBJ17A', 0.3, 0.4, 'no neck on a tvs'),
                                               ('Q7', 'FET', 0.3, 0.4, 'no neck on a power switch')):
            doc = self.neck(ref, value, length, width)
            self.assertEqual(checks_failed(doc), ['class_widths'], ref)
            self.assertTrue(any(why in f['detail'] for f in doc['findings']), (ref, doc['findings']))


class AdvisoryViaTests(unittest.TestCase):
    """PR-09: vias_per_transition is advisory and listed, not silently implied."""

    def test_split_net_vias_listed(self):
        doc = review(tree('power_neck.kicad_pcb'), PWR_SPEC)
        notes = [u for u in doc['unverified'] if u['item'] == 'E1_SHUNT_P vias']
        self.assertEqual(len(notes), 1)
        self.assertIn('advisory', notes[0]['reason'])


class ContractProjectionTests(unittest.TestCase):
    """PR-10: the contract hash covers only the keys the checker reads."""

    def test_unread_contract_keys_keep_the_hash(self):
        b = cb.Board(tree('power_neck.kicad_pcb'))
        views = cb.expected_views(PWR_SPEC, GRAPH)
        cbd = CONTRACT['boards']['FIX_PWR']
        base = cb.projections(b, PWR_SPEC, cbd, GRAPH, views, NETCLASSES)['contract_board']
        more = dict(cbd, placements={'U1': [1, 2]}, mount={'standoff': 'M3'}, dxf='x.dxf')
        self.assertEqual(cb.projections(b, PWR_SPEC, more, GRAPH, views, NETCLASSES)['contract_board'], base)
        moved = dict(cbd, holes_mm=[[4, 4], [36, 4], [4, 16], [36, 15]])
        self.assertNotEqual(cb.projections(b, PWR_SPEC, moved, GRAPH, views, NETCLASSES)['contract_board'], base)


class PadGeometryTests(unittest.TestCase):
    """PR-11: a pad without an angle is at absolute 0 deg; custom pads use their primitives."""

    def board_with(self, pad):
        return cb.Board(cb.parse('(kicad_pcb (layers (0 "F.Cu" signal) (2 "B.Cu" signal)) (footprint "X:Y" (layer "F.Cu") (at 10 10 90)'
                                 ' (property "Reference" "U1") ' + pad + '))'))

    def test_missing_pad_angle_is_absolute_zero(self):
        b = self.board_with('(pad "1" smd rect (at 0 0) (size 4 1) (layers "F.Cu") (net "N"))')
        x0, y0, x1, y1 = b.pads[0]['geo'].bbox
        self.assertAlmostEqual(x1 - x0, 4.0, places=6)
        self.assertAlmostEqual(y1 - y0, 1.0, places=6)
        b90 = self.board_with('(pad "1" smd rect (at 0 0 90) (size 4 1) (layers "F.Cu") (net "N"))')
        x0, y0, x1, y1 = b90.pads[0]['geo'].bbox
        self.assertAlmostEqual(y1 - y0, 4.0, places=6)

    def test_custom_pad_primitives(self):
        b = self.board_with('(pad "1" smd custom (at 0 0) (size 1 1) (layers "F.Cu") (net "N") (options (clearance outline) (anchor rect))'
                            ' (primitives (gr_poly (pts (xy 0 0) (xy 3 0) (xy 3 1) (xy 0 1)) (width 0) (fill yes))))')
        geo = b.pads[0]['geo']
        self.assertTrue(geo.contains(12.5, 10.5))
        self.assertFalse(geo.contains(10, 12.5))
        self.assertEqual([u['check'] for u in b.unverified], ['geometry'])


class CouponTests(unittest.TestCase):
    """W2 PCB-RF-2: spec coupons (a test coupon drawn beside the board in the same file)."""
    SPEC = dict(RF_SPEC, contract_transform={'origin': [OX, OY], 'y': 'up'})

    def with_coupon(self, width='0.36'):
        t = tree('rf_cpwg.kicad_pcb')
        loop = rect(0, -12, 30, -4)
        for a, b in zip(loop, loop[1:] + loop[:1]):
            (x0, y0), (x1, y1) = K(*a), K(*b)
            t.append(['gr_line', ['start', '%g' % x0, '%g' % y0], ['end', '%g' % x1, '%g' % y1],
                      ['stroke', ['width', '0.05'], ['type', 'solid']], ['layer', cb.Q('Edge.Cuts')]])
        (x0, y0), (x1, y1) = K(5, -8), K(25, -8)
        t.append(['segment', ['start', '%g' % x0, '%g' % y0], ['end', '%g' % x1, '%g' % y1], ['width', width],
                  ['layer', cb.Q('F.Cu')], ['net', cb.Q('CPN_X')]])
        return t

    def test_coupon_loop_needs_the_spec_coupon(self):
        t = self.with_coupon()
        self.assertIn('outline', checks_failed(review(t, self.SPEC)))
        doc = review(t, dict(self.SPEC, coupons=[{'rect': [0, -12, 30, 8], 'reason': 'test'}]))
        self.assertNotIn('outline', checks_failed(doc))
        self.assertEqual(doc['checks']['outline']['coupon_loops'], 1)
        self.assertNotIn('coupon_loops', review(tree('rf_cpwg.kicad_pcb'), RF_SPEC)['checks']['outline'])

    def test_coupon_rf50_nets_are_checked(self):
        spec = dict(self.SPEC, coupons=[{'rect': [0, -12, 30, 8], 'rf50_nets': ['CPN_X'], 'reason': 'test'}])
        doc = review(self.with_coupon('0.3'), spec)
        self.assertTrue(any(f['check'] == 'rf50' and f['item'] == 'CPN_X' and 'width' in f['detail'] for f in doc['findings']))
        plain = review(self.with_coupon('0.3'), dict(self.SPEC, coupons=[{'rect': [0, -12, 30, 8], 'reason': 'test'}]))
        self.assertFalse(any(f['item'] == 'CPN_X' for f in plain['findings']))


class RfNodeChecks(unittest.TestCase):
    """W2 PCB-RF-2: the GND-CHASSIS tie on the bond hole and the optional rf_checks (taps, tap capacitors, keepout, SENSE)."""

    def rf_review(self, t, rf_checks, components_csv=None):
        return cb.review_board(cb.Board(t), dict(RF_SPEC, rf_checks=rf_checks), CONTRACT, GRAPH, NETCLASSES,
                               components_csv=components_csv)

    def test_tie_must_reach_the_bond_hole(self):
        doc = review(tree('rf_cpwg.kicad_pcb'), RF_SPEC)
        self.assertEqual(doc['checks']['gnd_chassis_ties']['ties_on_bond_hole'], ['NT1'])
        t = tree('rf_cpwg.kicad_pcb')
        t[:] = [n for n in t if not (isinstance(n, list) and n and n[0] == 'segment' and cb.kid(n, 'net')[1] == 'CHASSIS')]
        doc = review(t, RF_SPEC)
        self.assertEqual(checks_failed(doc), ['gnd_chassis_ties'])
        self.assertEqual([f['item'] for f in doc['findings']], ['NT1'])
        self.assertEqual(doc['checks']['gnd_chassis_ties']['bond_net_islands'], 2)
        self.assertNotIn('ties_on_bond_hole', review(tree('power_neck.kicad_pcb'), PWR_SPEC)['checks']['gnd_chassis_ties'])

    def test_taps_on_their_rf50_line(self):
        rc = {'taps': [{'ref': 'C1', 'pad': '1', 'max_mm': 2.0}]}
        doc = self.rf_review(tree('rf_cpwg.kicad_pcb'), rc)
        self.assertEqual(doc['findings'], [])
        self.assertEqual(doc['checks']['rf_nodes']['taps']['C1.1']['to_rf50_line_mm'], 0.0)
        t = tree('rf_cpwg.kicad_pcb')
        cb.kid(footprint(t, 'C1'), 'at')[2] = '%g' % (float(cb.kid(footprint(t, 'C1'), 'at')[2]) - 3)  # 3 mm off the line
        doc = self.rf_review(t, rc)
        f = next(f for f in doc['findings'] if f['check'] == 'rf_nodes')
        self.assertEqual(f['item'], 'C1.1')
        self.assertAlmostEqual(f['value'], 3 - 0.3 - 0.18, places=3)
        doc = self.rf_review(tree('rf_cpwg.kicad_pcb'), {'taps': [{'ref': 'NT1', 'pad': '1', 'max_mm': 2.0}]})
        self.assertTrue(any(f['item'] == 'NT1.1' and 'not an RF50 line' in f['detail'] for f in doc['findings']))

    def test_tap_capacitor_next_to_the_tap(self):
        near = self.rf_review(tree('rf_cpwg.kicad_pcb'), {'tap_caps': [{'ref': 'C2', 'to': ['C1', '1'], 'max_mm': 40.0}]})
        self.assertEqual(near['findings'], [])
        self.assertAlmostEqual(near['checks']['rf_nodes']['tap_caps']['C2 to C1.1']['pad_gap_mm'], 35.4, places=3)
        far = self.rf_review(tree('rf_cpwg.kicad_pcb'), {'tap_caps': [{'ref': 'C2', 'to': ['C1', '1'], 'max_mm': 2.0}]})
        self.assertEqual(checks_failed(far), ['rf_nodes'])
        other = self.rf_review(tree('rf_cpwg.kicad_pcb'), {'tap_caps': [{'ref': 'NT1', 'to': ['C1', '1'], 'max_mm': 2.0}]})
        self.assertTrue(any('no pad of this part' in f['detail'] for f in other['findings']))

    def test_parts_outside_the_domain_keepout(self):
        rows = [{'ref': 'C2', 'board_candidate': 'DC_CORE', 'category': 'bare_board_part'}]
        ok = self.rf_review(tree('rf_cpwg.kicad_pcb'), {'keepout': {'domains': ['DC_CORE'], 'margin_mm': 5.0, 'refs': ['C1']}}, rows)
        self.assertEqual(ok['findings'], [])
        self.assertAlmostEqual(ok['checks']['rf_nodes']['keepout']['min_clearance_mm'], 36 - 1 - 5.0, places=3)
        bad = self.rf_review(tree('rf_cpwg.kicad_pcb'), {'keepout': {'domains': ['DC_CORE'], 'margin_mm': 40.0, 'refs': ['C1']}}, rows)
        self.assertEqual([f['item'] for f in bad['findings']], ['C1'])
        none = self.rf_review(tree('rf_cpwg.kicad_pcb'), {'keepout': {'domains': ['NOPE'], 'margin_mm': 5.0, 'refs': ['C1']}}, rows)
        self.assertEqual([f['item'] for f in none['findings']], ['keepout'])

    def test_sense_length_against_the_prototype(self):
        with tempfile.TemporaryDirectory() as d:
            proto = Path(d) / 'proto.json'

            def run(length):
                proto.write_text(json.dumps({'routing': [{'net': 'E4_RTLA_RF1', 'length_mm': length}]}), encoding='utf-8')
                return self.rf_review(tree('rf_cpwg.kicad_pcb'), {'sense': {'nets': ['E4_RTLA_RF1'], 'prototype': proto.as_posix()}})
            ok = run(40.0)
            self.assertEqual(ok['findings'], [])
            self.assertEqual(ok['checks']['rf_nodes']['sense']['nets']['E4_RTLA_RF1'], {'board_mm': 36.0, 'prototype_mm': 40.0})
            self.assertEqual(checks_failed(run(30.0)), ['rf_nodes'])
            proto.write_text(json.dumps({'routing': []}), encoding='utf-8')
            doc = self.rf_review(tree('rf_cpwg.kicad_pcb'), {'sense': {'nets': ['E4_RTLA_RF1'], 'prototype': proto.as_posix()}})
            self.assertTrue(any('not in the prototype routing' in f['detail'] for f in doc['findings']))

    def test_bad_rf_checks_are_refused(self):
        for bad in ({'nope': 1}, {'taps': [{'ref': 'C1', 'pad': '1'}]}, {'tap_caps': [{'ref': 'C1', 'to': 'C2', 'max_mm': 1}]},
                    {'keepout': {'domains': [], 'margin_mm': 1, 'refs': []}}, {'sense': {'nets': ['X']}}):
            with self.assertRaises(SystemExit, msg=bad):
                self.rf_review(tree('rf_cpwg.kicad_pcb'), bad)
        with self.assertRaises(SystemExit):
            cb.normalize_spec(dict(RF_SPEC, rf_checks=[]))

    def test_committed_rf_board(self):
        spec_path, board_path = ROOT / 'pcb/boards/RF.json', ROOT / 'build/kicad/boards/RF/RF.kicad_pcb'
        if not spec_path.is_file() or not board_path.is_file():
            self.skipTest('no RF board yet')
        spec = cb.normalize_spec(json.loads(spec_path.read_text(encoding='utf-8')))
        if 'rf_checks' not in spec:
            self.skipTest('RF spec without rf_checks')
        doc = cb.review_board(cb.load_board(board_path), spec, json.loads(cb.CONTRACT.read_text(encoding='utf-8')),
                              cb.load_graph(), NETCLASSES)
        self.assertEqual(doc['checks']['rf_nodes']['findings'], 0)
        self.assertEqual(doc['checks']['gnd_chassis_ties']['ties_on_bond_hole'], ['NT401'])
        self.assertEqual(len(doc['checks']['rf_nodes']['taps']), 3)


if __name__ == '__main__':
    unittest.main()
