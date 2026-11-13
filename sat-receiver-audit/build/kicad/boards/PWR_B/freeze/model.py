"""Board model of a routed board for the frozen-route completion (W2 CTRL-R; KiCad mm, y down).

W2 PWRB-R: copied unchanged in function from build/kicad/boards/CTRL/freeze/model.py of origin/wip/w2-ctrl4-layers6 (W2 CTRL-4)
for the 6-layer PWR_B board; configure() switches the stackup, keepouts include the planned_cutouts rule areas.

Items: pads (exact check_boards shapes), track segments, vias, keepout polygons, edge segments.
Clearance checks of new copper, per-net connectivity (union-find), numpy rasters for a grid router.
"""
import sys, math, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'pcb'))
import check_boards as cb  # noqa: E402

LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
RLAYERS = ['F.Cu', 'In2.Cu', 'B.Cu']  # routing layers (In1.Cu is the GND plane)
PLANES = {'GND': 'In1.Cu'}  # net -> plane layer that joins every via and THT pad of the net


def configure(layers, planes):
    """W2 CTRL-4: switch the model to another stackup (the 6-layer CTRL board: GND plane In1.Cu, 3V3_Q6A plane In4.Cu). The
    lists are changed in place, so router.py and fin.py see them; the defaults above are the 4-layer board of W2 CTRL-R."""
    LAYERS[:] = list(layers)
    RLAYERS[:] = [l for l in layers if l not in planes.values()]
    PLANES.clear()
    PLANES.update(planes)
CLR = 0.15          # board clearance
EDGE_CLR = 0.30     # copper to edge
HOLE_HOLE = 0.50    # hole edge to hole edge
BUCKET = 1.0


def seg_dist(px, py, x1, y1, x2, y2):
    return cb.seg_dist(px, py, x1, y1, x2, y2)


def segseg(a, b, c, d):
    """Distance between segments ab and cd."""
    def inter(p1, p2, p3, p4):
        def orient(p, q, r):
            return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        o1, o2, o3, o4 = orient(p1, p2, p3), orient(p1, p2, p4), orient(p3, p4, p1), orient(p3, p4, p2)
        return (o1 * o2 < 0) and (o3 * o4 < 0)
    if inter(a, b, c, d):
        return 0.0
    return min(seg_dist(a[0], a[1], c[0], c[1], d[0], d[1]), seg_dist(b[0], b[1], c[0], c[1], d[0], d[1]),
               seg_dist(c[0], c[1], a[0], a[1], b[0], b[1]), seg_dist(d[0], d[1], a[0], a[1], b[0], b[1]))


def shape_seg_dist(shape, a, b):
    """Distance from segment ab (zero width) to a check_boards shape."""
    if isinstance(shape, cb.Capsule):
        return max(0.0, segseg(a, b, (shape.x1, shape.y1), (shape.x2, shape.y2)) - shape.r)
    if isinstance(shape, cb.Multi):
        return min(shape_seg_dist(s, a, b) for s in shape.shapes)
    if isinstance(shape, RoundRect):
        return max(0.0, shape_seg_dist(shape.inner, a, b) - shape.r)
    # polygon: zero if an end is inside or the segment crosses an edge
    if shape.contains(*a) or shape.contains(*b):
        return 0.0
    return min(segseg(a, b, e0, e1) for e0, e1 in shape.edges)


def translate(shape, dx, dy):
    if isinstance(shape, cb.Capsule):
        return cb.Capsule(shape.x1 + dx, shape.y1 + dy, shape.x2 + dx, shape.y2 + dy, shape.r)
    if isinstance(shape, cb.Multi):
        return cb.Multi([translate(s, dx, dy) for s in shape.shapes])
    return cb.Poly([(x + dx, y + dy) for x, y in shape.pts])


class RoundRect:
    """Rounded rectangle pad: the inner rectangle (w-2r, h-2r) grown by r (exact KiCad roundrect copper)."""

    def __init__(self, cx, cy, w, h, angle, r):
        self.inner = cb.Poly(cb.rect_pts(cx, cy, max(w - 2 * r, 1e-6), max(h - 2 * r, 1e-6), angle))
        self.r = r
        b = self.inner.bbox
        self.bbox = (b[0] - r, b[1] - r, b[2] + r, b[3] + r)
        self.pts = self.inner.pts
        self.edges = self.inner.edges

    def dist(self, x, y):
        return max(0.0, self.inner.dist(x, y) - self.r)

    def contains(self, x, y):
        return self.inner.dist(x, y) <= self.r


