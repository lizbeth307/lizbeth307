#!/usr/bin/env python3
"""PWR-A SHRINK-2 planner spec (W2 PCB-PWRA-3): the two-sided PWR-A of the SHRINK-2 decision, standard library.

  python3 build/kicad/boards/PWR_A/make_spec.py           write PWR_A.spec-shrink2.json next to this file
  python3 build/kicad/boards/PWR_A/make_spec.py --check   fail unless PWR_A.spec-shrink2.json reproduces

The repository port of the scratch builder of the SHRINK-2 re-check (orchestrator decision of 11.11.2026; scratch
evidence, never committed). It reads, and never writes, the design: nothing here edits design/E*.json or the budget.
Inputs:
  PWR_A.spec-draft.json (this directory)       base: layers, project, rules, anchors, groups, scripted copper
  design/E1-E5 (board_gen.load_graph)          refs, footprints, MPNs and pin nets of the graph of record
  pcb/generated/partition.json                 PWR-A domain refs (pcb/prepare.py)
  pcb/partition-spec.json candidates.shrink2   planned changes (blocks w/d, footprints), pwr_a_bottom, h_trim
  pcb/partition-budget.json candidates.shrink2 status of every planned change ('pending' / 'in graph') and the
                                               planned PWR-B ref set (pwr_b_refs)
  pcb/boards/PWR_B.json, pcb/generated/b2b-nets.json   the J209 anchor and the J208 -> J209 contact map
  mechanical/generated/contract/boards.json    thermal_bond zones (MECH-7 writes zones 3'/4'; until then the
                                               planned zones of pwr_a_bottom.thermal_bond_planned are used)

Rules (SHRINK-2 options: F102 holder kept, C506 to PWR-B, 12 V dampers radial):
- A 'pending' change with reserved blocks drops its refs and adds its blocks as reserved areas at BLOCK_AT (zones
  3'/4' at the old module squares, F103 in the top strip); a 'pending' deletion drops its refs; a 'pending' footprint
  swap keeps the ref and records the planned footprint in planned_footprints (placement_study.py uses its courtyard).
  An 'in graph' block change becomes a placement group in the block rectangle: the refs of the change still in the
  graph and the new graph refs of the same schematic group (BLOCK_GROUPS), or carrying a reserve MPN.
- Refs of the planned PWR-B set (budget pwr_b_refs: the 5 V dampers C235-C298 and C506) leave PWR-A.
- The chip refs of pwr_a_bottom.refs go on the bottom side, in one bottom group per top group (BOTTOM_REGION),
  outside the thermal_bond zones (side-B reserved areas) and outside the top THT pin fields + tht_margin
  (placement_study.py adds those as it places the top).
- J208 (LSHM-150, graph ref since W2 B2B) is anchored so that its pad n lies under J209 pad map(n) (b2b-nets.json
  contacts), the B2B2 placeholder of the draft leaves.
- J113/J114/J115/J507 take FFC_PLACES only if the S02 FFC is in the graph (a PWR-A part with a Connector_FFC-FPC
  footprint, GR-5B); otherwise their wip/w2-pwra1 places (PWRA1_PLACES).
- Groups and new refs that no designed region names go to group NEW_UNASSIGNED (all top regions): the study lists
  them; a regeneration after GR-5A/GR-5B/MECH-7 names their regions.
MODEL / planning input only: not a board of record, nothing here is a hardware result; bench gates stay OPEN.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3]  # sat-receiver-audit
sys.path.insert(0, str(BASE / 'pcb'))
import board_gen as bg  # noqa: E402

DRAFT = HERE / 'PWR_A.spec-draft.json'
OUT = HERE / 'PWR_A.spec-shrink2.json'
PARTITION = BASE / 'pcb/generated/partition.json'
PSPEC = BASE / 'pcb/partition-spec.json'
BUDGET = BASE / 'pcb/partition-budget.json'
PWR_B_SPEC = BASE / 'pcb/boards/PWR_B.json'
B2B_NETS = BASE / 'pcb/generated/b2b-nets.json'
CONTRACT = BASE / 'mechanical/generated/contract/boards.json'
CANDIDATE = 'shrink2'
B2B_PAIR = ('J208', 'J209')
FFC_PREFIX = 'Connector_FFC-FPC:'

# Lower-left corner [x, y] (board mm) of each reserved block of the planned changes on the PWR-A top: design choice of the
# SHRINK-2 study (converters in zones 3'/4' at the old module squares; RPP and the F201 fuse beside CONV_SYS12; F103 in
# the top strip of the band). Width and depth come from pcb/partition-spec.json candidates.shrink2.planned.
BLOCK_AT = {'CONV_SYS12': [8.0, 40.0], 'RPP': [8.0, 55.0], 'FUSE_F201': [16.0, 55.0], 'CONV_LAB5': [8.0, 74.0],
            'FUSE_F103': [81.0, 31.0]}
# Schematic group (sheet, group) whose new graph refs fill a block once its change is 'in graph' (GR-5A).
BLOCK_GROUPS = {'CONV_SYS12': ('E1', 'SYS12'), 'CONV_LAB5': ('E1', 'LAB5'), 'RPP': ('E1', 'SYS12'),
                'FUSE_F103': None, 'FUSE_F201': None}
# wip/w2-pwra1 80d92c28 places of the right-edge headers (no FFC), and the FFC places of the SHRINK-2 decision.
PWRA1_PLACES = {'J113': ([117.7, 14.15], 90), 'J114': ([124.5, 4.13], 90), 'J115': ([124.5, 15.29], 90),
                'J507': ([117.7, 2.75], 90)}
FFC_PLACES = {'J113': ([102.0, 2.75], 90), 'J114': ([108.77, 4.13], 90), 'J115': ([116.04, 4.13], 90),
              'J507': ([122.54, 2.75], 90)}
GAP = 0.5  # mm, region edge to a fixed courtyard (the planner gap)

# Top regions of the SHRINK-2 layout (free rectangles after the anchors, J208, the blocks and the hole keepouts; design
# choice). The band keeps the draft regions left of J208; the leg is re-cut for the converter blocks (the SHRINK-2
# study regions LEG_P1/P2/P3/P5 and LEG_HFL for L501); the strip y 26.6-34.8 is free again (no QSH-060) apart from
# the F103 block; around J208 [83.45, 15.4, 114.15, 21.6] the band is cut below, above and beside it.
TOP_REGIONS = {
    'BAND_LNB': [15.8, 7.0, 42.6, 26.8], 'BAND_LEFT': [0.3, 9.8, 9.3, 26.8],
    'BAND_LT_LOW': [43.0, 7.0, 49.4, 11.4], 'BAND_LT_HIGH': [43.0, 22.4, 49.4, 26.8],
    'BAND_LNA': [49.6, 7.0, 72.3, 26.4], 'BAND_BONI': [78.8, 11.2, 82.95, 26.4],
    'BAND_B2B_BELOW': [83.45, 11.2, 115.2, 14.9], 'BAND_B2B_ABOVE': [83.45, 22.1, 107.8, 26.4],
    'BAND_B2B_ABOVE_R': [107.9, 22.1, 115.0, 24.5],
    'BAND_BOTTOM_M': [87.3, 6.3, 99.3, 11.0], 'BAND_BOTTOM_R': [99.6, 0.3, 115.2, 11.0],
    'BAND_COL3_TOP': [115.5, 19.1, 121.0, 24.5], 'BAND_COL2_TOP': [121.53, 22.6, 128.3, 24.5],
    'BAND_TOP_LEFT': [0.3, 27.0, 42.2, 34.8], 'BAND_TOP_MID': [50.0, 26.9, 107.8, 30.8],
    'BAND_TOP_MID2': [89.0, 30.9, 107.8, 34.8], 'BAND_TOP_MID3': [50.0, 30.9, 80.8, 34.8],
    'LEG_BOTTOM': [7.75, 35.2, 33.65, 39.6], 'LEG_LEFT_LOW': [0.3, 35.2, 7.75, 65.5],
    'LEG_LEFT_HIGH': [0.3, 83.0, 7.75, 102.2], 'LEG_P1': [23.2, 39.8, 33.65, 66.0], 'LEG_P2': [8.0, 63.0, 23.0, 73.8],
    'LEG_P3': [23.2, 66.2, 33.65, 83.8], 'LEG_HFL': [20.2, 84.0, 33.65, 97.7], 'LEG_P5': [8.0, 86.1, 20.0, 97.7],
    'LEG_Z3R': [19.9, 54.5, 23.0, 62.8],
    'LEG_RIGHT_LOW': [33.9, 35.2, 41.8, 52.3], 'LEG_RIGHT_HIGH': [33.9, 77.8, 41.8, 102.3],
    'LEG_TOP': [7.8, 97.9, 34.3, 102.8], 'LEG_TOP_L': [7.8, 102.8, 15.3, 109.7], 'LEG_TOP_R': [26.5, 102.8, 34.3, 109.7],
}
# With the FFC the right column is free (J113/J114/J115/J507 on the bottom edge): the SHRINK-2 study region.
FFC_REGIONS = {'drop': ['BAND_BOTTOM_R', 'BAND_COL3_TOP', 'BAND_COL2_TOP'],
               'add': {'BAND_RIGHT_COL': [114.65, 11.5, 128.6, 24.8]}}
# Top group -> (region, alt_regions); groups run in this order (HFP first: L501 needs the leg slot, as in the study).
TOP_GROUPS = [
    ('HFP', 'LEG_HFL', ['BAND_BOTTOM_R', 'LEG_P3']),
    ('LNB', 'BAND_LNB', []), ('LNA4V5', 'BAND_LNA', []), ('BONI', 'BAND_BONI', ['BAND_B2B_BELOW', 'BAND_B2B_ABOVE']),
    ('INA3221_2', 'LEG_RIGHT_LOW', []), ('LAB5', 'LEG_RIGHT_HIGH', ['LEG_LEFT_HIGH', 'BAND_TOP_MID']),
    ('SYS12', 'LEG_P2', ['LEG_RIGHT_LOW', 'LEG_BOTTOM']), ('J21', 'BAND_TOP_LEFT', ['BAND_TOP_MID', 'BAND_BOTTOM_R']),
    ('DISP', 'LEG_TOP', ['BAND_TOP_MID', 'BAND_BOTTOM_R', 'LEG_P3']),
    ('LIME', 'BAND_TOP_MID', ['BAND_BOTTOM_R', 'LEG_P3', 'LEG_TOP']),
    ('AUX12', 'BAND_BOTTOM_R', ['BAND_TOP_MID', 'LEG_P3', 'LEG_TOP']),
    ('E1_CTRL', 'LEG_P3', ['LEG_TOP', 'LEG_RIGHT_LOW', 'LEG_BOTTOM']),
    ('E1_USBPD', 'LEG_BOTTOM', ['LEG_RIGHT_LOW', 'BAND_LT_LOW']),
    ('E5_SERVICE', 'LEG_RIGHT_LOW', ['BAND_LT_LOW', 'BAND_LT_HIGH', 'LEG_BOTTOM']),
    ('E1_SERVICE', 'BAND_B2B_BELOW', ['BAND_TOP_MID']), ('E5_RTLA_LAB', 'LEG_LEFT_HIGH', ['BAND_TOP_MID']),
    ('PWRB_RADIALS', 'LEG_TOP_L', ['LEG_TOP_R', 'LEG_TOP']),
]
# Bottom regions (free rectangles of the bottom face outside the thermal_bond zones; the SHRINK-2 b1 study regions).
BOTTOM_REGIONS = {
    'BB_TOP1': [0.3, 27.2, 42.3, 34.7], 'BB_TOP2': [49.7, 27.2, 107.8, 34.7], 'BB_LEFT': [0.3, 9.8, 8.8, 27.0],
    'BB_GAP': [69.2, 4.2, 71.8, 27.0], 'BL_LEFT': [0.3, 35.2, 6.8, 102.2], 'BL_BOT': [7.0, 35.2, 41.8, 38.8],
    'BL_M1': [24.2, 39.0, 41.8, 52.3], 'BL_M2': [24.2, 59.8, 41.8, 102.3], 'BL_M3': [24.2, 52.5, 34.3, 59.6],
    'BL_M4': [7.0, 63.2, 24.0, 72.8], 'BL_M5': [7.0, 87.2, 24.0, 102.3], 'BL_TOPL': [7.6, 102.5, 15.2, 109.7],
    'BL_TOPR': [26.5, 102.5, 34.3, 109.7],
}
# Bottom group of each top group (the SHRINK-2 b1 study assignment: the nearest free bottom rectangle).
BOTTOM_REGION = {'LNB': 'BB_TOP1', 'LNA4V5': 'BB_GAP', 'BONI': 'BB_TOP2', 'INA3221_2': 'BL_M1', 'SYS12': 'BL_M4',
                 'J21': 'BB_LEFT', 'DISP': 'BL_M5', 'LIME': 'BL_BOT', 'AUX12': 'BL_TOPR', 'HFP': 'BL_M2',
                 'E1_CTRL': 'BL_M2', 'E1_USBPD': 'BL_M3', 'E5_SERVICE': 'BL_LEFT'}
TURN_WHATIF = ['J109', 'J110', 'J111', 'J112']  # PH headers turned by 90 degrees: bottom-edge need and PWR-B strip depth


def r4(v):
    return bg.r4(v)


def b2b_anchor(fp_geo, mate_anchor, pin_map):
    """Anchor of J208 (side F) that puts pad n under J209 pad pin_map[n] (J209 anchored on the PWR-B bottom)."""
    mate = bg.placed_geometry(fp_geo, mate_anchor)['pads']
    for rot in (0, 90, 180, 270):
        local = bg.placed_geometry(fp_geo, {'at': [0.0, 0.0], 'align': 'origin', 'rotation': rot, 'side': 'F'})['pads']
        p1 = local['1'][0]
        m1 = mate[pin_map['1']][0]
        dx, dy = m1[0] - p1[0], m1[1] - p1[1]
        if all(abs(local[n][0][0] + dx - mate[m][0][0]) < 1e-6 and abs(local[n][0][1] + dy - mate[m][0][1]) < 1e-6
               for n, m in pin_map.items()):
            return {'at': [r4(dx), r4(dy)], 'align': 'origin', 'rotation': rot, 'side': 'F'}
    raise SystemExit('make_spec: no rotation of J208 puts every contact under its J209 mate')


def build():
    draft = bg.read_json(DRAFT)
    graph = bg.load_graph()
    manifest = bg.read_json(bg.MANIFEST)
    fps = {f['footprint']: f for f in manifest['footprints']}
    pspec = bg.read_json(PSPEC)
    budget = bg.read_json(BUDGET)
    cand = pspec['candidates'][CANDIDATE]
    bud = budget['candidates'][CANDIDATE]
    contract = bg.read_json(CONTRACT)['boards'][draft['contract']['board']]
    partition = bg.read_json(PARTITION)
    domains = set(draft['domains'])
    domain_refs = sorted((p['ref'] for p in partition['parts'] if p['board_candidate'] in domains and not p['dnp']),
                         key=bg.sort_ref)
    draft_refs = {p['ref'] for p in draft['parts'] if p['source'] == 'graph'}

    # --- planned changes: status from the budget (generated, checked by sr-rx-pcb), content from the spec ---
    status = {row['id']: row for row in bud['planned']['changes']}
    changes = []
    drop, planned_fp, reserved, block_groups = set(), {}, [], []
    for ch in cand['planned']['changes']:
        st = status[ch['id']]['status']
        to = ch['to']
        row = {'id': ch['id'], 'refs': ch['refs'], 'owner': ch.get('owner'), 'status': st}
        if 'merge_into' in to or ch['id'] == 'C506-3x':
            row['effect'] = 'PWR-B (not on PWR-A)'
        elif st == 'pending':
            if to.get('delete'):
                drop |= set(ch['refs'])
                row['effect'] = 'dropped (deleted by the change)'
            elif 'blocks' in to:
                drop |= set(ch['refs'])
                for b in to['blocks']:
                    x, y = BLOCK_AT[b['id']]
                    reserved.append({'id': b['id'], 'rect': [x, y, r4(x + b['w']), r4(y + b['d'])], 'side': 'F',
                                     'kind': 'block', 'h_mm': b['h'], 'stands_for': ch['refs'], 'change': ch['id'],
                                     'what': b['what'], 'source': b['src'],
                                     'position_source': 'design choice of the SHRINK-2 study (make_spec.py BLOCK_AT)'})
                row['effect'] = 'reserved blocks ' + ', '.join(b['id'] for b in to['blocks'])
            else:
                for r in ch['refs']:
                    if r in graph:
                        planned_fp[r] = {'footprint': to['footprint'], 'mpn': to.get('mpn'), 'change': ch['id'],
                                         'graph_footprint': graph[r]['footprint']}
                row['effect'] = f'planned footprint {to["footprint"]}'
        else:
            row['effect'] = 'in graph: the graph counts'
            if 'blocks' in to:
                for b in to['blocks']:
                    block_groups.append({'block': b, 'change': ch})
        changes.append(row)
    for f in planned_fp:
        if planned_fp[f]['footprint'] not in fps:
            raise SystemExit(f'make_spec: planned footprint {planned_fp[f]["footprint"]} of {f} is not vendored')
    pwr_b = set(bud['pwr_b_refs'])

    # --- the PWR-A ref set ---
    keep = [r for r in domain_refs if r not in drop and r not in pwr_b]
    keep_set = set(keep)
    for r in list(planned_fp):
        if r not in keep_set:
            planned_fp.pop(r)
    ffc = sorted(r for r in keep if graph[r].get('footprint', '').startswith(FFC_PREFIX))
    bottom_list = cand['pwr_a_bottom']['refs']
    bottom = [r for r in bottom_list if r in keep_set]
    bottom_missing = [r for r in bottom_list if r not in keep_set]
    bottom_set = set(bottom)

    # --- anchors ---
    by_ref = {p['ref']: p for p in draft['parts']}
    places = FFC_PLACES if ffc else PWRA1_PLACES
    parts, anchored = [], set()
    b2b_contacts = bg.read_json(B2B_NETS)['contacts']
    pin_map = {c['pwr_a_pin']: c['pwr_b_pin'] for c in b2b_contacts}
    spec_b = bg.read_json(PWR_B_SPEC)
    mate = next(p for p in spec_b['parts'] if p['ref'] == B2B_PAIR[1])
    for ref in keep:
        old = by_ref.get(ref)
        if ref == B2B_PAIR[0]:
            fp_geo = bg.footprint_geometry((BASE / fps[graph[ref]['footprint']]['file']).read_text(encoding='utf-8'))
            anchor = b2b_anchor(fp_geo, mate['anchor'], pin_map)
            parts.append({'ref': ref, 'source': 'graph', 'anchor': anchor,
                          'anchor_source': f'under PWR_B {B2B_PAIR[1]} (pcb/boards/PWR_B.json anchor {mate["anchor"]["at"]} '
                                           f'side {mate["anchor"]["side"]} rotation {mate["anchor"]["rotation"]}): pad n of '
                                           f'{ref} under {B2B_PAIR[1]} pad map(n) of pcb/generated/b2b-nets.json contacts '
                                           '(n odd -> n+1, n even -> n-1), computed by make_spec.py b2b_anchor'})
            anchored.add(ref)
            continue
        if old is None or not old.get('anchor'):
            parts.append({'ref': ref, 'source': 'graph'})
            continue
        if ref in ('U107', 'U108'):  # a Pololu square anchor never carries over: the converter is a block group
            parts.append({'ref': ref, 'source': 'graph'})
            continue
        part = {k: v for k, v in old.items()}
        if ref in places:
            at, rot = places[ref]
            part['anchor'] = {**old['anchor'], 'at': at, 'rotation': rot}
            part['anchor_source'] = ('SHRINK-2: the S02 FFC is in the graph, so this header moves to the PWR-A bottom edge '
                                     '(decision place)') if ffc else (
                'SHRINK-2 without the S02 FFC: the wip/w2-pwra1 80d92c28 place (second/third column of the right edge, '
                'the recorded deviation of W2 PCB-PWRA-1); J208 ends at x 114.15, so the column is free again')
            part['anchor'].pop('ref_text', None)
        parts.append(part)
        anchored.add(ref)

    # --- groups ---
    grouped = set()
    draft_groups = {g['id']: g for g in draft['groups']}
    regions = dict(TOP_REGIONS)
    if ffc:
        for k in FFC_REGIONS['drop']:
            regions.pop(k)
        regions.update(FFC_REGIONS['add'])
    groups, bottom_groups = [], []
    for gid, region, alts in TOP_GROUPS:
        g = draft_groups.get(gid)
        if g is None:
            continue
        top = [m for m in g['members'] if m['ref'] in keep_set and m['ref'] not in bottom_set and m['ref'] not in anchored]
        bot = [{'ref': m['ref'], 'rotation': 0} for m in g['members'] if m['ref'] in bottom_set]
        alts = [a for a in alts if a in regions]
        if region not in regions:
            region, alts = alts[0], alts[1:]
        if top:
            groups.append({'id': gid, 'region': regions[region], 'region_name': region, 'alt_regions': alts,
                           'side': 'F', 'gap_mm': g.get('gap_mm', 0.5), 'members': top})
        if bot:
            bname = BOTTOM_REGION[gid]
            bottom_groups.append({'id': gid + '_BOT', 'region': BOTTOM_REGIONS[bname], 'region_name': bname,
                                  'alt_regions': [], 'side': 'B', 'gap_mm': g.get('gap_mm', 0.5), 'members': bot})
        grouped |= {m['ref'] for m in top} | {m['ref'] for m in bot}
    for gid in draft_groups:
        if gid not in {t[0] for t in TOP_GROUPS}:
            raise SystemExit(f'make_spec: draft group {gid} has no SHRINK-2 region (TOP_GROUPS)')
    # 'in graph' block changes: the change refs and the new refs of their schematic group fill the block rectangle
    new_refs = [r for r in keep if r not in draft_refs and r not in anchored]
    for item in block_groups:
        b, ch = item['block'], item['change']
        x, y = BLOCK_AT[b['id']]
        rect = [x, y, r4(x + b['w']), r4(y + b['d'])]
        sg = BLOCK_GROUPS.get(b['id'])
        refs = [r for r in ch['refs'] if r in keep_set and r not in grouped and r not in anchored]
        refs += [r for r in new_refs if r not in grouped and r not in refs and (
            (sg and (graph[r]['_sheet'], graph[r].get('group')) == tuple(sg)) or
            graph[r].get('mpn') in ch.get('until_mpn_in_graph', []))]
        if refs:
            groups.insert(0, {'id': b['id'], 'region': rect, 'region_name': b['id'], 'alt_regions': [], 'side': 'F',
                              'gap_mm': 0.25, 'members': [{'ref': r, 'rotation': 0} for r in refs],
                              'why': f'planned change {ch["id"]} is in the graph: its parts fill the block rectangle'})
            regions[b['id']] = rect
            grouped |= set(refs)
    rest = [r for r in keep if r not in grouped and r not in anchored]
    if rest:
        groups.append({'id': 'NEW_UNASSIGNED', 'region': regions['BAND_TOP_MID'], 'region_name': 'BAND_TOP_MID',
                       'alt_regions': [], 'side': 'F', 'gap_mm': 0.5,
                       'members': [{'ref': r, 'rotation': 0} for r in rest],
                       'why': 'graph refs that no designed SHRINK-2 region names (new since the draft): the study packs '
                              'them anywhere and lists them; a regeneration names their region'})
    # bottom: the thermal_bond zones are side-B obstacles (contract zones 1-2; zones 3/4 planned until MECH-7 lands)
    zones = [list(z) for z in contract['thermal_bond_mm']]
    planned_zones = cand['pwr_a_bottom'].get('thermal_bond_planned', {})
    zone_src = []
    for k, z in sorted(planned_zones.items()):
        i = int(k) - 1
        if zones[i] != list(z):
            zone_src.append(f'zone {k}: planned {z} (pcb/partition-spec.json candidates.shrink2.pwr_a_bottom.'
                            f'thermal_bond_planned; contract still {zones[i]}, MECH-7 pending)')
            zones[i] = list(z)
        else:
            zone_src.append(f'zone {k}: contract {z} (MECH-7 landed)')
    for i, (x, y, w, h) in enumerate(zones, 1):
        reserved.append({'id': f'BOND{i}', 'rect': [x, y, x + w, y + h], 'side': 'B', 'kind': 'thermal_bond',
                         'what': 'thermal_bond zone (Gelid pad on the plate): no bottom-side part',
                         'source': 'mechanical/generated/contract/boards.json PWR thermal_bond_mm' if i <= 2 else
                         '; '.join(s for s in zone_src if s.startswith(f'zone {i}:')) or 'contract'})

    # --- instances, nets, copper ---
    nets = set()
    for r in keep:
        nets |= {pin['net'] for pin in graph[r]['pins'] if pin.get('net') and not pin.get('nc')}
    pre = draft['pre_route']
    lab5_raw = 'E1_LAB5_RAW'  # the pour of the draft ran U108 VOUT -> F102.1; SHRINK-2 re-scripts it from the converter
    pre_route = {
        'tracks': [t for t in pre.get('tracks', []) if t['net'] in nets and t['net'] != lab5_raw],
        'vias': [v for v in pre.get('vias', []) if v['net'] in nets],
        'zones': [z for z in pre.get('zones', []) if z['net'] in nets and z['net'] != lab5_raw],
    }
    post = []
    for z in draft['post_route_zones']:
        zid = z['id']
        if zid in ('GND-BOND-3', 'GND-BOND-4'):
            x, y, w, h = zones[int(zid[-1]) - 1]
            z = {**z, 'outline': [[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
                 'why': f'GND copper on L4 over thermal_bond zone {zid[-1]} (SHRINK-2 converter zone); mask on'}
        if z['net'] in nets:
            post.append(z)
    item = draft['instances']['list'][0]
    inst = {
        'template_nets': sorted(nets),
        'list': [{**{k: v for k, v in item.items() if k not in ('refs', 'nets', 'source')},
                  'refs': {r: r for r in keep}, 'nets': {n: n for n in sorted(nets)},
                  'source': 'identity map (graph refs and nets of the SHRINK-2 PWR-A set)'}],
    }
    for k, v in draft['instances'].items():
        if k not in ('template_nets', 'list'):
            inst[k] = v

    out = {}
    for k, v in draft.items():
        if k in ('split_nets', 'split_nets_note', 'b2b', 'reserved_area_mm2'):
            continue
        if k == 'status':
            v = 'DRAFT_SHRINK2_PLANNER_NOT_FOR_FABRICATION'
        elif k == 'title':
            v = 'PWR-A plate-bonded power board, two-sided SHRINK-2 layout - placement draft'
        elif k == 'note':
            v = ('W2 PCB-PWRA-3: generated by build/kicad/boards/PWR_A/make_spec.py from PWR_A.spec-draft.json, the graph '
                 'and pcb/partition-spec.json candidates.shrink2 (never hand-edited). Kept in build/kicad/boards/PWR_A/, '
                 'not in pcb/boards/: while planned changes are pending (GR-5A, GR-5B, MECH-7) the domain audit fails by '
                 'construction (dropped refs stand as reserved blocks) and placement_study.py uses planned footprints. '
                 'placement_study.py --spec PWR_A.spec-shrink2.json writes placement-study-shrink2.json.')
        elif k == 'parts':
            v = parts
        elif k == 'instances':
            v = inst
        elif k == 'groups':
            v = groups + bottom_groups
        elif k == 'regions':
            v = {'note': 'free rectangles of the SHRINK-2 layout (make_spec.py TOP_REGIONS / BOTTOM_REGIONS, design '
                         'choice); a group names its preferred region and alt_regions; board_gen reads only group.region; '
                         'placement_study.py uses rects for top groups and bottom_rects for bottom groups',
                 'rects': regions, 'bottom_rects': dict(BOTTOM_REGIONS)}
        elif k == 'reserved_areas':
            v = reserved
        elif k == 'pre_route':
            v = pre_route
        elif k == 'post_route_zones':
            v = post
        out[k] = v
    out['budget_candidate'] = CANDIDATE
    out['fallback_id'] = 'F2-C'
    out['reserved_area_mm2'] = [{'id': 'PWR_B_THT_KEEPOUTS', 'area_mm2_source':
                                 f'pcb/partition-budget.json candidates.{CANDIDATE}.pwr_a_keepouts_mm2',
                                 'what': 'rule H-TRIM (pcb/partition-spec.json keepouts.h_trim): the area under the PWR-B THT '
                                         'pin fields is a height zone (parts up to zone_h_max_mm), not a keepout'}]
    out['b2b'] = [{'ref': B2B_PAIR[0], 'mate_board': 'PWR_B', 'mate_ref': B2B_PAIR[1],
                   'pin_map': {k: pin_map[k] for k in sorted(pin_map, key=int)},
                   'pin_map_source': 'pcb/generated/b2b-nets.json contacts (pwr_a_pin -> pwr_b_pin)'}]
    out['planned_footprints'] = {r: planned_fp[r] for r in sorted(planned_fp, key=bg.sort_ref)}
    out['planned_changes'] = changes
    out['two_sided'] = {
        'bottom_refs': bottom, 'bottom_refs_missing': bottom_missing,
        'tht_margin_mm': cand['pwr_a_bottom']['tht_margin'], 'h_room_mm': cand['pwr_a_bottom']['h_room_mm'],
        'thermal_bond_zones': [[x, y, x + w, y + h] for x, y, w, h in zones], 'thermal_bond_zones_source': zone_src,
        'rule': cand['pwr_a_bottom']['rule'],
    }
    out['h_trim'] = {k: pspec['keepouts']['h_trim'][k] for k in ('protrusion_max_mm', 'zone_h_max_mm', 'clearance_mm')}
    out['ffc'] = {'adopted': bool(ffc), 'refs': ffc,
                  'rule': 'the S02 FFC counts as adopted when a PWR-A graph part has a Connector_FFC-FPC footprint (GR-5B); '
                          'then J113/J114/J115/J507 take the decision places on the bottom edge and exit_edges says so'}
    if ffc:
        out['exit_edges'] = {r: 'bottom' for r in FFC_PLACES}
    out['turn_whatif'] = TURN_WHATIF
    out['generator'] = 'build/kicad/boards/PWR_A/make_spec.py'
    bg.validate_spec(out, 'PWR_A')
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args(argv)
    text = json.dumps(build(), ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if not OUT.is_file() or OUT.read_text(encoding='utf-8') != text:
            print('PWR_A.spec-shrink2.json is stale: rerun build/kicad/boards/PWR_A/make_spec.py')
            return 1
        print('PWR_A.spec-shrink2.json reproduces')
        return 0
    bg.atomic_write(OUT, text)
    doc = json.loads(text)
    print(f'{OUT.relative_to(BASE).as_posix()}: {len(doc["parts"])} parts, '
          f'{sum(1 for p in doc["parts"] if p.get("anchor"))} anchored, {len(doc["two_sided"]["bottom_refs"])} bottom, '
          f'{len(doc["reserved_areas"])} reserved areas, {len(doc["planned_footprints"])} planned footprints, '
          f'FFC {doc["ffc"]["adopted"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
