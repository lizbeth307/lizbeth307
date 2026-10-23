"""Optional local touch console. All power operations go through labd only."""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
from pathlib import Path
import queue
import selectors
import subprocess
import sys
import tempfile
import threading
import time
import uuid

EN_OUTPUTS = tuple("EN_" + name for name in (
    "LNA1", "LNA2", "LNA3", "LNA4", "LNB", "BONI", "SB_LNA", "RTLA",
    "RTLB", "HFP", "LIME3V3", "T7", "LABPORT", "AUX12"))
RECEIVERS = ("RTLA", "RTLB", "LIME")
ROUTES = ("PARK", "RF1", "RF2", "RF3", "RF4")
CONFIRMATIONS = ("bench_loads", "boni_connected", "boni_profile")
LABELS = ("unknown_energy", "analog_broadcast", "digital_broadcast",
          "weather_satellite", "amateur_digital", "voice_spectrogram")
MAX_FILE_BYTES = 2 * 1024 * 1024
PRODUCT_LABELS = {
    "LNA1": "LNA 1", "LNA2": "LNA 2", "LNA3": "LNA 3", "LNA4": "LNA 4",
    "LNB": "LNB supply", "BONI": "HF bias (Boni)", "SB_LNA": "S-band LNA",
    "RTLA": "RTL-A receiver", "RTLB": "RTL-B receiver", "HFP": "HF+ receiver",
    "LIME3V3": "Lime receiver", "T7": "Recorder storage", "LABPORT": "Lab USB", "AUX12": "Auxiliary 12 V",
}
CLASS_LABELS = {"unknown_energy": "Unknown energy", "analog_broadcast": "Analog broadcast",
                "digital_broadcast": "Digital broadcast", "weather_satellite": "Weather satellite",
                "amateur_digital": "Amateur digital", "voice_spectrogram": "Voice spectrogram"}
CHANNEL_DISPLAY_ORDER = ("RTLA", "RTLB", "HFP", "LIME3V3", "LNA1", "LNA2", "LNA3", "LNA4",
                         "LNB", "BONI", "SB_LNA", "T7", "LABPORT", "AUX12")


def readable_fault(value):
    if not value:
        return "No protection fault reported"
    return {"new_pico_session": "Stopped — ready for an explicit start",
            "operator_disarm": "Stopped by operator",
            "operator_shutdown": "Shutdown requested"}.get(str(value), str(value).replace("_", " ")[:240])


def channel_rows(data, live):
    policy = data.get("policy", {})
    outputs, observations = policy.get("outputs", {}), policy.get("branch_observability", {})
    if not isinstance(observations, dict):
        observations = {}
    rows = []
    for branch in CHANNEL_DISPLAY_ORDER:
        name = "EN_" + branch
        value = outputs.get(name)
        power = ("ON" if value else "OFF") if live and type(value) is bool else "Unknown"
        route = "—"
        receiver = {"RTLA": "RTLA", "RTLB": "RTLB", "LIME3V3": "LIME"}.get(branch)
        if live and receiver:
            a, b = outputs.get("SW_" + receiver + "_A"), outputs.get("SW_" + receiver + "_B")
            route = {(False, False): "PARK / RF1", (True, False): "RF2", (False, True): "RF3", (True, True): "RF4"}.get((a, b), "Unknown")
        elif live and branch == "HFP":
            route = {(False, False): "PARK", (True, False): "HF", (False, True): "VHF"}.get((outputs.get("K1_ON"), outputs.get("K2_ON")), "Unknown")
        observation = observations.get(branch, {})
        if not isinstance(observation, dict):
            observation = {}
        reserve = observation.get("reservation_a")
        reserved = f"{reserve * 1000:.0f} mA" if live and _finite(reserve) and reserve >= 0 else "Not set" if live else "Unknown"
        current = "Not measured" if observation.get("current_unknown") is True else "Not reported"
        rows.append((PRODUCT_LABELS[branch], power, route, current if live else "Unknown", reserved))
    return rows


def location_summary(value, live=False):
    source = value.get("source", "none")
    available = (value.get("available") is True and _finite(value.get("lat")) and -90 <= value["lat"] <= 90
                 and _finite(value.get("lon")) and -180 <= value["lon"] <= 180)
    if available:
        lat, lon = value["lat"], value["lon"]
        position = f"{abs(lat):.6f}° {'N' if lat >= 0 else 'S'}   {abs(lon):.6f}° {'E' if lon >= 0 else 'W'}"
    else:
        position = "No position available"
    source_label = {"gpsd": "GNSS (gpsd)", "nmea": "GNSS (serial)", "manual": "Manual entry",
                    "last_good": "Last known position", "none": "No source"}.get(source, "Unrecognised source")
    fix = ("Live GNSS fix" if live and value.get("fresh") is True and value.get("live_fix") is True
           else "Manual — not a GNSS fix" if source == "manual"
           else "No live fix" if not available else "Saved position — no live fix")
    age = value.get("age_ms")
    age_text = f"{age / 1000:.1f} s" if _finite(age) and age >= 0 else "Unknown"
    uncertainty = value.get("uncertainty_m")
    uncertainty_text = (f"±{uncertainty:.1f} m · confidence unspecified" if _finite(uncertainty) and uncertainty >= 0
                        else "Unknown — no accuracy estimate")
    return {"position": position, "source": source_label + (" · snapshot" if not live and source != "manual" else ""),
            "fix": fix, "age": age_text, "uncertainty": uncertainty_text}


def learning_summary(value, operation, model=None):
    if operation == "infer":
        label = value.get("label", "unknown_energy")
        title = "UNKNOWN — no accepted class match" if label == "unknown_energy" else CLASS_LABELS.get(label, "Unknown class")
        score = value.get("confidence")
        lines = [title, "", f"Heuristic score: {score:.2f} / 1 (not a probability)" if _finite(score) else "Heuristic score unavailable"]
        if label == "unknown_energy" and value.get("nearest_label"):
            lines.append("Closest example: " + CLASS_LABELS.get(value["nearest_label"], "Unknown") + " — not accepted")
        backend = value.get("backend", "CPU")
        npu = value.get("npu", {})
        reason = "not requested" if npu.get("reason") == "not_requested" else "unavailable or not qualified"
        lines.append("Processing: " + backend + (" · NPU " + reason if npu.get("available") is not True else " · qualified accelerator active"))
        lines.append("Capture: " + str(value.get("source", "Unknown")))
    elif operation in ("train", "model"):
        model = value
        lines = ["Model ready", "", "Categories: " + ", ".join(CLASS_LABELS.get(label, label) for label in model.get("labels", []))]
    else:
        records = value.get("annotations", [])
        groups = {record.get("group_sha256") for record in records}
        return f"Dataset ready\n\n{len(records)} confirmed annotations\n{len(value.get('frames', {}))} spectrum frames\n{len(groups)} independent capture groups\n\nCollect separate sessions before training."
    if isinstance(model, dict):
        provenance, validation = model.get("provenance", {}), model.get("validation", {})
        lines.extend(["", f"Training groups: {len(provenance.get('train_groups', []))}",
                      f"Held-out groups: {len(provenance.get('validation_groups', []))}"])
        accuracy = validation.get("accuracy")
        if _finite(accuracy):
            lines.append(f"Held-out check: {accuracy * 100:.1f}% of {validation.get('samples', 0)} examples · not field accuracy")
        sources = provenance.get("source_counts", {})
        if sources.get("SIMULATION", 0):
            lines.append("Includes simulated training examples")
    return "\n".join(lines)


def _child_environment():
    environment = dict(os.environ)
    package_root = str(Path(__file__).resolve().parent.parent)
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = package_root + (os.pathsep + existing if existing else "")
    return environment


class ServiceError(OSError):
    pass


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _no_constant(value):
    raise ValueError("Non-finite JSON is forbidden")


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON key")
        value[key] = item
    return value


def _json(text):
    try:
        return json.loads(text, parse_constant=_no_constant, object_pairs_hook=_unique)
    except RecursionError as error:
        raise ValueError("JSON nesting too deep") from error


def load_json(path):
    with open(path, "rb") as source:
        data = source.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("File exceeds the 2 MiB console limit")
    return _json(data.decode("utf-8"))


def load_spectrum(path):
    """Load a bounded JSON frame or the last nonblank JSONL survey record."""
    with open(path, "rb") as source:
        data = source.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("Use a survey excerpt of at most 2 MiB")
    text = data.decode("utf-8")
    try:
        frame = _json(text)
    except json.JSONDecodeError:
        lines = text.splitlines()
        if not lines or any(len(line) > MAX_FILE_BYTES for line in lines):
            raise ValueError("Invalid spectrum JSONL")
        frame = _json(next((line for line in reversed(lines) if line.strip()), ""))
    from .spectrum import mask_frame
    return mask_frame(frame)


