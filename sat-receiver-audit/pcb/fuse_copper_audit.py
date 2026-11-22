#!/usr/bin/env python3
"""Fuse-current copper audit of the committed boards (W2 CTRL-6, build/15 "Правило струму запобіжника для міді"). Standard library.

The rule (MODEL, IPC-2221 as pcb/stackup.py): copper on a loop that a fuse protects must
  (1) meet the project rule of +20 degC at 110 % of the fuse rating, the current a fuse passes indefinitely (Littelfuse MINI:
      110 % for at least 360000 s), and
  (2) at 135 % of the rating, which the fuse may pass up to its clearing time (MINI: 0.75-600 s, thermal steady state for board
      copper), stay below the laminate limit with margin at 70 degC ambient: rise <= Tg 130 degC (JLCPCB standard FR-4,
      https://jlcpcb.com/help/article/jlcpcb-base-material, read 2026-11-22) - 20 degC margin - 70 degC = +40 degC.
Because the IPC-2221 current goes with dT^0.44, (1) implies (2) for the same copper ((40/20)^0.44 = 1.357 > 1.35/1.1 = 1.227); the
audit checks both anyway.

Nets: every net of pcb/generated/netclasses.json whose protection names a fuse (F1xx/F2xx with an "N A" rating, not a PTC, eFuse
or TPS2553 limit), and every series-derived net reached through such a fuse. Per board (build/kicad/boards/<B>/<B>.kicad_pcb):
  * each track segment of such a net: IPC-2221 rise at 110 % and 135 % for its width and layer copper (outer k 0.048, inner k 0.024);
    the copper of each board is its own (review RV-CTRL6-S-2): report.json layers.copper_option 'outer_2oz' takes the outer and
    inner foil of pcb/generated/stackup-6l.json copper_options (0.070 / 0.0152 mm; without that file 0.070 mm outer and the
    project's 0.0152 mm finished 0.5 oz inner), a 6-layer board without an option takes the stackup-6l.json layers, any other
    board the stackup of netclasses.json (0.035 / 0.0152 mm); the basis is written per board (copper_basis);
    a segment wholly inside a filled zone of its own net on its layer is reported as covered (the pour carries it) and a segment
    shorter than --short mm (default 1.0, pad entries) is listed apart: the long-trace formula does not apply to them;
  * a pad stub of a multi-contact connector (a J* footprint with k >= 2 pads on the net; the chain of segments from the pad up
    to the first junction, via or other pad) carries the even share 1/k of the loop current (parallel contacts, MODEL) and is
    listed apart under connector_stubs with its share and rise; it counts as failing only if it fails at its share
    (review RV-CTRL6-S-2);
  * vias of the net grouped by proximity (3 mm): the group carries the full current with an even share as a lower bound of the
    hottest via (the CTRL clusters and ladders have their own DC share models in pcb/tests); rise of one via by the project fit
    (netclasses.json formulas.via, 1.001 A at +20 degC).
Output: JSON (stdout, or --out FILE) with every finding; exit 0 always (an audit for build/15, not a gate). CI/model only.
usage: python pcb/fuse_copper_audit.py [--board B ...] [--out FILE] [--short MM]
"""
from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path
import re
import sys

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'pcb'))
import check_boards as cb  # noqa: E402

TG_C, MARGIN_C, AMBIENT_C = 130.0, 20.0, 70.0
DT_110, DT_135 = 20.0, TG_C - MARGIN_C - AMBIENT_C
FUSE = re.compile(r'\b(F[12]\d{2})\b[^;]*?(\d+(?:\.\d+)?)\s*A(?![a-zA-Z])')


def fuse_of(entry, ptcs):
    """(fuse ref, rating A) of a netclasses.json net entry, or None for PTC/eFuse/limiter protection (a PTC ref of the graph,
    MPN MF-..., does not count as a fuse)."""
    text = entry['inputs'].get('protection') or entry['inputs'].get('via') or ''
    if not text or re.match(r'\s*(PTC|eFuse|U\d)', text):
        return None
    m = FUSE.search(text)
    if not m or m.group(1) in ptcs:
        return None
    return m.group(1), float(m.group(2))


def rise(amps, width_mm, copper_mm, k):
    area = (width_mm / 0.0254) * (copper_mm / 0.0254)
    return (amps / (k * area ** 0.725)) ** (1 / 0.44)


