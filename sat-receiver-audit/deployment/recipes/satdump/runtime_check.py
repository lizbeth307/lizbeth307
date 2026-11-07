#!/usr/bin/env python3
"""Runtime checks of the installed SatDump +lab package (stdlib only; sr-rx-packages runtime chroot).

deployment/repo/check_repo.py runtime-check copies this file alone into a fresh noble arm64 chroot
from the pinned snapshot, installs the built satdump .deb offline together with the recipe's
ci.runtime_depends (strace, binutils) and runs it as uid 1000 under unshare --net --mount --pid.
Rows (packaging.json builder_checks; deployment/tests/test_satdump_recipe.py keeps them equal):

  plugin-set              satdump_pass.probe_argv (`satdump pipeline meteor_m2-x_lrpt --help`) under
                          strace: the *.so opened in the plugin directory are exactly the seven of the
                          allowlist, the help names satdump_pass.PROBE_MARKERS, no plugin load failure
  ldd                     readelf -dW and ldd of every ELF file of the package: no DT_RPATH, DT_RUNPATH
                          only /usr/lib/satdump/plugins (and present where a plugin library is needed),
                          nothing "not found", no SDR, USB or audio library
  no-connect              every satdump run below under strace %network: no connect(), sendto(),
                          sendmsg() or bind() outside AF_UNIX; the cs16 noise decode reads its input
  cli-forms               the satdump_pass decode argv (--key=value) and the space form (--key value,
                          patch 0001) on 2 s of synthetic cs16 noise: exit 0, both log samplerate 256000
                          and baseband_format cs16, no CLI11 error
  planted-pipelines-json  pipelines.json (syracuse3_tlm) and settings.json planted in the caller's
                          working directory and HOME: opened when satdump runs there (positive control),
                          never opened in the unit shape (empty working directory, private empty HOME)

Not run here: omm-csv (a host test against the pinned reader), lrpt-fixture and lrpt-cadu-cut
(BLOCKED_NO_LICENSED_FIXTURE: no recording with a stated licence), live-localhost (PENDING_DEVICE).
The last stdout line is one JSON object: ok, findings, checks, installed_digests. Run details go to
stderr (the runtime-check log). CI model on the arm64 builder: no RF, no hardware, nothing REVIEWED.
"""
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time

SATDUMP = "/usr/bin/satdump"
CORE = "/usr/lib/libsatdump_core.so"
PLUGIN_DIR = "/usr/lib/satdump/plugins"
PIPELINE_DIR = "/usr/share/satdump/resources/pipelines"
RESOURCES = "/usr/share/satdump/resources"
CONFIG = "/usr/share/satdump/satdump_cfg.json"
RUNPATH = "/usr/lib/satdump/plugins"
EXPECTED_PLUGINS = ("libmeteor_support.so", "libnoaa_metop_support.so", "libaws_support.so", "libelektro_arktika_support.so",
                    "libxrit_support.so", "libfengyun2_support.so", "libnet_source_support.so")
PIPELINES = ("Meteor-M.json", "MetOp.json", "AWS.json", "FengYun-2.json", "Elektro_Arktika.json")
PIPELINE = "meteor_m2-x_lrpt"
# srrx.satdump_pass: OUTPUT_RATE_HZ, PROBE_MARKERS, decode_argv/probe_argv and the unit's LC_ALL.
SAMPLERATE = 256000
PROBE_MARKERS = ("level", "input_file", "output_folder", "--samplerate", "--baseband_format")
NOISE_SECONDS = 2
NOISE_SEED = 20261107
# Logged by SatDump 1aedd60 when a plugin does not load (src-core/core/plugin.cpp) or a CLI argument
# does not parse (CLI11).
PLUGIN_FAILURES = ("failed to load", "Error loading", "ABI mismatch", "No Plugins loaded", "No valid plugin directory")
CLI_ERRORS = ("The following arguments were not expected", "Run with --help for more information", "ArgumentMismatch",
              "is required", "Could not convert")
# Library names that must not appear anywhere in a resolved dependency (receive-only: no SDR, USB or
# audio device library reaches SatDump).
FORBIDDEN_LIBRARIES = ("rtlsdr", "limesuite", "soapysdr", "libusb", "hackrf", "bladerf", "portaudio", "rtaudio", "airspy",
                       "libuhd", "libiio", "ad9361", "mirisdr", "sdrplay", "hydrasdr", "librfnm", "fobos")
