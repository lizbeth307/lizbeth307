#!/usr/bin/env python3
"""Computed board-partition budget of SR-RX-v2.1 (wave 2, package AREA: D-AREA). MODEL ESTIMATE.

Usage (stdlib only; needs no KiCad):
  python pcb/partition_budget.py           # write pcb/partition-budget.json
  python pcb/partition_budget.py --check   # fail if the file is stale or the decision record does not hold

Inputs (read only):
  pcb/partition-spec.json                     decision record: parameters, candidates, header map (hand-written)
  build/kicad/footprints/manifest.json        footprint files; F.CrtYd bounding boxes and THT pad fields
  pcb/generated/components.csv                bare board parts, their mount and the pcb/prepare.py domain
  design/E1.json .. design/E5.json            schematic groups, values and pin nets
  design/parts/parts.json                     MPN of every ref (height table lookup)
  build/16-dzhgut-rozyemy.csv                 board-side harness headers per unit (family, pins, nets)
  mechanical/params/parts.json                harness_headers courtyard formulas (w = a (n-1) + b, d)
  mechanical/params/boards.json               outlines, holes, modules on PWR
  tools/assembly_data.py                      NET_CURRENT (read with ast, never imported)

Method: the area of a part is the bounding box of its F.CrtYd graphics (one count per ref; a ref that is a
bare board part and a build/16 connector is counted once, as the part). Demand of a board at factor f is
f x (parts + harness headers + B2B + test points) + modules at 1.0 + keepouts at 1.0; usable area is the
outline minus hole keep-outs, and for the PWR-B mezzanine also minus the windows over PWR-A parts taller
than hA, the Pololu windows, the uncovered edge strips over the PWR-A power headers and the probe windows of
the PWR-A test points. The PWR-A/PWR-B boundary is the set of nets with pins on both boards; each crossing
power net needs ceil(I_protection / I_pin) B2B contacts. A CTRL bottom header takes the first variant whose read
height fits the gap over BMS/IP2368 within the depth cap (dz_ctrl = the largest such term); a header without
one is listed as unresolved. Nothing here is a placement: the fill of a real placement (PCB-PWRA/PWRB/CTRL)
decides, and the fallbacks of the spec fire on the triggers it states.

W2 AREA-2 (SHRINK-2): a candidate may carry planned content changes (candidates.<id>.planned.changes: footprint/MPN
swaps, deletions, header merges and reserved blocks that stand in for parts without a graph ref yet). A change counts
while every one of its refs still has the graph value it replaces; once GR-5A/GR-5B put the new part into the graph it is
'in graph' and the graph counts. Such a candidate is also evaluated on the graph of record (no planned change), because
pcb/prepare.py (domain_override_pwr_a) and pcb/generated/b2b-nets.json follow the graph. pwr_a_bottom makes PWR-A
two-sided: the listed chip refs count on the bottom side (board PWR_A_BOTTOM), whose usable area is the outline minus the
hole keep-outs, the thermal_bond zones and the top THT pin fields plus the pocket margin (an area sum: the pin fields
have no positions here, so their overlap with the bond zones is not taken back). h_trim (rule H-TRIM) turns the PWR-A
keep-outs under the PWR-B THT pin fields into a height zone (low-profile parts allowed), so they cost no area.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "pcb" / "partition-spec.json"
OUT = ROOT / "pcb" / "partition-budget.json"
SHEETS = ("E1", "E2", "E3", "E4", "E5")
# the last two are the PWR-B domains that GR-3 adds to pcb/prepare.py (partition-spec domains.PWR_B); listing them
# here keeps the PWR part set the same before and after that change
PWR_DOMAINS = ("PWR_MAIN", "PWR_BRANCH", "USB_POWER", "PWR_BRANCH_SW", "USB_POWER_SW")
PWR_B_DOMAINS = ("PWR_BRANCH_SW", "USB_POWER_SW")
CURRENT_BOARDS = {"PWR": PWR_DOMAINS, "RF": ("RF_HMC", "RF_HF", "RF_INJECTOR", "DC_CORE"), "CTRL": ("CTRL_HMI",)}


def rel(path):
    return path.relative_to(ROOT).as_posix()


def rnd(x, n=1):
    v = round(x + 0.0, n)
    return 0.0 if v == 0 else v


# ------------------------------------------------------------------------------------------ s-expressions
def sexpr(text):
    """Tiny KiCad s-expression reader: nested lists of atoms (quoted strings unquoted)."""
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack, cur = [], []
    for t in tokens:
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done, cur = cur, stack.pop()
            cur.append(done)
        else:
            cur.append(t[1:-1] if t.startswith('"') else t)
    return cur[0]


def children(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def first(node, name):
    found = children(node, name)
    return found[0] if found else None


def num(node, i):
    return float(node[i])


class Footprints:
    """F.CrtYd bounding box and THT pad field of every footprint in the vendored library."""

    def __init__(self):
        man = json.loads((ROOT / "build/kicad/footprints/manifest.json").read_text(encoding="utf-8"))
        self.files = {f["footprint"]: ROOT / f["file"] for f in man["footprints"]}
        self.cache = {}

    def get(self, ident):
        if ident not in self.cache:
            self.cache[ident] = self._read(self.files[ident]) if ident in self.files else None
        return self.cache[ident]

    def _read(self, path):
        fp = sexpr(path.read_text(encoding="utf-8"))
        xs, ys = [], []
        for item in fp:
            if not (isinstance(item, list) and item and item[0] in ("fp_line", "fp_rect", "fp_circle", "fp_poly", "fp_arc")):
                continue
            layer = first(item, "layer")
            if not layer or layer[1] != "F.CrtYd":
                continue
            if item[0] == "fp_circle":
                c, e = first(item, "center"), first(item, "end")
                r = math.hypot(num(e, 1) - num(c, 1), num(e, 2) - num(c, 2))
                xs += [num(c, 1) - r, num(c, 1) + r]
                ys += [num(c, 2) - r, num(c, 2) + r]
                continue
            pts = [first(item, k) for k in ("start", "end", "mid")]
            pts = [p for p in pts if p]
            pl = first(item, "pts")
            if pl:
                pts += children(pl, "xy")
            for p in pts:
                xs.append(num(p, 1))
                ys.append(num(p, 2))
        crt = (max(xs) - min(xs), max(ys) - min(ys)) if xs else None
        px, py, n_tht = [], [], 0
        for pad in children(fp, "pad"):
            if pad[2] not in ("thru_hole", "np_thru_hole"):
                continue
            at, size = first(pad, "at"), first(pad, "size")
            w, h = num(size, 1), num(size, 2)
            if len(at) > 3 and round(float(at[3])) % 180 == 90:
                w, h = h, w
            x, y = num(at, 1), num(at, 2)
            px += [x - w / 2, x + w / 2]
            py += [y - h / 2, y + h / 2]
            n_tht += pad[2] == "thru_hole"
        field = (max(px) - min(px), max(py) - min(py)) if px else None
        return {"crtyd": crt, "tht_field": field, "tht_pads": n_tht}


# ------------------------------------------------------------------------------------------ geometry
def poly_area(pts):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def clip(poly, x0, y0, x1, y1):
    """Sutherland-Hodgman clip of a polygon to an axis-aligned rectangle."""
    def side(pts, inside, cross):
        out = []
        for i, p in enumerate(pts):
            q = pts[i - 1]
            if inside(p):
                if not inside(q):
                    out.append(cross(q, p))
                out.append(p)
            elif inside(q):
                out.append(cross(q, p))
        return out

    def xcut(xc):
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / (b[0] - a[0]))

    def ycut(yc):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yc - a[1]) / (b[1] - a[1]), yc)

    pts = list(poly)
    for inside, cross in ((lambda p: p[0] >= x0, xcut(x0)), (lambda p: p[0] <= x1, xcut(x1)),
                          (lambda p: p[1] >= y0, ycut(y0)), (lambda p: p[1] <= y1, ycut(y1))):
        pts = side(pts, inside, cross) if pts else []
    return pts


def rect_overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(w, 0.0) * max(h, 0.0)


def circle_rect_overlap(c, r, rc, step=0.01):
    """Area of a circle (centre c, radius r) inside the rectangle rc = (x0, y0, x1, y1), by vertical chords."""
    x0, x1 = max(c[0] - r, rc[0]), min(c[0] + r, rc[2])
    a, n = 0.0, int(max(x1 - x0, 0.0) / step + 0.5)
    for i in range(n):
        x = x0 + (i + 0.5) * step
        h = math.sqrt(max(r * r - (x - c[0]) ** 2, 0.0))
        a += max(min(c[1] + h, rc[3]) - max(c[1] - h, rc[1]), 0.0) * step
    return a


# ------------------------------------------------------------------------------------------ inputs
def net_currents():
    tree = ast.parse((ROOT / "tools/assembly_data.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "NET_CURRENT" for t in node.targets):
            return {k: {"cont": v[0], "prot": v[1], "protection": v[2]} for k, v in ast.literal_eval(node.value).items()}
    raise SystemExit("tools/assembly_data.py: NET_CURRENT not found")


def mpn_of_refs():
    db = json.loads((ROOT / "design/parts/parts.json").read_text(encoding="utf-8"))
    return {r: p.get("mpn") for p in db["parts"] for r in p.get("refs", [])}


class Design:
    def __init__(self, spec):
        self.spec = spec
        self.fps = Footprints()
        self.mpn = mpn_of_refs()
        self.current = net_currents()
        mech = json.loads((ROOT / "mechanical/params/boards.json").read_text(encoding="utf-8"))
        self.mech = mech["boards"]
        self.hh = json.loads((ROOT / "mechanical/params/parts.json").read_text(encoding="utf-8"))["parts"]["harness_headers"]
        self.comp = {}
        self.power_flags = set()
        for s in SHEETS:
            g = json.loads((ROOT / f"design/{s}.json").read_text(encoding="utf-8"))
            self.power_flags |= {f["net"] for f in g.get("power_flags", [])}
            for c in g["components"]:
                self.comp[c["ref"]] = dict(c, sheet=s)
        self.rows = {}
        with (ROOT / "pcb/generated/components.csv").open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                self.rows[r["ref"]] = r
        # W2 GR-3: a build/16 header that is a graph ref (bare board part) is counted as a part with its real courtyard;
        # its family, orientation and board come from build/16-dzhgut-rozyemy.csv
        self.header_rows = {}
        with (ROOT / "build/16-dzhgut-rozyemy.csv").open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r["connector"] in self.rows and self.rows[r["connector"]]["category"] == "bare_board_part":
                    self.header_rows[r["connector"]] = r
        self.parts = self._parts()
        self.headers_raw = self._headers()

    # -- parts ----------------------------------------------------------------------------------------
    def height(self, ref, fp):
        """(height, source, lower_bound): lower_bound marks a read value that is only a part of the stack
        (a fuse holder without its fuse), so the real height is above it."""
        return self.height_for(self.mpn.get(ref), fp)

    def height_for(self, mpn, fp):
        """height() of an MPN and footprint (also of a planned part that has no graph ref yet)."""
        h = self.spec["heights"]
        if mpn in h["by_mpn"]:
            e = h["by_mpn"][mpn]
            return e["h"], f"MPN {mpn}: {e['src']}", bool(e.get("lower_bound"))
        name = fp.split(":", 1)[-1]
        for key, e in h["by_footprint"].items():
            if name.startswith(key):
                return e["h"], f"footprint {key}: {e['src']}", bool(e.get("lower_bound"))
        for pat in h["low_profile"]["footprint_prefixes"]:
            if name.startswith(pat):
                return h["low_profile"]["h_max"], "class: " + h["low_profile"]["src"], False
        return None, "no read or class height", False

    @staticmethod
    def is_test_point(r):
        """A test point before GR-2 (category test_access_requirement) and after it (a board part, mount pcb_pad,
        kind testpoint or a TestPoint: footprint): the probe-window rule must not depend on the classification."""
        return (r["category"] == "test_access_requirement" or r.get("kind") == "testpoint"
                or (r["mount"] == "pcb_pad" and r["footprint"].startswith("TestPoint:")))

    def _parts(self):
        tp_fp = self.spec["test_points"]["footprint"]
        # W2 B2B: the two board-to-board halves are graph refs, but their area is the b2b courtyard of each board (b2b_raw) and
        # their nets are the boundary itself, so they are not parts here
        b2b_refs = set(self.spec["b2b"].get("graph_refs", {}).values())
        out = {}
        for ref, r in self.rows.items():
            tp = self.is_test_point(r)
            if r["dnp"] == "True" or not (r["category"] == "bare_board_part" or tp) or ref in b2b_refs:
                continue
            fp = (r["footprint"] if self.fps.get(r["footprint"]) else tp_fp) if tp else r["footprint"]
            info = self.fps.get(fp)
            if info is not None and info["crtyd"] is None and r["mount"] == "pcb_pad" and not tp:
                # A copper net tie (NT401, board part since GR-2): KiCad's NetTie footprints carry no courtyard, and the
                # mechanical area check lists it under parts_without_courtyard; it is not counted here either.
                continue
            if info is None or info["crtyd"] is None:
                raise SystemExit(f"{ref}: footprint {fp} has no F.CrtYd in the vendored library")
            c = self.comp[ref]
            h, hsrc, h_lb = self.height(ref, fp)
            hdr = self.header_rows.get(ref)
            if hdr is not None:
                fam = f"{hdr['family']}_{hdr['orientation']}"
                f = dict(self.hh.get(fam) or {}, **self.spec["header_families"].get(fam, {}))
                h = f.get("h_mated", f.get("h"))
                hsrc, h_lb = f"harness header {fam}: " + (f.get("h_src") or f.get("src") or "mechanical/params/parts.json harness_headers"), False
            w, d = info["crtyd"]
            nets = sorted({p["net"] for p in c["pins"] if p.get("net")})
            out[ref] = {
                "ref": ref, "sheet": c["sheet"], "group": c.get("group", ""), "value": c.get("value", ""),
                "domain": r["board_candidate"], "mount": "pcb_pad" if tp else r["mount"], "tp": tp,
                "footprint": fp, "w": w, "d": d, "area": w * d, "h": h, "h_src": hsrc, "h_lower_bound": h_lb,
                "module": r["mount"] == "pcb_module", "tht": (not tp) and r["mount"] in ("pcb_tht", "pcb_module"),
                "tht_field": info["tht_field"], "tht_pads": info["tht_pads"] if not tp else 0, "nets": nets,
                "pins": c["pins"], "header": hdr is not None,
                "header_family": f"{hdr['family']}_{hdr['orientation']}" if hdr is not None else None,
            }
        return out

    # -- harness headers --------------------------------------------------------------------------------
    def _headers(self):
        out = []
        with (ROOT / "build/16-dzhgut-rozyemy.csv").open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r["connector"] in self.parts:      # a header that is already a bare board part: counted once
                    continue
                out.append({"id": r["connector"], "unit": r["unit"], "segment": r["segment"], "family": r["family"],
                            "pins": int(r["pins"]), "nets": sorted(set(r["nets"].split()) - {"—", ""})})
        return out

    def family(self, family):
        """Courtyard formula of a header family: mechanical/params/parts.json harness_headers, completed or
        replaced by the spec's header_families (heights, pin fields, dual-row families)."""
        fam = self.family_or_none(family)
        if fam is None:
            raise SystemExit(f"header family {family}: no courtyard formula")
        return fam

    def family_or_none(self, family):
        """As family(), but None when the family has no courtyard formula (a variant that is not usable yet)."""
        fam = dict(self.hh.get(family) or {})
        fam.update(self.spec["header_families"].get(family, {}))
        return fam if all(k in fam for k in ("a", "b", "d")) else None

    def header_size(self, family, pins):
        fam = self.family(family)
        n = math.ceil(pins / 2) if fam.get("per_row") else pins     # dual row: width over the pins of one row
        return fam["a"] * (n - 1) + fam["b"], fam["d"], fam.get("h")

    def consolidated_headers(self, unit):
        """build/16 headers of one unit after the consolidation map of the spec."""
        # entries implemented as graph refs (W2 GR-3) are counted as parts, not here
        cmap = [m for m in self.spec["consolidation"]["map"] if m["unit"] == unit and "graph_refs" not in m]
        used, out = set(), []
        raw = {h["id"]: h for h in self.headers_raw if h["unit"] == unit}
        for m in cmap:
            olds = [raw[i] for i in m["from"] if i in raw]
            if len(olds) != len(m["from"]):
                raise SystemExit(f"consolidation {m['to']}: build/16 lacks {sorted(set(m['from']) - set(raw))}")
            pins = sum(h["pins"] for h in olds)
            for to in m["headers"]:
                if to["pins"] < 1:
                    raise SystemExit(f"consolidation {m['to']}: bad pin count")
            if sum(t["pins"] for t in m["headers"]) < pins:
                raise SystemExit(f"consolidation {m['to']}: {sum(t['pins'] for t in m['headers'])} contacts for {pins} pins")
            nets = sorted({n for h in olds for n in h["nets"]})
            for i, to in enumerate(m["headers"]):
                out.append({"id": to["id"], "unit": unit, "segment": "+".join(sorted({h["segment"] for h in olds})),
                            "family": to["family"], "pins": to["pins"], "nets": nets if i == 0 else [], "nets_shared_with": m["to"],
                            "from": m["from"], "consolidated": True})
            used |= set(m["from"])
        for h in self.headers_raw:
            if h["unit"] == unit and h["id"] not in used:
                fam = h["family"]
                if fam == "PH":
                    fam = self.spec["header_orientation"]["PH_default"].get(unit, "PH_top")
                elif fam in ("MF", "MFJ", "IDC", "FAN3"):
                    fam = fam + "_top"
                out.append(dict(h, family=fam, consolidated=False, from_=[h["id"]]))
        for h in out:
            w, d, ht = self.header_size(h["family"], h["pins"])
            h.update(w=w, d=d, area=w * d, h=ht)
        return out


