"""Harness routes from the enclosure model (MODEL ESTIMATE): one polyline per build/16 segment.

mechanical.json harness_routes gives each segment a list of waypoints. A waypoint names the layout envelope, structure
part, plate slot, RF-bay notch, panel port or board edge zone it uses, so a moved item moves the route:

    {"box": "<item or structure box>", "at": [fx, fy, fz], "off": [dx, dy, dz]}   point in that box (fractions + offset)
    {"slot": "SL2", ...} / {"notch": "N4", ...} / {"window": "riser_window", ...}  plate and RF-bay openings
    {"port": "USB_C_IN", "off": [...]}                                             panel port centre on the inner wall face
    {"edge": "PWR", "zone": 3, "t": 0.5, "dz": 5}                                  board edge zone (header position TBD)
    "keep": "z"                                                                    take these axes from the previous point

Length = polyline + bend allowance (outer conductor of the bundle round each corner: OD/2 x angle) + the 2 x 15 mm service
loops of build/16. The bundle OD is an upper bound from the wire count of build/16-dzhgut.csv and the largest insulation
the end terminals accept (fill 0.6): no wire type is chosen yet (AI-WIRE-PTFE). Routes never read the build/16 length
column, so build/16 can take its lengths from generated/harness-routes.json without a loop.

The keep-clear check runs on the centreline: no straight piece may pass through a layout envelope, a keep-clear
reserve or a structure part, except the envelopes of its own ends and the plate / RF-bay wall inside an opening.
A route with an end that is not placed yet (board headers have no positions before the board layout; modules without
an envelope) is OPEN (end provisional), never FAIL.

W2 MECH-6: an edge end names the board-side header refs of its segment (build/16-dzhgut-rozyemy.csv, the GR-3 graph refs);
named points ({"box": "lc76g.p1"}, {"box": "q6a.mkey_tap"}) are connector or pad positions inside an envelope; coax routes
(harness_routes.coax, W407) have no service loops and are checked against the pigtail lengths (R-P7-PIGTAIL); a provisional
end with a bound_mm (end_status) lets R-PPS-LEN judge the worst case.
"""
import csv
import functools
import math
from pathlib import Path

from .layout import item_boxes, structure_boxes

ROOT = Path(__file__).resolve().parents[2]


def _openings(P):
    """Openings that a route may pass through: plate slots, riser window, open plate notches, RF-bay notches (enclosure boxes)."""
    m = P.mech
    pl = m["plate"]
    pr, pf = m["stack_z"]["plate_rear"], m["stack_z"]["plate_front"]
    out = {}
    for sl in pl.get("slots", []):
        x, y, w, h = sl["rect"]
        out[f"slot:{sl['id']}"] = ("plate.", (x, y, pr, x + w, y + h, pf))
    if "riser_window" in pl:
        x, y, w, h = pl["riser_window"]
        out["window:riser_window"] = ("plate.", (x, y, pr, x + w, y + h, pf))
    for i, (x, y, w, h) in enumerate(pl.get("notches", []) + pl.get("notches_right", [])):
        out[f"plate_notch:{i}"] = ("plate.", (x, y, pr, x + w + 5.0, y + h + 5.0, pf))   # open notches: run out of the plate edge
    rb = m["rf_bay"]
    x, y, w, h = rb["rect"]
    wt = rb["wall_t"]
    z1 = rb["lid_z"][1]
    for n in rb.get("notches", []):
        if n["wall"] == "bottom":
            out[f"notch:{n['id']}"] = ("rfbay.wall.bottom", (n["x"][0], y, z1, n["x"][1], y + wt, z1 + n["h"]))
    return out


