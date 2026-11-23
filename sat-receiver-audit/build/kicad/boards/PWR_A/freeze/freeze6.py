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
W2 PWR-L6-SCRIPT: the scripted nets of the board (classes SCRIPTED_* of PWR_A.kicad_pro: the converter stages and the 'power'
nets of script-planned-6l.json) are never routed here, like GND; the necks of neck_link and the branches of branch_pass follow
the exemption policy of the board (pcb/check_boards.py exemption_role); router copper of a net without a pad in a converter zone
3'/4' (board-spec.json converter_zones) on F.Cu or In1.Cu over that zone is removed and the net joined again, and the A* keeps
such nets off F.Cu there.
W2 PWR-L6-ROUTE: --spec-zones models the scripted pours (pre_route zones of board-spec.json that carry clearance_mm) by their
outlines, as plan6.py and make_board.py draw them, in place of the fills of the routed board: route run 43591929140 filled
them at the KiCad zone default 0.3 mm (several filled nothing), and the spec now fills them at the project clearance. KiCad
open connections of scripted nets are then not fatal: they are listed (result.scripted_open_in_run) and left to the
scripted copper, which the next run measures.
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
BRANCH_W = {'TP': 0.25, 'R': 0.25, 'C': 0.4, 'S': 0.25}
ROUTING = tuple(M.RLAYERS)
OUTER = ('F.Cu', 'B.Cu')
K = lambda x, y: (round(x + 100.0, 4), round(210.0 - y, 4))  # board mm -> KiCad mm (frame of pcb/board_gen.py)
B = lambda p: [round(p[0] - 100.0, 4), round(210.0 - p[1], 4)]


def policy(m):
    """(branch test, neck test) of the exemption policy on the routed board (W2 PWR-L6-SCRIPT; pcb/check_boards.py roles)."""
    CB = M.cb
    graph = BG.load_graph()
    nc = json.loads((HERE.parents[4] / 'pcb/generated/netclasses.json').read_text(encoding='utf-8'))
    lookup = lambda n: (n, nc['nets'].get(n, {}).get('class', 'SIG'))  # noqa: E731
    spec = {'b2b': [{'ref': 'J208'}]}
    cache = {}

    def role(ref, num):
        if (ref, num) not in cache:
            cache[(ref, num)] = CB.exemption_role(m.b, spec, graph, ref, num, lookup, nc['classes'])[0]
        return cache[(ref, num)]

    def branch_ok(ref, net):
        pads = [p for p in m.b.pads if p['ref'] == ref and p['net'] == net]
        return bool(pads) and all(role(ref, p['number']) in CB.EXEMPT_BRANCH_ROLES for p in pads)

    def neck_ok(pad, width, length):
        rec = next((p for p in m.b.pads if p['ref'] == pad.ref and p['number'] == pad.pad), None)
        if rec is None or role(pad.ref, pad.pad) in CB.EXEMPT_NECK_FORBIDDEN:
            return False
        return width + 1e-9 >= min(rec['w'], rec['h']) and length <= max(rec['w'], rec['h']) + 1e-9
    return branch_ok, neck_ok


CZ_LAYERS = ['F.Cu', 'In1.Cu']  # the converter-zone layers of board-spec.json (W2 PWR-L6-SCRIPT review fix RV-PWRL6-PRE-C-02: + B.Cu)


def converter_zone_rule(m):
    """[(poly KiCad mm, own nets)] of board-spec.json converter_zones (W2 PWR-L6-SCRIPT), on CZ_LAYERS."""
    path = HERE.parent / 'board-spec.json'
    cz = (json.loads(path.read_text(encoding='utf-8')).get('converter_zones') or {}) if path.is_file() else {}
    out = []
    CZ_LAYERS[:] = cz.get('layers') or ['F.Cu', 'In1.Cu']
    for _zi, z in sorted((cz.get('zones') or {}).items()):
        x0, y0, x1, y1 = z['rect']
        a, b = K(x0, y1), K(x1, y0)
        out.append((M.cb.Poly([(a[0], a[1]), (b[0], a[1]), (b[0], b[1]), (a[0], b[1])]), set(z['own_nets'])))
    return out


def classes():
    """Net -> (class, track width) from the committed PWR_A.kicad_pro (net class patterns; Default 0.15 mm)."""
    pro = json.loads((HERE.parent / 'PWR_A.kicad_pro').read_text(encoding='utf-8'))['net_settings']
    width = {c['name']: c['track_width'] for c in pro['classes']}
    return {p['pattern']: (p['netclass'], width[p['netclass']]) for p in pro['netclass_patterns']}, width['Default']


# W2 PWR-L6-ROUTE: port of the W2 PWR-L6-PLACE fourth-pass helpers of build/kicad/boards/PWR_B/freeze/freeze6.py (unchanged):
# split remainders merged back and short pieces whose end meets nothing exactly (the KiCad 10.0.7 track_dangling pattern)
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
        # PWR_A: router and completion copper only (the scripted copper and the stubs are KiCad-checked by the route run, as in
        # fin.dangling)
        if not (t.alive and t.kind == 'track') or t.src not in ('router', 'new', 'escape') or math.dist(t.a, t.b) >= t.width:
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
    bad += short_pieces(m)
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
        elif it.kind == 'via' and it.src == 'vip':  # probe Y: a via in its own SMD pad
            mg, why = vip_margin(m, it.net, it.at, it.size, it.drill, ignore={it.id})
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


