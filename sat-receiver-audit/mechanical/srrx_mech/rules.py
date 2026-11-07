"""Design rules of build/05 6 and STACK 5.8 evaluated on the model (MODEL FIT ONLY).

Each rule returns {id, rule, value, limit, result, source}. result is one of
'PASS (model)', 'FAIL (model)' or 'OPEN: <what is missing>'. OPEN rows need a
measured or chosen part and never fail the CI gate; FAIL rows do.
"""
import itertools
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


def _corner_arc(prev, corner, nxt, centre, r, n=12):
    """Replace `corner` of a polygon by the arc of radius r about `centre` between its two edges (short way)."""
    def hit(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        fx, fy = a[0] - centre[0], a[1] - centre[1]
        A, B, C = dx * dx + dy * dy, 2 * (fx * dx + fy * dy), fx * fx + fy * fy - r * r
        disc = max(0.0, B * B - 4 * A * C)
        ts = [(-B - math.sqrt(disc)) / (2 * A), (-B + math.sqrt(disc)) / (2 * A)]
        ts = [t for t in ts if -1e-9 <= t <= 1 + 1e-9]
        return a[0] + dx * ts[0], a[1] + dy * ts[0]
    p0 = hit(corner, prev)
    p1 = hit(corner, nxt)
    a0 = math.atan2(p0[1] - centre[1], p0[0] - centre[0])
    a1 = math.atan2(p1[1] - centre[1], p1[0] - centre[0])
    d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    return [(centre[0] + r * math.cos(a0 + d * i / n), centre[1] + r * math.sin(a0 + d * i / n)) for i in range(n + 1)]


def plate_outline(P):
    """Plate outline; corners that reach into the rounded shell corners follow the corner arc (inner radius - clearance)."""
    pl = P.mech["plate"]
    x, y, w, h = pl["main"]
    ex, ey, ew, eh = pl["ext"]
    poly = [(x, y), (ex, y), (ex, ey), (ex + ew, ey)]
    for (nx, ny, nw, nh) in sorted(pl.get("notches_right", [])):          # open notches in the right edge, bottom to top
        poly += [(nx + nw, ny), (nx, ny), (nx, ny + nh), (nx + nw, ny + nh)]
    poly.append((x + w, y + h))
    for (nx, ny, nw, nh) in sorted(pl.get("notches", []), reverse=True):   # open notches in the top edge, right to left
        poly += [(nx + nw, y + h), (nx + nw, ny), (nx, ny), (nx, y + h)]
    poly.append((x, y + h))
    W, H, _ = P.outer
    t, R = P.mech["wall"], P.mech["outer"]["corner_r"]
    r = R - t - pl["corner_clearance"]
    centres = [(R, R), (W - R, R), (W - R, H - R), (R, H - R)]
    out = []
    for i, c in enumerate(poly):
        prev, nxt = poly[i - 1], poly[(i + 1) % len(poly)]
        cc = next((k for k in centres if (c[0] - k[0]) * (k[0] - W / 2) > 0 and (c[1] - k[1]) * (k[1] - H / 2) > 0
                   and math.hypot(c[0] - k[0], c[1] - k[1]) > r), None)
        out += _corner_arc(prev, c, nxt, cc, r) if cc else [c]
    return out


def plate_windows(P):
    """Closed openings of the plate: the riser window and the harness slots (mechanical.json plate.slots)."""
    pl = P.mech["plate"]
    out = []
    for key in ("riser_window", "hdmi_slot"):
        if key not in pl:
            continue
        x, y, w, h = pl[key]
        out.append((key, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]))
    for sl in pl.get("slots", []):
        x, y, w, h = sl["rect"]
        out.append((sl["id"], [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]))
    return out


def plate_holes(P):
    """Every hole of the mid-plate (enclosure x/y): id, centre, diameter, what goes in, min edge distance."""
    m = P.mech
    pl = m["plate"]
    H = P.outer
    out = []
    for i, b in enumerate(pl["mount_bosses"]):
        out.append({"id": f"PM{i + 1}", "c": tuple(b["c"]), "d": pl["mount_hole_d"], "use": "M3 screw into the front-shell boss insert"})
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
    af = P.parts[m["angles"]["fastener"]]
    at = m["angles"]["top"]
    for i, (xh, yh) in enumerate(angle_holes(P, "top")):
        out.append({"id": f"AT{i + 1}", "c": (xh, yh), "d": af["hole_d"], "edge_min": af["edge_min"],
                    "use": "PEM F-M3-1; M3 from the rear through the top Al angle"})
    for i, (xh, yh) in enumerate(angle_holes(P, "right")):
        out.append({"id": f"AR{i + 1}", "c": (xh, yh), "d": af["hole_d"], "edge_min": af["edge_min"],
                    "use": "PEM F-M3-1; M3 from the rear through the right Al angle"})
    for bp in pl["bond_points"]:
        out.append({"id": bp["id"], "c": tuple(bp["c"]), "d": 3.4, "use": "M3 + serrated washer, bare metal (RF GND/CHASSIS)"})
    ux0, uy0, ux1, uy1 = ufs_rect(P)
    for i, s in enumerate((-1, 1)):
        out.append({"id": f"UB{i + 1}", "c": ((ux0 + ux1) / 2 + s * 5.0, (uy0 + uy1) / 2), "d": 2.9,
                    "use": "M2.5 countersunk from the front face into the UFS boss (tapped M2.5)"})
    return out


