"""Solid interference check on the CAD parts (MODEL FIT ONLY).

The box check in layout.py compares envelopes with each other and with a few
structure boxes. This check intersects every envelope with the real B-rep of
the shells, plate, angles, RF bay, pedestal, bosses and tray, so wall radii,
the seam belt, bosses, webs, pads and seats are all seen. An overlap is a
conflict unless it lies inside a feature that the item is designed to touch
(a board on its standoffs, the Lime on its pedestal). Envelopes are reserves,
not vendor geometry: a clean result is a model fit only.
"""
import itertools

from build123d import Align, Box, Cylinder, Pos

from .layout import item_boxes

MIN3 = (Align.MIN, Align.MIN, Align.MIN)
TOL_MM3 = 0.5

# item id -> solids or named features it may overlap by design
ALLOWED = {
    "board_ctrl": {"front.ctrl_bosses"},
    "enc_main": {"front.enc_bosses"},
    "enc_volume": {"front.enc_bosses"},
    "lime": {"lime_pedestal"},                 # the Lime envelope starts at the plate and includes its pedestal
    "q6a": {"ufs_boss"},                       # contact through the UFS pad (thermal row T-UFS)
    "tripod_boss": {"rear.tripod_boss", "rear.module_bosses"},  # this envelope is the boss itself; W2 MECH-5: the CH334F and INA228 bosses rise from its rim
    "gx16": {"rear.gx16_pad"},                 # the socket nut sits on its seat
    "hatch_parts": {"rear.hatch_seat", "hatch_cover"},
    "battery_pack": {"battery_tray"},          # the pack lies in its tray (the tray solid is checked separately)
    "veml7700": {"front.veml_bosses"},         # W2 MECH-5: the board rests on its bosses in the top-wall pocket
}
SKIP_ITEMS = {"battery_tray"}                  # represented by its solid, not by its envelope box

# Every pair of structure solids is checked solid against solid: fastened parts only touch, so any volume above
# TOL_MM3 is a conflict (no pair is skipped because the parts are screwed together).
def struct_pairs(solids):
    return list(itertools.combinations(sorted(solids), 2))


def _box(b):
    return Pos(b[0], b[1], b[2]) * Box(b[3] - b[0], b[4] - b[1], b[5] - b[2], align=MIN3)


def _vol(shape):
    try:
        return shape.volume
    except Exception:          # empty intersection
        return 0.0


def _bb(shape):
    bb = shape.bounding_box()
    return [round(v, 1) + 0.0 for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)]


def check(P, solids, features):
    """solids: {name: final part}; features: {'front.<name>' | 'rear.<name>': [solids]}. Returns rows of conflicts and a summary."""
    rows, allowed_hits = [], []
    for iid, name, bx, it in item_boxes(P):
        if iid in SKIP_ITEMS:
            continue
        env = _box(bx)
        ok = ALLOWED.get(iid, set())
        for sname, solid in solids.items():
            inter = env & solid
            v = _vol(inter)
            if v <= TOL_MM3:
                continue
            explained = 0.0
            for f in ok:
                if f == sname:
                    explained = v
                    break
                if f in features and f.split(".")[0] == {"front_shell": "front", "rear_shell": "rear"}.get(sname):
                    for fs in features[f]:
                        explained += _vol(inter & fs)
            rest = v - explained
            row = {"item": name, "solid": sname, "overlap_mm3": round(v, 1), "by_design_mm3": round(min(explained, v), 1), "bbox_mm": _bb(inter)}
            if rest > TOL_MM3:
                row["result"] = "FAIL (model)"
                rows.append(row)
            else:
                row["result"] = "BY DESIGN (model)"
                allowed_hits.append(row)
    pairs = struct_pairs(solids)
    for a, b in pairs:
        inter = solids[a] & solids[b]
        v = _vol(inter)
        if v > TOL_MM3:
            rows.append({"item": a, "solid": b, "overlap_mm3": round(v, 1), "bbox_mm": _bb(inter), "result": "FAIL (model)"})
    return {"method": "B-rep intersection of every envelope with the shells, plate, angles, RF bay, pedestal, UFS boss, tray, hatch, hood and T7 holder; "
                      f"all {len(pairs)} pairs of these solids against each other; overlaps above {TOL_MM3} mm3 outside by-design features fail",
            "conflicts": rows, "by_design": allowed_hits,
            "result": "PASS (model fit only)" if not rows else f"FAIL (model): {len(rows)} conflicts"}


