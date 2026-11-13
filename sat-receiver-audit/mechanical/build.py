#!/usr/bin/env python3
"""Regenerate every SR-RX mechanical output from mechanical/params.

    python mechanical/build.py --vendor-cache DIR   # all outputs into mechanical/generated (the committed set)
    python mechanical/build.py --check --vendor-cache DIR   # rebuild into a temp dir, compare byte for byte
    python mechanical/build.py --fetch-vendor DIR   # download and verify the pinned vendor STEP archives only
    python mechanical/build.py --gate               # fail on any FAIL row of the committed fit report
    python mechanical/build.py --skip-cad           # 2D drawings, contract and fit report only (no build123d)
    python mechanical/build.py --update-zones       # rewrite the computed CTRL/RF height_zones/rear_zones in params/boards.json

--offline refuses downloads (the archives must already be in --vendor-cache).
Outputs are MODEL FIT ONLY: physical fit, sealing, thermal and drop gates stay OPEN.
"""
import argparse
import hashlib
import json
import math
import shutil
import sys
import tempfile
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from srrx_mech import VERSION, antennas, boards, drawings_enclosure as de, fasteners, layout, report_md, routes, rules, thermal, writers  # noqa: E402
from srrx_mech.geom2d import scale_label  # noqa: E402
from srrx_mech.params import Params  # noqa: E402

OUT = HERE / "generated"
D15 = (222.5, 137.5, 57.5)
COMPONENTS = HERE.parent / "pcb" / "generated" / "components.csv"
SPEC = HERE.parent / "pcb" / "partition-spec.json"
# PolyLite ASA, ISO 1183, 23 C: https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polylite-tm-asa (read 2026-10-24)
ASA_DENSITY = 1.13
STL_DEFLECTION, STL_ANGULAR = 0.1, 0.3   # mm (half a 0.2 mm print layer), rad


