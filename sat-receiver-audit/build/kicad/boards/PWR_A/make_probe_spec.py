#!/usr/bin/env python3
"""PWR-A probe specs: the skeleton probe of the draft (W2 PCB-PWRA-2) and the SHRINK-2 placement probe (W2 PCB-PWRA-3),
standard library.

  python3 build/kicad/boards/PWR_A/make_probe_spec.py            write skeleton-probe/ and placement-probe/probe-spec.json
  python3 build/kicad/boards/PWR_A/make_probe_spec.py --check    fail unless both probe-spec.json files reproduce
  python3 build/kicad/boards/PWR_A/make_probe_spec.py --install skeleton|placement
                                                                 also copy that probe to pcb/boards/PWR_A.json (probe
                                                                 commit only)

The probe is one sr-rx-pcb route run ('[pcb-route PWR_A]') of a board that holds only the anchored refs and the
placeholders of PWR_A.spec-draft.json, with all its scripted copper (tracks, zones, vias) and post-route pours, so
that KiCad 10.0.7 can measure what the draft fixes: anchor positions, the B2B mate against PWR_B, pour necks, EP vias,
THT pads over plate pockets. It is not a board of record: it covers a fraction of the PWR_A refs, so the domain and
boundary audits fail by construction, and pcb/boards/PWR_A.json is removed again by the next commit.

The placement probe (W2 PCB-PWRA-3) is one sr-rx-pcb route run of the SHRINK-2 planner spec PWR_A.spec-shrink2.json
(make_spec.py) with every ref the study placed anchored at its planned origin, side and rotation
(placement-study-shrink2.json positions, both sides): KiCad 10.0.7 then checks the planner's placement (courtyard
overlaps on both sides, holes, edges), the J208 mate against PWR_B J209 and the THT pockets, and Freerouting gives a first
route of the SHRINK-2 layout. Refs with a pending planned footprint (planned_footprints: the graph still has the old part)
and the reserved blocks of pending changes have no KiCad footprint of their own yet and stay out; the domain and boundary
audits fail by construction. pcb/boards/PWR_A.json is removed again by the next commit.

tht_pockets: one proposed plate relief pocket (M-07) per cluster of THT pads and NPTH pegs of a placed part:
the pad boxes + tht_pocket_margin_mm, rounded outward to 0.05 mm; margin boxes less than 3 mm apart share a pocket.
The skeleton probe needs KICAD10_FOOTPRINT_DIR for the FX8 placeholder land of the draft (board_gen.image_library_dir).
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
SHRINK2 = HERE / 'PWR_A.spec-shrink2.json'
SHRINK2_STUDY = HERE / 'placement-study-shrink2.json'
OUT_PLACEMENT = HERE / 'placement-probe' / 'probe-spec.json'
# planner-only keys of the SHRINK-2 spec (make_spec.py); board_gen and check_boards ignore or refuse them
PLANNER_KEYS = ('regions', 'reserved_areas', 'reserved_area_mm2', 'budget_candidate', 'fallback_id', 'planned_footprints',
                'planned_changes', 'two_sided', 'h_trim', 'ffc', 'exit_edges', 'turn_whatif', 'generator')
INSTALL = BASE / 'pcb' / 'boards' / 'PWR_A.json'
MARGIN = 1.0   # mm, mechanical/params/boards.json tht_pockets margin (the PWRA-1 probe rule)
GRID = 0.05    # mm, outward rounding of a pocket
SLACK = 0.01   # mm, added before the outward rounding
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
        # SLACK keeps a pad edge that falls exactly on the grid off the pocket edge (KiCad stores nm, probe 2 found it)
        x0, y0, x1, y1 = (outward(x0 - SLACK, False), outward(y0 - SLACK, False), outward(x1 + SLACK, True),
                          outward(y1 + SLACK, True))
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


def build_placement():
    spec = bg.read_json(SHRINK2)
    study = bg.read_json(SHRINK2_STUDY)
    if study['inputs']['spec_sha256'] != bg.sha256_bytes(bg.canonical(spec)):
        raise SystemExit('placement-study-shrink2.json is not the study of PWR_A.spec-shrink2.json: rerun placement_study.py')
    graph = bg.load_graph()
    manifest = bg.read_json(bg.MANIFEST)
    pos = {r['ref']: r for r in study['positions']['refs']}
    pending = set(spec.get('planned_footprints', {}))
    keep, left_out = [], []
    for p in spec['parts']:
        ref = p['ref']
        if ref in pending or ref not in pos:
            left_out.append(ref)
            continue
        if p.get('anchor'):
            keep.append(p)
            continue
        r = pos[ref]
        keep.append({'ref': ref, 'source': p['source'],
                     'anchor': {'at': r['at'], 'align': 'origin', 'rotation': r['rotation'], 'side': r['side']},
                     'anchor_source': 'placement-study-shrink2.json position (board_gen planner, chunked first-fit)'})
    refs = {p['ref'] for p in keep}
    nets = set()
    for p in keep:
        nets |= {pin['net'] for pin in graph[p['ref']]['pins'] if pin.get('net') and not pin.get('nc')}
    pre = spec['pre_route']
    pre_route = {k: [x for x in pre.get(k, []) if x['net'] in nets] for k in ('tracks', 'vias', 'zones')}
    item = spec['instances']['list'][0]
    probe_inst = {'template_nets': sorted(nets),
                  'list': [{**{k: v for k, v in item.items() if k not in ('refs', 'nets', 'source')},
                            'refs': {r: r for r in sorted(refs, key=bg.sort_ref)}, 'nets': {n: n for n in sorted(nets)},
                            'source': 'identity map (placement probe)'}]}
    for k, v in spec['instances'].items():
        if k not in ('template_nets', 'list'):
            probe_inst[k] = v
    spec_for_geo = {**spec, 'parts': keep, 'instances': probe_inst, 'groups': []}
    template = bg.resolve(spec_for_geo, graph, manifest)
    pockets = []
    geos = {}
    for t in template:
        geos[t['ref']] = geo = bg.footprint_geometry(bg.footprint_file(t).read_text(encoding='utf-8'))
        if t['anchor'].get('side', 'F') != 'F':
            continue
        pockets += pockets_for(geo, t['anchor'])
    # A post-route pour that no pad of its net can reach would only be isolated copper (the GND bond pours of zones 3'/4'
    # on B.Cu while their converters are reserved blocks): it stays out of the probe. A pad reaches a pour when its part
    # has a pin on the net, its courtyard overlaps the pour and it sits on the pour's side or has THT pads.
    boxes = {q['ref']: q['courtyard_box'] for q in study['positions']['refs']}
    post, post_left_out = [], []
    for z in spec['post_route_zones']:
        if z['net'] not in nets:
            continue
        zside = 'B' if z['layer'] == 'B.Cu' else 'F'
        zx, zy = [q[0] for q in z['outline']], [q[1] for q in z['outline']]
        zb = [min(zx), min(zy), max(zx), max(zy)]
        hit = [t['ref'] for t in template if any(pin.get('net') == z['net'] for pin in graph[t['ref']]['pins'])
               and bg.rects_overlap(boxes[t['ref']], zb)
               and (t['anchor'].get('side', 'F') == zside or any(q['type'] == 'thru_hole' for q in geos[t['ref']]['pads']))]
        if hit:
            post.append(z)
        else:
            post_left_out.append(z['id'])
    out = {}
    for k, v in spec.items():
        if k in PLANNER_KEYS:
            continue
        if k == 'status':
            v = 'PLACEMENT_PROBE_NOT_FOR_FABRICATION'
        elif k == 'title':
            v = (f'PWR-A SHRINK-2 placement probe: {len(keep)} refs at the planned positions (both sides) and the scripted '
                 'copper of the SHRINK-2 spec')
        elif k == 'note':
            v = ('W2 PCB-PWRA-3 probe for one CI route run (generated by build/kicad/boards/PWR_A/make_probe_spec.py from '
                 'PWR_A.spec-shrink2.json and placement-study-shrink2.json): every ref the board_gen planner placed is '
                 'anchored at its planned origin, so that KiCad 10.0.7 checks the placement (courtyards on both sides), the '
                 'J208 mate against PWR_B J209 and the THT pockets on a saved board, and Freerouting routes it once. Left '
                 f'out ({len(left_out)}): refs with a pending planned footprint ({", ".join(sorted(left_out, key=bg.sort_ref))}) '
                 'and the reserved blocks of pending changes, so the domain and boundary audits fail by construction; '
                 'removed from pcb/boards/ right after the run.')
        elif k == 'parts':
            v = keep
        elif k == 'groups':
            v = []
        elif k == 'instances':
            v = probe_inst
        elif k == 'pre_route':
            v = pre_route
        elif k == 'post_route_zones':
            v = post
        elif k == 'router':
            v = {**v, 'max_passes': 30, 'job_timeout': '00:10:00', 'timeout_s': 700}
        out[k] = v
    out['tht_pockets'] = pockets
    out['tht_pocket_margin_mm'] = MARGIN
    out['tht_pockets_note'] = ('proposed plate relief pockets (M-07) = THT pads and NPTH pegs of each placed top part + '
                               '1.0 mm (mechanical/params/boards.json tht_pockets margin), rounded outward to 0.05 mm; '
                               'margin boxes less than 3 mm apart share one pocket (make_probe_spec.py RIB)')
    out['probe_left_out'] = sorted(left_out, key=bg.sort_ref)
    out['probe_post_route_zones_left_out'] = post_left_out
    bg.validate_spec(out, 'PWR_A')
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--install', choices=('skeleton', 'placement'))
    args = ap.parse_args(argv)
    status = 0
    for kind, out, fn in (('skeleton', OUT, build), ('placement', OUT_PLACEMENT, build_placement)):
        text = json.dumps(fn(), ensure_ascii=False, indent=2) + '\n'
        name = out.relative_to(HERE).as_posix()
        if args.check:
            if not out.is_file() or out.read_text(encoding='utf-8') != text:
                print(f'{name} is stale: rerun build/kicad/boards/PWR_A/make_probe_spec.py')
                status = 1
            else:
                print(f'{name} reproduces')
            continue
        bg.atomic_write(out, text)
        if args.install == kind:
            bg.atomic_write(INSTALL, text)
            print(f'installed {INSTALL.relative_to(BASE).as_posix()} (probe commit only; remove it in the next commit)')
        print(f'{out.relative_to(BASE).as_posix()}: {len(json.loads(text)["parts"])} parts, '
              f'{len(json.loads(text)["tht_pockets"])} pockets')
    return status


if __name__ == '__main__':
    sys.exit(main())
