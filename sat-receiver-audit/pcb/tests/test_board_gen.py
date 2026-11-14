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
        self.assertEqual(contract['cutouts_mm'], [])  # W2 MECH-7 full L; the PWR-A cut-outs are spec height zones (W2 PCB-PWRB-2)
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



class PwrBLeavesPwrACutoutsFree(unittest.TestCase):
    """W2 PCB-PWRB-2: on the full-L contract no PWR_B top courtyard reaches a PWR-A cut-out of the PCB-PWRA-3 placement study;
    every cut-out is a 0 mm height zone of the spec, so pcb/check_boards.py reports a part over it."""

    def test_cutouts_are_zero_height_zones_and_free(self):
        if not bg.spec_path('PWR_B').is_file():
            self.skipTest('no PWR_B spec')
        import hashlib
        spec = bg.read_json(bg.spec_path('PWR_B'))
        study = bg.BASE / 'build/kicad/boards/PWR_A/placement-study-shrink2.json'
        cut = spec['pwr_a_cutouts']
        rows = [{'ref': c['ref'], 'kind': c['kind'], 'rect': [float(v) for v in c['rect']]}
                for c in bg.read_json(study)['pwr_b_cutouts']['placed']]
        self.assertIn(hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest(),
                      cut['source'])
        want = [[c['rect'][0], c['rect'][1], round(c['rect'][2] - c['rect'][0], 4), round(c['rect'][3] - c['rect'][1], 4)]
                for c in bg.read_json(study)['pwr_b_cutouts']['placed']]
        self.assertEqual([c['rect'] for c in cut['cutouts_mm']], want)
        zones = [z['region'] for z in spec['height_zones'] if z.get('max_height_mm') == 0.0 and z['side'] == 'top']
        self.assertEqual(zones, want)
        self.assertEqual(cut['overlay']['overlaps'], [])
        self.assertEqual(cut['overlay']['overlap_mm2'], 0.0)


