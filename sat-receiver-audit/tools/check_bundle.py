#!/usr/bin/env python3
"""Independently verify the final offline HTML, project ZIP and canonical PDF.

Read-only: no bundle generation, CAD export, downloads or report-file writes.
Relative artifact arguments are resolved under --project.

The stand-alone SR-RX-v2-project.zip is written by tools/build_bundle.py and is
not tracked in git. When --archive is not given and that file is absent (for
example on a clean checkout), the ZIP embedded in the HTML (#source-archive) is
checked against the current tree instead; the report then says
"archive_source": "html#source-archive". In that mode the HTML-to-ZIP byte
comparison is self-referential, so only the ZIP-to-tree binding is evidence.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from collections import Counter
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
from urllib.parse import unquote, urlsplit
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
ROOT = "SR-RX-v2"
MANIFEST = "ARCHIVE-MANIFEST.json"
ARCHIVE_NAME = "SR-RX-v2-project.zip"
EMBEDDED = "html#source-archive"


class InvalidBundle(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidBundle(message)


def digest_file(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def digest_stream(stream):
    value = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        value.update(block)
    return value.hexdigest()


def safe_path(value, directory=False):
    require(isinstance(value, str) and value, "Empty/non-string archive path")
    require(not any(ord(c) < 32 for c in value) and "\\" not in value,
            "Control character or backslash in archive path: " + repr(value))
    normalized = value[:-1] if directory and value.endswith("/") else value
    path = PurePosixPath(normalized)
    require(normalized and not path.is_absolute() and path.parts and
            all(p not in (".", "..") for p in path.parts) and ":" not in path.parts[0] and
            path.as_posix() == normalized,
            "Unsafe/aliased archive path: " + repr(value))
    return path


def eligible(relative):
    """Independent explicit release-file policy; never import the generator."""
    if any(part in {".git", "tmp", "qa", "__pycache__", ".ruff_cache", ".pytest_cache", ".mypy_cache", ".venv", "venv"} for part in relative.parts):
        return False
    suffix = relative.suffix.lower()
    if suffix in {".pyc", ".kicad_prl", ".lck", ".tmp"}:
        return False
    if suffix == ".html" and relative.as_posix() != "verification/module-lab/module-results.html":
        return False
    if suffix == ".png" and relative.parts[:2] not in {
            ("verification", "hmi-views"), ("verification", "linux-lab")}:
        return False
    if suffix == ".zip" and relative.parts[:2] != ("firmware", "dist"):
        return False
    return True


def project_files(project):
    found = {}
    for path in project.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(project)
        if eligible(relative):
            require(not path.is_symlink() and path.resolve().is_relative_to(project),
                    "Release source is a symlink/outside project: " + relative.as_posix())
            safe_path(relative.as_posix())
            found[relative.as_posix()] = path
    return found


def read_json(raw):
    return json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(
        InvalidBundle("Non-finite JSON value: " + value)))


def validate_manifest(records):
    require(isinstance(records, list), "ARCHIVE-MANIFEST must be a list")
    found = {}
    for row in records:
        require(isinstance(row, dict), "Non-object ARCHIVE-MANIFEST record")
        relative = safe_path(row.get("path")).as_posix()
        require(relative != MANIFEST and relative not in found,
                "Duplicate/self-referential manifest path: " + relative)
        require(type(row.get("bytes")) is int and row["bytes"] >= 0,
                "Invalid manifest byte count: " + relative)
        require(isinstance(row.get("sha256"), str) and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]),
                "Invalid manifest SHA256: " + relative)
        found[relative] = row
    return found


def check_zip(project, path):
    """path is a ZIP file path or, for the HTML-embedded archive, its bytes."""
    current = project_files(project)
    archive_name = ARCHIVE_NAME if isinstance(path, bytes) else path.name
    source = io.BytesIO(path) if isinstance(path, bytes) else path
    with zipfile.ZipFile(source) as archive:
        members = {}
        seen = set()
        for item in archive.infolist():
            member = safe_path(item.filename, item.is_dir())
            require(member.parts[0] == ROOT and len(member.parts) > 1,
                    "Unexpected ZIP root/member: " + item.filename)
            canonical = member.as_posix()
            require(canonical not in seen, "Duplicate ZIP member: " + item.filename)
            seen.add(canonical)
            require(not item.flag_bits & 1, "Encrypted ZIP member: " + item.filename)
            mode = stat.S_IFMT(item.external_attr >> 16)
            require(mode in (0, stat.S_IFDIR if item.is_dir() else stat.S_IFREG),
                    "ZIP symlink/special file: " + item.filename)
            if item.is_dir():
                continue
            relative = PurePosixPath(*member.parts[1:]).as_posix()
            require(relative not in {archive_name, ARCHIVE_NAME, "SR-RX-v2-ves-proekt.html"},
                    "Recursive release artifact inside ZIP: " + relative)
            require(not relative.endswith(".zip") or PurePosixPath(relative).parts[:2] == ("firmware", "dist"),
                    "Unexpected nested ZIP: " + relative)
            members[relative] = item
        require(MANIFEST in members, "Missing ARCHIVE-MANIFEST.json")
        require(members[MANIFEST].file_size <= 16 * 1024 * 1024, "Unreasonably large archive manifest")
        manifest = validate_manifest(read_json(archive.read(members[MANIFEST])))
        actual = set(members) - {MANIFEST}
        require(actual == set(manifest), "Manifest/ZIP path mismatch; missing=" +
                repr(sorted(set(manifest) - actual)[:12]) + "; extra=" + repr(sorted(actual - set(manifest))[:12]))
        require(actual == set(current), "ZIP/current-project file set mismatch; missing=" +
                repr(sorted(set(current) - actual)[:12]) + "; extra=" + repr(sorted(actual - set(current))[:12]))
        # Bound decompression to the actual source files before the full CRC pass.
        for name, row in manifest.items():
            require(members[name].file_size == row["bytes"] == current[name].stat().st_size,
                    "ZIP/manifest/current byte count mismatch: " + name)
        bad = archive.testzip()
        require(bad is None, "ZIP CRC failure: " + str(bad))
        total = 0
        for name, row in manifest.items():
            with archive.open(members[name]) as stream:
                require(digest_stream(stream) == row["sha256"], "ZIP/manifest SHA256 mismatch: " + name)
            require(digest_file(current[name]) == row["sha256"], "Current project differs from ZIP: " + name)
            total += row["bytes"]
            if name.lower().endswith(".zip"):
                # Firmware archives are legitimate; a renamed project release is
                # still recursion and is never a firmware distribution.
                with archive.open(members[name]) as stream:
                    nested = stream.read()
                with zipfile.ZipFile(io.BytesIO(nested)) as inner:
                    require(not any(PurePosixPath(n).name == MANIFEST for n in inner.namelist()),
                            "Nested project release archive: " + name)
    return {"status": "PASS", "crc": "PASS", "manifest_records": len(manifest),
            "uncompressed_source_bytes": total, "current_project_binding": "PASS"}


def clean_url(value):
    return re.sub(r"[\x00-\x20]", "", value.strip())


def decode_data_uri(value, expected_mime=None):
    require(isinstance(value, str) and value.lower().startswith("data:") and "," in value,
            "Expected a data URI")
    header, body = value.split(",", 1)
    parts = header[5:].split(";")
    mime = parts[0].lower()
    if expected_mime:
        require(mime == expected_mime, "Unexpected data MIME: " + mime)
    require(parts[1:] == ["base64"], "Expected canonical base64 data URI")
    try:
        return mime, base64.b64decode(body, validate=True)
    except (binascii.Error, ValueError) as error:
        raise InvalidBundle("Invalid base64 data URI: " + str(error)) from error


def css_unescape(value):
    value = re.sub(r"/\*.*?\*/", "", value, flags=re.S)
    value = re.sub(r"\\(?:\r\n|[\r\n\f])", "", value)
    def replace(match):
        if match.group(1):
            code = int(match.group(1), 16)
            return chr(code) if 0 < code <= 0x10ffff else "\ufffd"
        return match.group(2)
    return re.sub(r"\\([0-9a-fA-F]{1,6})(?:\r\n|[ \t\r\n\f])?|\\([^\r\n\f])", replace, value)


def check_css(value, label):
    css = css_unescape(value)
    require(not re.search(r"@import\b|(?:-webkit-)?image-set\s*\(|expression\s*\(|-moz-binding\s*:", css, re.I),
            "CSS loading/executable construct: " + label)
    for match in re.finditer(r"url\s*\((.*?)\)", css, flags=re.I | re.S):
        url = clean_url(match.group(1).strip().strip("\"'"))
        require(url.startswith("#") and len(url) > 1,
                "CSS automatic resource outside local fragment: " + label + " " + url[:120])


def local_name(value):
    return value.rsplit("}", 1)[-1].rsplit(":", 1)[-1].lower() if isinstance(value, str) else ""


def check_document(tree, label="HTML", svg=False):
    """Check static resources without fetching or executing any document code."""
    ids = [node.get("id") for node in tree.iter() if isinstance(node.tag, str) and node.get("id") is not None]
    duplicates = sorted(k for k, count in Counter(ids).items() if count > 1)
    require(not duplicates, label + " duplicate IDs: " + repr(duplicates[:12]))
    require(all(ids), label + " has an empty ID")
    known = set(ids)
    anchors = images = 0
    forbidden = {"script", "iframe", "frame", "frameset", "object", "embed", "applet", "foreignobject",
                 "set", "animate", "animatemotion", "animatetransform", "discard"}
    resource_attrs = {"src", "poster", "background", "data", "codebase", "archive", "manifest"}
    svg_resources = {"image", "use", "feimage", "mpath"}
    css_attrs = {"style", "fill", "stroke", "filter", "clip-path", "mask", "marker-start", "marker-mid", "marker-end"}
    for node in tree.iter():
        if not isinstance(node.tag, str):
            continue
        tag = local_name(node.tag)
        require(tag not in forbidden, label + " forbidden active element: " + tag)
        require(tag != "base", label + " base URL can redirect local references")
        require(not (tag == "meta" and node.get("http-equiv", "").lower().strip() == "refresh"),
                label + " meta refresh is automatic navigation")
        if tag == "style":
            check_css("".join(node.itertext()), label + " stylesheet")
        for attribute, raw in node.attrib.items():
            attr = local_name(attribute)
            require(not attr.startswith("on"), label + " event handler: " + attr)
            require(attr != "base", label + " xml:base can redirect local references")
            require(attr not in {"srcset", "imagesrcset"}, label + " srcset is not a verified offline resource")
            if attr in css_attrs:
                check_css(raw, label + " " + tag + "[" + attr + "]")
            url = clean_url(raw)
            if attr == "href":
                if url.startswith("#"):
                    target = unquote(url[1:])
                    require(not target or target in known, label + " broken internal anchor: " + url[:180])
                    anchors += 1
                elif tag == "a":
                    scheme = urlsplit(url).scheme.lower()
                    require(scheme in {"http", "https", "mailto", "data"} or url.startswith("//"),
                            label + " non-self-contained/unsafe hyperlink: " + url[:180])
                else:
                    require(tag in svg_resources, label + " unsupported automatic href element: " + tag)
                    require(url.startswith("data:"), label + " automatic href resource: " + url[:180])
            if attr in resource_attrs or (attr == "href" and tag in svg_resources):
                if attr == "href" and tag in svg_resources and url.startswith("#"):
                    continue
                require(url.startswith("data:"), label + " automatic non-embedded resource: " + tag + " " + url[:180])
                mime, payload = decode_data_uri(raw)
                if tag in {"img", "image", "feimage", "input"}:
                    require(mime.startswith("image/"), label + " non-image data used as an image")
                    images += 1
                if mime == "image/svg+xml":
                    from lxml import etree
                    declarations = re.findall(rb"<!DOCTYPE\b.*?>", payload, flags=re.I | re.S)
                    require(len(declarations) <= 1 and b"<!ENTITY" not in payload.upper() and
                            not any(b"[" in declaration for declaration in declarations),
                            label + " SVG entity/internal DTD is not permitted")
                    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
                    document = etree.fromstring(payload, parser=parser)
                    if declarations:
                        # KiCad emits this public SVG declaration. It is metadata;
                        # the validator neither resolves nor downloads its DTD.
                        info = document.getroottree().docinfo
                        require(info.public_id == "-//W3C//DTD SVG 1.1//EN" and info.system_url in {
                            "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd",
                            "https://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"},
                            label + " unrecognized external SVG DTD")
                    # The release generator's embedded SVGs are self-contained;
                    # nested data resources are rejected to bound recursion.
                    require(not document.xpath('//*[local-name()="image" or local-name()="feImage"]'),
                            label + " nested SVG image resource requires separate qualification")
                    check_document(document, label + " embedded SVG", svg=True)
    return {"unique_ids": len(known), "internal_links": anchors, "embedded_images": images,
            "external_automatic_resources": 0}


def equal_bytes(data, canonical):
    if isinstance(canonical, bytes):
        return data == canonical
    if len(data) != canonical.stat().st_size:
        return False
    with canonical.open("rb") as stream:
        for offset in range(0, len(data), 1024 * 1024):
            if stream.read(1024 * 1024) != data[offset:offset + 1024 * 1024]:
                return False
        return not stream.read(1)


def check_html(path, pdf, archive):
    from lxml import html
    parser = html.HTMLParser(huge_tree=True, no_network=True)
    tree = html.parse(str(path), parser=parser).getroot()
    details = check_document(tree)
    attachments = {"application/pdf": [], "application/zip": []}
    for node in tree.xpath('//a[@href]'):
        value = clean_url(node.get("href"))
        if value.lower().startswith("data:"):
            mime = value.split(",", 1)[0][5:].split(";", 1)[0].lower()
            if mime in attachments:
                attachments[mime].append(node)
    for identifier, mime, canonical in (("download-pdf", "application/pdf", pdf),
                                         ("source-archive", "application/zip", archive)):
        nodes = tree.xpath('//*[@id=$identifier]', identifier=identifier)
        require(len(nodes) == 1 and local_name(nodes[0].tag) == "a", "Missing/ambiguous attachment: " + identifier)
        _, data = decode_data_uri(nodes[0].get("href"), mime)
        require(equal_bytes(data, canonical), "Embedded attachment differs from canonical file: " + identifier)
        require(len(attachments[mime]) == 1 and attachments[mime][0] is nodes[0],
                "Missing/duplicate embedded " + mime + " attachments")
    return {"status": "PASS", "canonical_pdf_and_zip_bytes": "IDENTICAL", **details}


def import_pymupdf():
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf  # PyMuPDF < 1.24.3 only has the legacy name
    return pymupdf


def embedded_archive(document):
    """Decode the single #source-archive ZIP of the HTML, without writing it anywhere."""
    from lxml import html
    parser = html.HTMLParser(huge_tree=True, no_network=True)
    tree = html.parse(str(document), parser=parser).getroot()
    nodes = tree.xpath('//*[@id="source-archive"]')
    require(len(nodes) == 1 and local_name(nodes[0].tag) == "a", "Missing/ambiguous attachment: source-archive")
    return decode_data_uri(nodes[0].get("href"), "application/zip")[1]


