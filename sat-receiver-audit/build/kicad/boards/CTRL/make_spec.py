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
    the texts that describe them;
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
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']  # 6 layers, JLC06161H-2116 (W2 CTRL-R)
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
    'D304': (anchor((48.04, 68.81), 0), 'bottom over the zones x 43.5-50 y 65.6-72 (15.98 / 17.98 mm >= 8.6 mm LED), between '
             'J304 (y <= 65.51) and J313; its pins + 1.0 mm stay clear of the top parts'),
    'F301': (anchor((48.0, 79.4), 270), FAN_NOTE),
    'Q304': (anchor((48.0, 84.3), 270), FAN_NOTE),
    'C320': (anchor((48.2, 87.3), 0), FAN_NOTE),
    'R367': (anchor((45.4, 85.5), 90), FAN_NOTE),
    'Q303': (anchor((42.0, 85.0), 180), FAN_NOTE),
    'R365': (anchor((38.5, 85.0), 90), FAN_NOTE),
    'R366': (anchor((38.6, 88.0), 0), FAN_NOTE),
    'C318': (anchor((47.6, 74.6), 0), FAN_NOTE),
    'D305': (anchor((40.6, 91.6), 0), FAN_NOTE),
    'C319': (anchor((46.5, 91.6), 0), FAN_NOTE),
    'D306': (anchor((14.5, 56.3), 0), BLOWER_NOTE),
    'Q305': (anchor((20.23, 56.4), 0), BLOWER_NOTE),
}
U315_SOURCE = 'bottom strip between the cut-outs, above cut-out 1 (GNSS 5 V switch next to its capacitors)'


def edit_placement(spec):
    for p in spec['parts']:
        if p['ref'] in ANCHORS:
            p['anchor'], p['anchor_source'] = copy.deepcopy(ANCHORS[p['ref']][0]), ANCHORS[p['ref']][1]
        if p['ref'] == 'U315':
            p['anchor_source'] = U315_SOURCE
    groups = []
    for g in spec['groups']:
        if g['id'] in ('FAN', 'FAN2', 'BLOWER'):
            continue
        if g['id'] == 'FAN3':
            g['region'] = [37.05, 68.6, 43.4, 73.9]
            g['members'] = [m for m in g['members'] if m['ref'] != 'R366']
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
             'E3_BLOWER_GND return; locked, pad centre to pad centre, so Freerouting adds only the 0.5 mm PWR3A_BRANCH '
             'branches to the other LAB5 pads')
    cu.track('BLOWER-GND-RAIL', 'E3_BLOWER_GND', 'B.Cu', 1.85,
             [J314_1, (D306_2[0], YB), (Q305_3[0], YB), Q305_3],
             'blower return J314.1 to the low-side switch Q305 drain at the PWR3A width (pad centre to pad centre)')
    cu.track('BLOWER-GND-D306', 'E3_BLOWER_GND', 'B.Cu', 1.85, [(D306_2[0], YB), D306_2],
             'flyback diode D306 anode on the blower return at the PWR3A width')
    cu.track('FAN5-Q304-F301', 'E3_FAN5', 'B.Cu', 1.85, [Q304_3, F301_1],
             'fan switch Q304 drain to the PTC F301 at the PWR3A width (one segment, pad centre to pad centre)')

    # LAB5 branches (route run 43100344071 left 5 LAB5 connections open with router branches)
    D306_1, C342_1 = P('D306', '1')['c'], P('C342', '1')['c']
    U315_1, C321_1 = P('U315', '1')['c'], P('C321', '1')['c']
    Q304_2, C320_1, R367_2 = P('Q304', '2')['c'], P('C320', '1')['c'], P('R367', '2')['c']
    YD = 54.65  # below D306 and Q305, above the Pico pads
    cu.track('LAB5-D306', 'LAB5', 'B.Cu', 0.6, [J314_2, (10.6, YD), (D306_1[0], YD), D306_1],
             BR + 'D306): J314.2 to the flyback diode cathode below the D306 body; low current (transient only)')
    cu.track('LAB5-C343', 'LAB5', 'B.Cu', 0.6, [J305_4, P('C343', '1')['c']], BR + 'C343): decoupling capacitor next to J305.4')
    cu.track('LAB5-C342-F', 'LAB5', 'F.Cu', 0.6, [(XL, 64.5), (21.9, 64.5)],
             BR + 'C342): from the F.Cu feed above the J317 pins to a via next to C342')
    cu.via('LAB5-V-C342', 'LAB5', (21.9, 64.5), BR + 'C342): F.Cu to B.Cu')
    cu.track('LAB5-C342-B', 'LAB5', 'B.Cu', 0.6, [(21.9, 64.5), (21.9, 66.4), C342_1], BR + 'C342): via to the C342 LAB5 pad')
    # LAB5 islands without vias: route run 43106410728 with a scripted L3 run (J305.3 -> U315 -> fan -> D301) left 36 of
    # the 3V3_Q6A connections open (the run walled off L3); the router joins the islands in class PWR3A_BRANCH
    cu.track('LAB5-U315', 'LAB5', 'B.Cu', 0.6, [U315_1, (U315_1[0], 97.3), (26.2, 97.3), (26.2, 99.87), C321_1],
             BR + 'U315, C321): GNSS switch input and its capacitor, U315.1 left from above')
    cu.track('LAB5-FAN', 'LAB5', 'B.Cu', 0.6, [R367_2, (R367_2[0], 88.7), (C320_1[0], 88.7), C320_1],
             BR + 'R367, C320): fan switch gate pull-up and source capacitor, above C320')
    cu.track('LAB5-Q304', 'LAB5', 'B.Cu', 0.6, [C320_1, Q304_2], BR + 'Q304): fan switch source')
    return {'D306_1': D306_1, 'YD': YD}


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
    # U315 pin 3 (3V3_Q6A) is boxed in by the cut-out edge, U315 pin 2's GND stub and the U301 pads above
    cu.via('V33-U315', '3V3_Q6A', (27.5, 94.45), '3V3_Q6A via for U315 pin 3, right of the U301 pads')
    cu.track('V33-U315', '3V3_Q6A', 'B.Cu', 0.25, [P('U315', '3')['c'], (27.5, 94.45)], '3V3_Q6A stub, U315.3 to its via')