class PwrBSixLayersAndCutoutRuleAreas(unittest.TestCase):
    """W2 PWRB-R layers6: PWR_B on the 6-layer stackup (S-G-S-S-P-S), power classes on the outer copper only, and every PWR-A
    cut-out a rule area on all copper layers, audited by board_gen and check_boards (W2 PWR-TOOLS: the layers6 keepout_rects
    key gave way to planned_cutouts, the one cut-out key; these tests now read that key)."""

    def setUp(self):
        if not bg.spec_path('PWR_B').is_file():
            self.skipTest('no PWR_B spec')
        self.spec = bg.read_json(bg.spec_path('PWR_B'))

    def test_six_layers_planes_and_outer_power(self):
        spec = self.spec
        if spec['layers']['copper'] != 6:
            self.skipTest('PWR_B is not on 6 layers on this branch')
        self.assertEqual(spec['layers']['types'], {'In1.Cu': 'power', 'In4.Cu': 'power'})
        planes = {(z['layer'], z['net']) for z in spec['pre_route']['zones']}
        self.assertEqual(planes, {('In1.Cu', 'GND'), ('In4.Cu', '3V3_Q6A')})
        if not spec['router'].get('diagnostic'):  # a diagnostic route run may leave class_layers out (W2 PWRB-R probe 2)
            self.assertIn('PWR1A', spec['router']['class_layers'])
        for cls, layers in spec['router'].get('class_layers', {}).items():
            if cls.startswith(('PWR', 'BATT')):
                self.assertEqual(sorted(layers), ['B.Cu', 'F.Cu'])
        stack = bg.read_json(bg.BASE / 'pcb/generated/stackup-6l.json')
        self.assertIn('PWR_B', stack['stackup']['boards'])
        self.assertEqual([l['kicad'] for l in stack['stackup']['layers'] if 'kicad' in l],
                         ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu'])
        bg.validate_spec(spec, 'PWR_B')

    def test_cutouts_are_rule_areas_on_every_layer(self):
        spec = self.spec
        pc = spec.get('planned_cutouts')
        if not pc:
            self.skipTest('no planned_cutouts on this branch')
        self.assertNotIn('keepout_rects', spec)
        self.assertEqual([r['rect'] for r in pc['rects']], [c['rect'] for c in spec['pwr_a_cutouts']['cutouts_mm']])
        copper = ['F.Cu', 'B.Cu'] + [f'In{i}.Cu' for i in range(1, spec['layers']['copper'] - 1)]
        self.assertEqual(sorted(pc['layers']), sorted(copper))
        self.assertEqual(sorted(pc['blocks']), ['pads', 'tracks', 'vias', 'zone_fills'])
        self.assertGreaterEqual(pc['margin_mm'], spec['fab_floor']['min_copper_edge_clearance'])

    def test_planned_cutouts_validation_and_distance(self):
        base = {'why': 'w', 'margin_mm': 0.33, 'layers': ['F.Cu'], 'blocks': ['tracks', 'pads'],
                'rects': [{'id': 'A1', 'rect': [0, 0, 1, 1]}]}
        bg.validate_planned_cutouts({'planned_cutouts': base}, 'X', ['F.Cu', 'B.Cu'])
        bad = [dict(base, margin_mm=0), dict(base, layers=['In9.Cu']), dict(base, blocks=['footprints']),
               dict(base, rects=[{'id': 'A1', 'rect': [1, 0, 0, 1]}]), dict(base, rects=[{'id': 'A 1', 'rect': [0, 0, 1, 1]}]),
               dict(base, rects=base['rects'] * 2), dict(base, why=''), dict(base, rects=[])]
        for i, pc in enumerate(bad):
            with self.assertRaises(SystemExit, msg=i):
                bg.validate_planned_cutouts({'planned_cutouts': pc}, 'X', ['F.Cu', 'B.Cu'])
        box = (0.0, 0.0, 2.0, 1.0)
        self.assertEqual(bg.seg_rect_distance((-1.0, 0.5), (3.0, 0.5), box), 0.0)        # crosses
        self.assertEqual(bg.seg_rect_distance((0.5, 0.5), (0.6, 0.6), box), 0.0)          # inside
        self.assertAlmostEqual(bg.seg_rect_distance((-1.0, 2.0), (3.0, 2.0), box), 1.0)   # parallel above
        self.assertAlmostEqual(bg.seg_rect_distance((3.0, 4.0), (3.0, 4.0), box), 10 ** 0.5)

    def test_class_layers_dsn_patch(self):
        dsn = '(network (class PWR1A A B (circuit (use_via V)) (rule (width 350))) (class kicad_default C (circuit (use_via V))))'
        out = bg.patch_dsn_class_layers(dsn, {'PWR1A': ['F.Cu', 'B.Cu']})
        self.assertIn('(circuit\n        (use_layer F.Cu B.Cu) (use_via V)) (rule (width 350))', out)
        with self.assertRaises(SystemExit):
            bg.patch_dsn_class_layers(dsn, {'PWR3A': ['F.Cu']})

    def test_check_boards_fill_overlap_test_sees_track_via_and_fill(self):
        import check_boards as cb  # shape_hits_box: the zone-fill test of check_planned_cutouts
        box = (10.0, 10.0, 12.0, 12.0)
        self.assertTrue(cb.shape_hits_box(cb.Capsule(9.0, 9.0, 13.0, 13.0, 0.1), box))
        self.assertFalse(cb.shape_hits_box(cb.Capsule(9.0, 13.0, 13.0, 13.0, 0.1), box))
        self.assertTrue(cb.shape_hits_box(cb.Capsule(11.0, 12.5, 11.0, 12.5, 0.6), box))
        ring = cb.Poly([(0, 0), (30, 0), (30, 30), (0, 30)])            # a fill around the box
        self.assertTrue(cb.shape_hits_box(ring, box))
        notch = cb.Poly([(0, 0), (30, 0), (30, 9), (0, 9)])             # a fill below the box
        self.assertFalse(cb.shape_hits_box(notch, box))
        edge = cb.Poly([(0, 0), (30, 0), (30, 10.5), (0, 10.5)])        # a fill edge across the box
        self.assertTrue(cb.shape_hits_box(edge, box))



class PlannedCutoutKeyAndFrozenRouter(unittest.TestCase):
    """W2 PWR-TOOLS: planned_cutouts is the one cut-out key (the layers6 keepout_rects path is gone): PWR_B carries the
    regenerated PWR-A placement-study pwr_b_cutouts as rule areas on all six copper layers, and the board_gen report audit
    (planned_cutout_audit) and pcb/check_boards.py planned_cutouts read that key; a spec router with freeze_only routes
    nothing (router_skip: Freerouting is not started on a frozen board)."""

    def test_pwr_b_cutouts_equal_the_regenerated_placement_study(self):
        if not bg.spec_path('PWR_B').is_file():
            self.skipTest('no PWR_B spec')
        spec = bg.read_json(bg.spec_path('PWR_B'))
        self.assertNotIn('keepout_rects', spec)
        pc = spec['planned_cutouts']
        study = bg.read_json(bg.BASE / 'build/kicad/boards/PWR_A/placement-study-shrink2.json')['pwr_b_cutouts']['placed']
        want = [[c['rect'][0], c['rect'][1], round(c['rect'][2] - c['rect'][0], 4), round(c['rect'][3] - c['rect'][1], 4)]
                for c in study]
        self.assertEqual(len(pc['rects']), 47)  # 50 until W2 GR-ZONE2-SMD (no C265/C511/C512 windows), W2 PWR-L6-PLACE
        self.assertEqual([r['rect'] for r in pc['rects']], want)
        self.assertEqual([r['id'] for r in pc['rects']], [c['ref'] for c in study])
        self.assertEqual(pc['margin_mm'], 0.33)
        self.assertEqual(pc['layers'], ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu'])
        self.assertEqual(set(pc['blocks']), {'tracks', 'vias', 'zone_fills', 'pads'})
        boxes = bg.planned_cutout_boxes(spec)
        self.assertEqual(len(boxes), 47)
        for (cid, box), r in zip(boxes, pc['rects']):
            self.assertEqual(cid, r['id'])
            self.assertAlmostEqual(box[0], r['rect'][0] - 0.33)
            self.assertAlmostEqual(box[3], r['rect'][1] + r['rect'][3] + 0.33)
        bg.validate_spec(spec, 'PWR_B')

    def test_check_boards_reads_planned_cutouts(self):
        import check_boards as cb
        self.assertIn('planned_cutouts', cb.NATIVE_KEYS)
        self.assertNotIn('keepout_rects', cb.NATIVE_KEYS + cb.DICT_KEYS)
        self.assertFalse(hasattr(cb, 'check_keepout_rects') or hasattr(bg, 'validate_keepout_rects')
                         or hasattr(bg, 'keepout_rect_audit'))
        key = {'why': 'test', 'margin_mm': 0.3, 'layers': ['F.Cu', 'B.Cu'], 'blocks': ['tracks', 'vias'],
               'rects': [{'id': 'C1', 'rect': [2.0, 4.0, 1.0, 1.0]}]}
        edges = ''.join(f'(gr_line (start {a} {b}) (end {c} {d}) (layer "Edge.Cuts") (stroke (width 0.05)))'
                        for a, b, c, d in ((100, 100, 110, 100), (110, 100, 110, 110), (110, 110, 100, 110), (100, 110, 100, 100)))
        # contract rect [2, 4, 1, 1] (y up) = KiCad x 102-103, y 105-106; one track crosses it, one passes 0.2 mm off its
        # right edge (inside the 0.3 mm margin), one stays 1 mm away
        tracks = ('(segment (start 101 105.5) (end 104 105.5) (width 0.2) (layer "F.Cu") (net 1))'
                  '(segment (start 103.3 104) (end 103.3 107) (width 0.2) (layer "B.Cu") (net 1))'
                  '(segment (start 101 108) (end 104 108) (width 0.2) (layer "F.Cu") (net 1))')
        text = (f'(kicad_pcb (version 20241229) (layers (0 "F.Cu" signal) (31 "B.Cu" signal)) (net 0 "") (net 1 "A") '
                f'{edges}{tracks})')
        board = cb.Board(cb.parse(text))
        spec = {'board_id': 'T', 'planned_cutouts': key}
        contract = {'outline_mm': [[0, 0], [10, 0], [10, 10], [0, 10]]}
        out, info = cb.check_planned_cutouts(board, cb.Frame(board, contract, spec), spec)
        self.assertEqual(len(out), 2)
        self.assertEqual((info['per_rect'][0]['items_inside'], info['per_rect'][0]['items_within_margin']), (1, 1))
        self.assertEqual(cb.normalize_spec(dict(spec, schema=cb.SPEC_SCHEMA_V1))['planned_cutouts'], key)

    def test_board_gen_report_audit_reads_planned_cutouts(self):
        """planned_cutout_audit against a minimal stand-in of the pcbnew objects it reads (no KiCad here)."""
        class Obj:
            def __init__(self, **k):
                self.__dict__.update(k)

        class Box:
            def __init__(self, x0, y0, x1, y1):
                self.b = (x0, y0, x1, y1)

            def GetLeft(self):
                return self.b[0]

            def GetBottom(self):
                return self.b[1]

            def GetRight(self):
                return self.b[2]

            def GetTop(self):
                return self.b[3]
        pcb = Obj(PCB_TRACE_T=1, PCB_VIA_T=2, VECTOR2I=lambda x, y: (x, y), ToMM=lambda v: v)
        frame = Obj(m=lambda p: (float(p[0]), float(p[1])), k=lambda x, y: (x, y))
        track = Obj(Type=lambda: 1, GetNetname=lambda: 'A', GetStart=lambda: (0.0, 4.5), GetEnd=lambda: (2.5, 4.5),
                    GetWidth=lambda: 0.2, GetLayer=lambda: 'F.Cu')
        names = [f'KO_CUT_C1_{n}' for n in ('F.Cu', 'B.Cu')]
        zones = [Obj(GetZoneName=lambda n=n: n, GetIsRuleArea=lambda: True) for n in names]
        board = Obj(Zones=lambda: zones, GetTracks=lambda: [track], GetFootprints=lambda: [], GetLayerName=lambda layer: layer)
        spec = {'planned_cutouts': {'why': 'test', 'margin_mm': 0.33, 'layers': ['F.Cu', 'B.Cu'], 'blocks': ['tracks'],
                                    'rects': [{'id': 'C1', 'rect': [2.0, 4.0, 1.0, 1.0]}]}}
        res = bg.planned_cutout_audit(pcb, board, frame, spec)
        self.assertFalse(res['passed'])
        self.assertEqual([e['rect'] for e in res['errors']], ['C1'])
        self.assertEqual((res['margin_mm'], res['rule_areas_missing']), (0.33, []))
        track.GetEnd = lambda: (1.5, 4.5)  # 0.4 mm from the rect: clear of the 0.33 mm margin
        res = bg.planned_cutout_audit(pcb, board, frame, spec)
        self.assertTrue(res['passed'], res['errors'])
        board.Zones = lambda: zones[:1]
        self.assertEqual(bg.planned_cutout_audit(pcb, board, frame, spec)['rule_areas_missing'], ['KO_CUT_C1_B.Cu'])

    def test_freeze_only_router_skip(self):
        self.assertIsNone(bg.router_skip({'tool': 'freerouting'}))
        self.assertEqual(bg.router_skip({'freeze_only': 'frozen'}), 'frozen')
        for bad in ('', '  ', True, 1):
            with self.assertRaises(SystemExit, msg=bad):
                bg.router_skip({'freeze_only': bad})
        if not bg.spec_path('PWR_B').is_file():
            self.skipTest('no PWR_B spec')
        spec = bg.read_json(bg.spec_path('PWR_B'))
        if not spec['router'].get('freeze_only'):
            self.skipTest('PWR_B has no frozen route on this branch')
        bg.validate_spec(spec, 'PWR_B')
        s = copy.deepcopy(spec)
        s['pre_route']['tracks'] = [dict(t, locked=False) for t in s['pre_route']['tracks']]
        with self.assertRaises(SystemExit):
            bg.validate_spec(s, 'PWR_B')



class PwrL6PlaceEscapeAndAnchors(unittest.TestCase):
    """W2 PWR-L6-PLACE: the J209 escape corridor of PWR_B (no PWR-A window over a part taller than hA in the J209 field,
    C265/C511/C512 without a cut-out), the LAB5 branches of PWR_B at >= 0.667 mm (F102 4 A at +20 degC on 2 oz, IPC-2221
    MODEL) and the U107/U108 small-signal anchors of the PWR-A planner spec inside thermal_bond zones 3'/4'."""

    def test_j209_escape_corridor(self):
        if not bg.spec_path('PWR_B').is_file():
            self.skipTest('no PWR_B spec')
        spec = bg.read_json(bg.spec_path('PWR_B'))
        esc = spec['j209_escape']
        self.assertTrue(esc['passed'])
        self.assertEqual(esc['zone2_windows_in_field'], [])
        self.assertEqual({c['kind'] for c in esc['cutouts_in_field']}, {'header_edge_strip'})
        ids = {r['id'] for r in spec['planned_cutouts']['rects']}
        self.assertFalse(ids & {'C265', 'C511', 'C512'})
        self.assertGreaterEqual(esc['field_free_of_cutouts_mm2'], 400.0)  # third pass: the corridor is the band y 11.75-15.4, the field keeps 430.5 mm2 free

    def test_lab5_branches_take_the_f102_rating(self):
        if not bg.spec_path('PWR_B').is_file():
            self.skipTest('no PWR_B spec')
        spec = bg.read_json(bg.spec_path('PWR_B'))
        branches = [t for t in spec['pre_route']['tracks'] if t['id'].startswith('LAB5-BR-')]
        self.assertEqual(sorted(t['id'][8:] for t in branches), ['U210', 'U221', 'U501', 'U502'])
        for t in branches:
            self.assertGreaterEqual(t['width_mm'], 0.667, t['id'])
        for ref in ('U210', 'U221', 'U501', 'U502'):
            self.assertGreaterEqual(spec['branch_exempt'][ref]['min_width_mm'], 0.667, ref)

    def test_small_signal_anchors_inside_zones(self):
        path = bg.BASE / 'build/kicad/boards/PWR_A/PWR_A.spec-shrink2.json'
        if not path.is_file():
            self.skipTest('no PWR_A planner spec')
        spec = bg.read_json(path)
        ss = spec['power_stages']['small_signal']
        self.assertTrue(ss['passed'])
        want = {'C127': 3, 'R127': 3, 'C128': 3, 'C129': 3, 'R124': 3, 'R125': 3, 'R128': 3, 'R129': 4, 'R130': 4}
        self.assertEqual({r['ref']: r['zone'] for r in ss['rows']}, want)
        for r in ss['rows']:
            self.assertTrue(r['inside'], r['ref'])
            self.assertTrue(all(d <= r['limit_mm'] for d in r['pad_to_pin_mm'].values()), r['ref'])
        anchored = {p['ref'] for p in spec['parts'] if p.get('anchor')}
        self.assertLessEqual(set(want), anchored)


class PwrL6Place3ExitPair(unittest.TestCase):
    """W2 PWR-L6-PLACE third pass (judge decision ESC-JUDGE, option M): the vertical top-entry exit pair J203 / J506 in PWR_B
    zone 2 under the J209 escape band, the U215 I2C2 via in pad, the zone-2 height zone from the contract, the PWR-A parts under
    the new PWR-B pin fields (H-TRIM) and the fan-out-first completion order of freeze6. MODEL / CI inputs only."""

    def spec(self):
        if not bg.spec_path('PWR_B').is_file():
            self.skipTest('no PWR_B spec')
        return bg.read_json(bg.spec_path('PWR_B'))

    def test_exit_pair_in_zone_two(self):
        spec = self.spec()
        parts = {p['ref']: p['anchor'] for p in spec['parts']}
        self.assertEqual((parts['J203']['at'], parts['J203']['rotation']), ([93.3, 9.75], 0))
        self.assertEqual((parts['J506']['at'], parts['J506']['rotation']), ([92.5, 3.55], 0))
        self.assertEqual((parts['C249']['at'], parts['C249']['rotation']), ([112.85, 3.0], 180))
        esc = spec['j209_escape']
        self.assertTrue(esc['passed'])
        self.assertEqual(esc['exit_field_mm'], [90.0, 0.0, 115.0, 11.75])
        self.assertEqual(sorted(esc['exit_field_courtyards']), ['C249', 'J203', 'J506'])
        for ref in ('J203', 'J506'):
            self.assertTrue(esc['exit_pair'][ref]['inside_exit_field'], ref)
        self.assertEqual(spec['pwr_a_cutouts']['overlay']['overlaps'], [])
        for c in spec['pwr_a_cutouts']['cutouts_mm']:                      # no cut-out reaches into the exit field
            x0, y0, w, h = c['rect']
            hit = min(x0 + w, 115.0) - max(x0, 90.0) > 1e-9 and min(y0 + h, 11.75) - max(y0, 0.0) > 1e-9
            self.assertFalse(hit, c)
        contract = bg.read_json(bg.BASE / 'mechanical/generated/contract/boards.json')['boards']['PWR_B']
        ez = [z for z in contract['edge_zones'] if 'J203' in z.get('headers', [])]
        self.assertEqual([(z['edge'], z['span'], z.get('exit'), z['headers']) for z in ez], [('bottom', [90.0, 115.0], 'top', ['J203', 'J506'])])

    def test_escape_band_rule(self):
        esc = self.spec()['j209_escape']
        self.assertEqual(esc['corridor_mm'], [84.0, 11.75, 116.0, 15.4])
        self.assertAlmostEqual(esc['band_height_mm'], 3.65, places=3)          # J203 courtyard top 11.75 to J209 courtyard 15.4
        self.assertNotIn('J203', esc['pwr_b_top_courtyards_in_corridor'])
        self.assertNotIn('C249', esc['pwr_b_top_courtyards_in_corridor'])
        self.assertEqual(esc['zone2_windows_in_field'], [])

    def test_no_tall_pwr_a_part_under_the_new_pin_fields(self):
        study = bg.read_json(bg.BASE / 'build/kicad/boards/PWR_A/placement-study-shrink2.json')
        ht = study['h_trim']
        self.assertTrue(ht['passed'])
        self.assertEqual(ht['violations'], [])
        zones = {f['ref']: f['zone'] for f in ht['pwr_b_tht_fields']}
        self.assertEqual(zones['J203'], [92.2, 6.65, 112.4, 10.85])
        self.assertEqual(zones['J506'], [91.4, 2.175, 109.6, 4.925])
        for u in ht['parts_under']:
            if set(u['under']) & {'J203', 'J506'}:
                self.assertTrue(u['ok'] and u['h_mm'] is not None and u['h_mm'] <= 2.7, u)
        pos = {r['ref']: r for r in study['positions']['refs']}
        self.assertEqual((pos['C512']['at'], pos['C512']['how']), ([101.9, 31.45], 'anchor'))
        self.assertEqual(study['unplaced_refs'], [])
        self.assertEqual(study['pwr_b_cutouts']['unplaced_needing_one'], [])

    def test_u215_via_in_pad(self):
        spec = self.spec()
        vias = {v['id']: v for v in spec['pre_route']['vias']}
        rec = {r['id']: r for r in spec['via_in_pad']['vias']}
        want = {'VIP-U215-6': ('I2C2_SCL', [21.175, 56.35], 'U215.6'), 'VIP-U215-7': ('I2C2_SDA', [21.825, 56.9], 'U215.7')}
        for vid, (net, at, pad) in want.items():
            v = vias[vid]
            self.assertEqual((v['net'], v['at'], v['diameter_mm'], v['drill_mm'], v['locked']), (net, at, 0.6, 0.3, True))
            self.assertEqual(rec[vid]['pad'], pad)
            self.assertGreaterEqual(rec[vid]['gap_to_neighbour_pads_mm'], 0.15)    # KiCad clearance
            self.assertLess(rec[vid]['gap_to_neighbour_pads_mm'], 0.20)            # the recorded exception to CLEAR + MARGIN
        a, b = vias['VIP-U215-6']['at'], vias['VIP-U215-7']['at']
        self.assertGreaterEqual(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 - 0.3, 0.5 + 0.05)   # hole to hole
        self.assertIn('TBD at order', spec['via_in_pad']['fab'])
        self.assertTrue(spec['via_in_pad']['gate'].startswith('OPEN'))

    def test_zone_two_height_zone(self):
        spec = self.spec()
        contract = bg.read_json(bg.BASE / 'mechanical/generated/contract/boards.json')['boards']['PWR_B']
        top = [z for z in spec['height_zones'] if z['side'] == 'top' and z.get('max_height_mm', 0) > 0]
        self.assertEqual([z['region'] for z in top], [z['rect'] for z in contract['height_zones']])
        self.assertEqual([z['max_height_mm'] for z in top], [z['fits_mm'] for z in contract['height_zones']])
        self.assertFalse([z for z in spec['height_zones'] if z['side'] == 'top' and z['region'] == 'board'])
        self.assertEqual(contract['max_component_height'], 5.5)               # every other top part: the contract default
        self.assertEqual((spec['heights']['J203'], spec['heights']['J506']), (6.5, 6.0))
        self.assertLessEqual(spec['heights']['J203'], top[0]['max_height_mm'])

    def test_freeze6_fanout_order(self):
        import ast
        import collections
        import types
        src = (bg.BASE / 'build/kicad/boards/PWR_B/freeze/freeze6.py').read_text(encoding='utf-8')
        tree = ast.parse(src)
        keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name == 'fanout_first')
                or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Tuple) and 'FANOUT_TO' in [e.id for e in t.elts]
                                                     for t in n.targets))]
        self.assertEqual(len(keep), 2)
        self.assertIn("choices=('class', 'short', 'fanout')", src)
        ns = {'collections': collections, 'B2B': 'J209'}
        exec(compile(ast.Module(body=keep, type_ignores=[]), 'freeze6_fanout', 'exec'), ns)
        pad = lambda net, ref, x: types.SimpleNamespace(alive=True, kind='pad', net=net, ref=ref, at=(x, 0.0))
        items = [pad('A', 'J209', 190.0), pad('A', 'J203', 195.0), pad('B', 'J209', 199.0), pad('B', 'J203', 201.0),
                 pad('I2C2_SDA', 'J209', 195.5), pad('I2C2_SCL', 'J209', 196.0), pad('C', 'J209', 180.0), pad('C', 'U1', 120.0)]
        m = types.SimpleNamespace(items=items)
        order = ns['fanout_first'](m, {'A', 'B', 'C', 'I2C2_SCL', 'I2C2_SDA'}, lambda n: 0.0)
        self.assertEqual(order, ['B', 'A', 'I2C2_SCL', 'I2C2_SDA', 'C'])     # J209-to-J203 right to left, I2C2, the rest



