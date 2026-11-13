#!/usr/bin/env python3
"""Freeze a 6-layer PWR_A route run and complete it (W2 PWRJ-LAYERS6 study). Needs numpy; offline tool, not run by CI.

  python build/kicad/boards/PWR_A/freeze/freeze6.py --artifact <unzipped pcb-regenerated-PWR_A> [--out FILE] [--no-guard]

The PWR_A counterpart of build/kicad/boards/PWR_B/freeze/freeze6.py (W2 PWRB-R); model.py, router.py and fin.py here are
copies of the PWR_B (CTRL-4) tools. The artifact holds board/PWR_A.kicad_pcb, board/report.json and board/drc.json of a
route run whose inputs equal the spec made by make_board.py without route-frozen-6l.json. The tool
  1. reads the routed 6-layer board (In1.Cu GND plane, In4.Cu GND fill with the E1_CONV_IN strap; routing layers F.Cu,
     In2.Cu, In3.Cu, B.Cu; the hole and edge rule areas count as keepouts);
  2. removes router copper that breaks a clearance in the model and joins its net again;
  3. joins every open connection of KiCad's DRC by grid A* (exact clearance check, rip-up of router copper only when no
     free path exists, ripped nets joined again): power-class nets (BATT, PWR1A, PWR2A, PWR3A) on F.Cu/B.Cu only at their
     2 oz class width (the 0.5 oz inner layers would need 1.8 mm for PWR1A and do not count for PWR3A/BATT), signal nets
     on the four routing layers; nothing goes on a plane layer;
  4. removes dangling router/completion copper, checks every item again and writes route-frozen-6l.json (router copper
     as routed, completion copper, a guard: SHA256 of the pads and of the scripted copper, which make_board.py compares).
With --no-guard it writes no guard (a trial; make_board refuses such a file).
W2 PWR-TOOLS: the via-centre stubs that pcb/board_gen.py added in the run (route-log.json via_centre_stubs) are fixed copper
(fix_stubs), router copper that KiCad's DRC of the run flags as an error is removed and its net joined again (drc_drops), and
completion copper that fails the final exact check is dropped (port of W2 PWRJ F2ENV feb76b8f).
CI/model input only: the CI route run with '[pcb-route PWR_A]' is the check (KiCad 10.0.7 DRC); bench gates stay OPEN.
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
M.configure(COPPER, {'GND': 'In1.Cu'})
M.RLAYERS[:] = ['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu']  # In4.Cu is the GND fill / E1_CONV_IN strap layer (type power): never routed
import fin as F  # noqa: E402
import router as R  # noqa: E402
sys.path.insert(0, str(HERE.parents[4] / 'pcb'))
import board_gen as BG  # noqa: E402
GRAPH = {ref: {'value': c.get('value', '')} for ref, c in BG.load_graph().items()}

F.BOARD_BOX = (100.0, 100.0, 236.0, 210.0)  # KiCad mm: board_gen frame of the 136 x 110 mm L (x + 100, 210 - y)
OUT = HERE.parent / 'route-frozen-6l.json'
# the plane net (class SCRIPTED_GND of make_board.py): never routed here
NEVER = {'GND'}
POWER = ('BATT', 'PWR1A', 'PWR2A', 'PWR3A')
NECK_MAX = 3.0  # mm: longest pad-to-pad neck of a power pair without a class-width path (fin.neck_link)
# Low-current branches of the power nets (fin.branch_pass): test points (no current), capacitors (ripple only; outer
# 2 oz at the PWR2A width 0.4 mm, IPC-2221 about 2 A at +10 degC, MODEL) and resistors of 100 ohm or more (dividers, bias:
# milliamperes); series parts (fuses, shunts, inductors, FETs, diodes, connectors, damper resistors) stay main path
BRANCH_MAX = 12.0   # mm, longest branch path
BRANCH_W = {'TP': 0.25, 'R': 0.25, 'C': 0.4}
ROUTING = tuple(M.RLAYERS)
OUTER = ('F.Cu', 'B.Cu')
K = lambda x, y: (round(x + 100.0, 4), round(210.0 - y, 4))  # board mm -> KiCad mm (frame of pcb/board_gen.py)
B = lambda p: [round(p[0] - 100.0, 4), round(210.0 - p[1], 4)]


def classes():
    """Net -> (class, track width) from the committed PWR_A.kicad_pro (net class patterns; Default 0.15 mm)."""
    pro = json.loads((HERE.parent / 'PWR_A.kicad_pro').read_text(encoding='utf-8'))['net_settings']
    width = {c['name']: c['track_width'] for c in pro['classes']}
    return {p['pattern']: (p['netclass'], width[p['netclass']]) for p in pro['netclass_patterns']}, width['Default']


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


def ohms(value):
    """Resistance of a graph value string ('10k 1%', '4.7 kOhm', '0R33'): ohms or None."""
    import re as _re
    m = _re.match(r'\s*([0-9]+(?:[.,][0-9]+)?)\s*([RrKkMm]?)', str(value).replace('\u03a9', ''))
    if not m:
        return None
    v = float(m.group(1).replace(',', '.'))
    return v * {'': 1.0, 'r': 1.0, 'k': 1e3, 'm': 1e6}[m.group(2).lower()]


def branch_kind(graph):
    """ref -> 'TP' | 'C' | 'R' for parts that may hang on a power net as a low-current branch, else None."""
    def kind(ref):
        if ref is None:
            return None
        if ref.startswith('TP'):
            return 'TP'
        if re.match(r'C\d', ref):
            return 'C'
        if re.match(r'R\d', ref):
            r = ohms(graph.get(ref, {}).get('value', ''))
            return 'R' if r is not None and r >= 100.0 else None
        return None
    return kind


def fix_stubs(m, art):
    """W2 PWR-TOOLS: the stubs pcb/board_gen.py via_centre_stubs drew after the SES import (route-log.json, KiCad mm) come back
    in every run on the same locked copper, so they are fixed copper here (src 'stub'): never removed, ripped or harvested.
    Router copper that breaks their clearance goes instead (route run 43354942122: the frozen E2_AUX_SWITCHED via against
    the LAB5 stub at KiCad (150.95, 181.95), harvested as router copper and removed in place of the stub before).
    Returns (stubs matched, stubs in the log)."""
    path = art / 'board/route-log.json'
    stubs = json.loads(path.read_text(encoding='utf-8')).get('via_centre_stubs', []) if path.is_file() else []
    hit = 0
    for s in stubs:
        e, c = tuple(s['end']), tuple(s['centre'])
        box = (min(e[0], c[0]) - 0.01, min(e[1], c[1]) - 0.01, max(e[0], c[0]) + 0.01, max(e[1], c[1]) + 0.01)
        for it in m.near(s['layer'], box):
            if it.kind != 'track' or it.net != s['net'] or it.src == 'pad':
                continue
            ends = sorted([it.a, it.b])
            if all(math.hypot(q[0] - w[0], q[1] - w[1]) <= 1e-3 for q, w in zip(ends, sorted([e, c]))):
                it.src, it.locked, hit = 'stub', True, hit + 1
    return hit, len(stubs)


def drc_drops(m, drc):
    """W2 PWR-TOOLS: router copper (src 'router': the frozen copper harvested again and new router copper) that KiCad's DRC of
    the run names in an error (clearance, connection_width, track_dangling, ...) is removed before the completion; its net is
    pruned and joined again by the grid A*. Scripted copper, pads and fixed stubs stay. The exact model missed three such
    items in route run 43354942122: the E2_AUX_SWITCHED via against the LAB5 stub (clearance), the 0.81 mm 3V3_Q6A piece at
    J208.1 (connection_width: it leaves the pad over a corner) and a 0.13 mm E2_BONI_EF stub (track_dangling).
    Returns [{type, item, net, removed}]."""
    out = []
    for v in drc.get('violations', []):
        if v.get('severity') != 'error':
            continue
        for d in v.get('items', []):
            desc = d.get('description', '')
            mt = re.match(r'(Track|Via) \[([^\]]+)\]', desc)
            if not mt or 'pos' not in d:
                continue
            kind, net, pos = mt.group(1).lower(), mt.group(2), (float(d['pos']['x']), float(d['pos']['y']))
            ml = re.search(r'length ([0-9.]+) mm', desc)
            ly = re.search(r' on (\S+?),', desc)
            found = None
            for lay in ([ly.group(1)] if kind == 'track' and ly else M.LAYERS):
                for it in m.near(lay, (pos[0] - 0.5, pos[1] - 0.5, pos[0] + 0.5, pos[1] + 0.5)):
                    if it.kind != kind or it.net != net:
                        continue
                    if kind == 'via' and math.hypot(it.at[0] - pos[0], it.at[1] - pos[1]) <= 1e-3:
                        found = it
                    elif kind == 'track' and ml and abs(math.hypot(it.b[0] - it.a[0], it.b[1] - it.a[1]) - float(ml.group(1))) <= 1e-3 \
                            and min(math.hypot(q[0] - pos[0], q[1] - pos[1]) for q in (it.a, it.b)) <= 1e-3:
                        found = it
                    if found:
                        break
                if found:
                    break
            row = {'type': v.get('type'), 'item': desc, 'net': net, 'removed': bool(found and found.alive and found.src == 'router')}
            if row['removed']:
                m.remove(found)
            out.append(row)
    return out


def drop_failing_completion(m):
    """W2 PWR-TOOLS (port of W2 PWRJ F2ENV feb76b8f, PWR_A): completion copper that the final exact check finds too close
    is dropped with its dangling rest (the joins it made stay open). Returns the nets touched."""
    drop = []
    for it in m.items:
        if not (it.alive and it.src == 'new'):
            continue
        if it.kind == 'track':
            mg, _w = m.track_margin(it.net, it.layers[0], it.width, it.a, it.b, ignore={it.id})
        elif it.kind == 'via':
            mg, _w = m.via_margin(it.net, it.at, it.size, it.drill, ignore={it.id})
        else:
            continue
        if mg < -0.0005:
            drop.append(it)
    for it in drop:
        m.remove(it)
    nets = sorted({it.net for it in drop})
    for n in nets:
        F.prune(m, n)
    return len(drop), nets


def guard():
    """The guard make_board.py checks: computed by make_board itself on the spec without the frozen copper."""
    loader = importlib.util.spec_from_file_location('pwr_a_make_board', HERE.parent / 'make_board.py')
    mb = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(mb)
    return mb.frozen_guard_of_spec()


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
    ap.add_argument('--artifact', required=True, help='unzipped pcb-regenerated-PWR_A artifact (board/PWR_A.kicad_pcb, board/report.json)')
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--no-guard', action='store_true', help='trial: write no guard (make_board refuses the file)')
    ap.add_argument('--rounds', type=int, default=400)
    ap.add_argument('--no-rip', action='store_true', help='join only where a free path exists (no rip-up of router copper)')
    ap.add_argument('--prev', help='W2 PWRJ-LAYERS6 ratchet: the route-frozen-6l.json the run was routed with; its locked copper '
                                   'on the board is harvested again together with the new router copper')
    ap.add_argument('--order', choices=('class', 'short'), default='class', help='completion order of the open nets')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    art = Path(args.artifact)
    report = json.loads((art / 'board/report.json').read_text(encoding='utf-8'))
    m = M.Model(str(art / 'board/PWR_A.kicad_pcb'))
    assert m.b.copper_layers == M.LAYERS, m.b.copper_layers
    fz = F.Finisher(m)
    if args.prev:  # ratchet (W2 PWRJ-LAYERS6): the frozen copper of the previous file, locked on this board, is harvested again
        prev = json.loads(Path(args.prev).read_text(encoding='utf-8'))
        segs, pvias = set(), set()
        for key in ('router_tracks', 'completion_tracks'):
            for net, lay, w, path in prev[key]:
                for a, b in zip(path, path[1:]):
                    ka, kb = K(*a), K(*b)
                    segs.add((net, lay, round(w, 4), ka, kb))
                    segs.add((net, lay, round(w, 4), kb, ka))
        for key in ('router_vias', 'completion_vias'):
            for net, x, y, d, drill in prev[key]:
                pvias.add((net, K(x, y)))
        hit = 0
        for it in m.items:
            if not it.alive or it.src != 'scripted':
                continue
            if it.kind == 'track' and (it.net, it.layers[0], round(it.width, 4), (round(it.a[0], 4), round(it.a[1], 4)),
                                       (round(it.b[0], 4), round(it.b[1], 4))) in segs:
                it.src, hit = 'router', hit + 1
            elif it.kind == 'via' and (it.net, (round(it.at[0], 4), round(it.at[1], 4))) in pvias:
                it.src, hit = 'router', hit + 1
        print(f'ratchet: {hit} locked items of {args.prev} harvested again')
    stubs_hit, stubs_all = fix_stubs(m, art)
    print(f'via-centre stubs of the route log held fixed: {stubs_hit} of {stubs_all}')
    cls, default_w = classes()
    width = lambda n: cls.get(n, ('Default', default_w))[1]
    layers = lambda n: OUTER if cls.get(n, ('Default',))[0] in POWER else ROUTING
    drc = json.loads((art / 'board/drc.json').read_text(encoding='utf-8'))
    drops = drc_drops(m, drc)
    print('router copper named in a KiCad DRC error:', drops)
    kicad_open = collections.Counter(n for u in drc.get('unconnected_items', []) for n in
                                     {re.search(r'\[([^\]]+)\]', i.get('description', '')).group(1)
                                      for i in u.get('items', []) if re.search(r'\[([^\]]+)\]', i.get('description', ''))})
    bad_never = sorted(set(kicad_open) & NEVER)
    if bad_never:
        raise SystemExit(f'freeze6: KiCad reports open connections of {bad_never}: fix the GND fan-out and route again')
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
    viol |= {d['net'] for d in drops if d['removed']}
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
    touched, failed, necks, branches = set(first), [], [], []
    while queue and rounds < args.rounds:
        net = queue.popleft()
        rounds += 1
        if net in NEVER:
            raise SystemExit(f'freeze6: {net} is a plane or scripted net; it is never routed here')
        # W2 PWRJ-LAYERS6: pair by pair (a walled-in pair is skipped, the rest of the net is joined); a power pair without
        # a class-width path may take a short pad-to-pad neck (fin.neck_link, NECK_MAX mm), listed in the spec neck_exempt
        ok, ripped, nk = fz.connect_all(net, width=width(net), layers=layers(net), allow_rip=not args.no_rip,
                                        neck=(width(net), NECK_MAX) if layers(net) == OUTER else None)
        necks += nk
        if not ok and layers(net) == OUTER:  # low-current branches of a power net (test points, capacitors, dividers)
            bk = branch_kind(GRAPH)
            okb, br = fz.branch_pass(net, lambda r: bk(r) is not None,
                                     lambda refs: max(BRANCH_W[bk(r)] for r in refs),
                                     lambda refs: ROUTING if all(bk(r) == 'TP' for r in refs) else OUTER, BRANCH_MAX)
            branches += br
            ok = ok or okb
        print(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)', flush=True)
        if not ok:
            failed.append(net)
        queue.extend(n for n in ripped if n not in queue)
        touched |= set(ripped)
    for n in sorted({i.net for i in m.items if i.alive and i.net and i.net not in M.PLANES}):
        F.prune(m, n, srcs=('router', 'new', 'escape'))  # an escape stub whose link failed goes too
    open_, bad = verify(m)
    dropped = (0, [])
    if bad:
        dropped = drop_failing_completion(m)
        print('dropped completion items after the final check:', dropped)
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
        'schema': 'srrx-pwra-frozen-route-v1',
        'label': 'CI/model input for pcb/boards/PWR_A.json (W2 PWRJ-LAYERS6, 6 layers); not a hardware PASS; bench gates OPEN',
        'source': {'route_run': int(run) if run.isdigit() else '', 'inputs_sha256': report['inputs']['sha256'],
                   'board_sha256': report['board_sha256'], 'router': 'Freerouting 2.5.0 (sr-rx-pcb job Board PWR_A)',
                   'harvest': 'every unlocked track and via of that run, board mm (y up), coordinates as routed'},
        'completion': ('grid A* completion on the frozen copper (0.05 mm grid, exact clearance check 0.15 mm, 0.3 mm to edges, '
                       '0.5 mm hole to hole, keepouts incl. the hole and edge rule areas; through vias 0.65/0.3 mm; BATT, '
                       'PWR1A, PWR2A and PWR3A on F.Cu/B.Cu at their 2 oz widths, signals on F.Cu, In2.Cu, In3.Cu, B.Cu, no '
                       'plane layer) by build/kicad/boards/PWR_A/freeze/freeze6.py'),
        'result': {'open': open_, 'violations': len(bad), 'failed_nets': sorted(set(failed))},
        'fixes': {'via_centre_stubs_fixed': stubs_hit, 'drc_drops': drops,
                  'final_check_dropped': {'items': dropped[0], 'nets': dropped[1]}},
        'necks': sorted(necks, key=lambda r: (r['ref'], r['pad'], r['to'])),
        'branches': sorted(branches, key=lambda r: (r['net'], r['refs'])),
        'guard': None if args.no_guard else guard(),
        'segments': dict(nseg),
        'router_tracks': tracks['router'], 'router_vias': vias['router'],
        'completion_tracks': tracks['new'], 'completion_vias': vias['new'],
    }
    if args.prev:  # carry the neck and branch records of the frozen copper harvested again
        for key in ('necks', 'branches'):
            if key in doc:
                doc[key] = sorted(doc[key] + prev.get(key, []), key=lambda r: json.dumps(r, sort_keys=True))
        doc['source']['ratchet_of'] = prev.get('source', {}).get('route_run')
    Path(args.out).write_text(dump(doc), encoding='utf-8', newline='\n')
    print('wrote', args.out, dict(nseg), {k: len(v) for k, v in vias.items()})
    return 1 if (open_ or bad) else 0


if __name__ == '__main__':
    raise SystemExit(main())
