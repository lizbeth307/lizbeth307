#!/usr/bin/env python3
"""Independent board check: a pure-Python S-expression reader for KiCad 10 .kicad_pcb files (no pcbnew, stdlib only).

Run from any directory:
  python pcb/check_boards.py --all [--check]          every pcb/boards/*.json with a board_id
  python pcb/check_boards.py --board <B> [--check]    one board
Writes build/kicad/boards/<B>/review.json (--check compares instead and writes nothing). Exit 1 on findings or a stale review.

It checks what KiCad DRC does not prove by itself: the outline and the holes against the board contract
(mechanical/generated/contract/boards.json), every pad net against the graphs (design/E*.json), the copper width
of each net class (pcb/generated/netclasses.json, tracks exactly and pour necks by a raster bottleneck), RF50
CPWG geometry (width, gap, coplanar ground, solid L2 within 3h, fence pitch), no copper in hole keepouts except
the BOND-RF hole's own net, the count of GND-CHASSIS ties (and their copper path to the BOND-RF hole), optional RF
node checks (DC taps, tap capacitors, a domain keepout, SENSE length; rf_checks), B2B pin-for-pin nets between two
boards, THT pads over plate pockets and component heights against the height zones. Review hashes are projections (board refs,
pins, nets, footprints, contract, classes), not whole input files, so an unrelated parts.json or graph edit does
not stale a review (F10). Results are MODEL checks of the drawn copper; they prove no hardware gate.

Spec: pcb/boards/<B>.json is the board spec shared with pcb/board_gen.py (schema srrx-board-spec-v1, PCB-PIPE).
normalize_spec() reads these v1 keys: board_id, contract {file, board}, project (board file = same stem .kicad_pcb),
instances {template_nets, list [{id, refs {template_ref: graph_ref | null}, nets {template_net: graph_net}}]},
parts [{ref, source "graph" | "pilot_placeholder", pins, replaced_by}] (placeholders become board-only refs whose pads
are checked against `pins`), holes {ref_prefix} (mounting-hole footprints), height_zones [{region "board" | [x, y, w, h],
max_height_mm | max_height_mm_from_contract <contract key>, side}]. Every other v1 key (layers, router, drc_policy,
pre_route, ...) belongs to board_gen and is ignored here. A spec without "schema" uses the native form below; a spec with
another schema, or a v1 key in an unknown shape, stops with a SystemExit naming the key.
Checker keys (optional, in either form; contract frame mm, y up unless contract_transform says otherwise):
  board_file (default build/kicad/boards/<B>/<B>.kicad_pcb), contract_board (default contract.board, then board_id),
  refs | domains (graph refs on the board; domains use pcb/generated/components.csv board_candidate),
  board_only_refs {ref: reason}, instances [{id, ref_map {board_ref: graph_ref}, net_map {board_net: graph_net}}] (native),
  contract_transform {origin: [x, y] (KiCad position of contract (0, 0)), y: "up"|"down"} (default: y up, origin
  from the Edge.Cuts bounding box), bond_hole {at: [x, y], net}, gnd_chassis_ties (default: graph ties on the board),
  split_nets {net: ["F.Cu", "B.Cu"]} (verified: every declared layer must join the same vias/THT pads of the net),
  neck_exempt {ref: {escape_mm, reason}}, branch_exempt {ref: {max_mm, min_width_mm, reason}} (low-current track chains of a
  power net that end at that ref's pad: Kelvin sense, decoupling stubs; KiCad side: rule areas named PWR_BRANCH*),
  rf50_exempt {net: reason}, rf50_taper {ref: {max_len_mm, min_width_mm, reason}} (RF50 tapers into that ref's pad;
  KiCad side: rule areas named RF_TAPER*),
  b2b [{ref, mate_board, mate_ref, pin_map: "identity" | {pin: mate_pin}}],
  tht_pockets [[x, y, w, h], ...] + tht_pocket_margin_mm (contract frame), height_zones [{rect, max_height, side}],
  heights {ref: mm}, sides ["top"] (default top only), max_height_bottom,
  coupons [{rect: [x, y, w, h] (contract frame), rf50_nets [...], gnd_net, reason}] (test coupons drawn beside the board in
  the same file, e.g. the RF impedance coupons on their own outlines: Edge.Cuts loops inside a coupon rect are not board
  cutouts and stay out of the outline and area checks, here and in pcb/fab_export.py; rf50_nets are checked as RF50 lines against the coupon's own ground
  net gnd_net (default GND; a separate piece needs its own net, or KiCad reports the two GND islands unconnected); W2 PCB-RF-2),
  rf_checks {why, taps [{ref, pad, max_mm}] (pad edge to the RF50-width copper of its own RF50 net), tap_caps [{ref, to: [ref,
  pad], max_mm}] (a pad of ref on the net of the target pad, pad edge to pad edge), keepout {domains [...], margin_mm, refs [...]}
  (refs' courtyards outside the box of the domain parts' courtyards + margin; domains from pcb/generated/components.csv),
  sense {nets [...], prototype <routed prototype review json>} (track length on the board > 0 and <= the prototype's routing
  length of that net)} (W2 PCB-RF-2). With bond_hole, each GND-CHASSIS tie must also reach the plated bond hole land through
  copper of the bond net.
  planned_cutouts {margin_mm, rects [{id, rect [x, y, w, h]}]} (W2 PWRB-R; the same key makes pcb/board_gen.py rule areas, and
  W2 PWR-TOOLS made it the only cut-out key): areas that become cut-outs later; no copper of any kind on any layer inside a
  rect or within margin_mm of it.
  exemption_policy {why} (W2 PWR-L6-SCRIPT, opt-in): the class-width exemptions follow the power rating of the pad they serve
  (exemption_role, from the graph value, footprint and pin names). branch_exempt (optionally limited to `pads`) is kept only
  for test points, resistors of 100 ohm or more and sense or logic pins; a neck (neck_exempt) is kept only at a pad that is
  not a TVS, connector or harness land, shunt, fuse, power-switch node, eFuse IN/OUT or converter capacitor, at least as wide
  as that pad's narrow side and no longer than its long side (no pin stems). Anything else is a class_widths finding.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import csv
import hashlib
import heapq
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARDS_DIR = ROOT / 'pcb/boards'
OUT_DIR = ROOT / 'build/kicad/boards'
CONTRACT = ROOT / 'mechanical/generated/contract/boards.json'
NETCLASSES = ROOT / 'pcb/generated/netclasses.json'
STACKUP_6L = ROOT / 'pcb/generated/stackup-6l.json'  # W2 PWRJ-LAYERS6: copper_options of 6-layer boards
COMPONENTS = ROOT / 'pcb/generated/components.csv'
GRAPHS = [ROOT / f'design/E{i}.json' for i in range(1, 6)]
STATUS = 'MODEL_CHECK: drawn copper against contract, graphs and net classes (pure-Python reader); not a fabrication release; bench gates OPEN'
NECK_GRID = 0.05     # mm raster for pour necks; a measured neck passes within one cell of its limit
NECK_MAX_CELLS = 600_000  # larger pours use a coarser step (recorded per neck as grid_mm)
POS_TOL = 0.01       # mm outline vertex / hole position tolerance
HOLE_D_TOL = 0.01    # mm hole diameter tolerance
# mm: KiCad stores coordinates in 1 nm units and approximates knockout circles by polygons, so a correct fill edge can
# sit a few nm inside the keepout radius (ENC pilot: 2.9999987 mm against r 3.0). Project tolerance, far below any clearance.
KEEPOUT_TOL = 0.005
# Contract board keys this checker reads (the review hash covers these only, F10); MECH-3 keeps the names.
CONTRACT_KEYS = ('outline_mm', 'cutouts_mm', 'area_mm2', 'holes_mm', 'hole_d', 'hole_keepout_d', 'max_component_height')
SPEC_SCHEMA_V1 = 'srrx-board-spec-v1'  # pcb/board_gen.py SPEC_SCHEMA
CHAIN_TOL = 1e-3     # mm: track endpoints closer than this are one node


# ------------------------------------------------------------------ S-expressions
class Q(str):
    """A quoted atom (keeps the quoting for a faithful dump)."""
    __slots__ = ()


_TOKEN = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


def _unescape(s):
    return re.sub(r'\\(["\\])', r'\1', s)


def parse(text):
    """Parse one S-expression document into nested lists of str / Q atoms."""
    stack, top, pos = [[]], None, 0
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            if text[pos:].strip() == '':
                break
            raise ValueError(f'S-expression syntax error at offset {pos}')
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            if len(stack) < 2:
                raise ValueError(f'unbalanced ) at offset {pos}')
            node = stack.pop()
            stack[-1].append(node)
        elif m.group(3) is not None:
            stack[-1].append(Q(_unescape(m.group(3))))
        else:
            stack[-1].append(m.group(4))
    if len(stack) != 1 or len(stack[0]) != 1:
        raise ValueError('S-expression must hold exactly one balanced top node')
    top = stack[0][0]
    return top


def dump(node):
    """Single-line canonical form; parse(dump(x)) == x."""
    if isinstance(node, list):
        return '(' + ' '.join(dump(x) for x in node) + ')'
    if isinstance(node, Q):
        return '"' + node.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return str(node)


def kids(node, key):
    return [x for x in node[1:] if isinstance(x, list) and x and x[0] == key]


def kid(node, key):
    for x in node[1:]:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def num(node, key, idx=1, default=None):
    k = kid(node, key)
    if k is None or len(k) <= idx:
        return default
    return float(k[idx])


def atoms(node):
    return [x for x in node[1:] if not isinstance(x, list)]


# ------------------------------------------------------------------ geometry
def rot(x, y, deg):
    """KiCad orientation: +deg is counter-clockwise on screen (y down)."""
    if not deg:
        return x, y
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return x * c + y * s, -x * s + y * c


def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def poly_area(pts):
    return 0.5 * sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))


def arc_points(sx, sy, mx, my, ex, ey, max_seg=0.25):
    """Points of a three-point arc (start, mid, end)."""
    d = 2 * (sx * (my - ey) + mx * (ey - sy) + ex * (sy - my))
    if abs(d) < 1e-12:
        return [(sx, sy), (ex, ey)]
    ux = ((sx * sx + sy * sy) * (my - ey) + (mx * mx + my * my) * (ey - sy) + (ex * ex + ey * ey) * (sy - my)) / d
    uy = ((sx * sx + sy * sy) * (ex - mx) + (mx * mx + my * my) * (sx - ex) + (ex * ex + ey * ey) * (mx - sx)) / d
    r = math.hypot(sx - ux, sy - uy)
    a0, am, a1 = (math.atan2(p[1] - uy, p[0] - ux) for p in ((sx, sy), (mx, my), (ex, ey)))

    def norm(a):
        return a % (2 * math.pi)
    ccw = norm(am - a0) < norm(a1 - a0)
    span = norm(a1 - a0) if ccw else -norm(a0 - a1)
    steps = max(2, int(math.ceil(abs(span) * r / max_seg)))
    return [(ux + r * math.cos(a0 + span * i / steps), uy + r * math.sin(a0 + span * i / steps)) for i in range(steps + 1)]


class Poly:
    """Even-odd polygon (KiCad filled polygons are fractured: holes joined by zero-width slits)."""
    BAND = 0.5

    def __init__(self, pts):
        self.pts = [(float(x), float(y)) for x, y in pts]
        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))
        self.edges = [(self.pts[i - 1], self.pts[i]) for i in range(len(self.pts))]
        self.buckets = collections.defaultdict(list)
        for e in self.edges:
            lo, hi = sorted((e[0][1], e[1][1]))
            for b in range(int(math.floor(lo / self.BAND)), int(math.floor(hi / self.BAND)) + 1):
                self.buckets[b].append(e)

    def crossings(self, y, edges=None):
        xs = []
        for (x1, y1), (x2, y2) in (self.edges if edges is None else edges):
            if (y1 > y) != (y2 > y):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        return xs

    def contains(self, x, y):
        bx0, by0, bx1, by1 = self.bbox
        if not (bx0 <= x <= bx1 and by0 <= y <= by1):
            return False
        xs = self.crossings(y, self.buckets.get(int(math.floor(y / self.BAND)), []))
        return bisect.bisect_right(xs, x) % 2 == 1

    def dist(self, x, y):
        if self.contains(x, y):
            return 0.0
        return min(seg_dist(x, y, a[0], a[1], b[0], b[1]) for a, b in self.edges)

    def intervals(self, y):
        xs = self.crossings(y, self.buckets.get(int(math.floor(y / self.BAND)), []))
        return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


class Capsule:
    """Segment with a radius: tracks, arc pieces, vias, circles and oval pads."""

    def __init__(self, x1, y1, x2, y2, r):
        self.x1, self.y1, self.x2, self.y2, self.r = x1, y1, x2, y2, r
        self.bbox = (min(x1, x2) - r, min(y1, y2) - r, max(x1, x2) + r, max(y1, y2) + r)

    def dist(self, x, y):
        return max(0.0, seg_dist(x, y, self.x1, self.y1, self.x2, self.y2) - self.r)

    def contains(self, x, y):
        return seg_dist(x, y, self.x1, self.y1, self.x2, self.y2) <= self.r

    def intervals(self, y):
        out = []
        for cx, cy in ((self.x1, self.y1), (self.x2, self.y2)):
            dy = y - cy
            if abs(dy) <= self.r:
                h = math.sqrt(self.r * self.r - dy * dy)
                out.append((cx - h, cx + h))
        dx, dy = self.x2 - self.x1, self.y2 - self.y1
        L = math.hypot(dx, dy)
        if L > 0:
            nx, ny = -dy / L * self.r, dx / L * self.r
            band = Poly([(self.x1 + nx, self.y1 + ny), (self.x2 + nx, self.y2 + ny), (self.x2 - nx, self.y2 - ny), (self.x1 - nx, self.y1 - ny)])
            xs = band.crossings(y)
            if len(xs) >= 2:
                out.append((xs[0], xs[-1]))
        if not out:
            return []
        return [(min(a for a, _ in out), max(b for _, b in out))]


class Multi:
    """Union of shapes (a custom pad: anchor plus primitives)."""

    def __init__(self, shapes):
        self.shapes = list(shapes)
        bb = [s.bbox for s in self.shapes]
        self.bbox = (min(b[0] for b in bb), min(b[1] for b in bb), max(b[2] for b in bb), max(b[3] for b in bb))

    def dist(self, x, y):
        return min(s.dist(x, y) for s in self.shapes)

    def contains(self, x, y):
        return any(s.contains(x, y) for s in self.shapes)

    def intervals(self, y):
        spans = sorted(iv for s in self.shapes for iv in s.intervals(y))
        out = []
        for a, b in spans:
            if out and a <= out[-1][1]:
                out[-1] = (out[-1][0], max(out[-1][1], b))
            else:
                out.append((a, b))
        return out


def rect_pts(cx, cy, w, h, deg):
    out = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = rot(sx * w / 2, sy * h / 2, deg)
        out.append((cx + x, cy + y))
    return out


# ------------------------------------------------------------------ board model
class Item:
    __slots__ = ('kind', 'net', 'layer', 'shape', 'ref', 'pad', 'width', 'extra')

    def __init__(self, kind, net, layer, shape, ref=None, pad=None, width=None, extra=None):
        self.kind, self.net, self.layer, self.shape, self.ref, self.pad, self.width, self.extra = kind, net, layer, shape, ref, pad, width, extra


class Board:
    def __init__(self, tree, path=None):
        if not (isinstance(tree, list) and tree and tree[0] == 'kicad_pcb'):
            raise ValueError('not a kicad_pcb file')
        self.path = path
        self.tree = tree
        self.version = kid(tree, 'version')[1] if kid(tree, 'version') else None
        self.copper_layers = []
        for entry in (kid(tree, 'layers') or [None])[1:]:
            if isinstance(entry, list) and len(entry) >= 3 and str(entry[1]).endswith('.Cu'):
                self.copper_layers.append(str(entry[1]))
        order = {'F.Cu': 0, 'B.Cu': 999}
        self.copper_layers.sort(key=lambda n: order.get(n, int(re.sub(r'\D', '', n) or 500)))
        self.net_table = {}
        for n in kids(tree, 'net'):
            if len(n) >= 3:
                self.net_table[str(n[1])] = str(n[2])
        self.footprints, self.pads, self.copper, self.edges, self.zones, self.vias, self.tracks = [], [], [], [], [], [], []
        self.holes = []
        self.unverified = []  # what the reader models only approximately (custom pad primitives)
        for fp in kids(tree, 'footprint'):
            self._footprint(fp)
        for seg in kids(tree, 'segment'):
            self._track(seg)
        for arc in kids(tree, 'arc'):
            self._track(arc, arc=True)
        for via in kids(tree, 'via'):
            self._via(via)
        for z in kids(tree, 'zone'):
            self._zone(z)
        for head in ('gr_line', 'gr_arc', 'gr_rect', 'gr_circle', 'gr_poly'):
            for g in kids(tree, head):
                self._graphic(g, head)

    # nets
    def net_of(self, node):
        n = kid(node, 'net')
        if n is None or len(n) < 2:
            return None
        if len(n) >= 3:
            name = str(n[2])
        elif isinstance(n[1], Q):
            name = str(n[1])
        else:
            name = self.net_table.get(str(n[1]), str(n[1]))
        return name or None

    def layers_of(self, node):
        k = kid(node, 'layers')
        names = [str(x) for x in (k[1:] if k else [])] if k else []
        if not names and kid(node, 'layer'):
            names = [str(kid(node, 'layer')[1])]
        out = []
        for n in names:
            if n == '*.Cu':
                out.extend(self.copper_layers)
            elif n == 'F&B.Cu':
                out.extend(['F.Cu', 'B.Cu'])
            elif n.endswith('.Cu'):
                out.append(n)
        return [x for i, x in enumerate(out) if x not in out[:i]]

    def _footprint(self, fp):
        at = kid(fp, 'at')
        fx, fy, fa = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0
        props = {}
        for p in kids(fp, 'property'):
            props[str(p[1])] = str(p[2]) if len(p) > 2 else ''
        ref = props.get('Reference')
        if ref is None:  # KiCad 6 fp_text reference
            for t in kids(fp, 'fp_text'):
                if len(t) > 2 and t[1] == 'reference':
                    ref = str(t[2])
        side = str(kid(fp, 'layer')[1]) if kid(fp, 'layer') else 'F.Cu'
        attr = kid(fp, 'attr')
        rec = {'ref': ref, 'lib': str(fp[1]) if len(fp) > 1 and not isinstance(fp[1], list) else '', 'x': fx, 'y': fy, 'angle': fa,
               'side': 'bottom' if side == 'B.Cu' else 'top', 'props': props, 'attr': [str(a) for a in (attr[1:] if attr else [])],
               'pads': [], 'courtyard': None, 'net_tie': kid(fp, 'net_tie_pad_groups') is not None}
        pts = []
        for head in ('fp_line', 'fp_rect', 'fp_poly', 'fp_circle', 'fp_arc'):
            for g in kids(fp, head):
                lay = str(kid(g, 'layer')[1]) if kid(g, 'layer') else ''
                gp = self._shape_points(g, head, fx, fy, fa)
                if lay.endswith('CrtYd'):
                    pts.extend(gp)
                elif lay.endswith('.Cu') and gp:
                    width = num(kid(g, 'stroke') or g, 'width', default=0.0) or 0.0
                    shape = Poly(gp) if head in ('fp_poly', 'fp_rect', 'fp_circle') and len(gp) >= 3 else Capsule(gp[0][0], gp[0][1], gp[-1][0], gp[-1][1], width / 2)
                    self.copper.append(Item('fp_copper', None, lay, shape, ref=ref))
        if pts:
            rec['courtyard'] = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
        for pad in kids(fp, 'pad'):
            self._pad(pad, rec, fx, fy, fa)
        self.footprints.append(rec)

    def _shape_points(self, g, head, fx=0.0, fy=0.0, fa=0.0):
        def T(x, y):
            dx, dy = rot(float(x), float(y), fa)
            return fx + dx, fy + dy
        if head in ('fp_line', 'gr_line'):
            s, e = kid(g, 'start'), kid(g, 'end')
            return [T(s[1], s[2]), T(e[1], e[2])]
        if head in ('fp_rect', 'gr_rect'):
            s, e = kid(g, 'start'), kid(g, 'end')
            x1, y1, x2, y2 = float(s[1]), float(s[2]), float(e[1]), float(e[2])
            return [T(x1, y1), T(x2, y1), T(x2, y2), T(x1, y2)]
        if head in ('fp_circle', 'gr_circle'):
            c, e = kid(g, 'center'), kid(g, 'end')
            cx, cy = float(c[1]), float(c[2])
            r = math.hypot(float(e[1]) - cx, float(e[2]) - cy)
            return [T(cx + r * math.cos(2 * math.pi * i / 32), cy + r * math.sin(2 * math.pi * i / 32)) for i in range(32)]
        if head in ('fp_arc', 'gr_arc'):
            s, m, e = kid(g, 'start'), kid(g, 'mid'), kid(g, 'end')
            if m is None:
                return [T(s[1], s[2]), T(e[1], e[2])]
            return [T(x, y) for x, y in arc_points(float(s[1]), float(s[2]), float(m[1]), float(m[2]), float(e[1]), float(e[2]))]
        if head in ('fp_poly', 'gr_poly'):
            p = kid(g, 'pts')
            return [T(x[1], x[2]) for x in p[1:] if isinstance(x, list) and x[0] == 'xy'] if p else []
        return []

    def _pad(self, pad, fp, fx, fy, fa):
        number, kind, shape = str(pad[1]), str(pad[2]), str(pad[3]) if len(pad) > 3 else 'rect'
        at = kid(pad, 'at')
        lx, ly = float(at[1]), float(at[2])
        # KiCad 10 writes the pad's absolute orientation and omits it when it is 0 (pcb_io_kicad_sexpr.cpp format(PAD):
        # aPad->GetOrientation(), not GetFPRelativeOrientation()); the position is footprint-relative.
        angle = float(at[3]) if len(at) > 3 else 0.0
        dx, dy = rot(lx, ly, fa)
        x, y = fx + dx, fy + dy
        size = kid(pad, 'size')
        w, h = float(size[1]), float(size[2]) if len(size) > 2 else float(size[1])
        drill = kid(pad, 'drill')
        dvals = [float(v) for v in atoms(drill) if re.fullmatch(r'-?[0-9.]+', str(v))] if drill else []
        net = self.net_of(pad)
        layers = self.layers_of(pad)
        if shape == 'circle':
            geo = Capsule(x, y, x, y, w / 2)
        elif shape == 'oval':
            ax, ay = (w / 2 - h / 2, 0.0) if w >= h else (0.0, h / 2 - w / 2)
            ux, uy = rot(ax, ay, angle)
            geo = Capsule(x - ux, y - uy, x + ux, y + uy, min(w, h) / 2)
        else:  # rect, roundrect, trapezoid, chamfered rect, custom anchor: the bounding rectangle
            geo = Poly(rect_pts(x, y, w, h, angle))
        if shape == 'custom':
            opts = kid(pad, 'options')
            if opts is not None and kid(opts, 'anchor') is not None and str(kid(opts, 'anchor')[1]) == 'circle':
                geo = Capsule(x, y, x, y, w / 2)
            geo = self._custom_pad(pad, geo, x, y, angle, fp['ref'], number)
        rec = {'ref': fp['ref'], 'number': number, 'kind': kind, 'shape': shape, 'x': x, 'y': y, 'w': w, 'h': h, 'angle': angle,
               'drill': dvals, 'net': net, 'layers': layers, 'geo': geo, 'fp': fp}
        fp['pads'].append(rec)
        self.pads.append(rec)
        for lay in layers:
            self.copper.append(Item('pad', net, lay, geo, ref=fp['ref'], pad=number, extra=rec))
        if kind == 'np_thru_hole' or (kind == 'thru_hole' and (re.fullmatch(r'HB?\d*', fp['ref'] or '') or 'MountingHole' in fp['lib'])):
            d = dvals[0] if dvals else 0.0
            self.holes.append({'x': x, 'y': y, 'd': d, 'plated': kind == 'thru_hole', 'net': net, 'ref': fp['ref'], 'pad': number})

    def _custom_pad(self, pad, anchor, x, y, angle, ref, number):
        """Custom pad: the anchor plus its primitives in pad-local coordinates turned by the absolute pad orientation.
        Filled gr_poly/gr_rect/gr_circle and stroked gr_line/gr_arc are modelled; the stroke width of a filled primitive
        is not added (modelled copper up to that half-width smaller) and an unfilled circle counts as a disc; listed under
        unverified with the counts."""
        def T(px, py):
            dx, dy = rot(float(px), float(py), angle)
            return x + dx, y + dy
        shapes, stroked, skipped = [anchor], 0, []
        prims = kid(pad, 'primitives')
        for g in (prims[1:] if prims else []):
            if not isinstance(g, list) or not g:
                continue
            head = str(g[0])
            width = num(kid(g, 'stroke') or g, 'width', default=0.0) or 0.0
            if head == 'gr_poly':
                p = kid(g, 'pts')
                pts = [T(q[1], q[2]) for q in p[1:] if isinstance(q, list) and q and q[0] == 'xy'] if p else []
                if len(pts) >= 3:
                    shapes.append(Poly(pts))
                    stroked += width > 0
                else:
                    skipped.append(head)
            elif head == 'gr_rect':
                s, e = kid(g, 'start'), kid(g, 'end')
                x1, y1, x2, y2 = float(s[1]), float(s[2]), float(e[1]), float(e[2])
                shapes.append(Poly([T(x1, y1), T(x2, y1), T(x2, y2), T(x1, y2)]))
                stroked += width > 0
            elif head == 'gr_circle':
                c, e = kid(g, 'center'), kid(g, 'end')
                r = math.hypot(float(e[1]) - float(c[1]), float(e[2]) - float(c[2]))
                cx, cy = T(c[1], c[2])
                shapes.append(Capsule(cx, cy, cx, cy, r + width / 2))
            elif head == 'gr_line':
                s, e = kid(g, 'start'), kid(g, 'end')
                (ax, ay), (bx, by) = T(s[1], s[2]), T(e[1], e[2])
                shapes.append(Capsule(ax, ay, bx, by, width / 2))
            elif head == 'gr_arc' and kid(g, 'mid') is not None:
                s, m, e = kid(g, 'start'), kid(g, 'mid'), kid(g, 'end')
                pts = [T(px, py) for px, py in arc_points(float(s[1]), float(s[2]), float(m[1]), float(m[2]), float(e[1]), float(e[2]), max_seg=0.1)]
                shapes.extend(Capsule(a[0], a[1], b[0], b[1], width / 2) for a, b in zip(pts, pts[1:]))
            else:
                skipped.append(head)
        note = f'custom pad modelled as its anchor + {len(shapes) - 1} primitive shape(s)'
        if stroked:
            note += f'; stroke width of {stroked} filled primitive(s) not added'
        if skipped:
            note += f'; not modelled: {sorted(set(skipped))}'
        self.unverified.append({'check': 'geometry', 'item': f'{ref}.{number}', 'reason': note})
        return Multi(shapes) if len(shapes) > 1 else anchor

    def _track(self, node, arc=False):
        net, width = self.net_of(node), num(node, 'width', default=0.0)
        layer = str(kid(node, 'layer')[1])
        s, e = kid(node, 'start'), kid(node, 'end')
        if arc and kid(node, 'mid') is not None:
            m = kid(node, 'mid')
            pts = arc_points(float(s[1]), float(s[2]), float(m[1]), float(m[2]), float(e[1]), float(e[2]), max_seg=0.1)
        else:
            pts = [(float(s[1]), float(s[2])), (float(e[1]), float(e[2]))]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            cap = Capsule(x1, y1, x2, y2, width / 2)
            item = Item('arc' if arc else 'track', net, layer, cap, width=width)
            self.tracks.append(item)
            self.copper.append(item)

    def _via(self, node):
        at = kid(node, 'at')
        x, y = float(at[1]), float(at[2])
        size, drill = num(node, 'size', default=0.0), num(node, 'drill', default=0.0)
        net = self.net_of(node)
        lays = self.layers_of(node)
        if len(lays) == 2 and set(lays) == {'F.Cu', 'B.Cu'}:
            lays = list(self.copper_layers)  # through via
        rec = {'x': x, 'y': y, 'size': size, 'drill': drill, 'net': net, 'layers': lays}
        self.vias.append(rec)
        for lay in lays:
            self.copper.append(Item('via', net, lay, Capsule(x, y, x, y, size / 2), extra=rec))

    def _zone(self, node):
        net = self.net_of(node)
        lays = self.layers_of(node)
        keepout = kid(node, 'keepout') is not None
        outline = []
        poly = kid(node, 'polygon')
        if poly is not None and kid(poly, 'pts') is not None:
            outline = [(float(p[1]), float(p[2])) for p in kid(poly, 'pts')[1:] if isinstance(p, list) and p[0] == 'xy']
        fills = collections.defaultdict(list)
        for fp in kids(node, 'filled_polygon'):
            lay = str(kid(fp, 'layer')[1]) if kid(fp, 'layer') else (lays[0] if lays else '')
            pts = [(float(p[1]), float(p[2])) for p in kid(fp, 'pts')[1:] if isinstance(p, list) and p[0] == 'xy']
            if len(pts) >= 3:
                fills[lay].append(Poly(pts))
        name = kid(node, 'name')
        rec = {'net': net, 'layers': lays, 'keepout': keepout, 'outline': outline, 'fills': dict(fills), 'name': str(name[1]) if name else ''}
        self.zones.append(rec)
        if not keepout:
            for lay, polys in fills.items():
                for p in polys:
                    self.copper.append(Item('zone', net, lay, p, extra=rec))

    def _graphic(self, g, head):
        lay = str(kid(g, 'layer')[1]) if kid(g, 'layer') else ''
        pts = self._shape_points(g, head)
        if lay == 'Edge.Cuts':
            if head in ('gr_line', 'gr_arc'):
                self.edges.extend(zip(pts, pts[1:]))
            else:
                self.edges.extend(zip(pts, pts[1:] + pts[:1]))
        elif lay.endswith('.Cu') and pts:
            width = num(kid(g, 'stroke') or g, 'width', default=0.0) or 0.0
            if head in ('gr_poly', 'gr_rect', 'gr_circle') and len(pts) >= 3:
                shape = Poly(pts)
            else:
                shape = Capsule(pts[0][0], pts[0][1], pts[-1][0], pts[-1][1], width / 2)
            self.copper.append(Item('gr_copper', self.net_of(g), lay, shape))

    # queries
    def by_layer(self):
        out = collections.defaultdict(list)
        for it in self.copper:
            out[it.layer].append(it)
        return out


def load_board(path):
    path = Path(path)
    return Board(parse(path.read_text(encoding='utf-8')), path)


class LayerIndex:
    """Bucketed copper items of one layer for point queries."""
    CELL = 2.0

    def __init__(self, items):
        self.items = items
        self.grid = collections.defaultdict(list)
        for i, it in enumerate(items):
            x0, y0, x1, y1 = it.shape.bbox
            for gx in range(int(math.floor(x0 / self.CELL)), int(math.floor(x1 / self.CELL)) + 1):
                for gy in range(int(math.floor(y0 / self.CELL)), int(math.floor(y1 / self.CELL)) + 1):
                    self.grid[(gx, gy)].append(i)

    def at(self, x, y):
        return [self.items[i] for i in self.grid.get((int(math.floor(x / self.CELL)), int(math.floor(y / self.CELL))), ())
                if self.items[i].shape.contains(x, y)]


# ------------------------------------------------------------------ inputs
def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def load_graph():
    comps = {}
    for p in GRAPHS:
        for c in read_json(p)['components']:
            comps[c['ref']] = c
    return comps


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def r3(v):
    return round(v + 0.0, 3)


class Frame:
    """Contract coordinates (mm, y up by default) to KiCad board coordinates (mm, y down)."""

    def __init__(self, board, contract_board, spec):
        t = spec.get('contract_transform') or {}
        self.yup = t.get('y', 'up') == 'up'
        if t.get('origin') is not None:
            self.ox, self.oy = float(t['origin'][0]), float(t['origin'][1])
            self.source = 'spec contract_transform'
        else:
            pts = [p for e in board.edges for p in e]
            cpts = contract_board.get('outline_mm') or [[0, 0]]
            cminx, cminy = min(p[0] for p in cpts), min(p[1] for p in cpts)
            if pts:
                minx, miny, maxy = min(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)
            else:
                minx = miny = maxy = 0.0
            self.ox = minx - cminx
            self.oy = (maxy + cminy) if self.yup else (miny - cminy)
            self.source = 'Edge.Cuts bounding box'

    def to_board(self, x, y):
        return self.ox + x, (self.oy - y) if self.yup else (self.oy + y)

    def to_contract(self, x, y):
        return x - self.ox, (self.oy - y) if self.yup else (y - self.oy)

    def rect(self, r):
        x, y, w, h = r
        a, b = self.to_board(x, y), self.to_board(x + w, y + h)
        return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))


# ------------------------------------------------------------------ spec forms
NATIVE_KEYS = ('board_id', 'board_file', 'contract_file', 'contract_board', 'refs', 'domains', 'board_only_refs', 'board_only_pins',
               'instances', 'hole_ref_prefixes', 'contract_transform', 'bond_hole', 'gnd_chassis_ties', 'split_nets', 'neck_exempt',
               'branch_exempt', 'rf50_exempt', 'rf50_taper', 'b2b', 'tht_pockets', 'tht_pocket_margin_mm', 'height_zones', 'heights',
               'sides', 'max_height_bottom', 'coupons', 'rf_checks', 'planned_cutouts', 'copper_option', 'exemption_policy')
DICT_KEYS = ('board_only_refs', 'board_only_pins', 'contract_transform', 'bond_hole', 'split_nets', 'neck_exempt', 'branch_exempt',
             'rf50_exempt', 'rf50_taper', 'heights', 'rf_checks', 'planned_cutouts', 'exemption_policy')
LIST_KEYS = ('refs', 'domains', 'hole_ref_prefixes', 'b2b', 'tht_pockets', 'height_zones', 'sides', 'coupons')


def spec_error(spec, msg):
    bid = spec.get('board_id', '?') if isinstance(spec, dict) else '?'
    raise SystemExit(f'check_boards: {bid}: {msg}')


def v1_instances(spec, inst):
    """srrx-board-spec-v1 instances {template_nets, list [{id, refs, nets}]} -> native [{id, ref_map, net_map}]."""
    if not isinstance(inst, dict) or not isinstance(inst.get('list'), list) or not inst['list']:
        spec_error(spec, 'instances must be {"template_nets": [...], "list": [{"id", "refs", "nets"}, ...]} (srrx-board-spec-v1)')
    out = []
    for n, item in enumerate(inst['list']):
        if not isinstance(item, dict) or not isinstance(item.get('refs'), dict) or not isinstance(item.get('nets'), dict):
            spec_error(spec, f'instances.list[{n}] needs "refs" {{template_ref: graph_ref | null}} and "nets" {{template_net: graph_net}}')
        if any(v is not None and not isinstance(v, str) for v in item['refs'].values()):
            spec_error(spec, f'instances.list[{n}].refs values must be graph refs or null')
        out.append({'id': str(item.get('id', n)), 'ref_map': {k: v for k, v in item['refs'].items() if v},
                    'net_map': {str(k): str(v) for k, v in item['nets'].items()}})
    return out


def v1_height_zones(spec, zones):
    """height_zones entries: native {rect, max_height, side} or v1 {region "board" | [x, y, w, h], max_height_mm |
    max_height_mm_from_contract <contract key>, side}."""
    if not isinstance(zones, list):
        spec_error(spec, 'height_zones must be a list')
    out = []
    for n, z in enumerate(zones):
        if not isinstance(z, dict):
            spec_error(spec, f'height_zones[{n}] must be an object')
        if ('rect' in z or z.get('board') is True) and ('max_height' in z or 'max_height_from_contract' in z):
            out.append(z)  # native, or already translated
            continue
        if 'region' not in z:
            spec_error(spec, f'height_zones[{n}] needs rect + max_height or region + max_height_mm(_from_contract)')
        entry = {'side': z.get('side', 'top')}
        region = z['region']
        if region == 'board':
            entry['board'] = True
        elif isinstance(region, list) and len(region) == 4 and all(isinstance(v, (int, float)) for v in region):
            entry['rect'] = region
        else:
            spec_error(spec, f'height_zones[{n}].region must be "board" or [x, y, w, h] (contract mm)')
        if isinstance(z.get('max_height_mm'), (int, float)):
            entry['max_height'] = float(z['max_height_mm'])
        elif isinstance(z.get('max_height_mm_from_contract'), str):
            entry['max_height_from_contract'] = z['max_height_mm_from_contract']
        else:
            spec_error(spec, f'height_zones[{n}] needs max_height_mm (number) or max_height_mm_from_contract (contract key)')
        if 'checked' in z:
            entry['spec_checked'] = bool(z['checked'])
        out.append(entry)
    return out


def normalize_spec(raw):
    """The checker view of a board spec: native keys only, with the srrx-board-spec-v1 forms translated (module doc).
    Idempotent; the review hashes this view, so board_gen-only keys (router, drc_policy, ...) never stale a review."""
    if not isinstance(raw, dict) or not raw.get('board_id'):
        raise SystemExit('check_boards: a board spec must be an object with a board_id')
    schema = raw.get('schema')
    if schema not in (None, SPEC_SCHEMA_V1):
        spec_error(raw, f'unknown spec schema {schema!r} (expected {SPEC_SCHEMA_V1} or the native form without "schema")')
    spec = {k: raw[k] for k in NATIVE_KEYS if k in raw}
    if schema == SPEC_SCHEMA_V1:
        contract = raw.get('contract')
        if contract is not None:
            if not isinstance(contract, dict) or not isinstance(contract.get('board'), str):
                spec_error(raw, 'contract must be {"file": <path>, "board": <contract board id>}')
            spec.setdefault('contract_board', contract['board'])
            if contract.get('file'):
                spec.setdefault('contract_file', str(contract['file']))
        project = raw.get('project')
        if 'board_file' not in spec and isinstance(project, str) and project.endswith('.kicad_pro'):
            spec['board_file'] = project[:-len('.kicad_pro')] + '.kicad_pcb'
        if isinstance(raw.get('layers'), dict) and raw['layers'].get('copper_option'):  # W2 PWRJ-LAYERS6 (6-layer copper option)
            spec.setdefault('copper_option', str(raw['layers']['copper_option']))
        if 'instances' in raw:
            spec['instances'] = v1_instances(raw, raw['instances'])
        parts = raw.get('parts', [])
        if not isinstance(parts, list) or any(not isinstance(p, dict) or 'ref' not in p for p in parts):
            spec_error(raw, 'parts must be a list of {"ref", "source", ...}')
        only, pins = dict(spec.get('board_only_refs', {})), dict(spec.get('board_only_pins', {}))
        for p in parts:
            if p.get('source') == 'pilot_placeholder':
                only.setdefault(p['ref'], f"pilot placeholder, replaced by {p.get('replaced_by', 'TBD')}")
                if isinstance(p.get('pins'), dict):
                    pins.setdefault(p['ref'], {str(k): v for k, v in p['pins'].items()})
        if only:
            spec['board_only_refs'] = only
        if pins:
            spec['board_only_pins'] = pins
        holes = raw.get('holes')
        if holes is not None:
            if not isinstance(holes, dict):
                spec_error(raw, 'holes must be an object (srrx-board-spec-v1: from_contract, ref_prefix, keepout_*)')
            if holes.get('ref_prefix'):
                spec['hole_ref_prefixes'] = sorted(set(spec.get('hole_ref_prefixes', [])) | {str(holes['ref_prefix'])})
    elif isinstance(spec.get('instances'), dict):
        spec['instances'] = v1_instances(raw, spec['instances'])
    if 'height_zones' in spec:
        spec['height_zones'] = v1_height_zones(raw, spec['height_zones'])
    for k in DICT_KEYS:
        if k in spec and not isinstance(spec[k], dict):
            spec_error(raw, f'{k} must be an object')
    for k in LIST_KEYS:
        if k in spec and not isinstance(spec[k], list):
            spec_error(raw, f'{k} must be a list')
    if 'instances' in spec and (not isinstance(spec['instances'], list)
                                or any(not isinstance(i, dict) or not isinstance(i.get('ref_map', {}), dict)
                                       or not isinstance(i.get('net_map', {}), dict) for i in spec['instances'])):
        spec_error(raw, 'instances must be [{"id", "ref_map": {...}, "net_map": {...}}] (native) or the srrx-board-spec-v1 object')
    return spec


def mounting_refs(board, spec):
    """Mounting-hole footprints: ref H<n> / HB<n> (or a spec hole ref prefix), library MountingHole:*, or only NPTH pads.
    Only these are left out of the height and THT-pocket checks; connectors with NPTH pegs are checked normally."""
    prefixes = {'H', 'HB'} | set(spec.get('hole_ref_prefixes', []))
    out = set()
    for fp in board.footprints:
        ref = fp['ref'] or ''
        m = re.fullmatch(r'(.*?)\d+', ref)
        if (m and m.group(1) in prefixes) or 'MountingHole' in fp['lib'] \
                or (fp['pads'] and all(p['kind'] == 'np_thru_hole' for p in fp['pads'])):
            out.add(ref)
    return out


# ------------------------------------------------------------------ checks
def finding(check, item, detail, at=None, contract_at=None, **values):
    """One finding; `at` is in KiCad board coordinates, `contract_at` in the board contract frame (mm)."""
    f = {'check': check, 'item': item, 'detail': detail}
    if at is not None:
        f['at'] = [r3(at[0]), r3(at[1])]
    if contract_at is not None:
        f['contract_at'] = [r3(float(contract_at[0])), r3(float(contract_at[1]))]
    for k, v in values.items():
        f[k] = r3(v) if isinstance(v, float) else v
    return f


def loops(edges, tol=1e-3):
    key = lambda p: (round(p[0] / tol), round(p[1] / tol))
    adj = collections.defaultdict(list)
    for i, (a, b) in enumerate(edges):
        adj[key(a)].append((i, b))
        adj[key(b)].append((i, a))
    used, out, bad = set(), [], 0
    for i, (a, b) in enumerate(edges):
        if i in used:
            continue
        used.add(i)
        pts, cur, start = [a], b, key(a)
        while key(cur) != start:
            pts.append(cur)
            nxt = [(j, q) for j, q in adj[key(cur)] if j not in used]
            if not nxt:
                bad += 1
                break
            j, q = nxt[0]
            used.add(j)
            cur = q
        else:
            out.append(pts)
    return out, bad


def simplify(pts, tol=1e-4):
    out = list(pts)
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) < tol and seg_dist(b[0], b[1], a[0], a[1], c[0], c[1]) < 1e-3:
                del out[i]
                changed = True
                break
    return out


def same_polygon(a, b, tol=POS_TOL):
    if len(a) != len(b):
        return False
    n = len(a)
    for direction in (1, -1):
        bb = b if direction == 1 else b[::-1]
        for shift in range(n):
            if all(math.hypot(a[i][0] - bb[(i + shift) % n][0], a[i][1] - bb[(i + shift) % n][1]) <= tol for i in range(n)):
                return True
    return False


def coupon_boxes(spec, frame):
    """Board-coordinate boxes of the spec coupons (contract rects [x, y, w, h])."""
    out = []
    for n, c in enumerate(spec.get('coupons', [])):
        if not isinstance(c, dict) or not isinstance(c.get('rect'), list) or len(c['rect']) != 4:
            spec_error(spec, f'coupons[{n}] needs rect [x, y, w, h] (contract frame)')
        out.append(frame.rect(c['rect']))
    return out


def check_outline(board, cb, frame, spec=None):
    out = []
    lps, open_chains = loops(board.edges)
    if open_chains or not lps:
        out.append(finding('outline', 'Edge.Cuts', f'outline not closed ({open_chains} open chain(s), {len(lps)} loop(s))'))
        return out, {}
    lps = [simplify(lp) for lp in lps]
    boxes = coupon_boxes(spec or {}, frame)
    coupon_loops = [lp for lp in lps if any(all(b[0] - POS_TOL <= x <= b[2] + POS_TOL and b[1] - POS_TOL <= y <= b[3] + POS_TOL
                                                 for x, y in lp) for b in boxes)]
    lps = [lp for lp in lps if not any(lp is c for c in coupon_loops)]
    if not lps:
        out.append(finding('outline', 'Edge.Cuts', 'no board outline outside the spec coupons'))
        return out, {}
    lps.sort(key=lambda p: -abs(poly_area(p)))
    outer, inner = lps[0], lps[1:]
    want = [frame.to_board(x, y) for x, y in cb['outline_mm']]
    if not same_polygon(outer, want):
        out.append(finding('outline', 'Edge.Cuts outer', 'outer outline differs from the contract outline_mm',
                           board=[[r3(x), r3(y)] for x, y in (frame.to_contract(*p) for p in outer)], contract=cb['outline_mm']))
    cuts = [[frame.to_board(x, y), frame.to_board(x + w, y), frame.to_board(x + w, y + h), frame.to_board(x, y + h)] for x, y, w, h in cb.get('cutouts_mm', [])]
    matched = set()
    for lp in inner:
        hit = [i for i, c in enumerate(cuts) if i not in matched and same_polygon(lp, c)]
        if hit:
            matched.add(hit[0])
        else:
            out.append(finding('outline', 'Edge.Cuts cutout', 'cutout not in the contract cutouts_mm',
                               contract_at=frame.to_contract(*lp[0]), vertices=len(lp)))
    for i, c in enumerate(cb.get('cutouts_mm', [])):
        if i not in matched:
            out.append(finding('outline', 'contract cutout', f'contract cutout {c} missing on the board'))
    area = abs(poly_area(outer)) - sum(abs(poly_area(lp)) for lp in inner)
    if cb.get('area_mm2') is not None and abs(area - cb['area_mm2']) > 0.5:
        out.append(finding('outline', 'area', 'board area differs from the contract area_mm2', value=area, limit=cb['area_mm2']))
    info = {'area_mm2': r3(area), 'loops': len(lps)}
    if boxes:  # only boards with spec coupons carry this key
        info['coupon_loops'] = len(coupon_loops)
    return out, info


def check_holes(board, cb, frame, spec):
    out = []
    want = [frame.to_board(x, y) for x, y in cb.get('holes_mm', [])]
    d_want = cb.get('hole_d')
    bond = spec.get('bond_hole')
    bond_at = frame.to_board(*bond['at']) if bond else None
    candidates = [h for h in board.holes if d_want is None or abs(h['d'] - d_want) <= 0.05 + 1e-9]
    used = set()
    for (x, y), cpos in zip(want, cb.get('holes_mm', [])):
        near = [i for i, h in enumerate(candidates) if i not in used and math.hypot(h['x'] - x, h['y'] - y) <= POS_TOL + 1e-9]
        if not near:
            out.append(finding('holes', f'contract hole {cpos}', 'no hole of the contract diameter at this position', contract_at=cpos))
            continue
        i = near[0]
        used.add(i)
        h = candidates[i]
        if d_want is not None and abs(h['d'] - d_want) > HOLE_D_TOL + 1e-9:
            out.append(finding('holes', f"{h['ref']}", 'hole diameter differs from the contract hole_d', contract_at=cpos, value=h['d'], limit=d_want))
        is_bond = bond_at is not None and math.hypot(h['x'] - bond_at[0], h['y'] - bond_at[1]) <= POS_TOL + 1e-9
        if is_bond:
            if not h['plated'] or h['net'] != bond.get('net'):
                out.append(finding('holes', f"{h['ref']}", f"BOND-RF hole must be plated on net {bond.get('net')}", contract_at=cpos, net=h['net'], plated=h['plated']))
        elif h['plated'] or h['net']:
            out.append(finding('holes', f"{h['ref']}", 'mounting hole is plated or netted (only the BOND-RF hole may be)', contract_at=cpos, net=h['net'], plated=h['plated']))
    for i, h in enumerate(candidates):
        if i not in used:
            out.append(finding('holes', f"{h['ref']}", 'hole of the contract diameter not in the contract holes_mm', contract_at=frame.to_contract(h['x'], h['y'])))
    if bond and not any(math.hypot(bond_at[0] - x, bond_at[1] - y) <= POS_TOL for x, y in want):
        out.append(finding('holes', 'bond_hole', 'spec bond_hole is not a contract hole', contract_at=bond['at']))
    return out, {'contract_holes': len(want), 'board_holes': len(board.holes)}


def check_keepouts(board, cb, frame, spec):
    out = []
    r = (cb.get('hole_keepout_d') or 0) / 2
    if not r:
        return out, {'keepout_r_mm': 0}
    bond = spec.get('bond_hole')
    bond_at = frame.to_board(*bond['at']) if bond else None
    for cx, cy in (frame.to_board(x, y) for x, y in cb.get('holes_mm', [])):
        is_bond = bond_at is not None and math.hypot(cx - bond_at[0], cy - bond_at[1]) <= POS_TOL
        hole_pad = None
        for h in board.holes:
            if math.hypot(h['x'] - cx, h['y'] - cy) <= POS_TOL:
                hole_pad = (h['ref'], h['pad'])
        for it in board.copper:
            if it.shape.dist(cx, cy) >= r - KEEPOUT_TOL:
                continue
            if hole_pad and it.kind == 'pad' and (it.ref, it.pad) == hole_pad:
                continue
            if is_bond and it.net is not None and it.net == bond.get('net'):
                continue
            what = f'{it.kind} {it.ref}.{it.pad}' if it.kind == 'pad' else it.kind
            out.append(finding('keepouts', what, f'copper inside the hole keepout (d {2 * r} mm)', contract_at=frame.to_contract(cx, cy),
                               net=it.net, layer=it.layer, distance=it.shape.dist(cx, cy)))
    return out, {'keepout_r_mm': r, 'tolerance_mm': KEEPOUT_TOL}


def shape_hits_box(shape, box):
    """True when a copper shape (Poly, Capsule, Multi) overlaps an axis-aligned box (x0, y0, x1, y1), KiCad mm."""
    x0, y0, x1, y1 = box
    bx0, by0, bx1, by1 = shape.bbox
    if bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1:
        return False
    if isinstance(shape, Multi):
        return any(shape_hits_box(s, box) for s in shape.shapes)
    if isinstance(shape, Capsule):
        return seg_box_gap(shape.x1, shape.y1, shape.x2, shape.y2, box) <= shape.r
    # Poly (even-odd, fractured fills): the box centre inside it, or an edge of it inside or across the box
    if shape.contains((x0 + x1) / 2, (y0 + y1) / 2):
        return True
    edges = []
    for b in range(int(math.floor(y0 / shape.BAND)), int(math.floor(y1 / shape.BAND)) + 1):
        edges.extend(shape.buckets.get(b, []))
    return any(seg_box_gap(a[0], a[1], c[0], c[1], box) == 0.0 for a, c in set(edges))


def seg_box_gap(xa, ya, xb, yb, box):
    """Distance from segment ab to an axis-aligned box (0 when it touches, crosses or lies inside)."""
    x0, y0, x1, y1 = box
    if x0 <= xa <= x1 and y0 <= ya <= y1 or x0 <= xb <= x1 and y0 <= yb <= y1:
        return 0.0
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for (cx, cy), (dx, dy) in zip(corners, corners[1:] + corners[:1]):
        if seg_seg_dist((xa, ya), (xb, yb), (cx, cy), (dx, dy)) == 0.0:
            return 0.0
    return min([seg_dist(cx, cy, xa, ya, xb, yb) for cx, cy in corners]
               + [seg_dist(px, py, cx, cy, dx, dy) for px, py in ((xa, ya), (xb, yb))
                  for (cx, cy), (dx, dy) in zip(corners, corners[1:] + corners[:1])])


# A copper polygon with more points than this is a zone fill: planned_cutouts tests it for overlap (shape_hits_box, banded
# edges) instead of an edge-to-edge distance over all its edges
FILL_POINTS = 64


def check_planned_cutouts(board, frame, spec):
    """planned_cutouts {margin_mm, rects [{id, rect [x, y, w, h] contract mm}]} (W2 PWRB-R; pcb/board_gen.py makes each rect
    grown by margin_mm a rule area; W2 PWR-TOOLS: the only cut-out key, keepout_rects removed): areas that become board
    cut-outs later. No copper item of any kind or layer (pads, tracks, arcs, vias, zone fills, footprint and board copper)
    may lie inside a rect or closer than margin_mm to it, the copper-to-edge clearance the cut will need. Pads, tracks, vias
    and small polygons are measured edge to edge against the rect; a zone fill (a polygon of more than FILL_POINTS points)
    must not overlap the rect grown by margin_mm less KEEPOUT_TOL (its filled polygon, holes and slits included)."""
    pc = spec['planned_cutouts']
    if not isinstance(pc.get('rects'), list) or not isinstance(pc.get('margin_mm'), (int, float)):
        spec_error(spec, 'planned_cutouts needs margin_mm and rects [{id, rect [x, y, w, h]}]')
    m = float(pc['margin_mm'])
    out, rows = [], []
    for r in pc['rects']:
        x0, y0, x1, y1 = frame.rect(r['rect'])
        box = Poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        g = m - KEEPOUT_TOL
        grown = (x0 - g, y0 - g, x1 + g, y1 + g)
        inside, near, fills, closest = 0, 0, 0, None
        for it in board.copper:
            bb = it.shape.bbox
            if bb[0] > x1 + m or bb[2] < x0 - m or bb[1] > y1 + m or bb[3] < y0 - m:
                continue
            what = f'{it.kind} {it.ref}.{it.pad}' if it.kind == 'pad' else it.kind
            if isinstance(it.shape, Poly) and len(it.shape.pts) > FILL_POINTS:
                if shape_hits_box(it.shape, grown):
                    fills += 1
                    out.append(finding('planned_cutouts', what, f"copper fill within {m} mm of the planned cut-out {r['id']}",
                                       contract_at=r['rect'][:2], net=it.net, layer=it.layer))
                continue
            d = shape_gap(it.shape, box)
            closest = d if closest is None else min(closest, d)
            if d >= m - KEEPOUT_TOL:
                continue
            inside += d <= 0.0
            near += d > 0.0
            out.append(finding('planned_cutouts', what, f"copper {r3(d)} mm from the planned cut-out {r['id']} (needs {m} mm)",
                               contract_at=r['rect'][:2], net=it.net, layer=it.layer, distance=d))
        rows.append({'id': r['id'], 'items_inside': inside, 'items_within_margin': near, 'fills_within_margin': fills,
                     'closest_copper_mm': r3(closest) if closest is not None else None})
    return out, {'margin_mm': m, 'rects': len(pc['rects']), 'tolerance_mm': KEEPOUT_TOL, 'fill_points': FILL_POINTS,
                 'per_rect': rows}


def expected_views(spec, graph, components_csv=None):
    """[(view id, ref_map board->graph, net_map board->graph)] and the graph refs the board must carry."""
    inst = spec.get('instances')
    if isinstance(inst, dict):  # srrx-board-spec-v1 form
        inst = v1_instances(spec, inst)
    if inst:
        if not isinstance(inst, list) or any(not isinstance(i, dict) for i in inst):
            spec_error(spec, 'instances must be a list of {"id", "ref_map", "net_map"} or the srrx-board-spec-v1 object')
        views = [(str(i.get('id', n)), dict(i.get('ref_map') or {}), dict(i.get('net_map') or {})) for n, i in enumerate(inst)]
    else:
        if spec.get('refs') is not None:
            refs = list(spec['refs'])
        elif spec.get('domains'):
            if components_csv is not None:
                rows = components_csv
            else:
                with COMPONENTS.open(encoding='utf-8', newline='') as fh:
                    rows = list(csv.DictReader(fh))
            refs = [r['ref'] for r in rows if r['board_candidate'] in set(spec['domains']) and r['category'] == 'bare_board_part']
        else:
            refs = []
        views = [('board', {r: r for r in refs}, {})]
    return views


def check_pad_nets(board, spec, graph, views):
    out = []
    fps = {fp['ref']: fp for fp in board.footprints if fp['ref']}
    board_refs = set()
    for vid, ref_map, net_map in views:
        for bref, gref in sorted(ref_map.items()):
            board_refs.add(bref)
            comp = graph.get(gref)
            if comp is None:
                out.append(finding('pad_nets', f'{vid}:{gref}', 'graph has no such ref'))
                continue
            fp = fps.get(bref)
            if fp is None:
                out.append(finding('pad_nets', f'{vid}:{bref}', f'graph ref {gref} has no footprint on the board'))
                continue
            gfp = comp.get('footprint') or ''
            if gfp and fp['lib'] and fp['lib'] != gfp:
                out.append(finding('pad_nets', f'{bref}', 'footprint differs from the graph', value=fp['lib'], limit=gfp))
            pins = {str(p['number']): p.get('net') for p in comp['pins']}
            seen = set()
            for pad in fp['pads']:
                if pad['kind'] == 'np_thru_hole' or pad['number'] == '':
                    continue
                bnet = pad['net']
                if bnet and bnet.startswith('unconnected-'):
                    bnet = None
                gnet = net_map.get(bnet, bnet) if bnet else None
                if pad['number'] not in pins:
                    if bnet:
                        out.append(finding('pad_nets', f"{bref}.{pad['number']}", 'netted pad that the graph does not have', net=bnet))
                    continue
                seen.add(pad['number'])
                if gnet != pins[pad['number']]:
                    out.append(finding('pad_nets', f"{bref}.{pad['number']}", f'{vid}: board net differs from the graph',
                                       at=(pad['x'], pad['y']), net=bnet, graph_net=pins[pad['number']]))
            for number in sorted(set(pins) - seen):
                if pins[number]:
                    out.append(finding('pad_nets', f'{bref}.{number}', f'graph pin of {gref} has no pad', graph_net=pins[number]))
    allowed = spec.get('board_only_refs', {})
    for ref, want in sorted(spec.get('board_only_pins', {}).items()):  # placeholders: pads against the spec pin map
        fp = fps.get(ref)
        if fp is None:
            out.append(finding('pad_nets', ref, 'board-only part with a spec pin map has no footprint on the board'))
            continue
        have = {}
        for pad in fp['pads']:
            if pad['kind'] == 'np_thru_hole' or pad['number'] == '':
                continue
            net = pad['net'] if pad['net'] and not pad['net'].startswith('unconnected-') else None
            have.setdefault(pad['number'], set()).add(net)
        for number in sorted(set(want) | set(have)):
            nets = have.get(number)
            if nets is None:
                out.append(finding('pad_nets', f'{ref}.{number}', 'spec pin of the board-only part has no pad', net=want[number]))
            elif nets != {want.get(number)}:
                out.append(finding('pad_nets', f'{ref}.{number}', 'pad net differs from the spec pin map of the board-only part',
                                   net=sorted(n or '' for n in nets), graph_net=want.get(number)))
    for ref, fp in sorted(fps.items()):
        if ref in board_refs or ref in allowed:
            continue
        netted = [p for p in fp['pads'] if p['net'] and not p['net'].startswith('unconnected-')]
        if netted and not ref.startswith('HB'):
            out.append(finding('pad_nets', ref, 'netted footprint that the spec does not expect (refs/domains/board_only_refs)'))
    return out, {'expected_refs': len(board_refs), 'board_footprints': len(fps)}


def class_map(netclasses, views):
    """Board net -> (graph net, class)."""
    nets = netclasses.get('nets', {})
    default = netclasses.get('default_class', 'SIG')

    def lookup(bnet):
        for _vid, _rm, nm in views:
            g = nm.get(bnet, bnet)
            if g in nets:
                return g, nets[g]['class']
        return bnet, default
    return lookup


def split_layers(spec, bnet, gnet):
    """Layers a spec declares for a split net (keyed by graph or board net)."""
    sn = spec.get('split_nets', {})
    return sn.get(gnet) or sn.get(bnet)


def layer_requirement(cls_name, cls, layer, net, spec, outer_layers, split_ok=frozenset(), bnet=None):
    """(required width mm, note) for copper of a class net on a layer; None when the layer is not counted.
    The split width applies only to nets in split_ok (declared and verified by check_split)."""
    if cls.get('kind') == 'power':
        if layer in outer_layers:
            split = split_layers(spec, bnet or net, net)
            if split and cls.get('split_outer_per_layer_mm') and set(split) >= set(outer_layers) and layer in split and net in split_ok:
                return cls['split_outer_per_layer_mm'], 'split L1+L4'
            return cls['outer_min_width_mm'], 'single layer'
        if cls.get('inner_min_width_mm') is None:
            return None, 'inner copper not counted for ' + cls_name
        return cls['inner_min_width_mm'], 'inner'
    if cls.get('kind') in ('signal', 'dc_tap'):
        return cls['outer_min_width_mm'] if layer in outer_layers else cls['inner_min_width_mm'], 'class width'
    return None, 'not a width class'


def raster_neck(items, terminals, region, grid=NECK_GRID, entry=0.0):
    """Narrowest copper cross-section (mm) between terminals inside a region, per island: [(width, x, y)].

    Copper within `entry` mm of a terminal (pad or via) counts as that terminal: a pad at the end of a pour or track
    is entered over its own size, so the neck is measured beyond half the required width from every terminal."""
    x0, y0, x1, y1 = region
    nx, ny = max(1, int(math.ceil((x1 - x0) / grid))), max(1, int(math.ceil((y1 - y0) / grid)))
    cop = bytearray(nx * ny)
    term = [0] * (nx * ny)

    def fill(shape, value, target):
        bx0, by0, bx1, by1 = shape.bbox
        j0, j1 = max(0, int((by0 - y0) / grid) - 1), min(ny - 1, int((by1 - y0) / grid) + 1)
        for j in range(j0, j1 + 1):
            yc = y0 + (j + 0.5) * grid
            for a, b in shape.intervals(yc):
                i0 = max(0, int(math.ceil((a - x0) / grid - 0.5)))
                i1 = min(nx - 1, int(math.floor((b - x0) / grid - 0.5)))
                base = j * nx
                for i in range(i0, i1 + 1):
                    target[base + i] = value
    for it in items:
        fill(it.shape, 1, cop)
    for k, shape in enumerate(terminals, 1):
        fill(shape, k, term)
        fill(shape, 1, cop)
    if entry > 0:  # grow each terminal through copper by `entry` mm (multi-source BFS, Euclidean to the source cell)
        lim = (entry / grid) ** 2
        queue = collections.deque((c, c) for c in range(nx * ny) if term[c])
        while queue:
            c, src = queue.popleft()
            i, j = c % nx, c // nx
            si, sj = src % nx, src // nx
            for nb, ni, nj in ((c - 1, i - 1, j), (c + 1, i + 1, j), (c - nx, i, j - 1), (c + nx, i, j + 1)):
                if 0 <= ni < nx and 0 <= nj < ny and cop[nb] and not term[nb] and (ni - si) ** 2 + (nj - sj) ** 2 <= lim:
                    term[nb] = term[c]
                    queue.append((nb, src))
    # region border copper continues outside: each border run is a terminal
    nxt = len(terminals) + 1
    border = [(i, 0) for i in range(nx)] + [(nx - 1, j) for j in range(ny)] + [(i, ny - 1) for i in range(nx - 1, -1, -1)] + [(0, j) for j in range(ny - 1, -1, -1)]
    prev = False
    for i, j in border:
        c = j * nx + i
        if cop[c]:
            if not prev:
                nxt += 1
            if not term[c]:
                term[c] = nxt
            prev = True
        else:
            prev = False
    # squared Euclidean distance (cells) to the nearest non-copper cell, outside the region counts as copper
    INF = 1e18
    d2 = [0.0 if not cop[c] else INF for c in range(nx * ny)]

    def edt1(f, n):
        v, z, out = [0] * n, [0.0] * (n + 1), [0.0] * n
        k = -1
        for q in range(n):
            if f[q] >= INF:
                continue
            while k >= 0:
                s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k])
                if s <= z[k]:
                    k -= 1
                else:
                    break
            k += 1
            v[k] = q
            z[k] = -INF if k == 0 else ((f[q] + q * q) - (f[v[k - 1]] + v[k - 1] * v[k - 1])) / (2 * q - 2 * v[k - 1])
            z[k + 1] = INF
        if k < 0:
            return [INF] * n
        j = 0
        for q in range(n):
            while z[j + 1] < q:
                j += 1
            out[q] = (q - v[j]) ** 2 + f[v[j]]
        return out
    for j in range(ny):
        d2[j * nx:(j + 1) * nx] = edt1(d2[j * nx:(j + 1) * nx], nx)
    for i in range(nx):
        col = edt1(d2[i::nx], ny)
        d2[i::nx] = col
    parent = list(range(nx * ny))
    has_t = [False] * (nx * ny)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    order = sorted((c for c in range(nx * ny) if cop[c]), key=lambda c: (0 if term[c] else 1, -d2[c]))
    active = bytearray(nx * ny)
    merges = []
    for c in order:
        active[c] = 1
        has_t[c] = bool(term[c])
        i, j = c % nx, c // nx
        for nb in ((c - 1) if i > 0 else -1, (c + 1) if i < nx - 1 else -1, (c - nx) if j > 0 else -1, (c + nx) if j < ny - 1 else -1):
            if nb < 0 or not active[nb]:
                continue
            ra, rb = find(c), find(nb)
            if ra == rb:
                continue
            if has_t[ra] and has_t[rb] and not (term[c] and term[nb]):
                merges.append((math.sqrt(d2[c]) if d2[c] < INF else INF, c))
            parent[rb] = ra
            has_t[ra] = has_t[ra] or has_t[rb]
    worst = {}
    for level, c in merges:
        root = find(c)
        if root not in worst or level < worst[root][0]:
            worst[root] = (level, c)
    out = []
    for level, c in worst.values():
        if level >= INF:
            continue
        width = 2 * level * grid - grid
        out.append((width, x0 + (c % nx + 0.5) * grid, y0 + (c // nx + 0.5) * grid))
    return sorted(out)


def raster_fill(shape, value, target, x0, y0, grid, nx, ny):
    """Mark the raster cells whose centres lie inside a shape."""
    bx0, by0, bx1, by1 = shape.bbox
    j0, j1 = max(0, int((by0 - y0) / grid) - 1), min(ny - 1, int((by1 - y0) / grid) + 1)
    for j in range(j0, j1 + 1):
        yc = y0 + (j + 0.5) * grid
        for a, b in shape.intervals(yc):
            i0 = max(0, int(math.ceil((a - x0) / grid - 0.5)))
            i1 = min(nx - 1, int(math.floor((b - x0) / grid - 0.5)))
            base = j * nx
            for i in range(i0, i1 + 1):
                target[base + i] = value


def raster_grid(region):
    x0, y0, x1, y1 = region
    return max(NECK_GRID, math.ceil(math.sqrt((x1 - x0) * (y1 - y0) / NECK_MAX_CELLS) * 100) / 100)


def raster_islands(shapes, region, grid):
    """4-connected copper islands of shapes on a raster; returns a function (x, y) -> island id (0 = no copper)."""
    x0, y0, x1, y1 = region
    nx, ny = max(1, int(math.ceil((x1 - x0) / grid))), max(1, int(math.ceil((y1 - y0) / grid)))
    cop = bytearray(nx * ny)
    for s in shapes:
        raster_fill(s, 1, cop, x0, y0, grid, nx, ny)
    label = [0] * (nx * ny)
    nxt = 0
    for c in range(nx * ny):
        if not cop[c] or label[c]:
            continue
        nxt += 1
        label[c] = nxt
        queue = collections.deque([c])
        while queue:
            q = queue.popleft()
            i, j = q % nx, q // nx
            for nb, ok in ((q - 1, i > 0), (q + 1, i < nx - 1), (q - nx, j > 0), (q + nx, j < ny - 1)):
                if ok and cop[nb] and not label[nb]:
                    label[nb] = nxt
                    queue.append(nb)

    def at(x, y):
        i, j = int((x - x0) / grid), int((y - y0) / grid)
        for di, dj in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            ii, jj = i + di, j + dj
            if 0 <= ii < nx and 0 <= jj < ny and label[jj * nx + ii]:
                return label[jj * nx + ii]
        return 0
    return at


def check_split(board, bnet, layers, skip=frozenset()):
    """(ok, reason) for a net declared split over `layers`: each layer carries its own copper (pour or tracks) and joins
    the same groups of the net's vias and THT pads (the layers run in parallel between the same transitions)."""
    items = [it for it in board.copper if it.net == bnet and it.layer in layers and id(it) not in skip]
    terms = [(v['x'], v['y']) for v in board.vias if v['net'] == bnet and set(layers) <= set(v['layers'])]
    terms += [(p['x'], p['y']) for p in board.pads if p['net'] == bnet and p['kind'] == 'thru_hole' and set(layers) <= set(p['layers'])]
    for layer in layers:
        if not any(it.layer == layer and it.kind in ('zone', 'track', 'arc', 'gr_copper') for it in items):
            return False, f'no {layer} pour or track of the net (pads and vias only)'
    if not terms:
        return False, 'no via or THT pad of the net joins the declared layers'
    if not items:
        return False, 'no copper of the net on the declared layers'
    region = (min(it.shape.bbox[0] for it in items) - 1.0, min(it.shape.bbox[1] for it in items) - 1.0,
              max(it.shape.bbox[2] for it in items) + 1.0, max(it.shape.bbox[3] for it in items) + 1.0)
    grid = raster_grid(region)
    groups = {}
    for layer in layers:
        shapes = []
        for it in items:
            if it.layer != layer:
                continue
            s = it.shape
            # thin tracks and vias get half a cell more so a coarse raster cannot break them
            shapes.append(Capsule(s.x1, s.y1, s.x2, s.y2, s.r + grid / 2) if isinstance(s, Capsule) else s)
        at = raster_islands(shapes, region, grid)
        part = collections.defaultdict(set)
        for k, (x, y) in enumerate(terms):
            part[at(x, y)].add(k)
        groups[layer] = sorted(sorted(g) for lbl, g in part.items() if lbl) + [sorted(part.get(0, ()))]
    first = groups[layers[0]]
    for layer in layers[1:]:
        if groups[layer] != first:
            return False, f'{layers[0]} and {layer} join different groups of the net vias/THT pads ({len(first) - 1} vs {len(groups[layer]) - 1} island group(s), raster {grid} mm)'
    return True, f'{len(terms)} via/THT transition(s) joined alike on {layers}'


