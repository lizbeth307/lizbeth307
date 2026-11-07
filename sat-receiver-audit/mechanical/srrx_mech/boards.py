"""Board mechanical contract (JSON for pcb/ generators) and Edge.Cuts DXF per board."""
from .geom2d import Sheet, fmt


def poly_area(pts):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def board_sheet(P, bid):
    b = P.boards["boards"][bid]
    sh = Sheet(f"B-{bid}", f"Плата {bid}: контур Edge.Cuts і кріпильні отвори", b["name"], (420.0, 297.0), 1.0, (40.0, 60.0),
               "FR-4, 4 шари, 1.6 мм (build/15)",
               ["Координати — від лівого нижнього кута контуру, вид з боку компонентів (деталі лише зверху, build/15).",
                f"Отвори ⌀{fmt(b['hole_d'])}, зона заборони міді/деталей ⌀{fmt(b['hole_keepout_d'])}; висота деталей ≤{fmt(b['max_height'])} мм.",
                f"Кріплення: {b['place']['mount']}" + (f"; гвинт {b['screw']}" if b.get("screw") else "") + ".",
                "boards/<id>-edge-cuts.dxf — лише контур (CUT) і отвори (HOLE) для KiCad Edge.Cuts; 1 одиниця = 1 мм.",
                "Пунктир: зони термопрокладок, модулі на платі, перемикачі/енкодер; рамки по краях — зони роз'ємів (contract/boards.json)."])
    for (x, y, w, h) in b.get("thermal_bond", []):
        sh.rect(x, y, w, h, "HIDDEN")
        sh.label((x + 1, y + h - 3), "термопрокладка", 1.6)
    xs0 = [p[0] for p in b["outline"]]
    ys0 = [p[1] for p in b["outline"]]
    for i, ez in enumerate(b.get("edge_zones", [])):
        a0, a1 = ez["span"]
        if ez["edge"] == "bottom":
            sh.line((a0, min(ys0) - 2), (a1, min(ys0) - 2), "CENTER")
            sh.label((a0, min(ys0) - 5.5 - 3.5 * i), f"E{i + 1}: {ez['use'][:70]}", 1.6)
        elif ez["edge"] == "top":
            yt = ez.get("at", max(ys0))      # 'at': an inner top edge of a stepped outline (PWR bottom strip)
            sh.line((a0, yt + 2), (a1, yt + 2), "CENTER")
            sh.label((a0, yt + 3.5 + 3.5 * i), f"E{i + 1}: {ez['use'][:70]}", 1.6)
        elif ez["edge"] in ("left", "right"):
            x = min(xs0) - 2 if ez["edge"] == "left" else max(xs0) + 2
            sh.line((x, a0), (x, a1), "CENTER")
            sh.label((x + (1.0 if ez["edge"] == "right" else -60.0), a1 + 1.0 + 3.5 * i), f"E{i + 1}: {ez['use'][:60]}", 1.6)
    sh.poly([tuple(p) for p in b["outline"]], True, "CUT")
    for (x, y, w, h) in b.get("cutouts", []):
        sh.rect(x, y, w, h, "CUT")
    for (hx, hy) in b["holes"]:
        sh.hole((hx, hy), b["hole_d"], f"{fmt(hx)},{fmt(hy)}", 1.8)
        sh.circle((hx, hy), b["hole_keepout_d"] / 2, "HIDDEN")
    for sw in b.get("switches", []):
        sh.rect(sw[0] - 3.225, sw[1] - 3.225, 6.45, 6.45, "HIDDEN")
    if "encoder_at" in b:
        ex, ey = b["encoder_at"]
        sh.rect(ex - 6.25, ey - 6.7, 12.5, 13.4, "HIDDEN")
        sh.center_mark((ex, ey), 5)
    for mo in b.get("modules_on_board", []):
        pw, ph = P.parts[mo["part"]]["size"][:2]
        sh.rect(mo["at"][0], mo["at"][1], pw, ph, "HIDDEN")
        sh.text((mo["at"][0] + 1, mo["at"][1] + 1), mo["id"], 1.8)
    xs = [p[0] for p in b["outline"]]
    ys = [p[1] for p in b["outline"]]
    sh.dim_h(min(xs), max(xs), min(ys), min(ys) - 8)
    sh.dim_v(min(ys), max(ys), min(xs), min(xs) - 8)
    return sh


