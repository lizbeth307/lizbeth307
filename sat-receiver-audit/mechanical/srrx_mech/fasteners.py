"""Fastener stacks per screw joint (W2 MECH-3, written to generated/fastener-stacks.json).

For every screwed joint of the enclosure model: the head seat, the clamped stack, the grip (seat to the start of the
receiving thread), the receiving thread (insert, PEM nut or standoff, tapped boss), what limits the screw tip, and the
window of under-head screw lengths that gives the minimum engagement without hitting the tip limit. SRC-2 (C-13/C-14)
maps each window to an orderable ISO length. MODEL GEOMETRY ONLY: no screw was fitted; insert and standoff thread
depths that no read source gives stay TBD and the joint is OPEN.
"""

ENG_METAL = 1.0    # x d: minimum engagement in a metal internal thread (standoff, tapped Al) - design rule of this package
ENG_INSERT = 1.5   # x d: minimum engagement in a CNC Kitchen heat-set insert in ASA - design rule of this package
TIP_GAP = 0.5      # left between the screw tip and a blind-hole bottom, a pad face or another screw (design rule)


def _joint(jid, row, what, count, thread, d, seat, stack, receiver, recv_len, tip_room, min_eng, tip_limit, note="", tbd=None):
    grip = round(sum(t for _, t in stack), 2)
    out = {"id": jid, "build17_row": row, "what": what, "count": count, "thread": thread, "seat": seat,
           "stack_mm": [[k, round(t, 2)] for k, t in stack], "grip_mm": grip,
           "receiver": {"kind": receiver, "thread_mm": recv_len, "tip_limit": tip_limit},
           "min_engagement_mm": round(min_eng, 2)}
    if tbd or recv_len is None:
        out["length_window_mm"] = None
        out["result"] = "OPEN: " + (tbd or "receiving thread not read")
    else:
        lo = round(grip + min_eng, 2)
        hi = round(grip + recv_len + tip_room, 2)
        out["length_window_mm"] = [lo, hi]
        out["max_engagement_mm"] = round(hi - grip, 2)
        out["result"] = (f"PASS (model): under-head length {lo:g}-{hi:g} mm" if lo <= hi + 1e-9 else
                         f"FAIL (model): needs {lo:g} mm for {min_eng:g} mm engagement, the tip limit allows {hi:g}")
    if note:
        out["note"] = note
    return out


