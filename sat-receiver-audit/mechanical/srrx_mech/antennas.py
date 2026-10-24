"""Antenna fabrication: flat patterns (1:1), printed fixtures and the receive-only part-size checks."""
import math

from .geom2d import Sheet, fmt

AL = "Al 0.3-0.5 мм (лист), краї зачистити; лише прийом"


def _arc_pts(c, r, a0, a1, n=48):
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _offset_edge(p, q, d):
    """Strip of width d on the left side of edge p->q (as a quad)."""
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    nx, ny = -(q[1] - p[1]) / L, (q[0] - p[0]) / L
    return [p, q, (q[0] + nx * d, q[1] + ny * d), (p[0] + nx * d, p[1] + ny * d)]


def petal(sheet, a, ox, oy, label):
    """Isosceles trapezoid petal + disk tab + side overlap flap. Returns the outline points."""
    c1, c2, s = a["inner_chord"], a["outer_chord"], a["slant"]
    h = math.sqrt(s * s - ((c2 - c1) / 2) ** 2)
    p0, p1 = (ox - c1 / 2, oy), (ox + c1 / 2, oy)
    p2, p3 = (ox + c2 / 2, oy + h), (ox - c2 / 2, oy + h)
    tab = [(ox - c1 / 2 + 3, oy), (ox + c1 / 2 - 3, oy), (ox + c1 / 2 - 6, oy - a["tab"]), (ox - c1 / 2 + 6, oy - a["tab"])]
    flap = _offset_edge(p2, p1, a["overlap"])
    outline = [tab[3], tab[2], tab[1], p1, flap[2], flap[3], p2, p3, p0, tab[0]]
    sheet.poly(outline, True, "CUT")
    sheet.line(p0, p1, "BEND")
    sheet.line(p1, p2, "BEND")
    for f in (0.25, 0.75):
        sheet.hole((ox - c1 / 2 + c1 * f, oy - a["tab"] / 2), a.get("rivet_d", 3.2), None)
    for f in (0.2, 0.5, 0.8):
        mx, my = p1[0] + (p2[0] - p1[0]) * f, p1[1] + (p2[1] - p1[1]) * f
        L = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        nx, ny = (p2[1] - p1[1]) / L, -(p2[0] - p1[0]) / L
        sheet.hole((mx + nx * a["overlap"] / 2, my + ny * a["overlap"] / 2), a.get("rivet_d", 3.2), None)
    sheet.text((ox, oy + h / 2), label, 3.0, anchor="middle")
    sheet.dim_h(p3[0], p2[0], oy + h, oy + h + 8)
    sheet.dim_h(p0[0], p1[0], oy, oy - a["tab"] - 7)
    sheet.dim((ox, oy), (ox, oy + h), -(c2 / 2 + 14), fmt(h))
    return outline


