#!/usr/bin/env python3
"""Make the KiCad check/export outputs byte-reproducible.

KiCad 10 stamps the wall-clock time into the XML netlist, the ERC report,
every SVG <title> and the PDF /CreationDate, and writes the absolute path of
the schematic into the netlist. Those fields change on every run and leak the
directory layout of whichever machine ran the export. This module rewrites
exactly those fields:

* run timestamps -> the root sheet's title-block date (the design revision
  date) at 00:00:00. The wall-clock time of a run is deliberately not kept.
* absolute schematic path -> the path relative to the project root.

Each rewrite is anchored to the KiCad 10 field it replaces. If a field has an
unexpected form, the step fails instead of silently leaving machine state in
tracked files. The PDF date is replaced by a string of the same length, so the
PDF cross-reference offsets stay valid and nothing else in the file moves.

tools/run_checks.py applies this to every output it writes. Run this file
directly to normalise outputs that are already in the tree (no KiCad needed):

    python3 tools/normalise_outputs.py            # rewrite in place
    python3 tools/normalise_outputs.py --check    # exit 1 if anything would change
    python3 tools/normalise_outputs.py --no-pdf   # leave the PDF bytes alone
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

BASE = Path(__file__).resolve().parents[1]
SCHEMATIC = PurePosixPath("build/kicad/sr-rx-v2.kicad_sch")
NETLIST = PurePosixPath("verification/netlist.xml")
ERC = PurePosixPath("verification/erc.json")
DC_ANALYSIS = PurePosixPath("verification/dc-detector-analysis.json")
DC_DESIGN = PurePosixPath("design/E4.json")
SVG_DIR = PurePosixPath("build/kicad/svg")
PDF = PurePosixPath("build/kicad/sr-rx-v2.pdf")


class NotReproducible(RuntimeError):
    """A KiCad output no longer has the form this normaliser was written for."""


def design_date(base: Path = BASE) -> tuple[str, str, str]:
    """Title-block date of the root sheet as (YYYY, MM, DD)."""
    text = (base / SCHEMATIC).read_bytes().decode("utf-8")
    match = re.search(r'\(title_block\b.{0,4000}?\(date\s+"(\d{4})-(\d{2})-(\d{2})"\)', text, re.S)
    if not match:
        raise NotReproducible(f"{SCHEMATIC}: root title block has no (date \"YYYY-MM-DD\")")
    return match.group(1), match.group(2), match.group(3)


def iso(date: tuple[str, str, str]) -> str:
    return "{}-{}-{}T00:00:00".format(*date)


def _sub_once(pattern: str, replace, text: str, what: str, flags: int = 0) -> str:
    result, count = re.subn(pattern, replace, text, count=1, flags=flags)
    if count != 1:
        raise NotReproducible(what + ": expected KiCad field not found; update tools/normalise_outputs.py")
    return result


def netlist(text: str, date) -> str:
    """<design><source>ABSOLUTE</source><date>NOW</date> -> relative path, design date."""
    def replace(match):
        source = match.group(2)
        if PurePosixPath(source.replace("\\", "/")).name != SCHEMATIC.name:
            raise NotReproducible(f"{NETLIST}: netlist was exported from {source!r}, not {SCHEMATIC}")
        return match.group(1) + str(SCHEMATIC) + match.group(3) + iso(date) + match.group(4)
    return _sub_once(r"(<design>\s*<source>)([^<]*)(</source>\s*<date>)[^<]*(</date>)", replace, text,
                     f"{NETLIST} <design> source/date")


def erc(text: str, date) -> str:
    """Top-level "date" of the KiCad ERC JSON report -> design date."""
    result = _sub_once(r'^(\s*"date":\s*")[^"]*(")', lambda m: m.group(1) + iso(date) + m.group(2), text,
                       f"{ERC} date", flags=re.M)
    report = json.loads(result)
    if report.get("date") != iso(date):
        raise NotReproducible(f"{ERC}: the rewritten date is not the report's top-level date")
    if os.path.isabs(str(report.get("source", ""))):
        raise NotReproducible(f"{ERC}: KiCad wrote an absolute source path")
    return result


def svg(text: str, date) -> str:
    """<title>SVG Image created as NAME date NOW </title> -> design date."""
    return _sub_once(r"(<title>SVG Image created as [^<]*? date )[^<\s]+( </title>)",
                     lambda m: m.group(1) + iso(date) + m.group(2), text, "SVG <title> date")


def dc_analysis(text: str) -> str:
    """design_file written by design/E4-detector-analysis.py -> project-relative path."""
    def replace(match):
        value = json.loads(match.group(2))
        posix = value.replace("\\", "/")
        if posix != str(DC_DESIGN) and not posix.endswith("/" + str(DC_DESIGN)):
            raise NotReproducible(f"{DC_ANALYSIS}: unexpected design_file {value!r}")
        return match.group(1) + json.dumps(str(DC_DESIGN)) + match.group(3)
    return _sub_once(r'^(\s*"design_file":\s*)("(?:[^"\\]|\\.)*")(,?)$', replace, text,
                     f"{DC_ANALYSIS} design_file", flags=re.M)


_KICAD_PDF_DATE = re.compile(rb"D:\d{4}:\d{2}:\d{2}:\d{2}:\d{2}:\d{2}")           # KiCad 10
_PDF_DATE = re.compile(rb"D:(\d{14})(Z|[+-]\d{2}'\d{2}'?|[+-]\d{2})?")           # ISO 32000


def pdf(data: bytes, date) -> bytes:
    """/CreationDate and /ModDate -> design date, keeping every byte offset."""
    year, month, day = date

    def replace(match):
        old = match.group(2)
        if _KICAD_PDF_DATE.fullmatch(old):
            new = f"D:{year}:{month}:{day}:00:00:00".encode()
        else:
            standard = _PDF_DATE.fullmatch(old)
            if not standard:
                raise NotReproducible(f"{PDF}: unrecognised PDF date {old!r}")
            zone = standard.group(2) or b""
            zone = re.sub(rb"\d", b"0", zone)  # same length, UTC
            new = f"D:{year}{month}{day}000000".encode() + zone
        if len(new) != len(old):
            raise NotReproducible(f"{PDF}: date rewrite would move PDF offsets")
        return match.group(1) + new + match.group(3)
    return re.sub(rb"(/(?:CreationDate|ModDate)\s*\()([^)]*)(\))", replace, data)


def check_no_absolute_path(data: bytes | str, what: str, base: Path = BASE) -> None:
    """Fail when an output still names the project directory of this machine."""
    blob = data.encode("utf-8") if isinstance(data, str) else data
    for root in {str(base), str(base.resolve())}:
        if len(root) > 1 and root.encode() in blob:
            raise NotReproducible(f"{what} contains the absolute project path {root}")


def rewrite(path: Path, transform, base: Path = BASE, binary: bool = False, write: bool = True) -> bool:
    """Apply transform to path; write only when bytes change. Returns True if they would change."""
    raw = path.read_bytes()
    if binary:
        new = transform(raw)
    else:
        new = transform(raw.decode("utf-8")).encode("utf-8")
    check_no_absolute_path(new, str(path.relative_to(base)) if path.is_relative_to(base) else str(path), base)
    if new == raw:
        return False
    if write:
        staged = path.with_name(path.name + ".tmp")
        staged.write_bytes(new)
        os.chmod(staged, stat.S_IMODE(path.stat().st_mode))
        os.replace(staged, path)
    return True


def normalise_tree(base: Path = BASE, write: bool = True, include_pdf: bool = True) -> list[str]:
    """Normalise every KiCad/analysis output present under base; return changed paths."""
    date = design_date(base)
    jobs = [(base / NETLIST, lambda t: netlist(t, date), False),
            (base / ERC, lambda t: erc(t, date), False),
            (base / DC_ANALYSIS, dc_analysis, False)]
    jobs += [(path, lambda t: svg(t, date), False) for path in sorted((base / SVG_DIR).glob("*.svg"))]
    if include_pdf:
        jobs.append((base / PDF, lambda b: pdf(b, date), True))
    changed = []
    for path, transform, binary in jobs:
        if path.is_file() and rewrite(path, transform, base, binary=binary, write=write):
            changed.append(path.relative_to(base).as_posix())
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, default=BASE)
    parser.add_argument("--check", action="store_true", help="Only report; exit 1 if any output would change")
    parser.add_argument("--no-pdf", action="store_true", help="Do not rewrite the PDF /CreationDate")
    args = parser.parse_args()
    base = args.project.resolve()
    try:
        changed = normalise_tree(base, write=not args.check, include_pdf=not args.no_pdf)
    except NotReproducible as error:
        print("NOT REPRODUCIBLE: " + str(error), file=sys.stderr)
        return 2
    verb = "would change" if args.check else "normalised"
    for name in changed:
        print(f"{verb}: {name}")
    if not changed:
        print("all outputs already normalised")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