def contract(P):
    """Absolute placement of every board for the pcb/ generators and the CAD job."""
    out = {"schema": "srrx-board-mech-contract-v1", "status": "MODEL_FIT_ONLY",
           "source": "mechanical/params/boards.json + mechanical.json", "stackup": P.boards["stackup"], "boards": {}}
    for bid, b in P.boards["boards"].items():
        places = {k: v for k, v in b.get("place_at", {}).items()} or {"": b["place"]["origin"]}
        area = poly_area([tuple(p) for p in b["outline"]]) - sum(c[2] * c[3] for c in b.get("cutouts", []))
        out["boards"][bid] = {
            "name": b["name"], "domains": b["domains"],
            "outline_mm": b["outline"], "cutouts_mm": b.get("cutouts", []), "area_mm2": round(area, 1),
            "holes_mm": b["holes"], "hole_d": b["hole_d"], "hole_keepout_d": b["hole_keepout_d"],
            "max_component_height": b["max_height"],
            "placements": {k or "default": {"origin": v, "z_bottom": b["place"]["z_bottom"], "facing": b["place"]["facing"]} for k, v in places.items()},
            "mount": b["place"]["mount"], "edge_zones": b.get("edge_zones", []),
            "thermal_bond_mm": b.get("thermal_bond", []), "modules_on_board": b.get("modules_on_board", []),
            "dxf": f"boards/{bid.lower()}-edge-cuts.dxf",
        }
    return out


def area_check(P):
    """Board area against a courtyard estimate of its domains (pcb/generated/components.csv), x1.8 density."""
    import csv
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    comp = root / "pcb" / "generated" / "components.csv"
    if not comp.exists():
        return {"status": "SKIPPED", "reason": "pcb/generated/components.csv not found"}
    fp = [("Pololu_D36V50Fx", 0.0),   # counted by modules_on_board below
          ("R_0402", 2.0), ("C_0402", 2.0), ("R_0603", 4.8), ("C_0603", 4.8), ("R_0805", 7.0), ("C_0805", 7.0),
          ("R_1206", 10.0), ("C_1206", 10.0), ("R_1210", 14.4), ("C_1210", 14.4), ("SOT-23-6", 13.0), ("SOT-23-5", 13.0),
          ("SOT-23", 12.0), ("SOT-363", 7.0), ("D_SMA", 22.0), ("SOIC-28W", 240.0), ("SOIC-8", 40.0), ("TSSOP-24", 75.0),
          ("WSON-6", 9.0), ("Nexperia_CFP3", 12.0)]
    kind = {"resistor": 4.8, "capacitor": 6.0, "diode": 12.0, "nfet": 12.0, "pfet": 15.0, "ic": 30.0, "inductor": 40.0, "relay": 95.0, "module": 20.0}
    by = {}
    with comp.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["category"] != "bare_board_part":
                continue
            a = next((v for k, v in fp if k in r["footprint"]), kind.get(r["kind"], 20.0))
            by[r["board_candidate"]] = by.get(r["board_candidate"], 0.0) + a
    res = {"method": "courtyard estimate per footprint class x 1.8 placement density (model, not a placement)", "boards": {}}
    for bid, b in P.boards["boards"].items():
        need = sum(by.get(d, 0.0) for d in b["domains"] if d in by) * 1.8
        mods = sum(P.parts[m["part"]]["size"][0] * P.parts[m["part"]]["size"][1] for m in b.get("modules_on_board", []))
        have = poly_area([tuple(p) for p in b["outline"]]) - sum(c[2] * c[3] for c in b.get("cutouts", []))
        if bid == "ENC":
            continue
        res["boards"][bid] = {"area_mm2": round(have, 0), "estimate_mm2": round(need + mods, 0),
                              "ratio": round(have / (need + mods), 2) if need + mods else None,
                              "scope": "board parts and modules_on_board, without the harness headers",
                              "result": ("PASS (model)" if have >= need + mods else "FAIL (model)")}
    res["with_harness"] = harness_check(P, res, root)
    return res


