"""Completion of the frozen PWR_B route: connect every net's islands with the grid router, ripping up router copper of
other nets only when needed and re-routing those nets in turn (W2 PWRB-R, ported from W2 CTRL-R)."""
import math, collections
import model as M
import router as R

BOARD_BOX = (100.0, 100.0, 236.0, 210.0)  # KiCad mm (PWR_B: outline 136 x 110, frame of pcb/board_gen.py)


def conflicts(m, net, res, soft_src=('router',)):
    """Items of other nets that the routed result violates (only soft items can be ripped)."""
    hit = set()
    w = res['width']
    for lay, pts in res['runs']:
        for a, b in zip(pts, pts[1:]):
            r = w / 2
            bb = (min(a[0], b[0]) - r - 1, min(a[1], b[1]) - r - 1, max(a[0], b[0]) + r + 1, max(a[1], b[1]) + r + 1)
            for it in m.near(lay, bb):
                if it.net == net or it.kind == 'npth':
                    continue
                if M.shape_seg_dist(it.shape, a, b) - r - M.CLR < 0:
                    hit.add(it.id)
    for v in res['vias']:
        bb = (v[0] - 1.5, v[1] - 1.5, v[0] + 1.5, v[1] + 1.5)
        for lay in M.LAYERS:
            for it in m.near(lay, bb):
                if it.kind in ('via', 'npth') or (it.kind == 'pad' and it.drill):
                    if math.hypot(v[0] - it.at[0], v[1] - it.at[1]) - R.VIA_DRILL / 2 - (it.drill or 0) / 2 - M.HOLE_HOLE < 0:
                        hit.add(it.id)
                if it.net == net or it.kind == 'npth':
                    continue
                if it.shape.dist(*v) - R.VIA_D / 2 - M.CLR < 0:
                    hit.add(it.id)
    bad = [m.items[i] for i in hit if m.items[i].src not in soft_src]
    return [m.items[i] for i in hit], bad


def rip(m, net, srcs=('router',)):
    n = 0
    for it in m.items:
        if it.alive and it.net == net and it.kind in ('track', 'via') and it.src in srcs:
            m.remove(it)
            n += 1
    return n


def island_box(groups, margin=6.0):
    xs = [i.bbox[0] for g in groups for i in g] + [i.bbox[2] for g in groups for i in g]
    ys = [i.bbox[1] for g in groups for i in g] + [i.bbox[3] for g in groups for i in g]
    b = (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)
    return (max(b[0], BOARD_BOX[0]), max(b[1], BOARD_BOX[1]), min(b[2], BOARD_BOX[2]), min(b[3], BOARD_BOX[3]))