def check_pdf(path, expected_pages, project=PROJECT):
    with path.open("rb") as source:
        require(source.read(5) == b"%PDF-", "Canonical PDF has no PDF header")
        source.seek(max(0, path.stat().st_size - 4096))
        require(source.read().rstrip().endswith(b"%%EOF"), "Canonical PDF has no final %%EOF")
    # The export record binds these exact PDF bytes to the schematics KiCad exported.
    export = read_json((project / "verification/pdf-export.json").read_bytes())
    require(isinstance(export, dict) and export.get("pdf") == {"file": "build/kicad/sr-rx-v2.pdf", "sha256": digest_file(path)},
            "Canonical PDF is not the recorded KiCad export")
    schematics = {p.relative_to(project).as_posix(): digest_file(p) for p in sorted((project / "build/kicad").glob("*.kicad_sch"))}
    require(schematics and export.get("kicad_sch_sha256") == schematics,
            "Canonical PDF export is not bound to the current schematics")
    try:
        pymupdf = import_pymupdf()
    except ImportError as error:
        raise InvalidBundle("PyMuPDF/fitz is required to verify the canonical PDF page count") from error
    with pymupdf.open(path) as document:
        require(not document.is_encrypted, "Canonical PDF is encrypted")
        require(not document.is_repaired, "Canonical PDF needed parser repair")
        require(len(document) == expected_pages,
                "Canonical PDF page count is " + str(len(document)) + "; expected " + str(expected_pages))
        return {"status": "PASS", "header_and_eof": "PASS", "pages": len(document),
                "parser_repaired": False, "schematic_export_binding": "PASS"}