Q6A_PLANE = 'In4.Cu'  # W2 CTRL-R: L5 is a solid 3V3_Q6A plane (type power); its SMD pads reach it through scripted vias
# 3V3_Q6A pads already joined by scripted copper: one plane via per group is enough (the first pad that finds a spot)
Q6A_GROUPS = [('R392', 'R325', 'R324', 'R323', 'R322', 'R321', 'R320', 'R302', 'R301'), ('U303',), ('U302',)]
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
    cu.track('P33-HMI-BUS', P33, 'F.Cu', W, [r345['c'], (xr, r345['c'][1]), (xr, y3), (xe, y3), (xe, 70.3)],
             'E3_PICO3V3: R345.2 right of the HMI2 column, then the bus between the HMI3 pull-up pads and the cut-out 1 edge')
    cu.track('P33-R343', P33, 'F.Cu', W, [r343['c'], (r343['c'][0], y3), (xr, y3)], 'E3_PICO3V3 stub, R343.2 to the bus')
    for r in ('R347', 'R349'):
        p = P(r, '2')
        cu.track(f'P33-{r}', P33, 'F.Cu', W, [p['c'], (p['c'][0], y3)], f'E3_PICO3V3 stub, {r}.2 to the bus')
    cu.track('FN-R343-R344', 'E3_FN', 'F.Cu', W, [P('R343', '1')['c'], P('R344', '1')['c']],
             'E3_FN: pull-up R343 to series resistor R344 (adjacent pads of the HMI2 column)')
    for rs, rp in (('R348', 'R347'), ('R350', 'R349')):
        a, b = P(rs, '1'), P(rp, '1')
        assert a['net'] == b['net']
        cu.track(f'PRESS-{rs}-{rp}', a['net'], 'F.Cu', W, [a['c'], b['c']],
                 f'{a["net"]}: series resistor {rs} (upper pad) to pull-up {rp} (lower pad), diagonal between the pad rows')
    # on to the fan-tach pull-up R368 (bottom side, via above it) and the MCP reset pull-up R395 (top side)
    vx, vy = 38.6, 74.3
    cu.track('P33-R368-F', P33, 'F.Cu', W, [(xe, 70.3), (vx, 71.7), (vx, vy)], 'E3_PICO3V3 from the HMI3 bus to a via above R368')
    cu.via('P33-V-R368', P33, (vx, vy), 'E3_PICO3V3: F.Cu to B.Cu above R368, left of J313.1')
    cu.track('P33-R368-B', P33, 'B.Cu', W, [(vx, vy), P('R368', '2')['c']], 'E3_PICO3V3: via to R368.2')
    r395 = P('R395', '1')
    cu.track('P33-R395', P33, 'F.Cu', W, [(xe, 70.3), (r395['c'][0], 70.3), r395['c']],
             'E3_PICO3V3 from the HMI3 bus to R395.1, above the D304 pins')
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
    cu.track('P33-RIGHT-F', P33, 'In3.Cu', W, [(xd, 109.6), (40.55, 104.5), (40.55, 101.0), (39.235, 97.0), (39.235, 89.5), (vx, 88.8), (vx, vy)],
             'E3_PICO3V3 from the right-strip bus between the J316 pins 2 and 1, past C302/C304, then down beside the cut-out 1 edge to '
             'the via above R368 (route runs 43121860459 and 43131682520 left this link open); on L4 (In3.Cu) since the 6-layer '
             'stackup (W2 CTRL-R), so that the F.Cu pad C302.1 (3V3_Q6A) is not boxed in and gets its plane via')
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
    pw = power_copper(cu)
    log('Pico custom pad covers')
    pico_covers(cu)
    log('GND plane vias and 3V3_Q6A pieces')
    gnd_smd = [p for p in inp.pads if p['net'] == 'GND' and p['kind'] == 'smd' and p['number']]
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
    # LAB5 to the Pico VSYS diode D301 on B.Cu below D306/Q305, after the GND vias of the SOT-23-6 middle pins above it
    D306_1, YD = pw['D306_1'], pw['YD']
    D301_2 = cu.pad('D301', '2')['c']
    cu.via('LAB5-V-D306', 'LAB5', (D306_1[0], YD), BR + 'D301): B.Cu below D306 to L3')
    cu.track('LAB5-L3-D301', 'LAB5', 'In2.Cu', 0.6, [(D306_1[0], YD), (D306_1[0], 56.4), (34.6, 56.4)],
             BR + 'D301): short L3 run below cut-out 1, under the blower switch and the buzzer (Pico VSYS current only)')
    cu.via('LAB5-V-D301', 'LAB5', (34.6, 56.4), BR + 'D301): L3 to B.Cu above D301')
    cu.track('LAB5-D301', 'LAB5', 'B.Cu', 0.6, [(34.6, 56.4), (D301_2[0], 55.1), D301_2], BR + 'D301): via to the D301 LAB5 pad')
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
    return cu, skipped