class Finisher:
    def __init__(self, m, log=print):
        self.m, self.log = m, log
        self.records = []
        self.ripped = collections.Counter()
        self.tag = collections.Counter()

    def connect(self, net, allow_rip=True, width=0.15, soft_cost=2.0, margin=6.0, g=0.05, via_cost=1.5, first=None, max_iter=12,
                layers=('F.Cu', 'B.Cu'), bias=None, l2_bias=None):
        """Join the islands of net one by one; returns the list of nets whose router copper was ripped."""
        ripped = []
        prune(self.m, net)
        for _ in range(max_iter):
            groups = self.m.islands(net)
            groups = [gr for gr in groups if any(i.kind in ('pad',) for i in gr) or len(gr) > 1]
            if len(groups) <= 1:
                return True, ripped
            # source: the island holding `first` if given, else the biggest
            groups.sort(key=lambda gr: -len(gr))
            if first:
                groups.sort(key=lambda gr: 0 if any(f'{i.ref}.{i.pad}' == first for i in gr if i.kind == 'pad') else 1)
            A = groups[0]
            # nearest other island by bbox gap
            def gap(gr):
                ax = (min(i.bbox[0] for i in A), min(i.bbox[1] for i in A), max(i.bbox[2] for i in A), max(i.bbox[3] for i in A))
                bx = (min(i.bbox[0] for i in gr), min(i.bbox[1] for i in gr), max(i.bbox[2] for i in gr), max(i.bbox[3] for i in gr))
                dx = max(ax[0] - bx[2], bx[0] - ax[2], 0)
                dy = max(ax[1] - bx[3], bx[1] - ax[3], 0)
                return math.hypot(dx, dy)
            others = sorted(groups[1:], key=gap)
            B = others[0]
            box = island_box([A, B], margin)
            res = R.route_link(self.m, net, A, B, box, width=width, g=g, via_cost=via_cost, verbose=False, layers=layers, bias=bias)
            how = 'free'
            if res is None:
                box = island_box([A, B], 25.0)
                res = R.route_link(self.m, net, A, B, box, width=width, g=g, via_cost=via_cost, verbose=False, layers=layers, bias=bias)
                how = 'free-wide'
            if res is None and l2_bias is not None:
                # In2.Cu (the second GND plane) as a third layer at a higher cost per mm, only when F.Cu / B.Cu have no path
                l4 = ('F.Cu', 'In2.Cu', 'B.Cu')
                b4 = [0.0, l2_bias, 0.0]
                res = R.route_link(self.m, net, A, B, island_box([A, B], 25.0), width=width, g=g, via_cost=via_cost,
                                   verbose=False, layers=l4, bias=b4)
                how = 'free-L2'
                if res is None:
                    layers, bias = l4, b4
            if res is None and allow_rip:
                box = island_box([A, B], 8.0)
                res = R.route_link(self.m, net, A, B, box, width=width, g=g, via_cost=via_cost, verbose=False, layers=layers, bias=bias,
                                   soft_src=('router',), soft_cost=soft_cost)
                how = 'rip'
                if res is not None:
                    hits, bad = conflicts(self.m, net, res)
                    if bad:
                        self.log(f'    {net}: rip path hits locked items {[(b.kind, b.net, b.src) for b in bad][:4]}')
                        return False, ripped
                    for h in hits:  # local rip: only the conflicting router segments and vias
                        self.m.remove(h)
                        self.ripped[h.net] += 1
                        if h.net not in ripped:
                            ripped.append(h.net)
                    self.log(f'    ripped {len(hits)} router items of {sorted({h.net for h in hits})}')
            if res is not None and not res['runs'] and not res['vias']:
                # A and B overlap without a KiCad anchor connection: join with a short track to the B pad centre
                pads = [i for i in B if i.kind == 'pad']
                fixed = False
                for pd in pads:
                    for lay in pd.layers:
                        if lay in M.PLANES:
                            continue
                        # find an A point inside this pad on this layer
                        pts = []
                        for it in A:
                            if lay not in it.layers:
                                continue
                            if it.kind == 'track':
                                for k in range(21):
                                    q = (it.a[0] + (it.b[0] - it.a[0]) * k / 20, it.a[1] + (it.b[1] - it.a[1]) * k / 20)
                                    if pd.shape.dist(*q) <= 0:
                                        pts.append(q)
                        for q in pts:
                            mg, _ = self.m.track_margin(net, lay, width, q, pd.at)
                            if mg >= 0:
                                res = {'runs': [(lay, [q, pd.at])], 'vias': [], 'width': width}
                                fixed = True
                                break
                        if fixed:
                            break
                    if fixed:
                        break
                if not fixed:
                    # a via of one island on a track of the other: split the track at the via centre (explicit joint)
                    for P, Q in ((A, B), (B, A)):
                        for v in [i for i in P if i.kind == 'via']:
                            for t in [i for i in Q if i.kind == 'track' and i.src in ('router', 'new')]:
                                d = M.seg_dist(v.at[0], v.at[1], t.a[0], t.a[1], t.b[0], t.b[1])
                                if d <= t.width / 2 and min(math.hypot(v.at[0] - e[0], v.at[1] - e[1]) for e in (t.a, t.b)) > 1e-6:
                                    self.m.remove(t)
                                    self.m.add_track(net, t.layers[0], t.width, t.a, v.at, src=t.src)
                                    self.m.add_track(net, t.layers[0], t.width, v.at, t.b, src=t.src)
                                    fixed = True
                                    break
                            if fixed:
                                break
                        if fixed:
                            break
                    if fixed:
                        self.log(f'    {net}: split a track at a via of the other island')
                        continue
                    self.log(f'    {net}: zero-length link not fixable')
                    return False, ripped
                how = 'overlap-join'
            if res is None:
                self.log(f'    {net}: no path between islands {[f"{i.ref}.{i.pad}" for i in A if i.kind == "pad"][:3]} and '
                         f'{[f"{i.ref}.{i.pad}" for i in B if i.kind == "pad"][:3]}')
                return False, ripped
            self.tag[net] += 1
            tag = f'FIN-{net}-{self.tag[net]}'
            try:
                recs = R.commit(self.m, net, res, tag, lambda *a: None)
            except RuntimeError as e:
                self.log(f'    {net}: commit failed {e}')
                return False, ripped
            self.records += recs
            L = sum(math.hypot(q[0] - p[0], q[1] - p[1]) for _, pts in res['runs'] for p, q in zip(pts, pts[1:]))
            self.log(f'  {tag} ({how}): {len(res["runs"])} runs {len(res["vias"])} vias {L:.1f} mm')
        return False, ripped

    def unconnected(self):
        out = {}
        nets = sorted({i.net for i in self.m.items if i.alive and i.net})
        for n in nets:
            if n == 'GND':
                continue
            k = len(self.m.islands(n))
            if k > 1:
                out[n] = k - 1
        return out


