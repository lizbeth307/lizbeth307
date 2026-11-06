"""Printed fixtures for the antennas and the IMU pack (exported at the origin, print orientation)."""
import math

from build123d import Align, Box, Circle, Cylinder, Helix, Plane, Pos, RegularPolygon, Rot, extrude, sweep

MIN = (Align.MIN, Align.MIN, Align.MIN)
CMIN = (Align.CENTER, Align.CENTER, Align.MIN)


def _cyl(r, h, z0=0.0):
    return Pos(0, 0, z0) * Cylinder(r, h, align=CMIN)


def helix_mandrel(spec, base=5.0, top=5.0, groove_extra=0.1, groove_depth=1.2):
    """Tube with a helical groove that holds the wire on the helix diameter (wire centre on spec d)."""
    r_w = spec["d"] / 2.0
    wire = spec["wire_d"] / 2.0
    h = spec["turns"] * spec["pitch"]
    H = base + h + top
    r_out = r_w - wire + groove_depth
    tube = _cyl(r_out, H) - _cyl(r_out - 4.0, H + 2, -1)
    flange = _cyl(r_out + 6.0, 3.0) - _cyl(r_out - 4.0, 5.0, -1)
    part = tube + flange
    hx = Helix(pitch=spec["pitch"], height=h, radius=r_w, lefthand=False)
    prof = Plane(origin=hx @ 0, z_dir=hx % 0) * Circle(wire + groove_extra)
    groove = Pos(0, 0, base) * sweep(prof, path=hx)
    part = part - groove
    for a in (60, 180, 300):
        part = part - Pos(20.0 * math.cos(math.radians(a)), 20.0 * math.sin(math.radians(a)), -1) * Cylinder(1.7, 6.0, align=CMIN)
    part = part - Pos(r_w, 0, -1) * Cylinder(wire + 0.6, base + 2, align=CMIN)
    return part


def neck_adapter(spec):
    nd = spec["neck_d"]
    sleeve = _cyl(nd / 2 + 5.0, 25.0) - _cyl(nd / 2 + 0.15, 27.0, -1)
    scale = _cyl(nd / 2 + 12.0, 4.0) - _cyl(nd / 2 + 0.15, 6.0, -1)
    part = sleeve + scale
    ticks = []
    for d in range(-spec["skew_range_deg"], spec["skew_range_deg"] + 1, spec["skew_step_deg"]):
        L = 5.0 if d % 15 == 0 else 3.0
        r = nd / 2 + 12.0 - L / 2
        ticks.append(Pos(r * math.cos(math.radians(90 + d)), r * math.sin(math.radians(90 + d)), 3.4) * Rot(0, 0, 90 + d) * Box(L, 0.8, 1.0))
    part = part.cut(*ticks)
    boss = Pos(nd / 2 + 5.0, 0, 15.0) * Rot(0, 90, 0) * Cylinder(4.5, 6.0)
    part = part + boss
    part = part - Pos(nd / 2 + 4.0, 0, 15.0) * Rot(0, 90, 0) * Cylinder(2.0, 12.0)
    return part


def throat_ring(spec):
    ir = spec["cap_od"] / 2 + 0.15
    ring = _cyl(ir + spec["wall"], spec["h"]) - _cyl(ir, spec["h"] + 2, -1)
    fl = _cyl(ir + spec["wall"] + spec["flange"], 2.5) - _cyl(ir, 5, -1)
    part = ring + fl
    rr = ir + spec["wall"] + spec["flange"] / 2
    for k in range(spec["holes"]):
        a = 360.0 * k / spec["holes"]
        part = part - Pos(rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a)), -1) * Cylinder(1.6, 5.0, align=CMIN)
    return part


def horn_ring(d, half_angle, holes=6, h=8.0, wall=2.4):
    """Stiffening ring that sits outside the cone at diameter d (cone wall taper ignored over 8 mm)."""
    r = d / 2.0
    ring = _cyl(r + wall, h) - _cyl(r + 0.2, h + 2, -1)
    for k in range(holes):
        a = 360.0 * k / holes + 30.0
        ring = ring - Pos((r + wall / 2) * math.cos(math.radians(a)), (r + wall / 2) * math.sin(math.radians(a)), h / 2) * Rot(0, 90, a) * Cylinder(1.6, wall + 4)
    return ring


