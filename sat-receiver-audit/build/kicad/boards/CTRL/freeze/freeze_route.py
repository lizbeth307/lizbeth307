#!/usr/bin/env python3
"""Freeze a CTRL route run and complete it (W2 CTRL-R route study). Needs numpy; offline tool, not run by CI.

  python build/kicad/boards/CTRL/freeze/freeze_route.py --artifact <unzipped pcb-regenerated-CTRL> [--out FILE]
  python build/kicad/boards/CTRL/freeze/freeze_route.py --from-frozen [--rip NET] [--scripted NET] [--check]   (incremental.py)

The artifact holds board/CTRL.kicad_pcb and board/report.json of a route run whose inputs equal the spec made by
build/kicad/boards/CTRL/make_spec.py without route-frozen.json. The tool
  1. reads the routed board (pads with exact roundrect/custom shapes, tracks, vias, keepouts, edges);
  2. drops the scripted pieces listed in DROP (the dangling 3V3_Q6A via at U315.3 and its stub, the E3_PICO3V3 L1 link
     P33-RIGHT-F) and adds the E3_PICO3V3 crossing of the cut-out 1 band on L2 between the vias P33-V-R4B and P33-V-R368;
  3. joins every open connection by grid A* (0.05 mm grid) on the locked copper with the exact clearance check (board
     rules 0.15 mm, copper to edge 0.3 mm, hole to hole 0.5 mm, keepouts, no via in an SMD pad); when no free path
     exists it rips only the router segments the cheapest path crosses and joins those nets again;
  4. removes dangling router/completion copper, checks every item again and writes route-frozen.json (router copper as
     routed, completion copper, the drops and a guard: SHA256 of the pads and of the scripted copper, which make_spec.py
     compares before it uses the frozen copper).
CI/model input only: the CI route run with '[pcb-route CTRL]' is the check (KiCad 10.0.7 DRC); bench gates stay OPEN.
"""
import argparse, collections, importlib.util, json, math, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model as M  # noqa: E402
import router as R  # noqa: E402
import fin as F  # noqa: E402

BASE = HERE.parents[4]
OUT = HERE.parent / 'route-frozen.json'
DROP = {'tracks': ['V33-U315', 'P33-RIGHT-F'], 'vias': ['V33-U315']}
DROP_GEOMETRY = {  # board mm, as make_spec.py makes them
    'V33-U315': {'via': (27.5, 94.45), 'track_to_pad': ('U315', '3'), 'net': '3V3_Q6A'},
    'P33-RIGHT-F': {'path': [(40.3, 109.6), (40.55, 104.5), (40.55, 101.0), (39.235, 97.0), (39.235, 89.5), (38.6, 88.8), (38.6, 74.3)],
                    'net': 'E3_PICO3V3'},
}
L2_LINK = {'net': 'E3_PICO3V3', 'from': (40.3, 109.6), 'to': (38.6, 74.3), 'width': 0.2, 'box': (30.0, 68.0, 50.0, 115.0)}
ORDER = ['3V3_Q6A', 'E3_PANEL_TEMP', 'E3_Q6A_KEY_GATE', 'E3_PICO3V3', 'E3_CASE_TEMP', 'E3_REC_EXT']
L2_FALLBACK = {'E3_REC_EXT'}  # and every net whose router copper was ripped: L2 only when three layers have no path
L2_BIAS = 1.0                 # extra cost per mm on L2 (a L2 millimetre costs twice a millimetre on L1/L3/L4)
NEVER = {'GND', 'E3_FAN5', 'E3_BLOWER_GND'}  # scripted classes (SCRIPTED_GND, SCRIPTED_PWR3A): never routed here


def class_widths():
    """Track width per net from the committed CTRL.kicad_pro (net class patterns; Default 0.15 mm)."""
    pro = json.loads((HERE.parent / 'CTRL.kicad_pro').read_text(encoding='utf-8'))['net_settings']
    width = {c['name']: c['track_width'] for c in pro['classes']}
    return {p['pattern']: width[p['netclass']] for p in pro['netclass_patterns']}, width['Default']
K = lambda x, y: (round(x + 100, 4), round(244 - y, 4))  # board mm -> KiCad mm (frame of pcb/board_gen.py)
B = lambda p: [round(p[0] - 100.0, 4), round(244.0 - p[1], 4)]


