#!/usr/bin/env python3
"""SR-RX A/B UFS layout: validation, deterministic identifiers, sfdisk script and per-slot fstab.

Pure functions only (stdlib, host-testable). The layout itself is
deployment/image/partition-layout.json; build_image.py applies it to an image
FILE and recovery_kit.py grows /data to the end of the real UFS. Nothing here
opens a block device.
"""
import json
from pathlib import Path
import re
import uuid

HERE = Path(__file__).resolve().parent
LAYOUT = HERE / "partition-layout.json"
ROLES = ("esp", "root_a", "root_b", "data")
SLOT_ROLE = {"A": "root_a", "B": "root_b"}
# Fixed namespace of this project's derived identifiers: uuid5(namespace, seed + "/" + item).
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/lizbeth307/lizbeth307/sat-receiver-audit/deployment/image")
# GPT with 128 entries of 128 bytes: 16 KiB of entries + one header sector at each end.
GPT_ENTRY_BYTES = 128 * 128
GUID = re.compile(r"[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}\Z")
ITEM = re.compile(r"[a-z0-9_:-]{1,40}\Z")


class LayoutError(ValueError):
    pass


def _exact(data, expected, label):
    if type(data) is not dict or set(data) != set(expected):
        raise LayoutError(label + " has missing or unknown fields")


PART_KEYS = ("role", "gpt_name", "type_guid", "size_bytes", "filesystem", "fs_label", "mount", "mount_options", "fsck_pass")
DATA_KEYS = PART_KEYS + ("image_size_bytes", "directories", "grow_on_target")


def load(path=LAYOUT):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate(data)


def validate(layout):
    _exact(layout, ("schema_version", "status", "description", "sources", "label", "sector_size", "alignment_bytes",
                    "uuid_seed", "partitions", "binds", "quota", "target"), "partition layout")
    if layout["schema_version"] != 1 or layout["label"] != "gpt" or layout["sector_size"] != 4096:
        raise LayoutError("only schema 1, GPT on 4096-byte logical sectors (UFS 4K-native) is supported")
    if layout["status"] not in ("CANDIDATE", "TEST"):
        raise LayoutError("a layout is CANDIDATE (bench gates OPEN) or TEST (CI round trip only)")
    align = layout["alignment_bytes"]
    if type(align) is not int or align < 4096 or align % 4096:
        raise LayoutError("alignment must be a positive multiple of the sector size")
    if type(layout["uuid_seed"]) is not str or not 8 <= len(layout["uuid_seed"]) <= 128:
        raise LayoutError("uuid_seed must be a recorded text of 8..128 characters")
    parts = layout["partitions"]
    if type(parts) is not list or [p.get("role") if type(p) is dict else None for p in parts] != list(ROLES):
        raise LayoutError("partitions must be exactly esp, root_a, root_b, data in this order")
    for part in parts:
        _exact(part, DATA_KEYS if part["role"] == "data" else PART_KEYS, "partition " + part["role"])
        if type(part["type_guid"]) is not str or not GUID.match(part["type_guid"]):
            raise LayoutError(part["role"] + ": type GUID must be upper-case 8-4-4-4-12")
        if part["role"] == "data":
            if part["size_bytes"] is not None or type(part["image_size_bytes"]) is not int or part["image_size_bytes"] <= 0:
                raise LayoutError("data takes the rest of the device: size_bytes null, image_size_bytes > 0")
            if part["image_size_bytes"] % align or part["grow_on_target"] is not True:
                raise LayoutError("data image size must be aligned and grow on target")
            if type(part["directories"]) is not list or not all(type(d) is str and re.fullmatch(r"[a-z0-9-]{1,32}", d) for d in part["directories"]):
                raise LayoutError("data directories are plain names")
        elif type(part["size_bytes"]) is not int or part["size_bytes"] <= 0 or part["size_bytes"] % align:
            raise LayoutError(part["role"] + ": size must be a positive multiple of the alignment")
        expected_fs = "vfat" if part["role"] == "esp" else "ext4"
        if part["filesystem"] != expected_fs:
            raise LayoutError(part["role"] + " must be " + expected_fs)
        for key, pattern in (("gpt_name", r"[a-z0-9-]{1,36}"), ("fs_label", r"[A-Za-z0-9-]{1,11}" if expected_fs == "vfat" else r"[a-z0-9-]{1,16}"),
                             ("mount", r"/[a-z0-9/]*"), ("mount_options", r"[a-z0-9=,_-]+")):
            if type(part[key]) is not str or not re.fullmatch(pattern, part[key]):
                raise LayoutError(part["role"] + ": invalid " + key)
        if part["fsck_pass"] not in (1, 2):
            raise LayoutError(part["role"] + ": fsck pass must be 1 or 2")
    if parts[0]["type_guid"] != "C12A7328-F81F-11D2-BA4B-00A0C93EC93B":
        raise LayoutError("the ESP must carry the EFI System Partition type GUID")
    if parts[1]["size_bytes"] != parts[2]["size_bytes"]:
        raise LayoutError("root A and root B must have the same size")
    if len({p["gpt_name"] for p in parts}) != 4 or len({p["fs_label"].lower() for p in parts}) != 4:
        raise LayoutError("GPT names and filesystem labels must be distinct")
    for bind in layout["binds"]:
        _exact(bind, ("source", "target", "options", "why"), "bind mount")
        if not bind["source"].startswith("/data/") or "ro" not in bind["options"].split(","):
            raise LayoutError("binds are read-only views of /data")
    return layout