def yagi_tape_clamp(y, split=False):
    bs = y["boom"]["section"][0] + 0.4
    w = bs + 6.0
    L = 20.0 if not split else 22.0 + 2 * 20.0
    body = Pos(-w / 2, -L / 2, 0) * Box(w, L, bs + 6.0, align=MIN)
    body = body - Pos(-bs / 2, -L / 2 - 1, 3.0) * Box(bs, L + 2, bs, align=MIN)
    seat_w = y["tape_w"] + 0.5
    if not split:
        body = body - Pos(-w / 2 - 1, -seat_w / 2, bs + 6.0 - 1.2) * Box(w + 2, seat_w, 2.0, align=MIN)
        holes = [(0.0, -6.0), (0.0, 6.0)]
    else:
        holes = []
        for s in (-1, 1):
            cy = s * (11.0 + 10.0)
            body = body - Pos(-w / 2 - 1, cy - seat_w / 2, bs + 6.0 - 1.2) * Box(w + 2, seat_w, 2.0, align=MIN)
            holes += [(0.0, cy - 5.0), (0.0, cy + 5.0)]
    for (hx, hy) in holes:
        body = body - Pos(hx, hy, bs + 3.0) * Cylinder(1.6, 8.0)
    body = body - Pos(w / 2 - 1.0, 0, 3.0 + bs / 2) * Rot(0, 90, 0) * Cylinder(2.0, 8.0)
    return body


def boom_spigot(y, inner=16.8, length=40.0):
    s = Pos(-inner / 2, -inner / 2, 0) * Box(inner, inner, length, align=MIN)
    key = Pos(inner / 2 - 0.01, -1.0, 0) * Box(1.0, 2.0, length, align=MIN)
    stop = Pos(-inner / 2 - 1.6, -inner / 2 - 1.6, length / 2 - 1.5) * Box(inner + 3.2, inner + 3.2, 3.0, align=MIN)
    return s + key + stop


def imu_carrier(P):
    I = P.imu
    hb = P.parts["hammond_1550z101"]
    ix, iy = hb["inside"][0] - 0.6, hb["inside"][1] - 0.6
    t = I["carrier"]["t"]
    plate = Box(ix, iy, t, align=MIN)
    tx, ty = I["tripod"]["c"]
    boss = Pos(tx, ty, 0) * Cylinder(6.0, 14.0, align=CMIN)
    part = plate + boss
    part = part - Pos(tx, ty, -1) * Cylinder(4.3, 16.0, align=CMIN)
    bx, by = I["boards"]["origin_in_box"]
    pw, ph = I["boards"]["pair"]
    for (sx, sy) in ((bx + 2.5, by + 2.5), (bx + pw - 2.5, by + 2.5), (bx + 2.5, by + ph - 2.5), (bx + pw - 2.5, by + ph - 2.5)):
        part = part + Pos(sx, sy, 0) * (Cylinder(2.5, t + I["boards"]["standoff_h"], align=CMIN) - Pos(0, 0, 3) * Cylinder(1.0, 20, align=CMIN))
    for (sx, sy) in I["carrier"]["screws"]:
        part = part - Pos(sx, sy, -1) * Cylinder(2.0, t + 2, align=CMIN)
    return part


def helicone_disk(P):
    hc = P.antennas["helicone"]
    R = hc["disk_d"] / 2
    d = Cylinder(R, hc["disk_t"], align=CMIN)
    cut = [Pos(0, 0, -1) * Cylinder(hc["mount_hole_d"] / 2, 5, align=CMIN), Pos(hc["feed_r"], 0, -1) * Cylinder(hc["feed_hole_d"] / 2, 5, align=CMIN)]
    rr = R - hc["petals"]["tab"] / 2
    off = math.degrees(math.asin((hc["petals"]["inner_chord"] / 4) / rr))
    for k in range(8):
        for s in (-1, 1):
            a = math.radians(22.5 + 45 * k + s * off)
            cut.append(Pos(rr * math.cos(a), rr * math.sin(a), -1) * Cylinder(1.6, 5, align=CMIN))
    for a in (60, 180, 300):
        cut.append(Pos(20 * math.cos(math.radians(a)), 20 * math.sin(math.radians(a)), -1) * Cylinder(1.7, 5, align=CMIN))
    return d.cut(*cut)
