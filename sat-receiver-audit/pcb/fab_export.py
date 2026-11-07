#!/usr/bin/env python3
"""Fab set of one SR-RX board: Gerber X2, Excellon PTH/NPTH with map, IPC-D-356, JLC CPL and BOM, fab notes.

Run from any directory (KiCad 10.0.7 kicad-cli for the exports, as in the kicad/kicad:10.0.7 image):
  python3 pcb/fab_export.py --board ENC            write build/kicad/boards/ENC/fab/
  python3 pcb/fab_export.py --board ENC --check    regenerate in a temporary directory and compare byte for byte
                                                   with the committed fab/ (read-only; also runs the board's
                                                   kicad_jobset and compares its outputs with the direct export)
  python3 pcb/fab_export.py --board ALL [--check]  every pcb/boards/<B>.json with a committed board

Inputs: the committed, current board of pcb/board_gen.py (build/kicad/boards/<B>/<B>.kicad_pcb, its report.json
board_sha256 must match), the spec pcb/boards/<B>.json (instances, spares, layers, placeholders), the JLC rows of
build/10-jlc-bom.csv for the graph refs on the board, and the stackup of pcb/generated/netclasses.json.
KiCad stamps dates, absolute paths and its build string into the exports; those are normalised (rules listed in
manifest.json) so --check is byte-stable. The fab notes PDF is written by this script (standard library, no date).
Everything here is a CI/model output: NOT RELEASED, bench gates OPEN, CPL rotation offsets TBD at order time.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import board_gen  # noqa: E402  (stdlib at import time; pcbnew is not needed here)
import check_boards  # noqa: E402  (pure-Python .kicad_pcb reader)

BASE = board_gen.BASE
OUT_ROOT = board_gen.OUT_ROOT
JLC_BOM = BASE / 'build/10-jlc-bom.csv'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
KICAD_VERSION = board_gen.KICAD_VERSION
SCHEMA = 'srrx-fab-manifest-v1'
LABEL = 'NOT RELEASED: model/CI only; bench gates OPEN'
GENERATOR = 'pcb/fab_export.py'

# Read on 2026-11-07 (WebFetch of the pages named); quoted in manifest.json and the fab notes.
SOURCES = {
    'jlc_bom': {'url': 'https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly', 'read': '2026-11-07',
                'used': 'required BOM columns Comment, Designator, Footprint; .csv/.xls/.xlsx; designators are upper-cased by JLC'},
    'jlc_cpl': {'url': 'https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly', 'read': '2026-11-07',
                'used': 'CPL columns Designator, Mid X, Mid Y (mm, component centroid), Layer (Top/Bottom), Rotation (degrees, '
                        'positive counter-clockwise); the page names no coordinate origin and no rotation offsets'},
    'jlc_kicad': {'url': 'https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad', 'read': '2026-11-07',
                  'used': 'BOM Comment, Designator, Footprint, LCSC Part #; KiCad pos Ref/PosX/PosY/Rot/Side become '
                          'Designator/Mid X/Mid Y/Rotation/Layer'},
    'jlc_gerber': {'url': 'https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-8', 'read': '2026-11-07',
                   'used': 'layers F/B.Cu (+ inner), F/B.Paste, F/B.Silkscreen, F/B.Mask, Edge.Cuts; Protel extensions; '
                           'subtract soldermask from silkscreen; drill: alternate oval mode, absolute origin, millimetres, '
                           'decimal zeros, drill map recommended'},
    'jlc_capabilities': {'url': 'https://jlcpcb.com/capabilities/pcb-capabilities', 'read': '2026-11-07',
                         'used': 'FR-4; thickness 0.4/0.6/0.8/1.0/1.2/1.6/2.0 mm, tolerance +/-10 % for >= 1.0 mm; 2-layer '
                                 'outer copper 1/2/2.5/3.5/4.5 oz; impedance control listed from 4 layers, standard +/-10 %'},
    'kicad_cli': {'url': 'https://docs.kicad.org/10.0/en/cli/cli.html', 'read': '2026-11-07',
                  'used': 'options of pcb export gerbers/drill/ipcd356/pos and jobset run'},
    'kicad_jobs': {'url': 'https://gitlab.com/kicad/code/kicad/-/tree/10.0.7/common/jobs', 'read': '2026-11-07',
                   'used': 'jobset JSON keys: job_export_pcb_plot.cpp, job_export_pcb_gerber(s).cpp, job_export_pcb_drill.cpp, '
                           'job_export_pcb_pos.cpp, job_export_pcb_ipcd356.cpp, job.cpp, jobset.cpp, jobs_output_folder.cpp; '
                           'Gerber header lines: pcbnew/pcbplot.cpp AddGerberX2Header, common/plotters/GERBER_plotter.cpp'},
}

# The 2-layer stack: JLC standard FR-4 (no named stack-up; impedance control starts at 4 layers on the same page).
STACKUP_2L = {
    'id': 'JLC standard 2-layer FR-4',
    'material': 'FR-4',
    'copper_outer': '1 oz',
    'source': SOURCES['jlc_capabilities']['url'],
    'read': SOURCES['jlc_capabilities']['read'],
    'note': 'finished thickness from the spec layers.thickness_mm; JLC tolerance +/-10 % for boards >= 1.0 mm; '
            '1 oz outer copper is the project choice (build/15 rows Шари and Мідь і струмові класи)',
}

GERBER_EXT = re.compile(r'\.(gtl|gbl|g\d+|gts|gbs|gtp|gbp|gto|gbo|gm\d+|gbr)$')
DATE_LEFT = re.compile(r'(?<!\d)(19|20)\d\d-[01]\d-[0-3]\d[T ][0-2]\d:[0-5]\d|(?<!\d)[01]?\d/[0-3]?\d/(19|20)\d\d(?!\d)')
CPL_COLUMNS = ['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation']
BOM_COLUMNS = ['Comment', 'Designator', 'Footprint', 'LCSC Part #', 'Quantity', 'Boards', 'Total quantity', 'Mount',
               'Graph refs', 'Note']


class FabError(SystemExit):
    def __init__(self, message):
        super().__init__('fab_export: ' + message)


# --- small helpers -----------------------------------------------------------------------------------

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(data):
    return board_gen.sha256_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))


def canon_sha(value):
    return board_gen.sha256_bytes(board_gen.canonical(value))


def csv_bytes(header, rows):
    out = io.StringIO()
    w = csv.writer(out, quoting=csv.QUOTE_ALL, lineterminator='\n')
    w.writerow(header)
    for row in rows:
        w.writerow([row.get(h, '') for h in header])
    return out.getvalue().encode('utf-8')


def gerber_layers(copper):
    inner = [f'In{i}.Cu' for i in range(1, int(copper) - 1)]
    # canonical (file-format) layer names: kicad-cli accepts them, and the jobset reader resolves only these
    return (['F.Cu'] + inner + ['B.Cu', 'F.Paste', 'B.Paste', 'F.SilkS', 'B.SilkS', 'F.Mask', 'B.Mask', 'Edge.Cuts'])


def fab_dir(board):
    return OUT_ROOT / board / 'fab'


# --- normalisation of KiCad outputs ------------------------------------------------------------------

NORMALISATION = [
    'Gerber and drill-map Gerber: the %TF.CreationDate attribute line (optional in Gerber X2) is removed; '
    "'G04 Created by KiCad (...) date ...*' keeps the creator and loses the date",
    'Excellon: the \'; #@! TF.CreationDate\' line is removed; "; DRILL file KiCad ... date ..." loses the date',
    'Gerber job file (.gbrjob): Header.CreationDate is removed (JSON re-written with indent 2)',
    'IPC-D-356: comment-record dates are removed and file paths become the board file name',
    f'KiCad build strings that start with {KICAD_VERSION} become {KICAD_VERSION} in generator lines',
    'after normalisation no date/time stamp and no path of the export directory may remain (checked)',
]


def _version(line):
    if re.search(r'kicad|pcbnew', line, re.I):
        return re.sub(re.escape(KICAD_VERSION) + r'[^\s,*%)}\]"]*', KICAD_VERSION, line)
    return line


def normalise_gerber(text):
    out = []
    for line in text.splitlines():
        if re.match(r'^%TF\.CreationDate,.*\*%$', line) or re.match(r'^G04 #@! TF\.CreationDate,', line):
            continue
        line = re.sub(r'^(G04 Created by KiCad \(.*\)) date [^*]*\*$', r'\1*', line)
        out.append(_version(line))
    return '\n'.join(out) + '\n'


def normalise_drill(text):
    out = []
    for line in text.splitlines():
        if re.match(r'^;\s*#@!\s*TF\.CreationDate,', line):
            continue
        line = re.sub(r'^(; DRILL file .*?) date .*$', r'\1', line)
        out.append(_version(line))
    return '\n'.join(out) + '\n'


def normalise_gbrjob(text):
    doc = json.loads(text)
    header = doc.get('Header', {})
    header.pop('CreationDate', None)
    soft = header.get('GenerationSoftware', {})
    if str(soft.get('Version', '')).startswith(KICAD_VERSION):
        soft['Version'] = KICAD_VERSION
    return json.dumps(doc, ensure_ascii=False, indent=2) + '\n'


DATE_STAMP = re.compile(r'(?<!\d)(19|20)\d\d-[01]\d-[0-3]\d(?:[T ][0-2]\d:[0-5]\d(?::[0-5]\d(?:\.\d+)?)?(?:\s?[+-]\d\d:?\d\d|Z)?)?'
                        r'|(?<!\d)[01]?\d/[0-3]?\d/(19|20)\d\d(?!\d)')
TIME_OF_DAY = re.compile(r'(?<![\d.])[0-2]?\d:[0-5]\d(:[0-5]\d)?(\s*[AP]M)?(?![\d.])')


def normalise_ipc(text, board_name):
    """IPC-D-356: only comment (C) and job (P JOB) records carry dates and paths; test records stay as written."""
    out = []
    for line in text.splitlines():
        if line.startswith('C') or line.startswith('P  JOB'):
            line = re.sub(r'(?:[A-Za-z]:)?[/\\][^*\n]*?[/\\]([^/\\*\n]+?\.kicad_pcb)', r'\1', line)
            if re.search(r'\bdate\b', line, re.I):
                line = re.sub(r'(?i)(\bdate\b\s*:?\s*).*$', r'\1(normalised)', line)
            line = TIME_OF_DAY.sub('', DATE_STAMP.sub('', line)).rstrip()
        out.append(_version(line))
    return '\n'.join(out) + '\n'


def normalise(rel, data, board_name):
    """Normalised bytes of one raw KiCad output (rel = path inside fab/)."""
    text = data.decode('utf-8')
    if rel.endswith('.gbrjob'):
        return normalise_gbrjob(text).encode('utf-8')
    if GERBER_EXT.search(rel):
        return normalise_gerber(text).encode('utf-8')
    if rel.endswith('.drl'):
        return normalise_drill(text).encode('utf-8')
    if rel.endswith('.ipc356'):
        return normalise_ipc(text, board_name).encode('utf-8')
    return text.replace('\r\n', '\n').encode('utf-8')


def leftovers(files, temp_markers=()):
    """[(file, line)] of date stamps or export paths that survived normalisation."""
    bad = []
    for rel, data in sorted(files.items()):
        for line in data.decode('utf-8', errors='replace').splitlines():
            if DATE_LEFT.search(line):
                bad.append((rel, line[:160]))
            elif any(m and m in line for m in temp_markers):
                bad.append((rel, line[:160]))
    return bad


# --- KiCad exports -----------------------------------------------------------------------------------

def cli_jobs(board, pcb, raw, copper):
    """(name, kicad-cli argument list) of the direct exports; raw is the output root."""
    return [
        ('gerbers', ['pcb', 'export', 'gerbers', '--output', str(raw / 'gerber') + os.sep, '--layers',
                     ','.join(gerber_layers(copper)), '--subtract-soldermask', '--precision', '6', str(pcb)]),
        ('drill', ['pcb', 'export', 'drill', '--output', str(raw / 'drill') + os.sep, '--format', 'excellon',
                   '--drill-origin', 'absolute', '--excellon-zeros-format', 'decimal', '--excellon-oval-format', 'alternate',
                   '--excellon-units', 'mm', '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2', str(pcb)]),
        ('ipcd356', ['pcb', 'export', 'ipcd356', '--output', str(raw / f'{board}.ipc356'), str(pcb)]),
        ('pos', ['pcb', 'export', 'pos', '--output', str(raw / 'assembly' / f'{board}-pos-kicad.csv'), '--side', 'both',
                 '--format', 'csv', '--units', 'mm', '--exclude-dnp', str(pcb)]),
    ]


def shown(args, temp):
    out = []
    for a in args:
        a = str(a)
        if str(temp) in a:
            a = a.replace(str(temp), '<temp>').replace('\\', '/')
        out.append(a)
    return out


def kicad_cli():
    cli = shutil.which('kicad-cli')
    if not cli:
        raise FabError('kicad-cli not found (KiCad 10.0.7, kicad/kicad:10.0.7 image)')
    return cli


def run(cmd, timeout=600, cwd=None):
    proc = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=timeout, cwd=cwd,
                          stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        raise FabError(f'{" ".join(str(c) for c in cmd[1:4])} failed ({proc.returncode}):\n{proc.stdout}{proc.stderr}')
    return proc


def stage_sources(board, temp):
    """Copy the board, project and footprint table to temp/src (KiCad never writes into the committed board dir)."""
    src = Path(temp) / 'src'
    src.mkdir(parents=True, exist_ok=True)
    for name in (f'{board}.kicad_pcb', f'{board}.kicad_pro', 'fp-lib-table'):
        path = OUT_ROOT / board / name
        if path.is_file():
            shutil.copyfile(path, src / name)
    return src


def collect(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(Path(root).rglob('*')) if p.is_file()}


def export_raw(board, copper, temp):
    cli = kicad_cli()
    version = run([cli, 'version']).stdout.strip()
    if not version.startswith(KICAD_VERSION):
        raise FabError(f'kicad-cli {version} found, {KICAD_VERSION} required')
    src = stage_sources(board, temp)
    raw = Path(temp) / 'raw'
    for sub in ('gerber', 'drill', 'assembly'):
        (raw / sub).mkdir(parents=True, exist_ok=True)
    commands = []
    for name, args in cli_jobs(board, src / f'{board}.kicad_pcb', raw, copper):
        run([cli] + args)
        commands.append({'job': name, 'argv': ['kicad-cli'] + shown(args, temp)})
    return collect(raw), commands


# --- the kicad_jobset (manual reproduction of the raw exports) ---------------------------------------

def _id(board, name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'https://github.com/lizbeth307/lizbeth307/sr-rx/fab/{board}/{name}'))


def jobset(board, copper, output_path='${KIPRJMOD}/fab-jobset-raw'):
    """KiCad 10.0.7 jobset with the same export settings as cli_jobs (keys from common/jobs/*.cpp at 10.0.7)."""
    plot_common = {'layers_to_include_on_all_layers': [], 'mirror': False, 'black_and_white': False, 'negative': False,
                   'plot_footprint_values': True, 'plot_ref_des': True, 'hide_dnp_footprints_on_fab_layers': False,
                   'sketch_dnp_footprints_on_fab_layers': True, 'crossout_dnp_footprints_on_fab_layers': True,
                   'sketch_pads_on_fab_layers': False, 'plot_pad_numbers': False, 'plot_drawing_sheet': False,
                   'subtract_solder_mask_from_silk': True, 'use_drill_origin': False,
                   'drawing_sheet': '', 'check_zones': False, 'variant': ''}
    plot_common['drill_shape'] = 'none'  # Gerber: no drill marks on copper
    jobs = [
        {'id': _id(board, 'gerbers'), 'type': 'pcb_export_gerbers', 'description': 'Gerber X2 (netlist attributes, Protel extensions)',
         # plot jobs register their output path as output_filename (JOB(type, false)); the plotter uses it as the folder
         'settings': {'description': '', 'output_filename': 'gerber', 'layers': gerber_layers(copper), **plot_common,
                      'include_netlist_attributes': True, 'use_x2_format': True, 'disable_aperture_macros': False,
                      'use_protel_file_extension': True, 'precision': 6, 'create_gerber_job_file': True}},
        {'id': _id(board, 'drill'), 'type': 'pcb_export_drill', 'description': 'Excellon PTH/NPTH, mm, decimal, Gerber X2 map',
         'settings': {'description': '', 'output_dir': 'drill', 'excellon.mirror_y': False, 'excellon.minimal_header': False,
                      'excellon.combine_pth_npth': False, 'excellon.oval_drill_route': False, 'format': 'excellon',
                      'drill_origin': 'abs', 'units': 'mm', 'zero_format': 'decimal', 'generate_map': True,
                      'generate_tenting': False, 'map_format': 'gerberx2', 'gerber_precision': 6, 'generate_report': False,
                      'report_filename': ''}},
        {'id': _id(board, 'ipcd356'), 'type': 'pcb_export_ipcd356', 'description': 'IPC-D-356 netlist',
         'settings': {'description': '', 'output_filename': f'{board}.ipc356'}},
        {'id': _id(board, 'pos'), 'type': 'pcb_export_pos', 'description': 'Positions, CSV, mm, both sides, DNP excluded',
         'settings': {'description': '', 'output_filename': f'assembly/{board}-pos-kicad.csv', 'use_drill_place_file_origin': False,
                      'smd_only': False, 'exclude_footprints_with_th': False, 'exclude_dnp': True, 'exclude_bom': False,
                      'negate_bottom_x': False, 'single_file': True, 'gerber_board_edge': True, 'side': 'both', 'units': 'mm',
                      'format': 'csv', 'variant': ''}},
    ]
    outputs = [{'id': _id(board, 'folder'), 'type': 'folder', 'description': 'raw KiCad exports (dates not normalised)',
                'only': [], 'settings': {'output_path': output_path}}]
    return {'jobs': jobs, 'meta': {'version': 1}, 'outputs': outputs}


def jobset_name(rel):
    """The direct-export name of a jobset output: a jobset pos job appends '-all-pos' to a both-sides file."""
    return re.sub(r'-all-pos(\.csv)$', r'\1', rel)


def jobset_check(board, copper, direct, temp, raw_copy=None):
    """Run the jobset on a staged copy and compare its normalised outputs with the direct export."""
    cli = kicad_cli()
    src = stage_sources(board, Path(temp) / 'jobset')
    out = Path(temp) / 'jobset-out'
    path = src / f'{board}.kicad_jobset'
    path.write_text(json.dumps(jobset(board, copper, str(out)), indent=2) + '\n', encoding='utf-8')
    run([cli, 'jobset', 'run', '--stop-on-error', '--file', str(path), str(src / f'{board}.kicad_pro')], timeout=900)
    produced = collect(out)
    if raw_copy:  # raw jobset outputs next to the direct ones in the CI artifact
        for rel, data in produced.items():
            dest = Path(raw_copy) / f'{board}-jobset' / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
    got = {jobset_name(rel): normalise(jobset_name(rel), data, board) for rel, data in produced.items()}
    want = {rel: normalise(rel, data, board) for rel, data in direct.items()}
    problems = []
    for rel in sorted(set(got) | set(want)):
        if rel not in got:
            problems.append(f'jobset did not write {rel}')
        elif rel not in want:
            problems.append(f'jobset wrote {rel}, the direct export did not')
        elif got[rel] != want[rel]:
            problems.append(f'jobset output {rel} differs from the direct export')
    return problems


# --- board facts, BOM, CPL ---------------------------------------------------------------------------

def load_inputs(board):
    spec = read_json(board_gen.spec_path(board))
    out = OUT_ROOT / board
    pcb, report_path = out / f'{board}.kicad_pcb', out / 'report.json'
    if not pcb.is_file() or not report_path.is_file():
        raise FabError(f'{board}: no committed board or report.json (route it with [pcb-route {board}])')
    report = read_json(report_path)
    if report.get('board_sha256') != board_gen.sha256_file(pcb):
        raise FabError(f'{board}: {pcb.name} differs from report.json board_sha256; run pcb/board_gen.py --check first')
    parsed = check_boards.load_board(pcb)
    with JLC_BOM.open(encoding='utf-8', newline='') as fh:
        jlc = list(csv.DictReader(fh))
    return {'board': board, 'spec': spec, 'report': report, 'pcb': pcb, 'parsed': parsed, 'jlc': jlc,
            'graph': board_gen.load_graph(), 'netclasses': read_json(NETCLASSES)}


def footprint_facts(parsed):
    """Board footprints that carry a reference and pads: side, mount, pos/BOM flags."""
    out = {}
    for fp in parsed.footprints:
        if not fp['ref']:
            continue
        attr = set(fp['attr'])
        out[fp['ref']] = {'side': 'Top' if fp['side'] == 'top' else 'Bottom',
                          'mount': 'SMD' if 'smd' in attr else ('THT' if 'through_hole' in attr else 'other'),
                          'pos': 'exclude_from_pos_files' not in attr and 'dnp' not in attr,
                          'bom': 'exclude_from_bom' not in attr and 'dnp' not in attr,
                          'lib': fp['lib'], 'x': fp['x'], 'y': fp['y']}
    return out


def jlc_key(row):
    """The JLC columns of a build/10-jlc-bom.csv row (stock and alternates change with every snapshot: not used)."""
    return (row['Comment'], row['Footprint'], row['LCSC Part #'], row['Mount'])


def bom(inputs):
    """JLC BOM rows (template designators) and the build/10-jlc-bom.csv rows they come from."""
    spec, report, graph = inputs['spec'], inputs['report'], inputs['graph']
    facts = footprint_facts(inputs['parsed'])
    boards = int(report['build_quantity']['total'])
    by_ref = {}
    for row in inputs['jlc']:
        for d in row['Designator'].split(','):
            if d.strip():
                by_ref[d.strip()] = row
    placeholders = {p['ref']: p for p in spec['parts'] if p['source'] == 'pilot_placeholder'}
    groups, used_rows, dnp = {}, [], []
    for part in report['template']:
        tref = part['ref']
        fact = facts.get(tref)
        if fact is None:
            raise FabError(f'template ref {tref} has no footprint on the board')
        if not fact['bom']:
            dnp.append(tref)
            continue
        if part['source'] == 'pilot_placeholder':
            p = placeholders[tref]
            key = ('placeholder', tref)
            groups[key] = {'Comment': part['value'], 'Footprint': part['fpid'].split(':', 1)[1], 'LCSC Part #': 'TBD',
                           'Mount': fact['mount'], 'refs': [tref], 'graph': {tref: []},
                           'Note': f'TBD: pilot_placeholder, no graph ref and no MPN yet; replaced by {p["replaced_by"]}'}
            continue
        per = []
        for inst in spec['instances']['list']:
            gref = inst['refs'][tref]
            comp = graph.get(gref, {})
            if comp.get('dnp'):
                raise FabError(f'{gref} is DNP in the graph but placed on the board template {tref}')
            per.append((inst['id'], gref, by_ref.get(gref)))
        keys = {jlc_key(r) if r else None for _i, _g, r in per}
        if len(keys) != 1:
            raise FabError(f'{tref}: instances map to different JLC rows {sorted(map(str, keys))}; one template cannot serve both')
        row = per[0][2]
        if row is None:
            key = ('nojlc', part['value'], part['fpid'])
            entry = groups.setdefault(key, {'Comment': part['value'], 'Footprint': part['fpid'].split(':', 1)[1], 'LCSC Part #': 'TBD',
                                            'Mount': fact['mount'], 'refs': [], 'graph': {},
                                            'Note': 'TBD: no build/10-jlc-bom.csv row (design/parts/parts.json tbd or not a PCB mount)'})
        else:
            key = ('jlc',) + jlc_key(row)
            entry = groups.setdefault(key, {'Comment': row['Comment'], 'Footprint': row['Footprint'],
                                            'LCSC Part #': row['LCSC Part #'] or 'TBD', 'Mount': row['Mount'], 'refs': [], 'graph': {},
                                            'Note': '' if row['LCSC Part #'] else 'TBD: build/10-jlc-bom.csv row has no LCSC code'})
            used_rows.append({k: row[k] for k in ('Board', 'Comment', 'Designator', 'Footprint', 'LCSC Part #', 'Mount')})
        entry['refs'].append(tref)
        entry['graph'][tref] = [(iid, gref) for iid, gref, _r in per]
    rows = []
    for entry in groups.values():
        refs = sorted(entry['refs'], key=board_gen.sort_ref)
        graph_refs = '; '.join(f'{t}: ' + (', '.join(f'{iid} {g}' for iid, g in entry['graph'][t]) or 'none')
                               for t in refs)
        rows.append({'Comment': entry['Comment'], 'Designator': ','.join(refs), 'Footprint': entry['Footprint'],
                     'LCSC Part #': entry['LCSC Part #'], 'Quantity': str(len(refs)), 'Boards': str(boards),
                     'Total quantity': str(len(refs) * boards), 'Mount': entry['Mount'], 'Graph refs': graph_refs,
                     'Note': entry['Note']})
    rows.sort(key=lambda r: (r['Mount'], board_gen.sort_ref(r['Designator'].split(',')[0])))
    used_rows.sort(key=lambda r: (r['Board'], r['Designator']))
    unique = [dict(t) for t in sorted({tuple(sorted(r.items())) for r in used_rows})]
    return rows, unique, sorted(dnp, key=board_gen.sort_ref)


def cpl(pos_bytes):
    """JLC CPL rows from the KiCad CSV position file: raw rotation, Layer Top/Bottom, mm as KiCad wrote them."""
    rows = list(csv.DictReader(io.StringIO(pos_bytes.decode('utf-8'))))
    need = {'Ref', 'PosX', 'PosY', 'Rot', 'Side'}
    if rows and not need <= set(rows[0]):
        raise FabError(f'KiCad position file columns {sorted(rows[0])} lack {sorted(need - set(rows[0]))}')
    out = []
    for r in rows:
        side = r['Side'].strip().lower()
        if side not in ('top', 'bottom'):
            raise FabError(f'position file side {r["Side"]!r} of {r["Ref"]}')
        out.append({'Designator': r['Ref'].strip(), 'Mid X': r['PosX'].strip(), 'Mid Y': r['PosY'].strip(),
                    'Layer': 'Top' if side == 'top' else 'Bottom', 'Rotation': r['Rot'].strip(),
                    '_value': r.get('Val', ''), '_package': r.get('Package', '')})
    out.sort(key=lambda r: (r['Layer'] != 'Top', board_gen.sort_ref(r['Designator'])))
    return out


def rotation_offsets(cpl_rows, facts):
    rows = []
    for fpid in sorted({facts[r['Designator']]['lib'] for r in cpl_rows if r['Designator'] in facts}):
        refs = sorted((r['Designator'] for r in cpl_rows if facts.get(r['Designator'], {}).get('lib') == fpid), key=board_gen.sort_ref)
        rows.append({'Footprint': fpid, 'Designators': ','.join(refs), 'JLC rotation offset (deg)': '',
                     'JLC centroid offset (mm)': '',
                     'Status': 'TBD: check every part in the JLC assembly viewer at order time (builder step); '
                               'JLC rotation and centroid conventions are not read and are not checked in CI'})
    return rows


def instances_rows(spec, report):
    rows = []
    for inst in spec['instances']['list']:
        for tref, gref in sorted(inst['refs'].items(), key=lambda kv: board_gen.sort_ref(kv[0])):
            rows.append({'Instance': inst['id'], 'Placement': inst.get('placement', ''), 'Qty': str(inst['qty']),
                         'Template ref': tref, 'Graph ref': gref or 'none (pilot_placeholder)'})
    spares = int(spec['instances'].get('spares', 0))
    if spares:
        rows.append({'Instance': 'spare', 'Placement': '', 'Qty': str(spares), 'Template ref': '*',
                     'Graph ref': 'none (spare copy of the same design: ' + spec['instances'].get('spares_source', '') + ')'})
    return rows


# --- coverage checks ---------------------------------------------------------------------------------

def ipc_nets(text):
    """Net names of the IPC-D-356 test records (317/327/367), aliases (P NNAME) resolved; N/C dropped."""
    alias, nets = {}, set()
    for line in text.splitlines():
        m = re.match(r'^P\s+(NNAME\d+)\s+(.*\S)\s*$', line)
        if m:
            alias[m.group(1)] = m.group(2)
    for line in text.splitlines():
        if line[:3] in ('317', '327', '367') and len(line) >= 17:
            net = line[3:17].strip()
            net = alias.get(net, net)
            if net and net != 'N/C':
                nets.add(net)
    return nets


def drill_hits(text):
    return sum(1 for line in text.splitlines() if re.match(r'^X-?[\d.]+Y-?[\d.]+', line))


def coverage(files, inputs, cpl_rows, bom_rows):
    board, parsed = inputs['board'], inputs['parsed']
    facts = footprint_facts(parsed)
    problems, info = [], {}
    # CPL: every placed footprint (not excluded from position files, not DNP) exactly once, on its side.
    want = {r: f for r, f in facts.items() if f['pos']}
    seen = {}
    for r in cpl_rows:
        seen.setdefault(r['Designator'], []).append(r['Layer'])
    for ref in sorted(set(want) | set(seen), key=board_gen.sort_ref):
        if ref not in seen:
            problems.append(f'CPL lacks {ref}')
        elif ref not in want:
            problems.append(f'CPL lists {ref}, which is not a placed footprint')
        elif seen[ref] != [want[ref]['side']]:
            problems.append(f'CPL has {ref} as {seen[ref]}, the board has it once on {want[ref]["side"]}')
    by_side = {}
    for ref, f in sorted(want.items()):
        by_side.setdefault(f['side'], {}).setdefault(f['mount'], 0)
        by_side[f['side']][f['mount']] += 1
    info['cpl'] = {'rows': len(cpl_rows), 'placed_by_side_and_mount': by_side,
                   'smd_refs_once_per_side': not any('CPL' in p for p in problems)}
    # BOM: every BOM footprint exactly once; designators equal the CPL designators.
    refs = [d for r in bom_rows for d in r['Designator'].split(',')]
    want_bom = sorted((r for r, f in facts.items() if f['bom']), key=board_gen.sort_ref)
    if sorted(refs, key=board_gen.sort_ref) != want_bom:
        problems.append(f'BOM designators {sorted(refs)} differ from the board BOM footprints {want_bom}')
    if sorted(set(refs)) != sorted(seen):
        problems.append(f'BOM designators {sorted(set(refs))} differ from the CPL designators {sorted(seen)}')
    info['bom'] = {'rows': len(bom_rows), 'designators': len(refs),
                   'tbd': sorted((r['Designator'] for r in bom_rows if r['LCSC Part #'] == 'TBD'), key=board_gen.sort_ref),
                   'boards': int(inputs['report']['build_quantity']['total'])}
    # IPC-D-356: every net that has a pad on the board.
    pad_nets = sorted({p['net'] for p in parsed.pads if p['net'] and not p['net'].startswith('unconnected-')})
    ipc = files.get(f'{board}.ipc356', b'').decode('utf-8', errors='replace')
    got = ipc_nets(ipc)
    missing = sorted(set(pad_nets) - got)
    if missing:
        problems.append(f'IPC-D-356 lacks nets {missing}')
    info['ipc356'] = {'board_pad_nets': pad_nets, 'ipc_nets': sorted(got), 'missing': missing}
    # Gerber X2: one file per requested layer, each with X2 file attributes; copper with net attributes.
    gerbers = {rel: data.decode('utf-8', errors='replace') for rel, data in files.items()
               if rel.startswith('gerber/') and GERBER_EXT.search(rel)}
    layers = gerber_layers(inputs['spec']['layers']['copper'])
    if len(gerbers) != len(layers):
        problems.append(f'{len(gerbers)} Gerber files for {len(layers)} layers')
    functions = {}
    for rel, text in sorted(gerbers.items()):
        m = re.search(r'^%TF\.FileFunction,([^*]*)\*%$', text, re.M)
        if not m or f'%TF.GenerationSoftware,KiCad,Pcbnew,{KICAD_VERSION}*%' not in text:
            problems.append(f'{rel}: no Gerber X2 file attributes (%TF.FileFunction / %TF.GenerationSoftware)')
            continue
        functions[rel] = m.group(1)
        if m.group(1).startswith('Copper') and '%TO.N,' not in text:
            problems.append(f'{rel}: copper layer without X2 net attributes (%TO.N)')
    if not any(rel.endswith('.gbrjob') for rel in files):
        problems.append('no Gerber job file (.gbrjob)')
    info['gerber_x2'] = {'files': functions}
    # Drill: PTH and NPTH files and their maps; hits = plated pads + vias / non-plated pads.
    pth_pads = sum(1 for p in parsed.pads if p['kind'] == 'thru_hole' and p['drill'])
    npth_pads = sum(1 for p in parsed.pads if p['kind'] == 'np_thru_hole')
    drills = {rel: data.decode('utf-8', errors='replace') for rel, data in files.items() if rel.endswith('.drl')}
    pth = [t for rel, t in drills.items() if re.search(r'TF\.FileFunction,Plated', t)]
    npth = [t for rel, t in drills.items() if re.search(r'TF\.FileFunction,NonPlated', t)]
    hits = {'pth_file': len(pth), 'npth_file': len(npth), 'pth_hits': sum(map(drill_hits, pth)),
            'npth_hits': sum(map(drill_hits, npth)), 'board_pth_pads': pth_pads, 'board_vias': len(parsed.vias),
            'board_npth_pads': npth_pads,
            'maps': sorted(rel for rel in files if rel.startswith('drill/') and rel.endswith('.gbr'))}
    if len(pth) != 1 or len(npth) != 1:
        problems.append(f'expected one PTH and one NPTH Excellon file, found {len(pth)} / {len(npth)}')
    if hits['pth_hits'] != pth_pads + len(parsed.vias) or hits['npth_hits'] != npth_pads:
        problems.append(f'drill hits {hits["pth_hits"]} PTH / {hits["npth_hits"]} NPTH differ from the board '
                        f'{pth_pads} plated pads + {len(parsed.vias)} vias / {npth_pads} NPTH pads')
    if len(hits['maps']) != 2:
        problems.append(f'expected a PTH and an NPTH drill map, found {hits["maps"]}')
    info['drill'] = hits
    info['passed'] = not problems
    return info, problems


# --- fab notes PDF (standard library, deterministic) -------------------------------------------------

def pdf_text(s):
    s = (s.replace('±', '+/-').replace('Ω', 'ohm').replace('Ω', 'ohm').replace('°', ' deg')
         .replace('≤', '<=').replace('≥', '>=').replace('–', '-').replace('—', '-').replace('×', 'x'))
    s = s.encode('ascii', 'replace').decode('ascii')
    return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def f2(v):
    out = f'{v:.2f}'
    return '0.00' if out == '-0.00' else out


class Pdf:
    """Minimal PDF 1.4: A4 landscape pages, Helvetica / Helvetica-Bold, uncompressed streams, no dates."""
    W, H = 842, 595

    def __init__(self):
        self.pages = []

    def page(self):
        self.pages.append([])
        return self.pages[-1]

    @staticmethod
    def text(ops, x, y, size, s, bold=False):
        ops.append(f'BT /{"F2" if bold else "F1"} {f2(size)} Tf {f2(x)} {f2(y)} Td ({pdf_text(s)}) Tj ET')

    @staticmethod
    def line(ops, pts, width=0.6, close=False):
        if len(pts) < 2:
            return
        path = [f'{f2(pts[0][0])} {f2(pts[0][1])} m'] + [f'{f2(x)} {f2(y)} l' for x, y in pts[1:]]
        ops.append(f'{f2(width)} w ' + ' '.join(path) + (' h S' if close else ' S'))

    @staticmethod
    def circle(ops, cx, cy, r, width=0.6):
        k = 0.5523 * r
        ops.append(f'{f2(width)} w {f2(cx + r)} {f2(cy)} m '
                   f'{f2(cx + r)} {f2(cy + k)} {f2(cx + k)} {f2(cy + r)} {f2(cx)} {f2(cy + r)} c '
                   f'{f2(cx - k)} {f2(cy + r)} {f2(cx - r)} {f2(cy + k)} {f2(cx - r)} {f2(cy)} c '
                   f'{f2(cx - r)} {f2(cy - k)} {f2(cx - k)} {f2(cy - r)} {f2(cx)} {f2(cy - r)} c '
                   f'{f2(cx + k)} {f2(cy - r)} {f2(cx + r)} {f2(cy - k)} {f2(cx + r)} {f2(cy)} c S')

    def bytes(self, title, subject):
        objs = [b'<< /Type /Catalog /Pages 2 0 R >>', None,
                b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
                b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>',
                f'<< /Title ({pdf_text(title)}) /Subject ({pdf_text(subject)}) /Producer ({GENERATOR}) >>'.encode('ascii')]
        kids = []
        for ops in self.pages:
            stream = ('\n'.join(ops) + '\n').encode('ascii')
            page_no = len(objs) + 1
            kids.append(f'{page_no} 0 R')
            objs.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.W} {self.H}] '
                        f'/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {page_no + 1} 0 R >>'.encode('ascii'))
            objs.append(b'<< /Length ' + str(len(stream)).encode('ascii') + b' >>\nstream\n' + stream + b'endstream')
        objs[1] = f'<< /Type /Pages /Kids [{" ".join(kids)}] /Count {len(kids)} >>'.encode('ascii')
        out = bytearray(b'%PDF-1.4\n')
        offsets = []
        for i, body in enumerate(objs, 1):
            offsets.append(len(out))
            out += f'{i} 0 obj\n'.encode('ascii') + body + b'\nendobj\n'
        xref = len(out)
        out += f'xref\n0 {len(objs) + 1}\n0000000000 65535 f \n'.encode('ascii')
        for off in offsets:
            out += f'{off:010d} 00000 n \n'.encode('ascii')
        out += f'trailer\n<< /Size {len(objs) + 1} /Root 1 0 R /Info 5 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode('ascii')
        return bytes(out)


def stackup_record(inputs):
    spec, nc = inputs['spec'], inputs['netclasses']
    copper = int(spec['layers']['copper'])
    if copper == 4:
        st = nc['stackup']
        return {'id': st['id'], 'copper_layers': 4, 'thickness_mm': st['board_thickness_mm'], 'source': st['source'],
                'read': st['read'], 'layers': st['layers'], 'note': st.get('note', ''),
                'via': 'pcb/generated/netclasses.json stackup (pcb/stackup.py)'}
    return {**STACKUP_2L, 'copper_layers': copper, 'thickness_mm': spec['layers'].get('thickness_mm')}


def rf50_nets(inputs):
    """Graph nets of class RF50 that this board carries (any instance)."""
    nets = inputs['netclasses'].get('nets', {})
    out = set()
    for inst in inputs['spec']['instances']['list']:
        for gnet in inst['nets'].values():
            if nets.get(gnet, {}).get('class') == 'RF50':
                out.add(gnet)
    return sorted(out)


def notes_lines(inputs, stack, cov, bom_rows):
    spec, report, parsed, board = inputs['spec'], inputs['report'], inputs['parsed'], inputs['board']
    xs = [p[0] for e in parsed.edges for p in e]
    ys = [p[1] for e in parsed.edges for p in e]
    w, h = (max(xs) - min(xs), max(ys) - min(ys)) if xs else (0.0, 0.0)
    holes = parsed.holes
    rf = rf50_nets(inputs)
    q = report['build_quantity']
    inst = ', '.join(f'{i["id"]} {i["qty"]}' for i in spec['instances']['list'])
    drc = report['result']
    lines = [('h', f'{board} fab notes'), ('b', LABEL + '.'),
             ('t', f'Board status: {spec["status"]}. Every value below is a CI/model output of {GENERATOR} and pcb/board_gen.py; '
                   'no hardware or bench gate is closed by it.'),
             ('h', 'Board'),
             ('t', f'Outline (Edge.Cuts of {board}.kicad_pcb): {w:.3f} x {h:.3f} mm, area {cov.get("area_mm2", 0):.1f} mm2; '
                   f'lower-left corner at X {min(xs) if xs else 0:.3f}, Y {-max(ys) if ys else 0:.3f} mm in the Gerber/CPL frame '
                   '(KiCad absolute origin, Y up).'),
             ('t', 'Holes: ' + (', '.join(sorted({f'{"PTH" if hh["plated"] else "NPTH"} {hh["d"]:.2f} mm' for hh in holes}))
                                + f' ({len(holes)} mounting holes; NPTH unplated and without net)' if holes else 'no mounting holes') + '.'),
             ('h', 'Fabrication'),
             ('t', f'Copper layers: {stack["copper_layers"]}; finished thickness {stack["thickness_mm"]} mm '
                   '(JLC tolerance +/-10 % for boards >= 1.0 mm).')]
    if stack['copper_layers'] == 4:
        lines.append(('t', f'Stack-up {stack["id"]} ({stack["source"]}, read {stack["read"]}; {stack["via"]}):'))
        for layer in stack['layers']:
            if 'kicad' in layer:
                lines.append(('t', f'  {layer["plan"]} {layer["kicad"]}: copper {layer["copper_mm"]} mm'))
            else:
                lines.append(('t', f'  {layer["dielectric"]}: {layer["thickness_mm"]} mm, Er {layer["er"]}'))
        lines.append(('t', stack['note']))
    else:
        lines.append(('t', f'Stack-up: {stack["id"]}, outer copper {stack["copper_outer"]} '
                           f'({stack["source"]}, read {stack["read"]}).'))
    if rf:
        cls = inputs['netclasses']['classes']['RF50']
        tol = inputs['netclasses']['fab_floor']['jlc_4l_1oz'].get('impedance_tolerance_pct', 10)
        lines.append(('b', f'Impedance: 50 ohm CPWG on L1 over solid L2, w {cls["width_mm"]} mm, gap {cls["gap_mm"]} mm, '
                           f'+/-{tol} % (JLC standard): order WITH impedance control ({len(rf)} RF50 nets).'))
        lines.append(('t', 'The finished impedance is a coupon measurement (bench gate, OPEN); the design value is a MODEL.'))
    else:
        lines.append(('t', 'Impedance: no RF50 net on this board; order without impedance control.'))
    lines += [('t', 'Surface finish, solder mask and legend colours: order options, not fixed by this fab set.'),
              ('t', f'KiCad {KICAD_VERSION} DRC on the committed board: {drc["drc_errors"]} errors, {drc["drc_unconnected"]} '
                    f'unconnected, {drc["drc_warnings"]} reviewed warnings, ignored checks {drc["ignored_checks"]} '
                    '(report.json; CI/model result).'),
              ('h', 'Files (fab/)'),
              ('t', 'gerber/: Gerber X2 with netlist attributes, Protel extensions, one file per layer, Gerber job file '
                    '(.gbrjob). drill/: Excellon PTH and NPTH files (mm, decimal, absolute origin, alternate oval mode) '
                    f'and Gerber X2 drill maps. {board}.ipc356: IPC-D-356 netlist of every net with a pad. assembly/: JLC '
                    'BOM and CPL, the raw KiCad position file, the rotation offset table and the instance map.'),
              ('h', 'Assembly'),
              ('t', f'Boards to build: {q["total"]} = instances ({inst}) + spares {q["spares"]}; every board is the same '
                    'design and is assembled the same.'),
              ('t', 'Sides with parts: ' + ', '.join(f'{s} ({", ".join(f"{m} {n}" for m, n in sorted(c.items()))})'
                                                       for s, c in sorted(cov['cpl']['placed_by_side_and_mount'].items())) + '.'),
              ('t', 'CPL: Mid X / Mid Y are the KiCad footprint origins and Rotation the raw KiCad rotation (degrees, '
                    'counter-clockwise as the JLC CPL column). JLC rotation and centroid offsets per footprint are TBD '
                    f'(assembly/{board}-cpl-rotation-offsets.csv): check every part in the JLC viewer at order time; '
                    'nothing here verifies them.')]
    tbd = [r for r in bom_rows if r['LCSC Part #'] == 'TBD']
    for r in tbd:
        lines.append(('t', f'BOM TBD: {r["Designator"]} ({r["Comment"]}): {r["Note"]}'))
    lines.append(('h', 'Not proved here (OPEN)'))
    for item in report.get('does_not_prove', []):
        lines.append(('t', '- ' + item))
    lines.append(('t', 'Sources (read 2026-11-07): ' + '; '.join(SOURCES[k]['url'] for k in
                                                                 ('jlc_bom', 'jlc_cpl', 'jlc_kicad', 'jlc_gerber', 'jlc_capabilities'))))
    return lines


def fab_notes_pdf(inputs, stack, cov, bom_rows, cpl_rows):
    parsed, board = inputs['parsed'], inputs['board']
    pdf = Pdf()
    ops = pdf.page()
    # Left: the Edge.Cuts outline, holes and CPL centroids in the Gerber/CPL frame (x, -y), not to a fixed scale.
    box = (36, 80, 390, 440)
    segs = [((a[0], -a[1]), (b[0], -b[1])) for a, b in parsed.edges]
    pts = [p for s in segs for p in s]
    if pts:
        minx, maxx = min(p[0] for p in pts), max(p[0] for p in pts)
        miny, maxy = min(p[1] for p in pts), max(p[1] for p in pts)
        s = min(box[2] / max(maxx - minx, 1e-6), box[3] / max(maxy - miny, 1e-6))

        def T(x, y):
            return box[0] + (x - minx) * s, box[1] + (y - miny) * s
        for a, b in segs:
            pdf.line(ops, [T(*a), T(*b)], 1.0)
        for hh in parsed.holes:
            cx, cy = T(hh['x'], -hh['y'])
            pdf.circle(ops, cx, cy, hh['d'] / 2 * s, 0.6)
        for r in cpl_rows:
            cx, cy = T(float(r['Mid X']), float(r['Mid Y']))
            pdf.line(ops, [(cx - 4, cy), (cx + 4, cy)], 0.4)
            pdf.line(ops, [(cx, cy - 4), (cx, cy + 4)], 0.4)
            pdf.text(ops, cx + 5, cy + 3, 7, f'{r["Designator"]} ({r["Layer"]})')
        x0, y0 = T(minx, miny)
        x1, y1 = T(maxx, maxy)
        pdf.text(ops, x0, y0 - 14, 8, f'Board extent {maxx - minx:.3f} mm (X) x {maxy - miny:.3f} mm (Y)')
    pdf.text(ops, 36, 48, 7, f'Top view, Edge.Cuts and holes of {board}.kicad_pcb; crosses = CPL positions (KiCad footprint '
                             'origins). Not to a fixed scale.')
    pdf.text(ops, 36, 38, 7, LABEL)
    # Right column (then full pages): the notes.
    col, width_chars, y = 450, 78, 545
    for n, (kind, s) in enumerate(notes_lines(inputs, stack, cov, bom_rows)):
        size = 11 if kind == 'h' else 8
        if kind == 'h' and n:
            y -= 6  # space above a heading
        wrapped = textwrap.wrap(s, width_chars if kind != 'h' else 60) or ['']
        for piece in wrapped:
            if y < 40:
                ops = pdf.page()
                col, width_chars, y = 36, 150, 560
            pdf.text(ops, col, y, size, piece, bold=kind in ('h', 'b'))
            y -= size + 3
    return pdf.bytes(f'{board} fab notes - {LABEL}', f'{GENERATOR}; board {board}; {inputs["spec"]["status"]}')


# --- README, manifest, the whole set ------------------------------------------------------------------

def readme(inputs, cov, bom_rows, files):
    spec, report, board = inputs['spec'], inputs['report'], inputs['board']
    q = report['build_quantity']
    lines = [f'# Файли виробництва плати {board}', '',
             f'**{LABEL}.** Це вихід CI/моделі (`{GENERATOR}` у `sr-rx-pcb`, KiCad {KICAD_VERSION}), а не випуск для '
             f'фабрики: статус специфікації — `{spec["status"]}`; жодні апаратні чи стендові ворота цим не закриваються.', '',
             'Каталог повністю генерує `python3 pcb/fab_export.py --board ' + board + '`; вручну не редагувати. '
             '`--check` перегенеровує набір у тимчасовому каталозі й порівнює побайтово (KiCad ставить дати, '
             'абсолютні шляхи й рядок збірки — їх нормалізовано, правила в `manifest.json`), а також запускає '
             f'`{board}.kicad_jobset` і порівнює його вихід із прямим експортом.', '',
             '| Файл | Що це |', '|---|---|']
    descr = {'gerber/': 'Gerber X2 (атрибути X2 і нетліста, розширення Protel), по файлу на шар; `.gbrjob` — файл завдання Gerber',
             'drill/': 'Excellon: PTH і NPTH окремо (мм, десятковий формат, абсолютний початок, alternate для овальних) і карти свердлінь Gerber X2',
             f'{board}.ipc356': 'нетліст IPC-D-356 для електротесту (усі кола з контактними майданчиками)',
             f'assembly/{board}-bom-jlc.csv': 'BOM для JLC PCBA: Comment, Designator, Footprint, LCSC Part # + кількості на плату й на партію',
             f'assembly/{board}-cpl-jlc.csv': 'CPL для JLC: Designator, Mid X, Mid Y (мм), Layer (Top/Bottom), Rotation (сирий кут KiCad)',
             f'assembly/{board}-cpl-rotation-offsets.csv': 'таблиця поправок кута для JLC за посадковими місцями: порожня, TBD',
             f'assembly/{board}-instances.csv': 'відповідність шаблонних позначень плати позначенням графа для кожного екземпляра',
             f'assembly/{board}-pos-kicad.csv': 'сирий файл позицій KiCad (CSV, мм, обидва боки, без DNP)',
             f'{board}-fab-notes.pdf': 'примітки для фабрики: контур і отвори, шари й товщина, стек, імпеданс (лише RF), кількість',
             f'{board}.kicad_jobset': 'набір завдань KiCad 10.0.7 з тими самими параметрами експорту (для ручного відтворення)',
             'manifest.json': 'sha256 кожного файла, хеші входів, команди, правила нормалізації, перевірки повноти'}
    for key, text in descr.items():
        if any(rel == key or rel.startswith(key) for rel in files) or key == 'manifest.json':
            lines.append(f'| `{key}` | {text} |')
    inst = ', '.join(f'{i["id"]} ×{i["qty"]}' for i in spec['instances']['list'])
    lines += ['', '## Замовлення', '',
              f'- Плат: {q["total"]} = екземпляри ({inst}) + запасні {q["spares"]}; усі однакові й збираються однаково.',
              '- Gerber і свердління: заархівувати `gerber/` і `drill/` разом під час замовлення (архів не комітиться, '
              'бо zip має мітки часу).',
              '- Кут у CPL — сирий кут KiCad; поправки JLC для посадкових місць не прочитано й у CI не перевірено (TBD): '
              'кожну деталь перевіряє той, хто замовляє, у переглядачі JLC перед оплатою (крок збирання; у build/21 його '
              'додає власник STEPS).',
              f'- Позиції BOM з TBD: {", ".join(cov["bom"]["tbd"]) or "немає"}.']
    for r in bom_rows:
        if r['LCSC Part #'] == 'TBD':
            lines.append(f'  - {r["Designator"]} ({r["Comment"]}): {r["Note"]}.')
    for p in report.get('placeholders', []):
        lines.append(f'- Заглушка `{p["ref"]}` ({p["footprint"]}): її замінить {p["replaced_by"]}; доти набір не для виробництва.')
    lines += ['', '## Що цей набір не доводить (OPEN)', '']
    lines += [f'- {item}' for item in report.get('does_not_prove', [])]
    lines += ['', '## Джерела (прочитано 2026-11-07)', '']
    lines += [f'- {v["url"]} — {v["used"]}' for v in SOURCES.values()]
    return ('\n'.join(lines) + '\n').encode('utf-8')


def build_set(inputs, raw, commands):
    """Every file of fab/ (path -> bytes), the coverage record and its problems."""
    board, spec, report = inputs['board'], inputs['spec'], inputs['report']
    files = {rel: normalise(rel, data, board) for rel, data in raw.items()}
    pos = files.get(f'assembly/{board}-pos-kicad.csv')
    if pos is None:
        raise FabError('the KiCad position file is missing')
    cpl_rows = cpl(pos)
    bom_rows, used_rows, dnp = bom(inputs)
    facts = footprint_facts(inputs['parsed'])
    files[f'assembly/{board}-cpl-jlc.csv'] = csv_bytes(CPL_COLUMNS, cpl_rows)
    files[f'assembly/{board}-bom-jlc.csv'] = csv_bytes(BOM_COLUMNS, bom_rows)
    files[f'assembly/{board}-cpl-rotation-offsets.csv'] = csv_bytes(
        ['Footprint', 'Designators', 'JLC rotation offset (deg)', 'JLC centroid offset (mm)', 'Status'],
        rotation_offsets(cpl_rows, facts))
    files[f'assembly/{board}-instances.csv'] = csv_bytes(['Instance', 'Placement', 'Qty', 'Template ref', 'Graph ref'],
                                                         instances_rows(spec, report))
    cov, problems = coverage(files, inputs, cpl_rows, bom_rows)
    outline = check_boards.check_outline(inputs['parsed'], {'outline_mm': report['outline_mm']},
                                         check_boards.Frame(inputs['parsed'], {'outline_mm': report['outline_mm']}, {}))[1]
    cov['area_mm2'] = outline.get('area_mm2', 0.0)
    stack = stackup_record(inputs)
    files[f'{board}-fab-notes.pdf'] = fab_notes_pdf(inputs, stack, cov, bom_rows, cpl_rows)
    files[f'{board}.kicad_jobset'] = (json.dumps(jobset(board, spec['layers']['copper']), indent=2) + '\n').encode('utf-8')
    files['.gitattributes'] = b'# Generated by pcb/fab_export.py: byte-exact fab files (manifest sha256), no EOL conversion.\n* -text -whitespace\n'
    files['README.md'] = readme(inputs, cov, bom_rows, files)
    project = OUT_ROOT / board / f'{board}.kicad_pro'
    spec_part = {k: spec.get(k) for k in ('board_id', 'status', 'layers', 'instances')}
    spec_part['placeholders'] = [{k: p.get(k) for k in ('ref', 'footprint', 'value', 'pins', 'replaced_by')}
                                 for p in spec['parts'] if p['source'] == 'pilot_placeholder']
    report_part = {k: report.get(k) for k in ('template', 'build_quantity', 'placeholders', 'result', 'does_not_prove', 'outline_mm')}
    manifest = {
        'schema': SCHEMA, 'board_id': board, 'status': spec['status'], 'label': LABEL, 'generator': GENERATOR,
        'kicad_version': KICAD_VERSION,
        'inputs': {'board_file': board_gen.rel(inputs['pcb']), 'board_sha256': report['board_sha256'],
                   'project_sha256': board_gen.sha256_file(project) if project.is_file() else None,
                   'spec_projection_sha256': canon_sha(spec_part), 'report_projection_sha256': canon_sha(report_part),
                   'jlc_bom_rows': used_rows, 'jlc_bom_rows_sha256': canon_sha(used_rows),
                   'stackup': stack, 'stackup_sha256': canon_sha(stack), 'rf50_nets': rf50_nets(inputs),
                   'note': 'projections (F10): an unrelated build/10-jlc-bom.csv row, LCSC stock or spec edit does not stale this set'},
        'commands': commands,
        'normalisation': NORMALISATION,
        'build_quantity': report['build_quantity'],
        'dnp_excluded': dnp,
        'coverage': cov,
        'problems': problems,
        'sources': SOURCES,
        'files': [{'path': rel, 'sha256': sha(files[rel]), 'bytes': len(files[rel])} for rel in sorted(files)],
    }
    files['manifest.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    return files, cov, problems


def produce(board, temp, raw_copy=None):
    inputs = load_inputs(board)
    raw, commands = export_raw(board, inputs['spec']['layers']['copper'], temp)
    if raw_copy:
        dest = Path(raw_copy) / board
        for rel, data in raw.items():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            (dest / rel).write_bytes(data)
    files, cov, problems = build_set(inputs, raw, commands)
    left = leftovers(files, (str(temp), str(temp).replace('\\', '/')))
    if left:
        problems = problems + [f'not normalised: {rel}: {line}' for rel, line in left[:20]]
    return inputs, raw, files, cov, problems


def write(board, raw_copy=None):
    with tempfile.TemporaryDirectory(prefix=f'sr-rx-fab-{board}-') as temp:
        inputs, raw, files, cov, problems = produce(board, temp, raw_copy)
    out = fab_dir(board)
    if out.is_dir():
        for path in sorted(out.rglob('*'), reverse=True):
            rel = path.relative_to(out).as_posix()
            if path.is_file() and rel not in files:
                path.unlink()
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    for rel, data in files.items():
        board_gen.atomic_write(out / rel, data)
    print(json.dumps({'board': board, 'written': board_gen.rel(out), 'files': len(files), 'problems': problems},
                     ensure_ascii=False, indent=2))
    return 1 if problems else 0


def check(board, raw_copy=None, jobset_run=True):
    with tempfile.TemporaryDirectory(prefix=f'sr-rx-fab-{board}-') as temp:
        inputs, raw, files, cov, problems = produce(board, temp, raw_copy)
        problems = list(problems)
        if jobset_run:
            problems += jobset_check(board, inputs['spec']['layers']['copper'], raw, temp, raw_copy)
    out = fab_dir(board)
    have = collect(out) if out.is_dir() else {}
    for rel in sorted(set(files) | set(have)):
        if rel not in have:
            problems.append(f'missing in the committed fab/: {rel}')
        elif rel not in files:
            problems.append(f'not produced any more: {rel}')
        elif have[rel] != files[rel]:
            problems.append(f'differs from a fresh export: {rel}')
    print(json.dumps({'board': board, 'fab': board_gen.rel(out), 'files': len(files), 'coverage_passed': cov['passed'],
                      'problems': problems}, ensure_ascii=False, indent=2))
    return 1 if problems else 0


def boards_with_outputs():
    return [b for b in board_gen.list_boards() if (OUT_ROOT / b / f'{b}.kicad_pcb').is_file()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--board', required=True, help="board id of pcb/boards/<B>.json, or ALL")
    ap.add_argument('--check', action='store_true', help='regenerate in a temporary directory and compare (read-only)')
    ap.add_argument('--no-jobset', action='store_true', help='--check without running the kicad_jobset')
    args = ap.parse_args(argv)
    if args.board == 'ALL':
        boards = boards_with_outputs()
        if not boards:
            print('fab_export: 0 boards with a committed board file')
            return 0
    else:
        if not re.fullmatch(r'[A-Z][A-Z0-9_]*', args.board) or not board_gen.spec_path(args.board).is_file():
            ap.error(f'no spec pcb/boards/{args.board}.json')
        boards = [args.board]
    raw_copy = os.environ.get('SR_RX_FAB_RAW') or None
    rc = 0
    for board in boards:
        rc |= check(board, raw_copy, not args.no_jobset) if args.check else write(board, raw_copy)
    return rc


if __name__ == '__main__':
    sys.exit(main())