def derive_uuid(seed, item):
    """Deterministic, recorded identifier: uuid5 of the layout seed and one item name."""
    if type(seed) is not str or not seed or not ITEM.match(item):
        raise LayoutError("invalid identifier seed or item")
    return str(uuid.uuid5(NAMESPACE, seed + "/" + item))


def identifiers(layout, seed=None):
    """Disk GUID, PARTUUIDs, filesystem UUIDs (ext4), vfat volume id and ext4 hash seeds."""
    seed = layout["uuid_seed"] if seed is None else seed
    ids = {"seed": seed, "disk_guid": derive_uuid(seed, "disk"),
           "partuuid": {role: derive_uuid(seed, "part:" + role) for role in ROLES},
           "fs_uuid": {role: derive_uuid(seed, "fs:" + role) for role in ROLES if role != "esp"},
           "hash_seed": {role: derive_uuid(seed, "hash-seed:" + role) for role in ROLES if role != "esp"},
           "esp_volume_id": derive_uuid(seed, "fs:esp").replace("-", "")[:8].upper()}
    values = [ids["disk_guid"], *ids["partuuid"].values(), *ids["fs_uuid"].values()]
    if len(set(values)) != len(values):
        raise LayoutError("derived identifiers collide")
    return ids


def geometry(layout, data_bytes=None):
    """Sector geometry of the image file: start/size per role and the total file size.

    data_bytes defaults to the layout's image_size_bytes (a compact /data that
    recovery_kit grows to the real UFS end after the write)."""
    sector = layout["sector_size"]
    align = layout["alignment_bytes"] // sector
    data = layout["partitions"][3]
    data_bytes = data["image_size_bytes"] if data_bytes is None else data_bytes
    if type(data_bytes) is not int or data_bytes <= 0 or data_bytes % layout["alignment_bytes"]:
        raise LayoutError("data size must be a positive multiple of the alignment")
    start, out = align, {}
    for part in layout["partitions"]:
        size = (part["size_bytes"] if part["role"] != "data" else data_bytes) // sector
        out[part["role"]] = {"start": start, "size": size}
        start += size
    tail = 1 + GPT_ENTRY_BYTES // sector  # backup entries + backup header
    total = start + tail
    total += (-total) % align
    return {"sector_size": sector, "partitions": out, "total_sectors": total, "total_bytes": total * sector,
            "last_usable_lba": total - tail - 1}


