#!/usr/bin/env python3
"""Freeze a 6-layer PWR_B route run and complete it (W2 PWRB-R layers6 study). Needs numpy; offline tool, not run by CI.

  python build/kicad/boards/PWR_B/freeze/freeze6.py --artifact <unzipped pcb-regenerated-PWR_B> [--out FILE] [--no-guard]
         [--no-rip] [--order class|short|fanout] [--prev route-frozen-6l.json] [--renet] [--first NET,NET,...]
         [--inner-bias X]

The PWR_B counterpart of build/kicad/boards/CTRL/freeze/freeze6.py (W2 CTRL-4, origin/wip/w2-ctrl4-layers6); model.py,
router.py and fin.py here are copies of the CTRL tools. The artifact holds board/PWR_B.kicad_pcb, board/report.json and
board/drc.json of a route run whose inputs equal the spec made by make_spec.py without route-frozen-6l.json. The tool
  1. reads the routed 6-layer board (In1.Cu GND plane, In4.Cu 3V3_Q6A plane; routing layers F.Cu, In2.Cu, In3.Cu, B.Cu;
     the planned_cutouts rule areas (KO_CUT_*) of the PWR-A cut-outs and the edge strips count as keepouts);
  2. removes router copper that breaks a clearance in the model and joins its net again;
  3. joins every open connection of KiCad's DRC by grid A* (exact clearance check, rip-up of router copper only when no
     free path exists, ripped nets joined again): power-class nets (PWR1A) on F.Cu/B.Cu only at their class width (the
     0.5 oz inner layers would need 1.8 mm), signal nets on the four routing layers; nothing goes on a plane layer;
     W2 PWR-L6-PLACE fourth pass, combined: the PWR1A sub-classes of the copper option (pcb/generated/stackup-6l.json
     inner_classes, PWR05A) on the four routing layers at the outer width on F.Cu/B.Cu and the inner width on In2/In3,
     with an extra cost per mm on the outer layers (--inner-bias), so they leave the outer copper to the PWR1A nets;
  4. removes dangling router/completion copper, checks every item again and writes route-frozen-6l.json (router copper
     as routed, completion copper, a guard: SHA256 of the pads and of the scripted copper, which make_spec.py compares).
With --no-guard it writes no guard (a trial; make_spec refuses such a file).
W2 PWR-TOOLS: as build/kicad/boards/PWR_A/freeze/freeze6.py, the via-centre stubs of the run (route-log.json) are fixed
copper (fix_stubs) and router copper that KiCad's DRC of the run names in an error is removed and joined again (drc_drops).
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
# W2 PWR-L6-PLACE third pass, stage 2: the planned nets of route-planned-6l.json are scripted copper too (make_spec PLANNED)
_PLANNED = HERE.parent / 'route-planned-6l.json'
if _PLANNED.is_file():  # W2 PWR-L6-PLACE fourth pass: a planned 'link' is locked copper of a net that freeze6 still completes
    NEVER |= {n for n, d in json.loads(_PLANNED.read_text(encoding='utf-8'))['nets'].items() if d.get('kind') != 'link'}
ROUTING = tuple(M.RLAYERS)
OUTER = ('F.Cu', 'B.Cu')
K = lambda x, y: (round(x + 100.0, 4), round(210.0 - y, 4))  # board mm -> KiCad mm (frame of pcb/board_gen.py)
B = lambda p: [round(p[0] - 100.0, 4), round(210.0 - p[1], 4)]


def classes():
    """Net -> (class, track width) from the committed PWR_B.kicad_pro (net class patterns; Default 0.15 mm). A PWR1A
    sub-class of the copper option (inner_classes) has the width {layer: width} of its four routing layers."""
    pro = json.loads((HERE.parent / 'PWR_B.kicad_pro').read_text(encoding='utf-8'))['net_settings']
    width = {c['name']: c['track_width'] for c in pro['classes']}
    width.update(inner_widths())
    return {p['pattern']: (p['netclass'], width[p['netclass']]) for p in pro['netclass_patterns']}, width['Default']


COPPER_OPTION = 'outer_2oz'  # make_spec.py COPPER_OPTION


def inner_widths():
    """W2 PWR-L6-PLACE fourth pass, combined: {class: {layer: width}} of the PWR1A sub-classes of the copper option
    (pcb/generated/stackup-6l.json inner_classes): outer width on F.Cu/B.Cu, inner width on In2.Cu/In3.Cu."""
    doc = json.loads((HERE.parents[4] / 'pcb/generated/stackup-6l.json').read_text(encoding='utf-8'))
    out = {}
    for name, c in (doc['copper_options'][COPPER_OPTION].get('inner_classes') or {}).items():
        out[name] = {l: (c['outer_min_width_mm'] if l in ('F.Cu', 'B.Cu') else c['inner_min_width_mm']) for l in ROUTING}
    return out


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


FANOUT_TO, FANOUT_THEN = 'J203', ('I2C2_SCL', 'I2C2_SDA')


def fanout_first(m, nets, span):
    """W2 PWR-L6-PLACE third pass (judge decision ESC-JUDGE, --order fanout): the nets that join a J209 lower-row contact to the
    top-entry J203 of PWR-B zone 2 first, right to left along J209 (their short fan-out runs take the escape band before any long
    link crosses it), then I2C2 (its B2B contacts J209.43 / .45 sit between the fan-out contacts), then the rest shortest first
    (--order short). In the judge's model this order left 11 open connections against 17 for --order short (MODEL)."""
    pads = collections.defaultdict(dict)
    for i in m.items:
        if i.alive and i.kind == 'pad' and i.net in nets and i.ref in (B2B, FANOUT_TO):
            pads[i.net].setdefault(i.ref, i.at)
    fan = sorted((n for n in nets if B2B in pads[n] and FANOUT_TO in pads[n]), key=lambda n: (-pads[n][B2B][0], n))
    then = [n for n in FANOUT_THEN if n in nets and n not in fan]
    rest = sorted(set(nets) - set(fan) - set(then), key=lambda n: (span(n), n))
    print('fan-out order:', fan, then)
    return fan + then + rest


