"""Standard-library tests of pcb/fab_export.py (no KiCad needed).

Run from sat-receiver-audit: python3 -m unittest discover -s pcb/tests
The KiCad exports themselves (kicad-cli 10.0.7) run only in .github/workflows/sr-rx-pcb.yml; here the
normalisation, the JLC CPL/BOM conversion, the coverage checks, the PDF writer and the jobset are exercised on
synthetic KiCad-like outputs built from the committed board, and every committed fab/ set is checked against its
manifest.
"""
from __future__ import annotations

import copy
import csv
import io
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fab_export as fx  # noqa: E402

GERBER = '''%TF.GenerationSoftware,KiCad,Pcbnew,10.0.7-1.build*%
%TF.CreationDate,2026-11-07T10:20:31+00:00*%
%TF.ProjectId,ENC,454e432e6b696361645f706362,rev?*%
%TF.SameCoordinates,Original*%
%TF.FileFunction,Copper,L1,Top*%
%TF.FilePolarity,Positive*%
%FSLAX46Y46*%
G04 Gerber Fmt 4.6, Leading zero omitted, Abs format (unit mm)*
G04 Created by KiCad (PCBNEW 10.0.7-1.build) date 2026-11-07 10:20:31*
%MOMM*%
%LPD*%
G01*
%TO.N,GND*%
M02*
'''

DRILL = '''M48
; DRILL file KiCad 10.0.7 date 2026-11-07T10:20:31
; FORMAT={-:-/ absolute / metric / decimal}
; #@! TF.CreationDate,2026-11-07T10:20:31+00:00
; #@! TF.GenerationSoftware,Kicad,Pcbnew,10.0.7
; #@! TF.FileFunction,NonPlated,1,2,NPTH
FMAT,2
METRIC
T1C2.700
%
G90
G05
T1
X103.0Y-121.0
X121.0Y-103.0
M30
'''


def synthetic_raw(inputs):
    """KiCad-like raw exports of the committed board: one Gerber per layer, PTH/NPTH, maps, IPC-D-356, pos CSV."""
    board, parsed = inputs['board'], inputs['parsed']
    raw = {}
    for layer in fx.gerber_layers(inputs['spec']['layers']['copper']):
        function = 'Copper,L1,Top' if layer.endswith('.Cu') else 'Other,' + layer
        body = GERBER.replace('Copper,L1,Top', function)
        if not layer.endswith('.Cu'):
            body = body.replace('%TO.N,GND*%\n', '')
        raw[f'gerber/{board}-{layer.replace(".", "_")}.gbr'.replace('.gbr', '.g' + str(len(raw)))] = body.encode()
    raw[f'gerber/{board}-job.gbrjob'] = json.dumps({'Header': {'GenerationSoftware': {'Vendor': 'KiCad', 'Application': 'Pcbnew',
                                                                                     'Version': '10.0.7'},
                                                             'CreationDate': '2026-11-07T10:20:31+00:00'}}).encode()
    pth = [p for p in parsed.pads if p['kind'] == 'thru_hole' and p['drill']]
    npth = [p for p in parsed.pads if p['kind'] == 'np_thru_hole']
    vias = parsed.vias

    def drill(kind, items):
        hits = ''.join(f'X{x:.3f}Y{-y:.3f}\n' for x, y in items)
        return DRILL.replace('NonPlated,1,2,NPTH', kind).split('T1\nX')[0] + 'T1\n' + hits + 'M30\n'
    raw[f'drill/{board}-PTH.drl'] = drill('Plated,1,2,PTH', [(p['x'], p['y']) for p in pth] + [(v['x'], v['y']) for v in vias]).encode()
    raw[f'drill/{board}-NPTH.drl'] = drill('NonPlated,1,2,NPTH', [(p['x'], p['y']) for p in npth]).encode()
    raw[f'drill/{board}-PTH-drl_map.gbr'] = GERBER.replace('Copper,L1,Top', 'Drillmap').encode()
    raw[f'drill/{board}-NPTH-drl_map.gbr'] = GERBER.replace('Copper,L1,Top', 'Drillmap').encode()
    raw[f'{board}.ipc356'] = kicad_d356(board, parsed).encode()
    pos = io.StringIO()
    w = csv.writer(pos, lineterminator='\n')
    w.writerow(['Ref', 'Val', 'Package', 'PosX', 'PosY', 'Rot', 'Side'])
    for fp in parsed.footprints:
        if fp['ref'] and 'exclude_from_pos_files' not in fp['attr'] and 'dnp' not in fp['attr']:
            w.writerow([fp['ref'], fp['props'].get('Value', ''), fp['lib'].split(':')[-1], f'{fp["x"]:.4f}', f'{-fp["y"]:.4f}',
                        f'{fp["angle"]:.4f}', fp['side']])
    raw[f'assembly/{board}-pos-kicad.csv'] = pos.getvalue().encode()
    return raw


