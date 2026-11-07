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
the BOND-RF hole's own net, the count of GND-CHASSIS ties, B2B pin-for-pin nets between two boards, THT pads
over plate pockets and component heights against the height zones. Review hashes are projections (board refs,
pins, nets, footprints, contract, classes), not whole input files, so an unrelated parts.json or graph edit does
not stale a review (F10). Results are MODEL checks of the drawn copper; they prove no hardware gate.

Spec fields read from pcb/boards/<B>.json (all optional except board_id):
  board_id, board_file (default build/kicad/boards/<B>/<B>.kicad_pcb), contract_board (default board_id),
  refs | domains (graph refs on the board; domains use pcb/generated/components.csv board_candidate),
  board_only_refs {ref: reason}, instances [{id, ref_map {board_ref: graph_ref}, net_map {board_net: graph_net}}],
  contract_transform {origin: [x, y] (KiCad position of contract (0, 0)), y: "up"|"down"} (default: y up, origin
  from the Edge.Cuts bounding box), bond_hole {at: [x, y], net}, gnd_chassis_ties (default: graph ties on the board),
  split_nets {net: ["F.Cu", "B.Cu"]}, neck_exempt {ref: {escape_mm, reason}}, rf50_exempt {net: reason},
  b2b [{ref, mate_board, mate_ref, pin_map: "identity" | {pin: mate_pin}}],
  tht_pockets [[x, y, w, h], ...] + tht_pocket_margin_mm (contract frame), height_zones [{rect, max_height, side}],
  heights {ref: mm}, sides ["top"] (default top only), max_height_bottom.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import csv
import hashlib
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
COMPONENTS = ROOT / 'pcb/generated/components.csv'
GRAPHS = [ROOT / f'design/E{i}.json' for i in range(1, 6)]
STATUS = 'MODEL_CHECK: drawn copper against contract, graphs and net classes (pure-Python reader); not a fabrication release; bench gates OPEN'
NECK_GRID = 0.05     # mm raster for pour necks; a measured neck passes within one cell of its limit
NECK_MAX_CELLS = 600_000  # larger pours use a coarser step (recorded per neck as grid_mm)
POS_TOL = 0.01       # mm outline vertex / hole position tolerance
HOLE_D_TOL = 0.01    # mm hole diameter tolerance
PTH_ANNULAR_FLOOR = 0.15  # mm, JLC multilayer 1 oz absolute minimum (netclasses.json fab_floor)


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
        angle = float(at[3]) if len(at) > 3 else fa
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
        rec = {'ref': fp['ref'], 'number': number, 'kind': kind, 'shape': shape, 'x': x, 'y': y, 'w': w, 'h': h, 'angle': angle,
               'drill': dvals, 'net': net, 'layers': layers, 'geo': geo, 'fp': fp}
        fp['pads'].append(rec)
        self.pads.append(rec)
        for lay in layers:
            self.copper.append(Item('pad', net, lay, geo, ref=fp['ref'], pad=number, extra=rec))
        if kind == 'np_thru_hole' or (kind == 'thru_hole' and (re.fullmatch(r'HB?\d*', fp['ref'] or '') or 'MountingHole' in fp['lib'])):
            d = dvals[0] if dvals else 0.0
            self.holes.append({'x': x, 'y': y, 'd': d, 'plated': kind == 'thru_hole', 'net': net, 'ref': fp['ref'], 'pad': number})

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


def check_outline(board, cb, frame):
    out = []
    lps, open_chains = loops(board.edges)
    if open_chains or not lps:
        out.append(finding('outline', 'Edge.Cuts', f'outline not closed ({open_chains} open chain(s), {len(lps)} loop(s))'))
        return out, {}
    lps = [simplify(lp) for lp in lps]
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
    return out, {'area_mm2': r3(area), 'loops': len(lps)}


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
            if it.shape.dist(cx, cy) >= r - 1e-9:
                continue
            if hole_pad and it.kind == 'pad' and (it.ref, it.pad) == hole_pad:
                continue
            if is_bond and it.net is not None and it.net == bond.get('net'):
                continue
            what = f'{it.kind} {it.ref}.{it.pad}' if it.kind == 'pad' else it.kind
            out.append(finding('keepouts', what, f'copper inside the hole keepout (d {2 * r} mm)', contract_at=frame.to_contract(cx, cy),
                               net=it.net, layer=it.layer, distance=it.shape.dist(cx, cy)))
    return out, {'keepout_r_mm': r}


def expected_views(spec, graph, components_csv=None):
    """[(view id, ref_map board->graph, net_map board->graph)] and the graph refs the board must carry."""
    if spec.get('instances'):
        views = [(i.get('id', str(n)), dict(i.get('ref_map', {})), dict(i.get('net_map', {}))) for n, i in enumerate(spec['instances'])]
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


def layer_requirement(cls_name, cls, layer, net, spec, outer_layers):
    """(required width mm, note) for copper of a class net on a layer; None when the layer is not counted."""
    if cls.get('kind') == 'power':
        if layer in outer_layers:
            split = spec.get('split_nets', {}).get(net)
            if split and cls.get('split_outer_per_layer_mm') and set(split) >= set(outer_layers) and layer in split:
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


