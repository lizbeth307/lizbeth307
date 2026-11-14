#!/usr/bin/env python3
"""LAB5 E1 -> E2 copper resistance against E1-05 (W2 PCB-PWRA-2, CC-36 item 12; LSHM B2B W2 PCB-PWRA-3): a MODEL,
standard library only.

  python3 build/kicad/boards/PWR_A/lab5_budget.py           write lab5-budget.json next to this file
  python3 build/kicad/boards/PWR_A/lab5_budget.py --check   fail unless lab5-budget.json reproduces

E1-05 (design/E1.json open_items) budgets the LAB5 connection E1 -> E2 at <= 10 mOhm ("every 10 mOhm is 32 mV at
3.2 A"): the copper between the E1 LAB5 chain (U108 D36V50F5 -> F102 -> L101) and the E2 inputs, apart from the F102
cold resistance (its own <= 10 mOhm item) and the L101 DCR (R-E1-05). Two E2 destinations exist:
  A  the LT3045 pair U204/U205 on PWR-A (through L205; the headroom item of E1-05), no B2B in the path;
  B  the E2 switches U210/U221 on PWR-B (and the E5 switches U501/U502 beside them), through the B2B.
What is measured and what is modelled:
  - PWR-B copper: the CI-routed board build/kicad/boards/PWR_B/PWR_B.kicad_pcb (pcb/check_boards.py reader); every LAB5
    track and via becomes a resistor network (tracks rho*L/(w*t), via barrels rho*h/(pi*(r^2-(r-p)^2))), pads and
    overlapping copper are ideal joints; resistance from the shorted LAB5 contacts of the B2B mate (J209 since W2 B2B)
    to each LAB5 load pad.
  - B2B: Samtec LSHM-150 contact resistance (W2 B2B, J208/J209). The product specification states only the change
    after the tests (LLCR delta <= 15 mOhm per contact); the initial value is not stated there, so it stays TBD.
  - PWR-A copper: no routed PWR-A exists. From the anchors of the SHRINK-2 planner spec PWR_A.spec-shrink2.json
    (make_spec.py: L101.2 for the E1 end since W2 PCB-PWRA-3 part 2 anchors the LAB5 filter, else F102.2; U204/U205 IN
    pads; the J208 LAB5 contacts) the straight and the orthogonal path lengths give the resistance of the narrowest
    legal copper (PWR3A 1.85 mm, one outer layer) and the copper width x outer layers that the remaining budget needs.
    L205 is not anchored: the U204/U205 IN pads stand for the E2 end.
  - E1_LAB5_RAW (LAB5 converter output -> F102.1) and E1_LAB5_FUSED (F102.2 -> L101.1), upstream of the E1-05 figure:
    from the scripted pours of the spec when the converter is anchored (an upper bound: the whole orthogonal path at the
    narrowest pour width, F.Cu only); TBD while the SHRINK-2 converter is a reserved block (GR-5A pending).
Copper: annealed copper (IACS) at 20 C and at 50 C (the E1-05 thermal test ambient; the copper itself runs warmer).
W2 PWR-L6-SCRIPT: both power boards are 6 layers with 2 oz outer / 0.5 oz inner copper (pcb/boards/PWR_B.json layers.copper_option
outer_2oz, pcb/generated/stackup-6l.json): the PWR-B network takes 0.070 mm on F.Cu/B.Cu and 0.0152 mm on the inner layers, the
PWR-A planner paths the 2 oz PWR3A width. Path B is restated per destination (synthesis e105_decision, on E1-05's own basis
"10 mOhm = 32 mV at 3.2 A"): the drop from L101.2 to each TPS2553 input on PWR-B at the worst-case concurrent currents, the
TPS2553 limits of tools/assembly_data.py NET_CURRENT (protective column) for the output net of each switch, segment by segment
(multi-sink network solve). This file gives the PWR-B part and the B2B part; board_audit.py adds the PWR-A copper of the board.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3]  # sat-receiver-audit
sys.path.insert(0, str(BASE / 'pcb'))
import board_gen as bg  # noqa: E402
import check_boards as cb  # noqa: E402

OUT = HERE / 'lab5-budget.json'
SPEC = HERE / 'PWR_A.spec-shrink2.json'
PWR_B_BOARD = BASE / 'build/kicad/boards/PWR_B/PWR_B.kicad_pcb'
PWR_B_SPEC = BASE / 'pcb/boards/PWR_B.json'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
E1 = BASE / 'design/E1.json'

SIGMA_IACS = 58.0e6        # S/m at 20 C: International Annealed Copper Standard
SIGMA_SRC = ('https://en.wikipedia.org/wiki/International_Annealed_Copper_Standard read 2026-11-07: "equivalent to a '
             'conductivity of exactly 58x10^6 S/m at 20 C"')
ALPHA = 3.93e-3            # 1/K, annealed copper at 20 C
ALPHA_SRC = ('https://en.wikipedia.org/wiki/Electrical_resistivity_and_conductivity read 2026-11-07, table row '
             '"Annealed copper 1.72x10^-8 58.0x10^6 3.93x10^-3"')
T_HOT = 50.0               # C, E1-05 thermal test ambient (design/E1.json E1-05 resolve text)
B2B_DELTA = 0.015          # Ohm per contact, Samtec LLCR delta maximum
B2B_SRC = ('Samtec LSHM product specification Revision H (dated September 9, 2026) section 3.4, '
           'https://suddendocs.samtec.com/productspecs/lshm.pdf read 2026-11-12 (sha256 935cb14c85a2635b69b4f00bfd1568d3b8933'
           'c51386286aeaaa9b167188eef2d, the copy W2 B2B read): "Contact Resistance (LLCR) EIA-364-23 delta 15 mOhm maximum '
           '(Samtec defined)"; section 3.1 current rating 2 A (one pin powered per row); no initial value stated')
BUDGET = 0.010             # Ohm, E1-05
DROP_BUDGET_MV = 32.0      # mV: E1-05 "every 10 mOhm is 32 mV at 3.2 A" (design/E1.json), the per-destination restatement
STACKUP_6L = BASE / 'pcb/generated/stackup-6l.json'
ASSEMBLY = BASE / 'tools/assembly_data.py'
SWITCH = 'TPS2553'         # the current-limited switches at the path-B destinations
NET = 'LAB5'
PWR_A_ENDS = {'E1': [('F102', '2')], 'E2_LT3045': [('U204', p) for p in '1234'] + [('U205', p) for p in '1234']}
JOIN = 1e-3                # mm, node merge


def rho(temp_c):
    return (1.0 / SIGMA_IACS) * 1e3 * (1.0 + ALPHA * (temp_c - 20.0))  # Ohm*mm (Ohm*m * 1e3)


def r4(v):
    return bg.r4(v)


def r6(v):
    return round(float(v), 6)


class Net:
    """Resistor network with union-find joints; solve() gives two-terminal resistances."""

    def __init__(self):
        self.parent, self.edges = {}, []

    def node(self, key):
        self.parent.setdefault(key, key)
        return key

    def find(self, k):
        while self.parent[k] != k:
            self.parent[k] = self.parent[self.parent[k]]
            k = self.parent[k]
        return k

    def join(self, a, b):
        ra, rb = self.find(self.node(a)), self.find(self.node(b))
        if ra != rb:
            self.parent[max(ra, rb, key=repr)] = min(ra, rb, key=repr)

    def res(self, a, b, ohm):
        self.node(a), self.node(b)
        self.edges.append((a, b, ohm))

    def resistance(self, sources, sink):
        roots = sorted({self.find(k) for k in self.parent}, key=repr)
        src = {self.find(s) for s in sources}
        snk = self.find(sink)
        if snk in src:
            return 0.0
        index = {}
        for r in roots:
            if r in src:
                index[r] = 0
        for r in roots:
            if r not in index and r != snk:
                index[r] = len(set(index.values()))
        n = len(set(index.values()))
        g = [[0.0] * n for _ in range(n)]
        for a, b, ohm in self.edges:
            ra, rb = self.find(a), self.find(b)
            if ra == rb:
                continue
            c = 1.0 / ohm
            ia, ib = index.get(ra), index.get(rb)  # None = sink (ground)
            if ia is not None:
                g[ia][ia] += c
            if ib is not None:
                g[ib][ib] += c
            if ia is not None and ib is not None and ia != ib:
                g[ia][ib] -= c
                g[ib][ia] -= c
        rhs = [0.0] * n
        rhs[0] = 1.0  # 1 A into the shorted sources
        # Gaussian elimination with partial pivoting (dense, small n)
        for col in range(n):
            piv = max(range(col, n), key=lambda r: abs(g[r][col]))
            if abs(g[piv][col]) < 1e-15:
                raise SystemExit('lab5_budget: the LAB5 copper does not join the source and the load')
            g[col], g[piv] = g[piv], g[col]
            rhs[col], rhs[piv] = rhs[piv], rhs[col]
            for r in range(col + 1, n):
                f = g[r][col] / g[col][col]
                if f:
                    for k in range(col, n):
                        g[r][k] -= f * g[col][k]
                    rhs[r] -= f * rhs[col]
        v = [0.0] * n
        for r in range(n - 1, -1, -1):
            v[r] = (rhs[r] - sum(g[r][k] * v[k] for k in range(r + 1, n))) / g[r][r]
        return v[0]


def net_drops(net, sources, sinks):
    """Voltage drop (V) from the shorted sources to every node of a resistor network when the currents of sinks {node: A} are
    drawn at the same time (nodal solve, sources at 0 V): {root: drop}. Superposition of every sink, segment by segment."""
    roots = sorted({net.find(k) for k in net.parent}, key=repr)
    src = {net.find(s) for s in sources}
    index = {}
    for r in roots:
        if r not in src:
            index[r] = len(index)
    n = len(index)
    g = [[0.0] * n for _ in range(n)]
    for a, b, ohm in net.edges:
        ra, rb = net.find(a), net.find(b)
        if ra == rb:
            continue
        c = 1.0 / ohm
        ia, ib = index.get(ra), index.get(rb)  # None = a source (0 V)
        if ia is not None:
            g[ia][ia] += c
        if ib is not None:
            g[ib][ib] += c
        if ia is not None and ib is not None:
            g[ia][ib] -= c
            g[ib][ia] -= c
    rhs = [0.0] * n
    for node, amps in sinks.items():
        r = net.find(node)
        if r in index:
            rhs[index[r]] += amps
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(g[r][col]))
        if abs(g[piv][col]) < 1e-15:
            raise SystemExit('lab5_budget: a sink is not joined to the source by the copper')
        g[col], g[piv] = g[piv], g[col]
        rhs[col], rhs[piv] = rhs[piv], rhs[col]
        for r in range(col + 1, n):
            f = g[r][col] / g[col][col]
            if f:
                for k in range(col, n):
                    g[r][k] -= f * g[col][k]
                rhs[r] -= f * rhs[col]
    v = [0.0] * n
    for r in range(n - 1, -1, -1):
        v[r] = (rhs[r] - sum(g[r][k] * v[k] for k in range(r + 1, n))) / g[r][r]
    out = {r: 0.0 for r in src}
    out.update({r: v[i] for r, i in index.items()})
    return out


def copper_option(spec):
    """(outer mm, inner mm, option name) of the spec's copper option (pcb/generated/stackup-6l.json), or None."""
    name = (spec.get('layers') or {}).get('copper_option')
    if not name:
        return None
    opt = bg.read_json(STACKUP_6L)['copper_options'][name]
    return opt['outer_copper_mm'], opt['inner_copper_mm'], name