class Item:
    __slots__ = ('id', 'kind', 'net', 'layers', 'shape', 'bbox', 'locked', 'width', 'a', 'b', 'at', 'size', 'drill', 'ref', 'pad', 'src', 'alive')

    def __init__(self, **k):
        for s in self.__slots__:
            setattr(self, s, k.get(s))
        self.alive = True


class Model:
    def __init__(self, board_path):
        text = open(board_path, encoding='utf-8').read()
        self.b = cb.load_board(board_path)
        self.items = []
        self.grid = collections.defaultdict(list)  # (layer, ix, iy) -> item ids
        tree0 = cb.parse(text)
        self.offset_pads = 0
        for fnode, frec in zip(cb.kids(tree0, 'footprint'), self.b.footprints):
            for pnode, prec in zip(cb.kids(fnode, 'pad'), frec['pads']):
                assert str(pnode[1]) == prec['number']
                # KiCad PAD::ShapePos(): the copper is centred at the position plus the drill offset turned by the pad angle
                drill = cb.kid(pnode, 'drill')
                off = cb.kid(drill, 'offset') if isinstance(drill, list) else None
                dx = dy = 0.0
                if off is not None and (float(off[1]) or float(off[2])):
                    dx, dy = cb.rot(float(off[1]), float(off[2]), prec['angle'])
                    self.offset_pads += 1
                if prec['shape'] == 'roundrect':
                    rr = cb.kid(pnode, 'roundrect_rratio')
                    ratio = float(rr[1]) if rr else 0.25
                    prec['geo'] = RoundRect(prec['x'] + dx, prec['y'] + dy, prec['w'], prec['h'], prec['angle'], ratio * min(prec['w'], prec['h']))
                elif dx or dy:
                    prec['geo'] = translate(prec['geo'], dx, dy)
        for p in self.b.pads:
            kind = 'npth' if p['kind'] == 'np_thru_hole' else 'pad'
            lays = [l for l in p['layers'] if l in LAYERS] if kind == 'pad' else list(LAYERS)
            self.add(Item(kind=kind, net=p['net'] if kind == 'pad' else None, layers=lays, shape=p['geo'], ref=p['ref'], pad=p['number'],
                          at=(p['x'], p['y']), drill=(p['drill'][0] if p['drill'] else 0.0), locked=True, src='pad'))
        tree = cb.parse(text)
        for seg in cb.kids(tree, 'segment'):
            s, e = cb.kid(seg, 'start'), cb.kid(seg, 'end')
            w = float(cb.kid(seg, 'width')[1])
            lay = str(cb.kid(seg, 'layer')[1])
            net = self.b.net_of(seg)
            locked = cb.kid(seg, 'locked') is not None and str(cb.kid(seg, 'locked')[1]) == 'yes'
            a, bb = (float(s[1]), float(s[2])), (float(e[1]), float(e[2]))
            self.add_track(net, lay, w, a, bb, locked=locked, src='scripted' if locked else 'router')
        for v in cb.kids(tree, 'via'):
            at = cb.kid(v, 'at')
            locked = cb.kid(v, 'locked') is not None and str(cb.kid(v, 'locked')[1]) == 'yes'
            self.add_via(self.b.net_of(v), (float(at[1]), float(at[2])), float(cb.kid(v, 'size')[1]), float(cb.kid(v, 'drill')[1]),
                         locked=locked, src='scripted' if locked else 'router')
        self.keepouts = []
        for z in self.b.zones:
            if z['keepout'] and len(z['outline']) >= 3:
                self.keepouts.append({'layers': [l for l in z['layers'] if l in LAYERS], 'poly': cb.Poly(z['outline']), 'name': z['name']})
        # keepout zones inside footprints (the Pico TP7 pad keepouts): absolute board coordinates in the board file
        for fnode in cb.kids(tree0, 'footprint'):
            for z in cb.kids(fnode, 'zone'):
                if cb.kid(z, 'keepout') is None:
                    continue
                lay = cb.kid(z, 'layers') or cb.kid(z, 'layer')
                pts = [(float(q[1]), float(q[2])) for q in cb.kid(cb.kid(z, 'polygon'), 'pts')[1:] if isinstance(q, list) and q[0] == 'xy']
                name = cb.kid(z, 'name')
                if len(pts) >= 3:
                    self.keepouts.append({'layers': [str(l) for l in lay[1:] if str(l) in LAYERS], 'poly': cb.Poly(pts),
                                          'name': str(name[1]) if name else 'footprint keepout'})
        self.edges = [(tuple(a), tuple(c)) for a, c in self.b.edges]
        self.outline_loops = cb.loops(self.b.edges)

    # ---------------------------------------------------------------- items
    def add(self, it):
        it.id = len(self.items)
        it.bbox = it.shape.bbox
        self.items.append(it)
        x0, y0, x1, y1 = it.bbox
        for lay in it.layers:
            for ix in range(int(math.floor(x0 / BUCKET)), int(math.floor(x1 / BUCKET)) + 1):
                for iy in range(int(math.floor(y0 / BUCKET)), int(math.floor(y1 / BUCKET)) + 1):
                    self.grid[(lay, ix, iy)].append(it.id)
        return it

    def add_track(self, net, layer, width, a, b, locked=True, src='new'):
        return self.add(Item(kind='track', net=net, layers=[layer], shape=cb.Capsule(a[0], a[1], b[0], b[1], width / 2), width=width,
                             a=tuple(a), b=tuple(b), locked=locked, src=src))

    def add_via(self, net, at, size, drill, locked=True, src='new'):
        return self.add(Item(kind='via', net=net, layers=list(LAYERS), shape=cb.Capsule(at[0], at[1], at[0], at[1], size / 2), at=tuple(at),
                             size=size, drill=drill, locked=locked, src=src))

    def remove(self, it):
        it.alive = False

    def near(self, layer, bbox):
        x0, y0, x1, y1 = bbox
        seen = set()
        for ix in range(int(math.floor(x0 / BUCKET)), int(math.floor(x1 / BUCKET)) + 1):
            for iy in range(int(math.floor(y0 / BUCKET)), int(math.floor(y1 / BUCKET)) + 1):
                for i in self.grid.get((layer, ix, iy), ()):
                    if i not in seen:
                        seen.add(i)
                        it = self.items[i]
                        if it.alive:
                            yield it

    # ---------------------------------------------------------------- checks
    def edge_dist_seg(self, a, b):
        return min(segseg(a, b, e0, e1) for e0, e1 in self.edges)

    def inside(self, p):
        """Inside the outline and outside the cut-outs (even-odd over all edge loops)."""
        x, y = p
        c = 0
        for (x1, y1), (x2, y2) in self.edges:
            if (y1 > y) != (y2 > y):
                xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if xc > x:
                    c += 1
        return c % 2 == 1

    def track_margin(self, net, layer, width, a, b, clr=CLR, ignore=()):
        """Smallest margin (>= 0 is clear) of a new track against other-net copper, keepouts and edges."""
        r = width / 2
        bb = (min(a[0], b[0]) - r - 1.0, min(a[1], b[1]) - r - 1.0, max(a[0], b[0]) + r + 1.0, max(a[1], b[1]) + r + 1.0)
        worst, why = math.inf, None
        for it in self.near(layer, bb):
            if it.id in ignore:
                continue
            if it.kind != 'npth' and it.net == net and net is not None:
                continue
            extra = 0.1 if it.kind == 'npth' else 0.0
            m = shape_seg_dist(it.shape, a, b) - r - clr - extra
            if m < worst:
                worst, why = m, f'{it.kind} {it.net} {it.ref or ""}.{it.pad or ""} id{it.id}'
        for k in self.keepouts:
            if layer in k['layers']:
                kb = k['poly'].bbox
                if kb[0] > bb[2] or kb[2] < bb[0] or kb[1] > bb[3] or kb[3] < bb[1]:
                    continue
                m = shape_seg_dist(k['poly'], a, b) - r - 0.01
                if m < worst:
                    worst, why = m, 'keepout ' + k['name']
        m = self.edge_dist_seg(a, b) - r - EDGE_CLR - 0.02
        if m < worst:
            worst, why = m, 'edge'
        if not self.inside(a) or not self.inside(b):
            return -9.0, 'outside'
        return worst, why

    def via_margin(self, net, at, size=0.65, drill=0.3, clr=CLR, ignore=()):
        r = size / 2
        bb = (at[0] - r - 1.5, at[1] - r - 1.5, at[0] + r + 1.5, at[1] + r + 1.5)
        worst, why = math.inf, None
        seen = set()
        for lay in LAYERS:
            for it in self.near(lay, bb):
                if it.id in seen or it.id in ignore:
                    continue
                seen.add(it.id)
                # hole to hole (any net)
                if it.kind in ('via', 'npth') or (it.kind == 'pad' and it.drill):
                    d = math.hypot(at[0] - it.at[0], at[1] - it.at[1]) - drill / 2 - (it.drill or 0) / 2 - HOLE_HOLE - 0.02
                    if d < worst:
                        worst, why = d, f'hole {it.kind} {it.ref or ""}.{it.pad or ""} id{it.id}'
                if it.kind == 'npth':
                    continue
                if it.net == net:
                    if it.kind == 'pad' and not it.drill:
                        m = it.shape.dist(*at) - r - 0.02  # no via in an SMD pad
                        if m < worst:
                            worst, why = m, f'own pad {it.ref}.{it.pad}'
                    continue
                m = it.shape.dist(*at) - r - clr
                if m < worst:
                    worst, why = m, f'{it.kind} {it.net} {it.ref or ""}.{it.pad or ""} id{it.id}'
        for k in self.keepouts:
            kb = k['poly'].bbox
            if kb[0] > bb[2] or kb[2] < bb[0] or kb[1] > bb[3] or kb[3] < bb[1]:
                continue
            m = k['poly'].dist(*at) - r - 0.01
            if m < worst:
                worst, why = m, 'keepout ' + k['name']
        m = min(seg_dist(at[0], at[1], e0[0], e0[1], e1[0], e1[1]) for e0, e1 in self.edges) - r - EDGE_CLR - 0.02
        if m < worst:
            worst, why = m, 'edge'
        if not self.inside(at):
            return -9.0, 'outside'
        return worst, why

    # ---------------------------------------------------------------- connectivity
    def islands(self, net):
        """Connected groups of the net's copper (pads, tracks, vias); through vias and THT pads join layers."""
        its = [it for it in self.items if it.alive and it.net == net and it.kind in ('pad', 'track', 'via')]
        parent = {it.id: it.id for it in its}

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        byid = {it.id: it for it in its}
        for it in its:
            for lay in it.layers:
                bb = (it.bbox[0] - 0.01, it.bbox[1] - 0.01, it.bbox[2] + 0.01, it.bbox[3] + 0.01)
                for ot in self.near(lay, bb):
                    if ot.id <= it.id or ot.id not in byid:
                        continue
                    if find(ot.id) == find(it.id):
                        continue
                    if touches(it, ot):
                        parent[find(ot.id)] = find(it.id)
        if net in PLANES:  # the plane layer of the net (In1.Cu for GND) joins every via and THT pad of the net
            plane = [it.id for it in its if PLANES[net] in it.layers]
            for i in plane[1:]:
                parent[find(i)] = find(plane[0])
        groups = collections.defaultdict(list)
        for it in its:
            groups[find(it.id)].append(it)
        return list(groups.values())


