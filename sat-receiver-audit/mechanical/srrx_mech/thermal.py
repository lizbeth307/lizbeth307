"""Thermal interfaces (MECH-05): design gaps, Gelid GP-Ultimate pad choice, compression range and pad cuts.

Every gap is a design value of this model with an assumed tolerance; the pad
thickness is chosen so that the whole gap range keeps the compression between
COMP_MIN and the Gelid limit of 30 % (parts.json gelid_gp_ultimate). Gates T-02
and T-03 (fit and thermal) stay OPEN: the real gaps are measured at assembly.
"""

COMP_MIN = 0.10   # design choice of this package: below 10 % the contact is not assured over the tolerance range


def _comp(t, gap):
    return (t - gap) / t


def choose(P, gap, tol):
    """Smallest Gelid thickness whose compression stays in [COMP_MIN, max] over gap +- tol."""
    g = P.parts["gelid_gp_ultimate"]
    cmax = g["max_compression"]
    for key in sorted(g["thicknesses"], key=float):
        t = float(key)
        lo, hi = _comp(t, gap + tol), _comp(t, gap - tol)
        if lo >= COMP_MIN - 1e-9 and hi <= cmax + 1e-9:
            return t, g["thicknesses"][key], lo, hi
    return None


def interfaces(P):
    m = P.mech
    q = P.parts["q6a"]
    cb = m["cu_block"]
    soc, ram = q["soc"], q["lpddr5"]
    rows = []

    def pad_row(iid, where, gap, tol, cut, qty=1, note=""):
        c = choose(P, gap, tol)
        r = {"id": iid, "where": where, "medium": "Gelid GP-Ultimate pad", "design_gap_mm": round(gap, 2), "gap_tol_mm": tol,
             "cut_mm": [round(cut[0], 1), round(cut[1], 1)], "qty": qty, "note": note}
        if c is None:
            r.update({"pad_mm": None, "result": "OPEN: no Gelid thickness keeps 10-30 % compression over this gap range; measure the gap"})
        else:
            t, sku, lo, hi = c
            r.update({"pad_mm": t, "sku": sku, "compression": [round(lo, 3), round(hi, 3)], "result": "PASS (model)"})
        rows.append(r)

    rows.append({"id": "T-SOC", "where": "Q6A SoC (BGA1287) to the cooler-A Cu block, flat face", "medium": "thermal paste or PTM7950 (never a pad)",
                 "design_gap_mm": 0.0, "cut_mm": [round(soc["uv"][2] - soc["uv"][0], 1), round(soc["uv"][3] - soc["uv"][1], 1)], "qty": 1,
                 "note": "bond line and amount per the TDS of the chosen material (TBD); STACK 5.8: separate SoC and LPDDR5 contacts",
                 "result": "OPEN: material TDS not read in this package"})
    ram_gap = cb["ram_recess"] + (soc["top"] - ram["top"])
    pad_row("T-LPDDR5", "LPDDR5 (BGA315) to the recessed step of the Cu block", ram_gap, cb["gap_tol"],
            (ram["uv"][2] - ram["uv"][0], ram["uv"][3] - ram["uv"][1]),
            note=f"recess {cb['ram_recess']} mm below the SoC face; SoC and LPDDR5 tops {soc['top']} / {ram['top']} mm (Q6A STEP V1.21)")
    lp = m["lime_pedestal"]
    pad_row("T-LIME", "Lime bottom-side parts to the Al pedestal", lp["pad_gap"], lp["gap_tol"], (lp["rect"][2], lp["rect"][3]),
            note="card height set at the M.2 fixing; STACK 5.8 asks for contact on both sides: the top side through the shield can only, TBD")
    ub = m["ufs_boss"]
    pad_row("T-UFS", "UFS module (Q6A bottom side) to the Al boss on the plate", ub["pad_gap"], ub["gap_tol"], ub["contact"],
            note=f"boss height = measured gap - {ub['pad_gap']} mm (assumed module_below_board {ub['module_below_board']} mm gives "
                 f"{round(P.mech['q6a_mount']['standoff'] - ub['module_below_board'] - ub['pad_gap'], 2)} mm)")
    pb = m["pwr_bond"]
    b = P.boards["boards"]["PWR"]
    for i, z in enumerate(b["thermal_bond"]):
        pad_row(f"T-PWR{i + 1}", f"PWR board bottom copper to the plate, zone {i + 1}", pb["shim"], pb["gap_tol"], (z[2], z[3]),
                note="gap set by shim washers at the M3 screws")
    rows.append({"id": "T-KSD9700", "where": "KSD9700 70 C NO on the hottest IP2368 MOSFET", "medium": "polyimide tape + thermally conductive adhesive",
                 "result": "OPEN: adhesive product and its datasheet not chosen in this package (STACK 5.6 gives only the polyimide layer)"})
    rows.append({"id": "T-NTC", "where": "pack NTC on the middle cell (E3-06)", "medium": "polyimide tape",
                 "result": "OPEN: attachment product not chosen in this package"})
    return rows


def nest(rows, sheet):
    """Shelf packing of the pad cuts into sheets per thickness (2 mm kerf). Returns {thickness: {sheets, pieces}}."""
    W, H = sheet
    by = {}
    for r in rows:
        if r.get("pad_mm"):
            for _ in range(r.get("qty", 1)):
                by.setdefault(r["pad_mm"], []).append((r["id"], r["cut_mm"]))
    out = {}
    k = 2.0
    for t, pcs in sorted(by.items()):
        sheets = []   # each: list of shelves [y, height, x_used]
        placed = []
        for iid, (a, b) in sorted(pcs, key=lambda p: (-max(p[1]), p[0])):
            w, h = (max(a, b), min(a, b))
            if w > W:
                w, h = h, w
            if w > W or h > H:
                placed.append({"id": iid, "sheet": None, "note": "larger than one sheet: cut from two pieces"})
                continue
            done = False
            for si, shelves in enumerate(sheets):
                for sh in shelves:
                    if h <= sh[1] and sh[2] + w <= W:
                        placed.append({"id": iid, "sheet": si + 1, "at": [sh[2], sh[0]], "size": [w, h]})
                        sh[2] += w + k
                        done = True
                        break
                if not done:
                    top = sum(s[1] + k for s in shelves)
                    if top + h <= H:
                        shelves.append([top, h, w + k])
                        placed.append({"id": iid, "sheet": si + 1, "at": [0.0, top], "size": [w, h]})
                        done = True
                if done:
                    break
            if not done:
                sheets.append([[0.0, h, w + k]])
                placed.append({"id": iid, "sheet": len(sheets), "at": [0.0, 0.0], "size": [w, h]})
        out[str(t)] = {"sheets_90x50": len(sheets), "pieces": placed}
    return out