def track_chain(board, net, start_pads, max_len, width_ok):
    """Track pieces of `net` reached from `start_pads` along connected segments (vias join layers), within max_len mm path
    length and each passing width_ok. A chain stops where it joins other copper of the net: another pad or the net's pour.
    Returns (items, longest path mm)."""
    segs = [it for it in board.tracks if it.net == net]
    vias = [v for v in board.vias if v['net'] == net]
    zones = [it for it in board.copper if it.kind == 'zone' and it.net == net]
    start_ids = {id(p) for p in start_pads}
    others = [p for p in board.pads if p['net'] == net and id(p) not in start_ids]

    def key(x, y, layer):
        return (layer, round(x / CHAIN_TOL), round(y / CHAIN_TOL))
    adj, pts = collections.defaultdict(list), {}
    for i, it in enumerate(segs):
        s = it.shape
        a, b = key(s.x1, s.y1, it.layer), key(s.x2, s.y2, it.layer)
        length = math.hypot(s.x2 - s.x1, s.y2 - s.y1)
        adj[a].append((i, b, length))
        adj[b].append((i, a, length))
        pts[a], pts[b] = (s.x1, s.y1, it.layer), (s.x2, s.y2, it.layer)
    for v in vias:
        joined = [n for n, (x, y, layer) in pts.items() if layer in v['layers'] and math.hypot(x - v['x'], y - v['y']) <= v['size'] / 2 + 1e-9]
        for a in joined:
            adj[a].extend((None, b, 0.0) for b in joined if b != a)

    def inside(x, y, layer, pads):
        return any(layer in p['layers'] and p['geo'].contains(x, y) for p in pads)
    dist, heap = {}, []
    for n, (x, y, layer) in pts.items():
        if inside(x, y, layer, start_pads):
            dist[n] = 0.0
            heap.append((0.0, n))
    heapq.heapify(heap)
    chain, longest = {}, 0.0
    while heap:
        d, n = heapq.heappop(heap)
        if d > dist.get(n, math.inf):
            continue
        x, y, layer = pts[n]
        if d > 0 and (inside(x, y, layer, others) or any(z.layer == layer and z.shape.contains(x, y) for z in zones)):
            continue
        for i, m, length in adj[n]:
            nd = d + length
            if nd > max_len + 1e-9 or (i is not None and not width_ok(segs[i])):
                continue
            if i is not None:
                chain[i] = segs[i]
                longest = max(longest, nd)
            if nd < dist.get(m, math.inf):
                dist[m] = nd
                heapq.heappush(heap, (nd, m))
    return [chain[i] for i in sorted(chain)], longest