def board_copper(board, b, nc):
    """(layer -> finished copper mm, basis text) of one board (review RV-CTRL6-S-2)."""
    rep = BASE / f'build/kicad/boards/{board}/report.json'
    option = (json.loads(rep.read_text(encoding='utf-8')).get('layers') or {}).get('copper_option') if rep.is_file() else None
    six = BASE / 'pcb/generated/stackup-6l.json'
    six_doc = json.loads(six.read_text(encoding='utf-8')) if six.is_file() else None
    if option == 'outer_2oz':
        opt = ((six_doc or {}).get('copper_options') or {}).get('outer_2oz') or {}
        outer, inner = float(opt.get('outer_copper_mm', 0.070)), float(opt.get('inner_copper_mm', 0.0152))
        src = ('pcb/generated/stackup-6l.json copper_options.outer_2oz' if opt
               else 'no stackup-6l.json: 2 oz 0.070 mm outer, 0.0152 mm inner')
        return {l: (outer if l in ('F.Cu', 'B.Cu') else inner) for l in b.copper_layers}, f'report.json copper_option outer_2oz; {src}'
    copper = {l['kicad']: l['copper_mm'] for l in nc['stackup']['layers'] if 'kicad' in l}
    if not set(b.copper_layers) - set(copper):
        return copper, f'pcb/generated/netclasses.json stackup {nc["stackup"].get("id")}'
    if six_doc:
        copper = {l['kicad']: l['copper_mm'] for l in six_doc['stackup']['layers'] if 'kicad' in l}
        if not set(b.copper_layers) - set(copper):
            return copper, f'pcb/generated/stackup-6l.json stackup {six_doc["stackup"].get("id")}'
    return ({l: (0.035 if l in ('F.Cu', 'B.Cu') else 0.0152) for l in b.copper_layers},
            'no stackup for these layers: outer 1 oz 0.035 mm, inner 0.0152 mm assumed')


def connector_stubs(b, net, tracks):
    """{track index: (share 1/k, 'J.pad')} for the pad stubs of multi-contact connectors on this net (review RV-CTRL6-S-2).

    A stub starts at a J* pad of a footprint with k >= 2 pads on the net that has exactly one track of the net attached and no
    via in it, and follows single segments of that layer until a via or a junction of three or more track ends; that chain
    carries only its own contact's share. A chain that runs into another pad (a part, or another contact) or ends open is not a
    stub, and a pad where two or more tracks meet is a merge point: those keep the full loop current (conservative)."""
    def key(x, y):
        return (round(x, 4), round(y, 4))
    ends = collections.defaultdict(list)
    for i, t in enumerate(tracks):
        ends[(t.layer,) + key(t.shape.x1, t.shape.y1)].append(i)
        ends[(t.layer,) + key(t.shape.x2, t.shape.y2)].append(i)
    vias = [(v['x'], v['y'], v['size'] / 2) for v in b.vias if v['net'] == net]
    pads = [p for p in b.pads if p['net'] == net]

    def via_at(x, y):
        return any(math.hypot(x - vx, y - vy) <= r + 1e-6 for vx, vy, r in vias)

    def pad_at(layer, x, y, own):
        return any(p is not own and layer in p['layers'] and p['geo'].contains(x, y) for p in pads)
    out = {}
    for fp in b.footprints:
        if not re.fullmatch(r'J\d+', fp['ref'] or ''):
            continue
        mine = [p for p in fp['pads'] if p['net'] == net]
        k = len({p['number'] for p in mine})
        if k < 2:
            continue
        for p in mine:
            attached = []
            for i, t in enumerate(tracks):
                s = t.shape
                if t.layer in p['layers']:
                    for (ax, ay), (bx, by) in (((s.x1, s.y1), (s.x2, s.y2)), ((s.x2, s.y2), (s.x1, s.y1))):
                        if p['geo'].contains(ax, ay):
                            attached.append((i, (bx, by)))
                            break
            if len(attached) != 1 or any(p['geo'].contains(vx, vy) for vx, vy, _r in vias):
                continue
            cur, far = attached[0]
            chain, stub = [cur], False
            while True:
                lay = tracks[cur].layer
                if via_at(*far):
                    stub = True
                    break
                if pad_at(lay, far[0], far[1], p) or p['geo'].contains(*far):
                    break
                nxt = [j for j in ends[(lay,) + key(*far)] if j != cur]
                if len(nxt) >= 2:
                    stub = True
                    break
                if len(nxt) != 1 or nxt[0] in chain:
                    break
                cur = nxt[0]
                chain.append(cur)
                s2 = tracks[cur].shape
                far = (s2.x2, s2.y2) if key(s2.x1, s2.y1) == key(*far) else (s2.x1, s2.y1)
            if stub:
                for i in chain:
                    out[i] = (1.0 / k, f'{fp["ref"]}.{p["number"]}')
    return out


