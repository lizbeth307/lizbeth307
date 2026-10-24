#!/usr/bin/env python3
"""Fetch the pinned bytes of deployment/sources.lock.json into an offline cache, streaming.

Every download is hashed while it is written, in 1 MiB chunks, and is moved into place only
after its SHA-256 and size match the lock; a locked entry can never grow past its locked size.
There is no fixed size cap (the old 128 MiB acquisition cap left SDRangel unresolved):
`acquire`, for a not yet locked archive, is bounded only by --max-bytes. Nothing here edits the
lock: a reviewer copies acquired or resolved values into it.

Ubuntu packages are pinned only through a fixed snapshot.ubuntu.com timestamp (lock
apt_snapshot): gpgv checks InRelease against an explicit keyring and the pinned fingerprint
(deploy.gpgv_signed_text), the signed SHA256 list checks the Sources/Packages index, and the
index checks every .dsc, tarball and .deb. `resolve-debian` prints that record for a component;
`verify-debian` derives it again and fails on any difference from the lock.
No step installs, extracts or runs a downloaded file.
"""
import argparse
import hashlib
import http.client
import json
import lzma
import os
import re
from pathlib import Path
import sys
import tarfile
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import deploy  # noqa: E402  (one cache entry list, one gpgv/deb822 reader)

CHUNK = 1024 * 1024
USER_AGENT = "srrx-fetch-sources/1 (SR-RX-v2.1 offline cache)"
TRANSIENT = (URLError, TimeoutError, ConnectionError, http.client.HTTPException)


class FetchError(ValueError):
    pass


def download(url, path, sha256=None, size=None, max_bytes=None, attempts=3):
    """Stream url into path. With sha256/size the bytes must match exactly; without them
    (acquisition) they are measured. Returns {sha256, size, md5, cached}."""
    path = Path(path)
    if sha256 is not None and path.is_file() and not path.is_symlink() and path.stat().st_size == size and deploy.sha(path) == sha256:
        return {"sha256": sha256, "size": size, "md5": None, "cached": True}
    limit = size if size is not None else max_bytes
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, attempts + 1):
        fd, temporary = tempfile.mkstemp(prefix=".srrx-fetch-", dir=path.parent)
        try:
            value, md5, total = hashlib.sha256(), hashlib.md5(usedforsecurity=False), 0
            with os.fdopen(fd, "wb") as target, urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as source:
                for chunk in iter(lambda: source.read(CHUNK), b""):
                    total += len(chunk)
                    if limit is not None and total > limit:
                        raise FetchError("download exceeds the " + ("locked size" if size is not None else "--max-bytes bound") + ": " + url)
                    value.update(chunk)
                    md5.update(chunk)
                    target.write(chunk)
            if sha256 is not None and (value.hexdigest() != sha256 or total != size):
                raise FetchError("downloaded bytes differ from the lock: " + url)
            os.replace(temporary, path)
            return {"sha256": value.hexdigest(), "size": total, "md5": md5.hexdigest(), "cached": False}
        except TRANSIENT as exc:
            if attempt == attempts:
                raise FetchError("download failed after " + str(attempts) + " attempts: " + url + ": " + str(exc)) from exc
            time.sleep(5 * attempt)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    raise FetchError("unreachable")