def annular_sector(sheet, c, r0, r1, ang, overlap, rivet_r=(), rivet_d=3.2, label=""):
    """Developed cone segment from r0 to r1 spanning `ang` degrees, opening upward, + overlap flap on the right edge."""
    a0 = 90.0 - ang / 2.0
    a1 = 90.0 + ang / 2.0
    outer = _arc_pts(c, r1, a0, a1)
    inner = _arc_pts(c, r0, a1, a0)
    e0 = (c[0] + r0 * math.cos(math.radians(a0)), c[1] + r0 * math.sin(math.radians(a0)))
    e1 = (c[0] + r1 * math.cos(math.radians(a0)), c[1] + r1 * math.sin(math.radians(a0)))
    if overlap > 0:
        # overlap flap along the a0 edge (right edge)
        flap_o = _arc_pts(c, r1, a0 - math.degrees(overlap / r1), a0, 6)
        flap_i = _arc_pts(c, r0, a0, a0 - math.degrees(overlap / r0), 6)
        pts = flap_o + outer[1:] + inner + flap_i[1:]
        sheet.line(e0, e1, "BEND")
        rows = ((lambda r: a0 - math.degrees(overlap / 2 / r)),)
    else:
        # no integral flap: both radial edges get a rivet row 3 mm in, for a separate seam strap
        pts = outer + inner
        rows = ((lambda r: a0 + math.degrees(3.0 / r)), (lambda r: a1 - math.degrees(3.0 / r)))
    sheet.poly(pts, True, "CUT")
    for f in (0.15, 0.5, 0.85):
        r = r0 + (r1 - r0) * f
        for row in rows:
            am = row(r)
            sheet.hole((c[0] + r * math.cos(math.radians(am)), c[1] + r * math.sin(math.radians(am))), rivet_d, None)
    for rr in rivet_r:
        for f in (0.3, 0.7):
            am = a0 + ang * f
            sheet.hole((c[0] + rr * math.cos(math.radians(am)), c[1] + rr * math.sin(math.radians(am))), rivet_d, None)
    sheet.center_mark(c, 4)
    sheet.text((c[0], c[1] + (r0 + r1) / 2), label, 3.0, anchor="middle")
    sheet.text((c[0], c[1] + (r0 + r1) / 2 - 6.0), f"R{fmt(r0)} / R{fmt(r1)} від спільного центру", 2.4, anchor="middle")
    sheet.dim(e0, e1, -4.0)
    return pts


