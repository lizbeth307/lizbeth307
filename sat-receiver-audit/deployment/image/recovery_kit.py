#!/usr/bin/env python3
"""SR-RX-v2.1 recovery kit (IMG-14): assemble, verify and write the golden A/B image to the UFS.

  map       extent map of a sparse image file (SEEK_DATA/SEEK_HOLE, SHA-256 of every extent)
  assemble  kit directory: golden image + map + manifests, locked upstream files, SHA256SUMS, README
  verify    SHA256SUMS of the kit and every image extent against its map
  write     dry run by default. With --execute: writes the image extents to --target
            /dev/disk/by-id/..., reads every extent back, moves the backup GPT to the device
            end, grows /data to the rest of the UFS and checks GPT and filesystems.

Standard library only, so the kit runs from the rescue microSD (Radxa OS, python3) without the
repository. Safety of write: only a whole disk named through /dev/disk/by-id/, 4096-byte logical
sectors, large enough, not holding the running root or any mounted/swap/held partition, opened
O_EXCL, and only with --execute. CI never writes a disk: its only target is a 4K loop device over
a regular file (--test-loop-target). The UFS write itself is bench step W-01/W-09 (OPEN).
"""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
COALESCE = 1 << 20   # holes shorter than 1 MiB are written as zeros: fewer extents, same bytes
CHUNK = 4 << 20
# Recovery set of STACK.md:1700 and STACK.md:137 that sources.lock.json does not lock yet (IMG-08):
# the kit lists them as MISSING until the operator adds verified copies with --extra.
UNLOCKED_ITEMS = (
    ("radxa-os-r2-512", "Radxa OS r2 _512 image for the rescue microSD (never dd to UFS, STACK.md:87)"),
    ("bios-260120", "dragon-q6a_flat_build_wp_260120.zip (SPI BIOS 6.0.260120, STACK.md:137)"),
    ("edl-ng-dist-v1.6.0", "edl-ng-dist-v1.6.0.zip, service-PC EDL tool (STACK.md:137, :1700)"),
    ("spi-dump-1", "first full SPI read, 33,554,432 B (bench W-01)"),
    ("spi-dump-2", "second full SPI read, same SHA-256 as the first (bench W-01)"),
    ("offline-repo-snapshot", "signed aptly snapshot of the lab repository (IMG-08/IMG-09)"),
)


class KitError(RuntimeError):
    pass


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def data_extents(path):
    """[(offset, length)] of the allocated ranges of a sparse file, holes < 1 MiB merged."""
    fd = os.open(path, os.O_RDONLY)
    try:
        size = os.fstat(fd).st_size
        out, pos = [], 0
        while pos < size:
            try:
                start = os.lseek(fd, pos, os.SEEK_DATA)
            except OSError as exc:
                if exc.errno == errno.ENXIO:
                    break
                raise
            end = os.lseek(fd, start, os.SEEK_HOLE)
            if out and start - (out[-1][0] + out[-1][1]) < COALESCE:
                out[-1] = (out[-1][0], end - out[-1][0])
            else:
                out.append((start, end - start))
            pos = end
        return size, out
    finally:
        os.close(fd)


def make_map(image, layout_sector=4096):
    size, extents = data_extents(image)
    if size % layout_sector:
        raise KitError("image size is not a multiple of the sector size")
    rows = []
    with open(image, "rb") as handle:
        for offset, length in extents:
            digest = hashlib.sha256()
            handle.seek(offset)
            remaining = length
            while remaining:
                chunk = handle.read(min(CHUNK, remaining))
                if not chunk:
                    raise KitError("image shorter than its extents")
                digest.update(chunk)
                remaining -= len(chunk)
            rows.append([offset, length, digest.hexdigest()])
    return {"schema_version": 1, "format": "srrx-extent-map", "image": Path(image).name, "image_bytes": size,
            "sector_size": layout_sector, "data_bytes": sum(r[1] for r in rows), "extents": rows,
            "holes": "read as zero in the image; a write leaves them untouched on the target (free filesystem space)"}


