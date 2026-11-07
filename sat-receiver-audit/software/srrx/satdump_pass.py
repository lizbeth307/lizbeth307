"""SatDump pass glue for the v2.1 Meteor-M LRPT baseband policy (stdlib only).

Sources: STACK.md:882 and :886 (SatDump unit rules), :977 (baseband policy),
build/07-pz-vstanovlennia.md section 11, build/12-revision-v2.1.md, build/15 decision 6.

- select_windows(): recording windows from a saved srrx.passes plan. The window source is
  passes.baseband_windows(plan, ids) (complete passes, nothing without verified UTC:
  UTC_NOT_VERIFIED); the target set is enforced here: only accepted-allowlist targets with
  role LRPT whose reviewed display name is Meteor-M N2-3 or N2-4 (baseband.METEOR_TARGETS;
  software/config/orbit-targets.json names them by SATCAT name and launch date, never by a
  NORAD id in code). Other LRPT-role targets are counted, never recorded. Each window is
  AOS-60 s .. LOS+60 s, at most 20 min (srrx.baseband.window).
- decode_argv()/live_argv() are the only SatDump command lines: the pinned 1aedd60 CLI
  `satdump pipeline <id> baseband <in> <out> --samplerate=256000 --baseband_format=cs16`
  (CLI11 options as "--key=value"; c0b6f88 makes "--key value" work too) and the legacy live
  form `satdump legacy live <id> <out> --source net_source --mode udp --port P ...`, whose
  parser (src-core/common/cli_utils.cpp parse_common_flags) reads "--key value" pairs only.
- Each SatDump file decode is one instance of the static, root-owned template
  srrx-satdump-decode@<recording id>.service (software/systemd, text = unit_text("decode"),
  STACK.md:882): own user, empty root-owned WorkingDirectory (no ./resources, ./plugins or
  ./pipelines.json), a private empty HOME (RuntimeDirectory) so no user pipelines.json or
  settings load, /data replaced by an empty tmpfs with only the one baseband bound read-only
  and the work directory bound writable, LC_ALL=C.UTF-8, PrivateNetwork=yes. The sandbox and
  ExecStart are fixed in that file; the instance name (the recording id) selects the paths and
  nothing else, and srrx.satdump_unit re-validates the job inside the unit. Transient units
  are not used: systemd 255 authorises StartTransientUnit with no polkit details
  (src/core/dbus-manager.c:1108, src/core/dbus.c:1191-1193), so no rule could keep a
  transient unit from running as root, while a template start carries unit and verb
  (src/core/dbus-util.c:151-181). The live (UDP) decode keeps its reviewed properties
  (unit_lines("live")) but no unit is staged for it: it stays the device row RX-04-live.
- run_decode(): decoder_policy.satdump_plan (installation, metadata, scope), the decode unit
  started with `systemctl start` (srrx.baseband_scheduler starts it without blocking and polls),
  the unit's bounded output scan that fails on "CALCEPH ERROR" (srrx.satdump_unit), the baseband
  deleted before the sanitized PNG products are published (decoder_policy.satdump_publish), and
  deleted whatever the outcome.
- The work tree <products>/.satdump-<recording id> is made 2770 whatever the caller's umask
  (make_work_dir). The caller must hold group srrx-satdump (labd through the staged drop-in
  srrx.service.d/60-baseband-scheduler.conf, srrx.baseband_scheduler.labd_dropin; never a
  sysusers "m" line): it reads the unit's PNGs and removes the unit's directories.
- load_plan() reads only /var/lib/srrx/plans/<16 hex>.json written by srrx-passes@.service
  (srrx.pass_jobs: directory 2750 srrx-passes:labd, plans 0640), so the window source is the
  isolated plan unit, not any JSON a caller names.

labd schedules attended passes through srrx.baseband_scheduler (record unit, then this decode);
the CLI below stays for an administrator. Nothing here is RF or hardware evidence.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import sys
import time

from . import baseband, passes

SATDUMP = "/usr/bin/satdump"
SYSTEMCTL = "/usr/bin/systemctl"
UNIT_USER = "srrx-satdump"
BASEBAND_GROUP = "srrx-bb"
EMPTY_WORKDIR = "/var/lib/srrx-satdump/empty"
BASEBAND_ENV = "/etc/srrx/baseband.env"  # written by the administrator only; staging ships the .template
DATA_ROOT = baseband.DATA_ROOT
PRODUCTS_DIR = "products/satdump"
# The accepted SatDump installation record (decoder_policy.load_satdump_installation) the unit re-reads.
INSTALLATION_PATH = "/etc/srrx/satdump-installation.json"
# srrx.pass_jobs PLAN_ROOT / UNIT_USER (tests check the equality; no import of the labd side here).
PLAN_ROOT = "/var/lib/srrx/plans"
PLAN_WRITER = "srrx-passes"
WORK_MODE = 0o2770
PROBE_MAX_S = 60
DECODE_MAX_S = 1800
# TimeoutStartSec= of the decode template (a oneshot: RuntimeMaxSec= would not bound it): probe + decode + slack.
DECODE_UNIT_TIMEOUT_S = PROBE_MAX_S + DECODE_MAX_S + 60
# TimeoutStartSec= of the record template: the longest window (baseband.MAX_FILE_S), the early start, the
# 10 s worker start of labrx and slack for the flush, the branch OFF and the result file.
RECORD_UNIT_TIMEOUT_S = baseband.MAX_FILE_S + 120
LIVE_EXTRA_S = 120
OUTPUT_LIMIT = 64 * 1024
FAIL_MARKERS = (b"CALCEPH ERROR",)
PROBE_MARKERS = (b"level", b"input_file", b"output_folder", b"--samplerate", b"--baseband_format")
_UNIT_ID = re.compile(r"[0-9a-f]{16}\Z")
# Template instances: "lrpt-" + 16 lowercase hex digits, the recording id (decode) or the job id (record).
INSTANCE = re.compile(r"lrpt-[0-9a-f]{16}\Z")
DECODE_TEMPLATE = "srrx-satdump-decode@.service"
RECORD_TEMPLATE = "srrx-baseband-record@.service"
# labd's job directories (srrx.service RuntimeDirectory=srrx); PID 1 copies job.json into the unit (LoadCredential=).
JOB_ROOT = "/run/srrx/satdump"
JOB_FILE = "job.json"
RESULT_FILE = "result.json"  # the record unit's result, in its job directory
UNIT_RESULT = "unit-result.json"  # the decode unit's result, in its work tree
MAX_JOB_BYTES = 16 * 1024
MAX_RESULT_BYTES = 4096
# The record unit's interpreter: labrx needs NumPy, which the image's /usr/bin/python3 lacks
# (deployment/image/build_image.py, target_python_numpy); /opt/srrx/venv has it. The source tree comes
# first through PYTHONPATH, so the unit runs /opt/srrx/software as labd does, never a venv copy.
RECORD_PYTHON = "/opt/srrx/venv/bin/python3"
RTLA_DEVICE = "/dev/lab/rtla"  # deploy.udev_rules alias of the RTL-A USB node (devices.template.json)
_COMMON = ("Group=" + UNIT_USER, "UMask=0007", "LimitCORE=0", "NoNewPrivileges=yes", "CapabilityBoundingSet=",
           "AmbientCapabilities=", "ProtectSystem=strict", "ProtectHome=yes", "PrivateTmp=yes", "PrivateDevices=yes",
           "DevicePolicy=closed", "PrivateIPC=yes", "ProtectKernelTunables=yes", "ProtectKernelModules=yes",
           "ProtectKernelLogs=yes", "ProtectControlGroups=yes", "ProtectClock=yes", "ProtectHostname=yes",
           "RestrictNamespaces=yes", "RestrictRealtime=yes", "RestrictSUIDSGID=yes", "LockPersonality=yes",
           "SystemCallArchitectures=native", "MemoryMax=1536M", "MemorySwapMax=0", "TasksMax=64",
           "CPUAffinity=0-3", "Nice=10", "TemporaryFileSystem=" + DATA_ROOT + ":ro")


class PassRefused(ValueError):
    """Stable refusal code; never embeds paths, plan contents or decoder output."""


def _refuse(code):
    raise PassRefused(code)


# ---------------------------------------------------------------- windows

def meteor_targets(accepted):
    """({norad: display name} of Meteor-M LRPT targets, count of other LRPT-role targets)."""
    if type(accepted) is not dict:
        _refuse("ACCEPTED_ALLOWLIST_REQUIRED")
    targets, others = {}, 0
    for norad, target in accepted.items():
        if type(target) is not dict or type(norad) is not int or target.get("norad_id") != norad:
            _refuse("ACCEPTED_ALLOWLIST_REQUIRED")
        if target.get("role") != baseband.BASEBAND_ROLE:
            continue
        if target.get("name") in baseband.METEOR_TARGETS:
            targets[norad] = target["name"]
        else:
            others += 1
    return targets, others


def select_windows(plan, accepted, center_hz, symbol_rate):
    """Recording windows (srrx.baseband.window) of the plan's Meteor-M passes; fail closed.

    plan: a saved srrx.passes plan; accepted: norad_allowlist.load_accepted() output (the
    SHA-checked reviewed allowlist). center_hz/symbol_rate: one of the allowed LRPT tunings,
    chosen by the operator; nothing here guesses which satellite uses which.
    """
    targets, others = meteor_targets(accepted)
    baseband.channel_span(center_hz, symbol_rate)  # refuses a tuning outside the allowed set first
    result = {"windows": [], "reason": None, "non_meteor_lrpt_targets": others}
    if not targets:
        result["reason"] = "NO_METEOR_LRPT_TARGET"
        return result
    source = passes.baseband_windows(plan, frozenset(targets))
    if source["reason"] == "UTC_NOT_VERIFIED":
        result["reason"] = "UTC_NOT_VERIFIED"
        return result
    for item in source["windows"]:
        if item["name"] != targets.get(item["norad_id"]):
            continue  # the plan was made with another allowlist name: never recorded
        result["windows"].append(baseband.window(item["norad_id"], targets[item["norad_id"]], center_hz, symbol_rate,
                                                 item["start_unix_s"], item["end_unix_s"], item["start_utc"],
                                                 item["end_utc"]))
    result["reason"] = None if result["windows"] else "NO_METEOR_PASS"
    return result


def window_at(windows, now):
    """The window to record now: start - EARLY_START_S <= now <= end, or None."""
    for item in windows:
        if item["start_unix_s"] - baseband.EARLY_START_S <= now <= item["end_unix_s"]:
            return baseband.validate_window(item)
    return None


def _plan_writer_uid():
    import pwd  # POSIX only, as the plan unit
    try:
        return pwd.getpwnam(PLAN_WRITER).pw_uid
    except KeyError:
        _refuse("PLAN_WRITER_UNKNOWN")


def load_plan(path):
    """A plan of srrx-passes@.service: PLAN_ROOT/<16 hex>.json, regular, <= 2 MiB, checked by passes.validate_plan.

    time_verified and the pass times are the plan unit's statement, so the file must come from
    that unit: the directory and the file owned by PLAN_WRITER and writable by nobody else.
    """
    path = Path(path)
    if path.parent != Path(PLAN_ROOT) or not re.fullmatch(r"[0-9a-f]{16}\.json", path.name):
        _refuse("PLAN_NOT_FROM_PLAN_UNIT")
    writer = _plan_writer_uid()
    try:
        directory = os.lstat(PLAN_ROOT)
    except OSError:
        _refuse("PLAN_NOT_FROM_PLAN_UNIT")
    if not stat.S_ISDIR(directory.st_mode) or directory.st_uid != writer or directory.st_mode & 0o022:
        _refuse("PLAN_NOT_FROM_PLAN_UNIT")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
                         | getattr(os, "O_CLOEXEC", 0))
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            _refuse("PLAN_NOT_REGULAR_FILE")
        if info.st_uid != writer or info.st_mode & 0o022 or info.st_nlink != 1:
            _refuse("PLAN_NOT_FROM_PLAN_UNIT")
        data = stream.read(passes.MAX_PLAN_BYTES + 1)
    if len(data) > passes.MAX_PLAN_BYTES:
        _refuse("PLAN_SIZE_LIMIT")
    try:
        return passes.validate_plan(passes.orbits._json(data))
    except ValueError:
        _refuse("PLAN_INVALID")


# ---------------------------------------------------------------- SatDump command lines and units

def unit_id(recording_id):
    if type(recording_id) is not str or not baseband._ID.match(recording_id):
        _refuse("RECORDING_ID")
    return recording_id[len("lrpt-"):]


def decode_argv(executable, pipeline, input_path, output_dir):
    if pipeline not in baseband.PIPELINES.values():
        _refuse("PIPELINE_NOT_ALLOWLISTED")
    return [str(executable), "pipeline", pipeline, "baseband", str(input_path), str(output_dir),
            "--samplerate=%d" % baseband.OUTPUT_RATE_HZ, "--baseband_format=cs16"]


def probe_argv(executable, pipeline):
    if pipeline not in baseband.PIPELINES.values():
        _refuse("PIPELINE_NOT_ALLOWLISTED")
    return [str(executable), "pipeline", pipeline, "--help"]


def live_argv(executable, window_value, output_dir, port):
    checked = baseband.validate_window(window_value)
    if type(port) is not int or not baseband.LIVE_PORT_RANGE[0] <= port <= baseband.LIVE_PORT_RANGE[1]:
        _refuse("LIVE_PORT_RANGE")
    seconds = int(checked["end_unix_s"] - checked["start_unix_s"]) + 60
    return [str(executable), "legacy", "live", checked["pipeline"], str(output_dir), "--source", "net_source",
            "--mode", "udp", "--port", str(port), "--samplerate", str(baseband.OUTPUT_RATE_HZ),
            "--frequency", str(checked["center_hz"]), "--timeout", str(seconds)]


def _paths_ok(*paths):
    for path in paths:
        text = str(path)
        if not text.startswith("/") or "/../" in text + "/" or "/./" in text + "/" or any(c in text for c in " \t\n'\"\\;"):
            _refuse("UNIT_PATH")


def _instance(value):
    """A template instance name ("lrpt-" + 16 hex digits); "%i" only for the template text itself."""
    if value != "%i" and (type(value) is not str or not INSTANCE.match(value)):
        _refuse("UNIT_INSTANCE")
    return value


def unit_lines(kind, instance="%i"):
    """The [Service] sandbox lines of one SatDump unit kind, the single source of the template text.

    "decode": srrx-satdump-decode@.service (staged); instance "%i" gives the template lines, a
    recording id the lines one instance expands to. "live": the reviewed properties of a live
    (UDP) unit, which is not staged in this build (device row RX-04-live); a live unit would also
    bound itself to the window plus LIVE_EXTRA_S.
    """
    if kind not in ("decode", "live"):
        _refuse("UNIT_KIND")
    instance = _instance(instance)
    work = DATA_ROOT + "/" + PRODUCTS_DIR + "/.satdump-" + instance
    lines = ["User=" + UNIT_USER, *_COMMON, "WorkingDirectory=" + EMPTY_WORKDIR,
             "RuntimeDirectory=srrx-satdump-" + instance, "RuntimeDirectoryMode=0700",
             "Environment=HOME=/run/srrx-satdump-" + instance, "Environment=LC_ALL=C.UTF-8", "BindPaths=" + work]
    if kind == "decode":
        lines += ["SupplementaryGroups=" + BASEBAND_GROUP,
                  "BindReadOnlyPaths=" + DATA_ROOT + "/" + baseband.CLASS_DIR + "/" + instance + baseband.DATA_SUFFIX,
                  "PrivateNetwork=yes", "IPAddressDeny=any", "RestrictAddressFamilies=AF_UNIX",
                  "LoadCredential=job:" + JOB_ROOT + "/" + instance + "/" + JOB_FILE,
                  "TimeoutStartSec=%d" % DECODE_UNIT_TIMEOUT_S]
    else:
        lines += ["IPAddressDeny=any", "IPAddressAllow=localhost", "RestrictAddressFamilies=AF_INET AF_UNIX"]
    return lines


def record_lines(instance="%i"):
    """The [Service] lines of srrx-baseband-record@.service: labrx.run_baseband of one window as labd.

    User labd owns the class directory (2750 labd:srrx-bb). Group lab opens the RTL-A USB node
    (udev GROUP="lab"), and DevicePolicy=closed with DeviceAllow= of the RTL-A alias lets the cgroup
    open that node and nothing else; labd itself never gets group lab. The StorageGuard needs the
    whole /data mount writable (a nested ReadWritePaths= bind is a foreign mount to it, see
    sweep_units). AF_UNIX reaches labd's control socket (the read-only ControlGuard and the branch
    OFF); AF_NETLINK is libusb's device monitor. No AF_INET: the live UDP path is not available here.
    """
    instance = _instance(instance)
    return ["User=labd", "Group=" + BASEBAND_GROUP, "SupplementaryGroups=lab", "UMask=0027", "WorkingDirectory=/",
            "EnvironmentFile=" + BASEBAND_ENV,
            "Environment=PYTHONPATH=/opt/srrx/software PYTHONDONTWRITEBYTECODE=1 LC_ALL=C.UTF-8",
            "Environment=OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1",
            "LoadCredential=job:" + JOB_ROOT + "/" + instance + "/" + JOB_FILE,
            "ReadWritePaths=" + DATA_ROOT + " " + JOB_ROOT + "/" + instance,
            "ProtectSystem=strict", "ProtectHome=yes", "PrivateTmp=yes", "PrivateIPC=yes", "PrivateNetwork=yes",
            "IPAddressDeny=any", "RestrictAddressFamilies=AF_UNIX AF_NETLINK", "DevicePolicy=closed",
            "DeviceAllow=" + RTLA_DEVICE + " rw", "NoNewPrivileges=yes", "CapabilityBoundingSet=", "AmbientCapabilities=",
            "LimitCORE=0", "ProtectKernelTunables=yes", "ProtectKernelModules=yes", "ProtectKernelLogs=yes",
            "ProtectControlGroups=yes", "ProtectClock=yes", "ProtectHostname=yes", "RestrictNamespaces=yes",
            "RestrictRealtime=yes", "RestrictSUIDSGID=yes", "LockPersonality=yes", "SystemCallArchitectures=native",
            "MemoryMax=512M", "MemorySwapMax=0", "TasksMax=32", "KillMode=mixed",
            "TimeoutStartSec=%d" % RECORD_UNIT_TIMEOUT_S, "TimeoutStopSec=15"]


def unit_text(kind):
    """Exact text of software/systemd/srrx-satdump-decode@.service ("decode") or srrx-baseband-record@.service
    ("record"); tests and selftest RX-04-bb compare the files with it."""
    if kind == "decode":
        head = ("[Unit]\nDescription=SR-RX SatDump file decode of LRPT baseband %i (no network, no device)\n"
                "# Generated text: srrx.satdump_pass.unit_text(\"decode\"); edit the generator, then this file.\n"
                "# Started only by labd (srrx.baseband_scheduler) through 60-srrx-satdump.rules. No install section:\n"
                "# never enabled and never wanted by another unit. The instance is the recording id; it selects\n"
                "# the bound paths below and nothing else, and srrx.satdump_unit re-validates the job.\n"
                "CollectMode=inactive-or-failed\nRequiresMountsFor=" + DATA_ROOT + "\n\n[Service]\nType=oneshot\n")
        body = unit_lines("decode") + ["Environment=PYTHONPATH=/opt/srrx/software PYTHONDONTWRITEBYTECODE=1",
                                       "ExecStart=/usr/bin/python3 -P -s -B -m srrx.satdump_unit decode %i"]
    elif kind == "record":
        head = ("[Unit]\nDescription=SR-RX LRPT baseband recording %i on RTL-A (receive only, no network)\n"
                "# Generated text: srrx.satdump_pass.unit_text(\"record\"); edit the generator, then this file.\n"
                "# Started and stopped only by labd (srrx.baseband_scheduler) through 60-srrx-satdump.rules.\n"
                "# No install section. labrx observes labd read-only: the operator's lease, ARM and EN_RTLA stay theirs.\n"
                "CollectMode=inactive-or-failed\nRequiresMountsFor=" + DATA_ROOT + "\n"
                "# Skipped, not failed, until the administrator writes the storage binding at commissioning.\n"
                "ConditionPathExists=" + BASEBAND_ENV + "\n\n[Service]\nType=oneshot\n")
        body = record_lines() + ["ExecStart=/usr/bin/env " + RECORD_PYTHON + " -P -s -B -m srrx.satdump_unit record %i"]
    else:
        _refuse("UNIT_KIND")
    return head + "\n".join(body) + "\n"


def unit_name(template, instance):
    """srrx-satdump-decode@<instance>.service or srrx-baseband-record@<instance>.service."""
    if template not in (DECODE_TEMPLATE, RECORD_TEMPLATE) or instance == "%i":
        _refuse("UNIT_INSTANCE")
    return template.replace("@.", "@" + _instance(instance) + ".")


def make_work_dir(work):
    """Create one new work tree with mode WORK_MODE whatever the umask, or refuse.

    mkdir() masks its mode with the caller's umask (labd has none, a shell 022), so the mode is
    set by chmod() and read back. The setgid bit survives chmod only when the directory's group
    (srrx-satdump, inherited from the 2770 products directory) is one of the caller's groups:
    a caller outside group srrx-satdump gets WORK_DIR_MODE here, not a unit that cannot write.
    """
    work = Path(work)
    os.mkdir(work, 0o700)
    try:
        os.chmod(work, WORK_MODE)
        info = os.lstat(work)
        if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != WORK_MODE:
            _refuse("WORK_DIR_MODE")
    except BaseException:
        os.rmdir(work)
        raise
    return work


def run_bounded(argv, timeout_s, *, env=None, cwd="/"):
    """(exit code, last OUTPUT_LIMIT bytes of stdout+stderr plus every FAIL_MARKERS seen anywhere).

    The output is only scanned, never stored or logged. env replaces the whole environment.
    """
    environment = {"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "SYSTEMD_PAGER": "", "SYSTEMD_COLORS": "0"}
    if env is not None:
        environment = dict(env)
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               env=environment, cwd=cwd, close_fds=True, start_new_session=True)
    data, seen, deadline = bytearray(), set(), time.monotonic() + timeout_s
    overlap = max(len(marker) for marker in FAIL_MARKERS)
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    _refuse("SATDUMP_TIMEOUT")
                for key, unused in selector.select(remaining):
                    block = os.read(key.fileobj.fileno(), 65536)
                    if not block:
                        selector.unregister(key.fileobj)
                        continue
                    window = bytes(data[-overlap:]) + block
                    seen.update(marker for marker in FAIL_MARKERS if marker in window)
                    data.extend(block)
                    del data[:max(0, len(data) - OUTPUT_LIMIT)]
        code = process.wait(timeout=max(0.001, deadline - time.monotonic()))
        return code, bytes(data) + b"".join(b"\n" + marker for marker in sorted(seen))
    except subprocess.TimeoutExpired:
        _refuse("SATDUMP_TIMEOUT")
    finally:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            process.wait()
        process.stdout.close()


def output_failed(output):
    return any(marker in output for marker in FAIL_MARKERS)


# ---------------------------------------------------------------- jobs and results of the template units

_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,63}\Z")
_O_NEW = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
_O_READ = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)


def _sha(value, size):
    return type(value) is str and len(value) == size and all(c in "0123456789abcdef" for c in value)


def decode_job(recording_id, plan):
    """job.json of one decode instance: what labd's decoder_policy.satdump_plan fixed for the unit."""
    return check_decode_job({"v": 1, "kind": "srrx_satdump_decode_job", "recording_id": recording_id,
                             "pipeline": plan["pipeline"], "executable_sha256": plan["executable_sha256"],
                             "source_sha512": plan["source_sha512"]}, recording_id)


