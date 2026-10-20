#!/usr/bin/env python3
"""Package reviewed MicroPython source files, without pretending to build a UF2."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

BASE = Path(__file__).resolve().parents[1]


def main():
    dest = BASE / "firmware/dist"
    dest.mkdir(exist_ok=True)
    report = {"runtime_included": False, "device_flashed": False, "hardware_qualified": False, "packages": {}}
    for role in ("pico", "imu"):
        files = {p.name: p.read_bytes() for p in sorted((BASE / "firmware" / role).glob("*.py"))}
        files["wire.py"] = (BASE / "software/srrx/wire.py").read_bytes()
        # No accepted calibration or hardware-enabled commissioning file ships.
        manifest = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in files.items():
                z.writestr(name, data)
            z.writestr("SOURCE-SHA256.json", json.dumps(manifest, indent=2))
        data = buffer.getvalue()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            assert z.testzip() is None
        path = dest / (role + "-micropython-files.zip")
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)
        report["packages"][role] = {"file": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "source_files": manifest}
    (dest / "build-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({role: p["bytes"] for role, p in report["packages"].items()}))


if __name__ == "__main__":
    main()
