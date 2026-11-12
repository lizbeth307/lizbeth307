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
             'pending': 'header ref pending GR-3', 'anchor': {'at': [0, 0]}}],
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
        cmd = bg.freerouting_command('/t/java', '/t/fr.jar', 'b.dsn', 'b.ses', 20, 1, '/t/u', '00:05:00')
        self.assertEqual(cmd[:5], ['/t/java', '-Djava.awt.headless=true', '-cp', '/t/fr.jar', 'app.freerouting.cli.FreeroutingCli'])
        self.assertIn('-da', cmd)
        self.assertIn('--gui.enabled=false', cmd)
        self.assertIn('--router.job_timeout=00:05:00', cmd)
        self.assertIn('--router.autorouter.max_passes=20', cmd)
        self.assertIn('--router.optimizer.max_threads=1', cmd)
        self.assertEqual(cmd[cmd.index('-mt') + 1], '1')
        self.assertEqual(cmd[cmd.index('-de') + 1], 'b.dsn')
        self.assertEqual(cmd[cmd.index('-do') + 1], 'b.ses')
        with self.assertRaises(SystemExit):
            bg.freerouting_command('/t/java', '/t/fr.jar', 'b.dsn', 'b.ses', 20, 1, '/t/u', '5 min')

    def test_pinned_release(self):
        self.assertEqual(bg.FREEROUTING['version'], '2.5.0')
        for item in (bg.FREEROUTING, bg.TEMURIN_JRE):
            self.assertRegex(item['sha256'], r'^[0-9a-f]{64}$')
        self.assertTrue(bg.FREEROUTING['url'].startswith('https://github.com/freerouting/freerouting/releases/download/v2.5.0/'))
        self.assertTrue(bg.TEMURIN_JRE['url'].startswith('https://github.com/adoptium/temurin25-binaries/releases/download/'))

    def test_logged_arguments_hide_runner_paths(self):
        self.assertEqual(bg.shown_arg('/__w/_temp/freerouting/jre/x/bin/java'), 'java')
        self.assertEqual(bg.shown_arg('--user_data_path=/tmp/x'), '--user_data_path=<temp>')
        self.assertEqual(bg.shown_arg('-da'), '-da')

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


SOT236 = bg.BASE / 'build/kicad/footprints/Package_TO_SOT_SMD.pretty/SOT-23-6.kicad_mod'
C0603 = bg.BASE / 'build/kicad/footprints/Capacitor_SMD.pretty/C_0603_1608Metric.kicad_mod'


class RouteTokenSubjectOnly(unittest.TestCase):
    def test_only_the_subject_line_routes(self):
        self.assertTrue(bg.route_requested('PCB-SB1: new header [pcb-route ENC]\n\nBody text.\n', 'ENC'))
        self.assertFalse(bg.route_requested('PCB-SB1: new header\n[pcb-route ENC]\n', 'ENC'))
        self.assertFalse(bg.route_requested('PCB-SB1: new header\n\nRe-route with [pcb-route ENC] later.', 'ENC'))
        self.assertFalse(bg.route_requested('', 'ENC'))

    def test_generated_commit_quoting_its_route_run_is_a_check(self):
        msg = ('GENERATED: ENC board from sr-rx-pcb route run 1\n\nArtifact of the [pcb-route ENC] run, '
               'applied unchanged.\n\nCo-Authored-By: x')
        self.assertFalse(bg.route_requested(msg, 'ENC'))
        self.assertFalse(bg.route_requested('GENERATED: ENC [pcb-route ENC]', 'ENC'))


class FetchGuardCoversTheWholeRepository(unittest.TestCase):
    def test_destination_beside_sat_receiver_audit_is_refused(self):
        inside = bg.REPO_ROOT / 'freerouting-tools'
        self.assertFalse(bg.outside_repository(inside))
        self.assertFalse(bg.outside_repository(bg.BASE / 'build/freerouting'))
        with self.assertRaises(SystemExit):
            bg.fetch_freerouting(inside)
        with self.assertRaises(SystemExit):
            bg.fetch_freerouting(bg.REPO_ROOT)

    def test_repository_root_is_the_git_work_tree(self):
        if (bg.BASE.parent / '.git').exists():
            self.assertEqual(bg.REPO_ROOT, bg.BASE.parent)
        self.assertTrue(bg.outside_repository(bg.REPO_ROOT.parent / (bg.REPO_ROOT.name + '-tools')))


