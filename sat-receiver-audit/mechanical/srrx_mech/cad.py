"""3D parts (build123d). Every dimension comes from mechanical/params.

Coordinates: enclosure frame (x right, y up from the front, z from the rear face
towards the front face). Printed parts are exported in that frame except the
small loose parts, which are exported at the origin in their print orientation.
"""
import math

from build123d import (Align, Box, Circle, Compound, Cylinder, Helix, Plane, Pos, RectangleRounded,
                       RegularPolygon, Rot, SlotOverall, extrude, sweep)

from .features import HOLES, face_features, seam_geometry, to_xyz
from .layout import board_boxes, cu_block_geometry, item_boxes, q6a_boxes

MIN = (Align.MIN, Align.MIN, Align.MIN)


def box(x0, y0, z0, dx, dy, dz):
    return Pos(x0, y0, z0) * Box(dx, dy, dz, align=MIN)


def rbox(x0, y0, z0, w, h, d, r):
    r = max(0.2, min(r, w / 2 - 0.01, h / 2 - 0.01))
    return Pos(x0 + w / 2, y0 + h / 2, z0) * extrude(RectangleRounded(w, h, r), amount=d)


def zcyl(x, y, z0, z1, r):
    return Pos(x, y, min(z0, z1)) * Cylinder(r, abs(z1 - z0), align=(Align.CENTER, Align.CENTER, Align.MIN))


def axis_cyl(p, normal, r, length, inward=True):
    """Cylinder of `length` starting `length/2` outside the face point p and going inwards along -normal."""
    nx, ny, nz = normal
    cx, cy, cz = p[0] - nx * (length / 2 - 2.0), p[1] - ny * (length / 2 - 2.0), p[2] - nz * (length / 2 - 2.0)
    c = Cylinder(r, length)
    if nx:
        c = Rot(0, 90, 0) * c
    elif ny:
        c = Rot(90, 0, 0) * c
    return Pos(cx, cy, cz) * c


def cut(part, cutters):
    cutters = [c for c in cutters if c is not None]
    return part.cut(*cutters) if cutters else part


def fuse(part, adds):
    adds = [a for a in adds if a is not None]
    return part.fuse(*adds) if adds else part


