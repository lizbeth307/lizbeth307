#!/usr/bin/env python3
"""Package reviewed MicroPython source files, without pretending to build a UF2."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

BASE = Path(__file__).resolve().parents[1]
FLAGS = {"runtime_included": False, "device_flashed": False, "hardware_qualified": False}


def sources(base):
    for role in ("pico", "imu"):
        files = {p.name: p.read_bytes() for p in sorted((base / "firmware" / role).glob("*.py"))}
        files["wire.py"] = (base / "software/srrx/wire.py").read_bytes()
        # No accepted calibration or hardware-enabled commissioning file ships.
        yield role, files, {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}


def build(base=BASE):
    dest = base / "firmware/dist"
    dest.mkdir(exist_ok=True)
    report = dict(FLAGS, packages={})
    for role, files, manifest in sources(base):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in files.items():
                entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                entry.create_system = 3  # Unix mode bits; identical archive bytes on every host
                z.writestr(entry, data)
            entry = zipfile.ZipInfo("SOURCE-SHA256.json", date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            entry.create_system = 3
            z.writestr(entry, json.dumps(manifest, indent=2))
        data = buffer.getvalue()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if z.testzip() is not None:
                raise SystemExit("Firmware package CRC validation failed: " + role)
        path = dest / (role + "-micropython-files.zip")
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)
        report["packages"][role] = {"file": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "source_files": manifest}
    (dest / "build-manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def stale(base=BASE):
    """Read-only: what in firmware/dist no longer matches the current sources."""
    dest = base / "firmware/dist"
    try:
        built = json.loads((dest / "build-manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return ["build-manifest.json unreadable: " + str(error)]
    problems = []
    if {k: v for k, v in built.items() if k != "packages"} != FLAGS:
        problems.append("build-manifest.json flags changed")
    names = {role + "-micropython-files.zip" for role, _, _ in sources(base)}
    problems += ["unexpected package: " + p.name for p in sorted(dest.glob("*.zip")) if p.name not in names]
    for role, files, manifest in sources(base):
        path = dest / (role + "-micropython-files.zip")
        try:
            data = path.read_bytes()
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                listed = z.namelist()
                members = {name: z.read(name) for name in listed}
        except (OSError, zipfile.BadZipFile) as error:
            problems.append(role + ": unreadable package: " + str(error))
            continue
        expected = dict(files, **{"SOURCE-SHA256.json": json.dumps(manifest, indent=2).encode()})
        if len(listed) != len(members) or members != expected:
            problems.append(role + ": package contents differ from current sources")
        if built.get("packages", {}).get(role) != {"file": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "source_files": manifest}:
            problems.append(role + ": build-manifest.json record is stale")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Compare firmware/dist with the current sources; write nothing")
    args = ap.parse_args()
    if args.check:
        problems = stale()
        print(json.dumps({"status": "FAIL" if problems else "PASS", "problems": problems}, indent=2))
        return 1 if problems else 0
    report = build()
    print(json.dumps({role: p["bytes"] for role, p in report["packages"].items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
