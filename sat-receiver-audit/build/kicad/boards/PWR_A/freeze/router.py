"""Grid A* completion router on the board model (W2 CTRL-R; KiCad mm, y down). Needs numpy.

W2 PWRB-R: a copy of build/kicad/boards/CTRL/freeze/router.py (origin/wip/w2-ctrl4-layers6) for PWR_B.
W2 PWRJ-LAYERS6: copied unchanged from build/kicad/boards/PWR_B/freeze/router.py for the 6-layer PWR_A board."""
import math, heapq, time
import numpy as np
import model as M
from model import cb

VIA_D, VIA_DRILL = 0.65, 0.3


def cap_dist(X, Y, x1, y1, x2, y2, r):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 <= 0:
        return np.hypot(X - x1, Y - y1) - r
    t = np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0.0, 1.0)
    return np.hypot(X - (x1 + t * dx), Y - (y1 + t * dy)) - r


def poly_dist(X, Y, pts):
    inside = np.zeros(X.shape, dtype=bool)
    d = np.full(X.shape, np.inf)
    n = len(pts)
    for k in range(n):
        x1, y1 = pts[k - 1]
        x2, y2 = pts[k]
        cond = (y1 > Y) != (y2 > Y)
        with np.errstate(divide='ignore', invalid='ignore'):
            xc = x1 + (Y - y1) * (x2 - x1) / (y2 - y1) if y2 != y1 else np.full(X.shape, np.inf)
        inside ^= cond & (X < xc)
        d = np.minimum(d, cap_dist(X, Y, x1, y1, x2, y2, 0.0))
    d[inside] = 0.0
    return d


def shape_dist(X, Y, s):
    if isinstance(s, cb.Capsule):
        return np.maximum(cap_dist(X, Y, s.x1, s.y1, s.x2, s.y2, s.r), 0.0)
    if isinstance(s, cb.Multi):
        return np.minimum.reduce([shape_dist(X, Y, q) for q in s.shapes])
    if isinstance(s, M.RoundRect):
        return np.maximum(poly_dist(X, Y, s.inner.pts) - s.r, 0.0)
    return poly_dist(X, Y, s.pts)


