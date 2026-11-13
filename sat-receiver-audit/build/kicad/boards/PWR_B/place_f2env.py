#!/usr/bin/env python3
"""PWR-B re-placement for the F2-ENV probe (W2 PWRJ F2ENV), standard library. PROBE ONLY.

  python3 build/kicad/boards/PWR_B/place_f2env.py           write placement-f2env.json next to this file
  python3 build/kicad/boards/PWR_B/place_f2env.py --check   fail unless it reproduces

The F2-ENV contract grows the PWR-B L down by the slab (board y < 0, inside the bay), the PWR-A bottom harness row moves
to the new bottom edge and the S02 headers and J506 stand in the slab (make_spec.py PLACEMENT, BAY_PLUGS). This tool
re-places the parts that the earlier lineage had to park in the arm and the bar (the old leg and x < BAR_X of the band):
the Kelvin cells of LNA ch1-ch3 as rigid units (LNA_ROWS geometry kept, no turn), every other part of that region on its
own (quarter turns allowed). Fixed: everything right of BAR_X in the band (the J209 rail block tuned by PCB-PWRB-2), the
LAB5 switch cells, ch4, the headers. Legal place: courtyard inside the outline (inset), CRT_GUARD off every PWR-A
cut-out, off the plug zones, off the hole keep-outs, off the fixed scripted copper (LAB5 trunk, J209 spine, ch4 sense),
GAP from every courtyard. Cost: class-weighted half-perimeter of the non-GND nets. Simulated annealing with a fixed seed.
make_spec.py reads placement-f2env.json over its PLACEMENT table. MODEL placement input, not a hardware result.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_spec as ms  # noqa: E402

OUT = HERE / 'placement-f2env.json'
SEED = 20261113
GAP = 0.3
INSET = 0.3
BAR_X = 60.0          # band parts right of this stay (J209 rail block); left of it and the whole arm move
STEPS = 250000
WEIGHT = {'BATT': 4.0, 'PWR3A': 3.0, 'PWR2A': 2.0, 'PWR1A': 1.5}
FIXED_ALWAYS = {'J201', 'J202', 'J203', 'J204', 'J207', 'J209', 'J506'}
FIXED_PREFIX = ('LAB5', 'K4', 'GND-J209')
NO_TURN = {'U215'}   # its exposed-pad GND stub (make_spec gnd_fanout) is drawn for the table rotation


def ov(a, b, g=0.0):
    return not (a[2] + g <= b[0] or b[2] + g <= a[0] or a[3] + g <= b[1] or b[3] + g <= a[1])


def seg_box(path, w):
    out = []
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        out.append((min(x0, x1) - w, min(y0, y1) - w, max(x0, x1) + w, max(y0, y1) + w))
    return out


class Model:
    def __init__(self):
        inp = ms.Inputs()
        self.inp = inp
        anchors = ms.placement(inp)
        self.anchors = anchors
        c = inp.contract
        self.outline = [tuple(p) for p in c['outline_mm']]
        xs = sorted({p[0] for p in self.outline})
        ys = sorted({p[1] for p in self.outline})
        # the L (two rectangles), inset
        self.areas = [(xs[0] + INSET, ys[0] + INSET, xs[-1] - INSET, ys[1] - INSET),
                      (xs[0] + INSET, ys[0] + INSET, xs[1] - INSET, ys[-1] - INSET)]
        self.bbox = (xs[0], ys[0], xs[-1], ys[-1])
        g = ms.CRT_GUARD
        self.static = [(b[0] - g, b[1] - g, b[2] + g, b[3] + g) for b in inp.cut_boxes]
        self.holes = [(tuple(h), c['hole_keepout_d'] / 2) for h in c['holes_mm']]
        parts = ms.placed_parts(inp, anchors)
        # drilled holes of the fixed parts of both sides (J209 alignment pegs, header pins) keep every courtyard off
        self.cuts = [tuple(b) for b in inp.cut_boxes]
        self.drills = []
        for name in ms.PLUG_ZONES:
            hb = parts[name].box
            self.static.append((hb[0], hb[3], hb[2], ms.BAND_TOP))
        for name in ms.BAY_PLUGS:
            hb = parts[name].box
            self.static.append((hb[0], hb[3], hb[2], hb[3] + ms.BAY_PLUG_MM))
        # fixed scripted copper of the current spec (LAB5 trunk and taps, J209 spine and stubs, ch4 sense)
        spec = json.loads(ms.SPEC.read_text(encoding='utf-8'))
        for t in spec['pre_route']['tracks']:
            if t['id'].startswith(FIXED_PREFIX):
                self.static += seg_box(t['path'], t['width_mm'] / 2 + 0.2)
        for v in spec['pre_route']['vias']:
            if v['id'].startswith(FIXED_PREFIX):
                r = v['diameter_mm'] / 2 + 0.25
                self.static.append((v['at'][0] - r, v['at'][1] - r, v['at'][0] + r, v['at'][1] + r))
        # units
        cell_of = {}
        for ch in ('1', '2', '3'):
            for k, ref in ms.LNA_CELLS[ch].items():
                cell_of[ref] = 'CELL' + ch
        lab5 = {ref for _x, _y, d in ms.LAB5_CELLS for ref in d.values()}
        ch4 = set(ms.LNA_CELLS['4'].values())
        self.fixed = set()
        for ref, a in anchors.items():
            x, y = a['at']
            in_bar_or_arm = y >= 35 or x < BAR_X
            if (ref in FIXED_ALWAYS or ref in lab5 or ref in ch4 or not in_bar_or_arm or a.get('side') == 'B'):
                self.fixed.add(ref)
        units = {}
        for ref in anchors:
            if ref in self.fixed:
                continue
            u = cell_of.get(ref, ref)
            units.setdefault(u, []).append(ref)
        # a cell moves only if all its parts are movable
        for u in [u for u in units if u.startswith('CELL')]:
            ch = u[4:]
            refs = set(ms.LNA_CELLS[ch].values())
            if not refs <= set(units[u]):
                for r in units.pop(u):
                    self.fixed.add(r)
        self.units = units
        self.unit_of = {r: u for u, rs in units.items() for r in rs}
        # geometry per ref and rotation (singles), relative to the anchor point
        for ref, pa in parts.items():
            if ref in self.fixed:
                for p in pa.pads:
                    if p['type'] in ('thru_hole', 'np_thru_hole'):
                        self.drills.append(tuple(p['box']))
        self.shape = {}
        for ref, a in anchors.items():
            rots = ((0, 90, 180, 270) if (ref in self.unit_of and not self.unit_of[ref].startswith('CELL') and ref not in NO_TURN)
                    else (a['rotation'],))
            sh = {}
            for rot in rots:
                pa = ms.Placed(ref, inp.geo[ref], inp.fab[ref], {**a, 'at': [0.0, 0.0], 'rotation': rot}, inp.nets_of(ref))
                sh[rot] = (tuple(pa.box), [(p['number'], p['at'][0], p['at'][1], p['net']) for p in pa.pads],
                           [tuple(p['box']) for p in pa.pads if p['type'] != 'np_thru_hole'])
            self.shape[ref] = sh
        self.at = {r: (float(a['at'][0]), float(a['at'][1])) for r, a in anchors.items()}
        self.rot = {r: int(a['rotation']) % 360 for r, a in anchors.items()}
        nc = inp.netclasses
        cls = {p['pattern']: p['netclass'] for p in nc['kicad']['netclass_patterns']}
        cls.update(ms.BOARD_CLASSES)
        self.net_pins = {}
        for ref in anchors:
            for num, _x, _y, net in self.shape[ref][self.rot[ref]][1]:
                if net and net != 'GND':
                    self.net_pins.setdefault(net, []).append((ref, num))
        self.net_pins = {n: v for n, v in self.net_pins.items() if len({r for r, _ in v}) > 1}
        self.weight = {n: WEIGHT.get(cls.get(n), 1.0) for n in self.net_pins}
        self.nets_of = {r: sorted({n for n, v in self.net_pins.items() for rr, _ in v if rr == r}) for r in anchors}

    def box(self, ref, at=None, rot=None):
        at = self.at[ref] if at is None else at
        rot = self.rot[ref] if rot is None else rot
        b = self.shape[ref][rot][0]
        return (b[0] + at[0], b[1] + at[1], b[2] + at[0], b[3] + at[1])

    def pin(self, ref, num):
        x0, y0 = self.at[ref]
        for n, x, y, _net in self.shape[ref][self.rot[ref]][1]:
            if n == num:
                return (x + x0, y + y0)
        raise KeyError((ref, num))

    def pads_ok(self, ref, at, rot):
        e = ms.EDGE + ms.MARGIN
        for q in self.shape[ref][rot][2]:
            pb = (q[0] + at[0] - e, q[1] + at[1] - e, q[2] + at[0] + e, q[3] + at[1] + e)
            if not any(a[0] - 0.3 <= pb[0] and a[1] - 0.3 <= pb[1] and pb[2] <= a[2] + 0.3 and pb[3] <= a[3] + 0.3
                       for a in self.areas):
                return False
            if any(ov(pb, c) for c in self.cuts):
                return False
        return True

    def static_ok(self, b):
        if any(ov(b, d) for d in self.drills):
            return False
        if not any(a[0] - 1e-9 <= b[0] and a[1] - 1e-9 <= b[1] and b[2] <= a[2] + 1e-9 and b[3] <= a[3] + 1e-9
                   for a in self.areas):
            return False
        if any(ov(b, s) for s in self.static):
            return False
        for (hx, hy), r in self.holes:
            dx = max(b[0] - hx, 0.0, hx - b[2])
            dy = max(b[1] - hy, 0.0, hy - b[3])
            if math.hypot(dx, dy) < r:
                return False
        return True


def place(steps=STEPS):
    m = Model()
    rng = random.Random(SEED)
    cell = 3.0
    grid = {}

    def keys(b):
        for i in range(int(math.floor(b[0] / cell)), int(math.floor(b[2] / cell)) + 1):
            for j in range(int(math.floor(b[1] / cell)), int(math.floor(b[3] / cell)) + 1):
                yield (i, j)

    def add(r):
        for k in keys(m.box(r)):
            grid.setdefault(k, set()).add(r)

    def rem(r):
        for k in keys(m.box(r)):
            grid[k].discard(r)
    for r in m.at:
        if m.anchors[r].get('side', 'F') == 'F':
            add(r)

    def legal_ref(r, at, rot, ignore):
        b = m.box(r, at, rot)
        if not m.static_ok(b) or not m.pads_ok(r, at, rot):
            return False
        bb = (b[0] - GAP, b[1] - GAP, b[2] + GAP, b[3] + GAP)
        for k in keys(bb):
            for o in grid.get(k, ()):
                if o in ignore:
                    continue
                if ov(b, m.box(o), GAP):
                    return False
        return True

    def net_cost(n):
        xs, ys = [], []
        for r, num in m.net_pins[n]:
            x, y = m.pin(r, num)
            xs.append(x)
            ys.append(y)
        return m.weight[n] * ((max(xs) - min(xs)) + (max(ys) - min(ys)))
    cost = {n: net_cost(n) for n in m.net_pins}
    start = sum(cost.values())
    units = sorted(m.units)

    def try_unit(u, dx, dy, rot=None):
        refs = m.units[u]
        new = {}
        for r in refs:
            ro = m.rot[r] if rot is None else rot
            new[r] = ((round(m.at[r][0] + dx, 3), round(m.at[r][1] + dy, 3)), ro)
        ign = set(refs)
        if not all(legal_ref(r, a, ro, ign) for r, (a, ro) in new.items()):
            return None
        nets = sorted({n for r in refs for n in m.nets_of[r]})
        before = sum(cost[n] for n in nets)
        old = {r: (m.at[r], m.rot[r]) for r in refs}
        for r in refs:
            rem(r)
        for r, (a, ro) in new.items():
            m.at[r], m.rot[r] = a, ro
            add(r)
        nc = {n: net_cost(n) for n in nets}
        return sum(nc.values()) - before, nc, old

    def undo(old):
        for r in old:
            rem(r)
        for r, (a, ro) in old.items():
            m.at[r], m.rot[r] = a, ro
            add(r)

    # legalise: a unit on an illegal place moves by a spiral search
    moved = []
    for u in units:
        refs = m.units[u]
        if all(legal_ref(r, m.at[r], m.rot[r], set(refs)) for r in refs):
            continue
        done = False
        for rad in [i * 0.5 for i in range(1, 280)]:
            n = max(8, int(rad * 6))
            for k in range(n):
                ang = 2 * math.pi * k / n
                res = try_unit(u, rad * math.cos(ang), rad * math.sin(ang))
                if res:
                    for nn, v in res[1].items():
                        cost[nn] = v
                    done = True
                    break
            if done:
                break
        if not done:
            raise SystemExit(f'place_f2env: no legal place for {u}')
        moved.append(u)
    legal_cost = sum(cost.values())
    total = legal_cost
    t0, t1 = 6.0, 0.03
    accepted = 0
    x0, y0, x1, y1 = m.bbox
    for step in range(steps):
        f = step / steps
        T = t0 * (t1 / t0) ** f
        sig = 25.0 * (1 - f) + 0.4
        u = units[rng.randrange(len(units))]
        p = rng.random()
        if p < 0.12 and not u.startswith('CELL') and u not in NO_TURN:
            res = try_unit(u, 0.0, 0.0, rot=rng.choice((0, 90, 180, 270)))
        elif p < 0.30:
            # pull towards the centre of the unit's nets
            refs = m.units[u]
            pts = [m.pin(rr, num) for r0 in refs for n in m.nets_of[r0] for rr, num in m.net_pins[n]]
            if not pts:
                continue
            cx = sum(q[0] for q in pts) / len(pts)
            cy = sum(q[1] for q in pts) / len(pts)
            ux = sum(m.at[r][0] for r in refs) / len(refs)
            uy = sum(m.at[r][1] for r in refs) / len(refs)
            k = rng.random()
            res = try_unit(u, round((cx - ux) * k, 2), round((cy - uy) * k, 2))
        else:
            res = try_unit(u, round(rng.gauss(0, sig), 2), round(rng.gauss(0, sig), 2))
        if not res:
            continue
        d, nc, old = res
        if d <= 0 or rng.random() < math.exp(-d / T):
            for n, v in nc.items():
                cost[n] = v
            total += d
            accepted += 1
        else:
            undo(old)
    final = sum(cost.values())
    pos = {r: [round(m.at[r][0], 3), round(m.at[r][1], 3), m.rot[r]] for r in sorted(m.unit_of)}
    return {'schema': 'srrx-pwrb-f2env-placement-v1', 'board_id': 'PWR_B',
            'status': 'MODEL placement input of the W2 PWRJ F2ENV probe (place_f2env.py); not a board of record',
            'rules': {'seed': SEED, 'steps': steps, 'gap_mm': GAP, 'inset_mm': INSET, 'bar_x': BAR_X, 'weights': WEIGHT},
            'cost': {'start': round(start, 1), 'after_legalising': round(legal_cost, 1), 'final': round(final, 1),
                     'accepted': accepted},
            'units': {u: sorted(rs) for u, rs in sorted(m.units.items())}, 'legalised': moved,
            'fixed_refs': len(m.fixed), 'moved_refs': len(m.unit_of), 'positions': pos}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--steps', type=int, default=STEPS)
    a = ap.parse_args(argv)
    saved = None
    if OUT.is_file():
        saved = OUT.read_text(encoding='utf-8')
        OUT.unlink()    # place from the make_spec table, not from an earlier result
    try:
        doc = place(a.steps)
    finally:
        if saved is not None and a.check:
            OUT.write_text(saved, encoding='utf-8', newline='\n')
    text = json.dumps(doc, ensure_ascii=False, indent=1) + '\n'
    if a.check:
        if text != saved:
            print(f'{OUT.name} is stale: rerun place_f2env.py')
            return 1
        print(f'{OUT.name} reproduces')
        return 0
    OUT.write_text(text, encoding='utf-8', newline='\n')
    print(json.dumps(doc['cost']), doc['moved_refs'], 'moved,', doc['fixed_refs'], 'fixed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
