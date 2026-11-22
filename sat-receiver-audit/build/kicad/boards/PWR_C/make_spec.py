#!/usr/bin/env python3
"""Board spec generator of PWR-C, the F2-C front-slab power-entry board (W2 F2C-FALLBACK, PCB-PWRC-2). Standard library only.

  python -I build/kicad/boards/PWR_C/make_spec.py            write pcb/boards/PWR_C.json and PWR_C.kicad_pro
  python -I build/kicad/boards/PWR_C/make_spec.py --check    exit 1 unless both reproduce
  python -I build/kicad/boards/PWR_C/make_spec.py --draft    print placement and copper problems, write nothing

Inputs: the graph (design/E1.json, E5.json: the PWR_ENTRY refs of pcb/generated/partition.json, which pcb/prepare.py takes
from pcb/partition-spec.json partition.domain_override_pwr_c), contract-proposal.json (outline, holes, vent cut-out, in the
component-side frame of this board; mechanical/generated/contract/boards.json PWR_C is the same board in the enclosure frame,
mirrored, and make_spec checks the two agree once the mechanical patch carries it), pcb/generated/netclasses.json and the
vendored footprints (build/kicad/footprints/manifest.json). Every part is a graph ref: the pilot placeholders of the W2
PWRJ-F2C probe (origin/wip/w2-pwrj-f2c 23337c1a) are gone (GR-F2C made U102, R101, C101, C102, U106 and the harness ends
J118-J120 graph parts).

Design (W2 F2C-FALLBACK, choices recorded in README.md and build/15):
- The power copper is scripted, locked and at the class width of its net (pcb/generated/netclasses.json, 4 layers, 1 oz
  outer: BATT 3.2 mm, PWR3A 1.85 mm) from pad to pad: E1_SHUNT_P J105.2 -> R101.1; E1_N R101.2 -> the #2813 U106 VIN group
  (both 0.1 in pins and the large hole) with spurs to F103.1, the TVS D104 cathode and J108.2; E1_SW from the U106 VOUT group
  to J119.2 (W-C1) with the TVS D105 cathode; E1_SERVICE_P F103.2 -> J115.2; E1_USB_PD_RAW J114.2 -> the U109 IN bar (poured
  along the bar) with C116; E1_USB_PD_SAFE from the U109 OUT bar (poured along the bar) with C117 to J108.3; LAB5 J118.2 ->
  U553 IN with C552 (>= 1.335 mm: F102 4 A at +20 degC on 1 oz, IPC-2221 MODEL). The TVS anodes sit on F.Cu GND pours with
  plane vias. No branch_exempt or neck_exempt on J105, R101, U106, J118, J119, F103, J108, J114, J115, D104 or D105.
- The router (Freerouting) joins only low-current branches: the INA228 sense/VBUS pins at 0.2 mm (class PWRC_SENSE), the
  AON LDO input, dividers, test points and decoupling (class PWRC_BRANCH 0.5 mm); branch_exempt names exactly those refs.
- In1.Cu and In2.Cu are GND planes; every SMD GND pad gets a locked plane via (gnd_fanout of build/kicad/boards/PWR_A/make_board.py).
CI/MODEL input only: the routed board, report and fab set are CI outputs ('[pcb-route PWR_C]', applied as 'GENERATED:'); no
fabrication release, every bench gate stays OPEN.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3]  # sat-receiver-audit
sys.path.insert(0, str(BASE / 'pcb'))
sys.path.insert(0, str(BASE / 'build/kicad/boards/PWR_A'))
import board_gen as bg  # noqa: E402
import make_board as mb  # noqa: E402  (PWR_A: Placed, pad_copper, gnd_fanout, geometry helpers)

BOARD = 'PWR_C'
SPEC = BASE / 'pcb/boards/PWR_C.json'
PROJECT = HERE / 'PWR_C.kicad_pro'
CONTRACT = HERE / 'contract-proposal.json'
MECH_CONTRACT = BASE / 'mechanical/generated/contract/boards.json'
ENC_PROJECT = BASE / 'build/kicad/boards/ENC/ENC.kicad_pro'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
PARTITION = BASE / 'pcb/generated/partition.json'
PWRA_SPEC = BASE / 'build/kicad/boards/PWR_A/board-spec.json'
TAG = 'W2 F2C-FALLBACK (PCB-PWRC-2)'
CLEAR, MARGIN, EDGE = mb.CLEAR, mb.MARGIN, mb.EDGE
BATT_W, PWR3A_W = 3.2, 1.85     # netclasses.json BATT / PWR3A outer_min_width_mm (1 oz outer, 4 layers)
LAB5_W = 1.85                   # PWR3A; >= 1.335 mm (F102 4 A at +20 degC, 1 oz outer, IPC-2221 MODEL)
# class width per scripted net (pcb/generated/netclasses.json nets: BATT E1_SHUNT_P / E1_N / E1_SW, PWR3A E1_SERVICE_P /
# E1_USB_PD_RAW / E1_USB_PD_SAFE / LAB5; GND has no power class, SIG 0.15)
NET_W = {'E1_SHUNT_P': BATT_W, 'E1_N': BATT_W, 'E1_SW': BATT_W, 'E1_SERVICE_P': PWR3A_W, 'E1_USB_PD_RAW': PWR3A_W,
         'E1_USB_PD_SAFE': PWR3A_W, 'LAB5': LAB5_W, 'GND': 0.15}

# Anchors (board mm, y up, origin align; design choice, component-side frame of contract-proposal.json): ref -> (x, y, rot).
# Left: the battery entry (J105 S05 from PACK_FUSE, shunt R101, INA228 U102), the E1_N bus up the left side of the #2813, the
# service fuse F103 and J115 (S12), J108 (S10 to the IP2368), J120 (W-C2 to CTRL) and the TVS D104 on E1_N. Middle: the
# #2813 U106 flush on its land (VIN column left, VOUT column right, the power rows and large holes up). Right of it: the
# E1_SW pour to J119 (W-C1 to PWR-A J107) with the TVS D105 and the switch group. Above the vent cut-out: J118 (W-C1 LAB5
# from PWR-A J106). Right: the E5 IMU service (U553, U551, J507 S32), the UV supervisor, the USB-PD eFuse U109 with J114 and
# J113 (S11), J112 (S10 signals) and J109 (S05 NTC).
ANCHORS = {
    'J105': (11.0, 2.6, 0), 'R101': (23.6, 2.6, 0), 'U102': (23.2, 7.6, 0),
    'J120': (10.9, 21.9, 180), 'J108': (15.6, 30.8, 0), 'J115': (30.7, 30.8, 0),
    'F103': (33.0, 25.1, 90), 'D104': (22.0, 23.5, 0),
    'U106': (50.16, 18.16, 0),
    'D105': (66.0, 24.5, 0), 'J119': (68.5, 30.8, 180),
    'J118': (92.0, 30.8, 0), 'U553': (101.0, 18.0, 0), 'C552': (99.0, 22.0, 0),
    'J507': (115.95, 26.5, 180), 'J112': (127.45, 26.5, 180), 'J109': (134.95, 26.5, 180), 'J113': (142.45, 26.5, 180),
    'J114': (147.1, 30.8, 0), 'U109': (139.0, 15.0, 0), 'C116': (136.0, 19.5, 180), 'C117': (136.0, 9.0, 180),
    # route run 45044664444 (3 unconnected): R116 (ILM) and C115 (dV/dt) right of U109, beside its pins 9 and 7, which the
    # IN/OUT bar pours and the pin-8 GND via boxed in from the left group; Q101 out of the U104 - D101 row (E1_UV_OFF);
    # D102 / D103 left of the #2813 beside J120 (PICO_OFF, PWR_BUTTON short; E1_MASTER_OFF and E1_SWITCH_A reach the
    # #2813 OFF / A pins under the module on B.Cu instead of two runs across the board)
    'R116': (144.6, 15.6, 0), 'C115': (144.6, 13.3, 0), 'Q101': (120.0, 9.5, 0),
    'D102': (29.5, 15.6, 0), 'D103': (22.5, 15.6, 180),
}
# Placement groups (region [x0, y0, x1, y1], members); pcb/board_gen.py packs them in this order (CI computes the same).
GROUPS = [
    ('INA', [26.6, 5.2, 30.1, 13.4], ['C101', 'C102']),
    ('AON', [11.3, 5.0, 19.9, 17.6], ['U103', 'C103', 'C104', 'C105', 'R103', 'TP104', 'TP106']),
    ('SWITCH', [60.9, 5.5, 70.6, 21.6], ['R111', 'TP105']),
    ('E5', [103.4, 8.0, 112.4, 23.6], ['U551', 'C553', 'R553', 'TP503', 'R112', 'C114', 'TP107']),
    ('UV', [112.8, 12.0, 128.0, 22.0], ['U104', 'R104', 'R105', 'R106', 'R107', 'C106', 'D101', 'TP108',
                                        'R121', 'R122', 'R123']),
    ('USBPD', [128.4, 6.0, 134.0, 22.0], ['R113', 'R114', 'R115', 'TP103']),
]
SENSE_NETS = {'E1_N', 'E1_SHUNT_P'}    # router class PWRC_SENSE 0.2 mm: only sense and small loads are left to the router


def r4(v):
    return round(float(v) + 0.0, 4)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


class Inputs:
    def __init__(self):
        self.graph = bg.load_graph()
        self.manifest = bg.read_json(bg.MANIFEST)
        self.fps = {f['footprint']: f for f in self.manifest['footprints']}
        self.netclasses = read(NETCLASSES)
        self.cfile = read(CONTRACT)
        self.contract = self.cfile['boards'][BOARD]
        self.outline = [tuple(p) for p in self.contract['outline_mm']]
        part = read(PARTITION)
        self.refs = sorted((p['ref'] for p in part['parts'] if p['board_candidate'] == 'PWR_ENTRY' and not p['dnp']),
                           key=bg.sort_ref)
        self.text = {r: (BASE / self.fps[self.graph[r]['footprint']]['file']).read_text(encoding='utf-8') for r in self.refs}
        self.nets_of = {r: {str(p['number']): p.get('net') for p in self.graph[r]['pins'] if p.get('net')} for r in self.refs}
        self.geo = {}
        for r, text in self.text.items():
            geo = bg.footprint_geometry(text)
            keep = []
            for p, (cu, fbox) in zip(geo['pads'], mb.pad_copper(text)):
                if cu or p['type'] == 'np_thru_hole':
                    keep.append({**p, 'fbox': fbox})
            self.geo[r] = {**geo, 'pads': keep}


# Reference texts moved inside the outline (route run 45039071310: silk_edge_clearance on the default legends of the top-edge
# lands): ref -> board mm
REF_TEXT = {'J108': [18.3, 27.9], 'J114': [149.8, 27.9], 'J115': [27.9, 27.4], 'J118': [94.7, 27.9]}


def anchor_of(at, rot, ref=None):
    a = {'at': [r4(at[0]), r4(at[1])], 'align': 'origin', 'rotation': rot, 'side': 'F'}
    if ref in REF_TEXT:
        a['ref_text'] = {'at': REF_TEXT[ref], 'angle': 0}
    return a


def spec_parts(inp):
    grouped = {m for _, _, ms in GROUPS for m in ms}
    parts = []
    for r in inp.refs:
        if r in ANCHORS:
            parts.append({'ref': r, 'source': 'graph', 'anchor': anchor_of(ANCHORS[r][:2], ANCHORS[r][2], r),
                          'anchor_source': f'{TAG}: make_spec.py ANCHORS (design choice)'})
        elif r in grouped:
            parts.append({'ref': r, 'source': 'graph'})
        else:
            raise SystemExit(f'make_spec: {r} has neither an anchor nor a group')
    return parts


def groups_json():
    return [{'id': gid, 'region': region, 'side': 'F', 'gap_mm': 0.4, 'members': [{'ref': m, 'rotation': 0} for m in members]}
            for gid, region, members in GROUPS]


def plan(inp, parts):
    """Group anchors as board_gen computes them in CI (place_groups, deterministic)."""
    spec = {'groups': groups_json(), 'parts': parts}
    holes = [{'ref': f'H{i}', 'at': list(h), 'd': inp.contract['hole_d'], 'keepout_d': inp.contract['hole_keepout_d']}
             for i, h in enumerate(inp.contract['holes_mm'], 1)]
    template = [{'ref': p['ref'], 'anchor': p.get('anchor')} for p in parts]
    geometry = {r: bg.footprint_geometry(inp.text[r]) for r in inp.text}
    cut = [[x, y, x + w, y + h] for x, y, w, h in inp.contract.get('cutouts_mm', [])]
    anchors, rows = bg.place_groups(spec, template, geometry, holes, inp.contract['outline_mm'], cut)
    return anchors, rows


def placed_all(inp, parts, anchors):
    return {p['ref']: mb.Placed(p['ref'], inp.geo[p['ref']], p.get('anchor') or anchors[p['ref']], inp.nets_of[p['ref']])
            for p in parts}


def pad(placed, ref, num):
    hits = [p for p in placed[ref].pads if p['number'] == num]
    if not hits:
        raise SystemExit(f'make_spec: {ref} has no pad {num}')
    return hits


def bbox_of(pads_):
    return (min(p['box'][0] for p in pads_), min(p['box'][1] for p in pads_), max(p['box'][2] for p in pads_),
            max(p['box'][3] for p in pads_))


# ------------------------------------------------------------------ scripted power copper
def rect_union(rects):
    """The outline of the union of axis-aligned rectangles [x0, y0, x1, y1] that overlap into one piece without holes, as a
    counter-clockwise rectilinear polygon (coordinate compression and boundary tracing; standard library). KiCad removes a zone
    fill island that holds no pad of its net and does not join overlapping zones of one net (route run 45039071310: zones_intersect
    and island removal), so each connected piece of scripted copper is one zone."""
    xs = sorted({r[0] for r in rects} | {r[2] for r in rects})
    ys = sorted({r[1] for r in rects} | {r[3] for r in rects})
    cov = set()
    for x0, y0, x1, y1 in rects:
        for i in range(len(xs) - 1):
            if xs[i] >= x0 - 1e-9 and xs[i + 1] <= x1 + 1e-9:
                for j in range(len(ys) - 1):
                    if ys[j] >= y0 - 1e-9 and ys[j + 1] <= y1 + 1e-9:
                        cov.add((i, j))
    edges = {}
    for i, j in cov:
        # counter-clockwise edges of the cell that border an uncovered cell, keyed by their start vertex
        for (a, b, n) in (((i, j), (i + 1, j), (i, j - 1)), ((i + 1, j), (i + 1, j + 1), (i + 1, j)),
                          ((i + 1, j + 1), (i, j + 1), (i, j + 1)), ((i, j + 1), (i, j), (i - 1, j))):
            if n not in cov:
                edges.setdefault(a, []).append(b)
    loops = []
    while edges:
        start = next(iter(edges))
        loop, cur = [start], start
        while True:
            nxt = edges[cur].pop()
            if not edges[cur]:
                del edges[cur]
            if nxt == start:
                break
            loop.append(nxt)
            cur = nxt
        loops.append(loop)
    if len(loops) != 1:
        raise SystemExit(f'make_spec: a scripted pour is {len(loops)} loops (a hole or two pieces): {rects}')
    pts = [(xs[i], ys[j]) for i, j in loops[0]]
    out = []
    for k, p in enumerate(pts):  # drop collinear vertices
        a, c = pts[k - 1], pts[(k + 1) % len(pts)]
        if not ((abs(a[0] - p[0]) < 1e-9 and abs(c[0] - p[0]) < 1e-9) or (abs(a[1] - p[1]) < 1e-9 and abs(c[1] - p[1]) < 1e-9)):
            out.append([r4(p[0]), r4(p[1])])
    return out


def merge_pours(pieces):
    """pieces [(id, net, layer, rect, why)] -> one zone per connected group of overlapping rectangles of one net and layer, each with
    its own priority (no two scripted zones share one: KiCad zones_intersect)."""
    groups = []
    for pid, net, layer, rc, why in pieces:
        rc = [r4(v) for v in rc]
        hit = [g for g in groups if g['net'] == net and g['layer'] == layer and any(
            rc[0] < q[2] + 1e-9 and q[0] < rc[2] + 1e-9 and rc[1] < q[3] + 1e-9 and q[1] < rc[3] + 1e-9 for q in g['rects'])]
        g = {'net': net, 'layer': layer, 'ids': [pid], 'rects': [rc], 'why': [why]}
        for h in hit:
            g['ids'] = h['ids'] + g['ids']
            g['rects'] = h['rects'] + g['rects']
            g['why'] = h['why'] + g['why']
            groups.remove(h)
        groups.append(g)
    zones = []
    for k, g in enumerate(groups):
        zones.append({'id': g['ids'][0], 'net': g['net'], 'layer': g['layer'], 'outline': rect_union(g['rects']),
                      'priority': 2 + k, 'pad_connection': 'solid', 'clearance_mm': CLEAR,
                      'why': f'{TAG}: ' + '; '.join(g['why']) + ' (make_spec.py power_copper; pieces ' + ', '.join(g['ids']) + ')',
                      '_rects': g['rects']})
    return zones


def power_copper(placed):
    """(zones, tracks, vias) of the scripted power copper: rectilinear F.Cu pours at the class width of their net, each
    covering the pads it joins (solid pad connection), and the TVS anode GND pours with their plane vias."""
    pieces, tracks, vias = [], [], []

    def zone(zid, net, outline, why, priority=2, layer='F.Cu'):
        xs, ys = [q[0] for q in outline], [q[1] for q in outline]
        pieces.append((zid, net, layer, [min(xs), min(ys), max(xs), max(ys)], why))

    def track(tid, net, width, path, why, layer='F.Cu'):
        tracks.append({'id': tid, 'net': net, 'layer': layer, 'width_mm': width, 'path': [[r4(x), r4(y)] for x, y in path],
                       'locked': True, 'why': f'{TAG}: {why} (make_spec.py power_copper)'})

    def via(vid, net, at, why):
        vias.append({'id': vid, 'net': net, 'at': [r4(at[0]), r4(at[1])], 'drill_mm': mb.VIA_DRILL, 'diameter_mm': mb.VIA_D,
                     'locked': True, 'why': f'{TAG}: {why}'})

    j105 = pad(placed, 'J105', '2')[0]['at']
    r1, r2 = pad(placed, 'R101', '1')[0]['at'], pad(placed, 'R101', '2')[0]['at']
    track('PC-SHUNTP', 'E1_SHUNT_P', BATT_W, [j105, r1], 'BATT 3.2 mm: S05 land J105.2 to the shunt R101.1 (battery side)')
    # E1_N: R101.2 -> up the left side of the #2813 (x 30.4-33.6) -> the VIN group (pins VIN, VIN and the VIN large hole)
    vin = bbox_of(pad(placed, 'U106', 'VIN'))
    gnd_pin = min((p for p in pad(placed, 'U106', 'GND') if abs(p['at'][0] - vin[0] - 0.85) < 2.0),
                  key=lambda p: -p['at'][1])  # the GND pin of the VIN column next to the VIN pins
    y_low = r4(gnd_pin['box'][3] + CLEAR + 0.05)
    xs0, xs1 = 35.4, 38.6
    zone('PC-E1N-SHUNT', 'E1_N', rect(r2[0] - 1.25, r2[1] - BATT_W / 2, xs1, r2[1] + BATT_W / 2),
         'BATT 3.2 mm: shunt R101.2 to the E1_N bus')
    zone('PC-E1N-BUS', 'E1_N', rect(xs0, r2[1] - BATT_W / 2, xs1, y_low + 3.3), 'BATT 3.2 mm: the E1_N bus up the left of the #2813')
    zone('PC-E1N-VIN', 'E1_N', rect(xs1 - 0.6, y_low, vin[2] + 0.2, min(vin[3] - 0.4, 30.4)),
         'BATT: the #2813 VIN group (two 0.1 in pins and the large hole, Pololu: above 5 A both pins or the large hole per node)')
    f1 = pad(placed, 'F103', '1')[0]
    f2 = pad(placed, 'F103', '2')[0]
    (fb, ft) = (f1, f2) if f1['at'][1] < f2['at'][1] else (f2, f1)
    e1n_fuse, svc = (fb, ft) if placed['F103'].pads[0]['net'] == 'E1_N' else (fb, ft)
    e1n_pad = f1 if f1['net'] == 'E1_N' else f2
    svc_pad = f2 if e1n_pad is f1 else f1
    y_h0, y_h1 = 18.0, 18.0 + BATT_W
    zone('PC-E1N-WEST', 'E1_N', rect(14.0, y_h0, xs0 + 0.6, y_h1), 'BATT 3.2 mm: E1_N west to the J108.2 spur, F103 and D104')
    zone('PC-E1N-F103', 'E1_N', rect(e1n_pad['at'][0] - 1.6, y_h1 - 0.6, e1n_pad['at'][0] + 1.6, e1n_pad['box'][3] + 0.1),
         'BATT 3.2 mm: up to the fuse F103.1')
    j108 = pad(placed, 'J108', '2')[0]
    zone('PC-E1N-J108', 'E1_N', rect(j108['at'][0] - 1.6, y_h1 - 0.6, j108['at'][0] + 1.6, j108['box'][3] + 0.05),
         'BATT 3.2 mm: up to the S10 land J108.2 (IP2368 BAT+)')
    k104 = pad(placed, 'D104', 'K')[0]
    zone('PC-E1N-D104', 'E1_N', rect(k104['box'][0] - 0.6, y_h1 - 0.6, k104['box'][0] - 0.6 + BATT_W, k104['box'][3] + 0.1),
         'BATT 3.2 mm: the TVS D104 cathode at the class width')
    j115 = pad(placed, 'J115', '2')[0]
    zone('PC-SERVICE', 'E1_SERVICE_P', rect(svc_pad['at'][0] - 0.4, svc_pad['at'][1] - 0.5,
                                            max(svc_pad['at'][0], j115['at'][0]) + PWR3A_W / 2, j115['at'][1] + PWR3A_W / 2),
         'PWR3A 1.85 mm: F103.2 to the S12 land J115.2 (service XT30)')
    # E1_SW: the VOUT group (pins VOUT, VOUT and the VOUT large hole) -> J119.2 (W-C1 to PWR-A J107), the TVS D105 cathode
    vout = bbox_of(pad(placed, 'U106', 'VOUT'))
    j119 = pad(placed, 'J119', '2')[0]
    k105 = pad(placed, 'D105', 'K')[0]
    zone('PC-E1SW-VOUT', 'E1_SW', rect(vout[0] - 0.2, y_low, max(vout[2] + 0.2, k105['box'][2] + 0.1), min(vout[3] - 0.4, 30.4)),
         'BATT: the #2813 VOUT group and the TVS D105 cathode')
    zone('PC-E1SW-J119', 'E1_SW', rect(vout[2] - 2.0, 28.0, j119['box'][2] + 0.05, j119['box'][3] + 0.05),
         'BATT 3.2 mm: to the W-C1 land J119.2 (E1_SW to PWR-A J107)')
    # TVS anodes on F.Cu GND pours with two plane vias each (TVS GND at the class width, not a fan-out stub)
    for ref in ('D104', 'D105'):
        a = pad(placed, ref, 'A')[0]
        bx = a['box']
        zone(f'PC-GND-{ref}', 'GND', rect(bx[0] - 0.05, bx[1] - 0.1, bx[2] + 0.1, bx[3] + 2.6),
             f'GND of the TVS {ref} anode at the pad width and two stacked plane vias above it', priority=2)
        via(f'PC-GND-{ref}-V1', 'GND', (a['at'][0], bx[3] + 0.9), f'GND plane via of the TVS {ref} anode pour')
        via(f'PC-GND-{ref}-V2', 'GND', (a['at'][0], bx[3] + 1.9), f'GND plane via of the TVS {ref} anode pour')
    # USB-PD (TI SLVSFC9C figure 8-22: IN leaves at one bar end, OUT at the other): J114.2 -> the U109 IN bar (pin 5) poured
    # along its length, its top-end landing at the class width and C116.1; the OUT bar (pin 6) poured along its length, its
    # bottom-end landing, C117.1, a via cluster to B.Cu and the B.Cu run along the bottom edge to the S10 land J108.3 (THT)
    j114 = pad(placed, 'J114', '2')[0]
    inb, outb = pad(placed, 'U109', '5')[0]['box'], pad(placed, 'U109', '6')[0]['box']
    c116, c117 = pad(placed, 'C116', '1')[0], pad(placed, 'C117', '1')[0]
    gap = 0.2   # bar end to its landing (TI: the bar leaves at its end); within half the PWR3A width of the bar
    xin = (inb[0] + inb[2]) / 2
    zone('PC-PDRAW-BAR', 'E1_USB_PD_RAW', rect(inb[0], inb[1], inb[2], inb[3] + gap), 'the U109 IN bar poured along its length')
    lin = (xin - 0.9, inb[3] + gap, xin - 0.9 + PWR3A_W, inb[3] + gap + PWR3A_W)
    zone('PC-PDRAW-LAND', 'E1_USB_PD_RAW', rect(*lin), 'PWR3A 1.85 mm landing at the IN bar end')
    zone('PC-PDRAW-C116', 'E1_USB_PD_RAW', rect(c116['box'][0] - 0.05, lin[3] - 0.05, lin[2], c116['box'][3] + 0.05),
         'PWR3A: the input capacitor C116.1 on the landing')
    zone('PC-PDRAW-EAST', 'E1_USB_PD_RAW', rect(lin[0], lin[1], j114['at'][0] + PWR3A_W / 2, lin[3]),
         'PWR3A 1.85 mm: east to the J114 column')
    zone('PC-PDRAW-J114', 'E1_USB_PD_RAW', rect(j114['at'][0] - PWR3A_W / 2, lin[1], j114['at'][0] + PWR3A_W / 2,
                                                j114['box'][3] + 0.05), 'PWR3A 1.85 mm: up to the S11 land J114.2 (USB-C VBUS)')
    xout = (outb[0] + outb[2]) / 2
    zone('PC-PDSAFE-BAR', 'E1_USB_PD_SAFE', rect(outb[0], outb[1] - gap, outb[2], outb[3]), 'the U109 OUT bar poured along its length')
    lout = (xout - 0.9, outb[1] - gap - PWR3A_W, xout - 0.9 + PWR3A_W, outb[1] - gap)
    zone('PC-PDSAFE-LAND', 'E1_USB_PD_SAFE', rect(*lout), 'PWR3A 1.85 mm landing at the OUT bar end')
    y_via = 6.4
    zone('PC-PDSAFE-DOWN', 'E1_USB_PD_SAFE', rect(c117['box'][0] - 0.05, y_via - 1.0, lout[2], lout[1]),
         'PWR3A: C117.1 and the via cluster to B.Cu')
    vx = [round(c117['box'][2] + 0.8 + 1.0 * k, 4) for k in range(3)]
    for k, x in enumerate(vx):
        for j, y in enumerate((y_via - 0.5, y_via + 0.5)):
            via(f'PC-PDSAFE-V{k * 2 + j + 1}', 'E1_USB_PD_SAFE', (x, y), 'E1_USB_PD_SAFE F.Cu -> B.Cu (6 vias 0.7 / 0.3 for 3.5 A, MODEL)')
    j108_3 = pad(placed, 'J108', '3')[0]
    y_safe = 3.0

    def bzone(zid, outline, why):
        zone(zid, 'E1_USB_PD_SAFE', outline, why, layer='B.Cu')
    bzone('PC-PDSAFE-B-VIAS', rect(vx[0] - 0.9, y_safe - PWR3A_W / 2, vx[-1] + 0.9, y_via + 1.0), 'B.Cu under the via cluster')
    bzone('PC-PDSAFE-B-RUN', rect(j108_3['at'][0] - PWR3A_W / 2, y_safe - PWR3A_W / 2, vx[-1] + 0.9, y_safe + PWR3A_W / 2),
          'PWR3A 1.85 mm on B.Cu along the bottom edge, under the shunt and the #2813 (outer layer, power class allowed)')
    bzone('PC-PDSAFE-B-UP', rect(j108_3['at'][0] - PWR3A_W / 2, y_safe, j108_3['at'][0] + PWR3A_W / 2, j108_3['box'][3] + 0.05),
          'PWR3A 1.85 mm on B.Cu up to the S10 land J108.3 (THT, so no via at this end)')
    # LAB5: J118.2 (W-C1 from PWR-A J106) -> straight down to U553 IN (pin 1) and C552.1 beside the column
    j118 = pad(placed, 'J118', '2')[0]
    u553 = pad(placed, 'U553', '1')[0]
    c552 = pad(placed, 'C552', '1')[0]
    xl0 = j118['at'][0] - LAB5_W / 2
    zone('PC-LAB5-DOWN', 'LAB5', rect(xl0, u553['box'][1] - 0.3, xl0 + LAB5_W, j118['box'][3] + 0.05),
         'PWR3A 1.85 mm (>= 1.335 mm for F102 4 A on 1 oz): the W-C1 land J118.2 straight down to U553')
    zone('PC-LAB5-U553', 'LAB5', rect(xl0 + LAB5_W - 0.05, u553['box'][1] - 0.05, u553['box'][2] + 0.05, u553['box'][3] + 0.05),
         'the U553 IN pin entry: one pin pitch tall, within half the class width of the pin')
    zone('PC-LAB5-C552', 'LAB5', rect(xl0, c552['box'][1] - 0.05, c552['box'][2] + 0.05, c552['box'][3] + 0.05),
         'PWR3A: C552.1 on the column beside U553 IN')
    # Locked skeleton tracks (route run 45043947453: Freerouting led other nets across the pours and KiCad then cut them into
    # islands: 5 unconnected PC-E1N-SHUNT pieces, D105.K off the E1_SW pour, the E1_USB_PD_SAFE B.Cu run apart from its vias;
    # PWR_A met the same in run 43287918183): every piece at least its class width wide carries one locked track of its net
    # along its long axis, as wide as its short side and inside it, which the router keeps as fixed copper; the pour still
    # fills the piece and joins the pieces. Narrower pin-entry pieces (the U109 bars, the U553 / C552 entries) stay pours.
    for zid, net, layer, r, why in pieces:
        need = NET_W.get(net, NET_W['GND'])
        w, h = r[2] - r[0], r[3] - r[1]
        short = min(w, h)
        if short + 1e-9 < need:
            continue
        if w >= h:
            a, b = (r[0] + h / 2, (r[1] + r[3]) / 2), (max(r[2] - h / 2, r[0] + h / 2 + 0.002), (r[1] + r[3]) / 2)
        else:
            a, b = ((r[0] + r[2]) / 2, r[1] + w / 2), ((r[0] + r[2]) / 2, max(r[3] - w / 2, r[1] + w / 2 + 0.002))
        track(f'{zid}-SK', net, r4(math.floor(short * 1000) / 1000), [a, b],
              f'locked skeleton of the pour {zid} (its short side, >= the {net} class width {need} mm): the router keeps '
              'other nets off the pour', layer=layer)
    # U109 pins 9 (E1_PD_ILM) and 7 (E1_PD_DVDT) on the right side: locked escapes in their own lanes to R116.1 and C115.1
    # (route run 45044664444 left E1_PD_ILM open), so the pin-8 GND fan-out takes the lane between them
    for num, ref, nid in (('9', 'R116', 'ILM'), ('7', 'C115', 'DVDT')):
        u = pad(placed, 'U109', num)[0]
        q = pad(placed, ref, '1')[0]
        xk = u['box'][2] + 1.0
        track(f'PC-PD-{nid}', u['net'], 0.2, [u['at'], (xk, u['at'][1]), (xk, q['at'][1]), q['at']],
              f'{u["net"]}: U109.{num} escape to {ref}.1 in its own lane beside the pin-8 GND lane')
    zones = merge_pours(pieces)  # each zone carries its piece rectangles in '_rects' for problems() (not written to the spec)
    return zones, tracks, vias


# ------------------------------------------------------------------ checks (before CI routes)
def box_overlap(a, b, gap=0.0):
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def zone_box(z):
    xs = [p[0] for p in z['outline']]
    ys = [p[1] for p in z['outline']]
    return (min(xs), min(ys), max(xs), max(ys))


def zone_rects(z):
    return [tuple(r) for r in z.get('_rects') or [zone_box(z)]]


def problems(inp, placed, zones, tracks, vias):
    out = []
    outline = inp.outline
    cuts = [[x, y, x + w, y + h] for x, y, w, h in inp.contract.get('cutouts_mm', [])]
    holes = [tuple(h) for h in inp.contract['holes_mm']]
    kr = inp.contract['hole_keepout_d'] / 2
    refs = sorted(placed)
    for i, a in enumerate(refs):
        A = placed[a].box
        if not all(bg.point_in_outline(c, outline) for c in ((A[0], A[1]), (A[2], A[1]), (A[2], A[3]), (A[0], A[3]))):
            out.append(f'{a}: courtyard {[round(v, 2) for v in A]} leaves the outline')
        for c in cuts:
            if box_overlap(A, c):
                out.append(f'{a}: courtyard in the vent cut-out')
        for hx, hy in holes:
            dx, dy = max(A[0] - hx, 0, hx - A[2]), max(A[1] - hy, 0, hy - A[3])
            if math.hypot(dx, dy) < kr - 1e-9:
                out.append(f'{a}: courtyard in the keepout of hole ({hx}, {hy})')
        for b in refs[i + 1:]:
            if box_overlap(A, placed[b].box):
                out.append(f'{a} / {b}: courtyards overlap')
    pads = [(ref, p) for ref, pa in placed.items() for p in pa.pads if p['number']]
    for z in zones:
      for zb in zone_rects(z):
        for c in cuts:
            if box_overlap(zb, c, CLEAR):
                out.append(f'{z["id"]}: in the vent cut-out')
        for q in ((zb[0], zb[1]), (zb[2], zb[1]), (zb[2], zb[3]), (zb[0], zb[3])):
            if mb.edge_dist(q, outline) < EDGE + MARGIN or not bg.point_in_outline(q, outline):
                out.append(f'{z["id"]}: closer than the edge clearance at {q}')
        for hx, hy in holes:
            dx, dy = max(zb[0] - hx, 0, hx - zb[2]), max(zb[1] - hy, 0, hy - zb[3])
            if math.hypot(dx, dy) < kr:
                out.append(f'{z["id"]}: in the keepout of hole ({hx}, {hy})')
        for ref, p in pads:
            if p['net'] == z['net'] or z['layer'][0] not in p['layers']:
                continue
            if mb.box_dist(zb, p['box']) < CLEAR + MARGIN - 1e-6:
                out.append(f'{z["id"]} ({z["net"]}): {round(mb.box_dist(zb, p["box"]), 3)} mm to {ref}.{p["number"]} ({p["net"]})')
        for o in zones:
            if o is z or o['net'] == z['net'] or o['layer'] != z['layer']:
                continue
            for ob in zone_rects(o):
                if mb.box_dist(zb, ob) < CLEAR + MARGIN - 1e-6 and z['id'] < o['id']:
                    out.append(f'{z["id"]} / {o["id"]}: different-net pours {round(mb.box_dist(zb, ob), 3)} mm apart')
    for t in tracks:
        r = t['width_mm'] / 2
        for (x1, y1), (x2, y2) in zip(t['path'], t['path'][1:]):
            for ref, p in pads:
                if p['net'] == t['net'] or t['layer'][0] not in p['layers']:
                    continue
                d = mb.seg_box_dist((x1, y1), (x2, y2), p['box'])
                if d - r < CLEAR + MARGIN - 1e-6:
                    out.append(f'{t["id"]}: {round(d - r, 3)} mm to {ref}.{p["number"]} ({p["net"]})')
            for z in zones:
                if z['net'] == t['net'] or z['layer'] != t['layer']:
                    continue
                d = min(mb.seg_box_dist((x1, y1), (x2, y2), zb) for zb in zone_rects(z))
                if d - r < CLEAR + MARGIN - 1e-6:
                    out.append(f'{t["id"]}: {round(d - r, 3)} mm to pour {z["id"]} ({z["net"]})')
            for q in ((x1, y1), (x2, y2)):
                if mb.edge_dist(q, outline) - r < EDGE + MARGIN:
                    out.append(f'{t["id"]}: closer than the edge clearance at {q}')
    for v in vias:
        for ref, p in pads:
            if p['net'] == v['net']:
                continue
            if mb.box_dist((v['at'][0], v['at'][1], v['at'][0], v['at'][1]), p['box']) - v['diameter_mm'] / 2 < CLEAR + MARGIN - 1e-6:
                out.append(f'{v["id"]}: too close to {ref}.{p["number"]}')
        for z in zones:
            if z['net'] == v['net']:
                continue
            if min(mb.box_dist((v['at'][0], v['at'][1], v['at'][0], v['at'][1]), zb) for zb in zone_rects(z)) - v['diameter_mm'] / 2 \
                    < CLEAR + MARGIN - 1e-6:
                out.append(f'{v["id"]}: too close to pour {z["id"]}')
    return out


def mirror_check(inp):
    """The mechanical contract (enclosure frame) of PWR_C, when the sr-rx-mech patch carries it, must be this proposal mirrored
    about the board's vertical centre line: x_enclosure_board = W - x_component_side (the board faces -z)."""
    if not MECH_CONTRACT.is_file():
        return 'mechanical/generated/contract/boards.json missing'
    mc = read(MECH_CONTRACT)['boards'].get(BOARD)
    if mc is None:
        return 'no PWR_C entry in mechanical/generated/contract/boards.json yet (sr-rx-mech patch pending)'
    W = max(p[0] for p in inp.contract['outline_mm'])
    mir = lambda pts: sorted((r4(W - x), r4(y)) for x, y in pts)
    bad = []
    if mir(inp.contract['outline_mm']) != sorted((r4(x), r4(y)) for x, y in mc['outline_mm']):
        bad.append('outline')
    if mir(inp.contract['holes_mm']) != sorted((r4(x), r4(y)) for x, y in mc['holes_mm']):
        bad.append('holes')
    cm = sorted((r4(W - x - w), r4(y), r4(w), r4(h)) for x, y, w, h in inp.contract.get('cutouts_mm', []))
    if cm != sorted((r4(x), r4(y), r4(w), r4(h)) for x, y, w, h in mc.get('cutouts_mm', [])):
        bad.append('cutouts')
    if mc.get('max_component_height') != inp.contract['max_component_height']:
        bad.append('max_component_height')
    if bad:
        raise SystemExit(f'make_spec: contract-proposal.json and the mechanical PWR_C contract differ ({", ".join(bad)}) beyond the mirror')
    return 'agrees (mirrored) with mechanical/generated/contract/boards.json PWR_C'