def branch_kind(graph, sense=False):
    """ref -> 'TP' | 'C' | 'R' for parts that may hang on a power net as a low-current branch, else None. W2 PWR-A closure
    round 1, probe Y (sense=True): an IC ('U') is 'S', a sense/logic pin branch; the caller's role test (pcb/check_boards.py
    exemption_role sense_logic_pin) decides per pad."""
    def kind(ref):
        if ref is None:
            return None
        if ref.startswith('TP'):
            return 'TP'
        if sense and re.match(r'U\d', ref):
            return 'S'
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


def pad_escapes(m, drc, width):
    """W2 PWR-L6-ROUTE: a pad that KiCad's DRC of the run names in a connection_width error together with a router track (the
    track left the pad over its corner, route run 45019150709: U203.1, U109.4, J208.1, U202.7, U213.20) gets a stub of its net's
    width straight out along the pad's long axis, away from the footprint centre, before the completion (src 'escape': kept while
    its link is open, pruned at the end if the link fails). The piece of the run is already removed by drc_drops. Power-class and
    never-routed nets are left alone. Returns [{net, pad, width, to}] (board mm)."""
    out = []
    for v in drc.get('violations', []):
        if v.get('type') != 'connection_width' or v.get('severity') != 'error':
            continue
        descs = [d.get('description', '') for d in v.get('items', [])]
        pads = [re.match(r'Pad (\S+) \[([^\]]+)\] of (\S+)', d) for d in descs]
        pads = [p for p in pads if p]
        if not pads or not any(d.startswith('Track [') for d in descs):
            continue
        num, net, ref = pads[0].group(1), pads[0].group(2), pads[0].group(3)
        if net in NEVER or width(net) > 0.15 + 1e-9:
            continue
        pad = next((i for i in m.items if i.alive and i.kind == 'pad' and i.src == 'pad' and i.ref == ref and i.pad == num), None)
        if pad is None or not any(l in ('F.Cu', 'B.Cu') for l in pad.layers):
            continue
        lay = next(l for l in ('F.Cu', 'B.Cu') if l in pad.layers)
        own = [i.at for i in m.items if i.alive and i.kind == 'pad' and i.src == 'pad' and i.ref == ref]
        cx, cy = sum(p[0] for p in own) / len(own), sum(p[1] for p in own) / len(own)
        x0, y0, x1, y1 = pad.shape.bbox
        horiz = (x1 - x0) >= (y1 - y0)
        d = (pad.at[0] - cx) if horiz else (pad.at[1] - cy)
        if abs(d) < 1e-6:
            continue
        sign = 1.0 if d > 0 else -1.0
        half = ((x1 - x0) if horiz else (y1 - y0)) / 2
        w = width(net)
        for extra in (0.3, 0.45, 0.6, 0.8, 1.0):
            L = half + extra
            e = (round(pad.at[0] + sign * L, 4), pad.at[1]) if horiz else (pad.at[0], round(pad.at[1] + sign * L, 4))
            mg, _why = m.track_margin(net, lay, w, pad.at, e)
            if mg >= 0.005:
                m.add_track(net, lay, w, pad.at, e, src='escape')
                out.append({'net': net, 'pad': f'{ref}.{num}', 'width': w, 'to': B(e)})
                break
    return out


def drop_failing_completion(m):
    """W2 PWR-TOOLS (port of W2 PWRJ F2ENV feb76b8f, PWR_A): completion copper that the final exact check finds too close
    is dropped with its dangling rest (the joins it made stay open). Returns the nets touched."""
    drop = []
    for it in m.items:
        if not (it.alive and it.src in ('new', 'vip')):
            continue
        if it.kind == 'track':
            mg, _w = m.track_margin(it.net, it.layers[0], it.width, it.a, it.b, ignore={it.id})
        elif it.kind == 'via' and it.src == 'vip':
            mg, _w = vip_margin(m, it.net, it.at, it.size, it.drill, ignore={it.id})
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


# W2 PWR-A closure round 1, probe Y (--pad-vias): a through via in the SMD pad of a walled-in pin. The blocker split of route
# run 45062920789 (W2 F2C-FALLBACK part 2) left 15 signal nets with no 0.15 mm path on any routing layer: their pins are boxed in
# on their own layer by pads, scripted pours and planned copper, and no via site is reachable. A via in the pad takes such a pin
# straight to In2.Cu/In3.Cu. PWR_B carries the same kind of via (VIP-U215-6/7, W2 PWR-L6-PLACE third pass); JLC fills and caps
# via-in-pad by default from 6 layers (pcb/generated/stackup-6l.json capabilities.via_in_pad). The via is the project via
# 0.6/0.3 mm (PWR_A.kicad_pro min_via_diameter 0.6, annulus 0.15); it keeps the KiCad clearance 0.15 (+0.01) to other-net copper
# on every layer, the hole clearance 0.25 (+0.01), 0.5 mm (+0.02) hole to hole and the keep-outs; it overlaps only its own pad
# and its own net. Pads of 0.5 mm pitch (LSHM-150, TPS25947 RPW) take no such via (it would reach the neighbour pads).
VIP_SIZES = ((0.6, 0.3),)
VIP_CLR = 0.16       # mm: KiCad clearance 0.15 + 0.01
VIP_HOLE_CLR = 0.26  # mm: PWR_A.kicad_pro min_hole_clearance 0.25 + 0.01
VIP_MAX_PAD = 3.0    # mm: no via in pads larger than this on both sides (exposed pads; power pads keep their own vias)