class ContractProjection(unittest.TestCase):
    CONTRACT = {'name': 'enc', 'outline_mm': [[0, 0], [24, 0], [24, 24], [0, 24]], 'cutouts_mm': [], 'holes_mm': [[3, 3]],
                'hole_d': 2.7, 'hole_keepout_d': 6.0, 'max_component_height': 6.5,
                'edge_zones': [{'edge': 'left', 'span': [6, 18]}], 'dxf': 'boards/x.dxf', 'mount': 'M2.5',
                'placements': {'main': {'origin': [1, 2], 'z_bottom': 5, 'facing': '+z'}}}

    def proj(self, contract):
        spec, graph, manifest = synthetic()
        template = bg.resolve(spec, graph, manifest)
        return bg.projection(spec, contract, {'layers': 4}, template, graph, b'{}')['parts']['contract']

    def test_fields_that_cannot_move_copper_do_not_make_the_board_stale(self):
        base = self.proj(self.CONTRACT)
        more = copy.deepcopy(self.CONTRACT)
        more.update({'height_zones': [], 'rear_zones': [], 'name': 'renamed', 'dxf': 'other.dxf', 'area_mm2': 1.0,
                     'thermal_bond_mm': [], 'modules_on_board': ['x']})
        more['placements']['main']['note'] = 'added by a MECH package'
        self.assertEqual(self.proj(more), base)

    def test_outline_holes_and_placement_origin_do(self):
        base = self.proj(self.CONTRACT)
        for path, value in ((('outline_mm',), [[0, 0], [25, 0], [25, 24], [0, 24]]), (('hole_keepout_d',), 6.5),
                            (('edge_zones',), []), (('placements', 'main', 'origin'), [1, 3])):
            changed = copy.deepcopy(self.CONTRACT)
            target = changed
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            self.assertNotEqual(self.proj(changed), base, path)


class SpecRefusals(unittest.TestCase):
    def test_rules_file_is_refused_until_it_is_copied_and_hashed(self):
        spec = bg.read_json(bg.spec_path('ENC'))
        spec['rules_file'] = 'pcb/rules/jlc-2l.kicad_dru'
        with self.assertRaises(SystemExit) as caught:
            bg.validate_spec(spec, 'ENC')
        self.assertIn('rules_file', str(caught.exception))

    def test_placeholder_needs_a_pending_text(self):
        spec = bg.read_json(bg.spec_path('ENC'))
        del next(p for p in spec['parts'] if p['source'] == 'pilot_placeholder')['pending']
        with self.assertRaises(SystemExit):
            bg.validate_spec(spec, 'ENC')


class ProvisionalStatusFromPlaceholders(unittest.TestCase):
    def test_status_names_what_the_placeholder_waits_for(self):
        spec, graph, manifest = synthetic()
        spec['parts'][1]['pending'] = 'power header pending GR-4'
        rows = bg.boundary_audit(spec, bg.resolve(spec, graph, manifest), graph, {})
        self.assertEqual({r['status'] for r in rows}, {'provisional: power header pending GR-4'})

    def test_two_placeholders_are_both_named(self):
        spec, graph, manifest = synthetic()
        spec['parts'][1]['pins'] = {}  # J carries no net: only K's status counts
        spec['parts'].append({**copy.deepcopy(spec['parts'][1]), 'ref': 'K', 'pins': {'1': 'SIG', '2': 'GND'},
                              'pending': 'probe pad pending RF'})
        for item in spec['instances']['list']:
            item['refs']['K'] = None
        rows = bg.boundary_audit(spec, bg.resolve(spec, graph, manifest), graph, {})
        self.assertEqual(rows[0]['status'], 'provisional: probe pad pending RF')
        spec['parts'][1]['pins'] = {'1': 'GND'}  # GND also leaves the board (U2 of the other instance)
        rows = bg.boundary_audit(spec, bg.resolve(spec, graph, manifest), graph, {})
        self.assertEqual(rows[0]['status'], 'provisional: header ref pending GR-3; probe pad pending RF')

    def test_enc_keeps_the_acceptance_string(self):
        spec, contract, stackup, graph, db, template, project, proj = bg.prepare_inputs('ENC')
        self.assertEqual({r['status'] for r in bg.boundary_audit(spec, template, graph, db)},
                         {'provisional: header ref pending GR-3'})


