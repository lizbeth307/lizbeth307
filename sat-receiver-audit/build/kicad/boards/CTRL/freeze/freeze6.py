#!/usr/bin/env python3
"""Freeze a 6-layer CTRL route run and complete it (W2 CTRL-4). Needs numpy; offline tool, not run by CI.

  python build/kicad/boards/CTRL/freeze/freeze6.py --artifact <unzipped pcb-regenerated-CTRL> [--out FILE] [--no-guard]

The 6-layer counterpart of freeze_route.py (the 4-layer harvest of route run 43136394379). The artifact holds
board/CTRL.kicad_pcb and board/report.json of a route run whose inputs equal the spec made by make_spec.py without
route-frozen-6l.json. The tool
  1. reads the routed 6-layer board with the freeze model switched to JLC06161H-2116 (In1.Cu GND plane, In4.Cu 3V3_Q6A
     plane; routing layers F.Cu, In2.Cu, In3.Cu, B.Cu);
  2. joins every open connection by grid A* on the routing layers (exact clearance check, rip-up of router copper only
     when no free path exists, ripped nets joined again); nothing goes on a plane layer;
  1b. removes router copper that breaks a clearance (a KiCad DRC error of the route run) and joins its net again;
  3. removes dangling router/completion copper, checks every item again and writes route-frozen-6l.json (router copper
     as routed, completion copper, a guard: SHA256 of the pads and of the scripted copper, which make_spec.py compares).
With --no-guard it writes no guard (a trial on an artifact of another spec; make_spec refuses such a file).
CI/model input only: the CI route run with '[pcb-route CTRL]' is the check (KiCad 10.0.7 DRC); bench gates stay OPEN.
"""
import argparse, collections, json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model as M  # noqa: E402

M.configure(['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu'], {'GND': 'In1.Cu', '3V3_Q6A': 'In4.Cu'})
import fin as F  # noqa: E402
import freeze_route as FR  # noqa: E402  (verify, chains, dump, guard, class_widths: layer-generic through M)

OUT = HERE.parent / 'route-frozen-6l.json'
NEVER = {'GND', '3V3_Q6A', 'E3_FAN5', 'E3_BLOWER_GND', 'LAB5'}  # planes and scripted power nets: never routed here
ROUTING = tuple(M.RLAYERS)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--artifact', required=True, help='unzipped pcb-regenerated-CTRL artifact (board/CTRL.kicad_pcb, board/report.json)')
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--no-guard', action='store_true', help='trial on an artifact of another spec: write no guard')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    art = Path(args.artifact)
    report = json.loads((art / 'board/report.json').read_text(encoding='utf-8'))
    m = M.Model(str(art / 'board/CTRL.kicad_pcb'))
    assert m.b.copper_layers == M.LAYERS, m.b.copper_layers
    fz = F.Finisher(m)
    widths, default_w = FR.class_widths()
    # KiCad's own list of open connections (drc.json); the planes and the scripted power nets are joined by copper overlap
    # that the model (track end in pad, KiCad anchor rule) does not count, so they are taken from KiCad and never routed here
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
    # router copper that breaks a clearance (KiCad DRC errors of the route run, e.g. a router track at a Pico test pad) is
    # removed and its net joined again by the completion
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
    queue, rounds, t0 = collections.deque(sorted(set(kicad_open) | viol)), 0, time.time()
    touched = set(kicad_open) | viol
    while queue and rounds < 80:
        net = queue.popleft()
        rounds += 1
        if net in NEVER:
            raise SystemExit(f'freeze6: {net} is a plane or scripted net; it is never routed here')
        ok, ripped = fz.connect(net, width=widths.get(net, default_w), layers=ROUTING)
        print(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)')
        queue.extend(n for n in ripped if n not in queue)
        touched |= set(ripped)
    for n in sorted({i.net for i in m.items if i.alive and i.net and i.net not in M.PLANES}):
        F.prune(m, n)
    open_, bad = FR.verify(m)
    # nets this tool routed must be joined in the model too; the scripted nets and the model-only islands were checked by
    # KiCad (dangling ends of scripted copper included: KiCad 10 DRC of the route run counted none)
    open_ = {n: k for n, k in open_.items() if n in touched}
    bad = [b for b in bad if not (b[0] == 'dangling' and (b[2] in NEVER or b[2] in model_only))]
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
                vias[it.src].append([it.net] + FR.B(it.at) + [round(it.size, 4), round(it.drill, 4)])
    tracks, nseg = {'router': [], 'new': []}, collections.Counter()
    for (src, net, lay, w), segs in sorted(groups.items()):
        for path in FR.chains(segs):
            tracks[src].append([net, lay, w, [FR.B(p) for p in path]])
            nseg[src] += len(path) - 1
    for k in vias:
        vias[k].sort()
        tracks[k].sort()
    run = art.name.rsplit('-', 1)[-1]
    doc = {
        'schema': 'srrx-ctrl-frozen-route-v1',
        'label': 'CI/model input for pcb/boards/CTRL.json (W2 CTRL-4, 6 layers); not a hardware PASS; bench gates OPEN',
        'source': {'route_run': int(run) if run.isdigit() else report.get('route_run', ''),
                   'inputs_sha256': report['inputs']['sha256'], 'board_sha256': report['board_sha256'],
                   'router': 'Freerouting 2.5.0 (sr-rx-pcb job Board CTRL)',
                   'harvest': 'every unlocked track and via of that run, board mm (y up), coordinates as routed'},
        'completion': ('grid A* completion on the frozen copper (0.05 mm grid, exact clearance check 0.15 mm, 0.3 mm to edges, '
                       '0.5 mm hole to hole, keepouts; through vias 0.65/0.3 mm; routing layers F.Cu, In2.Cu, In3.Cu, B.Cu, no '
                       'plane layer) by build/kicad/boards/CTRL/freeze/freeze6.py'),
        'guard': None if args.no_guard else FR.guard(),
        'drop_scripted': {'tracks': [], 'vias': []},
        'segments': dict(nseg),
        'router_tracks': tracks['router'], 'router_vias': vias['router'],
        'completion_tracks': tracks['new'], 'completion_vias': vias['new'],
    }
    Path(args.out).write_text(FR.dump(doc), encoding='utf-8', newline='\n')
    print('wrote', args.out, dict(nseg), {k: len(v) for k, v in vias.items()})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