def net_current():
    """tools/assembly_data.py NET_CURRENT (read as data: the dict literal of the file, no import of the tool)."""
    import ast
    tree = ast.parse(ASSEMBLY.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) == 'NET_CURRENT' for t in node.targets):
            return ast.literal_eval(node.value)
    raise SystemExit('lab5_budget: no NET_CURRENT in tools/assembly_data.py')


def destinations(board, graph, net_name=NET):
    """Path-B destinations on PWR-B: the IN pads of the TPS2553 switches on LAB5 with the protective current of the net that
    NET_CURRENT rates by that switch (its protection text names the ref): [(ref, pad, rated net, amps, source)]."""
    nc = net_current()
    out = []
    refs = sorted({p['ref'] for p in board.pads if p['net'] == net_name}, key=bg.sort_ref)
    for ref in refs:
        comp = graph.get(ref) or {}
        if SWITCH not in str(comp.get('value', '')):
            continue
        pins = {str(p['number']): p for p in comp.get('pins', [])}
        inp = next((n for n, p in pins.items() if str(p.get('name', '')).upper() == 'IN' and p.get('net') == net_name), None)
        # the NET_CURRENT row whose protection names this switch (its OUT pin may feed the rated net through a filter)
        onet = next((n for n, row in sorted(nc.items()) if str(row[2]).startswith(f'{ref} {SWITCH}')), None)
        if inp is None or onet is None:
            continue
        cont, prot, why, src = nc[onet]
        out.append((ref, inp, onet, float(prot), f'tools/assembly_data.py NET_CURRENT {onet}: {why} ({src})'))
    return out