def audit(board, nc, nets, short_mm):
    path = BASE / f'build/kicad/boards/{board}/{board}.kicad_pcb'
    if not path.is_file():
        return {'board': board, 'status': 'no committed board'}
    b = cb.load_board(path)
    copper, basis = board_copper(board, b, nc)
    ipc = nc['formulas']['ipc2221']
    fit = nc['formulas']['via']['current_a_dt20']
    zones = collections.defaultdict(list)
    for z in b.zones:
        if not z['keepout']:
            for lay, polys in z['fills'].items():
                zones[(z['net'], lay)].extend(polys)
    out = {'board': board, 'copper_basis': basis, 'copper_mm': {l: copper[l] for l in b.copper_layers}, 'nets': []}
    present = {t.net for t in b.tracks} | {v['net'] for v in b.vias}
    for net, (fuse, rating) in sorted(nets.items()):
        if net not in present:
            continue
        i110, i135 = 1.1 * rating, 1.35 * rating
        rec = {'net': net, 'fuse': fuse, 'rating_a': rating, 'i110_a': round(i110, 3), 'i135_a': round(i135, 3),
               'fail_110': [], 'fail_135': [], 'short_pieces': [], 'connector_stubs': [], 'covered_by_pour': 0, 'segments': 0,
               'via_groups': []}
        tracks = [t for t in b.tracks if t.net == net]
        stubs = connector_stubs(b, net, tracks)
        for idx, t in enumerate(tracks):
            s = t.shape
            ln = math.hypot(s.x2 - s.x1, s.y2 - s.y1)
            rec['segments'] += 1
            inner = t.layer not in ('F.Cu', 'B.Cu')
            k = ipc['k_internal'] if inner else ipc['k_external']
            if any(p.contains(s.x1, s.y1) and p.contains(s.x2, s.y2) for p in zones[(net, t.layer)]):
                rec['covered_by_pour'] += 1
                continue
            item = {'layer': t.layer, 'width_mm': t.width, 'length_mm': round(ln, 3),
                    'at': [round(s.x1 - 100, 3), round(244 - s.y1, 3)]}
            if ln < short_mm:
                rec['short_pieces'].append(item)
                continue
            share = stubs.get(idx, (1.0, None))
            r110, r135 = rise(i110 * share[0], t.width, copper[t.layer], k), rise(i135 * share[0], t.width, copper[t.layer], k)
            if share[1]:
                rec['connector_stubs'].append(dict(item, pad=share[1], share=round(share[0], 4), rise_110_c=round(r110, 1),
                                                   rise_135_c=round(r135, 1)))
            if r110 > DT_110:
                rec['fail_110'].append(dict(item, rise_c=round(r110, 1)))
            if r135 > DT_135:
                rec['fail_135'].append(dict(item, rise_c=round(r135, 1)))
        pts = [(v['x'], v['y']) for v in b.vias if v['net'] == net]
        groups = []
        for p in pts:
            near = [g for g in groups if any(math.dist(p, q) <= 3.0 for q in g)]
            groups = [g for g in groups if g not in near] + [[p] + [q for g in near for q in g]]
        for g in groups:
            share = i110 / len(g)
            rec['via_groups'].append({'n': len(g), 'at': [round(g[0][0] - 100, 2), round(244 - g[0][1], 2)],
                                      'even_share_110_a': round(share, 3), 'rise_110_c': round(20 * (share / fit) ** (1 / 0.44), 1),
                                      'rise_135_c': round(20 * (i135 / len(g) / fit) ** (1 / 0.44), 1)})
        rec['worst_110_mm'] = sorted(rec['fail_110'], key=lambda x: -x['rise_c'])[:5]
        rec['n_fail_110'], rec['n_fail_135'] = len(rec['fail_110']), len(rec['fail_135'])
        rec['len_fail_110_mm'] = round(sum(x['length_mm'] for x in rec['fail_110']), 2)
        rec['via_groups_over_fit_110'] = [g for g in rec['via_groups'] if g['rise_110_c'] > DT_110]
        rec['fail_110_all'] = sorted(rec['fail_110'], key=lambda x: -x['rise_c'])
        del rec['fail_110'], rec['fail_135']
        out['nets'].append(rec)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', action='append', default=[])
    ap.add_argument('--out')
    ap.add_argument('--short', type=float, default=1.0)
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    nc = json.loads((BASE / 'pcb/generated/netclasses.json').read_text(encoding='utf-8'))
    ptcs = {ref for ref, c in cb.load_graph().items() if str(c.get('mpn', '')).startswith('MF-')}
    nets = {n: f for n, e in nc['nets'].items() if (f := fuse_of(e, ptcs))}
    boards = args.board or sorted(p.stem for p in (BASE / 'pcb/boards').glob('*.json'))
    doc = {'rule': {'dt_110_c': DT_110, 'dt_135_c': DT_135, 'tg_c': TG_C, 'margin_c': MARGIN_C, 'ambient_c': AMBIENT_C,
                    'tg_source': 'https://jlcpcb.com/help/article/jlcpcb-base-material (read 2026-11-22): standard FR-4 TG130',
                    'label': 'MODEL (IPC-2221 curve fit); not a hardware PASS'},
           'fuse_nets': {n: {'fuse': f, 'rating_a': r} for n, (f, r) in sorted(nets.items())},
           'boards': [audit(b, nc, nets, args.short) for b in boards]}
    text = json.dumps(doc, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text + '\n', encoding='utf-8', newline='\n')
    else:
        print(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
