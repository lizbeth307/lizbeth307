"""Incremental re-freeze of the CTRL route (W2 CTRL-4, review RV-CTRLR-5): freeze_route.py --from-frozen. Needs numpy.

The frozen route (route-frozen.json) is valid only for the pads and the scripted copper it was made on (its guard). After a
pad, net or scripted-copper change this mode starts from the committed frozen copper instead of a new Freerouting route:
  1. the board model: pads, keepouts and edges of the committed GENERATED board (build/kicad/boards/CTRL/CTRL.kicad_pcb,
     exact pad shapes); pads whose ref moved or whose net changed in the current spec are replaced by the pads make_spec.py
     places (its check_boards shapes); all copper of that board is dropped;
  2. the copper: the scripted copper make_spec.py makes now (before the frozen copper; drop_scripted applied) as hard,
     locked copper, and the frozen copper of route-frozen.json (router and completion copper) as soft copper;
  3. frozen copper of the nets named with --rip / --scripted is removed, every frozen item that breaks a clearance
     against the hard copper, a pad, a keepout or an edge is removed (exact check of model.py), and so is every frozen
     track the exact checks of step 5 flag (a dangling end, an end in a scripted via off its centre);
  4. dangling frozen copper of the touched nets is pruned and every touched net with open connections is joined again by
     the grid A* of fin.py (other nets' frozen copper is ripped only where the cheapest path crosses it, and those nets are
     joined again in turn); nets named with --scripted and the scripted classes are never routed here, they must be
     complete from the scripted copper;
  5. every item is checked again (open connections, dangling copper, clearance) and route-frozen.json is written: records
     the step left untouched stay byte for byte as they were, changed router records are re-chained, new copper goes to
     the completion lists; the guard is the one make_spec.py computes now.
--renet (W2 CTRL-4 PROTECT study, taken into W2 CTRL-4) handles a net split by a new part: pads that only changed nets keep
their exact board shapes (only their nets follow the spec), and an island of frozen copper of net N that touches pads or
scripted copper of exactly one other net M takes M (export keeps such records in place under the new net).
With no change (same pads, same scripted copper, nothing ripped) the output is the committed route-frozen.json byte for byte:
  python build/kicad/boards/CTRL/freeze/freeze_route.py --from-frozen --check
  python build/kicad/boards/CTRL/freeze/freeze_route.py --from-frozen --renet --check
The nets of the router-ignored classes of the spec (router.ignore_net_classes, CTRL.kicad_pro patterns) are never routed here.
CI/model input only: the CI route run with '[pcb-route CTRL]' is the check (KiCad 10.0.7 DRC); bench gates stay OPEN.
"""
import collections, hashlib, importlib.util, json, math, time
from pathlib import Path

import model as M
import fin as F
import plane as PL
from model import cb

HERE = Path(__file__).resolve().parent
BOARD = HERE.parent / 'CTRL.kicad_pcb'
OUT = HERE.parent / 'route-frozen.json'
NEVER = {'GND', 'E3_FAN5', 'E3_BLOWER_GND'}  # scripted classes (SCRIPTED_GND, SCRIPTED_PWR3A)
FP_KEEPOUT_REFS = {'U305'}  # footprints with keepout zones (the Pico TP7 pad keepouts)
MOVE_TOL = 0.002  # mm: KiCad keeps pad positions on its own grid (U315.1 at 24.188 against 24.1875 computed)
K = lambda x, y: (round(x + 100, 4), round(244 - y, 4))  # board mm -> KiCad mm (frame of pcb/board_gen.py)
B = lambda p: [round(p[0] - 100.0, 4), round(244.0 - p[1], 4)]


def load_make_spec():
    loader = importlib.util.spec_from_file_location('ctrl_make_spec', HERE.parent / 'make_spec.py')
    ms = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(ms)
    return ms


