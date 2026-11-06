#!/usr/bin/env python3
"""Field EDID edid/field.bin from the documented timings (STACK.md:81 C12, STACK.md:1035).

One EDID 1.4 base block, no CTA extension (no CEA VIC), established timings 00 00 00,
all eight standard timings 01 01, no CVT 3-byte or range-limits descriptor and the
continuous-frequency bit cleared, so the sink offers exactly two 1920x1080 modes in
the order the kernel tries them:

  DTD1 151.50 MHz, H 1920/88/44/148 (2200), V 1080/27/5/36 (1148): 68.864 kHz, 59.986 Hz
  DTD2 127.90 MHz, H 1920/88/44/148 (2200), V 1080/4/5/36 (1125):  58.136 kHz, 51.677 Hz

STACK gives the DTD2 horizontal split only as the 2200 total; it is taken equal to DTD1
(the same htotal). Sync polarity +H/+V follows the CEA-861 1080p timings these modes
derive from. Neither split nor polarity is a panel measurement: the Wisecoco timing
sheet and the bench (Д-05, modetest/debugfs, E-field probe) decide, and only the
pixel clocks and totals are fixed. Other fields are neutral conventions, not panel
data: manufacturer "LNX" as the Linux kernel's own generated EDIDs use, product 0001,
serial 0, year 2026, digital input with undefined depth/interface, size undefined
(the two published active areas disagree: components/display_hmi.md:13), gamma 2.2,
sRGB default with sRGB primaries, DTD1 marked as the native/preferred timing.

Refused: 128.70 MHz (x12 = 1544.4 MHz, Inmarsat-C), 148.5 MHz (start-up only), any
clock outside the clean windows 123.89-128.04 and 148.13-153.22 MHz (STACK.md:1035).
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
FIELD_BIN = HERE / "edid/field.bin"
FIELD_RECORD = HERE / "edid/field.json"

# (pixel clock kHz, h active, h front porch, h sync, h back porch, v active, v fp, v sync, v bp)
TIMINGS = (
    ("DTD1", 151500, 1920, 88, 44, 148, 1080, 27, 5, 36),
    ("DTD2", 127900, 1920, 88, 44, 148, 1080, 4, 5, 36),
)
CLEAN_WINDOWS_KHZ = ((123890, 128040), (148130, 153220))
BANNED_KHZ = {128700: "128.70 MHz x12 = 1544.4 MHz (Inmarsat-C) is forbidden",
              148500: "148.5 MHz is the start-up mode only, never a field DTD"}
MANUFACTURER = "LNX"
PRODUCT_CODE = 0x0001
YEAR = 2026
NAME = "SRRX FIELD"
# sRGB primaries and D65 white (IEC 61966-2-1), x/y.
CHROMA = {"rx": 0.640, "ry": 0.330, "gx": 0.300, "gy": 0.600, "bx": 0.150, "by": 0.060, "wx": 0.3127, "wy": 0.3290}


class EdidError(ValueError):
    pass


def check_timing(timing):
    name, clock, hact, hfp, hsync, hbp, vact, vfp, vsync, vbp = timing
    if clock in BANNED_KHZ:
        raise EdidError(name + ": " + BANNED_KHZ[clock])
    if not any(lo <= clock <= hi for lo, hi in CLEAN_WINDOWS_KHZ):
        raise EdidError(name + ": %.2f MHz is outside the clean pixel-clock windows" % (clock / 1000))
    if (hact, vact) != (1920, 1080):
        raise EdidError(name + ": the field EDID offers 1920x1080 only")
    for value, limit in ((hfp, 1023), (hsync, 1023), (vfp, 63), (vsync, 63), (hfp + hsync + hbp, 4095), (vfp + vsync + vbp, 4095)):
        if not 0 < value <= limit:
            raise EdidError(name + ": porch/sync value does not fit a detailed timing descriptor")
    return {"name": name, "pixel_clock_khz": clock, "h_total": hact + hfp + hsync + hbp,
            "v_total": vact + vfp + vsync + vbp,
            "line_khz": round(clock / (hact + hfp + hsync + hbp), 3),
            "refresh_hz": round(clock * 1000 / ((hact + hfp + hsync + hbp) * (vact + vfp + vsync + vbp)), 3)}


def _dtd(timing):
    check_timing(timing)
    name, clock, hact, hfp, hsync, hbp, vact, vfp, vsync, vbp = timing
    hblank, vblank = hfp + hsync + hbp, vfp + vsync + vbp
    units = clock // 10  # 10 kHz units
    return bytes([
        units & 0xFF, units >> 8,
        hact & 0xFF, hblank & 0xFF, (hact >> 8) << 4 | hblank >> 8,
        vact & 0xFF, vblank & 0xFF, (vact >> 8) << 4 | vblank >> 8,
        hfp & 0xFF, hsync & 0xFF, (vfp & 0x0F) << 4 | (vsync & 0x0F),
        (hfp >> 8) << 6 | (hsync >> 8) << 4 | (vfp >> 4) << 2 | (vsync >> 4),
        0, 0, 0,          # image size undefined (active area not measured)
        0, 0,             # no border
        0x1E,             # non-interlaced, digital separate sync, +V, +H
    ])


def _chroma():
    v = {k: round(x * 1024) for k, x in CHROMA.items()}
    low1 = (v["rx"] & 3) << 6 | (v["ry"] & 3) << 4 | (v["gx"] & 3) << 2 | (v["gy"] & 3)
    low2 = (v["bx"] & 3) << 6 | (v["by"] & 3) << 4 | (v["wx"] & 3) << 2 | (v["wy"] & 3)
    return bytes([low1, low2] + [v[k] >> 2 for k in ("rx", "ry", "gx", "gy", "bx", "by", "wx", "wy")])


def build(timings=TIMINGS):
    if [t[0] for t in timings] != ["DTD1", "DTD2"]:
        raise EdidError("exactly DTD1 (151.50 MHz) then DTD2 (127.90 MHz)")
    vendor = 0
    for letter in MANUFACTURER:
        vendor = vendor << 5 | (ord(letter) - 64)
    name = NAME.encode("ascii") + b"\n"
    block = bytearray()
    block += b"\x00\xff\xff\xff\xff\xff\xff\x00"
    block += bytes([vendor >> 8, vendor & 0xFF, PRODUCT_CODE & 0xFF, PRODUCT_CODE >> 8, 0, 0, 0, 0])
    block += bytes([0, YEAR - 1990, 1, 4])           # week unspecified, year, EDID 1.4
    block += bytes([0x80, 0, 0, 120, 0x06])          # digital; size undefined; gamma 2.2; sRGB, preferred=native
    block += _chroma()
    block += b"\x00\x00\x00"                         # established timings: none
    block += b"\x01\x01" * 8                         # standard timings: unused
    block += _dtd(timings[0]) + _dtd(timings[1])
    block += b"\x00\x00\x00\xfc\x00" + name + b" " * (13 - len(name))   # display product name
    block += b"\x00\x00\x00\x10\x00" + b"\x00" * 13                    # dummy descriptor
    block += b"\x00"                                 # no extension blocks (no CTA)
    block.append((-sum(block)) & 0xFF)
    if len(block) != 128 or sum(block) & 0xFF:
        raise EdidError("internal EDID length/checksum error")
    return bytes(block)


def decode(data):
    """The fields this project relies on, read back from bytes (tests and doctor-style checks)."""
    if len(data) != 128 or data[:8] != b"\x00\xff\xff\xff\xff\xff\xff\x00" or sum(data) & 0xFF:
        raise EdidError("not one checksummed EDID base block")
    out = {"version": (data[18], data[19]), "extensions": data[126], "established": data[35:38].hex(),
           "standard": data[38:54].hex(), "continuous_frequency": bool(data[24] & 1), "dtds": []}
    for offset in (54, 72, 90, 108):
        d = data[offset:offset + 18]
        clock = int.from_bytes(d[0:2], "little")
        if not clock:
            out.setdefault("descriptors", []).append(d[3])
            continue
        hact, hblank = d[2] | (d[4] >> 4) << 8, d[3] | (d[4] & 0x0F) << 8
        vact, vblank = d[5] | (d[7] >> 4) << 8, d[6] | (d[7] & 0x0F) << 8
        hfp, hsync = d[8] | (d[11] >> 6) << 8, d[9] | ((d[11] >> 4) & 3) << 8
        vfp, vsync = d[10] >> 4 | ((d[11] >> 2) & 3) << 4, (d[10] & 0x0F) | (d[11] & 3) << 4
        out["dtds"].append({"pixel_clock_khz": clock * 10, "h": (hact, hfp, hsync, hblank - hfp - hsync),
                            "v": (vact, vfp, vsync, vblank - vfp - vsync), "flags": d[17]})
    return out


def record(data):
    return {"schema_version": 1, "kind": "srrx_field_edid", "file": "field.bin", "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "timings": [check_timing(t) for t in TIMINGS],
            "source": "STACK.md:81 (C12), STACK.md:1035; generated by deployment/system/edid_field.py",
            "bench": "OPEN: Д-05 panel acceptance (modetest/kmsprint two modes, /sys/class/drm/card1-HDMI-A-1/edid == field.bin)"}


def stale():
    """Committed field.bin / field.json that no longer equal the generator output."""
    data = build()
    problems = []
    if not FIELD_BIN.is_file() or FIELD_BIN.read_bytes() != data:
        problems.append(str(FIELD_BIN.relative_to(HERE)) + " differs from the generator")
    try:
        committed = json.loads(FIELD_RECORD.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        committed = None
    if committed != record(data):
        problems.append(str(FIELD_RECORD.relative_to(HERE)) + " differs from the generator")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the committed files are stale")
    parser.add_argument("--output", type=Path, help="write field.bin here instead of the committed path")
    args = parser.parse_args(argv)
    if args.check:
        problems = stale()
        print(json.dumps({"status": "STALE" if problems else "EDID_MATCHES_GENERATOR", "problems": problems}, indent=2))
        return 2 if problems else 0
    data = build()
    if args.output:
        args.output.write_bytes(data)
    else:
        FIELD_BIN.parent.mkdir(exist_ok=True)
        FIELD_BIN.write_bytes(data)
        FIELD_RECORD.write_text(json.dumps(record(data), indent=2) + "\n", encoding="utf-8", newline="\n")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(record(data), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
