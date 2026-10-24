"""Board mechanical contract (JSON for pcb/ generators) and Edge.Cuts DXF per board."""
from .geom2d import Sheet, fmt


def poly_area(pts):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def board_sheet(P, bid):
    b = P.boards["boards"][bid]
    sh = Sheet(f"B-{bid}", f"Плата {bid}: контур Edge.Cuts і кріпильні отвори", b["name"], (297.0, 210.0), 1.0, (30.0, 40.0),
               "FR-4, 4 шари, 1.6 мм (build/15)",
               ["Координати — від лівого нижнього кута контуру, вид з боку компонентів.",
                f"Отвори ⌀{fmt(b['hole_d'])}, зона заборони міді/деталей ⌀{fmt(b['hole_keepout_d'])}; висота деталей ≤{fmt(b['max_height'])} мм.",
                "DXF цього аркуша імпортується в KiCad як Edge.Cuts (шар CUT) і отвори (шар HOLE); 1 одиниця = 1 мм."])
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
    fp = [("R_0402", 2.0), ("C_0402", 2.0), ("R_0603", 4.8), ("C_0603", 4.8), ("R_0805", 7.0), ("C_0805", 7.0),
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
                              "result": ("PASS (model)" if have >= need + mods else "FAIL (model)")}
    return res