def renet(m):
    """W2 PWR-L6-PLACE fourth pass, probe C (J202 <-> J203 pin swap): every pad whose net in the design graph (design/E*.json)
    differs from the routed board takes the graph net, so a ratchet (--prev) can carry a route across a pin-map change of the
    board's own headers. All router copper of the old and the new nets of such pads goes (it was routed to the old pads) and
    those nets are joined again by the completion. Returns ({ref.pad: [old, new]}, nets to join, router items removed)."""
    import board_gen as bg  # pcb/ is on the path (model.py)
    graph = bg.load_graph()
    pins = {(ref, str(p['number'])): (None if p.get('nc') else p.get('net')) for ref, c in graph.items() for p in c['pins']}
    changed, nets = {}, set()
    for it in m.items:
        if it.alive and it.kind == 'pad' and (it.ref, str(it.pad)) in pins and pins[(it.ref, str(it.pad))] != it.net:
            new = pins[(it.ref, str(it.pad))]
            changed[f'{it.ref}.{it.pad}'] = [it.net, new]
            nets |= {it.net, new} - {None}
            it.net = new
    gone = 0
    for it in m.items:
        if it.alive and it.kind in ('track', 'via') and it.net in nets:
            if it.src != 'router':
                raise SystemExit(f'freeze6 --renet: locked {it.kind} of {it.net} is not router copper (use --prev)')
            m.remove(it)
            gone += 1
    return dict(sorted(changed.items())), nets, gone


TINY = 0.15  # mm: a split remainder shorter than this is merged back (W2 PWR-L6-PLACE fourth pass, combined)


def _at_point(m, net, lay, q, skip):
    n = 0
    for ot in m.near(lay, (q[0] - 0.01, q[1] - 0.01, q[0] + 0.01, q[1] + 0.01)):
        if ot.id in skip or ot.net != net:
            continue
        if ot.kind == 'track' and min(math.dist(q, ot.a), math.dist(q, ot.b)) < 1e-6:
            n += 1
        elif ot.kind in ('via', 'pad') and ot.shape.dist(*q) <= 1e-6:
            n += 1
    return n