def check_decode_job(value, instance):
    if (type(value) is not dict or set(value) != {"v", "kind", "recording_id", "pipeline", "executable_sha256",
                                                    "source_sha512"}
            or value["v"] != 1 or type(value["v"]) is not int or value["kind"] != "srrx_satdump_decode_job"
            or value["recording_id"] != _instance(instance) or value["pipeline"] not in baseband.PIPELINES.values()
            or not _sha(value["executable_sha256"], 64) or not _sha(value["source_sha512"], 128)):
        _refuse("JOB_INVALID")
    return dict(value)


def record_job(instance, window_value):
    """job.json of one record instance: the window labd selected (select_windows) and nothing else."""
    return check_record_job({"v": 1, "kind": "srrx_baseband_record_job", "instance": instance,
                             "window": baseband.validate_window(window_value)}, instance)


def check_record_job(value, instance):
    if (type(value) is not dict or set(value) != {"v", "kind", "instance", "window"} or value["v"] != 1
            or type(value["v"]) is not int or value["kind"] != "srrx_baseband_record_job"
            or value["instance"] != _instance(instance)):
        _refuse("JOB_INVALID")
    try:
        window = baseband.validate_window(value["window"])
    except baseband.BasebandRefused:
        _refuse("JOB_INVALID")
    return dict(value, window=window)