def sheets(P):
    A = P.antennas
    rules = A["rules"]
    out, checks = [], []
    hc = A["helicone"]
    # A-01/A-02 petals
    for sid, key, title in (("A-01", "petals", "Гелікон: пелюстка (8 шт.)"), ("A-02", "petals_t0nito", "Гелікон t0nito A/B: пелюстка (8 шт.)")):
        a = hc[key]
        sh = Sheet(sid, title, "розгортка 1:1; згин язичка до диска, нахил пелюстки 42.7° від площини диска", (297.0, 420.0), 1.0, (148.5, 120.0), AL,
                   [f"Хорди {fmt(a['inner_chord'])}/{fmt(a['outer_chord'])}, похила {fmt(a['slant'])}, язичок {fmt(a['tab'])}, перекриття {fmt(a['overlap'])} (build/06 3.2).",
                    "Заклепки ⌀3.2 (алюмінієві), шви зверху — струмопровідна Al-стрічка; гострі краї обгорнути.", a.get("_note", "")])
        pts = petal(sh, a, 0.0, 0.0, f"{sid} x{a['n']}")
        x0, y0, x1, y1 = _bbox(pts)
        mx = max(x1 - x0, y1 - y0)
        checks.append({"part": sid, "max_dim_mm": round(mx, 1), "limit_mm": rules["max_part_mm"], "result": "PASS (model)" if mx <= rules["max_part_mm"] else "FAIL (model)"})
        out.append(sh)
    # A-03 disk
    sh = Sheet("A-03", "Диск гелікона / спіралі ⌀180", "1:1, Al 1.5 мм", (297.0, 297.0), 1.0, (148.5, 148.5), "Al 1.5 мм",
               ["Отвір живлення спіралі — на r = 30.9 мм від центру (build/06 2.5); SAWbird+ GOES — під диском на SMA.",
                "8 пар отворів під язички пелюсток; 3 отвори M3 оправки спіралі; центр — 1/4-20 (⌀6.6) для штатива/тримача."])
    R = hc["disk_d"] / 2
    sh.circle((0, 0), R, "CUT")
    sh.hole((0, 0), hc["mount_hole_d"], "⌀6.6", 2.2)
    sh.hole((hc["feed_r"], 0), hc["feed_hole_d"], "feed ⌀6.4 r30.9", 2.2)
    rr = R - hc["petals"]["tab"] / 2
    off = math.degrees(math.asin((hc["petals"]["inner_chord"] / 4) / rr))
    for k in range(8):
        for s in (-1, 1):
            a = 22.5 + 45 * k + s * off
            sh.hole((rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a))), 3.2, None)
    for a in (60, 180, 300):
        sh.hole((20 * math.cos(math.radians(a)), 20 * math.sin(math.radians(a))), 3.4, None)
    sh.dim((-R, 0), (R, 0), -R - 8, f"⌀{fmt(2 * R)}")
    out.append(sh)
    # A-04/A-05 horn segments
    hn = A["horn_qo100"]
    al = math.radians(hn["half_angle"])
    tot = 360.0 * math.sin(al)
    seg = tot / hn["segments_per_ring"]
    r_in = (hn["throat_od"] / 2) / math.sin(al)
    for sid, (r0, r1), lab, riv in (("A-04", (r_in, hn["inner_r"][1]), "внутрішній сегмент x3", (r_in + 5.0, hn["inner_r"][1] - 6.0)),
                                    ("A-05", tuple(hn["outer_r"]), "зовнішній сегмент x3", (hn["outer_r"][0] + 6.0, hn["outer_r"][1] - 5.0))):
        sh = Sheet(sid, f"Рупор QO-100: {lab}", f"розгортка 1:1, кут сегмента {fmt(seg, 2)}° (повна розгортка {fmt(tot, 2)}°)", (420.0, 297.0), 1.0, (160.0, 30.0 - r0 + 10.0), AL,
                   [f"Напівкут {fmt(hn['half_angle'])}°, горло ⌀{fmt(hn['throat_od'])} (виміряти ковпачок; ⌀{fmt(hn['throat_od_alt'])} для F4DAV), R_in = r/sin α = {fmt(r_in, 1)}.",
                    f"Шов — окрема накладка (перекриття ≥{fmt(hn['seam_overlap'])} мм на кожен сегмент, заклепки), зверху Al-стрічка: так сегмент лишається ≤18.7 см; кільця перекриваються 255-267 мм (build/06 3.3).",
                    "Кільця жорсткості ⌀127 і ⌀180 — друковані (STL); отвори кілець — по 2 на сегмент."])
        pts = annular_sector(sh, (0.0, 0.0), r0, r1, seg, 0.0, riv, hn["rivet_d"], lab)
        # separate seam strap (3 per ring): overlaps each neighbour by seam_overlap + 1 mm on the same rivet rows
        sw = 2.0 * (hn["seam_overlap"] + 1.0)
        sx, sy = r1 * math.sin(math.radians(seg / 2.0)) + 25.0, r0 + 20.0
        sh.rect(sx, sy, sw, r1 - r0, "CUT")
        for f in (0.15, 0.5, 0.85):
            for dx in (sw / 2.0 - 3.0, -(sw / 2.0 - 3.0)):
                sh.hole((sx + sw / 2.0 + dx, sy + (r1 - r0) * f), hn["rivet_d"], None)
        sh.text((sx, sy - 5.0), f"накладка шва x3: {fmt(r1 - r0)} x {fmt(sw)} (Al 0.3-0.5), заклепки ⌀3.2", 2.4)
        sh.dim_v(sy, r1, sx + sw, sx + sw + 6)
        x0, y0, x1, y1 = _bbox(pts)
        mx = max(x1 - x0, y1 - y0)
        checks.append({"part": sid, "max_dim_mm": round(mx, 1), "limit_mm": rules["horn_segment_max_mm"],
                       "result": "PASS (model)" if mx <= rules["horn_segment_max_mm"] else "FAIL (model): exceeds the 18.7 cm segment rule of build/06 0.3 with the seam flap"})
        out.append(sh)
    # A-06 LNB cone
    cn = A["cone_lnb"]
    al = math.radians(cn["half_angle"])
    r1 = (cn["mouth_d"] / 2) / math.sin(al)
    r0 = (cn["throat_od"] / 2) / math.sin(al)
    ang = 360.0 * math.sin(al)
    sh = Sheet("A-06", "Конус LNB 11 см (QO-100, патч-рівень)", f"розгортка 1:1, кут {fmt(ang, 1)}°", (420.0, 297.0), 1.0, (180.0, 60.0), AL,
               [f"Напівкут {fmt(cn['half_angle'])}°, устя ⌀{fmt(cn['mouth_d'])}: R = {fmt(r1, 1)}; горло ⌀{fmt(cn['throat_od'])}: R = {fmt(r0, 1)} (build/06 2.7).",
                "Шов внахлест 5 мм на заклепках; горло — на друкованому кільці на площині червоного ковпачка (ковпачок не знімати й не різати)."])
    pts = annular_sector(sh, (0.0, 0.0), r0, r1, ang, cn["seam_overlap"], (r0 + 5.0,), 3.2, "конус x1")
    x0, y0, x1, y1 = _bbox(pts)
    checks.append({"part": "A-06", "max_dim_mm": round(max(x1 - x0, y1 - y0), 1), "limit_mm": rules["max_part_mm"],
                   "result": "PASS (model)" if max(x1 - x0, y1 - y0) <= rules["max_part_mm"] else "FAIL (model)"})
    out.append(sh)
    # A-07 Yagi boom
    y = A["yagi"]
    bm = y["boom"]
    sh = Sheet("A-07", "Схрещений Yagi: штанга 20 x 20, розмітка і свердління", "1:1 по частинах (ультракомпакт, 5 частин)", (420.0, 297.0), 1.0, (20.0, 40.0),
               bm["material"],
               ["2 m (WB2HOL): R 0, DE 0.203 м, D 0.508 м — стрічки 25 мм у власних затискачах (STL), штангу не свердлити.",
                "70 см (N2SPI): поперечні отвори ⌀3.4 крізь штангу в перпендикулярній площині для муфт M3; довжини половин ≤17.0 см — за кресленням N2SPI (TBD).",
                "Стики — шипи-ключі (STL) ±0°; кожна частина ≤16 см і ≥3.6 см від елементів (build/06 3.1)."])
    joints = [0.0] + bm["joints"] + [bm["length"]]
    rowy = 0.0
    for i, (a, b) in enumerate(zip(joints, joints[1:])):
        L = b - a
        sh.rect(0, rowy, L, bm["section"][0], "CUT")
        sh.text((0, rowy + bm["section"][0] + 2), f"частина {i + 1}: {fmt(a)}-{fmt(b)} мм, довжина {fmt(L)}", 2.4)
        for e in y["elements_2m"]:
            if a <= e["pos"] <= b:
                sh.line((e["pos"] - a, rowy - 3), (e["pos"] - a, rowy + bm["section"][0] + 3), "CENTER")
                sh.text((e["pos"] - a + 1, rowy - 6), f"2m {e['id']}", 2.0)
        for e in y["elements_70cm"]:
            if a <= e["pos"] <= b:
                sh.hole((e["pos"] - a, rowy + bm["section"][0] / 2), y["rod_hole_d"], f"70 {e['id']}", 2.0)
        sh.dim_h(0, L, rowy, rowy - 4)
        rowy += 42.0
    out.append(sh)
    # yagi rules
    poss = [e["pos"] for e in y["elements_2m"]] + [e["pos"] for e in y["elements_70cm"]]
    for i, (a, b) in enumerate(zip(joints, joints[1:])):
        checks.append({"part": f"A-07 boom part {i + 1}", "max_dim_mm": round(b - a, 1), "limit_mm": rules["yagi_part_max_mm"],
                       "result": "PASS (model)" if b - a <= rules["yagi_part_max_mm"] else "FAIL (model)"})
    for j in bm["joints"]:
        dmin = min(abs(j - p) for p in poss)
        checks.append({"part": f"A-07 joint {fmt(j)}", "min_distance_to_element_mm": round(dmin, 1), "limit_mm": rules["yagi_joint_min_mm"],
                       "result": "PASS (model)" if dmin >= rules["yagi_joint_min_mm"] else "FAIL (model)"})
    return out, checks


