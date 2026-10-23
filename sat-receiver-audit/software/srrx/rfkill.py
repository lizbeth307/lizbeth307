"""Receive-only second layer: block wlan and bluetooth through the kernel rfkill API.

Same kernel operation as util-linux `rfkill block wlan` / `rfkill block bluetooth`
(RFKILL_OP_CHANGE_ALL on /dev/rfkill), without needing the rfkill package.
CHANGE_ALL also sets the per-type default, so a radio that registers later starts
blocked. This module never unblocks. The first layers on the field/QUIET root are
the AIC8800/btusb modprobe blacklist and udev authorized=0 on FE1.1s port 4
(deployment/deploy.py); rfkill alone is not sufficient (STACK.md v2, 5.2).
"""
import argparse
import os
from pathlib import Path
import struct
import sys

RFKILL_TYPES = {"wlan": 1, "bluetooth": 2}  # linux/rfkill.h enum rfkill_type
RFKILL_OP_CHANGE_ALL = 3  # linux/rfkill.h enum rfkill_operation
EVENT_V1 = struct.Struct("=IBBBB")  # packed struct rfkill_event: idx, type, op, soft, hard


def block_event(kind):
    return EVENT_V1.pack(0, RFKILL_TYPES[kind], RFKILL_OP_CHANGE_ALL, 1, 0)


def block(device="/dev/rfkill"):
    fd = os.open(device, os.O_WRONLY | os.O_CLOEXEC)
    try:
        for kind in RFKILL_TYPES:
            event = block_event(kind)
            if os.write(fd, event) != len(event):
                raise OSError("short rfkill write for " + kind)
    finally:
        os.close(fd)


def unblocked(sysfs="/sys/class/rfkill"):
    """Names of wlan/bluetooth rfkill switches that are neither soft- nor hard-blocked."""
    found = []
    for switch in sorted(Path(sysfs).glob("rfkill*")):
        try:
            kind = (switch / "type").read_text().strip()
            states = {(switch / name).read_text().strip() for name in ("soft", "hard")}
        except OSError:
            found.append(switch.name + " (unreadable)")
            continue
        if kind in RFKILL_TYPES and "1" not in states:
            found.append(switch.name + " " + kind)
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("block", "check"))
    parser.add_argument("--device", default="/dev/rfkill")
    parser.add_argument("--sysfs", default="/sys/class/rfkill")
    args = parser.parse_args(argv)
    try:
        if args.operation == "block":
            block(args.device)
        remaining = unblocked(args.sysfs)
    except OSError as exc:
        print("rfkill BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    if remaining:
        print("rfkill BLOCKED: not blocked: " + ", ".join(remaining), file=sys.stderr)
        return 1
    print("rfkill wlan and bluetooth blocked", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
