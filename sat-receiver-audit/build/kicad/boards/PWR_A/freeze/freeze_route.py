#!/usr/bin/env python3
"""Freeze a PWR_A route run and complete it (W2 PWRJ F2ENV: copy of the PWR_B tool of W2 PWRB-R, itself a port of the
W2 CTRL-R tool, driven by make_board.py instead of make_spec.py). Needs numpy; offline, not run by CI.

  python build/kicad/boards/PWR_A/freeze/freeze_route.py --artifact <unzipped pcb-regenerated-PWR_A> [--out FILE]

The text below is the PWR_B one; read PWR_A, make_board.py and pcb/boards/PWR_A.json for PWR_B, make_spec.py and its spec.

The artifact holds board/PWR_B.kicad_pcb and board/report.json of a route run whose inputs equal the spec that
build/kicad/boards/PWR_B/make_spec.py makes without route-frozen.json. The tool
  1. reads the routed board (pads with exact roundrect shapes, tracks, vias, keepouts: the hole keep-outs, the edge strips
     and the planned PWR-A cut-outs of spec planned_cutouts, edges) with model.py;
  2. joins every open connection of the autorouted nets by grid A* on F.Cu and B.Cu (0.05 mm grid, exact clearance check:
     board clearance 0.15 mm, copper to edge 0.3 mm, hole to hole 0.5 mm, keepouts, no via in an SMD pad; In1.Cu and In2.Cu
     are GND planes and never carry a track); where no free path exists it rips only the router copper the cheapest path
     crosses and joins those nets again (fin.py);
  3. removes dangling router and completion copper, checks every item again and writes route-frozen.json (router copper as
     routed, completion copper, and a guard: SHA256 of the pads and of the scripted copper, which make_spec.py compares
     before it uses the frozen copper).
The scripted nets (GND, LAB5, the Kelvin nets E2_LNA*_SW / *_SHUNT) are never routed here. CI/model input only: the CI
route run with '[pcb-route PWR_B]' is the check (KiCad 10.0.7 DRC); bench gates stay OPEN.
"""
import argparse, collections, importlib.util, json, math, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model as M  # noqa: E402
import fin as F  # noqa: E402

OUT = HERE.parent / 'route-frozen.json'
B = lambda p: [round(p[0] - 100.0, 4), round(210.0 - p[1], 4)]  # KiCad mm -> board mm (frame of pcb/board_gen.py)


def load_make_spec():
    sys.path.insert(0, str(HERE.parent))
    loader = importlib.util.spec_from_file_location('pwra_make_board', HERE.parent / 'make_board.py')
    ms = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(ms)
    return ms


