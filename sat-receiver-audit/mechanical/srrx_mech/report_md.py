"""Human-readable fit report (Ukrainian Markdown) generated from the same data as fit-report.json."""
from .geom2d import fmt
from .layout import item_boxes


def _r(v):
    if isinstance(v, (list, tuple)):
        return " / ".join(_r(x) for x in v)
    if isinstance(v, (int, float)):
        return fmt(v, 2)
    return str(v)


def render(P, report, params_short, boards_contract):
    e = report["envelope"]
    s = report["summary"]
    out = [
        "# Звіт посадки механічної моделі SR-RX-v2.1",
        "",
        f"Згенеровано `mechanical/build.py` (params {params_short}); не редагувати вручну. **MODEL FIT ONLY:** це перевірка конвертів і "
        "даних з даташитів, а не примірка деталей. Фізичні ворота посадки, ущільнення, тепла й падіння лишаються OPEN.",
        "",
        "## Габарит",
        "",
        "| | модель | D15 |",
        "|---|---|---|",
        f"| Ш x В x Г, мм | {_r(e['model'][0])} x {_r(e['model'][1])} x {_r(e['model'][2])} | {_r(e['d15'][0])} x {_r(e['d15'][1])} x {_r(e['d15'][2])} |",
        f"| об'єм, L | {_r(e['volume_l'])} | {_r(e['volume_l_d15'])} |",
        f"| поверхня, m² | {fmt(e['surface_m2'], 4)} | {fmt(e['surface_m2_d15'], 4)} |",
        f"| лице, m² | {fmt(e['front_m2'], 4)} | {fmt(e['d15'][0] * e['d15'][1] / 1e6, 4)} |",
        f"| над поясом шва, мм | {_r(e['over_seam_belt'][0])} x {_r(e['over_seam_belt'][1])} x {_r(e['over_seam_belt'][2])} | — |",
        f"| мішок 23 x 30 см (W+D ≤ 300, H+D ≤ 230; D — глибина закритого пристрою з усіма виступами"
        f"{', ' + _r(e['fire_bag_23x30cm']['depth_mm']) + ' мм' if 'depth_mm' in e['fire_bag_23x30cm'] else ''}) | "
        f"{_r(e['fire_bag_23x30cm']['w_plus_d'])} / {_r(e['fire_bag_23x30cm']['h_plus_d'])}: {e['fire_bag_23x30cm']['result']} | — |",
        "",
        "## Підсумок",
        "",
        f"- зіткнень конвертів: {s['collisions']}; поза внутрішнім об'ємом: {s['outside']}",
        f"- правила: FAIL {s['rule_failures']}, OPEN {s['rules_open']} (OPEN = потрібна обрана або виміряна деталь)",
        f"- антенні деталі за правилом розміру: FAIL {s['antenna_rule_failures']}; площа плат: FAIL {s['board_area_failures']}",
        f"- термоінтерфейси: FAIL {s['thermal_failures']}, OPEN {s['thermal_open']}; ущільнення: {s['gasket']}",
        f"- звірка з STEP постачальника: {s['vendor_fit']}",
        f"- перетини тіл B-rep (оболонки, пластина, кутники, РЧ-відсік, лоток) з конвертами: {s.get('solid_conflicts')}; "
        f"деталі з кількох тіл («висячі» елементи): {len(s.get('disconnected_parts') or [])}",
        "",
        "## Правила (build/05 §6, STACK 5.8)",
        "",
        "| ID | правило | значення, мм | межа | результат |",
        "|---|---|---|---|---|",
    ]
    cb = e.get("closed_bbox_mm")
    if cb:
        i = out.index("## Підсумок")
        out[i:i] = ["Глибина закритого пристрою (козирок складено, штекери вийнято), z від задньої зовнішньої грані:", ""] + [
            f"- {k}: z {_r(v)}" for k, v in list(cb["rear_protrusions_z"].items()) + list(cb["front_protrusions_z"].items())] + [
            "", f"Разом z {_r(cb['z'][0])}…{_r(cb['z'][1])}; без тримача T7 — {_r(e['fire_bag_23x30cm']['depth_without_t7_holder_mm'])} мм. "
            f"Не враховано: {cb['note']}.", ""]
    for r in report["rules"]:
        out.append(f"| {r['id']} | {r['rule']} | {_r(r.get('value_mm', ''))} | {_r(r.get('limit_mm', ''))} | {r['result']} |")
    bp = report["rf_bay_packing"]
    out += ["", "## РЧ-відсік: донгли V4L, розетки USB-подовжувачів і модулі LNA", "",
            f"Внутрішній розмір кришки {_r(bp['inner_mm'][0])} x {_r(bp['inner_mm'][1])} мм; резерви: V4L {_r(bp['v4l_reserve'])}, "
            f"розетка {_r(bp['socket_reserve'])} (припущення), корпус LNA {_r(bp['lna_case'])}.", ""]
    for k, v in bp["rows_mm"].items():
        out.append(f"- {k}: ряд {_r(v)} мм")
    out += [f"- висота двох рядів у варіанті «донгл + розетка + LNA»: {_r(bp['alternative_height_mm'])} мм", "", f"Результат: {bp['result']}", ""]
    t = report["thermal_interfaces"]
    out += ["## Термоінтерфейси (Gelid GP-Ultimate)", "", t["rule"], "",
            "| ID | де | середовище | зазор ± допуск, мм | прокладка | стиск | виріз, мм | результат |",
            "|---|---|---|---|---|---|---|---|"]
    for r in t["rows"]:
        gap = f"{_r(r['design_gap_mm'])} ± {_r(r['gap_tol_mm'])}" if "gap_tol_mm" in r else "—"
        pad = f"{_r(r['pad_mm'])} ({r['sku']})" if r.get("pad_mm") else "—"
        comp = f"{fmt(r['compression'][0] * 100, 0)}-{fmt(r['compression'][1] * 100, 0)} %" if r.get("compression") else "—"
        cut = f"{_r(r['cut_mm'][0])} x {_r(r['cut_mm'][1])}" if r.get("cut_mm") else "—"
        out.append(f"| {r['id']} | {r['where']} | {r['medium']} | {gap} | {pad} | {comp} | {cut} | {r['result']} |")
    out += ["", "Розкрій листів 90 x 50:", ""]
    for th, d in t["cuts_per_thickness"].items():
        pcs = ", ".join(f"{p['id']} {_r(p['size'][0])}x{_r(p['size'][1])} (лист {p['sheet']})" for p in d["pieces"])
        out.append(f"- {th} мм: {d['sheets_90x50']} лист(и): {pcs}")
    g = report["gasket"]
    cl = g["closure"]
    out += ["", "## Ущільнення шва і гвинти", "",
            f"EPDM-шнур ⌀{_r(g['cord_d'])} у пазу {_r(g['groove'][0])} x {_r(g['groove'][1])} у зовнішньому поясі {_r(g['belt_mm'])} мм: "
            f"стиск {fmt(g['squeeze'] * 100, 0)} %, заповнення {fmt(g['fill'] * 100, 0)} % — {g['result']}; довжина по осі паза {_r(g['cord_length_mm'])} мм, "
            f"замовити {g['cord_order_mm']} мм.", "",
            f"Гвинтів шва {cl['screws']}, середній проліт {_r(cl['mean_span_mm'])} мм, найдовший {_r(cl['max_span_mm'])} мм (лівий нижній кут: "
            "батарея й екран HF+ доходять до стінок, бобишка не вміщується; рішення — стенд T-07). Доступ інструмента до кожного гвинта — "
            "рядок R-TOOL-ACCESS (гвинти 1 і 2 — після зняття тримача T7, який кріпиться ззовні).", ""]
    si = report.get("solid_interference")
    if si:
        out += ["## Перетини тіл (B-rep)", "", si["method"] + ".", "", f"Результат: {si['result']}.", ""]
        for c in si["conflicts"]:
            out.append(f"- {c['item']} ↔ {c['solid']}: {_r(c['overlap_mm3'])} мм³, {c['bbox_mm']}")
        if si["by_design"]:
            out += ["", "Перетини за задумом (плата на стійках, Lime на п'єдесталі тощо):", ""]
            for c in si["by_design"]:
                out.append(f"- {c['item']} ↔ {c['solid']}: {_r(c['overlap_mm3'])} мм³")
        out.append("")
    if report["tight_below_0_5mm"]:
        out += ["## Тісні місця (зазор < 0.5 мм, модель)", ""]
        for c in report["tight_below_0_5mm"]:
            out.append(f"- {c['a']} ↔ {c['b']}: {_r(c['gap_mm'])} мм")
        out.append("")
    bc = boards_contract
    out += ["## Плати: механічний інтерфейс (contract/boards.json)", "",
            "| плата | домени pcb/prepare.py | контур, мм² | отвори | висота деталей | розміщення | кріплення |", "|---|---|---|---|---|---|---|"]
    for bid, b in bc["boards"].items():
        pl = "; ".join(f"{k}: ({_r(v['origin'][0])}, {_r(v['origin'][1])}) z {_r(v['z_bottom'])} {v['facing']}" for k, v in b["placements"].items())
        out.append(f"| {bid} | {', '.join(b['domains'])} | {_r(b['area_mm2'])} | {len(b['holes_mm'])} x ⌀{_r(b['hole_d'])} | ≤{_r(b['max_component_height'])} | {pl} | {b['mount']} |")
    out.append("")
    out += ["## Розташування конвертів (мм; x вправо, y вгору з лиця, z від задньої зовнішньої грані)", "",
            "| ID | деталь / плата | x | y | z | кріплення |", "|---|---|---|---|---|---|"]
    for iid, name, bx, it in item_boxes(P):
        what = it.get("part") or it.get("board") or ("резерв (порожньо)" if it.get("keep_clear") else "—")
        out.append(f"| {name} | {what} | {_r(bx[0])}-{_r(bx[3])} | {_r(bx[1])}-{_r(bx[4])} | {_r(bx[2])}-{_r(bx[5])} | {it.get('mount', '')} |")
    if "printed_mass_upper_bound_g" in report:
        m = report["printed_mass_upper_bound_g"]
        out += ["", "## Друковані деталі: верхня межа маси", "", m["rule"], "", "| деталь | об'єм, cm³ | g (суцільна) |", "|---|---|---|"]
        for k, v in m["parts"].items():
            out.append(f"| {k} | {_r(report['volumes_cm3'][k]['cm3'])} | {_r(v)} |")
    out.append("")
    return ("\n".join(out)).encode("utf-8")