def project_json(inp, nets):
    proj = read(ENC_PROJECT)
    proj['meta']['filename'] = 'PWR_C.kicad_pro'
    nc = inp.netclasses
    default = proj['net_settings']['classes'][0]
    pd = nc['project_defaults']['values_mm']
    classes = []
    for name, width, clearance in (('Default', nc['classes']['SIG']['outer_min_width_mm'], nc['classes']['SIG']['clearance_mm']),
                                   ('PWR1A', nc['classes']['PWR1A']['outer_min_width_mm'], nc['classes']['PWR1A']['clearance_mm']),
                                   ('PWRC_BRANCH', 0.5, nc['classes']['BATT']['clearance_mm']),
                                   ('PWRC_SENSE', 0.2, nc['classes']['BATT']['clearance_mm']),
                                   ('SCRIPTED_GND', nc['classes']['SIG']['outer_min_width_mm'], nc['classes']['SIG']['clearance_mm'])):
        row = copy.deepcopy(default)
        row['name'] = name
        row['track_width'] = width
        row['clearance'] = clearance
        row['via_diameter'] = mb.VIA_D
        row['via_drill'] = pd['via_hole']
        if name != 'Default':
            row['priority'] = len(classes) - 1
        classes.append(row)
    proj['net_settings']['classes'] = classes
    pats = []
    for n in sorted(nets):
        cls = (nc['nets'].get(n) or {}).get('class', 'SIG')
        if n == 'GND':
            pats.append({'netclass': 'SCRIPTED_GND', 'pattern': n})
        elif n in SENSE_NETS:
            pats.append({'netclass': 'PWRC_SENSE', 'pattern': n})
        elif cls in ('BATT', 'PWR3A', 'PWR2A'):
            pats.append({'netclass': 'PWRC_BRANCH', 'pattern': n})
        elif cls == 'PWR1A':
            pats.append({'netclass': 'PWR1A', 'pattern': n})
    proj['net_settings']['netclass_patterns'] = pats
    rules = proj['board']['design_settings']['rules']
    rules['min_track_width'] = pd['track_width']
    rules['min_clearance'] = pd['clearance']
    rules['min_copper_edge_clearance'] = pd['edge_clearance']
    rules['min_hole_to_hole'] = pd['hole_to_hole']
    return json.dumps(proj, indent=2) + '\n'


