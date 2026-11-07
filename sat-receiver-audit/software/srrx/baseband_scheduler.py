"""labd side of the v2.1 Meteor-M LRPT pass recording: one attended pass at a time (stdlib only).

labd never opens a receiver, never runs SatDump and never starts a transient unit. It starts and
stops two static, root-owned template units (software/systemd, text = srrx.satdump_pass.unit_text)
with `systemctl --no-block`, and the polkit rule from polkit_rule() lets the labd user start and
stop exactly their instances (systemd 255 gives a template start the polkit details unit and
verb, src/core/dbus-util.c:151-181; StartTransientUnit has none, src/core/dbus.c:1191-1193):

  srrx-baseband-record@lrpt-<16 hex>.service  labrx.run_baseband of one window as labd on RTL-A
  srrx-satdump-decode@lrpt-<16 hex>.service   SatDump file decode of that recording (srrx-satdump)

1. request() (labd op baseband_schedule) runs in labd's loop and only reads small files: the
   caller holds its own lease (the engine checks), UTC is verified (labd's utc_verified), the
   planner's current plan (pass_jobs.PassPlanner.current_plan) gives the windows through
   satdump_pass.select_windows with the accepted allowlist (norad_allowlist.load_accepted), the
   requested pass starts later than now + EARLY_START_S, and the storage binding, the RTL-A driver
   record and the installation record exist. Attended only: nothing is armed or switched here.
2. tick() decides; one worker thread runs every systemctl call, file write and store access in
   order (one queue: at most this thread and one systemctl child count against labd's
   TasksMax=8). At window start - EARLY_START_S (AOS-65 s) the record unit is started, only
   with verified UTC, the job owner's valid lease, ARM and EN_RTLA on. While it records, a lost
   lease, a DISARM, EN_RTLA off, lost UTC, a scope stop or a cancel stops the unit (labrx deletes
   the partial file on SIGTERM) and a store sweep removes what is left.
3. After the unit's result names the recording and not before LOS + MARGIN_S (LOS+60 s), the
   decode unit runs (satdump_pass.prepare_decode / finish_decode): the unit's PNGs are read, the
   baseband is deleted before they are published, the work tree is removed, and the baseband is
   deleted whatever the outcome.

Unattended scheduling (labd arming RTL-A itself) is not implemented: it is an open owner
decision (build/15 «Порядок»). Device timing (W-04/W-05, a real pass) stays OPEN; nothing here
is RF or hardware evidence. Status carries codes and pass identities, never paths or positions.
"""
from __future__ import annotations

import os
from pathlib import Path
import queue
import re
import secrets
import stat
import subprocess
import threading
import time

from . import baseband, satdump_pass as sp

LABD_USER = "labd"
POLKIT_RULE = "etc/polkit-1/rules.d/60-srrx-satdump.rules"
LABD_DROPIN = "etc/systemd/system/srrx.service.d/60-baseband-scheduler.conf"
ALLOWLIST_PATH = "/etc/srrx/orbit-allowlist.json"
ALLOWLIST_RECORD = "/etc/srrx/orbit-allowlist.acceptance.json"
PRODUCTS_ROOT = sp.DATA_ROOT + "/" + sp.PRODUCTS_DIR
UNIT_PATTERN = r"^srrx-(satdump-decode|baseband-record)@lrpt-[0-9a-f]{16}\.service$"
# labd publishes the PNGs itself (decoder_policy.satdump_publish keeps every sanitized image in memory, about
# total + 2 x largest at its peak) inside srrx.service MemoryMax=128M. A design bound on the PNG bytes of one
# pass: above it nothing is published (the baseband is still deleted), never an out-of-memory labd. The
# product size of a real pass is a bench measurement (build/15 «Baseband/IQ»).
LABD_PUBLISH_BUDGET_BYTES = 20 * 1024 * 1024
POLL_MS = 2000
START_GRACE_MS = 30_000  # a unit neither seen running nor with a result by then did not start
RECORD_OVERRUN_S = 120  # after the window end the record unit must have ended (its TimeoutStartSec= is longer)
DECODE_OVERRUN_S = sp.DECODE_UNIT_TIMEOUT_S + 120
SYSTEMCTL_TIMEOUT_S = 30
MAX_ENV_BYTES = 4096
REQUEST_KEYS = frozenset(("aos_utc", "center_hz", "symbol_rate"))
STATES = ("IDLE", "QUEUED", "RECORD_STARTING", "RECORDING", "RECORD_STOPPING", "DECODE_WAIT", "DECODE_STARTING",
          "DECODING", "DECODE_FINISHING", "DONE", "FAILED", "CANCELLED")
