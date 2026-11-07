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
"""
import csv
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
    return named


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


def bundle(P, sid, wires):
    """Bundle OD upper bound (mm) of a segment: largest accepted insulation of its families x sqrt(n / fill)."""
    hr = P.mech["harness_routes"]
    ins = hr["insulation_max_mm"]
    rows = wires.get(sid, [])
    if sid in hr.get("flat", {}):
        return hr["flat"][sid]["thickness_mm"], len(rows)
    d = []
    for fam_a, fam_b, awg in rows:
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
        return {wp["box"]}
    if "edge" in wp:
        bid = wp["edge"]
        return {n for n, (_, _, it) in named.items() if it.get("board") == bid}
    return set()


def evaluate_route(P, sid, spec, named, opens, wires):
    hr = P.mech["harness_routes"]
    via = spec.get("via", [])
    out = {"kind": spec.get("kind", "harness"), "ends": spec.get("ends", [])}
    if spec.get("note"):
        out["note"] = spec["note"]
    prov = [e["provisional"] for e in spec.get("end_status", []) if e.get("provisional")]
    for i in (0, -1):
        if via and "edge" in via[i]:
            prov.append(f"{via[i]['edge']} header position TBD (board layout; GR-3 header refs): end on the edge zone")
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
    loops = sum(hr["service_loops_mm"]) if out["kind"] != "external" else 0.0
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
        segs[sid] = evaluate_route(P, sid, spec, named, opens, wires)
        segs[sid]["in_build16"] = sid in wires
    branches = {bid: dict(evaluate_route(P, bid, spec, named, opens, wires), **{k: spec[k] for k in ("from_segment", "nets", "replaces") if k in spec})
                for bid, spec in hr.get("branches", {}).items()}
    slot_use = {}
    for sl in P.mech["plate"].get("slots", []):
        routed = sorted(s for s, r in segs.items() if sl["id"] in r.get("through", []))
        slot_use[sl["id"]] = {"listed": sl.get("segments", []), "routed": routed,
                              "listed_not_routed": sorted(set(sl.get("segments", [])) - set(routed)),
                              "routed_not_listed": sorted(set(routed) - set(sl.get("segments", [])))}
    return {"segments": segs, "branches": branches, "slots": slot_use}


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
        if prov:
            ends = pb.get("branch_provisional_ends") if "branch" in pb else []
            r1 = (f"OPEN (end provisional): {what} {'<=' if v <= lim else '>'} {lim:g} (model; ends on board edge zones / envelope faces until the header and pin positions are placed)"
                  + (f"; the margin depends on: {'; '.join(ends)}" if ends else ""))
        else:
            r1 = f"{'PASS' if v <= lim else 'FAIL'} (model): {what}"
    rows = [{"id": "R-PPS-LEN", "rule": f"PPS path Q6A J20.7 -> LC76G: harness length <= {lim:g} mm (STACK 5.2 'UART7/PPS wiring <= 20 cm'; E3 J301 note)",
             "value_mm": {k: pb[k] for k in ("via_segments_mm", "branch_mm") if k in pb}, "limit_mm": lim, "result": r1,
             "source": "mechanical.json harness_routes; generated/harness-routes.json"}]
    allr = [r for r in list(segs.values()) + list(res["branches"].values()) if r["kind"] != "external"]
    bad = [s for s, r in list(segs.items()) + list(res["branches"].items()) if r.get("crossings") and not r.get("provisional")]
    pcross = [s for s, r in list(segs.items()) + list(res["branches"].items()) if r.get("crossings") and r.get("provisional")]
    routed = [r for r in allr if r.get("points_mm")]
    nprov = sum(1 for r in routed if r.get("provisional"))
    unplaced = sorted(s for s, r in segs.items() if r["kind"] != "external" and not r.get("points_mm"))
    unlisted = {k: v["routed_not_listed"] for k, v in res["slots"].items() if v["routed_not_listed"]}
    missing = {k: v["listed_not_routed"] for k, v in res["slots"].items() if v["listed_not_routed"]}
    val = {"routed": len(routed), "clear": sum(1 for r in routed if not r.get("crossings")), "provisional_end": nprov,
           "no_route_unplaced_end": unplaced, "external": sorted(s for s, r in segs.items() if r["kind"] == "external"),
           "crossing": bad + pcross}
    if bad:
        res_txt = "FAIL (model): " + ", ".join(f"{s}: {'; '.join((segs.get(s) or res['branches'][s])['crossings'])}" for s in bad)
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
                   "on a board edge zone or at a module without an envelope (header positions, module envelopes and the bundle OD (AI-WIRE-PTFE) TBD); "
                   f"no route yet (end not placed): {', '.join(unplaced) or 'none'}"
                   + ("; " + "; ".join(notes) if notes else ""))
    rows.append({"id": "R-ROUTE-CLEAR", "rule": "harness route centrelines (mechanical.json harness_routes) clear of every envelope, keep-clear reserve and structure part; plate and RF-bay wall only through openings",
                 "value_mm": val, "result": res_txt, "source": "mechanical.json harness_routes, layout, plate.slots, rf_bay.notches"})
    return rows


def document(P, res):
    """generated/harness-routes.json (the build/16 length source, tools/build_assembly_docs.py)."""
    hr = P.mech["harness_routes"]
    return {"schema": "srrx-harness-routes-v1",
            "status": "MODEL ESTIMATE: centreline routes through the enclosure model; not cut lengths measured on a built unit. "
                      "OPEN (end provisional) = an end is a board edge zone or a module without an envelope.",
            "source": "mechanical/params/mechanical.json harness_routes + layout (mechanical/build.py)",
            "length_rule": f"length_mm = polyline + bend allowance (bundle OD / 2 x bend angle) + service loops {' + '.join(f'{v:g}' for v in hr['service_loops_mm'])} mm, "
                           "rounded up to 1 mm; bundle OD = largest insulation the end terminals accept x sqrt(wires / "
                           f"{hr['fill']:g}) (upper bound until AI-WIRE-PTFE is chosen)",
            "pps": pps_budget(P, res), "segments": res["segments"], "branches": res["branches"], "slots": res["slots"]}


def summary(P, res):
    """Compact per-route rows for fit-report.json / fit-report.md (the full polylines are in harness-routes.json)."""
    keys = ("kind", "length_mm", "path_mm", "bends", "bundle_od_mm", "bend_allowance_mm", "through", "status")
    return {"file": "generated/harness-routes.json", "pps": pps_budget(P, res),
            "segments": {s: {k: r[k] for k in keys if k in r} for s, r in res["segments"].items()},
            "branches": {s: {k: r[k] for k in keys if k in r} for s, r in res["branches"].items()},
            "slots": res["slots"]}