def slot_cutters(P, face, f, depth):
    """Grille slots through a wall of thickness `depth` on `face`."""
    out = []
    n = int((f["w"] if f["slots_along"] == "u" else f["h"]) // f["slot_pitch"])
    for i in range(n):
        if f["slots_along"] == "u":
            u = f["u"] - f["w"] / 2 + f["slot_pitch"] * (i + 0.5)
            v = f["v"]
            L, Wd = f["h"] - 3.0, f["slot_w"]
            rot_in_face = 90.0
        else:
            u = f["u"]
            v = f["v"] - f["h"] / 2 + f["slot_pitch"] * (i + 0.5)
            L, Wd = f["w"] - 3.0, f["slot_w"]
            rot_in_face = 0.0
        out.append(face_prism(P, face, u, v, SlotOverall(L, Wd, rotation=rot_in_face), depth + 4.0))
    return out


def face_prism(P, face, u, v, sketch, depth):
    """Extrude a 2D sketch drawn in the face (u, v) system inwards through the wall.

    The sketch starts 2 mm outside the face and runs `depth` inwards. Proper rotations only:
    the in-face v axis may come out reversed, which is harmless for the symmetric shapes used."""
    W, H, D = P.outer
    s = extrude(sketch, amount=depth)
    if face == "front":
        return Pos(u, v, D + 2.0) * Rot(180, 0, 0) * s
    if face == "rear":
        return Pos(W - u, v, -2.0) * Rot(0, 0, 180) * s
    if face == "top":
        return Pos(u, H + 2.0, D - v) * Rot(90, 0, 0) * s
    if face == "bottom":
        return Pos(u, -2.0, v) * Rot(-90, 0, 0) * s
    if face == "left":
        return Pos(-2.0, v, u) * Rot(0, 90, 0) * Rot(0, 0, 180) * s
    if face == "right":
        return Pos(W + 2.0, v, D - u) * Rot(0, -90, 0) * Rot(0, 0, 180) * s
    raise ValueError(face)


def feature_cutters(P, face, feats, wall_depth):
    out = []
    from .features import FACE_NORMAL
    n = FACE_NORMAL[face]
    for f in feats:
        k = f["kind"]
        if k in ("window",):
            out.append(face_prism(P, face, f["u"], f["v"], RectangleRounded(f["w"], f["h"], f["r"]), wall_depth + 4.0))
        elif k == "grille":
            out += slot_cutters(P, face, f, wall_depth)
        elif k == "hatch":
            out.append(face_prism(P, face, f["u"], f["v"], RectangleRounded(f["w"], f["h"], f["r"]), wall_depth + 4.0))
        elif k in ("closure", "pad", "strap"):
            continue
        elif k == "insert_m3":
            p = to_xyz(P, face, f["u"], f["v"])
            out.append(zcyl(p[0], p[1], -1.0, 7.0, f["d"] / 2.0) if face == "rear" else None)
        elif "d" in f:
            p = to_xyz(P, face, f["u"], f["v"])
            out.append(axis_cyl(p, n, f["d"] / 2.0, 2 * (wall_depth + 4.0)))
    return out


# ---------------------------------------------------------------------------------------------
def _ring(P, o0, o1, z0, h):
    """Closed band between the inward offsets o0 < o1 of the outer rounded rectangle, z0..z0+h."""
    W, H, _ = P.outer
    R = P.mech["outer"]["corner_r"]
    return rbox(o0, o0, z0, W - 2 * o0, H - 2 * o0, h, R - o0) - rbox(o1, o1, z0 - 1.0, W - 2 * o1, H - 2 * o1, h + 2.0, R - o1)


def _web(P, x, y, wall, z0, z1, w):
    """Rib of width w from (x, y) to the inner face of the given side wall."""
    W, H, _ = P.outer
    t = P.mech["wall"]
    if wall == "top":
        return box(x - w / 2, y, z0, w, H - t + 0.5 - y, z1 - z0)
    if wall == "bottom":
        return box(x - w / 2, t - 0.5, z0, w, y - t + 0.5, z1 - z0)
    if wall == "left":
        return box(t - 0.5, y - w / 2, z0, x - t + 0.5, w, z1 - z0)
    if wall == "right":
        return box(x, y - w / 2, z0, W - t + 0.5 - x, w, z1 - z0)
    raise ValueError(wall)


def front_parts(P):
    """Front shell as (shell with belt, [(feature name, [solids])], [cutters]); the names feed the interference check."""
    m = P.mech
    W, H, D = P.outer
    t, R, zs = m["wall"], m["outer"]["corner_r"], m["split_z"]
    gk = m["gasket"]
    sg = seam_geometry(P)
    sz = m["stack_z"]
    body = rbox(0, 0, zs, W, H, D - zs, R) - rbox(t, t, zs - 1.0, W - 2 * t, H - 2 * t, D - zs - t + 1.0, R - t)
    body = body + _ring(P, -sg["belt"], t - 0.01, zs, sg["belt_h"])
    feats = []
    # closure bosses (insert side): they hug the side walls, so each grows out of the wall over its whole height
    c = m["closure"]
    feats.append(("closure_bosses", [zcyl(bx, by, zs, c["front_boss_top"], c["boss_d"] / 2) for (bx, by) in c["bosses"]]))
    # plate bosses, each with a web to the nearest side wall
    pb = []
    for b in m["plate"]["mount_bosses"]:
        bx, by = b["c"]
        z0, z1 = sz["plate_front"], m["plate"]["mount_boss_top"]
        pb.append(zcyl(bx, by, z0, z1, m["plate"]["mount_boss_d"] / 2))
        pb.append(_web(P, bx, by, b["wall"], z0, z1, 3.0))
    feats.append(("plate_bosses", pb))
    fwi = sz["front_wall_inner"]
    feats.append(("clamp_bosses", [zcyl(bx, by, sz["module_back"], fwi + 0.1, m["display"]["clamp"]["boss_d"] / 2)
                                   for (bx, by) in m["display"]["clamp_bosses"]]))
    cb = P.boards["boards"]["CTRL"]
    ox, oy = cb["place"]["origin"]
    ctrl_top = cb["place"]["z_bottom"] + P.boards["stackup"]["t"]
    feats.append(("ctrl_bosses", [zcyl(ox + hx, oy + hy, ctrl_top, fwi + 0.1, 3.0) for (hx, hy) in cb["holes"]]))
    e = P.boards["boards"]["ENC"]
    enc_top = e["place"]["z_bottom"] + P.boards["stackup"]["t"]
    feats.append(("enc_bosses", [zcyl(ex + hx, ey + hy, enc_top, fwi + 0.1, 3.0) for (ex, ey) in e["place_at"].values() for (hx, hy) in e["holes"]]))
    # encoder boss pads (local wall 2.6 mm) and vent pads (flat 2.0-3.5 mm seats, LTW datasheet)
    eb = m["hmi"]["encoder_boss"]
    feats.append(("enc_pads", [zcyl(enc["c"][0], enc["c"][1], D - eb["wall"], fwi + 0.1, eb["boss_d"] / 2) for enc in m["hmi"]["encoders"].values()]))
    feats.append(("vent_pads", [vent_pad(P, v) for v in m["vents"]]))
    # intake foam seat frame on the bottom wall
    it = m["bottom_face"]["intake"]
    sx0, sx1, sz0, sz1 = it["x"][0] - 1.6, it["x"][1] + 1.6, it["z"][0] - 1.6, it["z"][1] + 1.6
    feats.append(("intake_seat", [box(sx0, t - 0.01, sz0, sx1 - sx0, it["seat_depth"], sz1 - sz0)
                                  - box(sx0 + 1.6, t - 1, sz0 + 1.6, sx1 - sx0 - 3.2, it["seat_depth"] + 2, sz1 - sz0 - 3.2)]))
    # hood hinge knuckles on the front face
    hh = m["top_face"]["hood_hinge"]
    feats.append(("hinge_knuckles", [box(x - hh["knuckle_w"] / 2, hh["axis_y"] - 4.0, D - 0.01, hh["knuckle_w"], 8.0, hh["axis_z"] - D + 3.0) for x in hh["x"]]))
    # ---- cutters
    cutters = [_ring(P, sg["groove_out"], sg["groove_in"], zs - 1.0, gk["groove_depth"] + 1.0)]
    ins = c["insert"]
    cutters += [zcyl(bx, by, zs - 1.0, zs + ins["len"] + 0.8, ins["hole_d"] / 2) for (bx, by) in c["bosses"]]
    cutters += [zcyl(b["c"][0], b["c"][1], sz["plate_front"] - 1.0, sz["plate_front"] + 6.5, 2.0) for b in m["plate"]["mount_bosses"]]
    cutters += [zcyl(bx, by, sz["module_back"] - 1.0, sz["module_back"] + 4.5, 1.8) for (bx, by) in m["display"]["clamp_bosses"]]
    cutters += [zcyl(ox + hx, oy + hy, ctrl_top - 1.0, ctrl_top + 4.5, 1.8) for (hx, hy) in cb["holes"]]
    cutters += [zcyl(ex + hx, ey + hy, enc_top - 1.0, enc_top + 4.5, 1.8) for (ex, ey) in e["place_at"].values() for (hx, hy) in e["holes"]]
    cutters += [Pos(x, hh["axis_y"], hh["axis_z"]) * Rot(0, 90, 0) * Cylinder(hh["pin_d"] / 2, hh["knuckle_w"] + 2.0) for x in hh["x"]]
    F = face_features(P)
    for face in ("front", "top", "bottom", "left", "right"):
        cutters += feature_cutters(P, face, F[face], 4.0 + sg["belt"])
    return body, feats, cutters


def vent_pad(P, v):
    """Flat seat on the inner face of the wall: pad_t is the total wall thickness at the vent."""
    W, H, D = P.outer
    t = P.mech["wall"]
    r, h = v["pad_d"] / 2, v["pad_t"] - t + 0.05
    if v["face"] == "front":
        return zcyl(v["x"], v["y"], D - v["pad_t"], D - t + 0.05, r)
    if v["face"] == "right":
        return Pos(W - v["pad_t"], v["y"], v["z"]) * Rot(0, 90, 0) * Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if v["face"] == "left":
        return Pos(t - 0.05, v["y"], v["z"]) * Rot(0, 90, 0) * Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    raise ValueError(v["face"])


def front_shell(P):
    body, feats, cutters = front_parts(P)
    return cut(fuse(body, [s for _, group in feats for s in group]), cutters)


def rear_parts(P):
    m = P.mech
    W, H, D = P.outer
    t, R, zs = m["wall"], m["outer"]["corner_r"], m["split_z"]
    sg = seam_geometry(P)
    body = rbox(0, 0, 0, W, H, zs, R) - rbox(t, t, t, W - 2 * t, H - 2 * t, zs, R - t)
    body = body + _ring(P, -sg["belt"], t - 0.01, zs - sg["belt_h"], sg["belt_h"])
    feats = []
    c = m["closure"]
    feats.append(("closure_bosses", [zcyl(bx, by, 0.0, zs, c["boss_d"] / 2) for (bx, by) in c["bosses"]]))
    rf = m["rear_face"]
    tp = rf["tripod"]
    tx, ty = tp["c"]
    ph = tp["plinth_h"]
    # the plate seats on a plinth ph proud of the rear face; the nut pocket moves out with it (outer wall stays outer_wall)
    feats.append(("tripod_boss", [zcyl(tx, ty, -ph, max(-ph + tp["outer_wall"] + tp["hex_depth"], t - 0.01), tp["boss_d"] / 2),
                                  zcyl(tx, ty, -ph, 0.01, tp["plinth_d"] / 2)]))
    gx = rf["gx16"]
    feats.append(("gx16_pad", [zcyl(gx["c"][0], gx["c"][1], 0.0, gx["pad_t"], gx["pad_d"] / 2)]))
    hx, hy, hw, hh = rf["hatch"]["rect"]
    seat = rf["hatch"]["seat"]
    feats.append(("hatch_seat", [rbox(hx - seat, hy - seat, 0.0, hw + 2 * seat, hh + 2 * seat, 4.0, rf["hatch"]["r"] + seat)]
                  + [zcyl(sx, sy, 0.0, 8.0, 3.5) for (sx, sy) in rf["hatch"]["screws"]]))
    x, y, w, h = rf["path1_intake"]["rect"]
    feats.append(("intake_seat", [box(x - 1.6, y - 1.6, t - 0.01, w + 3.2, h + 3.2, 5.0) - box(x, y, t - 1, w, h, 7.0)]))
    # strap tunnels and neck lugs on the outer rear face (protrude 6 mm)
    ss = rf["strap_slots"]
    lg = rf["strap_lug"]
    feats.append(("strap_lugs", [box(lx - lg["w"] / 2, ly - lg["h"] / 2, -lg["proud"], lg["w"], lg["h"], lg["proud"] + 0.01) for (lx, ly) in rf["strap_lugs"]]
                  + [box(ss["x"] - 9.0, yy - (ss["w"] + 8) / 2, -6.0, 18.0, ss["w"] + 8, 6.01) for yy in ss["y"]]))
    th = rf["t7_holder"]
    feats.append(("t7_pads", [zcyl(px, py, -th["pad_h"], 0.01, th["pad_d"] / 2) for (px, py) in th["screws"]]))
    cutters = []
    for (bx, by) in c["bosses"]:
        cutters.append(zcyl(bx, by, -1.0, zs + 1.0, c["clearance_d"] / 2))
        cutters.append(zcyl(bx, by, -1.0, c["counterbore_depth"], c["counterbore_d"] / 2))
    hexr = tp["hex_af"] / 2 / math.cos(math.radians(30))
    z_hex = -ph + tp["outer_wall"]
    cutters.append(Pos(tx, ty, z_hex) * extrude(RegularPolygon(hexr, 6), amount=max(tp["hex_depth"], t - z_hex) + 1.0))   # open towards the inside
    cutters.append(zcyl(tx, ty, -ph - 1.0, z_hex + 0.5, tp["hole_d"] / 2))
    cutters += [zcyl(sx, sy, -1.0, 6.5, 2.0) for (sx, sy) in rf["hatch"]["screws"]]
    cutters += [box(lx - 8.0, ly - 2.5, -lg["proud"] + 1.5, 16.0, 5.0, 3.0) for (lx, ly) in rf["strap_lugs"]]
    cutters += [box(ss["x"] - 11.0, yy - ss["w"] / 2, -4.5, 22.0, ss["w"], 3.0) for yy in ss["y"]]
    F = face_features(P)
    cutters += feature_cutters(P, "rear", F["rear"], 10.0)
    for face in ("top", "bottom", "left", "right"):
        cutters += feature_cutters(P, face, F[face], 4.0 + sg["belt"])
    # T7 holder: blind insert holes in the pads (screws from outside; 0.5 mm skin to the inside)
    ins = c["insert"]
    cutters += [zcyl(px, py, -th["pad_h"] - 1.0, -th["pad_h"] + ins["len"] + 0.8, ins["hole_d"] / 2) for (px, py) in th["screws"]]
    return body, feats, cutters


def rear_shell(P):
    body, feats, cutters = rear_parts(P)
    return cut(fuse(body, [s for _, group in feats for s in group]), cutters)


def hatch_cover(P):
    rf = P.mech["rear_face"]
    gk = P.mech["gasket"]
    hx, hy, hw, hh = rf["hatch"]["rect"]
    seat = rf["hatch"]["seat"]
    tcov = gk["groove_depth"] + 2.2
    cov = rbox(hx - seat + 0.3, hy - seat + 0.3, -tcov, hw + 2 * seat - 0.6, hh + 2 * seat - 0.6, tcov, rf["hatch"]["r"] + seat)
    lip = box(hx + 2, hy + 0.3, 0.0, hw - 4, 2.5, 3.5)   # locating tab inside the opening (bottom edge), no screw near the battery
    cov = fuse(cov, [lip])
    g, gw = seat / 2.0, gk["groove_w"] / 2.0     # same cord and groove section as the seam, centred on the seat
    groove = rbox(hx - g - gw, hy - g - gw, -gk["groove_depth"], hw + 2 * (g + gw), hh + 2 * (g + gw), gk["groove_depth"] + 1, rf["hatch"]["r"] + g + gw) \
        - rbox(hx - g + gw, hy - g + gw, -gk["groove_depth"] - 1, hw + 2 * (g - gw), hh + 2 * (g - gw), gk["groove_depth"] + 3, max(0.5, rf["hatch"]["r"] + g - gw))
    cutters = [groove]
    for (sx, sy) in rf["hatch"]["screws"]:
        cutters.append(zcyl(sx, sy, -tcov - 1, 1.0, 1.7))
    return cut(cov, cutters)


def display_clamp(P):
    d = P.mech["display"]["clamp"]
    part = box(-d["boss_d"] / 2, -d["boss_d"] / 2, 0, d["w"], d["w"], d["t"]) + box(d["boss_d"] / 2 - 1.0, d["boss_d"] / 2 - 1.0, 0, d["reach"], d["reach"], d["t"])
    return part - zcyl(0, 0, -1, d["t"] + 1, 1.45)


def hood(P):
    m = P.mech
    W, H, D = P.outer
    hd = m["hood"]
    hh = m["top_face"]["hood_hinge"]
    x0, x1 = hd["x"]
    plate = box(x0, hh["axis_y"] - hd["t"] / 2, hh["axis_z"] + 2.0, x1 - x0, hd["t"], hd["depth"])
    # notch the plate edge over the fixed knuckles of the front shell (they reach axis_z + 3 in the open position)
    plate = plate - [box(x - hh["knuckle_w"] / 2 - 0.5, hh["axis_y"] - 4.5, hh["axis_z"] + 1.0, hh["knuckle_w"] + 1.0, 9.0, 3.5) for x in hh["x"]]
    knuckles = []
    xs = sorted(hh["x"])
    for a, b in zip(xs, xs[1:]):
        knuckles.append(box(a + hh["knuckle_w"] / 2 + 0.5, hh["axis_y"] - 3.0, hh["axis_z"] - 3.0, b - a - hh["knuckle_w"] - 1.0, 6.0, 6.0))
    part = fuse(plate, knuckles)
    pins = [Pos((a + b) / 2, hh["axis_y"], hh["axis_z"]) * Rot(0, 90, 0) * Cylinder(hh["pin_d"] / 2, b - a) for a, b in zip(xs, xs[1:])]
    return cut(part, pins)


def interior_clearance(P, gap, z0=-50.0, h=200.0):
    """Rounded interior of the shells shrunk by `gap`: loose parts are intersected with it so they clear the corner radii."""
    W, H, _ = P.outer
    t, R = P.mech["wall"], P.mech["outer"]["corner_r"]
    o = t + gap
    return rbox(o, o, z0, W - 2 * o, H - 2 * o, h, R - o)


def battery_tray(P):
    """Printed U-channel tray (open towards the plate) with slots round the wall-hugging closure bosses."""
    m = P.mech
    it = [i for i in m["layout"]["items"] if i["id"] == "battery_tray"][0]
    x, y, z, dx, dy, dz = it["box"]
    wt = m["battery"]["tray_wall"]
    tray = box(x, y, z, dx, dy, dz) - box(x + wt, y + wt, z + wt, dx - 2 * wt, dy, dz - 2 * wt)
    tray = tray & interior_clearance(P, 0.3)
    for v in m["vents"]:
        if v["face"] == "front" and x < v["x"] < x + dx and y < v["y"] < y + dy:
            tray = tray - zcyl(v["x"], v["y"], z + dz - wt - 1.0, z + dz + 1.0, 6.6)   # the vent thread passes the tray front wall
    tray = tray - box(x + dx - 12.0, y + dy - wt - 1, z + dz - 16.0, 10.0, wt + 2, 10.0)
    c = m["closure"]
    slots = [zcyl(bx, by, -1.0, 100.0, c["boss_d"] / 2 + 0.5) for (bx, by) in c["bosses"]
             if x - 5 < bx < x + dx + 5 and y - 5 < by < y + dy + 5]
    return cut(tray, slots)


def t7_holder(P):
    """Cradle on the rear face: T7 stands vertical, air gap towards the enclosure, reflective shutter outside.

    Fastened from outside (M3 through the rails into inserts in pads on the rear shell), so it comes off
    before the closure screws under it are undone."""
    rf = P.mech["rear_face"]["t7_holder"]
    x, y, w, h = rf["rect"]
    t7 = P.parts["t7"]["size"]
    gap, rail, sh = rf["gap"], rf["rail"], rf["shutter_t"]
    depth = gap + t7[2] + sh
    frame = box(x, y, -depth, w, h, depth)
    pocket = box(x + rail, y + 3.0, -depth + sh, w - 2 * rail, h, depth)
    part = frame - pocket
    ribs = [box(x + rail, y + 3.0, -gap, 3.0, h - 3.0, gap), box(x + w - rail - 3.0, y + 3.0, -gap, 3.0, h - 3.0, gap)]
    part = fuse(part, ribs)
    vents = [box(x + rail + 6.0 + 10.0 * i, y + 0.5, -depth + sh, 5.0, 2.0, depth) for i in range(int((w - 2 * rail - 12.0) // 10.0))]
    holes = [zcyl(px, py, -depth - 1, 1.0, 1.7) for (px, py) in rf["screws"]]
    pads = [zcyl(px, py, -rf["pad_h"] - 0.3, 1.0, rf["pad_d"] / 2 + 0.3) for (px, py) in rf["screws"]]   # over the rear-shell pads
    return cut(part, vents + holes + pads)


def button_cap(P, ribbed=False):
    b = P.mech["hmi"]["buttons"]
    t = P.mech["hmi"]["encoder_boss"]["wall"]
    stem = zcyl(0, 0, 0, b["cap_flange_t"] + t + b["cap_protrusion"], b["cap_d"] / 2)
    fl = zcyl(0, 0, 0, b["cap_flange_t"], b["cap_flange_d"] / 2)
    part = stem + fl
    if ribbed:
        part = part + box(-b["cap_d"] / 2 + 1.5, -0.75, b["cap_flange_t"] + t + b["cap_protrusion"] - 0.01, b["cap_d"] - 3.0, 1.5, 1.0)
    return part


def main_knob(P):
    k = P.mech["hmi"]["encoders"]["main"]["knob_d"]
    kh = P.mech["hmi"]["encoders"]["main"]["knob_h"]
    pec = P.parts["pec11r"]
    body = zcyl(0, 0, 0, kh, k / 2) - zcyl(0, 0, -1, 5.0, k / 2 - 2.0)
    bore = zcyl(0, 0, -1, 12.5, pec["shaft_d"] / 2 + 0.1)
    flat = box(-5, pec["shaft_d"] / 2 - (pec["shaft_d"] - 4.5) + 0.1, -1, 10, 3, 13.5)
    hub = zcyl(0, 0, 0, 13.0, 5.5)
    knurl = [Pos((k / 2) * math.cos(math.radians(a)), (k / 2) * math.sin(math.radians(a)), 2.0) * Cylinder(1.2, 24.0, align=(Align.CENTER, Align.CENTER, Align.MIN)) for a in range(0, 360, 15)]
    part = fuse(body, [hub])
    part = cut(part, [bore - flat] + knurl)
    return part


# ---- aluminium / FR4 parts --------------------------------------------------------------------
def plate(P):
    m = P.mech
    pl = m["plate"]
    sz = m["stack_z"]
    x, y, w, h = pl["main"]
    ex, ey, ew, eh = pl["ext"]
    part = box(x, y, sz["plate_rear"], w, h, pl["t"]) + box(ex, ey, sz["plate_rear"], ew, y - ey + 0.01, pl["t"])
    part = part & interior_clearance(P, pl["corner_clearance"])
    from .rules import plate_holes
    cutters = [zcyl(h["c"][0], h["c"][1], 0, 100, h["d"] / 2) for h in plate_holes(P)]
    rw = pl["riser_window"]
    cutters.append(box(rw[0], rw[1], 0, rw[2], rw[3], 100))
    cutters += [box(nx, ny, 0, nw, nh, 100) for (nx, ny, nw, nh) in pl.get("notches", [])]
    cutters += [box(nx, ny, 0, nw + 5.0, nh, 100) for (nx, ny, nw, nh) in pl.get("notches_right", [])]
    return cut(part, cutters)


def angle_top(P):
    m = P.mech
    W, H, D = P.outer
    a = m["angles"]["top"]
    pr = m["stack_z"]["plate_rear"]
    t = m["wall"]
    L = a["x"][1] - a["x"][0]
    part = box(a["x"][0], H - t - a["t"], pr - a["leg_wall"], L, a["t"], a["leg_wall"]) + box(a["x"][0], H - t - a["leg_plate"], pr - a["t"], L, a["leg_plate"], a["t"])
    cutters = []
    for p in m["top_face"]["ports"]:
        if a["x"][0] < p["x"] < a["x"][1]:
            cutters.append(Pos(p["x"], H - t - a["t"] / 2, m["top_face"]["ports_z"]) * Rot(90, 0, 0) * Cylinder(HOLES[p["kind"]]["d"] / 2, 10))
    from .rules import angle_holes
    cutters += [zcyl(xh, yh, 0, 100, 1.7) for (xh, yh) in angle_holes(P, "top")]
    return cut(part, cutters)


def angle_right(P):
    m = P.mech
    W, H, D = P.outer
    a = m["angles"]["right"]
    pr = m["stack_z"]["plate_rear"]
    t = m["wall"]
    L = a["y"][1] - a["y"][0]
    part = box(W - t - a["t"], a["y"][0], pr - a["leg_wall"], a["t"], L, a["leg_wall"]) + box(W - t - a["leg_plate"], a["y"][0], pr - a["t"], a["leg_plate"], L, a["t"])
    cutters = [Pos(W - t - a["t"] / 2, p["y"], p["z"]) * Rot(0, 90, 0) * Cylinder(HOLES[p["kind"]]["d"] / 2, 10) for p in m["right_face"]["ports"]]
    from .rules import angle_holes
    cutters += [zcyl(xh, yh, 0, 100, 1.7) for (xh, yh) in angle_holes(P, "right")]
    return cut(part, cutters)


def lime_pedestal(P):
    m = P.mech
    lp = m["lime_pedestal"]
    x, y, w, h = lp["rect"]
    pf = m["stack_z"]["plate_front"]
    part = box(x, y, pf, w, h, lp["h"])
    return cut(part, [zcyl(px, y + h / 2, 0, 100, 1.7) for px in (x + 5, x + w - 5)])


def rf_bay(P):
    m = P.mech
    rb = m["rf_bay"]
    x, y, w, h = rb["rect"]
    wt = rb["wall_t"]
    pr = m["stack_z"]["plate_rear"]
    z0, z1 = rb["lid_z"]
    walls = box(x, y, z1, wt, h, pr - z1) + box(x, y, z1, w, wt, pr - z1) + box(x + w - wt, y, z1, wt, h, pr - z1)
    walls = walls - angle_keepouts(P, rb["angle_clearance"])
    lid = box(x, y, z0, w, h, z1 - z0)
    c = m["closure"]
    lid = cut(lid, [zcyl(bx, by, -1, 100, c["boss_d"] / 2 + 0.5) for (bx, by) in c["bosses"] if x < bx < x + w and y < by < y + h])
    return walls, lid


def angle_keepouts(P, c):
    """Both legs of the top Al angle grown by c (the FR4 walls are notched round them)."""
    m = P.mech
    W, H, D = P.outer
    t = m["wall"]
    a = m["angles"]["top"]
    pr = m["stack_z"]["plate_rear"]
    L = a["x"][1] - a["x"][0] + 2 * c
    return [box(a["x"][0] - c, H - t - a["t"] - c, pr - a["leg_wall"] - c, L, a["t"] + c + 1.0, a["leg_wall"] + c + 1.0),
            box(a["x"][0] - c, H - t - a["leg_plate"] - c, pr - a["t"] - c, L, a["leg_plate"] + c + 1.0, a["t"] + c + 1.0)]


def cu_block(P):
    """Contact face at z = 0 (towards the board); the face over the LPDDR5 is recessed for its pad."""
    cb = P.mech["cu_block"]
    _, (bw, bh), (rx, ry, rw, rh), _ = cu_block_geometry(P)
    base = box(0, 0, 0, bw, bh, cb["t"])
    return base - box(rx, ry, -1.0, rw, rh, cb["ram_recess"] + 1.0)


def ufs_boss(P):
    """Al boss on the plate rear face under the UFS module (enclosure frame)."""
    from .rules import ufs_rect
    m = P.mech
    ub = m["ufs_boss"]
    x0, y0, x1, y1 = ufs_rect(P)
    pr = m["stack_z"]["plate_rear"]
    hb = m["q6a_mount"]["standoff"] - ub["module_below_board"] - ub["pad_gap"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # two M2.5 tapped holes (tap drill 2.05) for countersunk screws from the plate front face
    return cut(box(x0, y0, pr - hb, x1 - x0, y1 - y0, hb), [zcyl(cx + s * 5.0, cy, pr - hb - 1, pr + 1, 1.025) for s in (-1, 1)])


# ---- assembly ---------------------------------------------------------------------------------
def envelope_parts(P):
    """Labelled envelope boxes (keep-outs) for the assembly STEP; not vendor geometry."""
    out = []
    for iid, name, bx, it in item_boxes(P):
        if it.get("keep_clear"):
            continue
        b = box(bx[0], bx[1], bx[2], bx[3] - bx[0], bx[4] - bx[1], bx[5] - bx[2])
        b.label = f"envelope:{name}"
        out.append(b)
    return out