def check_result(value, kind, instance):
    """The result a unit wrote: exact schema, stable codes only (never paths or decoder output)."""
    if kind == "decode":
        keys, statuses = {"v", "kind", "recording_id", "status", "reason"}, ("DECODED", "REFUSED")
        ident = "recording_id"
    else:
        keys = {"v", "kind", "instance", "status", "reason", "recording_id", "stop_reason", "samples",
                "branch_off_confirmed"}
        statuses, ident = ("RECORDED", "REFUSED"), "instance"
    if (type(value) is not dict or set(value) != keys or value["v"] != 1 or type(value["v"]) is not int
            or value["kind"] != "srrx_" + ("satdump_unit" if kind == "decode" else "baseband_record") + "_result"
            or value[ident] != _instance(instance) or value["status"] not in statuses):
        _refuse("UNIT_RESULT_INVALID")
    ok = value["status"] == statuses[0]
    if (value["reason"] is None) is not ok or (value["reason"] is not None and (type(value["reason"]) is not str
                                                                                 or not _CODE.match(value["reason"]))):
        _refuse("UNIT_RESULT_INVALID")
    if kind == "record":
        rid, samples, off = value["recording_id"], value["samples"], value["branch_off_confirmed"]
        if ok != (type(rid) is str and bool(baseband._ID.match(rid))) or (not ok and rid is not None):
            _refuse("UNIT_RESULT_INVALID")
        if ((ok and (type(samples) is not int or samples < 1 or value["stop_reason"] not in baseband.STOP_REASONS))
                or (not ok and (samples is not None or value["stop_reason"] is not None))
                or off not in (True, False, None)):
            _refuse("UNIT_RESULT_INVALID")
    return dict(value)