def spectrum_columns(frame, columns=512):
    """Coarsen only fully valid groups; a masked bin makes its whole pixel blank."""
    if type(columns) is not int or not 1 <= columns <= 1024:
        raise ValueError("Invalid display width")
    from .spectrum import mask_frame
    safe = mask_frame(frame)
    size = safe["fft_size"]
    width = min(size, columns)
    result = []
    for index in range(width):
        start, end = index * size // width, (index + 1) * size // width
        valid = safe["valid"][start:end]
        values = safe["power_dbfs"][start:end]
        result.append(max(values) if all(valid) and all(value is not None for value in values) else None)
    return result


class HMINavigation:
    """Baseline bounded physical counter snapshots; output UI gestures only."""
    NAMES = ("home", "back", "rec_note", "mark", "next_page", "lock", "focus_next", "focus_prev")

    def __init__(self):
        self.reset()

    def reset(self):
        self.session = self.sequence = self.presses = self.encoders = None
        self.generation = None

    def consume(self, snapshot, session):
        empty = {"events": [], "encoders": [0, 0], "lux": None}
        if (not isinstance(snapshot, dict) or snapshot.get("ok") is not True or snapshot.get("fresh") is not True
                or type(snapshot.get("age_ms")) is not int or not 0 <= snapshot["age_ms"] < 500
                or type(session) is not int or not 0 <= session <= 0xffffffff):
            self.reset()
            return empty
        presses, encoders, sequence = snapshot.get("presses"), snapshot.get("encoders"), snapshot.get("sequence")
        generation = snapshot.get("generation")
        if (not isinstance(presses, list) or len(presses) != 8
                or any(type(v) is not int or not 0 <= v <= 65535 for v in presses)
                or not isinstance(encoders, list) or len(encoders) != 2
                or any(type(v) is not int or not -2147483648 <= v <= 2147483647 for v in encoders)
                or type(sequence) is not int or not 0 <= sequence <= 0xffffffff
                or type(generation) is not int or not 0 <= generation <= 65535
                or type(snapshot.get("keys")) is not int or not 0 <= snapshot["keys"] <= 255):
            self.reset()
            return empty
        if (snapshot.get("lux_valid") is True and _finite(snapshot.get("lux")) and 0 <= snapshot["lux"] <= 200000
                and type(snapshot.get("lux_age_ms")) is int and 0 <= snapshot["lux_age_ms"] < 2000):
            empty["lux"] = snapshot["lux"]
        baseline = self.session != session or self.generation != generation or self.sequence is None
        if not baseline and sequence < self.sequence:
            return empty  # Delayed Qt/status delivery must never replay old counters.
        if not baseline and sequence == self.sequence:
            return empty
        if baseline:
            delta, turns = [0] * 8, [0] * 2
        else:
            delta = [(new - old) & 65535 for new, old in zip(presses, self.presses)]
            turns = [((new - old + 2147483648) & 0xffffffff) - 2147483648
                     for new, old in zip(encoders, self.encoders)]
        self.session, self.sequence, self.generation = session, sequence, generation
        self.presses, self.encoders = list(presses), list(encoders)
        if any(v > 4 for v in delta) or any(abs(v) > 16 for v in turns):
            return empty  # Rebaseline implausible jumps; never replay a queue.
        empty["events"] = [name for name, count in zip(self.NAMES, delta) for _ in range(count)]
        empty["encoders"] = turns
        return empty


