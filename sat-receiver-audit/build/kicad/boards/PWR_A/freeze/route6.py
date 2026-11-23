#!/usr/bin/env python3
"""Model route of the PWR_A board spec from its inputs (W2 PWR-A closure round 1, probe X). Needs numpy; offline tool, not run by CI.

  python build/kicad/boards/PWR_A/freeze/route6.py [--seed FROZEN] [--order class|short|long] [--tp-max MM] [--out FILE]

freeze6.py harvests the router copper of a CI route run; after a placement change that copper belongs to another board (its guard no
longer matches), and the next CI run would have to route afresh. This tool routes the board in the model instead, so that a placement
change costs one freeze-only CI run:
  1. the board is the spec make_board.py writes with the planned copper and without route-frozen-6l.json (pads at their places, the
     scripted pours, tracks and vias, the GND fan-out, the planned power copper), written as plan6.py's board text and read by the
     freeze model of this directory (model.py, router.py, fin.py);
  2. --seed: the router and completion copper of an earlier route-frozen-6l.json goes on it as router copper (the transactional ratchet
     across a placement change): an item that breaks a clearance on the new board, enters a converter zone 3'/4' of another net, or is
     a power-class piece below its class width or off F.Cu/B.Cu, is removed and its net joined again;
  3. every open net is joined by the freeze6 grid A* (fin.connect_all): power classes on F.Cu/B.Cu at the class width with the necks
     and low-current branches of the exemption policy (freeze6.policy), signals at 0.15 mm on the four routing layers, rip-up of
     router/completion copper (ripped nets queued again); --tp-max: a net whose last open island holds only test points joins by a
     0.25 mm test-point branch on the routing layers up to that length (a test point carries no load current; its place is the PWR-B
     probe window, make_spec.py CUTOUT_KEEP);
  4. dangling pieces are pruned, collinear pieces merged (freeze6.merge_remainders), a track end inside a same-net SMD pad less than half
     its width from the pad edge gets a track to the pad centre (KiCad 10.0.7 connection_width, route run 45062920789), the copper that
     fails the final exact check is dropped, and route-frozen-6l.json is written with the guard of the current inputs.
The CI route run with '[pcb-route PWR_A]' on the result (freeze-only) is the check: KiCad 10.0.7 DRC; bench gates stay OPEN.
"""
import argparse
import collections
import importlib.util
import json
import math
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE.parent / 'route-frozen-6l.json'


def load(name, path):
    ld = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(ld)
    ld.loader.exec_module(mod)
    return mod


