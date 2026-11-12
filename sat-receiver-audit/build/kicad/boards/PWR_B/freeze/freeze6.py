#!/usr/bin/env python3
"""Freeze a 6-layer PWR_B route run and complete it (W2 PWRB-R layers6 study). Needs numpy; offline tool, not run by CI.

  python build/kicad/boards/PWR_B/freeze/freeze6.py --artifact <unzipped pcb-regenerated-PWR_B> [--out FILE] [--no-guard]

The PWR_B counterpart of build/kicad/boards/CTRL/freeze/freeze6.py (W2 CTRL-4, origin/wip/w2-ctrl4-layers6); model.py,
router.py and fin.py here are copies of the CTRL tools. The artifact holds board/PWR_B.kicad_pcb, board/report.json and
board/drc.json of a route run whose inputs equal the spec made by make_spec.py without route-frozen-6l.json. The tool
  1. reads the routed 6-layer board (In1.Cu GND plane, In4.Cu 3V3_Q6A plane; routing layers F.Cu, In2.Cu, In3.Cu, B.Cu;
     the keepout_rects rule areas of the PWR-A cut-outs and the edge strips count as keepouts);
  2. removes router copper that breaks a clearance in the model and joins its net again;
  3. joins every open connection of KiCad's DRC by grid A* (exact clearance check, rip-up of router copper only when no
     free path exists, ripped nets joined again): power-class nets (PWR1A) on F.Cu/B.Cu only at their class width (the
     0.5 oz inner layers would need 1.8 mm), signal nets on the four routing layers; nothing goes on a plane layer;
  4. removes dangling router/completion copper, checks every item again and writes route-frozen-6l.json (router copper
     as routed, completion copper, a guard: SHA256 of the pads and of the scripted copper, which make_spec.py compares).
With --no-guard it writes no guard (a trial; make_spec refuses such a file).
CI/model input only: the CI route run with '[pcb-route PWR_B]' is the check (KiCad 10.0.7 DRC); bench gates stay OPEN.
"""
import argparse
import collections
import importlib.util
import json
import math
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model as M  # noqa: E402

COPPER = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
M.configure(COPPER, {'GND': 'In1.Cu', '3V3_Q6A': 'In4.Cu'})
import fin as F  # noqa: E402
import router as R  # noqa: E402

F.BOARD_BOX = (100.0, 100.0, 236.0, 210.0)  # KiCad mm: board_gen frame of the 136 x 110 mm L (x + 100, 210 - y)
OUT = HERE.parent / 'route-frozen-6l.json'
# planes and scripted nets (classes SCRIPTED_GND, SCRIPTED_PWR1A, SCRIPTED_PWR3A of make_spec.py): never routed here
NEVER = {'GND', '3V3_Q6A', 'LAB5'} | {f'E2_LNA{ch}_{k}' for ch in '1234' for k in ('SW', 'SHUNT')}
ROUTING = tuple(M.RLAYERS)
OUTER = ('F.Cu', 'B.Cu')
K = lambda x, y: (round(x + 100.0, 4), round(210.0 - y, 4))  # board mm -> KiCad mm (frame of pcb/board_gen.py)
B = lambda p: [round(p[0] - 100.0, 4), round(210.0 - p[1], 4)]


def classes():
    """Net -> (class, track width) from the committed PWR_B.kicad_pro (net class patterns; Default 0.15 mm)."""
    pro = json.loads((HERE.parent / 'PWR_B.kicad_pro').read_text(encoding='utf-8'))['net_settings']
    width = {c['name']: c['track_width'] for c in pro['classes']}
    return {p['pattern']: (p['netclass'], width[p['netclass']]) for p in pro['netclass_patterns']}, width['Default']


B2B, B2B_Y, ESCAPE_W = 'J209', 191.5, 0.25  # J209 strip axis (KiCad y = 210 - 18.5); escape width of the J209 branch_exempt


