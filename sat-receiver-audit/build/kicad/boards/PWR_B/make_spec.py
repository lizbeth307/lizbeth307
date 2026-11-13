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
  * the 4-layer plan (In1.Cu / In2.Cu GND planes of type power, signals on F.Cu / B.Cu), the project rules and net
    classes, and the router settings: Freerouting without its fan-out stage, the classes of the scripted nets
    (SCRIPTED_GND, SCRIPTED_PWR1A, SCRIPTED_PWR3A) not autorouted, rule-area strips on every board edge;
  * the PWR-A cut-outs as rule areas on all four copper layers (spec planned_cutouts, W2 PWRB-R: grown by the 0.3 mm
    copper-to-edge clearance, blocking tracks, vias, pads and zone fills; pcb/check_boards.py audits the copper);
  * optionally a frozen route (W2 PWRB-R, port of the W2 CTRL-R tool): build/kicad/boards/PWR_B/route-frozen.json, the
    harvested router copper of a route run plus its completion by freeze/freeze_route.py, added as locked copper only
    when its guard (pads and scripted copper) matches.
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
CRT_GUARD = 0.05      # courtyard boxes here are centre lines; KiCad's include half the 0.05 mm line (review F12 of W2 PCB-PWRB-2)
# W2 PWRB-R: In2.Cu as a third routing layer (the S-G-S-S plan of CTRL: In1.Cu solid GND, In2.Cu signals with a GND pour
# after routing). Route runs 43288408383 and 43290779665 (two routing layers, the PWR-A cut-outs as rule areas) left 98 and
# 89 connections open; the bar between J209 and the S02 headers has 13-17 mm per layer for 47 nets. Route run 43308775349
# with IN2_SIGNAL True left 73 open, and Freerouting put PWR1A copper on In2.Cu at 0.35 mm (88 check_boards findings: inner
# PWR1A needs 1.8 mm, pcb/generated/netclasses.json), because the DSN gives no per-class layer limit; freeze/freeze_route.py
# --in2-signal rips that copper and completes power nets on the outer layers only. False: the committed plan.
IN2_SIGNAL = False
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
def cutouts_digest(placed):
    """sha256 of the PWR-A cut-out list (ref, kind, rect) in canonical JSON."""
    rows = [{'ref': c['ref'], 'kind': c['kind'], 'rect': [float(v) for v in c['rect']]} for c in placed]
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


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
#  * The S02 headers J202 / J203 / J201 and the PH 9 J506 are parked: zone 0 (right edge) is covered by the PWR-A
#    J104 / J113-J115 / J507 strips and two hole keep-outs, and zone 2 (bottom span x 93-114.5) by the PWR-A windows of
#    C265, C512 and C511 (PCB-PWRA-3 placed them after MECH-7 set the span). J202 stands in the 10.6 mm column between
#    the PWR-A probe windows TP211 / TP215 and the C262 window, J203 above it, J201 and J506 in the arm; every one of
#    them has no harness exit (OPEN, build/15 W2 PCB-PWRB-2).
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
#  * W2 PWRB-R PLACE study (review F3-F5 of W2 PCB-PWRB-2; the PWR-A cut-outs are rule areas now, planned_cutouts):
#    - H-TRIM (F5): J203 turned by 180 in its own courtyard box, so its pin field lies at y 31-34 (off Q102); J201 turned
#      to 270 at x 1-9.6, y 35.4-48.3, its pin field in the column between C219 / L203 and L102 (x 6.9-8.6); U507 took the
#      J201 place below the ch1 cell, which moved up by 1.6 mm (the whole Kelvin cell, LNA_ROWS unchanged); J202 turned
#      to 270 in its box, so the pin fields of J202 and J203 face the bar and J209;
#    - dampers (F3): each 0.15 ohm series resistor next to its damper capacitor (R232 / C235, R237 / C239, R242 / C243
#      turned by 180), ch1 output capacitor C234 and TP206 at L206, ch2 output capacitor C238 on the BIAS_CH2 run between
#      L207 and the damper; C251 / R251 (VBUS_RTLB) and C298 / R295 (SB) stay where a 6 x 8 mm place exists (no place
#      within 25 mm of L210 or L215, OPEN);
#    - INA3221 (F4): U215 turned by 180 (ch1 inputs face the ch1 cell, ch2 inputs the bar), its filter capacitors C274,
#      C275, C276 at its input pins. Defect found by route run 43290779665: the ch2 inputs (pins 14, 15) then face the
#      PWR-A TP104 window 0.7 mm away and E2_U215_IP2 cannot leave pin 15; route run 43308775349 (U215 at 0 again, C275 at
#      (22.55, 61.925, 180), C276 at (22.825, 50.9, 270)) reached both ch2 inputs. That fix changes pads, so it waits for
#      the next route run (this table equals the spec of route run 43290779665, whose outputs are committed).
PLACEMENT = {
    'C232': (2.1, 60.8, 0), 'C233': (10.7, 56.1, 270), 'C234': (15.805, 53.55, 180), 'C235': (18, 49.5, 0),
    'C236': (44.15, 16.2, 0), 'C237': (52.75, 11.5, 270), 'C238': (40.776, 8.8, 0), 'C239': (30, 14, 90),
    'C240': (10.1, 83.7, 0), 'C241': (18.7, 79, 270), 'C242': (16.623, 94.606, 90), 'C243': (13.5, 89.5, 180),
    'C244': (95.211, 13.033, 0), 'C245': (103.6, 14.7, 270), 'C246': (98.85, 19.65, 270), 'C247': (110.98, 21.325, 180),
    'C248': (80.5, 16.9, 0), 'C249': (91.447, 2.319, 0), 'C250': (94.03, 19.65, 270), 'C251': (36, 12, 90),
    'C274': (19.675, 54.5, 270), 'C275': (22.55, 61.925, 180), 'C276': (22.825, 50.9, 270), 'C277': (36.97, 46.405, 90),
    'C282': (54.483, 20.169, 90), 'C283': (26.97, 29.32, 0), 'C284': (23.475, 29.022, 0), 'C285': (38.734, 47.163, 90),
    'C286': (42.496, 27.45, 90), 'C287': (36.764, 49.588, 90), 'C295': (72.5, 16.9, 0), 'C296': (61.947, 8.569, 0),
    'C297': (112.18, 15.097, 90), 'C298': (5.5, 22, 90), 'C501': (59, 23.5, 90), 'C502': (56.5, 25.2, 0),
    'C503': (38.5, 20.5, 0), 'C504': (67, 15.2, 90), 'C505': (64.5, 16.9, 0), 'C506': (37.5, 73, 0),
    'C507': (36.46, 76.867, 0), 'C521': (30.95, 105, 90), 'C522': (36, 90.5, 0), 'C550': (40.625, 47.101, 90),
    'C551': (38.651, 50.429, 90), 'C2901': (55.363, 33.73, 0), 'C2902': (40.167, 77.567, 0), 'C2911': (20.334, 42.046, 0),
    'C2912': (5.654, 98.616, 0), 'D2901': (25.835, 50.625, 0), 'D2902': (5.225, 95.981, 0), 'J201': (110.95, -12.15, 180),
    'J202': (73.15, -14.9, 180), 'J203': (97.05, -14.9, 180), 'J204': (104.55, 24.24, 180), 'J207': (85, 24.24, 180),
    'J209': (98.8, 18.5, 180, 'B'), 'J506': (133.05, -12.15, 180), 'L206': (15.1, 57.8, 0), 'L207': (57.15, 13.2, 0),
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
    'TP206': (12.755, 53.05, 0), 'TP207': (37.667, 31.094, 0), 'TP208': (13.323, 85.016, 0), 'TP209': (116.3, 22.8, 0),
    'TP210': (118.85, 22.8, 0), 'TP216': (92, 13, 0), 'TP2901': (58.876, 33.73, 0), 'TP2902': (40.679, 80.317, 0),
    'U206': (4.1, 57.6, 0), 'U207': (46.15, 13, 0), 'U208': (12.1, 80.5, 0), 'U209': (97, 16.2, 0), 'U210': (80.5, 20, 90),
    'U215': (21.5, 58.5, 0), 'U217': (44.5, 20, 90), 'U218': (9.5, 32.5, 90), 'U219': (23, 22, 90),
    'U221': (72.5, 20, 90), 'U501': (56.5, 28.3, 90), 'U502': (64.5, 20, 90), 'U507': (4.5, 51, 0),
}
PLUG_ZONES = ('J204', 'J207')   # top-span headers: no part between the mating face and the board edge
BAND_TOP = 35.0                 # the top span edge of the band (contract outline; W2 PWRJ F2ENV: the outline grows down)
# W2 PWRJ F2ENV probe: the S02 headers J201 / J202 / J203 and the PH 9 J506 stand in the slab under the band (board y < 0,
# inside the bay: no display over board y < 11.8), side entry turned by 180 so that the mating face looks up the board (+y);
# the plug and the wire bend need BAY_PLUG_MM of free board in front of the face, and the wires rise into the bay
BAY_PLUGS = ('J201', 'J202', 'J203', 'J506')
BAY_PLUG_MM = 4.0
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