# ------------------------------------------------------------------ spec texts, router settings, project
LAB5_REFS = ['C320', 'C321', 'C322', 'C342', 'C343', 'D301', 'D306', 'Q304', 'R367', 'U315']
BG_REFS = ['C342', 'C343']
BRANCH_REASON = {
    'LAB5': ('LAB5 branch from the scripted 1.85 mm feed (J305 -> J314.2) to a low-current load: scripted pieces at D306, '
             'C342, C343, U315/C321, C320/R367/Q304 and D301 (a 0.6 mm L3 run of 18 mm below cut-out 1), joined by Freerouting in '
             'class PWR3A_BRANCH at 0.5 mm on L1/L4. Besides the blower (fed by the 1.85 mm feed) the CTRL loads on LAB5 are U315 '
             '(limit 0.144-0.192 A, RILIM 162k), the fan switch Q304 (E3_FAN5 0.25 A continuous, tools/assembly_data.py '
             'NET_CURRENT via pcb/generated/netclasses.json), the Pico VSYS diode D301 and decoupling capacitors (no DC current): '
             'a branch carries at most 0.44 A plus the Pico VSYS current; 0.5 mm of 1 oz outer copper carries about 1.45 A at '
             '+10 degC (IPC-2221 external, k 0.048), and the L3 run to D301 carries the Pico VSYS current only. A short at the '
             'end of a branch (a capacitor failing short, or the E3_FAN5 node between Q304 and F301) drives the current of the '
             'upstream fuse F102 (4 A, holds its rating) through 0.5 mm copper (about +100 degC by IPC-2221): a recorded layout '
             'deviation from the PWR3A sizing of netclasses.json, not a bench gate (build/15 "Гілки LAB5 на CTRL (W2 PCB-CTRL)")'),
    'BG': ('E3_BLOWER_GND branch from the scripted 1.85 mm return rail (J314.1 -> D306.2 -> Q305.3) to a capacitor of the blower '
           'supply (C342 bulk, C343 decoupling): ripple current only, no DC path; scripted at 0.4 mm (C342, between the J317 pins '
           '3 and 2) and 0.3 mm (C343, between C343 and R363): 0.3 mm of 1 oz outer copper carries about 1.0 A at +10 degC '
           '(IPC-2221 external, k 0.048)'),
}
BRANCH_MIN_WIDTH = {'C342': 0.3, 'C343': 0.3}  # the scripted E3_BLOWER_GND branches; LAB5 branches stay >= 0.5 mm
FAN_FEED = ('fan switch Q304 source on LAB5: E3_FAN5 (Q304 drain to F301) is sized for the F102 4 A protective current '
            '(netclasses.json PWR3A, Q304 has no current limit), but the LAB5 feed of Q304 is this branch: the deviation is '
            'recorded in build/15 "Гілки LAB5 на CTRL (W2 PCB-CTRL)". ')
