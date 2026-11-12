#!/usr/bin/env python3
"""Board spec generator of the CTRL board (W2 PCB-CTRL). Standard library only.

Run from any directory:
  python build/kicad/boards/CTRL/make_spec.py           rewrite pcb/boards/CTRL.json and build/kicad/boards/CTRL/CTRL.kicad_pro
  python build/kicad/boards/CTRL/make_spec.py --check   regenerate in memory and compare with the committed files

The base is the committed pcb/boards/CTRL.json itself (parts, instances, holes, groups, heights, sides, cable exits);
this script owns the keys it rewrites and recomputes them every run, so a second run changes nothing:
  * the anchors of the fan cluster, the blower switch, J313, D304 and the R4B encoder resistor block (ANCHORS), and the
    placement groups it replaces (FAN, FAN2, BLOWER, R4B; FAN3 keeps three resistors);
  * the scripted, locked copper (pre_route): the LAB5 feed and its branches, the E3_BLOWER_GND return and its capacitor
    branches, E3_FAN5, the 3V3_Q6A pieces, the E3_PICO3V3 pieces, the encoder lines of the R4B block, GND copper over
    the custom Pico GND pads and one plane via per SMD GND pad (deterministic search on the exact pad shapes);
  * branch_exempt, neck_exempt, edge_keepout, router, height_zones (from the current contract), the layer plan and
    the texts that describe them, the D304 height and its source, the BZ301 height source and anchor_source, and the
    J304/J313 heights_open entries;
  * the net classes and patterns of build/kicad/boards/CTRL/CTRL.kicad_pro.
Pad shapes come from the vendored footprints (build/kicad/footprints/manifest.json), the custom Pico GND pads from
build/kicad/footprints/SR_RX_Custom.pretty/RaspberryPi_Pico_SMD_SWD.kicad_mod, placed like pcb/board_gen.py place()
(KiCad rotation, then the left-right flip of side B). Before writing, every scripted track and via is checked
against other-net pads, scripted copper, board and cut-out edges, hole keepouts and footprint keepouts.
The routed board, its report and the fab set are CI outputs (sr-rx-pcb route run of a commit whose subject carries
'[pcb-route CTRL]', applied as 'GENERATED:'). CI/model input only: no fabrication release; bench gates stay OPEN.
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys

BASE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(BASE / 'pcb'))
import board_gen as bg  # noqa: E402  (standard library)
import check_boards as cb  # noqa: E402  (standard library)

BOARD = 'CTRL'
SPEC = BASE / 'pcb/boards/CTRL.json'
PROJECT = BASE / 'build/kicad/boards/CTRL/CTRL.kicad_pro'
VIA_D, VIA_DRILL, STUB_W = 0.65, 0.3, 0.25   # scripted GND vias and stubs
CLR = 0.2          # design clearance of scripted copper to other-net copper (board rule 0.15)
EDGE = 0.35        # scripted copper to board and cut-out edges (rule 0.3)
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']  # 6 layers, JLC06161H-2116 (W2 CTRL-R layer study, W2 CTRL-4)
ROUTING = ['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu']  # In1.Cu: solid GND plane, In4.Cu: solid 3V3_Q6A plane (both type power)


# ------------------------------------------------------------------ footprint pads placed like board_gen.place()
class Geometry:
    """Library pads and keepout zones of the vendored footprints, placed by an anchor into board mm (y up)."""

    def __init__(self, graph):
        self.graph = graph
        self.libs = {}

    def lib(self, path):
        key = str(path)
        if key not in self.libs:
            text = Path(path).read_text(encoding='utf-8')
            tree = cb.parse(text)
            pads, zones = [], []
            for pad in cb.kids(tree, 'pad'):
                at = cb.kid(pad, 'at')
                size = cb.kid(pad, 'size')
                drill = cb.kid(pad, 'drill')
                dvals = [float(v) for v in cb.atoms(drill) if re.fullmatch(r'-?[0-9.]+', str(v))] if drill else []
                lay = cb.kid(pad, 'layers')
                layers = [str(x) for x in lay[1:]] if lay else []
                pads.append({'number': str(pad[1]), 'kind': str(pad[2]), 'shape': str(pad[3]),
                             'at': (float(at[1]), float(at[2])), 'a': float(at[3]) if len(at) > 3 else 0.0,
                             'w': float(size[1]), 'h': float(size[2]) if len(size) > 2 else float(size[1]),
                             'drill': dvals, 'layers': layers, 'node': pad})
            for z in cb.kids(tree, 'zone'):
                lay = cb.kid(z, 'layers') or cb.kid(z, 'layer')
                layers = [str(x) for x in lay[1:]]
                poly = cb.kid(z, 'polygon')
                pts = [(float(p[1]), float(p[2])) for p in cb.kid(poly, 'pts')[1:] if isinstance(p, list) and p[0] == 'xy']
                zones.append({'layers': layers, 'pts': pts, 'keepout': cb.kid(z, 'keepout') is not None})
            self.libs[key] = {'pads': pads, 'zones': zones, 'text': text}
        return self.libs[key]

    @staticmethod
    def copper_layers(names, side):
        out = []
        for n in names:
            if n in ('*.Cu', 'F&B.Cu'):
                out += LAYERS if n == '*.Cu' else ['F.Cu', 'B.Cu']
            elif n == 'F.Cu':
                out.append('B.Cu' if side == 'B' else 'F.Cu')
            elif n == 'B.Cu':
                out.append('F.Cu' if side == 'B' else 'B.Cu')
            elif n.endswith('.Cu'):
                out.append(n)
        return list(dict.fromkeys(out))

    @staticmethod
    def place_pt(pt, anchor):
        """Footprint-local point (KiCad, y down) -> board mm (y up) for an origin-aligned anchor."""
        x, y = bg.turn_point(pt, float(anchor.get('rotation', 0)))
        if anchor.get('side', 'F') == 'B':
            x = -x
        bx, by = (float(v) for v in anchor['at'])
        return (bx + x, by - y)

    def pad_shape(self, p, anchor):
        """check_boards shape of a library pad placed by anchor (board mm, y up) and its centre."""
        c = self.place_pt(p['at'], anchor)
        if p['shape'] == 'custom':
            return self.custom_shape(p, anchor), c
        rot = float(anchor.get('rotation', 0))
        ang = p['a'] + rot  # absolute angle before the flip

        def corner(dx, dy):
            x, y = cb.rot(dx, dy, ang)
            if anchor.get('side', 'F') == 'B':
                x = -x
            return (c[0] + x, c[1] - y)
        w, h = p['w'], p['h']
        if p['shape'] == 'circle':
            return cb.Capsule(c[0], c[1], c[0], c[1], w / 2), c
        if p['shape'] == 'oval':
            ax = (w / 2 - h / 2, 0.0) if w >= h else (0.0, h / 2 - w / 2)
            a1, a2 = corner(-ax[0], -ax[1]), corner(ax[0], ax[1])
            return cb.Capsule(a1[0], a1[1], a2[0], a2[1], min(w, h) / 2), c
        pts = [corner(sx * w / 2, sy * h / 2) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        return cb.Poly(pts), c

    def custom_shape(self, p, anchor):
        """A custom pad (the castellated Pico pins): its anchor plus the filled primitives, the way
        pcb/check_boards.py Board._custom_pad models it on a routed board, here from the footprint file."""
        def T(px, py):
            qx, qy = cb.rot(float(px), float(py), p['a'])
            return self.place_pt((p['at'][0] + qx, p['at'][1] + qy), anchor)
        node = p['node']
        opts = cb.kid(node, 'options')
        w, h = p['w'], p['h']
        if opts is not None and cb.kid(opts, 'anchor') is not None and str(cb.kid(opts, 'anchor')[1]) == 'circle':
            cx, cy = T(0.0, 0.0)
            shapes = [cb.Capsule(cx, cy, cx, cy, w / 2)]
        else:
            shapes = [cb.Poly([T(sx * w / 2, sy * h / 2) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])]
        prims = cb.kid(node, 'primitives')
        for g in (prims[1:] if prims else []):
            if not isinstance(g, list) or not g:
                continue
            head = str(g[0])
            width = cb.num(cb.kid(g, 'stroke') or g, 'width', default=0.0) or 0.0
            if head == 'gr_poly':
                q = cb.kid(g, 'pts')
                pts = [T(v[1], v[2]) for v in q[1:] if isinstance(v, list) and v and v[0] == 'xy'] if q else []
                if len(pts) >= 3:
                    shapes.append(cb.Poly(pts))
            elif head == 'gr_circle':
                c0, e0 = cb.kid(g, 'center'), cb.kid(g, 'end')
                r = math.hypot(float(e0[1]) - float(c0[1]), float(e0[2]) - float(c0[2]))
                cx, cy = T(c0[1], c0[2])
                shapes.append(cb.Capsule(cx, cy, cx, cy, r + width / 2))
            elif head == 'gr_line':
                s0, e0 = cb.kid(g, 'start'), cb.kid(g, 'end')
                (ax, ay), (bx, by) = T(s0[1], s0[2]), T(e0[1], e0[2])
                shapes.append(cb.Capsule(ax, ay, bx, by, width / 2))
            else:
                raise SystemExit(f'make_spec: custom pad primitive {head} is not modelled')
        return cb.Multi(shapes) if len(shapes) > 1 else shapes[0]

    def placed(self, ref, part, anchor):
        """All copper pads of a placed template part and its copper keepout zones."""
        L = self.lib(bg.footprint_file(part))
        pin_net = {str(p['number']): (None if p.get('nc') else p.get('net')) for p in self.graph[ref]['pins']}
        out = []
        side = anchor.get('side', 'F')
        for p in L['pads']:
            layers = self.copper_layers(p['layers'], side)
            if not layers and p['kind'] != 'np_thru_hole':
                continue  # paste-only aperture
            shape, c = self.pad_shape(p, anchor)
            out.append({'ref': ref, 'number': p['number'], 'net': pin_net.get(p['number']) if p['number'] else None,
                        'layers': layers if p['kind'] != 'np_thru_hole' else list(LAYERS),
                        'shape': shape, 'c': c, 'kind': p['kind'], 'drill': p['drill'], 'size': (p['w'], p['h']),
                        'lib': p})
        zones = []
        for z in L['zones']:
            if z['keepout']:
                zones.append({'ref': ref, 'layers': self.copper_layers(z['layers'], side),
                              'poly': cb.Poly([self.place_pt(q, anchor) for q in z['pts']])})
        return out, zones


# ------------------------------------------------------------------ placement of the spec
def anchor(at, rot, side='B'):
    return {'at': [round(at[0], 4), round(at[1], 4)], 'align': 'origin', 'rotation': rot, 'side': side}


FAN_NOTE = ('fan switch cluster on the bottom right strip, x 37-50 y 75-93.4 (W2 PCB-CTRL iteration 2): Q304 pin 3 faces the '
            'PTC F301 so the scripted E3_FAN5 copper is one 1.85 mm segment; F301.2 next to J313.2; the lime band '
            '(y >= 83, 4.98 mm) holds SMD parts only')
BLOWER_NOTE = ('blower switch on the bottom band y 54.5-58.1 between the Pico and the J317 pin row (W2 PCB-CTRL iteration 2): '
               'the scripted E3_BLOWER_GND rail J314.1 -> D306.2 -> Q305.3 runs at y 59.25, below the J317 pins (y >= 60.8) '
               'and above D306.1 (LAB5)')
ANCHORS = {
    'J313': (anchor((40.43, 75.7), 90), 'bottom, vertical KK over the plate zones x 37-46 y 68.5-83 (15.98 / 17.98 mm); '
             'courtyard y 73.93-82.55, below the lime band (y >= 83, 4.98 mm); its pin field + 1.0 mm (x <= 42.53) stays clear '
             'of the top TR3B parts; next to the fan switch'),
    'D304': (anchor((48.04, 68.81), 0), 'bottom over the zones x 43.5-50 y 65.6-72 (15.98 / 17.98 mm >= 9.6 mm LED, worst '
             'case of the 8.6 mm body plus up to 1.0 mm past the flange), between J304 (y <= 65.51) and J313; its pins + 1.0 mm '
             'stay clear of the top parts'),
    'F301': (anchor((48.0, 79.4), 270), FAN_NOTE),
    'Q304': (anchor((48.0, 84.3), 270), FAN_NOTE),
    'C320': (anchor((41.95, 88.1), 270), FAN_NOTE + '; W2 CTRL-4: C320 turned upright left of the LAB5 feed column (x 43.85), '
             'C320.1 on top under the 1.85 mm feed at y 88.9, so the feed reaches Q304.2 down the right edge'),
    'R367': (anchor((45.5, 85.5), 90), FAN_NOTE + '; W2 CTRL-4: 0.1 mm right of its W2 PCB-CTRL place, clear of the LAB5 feed column'),
    'Q303': (anchor((41.0, 84.6), 180), FAN_NOTE + '; W2 CTRL-4: 1.0 mm left and 0.4 mm down from its W2 PCB-CTRL place, clear of the '
             'LAB5 feed column and the C320 courtyard'),
    'C322': (anchor((26.6, 96.6), 270), 'W2 CTRL-4: second input capacitor of the GNSS switch U315, taken out of group R4A and '
             'placed upright right of U315 with C322.1 on top under the 1.85 mm LAB5 feed at y 98.1; C322.2 joins U315.2 (GND)'),
    'R365': (anchor((38.3, 85.0), 90), FAN_NOTE + '; W2 CTRL-4: 0.2 mm left, clear of the Q303 courtyard'),
    'R366': (anchor((38.6, 88.0), 0), FAN_NOTE),
    'C318': (anchor((47.6, 74.6), 0), FAN_NOTE),
    'D305': (anchor((40.6, 91.6), 0), FAN_NOTE),
    'C319': (anchor((46.5, 91.6), 0), FAN_NOTE),
    'D306': (anchor((14.5, 56.3), 0), BLOWER_NOTE),
    'Q305': (anchor((20.23, 56.4), 0), BLOWER_NOTE),
}
GROUP_DROP = {'R4A': ('C322',)}  # group id -> refs taken out of the group and anchored in ANCHORS (W2 CTRL-4)
U315_SOURCE = 'bottom strip between the cut-outs, above cut-out 1 (GNSS 5 V switch next to its capacitors)'
BZ301_SOURCE = ('bottom, y 55-68 below cut-out 1 (courtyard x 22.7-35.8, y 54.98-68.03): over the bms zone (x 0-34, y 0-57; '
                'fits_mm 7.48, free_mm 7.98) and the plate.main, hdmi_route_front_run, hdmi_route_front_turn and '
                'hdmi_route_front_flat zones (17.98 / 16.88 / 15.98 / 16.48 mm); the body is 7.0 mm with a +-0.5 mm drawing '
                'tolerance (Same Sky CPT-1207-3TH rev 1.01 p.2), so its 7.5 mm worst case is 0.02 mm above bms fits_mm 7.48 '
                'and below free_mm 7.98: OPEN for MECH (W2 CTRL-R, review CTRL-8); it cannot move up, cut-out 1 starts at y 68.5')


def edit_placement(spec):
    for p in spec['parts']:
        if p['ref'] in ANCHORS:
            p['anchor'], p['anchor_source'] = copy.deepcopy(ANCHORS[p['ref']][0]), ANCHORS[p['ref']][1]
        if p['ref'] == 'U315':
            p['anchor_source'] = U315_SOURCE
        if p['ref'] == 'BZ301':
            p['anchor_source'] = BZ301_SOURCE
    groups = []
    for g in spec['groups']:
        if g['id'] in ('FAN', 'FAN2', 'BLOWER'):
            continue
        if g['id'] == 'FAN3':
            g['region'] = [37.05, 68.6, 43.4, 73.9]
            g['members'] = [m for m in g['members'] if m['ref'] != 'R366']
        if g['id'] in GROUP_DROP:
            g['members'] = [m for m in g['members'] if m['ref'] not in GROUP_DROP[g['id']]]
        if g['id'] in PULLUP_ROWS:
            row = PULLUP_ROWS[g['id']]
            g['region'] = list(row['region'])
            if 'gap_mm' in row:
                g['gap_mm'] = row['gap_mm']
            for m in g['members']:
                if m['ref'] in row['turned']:
                    m['rotation'] = 270
        groups.append(g)
    spec['groups'] = groups


# Rows of vertical 0603 resistors whose pad-2 row faces a cut-out edge (W2 PCB-CTRL review CTRL-1, route run
# 43121860459): the pull-up pads (E3_PICO3V3) alternated with series-resistor pads of other nets in the row next to the
# edge, so neither could leave the row. The series resistors are turned 180 degrees (their pin towards the MCU
# moves to the lower row, their pin towards the connector, shared with the pull-up, to the upper row and is joined
# to the pull-up by a short diagonal in the 0.85 mm gap between the rows), and the row moves down so that a scripted
# E3_PICO3V3 bus runs between the upper pads and the cut-out edge.
PULLUP_ROWS = {
    # bottom side under cut-out 2: C314-C317, then pull-up / series pairs of the four encoder lines
    'R4B': {'region': [20.8, 104.6, 43.9, 108.86], 'turned': ('R352', 'R354', 'R356', 'R358')},
    # top side under cut-out 1: R346 (LOCK), then the pairs of ENC1_PRESS and ENC2_PRESS in one row (gap 0.2 mm)
    'HMI3': {'region': [31.7, 58.6, 39.9, 67.955], 'gap_mm': 0.2, 'turned': ('R348', 'R350')},
    # top side column beside J317: R344 turned so that its E3_FN pin sits next to the E3_FN pin of R343
    'HMI2': {'region': [23.8, 58.6, 26.8, 68.4], 'turned': ('R344',)},
}


class Inputs:
    def __init__(self, spec):
        bg.validate_spec(spec, BOARD)
        self.contract_all, self.stackup = bg.load_contract(spec)
        self.graph = bg.load_graph()
        self.template = bg.resolve(spec, self.graph, bg.read_json(bg.MANIFEST))
        ga, self.rows = bg.group_plan(spec, self.contract_all, self.template)
        self.anchors = {p['ref']: (p['anchor'] or ga[p['ref']]) for p in self.template}
        self.tpl = {p['ref']: p for p in self.template}
        self.contract = bg.read_json(BASE / 'mechanical/generated/contract/boards.json')['boards'][BOARD]
        self.geo = Geometry(self.graph)
        self.pads, self.keepouts = [], []
        for part in self.template:
            pads, zones = self.geo.placed(part['ref'], part, self.anchors[part['ref']])
            self.pads.extend(pads)
            self.keepouts.extend(zones)
        self.outline = self.contract['outline_mm']
        self.cuts = bg.cutout_boxes(self.contract)
        self.holes = [(float(x), float(y)) for x, y in self.contract['holes_mm']]


def samples(a, b, step=0.05):
    n = max(1, int(math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / step)))
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


class Copper:
    """Scripted copper with the clearance check of every track and via against what is already there."""

    def __init__(self, inp, log):
        self.inp, self.log = inp, log
        self.tracks, self.vias = [], []

    def edge_dist(self, pt):
        best = math.inf
        loops = [self.inp.outline] + [[(a, b), (c, b), (c, d), (a, d)] for a, b, c, d in self.inp.cuts]
        for loop in loops:
            for (x1, y1), (x2, y2) in zip(loop, loop[1:] + loop[:1]):
                best = min(best, cb.seg_dist(pt[0], pt[1], x1, y1, x2, y2))
        return best

    def inside_board(self, pt):
        return bg.point_in_outline(pt, self.inp.outline) and not any(
            a < pt[0] < c and b < pt[1] < d for a, b, c, d in self.inp.cuts)

    def track_clear(self, layer, width, path, net, clr=CLR):
        """Minimum margin (>= 0 is clear) of a track against other-net pads/tracks/vias, edges, keepouts."""
        worst, why = math.inf, None
        for a, b in zip(path, path[1:]):
            pts = samples(a, b)
            for p in self.inp.pads:
                if layer not in p['layers']:
                    continue
                if p['net'] == net and p['kind'] != 'np_thru_hole':
                    continue
                extra = 0.1 if p['kind'] == 'np_thru_hole' else 0.0  # NPTH: hole clearance 0.25 + margin
                m = min(p['shape'].dist(*q) for q in pts) - width / 2 - clr - extra
                if m < worst:
                    worst, why = m, f"pad {p['ref']}.{p['number']} ({p['net']})"
            for t in self.tracks:
                if t['layer'] != layer or t['net'] == net:
                    continue
                for c, d in zip(t['path'], t['path'][1:]):
                    cap = cb.Capsule(c[0], c[1], d[0], d[1], t['width_mm'] / 2)
                    m = min(cap.dist(*q) for q in pts) - width / 2 - clr
                    if m < worst:
                        worst, why = m, f"track {t['id']}"
            for v in self.vias:
                if v['net'] == net:
                    continue
                m = min(math.hypot(q[0] - v['at'][0], q[1] - v['at'][1]) for q in pts) - v['diameter_mm'] / 2 - width / 2 - clr
                if m < worst:
                    worst, why = m, f"via {v['id']}"
            for q in pts:
                if not self.inside_board(q):
                    return -9, 'outside the board'
                m = self.edge_dist(q) - width / 2 - EDGE
                if m < worst:
                    worst, why = m, 'edge'
                for h in self.inp.holes:
                    m = math.hypot(q[0] - h[0], q[1] - h[1]) - 3.0 - width / 2 - 0.05
                    if m < worst:
                        worst, why = m, f'hole keepout {h}'
                for z in self.inp.keepouts:
                    if layer in z['layers']:
                        m = z['poly'].dist(*q) - width / 2 - 0.05
                        if m < worst:
                            worst, why = m, f"keepout {z['ref']}"
        return worst, why

    def via_clear(self, c, net, d=VIA_D, drill=VIA_DRILL, clr=CLR):
        r = d / 2
        if not self.inside_board(c):
            return -9, 'outside'
        worst, why = self.edge_dist(c) - r - EDGE, 'edge'
        for h in self.inp.holes:
            m = math.hypot(c[0] - h[0], c[1] - h[1]) - 3.0 - r - 0.05
            if m < worst:
                worst, why = m, 'hole keepout'
        for z in self.inp.keepouts:
            m = z['poly'].dist(*c) - r - 0.1
            if m < worst:
                worst, why = m, f"keepout {z['ref']}"
        for p in self.inp.pads:
            if p['kind'] == 'np_thru_hole' or (p['kind'] == 'thru_hole' and p['drill']):
                hd = p['drill'][0] if p['drill'] else 0
                m = math.hypot(c[0] - p['c'][0], c[1] - p['c'][1]) - hd / 2 - drill / 2 - 0.55
                if m < worst:
                    worst, why = m, f"hole {p['ref']}.{p['number']}"
            if p['kind'] == 'np_thru_hole':
                continue
            if p['net'] == net:
                m = p['shape'].dist(*c) - r - 0.05  # no via in a pad
            else:
                m = p['shape'].dist(*c) - r - clr
            if m < worst:
                worst, why = m, f"pad {p['ref']}.{p['number']}"
        for v in self.vias:
            m = math.hypot(c[0] - v['at'][0], c[1] - v['at'][1]) - (0.95 if v['net'] == net else r + v['diameter_mm'] / 2 + clr)
            if m < worst:
                worst, why = m, f"via {v['id']}"
        for t in self.tracks:
            if t['net'] == net:
                continue
            for a, b in zip(t['path'], t['path'][1:]):
                m = cb.Capsule(a[0], a[1], b[0], b[1], t['width_mm'] / 2).dist(*c) - r - clr
                if m < worst:
                    worst, why = m, f"track {t['id']}"
        return worst, why

    def pad(self, ref, number):
        hits = [p for p in self.inp.pads if p['ref'] == ref and p['number'] == number]
        assert hits, (ref, number)
        return hits[0]

    def track(self, tid, net, layer, width, path, why, check=True, clr=CLR):
        path = [[round(x, 4), round(y, 4)] for x, y in path]
        if check:
            m, w = self.track_clear(layer, width, path, net, clr=clr)
            self.log(f'  {tid:24s} {layer} w{width} margin {m:+.3f} ({w})')
            if m < 0:
                raise SystemExit(f'make_spec: scripted track {tid} violates clearance: {w}')
        self.tracks.append({'id': tid, 'net': net, 'layer': layer, 'width_mm': width, 'path': path, 'locked': True, 'why': why})

    def via(self, vid, net, at, why, d=VIA_D, drill=VIA_DRILL):
        at = [round(at[0], 4), round(at[1], 4)]
        m, w = self.via_clear(at, net, d, drill)
        self.log(f'  via {vid:20s} margin {m:+.3f} ({w})')
        if m < 0:
            raise SystemExit(f'make_spec: scripted via {vid} violates clearance: {w}')
        self.vias.append({'id': vid, 'net': net, 'at': at, 'drill_mm': drill, 'diameter_mm': d, 'locked': True, 'why': why})


# ------------------------------------------------------------------ scripted copper
BR = 'LAB5 branch (branch_exempt, '
HARD = ('U310', 'U311', 'U315')  # middle GND pins of SOT-23-6 parts: placed first, they have the fewest via spots


def power_copper(cu):
    P = cu.pad
    J305_3, J305_4, J314_2, J314_1 = P('J305', '3')['c'], P('J305', '4')['c'], P('J314', '2')['c'], P('J314', '1')['c']
    D306_2, Q305_3 = P('D306', '2')['c'], P('Q305', '3')['c']
    Q304_3, F301_1 = P('Q304', '3')['c'], P('F301', '1')['c']
    YB = J314_1[1]  # E3_BLOWER_GND return rail at the J314.1 height
    XL = 12.2  # LAB5 trunk column on F.Cu
    cu.track('LAB5-TRUNK-F', 'LAB5', 'F.Cu', 1.85,
             [J305_3, J305_4, (XL, J305_4[1]), (XL, 64.5), (XL, J314_2[1]), J314_2],
             'LAB5 feed of the blower: J305.3/J305.4 (input pair) to J314.2 on F.Cu at the PWR3A width; it crosses the B.Cu '
             'E3_BLOWER_GND return; locked, pad centre to pad centre; the other LAB5 pads hang on the scripted 1.85 mm LAB5 '
             'feeds of W2 CTRL-4')
    cu.track('BLOWER-GND-RAIL', 'E3_BLOWER_GND', 'B.Cu', 1.85,
             [J314_1, (D306_2[0], YB), (Q305_3[0], YB), Q305_3],
             'blower return J314.1 to the low-side switch Q305 drain at the PWR3A width (pad centre to pad centre)')
    cu.track('BLOWER-GND-D306', 'E3_BLOWER_GND', 'B.Cu', 1.85, [(D306_2[0], YB), D306_2],
             'flyback diode D306 anode on the blower return at the PWR3A width')
    cu.track('FAN5-Q304-F301', 'E3_FAN5', 'B.Cu', 1.85, [Q304_3, F301_1],
             'fan switch Q304 drain to the PTC F301 at the PWR3A width (one segment, pad centre to pad centre)')

    # LAB5 capacitors of the trunk side at the class width too (W2 CTRL-4): C343 next to J305.4 from below (C343.2 sits above
    # C343.1), C342 off the trunk above the J317 pins through four vias
    cu.track('LAB5-C343', 'LAB5', 'B.Cu', FEED_W, [J305_4, (9.6, 65.3), (11.3, 65.3)],
             'LAB5 to the decoupling capacitor C343 next to J305.4, entering C343.1 from below (W2 CTRL-4). ' + FEED_RATING.format(w=FEED_W))
    cu.track('LAB5-C342-F', 'LAB5', 'F.Cu', FEED_W, [(XL, 64.5), (21.9, 64.5)],
             'LAB5 to the bulk capacitor C342: from the F.Cu trunk above the J317 pins to four vias next to C342 (W2 CTRL-4). '
             + FEED_RATING.format(w=FEED_W))
    for k, at in enumerate(((21.4, 64.0), (22.4, 64.0), (21.4, 65.0), (22.4, 65.0))):
        cu.via(f'LAB5-V-C342{"abcd"[k]}', 'LAB5', at, 'LAB5 C342 branch F.Cu to B.Cu: four 0.7/0.3 mm vias, about 1.0 A each at '
               '+20 degC (barrel model of pcb/stackup.py), 4 A for the F102 protective current (W2 CTRL-4)', d=0.7)
    cu.track('LAB5-C342-B', 'LAB5', 'B.Cu', FEED_W, [(21.9, 64.5), (21.4, 66.4)],
             'LAB5: the C342 vias to C342.1 (W2 CTRL-4). ' + FEED_RATING.format(w=FEED_W))
    lab5_feed(cu)
    return {}


# W2 CTRL-4 (6 layers): the right LAB5 group (the Pico VSYS diode D301, the GNSS switch U315 with C321/C322, the fan switch
# Q304 with C320/R367) and D306 hang on scripted outer copper at the PWR3A class width 1.85 mm (pcb/generated/netclasses.json:
# outer_min_width_mm 1.85 >= LAB5 required_outer_width_mm 1.3348 for the F102 4 A protective current at +20 degC; inner
# copper is no PWR3A current path), with four 0.7/0.3 mm vias per layer change (about 1.0 A each at +20 degC, barrel model
# of pcb/stackup.py). Each piece: (id, layer, width, path in board mm); 'V' rows are via clusters. Pad entries narrower
# than 1.85 mm stay inside neck_exempt (escape_mm) of the part.
FEED_W = 1.85
FEED_RATING = ('LAB5 PWR3A copper at the class width {w} mm on B.Cu (1 oz): IPC-2221 external (k 0.048; MODEL) about 5.1 A at '
               '+20 degC and 3.7 A at +10 degC, above the F102 4 A protective current at +20 degC and the 1.0 A continuous LAB5 '
               'budget at +10 degC (netclasses.json LAB5 required_outer_width_mm 1.3348); no via, no inner copper (W2 CTRL-4)')
FEED = [  # (id, layer, width, path: board mm or 'REF.PAD' for a pad centre); every LAB5 load of the right group on B.Cu
    ('LAB5-FEED-D', 'B.Cu', FEED_W,
     ['J314.2', (10.35, 54.65), (11.25, 53.95), (14.95, 53.95), (15.65, 53.15), (19.35, 47.45), (19.95, 46.95), (24.75, 47.35),
      (27.05, 49.65), (28.25, 53.85), (29.05, 54.55), (34.05, 54.25), (34.85, 53.45), 'D301.2', (44.3, 74.4), (43.85, 74.85),
      (43.85, 88.9), (48.7, 88.9), (48.7, 86.4)]),
    ('LAB5-FEED-D306', 'B.Cu', FEED_W, [(14.95, 53.95), 'D306.1']),
    ('LAB5-FEED-C320', 'B.Cu', FEED_W, [(43.85, 88.9), (41.95, 88.9)]),
    ('LAB5-FEED-R367', 'B.Cu', FEED_W, [(45.5, 88.9), (45.5, 87.1)]),
    ('LAB5-FEED-U', 'B.Cu', FEED_W,
     ['J305.3', (7.05, 67.15), (4.95, 65.45), (1.35, 69.05), (5.15, 93.35), (11.45, 99.55), (21.65, 98.15), (23.15, 98.1), (26.6, 98.1)]),
    ('LAB5-FEED-U315', 'B.Cu', FEED_W, [(24.5, 98.1), (24.5, 97.4)]),
    ('LAB5-FEED-C321', 'B.Cu', FEED_W, [(23.2, 98.1), (23.2, 99.3)]),
]
FEED_VIAS = []     # (id, (x, y)): none, the feed stays on B.Cu
FEED_WHY = {
    'LAB5-FEED-D': ('LAB5 feed D (W2 CTRL-4): J314.2 on B.Cu below D306 (spur LAB5-FEED-D306), under the Pico between its SWD '
                    'pads and pin 20/21, through the Pico VSYS diode pad D301.2, up the right strip beside cut-out 1 (x 43.85, '
                    'between the J313 pins and C318/F301) and along y 88.9 above the fan switch to Q304.2 (spurs to C320.1 and '
                    'R367.2). ' + FEED_RATING.format(w=FEED_W)),
    'LAB5-FEED-U': ('LAB5 feed U (W2 CTRL-4): J305.3 on B.Cu below J305, up the left board edge beside cut-out 1, past the H5 '
                    'keepout into the band between the cut-outs to the GNSS switch group: C321.1, U315.1 and C322.1 (spurs). '
                    + FEED_RATING.format(w=FEED_W)),
    '*': 'LAB5 spur of the W2 CTRL-4 feed to a right-group pad at the class width. ' + FEED_RATING.format(w=FEED_W),
}
GND_JOINED = {('U315', '2'): ('C322', '2')}  # GND pad -> GND pad with its own plane via (W2 CTRL-4: C322 took the U315.2 via spot)


def lab5_feed(cu):
    for tid, layer, width, path in FEED:
        cu.track(tid, 'LAB5', layer, width, [tuple(p) if not isinstance(p, str) else cu.pad(*p.split('.'))['c'] for p in path],
                 FEED_WHY.get(tid, FEED_WHY['*']))
    for vid, at in FEED_VIAS:
        cu.via(vid, 'LAB5', at, FEED_WHY.get(vid, FEED_WHY['*']), d=0.7)
    for (ra, na), (rb, nb) in GND_JOINED.items():
        a, b = cu.pad(ra, na), cu.pad(rb, nb)
        assert a['net'] == b['net'] == 'GND'
        cu.track(f'GND-{ra}.{na}', 'GND', 'B.Cu', STUB_W, [a['c'], b['c']],
                 f'GND pad {ra}.{na} joined to {rb}.{nb} and its plane via (W2 CTRL-4: the input capacitor C322 sits next to U315)')


def pico_covers(cu):
    """Locked GND copper over the custom Pico GND pads (castellated pins), so Freerouting sees the whole pad
    (route run 43100344071: two router tracks too close to U305 pads 8 and 13, the DSN carries the anchor only)."""
    inp = cu.inp
    lib = inp.geo.lib(bg.footprint_file(inp.tpl['U305']))
    nets = {str(p['number']): p.get('net') for p in inp.graph['U305']['pins']}
    count = 0
    for lp in lib['pads']:
        if lp['shape'] != 'custom' or nets.get(lp['number']) != 'GND':
            continue
        text = lib['text']
        m0 = text.index(f'(pad "{lp["number"]}" smd custom')
        block = text[m0:text.index('(uuid', m0)]
        circles = [(float(a), float(b), math.hypot(float(c) - float(a), float(d) - float(b))) for a, b, c, d in
                   re.findall(r'\(center (\S+) (\S+)\)\s*\(end (\S+) (\S+)\)', block)]
        big = [c for c in circles if c[2] > 0.5]
        small = [c for c in circles if c[2] <= 0.5]
        xs = [c[0] + c[2] for c in big] + [c[0] - c[2] for c in big] + [c[0] - c[2] for c in small] + [c[0] + c[2] for c in small]
        pts = [(float(a), float(b)) for a, b in re.findall(r'\(xy (\S+) (\S+)\)', block)]
        x0, x1 = min([p[0] for p in pts] + xs), max([p[0] for p in pts] + xs)
        r = 0.8
        segs = [((x0 + r, 0.0), (x1 - r, 0.0), 2 * r)]
        if small:
            sx = small[0][0]
            segs.append(((sx, -0.6), (sx, 0.6), 0.4))
            toward = 0.6 if sx < 0 else -0.6
            segs += [((sx, 0.6), (sx + toward, 0.6), 0.4), ((sx, -0.6), (sx + toward, -0.6), 0.4)]

        def to_board(q):
            qx, qy = cb.rot(q[0], q[1], lp['a'])
            return inp.geo.place_pt((lp['at'][0] + qx, lp['at'][1] + qy), inp.anchors['U305'])
        new = []
        for k, (pa, pb, w) in enumerate(segs):
            A, B = to_board(pa), to_board(pb)
            new.append({'id': f'GND-U305.{lp["number"]}-COVER{k}', 'net': 'GND', 'layer': 'B.Cu', 'width_mm': w,
                        'path': [[round(A[0], 4), round(A[1], 4)], [round(B[0], 4), round(B[1], 4)]], 'locked': True,
                        'why': 'inside the custom Pico GND pad outline: the router keeps its clearance to the whole pad'})
        shp = cu.pad('U305', lp['number'])['shape']
        for t in new:  # the cover stays inside the pad outline (+0.02)
            a, b = t['path']
            for q in samples(a, b, 0.02):
                for ang in range(0, 360, 30):
                    e = (q[0] + t['width_mm'] / 2 * 0.999 * math.cos(math.radians(ang)),
                         q[1] + t['width_mm'] / 2 * 0.999 * math.sin(math.radians(ang)))
                    if shp.dist(*e) >= 0.02:
                        raise SystemExit(f'make_spec: {t["id"]} leaves the pad outline at {e}')
        cu.tracks.extend(new)
        count += len(new)
    cu.log(f'  pad covers {count}')


def gnd_vias(cu, sel, centroid, skipped):
    """One locked plane via and a stub per SMD GND pad: 24 directions, growing radius, away from the part first."""
    plane_vias(cu, sel, centroid, skipped, 'GND')


def plane_vias(cu, sel, centroid, skipped, net):
    """One locked via to the plane of net and a stub per SMD pad in sel (GND; on 6 layers also 3V3_Q6A, W2 CTRL-R)."""
    for p in sorted(sel, key=lambda q: (bg.sort_ref(q['ref']), q['number'], q['c'])):
        layer = p['layers'][0]
        cx, cy = p['c']
        ox, oy = cx - centroid[p['ref']][0], cy - centroid[p['ref']][1]
        on = math.hypot(ox, oy) or 1.0
        cands = []
        for k in range(24):
            ang = 2 * math.pi * k / 24
            ux, uy = math.cos(ang), math.sin(ang)
            away = (ux * ox + uy * oy) / on
            for step in range(30):
                dist = 0.2 + VIA_D / 2 + 0.1 * step
                c = (round(cx + dist * ux, 3), round(cy + dist * uy, 3))
                if p['shape'].dist(*c) < VIA_D / 2 + 0.05:
                    continue
                if p['ref'] == 'U305':  # Pico GND pins: vias under the module, the escape channels outside stay free
                    away = -away
                cands.append((dist + (0.0 if away > 0.3 else 0.6), dist, c))
        if p['ref'] == 'U305' and p['number'] != 'SWD_GND':
            # castellated GND pin: via straight inwards under the module, past the pad end (the channels between the
            # pads and outside the module stay free for the router); the general search is the fallback
            sgn = 1.0 if centroid['U305'][0] > cx else -1.0
            general = sorted(cands)
            cands = [(d + abs(dy), d, (round(cx + sgn * d, 3), round(cy + dy, 3))) for d in [2.15 + 0.1 * k for k in range(30)]
                     for dy in (0.0, 0.2, -0.2, 0.5, -0.5, 0.9, -0.9)]
            cands = sorted(cands) + [(9.0 + g[0], g[1], g[2]) for g in general]
        cands.sort()
        done = False
        for _score, dist, c in cands:
            m, why = cu.via_clear(c, net)
            if m < 0:
                continue
            tm, twhy = cu.track_clear(layer, STUB_W, [(cx, cy), c], net)
            if tm < 0:
                continue
            vid = f'{"GND" if net == "GND" else "V33P"}-{p["ref"]}.{p["number"]}'
            if any(v['id'] == vid for v in cu.vias):
                vid += f'-{len(cu.vias)}'
            cu.vias.append({'id': vid, 'net': net, 'at': [c[0], c[1]], 'drill_mm': VIA_DRILL, 'diameter_mm': VIA_D, 'locked': True})
            cu.tracks.append({'id': vid, 'net': net, 'layer': layer, 'width_mm': STUB_W,
                              'path': [[round(cx, 4), round(cy, 4)], [c[0], c[1]]], 'locked': True})
            done = True
            break
        if not done:
            skipped.append(f"{p['ref']}.{p['number']}")
            cu.log(f"   skip {p['ref']} {p['number']} {p['c']}")


def q6a_copper(cu):
    """3V3_Q6A pieces the router left open (route runs 43106410728, 43111037016, 43114111838, 43118391983)."""
    P = cu.pad
    # left pull-up column R308-R319 (pad 2 of each, F.Cu): an L3 bus beside the column, one via beside each pad 2;
    # the FAULT pads 1 leave towards J306/J307 on F.Cu between the vias
    col = [P(f'R{n}', '2') for n in range(308, 320)]
    assert all(c['net'] == '3V3_Q6A' for c in col)
    XB = 2.3
    for c in col:
        cu.via(f'V33-{c["ref"]}', '3V3_Q6A', (XB, c['c'][1]), '3V3_Q6A pull-up bus via next to ' + c['ref'] + '.2')
        cu.track(f'V33-{c["ref"]}', '3V3_Q6A', 'F.Cu', 0.25, [c['c'], (XB, c['c'][1])], '3V3_Q6A stub, pad 2 to its bus via')
    # 6 layers (W2 CTRL-R): the vias reach the 3V3_Q6A plane on In4.Cu (L5), so the former L3 bus beside the column is gone
    # right pull-up column (pad 2 of R301, R302, R320-R325, R392): F.Cu chain on its left side, between the resistor
    # pads and the TL3145 pads (0.17 / 0.235 mm, board rule 0.15); the pads 1 leave to the right towards J304
    rcol = sorted([P(r, '2') for r in ('R301', 'R302', 'R320', 'R321', 'R322', 'R323', 'R324', 'R325', 'R392')],
                  key=lambda q: -q['c'][1])
    assert all(c['net'] == '3V3_Q6A' for c in rcol)
    XR3 = 39.27
    for a, b in zip(rcol, rcol[1:]):
        cu.track(f'V33-{a["ref"]}-{b["ref"]}', '3V3_Q6A', 'F.Cu', 0.2, [a['c'], (XR3, a['c'][1]), (XR3, b['c'][1]), b['c']],
                 '3V3_Q6A chain of the right pull-up column, left of the pads', clr=0.165)
    # MCP23017 U302/U303: VDD pin 9 to the address pins tied high (16, and 15 on U303) under the package body on F.Cu
    for ref, pins in (('U303', ('9', '16', '15')), ('U302', ('9', '16'))):
        p9, p16 = P(ref, '9')['c'], P(ref, '16')['c']
        path = [p9, (24.0, p9[1]), (24.0, p16[1]), p16] + ([P(ref, '15')['c']] if '15' in pins else [])
        cu.track(f'V33-{ref}', '3V3_Q6A', 'F.Cu', 0.25, path, f'3V3_Q6A of {ref}: VDD pin 9 to the address pins tied high, under the body')
    # decoupling row C302/C304/C306 (pad 1 each, F.Cu, one row): joined along the row, one plane via for the group (W2 CTRL-R)
    row = [P(r, '1') for r in ('C302', 'C304', 'C306')]
    assert all(c['net'] == '3V3_Q6A' for c in row)
    cu.track('V33-C302-C306', '3V3_Q6A', 'F.Cu', 0.25, [row[0]['c'], row[2]['c']], '3V3_Q6A: decoupling row C302-C304-C306, pad 1 to pad 1')
    # U315 pin 3 (3V3_Q6A) is boxed in by the cut-out edge, U315 pin 2's GND stub and the U301 pads above
    cu.via('V33-U315', '3V3_Q6A', (27.5, 94.45), '3V3_Q6A via for U315 pin 3, right of the U301 pads')
    cu.track('V33-U315', '3V3_Q6A', 'B.Cu', 0.25, [P('U315', '3')['c'], (27.5, 94.45)], '3V3_Q6A stub, U315.3 to its via')


Q6A_PLANE = 'In4.Cu'  # W2 CTRL-R: L5 is a solid 3V3_Q6A plane (type power); its SMD pads reach it through scripted vias
# 3V3_Q6A pads already joined by scripted copper: one plane via per group is enough (the first pad that finds a spot)
Q6A_GROUPS = [('R392', 'R325', 'R324', 'R323', 'R322', 'R321', 'R320', 'R302', 'R301'), ('U303',), ('U302',), ('C306', 'C304', 'C302')]
Q6A_HAVE_VIA = {f'R{n}' for n in range(308, 320)} | {'U315'}


def q6a_plane_vias(cu, centroid, skipped):
    """Plane vias of the SMD 3V3_Q6A pads (W2 CTRL-R, 6 layers): route runs 43136394379 (4 layers) and 43183047190 (6 layers,
    five routing layers) left 8 and 16 of the 3V3_Q6A connections open (42 pads, 38 SMD, 0.1 A logic supply)."""
    pads = [p for p in cu.inp.pads if p['net'] == '3V3_Q6A' and p['kind'] == 'smd' and p['number']]
    done = set(Q6A_HAVE_VIA)
    for group in Q6A_GROUPS:
        members = [p for r in group for p in sorted((q for q in pads if q['ref'] == r), key=lambda q: bg.sort_ref(q['number']))]
        for p in members:
            miss = []
            plane_vias(cu, [p], centroid, miss, '3V3_Q6A')
            if not miss:
                break
        else:
            skipped.append('3V3_Q6A group ' + '/'.join(group))
        done |= set(group)
    plane_vias(cu, [p for p in pads if p['ref'] not in done], centroid, skipped, '3V3_Q6A')


P33 = 'E3_PICO3V3'


def pico3v3_copper(cu):
    """E3_PICO3V3 (Pico 3V3 output to the HMI, encoder and fan-tach pull-ups) and the pull-up rows (route run
    43121860459 left 14 E3_PICO3V3 connections open, most of them at pads the router could not leave)."""
    P = cu.pad
    W = 0.2
    # R4B, bottom side under cut-out 2: bus between the pull-up pads and the cut-out edge, stub per pull-up
    y4 = 108.95
    pull = [P(r, '2') for r in ('R351', 'R353', 'R355', 'R357')]
    assert all(p['net'] == P33 for p in pull)
    xd = 40.3  # right of cut-out 2, between the J311 pins (x 38.9) and the J310 pins (x >= 40.9)
    j312 = P('J312', '4')
    cu.track('P33-R4B-BUS', P33, 'B.Cu', W, [(pull[0]['c'][0], y4), (xd, y4), (xd, 109.6), (xd, 132.8), (xd, 134.6), (39.0, 135.9), (39.0, 139.8),
                                            (j312['c'][0], 139.8), j312['c']],
             'E3_PICO3V3 bus of the R4B pull-ups between their pads and the cut-out 2 edge, then up the right strip beside the '
             'J311 pins and along the top edge above the header pins to J312.4 (route run 43131682520 left both open)')
    for p in pull:
        cu.track(f'P33-{p["ref"]}', P33, 'B.Cu', W, [p['c'], (p['c'][0], y4)], 'E3_PICO3V3 stub, pull-up pad 2 to the R4B bus')
    for rs, rp in (('R352', 'R351'), ('R354', 'R353'), ('R356', 'R355'), ('R358', 'R357')):
        a, b = P(rs, '1'), P(rp, '1')
        assert a['net'] == b['net']
        cu.track(f'RAW-{rs}-{rp}', a['net'], 'B.Cu', W, [a['c'], b['c']],
                 f'{a["net"]}: series resistor {rs} (upper pad) to pull-up {rp} (lower pad), diagonal between the pad rows')
    # HMI2 / HMI3, top side under cut-out 1: R345.2 -> right of the HMI2 column -> bus to R343.2, R347.2, R349.2
    y3, xr, xe = 68.05, 25.75, 40.0
    r343, r345 = P('R343', '2'), P('R345', '2')
    cu.track('P33-HMI-BUS', P33, 'F.Cu', W, [r345['c'], (xr, r345['c'][1]), (xr, y3), (xe, y3), (xe, 69.0)],
             'E3_PICO3V3: R345.2 right of the HMI2 column, then the bus between the HMI3 pull-up pads and the cut-out 1 edge')
    cu.via('P33-V-HMI', P33, (xe, 69.0), 'E3_PICO3V3: HMI bus to the L4 link up the right strip (W2 CTRL-R: the F.Cu pieces to '
           'R368/R395 gave way to the LAB5 feed of the right group)')
    cu.track('P33-R343', P33, 'F.Cu', W, [r343['c'], (r343['c'][0], y3), (xr, y3)], 'E3_PICO3V3 stub, R343.2 to the bus')
    for r in ('R347', 'R349'):
        p = P(r, '2')
        cu.track(f'P33-{r}', P33, 'F.Cu', W, [p['c'], (p['c'][0], y3)], f'E3_PICO3V3 stub, {r}.2 to the bus')
    # the HMI pull-ups R334/R335 (route run 43185702454 joined them to each other only): pad 2 to pad 2, then up to the bus
    r334, r335 = P('R334', '2'), P('R335', '2')
    assert r334['net'] == r335['net'] == P33
    cu.track('P33-R334-R335', P33, 'F.Cu', W, [r334['c'], r335['c']], 'E3_PICO3V3: R334.2 to R335.2 (adjacent pads)')
    cu.track('P33-R334-BUS', P33, 'F.Cu', W, [r334['c'], (r334['c'][0], 57.0), (xr, 58.28), (xr, r345['c'][1])],
             'E3_PICO3V3: R334.2 up to the HMI bus at R345.2 (W2 CTRL-R; route run 43185702454 left this group open)')
    # the HMI pull-up row group (C312, R337/R339/R341, U306.24) to R335.2 on L4 under the R335/R336 row (route runs 43136394379,
    # 43185702454 and 43190774090 left C312.1 and R335.2 unjoined; W2 CTRL-R)
    c312 = P('C312', '1')
    cu.via('P33-V-C312', P33, (29.6, 53.05), 'E3_PICO3V3: via above C312.1, below the R335/R336 row')
    cu.track('P33-C312-V', P33, 'F.Cu', W, [c312['c'], (29.6, 53.05)], 'E3_PICO3V3: C312.1 to its via')
    cu.via('P33-V-R335', P33, (30.6, 57.45), 'E3_PICO3V3: via above R336.2, clear of the buzzer pin')
    cu.track('P33-R335-V', P33, 'F.Cu', W, [r335['c'], (30.6, 57.45)], 'E3_PICO3V3: R335.2 to its via')
    cu.track('P33-C312-R335-L4', P33, 'In3.Cu', W, [(29.6, 53.05), (29.75, 53.2), (29.75, 56.6), (30.6, 57.45)],
             'E3_PICO3V3: L4 link from the C312 via to the R335 via')
    cu.track('FN-R343-R344', 'E3_FN', 'F.Cu', W, [P('R343', '1')['c'], P('R344', '1')['c']],
             'E3_FN: pull-up R343 to series resistor R344 (adjacent pads of the HMI2 column)')
    for rs, rp in (('R348', 'R347'), ('R350', 'R349')):
        a, b = P(rs, '1'), P(rp, '1')
        assert a['net'] == b['net']
        cu.track(f'PRESS-{rs}-{rp}', a['net'], 'F.Cu', W, [a['c'], b['c']],
                 f'{a["net"]}: series resistor {rs} (upper pad) to pull-up {rp} (lower pad), diagonal between the pad rows')
    # on to the fan-tach pull-up R368 (bottom side, via above it) and the MCP reset pull-up R395 (top side)
    # W2 CTRL-R: R368.2 (bottom) is left to the router; R395.1 hangs off the L4 link (below)
    vx = 38.6
    # R361 / R362 (AMB pull-ups, adjacent upper pads), joined to the right-strip bus on L4 along the right edge and
    # below the H4 keepout
    cu.track('P33-R361-R362', P33, 'F.Cu', W, [P('R361', '2')['c'], P('R362', '2')['c']], 'E3_PICO3V3: R361.2 to R362.2')
    r362 = P('R362', '2')
    xa = 48.6
    cu.track('P33-AMB-B', P33, 'B.Cu', W, [(xd, 132.8), (xa, 132.8), (xa, r362['c'][1])],
             'E3_PICO3V3: right-strip bus to a via right of R362, below the H4 keepout and along the right edge')
    cu.via('P33-V-AMB', P33, (xa, r362['c'][1]), 'E3_PICO3V3: B.Cu to F.Cu right of R362')
    cu.track('P33-AMB-F', P33, 'F.Cu', W, [(xa, r362['c'][1]), r362['c']], 'E3_PICO3V3: via to R362.2')
    # the R4B / right-strip bus to the HMI3 branch: via above R358, L1 between the J316 pins and down beside cut-out 1
    cu.via('P33-V-R4B', P33, (xd, 109.6), 'E3_PICO3V3: right-strip bus B.Cu to F.Cu above R358')
    cu.track('P33-RIGHT-F', P33, 'In3.Cu', W, [(xd, 109.6), (40.55, 104.5), (40.55, 101.0), (39.235, 97.0), (39.235, 89.5), (vx, 88.8),
                                                (vx, 73.5), (vx, 70.4), (xe, 69.0)],
             'E3_PICO3V3 from the right-strip bus between the J316 pins 2 and 1, past C302/C304, then down beside the cut-out 1 edge to '
             'the via at the HMI bus end (route runs 43121860459 and 43131682520 left this link open); on L4 (In3.Cu) since the 6-layer '
             'stackup (W2 CTRL-R), under the outer LAB5 feed of the right group, so that the F.Cu pad C302.1 (3V3_Q6A) gets its plane via')
    r395 = P('R395', '1')
    cu.track('P33-R395-L4', P33, 'In3.Cu', W, [(vx, 73.5), (46.3, 73.5), (46.3, 76.0)],
             'E3_PICO3V3: L4 branch from the right-strip link below J313 to a via next to R395 (W2 CTRL-R)')
    cu.via('P33-V-R395', P33, (46.3, 76.0), 'E3_PICO3V3: L4 to F.Cu next to R395.1')
    cu.track('P33-R395', P33, 'F.Cu', W, [(46.3, 76.0), r395['c']], 'E3_PICO3V3: via to R395.1')
    # Pico: pin 36 (3V3 out) to a via just right of the pad (the router joins it on any layer), R330.2 - R327.1 - C308.1
    u36, r330, r327, c308 = P('U305', '36'), P('R330', '2'), P('R327', '1'), P('C308', '1')
    assert u36['net'] == P33
    cu.track('P33-U305', P33, 'B.Cu', W, [u36['c'], (34.5, u36['c'][1])], 'E3_PICO3V3: Pico pin 36 to its escape via')
    cu.via('P33-V-U305', P33, (34.5, u36['c'][1]), 'E3_PICO3V3: escape via of Pico pin 36 below the PICO column')
    cu.track('P33-R330-R327', P33, 'B.Cu', W, [r330['c'], r327['c']], 'E3_PICO3V3: R330.2 to R327.1 (adjacent pads)')
    cu.track('P33-C308-R327', P33, 'B.Cu', W, [c308['c'], (37.75, 27.2), (37.75, r327['c'][1]), r327['c']],
             'E3_PICO3V3: C308.1 down between C311 and R327 to R327.1')
    # HMI row (top side): the pull-ups R337/R339/R341 joined in the 0.85 mm gap between the pad rows (where the router
    # joined them in route run 43121860459), on to C312.1 and down to U306.24 (VDD)
    yc = 51.32
    c312, u306 = P('C312', '1'), P('U306', '24')
    cu.track('P33-HMI-ROW', P33, 'F.Cu', W, [(P('R337', '2')['c'][0], yc), (c312['c'][0], yc), (c312['c'][0], u306['c'][1]),
                                            u306['c']],
             'E3_PICO3V3: HMI pull-ups R337/R339/R341 in the gap between the pad rows, C312.1, U306.24 (VDD)')
    for r in ('R337', 'R339', 'R341', 'C312'):
        q = P(r, '2' if r != 'C312' else '1')
        assert q['net'] == P33
        cu.track(f'P33-{r}', P33, 'F.Cu', W, [q['c'], (q['c'][0], yc)], f'E3_PICO3V3 stub, {r} to the HMI row link')


def blower_gnd_branches(cu):
    """E3_BLOWER_GND to the blower supply capacitors C342 (bulk) and C343 (decoupling): route run 43121860459 left both
    open at the 0.5 mm router width. Ripple current only, no DC path; 0.4 mm (C342, between the J317 pins) and 0.3 mm
    (C343, between C343 and R363)."""
    P = cu.pad
    rail_y = P('J314', '1')['c'][1]
    c342, c343 = P('C342', '2'), P('C343', '2')
    xg = (P('J317', '3')['c'][0] + P('J317', '2')['c'][0]) / 2
    cu.track('BLOWER-GND-C342', 'E3_BLOWER_GND', 'B.Cu', 0.4, [c342['c'], (c342['c'][0], 63.4), (xg, 63.4), (xg, rail_y)],
             'E3_BLOWER_GND branch to C342: between the J317 pins 3 and 2 down to the 1.85 mm rail (branch_exempt)')
    cu.track('BLOWER-GND-C343', 'E3_BLOWER_GND', 'B.Cu', 0.3, [c343['c'], (12.62, c343['c'][1]), (12.62, rail_y)],
             'E3_BLOWER_GND branch to C343: right of C343, down to the 1.85 mm rail (branch_exempt)')


def scripted_copper(inp, log):
    cu = Copper(inp, log)
    log('scripted power copper')
    power_copper(cu)
    log('Pico custom pad covers')
    pico_covers(cu)
    log('GND plane vias and 3V3_Q6A pieces')
    gnd_smd = [p for p in inp.pads if p['net'] == 'GND' and p['kind'] == 'smd' and p['number']
               and (p['ref'], p['number']) not in GND_JOINED]
    centroid = {}
    for part in inp.template:
        ps = [p['c'] for p in inp.pads if p['ref'] == part['ref']]
        centroid[part['ref']] = (sum(x for x, _ in ps) / len(ps), sum(y for _, y in ps) / len(ps))
    skipped = []
    q6a_copper(cu)
    log('E3_PICO3V3 pieces, pull-up rows and E3_BLOWER_GND branches')
    pico3v3_copper(cu)
    blower_gnd_branches(cu)
    gnd_vias(cu, [p for p in gnd_smd if p['ref'] in HARD], centroid, skipped)
    gnd_vias(cu, [p for p in gnd_smd if p['ref'] not in HARD], centroid, skipped)
    # a skipped pad joins the nearest GND via with a stub when that is clear
    for name in list(skipped):
        ref, num = name.split('.', 1)
        p = [q for q in gnd_smd if q['ref'] == ref and q['number'] == num][0]
        layer = p['layers'][0]
        for v in sorted(cu.vias, key=lambda v: math.hypot(v['at'][0] - p['c'][0], v['at'][1] - p['c'][1]))[:6]:
            if math.hypot(v['at'][0] - p['c'][0], v['at'][1] - p['c'][1]) > 3.0:
                break
            tm, _ = cu.track_clear(layer, STUB_W, [p['c'], v['at']], 'GND')
            if tm >= 0:
                cu.tracks.append({'id': f'GND-{name}', 'net': 'GND', 'layer': layer, 'width_mm': STUB_W,
                                  'path': [[round(p['c'][0], 4), round(p['c'][1], 4)], v['at']], 'locked': True})
                skipped.remove(name)
                log(f'  joined {name} to {v["id"]}')
                break
    q6a_plane_vias(cu, centroid, skipped)  # after the GND vias: GND keeps its via spots
    log(f'  {len(cu.vias)} vias, still skipped {skipped}')
    frozen_copper(cu, log)
    return cu, skipped


FROZEN = BASE / 'build/kicad/boards/CTRL/route-frozen.json'
# W2 CTRL-4 (6 layers): route-frozen.json holds the 4-layer router copper of route run 43136394379 (L2 links, L3 copper on
# In2.Cu of the 4-layer stackup); it does not apply to the 6-layer board, whose copper Freerouting routes afresh
FROZEN_APPLIES = len(LAYERS) == 4


def frozen_guard(cu):
    """SHA256 of what the frozen copper depends on: every copper pad (ref, pad, net, centre, layers) and the scripted copper
    made above (before the frozen route goes in). The scripted copper counts by geometry only (id, net, layer, width,
    path, via position and size): its 'why' texts can be corrected without a new harvest (W2 CTRL-R)."""
    pads = sorted(f"{p['ref']}.{p['number']}|{p['net']}|{p['c'][0]:.4f},{p['c'][1]:.4f}|{','.join(p['layers'])}" for p in cu.inp.pads)

    def geometry(item):
        return json.dumps({k: v for k, v in item.items() if k != 'why'}, sort_keys=True)
    scripted = [geometry(t) for t in cu.tracks] + [geometry(v) for v in cu.vias]
    return {'pads_sha256': hashlib.sha256('\n'.join(pads).encode()).hexdigest(),
            'scripted_sha256': hashlib.sha256('\n'.join(scripted).encode()).hexdigest()}


FROZEN_WHY = ('completion of the frozen route (build/kicad/boards/CTRL/route-frozen.json, W2 CTRL-R): grid A* on the locked copper '
              'of route run 43136394379, exact clearance check')


def frozen_copper(cu, log):
    """The frozen route (W2 CTRL-R route study): the router copper of route run 43136394379, harvested and locked, and the
    scripted completion of its open connections, from build/kicad/boards/CTRL/route-frozen.json. It goes in last, so the
    scripted copper and the GND via search above stay exactly as they were in that run; the scripted pieces the
    completion replaces (drop_scripted) are removed by id. Freerouting then finds no open connection to route."""
    if not FROZEN.is_file() or not FROZEN_APPLIES:
        return
    doc = json.loads(FROZEN.read_text(encoding='utf-8'))
    have = frozen_guard(cu)
    for key, value in have.items():  # the frozen copper fits only the placement, netlist and scripted copper it was routed on
        if doc['guard'][key] != value:
            raise SystemExit(f'make_spec: route-frozen.json was routed on another {key} ({doc["guard"][key][:12]}... != '
                             f'{value[:12]}...): route again with [pcb-route CTRL] without the frozen copper and harvest anew')
    for kind, items in (('tracks', cu.tracks), ('vias', cu.vias)):
        for name in doc['drop_scripted'][kind]:
            hits = [t for t in items if t['id'] == name]
            if len(hits) != 1:
                raise SystemExit(f'make_spec: route-frozen.json drops scripted {kind} {name}, found {len(hits)}')
            items.remove(hits[0])
    for prefix, key, why in (('RT', 'router_tracks', None), ('FIN', 'completion_tracks', FROZEN_WHY)):
        for k, (net, layer, width, path) in enumerate(doc[key]):
            t = {'id': f'{prefix}-{k + 1:04d}', 'net': net, 'layer': layer, 'width_mm': width, 'path': path, 'locked': True}
            if why:
                t['why'] = why
            cu.tracks.append(t)
    for prefix, key in (('RV', 'router_vias'), ('FINV', 'completion_vias')):
        for k, (net, x, y, d, drill) in enumerate(doc[key]):
            cu.vias.append({'id': f'{prefix}-{k + 1:04d}', 'net': net, 'at': [x, y], 'drill_mm': drill, 'diameter_mm': d, 'locked': True})
    log(f'  frozen route: {len(doc["router_tracks"])} + {len(doc["completion_tracks"])} tracks, '
        f'{len(doc["router_vias"])} + {len(doc["completion_vias"])} vias')


# ------------------------------------------------------------------ spec texts, router settings, project
LAB5_REFS = []  # W2 CTRL-4: every LAB5 pad sits on copper at the PWR3A class width 1.85 mm, no LAB5 branch_exempt
BG_REFS = ['C342', 'C343']
BRANCH_REASON = {
    'BG': ('E3_BLOWER_GND branch from the scripted 1.85 mm return rail (J314.1 -> D306.2 -> Q305.3) to a capacitor of the blower '
           'supply (C342 bulk, C343 decoupling): ripple current only, no DC path; scripted at 0.4 mm (C342, between the J317 pins '
           '3 and 2, 9.2 mm) and 0.3 mm (C343, between C343 and R363, 9.3 mm): 0.3 mm of 1 oz outer copper carries about 1.0 A at '
           '+10 degC (IPC-2221 external, k 0.048). max_mm 10 bounds the chain to these pieces; the LAB5 pads of C342/C343 sit on '
           '1.85 mm LAB5 copper (W2 CTRL-4), which the 10 mm chain from those pads also lists here'),
}
BRANCH_MIN_WIDTH = {'C342': 0.3, 'C343': 0.3}  # the scripted E3_BLOWER_GND branches
BRANCH_MAX = {'C342': 10.0, 'C343': 10.0}
NECK = ['C318', 'C319', 'D305', 'F301', 'J311', 'J313', 'U315']
CTRL4_RUNS = ''  # route runs of the W2 CTRL-4 probe, filled per run
ROUTER_WHY_6L = (
    ' W2 CTRL-R layer study (6 layers, JLC06161H-2116): route run 43183047190 (In3.Cu and In4.Cu as routing layers) 1 error '
    'and 27 unconnected (3V3_Q6A 16); In4.Cu became a solid 3V3_Q6A plane with a scripted via per SMD pad or scripted group '
    '(3V3_Q6A in class SCRIPTED_GND, not autorouted): route run 43185702454 DRC 0 errors, ignored [], 4 unconnected; route run '
    '43190774090 (with a 1.35 mm F.Cu/B.Cu LAB5 feed of Q304) DRC 0 errors, 4 unconnected (E3_MCP_RESET_N 3, E3_PICO3V3 1). '
    'W2 CTRL-4 on the CTRL-R board-of-record inputs: 6 layers, the 4-layer frozen route (route-frozen.json) does not apply; '
    'the whole right LAB5 group and D306 are fed on B.Cu at the PWR3A class width 1.85 mm without vias (LAB5-FEED-D: J314.2, '
    'under the Pico, D301.2, up the right strip to Q304.2, C320.1 and R367.2; LAB5-FEED-U: J305.3 up the left edge to C321.1, '
    'U315.1 and C322.1), C342/C343 at 1.85 mm too, the L3 run is gone; Q303, R367, C320 and C322 moved for the feed; the '
    'E3_PICO3V3 link up the right strip and the R395 branch run on L4 (In3.Cu), the C312 group joins R335 on L4. Class '
    'PWR3A_BRANCH (LAB5) has the track width 1.85 mm, so any router copper of LAB5 is at the class width.'
    + CTRL4_RUNS)
ROUTER_WHY = (
    'route run 42423914214 (fan-out on, power classes autorouted) stopped at 60 unrouted connections with 20 DRC errors '
    '(dangling fan-out vias, off-centre GND joints, LAB5 with 12 open connections): fan-out off, GND and E3_FAN5 scripted. '
    'Route run 43100344071 (34 min): 2 errors (router tracks too close to the custom Pico GND pads 8 and 13, the DSN '
    'carries the anchor only) and 8 unconnected (5 LAB5 branches): locked GND copper now covers the custom Pico GND pads. '
    'Route runs 43106410728 (a locked L3 LAB5 run across the board) and 43111037016 (LAB5 branches on L3 at 0.6 mm): DRC '
    'errors 0, but the router stalled with 36-37 of the 3V3_Q6A connections open once L3 carried LAB5. LAB5 now uses '
    'short scripted islands (one 18 mm L3 piece to D301) and the router joins them on L1/L4 at 0.5 mm. Route run '
    '43114111838 (that setting): LAB5 complete, DRC errors 0, but 34 of the 3V3_Q6A connections still open: the left '
    'pull-up column R308-R319 now has a scripted 3V3_Q6A bus on L3 with a via beside each pad 2, and the Pico GND vias '
    'sit under the module instead of in the escape channels between and outside the castellated pads. Route run '
    '43118391983 (that setting): 1 error (a router neck at U313.1) and 25 unconnected, 15 of them 3V3_Q6A: the right '
    'pull-up column, the MCP VDD-to-address-pin links and a via for the boxed-in U315.3 are scripted too. Route run '
    '43121860459 (that setting): DRC errors 0 and 22 unconnected (E3_PICO3V3 14, E3_ENC1_A/B 4, E3_BLOWER_GND 2, E3_FN_EXT 1, '
    'E3_ENC2_A 1), most of them at pads that could not leave their row: the pull-up rows R4B and HMI3 have their series '
    'resistors turned and a scripted E3_PICO3V3 bus along the cut-out edge, R344 is turned so that its E3_FN pin sits next '
    'to R343, E3_PICO3V3 has scripted pieces at the Pico, C312, R361/R362, R368 and R395, and E3_BLOWER_GND is fully scripted '
    '(class SCRIPTED_PWR3A). Route run 43131682520 (that setting): 1 error (the R4B bus end dangling) and 13 unconnected '
    '(E3_PICO3V3 8, E3_BACK_EXT 2, E3_FAN_EN 1, E3_GNSS5V 1, 3V3_Q6A 1): the R4B bus now runs up the right strip to J312.4 '
    'with branches to R362 and, on L1, to the HMI3 branch; the HMI pull-ups R337/R339/R341 are joined in the gap between their '
    'pad rows to C312 and U306; the scripted links that walled in BACK_EXT and the PICO column (C312 to R334, Pico pin 36 '
    'around the column) are gone, Pico pin 36 has an escape via. Route run 43136394379 (that setting): 1 error (the '
    'scripted 3V3_Q6A via at U315.3 left dangling) and 15 unconnected (3V3_Q6A 8, E3_PANEL_TEMP 2, E3_CASE_TEMP 2, '
    'E3_PICO3V3 1, E3_Q6A_KEY_GATE 1, E3_REC_EXT 1); five runs gave 13-22 unconnected because every scripted fix moved '
    'Freerouting failures to other nets at the saturated band entrances beside cut-out 1 (W2 CTRL-R study). Its router '
    'copper is now frozen and locked (build/kicad/boards/CTRL/route-frozen.json) and completed by a scripted grid A* pass '
    'with the exact clearance check (build/kicad/boards/CTRL/freeze/freeze_route.py): the V33-U315 via and stub and the '
    'P33-RIGHT-F link are dropped, E3_PICO3V3 crosses the cut-out 1 band on L2 between the vias P33-V-R4B and P33-V-R368, '
    'the router copper of 15 nets is ripped where the completion needed its place (112 of 2278 segments and 14 of 234 vias '
    'with their dangling ends) and those nets are joined again, and L2 carries 5 slow signals where three layers had no '
    'path (E3_PICO3V3 35.6 mm, E3_PICO_SWCLK 21.2 mm, E3_REC_EXT 14.9 mm, PG_BONI 4.7 mm, E3_MARK_EXT 4.4 mm). Freerouting '
    'finds no '
    'open connection of its own to route, so a re-route of the same inputs gives the same copper. CTRL-R route runs: '
    '43189431817 (12 errors: a completion via in the Pico SWCLK pad, whose copper the SMD drill offset moves by 0.8 mm, and '
    '8 track ends off via centres), 43199848180 (2 errors), 43204137006 (6 errors: the Pico TP7 footprint keepout, a '
    'dangling router stub) and 43206372346 (DRC 0 errors, 0 unconnected, ignored [], about 4.5 min; check-mode run '
    '43207377886 green), each with 0 unconnected; Freerouting still adds 69-72 redundant short wires per run, DRC-clean. '
    'After the completion the cut-out 1 band has no spare 0.15 mm crossing on L1/L3/L4 (model): any pad, net or '
    'scripted-copper change stops make_spec at the guard of route-frozen.json and needs a new harvest. Job timeout 34 min '
    'inside the 45 min CI job' + ROUTER_WHY_6L)


def spec_texts(spec, inp, cu, skipped):
    branch = {}
    for r in sorted(set(LAB5_REFS + BG_REFS), key=bg.sort_ref):
        branch[r] = {'max_mm': BRANCH_MAX.get(r, 80.0), 'min_width_mm': BRANCH_MIN_WIDTH.get(r, 0.5), 'reason': BRANCH_REASON['BG']}
    spec['branch_exempt'] = branch
    spec['neck_exempt'] = {r: {'escape_mm': 1.5, 'reason': (
        'pad escape of a PWR1A net (E3_FAN5_P, E3_GNSS5V) into a pad narrower than 0.35 mm plus clearance: a router track may '
        'narrow next to the pad; the class width resumes within the escape length')} for r in NECK}
    spec.pop('cutouts', None)
    spec['edge_keepout'] = {'width_mm': 0.2, 'layers': list(ROUTING), 'blocks': ['tracks', 'vias'],
                            'why': ('rule-area strips (half-width 0.2 mm) on every outline and cut-out edge of the routing layers: '
                                    'Freerouting keeps only its clearance to the edge keepout, less than the copper-to-edge 0.3 mm '
                                    '(route run 42423914214: In2.Cu tracks at 0.28 mm from the left edge; PCB-PWRB lesson)')}
    spec['audit_cutouts'] = True
    spec['layers']['copper'] = 6
    spec['layers']['thickness_mm'] = 1.6
    spec['layers']['source'] = (
        'W2 CTRL-R layer study and W2 CTRL-4: 6 layers, JLC06161H-2116 1.6 mm (pcb/generated/stackup-6l.json and '
        'pcb/rules/jlc-6l-1oz.kicad_dru from pcb/stackup.py; jlcpcb.com/impedance read 2026-11-12): outer 1 oz, inner 0.5 oz. '
        'The contract stackup (mechanical/generated/contract/boards.json: t 1.6, layers 4, JLC04161H-7628) keeps the thickness '
        '1.6 mm the mechanics use; its layer count is the 4-layer default of the other boards')
    spec['holes']['keepout_layers'] = list(LAYERS)
    spec['layers']['types'] = {'In1.Cu': 'power', Q6A_PLANE: 'power'}
    spec['layers']['types_why'] = (
        'In1.Cu (L2) carries a solid GND plane and In4.Cu (L5) a solid 3V3_Q6A plane, both laid before routing and typed power, '
        'so the Specctra export marks them (type power) and Freerouting does not route on them; every SMD GND pad has its own '
        'scripted via to L2, every SMD 3V3_Q6A pad (or scripted 3V3_Q6A group) its own scripted via to L5, THT pads join the '
        'planes directly. Every routing layer faces a solid plane: F.Cu (L1) 0.2234 mm above L2, In2.Cu (L3) 0.3 mm below L2, '
        'In3.Cu (L4) 0.3 mm above L5, B.Cu (L6) 0.2234 mm below L5 (JLC06161H-2116; the SIG/GND/SIG/SIG/PWR/SIG order of the '
        'typical 6-layer stackup on jlcpcb.com/6-layer-pcb, read 2026-11-12, with L3/L4 as signal pair). In3.Cu is the routing '
        'layer the 6-layer stackup adds. Route run 43183047190 (In3.Cu and In4.Cu both routing layers, 3V3_Q6A routed) gave 1 '
        'error and 27 unconnected (3V3_Q6A 16) against 1 and 15 on 4 layers (43136394379), so 3V3_Q6A became a plane. The power '
        'classes route on F.Cu/B.Cu only (router.class_layers), as pcb/check_boards.py requires (netclasses.json: no inner copper '
        'for PWR3A, 1.8 mm inner for PWR1A).')
    spec['pre_route'] = {
        'tracks': cu.tracks,
        'vias': cu.vias,
        'zones': [{'id': 'GND-L2', 'net': 'GND', 'layer': 'In1.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
                   'why': 'solid GND plane L2 (build/15 "План шарів"); every SMD GND pad joins it through its scripted via, every THT '
                          'GND pin directly (solid connection)'},
                  {'id': 'Q6A-L5', 'net': '3V3_Q6A', 'layer': Q6A_PLANE, 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
                   'why': 'solid 3V3_Q6A plane L5 (W2 CTRL-R, 6 layers): the reference plane of L4 and L6 and the 3V3_Q6A supply of the '
                          'MCP23017s, pull-ups and decoupling capacitors; every SMD 3V3_Q6A pad joins it through a scripted via, the THT '
                          'pins J302.1, J304.1, J304.17 and J311.2 directly (solid connection)'}],
        'gnd_vias_note': ('one locked 0.65/0.3 mm through via and a 0.25 mm stub per SMD GND pad, placed by a deterministic search '
                          '(24 directions, growing radius, directions away from the part first) on the exact pad shapes: 0.2 mm to '
                          'other-net copper on every layer the via spans, no via in a pad, 0.55 mm hole-to-hole margin, 0.95 mm '
                          'between vias, outside the hole keepouts, the Pico TP keepouts and 0.35 mm from every edge; the Pico GND pins get their via '
                          'straight inwards under the module, past the pad end; GND is in '
                          'class SCRIPTED_GND and not autorouted (route run 42423914214: the router left 9 GND connections and '
                          'dangling fan-out vias). 6 layers (W2 CTRL-R): the same search gives every SMD 3V3_Q6A pad, or one pad of a '
                          'scripted 3V3_Q6A group (right pull-up column, U302, U303, the C302-C306 row), a via to the L5 plane after '
                          'the GND vias (ids V33P-*); the left pull-up column and U315.3 keep their scripted vias'),
        'gnd_vias_skipped': skipped,
    }
    pz = {z['layer']: z for z in spec['post_route_zones']}
    for layer, zid in (('In3.Cu', 'GND-L4'),):  # the routing layer the 6-layer stackup adds
        pz.setdefault(layer, {'id': zid, 'net': 'GND', 'layer': layer, 'outline': 'board', 'priority': 0})
    spec['post_route_zones'] = [pz[n] for n in ROUTING]
    if FROZEN.is_file() and FROZEN_APPLIES:
        spec['pre_route']['frozen_route_note'] = (
            'W2 CTRL-R route study: the tracks RT-* and vias RV-* are the router copper of route run 43136394379 (Freerouting 2.5.0, '
            'inputs sha256 fd468b58...), harvested from that run board and locked; the tracks FIN-* and vias FINV-* complete its 15 '
            'open connections (grid A* on the locked copper, exact clearance check 0.15 mm, 0.3 mm to edges, 0.5 mm hole to hole, '
            'track ends on via centres; router copper of 15 nets ripped where needed and joined again; L2 only where three layers '
            'had no path). Tool: build/kicad/boards/CTRL/freeze/freeze_route.py (numpy, offline). '
            'Source: build/kicad/boards/CTRL/route-frozen.json. Valid only for this placement, netlist and scripted copper '
            '(guard: SHA256 of the pads and of the scripted copper geometry, texts excluded): a pad, net or scripted-copper '
            'change needs a new route run and a new harvest. CI/model result, not a hardware PASS')
    for z in spec['post_route_zones']:
        z['pad_connection'] = 'solid'
        z['why'] = 'GND pour after routing; solid pad connection (thermal spokes of THT GND pins starve between pins, PCB-PWRB lesson)'
    spec['router'] = {
        'tool': 'freerouting', 'max_passes': 60, 'threads': 1, 'job_timeout': '00:34:00', 'timeout_s': 2160,
        'fanout': False,
        'ignore_net_classes': ['SCRIPTED_GND', 'SCRIPTED_PWR3A'],  # GND, E3_FAN5, E3_BLOWER_GND
        'class_layers': {'PWR1A': ['F.Cu', 'B.Cu'], 'PWR3A_BRANCH': ['F.Cu', 'B.Cu']},
        'why': ROUTER_WHY,
        'class_layers_why': ('KiCad 10.0.7 exports no per-class layer list; board_gen writes (use_layer F.Cu B.Cu) into the DSN '
                             'classes PWR1A and PWR3A_BRANCH (Freerouting 2.5.0 Circuit.java / Network.java), so no router power copper '
                             'lands on the inner layers'),
    }
    ho = spec['heights_open']
    ho['J304'] = ('XDFH-0254-2*20P (C19193815) drawing not readable (mechanical/params/parts.json IDC_top h_src): height not '
                  'checked here; the reference 2x20 box header Würth 61204021621 (9.1 mm above the PCB) is below every bottom zone '
                  'J304 occupies (12.98-17.98 mm after the W2 MECH-4 HDMI route, contract rear_zones), so only the J304 part read '
                  'stays OPEN; the mated height with the IDC socket and the ribbon is not read either (TBD, mechanical/params/'
                  'parts.json IDC_top): the hdmi_insert zone (x 34.5-50, y 21-39) the J304 courtyard crosses allows 12.98 mm, '
                  'which leaves 3.88 mm above the 9.1 mm reference body for socket and ribbon, unchecked: OPEN for MECH '
                  '(W2 CTRL-R, review CTRL-9)')
    spec['heights']['D304'] = 9.6
    spec['heights_src']['D304'] = (
        'Kingbright WP7113LSECK/J3 data sheet (DSAN8286 / 1101033255, rev V.5A, 03/25/2025) p.1 package dimensions: 8.6 mm from '
        'the lens top to the lead-side face of the 1 mm flange, plus "1.0Max." of body past the flange on the lead side, so the '
        'seated height is up to 9.6 mm (worst case, used here; review CTRL-8), '
        'https://www.kingbrightusa.com/images/catalog/SPEC/WP7113LSECK-J3.pdf read 2026-11-07 and again 2026-11-12 (W2 CTRL-R; '
        'page rendered with PyMuPDF)')
    spec['heights_src']['BZ301'] = (
        'Same Sky CPT-1207-3TH data sheet (rev 1.01, 11/02/2026) p.1 dimensions "Ø12.5 x 7.0 mm", p.2 mechanical drawing '
        '"tolerance: ±0.5 mm" (7.5 mm worst case against bms fits_mm 7.48: OPEN for MECH, review CTRL-8), '
        'https://www.sameskydevices.com/product/resource/cpt-1207-3th.pdf read 2026-11-07 and again 2026-11-12 (W2 CTRL-R; '
        'PDF text read with PyMuPDF)')
    ho['J313'] = ('Molex KK 254 22-27-2031 vertical header with the Noctua housing: height not read (mechanical/params/parts.json '
                  'FAN3 TBD); placed over the bottom zones x 37-46 y 68.5-83 (15.98 / 17.98 mm) with its courtyard below the lime band '
                  '(y >= 83, 4.98 mm), not checked here')
    if 'Iteration 2' not in spec['note']:
        spec['note'] = spec['note'].replace(
            'CI/model output', 'Iteration 2: scripted LAB5 feed, blower return and fan copper, GND plane vias, fan cluster re-placed. CI/model output')
    zones = []
    for z in inp.contract['height_zones']:
        x, y, w, h = z['rect']
        zones.append({'region': [x, y, w, h], 'side': 'top', 'max_height_mm': round(min(z['fits_mm'], z['max_height']), 3),
                      'why': f"top: min(contract max_height {z['max_height']}, fits_mm {z['fits_mm']}) under {z['limit']}"})
    for z in inp.contract['rear_zones']:
        x, y, w, h = z['rect']
        zones.append({'region': [x, y, w, h], 'side': 'bottom', 'max_height_mm': z['fits_mm'],
                      'why': f"bottom: contract rear_zones fits_mm {z['fits_mm']} over {z['limit']}"})
    spec['height_zones'] = zones  # from the current contract (rear zones changed with the W2 MECH-4 HDMI route)
    spec['rules_note'] = (
        'Rules live in the committed CTRL.kicad_pro: the project defaults of pcb/generated/netclasses.json project_defaults '
        '(track 0.15 / clearance 0.15, copper-edge 0.3, hole-hole 0.5, hole clearance 0.25, text 1.0 / 0.15) with router vias '
        '0.7 / 0.3 (0.6 mm vias at 0.15 mm clearance sit 0.45 mm hole to hole, PCB-PWRB lesson), and the classes PWR1A (0.35 mm: '
        'E3_FAN5_P, E3_GNSS5V), PWR3A_BRANCH (LAB5: 1.85 mm since W2 CTRL-4, the PWR3A class width; every LAB5 pad is reached '
        'by scripted copper), SCRIPTED_GND (GND and, on 6 layers, the plane net 3V3_Q6A) and '
        'SCRIPTED_PWR3A (E3_FAN5, E3_BLOWER_GND), the last two not autorouted. check_boards widths follow netclasses.json (LAB5, E3_BLOWER_GND, '
        'E3_FAN5: PWR3A 1.85 mm outer; the E3_BLOWER_GND capacitor branches in branch_exempt). rules_file stays null (board_gen '
        'does not copy .kicad_dru files yet); the 6-layer rule file of the same defaults is pcb/rules/jlc-6l-1oz.kicad_dru (W2 CTRL-R).')
    spec['fab_floor']['source'] = (
        'https://jlcpcb.com/capabilities/pcb-capabilities read 2026-11-07, multilayer values (pcb/generated/netclasses.json '
        'fab_floor.jlc_4l_1oz); re-read 2026-11-12 for 6 layers: unchanged (pcb/generated/stackup-6l.json capabilities)')
    spec['layers']['plan'] = {
        'F.Cu': 'L1: top parts, signals, scripted LAB5 trunk J305 -> J314.2 (1.85 mm) and the 1.85 mm C342 branch to its four vias, scripted 3V3_Q6A pieces (right pull-up column, MCP pins, the C302-C306 row, stubs to the L5 plane vias), scripted E3_PICO3V3 pieces (HMI2/HMI3 bus along cut-out 1 to the L4 link via, R334/R335, the HMI pull-up row to C312 and U306, R361/R362), PWR1A routes, GND pour after routing',
        'In1.Cu': 'L2: GND plane (pre-route zone, DSN plane), no signals',
        'In2.Cu': 'L3: signals, GND pour after routing (no LAB5 copper since W2 CTRL-4)',
        'In3.Cu': 'L4 (added by the 6-layer stackup, W2 CTRL-R): signals, the scripted E3_PICO3V3 link up the right strip (between the J316 pins, past C302/C304, beside the cut-out 1 edge to the via at the HMI bus end) with its branch to R395, the C312-R335 link, GND pour after routing',
        'In4.Cu': 'L5 (added by the 6-layer stackup, W2 CTRL-R): solid 3V3_Q6A plane (pre-route zone, DSN plane), no signals',
        'B.Cu': 'L6: bottom parts, signals, scripted E3_BLOWER_GND rail and E3_FAN5 (1.85 mm) and the E3_BLOWER_GND capacitor '
                'branches, the 1.85 mm LAB5 feeds of W2 CTRL-4 (LAB5-FEED-D: J314.2, D306, under the Pico, D301, up the right strip '
                'to C320/R367/Q304; LAB5-FEED-U: J305.3 up the left edge to C321/U315/C322; C343, C342), scripted E3_PICO3V3 pieces '
                '(R4B bus along cut-out 2, up the right strip and along the top edge to J312.4, branch to R362; Pico pin 36 escape '
                'via, R330/R327/C308), locked GND copper over the custom Pico GND pads, PWR1A routes, GND pour after routing'}
    ce = spec['cable_exits']
    key_old = 'vertical, over the plate zone x 37-50 y 68.5-83 (bottom side)'
    if key_old in ce:
        spec['cable_exits'] = {('vertical, over the plate zones x 37-44 y 73.9-82.6, below the lime band (bottom side)'
                                if k == key_old else k): v for k, v in ce.items()}


def project_json(project):
    pro = copy.deepcopy(project)
    ns = pro['net_settings']
    base = copy.deepcopy(ns['classes'][0])
    assert base['name'] == 'Default'

    def cls(name, width, prio):
        c = copy.deepcopy(base)
        c['name'], c['track_width'], c['priority'] = name, width, prio
        c['via_diameter'], c['via_drill'] = 0.7, 0.3
        return c
    ns['classes'][0]['track_width'] = 0.15
    ns['classes'][0]['via_diameter'] = 0.7
    ns['classes'][0]['via_drill'] = 0.3
    ns['classes'] = [ns['classes'][0], cls('PWR1A', 0.35, 0), cls('PWR3A', 1.85, 1), cls('PWR3A_BRANCH', 1.85, 2),
                     cls('SCRIPTED_GND', 0.15, 3), cls('SCRIPTED_PWR3A', 1.85, 4)]
    ns['netclass_patterns'] = [{'netclass': 'PWR3A_BRANCH', 'pattern': 'LAB5'},
                               {'netclass': 'SCRIPTED_PWR3A', 'pattern': 'E3_BLOWER_GND'},
                               {'netclass': 'SCRIPTED_PWR3A', 'pattern': 'E3_FAN5'},
                               {'netclass': 'PWR1A', 'pattern': 'E3_FAN5_P'},
                               {'netclass': 'PWR1A', 'pattern': 'E3_GNSS5V'},
                               {'netclass': 'SCRIPTED_GND', 'pattern': 'GND'},
                               {'netclass': 'SCRIPTED_GND', 'pattern': '3V3_Q6A'}]  # W2 CTRL-R: plane net, scripted vias, not autorouted
    return json.dumps(pro, ensure_ascii=False, indent=2) + '\n'


def build(log):
    spec = json.loads(SPEC.read_text(encoding='utf-8'))
    project = json.loads(PROJECT.read_text(encoding='utf-8'))
    edit_placement(spec)
    inp = Inputs(spec)
    cu, skipped = scripted_copper(inp, log)
    spec_texts(spec, inp, cu, skipped)
    return json.dumps(spec, ensure_ascii=False, indent=2) + '\n', project_json(project), cu, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true', help='regenerate in memory and compare with the committed files')
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    log = (lambda *a: None) if args.quiet else print
    spec_text, project_text, cu, skipped = build(log)
    print(f'{len(cu.tracks)} scripted tracks, {len(cu.vias)} scripted vias, GND pads without a via: {skipped}')
    if args.check:
        bad = [p for p, text in ((SPEC, spec_text), (PROJECT, project_text)) if p.read_text(encoding='utf-8') != text]
        for p in bad:
            print(f'make_spec: {p.relative_to(BASE).as_posix()} is stale')
        return 1 if bad else 0
    for p, text in ((SPEC, spec_text), (PROJECT, project_text)):
        p.write_text(text, encoding='utf-8', newline='\n')
        print('wrote', p.relative_to(BASE).as_posix())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
