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
- Each SatDump run is one bounded transient unit (systemd-run, STACK.md:882): own user,
  empty root-owned WorkingDirectory (no ./resources, ./plugins or ./pipelines.json), a
  private empty HOME (RuntimeDirectory) so no user pipelines.json or settings load, /data
  replaced by an empty tmpfs with only the one baseband bound read-only and the work
  directory bound writable, LC_ALL=C.UTF-8. File decode: PrivateNetwork=yes. Live:
  IPAddressDeny=any + IPAddressAllow=localhost and AF_INET/AF_UNIX only, because net_source
  at 1aedd60 binds INADDR_ANY (src-core/common/net/udp.h; the +lab loopback patch of
  deployment/recipes/satdump is a second layer).
- run_decode(): decoder_policy.satdump_plan (installation, metadata, scope), the unit, a
  bounded output scan that fails on "CALCEPH ERROR", sanitized PNG products only
  (decoder_policy.satdump_publish), and then the baseband is deleted, whatever the outcome.

labd does not schedule these jobs yet (an open integration item): the CLI below is for an
administrator, and the polkit rule that would let labd start the transient units is not
written. Nothing here is RF or hardware evidence.
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

SYSTEMD_RUN = "/usr/bin/systemd-run"
SATDUMP = "/usr/bin/satdump"
UNIT_USER = "srrx-satdump"
BASEBAND_GROUP = "srrx-bb"
EMPTY_WORKDIR = "/var/lib/srrx-satdump/empty"
DATA_ROOT = "/data"
DECODE_MAX_S = 1800
LIVE_EXTRA_S = 120
OUTPUT_LIMIT = 64 * 1024
FAIL_MARKERS = (b"CALCEPH ERROR",)
PROBE_MARKERS = (b"level", b"input_file", b"output_folder", b"--samplerate", b"--baseband_format")
_UNIT_ID = re.compile(r"[0-9a-f]{16}\Z")
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


def load_plan(path):
    """A saved plan file (regular, <= 2 MiB), checked by passes.validate_plan."""
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
                         | getattr(os, "O_CLOEXEC", 0))
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            _refuse("PLAN_NOT_REGULAR_FILE")
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


def unit_properties(kind, ident, *, work_dir, input_path=None, runtime_max_s=DECODE_MAX_S):
    """The fixed systemd-run properties of one SatDump unit ("decode" or "live")."""
    if kind not in ("decode", "live") or type(ident) is not str or not _UNIT_ID.match(ident):
        _refuse("UNIT_KIND")
    if type(runtime_max_s) is not int or not 60 <= runtime_max_s <= 3 * 3600:
        _refuse("UNIT_RUNTIME")
    _paths_ok(work_dir, *(() if input_path is None else (input_path,)))
    if not str(work_dir).startswith(DATA_ROOT + "/"):
        _refuse("UNIT_PATH")
    properties = ["User=" + UNIT_USER, *_COMMON, "WorkingDirectory=" + EMPTY_WORKDIR,
                  "RuntimeDirectory=srrx-satdump-" + ident, "RuntimeDirectoryMode=0700",
                  "Environment=HOME=/run/srrx-satdump-" + ident, "Environment=LC_ALL=C.UTF-8",
                  "BindPaths=" + str(work_dir), "RuntimeMaxSec=%d" % runtime_max_s]
    if kind == "decode":
        if input_path is None or not str(input_path).startswith(DATA_ROOT + "/" + baseband.CLASS_DIR + "/"):
            _refuse("UNIT_PATH")
        properties += ["SupplementaryGroups=" + BASEBAND_GROUP, "BindReadOnlyPaths=" + str(input_path),
                       "PrivateNetwork=yes", "IPAddressDeny=any", "RestrictAddressFamilies=AF_UNIX"]
    else:
        if input_path is not None:
            _refuse("UNIT_PATH")
        properties += ["IPAddressDeny=any", "IPAddressAllow=localhost", "RestrictAddressFamilies=AF_INET AF_UNIX"]
    return properties


def systemd_run_argv(kind, ident, properties, argv):
    unit = "srrx-satdump-%s-%s" % (kind, ident)
    command = [SYSTEMD_RUN, "--quiet", "--wait", "--pipe", "--collect", "--service-type=exec", "--unit=" + unit]
    for value in properties:
        command += ["-p", value]
    return command + ["--"] + list(argv)


def run_bounded(argv, timeout_s):
    """(exit code, last OUTPUT_LIMIT bytes of stdout+stderr plus every FAIL_MARKERS seen anywhere).

    The output is only scanned, never stored or logged.
    """
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               env={"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "SYSTEMD_PAGER": "",
                                    "SYSTEMD_COLORS": "0"},
                               cwd="/", close_fds=True, start_new_session=True)
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
                os.killpg(process.pid, signal.SIGTERM)  # systemd-run stops its unit on SIGTERM
            except ProcessLookupError:
                pass
            process.wait()
        process.stdout.close()