def result_value(kind, instance, status, reason=None, **extra):
    base = {"v": 1, "kind": "srrx_" + ("satdump_unit" if kind == "decode" else "baseband_record") + "_result",
            ("recording_id" if kind == "decode" else "instance"): instance, "status": status, "reason": reason}
    if kind == "record":
        base.update({"recording_id": None, "stop_reason": None, "samples": None, "branch_off_confirmed": None}, **extra)
    return check_result(base, kind, instance)


def _write_new(path, value, mode):
    data = (json.dumps(value, allow_nan=False, sort_keys=True) + "\n").encode("ascii")
    descriptor = os.open(path, _O_NEW, mode)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)


def write_job(job_root, instance, value):
    """labd's private directory job_root/<instance>/ (0700) with job.json (0600) for LoadCredential=."""
    root = Path(job_root)
    try:
        os.mkdir(root, 0o700)
    except FileExistsError:
        pass
    info = os.lstat(root)
    euid = getattr(os, "geteuid", lambda: info.st_uid)()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != euid or info.st_mode & 0o077:
        raise OSError("the SatDump job directory must be labd's own private directory")
    directory = root / _instance(instance)
    os.mkdir(directory, 0o700)  # a fresh random instance: an existing entry is refused
    try:
        _write_new(directory / JOB_FILE, value, 0o600)
    except BaseException:
        remove_job(job_root, instance)
        raise
    return directory