# W2 PWR-L6-SCRIPT exemption policy (spec key exemption_policy, opt-in): the role of a pad decides which class-width exemption
# it may carry. Allowed for branch_exempt: test points, resistors of 100 ohm or more, sense or logic pins. Never for a neck:
# the power-path parts below. Sense or logic pins of an IC (pin names, upper case); a capacitor between a power net and a
# signal net (not GND, not power class: a bootstrap, feed-forward or filter capacitor) counts as a sense or logic part too.
EXEMPT_BRANCH_ROLES = ('test_point', 'resistor_ge_100', 'sense_logic_pin')
EXEMPT_NECK_FORBIDDEN = ('tvs', 'connector', 'shunt', 'fuse', 'power_switch', 'efuse_in_out', 'converter_capacitor')
SENSE_LOGIC_PINS = frozenset((
    'FB', 'SENSE/FB', 'SENSE', 'VSENSE', 'BIAS', 'VCC', 'VDD', 'VS', 'VLDOIN', 'VCAP', 'EN', 'EN/UV', 'EN/UVLO', 'EN/SYNC',
    'UVLO', 'OVLO', 'PG', 'PGOOD', 'PGFB', 'RT', 'SS', 'TR', 'ILM', 'ILIM', 'DVDT', 'SET', 'OUTS', 'ANODE', 'CATHODE', 'INA', 'INB',
    'CBOOT', 'BOOT', 'BST', 'RBOOT', 'IN+', 'IN-', 'INP', 'INN'))
