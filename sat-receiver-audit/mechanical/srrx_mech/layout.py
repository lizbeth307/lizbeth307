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
    """Cooler-A block in board (u, v) terms: origin, size, LPDDR5 recess and SoC rectangles (block-local mm).

    The block covers SoC and LPDDR5 with cu_block.margin and is clipped to the cooler keep-in
    (parts.json q6a_cooler_zone keep_in_uv)."""
    q = P.parts["q6a"]
    cb = P.mech["cu_block"]
    soc, ram = q["soc"]["uv"], q["lpddr5"]["uv"]
    mg = cb["margin"]
    ki = P.parts["q6a_cooler_zone"]["keep_in_uv"]
    u0, v0 = max(ki[0], min(soc[0], ram[0]) - mg), max(ki[1], min(soc[1], ram[1]) - mg)
    u1, v1 = min(ki[2], max(soc[2], ram[2]) + mg), min(ki[3], max(soc[3], ram[3]) + mg)
    bw, bh = min(cb["max"][0], u1 - u0), min(cb["max"][1], v1 - v0)
    recess = (ram[0] - u0 - 0.5, ram[1] - v0 - 0.5, ram[2] - ram[0] + 1.0, ram[3] - ram[1] + 1.0)
    soc_r = (soc[0] - u0, soc[1] - v0, soc[2] - soc[0], soc[3] - soc[1])
    return (u0, v0), (bw, bh), recess, soc_r


def q6a_top_z(P):
    """z of the Q6A component face (it faces the rear wall)."""
    m = P.mech["q6a_mount"]
    return P.mech["stack_z"]["plate_rear"] - m["standoff"] - P.parts["q6a"]["board"][2]


def cooler_boxes(P):
    """Cooler A: Cu block on SoC/LPDDR5, fin/spacer zone in the keep-in up to the fan face, Noctua fan (enclosure boxes)."""
    q = P.parts["q6a"]
    cz = P.parts["q6a_cooler_zone"]
    cb = P.mech["cu_block"]
    x0, y0 = P.mech["q6a_mount"]["origin"]
    bu = q["board"][0]
    zt = q6a_top_z(P)

    def uv(u0, v0, u1, v1):
        return x0 + bu - u1, y0 + v0, x0 + bu - u0, y0 + v1
    (u0, v0), (bw, bh), _, _ = cu_block_geometry(P)
    soc_top = zt - q["soc"]["top"]
    blk_top = soc_top - cb["t"]
    fan_face = zt - cb["fan_above_board"]
    a = uv(u0, v0, u0 + bw, v0 + bh)
    k = uv(*cz["keep_in_uv"])
    cu, cv = cz["center_in_board"]
    fw, fh, ft = cz["fan"]
    f = uv(cu - fw / 2, cv - fh / 2, cu + fw / 2, cv + fh / 2)
    return [("cooler_a.block", (a[0], a[1], blk_top, a[2], a[3], soc_top)),
            ("cooler_a.fins", (k[0], k[1], fan_face, k[2], k[3], blk_top)),
            ("cooler_a.fan", (f[0], f[1], fan_face - ft, f[2], f[3], fan_face))]


SMA_KINDS = ("sma_pigtail", "sma_k", "sma_cab01075", "sma_adamtech", "sma_cab718")


