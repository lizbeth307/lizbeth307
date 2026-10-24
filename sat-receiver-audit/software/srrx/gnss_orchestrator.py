"""labd's GNSS time orchestration around gnss_reset: a pure state machine, injected effects.

labd stays AF_UNIX only and the single I2C owner: this module never opens the UART,
gpsd or chrony. Its effects are four nonblocking requests (effects.invalidate,
effects.pps, effects.snapshot, effects.config) that return a handle polled from the
20 ms tick, and the engine's own policy-checked pulse. Nothing here blocks the tick:
the Pico heartbeat timeout is 750 ms (firmware/pico/supervisor.py).

Plans (build/07-pz-vstanovlennia.md:484-503, GNSS-UART.md "Служба місця навколо імпульсу"):
  boot    PPS noselect -> config + read-back -> qualified fix -> PPS select
  reset   locationd invalidate GNSS_RESET -> PPS noselect -> RTC/last-good stale
          -> 200 ms pulse (policy) -> release proven -> config (it waits for the first
          valid sentence, writes only on a mismatch, restarts the reader) -> qualified
          fix -> PPS select
  config  as boot, on operator request (labctl gnss_config)
No pulse without a confirmed PPS noselect. PPS select only after a matching read-back
and a qualified fix (3D, >= 6 satellites, no jamming flag) held for QUALIFY_MS. A
jamming flag at any time deselects PPS and latches JAMMED; leaving JAMMED takes an
operator reset or config (build/07:484). There is no automatic re-RESET, no retried
pulse and no escalation; the policy's 30 s spacing and 3 per 15 min still apply.
Status carries codes and booleans only, never coordinates.
"""
import json
from pathlib import Path
import socket
import subprocess
import time

from .gnss_config import RESULT_PATH as CONFIG_RESULT, UNIT as CONFIG_UNIT

LOCATION_SOCKET = "/run/srrx-loc/location.sock"
TIMEGATE_SOCKET = "/run/srrx-timegate/timegate.sock"
SYSTEMCTL = "/usr/bin/systemctl"
POLL_MS = 1000
QUALIFY_MS = 10000
RETRY_MS = 5000
RELEASE_TIMEOUT_MS = 2000      # 500 ms widest pulse, 1000 ms policy hard deadline, slack
CONFIG_TIMEOUT_MS = 150000     # srrx-gnss-config: 40 s first sentence + replies + reader restart
FIX_TIMEOUT_MS = 900000        # 15 min; chrony should select PPS within 10 min of a 3D fix (build/07:503)
PLANS = {"boot": ("noselect", "config", "await_fix", "select"),
         "reset": ("invalidate", "noselect", "stale", "pulse", "release", "config", "await_fix", "select"),
         "config": ("noselect", "config", "await_fix", "select")}
STEP_STATE = {"invalidate": "LOCATION_INVALIDATE", "noselect": "PPS_NOSELECT", "stale": "MARK_STALE",
              "pulse": "RESET_PULSE", "release": "RESET_RELEASE", "config": "GNSS_CONFIG",
              "await_fix": "AWAIT_FIX", "select": "PPS_SELECT", "jam_noselect": "PPS_NOSELECT_JAMMING"}
# A new operator plan may replace these; any other step is still running.
INTERRUPTIBLE = (None, "await_fix", "jam_noselect")


class Done:
    """An effect that finished when it was started (also every refused start)."""
    def __init__(self, result):
        self.result = result

    def poll(self, now_ms):
        return self.result

    def cancel(self):
        pass