def jdump(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")


def params_hash(P):
    h = hashlib.sha256()
    for name, data in P.files().items():
        h.update(name.encode() + b"\0" + data + b"\0")
    return h.hexdigest()


def write(out, rel, data, files):
    p = out / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    files[rel] = data


def closed_depth(P):
    """z extent of the closed unit (hood folded, plugs out): every fixed protrusion of the rear and front faces."""
    m = P.mech
    W, H, D = P.outer
    rf = m["rear_face"]
    th = rf["t7_holder"]
    pec = P.parts["pec11r"]
    knob = m["hmi"]["encoders"]["main"]
    hh = m["top_face"]["hood_hinge"]
    rear = {"strap lugs and tunnels": -rf["strap_lug"]["proud"], "tripod plinth": -rf["tripod"]["plinth_h"],
            "T7 holder": -(th["gap"] + P.parts["t7"]["size"][2] + th["shutter_t"]),
            "T7 gland outside (assumption)": -rf["t7_gland"]["proud"]}
    front = {"front face": D, "hood hinge knuckles (hood folded on them)": hh["axis_z"] + 3.0,
             "main knob": D + pec["washer"][2] + pec["nut_t"] + knob["skirt_gap"] + knob["knob_h"],
             "volume knob (Adafruit 2055)": D + pec["washer"][2] + pec["nut_t"] + knob["skirt_gap"] + P.parts["knob_2055"]["h"]}
    return rear, front


def envelope_report(P):
    W, H, D = P.outer
    belt = P.mech["gasket"]["belt"]
    Wb, Hb = W + 2 * belt, H + 2 * belt      # over the seam belt
    area = 2 * (W * H + W * D + H * D)
    a15 = 2 * (D15[0] * D15[1] + D15[0] * D15[2] + D15[1] * D15[2])
    rear, front = closed_depth(P)
    z0, z1 = min(rear.values()), max(front.values())
    Dc = z1 - z0
    no_t7 = max(front.values()) - min(v for k, v in rear.items() if k != "T7 holder")
    ok = Wb + Dc <= 300 and Hb + Dc <= 230
    return {
        "model": [W, H, D], "over_seam_belt": [Wb, Hb, D], "d15": list(D15),
        "growth_mm": [round(W - D15[0], 1), round(H - D15[1], 1), round(D - D15[2], 1)],
        "volume_l": round(W * H * D / 1e6, 3), "volume_l_d15": round(D15[0] * D15[1] * D15[2] / 1e6, 3),
        "surface_m2": round(area / 1e6, 4), "surface_m2_d15": round(a15 / 1e6, 4), "surface_ratio": round(area / a15, 3),
        "front_m2": round(W * H / 1e6, 4), "front_ratio": round(W * H / (D15[0] * D15[1]), 3),
        "closed_bbox_mm": {"x": [-belt, W + belt], "y": [-belt, H + belt], "z": [z0, z1],
                           "rear_protrusions_z": rear, "front_protrusions_z": front,
                           "note": "GX16 cap, SMA/F/BNC caps and screw heads on the T7 holder are not counted (parts not chosen); side-face parts (RX2/REF IN bulkheads, the J551 M8 receptacle 7.5 mm proud of the right face) are not in W/H"},
        "fire_bag_23x30cm": {
            "rule": "flat bag: half-girths W + D <= 300 and H + D <= 230 mm, W/H over the seam belt, D = closed depth with every fixed protrusion (geometry estimate, model)",
            "depth_mm": round(Dc, 1), "depth_without_t7_holder_mm": round(no_t7, 1),
            "w_plus_d": round(Wb + Dc, 1), "h_plus_d": round(Hb + Dc, 1),
            "result": "PASS (model)" if ok else "FAIL (model): charge on a non-flammable surface instead (STACK 5.8 fallback)"},
        "reason": depth_reason(P),
    }


def depth_reason(P):
    """Envelope reason with the front-tier stack computed from the parameters (W2 MECH-3 review F3)."""
    m, B = P.mech, P.boards["boards"]
    sz, ta, tb = m["stack_z"], P.board_t("PWR"), P.board_t("PWR_B")     # W2 MECH-8: each board's own thickness
    pa, pb = B["PWR"], B["PWR_B"]
    gap = pa["place"]["z_bottom"] - sz["plate_front"]
    stack = pb["place"]["z_bottom"] - (pa["place"]["z_bottom"] + ta)
    chan = sz["module_back"] - (pb["place"]["z_bottom"] + tb + pb["max_height"])
    front = sz["module_back"] - sz["plate_front"]
    dz = None
    if SPEC.exists():
        dz = json.loads(SPEC.read_text(encoding="utf-8")).get("envelope", {}).get("dz")

    def f(v):
        return f"{round(v, 2):g}"
    return (f"height: battery strip (33.4) + middle row with the 112 x 56 HF+ can beside the Q6A + RF bay ({f(m['rf_bay']['rect'][3])}: two rows "
            "of cased LNA modules, arrangement b, W2 MECH-3) along the top; "
            f"depth: wall {f(m['wall'])} + rear layer {f(sz['plate_rear'] - m['wall'])} (Q6A with cooler and fan duct) + plate {f(sz['plate_t'])} + "
            f"front layer {f(front)} (bond gap {f(gap)} + PWR-A {f(ta)} + B2B {f(stack)} + PWR-B {f(tb)} + parts {f(pb['max_height'])} + "
            f"path-2 channel {f(chan)}; W2 MECH-3 depth growth "
            + (f"dz {f(dz)} = pcb/partition-spec.json envelope.dz" if dz is not None else "dz: pcb/partition-spec.json not found")
            + f") + display {f(sz['front_wall_inner'] - sz['module_back'])} + front wall {f(P.outer[2] - sz['front_wall_inner'])}; "
            "width: display glass 164.8 + HMI column 51 (build/05 1.1)")


def gasket_report(P):
    from srrx_mech.features import seam_geometry
    m = P.mech
    gk = m["gasket"]
    W, H, D = P.outer
    gc = seam_geometry(P)["groove_centre"]          # inwards from the outer surface (negative: in the belt)
    R = m["outer"]["corner_r"] - gc
    L = 2 * (W - 2 * gc) + 2 * (H - 2 * gc) - 8 * R + 2 * math.pi * R
    rule = P.parts["oring_groove_rule"]
    sq = 1 - gk["groove_depth"] / gk["cord_d"]
    fill = (math.pi * gk["cord_d"] ** 2 / 4) / (gk["groove_w"] * gk["groove_depth"])
    return {"cord_d": gk["cord_d"], "groove": [gk["groove_w"], gk["groove_depth"]], "squeeze": round(sq, 3), "fill": round(fill, 3),
            "squeeze_rule": rule["squeeze"], "fill_max": rule["fill_max"], "belt_mm": gk["belt"], "land_mm": gk["land"],
            "result": "PASS (model)" if rule["squeeze"][0] <= sq <= rule["squeeze"][1] and fill <= rule["fill_max"] else "FAIL (model)",
            "groove_centre_corner_r": round(R, 2), "cord_length_mm": round(L, 0), "cord_order_mm": int(math.ceil(L * 1.05 / 10.0) * 10),
            "closure": rules.closure_spans(P)}


def all_sheets(P, vendor_fit):
    groups = {"enclosure": [], "boards": [], "antennas": [], "pod-imu": []}
    groups["enclosure"] += de.face_sheets(P)
    groups["enclosure"] += [de.plate_sheet(P), de.angles_sheet(P), de.rfbay_sheet(P), de.pedestal_cooler_sheet(P, vendor_fit),
                            de.hfplus_can_sheet(P), de.bezel_sheet(P), de.seam_sheet(P)]
    for bid in P.boards["boards"]:
        groups["boards"].append(boards.board_sheet(P, bid))
    ant, checks = antennas.sheets(P)
    groups["antennas"] += ant
    groups["pod-imu"] += [antennas.pod_sheet(P), antennas.pod_walls_sheet(P), antennas.imu_sheet(P)]
    return groups, checks


def cad_outputs(P, out, files):
    from build123d import Compound, export_step
    from srrx_mech import cad, cad_fixtures as fx, export3d, interference

    tmp = Path(tempfile.mkdtemp(prefix="srrx-mech-"))
    vols = {}

    def emit(name, part, stl=True, label=None):
        part.label = label or name
        s = tmp / f"{name}.step"
        export_step(part, str(s))
        write(out, f"step/{name}.step", export3d.normalise_step(s.read_bytes()), files)
        bb = part.bounding_box()
        vols[name] = {"cm3": round(part.volume / 1000.0, 2), "printed": stl, "solids": len(part.solids()),
                      "bbox_mm": [round(v, 2) + 0.0 for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)]}
        if stl:
            # absolute chordal deflection, single-threaded mesher (export3d)
            data, ntri = export3d.stl_bytes(part, name, STL_DEFLECTION, STL_ANGULAR)
            write(out, f"stl/{name}.stl", data, files)
            vols[name]["stl_triangles"] = ntri
        return part

    parts = {}
    parts["front_shell"] = emit("front_shell", cad.front_shell(P))
    parts["rear_shell"] = emit("rear_shell", cad.rear_shell(P))
    parts["hatch_cover"] = emit("hatch_cover", cad.hatch_cover(P))
    parts["hood"] = emit("hood", cad.hood(P))
    parts["battery_tray"] = emit("battery_tray", cad.battery_tray(P))
    parts["t7_holder"] = emit("t7_holder", cad.t7_holder(P))
    emit("display_clamp_x4", cad.display_clamp(P))
    emit("button_cap_x4", cad.button_cap(P, False))
    emit("button_cap_ribbed_x2", cad.button_cap(P, True))
    emit("main_knob", cad.main_knob(P))
    parts["plate"] = emit("plate_al", cad.plate(P), stl=False)
    parts["angle_top"] = emit("angle_top_al", cad.angle_top(P), stl=False)
    parts["angle_right"] = emit("angle_right_al", cad.angle_right(P), stl=False)
    parts["lime_pedestal"] = emit("lime_pedestal_al", cad.lime_pedestal(P), stl=False)
    parts["ufs_boss"] = emit("ufs_boss_al", cad.ufs_boss(P), stl=False)
    walls, lid = cad.rf_bay(P)
    parts["rf_bay_walls"] = emit("rf_bay_walls_fr4", walls, stl=False)
    parts["rf_bay_lid"] = emit("rf_bay_lid_fr4", lid, stl=False)
    emit("cooler_a_cu_block", cad.cu_block(P), stl=False)
    A = P.antennas
    emit("mandrel_hrpt_4t", fx.helix_mandrel(A["helix_hrpt"]))
    emit("mandrel_sband_7t", fx.helix_mandrel(A["helix_sband"]))
    emit("lnb_neck_adapter", fx.neck_adapter(A["lnb_neck_adapter"]))
    emit("lnb_throat_ring", fx.throat_ring(A["throat_ring"]))
    for d in A["horn_qo100"]["rings_d"]:
        emit(f"horn_ring_{int(d)}", fx.horn_ring(d, A["horn_qo100"]["half_angle"]))
    emit("yagi_tape_clamp", fx.yagi_tape_clamp(A["yagi"]))
    emit("yagi_de_clamp", fx.yagi_tape_clamp(A["yagi"], split=True))
    emit("yagi_boom_spigot", fx.boom_spigot(A["yagi"]))
    emit("imu_carrier", fx.imu_carrier(P))
    emit("helicone_disk_al", fx.helicone_disk(P), stl=False)
    # assembly with envelopes (keep-outs, not vendor geometry)
    kids = []
    for k, v in parts.items():
        v.label = k
        kids.append(v)
    kids += cad.envelope_parts(P)
    asm = Compound(label="srrx_v2_1_mechanical_model_fit_only", children=kids)
    s = tmp / "assembly.step"
    export_step(asm, str(s))
    write(out, "step/assembly.step", export3d.normalise_step(s.read_bytes()), files)
    shutil.rmtree(tmp, ignore_errors=True)
    feats = {}
    for side, fn in (("front", cad.front_parts), ("rear", cad.rear_parts)):
        for name, group in fn(P)[1]:
            feats[f"{side}.{name}"] = group
    return vols, interference.check(P, parts, feats), [interference.access(P, parts), interference.tripod_disc(P, parts)]


