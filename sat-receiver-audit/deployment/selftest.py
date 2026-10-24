#!/usr/bin/env python3
"""Offline receive-only/privacy self-test of a staged or extracted target rootfs.

Static allowlist evidence only (build/07-pz-vstanovlennia.md sections 22-23, build/09-testy.md
POL-01..13): allowlists are the primary control, deny tokens only a second layer (STACK.md:85,
STACK.md:886). It is not a universal TX proof. Rows that need an arm64 builder, the Q6A or RF
hardware are RUNTIME_ONLY; a row without code would be BLOCKED with evaluability NOT_IMPLEMENTED.
No row outside OFFLINE ever reports PASS and the report never sets hardware_ready or
receive_only_proven. A REVIEWED policy still blocks until a review record bound to its bytes is
given (load_review); nothing here changes a policy status. Nothing here runs apt, dpkg,
systemctl, chroot or mount or follows a target symlink on the host: links resolve chroot-style
inside the inventory. Only
readelf and gpgv run, each with a timeout and a capped output. Findings carry relative paths and
rule ids, never file contents (decoder_policy privacy principle).

Conservative choices where the specification leaves room: FAIL dominates BLOCKED, so a DRAFT
policy never hides a found violation yet can never yield OFFLINE_CHECKS_PASS; a symlink whose
lexical target climbs above the rootfs is BLOCKED although a chroot would clamp it; an engine
absent in profile full is BLOCKED (component_not_found) while profile controller requires its
absence, and a present engine whose row evidence (owrx/modes.py, the Gpredict ELF) is not found
is BLOCKED; bias keys are forbidden in engine configs even with a false value (STACK.md:888) and
Soapy device-argument strings (driver=rtlsdr,direct_samp=2) are scanned as well; pin_only
packages (apt -1 pins without a forbidden version) present without a reviewed version rule are
BLOCKED, not FAIL; lease units follow systemd unit/drop-in precedence (system.control > etc >
attached > usr/local/lib > usr/lib > lib, per-filename drop-in override, instance/template,
dash-prefix and service.d drop-ins, /dev/null and empty-file masks), an unresolvable unit or
drop-in link is BLOCKED, and a lease also needs IPAddressDeny=any because IPAddressAllow=localhost
alone restricts nothing in systemd; engine config keys are also matched on their last QSettings or
dotted component (rtlsdr\\biasTee); apt preference files other than lab.pref may only lower priorities. The
checker evaluates its own srrx modules and requires the target copy of each module and of every
srrx module it imports to be byte-identical, otherwise BLOCKED, so target code is never executed.
Identifiers in findings are policy-derived (rule name/glob, deny token, setting key); target
strings such as dataset labels, mode names or DT_NEEDED entries are never echoed.
"""
import argparse
import ast
from bisect import bisect_left
from datetime import date
import fnmatch
import functools
import hashlib
import importlib
import json
import os
from pathlib import Path
import posixpath
import re
import stat
import subprocess
import sys
import threading
import time
import uuid

sys.dont_write_bytecode = True  # never add __pycache__ to a tree verify_build allowlists
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import deploy  # noqa: E402  (same directory; strict JSON, hashing and verify_build are reused)
from deploy import DeploymentError  # noqa: E402

PROFILES = ("controller", "full")
STATUSES = ("PASS", "FAIL", "BLOCKED", "RUNTIME_ONLY", "NOT_IMPLEMENTED")  # NOT_IMPLEMENTED rows report BLOCKED
SKIP_TOP = frozenset(("proc", "sys", "dev", "run", "tmp"))
MAX_ENTRIES = 5_000_000
MAX_FINDINGS = 200
MAX_TEXT = 4 * 1024 * 1024
MAX_DPKG_STATUS = 64 * 1024 * 1024
MAX_DPKG_RECORDS = 1_000_000
MAX_HOPS = 40
MAX_DEPTH = 64
CHUNK = 1024 * 1024
ELF_MAGIC = b"\x7fELF"
READELF_TIMEOUT, READELF_LIMIT = 20, 16 * 1024 * 1024
GPGV_TIMEOUT, GPGV_LIMIT = 30, 64 * 1024
COMPONENT_MANIFESTS = ("sdrangel",)
_SAFE_ITEM = re.compile(r"[A-Za-z0-9*][A-Za-z0-9._+:~*@-]{0,127}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_B07, _B09 = "build/07-pz-vstanovlennia.md", "build/09-testy.md"

# (id, build07 row, evaluability, title, sources); one check_* per OFFLINE row.
CATALOGUE = (
    ("RX-00", None, "OFFLINE", "Target inventory: no special file, no symlink escaping the rootfs, within bounds", (_B07 + ":546",)),
    ("RX-01a", 1, "OFFLINE", "dpkg status: no forbidden package present (unpacked/half-*/triggers-* count)", (_B07 + ":540", _B07 + ":546", "STACK.md:888", "STACK.md:892", _B09 + ":70")),
    ("RX-01b", 1, "OFFLINE", "File names: no forbidden basename, AppImage, snap/flatpak/docker state, transmitting Dream", (_B07 + ":540", _B07 + ":546", "STACK.md:888")),
    ("RX-01c", 1, "OFFLINE", "Engine configs: direct sampling mode 0, no direct_sampling/direct_samp/bias keys or device args, no HF+ 256000",(_B07 + ":324", _B07 + ":409", _B07 + ":431", _B07 + ":540", "STACK.md:888")),
    ("RX-02", 2, "OFFLINE", "SDRangel: plugin set equals allowlist, deny layer, signed reviewed hash manifest", (_B07 + ":415-424", _B07 + ":547", "STACK.md:890", _B09 + ":79")),
    ("RX-03", 3, "OFFLINE", "SDR++: no recorder/iq_exporter/network_sink/pager_decoder, ON list only, no sdrpp --server", (_B07 + ":401-409", _B07 + ":548", "STACK.md:890")),
    ("RX-04", 4, "OFFLINE", "SatDump: allowlisted plugins and five pipelines, no sinks/sources/mqtt, kepler Never", (_B07 + ":362-389", _B07 + ":549", "STACK.md:886", _B09 + ":78")),
    ("RX-04-decode", 4, "BUILDER", "SatDump baseline decode of one stored file per allowlisted pipeline", (_B07 + ":389", _B07 + ":549")),
    ("RX-04-bb", 4, "OFFLINE", "v2.1 LRPT baseband recorder: policy constants, computed channel filter, out-of-window tone stored as zeros, fixed SatDump units",
     ("STACK.md:977", "STACK.md:882", "build/12-revision-v2.1.md:71", "software/srrx/baseband.py", "software/srrx/satdump_pass.py")),
    ("RX-04-live", 4, "DEVICE", "SatDump live unit on the Q6A: only 127.0.0.1 datagrams reach net_source; live products equal the file decode",
     ("STACK.md:1480", "software/srrx/satdump_pass.py unit_properties")),
    ("RX-05", 5, "OFFLINE", "OpenWebRX+: static modes subset of allowlist, locked settings, admin password present", (_B07 + ":426-433", _B07 + ":550", _B09 + ":79")),
    ("RX-05-live", 5, "DEVICE", "OpenWebRX+ live feature/mode list", (_B07 + ":433", _B07 + ":550")),
    ("RX-06", 6, "OFFLINE", "Soapy modules0.8 exactly rtlsdr/airspyhf, no Lime module, no 0.9, no plugin path override", (_B07 + ":328-338", _B07 + ":551", "deployment/deploy.py validate_devices")),
    ("RX-06-info", 6, "BUILDER", "SoapySDRUtil --info on the builder/device", (_B07 + ":338", _B07 + ":551")),
    ("RX-07", 7, "OFFLINE", "No Amarisoft shared object", (_B07 + ":358", _B07 + ":552")),
    ("RX-08", 8, "OFFLINE", "No Lime runtime library staged while Lime is disabled", (_B07 + ":342-358", _B07 + ":553", "deployment/deploy.py verify_build")),
    ("RX-08-hw", 8, "HARDWARE", "Lime --txen=0, register 0x0020 readback, TX setupStream fails", (_B07 + ":353", _B07 + ":553")),
    ("RX-09", 9, "OFFLINE", "librtlsdr.so.2: SONAME, 37 rtlsdr_* exports, no zero-copy text, consumers need .so.2", (_B07 + ":299-307", _B07 + ":554", "deployment/build-vendor.sh:41-48")),
    ("RX-09-hw", 9, "HARDWARE", "RTL bias/token tests without token", (_B07 + ":308-310", _B07 + ":554", _B09 + ":71")),
    ("RX-10", 10, "OFFLINE", "Gpredict: no libgps/libhamlib in DT_NEEDED, RX-only radios, network TLE update off", (_B07 + ":505-509", _B07 + ":555")),
    ("RX-11", 11, "OFFLINE", "Menu model: each leaf reaches a staged backend, Lime/T7 leaves declare their fallback, critical leaves have a key or encoder",
     (_B07 + ":556", "STACK.md:884", "STACK.md:110", "software/srrx/menu_model.py LEAVES")),
    ("RX-12", 12, "OFFLINE", "Lease units (systemd precedence): DevicePolicy=closed, ProtectSystem=strict, /data read-only, products lease, localhost only",
     (_B07 + ":532", _B07 + ":534", _B07 + ":557")),
    ("RX-12-runtime", 12, "DEVICE", "Lease EPERM/EROFS/EGL behaviour on the Q6A", (_B07 + ":557", _B09 + ":62")),
    ("RX-13", 13, "OFFLINE", "Band mask CPU path: 20 kHz, 300 MHz, 406.05 MHz, 1544.5 MHz bins invalid; annotate refuses",
     (_B07 + ":558", _B09 + ":73", "STACK.md:626", "software/srrx/spectrum.py mask_frame")),
    ("RX-13-npu", 13, "DEVICE", "NPU class-signal mask on the device", (_B07 + ":558",)),
    ("RX-14", 14, "OFFLINE", "Voice mask: synthetic NFM at 145.500, 433.500, 446.006 MHz and the static masks excised from pinned captures",
     (_B07 + ":559", _B09 + ":73", "STACK.md:977", "software/srrx/voice_mask.py excise")),
    ("RX-15", 15, "OFFLINE", "Dataset/model manifests: labels in learning.LABELS, no forbidden class tokens", (_B07 + ":560", "STACK.md:1147", _B09 + ":77")),
    ("RX-16", 16, "OFFLINE", "apt: no launchpad origin, lab.pref 1001/990/-1, dpkg md5sums of firmware/FastRPC", (_B07 + ":103", _B07 + ":108-119", _B07 + ":135", _B07 + ":561", _B09 + ":216")),
    ("RX-16-sim", 16, "BUILDER", "apt-get -s dist-upgrade and apt policy on the builder/device", (_B07 + ":135", _B07 + ":561")),
    ("RX-17", 17, "OFFLINE", "/etc/kernel/cmdline SHA-256 equals the reviewed record", (_B07 + ":181-193", _B07 + ":562")),
    ("RX-17-proc", 17, "DEVICE", "/proc/cmdline on the running device", (_B07 + ":193", _B07 + ":562")),
    ("RX-18", 18, "DEVICE", "labbar visible over every full-screen Expert GUI", (_B07 + ":563", "STACK.md:884")),
    ("RX-S1", None, "OFFLINE", "decoder_policy.availability(): EGC, DSC, AIS, ADS-B presets disabled; SatDump installation-gated (unavailable offline)",
     ("software/srrx/decoder_policy.py availability", "STACK.md:85")),
    ("RX-S2", None, "OFFLINE", "Field/QUIET Wi-Fi/BT off as staged: AIC8800/btusb blacklist + install /bin/false, FE1.1s port-4 authorized=0 rule, "
     "rfkill oneshot required by srrx.service only", ("STACK.md:726", "STACK.md:2167", "STACK.md:125", _B09 + ":69", "deployment/deploy.py stage")),
    ("RX-S2-runtime", None, "DEVICE", "Live rfkill block, no wlan/hci device, AIC8800 modules unloaded, port 4 deauthorized (deploy.py doctor radio_off)",
     (_B09 + ":69", "deployment/deploy.py radio_off_issues")),
)


class Blocked(Exception):
    """Evaluation impossible for one input; reported as a BLOCKED finding."""
    def __init__(self, path, rule):
        super().__init__(rule)
        self.path, self.rule = path, rule


class ElfError(ValueError):
    def __init__(self, rule):
        super().__init__(rule)
        self.rule = rule


class Entry:
    __slots__ = ("kind", "size", "target")

    def __init__(self, kind, size=0, target=None):
        self.kind, self.size, self.target = kind, size, target


def catalogue():
    return [{"id": i, "build07_row": row, "evaluability": e, "title": t, "sources": list(s)} for i, row, e, t, s in CATALOGUE]


# ---------------------------------------------------------------- policy

def _text(value, label):
    if type(value) is not str or not value:
        raise DeploymentError(label + " must be a non-empty string")


def _scalars(value, label):
    if type(value) is not dict or any(type(k) is not str or type(v) not in (str, int, bool) for k, v in value.items()):
        raise DeploymentError(label + " must map names to scalars")


def _package(value, label):
    if type(value) is not dict or not {"group", "check", "source"} <= set(value) or set(value) - {"name", "glob", "version_rule", "group", "check", "source"}:
        raise DeploymentError(label + " has missing or unknown fields")
    if len({"name", "glob"} & set(value)) != 1 or value["check"] not in ("presence", "pin_only"):
        raise DeploymentError(label + " needs exactly one of name/glob and a presence/pin_only check")
    for key in set(value) - {"version_rule"}:
        _text(value[key], label + "." + key)
    if "version_rule" in value:  # one vocabulary with doctor (deploy.VERSION_RULE_KEYS)
        deploy.check_version_rule(value["version_rule"], label)


# [spec] is a list, (spec,) a non-empty list (the checks name its first element in findings).
_COMMON = {"footprint": [_text], "plugin_dirs": [_text], "allow_plugins": [_text], "deny_tokens": [_text], "config_paths": [_text], "sources": [_text]}
POLICY_SCHEMA = {
    "schema_version": int, "status": _text, "scope": _text, "notes": [_text], "srrx_root": _text,
    "forbidden_packages": [_package],
    "forbidden_basenames": [{"name": _text, "source": _text}],
    "forbidden_path_parts": [{"name": _text, "source": _text}],
    "forbidden_path_prefixes": [{"path": _text, "source": _text}],
    "forbidden_suffixes": [{"suffix": _text, "source": _text}],
    "forbidden_module_words": [{"word": _text, "source": _text}],
    "engine_config_rules": {"direct_sampling_keys": (_text,), "direct_sampling_mode_keys": (_text,), "bias_keys": (_text,), "hfplus_rate_keys": [_text],
                            "hfplus_forbidden_rate": int, "extra_config_paths": [_text], "sources": [_text]},
    "components": {
        "sdrangel": dict(_COMMON, plugin_dirs=(_text,), install_prefix=_text),
        "sdrpp": dict(_COMMON, plugin_dirs=(_text,), launcher_globs=[_text]),
        "satdump": dict(_COMMON, plugin_dirs=(_text,), config_paths=(_text,), pipeline_dirs=(_text,), allow_pipelines=[_text], pipeline_deny_tokens=[_text],
                        required_settings=_scalars),
        "openwebrx": dict(_COMMON, modes_py=[_text], allow_modes=(_text,), deny_modes=[_text], settings_paths=(_text,), locked_settings=_scalars, users_paths=(_text,)),
        "soapy": dict(_COMMON, plugin_dirs=(_text,), forbidden_dirs=[_text]),
        "gpredict": dict(_COMMON, binaries=[_text], forbidden_needed=(_text,), radio_config_globs=[_text], rx_only_radio_type=_text,
                         tle_update={"file_globs": (_text,), "section": _text, "key": _text, "required": _text}),
    },
    "lime": {"runtime_library_globs": [_text], "sources": [_text]},
    "librtlsdr": {"library_glob": _text, "old_library_glob": _text, "soname": _text, "export_prefix": _text, "exports": int, "forbidden_strings": [_text], "sources": [_text]},
    "dream": {"binary_names": [_text], "forbidden_strings": [_text], "sources": [_text]},
    "units": {"system_unit_paths": (_text,), "unit_dirs": [_text], "environment_globs": [_text], "lease_user": _text,
              "lease_required": {"DevicePolicy": _text, "ProtectSystem": _text, "ReadOnlyPaths": _text, "ReadWritePaths": _text, "IPAddressAllow": _text,
                                 "IPAddressDeny": _text}, "sources": [_text]},
    "dataset_roots": [_text], "project_dataset_roots": [_text], "dataset_manifest_kinds": [_text], "dataset_label_keys": [_text],
    "dataset_deny_tokens": [_text], "apt_forbidden_origins": [_text],
    "apt": {"sources_globs": [_text], "forbidden_list_name_tokens": [_text], "pref_path": _text, "pref_priorities": (int,), "sources": [_text]},
    "dpkg_verify_packages": [_text], "decoder_gated_presets": [_text], "kernel_cmdline_path": _text,
}
_PATH_FIELDS = ("footprint", "plugin_dirs", "config_paths", "launcher_globs", "pipeline_dirs", "modes_py", "settings_paths", "users_paths",
                "forbidden_dirs", "binaries", "radio_config_globs", "file_globs", "extra_config_paths", "system_unit_paths", "unit_dirs",
                "environment_globs", "dataset_roots", "project_dataset_roots", "sources_globs")


def _shape(value, spec, label):
    if isinstance(spec, dict):
        deploy.keys(value, tuple(spec), label)
        for key, sub in spec.items():
            _shape(value[key], sub, label + "." + key)
    elif isinstance(spec, (list, tuple)):
        if type(value) is not list or (isinstance(spec, tuple) and not value):
            raise DeploymentError(label + (" must be a non-empty list" if isinstance(spec, tuple) else " must be a list"))
        for item in value:
            _shape(item, spec[0], label)
    elif isinstance(spec, type):
        if type(value) is not spec:
            raise DeploymentError(label + " has the wrong type")
    else:
        spec(value, label)


def _relative(pattern, label):
    parts = pattern.split("/")
    if pattern.startswith("/") or "\\" in pattern or any(p in ("", ".", "..") for p in parts):
        raise DeploymentError(label + " must be a clean relative path or glob")


def _paths(value, label):
    if type(value) is dict:
        for key, item in value.items():
            if key in _PATH_FIELDS:
                for pattern in item:
                    _relative(pattern, label + "." + key)
            else:
                _paths(item, label + "." + key)


def _json_once(path, label):
    """(value, SHA-256) of one bounded read: deploy.load's strict JSON rules (size, duplicate keys,
    no NaN/Infinity) applied to the very bytes the digest names, so a report never pairs a verdict
    with the digest of a file replaced between two reads."""
    with open(path, "rb") as handle:
        data = handle.read(4 * 1024 * 1024)
    if not data or len(data) >= 4 * 1024 * 1024:
        raise DeploymentError(label + " JSON size is invalid")

    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise DeploymentError(label + " has a duplicate JSON key")
            out[key] = value
        return out
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(DeploymentError(label + " has nonfinite JSON")))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise DeploymentError(label + " is not valid UTF-8 JSON") from None
    return value, hashlib.sha256(data).hexdigest()