def angle_holes(P, which):
    """Plate-leg screw axes of the Al angles (enclosure x/y): hole_inset from the free edge of the plate leg."""
    m = P.mech
    W, H, _ = P.outer
    t = m["wall"]
    a = m["angles"][which]
    if which == "top":
        y = H - t - a["leg_plate"] + a["hole_inset"]
        return [(xh, y) for xh in a["holes_x"]]
    x = W - t - a["leg_plate"] + a["hole_inset"]
    return [(x, yh) for yh in a["holes_y"]]


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
    # Panel bulkheads: thread left for mating per port, and the inner hardware envelopes (W2 MECH-2, makers' drawings).
    out.append(sma_thread_rule(P))
    out.append(bulkhead_nuts_rule(P))
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
    # Seam: every closure-screw hole stays inboard of the groove by at least the land (the screws are inside the seal).
    gk = m["gasket"]
    groove_in = gk["land"] + gk["groove_w"] - gk["belt"]
    worst = min((outer_depth(P, (bx, by)) - m["closure"]["insert"]["hole_d"] / 2 - groove_in, (bx, by)) for (bx, by) in m["closure"]["bosses"])
    out.append({"id": "R-SEAM-HOLES", "rule": "closure insert holes inboard of the seam groove (wall left between hole and groove, worst boss)",
                "value_mm": round(worst[0], 2), "limit_mm": gk["land"], "boss": list(worst[1]), "result": _res(worst[0] >= gk["land"] - 1e-6),
                "source": "seam design of this package (mechanical.json gasket, closure)"})
    # Vents: the flat seat thickness must suit the LTW through-hole mounting.
    lv = P.parts["ltw_vent"]
    lo, hi = lv["panel_t"]
    ok = all((v["pad_t"] >= lv["threaded_hole_min"]) if v["kind"].endswith("_threaded") else (lo <= v["pad_t"] <= hi) for v in m["vents"])
    out.append({"id": "R-VENT-SEAT", "rule": "vent seats: threaded hole >= 4.0 mm, or 2.0-3.5 mm through hole with the nut",
                "value_mm": {v["id"]: v["pad_t"] for v in m["vents"]}, "limit_mm": {"threaded": lv["threaded_hole_min"], "through": [lo, hi]},
                "result": _res(ok), "source": "Amphenol LTW vent datasheet (parts.json ltw_vent)"})
    # Vent threads: the 10 mm thread minus the seat must not reach a part (threaded-hole vents have no nut inside).
    worst = None
    for v in m["vents"]:
        reach = lv["thread_len"] - v["pad_t"]
        depth = vent_clearance(P, v)
        if worst is None or depth - reach < worst[0]:
            worst = (depth - reach, v["id"], round(reach, 2), round(depth, 2))
    out.append({"id": "R-VENT-REACH", "rule": "space behind each vent seat minus the thread reach (worst vent)", "value_mm": round(worst[0], 2),
                "limit_mm": 0.5, "vent": worst[1], "thread_reach_mm": worst[2], "space_mm": worst[3], "result": _res(worst[0] >= 0.5),
                "source": "LTW drawing: thread 10.0 (parts.json ltw_vent); envelopes in mechanical.json layout"})
    # Side-face cut-outs: on the flat part of the face (corner radii excluded) and clear of the seam plane.
    from .features import face_features
    W, H, D = P.outer
    R, zs = m["outer"]["corner_r"], m["split_z"]
    keep = gk["belt_h"] + 0.5          # the external seam belt (1.9 mm proud, belt_h on each shell) plus a margin
    bad = []
    for face, feats in face_features(P).items():
        if face in ("front", "rear"):
            continue
        for f in feats:
            hu = f["w"] / 2 if "w" in f and f["kind"] in ("grille", "tbd") else max(f["d"], f.get("flange_d", 0.0)) / 2
            hv = f["h"] / 2 if "h" in f and f["kind"] in ("grille", "tbd") else max(f["d"], f.get("flange_d", 0.0)) / 2
            if face in ("top", "bottom"):
                along, alen, z_lo, z_hi = (f["u"] - hu, f["u"] + hu), W, None, None
                z_lo, z_hi = ((D - f["v"] - hv, D - f["v"] + hv) if face == "top" else (f["v"] - hv, f["v"] + hv))
            else:
                along, alen = (f["v"] - hv, f["v"] + hv), H
                z_lo, z_hi = ((f["u"] - hu, f["u"] + hu) if face == "left" else (D - f["u"] - hu, D - f["u"] + hu))
            if along[0] < R - 1e-6 or along[1] > alen - R + 1e-6:
                bad.append(f"{f['id']}: on the corner radius")
            if z_lo < zs + keep and z_hi > zs - keep:
                bad.append(f"{f['id']}: crosses the seam belt")
    out.append({"id": "R-PANEL-FLAT", "rule": f"side-face cut-outs on the flat face and clear of the seam belt (split plane +- {fmt_mm(keep)} mm)",
                "value_mm": bad or "none", "result": _res(not bad), "source": "geometry of this model (outer.corner_r, gasket)"})
    # Power key: the top wall is the PV6 panel.
    lo, hi = P.parts["pv6_button"]["panel_t"]
    out.append({"id": "R-PWR-KEY", "rule": "E-Switch PV6F240SS panel thickness at the power key (top wall) and at SW501 (hatch board 1.6 mm)",
                "value_mm": [m["wall"], P.boards["stackup"]["t"]], "limit_mm": [lo, hi],
                "result": _res(lo <= m["wall"] <= hi and lo <= P.boards["stackup"]["t"] <= hi), "source": "E-Switch PV6 datasheet (parts.json pv6_button)"})
    pk, pv = m["top_face"]["power_key"], P.parts["pv6_button"]
    out.append({"id": "R-PWR-KEY-NUT", "rule": "PV6 panel nut inside the top wall clear of the HDMI board, the display clamp bosses and the top Al angle",
                "value_mm": {"key_x": pk["x"], "key_z": pk["z"], "nut_d_assumed": pv["nut_d"]},
                "result": f"OPEN: the PV6 datasheet gives no nut size; a D{pv['nut_d']:g} nut (assumption) at x {pk['x']:g} / z {pk['z']:g} would reach the HDMI "
                          "board edge (x 146.2) and the top-right display clamp boss (z >= 56.5): measure the received nut; if it does not clear, re-place "
                          "the key (wave 2 layout)", "source": "parts.json pv6_button; mechanical.json top_face.power_key"})
    out.append(plate_slot_rule(P))
    out.append(plate_slot_fill(P))
    out += module_rules(P)
    out += cooler_rules(P)
    # Battery-side vents: a thread that ends in the foam layer needs a hole in the foam.
    bad = []
    pack = [b for i, n, b, _ in item_boxes(P) if i == "battery_pack"][0]
    tray = [b for i, n, b, _ in item_boxes(P) if i == "battery_tray"][0]
    for v in m["vents"]:
        if v["face"] != "front" or not (tray[0] < v["x"] < tray[3] and tray[1] < v["y"] < tray[4]):
            continue
        end = D - v["pad_t"] - (lv["thread_len"] - v["pad_t"])
        if pack[5] < end + 1e-9 and v.get("foam_cutout_d", 0.0) < 12.0 + 0.5:
            bad.append(v["id"])
    out.append({"id": "R-VENT-FOAM", "rule": "battery vent: the thread ends in the 3 mm foam layer, so the foam has a hole >= thread d + 0.5 at the vent",
                "value_mm": {v["id"]: v.get("foam_cutout_d") for v in m["vents"] if "foam_cutout_d" in v}, "limit_mm": 12.5,
                "result": _res(not bad), "source": "mechanical.json vents, battery_pack (foam 3.0)"})
    hr = m["hdmi_route"]
    out.append({"id": "R-HDMI-ROUTE", "rule": "HDMI cable Q6A to HDMI board: keep-clear route in the envelope check (plug head, bends, plate notch, run)",
                "value_mm": {"cable_od": hr["cable_od"], "bend_r": hr["bend_r"]},
                "result": "OPEN: " + hr["_status"], "source": "mechanical.json hdmi_route, layout hdmi_*"})
    out += w2_mech1_rules(P)
    out += w2_mech2_rules(P)
    out += w2_mech3_rules(P)
    return out


