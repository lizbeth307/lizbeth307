#!/usr/bin/env python3
"""Assemble the srrx-pps-gpio DKMS source tree and check a built module's vermagic.

assemble: verifies the downloaded pps-gpio.c against system-sources.lock.json (SHA-256 and
size) and writes <dest>/srrx-pps-gpio-<version>/{dkms.conf,Makefile,pps-gpio.c} into a NEW
directory, ready for /usr/src and `dkms add/build/install` on a builder or the target.
vermagic: reads the modinfo vermagic string out of a built .ko (no modinfo binary needed)
and requires the held kernel release. Neither command loads a module or touches /lib/modules;
PPS on GPIO96 (pinmux owner, /dev/pps-gnss, chrony selection) stays bench gate W1-2.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
LOCK = HERE / "system-sources.lock.json"
TREE = HERE / "dkms/pps-gpio"
KERNEL_RELEASE = "6.18.2-4-qcom"


class DkmsError(ValueError):
    pass


def lock():
    return json.loads(LOCK.read_text(encoding="utf-8"))["pps_gpio"]


def package_version():
    match = re.search(r'^PACKAGE_VERSION="([^"]+)"$', (TREE / "dkms.conf").read_text(encoding="utf-8"), re.M)
    if not match:
        raise DkmsError("dkms.conf has no PACKAGE_VERSION")
    return match.group(1)


def assemble(source, dest):
    pin = lock()
    data = Path(source).read_bytes()
    if len(data) != pin["size"] or hashlib.sha256(data).hexdigest() != pin["sha256"]:
        raise DkmsError("pps-gpio.c differs from the locked radxa/kernel " + pin["commit"][:7] + " file")
    dest = Path(dest)
    if dest.exists():
        raise DkmsError("destination must be a new directory")
    tree = dest / ("srrx-pps-gpio-" + package_version())
    tree.mkdir(parents=True)
    for name in ("dkms.conf", "Makefile"):
        shutil.copyfile(TREE / name, tree / name)
    (tree / "pps-gpio.c").write_bytes(data)
    return {"status": "DKMS_SOURCE_ASSEMBLED", "tree": str(tree), "source_sha256": pin["sha256"],
            "module_loaded": False}


def vermagic(module):
    data = Path(module).read_bytes()
    if data[:4] != b"\x7fELF":
        raise DkmsError("not an ELF kernel module")
    found = re.findall(rb"vermagic=([^\0]{1,200})\0", data)
    if len(set(found)) != 1:
        raise DkmsError("module has no single vermagic string")
    return found[0].decode("ascii", "replace")


def check_vermagic(module, release=KERNEL_RELEASE):
    value = vermagic(module)
    if value.split()[0] != release:
        raise DkmsError("vermagic " + value + " is not for " + release)
    return {"status": "VERMAGIC_MATCHES", "vermagic": value, "module_loaded": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="op", required=True)
    a = sub.add_parser("assemble")
    a.add_argument("--source", type=Path, required=True)
    a.add_argument("--dest", type=Path, required=True)
    v = sub.add_parser("vermagic")
    v.add_argument("--module", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = assemble(args.source, args.dest) if args.op == "assemble" else check_vermagic(args.module)
    except (OSError, ValueError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