TRACE = "%network,openat"
INET = ("AF_INET", "AF_INET6", "AF_PACKET", "AF_BLUETOOTH", "AF_CAN")
STATIC_ROWS = {"omm-csv": {"status": "HOST_TEST", "where": "deployment/tests/test_satdump_recipe.py OmmCsvReaderTests "
                                                         "(reader src-core/db/kepler/kepler_utils.cpp, blob bound by verify-source)"},
               "lrpt-fixture": {"status": "BLOCKED_NO_LICENSED_FIXTURE", "reason": "no Meteor-M LRPT recording with a stated licence; owner bench recording needed"},
               "lrpt-cadu-cut": {"status": "BLOCKED_NO_LICENSED_FIXTURE", "reason": "needs the same licensed recording"},
               "live-localhost": {"status": "PENDING_DEVICE", "reason": "RX-04-live on the Q6A: live unit and net_source on 127.0.0.1"}}
RUN_ROWS = ("plugin-set", "ldd", "no-connect", "cli-forms", "planted-pipelines-json")
PLANTED_PIPELINE = {"syracuse3_tlm": {"name": "SR-RX planted user pipeline (must never load in the unit)", "parameters": {},
                                      "work": {"baseband": {}, "soft": {"module": "psk_demod",
                                                                        "parameters": {"constellation": "bpsk", "symbolrate": 1000}}}}}
OUTPUT_LIMIT = 256 * 1024


def log(*parts):
    print(*parts, file=sys.stderr, flush=True)


def tool(argv, timeout=120):
    result = subprocess.run(argv, capture_output=True, text=True, errors="replace", timeout=timeout)
    return result.returncode, result.stdout


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_digest(top):
    """check_recipe.tree_digest / decoder_policy.satdump_tree_digest of an installed tree."""
    lines = []
    for path in sorted(Path(top).rglob("*")):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise ValueError("link or special file in " + str(top))
        if path.is_file():
            lines.append((path.relative_to(top).as_posix(), sha256(path)))
    return hashlib.sha256("".join("%s  %s\n" % (d, n) for n, d in sorted(lines)).encode("utf-8", "surrogateescape")).hexdigest()


def parse_trace(text):
    """[(pid, syscall, text)] of strace -f output; an <unfinished ...> call joined with its resumed rest."""
    calls, pending = [], {}
    for raw in text.splitlines():
        match = re.match(r"(?:(\d+) +)?(.*)$", raw)
        pid, rest = match.group(1) or "0", match.group(2)
        resumed = re.match(r"<\.\.\. (\w+) resumed>(.*)$", rest)
        if resumed:
            if pid in pending and pending[pid][0] == resumed.group(1):
                name, head = pending.pop(pid)
                calls.append((pid, name, head + resumed.group(2)))
            continue
        call = re.match(r"(\w+)\(", rest)
        if not call:
            continue  # signals, exits
        if rest.endswith("<unfinished ...>"):
            pending[pid] = (call.group(1), rest[:-len("<unfinished ...>")])
            continue
        calls.append((pid, call.group(1), rest))
    return calls


def result_of(text):
    match = re.search(r"\)\s+=\s+(-?\d+)", text)
    return int(match.group(1)) if match else None


def opened(calls):
    """[(path, result)] of every openat; the path is the second argument."""
    found = []
    for unused, name, text in calls:
        if name in ("openat", "openat2", "open"):
            match = re.match(r"\w+\((?:[^,\"]*, )?\"((?:[^\"\\]|\\.)*)\"", text)
            if match:
                found.append((match.group(1), result_of(text)))
    return found


def network(calls):
    """(findings, socket families) of the %network calls: a connection, datagram or bind outside AF_UNIX is a finding."""
    findings, sockets = [], set()
    for unused, name, text in calls:
        if name == "socket":
            match = re.match(r"socket\((AF_\w+|\d+)", text)
            sockets.add(match.group(1) if match else "?")
        elif name in ("connect", "sendto", "sendmsg", "sendmmsg", "bind"):
            families = re.findall(r"sa_family=(AF_\w+|\d+)", text)
            if any(f != "AF_UNIX" and f != "AF_NETLINK" for f in families):
                findings.append(name + " " + ",".join(families))
    return findings, sorted(sockets)