def current_spec(ms):
    """Pads, scripted copper (before the frozen copper and its drops) and the guard of the spec make_spec.py makes now."""
    got = {}

    def hook(cu, log):
        got['tracks'] = [dict(t) for t in cu.tracks]
        got['vias'] = [dict(v) for v in cu.vias]
        got['guard'] = ms.frozen_guard(cu)
        got['pads'] = list(cu.inp.pads)
        got['keepouts'] = list(cu.inp.keepouts)
    ms.frozen_copper = hook
    spec_text, project_text, _cu, _skipped = ms.build(lambda *a: None)
    got['spec'], got['project'] = json.loads(spec_text), json.loads(project_text)
    got['netclass_guard'] = ms.netclass_guard
    return got


def to_kicad(shape):
    """A make_spec pad shape (check_boards shapes, board mm, y up) in KiCad mm (y down)."""
    if isinstance(shape, cb.Capsule):
        a, b = K(shape.x1, shape.y1), K(shape.x2, shape.y2)
        return cb.Capsule(a[0], a[1], b[0], b[1], shape.r)
    if isinstance(shape, cb.Multi):
        return cb.Multi([to_kicad(s) for s in shape.shapes])
    return cb.Poly([K(x, y) for x, y in shape.pts])


def sync_pads(m, pads, log, renet_in_place=False):
    """Replace the board pads of every ref that moved or changed nets by the pads make_spec places now. Returns the refs.
    With renet_in_place (--renet) a ref whose pads did not move and only changed nets keeps the exact board pad shapes."""
    board = collections.defaultdict(list)
    for it in m.items:  # copper pads and holes; paste-only apertures (no copper layer) do not count
        if it.ref and (it.kind == 'npth' or (it.kind == 'pad' and it.layers)):
            board[it.ref].append(it)
    spec = collections.defaultdict(list)
    for p in pads:
        spec[p['ref']].append(p)

    def key(kind, number, net):
        return ('npth', '', None) if kind in ('npth', 'np_thru_hole') else ('pad', str(number), net)

    def matched(old, new):
        if len(old) != len(new):
            return False
        left = list(new)
        for o in old:
            hit = [n for n in left if key(o.kind, o.pad, o.net) == key(n['kind'], n['number'], n['net'])
                   and math.hypot(o.at[0] - K(*n['c'])[0], o.at[1] - K(*n['c'])[1]) <= MOVE_TOL]
            if not hit:
                return False
            left.remove(hit[0])
        return True

    def same_place(old, new):
        """Same pads at the same places, only nets differ: (board pad, spec pad) pairs, else None."""
        if len(old) != len(new):
            return None
        left, pairs = list(new), []
        for o in old:
            hit = [n for n in left if key(o.kind, o.pad, None)[:2] == key(n['kind'], n['number'], None)[:2]
                   and math.hypot(o.at[0] - K(*n['c'])[0], o.at[1] - K(*n['c'])[1]) <= MOVE_TOL]
            if not hit:
                return None
            left.remove(hit[0])
            pairs.append((o, hit[0]))
        return pairs
    changed = []
    for ref in sorted(set(board) | set(spec)):
        old, new = board.get(ref, []), spec.get(ref, [])
        if not new and all(o.kind == 'npth' for o in old):
            continue  # board-only hole footprints (H1-H6, from the contract holes)
        if matched(old, new):
            continue
        changed.append(ref)
        pairs = same_place(old, new) if renet_in_place else None
        if pairs:  # --renet: the part did not move, only pad nets changed: keep the exact board pad shapes
            for o, n in pairs:
                if o.kind == 'pad':
                    o.net = n['net']
            log(f'  pads of {ref}: nets taken from the spec, exact board shapes kept')
            continue
        if ref in FP_KEEPOUT_REFS:
            raise SystemExit(f'incremental: {ref} has footprint keepouts (model.py reads them from the board); moving it is not modelled')
        for it in old:
            m.remove(it)
        for p in new:
            npth = p['kind'] == 'np_thru_hole'
            m.add(M.Item(kind='npth' if npth else 'pad', net=None if npth else p['net'], layers=list(M.LAYERS) if npth else
                         [l for l in p['layers'] if l in M.LAYERS], shape=to_kicad(p['shape']), ref=ref, pad=p['number'],
                         at=K(*p['c']), drill=(p['drill'][0] if p['drill'] else 0.0), locked=True, src='pad'))
        log(f'  pads of {ref} taken from the spec ({len(old)} on the board, {len(new)} now)')
    return changed