def fmt_mm(v):
    return f"{v:g}"


def _inside(p, poly):
    x, y = p
    ins = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            ins = not ins
    return ins


def plate_slot_rule(P, web_min=1.5):
    """Harness slots of the plate: inside the outline, with a web of at least web_min to the outline and to every other opening."""
    pl = P.mech["plate"]
    outline = plate_outline(P)
    wins = plate_windows(P)
    notches = [("notch", [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]) for (x, y, w, h) in pl.get("notches", []) + pl.get("notches_right", [])]
    worst, bad = None, []
    for sl in pl.get("slots", []):
        x, y, w, h = sl["rect"]
        corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        if not all(_inside(c, outline) for c in corners):
            bad.append(f"{sl['id']}: outside the outline")
            continue
        d = min(_seg_dist(c, a, b) for c in corners for a, b in zip(outline, outline[1:] + outline[:1]))
        for name, poly in wins + notches:
            if name == sl["id"]:
                continue
            d = min([d] + [_seg_dist(c, a, b) for c in corners for a, b in zip(poly, poly[1:] + poly[:1])]
                     + [_seg_dist(c, a, b) for c in poly for a, b in zip(corners, corners[1:] + corners[:1])])
        if worst is None or d < worst[0]:
            worst = (d, sl["id"])
    ok = not bad and (worst is None or worst[0] >= web_min)
    return {"id": "R-PLATE-SLOTS", "rule": f"plate harness slots inside the outline with a web >= {web_min:g} mm to the outline and to every other opening (worst slot)",
            "value_mm": round(worst[0], 2) if worst else None, "limit_mm": web_min, "slot": worst[1] if worst else None,
            "slots": [sl["id"] for sl in pl.get("slots", [])], "result": "FAIL (model): " + "; ".join(bad) if bad else _res(ok),
            "source": "mechanical.json plate.slots (harness pass-throughs, build/16 §1)"}


def _slot_trim_legs(P, sl):
    """Leg footprints of the grommet strip on each 'grommet' edge of a slot: (edge, face, (x0, y0, z0, x1, y1, z1))."""
    tr = P.mech["plate"]["slot_trim"]
    g = P.parts[tr["grommet"]]
    reach, proud = g["A"] - g["B"], (g["C"] - P.mech["plate"]["t"]) / 2.0
    x, y, w, h = sl["rect"]
    sz = P.mech["stack_z"]
    pr, pf = sz["plate_rear"], sz["plate_front"]
    rects = {"bottom": (x, y - reach, x + w, y), "top": (x, y + h, x + w, y + h + reach),
             "left": (x - reach, y, x, y + h), "right": (x + w, y, x + w + reach, y + h)}
    out = []
    for edge, kind in sl.get("trim", {}).items():
        if kind != "grommet":
            continue
        a = rects[edge]
        out.append((edge, "rear", (a[0], a[1], pr - proud, a[2], a[3], pr)))
        out.append((edge, "front", (a[0], a[1], pf, a[2], a[3], pf + proud)))
    return out


