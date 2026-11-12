#!/usr/bin/env python3
"""Freeze a PWR_B route run and complete it (W2 PWRB-R route study). Needs numpy; offline tool, not run by CI.

  python build/kicad/boards/PWR_B/freeze/freeze_route.py --artifact <unzipped pcb-regenerated-PWR_B> [--out FILE]

The artifact holds board/PWR_B.kicad_pcb and board/report.json of a route run whose spec is the one make_spec.py makes
without route-frozen.json (the PWR-A cut-outs as copper keep-outs, spec copper_keepouts). The tool
  1. reads the routed board (pads with exact roundrect/custom shapes, tracks, vias, keep-out rule areas, edges; the
     model of build/kicad/boards/CTRL/freeze, W2 CTRL-R / CTRL-4, ported to the PWR_B layers: F.Cu, In2.Cu and B.Cu route
     signals, F.Cu and B.Cu the power classes, In1.Cu is the GND plane);
  2. takes every unlocked track and via as router copper and every locked one as the scripted copper of make_spec.py;
  3. joins every open connection of the autorouted nets by grid A* (0.05 mm grid) on that copper with the exact
     clearance check (board rules 0.15 mm, copper to edge 0.3 mm, hole to hole 0.5 mm, keep-outs, no via in an SMD pad,
     a new path ends at least 0.13 mm inside a pad edge); when no free path exists it rips only the router segments the
     cheapest path crosses and joins those nets again; power classes never leave the outer layers (pcb/check_boards.py
     class_widths);
  4. removes dangling router/completion copper, checks every item again and writes route-frozen.json (router copper as
     routed, completion copper and a guard: SHA256 of the pads, of the scripted copper and of the keep-out rectangles,
     which make_spec.py compares before it uses the frozen copper).
CI/model input only: the CI route run with '[pcb-route PWR_B]' is the check (KiCad 10.0.7 DRC); bench gates stay OPEN.
"""
import argparse, collections, importlib.util, json, math, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model as M  # noqa: E402
import router as R  # noqa: E402
import fin as F  # noqa: E402

OUT = HERE.parent / 'route-frozen.json'
OY = 210.0          # pcb/board_gen.py Frame: KiCad y = 100 + max outline y (110) - board y
SIGNAL_LAYERS = ('F.Cu', 'In2.Cu', 'B.Cu')  # Default class (In2.Cu: signals and a GND pour, spec layers.plan)
POWER_LAYERS = ('F.Cu', 'B.Cu')             # power classes stay outer (router.class_layers, check_boards class_widths)
K = lambda x, y: (round(x + 100, 4), round(OY - y, 4))  # board mm -> KiCad mm
B = lambda p: [round(p[0] - 100.0, 4), round(OY - p[1], 4)]


def load_make_spec():
    loader = importlib.util.spec_from_file_location('pwrb_make_spec', HERE.parent / 'make_spec.py')
    ms = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(ms)
    return ms


def current(ms):
    """Inputs, scripted copper and guard of the spec make_spec.py makes now (before the frozen copper)."""
    inp = ms.Inputs()
    anchors, missing, pins, parts, tracks, vias, exempt = ms.build(inp)
    return {'guard': ms.frozen_guard(inp, parts, tracks, vias), 'tracks': tracks, 'vias': vias,
            'never': set(ms.SCRIPTED_CLASSES), 'scripted_nets': set(pins['scripted_nets'])}


def class_widths():
    """Track width and class per net from the committed PWR_B.kicad_pro (net class patterns; Default 0.15 mm)."""
    pro = json.loads((HERE.parent / 'PWR_B.kicad_pro').read_text(encoding='utf-8'))['net_settings']
    width = {c['name']: c['track_width'] for c in pro['classes']}
    return ({p['pattern']: width[p['netclass']] for p in pro['netclass_patterns']},
            {p['pattern']: p['netclass'] for p in pro['netclass_patterns']}, width['Default'])