def frozen_items(m, doc):
    """Add the frozen copper as soft items tagged with their record."""
    for k, (net, layer, width, path) in enumerate(doc['router_tracks']):
        pts = [K(*p) for p in path]
        for a, b in zip(pts, pts[1:]):
            m.add_track(net, layer, width, a, b, locked=True, src='router', tag=('router_tracks', k))
    for k, (net, layer, width, path) in enumerate(doc['completion_tracks']):
        pts = [K(*p) for p in path]
        for a, b in zip(pts, pts[1:]):
            m.add_track(net, layer, width, a, b, locked=True, src='router', tag=('completion_tracks', k))
    for key in ('router_vias', 'completion_vias'):
        for k, (net, x, y, d, drill) in enumerate(doc[key]):
            m.add_via(net, K(x, y), d, drill, locked=True, src='router', tag=(key, k))


def build_model(board, doc, cur, log, renet=False):
    m = M.Model(str(board))
    for it in m.items:  # the board copper: scripted, frozen and Freerouting's redundant wires; rebuilt below
        if it.kind in ('track', 'via'):
            m.remove(it)
    moved = sync_pads(m, cur['pads'], log, renet_in_place=renet)
    drop = {kind: set(doc['drop_scripted'][kind]) for kind in ('tracks', 'vias')}
    for t in cur['tracks']:
        if t['id'] in drop['tracks']:
            continue
        pts = [K(*p) for p in t['path']]
        for a, b in zip(pts, pts[1:]):
            m.add_track(t['net'], t['layer'], t['width_mm'], a, b, locked=True, src='scripted')
    for v in cur['vias']:
        if v['id'] in drop['vias']:
            continue
        m.add_via(v['net'], K(*v['at']), v['diameter_mm'], v['drill_mm'], locked=True, src='scripted')
    frozen_items(m, doc)
    return m, moved


def renet_frozen(m, log):
    """--renet (W2 CTRL-4 PROTECT study): a net split by a new part. An island of frozen copper of net N (frozen items of N
    joined to each other) that touches pads or scripted copper of exactly one net M != N, and none of N, takes the net M:
    the frozen branches follow the pads and scripted pieces they were routed to. Returns {(N, M): items}."""
    soft = [it for it in m.items if it.alive and it.src == 'router' and it.kind in ('track', 'via')]
    by_net = collections.defaultdict(list)
    for it in soft:
        by_net[it.net].append(it)
    done = collections.Counter()
    for net, items in sorted(by_net.items(), key=lambda kv: str(kv[0])):
        ids = {it.id: it for it in items}
        parent = {i: i for i in ids}

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        hard_nets = collections.defaultdict(set)
        for it in items:
            for lay in it.layers:
                bb = (it.bbox[0] - 0.01, it.bbox[1] - 0.01, it.bbox[2] + 0.01, it.bbox[3] + 0.01)
                for ot in m.near(lay, bb):
                    if ot.id == it.id or not ot.alive:
                        continue
                    if ot.id in ids:
                        if find(ot.id) != find(it.id) and M.touches(it, ot):
                            parent[find(ot.id)] = find(it.id)
                    elif ot.kind in ('pad', 'track', 'via') and ot.src in ('pad', 'scripted') and ot.net and M.touches(it, ot):
                        hard_nets[it.id].add(ot.net)
        groups = collections.defaultdict(list)
        for i in ids:
            groups[find(i)].append(ids[i])
        for members in groups.values():
            nets = set().union(*(hard_nets[it.id] for it in members))
            if len(nets) == 1 and net not in nets:
                new = next(iter(nets))
                for it in members:
                    it.net = new
                done[(net, new)] += len(members)
    for (a, b), n in sorted(done.items()):
        log(f'  renet: {n} frozen items {a} -> {b}')
    return dict(done)


