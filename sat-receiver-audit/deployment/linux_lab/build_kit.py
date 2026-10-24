#!/usr/bin/env python3
"""Build a relocatable, offline ARM64 Linux lab tar.zst from verified local inputs.

No downloads, package installation, VM boot or existing-directory replacement.
The supplied final project ZIP determines every image/wheel/guest-package lock.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import errno
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile

PROJECT = Path(__file__).resolve().parents[2]
PREFIX = "SR-RX-Linux-Lab"

LAUNCHER = r'''#!/usr/bin/env python3
"""Verify and run the bundled offline generic ARM64 Linux lab."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
import zipfile

KIT = Path(__file__).resolve().parent

def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()

def safe_name(value):
    p = PurePosixPath(value)
    if not value or "\\" in value or "\0" in value or p.is_absolute() or ".." in p.parts:
        raise ValueError("Unsafe payload path: " + value)
    return p

def verify():
    manifest = json.loads((KIT / "kit-manifest.json").read_text())
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported kit manifest")
    for name in manifest.get("directories", []):
        path = KIT / safe_name(name)
        if not stat.S_ISDIR(path.lstat().st_mode) or not path.resolve(strict=True).is_relative_to(KIT):
            raise ValueError("Payload directory missing or unsafe: " + name)
    seen = set()
    for record in manifest["files"]:
        relative = safe_name(record["path"])
        if record["path"] in seen:
            raise ValueError("Duplicate kit manifest path")
        seen.add(record["path"])
        path = KIT / relative
        if not path.parent.resolve().is_relative_to(KIT):
            raise ValueError("Payload parent escapes kit")
        info = path.lstat()
        if record["type"] == "symlink":
            if not stat.S_ISLNK(info.st_mode) or os.readlink(path) != record["target"]:
                raise ValueError("Symlink mismatch: " + str(relative))
            if not path.resolve(strict=True).is_relative_to(KIT / "tools" / "root"):
                raise ValueError("Runtime symlink escapes tools/root")
            actual = hashlib.sha256(os.fsencode(os.readlink(path))).hexdigest()
        elif record["type"] == "file":
            if not stat.S_ISREG(info.st_mode) or info.st_size != record["bytes"]:
                raise ValueError("Payload type/size mismatch: " + str(relative))
            actual = digest(path)
        else:
            raise ValueError("Unsupported payload type")
        if actual != record["sha256"]:
            raise ValueError("Payload SHA256 mismatch: " + str(relative))
        if record["type"] == "file" and stat.S_IMODE(info.st_mode) != record["mode"]:
            raise ValueError("Payload mode mismatch: " + str(relative))
    actual = {p.relative_to(KIT).as_posix() for p in KIT.rglob("*")
              if p.is_symlink() or p.is_file()}
    if actual != seen | {"kit-manifest.json"}:
        raise ValueError("Unexpected or missing payload files")
    print("Verified", len(seen), "payload files/symlinks", flush=True)
    return manifest