# ------------------------------------------------------------------------------------------ evaluation
class Evaluator:
    def __init__(self, design):
        self.D = design
        self.S = design.spec
        self.P = self.S["parameters"]
        self.pwr_parts = {r: p for r, p in design.parts.items() if p["domain"] in PWR_DOMAINS or
                          (p["tp"] and p["sheet"] in ("E1", "E2", "E5") and self.group_domain(p) in PWR_DOMAINS)}
        self.ctrl_parts = {r: p for r, p in design.parts.items() if p["domain"] == "CTRL_HMI" or
                           (p["tp"] and self.group_domain(p) == "CTRL_HMI")}
        n_tp = sum(1 for p in self.pwr_parts.values() if p["tp"])
        if n_tp != self.S["test_points"]["expected_pwr"]:
            raise SystemExit(f"found {n_tp} PWR test points, partition-spec test_points.expected_pwr says "
                             f"{self.S['test_points']['expected_pwr']}: check the test-point classification, then the spec")
        self.ctrl_hdrs = self.ctrl_bottom_headers()
        self.cur = design.parts         # the parts of the candidate being evaluated (graph, or with its planned changes)

    # -- planned content (W2 AREA-2) ---------------------------------------------------------------------------
    def planned(self, cand):
        """(parts, rows, blocks) of a candidate with candidates.<id>.planned.changes applied. A change is 'pending' while
        every one of its refs still has the graph value it names (while_mpn, or while_footprint for a header) and is then
        applied; it is 'in graph' when none has (GR-5A/GR-5B have put the new part into the graph, so the graph counts);
        a half-applied change stops the tool. rows: one status row per change; blocks: the reserved blocks of the pending
        changes that stand in for parts without a graph ref yet."""
        parts, rows, blocks = dict(self.D.parts), [], []
        for ch in cand.get("planned", {}).get("changes", []):
            def holds(r):
                p = self.D.parts.get(r)
                if p is None:
                    return False
                if "while_mpn" in ch:
                    return self.D.mpn.get(r) == ch["while_mpn"]
                return p["footprint"] == ch["while_footprint"][r]
            state = [holds(r) for r in ch["refs"]]
            if all(state):
                status = "pending"
            elif not any(state):
                status = "in graph"
            else:
                raise SystemExit(f"planned change {ch['id']}: only some of {ch['refs']} still have the graph value it replaces "
                                 "(a half-applied change): finish it in the graph or update candidates.<id>.planned")
            row = {"id": ch["id"], "refs": ch["refs"], "status": status, "owner": ch.get("owner")}
            rows.append(row)
            if status != "pending":
                continue
            to = ch["to"]
            if to.get("delete"):
                for r in ch["refs"]:
                    parts.pop(r)
                row["effect"] = "deleted"
            elif "blocks" in to:
                for r in ch["refs"]:
                    parts.pop(r)
                for b in to["blocks"]:
                    blocks.append(dict(b, stands_for=ch["refs"], area=b["w"] * b["d"]))
                row["effect"] = "reserved blocks " + ", ".join(b["id"] for b in to["blocks"])
            elif "merge_into" in to:
                keep = to["merge_into"]
                new = self.swapped(self.D.parts[keep], to)
                new.update(nets=sorted({n for r in ch["refs"] for n in self.D.parts[r]["nets"]}), merged_from=list(ch["refs"]))
                for r in ch["refs"]:
                    parts.pop(r)
                parts[keep] = new
                row["effect"] = f"merged into {keep} ({new['footprint']})"
            else:
                for r in ch["refs"]:
                    parts[r] = self.swapped(self.D.parts[r], to)
                row["effect"] = f"{to['footprint']} {to.get('mpn') or ''}".strip() + (f" x {to['count']}" if to.get("count", 1) > 1 else "")
        return parts, rows, blocks

    def swapped(self, p, to):
        """A part with the footprint, MPN, height and count of a planned change. A footprint that is not vendored yet is
        given as a linear series of two vendored footprints of the same family (to.series), at to.pins contacts."""
        fps = self.D.fps
        if "series" in to:
            (n0, f0), (n1, f1) = to["series"]["from"]
            i0, i1 = fps.get(f0), fps.get(f1)
            if not (i0 and i1 and i0["crtyd"] and i1["crtyd"]) or abs(i0["crtyd"][1] - i1["crtyd"][1]) > 1e-6:
                raise SystemExit(f"planned series {f0} / {f1}: not vendored, or not one family")
            k = (to["pins"] - n0) / (n1 - n0)
            w = i0["crtyd"][0] + (i1["crtyd"][0] - i0["crtyd"][0]) * k
            d = i0["crtyd"][1]
            field = (i0["tht_field"][0] + (i1["tht_field"][0] - i0["tht_field"][0]) * k, i0["tht_field"][1])
            pads, fp = to["pins"], to["series"]["footprint"]
        else:
            fp = to["footprint"]
            info = fps.get(fp)
            if info is None or info["crtyd"] is None:
                raise SystemExit(f"planned footprint {fp}: not in the vendored library (or no F.CrtYd)")
            (w, d), field, pads = info["crtyd"], info["tht_field"], info["tht_pads"]
        if "family" in to:
            f = dict(self.D.hh.get(to["family"]) or {}, **self.S["header_families"].get(to["family"], {}))
            h, hsrc, lb = f.get("h_mated", f.get("h")), f"harness header {to['family']}: " + (f.get("src") or ""), False
        else:
            h, hsrc, lb = self.D.height_for(to.get("mpn"), fp)
        n = to.get("count", 1)
        return dict(p, footprint=fp, w=w, d=d, area=w * d * n, count=n, h=h, h_src=hsrc, h_lower_bound=lb, module=False,
                    tht=pads > 0, tht_field=field, tht_pads=pads * n, planned_mpn=to.get("mpn"),
                    header_family=to.get("family", p["header_family"]))

    def move_to_bottom(self, cand, side):
        """Two-sided PWR-A (candidates.<id>.pwr_a_bottom): the listed chip refs move from PWR_A to PWR_A_BOTTOM."""
        B = cand["pwr_a_bottom"]
        pref = tuple(B["footprint_prefixes"])
        for ref in B["refs"]:
            p = self.cur.get(ref)
            if p is None or side.get(ref) != "PWR_A" or p["tp"] or p["header"] or p["tht"] or \
                    not p["footprint"].split(":", 1)[-1].startswith(pref):
                raise SystemExit(f"pwr_a_bottom: {ref} is not a PWR-A chip part of footprint_prefixes "
                                 f"({p and p['footprint']}, side {side.get(ref)})")
            side[ref] = "PWR_A_BOTTOM"

    def pwr_a_bottom(self, cand, side, pockets):
        """Bottom usable area of a two-sided PWR-A = outline - hole keep-outs - thermal_bond zones (boards.json PWR, with
        the planned zones of the candidate) - every top THT pin field + tht_margin on each side (an area sum: no positions,
        so a field that lies in a bond zone is counted twice; the bottom usable area is a lower bound)."""
        B = cand["pwr_a_bottom"]
        pref = tuple(B["footprint_prefixes"])
        mech = self.D.mech["PWR"]
        poly = [tuple(q) for q in mech["outline"]]
        zones = [list(z) for z in mech["thermal_bond"]]
        for k, z in B.get("thermal_bond_planned", {}).items():
            zones[int(k) - 1] = list(z)
        rects = [(x, y, x + w, y + h) for x, y, w, h in zones]
        if any(rect_overlap(a, b) > 0 for i, a in enumerate(rects) for b in rects[i + 1:]):
            raise SystemExit("pwr_a_bottom: thermal_bond zones overlap")
        r = mech["hole_keepout_d"] / 2
        bond = sum(poly_area(clip(poly, *rc)) for rc in rects)
        holes_in_bond = sum(circle_rect_overlap(c, r, rc) for c in mech["holes"] for rc in rects)
        geo = poly_area(poly) - len(mech["holes"]) * math.pi * r * r - bond + holes_in_bond
        m = B["tht_margin"]
        tht = sum((it["pin_field_mm"][0] + 2 * m) * (it["pin_field_mm"][1] + 2 * m) for it in pockets)
        tchk = [ref for ref in B["refs"] if any(ref == it["item"] for it in pockets)]
        top_chips = sorted(ref for ref, s in side.items() if s == "PWR_A" and not self.cur[ref]["tp"]
                           and self.cur[ref]["footprint"].split(":", 1)[-1].startswith(pref))
        return geo - tht, {"thermal_bond_zones_mm": [[rnd(v, 2) for v in z] for z in zones], "bond_zones_mm2": rnd(bond),
                           "hole_keepouts_mm2": rnd(len(mech["holes"]) * math.pi * r * r - holes_in_bond),
                           "outline_minus_holes_and_bond_mm2": rnd(geo), "top_tht_fields_plus_margin_mm2": rnd(tht),
                           "top_tht_items": len(pockets), "tht_margin_mm": m, "refs": len(B["refs"]),
                           "chip_refs_left_on_top": top_chips, "bottom_refs_with_tht": tchk}

    def group_domain(self, p):
        """Domain of the bare board parts of the same group (where a test point of that group lands)."""
        doms = {q["domain"] for q in self.D.parts.values() if not q["tp"] and q["sheet"] == p["sheet"] and q["group"] == p["group"]}
        if len(doms) == 1:
            return sorted(doms)[0]
        return self.S["test_points"]["group_domain"].get(f'{p["sheet"]}/{p["group"]}')

    # -- precision/Kelvin nets ---------------------------------------------------------------------------
    def sense_nets(self):
        kelvin, precision = set(), set()
        res = {}
        for p in self.D.parts.values():
            if "Kelvin" in p["value"]:
                kelvin |= set(p["nets"]) - {"GND"}
        for ref, c in self.D.comp.items():
            for pin in c["pins"]:
                if pin.get("net") and re.match(r"IN[+\-\u2212]\d?$", pin.get("name", "")):
                    precision.add(pin["net"])
            if ref.startswith("R") and re.search(r"0\.[15] ?%", c.get("value", "")):
                for pin in c["pins"]:
                    if pin.get("net"):
                        res.setdefault(pin["net"], set()).add(ref)
        for net, refs in res.items():
            ic_input = any(pin.get("net") == net and pin.get("type") == "input"
                           for c in self.D.comp.values() if not c["ref"].startswith("R") for pin in c["pins"])
            rail = net in self.D.power_flags or net in self.D.current or any(
                pin.get("net") == net and pin.get("type") in ("power_in", "power_out") for c in self.D.comp.values() for pin in c["pins"])
            if len(refs) >= 2 and ic_input and net != "GND" and not rail:
                precision.add(net)
        return kelvin, precision - {"GND"}

    # -- one candidate ---------------------------------------------------------------------------------
    def assign(self, cand):
        P = self.P
        groups_b = {(g["sheet"], g["group"]) for g in cand.get("pwr_b_groups", [])}
        groups_rear = {(g["sheet"], g["group"]) for g in cand.get("rear_groups", [])}
        groups_ctrl_to_b = {(g["sheet"], g["group"]) for g in cand.get("ctrl_groups_to_pwr_b", [])}
        pinned = set(cand.get("pinned_pwr_a", []))
        hB = cand.get("hB", P["hB"])
        side, override, rear_override = {}, [], []
        what_if = cand.get("what_if_height", {})
        for ref, p in sorted((r, self.cur[r]) for r in self.pwr_parts if r in self.cur):
            key = (p["sheet"], p["group"])
            if self.D.mpn.get(ref) in what_if:      # hypothetical replacement, reported as WHAT-IF only
                p = dict(p, h=what_if[self.D.mpn[ref]])
            if p["module"] and cand.get("pololu") == "plate":
                side[ref] = "PLATE"
                continue
            if p["header"]:
                side[ref] = "PWR_B" if p["domain"] in PWR_B_DOMAINS else "PWR_A"
                continue
            if key in groups_rear and ref not in pinned:
                if p["h"] is not None and p["h"] <= P["rear_board"]["h_max"] and not p["h_lower_bound"]:
                    side[ref] = "PCB_REAR"
                    continue
                rear_override.append(ref)
            if key in groups_b and ref not in pinned:
                if p["h"] is None:
                    raise SystemExit(f"{ref}: no height for the PWR-B rule ({p['footprint']})")
                if p["h"] <= hB and not p["h_lower_bound"]:
                    side[ref] = "PWR_B"
                    continue
                override.append(ref)
            side[ref] = "PWR_A"
        for ref, p in sorted(self.ctrl_parts.items()):
            key = (p["sheet"], p["group"])
            if p["header"]:
                side[ref] = "CTRL"
                continue
            if key in groups_ctrl_to_b:
                side[ref] = "PWR_B" if p["h"] is not None and p["h"] <= hB else "CTRL"
            else:
                side[ref] = "CTRL"
        return side, override, rear_override

    def place_headers(self, side, cand):
        """PWR headers: the power families of the spec on PWR-A (uncovered edge strips); the others on the side
        that holds most of their nets (ties to PWR-B), in the first family variant that fits under hB there."""
        hdrs = self.D.consolidated_headers("PWR")
        home = {}
        for ref, s in side.items():
            for n in self.cur[ref]["nets"]:
                home.setdefault(n, set()).add("PWR_A" if s == "PWR_A_BOTTOM" else s)
        pinned = cand.get("header_side", {})
        power = cand.get("pwr_a_families", self.S["header_orientation"]["pwr_a_families"])
        free = []
        for h in hdrs:
            if h["id"] in pinned:
                h["board"] = pinned[h["id"]]
            elif h["family"].split("_")[0] in power:
                h["board"] = "PWR_A"
            else:
                h["board"] = "PWR_B"
                free.append(h)
        for _ in range(2):           # greedy: each signal header on the side where fewer of its nets cross
            for h in free:
                where = {}
                for n, sides in home.items():
                    where[n] = set(sides)
                for g in hdrs:
                    if g is not h:
                        for n in g["nets"]:
                            where.setdefault(n, set()).add(g["board"])
                nets = set(h["nets"]) - {"GND"}
                cross_b = sum(1 for n in nets if "PWR_A" in where.get(n, set()))
                cross_a = sum(1 for n in nets if "PWR_B" in where.get(n, set()))
                h["board"] = "PWR_A" if cross_a < cross_b else "PWR_B"
        for h in hdrs:
            if h["board"] == "PWR_B":
                self.fit_on_b(h, cand.get("hB", self.P["hB"]))
        return hdrs

    def fit_on_b(self, h, hB):
        """Family variant of a PWR-B header: the first variant (top entry first) whose mated height fits under
        hB; a header with no fitting variant (or no read height) moves to PWR-A."""
        base = h["family"].split("_")[0]
        for fam in self.S["header_orientation"]["variants"].get(base, [h["family"]]):
            f = self.D.family(fam)
            ht = f.get("h_mated", f.get("h"))
            if ht is not None and ht <= hB:
                w, d, _ = self.D.header_size(fam, h["pins"])
                h.update(family=fam, w=w, d=d, area=w * d, h=ht)
                return
        h["board"] = "PWR_A"

    def crossing(self, side, hdrs):
        pins = {}
        for ref, s in side.items():
            s = "PWR_A" if s == "PWR_A_BOTTOM" else s     # both sides of PWR-A are one board
            if s not in ("PWR_A", "PWR_B"):
                continue
            for n in self.cur[ref]["nets"]:
                pins.setdefault(n, {}).setdefault(s, []).append(ref)
        for h in hdrs:
            for n in h["nets"]:
                pins.setdefault(n, {}).setdefault(h["board"], []).append(h["id"])
        return {n: v for n, v in pins.items() if n != "GND" and len(v) == 2}

    def low_ohm_links(self, max_ohm):
        """W2 B2B review R2 (the rule of pcb/prepare.py low_ohm_links): nets that a resistor below max_ohm joins to a net other
        than GND, such as the 0.22 ohm damper nodes; they sit at the potential of that net (rail nodes of b2b.guard_rule)."""
        out = {}
        def ref_key(s):  # the ref order of pcb/prepare.py sort_ref
            m = re.fullmatch(r"([^0-9]+)([0-9]+)", s)
            return (m[1], int(m[2])) if m else (s, 0)
        for ref in sorted(self.D.comp, key=ref_key):
            c = self.D.comp[ref]
            m = re.match(r"\s*(\d+(?:\.\d+)?)\s*(R|Ω|m)", c.get("value", "")) if c.get("kind") == "resistor" else None
            if not m:
                continue
            nets = [pin.get("net") for pin in c["pins"] if pin.get("net")]
            if float(m.group(1)) * (1e-3 if m.group(2) == "m" else 1.0) >= max_ohm or len(set(nets)) != 2 or "GND" in nets:
                continue
            a, b = nets
            out.setdefault(a, f"{ref} {c['value']} to {b}")
            out.setdefault(b, f"{ref} {c['value']} to {a}")
        return out

    def b2b_budget(self, cross, contacts):
        P, S = self.P, self.S
        kelvin, precision = self.sense_nets()
        declared = {n for pair in S["b2b"]["declared_sense_pairs"] for n in pair["nets"]}
        links = self.low_ohm_links(S["b2b"]["rail_node_max_ohm"])
        extra = S["b2b"]["net_current_extra"]
        rows, errors = [], []
        power_types = ("power_in", "power_out")
        for net in sorted(cross):
            row = {"net": net, "pwr_a": sorted(cross[net]["PWR_A"]), "pwr_b": sorted(cross[net]["PWR_B"])}
            if net in declared:
                row.update(kind="declared sense pair", pins=1)
            elif net in S["b2b"]["sense_taps"]:
                row.update(kind="sense/supply tap", pins=1, why=S["b2b"]["sense_taps"][net])
            elif net in kelvin or net in precision:
                row.update(kind="Kelvin/precision (refused)", pins=1)
                errors.append(f"{net}: Kelvin/precision net crosses PWR-A/PWR-B and is not a declared sense pair")
            else:
                prot, src = None, None
                if net in self.D.current:
                    prot, src = self.D.current[net]["prot"], "tools/assembly_data.py NET_CURRENT (protection limit)"
                elif net in extra:
                    e = extra[net]
                    if "sum_of" in e:
                        prot = sum(self.D.current[x]["prot"] for x in e["sum_of"])
                    else:
                        prot = e["prot_A"]
                    src = e["src"]
                refs = [o for ref in cross[net]["PWR_A"] + cross[net]["PWR_B"] for o in self.cur.get(ref, {}).get("merged_from", [ref])]
                is_power = prot is not None or net in self.D.power_flags or any(
                    pin.get("net") == net and pin.get("type") in power_types
                    for ref in refs if ref in self.D.comp for pin in self.D.comp[ref]["pins"])
                if is_power and prot is None:
                    row.update(kind="power (no current)", pins=None)
                    errors.append(f"{net}: power net crosses PWR-A/PWR-B without a protection current")
                elif is_power:
                    row.update(kind="power", prot_A=rnd(prot, 3), current_src=src, pins=math.ceil(prot / P["b2b_i_pin_A"] - 1e-9))
                elif net in links:
                    row.update(kind="rail node", pins=1, why=links[net])
                else:
                    row.update(kind="signal", pins=1)
            rows.append(row)
        n_power = sum(1 for r in rows if r["kind"] == "power")
        pins = sum(r["pins"] or 0 for r in rows)
        # W2 B2B: the LSHM pair has no ground plane. b2b.guard_rule (review R2): every rail contact (power, sense/supply tap,
        # rail node) has its GND return beside it (since 11.11.2026 the next contact of its row), plus a GND guard column beside
        # each crossing declared sense pair and one GND guard after the rail block
        rail = sum(r["pins"] or 0 for r in rows if r["kind"] in ("power", "sense/supply tap", "rail node"))
        pairs = sum(1 for pair in S["b2b"]["declared_sense_pairs"] if all(n in cross for n in pair["nets"]))
        guards = 2 * pairs + (1 if rail else 0)
        gnd = rail * S["b2b"]["gnd_pins_per_power_contact"] + guards
        with_spare = math.ceil((pins + gnd) * (1 + S["b2b"]["spare_fraction"]) - 1e-9)
        return {"nets": rows, "power_nets": n_power, "signal_pins": sum(r["pins"] for r in rows if r["kind"] != "power" and r["pins"]),
                "power_pins": sum(r["pins"] or 0 for r in rows if r["kind"] == "power"), "gnd_pins": gnd, "guard_pins": guards,
                "contacts_needed": pins + gnd, "contacts_with_spare": with_spare, "contacts_available": contacts,
                "meets_spare_rule": with_spare <= contacts,
                "fits": pins + gnd <= contacts and not errors, "errors": errors}

    def evaluate(self, cid):
        cand = self.S["candidates"][cid]
        P = self.P
        hA = cand.get("hA", P["hA"])
        hB = cand.get("hB", P["hB"])
        stack = cand.get("stack", P["stack"])
        bb = dict(self.S["b2b"])
        bb.update(cand.get("b2b", {}))       # a candidate may evaluate another B2B size (contacts, courtyards)
        graph = None
        if "planned" in cand:
            # W2 AREA-2: the graph of record (no planned change) gives what pcb/prepare.py and b2b-nets.json follow today
            self.cur = self.D.parts
            g_side, g_override, _ = self.assign(cand)
            g_b2b = self.b2b_budget(self.crossing(g_side, self.place_headers(g_side, cand)), bb["contacts"])
            graph = {"height_overrides_to_pwr_a": g_override,
                     "b2b": {k: g_b2b[k] for k in ("power_pins", "signal_pins", "gnd_pins", "contacts_needed", "contacts_with_spare",
                                                   "meets_spare_rule", "fits", "errors")} | {"crossing_nets": len(g_b2b["nets"])}}
            self.cur, changes, blocks = self.planned(cand)
        else:
            self.cur, changes, blocks = self.D.parts, [], []
        side, override, rear_override = self.assign(cand)
        if "pwr_a_bottom" in cand:
            self.move_to_bottom(cand, side)
        hdrs = self.place_headers(side, cand)
        cross = self.crossing(side, hdrs)
        b2b = self.b2b_budget(cross, bb["contacts"])
        if cand.get("ctrl_unresolved_to_pwr_a"):
            # rule_gr3 'otherwise the function moves to PWR': the CTRL headers without a height-valid bottom variant
            # are counted on PWR-A (area, edge strip, THT pockets); their nets are not modelled on PWR
            for h in self.ctrl_hdrs:
                if h["unresolved"]:
                    hdrs.append(dict(h, board="PWR_A", nets=[], moved_from="CTRL"))
        m = P["window_margin"]
        outline = poly_area([tuple(p) for p in self.D.mech["PWR"]["outline"]])
        holes = len(self.D.mech["PWR"]["holes"]) * math.pi * (self.D.mech["PWR"]["hole_keepout_d"] / 2) ** 2
        boards = {}

        def acc(board):
            return boards.setdefault(board, {"parts_raw": 0.0, "modules": 0.0, "headers_raw": 0.0, "b2b_raw": 0.0,
                                             "tps_raw": 0.0, "keepouts": 0.0, "refs": 0, "headers": 0, "tht_pads": 0})
        windows, tp_windows, strips = 0.0, 0.0, 0.0
        win_refs, win_lower_bound = [], []
        for blk in blocks:
            # reserved blocks (W2 AREA-2) count as part area on their side; one taller than hA would need a PWR-B window
            b = acc(blk["side"])
            b["blocks_raw"] = b.get("blocks_raw", 0.0) + blk["area"]
            if blk["side"] == "PWR_A" and blk["h"] > hA:
                windows += (blk["w"] + 2 * m) * (blk["d"] + 2 * m)
                win_refs.append(blk["id"])
        for ref, s in sorted(side.items()):
            p = self.cur[ref]
            if s == "CTRL":
                continue
            if s == "PLATE":
                continue
            b = acc(s)
            b["refs"] += p.get("count", 1)
            b["tht_pads"] += p["tht_pads"] if p["tht"] else 0
            if p["header"]:
                b["headers_raw"] += p["area"]
                b["headers"] += 1
                if s == "PWR_A":
                    strips += (p["w"] + 2 * m) * (p["d"] + m)
                continue
            if p["module"]:
                b["modules"] += p["area"]
            elif p["tp"]:
                b["tps_raw"] += p["area"]
            else:
                b["parts_raw"] += p["area"]
            what_if = self.D.mpn.get(ref) in cand.get("what_if_height", {})
            h_eff = cand["what_if_height"][self.D.mpn[ref]] if what_if else p["h"]
            lower_bound = p["h_lower_bound"] and not what_if
            # a lower-bound height (holder without its fuse) always gets a window: the real height is above it
            if s == "PWR_A" and h_eff is not None and (h_eff > hA or lower_bound) and not p["tp"]:
                windows += (p["w"] + 2 * m) * (p["d"] + 2 * m) * p.get("count", 1)
                win_refs.append(ref)
                if lower_bound:
                    win_lower_bound.append(ref)
            if s == "PWR_A" and p["tp"]:
                tp_windows += (P["tp_probe_window"]) ** 2
        for h in hdrs:
            b = acc(h["board"])
            b["headers_raw"] += h["area"]
            b["headers"] += 1
            if h["board"] == "PWR_A":
                strips += (h["w"] + 2 * m) * (h["d"] + m)
        bw, bd = bb["courtyard_pwr_a"]
        acc("PWR_A")["b2b_raw"] += bw * bd
        bw, bd = bb["courtyard_pwr_b"]
        acc("PWR_B")["b2b_raw"] += bw * bd
        # PWR-A keepouts under the THT pin fields of PWR-B parts and headers (their tails reach into the stack)
        keep, keep_items, pockets = 0.0, [], []
        for ref, s in sorted(side.items()):
            p = self.cur[ref]
            if s == "PWR_B" and p["tht"] and p["tht_field"]:
                keep += (p["tht_field"][0] + 2 * m) * (p["tht_field"][1] + 2 * m)
                keep_items.append({"item": ref, "pin_field_mm": [rnd(p["tht_field"][0], 2), rnd(p["tht_field"][1], 2)]})
            if s == "PWR_A" and p["tht"] and p["tht_pads"]:
                pockets.append({"item": ref, "tht_pads": p["tht_pads"], "pin_field_mm": [rnd(p["tht_field"][0], 2), rnd(p["tht_field"][1], 2)]})
        for h in hdrs:
            fw, fh = self.pin_field(h)
            if h["board"] == "PWR_B":
                keep += (fw + 2 * m) * (fh + 2 * m)
                keep_items.append({"item": h["id"], "pin_field_mm": [rnd(fw, 2), rnd(fh, 2)]})
            else:
                pockets.append({"item": h["id"], "tht_pads": h["pins"], "pin_field_mm": [rnd(fw, 2), rnd(fh, 2)]})
        # rule H-TRIM (W2 AREA-2, candidates.<id>.h_trim): PWR-B THT pins trimmed to the protrusion limit, so the field
        # under them is a height zone for low-profile PWR-A parts and costs no area; otherwise the keepout counts at 1.0
        h_trim = bool(cand.get("h_trim"))
        acc("PWR_A")["keepouts"] += 0.0 if h_trim else keep
        usable = {"PWR_A": outline - holes,
                  "PWR_B": outline - holes - windows - strips - tp_windows}
        bottom = None
        if "pwr_a_bottom" in cand:
            usable["PWR_A_BOTTOM"], bottom = self.pwr_a_bottom(cand, side, pockets)
            acc("PWR_A_BOTTOM")
        if "PCB_REAR" in boards:
            usable["PCB_REAR"] = P["rear_board"]["area"] - P["rear_board"]["holes"] * math.pi * (P["rear_board"]["hole_keepout_d"] / 2) ** 2
        rear_links = sorted(n for n in {n for r, s in side.items() if s == "PCB_REAR" for n in self.cur[r]["nets"]} - {"GND"}
                            if any(side.get(r) in ("PWR_A", "PWR_B") and n in self.cur[r]["nets"] for r in side))
        env = self.S["envelope"]
        res = {"title": cand["title"], "hA": hA, "hB": hB, "stack": stack,
               "window_ceiling_mm": rnd(stack + P["board_t"] + hB, 2),
               "dz_mezz_mm": rnd(env["pwr_top_z"] + stack + P["board_t"] + hB + env["air_channel"] - env["display_z"], 2),
               "boards": {}, "windows_mm2": rnd(windows), "window_refs": win_refs,
               "window_refs_height_lower_bound": win_lower_bound,
               "ctrl_headers_moved_to_pwr_a": [h["id"] for h in hdrs if h.get("moved_from") == "CTRL"],
               "pcb_rear_harness_nets": rear_links,
               "edge_strips_mm2": rnd(strips), "tp_probe_windows_mm2": rnd(tp_windows),
               "pwr_a_keepouts_mm2": rnd(0.0 if h_trim else keep), "pwr_a_keepout_items": keep_items, "pwr_a_tht_pocket_items": pockets,
               "height_overrides_to_pwr_a": override, "rear_overrides_to_pwr_a": rear_override,
               "b2b": b2b}
        if "h_trim" in cand:
            res["h_trim"] = {"applied": h_trim, "pin_field_zone_mm2": rnd(keep), "zone_h_max_mm": self.S["keepouts"]["h_trim"]["zone_h_max_mm"],
                             "counted_keepout_mm2": rnd(0.0 if h_trim else keep)}
        if "planned" in cand:
            res["planned"] = {"changes": changes,
                              "blocks": [{"id": b["id"], "side": b["side"], "w": b["w"], "d": b["d"], "area_mm2": rnd(b["area"], 2),
                                          "h": b["h"], "stands_for": b["stands_for"]} for b in blocks],
                              "graph_of_record": graph}
        if bottom is not None:
            res["pwr_a_bottom"] = bottom
        fits_all = True
        for name in sorted(boards):
            b = boards[name]
            raw = b["parts_raw"] + b["headers_raw"] + b["b2b_raw"] + b["tps_raw"] + b.get("blocks_raw", 0.0)
            u = usable[name]
            row = {"usable_mm2": rnd(u), "refs": b["refs"], "harness_headers": b["headers"], "tht_pads": b["tht_pads"],
                   "parts_raw_mm2": rnd(b["parts_raw"]), "headers_raw_mm2": rnd(b["headers_raw"]), "b2b_raw_mm2": rnd(b["b2b_raw"]),
                   "tps_raw_mm2": rnd(b["tps_raw"]), "modules_at_1_0_mm2": rnd(b["modules"]), "keepouts_at_1_0_mm2": rnd(b["keepouts"]),
                   **({"blocks_raw_mm2": rnd(b["blocks_raw"])} if "blocks_raw" in b else {}),
                   "raw_fill": rnd((raw + b["modules"] + b["keepouts"]) / u, 3)}
            for f in P["factors"]:
                need = f * raw + b["modules"] + b["keepouts"]
                row[f"demand_{f:g}_mm2"] = rnd(need)
                row[f"ratio_{f:g}"] = rnd(u / need, 3)
            fmax = max(P["factors"])
            row["fits_at_1_8"] = row[f"ratio_{fmax:g}"] >= 1.0
            fits_all &= row["fits_at_1_8"]
            res["boards"][name] = row
        res["headers"] = [dict({"id": h["id"], "board": h["board"], "family": h["family"], "pins": h["pins"],
                                "w": rnd(h["w"], 2), "d": rnd(h["d"], 2), "h": h["h"]},
                               **({"moved_from": "CTRL"} if h.get("moved_from") else {})) for h in hdrs]
        res["fits"] = fits_all and b2b["fits"]
        res["side"] = side
        self.cur = self.D.parts
        return res

    def pin_field(self, h):
        if h.get("tht_field"):
            return h["tht_field"]
        fam = self.D.family(h["family"])
        pf = fam.get("pin_field")
        if pf is None:
            raise SystemExit(f"header family {h['family']}: no pin_field in the spec")
        n = math.ceil(h["pins"] / 2) if fam.get("per_row") else h["pins"]
        return pf["a"] * (n - 1) + pf["b"], pf["d"]

    # -- CTRL two-sided ------------------------------------------------------------------------------------
    def ctrl_bottom_headers(self):
        """CTRL harness headers with their bottom-side variant: the first variant of ctrl.bottom_header_rule
        that has a courtyard and a read height h (mated if given) with h + clearance - gap <= the dz cap. A header
        with no such variant keeps its base courtyard and is marked unresolved (no height-valid variant)."""
        S = self.S["ctrl"]
        rule = S["bottom_header_rule"]
        cap = self.S["envelope"]["cap"]["dz_max"]
        out = []
        cand = list(self.D.consolidated_headers("CTRL"))
        for ref, p in sorted(self.ctrl_parts.items()):
            if p["header"]:
                hr = self.D.header_rows[ref]
                cand.append({"id": ref, "label": hr["label"], "unit": "CTRL", "segment": hr["segment"], "family": p["header_family"],
                             "pins": int(hr["pins"]), "nets": p["nets"], "w": p["w"], "d": p["d"], "area": p["area"], "h": p["h"],
                             "tht_field": p["tht_field"], "graph_ref": True})
        for h in cand:
            h = dict(h, unresolved=False, dz=None, tried=[])
            if h.get("graph_ref"):
                # the variant is fixed by the footprint of the graph ref: judge its read height only
                ht = h["h"]
                if ht is None:
                    h["tried"].append(f"{h['family']}: height not read (TBD)")
                    h["unresolved"] = True
                else:
                    dz = ht + rule["clearance_mm"] - rule["gap_mm"]
                    if dz > cap + 1e-9:
                        h["tried"].append(f"{h['family']}: h {ht:g} + {rule['clearance_mm']:g} - {rule['gap_mm']:g} = {dz:.1f} > dz cap {cap:g}")
                        h["unresolved"] = True
                    else:
                        h["dz"] = rnd(max(dz, 0.0), 2)
                out.append(h)
                continue
            if h["id"] in S["headers_top"]:
                out.append(h)
                continue
            base = h["family"].split("_")[0]
            for fam_id in rule["variants"].get(base, [h["family"]]):
                fam = self.D.family_or_none(fam_id)
                ht = None if fam is None else (fam.get("h_mated") if fam.get("h_mated") is not None else fam.get("h"))
                if fam is None:
                    h["tried"].append(f"{fam_id}: no courtyard formula (TBD)")
                    continue
                if ht is None:
                    h["tried"].append(f"{fam_id}: height not read (TBD)")
                    continue
                dz = ht + rule["clearance_mm"] - rule["gap_mm"]
                if dz > cap + 1e-9:
                    h["tried"].append(f"{fam_id}: h {ht:g} + {rule['clearance_mm']:g} - {rule['gap_mm']:g} = {dz:.1f} > dz cap {cap:g}")
                    continue
                w, d, _ = self.D.header_size(fam_id, h["pins"])
                h.update(family=fam_id, w=w, d=d, area=w * d, h=ht, dz=rnd(max(dz, 0.0), 2))
                break
            else:
                h["unresolved"] = True
            out.append(h)
        return out

    def ctrl(self, cid, moved_to_b=()):
        P, S = self.P, self.S["ctrl"]
        mech = self.D.mech["CTRL"]
        outline = poly_area([tuple(p) for p in mech["outline"]]) - sum(c[2] * c[3] for c in mech.get("cutouts", []))
        holes = len(mech["holes"]) * math.pi * (mech["hole_keepout_d"] / 2) ** 2
        bottom_prefix = tuple(S["bottom_footprint_prefixes"])
        top = {"parts_raw": 0.0, "modules": 0.0, "headers_raw": 0.0, "tps_raw": 0.0, "tht_fields_other_side": 0.0}
        bot = {"parts_raw": 0.0, "modules": 0.0, "headers_raw": 0.0, "tps_raw": 0.0, "tht_fields_other_side": 0.0}
        m = P["window_margin"]
        tht_top = 0
        for ref, p in sorted(self.ctrl_parts.items()):
            if ref in moved_to_b or p["header"]:
                continue  # header refs are counted by self.ctrl_hdrs (bottom side)
            name = p["footprint"].split(":", 1)[-1]
            on_bottom = (not p["tp"]) and name.startswith(bottom_prefix) and ref not in S["keep_top_refs"]
            tgt = bot if on_bottom else top
            if p["module"]:
                tgt["modules"] += p["area"]
            elif p["tp"]:
                tgt["tps_raw"] += p["area"]
            else:
                tgt["parts_raw"] += p["area"]
            if p["tht"] and p["tht_field"]:
                fw, fh = p["tht_field"]
                (top if on_bottom else bot)["tht_fields_other_side"] += (fw + 2 * m) * (fh + 2 * m)
                tht_top += 0 if on_bottom else p["tht_pads"]
        to_pwr = bool(self.S["candidates"][cid].get("ctrl_unresolved_to_pwr_a"))
        hdr_rows, unresolved = [], []
        for h in self.ctrl_hdrs:
            if h["unresolved"]:
                unresolved.append({"id": h["id"], "family": h["family"], "pins": h["pins"], "area_mm2": rnd(h["area"]),
                                   "tried": h["tried"], "counted_on": "PWR_A" if to_pwr else "CTRL bottom (base courtyard)"})
                if to_pwr:
                    continue
            on_top = h["id"] in S["headers_top"]
            tgt = top if on_top else bot
            tgt["headers_raw"] += h["area"]
            fw, fh = self.pin_field(h)
            # a bottom THT header is hand-soldered from the top: its pin field plus iron access is lost on top
            (bot if on_top else top)["tht_fields_other_side"] += (fw + 2 * S["iron_access_margin"]) * (fh + 2 * S["iron_access_margin"])
            hdr_rows.append({"id": h["id"], "side": "top" if on_top else "bottom", "family": h["family"], "pins": h["pins"],
                             "w": rnd(h["w"], 2), "d": rnd(h["d"], 2), "h": h["h"], "dz": h["dz"],
                             "height_valid": not h["unresolved"]})
        placed_dz = [h["dz"] for h in self.ctrl_hdrs if not h["unresolved"] and h["dz"] is not None]
        # bottom strip over the Lime module: gap 1.4 mm + dz (fit-report layout), no headers there
        place = mech["place"]["origin"]
        poly = [(x + place[0], y + place[1]) for x, y in mech["outline"]]
        lx0, ly0, lx1, ly1 = S["lime_band"]["rect"]
        band = poly_area(clip(poly, lx0, ly0, lx1, ly1)) if clip(poly, lx0, ly0, lx1, ly1) else 0.0
        for cx, cy, cw, ch in mech.get("cutouts", []):
            band -= rect_overlap((cx + place[0], cy + place[1], cx + place[0] + cw, cy + place[1] + ch), (lx0, ly0, lx1, ly1))
        out = {"outline_mm2": rnd(outline), "holes_mm2": rnd(holes), "lime_band_mm2": rnd(band), "headers": hdr_rows,
               "headers_unresolved": unresolved, "dz_ctrl_mm": max(placed_dz) if placed_dz else 0.0,
               "tht_pads_top_parts": tht_top, "sides": {}}
        fmax = max(P["factors"])
        for name, s, extra_loss in (("top", top, 0.0), ("bottom", bot, band)):
            u = outline - holes - s["tht_fields_other_side"] - extra_loss
            raw = s["parts_raw"] + s["headers_raw"] + s["tps_raw"]
            row = {"usable_mm2": rnd(u), "parts_raw_mm2": rnd(s["parts_raw"]), "headers_raw_mm2": rnd(s["headers_raw"]),
                   "tps_raw_mm2": rnd(s["tps_raw"]), "modules_at_1_0_mm2": rnd(s["modules"]),
                   "tht_fields_of_other_side_mm2": rnd(s["tht_fields_other_side"]), "raw_fill": rnd((raw + s["modules"]) / u, 3)}
            for f in P["factors"]:
                need = f * raw + s["modules"]
                row[f"demand_{f:g}_mm2"] = rnd(need)
                row[f"ratio_{f:g}"] = rnd(u / need, 3)
            row["fits_at_1_8"] = row[f"ratio_{fmax:g}"] >= 1.0
            out["sides"][name] = row
        # area alone is not a fit while a header has no height-valid place
        out["fits"] = all(v["fits_at_1_8"] for v in out["sides"].values()) and not (unresolved and not to_pwr)
        return out


