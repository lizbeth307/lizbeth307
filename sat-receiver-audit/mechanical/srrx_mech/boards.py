"""Board mechanical contract (JSON for pcb/ generators) and Edge.Cuts DXF per board."""
import math

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
            "height_zones": b.get("height_zones", []), "rear_zones": b.get("rear_zones", []),
            "dxf": f"boards/{bid.lower()}-edge-cuts.dxf",
        }
    return out


ROOT = None   # repository root of sat-receiver-audit (set lazily; tests may point it elsewhere)
FILL = (1.5, 1.8)   # placement fill factors reported for the courtyard sums (1.8 = planning value; build/15 W2 MECH-1)


def _root():
    from pathlib import Path
    return ROOT or Path(__file__).resolve().parents[2]


def _sexpr_items(text, kinds=("fp_line", "fp_rect", "fp_circle", "fp_poly", "fp_arc")):
    """Top-level graphic items of a .kicad_mod (kind, item text), found by balanced parentheses."""
    import re
    for m in re.finditer(r"\((" + "|".join(kinds) + r")\b", text):
        i, depth, j = m.start(), 0, m.start()
        while True:
            c = text[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        yield m.group(1), text[i:j + 1]


def courtyard(path):
    """F.CrtYd of one KiCad footprint file: {"w", "h", "area", "shape"} in mm, or None without a courtyard.

    w x h is the bounding box of every F.CrtYd primitive (line, rect, circle, arc points, polygon). The area is that
    box, except for a courtyard drawn as one closed fp_poly, where the polygon area is used (KiCad 10.0.7 files)."""
    import re
    num = r"(-?[0-9.]+)"
    text = path.read_text(encoding="utf-8")
    xs, ys, polys = [], [], []
    for kind, item in _sexpr_items(text):
        if '"F.CrtYd"' not in item:
            continue
        if kind == "fp_circle":
            c = re.search(r"\(center\s+" + num + r"\s+" + num, item)
            e = re.search(r"\(end\s+" + num + r"\s+" + num, item)
            cx, cy = float(c[1]), float(c[2])
            r = math.hypot(float(e[1]) - cx, float(e[2]) - cy)
            pts = [(cx - r, cy - r), (cx + r, cy + r)]
        else:
            pts = [(float(a), float(b)) for a, b in re.findall(r"\((?:start|end|xy|mid|center)\s+" + num + r"\s+" + num + r"\)", item)]
            if kind == "fp_poly":
                polys.append(pts)
        xs += [p[0] for p in pts]
        ys += [p[1] for p in pts]
    if not xs:
        return None
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if len(polys) == 1 and len(polys[0]) >= 3 and len(xs) == len(polys[0]):
        return {"w": round(w, 3), "h": round(h, 3), "area": poly_area(polys[0]), "shape": "fp_poly"}
    return {"w": round(w, 3), "h": round(h, 3), "area": w * h, "shape": "bbox"}


def footprint_courtyards(root=None):
    """Courtyard of every vendored footprint of build/kicad/footprints/manifest.json, by 'Lib:Name'."""
    import json
    root = root or _root()
    man = json.loads((root / "build" / "kicad" / "footprints" / "manifest.json").read_text(encoding="utf-8"))
    return {f["footprint"]: courtyard(root / f["file"]) for f in man["footprints"]}


def _groups(root):
    """design/E*.json: ref -> (sheet, group)."""
    import json
    out = {}
    for p in sorted((root / "design").glob("E[0-9].json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for c in d.get("components", []):
            out[c["ref"]] = (d.get("sheet", p.stem), c.get("group", ""))
    return out


def _need(raw, modules, k):
    return modules + (raw - modules) * k


def area_check(P):
    """Board area against the sum of the real KiCad courtyards of its domains (MODEL ESTIMATE, not gated).

    Every bare board part of pcb/generated/components.csv (DNP excluded) adds the F.CrtYd area of its vendored
    footprint (build/kicad/footprints, KiCad 10.0.7). Placement need = modules x 1.0 + other parts x fill factor,
    reported at 1.5 and 1.8 (1.8 = planning value). Modules are the parts mounted as 'pcb_module' (the Pololu
    carriers of boards.json modules_on_board, the Pico): nothing else can sit under them, and each is counted once."""
    import csv
    root = _root()
    comp = root / "pcb" / "generated" / "components.csv"
    if not comp.exists():
        return {"status": "SKIPPED", "reason": "pcb/generated/components.csv not found"}
    cy = footprint_courtyards(root)
    grp = _groups(root)
    by, mods, groups, gmods, refs, missing = {}, {}, {}, {}, {}, []
    with comp.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["category"] != "bare_board_part" or r["dnp"] == "True":
                continue
            c = cy.get(r["footprint"])
            if c is None:
                missing.append(r["ref"])
                continue
            d = r["board_candidate"]
            by[d] = by.get(d, 0.0) + c["area"]
            refs.setdefault(d, []).append(r["ref"])
            g = "{} {}".format(*grp.get(r["ref"], ("?", "?")))
            if r["mount"] == "pcb_module":
                mods[d] = mods.get(d, 0.0) + c["area"]
                gmods.setdefault(d, {})[g] = gmods.setdefault(d, {}).get(g, 0.0) + c["area"]
            groups.setdefault(d, {})[g] = groups.setdefault(d, {}).get(g, 0.0) + c["area"]
    res = {"method": "sum of the vendored KiCad 10.0.7 F.CrtYd courtyards (bbox; polygon area for a single fp_poly) of the bare board parts of "
                     "pcb/generated/components.csv (DNP excluded) per board domain; need = modules (mount pcb_module) x 1.0 + other parts x fill "
                     f"factor {FILL[0]:g} or {FILL[1]:g} ({FILL[1]:g} = planning value) — MODEL ESTIMATE, not a placement",
           "source": "KiCad 10.0.7 courtyards (build/kicad/footprints/manifest.json)",
           "status": "MODEL ESTIMATE: reported, not gated (OPEN = need at the planning factor exceeds the outline; the real placement decides)",
           "fill_factors": list(FILL), "parts_without_courtyard": sorted(missing), "boards": {}}
    for bid, b in P.boards["boards"].items():
        if bid == "ENC":
            continue
        have = poly_area([tuple(p) for p in b["outline"]]) - sum(c[2] * c[3] for c in b.get("cutouts", []))
        raw = sum(by.get(d, 0.0) for d in b["domains"])
        mod = sum(mods.get(d, 0.0) for d in b["domains"])
        n15, n18 = _need(raw, mod, FILL[0]), _need(raw, mod, FILL[1])
        res["boards"][bid] = {
            "area_mm2": round(have, 0), "courtyard_raw_mm2": round(raw, 0), "modules_mm2": round(mod, 0),
            "per_domain_raw_mm2": {d: round(by.get(d, 0.0), 0) for d in b["domains"]},
            "per_group_raw_mm2": {g: round(v, 0) for d in b["domains"] for g, v in sorted(groups.get(d, {}).items(), key=lambda kv: -kv[1])},
            "per_group_need_mm2": {g: [round(_need(v, gmods.get(d, {}).get(g, 0.0), FILL[0]), 0), round(_need(v, gmods.get(d, {}).get(g, 0.0), FILL[1]), 0)]
                                   for d in b["domains"] for g, v in sorted(groups.get(d, {}).items(), key=lambda kv: -kv[1])},
            "parts": sum(len(refs.get(d, [])) for d in b["domains"]),
            "need_1_5_mm2": round(n15, 0), "need_1_8_mm2": round(n18, 0), "estimate_mm2": round(n18, 0),
            "ratio_1_5": round(n15 / have, 2), "ratio_1_8": round(n18 / have, 2),
            "scope": "board parts and modules, without the harness headers",
            "result": "PASS (model estimate)" if n18 <= have else
                      f"OPEN: need {n18:.0f} mm2 at fill {FILL[1]:g} > outline {have:.0f} mm2 (model estimate; partition and placement decide, AREA / PCB)"}
    res["with_harness"] = harness_check(P, res, root, cy)
    return res


SIDE_ENTRY = ("CTRL", "RF", "ENCM", "ENCV")   # tools/assembly_data.py SIDE_ENTRY_UNITS
UNIT_BOARD = {"PWR": "PWR", "RF": "RF", "CTRL": "CTRL", "ENCM": "ENC", "ENCV": "ENC"}
# Vendored KiCad footprints of the header families, by (family, orientation): exact courtyards where the pin count exists.
HEADER_FP = {("PH", "top"): "Connector_JST:JST_PH_B{n}B-PH-K_1x{n:02d}_P2.00mm_Vertical",
             ("PH", "side"): "Connector_JST:JST_PH_S{n}B-PH-K_1x{n:02d}_P2.00mm_Horizontal",
             ("MF", "top"): "Connector_Molex:Molex_Micro-Fit_3.0_43650-{n:02d}15_1x{n:02d}_P3.00mm_Vertical"}


def header_orientation(family, unit):
    return "side" if family == "PH" and unit in SIDE_ENTRY else "top"


def header_size(P, family, pins, unit, courtyards=None):
    """(width along the edge, depth, source) of a harness header courtyard: the vendored KiCad footprint where it
    exists for that pin count, else parts.json harness_headers (w = a (n - 1) + b, d)."""
    hh = P.parts["harness_headers"]
    orient = header_orientation(family, unit)
    fp = HEADER_FP.get((family, orient))
    if fp and courtyards:
        c = courtyards.get(fp.format(n=pins))
        if c:
            return max(c["w"], c["h"]), min(c["w"], c["h"]), "KiCad"
    key = f"{family}_{orient}"
    if key not in hh or "a" not in hh[key]:
        return None
    c = hh[key]
    return c["a"] * (pins - 1) + c["b"], c["d"], "parts.json"


def harness_check(P, parts_res, root, courtyards=None):
    """Board area with the harness headers of build/16 §4 added, and their frontage against the edge zones (model estimate).

    Both are reported, not gated: a board whose estimate exceeds its outline is OPEN until its layout or the harness
    architecture is re-planned (wave 2). A header that is also a bare board part of pcb/generated/components.csv
    (same ref, e.g. once the headers get graph refs) is counted once, with the parts."""
    import csv
    path = root / "build" / "16-dzhgut-rozyemy.csv"
    if not path.exists():
        return {"status": "SKIPPED", "reason": "build/16-dzhgut-rozyemy.csv not found"}
    hh = P.parts["harness_headers"]
    parts = set()
    comp = root / "pcb" / "generated" / "components.csv"
    if comp.exists():
        with comp.open(encoding="utf-8", newline="") as fh:
            parts = {r["ref"] for r in csv.DictReader(fh) if r["category"] == "bare_board_part"}
    area, front, count, unknown, dup, src = {}, {}, {}, set(), [], {}
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            bid = UNIT_BOARD.get(r["unit"])
            if bid is None:
                continue
            if r["connector"] in parts or r.get("ref", "") in parts:
                dup.append(r["connector"])
                continue
            size = header_size(P, r["family"], int(r["pins"]), r["unit"], courtyards)
            if size is None:
                unknown.add(r["family"])
                continue
            w, d, how = size
            src[how] = src.get(how, 0) + 1
            n_boards = 2 if bid == "ENC" else 1
            area[bid] = area.get(bid, 0.0) + w * d / n_boards
            front[bid] = front.get(bid, 0.0) + w / n_boards
            count[bid] = count.get(bid, 0) + 1
    out = {"method": "header courtyard w x d (vendored KiCad 10.0.7 footprint where that pin count exists, else parts.json harness_headers) "
                     f"x fill factor {FILL[0]:g} or {FILL[1]:g}, added to the parts need; frontage = sum of header widths against the edge zones of "
                     "boards.json (every header at an edge, cable leaving sideways); Mini-Fit Jr., IDC and FAN3 courtyards are assumptions (parts.json)",
           "status": "MODEL ESTIMATE: reported, not gated (OPEN = the outline or the harness architecture needs a wave-2 decision)",
           "families_without_courtyard": sorted(unknown), "counted_with_parts": sorted(dup), "courtyard_sources": dict(sorted(src.items())),
           "boards": {}}
    for bid, b in P.boards["boards"].items():
        if bid not in count:
            continue
        have = poly_area([tuple(p) for p in b["outline"]]) - sum(c[2] * c[3] for c in b.get("cutouts", []))
        pr = parts_res["boards"].get(bid, {})
        n15 = pr.get("need_1_5_mm2", 0.0) + area[bid] * FILL[0]
        n18 = pr.get("need_1_8_mm2", 0.0) + area[bid] * FILL[1]
        edge = sum(z["span"][1] - z["span"][0] for z in b.get("edge_zones", []))
        ok_area, ok_front = have >= n18, edge >= front[bid]
        why = []
        if not ok_area:
            why.append(f"area {n18:.0f} > {have:.0f} mm2 at fill {FILL[1]:g}")
        if not ok_front:
            why.append(f"frontage {front[bid]:.0f} > {edge:.0f} mm of edge zones")
        out["boards"][bid] = {"headers": count[bid], "header_courtyard_mm2": round(area[bid], 0), "area_mm2": round(have, 0),
                              "with_headers_raw_mm2": round(pr.get("courtyard_raw_mm2", 0.0) + area[bid], 0),
                              "estimate_with_headers_1_5_mm2": round(n15, 0), "estimate_with_headers_mm2": round(n18, 0),
                              "ratio": round(n18 / have, 2), "frontage_mm": round(front[bid], 0), "edge_zones_mm": round(edge, 0),
                              "result": "PASS (model estimate)" if ok_area and ok_front else
                              "OPEN: " + "; ".join(why) + " (model estimate; re-plan the board outline or fewer/denser headers — wave 2)"}
    return out


ZONE_MARGIN = 0.5   # mm kept free between a part and the nearest envelope (the 'tight' threshold of layout.fit_checks)


def _hmi_flange_boxes(P):
    """Button-cap flanges behind the front wall (mechanical.json hmi.buttons): they sit over the CTRL switches."""
    m = P.mech
    bt = m["hmi"]["buttons"]
    r = bt["cap_flange_d"] / 2.0
    zf = m["stack_z"]["front_wall_inner"]
    return [(f"button_flange.{i}{j}", (x - r, y - r, zf - bt["cap_flange_t"], x + r, y + r, zf))
            for i, x in enumerate(bt["cols_x"]) for j, y in enumerate(bt["rows_y"])]


def clearance_map(P, bid):
    """Free height over the outline of board bid on its component side ('front') and its back ('rear').

    Every layout envelope, structure part (plate, angles, bosses, RF-bay walls and lid), the button-cap flanges and the
    inner shell faces count as obstacles; the board's own envelope does not. The outline is cut into rectangles at every
    obstacle edge and merged where the free height and the limiting part agree. Board coordinates (boards.json)."""
    from .layout import item_boxes, structure_boxes
    W, H, D = P.outer
    t_wall = P.mech["wall"]
    b = P.boards["boards"][bid]
    pl = b["place"]
    ox, oy = pl["origin"]
    tb = P.boards["stackup"]["t"]
    up = pl["facing"] == "+z"
    face = pl["z_bottom"] + tb if up else pl["z_bottom"] - tb      # component face
    back = pl["z_bottom"]                                        # face towards the mounting surface
    obst = [(n, bx) for _, n, bx, it in item_boxes(P) if it.get("board") != bid] + structure_boxes(P) + _hmi_flange_boxes(P)
    xs0, ys0 = [p[0] for p in b["outline"]], [p[1] for p in b["outline"]]
    xa, xb, ya, yb = ox + min(xs0), ox + max(xs0), oy + min(ys0), oy + max(ys0)
    near = [(n, bx) for n, bx in obst if bx[0] < xb and bx[3] > xa and bx[1] < yb and bx[4] > ya]
    xs = sorted({xa, xb} | {v for _, bx in near for v in (bx[0], bx[3]) if xa < v < xb}
                | {ox + r[0] for r in b["rects"]} | {ox + r[0] + r[2] for r in b["rects"]})
    ys = sorted({ya, yb} | {v for _, bx in near for v in (bx[1], bx[4]) if ya < v < yb}
                | {oy + r[1] for r in b["rects"]} | {oy + r[1] + r[3] for r in b["rects"]})

    def inside(x, y):
        u, v = x - ox, y - oy
        if any(c[0] < u < c[0] + c[2] and c[1] < v < c[1] + c[3] for c in b.get("cutouts", [])):
            return False
        return any(r[0] < u < r[0] + r[2] and r[1] < v < r[1] + r[3] for r in b["rects"])

    def free(x0, y0, x1, y1, side):
        towards_front = up if side == "front" else not up
        z0 = face if side == "front" else back
        best, lim = ((D - t_wall) - z0, "front wall") if towards_front else (z0 - t_wall, "rear wall")
        for n, bx in near:
            if not (bx[0] < x1 and bx[3] > x0 and bx[1] < y1 and bx[4] > y0):
                continue
            if towards_front and bx[5] > z0 + 1e-6:
                g = max(0.0, bx[2] - z0)
            elif not towards_front and bx[2] < z0 - 1e-6:
                g = max(0.0, z0 - bx[5])
            else:
                continue
            if g < best - 1e-9:
                best, lim = g, n
        return round(best, 2), lim

    out = {}
    for side in ("front", "rear"):
        rows = []
        for y0, y1 in zip(ys, ys[1:]):
            row = []
            for x0, x1 in zip(xs, xs[1:]):
                if not inside((x0 + x1) / 2, (y0 + y1) / 2):
                    continue
                f, lim = free(x0, y0, x1, y1, side)
                if row and abs(row[-1][1] - x0) < 1e-9 and row[-1][4] == (f, lim):
                    row[-1][1] = x1
                else:
                    row.append([x0, x1, y0, y1, (f, lim)])
            rows.append(row)
        rects = []
        open_ = {}
        for row in rows:
            nxt = {}
            for x0, x1, y0, y1, key in row:
                k = (round(x0, 6), round(x1, 6), key)
                if k in open_ and abs(open_[k][3] - y0) < 1e-9:
                    r = open_.pop(k)
                    r[3] = y1
                    nxt[k] = r
                else:
                    nxt[k] = [x0, x1, y0, y1, key]
            rects += list(open_.values())
            open_ = nxt
        rects += list(open_.values())
        zones = []
        for x0, x1, y0, y1, (f, lim) in sorted(rects, key=lambda r: (r[2], r[0])):
            zones.append({"rect": [round(x0 - ox, 2), round(y0 - oy, 2), round(x1 - x0, 2), round(y1 - y0, 2)],
                          "free_mm": f, "fits_mm": round(max(0.0, f - ZONE_MARGIN), 2), "limit": lim})
        out[side] = zones
    return out


ZONE_BOARDS = ("CTRL", "RF")   # boards whose height_zones / rear_zones in boards.json are the computed clearance map


def zones_from_map(m):
    """boards.json form of a clearance map (rectangles thinner than 0.05 mm dropped)."""
    def keep(z):
        return z["rect"][2] >= 0.05 and z["rect"][3] >= 0.05
    return ([dict(z) for z in m["front"] if keep(z)], [dict(z) for z in m["rear"] if keep(z)])


def header_height(P, family, unit):
    """(height above the board, orientation, source key) of a build/16 header as specified, or (None, ...) when not read."""
    hh = P.parts["harness_headers"]
    orient = header_orientation(family, unit)
    key = f"{family}_{orient}"
    c = hh.get(key, {})
    h = c.get("h_mated", c.get("h"))
    return h, orient, key


def header_height_rule(P):
    """R-HDR-HEIGHT: every build/16 board header against its board's height limit and the computed clearance map.

    Reported OPEN until the header refs and positions exist (GR-3 decides orientation, side and board); never FAIL."""
    import csv
    path = _root() / "build" / "16-dzhgut-rozyemy.csv"
    rule = {"id": "R-HDR-HEIGHT", "rule": "board-side harness headers (build/16 §4) inside the board height limit, or in a computed height zone (component side) / rear zone",
            "source": "parts.json harness_headers h; boards.json max_height, height_zones, rear_zones (clearance map)"}
    if not path.exists():
        return dict(rule, value_mm=None, result="OPEN: build/16-dzhgut-rozyemy.csv not found")
    hh = P.parts["harness_headers"]
    cy = footprint_courtyards()

    def best(zones, size, default):
        """Largest allowed height (fits_mm of a computed zone, else max_height of a declared zone) among the zones whose
        rectangle takes the header courtyard in either orientation."""
        if size is None:
            return default
        a, d = sorted(size[:2])
        ok = [z.get("fits_mm", z.get("max_height", 0.0)) for z in zones
              if min(z["rect"][2:]) + 1e-9 >= a and max(z["rect"][2:]) + 1e-9 >= d]
        return max(ok + [default])
    rows, over, unknown = [], [], []
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            bid = UNIT_BOARD.get(r["unit"])
            if bid is None:
                continue
            b = P.boards["boards"][bid]
            h, orient, key = header_height(P, r["family"], r["unit"])
            size = header_size(P, r["family"], int(r["pins"]), r["unit"], cy)
            front = best(b.get("height_zones", []), size, b["max_height"])
            rear = best(b.get("rear_zones", []), size, 0.0)
            row = {"connector": r["connector"], "board": bid, "family": r["family"], "orientation": orient, "h_mm": h,
                   "courtyard_mm": [round(v, 2) for v in size[:2]] if size else None,
                   "max_height": b["max_height"], "best_front_zone_mm": front, "best_rear_zone_mm": rear}
            if h is None:
                row["verdict"] = f"height of {key} not read (TBD)"
                unknown.append(r["connector"])
            elif h <= b["max_height"] + 1e-9:
                row["verdict"] = "inside the board limit"
            else:
                where = []
                if h <= front + 1e-9:
                    where.append("a component-side height zone")
                if h <= rear + 1e-9:
                    where.append("a rear zone (THT from the back)")
                row["verdict"] = f"above the board limit {b['max_height']:g}; fits " + (" or ".join(where) if where else "no computed zone that takes its courtyard")
                over.append(f"{r['connector']} {key} {h:g}")
            rows.append(row)
    ra = hh.get("MF_ra", {}).get("h")
    ctrl = P.boards["boards"]["CTRL"]
    ctrl_front = max([z["fits_mm"] for z in ctrl.get("height_zones", []) if "fits_mm" in z] or [ctrl["max_height"]])
    note = (f"; right-angle Micro-Fit {ra:g} mm {'fits' if ra is not None and ra <= ctrl_front else 'does not fit'} the CTRL component side "
            f"(best zone {ctrl_front:g} mm)" if ra is not None else "")
    return dict(rule, value_mm={"above_limit": over, "height_not_read": unknown}, limit_mm={k: v["max_height"] for k, v in P.boards["boards"].items()},
                headers=rows,
                result=f"OPEN: GR-3 decides (header orientation, board side or board): {len(over)} headers above their board limit"
                       + (f" ({', '.join(over)})" if over else "") + f"; {len(unknown)} heights not read" + note)