def plate_slot_fill(P):
    """R-PLATE-SLOT-FILL (W2 MECH-6): the harness bundle of each plate slot fits the opening left by the edge trim.

    Bundle = sum of the wire cross-sections of the slot's build/16 segments (OD = nominal + tolerance of the chosen PTFE wire,
    parts.json hookup_wire_ptfe) / fill + the S01 ribbon stack (two 20-way halves of parts.json ribbon_3m_3365_40). Opening =
    (w - loss_left - loss_right) x (h - loss_bottom - loss_top), loss = grommet bottom B or the tape allowance per edge
    (plate.slot_trim). The ribbon width, the stack and the largest wire must also fit the inner width / height, and every
    grommet leg (A - B from the edge, (C - t) / 2 proud on both faces) must clear the envelopes, the structure and the
    fastener footprints of the plate holes. A slot segment that build/16 does not have, or a wire without a read OD, is FAIL."""
    import csv
    from pathlib import Path
    from .layout import item_boxes, structure_boxes, gap
    path = Path(__file__).resolve().parents[2] / "build" / "16-dzhgut.csv"
    pl = P.mech["plate"]
    slots = pl.get("slots", [])
    tr = pl["slot_trim"]
    g = P.parts[tr["grommet"]]
    wod = P.parts["hookup_wire_ptfe"]["od"]
    rib = P.parts["ribbon_3m_3365_40"]
    flat = P.mech["harness_routes"].get("flat", {})
    rule = {"id": "R-PLATE-SLOT-FILL",
            "rule": f"harness bundle through each plate slot (wire areas / {tr['fill']:g} + ribbon stack) inside the opening left by the edge trim "
                    f"(grommet {tr['grommet']} B {g['B']:g} per edge, tape {tr['tape_mm']:g}); ribbon, stack and largest wire fit the inner size; grommet legs clear",
            "source": "mechanical.json plate.slots / slot_trim; build/16-dzhgut.csv; parts.json heyco_ngsg_105 (Heyco catalogue 6-23 read 2026-11-07), "
                      "hookup_wire_ptfe and ribbon_3m_3365_40 (SRC-1 rows read 2026-11-07)"}
    if not path.exists():
        return dict(rule, value_mm=None, result="OPEN: build/16-dzhgut.csv not found, bundle not counted")
    wires = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            wires.setdefault(r["segment"], []).append(r["awg"])
    obstacles = [(name, bx) for iid, name, bx, it in item_boxes(P) if not it.get("outside")]
    obstacles += [(name, bx) for name, bx in structure_boxes(P) if not name.startswith("plate.main") and not name.startswith("plate.ext")]
    holes = plate_holes(P)
    value, missing, bad = {}, [], []
    for sl in slots:
        x, y, w, h = sl["rect"]
        loss = {e: (g["B"] if sl.get("trim", {}).get(e) == "grommet" else tr["tape_mm"]) for e in ("bottom", "top", "left", "right")}
        iw, ih = w - loss["left"] - loss["right"], h - loss["bottom"] - loss["top"]
        counts, area, dmax, loose = {}, 0.0, 0.0, 0
        ribbon = None
        for seg in sl.get("segments", []):
            if seg not in wires:
                missing.append(f"{sl['id']}: {seg}")
                continue
            if seg in flat:                                    # the S01 IDC ribbon: two stacked 20-way halves
                ribbon = {"segment": seg, "w_mm": round(rib["w"] / 2.0, 2), "stack_mm": round(2 * rib["t"], 2),
                          "conductors_in_build16": len(wires[seg])}
                for awg in wires[seg]:
                    counts[awg] = counts.get(awg, 0) + 1
                continue
            for awg in wires[seg]:
                counts[awg] = counts.get(awg, 0) + 1
                loose += 1
                od = wod.get(awg)
                if od is None:
                    missing.append(f"{sl['id']}: {seg} {awg} AWG has no read wire OD")
                    continue
                d = od[0] + od[1]
                dmax = max(dmax, d)
                area += math.pi * d * d / 4.0
        need = area / tr["fill"] + (ribbon["w_mm"] * ribbon["stack_mm"] if ribbon else 0.0)
        have = max(iw, 0.0) * max(ih, 0.0)
        fits = [("bundle", need <= have + 1e-9), ("largest wire", dmax <= min(iw, ih) + 1e-9)]
        if ribbon:
            fits += [("ribbon width", ribbon["w_mm"] <= iw + 1e-9), ("ribbon stack", ribbon["stack_mm"] <= ih + 1e-9)]
        legs = []
        for edge, face, bx in _slot_trim_legs(P, sl):
            for name, ob in obstacles:
                if gap(bx, ob) <= 0.0:
                    legs.append(f"{edge} leg ({face}) on {name}")
            for ho in holes:
                rr = ho["d"] if tr["fastener_footprint"] == "d" else float(tr["fastener_footprint"])
                cx, cy = ho["c"]
                dx = max(bx[0] - cx, 0.0, cx - bx[3])
                dy = max(bx[1] - cy, 0.0, cy - bx[4])
                if math.hypot(dx, dy) < rr - 1e-9 and f"{edge} leg on hole {ho['id']}" not in legs:
                    legs.append(f"{edge} leg on hole {ho['id']}")
        ok = all(f for _, f in fits) and not legs
        if not ok:
            bad.append(sl["id"])
        value[sl["id"]] = {"opening_mm": [w, h], "trim": sl.get("trim", {}), "inner_mm": [round(iw, 2), round(ih, 2)],
                           "inner_mm2": round(have, 1), "wires": sum(counts.values()), "loose_wires": loose,
                           "wires_per_awg": {k: counts[k] for k in sorted(counts, key=int)}, "wire_area_mm2": round(area, 1),
                           "ribbon": ribbon, "bundle_need_mm2": round(need, 1), "fill_of_inner": round(need / have, 2) if have else None,
                           "largest_wire_mm": round(dmax, 2), "legs_clear": legs or "yes",
                           "result": ("PASS (model)" if ok else "FAIL (model): " + ", ".join([n for n, f in fits if not f] + legs))}
    if missing:
        return dict(rule, value_mm=value, result="FAIL (model): " + ", ".join(missing))
    txt = "; ".join(f"{k} {v['bundle_need_mm2']:g} <= {v['inner_mm2']:g} mm2 ({v['fill_of_inner']:g} of the inner opening "
                    f"{v['inner_mm'][0]:g} x {v['inner_mm'][1]:g})" for k, v in value.items())
    if bad:
        return dict(rule, value_mm=value, limit_mm="bundle inside the trimmed opening", result="FAIL (model): " + ", ".join(
            f"{k}: {value[k]['result']}" for k in bad))
    return dict(rule, value_mm=value, limit_mm="bundle inside the trimmed opening",
                result=f"PASS (model): {txt}; grommet legs clear of the envelopes, the structure and the plate-hole footprints")


def module_rules(P):
    """Purchased modules on a custom board must stay inside the board envelope height there."""
    out = []
    worst = None
    for bid, b in P.boards["boards"].items():
        for mo in b.get("modules_on_board", []):
            part = P.parts[mo["part"]]
            mx, my = mo["at"]
            mw, mh, mt = part["size"]
            need = mt + part.get("mount_standoff", 0.0)
            have = max([b["max_height"]] + [zn["max_height"] for zn in b.get("height_zones", [])
                                            if zn["rect"][0] <= mx and mx + mw <= zn["rect"][0] + zn["rect"][2]
                                            and zn["rect"][1] <= my and my + mh <= zn["rect"][1] + zn["rect"][3]])
            inside = any(r[0] <= mx and mx + mw <= r[0] + r[2] and r[1] <= my and my + mh <= r[1] + r[3] for r in b["rects"])
            margin = have - need if inside else -1.0
            if worst is None or margin < worst[0]:
                worst = (margin, f"{bid}/{mo['id']}", need, have)
    if worst:
        out.append({"id": "R-PWR-MODULES", "rule": "modules on a board (height + mount standoff) inside the board envelope height there (worst module)",
                    "value_mm": round(worst[2], 2), "limit_mm": worst[3], "module": worst[1], "result": _res(worst[0] >= -1e-9),
                    "source": "boards.json modules_on_board / height_zones; parts.json pololu_d36v50"})
    return out