TVS_MARKERS = ('SMBJ', 'SMAJ', 'SMCJ', 'SMF', 'TVS', 'ESD', 'PESD', 'TPD')
EFUSE_MARKERS = ('TPS259', 'TPS2596', 'TPS2594')        # TI eFuses (TPS259470, TPS259630, ...)
LOAD_SWITCH_MARKERS = ('TPS2553', 'TPS2051', 'TPS22')     # TI current-limited power switches
CONVERTER_POWER_PINS = ('VIN', 'VIN1', 'VIN2', 'PVIN', 'VOUT', 'VOUT1', 'VOUT2', 'SW', 'LX', 'PH')


def ohms_of(value):
    """Resistance of a graph value string ('10k 1%', '0.22R', '0R33', 'WSL2512R3300FEA 0.330 Ω'): ohms or None."""
    text = str(value or '').replace('Ω', 'R').replace('Ohm', 'R').replace('ohm', 'R')
    toks = text.split()
    for i, tok in enumerate(toks):
        m = re.fullmatch(r'([0-9]+)[Rr]([0-9]+)', tok)
        if m:
            return float(f'{m.group(1)}.{m.group(2)}')
        m = re.match(r'([0-9]+(?:[.,][0-9]+)?)([RrKkMm]?)', tok)
        if not m:
            continue
        unit = m.group(2) or ('R' if i + 1 < len(toks) and toks[i + 1] == 'R' else '')
        if unit or '.' in m.group(1):
            return float(m.group(1).replace(',', '.')) * {'': 1.0, 'r': 1.0, 'k': 1e3, 'm': 1e6}[unit.lower()]
    return None