def _port_box(P, pid):
    """Panel port centre on the inner face of its wall, as a flat box (x0, y0, z0, x1, y1, z1)."""
    m = P.mech
    W, H, D = P.outer
    t = m["wall"]
    for p in m["top_face"]["ports"]:
        if p["id"] == pid:
            z = m["top_face"]["ports_z"]
            return (p["x"], H - t, z, p["x"], H - t, z)
    for p in m["right_face"]["ports"] + m["right_face"].get("panel", []):
        if p["id"] == pid:
            return (W - t, p["y"], p["z"], W - t, p["y"], p["z"])
    for p in m["bottom_face"]["ports"]:
        if p["id"] == pid:
            return (p["x"], t, p["z"], p["x"], t, p["z"])
    if pid == "VEML7700":
        v = m["top_face"]["veml7700_window"]
        return (v["x"], H - t, v["z"], v["x"], H - t, v["z"])
    raise MissingWaypoint(f"port {pid}")


class MissingWaypoint(KeyError):
    """A waypoint names a box, opening, port or edge zone that the model does not have (renamed or removed item)."""


def boxes(P):
    """Every named box a waypoint can use and every obstacle of the keep-clear check."""
    named = {}
    for iid, name, bx, it in item_boxes(P):
        named[name if name not in named else f"{iid}/{name}"] = (iid, bx, it)   # ENC.r0 twice: enc_main, enc_volume/ENC.r0
    for name, bx in structure_boxes(P):
        named[name] = (name, bx, {})
    named.update(points(P))
    return named


def points(P):
    """Named points (zero-size boxes, never an obstacle): layout item 'points' (mm from the box minimum corner) and the Q6A
    VCC_3V3_MKEY tap (parts.json q6a.mkey_tap, board uv on its side), W2 MECH-6."""
    out = {}
    for it in P.mech["layout"]["items"]:
        if "points" in it and "box" in it:
            x, y, z = it["box"][:3]
            for name, off in it["points"].items():
                if name.startswith("_"):
                    continue
                p = (round(x + off[0], 3), round(y + off[1], 3), round(z + off[2], 3))
                out[f"{it['id']}.{name}"] = (it["id"], p + p, it)
    q = P.parts["q6a"]
    tap = q.get("mkey_tap")
    if tap:
        m = P.mech["q6a_mount"]
        x0, y0 = m["origin"]
        z_bot = P.mech["stack_z"]["plate_rear"] - m["standoff"]          # board face towards the plate (bottom side)
        z = z_bot if tap["side"] == "bottom" else z_bot - q["board"][2]
        p = (round(x0 + q["board"][0] - tap["uv"][0], 3), round(y0 + tap["uv"][1], 3), round(z, 3))
        out["q6a.mkey_tap"] = ("q6a", p + p, {"id": "q6a"})
    return out


@functools.lru_cache(maxsize=4)
def _header_rows(root):
    """(segment, unit) -> [(ref, label, board)] of build/16-dzhgut-rozyemy.csv (board-side headers, the GR-3 graph refs)."""
    path = Path(root) / "build" / "16-dzhgut-rozyemy.csv"
    out = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            for seg in r["segment"].split("+"):
                out.setdefault((seg, r["unit"]), []).append((r["connector"], r["label"], r["board"]))
    return out


EDGE_UNIT = {"PWR": "PWR", "PWR_B": "PWR", "CTRL": "CTRL", "RF": "RF", "ENC": {"main": "ENCM", "volume": "ENCV"}}


def edge_end_text(sid, wp, root=None):
    """Provisional reason of a route end on a board edge zone, naming the header refs of the segment on that board."""
    unit = EDGE_UNIT.get(wp["edge"])
    if isinstance(unit, dict):
        unit = unit.get(wp.get("at_place"))
    refs = _header_rows(str(root or ROOT)).get((sid, unit), [])
    if not refs:
        return f"{wp['edge']} header position TBD (board layout; GR-3 header refs): end on the edge zone"
    names = ", ".join(f"{ref} ({label}, {board})" if label and label != ref else f"{ref} ({board})" for ref, label, board in refs)
    return f"{names} position TBD (board placement): end on the {wp['edge']} edge zone {wp['zone']}"