def load_policy(path, digest=False):
    """Strict JSON plus exact schema; DRAFT is valid input but blocks the overall status. With
    digest=True returns (policy, SHA-256 of the bytes read)."""
    policy, sha256 = _json_once(path, "receive-only policy")
    _shape(policy, POLICY_SCHEMA, "receive-only policy")
    if policy["schema_version"] != 1 or policy["status"] not in ("DRAFT", "REVIEWED"):
        raise DeploymentError("receive-only policy schema/status is unsupported")
    _paths(policy, "receive-only policy")
    for name in ("srrx_root", "kernel_cmdline_path"):
        _relative(policy[name], name)
    for entry in policy["forbidden_path_prefixes"]:
        _relative(entry["path"], "forbidden_path_prefixes")
    _relative(policy["components"]["sdrangel"]["install_prefix"], "sdrangel.install_prefix")
    _relative(policy["apt"]["pref_path"], "apt.pref_path")
    return (policy, sha256) if digest else policy


REVIEW_FIELDS = ("schema_version", "status", "policy_sha256", "source_lock_sha256", "reviewer", "reviewed_on", "builds", "notes")


def load_review(path, policy_sha256, policy, source_lock_sha256):
    """Strict review record of a REVIEWED policy, kept apart because load_policy's schema is exact.

    policy_sha256 and source_lock_sha256 are the digests of the bytes the caller parsed. Returns
    (BOUND, or NOT_BOUND when the record answers other policy or source-lock bytes; the SHA-256 of
    the record bytes read once and validated); a malformed record raises. reviewer is a name or
    role, never an e-mail address; builds are the reviewed build outputs (name, SHA-256); notes
    answer every policy note by its index.
    """
    record, digest = _json_once(path, "policy review record")
    deploy.keys(record, REVIEW_FIELDS, "policy review record")
    if record["schema_version"] != 1 or record["status"] != "REVIEWED":
        raise DeploymentError("policy review record schema/status is unsupported")
    for name in ("policy_sha256", "source_lock_sha256"):
        if type(record[name]) is not str or not _HEX64.fullmatch(record[name]):
            raise DeploymentError("policy review record " + name + " must be 64 lowercase hex digits")
    reviewer = record["reviewer"]
    if type(reviewer) is not str or not reviewer.strip() or len(reviewer) > 128 or "@" in reviewer or not reviewer.isprintable():
        raise DeploymentError("policy review record needs a reviewer name or role (no e-mail address)")
    try:
        if type(record["reviewed_on"]) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", record["reviewed_on"]):
            raise ValueError
        date.fromisoformat(record["reviewed_on"])
    except ValueError:
        raise DeploymentError("policy review record reviewed_on must be YYYY-MM-DD") from None
    builds = record["builds"]
    if type(builds) is not list or not builds or any(type(b) is not dict or set(b) != {"name", "sha256"} or type(b["name"]) is not str
                                                     or not _SAFE_ITEM.fullmatch(b["name"]) or type(b["sha256"]) is not str
                                                     or not _HEX64.fullmatch(b["sha256"]) for b in builds) \
            or len({b["name"] for b in builds}) != len(builds):
        raise DeploymentError("policy review record needs uniquely named reviewed build outputs with SHA-256")
    notes = record["notes"]
    if type(notes) is not list or any(type(n) is not dict or set(n) != {"note", "resolution"} or type(n["note"]) is not int
                                      or type(n["resolution"]) is not str or not n["resolution"].strip() for n in notes) \
            or sorted(n["note"] for n in notes) != list(range(len(policy["notes"]))):
        raise DeploymentError("policy review record must resolve every policy note exactly once")
    bound = record["policy_sha256"] == policy_sha256 and record["source_lock_sha256"] == source_lock_sha256
    return ("BOUND" if bound else "NOT_BOUND"), digest


# ---------------------------------------------------------------- inventory and bounded I/O

def walk_rootfs(root, limit=None):
    """Inventory without following symlinks; top-level proc/sys/dev/run/tmp are skipped.

    Returns (entries, issues, complete). Special files are refused (BLOCKED), symlinks are
    recorded with their raw target and resolved later, chroot-style, inside the inventory. The
    bound is checked per entry while a directory is iterated, so one huge directory is never
    materialised; the key order is irrelevant because Ctx sorts the keys.
    """
    limit = MAX_ENTRIES if limit is None else limit
    root = Path(root)
    entries, issues, stack = {}, [], [""]
    while stack:
        rel = stack.pop()
        name = rel
        try:
            with os.scandir(root / rel if rel else root) as listing:
                for child in listing:
                    if not rel and child.name in SKIP_TOP:
                        continue
                    if len(entries) >= limit:
                        issues.append({"path": ".", "rule": "inventory_bound"})
                        return entries, issues, False
                    name = rel + "/" + child.name if rel else child.name
                    info = child.stat(follow_symlinks=False)
                    mode = info.st_mode
                    if stat.S_ISLNK(mode):
                        target = os.readlink(child.path)
                        entries[name] = Entry("link", 0, target.replace("\\", "/") if os.sep == "\\" else target)
                    elif stat.S_ISDIR(mode):
                        entries[name] = Entry("dir")
                        stack.append(name)
                    elif stat.S_ISREG(mode):
                        entries[name] = Entry("file", info.st_size)
                    else:
                        entries[name] = Entry("special")
                        issues.append({"path": name, "rule": "special_file"})
                    name = rel
        except OSError:
            issues.append({"path": name or ".", "rule": "unreadable_entry" if name != rel else "unreadable_directory"})
            return entries, issues, False
    return entries, issues, True


def _open_regular(path):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    fd = os.open(str(path), flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise DeploymentError("not a regular file")
        return os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise


def _stream_contains(handle, needles, ignore_case=False):
    needles = [n.encode() if isinstance(n, str) else n for n in needles]
    if ignore_case:
        needles = [n.lower() for n in needles]
    keep, found, tail = max(len(n) for n in needles) - 1, set(), b""
    while True:
        chunk = handle.read(CHUNK)
        if not chunk:
            return found
        window = tail + (chunk.lower() if ignore_case else chunk)
        found.update(n for n in needles if n in window)
        tail = window[-keep:] if keep else b""


@functools.lru_cache(maxsize=1024)
def _glob_regex(pattern):
    return re.compile("".join("[^/]*" if c == "*" else "[^/]" if c == "?" else re.escape(c) for c in pattern), re.S)


def _matches(name, patterns):
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


def run_bounded(args, timeout, limit):
    """Default runner: (returncode, stdout); -1 on timeout/error, -2 when stdout exceeds limit.

    None means the tool is not installed. LC_ALL=C keeps readelf/gpgv output parseable. Stdout
    is read from a pipe while the child runs and the child is killed as soon as limit+1 bytes
    arrive, so neither memory nor disk grows past the cap (a crafted ELF cannot make readelf
    write gigabytes); a cut listing would silently omit symbols, so capped output fails closed.
    """
    env = {"LC_ALL": "C", "LANG": "C", "PATH": os.environ.get("PATH", os.defpath)}
    env.update({k: os.environ[k] for k in ("SYSTEMROOT",) if k in os.environ})  # Windows interpreter start-up only
    deadline = time.monotonic() + timeout
    try:
        child = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
    except FileNotFoundError:
        return None
    except (OSError, subprocess.SubprocessError):
        return -1, ""
    chunks, state = [], {"size": 0, "capped": False, "error": False}

    def pump():
        try:
            while True:
                data = child.stdout.read1(CHUNK)
                if not data:
                    return
                state["size"] += len(data)
                if state["size"] > limit:
                    state["capped"] = True
                    child.kill()
                    return
                chunks.append(data)
        except (OSError, ValueError):
            state["error"] = True
            child.kill()

    reader = threading.Thread(target=pump, name="selftest-bounded-reader", daemon=True)
    reader.start()
    reader.join(max(deadline - time.monotonic(), 0))
    timed_out = reader.is_alive()
    if timed_out:
        child.kill()
        reader.join(5)
    try:
        code = child.wait(max(deadline - time.monotonic(), 0.1))
    except subprocess.TimeoutExpired:
        child.kill()
        timed_out = True
        try:
            child.wait(5)
        except subprocess.TimeoutExpired:
            pass
    if not reader.is_alive():
        child.stdout.close()
    if state["capped"]:
        return -2, ""
    if timed_out or state["error"] or reader.is_alive():
        return -1, ""
    return code, b"".join(chunks).decode("utf-8", "replace")


def elf_dynamic(path, runner=None):
    """Bounded `readelf -d --dyn-syms -W`; truncated or partial output fails closed."""
    result = (runner or run_bounded)(["readelf", "-d", "--dyn-syms", "-W", str(path)], READELF_TIMEOUT, READELF_LIMIT)
    if result is None:
        raise ElfError("readelf_unavailable")
    code, text = result
    if code != 0 or type(text) is not str:
        raise ElfError("readelf_failed")
    header = re.search(r"^Dynamic section at offset \S+ contains (\d+) entr(?:y|ies):", text, re.M)
    if header is None:
        if "There is no dynamic section in this file." not in text:
            raise ElfError("readelf_output_truncated")
        return {"needed": [], "soname": None, "symbols": []}
    if len(re.findall(r"^\s*0x[0-9a-fA-F]+\s+\([A-Za-z0-9_]+\)", text, re.M)) != int(header.group(1)):
        raise ElfError("readelf_output_truncated")
    needed = re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]\n]+)\]", text)
    sonames = re.findall(r"\(SONAME\)\s+Library soname: \[([^\]\n]+)\]", text)
    table = re.search(r"^Symbol table '\.dynsym' contains (\d+) entr(?:y|ies):\n[^\n]*\n((?:[ \t]*\d+:[^\n]*(?:\n|$))*)", text, re.M)
    if table is None or len(sonames) > 1:
        raise ElfError("readelf_output_truncated")
    rows = [line for line in table.group(2).splitlines() if line.strip()]
    if len(rows) != int(table.group(1)):
        raise ElfError("readelf_output_truncated")
    symbols = []
    for line in rows:
        fields = line.split()
        if len(fields) < 7:
            raise ElfError("readelf_output_truncated")
        if len(fields) >= 8:
            symbols.append((fields[7], fields[3], fields[4], fields[6]))
    return {"needed": needed, "soname": sonames[0] if sonames else None, "symbols": symbols}