def class_widths():
    """Track width per net from the committed PWR_B.kicad_pro (net class patterns; Default 0.15 mm)."""
    pro = json.loads((HERE.parent / 'PWR_A.kicad_pro').read_text(encoding='utf-8'))['net_settings']
    width = {c['name']: c['track_width'] for c in pro['classes']}
    return {p['pattern']: width[p['netclass']] for p in pro['netclass_patterns']}, width['Default']


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
        if not it.alive or it.src not in ('router', 'new'):
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--artifact', required=True, help='unzipped pcb-regenerated-PWR_B artifact (board/PWR_B.kicad_pcb, board/report.json)')
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--rounds', type=int, default=200)
    ap.add_argument('--in2', action='store_true', help='let slow signal nets use In2.Cu where F.Cu and B.Cu have no path')
    ap.add_argument('--in2-signal', action='store_true', help='In2.Cu is a signal layer (make_spec.py IN2_SIGNAL): signal nets '
                    'are completed on F.Cu, In2.Cu and B.Cu, power-class nets on F.Cu and B.Cu only (inner class widths)')
    ap.add_argument('--in2-bias', type=float, default=1.0, help='extra cost per mm on In2.Cu (1.0: an In2 mm costs two)')
    ap.add_argument('--no-rip', action='store_true', help='W2 PWRJ F2ENV: join only along free paths, never rip router copper')
    ap.add_argument('--partial', action='store_true', help='write route-frozen.json even with open connections (listed under open)')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    art = Path(args.artifact)
    report = json.loads((art / 'board/report.json').read_text(encoding='utf-8'))
    ms = load_make_spec()
    never = set(ms.SCRIPTED_CLASSES)
    have = ms.frozen_guard_of_spec()
    m = M.Model(str(art / 'board/PWR_A.kicad_pcb'))
    fz = F.Finisher(m)
    widths, default_w = class_widths()
    if args.in2_signal:
        # power-class copper must stay on the outer layers (pcb/generated/netclasses.json inner widths: PWR1A 1.8 mm, PWR2A
        # 4.7 mm): the router copper of power-class nets on In2.Cu is ripped here and those nets are completed outer only
        moved = [it for it in m.items if it.alive and it.kind == 'track' and it.src == 'router' and it.layers[0] == 'In2.Cu'
                 and it.net in widths and it.net not in never]
        for it in moved:
            m.remove(it)
        for n in sorted({it.net for it in moved}):
            F.prune(m, n)
        print('power-class router tracks on In2.Cu ripped:', len(moved), sorted({it.net for it in moved}))
    nets = sorted({i.net for i in m.items if i.alive and i.net and i.net not in never})
    todo = [n for n in nets if len(m.islands(n)) > 1]
    print('open nets of the route run:', {n: len(m.islands(n)) - 1 for n in todo})
    queue, rounds, t0, failed = collections.deque(todo), 0, time.time(), {}
    while queue and rounds < args.rounds:
        net = queue.popleft()
        rounds += 1
        before = len(m.islands(net))
        w = widths.get(net, default_w)
        # slow signal nets (Default class) may use In2.Cu where F.Cu and B.Cu have no path; power nets never (class widths
        # are outer-layer widths, pcb/generated/netclasses.json)
        if args.in2_signal:  # S-G-S-S (make_spec.py IN2_SIGNAL): signal nets on three layers, power nets outer only
            ok, ripped = fz.connect(net, width=w, max_iter=200,
                                    layers=('F.Cu', 'B.Cu') if net in widths else ('F.Cu', 'In2.Cu', 'B.Cu'))
        else:
            ok, ripped = fz.connect(net, allow_rip=not args.no_rip, width=w, max_iter=200,
                                    l2_bias=(args.in2_bias if args.in2 and net not in widths else None))
        after = len(m.islands(net))
        print(f'{net}: {"OK" if ok else "FAILED"} islands {before} -> {after} ripped {ripped} ({time.time() - t0:.0f} s)', flush=True)
        if ok:
            failed.pop(net, None)
        else:
            failed[net] = after - 1
            if after < before and net not in queue:  # progress: try the rest again after the others
                queue.append(net)
        queue.extend(n for n in ripped if n not in queue and n not in never)
    for n in nets:
        F.prune(m, n)
    open_, bad = verify(m)
    open_ = {k: v for k, v in open_.items() if k not in never or k == 'GND'}
    print('open connections', open_, 'clearance violations', len(bad))
    for b_ in bad[:12]:
        print('   ', b_)
    if bad or (open_ and not args.partial):
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
    doc = {
        'schema': 'srrx-pwra-frozen-route-v1',
        'label': 'CI/model input for pcb/boards/PWR_A.json (W2 PWRJ F2ENV probe); not a hardware PASS; bench gates OPEN',
        'source': {'route_run': int(art.name.rsplit('-', 1)[-1]) if art.name.rsplit('-', 1)[-1].isdigit() else '',
                   'inputs_sha256': report['inputs']['sha256'], 'board_sha256': report['board_sha256'],
                   'router': 'Freerouting 2.5.0 (sr-rx-pcb job Board PWR_A)',
                   'harvest': 'every unlocked track and via of that run, board mm (y up), coordinates as routed'},
        'completion': ('grid A* completion on the frozen copper (0.05 mm grid, exact clearance check 0.15 mm, 0.3 mm to edges, '
                       '0.5 mm hole to hole, keepouts incl. the planned PWR-A cut-outs; through vias 0.7 / 0.3 mm; F.Cu and B.Cu '
                       'only) by build/kicad/boards/PWR_A/freeze/freeze_route.py'),
        'guard': have,
        'open': open_,
        'segments': dict(nseg),
        'router_tracks': tracks['router'], 'router_vias': vias['router'],
        'completion_tracks': tracks['new'], 'completion_vias': vias['new'],
    }
    Path(args.out).write_text(dump(doc), encoding='utf-8', newline='\n')
    print('wrote', args.out, dict(nseg), {k: len(v) for k, v in vias.items()}, 'failed', failed)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