def sfdisk_script(layout, ids, data_bytes=None):
    """sfdisk input for a 4096-byte-sector device (build_image.py: `losetup --sector-size 4096` of the image file)."""
    geo = geometry(layout, data_bytes)
    lines = ["label: gpt", "label-id: " + ids["disk_guid"].upper(), "unit: sectors",
             "first-lba: " + str(layout["alignment_bytes"] // layout["sector_size"]),
             "last-lba: " + str(geo["last_usable_lba"]), ""]
    for part in layout["partitions"]:
        g = geo["partitions"][part["role"]]
        lines.append(f'start={g["start"]}, size={g["size"]}, type={part["type_guid"]}, '
                     f'uuid={ids["partuuid"][part["role"]].upper()}, name="{part["gpt_name"]}"')
    return "\n".join(lines) + "\n"


def fstab(layout, ids, slot):
    """/etc/fstab of one root slot: everything by PARTUUID, so slot B differs only in its root line."""
    if slot not in SLOT_ROLE:
        raise LayoutError("slot must be A or B")
    lines = ["# SR-RX-v2.1 slot " + slot + ": generated by deployment/image/build_image.py from partition-layout.json",
             "# (candidate; bench gates W-03/W-10 OPEN). <source> <mount> <type> <options> <dump> <pass>"]
    for part in layout["partitions"]:
        if part["role"] in ("root_a", "root_b") and part["role"] != SLOT_ROLE[slot]:
            continue  # the other slot is never mounted by this root
        lines.append("PARTUUID={}\t{}\t{}\t{}\t0\t{}".format(ids["partuuid"][part["role"]], part["mount"], part["filesystem"],
                                                            part["mount_options"], part["fsck_pass"]))
    for bind in layout["binds"]:
        lines.append("{}\t{}\tnone\t{}\t0\t0".format(bind["source"], bind["target"], bind["options"]))
    return "\n".join(lines) + "\n"


def mkfs_commands(layout, ids, devices, quota=False):
    """argv lists for mkfs on the given partition device nodes {role: path} (loop partitions of an image file)."""
    parts = {p["role"]: p for p in layout["partitions"]}
    cmds = {"esp": ["mkfs.vfat", "-F", "32", "-S", str(layout["sector_size"]), "-n", parts["esp"]["fs_label"],
                    "-i", ids["esp_volume_id"], devices["esp"]]}
    for role in ("root_a", "root_b", "data"):
        argv = ["mkfs.ext4", "-q", "-F", "-b", "4096", "-L", parts[role]["fs_label"], "-U", ids["fs_uuid"][role],
                "-E", "hash_seed=" + ids["hash_seed"][role] + ",lazy_itable_init=1,lazy_journal_init=1"]
        if role == "data" and quota:
            argv[-1] += ",quotatype=prjquota"
            argv += ["-O", "quota,project", "-I", "256"]
        cmds[role] = argv + [devices[role]]
    return cmds


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="op", required=True)
    for name in ("show", "sfdisk", "fstab"):
        p = sub.add_parser(name)
        p.add_argument("--layout", type=Path, default=LAYOUT)
        p.add_argument("--seed")
        p.add_argument("--data-bytes", type=int)
        if name == "fstab":
            p.add_argument("--slot", choices=("A", "B"), required=True)
    args = parser.parse_args()
    layout = load(args.layout)
    ids = identifiers(layout, args.seed)
    if args.op == "show":
        print(json.dumps({"identifiers": ids, "geometry": geometry(layout, args.data_bytes)}, indent=2))
    elif args.op == "sfdisk":
        print(sfdisk_script(layout, ids, args.data_bytes), end="")
    else:
        print(fstab(layout, ids, args.slot), end="")


if __name__ == "__main__":
    main()
