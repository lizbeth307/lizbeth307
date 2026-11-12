#!/usr/bin/env python3
"""Script the long PWR_B nets before Freerouting (W2 PWRB-R route study). Needs numpy; offline tool, not run by CI.

  python build/kicad/boards/PWR_B/freeze/prefreeze.py --artifact <unzipped pcb-regenerated-PWR_B> [--out FILE]

The S02 headers J202 / J203 / J201 and J506 are parked in the arm (build/15 W2 PCB-PWRB-2), so about 35 signals and the
LNA / USB power nets run from the J209 contact rows and the bar parts to the arm, 50-160 mm each; with the 50 PWR-A
cut-outs as copper keep-outs Freerouting 2.5.0 leaves 69-89 of them open in its 33 min (route runs 43288017730,
43294945712). This tool lays those cross nets first, on the bare board (pads, scripted copper, keep-outs and edges of the
artifact board; its router copper is dropped), by the grid A* of fin.py / router.py: signals prefer In2.Cu (F.Cu and B.Cu
cost more per mm, so the outer layers stay free for the local nets), power classes use F.Cu / B.Cu at their class width.
It writes route-frozen.json with these links as completion copper and no router copper; make_spec.py locks them, and the
next CI route ('[pcb-route PWR_B]') lets Freerouting route the rest around them. freeze_route.py then harvests that run
(--keep-frozen) and completes it. CI/model input only; bench gates stay OPEN.
"""
import argparse, collections, json, math, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model as M  # noqa: E402
import router as R  # noqa: E402
import fin as F  # noqa: E402
import freeze_route as FR  # noqa: E402

BAR_X, ARM_X = 44.0, 40.0   # board mm: a net with pads right of BAR_X and left of ARM_X crosses from the bar to the arm
OUTER_BIAS = 2.0            # extra cost per mm on F.Cu / B.Cu for a signal (In2.Cu costs 1, the outer layers 3)