def cooler_rules(P):
    """Cooler A: block inside the keep-in and over SoC + LPDDR5, fan face high enough over the tall connectors."""
    from .layout import cu_block_geometry
    q = P.parts["q6a"]
    cz = P.parts["q6a_cooler_zone"]
    cb = P.mech["cu_block"]
    (u0, v0), (bw, bh), _, _ = cu_block_geometry(P)
    ki = cz["keep_in_uv"]
    soc, ram = q["soc"]["uv"], q["lpddr5"]["uv"]
    inside = ki[0] - 1e-9 <= u0 and u0 + bw <= ki[2] + 1e-9 and ki[1] - 1e-9 <= v0 and v0 + bh <= ki[3] + 1e-9
    cover = min(min(soc[0], ram[0]) - u0, min(soc[1], ram[1]) - v0, u0 + bw - max(soc[2], ram[2]), v0 + bh - max(soc[3], ram[3]))
    tall = max(c["top"] for k, c in q["connectors"].items() if k in ("header40", "hdr2x2"))
    fan = cb["fan_above_board"]
    return [{"id": "R-COOLER-A", "rule": "cooler A: Cu block inside the 32 x 31 keep-in and over SoC + LPDDR5 (cover margin >= 0.5); fan face >= the keep-in minimum and above the 40-pin and 2x2 headers",
             "value_mm": {"cover_margin": round(cover, 2), "fan_face_above_board": fan, "tallest_header": tall},
             "limit_mm": {"cover_margin": 0.5, "fan_face_above_board": cz["fan_min_above_board"]},
             "result": _res(inside and cover >= 0.5 and fan >= cz["fan_min_above_board"] and fan > tall),
             "source": "parts.json q6a_cooler_zone (components/mechanical_thermal.md), q6a connectors (STEP V1.21)"}]


def vent_clearance(P, v):
    """Free depth along the vent axis from the inner face of its seat to the nearest envelope (excluding the tray it passes)."""
    W, H, D = P.outer
    r = 6.0
    best = 99.0
    for iid, name, bx, it in item_boxes(P):
        if iid in ("battery_tray", "usb_plug_bay") or it.get("outside"):
            continue
        if v["face"] == "front":
            if bx[0] - r < v["x"] < bx[3] + r and bx[1] - r < v["y"] < bx[4] + r and bx[5] <= D - v["pad_t"] + 1e-6:
                best = min(best, D - v["pad_t"] - bx[5])
        elif v["face"] == "right":
            if bx[1] - r < v["y"] < bx[4] + r and bx[2] - r < v["z"] < bx[5] + r and bx[3] <= W - v["pad_t"] + 1e-6:
                best = min(best, W - v["pad_t"] - bx[3])
        elif v["face"] == "left":
            if bx[1] - r < v["y"] < bx[4] + r and bx[2] - r < v["z"] < bx[5] + r and bx[0] >= v["pad_t"] - 1e-6:
                best = min(best, bx[0] - v["pad_t"])
    return best


def outer_depth(P, c):
    """Distance from a point inside the outline to the outer rounded rectangle of the shells (front view)."""
    W, H, _ = P.outer
    R = P.mech["outer"]["corner_r"]
    x, y = c
    cx, cy = min(max(x, R), W - R), min(max(y, R), H - R)
    if (cx, cy) != (x, y) and not (R <= x <= W - R or R <= y <= H - R):
        return R - math.hypot(x - cx, y - cy)
    return min(x, W - x, y, H - y)


def closure_spans(P):
    """Seam length between neighbouring closure screws, walked round the outline (front view)."""
    W, H, _ = P.outer
    per = 2 * (W + H)

    def pos(c):
        x, y = c
        d = {"bottom": y, "right": W - x, "top": H - y, "left": x}
        side = min(d, key=d.get)
        return {"bottom": x, "right": W + y, "top": W + H + (W - x), "left": 2 * W + H + (H - y)}[side]
    s = sorted(pos(tuple(b)) for b in P.mech["closure"]["bosses"])
    gaps = [((b - a) % per, a, b) for a, b in zip(s, s[1:] + s[:1])]
    worst = max(gaps)
    return {"screws": len(s), "max_span_mm": round(worst[0], 1), "mean_span_mm": round(per / len(s), 1),
            "note": "seam length (outline approximated by its bounding rectangle) between neighbouring screws; the longest span is the lower-left corner, where the battery pack and the HF+ can reach the walls (no boss fits); T-07 decides; every screw is reachable from outside (R-TOOL-ACCESS, screws 1-2 after the T7 holder is removed)"}


