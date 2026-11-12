"""Incremental re-freeze of the CTRL route (W2 CTRL-4, review RV-CTRLR-5): freeze_route.py --from-frozen. Needs numpy.

The frozen route (route-frozen.json) is valid only for the pads and the scripted copper it was made on (its guard). After a
pad, net or scripted-copper change this mode starts from the committed frozen copper instead of a new Freerouting route:
  1. the board model: pads, keepouts and edges of the committed GENERATED board (build/kicad/boards/CTRL/CTRL.kicad_pcb,
     exact pad shapes); pads whose ref moved or whose net changed in the current spec are replaced by the pads make_spec.py
     places (its check_boards shapes); all copper of that board is dropped;
  2. the copper: the scripted copper make_spec.py makes now (before the frozen copper; drop_scripted applied) as hard,
     locked copper, and the frozen copper of route-frozen.json (router and completion copper) as soft copper;
  3. frozen copper of the nets named with --rip / --scripted is removed, and every frozen item that breaks a clearance
     against the hard copper, a pad, a keepout or an edge is removed (exact check of model.py);
  4. dangling frozen copper of the touched nets is pruned and every touched net with open connections is joined again by
     the grid A* of fin.py (other nets' frozen copper is ripped only where the cheapest path crosses it, and those nets are
     joined again in turn); nets named with --scripted and the scripted classes are never routed here, they must be
     complete from the scripted copper;
  5. every item is checked again (open connections, dangling copper, clearance) and route-frozen.json is written: records
     the step left untouched stay byte for byte as they were, changed router records are re-chained, new copper goes to
     the completion lists; the guard is the one make_spec.py computes now.
With no change (same pads, same scripted copper, nothing ripped) the output is the committed route-frozen.json byte for byte:
  python build/kicad/boards/CTRL/freeze/freeze_route.py --from-frozen --check
CI/model input only: the CI route run with '[pcb-route CTRL]' is the check (KiCad 10.0.7 DRC); bench gates stay OPEN.
"""
import collections, hashlib, importlib.util, json, math, time
from pathlib import Path

import model as M
import fin as F
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
    ms.build(lambda *a: None)
    return got


def to_kicad(shape):
    """A make_spec pad shape (check_boards shapes, board mm, y up) in KiCad mm (y down)."""
    if isinstance(shape, cb.Capsule):
        a, b = K(shape.x1, shape.y1), K(shape.x2, shape.y2)
        return cb.Capsule(a[0], a[1], b[0], b[1], shape.r)
    if isinstance(shape, cb.Multi):
        return cb.Multi([to_kicad(s) for s in shape.shapes])
    return cb.Poly([K(x, y) for x, y in shape.pts])


def sync_pads(m, pads, log):
    """Replace the board pads of every ref that moved or changed nets by the pads make_spec places now. Returns the refs."""
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
    changed = []
    for ref in sorted(set(board) | set(spec)):
        old, new = board.get(ref, []), spec.get(ref, [])
        if not new and all(o.kind == 'npth' for o in old):
            continue  # board-only hole footprints (H1-H6, from the contract holes)
        if matched(old, new):
            continue
        changed.append(ref)
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


def build_model(board, doc, cur, log):
    m = M.Model(str(board))
    for it in m.items:  # the board copper: scripted, frozen and Freerouting's redundant wires; rebuilt below
        if it.kind in ('track', 'via'):
            m.remove(it)
    moved = sync_pads(m, cur['pads'], log)
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
                tracks[key].append(rec)
            elif segs:
                for it in segs:
                    loose[(key, it.net, it.layers[0], round(it.width, 4))].append((B(it.a), B(it.b)))
    for key in vias:
        for k, rec in enumerate(doc[key]):
            if alive.get((key, k)):
                vias[key].append(rec)
    for (key, net, layer, w), segs in sorted(loose.items()):
        for path in chains([(tuple(a), tuple(b)) for a, b in segs]):
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
        else:
            out[key] = doc[key]
        if key == 'drop_scripted' and history:
            out['increments'] = doc.get('increments', []) + [history]
    return out


def run(args, log=print):
    import freeze_route as FR
    t0 = time.time()
    out_path = Path(args.out)
    base_path = Path(args.base) if args.base else OUT
    base_text = base_path.read_text(encoding='utf-8')
    doc = json.loads(base_text)
    ms = load_make_spec()
    cur = current_spec(ms)
    log(f'spec: {len(cur["tracks"])} scripted tracks, {len(cur["vias"])} scripted vias ({time.time() - t0:.0f} s)')
    m, moved = build_model(Path(args.board), doc, cur, log)
    log(f'model: {sum(1 for i in m.items if i.alive and i.src == "router")} frozen items, moved/changed refs {moved} ({time.time() - t0:.0f} s)')
    touched = collections.Counter()
    removed = collections.Counter()
    scripted_only = set(NEVER) | set(args.scripted)
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
    log(f'removed frozen items by net: {dict(sorted(removed.items()))} ({len(hits)} clearance conflicts)')
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
    queue = collections.deque(n for n in nets if n not in scripted_only)
    fallback = set(args.l2)
    rounds = 0
    while queue and rounds < 120:
        net = queue.popleft()
        rounds += 1
        ok, ripped = fz.connect(net, l2_bias=FR.L2_BIAS if net in fallback else None, width=widths.get(net, default_w))
        log(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)')
        for n in ripped:
            touched[n] += 1
            if n in scripted_only:
                raise SystemExit(f'incremental: ripped scripted-only net {n}')
            if n not in queue:
                queue.append(n)
        if args.l2_cascade:
            fallback |= set(ripped)
    for n in sorted(n for n in touched if n):
        if n not in scripted_only:
            F.prune(m, n)
    open_, bad = FR.verify(m)
    log(f'open connections {open_}, clearance/dangling problems {len(bad)}')
    for b_ in bad[:20]:
        log('   ', b_)
    if bad or (open_ and not args.allow_open):
        return 1, None
    changed = bool(moved or removed or cur['guard'] != doc['guard'] or fz.records)
    history = None
    if changed:
        new_l2 = collections.Counter()
        new_mm = collections.Counter()
        for it in m.items:
            if it.alive and it.kind == 'track' and it.src == 'new':
                L = math.hypot(it.a[0] - it.b[0], it.a[1] - it.b[1])
                new_mm[it.layers[0]] += L
                if it.layers[0] == 'In1.Cu':
                    new_l2[it.net] += L
        history = {
            'tool': 'build/kicad/boards/CTRL/freeze/freeze_route.py --from-frozen (W2 CTRL-4)',
            'base_sha256': hashlib.sha256(base_text.encode('utf-8')).hexdigest(),
            'board': args.board_label or Path(args.board).name,
            'reason': args.reason or '',
            'rip': sorted(args.rip), 'scripted': sorted(args.scripted), 'moved_refs': moved,
            'removed_frozen_items': dict(sorted(removed.items())),
            'rejoined_nets': sorted(fz.tag),
            'new_copper_mm': {k: round(v, 1) for k, v in sorted(new_mm.items())},
            'new_l2_mm': {k: round(v, 1) for k, v in sorted(new_l2.items())},
            'left_open_for_freerouting': open_,
        }
    new = export(m, doc, cur['guard'], history)
    text = FR.dump(new)
    log(f'done in {time.time() - t0:.0f} s; changed: {changed}')
    return 0, text
