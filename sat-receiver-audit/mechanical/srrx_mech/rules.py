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
    # W2 MECH-5 (B-13): PEM standoffs of boards mounted on the plate without a boards.json place (module_mounts, on plate_front)
    k = 0
    for mt in m.get("module_mounts", {}).get("mounts", []):
        if mt["on"] != "plate_front":
            continue
        f = P.parts[mt["fastener"]]
        for (hx, hy) in mt["standoffs"]:
            k += 1
            out.append({"id": f"PF{k}", "c": (hx, hy), "d": f["hole_d"], "edge_min": f["edge_min"],
                        "use": f"PEM {f['mpn']}, head flush with the rear face ({mt['item']})"})
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
    out.append(pwr_key_nut_rule(P))
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
    out.append(hdmi_route_rule(P))
    out += w2_mech1_rules(P)
    out += w2_mech2_rules(P)
    out += w2_mech3_rules(P)
    out += w2_mech4_rules(P)
    out += w2_mech5_rules(P)
    out += w2_mech7_rules(P)
    out += w2_mech8_rules(P)
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
    reach, proud = trim_legs(P, g)
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


def trim_legs(P, g):
    """(leg reach from the slot edge, leg height proud of a plate face) of a U edging profile (parts.json semantic keys):
    reach = overall height - base (the inside depth of the U: the plate edge bottoms on the base, the legs run that far onto
    each face; for the Essentra MGS-2-01 the drawing's D, W2 MECH-6 review); proud = (outer - inner width) / 2 + (inner width
    - plate) with an inner width (worst case, panel against one leg), else (outer width - plate) / 2 (the profile's base width
    as an upper bound)."""
    t = P.mech["plate"]["t"]
    reach = g["overall_h"] - g["base_t"]
    proud = (g["outer_w"] - g["inner_w"]) / 2.0 + (g["inner_w"] - t) if "inner_w" in g else (g["outer_w"] - t) / 2.0
    return reach, proud


def _shelf_pack(diams, w, h):
    """Wire diameters left over after packing round wires into a w x h rectangle (next-fit decreasing shelves, no nesting of
    one row into the next, so a lower bound of what fits); both orientations are tried, the one leaving fewer wins."""
    best = None
    for a, b in ((w, h), (h, w)):
        left, used, row_w, row_h = [], 0.0, 0.0, 0.0
        for d in sorted(diams, reverse=True):
            if row_h > 0.0 and row_w + d <= a + 1e-9:
                row_w += d
            elif d <= a + 1e-9 and used + row_h + d <= b + 1e-9:
                used, row_w, row_h = used + row_h, d, d
            else:
                left.append(d)
        if best is None or len(left) < len(best):
            best = left
    return best


def plate_slot_fill(P):
    """R-PLATE-SLOT-FILL (W2 MECH-6): the harness bundle of each plate slot fits the opening left by the edge trim.

    Bundle = sum of the wire cross-sections of the slot's build/16 segments (OD = nominal + tolerance of the chosen PTFE wire,
    parts.json hookup_wire_ptfe) / fill + the S01 ribbon stack (two 20-way halves of parts.json ribbon_3m_3365_40). Opening =
    (w - loss_left - loss_right) x (h - loss_bottom - loss_top), loss = grommet bottom B or the tape allowance per edge
    (plate.slot_trim). The ribbon width, the stack and the largest wire must also fit the inner width / height; the loose
    wires must also pack as round wires (_shelf_pack) into what the rigid ribbon leaves: beside it ((inner w - ribbon w) x
    inner h) and on it (ribbon w x (inner h - stack)), or into the whole inner opening when the slot has no ribbon. Every
    grommet leg (trim_legs: overall height - base from the edge, the Essentra inside depth D; leg thickness plus the panel
    play proud on both faces) must clear the envelopes, the structure and the fastener footprints of the plate holes. A slot
    segment that build/16 does not have, or a wire without a read OD, is FAIL."""
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
                    f"(edging {tr['grommet']} base {g['base_t']:g} per edge, tape {tr['tape_mm']:g}); ribbon, stack and largest wire fit the inner size; "
                    f"loose wires pack as round wires beside / on the ribbon; edging legs ({trim_legs(P, g)[0]:.2f} onto each face) clear",
            "source": "mechanical.json plate.slots / slot_trim; build/16-dzhgut.csv; parts.json essentra_mgs_2_01 (Essentra catalogue p.276 read 2026-11-07), "
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
        loss = {e: (g["base_t"] if sl.get("trim", {}).get(e) == "grommet" else tr["tape_mm"]) for e in ("bottom", "top", "left", "right")}
        iw, ih = w - loss["left"] - loss["right"], h - loss["bottom"] - loss["top"]
        counts, area, dmax, loose = {}, 0.0, 0.0, 0
        ribbon, ds = None, []
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
                ds.append(d)
        need = area / tr["fill"] + (ribbon["w_mm"] * ribbon["stack_mm"] if ribbon else 0.0)
        have = max(iw, 0.0) * max(ih, 0.0)
        fits = [("bundle", need <= have + 1e-9), ("largest wire", dmax <= min(iw, ih) + 1e-9)]
        if ribbon:
            fits += [("ribbon width", ribbon["w_mm"] <= iw + 1e-9), ("ribbon stack", ribbon["stack_mm"] <= ih + 1e-9)]
            regions = [(iw - ribbon["w_mm"], ih), (ribbon["w_mm"], ih - ribbon["stack_mm"])]
        else:
            regions = [(iw, ih)]
        left = ds
        for rw_, rh_ in regions:
            left = _shelf_pack(left, max(rw_, 0.0), max(rh_, 0.0)) if left else left
        packing = {"regions_mm": [[round(max(a, 0.0), 2), round(max(b, 0.0), 2)] for a, b in regions],
                   "method": "round wires, next-fit decreasing shelves, no nesting (beside the ribbon, then on it)" if ribbon
                   else "round wires, next-fit decreasing shelves, no nesting", "unplaced": len(left)}
        fits.append(("wire packing", not left))
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
                           "largest_wire_mm": round(dmax, 2), "packing": packing, "legs_clear": legs or "yes",
                           "result": ("PASS (model)" if ok else "FAIL (model): " + ", ".join([n for n, f in fits if not f] + legs))}
    if missing:
        return dict(rule, value_mm=value, result="FAIL (model): " + ", ".join(missing))
    txt = "; ".join(f"{k} {v['bundle_need_mm2']:g} <= {v['inner_mm2']:g} mm2 ({v['fill_of_inner']:g} of the inner opening "
                    f"{v['inner_mm'][0]:g} x {v['inner_mm'][1]:g})" for k, v in value.items())
    if bad:
        return dict(rule, value_mm=value, limit_mm="bundle inside the trimmed opening", result="FAIL (model): " + ", ".join(
            f"{k}: {value[k]['result']}" for k in bad))
    return dict(rule, value_mm=value, limit_mm="bundle inside the trimmed opening",
                result=f"PASS (model): {txt}; loose wires pack beside / on the ribbon; edging legs clear of the envelopes, the structure and the plate-hole footprints")


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
    # W2 MECH-7 (SHRINK-2): no module on a board; the PWR-A converters are reserved blocks of the partition budget until GR-5A
    # gives them graph refs: each block height inside the PWR-A envelope (hA, under the PWR-B mezzanine)
    from .boards import budget_candidate, retired_blocks
    ch, cand = budget_candidate()
    retired = retired_blocks()      # W2 MECH-7 part 2: blocks whose change GR-5A has put into the graph leave the rule
    blocks = [bl for bl in ((cand or {}).get("planned") or {}).get("blocks", []) if bl.get("side") == "PWR_A" and bl["id"] not in retired]
    b = P.boards["boards"]["PWR"]
    if blocks:
        top = max(blocks, key=lambda bl: bl["h"])
        out.append({"id": "R-PWR-MODULES", "rule": "no purchased module on a custom board (W2 MECH-7: SHRINK-2 replaced the Pololu U107/U108); the reserved PWR-A "
                                                   "blocks of the partition budget (converters, RPP, SMD fuses) inside the PWR-A envelope height (tallest block)",
                    "value_mm": top["h"], "limit_mm": b["max_height"], "module": top["id"],
                    "blocks_mm": {bl["id"]: [bl["w"], bl["d"], bl["h"]] for bl in blocks},
                    "result": _res(all(bl["h"] <= b["max_height"] + 1e-9 for bl in blocks)),
                    "source": f"pcb/partition-budget.json candidates.{ch}.planned.blocks (heights: READS-P rows, MODEL blocks until GR-5A); boards.json PWR max_height"})
    else:
        gone = sorted(retired)
        out.append({"id": "R-PWR-MODULES", "rule": "no purchased module on a custom board (W2 MECH-7: SHRINK-2 replaced the Pololu U107/U108)",
                    "value_mm": None, "limit_mm": b["max_height"], "retired_blocks": gone,
                    "result": "PASS (model): no module on a board; the converters are board parts (partition height rule)"
                              + (f"; the reserved blocks {', '.join(gone)} are in the graph as real parts (GR-5A), so their heights are the "
                                 "partition height rule's (pcb/partition-spec.json heights.by_mpn)" if gone else ""),
                    "source": "boards.json modules_on_board; pcb/partition-budget.json; pcb/partition-spec.json candidates.<chosen>.planned (graph status)"})
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
def _merge_cells(cells):
    """Rectangles (x0, x1, y0, y1) from grid cells: merge along x in each row, then rows with the same x extent along y."""
    rows = {}
    for x0, x1, y0, y1 in sorted(cells, key=lambda c: (c[2], c[0])):
        row = rows.setdefault((y0, y1), [])
        if row and abs(row[-1][1] - x0) < 1e-9:
            row[-1][1] = x1
        else:
            row.append([x0, x1, y0, y1])
    rects, open_ = [], {}
    for key in sorted(rows):
        nxt = {}
        for x0, x1, y0, y1 in rows[key]:
            k = (round(x0, 6), round(x1, 6))
            if k in open_ and abs(open_[k][3] - y0) < 1e-9:
                r = open_.pop(k)
                r[3] = y1
                nxt[k] = r
            else:
                nxt[k] = [x0, x1, y0, y1]
        rects += list(open_.values())
        open_ = nxt
    return rects + list(open_.values())


