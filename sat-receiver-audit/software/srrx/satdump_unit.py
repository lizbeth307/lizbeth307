"""Entry point inside the static SatDump/baseband template units (stdlib only for decode).

  python3 -P -s -B -m srrx.satdump_unit decode <lrpt-16hex>   srrx-satdump-decode@.service
  python3 -P -s -B -m srrx.satdump_unit record <lrpt-16hex>   srrx-baseband-record@.service

labd (srrx.baseband_scheduler) writes the job as /run/srrx/satdump/<instance>/job.json; PID 1
copies it into this unit's credential directory (LoadCredential=job:...), and the instance
name comes from %i. Everything is re-validated here: the instance pattern, the job's exact
schema, its instance equal to %i, the pipeline in srrx.baseband.PIPELINES, the window by
srrx.baseband.validate_window. Paths are derived from the instance, never taken from the job.

decode: the accepted installation record (satdump_pass.INSTALLATION_PATH, root-owned) is
re-read and must name the executable digest labd's plan fixed; then the bounded `--help`
probe, a re-hash, the decode argv (satdump_pass.decode_argv) with a bounded output scan that
fails on "CALCEPH ERROR", and the result <work tree>/unit-result.json. The child gets a fixed
environment (PATH, LC_ALL, the unit's private HOME) and the empty root-owned working directory.

record: labrx.run_baseband of the job's window on the RTL-A driver record named by
SRRX_BB_DRIVER_RECORD (bound to acceptance gate E5-04, branch RTLA only, the one node the
unit's DeviceAllow= opens), the storage binding SRRX_BB_DEVICE (both from
/etc/srrx/baseband.env), labd's control socket as the read-only observer, a new ScopeLatch, no
live port. labrx's own stop handling applies: SIGTERM from `systemctl stop` (KillMode=mixed)
ends the recording and deletes the partial file, and the branch OFF is requested. The result
is /run/srrx/satdump/<instance>/result.json.

Results carry stable codes only (never paths, plan contents, positions or decoder output), and
stdout gets the same one JSON line. Nothing here is RF or hardware evidence.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import stat
import sys

from . import baseband, satdump_pass as sp

CREDENTIAL = "job"
ACCEPTANCE = "/etc/srrx/acceptance.json"
PROJECT = "/opt/srrx"
CONTROL_SOCKET = "/run/srrx/control.sock"
_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,63}\Z")


class UnitRefused(ValueError):
    """Stable refusal code of this entry point."""


def _code(error):
    """A stable code for any refusal: the exception's own code when it is one, else its class name."""
    if isinstance(error, KeyboardInterrupt):
        return "STOPPED_BY_SIGNAL"
    text = str(error)
    if isinstance(error, (ValueError, RuntimeError)) and _CODE.match(text):
        return text
    name = "UNIT_" + re.sub(r"[^A-Z0-9_]", "_", type(error).__name__.upper())
    return name[:64] if _CODE.match(name[:64]) else "UNIT_ERROR"


def read_job(instance, environ=None):
    """The job credential of this instance: $CREDENTIALS_DIRECTORY/job, regular, <= MAX_JOB_BYTES."""
    environ = os.environ if environ is None else environ
    directory = environ.get("CREDENTIALS_DIRECTORY")
    if type(directory) is not str or not os.path.isabs(directory):
        raise UnitRefused("JOB_CREDENTIAL_MISSING")
    try:
        descriptor = os.open(Path(directory) / CREDENTIAL, sp._O_READ)
    except OSError:
        raise UnitRefused("JOB_CREDENTIAL_MISSING") from None
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise UnitRefused("JOB_INVALID")
        data = stream.read(sp.MAX_JOB_BYTES + 1)
    if len(data) > sp.MAX_JOB_BYTES:
        raise UnitRefused("JOB_INVALID")
    try:
        return sp.passes.orbits._json(data)
    except (ValueError, RecursionError):
        raise UnitRefused("JOB_INVALID") from None


def write_result(path, value):
    """Write the result once (O_EXCL, no link followed), then the same line on stdout."""
    try:
        sp._write_new(path, value, 0o640)
    finally:
        print(json.dumps(value, sort_keys=True), flush=True)


# ---------------------------------------------------------------- decode