def verify(m):
    """Open connections, dangling copper and clearance of every track and via (exact checks)."""
    nets = sorted({i.net for i in m.items if i.alive and i.net})
    open_ = {n: len(m.islands(n)) - 1 for n in nets if len(m.islands(n)) > 1}
    bad = [('dangling',) + d for d in F.dangling(m)]
    ends = collections.defaultdict(list)
    for it in m.items:
        if it.alive and it.kind == 'track':
            for e, o in ((it.a, it.b), (it.b, it.a)):
                ends[(it.net, round(e[0], 5), round(e[1], 5))].append(o)
    for it in m.items:  # KiCad 10 track_not_centered_on_via (new copper; the router's own pattern is accepted)
        if not (it.alive and it.kind == 'track'):
            continue
        for e in (it.a, it.b):
            for v in m.near(it.layers[0], (e[0] - 0.5, e[1] - 0.5, e[0] + 0.5, e[1] + 0.5)):
                if v.kind != 'via' or v.net != it.net or (it.src != 'new' and v.src != 'new'):
                    continue
                if v.shape.dist(*e) <= 0 and math.hypot(e[0] - v.at[0], e[1] - v.at[1]) > 1e-4:
                    if not any(math.hypot(o[0] - v.at[0], o[1] - v.at[1]) <= 1e-4 for o in ends[(it.net, round(e[0], 5), round(e[1], 5))]):
                        bad.append(('track end not on via centre', it.net, e, 'via', v.at, v.src))
    for it in m.items:
        if not it.alive:
            continue
        if it.kind == 'track':
            mg, why = m.track_margin(it.net, it.layers[0], it.width, it.a, it.b, ignore={it.id})
        elif it.kind == 'via':
            mg, why = m.via_margin(it.net, it.at, it.size, it.drill, ignore={it.id})
            if why and why.startswith('own pad') and it.src != 'new':
                continue
        else:
            continue
        if mg < -0.0005:
            bad.append((round(mg, 4), it.src, it.kind, it.net, why, it.layers[0] if it.kind == 'track' else '*',
                        B(it.a if it.kind == 'track' else it.at)))
    return open_, bad


def chains(segs):
    key = lambda p: (round(p[0], 6), round(p[1], 6))
    adj = collections.defaultdict(list)
    for i, (a, b) in enumerate(segs):
        adj[key(a)].append(i)
        adj[key(b)].append(i)
    used = [False] * len(segs)
    out = []

    def walk(i, p):
        path = [p]
        while True:
            used[i] = True
            a, b = segs[i]
            q = b if key(a) == key(p) else a
            path.append(q)
            nxt = [j for j in adj[key(q)] if not used[j]]
            if len(adj[key(q)]) != 2 or not nxt:
                return path
            i, p = nxt[0], q
    for i, (a, b) in enumerate(segs):
        if not used[i]:
            for p in (a, b):
                if len(adj[key(p)]) != 2:
                    out.append(walk(i, p))
                    break
    for i, (a, b) in enumerate(segs):
        if not used[i]:
            out.append(walk(i, a))
    return out


def dump(doc):
    lines = ['{']
    keys = list(doc)
    for n, k in enumerate(keys):
        v, end = doc[k], (',' if n < len(keys) - 1 else '')
        if isinstance(v, list):
            lines.append(f'  {json.dumps(k)}: [')
            lines += ['    ' + json.dumps(r, ensure_ascii=False, separators=(', ', ': ')) + (',' if i < len(v) - 1 else '')
                      for i, r in enumerate(v)]
            lines.append('  ]' + end)
        else:
            lines.append(f'  {json.dumps(k)}: ' + json.dumps(v, ensure_ascii=False) + end)
    lines.append('}')
    return '\n'.join(lines) + '\n'


def spec_keepouts(ms):
    """The copper_keepouts rule areas make_spec.py makes now, as model keepouts (KiCad mm): each PWR-A cut-out rectangle
    grown by the copper-to-edge clearance on all four copper layers (the rule areas KO_AREA_* of pcb/board_gen.py)."""
    inp = ms.Inputs()
    g = ms.EDGE
    out = []
    for c in inp.cutouts:
        x0, y0, x1, y1 = c['rect']
        pts = [K(x0 - g, y0 - g), K(x1 + g, y0 - g), K(x1 + g, y1 + g), K(x0 - g, y1 + g)]
        out.append({'layers': list(M.LAYERS), 'poly': M.cb.Poly(pts), 'name': f'KO_AREA_{c["ref"]}'})
    return out


def replace_keepouts(m, ms, log=print):
    """--keepouts-from-spec: the board's KO_AREA_* keepouts are replaced by the spec's (a board routed before W2 PWRB-R, or
    on another cut-out list), and every router item that now breaks a keepout or a clearance is removed."""
    m.keepouts = [k for k in m.keepouts if not k['name'].startswith('KO_AREA_')] + spec_keepouts(ms)
    removed = collections.Counter()
    for it in m.items:
        if not (it.alive and it.src == 'router' and it.kind in ('track', 'via')):
            continue
        if it.kind == 'track':
            mg, why = m.track_margin(it.net, it.layers[0], it.width, it.a, it.b, ignore={it.id})
        else:
            mg, why = m.via_margin(it.net, it.at, it.size, it.drill, ignore={it.id})
            if why and why.startswith('own pad'):
                continue
        if mg < -0.0005:
            m.remove(it)
            removed[it.net] += 1
    log(f'keepouts from the spec: {len(spec_keepouts(ms))} areas; router items removed {sum(removed.values())} on {len(removed)} nets')
    return removed