def scripted_class_nets(cur):
    """Nets of the router-ignored classes of the spec make_spec.py makes now (router.ignore_net_classes, CTRL.kicad_pro
    patterns): complete from the scripted copper, never routed here (W2 CTRL-4: E3_FAN5_P joined GND, E3_FAN5 and
    E3_BLOWER_GND)."""
    ignored = set(cur['spec']['router'].get('ignore_net_classes', []))
    return {p['pattern'] for p in cur['project']['net_settings']['netclass_patterns'] if p['netclass'] in ignored}


def frozen_conflicts(m):
    """Frozen items that break a clearance against what is there now (pads, scripted copper, keepouts, edges)."""
    out = []
    for it in m.items:
        if not (it.alive and it.src == 'router'):
            continue
        if it.kind == 'track':
            mg, why = m.track_margin(it.net, it.layers[0], it.width, it.a, it.b, ignore={it.id})
        else:
            mg, why = m.via_margin(it.net, it.at, it.size, it.drill, ignore={it.id})
            if why and why.startswith('own pad'):
                continue  # router vias in their own SMD pad were accepted by KiCad on the frozen board
        if mg < -0.0005:
            out.append((it, round(mg, 4), why))
    return out


def chains(segs):
    """Polylines through segments (the chaining of freeze_route.py)."""
    import freeze_route as FR
    return FR.chains(segs)


def snap_points(segs, centres, tol=3e-4):
    """Board-mm segments after rounding: ends within tol of a via centre take the centre, ends within tol of each other
    take one value, and segments that become a point are dropped (a 0.0001 mm piece reads as a dangling track in KiCad)."""
    reps = [tuple(c) for c in centres]
    out = []

    def snap(p):
        for r in reps:
            if abs(p[0] - r[0]) <= tol and abs(p[1] - r[1]) <= tol:
                return r
        reps.append(tuple(p))
        return tuple(p)
    for a, b in segs:
        a, b = snap(tuple(a)), snap(tuple(b))
        if a != b:
            out.append((a, b))
    return out


def export(m, doc, guard, history):
    """The new route-frozen.json document: untouched records verbatim, changed records re-chained, new copper appended."""
    alive = collections.defaultdict(list)
    loose = collections.defaultdict(list)  # (list, net, layer, width) -> segments without an intact record
    vias = {'router_vias': [], 'completion_vias': []}
    for it in m.items:
        if not it.alive or it.kind not in ('track', 'via'):
            continue
        if it.src == 'router' and it.tag:
            alive[it.tag].append(it)
        elif it.src in ('router', 'new'):
            if it.kind == 'track':
                loose[('completion_tracks', it.net, it.layers[0], round(it.width, 4))].append((B(it.a), B(it.b)))
            else:
                vias['completion_vias'].append([it.net] + B(it.at) + [round(it.size, 4), round(it.drill, 4)])
    tracks = {'router_tracks': [], 'completion_tracks': []}
    for key in tracks:
        for k, rec in enumerate(doc[key]):
            segs = alive.get((key, k), [])
            if len(segs) == len(rec[3]) - 1:
                tracks[key].append(rec if segs[0].net == rec[0] else [segs[0].net] + rec[1:])  # --renet keeps the record
            elif segs:
                for it in segs:
                    loose[(key, it.net, it.layers[0], round(it.width, 4))].append((B(it.a), B(it.b)))
    for key in vias:
        for k, rec in enumerate(doc[key]):
            if alive.get((key, k)):
                it = alive[(key, k)][0]
                vias[key].append(rec if it.net == rec[0] else [it.net] + rec[1:])
    vcentre = collections.defaultdict(list)
    for it in m.items:
        if it.alive and it.kind == 'via':
            vcentre[it.net].append(B(it.at))
    for (key, net, layer, w), segs in sorted(loose.items()):
        for path in chains(snap_points(segs, vcentre[net])):
            tracks[key].append([net, layer, w, [list(p) for p in path]])
    for key in tracks:
        tracks[key].sort()
    for key in vias:
        vias[key].sort()
    out = {}
    for key in doc:
        if key == 'guard':
            out[key] = guard
        elif key == 'segments':
            out[key] = {'new': sum(len(r[3]) - 1 for r in tracks['completion_tracks']),
                        'router': sum(len(r[3]) - 1 for r in tracks['router_tracks'])}
        elif key in tracks:
            out[key] = tracks[key]
        elif key in vias:
            out[key] = vias[key]
        elif key == 'increments' and key in out:
            continue  # this run's record is already appended (after drop_scripted); keep the key order of the base
        else:
            out[key] = doc[key]
        if key == 'drop_scripted' and history:
            out['increments'] = doc.get('increments', []) + [history]
    return out


