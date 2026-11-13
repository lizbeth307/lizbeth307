"""Fastener stacks per screw joint (W2 MECH-3, written to generated/fastener-stacks.json).

For every screwed joint of the enclosure model: the head seat, the clamped stack, the grip (seat to the start of the
receiving thread), the receiving thread (insert, PEM nut or standoff, tapped boss), what limits the screw tip, and the
window of under-head screw lengths that gives the minimum engagement without hitting the tip limit. A joint is PASS
(model) only when a length of its named ISO series (mechanical/params/parts.json iso14580_lengths) falls in the window;
a window without such a length, or a joint whose screw or standoff is not chosen yet, is OPEN. SRC-2 (C-13/C-14) orders
the lengths. MODEL GEOMETRY ONLY: no screw was fitted; insert and standoff thread depths that no read source gives stay
TBD and the joint is OPEN.
"""

ENG_METAL = 1.0    # x d: minimum engagement in a metal internal thread (standoff, tapped Al) - design rule of this package
ENG_INSERT = 1.5   # x d: minimum engagement in a CNC Kitchen heat-set insert in ASA - design rule of this package
TIP_GAP = 0.5      # left between the screw tip and a blind-hole bottom, a pad face or another screw (design rule)


def _series(P, size, named=True):
    """ISO 14580 commercial lengths of one thread size (parts.json iso14580_lengths); named = the build/17 row names ISO 14580."""
    s = P.parts["iso14580_lengths"]
    return {"series": "ISO 14580", "size": size, "values": s[size], "named": named}


