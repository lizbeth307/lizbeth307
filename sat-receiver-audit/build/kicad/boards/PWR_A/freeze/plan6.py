#!/usr/bin/env python3
"""Plan the scripted power copper of PWR_A before any route (W2 PWR-L6-SCRIPT). Needs numpy; offline tool, not run by CI.

  python build/kicad/boards/PWR_A/freeze/plan6.py [--nets N1,N2] [--out FILE]     write script-planned-6l.json
  python build/kicad/boards/PWR_A/freeze/plan6.py --verify                          margins of the scripted copper only

The board is the spec make_board.py writes without planned and frozen copper (pads at their board-placement.json places,
the SHRINK-2 pours as locked tracks, the W2 PWR-L6-SCRIPT converter copper, the GND fan-out). It is written as a minimal
KiCad board text (pads as their copper boxes: conservative for round and custom pads) and read with the freeze model of this
directory (model.py, router.py, fin.py: the PWR_B / CTRL toolkit). For every power-class net (BATT, PWR3A, PWR2A, PWR1A of
pcb/generated/netclasses.json with the 2 oz widths of the copper option) in class order, shortest span first:
  1. pin-entry pours for pads that a class-width track cannot reach: the pad's own cross-section extended at most half the
     class width beyond the pad (where pcb/check_boards.py counts copper as the pad), then a landing of the class width;
  2. grid A* links at the class width on F.Cu/B.Cu only (0.05 mm grid, exact clearance check, planning clearance 0.20 mm =
     project 0.15 + MARGIN 0.05, 0.35 mm to the outline), a high via cost per class, extra vias at each layer change up to
     the class vias_per_transition where they fit;
  3. low-current branches at 0.25 mm for pads whose role the exemption policy allows (test points, resistors of 100 ohm or more,
     sense or logic pins: pcb/check_boards.py exemption_role), recorded as branch_exempt rows.
Converter zones 3'/4' of the contract (thermal_bond zones 3 and 4) are keep-outs on F.Cu for every net that has no pad there
(the zone rule of W2 PWR-L6-SCRIPT). A net whose pads all join is kind 'power' (scripted class, never routed); otherwise
'link' (its locked copper stays, the router and freeze6 complete the rest). The guard is the SHA256 of the pads and of the
scripted copper the plan was made on; make_board.py refuses the file when either changed.
CI/model input only: KiCad DRC in a CI route run is the check; bench gates stay OPEN.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import math
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import model as M  # noqa: E402

COPPER = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
M.configure(COPPER, {'GND': 'In1.Cu'})
M.RLAYERS[:] = ['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu']
import fin as F  # noqa: E402
import router as R  # noqa: E402

F.BOARD_BOX = (100.0, 100.0, 236.0, 210.0)
OUT = HERE.parent / 'script-planned-6l.json'
K = lambda x, y: (round(x + 100.0, 4), round(210.0 - y, 4))  # board mm -> KiCad mm (frame of pcb/board_gen.py)
B = lambda p: [round(p[0] - 100.0, 4), round(210.0 - p[1], 4)]
OUTER = ('F.Cu', 'B.Cu')
POWER = ('BATT', 'PWR3A', 'PWR2A', 'PWR1A')
CLASS_ORDER = {c: i for i, c in enumerate(POWER)}
VIA_COST = {'BATT': 40.0, 'PWR3A': 20.0, 'PWR2A': 8.0, 'PWR1A': 4.0}   # mm of track per layer change (prefer one layer)
PLAN_CLR = 0.20     # mm: project clearance 0.15 + make_board MARGIN 0.05
PLAN_EDGE = 0.35    # mm: copper to the outline (EDGE + MARGIN)
BRANCH_W = 0.25     # mm, low-current branch width
BRANCH_MAX = 15.0   # mm
RASTER_MARGIN = 0.1  # mm wider links on nets with pin-entry pours (the neck raster of pcb/check_boards.py, grid 0.05)
STRIP_CLR = 0.16    # mm: a pin-entry strip continues its own pad (which keeps its land-pattern gap); the project clearance + 0.01


def planning_rules(clr=None):
    """The toolkit binds its clearance defaults at definition time (M.CLR 0.15): the planner uses PLAN_CLR and PLAN_EDGE
    (the second pass the project clearance RELAXED_CLR)."""
    clr = PLAN_CLR if clr is None else clr
    M.EDGE_CLR = PLAN_EDGE - 0.02
    M.Model.track_margin.__defaults__ = (clr, ())
    M.Model.via_margin.__defaults__ = (0.65, 0.3, clr, ())
    R.Grid.blocked_track.__defaults__ = (clr, None, (), None, ())
    R.Grid.blocked_via.__defaults__ = (R.VIA_D, R.VIA_DRILL, clr, None, (), None, ())
    R.simplify.__defaults__ = (clr + 0.005, ())


_COVERED = R.Grid.covered


def covered_inside(self, items, layer):
    """Grid.covered with every pad of the footprints eroded by one cell: a planned track ends at least a grid step inside the
    pad copper, never on its edge (W2 PWR-L6-SCRIPT)."""
    pads = [it for it in items if it.kind == 'pad' and it.src == 'pad']
    cov = _COVERED(self, [it for it in items if not (it.kind == 'pad' and it.src == 'pad')], layer)
    for it in pads:
        cp = _COVERED(self, [it], layer)
        er = cp.copy()
        er[1:, :] &= cp[:-1, :]
        er[:-1, :] &= cp[1:, :]
        er[:, 1:] &= cp[:, :-1]
        er[:, :-1] &= cp[:, 1:]
        cov |= er if er.any() else cp
    return cov


R.Grid.covered = covered_inside
RELAXED_CLR = 0.155  # mm: second pass for the links the first pass left open, at the project clearance 0.15 (+5 um)


def load_make_board():
    loader = importlib.util.spec_from_file_location('pwr_a_make_board', HERE.parent / 'make_board.py')
    mb = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(mb)
    return mb


def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def pad_shapes(mb, inp):
    """ref -> [(shape, roundrect ratio)] of the copper pads in the order make_board.Inputs keeps them (pad_copper filter)."""
    out = {}
    for t in inp.template:
        text = mb.bg.footprint_file(t).read_text(encoding='utf-8')
        nodes = [n for n in mb.bg.sexpr(text)[1:] if isinstance(n, list) and n and n[0] == 'pad']
        keep = []
        for node, (cu, _box) in zip(nodes, mb.pad_copper(text)):
            if cu or node[2] == 'np_thru_hole':
                rr = next((float(k[1]) for k in node if isinstance(k, list) and k and k[0] == 'roundrect_rratio'), 0.25)
                keep.append((str(node[3]) if len(node) > 3 else 'rect', rr))
        out[t['ref']] = keep
    return out


def board_text(spec, inp, shapes=None):
    """Minimal KiCad board text of the pre-route spec: pads (their footprint shape over their copper box: circle, oval,
    roundrect, else the box), scripted tracks, vias and inner pours, hole keep-outs and the outline (KiCad mm)."""
    pre = spec['pre_route']
    shapes = shapes or {}
    nets = sorted({p['net'] for pa in inp.parts.values() for p in pa.pads if p['net']} | {t['net'] for t in pre['tracks']}
                  | {v['net'] for v in pre['vias']} | {z['net'] for z in pre['zones']})
    nid = {n: i + 1 for i, n in enumerate(nets)}
    L = ['(kicad_pcb (version 20250114) (generator "plan6")',
         ' (layers (0 "F.Cu" signal) (4 "In1.Cu" signal) (6 "In2.Cu" signal) (8 "In3.Cu" signal) (10 "In4.Cu" signal) '
         '(2 "B.Cu" signal) (25 "Edge.Cuts" user))', ' (net 0 "")'] + [f' (net {nid[n]} {q(n)})' for n in nets]
    for ref, pa in sorted(inp.parts.items()):
        L.append(f' (footprint "plan6:{ref}" (layer "{pa.side}.Cu") (at 0 0) (property "Reference" {q(ref)})')
        sh = shapes.get(ref) or []
        for k, p in enumerate(pa.pads):
            kind, rr = sh[k] if k < len(sh) else ('rect', 0.25)
            form = {'circle': 'circle', 'oval': 'oval', 'roundrect': 'roundrect'}.get(kind, 'rect')
            extra = f' (roundrect_rratio {rr})' if form == 'roundrect' else ''
            if form == 'circle':
                x0, y0, x1, y1 = p['box']
                if abs((x1 - x0) - (y1 - y0)) > 1e-6:
                    form = 'oval'
            p = dict(p)
            x0, y0, x1, y1 = p['box']
            k0, k1 = K(x0, y1), K(x1, y0)
            cx, cy, w, h = (k0[0] + k1[0]) / 2, (k0[1] + k1[1]) / 2, k1[0] - k0[0], k1[1] - k0[1]
            net = f' (net {nid[p["net"]]} {q(p["net"])})' if p['net'] else ''
            if p['type'] == 'np_thru_hole':
                d = p['drill'][0] if p['drill'] else min(w, h)
                L.append(f'  (pad "" np_thru_hole circle (at {cx:.4f} {cy:.4f}) (size {d:.4f} {d:.4f}) (drill {d:.4f}) (layers "*.Cu"))')
            elif p['type'] == 'thru_hole':
                d = p['drill'][0] if p['drill'] else min(w, h) * 0.6
                L.append(f'  (pad {q(p["number"])} thru_hole {form} (at {cx:.4f} {cy:.4f}) (size {w:.4f} {h:.4f}) (drill {d:.4f}) '
                         f'(layers "*.Cu"){extra}{net})')
            else:
                L.append(f'  (pad {q(p["number"])} smd {form} (at {cx:.4f} {cy:.4f}) (size {w:.4f} {h:.4f}) (layers "{pa.side}.Cu")'
                         f'{extra}{net})')
        L.append(' )')
    for t in pre['tracks']:
        for a, b in zip(t['path'], t['path'][1:]):
            ka, kb = K(*a), K(*b)
            L.append(f' (segment (start {ka[0]} {ka[1]}) (end {kb[0]} {kb[1]}) (width {t["width_mm"]}) (layer "{t["layer"]}") '
                     f'(net {nid[t["net"]]}) (locked yes))')
    for v in pre['vias']:
        k = K(*v['at'])
        L.append(f' (via (at {k[0]} {k[1]}) (size {v["diameter_mm"]}) (drill {v["drill_mm"]}) (layers "F.Cu" "B.Cu") '
                 f'(net {nid[v["net"]]}) (locked yes))')
    for z in pre['zones']:
        if z['outline'] == 'board' or z['net'] == 'GND':
            continue
        pts = ' '.join(f'(xy {K(*p)[0]} {K(*p)[1]})' for p in z['outline'])
        L.append(f' (zone (net {nid[z["net"]]}) (net_name {q(z["net"])}) (layer "{z["layer"]}") (name {q(z["id"])}) '
                 f'(polygon (pts {pts})) (filled_polygon (layer "{z["layer"]}") (pts {pts})))')
    c = inp.contract
    for i, (hx, hy) in enumerate(c['holes_mm']):
        k = K(hx, hy)
        rr = c['hole_keepout_d'] / 2
        pts = ' '.join(f'(xy {k[0] + rr * math.cos(2 * math.pi * j / 48):.4f} {k[1] + rr * math.sin(2 * math.pi * j / 48):.4f})'
                       for j in range(48))
        L.append(f' (zone (net 0) (net_name "") (layers "F.Cu" "In1.Cu" "In2.Cu" "In3.Cu" "In4.Cu" "B.Cu") (name "HOLE{i + 1}") '
                 f'(keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints allowed)) '
                 f'(polygon (pts {pts})))')
    for z in spec.get('post_route_zones', []):  # B.Cu GND bond copper of the thermal_bond zones (+ 0.3): no other copper
        if z['net'] == 'GND' and z['layer'] == 'B.Cu' and z['outline'] != 'board':
            xs, ys = [p[0] for p in z['outline']], [p[1] for p in z['outline']]
            box = (min(xs) - 0.3, min(ys) - 0.3, max(xs) + 0.3, max(ys) + 0.3)
            pts = ' '.join(f'(xy {K(*p)[0]} {K(*p)[1]})' for p in ((box[0], box[1]), (box[2], box[1]), (box[2], box[3]), (box[0], box[3])))
            L.append(f' (zone (net 0) (net_name "") (layers "B.Cu") (name "BOND-{z["id"]}") (keepout (tracks not_allowed) '
                     f'(vias allowed) (pads allowed) (copperpour allowed) (footprints allowed)) (polygon (pts {pts})))')
    o = [K(*p) for p in c['outline_mm']]
    for a, b in zip(o, o[1:] + o[:1]):
        L.append(f' (gr_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.05) (type solid)) (layer "Edge.Cuts"))')
    L.append(')')
    return '\n'.join(L) + '\n'


def script_guard(mb, inp, pre):
    """The guard make_board.py compares: pads and the scripted tracks, vias and pours the plan was made on."""
    g = mb.frozen_guard(inp, pre['tracks'], pre['vias'])
    zones = sorted(json.dumps({k: v for k, v in z.items() if k != 'why'}, sort_keys=True) for z in pre['zones'])
    g['zones_sha256'] = hashlib.sha256('\n'.join(zones).encode()).hexdigest()
    return g


class Planner:
    def __init__(self, mb, log=print):
        self.mb, self.log = mb, log
        self.spec, self.inp, problems, _nets = mb.build(frozen=False, planned=False)
        if problems:
            raise SystemExit('plan6: make_board problems: ' + '; '.join(problems[:5]))
        self.pre = self.spec['pre_route']
        self.tmp = Path(tempfile.mkdtemp(prefix='plan6-'))
        path = self.tmp / 'PWR_A-plan6.kicad_pcb'
        path.write_text(board_text(self.spec, self.inp, pad_shapes(mb, self.inp)), encoding='utf-8')
        self.m = M.Model(str(path))
        self.base_keepouts = list(self.m.keepouts)
        nc = self.inp.netclasses
        self.cls = {n: v['class'] for n, v in nc['nets'].items()}
        self.classes = nc['classes']
        self.fz = F.Finisher(self.m, log=lambda *a: None)
        cb = mb.bg  # pcb/board_gen; check_boards for the exemption roles
        sys.path.insert(0, str(mb.BASE / 'pcb'))
        import check_boards as CB
        self.CB = CB
        self.cboard = CB.Board(CB.parse(path.read_text(encoding='utf-8')), path)
        self.graph = CB.load_graph()
        self.lookup = lambda n: (n, self.cls.get(n, 'SIG'))
        zones = self.inp.contract['thermal_bond_mm']
        self.conv = {}
        for zi in (3, 4):
            x, y, w, h = zones[zi - 1]
            box = (x, y, x + w, y + h)
            own = {p['net'] for pa in self.inp.parts.values() for p in pa.pads if p['net']
                   and box[0] <= p['at'][0] <= box[2] and box[1] <= p['at'][1] <= box[3]} | {'GND'}
            self.conv[zi] = (box, own)

    # ---------------------------------------------------------------- geometry helpers (KiCad mm)
    def width(self, net):
        return self.classes[self.cls[net]]['outer_min_width_mm']

    def zone_keepouts(self, net):
        """F.Cu keep-outs of the converter zones 3'/4' for a net without a pad there (W2 PWR-L6-SCRIPT zone rule)."""
        out = []
        for zi, (box, own) in self.conv.items():
            if net in own:
                continue
            k0, k1 = K(box[0], box[3]), K(box[2], box[1])
            out.append({'layers': ['F.Cu', 'In1.Cu'], 'poly': M.cb.Poly([(k0[0], k0[1]), (k1[0], k0[1]), (k1[0], k1[1]), (k0[0], k1[1])]),
                        'name': f'converter zone {zi}'})
        return out

    def pads_of(self, net):
        return [it for it in self.m.items if it.alive and it.kind == 'pad' and it.net == net and it.src == 'pad']

    def reachable(self, net, pad, w):
        """A class-width disc fits on a cell of the pad (on one of its outer layers)."""
        lays = [l for l in pad.layers if l in OUTER]
        x0, y0, x1, y1 = pad.bbox
        pts = [((x0 + x1) / 2, (y0 + y1) / 2)]
        nx, ny = max(1, int((x1 - x0) / 0.1)), max(1, int((y1 - y0) / 0.1))
        pts += [(x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny) for i in range(nx + 1) for j in range(ny + 1)]
        for lay in lays:
            for p in pts:
                if pad.shape.dist(*p) > 0:
                    continue
                if self.m.track_margin(net, lay, w, p, p, clr=PLAN_CLR)[0] >= 0:
                    return True
        return False

    def entry_pour(self, net, pad, w):
        """A pin-entry pour for a pad that a class-width track cannot reach: the pad's cross-section extended e <= w/2 beyond the
        pad in one axis direction, then a w x w landing (both clear of other nets by PLAN_CLR). Returns (layer, rects KiCad) or None."""
        x0, y0, x1, y1 = pad.bbox
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        best = None
        for lay in [l for l in pad.layers if l in OUTER]:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                for k in range(0, int(w / 2 / 0.05) + 1):
                    e = k * 0.05
                    if dx:
                        edge = x1 if dx > 0 else x0
                        sx0, sx1 = sorted((edge, edge + dx * e))
                        strip = (sx0, y0, sx1, y1) if e else None
                        lx = edge + dx * (e + w / 2)
                        land = (lx - w / 2, cy - w / 2, lx + w / 2, cy + w / 2)
                        axis = ((cx, cy), (lx, cy))
                        cross = y1 - y0
                    else:
                        edge = y1 if dy > 0 else y0
                        sy0, sy1 = sorted((edge, edge + dy * e))
                        strip = (x0, sy0, x1, sy1) if e else None
                        ly = edge + dy * (e + w / 2)
                        land = (cx - w / 2, ly - w / 2, cx + w / 2, ly + w / 2)
                        axis = ((cx, cy), (cx, ly))
                        cross = x1 - x0
                    # the landing: a class-width disc at its centre and the square around it clear of other nets
                    lc = ((land[0] + land[2]) / 2, (land[1] + land[3]) / 2)
                    if self.m.track_margin(net, lay, w * math.sqrt(2) + 1e-3, lc, lc, clr=PLAN_CLR)[0] < 0:
                        continue
                    if strip and not self.rect_clear(net, lay, strip, clr=STRIP_CLR):
                        continue
                    if not self.rect_clear(net, lay, land):
                        continue
                    cand = (e, lay, [r for r in ((x0, y0, x1, y1), strip, land) if r], (round(e, 4), [round(w, 4), round(w, 4)]))
                    if best is None or cand[0] < best[0]:
                        best = cand
                    break
        return (best[1], best[2], best[3]) if best else None

    def rect_clear(self, net, lay, rect, clr=PLAN_CLR):
        """Exact clearance of an axis-aligned rectangle (KiCad mm) against other-net copper, keep-outs and the outline."""
        poly = M.cb.Poly([(rect[0], rect[1]), (rect[2], rect[1]), (rect[2], rect[3]), (rect[0], rect[3])])
        bb = (rect[0] - 1, rect[1] - 1, rect[2] + 1, rect[3] + 1)
        for it in self.m.near(lay, bb):
            if it.net == net and it.kind != 'npth':
                continue
            for e0, e1 in poly.edges:
                if M.shape_seg_dist(it.shape, e0, e1) < clr + (0.1 if it.kind == "npth" else 0.0):
                    return False
            if poly.contains(*((it.bbox[0] + it.bbox[2]) / 2, (it.bbox[1] + it.bbox[3]) / 2)):
                return False
        for kz in self.m.keepouts:
            if lay in kz['layers']:
                for e0, e1 in poly.edges:
                    if M.shape_seg_dist(kz['poly'], e0, e1) < 0.01:
                        return False
        for e0, e1 in poly.edges:
            if self.m.edge_dist_seg(e0, e1) < PLAN_EDGE:
                return False
        return all(self.m.inside(p) for p in poly.pts)

    def add_zone(self, net, lay, rects, zid):
        shapes = [M.cb.Poly([(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]) for r in rects]
        shape = shapes[0] if len(shapes) == 1 else M.cb.Multi(shapes)
        bx = shape.bbox
        it = self.m.add(M.Item(kind='pad', net=net, layers=[lay], shape=shape, ref='ZONE', pad=zid,
                               at=((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2), drill=0.0, locked=True, src='zone'))
        return it

    def via_cluster(self, net, w, need):
        """Extra vias around each new via of the net (layer change) up to `need` vias, joined on F.Cu and B.Cu at width w."""
        added = []
        for v in [it for it in self.m.items if it.alive and it.kind == 'via' and it.net == net and it.src == 'new']:
            have = 1 + sum(1 for a in added if a[0] == v.at)
            for ring in (0.95, 1.25, 1.6):
                for k in range(8):
                    if have >= need:
                        break
                    ang = 2 * math.pi * k / 8
                    p = (round(v.at[0] + ring * math.cos(ang), 4), round(v.at[1] + ring * math.sin(ang), 4))
                    if self.m.via_margin(net, p, R.VIA_D, R.VIA_DRILL, clr=PLAN_CLR)[0] < 0:
                        continue
                    if any(self.m.track_margin(net, lay, w, v.at, p, clr=PLAN_CLR)[0] < 0 for lay in OUTER):
                        continue
                    self.m.add_via(net, p, R.VIA_D, R.VIA_DRILL, src='new')
                    for lay in OUTER:
                        self.m.add_track(net, lay, w, v.at, p, src='new')
                    added.append((v.at, p))
                    have += 1
        return added

    # ---------------------------------------------------------------- planning
    def plan_net(self, net):
        cname = self.cls[net]
        w = self.width(net)
        need_v = int(self.classes[cname].get('vias_per_transition') or 1)
        self.m.keepouts[:] = self.base_keepouts + self.zone_keepouts(net)
        rec = {'class': cname, 'width_mm': w, 'zones': [], 'branches': [], 'log': []}
        try:
            # 1. entry pours
            for k, pad in enumerate(sorted(self.pads_of(net), key=lambda p: (p.ref, p.pad))):
                if self.reachable(net, pad, w) or pad.drill:
                    continue
                ep = self.entry_pour(net, pad, w)
                if ep is None:
                    rec['log'].append(f'no entry pour for {pad.ref}.{pad.pad}')
                    continue
                lay, rects, (strip, landing) = ep
                zid = f'PE-{net}-{pad.ref}.{pad.pad}'
                self.add_zone(net, lay, rects, zid)
                rec['zones'].append({'id': zid, 'pad': f'{pad.ref}.{pad.pad}', 'layer': lay, 'strip_mm': strip, 'landing_mm': landing,
                                     'rects': [[*B((r[0], r[3])), *B((r[2], r[1]))] for r in rects]})
            # 2. class-width links (no rip-up: only scripted copper exists); a net with pin-entry pours is checked by the 0.05 mm neck
            # raster of pcb/check_boards.py over its pours, which reads a diagonal track of exactly the class width up to a cell
            # narrower: its links take RASTER_MARGIN more
            w_link = round(w + RASTER_MARGIN, 4) if rec['zones'] else w
            rec['link_width_mm'] = w_link
            ok, _ripped, _necks = self.fz.connect_all(net, allow_rip=False, width=w_link, layers=OUTER, via_cost=VIA_COST[cname],
                                                    neck=None, max_links=60)
            if not ok:  # second pass: the project clearance and a 0.1 mm grid (wider search boxes for the long links)
                planning_rules(RELAXED_CLR)
                try:
                    ok, _ripped, _necks = self.fz.connect_all(net, allow_rip=False, width=w_link, layers=OUTER, via_cost=VIA_COST[cname],
                                                            neck=None, max_links=60, g=0.1)
                finally:
                    planning_rules()
                rec['log'].append(f'second pass (clearance {RELAXED_CLR} mm, grid 0.1 mm): {"joined" if ok else "still open"}')
            # 3. low-current branches of the allowed roles
            if not ok:
                CB = self.CB

                def allowed(ref):
                    pads = [p for p in self.cboard.pads if p['ref'] == ref and p['net'] == net]
                    return bool(pads) and all(CB.exemption_role(self.cboard, {'b2b': self.spec.get('b2b', [])}, self.graph, ref, p['number'],
                                                                self.lookup, self.classes)[0] in CB.EXEMPT_BRANCH_ROLES for p in pads)
                okb, br = self.fz.branch_pass(net, allowed, lambda refs: BRANCH_W, lambda refs: OUTER, BRANCH_MAX)
                rec['branches'] = br
                ok = ok or okb
            rec['via_cluster'] = len(self.via_cluster(net, w, need_v))
        finally:
            self.m.keepouts[:] = self.base_keepouts
        isl = [g for g in self.m.islands(net) if any(i.kind == 'pad' for i in g) or len(g) > 1]
        rec['open'] = max(0, len(isl) - 1)
        rec['open_islands'] = [sorted(f'{i.ref}.{i.pad}' for i in g if i.kind == 'pad' and i.src == 'pad') for g in isl] if len(isl) > 1 else []
        rec['kind'] = 'power' if rec['open'] == 0 else 'link'
        return rec

    def harvest(self, net):
        """The new copper of a net (tracks as chains, board mm) for the plan file."""
        segs = collections.defaultdict(list)
        vias = []
        for it in self.m.items:
            if not (it.alive and it.net == net and it.src == 'new'):
                continue
            if it.kind == 'track':
                segs[(it.layers[0], round(it.width, 4))].append((it.a, it.b))
            elif it.kind == 'via':
                vias.append([*B(it.at), round(it.size, 4), round(it.drill, 4)])
        tracks = []
        for (lay, w), ss in sorted(segs.items()):
            for a, b in ss:
                tracks.append([lay, w, B(a), B(b)])
        return sorted(tracks), sorted(vias)


def span(m, net):
    pts = [i.at for i in m.items if i.alive and i.kind == 'pad' and i.net == net]
    return math.hypot(max(p[0] for p in pts) - min(p[0] for p in pts), max(p[1] for p in pts) - min(p[1] for p in pts)) if pts else 0.0


def verify(pl):
    """Exact margins at the project clearance 0.15 mm of the W2 PWR-L6-SCRIPT copper on the planning board: the SC- converter copper
    of the spec (matched by geometry) and the planned copper (src new). The planning-only keep-outs (B.Cu bond zones, converter
    zones) are left out; pads count as their copper boxes (conservative)."""
    keys = set()
    for t in pl.pre['tracks']:
        if t['id'].startswith('SC-'):
            for a, b in zip(t['path'], t['path'][1:]):
                keys.add(('track', t['net'], t['layer'], tuple(K(*a)), tuple(K(*b))))
    for v in pl.pre['vias']:
        if v['id'].startswith('SC-'):
            keys.add(('via', v['net'], tuple(K(*v['at']))))
    saved = list(pl.m.keepouts)
    pl.m.keepouts[:] = [k for k in pl.base_keepouts if not k['name'].startswith('BOND-')]
    bad = []
    try:
        for it in pl.m.items:
            if not it.alive:
                continue
            if it.kind == 'track':
                key = ('track', it.net, it.layers[0], (round(it.a[0], 4), round(it.a[1], 4)), (round(it.b[0], 4), round(it.b[1], 4)))
                if it.src != 'new' and key not in keys:
                    continue
                mg, why = pl.m.track_margin(it.net, it.layers[0], it.width, it.a, it.b, clr=0.15, ignore={it.id})
            elif it.kind == 'via':
                if it.src != 'new' and ('via', it.net, (round(it.at[0], 4), round(it.at[1], 4))) not in keys:
                    continue
                mg, why = pl.m.via_margin(it.net, it.at, it.size, it.drill, clr=0.15, ignore={it.id})
            else:
                continue
            if mg < -0.0005:
                bad.append((round(mg, 4), it.kind, it.net, B(it.a or it.at), why))
    finally:
        pl.m.keepouts[:] = saved
    return bad


def drop_failing(pl):
    """Remove planned items (src new) below the project clearance, then prune each touched net (dangling copper goes too)."""
    out = []
    saved = list(pl.m.keepouts)
    pl.m.keepouts[:] = [k for k in pl.base_keepouts if not k['name'].startswith('BOND-')]
    try:
        for it in pl.m.items:
            if not (it.alive and it.src == 'new'):
                continue
            if it.kind == 'track':
                mg, _w = pl.m.track_margin(it.net, it.layers[0], it.width, it.a, it.b, clr=0.15, ignore={it.id})
            elif it.kind == 'via':
                mg, _w = pl.m.via_margin(it.net, it.at, it.size, it.drill, clr=0.15, ignore={it.id})
            else:
                continue
            if mg < -0.0005:
                pl.m.remove(it)
                out.append((it.kind, it.net, B(it.a or it.at)))
    finally:
        pl.m.keepouts[:] = saved
    for net in sorted({o[1] for o in out}):
        F.prune(pl.m, net, srcs=('new',), log=lambda *a: None)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--nets', help='comma-separated nets (default: every power-class net with pads on the board)')
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--verify', action='store_true', help='only report the margins of the scripted copper')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')
    mb = load_make_board()
    t0 = time.time()
    pl = Planner(mb)
    if not args.verify:
        planning_rules()
    print(f'planning board: {len(pl.m.items)} items ({time.time() - t0:.1f} s)')
    if args.verify:
        bad = verify(pl)
        print('scripted copper below the project clearance:', len(bad))
        for b in bad[:40]:
            print('  ', b)
        return 1 if bad else 0
    power = sorted({it.net for it in pl.m.items if it.alive and it.kind == 'pad' and it.net and pl.cls.get(it.net) in POWER})
    nets = args.nets.split(',') if args.nets else power
    todo = [n for n in nets if len([g for g in pl.m.islands(n) if any(i.kind == 'pad' for i in g)]) > 1]
    todo.sort(key=lambda n: (CLASS_ORDER[pl.cls[n]], round(span(pl.m, n), 3), n))
    print('nets to plan:', len(todo), 'of', len(nets))
    plan = {}
    for net in todo:
        t1 = time.time()
        rec = pl.plan_net(net)
        rec['tracks'], rec['vias'] = pl.harvest(net)
        plan[net] = rec
        print(f'{net} ({rec["class"]} {rec["width_mm"]} mm): {rec["kind"]}, open {rec["open"]}, zones {len(rec["zones"])}, '
              f'branches {len(rec["branches"])}, vias {len(rec["vias"])} (+{rec["via_cluster"]} cluster), {time.time() - t1:.0f} s', flush=True)
        if rec['open_islands']:
            print('    open:', [g[:4] for g in rec['open_islands']])
        for line in rec['log']:
            print('   ', line)
    bad = verify(pl)
    if bad:  # drop planned copper that fails the exact final check at 0.15 mm (its joins stay open) and re-harvest
        dropped = drop_failing(pl)
        print('dropped planned items after the final check:', dropped)
        for net in sorted({d[1] for d in dropped}):
            rec = plan[net]
            rec['tracks'], rec['vias'] = pl.harvest(net)
            isl = [g for g in pl.m.islands(net) if any(i.kind == 'pad' for i in g) or len(g) > 1]
            rec['open'] = max(0, len(isl) - 1)
            rec['open_islands'] = [sorted(f'{i.ref}.{i.pad}' for i in g if i.kind == 'pad' and i.src == 'pad') for g in isl] if len(isl) > 1 else []
            rec['kind'] = 'power' if rec['open'] == 0 else 'link'
        bad = verify(pl)
    result = {'nets': len(plan), 'power': sorted(n for n, r in plan.items() if r['kind'] == 'power'),
              'link': {n: r['open'] for n, r in sorted(plan.items()) if r['kind'] == 'link'}, 'violations': len(bad)}
    print('result:', json.dumps(result))
    for b in bad[:20]:
        print('  violation', b)
    doc = {
        'schema': 'srrx-pwra-script-plan-v1',
        'label': 'MODEL plan of the PWR_A scripted power copper (W2 PWR-L6-SCRIPT); not a hardware PASS; bench gates OPEN',
        'source': {'tool': 'build/kicad/boards/PWR_A/freeze/plan6.py', 'board': 'make_board.py build(frozen=False, planned=False)',
                   'rules': f'grid A* 0.05 mm, clearance {PLAN_CLR} mm, outline {PLAN_EDGE} mm, power classes on F.Cu/B.Cu at the 2 oz '
                            'widths, via cost per class, converter zones 3/4 kept free of foreign nets on F.Cu'},
        'guard': script_guard(mb, pl.inp, pl.pre),
        'result': result,
        'nets': {n: {k: r[k] for k in ('kind', 'class', 'width_mm', 'open', 'open_islands', 'zones', 'branches', 'tracks', 'vias')}
                 for n, r in sorted(plan.items())},
    }
    text = json.dumps(doc, ensure_ascii=False, indent=1) + '\n'
    Path(args.out).write_text(text, encoding='utf-8', newline='\n')
    print('wrote', args.out, f'({time.time() - t0:.0f} s)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
