#!/usr/bin/env python3
"""Board spec generator of the PWR-B mezzanine (W2 PCB-PWRB). Standard library only.

Run from any directory:
  python build/kicad/boards/PWR_B/make_spec.py            write pcb/boards/PWR_B.json and build/kicad/boards/PWR_B/PWR_B.kicad_pro
  python build/kicad/boards/PWR_B/make_spec.py --check    regenerate in memory and compare with the committed files
  python build/kicad/boards/PWR_B/make_spec.py --svg F    also write a placement preview (courtyards, pads, scripted copper)

What it decides, in one place (the spec records each rule with its source):
  * placement of the 128 PWR_BRANCH_SW / USB_POWER_SW refs of pcb/generated/partition.json, top side only, plus the B2B
    placeholder B2B1 on the bottom side (the Samtec QTH-060-01-L-D-A of pcb/partition-spec.json b2b has no graph ref and
    no vendored footprint yet: GR-3 for_dependents, OPEN for GR-4 / PCB-PWRA / PCB-PWRB);
  * the B2B pin map, generated from pcb/generated/b2b-nets.json (contacts per net, one GND contact per power net);
  * scripted locked copper: the LAB5 path (B2B pins -> B.Cu bar -> via array -> F.Cu trunk -> stubs) and the Kelvin
    nets of the four LNA shunts (current path and sense take-off from the shunt pads);
  * the 4-layer plan (In1.Cu / In2.Cu GND planes of type power, signals on F.Cu / B.Cu) and the project rules.
It checks courtyard overlaps, outline / cutouts, hole keepouts and the clearance of the scripted copper before CI routes.
CI/model input only: no fabrication release; bench gates stay OPEN.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys

BASE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(BASE / 'pcb'))
import board_gen as bg  # noqa: E402  (standard library at import time)

BOARD = 'PWR_B'
SPEC = BASE / 'pcb/boards/PWR_B.json'
PROJECT = BASE / 'build/kicad/boards/PWR_B/PWR_B.kicad_pro'
ENC_PROJECT = BASE / 'build/kicad/boards/ENC/ENC.kicad_pro'
B2B_NETS = BASE / 'pcb/generated/b2b-nets.json'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
PARTITION = BASE / 'pcb/generated/partition.json'
PARTITION_SPEC = BASE / 'pcb/partition-spec.json'
CONTRACT = BASE / 'mechanical/generated/contract/boards.json'
MANIFEST = BASE / 'build/kicad/footprints/manifest.json'

# B2B placeholder: official KiCad 10.0.7 library footprints (the plug on PWR-B, its socket for PWR-A), read 2026-11-07.
B2B_FP = 'Connector_Hirose_FX8:Hirose_FX8-120P-SV_2x60_P0.6mm'
B2B_FP_SHA = '9037e84fbb6b50960b888d23e8ba8dea9d7cd6d705ad00ea4d6b2893bffb586f'
B2B_FP_URL = ('https://gitlab.com/kicad/libraries/kicad-footprints/-/raw/10.0.7/Connector_Hirose_FX8.pretty/'
              'Hirose_FX8-120P-SV_2x60_P0.6mm.kicad_mod')
B2B_MATE_FP = 'Connector_Hirose_FX8:Hirose_FX8-120S-SV_2x60_P0.6mm'
B2B_MATE_SHA = '82ef2a7f5fbd930b90d97ef39fd59bbc18f8f31c22ec51cee135ad045241a67b'

CLEAR = 0.15          # project clearance (netclasses.json project_defaults)
MARGIN = 0.05         # design margin of the scripted copper over the clearance
EDGE = 0.3            # project copper-to-edge clearance
VIA_D, VIA_DRILL = 0.7, 0.3   # 0.7 / 0.3: router vias at clearance 0.15 keep the 0.5 mm hole-to-hole rule (0.55)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def r4(v):
    return bg.r4(v)


# ------------------------------------------------------------------ footprint geometry with F.Fab boxes and pad sizes
def ref_xy(text):
    """Local position of the Reference property of a .kicad_mod."""
    m = re.search(r'\(property "Reference" "[^"]*"\s*\(at (-?[\d.]+) (-?[\d.]+)', text)
    return (float(m.group(1)), float(m.group(2))) if m else (0.0, 0.0)


def fab_box(text):
    tree = bg.sexpr(text)
    pts = []
    for node in tree[1:]:
        if isinstance(node, list) and node and node[0] in ('fp_line', 'fp_rect', 'fp_circle', 'fp_poly', 'fp_arc'):
            layer = next((n[1] for n in node if isinstance(n, list) and n[0] == 'layer'), '')
            if layer != 'F.Fab':
                continue

            def walk(n):
                if isinstance(n, list) and n and n[0] in ('start', 'end', 'xy', 'mid', 'center'):
                    pts.append((float(n[1]), float(n[2])))
                elif isinstance(n, list):
                    for m in n:
                        walk(m)
            walk(node)
    if not pts:
        return None
    return [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]


class Placed:
    """A footprint at an anchor: courtyard, F.Fab and pad boxes in board mm (y up), pad nets (as pcb/board_gen.place())."""

    def __init__(self, ref, geo, fab, anchor, nets):
        self.ref, self.anchor, self.side = ref, anchor, anchor.get('side', 'F')
        rot = float(anchor.get('rotation', 0))
        flip = self.side == 'B'

        def local(pt):
            x, y = bg.turn_point(pt, rot)
            return (-x if flip else x), y
        align = anchor.get('align', 'origin')
        if align == 'origin':
            ax, ay = 0.0, 0.0
        else:
            want = str(align['pad'] if 'pad' in align else align['pad_centroid'])
            pts = [local(p['at']) for p in geo['pads'] if str(p['number']) == want]
            ax, ay = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        bx, by = (float(v) for v in anchor['at'])
        self.map = lambda pt: (bx + local(pt)[0] - ax, by - (local(pt)[1] - ay))
        self.box = self._box(geo['courtyard'])
        self.fab = self._box(fab) if fab else None
        quarter = int(round(rot / 90.0)) % 2
        self.pads = []
        for p in geo['pads']:
            cx, cy = self.map(p['at'])
            w, h = p['size'][::-1] if quarter else p['size']
            self.pads.append({'number': p['number'], 'type': p['type'], 'at': (cx, cy),
                              'box': (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2),
                              'net': nets.get(p['number']) if p['number'] else None,
                              'layers': ('F', 'B') if p['type'] in ('thru_hole', 'np_thru_hole') else (self.side,)})

    def _box(self, box):
        x0, y0, x1, y1 = box
        pts = [self.map(c) for c in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        return [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]

    def pad(self, number):
        hits = [p for p in self.pads if p['number'] == str(number)]
        if len(hits) != 1:
            raise SystemExit(f'make_spec: {self.ref} pad {number}: {len(hits)} pads')
        return hits[0]


def box_dist(a, b):
    dx = max(a[0] - b[2], 0.0, b[0] - a[2])
    dy = max(a[1] - b[3], 0.0, b[1] - a[3])
    return math.hypot(dx, dy)


def seg_box_dist(p, q, box):
    """Distance from segment pq to an axis-aligned box (0 when they touch)."""
    (x1, y1), (x2, y2) = p, q
    bx0, by0, bx1, by1 = box
    if bx0 <= x1 <= bx1 and by0 <= y1 <= by1:
        return 0.0
    best = math.inf
    n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.05) + 1)
    for i in range(n + 1):
        t = i / n
        x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        best = min(best, box_dist((x, y, x, y), box))
        if best == 0.0:
            return 0.0
    return best


def seg_seg_dist(a, b, c, d):
    best = math.inf
    for (p, q, r) in ((a, c, d), (b, c, d), (c, a, b), (d, a, b)):
        best = min(best, point_seg(p, q, r))
    # crossing
    def ccw(u, v, w):
        return (w[1] - u[1]) * (v[0] - u[0]) > (v[1] - u[1]) * (w[0] - u[0])
    if ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d):
        return 0.0
    return best


def point_seg(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def point_in_poly(pt, poly):
    return bg.point_in_outline(pt, poly)


def edge_dist(pt, outline, cuts):
    d = min(point_seg(pt, a, b) for a, b in zip(outline, outline[1:] + outline[:1]))
    for x0, y0, x1, y1 in cuts:
        c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        d = min(d, min(point_seg(pt, a, b) for a, b in zip(c, c[1:] + c[:1])))
    return d


# ------------------------------------------------------------------ inputs
class Inputs:
    def __init__(self):
        self.graph = bg.load_graph()
        self.manifest = {f['footprint']: f for f in read(MANIFEST)['footprints']}
        self.partition = read(PARTITION)
        self.b2b = read(B2B_NETS)
        self.netclasses = read(NETCLASSES)
        self.pspec = read(PARTITION_SPEC)
        contract = read(CONTRACT)
        self.contract = contract['boards'][BOARD]
        self.refs = sorted((p['ref'] for p in self.partition['parts']
                            if p['board_candidate'] in self.contract['domains'] and not p['dnp']), key=bg.sort_ref)
        self.geo, self.fab, self.refpos = {}, {}, {}
        for ref in self.refs:
            fp = self.manifest[self.graph[ref]['footprint']]
            text = (BASE / fp['file']).read_text(encoding='utf-8')
            self.geo[ref], self.fab[ref], self.refpos[ref] = bg.footprint_geometry(text), fab_box(text), ref_xy(text)
        text = self.b2b_text()
        self.geo['B2B1'], self.fab['B2B1'], self.refpos['B2B1'] = bg.footprint_geometry(text), fab_box(text), ref_xy(text)

    def b2b_text(self):
        lib = bg.image_library_dir()  # KiCad 10.0.7 library (image), or KICAD10_FOOTPRINT_DIR with a copy of B2B_FP_URL
        path = lib / 'Connector_Hirose_FX8.pretty' / 'Hirose_FX8-120P-SV_2x60_P0.6mm.kicad_mod' if lib else None
        if path is None or not path.is_file():
            raise SystemExit(f'make_spec: B2B placeholder footprint not found; set KICAD10_FOOTPRINT_DIR to a library with {B2B_FP_URL}')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != B2B_FP_SHA:
            raise SystemExit(f'make_spec: {path} sha256 differs from {B2B_FP_SHA}')
        return data.decode('utf-8')

    def nets_of(self, ref):
        return {str(p['number']): (None if p.get('nc') else p.get('net')) for p in self.graph[ref]['pins']}


# ------------------------------------------------------------------ placement (board mm: contract outline origin, y up, top view)
# Fixed anchors: harness headers on the board edges (mating face outwards), the B2B placeholder on the bottom side.
HEADERS = {
    # ref: (align pad 1 at, rotation); rotation 0 = mating face towards -y (bottom edge), 90 = +x (right edge), 180 = +y (top edge)
    'J202': ((62.0, 9.5), 0),     # S02-PWR-SIG-1 PHD 2x10 -> CTRL (bottom edge, towards the CTRL board at x >= 176 of the enclosure)
    'J203': ((85.0, 9.5), 0),     # S02-PWR-SIG-2 PHD 2x10 -> CTRL
    'J201': ((108.0, 6.75), 0),   # X02S0-PWR PH 5 -> CTRL J302
    'J506': ((121.0, 6.75), 0),   # X23S1-PWR PH 3 (S23 LAB PORT) -> plate slot SL3
    'J508': ((129.25, 13.5), 90),  # X34S1-PWR PH 6 (S34 LAB BUS) -> SL3, right edge between the hole keepouts
    'J207': ((107.0, 28.25), 180),  # SL2-PWR-PH PH 12 -> plate slot SL2 (top edge)
    'J204': ((126.0, 28.25), 180),  # X04S1-PWR PH 8 (S04, RF bias) -> SL2 (top edge zone 108-128)
}
B2B_AT = (106.0, 18.5)   # FX8 placeholder centre, bottom side, rotation 0: pin 1 at the right end of the lower row
TX, TY = 72.0, 13.2      # LAB5 F.Cu trunk: vertical at x = TX, horizontal at y = TY (to the B2B via block)


def mirror_rot(rot):
    return {0: 180, 180: 0, 90: 90, 270: 270}[rot % 360]


def cell(ox, oy, rows, refs):
    """Parts of a cell template: rows [(key, x, y, rotation)] in the cell frame, refs {key: graph ref}; origin (ox, oy)."""
    out = {}
    for key, x, y, rot in rows:
        ref = refs.get(key)
        if ref:
            out[ref] = {'at': [r4(ox + x), r4(oy + y)], 'rotation': rot % 360}
    return out


# LNA channel: TPS2553 switch, Kelvin shunt, XAL5030, input/shunt/output capacitors, damping resistor, test point and the
# two INA3221 filter resistors above the shunt (cell box x 1.3-21.45, y 1.17-10.85).
LNA_ROWS = [('U', 5.0, 5.0, 0), ('cin', 3.0, 8.2, 0), ('ren', 3.0, 1.9, 0), ('rilim', 8.3, 3.6, 270),
            ('rsh', 10.2, 6.6, 0), ('csh', 11.6, 3.5, 270), ('L', 16.0, 5.2, 0), ('cout', 20.2, 6.0, 270),
            ('rdamp', 16.0, 9.6, 180), ('tp', 20.2, 9.6, 0), ('rsp', 8.9, 9.3, 90), ('rsm', 11.5, 9.3, 90)]
# Reverse-blocking stage of LNA ch2/ch3 (DMP6050SSD back-to-back PMOS, zener, gate pull-up, 2N7002 sink): box 0-14.75 x 0-11.25.
BLOCK_ROWS = [('Q', 6.0, 6.5, 0), ('D', 2.0, 1.7, 0), ('QN', 6.2, 1.7, 0), ('RSINK', 11.3, 2.3, 90), ('RGS', 0.9, 6.5, 90),
              ('CGS', 11.3, 6.2, 90), ('RBL', 11.3, 9.4, 90), ('CPORT', 6.0, 10.2, 0), ('TPP', 13.5, 9.6, 0)]
# LAB5 switch above the horizontal trunk y = TY (cell frame: x from the switch axis, y from the trunk axis). The switch
# stands at 90 deg (pins 1-3 towards the trunk: pin 1 IN, 2 GND, 3 EN); its LAB5 branch rises from the trunk to pin 1
# through pad 1 of the input capacitor cA; the 100 nF cB sits with pad 1 on the trunk.
UP_ROWS = [('U', 0.0, 5.7, 90), ('cA', 0.0, 2.6, 0), ('cB', 2.5, 0.9, 90), ('ren', 3.0, 4.6, 90), ('rilim', 0.0, 8.9, 0)]
# Voltage monitor (TLV3011 + precision divider + sense filter + supply decoupling): box 0-9.3 x 0.7-5.5.
MON_ROWS = [('U', 5.1, 3.0, 0), ('rtop', 1.5, 4.6, 0), ('rbot', 1.5, 3.0, 0), ('cf', 1.5, 1.4, 0), ('cv', 8.6, 3.0, 90)]
LAB5_CELLS = [  # switch axis x, refs
    (58.0, dict(U='U210', cA='C248', ren='R249', rilim='R248')),
    (64.5, dict(U='U221', cA='C295', ren='R294', rilim='R293')),
    (71.0, dict(U='U501', cA='C502', cB='C501', ren='R502', rilim='R501')),
    (77.5, dict(U='U502', cA='C505', cB='C504', ren='R506', rilim='R505'))]


def placement(inp):
    """Anchor of every template ref (footprint origin unless 'align' says otherwise)."""
    anchors = {}

    def put(parts, side='F'):
        for ref, a in parts.items():
            if ref in anchors:
                raise SystemExit(f'make_spec: {ref} placed twice')
            anchors[ref] = {'at': a['at'], 'align': a.get('align', 'origin'), 'rotation': a['rotation'], 'side': side}
    for ref, (at, rot) in HEADERS.items():
        anchors[ref] = {'at': [at[0], at[1]], 'align': {'pad': '1'}, 'rotation': rot, 'side': 'F'}
    anchors['B2B1'] = {'at': list(B2B_AT), 'align': 'origin', 'rotation': 0, 'side': 'B'}
    # LNA channels ch1-ch3 in the left column (x 8-28), the INA3221 U215 beside the three Kelvin sense pairs, ch4 over
    # the right, contact-free part of the B2B (its Kelvin pair and LNA4V5 go through the B2B to PWR-A).
    lna = [('U206', 'C232', 'R229', 'R228', 'R231', 'C233', 'L206', 'C234', 'R232', 'TP206', 'R268', 'R269', (6.7, 24.0)),
           ('U207', 'C236', 'R234', 'R233', 'R236', 'C237', 'L207', 'C238', 'R237', 'TP207', 'R270', 'R271', (6.7, 12.9)),
           ('U208', 'C240', 'R239', 'R238', 'R241', 'C241', 'L208', 'C242', 'R242', 'TP208', 'R272', 'R273', (6.7, 1.8)),
           ('U209', 'C244', 'R244', 'R243', 'R246', 'C245', 'L209', 'C246', 'R247', 'TP209', None, None, (105.8, 15.5))]
    keys = ('U', 'cin', 'ren', 'rilim', 'rsh', 'csh', 'L', 'cout', 'rdamp', 'tp', 'rsp', 'rsm')
    for row in lna:
        put(cell(row[-1][0], row[-1][1], LNA_ROWS, dict(zip(keys, row[:-1]))))
    put(cell(29.2, 0.6, BLOCK_ROWS, dict(Q='Q2901', D='D2901', QN='Q2911', RSINK='R2911', RGS='R2901', CGS='C2911',
                                           RBL='R2921', CPORT='C2901', TPP='TP2901')))
    put(cell(44.2, 0.6, BLOCK_ROWS, dict(Q='Q2902', D='D2902', QN='Q2912', RSINK='R2912', RGS='R2902', CGS='C2912',
                                           RBL='R2922', CPORT='C2902', TPP='TP2902')))
    put(cell(29.0, 25.0, [('U', 5.5, 5.0, 0), ('c1', 1.6, 8.6, 0), ('c2', 1.6, 1.4, 0), ('c3', 9.6, 1.4, 0),
                          ('cvs', 9.6, 8.6, 0)], dict(U='U215', c1='C274', c2='C275', c3='C276', cvs='C277')))
    for (ox, oy), refs in (((29.5, 13.8), dict(U='U217', rtop='R280', rbot='R281', cf='C282', cv='C283')),
                           ((39.5, 13.8), dict(U='U218', rtop='R283', rbot='R284', cf='C284', cv='C285')),
                           ((29.5, 19.6), dict(U='U219', rtop='R286', rbot='R287', cf='C286', cv='C287'))):
        put(cell(ox, oy, MON_ROWS, refs))
    # LAB5 cluster: four TPS2553 above the LAB5 trunk; their output parts in the tier above.
    for cx, refs in LAB5_CELLS:
        put(cell(cx, TY, UP_ROWS, refs))
    put(cell(0.0, 0.0, [('L210', 59.5, 31.5, 0), ('L215', 66.5, 31.5, 0), ('C503', 76.0, 31.8, 0),
                        ('C249', 57.5, 26.0, 90), ('C250', 61.3, 26.0, 90), ('C296', 64.5, 26.0, 90), ('C297', 68.3, 26.0, 90),
                        ('R251', 72.5, 25.0, 0), ('R295', 72.5, 27.55, 0), ('TP210', 77.0, 25.0, 0), ('TP216', 80.0, 25.0, 0),
                        ('R504', 81.0, 31.6, 90), ('C507', 82.0, 18.0, 90), ('R508', 83.8, 18.0, 90)],
             {r: r for r in ('L210', 'L215', 'C503', 'C249', 'C250', 'C296', 'C297', 'R251', 'R295', 'TP210', 'TP216',
                             'R504', 'C507', 'R508')}))
    # LAB BUS I2C buffer U507 over the B2B, between J201/J506 and ch4.
    put(cell(0.0, 0.0, [('U507', 116.0, 12.4, 0), ('C550', 111.0, 13.0, 90), ('C551', 121.0, 13.0, 90),
                        ('R550', 122.8, 13.0, 90), ('R551', 124.6, 13.0, 90)],
             {r: r for r in ('U507', 'C550', 'C551', 'R550', 'R551')}))
    return anchors


# ------------------------------------------------------------------ geometry checks (before CI)
def placed_parts(inp, anchors, b2b_pins):
    out = {}
    for ref, anchor in anchors.items():
        nets = dict(b2b_pins) if ref == 'B2B1' else inp.nets_of(ref)
        out[ref] = Placed(ref, inp.geo[ref], inp.fab[ref], anchor, nets)
    return out


def check_placement(inp, parts):
    problems = []
    c = inp.contract
    outline = [tuple(p) for p in c['outline_mm']]
    cuts = bg.cutout_boxes(c)
    holes = [(tuple(h), c['hole_keepout_d'] / 2) for h in c['holes_mm']]
    refs = sorted(parts, key=bg.sort_ref)
    for i, a in enumerate(refs):
        pa = parts[a]
        corners = [(pa.box[0], pa.box[1]), (pa.box[2], pa.box[1]), (pa.box[2], pa.box[3]), (pa.box[0], pa.box[3])]
        if not all(point_in_poly(q, outline) for q in corners):
            problems.append(f'{a}: courtyard {pa.box} leaves the outline')
        for cut in cuts:
            if bg.rects_overlap(pa.box, cut):
                problems.append(f'{a}: courtyard over the cutout {cut}')
        for (hx, hy), r in holes:
            for p in pa.pads:
                if p['type'] != 'np_thru_hole' and box_dist(p['box'], (hx, hy, hx, hy)) < r:
                    problems.append(f'{a}.{p["number"]}: pad in the keepout of hole ({hx}, {hy})')
            if pa.fab and box_dist(pa.fab, (hx, hy, hx, hy)) < r:
                problems.append(f'{a}: F.Fab body in the keepout of hole ({hx}, {hy})')
        for p in pa.pads:
            if p['type'] == 'np_thru_hole':
                continue
            x0, y0, x1, y1 = p['box']
            if min(edge_dist(q, outline, cuts) for q in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))) < EDGE + MARGIN or \
                    not point_in_poly(p['at'], outline):
                problems.append(f'{a}.{p["number"]}: pad within {EDGE + MARGIN} mm of the board edge')
        for b in refs[i + 1:]:
            pb = parts[b]
            if pa.side == pb.side and bg.rects_overlap(pa.box, pb.box):
                problems.append(f'courtyards overlap: {a} {pa.box} / {b} {pb.box}')
    # drilled holes (THT pads, NPTH pegs, mounting holes) inside the courtyard of another part on either side
    drills = [(a, p['number'], p['box']) for a in refs for p in parts[a].pads if p['type'] in ('thru_hole', 'np_thru_hole')]
    drills += [(f'H{i}', '', (hx - c['hole_d'] / 2, hy - c['hole_d'] / 2, hx + c['hole_d'] / 2, hy + c['hole_d'] / 2))
               for i, (hx, hy) in enumerate(c['holes_mm'], 1)]
    for owner, number, box in drills:
        for a in refs:
            if a != owner and bg.rects_overlap(parts[a].box, box):
                problems.append(f'hole {owner}.{number} inside the courtyard of {a}')
    return problems


def move_edge_references(inp, anchors, parts):
    """Put the reference legend on the part centre where the library position leaves the board or a cutout
    (KiCad silk_edge_clearance), by the board_gen anchor key ref_text."""
    c = inp.contract
    outline = [tuple(p) for p in c['outline_mm']]
    cuts = bg.cutout_boxes(c)
    for ref, pa in parts.items():
        x, y = pa.map(inp.refpos[ref])
        n = max(2, len(ref))
        box = (x - 0.5 * n - 0.4, y - 0.9, x + 0.5 * n + 0.4, y + 0.9)
        corners = ((box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3]))
        if all(point_in_poly(q, outline) and edge_dist(q, outline, cuts) >= 0.3 for q in corners) and \
                not any(bg.rects_overlap(box, cut) for cut in cuts):
            continue
        b = pa.box
        anchors[ref]['ref_text'] = {'at': [r4((b[0] + b[2]) / 2), r4((b[1] + b[3]) / 2)], 'angle': 0}


def copper_items(parts):
    """Pads as (net, layer, box) for the clearance check of the scripted copper."""
    out = []
    for ref, pa in parts.items():
        for p in pa.pads:
            for layer in p['layers']:
                out.append({'ref': ref, 'pad': p['number'], 'net': p['net'], 'layer': layer, 'box': p['box'],
                            'npth': p['type'] == 'np_thru_hole'})
    return out


def scripted_segments(tracks, vias):
    segs = []
    for t in tracks:
        layer = t['layer'][0]
        for a, b in zip(t['path'], t['path'][1:]):
            segs.append({'id': t['id'], 'net': t['net'], 'layer': layer, 'a': tuple(a), 'b': tuple(b), 'r': t['width_mm'] / 2})
    for v in vias:
        for layer in ('F', 'B'):
            segs.append({'id': v['id'], 'net': v['net'], 'layer': layer, 'a': tuple(v['at']), 'b': tuple(v['at']),
                         'r': v['diameter_mm'] / 2, 'via': True})
    return segs


def check_copper(inp, parts, tracks, vias):
    problems = []
    pads = copper_items(parts)
    c = inp.contract
    outline = [tuple(p) for p in c['outline_mm']]
    cuts = bg.cutout_boxes(c)
    holes = [(tuple(h), c['hole_keepout_d'] / 2) for h in c['holes_mm']]
    segs = scripted_segments(tracks, vias)
    need = CLEAR + MARGIN
    for s in segs:
        for p in pads:
            if p['layer'] != s['layer'] or (p['net'] == s['net'] and not p['npth']):
                continue
            gap = 0.25 + MARGIN if p['npth'] else need
            d = seg_box_dist(s['a'], s['b'], p['box']) - s['r']
            if d < gap:
                problems.append(f'{s["id"]} ({s["net"]}, {s["layer"]}.Cu) {d:.3f} mm from {p["ref"]}.{p["pad"]} ({p["net"]})')
        for (hx, hy), r in holes:
            if point_seg((hx, hy), s['a'], s['b']) - s['r'] < r:
                problems.append(f'{s["id"]}: copper in the keepout of hole ({hx}, {hy})')
        for q in (s['a'], s['b']):
            if edge_dist(q, outline, cuts) - s['r'] < EDGE + MARGIN:
                problems.append(f'{s["id"]}: copper within {EDGE + MARGIN} mm of the board edge at {q}')
    for i, s in enumerate(segs):
        for t in segs[i + 1:]:
            if s['layer'] != t['layer'] or s['net'] == t['net']:
                continue
            d = seg_seg_dist(s['a'], s['b'], t['a'], t['b']) - s['r'] - t['r']
            if d < need:
                problems.append(f'{s["id"]} / {t["id"]}: {d:.3f} mm ({s["layer"]}.Cu)')
    vlist = [s for s in segs if s.get('via') and s['layer'] == 'F']
    for i, s in enumerate(vlist):
        for t in vlist[i + 1:]:
            if math.hypot(s['a'][0] - t['a'][0], s['a'][1] - t['a'][1]) < VIA_DRILL + 0.5:
                problems.append(f'{s["id"]} / {t["id"]}: via holes closer than the 0.5 mm hole-to-hole rule')
    return sorted(set(problems))


def connected(parts, tracks, vias, net, pad_refs):
    """True when every listed pad of the net touches scripted copper of the net that forms one connected tree."""
    segs = [s for s in scripted_segments(tracks, vias) if s['net'] == net]
    items = [('s', i) for i in range(len(segs))]
    pads = []
    for ref, number in pad_refs:
        p = parts[ref].pad(number)
        pads.append((ref, number, p))
    nodes = items + [('p', k) for k in range(len(pads))]
    parent = {n: n for n in nodes}

    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    def union(a, b):
        parent[find(a)] = find(b)
    for i, s in enumerate(segs):
        for j, t in enumerate(segs[i + 1:], i + 1):
            if (s['layer'] == t['layer'] or s.get('via') or t.get('via')) and \
                    seg_seg_dist(s['a'], s['b'], t['a'], t['b']) <= s['r'] + t['r'] + 1e-6:
                if s['layer'] == t['layer']:
                    union(('s', i), ('s', j))
        for k, (_r, _n, p) in enumerate(pads):
            if s['layer'] in p['layers'] and seg_box_dist(s['a'], s['b'], p['box']) <= s['r'] + 1e-6:
                union(('s', i), ('p', k))
    # a via joins its F and B copies
    vidx = {}
    for i, s in enumerate(segs):
        if s.get('via'):
            vidx.setdefault(s['id'], []).append(i)
    for ids in vidx.values():
        for i in ids[1:]:
            union(('s', ids[0]), ('s', i))
    roots = {find(('p', k)) for k in range(len(pads))}
    return len(roots) == 1, [f'{r}.{n}' for r, n, _p in pads]


# ------------------------------------------------------------------ preview
def svg(inp, parts, tracks, vias, path):
    c = inp.contract
    s = 8.0
    W, H = 140 * s, 40 * s if '--bar' in sys.argv else 114 * s
    top = 38 if '--bar' in sys.argv else 112

    def X(x):
        return (x + 2) * s

    def Y(y):
        return (top - y) * s
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           f'<rect width="{W}" height="{H}" fill="white"/>']
    pts = ' '.join(f'{X(x)},{Y(y)}' for x, y in c['outline_mm'])
    out.append(f'<polygon points="{pts}" fill="#f4f4f4" stroke="black" stroke-width="1"/>')
    for x0, y0, x1, y1 in bg.cutout_boxes(c):
        out.append(f'<rect x="{X(x0)}" y="{Y(y1)}" width="{(x1 - x0) * s}" height="{(y1 - y0) * s}" fill="white" stroke="black"/>')
    for (hx, hy) in c['holes_mm']:
        out.append(f'<circle cx="{X(hx)}" cy="{Y(hy)}" r="{c["hole_keepout_d"] / 2 * s}" fill="none" stroke="red" stroke-dasharray="3"/>')
        out.append(f'<circle cx="{X(hx)}" cy="{Y(hy)}" r="{c["hole_d"] / 2 * s}" fill="#ccc" stroke="black"/>')
    for x in range(0, 140, 10):
        out.append(f'<text x="{X(x)}" y="{Y(-1.5)}" font-size="9" fill="#888">{x}</text>')
    for ref, pa in sorted(parts.items(), key=lambda kv: kv[1].side != 'B'):
        col = '#3060c0' if pa.side == 'B' else '#208020'
        b = pa.box
        out.append(f'<rect x="{X(b[0])}" y="{Y(b[3])}" width="{(b[2] - b[0]) * s}" height="{(b[3] - b[1]) * s}" fill="none" stroke="{col}" stroke-width="0.8"/>')
        for p in pa.pads:
            pb = p['box']
            fill = '#9090ff' if pa.side == 'B' else ('#d0a030' if p['type'] == 'thru_hole' else '#e06060')
            out.append(f'<rect x="{X(pb[0])}" y="{Y(pb[3])}" width="{(pb[2] - pb[0]) * s}" height="{(pb[3] - pb[1]) * s}" fill="{fill}" opacity="0.7"/>')
        if pa.side == 'F':
            out.append(f'<text x="{X((b[0] + b[2]) / 2)}" y="{Y((b[1] + b[3]) / 2) + 3}" font-size="8" text-anchor="middle" fill="black">{ref}</text>')
    for t in tracks:
        col = '#c00000' if t['layer'] == 'F.Cu' else '#0000c0'
        d = ' '.join(f'{X(x)},{Y(y)}' for x, y in t['path'])
        out.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="{t["width_mm"] * s}" opacity="0.5" stroke-linecap="round"/>')
    for v in vias:
        out.append(f'<circle cx="{X(v["at"][0])}" cy="{Y(v["at"][1])}" r="{v["diameter_mm"] / 2 * s}" fill="#404040"/>')
    out.append('</svg>')
    Path(path).write_text('\n'.join(out), encoding='utf-8')


# ------------------------------------------------------------------ B2B pin map (generated from pcb/generated/b2b-nets.json)
# Rule (W2 PCB-PWRB): pcb/generated/b2b-nets.json gives every crossing net its contact count (ceil(I_protection / 1 A) for
# power nets, 1 for the others) and one GND contact per power net. On the placeholder the odd row (lower, y = cy - 2.7) fans
# out towards the bottom-edge headers and the LAB5 bar, the even row (upper) towards the top-edge headers and the LNA side.
# Contacts are taken from the left end of each row (pin 119/120) in the order below; a net whose PWR-B pad sits over the
# connector (the ch4 Kelvin pair and its damping net) takes the free upper-row contact under that pad. Every other contact
# is a spare without a net. PCB-PWRA-2 mirrors this map pin for pin on the mate (check_boards b2b).
LOWER_ORDER = ['LAB5', 'LAB5', 'LAB5', 'LAB5', 'GND',
               # CTRL pass-through to J202 / J203, in the order of their header pins (left to right)
               'CHG_INHIBIT', 'E1_BAT_ADC', 'EN_AUX12', 'EN_BONI', 'EN_HFP', 'EN_LIME3V3', 'EN_LNB', 'FAULT_HFP',
               'FLT_BONI', 'FLT_LIME3V3', 'FLT_LNB', 'I2C0_SCL', 'I2C0_SDA', 'IMU_RX', 'IMU_TX', 'INA228_ALERT',
               'OVP_LNB_N', 'PICO_DISP_EN', 'PICO_OFF', 'PWR_BUTTON',
               'GND', 'VBUS_LABPORT', 'I2C2_SCL', 'I2C2_SDA', '3V3_Q6A', 'GND']
UPPER_ORDER = ['LNA4V5', 'LNA4V5', 'GND', 'BIAS_CH1_DAMP', 'BIAS_CH2_DAMP', 'BIAS_CH3_DAMP', 'VBUS_RTLB_DAMP', 'E2_SB_DAMP',
               'BONI13V8', 'AUX12', 'GND', 'BONI13V8_PORT', 'GND', 'VBUS_HFP', 'GND', 'LNB13V2', 'GND',
               'LAB5_RLY', 'LAB5_RLY', 'GND']
UNDER_PAD = {'E2_LNA4_SW': ('R246', '1'), 'E2_LNA4_SHUNT': ('R246', '2'), 'BIAS_CH4_DAMP': ('R247', '2')}


def b2b_pin_xy(number):
    """Board position of a placeholder contact (FX8 at B2B_AT, bottom side, rotation 0: KiCad flips x)."""
    k = int(number)
    cx, cy = B2B_AT
    if k % 2:
        return (r4(cx + 17.7 - 0.3 * (k - 1)), r4(cy - 2.7))
    return (r4(cx + 17.7 - 0.3 * (k - 2)), r4(cy + 2.7))


def b2b_pin_map(inp, anchors):
    want = {}
    for n in inp.b2b['nets']:
        want[n['net']] = int(n['pins'])
    gnd = sum(int(n.get('gnd_pins', 0)) for n in inp.b2b['nets'])
    order_nets = [n for n in LOWER_ORDER + UPPER_ORDER if n != 'GND'] + list(UNDER_PAD)
    counts = {}
    for n in order_nets:
        counts[n] = counts.get(n, 0) + 1
    if counts != want:
        diff = sorted(set(counts.items()) ^ set(want.items()))
        raise SystemExit(f'make_spec: B2B order differs from pcb/generated/b2b-nets.json: {diff}')
    if (LOWER_ORDER + UPPER_ORDER).count('GND') != gnd:
        raise SystemExit(f'make_spec: {gnd} GND contacts in b2b-nets.json, the order has {(LOWER_ORDER + UPPER_ORDER).count("GND")}')
    pins = {}
    for i, net in enumerate(LOWER_ORDER):
        pins[str(119 - 2 * i)] = net
    for i, net in enumerate(UPPER_ORDER):
        pins[str(120 - 2 * i)] = net
    # nets under their pad: the free upper-row contact closest in x to the pad, two contacts apart from any used one
    geo = {ref: Placed(ref, inp.geo[ref], inp.fab[ref], anchors[ref], inp.nets_of(ref)) for ref, _p in UNDER_PAD.values()}
    for net, (ref, number) in UNDER_PAD.items():
        x = geo[ref].pad(number)['at'][0]
        free = [k for k in range(2, 121, 2) if str(k) not in pins and str(k - 2) not in pins and str(k + 2) not in pins]
        k = min(free, key=lambda k: (abs(b2b_pin_xy(k)[0] - x), k))
        pins[str(k)] = net
    used = sorted(pins, key=int)
    return {'pins': dict(sorted(pins.items(), key=lambda kv: int(kv[0]))), 'used': len(used), 'spare': 120 - len(used),
            'scripted_nets': {}}


# ------------------------------------------------------------------ scripted locked copper
LAB5_BAR_X = 89.2          # B.Cu bar over the four LAB5 contacts 113-119 and the via block
LAB5_VIAS = [(88.7, 12.2), (89.7, 12.2), (88.7, 13.2), (89.7, 13.2), (88.7, 14.2), (89.7, 14.2)]
W_TRUNK, W_BRANCH, W_CURRENT, W_SENSE = 2.0, 0.6, 0.5, 0.35


def scripted_copper(inp, parts, pins):
    """Locked tracks and vias (board mm). Returns (tracks, vias, branch_exempt) and fills pins['scripted_nets']."""
    tracks, vias = [], []

    def T(tid, net, layer, width, path, why):
        tracks.append({'id': tid, 'net': net, 'layer': layer, 'width_mm': width,
                       'path': [[r4(x), r4(y)] for x, y in path], 'locked': True, 'why': why})

    def V(vid, net, at, why):
        vias.append({'id': vid, 'net': net, 'at': [r4(at[0]), r4(at[1])], 'drill_mm': VIA_DRILL, 'diameter_mm': VIA_D,
                     'locked': True, 'why': why})

    def P(ref, number):
        return parts[ref].pad(number)['at']
    # LAB5: B2B contacts -> B.Cu bar -> six vias -> F.Cu trunk (PWR3A 2.0 mm >= 1.85) -> 0.6 mm branch to each switch IN.
    lab5 = [n for n, net in pins['pins'].items() if net == 'LAB5']
    ys = [P('B2B1', n)[1] for n in lab5]
    T('LAB5-B2B-BAR', 'LAB5', 'B.Cu', W_TRUNK, [(LAB5_BAR_X, ys[0] + 0.2), (LAB5_BAR_X, 12.4)],
      'B.Cu bar over the four LAB5 contacts (pcb/generated/b2b-nets.json: ceil(4 A / 1 A)) to the via block')
    for i, at in enumerate(LAB5_VIAS, 1):
        V(f'LAB5-V{i}', 'LAB5', at, 'LAB5 B.Cu bar to the F.Cu trunk: six vias (netclasses.json PWR3A vias_per_transition 5)')
    T('LAB5-F-LANDING', 'LAB5', 'F.Cu', W_TRUNK, [(LAB5_BAR_X, TY), (LAB5_BAR_X, 14.5)], 'F.Cu copper over the via block')
    first = LAB5_CELLS[0][0] - 0.95
    T('LAB5-TRUNK', 'LAB5', 'F.Cu', W_TRUNK, [(LAB5_BAR_X, TY), (first, TY)],
      'LAB5 trunk to the four TPS2553 inputs: PWR3A width 2.0 mm >= 1.85 (netclasses.json)')
    exempt = {}
    for cx, refs in LAB5_CELLS:
        u = refs['U']
        pin1 = P(u, '1')
        T(f'LAB5-BR-{u}', 'LAB5', 'F.Cu', W_BRANCH, [(cx - 0.95, TY), (cx - 0.95, pin1[1])],
          f'branch to {u} IN through pad 1 of {refs["cA"]}; carries at most the {u} current limit')
        exempt[u] = {'max_mm': 5.0, 'min_width_mm': W_BRANCH,
                     'reason': f'LAB5 branch from the 2.0 mm trunk to {u} IN (pin 1), through the input capacitor {refs["cA"]}: '
                               f'it carries at most the TPS2553 limit of {u} (<= 0.825 A, tools/assembly_data.py NET_CURRENT), '
                               f'within the PWR1A width 0.35 mm; the SOT-23-6 pin pitch 0.95 mm does not take 1.85 mm'}
    lab5_pads = [('B2B1', n) for n in lab5] + [(refs['U'], '1') for _cx, refs in LAB5_CELLS] + \
        [(refs['cA'], '1') for _cx, refs in LAB5_CELLS] + [(refs['cB'], '1') for _cx, refs in LAB5_CELLS if 'cB' in refs]
    pins['scripted_nets']['LAB5'] = lab5_pads
    # Kelvin shunts of the four LNA channels: current path and sense take-off from the shunt pads (cell frame of LNA_ROWS).
    chans = [('1', 'U206', 'R231', 'L206', 'C233', 'R268', 'R269'), ('2', 'U207', 'R236', 'L207', 'C237', 'R270', 'R271'),
             ('3', 'U208', 'R241', 'L208', 'C241', 'R272', 'R273'), ('4', 'U209', 'R246', 'L209', 'C245', None, None)]
    for ch, u, rsh, ind, csh, rsp, rsm in chans:
        sw, shunt = f'E2_LNA{ch}_SW', f'E2_LNA{ch}_SHUNT'
        u6, s1, s2, l1, c1 = P(u, '6'), P(rsh, '1'), P(rsh, '2'), P(ind, '1'), P(csh, '1')
        T(f'K{ch}-SW-I', sw, 'F.Cu', W_CURRENT, [u6, (s1[0] - 0.84, u6[1]), s1],
          f'{u} OUT to the {rsh} current pad (Kelvin: current enters from the side)')
        T(f'K{ch}-SH-I', shunt, 'F.Cu', W_CURRENT, [s2, (l1[0], s2[1])], f'{rsh} to {ind} (current path)')
        T(f'K{ch}-SH-C', shunt, 'F.Cu', W_CURRENT, [c1, (c1[0], s2[1])], f'{csh} to the {rsh} shunt-side pad')
        if rsp:
            p1, m1 = P(rsp, '1'), P(rsm, '1')
            T(f'K{ch}-SW-S', sw, 'F.Cu', W_SENSE, [(p1[0], s1[1]), p1], f'Kelvin sense: {rsh} pad 1 to the INA3221 filter {rsp}')
            T(f'K{ch}-SH-S', shunt, 'F.Cu', W_SENSE, [(m1[0], s2[1]), m1], f'Kelvin sense: {rsh} pad 2 to the INA3221 filter {rsm}')
            pins['scripted_nets'][sw] = [(u, '6'), (rsh, '1'), (rsp, '1')]
            pins['scripted_nets'][shunt] = [(rsh, '2'), (ind, '1'), (csh, '1'), (rsm, '1')]
        else:  # ch4: the sense pair crosses the B2B to INA3221 #2 U216 on PWR-A (declared sense pair, partition-spec b2b)
            for net, pad, tag in ((sw, s1, 'SW'), (shunt, s2, 'SH')):
                k = next(n for n, v in pins['pins'].items() if v == net)
                bk = P('B2B1', k)
                top = parts[rsh].pad('1')['box'][3]
                via = (pad[0] + (0.16 if tag == 'SW' else -0.16), top + 0.65)
                T(f'K{ch}-{tag}-S', net, 'F.Cu', W_SENSE, [(via[0], pad[1]), via], f'Kelvin sense: {rsh} pad to its via')
                V(f'K{ch}-{tag}-V', net, via, f'Kelvin sense {net} to the B2B contact {k} (bottom side)')
                T(f'K{ch}-{tag}-B', net, 'B.Cu', W_SENSE, [via, (bk[0], via[1] - 1.0), bk], f'Kelvin sense to B2B contact {k}')
            pins['scripted_nets'][sw] = [(u, '6'), (rsh, '1'), ('B2B1', next(n for n, v in pins['pins'].items() if v == sw))]
            pins['scripted_nets'][shunt] = [(rsh, '2'), (ind, '1'), (csh, '1'),
                                            ('B2B1', next(n for n, v in pins['pins'].items() if v == shunt))]
    return tracks, vias, exempt


# ------------------------------------------------------------------ heights (pcb/partition-spec.json heights, AREA reads)
def height_of(inp, ref):
    """(height mm, source) from pcb/partition-spec.json heights; JST side-entry headers from its header_families."""
    fp = inp.graph[ref]['footprint'].split(':', 1)[1]
    mpn = inp.graph[ref]['value'].split()
    heights = inp.pspec['heights']
    fam = inp.pspec['header_families']
    if fp.startswith('JST_PHD_S') and fp.endswith('Horizontal'):
        return fam['PHD_side']['h'], 'pcb/partition-spec.json header_families.PHD_side h (JST ePHD catalogue, LCSC C161675 Z-height; read 2026-11-07 by W2 AREA)'
    if fp.startswith('JST_PH_S') and fp.endswith('Horizontal'):
        return fam['PH_side']['h'], 'pcb/partition-spec.json header_families.PH_side h (JST ePH via mechanical/params/parts.json harness_headers; read 2026-11-07)'
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
    raise SystemExit(f'make_spec: no height source for {ref} ({fp})')


# ------------------------------------------------------------------ the spec
WARNINGS = {
    'footprint_filters_mismatch': 'schematic-parity check; per-board PCBs are not linked to the multi-sheet schematic, so DRC runs without --schematic-parity and the source-pad audit replaces it',
    'footprint_symbol_mismatch': 'schematic-parity check, not run (see footprint_filters_mismatch)',
    'footprint_symbol_field_mismatch': 'schematic-parity check, not run (see footprint_filters_mismatch)',
    'missing_footprint': 'schematic-parity check, not run (see footprint_filters_mismatch)',
    'extra_footprint': 'schematic-parity check, not run (see footprint_filters_mismatch)',
    'duplicate_footprints': 'schematic-parity check, not run (see footprint_filters_mismatch)',
    'net_conflict': 'schematic-parity check, not run (see footprint_filters_mismatch)',
    'missing_tuning_profile': 'no length-tuned nets and no tuning profiles on this board',
    'tuning_profile_track_geometries': 'no length-tuned nets and no tuning profiles on this board',
    'generic_warning': "KiCad's catch-all warning class; any instance is listed in report.json and reviewed",
    'silk_over_copper': 'legend only: the fab clips legend over exposed copper; library outlines of the JST and FX8 footprints sit close to their pads',
    'silk_overlap': 'legend only: overlapping legend items are cosmetic; every instance is listed in report.json',
}


def template_nets(inp, pins):
    nets = set(pins['pins'].values())
    for ref in inp.refs:
        nets |= {n for n in inp.nets_of(ref).values() if n}
    return sorted(nets)


def spec_json(inp, anchors, pins, tracks, vias, exempt):
    c = inp.contract
    nets = template_nets(inp, pins)
    floor = inp.netclasses['fab_floor']['jlc_4l_1oz']
    b2b_sha = hashlib.sha256(B2B_NETS.read_bytes()).hexdigest()
    parts = []
    for ref in sorted(anchors, key=bg.sort_ref):
        if ref == 'B2B1':
            continue
        a = anchors[ref]
        anchor = {'at': a['at'], 'align': a['align'], 'rotation': a['rotation'], 'side': a['side']}
        if 'ref_text' in a:
            anchor['ref_text'] = a['ref_text']
        parts.append({'ref': ref, 'source': 'graph', 'anchor': anchor})
    a = anchors['B2B1']
    parts.append({
        'ref': 'B2B1', 'source': 'pilot_placeholder', 'footprint': B2B_FP, 'footprint_library': 'kicad-image',
        'footprint_sha256': B2B_FP_SHA,
        'footprint_sha256_source': f'{B2B_FP_URL} read 2026-11-07; checked against the kicad/kicad:10.0.7 image copy at run time',
        'value': 'B2B placeholder: Samtec QTH-060-01-L-D-A pending',
        'pins': pins['pins'],
        'pins_source': 'generated by build/kicad/boards/PWR_B/make_spec.py b2b_pin_map() from pcb/generated/b2b-nets.json '
                       f'(sha256 {b2b_sha}): every crossing net with its contact count, one GND contact per power net',
        'replaced_by': 'graph ref of the Samtec QTH-060-01-L-D-A (pcb/partition-spec.json b2b.mpn.pwr_b) once its land pattern is '
                       'read and vendored (GR-4 / PCB-PWRA / PCB-PWRB lineage), keeping this pin map',
        'pending': 'B2B ref pending: Samtec QTH-060-01-L-D-A land pattern not read, no graph ref yet (GR-3 OPEN)',
        'why_placeholder': 'The QTH-060-01-L-D-A has no KiCad 10.0.7 footprint and Samtec\'s recommended PCB layout was not readable '
                           '(GR-3 for_dependents: suddendocs.samtec.com prints 403 on 2026-11-07), so pcb/partition-spec.json b2b has '
                           'no graph ref. The placeholder is the official KiCad 10.0.7 Hirose FX8-120P-SV land (2 x 60 contacts, '
                           '0.6 mm pitch, courtyard 43.6 x 7.9 against the QTH-060 catalogue outline 40.0 x 7.11, F-226 qth.pdf), so '
                           'the fan-out, the pin map and the PWR-A mate position can be routed and checked now. It is not the part '
                           f'to buy; its socket {B2B_MATE_FP} (sha256 {B2B_MATE_SHA}) is the PWR-A placeholder mate.',
        'anchor': {'at': a['at'], 'align': a['align'], 'rotation': a['rotation'], 'side': a['side']}})
    heights, sources = {}, {}
    for ref in inp.refs:
        heights[ref], sources[ref] = height_of(inp, ref)
    stack = inp.pspec['parameters']['stack']
    heights['B2B1'] = stack
    sources['B2B1'] = ('mated QTH-060-01 / QSH-060-01 stack = the PWR-A to PWR-B gap '
                       f'{stack} mm (pcb/partition-spec.json parameters.stack: Samtec catalogue F-226 qth.pdf, lead style -01)')
    spec = {
        'schema': bg.SPEC_SCHEMA,
        'board_id': BOARD,
        'status': 'MODEL_NOT_FOR_FABRICATION',
        'title': 'PWR-B power mezzanine (PWR_BRANCH_SW + USB_POWER_SW): LNA and USB branch switches, monitors, harness headers',
        'note': ('W2 PCB-PWRB. Generated by build/kicad/boards/PWR_B/make_spec.py (do not hand-edit; rerun it). Placement, the B2B pin '
                 'map and the scripted copper are design choices of this package (build/15 rows W2 PCB-PWRB); KiCad DRC, the '
                 'audits and check_boards are CI/model results. Not a fabrication release; mezzanine fit, heat and every bench '
                 'gate stay OPEN.'),
        'contract': {'file': 'mechanical/generated/contract/boards.json', 'board': BOARD},
        'domains': list(c['domains']),
        'partition': 'pcb/generated/partition.json',
        'layers': {
            'copper': 4, 'thickness_mm': 1.6,
            'source': 'build/15 Шари (4-layer JLC04161H-7628, 1 oz outer) and mechanical/generated/contract/boards.json stackup',
            'types': {'In1.Cu': 'power', 'In2.Cu': 'power'},
            'plan': {'F.Cu': 'parts (top side only), LAB5 trunk and Kelvin copper, signals, GND pour',
                     'In1.Cu': 'solid GND plane (layer type power: the router puts only vias through it)',
                     'In2.Cu': 'second GND plane (layer type power)',
                     'B.Cu': 'B2B placeholder (bottom), LAB5 bar, B2B fan-out, signals, GND pour'}},
        'project': 'build/kicad/boards/PWR_B/PWR_B.kicad_pro',
        'rules_file': None,
        'rules_note': ('Project rules live in the committed PWR_B.kicad_pro (generated by make_spec.py): the project defaults of '
                       'pcb/generated/netclasses.json project_defaults (track 0.15 / clearance 0.15, via 0.6 / 0.3, copper-edge '
                       '0.3, hole-hole 0.5) and its net classes SIG (Default), PWR1A, PWR2A, PWR3A with the outer minimum width as '
                       'track width. pcb/rules/jlc-4l-1oz.kicad_dru is not copied: board_gen refuses rules_file until it copies '
                       'and hashes it.'),
        'fab_floor': {
            'source': f'{inp.netclasses["fab_floor"]["source"]} read {inp.netclasses["fab_floor"]["read"]}, 4-layer 1 oz values '
                      '(pcb/generated/netclasses.json fab_floor.jlc_4l_1oz)',
            'min_track_width': floor['track_width_min'], 'min_clearance': floor['track_spacing_min'],
            'min_drill': floor['via_hole_min'], 'min_via_diameter': floor['via_diameter_min'],
            'min_hole_to_hole': floor['pad_hole_to_hole_min'],
            'min_hole_to_hole_note': f'{floor["pad_hole_to_hole_min"]} = pad hole-to-hole; via hole-to-hole is {floor["via_hole_to_hole_min"]}',
            'min_copper_edge_clearance': floor['copper_to_routed_edge_min'], 'min_text_height': floor['silk_text_height_min'],
            'min_text_thickness': floor['silk_line_min'], 'npth_min_diameter': floor['npth_hole_min'],
            'pth_annular_min': floor['pth_annular_min'], 'pth_annular_recommended': floor['pth_annular_recommended']},
        'instances': {
            'template_nets': nets,
            'list': [{'id': 'PWRB', 'placement': 'default', 'qty': 1,
                      'refs': {**{r: r for r in inp.refs}, 'B2B1': None}, 'nets': {n: n for n in nets},
                      'source': 'one board per device; template refs and nets are the graph refs and nets '
                                '(pcb/generated/partition.json domains PWR_BRANCH_SW, USB_POWER_SW)'}],
            'spares': 0,
            'spares_source': 'no spare board planned (build/15 W2 PCB-PWRB); a fab panel minimum is a purchasing matter'},
        'parts': parts,
        'holes': {'from_contract': True, 'ref_prefix': 'H', 'keepout_layers': ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'],
                  'keepout_blocks': ['tracks', 'vias', 'zone_fills']},
        'groups': [],
        'pre_route': {
            'tracks': tracks,
            'vias': vias,
            'zones': [{'id': 'GND-In1', 'net': 'GND', 'layer': 'In1.Cu', 'outline': 'board', 'priority': 0,
                       'why': 'GND plane, exported as a Specctra plane so the router joins GND pads to it with vias'},
                      {'id': 'GND-In2', 'net': 'GND', 'layer': 'In2.Cu', 'outline': 'board', 'priority': 0,
                       'why': 'second GND plane (power layer)'}]},
        'post_route_zones': [
            {'id': 'GND-F', 'net': 'GND', 'layer': 'F.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
             'why': 'solid pad connection: thermal spokes of THT header GND pins were starved between the pins (route run 42414083566)'},
            {'id': 'GND-B', 'net': 'GND', 'layer': 'B.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid'}],
        'edge_keepout': {'width_mm': 0.2, 'layers': ['F.Cu', 'B.Cu'], 'blocks': ['tracks', 'vias'],
                         'why': 'rule-area strips (half-width 0.2) on every outline and cutout edge: the router keeps its copper '
                                '0.35 mm off the edge, above the project copper-to-edge 0.3 (route run 42414083566 had 0.23)'},
        'height_zones': [
            {'region': 'board', 'max_height_mm_from_contract': 'max_component_height', 'side': 'top', 'checked': True,
             'why': 'hB 5.5 (pcb/partition-spec.json parameters.hB): parts on the top side; heights from heights below'},
            {'region': 'board', 'max_height_mm': stack, 'side': 'bottom', 'checked': True,
             'why': 'bottom side: only the B2B in the PWR-A to PWR-B gap (stack 5.0)'}],
        'sides': ['top', 'bottom'],
        'max_height_bottom': stack,
        'heights': dict(sorted(heights.items(), key=lambda kv: bg.sort_ref(kv[0]))),
        'heights_source': dict(sorted(sources.items(), key=lambda kv: bg.sort_ref(kv[0]))),
        'branch_exempt': exempt,
        'b2b_pin_map': {
            'connector': 'B2B1 (placeholder for the Samtec QTH-060-01-L-D-A, bottom side)',
            'mate': {'board': 'PWR_A', 'placeholder_footprint': B2B_MATE_FP, 'placeholder_sha256': B2B_MATE_SHA,
                     'mpn': 'Samtec QSH-060-01-L-D-A (pcb/partition-spec.json b2b.mpn.pwr_a)',
                     'rule': 'PCB-PWRA-2 puts the mate on the PWR-A top under B2B1 (connectors.json enclosure_xy of every contact) '
                             'and gives each contact the same net (check_boards b2b, pin_map identity)'},
            'source': f'pcb/generated/b2b-nets.json sha256 {b2b_sha}',
            'rule': ('contacts per crossing net from b2b-nets.json (ceil(I_protection / 1 A) for power nets, else 1) and one GND '
                     'contact per power net; odd (lower) row from contact 119 in LOWER_ORDER, even (upper) row from 120 in '
                     'UPPER_ORDER (make_spec.py), the ch4 Kelvin pair and BIAS_CH4_DAMP on the free upper contact under their pad'),
            'contacts': 120, 'used': pins['used'], 'spare': pins['spare'],
            'needed_with_spare': inp.b2b['totals']['contacts_with_spare']},
        'placement_rules': {
            'edges': 'harness headers on the board edges with the mating face outwards: CTRL-bound J202, J203, J201 and the '
                     'SL3-bound J506 on the bottom edge, J508 on the right edge between the hole keepouts, the SL2-bound J207 and '
                     'J204 on the top edge (contract edge_zones; the right edge holds one PH 6 only, see build/15 W2 PCB-PWRB)',
            'reserve': 'the arm of the L (x 0-42, y 35-110) carries no part: it stays free for the PWR-A windows and edge strips '
                       'that PCB-PWRA places (pcb/partition-budget.json windows and edge strips)',
            'kelvin': 'INA3221 U215 between the ch1-ch3 shunts; every shunt net is scripted copper (current path plus sense '
                      'take-off from the shunt pads); ch4 senses through the B2B to U216 on PWR-A'},
        'router': {'tool': 'freerouting', 'max_passes': 60, 'threads': 1, 'job_timeout': '00:25:00', 'timeout_s': 1620,
                   'fanout': False, 'ignore_net_classes': sorted(set(SCRIPTED_CLASSES.values())),
                   'why': 'the fan-out pre-pass escaped every SMD pin with necked-down (0.1124 mm) stubs and dangling vias, and '
                          'the router re-routed the scripted nets because locked copper that crosses a pad is no connection '
                          'for it (route run 42414083566): fan-out off, the scripted classes not autorouted'},
        'drc_policy': {'warning_checks': WARNINGS},
    }
    return json.dumps(spec, ensure_ascii=False, indent=2) + '\n'


# ------------------------------------------------------------------ the project (rules and net classes)
def project_json(inp, pins):
    proj = read(ENC_PROJECT)
    proj['meta']['filename'] = 'PWR_B.kicad_pro'
    nc = inp.netclasses
    default = proj['net_settings']['classes'][0]
    pd = nc['project_defaults']['values_mm']
    classes = []
    for name, cls in (('Default', nc['classes']['SIG']), ('PWR1A', nc['classes']['PWR1A']), ('PWR2A', nc['classes']['PWR2A']),
                      ('PWR3A', nc['classes']['PWR3A']), ('SCRIPTED_PWR1A', nc['classes']['PWR1A']),
                      ('SCRIPTED_PWR3A', nc['classes']['PWR3A'])):
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
    nets = set(template_nets(inp, pins))
    patterns = [p for p in nc['kicad']['netclass_patterns'] if p['pattern'] in nets and p['netclass'] in ('PWR1A', 'PWR2A', 'PWR3A')
                and p['pattern'] not in SCRIPTED_CLASSES]
    patterns += [{'netclass': cls, 'pattern': net} for net, cls in SCRIPTED_CLASSES.items()]
    have = {p['pattern'] for p in patterns}
    for net, cls in BOARD_CLASSES.items():
        if net not in have:
            patterns.append({'netclass': cls, 'pattern': net})
    proj['net_settings']['netclass_patterns'] = sorted(patterns, key=lambda p: p['pattern'])
    rules = proj['board']['design_settings']['rules']
    rules['min_track_width'] = pd['track_width']
    rules['min_clearance'] = pd['clearance']
    rules['min_copper_edge_clearance'] = pd['edge_clearance']
    rules['min_hole_to_hole'] = pd['hole_to_hole']
    return json.dumps(proj, indent=2) + '\n'


# Board routing classes beyond pcb/generated/netclasses.json (wider than its minimum, never narrower).
BOARD_CLASSES = {'LNA4V5': 'PWR2A'}
# Nets whose copper is all scripted and locked: widths of their netclasses.json class, not autorouted (router -inc).
SCRIPTED_CLASSES = {'LAB5': 'SCRIPTED_PWR3A', **{f'E2_LNA{ch}_{k}': 'SCRIPTED_PWR1A' for ch in '1234' for k in ('SW', 'SHUNT')}}  # 2 B2B contacts, up to 1.209 A (b2b-nets.json net_current_extra): 0.8 mm routing width


# ------------------------------------------------------------------ main
def build(inp):
    anchors = placement(inp)
    missing = [r for r in inp.refs if r not in anchors]
    pins = b2b_pin_map(inp, anchors)
    parts = placed_parts(inp, anchors, pins['pins'])
    move_edge_references(inp, anchors, parts)
    tracks, vias, exempt = scripted_copper(inp, parts, pins)
    return anchors, missing, pins, parts, tracks, vias, exempt


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--svg')
    ap.add_argument('--bar', action='store_true')
    ap.add_argument('--draft', action='store_true', help='report placement and copper problems, write nothing')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    inp = Inputs()
    anchors, missing, pins, parts, tracks, vias, exempt = build(inp)
    problems = check_placement(inp, parts) + check_copper(inp, parts, tracks, vias)
    problems += [f'not placed: {r}' for r in missing]
    for net, pad_refs in pins['scripted_nets'].items():
        ok, names = connected(parts, tracks, vias, net, pad_refs)
        if not ok:
            problems.append(f'scripted net {net} does not join {names}')
    if args.svg:
        svg(inp, parts, tracks, vias, args.svg)
    for p in problems:
        print('PROBLEM', p)
    print(f'{len(problems)} problem(s); {len(anchors)} parts; {len(tracks)} tracks; {len(vias)} vias')
    if args.draft:
        return 1 if problems else 0
    if problems:
        return 1
    spec_text, project_text = spec_json(inp, anchors, pins, tracks, vias, exempt), project_json(inp, pins)
    if args.check:
        bad = [p for p, text in ((SPEC, spec_text), (PROJECT, project_text)) if not p.is_file() or p.read_text(encoding='utf-8') != text]
        for p in bad:
            print(f'make_spec: {p.relative_to(BASE).as_posix()} is stale')
        return 1 if bad else 0
    for p, text in ((SPEC, spec_text), (PROJECT, project_text)):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8', newline='\n')
        print('wrote', p.relative_to(BASE).as_posix())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
