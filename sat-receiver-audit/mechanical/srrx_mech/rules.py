"""Design rules of build/05 6 and STACK 5.8 evaluated on the model (MODEL FIT ONLY).

Each rule returns {id, rule, value, limit, result, source}. result is one of
'PASS (model)', 'FAIL (model)' or 'OPEN: <what is missing>'. OPEN rows need a
measured or chosen part and never fail the CI gate; FAIL rows do.
"""
import math

from .layout import item_boxes


def _rect_gap(a, b):
    """In-plane gap between two rectangles (x0, y0, x1, y1); negative = overlap."""
    dx = max(b[0] - a[2], a[0] - b[2])
    dy = max(b[1] - a[3], a[1] - b[3])
    if dx < 0 and dy < 0:
        return max(dx, dy)
    return math.hypot(max(dx, 0.0), max(dy, 0.0))


def ufs_rect(P):
    """UFS boss contact face in enclosure x/y (the Q6A hangs component side to the rear, map in q6a_mount)."""
    m = P.mech
    u, v = m["ufs_boss"]["centre_uv"]
    cw, ch = m["ufs_boss"]["contact"]
    x0, y0 = m["q6a_mount"]["origin"]
    bw = P.parts["q6a"]["board"][0]
    cx, cy = x0 + bw - u, y0 + v
    return (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)


def _res(ok):
    return "PASS (model)" if ok else "FAIL (model)"


def plate_outline(P):
    pl = P.mech["plate"]
    x, y, w, h = pl["main"]
    ex, ey, ew, eh = pl["ext"]
    return [(x, y), (ex, y), (ex, ey), (ex + ew, ey), (x + w, y + h), (x, y + h)]


def plate_windows(P):
    pl = P.mech["plate"]
    out = []
    for key in ("riser_window", "hdmi_slot"):
        x, y, w, h = pl[key]
        out.append((key, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]))
    return out


def plate_holes(P):
    """Every hole of the mid-plate (enclosure x/y): id, centre, diameter, what goes in, min edge distance."""
    m = P.mech
    pl = m["plate"]
    H = P.outer
    out = []
    for i, (bx, by) in enumerate(pl["mount_bosses"]):
        out.append({"id": f"PM{i + 1}", "c": (bx, by), "d": pl["mount_hole_d"], "use": "M3 screw into the front-shell boss insert"})
    for bid in ("PWR", "RF"):
        b = P.boards["boards"][bid]
        f = P.parts[b["plate_fastener"]]
        ox, oy = b["place"]["origin"]
        for i, (hx, hy) in enumerate(b["holes"]):
            out.append({"id": f"{bid}{i + 1}", "c": (ox + hx, oy + hy), "d": f["hole_d"], "use": f["name"].split(" (")[0],
                        "edge_min": f["edge_min"]})
    q = P.parts["q6a"]
    x0, y0 = m["q6a_mount"]["origin"]
    e, (pu, pv) = q["holes"]["edge"], q["holes"]["pitch"]
    k = 0
    for u in (e, e + pu):
        for v in (e, e + pv):
            k += 1
            out.append({"id": f"Q6A{k}", "c": (x0 + q["board"][0] - u, y0 + v), "d": 2.9, "use": "M2.5 through, 6 mm F-F standoff on the rear face"})
    lp = m["lime_pedestal"]["rect"]
    for i, px in enumerate((lp[0] + 5, lp[0] + lp[2] - 5)):
        out.append({"id": f"LP{i + 1}", "c": (px, lp[1] + lp[3] / 2), "d": 3.4, "use": "M3 Lime pedestal (front face)"})
    at = m["angles"]["top"]
    for i in range(5):
        out.append({"id": f"AT{i + 1}", "c": (at["x"][0] + 8 + i * ((at["x"][1] - at["x"][0] - 16) / 4), H[1] - m["wall"] - at["leg_plate"] / 2),
                    "d": 3.4, "use": "M3 + nut, top Al angle"})
    ar = m["angles"]["right"]
    for i, yh in enumerate((ar["y"][0] + 6, (ar["y"][0] + ar["y"][1]) / 2, ar["y"][1] - 6)):
        out.append({"id": f"AR{i + 1}", "c": (H[0] - m["wall"] - ar["leg_plate"] / 2, yh), "d": 3.4, "use": "M3 + nut, right Al angle"})
    for bp in pl["bond_points"]:
        out.append({"id": bp["id"], "c": tuple(bp["c"]), "d": 3.4, "use": "M3 + serrated washer, bare metal (RF GND/CHASSIS)"})
    ux0, uy0, ux1, uy1 = ufs_rect(P)
    for i, s in enumerate((-1, 1)):
        out.append({"id": f"UB{i + 1}", "c": ((ux0 + ux1) / 2 + s * 5.0, (uy0 + uy1) / 2), "d": 2.9,
                    "use": "M2.5 countersunk from the front face into the UFS boss (tapped M2.5)"})
    return out


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def edge_distance(P, c):
    polys = [plate_outline(P)] + [w for _, w in plate_windows(P)]
    return min(_seg_dist(c, a, b) for poly in polys for a, b in zip(poly, poly[1:] + poly[:1]))