def libraries():
    out = {}
    for name in ("build123d", "cadquery-ocp-novtk", "matplotlib"):
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            pass
    return out


def summary(report):
    def fails(rows):
        return sum(1 for r in rows if str(r.get("result", "")).startswith("FAIL"))
    return {
        "collisions": len(report["collisions"]), "outside": len(report["outside_interior"]),
        "rule_failures": fails(report["rules"]),
        "rules_open": sum(1 for r in report["rules"] + [report["rf_bay_packing"]] if str(r["result"]).startswith("OPEN")),
        "antenna_rule_failures": fails(report["antenna_parts"]),
        "board_area_failures": fails(report["board_area"].get("boards", {}).values()),
        "board_area_open": sum(1 for r in report["board_area"].get("boards", {}).values() if str(r["result"]).startswith("OPEN")),
        "board_area_harness_open": sum(1 for r in report["board_area"].get("with_harness", {}).get("boards", {}).values() if str(r["result"]).startswith("OPEN")),
        "thermal_failures": fails(report["thermal_interfaces"]["rows"]),
        "thermal_open": sum(1 for r in report["thermal_interfaces"]["rows"] if r["result"].startswith("OPEN")),
        "gasket": report["gasket"]["result"],
        "vendor_fit": report["vendor_fit"],
        "solid_conflicts": len(report["solid_interference"]["conflicts"]) if "solid_interference" in report else None,
        "disconnected_parts": sorted(k for k, v in report.get("volumes_cm3", {}).items() if v["solids"] != 1) if "volumes_cm3" in report else None,
    }