def project(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    ll = dx * dx + dy * dy
    t = 0.0 if ll == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / ll))
    return t, (x1 + t * dx, y1 + t * dy)


def pwr_b_network(board, temp_c, t_outer, plating, thickness, net_name=NET, t_inner=None, zone_joints=False):
    """LAB5 copper of PWR_B (or net_name of any routed board, W2 PCB-PWRA-4 board_audit.py) as a network. Track pieces
    are split at every via, pad or track end that touches them. W2 PWR-L6-SCRIPT: with t_inner an inner-layer track takes the
    inner copper; with zone_joints a zone of the net (board.zones 'boxes', the planned board of board_audit.py) is an ideal
    joint of the tracks, vias and pads it touches (the pin-entry pours are at most half a class width long)."""
    net = Net()
    tracks = [t for t in board.tracks if t.net == net_name]
    vias = [v for v in board.vias if v['net'] == net_name]
    pads = [p for p in board.pads if p['net'] == net_name]
    joint_zones = [z for z in board.zones if zone_joints and z['net'] == net_name and not z['keepout'] and z.get('boxes')]
    unmodelled = [z['name'] or 'zone' for z in board.zones if z['net'] == net_name and not z['keepout'] and z not in joint_zones]
    branch = {}  # pad key -> (track width, far end node of the narrowest track that touches the pad)
    for t in tracks:
        s = t.shape
        cuts = {0.0: ('end', t.layer, round(s.x1, 4), round(s.y1, 4)), 1.0: ('end', t.layer, round(s.x2, 4), round(s.y2, 4))}
        attach = []
        for o in tracks:
            if o is t or o.layer != t.layer:
                continue
            for ox, oy in ((o.shape.x1, o.shape.y1), (o.shape.x2, o.shape.y2)):
                if cb.seg_dist(ox, oy, s.x1, s.y1, s.x2, s.y2) <= s.r + o.shape.r - 1e-9:
                    attach.append((('end', t.layer, round(ox, 4), round(oy, 4)), ox, oy))
        for i, v in enumerate(vias):
            if t.layer in v['layers'] and cb.seg_dist(v['x'], v['y'], s.x1, s.y1, s.x2, s.y2) <= s.r + v['size'] / 2 - 1e-9:
                attach.append((('via', i, t.layer), v['x'], v['y']))
        for p in pads:
            if t.layer not in p['layers'] and not (p['kind'] == 'thru_hole'):
                continue
            x0, y0, x1, y1 = p['geo'].bbox
            # pad box against the track capsule: nearest point of the box to the centre line
            qx, qy = min(max(project((x0 + x1) / 2, (y0 + y1) / 2, s.x1, s.y1, s.x2, s.y2)[1][0], x0), x1), \
                min(max(project((x0 + x1) / 2, (y0 + y1) / 2, s.x1, s.y1, s.x2, s.y2)[1][1], y0), y1)
            if cb.seg_dist(qx, qy, s.x1, s.y1, s.x2, s.y2) <= s.r + 1e-9:
                attach.append((('pad', p['ref'], p['number']), p['x'], p['y']))
        for key, ax, ay in attach:
            tpar, _ = project(ax, ay, s.x1, s.y1, s.x2, s.y2)
            tpar = round(tpar, 9)
            if key[0] == 'pad' and (key not in branch or t.width < branch[key][0]):
                branch[key] = (t.width, cuts[1.0] if tpar < 0.5 else cuts[0.0])
            if tpar in cuts:
                net.join(cuts[tpar], key)
            else:
                cuts[tpar] = key
        order = sorted(cuts)
        seg_len = math.hypot(s.x2 - s.x1, s.y2 - s.y1)
        for a, b in zip(order, order[1:]):
            length = (b - a) * seg_len
            if length <= JOIN:
                net.join(cuts[a], cuts[b])
            else:
                foil = t_outer if (t_inner is None or t.layer in ('F.Cu', 'B.Cu')) else t_inner
                net.res(cuts[a], cuts[b], rho(temp_c) * length / (t.width * foil))
    for i, v in enumerate(vias):
        layers = [l for l in v['layers'] if l in ('F.Cu', 'B.Cu')]
        r_out = v['drill'] / 2
        area = math.pi * (r_out ** 2 - (r_out - plating) ** 2)
        for a, b in zip(layers, layers[1:]):
            net.res(('via', i, a), ('via', i, b), rho(temp_c) * thickness / area)
    for p in pads:
        net.node(('pad', p['ref'], p['number']))
    for z in joint_zones:  # ideal joint: everything of the net that touches one of the zone's rectangles on its layer
        key = ('zone', z['name'])
        net.node(key)
        lay = z['layers'][0]
        for x0, y0, x1, y1 in z['boxes']:
            for t in tracks:
                if t.layer != lay:
                    continue
                s = t.shape
                for ex, ey, tp in ((s.x1, s.y1, 0.0), (s.x2, s.y2, 1.0)):
                    if x0 - s.r <= ex <= x1 + s.r and y0 - s.r <= ey <= y1 + s.r:
                        net.join(('end', t.layer, round(ex, 4), round(ey, 4)), key)
            for i, v in enumerate(vias):
                if x0 - v['size'] / 2 <= v['x'] <= x1 + v['size'] / 2 and y0 - v['size'] / 2 <= v['y'] <= y1 + v['size'] / 2:
                    for l in v['layers']:
                        if l == lay:
                            net.join(('via', i, l), key)
            for p in pads:
                bx = p['geo'].bbox
                if (lay in p['layers'] or p['kind'] == 'thru_hole') and not (bx[2] < x0 or bx[0] > x1 or bx[3] < y0 or bx[1] > y1):
                    net.join(('pad', p['ref'], p['number']), key)
    net.branch = branch
    return net, {'tracks': len(tracks), 'vias': len(vias), 'pads': len(pads), 'zones_not_modelled': unmodelled,
                 **({'zones_as_ideal_joints': sorted(z['name'] for z in joint_zones)} if joint_zones else {})}


