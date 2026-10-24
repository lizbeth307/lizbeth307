#!/usr/bin/env python3
"""Pinned MicroPython flashing for the Pico supervisor and the RP2040-Zero IMU pack.

Every subcommand is a dry run that prints its plan unless --execute is given. Inputs are
checked before anything touches a device: the UF2 against firmware/runtime.lock.json
(size, SHA-256, UF2 block magic and RP2040 family), the reviewed file package against
firmware/dist/build-manifest.json and its SOURCE-SHA256.json, mpremote against the locked
version. The device side then has to match too: MicroPython release and board name from
os.uname(), an empty filesystem before copying, exactly the role's files after it (each
SHA-256 computed on the device), and for the Pico the provisioned records bound to its
machine.unique_id(). Physical steps stay with the operator (BOOTSEL, LAB5 isolation,
bench checks in firmware/*/README.md); nothing here marks a board flashed or qualified.

  uf2      verify a UF2 (and with --drive/--execute copy it to the RPI-RP2 BOOTSEL drive)
  install  copy the role's files in order, verify on the device, optionally the records
  verify   compare the device filesystem with the package (no writes)
  serial   print machine.unique_id() of the connected board (no writes)
"""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
LOCK = PROJECT / "firmware/runtime.lock.json"
DIST = PROJECT / "firmware/dist"
UF2_MAGIC = (0x0A324655, 0x9E5D5157, 0x0AB16F30)
UF2_FAMILY_FLAG = 0x2000
RP2040_FAMILY = 0xE48BFF56
TIMEOUT_S = 60
# Runs on the board: SHA-256 of every top-level entry (directories reported as such).
HASH_SCRIPT = (
    "import os,hashlib,binascii,json\n"
    "r={}\n"
    "for n in os.listdir('/'):\n"
    " if os.stat('/'+n)[0]&0x4000:\n"
    "  r[n]='dir'\n"
    "  continue\n"
    " h=hashlib.sha256()\n"
    " f=open('/'+n,'rb')\n"
    " while True:\n"
    "  b=f.read(512)\n"
    "  if not b:\n"
    "   break\n"
    "  h.update(b)\n"
    " f.close()\n"
    " r[n]=binascii.hexlify(h.digest()).decode()\n"
    "print('SRRX-FS '+json.dumps(r))\n")
UNAME_SCRIPT = "import os,json\nu=os.uname()\nprint('SRRX-UNAME '+json.dumps({'release':u.release,'machine':u.machine}))\n"
SERIAL_SCRIPT = "import machine\nprint('SRRX-SERIAL '+machine.unique_id().hex())\n"


class FlashError(ValueError):
    pass