def cross_nets(m, never):
    """Nets with pads in the bar (x > BAR_X) and in the arm or corner (x < ARM_X): the two-pad signals first in the order
    of their bar pad (one bus, no crossings among them where the order holds), then the others, longest pad span first."""
    pads = collections.defaultdict(list)
    for it in m.items:
        if it.kind == 'pad' and it.net and it.net not in never:
            pads[it.net].append(FR.B(it.at))
    two, rest = [], []
    for net, ps in pads.items():
        xs, ys = [p[0] for p in ps], [p[1] for p in ps]
        if max(xs) > BAR_X and min(xs) < ARM_X:
            if len(ps) == 2:
                two.append((-max(xs), net))
            else:
                rest.append((-(max(xs) - min(xs) + max(ys) - min(ys)), net))
    return [n for _s, n in sorted(two)] + [n for _s, n in sorted(rest)]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--artifact', required=True, help='unzipped pcb-regenerated-PWR_B artifact of the current placement')
    ap.add_argument('--out', default=str(FR.OUT))
    ap.add_argument('--nets', default='', help='comma list instead of every cross net')
    ap.add_argument('--margin-steps', type=float, default=0.25)
    ap.add_argument('--pad-inset', type=float, default=0.13)
    ap.add_argument('--max-rounds', type=int, default=150)
    ap.add_argument('--no-rip', action='store_true', help='a cross net never rips an earlier one (it stays open instead)')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    R.PAD_INSET, R.MARGIN_STEPS = args.pad_inset, args.margin_steps
    art = Path(args.artifact)
    report = json.loads((art / 'board/report.json').read_text(encoding='utf-8'))
    ms = FR.load_make_spec()
    cur = FR.current(ms)
    m = M.Model(str(art / 'board/PWR_B.kicad_pcb'))
    ok, counts = FR.scripted_matches(m, cur)
    if not ok:
        raise SystemExit(f'prefreeze: the artifact locked copper is not the scripted copper of the current spec {counts}')
    for it in m.items:  # bare board: pads, scripted copper, keep-outs, edges
        if it.alive and it.src == 'router':
            m.remove(it)
    widths, classes, default_w = FR.class_widths()
    nets = [n for n in args.nets.split(',') if n] or cross_nets(m, cur['never'])
    print(len(nets), 'cross nets:', nets, flush=True)
    fz = F.Finisher(m)
    failed, t0 = [], time.time()
    queue, rounds = collections.deque(nets), 0
    while queue and rounds < args.max_rounds:
        net = queue.popleft()
        rounds += 1
        signal = classes.get(net, 'Default') == 'Default'
        layers = FR.SIGNAL_LAYERS if signal else FR.POWER_LAYERS
        bias = [OUTER_BIAS if l != 'In2.Cu' else 0.0 for l in layers] if signal else None
        ok, ripped = fz.connect(net, allow_rip=not args.no_rip, width=widths.get(net, default_w), layers=layers, bias=bias,
                                margin=25.0, max_iter=40)
        for it in m.items:  # a pre-route may be ripped by a later cross net (local rip of fin.py), which then joins it again
            if it.alive and it.src == 'new' and it.net == net:
                it.src = 'router'
        print(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)', flush=True)
        if not ok:
            failed.append(net)
        queue.extend(n for n in ripped if n not in queue)
    for n in nets:
        F.prune(m, n)
    open_, bad = FR.verify(m)
    open_ = {n: k for n, k in open_.items() if n in nets}
    print('cross nets still open', open_, 'problems', len(bad), 'failed', failed)
    for b_ in bad[:20]:
        print('   ', b_)
    if bad:
        return 1
    groups, vias = collections.defaultdict(list), []
    for it in m.items:
        if it.alive and it.src in ('new', 'router'):
            if it.kind == 'track':
                groups[(it.net, it.layers[0], round(it.width, 4))].append((it.a, it.b))
            elif it.kind == 'via':
                vias.append([it.net] + FR.B(it.at) + [round(it.size, 4), round(it.drill, 4)])
    tracks, nseg = [], 0
    for (net, lay, w), segs in sorted(groups.items()):
        for path in FR.chains(segs):
            tracks.append([net, lay, w, [FR.B(p) for p in path]])
            nseg += len(path) - 1
    tracks.sort()
    vias.sort()
    layer_mm = collections.Counter()
    for it in m.items:
        if it.alive and it.src in ('new', 'router') and it.kind == 'track':
            layer_mm[it.layers[0]] += math.hypot(it.a[0] - it.b[0], it.a[1] - it.b[1])
    run = int(art.name.rsplit('-', 1)[-1]) if art.name.rsplit('-', 1)[-1].isdigit() else None
    joined = [n for n in nets if n not in open_]
    doc = {
        'schema': 'srrx-pwrb-frozen-route-v1',
        'label': 'CI/model input for pcb/boards/PWR_B.json (W2 PWRB-R route study); not a hardware PASS; bench gates OPEN',
        'source': {'route_run': run, 'inputs_sha256': report['inputs']['sha256'], 'board_sha256': report['board_sha256'],
                   'router': 'none: pads, scripted copper and keep-outs of that run board, its router copper dropped',
                   'harvest': 'none (pre-route of the cross nets)'},
        'completion': ('pre-route of the bar-to-arm cross nets by the grid A* of build/kicad/boards/PWR_B/freeze (0.05 mm grid, '
                       'exact clearance check 0.15 mm, 0.3 mm to edges, 0.5 mm hole to hole, keep-outs incl. the PWR-A '
                       'cut-outs, path ends 0.13 mm inside pads; vias 0.7/0.3 mm; signals prefer In2.Cu, power classes on '
                       'F.Cu / B.Cu) by build/kicad/boards/PWR_B/freeze/prefreeze.py'),
        'summary': (f'Pre-route of {len(joined)} of {len(nets)} bar-to-arm cross nets ({nseg} segments, {len(vias)} vias; '
                    f'copper mm by layer { {k: round(v, 1) for k, v in sorted(layer_mm.items())} }); still open: {open_ or "none"}. '
                    'Freerouting routes the rest around this locked copper.'),
        'guard': cur['guard'],
        'open_before': {}, 'ripped': {}, 'open_after': open_,
        'segments': {'new': nseg},
        'router_tracks': [], 'router_vias': [],
        'completion_tracks': tracks, 'completion_vias': vias,
    }
    Path(args.out).write_text(FR.dump(doc), encoding='utf-8', newline='\n')
    print('wrote', args.out, nseg, 'segments', len(vias), 'vias', {k: round(v, 1) for k, v in layer_mm.items()})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