class ConsoleController:
    """Headless, single-thread controller. transport(request) returns labd JSON.

    poll() owns renewal. A rejected/failed renewal, stale poll or latched fault
    stops HOLD and attempts disarm. No poll, reconnect or status can arm.
    """
    def __init__(self, transport, clock=None):
        self.transport = transport
        self.clock = clock or time.monotonic
        self.snapshot = {}
        self.connected = False
        self.last_poll = None
        self.holding = False
        self.last_renew = None
        self.arm_started = None
        self.arm_fault = None
        self.bench_confirmed = False
        self.confirmed = dict.fromkeys(CONFIRMATIONS, False)
        self.error = None
        self.link_error = None
        self.notice = "DISARMED — explicit ARM + HOLD is required"
        self.closed = False
        self._last_time = None

    def _now(self):
        now = self.clock()
        if not _finite(now) or now < 0 or self._last_time is not None and now < self._last_time:
            raise ValueError("Invalid/backwards monotonic clock")
        self._last_time = now
        return now

    def _request(self, request):
        try:
            result = self.transport(copy.deepcopy(request))
        except (OSError, ValueError, TypeError, RuntimeError) as error:
            raise ServiceError(str(error)) from error
        if not isinstance(result, dict) or type(result.get("ok")) is not bool:
            raise ServiceError("Malformed labd response")
        return result

    def _stop(self, reason, send=True):
        self.holding = False
        self.arm_started = None
        self.last_renew = None
        self.bench_confirmed = False
        self.confirmed = dict.fromkeys(CONFIRMATIONS, False)
        self.notice = str(reason)[:240]
        if send:
            try:
                result = self._request({"op": "disarm"})
                if not result["ok"]:
                    self.error = "Disarm unconfirmed: " + str(result.get("error", "rejected"))[:180]
            except (OSError, ValueError, TypeError, RuntimeError) as error:
                self.error = "Disarm unconfirmed; lease will expire: " + str(error)[:150]
        return {"ok": self.error is None, "message": self.notice}

    @staticmethod
    def _validate_status(value):
        if (not isinstance(value, dict) or value.get("mode") not in ("SIMULATION", "HARDWARE")
                or not isinstance(value.get("policy"), dict) or not isinstance(value.get("pico"), dict)):
            raise ValueError("Invalid status shape")
        policy = value["policy"]
        if (type(policy.get("armed")) is not bool or policy.get("mode") not in ("field", "lab")
                or policy.get("fault") is not None and not isinstance(policy["fault"], str)
                or not isinstance(policy.get("outputs"), dict)
                or any(type(v) is not bool for v in policy["outputs"].values())):
            raise ValueError("Invalid policy status")
        # Reject nested non-finite/oversized data even for injected transports.
        if len(json.dumps(value, allow_nan=False).encode()) > 65536:
            raise ValueError("Oversize status")
        return copy.deepcopy(value)

    def status(self):
        now = self.clock()
        age = now - self.last_poll if self.last_poll is not None and _finite(now) else float("inf")
        fresh = self.connected and 0 <= age <= 1.5
        snapshot = copy.deepcopy(self.snapshot)
        imu = snapshot.get("imu")
        if isinstance(imu, dict) and imu.get("ok") is True:
            source_age = imu.get("age_ms")
            effective_age = source_age + int(max(0, age) * 1000) if fresh and type(source_age) is int else 500
            if effective_age >= 500:
                snapshot["imu"] = {"ok": False, "fresh": False, "quaternion": None, "error": "HMI_IMU_STALE"}
            else:
                imu["age_ms"] = effective_age
        hmi = snapshot.get("hmi")
        if isinstance(hmi, dict) and hmi.get("ok") is True:
            source_age = hmi.get("age_ms")
            effective_age = source_age + int(max(0, age) * 1000) if fresh and type(source_age) is int else 500
            if effective_age >= 500:
                snapshot["hmi"] = {"ok": False, "fresh": False, "error": "HMI_INPUT_STALE"}
            else:
                hmi["age_ms"] = effective_age
                if type(hmi.get("lux_age_ms")) is int:
                    hmi["lux_age_ms"] += int(max(0, age) * 1000)
                    if hmi["lux_age_ms"] >= 2000:
                        hmi.update(lux=None, lux_valid=False)
        return {"connected": fresh, "stale": not fresh, "holding": self.holding and fresh,
                "arming": self.arm_started is not None, "error": self.error, "notice": self.notice,
                "bench_confirmed": self.bench_confirmed, "confirmations": dict(self.confirmed), "data": snapshot}

    def _renew(self, now):
        if self.last_renew is None or now - self.last_renew >= 1.0:
            result = self._request({"op": "lease", "value": {"ttl_ms": 3000}})
            if not result["ok"]:
                self.error = str(result.get("error", "Lease rejected"))[:200]
                self._stop("Lease rejected — explicit recovery is required")
                return False
            self.last_renew = now
        return True

    def poll(self):
        if self.closed:
            return self.status()
        try:
            now = self._now()
            if self.holding and self.last_poll is not None and now - self.last_poll > 1.5:
                self.error = "UI/service polling gap exceeded 1.5 s"
                self._stop("Polling stalled — HOLD stopped")
            result = self._request({"op": "status"})
            if not result["ok"]:
                raise ValueError(str(result.get("error", "Status rejected")))
            self.snapshot = self._validate_status(result.get("data"))
            self.connected, self.last_poll = True, now
            policy, pico = self.snapshot["policy"], self.snapshot["pico"]
            if self.link_error is not None and not self.holding and not policy["armed"]:
                # Fresh status shows labd disarmed; clear only the error the link loss set.
                if self.error == self.link_error:
                    self.error = None
                self.link_error = None
            if self.holding:
                if self.arm_started is not None:
                    if policy["armed"] and not policy.get("fault") and pico.get("state") == "ACTIVE":
                        self.arm_started = None
                        self.notice = "ACTIVE — HOLD lease renewed every second"
                    elif now - self.arm_started >= 2.5 or pico.get("state") in ("OFF", "SHUTTING_DOWN"):
                        self.error = "ARM handshake did not complete"
                        self._stop("ARM failed — outputs requested OFF")
                    elif policy.get("fault") and policy["fault"] != self.arm_fault:
                        self.error = policy["fault"]
                        self._stop("New fault during ARM — HOLD stopped")
                    elif self.snapshot.get("last_error"):
                        # labd keeps the first fault; ARM clears last_error and any trip sets it.
                        self.error = str(self.snapshot["last_error"])[:200]
                        self._stop("ARM aborted by labd — HOLD stopped")
                elif policy.get("fault") or not policy["armed"] or pico.get("state") != "ACTIVE":
                    self.error = str(policy.get("fault") or self.snapshot.get("last_error") or "Supervisor permission lost")[:200]
                    self._stop("FAULT — HOLD stopped; no automatic re-arm")
                if self.holding:
                    self._renew(now)
            return self.status()
        except (OSError, ValueError, TypeError, RuntimeError) as error:
            was_holding = self.holding
            self.connected = False
            self.error = str(error)[:240]
            self._stop("Service timeout/error — HOLD stopped", send=was_holding)
            self.link_error = self.error
            return self.status()

    def _ready(self, active=False):
        view = self.status()
        if not view["connected"]:
            raise ValueError("Fresh labd status is required")
        if active:
            policy = self.snapshot["policy"]
            if (not self.holding or not policy["armed"] or policy.get("fault")
                    or self.snapshot["pico"].get("state") != "ACTIVE"):
                raise ValueError("Explicit ARM + HOLD and ACTIVE are required")

    def command(self, operation, **fields):
        """Only semantic labd operations; raw GPIO, sim and OFF_NOW are absent."""
        if self.closed:
            return {"ok": False, "error": "Console is closed"}
        try:
            now = self._now()
            required = {"arm": set(), "recover": set(), "disarm": set(), "shutdown": set(),
                        "control": {"name", "value"}, "mode": {"value"}, "relay": {"value"},
                        "route": {"receiver", "value"}, "confirmations": {"value"}}
            if operation not in required or set(fields) != required[operation]:
                raise ValueError("Unknown operation or unexpected fields")
            if operation == "disarm":
                self.error = None
                return self._stop("Operator DISARM — HOLD stopped")
            if operation == "shutdown":
                self._stop("Shutdown requested — HOLD stopped")
                return self._request({"op": "shutdown"})
            if operation in ("arm", "recover"):
                self._ready()
                if self.holding or self.snapshot["policy"]["armed"]:
                    raise ValueError("Disarm before a new ARM/RECOVER")
                if operation == "arm" and self.snapshot["policy"].get("fault") not in (None, "new_pico_session", "operator_disarm"):
                    raise ValueError("Latched fault requires explicit RECOVER + ARM")
                result = self._request({"op": operation})
                if result["ok"]:
                    self.error = None
                    self.arm_started = now
                    self.arm_fault = self.snapshot["policy"].get("fault")
                    self.holding = True
                    self.bench_confirmed, self.confirmed = False, dict.fromkeys(CONFIRMATIONS, False)
                    self.last_renew = None
                    self.notice = operation.upper() + " requested — outputs remain OFF until ACTIVE"
                    if not self._renew(now):
                        return {"ok": False, "error": self.error}
                else:
                    self.error = str(result.get("error", "ARM rejected"))[:200]
                return result
            if operation == "control":
                if fields["name"] not in EN_OUTPUTS or type(fields["value"]) is not bool:
                    raise ValueError("Named EN and boolean required")
                if fields["value"]:
                    self._ready(active=True)
                    if fields["name"] in ("EN_AUX12", "EN_LABPORT"):
                        self._bench_ready()
            elif operation == "mode":
                self._ready()
                if fields["value"] not in ("field", "lab") or self.holding or self.snapshot["policy"]["armed"]:
                    raise ValueError("Mode change requires disarmed field/lab selection")
            elif operation == "route":
                if fields["receiver"] not in RECEIVERS or fields["value"] not in ROUTES:
                    raise ValueError("Unknown receiver/route")
                if fields["value"] not in ("PARK", "RF1"):
                    self._ready(active=True)
                    if fields["receiver"] == "RTLB" and fields["value"] == "RF4":
                        self._bench_ready()
            elif operation == "relay":
                if fields["value"] not in ("PARK", "HF", "VHF"):
                    raise ValueError("Unknown relay state")
                if fields["value"] != "PARK":
                    self._ready(active=True)
            elif operation == "confirmations":
                value = fields["value"]
                if (not isinstance(value, dict) or not value or set(value) - set(CONFIRMATIONS)
                        or any(type(v) is not bool for v in value.values())):
                    raise ValueError("Explicit named boolean confirmations required")
                self._ready(active=True)
                if value.get("bench_loads") and self.snapshot["policy"]["mode"] != "lab":
                    raise ValueError("Bench confirmation requires active lab mode")
            result = self._request(dict(op=operation, **fields))
            if result["ok"]:
                self.error = None
                self.notice = operation + " accepted by labd"
                if operation == "mode":
                    self.notice = fields["value"].upper() + " staged; explicit ARM is required to apply it"
                if operation == "confirmations":
                    self.confirmed.update(fields["value"])
                    self.bench_confirmed = self.confirmed["bench_loads"]
            else:
                self.error = str(result.get("error", "Rejected"))[:240]
            return result
        except (OSError, ValueError, TypeError, RuntimeError) as error:
            self.error = str(error)[:240]
            if isinstance(error, OSError):
                self.connected = False
                self._stop("Service connection failed — HOLD stopped", send=self.holding)
                self.link_error = self.error
            return {"ok": False, "error": self.error}

    def _bench_ready(self):
        if self.snapshot["policy"]["mode"] != "lab" or not self.bench_confirmed:
            raise ValueError("BENCH requires lab mode and explicit loads confirmation")

    def arm(self):
        return self.command("arm")

    def recover(self):
        return self.command("recover")

    def disarm(self):
        return self.command("disarm")

    def hold(self, enabled=True):
        if type(enabled) is not bool:
            return {"ok": False, "error": "Boolean HOLD required"}
        if not enabled:
            return self.disarm()
        if self.holding and self.arm_started is not None:
            # poll() keeps the handshake deadline/fault checks; a second press must not cancel ARM.
            return {"ok": True, "message": "ARM handshake in progress; HOLD already active"}
        try:
            self._ready()
            policy = self.snapshot["policy"]
            if not policy["armed"] or policy.get("fault") or self.snapshot["pico"].get("state") != "ACTIVE":
                raise ValueError("HOLD does not arm; explicit ARM/RECOVER is required")
            self.holding = True
            self.error = None
            return {"ok": self._renew(self._now())}
        except (OSError, ValueError, TypeError, RuntimeError) as error:
            self.error = str(error)[:200]
            self._stop("HOLD rejected", send=self.holding)
            return {"ok": False, "error": self.error}

    def close(self):
        if not self.closed:
            self.error = None
            self._stop("Console closed — DISARM requested")
            self.closed = True


def socket_transport(path):
    from .daemon import request_once
    return lambda request: request_once(path, request, timeout=.4)


def location_callbacks(host=None, port=None, device=None):
    """Lazy, read-only location provider; a connection requires explicit endpoint."""
    from .location import LocationTracker, GpsdClient
    if (host is None) != (port is None):
        raise ValueError("Specify both gpsd host and port")
    tracker = LocationTracker(device=device)
    client = GpsdClient(tracker, host, port) if host is not None else None
    if client is not None:
        client.start(int(time.monotonic() * 1000))

    def current():
        now = int(time.monotonic() * 1000)
        if client is not None:
            client.poll(now)
        return tracker.status(now)

    def manual(lat, lon):
        tracker.manual(lat, lon, int(time.monotonic() * 1000))

    return {"location": current, "manual_location": manual}, (client.close if client is not None else lambda: None)