def pod_sheet(P):
    A = P.antennas["sband_pod"]
    hb = P.parts["hammond_1554u2gy"]
    cf, ln = P.parts["cf2235"], P.parts["lana_wb"]
    ox, oy = hb["outside"][0], hb["outside"][1]
    ix, iy = hb["inside"][0], hb["inside"][1]
    sh = Sheet("P-01", "Зовнішній S-band вузол: Hammond 1554U2GY", "розміщення і свердління, 1:1", (420.0, 297.0), 1.0, (30.0, 60.0),
               "корпус PC (Hammond), сталева панель 1554UPL",
               ["cf2235-kt30 (124 x 47 x 33) — на сталевій панелі; LaNA WB (60 x 38 x 25) — другим шаром, 5 мм над фільтром (build/12).",
                f"Стек 33 + 5 + 25 = 63 мм + стійки {fmt(A['standoff'])} ≤ внутрішньої висоти {fmt(hb['inside'][2])} — модельно, без кабелів; посадка і герметизація — ворота E4-04 OPEN.",
                "Отвори кріплення модулів — за їх кресленнями (TBD); SMA — ⌀6.4, гермоввід і клапан — ⌀12.2; клапан ніколи догори.",
                "Момент гвинтів кришки 30-40 cN·m (креслення Hammond 1554U)."])
    sh.rect(0, 0, ox, oy, "CUT")
    sh.rect((ox - ix) / 2, (oy - iy) / 2, ix, iy, "HIDDEN")
    for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        sh.hole((ox / 2 + sx * hb["lid_screws_pitch"][0] / 2, oy / 2 + sy * hb["lid_screws_pitch"][1] / 2), 4.0, None)
    cx, cy = (ox - cf["size"][0]) / 2, 12.0
    sh.rect(cx, cy, cf["size"][0], cf["size"][1], "HIDDEN")
    sh.text((cx + 2, cy + 2), "cf2235-kt30 (шар 1)", 2.4)
    lx, ly = (ox - ln["size"][0]) / 2, cy + cf["size"][1] + 8.0
    sh.rect(lx, ly, ln["size"][0], ln["size"][1], "HIDDEN")
    sh.text((lx + 2, ly + 2), "LaNA WB (шар 2, над фільтром)", 2.4)
    for (px, py) in ((ox / 2 - hb["panel_inserts_m3"][0] / 2, oy / 2 - hb["panel_inserts_m3"][1] / 2), (ox / 2 + hb["panel_inserts_m3"][0] / 2, oy / 2 - hb["panel_inserts_m3"][1] / 2),
                     (ox / 2 - hb["panel_inserts_m3"][0] / 2, oy / 2 + hb["panel_inserts_m3"][1] / 2), (ox / 2 + hb["panel_inserts_m3"][0] / 2, oy / 2 + hb["panel_inserts_m3"][1] / 2)):
        sh.center_mark((px, py), 3)
    sh.dim_h(0, ox, 0, -8)
    sh.dim_v(0, oy, 0, -8)
    return sh


