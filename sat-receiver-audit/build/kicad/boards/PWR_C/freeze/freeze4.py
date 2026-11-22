#!/usr/bin/env python3
"""Freeze a PWR_C route run and complete it (W2 F2C-FALLBACK, PCB-PWRC-2). Needs numpy; offline tool, not run by CI.

  python build/kicad/boards/PWR_C/freeze/freeze4.py --artifact <unzipped pcb-regenerated-PWR_C> [--out FILE] [--no-guard]
         [--no-rip] [--order short|class] [--first NET,NET,...]

The 4-layer PWR_C counterpart of build/kicad/boards/PWR_B/freeze/freeze6.py; it imports that board's model.py, router.py and
fin.py (the CTRL-4 toolkit) unchanged and switches them to this stackup: In1.Cu and In2.Cu are GND planes, so the routing
layers are F.Cu and B.Cu only. The artifact holds board/PWR_C.kicad_pcb, board/report.json, board/drc.json and
board/route-log.json of a route run whose inputs equal the spec made by make_spec.py without route-frozen.json. The tool
  1. reads the routed board; the filled scripted pours (F.Cu / B.Cu zones of the power nets) are copper of their net in the
     model: other nets keep the clearance from their fill, and the fill joins the pads and tracks of its net it covers
     (KiCad joins them through the solid zone connection);
  2. holds the via-centre stubs of the run fixed, removes router copper that KiCad's DRC of the run names in an error and
     router copper that breaks a clearance in the model, and prunes those nets;
  3. joins every open connection of KiCad's DRC by grid A* on F.Cu / B.Cu at the class width of the net (exact clearance
     check, rip-up of router copper only when no free path exists, ripped nets joined again);
  4. removes dangling router/completion copper, checks every item again and writes route-frozen.json (router copper as
     routed, completion copper, a guard: SHA256 of the pads, the scripted copper and the pours, which make_spec.py compares).
With --no-guard it writes no guard (a trial; make_spec refuses such a file).
CI/model input only: the CI route run with '[pcb-route PWR_C]' is the check (KiCad 10.0.7 DRC); bench gates stay OPEN.
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
TOOLS = HERE.parents[1] / 'PWR_B' / 'freeze'   # model.py, router.py, fin.py of the PWR_B freeze (CTRL-4 toolkit), unchanged
sys.path.insert(0, str(TOOLS))
import model as M  # noqa: E402

COPPER = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
M.configure(COPPER, {'GND': 'In1.Cu'})
M.RLAYERS[:] = ['F.Cu', 'B.Cu']  # In2.Cu is the second GND plane: never routed here
import fin as F  # noqa: E402
import router as R  # noqa: E402

F.BOARD_BOX = (100.0, 100.0, 256.0, 133.5)  # KiCad mm: board_gen frame of the 156 x 33.5 mm board (x + 100, 133.5 - y)
OUT = HERE.parent / 'route-frozen.json'
NEVER = {'GND'}  # the planes (and the scripted GND fan-out): never routed here
ROUTING = ('F.Cu', 'B.Cu')
K = lambda x, y: (round(x + 100.0, 4), round(133.5 - y, 4))  # board mm -> KiCad mm (frame of pcb/board_gen.py)
B = lambda p: [round(p[0] - 100.0, 4), round(133.5 - p[1], 4)]

_touches = M.touches


def touches(p, q):
    """model.touches plus the pour fills (src 'pour'): a fill joins a same-net track whose end lies in it, a via in it and a
    pad whose centre it covers (solid zone connection); two fills join only through other copper."""
    if p.src == 'pour' or q.src == 'pour':
        a, b = (p, q) if p.src == 'pour' else (q, p)
        if b.src == 'pour':
            return False
        if b.kind == 'track':
            return any(a.shape.dist(*e) <= 1e-4 for e in (b.a, b.b))
        if b.kind == 'via':
            return a.shape.dist(*b.at) <= 1e-4
        return a.shape.dist(*b.at) <= 1e-4
    return _touches(p, q)


M.touches = touches


def add_pours(m):
    """The filled F.Cu / B.Cu zones of the run (scripted pours; not the In1/In2 GND planes) as copper items of their net."""
    n = 0
    for z in m.b.zones:
        if z['keepout'] or not z['net']:
            continue
        for lay, polys in sorted(z['fills'].items()):
            if lay not in ROUTING:
                continue
            for poly in polys:
                bx = poly.bbox
                m.add(M.Item(kind='pad', net=z['net'], layers=[lay], shape=poly, ref='ZONE', pad=z['name'],
                             at=((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2), drill=0.0, locked=True, src='pour'))
                n += 1
    return n


def classes():
    """Net -> (class, track width) from the committed PWR_C.kicad_pro (net class patterns; Default 0.15 mm)."""
    pro = json.loads((HERE.parent / 'PWR_C.kicad_pro').read_text(encoding='utf-8'))['net_settings']
    width = {c['name']: c['track_width'] for c in pro['classes']}
    return {p['pattern']: (p['netclass'], width[p['netclass']]) for p in pro['netclass_patterns']}, width['Default']


def guard():
    """The guard make_spec.py checks: computed by make_spec itself on the spec without the frozen copper."""
    loader = importlib.util.spec_from_file_location('pwr_c_make_spec', HERE.parent / 'make_spec.py')
    ms = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(ms)
    return ms.frozen_guard_of_spec()


def load_freeze6():
    """The PWR_B freeze6 helpers that do not depend on the stackup (verify, chains, fix_stubs, drc_drops, dump,
    merge_remainders), loaded with this board's configuration of the shared model."""
    loader = importlib.util.spec_from_file_location('pwr_b_freeze6_helpers', TOOLS / 'freeze6.py')
    f6 = importlib.util.module_from_spec(loader)
    saved = (list(M.LAYERS), list(M.RLAYERS), dict(M.PLANES))
    loader.loader.exec_module(f6)   # its module code configures the 6-layer stackup: restore this board's afterwards
    M.LAYERS[:], M.RLAYERS[:] = saved[0], saved[1]
    M.PLANES.clear()
    M.PLANES.update(saved[2])
    F.BOARD_BOX = (100.0, 100.0, 256.0, 133.5)  # freeze6 sets the PWR_B frame on the shared finisher
    f6.NEVER = NEVER
    f6.ROUTING = ROUTING
    f6.K, f6.B = K, B
    return f6


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--artifact', required=True, help='unzipped pcb-regenerated-PWR_C artifact')
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--no-guard', action='store_true', help='trial: write no guard (make_spec refuses the file)')
    ap.add_argument('--rounds', type=int, default=400)
    ap.add_argument('--no-rip', action='store_true', help='join only where a free path exists (no rip-up of router copper)')
    ap.add_argument('--order', choices=('class', 'short'), default='short')
    ap.add_argument('--first', default='', help='comma-separated nets joined first, in this order (then --order)')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    f6 = load_freeze6()
    art = Path(args.artifact)
    report = json.loads((art / 'board/report.json').read_text(encoding='utf-8'))
    m = M.Model(str(art / 'board/PWR_C.kicad_pcb'))
    assert m.b.copper_layers == M.LAYERS, m.b.copper_layers
    print('pour fills in the model:', add_pours(m))
    fz = F.Finisher(m)
    stubs_hit, stubs_all = f6.fix_stubs(m, art)
    print(f'via-centre stubs of the route log held fixed: {stubs_hit} of {stubs_all}')
    cls, default_w = classes()
    width = lambda n: cls.get(n, ('Default', default_w))[1]
    drc = json.loads((art / 'board/drc.json').read_text(encoding='utf-8'))
    drops = f6.drc_drops(m, drc)
    print('router copper named in a KiCad DRC error:', drops)
    kicad_open = collections.Counter(n for u in drc.get('unconnected_items', []) for n in
                                     {re.search(r'\[([^\]]+)\]', i.get('description', '')).group(1)
                                      for i in u.get('items', []) if re.search(r'\[([^\]]+)\]', i.get('description', ''))})
    bad_never = sorted(set(kicad_open) & NEVER)
    if bad_never:
        raise SystemExit(f'freeze4: KiCad reports open connections of {bad_never}: fix the scripted copper and route again')
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
        if mg < -0.0005 and it.kind == 'via' and (why or '').startswith('own pad ZONE'):
            continue  # a router via in the fill of its own pour (the model's own-pad rule is for SMD pads, not fills)
        if mg < -0.0005:
            print(f'  router {it.kind} of {it.net} breaks a clearance ({mg:+.3f}, {why}): removed')
            m.remove(it)
            viol.add(it.net)
    viol |= {d['net'] for d in drops if d['removed']}
    for n in sorted(viol):
        F.prune(m, n)

    def span(n):
        pts = [i.at for i in m.items if i.alive and i.kind == 'pad' and i.src == 'pad' and i.net == n]
        return math.hypot(max(p[0] for p in pts) - min(p[0] for p in pts), max(p[1] for p in pts) - min(p[1] for p in pts)) if pts else 0.0
    nets = set(kicad_open) | viol
    first = sorted(nets, key=lambda n: (span(n), n)) if args.order == 'short' else sorted(nets)
    head = [n for n in args.first.split(',') if n and n in first]
    first = head + [n for n in first if n not in head]
    queue, rounds, t0 = collections.deque(first), 0, time.time()
    touched, failed = set(first), []
    while queue and rounds < args.rounds:
        net = queue.popleft()
        rounds += 1
        if net in NEVER:
            raise SystemExit(f'freeze4: {net} is a plane net; it is never routed here')
        ok, ripped, _nk = fz.connect_all(net, width=width(net), layers=ROUTING, allow_rip=not args.no_rip)
        print(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)', flush=True)
        if not ok:
            failed.append(net)
        queue.extend(n for n in ripped if n not in queue)
        touched |= set(ripped)
    for n in sorted({i.net for i in m.items if i.alive and i.net and i.net not in M.PLANES}):
        F.prune(m, n, srcs=('router', 'new'))
    merged = f6.merge_remainders(m, srcs=('router', 'new'))
    print('split remainders merged back:', len(merged))
    open_, bad = f6.verify(m)
    open_ = {n: k for n, k in open_.items() if n in touched}
    bad = [b for b in bad if not (b[0] == 'dangling' and (b[2] in NEVER or b[2] in model_only))]
    print('open connections', open_, 'clearance violations', len(bad), 'failed', sorted(set(failed)))
    for b_ in bad[:12]:
        print('   ', b_)
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
        for path in f6.chains(segs):
            tracks[src].append([net, lay, w, [B(p) for p in path]])
            nseg[src] += len(path) - 1
    for k in vias:
        vias[k].sort()
        tracks[k].sort()
    run = art.name.rsplit('-', 1)[-1]
    doc = {
        'schema': 'srrx-pwrc-frozen-route-v1',
        'label': 'CI/model input for pcb/boards/PWR_C.json (W2 F2C-FALLBACK, PCB-PWRC-2); not a hardware PASS; bench gates OPEN',
        'source': {'route_run': int(run) if run.isdigit() else '', 'inputs_sha256': report['inputs']['sha256'],
                   'board_sha256': report['board_sha256'], 'router': 'Freerouting 2.5.0 (sr-rx-pcb job Board PWR_C)',
                   'harvest': 'every unlocked track and via of that run, board mm (y up), coordinates as routed'},
        'completion': ('grid A* completion on the frozen copper (0.05 mm grid, exact clearance check 0.15 mm, 0.3 mm to edges, '
                       '0.5 mm hole to hole, the filled scripted pours as copper of their net; through vias 0.65/0.3 mm; F.Cu '
                       'and B.Cu only at the class width of the net, the GND planes In1.Cu/In2.Cu never) by '
                       'build/kicad/boards/PWR_C/freeze/freeze4.py with the PWR_B freeze model, router and finisher'),
        'result': {'open': open_, 'violations': len(bad), 'failed_nets': sorted(set(failed))},
        'fixes': {'via_centre_stubs_fixed': stubs_hit, 'drc_drops': drops, 'merged_split_remainders': len(merged),
                  **({'first': head} if head else {})},
        'guard': None if args.no_guard else guard(),
        'segments': dict(nseg),
        'router_tracks': tracks['router'], 'router_vias': vias['router'],
        'completion_tracks': tracks['new'], 'completion_vias': vias['new'],
    }
    Path(args.out).write_text(f6.dump(doc), encoding='utf-8', newline='\n')
    print('wrote', args.out, dict(nseg), {k: len(v) for k, v in vias.items()})
    return 1 if (open_ or bad) else 0


if __name__ == '__main__':
    raise SystemExit(main())
