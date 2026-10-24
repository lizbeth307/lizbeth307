"""labd's GNSS time orchestration around gnss_reset: a pure state machine, injected effects.

labd stays AF_UNIX only and the single I2C owner: this module never opens the UART,
gpsd or chrony. Its effects are four nonblocking requests (effects.invalidate,
effects.pps, effects.snapshot, effects.config) that return a handle polled from the
20 ms tick, the engine's own policy-checked pulse and a small latch file. Nothing here
blocks the tick: the Pico heartbeat timeout is 750 ms (firmware/pico/supervisor.py).

Plans (build/07-pz-vstanovlennia.md:484-503, GNSS-UART.md "Служба місця навколо імпульсу"):
  boot    PPS noselect -> config + read-back -> qualified fix -> PPS select
  reset   locationd invalidate GNSS_RESET -> PPS noselect -> RTC/last-good stale
          -> 200 ms pulse (policy) -> release proven -> config (it waits for the first
          valid sentence, writes only on a mismatch, restarts the reader) -> qualified
          fix -> PPS select
  config  as boot, on operator request (labctl gnss_config)
  watch   SELECTED without a fresh jamming report for WATCH_LOST_MS: PPS noselect ->
          qualified fix -> PPS select
No pulse without a confirmed PPS noselect. PPS select only after a matching read-back
and a qualified fix held for QUALIFY_MS: 3D, >= 6 satellites, no jamming flag and a
fresh "good" jamming report, the only sign that the receiver's jamming detection
reaches locationd at all. A jamming flag at any time deselects PPS and latches JAMMED.
After a jamming flag build/07:484 wants a cold restart and the settings again before
PPS is trusted: the latch survives labd restarts (JamLatchFile), the boot plan and
gnss_config never select PPS while it is set, and only a gnss_reset whose release is
proven clears it. Whenever PPS may still be selected, a failed noselect is retried every
RETRY_MS until confirmed (jamming, an orchestration fault, a failed operator plan).
In raw mode gpsd is stopped, chrony's NMEA SHM refclock gets no samples and its
'refclock PPS ... lock NMEA' drops every pulse, so the plans end in POSITION_ONLY
without a PPS select. There is no automatic re-RESET, no retried pulse and no
escalation; the policy's 30 s spacing and 3 per 15 min still apply. Status carries
codes and booleans only, never coordinates; pps_gate_open is labd's gate, not proof
that chrony selected PPS (chronyc -n sources / selectdata on the Q6A).
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import time

from .gnss_config import RESULT_PATH as CONFIG_RESULT, UNIT as CONFIG_UNIT

LOCATION_SOCKET = "/run/srrx-loc/location.sock"
TIMEGATE_SOCKET = "/run/srrx-timegate/timegate.sock"
LATCH_PATH = "/var/lib/srrx-gnss/jamming-latch.json"  # srrx.service StateDirectory=srrx-gnss
SYSTEMCTL = "/usr/bin/systemctl"
POLL_MS = 1000
QUALIFY_MS = 10000
RETRY_MS = 5000
JAMMING_FRESH_MS = 5000        # newest jamming report; its rate on LC76G firmware is a Q6A item
WATCH_LOST_MS = 5000           # SELECTED this long without a fresh "good" report -> watch plan
RELEASE_TIMEOUT_MS = 2000      # 500 ms widest pulse, 1000 ms policy hard deadline, slack
CONFIG_TIMEOUT_MS = 150000     # srrx-gnss-config: 40 s first sentence + replies + reader restart
FIX_TIMEOUT_MS = 900000        # 15 min; chrony should select PPS within 10 min of a 3D fix (build/07:502)
PLANS = {"boot": ("noselect", "config", "await_fix", "select"),
         "reset": ("invalidate", "noselect", "stale", "pulse", "release", "config", "await_fix", "select"),
         "config": ("noselect", "config", "await_fix", "select"),
         "watch": ("noselect", "await_fix", "select")}
STEP_STATE = {"invalidate": "LOCATION_INVALIDATE", "noselect": "PPS_NOSELECT", "stale": "MARK_STALE",
              "pulse": "RESET_PULSE", "release": "RESET_RELEASE", "config": "GNSS_CONFIG",
              "await_fix": "AWAIT_FIX", "select": "PPS_SELECT"}
# A new operator plan may replace these; any other step is still running. "deselect" is the
# retried noselect before a terminal state; every operator plan starts with its own noselect.
INTERRUPTIBLE = (None, "await_fix", "deselect")
# Their noselect retries until confirmed (timegate or chronyd may be missing), so it is replaceable too.
RETRYING_PLANS = ("boot", "watch")


class Done:
    """An effect that finished when it was started (also every refused start)."""
    def __init__(self, result):
        self.result = result

    def poll(self, now_ms):
        return self.result

    def cancel(self):
        pass


def _reject_constant(value):
    raise ValueError("nonfinite JSON constant")


class JamLatchFile:
    """The JAMMED latch across labd restarts: the file exists while a gnss_reset is required.

    load() fails closed: an unreadable or unexpected file, or a missing directory, means a
    reset is required. Written by an atomic rename without fsync, so the tick never waits
    for storage; a power loss that could drop the write also power-cycles the LC76G, which
    is itself the cold restart build/07:484 asks for.
    """
    RECORD = b'{"reset_required":true,"schema_version":1}\n'

    def __init__(self, path=LATCH_PATH):
        self.path = Path(path)

    def load(self):
        """(reset_required, code or None)."""
        try:
            with open(self.path, "rb") as handle:
                data = handle.read(4097)
        except FileNotFoundError:
            return (False, None) if self.path.parent.is_dir() else (True, "GNSS_JAM_LATCH_DIRECTORY_MISSING")
        except OSError:
            return True, "GNSS_JAM_LATCH_UNREADABLE"
        try:
            record = json.loads(data, parse_constant=_reject_constant) if len(data) <= 4096 else None
        except (ValueError, UnicodeError, RecursionError):
            record = None
        if isinstance(record, dict) and record.get("schema_version") == 1 and record.get("reset_required") is True:
            return True, None
        return True, "GNSS_JAM_LATCH_UNREADABLE"

    def store(self, required):
        """True when the file now says required."""
        try:
            if not required:
                self.path.unlink(missing_ok=True)
                return self.path.parent.is_dir()
            temporary = self.path.with_name(self.path.name + ".tmp")
            with open(temporary, "wb") as handle:  # in labd's own 0700 StateDirectory
                handle.write(self.RECORD)
            os.replace(temporary, self.path)
            return True
        except OSError:
            return False


class GnssOrchestrator:
    def __init__(self, effects, mode="gpsd", latch=None):
        if mode not in ("gpsd", "raw"):
            raise ValueError("orchestration needs --gnss gpsd or raw")
        self.effects, self.mode, self.latch = effects, mode, latch
        self.state, self.kind, self.step, self.plan, self.steps = "STARTING", None, None, [], []
        self.step_ms = self.next_ms = self.pulse_ms = self.qualified_since = self.watch_ms = None
        self.job = self.final = None
        self.owner = self.value = None
        self.pps_selected = None   # unknown until a confirmed noselect or select
        self.rtc_stale = True      # nothing verified since this labd started
        self.jamming_seen = False  # since this labd started
        self.jamming_active = self.jamming_visible = None  # from the newest snapshot
        # latch None (tests, simulation): in memory only.
        self.reset_required, self.latch_error = (False, None) if latch is None else latch.load()
        self.last_error, self.warnings, self.events, self.config = None, [], [], None
        self.started = False

    # ------------------------------------------------------------ requests

    def busy(self):
        if self.step in INTERRUPTIBLE:
            return False
        return not (self.step == "noselect" and self.kind in RETRYING_PLANS)

    def _busy_reply(self):
        detail = "" if self.last_error is None else " (" + self.last_error + ")"
        return {"ok": False, "error": "GNSS_ORCHESTRATION_BUSY: " + self.state + detail}

    def request_reset(self, owner, value, now_ms):
        if self.busy():
            return self._busy_reply()
        self._begin("reset", now_ms, owner, value)
        return {"ok": True, "state": "ACCEPTED", "orchestration": "reset", "steps": list(self.steps)}

    def request_config(self, owner, now_ms):
        if self.reset_required:
            return {"ok": False, "error": "GNSS_JAMMED_RESET_REQUIRED: after a jamming flag only gnss_reset "
                                          "(cold restart, then the settings again; build/07:484)"}
        if self.busy():
            return self._busy_reply()
        self._begin("config", now_ms, owner)
        return {"ok": True, "state": "ACCEPTED", "orchestration": "config", "steps": list(self.steps)}

    def fault(self, code, now_ms):
        """An orchestration error: nothing is retried except deselecting PPS that may still be selected."""
        error = str(code)[:120]
        if self.step == "deselect":
            # The retried noselect itself failed: keep its target state and try again later.
            self._cancel()
            self.last_error, self.next_ms = error, now_ms + RETRY_MS
            self._event(now_ms, error)
            return
        self._terminal("FAILED", now_ms, error)

    # ------------------------------------------------------------ machine

    def _event(self, now_ms, code):
        self.events = (self.events + [{"at_ms": now_ms, "event": code}])[-16:]

    def _cancel(self):
        if self.job is not None:
            self.job.cancel()
            self.job = None

    def _set_latch(self, required, now_ms):
        self.reset_required = required
        if self.latch is not None:
            self.latch_error = None if self.latch.store(required) else "GNSS_JAM_LATCH_STORE_FAILED"
        self._event(now_ms, "GNSS_JAM_LATCH_SET" if required else "GNSS_JAM_LATCH_CLEARED")

    def _begin(self, kind, now_ms, owner=None, value=None):
        self._cancel()
        self.started = True  # an operator plan before the first tick replaces the boot plan
        plan = list(PLANS[kind])
        if kind == "boot" and self.reset_required:
            plan = ["noselect", "latched"]  # no PPS before a proven reset (build/07:484)
        elif self.mode == "raw":
            plan = [step for step in plan if step not in ("await_fix", "select")] + ["position_only"]
        self.kind, self.plan, self.steps, self.owner, self.value = kind, plan, list(plan), owner, value
        self.warnings, self.last_error, self.pulse_ms, self.final = [], None, None, None
        if self.mode == "raw":
            self.warnings.append("RAW_MODE_NO_NMEA_SHM")
        self._event(now_ms, kind.upper() + "_STARTED")
        self._next(now_ms)

    def _next(self, now_ms):
        self.step = self.plan.pop(0) if self.plan else None
        self.step_ms = self.next_ms = now_ms
        self.qualified_since = None
        if self.step in STEP_STATE:
            self.state = STEP_STATE[self.step]

    def _finish(self, state, now_ms, error=None):
        self._cancel()
        self.plan, self.step, self.state, self.final = [], None, state, None
        if error is not None:
            self.last_error = error
        self._event(now_ms, error or state)
        self.next_ms = now_ms + POLL_MS

    def _terminal(self, state, now_ms, error=None, delay_ms=0, force=False):
        """End in state; PPS that may still be selected (or force) is deselected first."""
        if self.pps_selected is False and not force:
            self._finish(state, now_ms, error)
            return
        self._cancel()
        if error is not None:
            self.last_error = error
        self.final, self.plan, self.step = (state, error), [], "deselect"
        self.state = "PPS_NOSELECT_JAMMING" if state == "JAMMED" else "PPS_NOSELECT_FAULT"
        self.step_ms, self.next_ms = now_ms, now_ms + delay_ms
        self._event(now_ms, "PPS_DESELECT_BEFORE_" + state)

    def _job(self, now_ms, start):
        if self.job is None:
            self.job = start()
        result = self.job.poll(now_ms)
        if result is not None:
            self.job = None
            if not isinstance(result, dict):
                result = {"ok": False, "error": "EFFECT_RESULT_INVALID"}
        return result

    @staticmethod
    def _jammed(data):
        return isinstance(data, dict) and isinstance(data.get("jamming"), dict) and data["jamming"].get("active") is True

    @staticmethod
    def _verdict_good(data):
        """A fresh "good" (status 1) jamming report: the receiver's detection reaches locationd."""
        jamming = data.get("jamming") if isinstance(data, dict) else None
        if not isinstance(jamming, dict):
            return False
        status, reports, age = jamming.get("status"), jamming.get("reports"), jamming.get("age_ms")
        return (jamming.get("active") is False and type(status) is int and status == 1
                and type(reports) is int and reports > 0 and type(age) is int and 0 <= age <= JAMMING_FRESH_MS)

    def _observe(self, snapshot):
        """The snapshot's data (None if unusable); the jamming booleans go to the status."""
        data = snapshot.get("data") if snapshot.get("ok") is True else None
        if not isinstance(data, dict):
            self.jamming_active = self.jamming_visible = None
            return None
        jamming = data.get("jamming")
        self.jamming_active = jamming.get("active") is True if isinstance(jamming, dict) else None
        self.jamming_visible = self._verdict_good(data)
        return data

    def _jam(self, now_ms):
        self.jamming_seen = True
        self._event(now_ms, "GNSS_JAMMING_FLAG")
        if not self.reset_required:
            self._set_latch(True, now_ms)
        self._terminal("JAMMED", now_ms, "GNSS_JAMMING", force=True)

    def tick(self, now_ms, reset_status, pulse):
        """Advance at most a few instantaneous steps; pulse(owner, value) is the engine's checked pulse."""
        if not self.started:
            self.started = True
            self._begin("boot", now_ms)
        for unused in range(8):
            if not self._step(now_ms, reset_status if isinstance(reset_status, dict) else {}, pulse):
                break
        if self.step is None:
            self._monitor(now_ms)

    def _step(self, now, reset, pulse):
        step = self.step
        if step is None or (self.job is None and now < self.next_ms):
            return False
        if step == "invalidate":
            result = self._job(now, lambda: self.effects.invalidate("GNSS_RESET", now))
            if result is None:
                return False
            if not result.get("ok"):
                # Recorded, not fatal: other position holders (the HMI's own gpsd client) age out by themselves.
                self.warnings.append("LOCATION_INVALIDATE_FAILED")
            self._next(now)
            return True
        if step in ("noselect", "deselect"):
            result = self._job(now, lambda: self.effects.pps(False, now))
            if result is None:
                return False
            if result.get("ok"):
                self.pps_selected = False
                if step == "deselect":
                    self._finish(self.final[0], now, self.final[1])
                    return False
                if self.last_error == "PPS_NOSELECT_FAILED":
                    self.last_error = None  # a boot or watch retry succeeded
                self._next(now)
                return True
            known_off = self.pps_selected is False  # only labd's select step ever selects PPS
            if not known_off:
                self.pps_selected = None
            if step == "deselect" and known_off:
                self.warnings.append("PPS_NOSELECT_FAILED")
                self._finish(self.final[0], now, self.final[1])
                return False
            if step == "deselect" or self.kind in RETRYING_PLANS:
                # Keep trying: under jamming PPS must stop disciplining; at boot timegate may start later.
                self.last_error, self.next_ms = "PPS_NOSELECT_FAILED", now + RETRY_MS
                return False
            # An operator plan ends here, without a pulse (no pulse without a confirmed noselect).
            self._terminal("FAILED", now, "PPS_NOSELECT_FAILED", delay_ms=RETRY_MS)
            return False
        if step == "latched":
            self._finish("JAMMED", now, "GNSS_JAMMED_RESET_REQUIRED")
            return False
        if step == "position_only":
            self._finish("POSITION_ONLY", now)
            return False
        if step == "stale":
            self.rtc_stale = True
            self._event(now, "RTC_AND_LAST_GOOD_STALE")
            self._next(now)
            return True
        if step == "pulse":
            result = pulse(self.owner, self.value)
            if isinstance(result, dict) and result.get("ok"):
                self.pulse_ms = now
                self._event(now, "RESET_PULSE_ASSERTED")
            else:
                # Refused (e.g. spacing): the receiver was not reset; read back and reselect as a config plan.
                error = result.get("error") if isinstance(result, dict) else None
                self.warnings.append("GNSS_RESET_REFUSED")
                code = "GNSS_RESET_REFUSED: " + str(error)[:120]
                if self.reset_required:
                    self._finish("JAMMED", now, code)  # the latch still needs its cold restart
                    return False
                self.last_error = code
                if self.plan[:1] == ["release"]:
                    self.plan.pop(0)
            self._next(now)
            return True
        if step == "release":
            state, released = reset.get("state"), reset.get("release_ms")
            if state == "RELEASE_UNCONFIRMED":
                self._finish("FAILED", now, "GNSS_RESET_RELEASE_UNCONFIRMED")
                return False
            if state == "IDLE" and type(released) is int and released >= self.pulse_ms:
                self._event(now, "RESET_RELEASED")
                if self.reset_required:
                    self._set_latch(False, now)  # the cold restart happened; config sends the settings
                self._next(now)
                return True
            if now - self.step_ms > RELEASE_TIMEOUT_MS:
                self._finish("FAILED", now, "GNSS_RESET_RELEASE_TIMEOUT")
            return False
        if step == "config":
            if now - self.step_ms > CONFIG_TIMEOUT_MS:
                self._finish("FAILED", now, "GNSS_CONFIG_TIMEOUT")
                return False
            result = self._job(now, lambda: self.effects.config(now))
            if result is None:
                return False
            self.config = {key: result.get(key) for key in ("ok", "error", "readback_match", "wrote", "version")}
            if result.get("ok") is True and result.get("readback_match") is True:
                self._event(now, "GNSS_CONFIG_READBACK_MATCH")
                self._next(now)
                return True
            self._finish("FAILED", now, "GNSS_CONFIG_FAILED: " + str(result.get("error"))[:100])
            return False
        if step == "await_fix":
            if now - self.step_ms > FIX_TIMEOUT_MS:
                self._terminal("FIX_TIMEOUT", now, "GNSS_FIX_TIMEOUT")
                return False
            snapshot = self._job(now, lambda: self.effects.snapshot(now))
            if snapshot is None:
                return False
            self.next_ms = now + POLL_MS
            data = self._observe(snapshot)
            if self._jammed(data):
                self._jam(now)
                return True
            if isinstance(data, dict) and data.get("qualified_fix") is True and self.jamming_visible:
                if self.qualified_since is None:
                    self.qualified_since = now
                if now - self.qualified_since >= QUALIFY_MS:
                    self._next(now)
                    return True
            else:
                # Any unqualified or missing sample, or no fresh "good" jamming report, restarts the window.
                self.qualified_since = None
            return False
        if step == "select":
            result = self._job(now, lambda: self.effects.pps(True, now))
            if result is None:
                return False
            if result.get("ok"):
                self.pps_selected, self.rtc_stale, self.watch_ms = True, False, now
                if self.last_error == "PPS_SELECT_FAILED":
                    self.last_error = None
                self._finish("SELECTED", now)
                return False
            # Unknown: a timed-out request or a failed reselect may still have reached chronyd.
            self.pps_selected = None
            self.last_error = "PPS_SELECT_FAILED"
            self.plan.insert(0, "select")
            self.step, self.state = "await_fix", STEP_STATE["await_fix"]
            self.step_ms, self.next_ms, self.qualified_since = now, now + RETRY_MS, None
            return False
        self._terminal("FAILED", now, "GNSS_ORCHESTRATION_STEP")
        return False

    def _monitor(self, now):
        """No plan running: poll the jamming flag once a second; SELECTED also needs fresh "good" reports."""
        if self.job is None and now < self.next_ms:
            return
        snapshot = self._job(now, lambda: self.effects.snapshot(now))
        if snapshot is None:
            return
        self.next_ms = now + POLL_MS
        data = self._observe(snapshot)
        if self._jammed(data) and self.state != "JAMMED":
            self._jam(now)
            self._step(now, {}, None)
            return
        if self.state != "SELECTED":
            return
        if self.jamming_visible:
            self.watch_ms = now
        elif now - self.watch_ms > WATCH_LOST_MS:
            # Blind (locationd down, no snapshot, no jamming report): fail closed and requalify.
            self._begin("watch", now)
            self.warnings.append("JAMMING_WATCH_LOST")
            self._step(now, {}, None)

    def status(self):
        return {"enabled": True, "mode": self.mode, "state": self.state, "step": self.step,
                "plan": list(self.plan), "orchestration": self.kind, "pps_selected": self.pps_selected,
                "rtc_stale": self.rtc_stale,
                "pps_gate_open": self.state == "SELECTED" and self.pps_selected is True and not self.rtc_stale,
                "jamming_seen": self.jamming_seen, "jamming_active": self.jamming_active,
                "jamming_visible": self.jamming_visible, "reset_required": self.reset_required,
                "latch_error": self.latch_error, "qualified_since_ms": self.qualified_since,
                "last_error": self.last_error, "warnings": list(self.warnings), "config": self.config,
                "events": list(self.events), "automatic_reset": False}


