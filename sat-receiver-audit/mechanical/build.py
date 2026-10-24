#!/usr/bin/env python3
"""Regenerate every SR-RX mechanical output from mechanical/params.

    python mechanical/build.py                      # all outputs into mechanical/generated
    python mechanical/build.py --check              # rebuild into a temp dir, compare byte for byte
    python mechanical/build.py --vendor-cache DIR   # where pinned vendor STEP archives are kept (fetched if missing)
    python mechanical/build.py --skip-cad           # 2D drawings, contract and fit report only (no build123d)

Outputs are MODEL FIT ONLY: physical fit, sealing, thermal and drop gates stay OPEN.
"""
import argparse
import hashlib
import json
import math
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from srrx_mech import VERSION, antennas, boards, drawings_enclosure as de, layout, writers  # noqa: E402
from srrx_mech.params import Params  # noqa: E402

OUT = HERE / "generated"
D15 = (222.5, 137.5, 57.5)


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


def normalise_step(data):
    txt = data.decode("utf-8", "replace")
    txt = re.sub(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-10-24T00:00:00'", txt, count=1)
    return txt.replace("\r\n", "\n").encode("utf-8")


def envelope_report(P):
    W, H, D = P.outer
    area = 2 * (W * H + W * D + H * D)
    a15 = 2 * (D15[0] * D15[1] + D15[0] * D15[2] + D15[1] * D15[2])
    return {
        "model": [W, H, D], "d15": list(D15),
        "growth_mm": [round(W - D15[0], 1), round(H - D15[1], 1), round(D - D15[2], 1)],
        "volume_l": round(W * H * D / 1e6, 3), "volume_l_d15": round(D15[0] * D15[1] * D15[2] / 1e6, 3),
        "surface_m2": round(area / 1e6, 4), "surface_m2_d15": round(a15 / 1e6, 4), "surface_ratio": round(area / a15, 3),
        "front_m2": round(W * H / 1e6, 4), "front_ratio": round(W * H / (D15[0] * D15[1]), 3),
        "fire_bag_23x30cm": {
            "rule": "flat bag: half-girths W + D <= 300 and H + D <= 230 mm (geometry estimate, model)",
            "w_plus_d": W + D, "h_plus_d": H + D,
            "result": "PASS (model)" if (W + D <= 300 and H + D <= 230) else "FAIL (model): charge on a non-flammable surface instead (STACK 5.8 fallback)"},
        "reason": "D15 could not hold the v2.1 set with three boards, the 96.2 x 82 HDMI board, the 112 x 56 HF+ can and a full-depth battery strip without collisions (see collisions history in build/05 1.1); grown to the smallest envelope that passes the envelope checks",
    }


def gasket_report(P):
    m = P.mech
    gk = m["gasket"]
    W, H, D = P.outer
    gc = gk["rim_w"] / 2.0
    R = m["outer"]["corner_r"] - gc
    L = 2 * (W - 2 * gc) + 2 * (H - 2 * gc) - 8 * R + 2 * math.pi * R
    rule = P.parts["oring_groove_rule"]
    sq = 1 - gk["groove_depth"] / gk["cord_d"]
    fill = (math.pi * gk["cord_d"] ** 2 / 4) / (gk["groove_w"] * gk["groove_depth"])
    return {"cord_d": gk["cord_d"], "groove": [gk["groove_w"], gk["groove_depth"]], "squeeze": round(sq, 3), "fill": round(fill, 3),
            "squeeze_rule": rule["squeeze"], "fill_max": rule["fill_max"],
            "result": "PASS (model)" if rule["squeeze"][0] <= sq <= rule["squeeze"][1] and fill <= rule["fill_max"] else "FAIL (model)",
            "groove_centre_corner_r": round(R, 2), "cord_length_mm": round(L, 0), "cord_order_mm": int(math.ceil(L * 1.05 / 10.0) * 10)}


def all_sheets(P, vendor_fit):
    groups = {"enclosure": [], "boards": [], "antennas": [], "pod-imu": []}
    groups["enclosure"] += de.face_sheets(P)
    groups["enclosure"] += [de.plate_sheet(P), de.angles_sheet(P), de.rfbay_sheet(P), de.pedestal_cooler_sheet(P, vendor_fit),
                            de.hfplus_can_sheet(P), de.bezel_sheet(P), de.seam_sheet(P)]
    for bid in P.boards["boards"]:
        groups["boards"].append(boards.board_sheet(P, bid))
    ant, checks = antennas.sheets(P)
    groups["antennas"] += ant
    groups["pod-imu"] += [antennas.pod_sheet(P), antennas.imu_sheet(P)]
    return groups, checks


def cad_outputs(P, out, files):
    from build123d import Compound, export_step, export_stl
    from srrx_mech import cad, cad_fixtures as fx

    tmp = Path(tempfile.mkdtemp(prefix="srrx-mech-"))
    vols = {}

    def emit(name, part, stl=True, label=None):
        part.label = label or name
        s = tmp / f"{name}.step"
        export_step(part, str(s))
        write(out, f"step/{name}.step", normalise_step(s.read_bytes()), files)
        if stl:
            t = tmp / f"{name}.stl"
            export_stl(part, str(t), tolerance=0.05, angular_tolerance=0.2)
            write(out, f"stl/{name}.stl", t.read_bytes(), files)
        vols[name] = round(part.volume / 1000.0, 2)
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
    write(out, "step/assembly.step", normalise_step(s.read_bytes()), files)
    shutil.rmtree(tmp, ignore_errors=True)
    return vols


def build(out, vendor_cache=None, skip_cad=False):
    P = Params()
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    meta = {"params": params_hash(P)[:12], "version": VERSION}
    vendor_fit = None
    if vendor_cache:
        from srrx_mech import vendor
        steps = vendor.fetch(P, vendor_cache)
        vendor_fit = vendor.q6a_fit(P, steps["radxa_q6a_v1.21"])
        vendor_fit["status"] = "MODEL FIT ONLY: vendor STEP V1.21 against parts.json; the physical board is not measured"
        write(out, "vendor-fit.json", jdump(vendor_fit), files)
    groups, ant_checks = all_sheets(P, vendor_fit)
    for g, sheets in groups.items():
        for sh in sheets:
            sh.finish({"scale": __import__("srrx_mech.geom2d", fromlist=["scale_label"]).scale_label(sh.scale), **meta})
            write(out, f"drawings/{sh.sid}.svg", writers.to_svg(sh, meta), files)
            write(out, f"drawings/{sh.sid}.dxf", writers.to_dxf(sh), files)
            if g == "boards":
                write(out, f"boards/{sh.sid[2:].lower()}-edge-cuts.dxf", writers.to_dxf(sh), files)
        write(out, f"drawings/{g}.pdf", writers.to_pdf(sheets, meta), files)
    write(out, "contract/boards.json", jdump(boards.contract(P)), files)
    coll, outside = layout.fit_checks(P)
    report = {
        "schema": "srrx-mech-fit-report-v1",
        "status": "MODEL FIT ONLY: envelopes and datasheet dimensions; no physical part was fitted. Hardware gates stay OPEN.",
        "generator": {"version": VERSION, "params_sha256": params_hash(P)},
        "envelope": envelope_report(P),
        "collisions": [c for c in coll if c["gap_mm"] < 0],
        "tight_below_0_5mm": [c for c in coll if c["gap_mm"] >= 0],
        "outside_interior": outside,
        "channel_path2": layout.channel_check(P),
        "board_area": boards.area_check(P),
        "gasket": gasket_report(P),
        "antenna_parts": ant_checks,
        "vendor_fit": vendor_fit["result"] if vendor_fit else "NOT RUN (no --vendor-cache)",
    }
    report["summary"] = {
        "collisions": len(report["collisions"]), "outside": len(outside),
        "antenna_rule_failures": sum(1 for c in ant_checks if c["result"].startswith("FAIL")),
        "board_area_failures": sum(1 for b in report["board_area"].get("boards", {}).values() if b["result"].startswith("FAIL")),
    }
    if not skip_cad:
        report["printed_and_machined_volumes_cm3"] = cad_outputs(P, out, files)
    write(out, "fit-report.json", jdump(report), files)
    try:
        import build123d, matplotlib  # noqa: F401
        libs = {"build123d": getattr(build123d, "__version__", "?"), "matplotlib": matplotlib.__version__}
    except ImportError:
        libs = {}
    manifest = {"schema": "srrx-mech-manifest-v1", "generator": VERSION, "params_sha256": params_hash(P), "libraries": libs,
                "skip_cad": skip_cad, "vendor_fit": bool(vendor_cache),
                "files": {k: {"bytes": len(v), "sha256": hashlib.sha256(v).hexdigest()} for k, v in sorted(files.items())}}
    write(out, "manifest.json", jdump(manifest), files)
    return files, report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--check", action="store_true", help="rebuild into a temporary directory and compare with --out byte for byte")
    ap.add_argument("--vendor-cache", type=Path, default=None, help="directory for pinned vendor STEP archives (fetched if missing)")
    ap.add_argument("--skip-cad", action="store_true")
    a = ap.parse_args()
    if a.check:
        tmp = Path(tempfile.mkdtemp(prefix="srrx-mech-check-"))
        files, report = build(tmp, a.vendor_cache, a.skip_cad)
        bad = []
        for rel, data in files.items():
            p = a.out / rel
            if not p.exists():
                bad.append(f"missing in {a.out}: {rel}")
            elif p.read_bytes() != data:
                bad.append(f"differs: {rel}")
        for p in sorted(a.out.rglob("*")):
            if p.is_file() and p.relative_to(a.out).as_posix() not in files:
                bad.append(f"stale extra file: {p.relative_to(a.out).as_posix()}")
        shutil.rmtree(tmp, ignore_errors=True)
        for b in bad:
            print(b)
        print("mechanical outputs:", "STALE" if bad else "reproduce byte for byte", f"({len(files)} files)")
        return 1 if bad else 0
    if a.out.exists():
        shutil.rmtree(a.out)
    files, report = build(a.out, a.vendor_cache, a.skip_cad)
    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"{len(files)} files written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
