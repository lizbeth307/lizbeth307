#!/usr/bin/env python3
"""PWR-A skeleton probe spec (W2 PCB-PWRA-2): the anchored refs and the scripted copper of the draft, standard library.

  python3 build/kicad/boards/PWR_A/make_probe_spec.py            write skeleton-probe/probe-spec.json
  python3 build/kicad/boards/PWR_A/make_probe_spec.py --check    fail unless skeleton-probe/probe-spec.json reproduces
  python3 build/kicad/boards/PWR_A/make_probe_spec.py --install  also copy it to pcb/boards/PWR_A.json (probe commit only)

The probe is one sr-rx-pcb route run ('[pcb-route PWR_A]') of a board that holds only the anchored refs and the
placeholders of PWR_A.spec-draft.json, with all its scripted copper (tracks, zones, vias) and post-route pours, so
that KiCad 10.0.7 can measure what the draft fixes: anchor positions, the B2B mate against PWR_B, pour necks, EP vias,
THT pads over plate pockets. It is not a board of record: it covers a fraction of the PWR_A refs, so the domain and
boundary audits fail by construction, and pcb/boards/PWR_A.json is removed again by the next commit.

tht_pockets: one proposed plate relief pocket (M-07) per cluster of THT pads and NPTH pegs of an anchored part:
the pad boxes + tht_pocket_margin_mm, rounded outward to 0.05 mm; margin boxes less than 3 mm apart share a pocket.
Needs KICAD10_FOOTPRINT_DIR for the FX8 placeholder land (board_gen.image_library_dir).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3]  # sat-receiver-audit
sys.path.insert(0, str(BASE / 'pcb'))
import board_gen as bg  # noqa: E402

DRAFT = HERE / 'PWR_A.spec-draft.json'
OUT = HERE / 'skeleton-probe' / 'probe-spec.json'
INSTALL = BASE / 'pcb' / 'boards' / 'PWR_A.json'
MARGIN = 1.0   # mm, mechanical/params/boards.json tht_pockets margin (the PWRA-1 probe rule)
GRID = 0.05    # mm, outward rounding of a pocket
RIB = 3.0      # mm, design value: two pockets closer than this become one (a thinner plate rib is not kept)
DROP = ('regions', 'reserved_areas', 'reserved_area_mm2')  # planner-only keys of the draft


def outward(v, up):
    q = v / GRID
    q = math.ceil(q - 1e-9) if up else math.floor(q + 1e-9)
    return round(q * GRID, 4)


def pockets_for(geo, anchor):
    turned = int(round(float(anchor.get('rotation', 0)) / 90.0)) % 2
    boxes = []
    for p in geo['pads']:
        if p['type'] not in ('thru_hole', 'np_thru_hole'):
            continue
        q = {**p, 'number': p['number'] or 'NPTH'}
        cx, cy = bg.placed_geometry({'pads': [q], 'courtyard': None}, anchor)['pads'][q['number']][0]
        w, h = (p['size'][1], p['size'][0]) if turned else (p['size'][0], p['size'][1])
        boxes.append([cx - w / 2 - MARGIN, cy - h / 2 - MARGIN, cx + w / 2 + MARGIN, cy + h / 2 + MARGIN])
    clusters = []
    for b in boxes:
        merged = [c for c in clusters if not (b[2] + RIB < c[0] or b[0] > c[2] + RIB or b[3] + RIB < c[1] or b[1] > c[3] + RIB)]
        for c in merged:
            clusters.remove(c)
            b = [min(b[0], c[0]), min(b[1], c[1]), max(b[2], c[2]), max(b[3], c[3])]
        clusters.append(b)
    out = []
    for x0, y0, x1, y1 in sorted(clusters):
        x0, y0, x1, y1 = outward(x0, False), outward(y0, False), outward(x1, True), outward(y1, True)
        out.append([x0, y0, round(x1 - x0, 4), round(y1 - y0, 4)])
    return out


def build():
    draft = bg.read_json(DRAFT)
    graph = bg.load_graph()
    manifest = bg.read_json(bg.MANIFEST)
    keep = [p for p in draft['parts'] if p.get('anchor')]
    refs = {p['ref'] for p in keep}
    nets = set()
    for p in keep:
        if p['source'] == 'graph':
            nets |= {pin['net'] for pin in graph[p['ref']]['pins'] if pin.get('net')}
        else:
            nets |= {n for n in p['pins'].values() if n}
    for item in draft['pre_route'].get('tracks', []) + draft['pre_route'].get('zones', []) + \
            draft['pre_route'].get('vias', []) + draft['post_route_zones']:
        nets.add(item['net'])
    inst = draft['instances']
    probe_inst = {
        'template_nets': sorted(nets),
        'list': [{**{k: v for k, v in item.items() if k not in ('refs', 'nets', 'source')},
                  'refs': {r: g for r, g in item['refs'].items() if r in refs},
                  'nets': {n: g for n, g in item['nets'].items() if n in nets},
                  'source': 'identity map (skeleton probe)'} for item in inst['list']],
    }
    for k, v in inst.items():
        if k not in ('template_nets', 'list'):
            probe_inst[k] = v
    spec_for_geo = {**draft, 'parts': keep, 'instances': probe_inst, 'groups': []}
    template = bg.resolve(spec_for_geo, graph, manifest)
    pockets = []
    for t in template:
        geo = bg.footprint_geometry(bg.footprint_file(t).read_text(encoding='utf-8'))
        pockets += pockets_for(geo, t['anchor'])
    out = {}
    for k, v in draft.items():
        if k in DROP:
            continue
        if k == 'status':
            v = 'SKELETON_PROBE_NOT_FOR_FABRICATION'
        elif k == 'title':
            v = (f'PWR-A skeleton probe: the {len(keep)} anchored refs and placeholders and the scripted copper '
                 'of the draft only')
        elif k == 'note':
            v = ('W2 PCB-PWRA-2 probe for one CI route run (generated by build/kicad/boards/PWR_A/make_probe_spec.py '
                 'from PWR_A.spec-draft.json): loads the 4-layer PWR_A.kicad_pro in KiCad 10.0.7, places the anchors and '
                 'the B2B mate of the draft and lays its scripted copper, so that the anchors, the B2B mate against '
                 'PWR_B B2B1, the locked copper, the EP vias, the pour necks and the THT pockets can be measured on a '
                 f'saved board. It covers {len(refs)} of the {len(draft["parts"])} PWR_A template refs, so the domain '
                 'and boundary audits fail by construction; removed from pcb/boards/ right after the run.')
        elif k == 'parts':
            v = keep
        elif k == 'groups':
            v = []
        elif k == 'instances':
            v = probe_inst
        elif k == 'router':
            v = {**v, 'max_passes': 30, 'job_timeout': '00:10:00', 'timeout_s': 700}
        out[k] = v
    out['tht_pockets'] = pockets
    out['tht_pocket_margin_mm'] = MARGIN
    out['tht_pockets_note'] = ('proposed plate relief pockets (M-07) = THT pads and NPTH pegs of each anchored part + '
                               '1.0 mm (mechanical/params/boards.json tht_pockets margin), rounded outward to 0.05 mm; '
                               'margin boxes less than 3 mm apart share one pocket (make_probe_spec.py RIB)')
    bg.validate_spec(out, 'PWR_A')
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--install', action='store_true')
    args = ap.parse_args(argv)
    text = json.dumps(build(), ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if not OUT.is_file() or OUT.read_text(encoding='utf-8') != text:
            print('skeleton-probe/probe-spec.json is stale: rerun build/kicad/boards/PWR_A/make_probe_spec.py')
            return 1
        print('skeleton-probe/probe-spec.json reproduces')
        return 0
    bg.atomic_write(OUT, text)
    if args.install:
        bg.atomic_write(INSTALL, text)
        print(f'installed {INSTALL.relative_to(BASE).as_posix()} (probe commit only; remove it in the next commit)')
    print(f'{OUT.relative_to(BASE).as_posix()}: {len(json.loads(text)["parts"])} parts, '
          f'{len(json.loads(text)["tht_pockets"])} pockets')
    return 0


if __name__ == '__main__':
    sys.exit(main())