# ---------------------------------------------------------------- Linux effects

class UnixLineRequest:
    """One request to an AF_UNIX stream server and its one JSON reply line, never blocking."""
    def __init__(self, path, payload, now_ms, timeout_ms, label):
        self.label, self.deadline = label, now_ms + timeout_ms
        self.tx, self.rx, self.result, self.sock = bytearray(payload), bytearray(), None, None
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.setblocking(False)
            self.sock.connect(path)
        except OSError:  # missing, refused or a full backlog (EAGAIN)
            self._done(label + "_UNREACHABLE")

    def _done(self, error=None, reply=None):
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        self.result = reply if error is None else {"ok": False, "error": error}
        return self.result

    def poll(self, now_ms):
        if self.result is not None:
            return self.result
        try:
            if self.tx:
                del self.tx[:self.sock.send(self.tx)]
            while not self.tx:
                block = self.sock.recv(4096)
                if not block:
                    return self._done(self.label + "_CLOSED")
                self.rx.extend(block)
                if b"\n" in self.rx:
                    try:
                        reply = json.loads(bytes(self.rx).split(b"\n", 1)[0], parse_constant=_reject_constant)
                    except (ValueError, UnicodeError, RecursionError):
                        return self._done(self.label + "_REPLY_INVALID")
                    return self._done(None if isinstance(reply, dict) else self.label + "_REPLY_INVALID", reply)
                if len(self.rx) > 65536:
                    return self._done(self.label + "_REPLY_TOO_LARGE")
        except (BlockingIOError, InterruptedError):
            pass
        except OSError:
            return self._done(self.label + "_IO_ERROR")
        if now_ms >= self.deadline:
            return self._done(self.label + "_TIMEOUT")
        return None

    def cancel(self):
        if self.result is None:
            self._done(self.label + "_CANCELLED")