class DemoTransport:
    """A separate, bounded stdio labd process; it cannot select hardware mode."""
    def __init__(self, timeout=1.0):
        self.timeout = timeout
        self.process = subprocess.Popen([sys.executable, "-m", "srrx.daemon", "--simulate", "--stdio"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0,
            env=_child_environment())
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.pending = bytearray()
        self.closed = False
        self.answered = False

    def __call__(self, request):
        if self.closed or self.process.poll() is not None:
            raise OSError("SIMULATION daemon is unavailable")
        wire = json.dumps(request, allow_nan=False, separators=(",", ":")).encode() + b"\n"
        if len(wire) > 4096:
            raise ValueError("Oversize request")
        self.process.stdin.write(wire)
        # Only the cold-start reply gets a longer wait; no lease exists before it.
        deadline = time.monotonic() + (self.timeout if self.answered else max(self.timeout, 10.0))
        while b"\n" not in self.pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                # Kill on timeout so a late reply cannot answer a later request.
                self.close()
                raise OSError("SIMULATION daemon response timeout")
            block = os.read(self.process.stdout.fileno(), 8192)
            if not block:
                raise OSError("SIMULATION daemon closed")
            self.pending.extend(block)
            if len(self.pending) > 65536:
                self.close()
                raise ValueError("Oversize SIMULATION response")
        line, _, rest = self.pending.partition(b"\n")
        self.pending = bytearray(rest)
        self.answered = True
        return _json(line)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.process.stdin.close()  # EOF asks the real Engine to disarm/close.
        try:
            self.process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=.5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=1)
        self.selector.close()
        self.process.stdout.close()


