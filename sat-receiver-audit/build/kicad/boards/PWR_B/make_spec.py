#!/usr/bin/env python3
"""Board spec generator of the PWR-B mezzanine (W2 PCB-PWRB, W2 PCB-PWRB-2). Standard library only.

Run from any directory:
  python build/kicad/boards/PWR_B/make_spec.py            write pcb/boards/PWR_B.json and build/kicad/boards/PWR_B/PWR_B.kicad_pro
  python build/kicad/boards/PWR_B/make_spec.py --check    regenerate in memory and compare with the committed files
  python build/kicad/boards/PWR_B/make_spec.py --svg F    also write a placement preview (courtyards, pads, scripted copper)

What it decides, in one place (the spec records each rule with its source):
  * placement of the PWR_BRANCH_SW / USB_POWER_SW refs of pcb/generated/partition.json on the full L of the W2 MECH-7
    contract (SHRINK-2), top side only, except the B2B half J209 (W2 B2B: Samtec LSHM-150-02.5-L-DV-A-N-K-TR) on the
    bottom side under its mate J208 of the PWR-A placement (W2 PCB-PWRA-3); no top courtyard over a PWR-A cut-out
    (window over a PWR-A part taller than hA, header edge strip, test-point probe window) of
    build/kicad/boards/PWR_A/placement-study-shrink2.json pwr_b_cutouts (W2 PCB-PWRB-2, checked here and, as
    height zones of 0 mm, by pcb/check_boards.py);
  * the B2B pin map: J209 takes its pin nets from the graph, which carries pcb/generated/b2b-nets.json contacts pin for
    pin (checked here; the mating map to J208 on PWR-A is b2b-nets.json mating_map);
  * scripted locked copper: the LAB5 path (J209 contacts -> vias -> F.Cu trunk -> stubs), the Kelvin nets of the
    four LNA shunts (current path and sense take-off from the shunt pads), the J209 GND spine (every GND contact
    joins a B.Cu spine between the two contact rows, with plane vias on it) and a plane via next to every other SMD
    GND pad (gnd_fanout);
  * the 6-layer plan of W2 PWRB-R (S-G-S-S-P-S, JLC06161H-2116 as the 6-layer CTRL: In1.Cu GND and In4.Cu 3V3_Q6A planes
    of type power with a scripted via per SMD pad, signals on F.Cu / In2.Cu / In3.Cu / B.Cu, power classes on F.Cu /
    B.Cu only), the project rules and net classes, and the router settings: Freerouting without its fan-out stage, the
    classes of the scripted nets (SCRIPTED_GND, SCRIPTED_PWR1A, SCRIPTED_PWR3A) not autorouted, rule-area strips on
    every board edge and a rule area on every copper layer over each PWR-A cut-out (planned_cutouts);
  * the J209 escape corridor (W2 PWR-L6-PLACE, corridor_check and the spec key j209_escape): no PWR-A window over a part
    taller than hA in the field under the J209 lower contact row, and no PWR-B part or scripted via in the escape band
    beyond the placement of record; the LAB5 branches to the four TPS2553 at 0.7 mm (>= 0.667 mm, F102 4 A at +20 degC on 2 oz);
  * the zone-2 exit pair (W2 PWR-L6-PLACE third pass, judge decision ESC-JUDGE): J203 (JST PHD B20B-PHDSS) and J506 (JST PH
    B9B-PH-K-S) stand vertical, top entry, in the free part of the bottom edge (contract edge zone 2, x 90-115) under the
    escape band y 11.75-15.4; their height zone is the contract clearance-map zone (height_zones, fits_mm), the rest of the
    board keeps the contract default hB 5.5;
  * the U215.6 / U215.7 I2C2 via in pad (VIA_IN_PAD, filled and capped POFV at order, TBD): the pins face the PWR-A TP104
    probe window, so each pad gets a locked 0.6/0.3 via inside it; 0.197 mm to the neighbour pads is a recorded exception
    to CLEAR + MARGIN 0.20 (KiCad clearance 0.15 met).
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
# PWR-A cut-outs PWR-B must leave free (W2 PCB-PWRA-3 placement study of the SHRINK-2 PWR-A, pwr_b_cutouts)
PWRA_STUDY = BASE / 'build/kicad/boards/PWR_A/placement-study-shrink2.json'

# B2B half on PWR-B (W2 B2B): graph ref J209 (design/E2.json), its mate J208 on the PWR-A top (pcb/partition-spec.json
# b2b.graph_refs). Footprint and MPN come from the graph and the parts DB; the mating map from b2b-nets.json.
B2B_REF, B2B_MATE_BOARD, B2B_MATE_REF = 'J209', 'PWR_A', 'J208'

CLEAR = 0.15          # project clearance (netclasses.json project_defaults)
MARGIN = 0.05         # design margin of the scripted copper over the clearance
EDGE = 0.3            # project copper-to-edge clearance
CRT_GUARD = 0.05      # courtyard boxes here are centre lines; KiCad's include half the 0.05 mm line (review F12 of W2 PCB-PWRB-2, W2 PWRB-R place)
STACKUP_6L = BASE / 'pcb/generated/stackup-6l.json'
# W2 PWRJ-LAYERS6: finished outer copper 2 oz, inner 0.5 oz (pcb/generated/stackup-6l.json copper_options; jlcpcb.com read
# 2026-11-13): the power classes route at their 2 oz outer widths (PWR1A 0.2, PWR2A 0.4, PWR3A 0.95 mm, MODEL)
COPPER_OPTION = 'outer_2oz'
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


def pad_shapes(text):
    """(shape, roundrect ratio) of every pad of a .kicad_mod in file order (the order of bg.footprint_geometry pads); W2
    PWR-L6-PLACE third pass: the scripted-copper clearance check measures circles, ovals and rounded rectangles exactly."""
    out = []
    for node in bg.sexpr(text)[1:]:
        if isinstance(node, list) and node and node[0] == 'pad':
            rr = next((float(n[1]) for n in node if isinstance(n, list) and n and n[0] == 'roundrect_rratio'), 0.0)
            out.append((node[3] if len(node) > 3 and isinstance(node[3], str) else 'rect', rr))
    return out


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
                              'shape': p.get('shape', 'rect'), 'rratio': p.get('rratio', 0.0),
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


def seg_pad_dist(p, q, pad):
    """Distance from segment pq to a pad (0 when they touch): circles, ovals and rounded rectangles exactly (W2 PWR-L6-PLACE
    third pass), any other shape by its box."""
    x0, y0, x1, y1 = pad['box']
    w, h = x1 - x0, y1 - y0
    shape = pad.get('shape', 'rect')
    if shape == 'circle':
        return max(point_seg(pad['at'], p, q) - min(w, h) / 2, 0.0)
    if shape == 'oval':
        r = min(w, h) / 2
        cx, cy = pad['at']
        c1, c2 = ((cx - (w / 2 - r), cy), (cx + (w / 2 - r), cy)) if w >= h else ((cx, cy - (h / 2 - r)), (cx, cy + (h / 2 - r)))
        return max(seg_seg_dist(p, q, c1, c2) - r, 0.0)
    if shape == 'roundrect' and pad.get('rratio'):
        r = pad['rratio'] * min(w, h)
        return max(seg_box_dist(p, q, (x0 + r, y0 + r, x1 - r, y1 - r)) - r, 0.0)
    return seg_box_dist(p, q, pad['box'])


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
def cutouts_digest(placed):
    """sha256 of the PWR-A cut-out list (ref, kind, rect) in canonical JSON."""
    rows = [{'ref': c['ref'], 'kind': c['kind'], 'rect': [float(v) for v in c['rect']]} for c in placed]
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def with_copper_option(nc):
    """netclasses.json with the power-class widths of COPPER_OPTION (pcb/generated/stackup-6l.json, W2 PWRJ-LAYERS6), as
    pcb/check_boards.py board_netclasses applies them to this board."""
    opt = read(STACKUP_6L)['copper_options'][COPPER_OPTION]
    out = {**nc, 'classes': {k: dict(v) for k, v in nc['classes'].items()}}
    for name, w in opt['power_classes'].items():
        out['classes'][name].update({k: w[k] for k in ('outer_min_width_mm', 'outer_ipc_width_mm', 'split_outer_per_layer_mm',
                                                       'inner_min_width_mm')})
    # W2 PWR-L6-PLACE fourth pass, combined (lever 1): the PWR1A sub-classes of the option (PWR05A) take their member nets
    out['nets'] = dict(out['nets'])
    for name, cls in (opt.get('inner_classes') or {}).items():
        out['classes'][name] = {k: v for k, v in cls.items() if k != 'nets'}
        for n in cls['nets']:
            if n in out['nets']:
                out['nets'][n] = {**out['nets'][n], 'class': name}
    return out


class Inputs:
    def __init__(self):
        self.graph = bg.load_graph()
        self.manifest = {f['footprint']: f for f in read(MANIFEST)['footprints']}
        self.partition = read(PARTITION)
        self.b2b = read(B2B_NETS)
        self.netclasses = with_copper_option(read(NETCLASSES))
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
            shapes = pad_shapes(text)
            if len(shapes) == len(self.geo[ref]['pads']):
                self.geo[ref] = {**self.geo[ref], 'pads': [dict(q, shape=s, rratio=r) for q, (s, r) in zip(self.geo[ref]['pads'], shapes)]}
        if B2B_REF not in self.refs:
            raise SystemExit(f'make_spec: {B2B_REF} is not a {BOARD} ref of pcb/generated/partition.json (rerun pcb/prepare.py)')
        study = read(PWRA_STUDY)
        # hash of the cut-out list only: the study itself hashes pcb/boards/PWR_B.json, so a file hash here would never settle
        self.cutouts_sha = cutouts_digest(study['pwr_b_cutouts']['placed'])
        self.cutouts = [dict(c, rect=[float(v) for v in c['rect']]) for c in study['pwr_b_cutouts']['placed']]
        if study['pwr_b_cutouts'].get('unplaced_needing_one'):
            raise SystemExit(f'make_spec: PWR-A parts needing a PWR-B cut-out are unplaced in {PWRA_STUDY.name}')
        # the cut-out boxes [x0, y0, x1, y1] (board mm) count as board edges for copper and vias
        self.cut_boxes = [tuple(c['rect']) for c in self.cutouts]

    def nets_of(self, ref):
        return {str(p['number']): (None if p.get('nc') else p.get('net')) for p in self.graph[ref]['pins']}


# ------------------------------------------------------------------ placement (board mm: contract outline origin, y up, top view)
# Placement (W2 PCB-PWRB-2, SHRINK-2): the full L of the W2 MECH-7 contract less every PWR-A cut-out. Each entry is
# ref: (x, y, rotation[, side]) of the footprint origin (pad 1 of the JST headers), board mm, y up, top view.
#  * J209 (bottom) sits under its mate J208 of the PWR-A placement (98.8, 18.5); J204 and J207 on the top span x 58-107 of
#    contract edge zone 1, their mating faces 4.51 mm inboard of the edge (R-PWRB-EXIT set_back_min_mm of zone 1,
#    mechanical/generated/fit-report.json), the strip in front of them kept free of parts (plug zone, PLUG_ZONES).
#    J207 stands left, over the LAB5 switches whose outputs it takes, J204 right, over the J209 rail block (3V3_Q6A,
#    LNB13V2, LAB5_RLY): the reverse of the MECH-7 order (J207 next to SL2), chosen because the first route with the
#    MECH-7 order left the rail escapes towards J204 unrouted; MECH moves the start points of S04 and S20-S22 / S35 /
#    S36 (build/15 W2 PCB-PWRB-2). Over the rail block stands only the RTL-B filter inductor L210 (next to U210, below
#    J207 pin 4); the SB filter inductor L215 stands below the LAB5 trunk next to U221; the LAB BUS buffer U507 stands in
#    the arm with its I2C partners J201, U215 and J506.
#  * The S02 headers J202 and J201 are parked: zone 0 (right edge) is covered by the PWR-A J104 / J113-J115 / J507 strips
#    and two hole keep-outs. J202 stands in the 10.6 mm column between the PWR-A probe windows TP211 / TP215 and the C262
#    window, J201 in the arm; neither has a harness exit (OPEN, build/15 W2 PCB-PWRB-2).
#  * Zone 2 (bottom span x 90-115), free of PWR-A windows since W2 GR-ZONE2-SMD, holds the vertical top-entry exit pair
#    (W2 PWR-L6-PLACE third pass, judge decision ESC-JUDGE option M): J203 (S02-PWR-SIG-2, JST PHD B20B-PHDSS, pin 1 at
#    (93.3, 9.75), rows y 9.75 / 7.75 right under the J209 escape band) carries the 12 S02 nets of the J209 lower-row
#    contacts 33-41 / 47-59, which close as short fan-out runs; J506 (SL3-PWR-PH, JST PH B9B-PH-K-S, pin 1 at (92.5, 3.55))
#    stands at the edge; C249 (E2_RTLB_SW bypass) moves to (112.85, 3.0, 180) beside J506. A side entry is ruled out
#    (R-PWRB-EXIT: plug proud 2.3 + bundle OD + 0.5 - 0.55 mm room puts the J203 pins on J209).
#  * LNA ch1-ch3 keep the Kelvin cell of the W2 PCB-PWRB lineage (LNA_ROWS) without its output parts (cout, rdamp, test
#    point, damper), which stand near their nets: ch1 in the arm, ch2 between the J105 / J106 strips and J204, ch3 in
#    the upper arm; ch4 over the right half of J209 next to its sense contacts 99 / 100.
#  * ch4 output (iteration 2, review F1 of W2 PCB-PWRB-2): route run 43241032279 left the 62 mm link from the damper C247
#    in the arm to R247 open, and the J209 strip has no room for the ch4 cell, C247 and L210 side by side (each spans
#    the alignment-hole rows y 16.9-18.4 between the holes x 86.0-111.6). So L209 stands 1.2 mm lower than the cell
#    template (LNA_ROW_OFFSETS), C247 stands over it between the J204 courtyard and the J113 strip, with R247, TP209 and
#    TP210 to its right above the J113 strip. C250 (west, next to the L210 output pad) and C246 (east, nearer L209) take
#    the place R247 had over J209, turned so that their GND pads face the J209 spine, and C297 takes the C250 place right
#    of L209. Every other part, and every via between the J209 upper row and the J204 pins or in the B.Cu escape fan of
#    the lower-row contacts 17-59, stays as in route run 43241032279. The ch4 SHUNT sense runs east between L209 and
#    C247 (K4_SH_FY). Route runs of iteration 2 (DRC errors / unconnected; the BIAS_CH4_DAMP link routed in each):
#      43258433850  0 / 12  C250 / C297 vias between the J209 upper row and the J204 pins, C298 in the arm place
#      43261863661  0 / 7   whole ch4 cell 1.2 mm lower, U209 / C244 vias in the lower-row escape fan
#      43264707739  0 / 7   C297 next to L215, its via in the B.Cu fan towards the arm
#      43268279241  1 / 1   only seven ch4 parts moved, C246 west / C297 east in the R247 place (GND-F zone neck)
#      43270598656  0 / 3   C297 west / C246 east in the R247 place
#      43273190849  0 / 2   this placement (board of record: PICO_OFF and I2C2_SCL open, J209 lower row to the arm)
#      43276182228  0 / 17  TP210 in the R247 place
#      43278805983  0 / 11  TP209 and TP210 swapped
#    Freerouting stops after ten passes without a better score, so each small change gives another set of open long
#    nets between the bar and the arm (J209 rows, J204 and U502 to the parked S02 headers, J506, U507 and U218 there);
#    DRC 0 / 0 stays OPEN (build/15 W2 PCB-PWRB-2).
#  * Three LAB5 switches stand on the F.Cu trunk at TY next to the lower-row LAB5 contacts of J209, the fourth west of
#    J207 on a tap (LAB5_CELLS).
#  * The ten 16SVPG47M (dampers C235 C239 C243 C247 C251 C298, C503, C506 C521 C522), the two SOIC-8 blocking stages and
#    L215 take 6 x 8 mm places: C247 the place over L209 above, the others the free places of the cut-out map (the
#    assignment keeps each near its nets where it can); the arm place C247 had before iteration 2 stays free for the
#    arm-to-bar routes (route run 43258433850, with C298 moved there, left arm-to-bar connections open). The remaining
#    parts were packed next to the pads of their nets, 0.2 mm apart.
PLACEMENT = {
    'C232': (2.1, 60.8, 0), 'C233': (10.7, 56.1, 270), 'C234': (15.805, 53.55, 180), 'C235': (18, 49.5, 0),
    'C236': (44.15, 16.2, 0), 'C237': (52.75, 11.5, 270), 'C238': (40.776, 8.8, 0), 'C239': (30, 14, 90),
    'C240': (10.1, 83.7, 0), 'C241': (18.7, 79, 270), 'C242': (16.623, 94.606, 90), 'C243': (13.5, 89.5, 180),
    'C244': (95.211, 13.033, 0), 'C245': (103.6, 14.7, 270), 'C246': (98.85, 19.65, 270), 'C247': (110.98, 21.325, 180),
    'C248': (80.5, 16.9, 0), 'C249': (112.85, 3.0, 180), 'C250': (94.03, 19.65, 270), 'C251': (36, 12, 90),
    'C274': (19.675, 54.5, 270), 'C275': (22.55, 61.925, 180), 'C276': (22.825, 50.9, 270), 'C277': (36.97, 46.405, 90),
    'C282': (54.483, 20.169, 90), 'C283': (26.97, 29.32, 0), 'C284': (23.475, 29.022, 0), 'C285': (38.734, 47.163, 90),
    'C286': (42.496, 27.45, 90), 'C287': (36.764, 49.588, 90), 'C295': (72.5, 16.9, 0), 'C296': (61.947, 8.569, 0),
    'C297': (112.18, 15.097, 90), 'C298': (5.5, 22, 90), 'C501': (59, 23.5, 90), 'C502': (56.5, 25.2, 0),
    'C503': (38.5, 20.5, 0), 'C504': (67, 15.2, 90), 'C505': (64.5, 16.9, 0), 'C506': (37.5, 73, 0),
    'C507': (36.46, 76.867, 0), 'C521': (30.95, 105, 90), 'C522': (36, 90.5, 0), 'C550': (40.625, 47.101, 90),
    'C551': (38.651, 50.429, 90), 'C2901': (55.363, 33.73, 0), 'C2902': (40.167, 77.567, 0), 'C2911': (20.334, 42.046, 0),
    'C2912': (5.654, 98.616, 0), 'D2901': (25.835, 50.625, 0), 'D2902': (5.225, 95.981, 0), 'J201': (7.75, 45.8, 270),
    'J202': (18.08, 27.75, 270), 'J203': (93.3, 9.75, 0), 'J204': (104.55, 24.24, 180), 'J207': (85, 24.24, 180),
    'J209': (98.8, 18.5, 180, 'B'), 'J506': (92.5, 3.55, 0), 'L206': (15.1, 57.8, 0), 'L207': (57.15, 13.2, 0),
    'L208': (23.1, 80.7, 0), 'L209': (108, 15.2, 0), 'L210': (90, 18.5, 0), 'L215': (67, 10, 0), 'Q2901': (25, 45, 90),
    'Q2902': (11, 104, 0), 'Q2911': (23.034, 26.169, 0), 'Q2912': (10.491, 66.069, 0), 'R228': (7.4, 56.2, 270),
    'R229': (2.1, 54.5, 0), 'R231': (9.3, 59.2, 0), 'R232': (11.588, 49.5, 0), 'R233': (49.45, 11.6, 270),
    'R234': (44.15, 9.9, 0), 'R236': (51.35, 14.6, 0), 'R237': (29.288, 8.8, 0), 'R238': (15.4, 79.1, 270),
    'R239': (10.1, 77.4, 0), 'R241': (17.3, 82.1, 0), 'R242': (21.662, 85.5, 180), 'R243': (100.3, 14.8, 270),
    'R244': (76.281, 16.475, 0), 'R246': (102.2, 17.8, 0), 'R247': (117.33, 20.35, 180), 'R248': (77.5, 19.5, 90),
    'R249': (83.5, 18.9, 90), 'R251': (59.385, 19.013, 90), 'R268': (8, 61.9, 90), 'R269': (10.6, 61.9, 90),
    'R270': (50.05, 17.3, 90), 'R271': (52.65, 17.3, 90), 'R272': (16, 84.8, 90), 'R273': (18.6, 84.8, 90),
    'R280': (85.517, 20.651, 90), 'R281': (53.817, 23.411, 90), 'R283': (51.5, 25.856, 90), 'R284': (20.217, 22.522, 90),
    'R286': (42.217, 34.038, 0), 'R287': (44.996, 26.692, 0), 'R293': (69.5, 19.5, 90), 'R294': (75.5, 18.9, 90),
    'R295': (56.789, 19.26, 90), 'R501': (53.5, 27.8, 90), 'R502': (59.5, 27.2, 90), 'R504': (71.783, 12.226, 0),
    'R505': (61.5, 19.5, 90), 'R506': (67.5, 18.9, 90), 'R508': (32.581, 75.617, 90), 'R550': (33.859, 42.821, 90),
    'R551': (35.826, 42.961, 90), 'R2901': (17.112, 44.38, 90), 'R2902': (1.931, 96.061, 90), 'R2911': (30.635, 43.025, 0),
    'R2912': (2.025, 100.365, 90), 'R2921': (48.167, 27.094, 0), 'R2922': (17.073, 98.016, 90),
    'TP206': (12.755, 53.05, 0), 'TP207': (37.667, 31.094, 0), 'TP208': (13.323, 85.016, 0),
    'TP209': (116.3, 22.8, 0), 'TP210': (118.85, 22.8, 0), 'TP216': (92, 13, 0), 'TP2901': (58.876, 33.73, 0),
    'TP2902': (40.679, 80.317, 0), 'U206': (4.1, 57.6, 0), 'U207': (46.15, 13, 0), 'U208': (12.1, 80.5, 0),
    'U209': (97, 16.2, 0), 'U210': (80.5, 20, 90), 'U215': (21.5, 58.5, 0), 'U217': (44.5, 20, 90),
    'U218': (9.5, 32.5, 90), 'U219': (23, 22, 90), 'U221': (72.5, 20, 90), 'U501': (56.5, 28.3, 90),
    'U502': (64.5, 20, 90), 'U507': (4.5, 51, 0),
}
PLUG_ZONES = ('J204', 'J207')   # top-span headers: no part between the mating face and the board edge
# Kelvin cell of each LNA channel (W2 PCB-PWRB lineage): TPS2553 switch, Kelvin shunt, XAL5030, input / shunt capacitors and,
# for ch1-ch3, the two INA3221 filter resistors above the shunt; cell frame mm from the cell origin. The scripted Kelvin
# copper assumes this geometry, so kelvin_cells() checks every channel against it.
LNA_ROWS = [('U', 5.0, 5.0, 0), ('cin', 3.0, 8.2, 0), ('ren', 3.0, 1.9, 0), ('rilim', 8.3, 3.6, 270), ('rsh', 10.2, 6.6, 0),
            ('csh', 11.6, 3.5, 270), ('L', 16.0, 5.2, 0), ('rsp', 8.9, 9.3, 90), ('rsm', 11.5, 9.3, 90)]
LNA_CELLS = {'1': dict(U='U206', cin='C232', ren='R229', rilim='R228', rsh='R231', csh='C233', L='L206', rsp='R268', rsm='R269'),
             '2': dict(U='U207', cin='C236', ren='R234', rilim='R233', rsh='R236', csh='C237', L='L207', rsp='R270', rsm='R271'),
             '3': dict(U='U208', cin='C240', ren='R239', rilim='R238', rsh='R241', csh='C241', L='L208', rsp='R272', rsm='R273'),
             '4': dict(U='U209', rilim='R243', rsh='R246', csh='C245', L='L209')}
# Per-channel offsets from LNA_ROWS (mm): ch4's inductor L209 stands 1.2 mm lower than the template, so that the damper
# C247 fits above it under the J206 strip and clear of the J209 alignment hole (iteration 2 of W2 PCB-PWRB-2, review F1);
# its current path from the shunt runs down into the inductor pad (K{ch}-SH-I).
LNA_ROW_OFFSETS = {'4': {'L': (0.0, -1.2)}}


def kelvin_cells(anchors):
    """Problems where a channel's parts are not at their LNA_ROWS offsets (plus LNA_ROW_OFFSETS) from its switch (rotation
    included)."""
    out = []
    for ch, refs in LNA_CELLS.items():
        u = anchors[refs['U']]
        ox, oy = u['at'][0] - 5.0, u['at'][1] - 5.0
        for key, x, y, rot in LNA_ROWS:
            ref = refs.get(key)
            dx, dy = LNA_ROW_OFFSETS.get(ch, {}).get(key, (0.0, 0.0))
            x, y = x + dx, y + dy
            if ref and (abs(anchors[ref]['at'][0] - (ox + x)) > 1e-6 or abs(anchors[ref]['at'][1] - (oy + y)) > 1e-6
                        or anchors[ref]['rotation'] != rot % 360 or anchors[ref]['side'] != 'F'):
                out.append(f'LNA ch{ch}: {ref} is not at its Kelvin cell place ({key})')
    return out
B2B_AT = (98.8, 18.5)
B2B_ROT = 180
TY = 14.3       # LAB5 F.Cu trunk centre line (2.0 mm: y 13.3-15.3, above the PWR-A J108 / J112 strips and the TP205 window)
LAB5_VY = 15.35  # LAB5 vias below the lower J209 contact row
# LAB5 switch cells (cell frame: x from the switch axis, y from the LAB5 run under the cell). The switch stands at 90 deg
# (pins 1-3 towards the run: pin 1 IN, 2 GND, 3 EN); its LAB5 branch rises from the run to pin 1 through pad 1 of the
# input capacitor cA; the 100 nF cB sits with pad 1 on the run; the current-limit resistor stands left of the switch.
# Three cells stand on the trunk (run = TY). The fourth (U501, RTL-A) has no place on the trunk: east of U210 the
# J209 alignment hole and the GND spine under the rail block leave no fan-out for its GND pin, west of U502 stand the
# PWR-A TP205 probe window and the ch2 Kelvin cell; it stands west of J207 instead, fed by a LAB5 tap off the west end of
# the trunk (x LAB5_TAP_X, up to the run y LAB5_TAP_Y under the cell).
LAB5_CELLS = [  # switch axis x, run y, refs
    (64.5, TY, dict(U='U502', cA='C505', cB='C504', ren='R506', rilim='R505')),
    (72.5, TY, dict(U='U221', cA='C295', ren='R294', rilim='R293')),
    (80.5, TY, dict(U='U210', cA='C248', ren='R249', rilim='R248')),
    (56.5, 22.6, dict(U='U501', cA='C502', cB='C501', ren='R502', rilim='R501'))]
LAB5_TAP_X = 62.6   # LAB5 tap: west end of the trunk, between R505 and the U502 branch
LAB5_TAP_Y = 22.6   # run of the fourth cell: below the J207 pin 12 pad (y >= 23.37), above U502's current-limit resistor


def placement(inp):
    """Anchor of every template ref (footprint origin)."""
    anchors = {}
    for ref, row in PLACEMENT.items():
        side = row[3] if len(row) > 3 else 'F'
        anchors[ref] = {'at': [row[0], row[1]], 'align': 'origin', 'rotation': row[2] % 360, 'side': side}
    if tuple(anchors[B2B_REF]['at']) != B2B_AT or anchors[B2B_REF]['side'] != 'B':
        raise SystemExit(f'make_spec: {B2B_REF} must stand at {B2B_AT} on the bottom side')
    return anchors


# ------------------------------------------------------------------ geometry checks (before CI)
def placed_parts(inp, anchors):
    return {ref: Placed(ref, inp.geo[ref], inp.fab[ref], anchor, inp.nets_of(ref)) for ref, anchor in anchors.items()}


def all_cuts(inp):
    """Contract cutouts plus the PWR-A cut-outs (W2 PCB-PWRB-2): both are board edges for parts, copper and vias here,
    because the cut-outs become Edge.Cuts once the MECH lineage writes them into the contract (build/15 W2 PCB-PWRB-2)."""
    return list(bg.cutout_boxes(inp.contract)) + list(inp.cut_boxes)


def cutout_overlay(inp, parts, step=0.1):
    """Acceptance check of W2 PCB-PWRB-2: every PWR-B courtyard (top side; the bottom carries only J209 in the stack gap)
    against every PWR-A cut-out, exact rectangle intersection plus a raster overlay of the union (step mm); also the
    usable area (L outline less the cut-out union and the hole keep-outs) and the courtyard fill. MODEL."""
    pairs = []
    for ref in sorted(parts, key=bg.sort_ref):
        pa = parts[ref]
        if pa.side != 'F':
            continue
        for c in inp.cutouts:
            r = c['rect']
            w = min(pa.box[2], r[2]) - max(pa.box[0], r[0])
            h = min(pa.box[3], r[3]) - max(pa.box[1], r[1])
            if w > 0 and h > 0:
                pairs.append({'ref': ref, 'cutout': c['ref'], 'kind': c['kind'], 'mm2': r4(w * h)})
    c = inp.contract
    outline = [tuple(p) for p in c['outline_mm']]
    holes = [tuple(h) for h in c['holes_mm']]
    kr = c['hole_keepout_d'] / 2
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    nx, ny = int(round((max(xs) - min(xs)) / step)), int(round((max(ys) - min(ys)) / step))
    tops = [p.box for p in parts.values() if p.side == 'F']
    usable = cut = overlap = 0
    for i in range(nx):
        x = min(xs) + (i + 0.5) * step
        col_cuts = [r for r in inp.cut_boxes if r[0] <= x <= r[2]]
        col_tops = [b for b in tops if b[0] <= x <= b[2]]
        for j in range(ny):
            y = min(ys) + (j + 0.5) * step
            if not point_in_poly((x, y), outline):
                continue
            in_cut = any(r[1] <= y <= r[3] for r in col_cuts)
            if in_cut:
                cut += 1
                if any(b[1] <= y <= b[3] for b in col_tops):
                    overlap += 1
                continue
            if any((x - hx) ** 2 + (y - hy) ** 2 < kr * kr for hx, hy in holes):
                continue
            usable += 1
    a = step * step
    top = sum((b[2] - b[0]) * (b[3] - b[1]) for b in tops)
    b2b = parts[B2B_REF].box
    b2b_area = (b2b[2] - b2b[0]) * (b2b[3] - b2b[1])
    return {'pairs': pairs, 'raster_step_mm': step, 'cutout_union_mm2': round(cut * a, 1), 'overlap_mm2': round(overlap * a, 1),
            'usable_mm2': round(usable * a, 1), 'top_courtyards_mm2': round(top, 1), 'b2b_courtyard_mm2': round(b2b_area, 1),
            'fill_top': round(top / (usable * a), 4), 'fill_with_b2b': round((top + b2b_area) / (usable * a), 4)}


def check_placement(inp, parts):
    problems = []
    c = inp.contract
    outline = [tuple(p) for p in c['outline_mm']]
    cuts = all_cuts(inp)
    holes = [(tuple(h), c['hole_keepout_d'] / 2) for h in c['holes_mm']]
    refs = sorted(parts, key=bg.sort_ref)
    for i, a in enumerate(refs):
        pa = parts[a]
        corners = [(pa.box[0], pa.box[1]), (pa.box[2], pa.box[1]), (pa.box[2], pa.box[3]), (pa.box[0], pa.box[3])]
        if not all(point_in_poly(q, outline) for q in corners):
            problems.append(f'{a}: courtyard {pa.box} leaves the outline')
        for cut in cuts:
            if pa.side == 'F' and bg.rects_overlap(pa.box, cut, CRT_GUARD):
                problems.append(f'{a}: courtyard within {CRT_GUARD} mm of the cutout {cut}')
        for name in PLUG_ZONES:
            hb = parts[name].box
            if a not in PLUG_ZONES and pa.side == 'F' and bg.rects_overlap(pa.box, (hb[0], hb[3], hb[2], c['outline_mm'][2][1])):
                problems.append(f'{a}: courtyard in the plug zone in front of {name}')
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



def tht_fields(parts):
    """(ref, THT pin count, pin field box [x0, y0, x1, y1]) of every through-hole part (H-TRIM marking)."""
    out = []
    for ref, pa in parts.items():
        pads = [p for p in pa.pads if p['type'] == 'thru_hole']
        if pads:
            out.append((ref, len(pads), [r4(min(p['box'][0] for p in pads)), r4(min(p['box'][1] for p in pads)),
                                         r4(max(p['box'][2] for p in pads)), r4(max(p['box'][3] for p in pads))]))
    return out


def move_edge_references(inp, anchors, parts):
    """Put the reference legend on the part centre where the library position leaves the board or a cutout
    (KiCad silk_edge_clearance), by the board_gen anchor key ref_text."""
    c = inp.contract
    outline = [tuple(p) for p in c['outline_mm']]
    cuts = all_cuts(inp)
    def fits(x, y, n, vertical):
        hw, hh = (0.9, 0.5 * n + 0.4) if vertical else (0.5 * n + 0.4, 0.9)
        box = (x - hw, y - hh, x + hw, y + hh)
        corners = ((box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3]))
        return all(point_in_poly(q, outline) and edge_dist(q, outline, cuts) >= 0.3 for q in corners) and \
            not any(bg.rects_overlap(box, cut) for cut in cuts)
    for ref, pa in parts.items():
        x, y = pa.map(inp.refpos[ref])
        n = max(2, len(ref))
        b = pa.box
        near = min(edge_dist(q, outline, []) for q in ((b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])))
        # the legend turns with the footprint (W2 PCB-PWRB-2: route run 43222835469 had three legends of turned parts
        # over the board edge); within 3 mm of the outline the legend goes to the part centre, along the nearest edge
        # (route run 43236259234: one more legend over the arm edge)
        if near >= 3.0 and fits(x, y, n, anchors[ref]['rotation'] % 180 == 90):
            continue
        cx, cy = r4((b[0] + b[2]) / 2), r4((b[1] + b[3]) / 2)
        edges = list(zip(outline, outline[1:] + outline[:1]))
        e = min(edges, key=lambda ab: point_seg((cx, cy), ab[0], ab[1]))
        vertical = abs(e[0][0] - e[1][0]) < 1e-9
        if not fits(cx, cy, n, vertical) and fits(cx, cy, n, not vertical):
            vertical = not vertical
        anchors[ref]['ref_text'] = {'at': [cx, cy], 'angle': 90 if vertical else 0}


def copper_items(parts):
    """Pads as (net, layer, box) for the clearance check of the scripted copper."""
    out = []
    for ref, pa in parts.items():
        for p in pa.pads:
            if p['type'] == 'smd' and not p['number']:
                continue  # unnumbered SMD pads of the library footprints are paste apertures (F.Paste only)
            for layer in (p['layers'] + INNER_ROUTING if p['type'] in ('thru_hole', 'np_thru_hole') else p['layers']):
                out.append({'ref': ref, 'pad': p['number'], 'net': p['net'], 'layer': layer, 'box': p['box'],
                            'npth': p['type'] == 'np_thru_hole', 'at': p['at'], 'shape': p.get('shape', 'rect'),
                            'rratio': p.get('rratio', 0.0)})
    return out


INNER_ROUTING = ('In2', 'In3')  # the inner routing layers (W2 PWRB-R plan); THT pads and vias exist there too


def scripted_segments(tracks, vias):
    segs = []
    for t in tracks:
        layer = t['layer'].split('.')[0] if t['layer'].startswith('In') else t['layer'][0]
        for a, b in zip(t['path'], t['path'][1:]):
            segs.append({'id': t['id'], 'net': t['net'], 'layer': layer, 'a': tuple(a), 'b': tuple(b), 'r': t['width_mm'] / 2})
    for v in vias:
        for layer in ('F', 'B') + INNER_ROUTING:
            segs.append({'id': v['id'], 'net': v['net'], 'layer': layer, 'a': tuple(v['at']), 'b': tuple(v['at']),
                         'r': v['diameter_mm'] / 2, 'via': True})
    return segs


def check_copper(inp, parts, tracks, vias):
    problems = []
    pads = copper_items(parts)
    c = inp.contract
    outline = [tuple(p) for p in c['outline_mm']]
    cuts = all_cuts(inp)
    holes = [(tuple(h), c['hole_keepout_d'] / 2) for h in c['holes_mm']]
    segs = scripted_segments(tracks, vias)
    need = CLEAR + MARGIN
    for s in segs:
        for p in pads:
            if p['layer'] != s['layer'] or (p['net'] == s['net'] and not p['npth']):
                continue
            gap = 0.25 + MARGIN if p['npth'] else need
            if s['id'] in VIA_IN_PAD and p['ref'] == VIA_IN_PAD[s['id']][0]:
                gap = min(gap, VIP_GAP - 1e-6)   # recorded via-in-pad exception (spec via_in_pad): KiCad clearance 0.15 met
            d = seg_pad_dist(s['a'], s['b'], p) - s['r']
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
            lay = p['layers'] + INNER_ROUTING if p['type'] in ('thru_hole', 'np_thru_hole') else p['layers']
            if s['layer'] in lay and seg_box_dist(s['a'], s['b'], p['box']) <= s['r'] + 1e-6:
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
# W2 PWR-L6-PLACE: the LAB5 branches to the four TPS2553 are 0.7 mm >= 0.667 mm, the IPC-2221 width of the F102 rating (4 A)
# at +20 degC on the 2 oz outer copper (external k 0.048, foil 0.070 mm; MODEL), so a branch fault up to the LAB5 fuse stays
# within the protective rise (W2 PWR-L6 synthesis; 0.6 mm before)
W_TRUNK, W_BRANCH, W_CURRENT, W_SENSE = 2.0, 0.7, 0.5, 0.35
# W2 PWR-L6-PLACE third pass (judge decision ESC-JUDGE, the R lever kept): via in pad of the INA3221 U215 I2C2 pins 6 / 7, which
# face the PWR-A TP104 probe window (no F.Cu escape); 0.6 / 0.3 mm, staggered along the 0.75 mm pads so that the holes keep
# the 0.5 mm hole-to-hole rule with margin (0.851 mm centres); the via copper is 0.197 mm from the neighbour pads 5 / 7 and
# 6 / 8 (KiCad clearance 0.15 met, below CLEAR + MARGIN 0.20: recorded exception, spec via_in_pad); JLC fills and caps
# via-in-pad by default from 6 layers ('Compatible with via diameters from 0.15 to 0.55 mm': hole or finished diameter not
# stated, TBD at order; https://jlcpcb.com/capabilities/pcb-capabilities read 2026-11-13); assembly gate OPEN
VIP_D, VIP_GAP = 0.6, 0.197
VIA_IN_PAD = {'VIP-U215-6': ('U215', '6', 'I2C2_SCL', (21.175, 56.35)), 'VIP-U215-7': ('U215', '7', 'I2C2_SDA', (21.825, 56.90))}
# W2 PWR-L6-PLACE fourth pass, probe A: deterministic escape fan of the four innermost J202-bound contacts of the J209 lower
# row (25, 27, 29, 31 at 0.5 mm pitch; the greedy A* reached at most three of them in any order, PLACE third pass). The band
# y 14.3-15.35 between the J209 pads (y >= 15.9) and the F.Cu pads of TP216 / C244 (y <= 13.76) holds no four vias with
# their stubs at CLEAR + MARGIN 0.20 while the neighbour contacts 23 (EN_BONI, its via of record) and 33 (FLT_BONI, straight
# down) keep their escapes (MODEL search on a 0.1 mm grid, 0 solutions). So each contact leaves its row on a B.Cu stub
# (0.15 mm, the SIG width) 1.05 mm straight down and then diagonally to a locked via in the deep row under TP216 / C244
# (y 11.0-12.0, above the J203 pins at y <= 10.35); three of the vias stand in the J203 courtyard strip of the exit field
# (tented, no part there; corridor_check allows ESC-J209- vias). Offsets from the pad centre: (knee dy, via dx, via dy);
# the search kept CLEAR + MARGIN 0.20 to every pad and scripted item, the 0.9 mm via centre rule and EN_BONI's escape.
FAN_NETS = ('EN_HFP', 'EN_LIME3V3', 'EN_LNB', 'FAULT_HFP')
FAN_OFFSETS = None   # probe A, variant (ii): the escapes are planned links of route-planned-6l.json (route push 1 used ((-1.05, -1.15, -5.65), (-1.05, -0.85, -5.15), (-1.05, -0.55, -4.65), (-1.05, -0.05, -4.95)))
W_FAN = 0.15
# J209 escape copper (W2 B2B). The LSHM pads are 0.30 mm wide at 0.50 mm pitch (0.20 mm gaps), and every rail contact has a
# GND neighbour in its row (b2b-nets.json guard_rule), so: GND contacts join a B.Cu spine between the rows (inwards), rail
# and signal contacts escape outwards, and copper that enters a pad between two neighbours is at most W_PADSTUB wide.
W_PADSTUB = 0.25          # into a 0.30 mm pad beside a neighbour: 0.225 mm gap (clearance 0.15 + margin 0.05)
W_SPINE = 1.4             # GND spine on the connector centre line: 0.40 mm from the inner pad ends of both rows
SPINE_STUB = 0.5          # GND stubs end 0.5 mm off the spine centre line, so no stub end lies inside a spine via
NPTH_CLEAR = 0.25 + 0.05  # copper to the J209 alignment-post holes (KiCad hole clearance 0.25, design margin 0.05)
SPINE_VIAS_MIN = 4
SPINE_VIA_PITCH = 1.2     # spine plane vias at least this far apart: 0.5 mm between them for one F.Cu track
W_PAIR = 0.8              # copper of one LAB5 contact pair (2 A): PWR2A width (netclasses.json)
K4_UP_VY = 22.0           # ch4 SW sense: via above the upper J209 row (pad tops 21.1), below the J207 pins (23.4)
K4_SH_FY = 19.4           # ch4 SHUNT sense: F.Cu east above R246 (pads to 18.7), L209 (pads to 17.55) and the alignment
                          # hole (box to 18.4), below C247 (pads from 20.5), to its via right of the alignment hole
K4_LO_VY = 14.9           # ch4 SHUNT sense: B.Cu west under the lower J209 row (pad bottoms 15.9) into its contact


def via_spot_ok(inp, parts, tracks, vias, at, net):
    """A through via of `net` at `at` keeps CLEAR + MARGIN from every pad of both sides and any net (no via in a pad), from
    scripted copper of other nets, the edges and hole keepouts, and the hole-to-hole rule (with margin) to drilled holes."""
    c = inp.contract
    outline = [tuple(p) for p in c['outline_mm']]
    cuts = all_cuts(inp)
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
    # W2 PWR-L6-PLACE third pass: the U215 I2C2 pins 6 / 7 face the PWR-A TP104 probe window, so each gets a locked via in its
    # pad (VIA_IN_PAD); the router escapes from them on the inner layers or B.Cu
    for vid, (ref, pin, net, at) in VIA_IN_PAD.items():
        pad = parts[ref].pad(pin)
        b = pad['box']
        if pad['net'] != net or not (b[0] <= at[0] <= b[2] and b[1] <= at[1] <= b[3]):
            raise SystemExit(f'make_spec: via in pad {vid} at {at} is not inside {ref}.{pin} ({net}) {b}')
        vias.append({'id': vid, 'net': net, 'at': [r4(at[0]), r4(at[1])], 'drill_mm': VIA_DRILL, 'diameter_mm': VIP_D,
                     'locked': True, 'why': f'via in pad of {ref}.{pin} ({net}): the pin faces the PWR-A TP104 probe window; '
                                            f'filled and capped (POFV) at order, recorded exception {VIP_GAP} mm to the '
                                            f'neighbour pads (via_in_pad)'})

    def row(n):  # upper / lower contact row of J209 on the board (rotation 180: odd contacts lower, even upper)
        return 'upper' if j.pad(n)['at'][1] > B2B_AT[1] else 'lower'
    # LAB5: four J209 contacts (b2b-nets.json: ceil(4 A / 1 A)), all in the lower row (contacts 1, 5, 9, 13 of the
    # pin map). Each contact: a B.Cu stub out of the row to its via below the row (LAB5_VY), an F.Cu stub (PWR2A) from the
    # via into the 2.0 mm F.Cu trunk at TY, which runs west to the four switch cells and ends at pad 1 of the last cB.
    lab5 = sorted((n for n, net in pins['pins'].items() if net == 'LAB5'), key=int)
    if not lab5 or any(row(n) != 'lower' for n in lab5):
        raise SystemExit(f'make_spec: the LAB5 contacts {lab5} of {B2B_REF} are not all in the lower row (pin map changed)')
    for n in lab5:
        x = P(B2B_REF, n)[0]
        T(f'LAB5-J209-{n}', 'LAB5', 'B.Cu', W_PADSTUB, [P(B2B_REF, n), (x, LAB5_VY)],
          f'out of J209 contact {n} (lower row) between its GND neighbours to its via: one contact, at most 1 A')
        V(f'LAB5-V-{n}', 'LAB5', (x, LAB5_VY), f'LAB5 via of J209 contact {n}')
        T(f'LAB5-V-{n}-F', 'LAB5', 'F.Cu', W_PAIR, [(x, LAB5_VY), (x, TY)], f'LAB5 via of contact {n} into the trunk')
    last = max([P(B2B_REF, n)[0] for n in lab5] + [P(refs['cB'], '1')[0] for _cx, y, refs in LAB5_CELLS if 'cB' in refs and y == TY])
    T('LAB5-TRUNK', 'LAB5', 'F.Cu', W_TRUNK, [(LAB5_TAP_X, TY), (last, TY)],
      'LAB5 trunk from the J209 contacts to the TPS2553 inputs: PWR3A width 2.0 mm >= 1.85 (netclasses.json)')
    exempt = {}
    for cx, ry, refs in LAB5_CELLS:
        u = refs['U']
        pin1 = P(u, '1')
        if ry == TY:
            T(f'LAB5-BR-{u}', 'LAB5', 'F.Cu', W_BRANCH, [(cx - 0.95, TY), (cx - 0.95, pin1[1])],
              f'branch to {u} IN through pad 1 of {refs["cA"]}; carries at most the {u} current limit')
            reach = 5.0
        else:
            T(f'LAB5-TAP-{u}', 'LAB5', 'F.Cu', W_PAIR, [(LAB5_TAP_X, TY), (LAB5_TAP_X, ry), (cx - 0.95, ry)],
              f'LAB5 tap from the west end of the trunk to the {u} cell (PWR2A width 0.8 mm), through pad 1 of {refs.get("cB")}')
            T(f'LAB5-BR-{u}', 'LAB5', 'F.Cu', W_BRANCH, [(cx - 0.95, ry), (cx - 0.95, pin1[1])],
              f'branch to {u} IN through pad 1 of {refs["cA"]}; carries at most the {u} current limit')
            reach = round(abs(ry - TY) + abs(LAB5_TAP_X - cx + 0.95) + abs(pin1[1] - ry) + 2.0, 1)
        exempt[u] = {'max_mm': reach, 'min_width_mm': W_BRANCH,
                     'reason': f'LAB5 branch from the 2.0 mm trunk to {u} IN (pin 1), through the input capacitor {refs["cA"]}: '
                               f'it carries at most the TPS2553 limit of {u} (<= 0.825 A, tools/assembly_data.py NET_CURRENT), '
                               f'and is {W_BRANCH} mm wide, at least the 0.667 mm that F102 (4 A) needs at +20 degC on the '
                               f'2 oz outer copper (IPC-2221 external, MODEL; W2 PWR-L6-PLACE); the SOT-23-6 pin pitch 0.95 mm '
                               f'does not take the PWR3A width'}
    exempt[B2B_REF] = {'max_mm': 10.0, 'min_width_mm': W_PADSTUB,
                       'reason': 'J209 contact escapes (Samtec LSHM-150, pads 0.30 mm at 0.50 mm pitch, a GND or rail '
                                 'neighbour 0.20 mm away): every contact carries at most 1 A (b2b_i_pin_A, '
                                 'pcb/partition-spec.json b2b.i_pin_note), its stub is 0.25 mm wide inside the row up to its via, '
                                 'from where an 0.8 mm F.Cu stub joins the 2.0 mm LAB5 trunk; the 1.85 mm of PWR3A does not fit '
                                 'between 0.30 mm pads'}
    lab5_pads = [(B2B_REF, n) for n in lab5] + [(refs['U'], '1') for _cx, _y, refs in LAB5_CELLS] + \
        [(refs['cA'], '1') for _cx, _y, refs in LAB5_CELLS] + [(refs['cB'], '1') for _cx, _y, refs in LAB5_CELLS if 'cB' in refs]
    pins['scripted_nets']['LAB5'] = lab5_pads
    # Kelvin shunts of the four LNA channels: current path and sense take-off from the shunt pads (cell frame of LNA_ROWS).
    chans = [('1', 'U206', 'R231', 'L206', 'C233', 'R268', 'R269'), ('2', 'U207', 'R236', 'L207', 'C237', 'R270', 'R271'),
             ('3', 'U208', 'R241', 'L208', 'C241', 'R272', 'R273'), ('4', 'U209', 'R246', 'L209', 'C245', None, None)]
    for ch, u, rsh, ind, csh, rsp, rsm in chans:
        sw, shunt = f'E2_LNA{ch}_SW', f'E2_LNA{ch}_SHUNT'
        u6, s1, s2, l1, c1 = P(u, '6'), P(rsh, '1'), P(rsh, '2'), P(ind, '1'), P(csh, '1')
        T(f'K{ch}-SW-I', sw, 'F.Cu', W_CURRENT, [u6, (s1[0] - 0.84, u6[1]), s1],
          f'{u} OUT to the {rsh} current pad (Kelvin: current enters from the side)')
        T(f'K{ch}-SH-I', shunt, 'F.Cu', W_CURRENT, [s2, (l1[0], s2[1]), l1], f'{rsh} to {ind} (current path)')
        T(f'K{ch}-SH-C', shunt, 'F.Cu', W_CURRENT, [c1, (c1[0], s2[1])], f'{csh} to the {rsh} shunt-side pad')
        if rsp:
            p1, m1 = P(rsp, '1'), P(rsm, '1')
            T(f'K{ch}-SW-S', sw, 'F.Cu', W_SENSE, [(p1[0], s1[1]), p1], f'Kelvin sense: {rsh} pad 1 to the INA3221 filter {rsp}')
            T(f'K{ch}-SH-S', shunt, 'F.Cu', W_SENSE, [(m1[0], s2[1]), m1], f'Kelvin sense: {rsh} pad 2 to the INA3221 filter {rsm}')
            pins['scripted_nets'][sw] = [(u, '6'), (rsh, '1'), (rsp, '1')]
            pins['scripted_nets'][shunt] = [(rsh, '2'), (ind, '1'), (csh, '1'), (rsm, '1')]
            continue
        # ch4: the sense pair crosses the B2B to INA3221 #2 U216 on PWR-A (declared sense pair, partition-spec b2b). Its
        # contacts are J209 column 50 at the right end of the strip: SW in the upper row, SHUNT in the lower row. The shunt
        # R246 stands over the J209 contact rows, where no via fits and the B.Cu carries the GND spine, so each take-off leaves the top of
        # its shunt pad on F.Cu (the current path enters pad 1 from the left and leaves pad 2 to the right and below):
        #  * SW: F.Cu up to a via above the upper row (K4_UP_VY), B.Cu east over the spare upper contacts and down into its
        #    contact from above;
        #  * SHUNT: F.Cu up to K4_SH_FY, east past L209 to a via right of the J209 alignment hole, B.Cu down and west under
        #    the lower row into its contact from below.
        ksw = next(n for n, v in pins['pins'].items() if v == sw)
        ksh = next(n for n, v in pins['pins'].items() if v == shunt)
        if (row(ksw), row(ksh)) != ('upper', 'lower') or j.pad(ksw)['at'][0] != j.pad(ksh)['at'][0]:
            raise SystemExit(f'make_spec: J209 {sw} {ksw} / {shunt} {ksh} are not one column (SW upper, SHUNT lower)')
        b1, b2 = parts[rsh].pad('1')['box'], parts[rsh].pad('2')['box']
        bx, by = P(B2B_REF, ksw)
        T('K4-SW-S', sw, 'F.Cu', W_SENSE, [(s1[0], b1[3]), (s1[0], K4_UP_VY)], f'Kelvin sense: top of {rsh} pad 1 to its via')
        V('K4-SW-V', sw, (s1[0], K4_UP_VY), f'Kelvin sense {sw} to J209 contact {ksw} (bottom side)')
        end = j.pad(ksw)['box'][3] + 0.3
        T('K4-SW-B', sw, 'B.Cu', W_SENSE, [(s1[0], K4_UP_VY), (bx, K4_UP_VY), (bx, end)], f'Kelvin sense to J209 contact {ksw}')
        T('K4-SW-P', sw, 'B.Cu', W_PADSTUB, [(bx, end), (bx, by)], f'into J209 contact {ksw} between its neighbours')
        hole = max((p['box'] for p in j.pads if p['type'] == 'np_thru_hole'), key=lambda h: h[0])
        xs = r4(hole[2] + NPTH_CLEAR + W_SENSE / 2 + 0.25)
        T('K4-SH-S', shunt, 'F.Cu', W_SENSE, [(s2[0], b2[3]), (s2[0], K4_SH_FY), (xs, K4_SH_FY)],
          f'Kelvin sense: top of {rsh} pad 2 east past {ind} to its via right of the J209 alignment hole')
        V('K4-SH-V', shunt, (xs, K4_SH_FY), f'Kelvin sense {shunt} to J209 contact {ksh} (bottom side)')
        bx, by = P(B2B_REF, ksh)
        end = j.pad(ksh)['box'][1] - 0.3
        T('K4-SH-B', shunt, 'B.Cu', W_SENSE, [(xs, K4_SH_FY), (xs, K4_LO_VY), (bx, K4_LO_VY), (bx, end)],
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
    # plane vias SPINE_VIA_PITCH apart where a via clears the top-side pads over J209 (W2 PCB-PWRB-2: the fourth LAB5
    # switch and the ch4 Kelvin cell stand over the strip, so the vias are not limited to the GND columns any more; the
    # B.Cu between the rows carries only the spine, every rail and signal contact escapes outwards)
    k, last, x = 0, None, x0
    while x <= x1 + 1e-9:
        if (last is None or x - last >= SPINE_VIA_PITCH - 1e-9) and min(abs(x - x0), abs(x - x1)) >= VIA_D / 2 + 0.05 \
                and via_spot_ok(inp, parts, tracks, vias, (x, sy), 'GND'):
            k += 1
            V(f'GND-J209-V{k}', 'GND', (x, sy), 'plane via on the J209 GND spine')
            last = x
        x = r4(x + 0.05)
    if k < SPINE_VIAS_MIN:
        raise SystemExit(f'make_spec: only {k} plane vias fit on the J209 GND spine (need {SPINE_VIAS_MIN})')
    pins['scripted_nets']['GND'] = [(B2B_REF, n) for n in gnd]
    gt, gv, _n = gnd_fanout(inp, parts, tracks, vias)
    qt, qv = q6a_plane_copper(inp, parts, tracks + gt, vias + gv, pins)
    pt, pv = planned_copper(parts, pins)
    et, ev = escape_fan(parts, pins)
    return tracks + gt + qt + pt + et, vias + gv + qv + pv + ev, exempt


def escape_fan(parts, pins):
    """W2 PWR-L6-PLACE fourth pass, probe A: the locked escape fan of the J209 lower-row contacts of FAN_NETS (FAN_OFFSETS)."""
    if not FAN_OFFSETS:
        return [], []
    j = parts[B2B_REF]
    at = {net: n for n, net in pins['pins'].items() if net in FAN_NETS}
    xs = [j.pad(at[net])['at'] if net in at else None for net in FAN_NETS]
    if None in xs or any(p[1] >= B2B_AT[1] for p in xs) or \
            any(abs(b[0] - a[0] - 0.5) > 1e-6 or abs(b[1] - a[1]) > 1e-6 for a, b in zip(xs, xs[1:])):
        raise SystemExit(f'make_spec: the J209 contacts of {FAN_NETS} are not four neighbours of the lower row (pin map changed)')
    out_t, out_v = [], []
    for net, (px, py), (knee, dx, dy) in zip(FAN_NETS, xs, FAN_OFFSETS):
        n = at[net]
        via = (r4(px + dx), r4(py + dy))
        why = (f'W2 PWR-L6-PLACE fourth pass, probe A: escape fan of J209 contact {n} ({net}, lower row) to its via in the '
               f'escape band (FAN_OFFSETS)')
        out_t.append({'id': f'ESC-J209-{n}', 'net': net, 'layer': 'B.Cu', 'width_mm': W_FAN,
                      'path': [[r4(px), r4(py)], [r4(px), r4(py + knee)], list(via)], 'locked': True, 'why': why})
        out_v.append({'id': f'ESC-J209-{n}-V', 'net': net, 'at': list(via), 'drill_mm': VIA_DRILL, 'diameter_mm': VIA_D,
                      'locked': True, 'why': why})
    return out_t, out_v


def planned_copper(parts, pins):
    """Stage 2 of W2 PWR-L6-PLACE third pass: the locked copper of route-planned-6l.json (PLANNED), one tree per net that joins
    every pad of the net on this board (checked by connected() through pins['scripted_nets'])."""
    if not PLANNED:
        return [], []
    src = PLANNED['source']
    out_t, out_v = [], []
    for net, d in sorted(PLANNED['nets'].items()):
        how = src.get('why_short') or (f'W2 PWR-L6-PLACE third pass, stage 2): freeze6 grid A* on route run {src["route_run"]} '
                                       'with all router copper removed, at the scripted-copper margins')
        why = f'planned {d["kind"]} copper of {net} ({how}; {PLANNED6.name}'
        for k, (layer, w, a, b) in enumerate(d['tracks'], 1):
            out_t.append({'id': f'PL-{net}-{k:03d}', 'net': net, 'layer': layer, 'width_mm': w,
                          'path': [[r4(a[0]), r4(a[1])], [r4(b[0]), r4(b[1])]], 'locked': True, 'why': why})
        for k, (x, y, size, drill) in enumerate(d['vias'], 1):
            out_v.append({'id': f'PLV-{net}-{k:02d}', 'net': net, 'at': [r4(x), r4(y)], 'drill_mm': drill,
                          'diameter_mm': size, 'locked': True, 'why': why})
        if d['kind'] in PLANNED_WHOLE:  # a 'link' (W2 PWR-L6-PLACE fourth pass) is locked copper of a net that stays routed
            pins['scripted_nets'][net] = sorted({(r, p['number']) for r, pa in parts.items() for p in pa.pads
                                                 if p['net'] == net and p['number'] and p['type'] != 'np_thru_hole'})
    return out_t, out_v


# ------------------------------------------------------------------ 3V3_Q6A plane (6 layers, W2 PWRB-R)
Q6A_NET, Q6A_PLANE = '3V3_Q6A', 'In4.Cu'
Q6A_VY = (22.0, 22.2, 21.9, 22.4)   # via rows above the upper J209 row (pad tops 21.1), below the J207 pins (23.4)


def q6a_plane_copper(inp, parts, tracks, vias, pins):
    """In4.Cu is a solid 3V3_Q6A plane (S-G-S-S-P-S as the 6-layer CTRL of W2 CTRL-R): the J209 3V3_Q6A contact leaves
    its row on B.Cu (upper row: upwards, between its GND neighbours) to a via above the row, and every SMD 3V3_Q6A pad gets
    its own fan-out via (gnd_fanout with net 3V3_Q6A); the THT pins J201.1 and J204.2 join the plane directly. The net is
    then not autorouted (class SCRIPTED_GND, as CTRL)."""
    out_t, out_v = [], []
    j = parts[B2B_REF]
    for n in sorted((n for n, net in pins['pins'].items() if net == Q6A_NET), key=int):
        pad = j.pad(n)
        px, py = pad['at']
        if not py > B2B_AT[1]:
            raise SystemExit(f'make_spec: J209 {Q6A_NET} contact {n} is not in the upper row (pin map changed)')
        spot = next((vy for vy in Q6A_VY if via_spot_ok(inp, parts, tracks + out_t, vias + out_v, (px, vy), Q6A_NET)), None)
        if spot is None:
            raise SystemExit(f'make_spec: no via spot above J209 contact {n} ({Q6A_NET})')
        out_t.append({'id': f'Q6A-J209-{n}-S', 'net': Q6A_NET, 'layer': 'B.Cu', 'width_mm': W_PADSTUB,
                      'path': [[r4(px), r4(py)], [r4(px), r4(spot)]], 'locked': True,
                      'why': f'J209 contact {n} ({Q6A_NET}) out of the upper row between its GND neighbours to its plane via'})
        out_v.append({'id': f'Q6A-J209-{n}-V', 'net': Q6A_NET, 'at': [r4(px), r4(spot)], 'drill_mm': VIA_DRILL,
                      'diameter_mm': VIA_D, 'locked': True, 'why': f'{Q6A_NET} plane via (In4.Cu) of J209 contact {n}'})
    ft, fv, _n = gnd_fanout(inp, parts, tracks + out_t, vias + out_v, net=Q6A_NET, prefix='Q6A')
    return out_t + ft, out_v + fv


# ------------------------------------------------------------------ GND fan-out (scripted: every SMD GND pad gets a via)
W_GND = 0.25
GND_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
GND_GAPS = (0.55, 0.9, 1.3, 1.8)
# W2 PWR-L6-PLACE fifth pass, combined (lever 2 of the PWR_B closure): plane fan-outs pinned at their places on the board of
# record (route run 43553756303). They are tried before the candidate list, so the PWR-A test-point windows that left the
# bar-to-arm junction (PWR_A make_spec CUTOUT_KEEP) do not draw these two vias into the freed area, under the frozen copper
# (frozen guard scripted_sha256). A pin is taken only when it clears everything, like any other candidate.
FANOUT_PINS = {('GND', 'R287', '2'): ([(45.821, 26.692), (46.5458, 25.9672)], (46.5458, 25.9672)),
               ('3V3_Q6A', 'U217', '6'): ([(43.55, 21.1375), (42.85, 21.1375), (42.85, 20.5375)], (42.85, 20.5375))}


def gnd_fanout(inp, parts, tracks, vias, net='GND', prefix='GND'):
    """A locked via next to every SMD pad of a plane net (stub W_GND from the pad centre), so that the plane joins all
    its pads and the router never routes the net (route run 42415437982: Freerouting left 83 GND connections open and did
    not join the pads to the planes). GND: the In1.Cu plane (6 layers, W2 PWRB-R); 3V3_Q6A: the In4.Cu plane (W2 PWRB-R,
    as the 6-layer CTRL of W2 CTRL-R). Through-hole pins join the planes directly. The INA3221 exposed pad joins its
    GND pin 3 by a short track. Candidates are tried in a fixed order; the first that clears every other net, the
    edges, the hole keepouts and the via hole spacing is taken."""
    c = inp.contract
    outline = [tuple(p) for p in c['outline_mm']]
    cuts = all_cuts(inp)
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
        if any(edge_dist(q, outline, cuts) - W_GND / 2 < EDGE + MARGIN for q in path[1:]):
            return False  # stub corners and ends keep the edge clearance (PWR-A cut-outs included, W2 PCB-PWRB-2)
        # whole stub segments too (W2 PWRB-R: a diagonal 3V3_Q6A stub passed 0.1 mm from a cut-out corner)
        if any(seg_box_dist(a, q, cut) - W_GND / 2 < EDGE + MARGIN for a, q in stubs for cut in cuts
               if cut[0] - 4 < vx < cut[2] + 4 and cut[1] - 4 < vy < cut[3] + 4):
            return False
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
            if p['net'] == net and not p['npth']:
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
            if s['net'] == net:
                continue
            if new_via and seg_seg_dist(s['a'], s['b'], via_at, via_at) - s['r'] - r < need:
                return False
            if s['layer'] == layer and any(seg_seg_dist(s['a'], s['b'], a, q) - s['r'] - W_GND / 2 < need for a, q in stubs):
                return False
        return True
    spine_vias = [tuple(v['at']) for v in vias if v['id'].startswith(f'GND-{B2B_REF}-V')] if net == 'GND' else []
    done = 0
    for ref in sorted(parts, key=bg.sort_ref):
        if ref == B2B_REF:
            continue  # the J209 GND contacts join the GND spine (scripted_copper), not a via each
        pa = parts[ref]
        for p in sorted(pa.pads, key=lambda q: (bg.sort_ref(q['number']) if q['number'] else ('', -1, ''))):
            if p['net'] != net or p['type'] != 'smd' or not p['number']:
                continue
            if net == 'GND' and ref == 'U215' and p['number'] == 'EP':
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
            pin = FANOUT_PINS.get((net, ref, p['number']))
            if pin:
                cands.insert(0, (pin[0], pin[1], True))
            chosen = None
            for path, at, new_via in cands:
                if clear(path, at, layer, new_via):
                    chosen = (path, at, new_via)
                    break
            if chosen is None:
                raise SystemExit(f'make_spec: no {net} fan-out via position for {ref}.{p["number"]} at {p["at"]}')
            path, at, new_via = chosen
            vid = f'{prefix}-{ref}-{p["number"]}'
            out_t.append({'id': vid + '-S', 'net': net, 'layer': f'{layer}.Cu', 'width_mm': W_GND,
                          'path': [[r4(x), r4(y)] for x, y in path], 'locked': True,
                          'why': f'{net} fan-out of {ref}.{p["number"]} to its plane via' if new_via else
                                 f'GND fan-out of {ref}.{p["number"]} to the J209 GND spine via at {list(at)}'})
            if new_via:
                out_v.append({'id': vid + '-V', 'net': net, 'at': [at[0], at[1]], 'drill_mm': VIA_DRILL,
                              'diameter_mm': VIA_D, 'locked': True, 'why': f'{net} plane via of {ref}.{p["number"]}'})
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


def via_in_pad_record(parts, vias):
    """W2 PWR-L6-PLACE third pass: the U215 I2C2 via in pad (VIA_IN_PAD) with its measured gap to the neighbour pads (MODEL
    rectangle geometry of the pads, the via as a disc), the recorded clearance exception and the open fab / assembly gates."""
    rows = []
    for v in vias:
        if v['id'] not in VIA_IN_PAD:
            continue
        ref, pin, net, _at = VIA_IN_PAD[v['id']]
        gaps = [box_dist((v['at'][0], v['at'][1], v['at'][0], v['at'][1]), p['box']) - v['diameter_mm'] / 2
                for p in parts[ref].pads if p['number'] and p['number'] != pin and p['type'] == 'smd']
        rows.append({'id': v['id'], 'pad': f'{ref}.{pin}', 'net': net, 'at': v['at'], 'diameter_mm': v['diameter_mm'],
                     'drill_mm': v['drill_mm'], 'gap_to_neighbour_pads_mm': r4(min(gaps))})
    return {'vias': rows,
            'rule': ('W2 PWR-L6-PLACE third pass (judge decision ESC-JUDGE, the U215 lever of option R): INA3221 U215 pins 6 / 7 '
                     '(I2C2_SCL / I2C2_SDA) face the PWR-A TP104 probe window, so each pad carries a locked through via; the vias '
                     'are staggered along the 0.75 mm pads (0.851 mm centres, hole-to-hole 0.551 mm >= 0.5)'),
            'exception': (f'via copper {VIP_GAP} mm from the neighbour pads: the KiCad clearance 0.15 is met, the scripted-copper '
                          'design value CLEAR + MARGIN 0.20 is not (recorded exception, make_spec.py check_copper)'),
            'fab': ('filled and capped via in pad (POFV), the JLC default from 6 layers; the page gives "via diameters from 0.15 to '
                    '0.55 mm" without saying hole or finished diameter (https://jlcpcb.com/capabilities/pcb-capabilities, read '
                    '2026-11-13): TBD at order'),
            'gate': 'OPEN: assembly gate of the QFN with filled vias in two pads (voiding, coplanarity) at the first build'}


def spec_json(inp, anchors, pins, tracks, vias, exempt, pparts, frozen_note=None, escape=None):
    c = inp.contract
    overlay = cutout_overlay(inp, pparts)
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
        'note': ('W2 PCB-PWRB, W2 B2B, W2 PCB-PWRB-2. Generated by build/kicad/boards/PWR_B/make_spec.py (do not hand-edit; rerun '
                 'it). Placement and the scripted copper are design choices of these packages (build/15 rows W2 PCB-PWRB, W2 B2B '
                 'and W2 PCB-PWRB-2); the board is the full L of the W2 MECH-7 contract, the PWR-A cut-outs are kept free of parts '
                 'and scripted copper but not cut yet (pwr_a_cutouts: their Edge.Cuts wait for the contract); the J209 '
                 'pin map is the graph (pcb/generated/b2b-nets.json contacts). KiCad DRC, the audits and check_boards are '
                 'CI/model results. Not a fabrication release; mezzanine fit, heat and every bench gate stay OPEN.'),
        'contract': {'file': 'mechanical/generated/contract/boards.json', 'board': BOARD},
        'domains': list(c['domains']),
        'partition': 'pcb/generated/partition.json',
        'layers': {
            'copper': 6, 'thickness_mm': 1.6, 'copper_option': COPPER_OPTION,
            'source': ('W2 PWRB-R layers6 study and W2 PWRJ-LAYERS6: 6 layers JLC06161H-2116 1.6 mm, the stackup of the 6-layer CTRL '
                       '(W2 CTRL-R / CTRL-4; pcb/generated/stackup-6l.json from pcb/stackup.py, jlcpcb.com/impedance read 2026-11-12), '
                       'ordered with finished outer copper 2 oz and inner 0.5 oz (copper_option outer_2oz, jlcpcb.com read '
                       '2026-11-13): the power classes take their 2 oz outer widths (PWR1A 0.2 mm). 1.6 mm is the order thickness; the contract '
                       'gives PWR_B its own stackup (mechanical/generated/contract/boards.json PWR_B stackup: t 1.664 MODEL with '
                       '2 oz outer, 6 layers, order 1.6 +/- 10 %, W2 MECH-8), which the mechanics use'),
            'types': {'In1.Cu': 'power', 'In4.Cu': 'power'},
            'types_why': ('S-G-S-S-P-S as the 6-layer CTRL: In1.Cu (L2) a solid GND plane 0.2234 mm under F.Cu, so the LAB5 '
                          'trunk, the TPS2553 switches, the Kelvin shunts and the LNA bias filters (XAL5030 inductors, '
                          'dampers) on F.Cu keep a solid return plane directly below; In4.Cu (L5) a solid 3V3_Q6A plane '
                          '(the 20-pad monitor supply that crosses from the bar to the arm), both typed power so Freerouting '
                          'routes no trace on them. In2.Cu (L3) and In3.Cu (L4) are the routing layers the stackup adds; '
                          'every routing layer faces a plane (F.Cu-L2 0.2234 mm, L3-L2 0.3 mm, L4-L5 0.3 mm, B.Cu-L5 '
                          '0.2234 mm). The power classes route on F.Cu/B.Cu only (router.class_layers): inner copper is '
                          '0.5 oz (PWR1A would need 1.8 mm there, netclasses.json inner_min_width_mm); W2 PWR-L6-PLACE fourth '
                          'pass, combined: the PWR1A sub-class PWR05A (stackup-6l.json inner_classes, nets limited to <=0.339 A / '
                          '<=0.499 A) routes on all four routing layers, 0.5 mm on In2.Cu/In3.Cu'),
            'plan': {'F.Cu': 'L1: parts (top side only), LAB5 trunk and Kelvin copper, power and signal routes, GND pour',
                     'In1.Cu': 'L2: solid GND plane (pre-route zone, layer type power: the router puts only vias through it)',
                     'In2.Cu': 'L3: signal routes and the PWR05A power sub-class at 0.5 mm (no other power class), no pour (W2 PWRJ-LAYERS6; W2 PWR-L6-PLACE fourth pass, combined)',
                     'In3.Cu': 'L4: signal routes and the PWR05A power sub-class at 0.5 mm (no other power class), no pour (W2 PWRJ-LAYERS6; W2 PWR-L6-PLACE fourth pass, combined)',
                     'In4.Cu': 'L5: solid 3V3_Q6A plane (pre-route zone, layer type power); every SMD 3V3_Q6A pad has a scripted via',
                     'B.Cu': 'L6: B2B half J209 (bottom), its GND spine and contact escapes, LAB5 stubs, power and signal routes, GND pour'}},
        'project': 'build/kicad/boards/PWR_B/PWR_B.kicad_pro',
        'rules_file': None,
        'rules_note': ('Project rules live in the committed PWR_B.kicad_pro (generated by make_spec.py): the project defaults of '
                       'pcb/generated/netclasses.json project_defaults (track 0.15 / clearance 0.15, via 0.6 / 0.3, copper-edge '
                       '0.3, hole-hole 0.5) and its net classes SIG (Default), PWR1A, PWR2A, PWR3A with the outer minimum width as '
                       'track width (PWR05A of the copper option: its inner width, W2 PWR-L6-PLACE fourth pass, combined). pcb/rules/jlc-6l-1oz.kicad_dru is not copied: board_gen refuses rules_file until it copies '
                       'and hashes it; the multilayer JLC floors it carries equal the 4-layer ones (pcb/generated/stackup-6l.json).'),
        'fab_floor': {
            'source': f'{inp.netclasses["fab_floor"]["source"]} read {inp.netclasses["fab_floor"]["read"]}, multilayer 1 oz values '
                      '(pcb/generated/netclasses.json fab_floor.jlc_4l_1oz; unchanged for 6 layers on the 2026-11-12 re-read, '
                      'pcb/generated/stackup-6l.json capabilities)',
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
        'holes': {'from_contract': True, 'ref_prefix': 'H', 'keepout_layers': list(COPPER),
                  'keepout_blocks': ['tracks', 'vias', 'zone_fills']},
        'groups': [],
        'pre_route': {
            'tracks': tracks,
            'vias': vias,
            'zones': [{'id': 'GND-In1', 'net': 'GND', 'layer': 'In1.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
                       'why': 'GND plane L2 (layer type power, a plane in the DSN): the scripted vias of every SMD GND pad and the THT GND pins join it; '
                              'solid pad connection: a THT GND pin of J207 had one thermal spoke left on both planes (route run 42417213682). '
                              'Cost: the THT GND pins of J201-J207 and J506 join five GND layers without thermal relief, so their hole fill and solder joints are an assembly gate (OPEN, build/15 W2 PCB-PWRB)'},
                      {'id': 'Q6A-In4', 'net': Q6A_NET, 'layer': Q6A_PLANE, 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
                       'why': '3V3_Q6A plane L5 (layer type power, W2 PWRB-R as the 6-layer CTRL): every SMD 3V3_Q6A pad joins it through its '
                              'scripted via (the J209 contact through a B.Cu stub to a via above its row), the THT pins J201.1 and J204.2 directly'}]},
        'post_route_zones': [
            {'id': 'GND-F', 'net': 'GND', 'layer': 'F.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
             'why': 'solid pad connection: thermal spokes of THT header GND pins were starved between the pins (route run 42414083566); '
                    'the solder-joint cost of solid THT connections is an assembly gate (OPEN, see GND-In1)'},
            # W2 PWRJ-LAYERS6: no GND pours on the inner routing layers In2.Cu/In3.Cu any more: route run 43349395168 had two
            # connection_width errors on GND-L3 (necks between frozen tracks), the layers6 runs 43289131388 and 43307238078
            # on GND-F/GND-B; In1.Cu (GND) and In4.Cu (3V3_Q6A) stay solid planes next to both inner routing layers
            {'id': 'GND-B','net': 'GND', 'layer': 'B.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid'}],
        'edge_keepout': {'width_mm': 0.2, 'layers': list(ROUTING), 'blocks': ['tracks', 'vias'],
                         'why': 'rule-area strips (half-width 0.2) on every outline and cutout edge: the router keeps its copper '
                                '0.35 mm off the edge, above the project copper-to-edge 0.3 (route run 42414083566 had 0.23)'},
        'height_zones': [
            # W2 PWR-L6-PLACE third pass: no board-wide top zone any more: a top part outside every zone takes the contract
            # default max_component_height (hB 5.5, pcb/check_boards.py check_heights); the zone-2 exit pair takes the contract
            # clearance-map zone below (fits_mm)
            {'region': list(z['rect']), 'max_height_mm': z['fits_mm'], 'side': 'top', 'checked': True,
             'why': (f'contract height zone (mechanical/generated/contract/boards.json PWR_B height_zones, W2 PWR-L6-PLACE third '
                     f'pass): edge zone 2 of the vertical top-entry exit pair J203 / J506, free {z["free_mm"]} mm to the '
                     f'{z["limit"]}, fits {z["fits_mm"]} (MODEL clearance map); every other top part keeps the contract default '
                     f'hB {c["max_component_height"]}')}
            for z in c.get('height_zones', [])] + [
            {'region': 'board', 'max_height_mm': stack, 'side': 'bottom', 'checked': True,
             'why': 'bottom side: only the B2B half J209 in the PWR-A to PWR-B gap (stack 5.0; mechanical/params/boards.json '
                    'PWR_B b2b.bottom_side)'}] + [
            {'region': [cu['rect'][0], cu['rect'][1], r4(cu['rect'][2] - cu['rect'][0]), r4(cu['rect'][3] - cu['rect'][1])],
             'max_height_mm': 0.0, 'side': 'top', 'checked': True,
             'why': f'PWR-A cut-out {cu["ref"]} ({cu["kind"]}, {PWRA_STUDY.relative_to(BASE).as_posix()} pwr_b_cutouts): no PWR-B '
                    'part over it (W2 PCB-PWRB-2), so pcb/check_boards.py reports any courtyard that reaches it'}
            for cu in inp.cutouts],
        'sides': ['top', 'bottom'],
        'max_height_bottom': stack,
        'heights': dict(sorted(heights.items(), key=lambda kv: bg.sort_ref(kv[0]))),
        'heights_source': dict(sorted(sources.items(), key=lambda kv: bg.sort_ref(kv[0]))),
        'branch_exempt': exempt,
        'b2b_pin_map': {
            'connector': f'{B2B_REF} (Samtec LSHM-150-02.5-L-DV-A-N-K-TR, graph ref of design/E2.json, bottom side)',
            'mate': {'board': B2B_MATE_BOARD, 'ref': B2B_MATE_REF,
                     'pin_map': inp.b2b['mating_map']['formula'],
                     'rule': ('PWR_A has no board of record yet (W2 PCB-PWRA-3 placed it in a study: '
                              f'{PWRA_STUDY.relative_to(BASE).as_posix()}, {B2B_MATE_REF} at {list(B2B_AT)} rotation 0 on the top, '
                              f'its b2b check against {B2B_REF} 0 net differences); {B2B_REF} = {B2B_MATE_REF} mirrored about '
                              f'the strip axis, so {B2B_REF} pad m lies over {B2B_MATE_REF} pad m+1 for m odd and m-1 for m even, '
                              'and its alignment-post holes are mirrored too, they do not coincide: J208 has them at (+/-13.5, '
                              '+0.85) and J209 at (+/-13.5, -0.85) off the strip centre (b2b-nets.json mating_map.placement); '
                              'the check_boards b2b pair joins both specs once PWR_A has a board '
                              'of record (W2 PCB-PWRA-4); a geometric pad-over-pad check is not in check_boards yet (OPEN, '
                              'build/15 W2 B2B)')},
            'source': f'pcb/generated/b2b-nets.json sha256 {b2b_sha}',
            'rule': (f'{B2B_REF} pad nets are its graph pins, which equal b2b-nets.json contacts[].pwr_b_pin (make_spec.py '
                     'b2b_pin_map stops on any difference); the map itself is pcb/prepare.py b2b_contacts (pin_map_rule, '
                     'guard_rule in b2b-nets.json)'),
            'contacts': int(inp.b2b['contacts_available']), 'used': pins['used'], 'spare': pins['spare'],
            'needed_with_spare': inp.b2b['totals']['contacts_with_spare']},
        'placement_rules': {
            'edges': 'W2 PCB-PWRB-2 (SHRINK-2 without the S02 FFC and without the J204 + J207 PHD merge): J204 and J207 on the '
                     'top span x 58-107 of contract edge zone 1 (mechanical/generated/contract/boards.json PWR_B), mating faces '
                     f'{r4(c["outline_mm"][2][1] - (anchors["J204"]["at"][1] + 6.25))} mm inboard of the edge (R-PWRB-EXIT '
                     'set_back_min_mm of zone 1) and no part in front of them (plug zones). W2 PWR-L6-PLACE third pass: zone 2 '
                     '(bottom span x 90-115, exit top), free of PWR-A windows since W2 GR-ZONE2-SMD, holds the vertical top-entry '
                     'exit pair J203 (JST PHD B20B-PHDSS, harness branch S02B) and J506 (JST PH B9B-PH-K-S, S23 + S34) under the '
                     'J209 escape band (j209_escape); the S02 headers J202 and J201 stay parked inside the board without a harness '
                     'exit: zone 0 (right edge) is covered by the PWR-A strips of J104, J113-J115 and J507 and two hole keep-outs '
                     '(OPEN for MECH and PCB-PWRA-4, build/15 W2 PCB-PWRB-2); check_boards does not check edge zones',
            'cutouts': 'no top courtyard over a PWR-A cut-out (pwr_a_cutouts); pads, scripted copper and scripted vias keep the '
                       'edge clearance 0.35 mm from them as from a board edge; until they are Edge.Cuts every cut-out is a rule '
                       'area on all six copper layers (planned_cutouts: the rect grown by margin_mm 0.33, no tracks, vias, pads '
                       'or zone fills), so the router and the pours leave them free, and the board_gen report '
                       '(planned_cutout_audit) and pcb/check_boards.py (planned_cutouts) fail on any copper within 0.33 mm of '
                       'one (W2 PWRB-R, one key since W2 PWR-TOOLS)',
            'kelvin': 'INA3221 U215 near the ch1 shunt (the ch2 and ch3 sense lines are longer, MODEL; a deviation from the '
                      'W2 PCB-PWRB-2 brief, which asked for U215 at its shunts, accepted in build/15 W2 PCB-PWRB-2); every shunt '
                      'net is scripted copper (current path plus sense '
                      'take-off from the shunt pads) up to the 10 ohm INA3221 filter resistors next to each shunt; the filtered '
                      'input nets E2_U215_IP1-3 / IM1-3 from those resistors to U215 are autorouted as separate nets, not as pairs '
                      '(routed lengths of the board of record in build/kicad/boards/PWR_B/README.md and build/15 W2 PCB-PWRB-2), '
                      'so INA3221 accuracy stays a bench gate; ch4 senses through the B2B to U216 on PWR-A'},
        'pwr_a_cutouts': {
            'source': f'{PWRA_STUDY.relative_to(BASE).as_posix()} pwr_b_cutouts (sha256 of the list: {inp.cutouts_sha}; '
                      'make_spec.py cutouts_digest)',
            'rule': 'window (courtyard + 0.5) over every PWR-A part taller than hA, the edge strips of the PWR-A harness '
                    'headers and the test-point probe windows (pcb/partition-spec.json keepouts, height_rule)',
            'hand_back': 'not Edge.Cuts yet: the W2 MECH-7 contract is the full L (cutouts_mm []) and check_boards requires the '
                         'outline, the cut-outs and the area to equal the contract; the MECH lineage writes these rectangles '
                         'into mechanical/params/boards.json PWR_B (inner ones as cutouts, the edge ones as outline notches), '
                         'then this board is re-routed (OPEN, build/15 W2 PCB-PWRB-2)',
            'cutouts_mm': [{'ref': cu['ref'], 'kind': cu['kind'],
                            'rect': [cu['rect'][0], cu['rect'][1], r4(cu['rect'][2] - cu['rect'][0]), r4(cu['rect'][3] - cu['rect'][1])]}
                           for cu in inp.cutouts],
            'overlay': {**{k: v for k, v in overlay.items() if k != 'pairs'}, 'overlaps': overlay['pairs'],
                        'note': 'MODEL: exact rectangle intersection of the top courtyards with the cut-outs plus a raster of '
                                'their union; usable = L outline less the cut-out union and the hole keep-outs; fill_with_b2b '
                                'counts J209 on the top area as pcb/partition-budget.json does'}},
        'j209_escape': escape,
        'via_in_pad': via_in_pad_record(pparts, vias),
        'h_trim': {
            'rule': 'H-TRIM (pcb/partition-spec.json keepouts.h_trim, W2 AREA-2): after soldering, every THT pin of this board is '
                    'trimmed flush, protrusion at most 1.0 mm below the PWR-B bottom face; PWR-A parts up to 2.7 mm stand under '
                    'these pin fields (1.3 mm clearance in the 5.0 mm stack). Gate OPEN: measured at proof-fit',
            'pin_fields': [{'ref': ref, 'pins': n, 'field_mm': f}
                           for ref, n, f in sorted(tht_fields(pparts), key=lambda t: bg.sort_ref(t[0]))]},
        'planned_cutouts': {
            'why': ('W2 PWRB-R (review F2 of W2 PCB-PWRB-2), the only cut-out key since W2 PWR-TOOLS: the PWR-A cut-outs of '
                    'pwr_a_cutouts become holes or notches of PWR-B once the MECH lineage writes them into the contract, so no '
                    f'copper may cross them now: each rect grown by margin_mm {r4(KEEPOUT_GROW)} (copper-to-edge 0.3 + 0.03; '
                    'the scripted copper keeps 0.35) is a rule area on all six copper layers that blocks tracks, vias, pads and '
                    'zone fills, so Freerouting routes around it, the planes and pours leave it free and KiCad DRC reports any '
                    'copper in it; the board_gen report (planned_cutout_audit) and pcb/check_boards.py planned_cutouts measure '
                    'every copper item of the routed board against the rects'),
            'margin_mm': r4(KEEPOUT_GROW), 'layers': list(COPPER), 'blocks': ['tracks', 'vias', 'zone_fills', 'pads'],
            'rects': [{'id': cu['ref'], 'kind': cu['kind'],
                       'rect': [cu['rect'][0], cu['rect'][1], r4(cu['rect'][2] - cu['rect'][0]), r4(cu['rect'][3] - cu['rect'][1])]}
                      for cu in inp.cutouts]},
        'router': {'tool': 'freerouting', 'max_passes': 90, 'threads': 1, 'job_timeout': '00:33:00', 'timeout_s': 2100,
                   'fanout': False, 'ignore_net_classes': sorted(set(SCRIPTED_CLASSES.values())),
                   'class_layers': CLASS_LAYERS,
                   'why': 'the fan-out pre-pass escaped every SMD pin with necked-down (0.1124 mm) stubs and dangling vias, and '
                          'the router re-routed the scripted nets because locked copper that crosses a pad is no connection '
                          'for it (route run 42414083566): fan-out off, the scripted classes not autorouted; GND is joined by '
                          'the scripted plane vias of every SMD GND pad (run 42415437982 left 83 GND connections open)'},
        'drc_policy': {'warning_checks': WARNINGS},
    }
    if DIAG_POWER_INNER:  # W2 PWRB-R probe 2: a diagnostic, not a candidate board
        del spec['router']['class_layers']
        spec['router']['diagnostic'] = DIAG_POWER_INNER
    if frozen_note:  # W2 PWRB-R: the frozen 6-layer route is part of pre_route
        spec['pre_route']['frozen_route_note'] = frozen_note
    if FREEZE_ONLY and frozen_note:
        spec['router']['ignore_net_classes'] = sorted(set(SCRIPTED_CLASSES.values()) | {'kicad_default', 'PWR1A', *INNER_ROUTED})
        spec['router']['freeze_only'] = ('W2 PWRJ-LAYERS6 freeze-only: the frozen route in pre_route is the whole router copper, so '
                                         'pcb/board_gen.py does not start Freerouting (router_skip, W2 PWR-TOOLS) and the CI run '
                                         'measures exactly the frozen router copper plus the grid A* completion; in route run '
                                         '43349395168 Freerouting on top of the frozen copper joined no further connection (model '
                                         'open = KiCad open) and left KiCad clearance errors against the locked copper')
    return json.dumps(spec, ensure_ascii=False, indent=2) + '\n'


# ------------------------------------------------------------------ the project (rules and net classes)
def project_json(inp, pins):
    proj = read(ENC_PROJECT)
    proj['meta']['filename'] = 'PWR_B.kicad_pro'
    nc = inp.netclasses
    default = proj['net_settings']['classes'][0]
    pd = nc['project_defaults']['values_mm']
    classes = []
    for name, cls in (('Default', nc['classes']['SIG']), ('PWR1A', nc['classes']['PWR1A']), ('PWR05A', nc['classes']['PWR05A']),
                      ('PWR2A', nc['classes']['PWR2A']),
                      ('PWR3A', nc['classes']['PWR3A']), ('SCRIPTED_GND', nc['classes']['SIG']),
                      ('SCRIPTED_PWR1A', nc['classes']['PWR1A']), ('SCRIPTED_PWR3A', nc['classes']['PWR3A'])) + \
            ((('SCRIPTED_SIG', nc['classes']['SIG']),) if 'SCRIPTED_SIG' in SCRIPTED_CLASSES.values() else ()):
        row = copy.deepcopy(default)
        row['name'] = name
        # W2 PWR-L6-PLACE fourth pass, combined: a class that may route on In2/In3 (PWR05A) has the router width of its inner
        # copper, the one width that holds on every layer it uses (a Freerouting class has one width; freeze6 lays the 2 oz
        # outer width on F.Cu/B.Cu)
        row['track_width'] = cls['inner_min_width_mm'] if name in INNER_ROUTED else cls['outer_min_width_mm']
        row['clearance'] = cls['clearance_mm']
        row['via_diameter'] = VIA_D
        row['via_drill'] = pd['via_hole']
        if name != 'Default':
            row['priority'] = len(classes) - 1
        classes.append(row)
    proj['net_settings']['classes'] = classes
    nets = set(template_nets(inp, pins))
    # the class of netclasses.json with the copper option (PWR05A members), unless BOARD_CLASSES keeps a damper link on PWR1A
    patterns = [{**p, 'netclass': BOARD_CLASSES.get(p['pattern'], nc['nets'][p['pattern']]['class'])} for p in nc['kicad']['netclass_patterns']
                if p['pattern'] in nets and p['netclass'] in ('PWR1A', 'PWR2A', 'PWR3A') and p['pattern'] not in SCRIPTED_CLASSES]
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
DAMPER_LINKS = ('BIAS_CH1_DAMP', 'BIAS_CH2_DAMP', 'BIAS_CH3_DAMP', 'BIAS_CH4_DAMP', 'E2_SB_DAMP')
BOARD_CLASSES = {'LNA4V5': 'PWR1A',
                 # W2 PWRJ-LAYERS6 (PWRB-R layers6 finding): the LNA bias rails ch2/ch3 and their damper links are SIG by default
                 # (netclasses.json unclassified_supply_candidates) and drifted onto the 0.5 oz inner layers (damper copper 158 and
                 # 96 mOhm, MODEL); as BIAS_CH2_PORT / BIAS_CH3_PORT they take PWR1A, so they stay on the 2 oz outer copper.
                 # W2 PWR-L6-PLACE fourth pass, combined (lever 1): the rails take the class of BIAS_CH2_PORT / BIAS_CH3_PORT,
                 # PWR05A (U207 / U208 TPS2553 limit <=0.339 A): 0.2 mm on 2 oz outer copper or 0.5 mm on 0.5 oz inner copper.
                 # The damper links of every LNA / SB bias filter (0.15 ohm R + 47 uF) stay PWR1A, F.Cu/B.Cu only, although
                 # netclasses.json puts BIAS_CH1_DAMP, BIAS_CH4_DAMP and E2_SB_DAMP in PWR05A: the copper of a damper link
                 # adds to its 0.15 ohm (E2_SB_DAMP R295 -> C298: 74 mOhm on 2 oz outer in route run 43519497062, 138 mOhm
                 # with 49.8 mm on 0.5 oz In3 in run 43545826563, MODEL, 20 degC), so it stays on the 2 oz copper
                 **{n: 'PWR05A' for n in ('BIAS_CH2', 'BIAS_CH3')},
                 **{n: 'PWR1A' for n in DAMPER_LINKS}}
# Nets whose copper is all scripted and locked: widths of their netclasses.json class, not autorouted (router -inc).
SCRIPTED_CLASSES = {'GND': 'SCRIPTED_GND', 'LAB5': 'SCRIPTED_PWR3A',
                    **{f'E2_LNA{ch}_{k}': 'SCRIPTED_PWR1A' for ch in '1234' for k in ('SW', 'SHUNT')},
                    # 6 layers (W2 PWRB-R): 3V3_Q6A is the In4.Cu plane, every SMD pad on its own scripted via (as CTRL, W2 CTRL-R)
                    '3V3_Q6A': 'SCRIPTED_GND'}
# W2 PWR-L6-PLACE third pass, stage 2 (judge decision ESC-JUDGE: W's planned power copper re-planned on the M placement, and
# planned escapes for the innermost / interleaved J209 lower-row contacts): the nets that the fresh route of the zone-2 placement
# and its no-rip completion left open are planned on that route's board with all router copper removed (the freeze6 grid A* at
# the scripted-copper margins CLEAR + MARGIN 0.20 and EDGE + MARGIN 0.35; power class on F.Cu / B.Cu at its 2 oz width, signals
# on the four routing layers at 0.15 mm) and come in as locked copper of route-planned-6l.json; the router and freeze6 leave them
# alone (classes SCRIPTED_PWR1A / SCRIPTED_SIG), so the next fresh route works around them. MODEL plan, KiCad DRC is the check.
PLANNED6 = BASE / 'build/kicad/boards/PWR_B/route-planned-6l.json'
PLANNED = json.loads(PLANNED6.read_text(encoding='utf-8')) if PLANNED6.is_file() else None
# W2 PWR-L6-PLACE fourth pass (probe A): kind 'power' / 'signal' is the whole copper of its net (scripted class, joins every pad
# by itself); kind 'link' is locked copper that joins islands of a net whose other copper stays router / frozen copper (its
# class stays, connected() does not apply, freeze6 may complete it)
PLANNED_WHOLE = ('power', 'signal')
if PLANNED:
    SCRIPTED_CLASSES.update({net: ('SCRIPTED_PWR1A' if d['kind'] == 'power' else 'SCRIPTED_SIG')
                             for net, d in PLANNED['nets'].items() if d['kind'] in PLANNED_WHOLE})
# Routing layers of the 6-layer plan (W2 PWRB-R): In1.Cu (GND) and In4.Cu (3V3_Q6A) are planes of type power.
ROUTING = ['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu']
COPPER = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
# Power classes route on the outer copper only (pcb/board_gen.py router.class_layers, as CTRL): the 0.5 oz inner layers
# would need 1.8 mm for PWR1A (netclasses.json inner_min_width_mm) and do not count for PWR3A. W2 PWRJ-LAYERS6: the outer
# copper is 2 oz (COPPER_OPTION), so PWR1A routes at 0.2 mm there.
CLASS_LAYERS = {'PWR1A': ['F.Cu', 'B.Cu']}
# W2 PWR-L6-PLACE fourth pass, combined (lever 1 of the PWR_B closure): PWR05A, the PWR1A sub-class of the copper option
# (pcb/generated/stackup-6l.json inner_classes: the PWR1A nets limited to <=0.339 A / <=0.499 A), routes on all four routing
# layers: 0.2 mm on F.Cu/B.Cu (2 oz), 0.5 mm on In2.Cu/In3.Cu (IPC-2221 internal 0.453 mm on 0.5 oz, MODEL), so the outer
# copper stays for the high-current PWR1A nets (LNA4V5, VBUS_*, AUX12, E2_RTLB_SW, LAB5_RLY)
INNER_ROUTED = ('PWR05A',)
# W2 PWRB-R probe 2 (diagnostic only): without class_layers Freerouting may put PWR1A on In2.Cu/In3.Cu at the outer width
# 0.35 mm, which the 0.5 oz inner rule (1.8 mm) forbids; the run measures how much of probe 1's 59 open connections the
# outer-only power rule causes. Not a candidate board: pcb/check_boards.py class_widths flags every inner PWR1A piece.
# Route run 43301060296 (that diagnostic): DRC 0 errors, 45 unconnected (against 59), 140 class_widths findings (PWR1A
# at 0.35 mm on In2.Cu/In3.Cu); Freerouting stopped at its job timeout with 112 unrouted items. Off again (None) since.
DIAG_POWER_INNER = None
# PWR-A cut-out rule areas: the rect grown by the copper-to-edge clearance 0.3 plus 0.03; the scripted copper keeps 0.35
# (EDGE + MARGIN), so it never touches a rule area, and router copper and pours stay >= 0.33 from the future edge
KEEPOUT_GROW = EDGE + 0.03


# ------------------------------------------------------------------ frozen route (W2 PWRB-R, the CTRL-R / CTRL-4 toolkit)
FROZEN6 = BASE / 'build/kicad/boards/PWR_B/route-frozen-6l.json'
FREEZE_ONLY = True  # route run with the frozen copper: Freerouting routes no class (router.freeze_only)


def frozen_guard(parts, tracks, vias, cuts):
    """SHA256 of what the frozen copper depends on: every copper pad (ref, pad, net, centre, layers), the scripted copper
    (by geometry: id, net, layer, width, path, via position and size; the 'why' texts may change without a new harvest) and
    the PWR-A cut-outs (a PWR-A placement change moves the planned_cutouts rule areas, so the frozen copper must be harvested anew)."""
    pads = sorted(f'{ref}.{p["number"]}|{p["net"]}|{p["at"][0]:.4f},{p["at"][1]:.4f}|{",".join(p["layers"])}'
                  for ref, pa in parts.items() for p in pa.pads if p['number'] and p['type'] != 'np_thru_hole')

    def geometry(item):
        return json.dumps({k: v for k, v in item.items() if k != 'why'}, sort_keys=True)
    scripted = [geometry(t) for t in tracks] + [geometry(v) for v in vias]
    return {'pads_sha256': hashlib.sha256('\n'.join(pads).encode()).hexdigest(),
            'scripted_sha256': hashlib.sha256('\n'.join(scripted).encode()).hexdigest(),
            'cutouts_sha256': cutouts_digest(cuts)}


def frozen_guard_of_spec():
    """The guard of the current inputs (freeze/freeze6.py writes it into route-frozen-6l.json)."""
    inp = Inputs()
    _a, _m, _p, parts, tracks, vias, _e = build(inp)
    return frozen_guard(parts, tracks, vias, inp.cutouts)


def frozen_copper(inp, parts, tracks, vias):
    """The frozen 6-layer route (W2 PWRB-R): the router copper of one route run, harvested and locked, plus the grid A*
    completion of its open connections (freeze/freeze6.py), from route-frozen-6l.json when present. It goes in after the
    scripted copper, which it does not change; make_spec's own clearance checks cover the scripted copper only, the frozen
    copper is checked by freeze6.py (model) and by KiCad DRC in the CI route run. Returns (tracks, vias, note)."""
    if not FROZEN6.is_file():
        return [], [], None
    doc = json.loads(FROZEN6.read_text(encoding='utf-8'))
    if not doc.get('guard'):
        raise SystemExit(f'make_spec: {FROZEN6.name} has no guard (a freeze6.py --no-guard trial): harvest again with the guard')
    have = frozen_guard(parts, tracks, vias, inp.cutouts)
    for key, value in have.items():
        if doc['guard'][key] != value:
            raise SystemExit(f'make_spec: {FROZEN6.name} was routed on another {key} ({doc["guard"][key][:12]}... != '
                             f'{value[:12]}...): route again with [pcb-route PWR_B] without the frozen copper and harvest anew')
    why = (f'completion of the 6-layer frozen route ({FROZEN6.name}, W2 PWRB-R): grid A* on the locked copper of route run '
           f'{doc["source"]["route_run"]} (build/kicad/boards/PWR_B/freeze/freeze6.py), exact clearance check')
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
    note = (f'W2 PWRB-R: the router copper of route run {doc["source"]["route_run"]} is frozen and locked (RT-/RV- items) and its '
            f'open connections are joined by the grid A* completion (FIN-/FINV- items) of build/kicad/boards/PWR_B/freeze/freeze6.py '
            f'(numpy, offline; tools copied from the CTRL-4 freeze of origin/wip/w2-ctrl4-layers6). Source: '
            f'build/kicad/boards/PWR_B/{FROZEN6.name}; valid only for this placement, netlist and scripted copper (guard: SHA256 '
            f'of the pads and of the scripted copper). Freezer result: {json.dumps(doc.get("result", {}), sort_keys=True)}')
    return ft, fv, note


# ------------------------------------------------------------------ J209 escape corridor and the zone-2 radials (W2 PWR-L6-PLACE)
# The J209 lower contact row (pads to y 15.9) escapes downwards: B.Cu stubs to vias, then In2/In3/B.Cu west over the PWR-A
# J112/J108 strips. W2 PWRJ (LAYERS6 capacity, F2ENV probes 2-5, CI) measured that the PWR-A windows of the 12 V / HFP
# radials C265, C512 and C511 at y 3.7-11.5 wall that escape in (route run 43354942122: all 23 open connections start at
# J209 lower-row contacts; F2ENV probes 1-5 on the grown board: 52 -> 6 open, the radials moved off in probe 2 and the
# corridor kept in probe 3). J209_FIELD is the field the radials must leave (W2 PWR-L6 synthesis: PWR-B frame x 84-117,
# y 0-16); J209_CORRIDOR is the corridor of place_f2env.py CORRIDORS on the in-envelope outline (x 84-116, y 0-15.3), to
# be kept free of PWR-A windows and of new fixed vias. --corridor and --zone2-slots (about 8 min) are MODEL reports that
# write nothing; the slot search found no in-envelope place for the radial windows (build/15 W2 PWR-L6-PLACE), so W2
# GR-ZONE2-SMD made C265, C511 and C512 low SMD parts: they need no window any more.
# Since that swap the corridor is a placement check (corridor_check, W2 PWR-L6-PLACE second pass) and the spec records it
# (j209_escape): no PWR-A cut-out in J209_FIELD but the header edge strips of the MECH-7 bottom row and right column
# (CORRIDOR_STRIPS, which reach into its sides), and in J209_CORRIDOR no PWR-B top courtyard and no scripted via other than
# those of the placement of record (CORRIDOR_PARTS: the ch4 Kelvin cell of the J209 sense column, its bypasses, the
# BIAS_SB_LNA test point and the E2_RTLB_SW bypass C249, with their GND plane vias).
# W2 PWR-L6-PLACE third pass (judge decision ESC-JUDGE, option M): the field holds the vertical exit pair J203 / J506 (and
# C249 beside J506) in ZONE2_EXIT, the free part of the bottom edge (contract PWR_B edge_zones[2], x 90-115) under J203's
# courtyard top y 11.75; the J209 lower row escapes through the band J209_CORRIDOR, y 11.75-15.4 between the J203 courtyard
# and the J209 courtyard (y from 15.4), where the 12 J209-to-J203 S02 nets fan out and the other lower-row nets pass west.
CORRIDOR_STRIPS = ('J112', 'J113', 'J507')
CORRIDOR_PARTS = ('C244', 'C245', 'C297', 'L209', 'R243', 'TP216', 'U209')
EXIT_PARTS = ('C249', 'J203', 'J506')
J209_FIELD = (84.0, 0.0, 117.0, 16.0)
J209_CORRIDOR = (84.0, 11.75, 116.0, 15.4)
ZONE2_EXIT = (90.0, 0.0, 115.0, 11.75)
ZONE2_RADIALS = ('C265', 'C512', 'C511')
SLOT_STEP = 0.25        # mm, grid of the slot search (courtyard lower-left corner)
RELOCATE_MAX = 50.0     # mm, spiral radius of the relocation search for a displaced PWR-B part
RELOCATE_GAP = 0.1      # mm, courtyard gap of a relocated PWR-B part (the placement table packs at 0.2)
PWRA_EDGE_INSET = 0.3   # mm, a PWR-A courtyard keeps this off the outline (placement_study / place_board rule)


def _ov(a, b, gap=0.0):
    return min(a[2], b[2]) - max(a[0], b[0]) > -gap + 1e-9 and min(a[3], b[3]) - max(a[1], b[1]) > -gap + 1e-9


def _raster_area(boxes, clip, step=0.05):
    """Area (mm2) of the union of boxes inside clip, by rows of `step` (MODEL)."""
    x0, y0, x1, y1 = clip
    total, y = 0.0, y0 + step / 2
    while y < y1:
        iv = sorted((max(b[0], x0), min(b[2], x1)) for b in boxes if b[1] <= y < b[3] and b[2] > x0 and b[0] < x1)
        cur = None
        for a, b in iv:
            if cur and a <= cur[1]:
                cur[1] = max(cur[1], b)
            else:
                if cur:
                    total += cur[1] - cur[0]
                cur = [a, b]
        if cur:
            total += cur[1] - cur[0]
        y += step
    return total * step


def corridor_report(inp, parts, tracks, vias):
    """MODEL numbers of the J209 escape corridor: area, the PWR-A cut-outs in it (with and without the zone-2 radials),
    the PWR-B top courtyards in it and the scripted vias in it."""
    cor = J209_CORRIDOR
    cuts = [(c['ref'], c['rect']) for c in inp.cutouts if _ov(c['rect'], cor)]
    rad = [r for r, _ in cuts if r in ZONE2_RADIALS]
    crt = [(r, p.box) for r, p in sorted(parts.items()) if p.side == 'F' and _ov(p.box, cor)]
    fixed_vias = sorted({v['id'].rsplit('-', 1)[0] for v in vias if cor[0] <= v['at'][0] <= cor[2] and cor[1] <= v['at'][1] <= cor[3]})
    area = (cor[2] - cor[0]) * (cor[3] - cor[1])
    blocked = _raster_area([r for _, r in cuts], cor)
    blocked_wo = _raster_area([r for n, r in cuts if n not in ZONE2_RADIALS], cor)
    return {'corridor_mm': list(cor), 'field_mm': list(J209_FIELD), 'area_mm2': round(area, 1),
            'cutouts_in_corridor': [n for n, _ in cuts], 'zone2_radials_in_corridor': rad,
            'free_of_cutouts_mm2': round(area - blocked, 1),
            'free_of_cutouts_without_zone2_radials_mm2': round(area - blocked_wo, 1),
            'pwr_b_top_courtyards_in_corridor': [n for n, _ in crt],
            'pwr_b_top_courtyard_mm2': round(_raster_area([b for _, b in crt], cor), 1),
            'scripted_vias_in_corridor': len([v for v in vias if cor[0] <= v['at'][0] <= cor[2] and cor[1] <= v['at'][1] <= cor[3]]),
            'scripted_via_groups': fixed_vias}


def corridor_check(inp, parts, vias):
    """The J209 escape band and the zone-2 exit pair as a placement rule (W2 PWR-L6-PLACE second and third pass): returns
    (record, problems). MODEL geometry: areas by raster (_raster_area, 0.05 mm rows)."""
    field, cor, ex = J209_FIELD, J209_CORRIDOR, ZONE2_EXIT
    in_field = [c for c in inp.cutouts if _ov(c['rect'], field)]
    in_cor = [c for c in inp.cutouts if _ov(c['rect'], cor)]
    crt = sorted((r for r, p in parts.items() if p.side == 'F' and _ov(p.box, cor)), key=bg.sort_ref)
    in_ex = sorted((r for r, p in parts.items() if p.side == 'F' and _ov(p.box, ex)), key=bg.sort_ref)
    cvias = [v for v in vias if cor[0] <= v['at'][0] <= cor[2] and cor[1] <= v['at'][1] <= cor[3]]
    evias = [v for v in vias if ex[0] <= v['at'][0] <= ex[2] and ex[1] <= v['at'][1] <= ex[3]]
    problems = []
    for c in in_field:
        if c['ref'] in ZONE2_RADIALS or c['kind'] != 'header_edge_strip' or c['ref'] not in CORRIDOR_STRIPS:
            problems.append(f'J209 escape field: PWR-A cut-out {c["ref"]} ({c["kind"]}) {c["rect"]}')
    problems += [f'J209 escape band: PWR-B part {r} (not in CORRIDOR_PARTS)' for r in crt if r not in CORRIDOR_PARTS]
    owners = sorted({v['id'].split('-')[1] for v in cvias if v['id'].startswith(('GND-', 'Q6A-'))}, key=bg.sort_ref)
    # of record in the band: the plane vias of CORRIDOR_PARTS and the LAB5 contact vias of the J209 lower row (LAB5_VY)
    problems += [f'J209 escape band: scripted via {v["id"]} at {v["at"]}' for v in cvias
                 if not ((v['id'].startswith(('GND-', 'Q6A-')) and v['id'].split('-')[1] in CORRIDOR_PARTS)
                         or v['id'].startswith(('LAB5-V-', 'PLV-', 'ESC-J209-')))]
    # the exit pair: only its parts in ZONE2_EXIT, inside the contract edge zone 2 span and the zone-2 height zone
    problems += [f'zone-2 exit field: PWR-B part {r} (not in EXIT_PARTS)' for r in in_ex if r not in EXIT_PARTS]
    problems += [f'zone-2 exit field: scripted via {v["id"]} at {v["at"]}' for v in evias
                 if not ((v['id'].startswith(('GND-', 'Q6A-')) and v['id'].split('-')[1] in EXIT_PARTS)
                         or v['id'].startswith('ESC-J209-'))]
    ez = next((z for z in inp.contract.get('edge_zones', []) if set(z.get('headers', [])) >= {'J203', 'J506'}), None)
    pair = {}
    for r in ('J203', 'J506'):
        b = parts[r].box
        pair[r] = {'at': list(PLACEMENT[r][:2]), 'rotation': PLACEMENT[r][2], 'courtyard': [r4(v) for v in b],
                   'inside_exit_field': ex[0] <= b[0] and ex[1] <= b[1] and b[2] <= ex[2] and b[3] <= ex[3] + 1e-9}
        if not pair[r]['inside_exit_field']:
            problems.append(f'zone-2 exit field: {r} courtyard {b} leaves {list(ex)}')
        if ez is None or not (ez['span'][0] <= b[0] and b[2] <= ez['span'][1]) or ez.get('exit') != 'top':
            problems.append(f'zone-2 exit pair: {r} is not inside a top-exit contract edge zone that names it')
    band = r4(parts[B2B_REF].box[1] - parts['J203'].box[3])
    area = (field[2] - field[0]) * (field[3] - field[1])
    carea = (cor[2] - cor[0]) * (cor[3] - cor[1])
    record = {
        'rule': ('W2 PWR-L6-PLACE (W2 PWR-L6 synthesis, the place_f2env.py CORRIDORS idea of W2 PWRJ-F2ENV on the in-envelope '
                 'outline) and its third pass (judge decision ESC-JUDGE, option M): no PWR-A window over a part taller than hA '
                 'in J209_FIELD (C265, C511 and C512 are low SMD parts since W2 GR-ZONE2-SMD), only the header edge strips of '
                 'the MECH-7 bottom row and right column reach into it from its sides; the field holds the vertical top-entry '
                 'exit pair J203 / J506 and C249 in ZONE2_EXIT (contract edge zone 2, exit top) and nothing else; the J209 lower '
                 'row escapes through the band J209_CORRIDOR between the J203 courtyard and the J209 courtyard, where no PWR-B '
                 'top courtyard and no scripted via stand other than those of the placement of record (make_spec.py '
                 'corridor_check fails otherwise); W2 PWR-L6-PLACE fourth pass (probe A): the escape-fan vias ESC-J209- of the '
                 'contacts 25-31 (FAN_OFFSETS) belong to that record in the band and in the exit field'),
        'field_mm': list(field), 'field_area_mm2': round(area, 1),
        'field_free_of_cutouts_mm2': round(area - _raster_area([c['rect'] for c in in_field], field), 1),
        'cutouts_in_field': [{'ref': c['ref'], 'kind': c['kind'], 'rect': c['rect']} for c in in_field],
        'zone2_windows_in_field': sorted(c['ref'] for c in in_field if c['ref'] in ZONE2_RADIALS),
        'exit_field_mm': list(ex), 'exit_parts': list(EXIT_PARTS), 'exit_pair': pair,
        'exit_field_courtyards': in_ex, 'exit_field_scripted_vias': len(evias),
        'corridor_mm': list(cor), 'corridor_area_mm2': round(carea, 1), 'band_height_mm': band,
        'corridor_free_of_cutouts_mm2': round(carea - _raster_area([c['rect'] for c in in_cor], cor), 1),
        'corridor_free_of_cutouts_and_pwr_b_courtyards_mm2': round(
            carea - _raster_area([c['rect'] for c in in_cor] + [parts[r].box for r in crt], cor), 1),
        'pwr_b_top_courtyards_in_corridor': crt,
        'scripted_vias_in_corridor': len(cvias), 'scripted_via_owners': owners,
        'before': ('W2 PCB-PWRB-2 / PWRJ-LAYERS6 (until W2 GR-ZONE2-SMD): the windows of C265, C512 and C511 stood in the field '
                   '([89.6, 3.7, 97.4, 11.5], [99.1, 3.7, 106.9, 11.5], [106.4, 5.0, 112.9, 11.5]); the corridor had 248.1 mm2 '
                   'free of cut-outs (W2 PWR-L6-PLACE first pass, make_spec.py --corridor); second pass: the corridor was the '
                   'whole field (84, 0, 116, 15.3) with J203 and J506 parked in the arm (route run 43433071671: 0 / 23)'),
        'label': 'MODEL: rectangle geometry of the courtyards and cut-outs, raster 0.05 mm; not a routed result',
        'passed': not problems}
    return record, problems


def zone2_slots(inp, parts, tracks, vias):
    """MODEL slot search for the zone-2 radials (W2 PWR-L6-PLACE): every in-envelope place of a radial courtyard on the
    PWR-A top whose window (courtyard + window_margin) lies outside J209_FIELD, off the PWR-A hole keep-outs, the outline
    inset, the PWR-A anchors, the scripted F.Cu copper (reserved areas) and every other PWR-A part taller than hA or with a
    header strip, with PWR-A low parts allowed to give way (place_board.py re-places them). A PWR-A test point in the way
    is listed (its probe window would need a new PWR-B place, not searched here): 'strict' counts only slots that displace
    no test point, 'relaxed' also the others. On
    PWR-B the window must leave every top courtyard (CRT_GUARD) and scripted copper (KEEPOUT_GROW) free; a PWR-B part in
    the way counts only if it is not a header, J209 or scripted-copper part and a spiral search (RELOCATE_MAX) finds it a
    legal place off the cut-outs, the plug zones, J209_CORRIDOR and the hole keep-outs (pads), RELOCATE_GAP from the other
    courtyards. Returns the slot clusters per radial size and whether three disjoint slots exist (strict and relaxed)."""
    study = read(PWRA_STUDY)
    pspec = inp.pspec
    margin = float(pspec['parameters']['window_margin'])
    pwr_a = read(CONTRACT)['boards']['PWR']
    holes_a = [(tuple(h), pwr_a['hole_keepout_d'] / 2) for h in pwr_a['holes_mm']]
    outline = [tuple(p) for p in pwr_a['outline_mm']]
    xs, ys = sorted({p[0] for p in outline}), sorted({p[1] for p in outline})
    areas = [(xs[0] + PWRA_EDGE_INSET, ys[0] + PWRA_EDGE_INSET, xs[-1] - PWRA_EDGE_INSET, ys[1] - PWRA_EDGE_INSET),
             (xs[0] + PWRA_EDGE_INSET, ys[0] + PWRA_EDGE_INSET, xs[1] - PWRA_EDGE_INSET, ys[-1] - PWRA_EDGE_INSET)]
    cut_refs = {c['ref'] for c in study['pwr_b_cutouts']['placed'] if c['kind'] != 'test_point_probe_window'}
    probes = {c['ref'] for c in study['pwr_b_cutouts']['placed'] if c['kind'] == 'test_point_probe_window'}
    size = {c['ref']: round(c['rect'][2] - c['rect'][0] - 2 * margin, 4) for c in study['pwr_b_cutouts']['placed']
            if c['ref'] in ZONE2_RADIALS}
    fixed_a, low_a = [], []
    for r in study['positions']['refs']:
        if r['side'] != 'F' or r['ref'] in ZONE2_RADIALS:
            continue
        (fixed_a if (r['how'] == 'anchor' or r['ref'] in cut_refs) else low_a).append((r['ref'], r['courtyard_box']))
    fixed_a += [(rr['id'], rr['rect']) for rr in study['reserved']['rects'] if rr.get('side', 'F') == 'F']
    cuts = [c['rect'] for c in inp.cutouts if c['ref'] not in ZONE2_RADIALS]
    seg = []
    for t in tracks:
        w = t['width_mm'] / 2
        for (xa, ya), (xb, yb) in zip(t['path'], t['path'][1:]):
            seg.append((t['id'], t['net'], (min(xa, xb) - w, min(ya, yb) - w, max(xa, xb) + w, max(ya, yb) + w)))
    for v in vias:
        r = v['diameter_mm'] / 2
        seg.append((v['id'], v['net'], (v['at'][0] - r, v['at'][1] - r, v['at'][0] + r, v['at'][1] + r)))
    # PWR-B parts that cannot move: headers (THT pin fields: H-TRIM zones of PWR-A), J209 and every part whose pad carries
    # scripted copper other than its own GND / 3V3_Q6A plane via (Kelvin cells, LAB5 cells, J209 rail block)
    own = ('GND-', 'Q6A-')
    hard = {r for r, p in parts.items() if p.side == 'B' or any(q['type'] == 'thru_hole' for q in p.pads)}
    for sid, net, box in seg:
        if sid.startswith(own):
            continue
        for r, p in parts.items():
            if any(_ov(q['box'], box) for q in p.pads):
                hard.add(r)
    top = {r: p for r, p in parts.items() if p.side == 'F'}
    plugs = [(parts[n].box[0], parts[n].box[3], parts[n].box[2], max(y for _, y in outline)) for n in PLUG_ZONES]
    holes_b = [(tuple(h), inp.contract['hole_keepout_d'] / 2) for h in inp.contract['holes_mm']]

    def in_l(b, regions):
        return any(a[0] - 1e-9 <= b[0] and a[1] - 1e-9 <= b[1] and b[2] <= a[2] + 1e-9 and b[3] <= a[3] + 1e-9 for a in regions)

    def off_holes(b, holes):
        return all(math.hypot(max(b[0] - hx, 0, hx - b[2]), max(b[1] - hy, 0, hy - b[3])) >= r for (hx, hy), r in holes)

    b_areas = [(xs[0], ys[0], xs[-1], ys[1]), (xs[0], ys[0], xs[1], ys[-1])]

    def relocate(ref, wins, taken):
        p = top[ref]
        others = [q.box for r, q in top.items() if r != ref and r not in taken] + list(taken.values())
        steps = int(RELOCATE_MAX / SLOT_STEP)
        for k in range(steps + 1):
            rad = k * SLOT_STEP
            n = max(8, int(rad * 8))
            for i in range(n if rad else 1):
                a = 2 * math.pi * i / n
                dx, dy = round(rad * math.cos(a), 3), round(rad * math.sin(a), 3)
                b = (p.box[0] + dx, p.box[1] + dy, p.box[2] + dx, p.box[3] + dy)
                if not in_l(b, b_areas) or _ov(b, J209_CORRIDOR) or any(_ov(b, w, CRT_GUARD) for w in wins):
                    continue
                if any(_ov(b, z) for z in plugs) or any(_ov(b, o, RELOCATE_GAP) for o in others):
                    continue
                if not all(off_holes((q['box'][0] + dx, q['box'][1] + dy, q['box'][2] + dx, q['box'][3] + dy), holes_b)
                           for q in p.pads if q['type'] != 'np_thru_hole'):
                    continue
                if any(_ov(b, box, KEEPOUT_GROW) for sid, net, box in seg if not sid.startswith(own)):
                    continue
                return rad, b
        return None, None

    out = {}
    for cw in sorted(set(size.values()), reverse=True):
        found = []
        y = areas[0][1]
        while y + cw <= areas[1][3] + 1e-9:
            x = areas[0][0]
            while x + cw <= areas[0][2] + 1e-9:
                cy = (round(x, 3), round(y, 3), round(x + cw, 3), round(y + cw, 3))
                x += SLOT_STEP
                win = (cy[0] - margin, cy[1] - margin, cy[2] + margin, cy[3] + margin)
                if not in_l(cy, areas) or _ov(win, J209_FIELD) or not off_holes(cy, holes_a):
                    continue
                if any(_ov(cy, b, margin) for _, b in fixed_a):
                    continue
                conf = sorted(r for r, p in top.items() if _ov(win, p.box, CRT_GUARD))
                if any(r in hard for r in conf) or len(conf) > 4:
                    continue
                mine = tuple(f'{o}{r}-' for o in own for r in conf)  # the plane vias of a part that moves go with it
                if any(_ov(win, box, KEEPOUT_GROW) for sid, net, box in seg if not sid.startswith(mine or ('\0',))):
                    continue
                taken, moved = {}, {}
                for r in sorted(conf, key=lambda r: -(top[r].box[2] - top[r].box[0]) * (top[r].box[3] - top[r].box[1])):
                    d, b = relocate(r, cuts + [win], taken)
                    if d is None:
                        break
                    taken[r], moved[r] = b, round(d, 2)
                else:
                    disp = sorted(r for r, b in low_a if _ov(cy, b, margin))
                    found.append({'courtyard': list(cy), 'window': [round(v, 3) for v in win], 'pwr_b_moves_mm': moved,
                                  'pwr_a_low_parts_displaced': [r for r in disp if r not in probes],
                                  'pwr_a_test_points_displaced': [r for r in disp if r in probes]})
            y += SLOT_STEP
        def clusters(rows):
            got = []
            for s in sorted(rows, key=lambda s: (len(s['pwr_a_test_points_displaced']),
                                                 max(s['pwr_b_moves_mm'].values(), default=0.0),
                                                 len(s['pwr_a_low_parts_displaced']), s['courtyard'][1], s['courtyard'][0])):
                if not any(_ov(s['window'], c['window']) for c in got):
                    got.append(s)
            return got
        out[str(cw)] = {'radials': sorted(r for r, v in size.items() if v == cw), 'slot_positions': len(found),
                        'strict': clusters([s for s in found if not s['pwr_a_test_points_displaced']]),
                        'relaxed': clusters(found)}
    need = {str(cw): sum(1 for v in size.values() if v == cw) for cw in set(size.values())}

    def three(mode):
        # the large radials first, then the small ones in windows disjoint from those (greedy over the clusters)
        chosen = []
        for cw in sorted(need, key=float, reverse=True):
            for s in out[cw][mode]:
                if len([c for c in chosen if c[0] == cw]) < need[cw] and not any(_ov(s['window'], c[1]['window']) for c in chosen):
                    chosen.append((cw, s))
        return all(len([c for c in chosen if c[0] == cw]) >= need[cw] for cw in need)
    return {'rule': 'MODEL slot search of make_spec.py zone2_slots (W2 PWR-L6-PLACE); PWR-A study of '
                    f'{PWRA_STUDY.name}, PWR-B placement of this table', 'courtyard_mm': size, 'need': need,
            'sizes': out, 'three_disjoint_slots': {'strict': three('strict'), 'relaxed': three('relaxed')}}


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
    ap.add_argument('--corridor', action='store_true', help='MODEL report of the J209 escape corridor, write nothing')
    ap.add_argument('--zone2-slots', action='store_true', help='MODEL slot search for the zone-2 radials, write nothing')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    inp = Inputs()
    anchors, missing, pins, parts, tracks, vias, exempt = build(inp)
    if args.corridor or args.zone2_slots:
        rep = {'corridor': corridor_report(inp, parts, tracks, vias)}
        if args.zone2_slots:
            rep['zone2_slots'] = zone2_slots(inp, parts, tracks, vias)
        print(json.dumps(rep, ensure_ascii=False, indent=1))
        return 0
    escape, escape_problems = corridor_check(inp, parts, vias)
    problems = check_placement(inp, parts) + check_copper(inp, parts, tracks, vias) + kelvin_cells(anchors) + escape_problems
    problems += [f'not placed: {r}' for r in missing]
    gnd_pads = [(r, q['number']) for r, pa in parts.items() for q in pa.pads if q['net'] == 'GND' and q['type'] == 'smd'
                and (r, q['number']) != ('U215', 'EP') and r != B2B_REF]
    gnd_vias = {tuple(t['path'][0]) for t in tracks if t['net'] == 'GND' and t['id'].endswith('-S')}
    for r, n in gnd_pads:
        if tuple(r4(v) for v in parts[r].pad(n)['at']) not in gnd_vias:
            problems.append(f'GND pad {r}.{n} without a plane via')
    q6a_pads = [(r, q['number']) for r, pa in parts.items() for q in pa.pads if q['net'] == Q6A_NET and q['type'] == 'smd'
                and q['number']]
    q6a_vias = {tuple(t['path'][0]) for t in tracks if t['net'] == Q6A_NET and t['id'].endswith('-S')}
    for r, n in q6a_pads:  # 6 layers (W2 PWRB-R): every SMD 3V3_Q6A pad, the J209 contact included, has its In4.Cu plane via
        if tuple(r4(v) for v in parts[r].pad(n)['at']) not in q6a_vias:
            problems.append(f'{Q6A_NET} pad {r}.{n} without a plane via')
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
    ft, fv, frozen_note = frozen_copper(inp, parts, tracks, vias)
    if frozen_note:
        print(f'frozen route: {len(ft)} tracks, {len(fv)} vias')
    spec_text = spec_json(inp, anchors, pins, tracks + ft, vias + fv, exempt, parts, frozen_note, escape)
    project_text = project_json(inp, pins)
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