def pad_centres(spec, ref, numbers):
    part = next((p for p in spec['parts'] if p['ref'] == ref and p.get('anchor')), None)
    if part is None:
        return None
    graph = bg.load_graph() if part['source'] == 'graph' else None
    if part['source'] == 'graph':
        manifest = bg.read_json(bg.MANIFEST)
        fp = next(f for f in manifest['footprints'] if f['footprint'] == graph[ref]['footprint'])
        path = BASE / fp['file']
    else:
        path = bg.footprint_file({'fpid': part['footprint'], 'library': part['footprint_library'],
                                  'sha256': part['footprint_sha256']})
    geo = bg.placed_geometry(bg.footprint_geometry(path.read_text(encoding='utf-8')), part['anchor'])
    out = []
    for n in numbers:
        out += [tuple(xy) for xy in geo['pads'][str(n)]]
    return out


def centroid(points):
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def build():
    spec = bg.read_json(SPEC)
    netclasses = bg.read_json(NETCLASSES)
    e1 = bg.read_json(E1)
    e105 = next(o for o in e1['open_items'] if o['id'] == 'E1-05')
    i_design = e1['lab5_budget']['design_continuous_a']
    layers = {l.get('kicad'): l for l in netclasses['stackup']['layers'] if l.get('kicad')}
    t_outer = layers['F.Cu']['copper_mm']
    thickness = netclasses['stackup']['board_thickness_mm']
    plating = netclasses['formulas']['via']['plating_mm']
    w_class = netclasses['classes'][netclasses['nets'][NET]['class']]['outer_min_width_mm']
    pwr_b_spec = bg.read_json(PWR_B_SPEC)
    t_inner, option = None, None
    opt = copper_option(pwr_b_spec)
    if opt:  # W2 PWR-L6-SCRIPT: both power boards on the 6-layer 2 oz option (PWR_A make_board.py COPPER_OPTION, the same)
        t_outer, t_inner, option = opt
        o6 = bg.read_json(STACKUP_6L)['copper_options'][option]
        w_class = o6['power_classes'][netclasses['nets'][NET]['class']]['outer_min_width_mm']
    graph = bg.load_graph()
    pair = spec['b2b'][0]
    mine, mate_ref = pair['ref'], pair['mate_ref']
    mate = next(p for p in pwr_b_spec['parts'] if p['ref'] == mate_ref)
    mate_pins = ({str(p['number']): p.get('net') for p in graph[mate_ref]['pins']} if mate['source'] == 'graph'
                 else mate['pins'])
    lab5_contacts = sorted((k for k, v in mate_pins.items() if v == NET), key=int)
    inverse = {v: k for k, v in pair['pin_map'].items()} if isinstance(pair['pin_map'], dict) else None
    my_contacts = sorted((inverse[c] if inverse else c for c in lab5_contacts), key=int)
    board = cb.load_board(PWR_B_BOARD)

    temps = {'20C': 20.0, f'{int(T_HOT)}C': T_HOT}
    pwr_b = {}
    loads = sorted({(p['ref'], p['number']) for p in board.pads if p['net'] == NET and p['ref'] != mate_ref},
                   key=lambda x: (bg.sort_ref(x[0]), x[1]))
    for tk, tc in temps.items():
        net, info = pwr_b_network(board, tc, t_outer, plating, thickness, t_inner=t_inner)
        rows = []
        for ref, num in loads:
            src = [('pad', mate_ref, c) for c in lab5_contacts]
            r = net.resistance(src, ('pad', ref, num))
            width, far = net.branch.get(('pad', ref, num), (None, None))
            shared = net.resistance(src, far) if far is not None else None
            rows.append({'pad': f'{ref}.{num}', 'sheet': graph[ref]['_sheet'], 'group': graph[ref].get('group'),
                         'resistance_mohm': r4(r * 1e3),
                         'last_track_width_mm': width,
                         'to_start_of_last_track_mohm': r4(shared * 1e3) if shared is not None else None})
        pwr_b[tk] = rows
    e2_loads = [r['pad'] for r in pwr_b['20C'] if r['sheet'] == 'E2' and r['pad'].split('.')[0].startswith('U')]
    # W2 PWR-L6-SCRIPT: path B per destination, current-weighted (synthesis e105_decision): every TPS2553 input on PWR-B LAB5 at
    # the protective current of its output net, all at once, from the shorted J209 LAB5 contacts; the B2B delta at the share
    # per contact of the total current
    dests = destinations(board, graph)
    i_total = sum(d[3] for d in dests)
    weighted = {}
    for tk, tc in temps.items():
        net, _info = pwr_b_network(board, tc, t_outer, plating, thickness, t_inner=t_inner)
        src = [('pad', mate_ref, c) for c in lab5_contacts]
        v = net_drops(net, src, {('pad', r, n): a for r, n, _o, a, _w in dests})
        weighted[tk] = {f'{r}.{n}': r4(v[net.find(('pad', r, n))] * 1e3) for r, n, _o, _a, _w in dests}
    b2b_drop_mv = r4(i_total / len(lab5_contacts) * B2B_DELTA * 1e3)
    path_b_weighted = {
        'label': ('MODEL: path B restated per destination (synthesis e105_decision): drop from L101.2 to each TPS2553 input <= '
                  f'{DROP_BUDGET_MV} mV (E1-05 "10 mOhm = 32 mV at 3.2 A") at the worst-case concurrent currents, segment by segment. '
                  'This block: the PWR-B copper (multi-sink solve from the shorted J209 LAB5 contacts) and the B2B LLCR delta at the '
                  'per-contact share; board_audit.py adds the PWR-A copper L101.2 -> J208 at the total current'),
        'drop_budget_mv': DROP_BUDGET_MV,
        'destinations': [{'pad': f'{r}.{n}', 'out_net': o, 'current_a': a, 'current_source': w} for r, n, o, a, w in dests],
        'total_current_a': r4(i_total),
        'b2b': {'contacts': len(lab5_contacts), 'delta_per_contact_mohm': B2B_DELTA * 1e3,
                'drop_mv_max': b2b_drop_mv, 'initial_resistance': 'TBD (not stated in the Samtec product specification)'},
        'pwr_b_drop_mv': weighted,
        'not_included': 'the PWR-A LAB5 loads (U503, U553, J104, J206.2 and their bypasses) draw through the PWR-A trunk too; E1-05 '
                        'names E1 -> E2, so they are left out, as the synthesis says (MODEL)',
    }

    # --- PWR-A: anchored ends only ---
    l101 = pad_centres(spec, 'L101', ['2'])
    e1_ref = 'L101.2' if l101 else 'F102.2'
    e1_end = centroid(l101 or pad_centres(spec, 'F102', ['2']))
    lt_end = centroid(pad_centres(spec, 'U204', list('1234')) + pad_centres(spec, 'U205', list('1234')))
    b2b_end = centroid(pad_centres(spec, mine, my_contacts))
    vout = sorted(str(p['number']) for p in graph['U108']['pins'] if str(p.get('name', '')).startswith('VOUT')) \
        if 'U108' in graph else []
    raw_pads = pad_centres(spec, 'U108', vout) if vout else None

    def path(a, b):
        return {'from': [r4(a[0]), r4(a[1])], 'to': [r4(b[0]), r4(b[1])],
                'straight_mm': r4(math.hypot(b[0] - a[0], b[1] - a[1])),
                'orthogonal_mm': r4(abs(b[0] - a[0]) + abs(b[1] - a[1]))}

    def copper(length_mm, width_mm, n_layers, tc):
        return rho(tc) * length_mm / (width_mm * t_outer * n_layers)

    def width_layers_for(length_mm, r_ohm, tc):
        return None if r_ohm <= 0 else r4(rho(tc) * length_mm / (t_outer * r_ohm))

    out_paths = {}
    for key, (a, b, what) in {
        'A_E1_to_LT3045': (e1_end, lt_end, f'{e1_ref} (E1 LAB5 end) -> U204/U205 IN pads (E2_LNA_IN via L205): '
                                           'the E1-05 headroom path, PWR-A only'),
        'B_E1_to_B2B': (e1_end, b2b_end, f'{e1_ref} -> {mine} LAB5 contacts (PWR-A part of the path to the PWR-B loads)'),
    }.items():
        p = path(a, b)
        row = {'what': what, **p, 'by_temperature': {}}
        for tk, tc in temps.items():
            row['by_temperature'][tk] = {
                'narrowest_legal_mohm': {'straight': r4(copper(p['straight_mm'], w_class, 1, tc) * 1e3),
                                         'orthogonal': r4(copper(p['orthogonal_mm'], w_class, 1, tc) * 1e3)},
                'width_x_outer_layers_mm_for_whole_budget': {
                    'straight': width_layers_for(p['straight_mm'], BUDGET, tc),
                    'orthogonal': width_layers_for(p['orthogonal_mm'], BUDGET, tc)},
            }
        out_paths[key] = row
    # path B with the measured PWR-B copper and the B2B delta: what is left for the PWR-A copper
    remaining = {}
    for tk, tc in temps.items():
        rows = {}
        b2b_delta = B2B_DELTA / len(lab5_contacts)
        for r in pwr_b[tk]:
            if r['pad'] not in e2_loads:
                continue
            left = BUDGET - b2b_delta - r['resistance_mohm'] / 1e3
            orth = out_paths['B_E1_to_B2B']['orthogonal_mm']
            rows[r['pad']] = {
                'pwr_b_copper_mohm': r['resistance_mohm'],
                'pwr_b_copper_to_branch_start_mohm': r['to_start_of_last_track_mohm'],
                'pwr_b_branch_width_mm': r['last_track_width_mm'],
                'b2b_delta_max_mohm': r4(b2b_delta * 1e3),
                'b2b_initial_mohm': 'TBD (not stated in the Samtec product specification)',
                'left_for_pwr_a_copper_mohm': r4(left * 1e3),
                'pwr_a_width_x_outer_layers_mm_needed_orthogonal': width_layers_for(orth, left, tc) if left > 0 else None,
                'fits': left > 0,
            }
        remaining[tk] = rows
    def pour_path(net, a, b, what):
        zones = [z for z in spec['pre_route'].get('zones', []) if z['net'] == net and z.get('outline') != 'board']
        # pin-entry stems and branch pours (a side capacitor, review fix F2) are not the series path of the net
        main = [z for z in zones if not z.get('pin_entry') and not z.get('branch')]
        if not main:
            return None
        widths = []
        for z in main:
            zx, zy = [q[0] for q in z['outline']], [q[1] for q in z['outline']]
            widths.append(min(max(zx) - min(zx), max(zy) - min(zy)))
        w = min(widths)
        length = abs(b[0] - a[0]) + abs(b[1] - a[1])
        return {'what': what, 'from': [r4(a[0]), r4(a[1])], 'to': [r4(b[0]), r4(b[1])], 'orthogonal_mm': r4(length),
                'narrowest_pour_width_mm': r4(w), 'pours': sorted(z['id'] for z in main),
                'not_in_the_series_path': sorted(z['id'] for z in zones if z not in main), 'outer_layers': 1,
                'by_temperature_upper_bound': {tk: r4(copper(length, w, 1, tc) * 1e3) for tk, tc in temps.items()},
                'unit': 'mOhm',
                'label': 'MODEL upper bound: the whole orthogonal path at the narrowest scripted pour width, F.Cu only'}

    if raw_pads:
        upstream = pour_path('E1_LAB5_RAW', centroid(raw_pads), centroid(pad_centres(spec, 'F102', ['1'])),
                             f'E1_LAB5_RAW pours (scripted): U108 VOUT ({", ".join(vout)}) -> F102.1, before F102 (not part of '
                             'the E1-05 connection figure; adds to the total drop)')
        fused = pour_path('E1_LAB5_FUSED', centroid(pad_centres(spec, 'F102', ['2'])), e1_end if l101 else None,
                          'E1_LAB5_FUSED pour (scripted): F102.2 -> L101.1 (inside the E1 chain U108 -> F102 -> L101)') \
            if l101 else None
    else:
        upstream = {'what': 'E1_LAB5_RAW (LAB5 converter output -> F102.1, before F102; not part of the E1-05 connection '
                            'figure)',
                    'value': 'TBD: the SHRINK-2 LAB5 converter (TPSM63606RDLR) is the reserved block CONV_LAB5 until GR-5A '
                             'puts it into the graph; PCB-PWRA-3 part 2 scripts the pour from its output to F102.1',
                    'spec_planned_change': next((c for c in spec.get('planned_changes', []) if c['id'] == 'U108-LAB5'), None)}
        fused = None
    shared_b = {tk: rows for tk, rows in pwr_b.items()}

    return {
        'schema': 'srrx-pwra-lab5-budget-v1',
        'board_id': 'PWR_A',
        'status': (f'MODEL: copper resistance from geometry (IACS copper, finished outer {t_outer} mm'
                   + (f', inner {t_inner} mm, copper option {option}' if option else '') + '); no PWR-A board exists, no '
                   'measurement; E1-05 and every bench gate stay OPEN'),
        'generator': 'build/kicad/boards/PWR_A/lab5_budget.py',
        'inputs': {
            'spec_sha256': bg.sha256_bytes(bg.canonical(spec)),
            'pwr_b_board_sha256': bg.sha256_file(PWR_B_BOARD),
            'pwr_b_mate_pins_sha256': bg.sha256_bytes(bg.canonical(mate_pins)),
            'netclasses_sha256': bg.sha256_file(NETCLASSES),
            'e1_05': e105['resolve'][e105['resolve'].find('Відкрито'):].split('Якщо')[0].strip(),
        },
        'constants': {
            'copper_conductivity_s_per_m_20c': SIGMA_IACS, 'copper_conductivity_source': SIGMA_SRC,
            'alpha_per_k': ALPHA, 'alpha_source': ALPHA_SRC,
            'resistivity_ohm_mm_20c': r6(rho(20.0)), 'resistivity_ohm_mm_hot': r6(rho(T_HOT)), 'hot_c': T_HOT,
            'outer_copper_mm': t_outer, 'board_thickness_mm': thickness, 'via_plating_mm': plating,
            'copper_source': ('pcb/generated/stackup-6l.json copper_options.' + option + ' (jlcpcb.com read 2026-11-13; '
                              'pcb/boards/PWR_B.json layers.copper_option) and ' if option else
                              'pcb/generated/netclasses.json stackup (https://jlcpcb.com/impedance, JLC04161H-7628, read '
                              '2026-11-07) and ') + 'formulas.via.plating_mm (https://jlcpcb.com/capabilities/pcb-capabilities, '
                             'hole wall average plating 18 um, read 2026-11-07)',
            'inner_copper_mm': t_inner, 'copper_option': option,
            'class_width_mm': w_class, 'class': netclasses['nets'][NET]['class'],
            'budget_mohm': BUDGET * 1e3, 'design_current_a': i_design,
            'drop_per_10_mohm_mv': r4(0.010 * i_design * 1e3),
            'b2b_delta_per_contact_mohm': B2B_DELTA * 1e3, 'b2b_source': B2B_SRC,
            'b2b_pair': {'pwr_a': mine, 'pwr_b': mate_ref},
            'b2b_lab5_contacts': lab5_contacts, 'b2b_lab5_contacts_pwr_a': my_contacts,
        },
        'pwr_b_copper': {
            'label': 'MEASURED on the CI-routed PWR_B board (geometry of the drawn copper, not a bench value): resistance '
                     f'from the {len(lab5_contacts)} shorted {mate_ref} LAB5 contacts to each LAB5 pad, and to the start of the narrowest track '
                     'that reaches the pad (the branch that carries only that load; the rest is shared trunk)',
            'board': PWR_B_BOARD.relative_to(BASE).as_posix(),
            'network': pwr_b_network(board, 20.0, t_outer, plating, thickness, t_inner=t_inner)[1],
            'by_temperature': shared_b,
            'e2_loads': e2_loads,
        },
        'pwr_a_paths': out_paths,
        'path_b_remaining_budget': remaining,
        'path_b_current_weighted': path_b_weighted,
        'upstream_e1_lab5_raw': upstream,
        'upstream_e1_lab5_fused': fused,
        'e1_end': e1_ref,
        'findings': [],
    }