def vip_margin(m, net, at, size, drill, ignore=()):
    """Smallest margin (>= 0 is clear) of a via in a pad of `net`: other-net copper (VIP_CLR, hole VIP_HOLE_CLR), hole to hole,
    keep-outs, edges; same-net copper (its own pad) is allowed; items in `ignore` (the via itself) are skipped."""
    r = size / 2
    bb = (at[0] - r - 1.5, at[1] - r - 1.5, at[0] + r + 1.5, at[1] + r + 1.5)
    worst, why, seen = math.inf, None, set(ignore)
    for lay in M.LAYERS:
        for it in m.near(lay, bb):
            if it.id in seen:
                continue
            seen.add(it.id)
            if it.kind in ('via', 'npth') or (it.kind == 'pad' and it.drill):
                d = math.hypot(at[0] - it.at[0], at[1] - it.at[1]) - drill / 2 - (it.drill or 0) / 2 - M.HOLE_HOLE - 0.02
                if d < worst:
                    worst, why = d, f'hole {it.kind} {it.ref or ""}.{it.pad or ""}'
            if it.kind == 'npth' or it.net == net:
                continue
            dist = it.shape.dist(*at)
            for mg in (dist - r - VIP_CLR, dist - drill / 2 - VIP_HOLE_CLR):
                if mg < worst:
                    worst, why = mg, f'{it.kind} {it.net} {it.ref or ""}.{it.pad or ""}'
    for k in m.keepouts:
        kb = k['poly'].bbox
        if kb[0] > bb[2] or kb[2] < bb[0] or kb[1] > bb[3] or kb[3] < bb[1]:
            continue
        mg = k['poly'].dist(*at) - r - 0.01
        if mg < worst:
            worst, why = mg, 'keepout ' + k['name']
    mg = min(M.seg_dist(at[0], at[1], e0[0], e0[1], e1[0], e1[1]) for e0, e1 in m.edges) - r - M.EDGE_CLR - 0.02
    if mg < worst:
        worst, why = mg, 'edge'
    if not m.inside(at):
        return -9.0, 'outside'
    return worst, why


def vip_spots(pad, size):
    """Via centres in a pad: its centre, then along its long axis in 0.05 mm steps while the via centre stays a quarter of the via
    inside the pad ends (KiCad mm)."""
    x0, y0, x1, y1 = pad.shape.bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    horiz = (x1 - x0) >= (y1 - y0)
    half = ((x1 - x0) if horiz else (y1 - y0)) / 2 - size / 4
    out = [(round(cx, 4), round(cy, 4))]
    k = 1
    while k * 0.05 <= half + 1e-9:
        for sgn in (1, -1):
            d = sgn * k * 0.05
            out.append((round(cx + d, 4), round(cy, 4)) if horiz else (round(cx, 4), round(cy + d, 4)))
        k += 1
    return [q for q in out if pad.shape.dist(*q) <= 0.0]


def add_pad_vias(m, net, sizes=VIP_SIZES, refs=None):
    """A via in each SMD pad of `net` (outer layer, at most VIP_MAX_PAD on its short side, no via in it yet; refs limits the parts)
    that has a free spot, src 'vip'. Returns the added via items."""
    added = []
    groups = [gr for gr in m.islands(net) if any(i.kind == 'pad' for i in gr)]
    if len(groups) <= 1:
        return added
    for gr in groups:
        for p in gr:
            if p.kind != 'pad' or p.src != 'pad' or p.drill or not any(l in OUTER for l in p.layers):
                continue
            if refs is not None and p.ref not in refs:
                continue
            bx = p.shape.bbox
            if min(bx[2] - bx[0], bx[3] - bx[1]) > VIP_MAX_PAD:
                continue
            if any(o.kind == 'via' and o.net == net and p.shape.dist(*o.at) <= 0 for o in m.near(p.layers[0], bx)):
                continue
            done = False
            for size, drill in sizes:
                for at in vip_spots(p, size):
                    if vip_margin(m, net, at, size, drill)[0] >= 0:
                        added.append(m.add_via(net, at, size, drill, src='vip'))
                        done = True
                        break
                if done:
                    break
    return added


def vip_used(m, v):
    """A via in a pad is used when a track of its net ends in it on a layer other than its pad's."""
    for lay in M.LAYERS:
        if any(o.kind == 'pad' and o.src == 'pad' and o.net == v.net and o.shape.dist(*v.at) <= 0
               for o in m.near(lay, (v.at[0] - 0.5, v.at[1] - 0.5, v.at[0] + 0.5, v.at[1] + 0.5))):
            continue
        for o in m.near(lay, (v.at[0] - 1, v.at[1] - 1, v.at[0] + 1, v.at[1] + 1)):
            if o.kind == 'track' and o.net == v.net and any(v.shape.dist(*e) <= 1e-4 for e in (o.a, o.b)):
                return True
            if o.kind == 'pad' and o.src == 'zone' and o.net == v.net and o.shape.dist(*v.at) <= 1e-4:
                return True
    return False