# ------------------------------------------------------------------------------------------ report
def current_boards(design):
    """Raw courtyard sums per current board (the MECH-1 cross-check: fit-report within 1 %)."""
    out = {}
    for board, doms in CURRENT_BOARDS.items():
        parts = [p for p in design.parts.values() if not p["tp"] and p["domain"] in doms]
        out[board] = {"refs": len(parts), "parts_raw_mm2": rnd(sum(p["area"] for p in parts if not p["module"])),
                      "modules_mm2": rnd(sum(p["area"] for p in parts if p["module"])),
                      "total_raw_mm2": rnd(sum(p["area"] for p in parts))}
    hdr = {}
    for h in design.headers_raw:
        if h["unit"] in ("PWR", "CTRL", "RF"):
            fam = h["family"]
            key = fam + ("_side" if fam == "PH" and h["unit"] in ("CTRL", "RF") else "_top")
            c = design.hh[key]
            hdr.setdefault(h["unit"], 0.0)
            hdr[h["unit"]] += (c["a"] * (h["pins"] - 1) + c["b"]) * c["d"]
    for k, v in hdr.items():
        out[k]["harness_headers_raw_mm2_build16"] = rnd(v)
    return out


def group_table(design, ev):
    rows = []
    seen = {}
    for p in sorted(ev.pwr_parts.values(), key=lambda p: (p["sheet"], p["group"], p["ref"])):
        k = (p["sheet"], p["group"])
        r = seen.get(k)
        if r is None:
            r = seen[k] = {"sheet": p["sheet"], "group": p["group"], "refs": 0, "raw_mm2": 0.0, "tall_refs": [], "tht_refs": [], "headers_only": True}
            rows.append(r)
        r["headers_only"] = r["headers_only"] and p["header"]
        r["refs"] += 1
        r["raw_mm2"] += p["area"]
        if p["h"] is not None and p["h"] > ev.P["hB"] and not p["tp"]:
            r["tall_refs"].append(p["ref"])
        if p["tht"]:
            r["tht_refs"].append(p["ref"])
    for r in rows:
        r["raw_mm2"] = rnd(r["raw_mm2"])
    return rows


