"""Completion of a frozen route: connect every net's islands with the grid router, ripping up router copper of
other nets only when needed and re-routing those nets in turn (W2 CTRL-R; W2 PWRB-R copy for PWR_B, BOARD_BOX set by
the driver)."""
import math, collections
import model as M
import router as R

BOARD_BOX = (100.0, 100.0, 150.0, 244.0)  # KiCad mm (CTRL); freeze6.py sets the PWR_B box


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
                layers=('F.Cu', 'In2.Cu', 'B.Cu'), bias=None, l2_bias=None):
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
                # L2 (In1.Cu, the GND plane) as a fourth layer at a higher cost per mm, only when three layers have no path
                l4 = ('F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu')
                b4 = [0.0, l2_bias, 0.0, 0.0]
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
                        if lay in M.PLANES.values():
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
                    if lay == M.PLANES.get(net):
                        continue
                    for ot in m.near(lay, (it.at[0] - 1, it.at[1] - 1, it.at[0] + 1, it.at[1] + 1)):
                        if ot.id == it.id or ot.net != net:
                            continue
                        if ot.kind == 'track' and any(it.shape.dist(*e) <= 1e-4 for e in (ot.a, ot.b)):
                            lays.add(lay)
                        elif ot.kind == 'pad' and ot.shape.dist(*it.at) <= 1e-4:
                            lays.add(lay)
                if net in M.PLANES:
                    lays.add(M.PLANES[net])
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
            lays = {M.PLANES[net]} if net in M.PLANES else set()
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


# ---------------------------------------------------------------- W2 PWRJ-LAYERS6 additions (PWR_A, PWR_B)
def _pads(gr):
    return frozenset(f'{i.ref}.{i.pad}' for i in gr if i.kind == 'pad')


def _gap(A, B):
    ax = (min(i.bbox[0] for i in A), min(i.bbox[1] for i in A), max(i.bbox[2] for i in A), max(i.bbox[3] for i in A))
    bx = (min(i.bbox[0] for i in B), min(i.bbox[1] for i in B), max(i.bbox[2] for i in B), max(i.bbox[3] for i in B))
    return math.hypot(max(ax[0] - bx[2], bx[0] - ax[2], 0), max(ax[1] - bx[3], bx[1] - ax[3], 0))


def neck_link(m, net, A, B, layers, class_w, neck_max, neck_min=0.25):
    """A short pad-to-pad joint narrower than the class (W2 PWRJ-LAYERS6): between a pad of island A and a pad of island B
    at most neck_max apart on a common outer layer, a straight or one-elbow track from pad centre to pad centre, as wide as
    the class or the narrower pad (never below neck_min). The board spec lists the first pad's ref in neck_exempt with the
    link length as escape_mm (pcb/check_boards.py: both ends of the piece within escape_mm + half the pad of that pad), so
    the class-width check does not apply to this pin-entry piece. Returns (res, neck record) or (None, None)."""
    pa_list = [i for i in A if i.kind == 'pad']
    pb_list = [i for i in B if i.kind == 'pad']
    cands = []
    for pa in pa_list:
        for pb in pb_list:
            d = math.hypot(pa.at[0] - pb.at[0], pa.at[1] - pb.at[1])
            if d > neck_max:
                continue
            for lay in layers:
                if lay in pa.layers and lay in pb.layers:
                    cands.append((d, lay, pa, pb))
    cands.sort(key=lambda c: (c[0], c[1], c[2].ref or '', c[2].pad or ''))
    for d, lay, pa, pb in cands:
        def short(p):
            b = p.shape.bbox
            return min(b[2] - b[0], b[3] - b[1])
        w = max(neck_min, math.floor(min(class_w, short(pa), short(pb)) * 20 + 1e-9) / 20)
        paths = [[pa.at, pb.at], [pa.at, (pa.at[0], pb.at[1]), pb.at], [pa.at, (pb.at[0], pa.at[1]), pb.at]]
        for pts in paths:
            pts = [p for k, p in enumerate(pts) if k == 0 or math.hypot(p[0] - pts[k - 1][0], p[1] - pts[k - 1][1]) > 1e-6]
            if len(pts) < 2:
                continue
            if all(m.track_margin(net, lay, w, a, b)[0] >= 0.0 for a, b in zip(pts, pts[1:])):
                length = sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(pts, pts[1:]))
                far = max(math.hypot(p[0] - pa.at[0], p[1] - pa.at[1]) for p in pts)
                return ({'runs': [(lay, pts)], 'vias': [], 'width': w},
                        {'net': net, 'ref': pa.ref, 'pad': pa.pad, 'to': f'{pb.ref}.{pb.pad}', 'layer': lay, 'width_mm': round(w, 4),
                         'length_mm': round(length, 4), 'escape_mm': round(math.ceil(far / 0.05 - 1e-9) * 0.05, 4)})
    return None, None