def drop_scripted(m):
    g = DROP_GEOMETRY['V33-U315']
    at = K(*g['via'])
    vias = [it for it in m.items if it.alive and it.kind == 'via' and it.src == 'scripted' and it.net == g['net']
            and abs(it.at[0] - at[0]) < 1e-3 and abs(it.at[1] - at[1]) < 1e-3]
    pad = [it for it in m.items if it.kind == 'pad' and (it.ref, it.pad) == g['track_to_pad']][0]
    stub = [it for it in m.items if it.alive and it.kind == 'track' and it.src == 'scripted' and it.net == g['net']
            and {(round(it.a[0], 3), round(it.a[1], 3)), (round(it.b[0], 3), round(it.b[1], 3))}
            == {(round(pad.at[0], 3), round(pad.at[1], 3)), (round(at[0], 3), round(at[1], 3))}]
    assert len(vias) == 1 and len(stub) == 1, ('V33-U315', len(vias), len(stub))
    for it in vias + stub:
        m.remove(it)
    g = DROP_GEOMETRY['P33-RIGHT-F']
    pts = [K(*p) for p in g['path']]
    segs = set(zip(pts, pts[1:]))
    hit = [it for it in m.items if it.alive and it.kind == 'track' and it.src == 'scripted' and it.net == g['net']
           and (((round(it.a[0], 4), round(it.a[1], 4)), (round(it.b[0], 4), round(it.b[1], 4))) in segs
                or ((round(it.b[0], 4), round(it.b[1], 4)), (round(it.a[0], 4), round(it.a[1], 4))) in segs)]
    assert len(hit) == len(segs), ('P33-RIGHT-F', len(hit), len(segs))
    for it in hit:
        m.remove(it)


def l2_link(m):
    def via_at(p):
        at = K(*p)
        v = [it for it in m.items if it.alive and it.kind == 'via' and it.net == L2_LINK['net']
             and abs(it.at[0] - at[0]) < 1e-3 and abs(it.at[1] - at[1]) < 1e-3]
        assert len(v) == 1, p
        return v
    x0, y0, x1, y1 = L2_LINK['box']
    res = R.route_link(m, L2_LINK['net'], via_at(L2_LINK['from']), via_at(L2_LINK['to']), (x0 + 100, 244 - y1, x1 + 100, 244 - y0),
                       width=L2_LINK['width'], layers=('In1.Cu',))
    assert res and not res['vias'], 'no L2 path'
    return R.commit(m, L2_LINK['net'], res, 'FIN-P33-L2', print)


def verify(m):
    """Open connections, dangling copper and clearance of every track and via (exact checks)."""
    nets = sorted({i.net for i in m.items if i.alive and i.net})
    open_ = {n: len(m.islands(n)) - 1 for n in nets if n != 'GND' and len(m.islands(n)) > 1}
    if len(m.islands('GND')) > 1:
        open_['GND'] = len(m.islands('GND')) - 1
    bad = [('dangling',) + d for d in F.dangling(m)]
    # KiCad 10 DRC track_not_centered_on_via: a track end inside a via off its centre is accepted only in the pattern the
    # router itself leaves (another track of the net joins that end to the via centre); checked for every new via and
    # every completion track
    ends = collections.defaultdict(list)
    for it in m.items:
        if it.alive and it.kind == 'track':
            for e, o in ((it.a, it.b), (it.b, it.a)):
                ends[(it.net, round(e[0], 5), round(e[1], 5))].append(o)
    for it in m.items:
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
            bad.append((round(mg, 4), it.src, it.kind, it.net, why))
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


def guard():
    """The guard make_spec.py checks: computed by make_spec itself on the spec without the frozen copper."""
    loader = importlib.util.spec_from_file_location('ctrl_make_spec', HERE.parent / 'make_spec.py')
    ms = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(ms)
    got = {}
    ms.frozen_copper = lambda cu, log: got.update(ms.frozen_guard(cu))
    ms.build(lambda *a: None)
    return got


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