def heights_table(design, ev):
    out = {}
    for p in sorted(ev.pwr_parts.values(), key=lambda p: p["ref"]):
        if p["tp"] or p["h"] is None or p["h"] <= ev.P["hA"]:
            continue
        key = design.mpn.get(p["ref"]) or p["footprint"]
        e = out.setdefault(key, dict({"h": p["h"], "src": p["h_src"], "refs": []},
                                     **({"lower_bound": True} if p["h_lower_bound"] else {})))
        e["refs"].append(p["ref"])
    return out


def build(spec):
    design = Design(spec)
    ev = Evaluator(design)
    P = spec["parameters"]
    report = {
        "schema": "srrx-partition-budget-v1",
        "generator": "pcb/partition_budget.py",
        "status": "MODEL ESTIMATE: courtyard sums and a partition rule, not a placement; hardware and proof-fit gates stay OPEN",
        "spec": rel(SPEC),
        "inputs": ["build/kicad/footprints/manifest.json", "pcb/generated/components.csv", "design/E1.json..E5.json",
                   "design/parts/parts.json", "build/16-dzhgut-rozyemy.csv", "mechanical/params/parts.json harness_headers",
                   "mechanical/params/boards.json", "tools/assembly_data.py NET_CURRENT"],
        "parameters": {k: P[k] for k in ("hA", "hB", "board_t", "stack", "window_margin", "factors", "b2b_i_pin_A")},
        "current_boards_raw": current_boards(design),
        "pwr_groups": group_table(design, ev),
        "pwr_heights_above_hA": heights_table(design, ev),
        "b2b_footprints": {},
        "candidates": {},
    }
    # W2 B2B: footprint and F.CrtYd of each board-to-board half (graph ref), which the spec courtyards must equal
    for half, ref in spec["b2b"].get("graph_refs", {}).items():
        fp = design.rows.get(ref, {}).get("footprint", "")
        info = design.fps.get(fp) if fp else None
        report["b2b_footprints"][half] = {"ref": ref, "footprint": fp,
                                          "crtyd_mm": [rnd(x, 2) for x in info["crtyd"]] if info and info["crtyd"] else None}
    for cid in spec["candidates"]:
        res = ev.evaluate(cid)
        side = res.pop("side")
        moved = sorted(r for r, s in side.items() if s == "PWR_B" and ev.D.parts[r]["domain"] == "CTRL_HMI")
        res["ctrl"] = ev.ctrl(cid, moved_to_b=moved)
        res["fits"] = res["fits"] and res["ctrl"]["fits"]
        res["pwr_b_refs"] = sorted(r for r, s in side.items() if s == "PWR_B")
        res["pcb_rear_refs"] = sorted(r for r, s in side.items() if s == "PCB_REAR")
        res["plate_refs"] = sorted(r for r, s in side.items() if s == "PLATE")
        report["candidates"][cid] = res
    chosen = spec["decision"]["chosen"]
    report["chosen"] = chosen
    report["chosen_fits"] = report["candidates"][chosen]["fits"]
    return report


