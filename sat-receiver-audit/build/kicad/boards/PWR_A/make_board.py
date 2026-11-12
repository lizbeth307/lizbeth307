#!/usr/bin/env python3
"""PWR-A board spec for routing (W2 PCB-PWRA-4), standard library.

  python3 build/kicad/boards/PWR_A/make_board.py            write pcb/boards/PWR_A.json and PWR_A.kicad_pro
  python3 build/kicad/boards/PWR_A/make_board.py --check    fail unless both reproduce
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
  * the router budget of a board of record.
Every value is a CI/MODEL input: no fabrication release, bench gates stay OPEN.
"""
from __future__ import annotations

import argparse
import copy
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
SPEC = BASE / 'pcb/boards/PWR_A.json'
PROJECT = HERE / 'PWR_A.kicad_pro'
ENC_PROJECT = BASE / 'build/kicad/boards/ENC/ENC.kicad_pro'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
PSPEC = BASE / 'pcb/partition-spec.json'
PWR_B_SPEC = BASE / 'pcb/boards/PWR_B.json'
STUDY = HERE / 'placement-study-shrink2.json'
CONTRACT = BASE / 'mechanical/generated/contract/boards.json'

CLEAR = 0.15          # project clearance (netclasses.json project_defaults)
MARGIN = 0.05         # design margin of the scripted copper over the clearance
EDGE = 0.3            # project copper-to-edge clearance
VIA_D, VIA_DRILL = 0.7, 0.3   # as PWR_B: router vias at clearance 0.15 keep the 0.5 mm hole-to-hole rule
HOLE_GAP = 0.55       # drill edge to drill edge, the 0.5 mm hole-to-hole rule plus margin
W_GND = 0.25          # GND fan-out stub width (as PWR_B)
EPS = 1e-6            # mm, rounding tolerance of the clearance tests (a stub as wide as its pad keeps the pad's own gap)