def check_firmware(project):
    """Shipped MicroPython packages must hold exactly the current sources."""
    dist = project / "firmware/dist"
    roles = ("imu", "pico")
    record = read_json((dist / "build-manifest.json").read_bytes())
    require(isinstance(record, dict) and isinstance(record.get("packages"), dict) and set(record["packages"]) == set(roles),
            "Invalid firmware build manifest")
    require({p.name for p in dist.glob("*.zip")} == {role + "-micropython-files.zip" for role in roles},
            "Unexpected firmware package set in firmware/dist")
    for role in roles:
        expected = {p.name: p.read_bytes() for p in sorted((project / "firmware" / role).glob("*.py"))}
        expected["wire.py"] = (project / "software/srrx/wire.py").read_bytes()
        hashes = {name: hashlib.sha256(data).hexdigest() for name, data in expected.items()}
        package = dist / (role + "-micropython-files.zip")
        entry = record["packages"][role]
        require(isinstance(entry, dict) and entry.get("file") == package.name and entry.get("sha256") == digest_file(package)
                and entry.get("source_files") == hashes, "Stale firmware build record: " + role)
        with zipfile.ZipFile(package) as archive:
            names = archive.namelist()
            require(len(names) == len(set(names)), "Duplicate firmware package member: " + role)
            members = {name: archive.read(name) for name in names}
        sums = read_json(members.pop("SOURCE-SHA256.json", b"null"))
        require(members == expected and sums == hashes, "Firmware package differs from current sources: " + role)
    return {"status": "PASS", "packages": list(roles), "current_source_binding": "PASS"}