def evaluate(P):
    m = P.mech
    out = []
    # UFS boss >= 30 mm from the Lime pedestal and the regulator bond zones (heat spreading in the plate).
    ur = ufs_rect(P)
    x, y, w, h = m["lime_pedestal"]["rect"]
    g = _rect_gap(ur, (x, y, x + w, y + h))
    out.append({"id": "R-UFS-LIME", "rule": "UFS boss to the Lime pedestal (in the plate plane)", "value_mm": round(g, 1), "limit_mm": 30.0,
                "result": _res(g >= 30.0), "source": "STACK 5.8 / build/05 6"})
    b = P.boards["boards"]["PWR"]
    ox, oy = b["place"]["origin"]
    gz = min(_rect_gap(ur, (ox + r[0], oy + r[1], ox + r[0] + r[2], oy + r[1] + r[3])) for r in b["thermal_bond"])
    out.append({"id": "R-UFS-REG", "rule": "UFS boss to the regulator bond zones of the PWR board", "value_mm": round(gz, 1), "limit_mm": 30.0,
                "result": _res(gz >= 30.0), "source": "STACK 5.8 / build/05 6"})
    # IP2368 >= 10 mm from the cells.
    boxes = {iid: bx for iid, name, bx, it in item_boxes(P) if iid in ("ip2368", "battery_tray")}
    a, c = boxes["ip2368"], boxes["battery_tray"]
    d = math.sqrt(sum(max(0.0, max(c[i] - a[i + 3], a[i] - c[i + 3])) ** 2 for i in range(3)))
    out.append({"id": "R-IP2368", "rule": "IP2368 board to the battery compartment", "value_mm": round(d, 1), "limit_mm": 10.0,
                "result": _res(d >= 10.0), "source": "STACK 5.6 / build/05 6"})
    # Encoder bushing stack on the 7 mm M7x0.75 thread: O-ring + wall + washer + nut <= 6.5 and >= 0.5 thread left.
    pec = P.parts["pec11r"]
    eb = m["hmi"]["encoder_boss"]
    stack = eb["oring_t"] + eb["wall"] + pec["washer"][2] + pec["nut_t"]
    out.append({"id": "R-ENC", "rule": "PEC11R bushing stack (O-ring + boss wall + washer + nut)", "value_mm": round(stack, 2), "limit_mm": 6.5,
                "thread_left_mm": round(pec["bushing_len"] - stack, 2),
                "result": _res(stack <= 6.5 and pec["bushing_len"] - stack >= 0.5), "source": "STACK 5.8; Bourns PEC11R datasheet (parts.json)"})
    # Button caps: edge-to-edge gap.
    bt = m["hmi"]["buttons"]
    gap = min(bt["cols_x"][1] - bt["cols_x"][0], abs(bt["rows_y"][0] - bt["rows_y"][1])) - bt["cap_d"]
    out.append({"id": "R-KEYS", "rule": "button caps, edge-to-edge gap (pitch 22: STACK allows 22-25 when the face height permits)",
                "value_mm": round(gap, 1), "limit_mm": [7.0, 13.0], "result": _res(7.0 <= gap <= 13.0), "source": "STACK 5.8"})
    # Tripod nut pocket.
    tp = m["rear_face"]["tripod"]
    ok = tp["outer_wall"] <= 1.0 and tp["behind"] >= 3.0 and abs(tp["hex_af"] - 11.3) < 1e-6
    out.append({"id": "R-TRIPOD", "rule": "captive 1/4-20 nut pocket: outer wall <= 1.0, 11.3 AF, >= 3 mm behind the nut",
                "value_mm": [tp["outer_wall"], tp["hex_af"], tp["behind"]], "result": _res(ok), "source": "STACK D15 / 5.8"})
    # Panel bulkheads: thread engagement needs the bulkhead thread length, which no chosen part gives yet.
    wall = m["wall"] + m["angles"]["top"]["t"]
    out.append({"id": "R-SMA-THREAD", "rule": "bulkhead thread through ASA wall + Al angle with O-ring, lock washer and nut, >= 3 full threads left (1/4-36: 3 x 0.706 mm)",
                "value_mm": wall, "limit_mm": "thread length of the chosen bulkhead >= wall + O-ring + washer + nut + 2.1",
                "result": "OPEN: bulkhead/pigtail MPN and its thread length not chosen (MECH-07); check on the received part",
                "source": "STACK 5.8 'стінка 4-5 мм'"})
    # PWR pad zones must stay clear of the screw keep-outs (a pad never needs a hole).
    b = P.boards["boards"]["PWR"]
    kr = b["hole_keepout_d"] / 2
    worst = min(_rect_gap((hx, hy, hx, hy), (z[0], z[1], z[0] + z[2], z[1] + z[3])) - kr for hx, hy in b["holes"] for z in b["thermal_bond"])
    out.append({"id": "R-PWR-PADS", "rule": "PWR thermal-pad zones clear of the screw keep-outs (margin, worst pair)", "value_mm": round(worst, 2),
                "limit_mm": 0.0, "result": _res(worst >= 0.0), "source": "boards.json PWR"})
    # Every plate hole: centre at least one diameter from an edge or window (web >= d/2).
    worst = min(((edge_distance(P, h["c"]) - h["d"], h["id"]) for h in plate_holes(P)))
    out.append({"id": "R-HOLE-EDGE", "rule": "plate holes: centre-to-edge distance minus the hole diameter (worst hole)", "value_mm": round(worst[0], 2),
                "limit_mm": 0.0, "hole": worst[1], "result": _res(worst[0] >= 0.0), "source": "design rule of this package (web >= d/2 in 2 mm Al)"})
    # Self-clinching fasteners: hole centre to the plate edge or a window.
    worst = None
    for h in plate_holes(P):
        if "edge_min" in h:
            d = edge_distance(P, h["c"])
            if worst is None or d - h["edge_min"] < worst[1] - worst[2]:
                worst = (h["id"], d, h["edge_min"])
    out.append({"id": "R-CLINCH-EDGE", "rule": "self-clinching nut/standoff: hole centre to the nearest plate edge or window (worst hole)",
                "value_mm": round(worst[1], 2), "limit_mm": worst[2], "hole": worst[0], "result": _res(worst[1] >= worst[2]),
                "source": "PEM data (parts.json pem_f_m3_1, pem_so_m3_3)"})
    return out