def bay_packing(P):
    """RF-bay packing (B-08, W2 MECH-3): both V4L dongles with the USB-A socket carriers of their leads and the two LNA cases.

    Three arrangements are reported with numbers; the chosen one (rf_bay.arrangement) must fit the inner bay and its layout
    items must sit inside the bay at the clearance. (a) two dongles + sockets in one row, the LNA cases in a second row;
    (b) LNA case + V4L + socket per row, two rows (the LNA cases stacked at one end set the bay height); (c) V4L + socket
    per row, two rows, with the LNA cases out of the bay. V4L and socket are mated (no gap); every other neighbour and wall
    is at rf_bay.clearance. MODEL FIT ONLY: the V4L reserve is the listing maximum (parts.json v4l)."""
    from .layout import item_boxes
    rb = P.mech["rf_bay"]
    x, y, w, h = rb["rect"]
    wt = rb["wall_t"]
    c = rb.get("clearance", 0.5)
    inner_w = w - (2 if "right" in rb["walls"] else 1) * wt
    inner_h = h - wt
    v4l = P.parts["v4l"]["size"]
    lna = P.parts["sawbird_noaa"]["size"]
    sock = rb["usb_socket_reserve"]
    dongle = v4l[0] + sock[0]                      # V4L plugged into its socket carrier
    dh = max(v4l[1], sock[1])
    arr = {
        "a": {"title": "two dongles with their sockets in one row, the LNA cases in a second row",
              "row_mm": round(2 * dongle + 3 * c, 1), "height_mm": round(dh + lna[1] + 3 * c, 1)},
        "b": {"title": "LNA case + V4L + socket per row, two rows (LNA cases stacked at one end)",
              "row_mm": round(lna[0] + dongle + 3 * c, 1), "height_mm": round(2 * lna[1] + 3 * c, 1),
              "dongle_column_mm": round(2 * dh + 3 * c, 1)},
        "c": {"title": "V4L + socket per row, two rows, LNA cases moved out of the bay",
              "row_mm": round(dongle + 2 * c, 1), "height_mm": round(2 * dh + 3 * c, 1),
              "note": "fits without growth, but the two cased LNA modules then need a shielded place outside the RF bay with new wall ports and seals: none in the model, so not chosen"},
    }
    for k, a in arr.items():
        a["fits"] = a["row_mm"] <= inner_w + 1e-9 and a["height_mm"] <= inner_h + 1e-9
        a["spare_row_mm"] = round(inner_w - a["row_mm"], 1)
        a["spare_height_mm"] = round(inner_h - a["height_mm"], 1)
    chosen = rb.get("arrangement")
    ids = ("v4l_a", "v4l_b", "sawbird", "flamingo", "usb_socket_a", "usb_socket_b")
    boxes = {i: b for i, n, b, _ in item_boxes(P) if i in ids}
    ix0, iy0, ix1, iy1 = x + wt, y + wt, x + w - (wt if "right" in rb["walls"] else 0.0), y + h
    W, H, _ = P.outer
    iy1 = min(iy1, H - P.mech["wall"])
    outside = sorted(i for i, b in boxes.items()
                     if b[0] < ix0 + c - 1e-9 or b[3] > ix1 - c + 1e-9 or b[1] < iy0 + c - 1e-9 or b[4] > iy1 - c + 1e-9)
    missing = sorted(set(ids) - set(boxes))
    res = {"inner_mm": [round(inner_w, 1), round(inner_h, 1)], "clearance_mm": c, "v4l_reserve": v4l, "v4l_status": P.parts["v4l"]["status"],
           "socket_reserve": sock, "socket_part": "wurth_614004190021", "lna_case": lna[:2], "arrangements": arr, "chosen": chosen,
           "layout_outside_bay": outside, "layout_missing": missing,
           "not_included": "coax mating plugs at the module SMA ends (cable assemblies TBD, SRC-2): (b) leaves the row spare between the LNA case and the V4L SMA end for a right-angle plug; the lead paths beyond notches N2/N3 to the hub (Adafruit 5997, envelope MECH-5)"}
    ok = chosen in arr and arr[chosen]["fits"] and not outside and not missing
    if ok:
        res["result"] = (f"PASS (model): arrangement ({chosen}) {arr[chosen]['row_mm']:g} x {arr[chosen]['height_mm']:g} mm in "
                         f"{inner_w:g} x {inner_h:g}; socket Wurth 614004190021 from its drawing; V4L reserve is the seller-listing maximum (measure at receipt)")
    elif chosen in arr and not arr[chosen]["fits"]:
        res["result"] = f"FAIL (model): arrangement ({chosen}) needs {arr[chosen]['row_mm']:g} x {arr[chosen]['height_mm']:g} mm, inner bay {inner_w:g} x {inner_h:g}"
    else:
        res["result"] = f"FAIL (model): layout items outside the bay or missing: {', '.join(outside + missing) or 'no arrangement chosen'}"
    return res


def w2_mech1_rules(P):
    """Harness routes (R-PPS-LEN, R-ROUTE-CLEAR; srrx_mech/routes.py) and board header heights (R-HDR-HEIGHT; boards.py)."""
    from . import boards, routes
    return routes.route_rules(P) + [boards.header_height_rule(P)]


# ---- W2 MECH-2: panel bulkheads and the bottom port row from the makers' drawings ----------------------------
def _port_stack(P, p):
    """Thread left for mating at a panel port (worst case) with its basis and pitch; left is None when a stack item is not drawn.

    Front-side-nut SMA: thread_len(min) - wall - washer(max) - nut(max); a seal drawn at the flange (waterproof fallback family)
    sits inside, so it adds nothing to the outer stack. VFA340 (flange outside, nut inside): the long side left inside for the
    W402 F plug. An item that is not drawn leaves the row OPEN, unless the drawn items alone already leave less than 3 threads
    (then the row FAILs on what is drawn)."""
    from .layout import port_wall
    part = P.parts.get(p.get("part", ""))
    wall = port_wall(P, p)
    if part is None or part.get("status") == "listing":
        return None, p.get("_tbd_reason", "part not read"), None
    pitch = part["pitch"]
    if p["kind"] == "f_bulkhead":
        long_min = part["overall"] - part["overall_tol"] - (part["short_side"] + part["short_side_tol"]) - (part["flange_t"] + part["tol"])
        left = long_min - wall - part["washer"][2] - part["nut_t"] - part["nut_t_tol"]
        return round(left, 2), "inside, for the W402 F plug: long side (min) - wall - washer - nut (max); the 7.6 short side outside is free for W401", pitch
    t_min = part["thread_len"] - part.get("thread_len_tol", 0.0)
    if "item5_t" in part:
        hw = part["item5_t"] + part["item5_t_tol"] + part["item6_t"] + part["item6_t_tol"]
        return round(t_min - wall - hw, 2), "outside: thread (min) - wall - items 5 + 6 (max); the seal sits at the flange inside", pitch
    if "nut_t" in part:
        nut = part["nut_t"] + part.get("nut_t_tol", 0.0)
        allow = t_min - wall - nut - 3 * pitch
        if allow < 0:
            return round(t_min - wall - nut, 2), "outside: thread (min) - wall - nut (max), before the undrawn washer", pitch
        return None, f"washer thickness not drawn: {allow:.2f} mm left for it after the nut and 3 threads", pitch
    allow = t_min - wall - 3 * pitch
    if allow < 0:
        return round(t_min - wall, 2), "outside: thread (min) - wall, before the undrawn nut and washer", pitch
    return None, (f"nut and washer not drawn: {allow:.2f} mm left for both after 3 threads "
                  "(1/4-36 sets read: Taoglas p.11 items 5 + 6 up to 3.35, Samtec 2.5)"), pitch


