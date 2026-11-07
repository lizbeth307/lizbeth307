#!/usr/bin/env python3
"""PWR-A placement study (W2 PCB-PWRA-1): the board_gen planner run on the PWR_A draft spec, standard library only.

  python3 build/kicad/boards/PWR_A/placement_study.py           write placement-study.json next to this file
  python3 build/kicad/boards/PWR_A/placement_study.py --check   fail unless placement-study.json reproduces

Inputs: PWR_A.spec-draft.json (this directory), pcb/board_gen.py (its validation, net resolution, footprint
geometry and deterministic shelf packer are reused, nothing is re-implemented), the mechanical contract
(mechanical/generated/contract/boards.json PWR and PWR_B), design/E1-E5, the portable footprint manifest,
pcb/partition-spec.json, pcb/partition-budget.json, pcb/generated/netclasses.json and pcb/generated/b2b-nets.json.

What it reports (MODEL / CI-free planning result, not a KiCad board, not a hardware result):
- the anchors of the spec placed by board_gen.placed_geometry and checked against the contract (Pololu pin fields
  within 0.05 mm, regulators inside thermal_bond zones 1-2, harness headers on their exit edges, outline, holes);
- every placement group packed with board_gen.place_groups in spec order, first into its region and then into its
  alt_regions; a group that fits nowhere is listed with the planner's refusal, and its refs stay unplaced;
- the courtyard fill (sum of courtyard boxes + reserved areas over the usable outline) against the fallback F2
  trigger 0.60 of pcb/partition-spec.json, and the free area left after the anchors;
- the exit-edge length demand of the PWR-A and PWR-B harness headers, the PWR-B cut-outs this placement needs
  (windows over PWR-A parts taller than hA, header edge strips, test-point probe windows), the THT pads inside the
  thermal_bond zones (plate pockets, M-07) and a geometric pre-check of the scripted copper.
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

SPEC = HERE / 'PWR_A.spec-draft.json'
OUT = HERE / 'placement-study.json'
CONTRACT = BASE / 'mechanical/generated/contract/boards.json'
PARTITION_SPEC = BASE / 'pcb/partition-spec.json'
BUDGET = BASE / 'pcb/partition-budget.json'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
B2B_NETS = BASE / 'pcb/generated/b2b-nets.json'
PIN_FIELD_TOL = 0.05
EDGE_TOL = 0.5  # a header courtyard within 0.5 mm of its exit edge counts as on the edge
# Design value: depth of the header strip along an exit edge = the deepest vertical Mini-Fit Jr./Micro-Fit
# courtyard of the PWR-A headers at rotation 90 (6.4-6.8 mm, vendored KiCad 10.0.7 footprints), rounded up.
STRIP_DEPTH = 7.0

# Exit edge of each PWR-A harness header: contract edge_zones of PWR (mechanical/generated/contract/boards.json)
# by harness segment (build/16-dzhgut-rozyemy.csv, tools/assembly_data.py SEGMENTS).
EXIT_EDGE = {
    'J104': 'right', 'J113': 'right', 'J114': 'right', 'J115': 'right', 'J507': 'right',
    'J105': 'bottom', 'J106': 'bottom', 'J107': 'bottom', 'J108': 'bottom',
    'J109': 'bottom', 'J110': 'bottom', 'J111': 'bottom', 'J112': 'bottom',
    'J205': 'top_left', 'J206': 'top_sl2',
}
# The same for the PWR-B headers (contract PWR_B edge_zones; read-only here, PCB-PWRB places them).
PWR_B_EXIT_EDGE = {'J201': 'right', 'J202': 'right', 'J203': 'right', 'J506': 'right', 'J508': 'right',
                   'J204': 'top_sl2', 'J207': 'top_sl2'}
BOND_ZONE_REFS = {'U211': (1, 2), 'U213': (1, 2), 'U204': (1, 2), 'U205': (1, 2)}
POLOLU = {'U107': 0, 'U108': 1}  # index into contract modules_on_board


def r4(v):
    return bg.r4(v)


def area(box):
    return (box[2] - box[0]) * (box[3] - box[1])


def inside(box, rect, tol=1e-6):
    return box[0] >= rect[0] - tol and box[1] >= rect[1] - tol and box[2] <= rect[2] + tol and box[3] <= rect[3] + tol


def xywh(rect):
    x, y, w, h = rect
    return [x, y, x + w, y + h]


def polygon_area(poly):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))) / 2


def edge_spans(contract):
    """Available edge segments per exit edge, minus the chords of the hole keepouts touching that edge."""
    out = {}
    for z in contract['edge_zones']:
        key = {'bottom': 'bottom', 'right': 'right'}.get(z['edge'])
        if z['edge'] == 'top':
            key = 'top_sl2' if 'at' in z else 'top_left'
        out[key] = {'edge': z['edge'], 'at': z.get('at'), 'span': z['span'], 'use': z['use']}
    return out


def header_extent(box, edge):
    """Length of a header courtyard along its exit edge."""
    return (box[3] - box[1]) if edge == 'right' else (box[2] - box[0])


def on_edge(box, edge, outline_box, spans):
    x0, y0, x1, y1 = outline_box
    if edge == 'bottom':
        return abs(box[1] - y0) <= EDGE_TOL
    if edge == 'right':
        return abs(box[2] - x1) <= EDGE_TOL
    if edge == 'top_left':
        return abs(box[3] - y1) <= EDGE_TOL and box[2] <= spans['top_left']['span'][1] + 1e-6
    if edge == 'top_sl2':
        lo, hi = spans['top_sl2']['span']
        return abs(box[3] - spans['top_sl2']['at']) <= EDGE_TOL and box[0] >= lo - 1e-6 and box[2] <= hi + 1e-6
    return False


def study():
    spec = bg.read_json(SPEC)
    board = spec['board_id']
    bg.validate_spec(spec, board)
    contract_all = bg.read_json(CONTRACT)['boards']
    contract = contract_all[spec['contract']['board']]
    contract_b = contract_all['PWR_B']
    pspec = bg.read_json(PARTITION_SPEC)
    budget = bg.read_json(BUDGET)
    netclasses = bg.read_json(NETCLASSES)
    b2b_nets = bg.read_json(B2B_NETS)
    graph = bg.load_graph()
    db = bg.parts_by_ref()
    manifest = bg.read_json(bg.MANIFEST)
    project = bg.read_json(BASE / spec['project'])
    project_problems = bg.check_project(spec, project)
    template = bg.resolve(spec, graph, manifest)
    partition = bg.read_json(BASE / spec['partition'])
    domain = bg.domain_audit(spec, partition)
    geometry = {p['ref']: bg.footprint_geometry(bg.footprint_file(p).read_text(encoding='utf-8')) for p in template}
    outline = contract['outline_mm']
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    outline_box = [min(xs), min(ys), max(xs), max(ys)]
    hole_list = bg.holes(spec, contract)
    hA = pspec['parameters']['hA']
    margin = pspec['parameters']['window_margin']

    # --- usable area (outline minus the hole keepout circles, as pcb/partition_budget.py counts it) ---
    outline_area = polygon_area(outline)
    keepout_area = sum(math.pi * (h['keepout_d'] / 2) ** 2 for h in hole_list)
    usable = outline_area - keepout_area

    # --- anchors ---
    anchored = {p['ref']: p['anchor'] for p in template if p.get('anchor')}
    placed = {}
    anchor_rows, anchor_errors = [], []
    for ref in sorted(anchored, key=bg.sort_ref):
        g = bg.placed_geometry(geometry[ref], anchored[ref])
        placed[ref] = {'side': anchored[ref].get('side', 'F'), **g}
        box = g['box']
        row = {'ref': ref, 'at': anchored[ref]['at'], 'rotation': anchored[ref].get('rotation', 0),
               'courtyard_box': box, 'checks': {}}
        row['checks']['inside_outline'] = all(bg.point_in_outline(c, outline) for c in
                                              ((box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])))
        hits = [h['ref'] for h in hole_list if bg.box_circle_distance(box, h['at']) < h['keepout_d'] / 2 - 1e-9]
        row['checks']['clear_of_hole_keepouts'] = not hits
        if ref in POLOLU:
            mod = contract['modules_on_board'][POLOLU[ref]]
            pf = mod['pin_field']
            want = [pf[0], pf[1], pf[0] + pf[2], pf[1] + pf[3]]
            fp_pads = [p for p in geometry[ref]['pads'] if p['type'] == 'thru_hole']
            boxes = []
            for p in fp_pads:
                cx, cy = bg.placed_geometry({'pads': [p], 'courtyard': None}, anchored[ref])['pads'][str(p['number'])][0]
                boxes.append([cx - p['size'][0] / 2, cy - p['size'][1] / 2, cx + p['size'][0] / 2, cy + p['size'][1] / 2])
            got = [r4(min(b[0] for b in boxes)), r4(min(b[1] for b in boxes)), r4(max(b[2] for b in boxes)),
                   r4(max(b[3] for b in boxes))]
            dev = max(abs(a - b) for a, b in zip(got, want))
            row['checks']['pin_field_contract'] = {'contract': want, 'placed_pad_box': got, 'max_dev_mm': r4(dev),
                                                   'within_0_05': dev <= PIN_FIELD_TOL + 1e-9}
        if ref in BOND_ZONE_REFS:
            zones = [i for i in BOND_ZONE_REFS[ref] if inside(box, xywh(contract['thermal_bond_mm'][i - 1]))]
            row['checks']['inside_thermal_bond_zone'] = zones or False
        if ref in EXIT_EDGE:
            row['checks']['exit_edge'] = EXIT_EDGE[ref]
        for key, val in row['checks'].items():
            bad = (val is False) or (isinstance(val, dict) and val.get('within_0_05') is False)
            if bad:
                anchor_errors.append({'ref': ref, 'check': key})
        anchor_rows.append(row)
    refs_sorted = sorted(anchored, key=bg.sort_ref)
    for i, a in enumerate(refs_sorted):
        for b in refs_sorted[i + 1:]:
            if bg.rects_overlap(placed[a]['box'], placed[b]['box']):
                anchor_errors.append({'ref': a, 'check': f'courtyard overlaps {b}'})

    # --- reserved areas (study obstacles: no footprint exists for them yet) ---
    reserved_rows = []
    obstacles = []
    for res in spec.get('reserved_areas', []):
        rect = res['rect']
        ok = all(bg.point_in_outline(c, outline) for c in ((rect[0], rect[1]), (rect[2], rect[1]), (rect[2], rect[3]),
                                                           (rect[0], rect[3])))
        clash = sorted(r for r, p in placed.items() if bg.rects_overlap(rect, p['box']))
        holes_hit = [h['ref'] for h in hole_list if bg.box_circle_distance(rect, h['at']) < h['keepout_d'] / 2]
        reserved_rows.append({'id': res['id'], 'rect': rect, 'area_mm2': r4(area(rect)), 'inside_outline': ok,
                              'overlaps_anchors': clash, 'hole_keepouts_hit': holes_hit})
        obstacles.append({'ref': '__' + res['id'], 'box': rect})
    reserve_mm2 = 0.0
    reserve_rows = []
    for res in spec.get('reserved_area_mm2', []):
        val = budget['candidates'][budget['chosen']]['pwr_a_keepouts_mm2'] if res['id'] == 'PWR_B_THT_KEEPOUTS' else 0.0
        reserve_mm2 += val
        reserve_rows.append({'id': res['id'], 'area_mm2': r4(val), 'source': res['area_mm2_source']})

    # --- chunked first-fit with the board_gen planner ---
    # Each region hosts at most one packed chunk (board_gen shelf-packs a group from the top-left corner of its
    # region, so a second group in the same rectangle would collide); the strip left below the chunk's lowest
    # shelf becomes a new region '<name>+'. For every spec group in order, the regions are tried in the order
    # region_name, alt_regions, then every other free region; in each, the members still unplaced are added one
    # at a time, largest courtyard first, and kept when board_gen.place_groups still packs the chunk; a member is
    # turned by 90 degrees when that aligns its long side with the region's long side. Already placed parts and
    # reserved areas are fixed obstacles.
    regions = dict(spec['regions']['rects'])
    used = set()
    chunks = []  # accepted board_gen groups
    group_rows = []

    def as_obstacles(boxes):
        parts = [{'ref': ref, 'anchor': {'at': [0.0, 0.0], 'align': 'origin', 'rotation': 0, 'side': 'F'}} for ref in boxes]
        geo = {ref: {'pads': [], 'courtyard': [b[0], -b[3], b[2], -b[1]]} for ref, b in boxes.items()}
        return parts, geo

    fixed = {ref: p['box'] for ref, p in placed.items()}
    fixed.update({o['ref']: o['box'] for o in obstacles})

    def orient(ref, region):
        b = geometry[ref]['courtyard']
        w, h = b[2] - b[0], b[3] - b[1]
        rw, rh = region[2] - region[0], region[3] - region[1]
        rot = 0 if (w >= h) == (rw >= rh) else 90
        if rot == 0 and (w > rw or h > rh) and h <= rw and w <= rh:
            rot = 90
        if rot == 90 and (h > rw or w > rh) and w <= rw and h <= rh:
            rot = 0
        return rot

    def try_pack(gid, region, members):
        parts, geo = as_obstacles(fixed)
        trial = {'groups': [{'id': gid, 'region': region, 'side': 'F', 'gap_mm': 0.5, 'members': members}]}
        try:
            anchors, rows = bg.place_groups(trial, parts + [t for t in template if t['ref'] in {m['ref'] for m in members}],
                                            {**geo, **geometry}, hole_list, outline)
        except SystemExit as error:  # SpecError / PackError
            return None, str(error).replace('board_gen: ', '')
        return (anchors, rows), None

    for group in spec['groups']:
        members = [m['ref'] for m in group['members']]
        demand = sum(area(geometry[m]['courtyard']) for m in members)
        order = [group['region_name']] + list(group.get('alt_regions', [])) + [n for n in regions]
        seen, tried, used_here, remaining = set(), [], [], list(members)
        i = 0
        while i < len(order) and remaining:
            name = order[i]
            i += 1
            if name in seen or name in used:
                continue
            seen.add(name)
            region = regions[name]
            cand = sorted(remaining, key=lambda r: (-round(area(geometry[r]['courtyard']), 6), bg.sort_ref(r)))
            chunk, last = [], None
            for ref in cand:
                member = {'ref': ref, 'rotation': orient(ref, region)}
                ok, why = try_pack(f'{group["id"]}@{name}', region, chunk + [member])
                if ok:
                    chunk.append(member)
                    last = ok
                elif not chunk:
                    tried.append({'region': name, 'first_refusal': why})
            if not chunk:
                continue
            anchors_c, rows_c = last
            gid = f'{group["id"]}@{name}'
            chunks.append({'id': gid, 'region': region, 'side': 'F', 'gap_mm': 0.5, 'members': chunk})
            used.add(name)
            for row in rows_c:
                g = bg.placed_geometry(geometry[row['ref']], anchors_c[row['ref']])
                placed[row['ref']] = {'side': 'F', **g}
                fixed[row['ref']] = g['box']
            placed_here = [m['ref'] for m in chunk]
            remaining = [r for r in remaining if r not in placed_here]
            low = min(placed[r]['box'][1] for r in placed_here)
            if low - 0.5 - region[1] >= 1.5:
                regions[name + '+'] = [region[0], region[1], region[2], r4(low - 0.5)]
                order.insert(i, name + '+')
            used_here.append({'region': name, 'refs': len(placed_here),
                              'courtyard_mm2': r4(sum(area(geometry[r]['courtyard']) for r in placed_here)),
                              'region_mm2': r4(area(region))})
        group_rows.append({'group': group['id'], 'members': len(members), 'courtyard_mm2': r4(demand),
                           'placed_refs': len(members) - len(remaining), 'chunks': used_here,
                           'unplaced_refs': sorted(remaining, key=bg.sort_ref), 'regions_refused': tried})
    # The accepted chunks, re-run once together through board_gen.place_groups, give the plan of record.
    anchor_parts = [p for p in template if p.get('anchor')]
    res_parts, res_geo = as_obstacles({o['ref']: o['box'] for o in obstacles})
    group_anchors, plan_rows = (bg.place_groups({'groups': chunks}, anchor_parts + res_parts + [
        t for t in template if not t.get('anchor')], {**geometry, **res_geo}, hole_list, outline) if chunks else ({}, []))
    for row in plan_rows:
        g = bg.placed_geometry(geometry[row['ref']], group_anchors[row['ref']])
        if g['box'] != placed[row['ref']]['box']:
            raise SystemExit(f'placement_study: the joint re-run moved {row["ref"]}')

    # --- fill ---
    all_refs = [p['ref'] for p in template]
    cy = {r: area(geometry[r]['courtyard']) for r in all_refs}
    reserved_rect_mm2 = sum(area(o['box']) for o in obstacles)
    demand_total = sum(cy.values()) + reserved_rect_mm2 + reserve_mm2
    anchored_mm2 = sum(cy[r] for r in anchored)
    placed_group_refs = sorted({r['ref'] for r in plan_rows}, key=bg.sort_ref)
    unplaced = sorted(set(all_refs) - set(anchored) - set(placed_group_refs), key=bg.sort_ref)
    placed_mm2 = anchored_mm2 + sum(cy[r] for r in placed_group_refs) + reserved_rect_mm2
    # The carved free rectangles of the spec (residual '<name>+' regions lie inside them and are not added again).
    regions_mm2 = sum(area(r) for r in spec['regions']['rects'].values())
    trigger = pspec['fallbacks'][0]
    fill = {
        'label': 'MODEL: courtyard boxes of the vendored KiCad 10.0.7 footprints (F.CrtYd), not a routed board',
        'outline_mm2': r4(outline_area), 'hole_keepouts_mm2': r4(keepout_area), 'usable_mm2': r4(usable),
        'refs': len(all_refs), 'courtyard_sum_mm2': r4(sum(cy.values())),
        'reserved_rects_mm2': r4(reserved_rect_mm2), 'reserved_area_only_mm2': r4(reserve_mm2),
        'demand_mm2': r4(demand_total), 'fill_all_refs': r4(demand_total / usable),
        'budget_raw_fill': budget['candidates'][budget['chosen']]['boards']['PWR_A']['raw_fill'],
        'anchored_refs': len(anchored), 'anchored_mm2': r4(anchored_mm2),
        'free_after_anchors_and_reserves_mm2': r4(usable - anchored_mm2 - reserved_rect_mm2 - reserve_mm2),
        'remaining_demand_mm2': r4(sum(cy.values()) - anchored_mm2),
        'free_regions_of_spec_mm2': r4(regions_mm2),
        'placed_refs': len(anchored) + len(placed_group_refs), 'placed_mm2': r4(placed_mm2),
        'fill_placed': r4(placed_mm2 / usable),
        'unplaced_refs': len(unplaced), 'unplaced_mm2': r4(sum(cy[r] for r in unplaced)),
        'area_to_remove_for_0_60_mm2': r4(demand_total - 0.60 * usable),
        'f2_trigger': trigger['trigger'],
        'f2_fired': (demand_total / usable) > 0.60 or bool(unplaced),
        'f2_fired_why': [w for w, c in (('fill of all PWR_A refs > 0.60', demand_total / usable > 0.60),
                                        ('the planner leaves refs unplaced', bool(unplaced)),
                                        ('fill of the placed subset alone > 0.60', placed_mm2 / usable > 0.60)) if c],
    }

    # --- the F2 options of pcb/partition-spec.json, measured on the same courtyards ---
    radials = {r for r in all_refs if geometry[r]['courtyard'] and next(t for t in template if t['ref'] == r)['fpid']
               .startswith('Capacitor_THT:CP_Radial')}
    f2b_groups = {('E5', 'VBUS HF+ з демпфованим LC'), ('E5', 'VBUS RTL-A і LAB PORT'), ('E5', 'LAB BUS I2C buffer'),
                  ('E2', 'RTL-B: комутований VBUS'), ('E2', 'S-band LaNA WB: захищена шина 5 V')}
    f2b_refs = sorted((r for r in all_refs if (graph[r]['_sheet'], graph[r].get('group')) in f2b_groups
                       and r not in radials), key=bg.sort_ref)
    options = {
        'F2a_pololu_off_board': {'remove': ['U107', 'U108'],
                                 'what': 'Pololu D36V50F12/F5 on plate standoffs (option F2a (c))'},
        'F2b_pcb_rear': {'remove': f2b_refs,
                         'what': 'rear-tier board taking the F2b groups; their THT radials stay on PWR-A (F2b text)'},
    }
    options['F2a_plus_F2b'] = {'remove': sorted(set(options['F2a_pololu_off_board']['remove']) | set(f2b_refs),
                                                key=bg.sort_ref), 'what': 'both options together'}
    f2_rows = {}
    for key, opt in options.items():
        removed = sum(cy[r] for r in opt['remove'])
        f2_rows[key] = {'what': opt['what'], 'refs_removed': opt['remove'], 'courtyard_removed_mm2': r4(removed),
                        'fill_all_refs': r4((demand_total - removed) / usable),
                        'reaches_0_60': (demand_total - removed) / usable <= 0.60}
    fill['f2_options'] = f2_rows

    # --- exit-edge demand (PWR-A anchors and PWR-B headers, both at their courtyard extent along the edge) ---
    spans = edge_spans(contract)
    edges = {}
    for key, span in spans.items():
        lo, hi = span['span']
        # The edge line and the coordinate along it.
        if key == 'bottom':
            line, along, dist = outline_box[1], 0, (lambda h: h['at'][1] - outline_box[1])
        elif key == 'right':
            line, along, dist = outline_box[2], 1, (lambda h: outline_box[2] - h['at'][0])
        elif key == 'top_left':
            line, along, dist = outline_box[3], 0, (lambda h: outline_box[3] - h['at'][1])
        else:
            line, along, dist = span['at'], 0, (lambda h: span['at'] - h['at'][1])
        chords = []
        for h in hole_list:
            r = h['keepout_d'] / 2
            d = dist(h)
            if d < 0 or d - r >= STRIP_DEPTH:  # keepout outside the header strip along this edge
                continue
            c = h['at'][along]
            a, b = max(lo, c - r), min(hi, c + r)
            if b > a:
                chords.append([r4(a), r4(b)])
        blocked = sum(b - a for a, b in chords)
        pwr_a = []
        for ref, e in EXIT_EDGE.items():
            if e == key and ref in placed:
                ext = header_extent(placed[ref]['box'], span['edge'])
                pwr_a.append({'ref': ref, 'extent_mm': r4(ext)})
        pwr_b = []
        for ref, e in PWR_B_EXIT_EDGE.items():
            if e != key or ref not in graph:
                continue
            f = next(x for x in manifest['footprints'] if x['footprint'] == graph[ref]['footprint'])
            b = bg.footprint_geometry((BASE / f['file']).read_text(encoding='utf-8'))['courtyard']
            pwr_b.append({'ref': ref, 'footprint': graph[ref]['footprint'],
                          'extent_mm': r4(max(b[2] - b[0], b[3] - b[1]))})
        need = sum(x['extent_mm'] for x in pwr_a) + sum(x['extent_mm'] for x in pwr_b)
        edges[key] = {'edge': span['edge'], 'at': span['at'], 'span': span['span'], 'use': span['use'],
                      'hole_keepout_chords': chords, 'free_length_mm': r4(hi - lo - blocked),
                      'pwr_a_headers': pwr_a, 'pwr_b_headers_long_side': pwr_b,
                      'pwr_a_need_mm': r4(sum(x['extent_mm'] for x in pwr_a)),
                      'pwr_a_plus_pwr_b_need_mm': r4(need),
                      'single_row_fits': need <= hi - lo - blocked + 1e-9}
    edge_rows_off = [r['ref'] for r in anchor_rows if r['ref'] in EXIT_EDGE and not on_edge(
        placed[r['ref']]['box'], EXIT_EDGE[r['ref']], outline_box, spans)]

    # --- PWR-B cut-outs this placement needs ---
    window_refs = set(budget['candidates'][budget['chosen']]['window_refs'])
    cutouts = []
    for ref in sorted(placed, key=bg.sort_ref):
        if ref.startswith('__'):
            continue
        box = placed[ref]['box']
        kind = None
        if ref in EXIT_EDGE:
            kind = 'header_edge_strip'
        elif ref in window_refs:
            kind = 'window_taller_than_hA'
        elif ref.startswith('TP'):
            kind = 'test_point_probe_window'
        if kind:
            m = margin if kind != 'test_point_probe_window' else (pspec['parameters']['tp_probe_window'] - (box[2] - box[0])) / 2
            rect = [r4(box[0] - m), r4(box[1] - m), r4(box[2] + m), r4(box[3] + m)]
            cutouts.append({'ref': ref, 'kind': kind, 'rect': rect, 'area_mm2': r4(area(rect))})
    unplaced_windows = sorted((r for r in unplaced if r in window_refs or r.startswith('TP')), key=bg.sort_ref)

    # --- THT pads in the thermal_bond zones (plate pockets M-07) ---
    tht = []
    zones = [xywh(z) for z in contract['thermal_bond_mm']]
    for ref in sorted(placed, key=bg.sort_ref):
        if ref.startswith('__'):
            continue
        anchor = anchored.get(ref) or group_anchors.get(ref)
        # THT pads and the NPTH locating pegs (a connector peg stands below the board like a lead).
        tht_pads = [p for p in geometry[ref]['pads'] if p['type'] in ('thru_hole', 'np_thru_hole')]
        if not tht_pads:
            continue
        pts = []
        turned = int(round(float(anchor.get('rotation', 0)) / 90.0)) % 2
        for p in tht_pads:
            q = {**p, 'number': p['number'] or 'NPTH'}
            cx, cy0 = bg.placed_geometry({'pads': [q], 'courtyard': None}, anchor)['pads'][q['number']][0]
            w, h = (p['size'][1], p['size'][0]) if turned else (p['size'][0], p['size'][1])
            pts.append([cx, cy0, w, h])
        field = [r4(min(p[0] - p[2] / 2 for p in pts)), r4(min(p[1] - p[3] / 2 for p in pts)),
                 r4(max(p[0] + p[2] / 2 for p in pts)), r4(max(p[1] + p[3] / 2 for p in pts))]
        in_zone = [i + 1 for i, z in enumerate(zones) if bg.rects_overlap(field, z)]
        tht.append({'ref': ref, 'tht_pads': sum(p['type'] == 'thru_hole' for p in tht_pads),
                    'npth_pegs': sum(p['type'] == 'np_thru_hole' for p in tht_pads), 'pin_field': field,
                    'thermal_bond_zones': in_zone})

    # --- scripted copper, geometric pre-check (KiCad fill and neck widths need the routed board) ---
    cls_of = {n: v['class'] for n, v in netclasses['nets'].items()}
    width_of = {c: v.get('outer_min_width_mm') for c, v in netclasses['classes'].items()}
    split_of = {c: v.get('split_outer_per_layer_mm') for c, v in netclasses['classes'].items()}
    pad_index = []
    for ref, p in placed.items():
        if ref.startswith('__'):
            continue
        tp = next(t for t in template if t['ref'] == ref)
        anchor = anchored.get(ref) or group_anchors.get(ref)
        for pad in geometry[ref]['pads']:
            if not pad['number']:
                continue
            cx, cy0 = bg.placed_geometry({'pads': [pad], 'courtyard': None}, anchor)['pads'][str(pad['number'])][0]
            w, h = pad['size']
            rot = int(round(float(anchor.get('rotation', 0)) / 90.0)) % 2
            if rot:
                w, h = h, w
            pad_index.append({'ref': ref, 'pad': str(pad['number']), 'net': tp['pads'].get(str(pad['number'])),
                              'box': [cx - w / 2, cy0 - h / 2, cx + w / 2, cy0 + h / 2], 'at': [cx, cy0]})
    copper = []
    for track in spec['pre_route'].get('tracks', []):
        ends = []
        for pt in (track['path'][0], track['path'][-1]):
            hit = [f'{p["ref"]}.{p["pad"]}' for p in pad_index if p['net'] == track['net']
                   and p['box'][0] <= pt[0] <= p['box'][2] and p['box'][1] <= pt[1] <= p['box'][3]]
            ends.append(hit)
        cls = cls_of.get(track['net'], netclasses['default_class'])
        need = width_of.get(cls) or 0.0
        copper.append({'id': track['id'], 'kind': 'track', 'net': track['net'], 'class': cls, 'width_mm': track['width_mm'],
                       'class_outer_width_mm': need, 'width_ok': track['width_mm'] + 1e-9 >= need,
                       'end_pads': ends, 'ends_on_net_pads': all(ends), 'locked': bool(track.get('locked', True))})
    for zone in spec['pre_route'].get('zones', []):
        poly = zone['outline']
        zx, zy = [p[0] for p in poly], [p[1] for p in poly]
        zb = [min(zx), min(zy), max(zx), max(zy)]
        cls = cls_of.get(zone['net'], netclasses['default_class'])
        on_net = sorted(f'{p["ref"]}.{p["pad"]}' for p in pad_index if p['net'] == zone['net'] and bg.rects_overlap(p['box'], zb))
        foreign = sorted(f'{p["ref"]}.{p["pad"]}:{p["net"]}' for p in pad_index
                         if p['net'] != zone['net'] and bg.rects_overlap(p['box'], zb))
        need = split_of.get(cls) or width_of.get(cls) or 0.0
        copper.append({'id': zone['id'], 'kind': 'zone', 'net': zone['net'], 'layer': zone['layer'], 'class': cls,
                       'rect_min_width_mm': r4(min(zb[2] - zb[0], zb[3] - zb[1])), 'class_width_per_layer_mm': need,
                       'width_ok': min(zb[2] - zb[0], zb[3] - zb[1]) + 1e-9 >= need,
                       'net_pads_touched': on_net, 'foreign_pads_inside': foreign,
                       'inside_outline': all(bg.point_in_outline(c, outline) for c in poly)})

    # --- boundary: nets that leave PWR-A without a connector pin here ---
    boundary = bg.boundary_audit(spec, template, graph, db)[0]
    dangling = sorted(n['graph_net'] for n in boundary['nets'] if n['status'] == 'dangling')
    b2b = sorted(n['net'] for n in b2b_nets['nets'])

    return {
        'schema': 'srrx-pwra-placement-study-v1',
        'board_id': board,
        'status': 'MODEL / planning result of the board_gen planner (standard library); no KiCad board, no routing, no '
                  'hardware result; bench gates OPEN',
        'generator': 'build/kicad/boards/PWR_A/placement_study.py',
        'inputs': {
            'spec_sha256': bg.sha256_bytes(bg.canonical(spec)),
            'contract_pwr': bg.sha256_bytes(bg.canonical(bg.contract_projection(contract, {}))),
            'contract_pwr_b_outline': bg.sha256_bytes(bg.canonical({k: contract_b.get(k) for k in
                                                                     ('outline_mm', 'cutouts_mm', 'edge_zones')})),
            'template_sha256': bg.sha256_bytes(bg.canonical([{k: p[k] for k in ('ref', 'fpid', 'sha256', 'value', 'pads')}
                                                             for p in template])),
            'project_sha256': bg.sha256_file(BASE / spec['project']),
        },
        'spec_checks': {'validate_spec': 'passed', 'project_rules': project_problems or 'passed',
                        'domain_audit': {'passed': domain['passed'], 'refs': len(domain['domain_refs']),
                                         'missing': domain['missing'], 'foreign': domain['foreign']}},
        'fill': fill,
        'anchors': {'rows': anchor_rows, 'errors': anchor_errors, 'passed': not anchor_errors,
                    'headers_off_their_edge': edge_rows_off},
        'reserved': {'rects': reserved_rows, 'area_only': reserve_rows},
        'groups': group_rows,
        'unplaced_refs': unplaced,
        'exit_edges': edges,
        'pwr_b_cutouts': {'rule': 'pcb/partition-spec.json height_rule and keepouts: courtyard + window_margin for parts '
                                  'taller than hA and for the PWR-A headers; a probe window of tp_probe_window for a test point',
                          'placed': cutouts, 'area_mm2': r4(sum(c['area_mm2'] for c in cutouts)),
                          'unplaced_needing_one': unplaced_windows},
        'tht_pads': {'rule': 'every PWR-A THT pad and NPTH connector peg gets a plate relief pocket >= 1.0 mm and polyimide '
                             'over the 0.4 mm gap (mechanical/params/boards.json tht_pockets); pin_field = pads and pegs; rows '
                             'inside a thermal_bond zone also cut the Gelid pad',
                     'placed': tht, 'unplaced': sorted((r for r in unplaced if any(
                         p['type'] in ('thru_hole', 'np_thru_hole') for p in geometry[r]['pads'])), key=bg.sort_ref)},
        'scripted_copper_precheck': {'label': 'geometry of the spec copper against the planned pads; KiCad fill, '
                                              'thermal spokes and neck widths are checked only on the routed board',
                                     'items': copper},
        'boundary': {'dangling_nets': dangling, 'b2b_nets': len(b2b),
                     'dangling_not_in_b2b': sorted(set(dangling) - set(b2b)),
                     'b2b_not_dangling': sorted(set(b2b) - set(dangling)),
                     'note': 'nets with pins on other boards that end on no graph connector pin of PWR-A; the B2B is '
                             'not a graph ref yet (GR-4), so its nets show as dangling here'},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args(argv)
    text = json.dumps(study(), ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if not OUT.is_file() or OUT.read_text(encoding='utf-8') != text:
            print('placement-study.json is stale: rerun build/kicad/boards/PWR_A/placement_study.py')
            return 1
        print('placement-study.json reproduces')
        return 0
    bg.atomic_write(OUT, text)
    doc = json.loads(text)
    print(json.dumps({'fill': doc['fill'], 'anchors_passed': doc['anchors']['passed'],
                      'unplaced': len(doc['unplaced_refs'])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
