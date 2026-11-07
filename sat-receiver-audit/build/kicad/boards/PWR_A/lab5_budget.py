#!/usr/bin/env python3
"""LAB5 E1 -> E2 copper resistance against E1-05 (W2 PCB-PWRA-2, CC-36 item 12): a MODEL, standard library only.

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
    overlapping copper are ideal joints; resistance from the four shorted B2B1 LAB5 contacts to each LAB5 load pad.
  - B2B: Samtec QSH/QTH-060 contact resistance. The product specification states only the change after the tests
    (LLCR delta <= 15 mOhm per contact); the initial value is not stated there, so it stays TBD.
  - PWR-A copper: no placed or routed PWR-A exists (F2, placement-study.json). From the anchors of PWR_A.spec-draft.json
    (F102 for the E1 end, U204/U205 IN pads, the B2B2 LAB5 contacts) the straight and the orthogonal path lengths
    give the resistance of the narrowest legal copper (PWR3A 1.85 mm, one outer layer) and the copper width x outer
    layers that the remaining budget needs. L101, L205 and C111/C112 are not anchored: F102.2 and the U204/U205 IN
    pads stand for the two ends.
  - E1_LAB5_RAW (U108 VOUT -> F102.1, upstream of the E1-05 figure): the scripted 9.6 mm pours on L1 and L4.
Copper: annealed copper (IACS) at 20 C and at 50 C (the E1-05 thermal test ambient; the copper itself runs warmer).
Needs KICAD10_FOOTPRINT_DIR for the FX8 placeholder land of B2B2 (board_gen.image_library_dir).
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
DRAFT = HERE / 'PWR_A.spec-draft.json'
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
B2B_SRC = ('Samtec QSH/QTH product specification Rev K (2025-02-20) section 3.5, '
           'https://suddendocs.samtec.com/productspecs/qsh-qth.pdf read 2026-11-07: "Contact Resistance (LLCR) EIA-364-23 '
           'delta 15 mOhm maximum (Samtec defined)"; current rating 2 A (one pin powered per row); no initial value stated')
BUDGET = 0.010             # Ohm, E1-05
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


def project(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    ll = dx * dx + dy * dy
    t = 0.0 if ll == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / ll))
    return t, (x1 + t * dx, y1 + t * dy)


def pwr_b_network(board, temp_c, t_outer, plating, thickness):
    """LAB5 copper of PWR_B as a network. Track pieces are split at every via, pad or track end that touches them."""
    net = Net()
    tracks = [t for t in board.tracks if t.net == NET]
    vias = [v for v in board.vias if v['net'] == NET]
    pads = [p for p in board.pads if p['net'] == NET]
    unmodelled = [z['name'] or 'zone' for z in board.zones if z['net'] == NET and not z['keepout']]
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
                net.res(cuts[a], cuts[b], rho(temp_c) * length / (t.width * t_outer))
    for i, v in enumerate(vias):
        layers = [l for l in v['layers'] if l in ('F.Cu', 'B.Cu')]
        r_out = v['drill'] / 2
        area = math.pi * (r_out ** 2 - (r_out - plating) ** 2)
        for a, b in zip(layers, layers[1:]):
            net.res(('via', i, a), ('via', i, b), rho(temp_c) * thickness / area)
    for p in pads:
        net.node(('pad', p['ref'], p['number']))
    net.branch = branch
    return net, {'tracks': len(tracks), 'vias': len(vias), 'pads': len(pads), 'zones_not_modelled': unmodelled}


def pad_centres(spec, ref, numbers):
    part = next(p for p in spec['parts'] if p['ref'] == ref)
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
    spec = bg.read_json(DRAFT)
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
    b2b1 = next(p for p in pwr_b_spec['parts'] if p['ref'] == 'B2B1')
    lab5_contacts = sorted((k for k, v in b2b1['pins'].items() if v == NET), key=int)
    board = cb.load_board(PWR_B_BOARD)

    temps = {'20C': 20.0, f'{int(T_HOT)}C': T_HOT}
    pwr_b = {}
    loads = sorted({(p['ref'], p['number']) for p in board.pads if p['net'] == NET and p['ref'] != 'B2B1'},
                   key=lambda x: (bg.sort_ref(x[0]), x[1]))
    graph = bg.load_graph()
    for tk, tc in temps.items():
        net, info = pwr_b_network(board, tc, t_outer, plating, thickness)
        rows = []
        for ref, num in loads:
            src = [('pad', 'B2B1', c) for c in lab5_contacts]
            r = net.resistance(src, ('pad', ref, num))
            width, far = net.branch.get(('pad', ref, num), (None, None))
            shared = net.resistance(src, far) if far is not None else None
            rows.append({'pad': f'{ref}.{num}', 'sheet': graph[ref]['_sheet'], 'group': graph[ref].get('group'),
                         'resistance_mohm': r4(r * 1e3),
                         'last_track_width_mm': width,
                         'to_start_of_last_track_mohm': r4(shared * 1e3) if shared is not None else None})
        pwr_b[tk] = rows
    e2_loads = [r['pad'] for r in pwr_b['20C'] if r['sheet'] == 'E2' and r['pad'].split('.')[0].startswith('U')]

    # --- PWR-A: anchored ends only ---
    e1_end = centroid(pad_centres(spec, 'F102', ['2']))
    lt_end = centroid(pad_centres(spec, 'U204', list('1234')) + pad_centres(spec, 'U205', list('1234')))
    b2b_end = centroid(pad_centres(spec, 'B2B2', lab5_contacts))
    raw_a = centroid(pad_centres(spec, 'U108', ['VOUT']))
    raw_b = centroid(pad_centres(spec, 'F102', ['1']))
    raw_zone = next(z for z in spec['pre_route']['zones'] if z['id'] == 'LAB5-RAW-F')
    zx = [p[0] for p in raw_zone['outline']]
    zy = [p[1] for p in raw_zone['outline']]
    raw_w = min(max(zx) - min(zx), max(zy) - min(zy))
    raw_layers = len([z for z in spec['pre_route']['zones'] if z['net'] == 'E1_LAB5_RAW'])

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
        'A_E1_to_LT3045': (e1_end, lt_end, 'F102.2 (E1 LAB5 end; L101 adjacent) -> U204/U205 IN pads (E2_LNA_IN via L205): '
                                           'the E1-05 headroom path, PWR-A only'),
        'B_E1_to_B2B2': (e1_end, b2b_end, 'F102.2 -> B2B2 LAB5 contacts (PWR-A part of the path to the PWR-B loads)'),
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
            orth = out_paths['B_E1_to_B2B2']['orthogonal_mm']
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
    raw_len = math.hypot(raw_b[0] - raw_a[0], raw_b[1] - raw_a[1])
    upstream = {'what': 'E1_LAB5_RAW pours LAB5-RAW-F/B (scripted): U108 VOUT -> F102.1, before F102 (not part of the '
                        'E1-05 connection figure; adds to the total drop)',
                'from': [r4(raw_a[0]), r4(raw_a[1])], 'to': [r4(raw_b[0]), r4(raw_b[1])], 'length_mm': r4(raw_len),
                'pour_width_mm': r4(raw_w), 'outer_layers': raw_layers,
                'by_temperature': {tk: r4(copper(raw_len, raw_w, raw_layers, tc) * 1e3) for tk, tc in temps.items()},
                'unit': 'mOhm'}
    shared_b = {tk: rows for tk, rows in pwr_b.items()}

    return {
        'schema': 'srrx-pwra-lab5-budget-v1',
        'board_id': 'PWR_A',
        'status': 'MODEL: copper resistance from geometry (IACS copper, finished 1 oz outer); no PWR-A board exists, no '
                  'measurement; E1-05 and every bench gate stay OPEN',
        'generator': 'build/kicad/boards/PWR_A/lab5_budget.py',
        'inputs': {
            'spec_sha256': bg.sha256_bytes(bg.canonical(spec)),
            'pwr_b_board_sha256': bg.sha256_file(PWR_B_BOARD),
            'pwr_b_spec_b2b1_pins_sha256': bg.sha256_bytes(bg.canonical(b2b1['pins'])),
            'netclasses_sha256': bg.sha256_file(NETCLASSES),
            'e1_05': e105['resolve'][e105['resolve'].find('Відкрито'):].split('Якщо')[0].strip(),
        },
        'constants': {
            'copper_conductivity_s_per_m_20c': SIGMA_IACS, 'copper_conductivity_source': SIGMA_SRC,
            'alpha_per_k': ALPHA, 'alpha_source': ALPHA_SRC,
            'resistivity_ohm_mm_20c': r6(rho(20.0)), 'resistivity_ohm_mm_hot': r6(rho(T_HOT)), 'hot_c': T_HOT,
            'outer_copper_mm': t_outer, 'board_thickness_mm': thickness, 'via_plating_mm': plating,
            'copper_source': 'pcb/generated/netclasses.json stackup (https://jlcpcb.com/impedance, JLC04161H-7628, read '
                             '2026-11-07) and formulas.via.plating_mm (https://jlcpcb.com/capabilities/pcb-capabilities, '
                             'hole wall average plating 18 um, read 2026-11-07)',
            'class_width_mm': w_class, 'class': netclasses['nets'][NET]['class'],
            'budget_mohm': BUDGET * 1e3, 'design_current_a': i_design,
            'drop_per_10_mohm_mv': r4(0.010 * i_design * 1e3),
            'b2b_delta_per_contact_mohm': B2B_DELTA * 1e3, 'b2b_source': B2B_SRC,
            'b2b_lab5_contacts': lab5_contacts,
        },
        'pwr_b_copper': {
            'label': 'MEASURED on the CI-routed PWR_B board (geometry of the drawn copper, not a bench value): resistance '
                     'from the four shorted B2B1 LAB5 contacts to each LAB5 pad, and to the start of the narrowest track '
                     'that reaches the pad (the branch that carries only that load; the rest is shared trunk)',
            'board': PWR_B_BOARD.relative_to(BASE).as_posix(),
            'network': pwr_b_network(board, 20.0, t_outer, plating, thickness)[1],
            'by_temperature': shared_b,
            'e2_loads': e2_loads,
        },
        'pwr_a_paths': out_paths,
        'path_b_remaining_budget': remaining,
        'upstream_e1_lab5_raw': upstream,
        'findings': [],
    }


def findings(doc):
    out = []
    a = doc['pwr_a_paths']['A_E1_to_LT3045']['by_temperature']['20C']
    out.append(f"A (E1 -> LT3045, PWR-A only): the narrowest legal LAB5 copper (PWR3A 1.85 mm, one outer layer) gives "
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
