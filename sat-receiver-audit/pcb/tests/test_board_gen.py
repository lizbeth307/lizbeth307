"""Standard-library tests of pcb/board_gen.py (no KiCad needed).

Run from sat-receiver-audit: python3 -m unittest discover -s pcb/tests
The KiCad side (placement, Freerouting, DRC) runs only in .github/workflows/sr-rx-pcb.yml.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import board_gen as bg  # noqa: E402

PEC11R = bg.BASE / 'build/kicad/footprints/SR_RX_Custom.pretty/RotaryEncoder_Bourns_PEC11R-4xxxF-Sxxxx.kicad_mod'


def synthetic():
    """A two-instance spec, graph and manifest that do not depend on the repository data."""
    graph = {
        'U1': {'ref': 'U1', 'value': 'IC', 'kind': 'ic', 'footprint': 'L:FP2', '_sheet': 'E9',
               'pins': [{'number': '1', 'net': 'A_SIG'}, {'number': '2', 'net': 'GND'}]},
        'U2': {'ref': 'U2', 'value': 'IC', 'kind': 'ic', 'footprint': 'L:FP2', '_sheet': 'E9',
               'pins': [{'number': '1', 'net': 'B_SIG'}, {'number': '2', 'net': 'GND'}]},
        'R9': {'ref': 'R9', 'value': 'R', 'kind': 'resistor', 'footprint': 'L:FP2', '_sheet': 'E9',
               'pins': [{'number': '1', 'net': 'A_SIG'}, {'number': '2', 'net': 'B_SIG'}]},
    }
    manifest = {'footprints': [{'footprint': 'L:FP2', 'file': 'x.kicad_mod', 'sha256': '0' * 64, 'pads': ['1', '2', 'MP']}]}
    spec = {
        'board_id': 'T', 'domains': ['T'],
        'instances': {'template_nets': ['GND', 'SIG'], 'spares': 1, 'list': [
            {'id': 'I1', 'qty': 1, 'refs': {'U': 'U1', 'J': None}, 'nets': {'SIG': 'A_SIG', 'GND': 'GND'}},
            {'id': 'I2', 'qty': 1, 'refs': {'U': 'U2', 'J': None}, 'nets': {'SIG': 'B_SIG', 'GND': 'GND'}}]},
        'parts': [
            {'ref': 'U', 'source': 'graph', 'anchor': {'at': [1, 1]}},
            {'ref': 'J', 'source': 'pilot_placeholder', 'footprint': 'L:J2', 'footprint_library': 'kicad-image',
             'footprint_sha256': '1' * 64, 'value': 'J', 'pins': {'1': 'GND', '2': 'SIG'}, 'replaced_by': 'later',
             'anchor': {'at': [0, 0]}}],
    }
    return spec, graph, manifest


class TemplateResolution(unittest.TestCase):
    def test_two_instances_share_one_neutral_template(self):
        spec, graph, manifest = synthetic()
        template = bg.resolve(spec, graph, manifest)
        u = next(t for t in template if t['ref'] == 'U')
        self.assertEqual(u['pads'], {'1': 'SIG', '2': 'GND'})
        self.assertEqual(u['unused_pads'], ['MP'])

    def test_instances_that_differ_are_refused(self):
        spec, graph, manifest = synthetic()
        graph['U2']['pins'][1]['net'] = 'B_SIG'  # pin 2 of the second instance on SIG instead of GND
        with self.assertRaises(SystemExit):
            bg.resolve(spec, graph, manifest)

    def test_unmapped_graph_net_is_refused(self):
        spec, graph, manifest = synthetic()
        graph['U1']['pins'][0]['net'] = 'OTHER'
        with self.assertRaises(SystemExit):
            bg.resolve(spec, graph, manifest)

    def test_boundary_marks_placeholder_ends_provisional(self):
        spec, graph, manifest = synthetic()
        template = bg.resolve(spec, graph, manifest)
        rows = bg.boundary_audit(spec, template, graph, {})
        self.assertEqual({r['status'] for r in rows}, {'provisional: header ref pending GR-3'})
        sig = next(n for n in rows[0]['nets'] if n['net'] == 'SIG')
        self.assertEqual(sig['external_sample'], ['R9'])

    def test_boundary_dangling_without_any_board_pin(self):
        spec, graph, manifest = synthetic()
        spec['parts'][1]['pins'] = {'1': 'GND'}  # SIG (on U.1, also on R9 elsewhere) no longer leaves the board
        template = bg.resolve(spec, graph, manifest)
        rows = bg.boundary_audit(spec, template, graph, {})
        sig = next(n for n in rows[0]['nets'] if n['net'] == 'SIG')
        self.assertEqual(sig['status'], 'dangling')
        self.assertEqual(rows[0]['status'], 'fail: dangling SIG')

    def test_projection_follows_graph_pins_not_whole_files(self):
        spec, graph, manifest = synthetic()
        template = bg.resolve(spec, graph, manifest)
        a = bg.projection(spec, {'outline_mm': [[0, 0]]}, {}, template, graph, b'{}')
        graph['R9']['value'] = 'R changed'  # not on this board
        b = bg.projection(spec, {'outline_mm': [[0, 0]]}, {}, template, graph, b'{}')
        self.assertEqual(a['sha256'], b['sha256'])
        graph['U1']['value'] = graph['U2']['value'] = 'IC changed'
        c = bg.projection(spec, {'outline_mm': [[0, 0]]}, {}, bg.resolve(spec, graph, manifest), graph, b'{}')
        self.assertNotEqual(a['parts']['instances'], c['parts']['instances'])


class SourcePadAudit(unittest.TestCase):
    def facts(self, u_pads, j_pads):
        def fp(ref, fpid, pads):
            return {'ref': ref, 'fpid': fpid, 'value': 'IC' if ref == 'U' else 'J',
                    'pads': [{'number': n, 'net': net} for n, net in pads]}
        return {'footprints': [fp('U', 'L:FP2', u_pads), fp('J', 'L:J2', j_pads)]}

    def test_clean_board_has_no_errors_per_instance(self):
        spec, graph, manifest = synthetic()
        template = bg.resolve(spec, graph, manifest)
        facts = self.facts([('1', 'SIG'), ('2', 'GND'), ('MP', None)], [('1', 'GND'), ('2', 'SIG')])
        rows = bg.source_pad_audit(facts, spec, template, graph)
        self.assertEqual([r['errors'] for r in rows], [[], []])

    def test_wrong_and_extra_nets_are_errors(self):
        spec, graph, manifest = synthetic()
        template = bg.resolve(spec, graph, manifest)
        facts = self.facts([('1', 'GND'), ('2', 'GND'), ('MP', 'GND')], [('1', 'GND'), ('2', 'SIG')])
        kinds = sorted(e['kind'] for e in bg.source_pad_audit(facts, spec, template, graph)[0]['errors'])
        self.assertEqual(kinds, ['extra_netted_pad', 'pad_net'])


class Placement(unittest.TestCase):
    def test_shelf_pack_is_deterministic_and_inside_region(self):
        items = [{'ref': f'C{i}', 'w': 1.6 + (i % 3) * 0.5, 'h': 0.9 + (i % 2)} for i in range(1, 13)]
        a = bg.shelf_pack(items, [0, 0, 10, 10])
        b = bg.shelf_pack(list(reversed(items)), [0, 0, 10, 10])
        self.assertEqual(a, b)
        size = {i['ref']: (i['w'], i['h']) for i in items}
        rects = []
        for ref, (cx, cy) in a.items():
            w, h = size[ref]
            r = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]
            self.assertTrue(r[0] >= -1e-9 and r[1] >= -1e-9 and r[2] <= 10 + 1e-9 and r[3] <= 10 + 1e-9, (ref, r))
            self.assertFalse(any(bg.rects_overlap(r, o) for o in rects), ref)
            rects.append(r)

    def test_shelf_pack_reports_a_full_region(self):
        with self.assertRaises(SystemExit):
            bg.shelf_pack([{'ref': f'R{i}', 'w': 3, 'h': 3} for i in range(10)], [0, 0, 6, 6])

    def test_decoupling_lands_within_two_mm_of_its_pin(self):
        body = [0, 0, 5, 5]
        (cx, cy), dist = bg.place_near((1.0, 0.5), (5.0, 2.0), body, [body], [-10, -10, 20, 20], 2.0)
        self.assertLessEqual(dist, 2.0)
        self.assertGreater(cx - 0.5, 5.0)  # outside the IC body, on the pin's side
        self.assertEqual(cy, 2.0)

    def test_decoupling_without_room_fails(self):
        body = [0, 0, 5, 5]
        blocked = [[5.1, -10, 9, 10], [-9, -10, -0.1, 10], [-10, 5.1, 20, 9], [-10, -9, 20, -0.1]]
        with self.assertRaises(SystemExit):
            bg.place_near((1.0, 0.5), (5.0, 2.0), body, [body] + blocked, [-10, -10, 20, 20], 2.0)

    def test_rotate_box_matches_kicad_rotation(self):
        # KiCad RotatePoint(+90): (x, y) -> (y, -x)
        self.assertEqual(bg.rotate_box([-1.25, -5, 15.75, 10], 90), [-5, -15.75, 10, 1.25])
        self.assertEqual(bg.rotate_box([0, 0, 2, 1], 180), [-2, -1, 0, 0])


class Footprints(unittest.TestCase):
    def test_parser_reads_the_vendored_pec11r(self):
        geo = bg.footprint_geometry(PEC11R.read_text(encoding='utf-8'))
        self.assertEqual(sorted(p['number'] for p in geo['pads']), ['A', 'B', 'C', 'MP', 'MP', 'S1', 'S2'])
        self.assertEqual(geo['courtyard'], [-1.25, -5.0, 15.75, 10.0])

    def test_npth_footprint_has_one_unplated_hole(self):
        geo = bg.footprint_geometry(bg.npth_footprint('NPTH_2.7mm', 2.7))
        self.assertEqual([(p['number'], p['type'], p['drill']) for p in geo['pads']], [('', 'np_thru_hole', [2.7])])
        self.assertEqual(geo['courtyard'], [-1.35, -1.35, 1.35, 1.35])

    def test_circle_polygon_contains_the_circle(self):
        pts = bg.circle_polygon(3, 3, 3.0, 48)
        for k in range(len(pts)):
            (x1, y1), (x2, y2) = pts[k], pts[(k + 1) % len(pts)]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2  # edge midpoint is the closest point to the centre
            self.assertGreaterEqual(((mx - 3) ** 2 + (my - 3) ** 2) ** 0.5, 3.0 - 1e-9)


class DrcPolicy(unittest.TestCase):
    RAW = {'violations': [
        {'type': 'silk_over_copper', 'severity': 'warning', 'description': 'Silk clipped', 'items': [{'description': 'a', 'pos': {'x': 1, 'y': 2}}]},
        {'type': 'copper_sliver', 'severity': 'warning', 'description': 'Sliver', 'items': []},
        {'type': 'clearance', 'severity': 'error', 'description': 'Clearance', 'items': []}],
        'unconnected_items': [], 'schematic_parity': [], 'ignored_checks': []}

    def test_errors_and_reviewed_warnings_are_separate(self):
        out = bg.drc_summary(self.RAW, {'silk_over_copper': 'legend only'}, {'clearance': 'error'})
        self.assertEqual((out['errors'], out['warnings']), (2, 1))  # unreviewed warning counts as error
        self.assertEqual(out['warning_items'][0]['reason'], 'legend only')
        self.assertFalse(out['passed'])

    def test_clean_report_passes_and_ignored_checks_fail(self):
        raw = {'violations': [self.RAW['violations'][0]], 'unconnected_items': [], 'ignored_checks': []}
        self.assertTrue(bg.drc_summary(raw, {'silk_over_copper': 'x'}, {})['passed'])
        raw['ignored_checks'] = [{'key': 'footprint_filters_mismatch', 'description': 'x'}]
        self.assertFalse(bg.drc_summary(raw, {'silk_over_copper': 'x'}, {})['passed'])
        raw['ignored_checks'] = []
        raw['unconnected_items'] = [{'type': 'unconnected_items', 'severity': 'error', 'description': 'Missing', 'items': []}]
        self.assertFalse(bg.drc_summary(raw, {'silk_over_copper': 'x'}, {})['passed'])

    def test_normalised_drc_is_order_independent(self):
        a = copy.deepcopy(self.RAW)
        b = copy.deepcopy(self.RAW)
        b['violations'].reverse()
        a['date'], b['date'] = 'one', 'two'
        self.assertEqual(bg.normalise_drc(a), bg.normalise_drc(b))

    def test_project_review_refuses_ignore_and_unlisted_warnings(self):
        spec = bg.read_json(bg.spec_path('ENC'))
        project = bg.read_json(bg.BASE / spec['project'])
        self.assertEqual(bg.check_project(spec, project), [])
        bad = copy.deepcopy(project)
        bad['board']['design_settings']['rule_severities']['copper_sliver'] = 'ignore'
        self.assertTrue(any('ignore' in p for p in bg.check_project(spec, bad)))
        bad = copy.deepcopy(project)
        bad['board']['design_settings']['rule_severities']['clearance'] = 'warning'
        self.assertTrue(any('differ' in p for p in bg.check_project(spec, bad)))
        bad = copy.deepcopy(project)
        bad['net_settings']['classes'][0]['clearance'] = 0.05
        self.assertTrue(any('below the fab floor' in p for p in bg.check_project(spec, bad)))


class RouterAndToken(unittest.TestCase):
    def test_freerouting_is_headless_without_analytics(self):
        cmd = bg.freerouting_command('/t/freerouting-cli', 'b.dsn', 'b.ses', 20, 1, '/t/u')
        self.assertIn('-da', cmd)
        self.assertIn('--gui.enabled=false', cmd)
        self.assertEqual(cmd[cmd.index('-mt') + 1], '1')
        self.assertEqual(cmd[cmd.index('-de') + 1], 'b.dsn')
        self.assertEqual(cmd[cmd.index('-do') + 1], 'b.ses')

    def test_pinned_release(self):
        self.assertEqual(bg.FREEROUTING['version'], '2.5.0')
        self.assertRegex(bg.FREEROUTING['sha256'], r'^[0-9a-f]{64}$')
        self.assertTrue(bg.FREEROUTING['url'].startswith('https://github.com/freerouting/freerouting/releases/download/v2.5.0/'))

    def test_route_token_is_exact(self):
        self.assertTrue(bg.route_requested('fix [pcb-route ENC]', 'ENC'))
        self.assertTrue(bg.route_requested('[pcb-route CTRL] [pcb-route ENC]', 'ENC'))
        self.assertFalse(bg.route_requested('[pcb-route ENCX]', 'ENC'))
        self.assertFalse(bg.route_requested('[pcb-route enc]', 'ENC'))
        self.assertFalse(bg.route_requested('pcb-route ENC', 'ENC'))
        self.assertFalse(bg.route_requested(None, 'ENC'))

    def test_fetch_refuses_a_destination_inside_the_repository(self):
        with self.assertRaises(SystemExit):
            bg.fetch_freerouting(bg.BASE / 'build/freerouting')


class RepositorySpecs(unittest.TestCase):
    def test_every_spec_names_its_file_and_validates(self):
        boards = bg.list_boards()
        self.assertIn('ENC', boards)
        for board in boards:
            spec = bg.read_json(bg.spec_path(board))
            bg.validate_spec(spec, board)

    def test_enc_pilot_resolves_against_the_graph(self):
        spec, contract, stackup, graph, db, template, project, proj = bg.prepare_inputs('ENC')
        enc = next(t for t in template if t['ref'] == 'ENC')
        self.assertEqual(enc['fpid'], 'SR_RX_Custom:RotaryEncoder_Bourns_PEC11R-4xxxF-Sxxxx')
        self.assertEqual({k: v for k, v in enc['pads'].items() if k in 'ABC'}, {'A': 'ENC_A', 'B': 'ENC_B', 'C': 'GND'})
        partition = bg.read_json(bg.BASE / spec['partition'])
        self.assertTrue(bg.domain_audit(spec, partition)['passed'])
        self.assertEqual(sum(i['qty'] for i in spec['instances']['list']) + spec['instances']['spares'], 3)
        self.assertNotIn('ENC_SW', {v for k, v in enc['pads'].items() if k in 'ABC'})

    def test_fp_lib_table_points_into_the_project_and_the_image(self):
        spec, contract, stackup, graph, db, template, project, proj = bg.prepare_inputs('ENC')
        table = bg.fp_lib_table(template)
        self.assertIn('${KIPRJMOD}/../../footprints/SR_RX_Custom.pretty', table)
        self.assertIn('${KICAD10_FOOTPRINT_DIR}/Connector_PinHeader_2.00mm.pretty', table)


if __name__ == '__main__':
    unittest.main()