def pwr_bottom_regions(P):
    """W2 MECH-7: plate pockets PB* under the bottom side of the two-sided PWR-A (mechanical.json plate.pwr_bottom_pockets).

    PWR-A outline (boards.json PWR rects, board coordinates) minus every thermal_bond zone grown by bond_land, minus the
    keep_full rectangles (converter heat corridors), minus a square of half-side edge_min (else the hole diameter) around every
    plate hole, minus edge_web from the plate outline, the slots and the windows; regions narrower than min_w are dropped.
    Returns [(id, [x, y, w, h] board coordinates)], or [] when the plate has no pwr_bottom_pockets entry."""
    spec = P.mech["plate"].get("pwr_bottom_pockets")
    if not spec:
        return []
    b = P.boards["boards"]["PWR"]
    ox, oy = b["place"]["origin"]
    land, web, minw = spec["bond_land"], spec["edge_web"], spec["min_w"]
    excl = [(z[0] - land, z[1] - land, z[0] + z[2] + land, z[1] + z[3] + land) for z in b["thermal_bond"]]
    excl += [(k["rect"][0], k["rect"][1], k["rect"][0] + k["rect"][2], k["rect"][1] + k["rect"][3]) for k in spec.get("keep_full", [])]
    for h in plate_holes(P):
        r = h.get("edge_min") or h["d"]
        cx, cy = h["c"][0] - ox, h["c"][1] - oy
        excl.append((cx - r, cy - r, cx + r, cy + r))
    for _, poly in plate_windows(P):
        xs_, ys_ = [p[0] - ox for p in poly], [p[1] - oy for p in poly]
        excl.append((min(xs_) - web, min(ys_) - web, max(xs_) + web, max(ys_) + web))
    outline = plate_outline(P)
    xs0, ys0 = [p[0] for p in b["outline"]], [p[1] for p in b["outline"]]
    xmin, xmax, ymin, ymax = min(xs0), max(xs0), min(ys0), max(ys0)
    xs = sorted({xmin, xmax} | {r[0] for r in b["rects"]} | {r[0] + r[2] for r in b["rects"]}
                | {v for e in excl for v in (e[0], e[2]) if xmin < v < xmax}
                | {v + s * web for v in (p[0] - ox for p in outline) for s in (-1, 1) if xmin < v + s * web < xmax})
    ys = sorted({ymin, ymax} | {r[1] for r in b["rects"]} | {r[1] + r[3] for r in b["rects"]}
                | {v for e in excl for v in (e[1], e[3]) if ymin < v < ymax}
                | {v + s * web for v in (p[1] - oy for p in outline) for s in (-1, 1) if ymin < v + s * web < ymax})

    def keep(x, y):
        if not any(r[0] < x < r[0] + r[2] and r[1] < y < r[1] + r[3] for r in b["rects"]):
            return False
        if any(e[0] < x < e[2] and e[1] < y < e[3] for e in excl):
            return False
        X, Y = x + ox, y + oy
        if not _inside((X, Y), outline):
            return False
        return min(_seg_dist((X, Y), a, c) for a, c in zip(outline, outline[1:] + outline[:1])) >= web - 1e-9

    cells = []
    for y0, y1 in zip(ys, ys[1:]):
        for x0, x1 in zip(xs, xs[1:]):
            if keep((x0 + x1) / 2, (y0 + y1) / 2):
                cells.append((x0, x1, y0, y1))
    rects = [r for r in _merge_cells(cells) if min(r[1] - r[0], r[3] - r[2]) >= minw - 1e-9]
    rects.sort(key=lambda r: (r[2], r[0]))
    return [(f"PB{i + 1}", [round(r[0], 2), round(r[2], 2), round(r[1] - r[0], 2), round(r[3] - r[2], 2)]) for i, r in enumerate(rects)]


def pwr_pockets(P):
    """Plate relief pockets in the front face under PWR-A: (id, what, (x0, y0, x1, y1) enclosure, depth).

    The THT pin fields with a placement contract (boards.json modules_on_board pin_field, PK*; none since W2 MECH-7) and the
    bottom-part pockets PB* (pwr_bottom_regions, W2 MECH-7)."""
    b = P.boards["boards"]["PWR"]
    tp = b.get("tht_pockets", {})
    mg, depth = tp.get("margin", 1.0), tp.get("depth", 1.0)
    ox, oy = b["place"]["origin"]
    out = []
    for i, mo in enumerate(m for m in b.get("modules_on_board", []) if "pin_field" in m):
        x, y, w, h = mo["pin_field"]
        out.append((f"PK{i + 1}", mo["id"], (ox + x - mg, oy + y - mg, ox + x + w + mg, oy + y + h + mg), depth))
    for pid, (x, y, w, h) in pwr_bottom_regions(P):      # same depth as every M-07 relief pocket (tht_pockets.depth)
        out.append((pid, "PWR-A bottom side", (ox + x, oy + y, ox + x + w, oy + y + h), depth))
    return out


def pwr_pocket_rule(P):
    """R-PWR-POCKETS: every plate relief pocket under PWR-A (M-07: the bottom-part pockets PB*, W2 MECH-7, and any THT pin field
    with a placement contract) is at least depth_min deep with web_min of plate left, inside the plate and clear of the plate
    holes, and the PB pockets keep bond_land from every thermal_bond zone; the THT groups outside the PB pockets wait for the
    PCB-PWRA-3 placement (OPEN)."""
    b = P.boards["boards"]["PWR"]
    tp = b.get("tht_pockets", {})
    pl = P.mech["plate"]
    bp = pl.get("pwr_bottom_pockets", {})
    poly = plate_outline(P)
    holes = plate_holes(P)
    ox, oy = b["place"]["origin"]
    web_min = bp.get("web_min", 0.0)
    val, bad = {}, []
    for pid, mod, (x0, y0, x1, y1), depth in pwr_pockets(P):
        inside = all(_inside(c, poly) for c in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)))
        gap = min(_rect_gap((x0, y0, x1, y1), (h["c"][0] - h["d"] / 2, h["c"][1] - h["d"] / 2, h["c"][0] + h["d"] / 2, h["c"][1] + h["d"] / 2))
                  for h in holes)
        bond = min(_rect_gap((x0, y0, x1, y1), (ox + z[0], oy + z[1], ox + z[0] + z[2], oy + z[1] + z[3])) for z in b["thermal_bond"])
        ok = inside and tp.get("depth_min", 1.0) <= depth < pl["t"] and pl["t"] - depth >= web_min - 1e-9 and gap >= 0.5
        if pid.startswith("PB"):
            ok = ok and bond >= bp["bond_land"] - 1e-6
        val[pid] = (f"{mod}: {x1 - x0:.2f} x {y1 - y0:.2f} x {depth:g} deep at x {x0:.2f}..{x1:.2f}, y {y0:.2f}..{y1:.2f}; "
                    f"{gap:.1f} mm to the nearest plate hole, {bond:.1f} mm to the nearest bond zone")
        if not ok:
            bad.append(pid)
    from .boards import budget_candidate
    ch, cand = budget_candidate()
    items = (cand or {}).get("pwr_a_tht_pocket_items")
    if items is not None:
        drawn = [x["item"] for x in items if x["item"] in ("U107", "U108")]    # D36V50F12 U107 / D36V50F5 U108 (boards.json PWR notes)
        live = (f" (pcb/partition-budget.json candidates.{ch} pwr_a_tht_pocket_items now: {len(items)} items with "
                f"{sum(x['tht_pads'] for x in items)} THT pads" + (f", {'/'.join(drawn)} of them pocketed here" if drawn else "") + ")")
    else:
        live = " (pcb/partition-budget.json pwr_a_tht_pocket_items not found)"
    pb = [k for k in val if k.startswith("PB")]
    area = sum((x1 - x0) * (y1 - y0) for pid, _, (x0, y0, x1, y1), _ in pwr_pockets(P) if pid.startswith("PB"))
    if bad:
        res = "FAIL (model): " + ", ".join(bad)
    else:
        res = (f"OPEN: {len(pb)} bottom-part pockets PB1-PB{len(pb)} ({area:.0f} mm2, {tp.get('depth', 1.0):g} deep, web {pl['t'] - tp.get('depth', 1.0):g}, "
               f">= {bp.get('bond_land', 0):g} from every bond zone, outside the converter heat corridors and the plate-hole lands) are drawn (M-07); "
               if pb else "OPEN: ") + tp.get("from_placement", "the THT groups wait for the placement") + live
    return {"id": "R-PWR-POCKETS",
            "rule": f"plate relief pockets under PWR-A (M-07): bottom-part pockets PB* (W2 MECH-7) and a pocket >= {tp.get('depth_min', 1.0):g} mm under every PWR-A THT pad group "
                    f"(pin field + {tp.get('margin', 1.0):g} mm) outside them; polyimide film in every pocket",
            "value_mm": val, "limit_mm": {"depth_min": tp.get("depth_min", 1.0), "plate_t": pl["t"], "web_min": web_min, "bond_land": bp.get("bond_land")},
            "result": res,
            "source": "mechanical.json plate.pwr_bottom_pockets; boards.json PWR tht_pockets, thermal_bond; pcb/partition-spec.json keepouts.pwr_a_tht_pockets; "
                      "pcb/partition-budget.json pwr_a_tht_pocket_items"}


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
               f"SW 11 nut outside, {proud:g} mm proud of the right face; plain bore {part['hole_d']:g} (binder proposal 2: takes the M10x0.75 "
               f"body with or without flats); anti-rotation with the flats proposal ({part['hole_flats']:g} across) OPEN until flats on this "
               "part's body are confirmed (the READS-E reading of the scale drawing names none)")
    else:
        res = f"FAIL (model): wall {wall:g} outside {part['wall_min']:g}-{part['wall_max']:g}"
    return dict(rule, value_mm=val, limit_mm={"wall": [part["wall_min"], part["wall_max"]]}, result=res)


def w2_mech3_rules(P):
    """Rows added by W2 MECH-3 (registration list, append-only)."""
    from . import fasteners
    return [pwr_pocket_rule(P), j551_rule(P), fasteners.rule(P)]


def _boxes_by_name(P):
    from .layout import structure_boxes
    out = {name: bx for _, name, bx, _ in item_boxes(P)}
    out.update(dict(structure_boxes(P)))
    return out


def clamp_plate_boxes(P):
    """Display clamp plates under the clamp bosses (cad.display_clamp, screwed to the boss bottom at module_back, clamp t below the
    module back): the plate reaches from its boss towards the glass (long side boss_d / 2 - 1 + reach, short side boss_d / 2 away
    from the glass) and to either side along the glass edge."""
    m = P.mech
    d = m["display"]["clamp"]
    zb = m["stack_z"]["module_back"]
    gx, gy, gw, gh = m["display"]["glass_pocket"]
    long_, short = max(d["w"] - d["boss_d"] / 2, d["boss_d"] / 2 - 1.0 + d["reach"]), d["boss_d"] / 2
    out = []
    for i, (bx, by) in enumerate(m["display"]["clamp_bosses"]):
        y0, y1 = (by - long_, by + short) if by > gy + gh / 2 else (by - short, by + long_)
        out.append((f"display_clamp.{i}", (bx - long_, y0, zb - d["t"], bx + long_, y1, zb)))
    return out


def pwr_key_nut_rule(P):
    """R-PWR-KEY-NUT (W2 MECH-4, B-05): the PV6 nut reserve nut.PWR_KEY and the key body clear the HDMI board, the display, the clamp
    plates, the top Al angle and the plate (the nut only inside the plate notch); OPEN while the nut is not dimensioned."""
    from .layout import gap, pwr_key_nut_box
    m = P.mech
    pk, pv = m["top_face"]["power_key"], P.parts["pv6_button"]
    named = _boxes_by_name(P)
    nut, body = pwr_key_nut_box(P), named["pwr_key_body"]
    checks = {"nut-hdmi_board": gap(nut, named["hdmi_board"]), "body-hdmi_board": gap(body, named["hdmi_board"]),
              "body-display": gap(body, named["display"]), "nut-angle.top.plate": gap(nut, named["angle.top.plate"]),
              "nut-angle.top.wall": gap(nut, named["angle.top.wall"]), "body-plate.main": gap(body, named["plate.main"]),
              "nut-front_wall": m["stack_z"]["front_wall_inner"] - nut[5]}
    for name, c in clamp_plate_boxes(P):
        checks[f"body-{name}"] = gap(body, c)
        checks[f"nut-{name}"] = gap(nut, c)
    notch = [n for n in m["plate"].get("notches", []) if n[0] <= nut[0] - 0.5 and nut[3] + 0.5 <= n[0] + n[2] and n[1] <= nut[1]]
    in_notch = bool(notch) or nut[2] >= m["stack_z"]["plate_front"]
    worst = min(checks, key=checks.get)
    ok = checks[worst] >= 0.5 and in_notch
    val = {"key_x": pk["x"], "key_z": pk["z"], "nut_reserve": [pv["nut_d"], pv["nut_t"]],
           "clear_mm": {k: round(v, 2) for k, v in sorted(checks.items()) if v < 20.0}, "worst": [worst, round(checks[worst], 2)],
           "in_plate_notch": in_notch}
    rule = {"id": "R-PWR-KEY-NUT",
            "rule": "PV6 panel nut inside the top wall (reserve nut.PWR_KEY) and the key body clear of the HDMI board, the display and its clamp plates, "
                    "the top Al angle and the plate (the nut inside the plate notch), >= 0.5",
            "value_mm": val, "limit_mm": 0.5, "source": "parts.json pv6_button (nut_src); mechanical.json top_face.power_key, plate.notches, display.clamp"}
    if not ok:
        why = f"{worst} {checks[worst]:.2f} < 0.5" if checks[worst] < 0.5 else "not inside a plate notch"
        return dict(rule, result=f"FAIL (model): the nut reserve D{pv['nut_d']:g} x {pv['nut_t']:g} at x {pk['x']:g} / z {pk['z']:g}: {why}")
    return dict(rule, result=(
        f"OPEN: the nut is not dimensioned (PV6 and PV2 datasheets; DigiKey PV2PV3PV6HEX16 'HEX NUT FOR PV2 SERIES'; parts.json pv6_button nut_src): "
        f"the reserve D{pv['nut_d']:g} x {pv['nut_t']:g} (assumption) at x {pk['x']:g} / z {pk['z']:g} clears everything by >= 0.5 "
        f"(worst {worst} {checks[worst]:.2f}) inside the plate notch, and the key body no longer touches the plate; measure the received nut at "
        "incoming inspection: a nut wider than the reserve needs the top Al angle notched or the key moved"))


