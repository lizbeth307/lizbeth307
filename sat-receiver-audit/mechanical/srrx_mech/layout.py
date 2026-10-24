"""Envelope layout and the model-fit checks that need no CAD kernel.

Every item becomes one or more axis-aligned boxes (x0, y0, z0, x1, y1, z1).
The checks report clearances between envelopes; they are MODEL FIT ONLY.
"""
import itertools
import math


def _box(b):
    x, y, z, dx, dy, dz = b
    return (x, y, z, x + dx, y + dy, z + dz)


def q6a_boxes(P):
    """Q6A board, standoff zone and connector boxes in enclosure coordinates."""
    q = P.parts["q6a"]
    m = P.mech["q6a_mount"]
    x0, y0 = m["origin"]
    zr = P.mech["stack_z"]["plate_rear"]
    z_bot = zr - m["standoff"]            # board face towards the plate
    z_top = z_bot - q["board"][2]          # component face (towards the rear)
    bu, bv = q["board"][0], q["board"][1]

    def uv(u0, v0, u1, v1):
        xa, xb = x0 + bu - u1, x0 + bu - u0
        return xa, y0 + v0, xb, y0 + v1

    # board with a generic 7.5 mm component zone on the rear face and the bottom parts towards the plate
    out = [("q6a.board", (x0, y0, z_top - q.get("generic_top", 7.5), x0 + bu, y0 + bv, z_bot + q["bottom_max"]))]
    for name, c in q["connectors"].items():
        xa, ya, xb, yb = uv(*c["uv"])
        out.append((f"q6a.{name}", (xa, ya, z_top - c["top"], xb, yb, z_top)))
    return out


def cu_block_geometry(P):
    """Cooler-A block in board (u, v) terms: origin, size, LPDDR5 recess and SoC rectangles (block-local mm)."""
    q = P.parts["q6a"]
    cb = P.mech["cu_block"]
    soc, ram = q["soc"]["uv"], q["lpddr5"]["uv"]
    mg = cb["margin"]
    u0, v0 = min(soc[0], ram[0]) - mg, min(soc[1], ram[1]) - mg
    u1, v1 = max(soc[2], ram[2]) + mg, max(soc[3], ram[3]) + mg
    bw, bh = min(cb["max"][0], u1 - u0), min(cb["max"][1], v1 - v0)
    recess = (ram[0] - u0 - 0.5, ram[1] - v0 - 0.5, ram[2] - ram[0] + 1.0, ram[3] - ram[1] + 1.0)
    soc_r = (soc[0] - u0, soc[1] - v0, soc[2] - soc[0], soc[3] - soc[1])
    return (u0, v0), (bw, bh), recess, soc_r


def board_boxes(P, bid, at=None):
    b = P.boards["boards"][bid]
    pl = b["place"]
    if at is not None:
        ox, oy = b["place_at"][at]
    else:
        ox, oy = pl["origin"]
    t = P.boards["stackup"]["t"]
    z0 = pl["z_bottom"]
    h = b["max_height"]
    # z0 is the face opposite the components (towards the mounting surface)
    if pl["facing"] == "+z":
        za, zb = z0, z0 + t + h
    else:
        za, zb = z0 - t - h, z0
    return [(f"{bid}.r{i}", (ox + r[0], oy + r[1], za, ox + r[0] + r[2], oy + r[1] + r[3], zb)) for i, r in enumerate(b["rects"])]


def item_boxes(P):
    items = []
    for it in P.mech["layout"]["items"]:
        if "board" in it:
            for name, bx in board_boxes(P, it["board"], it.get("at")):
                items.append((it["id"], name, bx, it))
        elif it.get("part") == "q6a" and "box" not in it:
            for name, bx in q6a_boxes(P):
                items.append((it["id"], name, bx, it))
        else:
            items.append((it["id"], it["id"], _box(it["box"]), it))
    return items


def structure_boxes(P):
    """Fixed structure the envelopes must clear: plate, angles, closure and plate bosses, RF bay walls."""
    m = P.mech
    sz = m["stack_z"]
    out = []
    pr, pf = sz["plate_rear"], sz["plate_front"]
    x, y, w, h = m["plate"]["main"]
    out.append(("plate.main", (x, y, pr, x + w, y + h, pf)))
    x, y, w, h = m["plate"]["ext"]
    out.append(("plate.ext", (x, y, pr, x + w, y + h, pf)))
    W, H, D = P.outer
    t = m["wall"]
    a = m["angles"]["top"]
    out.append(("angle.top.wall", (a["x"][0], H - t - a["t"], pr - a["leg_wall"], a["x"][1], H - t, pr)))
    out.append(("angle.top.plate", (a["x"][0], H - t - a["leg_plate"], pr - a["t"], a["x"][1], H - t, pr)))
    a = m["angles"]["right"]
    out.append(("angle.right.wall", (W - t - a["t"], a["y"][0], pr - a["leg_wall"], W - t, a["y"][1], pr)))
    out.append(("angle.right.plate", (W - t - a["leg_plate"], a["y"][0], pr - a["t"], W - t, a["y"][1], pr)))
    c = m["closure"]
    r = c["boss_d"] / 2.0
    for i, (bx, by) in enumerate(c["bosses"]):
        out.append((f"closure.boss{i}", (bx - r, by - r, 0.0, bx + r, by + r, c["front_boss_top"])))
    for i, (bx, by) in enumerate(m["plate"]["mount_bosses"]):
        out.append((f"plate.boss{i}", (bx - 3.5, by - 3.5, pf, bx + 3.5, by + 3.5, m["plate"]["mount_boss_top"])))
    rb = m["rf_bay"]
    x, y, w, h = rb["rect"]
    wt = rb["wall_t"]
    walls = {"left": (x, y, rb["lid_z"][0], x + wt, y + h, pr),
             "bottom": (x, y, rb["lid_z"][0], x + w, y + wt, pr),
             "right": (x + w - wt, y, rb["lid_z"][0], x + w, y + h, pr)}
    for side in rb["walls"]:
        out.append((f"rfbay.wall.{side}", walls[side]))
    # UFS boss on the plate rear face, under the Q6A bottom side (rules.ufs_rect)
    from .rules import ufs_rect
    ub = m["ufs_boss"]
    ux0, uy0, ux1, uy1 = ufs_rect(P)
    zb = pr - (m["q6a_mount"]["standoff"] - ub["module_below_board"] - ub["pad_gap"])
    out.append(("plate.ufs_boss", (ux0, uy0, zb, ux1, uy1, pr)))
    out.append(("rfbay.lid", (x, y, rb["lid_z"][0], x + w, y + h, rb["lid_z"][1])))
    return out


