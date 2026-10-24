"""Panel features shared by the 3D model and the 2D drawings.

Each face has its own (u, v) system as seen from OUTSIDE the enclosure:
  front: u = x,     v = y      rear (from behind): u = W - x, v = y
  top (from above, front face down): u = x, v = D - z
  bottom (from below, front face up): u = x, v = z
  left (from the left, front face right): u = z, v = y
  right (from the right, front face left): u = D - z, v = y
"""

# Hole specifications by connector kind. d = finished hole; 'basis' says where it comes from.
HOLES = {
    "sma_pigtail": {"d": 6.4, "basis": "1/4-36 UNS bulkhead, STACK 5.8 'близько 6.4 з лискою'; D-flat per received part (TBD)"},
    "sma_k": {"d": 6.4, "basis": "SMA-K through bulkhead, 1/4-36 assumed; check the received part (TBD)"},
    "sma_cab01075": {"d": 6.4, "basis": "Taoglas CAB.01075 SMA(f) bulkhead, 1/4-36 assumed; datasheet not readable (403), check the part (TBD)"},
    "f_bulkhead": {"d": 9.7, "basis": "F-type 3/8-32 UNEF thread (IEC 61169-24), 9.525 + clearance; check the chosen F-F bulkhead (TBD)"},
    "bnc_bulkhead": {"d": 9.7, "basis": "BNC bulkhead 3/8-32 UNEF typical, D-flat per part; MPN TBD (MECH-07)"},
    "m12_vent": {"d": 12.2, "basis": "M12x1.5 clearance (design); Amphenol LTW VENT-PS1YBK-O8002"},
    "m12_gland": {"d": 12.2, "basis": "M12x1.5 clearance (design)"},
    "gx16": {"d": 16.0, "basis": "STACK D15: Olimex GX16-4 needs a 16 mm hole (not 12)"},
    "pec11r": {"d": 7.3, "basis": "M7x0.75 bushing (Bourns PEC11R datasheet), 0.3 clearance (design)"},
    "tbd": {"d": 3.0, "basis": "pilot only: connector MPN not chosen (MECH-07); final cut-out from the chosen part's drawing"},
    "pilot": {"d": 3.0, "basis": "pilot only: SKU TBD"},
}


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
        F["top"].append({"id": p["id"], "kind": p["kind"], "u": p["x"], "v": D - tz, "d": HOLES[p["kind"]]["d"]})
    vw = m["top_face"]["veml7700_window"]
    F["top"].append({"id": "VEML7700", "kind": "window_round", "u": vw["x"], "v": D - vw["z"], "d": vw["d"]})
    # right
    for p in m["right_face"]["ports"]:
        F["right"].append({"id": p["id"], "kind": p["kind"], "u": D - p["z"], "v": p["y"], "d": HOLES[p["kind"]]["d"]})
    # left
    for v in m["left_face"]["vents"]:
        F["left"].append({"id": v["id"], "kind": v["kind"], "u": v["z"], "v": v["y"], "d": HOLES[v["kind"]]["d"], "pad_t": v["pad_t"]})
    ex = m["left_face"]["exhaust"]
    F["left"].append({"id": "EXHAUST_P2", "kind": "grille", "u": (ex["z"][0] + ex["z"][1]) / 2, "v": (ex["y"][0] + ex["y"][1]) / 2,
                      "w": ex["z"][1] - ex["z"][0], "h": ex["y"][1] - ex["y"][0], "slot_w": ex["slot_w"], "slot_pitch": ex["slot_pitch"], "slots_along": "u"})
    # bottom
    for p in m["bottom_face"]["ports"]:
        F["bottom"].append({"id": p["id"], "kind": "tbd", "u": p["x"], "v": p["z"], "d": HOLES["tbd"]["d"], "w": p["w"], "h": p["h"], "note": p["_note"]})
    it = m["bottom_face"]["intake"]
    F["bottom"].append({"id": "INTAKE_P2", "kind": "grille", "u": (it["x"][0] + it["x"][1]) / 2, "v": (it["z"][0] + it["z"][1]) / 2,
                        "w": it["x"][1] - it["x"][0], "h": it["z"][1] - it["z"][0], "slot_w": it["slot_w"], "slot_pitch": it["slot_pitch"], "slots_along": "v"})
    # rear (u = W - x)
    rf = m["rear_face"]
    g = rf["gx16"]
    F["rear"].append({"id": "GX16_IMU", "kind": "gx16", "u": W - g["c"][0], "v": g["c"][1], "d": HOLES["gx16"]["d"], "pad_t": g["pad_t"]})
    tp = rf["tripod"]
    F["rear"].append({"id": "TRIPOD_1/4-20", "kind": "tripod", "u": W - tp["c"][0], "v": tp["c"][1], "d": tp["hole_d"]})
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
                      "note": "gland for the T7 lead, MPN TBD (STACK 5.8)"})
    c = m["closure"]
    for i, (bx, by) in enumerate(c["bosses"]):
        F["rear"].append({"id": f"CLOSURE_{i + 1}", "kind": "closure", "u": W - bx, "v": by, "d": c["clearance_d"],
                          "cb_d": c["counterbore_d"], "cb_depth": c["counterbore_depth"]})
    return F


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


def face_size(P, face):
    W, H, D = P.outer
    return {"front": (W, H), "rear": (W, H), "top": (W, D), "bottom": (W, D), "left": (D, H), "right": (D, H)}[face]