def build(out, vendor_cache=None, skip_cad=False, offline=False):
    P = Params()
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    meta = {"params": params_hash(P)[:12], "version": VERSION}
    vendor_fit = None
    if vendor_cache:
        from srrx_mech import vendor
        steps = vendor.fetch(P, vendor_cache, download=not offline)
        vendor_fit = vendor.q6a_fit(P, steps["radxa_q6a_v1.21"])
        vendor_fit["status"] = "MODEL FIT ONLY: vendor STEP V1.21 against parts.json; the physical board is not measured"
        write(out, "vendor-fit.json", jdump(vendor_fit), files)
    groups, ant_checks = all_sheets(P, vendor_fit)
    for g, sheets in groups.items():
        for sh in sheets:
            sh.finish({"scale": scale_label(sh.scale), **meta})
            write(out, f"drawings/{sh.sid}.svg", writers.to_svg(sh, meta), files)
            write(out, f"drawings/{sh.sid}.dxf", writers.to_dxf(sh), files)
            if g == "boards":
                write(out, f"boards/{sh.sid[2:].lower()}-edge-cuts.dxf", writers.to_dxf(sh, only=("CUT", "HOLE")), files)
        write(out, f"drawings/{g}.pdf", writers.to_pdf(sheets, meta), files)
    write(out, "contract/boards.json", jdump(boards.contract(P)), files)
    route_res = routes.evaluate(P)
    if route_res is not None:
        write(out, "harness-routes.json", jdump(routes.document(P, route_res)), files)
    write(out, "fastener-stacks.json", jdump(fasteners.stacks(P)), files)
    coll, outside = layout.fit_checks(P)
    trows = thermal.interfaces(P)
    report = {
        "schema": "srrx-mech-fit-report-v2",
        "status": "MODEL FIT ONLY: envelopes and datasheet dimensions; no physical part was fitted. Hardware gates stay OPEN.",
        "generator": {"version": VERSION, "params_sha256": params_hash(P),
                      "pcb_components_sha256": hashlib.sha256(COMPONENTS.read_bytes()).hexdigest() if COMPONENTS.exists() else None},
        "envelope": envelope_report(P),
        "collisions": [c for c in coll if c["gap_mm"] < 0],
        "tight_below_0_5mm": [c for c in coll if c["gap_mm"] >= 0],
        "outside_interior": outside,
        "channel_path2": layout.channel_check(P),
        "rules": rules.evaluate(P),
        "rf_bay_packing": rules.bay_packing(P),
        "board_area": boards.area_check(P),
        "board_zones": {bid: boards.clearance_map(P, bid) for bid in boards.ZONE_BOARDS},
        "harness_routes": routes.summary(P, route_res) if route_res else None,
        "thermal_interfaces": {"rule": f"Gelid GP-Ultimate, compression {thermal.COMP_MIN:.0%}-{P.parts['gelid_gp_ultimate']['max_compression']:.0%} "
                                       "over the design gap +- tolerance (upper limit: Gelid product page, parts.json)",
                               "rows": trows, "cuts_per_thickness": thermal.nest(trows, P.parts["gelid_gp_ultimate"]["sheet"])},
        "gasket": gasket_report(P),
        "antenna_parts": ant_checks,
        "vendor_fit": vendor_fit["result"] if vendor_fit else "NOT RUN (no --vendor-cache)",
    }
    if not skip_cad:
        vols, report["solid_interference"], cad_rules = cad_outputs(P, out, files)
        report["rules"] += cad_rules
        report["volumes_cm3"] = vols
        report["printed_mass_upper_bound_g"] = {
            "rule": f"solid CAD volume x {ASA_DENSITY} g/cm3 (PolyLite ASA, ISO 1183); real prints with 30 % infill weigh less",
            "parts": {k: round(v["cm3"] * ASA_DENSITY) for k, v in vols.items() if v["printed"]}}
    report["summary"] = summary(report)
    write(out, "fit-report.json", jdump(report), files)
    write(out, "fit-report.md", report_md.render(P, report, meta["params"], boards.contract(P)), files)
    manifest = {"schema": "srrx-mech-manifest-v1", "generator": VERSION, "params_sha256": params_hash(P), "libraries": libraries(),
                "skip_cad": skip_cad, "vendor_fit": bool(vendor_cache),
                "files": {k: {"bytes": len(v), "sha256": hashlib.sha256(v).hexdigest()} for k, v in sorted(files.items())}}
    write(out, "manifest.json", jdump(manifest), files)
    return files, report