def _edge_point(P, wp):
    """Point on a board edge zone (boards.json edge_zones), dz above the component face (towards the components)."""
    b = P.boards["boards"].get(wp["edge"])
    if b is None or not 0 <= wp["zone"] < len(b.get("edge_zones", [])):
        raise MissingWaypoint(f"edge {wp['edge']} zone {wp['zone']}")
    ez = b["edge_zones"][wp["zone"]]
    if "place_at" in b:
        ox, oy = b["place_at"][wp["at_place"]]
    else:
        ox, oy = b["place"]["origin"]
    xs, ys = [p[0] for p in b["outline"]], [p[1] for p in b["outline"]]
    a0, a1 = ez["span"]
    s = a0 + wp["s"] if "s" in wp else a0 + wp.get("t", 0.5) * (a1 - a0)
    if ez["edge"] == "bottom":
        x, y = ox + s, oy + min(ys)
    elif ez["edge"] == "top":
        x, y = ox + s, oy + ez.get("at", max(ys))
    elif ez["edge"] == "left":
        x, y = ox + min(xs), oy + s
    elif ez["edge"] == "right":
        x, y = ox + max(xs), oy + s
    else:
        raise KeyError(f"harness_routes: edge kind {ez['edge']} has no line")
    tb = P.boards["stackup"]["t"]
    pl = b["place"]
    dz = wp.get("dz", P.mech["harness_routes"]["edge_exit_mm"])
    z = pl["z_bottom"] + tb + dz if pl["facing"] == "+z" else pl["z_bottom"] - tb - dz
    return [x, y, z]


def point(P, wp, prev, named, opens):
    if "edge" in wp:
        p = _edge_point(P, wp)
    else:
        if "box" in wp:
            if wp["box"] not in named:
                raise MissingWaypoint(f"box {wp['box']}")
            bx = named[wp["box"]][1]
        elif "port" in wp:
            bx = _port_box(P, wp["port"])
        else:
            key = next(f"{k}:{wp[k]}" for k in ("slot", "notch", "window") if k in wp)
            if key not in opens:
                raise MissingWaypoint(key.replace(":", " "))
            bx = opens[key][1]
        f = wp.get("at", [0.5, 0.5, 0.5])
        p = [bx[i] + f[i] * (bx[i + 3] - bx[i]) for i in range(3)]
    off = wp.get("off", [0.0, 0.0, 0.0])
    p = [p[i] + off[i] for i in range(3)]
    for ax in wp.get("keep", ""):
        i = "xyz".index(ax)
        p[i] = prev[i]
    return [round(v, 3) for v in p]


def _seg_box(a, b, bx, eps=1e-6):
    """Parameter interval [t0, t1] of the segment a->b strictly inside the open box bx, or None."""
    t0, t1 = 0.0, 1.0
    for i in range(3):
        d = b[i] - a[i]
        lo, hi = bx[i] + eps, bx[i + 3] - eps
        if abs(d) < 1e-12:
            if not (lo < a[i] < hi):
                return None
            continue
        u0, u1 = (lo - a[i]) / d, (hi - a[i]) / d
        if u0 > u1:
            u0, u1 = u1, u0
        t0, t1 = max(t0, u0), min(t1, u1)
        if t0 >= t1:
            return None
    return t0, t1


def _within(p, bx, eps=1e-6):
    return all(bx[i] - eps <= p[i] <= bx[i + 3] + eps for i in range(3))


def wire_od(P, awg):
    """Largest OD (nominal + tolerance) of the chosen PTFE hook-up wire of this AWG (parts.json hookup_wire_ptfe), or None."""
    od = P.parts.get("hookup_wire_ptfe", {}).get("od", {}).get(str(awg))
    return round(od[0] + od[1], 3) if od else None