F2ENV_PLACEMENT = BASE / 'build/kicad/boards/PWR_B/placement-f2env.json'   # W2 PWRJ F2ENV probe (place_f2env.py)


def placement(inp):
    """Anchor of every template ref (footprint origin); the F2-ENV probe re-placement (placement-f2env.json, written by
    place_f2env.py) overrides the table for the refs it moved."""
    anchors = {}
    table = dict(PLACEMENT)
    if F2ENV_PLACEMENT.is_file():
        table.update({ref: tuple(v) for ref, v in read(F2ENV_PLACEMENT)['positions'].items()})
    for ref, row in table.items():
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
            if a not in PLUG_ZONES and pa.side == 'F' and bg.rects_overlap(pa.box, (hb[0], hb[3], hb[2], BAND_TOP)):
                problems.append(f'{a}: courtyard in the plug zone in front of {name}')
        for name in BAY_PLUGS:
            hb = parts[name].box
            if a != name and pa.side == 'F' and bg.rects_overlap(pa.box, (hb[0], hb[3], hb[2], hb[3] + BAY_PLUG_MM)):
                problems.append(f'{a}: courtyard in the bay plug zone in front of {name}')
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
    cuts = all_cuts(inp)
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
                               f'within the PWR1A width 0.35 mm; the SOT-23-6 pin pitch 0.95 mm does not take 1.85 mm'}
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
    if Q6A_PLANE_IN2:
        qt, qv = q6a_plane_copper(inp, parts, tracks + gt, vias + gv, pins)
        return tracks + gt + qt, vias + gv + qv, exempt
    return tracks + gt, vias + gv, exempt