def _harness_near(P, envs, named):
    """Harness routes next to the given envelopes. R-ROUTE-CLEAR checks centrelines only, so this gives the nearest centreline gap
    and the pieces whose bundle (bundle_od_mm / 2 about the centreline) reaches into an envelope. A piece is taken as its bounding
    box: exact for the axis-parallel pieces, a lower bound of the distance otherwise."""
    from . import routes
    from .layout import gap
    res = routes.evaluate(P)
    if res is None:
        return None
    near, over = None, []
    for sid, r in list(res["segments"].items()) + list(res["branches"].items()):
        pts, rad = r.get("points_mm") or [], (r.get("bundle_od_mm") or 0.0) / 2
        for a, b in zip(pts, pts[1:]):
            piece = tuple(min(a[i], b[i]) for i in range(3)) + tuple(max(a[i], b[i]) for i in range(3))
            for e in envs:
                d = max(gap(piece, named[e]), 0.0)
                if near is None or d < near[2] - 1e-9:
                    near = (sid, e, d)
                if rad - d > 1e-9:
                    over.append((sid, e, rad - d))
    worst = max(over, key=lambda o: o[2]) if over else None
    return {"nearest_centreline": [near[0], near[1], round(near[2], 2)] if near else None,
            "bundle_overlaps": len(over), "segments": sorted({o[0] for o in over}), "envelopes": sorted({o[1] for o in over}),
            "worst": [worst[0], worst[1], round(worst[2], 2)] if worst else None}


def hdmi_route_rule(P):
    """R-HDMI-ROUTE (W2 MECH-4, B-04): the FPC route envelopes (adapters, folds, ferrite, insert) are in the envelope check without a
    conflict, each flex is long enough for its centreline with bounded slack, the flex width fits the ferrite slot and the plate notch
    (the bare flex thickness against the slot height only once it is measured: parts.json adafruit_flex thickness)."""
    from .layout import fit_checks
    m = P.mech
    hr = m["hdmi_route"]
    flex, fer = P.parts[hr["flex"]], P.parts[hr["ferrite"]]
    named = _boxes_by_name(P)
    missing = [e for e in hr["envelopes"] if e not in named]
    coll, outside = fit_checks(P)
    env = set(hr["envelopes"])
    conflicts = [f"{c['a']} / {c['b']} {c['gap_mm']}" for c in coll if c["a"] in env or c["b"] in env]
    conflicts += [f"{o['item']} outside on {o['axis']}" for o in outside if o["item"] in env]
    segs, bad = {}, []
    for s in hr["segments"]:
        pts = s["points"]
        cl = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
        length = flex["lengths"][s["part"]]
        slack = length - cl
        segs[s["id"]] = {"part": s["part"], "flex_mm": length, "centreline_mm": round(cl, 1), "slack_mm": round(slack, 1), "folds": s.get("folds", 0)}
        if not 0.0 <= slack <= hr["slack_max"]:
            bad.append(f"{s['id']} slack {slack:.1f} outside 0-{hr['slack_max']:g}")
    w = flex["width"]
    if w > min(fer["cable_width_max"], fer["slot"][0]):
        bad.append(f"flex {w:g} wider than the ferrite slot {fer['slot'][0]:g}")
    t_bare = flex.get("thickness")                  # bare flex, measured; not published by Adafruit (thickness_reserve is with the wrap)
    if t_bare is not None and t_bare > fer["slot"][1]:
        bad.append(f"bare flex {t_bare:g} thicker than the ferrite slot height {fer['slot'][1]:g}")
    nx, ny, nw, nh = m["plate"]["notches_right"][0]
    xc = hr["segments"][0]["points"][4][0]
    if not (nx + hr["notch_clear"] <= xc - w / 2 and xc + w / 2 <= nx + nw - hr["notch_clear"]):
        bad.append(f"flex band x {xc - w / 2:g}-{xc + w / 2:g} not inside the notch x {nx:g}-{nx + nw:g} with {hr['notch_clear']:g} clearance")
    harn = _harness_near(P, [e for e in hr["envelopes"] if e in named], named)
    val = {"segments": segs, "flex_w": w, "ferrite_slot": fer["slot"], "flex_bare_t": t_bare if t_bare is not None else "not published (measure)",
           "notch": [nx, ny, nw, nh], "envelopes": len(hr["envelopes"]), "folds": sum(s.get("folds", 0) for s in hr["segments"]),
           "harness_near": harn}
    rule = {"id": "R-HDMI-ROUTE",
            "rule": "HDMI FPC route Q6A to the Wisecoco input: adapter, fold, ferrite, insert and run envelopes in the envelope check without a conflict; "
                    f"each flex covers its centreline with slack 0-{hr['slack_max']:g} mm; flex width through the ferrite slot and the plate notch "
                    "(bare flex thickness <= the slot height once measured)",
            "value_mm": val, "source": "mechanical.json hdmi_route, layout hdmi_*; parts.json adafruit_3550, adafruit_3548, adafruit_flex, wurth_74278011"}
    problems = [f"missing envelope {e}" for e in missing] + conflicts + bad
    if problems:
        return dict(rule, result="FAIL (model): " + "; ".join(problems))
    f1, f2 = segs["FLEX1"], segs["FLEX2"]
    if harn and harn["nearest_centreline"]:
        hs, he, hd = harn["nearest_centreline"]
        htxt = (f"harness bundles are centrelines in the envelope check (R-ROUTE-CLEAR): the nearest, {hs}, runs {hd:g} mm from {he}"
                + (f"; with bundle_od_mm / 2 about the centreline {harn['bundle_overlaps']} route pieces of {', '.join(harn['segments'])} reach into "
                   f"{', '.join(harn['envelopes'])} (worst {harn['worst'][0]} {harn['worst'][2]:g} mm into {harn['worst'][1]}): the drops must move "
                   "clear of flex 2, OPEN for the harness routes" if harn["bundle_overlaps"] else ""))
    else:
        htxt = "no harness route evaluated"
    return dict(rule, result=(
        f"PASS (model): Adafruit 3550 on the Q6A receptacle, flex 1 {f1['part']} ({f1['slack_mm']:g} mm slack) with the WE-FLAT 74278011 ferrite under the "
        f"LAB BUS nut, through the plate notch to the HDMI_INSERT reserve right of the BMS, flex 2 {f2['part']} ({f2['slack_mm']:g} mm slack) up the strip "
        f"and along y 78.65-88.65 to the Adafruit 3548 in the Wisecoco input; {val['folds']} 45-degree folds; labelled assumptions: 3550 axis from the "
        f"product photos (3550 or 3549 by the receptacle side), flex thickness {flex['thickness_reserve']:g} and bend radius {flex['bend_r']:g} not "
        "published, insert reserve size, Wisecoco HDMI input at the lower end of the board's right edge (STACK D5: measure the received board); "
        f"only the flex width is checked against the ferrite slot: the bare flex must be <= {fer['slot'][1]:g} thick for the "
        f"{fer['slot'][0]:g} x {fer['slot'][1]:g} (+0.5/-0) slot (thickness not published: measure, OPEN); {htxt}; "
        "link, EMI of the wrapped flex and the folds stay bench OPEN"))


def f101_access_rule(P):
    """R-F101-ACCESS (W2 MECH-4, B-12): can F101 face the service hatch for storage? Free depth in the hatch bottom strip in front of
    the USB-A plug bay against the carrier + holder + fuse body stack, and the place must not stand in the hatch access path to a
    keep-clear reserve behind it (the USB-A plug of the Q6A is reached through that strip, hatch.content); otherwise storage opens the
    seam (decision record)."""
    m = P.mech
    fa = m["rear_face"]["hatch"]["f101_access"]
    x, y, w, hh = fa["place"]
    t = m["wall"]
    holder, fuse = P.parts["keystone_3568"], P.parts["littelfuse_mini_297"]
    behind = [(name, bx, it) for iid, name, bx, it in item_boxes(P)
              if iid != "hatch_parts" and not it.get("outside") and bx[0] < x + w and bx[3] > x and bx[1] < y + hh and bx[4] > y and bx[2] > t]
    front = [bx for _, bx, _ in behind]
    z_front = min([bx[2] for bx in front] or [m["stack_z"]["plate_rear"]])
    free = round(z_front - t - fa["clearance"], 2)
    stack = round(fa["carrier_t"] + holder["body"][2] + fuse["body"][2], 2)
    blocks = sorted(name for name, _, it in behind if it.get("keep_clear"))
    val = {"place": fa["place"], "free_depth": free, "stack": stack,
           "stack_parts": {"carrier": fa["carrier_t"], "keystone_3568": holder["body"][2], "mini_fuse_body": fuse["body"][2]},
           "access_path_to": blocks}
    rule = {"id": "R-F101-ACCESS",
            "rule": "F101 for storage (STACK: F1 out for more than 2-4 weeks): the PACK_FUSE carrier with the fuse facing the hatch opening needs "
                    "carrier + Keystone 3568 + MINI body of free depth in the hatch bottom strip, and its place must leave the hatch access path "
                    "to the keep-clear reserves behind it (USB-A plug bay) open; otherwise the seam is opened",
            "value_mm": val, "limit_mm": stack, "source": "mechanical.json rear_face.hatch.f101_access, hatch.content, layout usb_plug_bay; "
                                                          "parts.json keystone_3568, littelfuse_mini_297"}
    if stack <= free and not blocks:
        return dict(rule, result=f"PASS (model): F101 fits facing the hatch opening ({stack:g} <= {free:g} mm free) and leaves the hatch access paths open")
    parts_txt = f"carrier {fa['carrier_t']:g} + Keystone 3568 {holder['body'][2]:g} + MINI body {fuse['body'][2]:g}"
    if stack > free:
        why = [f"facing the opening, the stack needs {stack:g} mm ({parts_txt}) against {free:g} mm in front of the USB-A plug bay"]
    else:
        why = [f"the stack {stack:g} mm ({parts_txt}) fits facing the hatch opening ({free:g} mm free)"]
    if blocks:
        why.append(f"{'but ' if stack <= free else ''}the place is the hatch access path to {', '.join(blocks)} (the USB-A plug of the Q6A goes in "
                   "through this strip, hatch.content)")
    return dict(rule, result=(
        "PASS (model, decision: seam): storage keeps the seam procedure, F101 is not reached through the hatch: " + "; ".join(why)
        + "; the rest of the hatch footprint is the hatch board (J502, J503) and the EDL key; F101 stays on the PACK_FUSE carrier beside the battery "
        "tray (envelope MECH-5) and comes out after the seam is opened (build/21 section 4 item 7, build/15 'Ущільнення')"))