def check_spec(spec, report):
    """The decision record must agree with the computed budget."""
    errs = []
    ch = spec["decision"]["chosen"]
    res = report["candidates"][ch]
    if res["b2b"]["errors"]:
        errs.append(f"chosen candidate {ch}: B2B rule violations: " + "; ".join(res["b2b"]["errors"]))
    if spec["decision"]["fits_at_1_8"] != res["fits"]:
        errs.append(f"decision.fits_at_1_8 is {spec['decision']['fits_at_1_8']} but the computed verdict is {res['fits']}")
    # a group of harness header refs (W2 GR-3) is placed by the pcb/prepare.py domain of each header, not by the group lists
    groups = {(g["sheet"], g["group"]) for g in report["pwr_groups"] if not g.get("headers_only")}
    rec = spec["partition"]
    listed_a = {(g["sheet"], g["group"]) for g in rec["PWR_A_groups"]}
    listed_b = {(g["sheet"], g["group"]) for g in rec["PWR_B_groups"]}
    both = listed_a & listed_b
    if both:
        errs.append(f"groups on both PWR_A and PWR_B: {sorted(both)}")
    missing = groups - listed_a - listed_b
    if missing:
        errs.append(f"PWR groups on neither list: {sorted(missing)}")
    unknown = (listed_a | listed_b) - groups
    if unknown:
        errs.append(f"listed groups that are not PWR groups: {sorted(unknown)}")
    cand_b = {(g["sheet"], g["group"]) for g in spec["candidates"][ch]["pwr_b_groups"]}
    if cand_b != listed_b:
        errs.append("partition.PWR_B_groups differs from the chosen candidate's pwr_b_groups")
    # W2 AREA-2: with planned changes the graph of record (what pcb/prepare.py and b2b-nets.json follow) and the planned state
    # are both recorded: domain_override_pwr_a / b2b.budget_chosen for the graph, the *_planned keys for the plan
    pinned = spec["candidates"][ch].get("pinned_pwr_a", [])
    graph = (res.get("planned") or {}).get("graph_of_record")
    g_over = graph["height_overrides_to_pwr_a"] if graph else res["height_overrides_to_pwr_a"]
    if sorted(rec["domain_override_pwr_a"]) != sorted(g_over + pinned):
        errs.append("partition.domain_override_pwr_a differs from the computed height overrides (graph of record) plus pinned refs: "
                    + json.dumps(sorted(g_over + pinned)) + (" (a planned change is in the graph now: take partition.domain_override_pwr_a_planned "
                                                             "and rerun pcb/prepare.py, pcb/write_b2b_graph.py and the protocol chain)" if graph else ""))
    if graph is not None and sorted(rec.get("domain_override_pwr_a_planned", [None])) != sorted(res["height_overrides_to_pwr_a"] + pinned):
        errs.append("partition.domain_override_pwr_a_planned differs from the computed planned overrides: "
                    + json.dumps(sorted(res["height_overrides_to_pwr_a"] + pinned)))
    b = res["b2b"]
    got = {"crossing_nets": len(b["nets"]), "power_pins": b["power_pins"], "signal_pins": b["signal_pins"],
           "gnd_pins": b["gnd_pins"], "contacts_needed": b["contacts_needed"], "contacts_with_spare": b["contacts_with_spare"]}
    if graph is not None:
        g = graph["b2b"]
        got_g = {k: g[k] for k in ("crossing_nets", "power_pins", "signal_pins", "gnd_pins", "contacts_needed", "contacts_with_spare")}
        if spec["b2b"]["budget_chosen"] != got_g:
            errs.append(f"b2b.budget_chosen {spec['b2b']['budget_chosen']} differs from the computed graph-of-record {got_g}")
        if not g["meets_spare_rule"] or g["errors"]:
            errs.append(f"chosen candidate {ch} on the graph of record: spare rule or B2B rule fails: {g['errors']}")
        if spec["b2b"].get("budget_planned") != got:
            errs.append(f"b2b.budget_planned {spec['b2b'].get('budget_planned')} differs from the computed {got}")
    elif spec["b2b"]["budget_chosen"] != got:
        errs.append(f"b2b.budget_chosen {spec['b2b']['budget_chosen']} differs from the computed {got}")
    if not b["meets_spare_rule"]:
        errs.append(f"chosen candidate {ch}: {b['contacts_with_spare']} contacts with spare exceed the {b['contacts_available']} of the B2B")
    ps = spec["decision"].get("placement_study")
    if ps:
        got_f = report["candidates"][ps["candidate"]]["boards"]["PWR_A"]["raw_fill"]
        if abs(got_f - ps["top_fill_all_refs"]) > ps["tolerance"] + 1e-9:
            errs.append(f"candidate {ps['candidate']} PWR_A raw_fill {got_f} is more than {ps['tolerance']} from the placement-study "
                        f"fill {ps['top_fill_all_refs']}")
    for half, row in report.get("b2b_footprints", {}).items():
        if row["footprint"] != spec["b2b"]["footprint"]:
            errs.append(f"B2B half {half} {row['ref']}: graph footprint {row['footprint']!r} is not b2b.footprint {spec['b2b']['footprint']!r}")
        if row["crtyd_mm"] != spec["b2b"][f"courtyard_{half}"]:
            errs.append(f"b2b.courtyard_{half} {spec['b2b'][f'courtyard_{half}']} differs from the F.CrtYd {row['crtyd_mm']} of {row['footprint']}")
    # every contact count the decision text quotes must be the computed one
    if "b2b_contacts_quoted" not in spec["decision"]:
        errs.append("decision.b2b_contacts_quoted is missing")
    for cid, n in spec["decision"].get("b2b_contacts_quoted", {}).items():
        got_n = report["candidates"].get(cid, {}).get("b2b", {}).get("contacts_needed")
        if got_n != n:
            errs.append(f"decision.b2b_contacts_quoted[{cid}] {n} differs from the computed {got_n}")
    got_short = {name: round(row["demand_1.8_mm2"] - row["usable_mm2"]) for name, row in res["boards"].items()
                 if row["demand_1.8_mm2"] > row["usable_mm2"]}
    got_short.update({f"CTRL_{name}": round(row["demand_1.8_mm2"] - row["usable_mm2"]) for name, row in res["ctrl"]["sides"].items()
                      if row["demand_1.8_mm2"] > row["usable_mm2"]})
    if spec["decision"]["shortfall_1_8_mm2"] != got_short:
        errs.append(f"decision.shortfall_1_8_mm2 {spec['decision']['shortfall_1_8_mm2']} differs from the computed {got_short}")
    got_unres = [h["id"] for h in res["ctrl"]["headers_unresolved"]]
    if spec["decision"].get("ctrl_headers_unresolved") != got_unres:
        errs.append(f"decision.ctrl_headers_unresolved {spec['decision'].get('ctrl_headers_unresolved')} differs from the computed {got_unres}")
    env = spec["envelope"]
    got_env = {"dz_mezz": res["dz_mezz_mm"], "dz_ctrl": res["ctrl"]["dz_ctrl_mm"],
               "dz": max(res["dz_mezz_mm"], res["ctrl"]["dz_ctrl_mm"])}
    want_env = {k: env.get(k) for k in got_env}
    if want_env != got_env:
        errs.append(f"envelope {want_env} differs from the computed {got_env}")
    got_ratios = {name: row["ratio_1.8"] for name, row in res["boards"].items()}
    got_ratios.update({f"CTRL_{name}": row["ratio_1.8"] for name, row in res["ctrl"]["sides"].items()})
    if spec["decision"]["ratios_1_8"] != got_ratios:
        errs.append(f"decision.ratios_1_8 {spec['decision']['ratios_1_8']} differs from the computed {got_ratios}")
    for fb in spec["fallbacks"]:
        for cid in fb.get("candidates", []):
            if cid not in report["candidates"]:
                errs.append(f"fallback {fb['id']}: candidate {cid} not evaluated")
                continue
            want = fb.get("ratios_1_8", {})
            r = report["candidates"][cid]
            got = {name: row["ratio_1.8"] for name, row in r["boards"].items()}
            got.update({f"CTRL_{name}": row["ratio_1.8"] for name, row in r["ctrl"]["sides"].items()})
            if want.get(cid) != got:
                errs.append(f"fallback {fb['id']}: ratios_1_8[{cid}] {want.get(cid)} differs from the computed {got}")
    return errs


def text_of(report):
    return json.dumps(report, ensure_ascii=False, indent=1) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail if partition-budget.json is stale or the spec disagrees")
    args = ap.parse_args()
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    report = build(spec)
    text = text_of(report)
    errs = check_spec(spec, report)
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            errs.insert(0, f"{rel(OUT)} is stale (run python pcb/partition_budget.py)")
        for e in errs:
            print("ERROR:", e)
        if errs:
            return 1
        verdict = "fits" if report["chosen_fits"] else "does NOT fit"
        print(f"{rel(OUT)} reproduces and agrees with {rel(SPEC)}; chosen candidate {report['chosen']} {verdict} at 1.8 (MODEL ESTIMATE)")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {rel(OUT)}; chosen {report['chosen']}; fits {report['chosen_fits']}")
    for e in errs:
        print("WARNING:", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
