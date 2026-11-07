"""Panel features shared by the 3D model and the 2D drawings.

Each face has its own (u, v) system as seen from OUTSIDE the enclosure:
  front: u = x,     v = y      rear (from behind): u = W - x, v = y
  top (from above, front face down): u = x, v = D - z
  bottom (from below, front face up): u = x, v = z
  left (from the left, front face right): u = z, v = y
  right (from the right, front face left): u = D - z, v = y
"""

# Hole specifications by connector kind. d = finished hole; 'basis' says where it comes from.
# shape: round (default) or dflat (a circle d with one flat, 'flat' = width across the flat, flat on the +v side of the face).
HOLES = {
    "sma_pigtail": {"d": 6.5, "basis": "Taoglas MHF1-SMA(F) BK waterproof (CAB.0243/01028/01029, READS-RF row): 1/4-36UNS-2A, no D-cut drawn; 6.5 = catalogue hole of its 1/4-36 bulkheads"},
    "sma_k": {"d": 6.4, "basis": "Taoglas CAB.011 (P7, W407): D-cut thread, hole and thread length not read (MECH-6, B-06); 1/4-36 clearance (TBD)"},
    "sma_cab01075": {"d": 6.5, "basis": "Taoglas CAB.01075 SMA(F) BK (catalogue p.14, READS-RF row): 1/4-36UNS-2A, threaded 11.4, no D-cut drawn"},
    "sma_adamtech": {"d": 6.5, "basis": "Adam Tech CA-DKCA1-305L5-APAJ drawing 11/16/18: 1/4-36UNS jack, washer ID 6.5, no D-cut drawn"},
    "sma_cab718": {"d": 6.5, "shape": "dflat", "flat": 6.0,
                   "basis": "Taoglas CAB.718 SPE-12-8-100 (READS-RF row): recommended mounting hole D6.5 with one flat at 6 +0.08/0, 1/4-36UNS-2A"},
    "f_bulkhead": {"d": 9.7, "basis": "Cinch VFA340 ISS 3: 3/8-32 UNEF, washer ID 9.7, no D-flat drawn; flange outside, nut inside"},
    "bnc_bulkhead": {"d": 9.7, "basis": "Amphenol RF 242181: drawing not readable (403, 2026-11-07); 3/8-32 typical, TBD (MECH-07)"},
    "m8_panel": {"d": 10.1, "flange_d": 12.7,
                 "basis": "binder 76 6618 1111 00003-0200 data sheet p.3 (READS-E row): M10x0.75 bore 10.1 (cut-out proposal 2, plain bore), wall 2.0-6.5, 1 Nm; SW 11 nut outside (12.7 across corners)"},
    "gx12": {"d": 12.0, "shape": "dflat", "flat": 11.2, "flange_d": 15.0,
             "basis": "Kinghelm KH-GX12-6P drawing rev A (READS-E row): hole D12.00 with one flat at 11.20, flange D15 outside, nut D14.6 inside"},
    "jack_3v5": {"d": 10.9, "shape": "dflat", "flat": 9.8, "flange_d": 13.5,
                 "basis": "Tensility 10-06000 rev A: recommended cut-out D10.9 with a flat at 9.8, panel 1.5-4, flange D13.5 outside"},
    "sma_bulkhead_pod": {"d": 6.47, "shape": "dflat", "flat": 5.94,
                         "basis": "Fairview SM4955 REV 2.0 (reference drawing): mounting hole D6.47 with a flat at 5.94, panel <= 6.35"},
    "m12_vent": {"d": 12.2, "basis": "M12x1.5 clearance (design); Amphenol LTW VENT-PS1YBK-O8002"},
    "m12_vent_threaded": {"d": 10.5, "basis": "Amphenol LTW vent in a threaded hole (pad >= 4.0 mm, no nut): tap drill 10.5, tap M12x1.5"},
    "m12_gland": {"d": 12.2, "basis": "M12x1.5 clearance (design); LAPP SKINTOP ST-M 12x1.5 53111400, clamping 3.5-7.0 mm, locknut separate"},
    "gx16": {"d": 16.0, "basis": "STACK D15 / Olimex GX16-4 dimension picture: M16x1 socket, 16 mm hole (not 12), hex nut 18.8"},
    "pec11r": {"d": 7.3, "basis": "M7x0.75 bushing (Bourns PEC11R datasheet), 0.3 clearance (design)"},
    "pv6": {"d": 16.1, "basis": "E-Switch PV6 datasheet 8.28.2025: panel cut-out 16.00 +0.20/-0.00 (drill 16.0, ream to 16.1), panel 1-10 mm"},
    "tbd": {"d": 3.0, "basis": "pilot only: part unread or not placed ('_tbd_reason' in mechanical.json); final cut-out from the chosen part's drawing"},
    "pilot": {"d": 3.0, "basis": "pilot only: SKU TBD"},
}