class PwrL6ProbeCPinSwap(unittest.TestCase):
    """W2 PWR-L6-PLACE fourth pass, probe C (connector lever, PWR-B only): the four innermost J202-bound J209 lower-row nets
    land on J203 (zone-2 top-entry header, harness branch S02B) by a pin swap with the four arm-local J203 nets, and freeze6
    --renet carries a ratchet across that pin-map change. MODEL / CI inputs only; the CTRL J306 / J307 maps do not change."""

    SWAP = {('J203', '2'): 'EN_HFP', ('J203', '14'): 'EN_LIME3V3', ('J203', '15'): 'EN_LNB', ('J203', '18'): 'FAULT_HFP',
            ('J202', '5'): 'PG_BONI', ('J202', '7'): 'PTC_AUX', ('J202', '12'): 'PG_LNB', ('J202', '16'): 'FAULT_RTLA'}

    def test_graph_pins(self):
        graph = bg.load_graph()
        for (ref, pin), net in self.SWAP.items():
            got = next(p for p in graph[ref]['pins'] if str(p['number']) == pin)
            self.assertEqual((got['net'], got['name']), (net, net), (ref, pin))
        b2b = {p['number']: p.get('net') for p in graph['J209']['pins']}
        for contact, net in (('25', 'EN_HFP'), ('27', 'EN_LIME3V3'), ('29', 'EN_LNB'), ('31', 'FAULT_HFP')):
            self.assertEqual(b2b[contact], net)            # the J209 / J208 pin map does not change

    def test_freeze6_renet(self):
        import ast
        import types
        src = (bg.BASE / 'build/kicad/boards/PWR_B/freeze/freeze6.py').read_text(encoding='utf-8')
        fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == 'renet')
        self.assertIn("ap.add_argument('--renet'", src)
        self.assertIn("ap.add_argument('--first'", src)
        graph = {'J203': {'pins': [{'number': '2', 'net': 'EN_HFP'}, {'number': '3', 'net': 'FAULT_RTLB'}]}}
        fake_bg = types.ModuleType('board_gen')
        fake_bg.load_graph = lambda: graph
        ns = {'__builtins__': __builtins__}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'freeze6_renet', 'exec'), ns)
        it = lambda **k: types.SimpleNamespace(alive=True, **k)
        items = [it(kind='pad', ref='J203', pad='2', net='FAULT_RTLA'), it(kind='pad', ref='J203', pad='3', net='FAULT_RTLB'),
                 it(kind='track', net='FAULT_RTLA', src='router'), it(kind='via', net='EN_HFP', src='router'),
                 it(kind='track', net='FAULT_RTLB', src='router')]

        class Mdl:
            def __init__(self):
                self.items = items

            def remove(self, i):
                i.alive = False
        import sys
        sys.modules['board_gen'], saved = fake_bg, sys.modules.get('board_gen')
        try:
            changed, nets, gone = ns['renet'](Mdl())
        finally:
            if saved is not None:
                sys.modules['board_gen'] = saved
            else:
                del sys.modules['board_gen']
        self.assertEqual(changed, {'J203.2': ['FAULT_RTLA', 'EN_HFP']})
        self.assertEqual((nets, gone), ({'FAULT_RTLA', 'EN_HFP'}, 2))
        self.assertEqual([i.alive for i in items[2:]], [False, False, True])   # FAULT_RTLB keeps its copper