class Grid:
    def __init__(self, m, box, g=0.05):
        self.m, self.g = m, g
        x0, y0, x1, y1 = box
        self.x0, self.y0 = x0, y0
        self.nx = int(math.ceil((x1 - x0) / g)) + 1
        self.ny = int(math.ceil((y1 - y0) / g)) + 1
        xs = x0 + np.arange(self.nx) * g
        ys = y0 + np.arange(self.ny) * g
        self.X, self.Y = np.meshgrid(xs, ys, indexing='ij')
        # inside the board (even-odd over all edge loops)
        ins = np.zeros(self.X.shape, dtype=bool)
        dedge = np.full(self.X.shape, np.inf)
        for (ax, ay), (bx, by) in m.edges:
            cond = (ay > self.Y) != (by > self.Y)
            with np.errstate(divide='ignore', invalid='ignore'):
                xc = ax + (self.Y - ay) * (bx - ax) / (by - ay) if by != ay else np.full(self.X.shape, np.inf)
            ins ^= cond & (self.X < xc)
            dedge = np.minimum(dedge, cap_dist(self.X, self.Y, ax, ay, bx, by, 0.0))
        self.inside, self.dedge = ins, dedge

    def win(self, bbox, pad):
        i0 = max(0, int(math.floor((bbox[0] - pad - self.x0) / self.g)))
        i1 = min(self.nx, int(math.ceil((bbox[2] + pad - self.x0) / self.g)) + 1)
        j0 = max(0, int(math.floor((bbox[1] - pad - self.y0) / self.g)))
        j1 = min(self.ny, int(math.ceil((bbox[3] + pad - self.y0) / self.g)) + 1)
        if i0 >= i1 or j0 >= j1:
            return None
        return slice(i0, i1), slice(j0, j1)

    def box(self):
        return (self.x0, self.y0, self.x0 + (self.nx - 1) * self.g, self.y0 + (self.ny - 1) * self.g)

    def blocked_track(self, net, layer, width, clr=M.CLR, margin=None, ignore=(), soft=None, soft_src=()):
        g = self.g
        margin = g * 0.75 if margin is None else margin
        blk = np.zeros(self.X.shape, dtype=bool)
        r = width / 2
        bx = self.box()
        for it in self.m.near(layer, (bx[0] - 2, bx[1] - 2, bx[2] + 2, bx[3] + 2)):
            if it.id in ignore or (it.kind != 'npth' and it.net == net and net is not None):
                continue
            infl = r + clr + margin + (0.1 if it.kind == 'npth' else 0.0)
            w = self.win(it.bbox, infl)
            if w is None:
                continue
            d = shape_dist(self.X[w], self.Y[w], it.shape)
            if soft is not None and it.src in soft_src:
                soft[w] |= d < infl
            else:
                blk[w] |= d < infl
        for k in self.m.keepouts:
            if layer not in k['layers']:
                continue
            infl = r + 0.01 + margin
            w = self.win(k['poly'].bbox, infl)
            if w is None:
                continue
            blk[w] |= poly_dist(self.X[w], self.Y[w], k['poly'].pts) < infl
        blk |= ~self.inside
        blk |= self.dedge < r + M.EDGE_CLR + 0.02 + margin
        return blk

    def blocked_via(self, net, d=VIA_D, drill=VIA_DRILL, clr=M.CLR, margin=None, ignore=(), soft=None, soft_src=()):
        g = self.g
        margin = g * 0.75 if margin is None else margin
        r = d / 2
        blk = np.zeros(self.X.shape, dtype=bool)
        bx = self.box()
        seen = set()
        for lay in M.LAYERS:
            for it in self.m.near(lay, (bx[0] - 2, bx[1] - 2, bx[2] + 2, bx[3] + 2)):
                if it.id in seen or it.id in ignore:
                    continue
                seen.add(it.id)
                tgt = soft if (soft is not None and it.src in soft_src) else blk
                if it.kind in ('via', 'npth') or (it.kind == 'pad' and it.drill):
                    hd = it.drill or 0.0
                    infl = drill / 2 + hd / 2 + M.HOLE_HOLE + 0.02 + margin
                    w = self.win((it.at[0], it.at[1], it.at[0], it.at[1]), infl)
                    if w is not None:
                        tgt[w] |= np.hypot(self.X[w] - it.at[0], self.Y[w] - it.at[1]) < infl
                if it.kind == 'npth':
                    continue
                if it.net == net:
                    tgt = blk  # same-net rules are never ripped
                    if it.kind == 'pad' and not it.drill and it.src != 'zone':  # W2 PWR-TOOLS: a via may stand in its own zone fill
                        infl = r + 0.02 + margin
                    elif it.kind == 'track':
                        # a new via either sits on a same-net track centre line (an explicit joint follows) or keeps off
                        # that track and its ends: no via over a track end, no via that only overlaps the track copper
                        # (KiCad 10 track_not_centered_on_via, no hidden anchor-free overlaps)
                        hw = it.width / 2
                        w = self.win(it.bbox, r + 0.01 + margin)
                        if w is not None:
                            d = cap_dist(self.X[w], self.Y[w], it.a[0], it.a[1], it.b[0], it.b[1], 0.0)
                            blk[w] |= (d > hw * 0.5) & (d < r + hw + 0.01 + margin)
                        for e in (it.a, it.b):
                            w = self.win((e[0], e[1], e[0], e[1]), r + 0.01 + margin)
                            if w is not None:
                                blk[w] |= np.hypot(self.X[w] - e[0], self.Y[w] - e[1]) < r + 0.01 + margin
                        continue
                    else:
                        continue
                else:
                    infl = r + clr + margin
                w = self.win(it.bbox, infl)
                if w is None:
                    continue
                tgt[w] |= shape_dist(self.X[w], self.Y[w], it.shape) < infl
        for k in self.m.keepouts:
            infl = r + 0.01 + margin
            w = self.win(k['poly'].bbox, infl)
            if w is None:
                continue
            blk[w] |= poly_dist(self.X[w], self.Y[w], k['poly'].pts) < infl
        blk |= ~self.inside
        blk |= self.dedge < r + M.EDGE_CLR + 0.02 + margin
        return blk

    def covered(self, items, layer):
        """Cells whose centre lies inside the copper of the items on the layer."""
        cov = np.zeros(self.X.shape, dtype=bool)
        for it in items:
            if layer not in it.layers:
                continue
            w = self.win(it.bbox, 0.0)
            if w is None:
                continue
            s = it.shape
            if it.kind == 'track':  # stay well inside the track: within a third of its width of the centre line
                s = cb.Capsule(it.a[0], it.a[1], it.b[0], it.b[1], it.width / 6)
            elif it.kind == 'via':
                s = cb.Capsule(it.at[0], it.at[1], it.at[0], it.at[1], it.size / 4)
            cov[w] |= shape_dist(self.X[w], self.Y[w], s) <= 0.0
        return cov

    def pt(self, i, j):
        return (self.x0 + i * self.g, self.y0 + j * self.g)


