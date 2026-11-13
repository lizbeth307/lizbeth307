#!/usr/bin/env python3
"""F2-ENV probe patch of the PWR-A planner spec and study (W2 PWRJ F2ENV), standard library. PROBE ONLY.

  python3 build/kicad/boards/PWR_A/f2env_patch.py            patch PWR_A.spec-shrink2.json and placement-study-shrink2.json
  python3 build/kicad/boards/PWR_A/f2env_patch.py --stage 2  then move the PWR-A tall parts under J209 (CUT_MOVES)

The F2-ENV variant (ENV-SLAB, E = SLAB mm; owner row 'Оболонка D15', not adopted) inserts a slab between the battery tray
and the plate. PWR-A and PWR-B keep the board frame of the L and grow down by SLAB (contract outline (0,-SLAB)-(136,-SLAB)-
(136,35)-(42,35)-(42,110)-(0,110), mechanical/params/boards.json). The bottom harness row stays where it is in the
enclosure, above the tray: so in board coordinates the row moves down by SLAB to the new bottom edge, and the E1_SW rise
pour that feeds J107.2 grows down with it. Everything else of the SHRINK-2 lineage (anchors, scripted copper, windows,
probe windows) keeps its board coordinates.

What it changes, in place (make_spec.py --check and placement_study.py --check then fail by design on the probe branch;
place_board.py and make_board.py rerun on the patched files):
  * spec parts anchors of ROW (the bottom row J105-J112 and the corner pair J114 / J507): y - SLAB;
  * spec pre_route zone E1SW-RISE and its reserved area CU_E1SW-RISE: the bottom edge y - SLAB;
  * study positions of ROW (at, courtyard_box) and their header edge strips in pwr_b_cutouts: y - SLAB;
  * SINGLE_SIDED: the 94 chip refs of two_sided.bottom_refs go to the top side (study positions side F; place_board.py
    legalises them): the slab gives the area, so the plate pockets PB1-PB13 and the bottom assembly pass are not needed;
  * the study's spec hash, so that make_probe_spec / place_board accept the pair.
A marker key 'f2env' in the spec stops a second run. CI/MODEL input only; bench gates OPEN.

Stage 2 (F2ENV probe 2): CUT_MOVES moves PWR-A parts that need a PWR-B cut-out (study positions, their window rect by the
same offset): the radials C265, C512 and C511 stood under the PWR-B J209 at y 3.7-11.5 and boxed in the escape of its
lower contact row (F2ENV probe 1, run 43340503685: the S02 nets J209 -> J202 / J203 stayed open); they go to the new bottom
edge between the J112 strip (x <= 89.6) and the J507 strip (x >= 115), as edge windows.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3]
sys.path.insert(0, str(BASE / 'pcb'))
import board_gen as bg  # noqa: E402

SPEC = HERE / 'PWR_A.spec-shrink2.json'
STUDY = HERE / 'placement-study-shrink2.json'
SLAB = 30.0
ROW = ('J105', 'J106', 'J107', 'J108', 'J109', 'J110', 'J111', 'J112', 'J114', 'J507')
SINGLE_SIDED = True


def r4(v):
    return round(v + 0.0, 4)


CUT_MOVES = {'C265': (0.0, -33.6), 'C512': (0.0, -33.6), 'C511': (0.0, -34.9)}   # ref -> (dx, dy) board mm


def stage2():
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    study = json.loads(STUDY.read_text(encoding='utf-8'))
    if 'f2env' not in spec or spec['f2env'].get('stage2'):
        raise SystemExit('f2env_patch: stage 2 needs stage 1 and runs once')
    for r in study['positions']['refs']:
        if r['ref'] in CUT_MOVES:
            dx, dy = CUT_MOVES[r['ref']]
            r['at'] = [r4(r['at'][0] + dx), r4(r['at'][1] + dy)]
            b = r['courtyard_box']
            r['courtyard_box'] = [r4(b[0] + dx), r4(b[1] + dy), r4(b[2] + dx), r4(b[3] + dy)]
            r['how'] = r.get('how', '') + f' (F2ENV stage 2: moved {dx:g}, {dy:g})'
    for c in study['pwr_b_cutouts']['placed']:
        if c['ref'] in CUT_MOVES:
            dx, dy = CUT_MOVES[c['ref']]
            q = c['rect']
            c['rect'] = [r4(q[0] + dx), r4(q[1] + dy), r4(q[2] + dx), r4(q[3] + dy)]
            if c['rect'][1] < -SLAB + 1.0:      # at the new bottom edge: an edge window down to the edge strip line
                c['rect'][1] = r4(-SLAB - 0.2)
    spec['f2env']['stage2'] = {'cut_moves': {k: list(v) for k, v in CUT_MOVES.items()},
                               'why': 'tall PWR-A radials out from under the PWR-B J209 lower contact row (probe 1, run 43340503685)'}
    study['inputs']['spec_sha256'] = bg.sha256_bytes(bg.canonical(spec))
    study['f2env'] = spec['f2env']
    SPEC.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    STUDY.write_text(json.dumps(study, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'stage 2: moved {sorted(CUT_MOVES)}')


def main():
    if '--stage' in sys.argv and sys.argv[sys.argv.index('--stage') + 1] == '2':
        return stage2()
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    study = json.loads(STUDY.read_text(encoding='utf-8'))
    if 'f2env' in spec:
        raise SystemExit('f2env_patch: the spec is already patched')
    for p in spec['parts']:
        if p['ref'] in ROW:
            p['anchor']['at'][1] = r4(p['anchor']['at'][1] - SLAB)
    z = next(z for z in spec['pre_route']['zones'] if z['id'] == 'E1SW-RISE')
    y0 = min(q[1] for q in z['outline'])
    z['outline'] = [[q[0], r4(q[1] - SLAB) if q[1] == y0 else q[1]] for q in z['outline']]
    z['why'] += f'; W2 PWRJ F2ENV probe: grown down by {SLAB:g} mm with the bottom row (slab under the band)'
    ra = next(a for a in spec['reserved_areas'] if a['id'] == 'CU_E1SW-RISE')
    ra['rect'][1] = r4(ra['rect'][1] - SLAB)
    bottom = list(spec['two_sided']['bottom_refs']) if SINGLE_SIDED else []
    if SINGLE_SIDED:
        spec['two_sided']['f2env_single_sided'] = ('W2 PWRJ F2ENV probe: the bottom_refs go to the top side (study positions '
                                                   'side F, legalised by place_board.py); the list is kept as a record')
        spec['sides'] = ['top']
    spec['f2env'] = {'slab_mm': SLAB, 'row_moved_down': list(ROW), 'single_sided': SINGLE_SIDED,
                     'generator': 'build/kicad/boards/PWR_A/f2env_patch.py (probe only, wip/w2-pwrj-f2env)'}
    for r in study['positions']['refs']:
        if r['ref'] in ROW:
            r['at'][1] = r4(r['at'][1] - SLAB)
            b = r['courtyard_box']
            r['courtyard_box'] = [b[0], r4(b[1] - SLAB), b[2], r4(b[3] - SLAB)]
        if r['ref'] in bottom and r['side'] == 'B':
            r['side'] = 'F'
            r['how'] = r.get('how', '') + ' (F2ENV: bottom -> top)'
    for c in study['pwr_b_cutouts']['placed']:
        if c['ref'] in ROW:
            q = c['rect']
            c['rect'] = [q[0], r4(q[1] - SLAB), q[2], r4(q[3] - SLAB)]
    study['inputs']['spec_sha256'] = bg.sha256_bytes(bg.canonical(spec))
    study['f2env'] = spec['f2env']
    SPEC.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    STUDY.write_text(json.dumps(study, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'patched {SPEC.name} and {STUDY.name}: ROW {len(ROW)} refs down {SLAB:g} mm, {len(bottom)} bottom refs to the top')


if __name__ == '__main__':
    main()