def check_classes(board, spec, netclasses, views):
    out, unverified, info = [], [], {'tracks_checked': 0, 'pour_necks': []}
    lookup = class_map(netclasses, views)
    classes = netclasses.get('classes', {})
    outer = [l for l in ('F.Cu', 'B.Cu') if l in board.copper_layers]
    exempt = spec.get('neck_exempt', {})
    pads_by_net = collections.defaultdict(list)
    for p in board.pads:
        if p['net']:
            pads_by_net[p['net']].append(p)

    def escaped(it):
        # a pad-escape segment: both ends within escape_mm (+ half the pad) of a pad of an exempt ref on the same net
        for p in pads_by_net.get(it.net, []):
            e = exempt.get(p['ref'])
            if not e:
                continue
            lim = float(e.get('escape_mm', 0)) + max(p['w'], p['h']) / 2
            if all(math.hypot(px - p['x'], py - p['y']) <= lim for px, py in ((it.shape.x1, it.shape.y1), (it.shape.x2, it.shape.y2))):
                return True
        return False
    noted = set()
    for it in board.tracks:
        if not it.net:
            continue
        gnet, cname = lookup(it.net)
        cls = classes.get(cname, {})
        if cname == 'RF50':
            continue
        need, why = layer_requirement(cname, cls, it.layer, gnet, spec, outer)
        info['tracks_checked'] += 1
        if need is None:
            if (gnet, it.layer) not in noted and cls.get('kind') == 'power':
                noted.add((gnet, it.layer))
                unverified.append({'check': 'class_widths', 'item': f'{gnet} on {it.layer}', 'reason': why})
            continue
        if it.width + 1e-9 < need and not escaped(it):
            out.append(finding('class_widths', f'{it.kind} {gnet}', f'{cname} copper narrower than {need} mm ({why}) on {it.layer}',
                               at=(it.shape.x1, it.shape.y1), value=it.width, limit=need, layer=it.layer))
    by_net_layer = collections.defaultdict(list)
    for it in board.copper:
        if it.net and it.kind in ('zone', 'track', 'arc', 'pad', 'via'):
            by_net_layer[(it.net, it.layer)].append(it)
    for (bnet, layer), items in sorted(by_net_layer.items(), key=lambda kv: kv[0]):
        zones = [it for it in items if it.kind == 'zone']
        if not zones:
            continue
        gnet, cname = lookup(bnet)
        cls = classes.get(cname, {})
        if cls.get('kind') != 'power':
            continue
        need, why = layer_requirement(cname, cls, layer, gnet, spec, outer)
        if need is None:
            unverified.append({'check': 'class_widths', 'item': f'{gnet} pour on {layer}', 'reason': why})
            continue
        bx0 = min(z.shape.bbox[0] for z in zones) - 1.0
        by0 = min(z.shape.bbox[1] for z in zones) - 1.0
        bx1 = max(z.shape.bbox[2] for z in zones) + 1.0
        by1 = max(z.shape.bbox[3] for z in zones) + 1.0
        copper = [it for it in items if it.kind in ('zone', 'track', 'arc')]
        terms = [it.shape for it in items if it.kind in ('pad', 'via') and not (it.shape.bbox[2] < bx0 or it.shape.bbox[0] > bx1 or it.shape.bbox[3] < by0 or it.shape.bbox[1] > by1)]
        # raster step: NECK_GRID, coarser for large pours so a region stays below NECK_MAX_CELLS (pure Python)
        grid = max(NECK_GRID, math.ceil(math.sqrt((bx1 - bx0) * (by1 - by0) / NECK_MAX_CELLS) * 100) / 100)
        necks = raster_neck(copper, terms, (bx0, by0, bx1, by1), grid=grid, entry=need / 2)
        for width, x, y in necks:
            info['pour_necks'].append({'net': gnet, 'layer': layer, 'neck_mm': r3(width), 'limit_mm': need, 'grid_mm': grid, 'at': [r3(x), r3(y)]})
            if width + grid + 1e-9 < need:
                out.append(finding('class_widths', f'pour {gnet}', f'{cname} pour neck below {need} mm ({why}) on {layer} (raster +/-{grid} mm)',
                                   at=(x, y), value=width, limit=need, layer=layer))
    return out, unverified, info


def check_rf50(board, spec, netclasses, views):
    out, unverified = [], []
    lookup = class_map(netclasses, views)
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
    gnd_vias = [v for v in board.vias if v['net'] == 'GND']
    segs = 0
    short = collections.Counter()
    exempt = spec.get('rf50_exempt', {})
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
            unverified.append({'check': 'rf50', 'item': gnet, 'reason': 'exempt from coplanar/L2/fence checks: ' + str(exempt[gnet])})
            continue
        gap_bad = ground_bad = l2_bad = 0
        first = {}
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
                if not any(c.net == 'GND' for c in top.at(qx, qy)):
                    ground_bad += 1
                    first.setdefault('ground', (qx, qy))
            k = 0
            while True:
                d = -band + k * 0.1
                if d > band + 1e-9:
                    break
                qx, qy = px + nx_ * d, py + ny_ * d
                if not any(c.net == 'GND' for c in l2.at(qx, qy)):
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


