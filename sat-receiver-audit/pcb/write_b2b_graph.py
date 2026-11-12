#!/usr/bin/env python3
"""Write the B2B contact map into the graph refs J208 (PWR-A) and J209 (PWR-B) of design/E2.json (W2 B2B). Standard library only.

Run from any directory:
  python -I pcb/write_b2b_graph.py           rewrite the pins of J208/J209 from the contact map
  python -I pcb/write_b2b_graph.py --check   compare only; exit 1 if the graph differs from the map

The map comes from pcb/prepare.py (b2b_nets -> b2b_contacts, rules in pcb/partition-spec.json b2b.pin_map_rule and
b2b.guard_rule), computed from the graphs design/E1..E5.json in the same way as prepare.py main(); this script does not read
verification/netlist.xml, so it runs before the CAD refreeze. Contact n of a half carries its net (type passive); a spare
contact is {name NC, type passive, nc true}. The refs are inserted after the last ref of the group "Роз'єми джгутів PWR" when
missing; otherwise only their pins change. JSON is written with indent 2, key order kept, ensure_ascii=False.

When a crossing net changes (a net added or removed between PWR-A and PWR-B parts), prepare.py stops with "graph pins differ
from the B2B contact map"; then run this script, tools/build_parts.py, and the chain of the shared-file protocol (refreeze,
CAD patch, build_assembly_docs, inventory, partition_budget). Design input only: no placement, no hardware result.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E2 = ROOT / 'design/E2.json'
SPEC = ROOT / 'pcb/partition-spec.json'
GROUP = "Роз'єми джгутів PWR"
SOURCE = 'pcb/generated/b2b-nets.json contacts (pcb/prepare.py b2b_contacts); pcb/partition-spec.json b2b (W2 B2B)'
VALUE = {'pwr_a': 'B2B-PWRA: Samtec LSHM-150 2×50, PWR-A верх, стик 5.00 мм',
         'pwr_b': 'B2B-PWRB: Samtec LSHM-150 2×50, PWR-B низ, стик 5.00 мм'}
NOTES = {
    'pwr_a': ["Половина стику B2B PWR-A/PWR-B (W2 B2B): Samtec LSHM-150-02.5-L-DV-A-N-K-TR на верхньому боці PWR-A, під J209. Контакт n "
              "зустрічає контакт n+1 J209 (n непарний) або n−1 (n парний): креслення Samtec Rev Z, примітка 4. Номери контактів і кола — "
              "pcb/generated/b2b-nets.json contacts; контакти без кола — резерв (nc)."],
    'pwr_b': ["Половина стику B2B PWR-A/PWR-B (W2 B2B): та сама деталь Samtec LSHM-150-02.5-L-DV-A-N-K-TR на нижньому боці PWR-B, над J208. "
              "Контакт m несе коло контакту J208, який його зустрічає (m+1 для непарного m, m−1 для парного). Номери контактів і кола — "
              "pcb/generated/b2b-nets.json contacts; контакти без кола — резерв (nc)."],
}


def load_prepare():
    spec = importlib.util.spec_from_file_location('srrx_prepare_b2b_writer', ROOT / 'pcb/prepare.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def contact_map(prep, graph_e2):
    """Contacts of b2b_nets for the graphs, with design/E2.json taken from graph_e2 (components and rows as in prepare.py main())."""
    db = prep.parts_db()
    components = []
    for i in range(1, 6):
        j = graph_e2 if i == 2 else json.loads((ROOT / f'design/E{i}.json').read_text(encoding='utf-8'))
        flags = frozenset(f['net'] for f in j.get('power_flags', []))
        for c in j['components']:
            components.append({**c, '_sheet': f'E{i}', '_mount': db[c['ref']]['mount'] if c['ref'] in db else None, '_flags': flags})
    rows = []
    for c in components:
        cat = prep.category(c)[0]
        rows.append({'ref': c['ref'], 'category': cat, 'board_candidate': prep.board(c, cat), 'dnp': bool(c.get('dnp', False))})
    return prep.b2b_nets(components, rows, prep.net_currents())


def pins(contacts, half):
    out = []
    for c in sorted(contacts, key=lambda c: int(c[half + '_pin'])):
        if c['net']:
            out.append({'number': c[half + '_pin'], 'name': c['net'], 'type': 'passive', 'net': c['net']})
        else:
            out.append({'number': c[half + '_pin'], 'name': 'NC', 'type': 'passive', 'nc': True})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='compare only; exit 1 if J208/J209 differ from the contact map')
    args = ap.parse_args()
    prep = load_prepare()
    text = E2.read_text(encoding='utf-8')
    graph = json.loads(text)
    b2b = json.loads(SPEC.read_text(encoding='utf-8'))['b2b']
    halves, n_all = b2b['graph_refs'], b2b['contacts']
    res = contact_map(prep, graph)
    contacts = res['contacts']
    if len(contacts) != n_all:
        raise SystemExit(f'write_b2b_graph: {len(contacts)} contacts in the map, b2b.contacts is {n_all}')
    if not res['totals']['contacts_needed'] <= n_all:
        raise SystemExit(f"write_b2b_graph: the map needs {res['totals']['contacts_needed']} contacts, more than {n_all}")
    comps = graph['components']
    for half in ('pwr_a', 'pwr_b'):
        ref = halves[half]
        refs = [c['ref'] for c in comps]
        if ref in refs:
            comps[refs.index(ref)]['pins'] = pins(contacts, half)
            continue
        at = max(i for i, c in enumerate(comps) if c.get('group') == GROUP) + 1
        comps.insert(at, {'ref': ref, 'value': VALUE[half], 'kind': 'connector', 'group': GROUP, 'source': SOURCE,
                          'status': 'design', 'pins': pins(contacts, half), 'notes': NOTES[half]})
    new = json.dumps(graph, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if new != text:
            raise SystemExit(f"write_b2b_graph: {halves['pwr_a']}/{halves['pwr_b']} in design/E2.json differ from the B2B contact map; "
                             'run python -I pcb/write_b2b_graph.py')
        print(f"write_b2b_graph: {halves['pwr_a']}/{halves['pwr_b']} carry the contact map ({res['totals']['contacts_needed']} of {n_all} "
              'contacts used)')
        return
    E2.write_text(new, encoding='utf-8', newline='\n')
    left = [e for e in contact_map(prep, graph)['errors'] if 'graph pins differ' in e]
    if left:
        raise SystemExit('write_b2b_graph: the map still differs after the write: ' + '; '.join(left))
    print(f"write_b2b_graph: wrote {halves['pwr_a']}/{halves['pwr_b']} into design/E2.json; totals {res['totals']}")


if __name__ == '__main__':
    main()
