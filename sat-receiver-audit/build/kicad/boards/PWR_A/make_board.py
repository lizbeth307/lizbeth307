#!/usr/bin/env python3
"""PWR-A board spec for routing (W2 PCB-PWRA-4), standard library.

  python3 build/kicad/boards/PWR_A/make_board.py            write board-spec.json and PWR_A.kicad_pro next to this file
  python3 build/kicad/boards/PWR_A/make_board.py --install  also copy board-spec.json to pcb/boards/PWR_A.json (a route
                                                            commit '[pcb-route PWR_A]', or the board of record)
  python3 build/kicad/boards/PWR_A/make_board.py --check    fail unless they reproduce (pcb/boards/PWR_A.json if present)
  python3 build/kicad/boards/PWR_A/make_board.py --svg F    also write a preview SVG (courtyards, pads, scripted copper)

The board spec of the SHRINK-2 PWR-A that sr-rx-pcb places and routes ('[pcb-route PWR_A]'). It starts from the
placement probe of W2 PCB-PWRA-3 (make_probe_spec.build_placement: every ref of PWR_A.spec-shrink2.json at its
placement-study-shrink2.json origin, side and rotation, with all the scripted copper) and adds, in one place:

  * MOVES: placement changes of this package (design choices, each with its reason). A part that needs a PWR-B
    cut-out (placement-study-shrink2.json pwr_b_cutouts: window over a part taller than hA, header edge strip, probe
    window) never moves here, because PCB-PWRB-2 placed PWR-B around exactly that cut-out list (fixed point of the two
    specs); make_board stops on such a move.
  * GND fan-out (port of build/kicad/boards/PWR_B/make_spec.py gnd_fanout, W2 PCB-PWRB): a locked via next to every SMD
    GND pad of both sides that no scripted GND pour already joins, so that the GND planes In1/In2 join every GND pad and
    the router never routes GND (net class SCRIPTED_GND, not autorouted: router -inc). On PWR_B, Freerouting left 83
    GND connections open without it (route run 42415437982); PWR-A placement probe 7 left 140 (run 43148929963).
  * the project rules of this board (PWR_A.kicad_pro): the classes of pcb/generated/netclasses.json, via 0.7 / 0.3 for
    the router (0.6 vias at clearance 0.15 break the 0.5 mm hole-to-hole rule, PWR_B), class SCRIPTED_GND;
  * the checker keys of pcb/check_boards.py: sides top and bottom, heights from pcb/partition-spec.json heights (read
    or class values), height zones (board hA, PWR-B windows at the window ceiling, rule H-TRIM under every PWR-B THT
    pin field of pcb/boards/PWR_B.json h_trim), the THT plate pockets of the probe, the B2B pair J208/J209;
  * the router budget of a board of record;
  * W2 PWRJ-LAYERS6: the 6-layer plan S-G-S-S-P-S of JLC06161H-2116 (as PWR_B and the 6-layer CTRL) with finished outer
    copper 2 oz and inner 0.5 oz (pcb/generated/stackup-6l.json copper_options outer_2oz): In1.Cu the solid GND plane,
    In2.Cu/In3.Cu signal routing, In4.Cu the GND fill with the scripted E1_CONV_IN strap/bridge pours (the In2.Cu role of
    the 4-layer plan), the power classes on F.Cu/B.Cu only at their 2 oz widths (router.class_layers).
Every value is a CI/MODEL input: no fabrication release, bench gates stay OPEN.
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3]  # sat-receiver-audit
sys.path.insert(0, str(BASE / 'pcb'))
sys.path.insert(0, str(HERE))
import board_gen as bg  # noqa: E402
import make_probe_spec as mps  # noqa: E402

BOARD = 'PWR_A'
SPEC = BASE / 'pcb/boards/PWR_A.json'   # installed only for a route run or a board of record (sr-rx-pcb routes and checks it)
SPEC_OUT = HERE / 'board-spec.json'     # the generated board spec, always written and checked
PROJECT = HERE / 'PWR_A.kicad_pro'
ENC_PROJECT = BASE / 'build/kicad/boards/ENC/ENC.kicad_pro'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
PSPEC = BASE / 'pcb/partition-spec.json'
PWR_B_SPEC = BASE / 'pcb/boards/PWR_B.json'
STUDY = HERE / 'placement-study-shrink2.json'
CONTRACT = BASE / 'mechanical/generated/contract/boards.json'
STACKUP_6L = BASE / 'pcb/generated/stackup-6l.json'

# W2 PWRJ-LAYERS6: 6 layers, 2 oz outer / 0.5 oz inner (pcb/generated/stackup-6l.json copper_options; jlcpcb.com read 2026-11-13)
COPPER_OPTION = 'outer_2oz'
COPPER6 = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
ROUTING6 = ['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu']
INNER_MAP = {'In2.Cu': 'In4.Cu'}   # the 4-layer L3 (GND fill + E1_CONV_IN strap/bridge) becomes L5 of the 6-layer plan
CLASS_LAYERS = {c: ['F.Cu', 'B.Cu'] for c in ('BATT', 'PWR1A', 'PWR2A', 'PWR3A')}

CLEAR = 0.15          # project clearance (netclasses.json project_defaults)
MARGIN = 0.05         # design margin of the scripted copper over the clearance
EDGE = 0.3            # project copper-to-edge clearance
VIA_D, VIA_DRILL = 0.7, 0.3   # as PWR_B: router vias at clearance 0.15 keep the 0.5 mm hole-to-hole rule
HOLE_GAP = 0.55       # drill edge to drill edge, the 0.5 mm hole-to-hole rule plus margin
W_GND = 0.25          # GND fan-out stub width (as PWR_B)
EPS = 1e-6            # mm, rounding tolerance of the clearance tests (a stub as wide as its pad keeps the pad's own gap)
JOINT_OVERLAP = 0.05  # mm, two scripted tracks of one net count as joined when they overlap at least this much

# Placement changes of W2 PCB-PWRA-4 (design choices; ref -> (x, y, rotation, side, reason)), applied after the
# positions of board-placement.json (place_board.py, net-aware re-placement; route iteration 2). Route iteration 1 used
# neither: the board was placed exactly as placement-study-shrink2.json.
MOVES: dict = {
    # W2 PWR-L6-SCRIPT (design choice): CIN_HF2 0.375 mm up, pad 1 still at the VIN2 level and pad 2 at the PGND2 level, so that
    # the SW link to the CBOOT capacitor passes under it from the gap between VIN2 and RBOOT (TI SNVSBD5D 11.1 / figure 11-2:
    # "route the SW connection under the device through the gap between VIN2 and RBOOT pins"); a 0603, no H-TRIM field
    'C122': (13.07, 47.9, 90, 'F', 'W2 PWR-L6-SCRIPT: C122 (CIN_HF2) 0.375 mm up for the SW-CBOOT link under it (SNVSBD5D 11.1)'),
}
PLACEMENT = HERE / 'board-placement.json'


def r4(v):
    return bg.r4(v)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


# ------------------------------------------------------------------ geometry (port of PWR_B make_spec.py, W2 PCB-PWRB)
class Placed:
    """A footprint at an anchor: courtyard and pad boxes in board mm (y up), pad nets (as pcb/board_gen.place())."""

    def __init__(self, ref, geo, anchor, nets):
        self.ref, self.anchor, self.side = ref, anchor, anchor.get('side', 'F')
        rot = float(anchor.get('rotation', 0))
        flip = self.side == 'B'

        def local(pt):
            x, y = bg.turn_point(pt, rot)
            return (-x if flip else x), y
        align = anchor.get('align', 'origin')
        ax, ay = 0.0, 0.0
        if align != 'origin':
            want = str(align['pad'] if 'pad' in align else align['pad_centroid'])
            pts = [local(p['at']) for p in geo['pads'] if str(p['number']) == want]
            ax, ay = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        bx, by = (float(v) for v in anchor['at'])
        self.map = lambda pt: (bx + local(pt)[0] - ax, by - (local(pt)[1] - ay))
        x0, y0, x1, y1 = geo['courtyard']
        pts = [self.map(c) for c in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        self.box = [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]
        self.pads = []
        for p in geo['pads']:
            cx, cy = self.map(p['at'])
            fx0, fy0, fx1, fy1 = p['fbox']
            corners = [self.map(c) for c in ((fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1))]
            self.pads.append({'number': str(p['number']), 'type': p['type'], 'at': (cx, cy),
                              'box': (min(c[0] for c in corners), min(c[1] for c in corners),
                                      max(c[0] for c in corners), max(c[1] for c in corners)),
                              'drill': p['drill'],
                              'net': nets.get(str(p['number'])) if p['number'] else None,
                              'layers': ('F', 'B') if p['type'] in ('thru_hole', 'np_thru_hole') else (self.side,)})


def box_dist(a, b):
    dx = max(a[0] - b[2], 0.0, b[0] - a[2])
    dy = max(a[1] - b[3], 0.0, b[1] - a[3])
    return math.hypot(dx, dy)


def point_seg(p, a, b):
    (ax, ay), (bx, by), (px, py) = a, b, p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def seg_seg_dist(a, b, c, d):
    best = min(point_seg(a, c, d), point_seg(b, c, d), point_seg(c, a, b), point_seg(d, a, b))

    def ccw(u, v, w):
        return (w[1] - u[1]) * (v[0] - u[0]) > (v[1] - u[1]) * (w[0] - u[0])
    if ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d):
        return 0.0
    return best


def seg_box_dist(p, q, box):
    """Distance from segment pq to an axis-aligned box (0 when they touch)."""
    x0, y0, x1, y1 = box
    if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 or x0 <= q[0] <= x1 and y0 <= q[1] <= y1:
        return 0.0
    edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    return min(seg_seg_dist(p, q, a, b) for a, b in edges)


def edge_dist(pt, outline):
    return min(point_seg(pt, a, b) for a, b in zip(outline, outline[1:] + outline[:1]))


def poly_box(outline):
    return (min(p[0] for p in outline), min(p[1] for p in outline), max(p[0] for p in outline), max(p[1] for p in outline))


# ------------------------------------------------------------------ inputs
def with_copper_option(nc):
    """netclasses.json with the power-class widths of COPPER_OPTION (pcb/generated/stackup-6l.json, W2 PWRJ-LAYERS6), as
    pcb/check_boards.py board_netclasses applies them to this board."""
    opt = read(STACKUP_6L)['copper_options'][COPPER_OPTION]
    out = {**nc, 'classes': {k: dict(v) for k, v in nc['classes'].items()}}
    for name, w in opt['power_classes'].items():
        out['classes'][name].update({k: w[k] for k in ('outer_min_width_mm', 'outer_ipc_width_mm', 'split_outer_per_layer_mm',
                                                       'inner_min_width_mm')})
    return out


def six_layer_zones(pre):
    """The scripted inner zones of the 4-layer SHRINK-2 spec on the 6-layer plan (INNER_MAP): In2.Cu (GND fill and the
    E1_CONV_IN strap/bridge pours) moves to In4.Cu; In1.Cu stays the solid GND plane."""
    for z in pre['zones']:
        if z['layer'] in INNER_MAP:
            z['layer'] = INNER_MAP[z['layer']]
            z['why'] = (z.get('why', '') + '; W2 PWRJ-LAYERS6: on In4.Cu (L5, the GND fill / power layer of the 6-layer plan; the '
                        '4-layer L3 role), so In2.Cu/In3.Cu route signals').lstrip('; ')
    for t in pre['tracks']:
        if t['layer'] in INNER_MAP:
            raise SystemExit(f'make_board: scripted track {t["id"]} on {t["layer"]}: no inner scripted tracks on the 6-layer plan')


class Inputs:
    def __init__(self, base_spec):
        self.spec = base_spec
        self.graph = bg.load_graph()
        self.manifest = bg.read_json(bg.MANIFEST)
        self.netclasses = with_copper_option(read(NETCLASSES))
        self.pspec = read(PSPEC)
        self.contract = read(CONTRACT)['boards'][base_spec['contract']['board']]
        self.study = read(STUDY)
        self.pwr_b = read(PWR_B_SPEC)
        self.outline = [tuple(p) for p in self.contract['outline_mm']]
        self.template = bg.resolve({**base_spec, 'groups': []}, self.graph, self.manifest)
        self.geo = {}
        for t in self.template:
            text = bg.footprint_file(t).read_text(encoding='utf-8')
            geo = bg.footprint_geometry(text)
            # copper pads only (paste apertures without a number are no copper; NPTH holes stay as holes); a pad with its
            # own rotation in the footprint gets its size turned (footprint_geometry keeps only x, y of the pad 'at')
            keep = []
            for p, (cu, fbox) in zip(geo['pads'], pad_copper(text)):
                if cu or p['type'] == 'np_thru_hole':
                    keep.append({**p, 'fbox': fbox})
            self.geo[t['ref']] = {**geo, 'pads': keep}
        self.parts = {t['ref']: Placed(t['ref'], self.geo[t['ref']], t['anchor'], t['pads']) for t in self.template}


def pad_copper(text):
    """For each pad of a .kicad_mod (footprint_geometry order): (True if it has a copper layer, the box of its copper
    in footprint coordinates). The box covers the pad size, the primitives of a custom pad (polygons, rectangles,
    circles, lines with their width) and the pad's own rotation (footprint_geometry keeps only the pad position)."""
    out = []
    for node in bg.sexpr(text)[1:]:
        if not (isinstance(node, list) and node and node[0] == 'pad'):
            continue
        layers = next((n[1:] for n in node if isinstance(n, list) and n and n[0] == 'layers'), [])
        at = next(n for n in node if isinstance(n, list) and n and n[0] == 'at')
        size = next(n for n in node if isinstance(n, list) and n and n[0] == 'size')
        px, py = float(at[1]), float(at[2])
        angle = float(at[3]) if len(at) > 3 else 0.0
        w, h = float(size[1]), float(size[2])
        pts = [(-w / 2, -h / 2), (w / 2, h / 2)]
        prims = next((n for n in node if isinstance(n, list) and n and n[0] == 'primitives'), None)
        for g in (prims[1:] if prims else []):
            if not isinstance(g, list):
                continue
            width = next((float(n[1]) for n in g if isinstance(n, list) and n and n[0] == 'width'), 0.0) / 2
            gp = []

            def walk(n):
                if isinstance(n, list) and n and n[0] in ('xy', 'start', 'end', 'center', 'mid'):
                    gp.append((float(n[1]), float(n[2])))
                elif isinstance(n, list):
                    for m in n:
                        walk(m)
            walk(g)
            if g[0] == 'gr_circle' and len(gp) >= 2:
                r = math.dist(gp[0], gp[1])
                gp = [(gp[0][0] - r, gp[0][1] - r), (gp[0][0] + r, gp[0][1] + r)]
            pts += [(x - width, y - width) for x, y in gp] + [(x + width, y + width) for x, y in gp]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        corners = [(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]
        rad = math.radians(angle)
        # KiCad RotatePoint (y down): (x, y) -> (x cos + y sin, -x sin + y cos)
        turned = [(x * math.cos(rad) + y * math.sin(rad) + px, -x * math.sin(rad) + y * math.cos(rad) + py) for x, y in corners]
        box = (min(c[0] for c in turned), min(c[1] for c in turned), max(c[0] for c in turned), max(c[1] for c in turned))
        out.append((any(str(x).endswith('.Cu') for x in layers), box))
    return out


# ------------------------------------------------------------------ placement
def cutout_refs(study):
    return {c['ref'] for c in study['pwr_b_cutouts']['placed']}


def all_moves(study):
    """board-placement.json positions (place_board.py), then MOVES; the placement file must belong to the current
    SHRINK-2 spec and study."""
    moves = {}
    if PLACEMENT.is_file():
        doc = read(PLACEMENT)
        spec_sha = bg.sha256_bytes(bg.canonical(read(HERE / 'PWR_A.spec-shrink2.json')))
        if doc['inputs']['spec_sha256'] != spec_sha or doc['inputs']['study_sha256'] != bg.sha256_bytes(bg.canonical(study)):
            raise SystemExit('make_board: board-placement.json is stale (spec or study changed): rerun place_board.py')
        for ref, row in doc['positions'].items():
            moves[ref] = (row['at'][0], row['at'][1], row['rotation'], row['side'],
                          'board-placement.json (place_board.py net-aware re-placement)')
    moves.update(MOVES)
    return moves


def apply_moves(spec, study):
    """The moves onto the probe anchors; a part with a PWR-B cut-out never moves (fixed point with PCB-PWRB-2)."""
    fixed = cutout_refs(study)
    outline = [tuple(p) for p in read(CONTRACT)['boards'][spec['contract']['board']]['outline_mm']]
    by_ref = {p['ref']: p for p in spec['parts']}
    moves = all_moves(study)
    for ref, (x, y, rot, side, why) in sorted(moves.items(), key=lambda kv: bg.sort_ref(kv[0])):
        if ref in fixed:
            raise SystemExit(f'make_board: {ref} has a PWR-B cut-out (placement-study-shrink2.json pwr_b_cutouts) and '
                             'cannot move without a PCB-PWRB re-placement')
        p = by_ref[ref]
        p['anchor'] = {'at': [r4(x), r4(y)], 'align': 'origin', 'rotation': float(rot), 'side': side}
        p['anchor_source'] = f'W2 PCB-PWRA-4: {why}'
    # legends of moved parts near the edge (make_probe_spec.edge_text rule)
    graph, manifest = bg.load_graph(), bg.read_json(bg.MANIFEST)
    template = {t['ref']: t for t in bg.resolve({**spec, 'groups': []}, graph, manifest)}
    for ref in [p['ref'] for p in spec['parts'] if p['ref'] in moves or not p.get('anchor', {}).get('ref_text')]:
        t = template[ref]
        pg = bg.placed_geometry(bg.footprint_geometry(bg.footprint_file(t).read_text(encoding='utf-8')), t['anchor'])
        text = mps.edge_text(pg['box'], outline)
        if text:
            by_ref[ref]['anchor']['ref_text'] = text


def check_placement(inp):
    """Courtyard overlaps per side, outline and hole keep-outs (MODEL, courtyard boxes)."""
    problems = []
    c = inp.contract
    holes = [(tuple(h), c['hole_keepout_d'] / 2) for h in c['holes_mm']]
    items = sorted(inp.parts.values(), key=lambda p: bg.sort_ref(p.ref))
    for i, a in enumerate(items):
        if not all(bg.point_in_outline(pt, inp.outline) for pt in ((a.box[0], a.box[1]), (a.box[2], a.box[3]),
                                                                    (a.box[0], a.box[3]), (a.box[2], a.box[1]))):
            problems.append(f'{a.ref} courtyard leaves the outline')
        for (hx, hy), hr in holes:
            if box_dist(a.box, (hx, hy, hx, hy)) < hr - 1e-6:
                problems.append(f'{a.ref} courtyard in the hole keep-out at ({hx}, {hy})')
        for b in items[i + 1:]:
            if a.side == b.side and bg.rects_overlap(a.box, b.box, -1e-6):
                problems.append(f'courtyards {a.ref} and {b.ref} overlap ({a.side})')
    return problems


# ------------------------------------------------------------------ scripted pours of the SHRINK-2 spec on the board
def capsule_hits_box(a, b, r, box):
    return seg_box_dist(a, b, box) < r - EPS


def rect_union_outline(rects):
    """Outline of the union of axis-aligned rectangles that form one simply connected rectilinear region (coordinate
    compression and boundary walk, counter-clockwise); None if the union has a hole or is not one piece."""
    xs = sorted({v for r in rects for v in (r[0], r[2])})
    ys = sorted({v for r in rects for v in (r[1], r[3])})
    nx, ny = len(xs) - 1, len(ys) - 1
    cov = [[any(r[0] <= xs[i] and xs[i + 1] <= r[2] and r[1] <= ys[j] and ys[j + 1] <= r[3] for r in rects)
            for j in range(ny)] for i in range(nx)]

    def c(i, j):
        return 0 <= i < nx and 0 <= j < ny and cov[i][j]
    edges = {}
    for i in range(nx):
        for j in range(ny):
            if not cov[i][j]:
                continue
            if not c(i, j - 1):
                edges[(i, j)] = (i + 1, j)
            if not c(i + 1, j):
                edges[(i + 1, j)] = (i + 1, j + 1)
            if not c(i, j + 1):
                edges[(i + 1, j + 1)] = (i, j + 1)
            if not c(i - 1, j):
                edges[(i, j + 1)] = (i, j)
    if not edges:
        return None
    start = min(edges)
    loop, cur = [start], edges[start]
    while cur != start:
        if cur not in edges or len(loop) > len(edges):
            return None
        loop.append(cur)
        cur = edges[cur]
    if len(loop) != len(edges):
        return None
    pts = [(xs[i], ys[j]) for i, j in loop]
    n = len(pts)
    out = [q for k, q in enumerate(pts)
           if (pts[k - 1][0] - q[0]) * (pts[(k + 1) % n][1] - q[1]) != (pts[k - 1][1] - q[1]) * (pts[(k + 1) % n][0] - q[0])]
    return [[r4(x), r4(y)] for x, y in out]


def board_copper(pre, inp=None):
    """The scripted copper of the SHRINK-2 spec as the board carries it (W2 PCB-PWRA-4 after route iteration 1, sr-rx-pcb
    run 43287918183): every F.Cu/B.Cu pour becomes one locked track along its long axis, as wide as its short side,
    because Freerouting routed other nets across the pours (planes in the DSN) and the KiCad refill then cut the LAB5
    trunk into isolated islands (29 isolated_copper, 6 dangling LAB5 vias); overlapping same-net pours of one priority
    on In2.Cu become one zone (31 zones_intersect in that run). With inp, a pad of the pour's net that the pour touched
    and the track's round ends miss gets a stub from the track axis to its centre, as wide as the pour or the pad.
    Returns (pre_route, notes)."""
    tracks, zones, notes = list(pre['tracks']), [], []
    inner = {}
    converted = []  # (pour id, net, layer, rect, track)
    pads = [q for pa in inp.parts.values() for q in pa.pads] if inp else []
    for z in pre['zones']:
        if z['outline'] == 'board':
            zones.append(z)
            continue
        if z['layer'] not in ('F.Cu', 'B.Cu'):
            inner.setdefault((z['net'], z['layer'], z.get('priority'), z.get('pad_connection')), []).append(z)
            continue
        x0, y0, x1, y1 = poly_box(z['outline'])
        w, h = x1 - x0, y1 - y0
        if w >= h:
            a, b, width = (x0 + h / 2, (y0 + y1) / 2), (x1 - h / 2, (y0 + y1) / 2), h
        else:
            a, b, width = ((x0 + x1) / 2, y0 + w / 2), ((x0 + x1) / 2, y1 - w / 2), w
        if math.dist(a, b) < 0.002:
            b = (a[0] + 0.002, a[1]) if w >= h else (a[0], a[1] + 0.002)
        path = [[r4(a[0]), r4(a[1])], [r4(b[0]), r4(b[1])]]
        tracks.append({'id': f'CU-{z["id"]}', 'net': z['net'], 'layer': z['layer'], 'width_mm': r4(width), 'path': path,
                       'locked': True, 'why': f'scripted pour {z["id"]} of PWR_A.spec-shrink2.json as a locked track '
                                              '(make_board.py board_copper)'})
        converted.append((z['id'], z['net'], z['layer'], (x0, y0, x1, y1), tracks[-1]))
        side = z['layer'][0]
        for q in pads:
            if q['net'] != z['net'] or side not in q['layers']:
                continue
            if not bg.rects_overlap(q['box'], (x0, y0, x1, y1), -EPS):
                continue
            if capsule_hits_box(tuple(path[0]), tuple(path[1]), width / 2, q['box']):
                continue
            (ax, ay), (bx, by) = path
            cx, cy = q['at']
            L2 = (bx - ax) ** 2 + (by - ay) ** 2
            tt = 0.0 if L2 == 0 else max(0.0, min(1.0, ((cx - ax) * (bx - ax) + (cy - ay) * (by - ay)) / L2))
            px, py = ax + tt * (bx - ax), ay + tt * (by - ay)
            sw = min(width, q['box'][2] - q['box'][0], q['box'][3] - q['box'][1])
            tracks.append({'id': f'CU-{z["id"]}-{q["number"]}', 'net': z['net'], 'layer': z['layer'], 'width_mm': r4(sw),
                           'path': [[r4(px), r4(py)], [r4(cx), r4(cy)]], 'locked': True,
                           'why': f'joins pad {q["number"]}, which pour {z["id"]} touched and its track misses'})
            notes.append(f'{z["id"]}: stub to pad {q["number"]} at ({r4(cx)}, {r4(cy)}), {r4(sw)} mm')
    # Joints (after route iteration 2, sr-rx-pcb run 43295500516: pours that met edge to edge became tracks that only
    # touch, so KiCad left them apart: E1_LAB5_RAW, E1_SW, E1_CONV_IN, E1_SYS12_SW and LAB5 stems unconnected, 2
    # track_dangling, 2 connection_width): for every pair of same-net pours that overlap or touch and whose tracks do not
    # overlap by JOINT_OVERLAP, a locked track from the nearest axis point of one to the nearest axis point of the other
    # through the centre of their common edge or area, as wide as the narrower pour and the common length allow.
    for i, (ida, net, layer, ra, ta) in enumerate(converted):
        for idb, netb, layerb, rb, tb in converted[i + 1:]:
            if netb != net or layerb != layer or not bg.rects_overlap(ra, rb, EPS):
                continue
            pa, pb = [tuple(p) for p in ta['path']], [tuple(p) for p in tb['path']]
            if seg_seg_dist(pa[0], pa[1], pb[0], pb[1]) <= (ta['width_mm'] + tb['width_mm']) / 2 - JOINT_OVERLAP:
                continue
            cx0, cy0, cx1, cy1 = max(ra[0], rb[0]), max(ra[1], rb[1]), min(ra[2], rb[2]), min(ra[3], rb[3])
            c = ((cx0 + cx1) / 2, (cy0 + cy1) / 2)
            common = max(cx1 - cx0, cy1 - cy0)
            ends = []
            for (a, b) in (pa, pb):
                L2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
                tt = 0.0 if L2 == 0 else max(0.0, min(1.0, ((c[0] - a[0]) * (b[0] - a[0]) + (c[1] - a[1]) * (b[1] - a[1])) / L2))
                ends.append((r4(a[0] + tt * (b[0] - a[0])), r4(a[1] + tt * (b[1] - a[1]))))
            path = [list(ends[0]), [r4(c[0]), r4(c[1])], list(ends[1])]
            path = [p for k, p in enumerate(path) if k == 0 or p != path[k - 1]]
            if len(path) < 2:
                continue
            # as wide as the narrower track, less where another net's pad or scripted copper of the layer comes closer
            # than CLEAR + MARGIN (never below the common length of the two pours)
            w = min(ta['width_mm'], tb['width_mm'])
            side = layer[0]
            for q in pads:
                if q['net'] == net or side not in q['layers']:
                    continue
                d = min(seg_box_dist(tuple(a), tuple(b), q['box']) for a, b in zip(path, path[1:]))
                w = min(w, 2 * (d - CLEAR - MARGIN))
            for o in tracks:
                if o['net'] == net or o['layer'] != layer:
                    continue
                for oa, ob in zip(o['path'], o['path'][1:]):
                    d = min(seg_seg_dist(tuple(a), tuple(b), tuple(oa), tuple(ob)) for a, b in zip(path, path[1:]))
                    w = min(w, 2 * (d - o['width_mm'] / 2 - CLEAR - MARGIN))
            w = r4(max(min(common, ta['width_mm'], tb['width_mm']), math.floor(w * 100) / 100))
            tracks.append({'id': f'CU-{ida}-J-{idb}', 'net': net, 'layer': layer, 'width_mm': w, 'path': path, 'locked': True,
                           'why': f'joint of the scripted pours {ida} and {idb}, which meet edge to edge (make_board.py '
                                  'board_copper)'})
            notes.append(f'joint {ida} - {idb} ({net}, {w} mm)')
    for (net, layer, _pri, _pc), group in sorted(inner.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        rest = list(group)
        while rest:
            cluster = [rest.pop(0)]
            grew = True
            while grew:
                grew = False
                for z in list(rest):
                    if any(bg.rects_overlap(poly_box(z['outline']), poly_box(c['outline']), EPS) for c in cluster):
                        cluster.append(z)
                        rest.remove(z)
                        grew = True
            if len(cluster) == 1:
                zones.append(cluster[0])
                continue
            outline = rect_union_outline([poly_box(c['outline']) for c in cluster])
            if outline is None:
                raise SystemExit(f'make_board: the {net} pours {[c["id"] for c in cluster]} on {layer} do not merge into one outline')
            ids = '+'.join(c['id'] for c in cluster)
            zones.append({**cluster[0], 'id': ids, 'outline': outline,
                          'why': f'merged scripted pours {ids} (KiCad 10.0.7 reports zones_intersect for same-net zones of '
                                 'one priority that overlap, sr-rx-pcb run 43287918183)'})
            notes.append(f'merged {ids} on {layer}')
    return {'tracks': tracks, 'vias': list(pre['vias']), 'zones': zones}, notes


def stem_exemptions(inp, tracks, netclasses):
    """neck_exempt for the scripted pin-entry stems (W2 PCB-PWRA-3: pours narrower than their class that lie within half
    the class width of their pins; as locked tracks pcb/check_boards.py measures them exactly): per ref, the escape
    length that covers every such stem from that ref's pad of the stem's net (check_boards neck_exempt rule: both ends
    within escape_mm + half the larger pad side of the pad centre)."""
    width = {n: netclasses['classes'][c['class']]['outer_min_width_mm'] for n, c in netclasses['nets'].items()
             if netclasses['classes'].get(c['class'], {}).get('kind') == 'power'}
    out = {}
    for t in tracks:
        need = width.get(t['net'])
        if need is None or t['width_mm'] + 1e-9 >= need or not t['id'].startswith('CU-'):
            continue
        ends = [tuple(p) for p in t['path']]
        a, b = ends[0], ends[-1]
        best = None
        for pa in inp.parts.values():
            for q in pa.pads:
                if q['net'] != t['net'] or t['layer'][0] not in q['layers']:
                    continue
                if not any(capsule_hits_box(p, r, t['width_mm'] / 2 + 3.0, q['box']) for p, r in zip(ends, ends[1:])):
                    continue
                half = max(q['box'][2] - q['box'][0], q['box'][3] - q['box'][1]) / 2
                esc = max(math.dist(p, q['at']) for p in ends) - half
                if best is None or esc < best[0]:
                    best = (esc, pa.ref, q['number'])
        if best is None:
            raise SystemExit(f'make_board: stem {t["id"]} ({t["width_mm"]} mm < {need} mm) touches no pad of its net')
        esc, ref, num = best
        row = out.setdefault(ref, {'escape_mm': 0.0, 'stems': []})
        row['escape_mm'] = max(row['escape_mm'], 0.1, r4(math.ceil((esc + 0.05) / 0.05) * 0.05))
        row['stems'].append(f'{t["id"][3:]} ({t["net"]}, {t["width_mm"]} mm, pad {num})')
    return {ref: {'escape_mm': r4(row['escape_mm']),
                  'reason': 'scripted pin-entry stem(s) narrower than the net class where they enter the pins (W2 PCB-PWRA-3 '
                            'scripted copper, kept within half the class width of the pins): ' + ', '.join(row['stems'])}
            for ref, row in sorted(out.items(), key=lambda kv: bg.sort_ref(kv[0]))}


# ------------------------------------------------------------------ W2 PWR-L6-SCRIPT: converter stages and 2 oz rework
# Sources, re-read 2026-11-14 (curl default User-Agent, HTTP 200; fetch-only, not committed):
#   TI LM61460 SNVSBD5D (rev. D, July 2022) section 11.1 Layout Guidelines and figure 11-2, https://www.ti.com/lit/ds/symlink/lm61460.pdf
#   (sha256 2c8a0bf340c70aa3ac29e586146804d7651822e14bee0897f6415ee9e56be84d): input capacitors at VIN1/PGND1 and VIN2/PGND2;
#   CVCC close to VCC and AGND "with short, wide traces"; "route the SW connection under the device through the gap between VIN2
#   and RBOOT pins"; RBOOT "as close as possible to CBOOT and RBOOT pins"; the feedback divider close to FB ("The connection to
#   VOUT can be somewhat longer", away from SW); "Layer of the PCB beneath the top layer with the IC must be a ground plane";
#   figure 11-2 "VIAS to BIAS"; 11.1.1 two-ounce outer copper.
#   TI TPSM63606 SLVSGB4B (rev. B, April 2022) section 11.1, https://www.ti.com/lit/ds/symlink/tpsm63606.pdf (sha256
#   d1c157ff51c0e24bec9749dc434c3f8cdb8e980a7d1295d3a51c7d13f8ab4147): "use a wide polygon plane on a lower PCB layer to connect
#   these [VOUT] pins together and to the load"; feedback resistors close to FB; "Connect AGND pins 6 and 11 directly to PGND
#   pin 19 under the module"; solid ground plane on the layer below; figure 11-2 "Place thermal vias at the VOUT pins".
SCRIPT_SOURCE = ('TI LM61460 SNVSBD5D (rev. D, July 2022) section 11.1 and figure 11-2, https://www.ti.com/lit/ds/symlink/lm61460.pdf, '
                 'and TI TPSM63606 SLVSGB4B (rev. B, April 2022) section 11.1 and figure 11-2, '
                 'https://www.ti.com/lit/ds/symlink/tpsm63606.pdf, both re-read 2026-11-14 (curl default User-Agent, HTTP 200, sha256 '
                 '2c8a0bf3... and d1c157ff...; fetch-only, not committed)')


def sc_track(tid, net, width, path, why, layer='F.Cu'):
    return {'id': tid, 'net': net, 'layer': layer, 'width_mm': width, 'path': [[r4(x), r4(y)] for x, y in path], 'locked': True,
            'why': why + ' (W2 PWR-L6-SCRIPT, make_board.py)'}


# The pin-entry stems of the SHRINK-2 pours (W2 PCB-PWRA-3, sized for 1 oz) that the 2 oz class widths and the exemption policy
# (no neck on power-switch nodes, converter capacitors or connector lands; no pin stems) replace: board_copper ids -> why.
SCRIPT_DROP = {
    'CU-E1SW-Q102': 'Q102 source stem 1.45 mm < BATT 1.6 (power switch): a 1.6 mm pin-group bar instead',
    'CU-E1SW-BAR-J-E1SW-Q102': 'joint of the old Q102 stem',
    'CU-SYS12-Q201': 'Q201 source stem 1.4 mm < BATT 1.6 (power switch): a 1.6 mm entry instead',
    'CU-SYS12SW-PIN': 'U107 SW stem 0.7 mm: the SW entry pour instead (within half the class width of the pin)',
    'CU-SYS12SW-PIN-J-SYS12SW-L102': 'joint of the old SW stem',
    'CU-CONVIN-U107-L-BAR': 'VIN2 bar re-scripted above the SW-CBOOT link (C122 moved up)',
    'CU-CONVIN-U107-L-J-CONVIN-U107-L-BAR': 'joint of the old VIN2 bar (it crossed the SW-CBOOT link)',
    'CU-GND-U107-L': 'PGND2 bar re-scripted clear of the moved C122.1',
    'CU-LAB5RAW-VOUT1': 'U108 VOUT1 stem 1.3 mm < BATT 1.6: a 1.6 mm entry instead',
    'CU-LAB5RAW-VOUT2': 'U108 VOUT2 stem 1.3 mm < BATT 1.6: a 1.6 mm entry instead',
    'CU-LAB5RAW-BAR-J-LAB5RAW-VOUT1': 'joint of the old VOUT1 stem',
    'CU-LAB5RAW-BAR-J-LAB5RAW-VOUT2': 'joint of the old VOUT2 stem',
    'CU-LAB5RAW-BAR-1': 'R129.1 stub 0.8 mm < BATT 1.6: a 1.6 mm track to the regulation point instead',
    'CU-LAB5-B-SPINE': 'B.Cu LAB5 spine 2.2 mm: wider (2.5 mm) where the bond zone 3 keep-out and the E1_CONV_IN via column allow, with '
                       'parallel strips (E1-05 path A)',
    'CU-LAB5-B-TOP': 'B.Cu LAB5 top run 2.2 mm: 2.4 / 2.3 mm (E1-05 path A)',
}
U107_WHY = 'LM61460 U107 stage per SNVSBD5D 11.1 / figure 11-2'
E105_WHY = 'PWR3A LAB5 E1-05 path A copper on 2 oz B.Cu'
U108_WHY = 'TPSM63606 U108 stage per SLVSGB4B 11.1 / figure 11-2'
# Converter-stage and rework copper (board mm, y up): tracks, vias, zones. Widths: signal pieces 0.2-0.25 mm (SIG class 0.15);
# power-class pieces at the 2 oz class width or wider; the three low-current power-net pieces narrower than their class are
# branch_exempt rows of SCRIPT_BRANCHES (exemption policy: sense or logic pins only).
SCRIPT_TRACKS = [
    # --- U107 LM61460 (zone 3') ---
    sc_track('SC-U107-SWLINK', 'E1_SYS12_SW', 0.25, [(16.0, 46.375), (11.15, 46.375), (11.15, 45.3)],
             f'{U107_WHY}: SW to the CBOOT capacitor C127.2 under the device through the gap between VIN2 (pin 12) and RBOOT (pin 13), '
             'then under C122.1 and above R127.2; F.Cu only, no via (gate-drive charge only: branch of C127)'),
    sc_track('SC-U107-CBOOT', 'E1_SYS12_CBOOT', 0.25, [(14.3, 45.375), (13.5, 45.375), (13.5, 43.525), (12.65, 43.525)],
             f'{U107_WHY}: CBOOT pin 14 to RBOOT R127.1 (short)'),
    sc_track('SC-U107-CBOOT-C127', 'E1_SYS12_CBOOT', 0.25, [(12.65, 43.55), (11.15, 43.575)], f'{U107_WHY}: R127.1 to CBOOT C127.1'),
    sc_track('SC-U107-RBOOT', 'E1_SYS12_RBOOT', 0.2, [(14.3, 45.875), (12.65, 45.875), (12.65, 45.3)],
             f'{U107_WHY}: RBOOT pin 13 to R127.2, between the CBOOT track and the SW link'),
    sc_track('SC-U107-VCC', 'E1_SYS12_VCC', 0.25, [(15.475, 44.5), (15.475, 43.3)], f'{U107_WHY}: VCC pin 2 to CVCC C128.1, short'),
    sc_track('SC-U107-AGND', 'GND', 0.2, [(16.0, 44.5), (16.0, 43.7), (16.4, 43.3)], f'{U107_WHY}: AGND pin 3 to CVCC C128.2, short'),
    sc_track('SC-U107-FB', 'E1_SYS12_FB', 0.2, [(16.525, 44.5), (16.525, 44.0), (17.4, 44.0), (17.4, 41.6)],
             f'{U107_WHY}: FB pin 4 round C128.2 to RFBB R125.1; FB node on F.Cu only'),
    sc_track('SC-U107-FB-R128', 'E1_SYS12_FB', 0.2, [(16.075, 41.5), (17.6, 41.5)], f'{U107_WHY}: RFF R128.2 to RFBB R125.1 (FB node)'),
    sc_track('SC-U107-FB-R124', 'E1_SYS12_FB', 0.2, [(17.6, 41.5), (17.6, 39.85)], f'{U107_WHY}: RFBB R125.1 to RFBT R124.2 (FB node)'),
    sc_track('SC-U107-FF', 'E1_SYS12_FF', 0.2, [(14.425, 41.5), (14.475, 39.85)], f'{U107_WHY}: RFF R128.1 to CFF C129.2'),
    sc_track('SC-U107-BIAS', 'SYS12', 0.25, [(14.4, 44.825), (13.95, 42.55)],
             f'{U107_WHY}: BIAS pin 1 down to the output sense line (sense/bias pin, milliamperes: branch of U107 pad 1)'),
    sc_track('SC-U107-SENSE', 'SYS12', 0.25, [(19.25, 39.85), (19.25, 38.9), (16.025, 38.9), (13.65, 38.9), (13.65, 42.2), (13.95, 42.55)],
             f'{U107_WHY}: the output sense of RFBT R124.1 and CFF C129.1 to the BIAS via, below the divider and away from SW'),
    sc_track('SC-U107-SENSE-C129', 'SYS12', 0.25, [(16.025, 39.85), (16.025, 38.9)], f'{U107_WHY}: CFF C129.1 to the output sense'),
    sc_track('SC-U107-SENSE-V1S', 'SYS12', 0.25, [(13.65, 38.9), (12.9, 38.3)],
             f'{U107_WHY}: the output sense line to its via below zone 3\' ("VIAS to BIAS"; the via outside the bond zone)'),
    sc_track('SC-U107-SENSE-IN2', 'SYS12', 0.25, [(12.9, 38.3), (12.9, 55.0), (6.2, 61.7), (6.2, 62.0)],
             f'{U107_WHY}: the BIAS / RFBT output sense on In2.Cu (In1.Cu GND between it and the F.Cu SW copper) to the SYS12 bar '
             'left of zone 3\'', layer='In2.Cu'),
    sc_track('SC-U107-VINBAR', 'E1_CONV_IN', 0.5, [(9.15, 46.725), (10.2, 47.05), (13.07, 47.05)],
             f'{U107_WHY}: CIN2 C119.1 to CIN_HF2 C122.1 along the VIN2 level, above the SW-CBOOT link'),
    # --- E1-05 path A (L101.2 -> L205.1): the B.Cu LAB5 trunk at the free width (MODEL scan of freeze/plan6.py at 0.20 mm) ---
    sc_track('SC-LAB5-B-TOP-1', 'LAB5', 2.4, [(2.0, 91.5), (13.0, 91.5)], E105_WHY + ': top run from the L101 vias, 2.4 mm', 'B.Cu'),
    sc_track('SC-LAB5-B-TOP-2', 'LAB5', 2.3, [(13.0, 91.5), (25.4, 91.5)], E105_WHY + ': top run to the spine, 2.3 mm', 'B.Cu'),
    sc_track('SC-LAB5-B-SPINE-1', 'LAB5', 2.5, [(25.6, 28.6), (25.6, 66.0)],
             E105_WHY + ': spine 2.5 mm (x 24.35-26.85: 0.3 mm off thermal_bond zone 3, 0.2 mm off the E1_CONV_IN vias at x 27.5)', 'B.Cu'),
    sc_track('SC-LAB5-B-SPINE-2', 'LAB5', 2.2, [(25.4, 66.0), (25.4, 91.5)], E105_WHY + ': spine 2.2 mm above y 66', 'B.Cu'),
    sc_track('SC-LAB5-B-PAR1', 'LAB5', 2.15, [(26.0, 37.0), (28.05, 37.0), (28.05, 41.0), (26.0, 41.0)],
             E105_WHY + ': parallel strip beside the spine at y 37-41', 'B.Cu'),
    sc_track('SC-LAB5-B-PAR2', 'LAB5', 2.5, [(26.0, 48.3), (28.05, 48.3), (28.05, 51.7), (26.0, 51.7)],
             E105_WHY + ': parallel strip beside the spine at y 48-52', 'B.Cu'),
    sc_track('SC-LAB5-B-PAR3', 'LAB5', 2.2, [(25.4, 72.5), (27.75, 72.5)], E105_WHY + ': join of the strip at y 72.5', 'B.Cu'),
    sc_track('SC-LAB5-B-PAR3-S', 'LAB5', 2.5, [(27.75, 72.5), (27.75, 84.0)], E105_WHY + ': parallel strip beside the spine at y 72-84',
             'B.Cu'),
    sc_track('SC-LAB5-B-PAR3-T', 'LAB5', 2.2, [(27.75, 84.0), (25.4, 84.0)], E105_WHY + ': join of the strip at y 84', 'B.Cu'),
    sc_track('SC-LAB5-F-BAND', 'LAB5', 2.0, [(26.2, 27.8), (39.6, 27.8)],
             E105_WHY.replace('B.Cu', 'F.Cu') + ': F.Cu strip over the B.Cu band (y 26.8-28.8, free at 0.20 mm) into the RISE-L copper; '
             'three vias to the band at its left end'),
    sc_track('SC-U107-PGND2', 'GND', 1.2, [(8.3, 48.4), (14.3, 48.4)], f'{U107_WHY}: PGND2 to C122.2 and C119.2 (clear of C122.1)'),
    sc_track('SC-Q102-S', 'E1_SW', 1.6, [(26.175, 35.0), (26.175, 36.9)],
             'BATT 1.6 mm pin-group bar over the Q102 sources S1-S3 from the E1_SW bar (power switch: no neck, no stem)'),
    sc_track('SC-Q201-S', 'SYS12', 1.6, [(31.468, 58.05), (31.468, 59.5)],
             'BATT 1.6 mm from the SYS12 crossing onto the Q201 source (power switch: no neck, no stem)'),
    # --- U108 TPSM63606 (zone 4') ---
    sc_track('SC-U108-VOUT1', 'E1_LAB5_RAW', 1.6, [(12.0, 76.2), (12.0, 77.3)], f'{U108_WHY}: BATT 1.6 mm onto VOUT1 (pin 8) from its via'),
    sc_track('SC-U108-VOUT2', 'E1_LAB5_RAW', 1.6, [(16.0, 76.2), (16.0, 77.3)], f'{U108_WHY}: BATT 1.6 mm onto VOUT2 (pin 9) from its via'),
    sc_track('SC-U108-R129', 'E1_LAB5_RAW', 1.6, [(16.0, 77.0), (17.875, 77.0)],
             f'{U108_WHY}: the regulation point RFBT R129.1 at the VOUT2 copper, at the class width'),
    sc_track('SC-U108-VLDOIN', 'E1_LAB5_RAW', 0.25, [(11.75, 79.725), (11.0, 79.725), (11.0, 78.35), (11.45, 77.9)],
             f'{U108_WHY}: VLDOIN pin 5 (LDO bias input, milliamperes: branch of U108 pad 5) to VOUT1'),
    sc_track('SC-U108-AGND6', 'GND', 0.25, [(11.75, 79.225), (13.4, 79.225)], f'{U108_WHY}: AGND pin 6 to PGND pin 19 under the module'),
    sc_track('SC-U108-AGND11', 'GND', 0.25, [(16.25, 79.225), (14.6, 79.225)], f'{U108_WHY}: AGND pin 11 to PGND pin 19 under the module'),
    sc_track('SC-U108-FB', 'E1_LAB5_FB', 0.2, [(16.25, 78.725), (17.875, 78.725), (18.7, 78.1), (19.525, 77.0)],
             f'{U108_WHY}: FB pin 10 to RFBB R130.1 and RFBT R129.2 (feedback resistors at FB), F.Cu only'),
    sc_track('SC-U108-RT', 'E1_LAB5_RT', 0.2, [(16.25, 79.725), (22.15, 79.725)], f'{U108_WHY}: RT pin 12 to R131.1'),
]
SCRIPT_VIAS = [  # (id, net, (x, y), why): 0.6 / 0.3 like the other scripted vias
    ('SC-U107-SENSE-V1', 'SYS12', (12.9, 38.3), f'{U107_WHY}: BIAS / output-sense via ("VIAS to BIAS"), below thermal_bond zone 3\''),
    ('SC-U107-SENSE-V2', 'SYS12', (6.2, 62.0), f'{U107_WHY}: the output sense up into the SYS12 bar left of thermal_bond zone 3\''),
    ('SC-LAB5-F-BAND-V1', 'LAB5', (26.2, 27.8), 'E1-05 path A: F.Cu band strip to the B.Cu band and spine'),
    ('SC-LAB5-F-BAND-V2', 'LAB5', (27.0, 28.4), 'E1-05 path A: F.Cu band strip to the B.Cu band'),
    ('SC-LAB5-F-BAND-V3', 'LAB5', (27.9, 28.4), 'E1-05 path A: F.Cu band strip to the B.Cu band'),
    ('SC-U108-VOUT-V1', 'E1_LAB5_RAW', (12.0, 76.2), f'{U108_WHY}: thermal via at VOUT1 to the In4.Cu VOUT polygon'),
    ('SC-U108-VOUT-V2', 'E1_LAB5_RAW', (16.0, 76.2), f'{U108_WHY}: thermal via at VOUT2 to the In4.Cu VOUT polygon'),
    ('SC-U108-VOUT-V3', 'E1_LAB5_RAW', (14.0, 76.2), f'{U108_WHY}: thermal via between the VOUT pins to the In4.Cu VOUT polygon'),
]


def sc_zone(zid, net, layer, outline, why, priority=3):
    return {'id': zid, 'net': net, 'layer': layer, 'outline': [[r4(x), r4(y)] for x, y in outline], 'priority': priority,
            'pad_connection': 'solid', 'why': why + ' (W2 PWR-L6-SCRIPT, make_board.py; a pin-entry pour stays a zone: narrower than '
            'its class only within half the class width of its pad, where pcb/check_boards.py counts it as the pad)'}


SCRIPT_ZONES = [
    sc_zone('SC-U107-SW-ENTRY', 'E1_SYS12_SW', 'F.Cu', [(15.25, 46.5), (16.75, 46.5), (16.75, 49.6), (15.25, 49.6)],
            f'{U107_WHY}: SW pin 10 (0.4 x 2.4 mm between the PGND/VIN pins) up to the L102.1 trunk: 1.5 mm wide inside the pin rows '
            '(0.2 mm to the PGND/VIN pins), the BATT trunk 0.8 mm beyond the pin end'),
    sc_zone('SC-U108-VOUT-IN4', 'E1_LAB5_RAW', 'In4.Cu', [(11.2, 75.5), (16.8, 75.5), (16.8, 76.9), (11.2, 76.9)],
            f'{U108_WHY}: VOUT pins 8/9 joined by a polygon on a lower layer (In4.Cu, over the GND fill) through the three VOUT vias',
            priority=2),
]
# branch_exempt rows of the scripted converter copper (exemption policy: sense or logic pins only): ref -> row
SCRIPT_BRANCHES = {
    'C127': {'max_mm': 7.0, 'min_width_mm': 0.25,
             'reason': 'SW-CBOOT link (SNVSBD5D 11.1: through the VIN2-RBOOT gap) to the bootstrap capacitor; gate-drive charge only'},
    'U107': {'pads': ['1'], 'max_mm': 40.0, 'min_width_mm': 0.25,
             'reason': 'BIAS pin 1 and the RFBT / CFF output sense: bias and sense current (milliamperes), In2.Cu under the In1.Cu GND'},
    'U108': {'pads': ['5'], 'max_mm': 3.5, 'min_width_mm': 0.25,
             'reason': 'VLDOIN pin 5 (internal LDO input, milliamperes) to VOUT1 between the module pins'},
}
EXEMPTION_POLICY = {
    'why': ('W2 PWR-L6-SCRIPT (synthesis PWR-L6-SCRIPT, judge 1 power rating): class-width exemptions follow the pad they serve. '
            'branch_exempt only for test points, resistors of 100 ohm or more and sense or logic pins; no neck on TVS, connector or '
            'harness lands, shunts, fuses, power-switch nodes, eFuse IN/OUT or converter capacitors; a neck at least as wide as its '
            'pad and no longer than it (no pin stems); pin entries are pours within half the class width of the pad'),
}


def script_copper(pre):
    """W2 PWR-L6-SCRIPT: the converter-stage copper of U107/U108 and the 2 oz rework of the SHRINK-2 pin-entry stems (SCRIPT_DROP
    out, SCRIPT_TRACKS / SCRIPT_VIAS / SCRIPT_ZONES in). Returns (pre_route, notes)."""
    have = {t['id'] for t in pre['tracks']}
    missing = sorted(set(SCRIPT_DROP) - have)
    if missing:
        raise SystemExit(f'make_board: the scripted pieces {missing} that W2 PWR-L6-SCRIPT replaces are gone (board_copper changed)')
    tracks = [t for t in pre['tracks'] if t['id'] not in SCRIPT_DROP] + [dict(t) for t in SCRIPT_TRACKS]
    vias = list(pre['vias']) + [{'id': vid, 'net': net, 'at': [r4(at[0]), r4(at[1])], 'diameter_mm': 0.6, 'drill_mm': 0.3,
                                 'locked': True, 'why': why + ' (W2 PWR-L6-SCRIPT, make_board.py; the project via 0.6/0.3)'}
                                for vid, net, at, why in SCRIPT_VIAS]
    zones = list(pre['zones']) + [dict(z) for z in SCRIPT_ZONES]
    notes = [f'dropped {k}: {v}' for k, v in sorted(SCRIPT_DROP.items())]
    return {'tracks': tracks, 'vias': vias, 'zones': zones}, notes


def script_clearance(inp, pre, ids):
    """Clearance of the W2 PWR-L6-SCRIPT copper (ids) against the pads of other nets and every other scripted item (pad copper
    boxes, capsules, pour boxes; MODEL, conservative for round and custom pads): problems below CLEAR."""
    problems = []
    pads = [(pa.ref, q) for pa in inp.parts.values() for q in pa.pads if q['type'] != 'np_thru_hole']
    segs = []
    for t in pre['tracks']:
        for a, b in zip(t['path'], t['path'][1:]):
            segs.append((t['id'], t['net'], t['layer'], tuple(a), tuple(b), t['width_mm'] / 2))
    for v in pre['vias']:
        segs.append((v['id'], v['net'], '*', tuple(v['at']), tuple(v['at']), v['diameter_mm'] / 2))
    boxes = [(z['id'], z['net'], z['layer'], zb) for z in pre['zones'] if z['outline'] != 'board' for zb in outline_boxes(z['outline'])]

    def on(layer_a, layer_b):
        return layer_a == '*' or layer_b == '*' or layer_a == layer_b
    for sid, net, layer, a, b, r in segs:
        if sid not in ids:
            continue
        for ref, q in pads:
            lays = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu'] if q['type'] == 'thru_hole' else [f'{q["layers"][0]}.Cu']
            if q['net'] == net or not any(on(layer, l) for l in lays):
                continue
            d = seg_box_dist(a, b, q['box']) - r
            if d < CLEAR - EPS:
                problems.append(f'{sid} ({net}) {r4(d)} mm from pad {ref}.{q["number"]} ({q["net"]})')
        for oid, onet, olayer, c, d_, orr in segs:
            if oid == sid or onet == net or not on(layer, olayer):
                continue
            d = seg_seg_dist(a, b, c, d_) - r - orr
            if d < CLEAR - EPS:
                problems.append(f'{sid} ({net}) {r4(d)} mm from {oid} ({onet})')
        for zid, znet, zlayer, zb in boxes:
            if znet == net or not on(layer, zlayer):
                continue
            d = seg_box_dist(a, b, zb) - r
            if d < CLEAR - EPS:
                problems.append(f'{sid} ({net}) {r4(d)} mm from pour {zid} ({znet})')
    for zid, znet, zlayer, zb in boxes:
        if zid not in ids:
            continue
        for ref, q in pads:
            if q['net'] == znet or zlayer[0] not in q['layers']:
                continue
            d = box_dist(zb, q['box'])
            if d < CLEAR - EPS:
                problems.append(f'{zid} ({znet}) {r4(d)} mm from pad {ref}.{q["number"]} ({q["net"]})')
        for oid, onet, olayer, c, d_, orr in segs:
            if onet == znet or not on(zlayer, olayer):
                continue
            d = seg_box_dist(c, d_, zb) - orr
            if d < CLEAR - EPS:
                problems.append(f'{zid} ({znet}) {r4(d)} mm from {oid} ({onet})')
    return sorted(set(problems))


def scripted_joined(inp, pre):
    """Per net with converted pours: the scripted tracks (CU-*) and the pads they reach, joined by geometric overlap of
    at least JOINT_OVERLAP (tracks) or contact (pads, vias), must form one piece. Returns problems."""
    problems = []
    # W2 PWR-L6-SCRIPT: the SC- copper (converter stages, 2 oz rework) counts too, and its F.Cu/B.Cu pin-entry pours join what they
    # overlap (as KiCad fills them: a zone joins its net's pads and tracks inside it)
    tracks = [t for t in pre['tracks'] if t['id'].startswith('CU-') or (t['id'].startswith('SC-') and t['net'] != 'GND')]
    for net in sorted({t['net'] for t in tracks}):
        mine = [t for t in tracks if t['net'] == net]
        segs = [(tuple(a), tuple(b), t['width_mm'] / 2, t['layer'][0], t['id']) for t in mine for a, b in zip(t['path'], t['path'][1:])]
        segs += [((zb[0], zb[1]), (zb[2], zb[3]), 0.0, z['layer'][0], z['id'], zb) for z in pre['zones']
                 if z['net'] == net and z['outline'] != 'board' and z['layer'] in ('F.Cu', 'B.Cu') for zb in [poly_box(z['outline'])]]
        segs = [s if len(s) == 6 else s + (None,) for s in segs]
        vias = [(tuple(v['at']), v['diameter_mm'] / 2) for v in pre['vias'] if v['net'] == net]
        pads = [(pa.ref, q) for pa in inp.parts.values() for q in pa.pads if q['net'] == net]
        nodes = [('s', k) for k in range(len(segs))] + [('v', k) for k in range(len(vias))] + [('p', k) for k in range(len(pads))]
        parent = {n: n for n in nodes}

        def find(n):
            while parent[n] != n:
                parent[n] = parent[parent[n]]
                n = parent[n]
            return n

        def union(a, b):
            parent[find(a)] = find(b)
        def touch(si, sj, overlap):
            (a, b, r, _l, _i, za), (c, d, r2, _l2, _i2, zb) = si, sj
            if za and zb:
                return bg.rects_overlap(za, zb, -overlap)
            if za or zb:
                box, (p, q, rr) = (za, (c, d, r2)) if za else (zb, (a, b, r))
                return seg_box_dist(p, q, box) <= rr - overlap
            return seg_seg_dist(a, b, c, d) <= r + r2 - overlap
        for i, (a, b, r, lay, _id, za) in enumerate(segs):
            for j in range(i + 1, len(segs)):
                if lay == segs[j][3] and touch(segs[i], segs[j], JOINT_OVERLAP):
                    union(('s', i), ('s', j))
            for k, (c, rv) in enumerate(vias):
                if (seg_box_dist(c, c, za) <= rv - JOINT_OVERLAP) if za else seg_seg_dist(a, b, c, c) <= r + rv - JOINT_OVERLAP:
                    union(('s', i), ('v', k))
            for k, (_ref, q) in enumerate(pads):
                if lay in q['layers'] and (bg.rects_overlap(za, q['box'], EPS) if za else capsule_hits_box(a, b, r, q['box'])):
                    union(('s', i), ('p', k))
        for k, (c, _rv) in enumerate(vias):  # a via in a pad of its net joins it
            for kp, (_ref, q) in enumerate(pads):
                if q['box'][0] - EPS <= c[0] <= q['box'][2] + EPS and q['box'][1] - EPS <= c[1] <= q['box'][3] + EPS:
                    union(('v', k), ('p', kp))
        # inner zones and planes of the net join the vias inside them (E1_CONV_IN strap and bridge on In2, GND planes)
        for z in pre['zones']:
            if z['net'] != net or z['layer'] in ('F.Cu', 'B.Cu'):
                continue
            inside = [k for k, (c, _rv) in enumerate(vias) if z['outline'] == 'board' or bg.point_in_outline(c, z['outline'])]
            for k in inside[1:]:
                union(('v', inside[0]), ('v', k))
        reached = {find(('s', i)) for i in range(len(segs))}
        if len(reached) > 1:
            groups = {}
            for i, s in enumerate(segs):
                groups.setdefault(find(('s', i)), set()).add(s[4][3:] if s[4][:3] in ('CU-', 'SC-') else s[4])
            problems.append(f'scripted {net} copper falls into {len(reached)} pieces: '
                            + ' | '.join(', '.join(sorted(g)) for g in groups.values()))
    return problems


# ------------------------------------------------------------------ scripted copper as obstacles
def scripted_items(pre):
    """Segments (tracks, vias as points) and pour boxes of the scripted copper: {'net', 'layer', 'a', 'b', 'r'}."""
    segs = []
    for t in pre.get('tracks', []):
        for a, b in zip(t['path'], t['path'][1:]):
            segs.append({'net': t['net'], 'layer': t['layer'][0], 'a': tuple(a), 'b': tuple(b), 'r': t['width_mm'] / 2})
    for v in pre.get('vias', []):
        segs.append({'net': v['net'], 'layer': '*', 'a': tuple(v['at']), 'b': tuple(v['at']), 'r': v['diameter_mm'] / 2})
    pours = []
    for z in pre.get('zones', []):
        if z['outline'] == 'board':
            continue
        layer = {'F.Cu': 'F', 'B.Cu': 'B'}.get(z['layer'], z['layer'])
        outline = [tuple(p) for p in z['outline']]
        for box in outline_boxes(outline):  # a merged rectilinear zone counts by its rectangles, not its bounding box
            pours.append({'net': z['net'], 'layer': layer, 'box': box, 'outline': outline, 'id': z['id']})
    return segs, pours


def outline_boxes(outline):
    """The rectangles of a rectilinear outline (coordinate compression: covered cells merged along x per row band)."""
    if len(outline) == 4:
        return [poly_box(outline)]
    xs = sorted({p[0] for p in outline})
    ys = sorted({p[1] for p in outline})
    out = []
    for j in range(len(ys) - 1):
        run = None
        for i in range(len(xs) - 1):
            inside_cell = bg.point_in_outline(((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2), outline)
            if inside_cell and run is None:
                run = xs[i]
            if not inside_cell and run is not None:
                out.append((run, ys[j], xs[i], ys[j + 1]))
                run = None
        if run is not None:
            out.append((run, ys[j], xs[-1], ys[j + 1]))
    return out


# ------------------------------------------------------------------ GND fan-out (port of PWR_B make_spec.py gnd_fanout)
GND_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
GND_GAPS = (0.55, 0.9, 1.3, 1.8)


GRID = 0.1       # mm, raster of the long-stub search
REACH = 6.0      # mm, half window of the long-stub search around the pad


def grid_paths(p, layer, pads, segs, pours, outline):
    """Long GND stubs for a pad whose short candidates all fail (W2 PCB-PWRA-4: bottom chips under the scripted pours of
    the top side): breadth-first search on a GRID raster of the pad's own layer, from the pad centre, through cells that
    keep the stub CLEAR + MARGIN off other-net pads, scripted tracks and pours of that layer and EDGE + MARGIN off the
    outline; yields (path with its corners only, end) in order of path length, each end a via candidate for clear()."""
    cx, cy = p['at']
    n = int(round(2 * REACH / GRID)) + 1
    x0, y0 = cx - REACH, cy - REACH
    half = W_GND / 2
    blocked = bytearray(n * n)

    def paint(box, inflate):
        bx0, by0, bx1, by1 = box[0] - inflate, box[1] - inflate, box[2] + inflate, box[3] + inflate
        i0, i1 = max(0, math.floor((bx0 - x0) / GRID)), min(n - 1, math.ceil((bx1 - x0) / GRID))
        j0, j1 = max(0, math.floor((by0 - y0) / GRID)), min(n - 1, math.ceil((by1 - y0) / GRID))
        for j in range(j0, j1 + 1):
            row = j * n
            for i in range(i0, i1 + 1):
                blocked[row + i] = 1
    need = CLEAR + MARGIN + half
    win = (x0 - 2, y0 - 2, x0 + 2 * REACH + 2, y0 + 2 * REACH + 2)
    for q in pads:
        if layer not in q['layers'] or not bg.rects_overlap(q['box'], win):
            continue
        if q['net'] == 'GND' and q['type'] != 'np_thru_hole':
            continue
        paint(q['box'], need + (0.1 if q['type'] == 'np_thru_hole' else 0.0))
    for s in segs:
        if s['net'] == 'GND' or s['layer'] not in (layer, '*'):
            continue
        box = (min(s['a'][0], s['b'][0]), min(s['a'][1], s['b'][1]), max(s['a'][0], s['b'][0]), max(s['a'][1], s['b'][1]))
        if bg.rects_overlap(box, win, s['r'] + need):
            paint(box, s['r'] + need)
    for z in pours:
        if z['net'] != 'GND' and z['layer'] == layer and bg.rects_overlap(z['box'], win, need):
            paint(z['box'], need)
    for j in range(n):
        for i in range(n):
            pt = (x0 + i * GRID, y0 + j * GRID)
            if not bg.point_in_outline(pt, outline) or edge_dist(pt, outline) - half < EDGE + MARGIN:
                blocked[j * n + i] = 1
    start = (int(round(REACH / GRID)), int(round(REACH / GRID)))
    # the pad's own copper is free for its stub
    sx0, sy0 = math.floor((p['box'][0] - x0) / GRID), math.floor((p['box'][1] - y0) / GRID)
    sx1, sy1 = math.ceil((p['box'][2] - x0) / GRID), math.ceil((p['box'][3] - y0) / GRID)
    for j in range(max(0, sy0), min(n, sy1 + 1)):
        for i in range(max(0, sx0), min(n, sx1 + 1)):
            blocked[j * n + i] = 0
    prev = {start: None}
    queue = [start]
    k = 0
    while k < len(queue):
        cur = queue[k]
        k += 1
        if k > 1:
            cells = [cur]
            while prev[cells[-1]] is not None:
                cells.append(prev[cells[-1]])
            cells.reverse()
            pts = [(r4(x0 + i * GRID), r4(y0 + j * GRID)) for i, j in cells]
            pts[0] = (cx, cy)
            corners = [pts[0]] + [b for a, b, c in zip(pts, pts[1:], pts[2:])
                                  if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1])] + [pts[-1]]
            yield corners, pts[-1]
        i, j = cur
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < n and 0 <= nj < n and (ni, nj) not in prev and not blocked[nj * n + ni]:
                prev[(ni, nj)] = cur
                queue.append((ni, nj))


def fixed_refs(study, shrink2=None):
    """Refs place_board.py never moves: the anchors of the SHRINK-2 spec and every part with a PWR-B cut-out."""
    shrink2 = shrink2 or read(HERE / 'PWR_A.spec-shrink2.json')
    return {p['ref'] for p in shrink2['parts'] if p.get('anchor')} | cutout_refs(study)


def gnd_fanout(inp, pre, first=frozenset(), failed=None):
    """A locked via next to every SMD GND pad that no scripted GND pour joins (stub W_GND from the pad centre); a pad
    in a pin row may instead reach an earlier GND fan-out or scripted GND via within 3 mm by a stub. Candidates are tried
    in a fixed order; the first that clears every other net (pads of both sides, scripted copper and pours on every layer
    for the via, on the stub layer for the stub), the edges, the hole keep-outs and the drill spacing is taken."""
    c = inp.contract
    holes = [(tuple(h), c['hole_keepout_d'] / 2) for h in c['holes_mm']]
    pads = [p for pa in inp.parts.values() for p in pa.pads]
    drills = [(p['at'], (p['drill'][0] if p['drill'] else min(p['box'][2] - p['box'][0], p['box'][3] - p['box'][1])))
              for p in pads if p['type'] in ('thru_hole', 'np_thru_hole')]
    drills += [(tuple(v['at']), v['drill_mm']) for v in pre.get('vias', [])]
    segs, pours = scripted_items(pre)
    gnd_vias = [tuple(v['at']) for v in pre.get('vias', []) if v['net'] == 'GND']
    need = CLEAR + MARGIN - EPS
    out_t, out_v, skipped = [], [], []

    def clear(path, via_at, layer, new_via):
        vx, vy = via_at
        stubs = list(zip(path, path[1:]))
        r = VIA_D / 2
        if any(edge_dist(q, inp.outline) - W_GND / 2 < EDGE + MARGIN or not bg.point_in_outline(q, inp.outline)
               for q in path[1:]):
            return False
        if new_via:
            if edge_dist(via_at, inp.outline) - r < EDGE + MARGIN:
                return False
            for (hx, hy), hr in holes:
                if math.hypot(vx - hx, vy - hy) - r < hr:
                    return False
            for (dx, dy), dd in drills:
                if math.hypot(vx - dx, vy - dy) < VIA_DRILL / 2 + dd / 2 + HOLE_GAP:
                    return False
        for p in pads:
            b = p['box']
            if b[0] - 4 > vx or b[2] + 4 < vx or b[1] - 4 > vy or b[3] + 4 < vy:
                continue
            if p['net'] == 'GND' and p['type'] != 'np_thru_hole':
                continue
            gap = 0.25 + MARGIN - EPS if p['type'] == 'np_thru_hole' else need
            if new_via and box_dist((vx, vy, vx, vy), b) - r < gap:
                return False
            if layer in p['layers'] and any(seg_box_dist(a, q, b) - W_GND / 2 < gap for a, q in stubs):
                return False
        for s in segs:
            if s['net'] == 'GND':
                continue
            if new_via and seg_seg_dist(s['a'], s['b'], via_at, via_at) - s['r'] - r < need:
                return False
            if s['layer'] in (layer, '*') and any(seg_seg_dist(s['a'], s['b'], a, q) - s['r'] - W_GND / 2 < need
                                                  for a, q in stubs):
                return False
        for z in pours:
            if z['net'] == 'GND':
                continue
            if new_via and box_dist((vx, vy, vx, vy), z['box']) - r < need:
                return False
            if z['layer'] == layer and any(seg_box_dist(a, q, z['box']) - W_GND / 2 < need for a, q in stubs):
                return False
        return True

    def in_gnd_pour(p, side):
        for z in pours:
            if z['net'] == 'GND' and z['layer'] == side and bg.point_in_outline(p['at'], z['outline']):
                if any(bg.point_in_outline(v, z['outline']) for v in gnd_vias):
                    return z['id']
        return None

    # the fixed parts first (place_board.py keeps the movable courtyards off their fan-out, so it does not depend on
    # where the movable parts went), then the rest; each group in reference order
    for ref in sorted(inp.parts, key=lambda r: (r not in first, bg.sort_ref(r))):
        pa = inp.parts[ref]
        done_boxes = []
        for p in sorted(pa.pads, key=lambda q: (bg.sort_ref(q['number']) if q['number'] else ('', -1, ''), q['at'])):
            if p['net'] != 'GND' or p['type'] != 'smd' or not p['number']:
                continue
            layer = pa.side
            pour = in_gnd_pour(p, layer)
            if pour:
                skipped.append({'pad': f'{ref}.{p["number"]}', 'joined_by': pour})
                continue
            if any(bg.rects_overlap(p['box'], b) for b in done_boxes):
                continue  # a pad entry of the same number that overlaps one already fanned out
            cx, cy = p['at']
            hw, hh = (p['box'][2] - p['box'][0]) / 2, (p['box'][3] - p['box'][1]) / 2
            cands = []
            for gap in GND_GAPS:
                for dx, dy in GND_DIRS:
                    n = math.hypot(dx, dy)
                    ux, uy = dx / n, dy / n
                    reach = (abs(ux) * hw + abs(uy) * hh) if (dx == 0 or dy == 0) else max(hw, hh)
                    at = (r4(cx + ux * (reach + gap)), r4(cy + uy * (reach + gap)))
                    cands.append(([(cx, cy), at], at, True))
            for leg in (0.4, 0.9, 1.5, 2.2):
                for dx, dy in GND_DIRS[:4]:
                    reach = abs(dx) * hw + abs(dy) * hh
                    knee = (r4(cx + dx * (reach + leg)), r4(cy + dy * (reach + leg)))
                    for gap in (0.6, 1.0, 1.5, 2.2):
                        for ex, ey in GND_DIRS:
                            if (ex, ey) == (-dx, -dy):
                                continue
                            n = math.hypot(ex, ey)
                            at = (r4(knee[0] + ex / n * gap), r4(knee[1] + ey / n * gap))
                            cands.append(([(cx, cy), knee, at], at, True))
            # last resort: a stub to a GND via that is already there (scripted or fanned out) within 3 mm
            near = sorted((v for v in gnd_vias if math.hypot(v[0] - cx, v[1] - cy) < 3.0),
                          key=lambda v: (math.hypot(v[0] - cx, v[1] - cy), v))
            for v in near:
                cands.append(([(cx, cy), v], v, False))
                for dx, dy in GND_DIRS[:4]:
                    reach = abs(dx) * hw + abs(dy) * hh
                    for leg in (0.4, 0.9):
                        knee = (r4(cx + dx * (reach + leg)), r4(cy + dy * (reach + leg)))
                        cands.append(([(cx, cy), knee, v], v, False))
            chosen = next(((path, at, nv) for path, at, nv in cands if clear(path, at, layer, nv)), None)
            if chosen is None:  # a pad under scripted copper of the other side: a longer stub on its own layer
                for path, at in grid_paths(p, layer, pads, segs, pours, inp.outline):
                    if clear(path, at, layer, True):
                        chosen = (path, at, True)
                        break
            if chosen is None:
                if failed is not None:  # place_board.py repair: report and go on
                    failed.append((ref, p['number']))
                    continue
                raise SystemExit(f'make_board: no GND fan-out via position for {ref}.{p["number"]} at {p["at"]}')
            path, at, new_via = chosen
            vid = f'GND-{ref}-{p["number"]}'
            if any(t['id'] == vid + '-S' for t in out_t):
                vid += f'-{len([t for t in out_t if t["id"].startswith(vid)])}'
            out_t.append({'id': vid + '-S', 'net': 'GND', 'layer': f'{layer}.Cu', 'width_mm': W_GND,
                          'path': [[r4(x), r4(y)] for x, y in path], 'locked': True,
                          'why': f'GND fan-out of {ref}.{p["number"]} to its plane via' if new_via else
                                 f'GND fan-out of {ref}.{p["number"]} to the GND via at {list(at)}'})
            if new_via:
                out_v.append({'id': vid + '-V', 'net': 'GND', 'at': [at[0], at[1]], 'drill_mm': VIA_DRILL,
                              'diameter_mm': VIA_D, 'locked': True, 'why': f'GND plane via of {ref}.{p["number"]}'})
                drills.append((at, VIA_DRILL))
                gnd_vias.append(at)
            for a, b in zip(path, path[1:]):
                segs.append({'net': 'GND', 'layer': layer, 'a': a, 'b': b, 'r': W_GND / 2})
            if new_via:
                segs.append({'net': 'GND', 'layer': '*', 'a': at, 'b': at, 'r': VIA_D / 2})
            done_boxes.append(p['box'])
    return out_t, out_v, skipped


# ------------------------------------------------------------------ heights (pcb/partition-spec.json, as PWR_B make_spec.py)
# Heights read by W2 PCB-PWRA-4 for parts that stand under a PWR-B THT pin field (rule H-TRIM) and have no row in
# pcb/partition-spec.json heights (maximum seated height; the PDFs are fetch-only, not committed).
READ_HEIGHTS = {
    'DMT6007LFG-7': (0.85, 'Diodes DMT6007LFG data sheet DS37335 Rev. 2-2, page 7, PowerDI3333-8 package outline: A max '
                           '0.85 mm; https://www.diodes.com/assets/Datasheets/DMT6007LFG.pdf read 2026-11-12 (curl default '
                           'User-Agent, HTTP 200, sha256 9e75ecab96b0a77b2ff31d61bdf5eba63d6bec5986a29dfc55053e4f253669bc)'),
    'SRP1040VA-4R7M': (4.0, 'Bourns SRP1040VA data sheet, page 1 Product Dimensions: side view 3.8 +- 0.2 mm, so 4.0 mm '
                            'max; https://www.bourns.com/docs/product-datasheets/srp1040va.pdf read 2026-11-12 (curl default '
                            'User-Agent, HTTP 200, sha256 6be1a36f9fafd7e2e3a24578ecee040640f0cee34f7a6c67e6275214bc63bb1c)'),
}


def height_of(inp, ref):
    """(height mm or None, source) from pcb/partition-spec.json heights, then READ_HEIGHTS; harness headers have no read
    height here."""
    g = inp.graph[ref]
    for key, (h, src) in READ_HEIGHTS.items():
        if key in g['value'].split() or bg.parts_by_ref().get(ref, {}).get('mpn') == key:
            return h, f'W2 PCB-PWRA-4 make_board.py READ_HEIGHTS.{key}: {src}'
    fp = g['footprint'].split(':', 1)[1]
    mpn = g['value'].split()
    heights = inp.pspec['heights']
    for key, row in heights['by_mpn'].items():
        if key in mpn or any(m.startswith(key) for m in mpn):
            return row['h'], f'pcb/partition-spec.json heights.by_mpn.{key}: {row["src"]}'
    db = bg.parts_by_ref().get(ref, {})
    if db.get('mpn') in heights['by_mpn']:
        row = heights['by_mpn'][db['mpn']]
        return row['h'], f'pcb/partition-spec.json heights.by_mpn.{db["mpn"]}: {row["src"]}'
    for key, row in heights['by_footprint'].items():
        if fp.startswith(key):
            return row['h'], f'pcb/partition-spec.json heights.by_footprint.{key}: {row["src"]}'
    low = heights['low_profile']
    if any(fp.startswith(p) for p in low['footprint_prefixes']):
        return low['h_max'], f'pcb/partition-spec.json heights.low_profile h_max (class bound of {fp}): {low["src"]}'
    return None, f'not read: no row of pcb/partition-spec.json heights covers {fp} (TBD)'


def heights_block(inp):
    """heights / heights_source for the top parts (the bottom chip heights are not read: TBD, check_boards lists them
    unverified); a part without a source stays out, so check_boards lists it unverified instead of passing it."""
    heights, sources, unread = {}, {}, []
    for ref, pa in sorted(inp.parts.items(), key=lambda kv: bg.sort_ref(kv[0])):
        if pa.side != 'F':
            continue
        h, src = height_of(inp, ref)
        if h is None:
            unread.append(ref)
            continue
        heights[ref], sources[ref] = h, src
    return heights, sources, unread


def height_zones(inp):
    hr = inp.pspec['height_rule']
    margin = inp.pspec['parameters']['window_margin']
    # No 'board' zone: pcb/check_boards.py applies the contract max_component_height (hA 4.5) to a top part that lies
    # inside no zone and max_height_bottom to a bottom part, while a 'board' zone would also cap the parts inside the
    # PWR-B windows at hA (route iteration 1 review: 15 radials and inductors reported against 4.5 mm).
    zones = []
    for cu in inp.study['pwr_b_cutouts']['placed']:
        x0, y0, x1, y1 = cu['rect']
        if cu['kind'] == 'window_taller_than_hA':
            zones.append({'region': [x0, y0, r4(x1 - x0), r4(y1 - y0)], 'max_height_mm': hr['window_ceiling_mm'],
                          'side': 'top', 'checked': True,
                          'why': f'PWR-B window over {cu["ref"]} (placement-study-shrink2.json pwr_b_cutouts): ceiling stack + '
                                 'board_t + hB (pcb/partition-spec.json height_rule window_ceiling_mm)'})
    for f in inp.pwr_b['h_trim']['pin_fields']:
        x0, y0, x1, y1 = f['field_mm']
        zones.append({'region': [r4(x0 - margin), r4(y0 - margin), r4(x1 - x0 + 2 * margin), r4(y1 - y0 + 2 * margin)],
                      'max_height_mm': inp.pspec['keepouts']['h_trim']['zone_h_max_mm'], 'side': 'top', 'checked': True,
                      'why': f'rule H-TRIM: PWR-B THT pin field of {f["ref"]} (pcb/boards/PWR_B.json h_trim) + window_margin; '
                             'PWR-A parts up to zone_h_max_mm stand under it (pcb/partition-spec.json keepouts.h_trim)'})
    return zones


# ------------------------------------------------------------------ project rules
SCRIPTED_CLASSES = {'GND': 'SCRIPTED_GND'}


def scripted_classes(inp, scripted_nets):
    """GND plus every net whose copper is all scripted (W2 PWR-L6-SCRIPT: the converter-stage nets and the 'power' nets of
    script-planned-6l.json): net -> SCRIPTED_<class>, a class with the widths of the net's class that the router never routes."""
    cls = {n: v['class'] for n, v in inp.netclasses['nets'].items()}
    out = dict(SCRIPTED_CLASSES)
    for net in sorted(scripted_nets):
        out[net] = 'SCRIPTED_' + cls.get(net, 'SIG')
    return out


def project_json(inp, nets, scripted=None):
    scripted = scripted or SCRIPTED_CLASSES
    proj = read(ENC_PROJECT)
    proj['meta']['filename'] = 'PWR_A.kicad_pro'
    nc = inp.netclasses
    default = proj['net_settings']['classes'][0]
    pd = nc['project_defaults']['values_mm']
    classes = []
    extra = [(c, nc['classes'][c[len('SCRIPTED_'):]]) for c in sorted(set(scripted.values()) - {'SCRIPTED_GND'})]
    for name, cls in (('Default', nc['classes']['SIG']), ('BATT', nc['classes']['BATT']), ('PWR1A', nc['classes']['PWR1A']),
                      ('PWR2A', nc['classes']['PWR2A']), ('PWR3A', nc['classes']['PWR3A']),
                      ('SCRIPTED_GND', nc['classes']['SIG']), *extra):
        row = copy.deepcopy(default)
        row['name'] = name
        row['track_width'] = cls['outer_min_width_mm']
        row['clearance'] = cls['clearance_mm']
        row['via_diameter'] = VIA_D
        row['via_drill'] = pd['via_hole']
        if name != 'Default':
            row['priority'] = len(classes) - 1
        classes.append(row)
    proj['net_settings']['classes'] = classes
    patterns = [p for p in nc['kicad']['netclass_patterns'] if p['pattern'] in nets and p['pattern'] not in scripted]
    patterns += [{'netclass': cls, 'pattern': net} for net, cls in scripted.items()]
    proj['net_settings']['netclass_patterns'] = sorted(patterns, key=lambda p: p['pattern'])
    rules = proj['board']['design_settings']['rules']
    rules['min_track_width'] = pd['track_width']
    rules['min_clearance'] = pd['clearance']
    rules['min_copper_edge_clearance'] = pd['edge_clearance']
    rules['min_hole_to_hole'] = pd['hole_to_hole']
    # the LT3045 footprint of the KiCad 10.0.7 library drills 0.2 mm thermal vias (as the earlier PWR_A project)
    rules['min_through_hole_diameter'] = 0.2
    return json.dumps(proj, indent=2) + '\n'


# ------------------------------------------------------------------ frozen route (W2 PWRJ-LAYERS6, the PWR_B / CTRL toolkit)
FROZEN6 = HERE / 'route-frozen-6l.json'
FREEZE_ONLY = True  # route run with the frozen copper: Freerouting routes no class (router.freeze_only)


def frozen_guard(inp, tracks, vias):
    """SHA256 of what the frozen copper depends on: every copper pad (ref, pad, net, centre, layers) and the scripted copper
    (pours as locked tracks, GND fan-out; by geometry: the 'why' texts may change without a new harvest)."""
    pads = sorted(f'{ref}.{q["number"]}|{q["net"]}|{q["at"][0]:.4f},{q["at"][1]:.4f}|{",".join(q["layers"])}'
                  for ref, pa in inp.parts.items() for q in pa.pads if q['number'] and q['type'] != 'np_thru_hole')

    def geometry(item):
        return json.dumps({k: v for k, v in item.items() if k != 'why'}, sort_keys=True)
    scripted = [geometry(t) for t in tracks] + [geometry(v) for v in vias]
    return {'pads_sha256': hashlib.sha256('\n'.join(pads).encode()).hexdigest(),
            'scripted_sha256': hashlib.sha256('\n'.join(scripted).encode()).hexdigest()}


def frozen_guard_of_spec():
    """The guard of the current inputs (freeze/freeze6.py writes it into route-frozen-6l.json)."""
    spec, inp, _problems, _nets = build(frozen=False)
    return frozen_guard(inp, spec['pre_route']['tracks'], spec['pre_route']['vias'])


def frozen_copper(inp, tracks, vias):
    """The frozen 6-layer route: the router copper of one route run, harvested and locked (RT-/RV-), plus the grid A*
    completion of its open connections (FIN-/FINV-, freeze/freeze6.py), from route-frozen-6l.json when present. It goes
    in after the scripted copper, which it does not change; the guard stops make_board when a pad or the scripted copper
    changed. Returns (tracks, vias, note, necks, branches)."""
    if not FROZEN6.is_file():
        return [], [], None, [], []
    doc = read(FROZEN6)
    if not doc.get('guard'):
        raise SystemExit(f'make_board: {FROZEN6.name} has no guard (a freeze6.py --no-guard trial): harvest again with the guard')
    have = frozen_guard(inp, tracks, vias)
    for key, value in have.items():
        if doc['guard'].get(key) != value:
            raise SystemExit(f'make_board: {FROZEN6.name} was routed on another {key} ({str(doc["guard"].get(key))[:12]}... != '
                             f'{value[:12]}...): route again with [pcb-route PWR_A] without the frozen copper and harvest anew')
    why = (f'completion of the 6-layer frozen route ({FROZEN6.name}, W2 PWRJ-LAYERS6): grid A* on the locked copper of route '
           f'run {doc["source"]["route_run"]} (build/kicad/boards/PWR_A/freeze/freeze6.py), exact clearance check')
    ft, fv = [], []
    for prefix, key, text in (('RT', 'router_tracks', None), ('FIN', 'completion_tracks', why)):
        for k, (net, layer, width, path) in enumerate(doc[key]):
            t = {'id': f'{prefix}-{k + 1:04d}', 'net': net, 'layer': layer, 'width_mm': width, 'path': path, 'locked': True}
            if text:
                t['why'] = text
            ft.append(t)
    for prefix, key in (('RV', 'router_vias'), ('FINV', 'completion_vias')):
        for k, (net, x, y, d, drill) in enumerate(doc[key]):
            fv.append({'id': f'{prefix}-{k + 1:04d}', 'net': net, 'at': [x, y], 'drill_mm': drill, 'diameter_mm': d, 'locked': True})
    note = (f'W2 PWRJ-LAYERS6: the router copper of route run {doc["source"]["route_run"]} is frozen and locked (RT-/RV- items) '
            'and its open connections are joined by the grid A* completion (FIN-/FINV- items) of '
            'build/kicad/boards/PWR_A/freeze/freeze6.py (numpy, offline; tools copied from build/kicad/boards/PWR_B/freeze). '
            f'Source: build/kicad/boards/PWR_A/{FROZEN6.name}; valid only for this placement, netlist and scripted copper (guard: '
            f'SHA256 of the pads and of the scripted copper). Freezer result: {json.dumps(doc.get("result", {}), sort_keys=True)}')
    return ft, fv, note, list(doc.get('necks', [])), list(doc.get('branches', []))


def branch_rows(branches):
    """branch_exempt rows for the low-current branches of the frozen completion (freeze/fin.py branch_pass): per ref the
    longest branch path (rounded up to 0.5 mm, + 0.5) as max_mm and the narrowest branch width as min_width_mm."""
    out = {}
    for b in branches:
        for ref in b['refs']:
            row = out.setdefault(ref, {'max_mm': 0.0, 'min_width_mm': 9.9, 'links': []})
            row['max_mm'] = max(row['max_mm'], math.ceil(float(b['length_mm']) * 2) / 2 + 0.5)
            row['min_width_mm'] = min(row['min_width_mm'], float(b['width_mm']))
            row['links'].append(f'{b["net"]} {b["width_mm"]} mm x {b["length_mm"]} mm on {"/".join(b["layers"])}')
    return out


def neck_rows(necks):
    """neck_exempt rows for the pad-to-pad necks of the frozen completion (freeze/fin.py neck_link): per ref, the longest
    neck as escape_mm (pcb/check_boards.py: both ends of a narrower piece within escape_mm + half the pad of that ref's pad)."""
    out = {}
    for r in necks:
        row = out.setdefault(r['ref'], {'escape_mm': 0.0, 'links': []})
        row['escape_mm'] = max(row['escape_mm'], float(r['escape_mm']))
        row['links'].append(f'{r["net"]} {r["ref"]}.{r["pad"]}-{r["to"]} {r["width_mm"]} mm x {r["length_mm"]} mm on {r["layer"]}')
    return out


# ------------------------------------------------------------------ planned power copper (W2 PWR-L6-SCRIPT, freeze/plan6.py)
SCRIPT6 = HERE / 'script-planned-6l.json'
# the converter-stage nets that the SC- copper joins whole (checked by net_pieces): scripted, never routed
CONVERTER_NETS = ('E1_SYS12_SW', 'E1_SYS12_CBOOT', 'E1_SYS12_RBOOT', 'E1_SYS12_VCC', 'E1_SYS12_FB', 'E1_SYS12_FF', 'E1_LAB5_FB',
                  'E1_LAB5_RT')


def script_guard(inp, pre):
    """SHA256 of what the planned copper depends on: the pads, the scripted tracks and vias (frozen_guard) and the pours."""
    g = frozen_guard(inp, pre['tracks'], pre['vias'])
    zones = sorted(json.dumps({k: v for k, v in z.items() if k != 'why'}, sort_keys=True) for z in pre['zones'])
    g['zones_sha256'] = hashlib.sha256('\n'.join(zones).encode()).hexdigest()
    return g


def planned_copper(inp, pre):
    """The locked copper of script-planned-6l.json (PL-/PLV- tracks and vias, PE- pin-entry pours) when present; the guard stops
    make_board when a pad or the scripted copper changed. Returns (tracks, vias, zones, branch rows, scripted nets, doc)."""
    if not SCRIPT6.is_file():
        return [], [], [], {}, set(), None
    doc = read(SCRIPT6)
    have = script_guard(inp, pre)
    for key, value in have.items():
        if doc['guard'].get(key) != value:
            raise SystemExit(f'make_board: {SCRIPT6.name} was planned on another {key} ({str(doc["guard"].get(key))[:12]}... != '
                             f'{value[:12]}...): rerun build/kicad/boards/PWR_A/freeze/plan6.py')
    tracks, vias, zones, branches, whole = [], [], [], {}, set()
    entries = {}
    for net, d in sorted(doc['nets'].items()):
        why = (f'W2 PWR-L6-SCRIPT planned {d["class"]} copper of {net} ({SCRIPT6.name}, freeze/plan6.py: grid A* at the 2 oz class '
               f'width {d["width_mm"]} mm on F.Cu/B.Cu, clearance 0.20 mm; kind {d["kind"]})')
        for k, (layer, w, a, b) in enumerate(d['tracks'], 1):
            tracks.append({'id': f'PL-{net}-{k:03d}', 'net': net, 'layer': layer, 'width_mm': w, 'path': [list(a), list(b)],
                           'locked': True, 'why': why})
        for k, (x, y, size, drill) in enumerate(d['vias'], 1):
            vias.append({'id': f'PLV-{net}-{k:02d}', 'net': net, 'at': [x, y], 'drill_mm': drill, 'diameter_mm': size, 'locked': True,
                         'why': why})
        for z in d['zones']:
            outline = rect_union_outline([tuple(r) for r in z['rects']])
            if outline is None:
                raise SystemExit(f'make_board: the pin-entry pour {z["id"]} of {SCRIPT6.name} is not one rectilinear piece')
            entries[z['id']] = {'pad': z['pad'], 'strip_mm': z['strip_mm'], 'landing_mm': z['landing_mm']}
            zones.append({'id': z['id'], 'net': net, 'layer': z['layer'], 'outline': outline, 'priority': 3, 'pad_connection': 'solid',
                          'why': f'W2 PWR-L6-SCRIPT pin-entry pour of {z["pad"]} ({SCRIPT6.name}): the pad, its cross-section at most '
                                 'half the class width beyond it, then a class-width landing for the planned track'})
        for b in d['branches']:
            for ref in b['refs']:
                row = branches.setdefault(ref, {'max_mm': 0.0, 'min_width_mm': 9.9, 'links': []})
                row['max_mm'] = max(row['max_mm'], math.ceil(float(b['length_mm']) * 2) / 2 + 0.5)
                row['min_width_mm'] = min(row['min_width_mm'], float(b['width_mm']))
                row['links'].append(f'{net} {b["width_mm"]} mm x {b["length_mm"]} mm')
        if d['kind'] == 'power':
            whole.add(net)
    doc['pin_entry_pours'] = entries
    return tracks, vias, zones, branches, whole, doc


def net_pieces(inp, pre, net):
    """(pieces, pads not on the largest piece): the pads of a net joined by its scripted copper (tracks, vias, pours by their
    rectangles; inner pours join their vias; a via in a pad joins it), MODEL geometry as scripted_joined."""
    segs = [(tuple(a), tuple(b), t['width_mm'] / 2, t['layer'], None) for t in pre['tracks'] if t['net'] == net
            for a, b in zip(t['path'], t['path'][1:])]
    segs += [(None, None, 0.0, z['layer'], zb) for z in pre['zones'] if z['net'] == net and z['outline'] != 'board'
             for zb in outline_boxes(z['outline'])]
    vias = [(tuple(v['at']), v['diameter_mm'] / 2) for v in pre['vias'] if v['net'] == net]
    pads = [(pa.ref, q) for pa in inp.parts.values() for q in pa.pads if q['net'] == net and q['type'] != 'np_thru_hole']
    parent = list(range(len(segs) + len(vias) + len(pads)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        parent[find(i)] = find(j)
    nv, npad = len(segs), len(segs) + len(vias)
    for i, (a, b, r, lay, zb) in enumerate(segs):
        for j in range(i + 1, len(segs)):
            c, d, r2, lay2, zb2 = segs[j]
            if lay != lay2:
                continue
            if zb and zb2:
                hit = bg.rects_overlap(zb, zb2, EPS)
            elif zb or zb2:
                box, (p, q, rr) = (zb, (c, d, r2)) if zb else (zb2, (a, b, r))
                hit = seg_box_dist(p, q, box) <= rr + EPS
            else:
                hit = seg_seg_dist(a, b, c, d) <= r + r2 + EPS
            if hit:
                union(i, j)
        for k, (c, rv) in enumerate(vias):
            if (box_dist(zb, (c[0], c[1], c[0], c[1])) <= rv + EPS) if zb else seg_seg_dist(a, b, c, c) <= r + rv + EPS:
                union(i, nv + k)
        for k, (_ref, q) in enumerate(pads):
            if lay[0] in q['layers'] and (bg.rects_overlap(zb, q['box'], EPS) if zb else capsule_hits_box(a, b, r + EPS, q['box'])):
                union(i, npad + k)
    for k, (c, _rv) in enumerate(vias):
        for kp, (_ref, q) in enumerate(pads):
            if q['box'][0] - EPS <= c[0] <= q['box'][2] + EPS and q['box'][1] - EPS <= c[1] <= q['box'][3] + EPS:
                union(nv + k, npad + kp)
    for z in pre['zones']:  # an inner pour (or a board plane) joins the vias inside it
        if z['net'] != net or z['layer'] in ('F.Cu', 'B.Cu'):
            continue
        inside = [nv + k for k, (c, _rv) in enumerate(vias) if z['outline'] == 'board' or bg.point_in_outline(c, z['outline'])]
        for k in inside[1:]:
            union(inside[0], k)
    roots = collections.Counter(find(npad + k) for k in range(len(pads)))
    main = roots.most_common(1)[0][0] if roots else None
    return len(roots), sorted(f'{ref}.{q["number"]}' for k, (ref, q) in enumerate(pads) if find(npad + k) != main)


# ------------------------------------------------------------------ the spec
def layers6():
    """The 6-layer plan of W2 PWRJ-LAYERS6."""
    return {
        'copper': 6, 'thickness_mm': 1.6, 'copper_option': COPPER_OPTION,
        'source': ('W2 PWRJ-LAYERS6: 6 layers JLC06161H-2116 1.6 mm (the stackup of PWR_B and the 6-layer CTRL; '
                   'pcb/generated/stackup-6l.json from pcb/stackup.py, jlcpcb.com/impedance read 2026-11-12), ordered with '
                   'finished outer copper 2 oz and inner 0.5 oz (copper_option outer_2oz; jlcpcb.com/impedance, '
                   'capabilities/pcb-capabilities and 6-layer-pcb read 2026-11-13). 1.6 mm is the order thickness; the contract '
                   'gives PWR its own stackup (mechanical/generated/contract/boards.json PWR stackup: t 1.664 MODEL with 2 oz '
                   'outer, order 1.6 +/- 10 %, W2 MECH-8), which the mechanics and the B2B stack row of placement_study use'),
        'plan': {'F.Cu': 'L1: parts (top), signals; BATT/PWR3A pours (scripted, locked tracks) and power routes at the 2 oz widths',
                 'In1.Cu': 'L2: solid GND plane (pre-route zone, layer type power): every SMD GND pad joins it by its scripted via',
                 'In2.Cu': 'L3: signal routes only (no power class: router.class_layers)',
                 'In3.Cu': 'L4: signal routes only (no power class: router.class_layers)',
                 'In4.Cu': ('L5: GND fill (pre-route plane, layer type power) with the scripted E1_CONV_IN strap/bridge pours of '
                            'the LM61460 input at higher priority (the L3 role of the 4-layer plan)'),
                 'B.Cu': ('L6: bottom chips, signals; BATT/PWR3A pours paired with L1; GND bond copper in the four thermal_bond '
                          'zones, solder mask on')},
        'plan_source': 'W2 PWRJ-LAYERS6 (build/kicad/boards/PWR_A/make_board.py layers6); the 4-layer plan was build/15 W2 PCB-RULES',
        'types': {'In1.Cu': 'power', 'In4.Cu': 'power'},
        'types_why': ('S-G-S-S-P-S as PWR_B and the 6-layer CTRL: In1.Cu (L2) a solid GND plane 0.2234 mm under F.Cu and In4.Cu '
                      '(L5) the GND fill 0.2234 mm over B.Cu, both of type power so Freerouting routes no trace on them; In2.Cu '
                      '(L3) and In3.Cu (L4) are the two routing layers the stackup adds, each 0.3 mm from a plane. The power '
                      'classes stay on the 2 oz outer copper (0.5 oz inner copper would need 1.8 mm for PWR1A and does not count '
                      'for PWR3A/BATT, netclasses.json). The 4-layer probes routed power on typed-signal inner layers (sr-rx-pcb '
                      'runs 42424071774, 42424538187), so class_layers keeps them out of In2/In3'),
    }


def build(frozen=True, planned=True):
    spec = mps.build_placement()
    for k in ('probe_left_out', 'probe_post_route_zones_left_out'):
        spec.pop(k, None)
    six_layer_zones(spec['pre_route'])
    study = read(STUDY)
    apply_moves(spec, study)
    inp = Inputs(spec)
    problems = check_placement(inp)
    pre, copper_notes = board_copper(spec['pre_route'], inp)
    pre, script_notes = script_copper(pre)
    problems += script_clearance(inp, pre, {t['id'] for t in SCRIPT_TRACKS} | {v[0] for v in SCRIPT_VIAS} | {z['id'] for z in SCRIPT_ZONES})
    problems += scripted_joined(inp, pre)
    gt, gv, skipped = gnd_fanout(inp, pre, first=fixed_refs(study))
    base = {'tracks': pre['tracks'] + gt, 'vias': pre['vias'] + gv, 'zones': pre['zones']}
    for net in CONVERTER_NETS:
        pieces, apart = net_pieces(inp, base, net)
        if pieces != 1:
            problems.append(f'converter net {net}: the scripted copper leaves {apart} apart')
    pt, pv, pz, pbranch, whole, plan_doc = planned_copper(inp, base) if planned else ([], [], [], {}, set(), None)
    scripted = scripted_classes(inp, set(CONVERTER_NETS) | whole)
    inp.scripted = scripted
    ft, fv, frozen_note, necks, branches = (frozen_copper(inp, base['tracks'] + pt, base['vias'] + pv) if frozen
                                            else ([], [], None, [], []))
    heights, sources, unread = heights_block(inp)
    nets = set(spec['instances']['template_nets'])
    out = {}
    for k, v in spec.items():
        if k == 'status':
            v = 'MODEL_NOT_FOR_FABRICATION'
        elif k == 'title':
            v = 'PWR-A plate-bonded power board, two-sided SHRINK-2 layout (PWR_MAIN + PWR_BRANCH + USB_POWER)'
        elif k == 'note':
            v = ('W2 PCB-PWRA-4: generated by build/kicad/boards/PWR_A/make_board.py (do not hand-edit; rerun it) from the '
                 'SHRINK-2 spec PWR_A.spec-shrink2.json and its placement study (W2 PCB-PWRA-3), with the placement changes '
                 'of make_board.py MOVES, a GND plane via for every SMD GND pad, heights and height zones (hA, PWR-B windows, '
                 'H-TRIM) and the router budget of a board of record. CI/MODEL only: no fabrication release, bench gates OPEN.')
        elif k == 'pre_route':
            v = {'tracks': base['tracks'] + pt + ft, 'vias': base['vias'] + pv + fv, 'zones': base['zones'] + pz}
            if frozen_note:
                v['frozen_route_note'] = frozen_note
        elif k == 'layers':
            v = layers6()
        elif k == 'holes':
            v = {**v, 'keepout_layers': list(COPPER6)}
        elif k == 'fab_floor':
            v = {**v, 'min_track_width': 0.15, 'min_clearance': 0.15,
                 'source': v['source'] + '; W2 PWRJ-LAYERS6: 2 oz outer copper, so track and spacing take the 2 oz multilayer floor '
                           '"Multilayer: 0.15 / 0.15 mm" (jlcpcb.com/capabilities/pcb-capabilities read 2026-11-13)'}
        elif k == 'rules_note':
            v = ('board_gen refuses rules_file until it copies and hashes it, so the net classes and project rules are mirrored in '
                 'PWR_A.kicad_pro: classes SIG (Default) 0.15 and the power classes at their 2 oz outer widths of '
                 'pcb/generated/stackup-6l.json copper_options outer_2oz (PWR1A 0.2, PWR2A 0.4, PWR3A 0.95, BATT 1.6 mm, MODEL), '
                 'clearance 0.15; router vias 0.7/0.3; min through hole 0.2 because the KiCad LT3045 footprint MSOP-12-1EP '
                 'ThermalVias drills 0.2 mm (JLC multilayer floor 0.15)')
        elif k == 'router':
            v = {'tool': 'freerouting', 'max_passes': 100, 'threads': 1, 'job_timeout': '00:32:00', 'timeout_s': 2040,
                 'fanout': False, 'ignore_net_classes': sorted(set(scripted.values())), 'class_layers': CLASS_LAYERS,
                 'why': 'fanout false as on PWR_B: the Freerouting 2.5.0 fan-out pre-pass escaped SMD pins with 0.1124 mm '
                        'stubs (PWR_A probe run 42413833702); GND (class SCRIPTED_GND) is not autorouted: every SMD GND pad '
                        'has a scripted plane via (make_board.py gnd_fanout; placement probe 7, run 43148929963, left 140 GND '
                        'connections open); the budget fits the 45 min board job of sr-rx-pcb with DRC and audits after it'}
        elif k == 'height_zones':
            v = height_zones(inp)
        elif k == 'post_route_zones':
            v = [{**z, 'pad_connection': 'solid',
                  'why': z.get('why', '') + '; solid pad connection (W2 PCB-PWRA-4: route iteration 2, sr-rx-pcb run '
                         '43295500516, starved the thermal spokes of the THT GND pins of J108, J110, J111 and J507 between '
                         'router tracks; as GND-F on PWR_B, the solid THT joints are an assembly gate, OPEN)'}
                 if z['net'] == 'GND' and z['id'].startswith('GND-BOND') else z for z in v]
        out[k] = v
    out['neck_exempt'] = stem_exemptions(inp, out['pre_route']['tracks'], inp.netclasses)
    for ref, row in sorted(neck_rows(necks).items(), key=lambda kv: bg.sort_ref(kv[0])):
        old = out['neck_exempt'].get(ref)
        why = ('W2 PWRJ-LAYERS6: pad-to-pad neck(s) of the frozen-route completion where no class-width path exists (a pin-entry '
               'piece no wider than the narrower pad, at most 3 mm; MODEL, the trace temperature stays a bench gate): '
               + ', '.join(row['links']))
        out['neck_exempt'][ref] = {'escape_mm': r4(max(row['escape_mm'], old['escape_mm'] if old else 0.0)),
                                   'reason': (old['reason'] + '; ' + why) if old else why}
    out['neck_exempt'] = dict(sorted(out['neck_exempt'].items(), key=lambda kv: bg.sort_ref(kv[0])))
    rows = branch_rows(branches)
    exempt = {ref: {**row, 'reason': 'W2 PWR-L6-SCRIPT converter stage (' + SCRIPT_SOURCE.split(',')[0] + '): ' + row['reason']}
              for ref, row in SCRIPT_BRANCHES.items()}
    for ref, row in pbranch.items():
        exempt[ref] = {'max_mm': r4(row['max_mm']), 'min_width_mm': r4(row['min_width_mm']),
                       'reason': ('W2 PWR-L6-SCRIPT planned low-current branch (freeze/plan6.py; exemption policy: a test point, a '
                                  'resistor of 100 ohm or more or a sense or logic pin; MODEL, bench gates OPEN): ' + ', '.join(row['links']))}
    for ref, row in rows.items():
        exempt[ref] = {'max_mm': r4(row['max_mm']), 'min_width_mm': r4(row['min_width_mm']),
                       'reason': ('W2 PWRJ-LAYERS6: low-current branch of a power net from the frozen-route completion (a test point: '
                                  'no current; a capacitor: ripple only, at 0.4 mm on 2 oz outer copper, IPC-2221 about 2 A at +10 degC; '
                                  'a resistor of 100 ohm or more: milliamperes; MODEL, bench gates OPEN): ' + ', '.join(row['links']))}
    if exempt:
        out['branch_exempt'] = dict(sorted(exempt.items(), key=lambda kv: bg.sort_ref(kv[0])))
    out['exemption_policy'] = EXEMPTION_POLICY
    if plan_doc and plan_doc.get('pin_entry_pours'):
        out['pin_entry_pours'] = dict(sorted(plan_doc['pin_entry_pours'].items()))
    zones = inp.contract['thermal_bond_mm']
    conv = {}
    for zi in (3, 4):
        x, y, w, h = zones[zi - 1]
        box = [x, y, x + w, y + h]
        own = sorted({q['net'] for pa in inp.parts.values() for q in pa.pads if q['net']
                      and box[0] <= q['at'][0] <= box[2] and box[1] <= q['at'][1] <= box[3]} | {'GND'})
        conv[str(zi)] = {'rect': box, 'own_nets': own}
    out['converter_zones'] = {
        'zones': conv, 'layers': ['F.Cu', 'In1.Cu'], 'scripted_nets': sorted(n for n in scripted if n != 'GND'),
        'rule': ("W2 PWR-L6-SCRIPT: on F.Cu and In1.Cu over the converter zones 3'/4' (contract thermal_bond zones 3 and 4) only "
                 'the nets with a pad inside the zone (own_nets) carry copper; In1.Cu is the solid GND plane under the converters. '
                 'The scripted nets are not autorouted (scripted classes); freeze/plan6.py keeps the zones as F.Cu keep-outs for the '
                 'other nets, freeze/freeze6.py drops router copper of other nets there; board_audit.py checks it (MODEL)'),
        'source': SCRIPT_SOURCE}
    out['script'] = {'notes': script_notes, 'converter_nets': list(CONVERTER_NETS),
                     'planned_file': (SCRIPT6.relative_to(BASE).as_posix() + ' sha256 ' + bg.sha256_file(SCRIPT6)) if plan_doc else None,
                     'planned_result': plan_doc['result'] if plan_doc else None,
                     'planned_nets': {n: {'kind': d['kind'], 'open': d['open']} for n, d in sorted(plan_doc['nets'].items())}
                     if plan_doc else {},
                     'rule': 'make_board.py script_copper (SC- converter stages, 2 oz rework of the SHRINK-2 stems) and planned_copper '
                             '(PL-/PLV-/PE- from script-planned-6l.json, freeze/plan6.py)'}
    out['edge_keepout'] = {'width_mm': 0.2, 'layers': list(ROUTING6), 'blocks': ['tracks', 'vias'],
                           'why': 'rule-area strips (half-width 0.2) on every outline edge, as PWR_B: the router keeps its '
                                  'copper 0.35 mm off the edge, above the project copper-to-edge 0.3'}
    out['heights'] = heights
    out['heights_source'] = sources
    out['heights_unread'] = {'refs': unread, 'why': 'no read or class height in pcb/partition-spec.json heights (harness '
                             'headers in uncovered edge strips, whose ceilings the contract does not give, and parts not '
                             'read yet): check_boards lists them unverified (TBD)'}
    out['scripted_copper_on_board'] = {'notes': copper_notes,
                                       'rule': 'make_board.py board_copper: F.Cu/B.Cu pours of PWR_A.spec-shrink2.json as locked '
                                               'tracks (ids CU-<pour>); same-net overlapping In2.Cu pours merged'}
    out['gnd_fanout'] = {'vias': len(gv), 'stubs': len(gt), 'pads_joined_by_scripted_gnd_pours': skipped,
                         'rule': 'make_board.py gnd_fanout (port of PWR_B make_spec.py): stub 0.25 mm from the pad centre to '
                                 'a 0.7 / 0.3 via, or to a GND via within 3 mm'}
    out['moves'] = {'placement_file': (PLACEMENT.relative_to(BASE).as_posix() + ' sha256 ' + bg.sha256_file(PLACEMENT))
                    if PLACEMENT.is_file() else None,
                    'moved_refs': len(all_moves(study)),
                    'manual': [{'ref': ref, 'to': [x, y], 'rotation': rot, 'side': side, 'why': why}
                               for ref, (x, y, rot, side, why) in sorted(MOVES.items(), key=lambda kv: bg.sort_ref(kv[0]))]}
    if FREEZE_ONLY and frozen_note:
        out['router']['ignore_net_classes'] = sorted(set(scripted.values()) | {'kicad_default', 'BATT', 'PWR1A', 'PWR2A', 'PWR3A'})
        out['router']['freeze_only'] = 'W2 PWRJ-LAYERS6 freeze-only: with the frozen route in pre_route no class is autorouted (all DSN classes in -inc), so the CI run measures exactly the frozen router copper plus the grid A* completion; in route run 43349395168 Freerouting on top of the frozen copper joined no further connection (model open = KiCad open) and left KiCad clearance errors against the locked copper'
    out['generator'] = 'build/kicad/boards/PWR_A/make_board.py'
    bg.validate_spec(out, BOARD)
    return out, inp, problems, nets


def svg(inp, spec, path):
    S = 7.0
    W, H = 136, 110
    X = lambda x: 20 + x * S  # noqa: E731
    Y = lambda y: 20 + (H - y) * S  # noqa: E731
    P = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S+40}" height="{H*S+40}" font-family="sans-serif">',
         f'<rect width="{W*S+40}" height="{H*S+40}" fill="white"/>',
         '<polygon points="' + ' '.join(f'{X(x)},{Y(y)}' for x, y in inp.outline) + '" fill="#f7f7f7" stroke="black"/>']
    for pa in inp.parts.values():
        x0, y0, x1, y1 = pa.box
        col = '#1565c0' if pa.side == 'F' else '#2e7d32'
        P.append(f'<rect x="{X(x0)}" y="{Y(y1)}" width="{(x1-x0)*S}" height="{(y1-y0)*S}" fill="none" stroke="{col}"/>')
        for p in pa.pads:
            b = p['box']
            P.append(f'<rect x="{X(b[0])}" y="{Y(b[3])}" width="{(b[2]-b[0])*S}" height="{(b[3]-b[1])*S}" fill="#b0bec5"/>')
    for t in spec['pre_route']['tracks']:
        pts = ' '.join(f'{X(x)},{Y(y)}' for x, y in t['path'])
        P.append(f'<polyline points="{pts}" fill="none" stroke="#c62828" stroke-width="{t["width_mm"]*S}"/>')
    for v in spec['pre_route']['vias']:
        P.append(f'<circle cx="{X(v["at"][0])}" cy="{Y(v["at"][1])}" r="{v["diameter_mm"]/2*S}" fill="#6a1b9a"/>')
    P.append('</svg>')
    Path(path).write_text('\n'.join(P), encoding='utf-8')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--install', action='store_true')
    ap.add_argument('--svg')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    spec, inp, problems, nets = build()
    for p in problems:
        print('problem:', p)
    if problems:
        return 1
    text = json.dumps(spec, ensure_ascii=False, indent=2) + '\n'
    proj = project_json(inp, nets, inp.scripted)
    if args.svg:
        svg(inp, spec, args.svg)
    status = 0
    targets = [(SPEC_OUT, text), (PROJECT, proj)]
    if args.install or (args.check and SPEC.is_file()):
        targets.append((SPEC, text))
    for path, data in targets:
        name = path.relative_to(BASE).as_posix()
        if args.check:
            if not path.is_file() or path.read_text(encoding='utf-8') != data:
                print(f'{name} is stale: rerun build/kicad/boards/PWR_A/make_board.py')
                status = 1
            else:
                print(f'{name} reproduces')
        else:
            bg.atomic_write(path, data)
            print(f'wrote {name}')
    print(f'{len(spec["parts"])} parts, {len(spec["pre_route"]["tracks"])} tracks, {len(spec["pre_route"]["vias"])} vias '
          f'({spec["gnd_fanout"]["vias"]} GND fan-out vias, {spec["gnd_fanout"]["stubs"]} stubs), '
          f'{len(spec["heights"])} heights, {len(spec["height_zones"])} height zones')
    return status


if __name__ == '__main__':
    sys.exit(main())