def pod_walls_sheet(P):
    """Drilling of the S-band pod walls, each seen from outside; z from the bottom of the box body."""
    A = P.antennas["sband_pod"]
    hb = P.parts["hammond_1554u2gy"]
    ox, oy = hb["outside"][0], hb["outside"][1]
    bh = hb["box_h"]
    sh = Sheet("P-02", "Зовнішній S-band вузол: свердління стінок", "вид ззовні кожної стінки, 1:1; z — від дна корпусу", (420.0, 297.0), 1.0,
               (30.0, 40.0), "корпус PC (Hammond 1554U2GY)",
               ["SMA-прохідники ⌀6.4 (1/4-36, тип TBD, MECH-07); гермоввід кабелю живлення USB-C (лише живлення LaNA) і клапан M12 — ⌀12.2.",
                "Клапан — на бічній стінці, ніколи догори; ущільнювальні кільця прохідників — з боку корпусу.",
                "Положення — модельні (build/12: шари з 5 мм між ними); посадка й герметизація — ворота E4-04 OPEN."])
    walls = [("left_end", "торець лівий", oy, 0.0, 115.0), ("right_end", "торець правий", oy, 150.0, 115.0),
             ("side_front", "бічна стінка (передня)", ox, 0.0, 0.0)]
    for wall, title, w, x0, y0 in walls:
        sh.rect(x0, y0, w, bh, "CUT")
        sh.label((x0, y0 + bh + 3), f"{title} ({fmt(w)} x {fmt(bh)})", 2.4)
        sh.dim_h(x0, x0 + w, y0, y0 - 5)
        sh.dim_v(y0, y0 + bh, x0, x0 - 6)
        for p in A["ports"]:
            if p["wall"] == wall:
                d = 6.4 if p["kind"] == "sma_bulkhead" else 12.2
                u = p["x"] if wall == "side_front" else p["y"]
                sh.hole((x0 + u, y0 + p["z"]), d, f"{p['id']} ⌀{fmt(d)} ({fmt(u)}, {fmt(p['z'])})", 2.2)
    return sh