def bundle(P, sid, wires):
    """Bundle OD upper bound (mm) of a segment: largest wire OD x sqrt(n / fill). The wire OD is the chosen PTFE wire's
    (parts.json hookup_wire_ptfe, W2 MECH-6); a gauge without a read OD takes the largest insulation its terminals accept."""
    hr = P.mech["harness_routes"]
    ins = hr["insulation_max_mm"]
    rows = wires.get(sid, [])
    if sid in hr.get("flat", {}):
        return hr["flat"][sid]["thickness_mm"], len(rows)
    d = []
    for fam_a, fam_b, awg in rows:
        w = wire_od(P, awg)
        if w:
            d.append(w)
            continue
        for fam in (fam_a, fam_b):
            v = ins.get(fam)
            if isinstance(v, dict):
                v = v.get(awg)
            if v:
                d.append(v)
    dmax = max(d) if d else ins["default"]
    n = max(1, len(rows))
    return round(dmax * math.sqrt(n / hr["fill"]), 2), len(rows)


def build16_wires(root=None):
    """segment -> [(family_from, family_to, awg)] of build/16-dzhgut.csv (wire counts only; the length column is never read)."""
    path = (root or ROOT) / "build" / "16-dzhgut.csv"
    out = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            out.setdefault(r["segment"], []).append((r["family_from"], r["family_to"], r["awg"]))
    return out


def _end_boxes(P, wp, named):
    """Names of the envelopes an end waypoint stands in (excluded from its own keep-clear check)."""
    if "box" in wp:
        if wp["box"] in named and tuple(named[wp["box"]][1][:3]) == tuple(named[wp["box"]][1][3:]):
            return {wp["box"], named[wp["box"]][0]}     # a named point: also the envelope it sits in (its item id)
        return {wp["box"]}
    if "edge" in wp:
        bid = wp["edge"]
        return {n for n, (_, _, it) in named.items() if it.get("board") == bid}
    return set()