class PwrL6Place4ProbeA(unittest.TestCase):
    """W2 PWR-L6-PLACE fourth pass, probe A: the probe-A copper of PWR_B is locked pre-route copper of
    build/kicad/boards/PWR_B/route-planned-6l.json, kind 'link' (the nets keep their routing classes, freeze6 may complete
    them): the escapes of the J209 lower-row contacts 25-31 to J202, the I2C0_SDA link J209.41 - J203.9 and the outer-layer
    links of the power nets LNA4V5, VBUS_LABPORT and BIAS_CH3_PORT at the PWR1A width of the 2 oz outer copper. MODEL / CI
    inputs only; the CI route run is the check."""

    PLAN = bg.BASE / 'build/kicad/boards/PWR_B/route-planned-6l.json'

    def plan(self):
        if not self.PLAN.is_file():
            self.skipTest('no planned PWR_B copper on this branch')
        return bg.read_json(self.PLAN)

    def test_links_keep_their_classes(self):
        plan = self.plan()
        pro = bg.read_json(bg.BASE / 'build/kicad/boards/PWR_B/PWR_B.kicad_pro')['net_settings']
        cls = {p['pattern']: p['netclass'] for p in pro['netclass_patterns']}
        for net, d in plan['nets'].items():
            self.assertEqual(d['kind'], 'link', net)
            self.assertFalse(cls.get(net, '').startswith('SCRIPTED'), net)
        for net in ('LNA4V5', 'VBUS_LABPORT', 'BIAS_CH3_PORT'):
            if net in plan['nets']:
                self.assertEqual(cls.get(net), 'PWR1A', net)
        src = (bg.BASE / 'build/kicad/boards/PWR_B/freeze/freeze6.py').read_text(encoding='utf-8')
        self.assertIn("d.get('kind') != 'link'", src)          # freeze6 completes a net with a planned link

    def test_power_links_outer_layers_at_ipc_width(self):
        plan = self.plan()
        pro = bg.read_json(bg.BASE / 'build/kicad/boards/PWR_B/PWR_B.kicad_pro')['net_settings']
        width = {c['name']: c['track_width'] for c in pro['classes']}['PWR1A']
        self.assertAlmostEqual(width, 0.2, places=6)
        # IPC-2221 external (k 0.048, I = k dT^0.44 A^0.725, A in mil2), 2 oz finished outer foil 0.070 mm: MODEL
        area = (width / 0.0254) * (0.070 / 0.0254)
        i10 = 0.048 * 10 ** 0.44 * area ** 0.725
        i20 = 0.048 * 20 ** 0.44 * area ** 0.725
        for net, amps in (('LNA4V5', 1.209), ('VBUS_LABPORT', 0.825), ('BIAS_CH3_PORT', 0.339)):
            if net not in plan['nets']:
                continue
            self.assertGreaterEqual(i10, amps, net)
            self.assertGreaterEqual(i20, amps, net)
            for layer, w, a, b in plan['nets'][net]['tracks']:
                self.assertIn(layer, ('F.Cu', 'B.Cu'), net)
                self.assertGreaterEqual(w, width - 1e-9, net)

    def test_planned_vias_and_escape_band(self):
        plan = self.plan()
        spec = bg.read_json(bg.spec_path('PWR_B'))
        self.assertTrue(spec['j209_escape']['passed'])
        vias = [v for v in spec['pre_route']['vias'] if v['id'].startswith('PLV-')]
        self.assertEqual(len(vias), sum(len(d['vias']) for d in plan['nets'].values()))
        for v in vias:
            self.assertTrue(v['locked'])
            self.assertGreaterEqual(v['diameter_mm'] - v['drill_mm'], 0.3, v['id'])


