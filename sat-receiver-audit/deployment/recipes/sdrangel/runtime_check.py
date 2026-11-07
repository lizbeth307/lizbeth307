#!/usr/bin/env python3
"""Runtime check of the SDRangel +lab packages (check_repo.py runtime-check, recipes/README.md).

check_repo.py installs sdrangel-common, sdrangel and sdrangelsrv offline in a fresh chroot from
the pinned snapshot and runs this file alone as uid 1000 under `unshare --net` (loopback only).
It checks the installed plugin and library sets, starts sdrangelsrv with the engine lease's own
command (software/systemd/srrx-lease-sdrangelsrv@.service: `/usr/bin/env sdrangelsrv -a
127.0.0.1 -w ...`), reads the REST API on 127.0.0.1:8091 (instance summary, Rx/Tx/MIMO channel
plugins, feature plugins, Rx/Tx/MIMO devices), checks that every listening TCP socket and every
bound UDP socket is a loopback address, compares the plugins the log says were loaded with the
server allowlist and stops the server with SIGTERM, as systemd does. A second run adds --soapy, so the
SoapySDR input plugin (not loaded by the lease while Lime is disabled) is shown to load too.
Finally it writes the unsigned per-file manifest of /opt/sdrangel for selftest RX-02 (the walk of
deploy.build_inventory; status OPEN) into its report.

Stdlib only (this file is copied alone into the chroot). The last stdout line is the result
object: ok true and no findings, or the runtime check fails. CI model on the arm64 builder: no
receiver, no RF, no signature.
"""
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time

PREFIX = Path("/opt/sdrangel")
# Copies of deployment/recipes/sdrangel/check_recipe.py (this file runs alone in the chroot;
# software/tests/test_sdrangel_client.py keeps the sets equal).
GUI_PLUGINS = frozenset({
    "libchanalyzer.so", "libchannelpower.so", "libdemodam.so", "libdemodbfm.so", "libdemodwfm.so", "libdemodnfm.so",
    "libdemodssb.so", "libdemodft8.so", "libradioclock.so", "libradioastronomy.so", "libfreqtracker.so", "libdemodvor.so",
    "libdemodils.so", "libnoisefigure.so", "libinputrtlsdr.so", "libinputairspyhf.so", "libinputsoapysdr.so",
    "libinputfileinput.so", "libinputtestsource.so", "libfeaturefreqdisplay.so", "libantennatools.so",
    "libfeaturedemodanalyzer.so"})
SERVER_PLUGINS = frozenset({
    "libchannelpowersrv.so", "libdemodamsrv.so", "libdemodbfmsrv.so", "libdemodwfmsrv.so", "libdemodnfmsrv.so",
    "libdemodssbsrv.so", "libdemodnavtexsrv.so", "libdemodrttysrv.so", "libdemodft8srv.so", "libdemodpacketsrv.so",
    "libradioclocksrv.so", "libradioastronomysrv.so", "libfreqtrackersrv.so", "libdemodvorsrv.so", "libdemodilssrv.so",
    "libnoisefiguresrv.so", "libinputrtlsdrsrv.so", "libinputairspyhfsrv.so", "libinputsoapysdrsrv.so",
    "libinputfileinputsrv.so", "libinputtestsourcesrv.so", "libfeaturefreqdisplaysrv.so", "libantennatoolssrv.so",
    "libfeaturedemodanalyzersrv.so"})
CORE_LIBRARIES = frozenset({
    "libsdrbase.so", "libhttpserver.so", "liblogging.so", "libqrtplib.so", "libswagger.so", "libft8.so",
    "libsoapysdrdevice.so", "libsdrgui.so", "libsdrsrv.so"})
SOAPY_PLUGIN = "libinputsoapysdrsrv.so"
# The ExecStart of the engine lease template (a host test compares them).
LEASE_ARGV = ("/usr/bin/env", "sdrangelsrv", "-a", "127.0.0.1", "-w", "/var/lib/lab/fftw/sdrangel.wisdom")
PORT = 8091
# REST ids of the server plugins: each plugin's m_channelId / m_featureId / m_hardwareID at 97e9e21.
RX_CHANNELS = frozenset({"ChannelPower", "AMDemod", "BFMDemod", "WFMDemod", "NFMDemod", "SSBDemod", "NavtexDemod", "RTTYDemod",
                         "FT8Demod", "PacketDemod", "RadioClock", "RadioAstronomy", "FreqTracker", "VORDemod", "ILSDemod",
                         "NoiseFigure"})