def port_inner(P, p):
    """Envelope of a panel port's parts inside the wall as (radius, depth from the inner wall face, basis), or None if unread.

    Front-side-nut SMA bulkheads (nut and washer outside): the connector body (hex) on the inner face.
    VFA340 (flange outside): washer, nut and the rest of the long side. GX12: nut corners and the rear thread with the solder cups.
    A port without a part entry keeps the representative SMA hardware envelope (parts.json sma_bulkhead_hw)."""
    part = P.parts.get(p.get("part", ""))
    kind = p["kind"]
    if kind == "tbd" or (part and part.get("status") == "listing"):
        return None
    if part is None:
        if kind in SMA_KINDS:
            hw = P.parts["sma_bulkhead_hw"]
            return hw["washer_od"] / 2.0, hw["washer_t"] + hw["nut_t"], "sma_bulkhead_hw (representative hardware, part not read)"
        return None
    if kind == "f_bulkhead":
        long_side = part["overall"] - part["short_side"] - part["flange_t"]
        r = max(part["washer"][0] / 2.0, part["nut_af"] / math.cos(math.radians(30)) / 2.0)
        return r, long_side - port_wall(P, p), "washer, nut and the long side inside (cinch_vfa340)"
    if kind == "gx12":
        # the drawing's nut size is across flats: the envelope takes the corners
        return part["nut_af"] / math.cos(math.radians(30)) / 2.0, part["behind_reserve"], "nut (corners) and rear thread with solder cups (kinghelm_gx12_6p)"
    if "inner_d" in part and "inner_depth" in part:
        return part["inner_d"] / 2.0, part["inner_depth"], f"collar, rear body and lead bend inside, nut outside ({p['part']})"
    if "body_od_reserve" in part:
        depth = part.get("body_len_reserve", part.get("body_len", 0.0) - part.get("thread_len", 0.0))
        return part["body_od_reserve"] / 2.0, depth, f"connector body inside, nut outside ({p['part']})"
    if "body_hex_af" in part:
        depth = part["body_hex_len"] + part["body_hex_len_tol"] if "body_hex_len" in part else part["body_len_reserve"]
        return part["body_hex_af"] / math.cos(math.radians(30)) / 2.0, depth, f"connector body hex inside, nut outside ({p['part']})"
    return None


def port_wall(P, p):
    """Panel thickness at a port: ASA wall + Al angle on the top and right faces, the ASA wall alone elsewhere."""
    m = P.mech
    if p in m["top_face"]["ports"]:
        return m["wall"] + m["angles"]["top"]["t"]
    a = m["angles"]["right"]
    if p in m["right_face"]["ports"] and a["y"][0] <= p["y"] <= a["y"][1]:
        return m["wall"] + a["t"]
    return m["wall"]


def bulkhead_nut_boxes(P):
    """Inner envelope (nut.<port>) of every read panel port: hardware or connector body inside the wall (port_inner)."""
    m = P.mech
    W, H, D = P.outer
    t = m["wall"]
    out = []
    a = m["angles"]["top"]
    y1 = H - t - a["t"]
    zc = m["top_face"]["ports_z"]
    for p in m["top_face"]["ports"]:
        e = port_inner(P, p)
        if e:
            r, th, _ = e
            out.append((f"nut.{p['id']}", (p["x"] - r, y1 - th, zc - r, p["x"] + r, y1, zc + r)))
    a = m["angles"]["right"]
    x1 = W - t - a["t"]
    for p in m["right_face"]["ports"]:
        e = port_inner(P, p)
        if e:
            r, th, _ = e
            out.append((f"nut.{p['id']}", (x1 - th, p["y"] - r, p["z"] - r, x1, p["y"] + r, p["z"] + r)))
    for p in m["right_face"].get("panel", []):        # panel parts on the bare ASA wall (no Al angle), W2 MECH-3
        e = port_inner(P, p)
        if e:
            r, th, _ = e
            out.append((f"nut.{p['id']}", (W - t - th, p["y"] - r, p["z"] - r, W - t, p["y"] + r, p["z"] + r)))
    for p in m["bottom_face"]["ports"]:
        e = port_inner(P, p)
        if e:
            r, th, _ = e
            out.append((f"nut.{p['id']}", (p["x"] - r, t, p["z"] - r, p["x"] + r, t + th, p["z"] + r)))
    return out


def board_boxes(P, bid, at=None):
    b = P.boards["boards"][bid]
    pl = b["place"]
    if at is not None:
        ox, oy = b["place_at"][at]
    else:
        ox, oy = pl["origin"]
    t = P.boards["stackup"]["t"]
    z0 = pl["z_bottom"]
    out = []

    def zspan(h):
        # z0 is the face opposite the components (towards the mounting surface)
        return (z0, z0 + t + h) if pl["facing"] == "+z" else (z0 - t - h, z0)
    for i, r in enumerate(b["rects"]):
        za, zb = zspan(b["max_height"])
        out.append((f"{bid}.r{i}", (ox + r[0], oy + r[1], za, ox + r[0] + r[2], oy + r[1] + r[3], zb)))
        # a taller height zone raises only its own part of the rectangle (W2 MECH-3: the PWR-A windows under PWR-B)
        for j, zn in enumerate(b.get("height_zones", [])):
            if zn["max_height"] <= b["max_height"]:
                continue
            q = zn["rect"]
            x0, y0 = max(r[0], q[0]), max(r[1], q[1])
            x1, y1 = min(r[0] + r[2], q[0] + q[2]), min(r[1] + r[3], q[1] + q[3])
            if x1 > x0 and y1 > y0:
                za, zb = zspan(zn["max_height"])
                out.append((f"{bid}.r{i}z{j}", (ox + x0, oy + y0, za, ox + x1, oy + y1, zb)))
    return out