def check_ties(board, spec, graph, views):
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
    return out, {'ties': sorted(ties), 'expected': want}


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
    hole_refs = {h['ref'] for h in board.holes}
    n = 0
    for p in board.pads:
        if p['kind'] != 'thru_hole' or p['ref'] in hole_refs:
            continue
        n += 1
        x0, y0, x1, y1 = p['geo'].bbox
        x0, y0, x1, y1 = x0 - margin, y0 - margin, x1 + margin, y1 + margin
        if not any(rx0 <= x0 and ry0 <= y0 and x1 <= rx1 and y1 <= ry1 for rx0, ry0, rx1, ry1 in rects):
            out.append(finding('tht_pockets', f"{p['ref']}.{p['number']}", f'THT pad (+{margin} mm) not inside a plate pocket', contract_at=frame.to_contract(p['x'], p['y'])))
    return out, {'applies': True, 'tht_pads': n, 'pockets': len(rects)}


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
    zones = [(frame.rect(z['rect']), float(z['max_height']), z.get('side', 'top')) for z in spec.get('height_zones', [])]
    default = {'top': cb.get('max_component_height'), 'bottom': spec.get('max_height_bottom')}
    hole_refs = {h['ref'] for h in board.holes}
    checked = 0
    for fp in board.footprints:
        if not fp['ref'] or fp['ref'] in hole_refs or not fp['pads']:
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


def check_annular(board):
    out = []
    for p in board.pads:
        if p['kind'] != 'thru_hole' or not p['drill']:
            continue
        if len(p['drill']) >= 2:  # (drill oval dx dy)
            ring = min((p['w'] - p['drill'][0]) / 2, (p['h'] - p['drill'][1]) / 2)
        else:
            ring = (min(p['w'], p['h']) - p['drill'][0]) / 2
        if ring + 1e-9 < PTH_ANNULAR_FLOOR:
            out.append(finding('pth_annular', f"{p['ref']}.{p['number']}", 'PTH annular ring below the JLC absolute minimum', at=(p['x'], p['y']), value=ring, limit=PTH_ANNULAR_FLOOR))
    return out, {}


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
    return {
        'graph_refs_pins_nets': sha_text(canon({'views': [[v, rm, nm] for v, rm, nm in views], 'refs': refs})),
        'footprints': sha_text(canon({k: v['footprint'] for k, v in refs.items()})),
        'contract_board': sha_text(canon(cb)),
        'netclasses': sha_text(canon({'nets': used, 'classes': {c: netclasses.get('classes', {}).get(c) for c in cls_names}})),
        'spec': sha_text(canon(spec)),
    }


def review_board(board, spec, contract, graph, netclasses, mates=None, components_csv=None, board_rel=None):
    bid = spec['board_id']
    cb = contract['boards'].get(spec.get('contract_board', bid))
    if cb is None:
        raise SystemExit(f'check_boards: contract board {spec.get("contract_board", bid)} not in {CONTRACT.relative_to(ROOT).as_posix()}')
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
    run('outline', check_outline(board, cb, frame))
    run('holes', check_holes(board, cb, frame, spec))
    run('keepouts', check_keepouts(board, cb, frame, spec))
    run('pad_nets', check_pad_nets(board, spec, graph, views))
    run('class_widths', check_classes(board, spec, netclasses, views))
    run('rf50', check_rf50(board, spec, netclasses, views))
    run('gnd_chassis_ties', check_ties(board, spec, graph, views))
    run('b2b', check_b2b(board, spec, mates or {}))
    run('tht_pockets', check_tht_pockets(board, spec, frame))
    run('heights', check_heights(board, spec, cb, frame))
    run('pth_annular', check_annular(board))
    return {
        'schema': 'srrx-board-review-v1',
        'board_id': bid,
        'status': STATUS,
        'generator': 'pcb/check_boards.py',
        'result': 'NO_FINDINGS' if not findings else 'FINDINGS',
        'inputs': {
            'board_file': {'path': board_rel or (board.path.as_posix() if board.path else ''), 'sha256': sha_file(board.path) if board.path else None},
            'projection_sha256': projections(board, spec, cb, graph, views, netclasses),
            'note': 'projections of refs/pins/nets, footprints, the contract entry, the classes used and the spec (F10); the board file itself is hashed whole',
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
    contract, netclasses, graph = read_json(CONTRACT), read_json(NETCLASSES), load_graph()
    loaded = {}
    for p in specs:
        if not p.is_file():
            raise SystemExit(f'check_boards: no spec {p.relative_to(ROOT).as_posix()}')
        spec = read_json(p)
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
                    mbf = board_file(read_json(mp))
                    if mbf.is_file():
                        mates[m] = load_board(mbf)
        doc = review_board(board, spec, contract, graph, netclasses, mates, board_rel=bf.relative_to(ROOT).as_posix())
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