def merge_remainders(m, srcs=('router', 'new', 'escape')):
    """W2 PWR-L6-PLACE fourth pass (probe A push 2, route run 43537055803: KiCad 10.0.7 track_dangling on two split
    remainders, FLT_SB_LNA In2.Cu 0.0904 mm and LNB13V2 F.Cu 0.0077 mm): a router / completion track shorter than TINY that
    shares an end, collinear, with one other such track of the same net, layer and width, and no other item at that end, is
    merged back into it (same copper). Returns [(net, layer, length)]."""
    done, changed = [], True
    while changed:
        changed = False
        for t in list(m.items):
            if not (t.alive and t.kind == 'track' and t.src in srcs and math.dist(t.a, t.b) < TINY):
                continue
            lay = t.layers[0]
            for q, far in ((t.a, t.b), (t.b, t.a)):
                partner = None
                for u in m.near(lay, (q[0] - 0.01, q[1] - 0.01, q[0] + 0.01, q[1] + 0.01)):
                    if u.id == t.id or u.kind != 'track' or u.net != t.net or u.src not in srcs or abs(u.width - t.width) > 1e-9:
                        continue
                    ufar = u.b if math.dist(u.a, q) < 1e-6 else u.a if math.dist(u.b, q) < 1e-6 else None
                    if ufar is None:
                        continue
                    v1, v2 = (q[0] - ufar[0], q[1] - ufar[1]), (far[0] - q[0], far[1] - q[1])
                    cross = v1[0] * v2[1] - v1[1] * v2[0]
                    if abs(cross) / (math.hypot(*v1) * math.hypot(*v2) + 1e-12) < 1e-3 and v1[0] * v2[0] + v1[1] * v2[1] > 0:
                        partner = (u, ufar)
                        break
                if partner is None or _at_point(m, t.net, lay, q, {t.id, partner[0].id}) > 0:
                    continue
                u, ufar = partner
                m.remove(t)
                m.remove(u)
                m.add_track(t.net, lay, t.width, ufar, far, src=u.src)
                done.append((t.net, lay, round(math.dist(t.a, t.b), 4)))
                changed = True
                break
    return done


def short_pieces(m):
    """Tracks shorter than their width with an end that meets no other item of the net exactly (a track end, a via or a
    pad): the pattern KiCad 10.0.7 flags as track_dangling (route run 43537055803); the model's end test accepts such an
    end inside another track's copper, so it is listed here."""
    out = []
    for t in m.items:
        if not (t.alive and t.kind == 'track') or math.dist(t.a, t.b) >= t.width:
            continue
        for e in (t.a, t.b):
            if not _at_point(m, t.net, t.layers[0], e, {t.id}) and not any(
                    o.kind in ('via', 'pad') and o.shape.dist(*e) <= 1e-4 for o in
                    m.near(t.layers[0], (e[0] - 0.01, e[1] - 0.01, e[0] + 0.01, e[1] + 0.01)) if o.net == t.net):
                out.append(('short piece', t.net, B(e), t.layers[0], round(math.dist(t.a, t.b), 4), t.src))
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
    bad += short_pieces(m)
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


