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
  * each track segment of such a net: IPC-2221 rise at 110 % and 135 % for its width and layer copper (outer k 0.048, inner k 0.024;
    stackup copper of netclasses.json); a segment wholly inside a filled zone of its own net on its layer is reported as covered
    (the pour carries it) and a segment shorter than --short mm (default 1.0, pad entries) is listed apart: the long-trace formula
    does not apply to them;
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


def audit(board, nc, nets, short_mm):
    path = BASE / f'build/kicad/boards/{board}/{board}.kicad_pcb'
    if not path.is_file():
        return {'board': board, 'status': 'no committed board'}
    b = cb.load_board(path)
    copper = {l['kicad']: l['copper_mm'] for l in nc['stackup']['layers'] if 'kicad' in l}
    if set(b.copper_layers) - set(copper):  # a board with another stack (6 layers): outer 1 oz, inner 0.5 oz like the project
        copper = {l: (0.035 if l in ('F.Cu', 'B.Cu') else 0.0152) for l in b.copper_layers}
    ipc = nc['formulas']['ipc2221']
    fit = nc['formulas']['via']['current_a_dt20']
    zones = collections.defaultdict(list)
    for z in b.zones:
        if not z['keepout']:
            for lay, polys in z['fills'].items():
                zones[(z['net'], lay)].extend(polys)
    out = {'board': board, 'nets': []}
    present = {t.net for t in b.tracks} | {v['net'] for v in b.vias}
    for net, (fuse, rating) in sorted(nets.items()):
        if net not in present:
            continue
        i110, i135 = 1.1 * rating, 1.35 * rating
        rec = {'net': net, 'fuse': fuse, 'rating_a': rating, 'i110_a': round(i110, 3), 'i135_a': round(i135, 3),
               'fail_110': [], 'fail_135': [], 'short_pieces': [], 'covered_by_pour': 0, 'segments': 0, 'via_groups': []}
        for t in b.tracks:
            if t.net != net:
                continue
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
            r110, r135 = rise(i110, t.width, copper[t.layer], k), rise(i135, t.width, copper[t.layer], k)
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