def drop_unused_vips(m, net):
    """Remove the vias in pads of `net` that no track uses. Returns the number removed."""
    n = 0
    for it in m.items:
        if it.alive and it.kind == 'via' and it.src == 'vip' and it.net == net and not vip_used(m, it):
            m.remove(it)
            n += 1
    return n


# W2 PWR-A closure round 1, probe Y (--deep-entry): a completion track ends inside a small SMD pad at least half its width from
# the pad edge (route run 45062920789: the A* entered the DVDT pins of U201 / U202 over a pad corner, two KiCad
# connection_width errors). Pads up to DEEP_MAX on their short side; a pad too small for that keeps its whole area.
DEEP_MAX = 1.0
_COVERED = R.Grid.covered
DEEP = {'width': None}


def covered_deep(self, items, layer):
    w = DEEP['width']
    if not w:
        return _COVERED(self, items, layer)
    w = R.wof(w, layer)
    small = [it for it in items if it.kind == 'pad' and it.src == 'pad' and layer in it.layers
             and min(it.bbox[2] - it.bbox[0], it.bbox[3] - it.bbox[1]) <= DEEP_MAX]
    ids = {it.id for it in small}
    cov = _COVERED(self, [it for it in items if it.id not in ids], layer)
    d = w / 2
    for it in small:
        win = self.win(it.bbox, 0.0)
        if win is None:
            continue
        X, Y = self.X[win], self.Y[win]
        full = R.shape_dist(X, Y, it.shape) <= 0.0
        deep = full.copy()
        for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d), (d * 0.7071, d * 0.7071), (-d * 0.7071, d * 0.7071),
                       (d * 0.7071, -d * 0.7071), (-d * 0.7071, -d * 0.7071)):
            deep &= R.shape_dist(X + dx, Y + dy, it.shape) <= 0.0
        cov[win] |= deep if deep.any() else full
    return cov


_ROUTE_LINK = R.route_link


def route_link_deep(m, net, isl_a, isl_b, box, width=0.15, **kw):
    """R.route_link with the deep pad entry of the track width of this link (DEEP)."""
    DEEP['width'] = width
    try:
        return _ROUTE_LINK(m, net, isl_a, isl_b, box, width=width, **kw)
    finally:
        DEEP['width'] = None


# W2 PWR-TOOLS: why a net may be left open (--leave-open) in a harvest
LEAVE_OPEN_WHY = {
    'E2_BONI_EF': ('the grid A* joins it only through a B.Cu end inside the copper of a diagonal E2_BONI_EF track, which KiCad '
                   '10.0.7 reported as track_dangling (route run 43375868329; the same piece was the track_dangling error of '
                   'route run 43354942122), while the net stayed open in KiCad; left open for the scripted power copper of '
                   'PWR-L6-SCRIPT'),
}


def centre_joints(m):
    """A router/completion track end inside a same-net SMD pad less than half its width from the pad edge gets a track of its width
    to the pad centre where that clears (KiCad 10.0.7 connection_width: a track that enters a pad over its corner, route runs
    45062920789 and 45109912253); the port of route6.py centre_joints. Returns [(net, pad)]."""
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


def rebase(m, art, prev):
    """W2 PWR-A closure round 1, probe Y (--rebase): every track and via of the run's board and the fills of the scripted pours of
    its board-spec.json go; the locked tracks and vias of the current board-spec.json (make_board.py without route-frozen-6l.json:
    scripted, GND fan-out, signal escapes, planned copper) come in as scripted copper, and the frozen copper of --prev (router and
    completion tracks and vias, its vias in pads as such) as router copper, so a harvest that was never routed in CI can be carried
    too. The pads must be those of the run (same placement); spec_zones() then models the current pours. Returns counts."""
    now = json.loads((HERE.parent / 'board-spec.json').read_text(encoding='utf-8'))
    old = json.loads((art / 'board/board-spec.json').read_text(encoding='utf-8'))
    pre = now['pre_route']
    if any(t['id'].startswith(('RT-', 'FIN-')) for t in pre['tracks']) or any(v['id'].startswith(('RV-', 'FINV-')) for v in pre['vias']):
        raise SystemExit('freeze6 --rebase: board-spec.json holds frozen copper; write it with make_board.py without route-frozen-6l.json')
    pads_now = sorted((p['ref'], tuple(p['anchor']['at']), p['anchor'].get('rotation'), p['anchor'].get('side'))
                      for p in now['parts'] if isinstance(p.get('anchor'), dict))
    pads_old = sorted((p['ref'], tuple(p['anchor']['at']), p['anchor'].get('rotation'), p['anchor'].get('side'))
                      for p in old['parts'] if isinstance(p.get('anchor'), dict))
    if pads_now != pads_old:
        raise SystemExit('freeze6 --rebase: the placement differs from the run; route again')
    n_old = 0
    for it in m.items:
        if it.alive and it.kind in ('track', 'via'):
            m.remove(it)
            n_old += 1
    fills = {z['id'] for z in old['pre_route']['zones'] if 'clearance_mm' in z} | {z['id'] for z in pre['zones'] if 'clearance_mm' in z}
    n_fill = 0
    for it in m.items:
        if it.alive and it.src == 'zone' and it.pad in fills:
            m.remove(it)
            n_fill += 1
    n_new = 0
    for t in pre['tracks']:
        for a, b in zip(t['path'], t['path'][1:]):
            m.add_track(t['net'], t['layer'], t['width_mm'], K(*a), K(*b), locked=True, src='scripted')
            n_new += 1
    for v in pre['vias']:
        m.add_via(v['net'], K(*v['at']), v['diameter_mm'], v['drill_mm'], locked=True, src='scripted')
        n_new += 1
    n_prev = 0
    pvip = {(r['net'], K(*r['at'])) for r in prev.get('via_in_pad', [])}
    for key in ('router_tracks', 'completion_tracks'):
        for net, lay, w, path in prev[key]:
            for a, b in zip(path, path[1:]):
                m.add_track(net, lay, w, K(*a), K(*b), locked=False, src='router')
                n_prev += 1
    for key in ('router_vias', 'completion_vias'):
        for net, x, y, d, drill in prev[key]:
            m.add_via(net, K(x, y), d, drill, locked=False, src='vip' if (net, K(x, y)) in pvip else 'router')
            n_prev += 1
    return {'run_items_removed': n_old, 'old_pour_fills_removed': n_fill, 'scripted_items_added': n_new, 'frozen_items_added': n_prev}