def verify_signature(manifest, signature, keyring, runner=None):
    """Bounded gpgv; returns None for a good signature, else a BLOCKED rule id."""
    result = (runner or run_bounded)(["gpgv", "--status-fd", "1", "--keyring", str(keyring), str(signature), str(manifest)], GPGV_TIMEOUT, GPGV_LIMIT)
    if result is None:
        return "gpgv_unavailable"
    code, text = result
    good = code == 0 and type(text) is str and re.search(r"^\[GNUPG:\] VALIDSIG ", text, re.M) and re.search(r"^\[GNUPG:\] GOODSIG ", text, re.M)
    return None if good else "manifest_signature_invalid"


def parse_dpkg_status(path, limit=None):
    """[{package, version, state}] from a dpkg status file; bounded and fail closed."""
    limit = MAX_DPKG_STATUS if limit is None else limit
    with _open_regular(path) as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise DeploymentError("dpkg status exceeds bound")
    records = []
    for block in re.split(r"\n[ \t\r]*\n", data.decode("utf-8", "replace")):
        fields = {}
        for line in block.splitlines():
            if not line.strip() or line[0] in " \t":
                continue  # continuation line of a multi-line field
            key, sep, value = line.partition(":")
            if not sep or key.strip().lower() in fields:
                raise DeploymentError("malformed dpkg status paragraph")
            fields[key.strip().lower()] = value.strip()
        if not fields:
            continue
        if not fields.get("package") or len(records) >= MAX_DPKG_RECORDS:
            raise DeploymentError("malformed or oversized dpkg status")
        words = fields.get("status", "").split()
        # Anything but not-installed/config-files has files on disk (unpacked, half-*, triggers-*).
        records.append({"package": fields["package"].lower(), "version": fields.get("version", ""),
                        "state": words[2] if len(words) == 3 else "unknown"})
    return records


# The version rules doctor applies too (one evaluator, so doctor and RX-01a cannot disagree).
deb_compare, _version_forbidden = deploy.deb_compare, deploy.version_forbidden


# ---------------------------------------------------------------- context and results

class Result:
    def __init__(self, row):
        self.id, self.row, self.evaluability, self.title, self.sources = row
        self.findings, self.notes, self.dropped = [], [], {"FAIL": 0, "BLOCKED": 0}

    def add(self, effect, path, rule, item=None):
        finding = {"path": str(path)[:512], "rule": rule, "effect": effect}
        if item is not None and _SAFE_ITEM.fullmatch(str(item)):
            finding["item"] = str(item)
        if finding in self.findings:
            return
        if len(self.findings) >= MAX_FINDINGS:
            self.dropped[effect] += 1
            return
        self.findings.append(finding)

    def fail(self, path, rule, item=None):
        self.add("FAIL", path, rule, item)

    def block(self, path, rule, item=None):
        self.add("BLOCKED", path, rule, item)

    def note(self, text):
        if text not in self.notes:
            self.notes.append(text)

    def status(self):
        if self.evaluability == "NOT_IMPLEMENTED":
            return "BLOCKED"
        if self.evaluability != "OFFLINE":
            return "RUNTIME_ONLY"  # never PASS without offline evidence
        effects = {f["effect"] for f in self.findings} | {k for k, v in self.dropped.items() if v}
        return "FAIL" if "FAIL" in effects else "BLOCKED" if "BLOCKED" in effects else "PASS"

    def report(self):
        out = {"id": self.id, "build07_row": self.row, "evaluability": self.evaluability, "status": self.status(),
               "title": self.title, "findings": self.findings, "notes": self.notes, "sources": list(self.sources)}
        if any(self.dropped.values()):
            out["findings_dropped"] = dict(self.dropped)
        return out


class Ctx:
    def __init__(self, rootfs, profile, policy, project, manifests, keyring, cmdline_sha256, runner):
        self.root, self.profile, self.policy, self.project = rootfs, profile, policy, project
        self.manifests, self.keyring, self.cmdline_sha256, self.runner = manifests, keyring, cmdline_sha256, runner
        self.entries, self.issues, self.complete = walk_rootfs(rootfs)
        self.keys = sorted(self.entries)
        self._elf, self._dpkg, self._elf_files, self._children = {}, None, None, None
        self.evaluated = {}  # checker srrx module -> SHA-256, reported as tool_dependencies
        for rel in self.keys:
            if self.entries[rel].kind == "link":
                reason = self.resolve(rel, why=True)[1]
                if reason in ("escape", "loop"):
                    self.issues.append({"path": rel, "rule": "symlink_escapes_rootfs" if reason == "escape" else "symlink_loop"})

    def comp(self, name):
        return self.policy["components"][name]

    def resolve(self, rel, why=False):
        """Chroot-style lexical resolution inside the inventory; host paths are never followed."""
        out, queue, hops = [], [p for p in rel.split("/") if p], 0
        while queue:
            part = queue.pop(0)
            if part == ".":
                continue
            if part == "..":
                if not out:
                    return (None, "escape") if why else None
                out.pop()
                continue
            out.append(part)
            entry = self.entries.get("/".join(out))
            if entry is None:
                return (None, "dangling") if why else None
            if entry.kind == "link":
                hops += 1
                if hops > MAX_HOPS:
                    return (None, "loop") if why else None
                out.pop()
                if entry.target.startswith("/"):
                    out = []
                queue[:0] = [p for p in entry.target.split("/") if p]
        final = "/".join(out)
        return (final, None) if why else final

    def masked(self, rel):
        """True when rel is a symlink chain ending at /dev/null (systemd mask); dev/ is never
        inventoried, so this is decided lexically on the link targets."""
        for _ in range(MAX_HOPS):
            entry = self.entries.get(rel)
            if entry is None or entry.kind != "link":
                return False
            target = posixpath.normpath(posixpath.join("/" + posixpath.dirname(rel), entry.target))
            if target == "/dev/null":
                return True
            parent = posixpath.dirname(target).lstrip("/")
            resolved = self.resolve(parent) if parent else ""
            if resolved is None:
                return False
            rel = (resolved + "/" if resolved else "") + posixpath.basename(target)
        return False

    def resolve_kind(self, rel, kind):
        final = self.resolve(rel)
        entry = self.entries.get(final) if final else None
        return final if entry is not None and entry.kind == kind else None

    def file(self, rel):
        return self.resolve_kind(rel, "file")

    def under(self, prefix):
        start = prefix + "/"
        for key in self.keys[bisect_left(self.keys, start):]:
            if not key.startswith(start):
                return
            yield key

    def children(self, directory):
        """Names directly inside one resolved inventory directory ("" is the rootfs root)."""
        if self._children is None:
            self._children = {}
            for key in self.keys:
                parent, _, name = key.rpartition("/")
                self._children.setdefault(parent, []).append(name)
        return self._children.get(directory, [])

    def glob(self, pattern):
        """Chroot-style glob: every non-final component that is a symlink is resolved inside the
        inventory, so content below a symlinked parent (SoapySDR -> /opt/x) is still matched.
        Returns the lexical matches (pattern instantiations); a leaf link is not resolved."""
        parts, found = pattern.split("/"), [("", "")]  # (lexical path, resolved directory)
        for index, part in enumerate(parts):
            last, step = index == len(parts) - 1, []
            for lexical, directory in found:
                base = directory + "/" if directory else ""
                if any(c in part for c in "*?["):
                    names = [n for n in self.children(directory) if fnmatch.fnmatchcase(n, part)]
                else:
                    names = [part] if base + part in self.entries else []
                for name in names:
                    path = (lexical + "/" if lexical else "") + name
                    if last:
                        step.append((path, None))
                        continue
                    resolved = self.resolve_kind(base + name, "dir")
                    if resolved is not None:
                        step.append((path, resolved))
            found = step
        return sorted({lexical for lexical, _ in found})

    def globs(self, patterns):
        return sorted({match for pattern in patterns for match in self.glob(pattern)})

    def files_in(self, patterns):
        """(listed path, resolved file) for every file below the directories the patterns match."""
        out, seen = {}, set()
        pending = [d for d in (self.resolve_kind(m, "dir") for m in self.globs(patterns)) if d is not None]
        while pending:
            directory = pending.pop()
            if directory in seen:
                continue
            seen.add(directory)
            for key in self.under(directory):
                entry = self.entries[key]
                if entry.kind == "file":
                    out.setdefault(key, key)
                elif entry.kind == "link":
                    final = self.resolve(key)
                    target = self.entries.get(final) if final else None
                    if target is not None and target.kind == "file":
                        out.setdefault(key, final)
                    elif target is not None and target.kind == "dir":
                        pending.append(final)
        return sorted(out.items())

    def open(self, final):
        return _open_regular(self.root / final)

    def read(self, final, limit=MAX_TEXT):
        with self.open(final) as handle:
            data = handle.read(limit + 1)
        if len(data) > limit:
            raise Blocked(final, "input_too_large")
        return data

    def text(self, final, limit=MAX_TEXT):
        return self.read(final, limit).decode("utf-8", "replace")

    def json(self, final):
        try:
            return deploy.load(self.root / final)
        except (DeploymentError, ValueError, UnicodeError):
            raise Blocked(final, "json_unparsable") from None

    def contains(self, final, needles, ignore_case=False):
        with self.open(final) as handle:
            return _stream_contains(handle, needles, ignore_case)

    def digest(self, final, algorithm="sha256"):
        with self.open(final) as handle:
            return hashlib.file_digest(handle, lambda: hashlib.new(algorithm, usedforsecurity=False)).hexdigest()

    def is_elf(self, final):
        with self.open(final) as handle:
            return handle.read(4) == ELF_MAGIC

    def elf_files(self):
        if self._elf_files is None:
            self._elf_files = [k for k in self.keys if self.entries[k].kind == "file" and self.entries[k].size >= 16 and self.is_elf(k)]
        return self._elf_files

    def elf(self, final, result):
        if final not in self._elf:
            try:
                self._elf[final] = elf_dynamic(self.root / final, self.runner)
            except ElfError as exc:
                self._elf[final] = exc.rule
        info = self._elf[final]
        if isinstance(info, str):
            result.block(final, info)
            return None
        return info

    def dpkg(self):
        """(status path or None, {package: [versions]} of present packages)."""
        if self._dpkg is None:
            final = self.file("var/lib/dpkg/status")
            present = {}
            try:
                records = parse_dpkg_status(self.root / final) if final is not None else []
            except (DeploymentError, OSError):
                raise Blocked("var/lib/dpkg/status", "dpkg_status_unparsable") from None
            for record in records:
                if record["state"] not in ("not-installed", "config-files"):
                    present.setdefault(record["package"], []).append(record["version"])
            self._dpkg = (final, present)
        return self._dpkg

    def unit_texts(self):
        """(listed, resolved file) of every system and user unit/drop-in file (launcher scans)."""
        units = self.policy["units"]
        return self.files_in(list(dict.fromkeys(units["system_unit_paths"] + units["unit_dirs"])))


def _presence(ctx, result, found, name):
    """Profile controller requires absence; profile full requires a found component."""
    if ctx.profile == "controller":
        for rel in found:
            result.fail(rel, "radio_application_in_controller_profile")
        if not found:
            result.note(name + "_absent")
        return
    if not found:
        result.block(".", "component_not_found", name)


def _plugin_name(base, suffixes=("srv",)):
    name = base.lower()
    name = name[3:] if name.startswith("lib") else name
    name = name.split(".so", 1)[0]
    for suffix in suffixes:
        if name.endswith(suffix) and len(name) > len(suffix):
            name = name[:-len(suffix)]
    return name


def _module_words(ctx):
    return tuple(w.lower() for w in deploy.BAD_MODULE_WORDS) + tuple(e["word"].lower() for e in ctx.policy["forbidden_module_words"])