def imu_sheet(P):
    I = P.imu
    hb = P.parts["hammond_1550z101"]
    ix, iy = hb["inside"][0], hb["inside"][1]
    sh = Sheet("I-01", "Пак IMU: Hammond 1550Z101 — свердління, плати, осі", "2:1", (297.0, 210.0), 2.0, (30.0, 40.0),
               "литий Al (Hammond 1550Z101), латунні гвинти кришки M4",
               ["Осі паку: +X — стрілка на кришці (бортове візування антени), +Z — з кришки, +Y = Z x X (правий трійник).",
                "BNO085 ставиться так, щоб осі мікросхеми збігалися з осями паку (матриця chip_to_pack = I); знаки й орієнтацію перевіряє стенд (OPEN).",
                "Дно: отвір ⌀6.6 під 1/4-20; носій (STL) з латунною вставкою 1/4-20 x 12.7, гвинти M3 у вставки; плати на стійках 13 мм над носієм.",
                "Стінка y_max: SKINTOP MS-SC-M12 ⌀12.2; шов кришки — провідна фольгова стрічка; момент гвинтів кришки 50-75 cN·m (креслення Hammond)."])
    sh.rect(0, 0, ix, iy, "CUT")
    bx, by = I["boards"]["origin_in_box"]
    pw, ph = I["boards"]["pair"]
    sh.rect(bx, by, pw, ph, "HIDDEN")
    sh.rect(bx, by, P.parts["bno085_board"]["bno_board"][0], ph, "HIDDEN")
    sh.text((bx + 1, by + 1), "BNO085", 1.6)
    sh.text((bx + 27, by + 1), "RP2040-Zero", 1.6)
    t = I["tripod"]
    sh.hole(tuple(t["c"]), t["hole_d"], "⌀6.6", 1.6)
    for (sx, sy) in I["carrier"]["screws"]:
        sh.hole((sx, sy), 3.4, None)
    g = I["gland"]
    sh.line((g["x"] - g["hole_d"] / 2, iy), (g["x"] + g["hole_d"] / 2, iy), "HOLE")
    sh.text((g["x"] - 14, iy + 1.5), f"SKINTOP M12 ⌀{fmt(g['hole_d'])}, центр {fmt(g['z'])} мм від дна (стінка y_max)", 1.6)
    # axis arrows
    ox, oy = ix / 2, iy / 2
    sh.line((ox, oy), (ox + 15, oy), "ENGRAVE")
    sh.line((ox + 15, oy), (ox + 12.5, oy + 1.5), "ENGRAVE")
    sh.line((ox + 15, oy), (ox + 12.5, oy - 1.5), "ENGRAVE")
    sh.text((ox + 16, oy - 1), "+X (boresight)", 1.8)
    sh.line((ox, oy), (ox, oy + 12), "ENGRAVE")
    sh.text((ox + 1, oy + 12), "+Y", 1.8)
    sh.circle((ox, oy), 1.5, "ENGRAVE")
    sh.text((ox - 6, oy - 4), "+Z (з кришки)", 1.8)
    sh.dim_h(0, ix, 0, -5)
    sh.dim_v(0, iy, 0, -5)
    return sh