def fix_stubs(m, art):
    """W2 PWR-TOOLS: the stubs pcb/board_gen.py via_centre_stubs drew after the SES import (route-log.json, KiCad mm) come back
    in every run on the same locked copper, so they are fixed copper here (src 'stub'): never removed, ripped or harvested.
    Router copper that breaks their clearance goes instead (PWR_A route run 43354942122: the frozen E2_AUX_SWITCHED via against
    the LAB5 stub at KiCad (150.95, 181.95), harvested as router copper and removed in place of the stub before; the same tool on PWR_B).
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
    ap.add_argument('--prev', help='W2 PWRJ-LAYERS6 ratchet: the route-frozen-6l.json the run was routed with; its locked copper '
                                   'on the board is harvested again together with the new router copper')
    ap.add_argument('--order', choices=('class', 'short', 'fanout'), default='class',
                    help='completion order of the open nets (fanout: W2 PWR-L6-PLACE third pass, fanout_first)')
    ap.add_argument('--renet', action='store_true', help='W2 PWR-L6-PLACE fourth pass: pads take the nets of the design graph '
                                                           '(a pin swap since the run); their old and new nets are joined again')
    ap.add_argument('--first', default='', help='comma-separated nets joined first, in this order (then --order)')
    ap.add_argument('--inner-bias', type=float, default=1.0, help='W2 PWR-L6-PLACE fourth pass, combined: extra cost per mm on '
                                                                   'F.Cu/B.Cu for the inner-routed power sub-classes (PWR05A)')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    art = Path(args.artifact)
    report = json.loads((art / 'board/report.json').read_text(encoding='utf-8'))
    m = M.Model(str(art / 'board/PWR_B.kicad_pcb'))
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
    renetted, renet_nets, renet_gone = renet(m) if args.renet else ({}, set(), 0)
    if args.renet:
        print(f'renet: {len(renetted)} pads take the graph net, {renet_gone} router items of {sorted(renet_nets)} removed')
    stubs_hit, stubs_all = fix_stubs(m, art)
    print(f'via-centre stubs of the route log held fixed: {stubs_hit} of {stubs_all}')
    cls, default_w = classes()
    width = lambda n: cls.get(n, ('Default', default_w))[1]
    inner = inner_widths()
    layers = lambda n: ROUTING if cls.get(n, ('Default',))[0] in inner else OUTER if 'PWR' in cls.get(n, ('Default',))[0] else ROUTING
    bias = lambda n: [args.inner_bias if l in OUTER else 0.0 for l in ROUTING]         if cls.get(n, ('Default',))[0] in inner and args.inner_bias else None
    drc = json.loads((art / 'board/drc.json').read_text(encoding='utf-8'))
    drops = drc_drops(m, drc)
    print('router copper named in a KiCad DRC error:', drops)
    kicad_open = collections.Counter(n for u in drc.get('unconnected_items', []) for n in
                                     {re.search(r'\[([^\]]+)\]', i.get('description', '')).group(1)
                                      for i in u.get('items', []) if re.search(r'\[([^\]]+)\]', i.get('description', ''))})
    bad_never = sorted(set(kicad_open) & NEVER)
    if bad_never:
        raise SystemExit(f'freeze6: KiCad reports open connections of {bad_never}: fix the scripted copper and route again')
    kicad_open.update({n: 1 for n in renet_nets if n not in kicad_open})
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
    if args.order == 'fanout':
        first = fanout_first(m, set(kicad_open) | viol, span)
    elif args.order == 'short':
        first = sorted(set(kicad_open) | viol, key=lambda n: (span(n), n))
    else:
        first = sorted(set(kicad_open) | viol, key=lambda n: (layers(n) != OUTER, n))
    head = [n for n in args.first.split(',') if n and n in first]
    first = head + [n for n in first if n not in head]
    queue, rounds, t0 = collections.deque(first), 0, time.time()
    touched, failed, necks = set(first), [], []
    while queue and rounds < args.rounds:
        net = queue.popleft()
        rounds += 1
        if net in NEVER:
            raise SystemExit(f'freeze6: {net} is a plane or scripted net; it is never routed here')
        if layers(net) == OUTER:
            for pad, e in j209_escape(m, net):
                print(f'  {net}: J209.{pad} escape stub {ESCAPE_W} mm to {e}')
        # W2 PWRJ-LAYERS6: pair by pair (a walled-in pair is skipped, the rest of the net is joined)
        ok, ripped, nk = fz.connect_all(net, width=width(net), layers=layers(net), allow_rip=not args.no_rip, bias=bias(net))
        necks += nk
        print(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)', flush=True)
        if not ok:
            failed.append(net)
        queue.extend(n for n in ripped if n not in queue)
        touched |= set(ripped)
    for n in sorted({i.net for i in m.items if i.alive and i.net and i.net not in M.PLANES}):
        F.prune(m, n, srcs=('router', 'new', 'escape'))  # an escape stub whose link failed goes too
    merged = merge_remainders(m)
    print('split remainders merged back:', len(merged))
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
                       'F.Cu/B.Cu, PWR05A on all four at 0.2 mm outer / 0.5 mm inner, signals on F.Cu, In2.Cu, In3.Cu, B.Cu, no '
                       'plane layer) by '
                       'build/kicad/boards/PWR_B/freeze/freeze6.py'),
        'result': {'open': open_, 'violations': len(bad), 'failed_nets': sorted(set(failed))},
        'fixes': {'via_centre_stubs_fixed': stubs_hit, 'drc_drops': drops, 'merged_split_remainders': len(merged),
                  **({'renet': renetted, 'first': head} if args.renet or head else {})},
        'necks': sorted(necks, key=lambda r: (r['ref'], r['pad'], r['to'])),
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