def findings(doc):
    out = []
    a = doc['pwr_a_paths']['A_E1_to_LT3045']['by_temperature']['20C']
    w = doc['constants']['class_width_mm']
    out.append(f"A (E1 -> LT3045, PWR-A only): the narrowest legal LAB5 copper (PWR3A {w} mm, one outer layer) gives "
               f"{a['narrowest_legal_mohm']['orthogonal']} mOhm on the orthogonal path at 20 C; the 10 mOhm budget needs "
               f"width x outer layers >= {a['width_x_outer_layers_mm_for_whole_budget']['orthogonal']} mm there")
    for pad, row in doc['path_b_remaining_budget']['20C'].items():
        if row['fits']:
            out.append(f"B (E1 -> {pad} on PWR-B): PWR-B copper {row['pwr_b_copper_mohm']} mOhm + B2B delta <= "
                       f"{row['b2b_delta_max_mohm']} mOhm leaves {row['left_for_pwr_a_copper_mohm']} mOhm for the PWR-A "
                       f"copper (width x outer layers >= {row['pwr_a_width_x_outer_layers_mm_needed_orthogonal']} mm "
                       f"orthogonal); B2B initial resistance TBD")
        else:
            out.append(f"B (E1 -> {pad} on PWR-B): PWR-B copper {row['pwr_b_copper_mohm']} mOhm (of it "
                       f"{row['pwr_b_copper_to_branch_start_mohm']} mOhm up to its {row['pwr_b_branch_width_mm']} mm branch) + "
                       f"B2B delta <= {row['b2b_delta_max_mohm']} mOhm already exceed 10 mOhm before any PWR-A copper")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args(argv)
    doc = build()
    doc['findings'] = findings(doc)
    text = json.dumps(doc, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if not OUT.is_file() or OUT.read_text(encoding='utf-8') != text:
            print('lab5-budget.json is stale: rerun build/kicad/boards/PWR_A/lab5_budget.py')
            return 1
        print('lab5-budget.json reproduces')
        return 0
    bg.atomic_write(OUT, text)
    print('\n'.join(doc['findings']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