RUNNING_STATES = ("activating", "active", "deactivating", "reloading")
_SYSTEMCTL_ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "SYSTEMD_PAGER": "", "SYSTEMD_COLORS": "0"}
_WORK = re.compile(r"\.satdump-lrpt-[0-9a-f]{16}\Z")


class SchedulerRefused(ValueError):
    """Stable refusal code; never a path, a position or file contents."""


def polkit_rule():
    """/etc/polkit-1/rules.d/60-srrx-satdump.rules: labd may start and stop only the two templates' instances."""
    return ("// SR-RX: srrx.baseband_scheduler.polkit_rule(), staged by deployment/deploy.py stage.\n"
            "// The " + LABD_USER + " user may start and stop, and only start and stop, instances\n"
            "// srrx-satdump-decode@lrpt-<16 hex>.service and srrx-baseband-record@lrpt-<16 hex>.service.\n"
            "// Their User=, sandbox and ExecStart are fixed in root-owned template files; a transient unit\n"
            "// is never allowed (systemd gives StartTransientUnit no unit or verb details).\n"
            "// Any other action, verb, unit or user falls through to the default policy.\n"
            "polkit.addRule(function(action, subject) {\n"
            '    if (action.id == "org.freedesktop.systemd1.manage-units" &&\n'
            '            subject.user == "' + LABD_USER + '" &&\n'
            '            (action.lookup("verb") == "start" || action.lookup("verb") == "stop") &&\n'
            "            /" + UNIT_PATTERN + "/.test(action.lookup(\"unit\"))) {\n"
            "        return polkit.Result.YES;\n"
            "    }\n"
            "});\n")


def labd_dropin():
    """srrx.service.d/60-baseband-scheduler.conf: what labd needs to finish a decode, nothing else.

    Group srrx-satdump reads the decode unit's PNGs and removes its work tree (2770, setgid; a
    sysusers "m" line would make labd a member everywhere). ReadWritePaths=/data: labd deletes the
    baseband through a StorageGuard, which needs the whole /data mount writable (a nested bind is a
    foreign mount to it, satdump_pass.sweep_units); file modes still limit labd to the trees it owns.
    "-": a root without /data (the QEMU guest) still starts labd. A drop-in, not srrx.service itself:
    the guest's simulation and hardware smoke install only srrx.service and the release guard.
    """
    return ("# SR-RX: srrx.baseband_scheduler.labd_dropin(), staged by deployment/deploy.py stage.\n"
            "# labd reads the SatDump decode unit's PNGs, removes its work tree and deletes the baseband.\n"
            "[Service]\nSupplementaryGroups=" + sp.UNIT_USER + "\nReadWritePaths=-" + sp.DATA_ROOT + "\n")


def staged_files():
    """Relative rootfs path -> text, for deploy.stage."""
    return {POLKIT_RULE: polkit_rule(), LABD_DROPIN: labd_dropin()}


def _admin_file(path, limit):
    """Bytes of a root-owned regular file, not group/world writable, <= limit (no link followed)."""
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
                             | getattr(os, "O_CLOEXEC", 0))
    except OSError:
        return None
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            return None
        data = stream.read(limit + 1)
    return data if len(data) <= limit else None