def p8_accessory_rule(P):
    """R-P8-ACCESSORY (W2 MECH-4, CC-27): the external P8 inline accessory (outside the enclosure) and what its envelope still lacks."""
    pa = P.parts["p8_accessory"]
    mods = pa["modules"]
    open_ = [f"{k}: {v.get('_tbd_reason', 'TBD')}" for k, v in mods.items() if not v.get("size")]
    val = {"outside_enclosure": True, "chain": pa["chain"], "modules": {k: v.get("size") for k, v in mods.items()},
           "envelope": {k: v for k, v in pa["envelope"].items() if not k.startswith("_")}}
    rule = {"id": "R-P8-ACCESSORY",
            "rule": "P8 external inline accessory (A403 -> A404 in the antenna line, ch4 bias through P8): module envelopes, chain and the parts still open",
            "value_mm": val, "source": "parts.json p8_accessory; build/03 P8 row; build/15 'Шлях P8 (W2 AREA)'"}
    if open_:
        return dict(rule, result="OPEN: " + "; ".join(open_) + "; " + pa["envelope"]["_tbd_reason"]
                    + "; sealing of the accessory box is OPEN (T-07); assembly order build/21 E9c")
    return dict(rule, result="PASS (model): every module of the accessory has an envelope")


def w2_mech4_rules(P):
    """Rows added by W2 MECH-4 (registration list, append-only)."""
    return [f101_access_rule(P), p8_accessory_rule(P)]


def module_mount_geometry(P):
    """Bosses, rests, spigots and pads of mechanical.json module_mounts as plain numbers (shared by cad.py, the drawings and the rule).

    rear_wall: (x, y) circles standing on the rear-wall inner face up to seat; top_wall: (x, z) circles hanging from the top-wall
    pocket floor down to seat. seat is the printed face; a taped mount (tape_t) has the board tape_t beyond it (rear: +z, top: -y),
    otherwise the board lies on it. Insert holes are hole_depth deep from the seat face; a spigot stands len on its rest face."""
    mm = P.mech.get("module_mounts")
    if not mm:
        return []
    ins = mm["insert"]
    depth = ins.get("hole_depth", ins["len"])
    out = []
    for mt in mm["mounts"]:
        if mt["on"] not in ("rear_wall", "top_wall"):
            continue
        if "pad" in mt:
            out.append({"item": mt["item"], "on": mt["on"], "kind": "pad", "rect": tuple(mt["pad"]), "seat": mt["pad_top_z"], "tape_t": mt["tape_t"]})
            continue
        board = mt.get("seat_z", mt.get("seat_y"))
        tape = mt.get("tape_t", 0.0)
        face = board - tape if mt["on"] == "rear_wall" else board + tape
        for kind in ("screws", "rests"):
            for c in mt.get(kind, []):
                out.append({"item": mt["item"], "on": mt["on"], "kind": kind, "c": tuple(c), "d": mm["boss_d"] if kind == "screws" else mm["rest_d"],
                            "insert": kind == "screws", "hole_d": ins["hole_d"], "hole_depth": depth, "seat": face if kind == "rests" else board,
                            "board": board, "tape_t": tape if kind == "rests" else 0.0})
        for c in mt.get("spigots", []):
            out.append({"item": mt["item"], "on": mt["on"], "kind": "spigot", "c": tuple(c), "d": mt["spigot_d"], "insert": False,
                        "seat": face, "board": board, "len": mt["spigot_len"]})
    return out


def _seg_box_dist(a, b, bx):
    """Shortest distance between the segment a-b and the box (x0, y0, z0, x1, y1, z1): convex along the segment, golden-section search."""
    def d(t):
        p = [a[i] + t * (b[i] - a[i]) for i in range(3)]
        return math.sqrt(sum(max(bx[i] - p[i], 0.0, p[i] - bx[i + 3]) ** 2 for i in range(3)))
    lo, hi = 0.0, 1.0
    g = (math.sqrt(5) - 1) / 2
    for _ in range(48):
        m1, m2 = hi - g * (hi - lo), lo + g * (hi - lo)
        if d(m1) <= d(m2):
            hi = m2
        else:
            lo = m1
    return min(d(0.0), d(1.0), d((lo + hi) / 2))


def _terminal_room(P, ina, side, routes_all, unit, t):
    """Free length in front of the INA228 terminal-block wire entries: envelopes and harness bundles (bundle_od_mm / 2) that cross the
    terminal span in front of the face, the routes ending at the INA228 itself (S06) excepted; the enclosure wall bounds it.
    Returns (envelopes only, envelopes and bundles, what limits it)."""
    W, H, D = P.outer
    cx = (ina[0] + ina[3]) / 2
    span = (cx - 3.5 * 1.5, cx + 3.5 * 1.5)
    face = ina[4] if side == "+y" else ina[1]
    sgn = 1.0 if side == "+y" else -1.0
    env = [((b[1] if side == "+y" else b[4]), iid) for iid, name, b, it in item_boxes(P) if iid != "ina228" and b[0] < span[1] and b[3] > span[0]
           and b[2] < ina[5] and b[5] > ina[2] and sgn * ((b[1] if side == "+y" else b[4]) - face) >= -1e-6]
    env.append(((H - t) if side == "+y" else t, "wall"))
    lim_env = min(env, key=lambda v: sgn * (v[0] - face))
    best = (sgn * (lim_env[0] - face), lim_env[1])
    for sid, r in routes_all:
        if unit in r.get("ends", []):
            continue
        od = r.get("bundle_od_mm") or 0.0
        pts = r.get("points_mm") or []
        for a, b in zip(pts, pts[1:]):
            n = max(2, int(math.dist(a, b) / 0.5) + 1)
            for k in range(n + 1):
                p = [a[i] + k / n * (b[i] - a[i]) for i in range(3)]
                if span[0] - od / 2 < p[0] < span[1] + od / 2 and ina[2] - od / 2 < p[2] < ina[5] + od / 2 and sgn * (p[1] - face) > 0:
                    room = sgn * (p[1] - face) - od / 2
                    if room < best[0]:
                        best = (room, sid)
    return round(sgn * (lim_env[0] - face), 2), round(best[0], 2), best[1]


def module_mounts_rule(P):
    """R-MODULE-MOUNTS (W2 MECH-5, B-13 / CC-36 item 11): fixing of the modules without a board place; insert skins, seats against the
    envelopes, insert holes clear of the tripod nut pocket, plate standoffs, the INA228 terminal-block wire side (envelopes and harness
    bundles) and the 18 AWG fit, the harness-bundle clearance of this package's envelopes, and what stays open."""
    from . import routes
    from .layout import gap as box_gap
    m = P.mech
    mm = m.get("module_mounts")
    rule = {"id": "R-MODULE-MOUNTS",
            "rule": "module fixing (mechanical.json module_mounts): insert hole + skin <= wall + boss, board face = envelope face, screw holes = the "
                    "makers' board-file holes, rear-wall insert holes >= tripod_clear from the 1/4-20 nut pocket, the INA228 terminal wire side free of "
                    "envelopes and harness bundles, 18 AWG inside the terminal range, this package's envelopes >= bundle OD / 2 + bundle_clear from "
                    "other routes, plate standoff barrels clear of the envelopes; plate standoff holes in R-HOLE-EDGE / R-CLINCH-EDGE",
            "source": "mechanical.json module_mounts, rear_face.tripod; parts.json adafruit_5997, adafruit_4162, adafruit_ina228_5832, pololu_2813, "
                      "pem_so_m25_6; generated/harness-routes.json bundle_od_mm"}
    if not mm:
        return dict(rule, value_mm=None, result="OPEN: no module_mounts")
    W, H, D = P.outer
    t = m["wall"]
    boxes = {iid: bx for iid, name, bx, it in item_boxes(P)}
    tp = m["rear_face"]["tripod"]
    hexr = tp["hex_af"] / 2 / math.cos(math.radians(30))
    veml = P.parts["adafruit_4162"]
    pocket = {mt["item"]: mt["pocket"][4] for mt in mm["mounts"] if "pocket" in mt}
    bad, val, tri = [], {}, []
    for g in module_mount_geometry(P):
        bx = boxes[g["item"]]
        if g["kind"] == "spigot":
            # a locating spigot on a taped rest: thinner than the board hole, ends inside the board
            ok = g["on"] == "top_wall" and g["d"] < veml["holes"]["d"] and g["len"] <= g["seat"] - g["board"] + veml["board"][2] - 0.1
            val.setdefault(g["item"], {}).setdefault("spigots", []).append({"c": list(g["c"]), "d": g["d"], "len": g["len"]})
        elif g["on"] == "rear_wall":
            if g["kind"] == "pad":
                x, y, w, h = g["rect"]
                ok = bx[0] <= x and x + w <= bx[3] and bx[1] <= y and y + h <= bx[4] and abs(g["seat"] + g["tape_t"] - bx[2]) < 1e-6
                val.setdefault(g["item"], {})["pad"] = {"rect": list(g["rect"]), "seat_z": g["seat"], "tape": g["tape_t"]}
            else:
                x, y = g["c"]
                skin = g["seat"] - g["hole_depth"] if g["insert"] else None
                ok = bx[0] <= x <= bx[3] and bx[1] <= y <= bx[4] and abs(g["board"] - bx[2]) < 1e-6 and (skin is None or skin >= mm["insert"]["skin_min"])
                row = {"c": [x, y], "skin_mm": None if skin is None else round(skin, 2)}
                if g["insert"]:
                    dt = round(math.hypot(x - tp["c"][0], y - tp["c"][1]) - hexr - g["hole_d"] / 2, 2)
                    row["to_tripod_pocket_mm"] = dt
                    tri.append(dt)
                    ok = ok and dt >= mm.get("tripod_clear", 0.0)
                val.setdefault(g["item"], {}).setdefault(g["kind"], []).append(row)
        else:
            x, z = g["c"]
            skin = H - (g["seat"] + g["hole_depth"]) if g["insert"] else None
            ok = (bx[0] <= x <= bx[3] and bx[2] <= z <= bx[5] and (skin is None or skin >= mm["insert"]["skin_min"])
                  and g["board"] <= g["seat"] <= H - t + pocket.get(g["item"], 0.0) + 1e-6)
            val.setdefault(g["item"], {}).setdefault(g["kind"], []).append({"c": [x, z], "skin_mm": None if skin is None else round(skin, 2),
                                                                            "face_y": round(g["seat"], 2), "tape": g.get("tape_t", 0.0)})
        if not ok:
            bad.append(f"{g['item']} {g['kind']} {g.get('c', g.get('rect'))}")
    # VEML7700: pocket skin, board front edge to the front wall, back face to the envelope below it
    vm = next((mt for mt in mm["mounts"] if mt["item"] == "veml7700"), None)
    if vm:
        px, pz, pw, ph, pd = vm["pocket"]
        fwi = m["stack_z"]["front_wall_inner"]
        val["veml7700"]["pocket_skin_mm"] = round(t - pd, 2)
        val["veml7700"]["front_edge_to_wall_mm"] = round(fwi - boxes["veml7700"][5], 2)
        if t - pd < 1.0 or fwi - boxes["veml7700"][5] < 0.5:
            bad.append("veml7700 pocket skin or front edge")
    res = routes.evaluate(P)
    allr = (list(res["segments"].items()) + list(res["branches"].items()) + list(res.get("coax", {}).items())) if res else []
    # INA228: free length in front of the terminal-block wire entries (envelopes and harness bundles) and the 18 AWG range
    ina, term = boxes["ina228"], P.parts["adafruit_ina228_5832"]["terminal"]
    side = next((mt.get("terminal_side", "-y") for mt in mm["mounts"] if mt["item"] == "ina228"), "-y")
    env_room, room, lim = _terminal_room(P, ina, side, allr, "INA", t)
    awg = 18
    val["ina228"]["terminal"] = {"wire_side": side, "free_mm": room, "free_envelopes_only_mm": env_room, "limited_by": lim, "need_mm": term["wire_room"],
                                 "awg_range": term["wire_awg"], "vin_awg": awg}
    if room < term["wire_room"] or not (term["wire_awg"][0] <= awg <= term["wire_awg"][1]):
        bad.append("ina228 terminal wire side")
    # this package's envelopes against the harness bundles of the routes that do not end at them
    margin = mm.get("bundle_clear", 0.5)
    bc = {}
    for iid, unit in mm.get("bundle_items", {}).items():
        bx = boxes[iid]
        worst = None
        for sid, r in allr:
            if unit in r.get("ends", []) or len(r.get("points_mm") or []) < 2:
                continue
            need = (r.get("bundle_od_mm") or 0.0) / 2 + margin
            dmin = min(_seg_box_dist(a, b, bx) for a, b in zip(r["points_mm"], r["points_mm"][1:]))
            if worst is None or dmin - need < worst[0]:
                worst = (dmin - need, sid, round(dmin, 2), round(need, 2))
        if worst:
            bc[iid] = {"route": worst[1], "centreline_mm": worst[2], "need_mm": worst[3]}
            if worst[0] < -1e-6:
                bad.append(f"{iid} {worst[2]:g} from the {worst[1]} centreline < bundle OD / 2 + {margin:g} = {worst[3]:g}")
    val["bundle_clearance"] = bc
    # plate standoff barrels (front face up to the board) clear of every other envelope and of the structure (plate bosses)
    from .layout import structure_boxes
    obst = dict(boxes)
    obst.update({n: b for n, b in structure_boxes(P) if n not in ("plate.main", "plate.ext")})
    pfz = m["stack_z"]["plate_front"]
    val["plate_standoffs"] = {}
    for mt in mm["mounts"]:
        if mt["on"] != "plate_front":
            continue
        f = P.parts[mt["fastener"]]
        r = f.get("barrel_d", f["hole_d"]) / 2
        rows = []
        for (hx, hy) in mt["standoffs"]:
            bar = (hx - r, hy - r, pfz, hx + r, hy + r, pfz + f["length"])
            near = min(((box_gap(bar, b), iid) for iid, b in obst.items() if not iid.startswith(mt["item"])), default=(99.0, ""))
            rows.append({"c": [hx, hy], "nearest": near[1], "gap_mm": round(near[0], 2)})
            if near[0] < 0.5:
                bad.append(f"{mt['item']} standoff ({hx:g}, {hy:g}) {near[0]:.2f} from {near[1]}")
        val["plate_standoffs"][mt["item"]] = rows
    rule["value_mm"] = val
    if bad:
        return dict(rule, result="FAIL (model): " + "; ".join(bad))
    opens = [f"{iid}: fixing TBD ({P.parts[it['part']]['status']}, no drawing)" for it in m["layout"]["items"]
             for iid in [it["id"]] if iid == "boni_a406"]
    vr = val["veml7700"]["rests"]
    gaps = [rw["gap_mm"] for rows in val["plate_standoffs"].values() for rw in rows]
    return dict(rule, result=(
        "PASS (model): CH334F 4 x M2.5 and INA228 2 x M2.5 (+2 rests) into TC-M2,5x4 inserts in rear-wall bosses (hole "
        f"{mm['insert'].get('hole_depth', mm['insert']['len']):g} deep, skin {min(v['skin_mm'] for v in val['hub_ch334f']['screws']):g}, "
        f"{min(tri):g} from the tripod nut pocket >= {mm.get('tripod_clear', 0.0):g}), #2813 on a printed pad with acrylic foam tape (no mounting "
        f"hole on the Pololu drawing), VEML7700 taped to {len(vr)} rests (+{len(val['veml7700'].get('spigots', []))} locating spigots) in a "
        f"{vm['pocket'][4]:g} mm pocket of the top wall (skin {val['veml7700']['pocket_skin_mm']:g}; no insert joint fits that wall), PACK_FUSE on "
        f"2 PEM SO-M2.5-6ZI (M-07 PF; barrels {min(gaps):g} from the nearest envelope); INA228 terminal wire side {side} with {room:g} mm free of "
        f"envelopes and harness bundles (limit: {lim}), 18 AWG inside {term['wire_awg'][1]}-{term['wire_awg'][0]} AWG (4UCON 19963; block identity "
        f"inferred, confirm at incoming inspection); this package's envelopes keep bundle OD / 2 + {margin:g} from the other route centrelines; "
        "torques coupon-defined (build/17 section 2)" + ("; OPEN: " + "; ".join(opens) if opens else "")))