def item_boxes(P):
    items = []
    for it in P.mech["layout"]["items"]:
        if "board" in it:
            for name, bx in board_boxes(P, it["board"], it.get("at")):
                items.append((it["id"], name, bx, it))
        elif it.get("part") == "q6a" and "box" not in it:
            for name, bx in q6a_boxes(P):
                items.append((it["id"], name, bx, it))
        elif it.get("derived") == "cooler_a":
            for name, bx in cooler_boxes(P):
                items.append((it["id"], name, bx, it))
        else:
            items.append((it["id"], it["id"], _box(it["box"]), it))
    for name, bx in bulkhead_nut_boxes(P):
        items.append((name, name, bx, {"id": name, "mount": "angle", "derived": "bulkhead_nut"}))
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
    r = m["plate"]["mount_boss_d"] / 2.0
    for i, b in enumerate(m["plate"]["mount_bosses"]):
        bx, by = b["c"]
        out.append((f"plate.boss{i}", (bx - r, by - r, pf, bx + r, by + r, m["plate"]["mount_boss_top"])))
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
    ("flamingo", "rfbay.lid"), ("battery_tray", "closure.boss"),   # the tray has slots round the wall-hugging bosses
    ("battery_pack", "battery_tray"),                                # the pack lies inside its tray
    ("pwr_key_body", "pwr_key_nut"),                                 # the nut sits on the key thread
    ("pwr_key_nut", "plate.main"),                                   # the plate has an open notch under the nut (plate.notches; the solid check sees it)
    ("tripod_boss", "rear"), ("gx16", "rear"), ("hatch_parts", "rear"), ("q6a_fan_duct", "rear"),
    ("enc_main", "board_ctrl"), ("enc_volume", "board_ctrl"), ("closure.boss", "rfbay.lid"),
    ("v4l_", "usb_socket_"), ("usb_lead_", "usb_socket_"),           # the V4L plug mates into its socket; the lead leaves the socket pads (W2 MECH-3)
    ("usb_socket_", "rfbay.lid"), ("usb_lead_", "rfbay.wall.bottom"),  # socket carriers on the lid; lead B through notch N3
    ("q6a.usb_stack", "usb_plug_bay"), ("q6a.hdmi", "hdmi_plug_ra"),
    ("q6a.board", "plate.ufs_boss"),  # contact through the UFS pad by design (thermal T-UFS)
    ("cooler_a", "q6a.board"),         # the cooler sits in the generic 7.5 mm component zone of the Q6A envelope
    ("cooler_a", "q6a_fan_duct"),      # the duct starts at the fan face
    ("nut.", "angle."),                # bulkhead nut / connector body clamps the Al angle
    ("hdmi_route", "hdmi_plug_ra"), ("hdmi_route", "hdmi_route"), ("hdmi_route", "plate."), ("hdmi_route", "hdmi_board"),
    ("t7_gland_body", "rear"), ("t7_gland_outside", "rear"),
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
    boxes = [(iid, name, bx, it) for iid, name, bx, it in item_boxes(P)] + [(n, n, bx, {}) for n, bx in structure_boxes(P)]
    results = []
    for (ia, na, ba, _), (ib, nb, bb, _) in itertools.combinations(boxes, 2):
        if ia == ib:
            continue
        if joined(na, nb):
            continue
        g = gap(ba, bb)
        if g < min_gap and not allowed(na, nb) and not allowed(ia, ib):
            results.append({"a": na, "b": nb, "gap_mm": round(g, 2), "result": "FAIL (model)" if g < 0 else "TIGHT (model)"})
    outside = []
    for iid, name, bx, it in boxes:
        if iid.startswith(("tripod_boss", "closure.", "plate.", "angle.")) or it.get("outside"):
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
