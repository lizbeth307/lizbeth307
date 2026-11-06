#!/usr/bin/env python3
"""Lay out the QNN HTP runtime /opt/lab/npu/2.42/{lib,dsp} from the locked qcom-qnn-sdk-v68 deb.

Input is either the downloaded deb (whole-file SHA-256 and size checked, then only the
pinned members read from data.tar.xz; nothing executed, no dpkg needed) or an installed
root whose dpkg-installed copies are checked against the same pins. Output is a NEW
directory tree with opt/lab/npu/2.42/..., LAYOUT.json (every copied file with SHA-256,
the excluded set with reasons) and etc/systemd/system/inferd-htp.service.

Licensing: the deb and its files are Qualcomm's. This tool is run by whoever obtained
the deb under its licence, on their own builder or the device; CI runs it on a freshly
downloaded deb and uploads only LAYOUT.json. Nothing here redistributes QAIRT, and the
QAIRT SDK zip is not used at all. Running graphs on the HTP stays hardware-only (Phase 0).
"""
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile

HERE = Path(__file__).resolve().parent
LOCK = HERE / "npu/qnn-layout.lock.json"
UNIT = HERE / "npu/inferd-htp.service"
MAX_DEB = 256 * 1024 * 1024


class LayoutError(ValueError):
    pass


def load_lock(path=LOCK):
    lock = json.loads(Path(path).read_text(encoding="utf-8"))
    if lock.get("schema_version") != 1 or lock.get("kind") != "srrx_qnn_runtime_layout":
        raise LayoutError("unexpected layout lock")
    for source, entry in lock["install"].items():
        dest = PurePosixPath(entry["dest"])
        if dest.is_absolute() or ".." in dest.parts or dest.parts[0] not in ("lib", "dsp", "share"):
            raise LayoutError("unsafe layout destination " + entry["dest"])
        if PurePosixPath(source).is_absolute() or ".." in PurePosixPath(source).parts:
            raise LayoutError("unsafe package path " + source)
    return lock


def _ar_members(data):
    if data[:8] != b"!<arch>\n":
        raise LayoutError("not a Debian package (ar)")
    pos = 8
    while pos + 60 <= len(data):
        header = data[pos:pos + 60]
        name = header[:16].decode("ascii", "replace").strip().rstrip("/")
        size = int(header[48:58].decode("ascii").strip())
        yield name, data[pos + 60:pos + 60 + size]
        pos += 60 + size + (size & 1)


def deb_members(deb, wanted, package):
    """{member path: bytes} for the wanted data.tar members of a verified deb."""
    deb = Path(deb)
    if deb.stat().st_size != package["size"] or deb.stat().st_size > MAX_DEB:
        raise LayoutError("deb size differs from the lock")
    data = deb.read_bytes()
    if hashlib.sha256(data).hexdigest() != package["sha256"]:
        raise LayoutError("deb SHA-256 differs from the lock")
    payload = [body for name, body in _ar_members(data) if name.startswith("data.tar")]
    names = [name for name, body in _ar_members(data) if name.startswith("data.tar")]
    if len(payload) != 1 or names[0] not in ("data.tar.xz", "data.tar"):
        raise LayoutError("unsupported deb payload " + ",".join(names))
    raw = lzma.decompress(payload[0]) if names[0].endswith(".xz") else payload[0]
    found = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        for member in tar.getmembers():
            name = member.name[2:] if member.name.startswith("./") else member.name
            if name in wanted:
                if not member.isfile():
                    raise LayoutError(name + " is not a regular file in the deb")
                found[name] = tar.extractfile(member).read()
    return found


def root_members(root, wanted):
    found = {}
    for name in wanted:
        path = Path(root) / name
        if path.is_symlink() or not path.is_file():
            raise LayoutError("/" + name + " is missing or not a regular file")
        found[name] = path.read_bytes()
    return found


def layout(dest, deb=None, root=None, lock=None):
    if (deb is None) == (root is None):
        raise LayoutError("give exactly one of --deb or --from-root")
    lock = lock or load_lock()
    dest = Path(dest)
    if dest.exists():
        raise LayoutError("destination must be a new directory")
    wanted = set(lock["install"])
    found = deb_members(deb, wanted, lock["package"]) if deb is not None else root_members(root, wanted)
    if set(found) != wanted:
        raise LayoutError("pinned files missing from the input: " + ", ".join(sorted(wanted - set(found))))
    for name, content in found.items():
        entry = lock["install"][name]
        if len(content) != entry["size"] or hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise LayoutError(name + " differs from the locked QAIRT 2.42 runtime")
    prefix = dest / lock["prefix"]
    record = {"schema_version": 1, "kind": "srrx_qnn_runtime_layout_record", "status": "LAID_OUT_NOT_EXECUTED",
              "package": {k: lock["package"][k] for k in ("name", "version", "qairt", "sha256", "size")},
              "source": "deb" if deb is not None else "installed root", "files": {}, "excluded": lock["excluded"],
              "htp_executed": False, "phase0": "OPEN"}
    for name, content in sorted(found.items()):
        target = prefix / lock["install"][name]["dest"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        record["files"][lock["install"][name]["dest"]] = {"sha256": lock["install"][name]["sha256"], "from": name}
    (prefix / "LAYOUT.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    units = dest / "etc/systemd/system"
    units.mkdir(parents=True)
    shutil.copyfile(UNIT, units / UNIT.name)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dest", type=Path, required=True, help="new directory (a staging root)")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--deb", type=Path, help="downloaded qcom-qnn-sdk-v68_0.1.0-2_all.deb")
    source.add_argument("--from-root", type=Path, help="root with the deb already installed (e.g. /)")
    parser.add_argument("--record", type=Path, help="also write LAYOUT.json here (CI uploads only this)")
    args = parser.parse_args(argv)
    try:
        record = layout(args.dest, deb=args.deb, root=args.from_root)
        if args.record:
            with args.record.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, tarfile.TarError, lzma.LZMAError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps({"status": record["status"], "files": sorted(record["files"]), "htp_executed": False}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