def _walk_json(value, depth=0):
    if depth > MAX_DEPTH:
        raise ValueError("JSON nesting exceeds bound")
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _walk_json(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_json(item, depth + 1)


def _strings(value, depth=0):
    """Every string scalar of a parsed JSON document (values and list items, not keys)."""
    if depth > MAX_DEPTH:
        raise ValueError("JSON nesting exceeds bound")
    if isinstance(value, str):
        yield value
    elif isinstance(value, (dict, list)):
        for item in value.values() if isinstance(value, dict) else value:
            yield from _strings(item, depth + 1)


def _scalar(text):
    text = text.strip().strip('"\'')
    if re.fullmatch(r"[+-]?\d{1,18}", text):
        return int(text)
    return {"true": True, "false": False}.get(text.lower(), text)


def _ini(text):
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


@functools.lru_cache(maxsize=64)
def srrx_closure(name):
    """The checker's srrx modules that importing srrx.<name> loads: __init__, the module and every
    srrx module it imports (relative or srrx.*, at any depth of the code), transitively."""
    package = deploy.PROJECT / "software/srrx"
    pending, seen = [name], {"__init__"}
    while pending:
        current = pending.pop()
        if current in seen or not (package / (current + ".py")).is_file():
            continue
        seen.add(current)
        for node in ast.walk(ast.parse((package / (current + ".py")).read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom):
                module = (node.module or "").split(".")
                if node.level == 1:
                    parts = module
                elif node.level == 0 and module[0] == "srrx":
                    parts = module[1:]
                else:
                    continue
                pending.extend([parts[0]] if parts and parts[0] else [alias.name for alias in node.names])
            elif isinstance(node, ast.Import):
                pending.extend(a.name.split(".")[1] for a in node.names if a.name.startswith("srrx."))
    return tuple(sorted(seen))


def _target_identical(ctx, result, name):
    """True when the target copy of srrx.<name> and of each srrx module it imports is byte-identical
    to the checker's; each missing or differing copy is a BLOCKED finding."""
    package = deploy.PROJECT / "software/srrx"
    problems = 0
    for dependency in srrx_closure(name):
        source = package / (dependency + ".py")
        rel = ctx.policy["srrx_root"] + "/software/srrx/" + dependency + ".py"
        final = ctx.file(rel)
        if final is None:
            result.block(rel, "target_module_missing")
            problems += 1
            continue
        digest = deploy.sha(source)
        ctx.evaluated["software/srrx/" + dependency + ".py"] = digest
        if ctx.digest(final) != digest:
            result.block(rel, "target_module_differs")
            problems += 1
    return not problems


def _target_module(ctx, result, name):
    """Checker's own srrx module, only when the target copies are identical (_target_identical);
    otherwise BLOCKED and nothing is imported."""
    package = deploy.PROJECT / "software/srrx"
    if not _target_identical(ctx, result, name):
        return None
    software = str(deploy.PROJECT / "software")
    if software not in sys.path:
        sys.path.insert(0, software)
    module = importlib.import_module("srrx." + name)
    for dependency in srrx_closure(name):
        loaded = sys.modules.get("srrx" if dependency == "__init__" else "srrx." + dependency)
        if loaded is not None and Path(loaded.__file__).resolve() != (package / (dependency + ".py")).resolve():
            result.block(ctx.policy["srrx_root"] + "/software/srrx/" + dependency + ".py", "checker_module_path_mismatch")
            return None
    return module


# ---------------------------------------------------------------- checks

def check_00(ctx, r):
    for issue in ctx.issues:
        r.block(issue["path"], issue["rule"])


def check_01a(ctx, r):
    final, present = ctx.dpkg()
    if final is None:
        if ctx.profile == "controller":
            return r.note("dpkg_database_absent_controller_overlay")
        return r.block("var/lib/dpkg/status", "dpkg_database_missing")
    for name in sorted(present):
        for rule in ctx.policy["forbidden_packages"]:
            if (name == rule["name"] if "name" in rule else fnmatch.fnmatchcase(name, rule["glob"])):
                if any(_version_forbidden(rule.get("version_rule"), v) for v in present[name]):
                    item = rule.get("name") or rule["glob"]  # policy identifier: the dpkg text is never echoed
                    if rule["check"] == "presence":
                        r.fail("var/lib/dpkg/status", "forbidden_package", item)
                    else:  # apt -1 pin target present: drift unless a reviewed version rule allows it
                        r.block("var/lib/dpkg/status", "pinned_package_present_unreviewed", item)


def check_01b(ctx, r):
    policy = ctx.policy
    names = deploy.forbidden_basenames(policy)  # the set doctor checks: BAD_NAMES, PROHIBITED_EXECUTABLES, policy
    parts = {p.lower() for p in deploy.BAD_PARTS} | {e["name"].lower() for e in policy["forbidden_path_parts"]}
    prefixes = {e["path"] for e in policy["forbidden_path_prefixes"]}
    suffixes = tuple(e["suffix"].lower() for e in policy["forbidden_suffixes"])
    dream = {n.lower() for n in policy["dream"]["binary_names"]}
    for rel in ctx.keys:
        base = rel.rsplit("/", 1)[-1].lower()
        if base in names:
            r.fail(rel, "forbidden_basename")
        if base in parts:
            r.fail(rel, "forbidden_path_part")
        if base.endswith(suffixes):
            r.fail(rel, "forbidden_suffix")
        if rel in prefixes:
            r.fail(rel, "forbidden_path")
        if base in dream:
            final = ctx.file(rel)
            if final is not None and ctx.contains(final, policy["dream"]["forbidden_strings"]):
                r.fail(rel, "dream_transmitter_strings")


def check_01c(ctx, r):
    rules, comps = ctx.policy["engine_config_rules"], ctx.policy["components"]
    patterns = [p for name in ("sdrangel", "sdrpp", "satdump", "openwebrx", "soapy") for p in comps[name]["config_paths"]] + rules["extra_config_paths"]
    owrx = [_glob_regex(p) for p in comps["openwebrx"]["config_paths"]]
    ds_keys, bias = {k.lower() for k in rules["direct_sampling_keys"]}, {k.lower() for k in rules["bias_keys"]}
    modes, rates = {k.lower() for k in rules["direct_sampling_mode_keys"]}, {k.lower() for k in rules["hfplus_rate_keys"]}

    def setting(rel, key, value):
        key = str(key).strip().strip("\"'").lower()
        keys = {key, re.split(r"[\\/.]", key)[-1]}  # QSettings "rtlsdr\biasTee", dotted "devices.x.biasT"
        if keys & ds_keys:
            r.fail(rel, "direct_sampling_key")
        if keys & modes and not (type(value) is int and value == 0):
            r.fail(rel, "direct_sampling_nonzero")
        if keys & bias:
            r.fail(rel, "bias_key")

    for rel in ctx.globs(patterns):
        final = ctx.file(rel)
        if final is None:
            continue
        if final.lower().endswith(".json"):
            data = ctx.json(final)
            items, strings = list(_walk_json(data)), list(_strings(data))
        else:
            text = ctx.text(final)
            items = [(k, _scalar(v)) for section in _ini(text).values() for k, values in section.items() for v in values]
            items += [(m.group(1), _scalar(m.group(2))) for m in re.finditer(r"(?m)^\s*([A-Za-z_][\w.-]*)\s*:\s*(\S[^\n]*)$", text)]
            strings = [v for _, v in items if isinstance(v, str)]
        for key, value in items:
            setting(rel, key, value)
            if (any(p.fullmatch(rel) for p in owrx) and str(key).lower() in rates and type(value) in (int, float)
                    and value == rules["hfplus_forbidden_rate"]):
                r.fail(rel, "hfplus_rate_256000")
        # Soapy device arguments live in strings: "driver=rtlsdr,direct_samp=2", "biastee=true".
        for value in strings:
            for token in re.split(r"[,;\s]+", value):
                key, sep, argument = token.partition("=")
                if sep and key:
                    setting(rel, key, _scalar(argument))


def _component_manifest(ctx, r, name, prefix):
    spec = ctx.manifests.get(name)
    if spec is None:
        return r.block(prefix, "component_manifest_missing", name)
    manifest, signature = spec
    before = deploy.sha(manifest)
    if signature is None or ctx.keyring is None:
        r.block(prefix, "manifest_signature_unverified", name)
    else:
        problem = verify_signature(manifest, signature, ctx.keyring, ctx.runner)
        if problem:
            r.block(prefix, problem, name)
    record = deploy.load(manifest)
    if deploy.sha(manifest) != before:
        return r.block(prefix, "manifest_changed_during_check", name)
    try:
        deploy.keys(record, ("schema_version", "status", "files", "allowed_modules", "source_audit", "tx_negative_tests"), "component manifest")
    except DeploymentError:
        return r.block(prefix, "component_manifest_invalid", name)
    if record["status"] != "REVIEWED" or record["schema_version"] != 1:
        return r.block(prefix, "component_manifest_not_reviewed", name)
    entry = ctx.entries.get(prefix)
    if entry is None or entry.kind != "dir":
        return r.block(prefix, "component_prefix_missing", name)
    # verify_build resolves links with Path.resolve: an absolute target would name a host path.
    absolute = [k for k in ctx.under(prefix) if ctx.entries[k].kind == "link" and ctx.entries[k].target.startswith("/")]
    if absolute:
        return r.block(absolute[0], "absolute_symlink_in_component_prefix", name)
    try:
        deploy.verify_build(ctx.root / prefix, record)
    except DeploymentError:
        r.fail(prefix, "component_manifest_mismatch", name)


def check_02(ctx, r):
    comp = ctx.comp("sdrangel")
    plugins = ctx.files_in(comp["plugin_dirs"])
    found = sorted(set(ctx.globs(comp["footprint"])) | {listed for listed, _ in plugins})
    _presence(ctx, r, found, "sdrangel")
    allow, deny, words, present = set(comp["allow_plugins"]), comp["deny_tokens"], _module_words(ctx), set()
    for listed, _ in plugins:
        base = listed.rsplit("/", 1)[-1].lower()
        if ".so" not in base:
            continue
        name = _plugin_name(base)
        if any(t in name for t in deny) or any(w in base for w in words):
            r.fail(listed, "deny_token")
        matched = {name, name[5:] if name.startswith("input") else name, name[7:] if name.startswith("feature") else name} & allow
        present |= matched
        if not matched:
            r.fail(listed, "plugin_not_allowlisted")
        if not listed.startswith(comp["install_prefix"] + "/"):
            r.fail(listed, "outside_reviewed_prefix")
    if ctx.profile == "full" and found:
        for missing in sorted(allow - present):  # build/07:415-419: the plugin set equals the allowlist
            r.fail(comp["plugin_dirs"][0], "allowlisted_plugin_missing", missing)
        _component_manifest(ctx, r, "sdrangel", comp["install_prefix"])


_SDRPP_SERVER = re.compile(r"(?m)\bsdrpp\b[^\n]*?\s(?:--server|-s)(?=[\s=]|$)")


def check_03(ctx, r):
    comp = ctx.comp("sdrpp")
    plugins = ctx.files_in(comp["plugin_dirs"])
    found = sorted(set(ctx.globs(comp["footprint"])) | {listed for listed, _ in plugins})
    _presence(ctx, r, found, "sdrpp")
    allow, names, words = {a.lower() for a in comp["allow_plugins"]}, set(), _module_words(ctx)
    for listed, _ in plugins:
        base = listed.rsplit("/", 1)[-1].lower()
        if ".so" not in base:
            continue
        name = base.split(".so", 1)[0]
        names.add(name)
        if any(t in name for t in comp["deny_tokens"]) or any(w in base for w in words):
            r.fail(listed, "forbidden_module")
        if name not in allow:
            r.fail(listed, "plugin_not_allowlisted")
    if ctx.profile == "full" and found:
        for missing in sorted(allow - names):
            r.fail(comp["plugin_dirs"][0], "allowlisted_module_missing", missing)
    launchers = {final: listed for listed, final in ctx.unit_texts()}
    launchers.update({f: rel for rel, f in ((rel, ctx.file(rel)) for rel in ctx.globs(comp["launcher_globs"])) if f})
    for final, listed in sorted(launchers.items()):
        if ctx.is_elf(final):
            continue
        if _SDRPP_SERVER.search(ctx.text(final)):
            r.fail(listed, "sdrpp_server_launcher")


def _setting_values(data, key):
    for k, value in _walk_json(data):
        if k == key:
            yield value.get("value") if isinstance(value, dict) else value


def check_04(ctx, r):
    comp = ctx.comp("satdump")
    plugins = ctx.files_in(comp["plugin_dirs"])
    pipelines = ctx.files_in(comp["pipeline_dirs"])
    found = sorted(set(ctx.globs(comp["footprint"])) | {listed for listed, _ in plugins + pipelines})
    _presence(ctx, r, found, "satdump")
    allow, words = set(comp["allow_plugins"]), _module_words(ctx)
    names = set()
    for listed, _ in plugins:
        base = listed.rsplit("/", 1)[-1].lower()
        if ".so" not in base:
            continue
        name = _plugin_name(base, ("_sdr_support", "_support"))
        names.add(name)
        if any(t in base for t in comp["deny_tokens"]) or any(w in base for w in words):
            r.fail(listed, "deny_token")
        if ("sdr_support" in base or "sdr_source" in base) and name != "net_source":
            r.fail(listed, "sdr_source_not_allowed")
        if name not in allow:
            r.fail(listed, "plugin_not_allowlisted")
    pipeline_names = set()
    for listed, final in pipelines:
        base = listed.rsplit("/", 1)[-1]
        pipeline_names.add(base)
        if base.lower().endswith(".json.inc"):
            r.fail(listed, "pipeline_include_forbidden")
        if base not in comp["allow_pipelines"]:
            r.fail(listed, "pipeline_not_allowlisted")
            continue
        data = ctx.json(final)
        for key, _ in _walk_json(data):
            if any(t in str(key).lower() for t in comp["pipeline_deny_tokens"]):
                r.fail(listed, "pipeline_mqtt" if "mqtt" in str(key).lower() else "hidden_pipeline_present")
    if ctx.profile == "full" and found:
        for missing in sorted(set(comp["allow_pipelines"]) - pipeline_names):
            r.fail(comp["pipeline_dirs"][0], "allowlisted_pipeline_missing", missing)
        for missing in sorted(allow - names):
            r.fail(comp["plugin_dirs"][0], "allowlisted_plugin_missing", missing)
    configs = [f for f in (ctx.file(rel) for rel in ctx.globs(comp["config_paths"])) if f]
    if found and not configs:
        r.fail(comp["config_paths"][0], "satdump_config_missing")
    for final in configs:
        data = ctx.json(final)
        for key, required in comp["required_settings"].items():
            values = list(_setting_values(data, key))
            if not values or any(v != required for v in values):
                r.fail(final, "kepler_update_not_never" if key == "kepler_update_interval" else "required_setting", key)
        for key, value in _walk_json(data):
            value = value.get("value") if isinstance(value, dict) else value
            if "record" in str(key).lower() and value is True:
                r.fail(final, "recording_enabled")  # the key is target text: not echoed
    for rel in ctx.keys:
        if rel.rsplit("/", 1)[-1] == "pipelines.json":
            r.fail(rel, "user_pipelines_json")
    r.note("baseline_decode_is_RX-04-decode_builder_row")


def _modes(ctx, final):
    try:
        tree = ast.parse(ctx.read(final, 1024 * 1024).decode("utf-8"), filename="modes.py")
    except (SyntaxError, ValueError, UnicodeError, RecursionError):
        raise Blocked(final, "modes_unparsable") from None
    modes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if name.endswith("Mode"):
                modes.add(node.args[0].value)
    if not modes:
        raise Blocked(final, "modes_not_found")
    return modes


def _password_present(users):
    if isinstance(users, dict):
        users = users.get("users", list(users.values()))
    if not isinstance(users, list):
        return False
    def secret(value):
        return (type(value) is str and bool(value)) or (isinstance(value, dict) and type(value.get("value")) is str and bool(value["value"]))
    return any(isinstance(u, dict) and u.get("enabled", True) is not False and secret(u.get("password")) for u in users)


def _package_files(ctx, suffix):
    """Inventory entries ending in /<suffix> anywhere (a venv or vendored copy is still found)."""
    return {k for k in ctx.keys if ("/" + k).endswith("/" + suffix)}


def check_05(ctx, r):
    comp = ctx.comp("openwebrx")
    modes_files = sorted(set(ctx.globs(comp["modes_py"])) | _package_files(ctx, "owrx/modes.py"))
    package = {k.rsplit("/", 1)[0] for k in _package_files(ctx, "owrx/__init__.py") | _package_files(ctx, "owrx/modes.py")}
    found = sorted(set(ctx.globs(comp["footprint"])) | package)
    _presence(ctx, r, found, "openwebrx")
    allow, deny = [m.lower() for m in comp["allow_modes"]], [m.lower() for m in comp["deny_modes"]]
    parsed = 0
    for rel in modes_files:
        final = ctx.file(rel)
        if final is None:
            continue
        try:
            modes = _modes(ctx, final)
        except Blocked as exc:
            r.block(rel, exc.rule)
            continue
        parsed += 1
        for mode in sorted(modes):  # mode names come from target code: only policy patterns are echoed
            denied = [p for p in deny if fnmatch.fnmatchcase(mode.lower(), p)]
            if denied:
                r.fail(rel, "mode_denied", denied[0])
            if not _matches(mode.lower(), allow):
                r.fail(rel, "mode_not_allowlisted")
    if found and not parsed:
        r.block(found[0], "modes_py_not_found")  # the mode allowlist was never evaluated
    settings = [f for f in (ctx.file(rel) for rel in ctx.globs(comp["settings_paths"])) if f]
    if found and not settings:
        r.fail(comp["settings_paths"][0], "settings_missing")
    for final in settings:
        data = ctx.json(final)
        for key, locked in comp["locked_settings"].items():
            if type(data) is not dict or key not in data or type(data[key]) is not type(locked) or data[key] != locked:
                r.fail(final, "locked_setting", key)
    if found:
        users = [f for f in (ctx.file(rel) for rel in ctx.globs(comp["users_paths"])) if f]
        # Presence only: the password value is never compared, copied or reported.
        if not users or not any(_password_present(ctx.json(f)) for f in users):
            r.fail(comp["users_paths"][0], "admin_password_missing")
    r.note("direct_sampling_keys_are_RX-01c")


def _environment_files(ctx):
    files = {final: listed for listed, final in ctx.unit_texts()}
    files.update({f: rel for rel, f in ((rel, ctx.file(rel)) for rel in ctx.globs(ctx.policy["units"]["environment_globs"])) if f})
    return sorted(files.items())


def check_06(ctx, r):
    comp = ctx.comp("soapy")
    modules = ctx.files_in(comp["plugin_dirs"])
    allow, names, words = {a.lower() for a in comp["allow_plugins"]}, set(), _module_words(ctx)
    for listed, _ in modules:
        base = listed.rsplit("/", 1)[-1].lower()
        if ".so" not in base:
            continue
        name = base.split(".so", 1)[0]
        names.add(name)
        if "lime" in name:
            r.fail(listed, "lime_module_while_lime_disabled")
        if any(t in name for t in comp["deny_tokens"]) or any(w in base for w in words):
            r.fail(listed, "deny_token")
        if name not in allow:
            r.fail(listed, "module_not_allowlisted")
    for rel in ctx.globs(comp["forbidden_dirs"]):
        r.fail(rel, "soapy_0_9_modules")
    if ctx.profile == "full" and not modules:
        r.block(".", "component_not_found", "soapy")
    elif ctx.profile == "full":
        for missing in sorted(allow - names):
            r.fail(comp["plugin_dirs"][0], "allowlisted_module_missing", missing)
    for final, listed in _environment_files(ctx):
        if not ctx.is_elf(final) and ctx.contains(final, ["SOAPY_SDR_PLUGIN_PATH"]):
            r.fail(listed, "soapy_plugin_path_override")
    r.note("SoapySDRUtil_info_is_RX-06-info_builder_row")


def check_07(ctx, r):
    for rel in ctx.keys:
        if ".so" in rel.rsplit("/", 1)[-1].lower() and "amarisoft" in rel.lower():
            r.fail(rel, "amarisoft_module")


def check_08(ctx, r):
    listed = ctx.globs(ctx.comp("soapy")["plugin_dirs"])
    soapy = sorted({d + "/" for d in listed} | {f + "/" for f in (ctx.resolve_kind(d, "dir") for d in listed) if f})  # RX-06 owns modules
    globs = [g.lower() for g in ctx.policy["lime"]["runtime_library_globs"]]
    for rel in ctx.keys:
        if ctx.entries[rel].kind in ("file", "link") and _matches(rel.rsplit("/", 1)[-1].lower(), globs) and not rel.startswith(tuple(soapy)):
            r.fail(rel, "lime_runtime_library")
    r.note("txen_register_and_tx_stream_are_RX-08-hw")


def check_09(ctx, r):
    lib = ctx.policy["librtlsdr"]
    libs = {}
    for rel in ctx.keys:
        base = rel.rsplit("/", 1)[-1]
        if fnmatch.fnmatchcase(base, lib["old_library_glob"]):
            r.fail(rel, "librtlsdr0_present")
        if fnmatch.fnmatchcase(base, lib["library_glob"]):
            final = ctx.file(rel)
            if final is not None:
                libs.setdefault(final, rel)
    if not libs:
        if ctx.profile == "controller":
            r.note("librtlsdr_not_staged")
        else:
            r.block(".", "librtlsdr_missing")
    for final in sorted(libs):
        if not ctx.is_elf(final):
            r.block(final, "not_elf")
            continue
        info = ctx.elf(final, r)
        if info is None:
            continue
        if info["soname"] != lib["soname"]:
            r.fail(final, "librtlsdr_soname")
        exports = {n.split("@", 1)[0] for n, _, _, ndx in info["symbols"] if ndx != "UND" and n.startswith(lib["export_prefix"])}
        if len(exports) != lib["exports"]:
            r.fail(final, "librtlsdr_export_count")
        if ctx.contains(final, lib["forbidden_strings"], ignore_case=True):
            r.fail(final, "zero_copy_string")
    for final in ctx.elf_files():
        if final in libs or not ctx.contains(final, ["librtlsdr"]):
            continue  # NEEDED names live verbatim in .dynstr; others cannot need it
        info = ctx.elf(final, r)
        if info is not None and any(n.startswith("librtlsdr") and n != lib["soname"] for n in info["needed"]):
            r.fail(final, "rtlsdr_consumer_wrong_soname")
    r.note("token_and_bias_tests_are_RX-09-hw")


def check_10(ctx, r):
    comp = ctx.comp("gpredict")
    binaries = set(ctx.globs(comp["binaries"])) | {k for k in ctx.keys if k.rsplit("/", 1)[-1] == "gpredict" and k.split("/")[-2:-1] in (["bin"], ["sbin"])}
    found = sorted(set(ctx.globs(comp["footprint"])) | binaries)
    _presence(ctx, r, found, "gpredict")
    evaluated = 0
    for rel in sorted(binaries):
        final = ctx.file(rel)
        if final is None:
            continue
        if not ctx.is_elf(final):
            r.block(rel, "not_elf")
            continue
        info = ctx.elf(final, r)
        if info is None:
            continue
        evaluated += 1
        for needed in info["needed"]:
            for prefix in comp["forbidden_needed"]:
                if needed.lower().startswith(prefix.lower()):
                    r.fail(rel, "forbidden_dependency", prefix)  # the policy prefix, not the DT_NEEDED text
    if found and not evaluated:
        r.block(found[0], "gpredict_binary_not_found")  # DT_NEEDED was never evaluated
    for rel in ctx.globs(comp["radio_config_globs"]):
        final = ctx.file(rel)
        if final is None:
            continue
        types = [v for section in _ini(ctx.text(final)).values() for v in section.get("type", [])]
        if not types:
            r.fail(rel, "radio_type_missing")
        elif any(v != comp["rx_only_radio_type"] for v in types):
            r.fail(rel, "radio_type_not_rx_only")
    if found:
        tle = comp["tle_update"]
        configs = [f for f in (ctx.file(rel) for rel in ctx.globs(tle["file_globs"])) if f]
        if not configs:
            r.fail(tle["file_globs"][0], "tle_update_config_missing")
        for final in configs:
            values = _ini(ctx.text(final)).get(tle["section"].lower(), {}).get(tle["key"].lower(), [])
            if not values or values[-1] != tle["required"]:
                r.fail(final, "tle_network_update_not_disabled")


_LIST_KEYS = ("ReadOnlyPaths", "ReadWritePaths", "IPAddressAllow", "IPAddressDeny", "DeviceAllow")
_UNIT_LIST_KEYS = ("Requires", "Requisite", "BindsTo", "Wants", "Upholds", "PartOf", "After", "Before", "RequiresMountsFor", "Conflicts")


def _unit_settings(texts, section_name="Service", list_keys=_LIST_KEYS):
    """One section's settings of a unit fragment followed by its drop-ins, in application order;
    list keys accumulate and an empty assignment resets them (systemd.unit(5))."""
    settings = {}
    for text in texts:
        section, lines, joined = None, [], ""
        for raw in text.splitlines():
            stripped = raw.strip()
            if stripped[:1] in ("#", ";"):
                continue  # also inside a continuation (systemd ignores those comment lines)
            if stripped.endswith("\\"):
                joined += stripped[:-1] + " "  # systemd: backslash-newline becomes one space
                continue
            lines.append(joined + stripped)
            joined = ""
        for line in lines + ([joined] if joined else []):
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
                continue
            key, sep, value = line.partition("=")
            if section != section_name or not sep:
                continue
            key, value = key.strip(), value.strip()
            if key in list_keys:
                settings[key] = settings.get(key, []) + value.split() if value else []
            else:
                settings[key] = value
    return settings


def _dropin_names(unit):
    """Drop-in directory names systemd searches for one unit, most specific first: the unit, its
    template for an instance, then dash-truncated prefixes (systemd src/shared/dropin.c)."""
    stem, _, suffix = unit.rpartition(".")
    names = [unit + ".d"]
    prefix, at, instance = stem.partition("@")
    if at and instance:
        names += _dropin_names(prefix + "@." + suffix)
    chopped = prefix[:-1] if prefix.endswith("-") else prefix
    dash = chopped.rfind("-")
    if dash > 0:
        names += _dropin_names(chopped[:dash + 1] + "." + suffix)
    return list(dict.fromkeys(names))


def _unit_source(ctx, rel):
    """('mask', None) for a /dev/null link or an empty file, ('file', final) or ('unresolved', None)."""
    if ctx.masked(rel):
        return "mask", None
    final = ctx.file(rel)
    if final is None:
        return "unresolved", None
    return ("mask" if ctx.entries[final].size == 0 else "file"), final


def _unit_fragment(ctx, r, dirs, name):
    """(listed, final) of the effective unit file: the first hit in precedence order of the
    instance name, then of its template; None when masked, absent or undecidable (BLOCKED)."""
    stem, _, suffix = name.rpartition(".")
    prefix, at, instance = stem.partition("@")
    for candidate in [name] + ([prefix + "@." + suffix] if at and instance else []):
        hits = [d + "/" + candidate for d in dirs if d + "/" + candidate in ctx.entries and ctx.entries[d + "/" + candidate].kind != "dir"]
        if not hits:
            continue
        kind, final = _unit_source(ctx, hits[0])
        if kind == "mask":
            r.note("masked_units_skipped")
        elif kind == "unresolved" and len(hits) > 1:
            r.block(hits[0], "unit_link_unresolvable")  # may or may not shadow the lower copy
        return (hits[0], final) if kind == "file" else None
    return None


def _unit_dropins(ctx, r, dirs, names):
    """Effective drop-in files: per filename the first directory in systemd's search order wins
    (each name over all unit paths, then service.d over all paths); applied in filename order."""
    search = [d + "/" + n for name in names for d in dirs for n in _dropin_names(name)] + [d + "/service.d" for d in dirs]
    chosen = {}
    for path in dict.fromkeys(search):
        if path not in ctx.entries:
            continue
        directory = ctx.resolve_kind(path, "dir")
        if directory is None:
            if not ctx.masked(path):
                r.block(path, "unit_link_unresolvable")
            continue
        for filename in ctx.children(directory):
            if filename.endswith(".conf") and filename not in chosen:
                chosen[filename] = _unit_source(ctx, directory + "/" + filename)
                if chosen[filename][0] == "unresolved":
                    r.block(path + "/" + filename, "unit_link_unresolvable")
    return [final for _, (kind, final) in sorted(chosen.items()) if kind == "file"]


def check_12(ctx, r):
    units = ctx.policy["units"]
    dirs = list(dict.fromkeys(d for d in (ctx.resolve_kind(p, "dir") for p in units["system_unit_paths"]) if d is not None))
    names, instances = set(), set()
    for directory in dirs:
        for name in ctx.children(directory):
            rel = directory + "/" + name
            if name.endswith(".service") and ctx.entries[rel].kind != "dir":
                names.add(name)
            elif name.endswith(".service.d"):
                instances.add(name[:-2])
            elif name.endswith((".wants", ".requires", ".upholds")):
                sub = ctx.resolve_kind(rel, "dir")
                instances.update(n for n in (ctx.children(sub) if sub else []) if n.endswith(".service"))
    # Template instances exist only by name (drop-in dirs, .wants links); each is evaluated too.
    instances = {n for n in instances if "@" in n and not n.split("@", 1)[1].startswith(".")}
    required, leases = units["lease_required"], 0
    for name in sorted(names | instances):
        fragment = _unit_fragment(ctx, r, dirs, name)
        if fragment is None:
            continue
        listed, final = fragment
        alias = posixpath.basename(final)
        aliases = [name] + ([alias] if alias != name and alias.endswith(".service") else [])
        settings = _unit_settings([ctx.text(final)] + [ctx.text(f) for f in _unit_dropins(ctx, r, dirs, aliases)])
        if settings.get("User") != units["lease_user"]:
            continue
        leases += 1
        if posixpath.basename(listed) != name:  # an instance evaluated through its template
            listed = next((d + "/" + name + ".d" for d in dirs if d + "/" + name + ".d" in ctx.entries), listed)
        for key in ("DevicePolicy", "ProtectSystem"):
            if settings.get(key) != required[key]:
                r.fail(listed, "lease_setting", key)
        if required["ReadOnlyPaths"] not in [p.lstrip("-+") for p in settings.get("ReadOnlyPaths", [])]:
            r.fail(listed, "lease_setting", "ReadOnlyPaths")
        writable = [p.lstrip("-+") for p in settings.get("ReadWritePaths", [])]
        prefix = required["ReadWritePaths"]
        if not writable or any(not p.startswith(prefix) or len(p) <= len(prefix) or "/.." in p or "/./" in p for p in writable):
            r.fail(listed, "lease_setting", "ReadWritePaths")
        if set(settings.get("IPAddressAllow", [])) != {required["IPAddressAllow"]}:
            r.fail(listed, "lease_setting", "IPAddressAllow")
        # IPAddressAllow= alone restricts nothing in systemd: localhost-only needs IPAddressDeny=any too.
        if required["IPAddressDeny"] not in settings.get("IPAddressDeny", []):
            r.fail(listed, "lease_setting", "IPAddressDeny")
    if not leases:
        if ctx.profile == "controller":
            r.note("no_lease_units_in_controller_profile")
        else:
            r.block(".", "lease_units_not_found")
    r.note("EPERM_EROFS_behaviour_is_RX-12-runtime")


def _synthetic_frame(center, rate, size=64):
    width = rate / size
    return {"v": 1, "kind": "spectrum", "center_hz": center, "sample_rate_hz": rate, "fft_size": size,
            "power_dbfs": [-50.0 - (i % 7) for i in range(size)], "valid": [True] * size,
            "relative_frequency_hz": [(i - size // 2) * width for i in range(size)], "source": "SIMULATION", "sample_count": size}


def check_13(ctx, r):
    spectrum, learning = _target_module(ctx, r, "spectrum"), _target_module(ctx, r, "learning")
    if spectrum is None or learning is None:
        return
    group = uuid.UUID(int=0x5352)
    # 406.05 MHz at 50 kS/s: all 64 bins lie inside the Cospas-Sarsat 406.0-406.1 MHz uplink (STACK.md:626).
    for label, center, rate in (("20kHz", 20_000.0, 16_000.0), ("300MHz", 300e6, 2.4e6), ("406.05MHz", 406.05e6, 50e3),
                                ("1544.5MHz", 1544.5e6, 2.4e6)):
        masked = spectrum.mask_frame(_synthetic_frame(center, rate))
        if any(masked["valid"]) or any(p is not None for p in masked["power_dbfs"]):
            r.fail("software/srrx/spectrum.py", "mask_bin_valid", label)
        try:
            learning.annotate(learning.empty_dataset(), _synthetic_frame(center, rate), 8, 24, "unknown_energy", group_id=group, user_confirmed=True)
            r.fail("software/srrx/learning.py", "annotate_accepted_masked_bins", label)
        except learning.LearningError:
            pass
    control = spectrum.mask_frame(_synthetic_frame(137.5e6, 1e6))
    try:  # an over-broad mask would make the refusals above meaningless
        if not all(control["valid"]):
            raise ValueError
        learning.annotate(learning.empty_dataset(), _synthetic_frame(137.5e6, 1e6), 8, 24, "unknown_energy", group_id=group, user_confirmed=True)
    except ValueError:
        r.block("software/srrx/spectrum.py", "mask_control_frame_rejected")
    r.note("npu_path_is_RX-13-npu")


def _manifest_labels(data, policy):
    """Labels of a dataset/model manifest, or None when the JSON is not one."""
    if type(data) is not dict:
        return None
    labels, manifest = [], False
    if data.get("kind") in policy["dataset_manifest_kinds"]:
        manifest = True
        for record in data.get("annotations", []) if type(data.get("annotations", [])) is list else [None]:
            if type(record) is not dict or type(record.get("label")) is not str:
                raise ValueError("manifest schema")
            labels.append(record["label"])
    for key in policy["dataset_label_keys"]:
        if key in data:
            manifest, value = True, data[key]
            items = list(value) if isinstance(value, dict) else value
            if type(items) is not list:
                raise ValueError("manifest schema")
            for item in items:
                item = item.get("name") if isinstance(item, dict) else item
                if type(item) is not str:
                    raise ValueError("manifest schema")
                labels.append(item)
    return labels if manifest else None


def _check_labels(r, where, labels, allowed, deny):
    """Labels are target text (they could name a person or a device): only the policy deny token
    is reported, a non-allowlisted label is reported without any identifier."""
    for label in labels:
        low = label.lower()
        if allowed is not None and label not in allowed:
            r.fail(where, "label_not_allowlisted")
        for token in deny:
            if token in low or token in low.replace("_", "-"):
                r.fail(where, "dataset_deny_token", token)


def check_15(ctx, r):
    policy = ctx.policy
    learning = _target_module(ctx, r, "learning")
    allowed = set(learning.LABELS) if learning is not None else None
    deny = [t.lower() for t in policy["dataset_deny_tokens"]]
    markers = ['"' + k + '"' for k in policy["dataset_label_keys"]] + policy["dataset_manifest_kinds"]
    for root in policy["dataset_roots"]:
        for listed, final in ctx.files_in([root]):
            if not listed.lower().endswith(".json") or not ctx.contains(final, markers):
                continue
            if ctx.entries[final].size >= MAX_TEXT:
                r.block(listed, "manifest_candidate_too_large")
                continue
            try:
                labels = _manifest_labels(ctx.json(final), policy)
            except ValueError:
                r.block(listed, "manifest_schema")
                continue
            _check_labels(r, listed, labels or [], allowed, deny)
    project = Path(ctx.project)
    for root in policy["project_dataset_roots"]:
        for directory, dirs, files in os.walk(project / root):
            dirs[:] = sorted(d for d in dirs if d not in ("tests", "upstream-fixtures", "__pycache__"))
            for name in sorted(files):
                path = Path(directory) / name
                where = "project:" + path.relative_to(project).as_posix()
                if not name.lower().endswith(".json") or path.is_symlink():
                    continue
                with _open_regular(path) as handle:
                    if not _stream_contains(handle, markers):
                        continue
                try:
                    labels = _manifest_labels(deploy.load(path), policy)
                except (ValueError, UnicodeError):
                    r.block(where, "manifest_schema")
                    continue
                _check_labels(r, where, labels or [], allowed, deny)


def _pref_stanzas(text):
    stanzas = []
    for block in re.split(r"\n[ \t\r]*\n", text):
        fields = {}
        for line in block.splitlines():
            if not line.strip() or line.lstrip().startswith("#") or line[0] in " \t":
                continue
            key, sep, value = line.partition(":")
            if sep:
                fields[key.strip().lower()] = value.strip()
        if fields:
            stanzas.append(fields)
    return stanzas


_APT_PART = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")


def _other_preferences(ctx, r, lab_pref):
    """etc/apt/preferences and every preferences.d part apt reads (no extension or .pref, apt's
    filename characters): outside lab.pref a stanza may only lower a priority (<= 0)."""
    apt_dir, parts = ctx.resolve_kind("etc/apt", "dir"), ctx.resolve_kind("etc/apt/preferences.d", "dir")
    candidates = [("etc/apt/preferences", apt_dir + "/preferences")] if apt_dir is not None else []
    for name in ctx.children(parts) if parts is not None else []:
        if _APT_PART.fullmatch(name) and ("." not in name or name.endswith(".pref")):
            candidates.append(("etc/apt/preferences.d/" + name, parts + "/" + name))
        else:
            r.note("apt_ignored_preference_parts")  # apt itself skips these names
    lab = ctx.file(lab_pref)
    for rel, key in candidates:
        entry = ctx.entries.get(key)
        if entry is None or entry.kind == "dir":
            continue
        final = ctx.file(key)
        if final is None:
            if not ctx.masked(key):
                r.block(rel, "apt_preferences_unresolvable")
            continue
        if final == lab:
            continue  # lab.pref itself: structure checked above
        for stanza in _pref_stanzas(ctx.text(final)):
            try:
                priority = int(stanza.get("pin-priority", ""))
            except ValueError:
                r.block(rel, "apt_preferences_unparsable")
                continue
            if priority > 0:
                r.fail(rel, "apt_pin_positive_outside_lab_pref")


def check_16(ctx, r):
    policy, apt = ctx.policy, ctx.policy["apt"]
    origins = [o.lower() for o in policy["apt_forbidden_origins"]]
    for rel in ctx.globs(apt["sources_globs"]):
        final = ctx.file(rel)
        if final is None:
            continue
        if any(t in rel.rsplit("/", 1)[-1].lower() for t in apt["forbidden_list_name_tokens"]):
            r.fail(rel, "rsdk_ppa_list_present")
        for line in ctx.text(final).splitlines():
            line = line.strip().lower()
            if line and not line.startswith("#") and any(o in line for o in origins):
                r.fail(rel, "apt_forbidden_origin")
                break
    configured = ctx.resolve_kind("etc/apt", "dir") is not None
    if configured or ctx.profile == "full":
        final = ctx.file(apt["pref_path"])
        if not configured:
            r.block("etc/apt", "apt_configuration_missing")
        elif final is None:
            r.fail(apt["pref_path"], "lab_pref_missing")
        else:
            stanzas = _pref_stanzas(ctx.text(final))
            try:
                wildcard = [(s.get("pin", ""), int(s.get("pin-priority", ""))) for s in stanzas if s.get("package") == "*"]
                extra = [int(s.get("pin-priority", "")) for s in stanzas if s.get("package") != "*"]
            except ValueError:
                wildcard, extra = None, []
            if wildcard is None or [p for _, p in wildcard] != apt["pref_priorities"] or wildcard[-1][0] not in ("origin *", "release *"):
                r.fail(apt["pref_path"], "lab_pref_structure")
            elif any("<" in pin for pin, _ in wildcard):
                r.block(apt["pref_path"], "apt_pin_origin_placeholder")
            if any(p > 0 for p in extra):
                r.fail(apt["pref_path"], "apt_pin_positive_extra")
        if configured:
            _other_preferences(ctx, r, apt["pref_path"])
    else:
        r.note("apt_configuration_absent_controller_overlay")
    status, present = ctx.dpkg()
    info = "var/lib/dpkg/info"
    for package in policy["dpkg_verify_packages"]:
        sums = ctx.globs([info + "/" + package + ".md5sums", info + "/" + package + ":*.md5sums"])
        if not sums:
            if status is not None and package in present:
                r.block(info, "dpkg_md5sums_missing", package)
            elif ctx.profile == "full":
                r.block(info, "firmware_package_unverified", package)
            else:
                r.note("firmware_packages_not_in_controller_overlay")
            continue
        for rel in sums:
            final = ctx.file(rel)
            if final is None:
                r.block(rel, "dpkg_md5sums_unreadable", package)
                continue
            for line in ctx.text(final).splitlines():
                if not line.strip():
                    continue
                match = re.fullmatch(r"([0-9a-fA-F]{32}) +(\S.*)", line.rstrip("\r"))
                if match is None:
                    r.block(rel, "dpkg_md5sums_malformed", package)
                    break
                target = match.group(2).lstrip("/")
                if ".." in target.split("/"):
                    r.block(rel, "dpkg_verify_unsafe_path", package)
                    continue
                listed = ctx.file(target)
                if listed is None:  # the md5sums text is never echoed: report the md5sums file
                    r.fail(rel, "dpkg_verify_missing_file", package)
                elif ctx.digest(listed, "md5") != match.group(1).lower():
                    r.fail(listed, "dpkg_verify_mismatch", package)
    r.note("apt_simulation_is_RX-16-sim")


def check_17(ctx, r):
    path = ctx.policy["kernel_cmdline_path"]
    if ctx.cmdline_sha256 is None:
        return r.block(path, "reviewed_cmdline_sha256_missing")
    final = ctx.file(path)
    if final is None:
        return r.block(path, "kernel_cmdline_missing")
    if ctx.digest(final) != ctx.cmdline_sha256:
        r.fail(path, "kernel_cmdline_mismatch")
    if "clk_ignore_unused" in ctx.text(final, 64 * 1024).split():
        r.fail(path, "clk_ignore_unused")
    r.note("proc_cmdline_is_RX-17-proc")


def check_s1(ctx, r):
    module = _target_module(ctx, r, "decoder_policy")
    if module is None:
        return
    available = module.availability()  # offline: no installation record, so nothing may read as accepted
    for preset in ctx.policy["decoder_gated_presets"]:
        value = available.get(preset)
        if type(value) is not str or not value.startswith(("DISABLED", "UNAVAILABLE")):
            r.fail("software/srrx/decoder_policy.py", "gated_preset_enabled", preset)


# STACK.md:977 and build/12-revision-v2.1.md:71 (owner decision 24.10.2026), reviewed values.
_BASEBAND_POLICY = {"INPUT_RATE_HZ": 1_024_000, "DECIMATION": 4, "OUTPUT_RATE_HZ": 256_000, "CI16_SCALE": 32767,
                    "CLASS_CAP_BYTES": 3 * 512 * 1024 * 1024, "RAW_QUOTA_BYTES": 30 * 1024 ** 3, "RESERVE_FACTOR": 1.1,
                    "RETENTION_S": 86400, "MAX_FILE_S": 1200, "MARGIN_S": 60.0, "GUARD_HZ": 20_000.0,
                    "LIVE_HOST": "127.0.0.1", "LIVE_MAX_SAMPLES": 8188, "STOPBAND_DB": -100.0,
                    "METEOR_TARGETS": ("Meteor-M N2-3", "Meteor-M N2-4"),
                    "CENTERS_HZ": (137_100_000, 137_900_000, 137_912_500)}
_LIVE_FORBIDDEN_ARGS = ("--http_server", "--client", "--server_address", "--server_port", "--multi_vfo", "--fft_enable",
                        "--source_id")


def check_04bb(ctx, r):
    """srrx.baseband and srrx.satdump_pass as staged: the v2.1 constants, the channel filter of every
    allowed tuning (stopband <= -100 dB beyond the window), a synthetic out-of-window tone that is stored
    as zeros, and the fixed SatDump unit properties and argv. Recorder runs on the device are RX-04-live."""
    bb, glue = _target_module(ctx, r, "baseband"), _target_module(ctx, r, "satdump_pass")
    if bb is None or glue is None:
        return
    try:
        import numpy as np
    except ImportError:
        return r.block(".", "numpy_unavailable")
    where, units = "software/srrx/baseband.py", "software/srrx/satdump_pass.py"
    for name, value in _BASEBAND_POLICY.items():
        if getattr(bb, name, None) != value:
            r.fail(where, "baseband_policy_constant", name)
    if bb.LIVE_MAX_SAMPLES * 8 > 65507 or set(bb.PIPELINES.values()) != {"meteor_m2-x_lrpt", "meteor_m2-x_lrpt_80k"}:
        r.fail(where, "baseband_policy_constant", "LIVE_OR_PIPELINES")
    for center in bb.CENTERS_HZ:
        for rate in sorted(bb.PIPELINES):
            try:
                low, high = bb.channel_span(center, rate)
                bb.verify_taps(bb.design_taps(center, rate), center, rate)
                if not 137e6 < low < high < 138e6:
                    raise bb.BasebandRefused("span")
            except bb.BasebandRefused:
                r.fail(where, "channel_filter_spec", "%d/%d" % (center, rate))
    window = bb.window(1, "Meteor-M N2-3", 137_900_000, 72_000, 1e9, 1e9 + 600, bb.iso_utc(1e9), bb.iso_utc(1e9 + 600))
    t = np.arange(bb.INPUT_RATE_HZ // 4) / bb.INPUT_RATE_HZ
    for offset, inside in ((150_000.0, False), (-110_000.0, False), (20_000.0, True)):
        chain = bb.ChannelChain(window)
        tone = (0.99 * np.exp(2j * np.pi * offset * t)).astype(np.complex64)
        stored = np.concatenate([chain.push(tone[k:k + 8192]) for k in range(0, tone.size, 8192)] + [chain.flush()])
        if not inside and np.count_nonzero(stored):
            r.fail(where, "out_of_window_tone_stored", "%+d kHz" % (offset / 1e3))
        if inside and abs(np.sqrt(np.mean(stored.astype(np.float64) ** 2 * 2)) / bb.CI16_SCALE - 0.99) > 0.01:
            r.fail(where, "in_window_tone_not_kept", "%+d kHz" % (offset / 1e3))
    ident = "0" * 16
    decode = glue.unit_properties("decode", ident, work_dir="/data/products/satdump/.satdump-" + ident,
                                  input_path="/data/raw/baseband-lrpt/lrpt-" + ident + ".sigmf-data")
    live = glue.unit_properties("live", ident, work_dir="/data/products/satdump/.satdump-" + ident)
    common = {"ProtectHome=yes", "ProtectSystem=strict", "NoNewPrivileges=yes", "Environment=LC_ALL=C.UTF-8",
              "WorkingDirectory=" + glue.EMPTY_WORKDIR, "TemporaryFileSystem=/data:ro", "IPAddressDeny=any",
              "User=" + glue.UNIT_USER}
    if not common | {"PrivateNetwork=yes", "RestrictAddressFamilies=AF_UNIX"} <= set(decode) or any(
            p.startswith("IPAddressAllow=") for p in decode):
        r.fail(units, "decode_unit_properties")
    if not common | {"IPAddressAllow=localhost"} <= set(live) or "PrivateNetwork=yes" in live:
        r.fail(units, "live_unit_properties")
    argv = glue.decode_argv("/usr/bin/satdump", "meteor_m2-x_lrpt", "/data/raw/baseband-lrpt/x", "/data/products/x")
    if argv[1:4] != ["pipeline", "meteor_m2-x_lrpt", "baseband"] or argv[-2:] != ["--samplerate=256000", "--baseband_format=cs16"]:
        r.fail(units, "decode_argv")
    command = glue.live_argv("/usr/bin/satdump", window, "/data/products/x", 8877)
    if command[1:3] != ["legacy", "live"] or command[command.index("--source") + 1] != "net_source" or any(
            a in command for a in _LIVE_FORBIDDEN_ARGS):
        r.fail(units, "live_argv")
    staged = ctx.file("etc/tmpfiles.d/srrx-satdump.conf")
    if staged is None:
        r.note("baseband_tmpfiles_not_staged")
    elif ctx.read(staged, 64 * 1024).decode("utf-8", "replace") != glue.tmpfiles():
        r.fail("etc/tmpfiles.d/srrx-satdump.conf", "baseband_tmpfiles_differs")
    r.note("live_localhost_behaviour_is_RX-04-live")
    r.note("device_recording_needs_labd_utc_verified")


# kmod and udev read these persistent directories in this precedence order (/run is runtime state).
_MODPROBE_DIRS = ("etc/modprobe.d", "usr/local/lib/modprobe.d", "usr/lib/modprobe.d", "lib/modprobe.d")
_UDEV_DIRS = ("etc/udev/rules.d", "usr/local/lib/udev/rules.d", "usr/lib/udev/rules.d", "lib/udev/rules.d")
_AUTHORIZE = re.compile(r'ATTR\{authorized(?:_default)?\}\s*[+:]?=(?!=)\s*"([^"]*)"')
# Drop-in keys that cannot defeat the rfkill oneshot (descriptions, logging, resource and network limits).
_RADIO_OFF_NEUTRAL_KEYS = frozenset(("Description", "Documentation", "IPAddressAllow", "IPAddressDeny", "MemoryMax", "MemoryHigh",
                                     "TasksMax", "CPUQuota", "CPUWeight", "IOWeight", "Nice", "LogLevelMax", "LogRateLimitIntervalSec"))


def _effective_parts(ctx, r, directories, suffix, own):
    """(listed, final) of each config part that could override a staged layer: per basename the
    first directory wins, and the staged file itself (own, compared byte for byte) is skipped."""
    seen, parts = {posixpath.basename(own)}, []
    for directory in directories:
        resolved = ctx.resolve_kind(directory, "dir")
        for name in sorted(ctx.children(resolved)) if resolved is not None else []:
            if name.endswith(suffix) and name not in seen:
                seen.add(name)
                final = ctx.file(resolved + "/" + name)
                if final is not None:
                    parts.append((directory + "/" + name, final))
                elif not ctx.masked(resolved + "/" + name):
                    r.block(directory + "/" + name, "radio_off_config_unresolvable")
    return parts


def _staged_copy(ctx, r, rel, expected, layer):
    final = ctx.file(rel)
    if final is None:
        r.fail(rel, "radio_off_" + layer + "_missing")
    elif ctx.text(final).strip() != expected.strip():
        r.fail(rel, "radio_off_" + layer + "_modified")


def check_s2(ctx, r):
    """Field/QUIET radio-off layers exactly as deploy.stage writes them (STACK.md:726); whether
    they took effect on the running Q6A is RX-S2-runtime. Weakening any layer is a FAIL."""
    _staged_copy(ctx, r, deploy.RADIO_OFF_MODPROBE, deploy.radio_off_modprobe(), "modprobe")
    modules = {m.replace("-", "_") for m in deploy.AIC8800_MODULES}
    # kmod runs the first install command whose module pattern matches: another one could load the driver.
    for listed, final in _effective_parts(ctx, r, _MODPROBE_DIRS, ".conf", deploy.RADIO_OFF_MODPROBE):
        for line in ctx.text(final).splitlines():
            words = line.split("#", 1)[0].split()
            if len(words) >= 2 and words[0] == "install" and any(fnmatch.fnmatchcase(m, words[1].replace("-", "_")) for m in modules):
                r.fail(listed, "radio_off_modprobe_override")
    devices = ctx.file("etc/srrx/devices.json")
    if devices is None:
        r.block("etc/srrx/devices.json", "radio_off_binding_missing")  # port-4 path unknown: never PASS
    else:
        try:
            rule = deploy.radio_off_udev(ctx.json(devices))
        except Blocked as exc:  # FAIL dominates BLOCKED: the other layers are still evaluated
            r.block(exc.path, exc.rule)
        except (ValueError, KeyError, TypeError):
            r.block("etc/srrx/devices.json", "radio_off_binding_invalid")
        else:
            _staged_copy(ctx, r, deploy.RADIO_OFF_UDEV, rule, "udev")
    for listed, final in _effective_parts(ctx, r, _UDEV_DIRS, ".rules", deploy.RADIO_OFF_UDEV):
        if any(value != "0" for value in _AUTHORIZE.findall(ctx.text(final))):
            r.fail(listed, "radio_off_udev_reauthorize")
    units = ctx.policy["units"]
    dirs = list(dict.fromkeys(d for d in (ctx.resolve_kind(p, "dir") for p in units["system_unit_paths"]) if d is not None))
    fragment = _unit_fragment(ctx, r, dirs, deploy.RADIO_OFF_UNIT)
    if fragment is None:
        r.fail("etc/systemd/system/" + deploy.RADIO_OFF_UNIT, "radio_off_unit_missing")
    else:
        if ctx.text(fragment[1]).strip() != deploy.radio_off_unit().strip():
            r.fail(fragment[0], "radio_off_unit_modified")
        # Stage writes no drop-in for it. One (also a generic service.d) may change only neutral keys:
        # ExecStart=, Type=, SuccessExitStatus=, Condition*= and the like could defeat the oneshot.
        base = [ctx.text(fragment[1])]
        texts = base + [ctx.text(f) for f in _unit_dropins(ctx, r, dirs, [deploy.RADIO_OFF_UNIT])]
        for section, lists in (("Unit", _UNIT_LIST_KEYS), ("Service", _LIST_KEYS)):
            before, after = _unit_settings(base, section, lists), _unit_settings(texts, section, lists)
            if {k for k in set(before) | set(after) if before.get(k) != after.get(k)} - _RADIO_OFF_NEUTRAL_KEYS:
                r.fail(fragment[0], "radio_off_unit_dropin")
    for name, required in (("srrx.service", True), ("srrx-poweroff.service", False)):
        unit = _unit_fragment(ctx, r, dirs, name)
        if unit is None:
            if required:
                r.block(".", "srrx_service_not_found")
            continue
        settings = _unit_settings([ctx.text(unit[1])] + [ctx.text(f) for f in _unit_dropins(ctx, r, dirs, [name])], "Unit", _UNIT_LIST_KEYS)
        if required and not all(deploy.RADIO_OFF_UNIT in settings.get(key, []) for key in ("Requires", "After")):
            r.fail(unit[0], "radio_off_not_required")
        if not required and any(deploy.RADIO_OFF_UNIT in settings.get(key, []) for key in ("Requires", "Requisite", "BindsTo")):
            r.fail(unit[0], "radio_off_hard_dependency_of_bridge")  # a failed oneshot would fail the shutdown bridge
    _target_identical(ctx, r, "rfkill")  # the unit runs the target's srrx.rfkill
    r.note("live_rfkill_and_usb_state_is_RX-S2-runtime")


# systemd --user unit search order of the image's persistent directories (systemd.unit(5) "User Unit
# Search Path", XDG defaults): $XDG_CONFIG_DIRS, /etc, $XDG_DATA_DIRS, then the package paths. /run and
# $XDG_RUNTIME_DIR are runtime state. The per-user directories rank higher (~/.config/systemd/user.control,
# ~/.config/systemd/user) or between /etc and $XDG_DATA_DIRS (~/.local/share/systemd/user); which home
# the console session uses is not decidable offline, so a unit, mask or drop-in there is BLOCKED.
_USER_UNIT_DIRS = ("etc/xdg/systemd/user", "etc/systemd/user", "usr/local/share/systemd/user", "usr/share/systemd/user",
                   "usr/local/lib/systemd/user", "usr/lib/systemd/user")
_USER_HOME_UNIT_DIRS = (".config/systemd/user.control", ".config/systemd/user", ".local/share/systemd/user")
_USER_HOMES = ("root", "home/*", "etc/skel")  # etc/skel: copied into every new home
# ExecStart= prefixes (systemd.service(5)) and systemd's fixed search path for a bare executable name.
_EXEC_PREFIXES = "-@:+!|"
_EXEC_SEARCH = ("usr/local/sbin", "usr/local/bin", "usr/sbin", "usr/bin")
_PRESET_ACCEPTED = "FILE_PRESET_ACCEPTED"  # decoder_policy.availability() with an accepted installation


def _checker_tree(name):
    return ast.parse((deploy.PROJECT / "software/srrx" / (name + ".py")).read_text(encoding="utf-8"))


def _labd_operations():
    """Operations srrx.engine.Engine.request dispatches: string constants an `if op == ...` or
    `if op in {...}` test compares with op (the ownership pre-check is a BoolOp and is skipped)."""
    operations = set()
    for cls in _checker_tree("engine").body:
        if not (isinstance(cls, ast.ClassDef) and cls.name == "Engine"):
            continue
        for method in cls.body:
            if not (isinstance(method, ast.FunctionDef) and method.name == "request"):
                continue
            for node in ast.walk(method):
                test = node.test if isinstance(node, ast.If) else None
                if (isinstance(test, ast.Compare) and isinstance(test.left, ast.Name) and test.left.id == "op"
                        and len(test.ops) == 1 and isinstance(test.ops[0], (ast.Eq, ast.In))):
                    value = test.comparators[0]
                    items = value.elts if isinstance(value, (ast.Set, ast.Tuple, ast.List)) else [value]
                    operations.update(i.value for i in items if isinstance(i, ast.Constant) and isinstance(i.value, str))
    return operations


def _home_unit_overrides(ctx, r, name):
    """BLOCKED for each per-user copy, mask or drop-in directory of a user unit (_USER_HOMES)."""
    names = {name, *_dropin_names(name), name.rpartition(".")[2] + ".d"}
    for home in ctx.globs(_USER_HOMES):
        for sub in _USER_HOME_UNIT_DIRS:
            directory = ctx.resolve_kind(home + "/" + sub, "dir")
            for child in sorted(names & set(ctx.children(directory))) if directory is not None else ():
                r.block(home + "/" + sub + "/" + child, "user_unit_in_home_directory")


def _exec_chain(words):
    """Executables an ExecStart command line starts: its first word, and for env(1) also the command
    after env's NAME=value assignments (None when an env option makes it undecidable)."""
    if not words:
        return []
    chain = [words[0].lstrip(_EXEC_PREFIXES)]
    if posixpath.basename(chain[0]) == "env":
        rest = words[1:]
        while rest and "=" in rest[0] and not rest[0].startswith(("-", "/")):
            rest = rest[1:]
        chain.append(rest[0] if rest and not rest[0].startswith("-") else None)
    return chain


def _exec_file(ctx, word):
    """Rootfs file an executable word names: an absolute path, or a bare name on systemd's search path."""
    if word is None or not word.startswith("/") and "/" in word:
        return None
    if word.startswith("/"):
        return ctx.file(word.lstrip("/"))
    return next((f for f in (ctx.file(d + "/" + word) for d in _EXEC_SEARCH) if f is not None), None)


def _unit_backend(ctx, r, backend, item):
    """A unit of the backend's scope is effective in the rootfs and its ExecStart runs the declared
    program: `-m srrx.<module>` with that module staged, or an absolute binary present in the rootfs.
    The executables ExecStart starts (the interpreter, also behind /usr/bin/env) must be files of the
    rootfs; a controller overlay without a dpkg database lacks the base image and the venv, so a
    missing one is a note there and BLOCKED otherwise. Enablement is an install step, not checked."""
    where = "software/srrx/menu_model.py"
    paths = ctx.policy["units"]["system_unit_paths"] if backend["scope"] == "system" else _USER_UNIT_DIRS
    if backend["scope"] == "user":
        _home_unit_overrides(ctx, r, backend["name"])
    dirs = list(dict.fromkeys(d for d in (ctx.resolve_kind(p, "dir") for p in paths) if d is not None))
    fragment = _unit_fragment(ctx, r, dirs, backend["name"])
    if fragment is None:
        return r.fail(where, "backend_unit_missing", item)
    texts = [ctx.text(fragment[1])] + [ctx.text(f) for f in _unit_dropins(ctx, r, dirs, [backend["name"]])]
    words, program = _unit_settings(texts).get("ExecStart", "").split(), backend["program"]
    if program.startswith("srrx."):
        runs = any(words[i:i + 2] == ["-m", program] for i in range(len(words)))
        present = ctx.file(ctx.policy["srrx_root"] + "/software/srrx/" + program[5:] + ".py") is not None
    else:
        runs = program in [w.lstrip(_EXEC_PREFIXES) for w in words[:2]]
        present = ctx.file(program.lstrip("/")) is not None
    if not (runs and present):
        return r.fail(fragment[0], "backend_program_missing", item)
    if any(_exec_file(ctx, word) is None for word in _exec_chain(words)):
        if ctx.profile == "controller" and ctx.file("var/lib/dpkg/status") is None:
            r.note("unit_interpreter_absent_controller_overlay")
        else:
            r.block(fragment[0], "unit_interpreter_missing", item)


def check_11(ctx, r):
    """srrx.menu_model against the staged rootfs (build/07 row 11, STACK.md:884): every leaf reaches
    its backend, a Lime/T7 leaf declares its no-Lime/no-T7 backend, a critical leaf has a key or
    encoder (STACK.md:110). The target console (hmi and its imports) must be the evaluated code.
    The model describes only the srrx.hmi touch console: the Lab Shell menu of STACK.md:884 (hubs,
    Lime capability check) has no code yet and stays outside this row (note, Д-06)."""
    menu = _target_module(ctx, r, "menu_model")
    hmi = _target_module(ctx, r, "hmi") if menu is not None else None  # importing srrx.hmi loads no Qt
    if hmi is None:
        return
    where, console = "software/srrx/menu_model.py", "software/srrx/hmi.py"
    try:
        menu.validate()
    except ValueError:
        return r.fail(where, "menu_model_invalid")
    if tuple(hmi.HMINavigation.NAMES) != menu.GESTURES:
        r.fail(console, "physical_controls_drift")
    builders = {n.name for n in ast.walk(_checker_tree("hmi")) if isinstance(n, ast.FunctionDef)}
    for page in menu.PAGES:
        if "_" + page["id"] + "_page" not in builders:
            r.fail(console, "page_builder_missing", page["id"])
    _unit_backend(ctx, r, menu.CONSOLE_UNIT, "console")
    _unit_backend(ctx, r, menu.LABD_UNIT, "labd")
    operations = _labd_operations() if _target_identical(ctx, r, "daemon") else None
    presets, imported = None, set(srrx_closure("hmi"))
    for leaf in menu.LEAVES:
        backend, item = leaf["backend"], leaf["id"]
        if backend["kind"] == "labd_op":
            if operations is not None and backend["name"] not in operations:
                r.fail(where, "backend_missing", item)
        elif backend["kind"] == "engine_unit":
            _unit_backend(ctx, r, backend, item)
        elif backend["kind"] == "decoder_preset":
            if presets is None:
                module = _target_module(ctx, r, "decoder_policy")
                presets = module.availability() if module is not None else False  # False: BLOCKED above
            if presets is not False and backend["name"] not in presets:
                r.fail(where, "backend_missing", item)
            elif presets and not str(presets[backend["name"]]).startswith(_PRESET_ACCEPTED) and not leaf["fallback_text"]:
                # DISABLED_* and UNAVAILABLE_* alike: offline there is no accepted installation either.
                r.fail(where, "unavailable_preset_without_fallback", item)
        elif ctx.file(ctx.policy["srrx_root"] + "/software/srrx/" + backend["name"] + ".py") is None:
            r.fail(where, "backend_missing", item)  # page_only: the srrx module doing the work
        elif backend["name"] not in imported:
            _target_identical(ctx, r, backend["name"])  # run apart from the console (labrx --simulate)
        if leaf["needs_lime"] and not leaf["fallback_text"]:
            r.fail(where, "no_lime_backend_undeclared", item)
        if leaf["needs_t7"] and not leaf["fallback_text"]:
            r.fail(where, "no_t7_backend_undeclared", item)
        if leaf["critical"] and not leaf["controls"]["keys"]:
            r.block(where, "critical_leaf_touch_only", item)  # no glove path yet: an open design item
    r.note("fallback_text_is_declared_not_rendered")
    r.note("glove_and_physical_key_operation_is_hardware_acceptance")
    r.note("unit_enablement_is_an_install_step")
    r.note("lab_shell_menu_not_modelled")


# RX-14 probes (build/07 row 14, ПОЛ-05): label, centre, rate, NFM voices, active windows, bench
# capture, control carriers. A window over 446.006 MHz must not re-open PMR446; the windows over
# 145.800, 437.800 and 436.795 MHz must not lift the static masks; 145.86, 435.2 and 137.6 MHz
# carriers must survive (an over-broad mask would make the voice probes meaningless).
_VOICE_PROBES = (
    ("145.500MHz", 145.65e6, 500e3, (145.500e6, 145.800e6), ((145.85e6, 145.87e6), (145.79e6, 145.81e6)), True, (145.86e6,)),
    ("433.500MHz", 434.3e6, 2.048e6, (433.500e6,), ((435.17e6, 435.23e6),), True, (435.2e6,)),
    ("446.006MHz", 446.05e6, 500e3, (446.00625e6,), ((445.99e6, 446.02e6),), False, ()),
    ("437.800MHz", 437.3e6, 1.2e6, (437.800e6, 436.795e6), ((437.79e6, 437.81e6), (436.785e6, 436.805e6)), True, ()),
    ("137.500MHz", 137.5e6, 500e3, (), (), True, (137.6e6,)),
)
_VOICE_SAMPLES, _VOICE_MARGIN_DB, _CONTROL_LOSS_DB = 1 << 16, 3.0, 1.0


def _voice_capture(np, centre, rate, voices, carriers, seed):
    """Pinned synthetic capture (seeded PCG64): complex noise, NFM voices (400/1100/2300 Hz tones,
    2.5 kHz peak deviation) and unmodulated control carriers. Returns (capture, noise)."""
    rng = np.random.default_rng(seed)
    t = np.arange(_VOICE_SAMPLES) / rate
    noise = (rng.standard_normal(t.size) + 1j * rng.standard_normal(t.size)) * (1e-3 / np.sqrt(2))
    audio = .6 * np.sin(2 * np.pi * 400 * t) + .3 * np.sin(2 * np.pi * 1100 * t + 1) + .1 * np.sin(2 * np.pi * 2300 * t + 2)
    deviation = 2 * np.pi * 2500 * np.cumsum(audio) / rate
    signal = np.zeros(t.size, np.complex128)
    for frequency in voices:
        signal += .1 * np.exp(1j * (2 * np.pi * (frequency - centre) * t + deviation))
    for frequency in carriers:
        signal += .01 * np.exp(2j * np.pi * (frequency - centre) * t)
    return (noise + signal).astype(np.complex64), noise


def _band_power(np, samples, centre, rate, frequency, half):
    """Mean Welch power (periodic Hann, 4096 bins, 50 % overlap) of the bins within frequency +- half."""
    size, window, total, count = 4096, np.hanning(4096), np.zeros(4096), 0
    for start in range(0, samples.size - size + 1, size // 2):
        total += np.abs(np.fft.fftshift(np.fft.fft(samples[start:start + size] * window))) ** 2
        count += 1
    bins = np.abs(centre + (np.arange(size) - size // 2) * rate / size - frequency) <= half
    return float(total[bins].mean() / count)


def check_14(ctx, r):
    """srrx.voice_mask.excise on pinned captures: the NFM residual of each voice stays within the
    noise floor + 3 dB, each control carrier keeps its power within 1 dB (STACK.md:977)."""
    mask = _target_module(ctx, r, "voice_mask")
    if mask is None:
        return
    try:
        import numpy as np
    except ImportError:
        return r.block(".", "numpy_unavailable")
    where = "software/srrx/voice_mask.py"
    for seed, (label, centre, rate, voices, windows, bench, carriers) in enumerate(_VOICE_PROBES, 1):
        capture, noise = _voice_capture(np, centre, rate, voices, carriers, seed)
        try:
            out = np.asarray(mask.excise(capture, centre, rate, windows, bench=bench))
        except ValueError:
            r.fail(where, "voice_mask_refused_capture", label)
            continue
        if out.shape != capture.shape or not np.all(np.isfinite(out)):
            r.fail(where, "voice_mask_output_invalid", label)
            continue
        for frequency in voices:
            floor = _band_power(np, noise, centre, rate, frequency, 6e3)
            if _band_power(np, out, centre, rate, frequency, 6e3) > floor * 10 ** (_VOICE_MARGIN_DB / 10):
                r.fail(where, "voice_residual_above_noise", "%.3fMHz" % (frequency / 1e6))
        for frequency in carriers:
            before = _band_power(np, capture, centre, rate, frequency, 1e3)
            if _band_power(np, out, centre, rate, frequency, 1e3) < before * 10 ** (-_CONTROL_LOSS_DB / 10):
                r.block(where, "voice_mask_control_removed", label)
    r.note("recorder_excises_through_srrx.baseband_RX-04-bb")
    r.note("repeater_pass_recording_is_device_evidence")


CHECKS = {"RX-00": check_00, "RX-01a": check_01a, "RX-01b": check_01b, "RX-01c": check_01c, "RX-02": check_02, "RX-03": check_03,
          "RX-04": check_04, "RX-04-bb": check_04bb, "RX-05": check_05, "RX-06": check_06, "RX-07": check_07, "RX-08": check_08, "RX-09": check_09,
          "RX-10": check_10, "RX-11": check_11, "RX-12": check_12, "RX-13": check_13, "RX-14": check_14, "RX-15": check_15,
          "RX-16": check_16, "RX-17": check_17, "RX-S1": check_s1, "RX-S2": check_s2}


# ---------------------------------------------------------------- report

def run_offline(rootfs, profile, policy, project=None, manifests=None, keyring=None, cmdline_sha256=None, runner=None, review=None):
    """Evaluate every catalogue row against one rootfs; returns the report dict. review is the
    policy review record (load_review); without a bound one a REVIEWED policy still blocks."""
    if profile not in PROFILES:
        raise DeploymentError("profile must be controller or full")
    rootfs = Path(rootfs)
    try:
        if not stat.S_ISDIR(os.lstat(rootfs).st_mode):
            raise DeploymentError("rootfs must be a real directory, not a symlink or file")
    except OSError:
        raise DeploymentError("rootfs is missing") from None
    rootfs = rootfs.resolve(strict=True)
    if cmdline_sha256 is not None and (type(cmdline_sha256) is not str or not _HEX64.fullmatch(cmdline_sha256)):
        raise DeploymentError("cmdline SHA-256 must be 64 lowercase hex digits")
    manifests = dict(manifests or {})
    for name, value in manifests.items():
        if name not in COMPONENT_MANIFESTS or type(value) is not tuple or len(value) != 2:
            raise DeploymentError("unsupported component manifest: " + str(name))
        if not Path(value[0]).is_file() or (value[1] is not None and not Path(value[1]).is_file()):
            raise DeploymentError("component manifest/signature file is missing")
    if keyring is not None and not Path(keyring).is_file():
        raise DeploymentError("keyring file is missing")
    project = Path(project if project is not None else deploy.PROJECT).resolve(strict=True)
    policy_path = Path(policy)
    # Each input is read once: the digests in the report name exactly the bytes validated.
    data, policy_sha256 = load_policy(policy_path, digest=True)
    source_lock_sha256 = deploy.sha(HERE / "sources.lock.json")
    reviewed, review_sha256 = (load_review(review, policy_sha256, data, source_lock_sha256) if review is not None
                               else ("MISSING", None))
    ctx = Ctx(rootfs, profile, data, project, manifests, Path(keyring).resolve() if keyring else None, cmdline_sha256, runner)
    checks = []
    for row in CATALOGUE:
        result = Result(row)
        check = CHECKS.get(row[0])
        if check is not None:
            try:
                check(ctx, result)
            except Blocked as exc:
                result.block(exc.path, exc.rule)
            except (ImportError, OSError, ValueError, RuntimeError, RecursionError, subprocess.SubprocessError):
                result.block(".", "evaluation_error")  # message omitted: it could quote target bytes
            if not ctx.complete and row[0] != "RX-00" and row[2] == "OFFLINE":
                result.block(".", "inventory_incomplete")
        checks.append(result.report())
    counts = {s: sum(c["status"] == s for c in checks) for s in STATUSES}
    policy_blocker = ("POLICY_NOT_REVIEWED" if data["status"] != "REVIEWED" else None if reviewed == "BOUND"
                      else "POLICY_REVIEW_RECORD_" + reviewed)
    blockers = ([policy_blocker] if policy_blocker else []) + [c["id"] for c in checks if c["status"] == "BLOCKED"]
    inventory = hashlib.sha256()
    for rel in ctx.keys:
        entry = ctx.entries[rel]
        inventory.update(("%s\0%s\0%d\0%s\n" % (rel, entry.kind, entry.size, entry.target or "")).encode("utf-8", "surrogateescape"))
    # The verdict also depends on deploy.py and on the checker's own srrx modules that ran.
    dependencies = dict(sorted({"deployment/deploy.py": deploy.sha(Path(deploy.__file__).resolve()), **ctx.evaluated}.items()))
    return {"schema_version": 1, "tool": "srrx-selftest", "mode": "offline", "profile": profile,
            "tool_sha256": deploy.sha(Path(__file__).resolve()), "tool_dependencies": dependencies,
            "policy_sha256": policy_sha256, "policy_status": data["status"],
            "policy_review": {"status": reviewed, "sha256": review_sha256},
            "source_lock_sha256": source_lock_sha256,
            "target": {"rootfs": str(rootfs), "files_scanned": sum(e.kind == "file" for e in ctx.entries.values()),
                       "entries": len(ctx.entries), "inventory_sha256": inventory.hexdigest(), "inventory_complete": ctx.complete},
            "status": "FAIL" if counts["FAIL"] else "BLOCKED" if blockers else "OFFLINE_CHECKS_PASS",
            "blockers": blockers, "hardware_ready": False, "receive_only_proven": False,
            "scope": "Static allowlist/denylist evidence only; runtime/hardware rows are RUNTIME_ONLY.",
            "checks": checks, "counts": counts}


def _manifest_args(values):
    out = {}
    for value in values:
        name, sep, rest = value.partition("=")
        if not sep or not rest or name in out:
            raise DeploymentError("--component-manifest needs NAME=MANIFEST[" + os.pathsep + "SIG] once per component")
        manifest, sep, signature = rest.rpartition(os.pathsep) if os.pathsep in rest else (rest, "", "")
        out[name] = (Path(manifest), Path(signature) if sep and signature else None)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    commands = parser.add_subparsers(dest="operation", required=True)
    commands.add_parser("catalogue")
    offline = commands.add_parser("offline")
    offline.add_argument("--rootfs", type=Path, required=True)
    offline.add_argument("--profile", choices=PROFILES, required=True)
    offline.add_argument("--policy", type=Path, required=True)
    offline.add_argument("--policy-review", type=Path, help="review record bound to a REVIEWED policy (load_review)")
    offline.add_argument("--project", type=Path)
    offline.add_argument("--component-manifest", action="append", default=[], metavar="NAME=MANIFEST[" + os.pathsep + "SIG]")
    offline.add_argument("--keyring", type=Path)
    offline.add_argument("--cmdline-sha256")
    offline.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == "catalogue":
            print(json.dumps(catalogue(), indent=2))
            return 0
        output = args.output.absolute()
        if output.exists() or output.is_symlink():
            raise DeploymentError("--output must be a NEW file")
        if output.resolve().is_relative_to(args.rootfs.resolve()):
            raise DeploymentError("--output must be outside the inspected rootfs")
        report = run_offline(args.rootfs, args.profile, args.policy, args.project, _manifest_args(args.component_manifest),
                             args.keyring, args.cmdline_sha256, review=args.policy_review)
        with output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"status": report["status"], "output": str(output), "counts": report["counts"], "blockers": report["blockers"]}, indent=2))
        return 0 if report["status"] == "OFFLINE_CHECKS_PASS" else 2
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    sys.exit(main())
