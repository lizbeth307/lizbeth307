#!/usr/bin/env python3
"""PWR-A audits of a routed board that pcb/check_boards.py does not make (W2 PCB-PWRA-4), standard library.

  python3 build/kicad/boards/PWR_A/board_audit.py [--dir DIR] [--review] [--check]

DIR (default build/kicad/boards/PWR_A) holds PWR_A.kicad_pcb and report.json of one sr-rx-pcb route run; the spec is
DIR/board-spec.json if it exists, else pcb/boards/PWR_A.json. Writes DIR/board-audit.json (--check compares). Read with
the pure-Python reader of pcb/check_boards.py; contract frame mm, y up.

Checks (brief of W2 PCB-PWRA-4; the rest is in check_boards review.json and the board_gen report):
  zones       TPS7A4701 / LT3045 courtyards inside contract thermal_bond zones 1-2; the converter_zone_refs of the
              contract (U107, L102 in zone 3; U108 in zone 4) inside their zone
  pockets     every bottom courtyard inside one plate pocket PB1-PB13 (contract bottom_side.keep_in_mm)
  h_trim      every top part whose courtyard meets a PWR-B THT pin field + window_margin (pcb/boards/PWR_B.json h_trim)
              is no taller than the H-TRIM zone height (2.7 mm); a part without a height in the spec is unverified
  holes       the 7 contract holes are unnetted mounting holes
  cell        no copper of E1_CELL0 or B- on the board (PWR-02: then no clearance from GND/P- can fail)
  copper      MODEL resistance of the drawn copper (IACS copper, 1 oz outer; lab5_budget.py network: tracks and vias,
              zones not modelled): LAB5 L101.2 -> L205.1 (path A to the LT3045 filter) and -> the J208 LAB5 contacts
              (path B, plus at most 15 mOhm / 4 of LSHM contact delta and the PWR-B copper of lab5-budget.json),
              E1_LAB5_RAW U108 VOUT -> F102.1 and E1_LAB5_FUSED F102.2 -> L101.1; a net the copper does not join
              is reported as not joined
  fill        top courtyards over the usable area (outline less the hole keep-outs), MODEL
  converters  (W2 PWR-L6-SCRIPT, MODEL geometry; TI LM61460 SNVSBD5D rev. D section 11.1 / figure 11-2 and TPSM63606 SLVSGB4B
              rev. B section 11.1, re-read 2026-11-14): CVCC within 2 mm of VCC/AGND, the feedback dividers within 5 mm of FB,
              no via on E1_SYS12_SW, the SW-CBOOT link on F.Cu through the VIN2-RBOOT gap, the FB nodes on F.Cu only, the U108
              VOUT pins joined by an In4.Cu/B.Cu polygon, AGND 6/11 to PGND 19 under U108, no copper of a foreign net on F.Cu or
              In1.Cu over the converter zones 3'/4' (board-spec converter_zones), In1.Cu a solid GND plane
  class_widths (W2 PWR-L6-SCRIPT, planned board only) pcb/check_boards.py check_classes on the scripted copper of the spec (2 oz
              widths of the copper option, exemption policy), MODEL
  e1_05       (W2 PWR-L6-SCRIPT) path A against 10 mOhm; path B per destination: the PWR-A copper L101.2 -> J208 at the total
              TPS2553 current + the B2B delta + the PWR-B drop of lab5-budget.json path_b_current_weighted, against 32 mV (MODEL)
With --review (a record folder such as route-iteration-2/, whose board pcb/check_boards.py --all does not see) it also
writes DIR/review.json: pcb/check_boards.py review_board on that board and spec, with the PWR_B board of record as the
B2B mate, as check_boards --board PWR_A writes it for an installed board.
MODEL / CI only: no bench gate is closed by this file.
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
sys.path.insert(0, str(HERE))
import board_gen as bg  # noqa: E402
import check_boards as cb  # noqa: E402
import lab5_budget as lb  # noqa: E402

CONTRACT = BASE / 'mechanical/generated/contract/boards.json'
PWR_B_SPEC = BASE / 'pcb/boards/PWR_B.json'
PSPEC = BASE / 'pcb/partition-spec.json'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
LAB5 = HERE / 'lab5-budget.json'
EPS = 1e-6


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def r4(v):
    return bg.r4(v)


def inside(b, r):
    return r[0] - EPS <= b[0] and r[1] - EPS <= b[1] and b[2] <= r[2] + EPS and b[3] <= r[3] + EPS


def overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


class _Box:
    def __init__(self, box):
        self.bbox = tuple(box)


class _Identity:
    def to_contract(self, x, y):
        return x, y


class SpecBoard:
    """The planned board of a spec (no routed board yet): footprints, pads and the scripted locked copper of
    make_board.py in contract mm, in the shape the check_boards reader gives (the copper section then models only the
    scripted tracks and vias; W2 PWR-L6-SCRIPT: pads as their copper boxes, scripted pours as zones filled to their outline,
    the 6 copper layers, so check_boards check_classes runs on it)."""

    def __init__(self, spec):
        import make_board as mb
        inp = mb.Inputs(spec)
        self.copper_layers = list(mb.COPPER6) if spec.get('layers', {}).get('copper') == 6 else ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
        self.footprints, self.pads, self.tracks, self.vias, self.zones, self.copper = [], [], [], [], [], []
        self.unverified = []
        self.path = None
        for ref, pa in inp.parts.items():
            pads = []
            for q in pa.pads:
                layers = list(self.copper_layers) if q['type'] in ('thru_hole', 'np_thru_hole') else [f'{pa.side}.Cu']
                x0, y0, x1, y1 = q['box']
                geo = cb.Poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
                rec = {'ref': ref, 'number': q['number'], 'kind': q['type'], 'net': q['net'], 'layers': layers,
                       'geo': geo, 'x': q['at'][0], 'y': q['at'][1], 'w': x1 - x0, 'h': y1 - y0, 'angle': 0.0, 'shape': 'rect',
                       'drill': list(q['drill'] or [])}
                pads.append(rec)
                self.pads.append(rec)
                if q['type'] != 'np_thru_hole':
                    for lay in layers:
                        self.copper.append(cb.Item('pad', q['net'], lay, geo, ref=ref, pad=q['number'], extra=rec))
            self.footprints.append({'ref': ref, 'side': 'top' if pa.side == 'F' else 'bottom', 'courtyard': tuple(pa.box),
                                    'pads': pads, 'lib': inp.graph.get(ref, {}).get('footprint', '')})
        for t in spec['pre_route']['tracks']:
            for a, b in zip(t['path'], t['path'][1:]):
                it = cb.Item('track', t['net'], t['layer'], cb.Capsule(a[0], a[1], b[0], b[1], t['width_mm'] / 2))
                it.width = t['width_mm']
                self.tracks.append(it)
                self.copper.append(it)
        for v in spec['pre_route']['vias']:
            rec = {'x': v['at'][0], 'y': v['at'][1], 'size': v['diameter_mm'], 'drill': v['drill_mm'], 'net': v['net'],
                   'layers': list(self.copper_layers), 'id': v.get('id')}
            self.vias.append(rec)
            for lay in self.copper_layers:
                self.copper.append(cb.Item('via', v['net'], lay, cb.Capsule(rec['x'], rec['y'], rec['x'], rec['y'], rec['size'] / 2), extra=rec))
        for z in spec['pre_route']['zones']:
            if z['outline'] == 'board':
                self.zones.append({'net': z['net'], 'layers': [z['layer']], 'keepout': False, 'outline': [], 'fills': {},
                                   'name': z['id'], 'plane': True})
                continue
            poly = cb.Poly([tuple(p) for p in z['outline']])
            self.zones.append({'net': z['net'], 'layers': [z['layer']], 'keepout': False, 'outline': [tuple(p) for p in z['outline']],
                               'fills': {z['layer']: [poly]}, 'name': z['id'], 'boxes': mb.outline_boxes([tuple(p) for p in z['outline']])})
            self.copper.append(cb.Item('zone', z['net'], z['layer'], poly, extra=self.zones[-1]))
        self.holes = [{'ref': f'H{k + 1}', 'net': None} for k in range(len(read(CONTRACT)['boards'][spec['contract']['board']]['holes_mm']))]


SCRIPT_SOURCE = ('TI LM61460 SNVSBD5D (rev. D, July 2022) section 11.1 and figure 11-2 and TI TPSM63606 SLVSGB4B (rev. B, April '
                 '2022) section 11.1, re-read 2026-11-14 (fetch-only, not committed); the 2 mm / 5 mm limits are project rules for '
                 'TI\'s "as close as possible"')
# converter small-signal parts: ref -> ({own pad: converter pin}, limit mm), pad centre to pin centre (make_spec SMALL_SIGNAL_ANCHORS)
CONVERTER_PARTS = {
    'C128': ({'1': 'U107.2', '2': 'U107.3'}, 2.0), 'R125': ({'1': 'U107.4'}, 5.0), 'R128': ({'2': 'U107.4'}, 5.0),
    'R124': ({'2': 'U107.4'}, 5.0), 'C129': ({'1': 'U107.4'}, 5.0), 'C127': ({'1': 'U107.14'}, 5.0),
    'R127': ({'1': 'U107.14', '2': 'U107.13'}, 5.0), 'R130': ({'1': 'U108.10'}, 5.0), 'R129': ({'2': 'U108.10'}, 5.0),
}


def converter_checks(board, spec):
    """W2 PWR-L6-SCRIPT converter-stage checks on the planned (or routed) board, MODEL geometry: rows and findings."""
    rows, findings = [], []
    pads = {(p['ref'], p['number']): p for p in board.pads}

    def row(check, ok, detail):
        rows.append({'check': check, 'ok': bool(ok), 'detail': detail, 'label': 'MODEL', 'source': SCRIPT_SOURCE})
        if not ok:
            findings.append({'check': 'converters', 'item': check, 'detail': detail})

    def pad(ref_pin):
        ref, num = ref_pin.split('.')
        return pads.get((ref, num))
    for ref, (pins, limit) in CONVERTER_PARTS.items():
        dist = {}
        for num, pin in pins.items():
            a, b = pads.get((ref, num)), pad(pin)
            dist[f'{ref}.{num}-{pin}'] = r4(math.hypot(a['x'] - b['x'], a['y'] - b['y'])) if a and b else None
        ok = all(d is not None and d <= limit + EPS for d in dist.values())
        row(f'{ref} within {limit} mm', ok, f'pad centre to pin centre {dist} (limit {limit} mm)')
    sw_vias = [v for v in board.vias if v['net'] == 'E1_SYS12_SW']
    row('no via on E1_SYS12_SW', not sw_vias, f'{len(sw_vias)} via(s) of E1_SYS12_SW')
    # the SW-CBOOT link: F.Cu copper of E1_SYS12_SW through the gap between VIN2 (pin 12) and RBOOT (pin 13), joining U107.10 to C127.2
    p12, p13 = pad('U107.12'), pad('U107.13')
    if p12 and p13:
        b12, b13 = p12['geo'].bbox, p13['geo'].bbox
        lo, hi = sorted((b13[3], b12[1])) if b13[3] <= b12[1] else sorted((b12[3], b13[1]))
        gap = (max(b12[0], b13[0]), lo, min(b12[2], b13[2]), hi)
        through = [t for t in board.tracks if t.net == 'E1_SYS12_SW' and t.layer == 'F.Cu'
                   and cb.seg_box_gap(t.shape.x1, t.shape.y1, t.shape.x2, t.shape.y2, gap) <= 0.0]
        fcu = [t for t in board.tracks if t.net == 'E1_SYS12_SW' and t.layer != 'F.Cu']
        joined = joined_on(board, 'E1_SYS12_SW', 'F.Cu', [('U107', '10'), ('C127', '2')])
        row('SW-CBOOT link on F.Cu through the VIN2-RBOOT gap', bool(through) and joined and not fcu,
            f'gap {[r4(v) for v in gap]}: {len(through)} F.Cu E1_SYS12_SW piece(s) through it; U107.10 and C127.2 joined on F.Cu: '
            f'{joined}; E1_SYS12_SW copper off F.Cu: {len(fcu)}')
    for net in ('E1_SYS12_FB', 'E1_LAB5_FB'):
        off = [t for t in board.tracks if t.net == net and t.layer != 'F.Cu'] + [v for v in board.vias if v['net'] == net]
        mine = [p for p in board.pads if p['net'] == net]
        joined = joined_on(board, net, 'F.Cu', [(p['ref'], p['number']) for p in mine])
        row(f'{net} node on F.Cu only', not off and joined, f'{len(off)} piece(s) or via(s) off F.Cu; pads {len(mine)} joined on F.Cu: {joined}')
    vout = [pad('U108.8'), pad('U108.9')]
    polys = [z for z in board.zones if z['net'] == 'E1_LAB5_RAW' and z['layers'][0] in ('In4.Cu', 'B.Cu') and z.get('outline')]
    near = {}
    for z in polys:
        poly = cb.Poly(z['outline'])
        vs = [v for v in board.vias if v['net'] == 'E1_LAB5_RAW' and poly.contains(v['x'], v['y'])]
        near[z['name']] = [sum(1 for v in vs if math.hypot(v['x'] - q['x'], v['y'] - q['y']) <= 2.0) for q in vout if q]
    ok = any(len(n) == 2 and all(k >= 1 for k in n) for n in near.values())
    row('U108 VOUT pins joined by an In4.Cu or B.Cu polygon', ok, f'E1_LAB5_RAW polygons {sorted(near)}: vias within 2 mm of VOUT1/VOUT2 {near}')
    for agnd in ('U108.6', 'U108.11'):
        a, g = pad(agnd), pad('U108.19')
        hit = [t for t in board.tracks if t.net == 'GND' and t.layer == 'F.Cu' and a and g and touches_pad(t, a) and touches_pad(t, g)]
        row(f'{agnd} AGND to PGND pin 19 under the module', bool(hit), f'{len(hit)} F.Cu GND track(s) from {agnd} to U108.19')
    cz = spec.get('converter_zones') or {}
    for zi, z in sorted((cz.get('zones') or {}).items()):
        box = tuple(z['rect'])
        own = set(z['own_nets'])
        foreign = sorted({t.net for t in board.tracks if t.layer in ('F.Cu', 'In1.Cu') and t.net not in own
                          and cb.seg_box_gap(t.shape.x1, t.shape.y1, t.shape.x2, t.shape.y2, box) <= 0.0}
                         | {v['net'] for v in board.vias if v['net'] not in own and box[0] <= v['x'] <= box[2] and box[1] <= v['y'] <= box[3]}
                         | {zz['net'] for zz in board.zones if zz['layers'][0] in ('F.Cu', 'In1.Cu') and zz['net'] not in own
                            and zz.get('outline') and bg.rects_overlap(poly_box(zz['outline']), box)})
        row(f'no foreign net on F.Cu / In1.Cu over converter zone {zi}', not foreign, f'zone {list(box)}: foreign nets {foreign}')
    in1 = [z for z in board.zones if z['layers'][0] == 'In1.Cu']
    in1_tracks = [t for t in board.tracks if t.layer == 'In1.Cu']
    row('In1.Cu solid GND plane', bool(in1) and all(z['net'] == 'GND' and z.get('plane') for z in in1) and not in1_tracks,
        f'In1.Cu zones {[(z["name"], z["net"]) for z in in1]}, tracks {len(in1_tracks)}')
    return rows, findings


def poly_box(outline):
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    return (min(xs), min(ys), max(xs), max(ys))


def touches_pad(t, p):
    s = t.shape
    x0, y0, x1, y1 = p['geo'].bbox
    return cb.seg_box_gap(s.x1, s.y1, s.x2, s.y2, (x0, y0, x1, y1)) <= s.r + EPS


def joined_on(board, net, layer, pins):
    """The pads `pins` of a net are joined by its tracks and zones on one layer (no vias), MODEL union-find."""
    items = [('t', t) for t in board.tracks if t.net == net and t.layer == layer]
    items += [('z', z) for z in board.zones if z['net'] == net and z['layers'][0] == layer and z.get('boxes')]
    pads = [p for p in board.pads if p['net'] == net and layer in p['layers']]
    n = len(items) + len(pads)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def touch(a, b):
        (ka, ia), (kb, ib) = a, b
        if ka == 't' and kb == 't':
            sa, sb = ia.shape, ib.shape
            return cb_seg_seg(sa, sb) <= sa.r + sb.r + EPS
        if ka == 'z' and kb == 'z':
            return any(bg.rects_overlap(x, y, EPS) for x in ia['boxes'] for y in ib['boxes'])
        t, z = (ia, ib) if ka == 't' else (ib, ia)
        s = t.shape
        return any(cb.seg_box_gap(s.x1, s.y1, s.x2, s.y2, x) <= s.r + EPS for x in z['boxes'])
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if touch(items[i], items[j]):
                parent[find(i)] = find(j)
        for k, p in enumerate(pads):
            kind, it = items[i]
            hit = touches_pad(it, p) if kind == 't' else any(bg.rects_overlap(x, p['geo'].bbox, EPS) for x in it['boxes'])
            if hit:
                parent[find(i)] = find(len(items) + k)
    idx = {(p['ref'], p['number']): len(items) + k for k, p in enumerate(pads)}
    roots = {find(idx[q]) for q in pins if q in idx}
    return len(roots) == 1 and all(q in idx for q in pins)


def cb_seg_seg(a, b):
    import make_board as mb
    return mb.seg_seg_dist((a.x1, a.y1), (a.x2, a.y2), (b.x1, b.y1), (b.x2, b.y2))


def audit(folder):
    folder = Path(folder).resolve()
    board_path = folder / 'PWR_A.kicad_pcb'
    spec_path = folder / 'board-spec.json' if (folder / 'board-spec.json').is_file() else BASE / 'pcb/boards/PWR_A.json'
    spec = read(spec_path)
    contract = read(CONTRACT)['boards'][spec['contract']['board']]
    pspec = read(PSPEC)
    graph = bg.load_graph()
    planned = not board_path.is_file()
    if planned:  # the generator's board spec before routing: courtyards, pads and scripted copper only
        board = SpecBoard(spec)
        frame = _Identity()
    else:
        board = cb.load_board(board_path)
        frame = cb.Frame(board, contract, spec)
    findings, unverified = [], []

    def cbox(fp):
        x0, y0, x1, y1 = fp['courtyard']
        a, b = frame.to_contract(x0, y0), frame.to_contract(x1, y1)
        return (r4(min(a[0], b[0])), r4(min(a[1], b[1])), r4(max(a[0], b[0])), r4(max(a[1], b[1])))
    fps = {fp['ref']: fp for fp in board.footprints if fp['ref']}
    zones = [(x, y, x + w, y + h) for x, y, w, h in contract['thermal_bond_mm']]
    # zones
    zone_rows = []
    regs = sorted((r for r in fps if any(k in graph.get(r, {}).get('value', '') for k in ('TPS7A4701', 'LT3045'))), key=bg.sort_ref)
    for ref in regs:
        b = cbox(fps[ref])
        ok = inside(b, zones[0]) or inside(b, zones[1])
        zone_rows.append({'ref': ref, 'part': graph[ref]['value'].split()[0], 'courtyard': list(b), 'zones': '1-2', 'ok': ok})
        if not ok:
            findings.append({'check': 'zones', 'item': ref, 'detail': 'courtyard not inside thermal_bond zone 1 or 2'})
    for z, refs in sorted(contract.get('converter_zone_refs', {}).items()):
        for ref in refs:
            b = cbox(fps[ref])
            ok = inside(b, zones[int(z) - 1])
            zone_rows.append({'ref': ref, 'part': graph[ref]['value'].split()[0], 'courtyard': list(b), 'zones': z, 'ok': ok})
            if not ok:
                findings.append({'check': 'zones', 'item': ref, 'detail': f'courtyard not inside thermal_bond zone {z}'})
    # pockets
    pockets = [(x, y, x + w, y + h) for x, y, w, h in contract['bottom_side']['keep_in_mm']]
    bottom = sorted((r for r, fp in fps.items() if fp['side'] == 'bottom'), key=bg.sort_ref)
    outside = [r for r in bottom if not any(inside(cbox(fps[r]), p) for p in pockets)]
    for r in outside:
        findings.append({'check': 'pockets', 'item': r, 'detail': 'bottom courtyard not inside one plate pocket PB1-PB13'})
    # H-TRIM
    zmax = pspec['keepouts']['h_trim']['zone_h_max_mm']
    wm = pspec['parameters']['window_margin']
    trim_rows = []
    for f in read(PWR_B_SPEC)['h_trim']['pin_fields']:
        x0, y0, x1, y1 = f['field_mm']
        zone = (x0 - wm, y0 - wm, x1 + wm, y1 + wm)
        for ref, fp in sorted(fps.items(), key=lambda kv: bg.sort_ref(kv[0])):
            if fp['side'] != 'top' or not fp['courtyard'] or not overlap(cbox(fp), zone):
                continue
            h = spec.get('heights', {}).get(ref)
            ok = h is not None and h <= zmax + EPS
            trim_rows.append({'ref': ref, 'under': f['ref'], 'h_mm': h, 'ok': ok if h is not None else None})
            if h is None:
                unverified.append({'check': 'h_trim', 'item': ref, 'reason': f'under the {f["ref"]} pin field; height not read'})
            elif not ok:
                findings.append({'check': 'h_trim', 'item': ref, 'detail': f'{h} mm under the PWR-B {f["ref"]} pin field '
                                 f'(H-TRIM zone height {zmax} mm)'})
    # holes
    holes = [h for h in board.holes if h['ref'] and h['ref'].startswith('H')]
    netted = [h['ref'] for h in holes if h['net']]
    if len(holes) != len(contract['holes_mm']) or netted:
        findings.append({'check': 'holes', 'item': ','.join(netted) or 'count',
                         'detail': f'{len(holes)} mounting holes, netted {netted}; contract has {len(contract["holes_mm"])}'})
    # cell
    cell = sorted({it.net for it in board.copper if it.net in ('E1_CELL0', 'B-')})
    if cell:
        findings.append({'check': 'cell', 'item': ','.join(cell), 'detail': 'battery-side copper on PWR-A: check PWR-02 clearance'})
    # copper (MODEL)
    nc = read(NETCLASSES)
    layers = {l.get('kicad'): l for l in nc['stackup']['layers'] if l.get('kicad')}
    t_outer, thick, plating = layers['F.Cu']['copper_mm'], nc['stackup']['board_thickness_mm'], nc['formulas']['via']['plating_mm']
    option = spec['layers'].get('copper_option')
    if option:  # W2 PWRJ-LAYERS6: the outer copper of the spec's copper option (pcb/generated/stackup-6l.json; outer_2oz 0.070 mm)
        t_outer = read(BASE / 'pcb/generated/stackup-6l.json')['copper_options'][option]['outer_copper_mm']
    lab5 = read(LAB5)
    contacts = lab5['constants']['b2b_lab5_contacts_pwr_a']

    def component(network, start):
        """The part of a network that the start key reaches (other islands of the net make the solve singular)."""
        adj = {}
        for a, b, _ohm in network.edges:
            ra, rb = network.find(a), network.find(b)
            adj.setdefault(ra, set()).add(rb)
            adj.setdefault(rb, set()).add(ra)
        root = network.find(start)
        seen, todo = {root}, [root]
        while todo:
            for y in adj.get(todo.pop(), ()):
                if y not in seen:
                    seen.add(y)
                    todo.append(y)
        sub = lb.Net()
        for k in network.parent:
            if network.find(k) in seen:
                sub.join(k, network.find(k))
        for a, b, ohm in network.edges:
            if network.find(a) in seen:
                sub.res(a, b, ohm)
        return sub, seen

    def resistance(net, sources, sinks):
        rows = {}
        for tk, tc in (('20C', 20.0), ('50C', 50.0)):
            network, info = lb.pwr_b_network(board, tc, t_outer, plating, thick, net_name=net, t_inner=t_inner, zone_joints=zj)
            try:
                src = [('pad', r, n) for r, n in sources]
                sub, seen = component(network, src[0])
                reach = [('pad', r2, n2) for r2, n2 in sinks if network.find(('pad', r2, n2)) in seen]
                if not reach or any(network.find(s) not in seen for s in src):
                    raise KeyError('not joined')
                rows[tk] = r4(min(sub.resistance(src, k) for k in reach) * 1e3)
            except (SystemExit, ZeroDivisionError, KeyError):
                rows[tk] = None
        return {'net': net, 'from': [f'{r}.{n}' for r, n in sources], 'to': [f'{r}.{n}' for r, n in sinks],
                'mohm': rows, 'joined': rows['20C'] is not None, 'network': info}
    vout = sorted(str(p['number']) for p in graph['U108']['pins'] if str(p.get('name', '')).startswith('VOUT'))
    zj = planned  # W2 PWR-L6-SCRIPT: on the planned board the pin-entry pours are ideal joints (lab5_budget.pwr_b_network)
    t_inner = read(BASE / 'pcb/generated/stackup-6l.json')['copper_options'][option]['inner_copper_mm'] if option else None
    copper = {
        'A_L101_to_L205': resistance('LAB5', [('L101', '2')], [('L205', '1')]),
        'B_L101_to_J208': resistance('LAB5', [('L101', '2')], [('J208', c) for c in contacts]),
        'raw_U108_to_F102': resistance('E1_LAB5_RAW', [('U108', n) for n in vout], [('F102', '1')]),
        'fused_F102_to_L101': resistance('E1_LAB5_FUSED', [('F102', '2')], [('L101', '1')]),
    }
    b2b_delta = r4(lb.B2B_DELTA / len(contacts) * 1e3)
    pwr_b = {r['pad']: r['resistance_mohm'] for r in lab5['pwr_b_copper']['by_temperature']['20C']
             if r['pad'] in lab5['pwr_b_copper']['e2_loads']}
    b_rows = {}
    if copper['B_L101_to_J208']['joined']:
        for pad, mohm in sorted(pwr_b.items()):
            total = r4(copper['B_L101_to_J208']['mohm']['20C'] + b2b_delta + mohm)
            b_rows[pad] = {'pwr_a_mohm': copper['B_L101_to_J208']['mohm']['20C'], 'b2b_delta_max_mohm': b2b_delta,
                           'pwr_b_mohm': mohm, 'total_mohm': total, 'within_10_mohm': total <= 10.0}
    copper['B_total_20C'] = b_rows
    # E1-05 (W2 PWR-L6-SCRIPT, synthesis e105_decision; MODEL, 20 degC): path A against 10 mOhm, path B per destination against 32 mV
    pbw = lab5.get('path_b_current_weighted') or {}
    a20 = copper['A_L101_to_L205']['mohm']['20C']
    e105 = {'label': 'MODEL: copper of the drawn (planned or routed) board, IACS copper at 20 degC; E1-05 and its bench stay OPEN',
            'A': {'what': 'L101.2 -> L205.1 (the LT3045 pair feed)', 'mohm_20c': a20, 'limit_mohm': lb.BUDGET * 1e3,
                  'met': a20 is not None and a20 <= lb.BUDGET * 1e3 + EPS}}
    if pbw and copper['B_L101_to_J208']['joined']:
        i_tot = pbw['total_current_a']
        pa_mv = r4(copper['B_L101_to_J208']['mohm']['20C'] * i_tot)
        rows_b = {}
        for d in pbw['destinations']:
            pb_mv = pbw['pwr_b_drop_mv']['20C'][d['pad']]
            total = r4(pa_mv + pbw['b2b']['drop_mv_max'] + pb_mv)
            rows_b[d['pad']] = {'current_a': d['current_a'], 'pwr_a_mv': pa_mv, 'b2b_mv_max': pbw['b2b']['drop_mv_max'],
                                'pwr_b_mv': pb_mv, 'total_mv': total, 'limit_mv': pbw['drop_budget_mv'],
                                'met': total <= pbw['drop_budget_mv'] + EPS}
        e105['B'] = {'what': 'L101.2 -> J208 / J209 -> each TPS2553 input on PWR-B at the worst-case concurrent currents (NET_CURRENT '
                             'protective column), segment by segment',
                     'total_current_a': i_tot, 'pwr_a_mohm_20c': copper['B_L101_to_J208']['mohm']['20C'], 'per_destination': rows_b,
                     'met': all(r['met'] for r in rows_b.values()),
                     'b2b_initial_resistance': 'TBD (the Samtec specification states only the delta)'}
    else:
        e105['B'] = {'joined': copper['B_L101_to_J208']['joined'], 'met': None}
    conv_rows, conv_findings = converter_checks(board, spec) if spec.get('converter_zones') else ([], [])
    findings += conv_findings
    class_doc = None
    if planned:  # W2 PWR-L6-SCRIPT: pcb/check_boards.py check_classes on the scripted copper (2 oz widths, exemption policy)
        nspec = cb.normalize_spec(spec)
        ncls = cb.board_netclasses(read(NETCLASSES), nspec)
        views = cb.expected_views(nspec, graph)
        cw_f, cw_u, cw_i = cb.check_classes(board, nspec, ncls, views, graph)
        class_doc = {'label': 'MODEL: pcb/check_boards.py check_classes on the planned board (pads as copper boxes, pours filled to '
                              'their outlines)', 'findings': cw_f, 'tracks_checked': cw_i['tracks_checked'],
                     'exemption_policy': cw_i.get('exemption_policy'), 'branch_rows': len(spec.get('branch_exempt', {})),
                     'neck_rows': len(spec.get('neck_exempt', {})),
                     'widths_mm': {c: ncls['classes'][c]['outer_min_width_mm'] for c in ('BATT', 'PWR3A', 'PWR2A', 'PWR1A')}}
        findings += [{'check': 'class_widths', 'item': f['item'], 'detail': f['detail']} for f in cw_f]
    # fill (MODEL, courtyards)
    usable = contract['area_mm2'] - len(contract['holes_mm']) * math.pi * (contract['hole_keepout_d'] / 2) ** 2
    top = [fp for fp in fps.values() if fp['side'] == 'top' and fp['courtyard'] and not fp['ref'].startswith('H')]
    demand = sum((fp['courtyard'][2] - fp['courtyard'][0]) * (fp['courtyard'][3] - fp['courtyard'][1]) for fp in top)
    report = read(folder / 'report.json') if (folder / 'report.json').is_file() else {}
    return {
        'schema': 'srrx-pwra-board-audit-v1',
        'board_id': 'PWR_A',
        'status': 'MODEL/CI: audits of the drawn board (pure-Python reader); not a fabrication release; bench gates OPEN',
        'generator': 'build/kicad/boards/PWR_A/board_audit.py',
        'board': 'planned (no routed board in this folder): courtyards, pads and the scripted locked copper of the spec'
                 if planned else 'routed board PWR_A.kicad_pcb of this folder',
        'inputs': {'board_sha256': None if planned else bg.sha256_file(board_path), 'spec': spec_path.relative_to(BASE).as_posix(),
                   'spec_sha256': bg.sha256_file(spec_path), 'pwr_b_h_trim_sha256': bg.sha256_bytes(bg.canonical(read(PWR_B_SPEC)['h_trim'])),
                   'lab5_budget_sha256': bg.sha256_file(LAB5)},
        'drc': report.get('result'),
        'zones': zone_rows,
        'pockets': {'bottom_refs': len(bottom), 'outside_a_pocket': outside},
        'h_trim': {'zone_h_max_mm': zmax, 'parts_under': trim_rows},
        'holes': {'mounting_holes': len(holes), 'netted': netted},
        'cell_nets_on_board': cell,
        'copper': copper,
        'e1_05': e105,
        'converters': {'rows': conv_rows, 'source': SCRIPT_SOURCE} if conv_rows else None,
        'class_widths': class_doc,
        'fill': {'label': 'MODEL: KiCad courtyard boxes of the top footprints over the outline less the 7 hole keep-outs',
                 'top_courtyards_mm2': r4(demand), 'usable_mm2': r4(usable), 'fill': r4(demand / usable)},
        'findings': findings,
        'unverified': unverified,
        'result': 'NO_FINDINGS' if not findings else 'FINDINGS',
    }


def review(folder):
    """pcb/check_boards.py review of the board in a record folder (as check_boards --board PWR_A on an installed board)."""
    folder = Path(folder).resolve()
    spec_path = folder / 'board-spec.json' if (folder / 'board-spec.json').is_file() else BASE / 'pcb/boards/PWR_A.json'
    spec = cb.normalize_spec(read(spec_path))
    board_path = folder / 'PWR_A.kicad_pcb'
    board = cb.load_board(board_path)
    mates = {}
    for pair in spec.get('b2b', []):
        mspec = cb.normalize_spec(read(BASE / 'pcb/boards' / f'{pair["mate_board"]}.json'))
        mbf = cb.board_file(mspec)
        if mbf.is_file():
            mates[pair['mate_board']] = cb.load_board(mbf)
    doc = cb.review_board(board, spec, read(cb.contract_path(spec)), cb.load_graph(), read(NETCLASSES), mates,
                          board_rel=board_path.relative_to(BASE).as_posix())
    return cb.dumps(doc), doc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dir', default=str(HERE))
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--review', action='store_true')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    status = 0
    if args.review:
        rtext, rdoc = review(args.dir)
        rout = Path(args.dir) / 'review.json'
        print(f"review: {len(rdoc['findings'])} finding(s), {len(rdoc['unverified'])} unverified")
        if args.check:
            if not rout.is_file() or rout.read_text(encoding='utf-8') != rtext:
                print(f'{rout} is stale: rerun board_audit.py --review')
                status = 1
        else:
            with open(rout, 'w', encoding='utf-8', newline='\n') as f:
                f.write(rtext)
    doc = audit(args.dir)
    text = json.dumps(doc, ensure_ascii=False, indent=2) + '\n'
    out = Path(args.dir) / 'board-audit.json'
    print(json.dumps({'result': doc['result'], 'findings': len(doc['findings']), 'unverified': len(doc['unverified']),
                      'fill': doc['fill']['fill'],
                      'copper_20C_mohm': {k: v['mohm']['20C'] for k, v in doc['copper'].items() if isinstance(v, dict) and 'mohm' in v}}))
    if args.check:
        if not out.is_file() or out.read_text(encoding='utf-8') != text:
            print(f'{out} is stale: rerun board_audit.py')
            return 1
        return status
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    return status


if __name__ == '__main__':
    sys.exit(main())