class PlacementGroups(unittest.TestCase):
    """Groups resolve to anchors with the repository's own footprints (no KiCad needed)."""

    def setup(self, side='F'):
        geo = {'U': bg.footprint_geometry(SOT236.read_text(encoding='utf-8'))}
        for ref in ('R1', 'R2', 'C1'):
            geo[ref] = bg.footprint_geometry(C0603.read_text(encoding='utf-8'))
        anchor_x = 10.0 if side == 'F' else 14.0
        template = [{'ref': 'U', 'anchor': {'at': [anchor_x, 10.0], 'rotation': 0, 'side': side}}] + \
                   [{'ref': r, 'anchor': None} for r in ('R1', 'R2', 'C1')]
        region = [12.0, 2.0, 22.0, 14.0] if side == 'F' else [2.0, 2.0, 12.0, 14.0]
        spec = {'groups': [{'id': 'G1', 'region': region, 'side': side, 'members': [
            {'ref': 'R2'}, {'ref': 'R1'}, {'ref': 'C1', 'decouple': {'ref': 'U', 'pad': '6', 'max_mm': 2.0}}]}]}
        return spec, template, geo

    def test_members_are_packed_and_the_decoupling_part_sits_by_its_pin(self):
        spec, template, geo = self.setup()
        outline = [[0, 0], [30, 0], [30, 20], [0, 20]]
        anchors, rows = bg.place_groups(spec, template, geo, [], outline)
        self.assertEqual(sorted(anchors), ['C1', 'R1', 'R2'])
        self.assertEqual((anchors, rows), bg.place_groups(spec, template, geo, [], outline))  # deterministic
        u = bg.placed_geometry(geo['U'], template[0]['anchor'])
        self.assertEqual(u['pads']['6'], [[11.1375, 10.95]])  # SOT-23-6 pad 6 at (+1.1375, -0.95), y up
        boxes = {r['ref']: r['courtyard_box'] for r in rows}
        for ref, box in boxes.items():
            self.assertTrue(12.0 - 1e-9 <= box[0] and box[2] <= 22.0 + 1e-9 and 2.0 - 1e-9 <= box[1] and box[3] <= 14.0 + 1e-9)
            self.assertFalse(bg.rects_overlap(box, u['box']), ref)
        self.assertFalse(bg.rects_overlap(boxes['R1'], boxes['C1']) or bg.rects_overlap(boxes['R2'], boxes['C1']))
        c1 = next(r for r in rows if r['ref'] == 'C1')
        self.assertLessEqual(c1['decouple']['planned_distance_mm'], 2.0)
        self.assertLessEqual(bg.box_circle_distance(c1['courtyard_box'], u['pads']['6'][0]), 2.0 + 1e-6)
        self.assertLess(boxes['R1'][0], boxes['R2'][0])  # equal heights pack in reference order

    def test_back_side_group_mirrors_like_kicad_flip(self):
        spec, template, geo = self.setup('B')
        anchors, rows = bg.place_groups(spec, template, geo, [], [[0, 0], [30, 0], [30, 20], [0, 20]])
        u = bg.placed_geometry(geo['U'], template[0]['anchor'])
        self.assertEqual(u['pads']['6'], [[12.8625, 10.95]])  # mirrored in x about the footprint position
        self.assertTrue(all(a['side'] == 'B' for a in anchors.values()))
        c1 = next(r for r in rows if r['ref'] == 'C1')
        self.assertLessEqual(bg.box_circle_distance(c1['courtyard_box'], u['pads']['6'][0]), 2.0 + 1e-6)

    def test_plan_matches_the_kicad_placement_of_the_enc_pilot(self):
        spec = bg.read_json(bg.spec_path('ENC'))
        report = bg.read_json(bg.OUT_ROOT / 'ENC/report.json')
        got = bg.placed_geometry(bg.footprint_geometry(PEC11R.read_text(encoding='utf-8')), spec['parts'][0]['anchor'])
        kicad = next(p for p in report['placement'] if p['ref'] == 'ENC')
        self.assertEqual(got['origin'], kicad['at'])
        for a, b in zip(got['box'], kicad['courtyard_box']):
            self.assertLessEqual(abs(a - b), 0.05)  # KiCad boxes include half the courtyard line
        self.assertEqual({k: v for k, v in got['pads'].items()},
                         {num: [p['at'] for p in report['pads']['ENC'] if p['number'] == num]
                          for num in {p['number'] for p in report['pads']['ENC']}})

    def test_keepouts_and_full_regions_are_refused(self):
        spec, template, geo = self.setup()
        outline = [[0, 0], [30, 0], [30, 20], [0, 20]]
        with self.assertRaises(SystemExit):
            bg.place_groups(spec, template, geo, [{'ref': 'H1', 'at': [13.5, 13.0], 'keepout_d': 3.0}], outline)
        spec['groups'][0]['region'] = [12.0, 2.0, 32.0, 14.0]
        with self.assertRaises(SystemExit):
            bg.place_groups(spec, template, geo, [], outline)

    def test_spec_validation_of_groups(self):
        base = bg.read_json(bg.spec_path('ENC'))
        spec = copy.deepcopy(base)
        enc = spec['parts'][0]
        del enc['anchor']
        spec['groups'] = [{'id': 'G', 'region': [5, 3, 20, 21], 'members': [{'ref': 'ENC', 'rotation': 90}]}]
        bg.validate_spec(spec, 'ENC')  # an anchor-less part is accepted when a group places it
        refused = []
        bad = copy.deepcopy(spec)
        bad['parts'][0]['anchor'] = base['parts'][0]['anchor']
        refused.append(bad)  # anchored and grouped
        bad = copy.deepcopy(spec)
        bad['groups'] = []
        refused.append(bad)  # no anchor and no group
        bad = copy.deepcopy(spec)
        bad['groups'][0]['members'].append({'ref': 'J1'})
        refused.append(bad)  # a placeholder needs an anchor
        bad = copy.deepcopy(spec)
        bad['groups'][0]['members'][0]['rotation'] = 45
        refused.append(bad)
        bad = copy.deepcopy(spec)
        bad['groups'][0]['region'] = [5, 3, 4, 21]
        refused.append(bad)
        bad = copy.deepcopy(spec)
        bad['groups'][0]['members'][0]['decouple'] = {'ref': 'J1', 'pad': '1', 'max_mm': 2.0}
        bad['groups'][0]['side'] = 'B'
        refused.append(bad)  # decoupling target on the other side
        for i, candidate in enumerate(refused):
            with self.assertRaises(SystemExit, msg=i):
                bg.validate_spec(candidate, 'ENC')


