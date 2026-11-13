#!/usr/bin/env python3
"""Board spec generator of the CTRL board (W2 PCB-CTRL). Standard library only.

Run from any directory:
  python build/kicad/boards/CTRL/make_spec.py           rewrite pcb/boards/CTRL.json and build/kicad/boards/CTRL/CTRL.kicad_pro
  python build/kicad/boards/CTRL/make_spec.py --check   regenerate in memory and compare with the committed files

The base is the committed pcb/boards/CTRL.json itself (parts, instances, holes, groups, heights, sides, cable exits);
this script owns the keys it rewrites and recomputes them every run, so a second run changes nothing:
  * the anchors of the fan cluster, the blower switch, J313, D304, the right LAB5 group, the blower capacitors and the
    R4B encoder resistor block (ANCHORS), and the placement groups it replaces (FAN, FAN2, BLOWER, BLOWER2, GNSS_IN, R4B;
    FAN3 keeps three resistors);
  * the scripted, locked copper (pre_route): every LAB5 piece (W2 CTRL-4: 1.85 mm outer), the E3_BLOWER_GND return and
    its capacitor bars, E3_FAN5, E3_FAN5_P, the 3V3_Q6A pieces, the E3_PICO3V3 pieces, the encoder lines of the R4B block, GND copper over
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
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']


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
BLOWER2_NOTE = ('bottom row below cut-out 1 left of the LAB5 feed vias, x 11-20 y 64-68.2 (W2 CTRL-4; was group BLOWER2: '
                'C342/C343 now sit between a 1.85 mm LAB5 bar at y 67.01 and a 1.85 mm E3_BLOWER_GND bar at y 64.95)')
ANCHORS = {
    'J313': (anchor((40.43, 75.7), 90), 'bottom, vertical KK over the plate zones x 37-46 y 68.5-83 (15.98 / 17.98 mm); '
             'courtyard y 73.93-82.55, below the lime band (y >= 83, 4.98 mm); its pin field + 1.0 mm (x <= 42.53) stays clear '
             'of the top TR3B parts; next to the fan switch'),
    'D304': (anchor((48.04, 68.81), 0), 'bottom over the zones x 43.5-50 y 65.6-72 (15.98 / 17.98 mm >= 9.85 mm LED, worst '
             'case of the 8.6 mm body with its +-0.25 mm drawing tolerance plus up to 1.0 mm past the flange; W2 CTRL-4, '
             'review RV-CTRLR-6), between J304 (y <= 65.51) and J313; its pins + 1.0 mm '
             'stay clear of the top parts'),
    'F301': (anchor((48.0, 79.4), 270), FAN_NOTE),
    'Q304': (anchor((47.77, 84.3005), 270), FAN_NOTE + '; W2 CTRL-4: 0.23 mm left of the board-of-record place so that the '
             '1.85 mm LAB5 feed ends at the centre of Q304.2 (0.355 mm from the right board edge) and Freerouting sees the pad '
             'joined, while Q304.1 keeps room for its gate via; y 84.3005 puts the Q304.2 centre on the 1 um grid of the '
             'Specctra export'),
    'C320': (anchor((48.4, 88.1), 90), FAN_NOTE + '; W2 CTRL-4: above Q304, its LAB5 pad 1 on the 1.85 mm LAB5 feed (y 87.15) '
             'that turns down into Q304.2'),
    'R367': (anchor((46.65, 87.975), 270), FAN_NOTE + '; W2 CTRL-4: above Q304, its LAB5 pad 2 on the 1.85 mm LAB5 feed (y 87.15)'),
    'Q303': (anchor((41.35, 85.0), 180), FAN_NOTE + '; W2 CTRL-4: moved left 0.65 mm in all, so that the 0.6 mm E3_FAN5_P piece '
             'J313.2 -> D305.1 (x 43.57) passes between Q303.3 and the LAB5 feed column (x 45.0)'),
    'R365': (anchor((38.5, 85.0), 90), FAN_NOTE),
    'R366': (anchor((38.6, 88.0), 0), FAN_NOTE),
    'C318': (anchor((47.6, 74.6), 0), FAN_NOTE),
    'D305': (anchor((40.6, 91.6), 0), FAN_NOTE),
    'C319': (anchor((47.825, 72.82), 0), FAN_NOTE + '; W2 CTRL-4: between the D304 and C318 courtyards (0.07 mm each side), right of the LAB5 feed column, so that its '
             'E3_FAN5_P pad joins F301.2 and C318.1 on B.Cu without a layer change (it sat above the LAB5 branch to Q304)'),
    'D306': (anchor((14.5, 56.3), 0), BLOWER_NOTE),
    'Q305': (anchor((20.23, 56.4), 0), BLOWER_NOTE),
    # W2 CTRL-4: the blower supply capacitors with pad 1 (LAB5) on a 1.85 mm LAB5 bar from J305.4 and pad 2
    # (E3_BLOWER_GND) on a 1.85 mm E3_BLOWER_GND bar and riser to the return rail; the BLOWER2 resistors move right
    'C343': (anchor((11.73, 66.235), 270), BLOWER2_NOTE + ': decoupling capacitor, pad 1 at (11.73, 67.01) on the LAB5 bar'),
    'C342': (anchor((13.65, 66.06), 270), BLOWER2_NOTE + ': bulk capacitor, pad 1 at (13.65, 67.01) on the LAB5 bar'),
    'R363': (anchor((15.45, 66.92), 90), BLOWER2_NOTE + ': piezo series resistor, right of C342'),
    'R370': (anchor((17.31, 66.92), 90), BLOWER2_NOTE + ': blower gate series resistor'),
    'R371': (anchor((19.17, 66.92), 90), BLOWER2_NOTE + ': blower gate pull-down, left of the LAB5 feed vias'),
    'U315': (anchor((23.0505, 95.7), 0), 'bottom strip between the cut-outs, above cut-out 1 (GNSS 5 V switch next to its '
             'capacitors); W2 CTRL-4: x 23.0505 (0.5 um right) puts the U315 pad centres on the 1 um grid of the Specctra '
             'export, so the LAB5 pad escape ends where Freerouting sees the U315.1 centre'),
    # W2 CTRL-4 (FEED4): right-group LAB5 parts on the 1.85 mm outer feed (out of their placement groups)
    'D301': (anchor((37.6, 64.8), 90), 'W2 CTRL-4: Pico VSYS diode below cut-out 1, its LAB5 pad 2 on the 1.85 mm B.Cu LAB5 feed '
             '(y 66.8), right of the BZ301 courtyard; was the first shelf of group PICO (the group region top moves down by that '
             'shelf, so the other PICO parts keep their places)'),
    'C321': (anchor((26.0, 98.075), 90), 'W2 CTRL-4: U315 input capacitor above U315, the centre of its LAB5 pad 1 on the '
             '1.85 mm B.Cu LAB5 feed (y 97.3) that ends above U315.1; was group GNSS_IN'),
    'C322': (anchor((45.95, 93.4), 180), 'W2 CTRL-4: GNSS-switch input bulk capacitor on the 1.85 mm B.Cu LAB5 feed column '
             '(x 45.0) at the top of the right strip; was the second shelf of group R4A (the shelf above keeps its places)'),
}
PICO_TOP = 47.45  # group PICO region top without the D301 shelf (54.9 - 6.95 courtyard - 0.5 gap): the other members do not move
BZ301_SOURCE = ('bottom, y 55-68 below cut-out 1 (courtyard x 22.7-35.8, y 54.98-68.03): over the bms zone (x 0-34, y 0-57; '
                'fits_mm 7.48, free_mm 7.98) and the plate.main, hdmi_route_front_run, hdmi_route_front_turn and '
                'hdmi_route_front_flat zones (17.98 / 16.88 / 15.98 / 16.48 mm); the body is 7.0 mm with a +-0.5 mm drawing '
                'tolerance (Same Sky CPT-1207-3TH rev 1.01 p.2), so its 7.5 mm worst case is 0.02 mm above bms fits_mm 7.48 '
                'and below free_mm 7.98: OPEN for MECH (W2 CTRL-R, review CTRL-8); it cannot move up, cut-out 1 starts at y 68.5')


def edit_placement(spec):
    for p in spec['parts']:
        if p['ref'] in ANCHORS:
            p['anchor'], p['anchor_source'] = copy.deepcopy(ANCHORS[p['ref']][0]), ANCHORS[p['ref']][1]
        if p['ref'] == 'BZ301':
            p['anchor_source'] = BZ301_SOURCE
    groups = []
    for g in spec['groups']:
        if g['id'] in ('FAN', 'FAN2', 'BLOWER', 'GNSS_IN', 'BLOWER2'):
            continue
        if g['id'] == 'PICO' and any(m['ref'] == 'D301' for m in g['members']):
            g['members'] = [m for m in g['members'] if m['ref'] != 'D301']
            g['region'][3] = PICO_TOP
        if g['id'] == 'R4A':
            g['members'] = [m for m in g['members'] if m['ref'] != 'C322']
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
HARD = ('U310', 'U311', 'U315')  # middle GND pins of SOT-23-6 parts: placed first, they have the fewest via spots
FEED_W = 1.85      # W2 CTRL-4: the LAB5 copper at the PWR3A class width of netclasses.json (outer layers only)
FEED_VIAS = [(x, y) for x in (20.55, 21.52, 22.49) for y in (64.0, 65.0)]  # F.Cu -> B.Cu transition of the feed
CLR_0603 = 0.17    # a 1.85 mm track through the centre of one 0603 pad passes 0.175 mm from the other pad (board rule 0.15)
FAN_LEAD = ('a fan-lead (S27) fault behind F301 is limited only by the PTC: between Ihold 0.75 A and Itrip 1.5 A at 23 degC it '
            'may flow indefinitely, Itrip about 2.0 A at -20 degC (Bourns MF-MSMF REV. BE, tabulated Ihold 1.01 A at -20 degC, '
            'scaled; an assumption); that current flows LAB5 -> Q304 -> F301 -> E3_FAN5_P (review RV-CTRLR-2)')
FEED_WHY = ('W2 CTRL-4: LAB5 feed of the right group (D301, Q304/C320/R367, U315/C321/C322) at the PWR3A class width 1.85 mm '
            'on the outer layers, sized for the F102 4 A protective current (netclasses.json LAB5: 1.0 A continuous, 4.0 A '
            'protective, required outer width 1.3348 mm at +20 degC; IPC-2221 external, k 0.048: 5.07 A at +20 degC, +11.7 degC '
            'at 4 A, MODEL); ' + FAN_LEAD + ': +1.3 degC at 1.5 A here; replaces the 0.6 mm L3 run of CTRL-4 (+153 degC at 1.5 A, '
            'about +1430 degC at 4 A); check_boards measures it (no branch_exempt); every LAB5 pad sits on a vertex of this '
            'copper (pad centre on the 1 um grid), so Freerouting adds no LAB5 wire')


def lab5_feed(cu):
    """W2 CTRL-4: the right-group LAB5 feed, 1.85 mm on F.Cu/B.Cu, through the centre of every LAB5 pad it feeds.
    F.Cu from the trunk at (12.2, 64.5) above the J317 pins to six 0.65/0.3 mm vias at x 20.55-22.49 (each about 1.0 A at
    +20 degC, pcb/stackup.py barrel model: 6.0 A), B.Cu along y 66.8 under cut-out 1 (above the BZ301 pins) through the D301
    LAB5 pad, left of D304 and up the right strip at x 45.0 between J313 and F301; at y 87.15 a branch through R367.2 and
    C320.1 turns down into the centre of Q304.2, the column goes on through C322.1 up to y 95.0, along the lower edge of the
    band between the cut-outs, round the GND via of U315.2 and back above U315 through the centre of C321.1;
    U315.1 itself (SOT-23-6, 0.6 mm pad below the feed end) is entered by a 0.6 mm, 0.65 mm pad escape (neck_exempt U315)."""
    P = cu.pad
    W = FEED_W
    d301, c320, r367, q304 = P('D301', '2')['c'], P('C320', '1')['c'], P('R367', '2')['c'], P('Q304', '2')['c']
    c322, c321, u315 = P('C322', '1')['c'], P('C321', '1')['c'], P('U315', '1')['c']
    XC, YR, YU, YH = 45.0, 66.8, 95.0, 87.15  # column, run under cut-out 1, band, fan branch
    assert abs(c320[1] - YH) < 1e-3 and abs(r367[1] - YH) < 1e-3 and abs(c322[0] - XC) < 1e-3 and abs(d301[1] - YR) < 1e-3
    xs = sorted({x for x, _ in FEED_VIAS})
    cu.track('LAB5-FEED-F', 'LAB5', 'F.Cu', W, [(12.2, 64.5)] + [(x, 64.5) for x in xs], FEED_WHY)
    for k, (x, y) in enumerate(FEED_VIAS):
        cu.via(f'LAB5-FEED-V{k + 1}', 'LAB5', (x, y), FEED_WHY)
        for lay in ('F', 'B'):
            cu.track(f'LAB5-FEED-{lay}V{k + 1}', 'LAB5', f'{lay}.Cu', W, [(x, 64.5), (x, y)], FEED_WHY + ': spur to a via')
    cu.track('LAB5-FEED-B1', 'LAB5', 'B.Cu', W,
             [(x, 64.5) for x in xs] + [(24.75, YR), d301, (43.3, YR), (43.3, 71.2), (XC, 72.9), (XC, YH), r367, c320,
                                         (q304[0], YH), q304],
             FEED_WHY + ': trunk side under cut-out 1 through D301.2, left of D304 and up the right strip between J313 and F301, '
             'over to R367.2 and C320.1 above Q304 and down to the centre of Q304.2 (the 1.85 mm copper ends 0.355 mm from the '
             'board edge, 0.25 mm from the E3_FAN5 piece at Q304.3)')
    XT, YT = 28.9, 97.3  # right of the GND via of U315.2 (27.312, 95.7), below the Q301 pads; above U315.1
    assert abs(c321[1] - YT) < 1e-6
    cu.track('LAB5-FEED-B2', 'LAB5', 'B.Cu', W, [(XC, YH), c322, (XC, YU), (XT, YU), (XT, YT), (27.2, YT)],
             FEED_WHY + ': up the right strip at x 45.0, along the lower edge of the band between the cut-outs and round the GND '
             'via of U315.2')
    cu.track('LAB5-FEED-B3', 'LAB5', 'B.Cu', W, [(27.2, YT), c321, (u315[0], YT)],
             FEED_WHY + ': above U315 through the centre of C321.1 (0.175 mm from C321.2, board rule 0.15 mm)', clr=CLR_0603)
    cu.track('LAB5-U315', 'LAB5', 'B.Cu', 0.6, [(u315[0], YT), u315],
             'W2 CTRL-4: pad escape of U315.1 (0.6 mm pad between U315.2 and the 1.85 mm feed end above it), 0.65 mm long '
             '(neck_exempt U315), ending at the pad centre')


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
             'E3_BLOWER_GND return; locked, pad centre to pad centre; every other LAB5 pad is joined by scripted copper too '
             '(W2 CTRL-4), so Freerouting has no LAB5 connection to route')
    cu.track('BLOWER-GND-RAIL', 'E3_BLOWER_GND', 'B.Cu', 1.85,
             [J314_1, (D306_2[0], YB), (Q305_3[0], YB), Q305_3],
             'blower return J314.1 to the low-side switch Q305 drain at the PWR3A width (pad centre to pad centre)')
    cu.track('BLOWER-GND-D306', 'E3_BLOWER_GND', 'B.Cu', 1.85, [(D306_2[0], YB), D306_2],
             'flyback diode D306 anode on the blower return at the PWR3A width')
    cu.track('FAN5-Q304-F301', 'E3_FAN5', 'B.Cu', 1.85, [Q304_3, F301_1],
             'fan switch Q304 drain to the PTC F301 at the PWR3A width (one segment, pad centre to pad centre)')

    # LAB5 branches on the trunk side (W2 CTRL-4: the right group has its own 1.85 mm outer feed, lab5_feed() below)
    D306_1 = P('D306', '1')['c']
    YD = 54.2  # below D306 and its 1.85 mm E3_BLOWER_GND piece (y >= 55.375), above the Pico pads
    cu.track('LAB5-D306', 'LAB5', 'B.Cu', 1.85, [J314_2, (10.6, YD), (D306_1[0], YD), D306_1],
             'LAB5 to the flyback diode D306 cathode at the PWR3A width (W2 CTRL-4): a D306 short with Q305 on puts the F102 '
             '4 A protective current on this piece; J314.2 to D306.1 below the D306 body')
    blower_caps(cu)
    return {'D306_1': D306_1, 'YD': YD}


C343_ENTRY = (0.9, 0.31)  # width, length of the E3_BLOWER_GND pad entry of C343 (inside C343.2 and the 1.85 mm bar end)
CAP_WHY = ('W2 CTRL-4: the blower supply capacitors C343 (decoupling) and C342 (bulk) sit between a 1.85 mm LAB5 bar and a '
           '1.85 mm E3_BLOWER_GND bar: a capacitor short with Q305 on drives the F102 4 A protective current through both '
           '(IPC-2221 external, k 0.048: 1.85 mm +11.7 degC at 4 A, MODEL; the 0.4/0.3 mm branches they replace: +146/+234 '
           'degC)')


def blower_caps(cu):
    """W2 CTRL-4: LAB5 bar J305.4 -> C343.1 -> C342.1 (B.Cu, y 67.01, through both pad centres) and the E3_BLOWER_GND bar
    C343.2 -> C342.2 (y 64.95) with a riser at x 12.5 down to the return rail (J314.1 -> D306.2 vertex at x 12.5).
    C342 (0805, 1.9 mm pad pitch): the bar ends 0.16 mm beyond the C342.2 centre, inside the pad, 0.21 mm from the LAB5 bar.
    C343 (0603, 1.55 mm pitch): a 1.85 mm end inside C343.2 cannot keep 0.15 mm from the LAB5 bar through C343.1, so C343.2
    is entered by a 0.9 x 0.31 mm piece from the 1.85 mm bar end (inside the pad and the bar end; branch_exempt C343)."""
    P = cu.pad
    j305_4, c343_1, c343_2 = P('J305', '4')['c'], P('C343', '1')['c'], P('C343', '2')['c']
    c342_1, c342_2 = P('C342', '1')['c'], P('C342', '2')['c']
    YL, YG, XR = 67.01, 64.95, 12.5
    assert abs(j305_4[1] - YL) < 1e-6 and abs(c343_1[1] - YL) < 1e-6 and abs(c342_1[1] - YL) < 1e-6
    assert abs(c343_1[0] - c343_2[0]) < 1e-6 and abs(c342_1[0] - c342_2[0]) < 1e-6 and c342_2[1] - 0.5 < YG < c342_2[1]
    cu.track('LAB5-CAPS', 'LAB5', 'B.Cu', FEED_W, [j305_4, c343_1, c342_1],
             CAP_WHY + ': LAB5 bar from the J305.4 input pin through the centres of C343.1 and C342.1 (0.175 mm from C343.2, '
             'board rule 0.15 mm)', clr=CLR_0603)
    cu.track('BLOWER-GND-CAPS', 'E3_BLOWER_GND', 'B.Cu', FEED_W, [(c343_2[0], YG), (XR, YG), (c342_2[0], YG)],
             CAP_WHY + ': E3_BLOWER_GND bar below the capacitors, into C342.2')
    cu.track('BLOWER-GND-RISER', 'E3_BLOWER_GND', 'B.Cu', FEED_W, [(XR, YG), (XR, P('J314', '1')['c'][1])],
             CAP_WHY + ': riser from the bar down to the return rail (its vertex above D306.2), left of the J317 pins')
    w, ln = C343_ENTRY
    cu.track('BLOWER-GND-C343', 'E3_BLOWER_GND', 'B.Cu', w, [(c343_2[0], YG), (c343_2[0], round(YG + ln, 4))],
             CAP_WHY + f': pad entry of C343.2, {w} x {ln} mm, inside the pad and the 1.85 mm bar end (branch_exempt C343)')


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
            m, why = cu.via_clear(c, 'GND')
            if m < 0:
                continue
            tm, twhy = cu.track_clear(layer, STUB_W, [(cx, cy), c], 'GND')
            if tm < 0:
                continue
            vid = f'GND-{p["ref"]}.{p["number"]}'
            if any(v['id'] == vid for v in cu.vias):
                vid += f'-{len(cu.vias)}'
            cu.vias.append({'id': vid, 'net': 'GND', 'at': [c[0], c[1]], 'drill_mm': VIA_DRILL, 'diameter_mm': VIA_D, 'locked': True})
            cu.tracks.append({'id': vid, 'net': 'GND', 'layer': layer, 'width_mm': STUB_W,
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
    ys = sorted(c['c'][1] for c in col)
    cu.track('V33-BUS-L3', '3V3_Q6A', 'In2.Cu', 0.25, [(XB, y) for y in reversed(ys)],
             '3V3_Q6A bus of the left pull-up column on L3 (no other copper on L3 left of the J306/J307 pins)')
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
    xr = 49.4  # W2 CTRL-4: along the right board edge, clear of the E3_FAN5_P F.Cu crossing at y 76.05 below R395
    cu.track('P33-R395', P33, 'F.Cu', W, [(xe, 70.3), (xr, 70.3), (xr, r395['c'][1]), r395['c']],
             'E3_PICO3V3 from the HMI3 bus to R395.1, above the D304 pins and up the right board edge (W2 CTRL-4: the '
             'E3_FAN5_P F.Cu piece crosses below R395)')
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
    cu.track('P33-RIGHT-F', P33, 'F.Cu', W, [(xd, 109.6), (40.55, 104.5), (40.55, 101.0), (39.235, 97.0), (39.235, 89.5), (vx, 88.8), (vx, vy)],
             'E3_PICO3V3 on L1 from the right-strip bus between the J316 pins 2 and 1, between C302 and C304, then down beside the cut-out 1 edge to '
             'the via above R368 (route runs 43121860459 and 43131682520 left this link open)')
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

FAN5P_W, FAN5P_WL = 0.8, 0.6   # E3_FAN5_P width; 0.6 mm on the left piece between Q303.3 and the LAB5 column
FAN5P_VIAS = [(46.63, 76.05), (47.59, 76.05), (48.55, 76.05)]  # B.Cu -> F.Cu below F301.2 (three 0.65/0.3 mm vias)
FAN5P_VIAS_L = [(43.54, 76.05), (43.06, 75.22), (42.58, 76.05)]  # F.Cu -> B.Cu left of the LAB5 column
FAN5P_WHY = ('W2 CTRL-4: E3_FAN5_P (fan supply behind the PTC F301, class PWR1A of netclasses.json, scripted and locked, '
             'class SCRIPTED_PWR3A of CTRL.kicad_pro so Freerouting leaves it alone): ' + FAN_LEAD + '. 0.8 mm outer copper '
             '(0.6 mm between Q303.3 and the LAB5 column) and three 0.3 mm vias at each of its two layer changes, a short F.Cu '
             'hop over the LAB5 column (IPC-2221 MODEL: 0.6 mm outer 2.24 A at +20 degC, +8.0 degC at 1.5 A and +15.8 degC at '
             '2.02 A; 0.8 mm +9.8 degC at 2.02 A; a via 1.0 A at +20 degC). The three vias of a layer change do not share the '
             'current equally (DC network of the scripted centre lines, barrel 0.3 mm / 18 um over 1.6 mm, MODEL): below F301.2 '
             '36.7/26.5/36.7 %, the hottest via 0.74 A and +10.1 degC at 2.02 A; left of the LAB5 column the F.Cu entry and the '
             'B.Cu exit share the via at (43.54, 76.05), which takes 60.8 %: 0.91 A and +16.2 degC at the 1.5 A protective current '
             'of the class (rule met), 1.23 A and +31.9 degC at the assumed cold-ambient 2.02 A (OPEN, build/15 "CTRL-4: залишки '
             '(W2 CTRL-4)"))')


def fan5p_copper(cu):
    """W2 CTRL-4: E3_FAN5_P fully scripted (judge 1 of the CTRL-4 study: the LAB5 column cut the F301.2 -> J313.2 path, which
    the router then crossed with single vias). C319.1 -> C318.1 -> F301.2 on B.Cu right of the LAB5 column, three vias below
    F301.2, a 3.1 mm F.Cu hop over the column to three vias left of it (a longer F.Cu run to J313.2 walled in the top-side
    R393-R395 pads: re-freeze trial, E3_MCP_RESET_ASSERT/GATE found no path), and B.Cu up to the J313.2 branch and from
    J313.2 between J313.3/Q303.3 and the column to D305.1."""
    P = cu.pad
    c319, c318, f301, j313, d305 = (P('C319', '1')['c'], P('C318', '1')['c'], P('F301', '2')['c'], P('J313', '2')['c'],
                                    P('D305', '1')['c'])
    W, WL = FAN5P_W, FAN5P_WL
    xv = [x for x, _ in FAN5P_VIAS]
    yv = FAN5P_VIAS[0][1]
    XL = 43.55  # B.Cu column left of the LAB5 column (x 45.0 - 0.925 - 0.2 - 0.3), right of J313.3 and Q303.3
    assert abs(xv[-1] - c318[0]) < 1e-6
    cu.track('FAN5P-B', 'E3_FAN5_P', 'B.Cu', W, [c319, c318, (c318[0], yv), (c318[0], f301[1])],
             FAN5P_WHY + ': C319.1 -> C318.1 -> F301.2 on B.Cu')
    cu.track('FAN5P-BV', 'E3_FAN5_P', 'B.Cu', W, list(reversed(FAN5P_VIAS)), FAN5P_WHY + ': B.Cu row of the three vias')
    for k, at in enumerate(FAN5P_VIAS):
        cu.via(f'FAN5P-V{k + 1}', 'E3_FAN5_P', at, FAN5P_WHY)
    for k, at in enumerate(FAN5P_VIAS_L):
        cu.via(f'FAN5P-VL{k + 1}', 'E3_FAN5_P', at, FAN5P_WHY)
    cu.track('FAN5P-F', 'E3_FAN5_P', 'F.Cu', W, list(reversed(FAN5P_VIAS)) + FAN5P_VIAS_L,
             FAN5P_WHY + ': F.Cu hop over the LAB5 column from the three vias below F301.2 to the three vias left of it')
    cu.track('FAN5P-LV', 'E3_FAN5_P', 'B.Cu', WL, list(reversed(FAN5P_VIAS_L)) + [(XL, j313[1])],
             FAN5P_WHY + ': B.Cu from the three vias left of the LAB5 column up to the J313.2 branch')
    cu.track('FAN5P-L', 'E3_FAN5_P', 'B.Cu', WL, [j313, (XL, j313[1]), (XL, d305[1]), d305],
             FAN5P_WHY + ': B.Cu from J313.2 between J313.3/Q303.3 and the LAB5 column up to the flyback diode D305.1')


FANPG_VIA = (46.475, 84.1)


def q304_gate_escape(cu):
    """W2 CTRL-4: with Q304 0.23 mm further left (the LAB5 feed ends at the Q304.2 centre) its gate pad Q304.1 lies in a pocket
    between the LAB5 column, the LAB5 branch and drop and the E3_FAN5 piece, where the grid A* of the re-freeze found no
    place for a via: a scripted 0.65/0.3 mm via below-left of the pad (0.2 mm design clearance, 0.025 mm to spare) and a
    0.2 mm stub; the frozen route joins the via on the other layers."""
    why = ('W2 CTRL-4: E3_FAN_PG escape of the Q304 gate pad out of the pocket between the LAB5 column, the LAB5 drop to Q304.2 '
           'and the E3_FAN5 piece')
    cu.via('FANPG-V-Q304', 'E3_FAN_PG', FANPG_VIA, why)
    cu.track('FANPG-Q304', 'E3_FAN_PG', 'B.Cu', 0.2, [cu.pad('Q304', '1')['c'], FANPG_VIA], why)


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
    log('E3_PICO3V3 pieces and pull-up rows')
    pico3v3_copper(cu)
    gnd_vias(cu, [p for p in gnd_smd if p['ref'] in HARD], centroid, skipped)
    # W2 CTRL-4: the right-group LAB5 feed (outer, 1.85 mm) where the 0.6 mm L3 run was, and E3_FAN5_P, before the other
    # GND vias
    lab5_feed(cu)
    fan5p_copper(cu)
    q304_gate_escape(cu)
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
    log(f'  {len(cu.vias)} vias, still skipped {skipped}')
    frozen_copper(cu, log)
    return cu, skipped


FROZEN = BASE / 'build/kicad/boards/CTRL/route-frozen.json'


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
    if not FROZEN.is_file():
        return
    doc = json.loads(FROZEN.read_text(encoding='utf-8'))
    have = frozen_guard(cu)
    for key, value in have.items():  # the frozen copper fits only the placement, netlist and scripted copper it was routed on
        if doc['guard'][key] != value:
            raise SystemExit(f'make_spec: route-frozen.json was routed on another {key} ({doc["guard"][key][:12]}... != '
                             f'{value[:12]}...): re-freeze with build/kicad/boards/CTRL/freeze/freeze_route.py --from-frozen, '
                             f'then route with [pcb-route CTRL]')
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
# W2 CTRL-4: every LAB5 and E3_BLOWER_GND piece is 1.85 mm outer copper, measured by check_boards; the one exemption is the
# 0.9 x 0.31 mm E3_BLOWER_GND pad entry of C343.2 (max_mm keeps every LAB5 piece at C343.1, each longer, measured)
BRANCH = {'C343': {'max_mm': 0.4, 'min_width_mm': C343_ENTRY[0], 'reason': (
    f'E3_BLOWER_GND pad entry of the 0603 decoupling capacitor C343 (W2 CTRL-4): one {C343_ENTRY[0]} x {C343_ENTRY[1]} mm '
    'piece from the end of the 1.85 mm E3_BLOWER_GND bar (y 64.95) into C343.2, wholly inside the pad and the bar end; '
    'C343.1 sits on a vertex of the 1.85 mm LAB5 bar (y 67.01) and the 0603 pad pitch of 1.55 mm leaves no place inside '
    'C343.2 for a 1.85 mm end 0.15 mm from that bar. A C343 short with Q305 on drives the F102 4 A protective current '
    'through it; the long-trace IPC-2221 formula does not apply to a 0.31 mm piece within pad and bar copper (MODEL). '
    'max_mm 0.4 keeps every LAB5 piece at C343.1 (each longer than 0.4 mm) in the class width check. Not a bench gate')}}
NECK = ['J311', 'U315']  # E3_GNSS5V pad escapes (router copper); E3_FAN5_P is scripted at 0.6/0.8 mm since W2 CTRL-4
NECK_LAB5 = {  # W2 CTRL-4: the one LAB5 pad entry narrower than the 1.85 mm feed
    'U315': ('LAB5 pad escape of U315.1 (SOT-23-6, 0.6 mm pad between U315.2 (GND) and the feed, 0.95 mm pitch): the 1.85 mm '
             'feed passes 0.65 mm above the pad centre and a 0.6 mm, 0.65 mm piece enters it at the centre, wholly inside the '
             'pad and the feed (W2 CTRL-4)'),
}
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
    '43207377886 green), each with 0 unconnected; Freerouting still adds redundant short wires, DRC-clean: 69-72 per run in '
    'the CTRL-R runs, 188 (58.7 mm on 62 nets) in route run 43343260630 of W2 CTRL-4 (parse of CTRL.kicad_pcb). '
    'After the completion the cut-out 1 band has no spare 0.15 mm crossing on L1/L3/L4 (model): any pad, net or '
    'scripted-copper change stops make_spec at the guard of route-frozen.json. W2 CTRL-4: freeze_route.py --from-frozen '
    're-freezes from the committed GENERATED board (FEED4 study route runs 43270651486, 43276220883 and 43287143670: 2/2, 1/0 '
    'and 0/0 DRC errors/unconnected), here for the outer LAB5 feed, the fully scripted E3_FAN5_P and the blower capacitor '
    'bars; route run 43314567534 of that increment gave 3 errors and 0 unconnected (C319/D304 courtyards; an L2 E3_FAN_PG '
    'piece inside the scripted Q304 gate via off its centre; a dangling 0.0001 mm E3_ENC2_B piece the model read as joined), '
    'so a third increment moves C319 and removes the frozen pieces the exact checks now flag. The lane merge of wip/w2-int '
    '5283b260 (W2 CTRL-R integration: the B2B J208/J209 in the graph) changes only the external refs of the boundary audit, '
    'not the pads, nets or scripted copper, and is re-routed with the same frozen copper (W2 CTRL-4 integration). Job timeout '
    '34 min inside the 45 min CI job')


def l2_plan():
    """The L2 text: the GND plane and the locked signal links the frozen route puts on it (measured from route-frozen.json)."""
    base = 'L2: GND plane (pre-route zone, DSN plane)'
    if not FROZEN.is_file():
        return base
    doc = json.loads(FROZEN.read_text(encoding='utf-8'))
    mm = collections.Counter()
    for net, layer, width, path in doc['router_tracks'] + doc['completion_tracks']:
        if layer == 'In1.Cu':
            mm[net] += sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:]))
    links = ', '.join(f'{n} {v:.1f} mm' for n, v in sorted(mm.items(), key=lambda kv: (-kv[1], kv[0])))
    return (f'{base} with {len(mm)} locked slow signal links of the frozen route completion ({sum(mm.values()):.0f} mm in all; '
            f'W2 CTRL-R, and the W2 CTRL-4 increment where it has added links): {links}; the plane flows around them')


def spec_texts(spec, inp, cu, skipped):
    spec['branch_exempt'] = copy.deepcopy(BRANCH)
    spec['neck_exempt'] = {r: {'escape_mm': 1.5, 'reason': (
        'pad escape of a PWR1A net (E3_GNSS5V) into a pad narrower than 0.35 mm plus clearance: a router track may '
        'narrow next to the pad; the class width resumes within the escape length')} for r in NECK}
    for r, why in NECK_LAB5.items():
        old = spec['neck_exempt'].get(r)
        spec['neck_exempt'][r] = {'escape_mm': 1.5, 'reason': (old['reason'] + '; ' if old else '') + why}
    spec.pop('cutouts', None)
    spec['edge_keepout'] = {'width_mm': 0.2, 'layers': ['F.Cu', 'In2.Cu', 'B.Cu'], 'blocks': ['tracks', 'vias'],
                            'why': ('rule-area strips (half-width 0.2 mm) on every outline and cut-out edge of the routing layers: '
                                    'Freerouting keeps only its clearance to the edge keepout, less than the copper-to-edge 0.3 mm '
                                    '(route run 42423914214: In2.Cu tracks at 0.28 mm from the left edge; PCB-PWRB lesson)')}
    spec['audit_cutouts'] = True
    spec['layers']['types_why'] = (
        'In1.Cu (L2) carries a solid GND plane laid before routing and typed power, so the Specctra export marks it (type power) '
        'and Freerouting does not route on it; every SMD GND pad has its own scripted via to it. F.Cu, In2.Cu and B.Cu are routing '
        'layers; the power classes route on F.Cu/B.Cu only (router.class_layers), as pcb/check_boards.py requires '
        '(netclasses.json: no inner copper for PWR3A, 1.8 mm inner for PWR1A).')
    spec['pre_route'] = {
        'tracks': cu.tracks,
        'vias': cu.vias,
        'zones': [{'id': 'GND-L2', 'net': 'GND', 'layer': 'In1.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
                   'why': 'solid GND plane L2 (build/15 "План шарів"); every SMD GND pad joins it through its scripted via, every THT '
                          'GND pin directly (solid connection)'}],
        'gnd_vias_note': ('one locked 0.65/0.3 mm through via and a 0.25 mm stub per SMD GND pad, placed by a deterministic search '
                          '(24 directions, growing radius, directions away from the part first) on the exact pad shapes: 0.2 mm to '
                          'other-net copper on every layer the via spans, no via in a pad, 0.55 mm hole-to-hole margin, 0.95 mm '
                          'between vias, outside the hole keepouts, the Pico TP keepouts and 0.35 mm from every edge; the Pico GND pins get their via '
                          'straight inwards under the module, past the pad end; GND is in '
                          'class SCRIPTED_GND and not autorouted (route run 42423914214: the router left 9 GND connections and '
                          'dangling fan-out vias)'),
        'gnd_vias_skipped': skipped,
    }
    if FROZEN.is_file():
        spec['pre_route']['frozen_route_note'] = (
            'W2 CTRL-R route study: the tracks RT-* and vias RV-* are the router copper of route run 43136394379 (Freerouting 2.5.0, '
            'inputs sha256 fd468b58...), harvested from that run board and locked; the tracks FIN-* and vias FINV-* complete its 15 '
            'open connections (grid A* on the locked copper, exact clearance check 0.15 mm, 0.3 mm to edges, 0.5 mm hole to hole, '
            'track ends on via centres; router copper of 15 nets ripped where needed and joined again; L2 only where three layers '
            'had no path). Tool: build/kicad/boards/CTRL/freeze/freeze_route.py (numpy, offline). '
            'Source: build/kicad/boards/CTRL/route-frozen.json. Valid only for this placement, netlist and scripted copper '
            '(guard: SHA256 of the pads and of the scripted copper geometry, texts excluded): after a pad, net or scripted-copper '
            'change build/kicad/boards/CTRL/freeze/freeze_route.py --from-frozen re-freezes from the committed GENERATED board and '
            'this file (W2 CTRL-4, review RV-CTRLR-5; --from-frozen --check reproduces the file byte for byte), then one route '
            'run. CI/model result, not a hardware PASS')
        doc = json.loads(FROZEN.read_text(encoding='utf-8'))
        for inc in doc.get('increments', []):
            spec['pre_route']['frozen_route_note'] += (
                f'. Increment ({inc["tool"]}): {inc["reason"]}; frozen copper of '
                f'{", ".join(inc["scripted"] + inc["rip"]) or "no whole net"} removed, '
                + (f'frozen pieces flagged by the exact checks {inc["flagged_frozen_items"]} removed, '
                   if inc.get('flagged_frozen_items') else '') +
                f'pads of {", ".join(inc["moved_refs"]) or "no ref"} moved, {sum(inc["removed_frozen_items"].values())} frozen '
                f'items removed, {len(inc["rejoined_nets"])} nets joined again by the same grid A* (copper added '
                f'{inc["added_copper_mm"]} mm and removed {inc["removed_copper_mm"]} mm by layer, vias +{inc["added_vias"]} '
                f'-{inc["removed_vias"]}, added on L2 {sum(inc["added_l2_mm"].values()):.0f} mm on {len(inc["added_l2_mm"])} nets), '
                f'left open for Freerouting: {inc["left_open_for_freerouting"] or "none"}')
    for z in spec['post_route_zones']:
        z['pad_connection'] = 'solid'
        z['why'] = 'GND pour after routing; solid pad connection (thermal spokes of THT GND pins starve between pins, PCB-PWRB lesson)'
    spec['router'] = {
        'tool': 'freerouting', 'max_passes': 60, 'threads': 1, 'job_timeout': '00:34:00', 'timeout_s': 2160,
        'fanout': False,
        'ignore_net_classes': ['SCRIPTED_GND', 'SCRIPTED_PWR3A'],  # GND, E3_FAN5, E3_FAN5_P, E3_BLOWER_GND
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
    spec['heights']['D304'] = 9.85
    spec['heights_src']['D304'] = (
        'Kingbright WP7113LSECK/J3 data sheet (DSAN8286 / 1101033255, rev V.5A, 03/25/2025) p.1 package dimensions: 8.6 mm from '
        'the lens top to the lead-side face of the 1 mm flange, plus "1.0Max." of body past the flange on the lead side, and '
        'note 2 "Tolerance is ±0.25(0.01\\") unless otherwise noted" on the 8.6 mm dimension, so the seated height is up to '
        '8.6 + 0.25 + 1.0 = 9.85 mm (worst case, used here; review CTRL-8 and RV-CTRLR-6), '
        'https://www.kingbrightusa.com/images/catalog/SPEC/WP7113LSECK-J3.pdf read 2026-11-07 and again 2026-11-12 (W2 CTRL-R, '
        'W2 CTRL-4; page rendered with PyMuPDF)')
    spec['heights_src']['BZ301'] = (
        'Same Sky CPT-1207-3TH data sheet (rev 1.01, 11/02/2026) p.1 dimensions "Ø12.5 x 7.0 mm", p.2 mechanical drawing '
        '"tolerance: ±0.5 mm"; the height check here uses the nominal 7.0 mm (W2 CTRL-4, review RV-CTRLR-6): its 7.5 mm worst '
        'case is 0.02 mm above bms fits_mm 7.48 and below free_mm 7.98, OPEN for MECH (review CTRL-8), '
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
        'E3_GNSS5V), PWR3A_BRANCH (LAB5: every LAB5 pad sits on a vertex of the scripted 1.85 mm copper since W2 CTRL-4, so '
        'the router has no LAB5 connection left), SCRIPTED_GND (GND) and SCRIPTED_PWR3A (E3_FAN5, E3_FAN5_P, E3_BLOWER_GND), '
        'the last two not autorouted (E3_FAN5_P is a PWR1A net of netclasses.json scripted at 0.6/0.8 mm, W2 CTRL-4). '
        'check_boards widths follow netclasses.json (LAB5, E3_BLOWER_GND, E3_FAN5: PWR3A 1.85 mm outer; E3_FAN5_P, E3_GNSS5V: '
        'PWR1A 0.35 mm outer; the C343.2 pad entry in branch_exempt). rules_file stays null (board_gen does not copy .kicad_dru '
        'files yet).')
    spec['layers']['plan'] = {
        'F.Cu': 'L1: top parts, signals, scripted LAB5 feed J305 -> J314.2 (1.85 mm) and the first 10 mm of the right-group LAB5 feed (1.85 mm, y 64.5, to its six vias; W2 CTRL-4), the scripted E3_FAN5_P hop (0.8 mm, from its three vias below F301.2 over the LAB5 column to three vias left of it; W2 CTRL-4), scripted 3V3_Q6A pieces (right pull-up column, MCP pins), scripted E3_PICO3V3 pieces (HMI2/HMI3 bus along cut-out 1 to R368, up the right board edge to R395, the HMI pull-up row to C312 and U306, R361/R362), the frozen router copper of route run 43136394379 and its completion and increments (route-frozen.json), GND pour after routing',
        'In1.Cu': l2_plan(),
        'In2.Cu': 'L3: signals (no LAB5 copper since W2 CTRL-4: the 0.6 mm L3 run to the right group is replaced by outer copper), the scripted 3V3_Q6A bus of the left pull-up column, the frozen router copper and its completion, GND pour after routing',
        'B.Cu': 'L4: bottom parts, signals, scripted E3_BLOWER_GND rail and E3_FAN5 (1.85 mm), the 1.85 mm LAB5 bar from J305.4 and '
                'E3_BLOWER_GND bar and riser of the blower capacitors C343/C342 (W2 CTRL-4), the scripted 1.85 mm LAB5 pieces (J314.2 -> D306, and the right-group feed: y 66.8 under cut-out 1 through D301.2, up the right strip through C320.1/R367.2 to Q304.2 and through C322.1 to the band between the cut-outs and C321.1/U315.1; W2 CTRL-4), scripted E3_FAN5_P (C319.1 -> C318.1 -> F301.2 and three vias right of the LAB5 column; three vias left of it, J313.2 and D305.1 at 0.6 mm; W2 CTRL-4), scripted E3_PICO3V3 pieces (R4B bus along cut-out 2, up the right strip and along the top '
                'edge to J312.4, branch to R362; Pico pin 36 escape via, R330/R327/C308), '
                'locked GND copper over the custom Pico GND pads, the frozen router copper and its completion, GND pour after routing'}
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
                               {'netclass': 'SCRIPTED_PWR3A', 'pattern': 'E3_FAN5_P'},  # W2 CTRL-4: scripted, not routed
                               {'netclass': 'PWR1A', 'pattern': 'E3_GNSS5V'},
                               {'netclass': 'SCRIPTED_GND', 'pattern': 'GND'}]
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