# Placement changes of W2 PCB-PWRA-4 (design choices; ref -> (x, y, rotation, side, reason)). Empty in route iteration 1:
# the board is placed exactly as placement-study-shrink2.json.
MOVES: dict = {}


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
        quarter = int(round(rot / 90.0)) % 2
        self.pads = []
        for p in geo['pads']:
            cx, cy = self.map(p['at'])
            w, h = p['size'][::-1] if quarter else p['size']
            self.pads.append({'number': str(p['number']), 'type': p['type'], 'at': (cx, cy),
                              'box': (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2),
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
class Inputs:
    def __init__(self, base_spec):
        self.spec = base_spec
        self.graph = bg.load_graph()
        self.manifest = bg.read_json(bg.MANIFEST)
        self.netclasses = read(NETCLASSES)
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
            # copper pads only (paste apertures without a number are no copper; NPTH holes stay as holes)
            keep = [p for p, cu in zip(geo['pads'], pad_copper(text)) if cu or p['type'] == 'np_thru_hole']
            self.geo[t['ref']] = {**geo, 'pads': keep}
        self.parts = {t['ref']: Placed(t['ref'], self.geo[t['ref']], t['anchor'], t['pads']) for t in self.template}


def pad_copper(text):
    """For each pad of a .kicad_mod (footprint_geometry order): True if it has a copper layer."""
    out = []
    for node in bg.sexpr(text)[1:]:
        if isinstance(node, list) and node and node[0] == 'pad':
            layers = next((n[1:] for n in node if isinstance(n, list) and n and n[0] == 'layers'), [])
            out.append(any(str(x).endswith('.Cu') for x in layers))
    return out


# ------------------------------------------------------------------ placement
def cutout_refs(study):
    return {c['ref'] for c in study['pwr_b_cutouts']['placed']}


def apply_moves(spec, study):
    """MOVES onto the probe anchors; a part with a PWR-B cut-out never moves (fixed point with PCB-PWRB-2)."""
    fixed = cutout_refs(study)
    outline = [tuple(p) for p in read(CONTRACT)['boards'][spec['contract']['board']]['outline_mm']]
    by_ref = {p['ref']: p for p in spec['parts']}
    for ref, (x, y, rot, side, why) in sorted(MOVES.items(), key=lambda kv: bg.sort_ref(kv[0])):
        if ref in fixed:
            raise SystemExit(f'make_board: {ref} has a PWR-B cut-out (placement-study-shrink2.json pwr_b_cutouts) and '
                             'cannot move without a PCB-PWRB re-placement')
        p = by_ref[ref]
        p['anchor'] = {'at': [r4(x), r4(y)], 'align': 'origin', 'rotation': float(rot), 'side': side}
        p['anchor_source'] = f'W2 PCB-PWRA-4 make_board.py MOVES: {why}'
    # legends of moved parts near the edge (make_probe_spec.edge_text rule)
    graph, manifest = bg.load_graph(), bg.read_json(bg.MANIFEST)
    template = {t['ref']: t for t in bg.resolve({**spec, 'groups': []}, graph, manifest)}
    for ref in MOVES:
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
        pours.append({'net': z['net'], 'layer': layer, 'box': poly_box(z['outline']), 'outline': [tuple(p) for p in z['outline']],
                      'id': z['id']})
    return segs, pours


# ------------------------------------------------------------------ GND fan-out (port of PWR_B make_spec.py gnd_fanout)
GND_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
GND_GAPS = (0.55, 0.9, 1.3, 1.8)


GRID = 0.1       # mm, raster of the long-stub search
REACH = 4.5      # mm, half window of the long-stub search around the pad


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


def gnd_fanout(inp, pre):
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

    for ref in sorted(inp.parts, key=bg.sort_ref):
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
def height_of(inp, ref):
    """(height mm or None, source) from pcb/partition-spec.json heights; harness headers have no read height here."""
    g = inp.graph[ref]
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
    zones = [{'region': 'board', 'max_height_mm_from_contract': 'max_component_height', 'side': 'top', 'checked': True,
              'why': 'hA 4.5 (pcb/partition-spec.json parameters.hA): top parts outside the PWR-B windows'},
             {'region': 'board', 'max_height_mm': inp.contract['bottom_side']['h_max'], 'side': 'bottom', 'checked': True,
              'why': 'bottom chip parts in the plate pockets: contract bottom_side h_max (MECH-7: shim gap 0.4 + pocket '
                     'depth 1.0 - polyimide 0.07 - clearance 0.3)'}]
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


def project_json(inp, nets):
    proj = read(ENC_PROJECT)
    proj['meta']['filename'] = 'PWR_A.kicad_pro'
    nc = inp.netclasses
    default = proj['net_settings']['classes'][0]
    pd = nc['project_defaults']['values_mm']
    classes = []
    for name, cls in (('Default', nc['classes']['SIG']), ('BATT', nc['classes']['BATT']), ('PWR1A', nc['classes']['PWR1A']),
                      ('PWR2A', nc['classes']['PWR2A']), ('PWR3A', nc['classes']['PWR3A']),
                      ('SCRIPTED_GND', nc['classes']['SIG'])):
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
    patterns = [p for p in nc['kicad']['netclass_patterns'] if p['pattern'] in nets and p['pattern'] not in SCRIPTED_CLASSES]
    patterns += [{'netclass': cls, 'pattern': net} for net, cls in SCRIPTED_CLASSES.items()]
    proj['net_settings']['netclass_patterns'] = sorted(patterns, key=lambda p: p['pattern'])
    rules = proj['board']['design_settings']['rules']
    rules['min_track_width'] = pd['track_width']
    rules['min_clearance'] = pd['clearance']
    rules['min_copper_edge_clearance'] = pd['edge_clearance']
    rules['min_hole_to_hole'] = pd['hole_to_hole']
    # the LT3045 footprint of the KiCad 10.0.7 library drills 0.2 mm thermal vias (as the earlier PWR_A project)
    rules['min_through_hole_diameter'] = 0.2
    return json.dumps(proj, indent=2) + '\n'


# ------------------------------------------------------------------ the spec
def build():
    spec = mps.build_placement()
    for k in ('probe_left_out', 'probe_post_route_zones_left_out'):
        spec.pop(k, None)
    study = read(STUDY)
    apply_moves(spec, study)
    inp = Inputs(spec)
    problems = check_placement(inp)
    pre = spec['pre_route']
    gt, gv, skipped = gnd_fanout(inp, pre)
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
            v = {'tracks': pre['tracks'] + gt, 'vias': pre['vias'] + gv, 'zones': pre['zones']}
        elif k == 'router':
            v = {'tool': 'freerouting', 'max_passes': 100, 'threads': 1, 'job_timeout': '00:32:00', 'timeout_s': 2040,
                 'fanout': False, 'ignore_net_classes': sorted(set(SCRIPTED_CLASSES.values())),
                 'why': 'fanout false as on PWR_B: the Freerouting 2.5.0 fan-out pre-pass escaped SMD pins with 0.1124 mm '
                        'stubs (PWR_A probe run 42413833702); GND (class SCRIPTED_GND) is not autorouted: every SMD GND pad '
                        'has a scripted plane via (make_board.py gnd_fanout; placement probe 7, run 43148929963, left 140 GND '
                        'connections open); the budget fits the 45 min board job of sr-rx-pcb with DRC and audits after it'}
        elif k == 'height_zones':
            v = height_zones(inp)
        out[k] = v
    out['edge_keepout'] = {'width_mm': 0.2, 'layers': ['F.Cu', 'B.Cu'], 'blocks': ['tracks', 'vias'],
                           'why': 'rule-area strips (half-width 0.2) on every outline edge, as PWR_B: the router keeps its '
                                  'copper 0.35 mm off the edge, above the project copper-to-edge 0.3'}
    out['heights'] = heights
    out['heights_source'] = sources
    out['heights_unread'] = {'refs': unread, 'why': 'no read or class height in pcb/partition-spec.json heights (harness '
                             'headers in uncovered edge strips, whose ceilings the contract does not give, and parts not '
                             'read yet): check_boards lists them unverified (TBD)'}
    out['gnd_fanout'] = {'vias': len(gv), 'stubs': len(gt), 'pads_joined_by_scripted_gnd_pours': skipped,
                         'rule': 'make_board.py gnd_fanout (port of PWR_B make_spec.py): stub 0.25 mm from the pad centre to '
                                 'a 0.7 / 0.3 via, or to a GND via within 3 mm'}
    out['moves'] = [{'ref': ref, 'to': [x, y], 'rotation': rot, 'side': side, 'why': why}
                    for ref, (x, y, rot, side, why) in sorted(MOVES.items(), key=lambda kv: bg.sort_ref(kv[0]))]
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
    ap.add_argument('--svg')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    spec, inp, problems, nets = build()
    for p in problems:
        print('problem:', p)
    if problems:
        return 1
    text = json.dumps(spec, ensure_ascii=False, indent=2) + '\n'
    proj = project_json(inp, nets)
    if args.svg:
        svg(inp, spec, args.svg)
    status = 0
    for path, data in ((SPEC, text), (PROJECT, proj)):
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