def _safe_cache(root, relative):
    relative = Path(relative)
    target = (root / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or not target.is_relative_to(root):
        raise FetchError("unsafe cache path: " + str(relative))
    return target


def fetch(cache, components=None, include_core=True, lock=None):
    lock = lock or deploy.load(HERE / "sources.lock.json")
    unresolved = sorted(c["id"] for c in lock["components"] if c["source_archive_sha256"] is None)
    if components is None:
        components = [c["id"] for c in lock["components"] if c["source_archive_sha256"] is not None]
    blocked = sorted(set(components) & set(unresolved))
    if blocked:
        raise FetchError("source archive SHA256 unresolved: " + ", ".join(blocked))
    root = Path(cache).resolve()
    root.mkdir(parents=True, exist_ok=True)
    total = fetched = 0
    entries = deploy.cache_entries(lock, components, include_core)
    for item in entries:
        if not item.get("url"):
            raise FetchError("lock entry has no URL: " + item["path"])
        result = download(item["url"], _safe_cache(root, item["path"]), item["sha256"], item["size"])
        total += result["size"]
        fetched += not result["cached"]
        print(("cached " if result["cached"] else "fetched ") + item["path"], flush=True)
    return {"status": "FETCHED_AND_VERIFIED", "entries": len(entries), "downloaded": fetched, "bytes": total,
            "components": sorted(components), "includes_core": include_core, "unresolved_in_lock": unresolved,
            "hardware_ready": False}


def git_tree_sha1(archive, gitlinks=None):
    """Git tree id of the single root of a `git archive` tarball (GitHub /archive/<commit>.tar.gz).

    The archive SHA-256 pins the compressed bytes, which GitHub once changed (2023); a tree id
    that matches the commit's tree (GitHub git/commits API) identifies the same content for a
    re-review. A submodule is an empty directory in the archive: gitlinks {path: commit} (lock
    git_submodules) restores its 160000 entry. Any other empty directory and export-ignore/
    export-subst attributes make the id differ: then it is no identity and is not recorded."""
    gitlinks = dict(gitlinks or {})
    tree, root = {"": {}}, None
    with tarfile.open(archive, "r:gz") as stream:
        for member in stream:
            parts = member.name.rstrip("/").split("/")
            if root is None:
                root = parts[0]
            if parts[0] != root or ".." in parts:
                raise FetchError("archive is not one safe root")
            relative = "/".join(parts[1:])
            if not relative:
                continue
            parent, _, name = relative.rpartition("/")
            if member.isdir():
                tree.setdefault(relative, {})
                tree.setdefault(parent, {})[name] = ("40000", relative)
                continue
            if member.issym():
                data, mode = member.linkname.encode(), "120000"
            elif member.isfile():
                data, mode = stream.extractfile(member).read(), ("100755" if member.mode & 0o111 else "100644")
            else:
                raise FetchError("archive member is neither file, directory nor symlink: " + member.name)
            tree.setdefault(parent, {})[name] = (mode, hashlib.sha1(b"blob %d\0" % len(data) + data).digest())

    def object_id(directory):
        entries = []
        for name, (mode, value) in tree.get(directory, {}).items():
            if mode == "40000" and not tree.get(value):
                if value not in gitlinks:
                    raise FetchError("empty directory without a locked gitlink: " + value)
                mode, value = "160000", bytes.fromhex(gitlinks.pop(value))
            elif mode == "40000":
                value = object_id(value)
            entries.append((name + "/" if mode == "40000" else name, mode, name, value))
        body = b"".join(mode.encode() + b" " + name.encode() + b"\0" + value for _, mode, name, value in sorted(entries))
        return hashlib.sha1(b"tree %d\0" % len(body) + body).digest()
    identity = object_id("").hex()
    if gitlinks:
        raise FetchError("locked gitlink is not an empty directory of the archive: " + sorted(gitlinks)[0])
    return identity


def verify_trees(cache, components=None, lock=None):
    """Recompute git_tree_sha1 of fetched archives (fetch first: their SHA-256 is checked there)."""
    lock = lock or deploy.load(HERE / "sources.lock.json")
    selected = [c for c in lock["components"] if c.get("git_tree_sha1") and (components is None or c["id"] in components)]
    if components is not None and {c["id"] for c in selected} != set(components):
        raise FetchError("component has no recorded git_tree_sha1")
    root = Path(cache).resolve(strict=True)
    for component in selected:
        if git_tree_sha1(_safe_cache(root, component["source_cache_path"]), component.get("git_submodules")) != component["git_tree_sha1"]:
            raise FetchError("archive content differs from the locked git tree: " + component["id"])
    return {"status": "ARCHIVE_TREES_MATCH_LOCKED_COMMITS", "components": [c["id"] for c in selected], "hardware_ready": False}


def member_tree_sha1(archive, member, gitlinks=None):
    """git_tree_sha1 of a tarball nested in another (WSJT-X superbuild src/wsjtx.tgz)."""
    with tarfile.open(archive, "r:gz") as outer, tempfile.TemporaryDirectory(prefix="srrx-member-") as temporary:
        inner = Path(temporary) / "member.tar.gz"
        with outer.extractfile(member) as source, inner.open("wb") as target:
            for chunk in iter(lambda: source.read(CHUNK), b""):
                target.write(chunk)
        return git_tree_sha1(inner, gitlinks)


# --- Ubuntu snapshot pins ---------------------------------------------------------------

def _snapshot_get(snapshot, relative, directory, sha256=None, size=None):
    name = relative.replace("/", "_")
    return download(snapshot["archive"] + "/" + snapshot["timestamp"] + "/" + relative, Path(directory) / name, sha256, size), Path(directory) / name


def signed_release(snapshot, suite, keyring, directory):
    """(InRelease record, {path: (sha256, size)}) of one suite, after gpgv by the pinned key."""
    result, path = _snapshot_get(snapshot, "dists/" + suite + "/InRelease", directory)
    paragraphs = deploy.deb822(deploy.gpgv_signed_text(path, keyring, snapshot["signing_fingerprints"]), suite + " InRelease")
    if len(paragraphs) != 1 or paragraphs[0].get("codename") != "noble" or paragraphs[0].get("suite") != suite:
        raise FetchError("unexpected InRelease for " + suite)
    return {"suite": suite, "inrelease_sha256": result["sha256"], "size": result["size"]}, deploy.release_files(paragraphs[0], suite)


def index(snapshot, suite, relative, files, directory):
    """Decompressed text of a signed index (.xz), with its record."""
    if relative not in files:
        raise FetchError("signed Release does not list " + suite + "/" + relative)
    digest, size = files[relative]
    _, path = _snapshot_get(snapshot, "dists/" + suite + "/" + relative, directory, digest, size)
    return {"suite": suite, "path": relative, "sha256": digest, "size": size}, lzma.decompress(path.read_bytes()).decode("utf-8")


def _checksums(field, label):
    out = []
    for line in field.split("\n"):
        if line.strip():
            digest, size, name = line.split()
            if "/" in name or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise FetchError("malformed Checksums-Sha256 in " + label)
            out.append({"name": name, "sha256": digest, "size": int(size)})
    return out


def resolve_debian(lock, component_id, keyring, directory):
    """debian_source + binary_debs (+ the signed records used) for one locked Ubuntu version."""
    snapshot = lock["apt_snapshot"]
    component = next(c for c in lock["components"] if c["id"] == component_id)
    package = (component.get("debian_source") or {}).get("package", component_id)
    releases, indices = [], []
    for suite in snapshot["suites"]:
        release, files = signed_release(snapshot, suite, keyring, directory)
        found = None
        for area in snapshot["areas"]:
            record, text = index(snapshot, suite, area + "/source/Sources.xz", files, directory)
            for stanza in deploy.deb822(text, suite + " Sources"):
                if stanza.get("package") == package and stanza.get("version") == component["version"]:
                    found = (area, record, stanza)
            if found:
                break
        if not found:
            continue
        area, record, stanza = found
        releases.append(release)
        indices.append(record)
        debs = []
        for binary_area in snapshot["areas"]:
            record, text = index(snapshot, suite, binary_area + "/binary-" + snapshot["architecture"] + "/Packages.xz", files, directory)
            indices.append(record)
            for item in deploy.deb822(text, suite + " Packages"):
                source = item.get("source", item.get("package", "")).split()
                source_version = source[1].strip("()") if len(source) > 1 else item.get("version")
                if source and source[0] == package and source_version == component["version"]:
                    debs.append({"package": item["package"], "version": item["version"], "architecture": item["architecture"],
                                 "filename": item["filename"], "sha256": item["sha256"], "size": int(item["size"])})
        files_ = _checksums(stanza["checksums-sha256"], package)
        dsc = [f for f in files_ if f["name"].endswith(".dsc")]
        if len(dsc) != 1 or not debs:
            raise FetchError("source " + package + " " + component["version"] + " lacks one .dsc or any arm64 binary")
        debian = {"package": package, "suite": suite, "area": area, "directory": stanza["directory"], "files": files_}
        return {"debian_source": debian, "binary_debs": sorted(debs, key=lambda d: d["package"]),
                "source_archive_sha256": dsc[0]["sha256"], "source_cache_path": "sources/" + component_id + "/" + dsc[0]["name"],
                "releases": releases, "indices": indices}
    raise FetchError(package + " " + component["version"] + " is not in the pinned snapshot suites")


def verify_debian(lock, keyring, directory, components=None):
    """Derive every debian_source pin again from the signed snapshot; any difference fails."""
    selected = [c for c in lock["components"] if c.get("debian_source") and (components is None or c["id"] in components)]
    if components is not None and {c["id"] for c in selected} != set(components):
        raise FetchError("component has no debian_source pin")
    recorded_releases = {r["suite"]: r for r in lock["apt_snapshot"]["releases"]}
    recorded_indices = {(r["suite"], r["path"]): r for r in lock["apt_snapshot"]["indices"]}
    for component in selected:
        derived = resolve_debian(lock, component["id"], keyring, directory)
        for key in ("debian_source", "binary_debs", "source_archive_sha256", "source_cache_path"):
            if derived[key] != component[key]:
                raise FetchError("signed snapshot differs from the lock: " + component["id"] + " " + key)
        for release in derived["releases"]:
            if recorded_releases.get(release["suite"]) != release:
                raise FetchError("InRelease differs from the lock: " + release["suite"])
        for record in derived["indices"]:
            if recorded_indices.get((record["suite"], record["path"])) != record:
                raise FetchError("signed index differs from the lock: " + record["suite"] + "/" + record["path"])
    return {"status": "DEBIAN_PINS_MATCH_SIGNED_SNAPSHOT", "components": [c["id"] for c in selected],
            "snapshot": lock["apt_snapshot"]["timestamp"], "hardware_ready": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="operation", required=True)
    get = commands.add_parser("fetch", help="download locked entries into a cache and verify them")
    get.add_argument("--cache", type=Path, required=True)
    get.add_argument("--component", action="append", help="default: every component with a locked hash")
    get.add_argument("--sources-only", action="store_true", help="skip the core image/kernel artifacts")
    get.add_argument("--report", type=Path)
    acquire = commands.add_parser("acquire", help="measure a not yet locked archive (prints, never edits the lock)")
    acquire.add_argument("--url", required=True)
    acquire.add_argument("--output", type=Path, required=True)
    acquire.add_argument("--max-bytes", type=int, default=8 * 1024 ** 3)
    acquire.add_argument("--expect-size", type=int, help="published size to cross-check (e.g. SourceForge file metadata)")
    acquire.add_argument("--expect-md5", help="published MD5 to cross-check; integrity is the SHA-256 recorded from the bytes")
    trees = commands.add_parser("tree", help="git tree id of archives: verify fetched ones, or print one")
    trees.add_argument("--cache", type=Path)
    trees.add_argument("--archive", type=Path)
    trees.add_argument("--member", help="nested tarball inside --archive")
    trees.add_argument("--component", action="append")
    for name in ("resolve-debian", "verify-debian"):
        sub = commands.add_parser(name)
        sub.add_argument("--keyring", type=Path, required=True)
        sub.add_argument("--work", type=Path, required=True, help="new or empty directory for downloaded indices")
        sub.add_argument("--component", action="append", required=name == "resolve-debian")
    args = parser.parse_args()
    try:
        if args.operation == "fetch":
            result = fetch(args.cache, args.component, not args.sources_only)
            if args.report:
                args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        elif args.operation == "acquire":
            if args.output.exists():
                raise FetchError("output exists; acquisition writes a new file")
            measured = download(args.url, args.output, max_bytes=args.max_bytes)
            if (args.expect_size is not None and measured["size"] != args.expect_size) or (args.expect_md5 and measured["md5"] != args.expect_md5.lower()):
                raise FetchError("acquired bytes differ from the published size/MD5")
            result = {"status": "ACQUIRED_NOT_LOCKED", "url": args.url, "sha256": measured["sha256"], "size": measured["size"],
                      "md5": measured["md5"], "acquired_on": time.strftime("%Y-%m-%d", time.gmtime())}
        elif args.operation == "tree":
            if bool(args.cache) == bool(args.archive):
                raise FetchError("give exactly one of --cache and --archive")
            if args.cache:
                result = verify_trees(args.cache, args.component)
            else:
                lock = deploy.load(HERE / "sources.lock.json")
                component = next((c for c in lock["components"] if c["id"] in (args.component or [])), {})
                links = component.get("git_submodules")
                tree = member_tree_sha1(args.archive, args.member, links) if args.member else git_tree_sha1(args.archive, links)
                result = {"git_tree_sha1": tree, "locked": component.get("git_tree_sha1"),
                          "matches_lock": tree == component.get("git_tree_sha1") if component.get("git_tree_sha1") else None}
        else:
            lock = deploy.load(HERE / "sources.lock.json")
            args.work.mkdir(parents=True, exist_ok=True)
            if args.operation == "resolve-debian":
                result = {c: resolve_debian(lock, c, args.keyring, args.work) for c in args.component}
            else:
                result = verify_debian(lock, args.keyring, args.work, args.component)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, KeyError, StopIteration, lzma.LZMAError, tarfile.TarError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