def gate(out):
    """CI gate on the committed report: any FAIL row, collision or non-PASS vendor cross-check fails."""
    path = out / "fit-report.json"
    if not path.exists():
        print(f"no {path}: generate the outputs first")
        return 1
    s = json.loads(path.read_text(encoding="utf-8"))["summary"]
    bad = [k for k in ("collisions", "outside", "rule_failures", "antenna_rule_failures", "board_area_failures", "thermal_failures") if s[k]]
    if not s["gasket"].startswith("PASS"):
        bad.append("gasket")
    if not s["vendor_fit"].startswith("PASS"):
        bad.append("vendor_fit")
    if s.get("solid_conflicts") is None or s["solid_conflicts"]:
        bad.append("solid_conflicts")
    if s.get("disconnected_parts") is None or s["disconnected_parts"]:
        bad.append("disconnected_parts")   # a part made of several solids has a floating feature
    print(json.dumps(s, ensure_ascii=False))
    print("model-fit gate:", "FAIL " + ", ".join(bad) if bad else "PASS (model fit only; OPEN rows need measured or chosen parts)")
    return 1 if bad else 0


PORTABLE_SKIP = ("step/", "stl/", "manifest.json", "fit-report.md")
VENDOR_DEPENDENT = ("vendor-fit.json", "drawings/M-10.svg", "drawings/M-10.dxf", "drawings/enclosure.pdf")