FEATURES = frozenset({"FreqDisplay", "AntennaTools", "DemodAnalyzer"})
# FileInput and TestSource always enumerate one device; RTL-SDR, AirspyHF and SoapySDR need hardware.
RX_DEVICES_REQUIRED = frozenset({"FileInput", "TestSource"})
RX_DEVICES_ALLOWED = RX_DEVICES_REQUIRED | {"RTLSDR", "AirspyHF", "SoapySDR"}
START_TIMEOUT, STOP_TIMEOUT = 90.0, 20.0
LOADED = re.compile(r"PluginManager::loadPluginsDir: loaded plugin (\S+)")
SKIPPED = re.compile(r"PluginManager::loadPluginsDir: Soapy SDR disabled skipping (\S+)")


def set_findings(label, found, expected):
    missing, extra = sorted(set(expected) - set(found)), sorted(set(found) - set(expected))
    if not missing and not extra:
        return []
    return ["%s differs: missing %s, unexpected %s" % (label, ",".join(missing) or "-", ",".join(extra) or "-")]


def installed_findings(prefix=PREFIX, links=None):
    """The installed plugin, library and binary sets and the /usr/bin links."""
    prefix = Path(prefix)
    findings = []
    for label, directory, expected in (("GUI plugins", prefix / "lib/sdrangel/plugins", GUI_PLUGINS),
                                       ("server plugins", prefix / "lib/sdrangel/pluginssrv", SERVER_PLUGINS)):
        found = sorted(p.name for p in directory.iterdir()) if directory.is_dir() else []
        findings += set_findings(label, found, expected)
    libraries = sorted(p.name for p in (prefix / "lib").iterdir() if p.name != "sdrangel") if (prefix / "lib").is_dir() else []
    findings += set_findings("core libraries", libraries, CORE_LIBRARIES)
    if links is None:
        links = {"/usr/bin/sdrangelsrv": prefix / "bin/sdrangelsrv", "/usr/bin/sdrangel": prefix / "bin/sdrangel"}
    for link, binary in links.items():
        if not Path(link).is_symlink() or Path(link).resolve() != Path(binary).resolve():
            findings.append("%s is not a link to %s" % (link, binary))
    return findings


def _socket_lines(path):
    try:
        lines = Path(path).read_text(encoding="ascii").splitlines()[1:]
    except OSError:
        return []
    return [line.split() for line in lines if line.strip()]


def _address(text):
    """(address, port) of a /proc/net/{tcp,udp}[6] local_address field."""
    host, port = text.split(":")
    raw = bytes.fromhex(host)
    if len(raw) == 4:
        address = ".".join(str(b) for b in raw[::-1])
    else:  # four little-endian 32-bit words
        words = b"".join(raw[i:i + 4][::-1] for i in range(0, 16, 4))
        address = ":".join(words[i:i + 2].hex() for i in range(0, 16, 2))
    return address, int(port, 16)


def is_loopback(address):
    if "." in address and ":" not in address:
        return address.startswith("127.")
    groups = address.split(":")
    if groups == ["0000"] * 7 + ["0001"]:
        return True
    # ::ffff:127.x.y.z
    return groups[:6] == ["0000"] * 5 + ["ffff"] and int(groups[6], 16) >> 8 == 127


def bound_sockets(proc_net="/proc/net"):
    """Listening TCP and bound UDP sockets of this network namespace: [(proto, address, port)]."""
    found = []
    for proto, wanted in (("tcp", "0A"), ("tcp6", "0A"), ("udp", "07"), ("udp6", "07")):
        for fields in _socket_lines(Path(proc_net) / proto):
            if len(fields) > 3 and fields[3] == wanted:
                address, port = _address(fields[1])
                found.append((proto, address, port))
    return sorted(found)


def socket_findings(sockets):
    findings = ["%s socket bound to a non-loopback address %s port %d" % (p, a, n) for p, a, n in sockets if not is_loopback(a)]
    if not any(p.startswith("tcp") and n == PORT for p, a, n in sockets):
        findings.append("no listening TCP socket on port %d" % PORT)
    return findings