def exemption_role(board, spec, graph, ref, number, lookup, classes):
    """(role, why) of pad ref.number for the exemption policy (W2 PWR-L6-SCRIPT): from the ref prefix, the graph value and
    footprint, the pin name and the nets of the part's other pads. MODEL classification; the spec says why it is used."""
    comp = (graph or {}).get(ref) or {}
    value = str(comp.get('value', ''))
    fp = next((f for f in board.footprints if f['ref'] == ref), None)
    lib = (comp.get('footprint') or (fp or {}).get('lib') or '')
    pins = {str(p.get('number')): p for p in comp.get('pins', [])}
    name = str((pins.get(str(number)) or {}).get('name') or '').upper()
    up = value.upper()
    pads = [p for p in board.pads if p['ref'] == ref]
    mine = [p for p in pads if p['number'] == str(number)]
    net = mine[0]['net'] if mine else (pins.get(str(number)) or {}).get('net')
    other_nets = sorted({p['net'] for p in pads if p['number'] != str(number) and p['net']})

    def power(n):
        return n and classes.get(lookup(n)[1], {}).get('kind') == 'power'
    b2b = {e.get('ref') for e in spec.get('b2b', []) if isinstance(e, dict)}
    if ref.startswith('TP'):
        return 'test_point', 'test point (no load current)'
    if re.match(r'F\d', ref):
        return 'fuse', 'fuse in the power path'
    if ref in b2b:
        return 'b2b_contact', 'board-to-board mezzanine contact of the spec b2b pair'
    if re.match(r'(J|P|X|CN)\d', ref) or lib.startswith('Connector'):
        return 'connector', 'connector or harness land'
    if re.match(r'D\d', ref):
        if any(k in up for k in TVS_MARKERS) or 'TVS' in lib.upper():
            return 'tvs', 'TVS diode on the power net'
        return 'diode', 'diode in the power path'
    if re.match(r'Q\d', ref):
        return 'power_switch', 'power FET (switch node of the power path)'
    if re.match(r'L\d', ref) or re.match(r'FB\d', ref):
        return 'inductor', 'series inductor or bead of the power path'
    if re.match(r'R\d', ref):
        r = ohms_of(value)
        if r is None:
            return 'resistor_unknown', f'resistor of unread value {value!r}'
        if r < 1.0:
            return 'shunt', f'shunt / damper resistor {r:g} ohm in the power path'
        return ('resistor_ge_100', f'resistor {r:g} ohm (milliamperes)') if r >= 100.0 else \
            ('resistor_lt_100', f'resistor {r:g} ohm (below 100 ohm)')
    if re.match(r'C\d', ref):
        if other_nets and all(n != 'GND' and not power(n) for n in other_nets):
            return 'sense_logic_pin', f'capacitor from the power net to the signal net(s) {", ".join(other_nets)} (bootstrap, feed-forward, filter)'
        conv = any(p.get('net') in {net, *other_nets} and str(p.get('name', '')).upper() in CONVERTER_POWER_PINS
                   for c in (graph or {}).values() if re.match(r'U\d', c.get('ref', ''))
                   for p in c.get('pins', []) if p.get('net') and p.get('net') != 'GND')
        return ('converter_capacitor', 'input or output capacitor of a converter') if conv else \
            ('capacitor', 'decoupling or bulk capacitor on the power net')
    if re.match(r'U\d', ref):
        if any(k in up for k in EFUSE_MARKERS) and name in ('IN', 'OUT', 'VIN', 'VOUT'):
            return 'efuse_in_out', f'eFuse {name} pin'
        if any(k in up for k in LOAD_SWITCH_MARKERS) and name in ('IN', 'OUT', 'VIN', 'VOUT'):
            return 'power_switch', f'power-switch {name} pin'
        if name in SENSE_LOGIC_PINS:
            return 'sense_logic_pin', f'{name} pin (sense or logic, milliamperes)'
        if name in CONVERTER_POWER_PINS:
            return 'converter_power_pin', f'converter {name} pin'
        return 'ic_power_pin', f'IC pin {name or number} on the power net'
    return 'other', 'not classified'


