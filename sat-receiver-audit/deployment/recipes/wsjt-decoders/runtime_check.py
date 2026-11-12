#!/usr/bin/env python3
"""Runtime check of lab-wsjt-decoders in the sr-rx-packages runtime chroot (stdlib only).

check_repo.py runtime-check runs it as uid 1000 under `unshare --net` in a fresh chroot from the
pinned snapshot, after lab-wsjt-decoders and its Depends were installed offline, with --samples
<dir>: the ci.tag_samples paths of recipe.json exported from a clone of tag wsjtx-2.7.0 (the
locked commit b4f9a43; the release tarball has no samples/). It checks that

  - /usr/bin/jt9, /usr/bin/wsprd and /usr/bin/wsjtx_app_version are the PATH entries;
  - wsjtx_app_version --version prints exactly "WSJT-X 2.7.0" (the line OpenWebRX+ reads);
  - no wsjtx, rigctl/rigctld/rigctlcom, rotctl/rotctld or WSJT-X utility is on PATH;
  - the package Depends and the ldd closure of jt9/wsprd name no libhamlib;
  - jt9 -8 decodes FT8 and wsprd decodes WSPR from the samples (at least one message each).

The last stdout line is one JSON object ({"ok": true, "findings": []} on success, the hook
contract of build_recipe.run_hook); the decode counts in it are a CI model on the arm64
builder, not an on-air, device or hardware result. Decoded messages are printed only as counts.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

# The recipe's ci.tag_samples, in this order (deployment/tests/test_selftest.py checks they agree).
FT8_SAMPLE = "samples/FT8/210703_133430.wav"
WSPR_SAMPLE = "samples/WSPR/150426_0918.wav"
SAMPLES = (FT8_SAMPLE, WSPR_SAMPLE)
PACKAGE = "lab-wsjt-decoders"
BINARIES = ("jt9", "wsprd", "wsjtx_app_version")
STUB_OUTPUT = "WSJT-X 2.7.0\n"
# WSJT-X GUI, Hamlib rig/rotator tools and the WSJT-X utilities (encoders/simulators) that the
# recipe never builds; none may be reachable on PATH next to the decoders.
FORBIDDEN_ON_PATH = ("wsjtx", "rigctl", "rigctld", "rigctlcom", "rotctl", "rotctld", "jt9code", "ft8code", "ft4code", "wsprcode",
                     "ft8sim", "ft4sim", "wsprsim", "fst4sim", "q65sim", "message_aggregator", "udp_daemon")
# lib/decoder.f90 ft8_decoded, format 1001: i6.6,i4,f5.1,i5,' ~ ',1x,a37,1x,a2
FT8_LINE = re.compile(r"^(\d{6})\s*(-?\d+)\s+(-?\d+\.\d)\s+(\d+) ~  (\S.*?)\s*$")
# lib/wsprd/wsprd.c: "%4s %3.0f %4.1f %10.6f %2d  %-s \n" (time, snr, dt, frequency, drift, message)
WSPR_LINE = re.compile(r"^\s*(\S{1,6})\s+(-?\d+)\s+(-?\d+\.\d)\s+(-?\d+\.\d{6})\s+(-?\d+)\s+(\S.*?)\s*$")
# Both decoders end a pass with this marker (jt9 appends its counts: "<DecodeFinished>   2   2        0").
FINISHED = "<DecodeFinished>"
TIMEOUT = 900


def ft8_messages(stdout):
    """Decoded FT8 messages of `jt9 -8` output, in order (the early passes print only new ones)."""
    return [m.group(5) for m in map(FT8_LINE.match, stdout.splitlines()) if m]


def finished(stdout):
    """True when the decoder printed its end-of-pass marker."""
    return any(line.startswith(FINISHED) for line in stdout.splitlines())


def wspr_messages(stdout):
    """Decoded WSPR messages of wsprd output: the lines before <DecodeFinished>."""
    lines = stdout.splitlines()
    end = next((i for i, line in enumerate(lines) if line.startswith(FINISHED)), len(lines))
    return [m.group(6) for m in map(WSPR_LINE.match, lines[:end]) if m]


def hamlib_libraries(ldd_output):
    """Library names of an ldd listing that are Hamlib's (libhamlib*)."""
    return sorted({line.split()[0] for line in ldd_output.splitlines() if line.strip().startswith("libhamlib")})


