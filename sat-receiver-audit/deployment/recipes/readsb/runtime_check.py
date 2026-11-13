#!/usr/bin/env python3
"""Runtime check of the readsb +lab package (check_repo.py runtime-check, sr-rx-packages lab-light).

Runs as uid 1000 in the offline runtime chroot (unshare --net, only loopback) after the package was
installed with dpkg -i from the build output; binutils comes from ci.runtime_depends. Checks: the
installed /usr/bin/readsb reports the lab version; its DT_NEEDED entries are exactly within the
RTL-SDR/libusb/zlib/zstd/libc set (no libbladeRF, libhackrf, libiio, libSoapySDR, ncurses, TLS);
it imports no rtlsdr_set_bias_tee; device type rtlsdr is compiled in (with no receiver in the
chroot it stops with "no supported devices"), and bladerf, hackrf, plutosdr and soapysdr are not
(the option parser refuses them). The last stdout line is the JSON report (ok, findings).
A CI model on the arm64 builder: no receiver, no RF, no hardware PASS.
"""
import json
import re
import subprocess
import sys

BINARY = "/usr/bin/readsb"
VERSION = "3.16.17+lab1"
# Shared objects readsb links (Makefile:36 -pthread -lm -lrt -lzstd, :51 -lz, :146 -lrtlsdr -lusb-1.0);
# libpthread and librt are part of libc.so.6 on noble (glibc 2.39), and the arm64 build also names
# glibc's dynamic loader ld-linux-aarch64.so.1 (seen in CI run 42406849942); libusb-1.0 is not
# a direct entry (readsb calls only librtlsdr; linked --as-needed).
ALLOWED_NEEDED = ("librtlsdr.so.2", "libusb-1.0.so.0", "libzstd.so.1", "libz.so.1", "libm.so.6", "libc.so.6", "ld-linux-aarch64.so.1")
FORBIDDEN_SYMBOLS = ("rtlsdr_set_bias_tee", "bladerf_open", "hackrf_open", "SoapySDRDevice_make", "iio_create_context")
ABSENT_TYPES = ("bladerf", "hackrf", "plutosdr", "soapysdr")
TIMEOUT_S = 30


def run(argv):
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, ""
    return done.returncode, done.stdout + done.stderr


def main():
    findings, report = [], {}
    code, text = run(["readelf", "-d", "--dyn-syms", "-W", BINARY])
    if code != 0:
        findings.append("readelf failed on " + BINARY)
    else:
        needed = re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]]+)\]", text)
        report["dt_needed"] = needed
        outside = sorted(set(needed) - set(ALLOWED_NEEDED))
        if outside:
            findings.append("DT_NEEDED outside the allowlist: " + ", ".join(outside))
        if "librtlsdr.so.2" not in needed:
            findings.append("readsb does not need the lab librtlsdr.so.2")
        imported = sorted({s for s in FORBIDDEN_SYMBOLS if re.search(r"\bUND\s+" + re.escape(s) + r"\b", text)})
        if imported:
            findings.append("forbidden SDR or bias-tee symbol imported: " + ", ".join(imported))
    code, text = run([BINARY, "--version"])
    report["version_exit"] = code
    if code != 0 or VERSION not in text:
        findings.append("readsb --version does not report " + VERSION)
    code, text = run([BINARY, "--device-type", "rtlsdr", "--quiet"])
    report["rtlsdr_exit"] = code
    if code in (0, None) or "no supported devices found" not in text:
        findings.append("device type rtlsdr is not compiled in, or readsb did not stop without a receiver")
    for kind in ABSENT_TYPES:
        code, text = run([BINARY, "--device-type", kind, "--quiet"])
        report[kind + "_exit"] = code
        if code in (0, None) or "Unknown device type" not in text:
            findings.append("device type " + kind + " is not refused by the option parser")
    print(json.dumps({"ok": not findings, "findings": findings, "component": "readsb", "version": VERSION,
                      "checks": report, "hardware_ready": False}))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