def _joint(jid, row, what, count, thread, d, seat, stack, receiver, recv_len, tip_room, min_eng, tip_limit, note="", tbd=None,
           lengths=None, pending=None):
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
        fits = [v for v in lengths["values"] if lo - 1e-9 <= v <= hi + 1e-9] if lengths else []
        if lengths:
            out["orderable_lengths"] = {"series": f"{lengths['series']} {lengths['size']}", "named_in_build17": lengths["named"],
                                        "in_window": fits, "src": "mechanical/params/parts.json iso14580_lengths"}
        name = f"{lengths['series']} {lengths['size']}" if lengths else ""
        if lo > hi + 1e-9:
            out["result"] = f"FAIL (model): needs {lo:g} mm for {min_eng:g} mm engagement, the tip limit allows {hi:g}"
        elif lengths and fits and not pending:
            out["result"] = f"PASS (model): under-head length {lo:g}-{hi:g} mm; {name} x {', x '.join(f'{v:g}' for v in fits)} in the window"
        elif lengths and not pending:
            below = [v for v in lengths["values"] if v < lo]
            above = [v for v in lengths["values"] if v > hi]
            near = " and ".join(f"x {v:g}" for v in ([below[-1]] if below else []) + ([above[0]] if above else []))
            out["result"] = f"OPEN: under-head length window {lo:g}-{hi:g} mm holds no {name} length ({near} miss it)"
        else:
            cand = (f"; {name} lengths in the window: " + (", ".join(f"x {v:g}" for v in fits) if fits else "none")) if lengths else ""
            out["result"] = f"OPEN: under-head length window {lo:g}-{hi:g} mm; {pending or 'no length series for this screw'}{cand}"
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
                    "the sealing washer under the head (AI-SEAL-WASHER-M3, thickness TBD) adds its thickness to the grip and to both window ends",
                    lengths=_series(P, "M3")))
    cl = J[-1]
    if cl.get("orderable_lengths", {}).get("in_window"):
        v = max(cl["orderable_lengths"]["in_window"])
        cl["note"] += f"; M3 x {v:g} stays in the window for a washer up to {round(v - cl['length_window_mm'][0], 2):g} mm thick"
    # service hatch cover into the rear-wall hatch bosses
    hc = m["gasket"]["groove_depth"] + 2.2
    J.append(_joint("HATCH", "F13", "service-hatch cover", len(m["rear_face"]["hatch"]["screws"]), "M3", 3.0,
                    f"cover outer face, z {-hc:g}", [("hatch cover (groove depth + 2.2)", hc)],
                    f"CNC Kitchen TC-M3x{ins['len']:g} insert in the hatch boss (hole to z 6.5)", ins["len"], 0.8 - TIP_GAP,
                    ENG_INSERT * 3.0, "blind insert hole bottom (insert + 0.8)", "captive screw type TBD (AI-M3-HATCH): its shoulder changes the grip",
                    pending="captive screw type TBD (F13, AI-M3-HATCH): no length series"))
    # T7 holder from outside into the rear-face pads
    th = m["rear_face"]["t7_holder"]
    depth = th["gap"] + P.parts["t7"]["size"][2] + th["shutter_t"]
    J.append(_joint("T7_HOLDER", "F33", "T7 holder rails into the rear-face pads", len(th["screws"]), "M3", 3.0,
                    f"holder outer face, z {-depth:g}", [("holder rail (gap + T7 + shutter) down to the pad face", depth - th["pad_h"])],
                    f"CNC Kitchen TC-M3x{ins['len']:g} insert in the pad (blind, 0.5 skin to the inside)", ins["len"], 0.8 - TIP_GAP,
                    ENG_INSERT * 3.0, "blind insert hole bottom (0.5 mm skin to the enclosure inside)", lengths=_series(P, "M3")))
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
                        ENG_INSERT * 3.0, "blind insert hole bottom", lengths=_series(P, "M3")))
    # Al angles into PEM F-M3-1 flush nuts in the plate: the nut thread is its shank (parts.json pem_f_m3_1), shorter than the
    # 2.0 plate, so the nut sits flush with the screw-entry face (M-07) and the rest of the hole is a recess to the far face
    pem = P.parts[m["angles"]["fastener"]]
    sh_ = pem["shank"]
    n_ang = len(m["angles"]["top"]["holes_x"]) + len(m["angles"]["right"]["holes_y"])
    J.append(_joint("ANGLES", "F31", "top and right Al angles to the plate (AT1-5, AR1-3)", n_ang, "M3", 3.0,
                    f"angle plate leg rear face, z {sz['plate_rear'] - a['t']:g}", [("Al angle plate leg", a["t"])],
                    f"PEM F-M3-1 flush nut flush with the plate rear face, the angle side (M-07): thread = its shank {sh_:g} "
                    f"in the {pl['t']:g} plate, then a {pl['t'] - sh_:.2f} recess to the front face", sh_, pl["t"] - sh_, sh_,
                    f"plate front face (flush: IP2368, Lime and HDMI board sit there; {pem['name'].split(' (')[0]})", lengths=_series(P, "M3")))
    # PWR-A to the plate through the M3 male studs of the F45 standoffs
    pw = B["PWR"]
    shim = m["pwr_bond"]["shim"]
    t_a = P.board_t("PWR")      # W2 MECH-8: the 6-layer PWR-A thickness (boards.json PWR stackup, MODEL)
    pwr_top = pw["place"]["z_bottom"] + t_a
    J.append(_joint("PWR_A-PLATE", "F06 / F45", "PWR-A to the plate: male stud of each PWR-A/PWR-B standoff", len(pw["holes"]), "M3", 3.0,
                    f"standoff hex face on the PWR-A top, z {pwr_top:g}", [("PWR-A", t_a), ("shim washer (pwr_bond.shim)", shim)],
                    f"PEM F-M3-1 flush nut flush with the plate front face, the PWR-A side (M-07): thread = its shank {sh_:g} "
                    f"in the {pl['t']:g} plate, then a {pl['t'] - sh_:.2f} recess to the rear face", sh_, pl["t"] - sh_, sh_,
                    "plate rear face: the stud must not stand proud (HF+ can lid and RF board behind the plate)",
                    "the window is the male stud length of the F45 standoff (male-female M3, body 5.0 = the B2B stack); the MPN with that stud is SRC-2's (C-14)",
                    pending="F45 standoff not chosen: SRC-2 (C-14) picks a male-female M3 standoff with a stud in this window"))
    # PWR-B to the female thread of the standoffs
    pb = B["PWR_B"]
    t_b = P.board_t("PWR_B")    # W2 MECH-8: the 6-layer PWR-B thickness
    pwrb_top = pb["place"]["z_bottom"] + t_b
    body = pb["place"]["z_bottom"] - pwr_top
    J.append(_joint("PWR_B-STANDOFF", "F46", "PWR-B to the female end of each PWR-A/PWR-B standoff", len(pb["holes"]), "M3", 3.0,
                    f"PWR-B top face, z {pwrb_top:g}", [("PWR-B", t_b)],
                    f"female thread of the F45 standoff body {body:g} mm (depth of the part's thread TBD; taken as the body length)", body, -TIP_GAP,
                    ENG_METAL * 3.0, "standoff thread bottom / the male stud root",
                    f"head height of an ISO 14580 M3 ({P.parts['iso14580_lengths']['k_max']['M3']:g} max) stays under hB 5.5 on the PWR-B top",
                    lengths=_series(P, "M3")))
    # RF board on PEM SO-M3-3 standoffs
    rf = B["RF"]
    so = P.parts[rf["plate_fastener"]]
    J.append(_joint("RF-STANDOFF", "F07", "RF board to the PEM SO-M3-3 standoffs in the plate", len(rf["holes"]), "M3", 3.0,
                    f"RF component face, z {rf['place']['z_bottom'] - t_pcb:g}", [("RF board", t_pcb)],
                    f"PEM SO-M3-3 thru-threaded standoff, L {so['length']:g} + its head flush in the plate", so["length"] + pl["t"], 0.0,
                    ENG_METAL * 3.0, "plate front face (PWR-A bottom copper 0.4 above it at RF1/RF4)", lengths=_series(P, "M3")))
    # CTRL and ENC into the front-shell boss inserts (screw from the board's rear face)
    for jid, bid, row in (("CTRL", "CTRL", "F08"), ("ENC", "ENC", "F29")):
        bd = B[bid]
        n = len(bd["holes"]) * (len(bd.get("place_at", {})) or 1)
        J.append(_joint(jid, row, f"{bid} board to the front-shell bosses", n, "M2.5", 2.5,
                        f"{bid} rear face, z {bd['place']['z_bottom']:g}", [(f"{bid} board", t_pcb)],
                        "CNC Kitchen TC-M2,5x4 insert in the front-shell boss (hole to the board face + 4.5)", 4.0, 0.5 - TIP_GAP,
                        ENG_INSERT * 2.5, "blind insert hole bottom (insert + 0.5)",
                        "the window is narrow: M2.5 x 5 engages 3.4 (1.36 d) and leaves the insert end free; a hole 1 mm deeper would take M2.5 x 6",
                        lengths=_series(P, "M2.5", named=False),
                        pending=f"head type and length TBD in build/17 {row} (M2.5 A2 TX8); deepen the boss hole by 1 mm for M2.5 x 6, or a non-standard length"))
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
                    f"ISO 10642 lengths include the head; a whole-mm length misses the window: M2.5 x 4 engages {4 - pl['t']:g} "
                    f"({(4 - pl['t']) / 2.5:.1f} d), M2.5 x 5 ends {round(5 - pl['t'] - hb, 2):g} past the boss rear face; a taller boss or a "
                    "smaller pad gap widens it",
                    pending="no length table of M2.5 countersunk screws was read (the ISO 10642 page read for this check gives head "
                            "dimensions only: parts.json iso14580_lengths src), so no orderable length is confirmed"))
    # Lime pedestal from the plate rear into the pedestal thread
    lp = m["lime_pedestal"]
    J.append(_joint("LIME-PEDESTAL", "F04", "Lime pedestal to the plate (screw from the plate rear face)", 2, "M3", 3.0,
                    f"plate rear face, z {sz['plate_rear']:g} (head in the 3.0 mm gap behind the plate, RF board at LP1)", [("plate", pl["t"])],
                    f"Al pedestal tapped M3, height {lp['h']:g} (F04: thread in the pedestal)", lp["h"], -TIP_GAP, ENG_METAL * 3.0,
                    "pedestal front face under the Lime pad",
                    "cad.lime_pedestal draws the two holes as 3.4 clearance holes: the pedestal drawing must call them M3 tapped (tap drill 2.5)",
                    lengths=_series(P, "M3", named=False), pending="screw type and length TBD in build/17 F04 (AI-M3-LIME)"))
    # display clamps (no build/17 row yet)
    dc = m["display"]["clamp"]
    J.append(_joint("DISPLAY-CLAMP", "—", "display clamps into the front-shell clamp bosses", len(m["display"]["clamp_bosses"]), "M2.5", 2.5,
                    f"clamp rear face, z {sz['module_back'] - dc['t']:g}", [("printed clamp", dc["t"])],
                    "CNC Kitchen TC-M2,5x4 insert in the clamp boss (hole to the module back + 4.5)", 4.0, 0.5 - TIP_GAP, ENG_INSERT * 2.5,
                    "blind insert hole bottom", "no build/17 row for the display clamps yet (DOCS): screw and insert to be added there",
                    lengths=_series(P, "M2.5", named=False), pending="no build/17 row names the clamp screw yet (DOCS)"))
    # IMU pack carrier (inserts in a 3.0 mm printed plate)
    I = P.imu
    hb2 = P.parts["hammond_1550z101"]
    J.append(_joint("IMU-CARRIER", "F35", "IMU carrier to the Hammond 1550Z101 floor (screw from outside)", len(I["carrier"]["screws"]), "M3", 3.0,
                    "box outside floor face", [("Hammond 1550Z101 floor", hb2["floor"])],
                    f"insert hole in the {I['carrier']['t']:g} mm printed carrier (imu_pack.json carrier: M3 x 5.7 insert named)", I["carrier"]["t"], 0.0,
                    ENG_INSERT * 3.0, "carrier top face (board pair and the IMU_CARRIER strip above)", "",
                    "the named M3 x 5.7 insert is longer than the 3.0 mm carrier and the IMU_CARRIER strip shares the screws: bosses >= 6.5 at the two "
                    "screws or a short insert are not designed (imu_pack.json; IMU lineage)"))
    # IMU pack: lid screws, board standoffs and the tripod insert (screw joints whose threads are not read or not designed)
    J.append(_joint("IMU-LID", "F24", f"IMU pack lid to the Hammond 1550Z101 body ({hb2['lid_screws']['thread']} brass instead of the stock screws)", 2,
                    hb2["lid_screws"]["thread"].split("-")[0], 4.0, "lid outer face", [],
                    "Hammond 1550Z101 body bosses (supplied thread)", None, 0.0, ENG_METAL * 4.0, "boss thread bottom",
                    "the brass M4 x 20 keeps the length of the stock Hammond lid screws",
                    f"lid ({hb2['lid_h']:g} high) thickness at the screws and the body boss thread depth are not read (Hammond 1550Z101 drawing): no window"))
    J.append(_joint("IMU-BOARD-STANDOFFS", "F36", "BNO085 + RP2040-Zero pair to the IMU carrier", None, "TBD", None, "board top face",
                    [], f"{I['boards']['standoff_h']:g} mm standoffs (AI-STANDOFF-IMU-13)", None, 0.0, 0.0, "TBD", "",
                    "standoff type, its thread depth and the screws are TBD (F36, AI-STANDOFF-IMU-13): no stack"))
    J.append(_joint("IMU-TRIPOD", "F37", "tripod camera screw into the 1/4-20 insert of the IMU carrier (from outside through the box floor)", 1,
                    "1/4-20 UNC", 6.35, "tripod head plate on the box floor outside",
                    [("Hammond 1550Z101 floor (tripod hole)", hb2["floor"])], f"brass insert {I['tripod']['carrier_insert']}", None, 0.0, 0.0,
                    "insert end inside the carrier", "",
                    "the camera screw belongs to the tripod (not a kit part) and the insert depth below the board pair is not dimensioned "
                    "(imu_pack.json tripod / boards.standoff_h): no window"))
    # pod (Hammond 1554U2GY): lid and panel
    hp = P.parts["hammond_1554u2gy"]
    J.append(_joint("POD-LID", "F40", "S-band pod lid (Hammond 1554U2GY)", 4, "Hammond lid screw", None, "lid", [],
                    "Hammond lid inserts", None, 0.0, 0.0, "—", "screws supplied with the enclosure (DigiKey 'Cover Included'); stack set by Hammond",
                    "supplied part: no stack to compute"))
    J.append(_joint("POD-PANEL", "F41", f"steel panel 1554UPL to the pod body (insert pitch {hp.get('panel_inserts_m3')})", 4, "M3", 3.0, "panel", [],
                    "Hammond M3 panel inserts (depth not read)", None, 0.0, ENG_METAL * 3.0, "insert bottom", "",
                    "insert depth and panel thickness at the screws not read (P-01)"))
    # W2 MECH-5 (review): module joints of mechanical.json module_mounts - rear-wall insert bosses, taped modules, plate PEM standoffs
    J += module_joints(P)
    # joints whose fixing is not designed yet
    for jid, row, what in (("PWR-BOND", "F26", "BOND-RF and the other CHASSIS bond points (lug + serrated washer)"),
                           ("IP2368", "F11", "IP2368 board"),
                           ("FAN-NF-A4X10", "F27", "Noctua fan of cooler A"), ("BLOWER", "F28", "Delta BFB0305HA-C"),
                           ("HATCH-BOARD", "F38", "hatch board HATCH"),
                           ("POD-MODULES", "F42", "cf2235 / LaNA WB in the pod")):
        J.append(_joint(jid, row, what, None, "TBD", None, "TBD", [], "TBD", None, 0.0, 0.0, "TBD", "",
                        "fixing not designed in the model yet (MECH-4 / MECH-5 / pod lineage): no stack"))
    nut_rows = {"F14": "SMA bulkheads (R-SMA-THREAD)", "F16": "F bulkhead P4 (R-SMA-THREAD)", "F17": "BNC P5 (R-SMA-THREAD OPEN)",
                "F18": "GX16-4 nut", "F19": "GX12 LAB BUS nut", "F20": "PEC11R nuts (R-ENC)", "F21": "PV6 power key nut (R-PWR-KEY-NUT)",
                "F22a": "LTW vents (threaded seats, R-VENT-SEAT)", "F22b": "LTW vents with nuts", "F23": "LAPP gland",
                "F25": "captive 1/4-20 nut (R-TRIPOD)", "F34": "PV6 EDL key nut",
                "F43": "pod bulkheads and gland", "F44": "pod vent", "F03": "Armor 7056A kit", "F15": "SMA mating torque"}
    counts = {"PASS": sum(1 for j in J if j["result"].startswith("PASS")), "OPEN": sum(1 for j in J if j["result"].startswith("OPEN")),
              "FAIL": sum(1 for j in J if j["result"].startswith("FAIL"))}
    return {"schema": "srrx-fastener-stacks-v1",
            "status": "MODEL GEOMETRY ONLY: stacks from mechanical/params (mechanical.json, boards.json, imu_pack.json, parts.json); no screw was fitted",
            "generator": "mechanical/srrx_mech/fasteners.py (W2 MECH-3)",
            "rules": {"min_engagement": f"heat-set insert in ASA >= {ENG_INSERT:g} d, metal thread >= {ENG_METAL:g} d, PEM flush nut = its full thread (its shank, flush with the screw-entry face)",
                      "tip_gap_mm": TIP_GAP, "length": "under-head length (ISO 14580); ISO 10642 includes the head",
                      "use": "PASS (model) = a length of the named ISO series (parts.json iso14580_lengths) falls in the window; a window without one, or a joint whose screw or standoff is not chosen, is OPEN; SRC-2 (C-13/C-14) orders the lengths and a window that no stocked length meets keeps the item TBD"},
            "joints": J, "nut_and_kit_rows": nut_rows, "summary": counts}