def power_vias(nets):
    """W2 CTRL-5 (review RV4-E-4): vias per layer change of every outer-only (power-class) net from its protective current in
    pcb/generated/netclasses.json and the project via fit (fin.vias_per_change); 1 for a net without a current entry."""
    nc = json.loads((HERE.parents[4] / 'pcb/generated/netclasses.json').read_text(encoding='utf-8'))
    fit = nc['formulas']['via']['current_a_dt20']
    return {n: F.vias_per_change(nc['nets'][n]['inputs']['protective_a'], fit) if n in nc['nets'] else 1 for n in nets}


def outer_only_nets(cur):
    """Nets of the classes the spec make_spec.py makes now keeps on the outer layers (router.class_layers, CTRL.kicad_pro
    patterns)."""
    outer = {c for c, lays in cur['spec']['router'].get('class_layers', {}).items() if set(lays) <= {'F.Cu', 'B.Cu'}}
    return {p['pattern'] for p in cur['project']['net_settings']['netclass_patterns'] if p['netclass'] in outer}


def t_junctions(m, log):
    """Explicit joints for new track ends that lie on the body of another track of the net (route run 43276220883: KiCad
    flagged such an end, 0.012 mm off the other centre line, as track_dangling): the other track is split at the
    projection of the end and the end moves onto it (after the exact clearance check)."""
    fixed = 0
    for it in list(m.items):
        if not (it.alive and it.kind == 'track' and (it.src == 'new' or (it.src == 'router' and it.tag is None))):
            continue  # copper this run made (the retry relabels it 'router' without a record tag)
        for e in (it.a, it.b):
            if not it.alive:
                break
            o = it.b if e == it.a else it.a
            lay = it.layers[0]
            near = [q for q in m.near(lay, (e[0] - 0.5, e[1] - 0.5, e[0] + 0.5, e[1] + 0.5)) if q.alive and q.net == it.net and q.id != it.id]
            if any(q.kind in ('pad', 'via') and q.shape.dist(*e) <= 1e-4 for q in near):
                continue
            if any(q.kind == 'track' and min(math.hypot(e[0] - c[0], e[1] - c[1]) for c in (q.a, q.b)) <= 1e-4 for q in near):
                continue
            host = [q for q in near if q.kind == 'track' and M.seg_dist(e[0], e[1], q.a[0], q.a[1], q.b[0], q.b[1]) <= q.width / 2 + 1e-4
                    and min(math.hypot(o[0] - c[0], o[1] - c[1]) for c in (q.a, q.b)) > 1e-4]
            if not host:
                continue
            q = host[0]
            n_before = len(m.items)
            local = lambda: [x for x in m.near(lay, (e[0] - 1, e[1] - 1, e[0] + 1, e[1] + 1))
                             if x.alive and x.kind == 'track' and x.net == it.net]
            loose_before = sum(1 for x in local() for c in (x.a, x.b) if not F.end_joined(m, x, c, x.net))
            dx, dy = q.b[0] - q.a[0], q.b[1] - q.a[1]
            L2 = dx * dx + dy * dy
            t = max(0.0, min(1.0, ((e[0] - q.a[0]) * dx + (e[1] - q.a[1]) * dy) / L2)) if L2 > 0 else 0.0
            j = (round(q.a[0] + t * dx, 6), round(q.a[1] + t * dy, 6))
            if min(math.hypot(j[0] - c[0], j[1] - c[1]) for c in (q.a, q.b)) <= 1e-3:
                j = q.a if math.hypot(j[0] - q.a[0], j[1] - q.a[1]) <= 1e-3 else q.b
            else:
                m.remove(q)
                m.add_track(q.net, lay, q.width, q.a, j, src='new')
                m.add_track(q.net, lay, q.width, j, q.b, src='new')
            mg, why = m.track_margin(it.net, lay, it.width, o, j, ignore={it.id})
            if mg < -0.0005:
                raise RuntimeError(f't-junction of {it.net} at {e}: {mg:.3f} {why}')
            old_it = it
            m.remove(it)
            it = m.add_track(it.net, lay, it.width, o, j, src='new')
            if sum(1 for x in local() for c in (x.a, x.b) if not F.end_joined(m, x, c, x.net)) > loose_before:
                for x in m.items[n_before:]:  # the joint would leave another end loose: undo it
                    x.alive = False
                old_it.alive = True
                q.alive = True
                it = old_it
                continue
            fixed += 1
    log(f'explicit t-junctions: {fixed}')
    return fixed