def load_map(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("format") != "srrx-extent-map" or data.get("schema_version") != 1 or data.get("sector_size") != 4096:
        raise KitError("not an srrx extent map for 4096-byte sectors")
    end = 0
    for offset, length, digest in data["extents"]:
        if offset < end or length <= 0 or offset % 512 or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise KitError("extent map entries overlap or are malformed")
        end = offset + length
    if end > data["image_bytes"]:
        raise KitError("extent map exceeds the image size")
    return data


def verify_extents(source, extent_map, fd=None):
    """Hash every mapped extent of `source` (a file path) or of an open device fd."""
    bad = []
    handle = open(source, "rb") if fd is None else None
    try:
        for offset, length, digest in extent_map["extents"]:
            h, pos, remaining = hashlib.sha256(), offset, length
            while remaining:
                size = min(CHUNK, remaining)
                chunk = os.pread(fd, size, pos) if fd is not None else (handle.seek(pos), handle.read(size))[1]
                if len(chunk) != size:
                    raise KitError("short read at offset " + str(pos))
                h.update(chunk)
                pos += size
                remaining -= size
            if h.hexdigest() != digest:
                bad.append(offset)
    finally:
        if handle:
            handle.close()
    return bad


# ---------------------------------------------------------------- kit

def sparse_copy(source, target):
    size, extents = data_extents(source)
    with open(source, "rb") as src, open(target, "xb") as dst:
        for offset, length in extents:
            src.seek(offset)
            dst.seek(offset)
            remaining = length
            while remaining:
                chunk = src.read(min(CHUNK, remaining))
                dst.write(chunk)
                remaining -= len(chunk)
        dst.truncate(size)


def assemble(image, extent_map, out, manifest=None, facts=None, cache=None, lock=None, extras=(), link=False):
    out = Path(out)
    if out.exists():
        raise KitError("kit output must be a new directory")
    load_map(extent_map)
    (out / "golden").mkdir(parents=True)
    target = out / "golden" / Path(image).name
    if link:
        os.link(image, target)  # same filesystem only (CI): no second copy of the image data
    else:
        sparse_copy(image, target)
    shutil.copyfile(extent_map, out / "golden" / Path(extent_map).name)
    for extra in (manifest, facts):
        if extra:
            shutil.copyfile(extra, out / "golden" / Path(extra).name)
    items = []
    if cache and lock:
        for art in json.loads(Path(lock).read_text(encoding="utf-8"))["artifacts"]:
            source = Path(cache) / art["cache_path"]
            dest = out / "upstream" / art["cache_path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
            ok = sha256_file(dest) == art["sha256"] and dest.stat().st_size == art["size"]
            if not ok:
                raise KitError("locked upstream file differs: " + art["id"])
            items.append({"id": art["id"], "path": dest.relative_to(out).as_posix(), "sha256": art["sha256"], "status": "PRESENT"})
    given = {}
    for spec in extras:
        name, _, rest = spec.partition("=")
        path, _, digest = rest.rpartition(":")
        if not name or not path or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise KitError("--extra NAME=PATH:SHA256")
        if sha256_file(path) != digest:
            raise KitError("--extra " + name + " differs from the given SHA-256")
        dest = out / "extra" / name / Path(path).name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        given[name] = {"id": name, "path": dest.relative_to(out).as_posix(), "sha256": digest, "status": "PRESENT"}
    for item_id, what in UNLOCKED_ITEMS:
        items.append(given.pop(item_id, {"id": item_id, "status": "MISSING", "what": what,
                                         "why": "not locked in deployment/sources.lock.json (IMG-08) or a bench product; add with --extra NAME=PATH:SHA256"}))
    items.extend(given.values())
    (out / "tools").mkdir()
    shutil.copyfile(Path(__file__), out / "tools/recovery_kit.py")
    readme = HERE / "files/kit-README.uk.txt"
    shutil.copyfile(readme, out / "README.uk.txt")
    kit = {"schema_version": 1, "status": "KIT_ASSEMBLED", "image": target.relative_to(out).as_posix(),
           "map": "golden/" + Path(extent_map).name, "items": items,
           "missing": [i["id"] for i in items if i["status"] == "MISSING"], "hardware_ready": False,
           "bench_steps_open": ["W-01 (SPI dumps, EDL)", "W-09 (rescue cards)", "UFS write on the unit"]}
    (out / "kit-manifest.json").write_text(json.dumps(kit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sums = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path != target and path.name != "SHA256SUMS":
            sums.append(sha256_file(path) + "  " + path.relative_to(out).as_posix())
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return kit


def verify_kit(kit_dir):
    kit_dir = Path(kit_dir)
    bad = []
    for line in (kit_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, _, name = line.partition("  ")
        path = kit_dir / name
        if ".." in Path(name).parts or not path.is_file() or sha256_file(path) != digest:
            bad.append(name)
    kit = json.loads((kit_dir / "kit-manifest.json").read_text(encoding="utf-8"))
    extent_map = load_map(kit_dir / kit["map"])
    image = kit_dir / kit["image"]
    if image.stat().st_size != extent_map["image_bytes"]:
        bad.append(kit["image"] + " size")
    bad += ["extent@" + str(o) for o in verify_extents(image, extent_map)]
    return {"status": "KIT_VERIFIED" if not bad else "BLOCKED", "bad": bad, "missing": kit["missing"]}


# ---------------------------------------------------------------- target checks

def _sys_block(name):
    return Path("/sys/class/block") / name


def _disk_of(majmin):
    """Whole-disk name of a block device number (a partition maps to its parent)."""
    try:
        node = Path("/sys/dev/block", majmin).resolve(strict=True)
    except OSError:
        return None
    return node.parent.name if (node / "partition").exists() else node.name


def _mounted_disks():
    disks = {}
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        fields = line.split()
        disk = _disk_of(fields[2])
        if disk:
            disks.setdefault(disk, []).append(fields[4])
    for line in Path("/proc/swaps").read_text().splitlines()[1:]:
        device = line.split()[0] if line.split() else ""
        if device.startswith("/dev/"):
            try:
                st = os.stat(device)
                disk = _disk_of("%d:%d" % (os.major(st.st_rdev), os.minor(st.st_rdev)))
                if disk:
                    disks.setdefault(disk, []).append("[swap]")
            except OSError:
                pass
    return disks


def check_target(target, extent_map, image=None, test_loop=False):
    target = str(target)
    if test_loop:
        if not re.fullmatch(r"/dev/loop[0-9]+", target):
            raise KitError("--test-loop-target accepts only /dev/loopN")
        backing = _sys_block(target[5:]) / "loop/backing_file"
        if not backing.is_file() or not Path(backing.read_text().strip()).is_file():
            raise KitError("test loop device is not backed by a regular file")
        device = target
    else:
        if not target.startswith("/dev/disk/by-id/"):
            raise KitError("target must be named through /dev/disk/by-id/ (never /dev/sdX or a partition)")
        device = os.path.realpath(target)
    st = os.stat(device)
    if not stat.S_ISBLK(st.st_mode):
        raise KitError("target is not a block device")
    name = Path(device).name
    sysdir = _sys_block(name)
    if (sysdir / "partition").exists():
        raise KitError("target is a partition, not a whole disk")
    if not test_loop and name.startswith(("loop", "ram", "zram", "dm-", "md")):
        raise KitError("target is a virtual block device")
    log_sec = int((sysdir / "queue/logical_block_size").read_text())
    size = int((sysdir / "size").read_text()) * 512
    if log_sec != extent_map["sector_size"]:
        raise KitError("target LOG-SEC is %d, the image needs %d (UFS 4K-native, STACK.md:87)" % (log_sec, extent_map["sector_size"]))
    if size < extent_map["image_bytes"]:
        raise KitError("target (%d B) is smaller than the image (%d B)" % (size, extent_map["image_bytes"]))
    mounted = _mounted_disks()
    if name in mounted:
        raise KitError("target holds mounted filesystems or swap (" + ",".join(mounted[name][:4]) + "), e.g. the running root")
    holders = [p.name for p in (sysdir / "holders").iterdir()] if (sysdir / "holders").is_dir() else []
    for part in sysdir.iterdir():
        if (part / "partition").exists() and (part / "holders").is_dir():
            holders += [p.name for p in (part / "holders").iterdir()]
    if holders:
        raise KitError("target or its partitions are held by " + ",".join(holders))
    if image is not None:
        ist = os.stat(image)
        if _disk_of("%d:%d" % (os.major(ist.st_dev), os.minor(ist.st_dev))) == name:
            raise KitError("the image file lives on the target disk")
    return {"device": device, "name": name, "log_sec": log_sec, "size_bytes": size, "image_bytes": extent_map["image_bytes"]}


def _part_device(name, number):
    for part in sorted(_sys_block(name).iterdir()):
        if (part / "partition").is_file() and (part / "partition").read_text().strip() == str(number):
            return "/dev/" + part.name
    raise KitError("partition %d of %s not found" % (number, name))


def _run(argv, check=True, input=None):
    done = subprocess.run(argv, capture_output=True, text=True, input=input)
    if check and done.returncode:
        raise KitError(" ".join(argv) + " failed: " + (done.stdout + done.stderr)[-800:])
    return done


def write(image, extent_map_path, target, execute=False, test_loop=False, grow=True):
    extent_map = load_map(extent_map_path)
    if Path(image).stat().st_size != extent_map["image_bytes"]:
        raise KitError("image size differs from its map")
    info = check_target(target, extent_map, image, test_loop)
    plan = {"target": info, "extents": len(extent_map["extents"]), "data_bytes": extent_map["data_bytes"],
            "then": ["read back every extent (SHA-256)", "sfdisk --relocate gpt-bak-std", "grow partition 4 (/data) to the device end",
                     "e2fsck -f + resize2fs /data", "sfdisk --verify, e2fsck -fn (2,3,4), fsck.vfat -n (1)"] if grow else ["read back"]}
    if not execute:
        return dict(status="DRY_RUN_ONLY", **plan)
    bad = verify_extents(image, extent_map)
    if bad:
        raise KitError("the kit image differs from its map before the write: " + str(bad[:5]))
    fd = os.open(info["device"], os.O_RDWR | os.O_EXCL | os.O_CLOEXEC)
    started = time.monotonic()
    try:
        with open(image, "rb") as src:
            for offset, length, _ in extent_map["extents"]:
                pos, remaining = offset, length
                while remaining:
                    chunk = os.pread(src.fileno(), min(CHUNK, remaining), pos)
                    written = os.pwrite(fd, chunk, pos)
                    if written != len(chunk):
                        raise KitError("short write at offset " + str(pos))
                    pos += written
                    remaining -= written
        os.fsync(fd)
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        bad = verify_extents(None, extent_map, fd=fd)
    finally:
        os.close(fd)
    if bad:
        raise KitError("read-back differs at %d extents (first %s)" % (len(bad), bad[:3]))
    result = dict(status="WRITTEN_AND_READ_BACK", seconds=round(time.monotonic() - started, 1), **plan)
    if grow:
        device = info["device"]
        _run(["sfdisk", "--relocate", "gpt-bak-std", device])
        _run(["sfdisk", "--no-reread", "-N", "4", device], input=", +\n")
        _run(["partx", "-u", device], check=False)
        _run(["udevadm", "settle"], check=False)
        data = _part_device(info["name"], 4)
        fsck = _run(["e2fsck", "-f", "-y", data], check=False)
        if fsck.returncode not in (0, 1):
            raise KitError("e2fsck of /data before resize failed: " + fsck.stdout[-400:])
        _run(["resize2fs", data])
        checks = {"sfdisk_verify": _run(["sfdisk", "--verify", device], check=False).returncode,
                  "esp": _run(["fsck.vfat", "-n", _part_device(info["name"], 1)], check=False).returncode}
        for number in (2, 3, 4):
            checks["part%d" % number] = _run(["e2fsck", "-fn", _part_device(info["name"], number)], check=False).returncode
        table = json.loads(_run(["sfdisk", "--json", device]).stdout)["partitiontable"]
        result.update(checks=checks, partition_table=table)
        if any(checks.values()):
            result["status"] = "BLOCKED"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="op", required=True)
    p = sub.add_parser("map")
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("assemble")
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--map", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--manifest", type=Path)
    p.add_argument("--facts", type=Path)
    p.add_argument("--cache", type=Path, help="cache with the locked base image and kernel debs (sources.lock.json)")
    p.add_argument("--lock", type=Path)
    p.add_argument("--extra", action="append", default=[], metavar="NAME=PATH:SHA256")
    p.add_argument("--link", action="store_true", help="hard-link the image (same filesystem) instead of a sparse copy")
    p = sub.add_parser("verify")
    p.add_argument("--kit", type=Path, required=True)
    p = sub.add_parser("write")
    p.add_argument("--kit", type=Path)
    p.add_argument("--image", type=Path)
    p.add_argument("--map", type=Path)
    p.add_argument("--target", required=True, help="/dev/disk/by-id/<UFS whole disk>")
    p.add_argument("--execute", action="store_true", help="really write; without it only the checks and the plan run")
    p.add_argument("--test-loop-target", action="store_true", help="CI only: the target is a 4K loop device over a regular file")
    p.add_argument("--no-grow", action="store_true")
    args = parser.parse_args()
    try:
        if args.op == "map":
            if args.output.exists():
                raise KitError("map output must be new")
            data = make_map(args.image)
            args.output.write_text(json.dumps(data) + "\n", encoding="utf-8")
            result = {"status": "MAP_WRITTEN", "extents": len(data["extents"]), "data_bytes": data["data_bytes"]}
        elif args.op == "assemble":
            result = assemble(args.image, args.map, args.out, args.manifest, args.facts, args.cache, args.lock, args.extra, args.link)
        elif args.op == "verify":
            result = verify_kit(args.kit)
        else:
            if args.kit:
                kit = json.loads((args.kit / "kit-manifest.json").read_text(encoding="utf-8"))
                image, extent_map = args.kit / kit["image"], args.kit / kit["map"]
            elif args.image and args.map:
                image, extent_map = args.image, args.map
            else:
                raise KitError("write needs --kit or --image with --map")
            result = write(image, extent_map, args.target, args.execute, args.test_loop_target, not args.no_grow)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("status") != "BLOCKED" else 2
    except (OSError, ValueError, KitError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
