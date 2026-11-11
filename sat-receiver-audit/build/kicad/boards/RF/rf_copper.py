"""Scripted GND vias, RF50 pad entries and the impedance coupon of the RF board (W2 PCB-RF-2; imported by rf_layout.py).

Standard library only. Everything here is geometry in board mm (contract outline, y up, top view), checked against
the same clearances the KiCad project uses (rf_layout.CLEAR): a via is placed only where it keeps its class clearance
to every pad, scripted track, hole keepout and footprint keepout of another net, 0.75 mm centre to centre to every
other drilled hole (min_hole_to_hole 0.45 + the 0.3 drill) and 0.3 mm copper to the board edge. CI/model geometry;
no bench gate is closed by it.
"""
from __future__ import annotations

import collections
import math

VIA_D, VIA_DRILL = 0.6, 0.3          # project via (RF.kicad_pro min_via_diameter / min_through_hole_diameter)
VIA_R = VIA_D / 2
HOLE_PITCH = 0.75                    # via centre to drilled-hole centre: min_hole_to_hole 0.45 + 0.3 drill
EDGE_CU = 0.3                        # RF.kicad_pro min_copper_edge_clearance
EPAD_EDGE = 0.01                     # an exposed-pad via keeps its copper this far inside the pad (epad_vias)
TRIM_IN = 0.2                        # an RF50 end stays this far inside its pad (pad entry, see trim_pad_entries)
# RF50 fence (pcb/generated/netclasses.json RF50: width 0.36, gap 0.20, fence pitch <= 2.0, row <= 1.0 from the gap):
# the band for a fence via centre is w/2 + s + via r = 0.68 to w/2 + s + 1.0 = 1.38 from the trace axis.
FENCE_LAT = (0.9, 0.8, 1.0, 1.15, 0.72, 1.3)
FENCE_STEP = 1.0
GND = 'GND'