def j209_escape(m, net):
    """A J209 contact of a power-class net that the router left bare: a 0.25 mm B.Cu stub straight out of its row (the
    J209 branch_exempt of the spec: contact escapes >= 0.25 mm within 10 mm; a 0.35 mm track on the 0.05 mm grid does not
    pass between the 0.30 mm pads at 0.50 mm pitch), so the class-width link starts beyond the row. Returns the stubs."""
    out = []
    for gr in m.islands(net):
        pads = [i for i in gr if i.kind == 'pad' and i.ref == B2B]
        if len(gr) != 1 or not pads:
            continue
        p = pads[0]
        sign = -1.0 if p.at[1] < B2B_Y else 1.0  # outwards: upper row (smaller KiCad y) up, lower row down
        for length in (1.3, 1.5, 1.8, 2.1, 2.5):
            e = (p.at[0], round(p.at[1] + sign * length, 4))
            mg, why = m.track_margin(net, 'B.Cu', ESCAPE_W, p.at, e)
            if mg >= 0.005:
                m.add_track(net, 'B.Cu', ESCAPE_W, p.at, e, src='escape')  # not pruned while its link is open
                out.append((p.pad, e))
                break
    return out


def verify(m):
    """Open connections, dangling copper and clearance of every track and via (exact checks), as CTRL freeze_route.py."""
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
    loader = importlib.util.spec_from_file_location('pwr_b_make_spec', HERE.parent / 'make_spec.py')
    ms = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(ms)
    return ms.frozen_guard_of_spec()


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
    ap.add_argument('--no-guard', action='store_true', help='trial: write no guard (make_spec refuses the file)')
    ap.add_argument('--rounds', type=int, default=400)
    ap.add_argument('--no-rip', action='store_true', help='join only where a free path exists (no rip-up of router copper)')
    ap.add_argument('--order', choices=('class', 'short'), default='class', help='completion order of the open nets')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    art = Path(args.artifact)
    report = json.loads((art / 'board/report.json').read_text(encoding='utf-8'))
    m = M.Model(str(art / 'board/PWR_B.kicad_pcb'))
    assert m.b.copper_layers == M.LAYERS, m.b.copper_layers
    fz = F.Finisher(m)
    cls, default_w = classes()
    width = lambda n: cls.get(n, ('Default', default_w))[1]
    layers = lambda n: OUTER if 'PWR' in cls.get(n, ('Default',))[0] else ROUTING
    drc = json.loads((art / 'board/drc.json').read_text(encoding='utf-8'))
    kicad_open = collections.Counter(n for u in drc.get('unconnected_items', []) for n in
                                     {re.search(r'\[([^\]]+)\]', i.get('description', '')).group(1)
                                      for i in u.get('items', []) if re.search(r'\[([^\]]+)\]', i.get('description', ''))})
    bad_never = sorted(set(kicad_open) & NEVER)
    if bad_never:
        raise SystemExit(f'freeze6: KiCad reports open connections of {bad_never}: fix the scripted copper and route again')
    model_only = {n: k for n, k in fz.unconnected().items() if n not in NEVER and n not in kicad_open}
    print('KiCad open connections:', dict(kicad_open))
    print('model-only islands (joined in KiCad by copper overlap, left as routed):', model_only)
    viol = set()
    for it in m.items:
        if not (it.alive and it.src == 'router'):
            continue
        if it.kind == 'track':
            mg, why = m.track_margin(it.net, it.layers[0], it.width, it.a, it.b, ignore={it.id})
        elif it.kind == 'via':
            mg, why = m.via_margin(it.net, it.at, it.size, it.drill, ignore={it.id})
        else:
            continue
        if mg < -0.0005:
            print(f'  router {it.kind} of {it.net} breaks a clearance ({mg:+.3f}, {why}): removed')
            m.remove(it)
            viol.add(it.net)
    for n in sorted(viol):
        F.prune(m, n)
    # power-class nets first: they have only the outer layers (--order class); or the shortest nets first (--order short:
    # the long links take the free corridor space last, so fewer short links are walled in)
    def span(n):
        pts = [i.at for i in m.items if i.alive and i.kind == 'pad' and i.net == n]
        return math.hypot(max(p[0] for p in pts) - min(p[0] for p in pts), max(p[1] for p in pts) - min(p[1] for p in pts)) if pts else 0.0
    if args.order == 'short':
        first = sorted(set(kicad_open) | viol, key=lambda n: (span(n), n))
    else:
        first = sorted(set(kicad_open) | viol, key=lambda n: (layers(n) != OUTER, n))
    queue, rounds, t0 = collections.deque(first), 0, time.time()
    touched, failed = set(first), []
    while queue and rounds < args.rounds:
        net = queue.popleft()
        rounds += 1
        if net in NEVER:
            raise SystemExit(f'freeze6: {net} is a plane or scripted net; it is never routed here')
        if layers(net) == OUTER:
            for pad, e in j209_escape(m, net):
                print(f'  {net}: J209.{pad} escape stub {ESCAPE_W} mm to {e}')
        ok, ripped = fz.connect(net, width=width(net), layers=layers(net), allow_rip=not args.no_rip)
        print(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)', flush=True)
        if not ok:
            failed.append(net)
        queue.extend(n for n in ripped if n not in queue)
        touched |= set(ripped)
    for n in sorted({i.net for i in m.items if i.alive and i.net and i.net not in M.PLANES}):
        F.prune(m, n, srcs=('router', 'new', 'escape'))  # an escape stub whose link failed goes too
    open_, bad = verify(m)
    open_ = {n: k for n, k in open_.items() if n in touched}
    bad = [b for b in bad if not (b[0] == 'dangling' and (b[2] in NEVER or b[2] in model_only))]
    print('open connections', open_, 'clearance violations', len(bad), 'failed', sorted(set(failed)))
    for b_ in bad[:12]:
        print('   ', b_)
    groups = collections.defaultdict(list)
    vias = {'router': [], 'new': []}
    for it in m.items:
        if it.alive and it.src in ('router', 'new', 'escape'):
            src = 'new' if it.src == 'escape' else it.src
            if it.kind == 'track':
                groups[(src, it.net, it.layers[0], round(it.width, 4))].append((it.a, it.b))
            elif it.kind == 'via':
                vias[src].append([it.net] + B(it.at) + [round(it.size, 4), round(it.drill, 4)])
    tracks, nseg = {'router': [], 'new': []}, collections.Counter()
    for (src, net, lay, w), segs in sorted(groups.items()):
        for path in chains(segs):
            tracks[src].append([net, lay, w, [B(p) for p in path]])
            nseg[src] += len(path) - 1
    for k in vias:
        vias[k].sort()
        tracks[k].sort()
    run = art.name.rsplit('-', 1)[-1]
    doc = {
        'schema': 'srrx-pwrb-frozen-route-v1',
        'label': 'CI/model input for pcb/boards/PWR_B.json (W2 PWRB-R, 6 layers); not a hardware PASS; bench gates OPEN',
        'source': {'route_run': int(run) if run.isdigit() else '', 'inputs_sha256': report['inputs']['sha256'],
                   'board_sha256': report['board_sha256'], 'router': 'Freerouting 2.5.0 (sr-rx-pcb job Board PWR_B)',
                   'harvest': 'every unlocked track and via of that run, board mm (y up), coordinates as routed'},
        'completion': ('grid A* completion on the frozen copper (0.05 mm grid, exact clearance check 0.15 mm, 0.3 mm to edges, '
                       '0.5 mm hole to hole, keepouts incl. the PWR-A cut-out rule areas; through vias 0.65/0.3 mm; PWR1A on '
                       'F.Cu/B.Cu, signals on F.Cu, In2.Cu, In3.Cu, B.Cu, no plane layer) by '
                       'build/kicad/boards/PWR_B/freeze/freeze6.py'),
        'result': {'open': open_, 'violations': len(bad), 'failed_nets': sorted(set(failed))},
        'guard': None if args.no_guard else guard(),
        'segments': dict(nseg),
        'router_tracks': tracks['router'], 'router_vias': vias['router'],
        'completion_tracks': tracks['new'], 'completion_vias': vias['new'],
    }
    Path(args.out).write_text(dump(doc), encoding='utf-8', newline='\n')
    print('wrote', args.out, dict(nseg), {k: len(v) for k, v in vias.items()})
    return 1 if (open_ or bad) else 0


if __name__ == '__main__':
    raise SystemExit(main())