class CutoutsViasAndLayerTypes(unittest.TestCase):
    """W2 PCB-PWRB: contract cutouts, scripted vias, zone pad connection and copper layer types (optional spec keys)."""

    def enc(self):
        return bg.read_json(bg.spec_path('ENC'))

    def test_cutout_boxes_read_x_y_w_h(self):
        self.assertEqual(bg.cutout_boxes({'cutouts_mm': [[7.5, 39.5, 26.4, 26.4]]}), [[7.5, 39.5, 33.9, 65.9]])
        self.assertEqual(bg.cutout_boxes({}), [])

    def test_group_region_and_parts_stay_out_of_cutouts(self):
        template = [{'ref': 'C1', 'anchor': None}]
        geometry = {'C1': bg.footprint_geometry(C0603.read_text(encoding='utf-8'))}
        outline = [[0, 0], [40, 0], [40, 20], [0, 20]]
        spec = {'groups': [{'id': 'G', 'region': [2, 2, 12, 12], 'members': [{'ref': 'C1'}]}]}
        anchors, _rows = bg.place_groups(spec, template, geometry, [], outline, bg.cutout_boxes({'cutouts_mm': [[20, 5, 10, 10]]}))
        self.assertIn('C1', anchors)
        spec['groups'][0]['region'] = [15, 2, 25, 12]
        with self.assertRaises(SystemExit):
            bg.place_groups(spec, template, geometry, [], outline, bg.cutout_boxes({'cutouts_mm': [[20, 5, 10, 10]]}))

    def test_optional_keys_validate(self):
        spec = self.enc()
        spec['layers']['types'] = {'B.Cu': 'signal'}
        spec['pre_route']['vias'] = [{'id': 'V1', 'net': 'GND', 'at': [12.0, 4.5], 'drill_mm': 0.3, 'diameter_mm': 0.6}]
        spec['post_route_zones'][0]['pad_connection'] = 'tht_thermal'
        bg.validate_spec(spec, 'ENC')
        bad = []
        for key, value in (('types', {'In1.Cu': 'power'}), ('types', {'F.Cu': 'plane'})):
            s = copy.deepcopy(spec)
            s['layers'][key] = value
            bad.append(s)  # In1.Cu does not exist on a 2-layer board; unknown type
        s = copy.deepcopy(spec)
        s['pre_route']['vias'][0]['net'] = 'NOPE'
        bad.append(s)
        s = copy.deepcopy(spec)
        s['pre_route']['vias'][0]['drill_mm'] = 0.7
        bad.append(s)  # drill not below the diameter
        s = copy.deepcopy(spec)
        s['post_route_zones'][0]['pad_connection'] = 'spokes'
        bad.append(s)
        for i, candidate in enumerate(bad):
            with self.assertRaises(SystemExit, msg=i):
                bg.validate_spec(candidate, 'ENC')

    def test_router_extras_and_edge_strips(self):
        self.assertEqual(bg.router_extra({}), [])
        self.assertEqual(bg.router_extra({'fanout': False, 'ignore_net_classes': ['SCRIPTED_A', 'B']}),
                         ['--router.fanout.enabled=false', '-inc', 'SCRIPTED_A,B'])
        cmd = bg.freerouting_command('/t/java', '/t/fr.jar', 'b.dsn', 'b.ses', 20, 1, '/t/u', '00:05:00', ['-inc', 'X'])
        self.assertEqual(cmd[-2:], ['-inc', 'X'])
        for bad in ({'fanout': 'no'}, {'ignore_net_classes': ['A B']}):
            with self.assertRaises(SystemExit):
                bg.router_extra(bad)
        strip = bg.edge_strip((0.0, 0.0), (10.0, 0.0), 0.2)
        xs, ys = [p[0] for p in strip], [p[1] for p in strip]
        self.assertEqual((round(min(xs), 6), round(max(xs), 6), round(min(ys), 6), round(max(ys), 6)), (-0.2, 10.2, -0.2, 0.2))

    def test_pwr_b_spec_resolves_with_the_b2b_half_j209(self):
        # W2 B2B: the graph ref J209 (Samtec LSHM-150) replaced the FX8 pilot placeholder B2B1 on the PWR-B bottom
        if not bg.spec_path('PWR_B').is_file():
            self.skipTest('no PWR_B spec')
        spec, contract, stackup, graph, db, template, project, proj = bg.prepare_inputs('PWR_B')
        self.assertTrue(contract['cutouts_mm'])
        self.assertTrue(bg.domain_audit(spec, bg.read_json(bg.BASE / spec['partition']))['passed'])
        self.assertFalse([p['ref'] for p in spec['parts'] if p['source'] == 'pilot_placeholder'])
        b2b = next(t for t in template if t['ref'] == 'J209')
        self.assertEqual((b2b['source'], b2b['anchor']['side']), ('graph', 'B'))
        self.assertEqual(sum(1 for n in b2b['pads'].values() if n == 'LAB5'), 4)  # ceil(4 A / 1 A), b2b-nets.json
        status = {b['status'] for b in bg.boundary_audit(spec, template, graph, db)}
        self.assertEqual(status, {'pass'})