# Power-net pads joined by the scripted copper (no exemption); the router reaches the others, which branch_exempt lists.
NO_EXEMPT = ('J105', 'R101', 'U106', 'J118', 'J119', 'F103', 'J108', 'J114', 'J115', 'D104', 'D105')


def branch_exempt(inp, placed):
    """Refs whose pads on a power-class net take router branches narrower than the class: sense pins, the AON LDO input,
    dividers, test points and decoupling capacitors. Never one of NO_EXEMPT (the acceptance of F2C-FALLBACK)."""
    nc = inp.netclasses
    power = {n for n, c in nc['nets'].items() if c.get('class') in ('BATT', 'PWR3A', 'PWR2A')}
    scripted = {'U109': {'5', '6'}, 'C116': {'1'}, 'C117': {'1'}, 'U553': {'1'}, 'C552': {'1'}}
    out = {}
    for ref, pa in sorted(placed.items(), key=lambda kv: bg.sort_ref(kv[0])):
        pads_ = sorted({p['number'] for p in pa.pads if p['net'] in power} - scripted.get(ref, set()), key=bg.sort_ref)
        if not pads_ or ref in NO_EXEMPT:
            continue
        nets = sorted({p['net'] for p in pa.pads if p['number'] in pads_})
        sense = set(nets) <= SENSE_NETS
        out[ref] = {'max_mm': 25.0, 'min_width_mm': 0.2 if sense else 0.5, 'pads': pads_,
                    'reason': f'{TAG}: router branch of {", ".join(nets)} to a low-current pad ({inp.graph[ref]["value"][:40]}); '
                              'the current path is the scripted class-width copper (make_spec.py power_copper)'}
    return out