def touches(p, q):
    """Two same-net items touch (copper overlaps)."""
    if p.kind == 'track' and q.kind == 'track':
        return segseg(p.a, p.b, q.a, q.b) <= p.width / 2 + q.width / 2 + 1e-4 and _endpoint_join(p, q)
    if p.kind == 'track':
        p, q = q, p
    if q.kind == 'track':
        # KiCad joins a track to a pad/via when a track end lies inside it
        return any(p.shape.dist(*e) <= 1e-4 for e in (q.a, q.b)) or (p.kind == 'via' and False)
    # pad/via vs pad/via
    if p.kind == 'via' and q.kind == 'via':
        return math.hypot(p.at[0] - q.at[0], p.at[1] - q.at[1]) <= 1e-4
    if p.kind == 'via':
        p, q = q, p
    if q.kind == 'via':
        return p.shape.dist(*q.at) <= 1e-4
    return False


def _endpoint_join(p, q):
    """KiCad: tracks connect when an end of one lies on the other (within its half-width)."""
    for e in (p.a, p.b):
        if seg_dist(e[0], e[1], q.a[0], q.a[1], q.b[0], q.b[1]) <= q.width / 2 + 1e-4:
            return True
    for e in (q.a, q.b):
        if seg_dist(e[0], e[1], p.a[0], p.a[1], p.b[0], p.b[1]) <= p.width / 2 + 1e-4:
            return True
    return False