def run(argv, cwd=None):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT)


def decode(program_argv, sample, work, parse):
    """Copy the sample into a fresh writable directory (jt9/wsprd write wisdom, timer and spot
    files next to it), run the decoder there and parse its stdout."""
    work.mkdir()
    local = work / Path(sample).name
    shutil.copyfile(sample, local)
    try:
        result = run(program_argv + [str(local)], cwd=work)
    except subprocess.TimeoutExpired as exc:
        result = subprocess.CompletedProcess(exc.cmd, -1, "", "timed out after %d s\n" % TIMEOUT)
    messages = parse(result.stdout)
    return {"exit": result.returncode, "decodes": len(messages), "unique_messages": len(set(messages)),
            "finished": finished(result.stdout)}, result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--samples", type=Path, required=True, help="the exported ci.tag_samples tree of this recipe")
    args = parser.parse_args()
    findings, report = [], {"package": PACKAGE, "scope": "CI model on the arm64 builder: decodes of the upstream tag samples; "
                            "no RF, no device, no hardware", "hardware_ready": False}
    paths = {name: shutil.which(name) for name in BINARIES}
    report["paths"] = paths
    findings += ["%s is not /usr/bin/%s on PATH" % (n, n) for n, p in paths.items() if p != "/usr/bin/" + n]
    present = sorted(n for n in FORBIDDEN_ON_PATH if shutil.which(n))
    report["forbidden_on_path"] = present
    findings += ["forbidden program on PATH: " + n for n in present]

    stub = run(["wsjtx_app_version", "--version"]) if paths["wsjtx_app_version"] else None
    report["app_version"] = None if stub is None else {"exit": stub.returncode, "stdout": stub.stdout[:64]}
    if stub is None or stub.returncode != 0 or stub.stdout != STUB_OUTPUT:
        findings.append("wsjtx_app_version --version does not print exactly " + STUB_OUTPUT.strip())

    depends = run(["dpkg-query", "-W", "-f", "${Depends}", PACKAGE])
    report["depends"] = depends.stdout.strip()
    if depends.returncode != 0 or not depends.stdout.strip():
        findings.append(PACKAGE + " is not installed or has no Depends")
    elif "hamlib" in depends.stdout.lower():
        findings.append(PACKAGE + " Depends names Hamlib")
    linked = {}
    for name in ("jt9", "wsprd"):
        if paths[name]:
            listing = run(["ldd", paths[name]])
            linked[name] = hamlib_libraries(listing.stdout)
            if listing.returncode != 0 or "not found" in listing.stdout:
                findings.append(name + ": ldd failed or a library is missing")
            if linked[name]:
                findings.append(name + " loads Hamlib")
    report["hamlib_libraries"] = linked

    samples = {sample: args.samples / sample for sample in SAMPLES}
    missing = [s for s, p in samples.items() if not p.is_file()]
    findings += ["tag sample missing: " + s for s in missing]
    if paths["jt9"] and paths["wsprd"] and not missing:
        with tempfile.TemporaryDirectory(prefix="srrx-wsjt-") as temporary:
            work = Path(temporary)
            ft8, ft8_run = decode(["jt9", "-8", "-d", "3", "-a", str(work / "ft8"), "-t", str(work / "ft8")],
                                  samples[FT8_SAMPLE], work / "ft8", ft8_messages)
            wspr, wspr_run = decode(["wsprd", "-a", str(work / "wspr")], samples[WSPR_SAMPLE], work / "wspr", wspr_messages)
        report["ft8"], report["wspr"] = dict(ft8, sample=FT8_SAMPLE), dict(wspr, sample=WSPR_SAMPLE)
        for mode, result, completed in (("FT8", ft8, ft8_run), ("WSPR", wspr, wspr_run)):
            print("%s (CI model): exit %d, %d decodes, %d unique messages, finished %s"
                  % (mode, result["exit"], result["decodes"], result["unique_messages"], result["finished"]))
            if result["exit"] != 0 or result["decodes"] < 1:
                findings.append("%s decode of the tag sample failed: exit %d, %d decodes" % (mode, result["exit"], result["decodes"]))
                sys.stdout.write(completed.stderr[-2000:])
    report.update(ok=not findings, findings=findings, uid=os.getuid())
    print(json.dumps(report, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
