#!/usr/bin/env python3
"""Runtime check of the sdrpp +lab package in the sr-rx-packages runtime chroot (recipes/README.md).

check_repo.py runtime-check runs it as uid 1000 under unshare --net in a fresh chroot from the
pinned snapshot, with the package and its runtime dependencies installed offline. Standard library
only. It checks that:
- the installed plugin directory holds exactly the allowlisted module files (receive-only-policy.json
  components.sdrpp.allow_plugins; nothing else, no other file type);
- rtl_sdr_source.so carries no bias-tee or direct-sampling control (lab patch 0001): no biasT key,
  no Bias T or Direct Sampling label and no rtlsdr_set_bias_tee import, while the directSampling key
  (always written as 0) is still there;
- rtl_sdr_source.so resolves librtlsdr.so.2 to the lab librtlsdr2 package (+labN version) and never
  to librtlsdr.so.0;
- `sdrpp --help` exits 0, and `sdrpp --server` exits non-zero with the lab refusal before it
  creates the root directory it was given (lab patch 0002).
The GUI is never started: no display, no device, no RF. The last stdout line is a JSON object with
ok true and no findings when everything holds. CI model only: no hardware PASS.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

PLUGINS = "/usr/lib/sdrpp/plugins"
BINARY = "/usr/bin/sdrpp"
ALLOWED = sorted(["radio", "audio_sink", "frequency_manager", "rtl_sdr_source", "airspyhf_source", "file_source",
                  "network_source", "soapy_source", "rigctl_server"])
RTL_FORBIDDEN = (b"biasT", b"Bias T", b"rtlsdr_set_bias_tee", b"Direct Sampling")
RTL_REQUIRED = (b"directSampling",)
REFUSAL = "Server mode is disabled in the SR-RX receive-only lab build"
LAB_VERSION = re.compile(r"\+lab[1-9][0-9]*\Z")
LDD_LINE = re.compile(r"^\s*(\S+)\s+=>\s+(\S+)\s+\(0x[0-9a-f]+\)\s*$")


def run(argv, timeout=60, cwd=None, home=None):
    # sdrpp builds its default root from $HOME (core/src/command_args.cpp:13): give it a scratch one.
    env = dict(os.environ, HOME=home) if home else None
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, cwd=cwd, env=env)


def plugin_directory(findings):
    names = sorted(os.listdir(PLUGINS))
    modules = sorted(n[:-3] for n in names if n.endswith(".so") and os.path.isfile(os.path.join(PLUGINS, n))
                     and not os.path.islink(os.path.join(PLUGINS, n)))
    others = sorted(n for n in names if not (n.endswith(".so") and n[:-3] in modules))
    if modules != ALLOWED:
        findings.append("plugin directory differs from the allowlist: extra %s, missing %s"
                        % (sorted(set(modules) - set(ALLOWED)), sorted(set(ALLOWED) - set(modules))))
    if others:
        findings.append("plugin directory holds other entries: " + ", ".join(others))
    return modules


def rtl_module(findings):
    path = os.path.join(PLUGINS, "rtl_sdr_source.so")
    with open(path, "rb") as handle:
        data = handle.read()
    hits = [t.decode() for t in RTL_FORBIDDEN if t in data]
    if hits:
        findings.append("rtl_sdr_source.so still carries bias-tee or direct-sampling controls: " + ", ".join(hits))
    missing = [t.decode() for t in RTL_REQUIRED if t not in data]
    if missing:
        findings.append("rtl_sdr_source.so lacks the expected config key: " + ", ".join(missing))
    result = run(["ldd", path])
    resolved = {}
    for line in result.stdout.splitlines():
        match = LDD_LINE.match(line)
        if match:
            resolved[match.group(1)] = match.group(2)
    if "librtlsdr.so.2" not in resolved:
        findings.append("rtl_sdr_source.so does not resolve librtlsdr.so.2: " + result.stdout.strip()[-300:])
        return {}
    if any(name.startswith("librtlsdr.so.0") for name in resolved):
        findings.append("rtl_sdr_source.so loads librtlsdr.so.0")
    real = os.path.realpath(resolved["librtlsdr.so.2"])
    candidates = [real] + ([real[len("/usr"):]] if real.startswith("/usr/") else ["/usr" + real])
    owner = None
    for candidate in candidates:
        query = run(["dpkg-query", "-S", candidate])
        if query.returncode == 0 and query.stdout.strip():
            owner = query.stdout.split(":", 1)[0].strip()
            break
    version = run(["dpkg-query", "-W", "-f", "${Version}", owner]).stdout.strip() if owner else ""
    if owner != "librtlsdr2" or not LAB_VERSION.search(version):
        findings.append("librtlsdr.so.2 of rtl_sdr_source.so is not the lab librtlsdr2: %s from %s %s" % (real, owner, version))
    return {"librtlsdr.so.2": real, "package": owner, "version": version}


def binary(findings):
    report = {}
    scratch = tempfile.mkdtemp(prefix="sdrpp-check-")
    helped = run([BINARY, "--help"], timeout=30, cwd=scratch, home=scratch)
    report["help_exit"] = helped.returncode
    if helped.returncode != 0:
        findings.append("sdrpp --help exited %d: %s" % (helped.returncode, (helped.stdout + helped.stderr).strip()[-300:]))
    root = os.path.join(scratch, "root")
    served = run([BINARY, "--server", "-r", root], timeout=30, cwd=scratch, home=scratch)
    output = served.stdout + served.stderr
    report["server_exit"] = served.returncode
    if served.returncode == 0 or REFUSAL not in output:
        findings.append("sdrpp --server was not refused (exit %d): %s" % (served.returncode, output.strip()[-300:]))
    if os.path.exists(root):
        findings.append("sdrpp --server created its root directory before refusing")
    return report


def main():
    findings, report = [], {}
    for name, step in (("modules", plugin_directory), ("rtl_sdr_source", rtl_module), ("binary", binary)):
        try:
            report[name] = step(findings)
        except (OSError, subprocess.SubprocessError) as exc:  # missing file, timeout: a finding, not a traceback
            findings.append("%s check could not run: %s" % (name, exc))
    print(json.dumps({"ok": not findings, "findings": findings, "report": report, "uid": os.getuid(),
                      "scope": "CI model in the runtime chroot: no GUI, no device, no RF; hardware rows stay OPEN"}))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
