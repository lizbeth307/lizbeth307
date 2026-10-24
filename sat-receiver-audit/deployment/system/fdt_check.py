#!/usr/bin/env python3
"""Read a flattened device tree and check the SR-RX lab/field overlay effects in it.

Works on a merged lab.dtb/field.dtb (CI) and on /sys/firmware/fdt of the booted Q6A
(bench W-10, build/07 §3.3). The whole-blob SHA-256 of /sys/firmware/fdt is not a
usable reference: the EFI stub writes /chosen (bootargs, initrd, kaslr-seed, EFI memory
map) and the UEFI DT fixup may touch more, so `diff` compares node by node and reports
what differs instead. Pure Python, read-only, no dtc needed.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

FDT_MAGIC = 0xD00DFEED
BEGIN_NODE, END_NODE, PROP, NOP, END = 1, 2, 3, 4, 9
MAX_BYTES = 8 * 1024 * 1024
QUP0 = "/soc@0/geniqup@9c0000"
TLMM = "/soc@0/pinctrl@f100000"
PCIE0 = "/soc@0/pcie@1c00000"
PPS = "/pps-gnss"
# Firmware/EFI-stub owned nodes, never part of the overlay comparison.
VOLATILE = ("/chosen",)


class FdtError(ValueError):
    pass


def parse(data):
    """{node path: {property: bytes}} of a DTB (FDT v17 struct block)."""
    if len(data) < 40 or len(data) > MAX_BYTES:
        raise FdtError("not a DTB of plausible size")
    magic, total, off_struct, off_strings, _rsv, version, _last, _cpu, size_strings, size_struct = struct.unpack(">10I", data[:40])
    if magic != FDT_MAGIC or total > len(data) or version < 17:
        raise FdtError("bad FDT header")
    strings = data[off_strings:off_strings + size_strings]
    pos, end = off_struct, off_struct + size_struct
    nodes, stack = {}, []

    def take_string(start):
        stop = data.index(b"\0", start)
        return data[start:stop].decode("ascii", "replace"), stop + 1

    while pos < end:
        (token,) = struct.unpack(">I", data[pos:pos + 4])
        pos += 4
        if token == BEGIN_NODE:
            name, pos = take_string(pos)
            pos = (pos + 3) & ~3
            path = "/" if not stack else (stack[-1].rstrip("/") + "/" + name)
            stack.append(path)
            nodes.setdefault(path, {})
        elif token == END_NODE:
            if not stack:
                raise FdtError("unbalanced END_NODE")
            stack.pop()
        elif token == PROP:
            length, nameoff = struct.unpack(">II", data[pos:pos + 8])
            pos += 8
            if not stack or nameoff >= len(strings):
                raise FdtError("property outside a node")
            name = strings[nameoff:strings.index(b"\0", nameoff)].decode("ascii", "replace")
            nodes[stack[-1]][name] = data[pos:pos + length]
            pos = (pos + length + 3) & ~3
        elif token == NOP:
            continue
        elif token == END:
            break
        else:
            raise FdtError("unknown FDT token %d" % token)
    if stack:
        raise FdtError("unterminated node")
    return nodes


def text(value):
    return value.rstrip(b"\0").decode("ascii", "replace") if value is not None else None


def strings_of(value):
    return [s.decode("ascii", "replace") for s in value.rstrip(b"\0").split(b"\0")] if value else []


def cells(value):
    return list(struct.unpack(">%dI" % (len(value) // 4), value)) if value else []


def by_phandle(nodes):
    return {cells(props["phandle"])[0]: path for path, props in nodes.items() if "phandle" in props}


def check(nodes, profile):
    """Problems (empty: the overlay effects are present) for profile lab or field."""
    if profile not in ("lab", "field"):
        raise FdtError("profile must be lab or field")
    problems = []
    handles = by_phandle(nodes)

    def prop(path, name):
        return nodes.get(path, {}).get(name)

    def want_status(path, value):
        status = text(prop(path, "status")) if path in nodes else None
        actual = "okay" if path in nodes and status is None else status
        if actual != value and not (value == "okay" and actual == "ok"):
            problems.append("%s status %s, expected %s" % (path, actual, value))

    def want_pinctrl(path, states):
        refs = [handles.get(h) for h in cells(prop(path, "pinctrl-0"))]
        if refs != [TLMM + "/" + s for s in states]:
            problems.append("%s pinctrl-0 %s, expected %s" % (path, refs, states))

    if "radxa,dragon-q6a" not in strings_of(prop("/", "compatible")):
        problems.append("root compatible lacks radxa,dragon-q6a")
    for node, states in (("serial@998000", ("qup-uart6-tx-state", "qup-uart6-rx-state")),
                         ("serial@99c000", ("qup-uart7-tx-state", "qup-uart7-rx-state"))):
        want_status(QUP0 + "/" + node, "okay")
        want_pinctrl(QUP0 + "/" + node, states)
    for node in ("i2c@980000", "i2c@988000"):
        want_status(QUP0 + "/" + node, "okay")
        if cells(prop(QUP0 + "/" + node, "clock-frequency")) != [100000]:
            problems.append(QUP0 + "/" + node + " clock-frequency is not 100000")
    for node in ("spi@998000", "i2c@998000", "spi@99c000", "i2c@99c000", "spi@980000", "serial@980000",
                 "spi@988000", "serial@988000"):
        want_status(QUP0 + "/" + node, "disabled")
    for alias, target in (("serial1", QUP0 + "/serial@998000"), ("serial2", QUP0 + "/serial@99c000")):
        if text(prop("/aliases", alias)) != target:
            problems.append("/aliases %s is %s, expected %s" % (alias, text(prop("/aliases", alias)), target))
    pps = [path for path, props in nodes.items() if "pps-gpio" in strings_of(props.get("compatible"))]
    if pps != [PPS]:
        problems.append("pps-gpio nodes %s, expected exactly %s" % (pps, PPS))
    else:
        gpios = cells(prop(PPS, "gpios"))
        if len(gpios) != 3 or handles.get(gpios[0]) != TLMM or gpios[1:] != [96, 0]:
            problems.append("%s gpios is not <&tlmm 96 GPIO_ACTIVE_HIGH>" % PPS)
        state = [handles.get(h) for h in cells(prop(PPS, "pinctrl-0"))]
        if len(state) != 1 or text(nodes.get(state[0] or "", {}).get("pins")) != "gpio96" \
                or text(nodes.get(state[0] or "", {}).get("function")) != "gpio":
            problems.append("%s pinctrl state is not gpio96 / function gpio" % PPS)
    want_status(PCIE0, "okay" if profile == "lab" else "disabled")
    return problems


def diff(reference, actual, ignore=VOLATILE):
    """Node/property paths that differ between two parsed trees, outside the ignored subtrees."""
    def skip(path):
        return any(path == i or path.startswith(i + "/") for i in ignore)
    out = []
    for path in sorted(set(reference) | set(actual)):
        if skip(path):
            continue
        a, b = reference.get(path), actual.get(path)
        if a is None or b is None:
            out.append(path + (" missing" if b is None else " added"))
            continue
        out += [path + ":" + name for name in sorted(set(a) | set(b)) if a.get(name) != b.get(name)]
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dtb", type=Path, help="merged lab.dtb/field.dtb or /sys/firmware/fdt")
    parser.add_argument("--profile", choices=("lab", "field"), required=True)
    parser.add_argument("--reference", type=Path, help="merged DTB to compare node by node (bench W-10)")
    args = parser.parse_args(argv)
    try:
        nodes = parse(args.dtb.read_bytes())
        report = {"dtb": str(args.dtb), "profile": args.profile, "problems": check(nodes, args.profile)}
        if args.reference:
            report["differs_from_reference"] = diff(parse(args.reference.read_bytes()), nodes)
    except (OSError, ValueError, struct.error) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    bad = report["problems"] or report.get("differs_from_reference")
    report["status"] = "BLOCKED" if bad else "OVERLAY_EFFECTS_PRESENT"
    print(json.dumps(report, indent=2))
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