def remove_job(job_root, instance):
    directory = Path(job_root) / _instance(instance)
    for name in (JOB_FILE, RESULT_FILE, RESULT_FILE + ".tmp"):
        try:
            os.unlink(directory / name)
        except OSError:
            pass
    try:
        os.rmdir(directory)
    except OSError:
        pass


def read_result(path, kind, instance):
    """A unit's result file, or None when there is none yet: regular, no link, <= MAX_RESULT_BYTES."""
    try:
        descriptor = os.open(path, _O_READ)
    except FileNotFoundError:
        return None
    except OSError:
        _refuse("UNIT_RESULT_INVALID")
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            _refuse("UNIT_RESULT_INVALID")
        data = stream.read(MAX_RESULT_BYTES + 1)
    if len(data) > MAX_RESULT_BYTES:
        _refuse("UNIT_RESULT_INVALID")
    try:
        value = passes.orbits._json(data)
    except (ValueError, RecursionError):
        _refuse("UNIT_RESULT_INVALID")
    return check_result(value, kind, instance)


def systemctl_start(unit, timeout_s):
    """`systemctl --no-ask-password start` of one template instance (blocking: the oneshot runs to its end)."""
    process = subprocess.Popen([SYSTEMCTL, "--no-ask-password", "--quiet", "start", unit], stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd="/", close_fds=True,
                               env={"PATH": "/usr/bin:/bin", "LC_ALL": "C", "SYSTEMD_PAGER": "", "SYSTEMD_COLORS": "0"})
    try:
        return process.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise


# ---------------------------------------------------------------- decode job

def prepare_decode(store, recording_id, installation, products_root, *, scope=None, work_root=None, job_root=JOB_ROOT):
    """labd's part before the decode unit: the metadata and plan, an unused 2770 work tree, the job.

    Refusals are PassRefused or decoder_policy.DecoderRefused codes; the caller deletes the
    baseband after any refusal (run_decode, srrx.baseband_scheduler).
    """
    from . import decoder_policy
    unit_id(recording_id)
    products_root = Path(products_root)
    work = Path(work_root if work_root is not None else products_root) / (".satdump-" + recording_id)
    target = products_root / recording_id
    meta, identity = store.load(recording_id)
    plan = decoder_policy.satdump_plan(meta, installation, scope=scope)
    if target.exists() or target.is_symlink() or work.exists() or work.is_symlink():
        _refuse("OUTPUT_EXISTS")
    make_work_dir(work)  # 2770, setgid group srrx-satdump of the parent: the unit writes out/ there
    try:
        write_job(job_root, recording_id, decode_job(recording_id, plan))
    except BaseException:
        _remove_tree(work)
        raise
    return {"recording_id": recording_id, "work": work, "target": target, "plan": plan, "identity": identity,
            "job_root": str(job_root), "unit": unit_name(DECODE_TEMPLATE, recording_id)}


