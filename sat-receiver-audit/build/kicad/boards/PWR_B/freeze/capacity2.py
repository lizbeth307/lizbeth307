#!/usr/bin/env python3
"""PWR-B bar capacity on a cut line (W2 PWR-TOOLS). MODEL diagnostic: standard library, offline, not run by CI.

  python build/kicad/boards/PWR_B/freeze/capacity2.py [--layers F,In2,In3,B] [--x0 42 --x1 50] [--y1 35] [--json OUT]

From the W2 PWRJ F2C scratch tool capacity2.py (paths relative to this file, the cut-line band as options). For every
vertical line x = x0 .. x1 (1 mm steps) through the band y 0 .. y1 of the PWR_B placement made by make_spec.py (board mm,
y up) it sums the free span per copper layer: the band less the pads (+0.15 clearance), the scripted tracks and vias
(+0.15), the PWR-A cut-outs grown 0.3 (+0.15 router clearance), the hole keep-outs and the 0.35 mm edge bands, and the track
count that span holds at 0.3 mm pitch (0.15 track + 0.15 space). It also lists the nets with pads on both sides of the band
(x < x0 and x > x1), which must cross it. The default band is the x 42-50 bar of the W2 PWRB-R PLACE study; a frozen route
is not counted (the free space before routing). Every number is MODEL; bench gates stay OPEN.
"""
import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[4]
C = 0.15  # project clearance (netclasses.json project_defaults)


def load_make_spec():
    sys.path.insert(0, str(BASE / 'pcb'))
    loader = importlib.util.spec_from_file_location('pwr_b_make_spec_cap', HERE.parent / 'make_spec.py')
    ms = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(ms)
    return ms


def capacity(layers, x0=42, x1=50, y1=35.0):
    ms = load_make_spec()
    inp = ms.Inputs()
    _anchors, _missing, _pins, parts, tracks, vias, _exempt = ms.build(inp)
    cuts = [tuple(c['rect']) for c in inp.cutouts]
    holes = [tuple(h) for h in inp.contract['holes_mm']]
    kr = inp.contract['hole_keepout_d'] / 2

    def spans(x, layer):
        blk = [(-1.0, 0.35), (y1 - 0.35, y1 + 5.0)]
        for r in cuts:
            if r[0] - 0.45 <= x <= r[2] + 0.45:
                blk.append((r[1] - 0.45, r[3] + 0.45))
        for hx, hy in holes:
            if abs(x - hx) < kr:
                d = math.sqrt(kr ** 2 - (x - hx) ** 2)
                blk.append((hy - d, hy + d))
        for pa in parts.values():
            for p in pa.pads:
                th = p['type'] in ('thru_hole', 'np_thru_hole')
                if not th and layer not in p['layers']:
                    continue
                b = p['box']
                if b[0] - C <= x <= b[2] + C:
                    blk.append((b[1] - C, b[3] + C))
        for t in tracks:
            if t['layer'].split('.')[0] != layer:
                continue
            r = t['width_mm'] / 2 + C
            for (xa, ya), (xb, yb) in zip(t['path'], t['path'][1:]):
                if min(xa, xb) - r <= x <= max(xa, xb) + r:
                    if abs(xb - xa) < 1e-9:
                        blk.append((min(ya, yb) - r, max(ya, yb) + r))
                    else:
                        u = max(0.0, min(1.0, (x - xa) / (xb - xa)))
                        yy = ya + u * (yb - ya)
                        blk.append((yy - r, yy + r))
        for v in vias:
            r = v['diameter_mm'] / 2 + C
            if abs(x - v['at'][0]) <= r:
                blk.append((v['at'][1] - r, v['at'][1] + r))
        blk.sort()
        free, cur = 0.0, 0.35
        for a, b in blk:
            if a > cur:
                free += a - cur
            cur = max(cur, b)
        return free
    rows = []
    for x in range(int(x0), int(x1) + 1):
        fr = {lay: round(spans(x, lay), 2) for lay in layers}
        rows.append({'x': x, 'free_mm': fr, 'sum_mm': round(sum(fr.values()), 2), 'tracks': sum(int(v / 0.3) for v in fr.values())})
    nets = {}
    for pa in parts.values():
        for p in pa.pads:
            if p['net'] and p['net'] not in ms.SCRIPTED_CLASSES:
                nets.setdefault(p['net'], []).append(p['at'])
    cross = sorted(n for n, pts in nets.items() if any(a[0] < x0 for a in pts) and any(a[0] > x1 for a in pts))
    return {'band': {'x': [x0, x1], 'y': [0.0, y1]}, 'layers': list(layers), 'lines': rows,
            'min_free_mm': {lay: min(r['free_mm'][lay] for r in rows) for lay in layers},
            'min_tracks': min(r['tracks'] for r in rows), 'crossing_nets': cross,
            'label': 'MODEL diagnostic (build/kicad/boards/PWR_B/freeze/capacity2.py): free span on cut lines before routing'}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--layers', default='F,In2,In3,B', help='routing layers, comma separated (F, In2, In3, B)')
    ap.add_argument('--x0', type=float, default=42)
    ap.add_argument('--x1', type=float, default=50)
    ap.add_argument('--y1', type=float, default=35.0)
    ap.add_argument('--json', help='write the result here')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    res = capacity(args.layers.split(','), args.x0, args.x1, args.y1)
    for r in res['lines']:
        print(f"x {r['x']:3d} " + ' '.join(f'{lay} {v:5.1f}' for lay, v in r['free_mm'].items())
              + f"  sum {r['sum_mm']:5.1f}  tracks <= {r['tracks']}")
    print('min per layer', res['min_free_mm'], 'min tracks', res['min_tracks'])
    print('crossing nets', len(res['crossing_nets']))
    print(' '.join(res['crossing_nets']))
    if args.json:
        Path(args.json).write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
