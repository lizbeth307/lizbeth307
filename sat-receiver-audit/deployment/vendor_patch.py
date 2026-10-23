#!/usr/bin/env python3
"""Apply reviewed patches to a new copy of an exact vendor checkout, offline.

This is a staging helper, never an installer. The Lime patch guards Soapy and
typed Micro stream entry points; raw register/firmware paths still need audit.
It is not proof that the complete SDK or hardware cannot transmit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
PINS = {"rtlsdr": "797f8143266d983c56d8f35d2d442527529dd8a5",
        "limesuiteng": "37cb1833e35955f7072c0fb91642d14ae5515f28"}


class PatchError(ValueError):
    pass


PATCH_GIT = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "-c", "apply.whitespace=nowarn", "apply"]


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _run(args, cwd):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise PatchError(result.stderr.strip() or result.stdout.strip() or "command failed")
    return result.stdout.strip()


def check_source(component, source, fixture=False):
    if component not in PINS:
        raise PatchError("component has no reviewed patch")
    source = Path(source).resolve(strict=True)
    expected = json.loads((HERE / "patches/target-hashes.json").read_text())[component]
    if not fixture:
        if _run(["git", "rev-parse", "HEAD"], source) != PINS[component]:
            raise PatchError("vendor HEAD is not the exact pinned commit")
        if _run(["git", "status", "--porcelain", "--untracked-files=all", "--ignored"], source):
            raise PatchError("vendor checkout has local changes, untracked or ignored build files")
        if (source / ".gitmodules").exists():
            states = _run(["git", "submodule", "status", "--recursive"], source)
            if any(line.startswith(("-", "+", "U")) for line in states.splitlines()):
                raise PatchError("submodules are missing or differ from pinned source")
    for relative, hashes in expected.items():
        path = source / relative
        if path.is_symlink() or not path.is_file() or digest(path) != hashes["before_sha256"]:
            raise PatchError("source target SHA256 differs: " + relative)
    patch = HERE / "patches" / (component + "-rx-only.patch")
    _run(PATCH_GIT + ["--check", str(patch)], source)
    return source, expected, patch


def apply_to_copy(component, source, destination, fixture=False):
    source, expected, patch = check_source(component, source, fixture)
    destination = Path(destination).resolve()
    if destination.exists() or destination.is_relative_to(source) or source.is_relative_to(destination):
        raise PatchError("output must be a new directory separate from source")
    if str(destination).startswith(("/etc/", "/usr/", "/opt/", "/boot/", "/dev/", "/sys/", "/proc/")):
        raise PatchError("host prefixes are not vendor staging directories")
    # copytree preserves the upstream source and does not modify a host prefix.
    shutil.copytree(source, destination, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    try:
        _run(PATCH_GIT + [str(patch)], destination)
        for relative, hashes in expected.items():
            if digest(destination / relative) != hashes["after_sha256"]:
                raise PatchError("post-patch SHA256 differs: " + relative)
        result = {"component": component, "upstream_commit": PINS[component],
                  "patch_sha256": digest(patch), "target_hashes": expected,
                  "source_fixture_only": fixture, "release_ready": False,
                  "limits": "Source application checked; full vendor compile/native TX audit and hardware acceptance are separate."}
        (destination / "SRRX-PATCH-RECEIPT.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    except Exception:
        # Retain failed output for review; it is never silently treated as good.
        raise


def check_fixtures():
    results = []
    with tempfile.TemporaryDirectory(prefix="srrx-patch-check-") as temporary:
        for component in PINS:
            fixture = HERE / "upstream-fixtures" / ("rtl-sdr" if component == "rtlsdr" else component)
            results.append(apply_to_copy(component, fixture, Path(temporary) / component, fixture=True))
    return results


def apply_from_archive(component, archive_path, destination):
    """Verified full pinned archive can be used offline without .git history."""
    lock = json.loads((HERE / "sources.lock.json").read_text())
    component_record = next((c for c in lock["components"] if c["id"] == component), None)
    archive_path = Path(archive_path).resolve(strict=True)
    if (not component_record or not component_record.get("source_archive_sha256")
            or digest(archive_path) != component_record["source_archive_sha256"]
            or archive_path.stat().st_size != component_record.get("source_archive_size")):
        raise PatchError("archive has no matching independently acquired SHA256/size lock")
    if not hasattr(tarfile, "data_filter"):
        raise PatchError("safe tar data_filter is required; target CPython3.12 supports it")
    with tempfile.TemporaryDirectory(prefix="srrx-vendor-archive-") as temporary:
        temporary = Path(temporary)
        with tarfile.open(archive_path, "r:gz") as archive:
            members = archive.getmembers()
            if len(members) > 100_000 or sum(m.size for m in members) > 512 * 1024 * 1024:
                raise PatchError("source archive expansion exceeds staging limit")
            roots = set()
            for member in members:
                name = Path(member.name)
                if name.is_absolute() or ".." in name.parts or not name.parts:
                    raise PatchError("unsafe archive member")
                roots.add(name.parts[0])
            if len(roots) != 1 or component_record["commit"] not in next(iter(roots)):
                raise PatchError("archive root is not the full pinned commit")
            archive.extractall(temporary, members=members, filter="data")
        source = temporary / next(iter(roots))
        result = apply_to_copy(component, source, destination, fixture=True)
        result.update(source_fixture_only=False, source_verification="full_archive_SHA256",
                      source_archive_sha256=component_record["source_archive_sha256"])
        (Path(destination) / "SRRX-PATCH-RECEIPT.json").write_text(json.dumps(result, indent=2) + "\n")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="apply to temporary exact upstream fixtures only")
    parser.add_argument("--component", choices=PINS)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.check:
            if args.source or args.archive or args.output or args.component:
                parser.error("--check does not accept source/output/component")
            result = check_fixtures()
        else:
            if not args.component or not args.output or bool(args.source) == bool(args.archive):
                parser.error("supply --component, exactly one of --source/--archive, and a new --output")
            result = apply_from_archive(args.component, args.archive, args.output) if args.archive else apply_to_copy(args.component, args.source, args.output)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