def load_binding(path=sp.BASEBAND_ENV, reader=_admin_file):
    """(SRRX_BB_DEVICE, SRRX_BB_DRIVER_RECORD) of the administrator's /etc/srrx/baseband.env, or a refusal."""
    data = reader(path, MAX_ENV_BYTES)
    if data is None:
        raise SchedulerRefused("BASEBAND_STORAGE_UNBOUND")
    values = {}
    for line in data.decode("ascii", "replace").splitlines():
        if line.strip() and not line.startswith("#"):
            key, sep, value = line.partition("=")
            if not sep or key in values:
                raise SchedulerRefused("BASEBAND_STORAGE_UNBOUND")
            values[key] = value
    device, driver = values.get("SRRX_BB_DEVICE", ""), values.get("SRRX_BB_DRIVER_RECORD", "")
    if not re.fullmatch(r"/dev/disk/by-uuid/[A-Za-z0-9-]{1,64}", device):
        raise SchedulerRefused("BASEBAND_STORAGE_UNBOUND")
    if not re.fullmatch(r"/opt/srrx/[A-Za-z0-9_./-]{1,200}\.json", driver) or "/../" in driver or "/./" in driver:
        raise SchedulerRefused("RTLA_DRIVER_RECORD_UNBOUND")
    return device, driver


def installation_present(path=sp.INSTALLATION_PATH, reader=_admin_file):
    """Cheap check in labd's loop; the full installation validation runs before the decode (worker)."""
    if reader(path, 8192) is None:
        raise SchedulerRefused("BASEBAND_DECODER_UNAVAILABLE")