def sma_thread_rule(P):
    """R-SMA-THREAD per panel port: >= 3 full threads left for mating after wall, washer and nut (STACK 5.8)."""
    m = P.mech
    rows, opened = {}, []
    for p in m["top_face"]["ports"] + m["right_face"]["ports"]:
        left, how, pitch = _port_stack(P, p)
        if left is None:
            rows[p["id"]] = f"OPEN: {how}"
            opened.append(p["id"])
        else:
            need = 3 * pitch
            rows[p["id"]] = f"{'PASS' if left >= need - 1e-9 else 'FAIL'} (model): {left:g} mm left >= {need:.2f} (3 x {pitch:g}); {how}"
    fails = [k for k, v in rows.items() if v.startswith("FAIL")]
    passed = [k for k, v in rows.items() if v.startswith("PASS")]
    if fails:
        res = "FAIL (model): " + ", ".join(fails)
    elif opened:
        res = f"OPEN: {', '.join(opened)} (thread or hardware not drawn, or part not read); PASS (model): {', '.join(passed)}"
    else:
        res = "PASS (model)"
    wall = m["wall"] + m["angles"]["top"]["t"]
    return {"id": "R-SMA-THREAD", "rule": "per panel port: thread left for mating after the 4.5 mm wall (ASA 2.5 + Al angle 2.0), washer and nut >= 3 full threads (1/4-36: 3 x 0.706; 3/8-32: 3 x 0.794)",
            "value_mm": rows, "limit_mm": f"3 x pitch; wall {wall:g}", "result": res,
            "source": "STACK 5.8 'стінка 4-5 мм'; parts.json taoglas_cab718, adamtech_ca_dkca1_305l5, taoglas_cab01075, cinch_vfa340 (read 2026-11-07)"}


def bulkhead_nuts_rule(P):
    """R-BULKHEAD-NUTS: every panel port has an inner envelope from its drawing (nut.* in the envelope check), or is OPEN."""
    from .layout import port_inner
    m = P.mech
    val, opened, assumed = {}, [], []
    for p in m["top_face"]["ports"] + m["right_face"]["ports"] + m["right_face"].get("panel", []) + [q for q in m["bottom_face"]["ports"] if q["kind"] != "tbd"]:
        e = port_inner(P, p)
        if e is None:
            opened.append(p["id"])
            val[p["id"]] = "no envelope: " + p.get("_tbd_reason", "part not read")
            continue
        r, th, basis = e
        part = P.parts.get(p.get("part", ""), {})
        if "representative" in basis or "body_od_reserve" in part or ("body_len_reserve" in part and "body_hex_len" not in part):
            assumed.append(p["id"])
        val[p["id"]] = f"d {2 * r:.2f} x {th:.2f} deep: {basis}"
    res = f"OPEN: no inner envelope for {', '.join(opened)} (drawing not read)" if opened else "PASS (model)"
    if assumed:
        res += f"; body OD or length not dimensioned, envelope reserve for {', '.join(assumed)}"
    return {"id": "R-BULKHEAD-NUTS", "rule": "nut, washer or connector body of every panel bulkhead inside the wall: an envelope from the part's drawing in the envelope check (nut.*: clear of the RF-bay walls, modules and structure)",
            "value_mm": val, "result": res, "source": "parts.json (makers' drawings read 2026-11-07); envelopes in fit-report 'tight' / 'collisions'"}


def _port_radius(P, p):
    """Largest radius of a bottom port about its axis: outer flange or hole (HOLES) and inner nut (part drawing); None if not modelled."""
    from .features import HOLES
    from .layout import port_inner
    if p["kind"] == "tbd":
        return None
    e = port_inner(P, p)
    h = HOLES[p["kind"]]
    return max(h.get("flange_d", h["d"]) / 2.0, e[0] if e else 0.0)


def bottom_pitch_rule(P, clear=1.0):
    """R-BOTTOM-PITCH: every pair of bottom-face ports, radius of each + clear <= centre distance (in the face)."""
    m = P.mech
    ports = m["bottom_face"]["ports"]
    val, bad, opened = {}, [], []
    for a, b in itertools.combinations(ports, 2):
        dist = math.hypot(a["x"] - b["x"], a["z"] - b["z"])
        ra, rb = _port_radius(P, a), _port_radius(P, b)
        key = f"{a['id']}-{b['id']}"
        if ra is None or rb is None:
            opened.append(key)
            val[key] = f"{dist:.1f} mm apart; OPEN: {', '.join(q['id'] for q, r in ((a, ra), (b, rb)) if r is None)} not modelled"
            continue
        need = ra + rb + clear
        val[key] = f"{dist:.1f} >= {need:.2f}: {'PASS' if dist >= need - 1e-9 else 'FAIL'} (model)"
        if dist < need - 1e-9:
            bad.append(key)
    px = P.parts.get("bulgin_px0845a")
    note = (f"; read but not placed: PX0845/A (hex {px['hex']:g}) needs {px['hex'] / 2 + clear:g} mm + the neighbour radius to each neighbour, "
            "more than the 17 mm row pitch" if px else "")
    if bad:
        res = "FAIL (model): " + ", ".join(bad)
    elif opened:
        res = "OPEN: " + ", ".join(q["id"] for q in ports if q["kind"] == "tbd") + " not modelled (mechanical.json bottom_face '_tbd_reason')" + note
    else:
        res = "PASS (model)"
    return {"id": "R-BOTTOM-PITCH", "rule": f"bottom-face port row: outer flange or inner nut radius of each port + {clear:g} mm <= centre distance (re-space inside x 163-213 if it fails)",
            "value_mm": val, "limit_mm": clear, "result": res, "source": "mechanical.json bottom_face.ports; parts.json (makers' drawings read 2026-11-07)"}


def pod_wall_rule(P):
    """R-POD-WALL: S-band pod wall parts against the wall they pass (worst-case wall per port, antennas.pod_wall_t)."""
    from .antennas import pod_wall_t
    val, bad = {}, []
    for p in P.antennas["sband_pod"]["ports"]:
        t, basis = pod_wall_t(P, p["wall"])
        part = P.parts.get(p.get("part", ""), {})
        if "panel_max" in part:
            ok, txt = t <= part["panel_max"], f"wall {t:.2f} <= panel max {part['panel_max']:g}"
        elif "locknut_t" in part:
            left = part["thread_len"] - t - part["locknut_t"]
            ok, txt = left >= 0, f"thread {part['thread_len']:g} - wall {t:.2f} - locknut {part['locknut_t']:g} = {left:.2f} >= 0 (locknut fully on the thread)"
        elif "panel_t" in part:
            ok, txt = part["panel_t"][0] <= t <= part["panel_t"][1], f"wall {t:.2f} in the through-hole range {part['panel_t'][0]:g}-{part['panel_t'][1]:g}"
        else:
            val[p["id"]] = f"OPEN: no panel data for {p.get('part', p['kind'])}"
            continue
        val[p["id"]] = f"{'PASS' if ok else 'FAIL'} (model): {txt}; {basis}"
        if not ok:
            bad.append(p["id"])
    opened = [k for k, v in val.items() if v.startswith("OPEN")]
    res = ("FAIL (model): " + ", ".join(bad)) if bad else (("OPEN: " + ", ".join(opened)) if opened else
                                                           "PASS (model); the end walls are not dimensioned (upper bound used)")
    return {"id": "R-POD-WALL", "rule": "S-band pod: bulkhead panel range, gland thread through wall + locknut, vent through-hole range against the pod wall (worst case)",
            "value_mm": val, "result": res,
            "source": "antennas.json sband_pod.ports; parts.json hammond_1554u2gy, fairview_sm4955, lapp_skintop_st_m12, ltw_vent (read 2026-11-07)"}