class ReceiverSimulation:
    """Explicit simulation CLI only; no driver name or hardware option accepted."""
    def __init__(self):
        self.directory = tempfile.TemporaryDirectory(prefix="srrx-hmi-rx-")
        self.path = Path(self.directory.name) / "spectrum.json"
        self.process = None
        self.started = None
        self.last_version = None

    def start(self, center_hz, sample_rate):
        if (not _finite(center_hz) or not 0 <= center_hz <= 6e9 or int(center_hz) != center_hz
                or not _finite(sample_rate) or not 48000 <= sample_rate <= 56e6 or int(sample_rate) != sample_rate):
            raise ValueError("Integer centre0..6GHz and rate48kHz..56MHz required")
        if self.process is not None and self.process.poll() is None:
            raise ValueError("A SIM capture is already running")
        self.path.unlink(missing_ok=True)
        self.last_version = None
        self.process = subprocess.Popen([sys.executable, "-m", "srrx.labrx", "--simulate",
            "--center-hz", str(int(center_hz)), "--sample-rate", str(int(sample_rate)), "--frames", "10",
            "--output", str(self.path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env=_child_environment())
        self.started = time.monotonic()

    def poll(self):
        if self.process is None:
            return None
        if time.monotonic() - self.started > 20:
            self._stop()
            raise ValueError("SIM receiver exceeded20s")
        code = self.process.poll()
        if code is not None:
            self.process = None
        if code is not None and code:
            raise ValueError("SIM receiver failed with exit code " + str(code))
        if self.path.exists():
            version = self.path.stat().st_mtime_ns
            if version != self.last_version:
                value = load_spectrum(self.path)
                self.last_version = version
                return value
        if code == 0 and self.last_version is None:
            raise ValueError("SIM receiver produced no SpectrumFrame")
        return None

    def _stop(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=.5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=1)
            self.process = None

    def close(self):
        self._stop()
        self.directory.cleanup()


def create_window(controller, *, callbacks=None, start_worker=True):
    """Lazy Qt entry point. callbacks may supply location() / manual_location()."""
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
    except ImportError as error:
        raise RuntimeError("Touch UI needs optional PySide6; the controller remains usable without Qt") from error
    callbacks = callbacks or {}

    class Worker(QtCore.QThread):
        state = QtCore.Signal(object)

        def __init__(self):
            super().__init__()
            self.commands = queue.Queue(maxsize=16)
            self.stopping = threading.Event()
            self.ui_at = time.monotonic()
            self.last_poll = 0
            self.locked = False

        def submit(self, operation, fields=None):
            if self.stopping.is_set():
                return
            if self.locked and operation not in ("disarm", "shutdown"):
                return
            if operation in ("disarm", "shutdown"):
                while True:
                    try:
                        self.commands.get_nowait()
                    except queue.Empty:
                        break
            try:
                self.commands.put_nowait((operation, fields or {}))
            except queue.Full:
                controller.notice = "Command queue full — request not accepted"

        def run(self):
            try:
                while not self.stopping.is_set():
                    now = time.monotonic()
                    if now - self.ui_at > 1.5 and controller.holding:
                        controller.disarm()
                        controller.notice = "Touch UI heartbeat lost — HOLD stopped"
                    try:
                        operation, fields = self.commands.get_nowait()
                        if self.locked and operation not in ("disarm", "shutdown"):
                            controller.notice = "Touch controls locked; DISARM remains available"
                        elif operation == "hold":
                            controller.hold(**fields)
                        else:
                            controller.command(operation, **fields)
                        self.state.emit(controller.status())
                    except queue.Empty:
                        pass
                    if now - self.last_poll >= .25:
                        self.state.emit(controller.poll())
                        self.last_poll = now
                    self.stopping.wait(.02)
            finally:
                controller.close()
                if isinstance(controller.transport, DemoTransport):
                    controller.transport.close()

    class Plot(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self.rows = []
            self.geometry = None
            self.setMinimumHeight(270)
            self.setAccessibleName("Masked spectrum and waterfall")

        def add(self, frame):
            geometry = (frame["center_hz"], frame["sample_rate_hz"], frame["fft_size"], frame["source"])
            if geometry != self.geometry:
                self.rows = []
                self.geometry = geometry
            self.rows.append(spectrum_columns(frame))
            self.rows = self.rows[-96:]
            self.update()

        def paintEvent(self, event):
            painter = QtGui.QPainter(self)
            painter.fillRect(self.rect(), QtGui.QColor("#080c11"))
            if not self.rows:
                painter.setPen(QtGui.QColor("#ffffff"))
                painter.drawText(self.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "Load a masked SpectrumFrame — no live data")
                return
            width, top = self.width(), self.height() // 2
            row = self.rows[-1]
            painter.setPen(QtGui.QPen(QtGui.QColor("#4fe3db"), 2))
            segment = []
            for index, value in enumerate(row):
                if value is None:
                    if len(segment) > 1:
                        painter.drawPolyline(QtGui.QPolygonF(segment))
                    segment = []
                else:
                    y = top - 12 - max(0, min(1, (value + 130) / 130)) * (top - 25)
                    segment.append(QtCore.QPointF(index * width / len(row), y))
            if len(segment) > 1:
                painter.drawPolyline(QtGui.QPolygonF(segment))
            for yindex, values in enumerate(reversed(self.rows)):
                y = top + yindex * (self.height() - top) / 96
                for index, value in enumerate(values):
                    if value is None:
                        continue
                    intensity = max(0, min(1, (value + 120) / 110))
                    color = QtGui.QColor.fromHsvF(.65 - intensity * .55, .9, .2 + intensity * .8)
                    left, right = index * width // len(values), (index + 1) * width // len(values)
                    lower = top + (yindex + 1) * (self.height() - top) // 96
                    painter.fillRect(QtCore.QRect(left, int(y), right - left, max(1, lower - int(y))), color)
            painter.setPen(QtGui.QColor("#e5ecf5"))
            painter.drawText(8, 20, "0 dBFS")
            painter.drawText(8, top - 5, "−130 dBFS")
            painter.drawText(8, top + 24, "older rows ↓")

    class ConsoleWindow(QtWidgets.QMainWindow):
        PINNED = "Saved snapshot shown — live updates paused until Return to live position"

        def __init__(self):
            super().__init__()
            self.setWindowTitle("SR-RX • local receive console")
            self.resize(1100, 800)
            self.setMinimumSize(800, 640)
            self.worker = Worker()
            self.worker.state.connect(self.render_state)
            self.worker.finished.connect(self._finished)
            self.closing = False
            self.worker_started = start_worker
            self.frame = None
            self.frame_file = None
            self.frame_version = None
            self.dataset = None
            self.model = None
            self.group_id = str(uuid.uuid4())
            self.navigation = HMINavigation()
            self.mark_count = 0
            self.input_message = ""
            self.location = None
            self.location_pinned = False
            self.location_status = None
            self.teach_frame = None
            self.worker_dead = False
            self.tab_commands = []
            self.receiver_job = ReceiverSimulation()
            self.setStyleSheet("""
                QWidget {background:#101821;color:#f6f8fb;font-size:18px;}
                QPushButton {background:#263e51;border:2px solid #9bb7cb;border-radius:8px;
                    padding:12px;min-height:44px;font-size:19px;font-weight:600;}
                QPushButton:pressed {background:#456a83;} QPushButton:disabled {color:#80909c;border-color:#465462;}
                QTabBar::tab {padding:14px 10px;min-height:32px;} QTabBar::tab:selected {background:#35546b;}
                QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {background:#233342;padding:10px;min-height:36px;}
                QCheckBox {spacing:14px;min-height:50px;} QCheckBox::indicator {width:30px;height:30px;}
                QCheckBox::indicator:unchecked {border:2px solid #c5d9e8;background:#182633;}
                QCheckBox::indicator:checked {border:2px solid #ffffff;background:#59efad;}
                QPlainTextEdit {background:#090f16;font-family:monospace;font-size:16px;}
            """)
            root = QtWidgets.QWidget()
            self.setCentralWidget(root)
            layout = QtWidgets.QVBoxLayout(root)
            self.banner = QtWidgets.QLabel("CONNECTING — outputs must remain OFF")
            self.banner.setWordWrap(True)
            self.banner.setMinimumHeight(60)
            layout.addWidget(self.banner)
            actions = QtWidgets.QHBoxLayout()
            self.command_buttons = {}
            for text, op in (("ARM + HOLD", "arm"), ("RECOVER + ARM", "recover"), ("DISARM / STOP", "disarm")):
                button = self.button(text, lambda checked=False, value=op: self.action(value))
                if op == "disarm":
                    button.setStyleSheet("background:#942d2d;border-color:#ffceba;font-size:21px;")
                else:
                    self.command_buttons[op] = button
                actions.addWidget(button)
            self.command_buttons["hold"] = self.button("HOLD lease", lambda: self.action("hold", {"enabled": True}))
            actions.addWidget(self.command_buttons["hold"])
            layout.addLayout(actions)
            self.tabs = QtWidgets.QTabWidget()
            layout.addWidget(self.tabs, 1)
            self._overview_page()
            self._receiver_page()
            self._spectrum_page()
            self._location_page()
            self._learning_page()
            self._bench_page()
            self.notice = QtWidgets.QLabel("Status reads do not arm or renew a lease.")
            self.notice.setTextFormat(QtCore.Qt.TextFormat.PlainText)
            self.notice.setWordWrap(True)
            layout.addWidget(self.notice)
            self.input_note = QtWidgets.QLabel("Ambient lux unavailable | touch unlocked")
            self.input_note.setWordWrap(True)
            layout.addWidget(self.input_note)
            bottom = QtWidgets.QHBoxLayout()
            bottom.addWidget(self.button("Shutdown…", lambda: self.action("shutdown")))
            bottom.addWidget(self.button("Unlock touch…", self.unlock_touch))
            bottom.addWidget(self.button("Close + DISARM", self.close))
            layout.addLayout(bottom)
            self.timer = QtCore.QTimer(self)
            self.timer.setInterval(250)
            self.timer.timeout.connect(self._heartbeat)
            self.timer.start()
            if start_worker:
                self.worker.start()
            self.render_state(controller.status())

        def button(self, text, handler):
            button = QtWidgets.QPushButton(text)
            button.clicked.connect(handler)
            button.setAccessibleName(text)
            return button

        def page(self, name):
            page = QtWidgets.QWidget()
            page.setLayout(QtWidgets.QVBoxLayout())
            scroll = QtWidgets.QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            self.tabs.addTab(scroll, name)
            return page.layout()

        def text_page(self, name):
            layout = self.page(name)
            text = QtWidgets.QPlainTextEdit()
            text.setReadOnly(True)
            layout.addWidget(text)
            return text

        def diagnostics(self, layout, title="Show diagnostics"):
            button = QtWidgets.QPushButton(title)
            button.setCheckable(True)
            text = QtWidgets.QPlainTextEdit()
            text.setReadOnly(True)
            text.setMinimumHeight(200)
            text.setVisible(False)
            button.toggled.connect(text.setVisible)
            layout.addWidget(button)
            layout.addWidget(text)
            return text

        def _overview_page(self):
            layout = self.page("Overview")
            cards = QtWidgets.QHBoxLayout()
            self.metric_values = {}
            for name, title in (("battery", "Battery"), ("temperature", "Temperatures"), ("supervisor", "Controller / operator")):
                card = QtWidgets.QFrame()
                card.setStyleSheet("QFrame{background:#203342;border:1px solid #7797b0;border-radius:8px;} QLabel{border:0;background:transparent;}")
                content = QtWidgets.QVBoxLayout(card)
                heading = QtWidgets.QLabel(title)
                value = QtWidgets.QLabel("Unavailable")
                value.setWordWrap(True)
                value.setStyleSheet("font-size:23px;font-weight:700;")
                value.setMinimumHeight(64)
                content.addWidget(heading); content.addWidget(value)
                cards.addWidget(card, 1)
                self.metric_values[name] = value
            layout.addLayout(cards)
            self.fault_text = QtWidgets.QLabel("Waiting for a fresh controller status")
            self.fault_text.setTextFormat(QtCore.Qt.TextFormat.PlainText)
            self.fault_text.setWordWrap(True)
            self.fault_text.setMinimumHeight(42)
            layout.addWidget(self.fault_text)
            self.channel_table = QtWidgets.QTableWidget(len(EN_OUTPUTS), 5)
            self.channel_table.setStyleSheet("QTableWidget{background:#132533;alternate-background-color:#1c2e3f;gridline-color:#496173;font-size:17px;} QHeaderView::section{background:#263e51;color:#ffffff;padding:7px;}")
            self.channel_table.setHorizontalHeaderLabels(("Channel", "Power", "Route", "Current", "Reserved"))
            self.channel_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
            self.channel_table.verticalHeader().setVisible(False)
            self.channel_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.channel_table.setMinimumHeight(285)
            self.channel_table.setAlternatingRowColors(True)
            for row in range(len(EN_OUTPUTS)):
                self.channel_table.setRowHeight(row, 48)
            layout.addWidget(self.channel_table, 1)
            explanation = QtWidgets.QLabel("Reserved = budgeted current, not a live measurement. OFF and route changes are on Receiver / Bench.")
            explanation.setWordWrap(True)
            layout.addWidget(explanation)
            self.overview = self.diagnostics(layout, "Controller diagnostics…")

        def action(self, operation, fields=None):
            if self.worker_dead:
                self.input_message = "Control worker stopped — " + operation.upper() + " not sent; restart the console"
                return
            if self.worker.locked and operation not in ("disarm", "shutdown"):
                self.input_message = "Touch controls locked — " + operation.upper() + " not sent; DISARM remains available"
                return
            if operation in ("arm", "recover", "shutdown"):
                text = {"arm": "Request ARM and renew the operator lease while this console is responsive? All loads start OFF.",
                        "recover": "Cause removed and hardware checked? RECOVER performs a new ARM handshake. Loads start OFF.",
                        "shutdown": "Request controlled shutdown? labd stops loads; the accepted system shutdown bridge handles OS poweroff."}[operation]
                answer = QtWidgets.QMessageBox.question(self, operation.upper(), text,
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                    QtWidgets.QMessageBox.StandardButton.No)
                if answer != QtWidgets.QMessageBox.StandardButton.Yes:
                    return
            self.worker.submit(operation, fields)

        def set_locked(self, locked):
            self.worker.locked = locked
            self.tabs.setEnabled(not locked)
            for button in self.command_buttons.values():
                button.setEnabled(not locked and not self.worker_dead)
            for widget in self.tab_commands:
                widget.setEnabled(not self.worker_dead)

        def tab_button(self, text, handler):
            # In-tab labd commands go through action(); a dead worker disables them.
            button = self.button(text, handler)
            self.tab_commands.append(button)
            return button

        def unlock_touch(self):
            if not self.worker.locked:
                return
            answer = QtWidgets.QMessageBox.question(self, "Unlock touch", "Unlock touch controls? This does not arm or enable a load.")
            if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                self.set_locked(False)

        def _receiver_page(self):
            layout = self.page("Receiver")
            note = QtWidgets.QLabel("Receive-only. SIM capture never powers EN or starts a physical driver.\nPhysical RX requires the accepted labrx CLI/driver workflow.")
            note.setWordWrap(True)
            layout.addWidget(note)
            form = QtWidgets.QFormLayout()
            self.center = QtWidgets.QDoubleSpinBox()
            self.center.setDecimals(0); self.center.setRange(0, 6000000000); self.center.setValue(100000000)
            self.rate = QtWidgets.QDoubleSpinBox()
            self.rate.setDecimals(0); self.rate.setRange(48000, 56000000); self.rate.setValue(1024000)
            form.addRow("Centre (Hz)", self.center); form.addRow("Sample rate (Hz)", self.rate)
            layout.addLayout(form)
            layout.addWidget(self.button("Start SIM capture · 10 frames", self.start_capture))
            self.rx_note = QtWidgets.QLabel("No receiver process started")
            self.rx_note.setWordWrap(True); layout.addWidget(self.rx_note)
            for receiver in RECEIVERS:
                row = QtWidgets.QHBoxLayout()
                row.addWidget(QtWidgets.QLabel(receiver))
                selection = QtWidgets.QComboBox(); selection.addItems(ROUTES)
                row.addWidget(selection)
                row.addWidget(self.tab_button("Apply route", lambda checked=False, r=receiver, s=selection:
                    self.action("route", {"receiver": r, "value": s.currentText()})))
                layout.addLayout(row)
            relay = QtWidgets.QComboBox(); relay.addItems(("PARK", "HF", "VHF"))
            layout.addWidget(relay)
            layout.addWidget(self.tab_button("Apply HF relay", lambda: self.action("relay", {"value": relay.currentText()})))
            layout.addStretch()

        def start_capture(self):
            try:
                self.receiver_job.start(self.center.value(), self.rate.value())
                self.rx_note.setText("SIMULATION capture running; RF hardware remains controlled by labd")
            except (OSError, ValueError, RuntimeError) as error:
                self.rx_note.setText(str(error))

        def _spectrum_page(self):
            layout = self.page("Spectrum")
            layout.addWidget(self.button("Load spectrum JSON / survey JSONL", self.open_spectrum))
            self.spec_note = QtWidgets.QLabel("Masked/no-data bins remain blank. Files are snapshots.")
            self.spec_note.setWordWrap(True); layout.addWidget(self.spec_note)
            self.plot = Plot(); layout.addWidget(self.plot, 1)

        def accept_frame(self, frame):
            from .spectrum import mask_frame
            previous, self.frame = self.frame, mask_frame(frame)
            self.plot.add(self.frame)
            size, valid = self.frame["fft_size"], sum(self.frame["valid"])
            self.spec_note.setText(f"{self.frame['source']} snapshot | centre {self.frame['center_hz']:.0f} Hz | "
                f"rate {self.frame['sample_rate_hz']:.0f} Hz | {valid}/{size} valid bins")
            self.bin_start.setMaximum(size - 1)
            self.bin_end.setMaximum(size)
            if previous is None or any(previous[k] != self.frame[k] for k in ("center_hz", "sample_rate_hz", "fft_size", "source")):
                # A streamed frame of the same geometry keeps the operator's selection.
                self.bin_start.setValue(0)
                self.bin_end.setValue(min(256, size))
                self.teach_confirm.setChecked(False)

        def open_spectrum(self):
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Spectrum snapshot", "", "JSON (*.json *.jsonl)")
            if path:
                try:
                    self.accept_frame(load_spectrum(path))
                    self.frame_file = Path(path)
                    self.frame_version = self.frame_file.stat().st_mtime_ns
                except (OSError, ValueError, ImportError, TypeError, KeyError, RuntimeError) as error:
                    self.spec_note.setText("Rejected: " + str(error))

        def _location_page(self):
            layout = self.page("Location")
            self.location_text = QtWidgets.QLabel("No position available")
            self.location_text.setTextFormat(QtCore.Qt.TextFormat.PlainText)
            self.location_text.setWordWrap(True)
            self.location_text.setMinimumHeight(195)
            self.location_text.setStyleSheet("background:#203342;padding:16px;font-size:22px;")
            layout.addWidget(self.location_text)
            self.location_note = QtWidgets.QLabel("Live tracker position" if "location" in callbacks else "No live location provider")
            self.location_note.setTextFormat(QtCore.Qt.TextFormat.PlainText)
            self.location_note.setWordWrap(True); layout.addWidget(self.location_note)
            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.button("Load saved position…", self.open_location))
            row.addWidget(self.button("Return to live position", self.live_location))
            layout.addLayout(row)
            form = QtWidgets.QFormLayout()
            self.latitude = QtWidgets.QDoubleSpinBox(); self.latitude.setDecimals(7); self.latitude.setRange(-90, 90)
            self.longitude = QtWidgets.QDoubleSpinBox(); self.longitude.setDecimals(7); self.longitude.setRange(-180, 180)
            form.addRow("Manual latitude (degrees)", self.latitude)
            form.addRow("Manual longitude (degrees)", self.longitude)
            layout.addLayout(form)
            layout.addWidget(self.button("Use manual location", self.manual_location))
            self.location_diagnostics = self.diagnostics(layout, "Location diagnostics…")

        def open_location(self):
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Location snapshot", "", "JSON (*.json)")
            if path:
                try:
                    value = load_json(path)
                    self._location_value(value, live=False)
                    self.location_pinned = True
                    self._location_note(self.PINNED, force=True)
                except (OSError, ValueError, TypeError, RuntimeError) as error:
                    self.location_note.setText("Position rejected: " + str(error))

        def live_location(self):
            if "location" not in callbacks:
                self.location_note.setText("No live location provider")
                return
            self.location_pinned, self.location_status = False, None
            self._live_location()

        def _live_location(self):
            # Polled even while pinned, so the gpsd socket keeps draining; only rendering pauses.
            try:
                value = callbacks["location"]()
                if self.location_pinned:
                    note = self.PINNED
                else:
                    self._location_value(value, live=True)
                    note = "Manual position — not a GNSS fix" if self.location.get("source") == "manual" else "Live tracker position"
            except (ImportError, OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
                if self.location_pinned:
                    note = self.PINNED + "\nLive provider error: " + str(error)[:160]
                else:
                    # Never leave an old "Live GNSS fix" on screen when the provider fails.
                    self.location = None
                    self.location_text.setText("Location unavailable: " + str(error)[:200])
                    note = "Live tracker unavailable"
            self._location_note(note)

        def _location_note(self, text, force=False):
            # Only a change of the shown state replaces the note; a rejection stays readable.
            if force or text != self.location_status:
                self.location_status = text
                self.location_note.setText(text)

        def _location_value(self, value, live=False):
            if not isinstance(value, dict):
                raise ValueError("Location object required")
            if value.get("available") is True:
                if not _finite(value.get("lat")) or not -90 <= value["lat"] <= 90 or not _finite(value.get("lon")) or not -180 <= value["lon"] <= 180:
                    raise ValueError("Finite latitude/longitude required")
            self.location = copy.deepcopy(value)
            if not live:
                self.location.update(fresh=False, live_fix=False)
            summary = location_summary(self.location, live)
            self.location_text.setText(summary["position"] + "\n\n" + summary["fix"] + "\nSource: " + summary["source"]
                + ("\nFix age: " if live else "\nAge at capture: ") + summary["age"] + "\nAccuracy: " + summary["uncertainty"])
            self.location_diagnostics.setPlainText(json.dumps(self.location, indent=2, ensure_ascii=False, allow_nan=False))

        def manual_location(self):
            lat, lon = self.latitude.value(), self.longitude.value()
            try:
                if "manual_location" in callbacks:
                    callbacks["manual_location"](lat, lon)
                self._location_value({"available": True, "source": "manual", "lat": lat, "lon": lon,
                    "fresh": False, "live_fix": False, "uncertainty_m": None, "uncertainty_confidence": "unknown"})
                # The tracker now reports the manual entry, so live refresh resumes;
                # a later fresh GNSS fix from the tracker replaces this note.
                self.location_pinned = False
                self._location_note("Manual position — not a GNSS fix", force=True)
            except (OSError, ValueError, TypeError, RuntimeError) as error:
                self.location_note.setText("Manual position rejected: " + str(error))

        def _learning_page(self):
            layout = self.page("Teach / Classify")
            note = QtWidgets.QLabel("Coarse masked-spectrum labels. Model scores are not calibrated probabilities.\nNo decoded payload, identity or location enters the training dataset.")
            note.setWordWrap(True); layout.addWidget(note)
            row = QtWidgets.QHBoxLayout()
            self.bin_start = QtWidgets.QSpinBox(); self.bin_start.setRange(0, 1048575)
            self.bin_end = QtWidgets.QSpinBox(); self.bin_end.setRange(1, 1048576); self.bin_end.setValue(256)
            self.label = QtWidgets.QComboBox()
            for key in LABELS:
                self.label.addItem(CLASS_LABELS[key], key)
            row.addWidget(QtWidgets.QLabel("Bins [start,end)")); row.addWidget(self.bin_start); row.addWidget(self.bin_end); row.addWidget(self.label)
            layout.addLayout(row)
            self.teach_confirm = QtWidgets.QCheckBox("I explicitly confirm this coarse label and independent capture grouping")
            layout.addWidget(self.teach_confirm)
            # Confirmation binds the frame shown now; changing bins or label requires a new one.
            self.teach_confirm.toggled.connect(self._teach_toggled)
            for signal in (self.bin_start.valueChanged, self.bin_end.valueChanged, self.label.currentIndexChanged):
                signal.connect(lambda _=None: self.teach_confirm.setChecked(False))
            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.button("Add annotation", lambda: self.learning_action("annotate")))
            row.addWidget(self.button("Train CPU model", lambda: self.learning_action("train")))
            row.addWidget(self.button("Classify selected bins", lambda: self.learning_action("infer")))
            layout.addLayout(row)
            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.button("New independent session…", self.new_group))
            row.addWidget(self.button("Load dataset", lambda: self.learning_file("dataset", False)))
            row.addWidget(self.button("Save dataset", lambda: self.learning_file("dataset", True)))
            layout.addLayout(row)
            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.button("Load model", lambda: self.learning_file("model", False)))
            row.addWidget(self.button("Save model", lambda: self.learning_file("model", True)))
            layout.addLayout(row)
            self.learning_text = QtWidgets.QPlainTextEdit(); self.learning_text.setReadOnly(True)
            self.learning_text.setStyleSheet("QPlainTextEdit{background:#203342;font-family:sans-serif;font-size:20px;padding:8px;}")
            self.learning_text.setMinimumHeight(300)
            layout.addWidget(self.learning_text, 1)
            self.learning_diagnostics = self.diagnostics(layout, "Learning diagnostics…")

        def _teach_toggled(self, checked):
            self.teach_frame = self.frame if checked else None

        def new_group(self):
            answer = QtWidgets.QMessageBox.question(self, "Independent session", "Start a genuinely independent capture session? Relabelling overlapping snapshots does not create independent validation data.")
            if answer == QtWidgets.QMessageBox.StandardButton.Yes:
                self.group_id = str(uuid.uuid4())
                self.teach_confirm.setChecked(False)
                self.learning_text.setPlainText("Independent session ready\n\nNew annotations will use this group. Collect genuinely separate capture conditions before adding a validation session.")
                self.learning_diagnostics.setPlainText("Anonymous group: " + self.group_id)

        def learning_action(self, operation):
            try:
                from . import learning
                if self.dataset is None:
                    self.dataset = learning.empty_dataset()
                if operation == "train":
                    self.model = learning.train(self.dataset, seed=0, validation_fraction=.25)
                    result = self.model
                elif self.frame is None:
                    raise ValueError("Load a masked spectrum first")
                elif operation == "annotate":
                    if not self.teach_confirm.isChecked() or self.teach_frame is None:
                        raise ValueError("Explicit label/group confirmation required")
                    self.dataset = learning.annotate(self.dataset, self.teach_frame, self.bin_start.value(), self.bin_end.value(),
                        self.label.currentData(), group_id=self.group_id, user_confirmed=True)
                    self.teach_confirm.setChecked(False)
                    result = self.dataset
                else:
                    if self.model is None:
                        raise ValueError("Load/train a model first")
                    result = learning.infer(self.model, self.frame, self.bin_start.value(), self.bin_end.value(), backend="cpu")
                self.learning_text.setPlainText(learning_summary(result, operation, self.model))
                self.learning_diagnostics.setPlainText(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)[:16000])
            except (ImportError, OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
                self.learning_text.setPlainText("Rejected: " + str(error))
            if self.tabs.currentIndex() == 4:
                self.tabs.currentWidget().ensureWidgetVisible(self.learning_text)

        def learning_file(self, kind, save):
            try:
                from . import learning
                if save:
                    value = getattr(self, kind)
                    if value is None:
                        raise ValueError("No " + kind + " to save")
                    path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save " + kind, kind + ".json", "JSON (*.json)")
                    if path:
                        data = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False).encode()
                        if len(data) > MAX_FILE_BYTES:
                            raise ValueError("Metadata exceeds console size limit")
                        if kind == "dataset":
                            learning.save_dataset(path, value)
                        else:
                            learning.save_model(path, value)
                else:
                    path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load " + kind, "", "JSON (*.json)")
                    if path:
                        value = load_json(path)
                        value = learning.validate_dataset(value) if kind == "dataset" else learning.validate_model(value)
                        setattr(self, kind, value)
                        self.learning_text.setPlainText(learning_summary(value, kind))
                        self.learning_diagnostics.setPlainText(json.dumps(value, indent=2)[:16000])
            except (ImportError, OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
                self.learning_text.setPlainText("Rejected: " + str(error))

        def _bench_page(self):
            layout = self.page("Bench")
            note = QtWidgets.QLabel("BENCH: stage lab mode while DISARMED, then explicit ARM. Confirm real loads before LABPORT/AUX12 or RTL-B RF4. labd checks PARK, bias, limits and telemetry. No raw GPIO or charging override.")
            note.setWordWrap(True); layout.addWidget(note)
            row = QtWidgets.QHBoxLayout()
            for mode in ("field", "lab"):
                row.addWidget(self.tab_button("Stage " + mode.upper(), lambda checked=False, m=mode: self.action("mode", {"value": m})))
            layout.addLayout(row)
            for name, label in (("bench_loads", "Bench loads connected and checked"),
                                ("boni_connected", "Boni antenna/module connected"), ("boni_profile", "Boni profile/current window checked")):
                check = QtWidgets.QCheckBox(label)
                if not hasattr(self, "confirmation_checks"):
                    self.confirmation_checks = []
                self.confirmation_checks.append(check)
                self.tab_commands.append(check)
                layout.addWidget(check)
                check.clicked.connect(lambda value, n=name: self.action("confirmations", {"value": {n: value}}))
            grid = QtWidgets.QGridLayout()
            self.output_labels = {}
            self.output_on_buttons = {}
            for index, name in enumerate(EN_OUTPUTS):
                cell = QtWidgets.QWidget(); row = QtWidgets.QHBoxLayout(cell)
                label = QtWidgets.QLabel(name + " ?"); self.output_labels[name] = label
                row.addWidget(label)
                on_button = self.button("ON", lambda checked=False, n=name: self.action("control", {"name": n, "value": True}))
                self.output_on_buttons[name] = on_button
                row.addWidget(on_button)
                row.addWidget(self.tab_button("OFF", lambda checked=False, n=name: self.action("control", {"name": n, "value": False})))
                grid.addWidget(cell, index // 2, index % 2)
            layout.addLayout(grid)
            layout.addStretch()

        @QtCore.Slot(object)
        def render_state(self, view):
            data = view.get("data", {})
            policy, pico = data.get("policy", {}), data.get("pico", {})
            live = view.get("connected") is True and not self.worker_dead
            # Pico readouts need labd's own Pico freshness, not only a fresh labd reply.
            # A labd that omits the field is "unreported": readouts withheld, no stale/ARM claim.
            freshness = data.get("pico_fresh")
            pico_live = live and freshness is True
            holding = view.get("holding") is True and not self.worker_dead
            backend = data.get("mode", "UNKNOWN")
            state = "NO CONNECTION" if not live else ("PICO STATUS STALE" if freshness is False else "PICO FRESHNESS UNREPORTED") if not pico_live else {"ACTIVE": "READY", "SAFE": "STOPPED", "TRIPPED": "PROTECTION STOP",
                "CONFIGURING": "STARTING", "RESETTING": "STARTING", "WARMING": "STARTING", "SHUTTING_DOWN": "SHUTTING DOWN", "OFF": "OFF"}.get(pico.get("state"), "WAITING")
            control = ("CONTROL ARMED" if policy.get("armed") else "CONTROL OFF") if live else "CONTROL UNKNOWN"
            mode = str(policy.get("mode", "?")).upper() if live else "MODE UNKNOWN"
            self.banner.setText(("Control worker stopped — HOLD is OFF; verify labd/Pico state | " if self.worker_dead else "")
                + f"{backend} | {state} | {control} | HOLD {'ON' if holding else 'OFF'} | {mode}")
            self.banner.setStyleSheet("background:" + ("#8a2828" if not pico_live or view.get("error") or policy.get("fault") else "#22493b") + ";padding:10px;font-size:20px;font-weight:700;")
            self.notice.setText(str(view.get("notice", "")))
            voltage = pico.get("battery_mv")
            self.metric_values["battery"].setText(f"{voltage / 1000:.2f} V" if pico_live and _finite(voltage) and voltage >= 0 else "Unavailable")
            temperatures = []
            for label, key in (("Case", "case_temp_c"), ("Panel", "panel_temp_c")):
                temperature = pico.get(key)
                temperatures.append(f"{label} {temperature:.1f} °C" if pico_live and _finite(temperature) else label + " unavailable")
            self.metric_values["temperature"].setText("\n".join(temperatures))
            self.metric_values["supervisor"].setText(state.title() + "\nLease: " + ("holding" if holding else "stopped"))
            fault = ("Connection lost — current power state is unconfirmed." if not live
                     else readable_fault(policy.get("fault")) if pico_live
                     else ("Supervisor status stale — no fresh Pico status; ARM will be refused." if freshness is False
                           else "labd did not report Pico freshness — Pico readouts withheld; labd checks it before ARM.")
                     # The labd fault stays visible, but never as "ready" without fresh Pico status.
                     + ("\n" + readable_fault(policy["fault"]) if policy.get("fault") not in (None, "", "new_pico_session") else ""))
            # The console's own error never hides the labd protection fault.
            self.fault_text.setText(fault + ("\nConsole: " + str(view["error"])[:240] if view.get("error") else ""))
            for row, values in enumerate(channel_rows(data, live)):
                for column, text in enumerate(values):
                    item = self.channel_table.item(row, column)
                    if item is None:
                        item = QtWidgets.QTableWidgetItem()
                        self.channel_table.setItem(row, column, item)
                    item.setText(text)
                    if column == 1:
                        item.setForeground(QtGui.QColor("#72efb5" if text == "ON" else "#f4f6f8"))
            diagnostic_scroll = self.overview.verticalScrollBar().value()
            self.overview.setPlainText(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)[:24000])
            self.overview.verticalScrollBar().setValue(diagnostic_scroll)
            for name, label in self.output_labels.items():
                value = policy.get("outputs", {}).get(name)
                label.setText(name + (" ON" if value else " OFF") if live and type(value) is bool else name + " UNKNOWN")
                enabled = live and holding and policy.get("armed") and not policy.get("fault") and pico.get("state") == "ACTIVE"
                if name in ("EN_AUX12", "EN_LABPORT"):
                    enabled = enabled and policy.get("mode") == "lab" and view.get("bench_confirmed")
                self.output_on_buttons[name].setEnabled(bool(enabled))
            # Show only confirmations labd accepted; a rejected click must not stay ticked.
            accepted = view.get("confirmations") if isinstance(view.get("confirmations"), dict) else {}
            for name, check in zip(CONFIRMATIONS, self.confirmation_checks):
                check.blockSignals(True)
                check.setChecked(holding and accepted.get(name) is True)
                check.blockSignals(False)
            self.physical_inputs()

        def physical_inputs(self):
            # A queued Qt signal can be delayed. Re-read current, aged state at
            # delivery, rather than treating the old signal snapshot as fresh.
            view = controller.status()
            data = view.get("data", {})
            gestures = self.navigation.consume(data.get("hmi") if view.get("connected") else None, data.get("session"))
            for gesture in gestures["events"]:
                if gesture == "lock":
                    self.set_locked(not self.worker.locked)
                elif not self.worker.locked:
                    if gesture == "home":
                        self.tabs.setCurrentIndex(0)
                    elif gesture == "back":
                        self.tabs.setCurrentIndex(max(0, self.tabs.currentIndex() - 1))
                    elif gesture == "next_page":
                        self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % self.tabs.count())
                    elif gesture == "mark":
                        self.mark_count = min(0xffffffff, self.mark_count + 1)
                        self.input_message = "Local spectrum mark " + str(self.mark_count)
                    elif gesture == "rec_note":
                        self.input_message = "REC received — choose an explicit capture; no power action issued"
                    elif gesture in ("focus_next", "focus_prev"):
                        self.focusNextPrevChild(gesture == "focus_next")
            if not self.worker.locked:
                turn, scroll = gestures["encoders"]
                if turn:
                    self.tabs.setCurrentIndex((self.tabs.currentIndex() + turn) % self.tabs.count())
                if scroll:
                    bar = self.tabs.currentWidget().verticalScrollBar()
                    bar.setValue(bar.value() + scroll * 48)
            lux = gestures["lux"]
            ambient = f"Ambient {lux:.1f} lux" if lux is not None else "Ambient lux unavailable"
            self.input_note.setText(ambient + (" | TOUCH LOCKED — DISARM available" if self.worker.locked else " | touch unlocked")
                                   + (" | " + self.input_message if self.input_message else ""))

        def _heartbeat(self):
            self.worker.ui_at = time.monotonic()
            if self.closing:
                return
            self.render_state(controller.status())
            # Independent steps: one failing source must not freeze the others.
            try:
                frame = self.receiver_job.poll()
                if frame is not None:
                    self.accept_frame(frame)
                    self.rx_note.setText("SIMULATION snapshot loaded into Spectrum")
            except (ImportError, OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
                self.rx_note.setText(str(error))
            if self.frame_file is not None:
                try:
                    info = self.frame_file.stat()
                    if info.st_size > MAX_FILE_BYTES:
                        self.frame_file = self.frame_version = None
                        self.spec_note.setText("Tracked file exceeds 2 MiB — tracking stopped; load a survey excerpt")
                    elif info.st_mtime_ns != self.frame_version:
                        self.frame_version = info.st_mtime_ns  # A rejected version is not re-read every tick.
                        self.accept_frame(load_spectrum(self.frame_file))
                except OSError as error:
                    self.frame_file = self.frame_version = None
                    self.spec_note.setText("Tracked file lost — tracking stopped: " + str(error))
                except (ImportError, ValueError, TypeError, KeyError, RuntimeError) as error:
                    self.spec_note.setText("Tracked file rejected: " + str(error))
            if "location" in callbacks:
                self._live_location()  # Also while pinned: the provider must keep draining gpsd.

        def closeEvent(self, event):
            if self.worker_started and self.worker.isRunning():
                self.closing = True
                self.timer.stop()
                self.worker.stopping.set()
                self.notice.setText("Closing — DISARM requested; lease renewal stopped")
                event.ignore()
            else:
                self.timer.stop()
                if not self.worker_started:
                    controller.close()
                self.receiver_job.close()
                event.accept()

        def _finished(self):
            if self.closing:
                self.close()
            else:
                # Nothing reads the queue any more: drop commands and keep the warning visible.
                self.worker_dead = True
                self.worker.stopping.set()
                self.set_locked(self.worker.locked)
                self.render_state(controller.status())

    return ConsoleWindow()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", default="/tmp/srrx/control.sock")
    parser.add_argument("--demo", action="store_true", help="Start a separate SIMULATION labd over bounded local pipes")
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--gpsd-host", help="Explicit numeric loopback or localhost; no automatic GNSS connection")
    parser.add_argument("--gpsd-port", type=int)
    parser.add_argument("--gpsd-device", help="Optional verified gpsd device identity")
    args = parser.parse_args(argv)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("srrx.hmi: optional PySide6 is required for the GUI; install it in the operator environment", file=sys.stderr)
        return 2
    if (args.gpsd_host is None) != (args.gpsd_port is None):
        parser.error("--gpsd-host and --gpsd-port must be supplied together")
    try:
        callbacks, close_location = location_callbacks(args.gpsd_host, args.gpsd_port, args.gpsd_device)
    except (ImportError, OSError, ValueError) as error:
        print("srrx.hmi: location provider: " + str(error), file=sys.stderr)
        return 2
    transport = DemoTransport() if args.demo else socket_transport(args.socket)
    controller = ConsoleController(transport)
    application = QApplication.instance() or QApplication(sys.argv[:1])
    window = create_window(controller, callbacks=callbacks)
    window.showFullScreen() if args.fullscreen else window.show()
    try:
        return application.exec()
    finally:
        controller.close()
        if isinstance(transport, DemoTransport):
            transport.close()
        close_location()


if __name__ == "__main__":
    raise SystemExit(main())