# ------------------------------------------------------------------ 3V3_Q6A plane on In2.Cu (W2 PWRJ F2ENV probe 4)
# F2ENV probe 3 (run 43349901150): 12 of the 35 open connections were 3V3_Q6A, the 3.3 V logic rail from J201 / J209 to
# sixteen pads over the whole board (U215, U217-U219, U507, the I2C pull-ups and their capacitors); the A* completion left
# 9. As on the 6-layer PWR_B (wip/w2-pwrbr-layers6: In4.Cu) and CTRL, the rail becomes a plane, here In2.Cu (In1.Cu stays
# the solid GND plane under F.Cu): every SMD 3V3_Q6A pad gets its own scripted plane via, the J209 contact leaves its row to
# a via above it, the THT pins join the plane directly, and the net is not autorouted (class SCRIPTED_GND).
Q6A_PLANE_IN2 = True
Q6A_NET = '3V3_Q6A'
Q6A_VY = (22.0, 22.2, 21.9, 22.4)   # via rows above the upper J209 row (pad tops 21.1), below the J207 pins (23.4)


def q6a_plane_copper(inp, parts, tracks, vias, pins):
    """Port of wip/w2-pwrbr-layers6 make_spec.py q6a_plane_copper, plane on In2.Cu."""
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
                      'diameter_mm': VIA_D, 'locked': True, 'why': f'{Q6A_NET} plane via (In2.Cu) of J209 contact {n}'})
    ft, fv, _n = gnd_fanout(inp, parts, tracks + out_t, vias + out_v, net=Q6A_NET, prefix='Q6A')
    return out_t + ft, out_v + fv