def module_joints(P):
    """W2 MECH-5 review: F09/F10 screws into the rear-wall TC-M2,5x4 inserts (hole insert + 1.0, mechanical.json module_mounts.insert
    hole_depth), F05/F47 taped modules (no screw), F39 PACK_FUSE carrier on the PEM SO-M2.5-6ZI standoffs (carrier and screw: PCB-SB2)."""
    m = P.mech
    mmt = m.get("module_mounts")
    if not mmt:
        return []
    ins = mmt["insert"]
    depth = ins.get("hole_depth", ins["len"])
    mounts = {x["item"]: x for x in mmt["mounts"]}
    out = []
    for jid, row, item, part, what in (("INA228", "F09", "ina228", "adafruit_ina228_5832", "INA228 5832 to the rear-wall bosses"),
                                       ("HUB-5997", "F10", "hub_ch334f", "adafruit_5997", "Adafruit 5997 CH334F to the rear-wall bosses")):
        mt = mounts.get(item)
        if not mt:
            continue
        tb = P.parts[part]["board"][2]
        out.append(_joint(jid, row, what, len(mt["screws"]), "M2.5", 2.5, f"{item} board top face, z {mt['seat_z'] + tb:g}", [(f"{item} board", tb)],
                          f"CNC Kitchen {ins['part']} insert in a printed rear-wall boss (hole {depth:g} deep from the boss top z {mt['seat_z']:g})",
                          ins["len"], depth - ins["len"] - TIP_GAP, ENG_INSERT * 2.5, f"blind insert hole bottom (insert + {depth - ins['len']:g})",
                          "M2.5 x 6 passes 0.4 beyond the insert into the empty hole (the full 4.0 insert thread engaged)", lengths=_series(P, "M2.5")))
    tape = P.parts[mmt["tape"]]
    for jid, row, item, what in (("SWM-2813", "F05", "swm_2813", "Pololu #2813 to the printed pad of the rear wall"),
                                 ("VEML7700", "F47", "veml7700", "Adafruit 4162 VEML7700 to 4 printed rests in the top-wall pocket")):
        mt = mounts.get(item)
        if not mt:
            continue
        n = len(mt.get("rests", [])) or 1
        out.append({"id": jid, "build17_row": row, "what": what, "count": n, "thread": "none (tape joint)",
                    "seat": "printed pad top" if "pad" in mt else "printed rest faces",
                    "stack_mm": [[f"{tape['name'].split(' (')[0]}", tape["t"]]], "grip_mm": None,
                    "receiver": {"kind": "acrylic foam tape on a printed face (no screw)", "thread_mm": None, "tip_limit": None},
                    "min_engagement_mm": None, "length_window_mm": None,
                    "result": f"OPEN: tape joint, no screw: {tape['t']:g} mm tape (parts.json {mmt['tape']}, status {tape['status']}); bond strength on ASA and on "
                              "the board solder mask not read; hold under vibration and temperature - bench",
                    "note": ("locating spigots in two board holes (mechanical.json module_mounts veml7700)" if mt.get("spigots") else
                             "the wires are tied down next to the board (the tape does not carry the wire pull)")})
    pf = mounts.get("pack_fuse")
    if pf:
        so = P.parts[pf["fastener"]]
        ct = m["rear_face"]["hatch"]["f101_access"]["carrier_t"]
        out.append(_joint("PACK-FUSE", "F39", "PACK_FUSE carrier (F101) to the PEM standoffs PF1-PF2", len(pf["standoffs"]), "M2.5", 2.5,
                          "carrier top face", [("PACK_FUSE carrier (thickness assumption, PCB-SB2)", ct)],
                          f"PEM {so['mpn']} thru-threaded standoff, L {so['length']:g} + its head flush in the plate", so["length"] + m["plate"]["t"], 0.0,
                          ENG_METAL * 2.5, "plate rear face (head flush with it)", lengths=_series(P, "M2.5", named=False),
                          pending="the carrier board, its screws and insulation are PCB-SB2's (build/17 F39)"))
    return out


def rule(P):
    """R-FASTENER-STACKS: every computed window is non-empty; joints with unread threads, undesigned fixings, unchosen screws or no ISO length in the window are OPEN."""
    doc = stacks(P)
    fails = [j["id"] for j in doc["joints"] if j["result"].startswith("FAIL")]
    opened = [j["id"] for j in doc["joints"] if j["result"].startswith("OPEN")]
    passed = [j["id"] for j in doc["joints"] if j["result"].startswith("PASS")]
    if fails:
        res = "FAIL (model): " + ", ".join(fails)
    else:
        res = f"OPEN: {', '.join(opened)} (thread depth not read, fixing or screw not chosen, or no ISO length in the window); PASS (model): {', '.join(passed)}" if opened else "PASS (model)"
    return {"id": "R-FASTENER-STACKS", "rule": "screw joints: under-head length window between the minimum engagement and the tip limit (generated/fastener-stacks.json)",
            "value_mm": {j["id"]: j["length_window_mm"] for j in doc["joints"] if j["length_window_mm"]}, "result": res,
            "source": "mechanical/srrx_mech/fasteners.py; build/17 rows"}