NECK = ['C318', 'C319', 'D305', 'F301', 'J311', 'J313', 'U315']
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
    'around the column) are gone, Pico pin 36 has an escape via. Job timeout 34 min inside the 45 min CI job. '
    'W2 CTRL-R layer study: route run 43136394379 (1 error, 15 unconnected, 3V3_Q6A 8) on 4 layers; the board goes to 6 layers '
    '(JLC06161H-2116). Route run 43183047190 (In3.Cu and In4.Cu as routing layers, placement and scripted copper unchanged): '
    '1 error (the U315.3 via dangling) and 27 unconnected (3V3_Q6A 16, E3_CASE_TEMP 3, E3_PICO3V3 2, six nets 1 each); Freerouting '
    'stopped after 21 passes (no gain since pass 11, 10.5 min). In4.Cu is now a solid 3V3_Q6A plane with a scripted via per SMD '
    'pad or scripted group, and 3V3_Q6A sits in class SCRIPTED_GND (not autorouted)')


def spec_texts(spec, inp, cu, skipped):
    branch = {}
    for r in sorted(set(LAB5_REFS + BG_REFS), key=bg.sort_ref):
        nets = (['LAB5'] if r in LAB5_REFS else []) + (['E3_BLOWER_GND'] if r in BG_REFS else [])
        reason = ' '.join(BRANCH_REASON['LAB5' if n == 'LAB5' else 'BG'] for n in nets)
        if r == 'D306':
            reason = ('flyback diode D306 cathode on LAB5: it conducts the blower current only while the coil current decays after '
                      'Q305 turns off (ms); ' + BRANCH_REASON['LAB5'])
        if r in ('Q304', 'C320', 'R367'):
            reason = FAN_FEED + reason
        branch[r] = {'max_mm': 80.0, 'min_width_mm': BRANCH_MIN_WIDTH.get(r, 0.5), 'reason': reason}
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
        'W2 CTRL-R layer study: 6 layers, JLC06161H-2116 1.6 mm (pcb/generated/stackup-6l.json and pcb/rules/jlc-6l-1oz.kicad_dru '
        'from pcb/stackup.py; jlcpcb.com/impedance read 2026-11-12): outer 1 oz, inner 0.5 oz. The contract stackup '
        '(mechanical/generated/contract/boards.json: t 1.6, layers 4, JLC04161H-7628) keeps the thickness 1.6 mm the mechanics '
        'use; its layer count is the 4-layer default of the other boards')
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
                          'scripted 3V3_Q6A group (right pull-up column, U302, U303), a via to the L5 plane after the GND vias '
                          '(ids V33P-*); the left pull-up column and U315.3 keep their scripted vias'),
        'gnd_vias_skipped': skipped,
    }
    pz = {z['layer']: z for z in spec['post_route_zones']}
    for layer, zid in (('In3.Cu', 'GND-L4'),):  # the routing layer the 6-layer stackup adds
        pz.setdefault(layer, {'id': zid, 'net': 'GND', 'layer': layer, 'outline': 'board', 'priority': 0})
    spec['post_route_zones'] = [pz[n] for n in ROUTING]
    for z in spec['post_route_zones']:
        z['pad_connection'] = 'solid'
        z['why'] = 'GND pour after routing; solid pad connection (thermal spokes of THT GND pins starve between pins, PCB-PWRB lesson)'
    spec['router'] = {
        'tool': 'freerouting', 'max_passes': 60, 'threads': 1, 'job_timeout': '00:34:00', 'timeout_s': 2160,
        'fanout': False,
        'ignore_net_classes': ['SCRIPTED_GND', 'SCRIPTED_PWR3A'],  # GND, 3V3_Q6A (plane, W2 CTRL-R), E3_FAN5, E3_BLOWER_GND
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
                  'stays OPEN')
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
        'E3_FAN5_P, E3_GNSS5V), PWR3A_BRANCH (0.5 mm router branches of LAB5), SCRIPTED_GND (GND and, on 6 layers, the plane net 3V3_Q6A) and '
        'SCRIPTED_PWR3A (E3_FAN5, E3_BLOWER_GND), the last two not autorouted. check_boards widths follow netclasses.json (LAB5, E3_BLOWER_GND, '
        'E3_FAN5: PWR3A 1.85 mm outer, branches in branch_exempt). rules_file stays null (board_gen does not copy .kicad_dru '
        'files yet); the 6-layer rule file of the same defaults is pcb/rules/jlc-6l-1oz.kicad_dru (W2 CTRL-R).')
    spec['fab_floor']['source'] = (
        'https://jlcpcb.com/capabilities/pcb-capabilities read 2026-11-07, multilayer values (pcb/generated/netclasses.json '
        'fab_floor.jlc_4l_1oz); re-read 2026-11-12 for 6 layers: unchanged (pcb/generated/stackup-6l.json capabilities)')
    spec['layers']['plan'] = {
        'F.Cu': 'L1: top parts, signals, scripted LAB5 feed J305 -> J314.2 (1.85 mm) and C342 branch, scripted 3V3_Q6A pieces (right pull-up column, MCP pins, stubs to the L5 plane vias), scripted E3_PICO3V3 pieces (HMI2/HMI3 bus along cut-out 1 to R368/R395, the HMI pull-up row to C312 and U306, R361/R362), PWR1A/PWR3A_BRANCH routes, GND pour after routing',
        'In1.Cu': 'L2: GND plane (pre-route zone, DSN plane), no signals',
        'In2.Cu': 'L3: signals, the scripted 18 mm LAB5 run to D301 below cut-out 1, GND pour after routing',
        'In3.Cu': 'L4 (added by the 6-layer stackup, W2 CTRL-R): signals, the scripted E3_PICO3V3 link up the right strip (between the J316 pins, past C302/C304, beside the cut-out 1 edge to the via above R368), GND pour after routing',
        'In4.Cu': 'L5 (added by the 6-layer stackup, W2 CTRL-R): solid 3V3_Q6A plane (pre-route zone, DSN plane), no signals',
        'B.Cu': 'L6: bottom parts, signals, scripted E3_BLOWER_GND rail and E3_FAN5 (1.85 mm) and the E3_BLOWER_GND capacitor '
                'branches, scripted LAB5 islands, scripted E3_PICO3V3 pieces (R4B bus along cut-out 2, up the right strip and along the top '
                'edge to J312.4, branch to R362; Pico pin 36 escape via, R330/R327/C308), '
                'locked GND copper over the custom Pico GND pads, PWR1A/PWR3A_BRANCH routes, GND pour after routing'}
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
    ns['classes'] = [ns['classes'][0], cls('PWR1A', 0.35, 0), cls('PWR3A', 1.85, 1), cls('PWR3A_BRANCH', 0.5, 2),
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