# ------------------------------------------------------------------ GND fan-out (scripted: every SMD GND pad gets a via)
W_GND = 0.25
GND_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
GND_GAPS = (0.55, 0.9, 1.3, 1.8)


def gnd_fanout(inp, parts, tracks, vias, net='GND', prefix='GND'):
    """W2 PWRJ F2ENV: net/prefix make it the fan-out of any plane net (3V3_Q6A on In2.Cu, Q6A_PLANE_IN2).
    A locked via next to every GND SMD pad (stub W_GND from the pad centre), so that the GND planes In1/In2 join all
    GND pads and the router never routes GND (route run 42415437982: Freerouting left 83 GND connections open and did
    not join the pads to the planes). Through-hole GND pins join the planes directly. The INA3221 exposed pad joins its
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
    spine_vias = [tuple(v['at']) for v in vias if v['id'].startswith(f'GND-{B2B_REF}-V')]
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
            for sv in sorted(spine_vias if net == 'GND' else [], key=lambda v: (math.hypot(v[0] - cx, v[1] - cy), v)):
                if math.hypot(sv[0] - cx, sv[1] - cy) < 4.0:
                    cands.append(([(cx, cy), (sv[0], cy), sv], sv, False))
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


def spec_json(inp, anchors, pins, tracks, vias, exempt, pparts):
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
            'copper': 4, 'thickness_mm': 1.6,
            'source': 'build/15 Шари (4-layer JLC04161H-7628, 1 oz outer) and mechanical/generated/contract/boards.json stackup',
            'types': {'In1.Cu': 'power'} if IN2_SIGNAL else {'In1.Cu': 'power', 'In2.Cu': 'power'},
            'plan': {'F.Cu': 'parts (top side only), LAB5 trunk and Kelvin copper, signals, GND pour',
                     'In1.Cu': 'solid GND plane (layer type power: the router puts only vias through it)',
                     'In2.Cu': ('signals (autorouted; W2 PWRB-R: the S-G-S-S plan of CTRL, a third routing layer for the '
                                'bar between J209 and the S02 headers), GND pour after routing') if IN2_SIGNAL else
                               'second GND plane (layer type power)' + (
                         '; locked slow-signal links of the frozen route completion (route-frozen.json, W2 PWRB-R) where '
                         'F.Cu and B.Cu had no path; the plane fill flows around them, In1.Cu stays solid'
                         if any(t['layer'] == 'In2.Cu' for t in tracks) else ''),
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
            **({'frozen_route_note': (
                'W2 PWRB-R: tracks RT-* / vias RV-* are the router copper of the harvested route run, locked; FIN-* / FINV-* '
                'are its completion by build/kicad/boards/PWR_B/freeze/freeze_route.py (grid A*, exact clearance check, the '
                'planned cut-outs as keepouts). Valid only for this placement, netlist and scripted copper (guard: SHA256 of '
                'the pads and of the scripted copper geometry); a change stops make_spec.py at the guard and needs a new '
                'harvest. Source: build/kicad/boards/PWR_B/route-frozen.json')} if FROZEN.is_file() else {}),
            'tracks': tracks,
            'vias': vias,
            'zones': [{'id': 'GND-In1', 'net': 'GND', 'layer': 'In1.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
                       'why': 'GND plane (layer type power, a plane in the DSN): the scripted vias of every SMD GND pad and the THT GND pins join it'}] + ([] if IN2_SIGNAL else [
                      {'id': 'Q6A-In2' if Q6A_PLANE_IN2 else 'GND-In2', 'net': Q6A_NET if Q6A_PLANE_IN2 else 'GND',
                       'layer': 'In2.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
                       'why': ('W2 PWRJ F2ENV probe 4: In2.Cu is the solid 3V3_Q6A plane (make_spec.py Q6A_PLANE_IN2), In1.Cu stays '
                               'the GND plane under F.Cu; ' if Q6A_PLANE_IN2 else '') + 'second GND plane (power layer); solid pad connection: a THT GND pin of J207 had one thermal spoke left on both planes (route run 42417213682). '
                              'Cost: the THT GND pins of J201-J207 and J506 join four GND layers without thermal relief, so their hole fill and solder joints are an assembly gate (OPEN, build/15 W2 PCB-PWRB)'}])},
        'post_route_zones': ([{'id': 'GND-In2', 'net': 'GND', 'layer': 'In2.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
                               'why': 'W2 PWRB-R: In2.Cu is a signal layer (IN2_SIGNAL); its GND pour after routing joins the scripted GND vias'}]
                             if IN2_SIGNAL else []) + [
            {'id': 'GND-F', 'net': 'GND', 'layer': 'F.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid',
             'why': 'solid pad connection: thermal spokes of THT header GND pins were starved between the pins (route run 42414083566); '
                    'the solder-joint cost of solid THT connections is an assembly gate (OPEN, see GND-In2)'},
            {'id': 'GND-B', 'net': 'GND', 'layer': 'B.Cu', 'outline': 'board', 'priority': 0, 'pad_connection': 'solid'}],
        'edge_keepout': {'width_mm': 0.2, 'layers': ['F.Cu', 'In2.Cu', 'B.Cu'] if IN2_SIGNAL else ['F.Cu', 'B.Cu'], 'blocks': ['tracks', 'vias'],
                         'why': 'rule-area strips (half-width 0.2) on every outline and cutout edge: the router keeps its copper '
                                '0.35 mm off the edge, above the project copper-to-edge 0.3 (route run 42414083566 had 0.23)'},
        'planned_cutouts': {
            'why': ('W2 PWRB-R (review F2 of W2 PCB-PWRB-2): the PWR-A cut-outs (pwr_a_cutouts) become holes and notches of this '
                    'board once the MECH lineage writes them into the contract, so no copper may cross them now: each rect grown '
                    f'by margin_mm (the project copper-to-edge clearance {EDGE}) is a rule area on all four copper layers that '
                    'blocks tracks, vias, pads and zone fills, so Freerouting routes around it, the GND planes and pours leave '
                    'it free and KiCad DRC reports any copper in it; pcb/check_boards.py planned_cutouts measures every copper '
                    'item of the routed board against the rects'),
            'margin_mm': EDGE, 'layers': ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'], 'blocks': ['tracks', 'vias', 'zone_fills', 'pads'],
            'rects': [{'id': cu['ref'], 'kind': cu['kind'],
                       'rect': [cu['rect'][0], cu['rect'][1], r4(cu['rect'][2] - cu['rect'][0]), r4(cu['rect'][3] - cu['rect'][1])]}
                      for cu in inp.cutouts]},
        'height_zones': [
            {'region': 'board', 'max_height_mm_from_contract': 'max_component_height', 'side': 'top', 'checked': True,
             'why': 'hB 5.5 (pcb/partition-spec.json parameters.hB): parts on the top side; heights from heights below'},
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
                     'set_back_min_mm of zone 1) and no part in front of them (plug zones). The S02 headers J202, J203 and J201 '
                     'and the PH 9 J506 are parked inside the board without a harness exit: zone 0 (right edge) is covered by the '
                     'PWR-A strips of J104, J113-J115 and J507 and two hole keep-outs, zone 2 (bottom span x 93-114.5) by the PWR-A '
                     'windows of C265, C512 and C511 of the PCB-PWRA-3 placement. OPEN for MECH and PCB-PWRA-4 (build/15 '
                     'W2 PCB-PWRB-2); check_boards does not check edge zones',
            'cutouts': 'no top courtyard over a PWR-A cut-out (pwr_a_cutouts); pads, scripted copper and scripted vias keep the '
                       'edge clearance 0.35 mm from them as from a board edge; the router does not know them until they are '
                       'Edge.Cuts, so the routed copper of record may cross them (re-route after the contract change, OPEN)',
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
        'h_trim': {
            'rule': 'H-TRIM (pcb/partition-spec.json keepouts.h_trim, W2 AREA-2): after soldering, every THT pin of this board is '
                    'trimmed flush, protrusion at most 1.0 mm below the PWR-B bottom face; PWR-A parts up to 2.7 mm stand under '
                    'these pin fields (1.3 mm clearance in the 5.0 mm stack). Gate OPEN: measured at proof-fit',
            'pin_fields': [{'ref': ref, 'pins': n, 'field_mm': f}
                           for ref, n, f in sorted(tht_fields(pparts), key=lambda t: bg.sort_ref(t[0]))]},
        'router': {'tool': 'freerouting', 'max_passes': 90, 'threads': 1, 'job_timeout': '00:33:00', 'timeout_s': 2100,
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
                    **{f'E2_LNA{ch}_{k}': 'SCRIPTED_PWR1A' for ch in '1234' for k in ('SW', 'SHUNT')},
                    # W2 PWRJ F2ENV probe 4: 3V3_Q6A is the In2.Cu plane, every SMD pad on its own scripted via
                    **({Q6A_NET: 'SCRIPTED_GND'} if Q6A_PLANE_IN2 else {})}


# ------------------------------------------------------------------ main
# ------------------------------------------------------------------ frozen route (W2 PWRB-R, port of the W2 CTRL-R tool)
FROZEN = BASE / 'build/kicad/boards/PWR_B/route-frozen.json'
FROZEN_PREFIXES = ('RT-', 'RV-', 'FIN-', 'FINV-')
FROZEN_WHY = ('completion of the frozen route (build/kicad/boards/PWR_B/route-frozen.json, W2 PWRB-R): grid A* on F.Cu and '
              'B.Cu on the locked copper of the harvested route run, exact clearance check (freeze/freeze_route.py)')


def frozen_guard(parts, tracks, vias, cutouts_sha):
    """SHA256 of what the frozen copper depends on: every copper pad (ref, pad, net, centre, layers), the scripted copper
    (geometry only: its 'why' texts can be corrected without a new harvest), as W2 CTRL-R did for CTRL, and the PWR-A
    cut-out list (its rule areas are keepouts of the frozen copper; PCB-PWRA-4 may still move them)."""
    pads = sorted(f"{ref}.{p['number']}|{p['net']}|{p['at'][0]:.4f},{p['at'][1]:.4f}|{','.join(p['layers'])}"
                  for ref, pa in parts.items() for p in pa.pads if p['number'])

    def geometry(item):
        return json.dumps({k: v for k, v in item.items() if k != 'why'}, sort_keys=True)
    scripted = [geometry(t) for t in tracks] + [geometry(v) for v in vias]
    return {'pads_sha256': hashlib.sha256('\n'.join(pads).encode()).hexdigest(),
            'scripted_sha256': hashlib.sha256('\n'.join(scripted).encode()).hexdigest(), 'cutouts_sha256': cutouts_sha}


def frozen_guard_of_spec():
    """The guard of the spec this file makes now without the frozen copper (freeze/freeze_route.py writes it)."""
    inp = Inputs()
    _a, _m, _p, parts, tracks, vias, _e = build(inp, frozen=False)
    return frozen_guard(parts, tracks, vias, inp.cutouts_sha)


def frozen_copper(inp, parts, tracks, vias):
    """The frozen route: the router copper of a harvested route run, locked, and the scripted completion of its open
    connections, from route-frozen.json. It goes in after the scripted copper, which stays exactly as in that run; the
    guard stops make_spec when a pad, a net, the scripted copper or the PWR-A cut-out list changed (route again without
    the frozen copper)."""
    if not FROZEN.is_file():
        return [], [], None
    doc = json.loads(FROZEN.read_text(encoding='utf-8'))
    have = frozen_guard(parts, tracks, vias, inp.cutouts_sha)
    for key, value in have.items():
        if doc['guard'].get(key) != value:
            raise SystemExit(f'make_spec: route-frozen.json was routed on another {key} ({str(doc["guard"].get(key))[:12]}... != '
                             f'{value[:12]}...): route again with [pcb-route PWR_B] without the frozen copper and harvest anew')
    ft, fv = [], []
    for prefix, key, why in (('RT', 'router_tracks', None), ('FIN', 'completion_tracks', FROZEN_WHY)):
        for k, (net, layer, width, path) in enumerate(doc[key]):
            t = {'id': f'{prefix}-{k + 1:04d}', 'net': net, 'layer': layer, 'width_mm': width, 'path': path, 'locked': True}
            if why:
                t['why'] = why
            ft.append(t)
    for prefix, key in (('RV', 'router_vias'), ('FINV', 'completion_vias')):
        for k, (net, x, y, d, drill) in enumerate(doc[key]):
            fv.append({'id': f'{prefix}-{k + 1:04d}', 'net': net, 'at': [x, y], 'drill_mm': drill, 'diameter_mm': d, 'locked': True})
    return ft, fv, doc


def build(inp, frozen=True):
    anchors = placement(inp)
    missing = [r for r in inp.refs if r not in anchors]
    pins = b2b_pin_map(inp)
    parts = placed_parts(inp, anchors)
    move_edge_references(inp, anchors, parts)
    tracks, vias, exempt = scripted_copper(inp, parts, pins)
    if frozen:
        ft, fv, _doc = frozen_copper(inp, parts, tracks, vias)
        tracks, vias = tracks + ft, vias + fv
    return anchors, missing, pins, parts, tracks, vias, exempt


def scripted_only(items):
    return [t for t in items if not t['id'].startswith(FROZEN_PREFIXES)]


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
    # the frozen route copper is checked by freeze/freeze_route.py (exact model) and KiCad DRC, not by the pairwise check here
    problems = check_placement(inp, parts) + check_copper(inp, parts, scripted_only(tracks), scripted_only(vias)) + kelvin_cells(anchors)
    problems += [f'not placed: {r}' for r in missing]
    gnd_pads = [(r, q['number']) for r, pa in parts.items() for q in pa.pads if q['net'] == 'GND' and q['type'] == 'smd'
                and (r, q['number']) != ('U215', 'EP') and r != B2B_REF]
    gnd_vias = {tuple(t['path'][0]) for t in tracks if t['net'] == 'GND' and t['id'].endswith('-S')}
    for r, n in gnd_pads:
        if tuple(r4(v) for v in parts[r].pad(n)['at']) not in gnd_vias:
            problems.append(f'GND pad {r}.{n} without a plane via')
    if Q6A_PLANE_IN2:
        q6a_pads = [(r, q['number']) for r, pa in parts.items() for q in pa.pads if q['net'] == Q6A_NET and q['type'] == 'smd'
                    and q['number']]
        q6a_vias = {tuple(t['path'][0]) for t in tracks if t['net'] == Q6A_NET and t['id'].endswith('-S')}
        for r, n in q6a_pads:  # every SMD 3V3_Q6A pad, the J209 contact included, has its In2.Cu plane via
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
    spec_text, project_text = spec_json(inp, anchors, pins, tracks, vias, exempt, parts), project_json(inp, pins)
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
