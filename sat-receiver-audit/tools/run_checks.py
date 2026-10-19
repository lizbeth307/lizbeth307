#!/usr/bin/env python3
"""Run the reproducible schematic checks in dependency order, without masking failures."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import json

BASE = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kicad-cli", default=os.environ.get("KICAD_CLI", shutil.which("kicad-cli")))
    ap.add_argument("--export", action="store_true", help="Also export SVG/PDF after checks pass")
    args = ap.parse_args()
    if not args.kicad_cli:
        ap.error("KiCad 10 CLI required: install it or provide --kicad-cli")
    def run(*cmd):
        subprocess.run(list(map(str, cmd)), cwd=BASE, check=True)
    cad = BASE / "build/kicad"
    verify = BASE / "verification"
    verify.mkdir(exist_ok=True)
    sch = cad / "sr-rx-v2.kicad_sch"
    run(sys.executable, BASE / "tools/generate_kicad.py")
    run(args.kicad_cli, "sch", "export", "netlist", "--format", "kicadxml", "-o", verify / "netlist.xml", sch)
    # Always produce the independent comparison report, even when ERC fails.
    erc = subprocess.run([args.kicad_cli, "sch", "erc", "--format", "json", "--severity-all", "--exit-code-violations", "-o", str(verify / "erc.json"), str(sch)], cwd=BASE)
    run(sys.executable, BASE / "tools/validate_project.py")
    run(sys.executable, BASE / "tools/check_electrical_invariants.py")
    analysis = subprocess.run([sys.executable, str(BASE / "design/E4-detector-analysis.py"), "--json"], cwd=BASE, text=True, capture_output=True, check=True)
    (verify / "dc-detector-analysis.json").write_text(analysis.stdout)
    print("DC-detector arithmetic model: PASS; hardware qualification OPEN")
    if erc.returncode:
        raise SystemExit(erc.returncode)
    run(sys.executable, BASE / "tools/build_documents.py")
    if args.export:
        (cad / "svg").mkdir(exist_ok=True)
        run(args.kicad_cli, "sch", "export", "svg", "-o", cad / "svg", sch)
        import fitz
        # Export outside the live project, validate completely, then publish
        # atomically. KiCad can report success before producing a usable PDF.
        with tempfile.TemporaryDirectory(prefix="sr-rx-pdf-") as tmp:
            exported = Path(tmp) / "schematics.pdf"
            run(args.kicad_cli, "sch", "export", "pdf", "--exclude-pdf-property-popups", "--exclude-pdf-hierarchical-links", "-o", exported, sch)
            pdf = exported.read_bytes()
            if not pdf.startswith(b"%PDF-") or not pdf.rstrip().endswith(b"%%EOF"):
                raise SystemExit("PDF exporter returned an incomplete file; do not package it")
            with fitz.open(stream=pdf, filetype="pdf") as doc:
                expected = len(json.loads((cad / "generation-manifest.json").read_text())["pages"]) + 1
                assert len(doc) == expected, "PDF has missing pages"
                for page in doc:
                    page.get_text()
            staged = cad / "sr-rx-v2.pdf.tmp"
            staged.write_bytes(pdf)
            os.replace(staged, cad / "sr-rx-v2.pdf")


if __name__ == "__main__":
    main()