def boottime_ms():
    clock = getattr(time, "CLOCK_BOOTTIME", None)
    return time.clock_gettime_ns(clock) // 1000000 if clock is not None else int(time.monotonic() * 1000)


def read_config_result(path):
    """The config unit's result.json, or None while it is absent or unreadable."""
    try:
        with open(path, "rb") as handle:
            data = handle.read(16385)
        result = json.loads(data, parse_constant=_reject_constant) if len(data) <= 16384 else None
    except (OSError, ValueError, UnicodeError):
        return None
    return result if isinstance(result, dict) and result.get("schema_version") == 1 else None


class ConfigRun:
    """`systemctl --no-block start` of the config unit, then the result.json of this run only.

    The unit removes its old result first and stamps CLOCK_BOOTTIME; a result that
    started before this request is the previous run's and is ignored.
    """
    def __init__(self, unit, result_path, now_ms, *, popen=subprocess.Popen, boottime=boottime_ms,
                 start_timeout_ms=10000):
        self.path, self.result, self.next_read = Path(result_path), None, now_ms
        self.deadline, self.requested = now_ms + start_timeout_ms, boottime()
        try:
            self.proc = popen([SYSTEMCTL, "--no-ask-password", "--no-block", "start", unit],
                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              close_fds=True)
        except OSError:
            self.proc, self.result = None, {"ok": False, "error": "GNSS_CONFIG_START_EXEC"}

    def poll(self, now_ms):
        if self.result is not None:
            return self.result
        if self.proc is not None:
            code = self.proc.poll()
            if code is None:
                if now_ms < self.deadline:
                    return None
                self.cancel()
                self.result = {"ok": False, "error": "GNSS_CONFIG_START_TIMEOUT"}
                return self.result
            self.proc = None
            if code != 0:  # polkit refusal or an unknown unit
                self.result = {"ok": False, "error": "GNSS_CONFIG_START_REFUSED"}
                return self.result
        if now_ms < self.next_read:
            return None
        self.next_read = now_ms + 250
        record = read_config_result(self.path)
        started, finished = (record or {}).get("started_boottime_ms"), (record or {}).get("finished_boottime_ms")
        if type(started) is not int or type(finished) is not int or started < self.requested:
            return None
        self.result = record
        return record

    def cancel(self):
        if self.proc is not None:
            try:
                self.proc.kill()
                self.proc.wait(timeout=.1)
            except (OSError, subprocess.SubprocessError):
                pass
            self.proc = None


class LinuxGnssEffects:
    def __init__(self, location_socket=LOCATION_SOCKET, timegate_socket=TIMEGATE_SOCKET,
                 config_unit=CONFIG_UNIT, config_result=CONFIG_RESULT):
        self.location_socket, self.timegate_socket = location_socket, timegate_socket
        self.config_unit, self.config_result = config_unit, config_result

    def _location(self, request, now_ms):
        payload = json.dumps(request, separators=(",", ":")).encode() + b"\n"
        return UnixLineRequest(self.location_socket, payload, now_ms, 2000, "LOCATIOND")

    def invalidate(self, reason, now_ms):
        return self._location({"op": "invalidate", "reason": reason}, now_ms)

    def snapshot(self, now_ms):
        return self._location({"op": "snapshot"}, now_ms)

    def pps(self, select, now_ms):
        # Two bounded chronyc calls in timegate (5 s each) plus slack.
        return UnixLineRequest(self.timegate_socket, b"PPS_SELECT\n" if select else b"PPS_NOSELECT\n",
                               now_ms, 12000, "TIMEGATE")

    def config(self, now_ms):
        return ConfigRun(self.config_unit, self.config_result, now_ms)
