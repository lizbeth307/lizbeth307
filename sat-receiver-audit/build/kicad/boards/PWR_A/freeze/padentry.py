#!/usr/bin/env python3
"""Open-connection classification of a PWR_A route run (W2 PWR-TOOLS). MODEL diagnostic: standard library, offline, not run by CI.

  python build/kicad/boards/PWR_A/freeze/padentry.py <drc.json of a run> [<board-spec.json of that run>] [--json OUT]

From the W2 PWRJ F2C scratch tool padentry.py (paths made relative to this file, the board's own class widths). For every
unconnected item of the KiCad DRC of a route run it asks whether one of its pad ends has a copper pad whose short side is
narrower than the outer class width of its net (pad entry: a class-width track cannot enter that pad, so the link needs a
pad-width neck (freeze/fin.py neck_link) or scripted pin-group copper) or not (an island gap or a long net). The widths
are the board's: pcb/generated/netclasses.json with the 2 oz copper option of make_board.py (with_copper_option, as
pcb/check_boards.py board_netclasses applies them). The board spec defaults to build/kicad/boards/PWR_A/board-spec.json; pass
the board-spec.json of a record folder (route-layers6-3/, ...) for an older run. Prints the counts per (class, pad entry);
--json writes them. CI/model only: bench gates stay OPEN.
"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[4]
sys.path.insert(0, str(BASE / 'pcb'))
sys.path.insert(0, str(HERE.parent))
import make_board as mb  # noqa: E402

PAD = re.compile(r'Pad (\S+) \[([^\]]+)\] of (\S+)')
NET = re.compile(r'\[([^\]]+)\]')


def classify(drc, spec):
    """{'unconnected', 'pad_entry', 'other', 'by_class': [[class, pad_entry, count]], 'pad_entry_items': [...]}."""
    inp = mb.Inputs(spec)
    nc = inp.netclasses
    width = {n: nc['classes'][c['class']].get('outer_min_width_mm') for n, c in nc['nets'].items() if c.get('class') in nc['classes']}
    counts, rows = collections.Counter(), []
    for u in drc.get('unconnected_items', []):
        hit, net, why = False, None, []
        for it in u.get('items', []):
            mt = PAD.search(it.get('description', ''))
            if not mt:
                continue
            num, net, ref = mt.groups()
            w = width.get(net) or 0.15
            pa = inp.parts.get(ref)
            for p in (pa.pads if pa else []):
                if p['number'] == num:
                    b = p['box']
                    short = min(b[2] - b[0], b[3] - b[1])
                    if w > short + 1e-6:
                        hit = True
                        why.append(f'{ref}.{num} pad {round(short, 3)} mm < class {w} mm')
        if net is None:
            mt = NET.search(u['items'][0].get('description', '')) if u.get('items') else None
            net = mt.group(1) if mt else '?'
        cls = nc['nets'].get(net, {}).get('class', 'SIG')
        counts[(cls, hit)] += 1
        if hit:
            rows.append({'net': net, 'class': cls, 'why': why})
    return {'unconnected': sum(counts.values()), 'pad_entry': sum(v for (c, h), v in counts.items() if h),
            'other': sum(v for (c, h), v in counts.items() if not h),
            'by_class': [[c, h, v] for (c, h), v in sorted(counts.items())], 'pad_entry_items': rows,
            'label': 'MODEL diagnostic (build/kicad/boards/PWR_A/freeze/padentry.py): pad short side against the outer class '
                     'width; not a DRC result'}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('drc', help='drc.json of a PWR_A route run (artifact board/drc.json or a committed record)')
    ap.add_argument('spec', nargs='?', default=str(HERE.parent / 'board-spec.json'), help='board-spec.json of that run')
    ap.add_argument('--json', help='write the classification here')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    res = classify(json.loads(Path(args.drc).read_text(encoding='utf-8')), json.loads(Path(args.spec).read_text(encoding='utf-8')))
    print('unconnected', res['unconnected'], 'with a pad end narrower than the class width', res['pad_entry'], 'others', res['other'])
    print(res['by_class'])
    if args.json:
        Path(args.json).write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