def astar(grid, layers, blk, vblk, src, dst, via_cost=1.5, bias=None, max_nodes=6_000_000, soft=None, vsoft=None, soft_cost=3.0):
    """src/dst: dict layer -> bool raster. Returns list of (layer, i, j) or None."""
    nl, nx, ny = len(layers), grid.nx, grid.ny
    N = nl * nx * ny
    free = np.stack([~blk[l] for l in layers]).reshape(-1)
    vfree = (~vblk).reshape(-1)
    pen = np.stack([soft[l] for l in layers]).reshape(-1).astype(np.float64) * soft_cost if soft else None
    vpen = vsoft.reshape(-1).astype(np.float64) * (soft_cost * 3) if vsoft is not None else None
    goal = np.stack([dst[l] for l in layers]).reshape(-1) & free
    if not goal.any():
        return None, 'no free goal cell'
    gi = np.nonzero(goal)[0]
    gl, rem = np.divmod(gi, nx * ny)
    gx, gy = np.divmod(rem, ny)
    tx0, tx1, ty0, ty1 = gx.min(), gx.max(), gy.min(), gy.max()
    g = grid.g
    gs = np.full(N, np.inf, dtype=np.float64)
    came = np.full(N, -1, dtype=np.int64)
    heap = []
    starts = np.nonzero(np.stack([src[l] for l in layers]).reshape(-1) & free)[0]
    if len(starts) == 0:
        return None, 'no free start cell'

    def h(i, j):
        dx = max(tx0 - i, 0, i - tx1)
        dy = max(ty0 - j, 0, j - ty1)
        return g * (max(dx, dy) + 0.41421356 * min(dx, dy))
    for s in starts:
        gs[s] = 0.0
        l, rem = divmod(int(s), nx * ny)
        i, j = divmod(rem, ny)
        heapq.heappush(heap, (h(i, j), 0.0, int(s)))
    D2 = g * math.sqrt(2)
    steps = [(1, 0, g), (-1, 0, g), (0, 1, g), (0, -1, g), (1, 1, D2), (1, -1, D2), (-1, 1, D2), (-1, -1, D2)]
    pops = 0
    while heap:
        f, c, s = heapq.heappop(heap)
        if c > gs[s]:
            continue
        pops += 1
        if pops > max_nodes:
            return None, f'node limit {pops}'
        l, rem = divmod(s, nx * ny)
        via_arrival = came[s] != -1 and int(came[s]) // (nx * ny) != l
        if goal[s] and not via_arrival:
            path = []
            while s != -1:
                l, rem = divmod(int(s), nx * ny)
                i, j = divmod(rem, ny)
                path.append((layers[l], i, j))
                s = int(came[s])
            return path[::-1], f'{pops} pops'
        i, j = divmod(rem, ny)
        base = l * nx * ny
        for di, dj, cost in steps:
            a, b = i + di, j + dj
            if 0 <= a < nx and 0 <= b < ny:
                t = base + a * ny + b
                if free[t]:
                    if di and dj:  # no corner cutting
                        if not (free[base + a * ny + j] and free[base + i * ny + b]):
                            continue
                    nc = c + cost + (bias[l] if bias else 0.0) * cost
                    if pen is not None and pen[t]:
                        nc += pen[t] * cost / g
                    if nc < gs[t]:
                        gs[t] = nc
                        came[t] = s
                        heapq.heappush(heap, (nc + h(a, b), nc, t))
        if vfree[rem] and came[s] != -1 and not via_arrival:
            for l2 in range(nl):
                if l2 == l:
                    continue
                t = l2 * nx * ny + rem
                if free[t]:
                    nc = c + via_cost + (vpen[rem] if vpen is not None else 0.0) + (pen[t] if pen is not None else 0.0)
                    if nc < gs[t]:
                        gs[t] = nc
                        came[t] = s
                        heapq.heappush(heap, (nc + h(i, j), nc, t))
    astar.last_explored = np.isfinite(gs).reshape(nl, nx, ny)
    return None, f'exhausted {pops}'


def to_runs(grid, path):
    """Grid path -> [(layer, [points])], via positions between runs."""
    runs, vias = [], []
    cur = None
    for lay, i, j in path:
        p = grid.pt(i, j)
        if cur is None or cur[0] != lay:
            if cur is not None:
                vias.append(cur[1][-1])
                cur = (lay, [cur[1][-1]])
                runs.append(cur)
            else:
                cur = (lay, [p])
                runs.append(cur)
                continue
        if cur[1][-1] != p:
            cur[1].append(p)
    return runs, vias