def prune(m, net, srcs=('router', 'new'), log=print):
    """Remove dangling copper of a net: track ends that touch nothing, vias joined on fewer than two layers,
    and copper islands without a pad (only router or new copper is removed)."""
    removed = 0
    while True:
        its = [it for it in m.items if it.alive and it.net == net and it.kind in ('pad', 'track', 'via')]
        changed = False
        for it in its:
            if not it.alive or it.src not in srcs:
                continue
            if it.kind == 'track':
                for e in (it.a, it.b):
                    if not end_joined(m, it, e, net):
                        m.remove(it)
                        removed += 1
                        changed = True
                        break
            elif it.kind == 'via':
                lays = set()
                for lay in M.LAYERS:
                    if lay == 'In1.Cu' and net == 'GND':
                        continue
                    for ot in m.near(lay, (it.at[0] - 1, it.at[1] - 1, it.at[0] + 1, it.at[1] + 1)):
                        if ot.id == it.id or ot.net != net:
                            continue
                        if ot.kind == 'track' and any(it.shape.dist(*e) <= 1e-4 for e in (ot.a, ot.b)):
                            lays.add(lay)
                        elif ot.kind == 'pad' and ot.shape.dist(*it.at) <= 1e-4:
                            lays.add(lay)
                if net == 'GND':
                    lays.add('In1.Cu')
                if len(lays) < 2:
                    m.remove(it)
                    removed += 1
                    changed = True
        for gr in m.islands(net):
            if not any(i.kind == 'pad' for i in gr) and all(i.src in srcs for i in gr):
                for i in gr:
                    m.remove(i)
                    removed += 1
                changed = True
        if not changed:
            return removed


def dangling(m):
    """Report (no removal) track ends that touch nothing and vias joined on fewer than two layers."""
    out = []
    for it in m.items:
        if not it.alive or it.kind not in ('track', 'via'):
            continue
        net = it.net
        if it.kind == 'track':
            for e in (it.a, it.b):
                if not end_joined(m, it, e, net):
                    out.append(('track end', net, e))
        else:
            lays = {'In1.Cu'} if net == 'GND' else set()
            for lay in M.LAYERS:
                for ot in m.near(lay, (it.at[0] - 1, it.at[1] - 1, it.at[0] + 1, it.at[1] + 1)):
                    if ot.id == it.id or ot.net != net:
                        continue
                    if (ot.kind == 'track' and any(it.shape.dist(*e) <= 1e-4 for e in (ot.a, ot.b))) or \
                            (ot.kind == 'pad' and ot.shape.dist(*it.at) <= 1e-4):
                        lays.add(lay)
            if len(lays) < 2:
                out.append(('via', net, it.at))
    return out


def end_joined(m, it, e, net):
    """KiCad 10 track_dangling, strict: the end of track it is joined when a pad or via of the net contains it, another
    track of the net ends on it, or a track of the net that does not share its other end covers it (KiCad anchor test)."""
    other = it.b if e == it.a else it.a
    lay = it.layers[0]
    for ot in m.near(lay, (e[0] - 0.5, e[1] - 0.5, e[0] + 0.5, e[1] + 0.5)):
        if ot.id == it.id or ot.net != net or not ot.alive:
            continue
        if ot.kind in ('pad', 'via'):
            if ot.shape.dist(*e) <= 1e-4:
                return True
        elif ot.kind == 'track':
            if min(math.hypot(e[0] - q[0], e[1] - q[1]) for q in (ot.a, ot.b)) <= 1e-4:
                return True
            if min(math.hypot(other[0] - q[0], other[1] - q[1]) for q in (ot.a, ot.b)) <= 1e-4:
                continue  # the adjacent segment of the same chain
            if M.seg_dist(e[0], e[1], ot.a[0], ot.a[1], ot.b[0], ot.b[1]) <= ot.width / 2:
                return True
    return False