def from_frozen(args):
    """--from-frozen (W2 CTRL-4, review RV-CTRLR-5): re-freeze from the committed frozen copper; see incremental.py."""
    import incremental as I
    rc, text = I.run(args)
    if rc or text is None:
        return rc or 1
    out = Path(args.out)
    if args.check:
        same = out.is_file() and out.read_text(encoding='utf-8') == text
        print('route-frozen.json reproduced byte for byte' if same else f'{out} differs from the incremental result')
        return 0 if same else 1
    out.write_text(text, encoding='utf-8', newline='\n')
    print('wrote', out)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--artifact', help='unzipped pcb-regenerated-CTRL artifact (board/CTRL.kicad_pcb, board/report.json)')
    ap.add_argument('--out', default=str(OUT))
    inc = ap.add_argument_group('--from-frozen (incremental, W2 CTRL-4): start from the committed route-frozen.json')
    inc.add_argument('--from-frozen', action='store_true', help='re-freeze from the committed frozen copper (incremental.py)')
    inc.add_argument('--board', default=str(HERE.parent / 'CTRL.kicad_pcb'),
                     help='routed board for pads, keepouts and edges (default: the committed GENERATED CTRL.kicad_pcb)')
    inc.add_argument('--board-label', default='', help='provenance text for the board (for example its route run)')
    inc.add_argument('--base', default='', help='frozen route to start from (default: the committed route-frozen.json)')
    inc.add_argument('--rip', action='append', default=[], metavar='NET', help='remove the frozen copper of NET and join it again')
    inc.add_argument('--scripted', action='append', default=[], metavar='NET',
                     help='remove the frozen copper of NET; it must be complete from the scripted copper (never routed here)')
    inc.add_argument('--l2', action='append', default=[], metavar='NET', help='NET may use L2 where three layers have no path')
    inc.add_argument('--l2-cascade', action='store_true', help='nets ripped on the way may use L2 too (as the first freeze)')
    inc.add_argument('--allow-open', action='store_true', help='write the result with open connections left to Freerouting')
    inc.add_argument('--reason', default='', help='why (recorded in the increments list of route-frozen.json)')
    inc.add_argument('--check', action='store_true', help='compare the result with --out instead of writing it')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    if args.from_frozen:
        return from_frozen(args)
    if not args.artifact:
        ap.error('--artifact is required without --from-frozen')
    art = Path(args.artifact)
    report = json.loads((art / 'board/report.json').read_text(encoding='utf-8'))
    m = M.Model(str(art / 'board/CTRL.kicad_pcb'))
    drop_scripted(m)
    recs = l2_link(m)
    fz = F.Finisher(m)
    queue, rounds, t0 = collections.deque(ORDER), 0, time.time()
    fallback = set(L2_FALLBACK)
    widths, default_w = class_widths()
    while queue and rounds < 80:
        net = queue.popleft()
        rounds += 1
        if net in NEVER:
            raise SystemExit(f'freeze_route: {net} is scripted copper; it is never routed here')
        ok, ripped = fz.connect(net, l2_bias=L2_BIAS if net in fallback else None, width=widths.get(net, default_w))
        print(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)')
        queue.extend(n for n in ripped if n not in queue)
        fallback |= set(ripped)
    for n in sorted({i.net for i in m.items if i.alive and i.net and i.net != 'GND'}):
        F.prune(m, n)
    open_, bad = verify(m)
    print('open connections', open_, 'clearance violations', len(bad))
    for b_ in bad[:12]:
        print('   ', b_)
    if open_ or bad:
        return 1
    groups = collections.defaultdict(list)
    vias = {'router': [], 'new': []}
    for it in m.items:
        if it.alive and it.src in ('router', 'new'):
            if it.kind == 'track':
                groups[(it.src, it.net, it.layers[0], round(it.width, 4))].append((it.a, it.b))
            elif it.kind == 'via':
                vias[it.src].append([it.net] + B(it.at) + [round(it.size, 4), round(it.drill, 4)])
    tracks, nseg = {'router': [], 'new': []}, collections.Counter()
    for (src, net, lay, w), segs in sorted(groups.items()):
        for path in chains(segs):
            tracks[src].append([net, lay, w, [B(p) for p in path]])
            nseg[src] += len(path) - 1
    for k in vias:
        vias[k].sort()
        tracks[k].sort()
    run = report.get('route_run') or ''
    doc = {
        'schema': 'srrx-ctrl-frozen-route-v1',
        'label': 'CI/model input for pcb/boards/CTRL.json (W2 CTRL-R route study); not a hardware PASS; bench gates OPEN',
        'source': {'route_run': int(art.name.rsplit('-', 1)[-1]) if art.name.rsplit('-', 1)[-1].isdigit() else run,
                   'inputs_sha256': report['inputs']['sha256'], 'board_sha256': report['board_sha256'],
                   'router': 'Freerouting 2.5.0 (sr-rx-pcb job Board CTRL)',
                   'harvest': 'every unlocked track and via of that run, board mm (y up), coordinates as routed'},
        'completion': ('grid A* completion on the frozen copper (0.05 mm grid, exact clearance check 0.15 mm, 0.3 mm to edges, '
                       '0.5 mm hole to hole, keepouts; through vias 0.65/0.3 mm; L2 only where three layers have no path) by '
                       'build/kicad/boards/CTRL/freeze/freeze_route.py'),
        'guard': guard(),
        'drop_scripted': DROP,
        'segments': dict(nseg),
        'router_tracks': tracks['router'], 'router_vias': vias['router'],
        'completion_tracks': tracks['new'], 'completion_vias': vias['new'],
    }
    Path(args.out).write_text(dump(doc), encoding='utf-8', newline='\n')
    l2 = collections.Counter()
    for it in m.items:
        if it.alive and it.kind == 'track' and it.layers[0] == 'In1.Cu':
            l2[it.net] += math.hypot(it.a[0] - it.b[0], it.a[1] - it.b[1])
    print('wrote', args.out, dict(nseg), {k: len(v) for k, v in vias.items()}, 'L2 mm by net', {k: round(v, 1) for k, v in l2.items()})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