class PwrBPinMapFollowsB2bNets(unittest.TestCase):
    """W2 PCB-PWRB, W2 B2B: the PWR_B B2B half J209 carries pcb/generated/b2b-nets.json contacts pin for pin (CI does not run
    build/kicad/boards/PWR_B/make_spec.py --check, and b2b-nets.json is no board_gen input)."""

    def test_contacts_per_net_gnd_count_and_source_hash(self):
        if not bg.spec_path('PWR_B').is_file():
            self.skipTest('no PWR_B spec')
        import collections
        import hashlib
        spec = bg.read_json(bg.spec_path('PWR_B'))
        path = bg.BASE / 'pcb/generated/b2b-nets.json'
        b2b = bg.read_json(path)
        ref = b2b['graph_refs']['pwr_b']
        self.assertTrue(any(p['ref'] == ref and p['source'] == 'graph' and p['anchor']['side'] == 'B' for p in spec['parts']))
        pins = {str(p['number']): (None if p.get('nc') else p.get('net')) for p in bg.load_graph()[ref]['pins']}
        self.assertEqual(pins, {str(c['pwr_b_pin']): (c['net'] or None) for c in b2b['contacts']})
        want = collections.Counter({n['net']: int(n['pins']) for n in b2b['nets']})
        want['GND'] += b2b['totals']['gnd_pins']
        self.assertEqual(collections.Counter(n for n in pins.values() if n), want)
        pin_map = spec['b2b_pin_map']
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(pin_map['source'], f'pcb/generated/b2b-nets.json sha256 {digest}')
        self.assertEqual((pin_map['used'], pin_map['spare']), (b2b['totals']['contacts_needed'],
                                                               b2b['contacts_available'] - b2b['totals']['contacts_needed']))