def evaluate_route(P, sid, spec, named, opens, wires, root=None):
    hr = P.mech["harness_routes"]
    via = spec.get("via", [])
    out = {"kind": spec.get("kind", "harness"), "ends": spec.get("ends", [])}
    if spec.get("note"):
        out["note"] = spec["note"]
    prov = [e["provisional"] for e in spec.get("end_status", []) if e.get("provisional")]
    bound = round(sum(e.get("bound_mm", 0.0) for e in spec.get("end_status", []) if e.get("provisional")), 1)
    for i in (0, -1):
        if via and "edge" in via[i]:
            prov.append(edge_end_text(sid, via[i], root))
    if not via and out["kind"] == "external":
        out.update({"points_mm": [], "length_mm": None, "provisional": [],
                    "status": "EXTERNAL: outside the enclosure; the length is set by the cable, not by the enclosure model"})
        return out
    if not via:
        out.update({"points_mm": [], "length_mm": None, "provisional": prov or [spec.get("open", "no route")],
                    "status": "OPEN (end provisional): " + (spec.get("open") or "no route")})
        return out
    pts = []
    try:
        for wp in via:
            pts.append(point(P, wp, pts[-1] if pts else None, named, opens))
    except MissingWaypoint as e:      # a renamed or removed layout item shows up as OPEN, not as a crash of build.py
        msg = f"waypoint {e.args[0]} not in the model"
        out.update({"points_mm": [], "length_mm": None, "provisional": prov + [msg], "status": "OPEN (end provisional): " + msg})
        return out
    path = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    if "od" in spec:                                   # a single cable (coax pigtail W407): its own OD
        od, n = spec["od"], 1
    else:
        od, n = bundle(P, sid, wires) if spec.get("wires") is None else (round(hr["insulation_max_mm"]["default"] * math.sqrt(spec["wires"] / hr["fill"]), 2), spec["wires"])
    bends, ang = 0, 0.0
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        u = [b[i] - a[i] for i in range(3)]
        v = [c[i] - b[i] for i in range(3)]
        lu, lv = math.sqrt(sum(x * x for x in u)), math.sqrt(sum(x * x for x in v))
        if lu < 1e-9 or lv < 1e-9:
            continue
        cosang = max(-1.0, min(1.0, sum(u[i] * v[i] for i in range(3)) / (lu * lv)))
        th = math.acos(cosang)
        if th > math.radians(1.0):
            bends += 1
            ang += th
    allowance = od / 2.0 * ang
    loops = sum(hr["service_loops_mm"]) if out["kind"] not in ("external", "coax") else 0.0
    total = path + allowance + loops
    # keep-clear check on the centreline
    exempt = _end_boxes(P, via[0], named) | _end_boxes(P, via[-1], named) | set(spec.get("touch", []))
    W, H, D = P.outer
    t = P.mech["wall"]
    interior = (t, t, t, W - t, H - t, D - t)
    crossings, through = [], []
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        for name, (iid, bx, it) in named.items():
            if name in exempt or iid in exempt or it.get("outside"):
                continue
            hit = _seg_box(a, b, bx)
            if hit is None:
                continue
            ia = [a[i] + hit[0] * (b[i] - a[i]) for i in range(3)]
            ib = [a[i] + hit[1] * (b[i] - a[i]) for i in range(3)]
            ok = None
            for oname, (owner, obx) in opens.items():
                if name.startswith(owner) and _within(ia, obx) and _within(ib, obx):
                    ok = oname
                    break
            if ok:
                if ok.split(":", 1)[1] not in through:
                    through.append(ok.split(":", 1)[1])
                continue
            crossings.append(f"piece {k + 1} through {name}")
        if out["kind"] != "external" and not (_within(a, interior) and _within(b, interior)):
            crossings.append(f"piece {k + 1} leaves the interior")
    out.update({"points_mm": pts, "path_mm": round(path, 1), "bends": bends, "bundle_od_mm": od, "wires": n,
                "bend_allowance_mm": round(allowance, 1), "service_loops_mm": loops,
                "length_mm": int(math.ceil(total - 1e-9)), "through": through, "crossings": crossings,
                "provisional": prov})
    if bound and prov:
        out["bound_mm"] = bound                        # worst-case extra length of the bounded provisional ends
    if crossings:
        out["status"] = ("OPEN (end provisional): route crosses a solid — re-route when the ends are placed: " if prov else "FAIL (model): ") + "; ".join(crossings)
    elif prov:
        out["status"] = "OPEN (end provisional): " + "; ".join(prov)
    else:
        out["status"] = "PASS (model)"
    return out


def evaluate(P, root=None):
    """All routes of mechanical.json harness_routes, the branches and the build/16 segments without a route."""
    hr = P.mech.get("harness_routes")
    if not hr:
        return None
    named = boxes(P)
    opens = _openings(P)
    wires = build16_wires(root)
    segs = {}
    order = sorted(set(hr["segments"]) | set(wires), key=lambda s: (len(s), s))
    for sid in order:
        spec = hr["segments"].get(sid)
        if spec is None:
            segs[sid] = {"kind": "harness", "length_mm": None, "provisional": ["no route in mechanical.json harness_routes"],
                         "status": "OPEN (end provisional): no route in mechanical.json harness_routes"}
            continue
        segs[sid] = evaluate_route(P, sid, spec, named, opens, wires, root)
        segs[sid]["in_build16"] = sid in wires
    branches = {bid: dict(evaluate_route(P, bid, spec, named, opens, wires, root), **{k: spec[k] for k in ("from_segment", "nets", "replaces") if k in spec})
                for bid, spec in hr.get("branches", {}).items()}
    coax = {cid: evaluate_route(P, cid, dict(spec, kind="coax"), named, opens, wires, root) for cid, spec in hr.get("coax", {}).items()}
    slot_use = {}
    for sl in P.mech["plate"].get("slots", []):
        routed = sorted(s for s, r in segs.items() if sl["id"] in r.get("through", []))
        slot_use[sl["id"]] = {"listed": sl.get("segments", []), "routed": routed,
                              "listed_not_routed": sorted(set(sl.get("segments", [])) - set(routed)),
                              "routed_not_listed": sorted(set(routed) - set(sl.get("segments", [])))}
    return {"segments": segs, "branches": branches, "coax": coax, "slots": slot_use}