class GnssOrchestrator:
    def __init__(self, effects, mode="gpsd"):
        if mode not in ("gpsd", "raw"):
            raise ValueError("orchestration needs --gnss gpsd or raw")
        self.effects, self.mode = effects, mode
        self.state, self.kind, self.step, self.plan = "STARTING", None, None, []
        self.step_ms = self.next_ms = self.pulse_ms = self.qualified_since = None
        self.job = None
        self.owner = self.value = None
        self.pps_selected = None   # unknown until a confirmed noselect or select
        self.rtc_stale = True      # nothing verified since this labd started
        self.jamming_seen = False
        self.last_error, self.warnings, self.events, self.config = None, [], [], None
        self.started = False

    # ------------------------------------------------------------ requests

    def busy(self):
        return self.step not in INTERRUPTIBLE

    def request_reset(self, owner, value, now_ms):
        if self.busy():
            return {"ok": False, "error": "GNSS_ORCHESTRATION_BUSY: " + self.state}
        self._begin("reset", now_ms, owner, value)
        return {"ok": True, "state": "ACCEPTED", "orchestration": "reset", "steps": list(PLANS["reset"])}

    def request_config(self, owner, now_ms):
        if self.busy():
            return {"ok": False, "error": "GNSS_ORCHESTRATION_BUSY: " + self.state}
        self._begin("config", now_ms, owner)
        return {"ok": True, "state": "ACCEPTED", "orchestration": "config", "steps": list(PLANS["config"])}

    def fault(self, code, now_ms):
        """An orchestration error: PPS is left as it is and nothing is retried."""
        self._finish("FAILED", now_ms, str(code)[:120])

    # ------------------------------------------------------------ machine

    def _event(self, now_ms, code):
        self.events = (self.events + [{"at_ms": now_ms, "event": code}])[-16:]

    def _cancel(self):
        if self.job is not None:
            self.job.cancel()
            self.job = None

    def _begin(self, kind, now_ms, owner=None, value=None):
        self._cancel()
        self.started = True  # an operator plan before the first tick replaces the boot plan
        self.kind, self.plan, self.owner, self.value = kind, list(PLANS[kind]), owner, value
        self.warnings, self.last_error, self.pulse_ms = [], None, None
        self._event(now_ms, kind.upper() + "_STARTED")
        self._next(now_ms)

    def _next(self, now_ms):
        self.step = self.plan.pop(0) if self.plan else None
        self.step_ms = self.next_ms = now_ms
        self.qualified_since = None
        if self.step is not None:
            self.state = STEP_STATE[self.step]

    def _finish(self, state, now_ms, error=None):
        self._cancel()
        self.plan, self.step, self.state = [], None, state
        if error is not None:
            self.last_error = error
        self._event(now_ms, error or state)
        self.next_ms = now_ms + POLL_MS

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

    def _jam(self, now_ms):
        self._cancel()
        self.jamming_seen = True
        self._event(now_ms, "GNSS_JAMMING_FLAG")
        self.plan, self.step, self.state = [], "jam_noselect", STEP_STATE["jam_noselect"]
        self.step_ms = self.next_ms = now_ms

    def tick(self, now_ms, reset_status, pulse):
        """Advance at most a few instantaneous steps; pulse(owner, value) is the engine's checked pulse."""
        if not self.started:
            self.started = True
            self._begin("boot", now_ms)
        for unused in range(8):
            if not self._step(now_ms, reset_status if isinstance(reset_status, dict) else {}, pulse):
                break
        if self.step is None and self.state == "SELECTED":
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
                # No reachable locationd means no consumer holds its positions; recorded, not fatal.
                self.warnings.append("LOCATION_INVALIDATE_FAILED")
            self._next(now)
            return True
        if step in ("noselect", "jam_noselect"):
            result = self._job(now, lambda: self.effects.pps(False, now))
            if result is None:
                return False
            if result.get("ok"):
                self.pps_selected = False
                if step == "jam_noselect":
                    self._finish("JAMMED", now, "GNSS_JAMMING")
                    return False
                self._next(now)
                return True
            self.pps_selected = None
            if step == "jam_noselect" or self.kind == "boot":
                # Keep trying: under jamming PPS must stop disciplining; at boot timegate may start later.
                self.last_error, self.next_ms = "PPS_NOSELECT_FAILED", now + RETRY_MS
                return False
            self._finish("FAILED", now, "PPS_NOSELECT_FAILED")  # no pulse without a confirmed noselect
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
                self.last_error = "GNSS_RESET_REFUSED: " + str(error)[:120]
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
                self._finish("FIX_TIMEOUT", now, "GNSS_FIX_TIMEOUT")
                return False
            snapshot = self._job(now, lambda: self.effects.snapshot(now))
            if snapshot is None:
                return False
            self.next_ms = now + POLL_MS
            data = snapshot.get("data") if snapshot.get("ok") else None
            if self._jammed(data):
                self._jam(now)
                return True
            if isinstance(data, dict) and data.get("qualified_fix") is True:
                if self.qualified_since is None:
                    self.qualified_since = now
                if now - self.qualified_since >= QUALIFY_MS:
                    self._next(now)
                    return True
            else:
                self.qualified_since = None  # any unqualified or missing sample restarts the window
            return False
        if step == "select":
            result = self._job(now, lambda: self.effects.pps(True, now))
            if result is None:
                return False
            if result.get("ok"):
                self.pps_selected, self.rtc_stale = True, False
                self._finish("SELECTED", now)
                return False
            self.last_error = "PPS_SELECT_FAILED"
            self.plan.insert(0, "select")
            self.step, self.state = "await_fix", STEP_STATE["await_fix"]
            self.step_ms, self.next_ms, self.qualified_since = now, now + RETRY_MS, None
            return False
        self._finish("FAILED", now, "GNSS_ORCHESTRATION_STEP")
        return False

    def _monitor(self, now):
        """SELECTED: poll for the jamming flag once a second."""
        if self.job is None and now < self.next_ms:
            return
        snapshot = self._job(now, lambda: self.effects.snapshot(now))
        if snapshot is None:
            return
        self.next_ms = now + POLL_MS
        if self._jammed(snapshot.get("data") if snapshot.get("ok") else None):
            self._jam(now)
            self._step(now, {}, None)

    def status(self):
        return {"enabled": True, "mode": self.mode, "state": self.state, "step": self.step,
                "plan": list(self.plan), "orchestration": self.kind, "pps_selected": self.pps_selected,
                "rtc_stale": self.rtc_stale, "time_trusted": self.pps_selected is True and not self.rtc_stale,
                "jamming_seen": self.jamming_seen, "qualified_since_ms": self.qualified_since,
                "last_error": self.last_error, "warnings": list(self.warnings), "config": self.config,
                "events": list(self.events), "automatic_reset": False}


# ---------------------------------------------------------------- Linux effects

def _reject_constant(value):
    raise ValueError("nonfinite JSON constant")


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
