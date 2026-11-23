#!/usr/bin/env python3
"""Which committed boards need a route run after a graph change (W2 CTRL-6, review RV-CTRL6-S2-1). Standard library, read-only.

`board_gen.py --board B --inputs-only` hashes the spec, contract, project rules, template and the board's own instances; it does
not hash the boundary audit of report.json (external_refs, status, board_pads and external_sample of every boundary net), so a
board whose only change is a new GND or LAB5 reference on another board looks current there, while the check mode of sr-rx-pcb
then fails on its stale report.json. This tool compares, for every board with a spec in pcb/boards/ (or the --board list):
  (a) the committed build/kicad/boards/<B>/report.json audits.boundary with board_gen.boundary_audit() of the current graph,
      per (instance, net) on every field, and the instance status;
  (b) the committed inputs projection (report.json inputs.parts) with board_gen.projection() of the current tree (stale parts);
  (c) board_gen.domain_audit() of the current partition (it must pass).
A board for which any of them fails goes into the batched route push ('[pcb-route <B>]').
Output: one line per board (or JSON with --json). Exit 0 when every board is current, 1 when a board needs a route run.
usage: python pcb/boundary_stale.py [--board B ...] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import board_gen as bg  # noqa: E402


def boundary_key(audit):
    """{(instance, net): canonical net record} plus {(instance, None): instance status}."""
    out = {}
    for inst in audit:
        out[(inst['instance'], None)] = inst.get('status')
        for n in inst['nets']:
            out[(inst['instance'], n['net'])] = json.dumps(n, sort_keys=True, ensure_ascii=False)
    return out


def check(board):
    spec, contract, stackup, graph, db, template, project, proj = bg.prepare_inputs(board)
    rep = bg.OUT_ROOT / board / 'report.json'
    res = {'board': board, 'reasons': []}
    partition = bg.read_json(bg.BASE / spec['partition'])
    if not bg.domain_audit(spec, partition)['passed']:
        res['reasons'].append('domain_audit false')
    if not rep.is_file():
        res['reasons'].append('no committed report.json')
        return res
    report = bg.read_json(rep)
    stale = sorted(k for k in proj['parts'] if report['inputs']['parts'].get(k) != proj['parts'][k])
    if stale or report['inputs']['sha256'] != proj['sha256']:
        res['reasons'].append('inputs: ' + (', '.join(stale) or 'sha256'))
    cur = boundary_key(bg.boundary_audit(spec, template, graph, db))
    com = boundary_key(report['audits']['boundary'])
    diff = []
    for k in sorted(set(cur) | set(com), key=lambda t: (t[0], t[1] or '')):
        if cur.get(k) == com.get(k):
            continue
        if k[1] is None:
            diff.append(f'{k[0]}: status {com.get(k)} -> {cur.get(k)}')
            continue
        a = json.loads(com[k]) if k in com else {}
        b = json.loads(cur[k]) if k in cur else {}
        fields = sorted(f for f in set(a) | set(b) if a.get(f) != b.get(f))
        what = []
        for f in fields:
            what.append(f'{f} {a.get(f)} -> {b.get(f)}' if f in ('external_refs', 'status') else f)
        diff.append(f'{k[0]}/{k[1]}: ' + '; '.join(what))
    if diff:
        res['reasons'].append('boundary: ' + ' | '.join(diff))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--board', action='append', help='board id (default: every spec in pcb/boards/)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    boards = a.board or sorted(p.stem for p in (bg.BASE / 'pcb/boards').glob('*.json'))
    results = [check(b) for b in boards]
    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"{r['board']}: {'ROUTE AGAIN - ' + ' || '.join(r['reasons']) if r['reasons'] else 'current'}")
    return 1 if any(r['reasons'] for r in results) else 0


if __name__ == '__main__':
    sys.exit(main())