class Runner:
    """Every satdump command of this check runs through here: under strace, with a chosen working
    directory and HOME, LC_ALL=C.UTF-8 as in the decode unit, bounded output and time."""

    def __init__(self, base):
        self.base, self.count, self.network_findings, self.sockets, self.runs = Path(base), 0, [], set(), []

    def fresh(self, label):
        self.count += 1
        path = self.base / ("%02d-%s" % (self.count, label))
        path.mkdir(mode=0o700)
        return path

    def run(self, label, argv, cwd, home, timeout=300):
        trace = self.base / ("%02d-%s.trace" % (self.count, label))
        env = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": str(home), "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"}
        command = ["strace", "-f", "-qq", "-s", "4096", "-e", "trace=" + TRACE, "-o", str(trace)] + list(argv)
        started = time.monotonic()
        try:
            result = subprocess.run(command, cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
            code, output = result.returncode, result.stdout[-OUTPUT_LIMIT:].decode("utf-8", "replace")
        except subprocess.TimeoutExpired as exc:
            code, output = "timeout", (exc.stdout or b"")[-OUTPUT_LIMIT:].decode("utf-8", "replace")
        text = trace.read_text(encoding="utf-8", errors="replace") if trace.is_file() else ""
        calls = parse_trace(text)
        findings, sockets = network(calls)
        if not text:
            findings = ["no strace output (strace could not trace the command)"]
        self.network_findings += [label + ": " + f for f in findings]
        self.sockets.update(sockets)
        self.runs.append({"run": label, "exit": code, "argv": list(argv)[1:], "syscalls": len(calls),
                          "seconds": round(time.monotonic() - started, 1)})
        log("=== %s: exit %s, %d traced calls, cwd %s, HOME %s" % (label, code, len(calls), cwd, home))
        log(output[-12000:])
        return code, output, opened(calls)


def check_plugin_set(runner):
    cwd, home = runner.fresh("probe-cwd"), runner.fresh("probe-home")
    code, output, files = runner.run("probe", [SATDUMP, "pipeline", PIPELINE, "--help"], cwd, home, timeout=180)
    loaded = sorted({Path(p).name for p, r in files if p.startswith(PLUGIN_DIR + "/") and p.endswith(".so") and r is not None and r >= 0})
    findings = []
    if code != 0:
        findings.append("probe exit %s" % code)
    if loaded != sorted(EXPECTED_PLUGINS):
        findings.append("plugins opened %s, expected %s" % (loaded, sorted(EXPECTED_PLUGINS)))
    findings += ["probe marker missing: " + m for m in PROBE_MARKERS if m not in output]
    findings += ["plugin load failure logged: " + m for m in PLUGIN_FAILURES if m in output]
    pipelines = sorted({Path(p).name for p, r in files if p.startswith(PIPELINE_DIR + "/") and r is not None and r >= 0})
    if pipelines != sorted(PIPELINES):
        findings.append("pipelines opened %s, expected %s" % (pipelines, sorted(PIPELINES)))
    return {"status": "FAIL" if findings else "CI_PASS", "findings": findings, "plugins_opened": loaded, "pipelines_opened": pipelines}


def readelf(path):
    code, text = tool(["readelf", "-dW", path])
    if code:
        return None
    tags = {}
    for tag, value in re.findall(r"\((NEEDED|RUNPATH|RPATH|SONAME)\)\s+[^\[]*\[([^\]]*)\]", text):
        tags.setdefault(tag, []).append(value)
    return tags


def check_ldd(package_files):
    elves, findings = {}, []
    for path in package_files:
        try:
            with open(path, "rb") as stream:
                if stream.read(4) != b"\x7fELF":
                    continue
        except (IsADirectoryError, FileNotFoundError, PermissionError):
            continue
        tags = readelf(path)
        if tags is None:
            findings.append(path + ": readelf failed")
            continue
        code, text = tool(["ldd", path])
        resolved = []
        for line in text.splitlines():
            line = line.strip()
            if "not found" in line:
                findings.append(path + ": " + line)
            match = re.match(r"(\S+)(?: => (\S+))?", line)
            if match:
                resolved.append(match.group(2) or match.group(1))
        if code:
            findings.append(path + ": ldd exit %d" % code)
        if tags.get("RPATH"):
            findings.append(path + ": DT_RPATH " + ":".join(tags["RPATH"]))
        runpath = [p for value in tags.get("RUNPATH", []) for p in value.split(":")]
        if runpath and runpath != [RUNPATH]:
            findings.append(path + ": DT_RUNPATH " + ":".join(runpath))
        if any(n.endswith("_support.so") for n in tags.get("NEEDED", [])) and runpath != [RUNPATH]:
            findings.append(path + ": needs a plugin library without DT_RUNPATH " + RUNPATH)
        for name in tags.get("NEEDED", []) + resolved:
            lower = name.lower()
            if any(word in lower for word in FORBIDDEN_LIBRARIES):
                findings.append(path + ": forbidden library " + name)
        elves[path] = {"needed": tags.get("NEEDED", []), "runpath": runpath, "soname": tags.get("SONAME", [])}
    wanted = {SATDUMP, CORE} | {PLUGIN_DIR + "/" + n for n in EXPECTED_PLUGINS}
    missing = sorted(wanted - set(elves))
    if missing:
        findings.append("ELF files not found in the package: " + ", ".join(missing))
    return {"status": "FAIL" if findings else "CI_PASS", "findings": sorted(set(findings)), "elf_files": len(elves),
            "needed": {Path(p).name: v["needed"] for p, v in sorted(elves.items())},
            "runpath": {Path(p).name: v["runpath"] for p, v in sorted(elves.items())}}


def check_cli_forms(runner, noise):
    forms = {"equals": ["--samplerate=%d" % SAMPLERATE, "--baseband_format=cs16"],
             "space": ["--samplerate", str(SAMPLERATE), "--baseband_format", "cs16"]}
    results, findings, read_input = {}, [], True
    for label, tail in forms.items():
        cwd, home, out = runner.fresh("decode-%s-cwd" % label), runner.fresh("decode-%s-home" % label), runner.fresh("decode-%s-out" % label)
        argv = [SATDUMP, "pipeline", PIPELINE, "baseband", str(noise), str(out / "products")] + tail
        code, output, files = runner.run("decode-" + label, argv, cwd, home, timeout=900)
        parsed = {"samplerate": "- samplerate : %d" % SAMPLERATE in output, "baseband_format": '- baseband_format : "cs16"' in output}
        errors = [e for e in CLI_ERRORS if e in output]
        reads = any(p == str(noise) and r is not None and r >= 0 for p, r in files)
        read_input = read_input and reads
        results[label] = {"exit": code, "parsed": parsed, "cli_errors": errors, "read_input": reads,
                          "outputs": sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())[:40]}
        if code != 0:
            findings.append("%s form: exit %s" % (label, code))
        findings += ["%s form: %s not logged as parsed" % (label, k) for k, v in parsed.items() if not v]
        findings += ["%s form: CLI error %r" % (label, e) for e in errors]
        if not reads:
            findings.append("%s form: the decode never opened its input" % label)
    return {"status": "FAIL" if findings else "CI_PASS", "findings": findings, "forms": results}, read_input