def w2_mech5_rules(P):
    """Rows added by W2 MECH-5 (registration list, append-only)."""
    return [module_mounts_rule(P)]


# ---- W2 MECH-7 (SHRINK-2): converter zones, two-sided PWR-A, H-TRIM, mated header heights under the display ----
def _budget_planned():
    from .boards import budget_candidate
    ch, cand = budget_candidate()
    return ch, cand or {}, (cand or {}).get("planned") or {}


def _pack_in_zone(sizes, zw, zh):
    """Best simple arrangement of courtyards (w, h) inside a zone zw x zh: every part turned 0 or 90 deg, all in one row
    along x or one column along y; (margin, arrangement, dims) with margin = the smaller free length, or None."""
    best = None
    for flips in itertools.product((0, 1), repeat=len(sizes)):
        dims = [(h, w) if f else (w, h) for (w, h), f in zip(sizes, flips)]
        for how, W, H in (("row along x", sum(d[0] for d in dims), max(d[1] for d in dims)),
                          ("column along y", max(d[0] for d in dims), sum(d[1] for d in dims))):
            if W <= zw + 1e-9 and H <= zh + 1e-9:
                m = min(zw - W, zh - H)
                if best is None or m > best[0] + 1e-9:
                    best = (m, how, dims)
    return best


def pwr_zones_rule(P):
    """R-PWR-ZONES: the converter of each PWR-A converter zone fits inside its thermal_bond zone (boards.json PWR
    converter_zones). W2 MECH-7 part 2: once GR-5A has put the converter into the graph (its budget block is retired,
    boards.planned_live), the graph courtyards of the zone refs (converter_zone_refs: the exposed-pad IC and its power
    inductor) are packed into the zone, every part turned 0 or 90 deg, in one row or one column; until then the SHRINK-2
    study block of the partition budget stands for it (block w x d in either orientation). MODEL: positions at placement."""
    from .boards import footprint_courtyards, graph_board_parts, retired_blocks
    b = P.boards["boards"]["PWR"]
    ch, cand, planned = _budget_planned()
    blocks = {bl["id"]: bl for bl in planned.get("blocks", [])}
    retired = retired_blocks()
    zrefs = b.get("converter_zone_refs", {})
    rule = {"id": "R-PWR-ZONES", "rule": "PWR-A converters inside their thermal_bond zones (graph courtyards of the zone refs once GR-5A has "
                                         "placed them in the graph, else the budget block; each part turned 0 or 90 deg)",
            "source": f"boards.json PWR thermal_bond / converter_zones / converter_zone_refs; pcb/generated/components.csv and the vendored "
                      f"KiCad 10.0.7 courtyards (build/kicad/footprints/manifest.json); pcb/partition-budget.json candidates.{ch}.planned.blocks "
                      "(SHRINK-2 study blocks, MODEL) while a block is pending"}
    if not b.get("converter_zones"):
        return dict(rule, value_mm=None, result="OPEN: boards.json PWR has no converter_zones")
    graph = graph_board_parts()
    cy = footprint_courtyards()
    val, bad, opened, txt = {}, [], [], []
    for zn, bid in sorted(b["converter_zones"].items()):
        z = b["thermal_bond"][int(zn) - 1]
        refs = zrefs.get(zn, [])
        real = bool(refs) and all(r in graph and graph[r].get("mount") != "pcb_module" and cy.get(graph[r]["footprint"]) for r in refs)
        if real and (bid in retired or bid not in blocks):
            sizes = [(cy[graph[r]["footprint"]]["w"], cy[graph[r]["footprint"]]["h"]) for r in refs]
            fit = _pack_in_zone(sizes, z[2], z[3])
            row = {"zone_mm": z, "basis": "graph courtyards (GR-5A)", "refs": {r: [round(w, 2), round(h, 2)] for r, (w, h) in zip(refs, sizes)},
                   "footprints": {r: graph[r]["footprint"] for r in refs}, "block_retired": bid,
                   "budget_still_lists_block": bid in blocks,
                   "margin_mm": None if fit is None else round(fit[0], 2), "arrangement": None if fit is None else fit[1]}
            val[f"zone {zn}"] = row
            parts = " + ".join(f"{r} {w:g} x {h:g}" for r, (w, h) in zip(refs, sizes))
            if fit is None:
                bad.append(f"zone {zn} {z[2]:g} x {z[3]:g} cannot hold {parts} in a row or a column")
            else:
                txt.append(f"zone {zn} {z[2]:g} x {z[3]:g} holds {parts} (graph courtyards, {fit[1]}, margin {fit[0]:.2f})")
            continue
        bl = blocks.get(bid)
        if bl is None:
            opened.append(f"zone {zn}: block {bid} not in the budget and the zone refs {', '.join(refs) or '(none)'} are not graph board parts")
            continue
        fits = [(z[2] - w, z[3] - d) for w, d in ((bl["w"], bl["d"]), (bl["d"], bl["w"])) if w <= z[2] + 1e-9 and d <= z[3] + 1e-9]
        margin = max((min(m) for m in fits), default=None)
        val[f"zone {zn}"] = {"zone_mm": z, "basis": "budget block", "block": bid, "block_mm": [bl["w"], bl["d"]], "block_h_mm": bl.get("h"),
                             "margin_mm": None if margin is None else round(margin, 2)}
        if margin is None:
            bad.append(f"zone {zn} {z[2]:g} x {z[3]:g} < {bid} {bl['w']:g} x {bl['d']:g}")
        else:
            txt.append(f"zone {zn} {z[2]:g} x {z[3]:g} holds {bid} {bl['w']:g} x {bl['d']:g} (budget block, margin {margin:g})")
    if bad:
        return dict(rule, value_mm=val, result="FAIL (model): " + "; ".join(bad))
    if opened:
        return dict(rule, value_mm=val, result="OPEN: " + "; ".join(opened) + ("; " + "; ".join(txt) if txt else ""))
    gone = sorted({v["block_retired"] for v in val.values() if v.get("budget_still_lists_block")})
    note = (f"; the budget blocks {', '.join(gone)} retired with GR-5A, pcb/partition-budget.json still lists them until the AREA lineage "
            "reruns pcb/partition_budget.py" if gone else "")
    return dict(rule, value_mm=val, limit_mm="converter inside its zone",
                result=f"PASS (model): {'; '.join(txt)}{note}; the power passives sit next to them (TI layout), positions at the PCB-PWRA-3 placement")