def segments_of(doc):
    out = set()
    for key in ('router_tracks', 'completion_tracks'):
        for net, layer, width, path in doc[key]:
            for a, b in zip(path, path[1:]):
                out.add((net, layer, width) + tuple(sorted((tuple(a), tuple(b)))))
    return out


def copper_diff(old, new):
    """Copper the increment added and removed (segment by segment against the base file), mm per layer, and L2 per net."""
    a, b = segments_of(old), segments_of(new)
    length = lambda s: math.hypot(s[3][0] - s[4][0], s[3][1] - s[4][1])
    added, gone, l2 = collections.Counter(), collections.Counter(), collections.Counter()
    for s in b - a:
        added[s[1]] += length(s)
        if s[1] == 'In1.Cu':
            l2[s[0]] += length(s)
    for s in a - b:
        gone[s[1]] += length(s)
    va = {tuple(v) for k in ('router_vias', 'completion_vias') for v in old[k]}
    vb = {tuple(v) for k in ('router_vias', 'completion_vias') for v in new[k]}
    return {'added_copper_mm': {k: round(v, 1) for k, v in sorted(added.items())},
            'removed_copper_mm': {k: round(v, 1) for k, v in sorted(gone.items())},
            'added_vias': len(vb - va), 'removed_vias': len(va - vb),
            'added_l2_mm': {k: round(v, 1) for k, v in sorted(l2.items())}}