SIDE_ENTRY = ("CTRL", "RF", "ENCM", "ENCV")   # tools/assembly_data.py SIDE_ENTRY_UNITS
UNIT_BOARD = {"PWR": "PWR", "RF": "RF", "CTRL": "CTRL", "ENCM": "ENC", "ENCV": "ENC"}


def header_size(P, family, pins, unit):
    """(width along the edge, depth) of a harness header courtyard, parts.json harness_headers."""
    hh = P.parts["harness_headers"]
    key = f"{family}_{'side' if family == 'PH' and unit in SIDE_ENTRY else 'top'}"
    if key not in hh:
        return None
    c = hh[key]
    return c["a"] * (pins - 1) + c["b"], c["d"]


def harness_check(P, parts_res, root):
    """Board area with the harness headers of build/16 §4 added, and their frontage against the edge zones (model estimate).

    Both are reported, not gated: a board whose estimate exceeds its outline is OPEN until its layout or the harness
    architecture is re-planned (wave 2); the parts-only row above keeps its own PASS/FAIL."""
    import csv
    path = root / "build" / "16-dzhgut-rozyemy.csv"
    if not path.exists():
        return {"status": "SKIPPED", "reason": "build/16-dzhgut-rozyemy.csv not found"}
    hh = P.parts["harness_headers"]
    area, front, count, unknown = {}, {}, {}, set()
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            bid = UNIT_BOARD.get(r["unit"])
            if bid is None:
                continue
            size = header_size(P, r["family"], int(r["pins"]), r["unit"])
            if size is None:
                unknown.add(r["family"])
                continue
            w, d = size
            n_boards = 2 if bid == "ENC" else 1
            area[bid] = area.get(bid, 0.0) + w * d / n_boards
            front[bid] = front.get(bid, 0.0) + w / n_boards
            count[bid] = count.get(bid, 0) + 1
    out = {"method": f"courtyard w x d per header (parts.json harness_headers) x {hh['density']:g} placement density, added to the parts estimate; "
                     "frontage = sum of header widths against the edge zones of boards.json (every header at an edge, cable leaving sideways)",
           "status": "MODEL ESTIMATE: reported, not gated (OPEN = the outline or the harness architecture needs a wave-2 decision)",
           "families_without_courtyard": sorted(unknown), "boards": {}}
    for bid, b in P.boards["boards"].items():
        if bid not in count:
            continue
        have = poly_area([tuple(p) for p in b["outline"]]) - sum(c[2] * c[3] for c in b.get("cutouts", []))
        base = parts_res["boards"].get(bid, {}).get("estimate_mm2", 0.0)
        need = base + area[bid] * hh["density"]
        edge = sum(z["span"][1] - z["span"][0] for z in b.get("edge_zones", []))
        ok_area, ok_front = have >= need, edge >= front[bid]
        why = []
        if not ok_area:
            why.append(f"area {need:.0f} > {have:.0f} mm2")
        if not ok_front:
            why.append(f"frontage {front[bid]:.0f} > {edge:.0f} mm of edge zones")
        out["boards"][bid] = {"headers": count[bid], "header_courtyard_mm2": round(area[bid], 0), "area_mm2": round(have, 0),
                              "estimate_with_headers_mm2": round(need, 0), "ratio": round(have / need, 2),
                              "frontage_mm": round(front[bid], 0), "edge_zones_mm": round(edge, 0),
                              "result": "PASS (model)" if ok_area and ok_front else
                              "OPEN: " + "; ".join(why) + " (model estimate; re-plan the board outline or fewer/denser headers — wave 2)"}
    return out
