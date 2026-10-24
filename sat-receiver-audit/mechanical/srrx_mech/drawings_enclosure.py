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
    m = P.mech
    pl = m["plate"]
    sh = Sheet("M-07", "Середня пластина (шасі), шаблон 1:1", "лазер/фрезер; отвори ±0.2; площинність ≤0.2 під Q6A, п'єдесталом і регуляторами; різьбу не нарізати",
               (420.0, 297.0), 1.0, (25.0, 70.0), pl["material"],
               ["Контур і отвори — з mechanical/params; DXF того самого аркуша — для різання.",
                "Отвори кріплення плат: M3 — самозатискні гайки врівень (MPN TBD, MECH-04); M2.5 для Q6A — наскрізні з гайкою.",
                "Ребра шляху 2 (смуги Al 1 x 3.5) — на передній грані під HDMI-платою, уздовж потоку; точки з'єднання — голий метал."])
    x, y, w, h = pl["main"]
    ex, ey, ew, eh = pl["ext"]
    pts = [(x, y), (ex, y), (ex, ey), (ex + ew, ey), (x + w, y + h), (x, y + h)]
    sh.poly(pts, True, "CUT")
    for (bx, by) in pl["mount_bosses"]:
        sh.hole((bx, by), pl["mount_hole_d"], None)
    rw = pl["riser_window"]
    sh.rect(rw[0], rw[1], rw[2], rw[3], "CUT")
    sh.text((rw[0], rw[1] + rw[3] + 1), "вікно riser R44SF", 2.0)
    hs = pl["hdmi_slot"]
    sh.rrect(hs[0], hs[1], hs[2], hs[3], hs[3] / 2, "CUT")
    sh.text((hs[0], hs[1] - 3), "проріз кабелю HDMI", 2.0)
    for bp in pl["bond_points"]:
        sh.hole(tuple(bp["c"]), 3.4, bp["id"], 2.0)
        sh.circle(tuple(bp["c"]), 5.0, "HIDDEN")
    # board fixing holes in plate coordinates
    for bid, b in P.boards["boards"].items():
        if bid not in ("PWR", "RF"):
            continue
        ox, oy = b["place"]["origin"]
        for hx, hy in b["holes"]:
            sh.hole((ox + hx, oy + hy), 3.4 if bid == "RF" else 3.4, None)
        sh.poly([(ox + px, oy + py) for px, py in b["outline"]], True, "HIDDEN")
        sh.text((ox + 2, oy + 2), f"плата {bid} (контур, пунктир)", 2.0)
    # Q6A standoffs (M2.5)
    q = P.parts["q6a"]
    x0, y0 = m["q6a_mount"]["origin"]
    e, (pu, pv) = q["holes"]["edge"], q["holes"]["pitch"]
    for u in (e, e + pu):
        for v in (e, e + pv):
            sh.hole((x0 + q["board"][0] - u, y0 + v), 2.9, None)
    sh.rect(x0, y0, q["board"][0], q["board"][1], "HIDDEN")
    sh.text((x0 + 2, y0 + q["board"][1] - 4), "Q6A (з тильного боку), стійки M2.5 x 6", 2.0)
    # angles and pedestal footprint
    lp = m["lime_pedestal"]["rect"]
    sh.rect(lp[0], lp[1], lp[2], lp[3], "HIDDEN")
    sh.text((lp[0] + 1, lp[1] + 1), "п'єдестал Lime (передня грань)", 2.0)
    for (px, py) in ((lp[0] + 5, lp[1] + lp[3] / 2), (lp[0] + lp[2] - 5, lp[1] + lp[3] / 2)):
        sh.hole((px, py), 3.4, None)
    at = m["angles"]["top"]
    for xh in [at["x"][0] + 8 + i * ((at["x"][1] - at["x"][0] - 16) / 4) for i in range(5)]:
        sh.hole((xh, P.outer[1] - m["wall"] - at["leg_plate"] / 2), 3.4, None)
    ar = m["angles"]["right"]
    for yh in (ar["y"][0] + 6, (ar["y"][0] + ar["y"][1]) / 2, ar["y"][1] - 6):
        sh.hole((P.outer[0] - m["wall"] - ar["leg_plate"] / 2, yh), 3.4, None)
    fn = m["fins"]
    n = int((fn["y"][1] - fn["y"][0]) // fn["pitch"]) + 1
    for i in range(n):
        yy = fn["y"][0] + i * fn["pitch"]
        sh.line((fn["x"][0], yy), (fn["x"][1], yy), "HIDDEN")
    sh.dim_h(x, x + w, y + h, y + h + 10)
    sh.dim_v(y, y + h, x, x - 10)
    sh.dim_h(ex, ex + ew, ey, ey - 10)
    sh.dim_v(ey, y, ex + ew, ex + ew + 10)
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
    sh = Sheet("M-09", "РЧ-відсік: розкрій фольгованого FR4", "стінки й кришка, 1:1; шви пропаяти суцільно з обох боків",
               (420.0, 297.0), 1.0, (25.0, 30.0), rb["material"],
               ["Дно відсіку — пластина (Al), верх і правий бік — Al-кутники + стінка корпусу; FR4-стінки — лівий і нижній боки.",
                "Кришка FR4 несе модулі (V4L x2, SAWbird+ NOAA, Flamingo+): отвори M3 за M-09; мідь кришки з'єднати зі стінками пайкою.",
                "Висота стінок = від тильної грані пластини до кришки. Фоторезист зняти перед паянням (STACK 2.9)."])
    sh.rect(0, 200, w, hz, "CUT")
    sh.text((0, 200 + hz + 3), f"Нижня стінка {fmt(w)} x {fmt(hz)}", 2.6)
    sh.rect(0, 150, h, hz, "CUT")
    sh.text((0, 150 + hz + 3), f"Ліва стінка {fmt(h)} x {fmt(hz)}", 2.6)
    for i in range(3):
        sh.rect(10 + i * 30, 200 + hz - 3, 15, 3, "HIDDEN")
    sh.rect(0, 10, w, h, "CUT")
    sh.text((0, 10 + h + 3), f"Кришка {fmt(w)} x {fmt(h)} (несе модулі)", 2.6)
    for it in m["layout"]["items"]:
        if it.get("mount") == "rf_lid":
            bx, by, _, dx, dy, _ = it["box"]
            sh.rect(bx - x, by - y + 10, dx, dy, "HIDDEN")
            sh.text((bx - x + 2, by - y + 12), it["id"], 2.0)
            for hx, hy in ((bx - x + 4, by - y + 10 + dy / 2), (bx - x + dx - 4, by - y + 10 + dy / 2)):
                sh.hole((hx, hy), 3.2, None)
    sh.dim_h(0, w, 10, 4)
    sh.dim_v(10, 10 + h, 0, -8)
    return sh


def pedestal_cooler_sheet(P, vendor_fit=None):
    m = P.mech
    lp = m["lime_pedestal"]
    sh = Sheet("M-10", "П'єдестал Lime, бобишка UFS, мідний блок охолоджувача A", "механічна обробка, 2:1", (420.0, 297.0), 2.0, (25.0, 40.0),
               "Al 6082/5754 (п'єдестал), Cu (блок)",
               ["Висоти ступенів і товщини прокладок — з таблиці зазорів build/05 7.1 (vendor-fit.json); виміряти перед обробкою.",
                "Площинність контактних площин ≤0.05, шорсткість Ra ≤1.6; кромки притупити."])
    w, h = lp["rect"][2], lp["rect"][3]
    sh.rect(0, 60, w, h, "CUT")
    sh.text((0, 60 + h + 2), f"П'єдестал Lime {fmt(w)} x {fmt(h)} x {fmt(lp['h'])} (вид зверху)", 2.4)
    for hx in (5, w - 5):
        sh.hole((hx, 60 + h / 2), 3.4, "M3", 2.0)
    sh.dim_h(0, w, 60, 55)
    sh.dim_v(60, 60 + h, w, w + 6)
    us = m["ufs_boss"]["size"]
    sh.rect(100, 60, us[0], us[1], "CUT")
    sh.text((100, 60 + us[1] + 2), f"Бобишка UFS {fmt(us[0])} x {fmt(us[1])}", 2.4)
    sh.dim_h(100, 100 + us[0], 60, 55)
    # cooler A Cu block: 35 x 35 max, two steps (SoC / LPDDR5)
    q = P.parts["q6a"]
    soc, ram = q["soc"]["uv"], q["lpddr5"]["uv"]
    u0 = min(soc[0], ram[0]) - 1.0
    v0 = min(soc[1], ram[1]) - 1.0
    u1 = max(soc[2], ram[2]) + 1.0
    v1 = max(soc[3], ram[3]) + 1.0
    bw, bh = min(35.0, u1 - u0), min(35.0, v1 - v0)
    sh.rect(0, 0, bw, bh, "CUT")
    sh.rect(soc[0] - u0, soc[1] - v0, soc[2] - soc[0], soc[3] - soc[1], "HIDDEN")
    sh.rect(ram[0] - u0, ram[1] - v0, ram[2] - ram[0], ram[3] - ram[1], "HIDDEN")
    sh.text((0, bh + 2), f"Cu-блок A {fmt(bw)} x {fmt(bh)}: ступінь SoC (паста/PTM7950) і LPDDR5 (прокладка)", 2.4)
    sh.dim_h(0, bw, 0, -5)
    sh.dim_v(0, bh, bw, bw + 6)
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
    sh = Sheet("M-13", "Шов корпусу і лючок: паз ущільнення", "переріз 5:1", (297.0, 210.0), 5.0, (40.0, 60.0),
               "ASA + EPDM-шнур ⌀3.0 (70 Shore A)",
               [f"Паз {fmt(gk['groove_w'])} x {fmt(gk['groove_depth'])} мм; шнур ⌀{fmt(gk['cord_d'])}: стиск {fmt(sq * 100, 0)} %, заповнення {fmt(fill * 100, 0)} %",
                "(правило статичного ущільнення 15-30 % стиску, ≤85 % заповнення — parts.json oring_groove_rule).",
                "Шнур укласти без натягу, стик — внизу посередині, торці склеїти; кути паза R ≥ 9 мм.",
                "Гвинти M3 x 20 ISO 14580 з ущільнювальною шайбою під головкою; IPX4 — ворота T-07 OPEN."])
    rw, rh = gk["rim_w"], gk["rim_h"]
    t = m["wall"]
    sh.poly([(0, 0), (rw, 0), (rw, rh), (t, rh), (t, rh + 10), (0, rh + 10)], True, "CUT")
    gx = (rw - gk["groove_w"]) / 2
    sh.rect(gx, 0, gk["groove_w"], gk["groove_depth"], "CUT")
    sh.circle((gx + gk["groove_w"] / 2, gk["groove_depth"] - gk["cord_d"] / 2), gk["cord_d"] / 2, "HIDDEN")
    sh.poly([(0, 0), (rw, 0), (rw, -4), (t, -4), (t, -12), (0, -12)], True, "CUT")
    sh.text((rw + 1, 2), "передня оболонка (паз)", 2.2)
    sh.text((rw + 1, -6), "задня оболонка (площина)", 2.2)
    sh.dim_h(gx, gx + gk["groove_w"], 0, gk["groove_depth"] + 1.2)
    sh.dim_v(0, gk["groove_depth"], gx, gx - 1.5)
    return sh
