"""pcb/stackup.py: calculators, generated net classes and the JLC DRC rule files (stdlib only).

Run: python -m unittest discover -s pcb/tests  (from sat-receiver-audit/)
"""
import ast
import importlib.util
import json
import re
import unittest
from pathlib import Path

PCB = Path(__file__).resolve().parents[1]
ROOT = PCB.parent
_spec = importlib.util.spec_from_file_location('srrx_stackup', PCB / 'stackup.py')
stackup = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stackup)


def load_doc():
    return json.loads((PCB / 'generated/netclasses.json').read_text(encoding='utf-8'))


class CalculatorTests(unittest.TestCase):
    def test_cbcpw_reference_case(self):
        # Plan acceptance: 51.2 ohm (+/-0.1) for w 0.36 / s 0.20 / h 0.2104 / er 4.4 (closed form, t = 0).
        z0, eps = stackup.cbcpw(0.36, 0.20, 0.2104, 4.4)
        self.assertAlmostEqual(z0, 51.2, delta=0.1)
        self.assertGreater(eps, 1.0)
        self.assertLess(eps, 4.4)

    def test_cbcpw_trends(self):
        base = stackup.cbcpw(0.36, 0.20, 0.2104, 4.4)[0]
        self.assertLess(stackup.cbcpw(0.40, 0.20, 0.2104, 4.4)[0], base)   # wider strip -> lower Z
        self.assertGreater(stackup.cbcpw(0.36, 0.30, 0.2104, 4.4)[0], base)  # wider gap -> higher Z
        self.assertLess(stackup.cbcpw(0.36, 0.20, 0.2104, 4.6)[0], base)   # higher er -> lower Z
        self.assertGreater(stackup.cbcpw(0.36, 0.20, 0.25, 4.4)[0], base)  # thicker dielectric -> higher Z

    def test_ellipk_known_values(self):
        self.assertAlmostEqual(stackup.ellipk(0.0), 1.5707963267948966, places=12)
        self.assertAlmostEqual(stackup.ellipk(0.5 ** 0.5), 1.8540746773013719, places=10)

    def test_ipc2221_reference_widths(self):
        # Plan acceptance: 2.46 mm (4.6 A, dT 10, 1 oz external) and 3.17 mm (7.5 A, dT 20).
        self.assertAlmostEqual(stackup.ipc2221_width_mm(4.6, 10), 2.46, delta=0.01)
        self.assertAlmostEqual(stackup.ipc2221_width_mm(7.5, 20), 3.17, delta=0.01)

    def test_ipc2221_internal_needs_more_copper(self):
        ext = stackup.ipc2221_width_mm(1.0, 10)
        inner = stackup.ipc2221_width_mm(1.0, 10, stackup.INNER_CU, 'internal')
        self.assertGreater(inner, 2 * ext)
        self.assertEqual(stackup.ipc2221_width_mm(0, 10), 0.0)

    def test_ipc2221_roundtrip(self):
        area = stackup.ipc2221_area_mil2(3.0, 10)
        self.assertAlmostEqual(stackup.ipc2221_current(area, 10), 3.0, places=9)

    def test_via_current_uses_jlc_plating(self):
        plating = stackup.CAPS['hole_wall_plating_mm'][0]
        self.assertEqual(plating, 0.018)
        i10 = stackup.via_current(0.3, plating, 10)
        self.assertGreater(stackup.via_current(0.3, plating, 20), i10)
        self.assertGreater(stackup.via_current(0.4, plating, 10), i10)

    def test_round_up(self):
        self.assertEqual(stackup.up(3.1766), 3.2)
        self.assertEqual(stackup.up(1.85), 1.85)
        self.assertEqual(stackup.up(0.3004), 0.35)

    def test_value_parsers(self):
        self.assertEqual(stackup.ohms('15 mΩ 1% 2 W (Adafruit R1)'), 0.015)
        self.assertEqual(stackup.ohms('WSL2512R3300FEA 0.330 Ω 1%'), 0.33)
        self.assertEqual(stackup.ohms('0.22R 1% 0.25W'), 0.22)
        self.assertEqual(stackup.ohms('20mR 1% 0.25W'), 0.02)
        self.assertEqual(stackup.ohms('10.0R 1%'), 10.0)
        self.assertIsNone(stackup.ohms('4.7k 1%'))
        self.assertEqual(stackup.rating_a('Mini-blade 7.5 A DC ≥32 V'), 7.5)
        self.assertEqual(stackup.rating_a('Littelfuse0297004.WXNV 4A'), 4.0)
        self.assertEqual(stackup.rating_a('MF-MSMF075/24-2 0.75A'), 0.75)