def rest_findings(rest):
    """Findings of the REST answers {name: json}: the server plugin allowlist, and no Tx or MIMO path."""
    findings = []
    summary = rest.get("summary") or {}
    if summary.get("appname") != "SDRangelSrv" or not str(summary.get("version", "")).startswith("7.27.2"):
        findings.append("instance summary is not SDRangelSrv 7.27.2: %s %s" % (summary.get("appname"), summary.get("version")))
    channels = [c.get("id") for c in (rest.get("channels_rx") or {}).get("channels", [])]
    findings += set_findings("REST Rx channel plugins", channels, RX_CHANNELS)
    if len(channels) != len(set(channels)):
        findings.append("REST Rx channel plugins repeat an id")
    features = [f.get("id") for f in (rest.get("features") or {}).get("features", [])]
    findings += set_findings("REST feature plugins", features, FEATURES)
    for name in ("channels_tx", "channels_mimo"):
        count = (rest.get(name) or {}).get("channelcount")
        if count != 0:
            findings.append("REST %s is not empty: %s" % (name, count))
    for name in ("devices_tx", "devices_mimo"):
        count = (rest.get(name) or {}).get("devicecount")
        if count != 0:
            findings.append("REST %s is not empty: %s" % (name, count))
    devices = {d.get("hwType") for d in (rest.get("devices_rx") or {}).get("devices", [])}
    if not RX_DEVICES_REQUIRED <= devices or not devices <= RX_DEVICES_ALLOWED:
        findings.append("REST Rx devices %s are not FileInput and TestSource within %s" % (sorted(devices), sorted(RX_DEVICES_ALLOWED)))
    return findings


def log_findings(text, soapy):
    loaded, skipped = set(LOADED.findall(text)), set(SKIPPED.findall(text))
    expected = set(SERVER_PLUGINS) if soapy else set(SERVER_PLUGINS) - {SOAPY_PLUGIN}
    findings = set_findings("plugins loaded%s" % (" with --soapy" if soapy else ""), loaded, expected)
    if not soapy and skipped != {SOAPY_PLUGIN}:
        findings.append("the lease run did not skip exactly the SoapySDR plugin: %s" % sorted(skipped))
    return findings, sorted(loaded)


def prefix_manifest(prefix=PREFIX):
    """deploy.build_inventory(prefix) as a verify_build manifest with status OPEN (same walk:
    sorted rglob, internal directory links as "symlink:<target>", file links by their target's
    SHA-256, every path with ".so" in its name a module). Links leaving the prefix fail."""
    root = Path(prefix).resolve(strict=True)
    files, modules = {}, []
    for path in sorted(root.rglob("*")):
        link = path.resolve(strict=True) if path.is_symlink() else None
        if link is not None and not link.is_relative_to(root):
            raise ValueError("external symlink in the prefix: " + str(path))
        if link is None and path.is_dir():
            continue
        relative = path.relative_to(root).as_posix()
        if not path.is_file() and not (link is not None and link.is_dir()):
            raise ValueError("non-regular file in the prefix: " + relative)
        if link is not None and link.is_dir():
            files[relative] = "symlink:" + link.relative_to(root).as_posix()
            continue
        if ".so" in path.name:
            modules.append(relative)
        with open(path, "rb") as handle:
            files[relative] = hashlib.file_digest(handle, "sha256").hexdigest()
    return {"schema_version": 1, "status": "OPEN", "files": files, "allowed_modules": sorted(modules),
            "source_audit": {"status": "OPEN", "report": {"path": None, "sha256": None}},
            "tx_negative_tests": {"status": "OPEN", "report": {"path": None, "sha256": None}}}


def canonical(document):
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def request(method, path, timeout=5.0):
    connection = http.client.HTTPConnection("127.0.0.1", PORT, timeout=timeout)
    try:
        connection.request(method, path, headers={"Accept": "application/json"})
        response = connection.getresponse()
        body = response.read()
    finally:
        connection.close()
    try:
        data = json.loads(body.decode("utf-8")) if body else None
    except ValueError:
        data = None
    return response.status, data