def simplify(m, net, lay, width, pts, clr=M.CLR + 0.005, ignore=()):
    """Greedy string pulling with the exact clearance check."""
    out = [pts[0]]
    i = 0
    n = len(pts)
    while i < n - 1:
        best = i + 1
        # try far jumps first (coarse), then refine
        j = n - 1
        lo = i + 1
        while j > lo:
            mg, _ = m.track_margin(net, lay, width, pts[i], pts[j], clr=clr, ignore=ignore)
            if mg >= 0:
                best = j
                break
            j = lo + (j - lo) // 2 if j - lo > 8 else j - 1
        # walk forward from best while clear
        k = best + 1
        while k < n:
            mg, _ = m.track_margin(net, lay, width, pts[i], pts[k], clr=clr, ignore=ignore)
            if mg < 0:
                break
            best = k
            k += 1
        out.append(pts[best])
        i = best
    return out


def route_link(m, net, isl_a, isl_b, box, width=0.15, g=0.05, via_cost=1.5, layers=('F.Cu', 'In2.Cu', 'B.Cu'), bias=None,
               ignore=(), verbose=True, max_nodes=6_000_000, soft_src=(), soft_cost=3.0):
    t = time.time()
    grid = Grid(m, box, g)
    soft = {l: np.zeros(grid.X.shape, dtype=bool) for l in layers} if soft_src else None
    vsoft = np.zeros(grid.X.shape, dtype=bool) if soft_src else None
    blk = {l: grid.blocked_track(net, l, width, ignore=ignore, soft=soft[l] if soft else None, soft_src=soft_src) for l in layers}
    vblk = grid.blocked_via(net, ignore=ignore, soft=vsoft, soft_src=soft_src)
    src = {l: grid.covered(isl_a, l) for l in layers}
    dst = {l: grid.covered(isl_b, l) for l in layers}
    t1 = time.time()
    path, why = astar(grid, list(layers), blk, vblk, src, dst, via_cost=via_cost, bias=bias, max_nodes=max_nodes,
                      soft=soft, vsoft=vsoft, soft_cost=soft_cost)
    if verbose:
        print(f'  {net}: grid {grid.nx}x{grid.ny} raster {t1 - t:.1f}s astar {time.time() - t1:.1f}s {why}')
    if path is None:
        return None
    runs, vias = to_runs(grid, path)
    out_runs = []
    sign = set(ignore) | ({it.id for it in m.items if it.alive and it.src in soft_src} if soft_src else set())
    for lay, pts in runs:
        if len(pts) == 1:
            continue
        out_runs.append((lay, simplify(m, net, lay, width, pts, ignore=sign)))
    return {'runs': out_runs, 'vias': vias, 'width': width}


def snap_to_vias(m, net, res):
    """KiCad 10 DRC 'track_not_centered_on_via': a track end inside a via must sit on its centre. A polyline stretch
    inside a same-net via (existing or new) becomes [entry point just outside the via, via centre, exit point just
    outside the via]; the entry and exit points lie on the original segments, so the clearance check still holds."""
    centres = [(it.at, it.size / 2) for it in m.items if it.alive and it.kind == 'via' and it.net == net] +         [(v, VIA_D / 2) for v in res['vias']]
    radius = {}
    for c, rr in centres:
        radius[c] = max(rr, radius.get(c, 0.0))

    def via_of(p):
        for c, rr in centres:
            if math.hypot(p[0] - c[0], p[1] - c[1]) < rr + 1e-6:
                return c
        return None

    def boundary(a, b, c):
        """Point on segment a (outside) -> b (inside) at distance r + 0.005 from c, nearest b."""
        lo, hi = 0.0, 1.0  # t along a->b; dist(t=0) > rb, dist(t=1) < rb
        rb = radius[c] + 0.005
        for _ in range(60):
            mid = (lo + hi) / 2
            q = (a[0] + (b[0] - a[0]) * mid, a[1] + (b[1] - a[1]) * mid)
            if math.hypot(q[0] - c[0], q[1] - c[1]) > rb:
                lo = mid
            else:
                hi = mid
        return (a[0] + (b[0] - a[0]) * lo, a[1] + (b[1] - a[1]) * lo)
    runs = []
    for lay, pts in res['runs']:
        out, i, n = [], 0, len(pts)
        while i < n:
            c = via_of(pts[i])
            if c is None:
                out.append(pts[i])
                i += 1
                continue
            j = i
            while j + 1 < n and via_of(pts[j + 1]) == c:
                j += 1
            if i > 0 and math.hypot(pts[i - 1][0] - c[0], pts[i - 1][1] - c[1]) > radius[c] + 0.005:
                out.append(boundary(pts[i - 1], pts[i], c))
            out.append((c[0], c[1]))
            if j < n - 1 and math.hypot(pts[j + 1][0] - c[0], pts[j + 1][1] - c[1]) > radius[c] + 0.005:
                out.append(boundary(pts[j + 1], pts[j], c))
            i = j + 1
        ded = []
        for q in out:
            if not ded or math.hypot(q[0] - ded[-1][0], q[1] - ded[-1][1]) > 1e-6:
                ded.append(q)
        if len(ded) >= 2:
            runs.append((lay, ded))
    res['runs'] = runs
    return res