def connect_all(self, net, allow_rip=True, width=0.15, layers=('F.Cu', 'In2.Cu', 'B.Cu'), g=0.05, via_cost=1.5, neck=None,
                max_links=80):
    """Join the islands of a net pair by pair (W2 PWRJ-LAYERS6): as Finisher.connect, but a pair without a path is skipped
    and the next pair is tried, so one walled-in pad does not leave the rest of the net open; neck = (class width, max mm)
    allows neck_link for a pair that has no class-width path. Returns (all joined, ripped nets, neck records)."""
    ripped, necks, failed = [], [], set()
    prune(self.m, net)
    for _ in range(max_links):
        groups = [gr for gr in self.m.islands(net) if any(i.kind == 'pad' for i in gr) or len(gr) > 1]
        if len(groups) <= 1:
            return True, ripped, necks
        groups.sort(key=lambda gr: (-len(gr), sorted(_pads(gr))))
        done = False
        for A in groups:
            # the nearest three other islands of A only, the wide search for the nearest one only (bounded cost per net)
            for nb, B in enumerate(sorted((gr for gr in groups if gr is not A), key=lambda gr: (_gap(A, gr), sorted(_pads(gr))))[:3]):
                key = frozenset((_pads(A), _pads(B)))
                if key in failed:
                    continue
                res, how, rec = None, 'free', None
                res = R.route_link(self.m, net, A, B, island_box([A, B], 6.0), width=width, g=g, via_cost=via_cost, verbose=False,
                                   layers=layers, max_nodes=2_000_000)
                if res is None and nb == 0:
                    res = R.route_link(self.m, net, A, B, island_box([A, B], 25.0), width=width, g=g, via_cost=via_cost,
                                       verbose=False, layers=layers, max_nodes=3_000_000)
                    how = 'free-wide'
                if res is None and neck:
                    res, rec = neck_link(self.m, net, A, B, [l for l in layers if l in ('F.Cu', 'B.Cu')], neck[0], neck[1])
                    how = 'neck'
                if res is None and allow_rip:
                    res = R.route_link(self.m, net, A, B, island_box([A, B], 8.0), width=width, g=g, via_cost=via_cost,
                                       verbose=False, layers=layers, soft_src=('router',), soft_cost=2.0)
                    how = 'rip'
                    if res is not None:
                        hits, bad = conflicts(self.m, net, res)
                        if bad:
                            res = None
                        else:
                            for h in hits:
                                self.m.remove(h)
                                self.ripped[h.net] += 1
                                if h.net not in ripped:
                                    ripped.append(h.net)
                if res is None or (not res['runs'] and not res['vias']):
                    failed.add(key)
                    self.log(f'    {net}: no path {sorted(_pads(A))[:3]} - {sorted(_pads(B))[:3]}')
                    continue
                self.tag[net] += 1
                tag = f'FIN-{net}-{self.tag[net]}'
                try:
                    self.records += R.commit(self.m, net, res, tag, lambda *a: None)
                except RuntimeError as e:
                    failed.add(key)
                    self.log(f'    {net}: commit failed {e}')
                    continue
                if rec:
                    necks.append(rec)
                L = sum(math.hypot(q[0] - p[0], q[1] - p[1]) for _, pts in res['runs'] for p, q in zip(pts, pts[1:]))
                self.log(f'  {tag} ({how}): {len(res["runs"])} runs {len(res["vias"])} vias {L:.1f} mm')
                done = True
                break
            if done:
                break
        if not done:
            return False, ripped, necks
    return False, ripped, necks


Finisher.connect_all = connect_all