class GeneratedOutputTests(unittest.TestCase):
    def test_outputs_reproduce(self):
        for path, text in stackup.outputs().items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.read_text(encoding='utf-8'), text, f'{path} is stale: rerun python pcb/stackup.py')

    def test_every_net_current_entry_is_listed_with_line_and_inputs(self):
        doc = load_doc()
        text = (ROOT / 'tools/assembly_data.py').read_text(encoding='utf-8')
        lines = text.splitlines()
        tree = ast.parse(text)
        entries = [n for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'NET_CURRENT'][0]
        keys = [ast.literal_eval(k) for k in entries.value.keys]
        self.assertGreater(len(keys), 20)
        for net in keys:
            entry = doc['nets'][net]
            self.assertIn(entry['class'], doc['classes'])
            path, line = entry['source'].rsplit(':', 1)
            self.assertEqual(path, 'tools/assembly_data.py')
            self.assertIn(f'"{net}"', lines[int(line) - 1], net)
            for key in ('continuous_a', 'protective_a', 'protection', 'current_source'):
                self.assertIn(key, entry['inputs'], net)
            self.assertIn('required_outer_width_mm', entry)

    def test_class_widths_cover_member_requirements(self):
        doc = load_doc()
        for net, entry in doc['nets'].items():
            cls = doc['classes'][entry['class']]
            if entry['class'] in stackup.POWER_CLASSES:
                self.assertLessEqual(entry['required_outer_width_mm'], cls['outer_min_width_mm'] + 1e-9, net)
            if entry['class'] == 'RF50' and 'required_outer_width_mm' in entry:
                self.assertLessEqual(entry['required_outer_width_mm'], cls['width_mm'], net)

    def test_battery_path_is_batt(self):
        doc = load_doc()
        for net in ('E1_SHUNT_P', 'E1_N', 'E1_SW', 'E1_CELL4'):
            self.assertEqual(doc['nets'][net]['class'], 'BATT', net)
        batt = doc['classes']['BATT']
        self.assertEqual(batt['outer_min_width_mm'], 3.2)
        self.assertGreaterEqual(batt['split_outer_per_layer_mm'], 1.8)

    def test_dctap_clearance_is_tbd_with_project_rule(self):
        dctap = load_doc()['classes']['DCTAP']
        self.assertEqual(dctap['clearance_mm'], 'TBD')
        self.assertIn('not IPC-verified', dctap['project_rule_note'])
        self.assertIn('TBD', dctap['clearance_ipc'])

    def test_rf50_model_values(self):
        rf = load_doc()['classes']['RF50']
        self.assertAlmostEqual(rf['model']['z0_ohm'], 51.2, delta=0.1)
        self.assertAlmostEqual(rf['l2_solid_band_mm'], 0.18 + 3 * 0.2104, places=4)
        self.assertIn('MODEL', rf['model']['method'])

    def test_status_is_model(self):
        doc = load_doc()
        self.assertTrue(doc['status'].startswith('MODEL'))
        self.assertNotIn('PASS', json.dumps(doc, ensure_ascii=False).replace('pass', ''))


RULE = re.compile(r'\(rule\s+"([^"]+)"')
VALUE = re.compile(r'\((min|opt|max)\s+([0-9.]+)mm\)')
KNOWN_CONSTRAINTS = {'annular_width', 'assertion', 'bridged_mask', 'clearance', 'connection_width', 'courtyard_clearance',
                     'creepage', 'diff_pair_gap', 'diff_pair_uncoupled', 'disallow', 'edge_clearance', 'hole_clearance',
                     'hole_size', 'hole_to_hole', 'length', 'min_resolved_spokes', 'physical_clearance',
                     'physical_hole_clearance', 'silk_clearance', 'skew', 'solder_mask_expansion', 'solder_paste_abs_margin',
                     'solder_paste_rel_margin', 'text_height', 'text_thickness', 'thermal_relief_gap', 'thermal_spoke_width',
                     'track_angle', 'track_segment_length', 'track_width', 'via_count', 'via_dangling', 'via_diameter',
                     'zone_connection'}  # KiCad 10.0.7 panel_setup_rules_help_2constraints.md


def strip_comments(text):
    return '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('#'))


