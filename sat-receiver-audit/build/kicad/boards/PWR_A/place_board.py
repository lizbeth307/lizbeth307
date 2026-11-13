#!/usr/bin/env python3
"""PWR-A board placement (W2 PCB-PWRA-4): net-aware re-placement of the planner-placed parts, standard library.

  python3 build/kicad/boards/PWR_A/place_board.py           write board-placement.json next to this file
  python3 build/kicad/boards/PWR_A/place_board.py --check   fail unless board-placement.json reproduces

Why: the board_gen planner of W2 PCB-PWRA-3 packs groups first-fit into free rectangles and splits groups into distant
chunks; route iteration 1 of the board of record (W2 PCB-PWRA-4) measured what that costs the router. This tool keeps
everything the earlier packages fixed and moves only the rest:

  fixed  the anchors of PWR_A.spec-shrink2.json (power stages and their scripted copper, harness headers, J208, the
         zone 1-2 regulators) and every part with a PWR-B cut-out (placement-study-shrink2.json pwr_b_cutouts: windows
         over parts taller than hA, header edge strips, test-point probe windows), because PCB-PWRB-2 placed PWR-B around
         exactly that cut-out list;
  moved  the other top parts (planner-placed chips, SOT, SO, QFN, 16SVPG47M) and the 94 bottom chips, each on its side.

Legal place of a top part: courtyard inside the L outline less EDGE_INSET, off the hole keep-outs, off every scripted
F.Cu pour (reserved kind 'copper'), off every scripted via, GAP from every other top courtyard, and, unless its read or
class height is at most the H-TRIM zone height (2.7 mm), off every PWR-B THT pin field + window_margin
(pcb/boards/PWR_B.json h_trim). Legal place of a bottom part: courtyard inside one plate pocket PB1-PB13 of the contract
(bottom_side.keep_in_mm, EDGE_INSET from the outline), off the scripted B.Cu copper, the thermal bond zones, the top THT
pin fields + tht_margin and every scripted via, GAP from every other bottom courtyard.

Method: legalise the planner positions (a part on an illegal spot moves to the nearest legal one, spiral search), then
simulated annealing with a fixed seed: moves are a shift (with a quarter turn now and then), a swap of two parts of one
side and a pull towards the centre of a part's nets; the cost is the sum over the nets (GND excluded: every GND pad has
its plane via) of the half-perimeter of the pin box, weighted by the net class of pcb/generated/netclasses.json (wide
copper is harder to route). Deterministic: same inputs, same output. MODEL placement input, not a hardware result.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[3]  # sat-receiver-audit
sys.path.insert(0, str(BASE / 'pcb'))
sys.path.insert(0, str(HERE))
import board_gen as bg  # noqa: E402
import make_board as mb  # noqa: E402
import make_probe_spec as mps  # noqa: E402

SHRINK2 = HERE / 'PWR_A.spec-shrink2.json'
STUDY = HERE / 'placement-study-shrink2.json'
OUT = HERE / 'board-placement.json'
CONTRACT = BASE / 'mechanical/generated/contract/boards.json'
NETCLASSES = BASE / 'pcb/generated/netclasses.json'
PWR_B_SPEC = BASE / 'pcb/boards/PWR_B.json'
PSPEC = BASE / 'pcb/partition-spec.json'

SEED = 20261112
EDGE_INSET = 0.3   # mm, courtyard to board outline (the planner rule)
GAP = 0.4          # mm, courtyard to courtyard on one side (routing room; the planner packed at 0.5)
VIA_KEEP = 0.5     # mm, courtyard to a scripted via centre beyond its radius (pads keep the 0.15 clearance with room)
STEPS = 400000     # annealing moves
GRIDSTEP = 0.05    # mm, position grid
WEIGHT = {'BATT': 4.0, 'PWR3A': 3.0, 'PWR2A': 2.0, 'PWR1A': 1.5}  # cost weight per net class (others 1.0)


def r4(v):
    return bg.r4(v)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def snap(v):
    return round(round(v / GRIDSTEP) * GRIDSTEP, 4)


def overlap(a, b, gap=0.0):
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])


def inside(a, r):
    return r[0] - 1e-9 <= a[0] and r[1] - 1e-9 <= a[1] and a[2] <= r[2] + 1e-9 and a[3] <= r[3] + 1e-9


def box_circle(box, c, r):
    dx = max(box[0] - c[0], 0.0, c[0] - box[2])
    dy = max(box[1] - c[1], 0.0, c[1] - box[3])
    return math.hypot(dx, dy) < r


class Model:
    def __init__(self):
        self.spec = read(SHRINK2)
        self.study = read(STUDY)
        contract = read(CONTRACT)['boards'][self.spec['contract']['board']]
        self.contract = contract
        nc = read(NETCLASSES)
        pspec = read(PSPEC)
        pwr_b = read(PWR_B_SPEC)
        graph = bg.load_graph()
        manifest = bg.read_json(bg.MANIFEST)
        pos = {r['ref']: r for r in self.study['positions']['refs']}
        fixed = mb.fixed_refs(self.study, self.spec)
        parts = []
        for p in self.spec['parts']:
            r = pos[p['ref']]
            anchor = p['anchor'] if p.get('anchor') else {'at': r['at'], 'align': 'origin', 'rotation': r['rotation'],
                                                          'side': r['side']}
            parts.append({'ref': p['ref'], 'source': p['source'], 'anchor': anchor})
        template = bg.resolve({**self.spec, 'parts': parts, 'groups': []}, graph, manifest)
        self.refs = [t['ref'] for t in template]
        self.side, self.at, self.rot, self.shape, self.fixed, self.nets_of = {}, {}, {}, {}, {}, {}
        self.tht = {}
        for t in template:
            ref = t['ref']
            geo = bg.footprint_geometry(bg.footprint_file(t).read_text(encoding='utf-8'))
            a = t['anchor']
            side = a.get('side', 'F')
            self.side[ref] = side
            self.fixed[ref] = ref in fixed
            # shapes per rotation: courtyard box and pad points relative to the anchor point
            shapes = {}
            for rot in (0, 90, 180, 270):
                g = bg.placed_geometry(geo, {'at': [0.0, 0.0], 'align': a.get('align', 'origin'), 'rotation': rot, 'side': side})
                pads = [(num, pt[0], pt[1]) for num, pts in g['pads'].items() for pt in pts]
                shapes[rot] = (tuple(g['box']), pads)
            self.shape[ref] = shapes
            self.at[ref] = (float(a['at'][0]), float(a['at'][1]))
            self.rot[ref] = int(round(float(a.get('rotation', 0)))) % 360
            self.nets_of[ref] = {num: n for num, n in t['pads'].items() if n and n != 'GND'}
            if side == 'F':
                # THT pads and NPTH pegs (numbered or not) of a top part: their pin field (placed_geometry keeps only
                # numbered pads, so the transform is done here the same way: rotation, then the board y flip)
                tp = [q for q in geo['pads'] if q['type'] in ('thru_hole', 'np_thru_hole')]
                if tp:
                    ox, oy = bg.placed_geometry(geo, a)['origin']
                    bx0 = by0 = math.inf
                    bx1 = by1 = -math.inf
                    for q in tp:
                        x, y = bg.turn_point(q['at'], float(a.get('rotation', 0)))
                        cx, cy = ox + x, oy - y
                        hw = max(q['size']) / 2
                        bx0, by0, bx1, by1 = min(bx0, cx - hw), min(by0, cy - hw), max(bx1, cx + hw), max(by1, cy + hw)
                    self.tht[ref] = (bx0, by0, bx1, by1)
        self.movable = [r for r in self.refs if not self.fixed[r]]
        # nets and weights
        cls = {p['pattern']: p['netclass'] for p in nc['kicad']['netclass_patterns']}
        self.weight = {}
        self.net_pins = {}
        for ref in self.refs:
            for num, n in self.nets_of[ref].items():
                self.net_pins.setdefault(n, []).append((ref, num))
                self.weight[n] = WEIGHT.get(cls.get(n), 1.0)
        self.net_pins = {n: v for n, v in self.net_pins.items() if len({r for r, _ in v}) > 1}
        self.part_nets = {r: sorted({n for n in self.nets_of[r].values() if n in self.net_pins}) for r in self.refs}
        # static obstacles
        ol = contract['outline_mm']
        xs = sorted({p[0] for p in ol})
        ys = sorted({p[1] for p in ol})
        # the L of the contract as the union of two rectangles (outline [[0,0],[136,0],[136,35],[42,35],[42,110],[0,110]])
        self.areas_top = [(EDGE_INSET, EDGE_INSET, xs[-1] - EDGE_INSET, ys[1] - EDGE_INSET),
                          (EDGE_INSET, EDGE_INSET, xs[1] - EDGE_INSET, ys[-1] - EDGE_INSET)]
        self.holes = [(tuple(h), contract['hole_keepout_d'] / 2) for h in contract['holes_mm']]
        self.copper = {'F': [], 'B': []}
        for ra in self.spec['reserved_areas']:
            if ra.get('kind') in ('copper', 'thermal_bond'):
                self.copper[ra.get('side', 'F')].append(tuple(ra['rect']))
        self.vias = [(tuple(v['at']), v['diameter_mm'] / 2 + VIA_KEEP) for v in self.spec['pre_route']['vias']]
        # the GND fan-out of the fixed parts (make_board.py gnd_fanout on the fixed parts alone; make_board fans them out
        # first, so the same vias and stubs come back): its vias keep every courtyard off, its stubs the courtyards of
        # their side
        self.stubs = {'F': [], 'B': []}
        base = mps.build_placement()
        keep = [p for p in base['parts'] if p['ref'] in fixed]
        sub = mb.Inputs({**base, 'parts': keep})
        ft, fv, _skip = mb.gnd_fanout(sub, mb.board_copper(base['pre_route'], sub)[0], first=fixed)
        self.vias += [(tuple(v['at']), v['diameter_mm'] / 2 + VIA_KEEP) for v in fv]
        for s in ft:
            side = s['layer'][0]
            for a, b in zip(s['path'], s['path'][1:]):
                w = s['width_mm'] / 2 + VIA_KEEP
                self.stubs[side].append((min(a[0], b[0]) - w, min(a[1], b[1]) - w, max(a[0], b[0]) + w, max(a[1], b[1]) + w))
        self.fanout_fixed = {'vias': len(fv), 'stubs': len(ft)}

        # each pocket clipped to the inset L (route iteration 2, sr-rx-pcb run 43295500516: R123 stood at the inner edge
        # x 42 of the leg, copper_edge_clearance)
        self.pockets = []
        for x, y, w, h in contract['bottom_side']['keep_in_mm']:
            cuts = [(max(x, a[0]), max(y, a[1]), min(x + w, a[2]), min(y + h, a[3])) for a in self.areas_top]
            cuts = [c for c in cuts if c[2] > c[0] and c[3] > c[1]]
            self.pockets.append(max(cuts, key=lambda c: ((c[2] - c[0]) * (c[3] - c[1]), c)))
        margin = float(self.spec['two_sided']['tht_margin_mm'])
        self.tht_fields = [(b[0] - margin, b[1] - margin, b[2] + margin, b[3] + margin) for b in self.tht.values()]
        zmax = pspec['keepouts']['h_trim']['zone_h_max_mm']
        wm = pspec['parameters']['window_margin']
        self.htrim = [(f['field_mm'][0] - wm, f['field_mm'][1] - wm, f['field_mm'][2] + wm, f['field_mm'][3] + wm)
                      for f in pwr_b['h_trim']['pin_fields']]
        self.low = {}
        hin = type('H', (), {'graph': graph, 'pspec': pspec})()
        for ref in self.refs:
            h, _src = mb.height_of(hin, ref)  # the heights make_board.py writes into the spec
            self.low[ref] = h is not None and h <= zmax + 1e-9

    def box(self, ref, at=None, rot=None):
        at = self.at[ref] if at is None else at
        rot = self.rot[ref] if rot is None else rot
        b = self.shape[ref][rot][0]
        return (b[0] + at[0], b[1] + at[1], b[2] + at[0], b[3] + at[1])

    def pins(self, ref, at=None, rot=None):
        at = self.at[ref] if at is None else at
        rot = self.rot[ref] if rot is None else rot
        return {num: (x + at[0], y + at[1]) for num, x, y in self.shape[ref][rot][1]}

    def static_ok(self, ref, box):
        side = self.side[ref]
        if side == 'F':
            if not any(inside(box, a) for a in self.areas_top):
                return False
            if any(overlap(box, c) for c in self.copper['F']):
                return False
            if not self.low[ref] and any(overlap(box, z) for z in self.htrim):
                return False
        else:
            if not any(inside(box, p) for p in self.pockets):
                return False
            if any(overlap(box, c) for c in self.copper['B']):
                return False
            if any(overlap(box, f) for f in self.tht_fields):
                return False
        if any(overlap(box, s) for s in self.stubs[side]):
            return False
        if any(box_circle(box, c, r) for c, r in self.holes):
            return False
        if any(box_circle(box, c, r) for c, r in self.vias):
            return False
        return True


class Grid:
    """Spatial hash of the courtyards of one side."""

    def __init__(self, cell=5.0):
        self.cell = cell
        self.cells = {}

    def keys(self, b):
        c = self.cell
        for i in range(int(math.floor(b[0] / c)), int(math.floor(b[2] / c)) + 1):
            for j in range(int(math.floor(b[1] / c)), int(math.floor(b[3] / c)) + 1):
                yield (i, j)

    def add(self, ref, b):
        for k in self.keys(b):
            self.cells.setdefault(k, set()).add(ref)

    def remove(self, ref, b):
        for k in self.keys(b):
            self.cells[k].discard(ref)

    def near(self, b):
        out = set()
        for k in self.keys((b[0] - GAP, b[1] - GAP, b[2] + GAP, b[3] + GAP)):
            out |= self.cells.get(k, set())
        return out


def place():
    m = Model()
    rng = random.Random(SEED)
    grids = {'F': Grid(), 'B': Grid()}
    for ref in m.refs:
        grids[m.side[ref]].add(ref, m.box(ref))

    def legal(ref, at, rot, ignore=()):
        b = m.box(ref, at, rot)
        if not m.static_ok(ref, b):
            return False
        for other in grids[m.side[ref]].near(b):
            if other == ref or other in ignore:
                continue
            if overlap(b, m.box(other), GAP):
                return False
        return True

    # pin positions and net costs
    pinpos = {ref: m.pins(ref) for ref in m.refs}

    def net_cost(n):
        xs, ys = [], []
        for ref, num in m.net_pins[n]:
            x, y = pinpos[ref][num]
            xs.append(x)
            ys.append(y)
        return m.weight[n] * ((max(xs) - min(xs)) + (max(ys) - min(ys)))
    cost = {n: net_cost(n) for n in m.net_pins}
    start_cost = sum(cost.values())

    # 1. legalise: a part on an illegal spot moves to the nearest legal one (spiral search); if there is none, it takes
    # the place of a legal part of its side whose own new place is legal (swap, or that part moved by a spiral search)
    def spiral(ref, origin, rots, max_r, ignore=()):
        for radius in [i * 0.25 for i in range(0, int(max_r / 0.25) + 1)]:
            n = max(8, int(radius * 8)) if radius else 1
            for k in range(n):
                ang = 2 * math.pi * k / n
                at = (snap(origin[0] + radius * math.cos(ang)), snap(origin[1] + radius * math.sin(ang)))
                for rot in rots:
                    if legal(ref, at, rot, ignore):
                        return at, rot
        return None

    def centre(ref, at=None, rot=None):
        b = m.box(ref, at, rot)
        return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)

    def at_for_centre(ref, c, rot):
        b = m.shape[ref][rot][0]
        return (snap(c[0] - (b[0] + b[2]) / 2), snap(c[1] - (b[1] + b[3]) / 2))

    def commit(ref, at, rot):
        grids[m.side[ref]].remove(ref, m.box(ref))
        m.at[ref], m.rot[ref] = at, rot
        grids[m.side[ref]].add(ref, m.box(ref))
        pinpos[ref] = m.pins(ref)

    def evict(ref, c0):
        """Place ref on a statically legal spot (nearest first) after moving every movable courtyard it would touch to
        a spiral spot within 15 mm; all or nothing. Returns ([evicted refs], spot) or None."""
        side = m.side[ref]
        spots = []
        for x in range(1, 136):
            for y in range(1, 110):
                for rot in (0, 90, 180, 270):
                    at = at_for_centre(ref, (x, y), rot)
                    b = m.box(ref, at, rot)
                    if m.static_ok(ref, b):
                        spots.append((math.dist((x, y), c0), x, y, rot, at))
        spots.sort()
        for _d, _x, _y, rot, at in spots[:400]:
            b = m.box(ref, at, rot)
            # sorted: near() is a set, and the eviction order below breaks area ties by this order (W2 PWRJ-LAYERS6: with
            # str hash randomisation the set order made two runs differ)
            hit = sorted((o for o in grids[side].near(b) if o != ref and overlap(b, m.box(o), GAP)), key=bg.sort_ref)
            if any(m.fixed[o] for o in hit):
                continue
            saved = {o: (m.at[o], m.rot[o]) for o in hit}
            for o in hit:
                grids[side].remove(o, m.box(o))
            m.at[ref], m.rot[ref] = at, rot
            grids[side].add(ref, b)
            placed = []
            ok = True
            for o in sorted(hit, key=lambda r: -((m.box(r)[2] - m.box(r)[0]) * (m.box(r)[3] - m.box(r)[1]))):
                s = spiral(o, saved[o][0], (saved[o][1], (saved[o][1] + 90) % 360), 15.0)
                if s is None:
                    ok = False
                    break
                m.at[o], m.rot[o] = s
                grids[side].add(o, m.box(o))
                placed.append(o)
            if ok:
                for o in hit + [ref]:
                    pinpos[o] = m.pins(o)
                return (hit, (at, rot))
            for o in placed:
                grids[side].remove(o, m.box(o))
            grids[side].remove(ref, b)
            for o, (a2, r2) in saved.items():
                m.at[o], m.rot[o] = a2, r2
                grids[side].add(o, m.box(o))
        return None

    moved_legal = []
    ghosts = []
    for ref in sorted(m.movable, key=bg.sort_ref):
        if legal(ref, m.at[ref], m.rot[ref]):
            continue
        grids[m.side[ref]].remove(ref, m.box(ref))
        found = spiral(ref, m.at[ref], (m.rot[ref], (m.rot[ref] + 90) % 360), 30.0)
        if found:
            m.at[ref], m.rot[ref] = found
            grids[m.side[ref]].add(ref, m.box(ref))
            pinpos[ref] = m.pins(ref)
            moved_legal.append(ref)
        else:
            ghosts.append(ref)
    for ref in ghosts:
        c0 = centre(ref)
        rots = (0, 90, 180, 270)
        others = sorted((r for r in m.movable if m.side[r] == m.side[ref] and r not in ghosts and r != ref),
                        key=lambda r: (math.dist(centre(r), c0), bg.sort_ref(r)))
        done = None
        for g in others:
            cg = centre(g)
            for rot in rots:
                at_ghost = at_for_centre(ref, cg, rot)
                if not legal(ref, at_ghost, rot, ignore=(g,)):
                    continue
                # g leaves its place: to the ghost's old centre, else to a spiral spot away from the ghost's new box
                grids[m.side[g]].remove(g, m.box(g))
                grids[m.side[ref]].add(ref, m.box(ref, at_ghost, rot))
                m_at_ref, m_rot_ref = m.at[ref], m.rot[ref]
                m.at[ref], m.rot[ref] = at_ghost, rot
                spot = None
                for rg in (m.rot[g], (m.rot[g] + 90) % 360):
                    a2 = at_for_centre(g, c0, rg)
                    if legal(g, a2, rg):
                        spot = (a2, rg)
                        break
                if spot is None:
                    spot = spiral(g, m.at[g], (m.rot[g], (m.rot[g] + 90) % 360), 12.0)
                if spot is None:
                    grids[m.side[ref]].remove(ref, m.box(ref))
                    m.at[ref], m.rot[ref] = m_at_ref, m_rot_ref
                    grids[m.side[g]].add(g, m.box(g))
                    continue
                m.at[g], m.rot[g] = spot
                grids[m.side[g]].add(g, m.box(g))
                pinpos[g], pinpos[ref] = m.pins(g), m.pins(ref)
                done = (g, spot)
                break
            if done:
                break
        if not done:
            done = evict(ref, c0)
        if not done:
            raise SystemExit(f'place_board: no legal place for {ref} (no free spot, no swap, no eviction)')
        moved_legal += [ref] + list(done[0] if isinstance(done[0], list) else [done[0]])
    for n in m.net_pins:
        cost[n] = net_cost(n)
    legal_cost = sum(cost.values())

    # 2. anneal
    movable = sorted(m.movable, key=bg.sort_ref)
    by_side = {s: [r for r in movable if m.side[r] == s] for s in ('F', 'B')}
    total = legal_cost
    t0, t1 = 8.0, 0.05
    accepted = 0

    def try_apply(changes):
        """changes: [(ref, at, rot)]; returns delta or None if illegal (state unchanged)."""
        refs = [c[0] for c in changes]
        old = {r: (m.at[r], m.rot[r]) for r in refs}
        for r, at, rot in changes:
            if not legal(r, at, rot, ignore=refs):
                return None, old
        # pairwise among the changed parts
        boxes = {r: m.box(r, at, rot) for r, at, rot in changes}
        for i, (a, _, _) in enumerate(changes):
            for b, _, _ in changes[i + 1:]:
                if m.side[a] == m.side[b] and overlap(boxes[a], boxes[b], GAP):
                    return None, old
        nets = sorted({n for r in refs for n in m.part_nets[r]})
        before = sum(cost[n] for n in nets)
        for r, at, rot in changes:
            grids[m.side[r]].remove(r, m.box(r))
        for r, at, rot in changes:
            m.at[r], m.rot[r] = at, rot
            grids[m.side[r]].add(r, m.box(r))
            pinpos[r] = m.pins(r)
        new = {n: net_cost(n) for n in nets}
        return (sum(new.values()) - before, new), old

    def undo(old):
        for r, (at, rot) in old.items():
            grids[m.side[r]].remove(r, m.box(r))
        for r, (at, rot) in old.items():
            m.at[r], m.rot[r] = at, rot
            grids[m.side[r]].add(r, m.box(r))
            pinpos[r] = m.pins(r)

    for step in range(STEPS):
        frac = step / STEPS
        temp = t0 * (t1 / t0) ** frac
        reach = max(0.5, 25.0 * (1 - frac))
        kind = rng.random()
        ref = movable[rng.randrange(len(movable))]
        if kind < 0.55:
            rot = m.rot[ref] if rng.random() > 0.15 else (m.rot[ref] + rng.choice((90, 180, 270))) % 360
            at = (snap(m.at[ref][0] + rng.uniform(-reach, reach)), snap(m.at[ref][1] + rng.uniform(-reach, reach)))
            changes = [(ref, at, rot)]
        elif kind < 0.8:
            pool = by_side[m.side[ref]]
            other = pool[rng.randrange(len(pool))]
            if other == ref:
                continue
            ca, cb = m.box(ref), m.box(other)
            dxa = ((cb[0] + cb[2]) - (ca[0] + ca[2])) / 2
            dya = ((cb[1] + cb[3]) - (ca[1] + ca[3])) / 2
            if math.hypot(dxa, dya) > reach * 2:
                continue
            changes = [(ref, (snap(m.at[ref][0] + dxa), snap(m.at[ref][1] + dya)), m.rot[ref]),
                       (other, (snap(m.at[other][0] - dxa), snap(m.at[other][1] - dya)), m.rot[other])]
        else:
            pts = []
            for n in m.part_nets[ref]:
                for r2, num in m.net_pins[n]:
                    if r2 != ref:
                        pts.append(pinpos[r2][num])
            if not pts:
                continue
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            b = m.box(ref)
            ox, oy = m.at[ref][0] - (b[0] + b[2]) / 2, m.at[ref][1] - (b[1] + b[3]) / 2
            at = (snap(cx + ox + rng.uniform(-2, 2)), snap(cy + oy + rng.uniform(-2, 2)))
            changes = [(ref, at, m.rot[ref])]
        res, old = try_apply(changes)
        if res is None:
            continue
        delta, new = res
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            cost.update(new)
            total += delta
            accepted += 1
        else:
            undo(old)
    # 3. repair: a movable part whose GND pad gets no fan-out (make_board.py gnd_fanout on the whole board) moves to the
    # nearest legal spot where every GND pad of the board fans out
    base = mps.build_placement()

    def fanout_failures():
        parts = []
        for p in base['parts']:
            if m.fixed[p['ref']]:
                parts.append(p)
            else:
                parts.append({**p, 'anchor': {'at': [r4(m.at[p['ref']][0]), r4(m.at[p['ref']][1])], 'align': 'origin',
                                              'rotation': float(m.rot[p['ref']]), 'side': m.side[p['ref']]}})
        failed = []
        sub = mb.Inputs({**base, 'parts': parts})
        mb.gnd_fanout(sub, mb.board_copper(base['pre_route'], sub)[0], first={r for r in m.refs if m.fixed[r]},
                      failed=failed)
        return sorted({r for r, _ in failed}, key=bg.sort_ref)
    repaired = []
    for _round in range(6):
        bad = fanout_failures()
        if not bad:
            break
        for ref in bad:
            here, rot0 = m.at[ref], m.rot[ref]
            grids[m.side[ref]].remove(ref, m.box(ref))
            fixed_it = False
            tried = 0
            for radius in [i * 0.5 for i in range(1, 30)]:
                n = max(8, int(radius * 8))
                for k in range(n):
                    ang = 2 * math.pi * k / n
                    at = (snap(here[0] + radius * math.cos(ang)), snap(here[1] + radius * math.sin(ang)))
                    if not legal(ref, at, rot0):
                        continue
                    m.at[ref] = at
                    pinpos[ref] = m.pins(ref)
                    tried += 1
                    if ref not in fanout_failures():
                        fixed_it = True
                        break
                    if tried >= 30:
                        break
                if fixed_it or tried >= 30:
                    break
            if not fixed_it:
                m.at[ref] = here
                pinpos[ref] = m.pins(ref)
            grids[m.side[ref]].add(ref, m.box(ref))
            repaired.append({'ref': ref, 'fixed': fixed_it, 'tries': tried})
    still = fanout_failures()
    if still:
        raise SystemExit(f'place_board: no GND fan-out for {still} after repair')
    final = sum(net_cost(n) for n in m.net_pins)
    rows = {}
    study_pos = {r['ref']: r for r in m.study['positions']['refs']}
    for ref in movable:
        s = study_pos[ref]
        if (r4(m.at[ref][0]), r4(m.at[ref][1])) != (r4(s['at'][0]), r4(s['at'][1])) or m.rot[ref] != int(s['rotation']) % 360:
            rows[ref] = {'at': [r4(m.at[ref][0]), r4(m.at[ref][1])], 'rotation': m.rot[ref], 'side': m.side[ref]}
    unweighted = 0.0
    for n, lst in m.net_pins.items():
        xs = [pinpos[r][num][0] for r, num in lst]
        ys = [pinpos[r][num][1] for r, num in lst]
        unweighted += (max(xs) - min(xs)) + (max(ys) - min(ys))
    return {
        'schema': 'srrx-pwra-board-placement-v1',
        'board_id': 'PWR_A',
        'status': 'MODEL placement input of W2 PCB-PWRA-4 (generated by place_board.py; never hand-edited)',
        'generator': 'build/kicad/boards/PWR_A/place_board.py',
        'inputs': {'spec_sha256': bg.sha256_bytes(bg.canonical(m.spec)),
                   'study_sha256': bg.sha256_bytes(bg.canonical(m.study)),
                   'pwr_b_h_trim_sha256': bg.sha256_bytes(bg.canonical(read(PWR_B_SPEC)['h_trim']))},
        'rules': {'seed': SEED, 'steps': STEPS, 'gap_mm': GAP, 'edge_inset_mm': EDGE_INSET, 'via_keep_mm': VIA_KEEP,
                  'weights': WEIGHT, 'fixed': 'anchors of PWR_A.spec-shrink2.json and parts with a PWR-B cut-out'},
        'cost': {'note': 'sum over the non-GND nets of the half-perimeter of the pin box (weighted by class), mm',
                 'planner': r4(start_cost), 'after_legalising': r4(legal_cost), 'final': r4(final),
                 'final_unweighted_hpwl_mm': r4(unweighted), 'accepted_moves': accepted},
        'legalised': sorted(moved_legal, key=bg.sort_ref),
        'fanout_repair': repaired,
        'fixed_fanout': m.fanout_fixed,
        'fixed_refs': sum(1 for r in m.refs if m.fixed[r]),
        'movable_refs': len(movable),
        'moved_refs': len(rows),
        'positions': dict(sorted(rows.items(), key=lambda kv: bg.sort_ref(kv[0]))),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args(argv)
    doc = place()
    text = json.dumps(doc, ensure_ascii=False, indent=2) + '\n'
    print(json.dumps(doc['cost']), f"moved {doc['moved_refs']} of {doc['movable_refs']}; legalised {doc['legalised']}")
    if args.check:
        if not OUT.is_file() or OUT.read_text(encoding='utf-8') != text:
            print(f'{OUT.name} is stale: rerun build/kicad/boards/PWR_A/place_board.py')
            return 1
        print(f'{OUT.name} reproduces')
        return 0
    bg.atomic_write(OUT, text)
    print(f'wrote {OUT.relative_to(BASE).as_posix()}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