def seg_point(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def seg_seg(a, b, c, d):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if o1 * o2 < 0 and o3 * o4 < 0:
        return 0.0
    return min(seg_point(c, a, b), seg_point(d, a, b), seg_point(a, c, d), seg_point(b, c, d))


def box_point(box, p):
    x0, y0, x1, y1 = box
    dx = max(x0 - p[0], 0.0, p[0] - x1)
    dy = max(y0 - p[1], 0.0, p[1] - y1)
    return math.hypot(dx, dy)


def seg_box(a, b, box):
    x0, y0, x1, y1 = box

    def inside(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    if inside(a) or inside(b):
        return 0.0
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    for c, d in zip(corners, corners[1:] + corners[:1]):
        if seg_seg(a, b, c, d) == 0.0:
            return 0.0
    return min([seg_point(c, a, b) for c in corners] + [box_point(box, a), box_point(box, b)])


def inside(box, p, eps=1e-9):
    return box[0] - eps <= p[0] <= box[2] + eps and box[1] - eps <= p[1] <= box[3] + eps


def ray_exit(p, u, box):
    """Distance from p (inside box) along unit u to the box boundary."""
    best = math.inf
    for k, (lo, hi) in enumerate(((box[0], box[2]), (box[1], box[3]))):
        if abs(u[k]) > 1e-12:
            t = ((hi if u[k] > 0 else lo) - p[k]) / u[k]
            best = min(best, t)
    return best


class Grid:
    """Bucketed items for neighbourhood queries (2 mm cells)."""
    CELL = 2.0

    def __init__(self):
        self.cells = collections.defaultdict(list)

    def add(self, box, item):
        c = self.CELL
        for gx in range(int(math.floor(box[0] / c)), int(math.floor(box[2] / c)) + 1):
            for gy in range(int(math.floor(box[1] / c)), int(math.floor(box[3] / c)) + 1):
                self.cells[(gx, gy)].append(item)

    def near(self, p, r):
        c = self.CELL
        seen, out = set(), []
        for gx in range(int(math.floor((p[0] - r) / c)), int(math.floor((p[0] + r) / c)) + 1):
            for gy in range(int(math.floor((p[1] - r) / c)), int(math.floor((p[1] + r) / c)) + 1):
                for it in self.cells.get((gx, gy), ()):
                    if id(it) not in seen:
                        seen.add(id(it))
                        out.append(it)
        return out


class Copper:
    """Obstacles of one region (the board or one coupon) and the vias placed in it."""

    def __init__(self, region, pads, tracks, clear, holes=(), bond=None, keepouts=()):
        self.region = region             # [x0, y0, x1, y1] board mm (outline box)
        self.clear = clear               # net -> clearance mm
        self.pads, self.tracks, self.vias = Grid(), Grid(), Grid()
        self.pad_list, self.via_list = list(pads), []
        for p in self.pad_list:
            self.pads.add(p['box'], p)
        self.segs = []
        for t in tracks:
            for a, b in zip(t['path'], t['path'][1:]):
                s = {'a': tuple(a), 'b': tuple(b), 'w': t['width_mm'], 'net': t['net']}
                self.segs.append(s)
                w = t['width_mm'] / 2
                self.tracks.add([min(a[0], b[0]) - w, min(a[1], b[1]) - w, max(a[0], b[0]) + w, max(a[1], b[1]) + w], s)
        self.holes = list(holes)         # [(centre, keepout radius)]: NPTH rule-area keepouts (vias blocked)
        self.bond = bond                 # (centre, land radius, net) or None
        self.keepouts = list(keepouts)   # boxes where footprint keepout zones block vias and tracks

    def add_track(self, t):
        for a, b in zip(t['path'], t['path'][1:]):
            s = {'a': tuple(a), 'b': tuple(b), 'w': t['width_mm'], 'net': t['net']}
            self.segs.append(s)
            w = t['width_mm'] / 2
            self.tracks.add([min(a[0], b[0]) - w, min(a[1], b[1]) - w, max(a[0], b[0]) + w, max(a[1], b[1]) + w], s)

    def cl(self, net):
        return self.clear(net)

    def via_ok(self, p, net=GND, allow=()):
        x, y = p
        x0, y0, x1, y1 = self.region
        m = EDGE_CU + VIA_R
        if not (x0 + m <= x <= x1 - m and y0 + m <= y <= y1 - m):
            return False
        for c, r in self.holes:
            if math.hypot(x - c[0], y - c[1]) < r + VIA_R + 0.01:
                return False
        if self.bond and math.hypot(x - self.bond[0][0], y - self.bond[0][1]) < self.bond[1] + VIA_R + self.cl(self.bond[2]):
            return False
        for k in self.keepouts:
            if box_point(k, p) < VIA_R + 0.05:
                return False
        for pd in self.pads.near(p, 3.0):
            if any(pd is a for a in allow):
                continue
            d = box_point(pd['box'], p)
            need = VIA_R + (self.cl(pd['net']) if pd['net'] != net else 0.15)
            if d < need - 1e-9:
                return False
            if pd.get('drill') and math.hypot(x - pd['center'][0], y - pd['center'][1]) < pd['drill'] / 2 + VIA_DRILL / 2 + 0.45:
                return False
        for s in self.tracks.near(p, 3.0):
            if s['net'] == net:
                continue
            if seg_point(p, s['a'], s['b']) - s['w'] / 2 < VIA_R + self.cl(s['net']) - 1e-9:
                return False
        for v in self.vias.near(p, 2.0):
            if math.hypot(x - v['at'][0], y - v['at'][1]) < HOLE_PITCH - 1e-9:
                return False
        return True

    def track_ok(self, a, b, w, net=GND, allow=()):
        for k in self.keepouts:
            if seg_box(a, b, k) < w / 2 + 0.01:
                return False
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        r = math.hypot(b[0] - a[0], b[1] - a[1]) / 2 + 2.0
        for pd in self.pads.near(mid, r):
            if pd['net'] == net or any(pd is x for x in allow):
                continue
            if seg_box(a, b, pd['box']) < w / 2 + self.cl(pd['net']) - 1e-9:
                return False
        for s in self.tracks.near(mid, r):
            if s['net'] == net:
                continue
            if seg_seg(a, b, s['a'], s['b']) < (w + s['w']) / 2 + max(self.cl(net), self.cl(s['net'])) - 1e-9:
                return False
        return True

    def add_via(self, p, why, net=GND):
        v = {'id': f'V{len(self.via_list) + 1}', 'net': net, 'at': [round(p[0], 4), round(p[1], 4)],
             'diameter_mm': VIA_D, 'drill_mm': VIA_DRILL, 'locked': True, 'why': why}
        self.via_list.append(v)
        self.vias.add([p[0] - VIA_R, p[1] - VIA_R, p[0] + VIA_R, p[1] + VIA_R], v)
        return v


# ----------------------------------------------------------------------------------------------- pad entries
def trim_pad_entries(tracks, pads, is_rf50, rf_w):
    """RF50 lines end TRIM_IN inside their pads instead of at the pad centres, and pass-through pads split a line.

    A trace that runs on top of a wider pad has no CPWG gap or coplanar ground there (the pad is the line), so the line
    ends just inside the pad edge, the pad joins the pieces (KiCad: a track end inside a pad is connected), and the
    sampled length of every RF50 segment starts outside its pads (pcb/check_boards.py samples from w/2 + s + 0.2 of
    each segment end). The HMC7992 pin tapers (narrower than RF50) are kept as they are (rf50_taper).
    """
    by_net = collections.defaultdict(list)
    for p in pads:
        if p['net']:
            by_net[p['net']].append(p)
    out = []
    for t in tracks:
        if not is_rf50(t['net']) or abs(t['width_mm'] - rf_w) > 1e-6:
            out.append(t)
            continue
        own = by_net.get(t['net'], [])
        pieces = [[tuple(t['path'][0])]]
        for v in t['path'][1:-1]:
            pieces[-1].append(tuple(v))
            if any(math.hypot(v[0] - p['center'][0], v[1] - p['center'][1]) < 1e-4 for p in own):
                pieces.append([tuple(v)])
        pieces[-1].append(tuple(t['path'][-1]))
        for path in pieces:
            path = [list(p) for p in path]
            for end, nxt in ((0, 1), (len(path) - 1, len(path) - 2)):
                e, o = path[end], path[nxt]
                L = math.hypot(o[0] - e[0], o[1] - e[1])
                if L < 1e-9:
                    continue
                u = ((o[0] - e[0]) / L, (o[1] - e[1]) / L)
                for p in own:
                    if inside(p['box'], e):
                        move = ray_exit(e, u, p['box']) - TRIM_IN
                        if 0.05 < move < L - 0.3:
                            path[end] = [round(e[0] + u[0] * move, 4), round(e[1] + u[1] * move, 4)]
                        break
            out.append(dict(t, path=[[round(x, 4), round(y, 4)] for x, y in path]))
    count = collections.Counter()
    for t in out:
        count[t['net']] += 1
        t['id'] = f'{t["net"]}-{count[t["net"]]}'
    return out


# ----------------------------------------------------------------------------------------------- vias
def epad_vias(cu, parts):
    """GND vias inside exposed pads. STACK.md:299 asks for >= 5 vias in the HMC7992 EPAD: where five fit, the centre
    and four corner vias, the corners as far out as the via copper stays EPAD_EDGE inside the pad, kept only when the
    corner-to-centre pitch is HOLE_PITCH or more (the 1.7 mm HMC7992 pad: +/-0.54 mm, pitch 0.764 mm); else 2 x 2 at
    +/-0.425 mm in a pad of 1.5 mm or more, one at the centre of a smaller one. Project choice: the ADI HMC7992 land
    pattern was not readable (2026-11-07, 2026-11-11), see epad_vias_source in the spec."""
    out = []
    for ref, pad in parts:
        (cx, cy), (w, h) = pad['center'], (pad['box'][2] - pad['box'][0], pad['box'][3] - pad['box'][1])
        off = round(min(w, h) / 2 - VIA_R - EPAD_EDGE, 4)
        if off * math.sqrt(2) >= HOLE_PITCH - 1e-9:
            pts = [(cx, cy)] + [(cx + dx, cy + dy) for dx in (-off, off) for dy in (-off, off)]
        elif min(w, h) >= 1.5:
            pts = [(cx + dx, cy + dy) for dx in (-0.425, 0.425) for dy in (-0.425, 0.425)]
        else:
            pts = [(cx, cy)]
        for p in pts:
            if cu.via_ok(p, allow=(pad,)):
                out.append(cu.add_via(p, f'{ref} exposed pad to the In1.Cu GND plane'))
    return out


def inward_stub(cu, pin, epad, width):
    """Short GND track from a QFN GND pin to its exposed pad, when it clears the neighbouring pins."""
    a = tuple(pin['center'])
    c = tuple(epad['center'])
    # along the pin axis towards the package centre, ending inside the exposed pad
    dx, dy = c[0] - a[0], c[1] - a[1]
    if abs(dx) > abs(dy):
        b = (epad['box'][0] + 0.1 if dx > 0 else epad['box'][2] - 0.1, a[1])
    else:
        b = (a[0], epad['box'][1] + 0.1 if dy > 0 else epad['box'][3] - 0.1)
    if not inside(epad['box'], b) or not cu.track_ok(a, b, width, allow=(pin, epad)):
        return None
    t = {'net': GND, 'layer': 'F.Cu', 'width_mm': width, 'path': [[round(a[0], 4), round(a[1], 4)], [round(b[0], 4), round(b[1], 4)]],
         'locked': True, 'why': 'QFN GND pin to its exposed pad (scripted, locked)'}
    cu.add_track(t)
    return t


def fanout(cu, pad, centre_of_part, width=0.3, net=GND, why=None):
    """One via of the pad's net next to an SMD pad with a short stub; None when nothing fits.

    Of the positions that clear everything (8 directions, 3 distances), the one with the least foreign copper within
    1.5 mm wins (a fan-out via in front of a QFN pin row blocks the router there, route run 42421969829: U407.7), then
    the shorter stub, then outward from the part.
    """
    cx, cy = pad['center']
    hx, hy = (pad['box'][2] - pad['box'][0]) / 2, (pad['box'][3] - pad['box'][1]) / 2
    ox, oy = cx - centre_of_part[0], cy - centre_of_part[1]
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (0.7071, 0.7071), (-0.7071, 0.7071), (0.7071, -0.7071), (-0.7071, -0.7071)]
    dirs.sort(key=lambda d: (-(d[0] * ox + d[1] * oy), d))
    w = min(width, 2 * min(hx, hy))
    best = None
    for k, extra in enumerate((0.05, 0.3, 0.6)):
        for j, (ux, uy) in enumerate(dirs):
            reach = min(hx / abs(ux) if ux else math.inf, hy / abs(uy) if uy else math.inf)
            d = reach + VIA_R + extra
            p = (cx + ux * d, cy + uy * d)
            if not cu.via_ok(p, net, allow=(pad,)):
                continue
            if not cu.track_ok((cx, cy), p, w, net, allow=(pad,)):
                continue
            crowd = sum(max(0.0, 1.5 - box_point(q['box'], p)) for q in cu.pads.near(p, 2.0)
                        if q['net'] != net and q is not pad)
            key = (round(crowd, 3), k, j)
            if best is None or key < best[0]:
                best = (key, p)
    if best is None:
        return None
    p = best[1]
    t = {'net': net, 'layer': 'F.Cu', 'width_mm': round(w, 4),
         'path': [[round(cx, 4), round(cy, 4)], [round(p[0], 4), round(p[1], 4)]], 'locked': True,
         'why': why or 'GND pad fan-out to its via (scripted, locked; the router does not route GND)'}
    cu.add_track(t)
    v = cu.add_via(p, f'{pad["ref"]}.{pad["num"]} {net} fan-out', net)
    return t, v


def fences(cu, tracks, is_rf50, rf_w, why='RF50 GND fence', net=GND):
    """Ground vias (net) on both sides of every RF50 segment, about FENCE_STEP apart, in the fence band."""
    out = []
    for t in tracks:
        if not is_rf50(t['net']) or abs(t['width_mm'] - rf_w) > 1e-6:
            continue
        for a, b in zip(t['path'], t['path'][1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 1e-6:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            nx, ny = -uy, ux
            n = max(1, int(math.ceil(L / FENCE_STEP)))
            for side in (1, -1):
                for k in range(n + 1):
                    s = L * k / n
                    for lat in FENCE_LAT:
                        p = (a[0] + ux * s + side * nx * lat, a[1] + uy * s + side * ny * lat)
                        if cu.via_ok(p, net):
                            out.append(cu.add_via(p, f'{why} {t["net"]}', net))
                            break
    return out


def ring(cu, box, step=1.2, why='GND via ring'):
    x0, y0, x1, y1 = box
    out = []
    per = 2 * ((x1 - x0) + (y1 - y0))
    n = int(per / step)
    for k in range(n):
        s = per * k / n
        if s < x1 - x0:
            p = (x0 + s, y0)
        elif s < (x1 - x0) + (y1 - y0):
            p = (x1, y0 + s - (x1 - x0))
        elif s < 2 * (x1 - x0) + (y1 - y0):
            p = (x1 - (s - (x1 - x0) - (y1 - y0)), y1)
        else:
            p = (x0, y1 - (s - 2 * (x1 - x0) - (y1 - y0)))
        if cu.via_ok(p):
            out.append(cu.add_via(p, why))
    return out


def stitch(cu, boxes, pitch=3.5, margin=0.25, why='GND stitching of the four GND layers'):
    """Grid of GND vias outside every courtyard (+margin), so the router keeps its room between the parts."""
    x0, y0, x1, y1 = cu.region
    out = []
    y = y0 + 1.5
    while y < y1 - 1.0:
        x = x0 + 1.5
        while x < x1 - 1.0:
            p = (round(x, 4), round(y, 4))
            if not any(b[0] - margin <= p[0] <= b[2] + margin and b[1] - margin <= p[1] <= b[3] + margin for b in boxes) \
                    and cu.via_ok(p):
                out.append(cu.add_via(p, why))
            x += pitch
        y += pitch
    return out


def fence_gaps(vias, tracks, is_rf50, rf_w, w=0.36, s=0.2, pitch=2.0, row=1.0):
    """The pcb/check_boards.py RF50 fence rule on the scripted geometry: [(net, a, b, side, worst gap mm)]."""
    bad = []
    lo, hi = w / 2 + s + VIA_R, w / 2 + s + row
    end_ex = w / 2 + s + 0.2
    for t in tracks:
        if not is_rf50(t['net']) or abs(t['width_mm'] - rf_w) > 1e-6:
            continue
        for a, b in zip(t['path'], t['path'][1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L <= 2 * end_ex:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            for side in (1, -1):
                proj = []
                for v in vias:
                    rx, ry = v['at'][0] - a[0], v['at'][1] - a[1]
                    tt = rx * ux + ry * uy
                    d = side * (-rx * uy + ry * ux)
                    if -pitch <= tt <= L + pitch and lo - 1e-9 <= d <= hi + 1e-9:
                        proj.append(tt)
                pts = sorted([0.0, L] + [x for x in proj if 0.0 < x < L])
                worst = max(q - p for p, q in zip(pts, pts[1:]))
                if worst > pitch + 1e-9:
                    bad.append((t['net'], a, b, side, round(worst, 3)))
    return bad