def check_planted(runner):
    caller = runner.fresh("caller")
    caller_home = caller / "home"
    planted = [caller / "pipelines.json", caller / "settings.json", caller_home / ".config/satdump/pipelines.json",
               caller_home / ".config/satdump/settings.json"]
    for path in planted:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(PLANTED_PIPELINE if path.name == "pipelines.json" else {}) + "\n", encoding="utf-8")
    findings, details = [], {}
    # Positive controls: the same binary does read user files from its working directory and HOME.
    code, output, files = runner.run("planted-cwd", [SATDUMP, "pipeline", "--help"], caller, runner.fresh("planted-cwd-home"), timeout=180)
    names = {p for p, unused in files}
    details["cwd_control"] = {"exit": code, "opened": sorted(n for n in names if n in ("pipelines.json", "settings.json")),
                              "syracuse3_tlm_listed": "syracuse3_tlm" in output}
    if code != 0 or not {"pipelines.json", "settings.json"} <= names:
        findings.append("positive control (working directory): planted files not opened, exit %s" % code)
    code, output, files = runner.run("planted-home", [SATDUMP, "pipeline", "--help"], runner.fresh("planted-home-cwd"), caller_home, timeout=180)
    names = {p for p, unused in files}
    wanted = {str(caller_home / ".config/satdump/pipelines.json"), str(caller_home / ".config/satdump/settings.json")}
    details["home_control"] = {"exit": code, "opened": sorted(names & wanted), "syracuse3_tlm_listed": "syracuse3_tlm" in output}
    if code != 0 or not wanted <= names:
        findings.append("positive control (HOME): planted files not opened, exit %s" % code)
    # The unit shape (srrx.satdump_pass.unit_lines): an empty working directory and a private empty HOME,
    # started by a caller whose working directory and HOME hold the planted files.
    for label, argv in (("unit-list", [SATDUMP, "pipeline", "--help"]), ("unit-probe", [SATDUMP, "pipeline", PIPELINE, "--help"])):
        cwd, home = runner.fresh(label + "-cwd"), runner.fresh(label + "-home")
        code, output, files = runner.run(label, argv, cwd, home, timeout=180)
        user_files = sorted(p for p, unused in files if Path(p).name in ("pipelines.json", "settings.json")
                            or (Path(p).name == "satdump_cfg.json" and p != CONFIG) or p.startswith(str(caller)))
        details[label] = {"exit": code, "user_files_opened": user_files, "syracuse3_tlm_listed": "syracuse3_tlm" in output}
        if code != 0:
            findings.append("%s: exit %s" % (label, code))
        if user_files:
            findings.append("%s: opened %s" % (label, ", ".join(user_files)))
        if "syracuse3_tlm" in output:
            findings.append(label + ": syracuse3_tlm listed")
    return {"status": "FAIL" if findings else "CI_PASS", "findings": findings, **details}