def spec_zones(m):
    """W2 PWR-L6-ROUTE (--spec-zones): replace the zone items (src 'zone', the fills of the routed board) of every scripted pour
    that board-spec.json pre_route gives a clearance_mm by its outline polygon (KiCad mm), the copper plan6.py and make_board.py
    checked and that KiCad fills at that clearance. Returns (zones replaced, fill items removed)."""
    spec = json.loads((HERE.parent / 'board-spec.json').read_text(encoding='utf-8'))
    zones = [z for z in spec['pre_route']['zones'] if 'clearance_mm' in z and z['outline'] != 'board' and z['net'] not in M.PLANES]
    names = {z['id'] for z in zones}
    gone = 0
    for it in m.items:
        if it.alive and it.src == 'zone' and it.pad in names:
            m.remove(it)
            gone += 1
    for z in zones:
        pts = [K(x, y) for x, y in z['outline']]
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        m.add(M.Item(kind='pad', net=z['net'], layers=[z['layer']], shape=M.cb.Poly(pts), ref='ZONE', pad=z['id'],
                     at=((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2), drill=0.0, locked=True, src='zone'))
    return len(zones), gone


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


TP_TARGET_GAP = 1.0  # mm: a long test-point branch ends at least this far off a connector land (tp_target)


def tp_target(m, w):
    """Target of the long test-point branch (--tp-max; W2 PWR-A closure round 2, combine pass): class-width copper of the net that
    is not on a connector land. pcb/check_boards.py walks a branch from its test point to the first class-width copper; a branch that
    reaches a pad of a role the exemption policy forbids (a connector land: J205.2 in the MODEL route of the combine pass, where the
    branch ended on the end of the planned DISP12 track over that pad) is a class_widths finding. So a pin-entry pour (PE-, it sits on
    its pad) and a track with an end on a connector pad (ref J...) of its net are no target."""
    def on_connector(t):  # any point of the track within its half width + TP_TARGET_GAP of a connector land of its net
        n = max(1, int(math.dist(t.a, t.b) / 0.1))
        pts = [(t.a[0] + (t.b[0] - t.a[0]) * k / n, t.a[1] + (t.b[1] - t.a[1]) * k / n) for k in range(n + 1)]
        r = t.width / 2 + TP_TARGET_GAP
        box = (min(t.a[0], t.b[0]) - r, min(t.a[1], t.b[1]) - r, max(t.a[0], t.b[0]) + r, max(t.a[1], t.b[1]) + r)
        for p in m.near(t.layers[0], box):
            if (p.alive and p.kind == 'pad' and p.src == 'pad' and p.net == t.net and str(p.ref).startswith('J')
                    and any(p.shape.dist(*q) <= r for q in pts)):
                return True
        return False
    return lambda i: ((i.kind == 'track' and i.width + 1e-6 >= w and not on_connector(i))
                      or (i.kind == 'pad' and i.src == 'zone' and not str(i.pad).startswith('PE-')))


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
    ap.add_argument('--rip-wide', action='store_true',
                    help='W2 PWR-L6-ROUTE: a rip-up search in the 25 mm box when the 8 mm box has none (fin.connect_all rip_wide)')
    ap.add_argument('--rip-new', action='store_true',
                    help='W2 PWR-L6-ROUTE: the rip-up may also move completion copper of other nets (queued again)')
    ap.add_argument('--spec-zones', action='store_true',
                    help='W2 PWR-L6-ROUTE: model the scripted pours with clearance_mm by their spec outlines (spec_zones)')
    ap.add_argument('--leave-open', action='append', default=[], metavar='NET',
                    help='W2 PWR-TOOLS: a net the grid A* does not complete in this harvest (its DRC drops and pruning still '
                         'apply); recorded under fixes.left_open with LEAVE_OPEN_WHY')
    ap.add_argument('--pad-vias', action='store_true',
                    help='W2 PWR-A closure round 1, probe Y: a net left open tries again with a via in the SMD pads of its pins '
                         '(add_pad_vias); unused ones are removed')
    ap.add_argument('--deep-entry', action='store_true',
                    help='W2 PWR-A closure round 1, probe Y: completion tracks end at least half their width inside small pads '
                         '(covered_deep)')
    ap.add_argument('--sense-branches', action='store_true',
                    help='W2 PWR-A closure round 1, probe Y: sense/logic pins of ICs on a power net (pcb/check_boards.py role '
                         'sense_logic_pin) take a 0.25 mm branch on the four routing layers, as test points do')
    ap.add_argument('--tp-max', type=float, default=0.0,
                    help='W2 PWR-A closure round 1, combine pass: longest test-point branch in mm (route6.py --tp-max; a test point '
                         'carries no load current; 0: none beyond BRANCH_MAX)')
    ap.add_argument('--tp-outer', action='store_true',
                    help='W2 PWR-A closure round 2, combine pass: the long test-point branch of --tp-max on F.Cu/B.Cu only (0.25 mm on 2 oz '
                         'outer copper: 1.96 A at +20 degC by IPC-2221, MODEL, above the eFuse current limit of the rail; the same 0.25 mm '
                         'on the 0.5 oz inner layers carries 0.32 A)')
    ap.add_argument('--centre-joints', action='store_true',
                    help='W2 PWR-A closure round 1, combine pass: a router/completion track end inside a same-net SMD pad less than half its '
                         'width from the pad edge gets a track to the pad centre (route6.py centre_joints; KiCad connection_width at '
                         'D202.1 in route run 45109912253)')
    ap.add_argument('--rebase', action='store_true',
                    help='W2 PWR-A closure round 1, probe Y: carry the frozen copper of --prev onto changed scripted / planned '
                         'copper (rebase(): the scripted copper of the run is replaced by that of the current board-spec.json, '
                         'written by make_board.py without route-frozen-6l.json), and complete every net open in the model')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    if args.rebase and not args.prev:
        raise SystemExit('freeze6: --rebase needs --prev (the frozen copper to carry over)')
    if args.deep_entry:
        R.Grid.covered = covered_deep
        R.route_link = route_link_deep
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
        pvip = {(r['net'], K(*r['at'])) for r in prev.get('via_in_pad', [])}
        hit = 0
        for it in m.items:
            if not it.alive or it.src != 'scripted':
                continue
            if it.kind == 'track' and (it.net, it.layers[0], round(it.width, 4), (round(it.a[0], 4), round(it.a[1], 4)),
                                       (round(it.b[0], 4), round(it.b[1], 4))) in segs:
                it.src, hit = 'router', hit + 1
            elif it.kind == 'via' and (it.net, (round(it.at[0], 4), round(it.at[1], 4))) in pvias:
                it.src, hit = ('vip' if (it.net, (round(it.at[0], 4), round(it.at[1], 4))) in pvip else 'router'), hit + 1
        print(f'ratchet: {hit} locked items of {args.prev} harvested again')
    rebased = rebase(m, art, prev) if args.rebase else None
    if rebased:
        print('rebase:', rebased)
    stubs_hit, stubs_all = fix_stubs(m, art)
    print(f'via-centre stubs of the route log held fixed: {stubs_hit} of {stubs_all}')
    zones_modelled = spec_zones(m) if args.spec_zones else None
    if zones_modelled:
        print(f'scripted pours modelled by their spec outlines: {zones_modelled[0]} (fill items removed {zones_modelled[1]})')
    cls, default_w = classes()
    width = lambda n: cls.get(n, ('Default', default_w))[1]
    layers = lambda n: OUTER if cls.get(n, ('Default',))[0] in POWER else ROUTING
    NEVER.update(n for n, (c, _w) in cls.items() if c.startswith('SCRIPTED_'))  # W2 PWR-L6-SCRIPT: scripted nets, never routed
    branch_ok, neck_ok = policy(m)
    czones = converter_zone_rule(m)
    base_keepouts = list(m.keepouts)

    def zone_keepouts(net):
        return [{'layers': list(CZ_LAYERS), 'poly': poly, 'name': 'converter zone'} for poly, own in czones if net not in own]
    drc = json.loads((art / 'board/drc.json').read_text(encoding='utf-8'))
    drops = drc_drops(m, drc)
    print('router copper named in a KiCad DRC error:', drops)
    kicad_open = collections.Counter(n for u in drc.get('unconnected_items', []) for n in
                                     {re.search(r'\[([^\]]+)\]', i.get('description', '')).group(1)
                                      for i in u.get('items', []) if re.search(r'\[([^\]]+)\]', i.get('description', ''))})
    if args.rebase:  # the DRC of the run measured the old scripted copper: every net open in the model is open now
        for n in [n for n in kicad_open if n not in NEVER]:
            del kicad_open[n]
        for n, k in fz.unconnected().items():
            if n not in NEVER:
                kicad_open[n] = k
        gone = [it for it in m.items if it.alive and it.src == 'router' and it.net in NEVER]
        for it in gone:  # a net the new plan joins whole (scripted class) keeps only its planned copper
            m.remove(it)
        print('rebase: router items of scripted nets removed', len(gone), sorted({it.net for it in gone}))
    bad_never = sorted(set(kicad_open) & NEVER)
    if bad_never and (not args.spec_zones or 'GND' in bad_never):
        raise SystemExit(f'freeze6: KiCad reports open connections of {bad_never}: fix the GND fan-out and route again')
    scripted_split = {}
    if bad_never:  # W2 PWR-L6-ROUTE (--spec-zones): scripted nets the run left open; their copper is the spec's, never routed here
        print('KiCad open connections of scripted nets (left to the scripted copper):', bad_never)
        # with the pours at their outlines the scripted copper must join each such net in the model; a net it still leaves
        # split stays open in the next run as well (recorded, never routed here)
        scripted_split = {n: len(m.islands(n)) - 1 for n in bad_never if len(m.islands(n)) > 1}
        print('scripted nets still split in the model with the spec outlines:', scripted_split)
    for n in bad_never:
        del kicad_open[n]
    model_only = {n: k for n, k in fz.unconnected().items() if n not in NEVER and n not in kicad_open}
    print('KiCad open connections:', dict(kicad_open))
    print('model-only islands (joined in KiCad by copper overlap, left as routed):', model_only)
    viol = set()
    for it in m.items:  # probe Y: a via in pad of the previous harvest keeps its own check (vip_margin)
        if it.alive and it.src == 'vip' and vip_margin(m, it.net, it.at, it.size, it.drill, ignore={it.id})[0] < 0:
            print(f'  via in pad of {it.net} breaks a clearance: removed')
            m.remove(it)
            viol.add(it.net)
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
    escapes = pad_escapes(m, drc, width)
    for e in escapes:
        print(f'  {e["net"]}: {e["pad"]} escape stub {e["width"]} mm to {e["to"]} (connection_width in the run)')
        viol.add(e['net'])
    for poly, own in czones:  # W2 PWR-L6-SCRIPT zone rule: no foreign router copper on F.Cu / In1.Cu over a converter zone
        for it in m.items:
            if not (it.alive and it.src == 'router') or it.net in own or it.net in NEVER:
                continue
            on = [l for l in it.layers if l in CZ_LAYERS]
            if on and (M.shape_seg_dist(poly, it.a, it.b) <= it.width / 2 if it.kind == 'track' else poly.dist(*it.at) <= it.size / 2):
                print(f'  router {it.kind} of {it.net} on {on} over a converter zone: removed')
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
    left_open = {n: LEAVE_OPEN_WHY.get(n, 'left open on the command line (--leave-open)') for n in sorted(set(args.leave_open))}
    first = [n for n in first if n not in left_open and n not in NEVER]
    queue, rounds, t0 = collections.deque(first), 0, time.time()
    touched, failed, necks, branches = set(first), [], [], []
    while queue and rounds < args.rounds:
        net = queue.popleft()
        rounds += 1
        if net in NEVER:
            raise SystemExit(f'freeze6: {net} is a plane or scripted net; it is never routed here')
        # W2 PWRJ-LAYERS6: pair by pair (a walled-in pair is skipped, the rest of the net is joined); a power pair without
        # a class-width path may take a short pad-to-pad neck (fin.neck_link, NECK_MAX mm), listed in the spec neck_exempt
        m.keepouts[:] = base_keepouts + zone_keepouts(net)
        ok, ripped, nk = fz.connect_all(net, width=width(net), layers=layers(net), allow_rip=not args.no_rip,
                                        neck=(width(net), NECK_MAX, neck_ok) if layers(net) == OUTER else None,
                                        rip_wide=args.rip_wide, soft=('router', 'new') if args.rip_new else ('router',))
        necks += nk
        vips = []
        if not ok and args.pad_vias and layers(net) != OUTER:  # probe Y: a via in the pads of the walled-in pins, then again
            vips = add_pad_vias(m, net)
            if vips:
                ok, ripped2, nk = fz.connect_all(net, width=width(net), layers=layers(net), allow_rip=not args.no_rip, neck=None,
                                                 rip_wide=args.rip_wide, soft=('router', 'new') if args.rip_new else ('router',))
                ripped += [n for n in ripped2 if n not in ripped]
                necks += nk
        if not ok and layers(net) == OUTER:  # low-current branches of a power net (exemption policy: TP, R >= 100 ohm, sense pins)
            bk = branch_kind(GRAPH, sense=args.sense_branches)
            for attempt in ((False, True) if args.pad_vias else (False,)):
                if attempt:  # probe Y: the branch parts get vias in their pads (branches on the routing layers only)
                    vips += add_pad_vias(m, net, refs={i.ref for gr in m.islands(net) for i in gr if i.kind == 'pad'
                                                       and bk(i.ref) in ('TP', 'S') and branch_ok(i.ref, net)})
                okb, br = fz.branch_pass(net, lambda r: bk(r) is not None and branch_ok(r, net),
                                         lambda refs: max(BRANCH_W[bk(r)] for r in refs),
                                         lambda refs: ROUTING if all(bk(r) in ('TP', 'S') for r in refs) else OUTER, BRANCH_MAX,
                                         target_ok=lambda i: (i.kind == 'track' and i.width + 1e-6 >= width(net))
                                         or (i.kind == 'pad' and i.src == 'zone'))
                branches += br
                ok = ok or okb
                if ok:
                    break
            if not ok and args.tp_max:  # combine pass: a test-point island joins by a longer 0.25 mm branch (route6.py --tp-max)
                okt, brt = fz.branch_pass(net, lambda r: r is not None and r.startswith('TP') and branch_ok(r, net),
                                          lambda refs: BRANCH_W['TP'], lambda refs: OUTER if args.tp_outer else ROUTING, args.tp_max,
                                          target_ok=tp_target(m, width(net)))
                branches += brt
                ok = ok or okt
        if vips:
            n_drop = drop_unused_vips(m, net)
            print(f'  {net}: vias in pads added {len(vips)}, unused removed {n_drop}')
        m.keepouts[:] = base_keepouts
        print(f'{net}: {"OK" if ok else "FAILED"} ripped {ripped} ({time.time() - t0:.0f} s)', flush=True)
        if not ok:
            failed.append(net)
        queue.extend(n for n in ripped if n not in queue and n not in left_open)
        touched |= set(ripped)
    for n in sorted({i.net for i in m.items if i.alive and i.net and i.net not in M.PLANES}):
        F.prune(m, n, srcs=('router', 'new', 'escape'))  # an escape stub whose link failed goes too
        drop_unused_vips(m, n)
    merged = merge_remainders(m)
    print('split remainders merged back:', len(merged))
    joints = centre_joints(m) if args.centre_joints else []
    if joints:
        print('centre joints added (track end shallow inside a pad):', joints)
    open_, bad = verify(m)
    dropped = (0, [])
    if bad:
        dropped = drop_failing_completion(m)
        print('dropped completion items after the final check:', dropped)
        open_, bad = verify(m)
    open_ = {n: k for n, k in open_.items() if n in touched or n in left_open}
    bad = [b for b in bad if not (b[0] == 'dangling' and (b[2] in NEVER or b[2] in model_only))]
    # W2 PWR-A closure round 1, probe Y: a locked via of a routed net (a signal escape of make_board.py signal_fanout) that its
    # net's copper joins on one layer only is a KiCad via_dangling error in the run (reported here, not changed: scripted copper)
    lone = []
    for it in m.items:
        if not (it.alive and it.kind == 'via' and it.src == 'scripted') or it.net in NEVER or it.net in M.PLANES:
            continue
        lays = set()
        for lay in M.LAYERS:
            for ot in m.near(lay, (it.at[0] - 1, it.at[1] - 1, it.at[0] + 1, it.at[1] + 1)):
                if ot.id != it.id and ot.net == it.net and ((ot.kind == 'track' and (any(it.shape.dist(*e) <= 1e-4 for e in (ot.a, ot.b))
                                                                                         or ot.shape.dist(*it.at) <= 1e-4))
                                                            or (ot.kind == 'pad' and ot.shape.dist(*it.at) <= 1e-4)
                                                            or (ot.kind == 'via' and math.dist(ot.at, it.at) <= 1e-4)):
                    lays.add(lay)
        if len(lays) < 2:
            lone.append({'net': it.net, 'at': B(it.at)})
    print('open connections', open_, 'clearance violations', len(bad), 'failed', sorted(set(failed)), 'scripted vias on one layer', lone)
    for b_ in bad[:12]:
        print('   ', b_)
    groups = collections.defaultdict(list)
    vias = {'router': [], 'new': []}
    for it in m.items:
        if it.alive and it.src in ('router', 'new', 'escape', 'vip'):
            src = 'new' if it.src in ('escape', 'vip') else it.src
            if it.kind == 'track':
                groups[(src, it.net, it.layers[0], round(it.width, 4))].append((it.a, it.b))
            elif it.kind == 'via':
                vias[src].append([it.net] + B(it.at) + [round(it.size, 4), round(it.drill, 4)])
    vip_rec = []
    for it in m.items:
        if it.alive and it.kind == 'via' and it.src == 'vip':
            pad = next((o for lay in ('F.Cu', 'B.Cu') for o in m.near(lay, it.bbox) if o.kind == 'pad' and o.src == 'pad'
                        and o.net == it.net and o.shape.dist(*it.at) <= 0), None)
            vip_rec.append({'net': it.net, 'at': B(it.at), 'diameter_mm': round(it.size, 4), 'drill_mm': round(it.drill, 4),
                            'pad': f'{pad.ref}.{pad.pad}' if pad else None,
                            'margin_mm': round(vip_margin(m, it.net, it.at, it.size, it.drill, ignore={it.id})[0], 4)})
    vip_rec.sort(key=lambda r: (r['pad'] or '', r['net']))
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
        'result': {'open': open_, 'violations': len(bad), 'failed_nets': sorted(set(failed)),
                   **({'scripted_vias_one_layer': lone} if lone else {}),
                   **({'scripted_open_in_run': bad_never, 'scripted_split_in_model': scripted_split} if bad_never else {})},
        'fixes': {'via_centre_stubs_fixed': stubs_hit, 'drc_drops': drops, 'merged_split_remainders': len(merged), 'pad_escapes': escapes,
                  **({'spec_zones': {'modelled': zones_modelled[0], 'fill_items_removed': zones_modelled[1]}} if zones_modelled else {}),
                  'final_check_dropped': {'items': dropped[0], 'nets': dropped[1]}, 'left_open': left_open},
        'necks': sorted(necks, key=lambda r: (r['ref'], r['pad'], r['to'])),
        'branches': sorted(branches, key=lambda r: (r['net'], r['refs'])),
        'guard': None if args.no_guard else guard(),
        'segments': dict(nseg),
        'router_tracks': tracks['router'], 'router_vias': vias['router'],
        'completion_tracks': tracks['new'], 'completion_vias': vias['new'],
        **({'via_in_pad': vip_rec} if vip_rec else {}),
        **({'rebase': rebased} if rebased else {}),
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