def hole_outline(f, n=24):
    """Outline of a dflat hole in face (u, v) coordinates: arc on the -v side, chord on the +v side."""
    import math
    r = f["d"] / 2.0
    c = f["flat"] - r                     # chord distance from the centre on the +v side
    a = math.asin(max(-1.0, min(1.0, c / r)))
    a0, a1 = a, math.pi - a               # chord ends; the arc runs the long way round through -v
    pts = []
    for i in range(n + 1):
        t = a1 + (2 * math.pi - (a1 - a0)) * i / n
        pts.append((f["u"] + r * math.cos(t), f["v"] + r * math.sin(t)))
    return pts


def face_features(P):
    """Dict face -> list of features {id, kind, u, v, d | w,h, note}."""
    m = P.mech
    W, H, D = P.outer
    F = {k: [] for k in ("front", "rear", "top", "bottom", "left", "right")}
    # front
    g = m["display"]["glass_pocket"]
    act = P.parts["display_module"]["active"]
    mg = m["display"]["window_margin"]
    cx, cy = g[0] + g[2] / 2.0, g[1] + g[3] / 2.0
    F["front"].append({"id": "WINDOW", "kind": "window", "u": cx, "v": cy, "w": act[0] + 2 * mg, "h": act[1] + 2 * mg,
                       "r": m["display"]["window_r"], "note": "display window = active area 155.82 x 87.83 + margin"})
    for name, e in m["hmi"]["encoders"].items():
        F["front"].append({"id": f"ENC_{name.upper()}", "kind": "pec11r", "u": e["c"][0], "v": e["c"][1], "d": HOLES["pec11r"]["d"],
                           "boss_d": m["hmi"]["encoder_boss"]["boss_d"]})
    b = m["hmi"]["buttons"]
    for r, yv in enumerate(b["rows_y"]):
        for c, xv in enumerate(b["cols_x"]):
            F["front"].append({"id": f"KEY_{b['labels'][r][c]}", "kind": "button", "u": xv, "v": yv, "d": b["hole_d"]})
    for k, s in m["front_face_small"].items():
        F["front"].append({"id": k.upper(), "kind": "pilot", "u": s["c"][0], "v": s["c"][1], "d": s["pilot_d"]})
    # top
    tz = m["top_face"]["ports_z"]
    for p in m["top_face"]["ports"]:
        F["top"].append(dict(hole(p["kind"]), id=p["id"], kind=p["kind"], u=p["x"], v=D - tz))
    pk = m["top_face"]["power_key"]
    F["top"].append({"id": pk["id"], "kind": pk["kind"], "u": pk["x"], "v": D - pk["z"], "d": HOLES[pk["kind"]]["d"]})
    vw = m["top_face"]["veml7700_window"]
    F["top"].append({"id": "VEML7700", "kind": "window_round", "u": vw["x"], "v": D - vw["z"], "d": vw["d"]})
    # right
    for p in m["right_face"]["ports"] + m["right_face"].get("panel", []):
        F["right"].append(dict(hole(p["kind"]), id=p["id"], kind=p["kind"], u=D - p["z"], v=p["y"]))
    # vents (any face; enclosure coordinates in the params)
    for v in m["vents"]:
        u, vv = face_uv(P, v["face"], v.get("x", 0.0), v.get("y", 0.0), v.get("z", 0.0))
        F[v["face"]].append({"id": v["id"], "kind": v["kind"], "u": u, "v": vv, "d": HOLES[v["kind"]]["d"], "pad_t": v["pad_t"]})
    # left
    ex = m["left_face"]["exhaust"]
    F["left"].append({"id": "EXHAUST_P2", "kind": "grille", "u": (ex["z"][0] + ex["z"][1]) / 2, "v": (ex["y"][0] + ex["y"][1]) / 2,
                      "w": ex["z"][1] - ex["z"][0], "h": ex["y"][1] - ex["y"][0], "slot_w": ex["slot_w"], "slot_pitch": ex["slot_pitch"], "slots_along": "u"})
    # bottom: a port keeps the 'tbd' pilot and reserve until its part is read and placed ('_tbd_reason')
    for p in m["bottom_face"]["ports"]:
        if p["kind"] == "tbd":
            F["bottom"].append({"id": p["id"], "kind": "tbd", "u": p["x"], "v": p["z"], "d": HOLES["tbd"]["d"], "w": p["w"], "h": p["h"],
                                "note": p.get("_tbd_reason", p.get("_note", ""))})
        else:
            F["bottom"].append(dict(hole(p["kind"]), id=p["id"], kind=p["kind"], u=p["x"], v=p["z"]))
    it = m["bottom_face"]["intake"]
    F["bottom"].append({"id": "INTAKE_P2", "kind": "grille", "u": (it["x"][0] + it["x"][1]) / 2, "v": (it["z"][0] + it["z"][1]) / 2,
                        "w": it["x"][1] - it["x"][0], "h": it["z"][1] - it["z"][0], "slot_w": it["slot_w"], "slot_pitch": it["slot_pitch"], "slots_along": "v"})
    # rear (u = W - x)
    rf = m["rear_face"]
    g = rf["gx16"]
    F["rear"].append({"id": "GX16_IMU", "kind": "gx16", "u": W - g["c"][0], "v": g["c"][1], "d": HOLES["gx16"]["d"], "pad_t": g["pad_t"]})
    tp = rf["tripod"]
    F["rear"].append({"id": "TRIPOD_1/4-20", "kind": "tripod", "u": W - tp["c"][0], "v": tp["c"][1], "d": tp["hole_d"],
                      "plinth_d": tp["plinth_d"], "disc_d": tp["plate_disc_d"], "note": f"plinth {tp['plinth_h']} mm proud"})
    hx, hy, hw, hh = rf["hatch"]["rect"]
    F["rear"].append({"id": "HATCH", "kind": "hatch", "u": W - (hx + hw / 2), "v": hy + hh / 2, "w": hw, "h": hh, "r": rf["hatch"]["r"]})
    for i, (sx, sy) in enumerate(rf["hatch"]["screws"]):
        F["rear"].append({"id": f"HATCH_M3_{i + 1}", "kind": "insert_m3", "u": W - sx, "v": sy, "d": 4.0})
    for key, fid in (("path1_intake", "INTAKE_P1"), ("path1_exhaust", "EXHAUST_P1")):
        x, y, w, h = rf[key]["rect"]
        F["rear"].append({"id": fid, "kind": "grille", "u": W - (x + w / 2), "v": y + h / 2, "w": w, "h": h,
                          "slot_w": rf[key]["slot_w"], "slot_pitch": rf[key]["slot_pitch"], "slots_along": "u"})
    tg = rf["t7_gland"]
    F["rear"].append({"id": "T7_GLAND", "kind": "tbd", "u": W - tg["c"][0], "v": tg["c"][1], "d": HOLES["tbd"]["d"], "w": tg["w"], "h": tg["h"],
                      "note": tg.get("_tbd_reason", "gland for the T7 lead, MPN TBD (STACK 5.8)")})
    ss = rf["strap_slots"]
    for i, y in enumerate(ss["y"]):
        F["rear"].append({"id": f"STRAP_SLOT_{i + 1}", "kind": "strap", "u": W - ss["x"], "v": y, "w": 18.0, "h": ss["w"] + 8.0,
                          "pw": 22.0, "ph": ss["w"], "note": "tunnel for SmallRig PAC2456, printed with the rear shell (6 mm proud)"})
    lg = rf["strap_lug"]
    for i, (lx, ly) in enumerate(rf["strap_lugs"]):
        F["rear"].append({"id": f"LUG_{i + 1}", "kind": "strap", "u": W - lx, "v": ly, "w": lg["w"], "h": lg["h"], "pw": 16.0, "ph": 5.0,
                          "note": f"neck-strap lug (Peak Design Leash), solid {lg['w']:g} x {lg['h']:g}, {lg['proud']:g} proud, printed with the rear shell"})
    th = rf["t7_holder"]
    for i, (px, py) in enumerate(th["screws"]):
        F["rear"].append({"id": f"T7_PAD_{i + 1}", "kind": "pad", "u": W - px, "v": py, "d": th["pad_d"], "insert_d": 4.0,
                          "note": f"pad {th['pad_h']:g} proud with an M3 insert (T7 holder screw from outside)"})
    c = m["closure"]
    for i, (bx, by) in enumerate(c["bosses"]):
        F["rear"].append({"id": f"CLOSURE_{i + 1}", "kind": "closure", "u": W - bx, "v": by, "d": c["clearance_d"],
                          "cb_d": c["counterbore_d"], "cb_depth": c["counterbore_depth"]})
    return F