def extract_project(archive, destination, root):
    destination.mkdir()
    with zipfile.ZipFile(archive) as source:
        seen = set()
        for item in source.infolist():
            relative = safe_name(item.filename)
            if relative.parts[0] != root or item.filename in seen:
                raise ValueError("Unexpected project ZIP root/duplicate")
            seen.add(item.filename)
            mode = item.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError("Project ZIP symlinks are not permitted")
            target = destination / relative
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if mode and stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                raise ValueError("Project ZIP special file is not permitted")
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open(item) as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer, 1024 * 1024)
            target.chmod(0o755 if mode & 0o111 else 0o644)
    return destination / root

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path,
                        default=Path("/tmp") / ("srrx-linux-lab-" + uuid.uuid4().hex[:12]),
                        help="New workspace outside the kit (default: a new /tmp/srrx-linux-lab-* path); no spaces or commas")
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--prepare-only", action="store_true", help="Verify inputs and create disks/ISOs without booting")
    operation.add_argument("--verify-only", action="store_true", help="Only verify all kit payload hashes, modes and symlinks")
    parser.add_argument("--timeout", type=int, default=3600, help="Guest time limit in seconds (default: 3600)")
    args = parser.parse_args()
    manifest = verify()
    if args.verify_only:
        return 0
    if sys.version_info < (3, 10) or platform.system() != "Linux" or platform.machine() not in ("x86_64", "amd64"):
        parser.error("Requires Linux x86_64 and Python 3.10 or newer")
    if args.timeout < 1:
        parser.error("--timeout must be positive")
    for name in ("gpgv", "mke2fs", "debugfs"):
        if not shutil.which(name):
            parser.error("Required existing host utility missing: " + name)
    work = args.work.expanduser().resolve()
    if work.exists() or args.work.is_symlink() or work.is_relative_to(KIT):
        parser.error("--work must be a new directory outside the kit")
    if any(c.isspace() or c == "," for c in str(work)) or "," in str(KIT):
        parser.error("Work paths must have no whitespace/commas; kit paths must have no commas")
    work.mkdir(parents=True, mode=0o700, exist_ok=False)
    project = extract_project(KIT / "project" / "SR-RX-v2-project.zip", work / "project", manifest["project_zip_root"])
    # Copy inputs into the new workspace: host.prepare resolves and constrains
    # every Ubuntu path to this assets directory. No kit bytes are modified.
    assets = work / "assets"
    shutil.copytree(KIT / "assets", assets)
    source = json.loads((assets / "ubuntu-assets.json").read_text())
    for item in source["assets"]:
        item["file"] = str(assets / safe_name(item["file"]))
    (assets / "ubuntu-assets.json").write_text(json.dumps(source, indent=2) + "\n")
    host = project / "deployment" / "linux_lab" / "host.py"
    command = [sys.executable, "-B", str(host), "prepare", "--assets", str(assets), "--work", str(work / "vm"),
               "--keyring", str(KIT / "trust" / "ubuntu-cloudimage-keyring.gpg")]
    for flag, program in (("qemu", "qemu-system-aarch64"), ("qemu-img", "qemu-img"), ("genisoimage", "genisoimage")):
        command.extend(["--" + flag, str(KIT / "tools" / "bin" / program)])
    subprocess.run(command, check=True)
    print("Prepared:", work / "vm", flush=True)
    if args.prepare_only:
        print("No guest boot performed. To run: ", sys.executable, "-B", host, "run --work", work / "vm", "--timeout", args.timeout)
        return 0
    return subprocess.run([sys.executable, "-B", str(host), "run", "--work", str(work / "vm"), "--timeout", str(args.timeout)], check=False).returncode

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        print("Offline lab failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
'''

README = """# Offline SR-RX ARM64 Linux lab

This kit contains the pinned Ubuntu 24.04 ARM64 base image, direct-boot kernel
and initrd, 23 Python wheels, 82 guest packages, isolated x86_64 QEMU/ISO runtime,
the public Ubuntu cloud-image keyring, and the complete final project ZIP.
All payload files and symlink targets are recorded in `kit-manifest.json`.
No cache directories, APT indexes, VM overlay, user credentials or prior VM
results are included as runnable inputs. Project reports are retained in its ZIP.

On an existing Linux x86_64 machine with Python 3.10+, `/bin/sh`, `gpgv`,
`mke2fs` and `debugfs` available, extract using GNU tar with zstd support:

```sh
tar --no-same-owner --same-permissions --zstd -xf SR-RX-Linux-Lab.tar.zst
python3 SR-RX-Linux-Lab/launch.py --verify-only
python3 SR-RX-Linux-Lab/launch.py --work /tmp/srrx-lab-example --prepare-only
```

Omit `--prepare-only` to prepare and boot the guest with a 3600-second limit.
Omit `--work` to use a new `/tmp/srrx-linux-lab-*` directory. Keep live VM
workspaces under `/tmp` or another ordinary local filesystem, outside a synced
folder; automatic syncing can copy each changing large virtual disk repeatedly.
The work directory must not already exist and must be outside this kit; its
absolute path must contain no whitespace or commas. The extracted kit path
must contain no commas. Nothing is installed on the host and no download is
attempted. Existing host utilities are prerequisites; this launcher does not
install them. Keep several GB free for copied assets, ISO payload and disks;
QEMU uses 3 GB RAM plus host/emulator overhead and four emulated CPUs.

The launcher verifies the complete payload, extracts a new project, copies
assets into the new workspace, rewrites only that copy's local Ubuntu paths,
then calls the bundled `deployment/linux_lab/host.py prepare` and `run`.
The guest has no network device, shared host directory or hardware passthrough.
It starts from the pinned base image, without an existing writable VM overlay.
Inspect `WORK/vm/report.json`, `console.log` and `results/` after the run.
For a prepared-only VM, the launcher prints the exact command for a later run.

This is generic QEMU ARM64 Linux, not Q6A peripheral, GPU/NPU, electrical,
analog RF, USB silicon, power-safety or physical-module qualification.
The included public keyring comes from the builder's trusted distribution
keyring. The manifest detects corruption; verify the delivered archive SHA256
through the same trusted channel as the project before using the kit.
"""


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    if not name or "\\" in name or "\0" in name or path.is_absolute() or ".." in path.parts:
        raise ValueError("Unsafe archive path: " + name)
    return path


@dataclass
class Entry:
    name: str
    source: Path | None = None
    data: bytes | None = None
    mode: int = 0o644
    target: str | None = None
    expected_sha256: str | None = None
    expected_bytes: int | None = None

    def record(self):
        if self.target is not None:
            return {"path": self.name, "type": "symlink", "target": self.target,
                    "sha256": hashlib.sha256(os.fsencode(self.target)).hexdigest()}
        size = self.source.stat().st_size if self.source else len(self.data)
        hashed = digest(self.source) if self.source else hashlib.sha256(self.data).hexdigest()
        if self.expected_sha256 is not None and (hashed != self.expected_sha256 or size != self.expected_bytes):
            raise ValueError("Input changed after lock validation: " + self.name)
        return {"path": self.name, "type": "file", "bytes": size, "sha256": hashed, "mode": self.mode}


def locked_file(path, record, size_key="bytes"):
    if not path.is_file() or path.is_symlink() or path.stat().st_size != record[size_key] or digest(path) != record["sha256"]:
        raise ValueError("Locked file mismatch: " + str(path))
    return path


def fetch_tools():
    spec = importlib.util.spec_from_file_location("srrx_fetch_tools", Path(__file__).with_name("fetch_tools.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runtime_tree(root):
    """Relative path -> type, content hash/link target and executable bit."""
    tree = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            tree[relative] = ("symlink", os.readlink(path))
        elif path.is_file():
            tree[relative] = ("file", digest(path), path.stat().st_size, bool(path.stat().st_mode & 0o111))
        else:
            tree[relative] = ("directory",) if path.is_dir() else ("special",)
    return tree


def check_runtime(tools, packages):
    """tools/root must equal a fresh lock-ordered unpack of the hash-locked
    debs (fetch_tools.py procedure); tools/bin must be its exact wrappers."""
    helper = fetch_tools()
    for record in packages:
        if safe_name(record["filename"]).name != record["filename"]:
            raise ValueError("Unsafe locked host package name")
        locked_file(tools / "debs" / record["filename"], record)
    with tempfile.TemporaryDirectory(prefix="srrx-kit-runtime-") as temporary:
        try:
            helper.unpack(tools / "debs", packages, Path(temporary))
        except RuntimeError as error:
            raise ValueError(str(error)) from error
        expected = runtime_tree(Path(temporary))
    actual = runtime_tree(tools / "root")
    changed = sorted(name for name in set(actual) | set(expected) if actual.get(name) != expected.get(name))
    if changed:
        raise ValueError("tools/root differs from the locked host debs: " + ", ".join(changed[:10]))
    wrappers = helper.wrapper_texts()
    if {p.name for p in (tools / "bin").iterdir()} != set(wrappers) or any(
            (tools / "bin" / name).is_symlink() or (tools / "bin" / name).read_text() != text for name, text in wrappers.items()):
        raise ValueError("tools/bin differs from the fetch_tools.py wrappers")
    return expected


def project_locks(path):
    with zipfile.ZipFile(path) as archive:
        seen = set()
        for item in archive.infolist():
            safe_name(item.filename)
            mode = item.external_attr >> 16
            if item.filename in seen or stat.S_ISLNK(mode):
                raise ValueError("Project ZIP has duplicates or symlinks")
            if not item.is_dir() and stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                raise ValueError("Project ZIP has a special file")
            seen.add(item.filename)
        candidates = [n[:-len("/deployment/linux_lab/host.py")] for n in seen if n.endswith("/deployment/linux_lab/host.py")]
        if len(candidates) != 1 or "/" in candidates[0]:
            raise ValueError("Project ZIP must contain one project root with linux_lab/host.py")
        root = candidates[0]
        if any(PurePosixPath(n).parts[0] != root for n in seen):
            raise ValueError("Project ZIP has unexpected top-level paths")
        bad = archive.testzip()
        if bad:
            raise ValueError("Project ZIP CRC failed: " + bad)
        names = ("assets.lock.json", "wheelhouse-manifest.json", "wheelhouse-requirements.txt", "guest-packages.lock.json", "host-packages.lock.json")
        raw = {n: archive.read(root + "/deployment/linux_lab/" + n) for n in names}
    return root, raw


def assemble(args):
    assets, tools, keyring, project_zip = [p.expanduser().resolve(strict=True) for p in
                                          (args.assets, args.tools, args.keyring, args.project_zip)]
    project_sha, project_size = digest(project_zip), project_zip.stat().st_size
    project_root, raw = project_locks(project_zip)
    locks = {name: json.loads(data) for name, data in raw.items() if name.endswith(".json")}
    images = locks["assets.lock.json"]
    wheels = locks["wheelhouse-manifest.json"]
    guest = locks["guest-packages.lock.json"]
    host = locks["host-packages.lock.json"]
    if len(images["ubuntu_assets"]) != 3 or len(wheels["wheels"]) != 23 or len(guest["packages"]) != 82 or len(host["packages"]) != 87:
        raise ValueError("Unexpected locked input counts; expected 3 Ubuntu assets, 23 wheels, 82 guest and 87 host packages")
    entries = [Entry("launch.py", data=LAUNCHER.encode(), mode=0o755), Entry("README.md", data=README.encode()),
               Entry("project/SR-RX-v2-project.zip", source=project_zip, expected_sha256=project_sha, expected_bytes=project_size),
               Entry("trust/ubuntu-cloudimage-keyring.gpg", source=keyring)]
    signed = {}
    for directory in ("ubuntu", "unpacked"):
        folder = assets / directory
        subprocess.run(["gpgv", "--keyring", str(keyring), str(folder / "SHA256SUMS.gpg"), str(folder / "SHA256SUMS")], check=True)
        signed[directory] = {line.split(maxsplit=1)[1].lstrip("*"): line.split()[0]
                             for line in (folder / "SHA256SUMS").read_text().splitlines() if line.strip()}
        entries.extend(Entry("assets/" + directory + "/" + name, source=folder / name) for name in ("SHA256SUMS", "SHA256SUMS.gpg"))
    local = []
    for record in images["ubuntu_assets"]:
        name = record["name"]
        if safe_name(name).name != name:
            raise ValueError("Unsafe locked image name")
        directory = "ubuntu" if name.endswith(".img") else "unpacked"
        if signed[directory].get(name) != record["sha256"]:
            raise ValueError("Image lock differs from signed Ubuntu checksums")
        entries.append(Entry("assets/" + directory + "/" + name, source=locked_file(assets / directory / name, record),
                             expected_sha256=record["sha256"], expected_bytes=record["bytes"]))
        local.append({**record, "file": directory + "/" + name, "expected_sha256": record["sha256"]})
    entries.append(Entry("assets/ubuntu-assets.json", data=(json.dumps({"image_release": images["image_release"], "assets": local}, indent=2) + "\n").encode()))
    manifest_name = "ubuntu-24.04-server-cloudimg-arm64.manifest"
    manifest_path = assets / "ubuntu" / manifest_name
    if digest(manifest_path) != guest["guest_manifest_sha256"] or signed["ubuntu"].get(manifest_name) != guest["guest_manifest_sha256"]:
        raise ValueError("Guest package-state manifest differs from signed Ubuntu metadata")
    entries.append(Entry("assets/ubuntu/" + manifest_name, source=manifest_path,
                         expected_sha256=guest["guest_manifest_sha256"], expected_bytes=manifest_path.stat().st_size))
    for directory, records, size_key, name_key in (("wheels", wheels["wheels"], "size_bytes", "filename"),
                                                   ("debs", guest["packages"], "bytes", "filename")):
        for record in records:
            name = record[name_key]
            if safe_name(name).name != name:
                raise ValueError("Unsafe locked dependency name")
            entries.append(Entry("assets/" + directory + "/" + name, source=locked_file(assets / directory / name, record, size_key),
                                 expected_sha256=record["sha256"], expected_bytes=record[size_key]))
    for name in ("wheelhouse-manifest.json", "wheelhouse-requirements.txt"):
        entries.append(Entry("assets/" + name, data=raw[name]))
    for name, data in raw.items():
        entries.append(Entry("locks/" + name, data=data))
    entries.append(Entry("tools/host-packages.lock.json", data=raw["host-packages.lock.json"]))
    if (tools / "host-packages.lock.json").read_bytes() != raw["host-packages.lock.json"]:
        raise ValueError("Tools directory was not fetched for the project host lock")
    # Bind the shipped bytes to the hash-locked debs, not to self-declared JSON.
    tree = check_runtime(tools, host["packages"])
    runtime = tools / "root"
    runtime_directories = []
    for directory in (tools / "bin", runtime):
        for path in sorted(directory.rglob("*")):
            relative = path.relative_to(tools).as_posix()
            if path.is_symlink():
                target = os.readlink(path)
                if Path(target).is_absolute() or not path.resolve(strict=True).is_relative_to(runtime):
                    raise ValueError("Nonportable runtime symlink: " + relative)
                entries.append(Entry("tools/" + relative, target=target))
            elif path.is_file():
                known = tree.get(path.relative_to(runtime).as_posix()) if directory == runtime else None
                entries.append(Entry("tools/" + relative, source=path, mode=0o755 if path.stat().st_mode & 0o111 else 0o644,
                                     expected_sha256=known and known[1], expected_bytes=known and known[2]))
            elif path.is_dir():
                runtime_directories.append("tools/" + relative)
            else:
                raise ValueError("Special runtime file: " + relative)
    for name in ("qemu-system-aarch64", "qemu-img", "genisoimage"):
        subprocess.run([str(tools / "bin" / name), "--version"], stdout=subprocess.DEVNULL, check=True)
    entries.sort(key=lambda x: x.name)
    records = [entry.record() for entry in entries]
    if len({r["path"] for r in records}) != len(records):
        raise ValueError("Duplicate kit payload path")
    manifest = {"schema_version": 1, "purpose": "offline generic ARM64 Linux tests; no physical hardware qualification",
                "project_zip_root": project_root, "image_release": images["image_release"],
                "locked_counts": {"ubuntu_assets": 3, "wheels": 23, "guest_packages": 82, "host_packages": 87},
                "manifest_self_excluded": True, "files": records,
                "directories": sorted(runtime_directories)}
    entries.append(Entry("kit-manifest.json", data=(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()))
    return entries, manifest


def planned_directories(names, extra):
    directories = {PREFIX}
    for name in list(names) + list(extra):
        parent = PurePosixPath(PREFIX, safe_name(name)).parent
        if name in extra:
            directories.add(str(PurePosixPath(PREFIX, safe_name(name))))
        while str(parent) != ".":
            directories.add(str(parent))
            parent = parent.parent
    return directories


def archive(entries, destination, level, extra_directories=()):
    # tar and zstd both stream; the large image/wheelhouse is never buffered.
    with destination.open("xb") as output:
        compressor = subprocess.Popen(["zstd", "--quiet", "-T1", "-" + str(level), "-c"], stdin=subprocess.PIPE, stdout=output)
        try:
            with tarfile.open(fileobj=compressor.stdin, mode="w|", format=tarfile.PAX_FORMAT) as tar:
                directories = planned_directories([entry.name for entry in entries], extra_directories)
                for name in sorted(directories):
                    info = tarfile.TarInfo(name); info.type = tarfile.DIRTYPE; info.mode = 0o755; tar.addfile(info)
                for entry in entries:
                    info = tarfile.TarInfo(PREFIX + "/" + entry.name)
                    info.mode = entry.mode
                    if entry.target is not None:
                        info.type = tarfile.SYMTYPE; info.linkname = entry.target; tar.addfile(info)
                    elif entry.source:
                        info.size = entry.source.stat().st_size
                        with entry.source.open("rb") as source:
                            tar.addfile(info, source)
                    else:
                        info.size = len(entry.data); tar.addfile(info, io.BytesIO(entry.data))
        finally:
            compressor.stdin.close()
            code = compressor.wait()
        if code:
            raise RuntimeError("zstd compression failed")
        output.flush(); os.fsync(output.fileno())


def check_archive(path, manifest):
    expected = {PREFIX + "/" + item["path"]: item for item in manifest["files"]}
    seen = set()
    expected_directories = planned_directories(
        [item["path"] for item in manifest["files"]] + ["kit-manifest.json"], manifest.get("directories", []))
    seen_directories = set()
    decompressor = subprocess.Popen(["zstd", "--quiet", "-d", "-c", str(path)], stdout=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=decompressor.stdout, mode="r|") as tar:
            for item in tar:
                if item.isdir():
                    if item.name not in expected_directories or item.name in seen_directories or item.mode != 0o755:
                        raise ValueError("Unexpected, duplicate or invalid archive directory")
                    seen_directories.add(item.name)
                    continue
                if item.name in seen:
                    raise ValueError("Duplicate output archive member")
                seen.add(item.name)
                if item.name == PREFIX + "/kit-manifest.json":
                    if json.load(tar.extractfile(item)) != manifest:
                        raise ValueError("Archived manifest mismatch")
                    continue
                record = expected[item.name]
                if record["type"] == "symlink":
                    if not item.issym() or item.linkname != record["target"]:
                        raise ValueError("Archived symlink mismatch")
                else:
                    if not item.isfile() or item.size != record["bytes"] or item.mode != record["mode"]:
                        raise ValueError("Archived file metadata mismatch")
                    value = hashlib.sha256()
                    with tar.extractfile(item) as source:
                        for block in iter(lambda: source.read(1024 * 1024), b""):
                            value.update(block)
                    if value.hexdigest() != record["sha256"]:
                        raise ValueError("Archived payload hash mismatch: " + item.name)
        # Consume padding/frame trailer so zstd validates the complete frame.
        while decompressor.stdout.read(1024 * 1024):
            pass
    finally:
        decompressor.stdout.close(); code = decompressor.wait()
    if code or seen != set(expected) | {PREFIX + "/kit-manifest.json"} or seen_directories != expected_directories:
        raise ValueError("Incomplete compressed kit archive")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True, help="Existing fetch_assets.py image/manifest/wheel/deb cache")
    parser.add_argument("--tools", type=Path, required=True, help="Existing fetch_tools.py output with debs/, root/, bin/ and host-packages.lock.json")
    parser.add_argument("--project-zip", type=Path, required=True, help="Final full project ZIP; its locks select all payload inputs")
    parser.add_argument("--output", type=Path, required=True, help="New .tar.zst path outside the source checkout")
    parser.add_argument("--keyring", type=Path, default=Path("/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg"))
    parser.add_argument("--level", type=int, default=3, choices=range(1, 10), help="Single-threaded zstd compression level (default: 3)")
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.exists() or args.output.is_symlink() or output.is_relative_to(PROJECT):
        parser.error("--output must be a new path outside the source checkout")
    if not output.name.endswith(".tar.zst"):
        parser.error("--output must end with .tar.zst")
    if not output.parent.is_dir():
        parser.error("--output parent directory must already exist")
    for utility in ("gpgv", "zstd", "dpkg-deb", "tar"):
        if not shutil.which(utility):
            parser.error("Missing existing builder utility: " + utility)
    print("Validating signed/locked inputs and recording runtime files...", flush=True)
    entries, manifest = assemble(args)
    # Keep the changing large archive off synced project/workspace storage.
    # Publication exposes only a completely checked, fsynced archive.
    handle, temporary = tempfile.mkstemp(prefix="srrx-offline-kit-", suffix=".tar.zst", dir="/tmp")
    os.close(handle); Path(temporary).unlink()
    try:
        print("Streaming archive under /tmp with zstd -T1 -" + str(args.level) + "...", flush=True)
        archive(entries, Path(temporary), args.level, manifest["directories"])
        print("Checking every compressed archive payload hash...", flush=True)
        check_archive(Path(temporary), manifest)
        # Link publication refuses to overwrite an output created concurrently.
        try:
            os.link(temporary, output)
        except OSError as error:
            if error.errno != errno.EXDEV:
                raise
            fd, staging = tempfile.mkstemp(prefix="srrx-kit-publish-", dir=output.parent)
            try:
                with os.fdopen(fd, "wb") as target, Path(temporary).open("rb") as source:
                    shutil.copyfileobj(source, target, 1024 * 1024)
                    target.flush(); os.fsync(target.fileno())
                if digest(staging) != digest(temporary):
                    raise ValueError("Cross-filesystem archive copy mismatch")
                os.link(staging, output)
            finally:
                Path(staging).unlink(missing_ok=True)
        directory = os.open(output.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        print(json.dumps({"status": "PASS", "archive": str(output), "bytes": output.stat().st_size,
                          "sha256": digest(output), "payload_entries": len(manifest["files"]),
                          "locked_counts": manifest["locked_counts"], "guest_boot_performed": False}, indent=2))
    finally:
        Path(temporary).unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        print("Offline kit build failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