class BondHoleAndCoupon(unittest.TestCase):
    """W2 PCB-RF-2: optional spec keys bond_hole (plated, netted contract hole) and coupon (post-route test coupon)."""

    def setUp(self):
        if not bg.spec_path('RF').is_file():
            self.skipTest('no RF spec')

    def test_rf_bond_hole_is_plated_and_ends_chassis(self):
        spec, contract, stackup, graph, db, template, project, proj = bg.prepare_inputs('RF')
        plated = [(h['ref'], h['plated']['net']) for h in bg.holes(spec, contract) if h.get('plated')]
        self.assertEqual(plated, [('H5', 'CHASSIS')])
        rows = bg.boundary_audit(spec, template, graph, db)[0]['nets']
        self.assertEqual(next(r for r in rows if r['net'] == 'CHASSIS')['status'], 'connector')
        self.assertTrue(spec['coupon']['footprints'] and spec['coupon']['zones'])

    def test_bad_bond_hole_and_coupon_are_refused(self):
        spec = bg.read_json(bg.spec_path('RF'))
        mutations = (lambda s: s['bond_hole'].update(net='NOPE'), lambda s: s['bond_hole'].pop('why'),
                     lambda s: s['coupon'].pop('why'), lambda s: s['coupon']['footprints'][0].update(ref='C401'),
                     lambda s: s['coupon']['tracks'][0].update(net='NOPE'),
                     lambda s: s['coupon']['zones'][0].update(outline='board'),
                     lambda s: s['coupon']['outlines'][0].__setitem__(2, -1.0))
        for i, mutate in enumerate(mutations):
            s = copy.deepcopy(spec)
            mutate(s)
            with self.assertRaises(SystemExit, msg=i):
                bg.validate_spec(s, 'RF')
        contract, _stack = bg.load_contract(spec)
        for at, pad in (([93.0, 40.5], 7.0), ([92.0, 40.5], 8.0), ([92.0, 40.5], 3.0)):
            s = copy.deepcopy(spec)
            s['bond_hole'].update(at=at, pad_mm=pad)
            with self.assertRaises(SystemExit, msg=(at, pad)):
                bg.holes(s, contract)


if __name__ == '__main__':
    unittest.main()
