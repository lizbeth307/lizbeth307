#!/usr/bin/env python3
"""Board spec generator of the PWR-B mezzanine (W2 PCB-PWRB). Standard library only.

Run from any directory:
  python build/kicad/boards/PWR_B/make_spec.py            write pcb/boards/PWR_B.json and build/kicad/boards/PWR_B/PWR_B.kicad_pro
  python build/kicad/boards/PWR_B/make_spec.py --check    regenerate in memory and compare with the committed files
  python build/kicad/boards/PWR_B/make_spec.py --svg F    also write a placement preview (courtyards, pads, scripted copper)

What it decides, in one place (the spec records each rule with its source):
  * placement of the PWR_BRANCH_SW / USB_POWER_SW refs of pcb/generated/partition.json, top side only, except the B2B
    half J209 (W2 B2B: Samtec LSHM-150-02.5-L-DV-A-N-K-TR, graph ref, vendored KiCad 10.0.7 footprint) on the bottom
    side, at the nearest place to the former FX8 placeholder anchor where its two alignment-post holes clear the
    top-side courtyards;
  * the B2B pin map: J209 takes its pin nets from the graph, which carries pcb/generated/b2b-nets.json contacts pin for
    pin (checked here; the mating map to J208 on PWR-A is b2b-nets.json mating_map);
  * scripted locked copper: the LAB5 path (J209 contacts -> via blocks -> F.Cu trunk -> stubs), the Kelvin nets of the
    four LNA shunts (current path and sense take-off from the shunt pads), the J209 GND spine (every GND contact
    joins a B.Cu spine between the two contact rows, with plane vias on it) and a plane via next to every other SMD
    GND pad (gnd_fanout);
  * the 4-layer plan (In1.Cu / In2.Cu GND planes of type power, signals on F.Cu / B.Cu), the project rules and net
    classes, and the router settings: Freerouting without its fan-out stage, the classes of the scripted nets
    (SCRIPTED_GND, SCRIPTED_PWR1A, SCRIPTED_PWR3A) not autorouted, rule-area strips on every board edge.
Why each router setting exists is in the spec (router.why, edge_keepout.why) with the sr-rx-pcb run that showed it.
It checks courtyard overlaps, outline / cutouts, hole keepouts, drilled holes in courtyards, the GND via of every SMD
GND pad and the clearance of the scripted copper before CI routes. The routed board, its report and the fab set are
CI outputs (route run of a commit whose subject carries '[pcb-route PWR_B]', applied as 'GENERATED:').
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

# B2B half on PWR-B (W2 B2B): graph ref J209 (design/E2.json), its mate J208 on the PWR-A top (pcb/partition-spec.json
# b2b.graph_refs). Footprint and MPN come from the graph and the parts DB; the mating map from b2b-nets.json.
B2B_REF, B2B_MATE_BOARD, B2B_MATE_REF = 'J209', 'PWR_A', 'J208'

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
        if B2B_REF not in self.refs:
            raise SystemExit(f'make_spec: {B2B_REF} is not a {BOARD} ref of pcb/generated/partition.json (rerun pcb/prepare.py)')

    def nets_of(self, ref):
        return {str(p['number']): (None if p.get('nc') else p.get('net')) for p in self.graph[ref]['pins']}


# ------------------------------------------------------------------ placement (board mm: contract outline origin, y up, top view)
# Fixed anchors: harness headers on the board edges (mating face outwards), the B2B half J209 on the bottom side.
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
# J209 centre, bottom side, rotation 180: contact 1 at the left end of the lower row (odd contacts lower, even upper,
# pads 2k-1 / 2k in one column, 0.5 mm pitch), so the rail block (columns 1-21 of b2b-nets.json) lies next to the end of
# the LAB5 trunk and the left LNA channels, the signal block over the header J203 and the sense pair (column 50) under
# the ch4 shunt R246. The FX8 placeholder sat at (106.0, 18.5); there the right alignment-post hole (footprint
# (13.5, -0.85), 1.45 mm NPTH) lands in a top-side courtyard (L209 at rotation 0 or 180). On y 18.5 with rotation 180
# both holes clear every top-side courtyard for x 98.46-99.14 (right hole between R244 and R243, left hole right of
# R506); 98.8 is its middle. With rotation 0 only x 102.05-102.2 is legal, and there the LAB5 contacts lie under U209
# (route run 43100556016: 21 connections open).
B2B_AT = (98.8, 18.5)
B2B_ROT = 180
TX, TY = 72.0, 13.2      # LAB5 F.Cu trunk: vertical at x = TX, horizontal at y = TY (to the J209 via blocks)


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
    (61.0, dict(U='U210', cA='C248', ren='R249', rilim='R248')),
    (67.5, dict(U='U221', cA='C295', ren='R294', rilim='R293')),
    (74.0, dict(U='U501', cA='C502', cB='C501', ren='R502', rilim='R501')),
    (80.5, dict(U='U502', cA='C505', cB='C504', ren='R506', rilim='R505'))]


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
    anchors[B2B_REF] = {'at': list(B2B_AT), 'align': 'origin', 'rotation': B2B_ROT, 'side': 'B'}
    # LNA channels ch1-ch3 in the left column (x 8-28), the INA3221 U215 beside the three Kelvin sense pairs, ch4 over
    # the right end of J209 (its Kelvin pair in column 50 and LNA4V5 go through the B2B to PWR-A).
    lna = [('U206', 'C232', 'R229', 'R228', 'R231', 'C233', 'L206', 'C234', 'R232', 'TP206', 'R268', 'R269', (6.7, 24.0)),
           ('U207', 'C236', 'R234', 'R233', 'R236', 'C237', 'L207', 'C238', 'R237', 'TP207', 'R270', 'R271', (6.7, 12.9)),
           ('U208', 'C240', 'R239', 'R238', 'R241', 'C241', 'L208', 'C242', 'R242', 'TP208', 'R272', 'R273', (6.7, 1.8)),
           ('U209', 'C244', 'R244', 'R243', 'R246', 'C245', 'L209', 'C246', 'R247', 'TP209', None, None, (105.8, 15.5))]
    keys = ('U', 'cin', 'ren', 'rilim', 'rsh', 'csh', 'L', 'cout', 'rdamp', 'tp', 'rsp', 'rsm')
    for row in lna:
        put(cell(row[-1][0], row[-1][1], LNA_ROWS, dict(zip(keys, row[:-1]))))
    put(cell(29.2, 2.6, BLOCK_ROWS, dict(Q='Q2901', D='D2901', QN='Q2911', RSINK='R2911', RGS='R2901', CGS='C2911',
                                           RBL='R2921', CPORT='C2901', TPP='TP2901')))
    put(cell(44.2, 2.6, BLOCK_ROWS, dict(Q='Q2902', D='D2902', QN='Q2912', RSINK='R2912', RGS='R2902', CGS='C2912',
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
                        ('R504', 81.0, 31.6, 90), ('C507', 83.2, 24.6, 90), ('R508', 85.0, 24.6, 90)],
             {r: r for r in ('L210', 'L215', 'C503', 'C249', 'C250', 'C296', 'C297', 'R251', 'R295', 'TP210', 'TP216',
                             'R504', 'C507', 'R508')}))
    # LAB BUS I2C buffer U507 right of the B2B, between J201/J506 and ch4.
    put(cell(0.0, 0.0, [('U507', 116.0, 12.4, 0), ('C550', 111.0, 13.0, 90), ('C551', 121.0, 13.0, 90),
                        ('R550', 122.8, 13.0, 90), ('R551', 124.6, 13.0, 90)],
             {r: r for r in ('U507', 'C550', 'C551', 'R550', 'R551')}))
    return anchors


# ------------------------------------------------------------------ geometry checks (before CI)
def placed_parts(inp, anchors):
    return {ref: Placed(ref, inp.geo[ref], inp.fab[ref], anchor, inp.nets_of(ref)) for ref, anchor in anchors.items()}


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
            if p['type'] == 'smd' and not p['number']:
                continue  # unnumbered SMD pads of the library footprints are paste apertures (F.Paste only)
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


# ------------------------------------------------------------------ B2B pin map (J209 graph pins = pcb/generated/b2b-nets.json)
# W2 B2B: pcb/prepare.py b2b_contacts generates the contact map of both halves (b2b-nets.json contacts: pwr_a_pin on J208,
# pwr_b_pin on J209, pin_map_rule and guard_rule there) and the graph carries it pin for pin. This board takes the J209
# pad nets from the graph and stops when they differ from the map. Spare contacts are nc in the graph (no net).
def b2b_pin_map(inp):
    graph = inp.nets_of(B2B_REF)
    want = {str(c['pwr_b_pin']): (c['net'] or None) for c in inp.b2b['contacts']}
    have = {n: graph.get(n) for n in want}
    diff = sorted((n for n in want if want[n] != have[n]), key=int)
    if diff or set(graph) != set(want):
        raise SystemExit(f'make_spec: {B2B_REF} graph pins differ from pcb/generated/b2b-nets.json contacts at '
                         f'{diff[:6] or sorted(set(graph) ^ set(want))} (rerun pcb/write_b2b_graph.py and the refreeze chain)')
    if inp.b2b['graph_refs'].get('pwr_b') != B2B_REF or inp.b2b['graph_refs'].get('pwr_a') != B2B_MATE_REF:
        raise SystemExit(f'make_spec: b2b-nets.json graph_refs {inp.b2b["graph_refs"]} are not {B2B_MATE_REF} / {B2B_REF}')
    pins = {n: net for n, net in want.items() if net}
    return {'pins': dict(sorted(pins.items(), key=lambda kv: int(kv[0]))), 'used': len(pins),
            'spare': int(inp.b2b['contacts_available']) - len(pins), 'scripted_nets': {}}


# ------------------------------------------------------------------ scripted locked copper
W_TRUNK, W_BRANCH, W_CURRENT, W_SENSE = 2.0, 0.6, 0.5, 0.35
# J209 escape copper (W2 B2B). The LSHM pads are 0.30 mm wide at 0.50 mm pitch (0.20 mm gaps), and every rail contact has a
# GND neighbour in its row (b2b-nets.json guard_rule), so: GND contacts join a B.Cu spine between the rows (inwards), rail
# and signal contacts escape outwards, and copper that enters a pad between two neighbours is at most W_PADSTUB wide.
W_PADSTUB = 0.25          # into a 0.30 mm pad beside a neighbour: 0.225 mm gap (clearance 0.15 + margin 0.05)
W_SPINE = 1.4             # GND spine on the connector centre line: 0.40 mm from the inner pad ends of both rows
SPINE_STUB = 0.5          # GND stubs end 0.5 mm off the spine centre line, so no stub end lies inside a spine via
NPTH_CLEAR = 0.25 + 0.05  # copper to the J209 alignment-post holes (KiCad hole clearance 0.25, design margin 0.05)
SPINE_VIAS_MIN = 4
SPINE_VIA_PITCH = 1.2     # spine plane vias at least this far apart: 0.5 mm between them for one F.Cu track
LAB5_UP_VY = 22.2         # upper LAB5 vias above the upper contact row (top side free there)
LAB5_LO_VY = 15.4         # lower LAB5 vias below the lower contact row, clear of the GND contacts beside them
W_PAIR = 0.8              # copper of one LAB5 contact pair (2 A): PWR2A width (netclasses.json)
K4_KLO = 15.2             # ch4 SHUNT sense: B.Cu right of the J209 hole, under the lower row into its contact


def via_spot_ok(inp, parts, tracks, vias, at, net):
    """A through via of `net` at `at` keeps CLEAR + MARGIN from every pad of both sides and any net (no via in a pad), from
    scripted copper of other nets, the edges and hole keepouts, and the hole-to-hole rule (with margin) to drilled holes."""
    c = inp.contract
    outline = [tuple(p) for p in c['outline_mm']]
    cuts = bg.cutout_boxes(c)
    r = VIA_D / 2
    vx, vy = at
    if not point_in_poly(at, outline) or edge_dist(at, outline, cuts) - r < EDGE + MARGIN:
        return False
    if any(math.hypot(vx - hx, vy - hy) - r < c['hole_keepout_d'] / 2 for hx, hy in c['holes_mm']):
        return False
    for p in copper_items(parts):
        if box_dist((vx, vy, vx, vy), p['box']) - r < (0.25 + MARGIN if p['npth'] else CLEAR + MARGIN):
            return False
    for pa in parts.values():
        for p in pa.pads:
            if p['type'] in ('thru_hole', 'np_thru_hole'):
                d = min(p['box'][2] - p['box'][0], p['box'][3] - p['box'][1])
                if math.hypot(vx - p['at'][0], vy - p['at'][1]) < VIA_DRILL / 2 + d / 2 + 0.55:
                    return False
    if any(math.hypot(vx - v['at'][0], vy - v['at'][1]) < VIA_DRILL + 0.55 for v in vias):
        return False
    return all(s['net'] == net or point_seg(at, s['a'], s['b']) - s['r'] - r >= CLEAR + MARGIN
               for s in scripted_segments(tracks, []))


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
    j = parts[B2B_REF]

    def row(n):  # upper / lower contact row of J209 on the board (rotation 180: odd contacts lower, even upper)
        return 'upper' if j.pad(n)['at'][1] > B2B_AT[1] else 'lower'
    # LAB5: four J209 contacts (b2b-nets.json: ceil(4 A / 1 A)), two in each row (guard_rule checkerboard), next to the end of
    # the trunk. Each contact: B.Cu stub -> one via; each pair (2 A): F.Cu bar 0.8 mm (PWR2A); the upper pair by a 0.8 mm riser
    # over the strip (top side free there) down to the lower bar; from there a 2.0 mm plate (4 A, PWR3A >= 1.85) to the
    # F.Cu trunk -> 0.6 mm branch to each switch IN.
    lab5 = sorted((n for n, net in pins['pins'].items() if net == 'LAB5'), key=int)
    up, lo = [n for n in lab5 if row(n) == 'upper'], [n for n in lab5 if row(n) == 'lower']
    if len(up) != 2 or len(lo) != 2:
        raise SystemExit(f'make_spec: LAB5 contacts {lab5} are not two per row; the J209 LAB5 copper assumes the guard_rule map')
    for n in up:
        x = P(B2B_REF, n)[0]
        end = j.pad(n)['box'][3] + 0.3
        T(f'LAB5-J209-{n}', 'LAB5', 'B.Cu', W_PADSTUB, [P(B2B_REF, n), (x, end)],
          f'out of J209 contact {n} (upper row) between its GND neighbours')
        T(f'LAB5-J209-{n}-E', 'LAB5', 'B.Cu', W_SENSE, [(x, end), (x, LAB5_UP_VY)],
          f'J209 contact {n} to its via: one contact, at most 1 A (b2b_i_pin_A), PWR1A width')
        V(f'LAB5-UV-{n}', 'LAB5', (x, LAB5_UP_VY), f'LAB5 via of J209 contact {n}')
    ux = sorted(P(B2B_REF, n)[0] for n in up)
    xr = sum(ux) / len(ux)
    T('LAB5-UP-BAR', 'LAB5', 'F.Cu', W_PAIR, [(ux[0], LAB5_UP_VY), (ux[-1], LAB5_UP_VY)], 'F.Cu over the two upper LAB5 vias')
    T('LAB5-RISER', 'LAB5', 'F.Cu', W_PAIR, [(xr, LAB5_UP_VY), (xr, LAB5_LO_VY)],
      'F.Cu riser of the two upper LAB5 contacts (2 A, PWR2A width 0.8 mm) over J209 (no top-side part there)')
    for n in lo:
        x = P(B2B_REF, n)[0]
        T(f'LAB5-J209-{n}', 'LAB5', 'B.Cu', W_PADSTUB, [P(B2B_REF, n), (x, LAB5_LO_VY)],
          f'out of J209 contact {n} (lower row) between its GND neighbours to its via: one contact, at most 1 A')
        V(f'LAB5-LV-{n}', 'LAB5', (x, LAB5_LO_VY), f'LAB5 via of J209 contact {n}')
    lx = sorted(P(B2B_REF, n)[0] for n in lo)
    T('LAB5-LO-BAR', 'LAB5', 'F.Cu', W_PAIR, [(lx[0], LAB5_LO_VY), (max(lx[-1], xr), LAB5_LO_VY)],
      'F.Cu over the two lower LAB5 vias to the riser (2 A, PWR2A width 0.8 mm)')
    T('LAB5-PLATE', 'LAB5', 'F.Cu', W_TRUNK, [(xr, LAB5_LO_VY), (xr, TY)],
      'the four LAB5 contacts (4 A) from the riser to the trunk: PWR3A width 2.0 mm')
    xm = xr
    first = LAB5_CELLS[0][0] - 0.95
    T('LAB5-TRUNK', 'LAB5', 'F.Cu', W_TRUNK, [(xm, TY), (first, TY)],
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
    exempt[B2B_REF] = {'max_mm': 10.0, 'min_width_mm': W_PADSTUB,
                       'reason': 'J209 contact escapes (Samtec LSHM-150, pads 0.30 mm at 0.50 mm pitch, a GND or rail '
                                 'neighbour 0.20 mm away): every contact carries at most 1 A (b2b_i_pin_A, '
                                 'pcb/partition-spec.json b2b.i_pin_note), its stub is 0.25 mm wide inside the row and 0.35 mm '
                                 '(PWR1A, 1 A) beyond it up to its via; each LAB5 pair (2 A) then runs at the PWR2A width 0.8 mm '
                                 '(LAB5-UP-BAR, LAB5-RISER, LAB5-LO-BAR) up to the 2.0 mm LAB5-PLATE where the four contacts join; '
                                 'the 1.85 mm of PWR3A does not fit between 0.30 mm pads'}
    lab5_pads = [(B2B_REF, n) for n in lab5] + [(refs['U'], '1') for _cx, refs in LAB5_CELLS] + \
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
            continue
        # ch4: the sense pair crosses the B2B to INA3221 #2 U216 on PWR-A (declared sense pair, partition-spec b2b). Its
        # contacts are J209 column 50 under R246: SW in the upper row, SHUNT in the lower row. Each take-off leaves the top of
        # its shunt pad to a via (as for the FX8 placeholder); SW runs on B.Cu into its contact from above, SHUNT on B.Cu
        # right of the J209 alignment hole and under the lower row into its contact. The take-offs touch only their shunt
        # pad, not the current-path copper (K4-SW-I enters pad 1 from the left, K4-SH-I and K4-SH-C leave pad 2 to the
        # right and below).
        ksw = next(n for n, v in pins['pins'].items() if v == sw)
        ksh = next(n for n, v in pins['pins'].items() if v == shunt)
        if (row(ksw), row(ksh)) != ('upper', 'lower') or j.pad(ksw)['at'][0] != j.pad(ksh)['at'][0]:
            raise SystemExit(f'make_spec: J209 {sw} {ksw} / {shunt} {ksh} are not one column (SW upper, SHUNT lower)')
        top = parts[rsh].pad('1')['box'][3]
        vsw, vsh = (s1[0] + 0.16, top + 0.65), (s2[0] - 0.16, top + 0.65)
        T('K4-SW-S', sw, 'F.Cu', W_SENSE, [(vsw[0], s1[1]), vsw], f'Kelvin sense: top of {rsh} pad 1 to its via')
        V('K4-SW-V', sw, vsw, f'Kelvin sense {sw} to J209 contact {ksw} (bottom side)')
        bx, by = P(B2B_REF, ksw)
        end = j.pad(ksw)['box'][3] + 0.3
        T('K4-SW-B', sw, 'B.Cu', W_SENSE, [vsw, (bx, end + 0.6), (bx, end)], f'Kelvin sense to J209 contact {ksw}')
        T('K4-SW-P', sw, 'B.Cu', W_PADSTUB, [(bx, end), (bx, by)], f'into J209 contact {ksw} between its neighbours')
        T('K4-SH-S', shunt, 'F.Cu', W_SENSE, [(vsh[0], s2[1]), vsh], f'Kelvin sense: top of {rsh} pad 2 to its via')
        V('K4-SH-V', shunt, vsh, f'Kelvin sense {shunt} to J209 contact {ksh} (bottom side)')
        bx, by = P(B2B_REF, ksh)
        end = j.pad(ksh)['box'][1] - 0.3
        T('K4-SH-B', shunt, 'B.Cu', W_SENSE, [vsh, (vsh[0], K4_KLO), (bx, K4_KLO), (bx, end)],
          f'Kelvin sense on B.Cu right of the J209 alignment hole, under the lower row to contact {ksh}')
        T('K4-SH-P', shunt, 'B.Cu', W_PADSTUB, [(bx, end), (bx, by)], f'into J209 contact {ksh} between its neighbours')
        pins['scripted_nets'][sw] = [(u, '6'), (rsh, '1'), (B2B_REF, ksw)]
        pins['scripted_nets'][shunt] = [(rsh, '2'), (ind, '1'), (csh, '1'), (B2B_REF, ksh)]
    # J209 GND spine: every GND contact (b2b-nets.json guard_rule: the return beside each rail contact and the guards)
    # stubs inwards to a B.Cu track on the connector centre line, between the two rows; plane vias on the spine where a
    # via clears every pad and the other copper. The rail and signal contacts all escape outwards.
    gnd = sorted((n for n, net in pins['pins'].items() if net == 'GND'), key=int)
    sy = B2B_AT[1]
    gx = [P(B2B_REF, n)[0] for n in gnd]
    holes = [p['box'] for p in j.pads if p['type'] == 'np_thru_hole']
    x0, x1 = min(gx), max(gx)
    # keep the spine ends clear of the alignment-post holes beside columns 1 and 50 (hole box, as check_copper measures)
    while any(seg_box_dist((x0, sy), (x1, sy), h) - W_SPINE / 2 < NPTH_CLEAR for h in holes if h[0] < (x0 + x1) / 2):
        x0 = r4(x0 + 0.05)
    while any(seg_box_dist((x0, sy), (x1, sy), h) - W_SPINE / 2 < NPTH_CLEAR for h in holes if h[0] > (x0 + x1) / 2):
        x1 = r4(x1 - 0.05)
    T('GND-J209-SPINE', 'GND', 'B.Cu', W_SPINE, [(x0, sy), (x1, sy)],
      f'GND spine of the {len(gnd)} J209 GND contacts between the contact rows (no ground plane in the LSHM)')
    for n in gnd:
        px, py = P(B2B_REF, n)
        T(f'GND-J209-{n}-S', 'GND', 'B.Cu', W_PADSTUB, [(px, py), (px, sy + (SPINE_STUB if py > sy else -SPINE_STUB))],
          f'J209 GND contact {n} inwards into the spine')
    # plane vias only under GND columns (rail block, guards) and SPINE_VIA_PITCH apart, so the spine leaves F.Cu channels
    # across the strip between them and none at all over the signal and spare columns
    k, last, x = 0, None, x0
    while x <= x1 + 1e-9:
        if (last is None or x - last >= SPINE_VIA_PITCH - 1e-9) and min(abs(x - g) for g in gx) <= 0.25 + 1e-9 and \
                min(abs(x - x0), abs(x - x1)) >= VIA_D / 2 + 0.05 and via_spot_ok(inp, parts, tracks, vias, (x, sy), 'GND'):
            k += 1
            V(f'GND-J209-V{k}', 'GND', (x, sy), 'plane via on the J209 GND spine')
            last = x
        x = r4(x + 0.05)
    if k < SPINE_VIAS_MIN:
        raise SystemExit(f'make_spec: only {k} plane vias fit on the J209 GND spine (need {SPINE_VIAS_MIN})')
    pins['scripted_nets']['GND'] = [(B2B_REF, n) for n in gnd]
    gt, gv, _n = gnd_fanout(inp, parts, tracks, vias)
    return tracks + gt, vias + gv, exempt


# ------------------------------------------------------------------ GND fan-out (scripted: every SMD GND pad gets a via)
W_GND = 0.25
GND_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
GND_GAPS = (0.55, 0.9, 1.3, 1.8)


def gnd_fanout(inp, parts, tracks, vias):
    """A locked via next to every GND SMD pad (stub W_GND from the pad centre), so that the GND planes In1/In2 join all
    GND pads and the router never routes GND (route run 42415437982: Freerouting left 83 GND connections open and did
    not join the pads to the planes). Through-hole GND pins join the planes directly. The INA3221 exposed pad joins its
    GND pin 3 by a short track. Candidates are tried in a fixed order; the first that clears every other net, the
    edges, the hole keepouts and the via hole spacing is taken."""
    c = inp.contract
    outline = [tuple(p) for p in c['outline_mm']]
    cuts = bg.cutout_boxes(c)
    holes = [(tuple(h), c['hole_keepout_d'] / 2) for h in c['holes_mm']]
    pads = copper_items(parts)
    drills = []
    for ref, pa in parts.items():
        for p in pa.pads:
            if p['type'] in ('thru_hole', 'np_thru_hole'):
                drills.append((p['at'], min(p['box'][2] - p['box'][0], p['box'][3] - p['box'][1])))
    for v in vias:
        drills.append((tuple(v['at']), v['drill_mm']))
    segs = scripted_segments(tracks, vias)
    need = CLEAR + MARGIN
    out_t, out_v = [], []

    def clear(path, via_at, layer, new_via=True):
        vx, vy = via_at
        stubs = list(zip(path, path[1:]))
        r = VIA_D / 2
        if new_via:
            if edge_dist(via_at, outline, cuts) - r < EDGE + MARGIN or not point_in_poly(via_at, outline):
                return False
            if any(bg.rects_overlap((vx - r, vy - r, vx + r, vy + r), cut) for cut in cuts):
                return False
            for (hx, hy), hr in holes:
                if math.hypot(vx - hx, vy - hy) - r < hr:
                    return False
            for (dx, dy), dd in drills:
                if math.hypot(vx - dx, vy - dy) < VIA_DRILL / 2 + dd / 2 + 0.55:
                    return False
        for p in pads:
            if p['net'] == 'GND' and not p['npth']:
                continue
            gap = 0.25 + MARGIN if p['npth'] else need
            b = p['box']
            if b[0] - 3 > vx or b[2] + 3 < vx or b[1] - 3 > vy or b[3] + 3 < vy:
                continue
            if new_via and box_dist((vx, vy, vx, vy), b) - r < gap:
                return False
            if p['layer'] == layer and any(seg_box_dist(a, q, b) - W_GND / 2 < gap for a, q in stubs):
                return False
        for s in segs:
            if s['net'] == 'GND':
                continue
            if new_via and seg_seg_dist(s['a'], s['b'], via_at, via_at) - s['r'] - r < need:
                return False
            if s['layer'] == layer and any(seg_seg_dist(s['a'], s['b'], a, q) - s['r'] - W_GND / 2 < need for a, q in stubs):
                return False
        return True
    spine_vias = [tuple(v['at']) for v in vias if v['id'].startswith(f'GND-{B2B_REF}-V')]
    done = 0
    for ref in sorted(parts, key=bg.sort_ref):
        if ref == B2B_REF:
            continue  # the J209 GND contacts join the GND spine (scripted_copper), not a via each
        pa = parts[ref]
        for p in sorted(pa.pads, key=lambda q: (bg.sort_ref(q['number']) if q['number'] else ('', -1, ''))):
            if p['net'] != 'GND' or p['type'] != 'smd' or not p['number']:
                continue
            if ref == 'U215' and p['number'] == 'EP':
                pin3 = pa.pad('3')['at']
                out_t.append({'id': 'GND-U215-EP', 'net': 'GND', 'layer': 'F.Cu', 'width_mm': W_GND,
                              'path': [[r4(pin3[0]), r4(pin3[1])], [r4(p['at'][0]), r4(pin3[1])]], 'locked': True,
                              'why': 'INA3221 exposed pad to its GND pin 3 (the pin 3 via joins both to the planes)'})
                continue
            layer = p['layers'][0]
            cx, cy = p['at']
            hw, hh = (p['box'][2] - p['box'][0]) / 2, (p['box'][3] - p['box'][1]) / 2
            cands = []
            for gap in GND_GAPS:
                for dx, dy in GND_DIRS:
                    n = math.hypot(dx, dy)
                    ux, uy = dx / n, dy / n
                    reach = (abs(ux) * hw + abs(uy) * hh) if (dx == 0 or dy == 0) else max(hw, hh)
                    at = (r4(cx + ux * (reach + gap)), r4(cy + uy * (reach + gap)))
                    cands.append(([(cx, cy), at], at))
            # dog-legs: out of the pad along an axis, then to the via in any direction (pads in a pin row)
            for leg in (0.4, 0.9, 1.5):
                for dx, dy in GND_DIRS[:4]:
                    reach = abs(dx) * hw + abs(dy) * hh
                    knee = (r4(cx + dx * (reach + leg)), r4(cy + dy * (reach + leg)))
                    for gap in (0.6, 1.0, 1.5, 2.2):
                        for ex, ey in GND_DIRS:
                            if (ex, ey) == (-dx, -dy):
                                continue
                            n = math.hypot(ex, ey)
                            at = (r4(knee[0] + ex / n * gap), r4(knee[1] + ey / n * gap))
                            cands.append(([(cx, cy), knee, at], at))
            cands = [(path, at, True) for path, at in cands]
            # last resort over the J209 contact rows (W2 B2B), where no new via fits: sideways out of the pad, then to the
            # nearest plane via of the J209 GND spine (the bottom side there carries GND copper only)
            for sv in sorted(spine_vias, key=lambda v: (math.hypot(v[0] - cx, v[1] - cy), v)):
                if math.hypot(sv[0] - cx, sv[1] - cy) < 4.0:
                    cands.append(([(cx, cy), (sv[0], cy), sv], sv, False))
            chosen = None
            for path, at, new_via in cands:
                if clear(path, at, layer, new_via):
                    chosen = (path, at, new_via)
                    break
            if chosen is None:
                raise SystemExit(f'make_spec: no GND fan-out via position for {ref}.{p["number"]} at {p["at"]}')
            path, at, new_via = chosen
            vid = f'GND-{ref}-{p["number"]}'
            out_t.append({'id': vid + '-S', 'net': 'GND', 'layer': f'{layer}.Cu', 'width_mm': W_GND,
                          'path': [[r4(x), r4(y)] for x, y in path], 'locked': True,
                          'why': f'GND fan-out of {ref}.{p["number"]} to its plane via' if new_via else
                                 f'GND fan-out of {ref}.{p["number"]} to the J209 GND spine via at {list(at)}'})
            if new_via:
                out_v.append({'id': vid + '-V', 'net': 'GND', 'at': [at[0], at[1]], 'drill_mm': VIA_DRILL,
                              'diameter_mm': VIA_D, 'locked': True, 'why': f'GND plane via of {ref}.{p["number"]}'})
                drills.append((at, VIA_DRILL))
            segs += scripted_segments(out_t[-1:], out_v[-1:] if new_via else [])
            done += 1
    return out_t, out_v, done


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
    'silk_over_copper': 'legend only: the fab clips legend over exposed copper; library outlines of the JST and Samtec LSHM footprints sit close to their pads',
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
        a = anchors[ref]
        anchor = {'at': a['at'], 'align': a['align'], 'rotation': a['rotation'], 'side': a['side']}
        if 'ref_text' in a:
            anchor['ref_text'] = a['ref_text']
        parts.append({'ref': ref, 'source': 'graph', 'anchor': anchor})
    heights, sources = {}, {}
    stack = inp.pspec['parameters']['stack']
    for ref in inp.refs:
        if ref == B2B_REF:
            heights[ref] = stack
            sources[ref] = ('mated LSHM-150-02.5 pair J209 / J208 = the PWR-A to PWR-B gap '
                            f'{stack} mm (pcb/partition-spec.json parameters.stack: Samtec catalogue F-224 lshm.pdf and spec Rev H '
                            '7.9, read 2026-11-07 by W2 B2B); one half alone is lower (b2b.mpn.src lead style -02.5 A 3.95)')
            continue
        heights[ref], sources[ref] = height_of(inp, ref)
    spec = {
        'schema': bg.SPEC_SCHEMA,
        'board_id': BOARD,
        'status': 'MODEL_NOT_FOR_FABRICATION',
        'title': 'PWR-B power mezzanine (PWR_BRANCH_SW + USB_POWER_SW): LNA and USB branch switches, monitors, harness headers',
        'note': ('W2 PCB-PWRB, W2 B2B. Generated by build/kicad/boards/PWR_B/make_spec.py (do not hand-edit; rerun it). Placement '
                 'and the scripted copper are design choices of these packages (build/15 rows W2 PCB-PWRB and W2 B2B); the J209 '
                 'pin map is the graph (pcb/generated/b2b-nets.json contacts). KiCad DRC, the audits and check_boards are '
                 'CI/model results. Not a fabrication release; mezzanine fit, heat and every bench gate stay OPEN.'),
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
                     'B.Cu': 'B2B half J209 (bottom), its GND spine and contact escapes, LAB5 stubs, signals, GND pour'}},
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
                      'refs': {r: r for r in inp.refs}, 'nets': {n: n for n in nets},
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
            'zones': [{'id': 'GND-In1', 'net': 'GND', 'layer': 'In1.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
                       'why': 'GND plane (layer type power, a plane in the DSN): the scripted vias of every SMD GND pad and the THT GND pins join it'},
                      {'id': 'GND-In2', 'net': 'GND', 'layer': 'In2.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
                       'why': 'second GND plane (power layer); solid pad connection: a THT GND pin of J207 had one thermal spoke left on both planes (route run 42417213682). '
                              'Cost: the THT GND pins of J201-J508 join four GND layers without thermal relief, so their hole fill and solder joints are an assembly gate (OPEN, build/15 W2 PCB-PWRB)'}]},
        'post_route_zones': [
            {'id': 'GND-F', 'net': 'GND', 'layer': 'F.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
             'why': 'solid pad connection: thermal spokes of THT header GND pins were starved between the pins (route run 42414083566); '
                    'the solder-joint cost of solid THT connections is an assembly gate (OPEN, see GND-In2)'},
            {'id': 'GND-B', 'net': 'GND', 'layer': 'B.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid'}],
        'edge_keepout': {'width_mm': 0.2, 'layers': ['F.Cu', 'B.Cu'], 'blocks': ['tracks', 'vias'],
                         'why': 'rule-area strips (half-width 0.2) on every outline and cutout edge: the router keeps its copper '
                                '0.35 mm off the edge, above the project copper-to-edge 0.3 (route run 42414083566 had 0.23)'},
        'height_zones': [
            {'region': 'board', 'max_height_mm_from_contract': 'max_component_height', 'side': 'top', 'checked': True,
             'why': 'hB 5.5 (pcb/partition-spec.json parameters.hB): parts on the top side; heights from heights below'},
            {'region': 'board', 'max_height_mm': stack, 'side': 'bottom', 'checked': True,
             'why': 'bottom side: only the B2B half J209 in the PWR-A to PWR-B gap (stack 5.0; mechanical/params/boards.json '
                    'PWR_B b2b.bottom_side)'}],
        'sides': ['top', 'bottom'],
        'max_height_bottom': stack,
        'heights': dict(sorted(heights.items(), key=lambda kv: bg.sort_ref(kv[0]))),
        'heights_source': dict(sorted(sources.items(), key=lambda kv: bg.sort_ref(kv[0]))),
        'branch_exempt': exempt,
        'b2b_pin_map': {
            'connector': f'{B2B_REF} (Samtec LSHM-150-02.5-L-DV-A-N-K-TR, graph ref of design/E2.json, bottom side)',
            'mate': {'board': B2B_MATE_BOARD, 'ref': B2B_MATE_REF,
                     'pin_map': inp.b2b['mating_map']['formula'],
                     'rule': ('PWR_A has no board of record yet (W2 PCB-PWRA-2 not run: area study); when it has one, its spec '
                              f'places {B2B_MATE_REF} on the PWR-A top under {B2B_REF} ({B2B_REF} = {B2B_MATE_REF} mirrored about '
                              f'the strip axis, so {B2B_REF} pad m lies over {B2B_MATE_REF} pad m+1 for m odd and m-1 for m even, '
                              'and the alignment holes coincide) and both specs get the check_boards b2b pair with that pin_map; '
                              'a geometric pad-over-pad check is not in check_boards yet (OPEN, build/15 W2 B2B)')},
            'source': f'pcb/generated/b2b-nets.json sha256 {b2b_sha}',
            'rule': (f'{B2B_REF} pad nets are its graph pins, which equal b2b-nets.json contacts[].pwr_b_pin (make_spec.py '
                     'b2b_pin_map stops on any difference); the map itself is pcb/prepare.py b2b_contacts (pin_map_rule, '
                     'guard_rule in b2b-nets.json)'),
            'contacts': int(inp.b2b['contacts_available']), 'used': pins['used'], 'spare': pins['spare'],
            'needed_with_spare': inp.b2b['totals']['contacts_with_spare']},
        'placement_rules': {
            'edges': 'harness headers on the board edges with the mating face outwards: CTRL-bound J202, J203, J201 and the '
                     'SL3-bound J506 on the bottom edge (courtyards x 59.5-127.5), J508 on the right edge between the hole keepouts '
                     '(y 11-26), the SL2-bound J207 and J204 on the top edge (x 82.5-128.5). This deviates from the contract '
                     'edge_zones (mechanical/generated/contract/boards.json PWR_B: right edge y 0-35 for S02, LAB PORT and LAB BUS; '
                     'top edge x 108-128 for SL2 and S04), which cannot hold these headers: the right edge has only y 9.5-27.5 '
                     'between the hole keepouts for about 82 mm of headers, and the 20 mm top zone is shorter than the 45.8 mm of '
                     'J207 plus J204. OPEN for MECH and PCB-PWRA (build/15 W2 PCB-PWRB): new edge_zones, harness routes, build/16 '
                     'lengths and the SL2 / SL3 slot positions, and the PWR-A bottom-edge power headers kept out of x 59.5-127.5 '
                     '(or PWR_B re-placed); check_boards does not check edge zones',
            'reserve': 'the arm of the L (x 0-42, y 35-110) carries no part: it stays free for the PWR-A windows and edge strips '
                       'that PCB-PWRA places (pcb/partition-budget.json windows and edge strips)',
            'kelvin': 'INA3221 U215 between the ch1-ch3 shunts; every shunt net is scripted copper (current path plus sense '
                      'take-off from the shunt pads) up to the 10 ohm INA3221 filter resistors next to each shunt; the filtered '
                      'input nets E2_U215_IP1-3 / IM1-3 from those resistors to U215 are autorouted as separate nets, not as pairs '
                      '(lengths in build/15 W2 PCB-PWRB), so INA3221 accuracy stays a bench gate; ch4 senses through the B2B to '
                      'U216 on PWR-A'},
        'router': {'tool': 'freerouting', 'max_passes': 60, 'threads': 1, 'job_timeout': '00:25:00', 'timeout_s': 1620,
                   'fanout': False, 'ignore_net_classes': sorted(set(SCRIPTED_CLASSES.values())),
                   'why': 'the fan-out pre-pass escaped every SMD pin with necked-down (0.1124 mm) stubs and dangling vias, and '
                          'the router re-routed the scripted nets because locked copper that crosses a pad is no connection '
                          'for it (route run 42414083566): fan-out off, the scripted classes not autorouted; GND is joined by '
                          'the scripted plane vias of every SMD GND pad (run 42415437982 left 83 GND connections open)'},
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
                      ('PWR3A', nc['classes']['PWR3A']), ('SCRIPTED_GND', nc['classes']['SIG']),
                      ('SCRIPTED_PWR1A', nc['classes']['PWR1A']), ('SCRIPTED_PWR3A', nc['classes']['PWR3A'])):
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


# Board routing classes beyond pcb/generated/netclasses.json (never narrower than its minimum).
# LNA4V5: 2 B2B contacts, up to 1.209 A at the protection limits (b2b-nets.json net_current_extra); routed at the PWR1A
# width 0.35 mm (IPC-2221 external 1 oz about 1.1 A at +10 degC per track, MODEL): a wider track does not leave a 0.30 mm
# J209 pad between its GND neighbours at 0.50 mm pitch (route run 42415437982 on the FX8 placeholder: 0.8 mm could not
# reach its contacts either).
BOARD_CLASSES = {'LNA4V5': 'PWR1A'}
# Nets whose copper is all scripted and locked: widths of their netclasses.json class, not autorouted (router -inc).
SCRIPTED_CLASSES = {'GND': 'SCRIPTED_GND', 'LAB5': 'SCRIPTED_PWR3A',
                    **{f'E2_LNA{ch}_{k}': 'SCRIPTED_PWR1A' for ch in '1234' for k in ('SW', 'SHUNT')}}


# ------------------------------------------------------------------ main
def build(inp):
    anchors = placement(inp)
    missing = [r for r in inp.refs if r not in anchors]
    pins = b2b_pin_map(inp)
    parts = placed_parts(inp, anchors)
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
    gnd_pads = [(r, q['number']) for r, pa in parts.items() for q in pa.pads if q['net'] == 'GND' and q['type'] == 'smd'
                and (r, q['number']) != ('U215', 'EP') and r != B2B_REF]
    gnd_vias = {tuple(t['path'][0]) for t in tracks if t['net'] == 'GND' and t['id'].endswith('-S')}
    for r, n in gnd_pads:
        if tuple(r4(v) for v in parts[r].pad(n)['at']) not in gnd_vias:
            problems.append(f'GND pad {r}.{n} without a plane via')
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