def overlap(a, b):
    return [min(a[i + 3], b[i + 3]) - max(a[i], b[i]) for i in range(3)]


def gap(a, b):
    """Separation between two boxes (negative = interpenetration depth along the best axis)."""
    ov = overlap(a, b)
    if min(ov) > 0:
        return -min(ov)
    outside = [max(0.0, -v) for v in ov]
    return math.sqrt(sum(v * v for v in outside))


# Pairs that touch by design (a board on its plate, modules carried by a board, the lid under modules).
ALLOWED = [
    ("board_pwr", "plate.main"), ("board_pwr", "plate.ext"), ("hdmi_board", "plate.main"),
    ("blower", "plate.main"), ("bms", "plate.main"), ("bms", "plate.ext"), ("lime", "plate.main"),
    ("hfplus", "plate.main"), ("q6a", "plate.main"), ("board_rf", "plate.main"),
    ("v4l_a", "rfbay.lid"), ("v4l_b", "rfbay.lid"), ("sawbird", "rfbay.lid"),
    ("flamingo", "rfbay.lid"), ("battery_tray", "closure.boss0"),
    ("tripod_boss", "rear"), ("gx16", "rear"), ("hatch_parts", "rear"), ("q6a_fan_duct", "rear"),
    ("enc_main", "board_ctrl"), ("enc_volume", "board_ctrl"), ("closure.boss", "rfbay.lid"),
    ("q6a.usb_stack", "usb_plug_bay"), ("q6a.hdmi", "hdmi_plug"), ("ferrite_a", "rear"),
    ("q6a.board", "plate.ufs_boss"),  # contact through the UFS pad by design (thermal T-UFS)
]

STRUCT = ("plate.", "angle.", "rfbay.")


def joined(a, b):
    """Structure parts that are fastened to each other by design."""
    return a.startswith(STRUCT) and b.startswith(STRUCT)


def allowed(a, b):
    for x, y in ALLOWED:
        if (a.startswith(x) and b.startswith(y)) or (a.startswith(y) and b.startswith(x)):
            return True
    return False


def fit_checks(P, min_gap=0.5):
    W, H, D = P.outer
    t = P.mech["wall"]
    interior = (t, t, t, W - t, H - t, D - t)
    boxes = [(iid, name, bx) for iid, name, bx, _ in item_boxes(P)] + [(n, n, bx) for n, bx in structure_boxes(P)]
    results = []
    for (ia, na, ba), (ib, nb, bb) in itertools.combinations(boxes, 2):
        if ia == ib:
            continue
        if joined(na, nb):
            continue
        g = gap(ba, bb)
        if g < min_gap and not allowed(na, nb) and not allowed(ia, ib):
            results.append({"a": na, "b": nb, "gap_mm": round(g, 2), "result": "FAIL (model)" if g < 0 else "TIGHT (model)"})
    outside = []
    for iid, name, bx in boxes:
        if iid.startswith(("tripod_boss", "closure.", "plate.", "angle.")):
            continue
        for i, ax in enumerate("xyz"):
            if bx[i] < interior[i] - 1e-6 or bx[i + 3] > interior[i + 3] + 1e-6:
                outside.append({"item": name, "axis": ax, "range": [round(bx[i], 2), round(bx[i + 3], 2)],
                                "interior": [interior[i], interior[i + 3]]})
    return results, outside


def channel_check(P, need=4.0):
    """Path-2 channel: free height between front-layer parts under the display module and the module back
    (STACK 5.8: channel 4-6 mm). The HDMI board is part of the display stack and is not a channel obstacle."""
    zb = P.mech["stack_z"]["module_back"]
    d = [b for i, n, b, _ in item_boxes(P) if i == "display"][0]
    out = []
    for iid, name, bx, it in item_boxes(P):
        if it.get("mount") != "plate_front" or iid == "hdmi_board":
            continue
        ov = overlap(bx, d)
        if ov[0] <= 0 or ov[1] <= 0:
            continue
        g = zb - bx[5]
        out.append({"item": name, "top_z": round(bx[5], 2), "gap_to_module_mm": round(g, 2),
                    "result": "PASS (model)" if g >= need else "TIGHT (model): local, below the 4 mm channel rule"})
    return out