def bay_packing(P):
    """Can the RF bay lid carry both V4L dongles with the female ends of their USB leads and the two LNA cases?

    Rows along x on the lid; the modules sit next to each other in two rows (layout). The check adds the
    socket reserve in line with each dongle and compares the row lengths with the inner bay width."""
    rb = P.mech["rf_bay"]
    x, y, w, h = rb["rect"]
    wt = rb["wall_t"]
    inner_w = w - (2 if "right" in rb["walls"] else 1) * wt
    inner_h = h - wt
    v4l = P.parts["v4l"]["size"]
    lna = P.parts["sawbird_noaa"]["size"]
    sock = rb["usb_socket_reserve"]
    rows = {
        "layout (two dongles in one row)": 2 * (v4l[0] + sock[0]),
        "alternative (dongle + socket + LNA case per row)": v4l[0] + sock[0] + lna[0],
    }
    alt_h = 2 * max(v4l[1], lna[1])
    res = {"inner_mm": [round(inner_w, 1), round(inner_h, 1)], "v4l_reserve": v4l, "socket_reserve": sock, "lna_case": lna[:2],
           "rows_mm": {k: round(v, 1) for k, v in rows.items()}, "alternative_height_mm": round(alt_h, 1)}
    fits_layout = rows["layout (two dongles in one row)"] <= inner_w
    fits_alt = rows["alternative (dongle + socket + LNA case per row)"] <= inner_w and alt_h <= inner_h
    if fits_layout or fits_alt:
        res["result"] = "PASS (model)"
    else:
        res["result"] = ("OPEN: the female USB ends of the two V4L leads are not inside the modelled bay; with the current reserves "
                         "neither arrangement fits (measure the V4L and the socket, then re-pack or move the cased LNA modules out of the bay)")
    return res
