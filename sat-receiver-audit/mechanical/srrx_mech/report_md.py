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
        f"- антенні деталі за правилом розміру: FAIL {s['antenna_rule_failures']}; площа плат (курт'ярди KiCad, деталі без роз'ємів джгутів): "
        f"OPEN {s.get('board_area_open', s['board_area_failures'])}; з роз'ємами джгутів build/16: OPEN {s.get('board_area_harness_open', 0)} "
        "(MODEL ESTIMATE, не в гейті; рішення — розбиття й розкладка плат)",
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
            f"Внутрішній розмір кришки {_r(bp['inner_mm'][0])} x {_r(bp['inner_mm'][1])} мм, зазор {_r(bp['clearance_mm'])} мм; резерви: "
            f"V4L {_r(bp['v4l_reserve'])} ({bp['v4l_status']}), розетка на носійній платі {_r(bp['socket_reserve'])} ({bp['socket_part']}), "
            f"корпус LNA {_r(bp['lna_case'])}.", "",
            "| варіант | розкладка | ряд, мм | висота, мм | запас ряду / висоти, мм | вміщується |", "|---|---|---|---|---|---|"]
    for k, a in bp["arrangements"].items():
        mark = " (обрано)" if k == bp["chosen"] else ""
        out.append(f"| ({k}){mark} | {a['title']} | {_r(a['row_mm'])} | {_r(a['height_mm'])} | {_r(a['spare_row_mm'])} / {_r(a['spare_height_mm'])} | "
                   f"{'так' if a['fits'] else 'ні'}{'; ' + a['note'] if a.get('note') else ''} |")
    out += ["", f"Не враховано: {bp['not_included']}.", "", f"Результат: {bp['result']}", ""]
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
    ba = report.get("board_area", {})
    if ba.get("boards"):
        wh = ba.get("with_harness", {})
        out += ["## Площа плат: курт'ярди KiCad і роз'єми джгутів (MODEL ESTIMATE)", "",
                f"Джерело: {ba.get('source', '')}. Метод: {ba['method']}; роз'єми: {wh.get('method', '')}.", "",
                ba.get("status", "") + "; " + wh.get("status", ""), "",
                "| плата | контур, мм² | курт'ярди деталей, мм² | з них модулі (×1.0), мм² | потреба ×1.5 / ×1.8, мм² | результат | роз'ємів джгутів | "
                "курт'ярди роз'ємів, мм² | з роз'ємами ×1.5 / ×1.8, мм² | ширина роз'ємів / крайові зони, мм | результат |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        whb = wh.get("boards", {})
        for bid in P.boards["boards"]:
            p_, h_ = ba["boards"].get(bid, {}), whb.get(bid, {})
            if not p_ and not h_:
                continue
            need = f"{_r(p_['need_1_5_mm2'])} / {_r(p_['need_1_8_mm2'])}" if p_.get("need_1_5_mm2") is not None else "—"
            hneed = (f"{_r(h_['estimate_with_headers_1_5_mm2'])} / {_r(h_['estimate_with_headers_mm2'])}"
                     if h_.get("estimate_with_headers_1_5_mm2") is not None else "—")
            out.append(f"| {bid} | {_r(p_.get('area_mm2', h_.get('area_mm2', 0)))} | {_r(p_['courtyard_raw_mm2']) if p_ else '—'} | "
                       f"{_r(p_['modules_mm2']) if p_ else '—'} | {need} | {p_.get('result', '—')} | {h_.get('headers', '—')} | "
                       f"{_r(h_['header_courtyard_mm2']) if h_ else '—'} | {hneed} | "
                       f"{(_r(h_['frontage_mm']) + ' / ' + _r(h_['edge_zones_mm'])) if h_ else '—'} | {h_.get('result', '—')} |")
        out += ["", "Курт'ярди деталей за групами схем (design/E*.json «group»), мм²: курт'ярди (потреба ×1.5 / ×1.8):", ""]
        for bid, p_ in ba["boards"].items():
            nd = p_.get("per_group_need_mm2", {})
            out.append(f"- {bid}: " + "; ".join(f"{g} {_r(v)}" + (f" ({_r(nd[g][0])} / {_r(nd[g][1])})" if g in nd else "")
                                               for g, v in p_.get("per_group_raw_mm2", {}).items()))
        if wh.get("counted_with_parts"):
            out.append(f"- роз'єми, що вже є деталями плати (пораховано раз): {', '.join(wh['counted_with_parts'])}")
        out.append("")
    bz = report.get("board_zones")
    if bz:
        out += ["## Зони висоти CTRL і RF (карта вільної висоти, модель)", "",
                "Вільна висота від площини компонентів (лице) і від тильної площини плати до найближчого конверту, деталі конструкції, фланця "
                "кнопки або стінки; «вміщує» = вільна − 0.5 мм. Координати — від лівого нижнього кута контуру плати (boards.json). "
                "Ті самі списки записано в boards.json (height_zones / rear_zones) і в contract/boards.json.", "",
                "| плата | бік | x, y, ш x в, мм | вільна, мм | вміщує, мм | обмежує |", "|---|---|---|---|---|---|"]
        for bid, m in bz.items():
            for side, zones in m.items():
                for z in zones:
                    if z["rect"][2] < 0.05 or z["rect"][3] < 0.05:
                        continue
                    x, y, w, h = z["rect"]
                    out.append(f"| {bid} | {'лице' if side == 'front' else 'тил'} | {_r(x)}, {_r(y)}, {_r(w)} x {_r(h)} | {_r(z['free_mm'])} | "
                               f"{_r(z['fits_mm'])} | {z['limit']} |")
        hr = next((r for r in report["rules"] if r["id"] == "R-HDR-HEIGHT"), None)
        if hr and hr.get("headers"):
            rows = [x for x in hr["headers"] if x["verdict"] != "inside the board limit"]
            out += ["", f"Роз'єми джгутів понад обмеження плати або без прочитаної висоти ({len(rows)} з {len(hr['headers'])}; правило R-HDR-HEIGHT). "
                    "Висота — з'єднаної пари (вилка + кабельна частина), де її прочитано, інакше корпусу вилки (позначено); вихід дроту за "
                    "кабельною частиною не враховано (дріт TBD, AI-WIRE-PTFE). Для Micro-Fit понад межу наведено й кутову 43650 (MF_ra):", "",
                    "| роз'єм | плата | родина | висота, мм | курт'ярд, мм | межа плати | найкраща зона лиця / тилу, мм | кутова 43650: висота, курт'ярд, зони лиця / тилу, мм | висновок |",
                    "|---|---|---|---|---|---|---|---|---|"]
            basis = {"mated": "пара", "body": "корпус"}
            for x in rows:
                cyd = " x ".join(_r(v) for v in x["courtyard_mm"]) if x.get("courtyard_mm") else "—"
                hb = f" ({basis[x['h_basis']]})" if x.get("h_basis") in basis else ""
                a = x.get("alternative")
                alt = (f"{_r(a['h_mm'])} ({basis.get(a['h_basis'], a['h_basis'])}); {' x '.join(_r(v) for v in a['courtyard_mm']) if a.get('courtyard_mm') else '—'}; "
                       f"{_r(a['best_front_zone_mm'])} / {_r(a['best_rear_zone_mm'])}") if a else "—"
                out.append(f"| {x['connector']} | {x['board']} | {x['family']} {x['orientation']} | {_r(x['h_mm']) + hb if x['h_mm'] is not None else 'TBD'} | "
                           f"{cyd} | {_r(x['max_height'])} | {_r(x['best_front_zone_mm'])} / {_r(x['best_rear_zone_mm'])} | {alt} | {x['verdict']} |")
        out.append("")
    rt = report.get("harness_routes")
    if rt:
        pb = rt["pps"]
        out += ["## Траси джгутів (модель, generated/harness-routes.json)", "",
                "Осьова лінія кожного сегмента build/16 крізь модель корпусу (mechanical.json harness_routes): довжина = ламана + запас на вигини "
                "(половина діаметра джгута × кут) + 2 × 15 мм сервісних петель, округлено вгору до 1 мм. Діаметр джгута — верхня межа за "
                "кількістю жил build/16 і найбільшою ізоляцією, яку беруть клеми (дріт не обрано, AI-WIRE-PTFE). Кінці на крайових зонах плат "
                "і біля модулів без конверту — попередні (OPEN), доки немає позицій роз'ємів. MODEL ESTIMATE, не виміряні довжини.", "",
                f"PPS (R-PPS-LEN): {'+'.join(pb['via_segments'])} = {pb.get('via_segments_mm')} мм проти {_r(pb['limit_mm'])} мм"
                + (f"; рішення — {pb['decision']}; гілка {pb['branch']} = {pb.get('branch_mm')} мм" if "branch" in pb else "") + ".", "",
                "| сегмент | тип | довжина, мм | ламана, мм | вигинів | ⌀ джгута, мм | прорізи | стан |", "|---|---|---|---|---|---|---|---|"]
        for sid, r in list(rt["segments"].items()) + [(f"{k} (гілка)", v) for k, v in rt["branches"].items()]:
            out.append(f"| {sid} | {r.get('kind', '')} | {r.get('length_mm') if r.get('length_mm') is not None else '—'} | "
                       f"{_r(r['path_mm']) if 'path_mm' in r else '—'} | {r.get('bends', '—')} | {_r(r['bundle_od_mm']) if 'bundle_od_mm' in r else '—'} | "
                       f"{', '.join(r.get('through', [])) or '—'} | {r['status']} |")
        out += ["", "Прорізи пластини: " + "; ".join(
            f"{k} — у plate.slots {len(v['listed'])}, трасами {len(v['routed'])}"
            + (f", поза списком: {', '.join(v['routed_not_listed'])}" if v["routed_not_listed"] else "")
            + (f", без траси: {', '.join(v['listed_not_routed'])}" if v["listed_not_routed"] else "") for k, v in rt["slots"].items()) + ".", ""]
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