def png_bytes(output_dir, limit=4096):
    """Total size of the *.png files below a work tree's out/ (lstat only, no link followed, bounded)."""
    total, seen, stack = 0, 0, [Path(output_dir)]
    while stack:
        directory = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except FileNotFoundError:
            continue
        for entry in entries:
            seen += 1
            if seen > limit:
                _refuse("SATDUMP_OUTPUT_LIMIT")
            if entry.is_dir(follow_symlinks=False):
                if len(stack) < 64:
                    stack.append(Path(entry.path))
            elif entry.is_file(follow_symlinks=False) and entry.name.lower().endswith(".png"):
                total += entry.stat(follow_symlinks=False).st_size
    return total


def finish_decode(store, job, *, scope=None, publish_budget=None):
    """After the decode unit ended: its result, the unchanged source, the baseband deleted, then the PNGs.

    The baseband is deleted first and the products are published second, so the report's
    input_iq_deleted_after_decode states a completed deletion; a failed deletion publishes nothing
    (the sweep removes the file later). The work tree and the job directory are removed and the
    baseband is deleted whatever the outcome. publish_budget: the most PNG bytes this caller may
    hold in memory while publishing (labd: baseband_scheduler.LABD_PUBLISH_BUDGET_BYTES).
    """
    from . import decoder_policy
    recording_id, deleted = job["recording_id"], False
    try:
        try:
            result = read_result(Path(job["work"]) / UNIT_RESULT, "decode", recording_id)
            if result is None:
                decoder_policy._refuse("DECODE_UNIT_NO_RESULT")
            if result["status"] != "DECODED":
                decoder_policy._refuse(result["reason"])
            if store.identity(recording_id) != job["identity"]:
                decoder_policy._refuse("SOURCE_CHANGED_DURING_DECODE")
            if publish_budget is not None and png_bytes(Path(job["work"]) / "out") > publish_budget:
                decoder_policy._refuse("SATDUMP_PRODUCTS_OVER_PUBLISH_BUDGET")
            store.delete(recording_id)  # raises on failure: nothing is published with a false report
            deleted = True
            return decoder_policy.satdump_publish(Path(job["work"]) / "out", job["target"], job["plan"],
                                                  input_iq_deleted=True, scope=scope)
        finally:
            _remove_tree(job["work"])
            remove_job(job["job_root"], recording_id)
    finally:
        if not deleted:
            store.delete(recording_id)  # after a refused decode as well: never kept for later


def run_decode(store, recording_id, installation, products_root, *, scope=None, start_unit=systemctl_start,
               work_root=None, job_root=JOB_ROOT):
    """Decode one recording into sanitized PNG products; the baseband is deleted in every case.

    The decode runs in srrx-satdump-decode@<recording_id>.service (`systemctl start` blocks until
    the oneshot ends; the unit's result file, not systemctl's exit code, decides). Returns
    decoder_policy.satdump_publish's report. Refusals are PassRefused or decoder_policy.DecoderRefused
    codes.
    """
    job = None
    try:
        job = prepare_decode(store, recording_id, installation, products_root, scope=scope, work_root=work_root,
                             job_root=job_root)
    finally:
        if job is None:
            store.delete(recording_id)
    try:
        start_unit(job["unit"], DECODE_UNIT_TIMEOUT_S + 60)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass  # no result file: finish_decode refuses DECODE_UNIT_NO_RESULT and deletes the baseband
    return finish_decode(store, job, scope=scope)


def _remove_tree(path):
    """Remove a work tree without following links (the unit may have written anything there)."""
    path = Path(path)
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return
    if not stat.S_ISDIR(info.st_mode):
        os.unlink(path)
        return
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            _remove_tree(entry.path)
        else:
            os.unlink(entry.path)
    os.rmdir(path)


def tmpfiles():
    """tmpfiles.d text: the empty root-owned SatDump working directory and the baseband class directory."""
    return ("# SR-RX SatDump units (srrx.satdump_pass.tmpfiles): an empty, root-owned working directory and the\n"
            "# products directory, setgid " + UNIT_USER + " so the unit writes its work tree there; the caller needs\n"
            "# group " + UNIT_USER + " (it reads the unit's PNGs and removes its work tree): labd via SupplementaryGroups=.\n"
            "d /var/lib/srrx-satdump 0755 root root -\n"
            "d " + EMPTY_WORKDIR + " 0555 root root -\n"
            "d " + DATA_ROOT + "/products/satdump 2770 labd " + UNIT_USER + " -\n" + baseband.tmpfiles(DATA_ROOT))