def w2_mech2_rules(P):
    """Rows added by W2 MECH-2 (registration list, append-only)."""
    return [bottom_pitch_rule(P), pod_wall_rule(P)]


# ---- W2 MECH-3: PWR-A relief pockets, the J551 pod power entry --------------------------------------------
def pwr_pockets(P):
    """Plate relief pockets under the PWR-A THT pin fields that have a placement contract (boards.json modules_on_board
    pin_field): (id, module, (x0, y0, x1, y1) enclosure, depth)."""
    b = P.boards["boards"]["PWR"]
    tp = b.get("tht_pockets", {})
    mg, depth = tp.get("margin", 1.0), tp.get("depth", 1.0)
    ox, oy = b["place"]["origin"]
    out = []
    for i, mo in enumerate(m for m in b.get("modules_on_board", []) if "pin_field" in m):
        x, y, w, h = mo["pin_field"]
        out.append((f"PK{i + 1}", mo["id"], (ox + x - mg, oy + y - mg, ox + x + w + mg, oy + y + h + mg), depth))
    return out


def pwr_pocket_rule(P):
    """R-PWR-POCKETS: every PWR-A THT pin field with a placement contract has a plate relief pocket (M-07) of at least
    depth_min, inside the plate and clear of the plate holes; the other PWR-A THT groups wait for the PCB-PWRA placement."""
    b = P.boards["boards"]["PWR"]
    tp = b.get("tht_pockets", {})
    pl = P.mech["plate"]
    poly = plate_outline(P)
    holes = plate_holes(P)
    val, bad = {}, []
    for pid, mod, (x0, y0, x1, y1), depth in pwr_pockets(P):
        inside = all(_inside(c, poly) for c in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)))
        gap = min(_rect_gap((x0, y0, x1, y1), (h["c"][0] - h["d"] / 2, h["c"][1] - h["d"] / 2, h["c"][0] + h["d"] / 2, h["c"][1] + h["d"] / 2))
                  for h in holes)
        ok = inside and tp.get("depth_min", 1.0) <= depth < pl["t"] and gap >= 0.5
        val[pid] = (f"{mod}: {x1 - x0:.2f} x {y1 - y0:.2f} x {depth:g} deep at x {x0:.2f}..{x1:.2f}, y {y0:.2f}..{y1:.2f}; "
                    f"{gap:.1f} mm to the nearest plate hole")
        if not ok:
            bad.append(pid)
    if bad:
        res = "FAIL (model): " + ", ".join(bad)
    else:
        res = ("OPEN: the Pololu pin rows are pocketed (M-07 " + ", ".join(val) + "); "
               + tp.get("from_placement", "the other THT groups wait for the placement"))
    return {"id": "R-PWR-POCKETS",
            "rule": f"plate relief pocket >= {tp.get('depth_min', 1.0):g} mm under every PWR-A THT pad group (pin field + {tp.get('margin', 1.0):g} mm), polyimide over it",
            "value_mm": val, "limit_mm": {"depth_min": tp.get("depth_min", 1.0), "plate_t": pl["t"]}, "result": res,
            "source": "boards.json PWR tht_pockets / modules_on_board pin_field; pcb/partition-spec.json keepouts.pwr_a_tht_pockets"}


def j551_rule(P):
    """R-J551: the pod power receptacle J551 (binder M8) on a flat face, in a wall inside the binder range, inner envelope in
    the collision set; mounting side from the data-sheet drawing (inserted from inside, nut outside)."""
    from .layout import port_wall
    m = P.mech
    ports = [p for p in m["right_face"].get("panel", []) if p["id"] == "J551"]
    rule = {"id": "R-J551",
            "rule": "pod power receptacle J551 (binder M8): wall inside the data-sheet range, cut-out from the data sheet, inner envelope nut.J551 in the envelope check",
            "source": "parts.json binder_76_6618_1111 (READS-E row web:binder-76-6618-1111-00003-0200); mechanical.json right_face.panel"}
    if not ports:
        return dict(rule, value_mm=None, result="OPEN: J551 not placed on a face")
    p = ports[0]
    part = P.parts[p["part"]]
    wall = port_wall(P, p)
    ok = part["wall_min"] <= wall <= part["wall_max"]
    proud = part["front_to_collar"] - wall
    val = {"face": "right", "y": p["y"], "z": p["z"], "wall": wall, "range": [part["wall_min"], part["wall_max"]], "hole_d": part["hole_d"],
           "proud_outside": round(proud, 2), "inner": [part["inner_d"], part["inner_depth"]], "leads_mm": part["leads_mm"]}
    if ok:
        res = (f"PASS (model): {wall:g} mm ASA wall inside {part['wall_min']:g}-{part['wall_max']:g}; inserted from inside (collar on the inner face), "
               f"SW 11 nut outside, {proud:g} mm proud of the right face; plain bore {part['hole_d']:g} (binder proposal 2)")
    else:
        res = f"FAIL (model): wall {wall:g} outside {part['wall_min']:g}-{part['wall_max']:g}"
    return dict(rule, value_mm=val, limit_mm={"wall": [part["wall_min"], part["wall_max"]]}, result=res)


def w2_mech3_rules(P):
    """Rows added by W2 MECH-3 (registration list, append-only)."""
    from . import fasteners
    return [pwr_pocket_rule(P), j551_rule(P), fasteners.rule(P)]