def hole(kind):
    """Hole geometry of a connector kind for a feature: d, and shape / flat / flange_d where the drawing gives them."""
    h = HOLES[kind]
    return {k: h[k] for k in ("d", "shape", "flat", "flange_d") if k in h}


def face_uv(P, face, x, y, z):
    """Inverse of to_xyz for a point on the face (the coordinate along the face normal is ignored)."""
    W, H, D = P.outer
    return {"front": (x, y), "rear": (W - x, y), "top": (x, D - z), "bottom": (x, z), "left": (z, y), "right": (D - z, y)}[face]


def to_xyz(P, face, u, v, depth=0.0):
    """Point on a face (outer surface) moved `depth` inwards, in enclosure coordinates."""
    W, H, D = P.outer
    if face == "front":
        return (u, v, D - depth)
    if face == "rear":
        return (W - u, v, depth)
    if face == "top":
        return (u, H - depth, D - v)
    if face == "bottom":
        return (u, depth, v)
    if face == "left":
        return (depth, v, u)
    if face == "right":
        return (W - depth, v, D - u)
    raise ValueError(face)


FACE_NORMAL = {"front": (0, 0, 1), "rear": (0, 0, -1), "top": (0, 1, 0), "bottom": (0, -1, 0), "left": (-1, 0, 0), "right": (1, 0, 0)}
# +v of each face's (u, v) system in enclosure coordinates (see the module docstring)
FACE_V = {"front": (0, 1, 0), "rear": (0, 1, 0), "top": (0, 0, -1), "bottom": (0, 0, 1), "left": (0, 1, 0), "right": (0, 1, 0)}


def face_size(P, face):
    W, H, D = P.outer
    return {"front": (W, H), "rear": (W, H), "top": (W, D), "bottom": (W, D), "left": (D, H), "right": (D, H)}[face]


def seam_geometry(P):
    """Belt and groove offsets, measured inwards from the outer surface of the shells (negative = outside).

    The seam is a face seal: the EPDM cord lies in a groove cut into the split face of the front shell, inside
    an external belt (the wall is thickened outwards at the seam, so nothing intrudes into the interior)."""
    gk = P.mech["gasket"]
    b = gk["belt"]
    centre = gk["land"] + gk["groove_w"] / 2.0 - b
    return {"belt": b, "belt_h": gk["belt_h"], "groove_centre": centre,
            "groove_out": centre - gk["groove_w"] / 2.0, "groove_in": centre + gk["groove_w"] / 2.0}
