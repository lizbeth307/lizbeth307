"""Solid interference check on the CAD parts (MODEL FIT ONLY).

The box check in layout.py compares envelopes with each other and with a few
structure boxes. This check intersects every envelope with the real B-rep of
the shells, plate, angles, RF bay, pedestal, bosses and tray, so wall radii,
the seam belt, bosses, webs, pads and seats are all seen. An overlap is a
conflict unless it lies inside a feature that the item is designed to touch
(a board on its standoffs, the Lime on its pedestal). Envelopes are reserves,
not vendor geometry: a clean result is a model fit only.
"""
from build123d import Align, Box, Pos

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
    "tripod_boss": {"rear.tripod_boss"},       # this envelope is the boss itself
    "gx16": {"rear.gx16_pad"},                 # the socket nut sits on its seat
    "hatch_parts": {"rear.hatch_seat", "hatch_cover"},
    "battery_pack": {"battery_tray"},          # the pack lies in its tray (the tray solid is checked separately)
}
SKIP_ITEMS = {"battery_tray"}                  # represented by its solid, not by its envelope box

# structure pairs checked solid against solid (fastened parts only touch, so any volume is a conflict)
STRUCT_PAIRS = [
    ("plate", "front_shell"), ("plate", "rear_shell"), ("battery_tray", "front_shell"), ("battery_tray", "rear_shell"),
    ("battery_tray", "plate"), ("angle_top", "front_shell"), ("angle_top", "rear_shell"), ("angle_right", "front_shell"),
    ("angle_right", "rear_shell"), ("rf_bay_walls", "rear_shell"), ("rf_bay_walls", "front_shell"), ("rf_bay_lid", "rear_shell"),
    ("lime_pedestal", "front_shell"), ("ufs_boss", "rear_shell"), ("rf_bay_walls", "plate"), ("rf_bay_lid", "rf_bay_walls"),
    ("hatch_cover", "rear_shell"), ("t7_holder", "rear_shell"),
]


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
    for a, b in STRUCT_PAIRS:
        if a not in solids or b not in solids:
            continue
        inter = solids[a] & solids[b]
        v = _vol(inter)
        if v > TOL_MM3:
            rows.append({"item": a, "solid": b, "overlap_mm3": round(v, 1), "bbox_mm": _bb(inter), "result": "FAIL (model)"})
    return {"method": "B-rep intersection of every envelope with the shells, plate, angles, RF bay, pedestal, UFS boss, tray, hatch and T7 holder; "
                      f"structure pairs solid against solid; overlaps above {TOL_MM3} mm3 outside by-design features fail",
            "conflicts": rows, "by_design": allowed_hits,
            "result": "PASS (model fit only)" if not rows else f"FAIL (model): {len(rows)} conflicts"}