class Systemctl:
    """The three systemctl calls of the worker thread; each one child, bounded by SYSTEMCTL_TIMEOUT_S."""

    def _run(self, argv, capture=False):
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, env=dict(_SYSTEMCTL_ENV), cwd="/", close_fds=True)
        try:
            out, unused = process.communicate(timeout=SYSTEMCTL_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise
        return process.returncode, (out or b"")[:4096]

    def start(self, unit):
        """Queue the start (--no-block): polkit decides on unit and verb, the worker polls the state."""
        return self._run([sp.SYSTEMCTL, "--no-ask-password", "--quiet", "--no-block", "start", unit])[0]

    def stop(self, unit):
        return self._run([sp.SYSTEMCTL, "--no-ask-password", "--quiet", "--no-block", "stop", unit])[0]

    def show(self, unit):
        code, out = self._run([sp.SYSTEMCTL, "show", "--property=ActiveState", "--property=SubState", unit], capture=True)
        values = dict(line.split("=", 1) for line in out.decode("ascii", "replace").splitlines() if "=" in line)
        return {"ActiveState": values.get("ActiveState", "unknown"), "SubState": values.get("SubState", "unknown"),
                "exit": code}


def _default_store(device):
    from .storage import StorageGuard
    guard = StorageGuard(sp.DATA_ROOT, device)
    try:
        return baseband.BasebandStore(guard), guard.close
    except BaseException:
        guard.close()
        raise


def _daemon_thread(target):
    thread = threading.Thread(target=target, name="srrx-baseband-job", daemon=True)
    thread.start()
    return thread


class BasebandScheduler:
    """labd's attended pass recorder and decoder; see the module docstring. Thread-safe status."""

    def __init__(self, *, planner=None, utc_verified=None, systemctl=None, accepted_loader=None, binding_loader=None,
                 installation_check=None, installation_loader=None, store_factory=None, scope=None,
                 wall_clock=time.time, start_thread=None, job_root=sp.JOB_ROOT, products_root=PRODUCTS_ROOT,
                 work_root=None):
        from . import norad_allowlist
        from .scope_policy import ScopeLatch
        self.planner = planner
        self.utc_verified = utc_verified or (lambda: False)
        self.systemctl = systemctl or Systemctl()
        self.accepted_loader = accepted_loader or (lambda: norad_allowlist.load_accepted(ALLOWLIST_PATH, ALLOWLIST_RECORD))
        self.binding_loader = binding_loader or load_binding
        self.installation_check = installation_check or installation_present
        if installation_loader is None:
            from . import decoder_policy
            installation_loader = lambda: decoder_policy.load_satdump_installation(sp.INSTALLATION_PATH)  # noqa: E731
        self.installation_loader = installation_loader
        self.store_factory = store_factory or _default_store
        self.scope = scope if scope is not None else ScopeLatch()
        self.wall_clock, self.start_thread = wall_clock, start_thread or _daemon_thread
        self.job_root, self.products_root = str(job_root), Path(products_root)
        self.work_root = Path(work_root) if work_root is not None else None
        self._lock = threading.Lock()
        self._queue = queue.Queue()
        self._worker_running = False
        self._stale_tokens = []
        self._job = None
        self._last = None
        self._closed = False

    # ------------------------------------------------------------ requests (labd's loop)

    def request(self, value, owner, now_ms):
        """baseband_schedule {aos_utc, center_hz, symbol_rate}: queue one pass of the current plan."""
        try:
            job = self._new_job(value, owner, int(now_ms))
        except (SchedulerRefused, sp.PassRefused, baseband.BasebandRefused) as error:
            return {"ok": False, "error": str(error)}
        except (ValueError, OSError, TypeError, KeyError):
            return {"ok": False, "error": "BASEBAND_INTERNAL"}
        return {"ok": True, "state": job["state"], "job_id": job["id"], "aos_utc": job["window"]["aos_utc"]}

    def _new_job(self, value, owner, now_ms):
        if (type(value) is not dict or set(value) != REQUEST_KEYS or type(value["aos_utc"]) is not str
                or type(value["center_hz"]) is not int or type(value["symbol_rate"]) is not int
                or type(owner) is not str or not owner):
            raise SchedulerRefused("BASEBAND_BAD_REQUEST")
        with self._lock:
            if self._closed:
                raise SchedulerRefused("BASEBAND_CLOSED")
            if self._job is not None:
                raise SchedulerRefused("BASEBAND_BUSY")
        try:
            verified = self.utc_verified() is True
        except Exception:
            verified = False
        if not verified:
            raise SchedulerRefused("UTC_NOT_VERIFIED")
        current = self.planner.current_plan() if self.planner is not None else None
        if current is None:
            raise SchedulerRefused("NO_PLAN")
        try:
            accepted = self.accepted_loader()
        except (ValueError, OSError):
            raise SchedulerRefused("BASEBAND_ALLOWLIST_UNACCEPTED") from None
        selected = sp.select_windows(current["plan"], accepted, value["center_hz"], value["symbol_rate"])
        if selected["reason"]:
            raise SchedulerRefused(selected["reason"])
        windows = [item for item in selected["windows"] if item["aos_utc"] == value["aos_utc"]]
        if len(windows) != 1:
            raise SchedulerRefused("BASEBAND_NO_SUCH_PASS")
        window = baseband.validate_window(windows[0])
        if self.wall_clock() >= window["start_unix_s"] - baseband.EARLY_START_S:
            raise SchedulerRefused("BASEBAND_WINDOW_STARTED")
        self.binding_loader()
        self.installation_check()
        span = baseband.channel_span(window["center_hz"], window["symbol_rate"])
        if not self.scope.permits("record", span):
            raise SchedulerRefused("OUT_OF_SCOPE")
        job = {"id": "lrpt-" + secrets.token_hex(8), "owner": owner, "window": window, "span": span,
               "los_s": baseband._unix(window["los_utc"]), "plan_request_id": current["request_id"],
               "state": "QUEUED", "accepted_ms": now_ms, "pending": None, "started_ms": None, "polled_ms": None,
               "seen_running": False, "active": None, "result": None, "stop_reason": None, "error": None,
               "aborted": False, "cancel": False, "abort_token": None, "recording_id": None, "decode": None,
               "report": None}
        with self._lock:
            if self._closed or self._job is not None:
                raise SchedulerRefused("BASEBAND_BUSY")
            self._job = job
        return job

    def cancel(self, owner, now_ms, scope_stop=False):
        """baseband_cancel: any local operator may stop (de-energizing side); scope_stop also latches the span."""
        with self._lock:
            job = self._job
            if job is None:
                return {"ok": False, "error": "BASEBAND_IDLE"}
            job["cancel"] = True
            span = job["span"]
        if scope_stop:
            self.scope.stop(*span)  # runs the abort callback of a recording in progress
        return {"ok": True, "job_id": job["id"], "state": job["state"]}

    def status(self):
        with self._lock:
            job, last = self._job, self._last
            current = None if job is None else self._view(job)
        return {"enabled": True, "state": "IDLE" if job is None else job["state"], "job": current, "last": last,
                "attended_only": True, "live_decode": False}

    @staticmethod
    def _view(job):
        window = job["window"]
        return {"job_id": job["id"], "state": job["state"], "norad_id": window["norad_id"], "target": window["target"],
                "aos_utc": window["aos_utc"], "los_utc": window["los_utc"], "center_hz": window["center_hz"],
                "symbol_rate": window["symbol_rate"], "pipeline": window["pipeline"], "clipped": window["clipped"],
                "recording_id": job["recording_id"], "error": job["error"],
                "products": None if job["report"] is None else job["report"].get("images")}

    def close(self):
        with self._lock:
            self._closed = True
        self._queue.put(None)

    # ------------------------------------------------------------ decisions (labd's loop)

    def _hold_refusal(self, job, lease):
        """Why the record unit may not run now, or None: the attended conditions of the module docstring."""
        if job["cancel"]:
            return "CANCELLED"
        if job["aborted"]:
            return "OUT_OF_SCOPE"
        lease = lease if isinstance(lease, dict) else {}
        if lease.get("valid") is not True or lease.get("owner") != job["owner"]:
            return "LEASE_LOST" if job["state"] != "QUEUED" else "LEASE_NOT_HELD"
        if lease.get("armed") is not True:
            return "DISARMED"
        if lease.get("rtla_on") is not True:
            return "RTLA_OFF"
        try:
            if self.utc_verified() is not True:
                return "UTC_NOT_VERIFIED"
        except Exception:
            return "UTC_NOT_VERIFIED"
        return None

    def tick(self, now_ms, lease):
        """Advance the one job by at most one worker command; never blocks."""
        now_ms = int(now_ms)
        if self._stale_tokens:
            self._release_scope(None)
        with self._lock:
            job = self._job
            if job is None or job["pending"] is not None or self._closed:
                return
        now_s = self.wall_clock()
        state = job["state"]
        if state == "QUEUED":
            self._tick_queued(job, now_ms, now_s, lease)
        elif state in ("RECORD_STARTING", "RECORDING"):
            self._tick_recording(job, now_ms, now_s, lease)
        elif state == "RECORD_STOPPING":
            self._tick_stopping(job, now_ms)
        elif state == "DECODE_WAIT":
            if job["cancel"]:
                self._finish(job, "CANCELLED", "CANCELLED", cleanup=True)
            elif now_s >= max(job["window"]["end_unix_s"], job["los_s"] + baseband.MARGIN_S):
                from .decoder_policy import APT_SPAN_HZ
                if not self.scope.permits("decode", APT_SPAN_HZ):
                    self._finish(job, "FAILED", "OUT_OF_SCOPE", cleanup=True)
                else:
                    job["started_ms"] = now_ms
                    self._command(job, "DECODE_STARTING", self._op_decode_start, now_ms)
        elif state == "DECODING":
            self._tick_decoding(job, now_ms, now_s)

    def _tick_queued(self, job, now_ms, now_s, lease):
        window = job["window"]
        if job["cancel"]:
            self._finish(job, "CANCELLED", "CANCELLED")
        elif now_s > window["end_unix_s"]:
            self._finish(job, "FAILED", "WINDOW_MISSED")
        elif now_s >= window["start_unix_s"] - baseband.EARLY_START_S:
            refusal = self._hold_refusal(job, lease)
            if refusal is None and not self.scope.permits("record", job["span"]):
                refusal = "OUT_OF_SCOPE"
            if refusal is not None:
                self._finish(job, "FAILED", refusal)  # nothing was started
                return
            self.scope.retune(*job["span"])
            job["abort_token"] = self.scope.register_abort(lambda: job.update(aborted=True))
            job["started_ms"] = now_ms
            self._command(job, "RECORD_STARTING", self._op_start_record, now_ms)

    def _tick_recording(self, job, now_ms, now_s, lease):
        refusal = self._hold_refusal(job, lease)
        result = job["result"]
        if result is not None:
            # labrx checked the lease, ARM, EN_RTLA and UTC on every block, so a finished recording stands
            # even if the lease ends right after the window; a cancel or a scope stop discards it.
            if result["status"] == "RECORDED" and not job["cancel"] and not job["aborted"]:
                job["recording_id"] = result["recording_id"]
                job["result"], job["seen_running"], job["active"] = None, False, None
                self._release_scope(job)
                self._set(job, "DECODE_WAIT")
            else:
                self._finish(job, "FAILED", refusal or result["reason"], cleanup=True)
            return
        if refusal is None and now_s > job["window"]["end_unix_s"] + RECORD_OVERRUN_S:
            refusal = "RECORD_UNIT_OVERRUN"
        ended = job["seen_running"] and job["active"] not in RUNNING_STATES
        if refusal is None and (ended or (not job["seen_running"] and now_ms - job["started_ms"] > START_GRACE_MS)):
            refusal = "RECORD_UNIT_NO_RESULT" if ended else "RECORD_UNIT_NOT_STARTED"
        if refusal is not None:
            job["stop_reason"] = refusal
            self._command(job, "RECORD_STOPPING", self._op_stop_record, now_ms)
        elif job["polled_ms"] is None or now_ms - job["polled_ms"] >= POLL_MS:
            job["polled_ms"] = now_ms
            self._command(job, job["state"], lambda j: self._op_poll(j, "record"), now_ms)

    def _tick_stopping(self, job, now_ms):
        # Stopped: wait until the unit is seen ended (or never ran), then sweep and fail with the stop reason.
        if job["active"] not in RUNNING_STATES and job["polled_ms"] is not None and job["polled_ms"] >= job["stop_ms"]:
            self._finish(job, "FAILED", job["stop_reason"], cleanup=True)
        elif now_ms - job["stop_ms"] > START_GRACE_MS:
            self._finish(job, "FAILED", job["stop_reason"], cleanup=True)  # the sweep still removes a partial file
        elif job["polled_ms"] is None or now_ms - job["polled_ms"] >= POLL_MS // 2:
            job["polled_ms"] = now_ms
            self._command(job, "RECORD_STOPPING", lambda j: self._op_poll(j, "record"), now_ms)

    def _tick_decoding(self, job, now_ms, now_s):
        ended = job["seen_running"] and job["active"] not in RUNNING_STATES
        late = not job["seen_running"] and now_ms - job["started_ms"] > START_GRACE_MS
        overrun = now_ms - job["started_ms"] > DECODE_OVERRUN_S * 1000
        if job["result"] is not None or ended or late or overrun or job["cancel"]:
            stop = job["result"] is None and not ended
            self._command(job, "DECODE_FINISHING", lambda j: self._op_decode_finish(j, stop), now_ms)
        elif job["polled_ms"] is None or now_ms - job["polled_ms"] >= POLL_MS:
            job["polled_ms"] = now_ms
            self._command(job, "DECODING", lambda j: self._op_poll(j, "decode"), now_ms)

    # ------------------------------------------------------------ state changes

    def _set(self, job, state):
        with self._lock:
            job["state"] = state

    def _release_scope(self, job):
        """labd's loop only (the ScopeLatch is not thread-safe); the worker queues tokens in _stale_tokens."""
        with self._lock:
            tokens, self._stale_tokens = self._stale_tokens, []
            if job is not None and job["abort_token"] is not None:
                tokens.append(job["abort_token"])
                job["abort_token"] = None
        for token in tokens:
            self.scope.unregister_abort(token)

    def _wake(self):
        """Start the worker thread unless it runs; False when no thread could be started."""
        with self._lock:
            if self._worker_running:
                return True
            self._worker_running = True
        try:
            self.start_thread(self._work)
        except RuntimeError:  # e.g. TasksMax reached: no thread, so no job
            with self._lock:
                self._worker_running = False
            return False
        return True

    def _command(self, job, state, operation, now_ms):
        """Hand one operation to the worker; the job waits (pending) until it is done."""
        with self._lock:
            job["state"], job["pending"] = state, operation
            if state == "RECORD_STOPPING" and job.get("stop_ms") is None:
                job["stop_ms"], job["polled_ms"] = now_ms, None
        self._queue.put(job)
        if not self._wake():
            with self._lock:
                job["pending"] = None
            self._finish(job, "FAILED", "BASEBAND_WORKER_START_FAILED")

    def _finish(self, job, state, error, cleanup=False):
        """Terminal state (labd's loop). cleanup: the store sweep and the deletion of a recording (worker)."""
        self._release_scope(job)
        if cleanup:
            with self._lock:
                job["pending"] = lambda j: self._op_cleanup(j, state, error)
            self._queue.put(job)
            if self._wake():
                return
        self._terminal(job, state, error)

    def _terminal(self, job, state, error):
        """Labd's loop or the worker: the job ends; a still registered scope callback is dropped on the next tick."""
        with self._lock:
            job["state"], job["error"], job["pending"] = state, error, None
            if job["abort_token"] is not None:
                self._stale_tokens.append(job["abort_token"])
                job["abort_token"] = None
            self._last = dict(self._view(job), state=state, error=error)
            if self._job is job:
                self._job = None

    # ------------------------------------------------------------ worker thread

    def _work(self):
        while True:
            try:
                job = self._queue.get(timeout=5)
            except queue.Empty:
                with self._lock:
                    if self._job is None or self._closed:
                        self._worker_running = False
                        return
                continue
            if job is None:
                with self._lock:
                    self._worker_running = False
                return
            self._run(job)

    def drain(self):
        """Run every queued operation in the calling thread (tests; in labd the worker thread does this)."""
        while True:
            try:
                job = self._queue.get_nowait()
            except queue.Empty:
                return
            if job is not None:
                self._run(job)

    def _run(self, job):
        with self._lock:
            operation = job["pending"]
        if operation is None:
            return
        try:
            operation(job)
        except Exception:
            with self._lock:
                job["error"] = job["error"] or "BASEBAND_INTERNAL"
            if job["state"] not in ("DONE", "FAILED", "CANCELLED"):
                self._terminal(job, "FAILED", "BASEBAND_INTERNAL")
        finally:
            with self._lock:
                if job["pending"] is operation:
                    job["pending"] = None

    def _store(self):
        device, unused = self.binding_loader()
        return self.store_factory(device)

    def _op_start_record(self, job):
        self._remove_stale_work()
        unit = sp.unit_name(sp.RECORD_TEMPLATE, job["id"])
        try:
            sp.write_job(self.job_root, job["id"], sp.record_job(job["id"], job["window"]))
            code = self.systemctl.start(unit)
        except (OSError, ValueError, subprocess.SubprocessError):
            code = None
        if code != 0:
            sp.remove_job(self.job_root, job["id"])
            with self._lock:
                job["stop_reason"] = "RECORD_UNIT_START_FAILED"
            self._terminal(job, "FAILED", "RECORD_UNIT_START_FAILED")
            return
        self._set(job, "RECORDING")

    def _op_poll(self, job, kind):
        if kind == "record":
            unit = sp.unit_name(sp.RECORD_TEMPLATE, job["id"])
            path = Path(self.job_root) / job["id"] / sp.RESULT_FILE
            instance = job["id"]
        else:
            rid = job["recording_id"]
            unit = sp.unit_name(sp.DECODE_TEMPLATE, rid)
            path = Path(job["decode"]["work"]) / sp.UNIT_RESULT
            instance = rid
        try:
            shown = self.systemctl.show(unit)
            active = shown["ActiveState"]
        except (OSError, ValueError, subprocess.SubprocessError):
            active = "unknown"
        try:
            result = sp.read_result(path, kind, instance)
        except sp.PassRefused:
            result = sp.result_value(kind, instance, "REFUSED", "UNIT_RESULT_INVALID")
        with self._lock:
            job["active"] = active
            job["seen_running"] = job["seen_running"] or active in RUNNING_STATES
            if result is not None and job["result"] is None:
                job["result"] = result

    def _op_stop_record(self, job):
        try:
            self.systemctl.stop(sp.unit_name(sp.RECORD_TEMPLATE, job["id"]))
        except (OSError, ValueError, subprocess.SubprocessError):
            pass  # the poll and the sweep below still run; the unit's own bounds end it

    def _op_cleanup(self, job, state, error):
        """Sweep (incomplete files), delete a finished recording of this job, remove the job directory."""
        try:
            store, close = self._store()
            try:
                result = job["result"]
                for rid in {job["recording_id"], result.get("recording_id") if result else None} - {None}:
                    store.delete(rid)
                store.sweep()
            finally:
                close()
        except Exception:
            pass  # the sweep unit (srrx-baseband-sweep.timer) and the 24 h rule remain
        sp.remove_job(self.job_root, job["id"])
        self._terminal(job, state, error)

    def _op_decode_start(self, job):
        sp.remove_job(self.job_root, job["id"])  # the record job is over
        rid = job["recording_id"]
        try:
            store, close = self._store()
        except Exception:
            self._terminal(job, "FAILED", "BASEBAND_STORAGE_UNAVAILABLE")  # the sweep removes it within 24 h
            return
        try:
            prepared = None
            try:
                installation = self.installation_loader()
                prepared = sp.prepare_decode(store, rid, installation, self.products_root, work_root=self.work_root,
                                             job_root=self.job_root)
            except Exception as error:
                store.delete(rid)
                self._terminal(job, "FAILED", _code(error))
                return
            try:
                code = self.systemctl.start(prepared["unit"])
            except (OSError, ValueError, subprocess.SubprocessError):
                code = None
            if code != 0:
                try:
                    sp.finish_decode(store, prepared)  # no result: refused, the baseband deleted
                except Exception:
                    pass
                self._terminal(job, "FAILED", "DECODE_UNIT_START_FAILED")
                return
            with self._lock:
                job["decode"], job["result"], job["seen_running"], job["active"] = prepared, None, False, None
                job["polled_ms"] = None
                job["state"] = "DECODING"
        finally:
            close()

    def _op_decode_finish(self, job, stop):
        if stop:
            try:
                self.systemctl.stop(job["decode"]["unit"])
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
        try:
            store, close = self._store()
        except Exception:
            self._terminal(job, "FAILED", "BASEBAND_STORAGE_UNAVAILABLE")
            return
        try:
            report = sp.finish_decode(store, job["decode"], publish_budget=LABD_PUBLISH_BUDGET_BYTES)
        except Exception as error:
            self._terminal(job, "FAILED", "CANCELLED" if job["cancel"] and job["result"] is None else _code(error))
            return
        finally:
            close()
        with self._lock:
            job["report"] = {"images": len(report.get("images") or ()) if isinstance(report, dict) else None}
        self._terminal(job, "DONE", None)

    def _remove_stale_work(self):
        """Work trees of decodes a previous labd left behind (a restart ends the job, not the unit)."""
        root = self.work_root or self.products_root
        try:
            entries = [entry for entry in os.scandir(root) if _WORK.match(entry.name)
                       and entry.is_dir(follow_symlinks=False)][:64]
        except OSError:
            return
        for entry in entries:
            try:
                sp._remove_tree(entry.path)
            except OSError:
                pass


def _code(error):
    text = str(error)
    if isinstance(error, ValueError) and re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", text):
        return text
    return "BASEBAND_" + type(error).__name__.upper()[:40]