def policy_neck_ok(role, pad, piece):
    """Neck rule of the exemption policy: not a forbidden role, at least the pad's narrow side wide, no longer than its long side."""
    if role in EXEMPT_NECK_FORBIDDEN:
        return False, f'no neck on a {role.replace("_", " ")}'
    s = piece.shape
    length = math.hypot(s.x2 - s.x1, s.y2 - s.y1)
    narrow, long_side = min(pad['w'], pad['h']), max(pad['w'], pad['h'])
    if piece.width + 1e-9 < narrow:
        return False, f'neck {r3(piece.width)} mm narrower than the pad ({r3(narrow)} mm)'
    if length > long_side + 1e-9:
        return False, f'neck {r3(length)} mm longer than the pad ({r3(long_side)} mm): a pin stem'
    return True, ''


def branch_exemptions(board, spec, netclasses, views, graph=None, policy_out=None):
    """branch_exempt {ref: {max_mm, min_width_mm, reason[, pads]}}: power-class track chains ending at that ref's pads (all of
    them, or only `pads`). With exemption_policy, a row whose start pads are not all allowed roles exempts nothing and is a
    finding in policy_out. Returns ({id(track item)}, {id(pad)}, unverified entries)."""
    lookup = class_map(netclasses, views)
    classes = netclasses.get('classes', {})
    tracks, pads, notes = set(), set(), []
    policy = spec.get('exemption_policy')
    for ref, rule in sorted(spec.get('branch_exempt', {}).items()):
        if not isinstance(rule, dict) or 'max_mm' not in rule or 'min_width_mm' not in rule:
            spec_error(spec, f'branch_exempt.{ref} needs max_mm, min_width_mm and reason')
        only = {str(n) for n in rule['pads']} if rule.get('pads') is not None else None
        mine = [p for p in board.pads if p['ref'] == ref and p['net'] and (only is None or p['number'] in only)]
        for bnet in sorted({p['net'] for p in mine}):
            gnet, cname = lookup(bnet)
            if classes.get(cname, {}).get('kind') != 'power':
                continue
            start = [p for p in mine if p['net'] == bnet]
            if policy is not None:
                roles = {p['number']: exemption_role(board, spec, graph, ref, p['number'], lookup, classes) for p in start}
                bad = {n: r for n, r in roles.items() if r[0] not in EXEMPT_BRANCH_ROLES}
                if bad:
                    if policy_out is not None:
                        n, (role, why) = sorted(bad.items())[0]
                        policy_out.append(finding('class_widths', f'{ref} branch on {gnet}',
                                                  f'exemption_policy: branch_exempt not allowed on {ref}.{n} ({role}: {why}); only '
                                                  f'{", ".join(EXEMPT_BRANCH_ROLES)}', at=(start[0]['x'], start[0]['y'])))
                    continue
            items, longest = track_chain(board, bnet, start, float(rule['max_mm']), lambda it: it.width + 1e-9 >= float(rule['min_width_mm']))
            tracks.update(id(it) for it in items)
            pads.update(id(p) for p in start)
            notes.append({'check': 'class_widths', 'item': f'{ref} branch on {gnet}',
                          'reason': f"branch_exempt: {len(items)} track piece(s), path {r3(longest)} mm <= {rule['max_mm']} mm, width >= {rule['min_width_mm']} mm "
                                    f"left out of the {cname} width and neck checks: {rule.get('reason', '')}"})
    return tracks, pads, notes


def check_classes(board, spec, netclasses, views, graph=None):
    out, unverified, info = [], [], {'tracks_checked': 0, 'pour_necks': [], 'split_nets': {}}
    lookup = class_map(netclasses, views)
    classes = netclasses.get('classes', {})
    outer = [l for l in ('F.Cu', 'B.Cu') if l in board.copper_layers]
    exempt = spec.get('neck_exempt', {})
    policy = spec.get('exemption_policy')
    branch_tracks, branch_pads, notes = branch_exemptions(board, spec, netclasses, views, graph=graph, policy_out=out)
    unverified.extend(notes)
    if policy is not None:
        info['exemption_policy'] = {'branch_roles': list(EXEMPT_BRANCH_ROLES), 'neck_forbidden_roles': list(EXEMPT_NECK_FORBIDDEN),
                                    'neck_rule': 'at least the narrow side of its pad wide, no longer than its long side',
                                    'branch_exempt': len(spec.get('branch_exempt', {})), 'neck_exempt': len(exempt)}
    role_cache = {}

    def role(p):
        key = (p['ref'], p['number'])
        if key not in role_cache:
            role_cache[key] = exemption_role(board, spec, graph, p['ref'], p['number'], lookup, classes)
        return role_cache[key]
    pads_by_net = collections.defaultdict(list)
    for p in board.pads:
        if p['net']:
            pads_by_net[p['net']].append(p)
    split_ok = set()
    for bnet in sorted({it.net for it in board.copper if it.net}):
        gnet, cname = lookup(bnet)
        layers = split_layers(spec, bnet, gnet)
        if not layers or classes.get(cname, {}).get('kind') != 'power':
            continue
        ok, why = check_split(board, bnet, [l for l in layers if l in board.copper_layers] or list(layers), skip=branch_tracks)
        info['split_nets'][gnet] = {'layers': list(layers), 'verified': ok, 'detail': why}
        if ok:
            split_ok.add(gnet)
        else:
            out.append(finding('class_widths', f'split {gnet}', f'split_nets declares {list(layers)} but {why}; '
                               f'checked at the single-layer width {classes[cname]["outer_min_width_mm"]} mm', layer=','.join(layers)))

    refused = []

    def escaped(it):
        # a pad-escape segment: both ends within escape_mm (+ half the pad) of a pad of an exempt ref on the same net; with
        # exemption_policy only where that pad's role and the piece's width and length allow a neck (policy_neck_ok)
        why_not = None
        for p in pads_by_net.get(it.net, []):
            e = exempt.get(p['ref'])
            if not e:
                continue
            lim = float(e.get('escape_mm', 0)) + max(p['w'], p['h']) / 2
            if all(math.hypot(px - p['x'], py - p['y']) <= lim for px, py in ((it.shape.x1, it.shape.y1), (it.shape.x2, it.shape.y2))):
                if policy is None:
                    return True
                r, rwhy = role(p)
                ok, why = policy_neck_ok(r, p, it)
                if ok:
                    return True
                why_not = why_not or f'{p["ref"]}.{p["number"]} ({r}: {rwhy}): {why}'
        if why_not:
            refused.append(why_not)
        return False
    noted = set()
    for it in board.tracks:
        if not it.net:
            continue
        gnet, cname = lookup(it.net)
        cls = classes.get(cname, {})
        if cname == 'RF50':
            continue
        if id(it) in branch_tracks:
            continue
        need, why = layer_requirement(cname, cls, it.layer, gnet, spec, outer, split_ok, it.net)
        info['tracks_checked'] += 1
        if need is None:
            if cls.get('kind') == 'power':
                # inner copper is not a current path for this class: a track there would carry the current in series
                out.append(finding('class_widths', f'{it.kind} {gnet}', f'{cname} track on {it.layer}: {why} (route it on {"/".join(outer)} or pour; '
                                   'low-current branches go in branch_exempt)', at=(it.shape.x1, it.shape.y1), value=it.width, layer=it.layer))
            continue
        if it.width + 1e-9 < need and not escaped(it):
            note = f'; exemption_policy refuses the neck at {refused.pop()}' if refused else ''
            out.append(finding('class_widths', f'{it.kind} {gnet}', f'{cname} copper narrower than {need} mm ({why}) on {it.layer}{note}',
                               at=(it.shape.x1, it.shape.y1), value=it.width, limit=need, layer=it.layer))
        refused.clear()
    by_net_layer = collections.defaultdict(list)
    for it in board.copper:
        if it.net and it.kind in ('zone', 'track', 'arc', 'pad', 'via') and id(it) not in branch_tracks:
            by_net_layer[(it.net, it.layer)].append(it)
    for (bnet, layer), items in sorted(by_net_layer.items(), key=lambda kv: kv[0]):
        zones = [it for it in items if it.kind == 'zone']
        if not zones:
            continue
        gnet, cname = lookup(bnet)
        cls = classes.get(cname, {})
        if cls.get('kind') != 'power':
            continue
        need, why = layer_requirement(cname, cls, layer, gnet, spec, outer, split_ok, bnet)
        if need is None:
            if (gnet, layer) not in noted:
                noted.add((gnet, layer))
                unverified.append({'check': 'class_widths', 'item': f'{gnet} pour on {layer}', 'reason': why})
            continue
        bx0 = min(z.shape.bbox[0] for z in zones) - 1.0
        by0 = min(z.shape.bbox[1] for z in zones) - 1.0
        bx1 = max(z.shape.bbox[2] for z in zones) + 1.0
        by1 = max(z.shape.bbox[3] for z in zones) + 1.0
        copper = [it for it in items if it.kind in ('zone', 'track', 'arc')]
        terms = [it.shape for it in items if it.kind in ('pad', 'via') and not (it.kind == 'pad' and id(it.extra) in branch_pads)
                 and not (it.shape.bbox[2] < bx0 or it.shape.bbox[0] > bx1 or it.shape.bbox[3] < by0 or it.shape.bbox[1] > by1)]
        # raster step: NECK_GRID, coarser for large pours so a region stays below NECK_MAX_CELLS (pure Python)
        grid = raster_grid((bx0, by0, bx1, by1))
        necks = raster_neck(copper, terms, (bx0, by0, bx1, by1), grid=grid, entry=need / 2)
        for width, x, y in necks:
            info['pour_necks'].append({'net': gnet, 'layer': layer, 'neck_mm': r3(width), 'limit_mm': need, 'grid_mm': grid, 'at': [r3(x), r3(y)]})
            if width + grid + 1e-9 < need:
                out.append(finding('class_widths', f'pour {gnet}', f'{cname} pour neck below {need} mm ({why}) on {layer} (raster +/-{grid} mm)',
                                   at=(x, y), value=width, limit=need, layer=layer))
    # vias_per_transition is a design value (netclasses.json): neither KiCad nor this checker counts vias per transition
    vias_by_net = collections.Counter(v['net'] for v in board.vias if v['net'])
    for bnet in sorted({it.net for it in board.copper if it.net}):
        gnet, cname = lookup(bnet)
        cls = classes.get(cname, {})
        if cls.get('kind') != 'power' or not (vias_by_net.get(bnet) or split_layers(spec, bnet, gnet)):
            continue
        unverified.append({'check': 'class_widths', 'item': f'{gnet} vias',
                           'reason': f"vias_per_transition {cls.get('vias_per_transition')} ({cname}) is advisory, not counted: "
                                     f"{vias_by_net.get(bnet, 0)} via(s) of the net on the board"})
    return out, unverified, info


def check_rf50(board, spec, netclasses, views):
    out, unverified = [], []
    lookup = class_map(netclasses, views)
    coupon_rf50 = {n for c in spec.get('coupons', []) for n in c.get('rf50_nets', [])}
    ground_of = {n: c.get('gnd_net', 'GND') for c in spec.get('coupons', []) for n in c.get('rf50_nets', [])}
    if coupon_rf50:  # coupon lines (board-only nets) are checked as RF50 lines too
        graph_lookup = lookup

        def lookup(bnet):
            return (bnet, 'RF50') if bnet in coupon_rf50 else graph_lookup(bnet)
    rf = netclasses.get('classes', {}).get('RF50')
    if not rf:
        return out, unverified, {'rf50_segments': 0}
    w, s, tol = rf['width_mm'], rf['gap_mm'], rf['width_tol_mm']
    ground_within = rf['coplanar_ground_within_mm']
    band = rf['l2_solid_band_mm']
    pitch, row = rf['fence_pitch_max_mm'], rf['fence_row_max_from_gap_mm']
    layers = board.by_layer()
    top = LayerIndex(layers.get('F.Cu', []))
    l2 = LayerIndex(layers.get('In1.Cu', []))
    vias_of = collections.defaultdict(list)
    for v in board.vias:
        vias_of[v['net']].append(v)
    segs = 0
    short = collections.Counter()
    exempt = spec.get('rf50_exempt', {})
    # rf50_taper {ref: {max_len_mm, min_width_mm, reason}}: narrower F.Cu pieces from that ref's pad (taper into a QFN pin)
    taper = set()
    for ref, rule in sorted(spec.get('rf50_taper', {}).items()):
        if not isinstance(rule, dict) or 'max_len_mm' not in rule or 'min_width_mm' not in rule:
            spec_error(spec, f'rf50_taper.{ref} needs max_len_mm, min_width_mm and reason')
        lo = float(rule['min_width_mm'])
        mine = [p for p in board.pads if p['ref'] == ref and p['net']]
        for bnet in sorted({p['net'] for p in mine}):
            gnet, cname = lookup(bnet)
            if cname != 'RF50':
                continue
            items, longest = track_chain(board, bnet, [p for p in mine if p['net'] == bnet], float(rule['max_len_mm']),
                                         lambda it: it.layer == 'F.Cu' and lo - 1e-9 <= it.width < w - tol - 1e-9)
            taper.update(id(it) for it in items)
            unverified.append({'check': 'rf50', 'item': f'{ref} taper on {gnet}',
                               'reason': f"rf50_taper: {len(items)} piece(s), path {r3(longest)} mm <= {rule['max_len_mm']} mm, width {lo}-{w} mm, "
                                         f"left out of the width and CPWG gap/ground/L2/fence checks: {rule.get('reason', '')}"})
    noted_exempt = set()
    for it in board.tracks:
        if not it.net:
            continue
        gnet, cname = lookup(it.net)
        if cname != 'RF50':
            continue
        if it.layer != 'F.Cu':
            out.append(finding('rf50', f'{gnet}', 'RF50 copper off L1 (F.Cu)', at=(it.shape.x1, it.shape.y1), layer=it.layer))
            continue
        segs += 1
        if id(it) in taper:
            continue
        if abs(it.width - w) > tol + 1e-9:
            out.append(finding('rf50', f'{gnet}', 'RF50 width outside tolerance', at=(it.shape.x1, it.shape.y1), value=it.width, limit=w))
        x1, y1, x2, y2 = it.shape.x1, it.shape.y1, it.shape.x2, it.shape.y2
        L = math.hypot(x2 - x1, y2 - y1)
        if L == 0:
            continue
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx_, ny_ = -uy, ux
        end_ex = w / 2 + s + 0.2
        ts = [end_ex + k * 0.1 for k in range(int(max(0.0, L - 2 * end_ex) / 0.1) + 1)] if L > 2 * end_ex else []
        if not ts:
            short[gnet] += 1
        if gnet in exempt:
            if gnet not in noted_exempt:
                noted_exempt.add(gnet)
                unverified.append({'check': 'rf50', 'item': gnet, 'reason': 'exempt from coplanar/L2/fence checks: ' + str(exempt[gnet])})
            continue
        gap_bad = ground_bad = l2_bad = 0
        first = {}
        gnd = ground_of.get(it.net, 'GND')
        gnd_vias = vias_of.get(gnd, [])
        for t in ts:
            px, py = x1 + ux * t, y1 + uy * t
            for side in (1, -1):
                for d in (w / 2 + 0.02, w / 2 + s / 2, w / 2 + s - 0.02):
                    qx, qy = px + side * nx_ * d, py + side * ny_ * d
                    others = [c for c in top.at(qx, qy) if c.net != it.net]
                    if others:
                        gap_bad += 1
                        first.setdefault('gap', (qx, qy, others[0].net))
                d = w / 2 + ground_within
                qx, qy = px + side * nx_ * d, py + side * ny_ * d
                if not any(c.net == gnd for c in top.at(qx, qy)):
                    ground_bad += 1
                    first.setdefault('ground', (qx, qy))
            k = 0
            while True:
                d = -band + k * 0.1
                if d > band + 1e-9:
                    break
                qx, qy = px + nx_ * d, py + ny_ * d
                if not any(c.net == gnd for c in l2.at(qx, qy)):
                    l2_bad += 1
                    first.setdefault('l2', (qx, qy))
                k += 1
        if gap_bad:
            qx, qy, onet = first['gap']
            out.append(finding('rf50', gnet, f'other-net copper inside the {s} mm CPWG gap', at=(qx, qy), net=onet, samples=gap_bad))
        if ground_bad:
            qx, qy = first['ground']
            out.append(finding('rf50', gnet, f'no coplanar GND within {ground_within} mm of the trace edge', at=(qx, qy), samples=ground_bad))
        if l2_bad:
            qx, qy = first['l2']
            out.append(finding('rf50', gnet, f'In1.Cu GND void within {band} mm of the trace axis (3h band)', at=(qx, qy), samples=l2_bad))
        if ts:
            for side in (1, -1):
                proj = []
                for v in gnd_vias:
                    rx, ry = v['x'] - x1, v['y'] - y1
                    t = rx * ux + ry * uy
                    d = side * (rx * nx_ + ry * ny_)
                    if -pitch <= t <= L + pitch and w / 2 + s + v['size'] / 2 - 1e-9 <= d <= w / 2 + s + row + 1e-9:
                        proj.append(t)
                pts = sorted([0.0, L] + [t for t in proj if 0.0 < t < L])
                worst = max(b - a for a, b in zip(pts, pts[1:]))
                if worst > pitch + 1e-9:
                    out.append(finding('rf50', gnet, f'GND fence gap above {pitch} mm on one side', at=(x1, y1), value=worst, limit=pitch))
    for gnet, count in sorted(short.items()):
        unverified.append({'check': 'rf50', 'item': gnet, 'reason': f'{count} RF50 segment(s) shorter than 2 x (w/2 + s + 0.2) mm (bends, arc pieces, pad entries) not sampled for gap/L2/fence'})
    return out, unverified, {'rf50_segments': segs}