def build():
    inp = Inputs()
    parts = spec_parts(inp)
    anchors, _rows = plan(inp, parts)
    placed = placed_all(inp, parts, anchors)
    zones, tracks, vias = power_copper(placed)
    probs = problems(inp, placed, zones, tracks, vias)
    for z in zones:
        z.pop('_rects', None)
    pre = {'tracks': list(tracks), 'vias': list(vias), 'zones': zones + [
        {'id': 'GND-In1', 'net': 'GND', 'layer': 'In1.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
         'why': 'GND plane (layer type power: a plane in the DSN); joined by the scripted via of every SMD GND pad'},
        {'id': 'GND-In2', 'net': 'GND', 'layer': 'In2.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
         'why': 'second GND plane, as PWR_A'}]}
    fan_inp = SimpleNamespace(contract=inp.contract, parts=placed, outline=inp.outline)
    gt, gv, skipped = mb.gnd_fanout(fan_inp, pre)
    pre['tracks'] = tracks + gt
    pre['vias'] = vias + gv
    nets = set()
    for ns in inp.nets_of.values():
        nets |= {n for n in ns.values() if n}
    mirror = mirror_check(inp)
    pwra = read(PWRA_SPEC)
    spec = {
        'schema': bg.SPEC_SCHEMA, 'board_id': BOARD,
        'status': 'CI_MODEL_NOT_FOR_FABRICATION',
        'title': 'PWR-C front-slab power-entry board (F2-C): E1 battery front end, INA228 shunt, Pololu #2813, E5 IMU service',
        'note': (f'{TAG}: generated by build/kicad/boards/PWR_C/make_spec.py; outline, holes and the vent cut-out come from '
                 'build/kicad/boards/PWR_C/contract-proposal.json (component-side frame; the mechanical contract carries the '
                 f'same board in the enclosure frame, mirror check: {mirror}). Every part is a graph ref. CI/MODEL output only; '
                 'every bench gate stays OPEN.'),
        'contract': {'file': 'build/kicad/boards/PWR_C/contract-proposal.json', 'board': BOARD},
        'domains': ['PWR_ENTRY'], 'partition': 'pcb/generated/partition.json',
        'layers': {'copper': 4, 'thickness_mm': 1.6,
                   'source': "JLC04161H-7628, 1 oz outer / 0.5 oz inner (build/15 'Шари', as the other 4-layer boards)",
                   'plan': {'F.Cu': 'parts, signals and the scripted power pours', 'In1.Cu': 'GND plane',
                            'In2.Cu': 'GND plane', 'B.Cu': 'signals'},
                   'types': {'In1.Cu': 'power', 'In2.Cu': 'power'},
                   'types_why': 'plane layers in the DSN, as PWR_A and PWR_B: Freerouting puts only vias through them'},
        'project': 'build/kicad/boards/PWR_C/PWR_C.kicad_pro',
        'rules_file': None,
        'rules_note': 'the rules live in the committed project file: project defaults of pcb/generated/netclasses.json, classes '
                      'Default (SIG), PWR1A, PWRC_BRANCH 0.5 mm, PWRC_SENSE 0.2 mm and SCRIPTED_GND',
        'fab_floor': pwra['fab_floor'],
        'instances': {'template_nets': sorted(nets),
                      'list': [{'id': 'PWRC', 'placement': 'default', 'qty': 1, 'refs': {r: r for r in inp.refs},
                                'nets': {n: n for n in sorted(nets)},
                                'source': 'identity map: the PWR_ENTRY refs of pcb/generated/partition.json'}],
                      'spares': 0, 'spares_source': 'one board per device'},
        'parts': parts,
        'holes': {'from_contract': True, 'ref_prefix': 'H', 'keepout_layers': ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'],
                  'keepout_blocks': ['tracks', 'vias', 'zone_fills']},
        'groups': groups_json(),
        'pre_route': pre,
        'post_route_zones': [],
        'edge_keepout': {'width_mm': 0.2, 'layers': ['F.Cu', 'B.Cu'], 'blocks': ['tracks', 'vias'],
                         'why': 'rule-area strips (half-width 0.2) on every outline and cut-out edge, as PWR_A and PWR_B'},
        'router': {'tool': 'freerouting', 'max_passes': 60, 'threads': 1, 'job_timeout': '00:20:00', 'timeout_s': 1320,
                   'fanout': False, 'ignore_net_classes': ['SCRIPTED_GND'],
                   'why': 'no fan-out pre-pass; GND joins the planes through the scripted vias (SCRIPTED_GND not autorouted); '
                          'the power paths are scripted pours, the router joins sense and low-current branches only'},
        'drc_policy': pwra['drc_policy'],
        'branch_exempt': branch_exempt(inp, placed),
        'gnd_fanout': {'vias': len(gv), 'stubs': len(gt), 'pads_joined_by_scripted_gnd_pours': skipped,
                       'rule': 'build/kicad/boards/PWR_A/make_board.py gnd_fanout: stub 0.25 mm to a 0.7 / 0.3 via'},
        'power_copper_rule': {'no_exemption_refs': list(NO_EXEMPT),
                              'rule': ('W2 F2C-FALLBACK acceptance: no branch_exempt or neck_exempt on these refs; their power '
                                       'pads are joined by scripted pours at the class width of the net (BATT 3.2 mm, PWR3A '
                                       '1.85 mm, 1 oz outer); the U109 IN/OUT bars are poured along their length; the TVS '
                                       'cathodes sit on class-width pours and their anodes on GND pours with two plane vias'),
                              'lab5_min_mm': 1.335, 'lab5_mm': LAB5_W},
        'generator': 'build/kicad/boards/PWR_C/make_spec.py',
    }
    bg.validate_spec(spec, BOARD)
    return spec, project_json(inp, nets), probs, placed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--draft', action='store_true')
    args = ap.parse_args(argv)
    spec, proj, probs, placed = build()
    for p in probs:
        print('PROBLEM', p)
    text = json.dumps(spec, ensure_ascii=False, indent=2) + '\n'
    print(f'{len(probs)} problem(s); {len(spec["parts"])} parts; {len(spec["pre_route"]["tracks"])} tracks; '
          f'{len(spec["pre_route"]["vias"])} vias; {len(spec["pre_route"]["zones"])} zones')
    if args.draft:
        return 0
    if args.check:
        ok = SPEC.is_file() and SPEC.read_text(encoding='utf-8') == text and PROJECT.is_file() and \
            PROJECT.read_text(encoding='utf-8') == proj
        print('PWR_C spec and project', 'reproduce' if ok else 'are stale: rerun build/kicad/boards/PWR_C/make_spec.py')
        return 0 if ok else 1
    if probs:
        print('make_spec: not written while problems remain')
        return 1
    SPEC.write_text(text, encoding='utf-8', newline='\n')
    PROJECT.write_text(proj, encoding='utf-8', newline='\n')
    print('wrote pcb/boards/PWR_C.json and build/kicad/boards/PWR_C/PWR_C.kicad_pro')
    return 0


if __name__ == '__main__':
    sys.exit(main())