def pwr_bottom_rule(P):
    """R-PWR-BOTTOM: the bottom side of the two-sided PWR-A (boards.json PWR bottom_side) has room: the PB pockets hold the
    budget's bottom refs (raw and at the 1.8 planning factor), and the room h_max = shim gap + pocket depth - film - clearance."""
    b = P.boards["boards"]["PWR"]
    bs = b.get("bottom_side")
    spec = P.mech["plate"].get("pwr_bottom_pockets")
    rule = {"id": "R-PWR-BOTTOM", "rule": "bottom-side parts of PWR-A: inside the plate pockets PB*, no taller than shim gap + pocket depth - polyimide film - clearance",
            "source": "boards.json PWR bottom_side; mechanical.json plate.pwr_bottom_pockets, pwr_bond.shim; pcb/partition-budget.json candidates.<chosen>.boards.PWR_A_BOTTOM"}
    if not bs or not spec:
        return dict(rule, value_mm=None, result="OPEN: boards.json PWR bottom_side or mechanical.json plate.pwr_bottom_pockets missing")
    shim = P.mech["pwr_bond"]["shim"]
    h_max = pwr_bottom_h_max(P)
    regions = pwr_bottom_regions(P)
    area = sum(r[2] * r[3] for _, r in regions)
    ch, cand, _ = _budget_planned()
    row = (cand.get("boards") or {}).get("PWR_A_BOTTOM") or {}
    refs = (cand.get("pwr_a_bottom") or {}).get("refs")
    raw, d18 = row.get("parts_raw_mm2"), row.get("demand_1.8_mm2")
    depth = b.get("tht_pockets", {}).get("depth", 1.0)
    val = {"pockets": len(regions), "pocket_area_mm2": round(area, 1), "h_room_mm": round(shim + depth, 3), "film_mm": spec["film_t"],
           "clearance_mm": bs["clearance"], "h_max_mm": h_max, "bottom_refs": refs, "budget_raw_mm2": raw, "budget_demand_1_8_mm2": d18,
           "raw_fill": round(raw / area, 3) if raw and area else None, "ratio_1_8": round(d18 / area, 3) if d18 and area else None,
           "budget_bottom_usable_mm2": row.get("usable_mm2")}
    if raw is None or not area:
        return dict(rule, value_mm=val, result=f"OPEN: pcb/partition-budget.json candidates.{ch} has no PWR_A_BOTTOM row or no PB pocket; "
                                               f"{len(regions)} pockets, {area:.0f} mm2, h_max {h_max:g}")
    if raw > area + 1e-9:
        return dict(rule, value_mm=val, result=f"FAIL (model): bottom courtyards {raw:g} mm2 > the PB pockets {area:.0f} mm2")
    fit18 = "fits" if d18 <= area + 1e-9 else "does NOT fit"
    return dict(rule, value_mm=val, limit_mm={"h_max": h_max, "pocket_area_mm2": round(area, 1)},
                result=(f"OPEN: {refs} bottom refs, courtyards {raw:g} mm2 = {raw / area:.2f} of the {len(regions)} PB pockets ({area:.0f} mm2; "
                        f"{d18:g} at 1.8 {fit18}, ratio {d18 / area:.2f}); room {shim + depth:g} - film {spec['film_t']:g} - clearance "
                        f"{bs['clearance']:g} = h_max {h_max:g} mm; {bs.get('heights', 'per-part heights TBD')}; positions at the PCB-PWRA-3 placement"))


def pwr_bottom_h_max(P):
    """Room of a PWR-A bottom-side part: shim gap + pocket depth - polyimide film - clearance (boards.json PWR bottom_side)."""
    bs = P.boards["boards"]["PWR"].get("bottom_side")
    spec = P.mech["plate"].get("pwr_bottom_pockets")
    if not bs or not spec:
        return None
    depth = P.boards["boards"]["PWR"].get("tht_pockets", {}).get("depth", 1.0)
    return round(P.mech["pwr_bond"]["shim"] + depth - spec["film_t"] - bs["clearance"], 3)


def h_trim_rule(P):
    """R-H-TRIM: the H-TRIM stack (boards.json PWR h_trim = pcb/partition-spec.json keepouts.h_trim): PWR-B bottom face -
    trimmed pin protrusion - (PWR-A component face + zone part height) leaves at least the 0.5 mm model gap; the trim is a
    proof-fit gate (OPEN)."""
    import json
    from pathlib import Path
    a, bb = P.boards["boards"]["PWR"], P.boards["boards"]["PWR_B"]
    ht = a.get("h_trim")
    rule = {"id": "R-H-TRIM", "rule": "rule H-TRIM: PWR-A parts <= zone_h_max under the PWR-B THT pin fields, pins trimmed to <= protrusion_max; clearance >= 0.5 (model gap)",
            "source": "boards.json PWR h_trim, PWR_B place; pcb/partition-spec.json keepouts.h_trim (W2 AREA-2)"}
    if not ht:
        return dict(rule, value_mm=None, result="OPEN: boards.json PWR has no h_trim")
    t = P.board_t("PWR")        # W2 MECH-8: the 6-layer PWR-A thickness
    face = a["place"]["z_bottom"] + t
    under = bb["place"]["z_bottom"]
    clear = round(under - ht["protrusion_max"] - (face + ht["zone_h_max"]), 3)
    p = Path(__file__).resolve().parents[2] / "pcb" / "partition-spec.json"
    spec = json.loads(p.read_text(encoding="utf-8"))["keepouts"].get("h_trim", {}) if p.exists() else {}
    diff = [k for k, s in (("protrusion_max", "protrusion_max_mm"), ("zone_h_max", "zone_h_max_mm"))
            if s in spec and abs(ht[k] - spec[s]) > 1e-9]
    if "clearance_mm" in spec and abs(clear - spec["clearance_mm"]) > 1e-6:
        diff.append("clearance")
    val = {"pwr_a_face_z": face, "pwr_b_bottom_z": under, "protrusion_max": ht["protrusion_max"], "zone_h_max": ht["zone_h_max"], "clearance_mm": clear,
           "spec_clearance_mm": spec.get("clearance_mm")}
    if diff or clear < 0.5 - 1e-9:
        return dict(rule, value_mm=val, limit_mm=0.5, result="FAIL (model): " + (f"differs from pcb/partition-spec.json keepouts.h_trim: {', '.join(diff)}" if diff
                                                                                 else f"clearance {clear:g} < 0.5"))
    return dict(rule, value_mm=val, limit_mm=0.5,
                result=(f"OPEN: stack {under:g} - {ht['protrusion_max']:g} - ({face:g} + {ht['zone_h_max']:g}) = {clear:g} mm clearance (model arithmetic, "
                        f"equal to pcb/partition-spec.json keepouts.h_trim); {ht['gate']}"))


def _channel_floor(P):
    """z of the path-2 channel floor under the display: module back - air_channel (pcb/partition-spec.json envelope, else 4.0)."""
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parents[2] / "pcb" / "partition-spec.json"
    need = 4.0
    if p.exists():
        need = json.loads(p.read_text(encoding="utf-8")).get("envelope", {}).get("air_channel", need)
    return round(P.mech["stack_z"]["module_back"] - need, 3), need


def mated_height_rule(P):
    """R-HDR-MATED (W2 MECH-7): every PWR-A header of build/16 (board PWR_A) whose edge strip lies under the display module
    has its mated top (PWR-A component face + header and plug height) at or below the floor of the path-2 channel
    (display module back - air_channel). The edge comes from boards.json PWR edge_zones 'headers'; the strip is the zone span
    x the header courtyard depth (smaller courtyard side, the long side along the edge), so 'under the display' is the
    possible worst case until the PCB-PWRA-3 placement. Reported per header; OPEN while a header fails as specified or has no
    read mated height (family and orientation are GR's, build/16); never FAIL."""
    import csv
    from pathlib import Path
    from .boards import footprint_courtyards, header_size, header_height_basis, HEADER_ALT
    root = Path(__file__).resolve().parents[2]
    a = P.boards["boards"]["PWR"]
    t = P.board_t("PWR")        # W2 MECH-8: the 6-layer PWR-A thickness
    face = round(a["place"]["z_bottom"] + t, 3)
    ox, oy = a["place"]["origin"]
    z_lim, need = _channel_floor(P)
    disp = [bx for iid, _, bx, _ in item_boxes(P) if iid == "display"][0]
    hh = P.parts["harness_headers"]
    rule = {"id": "R-HDR-MATED",
            "rule": f"PWR-A headers under the display: mated top (PWR-A face {face:g} + header and plug) <= the path-2 channel floor "
                    f"{z_lim:g} (display module back {P.mech['stack_z']['module_back']:g} - channel {need:g})",
            "source": "build/16-dzhgut-rozyemy.csv (board PWR_A); boards.json PWR edge_zones headers; parts.json harness_headers h_mated; "
                      "mechanical.json stack_z.module_back, layout display; pcb/partition-spec.json envelope.air_channel"}
    path = root / "build" / "16-dzhgut-rozyemy.csv"
    if not path.exists():
        return dict(rule, value_mm=None, result="OPEN: build/16-dzhgut-rozyemy.csv not found")
    edge_of = {h: i for i, ez in enumerate(a.get("edge_zones", [])) for h in ez.get("headers", [])}
    fps = {}
    comp = root / "pcb" / "generated" / "components.csv"
    if comp.exists():
        with comp.open(encoding="utf-8", newline="") as fh:
            fps = {r["ref"]: r["footprint"] for r in csv.DictReader(fh)}
    cy = footprint_courtyards()
    xs0, ys0 = [p[0] for p in a["outline"]], [p[1] for p in a["outline"]]
    rows, fail, tbd, alt_ok = [], [], [], []
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("board") != "PWR_A":
                continue
            ref, fam, orient = r["connector"], r["family"], r["orientation"]
            key = f"{fam}_{orient}"
            hm = hh.get(key, {}).get("h_mated")
            c = cy.get(fps[ref]) if ref in fps else None
            if c:
                depth, how = min(c["w"], c["h"]), "KiCad courtyard"
            else:
                size = header_size(P, fam, int(r["pins"]), "PWR", cy)
                depth, how = (size[1], "parts.json") if size else (None, None)
            row = {"connector": ref, "segment": r["segment"], "family": key, "h_mated_mm": hm, "h_basis": header_height_basis(P, key)}
            zi = edge_of.get(ref)
            if zi is None or depth is None:
                row["verdict"] = "TBD: no exit edge in boards.json PWR edge_zones headers" if zi is None else "TBD: no courtyard depth"
                tbd.append(ref)
                rows.append(row)
                continue
            ez = a["edge_zones"][zi]
            s0, s1 = ez["span"]
            if ez["edge"] == "bottom":
                strip = (s0, min(ys0), s1, min(ys0) + depth)
            elif ez["edge"] == "top":
                yt = ez.get("at", max(ys0))
                strip = (s0, yt - depth, s1, yt)
            elif ez["edge"] == "right":
                strip = (max(xs0) - depth, s0, max(xs0), s1)
            else:
                strip = (min(xs0), s0, min(xs0) + depth, s1)
            enc = (ox + strip[0], oy + strip[1], ox + strip[2], oy + strip[3])
            under = enc[0] < disp[3] and enc[2] > disp[0] and enc[1] < disp[4] and enc[3] > disp[1]
            row.update(edge_zone=zi, edge=ez["edge"], depth_mm=round(depth, 2), depth_from=how, strip_xy=[round(v, 2) for v in enc], under_display=under)
            if not under:
                row["verdict"] = "outside the display footprint (no channel limit)" + ("" if hm is not None else "; mated height not read (TBD)")
            elif hm is None:
                row["verdict"] = "TBD: under the display, mated height not read"
                tbd.append(ref)
            else:
                top = round(face + hm, 2)
                row["mated_top_z"] = top
                if top <= z_lim + 1e-9:
                    row["verdict"] = f"PASS (model): mated top {top:g} <= {z_lim:g}"
                else:
                    row["verdict"] = f"FAIL as specified: mated top {top:g} > {z_lim:g}"
                    fail.append(f"{ref} {key} {top:g}")
                    alt = HEADER_ALT.get(fam)
                    ha = hh.get(f"{fam}_{alt}", {}).get("h_mated") if alt else None
                    if ha is not None:
                        ta = round(face + ha, 2)
                        ok = ta <= z_lim + 1e-9
                        row["alternative"] = {"family": f"{fam}_{alt}", "h_mated_mm": ha, "mated_top_z": ta, "fits": ok}
                        row["verdict"] += f"; as {fam}_{alt} (mated {ha:g}) {ta:g}: " + ("passes" if ok else "fails")
                        if ok:
                            alt_ok.append(ref)
                        # W2 MECH-7 review F1: the alternative's courtyard against the one of the specified part (PWR-A top area)
                        sa = header_size(P, fam, int(r["pins"]), "PWR", cy, orient=alt)
                        now = c["w"] * c["h"] if c else (size[0] * size[1] if size else None)
                        if sa and now is not None:
                            row["alternative"].update(courtyard_mm=[round(sa[0], 2), round(sa[1], 2)], courtyard_from=sa[2],
                                                      area_delta_mm2=round(sa[0] * sa[1] - now, 1))
                    else:
                        row["verdict"] += "; no lower-mated part of this family read (TBD)"
                # W2 MECH-7 review F1: the longest run of the exit edge zone whose strip lies outside the display footprint
                row["off_display_run_mm"] = _off_display_run(enc, ez["edge"], disp)
            rows.append(row)
    passed = [x["connector"] for x in rows if x.get("verdict", "").startswith("PASS")]
    outside = [x["connector"] for x in rows if x.get("under_display") is False]
    val = {"channel_floor_z": z_lim, "pwr_a_face_z": face, "under_display_pass": passed, "fails_as_specified": fail,
           "alternative_passes": alt_ok, "tbd": tbd, "outside_display": outside}
    cost = _alternative_area_cost(rows, alt_ok)
    val.update(cost)
    parts = []
    if passed:
        parts.append(f"{len(passed)} pass ({', '.join(passed)})")
    if fail:
        parts.append(f"{len(fail)} fail as specified ({', '.join(fail)})"
                     + (f", as the right-angle Micro-Fit 43650 (MF_ra) {', '.join(alt_ok)} pass" if alt_ok else ""))
        parts.append(cost["text"])
        no_alt = [x["connector"] for x in rows if x.get("verdict", "").startswith("FAIL") and "alternative" not in x]
        if no_alt:
            parts.append(f"no passing part read for {', '.join(no_alt)} (TBD: a lower-mated part or a place outside the display)")
        runs =[f"{x['connector']} {x['edge']} {x['off_display_run_mm']['run_mm']:g} mm"
                + (f" (enclosure {x['off_display_run_mm']['axis']} {x['off_display_run_mm']['at'][0]:g}-{x['off_display_run_mm']['at'][1]:g})"
                   if x["off_display_run_mm"]["run_mm"] > 0 else "")
                for x in rows if x.get("verdict", "").startswith("FAIL") and "off_display_run_mm" in x]
        parts.append("places outside the display, the longest run of each failing header's exit edge zone clear of the display "
                     f"footprint: {', '.join(runs)} (shared with the other headers of that zone; positions at the PCB-PWRA-3 placement)")
    if tbd:
        parts.append(f"TBD: {', '.join(tbd)}")
    if outside:
        parts.append(f"outside the display footprint: {', '.join(outside)}")
    if fail or tbd:
        res = "OPEN: " + "; ".join(parts) + "; the header family and orientation are GR's (build/16), the exit edge and position PCB-PWRA-3's"
    else:
        res = "PASS (model): " + "; ".join(parts)
    return dict(rule, value_mm=val, limit_mm=z_lim, headers=rows, result=res)