class RuleFileTests(unittest.TestCase):
    FILES = {'4l': PCB / 'rules/jlc-4l-1oz.kicad_dru', '2l': PCB / 'rules/jlc-2l.kicad_dru'}

    def test_syntax_subset(self):
        for kind, path in self.FILES.items():
            text = strip_comments(path.read_text(encoding='utf-8'))
            self.assertTrue(text.startswith('(version 1)'), path)
            depth = 0
            in_str = False
            for ch in text:
                if ch == '"':
                    in_str = not in_str
                elif not in_str:
                    depth += ch == '('
                    depth -= ch == ')'
                    self.assertGreaterEqual(depth, 0, path)
            self.assertEqual(depth, 0, path)
            self.assertFalse(in_str, path)
            for name in re.findall(r'\(constraint\s+([a-z_]+)', text):
                self.assertIn(name, KNOWN_CONSTRAINTS, (path, name))
            for layer in re.findall(r'\(layer\s+([^)]+)\)', text):
                self.assertIn(layer.strip(), {'outer', 'inner', '"F.Cu"', '"B.Cu"'}, (path, layer))
            names = RULE.findall(text)
            self.assertEqual(len(names), len(set(names)), path)

    def test_every_rule_value_cites_url_and_date_and_meets_the_jlc_floor(self):
        doc = load_doc()
        for kind, path in self.FILES.items():
            text = path.read_text(encoding='utf-8')
            header = '\n'.join(text.splitlines()[:6])
            self.assertIn(stackup.URL_CAPS, header)
            self.assertIn(stackup.READ, header)
            floor = doc['fab_floor']['jlc_4l_1oz' if kind == '4l' else 'jlc_2l_1oz']
            chunks = re.findall(r'((?:#[^\n]*\n)*)\(rule "([^"]+)"(.*?)\n\)', text, re.S)
            self.assertTrue(chunks)
            for comments, name, body in chunks:
                vals = [float(v) for _kind, v in VALUE.findall(body)]
                if not vals:
                    continue
                if name.startswith(('project', 'JLC')):
                    self.assertIn('jlcpcb.com', comments, name)
                    self.assertIn(stackup.READ, comments, name)
                m = {c: [float(v) for v in re.findall(r'\(min ([0-9.]+)mm\)', seg)] for c, seg in re.findall(r'\(constraint ([a-z_]+)(.*?)\)\s*(?=\(constraint|\(condition|$)', body + '\n', re.S)}
                checks = {'clearance': floor['track_spacing_min'], 'track_width': floor['track_width_min'],
                          'via_diameter': floor['via_diameter_min'], 'edge_clearance': floor['copper_to_routed_edge_min'],
                          'hole_to_hole': floor['via_hole_to_hole_min'], 'text_height': floor['silk_text_height_min'],
                          'text_thickness': floor['silk_line_min']}
                for cons, mins in m.items():
                    for v in mins:
                        if cons in checks:
                            self.assertGreaterEqual(v + 1e-9, checks[cons], (path.name, name, cons, v))
                        if cons == 'hole_size' and 'Via' in body:
                            self.assertGreaterEqual(v, floor['via_hole_min'], (path.name, name))
                        if cons == 'hole_size' and 'NPTH' in body:
                            self.assertGreaterEqual(v, floor['npth_hole_min'], (path.name, name))
                        if cons == 'hole_clearance' and "'Via'" in body:
                            self.assertGreaterEqual(v, floor['via_hole_to_track_min'], (path.name, name))
                        if cons == 'hole_clearance' and 'isPlated' in body:
                            self.assertGreaterEqual(v, floor['pth_to_track_min'], (path.name, name))
                        if cons == 'hole_clearance' and 'NPTH' in body:
                            self.assertGreaterEqual(v, floor['npth_to_track_min'], (path.name, name))

    def test_hole_to_hole_meets_pad_floor(self):
        doc = load_doc()
        for kind, path in self.FILES.items():
            text = path.read_text(encoding='utf-8')
            v = float(re.search(r'hole_to_hole \(min ([0-9.]+)mm\)', text)[1])
            self.assertGreaterEqual(v, doc['fab_floor']['jlc_4l_1oz']['pad_hole_to_hole_min'])

    def test_keepouts_match_contract(self):
        contract = json.loads((ROOT / 'mechanical/generated/contract/boards.json').read_text(encoding='utf-8'))
        text = self.FILES['4l'].read_text(encoding='utf-8')
        for board in contract['boards'].values():
            want = (board['hole_keepout_d'] - board['hole_d']) / 2
            m = re.search(r'\(rule "mounting hole %s keepout"\n  \(constraint hole_clearance \(min ([0-9.]+)mm\)\)' % board['hole_d'], text)
            self.assertIsNotNone(m, board['hole_d'])
            self.assertAlmostEqual(float(m[1]), want, places=6)

    def test_rf_and_dctap_only_in_4l(self):
        self.assertIn('RF50', self.FILES['4l'].read_text(encoding='utf-8'))
        self.assertIn('DCTAP', self.FILES['4l'].read_text(encoding='utf-8'))
        two = self.FILES['2l'].read_text(encoding='utf-8')
        self.assertNotIn("hasNetclass('RF50')", two)
        self.assertNotIn('(layer inner)', two)

    def test_dctap_rule_labelled_project_choice(self):
        text = self.FILES['4l'].read_text(encoding='utf-8')
        self.assertIn('project choice, not IPC-verified', text)


if __name__ == '__main__':
    unittest.main()
