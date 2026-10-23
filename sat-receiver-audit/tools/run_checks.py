#!/usr/bin/env python3
"""Run the reproducible schematic checks in dependency order, without masking failures.

Every file this writes is byte-reproducible: KiCad's run timestamps are replaced
by the root sheet's title-block date and absolute paths by project-relative ones
(see tools/normalise_outputs.py), so a rerun on any machine leaves git clean
unless the design itself changed.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import json

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "tools"))
import normalise_outputs as normalise  # noqa: E402


def import_pymupdf():
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf  # PyMuPDF < 1.24.3 only has the legacy name
    return pymupdf


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
    date = normalise.design_date(BASE)
    # Never validate new schematics against an earlier export's netlist or ERC.
    for stale in (verify / "netlist.xml", verify / "erc.json"):
        stale.unlink(missing_ok=True)
    run(args.kicad_cli, "sch", "export", "netlist", "--format", "kicadxml", "-o", verify / "netlist.xml", sch)
    normalise.rewrite(verify / "netlist.xml", lambda text: normalise.netlist(text, date))
    # Always produce the independent comparison report, even when ERC fails.
    erc = subprocess.run([args.kicad_cli, "sch", "erc", "--format", "json", "--severity-all", "--exit-code-violations", "-o", str(verify / "erc.json"), str(sch)], cwd=BASE)
    if erc.returncode not in (0, 5) or not (verify / "erc.json").is_file():
        raise SystemExit("KiCad ERC did not complete; validation not updated")
    normalise.rewrite(verify / "erc.json", lambda text: normalise.erc(text, date))
    run(sys.executable, BASE / "tools/validate_project.py")
    run(sys.executable, BASE / "tools/check_electrical_invariants.py")
    run(sys.executable, BASE / "verification/independent_netlist_check.py")
    # A relative --design keeps the build machine's directory out of the report.
    analysis = subprocess.run([sys.executable, "-X", "utf8", str(BASE / "design/E4-detector-analysis.py"), "--json", "--design", str(normalise.DC_DESIGN)], cwd=BASE, encoding="utf-8", capture_output=True, check=True)
    normalise.check_no_absolute_path(analysis.stdout, str(normalise.DC_ANALYSIS))
    (verify / "dc-detector-analysis.json").write_bytes(normalise.dc_analysis(analysis.stdout).encode("utf-8"))
    print("DC-detector arithmetic model: PASS; hardware qualification OPEN")
    if erc.returncode:
        raise SystemExit(erc.returncode)
    run(sys.executable, BASE / "tools/build_documents.py")
    if args.export:
        # A failed export must not leave the earlier PDF bound to new schematics.
        binding = verify / "pdf-export.json"
        binding.unlink(missing_ok=True)
        schematics = {p.relative_to(BASE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(cad.glob("*.kicad_sch"))}
        (cad / "svg").mkdir(exist_ok=True)
        run(args.kicad_cli, "sch", "export", "svg", "-o", cad / "svg", sch)
        for image in sorted((cad / "svg").glob("*.svg")):
            normalise.rewrite(image, lambda text: normalise.svg(text, date))
        pymupdf = import_pymupdf()
        # Export outside the live project, validate completely, then publish
        # atomically. KiCad can report success before producing a usable PDF.
        with tempfile.TemporaryDirectory(prefix="sr-rx-pdf-") as tmp:
            exported = Path(tmp) / "schematics.pdf"
            run(args.kicad_cli, "sch", "export", "pdf", "--exclude-pdf-property-popups", "--exclude-pdf-hierarchical-links", "-o", exported, sch)
            pdf = exported.read_bytes()
            if not pdf.startswith(b"%PDF-") or not pdf.rstrip().endswith(b"%%EOF"):
                raise SystemExit("PDF exporter returned an incomplete file; do not package it")
            pdf = normalise.pdf(pdf, date)
            normalise.check_no_absolute_path(pdf, str(normalise.PDF))
            with pymupdf.open(stream=pdf, filetype="pdf") as doc:
                expected = len(json.loads((cad / "generation-manifest.json").read_text(encoding="utf-8"))["pages"]) + 1
                if len(doc) != expected:
                    raise SystemExit("PDF has missing pages; do not package it")
                if doc.is_repaired:
                    raise SystemExit("PDF needed repair after date normalisation; do not package it")
                for page in doc:
                    page.get_text()
            staged = cad / "sr-rx-v2.pdf.tmp"
            staged.write_bytes(pdf)
            os.replace(staged, cad / "sr-rx-v2.pdf")
        if {p.relative_to(BASE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(cad.glob("*.kicad_sch"))} != schematics:
            raise SystemExit("Schematics changed during export; PDF left unbound")
        record = {"pdf": {"file": "build/kicad/sr-rx-v2.pdf", "sha256": hashlib.sha256(pdf).hexdigest()}, "kicad_sch_sha256": schematics}
        binding.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    try:
        main()
    except normalise.NotReproducible as error:
        raise SystemExit("NOT REPRODUCIBLE: " + str(error))
