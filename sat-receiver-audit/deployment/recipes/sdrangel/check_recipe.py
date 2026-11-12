#!/usr/bin/env python3
"""Package hook of the SDRangel +lab recipe (recipe.json hooks.package, recipes/README.md).

  package --destdir DIR --out FILE
      DIR is the `cmake --install` tree of one build. The hook checks it against the allowlisted
      sets below (the exact plugin files of opt/sdrangel/lib/sdrangel/plugins and pluginssrv, the
      core libraries of opt/sdrangel/lib, the two binaries, no other ELF file anywhere), links
      usr/bin/sdrangel and usr/bin/sdrangelsrv to ../../opt/sdrangel/bin/ (the engine lease runs
      `/usr/bin/env sdrangelsrv`, software/systemd/srrx-lease-sdrangelsrv@.service) and writes
      FILE: the unsigned per-file manifest of /opt/sdrangel for selftest RX-02, built by
      deploy.build_inventory (the walk deploy.verify_build compares) with status OPEN, plus the
      record_digests the build record carries.

Stdlib plus deployment/deploy.py; it runs inside the builder chroot as uid 1000 (build_recipe
run_hook). The last stdout line is the hook result: ok true and no findings, or the build stops.
CI evidence only: nothing here reviews the build or signs the manifest, so RX-02 stays BLOCKED
until the owner's offline signing ceremony (build/15, Ключ підпису офлайн-репозиторію).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # deployment/
import deploy  # noqa: E402

PREFIX = "opt/sdrangel"
# GUI plugins (lib/sdrangel/plugins): the build/07-pz-vstanovlennia.md:417-419 allowlist that noble
# can build, without the text decoders (demodnavtex, demodrtty, demodpacket: server only,
# build/07-pz-vstanovlennia.md:422). File names follow each plugin's TARGET_NAME at 97e9e21.
GUI_PLUGINS = frozenset({
    "libchanalyzer.so", "libchannelpower.so", "libdemodam.so", "libdemodbfm.so", "libdemodwfm.so", "libdemodnfm.so",
    "libdemodssb.so", "libdemodft8.so", "libradioclock.so", "libradioastronomy.so", "libfreqtracker.so", "libdemodvor.so",
    "libdemodils.so", "libnoisefigure.so", "libinputrtlsdr.so", "libinputairspyhf.so", "libinputsoapysdr.so",
    "libinputfileinput.so", "libinputtestsource.so", "libfeaturefreqdisplay.so", "libantennatools.so",
    "libfeaturedemodanalyzer.so"})
# Server plugins (lib/sdrangel/pluginssrv): chanalyzer is GUI-only upstream (plugins/channelrx
# CMakeLists, NOT SERVER_MODE); the text decoders are here.
SERVER_PLUGINS = frozenset({
    "libchannelpowersrv.so", "libdemodamsrv.so", "libdemodbfmsrv.so", "libdemodwfmsrv.so", "libdemodnfmsrv.so",
    "libdemodssbsrv.so", "libdemodnavtexsrv.so", "libdemodrttysrv.so", "libdemodft8srv.so", "libdemodpacketsrv.so",
    "libradioclocksrv.so", "libradioastronomysrv.so", "libfreqtrackersrv.so", "libdemodvorsrv.so", "libdemodilssrv.so",
    "libnoisefiguresrv.so", "libinputrtlsdrsrv.so", "libinputairspyhfsrv.so", "libinputsoapysdrsrv.so",
    "libinputfileinputsrv.so", "libinputtestsourcesrv.so", "libfeaturefreqdisplaysrv.so", "libantennatoolssrv.so",
    "libfeaturedemodanalyzersrv.so"})
# opt/sdrangel/lib (the patch moves the core libraries out of lib/sdrangel).
CORE_LIBRARIES = frozenset({
    "libsdrbase.so", "libhttpserver.so", "liblogging.so", "libqrtplib.so", "libswagger.so", "libft8.so",
    "libsoapysdrdevice.so", "libsdrgui.so", "libsdrsrv.so"})
BINARIES = frozenset({"sdrangel", "sdrangelsrv"})
LINKS = {"usr/bin/sdrangel": "../../opt/sdrangel/bin/sdrangel", "usr/bin/sdrangelsrv": "../../opt/sdrangel/bin/sdrangelsrv"}
MANIFEST_KIND = "srrx_sdrangel_rx02_manifest"
BLOCKED_REASON = ("unsigned CI manifest: RX-02 needs a reviewed manifest (status REVIEWED, source audit and TX negative "
                  "tests PASS) signed by the offline repository key of the owner's ceremony; no private key enters CI or Git")


def _names(directory):
    try:
        return sorted(p.name for p in Path(directory).iterdir())
    except OSError:
        return None


def _regular(directory, names):
    return sorted(n for n in names if (Path(directory) / n).is_symlink() or not (Path(directory) / n).is_file())


def _is_elf(path):
    try:
        with open(path, "rb") as handle:
            return handle.read(4) == b"\x7fELF"
    except OSError:
        return False


def _set_finding(label, found, expected):
    missing, extra = sorted(set(expected) - set(found)), sorted(set(found) - set(expected))
    if not missing and not extra:
        return []
    return ["%s differs: missing %s, unexpected %s" % (label, ",".join(missing) or "-", ",".join(extra) or "-")]


def check_tree(destdir):
    """Findings of one install tree before the links exist (empty list: the allowlisted layout)."""
    root = Path(destdir)
    prefix = root / PREFIX
    findings = []
    top = _names(root)
    if top != ["opt"]:
        findings.append("install tree top level is not only opt/: %s" % ",".join(top or []))
    if _names(root / "opt") != ["sdrangel"]:
        findings.append("opt/ holds more than sdrangel/")
    plugins = prefix / "lib/sdrangel"
    if _names(plugins) != ["plugins", "pluginssrv"]:
        findings.append("lib/sdrangel holds more than plugins/ and pluginssrv/: %s" % ",".join(_names(plugins) or []))
    for label, directory, expected in (("GUI plugins", plugins / "plugins", GUI_PLUGINS),
                                       ("server plugins", plugins / "pluginssrv", SERVER_PLUGINS)):
        names = _names(directory) or []
        findings += _set_finding(label, names, expected)
        findings += ["%s/%s is not a regular file" % (label, n) for n in _regular(directory, names)]
    libraries = [n for n in (_names(prefix / "lib") or []) if n != "sdrangel"]
    findings += _set_finding("core libraries", libraries, CORE_LIBRARIES)
    findings += ["lib/%s is not a regular file" % n for n in _regular(prefix / "lib", libraries)]
    binaries = _names(prefix / "bin") or []
    findings += _set_finding("binaries", binaries, BINARIES)
    allowed = ({PREFIX + "/lib/sdrangel/plugins/" + n for n in GUI_PLUGINS} | {PREFIX + "/lib/sdrangel/pluginssrv/" + n for n in SERVER_PLUGINS}
               | {PREFIX + "/lib/" + n for n in CORE_LIBRARIES} | {PREFIX + "/bin/" + n for n in BINARIES})
    for directory, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                findings.append("unexpected symlink in the install tree: " + relative)
            elif relative not in allowed and (_is_elf(path) or ".so" in name):
                findings.append("unexpected ELF or shared object: " + relative)
    return findings


def manifest(prefix):
    """The RX-02 component manifest of the installed prefix: verify_build schema, status OPEN."""
    files, modules = deploy.build_inventory(prefix)
    return {"schema_version": 1, "status": "OPEN", "files": files, "allowed_modules": sorted(modules),
            "source_audit": {"status": "OPEN", "report": {"path": None, "sha256": None}},
            "tx_negative_tests": {"status": "OPEN", "report": {"path": None, "sha256": None}}}


def canonical(document):
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def package(destdir, out):
    root = Path(destdir)
    findings = check_tree(root)
    result = {"ok": False, "findings": findings}
    if findings:
        return result
    for link, target in sorted(LINKS.items()):
        path = root / link
        if path.exists() or path.is_symlink():
            return dict(result, findings=["%s exists before the hook" % link])
        path.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(target, path)
        if path.resolve() != (root / PREFIX / "bin" / Path(target).name).resolve():
            return dict(result, findings=["%s does not resolve to the installed binary" % link])
    try:
        document = manifest(root / PREFIX)
    except (OSError, deploy.DeploymentError) as exc:
        return dict(result, findings=["deploy.build_inventory refuses /opt/sdrangel: " + str(exc)[:200]])
    data = canonical(document)
    digests = {"rx02_manifest_sha256": hashlib.sha256(data).hexdigest(), "rx02_manifest_files": len(document["files"]),
               "rx02_manifest_modules": len(document["allowed_modules"])}
    output = {"schema_version": 1, "kind": MANIFEST_KIND, "status": "OPEN_UNSIGNED", "prefix": PREFIX,
              "signature": None, "blocked_reason": BLOCKED_REASON, "manifest": document, "record_digests": digests,
              "links": dict(sorted(LINKS.items())), "hardware_ready": False}
    Path(out).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return {"ok": True, "findings": [], "gui_plugins": len(GUI_PLUGINS), "server_plugins": len(SERVER_PLUGINS),
            "core_libraries": len(CORE_LIBRARIES), **digests}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    hook = commands.add_parser("package", help="check the install tree, add the /usr/bin links, write the RX-02 manifest")
    hook.add_argument("--destdir", type=Path, required=True)
    hook.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = package(args.destdir, args.out)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
