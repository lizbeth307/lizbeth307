"""Panel drilling sheets, mid-plate, angles, RF bay, pedestal, cooler block, HF+ can, bezel and seam details."""
import math

from .features import HOLES, face_features, face_size
from .geom2d import Sheet, fmt

FACE_UK = {"front": "лице (z = D)", "rear": "задня стінка, вид ззаду", "top": "верхня грань, вид згори (лице внизу)",
           "bottom": "нижня грань, вид знизу (лице вгорі)", "left": "ліва стінка, вид зліва (лице праворуч)",
           "right": "права стінка, вид справа (лице ліворуч)"}


def _feature(sh, f, ox=0.0, oy=0.0):
    u, v = f["u"] + ox, f["v"] + oy
    k = f["kind"]
    if k in ("window",):
        sh.rrect(u - f["w"] / 2, v - f["h"] / 2, f["w"], f["h"], f.get("r", 0), "CUT")
        sh.center_mark((u, v), 6)
        sh.text((u - f["w"] / 2 + 2, v + f["h"] / 2 - 5), f"{f['id']} {fmt(f['w'])} x {fmt(f['h'])}", 2.5)
    elif k == "grille":
        sh.rect(u - f["w"] / 2, v - f["h"] / 2, f["w"], f["h"], "HIDDEN")
        n = int((f["w"] if f["slots_along"] == "u" else f["h"]) // f["slot_pitch"])
        for i in range(n):
            if f["slots_along"] == "u":
                x = u - f["w"] / 2 + f["slot_pitch"] * (i + 0.5)
                sh.rrect(x - f["slot_w"] / 2, v - f["h"] / 2 + 1.5, f["slot_w"], f["h"] - 3.0, f["slot_w"] / 2, "CUT")
            else:
                y = v - f["h"] / 2 + f["slot_pitch"] * (i + 0.5)
                sh.rrect(u - f["w"] / 2 + 1.5, y - f["slot_w"] / 2, f["w"] - 3.0, f["slot_w"], f["slot_w"] / 2, "CUT")
        sh.text((u - f["w"] / 2, v + f["h"] / 2 + 1.5), f"{f['id']} {fmt(f['w'])} x {fmt(f['h'])}", 2.2)
    elif k == "hatch":
        sh.rrect(u - f["w"] / 2, v - f["h"] / 2, f["w"], f["h"], f["r"], "CUT")
        sh.text((u - f["w"] / 2, v + f["h"] / 2 + 1.5), f"{f['id']} {fmt(f['w'])} x {fmt(f['h'])}", 2.2)
    elif k == "tbd":
        sh.rect(u - f["w"] / 2, v - f["h"] / 2, f["w"], f["h"], "HIDDEN")
        sh.hole((u, v), f["d"], f"{f['id']} TBD", 2.0)
    elif k == "strap":
        sh.rect(u - f["w"] / 2, v - f["h"] / 2, f["w"], f["h"], "HIDDEN")
        sh.label((u - f["w"] / 2, v + f["h"] / 2 + 1.0), f["id"], 1.8,
                 [(u - f["w"] / 2, v - f["h"] / 2 - 3.5), (u + f["w"] / 2 + 1.0, v)])
    elif k == "tripod":
        sh.hole((u, v), f["d"], f"⌀{fmt(f['d'])} 1/4-20", 2.2)
        af = 11.3
        r = af / math.sqrt(3)
        pts = [(u + r * math.cos(math.radians(30 + 60 * i)), v + r * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
        sh.poly(pts, True, "HIDDEN")
    elif k == "closure":
        sh.circle((u, v), f["cb_d"] / 2, "HIDDEN")
        sh.hole((u, v), f["d"], None)
    else:
        lab = f["id"].replace("KEY_", "").replace("ENC_", "ENC ").replace("_PORT", "").replace("STATUS_", "")
        sh.hole((u, v), f["d"], lab, 1.8, dx=-f["d"] / 2, dy=-(f["d"] / 2 + 3.2))
        if f.get("boss_d"):
            sh.circle((u, v), f["boss_d"] / 2, "HIDDEN")


def _table(sh, feats, x, y, title):
    sh.ptext((x, y), title, 2.8)
    y -= 4.5
    sh.ptext((x, y), "ID                 u       v  розмір", 2.0, layer="TABLE")
    y -= 3.4
    for f in feats:
        size = f"⌀{fmt(f['d'])}" if "d" in f and f["kind"] not in ("grille", "hatch", "window", "tbd") else f"{fmt(f.get('w', 0))} x {fmt(f.get('h', 0))}"
        basis = HOLES.get(f["kind"], {}).get("basis", "")
        line = f"{f['id'][:14]:14s} {fmt(f['u'], 1):>7s} {fmt(f['v'], 1):>7s}  {size}"
        sh.ptext((x, y), line, 2.0, layer="TABLE")
        y -= 3.0
        if basis and f["kind"] not in ("closure", "insert_m3"):
            sh.ptext((x + 4, y), basis[:92], 1.6)
            y -= 2.6
    return y


def face_outline(sh, P, face, ox, oy):
    W, H, D = P.outer
    w, h = face_size(P, face)
    m = P.mech
    if face in ("front", "rear"):
        sh.rrect(ox, oy, w, h, m["outer"]["corner_r"], "CUT")
    else:
        sh.rect(ox, oy, w, h, "CUT")
        split = m["split_z"]
        if face in ("top",):
            sh.line((ox, oy + D - split), (ox + w, oy + D - split), "BEND")
        elif face == "bottom":
            sh.line((ox, oy + split), (ox + w, oy + split), "BEND")
        elif face == "left":
            sh.line((ox + split, oy), (ox + split, oy + h), "BEND")
        elif face == "right":
            sh.line((ox + D - split, oy), (ox + D - split, oy + h), "BEND")
    sh.dim_h(ox, ox + w, oy, oy - 12, fmt(w))
    sh.dim_v(oy, oy + h, ox, ox - 12, fmt(h))


def face_sheets(P):
    F = face_features(P)
    sheets = []
    notes_common = ["Координати u/v — від лівої (A) і нижньої (B) кромок грані, як видно ззовні. Одиниці мм, допуск ±0.2.",
                    "Лінія роз'єму корпусу показана штриховою (BEND); отвори ⌀3 'TBD' — лише кернування, остаточний виріз за кресленням обраної деталі.",
                    "MODEL FIT ONLY: посадку кожної деталі перевірити на стенді (ворота OPEN)."]
    # front and rear on separate A3 sheets
    for sid, face in (("M-01", "front"), ("M-06", "rear")):
        sh = Sheet(sid, f"Корпус: {FACE_UK[face]}", "свердління/вирізи, 1:1", (420.0, 297.0), 1.0, (30.0, 60.0),
                   "ASA (Polymaker PF01002), друк", notes_common)
        face_outline(sh, P, face, 0.0, 0.0)
        for f in F[face]:
            _feature(sh, f)
        if face == "front":
            g = P.mech["display"]["glass_pocket"]
            sh.rect(g[0], g[1], g[2], g[3], "HIDDEN")
            sh.text((g[0] + 1, g[1] + 1), "кишеня скла 164.82 x 98.58 (усередині)", 2.0)
            e = P.mech["hmi"]["encoders"]
            sh.dim_v(e["volume"]["c"][1], e["main"]["c"][1], e["main"]["c"][0], 245.0 - 30.0)
            b = P.mech["hmi"]["buttons"]
            sh.dim_h(b["cols_x"][0], b["cols_x"][1], b["rows_y"][-1], 6.0)
        if face == "rear":
            t7 = P.mech["rear_face"]["t7_holder"]["rect"]
            W = P.outer[0]
            sh.rect(W - t7[0] - t7[2], t7[1], t7[2], t7[3], "HIDDEN")
            sh.text((W - t7[0] - t7[2] + 2, t7[1] + 2), "тримач T7 (зовні, гвинти M3)", 2.0)
        _table(sh, F[face], 268.0, 222.0, "Таблиця отворів")
        sheets.append(sh)
    # top + bottom on one sheet, left + right on another
    for sid, pair in (("M-02", ("top", "bottom")), ("M-03", ("left", "right"))):
        sh = Sheet(sid, "Корпус: " + " і ".join(FACE_UK[f].split(",")[0] for f in pair), "свердління/вирізи, 1:1",
                   (420.0, 297.0), 1.0, (30.0, 50.0), "ASA (Polymaker PF01002), друк", notes_common)
        ty = 222.0
        if pair[0] == "top":
            offs = [(0.0, 120.0), (0.0, 20.0)]
        else:
            offs = [(0.0, 20.0), (110.0, 20.0)]
        for face, (ox, oy) in zip(pair, offs):
            face_outline(sh, P, face, ox, oy)
            for f in F[face]:
                _feature(sh, f, ox, oy)
            w, h = face_size(P, face)
            sh.text((ox, oy + h + 3), FACE_UK[face], 2.6)
            ty = _table(sh, F[face], 268.0, ty, f"Таблиця: {face}") - 4.0
        sheets.append(sh)
    return sheets


def plate_sheet(P):
    from .rules import plate_holes, plate_outline, ufs_rect
    m = P.mech
    pl = m["plate"]
    sh = Sheet("M-07", "Середня пластина (шасі), шаблон 1:1", "лазер/фрезер; отвори ±0.2; площинність ≤0.2 під Q6A, п'єдесталом і регуляторами",
               (420.0, 297.0), 1.0, (25.0, 60.0), pl["material"],
               ["Контур і отвори — з mechanical/params; DXF того самого аркуша — для різання. Різьбу в пластині не нарізати (STACK 5.8).",
                "PWR1-7: гайки PEM F-M3-1 врівень з обох боків (отвір 4.37 +0.08); RF1-6: стійки PEM SO-M3-3, голівка врівень з лицьовою гранню (4.22 +0.08).",
                "UB1-2: потай M2.5 з лицьової грані в бобишку UFS; Q6A1-4: M2.5 крізь пластину в стійки 6 мм з тильного боку.",
                "Ребра шляху 2 (смуги Al 1 x 3.5) — на лицьовій грані під HDMI-платою, уздовж потоку; точки з'єднання — голий метал.",
                "Пунктир: контури плат, Q6A, бобишки UFS (тильна грань), п'єдесталу Lime і зон термопрокладок PWR."])
    sh.poly(plate_outline(P), True, "CUT")
    rw = pl["riser_window"]
    sh.rect(rw[0], rw[1], rw[2], rw[3], "CUT")
    sh.label((rw[0], rw[1] + rw[3] + 1), "проріз riser R44SF", 2.0)
    hs = pl["hdmi_slot"]
    sh.rrect(hs[0], hs[1], hs[2], hs[3], hs[3] / 2, "CUT")
    sh.label((hs[0], hs[1] - 3), "проріз кабелю HDMI", 2.0)
    holes = plate_holes(P)
    for h in holes:
        sh.hole(h["c"], h["d"], h["id"], 1.6)
    for bp in pl["bond_points"]:
        sh.circle(tuple(bp["c"]), 5.0, "HIDDEN")
    for bid in ("PWR", "RF"):
        b = P.boards["boards"][bid]
        ox, oy = b["place"]["origin"]
        sh.poly([(ox + px, oy + py) for px, py in b["outline"]], True, "HIDDEN")
        sh.label((ox + 2, oy + 2), f"плата {bid}", 2.0, [(ox + 2, oy + 6)])
    for z in P.boards["boards"]["PWR"]["thermal_bond"]:
        ox, oy = P.boards["boards"]["PWR"]["place"]["origin"]
        sh.rect(ox + z[0], oy + z[1], z[2], z[3], "HIDDEN")
    q = P.parts["q6a"]
    x0, y0 = m["q6a_mount"]["origin"]
    sh.rect(x0, y0, q["board"][0], q["board"][1], "HIDDEN")
    sh.label((x0 + 2, y0 + q["board"][1] - 4), "Q6A (тильна грань), стійки M2.5 x 6", 2.0)
    ux0, uy0, ux1, uy1 = ufs_rect(P)
    sh.rect(ux0, uy0, ux1 - ux0, uy1 - uy0, "HIDDEN")
    sh.label((ux0, uy1 + 1), "бобишка UFS", 1.8, [(ux0, uy0 - 3)])
    lp = m["lime_pedestal"]["rect"]
    sh.rect(lp[0], lp[1], lp[2], lp[3], "HIDDEN")
    sh.label((lp[0] + 1, lp[1] + 1), "п'єдестал Lime (лицьова грань)", 1.8, [(lp[0] + 1, lp[1] + lp[3] - 3)])
    fn = m["fins"]
    n = int((fn["y"][1] - fn["y"][0]) // fn["pitch"]) + 1
    for i in range(n):
        yy = fn["y"][0] + i * fn["pitch"]
        sh.line((fn["x"][0], yy), (fn["x"][1], yy), "HIDDEN")
    x, y, w, h = pl["main"]
    ex, ey, ew, eh = pl["ext"]
    sh.dim_h(x, x + w, y + h, y + h + 10)
    sh.dim_v(y, y + h, x, x - 10)
    sh.dim_h(ex, ex + ew, ey, ey - 10)
    sh.dim_v(ey, y, ex + ew, ex + ew + 10)
    # hole table; X/Y from datums A (left edge of the plate) and B (lower edge of the extension)
    dx, dy = x, ey
    tx, ty = 262.0, 268.0
    sh.ptext((tx, ty), f"Таблиця отворів: X від кромки A (x = {fmt(dx)}), Y від кромки B (y = {fmt(dy)})", 2.4)
    ty -= 4.0
    sh.ptext((tx, ty), "ID        X       Y     ⌀  що ставиться", 1.9, layer="TABLE")
    ty -= 3.0
    for hrow in holes:
        line = f"{hrow['id']:7s} {fmt(hrow['c'][0] - dx, 2):>7s} {fmt(hrow['c'][1] - dy, 2):>7s} {fmt(hrow['d'], 2):>5s}  {hrow['use'][:44]}"
        sh.ptext((tx, ty), line, 1.75, layer="TABLE")
        ty -= 2.55
    for key, label in (("riser_window", "проріз riser"), ("hdmi_slot", "проріз HDMI")):
        rx, ry, rw_, rh_ = pl[key]
        sh.ptext((tx, ty), f"{label}: X {fmt(rx - dx)}..{fmt(rx + rw_ - dx)}, Y {fmt(ry - dy)}..{fmt(ry + rh_ - dy)}", 1.75, layer="TABLE")
        ty -= 2.55
    return sh


def angles_sheet(P):
    m = P.mech
    W, H, D = P.outer
    sh = Sheet("M-08", "Алюмінієві кутники роз'ємів (стінка 4-5 мм = ASA + 2 мм Al)", "кутник 20 x 20 x 2, розгортки полиць 1:1",
               (420.0, 297.0), 1.0, (25.0, 40.0), m["angles"]["material"],
               ["Полиця 'стінка' прилягає до стінки корпусу зсередини; отвори збігаються з отворами корпусу (M-02, M-03).",
                "Полиця 'пластина' кріпиться до тильного боку пластини (M-07) гвинтами M3 з гайками; з'єднання — голий метал.",
                "Прохідники: ≥3 повні витки різьби після кільця, стопорної шайби й гайки (STACK 5.8)."])
    at = m["angles"]["top"]
    L = at["x"][1] - at["x"][0]
    # wall leg (in XZ): u = x - x0, v = z - (plate_rear - leg)
    pr = m["stack_z"]["plate_rear"]
    oy = 150.0
    sh.rect(0, oy, L, at["leg_wall"], "CUT")
    sh.text((0, oy + at["leg_wall"] + 3), "Верхній кутник: полиця 'стінка' (вид згори)", 2.6)
    for p in m["top_face"]["ports"]:
        if at["x"][0] < p["x"] < at["x"][1]:
            d = HOLES[p["kind"]]["d"]
            sh.hole((p["x"] - at["x"][0], oy + (m["top_face"]["ports_z"] - (pr - at["leg_wall"]))), d, f"{p['id']} ⌀{fmt(d)}", 2.0)
    sh.dim_h(0, L, oy, oy - 8)
    oy2 = 100.0
    sh.rect(0, oy2, L, at["leg_plate"], "CUT")
    sh.text((0, oy2 + at["leg_plate"] + 3), "Верхній кутник: полиця 'пластина'", 2.6)
    for i in range(5):
        xh = 8 + i * ((L - 16) / 4)
        sh.hole((xh, oy2 + at["leg_plate"] / 2), 3.4, None)
    ar = m["angles"]["right"]
    L2 = ar["y"][1] - ar["y"][0]
    ox = 260.0
    sh.rect(ox, 100.0, ar["leg_wall"], L2, "CUT")
    sh.text((ox, 100.0 + L2 + 3), "Правий кутник: 'стінка'", 2.6)
    for p in m["right_face"]["ports"]:
        d = HOLES[p["kind"]]["d"]
        sh.hole((ox + (p["z"] - (pr - ar["leg_wall"])), 100.0 + p["y"] - ar["y"][0]), d, f"{p['id']} ⌀{fmt(d)}", 2.0)
    ox2 = 300.0
    sh.rect(ox2, 100.0, ar["leg_plate"], L2, "CUT")
    sh.text((ox2, 100.0 + L2 + 3), "'пластина'", 2.6)
    for yh in (6, L2 / 2, L2 - 6):
        sh.hole((ox2 + ar["leg_plate"] / 2, 100.0 + yh), 3.4, None)
    sh.dim_v(100.0, 100.0 + L2, ox, ox - 8)
    return sh


def rfbay_sheet(P):
    m = P.mech
    rb = m["rf_bay"]
    x, y, w, h = rb["rect"]
    pr = m["stack_z"]["plate_rear"]
    hz = pr - rb["lid_z"][1]
    sh = Sheet("M-09", "РЧ-відсік: розкрій фольгованого FR4", "кришка і стінки, 1:1; шви пропаяти суцільно з обох боків",
               (420.0, 297.0), 1.0, (25.0, 35.0), rb["material"],
               ["Дно відсіку — пластина (Al); верх — Al-кутник + стінка корпусу; FR4: кришка (несе модулі), ліва, нижня й права стінки.",
                f"Висота стінок {fmt(hz)} = від кришки до тильної грані пластини; стінки паяти до кришки, до пластини — мідною стрічкою або пружними лапками.",
                "Вирізи N1-N4 — біля кришки, під кабелі (таблиця); краї вирізів облудити. Фоторезист зняти перед паянням (STACK 2.9).",
                "Модулі на кришці: SAWbird+/Flamingo+ — M3 за отворами корпусу модуля (розмітити по деталі, TBD); V4L — хомути через пари прорізів 2 x 4.",
                "Розетки USB-подовжувачів V4L у відсіку не змодельовано (fit-report 'rf_bay_packing': OPEN)."])
    # lid
    sh.rect(0, 0, w, h, "CUT")
    sh.label((0, h + 3), f"Кришка {fmt(w)} x {fmt(h)} (несе модулі), 1 шт.", 2.6)
    for it in m["layout"]["items"]:
        if it.get("mount") == "rf_lid":
            bx, by, _, dx, dy, _ = it["box"]
            sh.rect(bx - x, by - y, dx, dy, "HIDDEN")
            sh.label((bx - x + 2, by - y + 2), it["id"], 2.0)
            if it["part"] == "v4l":
                for fx in (0.25, 0.75):
                    for fy in (-1, 1):
                        sh.rrect(bx - x + dx * fx - 2.0, by - y + dy / 2 + fy * (dy / 2 + 2.5) - 0.75, 4.0, 1.5, 0.75, "CUT")
            else:
                for hx in (bx - x + 4, bx - x + dx - 4):
                    sh.hole((hx, by - y + dy / 2), 3.2, None)
    c = m["closure"]
    for (bx, by) in c["bosses"]:
        if x < bx < x + w and y < by < y + h:
            sh.circle((bx - x, by - y), c["boss_d"] / 2 + 0.5, "CUT")
    sh.dim_h(0, w, 0, -6)
    sh.dim_v(0, h, 0, -8)
    # bottom wall with notches at the lid edge (v = 0)
    oy = h + 20.0
    sh.rect(0, oy, w, hz, "CUT")
    sh.label((0, oy + hz + 3), f"Нижня стінка {fmt(w)} x {fmt(hz)}, 1 шт. (низ — кромка кришки)", 2.6)
    for n in rb["notches"]:
        if n["wall"] == "bottom":
            sh.rect(n["x"][0] - x, oy, n["x"][1] - n["x"][0], n["h"], "CUT")
            sh.label((n["x"][0] - x, oy + n["h"] + 1), n["id"], 2.0)
    sh.dim_h(0, w, oy, oy - 5)
    sh.dim_v(oy, oy + hz, w, w + 8)
    # side walls
    oy2 = oy + hz + 20.0
    for i, side in enumerate(s for s in rb["walls"] if s != "bottom"):
        ox = i * (h + 25.0)
        sh.rect(ox, oy2, h, hz, "CUT")
        sh.label((ox, oy2 + hz + 3), f"{'Ліва' if side == 'left' else 'Права'} стінка {fmt(h)} x {fmt(hz)}, 1 шт.", 2.6)
        sh.dim_h(ox, ox + h, oy2, oy2 - 5)
    tx, ty = 262.0, 150.0
    sh.ptext((tx, ty), "Вирізи нижньої стінки (від лівого краю кришки)", 2.4)
    ty -= 4.0
    for n in rb["notches"]:
        sh.ptext((tx, ty), f"{n['id']}: {fmt(n['x'][0] - x)}..{fmt(n['x'][1] - x)} x {fmt(n['h'])} — {n['use'][:60]}", 1.8, layer="TABLE")
        ty -= 3.0
    return sh


def pedestal_cooler_sheet(P, vendor_fit=None):
    from .layout import cu_block_geometry
    m = P.mech
    lp = m["lime_pedestal"]
    ub = m["ufs_boss"]
    cb = m["cu_block"]
    sh = Sheet("M-10", "П'єдестал Lime, бобишка UFS, мідний блок охолоджувача A", "механічна обробка, 2:1", (420.0, 297.0), 2.0, (25.0, 30.0),
               "Al 6082/5754 (п'єдестал, бобишка), Cu (блок)",
               ["Площинність контактних площин ≤0.05, шорсткість Ra ≤1.6; кромки притупити. Прокладки — таблиця thermal_interfaces у fit-report.json.",
                f"Бобишка UFS: висота = виміряний зазор − {fmt(ub['pad_gap'])} (прокладка {fmt(ub['pad'])} мм, стиск 10-30 %); "
                f"за припущенням {fmt(ub['module_below_board'])} мм під платою — {fmt(m['q6a_mount']['standoff'] - ub['module_below_board'] - ub['pad_gap'])} мм.",
                f"Cu-блок A: SoC — паста/PTM7950 по плоскій грані; LPDDR5 — прокладка {fmt(cb['ram_pad'])} мм у виїмці {fmt(cb['ram_recess'])} мм. Кріплення блока й вентилятора — TBD.",
                f"П'єдестал: прокладка {fmt(lp['pad'])} мм, зазор {fmt(lp['pad_gap'])} задає висота кріплення картки M.2; гвинти M3 з тильного боку пластини."])
    # Lime pedestal: top view and side view
    w, h = lp["rect"][2], lp["rect"][3]
    oy = 85.0
    sh.rect(0, oy, w, h, "CUT")
    sh.label((0, oy + h + 2), f"П'єдестал Lime {fmt(w)} x {fmt(h)} x {fmt(lp['h'])}, вид згори", 2.4)
    for hx in (5, w - 5):
        sh.hole((hx, oy + h / 2), 2.5, "M3", 2.0)
    sh.dim_h(0, w, oy, oy - 4)
    sh.dim_v(oy, oy + h, w, w + 5)
    sh.dim_h(0, 5, oy + h, oy + h + 4)
    sh.rect(0, oy - 20, w, lp["h"], "CUT")
    sh.dim_v(oy - 20, oy - 20 + lp["h"], 0, -4)
    sh.label((w + 3, oy - 20), "вид збоку; M3 різьба наскрізна", 2.0)
    # UFS boss
    cw, ch = ub["contact"]
    hb = m["q6a_mount"]["standoff"] - ub["module_below_board"] - ub["pad_gap"]
    bx = 95.0
    sh.rect(bx, oy, cw, ch, "CUT")
    for s in (-1, 1):
        sh.hole((bx + cw / 2 + s * 5.0, oy + ch / 2), 2.05, None)
    sh.label((bx, oy + ch + 2), f"Бобишка UFS {fmt(cw)} x {fmt(ch)} x {fmt(hb)}; 2 x M2.5", 2.4)
    sh.dim_h(bx, bx + cw, oy, oy - 4)
    sh.dim_v(oy, oy + ch, bx + cw, bx + cw + 5)
    sh.dim_h(bx + cw / 2 - 5.0, bx + cw / 2 + 5.0, oy + ch / 2, oy + ch + 7)
    sh.rect(bx, oy - 20, cw, hb, "CUT")
    sh.dim_v(oy - 20, oy - 20 + hb, bx, bx - 4)
    # Cu block: top view (board u/v orientation) and side view
    (u0, v0), (bw, bh), (rx, ry, rw_, rh_), (sx, sy, sw, sh_) = cu_block_geometry(P)
    sh.rect(0, 0, bw, bh, "CUT")
    sh.rect(rx, ry, rw_, rh_, "CUT")
    sh.rect(sx, sy, sw, sh_, "HIDDEN")
    sh.label((rx + 1, ry + 1), "виїмка", 1.8)
    sh.label((sx + 1, sy + 1), "SoC", 1.8)
    sh.label((0, bh + 2), f"Cu-блок A {fmt(bw)} x {fmt(bh)} x {fmt(cb['t'])}, вид з боку плати", 2.4, [(0, bh + 6)])
    sh.dim_h(0, bw, 0, -4)
    sh.dim_v(0, bh, bw, bw + 5)
    sh.dim_v(ry, ry + rh_, rx, -6)
    ox = bw + 40.0
    sh.poly([(ox, 0), (ox + bh, 0), (ox + bh, cb["t"]), (ox, cb["t"])], True, "CUT")
    sh.rect(ox + ry, 0, rh_, cb["ram_recess"], "HIDDEN")
    sh.dim_v(0, cb["t"], ox + bh, ox + bh + 4)
    sh.label((ox, cb["t"] + 2), f"вид збоку: виїмка {fmt(cb['ram_recess'])} мм", 2.0)
    if vendor_fit:
        sh.notes.append(f"vendor-fit: SoC top {vendor_fit.get('soc_top', '?')} мм, LPDDR5 top {vendor_fit.get('lpddr5_top', '?')} мм над платою (STEP V1.21).")
    return sh


def hfplus_can_sheet(P):
    p = P.parts["hfplus_can"]
    L, Wd, Hh = p["body"]
    sh = Sheet("M-11", "Екран HF+ (Schubert Art. 6B): свердління", "розгортка бічних стінок 1:1", (420.0, 297.0), 1.0, (40.0, 60.0),
               "жерсть 0.5 мм (Schubert 6B)",
               ["Вводи: 2 коаксіальні (K401 HF, K402 VHF) і пігтейл micro-USB HF+; прохідні конденсатори живлення — тип і діаметр TBD (STACK 2.10).",
                "4 лапки з отворами M3 — до пластини, контакт по голому металу; кришки екрана паяні у 4 точках мінімум.",
                "Розміри корпусу 111 x 55 x 20 (components/tinplate_hf_can_lc_mix_31_on_vbus.md)."])
    sh.rect(0, 0, L, Hh, "CUT")
    sh.text((0, Hh + 2), "довга стінка (до РЧ-плати)", 2.4)
    for i, (lab, xx) in enumerate((("K401 HF", 20.0), ("K402 VHF", 40.0))):
        sh.hole((xx, Hh / 2), 4.2, lab + " ⌀4.2 (RG316 + втулка)", 2.0)
    sh.hole((90.0, Hh / 2), 8.0, "micro-USB пігтейл ⌀8", 2.0)
    sh.rect(0, 40, Wd, Hh, "CUT")
    sh.text((0, 40 + Hh + 2), "торцева стінка: прохідні C (TBD)", 2.4)
    for xx in (15.0, 35.0):
        sh.hole((xx, 40 + Hh / 2), 3.0, "пілот TBD", 1.8)
    for (x, y) in ((0, 80), (L - 12, 80)):
        sh.rect(x, y, 12, 8, "CUT")
        sh.hole((x + 6, y + 4), 3.4, None)
    sh.text((0, 92), "лапки кріплення (4 шт., жерсть 0.5, припаяти до стінок)", 2.2)
    sh.dim_h(0, L, 0, -6)
    sh.dim_v(0, Hh, 0, -6)
    return sh


def bezel_sheet(P):
    m = P.mech
    g = m["display"]["glass_pocket"]
    d = P.parts["display_module"]
    sh = Sheet("M-12", "Безель і вікно дисплея (параметрично)", "переріз скла/VHB/притискачів, 1:1; розміри перевірити на отриманій панелі",
               (420.0, 297.0), 1.0, (30.0, 60.0), "ASA (лице), VHB 4910 1.0 мм",
               ["Скло вклеєне зсередини на суцільну смугу VHB 1.0 мм (ущільнення вікна); 4 притискачі ззаду тримають пакет.",
                f"Вікно = активна зона {fmt(d['active'][0])} x {fmt(d['active'][1])} (більше з двох значень лістингу) + {fmt(m['display']['window_margin'])} на бік.",
                "Скло 164.22 x 97.98 — з лістингу; товщина пакета 6.0 — припущення (TBD). Запас 4D 4DHDMI-70: параметри замінити з даташита 4D до друку.",
                "Положення активної зони відносно скла прийнято центральним — ворота: перемір панелі (STACK D5)."])
    W, H = P.outer[0], P.outer[1]
    sh.rrect(0, 0, W, H, m["outer"]["corner_r"], "THIN")
    sh.rect(g[0], g[1], g[2], g[3], "CUT")
    a = d["active"]
    mg = m["display"]["window_margin"]
    cx, cy = g[0] + g[2] / 2, g[1] + g[3] / 2
    sh.rrect(cx - a[0] / 2 - mg, cy - a[1] / 2 - mg, a[0] + 2 * mg, a[1] + 2 * mg, m["display"]["window_r"], "CUT")
    for (bx, by) in m["display"]["clamp_bosses"]:
        sh.hole((bx, by), 2.5, None)
        sh.circle((bx, by), m["display"]["clamp"]["boss_d"] / 2, "HIDDEN")
    vt = 8.0
    sh.rect(g[0] + 1, g[1] + 1, g[2] - 2, vt, "HIDDEN")
    sh.text((g[0] + 3, g[1] + 3), "смуга VHB 8 мм по периметру скла", 2.0)
    sh.dim_h(g[0], g[0] + g[2], g[1], g[1] - 8)
    sh.dim_v(g[1], g[1] + g[3], g[0], g[0] - 8)
    sh.dim_h(cx - a[0] / 2 - mg, cx + a[0] / 2 + mg, g[1] + g[3], g[1] + g[3] + 6)
    return sh


def seam_sheet(P):
    m = P.mech
    gk = m["gasket"]
    sq = 1 - gk["groove_depth"] / gk["cord_d"]
    fill = (math.pi * gk["cord_d"] ** 2 / 4) / (gk["groove_w"] * gk["groove_depth"])
    hx, hy, hw, hh = m["rear_face"]["hatch"]["rect"]
    seat = m["rear_face"]["hatch"]["seat"]
    hatch_len = 2 * (hw + seat) + 2 * (hh + seat)
    sh = Sheet("M-13", "Шов корпусу і лючок: паз ущільнення", "переріз 5:1", (297.0, 210.0), 5.0, (60.0, 90.0),
               "ASA + EPDM-шнур ⌀3.0 (70 Shore A)",
               [f"Паз {fmt(gk['groove_w'])} x {fmt(gk['groove_depth'])} мм; шнур ⌀{fmt(gk['cord_d'])}: стиск {fmt(sq * 100, 0)} %, заповнення {fmt(fill * 100, 0)} %",
                "(правило статичного ущільнення 15-30 % стиску, ≤85 % заповнення — parts.json oring_groove_rule).",
                "Шнур укласти без натягу, стик — внизу посередині, торці склеїти; кути паза R ≥ 9 мм.",
                f"Лючок: той самий переріз паза в кришці лючка, шнур близько {fmt(hatch_len, 0)} мм; довжина шнура шва — fit-report 'gasket'.",
                "Гвинти M3 ISO 14580 з ущільнювальною шайбою під головкою; IPX4 — ворота T-07 OPEN."])
    rw, rh = gk["rim_w"], gk["rim_h"]
    t = m["wall"]
    sh.poly([(0, 0), (rw, 0), (rw, rh), (t, rh), (t, rh + 8), (0, rh + 8)], True, "CUT")
    gx = (rw - gk["groove_w"]) / 2
    sh.rect(gx, 0, gk["groove_w"], gk["groove_depth"], "CUT")
    sh.circle((gx + gk["groove_w"] / 2, gk["groove_depth"] - gk["cord_d"] / 2), gk["cord_d"] / 2, "HIDDEN")
    sh.poly([(0, 0), (rw, 0), (rw, -4), (t, -4), (t, -10), (0, -10)], True, "CUT")
    sh.label((rw + 1, 2), "передня оболонка (паз)", 2.2)
    sh.label((rw + 1, -6), "задня оболонка (площина)", 2.2)
    sh.label((rw + 1, -1.2), "шнур ⌀3 до стиску (пунктир)", 1.8)
    sh.dim_h(gx, gx + gk["groove_w"], 0, gk["groove_depth"] + 1.2)
    sh.dim_v(0, gk["groove_depth"], gx, gx - 1.5)
    return sh