def sweep_units():
    """srrx-baseband-sweep.service/.timer text: sweep() every 15 min and after boot (24 h rule).

    The sandbox is the one StorageGuard can work in: python3 without -I (-I implies -E and
    would drop PYTHONPATH; -P and -s keep the working directory and the user site out), the
    whole bound mount writable (ProtectSystem=strict remounts it read-only, and a nested
    ReadWritePaths= bind is a foreign mount to the guard), and /dev visible (the guard stats
    /dev/disk/by-uuid and the mount source) with DevicePolicy=closed denying every open().
    """
    service = ("[Unit]\nDescription=SR-RX LRPT baseband sweep (delete >= 24 h, incomplete or invalid recordings)\n"
               "RequiresMountsFor=" + DATA_ROOT + "\n"
               "# Skipped, not failed, until the administrator writes the storage binding at commissioning.\n"
               "ConditionPathExists=" + BASEBAND_ENV + "\n\n[Service]\nType=oneshot\nUser=labd\nGroup=" + BASEBAND_GROUP + "\n"
               "EnvironmentFile=" + BASEBAND_ENV + "\n"
               "Environment=PYTHONPATH=/opt/srrx/software PYTHONDONTWRITEBYTECODE=1\nWorkingDirectory=/\n"
               "ExecStart=/usr/bin/python3 -P -s -B -m srrx.baseband sweep --storage-root " + DATA_ROOT + " "
               "--storage-device ${SRRX_BB_DEVICE}\n"
               "ReadWritePaths=" + DATA_ROOT + "\nProtectSystem=strict\nProtectHome=yes\nPrivateTmp=yes\n"
               "PrivateNetwork=yes\nIPAddressDeny=any\nRestrictAddressFamilies=AF_UNIX\nNoNewPrivileges=yes\n"
               "DevicePolicy=closed\nCapabilityBoundingSet=\nTimeoutStartSec=120\n")
    timer = ("[Unit]\nDescription=SR-RX LRPT baseband sweep every 15 min\n\n[Timer]\nOnBootSec=2min\n"
             "OnUnitActiveSec=15min\nAccuracySec=1min\nPersistent=false\n\n[Install]\nWantedBy=timers.target\n")
    return {"etc/systemd/system/srrx-baseband-sweep.service": service,
            "etc/systemd/system/srrx-baseband-sweep.timer": timer}


def baseband_env_template():
    """etc/srrx/baseband.env.template: never the live file, which the administrator writes."""
    return ("# SR-RX v2.1 LRPT baseband storage binding (srrx.satdump_pass.baseband_env_template). TEMPLATE ONLY.\n"
            "# At commissioning the administrator writes " + BASEBAND_ENV + " (root:root 0644) with the verified\n"
            "# UUID of the /data partition of this unit, SRRX_BB_DEVICE=/dev/disk/by-uuid/<UUID>, then enables\n"
            "# srrx-baseband-sweep.timer. Without that file the sweep unit is skipped (ConditionPathExists=).\n"
            "# SRRX_BB_DRIVER_RECORD: the project-local RTL-A driver record bound to acceptance gate E5-04\n"
            "# (srrx.receivers.load_driver_record), for example /opt/srrx/evidence/<file>.json. The record unit\n"
            "# srrx-baseband-record@.service reads both values; srrx.baseband_scheduler refuses passes until they are set.\n"
            "SRRX_BB_DEVICE=\nSRRX_BB_DRIVER_RECORD=\n")


def transient_units():
    """Always empty: no SatDump unit is transient any more. Both are static templates in software/systemd,
    whose User=/Group= the staged-unit account check covers. Kept so deploy.stage and older callers stay valid."""
    return []


def staged_files():
    """Relative rootfs path -> text that deploy.stage writes: tmpfiles, the sweep service and timer
    (left disabled by the system preset) and the baseband.env template."""
    return dict(sweep_units(), **{"etc/tmpfiles.d/srrx-satdump.conf": tmpfiles(),
                                  "etc/srrx/baseband.env.template": baseband_env_template()})


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m srrx.satdump_pass",
                                     description="Meteor-M LRPT windows and SatDump decode (v2.1 policy)")
    commands = parser.add_subparsers(dest="command", required=True)
    windows = commands.add_parser("windows", help="list the recording windows of a saved plan")
    windows.add_argument("--plan", type=Path, required=True)
    windows.add_argument("--orbit-allowlist", type=Path, required=True)
    windows.add_argument("--orbit-allowlist-record", type=Path, required=True)
    windows.add_argument("--center-hz", type=int, required=True)
    windows.add_argument("--symbol-rate", type=int, required=True)
    decode = commands.add_parser("decode", help="decode one recording, publish sanitized products, delete it")
    decode.add_argument("--recording", required=True)
    decode.add_argument("--installation", type=Path, required=True)
    decode.add_argument("--products", type=Path, required=True)
    decode.add_argument("--storage-root", required=True)
    decode.add_argument("--storage-device", required=True)
    commands.add_parser("units", help="print the tmpfiles and sweep unit texts")
    args = parser.parse_args(argv)
    guard = None
    try:
        if args.command == "units":
            result = staged_files()
        elif args.command == "windows":
            from . import norad_allowlist
            accepted = norad_allowlist.load_accepted(args.orbit_allowlist, args.orbit_allowlist_record)
            selected = select_windows(load_plan(args.plan), accepted, args.center_hz, args.symbol_rate)
            result = dict(selected, windows=[{key: item[key] for key in ("norad_id", "target", "pipeline", "aos_utc",
                                                                          "los_utc", "clipped")}
                                             for item in selected["windows"]])
        else:
            from . import decoder_policy
            from .storage import StorageGuard
            guard = StorageGuard(args.storage_root, args.storage_device)
            installation = decoder_policy.load_satdump_installation(args.installation)
            result = run_decode(baseband.BasebandStore(guard), args.recording, installation, args.products)
    except (PassRefused, baseband.BasebandRefused, ValueError, OSError) as error:
        code = str(error) if isinstance(error, ValueError) and re.fullmatch(r"[A-Z0-9_]+", str(error)) else type(error).__name__
        print(json.dumps({"status": "REFUSED", "reason": code}))
        return 2
    finally:
        if guard is not None:
            guard.close()
    print(json.dumps(result, sort_keys=True, indent=1 if args.command == "units" else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