def lock():
    data = json.loads(LOCK.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("kind") != "srrx_mcu_runtime_lock":
        raise FlashError("unexpected firmware/runtime.lock.json")
    return data


def board(role):
    boards = lock()["boards"]
    if role not in boards:
        raise FlashError("role must be one of " + ", ".join(sorted(boards)))
    return boards[role]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def check_uf2(path, pin, ram_loader=False):
    """Size, SHA-256 and UF2 structure of a pinned image; family RP2040 in every flash block."""
    data = Path(path).read_bytes()
    if len(data) != pin["size"] or sha256(data) != pin["sha256"]:
        raise FlashError(Path(path).name + " differs from the locked " + pin["file"])
    if len(data) % 512 or len(data) // 512 != pin["blocks"]:
        raise FlashError("UF2 block count differs")
    families = set()
    for offset in range(0, len(data), 512):
        block = data[offset:offset + 512]
        magic0, magic1, flags, address, _size, _number, _total, family = struct.unpack("<8I", block[:32])
        if (magic0, magic1, struct.unpack("<I", block[508:])[0]) != UF2_MAGIC or not flags & UF2_FAMILY_FLAG:
            raise FlashError("not a family-tagged UF2 block at offset %d" % offset)
        families.add(family)
        if not ram_loader and (family != RP2040_FAMILY or not 0x10000000 <= address < 0x11000000):
            raise FlashError("block outside RP2040 flash or another family at offset %d" % offset)
    if RP2040_FAMILY not in families:
        raise FlashError("no RP2040 blocks")
    return {"file": pin["file"], "sha256": pin["sha256"], "blocks": len(data) // 512}


def package(role):
    """{name: bytes} of the role's device files from the reviewed zip, in copy order."""
    pin = board(role)
    zpath = PROJECT / pin["package"]
    data = zpath.read_bytes()
    built = json.loads((DIST / "build-manifest.json").read_text(encoding="utf-8"))["packages"][role]
    if built["sha256"] != sha256(data) or built["bytes"] != len(data):
        raise FlashError(zpath.name + " differs from firmware/dist/build-manifest.json")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    listed = json.loads(members.pop("SOURCE-SHA256.json"))
    if listed != built["source_files"] or {n: sha256(b) for n, b in members.items()} != listed:
        raise FlashError(zpath.name + " members differ from SOURCE-SHA256.json")
    order = pin["copy_order"]
    if sorted(order + pin["not_copied"]) != sorted(members) or order[-1] != "main.py" or len(set(order)) != len(order):
        raise FlashError("copy order does not cover exactly the package (main.py last)")
    return {name: members[name] for name in order}


class Mpremote:
    """Device access through the locked mpremote; every call is one bounded subprocess."""
    def __init__(self, port, command=("mpremote",)):
        self.port, self.command = port, list(command)

    def _run(self, *args, timeout=TIMEOUT_S):
        out = subprocess.run(self.command + list(args), capture_output=True, text=True, timeout=timeout)
        if out.returncode:
            raise FlashError("mpremote " + args[0] + " failed: " + out.stderr.strip()[-300:])
        return out.stdout

    def version(self):
        return self._run("version").strip()

    def exec(self, code):
        return self._run("connect", self.port, "exec", code)

    def cp(self, local, remote):
        self._run("connect", self.port, "fs", "cp", str(local), ":" + remote)

    def rm(self, remote):
        self._run("connect", self.port, "fs", "rm", ":" + remote)

    def reset(self):
        self._run("connect", self.port, "reset")


def _tagged(output, tag):
    lines = [line[len(tag) + 1:] for line in output.splitlines() if line.startswith(tag + " ")]
    if len(lines) != 1:
        raise FlashError("device gave no single " + tag + " line")
    return lines[0]


def device_files(transport):
    return json.loads(_tagged(transport.exec(HASH_SCRIPT), "SRRX-FS"))


def device_serial(transport):
    serial = _tagged(transport.exec(SERIAL_SCRIPT), "SRRX-SERIAL")
    if len(serial) != 16 or any(c not in "0123456789abcdef" for c in serial):
        raise FlashError("unexpected machine.unique_id()")
    return serial


def check_device(transport, role):
    pin = board(role)
    version = transport.version()
    if version != "mpremote " + lock()["mpremote"]["version"]:
        raise FlashError("mpremote is not the locked " + lock()["mpremote"]["version"] + ": " + version)
    uname = json.loads(_tagged(transport.exec(UNAME_SCRIPT), "SRRX-UNAME"))
    if uname["release"] != pin["micropython"] or uname["machine"] != pin["uname_machine"]:
        raise FlashError("board runs %s on %s, expected %s on %s" % (uname["release"], uname["machine"],
                                                                    pin["micropython"], pin["uname_machine"]))
    return uname


def load_records(records, serial):
    """calibration.json + commissioning.json, validated by the Pico's own calibration.py for this serial."""
    spec = importlib.util.spec_from_file_location("srrx_flash_calibration", PROJECT / "firmware/pico/calibration.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    files = {name: (Path(records) / name).read_bytes() for name in board("pico")["records"]}
    calibration = json.loads(files["calibration.json"])
    commissioning = json.loads(files["commissioning.json"])
    try:
        module.validate(calibration, serial)
        valid = module.commissioning_valid(commissioning, calibration, serial)
    except (ValueError, KeyError, TypeError) as exc:
        raise FlashError("records are not valid for this Pico: " + str(exc)) from exc
    if not valid:
        raise FlashError("commissioning.json is not valid for this Pico and calibration")
    return files


def expected_after(role, records=None):
    files = {name: sha256(data) for name, data in package(role).items()}
    files.update({name: sha256(data) for name, data in (records or {}).items()})
    return files


def verify(transport, role, records=None):
    expected, actual = expected_after(role, records), device_files(transport)
    if actual != expected:
        extra = sorted(set(actual) - set(expected))
        wrong = sorted(n for n in expected if actual.get(n) != expected[n])
        raise FlashError("device files differ: extra %s, missing or different %s" % (extra, wrong))
    return {"status": "DEVICE_FILES_MATCH_PACKAGE", "role": role, "files": sorted(expected), "hardware_qualified": False}


def plan_install(role, port, records_dir=None):
    pin = board(role)
    steps = ["mpremote version  # must print: mpremote " + lock()["mpremote"]["version"],
             "mpremote connect %s exec <os.uname() check: %s on %s>" % (port, pin["micropython"], pin["uname_machine"]),
             "mpremote connect %s exec <list files: must be empty>" % port]
    steps += ["mpremote connect %s fs cp <%s from %s> :%s" % (port, name, pin["package"], name) for name in pin["copy_order"]]
    if records_dir:
        steps.insert(3, "mpremote connect %s exec <machine.unique_id() for the records>" % port)
        steps += ["mpremote connect %s fs cp %s :%s" % (port, Path(records_dir) / name, name) for name in pin["records"]]
    steps += ["mpremote connect %s exec <SHA-256 of every file: exactly the package%s>" % (port, " and records" if records_dir else ""),
              "mpremote connect %s reset" % port]
    return steps


def install(transport, role, records_dir=None, staging=None):
    """Fresh filesystem -> package in order -> optional records -> on-device verification -> reset."""
    check_device(transport, role)
    if role != "pico" and records_dir:
        raise FlashError("only the Pico takes calibration/commissioning records")
    present = device_files(transport)
    if present:
        raise FlashError("device filesystem is not empty (%s): erase with the locked nuke UF2 and reflash MicroPython first"
                         % ", ".join(sorted(present)))
    records = load_records(records_dir, device_serial(transport)) if records_dir else None
    files = package(role)
    staging = Path(staging)
    for name, data in list(files.items()) + list((records or {}).items()):
        local = staging / name
        local.write_bytes(data)
        transport.cp(local, name)
    result = verify(transport, role, records)
    transport.reset()
    return dict(result, reset=True, records_copied=bool(records))


def copy_uf2(image, drive):
    """Copy a verified UF2 onto the RP2040 bootrom drive (INFO_UF2.TXT names Board-ID RPI-RP2)."""
    info = (Path(drive) / "INFO_UF2.TXT").read_text(encoding="ascii", errors="replace")
    if "Board-ID: RPI-RP2" not in info:
        raise FlashError(str(drive) + " is not an RP2040 BOOTSEL drive")
    shutil.copyfile(image, Path(drive) / Path(image).name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="op", required=True)
    u = sub.add_parser("uf2")
    u.add_argument("--role", choices=("pico", "imu"), required=True)
    u.add_argument("--image", choices=("micropython", "erase"), default="micropython")
    u.add_argument("--file", type=Path, required=True, help="downloaded UF2")
    u.add_argument("--drive", type=Path, help="mounted RPI-RP2 drive")
    for name in ("install", "verify", "serial"):
        p = sub.add_parser(name)
        p.add_argument("--port", required=True, help="e.g. /dev/ttyACM0 (USB REPL of the isolated board)")
        p.add_argument("--mpremote", default="mpremote", help="locked mpremote executable")
        if name != "serial":
            p.add_argument("--role", choices=("pico", "imu"), required=True)
        if name in ("install", "verify"):
            p.add_argument("--records", type=Path, help="Pico only: directory from srrx.provision prepare")
    for p in sub.choices.values():
        p.add_argument("--execute", action="store_true", help="act on the device (default: dry run)")
    args = parser.parse_args(argv)
    try:
        if args.op == "uf2":
            pin = lock()["flash_erase"] if args.image == "erase" else board(args.role)["uf2"]
            result = dict(check_uf2(args.file, pin, ram_loader=args.image == "erase"), status="UF2_MATCHES_LOCK", copied=False)
            if args.drive and args.execute:
                copy_uf2(args.file, args.drive)
                result["copied"] = True
            elif args.drive:
                result["plan"] = "copy %s to %s (dry run; add --execute)" % (args.file.name, args.drive)
        elif not args.execute and args.op == "install":
            package(args.role)
            result = {"status": "DRY_RUN", "plan": plan_install(args.role, args.port, args.records)}
        else:
            transport = Mpremote(args.port, (args.mpremote,))
            if args.op == "serial":
                result = {"status": "SERIAL_READ", "serial": device_serial(transport)}
            elif args.op == "verify":
                check_device(transport, args.role)
                records = load_records(args.records, device_serial(transport)) if args.records else None
                result = verify(transport, args.role, records)
            else:
                import tempfile
                with tempfile.TemporaryDirectory(prefix="srrx-mcu-") as staging:
                    result = install(transport, args.role, args.records, staging)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