def pps_budget(P, res):
    """R-PPS-LEN: PPS path Q6A J20 pin 7 -> LC76G <= limit (STACK 5.2: UART7 and PPS wiring <= 20 cm)."""
    hr = P.mech["harness_routes"]
    pb = hr["pps"]
    segs = res["segments"]
    parts = [segs.get(s, {}) for s in pb["path"]]
    via = sum(p.get("length_mm") or 0 for p in parts) if all(p.get("length_mm") for p in parts) else None
    out = {"limit_mm": pb["limit_mm"], "via_segments": pb["path"], "via_segments_mm": via,
           "via_segments_provisional": any(p.get("provisional") for p in parts)}
    br = res["branches"].get(pb["branch"]) if pb.get("branch") else None
    if via is not None and via > pb["limit_mm"] and br:
        out["decision"] = pb["decision"]
        out["branch"] = pb["branch"]
        out["branch_mm"] = br.get("length_mm")
        out["branch_provisional"] = bool(br.get("provisional"))
        out["branch_provisional_ends"] = list(br.get("provisional") or [])
        out["value_mm"] = br.get("length_mm")
        # W2 MECH-6: every provisional end of the branch carries a bound (end_status bound_mm), so the worst case is known
        spec = P.mech["harness_routes"]["branches"][pb["branch"]]
        prov_ends = [e for e in spec.get("end_status", []) if e.get("provisional")]
        if br.get("length_mm") is not None and prov_ends and all("bound_mm" in e for e in prov_ends):
            out["branch_bound_mm"] = br.get("bound_mm", 0.0)
            out["branch_max_mm"] = int(math.ceil(br["length_mm"] + br.get("bound_mm", 0.0) - 1e-9))
    else:
        out["value_mm"] = via
    return out