def stacks(P):
    m = P.mech
    B = P.boards["boards"]
    t_pcb = P.boards["stackup"]["t"]
    sz = m["stack_z"]
    pl = m["plate"]
    c = m["closure"]
    ins = c["insert"]
    zs = m["split_z"]
    J = []
    # closure: rear-shell counterbore to the insert in the front-shell boss (blind hole = insert + 0.8)
    J.append(_joint("CLOSURE", "F12", "half shells, 14 seam screws", len(c["bosses"]), "M3", 3.0,
                    f"counterbore bottom, z {c['counterbore_depth']:g} (rear shell, counterbore d {c['counterbore_d']:g})",
                    [("rear shell boss from the counterbore to the seam", zs - c["counterbore_depth"])],
                    f"CNC Kitchen TC-M3x{ins['len']:g} insert in the front-shell boss (hole d {ins['hole_d']:g})", ins["len"], 0.8 - TIP_GAP,
                    ENG_INSERT * 3.0, "blind insert hole bottom (insert + 0.8)",
                    "the sealing washer under the head (AI-SEAL-WASHER-M3, thickness TBD) adds its thickness to the grip and to both window ends"))
    # service hatch cover into the rear-wall hatch bosses
    hc = m["gasket"]["groove_depth"] + 2.2
    J.append(_joint("HATCH", "F13", "service-hatch cover", len(m["rear_face"]["hatch"]["screws"]), "M3", 3.0,
                    f"cover outer face, z {-hc:g}", [("hatch cover (groove depth + 2.2)", hc)],
                    f"CNC Kitchen TC-M3x{ins['len']:g} insert in the hatch boss (hole to z 6.5)", ins["len"], 0.8 - TIP_GAP,
                    ENG_INSERT * 3.0, "blind insert hole bottom (insert + 0.8)", "captive screw type TBD (AI-M3-HATCH): its shoulder changes the grip"))
    # T7 holder from outside into the rear-face pads
    th = m["rear_face"]["t7_holder"]
    depth = th["gap"] + P.parts["t7"]["size"][2] + th["shutter_t"]
    J.append(_joint("T7_HOLDER", "F33", "T7 holder rails into the rear-face pads", len(th["screws"]), "M3", 3.0,
                    f"holder outer face, z {-depth:g}", [("holder rail (gap + T7 + shutter) down to the pad face", depth - th["pad_h"])],
                    f"CNC Kitchen TC-M3x{ins['len']:g} insert in the pad (blind, 0.5 skin to the inside)", ins["len"], 0.8 - TIP_GAP,
                    ENG_INSERT * 3.0, "blind insert hole bottom (0.5 mm skin to the enclosure inside)"))
    # plate to the front-shell plate bosses (screw from the rear face of the plate)
    a = m["angles"]["top"]
    W, H, D = P.outer
    t = m["wall"]
    for i, bb in enumerate(pl["mount_bosses"]):
        bx, by = bb["c"]
        under_angle = a["x"][0] <= bx <= a["x"][1] and H - t - a["leg_plate"] <= by <= H - t
        stack = [("plate", pl["t"])] + ([("top Al angle plate leg (needs a clearance hole)", a["t"])] if under_angle else [])
        J.append(_joint(f"PLATE_PM{i + 1}", "F30", f"plate to the front-shell boss PM{i + 1}", 1, "M3", 3.0,
                        f"plate rear face, z {sz['plate_rear']:g}" + (" (on the top Al angle leg)" if under_angle else ""), stack,
                        f"CNC Kitchen TC-M3x{ins['len']:g} insert in the front-shell plate boss (hole to plate front + 6.5)", ins["len"], 0.8 - TIP_GAP,
                        ENG_INSERT * 3.0, "blind insert hole bottom"))
    # Al angles into PEM F-M3-1 flush nuts in the plate
    pem = P.parts[m["angles"]["fastener"]]
    n_ang = len(m["angles"]["top"]["holes_x"]) + len(m["angles"]["right"]["holes_y"])
    J.append(_joint("ANGLES", "F31", "top and right Al angles to the plate (AT1-5, AR1-3)", n_ang, "M3", 3.0,
                    f"angle plate leg rear face, z {sz['plate_rear'] - a['t']:g}", [("Al angle plate leg", a["t"])],
                    "PEM F-M3-1 flush nut in the plate (thread = plate thickness)", pl["t"], 0.0, pl["t"],
                    f"plate front face (flush: IP2368, Lime and HDMI board sit there; {pem['name'].split(' (')[0]})"))
    # PWR-A to the plate through the M3 male studs of the F45 standoffs
    pw = B["PWR"]
    shim = m["pwr_bond"]["shim"]
    pwr_top = pw["place"]["z_bottom"] + t_pcb
    J.append(_joint("PWR_A-PLATE", "F06 / F45", "PWR-A to the plate: male stud of each PWR-A/PWR-B standoff", len(pw["holes"]), "M3", 3.0,
                    f"standoff hex face on the PWR-A top, z {pwr_top:g}", [("PWR-A", t_pcb), ("shim washer (pwr_bond.shim)", shim)],
                    "PEM F-M3-1 flush nut in the plate (thread = plate thickness)", pl["t"], 0.0, pl["t"],
                    "plate rear face: the stud must not stand proud (HF+ can lid and RF board behind the plate)",
                    "the window is the male stud length of the F45 standoff (male-female M3, body 5.0 = the B2B stack): at most 4.0 mm; the MPN with that stud is SRC-2's (C-14)"))
    # PWR-B to the female thread of the standoffs
    pb = B["PWR_B"]
    pwrb_top = pb["place"]["z_bottom"] + t_pcb
    body = pb["place"]["z_bottom"] - pwr_top
    J.append(_joint("PWR_B-STANDOFF", "F46", "PWR-B to the female end of each PWR-A/PWR-B standoff", len(pb["holes"]), "M3", 3.0,
                    f"PWR-B top face, z {pwrb_top:g}", [("PWR-B", t_pcb)],
                    f"female thread of the F45 standoff body {body:g} mm (depth of the part's thread TBD; taken as the body length)", body, -TIP_GAP,
                    ENG_METAL * 3.0, "standoff thread bottom / the male stud root",
                    "head height of an ISO 14580 M3 (2.4 max) stays under hB 5.5 on the PWR-B top"))
    # RF board on PEM SO-M3-3 standoffs
    rf = B["RF"]
    so = P.parts[rf["plate_fastener"]]
    J.append(_joint("RF-STANDOFF", "F07", "RF board to the PEM SO-M3-3 standoffs in the plate", len(rf["holes"]), "M3", 3.0,
                    f"RF component face, z {rf['place']['z_bottom'] - t_pcb:g}", [("RF board", t_pcb)],
                    f"PEM SO-M3-3 thru-threaded standoff, L {so['length']:g} + its head flush in the plate", so["length"] + pl["t"], 0.0,
                    ENG_METAL * 3.0, "plate front face (PWR-A bottom copper 0.4 above it at RF1/RF4)"))
    # CTRL and ENC into the front-shell boss inserts (screw from the board's rear face)
    for jid, bid, row in (("CTRL", "CTRL", "F08"), ("ENC", "ENC", "F29")):
        bd = B[bid]
        n = len(bd["holes"]) * (len(bd.get("place_at", {})) or 1)
        J.append(_joint(jid, row, f"{bid} board to the front-shell bosses", n, "M2.5", 2.5,
                        f"{bid} rear face, z {bd['place']['z_bottom']:g}", [(f"{bid} board", t_pcb)],
                        "CNC Kitchen TC-M2,5x4 insert in the front-shell boss (hole to the board face + 4.5)", 4.0, 0.5 - TIP_GAP,
                        ENG_INSERT * 2.5, "blind insert hole bottom (insert + 0.5)",
                        "the window is narrow: M2.5 x 5 engages 3.4 (1.36 d) and leaves the insert end free; a hole 1 mm deeper would take M2.5 x 6"))
    # Q6A on 6 mm F-F standoffs: screw from the board and from the plate front share the standoff thread
    so6 = m["q6a_mount"]["standoff"]
    J.append(_joint("Q6A-STANDOFF", "F01", "Q6A to the F-F standoffs (component side)", 4, "M2.5", 2.5,
                    "Q6A component face", [("Q6A board", P.parts["q6a"]["board"][2])],
                    f"F-F standoff {so6:g} mm (AI-STANDOFF-M25-6, part not read): thread depth per end TBD", None, 0.0, ENG_METAL * 2.5,
                    "the F02 screw tip from the plate side",
                    f"pair rule with F02: engagement F01 + F02 <= {so6:g} - {TIP_GAP:g} if the standoff is threaded through; STACK's M2.5 x 6 for F01 "
                    f"engages 4.4 and leaves {so6 - TIP_GAP - 4.4:.1f} for F02 (< 1 d): F01 M2.5 x 4 (2.4) with F02 M2.5 x 5 (3.0) fits",
                    "standoff thread depth per end not read (AI-STANDOFF-M25-6 has no MPN)"))
    J.append(_joint("Q6A-PLATE", "F02", "F-F standoffs to the plate (from the plate front face)", 4, "M2.5", 2.5,
                    f"plate front face, z {sz['plate_front']:g}", [("plate", pl["t"])],
                    f"F-F standoff {so6:g} mm, other end (part not read)", None, 0.0, ENG_METAL * 2.5, "the F01 screw tip",
                    "see Q6A-STANDOFF", "standoff thread depth per end not read"))
    # UFS boss: countersunk M2.5 from the plate front into the tapped Al boss
    ub = m["ufs_boss"]
    hb = round(m["q6a_mount"]["standoff"] - ub["module_below_board"] - ub["pad_gap"], 2)
    J.append(_joint("UFS-BOSS", "F32", "UFS boss to the plate (ISO 10642 countersunk from the front face)", 2, "M2.5", 2.5,
                    "countersink in the plate front face", [("plate (countersunk head inside it)", pl["t"])],
                    f"Al boss tapped M2.5 through its height {hb:g}", hb, 0.0, ENG_METAL * 2.5,
                    "boss rear face under the UFS Gelid pad (the tip must not reach the pad)",
                    "ISO 10642 lengths include the head; no standard length falls in the window: M2.5 x 4 engages 2.0 (0.8 d) unless the boss grows"))
    # Lime pedestal from the plate rear into the pedestal thread
    lp = m["lime_pedestal"]
    J.append(_joint("LIME-PEDESTAL", "F04", "Lime pedestal to the plate (screw from the plate rear face)", 2, "M3", 3.0,
                    f"plate rear face, z {sz['plate_rear']:g} (head in the 3.0 mm gap behind the plate, RF board at LP1)", [("plate", pl["t"])],
                    f"Al pedestal tapped M3, height {lp['h']:g} (F04: thread in the pedestal)", lp["h"], -TIP_GAP, ENG_METAL * 3.0,
                    "pedestal front face under the Lime pad",
                    "cad.lime_pedestal draws the two holes as 3.4 clearance holes: the pedestal drawing must call them M3 tapped (tap drill 2.5)"))
    # display clamps (no build/17 row yet)
    dc = m["display"]["clamp"]
    J.append(_joint("DISPLAY-CLAMP", "—", "display clamps into the front-shell clamp bosses", len(m["display"]["clamp_bosses"]), "M2.5", 2.5,
                    f"clamp rear face, z {sz['module_back'] - dc['t']:g}", [("printed clamp", dc["t"])],
                    "CNC Kitchen TC-M2,5x4 insert in the clamp boss (hole to the module back + 4.5)", 4.0, 0.5 - TIP_GAP, ENG_INSERT * 2.5,
                    "blind insert hole bottom", "no build/17 row for the display clamps yet (DOCS): screw and insert to be added there"))
    # IMU pack carrier (inserts in a 3.0 mm printed plate)
    I = P.imu
    hb2 = P.parts["hammond_1550z101"]
    J.append(_joint("IMU-CARRIER", "F35", "IMU carrier to the Hammond 1550Z101 floor (screw from outside)", len(I["carrier"]["screws"]), "M3", 3.0,
                    "box outside floor face", [("Hammond 1550Z101 floor", hb2["floor"])],
                    f"insert hole in the {I['carrier']['t']:g} mm printed carrier (imu_pack.json carrier: M3 x 5.7 insert named)", I["carrier"]["t"], 0.0,
                    ENG_INSERT * 3.0, "carrier top face (board pair and the IMU_CARRIER strip above)", "",
                    "the named M3 x 5.7 insert is longer than the 3.0 mm carrier and the IMU_CARRIER strip shares the screws: bosses >= 6.5 at the two "
                    "screws or a short insert are not designed (imu_pack.json; IMU lineage)"))
    # pod (Hammond 1554U2GY): lid and panel
    hp = P.parts["hammond_1554u2gy"]
    J.append(_joint("POD-LID", "F40", "S-band pod lid (Hammond 1554U2GY)", 4, "Hammond lid screw", None, "lid", [],
                    "Hammond lid inserts", None, 0.0, 0.0, "—", "screws supplied with the enclosure (DigiKey 'Cover Included'); stack set by Hammond",
                    "supplied part: no stack to compute"))
    J.append(_joint("POD-PANEL", "F41", f"steel panel 1554UPL to the pod body (insert pitch {hp.get('panel_inserts_m3')})", 4, "M3", 3.0, "panel", [],
                    "Hammond M3 panel inserts (depth not read)", None, 0.0, ENG_METAL * 3.0, "insert bottom", "",
                    "insert depth and panel thickness at the screws not read (P-01)"))
    # joints whose fixing is not designed yet
    for jid, row, what in (("PWR-BOND", "F26", "BOND-RF and the other CHASSIS bond points (lug + serrated washer)"),
                           ("INA228", "F09", "INA228 5832 on stand-offs on the rear wall (W2 MECH-3 place)"),
                           ("SWM-2813", "F05", "Pololu #2813 on stand-offs on the rear wall (W2 MECH-3 place)"),
                           ("HUB-5997", "F10", "Adafruit 5997 CH334F"), ("IP2368", "F11", "IP2368 board"),
                           ("FAN-NF-A4X10", "F27", "Noctua fan of cooler A"), ("BLOWER", "F28", "Delta BFB0305HA-C"),
                           ("HATCH-BOARD", "F38", "hatch board HATCH"), ("PACK-FUSE", "F39", "F101 carrier PACK_FUSE"),
                           ("POD-MODULES", "F42", "cf2235 / LaNA WB in the pod")):
        J.append(_joint(jid, row, what, None, "TBD", None, "TBD", [], "TBD", None, 0.0, 0.0, "TBD", "",
                        "fixing not designed in the model yet (MECH-4 / MECH-5 / pod lineage): no stack"))
    nut_rows = {"F14": "SMA bulkheads (R-SMA-THREAD)", "F16": "F bulkhead P4 (R-SMA-THREAD)", "F17": "BNC P5 (R-SMA-THREAD OPEN)",
                "F18": "GX16-4 nut", "F19": "GX12 LAB BUS nut", "F20": "PEC11R nuts (R-ENC)", "F21": "PV6 power key nut (R-PWR-KEY-NUT)",
                "F22a": "LTW vents (threaded seats, R-VENT-SEAT)", "F22b": "LTW vents with nuts", "F23": "LAPP gland", "F24": "Hammond 1550Z101 lid",
                "F25": "captive 1/4-20 nut (R-TRIPOD)", "F34": "PV6 EDL key nut", "F36": "IMU board standoffs", "F37": "1/4-20 insert",
                "F43": "pod bulkheads and gland", "F44": "pod vent", "F03": "Armor 7056A kit", "F15": "SMA mating torque"}
    counts = {"PASS": sum(1 for j in J if j["result"].startswith("PASS")), "OPEN": sum(1 for j in J if j["result"].startswith("OPEN")),
              "FAIL": sum(1 for j in J if j["result"].startswith("FAIL"))}
    return {"schema": "srrx-fastener-stacks-v1",
            "status": "MODEL GEOMETRY ONLY: stacks from mechanical/params (mechanical.json, boards.json, imu_pack.json, parts.json); no screw was fitted",
            "generator": "mechanical/srrx_mech/fasteners.py (W2 MECH-3)",
            "rules": {"min_engagement": f"heat-set insert in ASA >= {ENG_INSERT:g} d, metal thread >= {ENG_METAL:g} d, PEM flush nut = its full thread (the plate)",
                      "tip_gap_mm": TIP_GAP, "length": "under-head length (ISO 14580); ISO 10642 includes the head",
                      "use": "SRC-2 (C-13/C-14) maps each window to an orderable length; a window that no stocked length meets keeps the item TBD"},
            "joints": J, "nut_and_kit_rows": nut_rows, "summary": counts}


def rule(P):
    """R-FASTENER-STACKS: every computed window is non-empty; joints with unread threads or undesigned fixings are OPEN."""
    doc = stacks(P)
    fails = [j["id"] for j in doc["joints"] if j["result"].startswith("FAIL")]
    opened = [j["id"] for j in doc["joints"] if j["result"].startswith("OPEN")]
    passed = [j["id"] for j in doc["joints"] if j["result"].startswith("PASS")]
    if fails:
        res = "FAIL (model): " + ", ".join(fails)
    else:
        res = f"OPEN: {', '.join(opened)} (thread depth not read or fixing not designed); PASS (model): {', '.join(passed)}" if opened else "PASS (model)"
    return {"id": "R-FASTENER-STACKS", "rule": "screw joints: under-head length window between the minimum engagement and the tip limit (generated/fastener-stacks.json)",
            "value_mm": {j["id"]: j["length_window_mm"] for j in doc["joints"] if j["length_window_mm"]}, "result": res,
            "source": "mechanical/srrx_mech/fasteners.py; build/17 rows"}