def serve(argv, home, log):
    """Start one sdrangelsrv, wait for its REST API, read it, stop it. Returns (rest, sockets, log text, findings)."""
    findings, rest, sockets = [], {}, []
    env = {"PATH": os.environ.get("PATH", "/usr/sbin:/usr/bin:/sbin:/bin"), "HOME": str(home), "LANG": "C.UTF-8",
           "XDG_RUNTIME_DIR": str(home)}
    with open(log, "wb") as stream:
        process = subprocess.Popen(list(argv), stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, env=env, cwd=str(home))
    try:
        deadline = time.monotonic() + START_TIMEOUT
        while True:
            if process.poll() is not None:
                findings.append("sdrangelsrv exited with %s before its REST API answered" % process.returncode)
                break
            try:
                status, data = request("GET", "/sdrangel", timeout=2.0)
                if status == 200:
                    rest["summary"] = data
                    break
            except (OSError, http.client.HTTPException):
                pass
            if time.monotonic() > deadline:
                findings.append("the REST API did not answer within %d s" % START_TIMEOUT)
                break
            time.sleep(0.5)
        if "summary" in rest:
            for name, path in (("channels_rx", "/sdrangel/channels?direction=0"), ("channels_tx", "/sdrangel/channels?direction=1"),
                               ("channels_mimo", "/sdrangel/channels?direction=2"), ("features", "/sdrangel/features"),
                               ("devices_rx", "/sdrangel/devices?direction=0"), ("devices_tx", "/sdrangel/devices?direction=1"),
                               ("devices_mimo", "/sdrangel/devices?direction=2")):
                try:
                    status, data = request("GET", path)
                except (OSError, http.client.HTTPException) as exc:
                    status, data = "no answer (%s)" % type(exc).__name__, None
                if status != 200:
                    findings.append("GET %s gave %s" % (path, status))
                rest[name] = data
            sockets = bound_sockets()
        # DELETE /sdrangel answers 400 at 97e9e21 (the shared WebAPIAdapter::instanceDelete), so
        # the server stops as systemd stops the lease: SIGTERM, which appsrv/main.cpp maps to quit().
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=STOP_TIMEOUT)
            except subprocess.TimeoutExpired:
                findings.append("sdrangelsrv did not stop within %d s of SIGTERM" % STOP_TIMEOUT)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    text = Path(log).read_text(encoding="utf-8", errors="replace")
    return rest, sockets, text, findings


def main():
    findings = installed_findings()
    report = {"recipe": "sdrangel", "lease_argv": list(LEASE_ARGV), "runs": {}, "hardware_ready": False,
              "scope": "CI model in the runtime-check chroot: loopback only, no receiver, no RF; the manifest is unsigned."}
    with tempfile.TemporaryDirectory(prefix="srrx-sdrangel-") as temporary:
        for label, argv, soapy in (("lease", LEASE_ARGV, False), ("soapy", LEASE_ARGV + ("--soapy",), True)):
            home = Path(temporary) / label
            home.mkdir(mode=0o700)
            rest, sockets, text, problems = serve(argv, home, Path(temporary) / (label + ".log"))
            problems += rest_findings(rest) if "summary" in rest else []
            problems += socket_findings(sockets) if "summary" in rest else []
            log_problems, loaded = log_findings(text, soapy)
            problems += log_problems
            findings += ["%s run: %s" % (label, p) for p in problems]
            report["runs"][label] = {"argv": list(argv), "summary": rest.get("summary"),
                                     "rx_channels": sorted(c.get("id") for c in (rest.get("channels_rx") or {}).get("channels", [])),
                                     "features": sorted(f.get("id") for f in (rest.get("features") or {}).get("features", [])),
                                     "rx_devices": sorted(d.get("hwType") for d in (rest.get("devices_rx") or {}).get("devices", [])),
                                     "sockets": [list(s) for s in sockets], "loaded_plugins": loaded,
                                     "log_tail": text.splitlines()[-40:]}
    try:
        document = prefix_manifest()
        report.update(rx02_manifest=document, rx02_manifest_sha256=hashlib.sha256(canonical(document)).hexdigest(),
                      rx02_manifest_files=len(document["files"]), rx02_manifest_status="OPEN_UNSIGNED")
    except (OSError, ValueError) as exc:
        findings.append("manifest of /opt/sdrangel: " + str(exc)[:200])
    report.update(ok=not findings, findings=findings)
    print(json.dumps(report, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