def decode(instance, *, environ=None, runner=sp.run_bounded, load_installation=None, executable_check=None):
    """Run the probe and the decode of one recording inside its unit; returns the result value."""
    from . import decoder_policy
    load_installation = load_installation or decoder_policy.load_satdump_installation
    executable_check = executable_check or decoder_policy.satdump_executable
    environ = os.environ if environ is None else environ
    job = sp.check_decode_job(read_job(instance, environ), instance)
    work = Path(sp.DATA_ROOT) / sp.PRODUCTS_DIR / (".satdump-" + instance)
    source = sp.DATA_ROOT + "/" + baseband.CLASS_DIR + "/" + instance + baseband.DATA_SUFFIX
    home = "/run/srrx-satdump-" + instance
    if environ.get("HOME") != home:  # the unit's private RuntimeDirectory, never the account's home
        raise UnitRefused("UNIT_HOME_MISMATCH")
    installation = load_installation(sp.INSTALLATION_PATH)
    if installation.get("sha256") != job["executable_sha256"]:
        raise UnitRefused("INSTALLATION_CHANGED_SINCE_PLAN")
    executable = executable_check(installation)
    child = {"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "HOME": home}
    code, output = runner(sp.probe_argv(executable, job["pipeline"]), sp.PROBE_MAX_S, env=child, cwd=sp.EMPTY_WORKDIR)
    if code or not all(marker in output for marker in sp.PROBE_MARKERS):
        raise UnitRefused("LIVE_VENDOR_INTERFACE_UNVERIFIED")
    executable_check(installation)  # re-hash after the probe
    code, output = runner(sp.decode_argv(executable, job["pipeline"], source, work / "out"), sp.DECODE_MAX_S,
                          env=child, cwd=sp.EMPTY_WORKDIR)
    if code:
        raise UnitRefused("DECODER_NONZERO_EXIT")
    if sp.output_failed(output):
        raise UnitRefused("SATDUMP_CALCEPH_ERROR")
    return sp.result_value("decode", instance, "DECODED")


# ---------------------------------------------------------------- record

def record(instance, *, environ=None, recorder=None, clock=None):
    """labrx.run_baseband of the job's window inside the record unit; returns the result value."""
    import time
    environ = os.environ if environ is None else environ
    job = sp.check_record_job(read_job(instance, environ), instance)
    device, driver = environ.get("SRRX_BB_DEVICE", ""), environ.get("SRRX_BB_DRIVER_RECORD", "")
    if not device.startswith("/dev/disk/by-uuid/") or len(device) <= len("/dev/disk/by-uuid/"):
        raise UnitRefused("BASEBAND_STORAGE_UNBOUND")
    if not driver.startswith("/") or not driver.endswith(".json"):
        raise UnitRefused("RTLA_DRIVER_RECORD_UNBOUND")
    now = (clock or time.time)()
    if now > job["window"]["end_unix_s"]:
        raise UnitRefused("WINDOW_OVER")
    if recorder is None:
        recorder = _hardware_recorder
    result = recorder(job["window"], device, driver)
    return sp.result_value("record", instance, "RECORDED", recording_id=result["recording_id"],
                           stop_reason=result["stop_reason"], samples=result["samples"],
                           branch_off_confirmed=result["branch_off_confirmed"])


def _hardware_recorder(window, device, driver):  # pragma: no cover - device only (RX-04-sched)
    from . import labrx
    from .commissioning import load_acceptance
    from .daemon import request_once
    from .receivers import load_driver_record
    from .scope_policy import ScopeLatch
    from .storage import StorageGuard
    accepted = load_acceptance(Path(ACCEPTANCE), Path(PROJECT), clock_check=False)
    driver_record = load_driver_record(Path(driver), Path(PROJECT), accepted)
    if driver_record["backend"] != "rtl" or driver_record["branch"] != "RTLA":
        raise UnitRefused("RTLA_DRIVER_RECORD_REQUIRED")  # DeviceAllow= opens the RTL-A node only
    guard = StorageGuard(baseband.DATA_ROOT, device)
    try:
        return labrx.run_baseband(window, baseband.BasebandStore(guard), scope=ScopeLatch(), record=driver_record,
                                  transport=lambda request: request_once(CONTROL_SOCKET, request, timeout=.2))
    finally:
        guard.close()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] not in ("decode", "record") or not sp.INSTANCE.match(argv[1]):
        print(json.dumps({"status": "REFUSED", "reason": "USAGE"}), flush=True)
        return 2
    kind, instance = argv
    if kind == "record":
        path = Path(sp.JOB_ROOT) / instance / sp.RESULT_FILE
    else:
        path = Path(sp.DATA_ROOT) / sp.PRODUCTS_DIR / (".satdump-" + instance) / sp.UNIT_RESULT
    try:
        if kind == "record":
            import signal
            try:
                from . import labrx  # its one-shot stop handler: a stop runs the cleanup that sends branch OFF
            except ImportError:
                raise UnitRefused("RECORDER_RUNTIME_MISSING") from None
            for number in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
                signal.signal(number, labrx._stop)
        value = decode(instance) if kind == "decode" else record(instance)
    except (Exception, KeyboardInterrupt) as error:
        value = sp.result_value(kind, instance, "REFUSED", _code(error))
    try:
        write_result(path, value)
    except OSError:
        return 2
    return 0 if value["status"] in ("DECODED", "RECORDED") else 2


if __name__ == "__main__":
    raise SystemExit(main())