def check_ties(board, spec, graph, views, frame=None):
    ties = []
    for fp in board.footprints:
        nets = {p['net'] for p in fp['pads']}
        if 'GND' in nets and 'CHASSIS' in nets:
            ties.append(fp['ref'])
    if 'gnd_chassis_ties' in spec:
        want = int(spec['gnd_chassis_ties'])
    else:
        want = 0
        for _vid, ref_map, _nm in views:
            for g in ref_map.values():
                c = graph.get(g)
                if c and {p.get('net') for p in c['pins']} >= {'GND', 'CHASSIS'}:
                    want += 1
    out = []
    if len(ties) != want:
        out.append(finding('gnd_chassis_ties', 'board', f'{len(ties)} GND-CHASSIS tie(s), expected exactly {want}', value=len(ties), limit=want, refs=sorted(ties)))
    info = {'ties': sorted(ties), 'expected': want}
    bond = spec.get('bond_hole')
    if bond and ties and frame is not None:  # W2 PCB-RF-2: each tie reaches the BOND-RF hole land through bond-net copper
        info.update(tie_on_bond_hole(board, bond, frame.to_board(*bond['at']), ties, out))
    return out, info


def seg_seg_dist(a, b, c, d):
    """Distance between the segments ab and cd (0 where they cross or touch)."""
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    if orient(a, b, c) * orient(a, b, d) < 0 and orient(c, d, a) * orient(c, d, b) < 0:
        return 0.0
    return min(seg_dist(c[0], c[1], a[0], a[1], b[0], b[1]), seg_dist(d[0], d[1], a[0], a[1], b[0], b[1]),
               seg_dist(a[0], a[1], c[0], c[1], d[0], d[1]), seg_dist(b[0], b[1], c[0], c[1], d[0], d[1]))


def shape_gap(a, b):
    """Edge-to-edge distance between two copper shapes (Poly, Capsule, Multi); 0 where they overlap."""
    if isinstance(a, Multi):
        return min(shape_gap(s, b) for s in a.shapes)
    if isinstance(b, Multi):
        return min(shape_gap(a, s) for s in b.shapes)
    if isinstance(a, Capsule) and isinstance(b, Capsule):
        return max(0.0, seg_seg_dist((a.x1, a.y1), (a.x2, a.y2), (b.x1, b.y1), (b.x2, b.y2)) - a.r - b.r)
    if isinstance(a, Capsule):
        a, b = b, a
    if isinstance(b, Capsule):  # a is a Poly
        if a.contains(b.x1, b.y1) or a.contains(b.x2, b.y2):
            return 0.0
        return max(0.0, min(seg_seg_dist(p, q, (b.x1, b.y1), (b.x2, b.y2)) for p, q in a.edges) - b.r)
    if a.contains(*b.pts[0]) or b.contains(*a.pts[0]):
        return 0.0
    return min(seg_seg_dist(p, q, r, s) for p, q in a.edges for r, s in b.edges)


def net_islands(board, net):
    """Connected pieces of the copper of one net: items on one layer join where they touch, a pad or via joins its
    own layers. Returns (items, {id(item): island number})."""
    items = [it for it in board.copper if it.net == net]
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def join(i, j):
        parent[find(i)] = find(j)
    owner = {}
    for i, it in enumerate(items):
        if it.kind in ('pad', 'via'):
            k = id(it.extra)
            if k in owner:
                join(i, owner[k])
            owner[k] = i
    for i, a in enumerate(items):
        ax0, ay0, ax1, ay1 = a.shape.bbox
        for j in range(i + 1, len(items)):
            b = items[j]
            bx0, by0, bx1, by1 = b.shape.bbox
            if a.layer != b.layer or ax1 < bx0 or bx1 < ax0 or ay1 < by0 or by1 < ay0:
                continue
            if find(i) != find(j) and shape_gap(a.shape, b.shape) <= 1e-6:
                join(i, j)
    roots = {}
    return items, {id(it): roots.setdefault(find(i), len(roots)) for i, it in enumerate(items)}


def tie_on_bond_hole(board, bond, bond_at, ties, out):
    """Each GND-CHASSIS tie reaches the plated bond hole (at bond_at, board mm) through copper of the bond net (W2 PCB-RF-2)."""
    net = bond.get('net')
    hole = next((h for h in board.holes if h['plated'] and math.hypot(h['x'] - bond_at[0], h['y'] - bond_at[1]) <= POS_TOL + 1e-9), None)
    items, island = net_islands(board, net)
    hole_islands = {island[id(it)] for it in items if hole and it.kind == 'pad' and (it.ref, it.pad) == (hole['ref'], hole['pad'])}
    on_hole = []
    for ref in sorted(ties):
        mine = {island[id(it)] for it in items if it.kind == 'pad' and it.ref == ref}
        if mine & hole_islands:
            on_hole.append(ref)
        else:
            out.append(finding('gnd_chassis_ties', ref, f'GND-CHASSIS tie does not reach the bond hole through {net} copper',
                               contract_at=bond['at'], hole=(hole or {}).get('ref')))
    return {'bond_net_islands': len(set(island.values())), 'ties_on_bond_hole': on_hole}


RF_CHECK_KEYS = ('why', 'taps', 'tap_caps', 'keepout', 'sense')


def rf_check_spec(spec):
    """rf_checks {why, taps [{ref, pad, max_mm}], tap_caps [{ref, to: [ref, pad], max_mm}], keepout {domains [...],
    margin_mm, refs [...]}, sense {nets [...], prototype <review json>}} (W2 PCB-RF-2); a bad shape stops."""
    rc = spec['rf_checks']
    extra = sorted(set(rc) - set(RF_CHECK_KEYS))
    if extra:
        spec_error(spec, f'rf_checks: unknown keys {extra}')
    for n, t in enumerate(rc.get('taps', [])):
        if not isinstance(t, dict) or not t.get('ref') or not t.get('pad') or not isinstance(t.get('max_mm'), (int, float)):
            spec_error(spec, f'rf_checks.taps[{n}] needs ref, pad and max_mm')
    for n, t in enumerate(rc.get('tap_caps', [])):
        if (not isinstance(t, dict) or not t.get('ref') or not isinstance(t.get('to'), list) or len(t['to']) != 2
                or not isinstance(t.get('max_mm'), (int, float))):
            spec_error(spec, f'rf_checks.tap_caps[{n}] needs ref, to [ref, pad] and max_mm')
    ko = rc.get('keepout')
    if ko is not None and (not isinstance(ko, dict) or not isinstance(ko.get('domains'), list) or not ko['domains']
                           or not isinstance(ko.get('margin_mm'), (int, float)) or not isinstance(ko.get('refs'), list)):
        spec_error(spec, 'rf_checks.keepout needs domains [...], margin_mm and refs [...]')
    se = rc.get('sense')
    if se is not None and (not isinstance(se, dict) or not isinstance(se.get('nets'), list) or not se['nets']
                           or not isinstance(se.get('prototype'), str)):
        spec_error(spec, 'rf_checks.sense needs nets [...] and prototype (a routed prototype review json)')
    return rc


def check_rf_nodes(board, spec, netclasses, views, frame, components_csv=None):
    """rf_checks (W2 PCB-RF-2) on the routed board: DC tap resistors on their RF50 line, their first capacitor next to
    the tap's far pad, parts outside a domain keepout box, and SENSE copper not longer than the routed prototype's."""
    rc = rf_check_spec(spec)
    out, info = [], {}
    pads = {(p['ref'], p['number']): p for p in board.pads}
    fps = {fp['ref']: fp for fp in board.footprints if fp['ref']}
    lookup = class_map(netclasses, views)
    rf = netclasses.get('classes', {}).get('RF50') or {}
    w, tol = rf.get('width_mm'), rf.get('width_tol_mm', 0.0)
    taps = {}
    for t in rc.get('taps', []):
        item = f"{t['ref']}.{t['pad']}"
        p = pads.get((t['ref'], str(t['pad'])))
        if p is None or not p['net']:
            out.append(finding('rf_nodes', item, 'tap pad not on the board or without a net'))
            continue
        gnet, cname = lookup(p['net'])
        lines = [it for it in board.tracks if it.net == p['net'] and it.layer in p['layers']
                 and w is not None and abs(it.width - w) <= tol + 1e-9]
        if cname != 'RF50' or not lines:
            out.append(finding('rf_nodes', item, 'tap pad net is not an RF50 line with RF50-width copper on the pad layer', net=gnet, net_class=cname))
            continue
        d = min(shape_gap(p['geo'], it.shape) for it in lines)
        taps[item] = {'net': gnet, 'to_rf50_line_mm': r3(d), 'max_mm': t['max_mm']}
        if d > t['max_mm'] + 1e-9:
            out.append(finding('rf_nodes', item, 'tap pad farther from its RF50 line than allowed', at=(p['x'], p['y']), value=d, limit=t['max_mm']))
    if 'taps' in rc:
        info['taps'] = taps
    caps = {}
    for t in rc.get('tap_caps', []):
        to = pads.get((t['to'][0], str(t['to'][1])))
        item = f"{t['ref']} to {t['to'][0]}.{t['to'][1]}"
        mine = [p for p in fps.get(t['ref'], {}).get('pads', []) if to is not None and to['net'] and p['net'] == to['net']]
        if not mine:
            out.append(finding('rf_nodes', item, 'no pad of this part on the net of the target pad', net=(to or {}).get('net')))
            continue
        d = min(shape_gap(p['geo'], to['geo']) for p in mine)
        caps[item] = {'net': lookup(to['net'])[0], 'pad_gap_mm': r3(d), 'max_mm': t['max_mm']}
        if d > t['max_mm'] + 1e-9:
            out.append(finding('rf_nodes', item, 'capacitor pad farther from the tap pad than allowed', at=(to['x'], to['y']), value=d, limit=t['max_mm']))
    if 'tap_caps' in rc:
        info['tap_caps'] = caps
    ko = rc.get('keepout')
    if ko is not None:
        if components_csv is None:
            with COMPONENTS.open(encoding='utf-8', newline='') as fh:
                components_csv = list(csv.DictReader(fh))
        in_domain = {r['ref'] for r in components_csv if r['board_candidate'] in set(ko['domains'])}
        members = sorted({bref for _v, ref_map, _n in views for bref, gref in ref_map.items() if gref in in_domain and bref in fps})

        def box(fp):
            if fp['courtyard']:
                return fp['courtyard']
            bb = [p['geo'].bbox for p in fp['pads']]
            return (min(b[0] for b in bb), min(b[1] for b in bb), max(b[2] for b in bb), max(b[3] for b in bb))
        gap = float(ko['margin_mm'])
        if not members:
            out.append(finding('rf_nodes', 'keepout', f"no footprint of the domains {ko['domains']} on the board"))
        else:
            boxes = [box(fps[r]) for r in members]
            kb = (min(b[0] for b in boxes) - gap, min(b[1] for b in boxes) - gap, max(b[2] for b in boxes) + gap, max(b[3] for b in boxes) + gap)
            clear = {}
            for ref in ko['refs']:
                fp = fps.get(ref)
                if fp is None:
                    out.append(finding('rf_nodes', ref, 'keepout part not on the board'))
                    continue
                b = box(fp)
                dx, dy = max(kb[0] - b[2], b[0] - kb[2], 0.0), max(kb[1] - b[3], b[1] - kb[3], 0.0)
                clear[ref] = r3(math.hypot(dx, dy))
                if dx <= 0 and dy <= 0:
                    out.append(finding('rf_nodes', ref, f"part inside the {'/'.join(ko['domains'])} keepout (courtyards + {gap} mm)",
                                       contract_at=frame.to_contract(fp['x'], fp['y'])))
            c0, c1 = frame.to_contract(kb[0], kb[1]), frame.to_contract(kb[2], kb[3])
            info['keepout'] = {'domains': ko['domains'], 'domain_parts': len(members), 'margin_mm': gap,
                               'box_contract': [r3(min(c0[0], c1[0])), r3(min(c0[1], c1[1])), r3(max(c0[0], c1[0])), r3(max(c0[1], c1[1]))],
                               'min_clearance_mm': min(clear.values()) if clear else None, 'parts': len(clear)}
    se = rc.get('sense')
    if se is not None:
        path = ROOT / se['prototype']
        proto = collections.Counter()
        if path.is_file():
            for s in read_json(path).get('routing', []):
                proto[s['net']] += float(s['length_mm'])
        lengths = {}
        for net in se['nets']:
            L = sum(math.hypot(it.shape.x2 - it.shape.x1, it.shape.y2 - it.shape.y1) for it in board.tracks if it.net == net)
            lengths[net] = {'board_mm': r3(L), 'prototype_mm': r3(proto[net]) if net in proto else None}
            if net not in proto:
                out.append(finding('rf_nodes', net, f"SENSE net not in the prototype routing ({se['prototype']})"))
            elif not 0 < L <= proto[net] + 1e-6:
                out.append(finding('rf_nodes', net, 'SENSE copper missing or longer than in the routed prototype', value=L, limit=proto[net]))
        info['sense'] = {'prototype': se['prototype'], 'nets': lengths}
    return out, info


def pin_nets(board, ref):
    fp = next((f for f in board.footprints if f['ref'] == ref), None)
    if fp is None:
        return None
    return {p['number']: p['net'] for p in fp['pads'] if p['kind'] != 'np_thru_hole'}