def _zcyl(x, y, z0, z1, r):
    return Pos(x, y, min(z0, z1)) * Cylinder(r, abs(z1 - z0), align=(Align.CENTER, Align.CENTER, Align.MIN))


def _outside_envelopes(P):
    return {name: _box(bx) for iid, name, bx, it in item_boxes(P) if it.get("outside")}


def access(P, solids):
    """R-TOOL-ACCESS: every closure, hatch and T7-holder screw has a clear tool path from outside.

    Tool path = the counterbore (closure screws) from the head seat to the outer face, then a cylinder of
    closure.tool_d for 60 mm outside. A removable outside part (T7 holder, hatch cover) may cover a closure screw only
    if its own screws are clear; anything else in the path (a lug, a tunnel, a fixed boss) fails."""
    m = P.mech
    c = m["closure"]
    rf = m["rear_face"]
    tool_r = c["tool_d"] / 2.0
    tcov = m["gasket"]["groove_depth"] + 2.2
    th = rf["t7_holder"]
    depth = th["gap"] + P.parts["t7"]["size"][2] + th["shutter_t"]
    groups = {"closure": [(f"CLOSURE_{i + 1}", bx, by, c["counterbore_depth"], 0.0, c["counterbore_d"] / 2) for i, (bx, by) in enumerate(c["bosses"])],
              "hatch_cover": [(f"HATCH_M3_{i + 1}", sx, sy, -tcov, -tcov, None) for i, (sx, sy) in enumerate(rf["hatch"]["screws"])],
              "t7_holder": [(f"T7_M3_{i + 1}", px, py, -depth, -depth, None) for i, (px, py) in enumerate(th["screws"])]}
    blockers = {k: v for k, v in solids.items() if k in ("rear_shell", "hatch_cover", "t7_holder", "hood")}
    blockers.update(_outside_envelopes(P))
    removable = ("hatch_cover", "t7_holder")
    found = {}
    for g, screws in groups.items():
        for sid, x, y, z_seat, z_face, rcb in screws:
            path = _zcyl(x, y, z_face - 60.0, z_face, tool_r)
            if rcb:
                path = path + _zcyl(x, y, z_face - 0.01, z_seat - 0.05, rcb - 0.05)
            hit = []
            for name, solid in blockers.items():
                if name == g:
                    continue
                if _vol(path & solid) > TOL_MM3:
                    hit.append(name)
            found[sid] = (g, hit)
    rows, bad = [], []
    own_clear = {g: all(not found[sid][1] for sid, *_ in groups[g]) for g in removable}
    for sid, (g, hit) in found.items():
        fixed = [h for h in hit if h not in removable or not own_clear[h]]
        if fixed:
            bad.append(f"{sid}: {', '.join(fixed)}")
        elif hit:
            rows.append(f"{sid}: remove {', '.join(hit)} first")
    return {"id": "R-TOOL-ACCESS", "rule": f"every closure, hatch and T7-holder screw: clear tool path (counterbore, then d {c['tool_d']} for 60 mm) from outside",
            "value_mm": bad or (rows or "all clear"), "limit_mm": "no fixed solid in a tool path; removable parts only over closure screws",
            "result": "FAIL (model): " + "; ".join(bad) if bad else "PASS (model)",
            "source": "mechanical.json closure, rear_face.hatch, rear_face.t7_holder; B-rep of the rear shell, hatch cover, T7 holder, hood"}


def tripod_disc(P, solids):
    """R-TRIPOD-DISC: nothing stands prouder than the tripod plinth inside the plate disc."""
    tp = P.mech["rear_face"]["tripod"]
    tx, ty = tp["c"]
    ph = tp["plinth_h"]
    disc = _zcyl(tx, ty, -ph - 80.0, -ph - 0.01, tp["plate_disc_d"] / 2)
    blockers = {k: v for k, v in solids.items() if k in ("rear_shell", "hatch_cover", "t7_holder")}
    blockers.update(_outside_envelopes(P))
    hit = sorted(k for k, v in blockers.items() if _vol(disc & v) > TOL_MM3)
    return {"id": "R-TRIPOD-DISC", "rule": f"tripod plate disc d {tp['plate_disc_d']} about the 1/4-20: no solid prouder than the plinth face ({ph} mm)",
            "value_mm": hit or "none", "limit_mm": f"plinth d {tp['plinth_d']}, {ph} proud",
            "result": "FAIL (model): " + ", ".join(hit) if hit else "PASS (model)",
            "source": "mechanical.json rear_face.tripod; B-rep of the rear shell, hatch cover, T7 holder; outside envelopes"}