def frozen_to_router(m, cur):
    """Locked board copper that is not scripted copper of the current spec (the frozen copper of a spec that had
    route-frozen.json, for example the pre-route of prefreeze.py) is taken as router copper: harvested, rippable."""
    key = lambda p: (round(p[0], 3), round(p[1], 3))
    segs = set()
    for t in cur['tracks']:
        pts = [K(*p) for p in t['path']]
        for a, b in zip(pts, pts[1:]):
            segs.add((t['net'], t['layer'], frozenset((key(a), key(b)))))
    vias = {(v['net'], key(K(*v['at']))) for v in cur['vias']}
    moved = 0
    for it in m.items:
        if not (it.alive and it.src == 'scripted'):
            continue
        if it.kind == 'track' and (it.net, it.layers[0], frozenset((key(it.a), key(it.b)))) not in segs:
            it.src, moved = 'router', moved + 1
        elif it.kind == 'via' and (it.net, key(it.at)) not in vias:
            it.src, moved = 'router', moved + 1
    return moved


def scripted_matches(m, cur):
    """The locked copper of the board is the scripted copper of the current spec (same segment and via count)."""
    segs = sum(len(t['path']) - 1 for t in cur['tracks'])
    on_board = sum(1 for it in m.items if it.alive and it.kind == 'track' and it.src == 'scripted')
    vias = len(cur['vias'])
    board_vias = sum(1 for it in m.items if it.alive and it.kind == 'via' and it.src == 'scripted')
    return segs == on_board and vias == board_vias, (segs, on_board, vias, board_vias)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--artifact', required=True, help='unzipped pcb-regenerated-PWR_B artifact (board/PWR_B.kicad_pcb, board/report.json)')
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--route-run', type=int, help='route run id of the artifact (default: from the artifact directory name)')
    ap.add_argument('--first', action='append', default=[], metavar='NET', help='join NET before the others (repeatable)')
    ap.add_argument('--max-rounds', type=int, default=150)
    ap.add_argument('--pad-inset', type=float, default=0.13,
                    help='a new path starts or ends at least this far inside a pad edge (KiCad connection_width; default 0.13)')
    ap.add_argument('--allow-open', action='store_true', help='write the result even with open connections (study only)')
    ap.add_argument('--margin-steps', type=float, default=0.25,
                    help='raster margin over the exact clearance in grid steps (default 0.25; 0.75 again after a refused commit)')
    ap.add_argument('--keepouts-from-spec', action='store_true',
                    help="replace the board's KO_AREA_* keep-outs by the spec's and remove the router copper that breaks them")
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    R.PAD_INSET = args.pad_inset
    R.MARGIN_STEPS = args.margin_steps
    art = Path(args.artifact)
    report = json.loads((art / 'board/report.json').read_text(encoding='utf-8'))
    ms = load_make_spec()
    cur = current(ms)
    m = M.Model(str(art / 'board/PWR_B.kicad_pcb'))
    moved = frozen_to_router(m, cur)
    if moved:
        print(f'{moved} locked items of an earlier route-frozen.json taken as router copper')
    ok, counts = scripted_matches(m, cur)
    if not ok:
        raise SystemExit(f'freeze_route: the board locked copper is not the scripted copper of the current spec {counts}: '
                         'route the current spec without route-frozen.json first')
    widths, classes, default_w = class_widths()
    if args.keepouts_from_spec:
        replace_keepouts(m, ms)
        for n in sorted({i.net for i in m.items if i.alive and i.net and i.net not in cur['never']}):
            F.prune(m, n)
    nets = sorted({i.net for i in m.items if i.alive and i.net})
    open0 = {n: len(m.islands(n)) - 1 for n in nets if n not in cur['never'] and len(m.islands(n)) > 1}
    stuck = {n: len(m.islands(n)) - 1 for n in cur['never'] if n in nets and len(m.islands(n)) > 1}
    print('router copper:', sum(1 for i in m.items if i.alive and i.src == 'router' and i.kind == 'track'), 'segments,',
          sum(1 for i in m.items if i.alive and i.src == 'router' and i.kind == 'via'), 'vias; open', open0, 'scripted open', stuck)
    if stuck:
        raise SystemExit(f'freeze_route: scripted nets {stuck} are open on the board; they are never routed here')
    fz = F.Finisher(m)
    order = [n for n in args.first if n in open0] + sorted((n for n in open0 if n not in args.first),
                                                           key=lambda n: (-open0[n], n))
    queue, rounds, t0 = collections.deque(order), 0, time.time()
    failed, plane = [], set()
    while queue and rounds < args.max_rounds:
        net = queue.popleft()
        rounds += 1
        if net in cur['never']:
            raise SystemExit(f'freeze_route: {net} is scripted copper; it is never routed here')
        signal = classes.get(net, 'Default') == 'Default'
        ok, ripped = fz.connect(net, width=widths.get(net, default_w), layers=SIGNAL_LAYERS if signal else POWER_LAYERS)
        print(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)', flush=True)
        if not ok:
            failed.append(net)
        bad = [n for n in ripped if n in cur['never']]
        if bad:
            raise SystemExit(f'freeze_route: ripped scripted nets {bad}')
        queue.extend(n for n in ripped if n not in queue)
    for n in sorted({i.net for i in m.items if i.alive and i.net and i.net != 'GND'}):
        F.prune(m, n)
    open_, bad = verify(m)
    open_ = {n: k for n, k in open_.items() if n != 'GND' or k}
    print('open connections', open_, 'clearance / dangling problems', len(bad), 'failed joins', failed)
    for b_ in bad[:20]:
        print('   ', b_)
    if (open_ or bad) and not args.allow_open:
        return 1
    groups = collections.defaultdict(list)
    vias = {'router': [], 'new': []}
    for it in m.items:
        if it.alive and it.src in ('router', 'new'):
            if it.kind == 'track':
                groups[(it.src, it.net, it.layers[0], round(it.width, 4))].append((it.a, it.b))
            elif it.kind == 'via':
                vias[it.src].append([it.net] + B(it.at) + [round(it.size, 4), round(it.drill, 4)])
            if it.kind in ('track', 'via') and 'In2.Cu' in it.layers and it.kind == 'track':
                plane.add(it.net)
    tracks, nseg = {'router': [], 'new': []}, collections.Counter()
    for (src, net, lay, w), segs in sorted(groups.items()):
        for path in chains(segs):
            tracks[src].append([net, lay, w, [B(p) for p in path]])
            nseg[src] += len(path) - 1
    for k in vias:
        vias[k].sort()
        tracks[k].sort()
    inner = collections.Counter()
    for it in m.items:
        if it.alive and it.kind == 'track' and it.layers[0] in ('In1.Cu', 'In2.Cu'):
            inner[it.net] += math.hypot(it.a[0] - it.b[0], it.a[1] - it.b[1])
    run = args.route_run or (int(art.name.rsplit('-', 1)[-1]) if art.name.rsplit('-', 1)[-1].isdigit() else None)
    ripped = dict(sorted(fz.ripped.items()))
    summary = (f'Route run {run} left {sum(open0.values())} open connections on {len(open0)} nets '
               f'({", ".join(f"{n} {k}" for n, k in sorted(open0.items()))}); the completion joined them with '
               f'{nseg["new"]} segments and {len(vias["new"])} vias, ripping {sum(ripped.values())} router items of '
               f'{len(ripped)} nets where it needed their place and joining those again; inner-layer signal copper '
               f'{ {k: round(v, 1) for k, v in sorted(inner.items())} } mm (In2.Cu).')
    doc = {
        'schema': 'srrx-pwrb-frozen-route-v1',
        'label': 'CI/model input for pcb/boards/PWR_B.json (W2 PWRB-R route study); not a hardware PASS; bench gates OPEN',
        'source': {'route_run': run, 'inputs_sha256': report['inputs']['sha256'], 'board_sha256': report['board_sha256'],
                   'router': 'Freerouting 2.5.0 (sr-rx-pcb job Board PWR_B)',
                   'harvest': 'every unlocked track and via of that run, board mm (y up), coordinates as routed'},
        'completion': ('grid A* on the locked copper, 0.05 mm grid, exact clearance check 0.15 mm, 0.3 mm to edges, 0.5 mm hole '
                       'to hole, keep-outs (holes, edge strips, the PWR-A cut-outs), track ends on via centres, path ends 0.13 '
                       'mm inside pads; through vias 0.7/0.3 mm; signals on F.Cu / In2.Cu / B.Cu, power classes on F.Cu / B.Cu'),
        'summary': summary,
        'guard': cur['guard'],
        'open_before': open0, 'ripped': ripped, 'open_after': open_,
        'segments': dict(nseg),
        'router_tracks': tracks['router'], 'router_vias': vias['router'],
        'completion_tracks': tracks['new'], 'completion_vias': vias['new'],
    }
    Path(args.out).write_text(dump(doc), encoding='utf-8', newline='\n')
    print('wrote', args.out, dict(nseg), {k: len(v) for k, v in vias.items()}, 'inner mm by net',
          {k: round(v, 1) for k, v in inner.items()})
    return 0 if not (open_ or bad) else 1


if __name__ == '__main__':
    raise SystemExit(main())