def via_joints(m, net, vias, width):
    """Explicit joints at every new via (KiCad 10 DRC track_not_centered_on_via, and connectivity that does not lean on
    KiCad's anchor rule): a same-net track end inside the via moves onto its centre (or, where that move breaks a
    clearance, gets a short track to the centre); a track that crosses the via centre away from its ends is split
    there (router or new copper) or joined by a short track to its nearer end inside its own copper (scripted copper,
    made by make_spec.py and kept as it is)."""
    r = VIA_D / 2
    for v in vias:
        near = []
        for lay in M.LAYERS:
            near += [it for it in m.near(lay, (v[0] - 1, v[1] - 1, v[0] + 1, v[1] + 1)) if it.alive and it.kind == 'track' and it.net == net]
        for it in near:
            if not it.alive:
                continue
            if any(math.hypot(v[0] - e[0], v[1] - e[1]) <= 1e-6 for e in (it.a, it.b)):
                continue
            inside = [e for e in (it.a, it.b) if math.hypot(v[0] - e[0], v[1] - e[1]) <= r + 1e-6]
            if inside:
                e = inside[0]
                o = it.b if e == it.a else it.a
                if it.src in ('router', 'new'):
                    mg, why = m.track_margin(net, it.layers[0], it.width, o, v, ignore={it.id})
                    if mg >= 0:
                        m.remove(it)
                        m.add_track(net, it.layers[0], it.width, o, v, src=it.src)
                        continue
                mg, why = m.track_margin(net, it.layers[0], min(width, it.width), e, v)
                if mg < 0:
                    raise RuntimeError(f'track end inside the via at {v}: no joint to its centre ({mg:.3f} {why})')
                m.add_track(net, it.layers[0], min(width, it.width), e, v, src='new')
                continue
            if M.seg_dist(v[0], v[1], it.a[0], it.a[1], it.b[0], it.b[1]) > it.width / 2:
                continue
            if it.src in ('router', 'new'):
                m.remove(it)
                m.add_track(net, it.layers[0], it.width, it.a, v, src=it.src)
                m.add_track(net, it.layers[0], it.width, v, it.b, src=it.src)
            else:
                e = min((it.a, it.b), key=lambda q: math.hypot(v[0] - q[0], v[1] - q[1]))
                w = min(width, it.width)
                mg, why = m.track_margin(net, it.layers[0], w, v, e)
                if mg < 0:
                    raise RuntimeError(f'via joint to scripted track at {v}: margin {mg:.3f} {why}')
                m.add_track(net, it.layers[0], w, v, e, src='new')


def commit(m, net, res, tag, log):
    """Add the routed copper to the model after an exact check; returns spec-ready records (KiCad mm)."""
    res = snap_to_vias(m, net, res)
    recs = []
    for k, v in enumerate(res['vias']):
        mg, why = m.via_margin(net, v)
        if mg < 0:
            raise RuntimeError(f'{tag}: via {v} margin {mg:.3f} {why}')
        m.add_via(net, v, VIA_D, VIA_DRILL, src='new')
        recs.append({'kind': 'via', 'net': net, 'at': v, 'id': f'{tag}-V{k}', 'margin': mg})
    for k, (lay, pts) in enumerate(res['runs']):
        for a, b in zip(pts, pts[1:]):
            mg, why = m.track_margin(net, lay, res['width'], a, b)
            if mg < 0:
                raise RuntimeError(f'{tag}: track {a}-{b} on {lay} margin {mg:.3f} {why}')
        for a, b in zip(pts, pts[1:]):
            m.add_track(net, lay, res['width'], a, b, src='new')
        recs.append({'kind': 'track', 'net': net, 'layer': lay, 'width': res['width'], 'path': pts, 'id': f'{tag}-{k}'})
    via_joints(m, net, res['vias'], res['width'])
    log(f'  committed {tag}: {len(res["runs"])} runs, {len(res["vias"])} vias')
    return recs
