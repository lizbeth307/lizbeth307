#!/usr/bin/env python3
"""Runtime check of the gpredict +lab package in the sr-rx-packages runtime chroot (recipes/README.md).

check_repo.py runtime-check runs it as uid 1000 under unshare --net in a fresh chroot from the
pinned snapshot, with the package and its runtime dependencies installed offline. Standard library
only. It checks that:
- /usr/bin/gpredict resolves every library (ldd) and loads no libgps, no libhamlib and no libcurl;
- the package ships no bundled satellite data (no usr/share/gpredict/data/satdata files: Gpredict
  loads only what the srrx Gpredict bridge writes);
- the binary carries the lab refusals (no network TLE or transponder update, RX only radios, the
  rotctld full-buffer error) and none of the removed texts (IQRECORD, the CelesTrak, AMSAT and
  SatNOGS default URLs);
- the /etc/skel defaults hold [TLE] AUTO_UPDATE_FREQ=0 with an empty URL list and exactly one radio,
  Type 0 at 127.0.0.1:4532 (SDR++ rigctl_server) with every AOS/LOS/IQ signal off.
The GUI is never started (gtk_init needs a display): no device, no RF. The last stdout line is a
JSON object with ok true and no findings when everything holds. CI model only: no hardware PASS.
"""
import json
import os
import re
import subprocess
import sys

BINARY = "/usr/bin/gpredict"
SKEL = "/etc/skel/.config/Gpredict"
REQUIRED = (b"network TLE update is disabled in the SR-RX lab build",
            b"network transponder update is disabled in the SR-RX lab build",
            b"is not an RX only radio; refused by the SR-RX lab build",
            b"rotctld answer fills the")
FORBIDDEN = (b"IQRECORD", b"celestrak.org/NORAD", b"amsat.org/amsat/ftp", b"db.satnogs.org")
FORBIDDEN_LIBRARIES = re.compile(r"^(libgps|libhamlib|libcurl)", re.I)
RADIO = {"host": "127.0.0.1", "port": "4532", "type": "0", "ptt": "0", "signal_aos": "false", "signal_los": "false",
         "signal_aoiq": "false", "signal_loiq": "false"}


def run(argv, timeout=60):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def ini(text):
    sections, section = {}, ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        key, sep, value = line.partition("=")
        if sep:
            sections.setdefault(section, {}).setdefault(key.strip().lower(), []).append(value.strip())
    return sections


def libraries(findings):
    result = run(["ldd", BINARY])
    names = sorted({line.split()[0] for line in result.stdout.splitlines() if line.strip() and "=>" in line})
    missing = [line.split()[0] for line in result.stdout.splitlines() if "not found" in line]
    if result.returncode != 0 or missing:
        findings.append("ldd %s failed or misses libraries: %s" % (BINARY, ", ".join(missing) or result.stderr.strip()[-200:]))
    hits = [n for n in names if FORBIDDEN_LIBRARIES.match(n)]
    if hits:
        findings.append("gpredict loads " + ", ".join(hits))
    return {"libraries": names, "libcurl": any(n.startswith("libcurl") for n in names)}


def package_files(findings):
    listed = run(["dpkg-query", "-L", "gpredict"]).stdout.splitlines()
    bundled = [p for p in listed if p.startswith("/usr/share/gpredict/data/satdata/") and os.path.isfile(p)]
    if bundled:
        findings.append("bundled satellite data is installed: " + ", ".join(bundled[:5]))
    return {"files": len(listed), "satdata_files": len(bundled)}


def binary_texts(findings):
    with open(BINARY, "rb") as handle:
        data = handle.read()
    missing = [t.decode() for t in REQUIRED if t not in data]
    if missing:
        findings.append("gpredict lacks the lab refusal texts: " + "; ".join(missing))
    present = [t.decode() for t in FORBIDDEN if t in data]
    if present:
        findings.append("gpredict still carries removed texts: " + ", ".join(present))
    return {"required": len(REQUIRED) - len(missing), "forbidden_present": present}


def skeleton(findings):
    with open(os.path.join(SKEL, "gpredict.cfg"), encoding="ascii") as handle:
        config = ini(handle.read())
    tle = config.get("tle", {})
    if tle.get("auto_update_freq", [None])[-1] != "0" or tle.get("urls", [None])[-1] != "":
        findings.append("skel gpredict.cfg does not keep network TLE updates off")
    radios = sorted(os.listdir(os.path.join(SKEL, "hwconf")))
    if radios != ["SDRPP-RX.rig"]:
        findings.append("skel hwconf holds other radios: " + ", ".join(radios))
        return {"radios": radios}
    with open(os.path.join(SKEL, "hwconf", radios[0]), encoding="ascii") as handle:
        radio = ini(handle.read()).get("radio", {})
    wrong = sorted(k for k, v in RADIO.items() if radio.get(k, [None])[-1] != v)
    if wrong:
        findings.append("skel radio differs from RX only at 127.0.0.1:4532: " + ", ".join(wrong))
    return {"radios": radios}


def main():
    findings, report = [], {}
    for name, step in (("libraries", libraries), ("package", package_files), ("binary", binary_texts), ("skeleton", skeleton)):
        try:
            report[name] = step(findings)
        except (OSError, UnicodeError, subprocess.SubprocessError) as exc:  # missing file, timeout: a finding, not a traceback
            findings.append("%s check could not run: %s" % (name, exc))
    print(json.dumps({"ok": not findings, "findings": findings, "report": report, "uid": os.getuid(),
                      "scope": "CI model in the runtime chroot: no GUI, no device, no RF; hardware rows stay OPEN"}))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