# Placement fill trigger of PWR-A (pcb/partition-spec.json fallbacks F2 and F2-C: 'courtyard fill ... > 0.60 in placement',
# 'a sourced part or block grows the PWR-A top demand by more than the 90.4 mm2 left below 0.60'); W2 MECH-7 review F1.
FILL_TRIGGER = 0.60


def _off_display_run(enc, edge, disp):
    """Longest run along the edge (mm) of a header edge strip (enclosure x0, y0, x1, y1) that lies outside the display
    footprint (layout display box): where a header of that zone could stand with no channel limit (W2 MECH-7 review F1)."""
    if edge in ("bottom", "top"):
        lo, hi, a0, a1, d_lo, d_hi, e0, e1, axis = enc[0], enc[2], enc[1], enc[3], disp[0], disp[3], disp[1], disp[4], "x"
    else:
        lo, hi, a0, a1, d_lo, d_hi, e0, e1, axis = enc[1], enc[3], enc[0], enc[2], disp[1], disp[4], disp[0], disp[3], "y"
    if a0 >= e1 or a1 <= e0:                                     # the strip lies beside the display across the edge
        return {"run_mm": round(hi - lo, 2), "axis": axis, "at": [round(lo, 2), round(hi, 2)]}
    runs = [(lo, min(hi, d_lo)), (max(lo, d_hi), hi)]
    best = max(runs, key=lambda r: r[1] - r[0])
    if best[1] - best[0] <= 1e-9:
        return {"run_mm": 0.0, "axis": axis, "at": []}
    return {"run_mm": round(best[1] - best[0], 2), "axis": axis, "at": [round(best[0], 2), round(best[1], 2)]}


def _alternative_area_cost(rows, alt_ok):
    """W2 MECH-7 review F1: PWR-A top courtyard area that the passing alternative (MF_ra) adds per failing header, against the
    margin of pcb/partition-budget.json candidates.<chosen> PWR_A below the placement fill trigger (F2-C fires when a sourced
    part grows the demand by more than that margin); the largest header sets that stay within it."""
    from .boards import budget_candidate
    ch, cand = budget_candidate()
    pa = ((cand or {}).get("boards") or {}).get("PWR_A") or {}
    usable, demand = pa.get("usable_mm2"), pa.get("demand_1_mm2")
    delta = {x["connector"]: x["alternative"]["area_delta_mm2"] for x in rows
             if x["connector"] in alt_ok and "area_delta_mm2" in x.get("alternative", {})}
    total = round(sum(delta.values()), 1)
    out = {"alternative_area_delta_mm2": delta, "alternative_area_total_mm2": total, "fill_trigger": FILL_TRIGGER}
    if not delta:
        out["text"] = "the passing alternative has no courtyard area (TBD)"
        return out
    if usable is None or demand is None:
        out["text"] = (f"MF_ra adds {total:g} mm2 of PWR-A top courtyards; the margin below the fill trigger is not computed "
                       "(pcb/partition-budget.json has no PWR_A row)")
        return out
    margin = round(FILL_TRIGGER * usable - demand, 1)
    refs = sorted(delta)
    within = [set(s) for k in range(len(refs), 0, -1) for s in itertools.combinations(refs, k)
              if sum(delta[r] for r in s) <= margin + 1e-9]
    maximal = [sorted(s) for s in within if not any(s < t for t in within)]
    out.update(pwr_a_margin_mm2=margin, budget=f"candidates.{ch} PWR_A usable {usable:g}, demand {demand:g}",
               all_within_margin=total <= margin + 1e-9, largest_sets_within_margin=maximal)
    each = ", ".join(f"{r} {delta[r]:g}" for r in refs)
    head = (f"MF_ra adds PWR-A top courtyard area ({each}; total {total:g} mm2) against the {margin:g} mm2 left below the fill "
            f"trigger {FILL_TRIGGER:.2f} (pcb/partition-budget.json candidates.{ch} PWR_A: {FILL_TRIGGER:.2f} x {usable:g} - {demand:g})")
    if total <= margin + 1e-9:
        out["text"] = head + ": all of them fit the margin"
    else:
        sets = "; ".join("{" + ", ".join(s) + "}" for s in maximal) or "none"
        out["text"] = (head + f": MF_ra on all of them would fire F2-C (pcb/partition-spec.json fallbacks F2-C); the largest sets within "
                       f"the margin: {sets}; the others need a place outside the display or F2-C")
    return out


def pwr_b_exit_rule(P):
    """R-PWRB-EXIT (W2 MECH-7 part 2): room in front of each PWR-B edge zone for its side-entry harness plugs. For every
    zone of boards.json PWR_B edge_zones: the distance from the board edge, outwards, to the nearest layout envelope or
    structure part that overlaps the zone span and the plug height band (PWR-B component face + the side-entry body height
    of the zone's header families, parts.json harness_headers <family>_side h), against the distance the mated housing
    stands proud of the header face (boards.json PWR_B exit_rule plug_proud_mm). W2 MECH-7 review F2: the room is also
    compared with the largest bundle OD of the zone's harness segments (generated harness-routes.json bundle_od_mm): a
    bundle wider than the room cannot turn in front of the edge, so the header face sits at least proud + OD + clearance -
    room inboard and the wires turn over the board; and each segment's leg from the PWR-B edge to its first plate opening
    or panel port is checked with its bundle (centreline + OD/2) against the envelopes, since R-ROUTE-CLEAR checks
    centrelines only. The header set-back from the board edge and the wire bend radius (not read) are placement and
    proof-fit items, so the rule reports (OPEN), never FAIL."""
    import csv
    from pathlib import Path
    b = P.boards["boards"]["PWR_B"]
    ex = b.get("exit_rule") or {}
    rule = {"id": "R-PWRB-EXIT",
            "rule": "PWR-B edge zones: free room in front of the edge in the plug height band against the mated side-entry housing proud of the "
                    "header face plus the bundle OD of the zone's segments; bundle clearance of each segment's leg to its first opening "
                    "(header set-back and wire bend: PCB-PWRB-2 placement, proof-fit)",
            "source": "boards.json PWR_B edge_zones / exit_rule; parts.json harness_headers; build/16-dzhgut-rozyemy.csv (board PWR_B); "
                      "mechanical.json layout, harness_routes; generated/harness-routes.json bundle_od_mm"}
    if not b.get("edge_zones") or not ex:
        return dict(rule, value_mm=None, result="OPEN: boards.json PWR_B has no edge_zones or exit_rule")
    root = Path(__file__).resolve().parents[2]
    legs = _pwr_b_exit_legs(P)
    clr = ex.get("bundle_clearance_mm", 0.0)
    fam_of = {}
    path = root / "build" / "16-dzhgut-rozyemy.csv"
    if path.exists():
        with path.open(encoding="utf-8", newline="") as fh:
            fam_of = {r["connector"]: r["family"] for r in csv.DictReader(fh) if r.get("board") == "PWR_B"}
    hh = P.parts["harness_headers"]
    face = b["place"]["z_bottom"] + P.board_t("PWR_B")       # W2 MECH-8: the 6-layer PWR-B thickness
    ox, oy = b["place"]["origin"]
    xs, ys = [p[0] for p in b["outline"]], [p[1] for p in b["outline"]]
    obstacles = [(name, bx) for iid, name, bx, it in item_boxes(P) if it.get("board") not in ("PWR", "PWR_B") and not it.get("outside")]
    from .layout import structure_boxes
    obstacles += list(structure_boxes(P))
    rows, txt = [], []
    for i, ez in enumerate(b["edge_zones"]):
        fams = sorted({fam_of[h] for h in ez.get("headers", []) if h in fam_of})
        hs = [hh.get(f"{f}_side", {}).get("h") for f in fams]
        band = (face, face + max([h for h in hs if h] or [b["max_height"]]))
        a0, a1 = ez["span"]
        if ez["edge"] in ("bottom", "top"):
            e = oy + (min(ys) if ez["edge"] == "bottom" else ez.get("at", max(ys)))
            lo, hi, ai, ci, sgn = ox + a0, ox + a1, 0, 1, (-1 if ez["edge"] == "bottom" else 1)
        else:
            e = ox + (max(xs) if ez["edge"] == "right" else min(xs))
            lo, hi, ai, ci, sgn = oy + a0, oy + a1, 1, 0, (1 if ez["edge"] == "right" else -1)
        best = None
        for name, bx in obstacles:
            if bx[ai + 3] <= lo + 1e-9 or bx[ai] >= hi - 1e-9 or bx[5] <= band[0] + 1e-9 or bx[2] >= band[1] - 1e-9:
                continue                                         # beside the span or outside the plug height band
            near, far = bx[ci], bx[ci + 3]                       # extent across the edge (y for top/bottom, x for left/right)
            gap = (near - e) if sgn > 0 else (e - far)
            if (sgn > 0 and far <= e + 1e-9) or (sgn < 0 and near >= e - 1e-9):
                continue                                         # behind the edge (over the board)
            gap = max(gap, 0.0)
            if best is None or gap < best[0]:
                best = (round(gap, 2), name)
        proud = [ex["plug_proud_mm"].get(f) for f in fams]
        p_max = max([p for p in proud if p is not None], default=None)
        zl = {sid: v for sid, v in legs.items() if v["zone"] == i}
        od = max([v["bundle_od_mm"] for v in zl.values()], default=None)
        od_seg = [sid for sid, v in zl.items() if v["bundle_od_mm"] == od]
        row = {"zone": i, "edge": ez["edge"], "span": ez["span"], "headers": ez.get("headers", []), "families": fams, "band_z": [round(v, 2) for v in band],
               "room_mm": None if best is None else best[0], "nearest": None if best is None else best[1], "plug_proud_mm": p_max,
               "plug_proud_tbd": [f for f, p in zip(fams, proud) if p is None], "segments": sorted(zl),
               "bundle_od_max_mm": od, "bundle_clearance_mm": clr,
               "legs": {sid: {k: v[k] for k in ("bundle_od_mm", "pieces", "clear_mm", "nearest")} for sid, v in sorted(zl.items())}}
        if best is None:
            row["verdict"] = "no envelope in front of the edge in the band"
        elif p_max is None:
            row["verdict"] = f"room {best[0]:g} mm to {best[1]}; housing proud TBD ({', '.join(fams) or 'no header'})"
        else:
            need = p_max + (od or 0.0) + (clr if od else 0.0)
            row["set_back_min_mm"] = round(max(need - best[0], 0.0), 2)
            what = f"housing proud {p_max:g}" + (f" + bundle OD {od:g} ({', '.join(od_seg)}) + clearance {clr:g}" if od else "")
            if best[0] >= need - 1e-9:
                row["verdict"] = f"room {best[0]:g} mm to {best[1]} >= {what}: header face at the edge; the wire bend radius (TBD) needs the rest"
            else:
                row["verdict"] = (f"room {best[0]:g} mm to {best[1]} < {what} = {need:g}"
                                  + (f" (bundle OD {od:g} > room {best[0]:g}: the bundle cannot turn in front of the edge)" if od and od > best[0] else "")
                                  + f": the header face sits >= {row['set_back_min_mm']:g} mm inboard of the board edge and the wires turn over the board "
                                  "(bend radius TBD)")
        if row["plug_proud_tbd"] and p_max is not None:
            row["verdict"] += f"; housing proud of {', '.join(row['plug_proud_tbd'])} TBD"
        if zl:
            bad = [f"{sid} reaches {-v['clear_mm']:g} into {v['nearest']}" for sid, v in sorted(zl.items())
                   if v["clear_mm"] is not None and v["clear_mm"] < -1e-9]
            ok = [f"{sid} {v['clear_mm']:g}" for sid, v in sorted(zl.items()) if v["clear_mm"] is not None and v["clear_mm"] >= -1e-9]
            row["verdict"] += ("; leg to the first opening, bundle (centreline + OD/2) against the envelopes: "
                               + "; ".join(([", ".join(bad)] if bad else []) + ([f"clear: {', '.join(ok)} mm"] if ok else [])))
        rows.append(row)
        txt.append(f"zone {i} ({ez['edge']} {a0:g}-{a1:g}, {', '.join(ez.get('headers', [])) or 'no header'}): {row['verdict']}")
    return dict(rule, value_mm={"zones": rows}, limit_mm=ex["plug_proud_mm"],
                result="OPEN: " + "; ".join(txt) + f"; {ex.get('gate', 'header set-back and wire bend at the PCB-PWRB-2 placement and proof-fit')}")