def main(argv=None, mb=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--seed', help='an earlier route-frozen-6l.json: its copper as router copper on the new board (ratchet)')
    ap.add_argument('--order', default='class', choices=('class', 'short', 'long'), help='completion order of the open nets')
    ap.add_argument('--soft', default='router', choices=('none', 'router', 'new'),
                    help='what the rip-up may move: nothing, router copper, or router and completion copper')
    ap.add_argument('--rip-wide', action='store_true', help='a rip-up search in the 25 mm box when the 8 mm box has none')
    ap.add_argument('--rounds', type=int, default=600)
    ap.add_argument('--first', default='', help='comma-separated nets joined first')
    ap.add_argument('--tp-max', type=float, default=0.0, help='longest test-point branch, mm (0: none beyond freeze6.BRANCH_MAX)')
    ap.add_argument('--summary', help='also write a short JSON summary here')
    ap.add_argument('--tp-outer', action='store_true', help='freeze6 --tp-outer: the --tp-max test-point branch on F.Cu/B.Cu only')
    # W2 PWR-A closure round 1, combine pass: the probe-Y options of freeze6.py on the model route
    ap.add_argument('--pad-vias', action='store_true', help='freeze6 --pad-vias: a net left open tries again with a via in its SMD pads')
    ap.add_argument('--deep-entry', action='store_true', help='freeze6 --deep-entry: completion tracks end deep inside small pads')
    ap.add_argument('--sense-branches', action='store_true', help='freeze6 --sense-branches: 0.25 mm branches to IC sense/logic pins')
    ap.add_argument('--leave-open', action='append', default=[], metavar='NET', help='a net the model route does not join')
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    t_start = time.time()
    F6 = load('freeze6r', HERE / 'freeze6.py')
    p6 = load('plan6r', HERE / 'plan6.py')  # board_text / pad_shapes (sets R.Grid.covered to the eroded-pad test, as plan6 does)
    M, F = F6.M, F6.F
    K, B = F6.K, F6.B
    if a.deep_entry:  # after plan6 (which sets the eroded-pad test): the deep entry of freeze6 for small pads
        F6.R.Grid.covered = F6.covered_deep
        F6.R.route_link = F6.route_link_deep
    mb = mb or p6.load_make_board()
    spec, inp, problems, nets = mb.build(frozen=False, planned=True)
    if problems:
        raise SystemExit(f'route6: make_board problems: {problems[:10]}')
    proj = json.loads(mb.project_json(inp, nets, inp.scripted))
    path = Path(tempfile.mkdtemp(prefix='route6-')) / 'PWR_A-route6.kicad_pcb'
    path.write_text(p6.board_text(spec, inp, p6.pad_shapes(mb, inp)), encoding='utf-8')
    m = M.Model(str(path))
    fz = F.Finisher(m, log=lambda *x, **k: None)
    width_of = {c['name']: c['track_width'] for c in proj['net_settings']['classes']}
    cls = {p['pattern']: p['netclass'] for p in proj['net_settings']['netclass_patterns']}

    def klass(n):
        return cls.get(n, 'Default')

    def width(n):
        return width_of[klass(n)]

    def layers(n):
        return F6.OUTER if klass(n) in F6.POWER else F6.ROUTING
    never = {'GND'} | set(inp.scripted)
    cz = spec.get('converter_zones') or {}
    F6.CZ_LAYERS[:] = cz.get('layers') or ['F.Cu', 'In1.Cu']
    czones = []
    for _zi, z in sorted((cz.get('zones') or {}).items()):
        x0, y0, x1, y1 = z['rect']
        p, q = K(x0, y1), K(x1, y0)
        czones.append((M.cb.Poly([(p[0], p[1]), (q[0], p[1]), (q[0], q[1]), (p[0], q[1])]), set(z['own_nets'])))
    base_keepouts = list(m.keepouts)

    def zone_keepouts(net):
        return [{'layers': list(F6.CZ_LAYERS), 'poly': poly, 'name': 'converter zone'} for poly, own in czones if net not in own]

    seed_note, seed_run = None, ''
    if a.seed:
        sd = json.loads(Path(a.seed).read_text(encoding='utf-8'))
        seed_run = sd.get('source', {}).get('route_run', '')
        seeded = removed = 0
        svip = {(r['net'], K(*r['at'])) for r in sd.get('via_in_pad', [])}
        for key in ('router_tracks', 'completion_tracks'):
            for net, lay, w, pts in sd[key]:
                if net not in nets or net in never:
                    continue
                for p, q in zip(pts, pts[1:]):
                    m.add_track(net, lay, w, K(*p), K(*q), locked=False, src='router')
                    seeded += 1
        for key in ('router_vias', 'completion_vias'):
            for net, x, y, d, drill in sd[key]:
                if net not in nets or net in never:
                    continue
                m.add_via(net, K(x, y), d, drill, locked=False, src='vip' if (net, K(x, y)) in svip else 'router')
                seeded += 1
        viol = set()
        for it in m.items:  # a seeded via in pad keeps its own check (freeze6.vip_margin)
            if it.alive and it.src == 'vip' and F6.vip_margin(m, it.net, it.at, it.size, it.drill, ignore={it.id})[0] < 0:
                m.remove(it)
                removed += 1
                viol.add(it.net)
        for it in m.items:
            if not (it.alive and it.src == 'router'):
                continue
            if it.kind == 'track':
                mg, _why = m.track_margin(it.net, it.layers[0], it.width, it.a, it.b, ignore={it.id})
            else:
                mg, _why = m.via_margin(it.net, it.at, it.size, it.drill, ignore={it.id})
            bad = mg < -0.0005
            if not bad and czones:
                on = [lay for lay in it.layers if lay in F6.CZ_LAYERS]
                for poly, own in czones:
                    if it.net in own or not on:
                        continue
                    if (M.shape_seg_dist(poly, it.a, it.b) <= it.width / 2) if it.kind == 'track' else (poly.dist(*it.at) <= it.size / 2):
                        bad = True
            if not bad and it.kind == 'track' and klass(it.net) in F6.POWER and \
                    (it.layers[0] not in F6.OUTER or it.width + 1e-6 < width(it.net)):
                bad = True
            if bad:
                m.remove(it)
                removed += 1
                viol.add(it.net)
        for n in sorted({i.net for i in m.items if i.alive and i.src == 'router'} | viol):
            F.prune(m, n, log=lambda *x, **k: None)
        seed_note = {'file': Path(a.seed).name, 'route_run': seed_run, 'items': seeded, 'removed_by_check': removed,
                     'kept': sum(1 for i in m.items if i.alive and i.src == 'router')}
        print('seed:', seed_note, flush=True)
    branch_ok, neck_ok = F6.policy(m)
    open0 = {n: k for n, k in fz.unconnected().items() if n not in never}
    scripted_split = {n: k for n, k in fz.unconnected().items() if n in never and n != 'GND'}
    print(f'model loaded {time.time() - t_start:.0f} s; open nets {len(open0)} ({sum(open0.values())} joins)', flush=True)

    def span(n):
        pts = [i.at for i in m.items if i.alive and i.kind == 'pad' and i.net == n]
        return math.hypot(max(p[0] for p in pts) - min(p[0] for p in pts), max(p[1] for p in pts) - min(p[1] for p in pts)) if pts else 0.0
    first = [n for n in a.first.split(',') if n in open0]
    if a.order == 'short':
        order = sorted(open0, key=lambda n: (span(n), n))
    elif a.order == 'long':
        order = sorted(open0, key=lambda n: (layers(n) != F6.OUTER, -span(n), n))
    else:
        order = sorted(open0, key=lambda n: (layers(n) != F6.OUTER, n))
    order = first + [n for n in order if n not in first]
    left_open = set(a.leave_open)
    order = [n for n in order if n not in left_open]
    queue, rounds, t0 = collections.deque(order), 0, time.time()
    failed, necks, branches = [], [], []
    soft = () if a.soft == 'none' else (('router',) if a.soft == 'router' else ('router', 'new'))
    bk = F6.branch_kind(F6.GRAPH, sense=a.sense_branches)
    while queue and rounds < a.rounds:
        net = queue.popleft()
        rounds += 1
        m.keepouts[:] = base_keepouts + zone_keepouts(net)
        ok, ripped, nk = fz.connect_all(net, width=width(net), layers=layers(net), allow_rip=bool(soft),
                                        neck=(width(net), F6.NECK_MAX, neck_ok) if layers(net) == F6.OUTER else None,
                                        rip_wide=a.rip_wide, soft=soft or ('router',))
        necks += nk
        vips = []
        if not ok and a.pad_vias and layers(net) != F6.OUTER:  # freeze6 --pad-vias: vias in the pads of the walled-in pins, again
            vips = F6.add_pad_vias(m, net)
            if vips:
                ok, ripped2, nk = fz.connect_all(net, width=width(net), layers=layers(net), allow_rip=bool(soft), neck=None,
                                                 rip_wide=a.rip_wide, soft=soft or ('router',))
                ripped += [n for n in ripped2 if n not in ripped]
                necks += nk
        target = (lambda i, net=net: (i.kind == 'track' and i.width + 1e-6 >= width(net)) or (i.kind == 'pad' and i.src == 'zone'))
        if not ok and layers(net) == F6.OUTER:
            for attempt in ((False, True) if a.pad_vias else (False,)):
                if attempt:  # freeze6 --pad-vias: the branch parts get vias in their pads (branches on the routing layers only)
                    vips += F6.add_pad_vias(m, net, refs={i.ref for gr in m.islands(net) for i in gr if i.kind == 'pad'
                                                          and bk(i.ref) in ('TP', 'S') and branch_ok(i.ref, net)})
                okb, br = fz.branch_pass(net, lambda r, net=net: bk(r) is not None and branch_ok(r, net),
                                         lambda refs: max(F6.BRANCH_W[bk(r)] for r in refs),
                                         lambda refs: F6.ROUTING if all(bk(r) in ('TP', 'S') for r in refs) else F6.OUTER,
                                         F6.BRANCH_MAX, target_ok=target)
                branches += br
                ok = ok or okb
                if ok:
                    break
            if not ok and a.tp_max:
                okt, brt = fz.branch_pass(net, lambda r, net=net: r is not None and r.startswith('TP') and branch_ok(r, net),
                                          lambda refs: F6.BRANCH_W['TP'], lambda refs: F6.OUTER if a.tp_outer else F6.ROUTING, a.tp_max,
                                          target_ok=target)
                branches += brt
                ok = ok or okt
        if vips:
            F6.drop_unused_vips(m, net)
        m.keepouts[:] = base_keepouts
        print(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)', flush=True)
        if not ok:
            failed.append(net)
        queue.extend(n for n in ripped if n not in queue and n not in left_open)
    for n in sorted({i.net for i in m.items if i.alive and i.net and i.net not in M.PLANES}):
        F.prune(m, n, srcs=('router', 'new', 'escape'), log=lambda *x, **k: None)
        F6.drop_unused_vips(m, n)
    F6.merge_remainders(m)
    joints = centre_joints(m)
    shorts = drop_short_pieces(m, F6, F)
    open_, bad = F6.verify(m)
    dropped = 0
    if bad:
        dropped = F6.drop_failing_completion(m)[0]
        open_, bad = F6.verify(m)
    open_ = {n: k for n, k in open_.items() if n not in never}
    # the scripted and planned copper (pours drawn as tracks in this model, vias in the bond keep-outs by design) is KiCad-checked by
    # the route run: only the router and completion copper counts here
    bad = [b for b in bad if (isinstance(b[0], float) and b[1] in ('router', 'new', 'escape'))
           or (b[0] in ('short piece', 'track end not on via centre'))]
    print('open', open_, 'violations', len(bad), 'failed', sorted(set(failed)), 'joints', len(joints), flush=True)
    groups = collections.defaultdict(list)
    vias = {'router': [], 'new': []}
    for it in m.items:
        if it.alive and it.src in ('router', 'new', 'escape', 'vip'):
            src = 'new' if it.src in ('escape', 'vip') else it.src
            if it.kind == 'track':
                groups[(src, it.net, it.layers[0], round(it.width, 4))].append((it.a, it.b))
            elif it.kind == 'via':
                vias[src].append([it.net] + B(it.at) + [round(it.size, 4), round(it.drill, 4)])
    tracks, nseg = {'router': [], 'new': []}, collections.Counter()
    for (src, net, lay, w), segs in sorted(groups.items()):
        for pth in F6.chains(segs):
            tracks[src].append([net, lay, w, [B(p) for p in pth]])
            nseg[src] += len(pth) - 1
    for k in vias:
        vias[k].sort()
        tracks[k].sort()
    vip_rec = []  # the vias in pads, as freeze6.py records them (make_board.py via_in_pad)
    for it in m.items:
        if it.alive and it.kind == 'via' and it.src == 'vip':
            pad = next((o for lay in ('F.Cu', 'B.Cu') for o in m.near(lay, it.bbox) if o.kind == 'pad' and o.src == 'pad'
                        and o.net == it.net and o.shape.dist(*it.at) <= 0), None)
            vip_rec.append({'net': it.net, 'at': B(it.at), 'diameter_mm': round(it.size, 4), 'drill_mm': round(it.drill, 4),
                            'pad': f'{pad.ref}.{pad.pad}' if pad else None,
                            'margin_mm': round(F6.vip_margin(m, it.net, it.at, it.size, it.drill, ignore={it.id})[0], 4)})
    vip_rec.sort(key=lambda r: (r['pad'] or '', r['net']))
    guard = mb.frozen_guard(inp, spec['pre_route']['tracks'], spec['pre_route']['vias'])
    doc = {
        'schema': 'srrx-pwra-frozen-route-v1',
        'label': 'CI/model input for pcb/boards/PWR_A.json (W2 PWRJ-LAYERS6, 6 layers); not a hardware PASS; bench gates OPEN',
        'source': {'route_run': (f'{seed_run} (seed, carried by the model route)' if seed_run else 'none (model route)'),
                   'harvest': 'build/kicad/boards/PWR_A/freeze/route6.py: model route of the spec (W2 PWR-A closure probe X)',
                   'args': {k: v for k, v in vars(a).items() if k not in ('out', 'summary')}, 'seed': seed_note},
        'result': {'open': open_, 'violations': len(bad), 'failed_nets': sorted(set(failed)), 'centre_joints': len(joints),
                   'dropped': dropped, 'short_pieces_removed': shorts},
        'necks': sorted(necks, key=lambda r: (r['ref'], r['pad'], r['to'])),
        'branches': sorted(branches, key=lambda r: (r['net'], r['refs'])),
        'guard': guard,
        'segments': dict(nseg),
        'router_tracks': tracks['router'], 'router_vias': vias['router'],
        'completion_tracks': tracks['new'], 'completion_vias': vias['new'],
        **({'via_in_pad': vip_rec} if vip_rec else {}),
    }
    Path(a.out).write_text(F6.dump(doc), encoding='utf-8', newline='\n')
    summ = {'open_nets': len(open_), 'open_joins': sum(open_.values()), 'open': open_, 'violations': len(bad),
            'power_open': {n: k for n, k in open_.items() if klass(n) in F6.POWER},
            'by_class': dict(collections.Counter(klass(n) for n in open_)), 'scripted_split': scripted_split,
            'joints': len(joints), 'dropped': dropped, 'seed': seed_note, 'segments': dict(nseg),
            'vias': {k: len(v) for k, v in vias.items()}, 'via_in_pad': [r['pad'] for r in vip_rec], 'seconds': round(time.time() - t_start), 'args': vars(a)}
    if a.summary:
        Path(a.summary).write_text(json.dumps(summ, indent=1), encoding='utf-8')
    print('SUMMARY', json.dumps({k: summ[k] for k in ('open_nets', 'open_joins', 'violations', 'power_open', 'seconds')}), flush=True)
    return 0 if not open_ and not bad else 1


def drop_short_pieces(m, F6, F):
    """Router/completion pieces shorter than their width with a free end (freeze6.short_pieces: the KiCad 10.0.7 track_dangling
    pattern) are removed and their net pruned, until none is left. Returns the number removed."""
    n = 0
    for _ in range(5):
        found = F6.short_pieces(m)
        if not found:
            break
        keys = {(f[1], tuple(f[2]), f[3]) for f in found}
        for t in list(m.items):
            if t.alive and t.kind == 'track' and t.src in ('router', 'new', 'escape') and math.dist(t.a, t.b) < t.width:
                for e in (t.a, t.b):
                    if (t.net, tuple(F6.B(e)), t.layers[0]) in keys:
                        m.remove(t)
                        n += 1
                        break
        for net in sorted({f[1] for f in found}):
            F.prune(m, net, srcs=('router', 'new', 'escape'), log=lambda *x, **k: None)
    return n


def centre_joints(m):
    """A router/completion track end inside a same-net SMD pad less than half its width from the pad edge gets a track of its width
    to the pad centre (KiCad 10.0.7 connection_width: a track that enters a pad over its corner, route run 45062920789)."""
    added = []
    for t in list(m.items):
        if not (t.alive and t.kind == 'track' and t.src in ('router', 'new')):
            continue
        lay = t.layers[0]
        for e in (t.a, t.b):
            for p in m.near(lay, (e[0] - 0.01, e[1] - 0.01, e[0] + 0.01, e[1] + 0.01)):
                if not (p.alive and p.kind == 'pad' and p.src == 'pad' and p.net == t.net and not p.drill):
                    continue
                if p.shape.dist(*e) > 0:
                    continue
                x0, y0, x1, y1 = p.bbox
                depth = min(e[0] - x0, x1 - e[0], e[1] - y0, y1 - e[1])
                c = ((x0 + x1) / 2, (y0 + y1) / 2)
                if depth + 1e-6 >= t.width / 2 or math.dist(e, c) < 1e-4:
                    continue
                mg, _w = m.track_margin(t.net, lay, t.width, e, c)
                if mg >= 0:
                    m.add_track(t.net, lay, t.width, e, c, src='new')
                    added.append((t.net, f'{p.ref}.{p.pad}'))
    return added


if __name__ == '__main__':
    raise SystemExit(main())