class PwrL6CombinedFreezeTools(unittest.TestCase):
    """W2 PWR-L6-PLACE fourth pass, combined: freeze6 merges split remainders shorter than TINY back and lists short pieces
    whose end meets nothing exactly (the KiCad 10.0.7 track_dangling pattern of route run 43537055803); the PWR05A sub-class
    routes on all four routing layers at {outer 2 oz, inner 0.5 oz} widths of pcb/generated/stackup-6l.json."""

    def freeze6(self):
        path = bg.BASE / 'build/kicad/boards/PWR_B/freeze/freeze6.py'
        return path.read_text(encoding='utf-8')

    def test_merge_and_short_piece_hooks(self):
        src = self.freeze6()
        self.assertIn('def merge_remainders(', src)
        self.assertIn('bad += short_pieces(m)', src)
        self.assertIn("'merged_split_remainders'", src)

    def test_inner_class_layers_and_widths(self):
        doc = bg.read_json(bg.BASE / 'pcb/generated/stackup-6l.json')
        cls = doc['copper_options']['outer_2oz']['inner_classes']['PWR05A']
        pro = bg.read_json(bg.BASE / 'build/kicad/boards/PWR_B/PWR_B.kicad_pro')['net_settings']
        width = {c['name']: c['track_width'] for c in pro['classes']}
        self.assertEqual(width['PWR05A'], cls['inner_min_width_mm'])
        pats = {p['pattern']: p['netclass'] for p in pro['netclass_patterns']}
        for net in ('BIAS_CH3_PORT', 'BIAS_CH2', 'BIAS_CH3', 'LNB13V2', 'BIAS_SB_LNA'):
            self.assertEqual(pats.get(net), 'PWR05A', net)
        for net in ('LNA4V5', 'VBUS_LABPORT', 'E2_RTLB_SW', 'AUX12'):
            self.assertEqual(pats.get(net), 'PWR1A', net)
        spec = bg.read_json(bg.spec_path('PWR_B'))
        self.assertNotIn('PWR05A', spec['router'].get('class_layers', {}))


if __name__ == '__main__':
    unittest.main()