def flagged_frozen(m, skip=()):
    """Frozen tracks the exact checks of freeze_route.verify flag although no change of this run touches them (W2 CTRL-4,
    route run 43314567534): a dangling end (KiCad track_dangling: a 0.0001 mm E3_ENC2_B piece left where an earlier
    increment removed the via it ended in) or an end inside a scripted via off its centre that no track of the net joins to
    the centre (KiCad track_not_centered_on_via: an L2 E3_FAN_PG piece inside the scripted Q304 gate via). They are removed
    and their nets pruned and joined again like the touched nets; with none (the committed route) nothing changes."""
    ends = collections.defaultdict(list)
    for it in m.items:
        if it.alive and it.kind == 'track':
            for e, o in ((it.a, it.b), (it.b, it.a)):
                ends[(it.net, round(e[0], 5), round(e[1], 5))].append(o)
    out = []
    for it in m.items:
        if not (it.alive and it.kind == 'track' and it.src == 'router') or it.net in skip:
            continue
        bad = not all(F.end_joined(m, it, e, it.net) for e in (it.a, it.b))
        for e in (it.a, it.b):
            if bad:
                break
            for v in m.near(it.layers[0], (e[0] - 0.5, e[1] - 0.5, e[0] + 0.5, e[1] + 0.5)):
                if v.kind == 'via' and v.net == it.net and v.src == 'scripted' and v.shape.dist(*e) <= 0 \
                        and math.hypot(e[0] - v.at[0], e[1] - v.at[1]) > 1e-4 \
                        and not any(math.hypot(o[0] - v.at[0], o[1] - v.at[1]) <= 1e-4
                                    for o in ends[(it.net, round(e[0], 5), round(e[1], 5))]):
                    bad = True
                    break
        if bad:
            out.append(it)
    return out