def check_b2b(board, spec, mates):
    out = []
    for pair in spec.get('b2b', []):
        mine = pin_nets(board, pair['ref'])
        mate = mates.get(pair['mate_board'])
        if mine is None:
            out.append(finding('b2b', pair['ref'], 'B2B connector not on this board'))
            continue
        if mate is None:
            out.append(finding('b2b', pair['ref'], f"mate board {pair['mate_board']} not available"))
            continue
        theirs = pin_nets(mate, pair['mate_ref'])
        if theirs is None:
            out.append(finding('b2b', pair['mate_ref'], f"mate connector not on {pair['mate_board']}"))
            continue
        pmap = pair.get('pin_map', 'identity')
        for pin in sorted(mine, key=lambda p: (len(p), p)):
            other = pin if pmap == 'identity' else pmap.get(pin)
            if other is None or other not in theirs:
                out.append(finding('b2b', f"{pair['ref']}.{pin}", f"no mating pin on {pair['mate_board']} {pair['mate_ref']}"))
            elif (mine[pin] or None) != (theirs[other] or None):
                out.append(finding('b2b', f"{pair['ref']}.{pin}", f"net differs from {pair['mate_board']} {pair['mate_ref']}.{other}",
                                   net=mine[pin], mate_net=theirs[other]))
        extra = set(theirs) - {(p if pmap == 'identity' else pmap.get(p)) for p in mine}
        for pin in sorted(extra):
            out.append(finding('b2b', f"{pair['mate_ref']}.{pin}", f"mate pin without a pin on {pair['ref']}"))
    return out, {'pairs': len(spec.get('b2b', []))}


def check_tht_pockets(board, spec, frame):
    out = []
    pockets = spec.get('tht_pockets')
    if pockets is None:
        return out, {'applies': False}
    margin = float(spec['tht_pocket_margin_mm'])
    rects = [frame.rect(r) for r in pockets]
    mounting = mounting_refs(board, spec)
    n = pegs = 0
    for p in board.pads:
        # THT pads and the NPTH locating pegs of parts (both go through the board); mounting holes are left out
        if p['kind'] not in ('thru_hole', 'np_thru_hole') or p['ref'] in mounting:
            continue
        n += 1
        pegs += p['kind'] == 'np_thru_hole'
        what = 'THT pad' if p['kind'] == 'thru_hole' else 'NPTH peg'
        x0, y0, x1, y1 = p['geo'].bbox
        x0, y0, x1, y1 = x0 - margin, y0 - margin, x1 + margin, y1 + margin
        if not any(rx0 <= x0 and ry0 <= y0 and x1 <= rx1 and y1 <= ry1 for rx0, ry0, rx1, ry1 in rects):
            out.append(finding('tht_pockets', f"{p['ref']}.{p['number'] or 'NPTH'}", f'{what} (+{margin} mm) not inside a plate pocket', contract_at=frame.to_contract(p['x'], p['y'])))
    return out, {'applies': True, 'tht_pads': n, 'npth_pegs': pegs, 'pockets': len(rects)}


def fp_height(fp, spec):
    h = spec.get('heights', {}).get(fp['ref'])
    if h is None:
        for key in ('Height', 'Height_mm', 'height'):
            if key in fp['props']:
                try:
                    h = float(re.sub(r'[^0-9.]', '', fp['props'][key]))
                except ValueError:
                    h = None
    return h


def check_heights(board, spec, cb, frame):
    out, unverified = [], []
    sides = set(spec.get('sides', ['top']))
    zones = []
    for z in spec.get('height_zones', []):
        rect = (-math.inf, -math.inf, math.inf, math.inf) if z.get('board') else frame.rect(z['rect'])
        if 'max_height' in z:
            zmax = float(z['max_height'])
        else:
            zmax = cb.get(z['max_height_from_contract'])
            if not isinstance(zmax, (int, float)):
                spec_error(spec, f"height_zones: the contract board has no numeric {z['max_height_from_contract']!r}")
        zones.append((rect, float(zmax), z.get('side', 'top')))
    default = {'top': cb.get('max_component_height'), 'bottom': spec.get('max_height_bottom')}
    mounting = mounting_refs(board, spec)
    checked = 0
    for fp in board.footprints:
        if not fp['ref'] or fp['ref'] in mounting or not fp['pads']:
            continue
        if fp['side'] not in sides:
            out.append(finding('heights', fp['ref'], f"part on the {fp['side']} side; spec sides {sorted(sides)}"))
            continue
        box = fp['courtyard'] or (min(p['geo'].bbox[0] for p in fp['pads']), min(p['geo'].bbox[1] for p in fp['pads']),
                                  max(p['geo'].bbox[2] for p in fp['pads']), max(p['geo'].bbox[3] for p in fp['pads']))
        limits = []
        inside_any = False
        for (zx0, zy0, zx1, zy1), zmax, zside in zones:
            if zside != fp['side']:
                continue
            overlap = not (box[2] <= zx0 or box[0] >= zx1 or box[3] <= zy0 or box[1] >= zy1)
            inside = zx0 <= box[0] and zy0 <= box[1] and box[2] <= zx1 and box[3] <= zy1
            if inside:
                limits.append(zmax)
                inside_any = True
            elif overlap:
                limits.append(zmax)
        if not inside_any and default.get(fp['side']) is not None:
            limits.append(float(default[fp['side']]))
        if not limits:
            unverified.append({'check': 'heights', 'item': fp['ref'], 'reason': f"no height limit for the {fp['side']} side"})
            continue
        limit = min(limits)
        h = fp_height(fp, spec)
        if h is None:
            unverified.append({'check': 'heights', 'item': fp['ref'], 'reason': f'height unknown (spec heights or footprint property Height); limit {limit} mm'})
            continue
        checked += 1
        if h > limit + 1e-9:
            out.append(finding('heights', fp['ref'], 'part taller than its height zone', contract_at=frame.to_contract(fp['x'], fp['y']), value=h, limit=limit))
    return out, unverified, {'checked': checked}


def annular_floor(board, netclasses):
    """(mm, fab_floor key): the JLC PTH annular-ring absolute minimum for the board's copper layer count."""
    key = 'jlc_4l_1oz' if len(board.copper_layers) > 2 else 'jlc_2l_1oz'
    return float(netclasses['fab_floor'][key]['pth_annular_min']), key


def check_annular(board, netclasses):
    out = []
    floor, key = annular_floor(board, netclasses)
    for p in board.pads:
        if p['kind'] != 'thru_hole' or not p['drill']:
            continue
        if len(p['drill']) >= 2:  # (drill oval dx dy)
            ring = min((p['w'] - p['drill'][0]) / 2, (p['h'] - p['drill'][1]) / 2)
        else:
            ring = (min(p['w'], p['h']) - p['drill'][0]) / 2
        if ring + 1e-9 < floor:
            out.append(finding('pth_annular', f"{p['ref']}.{p['number']}", f'PTH annular ring below the JLC absolute minimum ({key})', at=(p['x'], p['y']), value=ring, limit=floor))
    return out, {'floor_mm': floor, 'fab_floor': key}


# ------------------------------------------------------------------ review
def projections(board, spec, cb, graph, views, netclasses):
    refs = {}
    for vid, ref_map, net_map in views:
        for bref, gref in sorted(ref_map.items()):
            c = graph.get(gref)
            refs[f'{vid}:{bref}'] = {'graph_ref': gref, 'footprint': (c or {}).get('footprint', ''),
                                     'pins': {str(p['number']): p.get('net') for p in (c or {}).get('pins', [])}}
    board_nets = sorted({it.net for it in board.copper if it.net})
    lookup = class_map(netclasses, views)
    used = {n: lookup(n) for n in board_nets}
    cls_names = sorted({c for _g, c in used.values()})
    keys = set(CONTRACT_KEYS) | {z['max_height_from_contract'] for z in spec.get('height_zones', []) if 'max_height_from_contract' in z}
    return {
        'graph_refs_pins_nets': sha_text(canon({'views': [[v, rm, nm] for v, rm, nm in views], 'refs': refs})),
        'footprints': sha_text(canon({k: v['footprint'] for k, v in refs.items()})),
        'contract_board': sha_text(canon({k: cb.get(k) for k in sorted(keys)})),
        'netclasses': sha_text(canon({'nets': used, 'classes': {c: netclasses.get('classes', {}).get(c) for c in cls_names}})),
        'spec': sha_text(canon(spec)),
    }


def contract_path(spec):
    return ROOT / spec['contract_file'] if spec.get('contract_file') else CONTRACT


def board_netclasses(netclasses, spec):
    """The net classes a board is checked against (W2 PWRJ-LAYERS6): a spec whose layers name a copper_option of
    pcb/generated/stackup-6l.json (e.g. outer_2oz: 2 oz outer / 0.5 oz inner copper) takes that option's power-class
    widths; every other board keeps pcb/generated/netclasses.json unchanged."""
    option = spec.get('copper_option')
    if not option:
        return netclasses
    doc = read_json(STACKUP_6L)
    opt = (doc.get('copper_options') or {}).get(option)
    if opt is None or spec.get('board_id') not in opt.get('boards', []):
        raise SystemExit(f'check_boards: {spec.get("board_id")}: copper_option {option!r} is not in {STACKUP_6L.name} for this board')
    out = {**netclasses, 'classes': {k: dict(v) for k, v in netclasses.get('classes', {}).items()}}
    for name, widths in opt['power_classes'].items():
        out['classes'][name].update({k: widths[k] for k in ('outer_min_width_mm', 'outer_ipc_width_mm',
                                                           'split_outer_per_layer_mm', 'inner_min_width_mm')})
        out['classes'][name]['basis'] = widths['basis'] + f' (copper_option {option}, {STACKUP_6L.name})'
    # W2 PWR-L6-PLACE fourth pass, combined: the PWR1A sub-classes of the option (inner_classes, e.g. PWR05A: the PWR1A nets
    # limited to <=0.339 A / <=0.499 A at their own IPC-2221 inner width) take their member nets on this board
    inner = opt.get('inner_classes') or {}
    if inner:
        out['nets'] = dict(out.get('nets', {}))
        for name, cls in inner.items():
            out['classes'][name] = {k: v for k, v in cls.items() if k != 'nets'}
            out['classes'][name]['basis'] = cls['basis'] + f' (copper_option {option}, {STACKUP_6L.name})'
            for net in cls['nets']:
                if net in out['nets']:
                    out['nets'][net] = {**out['nets'][net], 'class': name}
    return out


def review_board(board, spec, contract, graph, netclasses, mates=None, components_csv=None, board_rel=None):
    spec = normalize_spec(spec)
    netclasses = board_netclasses(netclasses, spec)
    bid = spec['board_id']
    cb = contract['boards'].get(spec.get('contract_board', bid))
    if cb is None:
        raise SystemExit(f'check_boards: {bid}: contract board {spec.get("contract_board", bid)} not in {contract_path(spec).name}')
    frame = Frame(board, cb, spec)
    views = expected_views(spec, graph, components_csv)
    findings, unverified, checks = [], [], collections.OrderedDict()

    def run(name, result):
        f = result[0]
        if len(result) == 3:
            unverified.extend(result[1])
            info = result[2]
        else:
            info = result[1]
        findings.extend(f)
        checks[name] = {'findings': len(f), **info}
    run('outline', check_outline(board, cb, frame, spec))
    run('holes', check_holes(board, cb, frame, spec))
    run('keepouts', check_keepouts(board, cb, frame, spec))
    if 'planned_cutouts' in spec:  # W2 PWRB-R: only specs with planned_cutouts (every other review stays unchanged)
        run('planned_cutouts', check_planned_cutouts(board, frame, spec))
    run('pad_nets', check_pad_nets(board, spec, graph, views))
    run('class_widths', check_classes(board, spec, netclasses, views, graph))
    run('rf50', check_rf50(board, spec, netclasses, views))
    run('gnd_chassis_ties', check_ties(board, spec, graph, views, frame))
    if 'rf_checks' in spec:
        run('rf_nodes', check_rf_nodes(board, spec, netclasses, views, frame, components_csv))
    run('b2b', check_b2b(board, spec, mates or {}))
    run('tht_pockets', check_tht_pockets(board, spec, frame))
    run('heights', check_heights(board, spec, cb, frame))
    run('pth_annular', check_annular(board, netclasses))
    unverified.extend(board.unverified)
    return {
        'schema': 'srrx-board-review-v1',
        'board_id': bid,
        'status': STATUS,
        'generator': 'pcb/check_boards.py',
        'result': 'NO_FINDINGS' if not findings else 'FINDINGS',
        'inputs': {
            'board_file': {'path': board_rel or (board.path.as_posix() if board.path else ''), 'sha256': sha_file(board.path) if board.path else None},
            'projection_sha256': projections(board, spec, cb, graph, views, netclasses),
            'note': 'projections of refs/pins/nets, footprints, the contract keys read, the classes used and the checker view of the spec (F10); the board file itself is hashed whole',
        },
        'frame': {'origin': [r3(frame.ox), r3(frame.oy)], 'y': 'up' if frame.yup else 'down', 'source': frame.source},
        'counts': {'footprints': len(board.footprints), 'pads': len(board.pads), 'tracks': len(board.tracks), 'vias': len(board.vias),
                   'zones': len(board.zones), 'holes': len(board.holes), 'copper_layers': board.copper_layers},
        'checks': checks,
        'findings': findings,
        'unverified': unverified,
    }


def dumps(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2) + '\n'


def spec_paths():
    if not BOARDS_DIR.is_dir():
        return []
    out = []
    for p in sorted(BOARDS_DIR.glob('*.json')):
        try:
            if 'board_id' in read_json(p):
                out.append(p)
        except (ValueError, OSError):
            continue
    return out


def board_file(spec):
    if spec.get('board_file'):
        return ROOT / spec['board_file']
    return OUT_DIR / spec['board_id'] / f"{spec['board_id']}.kicad_pcb"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--board', help='board id (pcb/boards/<B>.json)')
    g.add_argument('--all', action='store_true', help='every pcb/boards/*.json with a board_id')
    ap.add_argument('--check', action='store_true', help='compare with the committed review.json, write nothing')
    args = ap.parse_args(argv)
    specs = spec_paths() if args.all else [BOARDS_DIR / f'{args.board}.json']
    netclasses, graph = read_json(NETCLASSES), load_graph()
    contracts = {}
    loaded = {}
    for p in specs:
        if not p.is_file():
            raise SystemExit(f'check_boards: no spec {p.relative_to(ROOT).as_posix()}')
        spec = normalize_spec(read_json(p))
        bf = board_file(spec)
        loaded[spec['board_id']] = (spec, bf, load_board(bf) if bf.is_file() else None)
    if not loaded:
        print('check_boards: 0 boards (no pcb/boards/*.json with a board_id yet)')
        return 0
    bad = []
    for bid, (spec, bf, board) in loaded.items():
        if board is None:
            print(f'check_boards: {bid}: no board file {bf.relative_to(ROOT).as_posix()} yet, skipped')
            continue
        mates = {}
        for pair in spec.get('b2b', []):
            m = pair['mate_board']
            if m in loaded:
                mates[m] = loaded[m][2]
            else:
                mp = BOARDS_DIR / f'{m}.json'
                if mp.is_file():
                    mbf = board_file(normalize_spec(read_json(mp)))
                    if mbf.is_file():
                        mates[m] = load_board(mbf)
        cpath = contract_path(spec)
        if cpath not in contracts:
            if not cpath.is_file():
                raise SystemExit(f'check_boards: {bid}: no contract file {cpath}')
            contracts[cpath] = read_json(cpath)
        doc = review_board(board, spec, contracts[cpath], graph, netclasses, mates, board_rel=bf.relative_to(ROOT).as_posix())
        text = dumps(doc)
        out = OUT_DIR / bid / 'review.json'
        if args.check:
            if not out.is_file() or out.read_text(encoding='utf-8') != text:
                bad.append(f'{bid}: review.json stale (rerun python pcb/check_boards.py --board {bid})')
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding='utf-8', newline='\n')
        print(f"check_boards: {bid}: {len(doc['findings'])} finding(s), {len(doc['unverified'])} unverified")
        for f in doc['findings'][:20]:
            print('  ', json.dumps(f, ensure_ascii=False))
        if doc['findings']:
            bad.append(f"{bid}: {len(doc['findings'])} finding(s)")
    if bad:
        print('check_boards: FAIL: ' + '; '.join(bad), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
