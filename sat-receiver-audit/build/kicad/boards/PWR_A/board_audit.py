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
    scripted tracks and vias)."""

    def __init__(self, spec):
        import make_board as mb
        inp = mb.Inputs(spec)
        self.footprints, self.pads, self.tracks, self.vias, self.zones, self.copper = [], [], [], [], [], []
        for ref, pa in inp.parts.items():
            pads = []
            for q in pa.pads:
                layers = ['F.Cu', 'B.Cu'] if q['type'] in ('thru_hole', 'np_thru_hole') else [f'{pa.side}.Cu']
                rec = {'ref': ref, 'number': q['number'], 'kind': q['type'], 'net': q['net'], 'layers': layers,
                       'geo': _Box(q['box']), 'x': q['at'][0], 'y': q['at'][1]}
                pads.append(rec)
                self.pads.append(rec)
            self.footprints.append({'ref': ref, 'side': 'top' if pa.side == 'F' else 'bottom', 'courtyard': tuple(pa.box),
                                    'pads': pads})
        for t in spec['pre_route']['tracks']:
            for a, b in zip(t['path'], t['path'][1:]):
                it = cb.Item('track', t['net'], t['layer'], cb.Capsule(a[0], a[1], b[0], b[1], t['width_mm'] / 2))
                it.width = t['width_mm']
                self.tracks.append(it)
                self.copper.append(it)
        for v in spec['pre_route']['vias']:
            self.vias.append({'x': v['at'][0], 'y': v['at'][1], 'size': v['diameter_mm'], 'drill': v['drill_mm'],
                              'net': v['net'], 'layers': ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']})
        self.holes = [{'ref': f'H{k + 1}', 'net': None} for k in range(len(read(CONTRACT)['boards'][spec['contract']['board']]['holes_mm']))]


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
    pockets = [(x, y, x + w, y + h) for x, y, w, h in (contract.get('bottom_side') or {}).get('keep_in_mm', [])]  # F2ENV: single-sided
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
            network, info = lb.pwr_b_network(board, tc, t_outer, plating, thick, net_name=net)
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