def run(args, log=print):
    import freeze_route as FR
    import router as R
    R.PAD_INSET = args.pad_inset
    t0 = time.time()
    out_path = Path(args.out)
    base_path = Path(args.base) if args.base else OUT
    base_text = base_path.read_text(encoding='utf-8')
    doc = json.loads(base_text)
    ms = load_make_spec()
    cur = current_spec(ms)
    log(f'spec: {len(cur["tracks"])} scripted tracks, {len(cur["vias"])} scripted vias ({time.time() - t0:.0f} s)')
    m, moved = build_model(Path(args.board), doc, cur, log, renet=getattr(args, 'renet', False))
    log(f'model: {sum(1 for i in m.items if i.alive and i.src == "router")} frozen items, moved/changed refs {moved} ({time.time() - t0:.0f} s)')
    touched = collections.Counter()
    removed = collections.Counter()
    renamed = renet_frozen(m, log) if getattr(args, 'renet', False) else {}
    for (a, b) in renamed:
        touched[a] += 1
        touched[b] += 1
    scripted_only = set(NEVER) | scripted_class_nets(cur) | set(args.scripted)
    flagged = flagged_frozen(m, scripted_only)  # before the removals below, so it names what the frozen copper had
    for it in flagged:
        m.remove(it)
        removed[it.net] += 1
        touched[it.net] += 1
    for net in list(args.rip) + list(args.scripted):
        for it in m.items:
            if it.alive and it.src == 'router' and it.net == net:
                m.remove(it)
                removed[net] += 1
        touched[net] += 1
    hits = frozen_conflicts(m)
    for it, mg, why in hits:
        m.remove(it)
        removed[it.net] += 1
        touched[it.net] += 1
    log(f'removed frozen items by net: {dict(sorted(removed.items()))} ({len(hits)} clearance conflicts, '
        f'{len(flagged)} flagged by the exact checks)')
    for ref in moved:
        for it in m.items:
            if it.alive and it.kind == 'pad' and it.ref == ref and it.net:
                touched[it.net] += 1
    nets = sorted(n for n in touched if n)
    for n in nets:
        if n not in scripted_only:
            F.prune(m, n)
    fz = F.Finisher(m, log=log)
    widths, default_w = FR.class_widths()
    outer_only = outer_only_nets(cur)
    vias_n = power_vias(outer_only)
    planes0 = PL.split_count(m) if args.plane_guard else 0
    if args.plane_guard:
        log(f'L2 plane components with GND vias before the joins: {planes0}')
    queue = collections.deque(n for n in nets if n not in scripted_only)
    fallback = set(args.l2) | (set(queue) if args.l2_touched else set())
    rounds, failed = 0, []
    while queue and rounds < args.max_rounds:
        net = queue.popleft()
        rounds += 1
        n0, alive0 = len(m.items), [it.id for it in m.items if it.alive]
        if net in outer_only:  # power classes route on F.Cu/B.Cu only (spec router.class_layers; check_boards inner widths)
            ok, ripped = fz.connect(net, l2_bias=None, width=widths.get(net, default_w), layers=('F.Cu', 'B.Cu'),
                                    vias_per_change=vias_n[net])
        else:
            ok, ripped = fz.connect(net, l2_bias=FR.L2_BIAS if net in fallback else None, width=widths.get(net, default_w))
        if args.plane_guard and any(it.alive and it.kind == 'track' and 'In1.Cu' in it.layers for it in m.items[n0:])                 and PL.split_count(m) > planes0:
            # the L2 links of this join split the GND plane: undo the join and join the net again without L2
            for it in m.items[n0:]:
                it.alive = False
            for i in alive0:
                m.items[i].alive = True
            log(f'{net}: L2 link would split the GND plane, joined again without L2')
            ok, ripped = fz.connect(net, l2_bias=None, width=widths.get(net, default_w),
                                    layers=('F.Cu', 'B.Cu') if net in outer_only else ('F.Cu', 'In2.Cu', 'B.Cu'),
                                    vias_per_change=vias_n.get(net, 1))
        log(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)')
        if not ok and net not in failed:
            failed.append(net)
        for n in ripped:
            touched[n] += 1
            if n in scripted_only:
                raise SystemExit(f'incremental: ripped scripted-only net {n}')
            if n not in queue:
                queue.append(n)
        if args.l2_cascade:
            fallback |= set(ripped)
        if not queue and failed and args.retry:
            # nets that found no path go once more at the end (the copper around them has changed), L2 allowed if --retry-l2
            queue.extend(failed)
            fallback |= set(failed) if args.retry_l2 else set()
            if args.retry_rip_new:
                # the copper this run added becomes rippable too (it goes to the completion lists either way)
                for it in m.items:
                    if it.alive and it.src == 'new':
                        it.src = 'router'
            failed, args.retry = [], False
            log(f'retry: {list(queue)}')
    for n in sorted(n for n in touched if n):
        if n not in scripted_only:
            F.prune(m, n)
    t_junctions(m, log)
    open_, bad = FR.verify(m)
    planes = PL.split_count(m)
    if planes > 1:
        bad.append(('L2 GND plane split', planes, 'components with GND vias'))
    log(f'open connections {open_}, clearance/dangling problems {len(bad)}, L2 plane components {planes}')
    for b_ in bad[:20]:
        log('   ', b_)
    if bad or (open_ and not args.allow_open):
        return 1, None
    # W2 CTRL-5 (review RV4-E-4): the guard also covers the net classes of the nets that keep frozen copper
    guard = dict(cur['guard'])
    guard['netclass_sha256'] = cur['netclass_guard']({it.net for it in m.items if it.alive and it.src in ('router', 'new')
                                                      and it.kind in ('track', 'via') and it.net})
    changed = bool(moved or removed or renamed or guard != doc['guard'] or fz.records)
    history = None
    if changed:
        history = {
            'tool': 'build/kicad/boards/CTRL/freeze/freeze_route.py --from-frozen (W2 CTRL-4)',
            'base_sha256': hashlib.sha256(base_text.encode('utf-8')).hexdigest(),
            'board': args.board_label or Path(args.board).name,
            'reason': args.reason or '',
            'rip': sorted(args.rip), 'scripted': sorted(args.scripted), 'moved_refs': moved,
            **({'renamed_frozen_items': {f'{a} -> {b}': n for (a, b), n in sorted(renamed.items())}} if renamed else {}),
            **({'flagged_frozen_items': dict(sorted(collections.Counter(it.net for it in flagged).items()))} if flagged else {}),
            'removed_frozen_items': dict(sorted(removed.items())),
            'rejoined_nets': sorted(fz.tag),
            'left_open_for_freerouting': open_,
        }
    new = export(m, doc, guard, history)
    if history is not None:
        history.update(copper_diff(doc, new))
    text = FR.dump(new)
    log(f'done in {time.time() - t0:.0f} s; changed: {changed}')
    return 0, text