def kicad_d356_name(net, upper):
    """sanitize_d356_name of KiCad 10.0.7 pcbnew/exporters/export_d356.cpp (read 2026-11-07), written out again here
    so the fixture does not reuse the code under test."""
    return ''.join('?' if ord(ch) > 126 or not ('!' <= ch <= '~') else (ch.upper() if upper and 'a' <= ch <= 'z' else ch)
                   for ch in net)


def kicad_d356(board, parsed):
    """IPC-D-356 text as KiCad 10.0.7 write_D356_records writes it: pad and via records; a net keeps its upper-cased
    sanitised name when <= 14 characters, not N/C and unique, every other net gets an alias M + 4 base-36 digits
    declared as 'P  NNAME%-5.5s %-66.66s' (case-kept name, last 58 characters); records sorted by signal name."""
    records = [(p['net'] or '', p) for p in parsed.pads if p['layers']] + [(v['net'] or '', None) for v in parsed.vias]
    names = sorted({n for n, _p in records if n})
    count = {}
    for n in names:
        count[kicad_d356_name(n, True)] = count.get(kicad_d356_name(n, True), 0) + 1
    taken = {'N/C'} | set(count)
    canon = {n: kicad_d356_name(n, True) for n in names
             if len(kicad_d356_name(n, True)) <= 14 and kicad_d356_name(n, True) != 'N/C' and count[kicad_d356_name(n, True)] == 1}
    lines = ['C  IPC-D-356 Netlist generated by KiCad 10.0.7', 'C  Date: Sat Nov  7 10:20:31 2026',
             f'C  File: /tmp/sr-rx-fab-x/src/{board}.kicad_pcb', f'P  JOB   {board}', 'P  UNITS CUST 0', 'P  VER   IPC-D-356A']
    digits, index = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', 0
    for n in names:
        if n in canon:
            continue
        while True:
            alias = 'M' + ''.join(digits[(index // d) % 36] for d in (36 ** 3, 36 ** 2, 36, 1))
            index += 1
            if alias not in taken:
                taken.add(alias)
                break
        canon[n] = alias
        lines.append(f'P  NNAME{alias:<5.5} {kicad_d356_name(n, False)[-58:]:<66.66}')
    for net, p in sorted(records, key=lambda r: canon.get(r[0], 'N/C')):
        sig = canon.get(net, 'N/C')
        if p is None:
            lines.append(f'317{sig:<14.14}   {"VIA":<6.6} {"":<4.4}M')
            continue
        op = 327 if p['kind'] in ('smd', 'connect') else (367 if p['kind'] == 'np_thru_hole' else 317)
        lines.append(f'{op:03d}{sig:<14.14}   {p["ref"]:<6.6}{"-" if p["number"] else " "}{p["number"]:<4.4} ')
    lines.append('999')
    return '\n'.join(lines) + '\n'


def renamed_nets(inputs, names):
    """inputs with board nets renamed ({old: new}) on the pads and vias (the IPC-D-356 coverage reads only those)."""
    parsed = copy.copy(inputs['parsed'])
    parsed.pads = [dict(p, net=names.get(p['net'], p['net'])) for p in inputs['parsed'].pads]
    parsed.vias = [dict(v, net=names.get(v['net'], v['net'])) for v in inputs['parsed'].vias]
    return dict(inputs, parsed=parsed)


class NormalisationTests(unittest.TestCase):
    def test_gerber_dates_and_build_string(self):
        out = fx.normalise_gerber(GERBER)
        self.assertNotIn('CreationDate', out)
        self.assertIn('G04 Created by KiCad (PCBNEW 10.0.7)*\n', out)
        self.assertIn('%TF.GenerationSoftware,KiCad,Pcbnew,10.0.7*%', out)
        self.assertEqual(fx.normalise_gerber(out), out)
        self.assertFalse(fx.DATE_LEFT.search(out))

    def test_drill_dates(self):
        out = fx.normalise_drill(DRILL)
        self.assertIn('; DRILL file KiCad 10.0.7\n', out)
        self.assertNotIn('CreationDate', out)
        self.assertEqual(fx.drill_hits(out), 2)
        self.assertEqual(fx.normalise_drill(out), out)

    def test_gbrjob_and_ipc(self):
        job = fx.normalise_gbrjob(json.dumps({'Header': {'GenerationSoftware': {'Version': '10.0.7-x'}, 'CreationDate': 'now'}}))
        self.assertNotIn('CreationDate', job)
        self.assertIn('"Version": "10.0.7"', job)
        ipc = fx.normalise_ipc('C  Date: Sat Nov  7 10:20:31 2026\nC  File: /tmp/a b/x/ENC.kicad_pcb\nP  JOB   /tmp/q/ENC.kicad_pcb\n'
                               '327GND           ENC   -C\n', 'ENC')
        self.assertIn('C  Date: (normalised)', ipc)
        self.assertIn('P  JOB   ENC.kicad_pcb', ipc)
        self.assertNotIn('/tmp/', ipc)
        self.assertIn('327GND           ENC   -C', ipc)

    def test_leftover_dates_are_reported(self):
        bad = fx.leftovers({'gerber/x.gtl': b'G04 stamp 2026-11-07 10:20:31*\n', 'ok.csv': b'"a","b"\n'}, ('/tmp/q',))
        self.assertEqual([rel for rel, _ in bad], ['gerber/x.gtl'])
        self.assertTrue(fx.leftovers({'a.ipc356': b'P  JOB /tmp/q/x\n'}, ('/tmp/q',)))


class CplBomTests(unittest.TestCase):
    def test_cpl_columns_layers_and_raw_rotation(self):
        pos = b'Ref,Val,Package,PosX,PosY,Rot,Side\n"R2","1k","R_0603",101.0000,-102.5000,270.0000,bottom\n' \
              b'"R1","1k","R_0603",100.0000,-100.0000,90.0000,top\n'
        rows = fx.cpl(pos)
        self.assertEqual([r['Designator'] for r in rows], ['R1', 'R2'])
        self.assertEqual(rows[1]['Layer'], 'Bottom')
        self.assertEqual(rows[1]['Rotation'], '270.0000')
        text = fx.csv_bytes(fx.CPL_COLUMNS, rows).decode()
        self.assertTrue(text.startswith('"Designator","Mid X","Mid Y","Layer","Rotation"\n'))

    def test_enc_bom_has_instance_quantities_and_tbd_placeholder(self):
        # Follows the data (spec, report template, build/10-jlc-bom.csv): holds for the pilot placeholder and
        # after a board package replaces it with graph refs.
        inputs = fx.load_inputs('ENC')
        rows, used, dnp = fx.bom(inputs)
        spec, report = inputs['spec'], inputs['report']
        by_tref = {t: r for r in rows for t in r['Designator'].split(',')}
        q = report['build_quantity']['total']
        self.assertEqual(q, sum(int(i['qty']) for i in spec['instances']['list']) + int(spec['instances'].get('spares', 0)))
        jlc_by_ref = {d.strip(): r for r in inputs['jlc'] for d in r['Designator'].split(',') if d.strip()}
        want_used = set()
        for part in report['template']:
            row = by_tref[part['ref']]
            n = len(row['Designator'].split(','))
            self.assertEqual((row['Quantity'], row['Boards'], row['Total quantity']), (str(n), str(q), str(n * q)))
            if part['source'] == 'pilot_placeholder':
                self.assertEqual(row['LCSC Part #'], 'TBD')
                self.assertIn('pilot_placeholder', row['Note'])
                continue
            for inst in spec['instances']['list']:
                self.assertIn(f'{inst["id"]} {inst["refs"][part["ref"]]}', row['Graph refs'])
            jlc_rows = [jlc_by_ref.get(inst['refs'][part['ref']]) for inst in spec['instances']['list']]
            jlc = jlc_rows[0]
            if jlc is None:
                self.assertEqual(row['LCSC Part #'], 'TBD')
                self.assertIn('no build/10-jlc-bom.csv row', row['Note'])
                continue
            self.assertEqual((row['Comment'], row['LCSC Part #'], row['Footprint']),
                             (jlc['Comment'], jlc['LCSC Part #'] or 'TBD', jlc['Footprint']))
            want_used.update(r['Designator'] for r in jlc_rows if r)
        self.assertEqual(dnp, [])
        self.assertEqual(sorted(u['Designator'] for u in used), sorted(want_used))

    def test_rotation_offsets_are_empty_and_tbd(self):
        facts = {'R1': {'lib': 'L:R_0603'}, 'R2': {'lib': 'L:R_0603'}}
        rows = fx.rotation_offsets([{'Designator': 'R1'}, {'Designator': 'R2'}], facts)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['JLC rotation offset (deg)'], '')
        self.assertTrue(rows[0]['Status'].startswith('TBD'))


class PdfAndJobsetTests(unittest.TestCase):
    def test_pdf_is_deterministic_and_xref_is_exact(self):
        def make():
            pdf = fx.Pdf()
            ops = pdf.page()
            fx.Pdf.text(ops, 40, 500, 10, 'Board (ENC) 50 Ω ±10 %')
            fx.Pdf.line(ops, [(10, 10), (100, 10), (100, 100)], close=True)
            fx.Pdf.circle(ops, 50, 50, 5)
            pdf.page()
            return pdf.bytes('t', 's')
        a, b = make(), make()
        self.assertEqual(a, b)
        self.assertTrue(a.startswith(b'%PDF-1.4\n') and a.endswith(b'%%EOF\n'))
        self.assertNotIn(b'CreationDate', a)
        self.assertIn(b'(Board \\(ENC\\) 50 ohm +/-10 %)', a)
        start = int(re.search(rb'startxref\n(\d+)\n', a).group(1))
        self.assertTrue(a[start:].startswith(b'xref\n'))
        for n, off in enumerate(re.findall(rb'(\d{10}) 00000 n ', a), 1):
            self.assertTrue(a[int(off):].startswith(f'{n} 0 obj\n'.encode()), n)

    def test_jobset_matches_the_direct_export_settings(self):
        js = fx.jobset('ENC', 2)
        self.assertEqual([j['type'] for j in js['jobs']], ['pcb_export_gerbers', 'pcb_export_drill', 'pcb_export_ipcd356', 'pcb_export_pos'])
        g, d, _i, p = (j['settings'] for j in js['jobs'])
        self.assertEqual(g['layers'], fx.gerber_layers(2))
        self.assertTrue(g['use_x2_format'] and g['include_netlist_attributes'] and g['subtract_solder_mask_from_silk'])
        self.assertEqual((d['excellon.combine_pth_npth'], d['units'], d['map_format'], d['drill_origin']), (False, 'mm', 'gerberx2', 'abs'))
        self.assertEqual((p['format'], p['units'], p['side'], p['exclude_dnp'], p['use_drill_place_file_origin']),
                         ('csv', 'mm', 'both', True, False))
        self.assertEqual(fx.jobset('ENC', 2), js)
        self.assertEqual(g['output_filename'], 'gerber')
        self.assertEqual(fx.jobset_name('assembly/ENC-pos-kicad-all-pos.csv'), 'assembly/ENC-pos-kicad.csv')
        self.assertEqual(fx.gerber_layers(4)[:4], ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'])
        args = dict(fx.cli_jobs('ENC', Path('b.kicad_pcb'), Path('raw'), 2))
        self.assertNotIn('--no-x2', args['gerbers'])
        self.assertIn('--excellon-separate-th', args['drill'])
        self.assertIn('--exclude-dnp', args['pos'])


class NotesTests(unittest.TestCase):
    def test_four_layer_rf_board_gets_the_stackup_and_impedance_lines(self):
        inputs = fx.load_inputs('ENC')
        rf_net = next(n for n, v in inputs['netclasses']['nets'].items() if v['class'] == 'RF50')
        spec = json.loads(json.dumps(inputs['spec']))
        spec['layers']['copper'] = 4
        spec['instances']['list'][0]['nets']['ENC_A'] = rf_net
        rf = dict(inputs, spec=spec)
        stack = fx.stackup_record(rf)
        self.assertEqual((stack['id'], stack['copper_layers']), ('JLC04161H-7628', 4))
        files, cov, problems = fx.build_set(inputs, synthetic_raw(inputs), [])
        text = ' '.join(s for _k, s in fx.notes_lines(rf, stack, cov, fx.bom(inputs)[0]))
        cls = inputs['netclasses']['classes']['RF50']
        self.assertIn(f'w {cls["width_mm"]} mm, gap {cls["gap_mm"]} mm', text)
        self.assertIn('order WITH impedance control', text)
        self.assertIn('https://jlcpcb.com/impedance', text)
        plain = ' '.join(s for _k, s in fx.notes_lines(inputs, fx.stackup_record(inputs), cov, fx.bom(inputs)[0]))
        self.assertIn('order without impedance control', plain)
        self.assertIn(fx.STACKUP_2L['source'], plain)


class SyntheticSetTests(unittest.TestCase):
    """build_set on synthetic KiCad outputs of every committed board: coverage passes, mutations fail."""

    def boards(self):
        return fx.boards_with_outputs()

    def test_synthetic_set_is_complete_and_stable(self):
        for board in self.boards():
            with self.subTest(board=board):
                inputs = fx.load_inputs(board)
                raw = synthetic_raw(inputs)
                files, cov, problems = fx.build_set(inputs, raw, [])
                self.assertEqual(problems, [])
                self.assertTrue(cov['passed'])
                self.assertEqual(fx.leftovers(files, ('/tmp/sr-rx-fab-x',)), [])
                again, _c, _p = fx.build_set(fx.load_inputs(board), synthetic_raw(fx.load_inputs(board)), [])
                self.assertEqual(files, again)
                manifest = json.loads(files['manifest.json'])
                self.assertEqual(sorted(f['path'] for f in manifest['files']), sorted(set(files) - {'manifest.json'}))
                self.assertIn(fx.LABEL, files['README.md'].decode())
                self.assertIn(fx.LABEL.encode(), files[f'{board}-fab-notes.pdf'])
                for rel in (f'assembly/{board}-cpl-jlc.csv', f'assembly/{board}-bom-jlc.csv', f'{board}.kicad_jobset'):
                    self.assertIn(rel, files)

    def test_mutations_fail_coverage(self):
        board = 'ENC' if 'ENC' in self.boards() else (self.boards() or [None])[0]
        if board is None:
            self.skipTest('no committed board')
        inputs = fx.load_inputs(board)
        raw = synthetic_raw(inputs)
        first = next(fp['ref'] for fp in inputs['parsed'].footprints if fp['ref'] and 'exclude_from_pos_files' not in fp['attr'])
        pos = raw[f'assembly/{board}-pos-kicad.csv'].decode().splitlines()
        dup = dict(raw, **{f'assembly/{board}-pos-kicad.csv': ('\n'.join(pos + [l for l in pos if l.startswith(first + ',')]) + '\n').encode()})
        self.assertTrue(any('CPL' in p for p in fx.build_set(inputs, dup, [])[2]))
        net = sorted({p['net'] for p in inputs['parsed'].pads if p['net']})[0]
        ipc = '\n'.join(l for l in raw[f'{board}.ipc356'].decode().splitlines() if net not in l[3:17] and not l.startswith('P  NNAME'))
        self.assertTrue(any('IPC-D-356 lacks' in p for p in fx.build_set(inputs, dict(raw, **{f'{board}.ipc356': ipc.encode()}), [])[2]))
        layer = next(k for k in raw if k.startswith('gerber/') and not k.endswith('.gbrjob'))
        x1 = dict(raw, **{layer: raw[layer].replace(b'%TF.FileFunction,', b'G04 FileFunction,')})
        self.assertTrue(any('Gerber X2' in p for p in fx.build_set(inputs, x1, [])[2]))
        npth = f'drill/{board}-NPTH.drl'
        lost = dict(raw, **{npth: re.sub(rb'X[\d.]+Y-?[\d.]+\n', b'', raw[npth], count=1)})
        self.assertTrue(any('drill hits' in p for p in fx.build_set(inputs, lost, [])[2]))


class CommittedSetTests(unittest.TestCase):
    """Every committed fab/ set matches its manifest; while its board is current, the coverage holds again."""

    def test_committed_sets(self):
        found = 0
        for board in fx.boards_with_outputs():
            out = fx.fab_dir(board)
            if not (out / 'manifest.json').is_file():
                continue
            found += 1
            with self.subTest(board=board):
                manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
                have = fx.collect(out)
                self.assertEqual(sorted(f['path'] for f in manifest['files']), sorted(set(have) - {'manifest.json'}))
                for f in manifest['files']:
                    self.assertEqual(fx.sha(have[f['path']]), f['sha256'], f['path'])
                self.assertEqual(manifest['label'], fx.LABEL)
                self.assertEqual(manifest['problems'], [])
                self.assertTrue(manifest['coverage']['passed'])
                self.assertIn(fx.LABEL, have['README.md'].decode())
                inputs = fx.load_inputs(board)
                if manifest['inputs']['board_sha256'] != inputs['report']['board_sha256']:
                    continue  # stale: fab_export --check in sr-rx-pcb reports it
                cpl_rows = fx.cpl(have[f'assembly/{board}-pos-kicad.csv'])
                rows = list(csv.DictReader(io.StringIO(have[f'assembly/{board}-bom-jlc.csv'].decode())))
                cov, problems = fx.coverage(have, inputs, cpl_rows, rows)
                self.assertEqual(problems, [])
        if not found:
            self.skipTest('no committed fab/ set yet (sr-rx-pcb writes it)')


class IpcNetNameTests(unittest.TestCase):
    """IPC-D-356 coverage reads net names the way KiCad 10.0.7 writes them: upper-cased short names, NNAME aliases."""

    LONG = 'E1_CHG_INHIBIT_LOW'  # 18 characters, a graph net

    def test_alias_and_case_rules(self):
        text = ('P  NNAMEM0000 ' + f'{self.LONG:<66}\n'
                '317M0000            U1    -3    D0433PA00X+043110Y-047047X0787Y0787R270 S0\n'
                '327ENC_B?           U1    -4    A01X+043110Y-047047X0787Y0787R270 S0\n'
                '317GND              U1    -1    D0433PA00X+043110Y-047047X0787Y0787R270 S0\n'
                '367N/C              H1         MD1063UA00X+040551Y-047638X1063Y0000R000 S0\n')
        self.assertEqual(fx.ipc_nets(text), {self.LONG, 'ENC_B?', 'GND'})
        nets = {self.LONG, 'enc_b\u00b0', 'GND', 'Net_x', 'NET_X'}
        exp = fx.ipc_expected(nets)
        self.assertEqual(exp[self.LONG], ('alias', self.LONG))
        self.assertEqual(exp['enc_b\u00b0'], ('signal', 'ENC_B?'))
        self.assertEqual(exp['GND'], ('signal', 'GND'))
        self.assertEqual((exp['Net_x'], exp['NET_X']), (('alias', 'Net_x'), ('alias', 'NET_X')))
        self.assertEqual(fx.ipc_missing(sorted({self.LONG, 'enc_b\u00b0', 'GND'}), nets - {'Net_x', 'NET_X'}, text), [])
        self.assertEqual(fx.ipc_missing(['ENC_A'], {'ENC_A'}, text), ['ENC_A'])
        long_name = 'X' * 70
        self.assertEqual(fx.ipc_expected({long_name})[long_name], ('alias', 'X' * 58))

    def test_long_lowercase_and_colliding_nets_on_the_enc_board(self):
        inputs = fx.load_inputs('ENC')
        names = {'ENC_A': self.LONG, 'ENC_B': 'enc_b\u00b0', 'ENC_SW': 'Gnd'}  # 'Gnd' collides with GND: both aliased
        mod = renamed_nets(inputs, names)
        board = mod['board']
        raw = synthetic_raw(mod)
        ipc = raw[f'{board}.ipc356'].decode()
        self.assertIn('P  NNAMEM0000 ', ipc)
        self.assertNotIn('NNAME1', ipc)
        files, cov, problems = fx.build_set(mod, raw, [])
        self.assertEqual(problems, [])
        self.assertEqual(cov['ipc356']['missing'], [])
        self.assertEqual(sorted(cov['ipc356']['aliases'].values()), sorted(['GND', 'Gnd', self.LONG]))
        alias = next(a for a, n in cov['ipc356']['aliases'].items() if n == self.LONG)
        no_alias = '\n'.join(l for l in ipc.splitlines() if not l.startswith(f'P  NNAME{alias}')) + '\n'
        got = fx.build_set(mod, dict(raw, **{f'{board}.ipc356': no_alias.encode()}), [])[2]
        self.assertTrue(any('IPC-D-356 lacks' in p and self.LONG in p for p in got), got)
        no_short = '\n'.join(l for l in ipc.splitlines() if l[3:17].strip() != 'ENC_B?') + '\n'
        got = fx.build_set(mod, dict(raw, **{f'{board}.ipc356': no_short.encode()}), [])[2]
        self.assertTrue(any('IPC-D-356 lacks' in p and 'enc_b' in p for p in got), got)
        # the format of the earlier fixture ('P  NNAME1 <net>') is not what KiCad writes and does not resolve
        old = ipc.replace(f'P  NNAME{alias} ', 'P  NNAME1 ').replace(f'317{alias:<14}', f'317{"NNAME1":<14}')
        got = fx.build_set(mod, dict(raw, **{f'{board}.ipc356': old.encode()}), [])[2]
        self.assertTrue(any('IPC-D-356 lacks' in p and self.LONG in p for p in got), got)


if __name__ == '__main__':
    unittest.main()