def _pwr_b_exit_legs(P):
    """W2 MECH-7 review F2: for every harness segment with an end on a PWR-B edge zone, its bundle OD and the bundle clearance
    of its leg (the pieces from the PWR-B end to its first plate slot, notch, window or panel port, else the whole route)
    against every envelope and structure part except the envelopes of its own ends and its 'touch' list. Pieces are taken as
    their bounding boxes (exact for the axis-parallel pieces of these routes)."""
    from . import routes
    from .layout import gap
    res = routes.evaluate(P)
    if res is None:
        return {}
    named = routes.boxes(P)
    out = {}
    for sid, spec in P.mech["harness_routes"]["segments"].items():
        via = spec.get("via") or []
        r = res["segments"].get(sid, {})
        pts = r.get("points_mm") or []
        if not via or len(pts) != len(via):
            continue
        ends = [k for k in (0, len(via) - 1) if "edge" in via[k] and via[k]["edge"] == "PWR_B"]
        if not ends:
            continue
        seq = list(range(len(via))) if ends[0] == 0 else list(range(len(via)))[::-1]
        leg = [seq[0]]
        for k in seq[1:]:
            leg.append(k)
            if any(key in via[k] for key in ("slot", "notch", "window", "port")):
                break
        exempt = routes._end_boxes(P, via[0], named) | routes._end_boxes(P, via[-1], named) | set(spec.get("touch", []))
        rad = (r.get("bundle_od_mm") or 0.0) / 2
        worst = None
        for a, b in zip(leg, leg[1:]):
            pa, pb = pts[a], pts[b]
            piece = tuple(min(pa[i], pb[i]) for i in range(3)) + tuple(max(pa[i], pb[i]) for i in range(3))
            for name, (iid, bx, it) in named.items():
                if name in exempt or iid in exempt or it.get("outside") or tuple(bx[:3]) == tuple(bx[3:]):
                    continue
                d = max(gap(piece, bx), 0.0) - rad
                if worst is None or d < worst[0] - 1e-9:
                    worst = (d, name)
        out[sid] = {"zone": via[ends[0]]["zone"], "bundle_od_mm": r.get("bundle_od_mm"), "pieces": len(leg) - 1,
                    "clear_mm": None if worst is None else round(worst[0], 2), "nearest": None if worst is None else worst[1]}
    return out


def w2_mech7_rules(P):
    """Rows added by W2 MECH-7 (registration list, append-only)."""
    return [pwr_zones_rule(P), pwr_bottom_rule(P), h_trim_rule(P), mated_height_rule(P), pwr_b_exit_rule(P)]


def pwr_stack_rule(P):
    """R-PWR-STACK (W2 MECH-8): the mated PWR-A/PWR-B stack with the 6-layer boards (boards.json PWR / PWR_B stackup, t
    1.664 mm MODEL). The PWR-B bottom face must follow PWR-A bottom + PWR-A thickness + B2B stack (boards.json PWR_B b2b.stack
    = pcb/partition-spec.json parameters.stack), and the PWR-B part envelope (PWR-B top face + hB) must stay under the path-2
    channel floor (display module back - air_channel). The margin is computed at the board thicknesses of the contract and
    over the order band order_t +/- order_tol of each board (the B2B stack fixes the gap, so PWR-B follows PWR-A). FAIL
    (model) when the placement does not follow the stack, the two stack values differ or the margin is negative anywhere
    in the band; else PASS (model): the finished thickness is TBD at order and the stack is a proof-fit gate (OPEN)."""
    import json
    from pathlib import Path
    B = P.boards["boards"]
    a, b = B["PWR"], B["PWR_B"]
    sz = P.mech["stack_z"]
    ta, tb = P.board_t("PWR"), P.board_t("PWR_B")
    stack = b["b2b"]["stack"]
    hB = b["max_height"]
    za, zb = a["place"]["z_bottom"], b["place"]["z_bottom"]
    floor, need = _channel_floor(P)
    p = Path(__file__).resolve().parents[2] / "pcb" / "partition-spec.json"
    spec = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    par, env = spec.get("parameters", {}), spec.get("envelope", {})
    rule = {"id": "R-PWR-STACK",
            "rule": "mated PWR-A/PWR-B stack (W2 MECH-8, 6-layer boards): PWR-B bottom = PWR-A bottom + t(PWR) + B2B stack, and "
                    "PWR-B top + hB <= the path-2 channel floor (module back - air_channel), at the contract thickness and over "
                    "the order band of each board",
            "source": "boards.json PWR / PWR_B place, stackup (t, order_t, order_tol), max_height, b2b.stack; mechanical.json stack_z; "
                      "pcb/partition-spec.json parameters.stack, envelope (air_channel, pwr_top_z, display_z, dz)"}

    def r3(v):
        return round(v, 3)

    def top(t_a, t_b):
        return za + t_a + stack + t_b + hB

    def band(bd):
        st = bd.get("stackup") or {}
        if "order_t" not in st:
            return None
        return (r3(st["order_t"] * (1 - st["order_tol"])), r3(st["order_t"] * (1 + st["order_tol"])))
    ba, bb = band(a), band(b)
    margin = r3(floor - top(ta, tb))
    t0 = P.boards["stackup"]["t"]
    val = {"plate_front_z": sz["plate_front"], "bond_gap_mm": r3(za - sz["plate_front"]),
           "pwr_a": {"t_mm": ta, "layers": (a.get("stackup") or P.boards["stackup"])["layers"], "bottom_z": za, "top_z": r3(za + ta)},
           "b2b_stack_mm": stack, "partition_spec_stack_mm": par.get("stack"),
           "pwr_b": {"t_mm": tb, "layers": (b.get("stackup") or P.boards["stackup"])["layers"], "bottom_z": zb,
                     "bottom_z_from_stack": r3(za + ta + stack), "top_z": r3(zb + tb), "parts_top_z": r3(zb + tb + hB)},
           "stack_height_from_plate_mm": r3(zb + tb + hB - sz["plate_front"]),
           "channel_floor_z": floor, "air_channel_mm": need, "channel_to_module_back_mm": r3(sz["module_back"] - (zb + tb + hB)),
           "margin_mm": margin, "margin_with_shared_t_mm": r3(floor - top(t0, t0)), "shared_t_mm": t0}
    worst = margin
    if ba and bb:
        lo, hi = r3(floor - top(ba[1], bb[1])), r3(floor - top(ba[0], bb[0]))
        val["order_band_mm"] = {"PWR": list(ba), "PWR_B": list(bb), "margin_min_mm": lo, "margin_max_mm": hi}
        worst = min(worst, lo)
    if env.get("display_z") is not None and env.get("air_channel") is not None:
        dzm = r3(za + ta + stack + tb + hB + env["air_channel"] - env["display_z"])
        val["dz_mezz_mm"] = {"at_contract_t": dzm, "partition_spec_recorded": env.get("dz_mezz"), "partition_spec_dz": env.get("dz"),
                             "dz_unchanged": env.get("dz") is not None and dzm <= env["dz"] + 1e-9}
    pem = P.parts.get(a.get("plate_fastener", ""), {})
    if "shank" in pem:
        pt, shim = P.mech["plate"]["t"], P.mech["pwr_bond"]["shim"]

        def stud(t):
            return [r3(t + shim + pem["shank"]), r3(t + shim + pt)]
        val["pwr_a_stud_window_mm"] = {"at_contract_t": stud(ta)}
        if ba:
            common = [stud(ba[1])[0], stud(ba[0])[1]]
            val["pwr_a_stud_window_mm"].update({"at_band_ends": [stud(ba[0]), stud(ba[1])],
                                                "common_over_band": common if common[0] <= common[1] else None})
    bad = []
    if abs(zb - (za + ta + stack)) > 1e-6:
        bad.append(f"PWR-B bottom {zb:g} != PWR-A {za:g} + {ta:g} + stack {stack:g} = {za + ta + stack:g}")
    if par.get("stack") is not None and abs(par["stack"] - stack) > 1e-9:
        bad.append(f"b2b.stack {stack:g} differs from pcb/partition-spec.json parameters.stack {par['stack']:g}")
    if worst < -1e-9:
        bad.append(f"PWR-B parts above the channel floor: margin {worst:g} mm")
    if bad:
        return dict(rule, value_mm=val, limit_mm=0.0, result="FAIL (model): " + "; ".join(bad))
    txt = (f"PASS (model): PWR-A {za:g} + {ta:g} + B2B {stack:g} = PWR-B {zb:g}; PWR-B parts top {val['pwr_b']['parts_top_z']:g} "
           f"under the channel floor {floor:g}: margin {margin:g} mm ({val['margin_with_shared_t_mm']:g} with {t0:g} mm boards)")
    if "order_band_mm" in val:
        ob = val["order_band_mm"]
        txt += (f"; over the order band {ob['PWR'][0]:g}-{ob['PWR'][1]:g} mm of both boards the margin is "
                f"{ob['margin_min_mm']:g}-{ob['margin_max_mm']:g} mm")
    txt += "; finished thickness TBD at order, mated stack a proof-fit gate (OPEN)"
    return dict(rule, value_mm=val, limit_mm=0.0, result=txt)


def w2_mech8_rules(P):
    """Rows added by W2 MECH-8 (registration list, append-only)."""
    return [pwr_stack_rule(P)]