def installed_digests():
    """The record_digests fields recomputed from the installed files (recipe_sha256 is not in this chroot)."""
    return {"sha256": sha256(SATDUMP), "core_sha256": sha256(CORE), "resources_sha256": tree_digest(RESOURCES),
            "plugins": {n: sha256(PLUGIN_DIR + "/" + n) for n in EXPECTED_PLUGINS},
            "pipelines": {n: sha256(PIPELINE_DIR + "/" + n) for n in PIPELINES}, "config_sha256": sha256(CONFIG)}


def main():
    report = {"ok": False, "findings": [], "component": "satdump", "checks": {}, "hardware_ready": False,
              "scope": "CI model on the arm64 builder: the installed package in a fresh chroot, offline, synthetic noise only; "
                       "no RF, no hardware, no decode fixture."}
    checks = report["checks"]
    if os.getuid() == 0:
        report["findings"].append("runs as root")
    base = Path(tempfile.mkdtemp(prefix="srrx-satdump-runtime-", dir="/tmp"))
    runner = Runner(base)
    try:
        code, listing = tool(["dpkg-query", "-L", "satdump"])
        package_files = [line for line in listing.splitlines() if line.startswith("/") and os.path.isfile(line) and not os.path.islink(line)]
        if code or not package_files:
            report["findings"].append("satdump is not installed")
        code, unused = tool(["strace", "-f", "-qq", "-o", str(base / "preflight.trace"), "-e", "trace=" + TRACE, "/bin/true"])
        report["strace_preflight"] = {"exit": code, "traced": (base / "preflight.trace").is_file()}
        noise = base / "noise.cs16"
        noise.write_bytes(random.Random(NOISE_SEED).randbytes(SAMPLERATE * 4 * NOISE_SECONDS))  # int16 I/Q pairs
        checks["plugin-set"] = check_plugin_set(runner)
        checks["ldd"] = check_ldd(package_files)
        checks["cli-forms"], read_input = check_cli_forms(runner, noise)
        checks["planted-pipelines-json"] = check_planted(runner)
        findings = list(runner.network_findings) + ([] if read_input else ["the noise decode did not read its input"])
        checks["no-connect"] = {"status": "FAIL" if findings else "CI_PASS", "findings": findings, "socket_families": sorted(runner.sockets),
                                "runs": runner.runs}
        report["installed_digests"] = installed_digests()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report["findings"].append("runtime check error: %s: %s" % (type(exc).__name__, exc))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    for name in RUN_ROWS:
        status = checks.get(name, {}).get("status", "NOT_RUN")
        if status != "CI_PASS":
            report["findings"].append(name + " " + status)
    checks.update({name: dict(row) for name, row in STATIC_ROWS.items()})
    report["ok"] = not report["findings"]
    print(json.dumps(report, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