def output_failed(output):
    return any(marker in output for marker in FAIL_MARKERS)


# ---------------------------------------------------------------- decode job

def run_decode(store, recording_id, installation, products_root, *, scope=None, runner=run_bounded,
               work_root=None):
    """Decode one recording into sanitized PNG products; the baseband is deleted in every case.

    Returns decoder_policy.satdump_publish's report. Refusals are PassRefused or
    decoder_policy.DecoderRefused codes.
    """
    from . import decoder_policy
    ident = unit_id(recording_id)
    products_root = Path(products_root)
    work = Path(work_root if work_root is not None else products_root) / (".satdump-" + ident)
    target = products_root / recording_id
    try:
        meta, identity = store.load(recording_id)
        plan = decoder_policy.satdump_plan(meta, installation, scope=scope)
        if target.exists() or target.is_symlink() or work.exists() or work.is_symlink():
            _refuse("OUTPUT_EXISTS")
        executable = decoder_policy.satdump_executable(installation)
        input_path = store.data_path(recording_id)
        os.mkdir(work, 0o2770)  # setgid group of the parent: the unit (group srrx-satdump/srrx-bb) writes
        try:
            probe = systemd_run_argv("probe", ident, unit_properties("decode", ident, work_dir=work,
                                                                       input_path=input_path, runtime_max_s=60),
                                     probe_argv(executable, plan["pipeline"]))
            code, output = runner(probe, 90)
            if code or not all(marker in output for marker in PROBE_MARKERS):
                decoder_policy._refuse("LIVE_VENDOR_INTERFACE_UNVERIFIED")
            decoder_policy.satdump_executable(installation)  # re-hash after the probe
            argv = systemd_run_argv("decode", ident, unit_properties("decode", ident, work_dir=work,
                                                                       input_path=input_path),
                                    decode_argv(executable, plan["pipeline"], input_path, work / "out"))
            code, output = runner(argv, DECODE_MAX_S + 60)
            if code:
                decoder_policy._refuse("DECODER_NONZERO_EXIT")
            if output_failed(output):
                decoder_policy._refuse("SATDUMP_CALCEPH_ERROR")
            if store.identity(recording_id) != identity:
                decoder_policy._refuse("SOURCE_CHANGED_DURING_DECODE")
            return decoder_policy.satdump_publish(work / "out", target, plan, scope=scope)
        finally:
            _remove_tree(work)
    finally:
        store.delete(recording_id)  # after decode, or a refused one: never kept for later


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
            "# products directory, setgid " + UNIT_USER + " so the unit writes its work tree there.\n"
            "d /var/lib/srrx-satdump 0755 root root -\n"
            "d " + EMPTY_WORKDIR + " 0555 root root -\n"
            "d " + DATA_ROOT + "/products/satdump 2770 labd " + UNIT_USER + " -\n" + baseband.tmpfiles(DATA_ROOT))


def sweep_units():
    """srrx-baseband-sweep.service/.timer text: sweep() every 15 min and after boot (24 h rule)."""
    service = ("[Unit]\nDescription=SR-RX LRPT baseband sweep (delete >= 24 h, incomplete or invalid recordings)\n"
               "RequiresMountsFor=" + DATA_ROOT + "\n\n[Service]\nType=oneshot\nUser=labd\nGroup=" + BASEBAND_GROUP + "\n"
               "EnvironmentFile=/etc/srrx/baseband.env\n"
               "ExecStart=/usr/bin/python3 -I -B -m srrx.baseband sweep --storage-root ${SRRX_BB_ROOT} "
               "--storage-device ${SRRX_BB_DEVICE}\nEnvironment=PYTHONPATH=/opt/srrx/software\n"
               "ReadWritePaths=" + DATA_ROOT + "/" + baseband.CLASS_DIR + "\nProtectSystem=strict\nProtectHome=yes\n"
               "PrivateNetwork=yes\nIPAddressDeny=any\nRestrictAddressFamilies=AF_UNIX\nNoNewPrivileges=yes\n"
               "PrivateDevices=yes\nTimeoutStartSec=120\n")
    timer = ("[Unit]\nDescription=SR-RX LRPT baseband sweep every 15 min\n\n[Timer]\nOnBootSec=2min\n"
             "OnUnitActiveSec=15min\nAccuracySec=1min\nPersistent=false\n\n[Install]\nWantedBy=timers.target\n")
    return {"etc/systemd/system/srrx-baseband-sweep.service": service,
            "etc/systemd/system/srrx-baseband-sweep.timer": timer}


def staged_files():
    """Relative rootfs path -> text, for a future deploy.stage (not staged yet: integration item)."""
    return dict(sweep_units(), **{"etc/tmpfiles.d/srrx-satdump.conf": tmpfiles()})


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
