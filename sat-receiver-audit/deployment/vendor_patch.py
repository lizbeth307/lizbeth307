#!/usr/bin/env python3
"""Apply reviewed patches to a new copy of an exact vendor checkout, offline.

This is a staging helper, never an installer. The Lime patch guards Soapy and
typed Micro stream entry points; raw register/firmware paths still need audit.
It is not proof that the complete SDK or hardware cannot transmit.
The reviewed patch of a component is patches/<id>-rx-only.patch with its target hashes in
patches/target-hashes.json; the pinned commit is that component's commit in sources.lock.json.
apply_listed applies the other patches of a schema-2 recipe (deployment/recipes/<id>/patches/,
source.patches) after checking their SHA-256 and the git blob of every target.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
FIXTURES = {"rtlsdr": "rtl-sdr"}  # upstream-fixtures/<directory> when it differs from the component id


class PatchError(ValueError):
    pass


PATCH_GIT = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "-c", "apply.whitespace=nowarn", "apply"]


def pins():
    """{component: pinned commit} of every reviewed -rx-only.patch, in patches/target-hashes.json
    order, with the commit taken from sources.lock.json (not a copy in this file). A target-hash
    entry without a locked 40-hex commit or without its patch file fails."""
    lock = {c["id"]: c for c in json.loads((HERE / "sources.lock.json").read_text(encoding="utf-8"))["components"]}
    result = {}
    for component in json.loads((HERE / "patches/target-hashes.json").read_text(encoding="utf-8")):
        commit = (lock.get(component) or {}).get("commit")
        if type(commit) is not str or not re.fullmatch(r"[0-9a-f]{40}", commit) or not (HERE / "patches" / (component + "-rx-only.patch")).is_file():
            raise PatchError("reviewed patch has no locked commit or no patch file: " + component)
        result[component] = commit
    return result


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def git_blob(path):
    data = Path(path).read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data, usedforsecurity=False).hexdigest()


def _run(args, cwd, env=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30, env=env)
    if result.returncode:
        raise PatchError(result.stderr.strip() or result.stdout.strip() or "command failed")
    return result.stdout.strip()


def apply_listed(tree, base, patches):
    """source.patches of a schema-2 recipe, in order, onto an extracted tree (offline, git apply):
    before each patch its file must have the recorded SHA-256 and every target the recorded git
    blob, and `git apply --numstat` must name exactly the targets. Returns one receipt per patch
    (file, sha256, strip, targets before, git blobs after)."""
    tree, base = Path(tree).resolve(strict=True), Path(base).resolve(strict=True)
    # No repository above the tree is ever discovered: git apply works on plain files here.
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(tree.parent))
    receipts = []
    for entry in patches:
        patch = base / entry["file"]
        if (patch.is_symlink() or not patch.is_file() or not patch.resolve().is_relative_to(base / "patches")
                or digest(patch) != entry["sha256"]):
            raise PatchError("listed patch differs from its recorded SHA-256: " + entry["file"])
        for relative, blob in entry["targets"].items():
            path = tree / relative
            if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(tree) or git_blob(path) != blob:
                raise PatchError("patch target differs from its recorded git blob: " + relative)
        strip = "-p%d" % entry["strip"]
        touched = {line.split("\t", 2)[-1] for line in _run(PATCH_GIT + [strip, "--numstat", str(patch)], tree, env).splitlines() if line.strip()}
        if touched != set(entry["targets"]):
            raise PatchError("listed patch changes other files than its targets: " + entry["file"])
        _run(PATCH_GIT + [strip, "--check", str(patch)], tree, env)
        _run(PATCH_GIT + [strip, str(patch)], tree, env)
        receipts.append({"file": entry["file"], "sha256": entry["sha256"], "strip": entry["strip"], "targets": dict(entry["targets"]),
                         "after": {relative: git_blob(tree / relative) for relative in sorted(entry["targets"])}})
    return receipts


def check_source(component, source, fixture=False):
    pinned = pins()
    if component not in pinned:
        raise PatchError("component has no reviewed patch")
    source = Path(source).resolve(strict=True)
    expected = json.loads((HERE / "patches/target-hashes.json").read_text(encoding="utf-8"))[component]
    if not fixture:
        if _run(["git", "rev-parse", "HEAD"], source) != pinned[component]:
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
        result = {"component": component, "upstream_commit": pins()[component],
                  "patch_sha256": digest(patch), "target_hashes": expected,
                  "source_fixture_only": fixture, "release_ready": False,
                  "limits": "Source application checked; full vendor compile/native TX audit and hardware acceptance are separate."}
        (destination / "SRRX-PATCH-RECEIPT.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    except Exception:
        # Retain failed output for review; it is never silently treated as good.
        raise


def check_fixtures():
    """Every reviewed patch that has an exact upstream fixture (upstream-fixtures/) applies to a
    copy of it; a component without a fixture is checked from its locked archive by the builder."""
    results = []
    with tempfile.TemporaryDirectory(prefix="srrx-patch-check-") as temporary:
        for component in pins():
            fixture = HERE / "upstream-fixtures" / FIXTURES.get(component, component)
            if fixture.is_dir():
                results.append(apply_to_copy(component, fixture, Path(temporary) / component, fixture=True))
    return results


def apply_from_archive(component, archive_path, destination):
    """Verified full pinned archive can be used offline without .git history."""
    lock = json.loads((HERE / "sources.lock.json").read_text(encoding="utf-8"))
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
    parser.add_argument("--component", choices=pins())
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