def _close(a, b, path=""):
    """Structural JSON comparison; CAD volumes, boxes and triangle counts within tolerance."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return [f"{path}: keys differ"]
        return [m for k in a for m in _close(a[k], b[k], f"{path}/{k}")]
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length differs"]
        return [m for i, (x, y) in enumerate(zip(a, b)) for m in _close(x, y, f"{path}[{i}]")]
    if "/volumes_cm3/" in path and isinstance(a, (int, float)) and isinstance(b, (int, float)):
        tol = {"cm3": max(0.01, 1e-3 * abs(a)), "stl_triangles": max(2, 0.05 * abs(a))}.get(path.rsplit("/", 1)[-1].split("[")[0], 0.02)
        return [] if abs(a - b) <= tol else [f"{path}: {a} != {b}"]
    if "/printed_mass_upper_bound_g/" in path and isinstance(a, (int, float)):
        return [] if abs(a - b) <= 1 else [f"{path}: {a} != {b}"]
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def compare(out, files, portable=False, vendor=True):
    bad = []
    for rel, data in files.items():
        p = out / rel
        if not p.exists():
            bad.append(f"missing in {out}: {rel}")
            continue
        if portable and rel.startswith(PORTABLE_SKIP):
            continue
        if portable and rel == "fit-report.json":
            old, new = json.loads(p.read_text(encoding="utf-8")), json.loads(data.decode("utf-8"))
            if not vendor:
                for r in (old, new):
                    r.pop("vendor_fit", None)
                    r.get("summary", {}).pop("vendor_fit", None)
            bad += [f"differs: fit-report.json {m}" for m in _close(old, new)][:20]
            continue
        if p.read_bytes() != data:
            bad.append(f"differs: {rel}")
    if out.exists():
        for p in sorted(out.rglob("*")):
            rel = p.relative_to(out).as_posix()
            if p.is_file() and rel not in files and (vendor or rel not in VENDOR_DEPENDENT):
                bad.append(f"stale extra file: {rel}")
    if portable and not vendor:
        bad = [b for b in bad if not any(v in b for v in VENDOR_DEPENDENT)]
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--check", action="store_true", help="rebuild into a temporary directory and compare with --out byte for byte")
    ap.add_argument("--portable", action="store_true",
                    help="with --check on another platform: STEP/STL by volume, box and triangle count, everything else byte for byte")
    ap.add_argument("--vendor-cache", type=Path, default=None, help="directory for pinned vendor STEP archives (fetched if missing)")
    ap.add_argument("--offline", action="store_true", help="never download; the vendor archives must be in --vendor-cache")
    ap.add_argument("--fetch-vendor", type=Path, default=None, metavar="DIR", help="only download and verify the pinned vendor archives")
    ap.add_argument("--gate", action="store_true", help="evaluate the fit report in --out and fail on FAIL rows")
    ap.add_argument("--skip-cad", action="store_true")
    ap.add_argument("--update-zones", action="store_true", help="rewrite the computed height_zones/rear_zones of CTRL and RF in params/boards.json")
    a = ap.parse_args()
    if a.update_zones:
        from srrx_mech.params import PARAMS
        boards.write_zones(Params(), PARAMS / "boards.json")
        print("params/boards.json: height_zones / rear_zones of", ", ".join(boards.ZONE_BOARDS), "rewritten from the clearance map")
        return 0
    if a.fetch_vendor:
        from srrx_mech import vendor
        for k, v in vendor.fetch(Params(), a.fetch_vendor).items():
            print(k, "verified:", v.name)
        return 0
    if a.gate:
        return gate(a.out)
    if a.check:
        tmp = Path(tempfile.mkdtemp(prefix="srrx-mech-check-"))
        files, report = build(tmp, a.vendor_cache, a.skip_cad, a.offline)
        bad = compare(a.out, files, portable=a.portable, vendor=bool(a.vendor_cache))
        shutil.rmtree(tmp, ignore_errors=True)
        for b in bad:
            print(b)
        mode = "geometry within tolerance (portable)" if a.portable else "byte for byte"
        print("mechanical outputs:", "STALE" if bad else f"reproduce {mode}", f"({len(files)} files)")
        return 1 if bad else 0
    if a.out.exists():
        shutil.rmtree(a.out)
    files, report = build(a.out, a.vendor_cache, a.skip_cad, a.offline)
    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"{len(files)} files written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