def generated_pages(project):
    """Contents page plus every electrical page of the generated KiCad project."""
    manifest = json.loads((project / "build/kicad/generation-manifest.json").read_text(encoding="utf-8"))
    return len(manifest["pages"]) + 1


def validate(project, archive, document, pdf, expected_pages=None):
    """archive is a ZIP path, or None to check the ZIP embedded in the HTML."""
    checks, errors, before = {}, [], {}
    if expected_pages is None:
        expected_pages = generated_pages(project)
    files = [("html", document), ("pdf", pdf)] + ([("archive", archive)] if archive is not None else [])
    for name, path in files:
        try:
            require(path.is_file(), "Missing canonical artifact: " + str(path))
            before[name] = {"bytes": path.stat().st_size, "sha256": digest_file(path)}
        except (OSError, ValueError) as error:
            errors.append(str(error))
    if archive is None:
        try:
            require("html" in before, "No HTML to take the embedded archive from")
            archive = embedded_archive(document)
            before["archive"] = {"source": EMBEDDED, "bytes": len(archive),
                                 "sha256": hashlib.sha256(archive).hexdigest()}
        except Exception as error:
            errors.append("archive: " + type(error).__name__ + ": " + str(error))
            archive = b""
    stages = (("zip", lambda: check_zip(project, archive)), ("html", lambda: check_html(document, pdf, archive)),
              ("pdf", lambda: check_pdf(pdf, expected_pages, project)), ("firmware", lambda: check_firmware(project)))
    for name, operation in stages:
        try:
            checks[name] = operation()
        except Exception as error:
            # The command remains a read-only validator even for malformed XML,
            # base64, ZIP or JSON; failures are visible and never become PASS.
            errors.append(name + ": " + type(error).__name__ + ": " + str(error))
            checks[name] = {"status": "FAIL"}
    for name, path in files:
        if name in before:
            try:
                require(before[name] == {"bytes": path.stat().st_size, "sha256": digest_file(path)},
                        "Artifact changed while validating: " + name)
            except (OSError, ValueError) as error:
                errors.append(str(error))
    return {"status": "FAIL" if errors else "PASS", "read_only": True,
            "archive_source": EMBEDDED if isinstance(archive, bytes) else "file",
            "artifacts": before, "checks": checks, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=PROJECT)
    parser.add_argument("--archive", type=Path, default=None,
                        help="Project ZIP from tools/build_bundle.py (default: " + ARCHIVE_NAME +
                             " if present, else the ZIP embedded in the HTML)")
    parser.add_argument("--embedded-archive", action="store_true",
                        help="Check the ZIP embedded in the HTML even if " + ARCHIVE_NAME + " exists")
    parser.add_argument("--html", type=Path, default=Path("SR-RX-v2-ves-proekt.html"))
    parser.add_argument("--pdf", type=Path, default=Path("build/kicad/sr-rx-v2.pdf"))
    parser.add_argument("--expected-pages", type=int, default=None,
                        help="Default: contents page + electrical pages in build/kicad/generation-manifest.json")
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    if not project.is_dir() or (args.expected_pages is not None and args.expected_pages < 1):
        parser.error("Existing --project directory and positive --expected-pages required")
    if args.archive and args.embedded_archive:
        parser.error("--archive and --embedded-archive are mutually exclusive")
    def artifact(path):
        return (path if path.is_absolute() else project / path).resolve()
    archive = artifact(args.archive or Path(ARCHIVE_NAME))
    if args.embedded_archive or (args.archive is None and not archive.is_file()):
        archive = None
    report = validate(project, archive, artifact(args.html), artifact(args.pdf), args.expected_pages)
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