def route_rules(P, res=None):
    """R-PPS-LEN and R-ROUTE-CLEAR rows for rules.evaluate."""
    res = res or evaluate(P)
    if res is None:
        return []
    segs = res["segments"]
    pb = pps_budget(P, res)
    v = pb["value_mm"]
    lim = pb["limit_mm"]
    if v is None:
        r1 = "OPEN (end provisional): a PPS segment has no route length"
    else:
        prov = pb.get("branch_provisional") if "branch" in pb else pb["via_segments_provisional"]
        what = (f"{'+'.join(pb['via_segments'])} = {pb['via_segments_mm']} mm > {lim:g}: decision (build/15 W2 MECH-1) — {pb['decision']}; "
                f"branch {pb['branch']} = {v} mm" if "branch" in pb else f"{'+'.join(pb['via_segments'])} = {v} mm")
        if prov and "branch_max_mm" in pb:
            worst = pb["branch_max_mm"]
            r1 = (f"{'PASS' if worst <= lim else 'FAIL'} (model): {what}; worst case {worst} mm with the bounded provisional ends "
                  f"(+{pb['branch_bound_mm']:g} mm: {'; '.join(pb['branch_provisional_ends'])}) {'<=' if worst <= lim else '>'} {lim:g}")
        elif prov:
            ends = pb.get("branch_provisional_ends") if "branch" in pb else []
            r1 = (f"OPEN (end provisional): {what} {'<=' if v <= lim else '>'} {lim:g} (model; ends on board edge zones / envelope faces until the header and pin positions are placed)"
                  + (f"; the margin depends on: {'; '.join(ends)}" if ends else ""))
        else:
            r1 = f"{'PASS' if v <= lim else 'FAIL'} (model): {what}"
    rows = [{"id": "R-PPS-LEN", "rule": f"PPS path Q6A J20.7 -> LC76G: harness length <= {lim:g} mm (STACK 5.2 'UART7/PPS wiring <= 20 cm'; E3 J301 note)",
             "value_mm": {k: pb[k] for k in ("via_segments_mm", "branch_mm", "branch_max_mm") if k in pb}, "limit_mm": lim, "result": r1,
             "source": "mechanical.json harness_routes; generated/harness-routes.json"}]
    allroutes = list(segs.items()) + list(res["branches"].items()) + list(res.get("coax", {}).items())
    allr = [r for _, r in allroutes if r["kind"] != "external"]
    bad = [s for s, r in allroutes if r.get("crossings") and not r.get("provisional")]
    pcross = [s for s, r in allroutes if r.get("crossings") and r.get("provisional")]
    routed = [r for r in allr if r.get("points_mm")]
    nprov = sum(1 for r in routed if r.get("provisional"))
    unplaced = sorted(s for s, r in segs.items() if r["kind"] != "external" and not r.get("points_mm"))
    unlisted = {k: v["routed_not_listed"] for k, v in res["slots"].items() if v["routed_not_listed"]}
    missing = {k: v["listed_not_routed"] for k, v in res["slots"].items() if v["listed_not_routed"]}
    val = {"routed": len(routed), "clear": sum(1 for r in routed if not r.get("crossings")), "provisional_end": nprov,
           "no_route_unplaced_end": unplaced, "external": sorted(s for s, r in segs.items() if r["kind"] == "external"),
           "crossing": bad + pcross}
    if bad:
        res_txt = "FAIL (model): " + ", ".join(f"{s}: {'; '.join(dict(allroutes)[s]['crossings'])}" for s in bad)
    else:
        notes = []
        if pcross:
            notes.append("provisional routes crossing a solid: " + ", ".join(pcross))
        if unlisted:
            notes.append("routes through a plate slot that plate.slots does not list (R-PLATE-SLOT-FILL undercounts): "
                         + "; ".join(f"{k}: {', '.join(v)}" for k, v in unlisted.items()))
        if missing:
            notes.append("plate.slots segments not routed through their slot: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in missing.items()))
        res_txt = (f"OPEN (end provisional): every routed centreline clears the envelopes and structure; {nprov} of {len(routed)} routes end "
                   "on a board edge zone (header refs named, positions TBD until the board placement) or at a module without an envelope; "
                   f"no route yet (end not placed): {', '.join(unplaced) or 'none'}"
                   + ("; " + "; ".join(notes) if notes else ""))
    rows.append({"id": "R-ROUTE-CLEAR", "rule": "harness route centrelines (mechanical.json harness_routes) clear of every envelope, keep-clear reserve and structure part; plate and RF-bay wall only through openings",
                 "value_mm": val, "result": res_txt, "source": "mechanical.json harness_routes, layout, plate.slots, rf_bay.notches"})
    rows += coax_rules(P, res)
    return rows


def pigtail_choice(P, res, cid):
    """Shortest listed pigtail whose lower length (nominal - tolerance) leaves >= slack_min over the coax route; None if none."""
    spec = P.mech["harness_routes"]["coax"][cid]
    r = res.get("coax", {}).get(cid, {})
    L = r.get("length_mm")
    if L is None:
        return None, []
    rows = []
    for pt in spec["pigtails"]:
        low = pt["length_mm"] - pt["tol_mm"]
        rows.append({"mpn": pt["mpn"], "length_mm": pt["length_mm"], "tol_mm": pt["tol_mm"], "slack_mm": round(low - L, 1),
                     "fits": low - L >= spec["slack_min_mm"] - 1e-9})
    fit = next((x for x in rows if x["fits"]), None)
    return fit, rows


def coax_rules(P, res):
    """R-P7-PIGTAIL (W2 MECH-6): the W407 pigtail from the P7 bulkhead to the LC76G IPEX leaves >= slack_min over its route."""
    out = []
    for cid, spec in P.mech["harness_routes"].get("coax", {}).items():
        r = res.get("coax", {}).get(cid, {})
        fit, rows = pigtail_choice(P, res, cid)
        chosen = spec.get("chosen")
        if r.get("length_mm") is None:
            txt = "OPEN (end provisional): " + "; ".join(r.get("provisional") or ["no route"])
        elif r.get("crossings"):
            txt = "FAIL (model): route crosses a solid: " + "; ".join(r["crossings"])
        elif fit is None:
            txt = f"FAIL (model): route {r['length_mm']} mm; no listed pigtail leaves {spec['slack_min_mm']:g} mm slack ({rows})"
        elif fit["mpn"] != chosen:
            txt = f"FAIL (model): the shortest pigtail with {spec['slack_min_mm']:g} mm slack is {fit['mpn']}, mechanical.json names {chosen}"
        else:
            txt = (f"{'OPEN (end provisional)' if r.get('provisional') else 'PASS (model)'}: route {r['length_mm']} mm "
                   f"(bulkhead body to the IPEX plug, no service loops); {fit['mpn']} {fit['length_mm']:g} - {fit['tol_mm']:g} mm leaves "
                   f"{fit['slack_mm']:g} mm >= {spec['slack_min_mm']:g}"
                   + "".join(f"; {x['mpn']} {x['length_mm']:g} mm leaves {x['slack_mm']:g} mm" for x in rows if x["mpn"] != fit["mpn"])
                   + (f"; provisional: {'; '.join(r['provisional'])}" if r.get("provisional") else ""))
        out.append({"id": spec.get("rule_id", f"R-{cid}-PIGTAIL"), "rule": spec["rule"], "value_mm": {"route_mm": r.get("length_mm"), "pigtails": rows},
                    "limit_mm": spec["slack_min_mm"], "result": txt, "source": spec["source"]})
    return out


def document(P, res):
    """generated/harness-routes.json (the build/16 length source, tools/build_assembly_docs.py)."""
    hr = P.mech["harness_routes"]
    return {"schema": "srrx-harness-routes-v1",
            "status": "MODEL ESTIMATE: centreline routes through the enclosure model; not cut lengths measured on a built unit. "
                      "OPEN (end provisional) = an end is a board edge zone or a module without an envelope.",
            "source": "mechanical/params/mechanical.json harness_routes + layout (mechanical/build.py)",
            "length_rule": f"length_mm = polyline + bend allowance (bundle OD / 2 x bend angle) + service loops {' + '.join(f'{v:g}' for v in hr['service_loops_mm'])} mm, "
                           "rounded up to 1 mm; bundle OD = largest wire OD (chosen PTFE wire, nominal + tolerance; parts.json hookup_wire_ptfe) x sqrt(wires / "
                           f"{hr['fill']:g}); a gauge without a read OD takes the largest insulation its terminals accept; coax routes: no service loops",
            "pps": pps_budget(P, res), "segments": res["segments"], "branches": res["branches"], "coax": res.get("coax", {}), "slots": res["slots"]}


def summary(P, res):
    """Compact per-route rows for fit-report.json / fit-report.md (the full polylines are in harness-routes.json)."""
    keys = ("kind", "length_mm", "path_mm", "bends", "bundle_od_mm", "bend_allowance_mm", "through", "status")
    return {"file": "generated/harness-routes.json", "pps": pps_budget(P, res),
            "segments": {s: {k: r[k] for k in keys if k in r} for s, r in res["segments"].items()},
            "branches": {s: {k: r[k] for k in keys if k in r} for s, r in res["branches"].items()},
            "coax": {s: {k: r[k] for k in keys if k in r} for s, r in res.get("coax", {}).items()},
            "slots": res["slots"]}
