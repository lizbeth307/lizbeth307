"""Portable safety state machine. Time is *unwrapped*, monotonically increasing ms.

No hardware, wire parser, filesystem, or receiver dependencies. The caller must
sample inputs and apply outputs at least every 20 ms. See README.md for limits.
"""

UINT32_MAX = 0xffffffff
HB_TIMEOUT_MS = 750
WARM_GUARD_MS = 100
CONFIG_TIMEOUT_MS = 1000
SENSOR_MAX_AGE_MS = 250
Q6A_OFF_DELAY_MS = 3000
OFF_NOW_DELAY_MS = 20000
ARM_OFF_HB_LOSS_MS = 60000
UV_DWELL_MS = 5000
OFF_PULSE_MS = 250
# PWR_ON_KEY boot assist (STACK D3, bench B11): GP12 drives Q302, which pulls
# J21 pin 3 low. STACK allows 0.8-1.0 s, never 2 s; a 6 s hold is the Q6A
# hard power-off. Retries are bounded per Pico boot or physical restart.
KEY_WAIT_MS = 1500
KEY_PULSE_MS = 900
KEY_RETRY_MS = 5000
KEY_MAX_PULSES = 3


def _number(value, low, high):
    return (type(value) in (int, float) and value == value
            and low <= value <= high)


class Supervisor:
    def __init__(self, calibration_valid=False, session_factory=None,
                 hardware_commissioned=False):
        # A remote ARM can never override either locally established gate.
        self.calibration_valid = calibration_valid is True
        self.hardware_commissioned = hardware_commissioned is True
        self._session_factory = session_factory
        self._session_counter = 0
        self.session = 0
        self._rotate_session()
        self.state = "SAFE"
        self.fault = None
        self.reject_reason = None
        self.last_host_seq = -1
        self._now = 0
        self._started = False
        self._inputs_at = None
        self._inputs = {}
        self._last_hb = None
        self._soc_temp = None
        self._arm_at = None
        self._warm_hbs = 0
        self._warm_hb_at = None
        self._config_at = None
        self._shutdown_at = None
        self._shutdown_hb_at = None
        self._off_now_at = None
        self._off_at = None
        self._q6a_seen = False
        self._q6a_off_at = None
        self._key_from = None  # Wait reference for the next key pulse; None ends the assist.
        self._key_at = None    # Start of the key pulse in progress.
        self.key_pulses = 0
        self._uv_at = None
        self._button_raw = False
        self._button_changed_at = 0
        self._button_stable = False
        self._button_down_at = None
        self._button_handled = False
        self._fan_latch = True
        self._blower_latch = True
        self._disp_hot = True  # Unknown panel temperature keeps DISP12 off.
        self._thermal_trip = False  # CASE_HOT/FAN_STALLED trip keeps DISP12 off.
        self.events = []
        self.outputs = {}
        self._render_outputs()

    def _rotate_session(self):
        previous = self.session
        candidate = None
        if self._session_factory is not None:
            candidate = self._session_factory()
        if (type(candidate) is not int or not 1 <= candidate <= UINT32_MAX
                or candidate == previous):
            # Deterministic fallback is for model tests only. The adapter supplies
            # os.urandom; a session nonce is replay separation, not authentication.
            self._session_counter += 1
            candidate = ((previous + self._session_counter) % UINT32_MAX) + 1
        self.session = candidate
        self.last_host_seq = -1

    def _event(self, name, **fields):
        event = {"event": name}
        event.update(fields)
        # Bound memory if the caller fails to drain events.
        if len(self.events) >= 16:
            self.events.pop(0)
        self.events.append(event)

    def drain_events(self):
        result = self.events
        self.events = []
        return result

    def _clock(self, now_ms):
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be a nonnegative unwrapped integer")
        if self._started and now_ms < self._now:
            self._trip("CLOCK_REVERSED")
            return False
        self._now = now_ms
        self._started = True
        return True

    def _hb_fresh(self):
        return self._last_hb is not None and self._now - self._last_hb < HB_TIMEOUT_MS

    def _sensors_valid(self):
        return (_number(self._inputs.get("battery_mv"), 8000, 17500)
                and _number(self._inputs.get("panel_temp_c"), -20, 120)
                and _number(self._inputs.get("case_temp_c"), -20, 120))

    def _readiness(self, ignore_battery=False):
        if not self.hardware_commissioned:
            return "NOT_COMMISSIONED"
        if not self.calibration_valid:
            return "ADC_UNCALIBRATED"
        if self._inputs_at is None or self._now - self._inputs_at > SENSOR_MAX_AGE_MS:
            return "SENSOR_STALE"
        if self._inputs.get("q6a_on") is not True:
            return "Q6A_OFF"
        if not self._sensors_valid():
            return "SENSOR_INVALID"
        if not ignore_battery and self._inputs["battery_mv"] <= 13050:
            return "BATTERY_LOW"
        if self._inputs["panel_temp_c"] >= 68:
            return "PANEL_HOT"
        # This is the enclosure NTC, not the separate battery-cell NTC.
        if self._inputs["case_temp_c"] > 60:
            return "CASE_HOT"
        if self._inputs.get("fan_stalled") is True:
            return "FAN_STALLED"
        return None

    def _trip(self, reason):
        if self.state in ("OFF", "SHUTTING_DOWN"):
            return
        if self.state == "TRIPPED" and self.fault == reason:
            return
        self.state = "TRIPPED"
        self.fault = reason
        if reason in ("CASE_HOT", "FAN_STALLED"):
            # Hot enclosure or lost airflow: drop the display load until the
            # fault clears (ARM/restart); a later HOST_TRIP relabel cannot relight.
            self._thermal_trip = True
        self._arm_at = self._config_at = None
        self._warm_hbs = 0
        self._last_hb = None
        self._soc_temp = None
        self._rotate_session()
        self._event("TRIP", fault=reason)
        self._render_outputs()

    def _request_shutdown(self, reason):
        if self.state in ("SHUTTING_DOWN", "OFF"):
            return
        self.state = "SHUTTING_DOWN"
        self.fault = reason
        self._shutdown_at = self._now
        self._shutdown_hb_at = self._last_hb
        self._off_now_at = None  # Each shutdown gets its own full OFF_NOW grace.
        self._event("SHUTDOWN_REQUEST", reason=reason)

    def _cut_power(self, reason):
        if self.state == "OFF":
            return
        self.state = "OFF"
        self.fault = reason
        self._off_at = self._now
        self._last_hb = None
        self._rotate_session()
        self._event("POWER_CUT", reason=reason)

    def receive(self, frame, now_ms):
        """Return True for an accepted host frame. Replays never refresh HB."""
        if not self._clock(now_ms):
            return False
        # Enforce deadlines before processing a packet that arrived too late.
        self._advance()
        self._render_outputs()
        if (not isinstance(frame, dict) or type(frame.get("v")) is not int or frame["v"] != 1
                or type(frame.get("s")) is not int or frame["s"] != self.session
                or type(frame.get("q")) is not int
                or not 0 <= frame["q"] <= UINT32_MAX
                or frame["q"] <= self.last_host_seq
                or not isinstance(frame.get("p"), dict)):
            self.reject_reason = "FRAME_OR_REPLAY"
            return False
        kind = frame.get("t")
        if kind not in ("HB", "ARM", "CONFIGURED", "TRIP", "SHUTDOWN"):
            self.reject_reason = "HOST_TYPE"
            return False
        if frame["q"] == UINT32_MAX:
            self._trip("SEQUENCE_EXHAUSTED")
            self.reject_reason = "SEQUENCE_EXHAUSTED"
            return False
        self.last_host_seq = frame["q"]
        payload = frame["p"]
        self.reject_reason = None
        accepted = True
        if kind == "HB":
            self._last_hb = self._now
            temp = payload.get("soc_temp_c")
            self._soc_temp = temp if _number(temp, -40, 130) else None
            if self.state == "WARMING" and self._warm_hb_at != self._now:
                self._warm_hbs += 1
                self._warm_hb_at = self._now
            if self.state == "SHUTTING_DOWN":
                self._shutdown_hb_at = self._now
        elif kind == "ARM":
            reason = self._readiness()
            if self.state not in ("SAFE", "TRIPPED"):
                reason = "STATE_REQUIRES_NEW_SESSION" if self.state == "OFF" else "ALREADY_ARMED"
            if payload.get("qualified") is not True:
                reason = "HOST_NOT_QUALIFIED"
            if reason is not None:
                self.reject_reason = reason
                self._event("ARM_REFUSED", reason=reason)
                accepted = False
            else:
                self.state = "WARMING"
                self.fault = None
                self._thermal_trip = False  # Readiness above proved case <=60 C, no stall.
                self._arm_at = self._now
                self._last_hb = None
                self._warm_hbs = 0
                self._warm_hb_at = None
                self._soc_temp = None
                self._event("ARM_ACCEPTED")
        elif kind == "CONFIGURED":
            if self.state != "CONFIGURING" or payload.get("safe") is not True:
                self.reject_reason = "CONFIGURED_UNEXPECTED_OR_UNSAFE"
                accepted = False
                if self.state in ("WARMING", "CONFIGURING", "ACTIVE"):
                    self._trip("CONFIGURATION_INVALID")
            else:
                self.state = "ACTIVE"
                self._event("ACTIVE")
        elif kind == "TRIP":
            self._trip("HOST_TRIP")
        elif kind == "SHUTDOWN":
            phase = payload.get("phase")
            if phase == "ARM_OFF":
                self._request_shutdown("HOST_SHUTDOWN")
            elif phase == "OFF_NOW" and self.state == "SHUTTING_DOWN":
                # Repeated OFF_NOW must never postpone an existing cutoff.
                if self._off_now_at is None:
                    self._off_now_at = self._now
                    self._event("OFF_NOW_ACCEPTED", delay_ms=OFF_NOW_DELAY_MS)
            else:
                self.reject_reason = "SHUTDOWN_PHASE"
                accepted = False
        self._advance()
        self._render_outputs()
        return accepted

    def step(self, now_ms, inputs):
        if not self._clock(now_ms):
            return self.outputs
        # A fresh sample is required on every call, including explicit None on
        # failed conversion. Never retain the last plausible sensor value.
        self._inputs = dict(inputs)
        for field, low, high in (("battery_mv", 8000, 17500),
                                 ("panel_temp_c", -20, 120),
                                 ("case_temp_c", -20, 120)):
            if not _number(self._inputs.get(field), low, high):
                self._inputs[field] = None
        if self._inputs_at is None:
            self._key_from = self._now  # First sample after boot starts the 3V3 wait.
        self._inputs_at = self._now
        if self._inputs.get("q6a_on") is True:
            self._q6a_seen = True
            self._q6a_off_at = None
        elif self._q6a_seen and self._q6a_off_at is None:
            self._q6a_off_at = self._now
        self._button_step(self._inputs.get("button_pressed") is True)
        self._advance()
        self._key_step()
        self._render_outputs()
        return self.outputs

    def _key_battery_ok(self):
        # A calibrated Pico presses only above the 13.05 V cutoff: below it the
        # no-HB UV fallback would cut a booting Q6A. Uncalibrated, no battery
        # value is trusted; E1's hardware UV trip still applies.
        if not self.calibration_valid:
            return True
        battery = self._inputs.get("battery_mv")
        return _number(battery, 8000, 17500) and battery > 13050

    def _key_release(self):
        self._key_at = None
        self._key_from = self._now
        if self.key_pulses >= KEY_MAX_PULSES:
            self._key_from = None
            self._event("Q6A_KEY_GAVE_UP", pulses=self.key_pulses)

    def _key_step(self):
        # Boot assist only: Q6A 3V3 never seen since this boot or physical
        # restart. A seen Q6A (even if lost again) or any state but SAFE ends it.
        if self._q6a_seen or self.state != "SAFE":
            self._key_from = self._key_at = None
            return
        if self._key_from is None:
            return
        # The case button reaches J21 pin 3 itself through D303: never add a
        # pulse to an operator press, and give the PMIC the full wait after it.
        hold = self._inputs.get("button_pressed") is True or not self._key_battery_ok()
        if self._key_at is not None:
            if hold or self._now - self._key_at >= KEY_PULSE_MS:
                self._key_release()
            return
        if hold:
            self._key_from = self._now
        elif self._now - self._key_from >= (KEY_RETRY_MS if self.key_pulses else KEY_WAIT_MS):
            self._key_at = self._now
            self.key_pulses += 1
            self._event("Q6A_KEY_PULSE", pulse=self.key_pulses)

    def _button_step(self, pressed):
        if pressed != self._button_raw:
            self._button_raw = pressed
            self._button_changed_at = self._now
        if self._now - self._button_changed_at < 30:
            return
        if pressed != self._button_stable:
            self._button_stable = pressed
            if pressed:
                self._button_down_at = self._now
                self._button_handled = False
                if (self.state == "OFF" and self._sensors_valid()
                        and self._inputs["battery_mv"] >= 13600):
                    # Physical button is also wired to Pololu A and PMIC key.
                    # This clears the software latch; it never powers on remotely.
                    self.state = "SAFE"
                    self.fault = None
                    self._thermal_trip = False
                    self._q6a_seen = False
                    self._q6a_off_at = None
                    # A fresh, bounded PWR_ON_KEY assist, as after a LAB5 boot.
                    self._key_from, self._key_at, self.key_pulses = self._now, None, 0
                    self._off_at = None
                    self._off_now_at = self._shutdown_at = self._shutdown_hb_at = None
                    self._rotate_session()
                    self._button_handled = True
                    self._event("PHYSICAL_RESTART")
            elif not self._button_handled:
                self._event("POWER_BUTTON")
        if (pressed and not self._button_handled and self._button_down_at is not None
                and self._now - self._button_down_at >= 1500):
            self._button_handled = True
            self._request_shutdown("BUTTON")

    def _advance(self):
        armed = self.state in ("WARMING", "CONFIGURING", "ACTIVE")
        if armed:
            # Falling below UV threshold does not bypass the required dwell;
            # Linux handles live-HB undervoltage, Pico covers absent-HB fallback.
            # Skip only that gate: thermal/fan gates after it must still trip.
            reason = self._readiness(ignore_battery=True)
            if reason is not None:
                self._trip(reason)
            elif (self._last_hb is None and self._now - self._arm_at >= HB_TIMEOUT_MS
                  or self._last_hb is not None and not self._hb_fresh()):
                self._trip("HEARTBEAT_TIMEOUT")
            elif self.state == "WARMING" and self._warm_hbs >= 2 and self._now - self._arm_at >= WARM_GUARD_MS:
                self.state = "CONFIGURING"
                self._config_at = self._now
                self._event("RESET_RELEASED", configure_within_ms=CONFIG_TIMEOUT_MS)
            elif self.state == "CONFIGURING" and self._now - self._config_at >= CONFIG_TIMEOUT_MS:
                self._trip("CONFIGURATION_TIMEOUT")
        if (self._q6a_off_at is not None and self.state != "OFF"
                and self._now - self._q6a_off_at >= Q6A_OFF_DELAY_MS):
            self._cut_power("Q6A_POWER_OFF")
        if self.state == "SHUTTING_DOWN":
            reference = self._shutdown_hb_at
            if reference is None or reference < self._shutdown_at:
                reference = self._shutdown_at
            if self._off_now_at is not None and self._now - self._off_now_at >= OFF_NOW_DELAY_MS:
                self._cut_power("OFF_NOW_GRACE_ELAPSED")
            elif self._now - reference >= ARM_OFF_HB_LOSS_MS:
                self._cut_power("ARM_OFF_HEARTBEAT_LOST")
        low = (_number(self._inputs.get("battery_mv"), 8000, 17500)
               and self._inputs["battery_mv"] <= 13050 and not self._hb_fresh()
               and self.calibration_valid)
        if low:
            if self._uv_at is None:
                self._uv_at = self._now
            elif self._now - self._uv_at >= UV_DWELL_MS:
                self._cut_power("UNDERVOLTAGE_NO_HEARTBEAT")
        else:
            self._uv_at = None

    def _render_outputs(self):
        active = self.state == "ACTIVE"
        q6a_on = self._inputs.get("q6a_on") is True
        cooling_safe = active and self._sensors_valid() and self._hb_fresh()
        if cooling_safe:
            if self._soc_temp is None or self._soc_temp >= 60:
                self._fan_latch = True
            elif self._soc_temp <= 50:
                self._fan_latch = False
            panel = self._inputs["panel_temp_c"]
            if panel >= 45:
                self._blower_latch = True
            elif panel <= 40:
                self._blower_latch = False
        else:
            self._fan_latch = self._blower_latch = True
        panel = self._inputs.get("panel_temp_c")
        brightness = 100
        if _number(panel, -20, 120):
            brightness = 20 if panel >= 68 else 50 if panel >= 60 else 100
        # DISP12 is the operator console, not an ARM output. Missing, invalid or
        # stale panel NTC counts as hot; it re-enables only at <=60 C. A CASE_HOT
        # or FAN_STALLED trip also removes it until that fault is cleared.
        if (self._inputs_at is None or self._now - self._inputs_at > SENSOR_MAX_AGE_MS
                or not _number(panel, -20, 120) or panel >= 68):
            self._disp_hot = True
        elif panel <= 60:
            self._disp_hot = False
        # PWR_ON_KEY needs a fresh sample with Q6A 3V3 absent and is time-bounded
        # here too, so a missed step() cannot stretch the press.
        key = (self._key_at is not None and self.state == "SAFE" and not q6a_on
               and self._now - self._key_at < KEY_PULSE_MS
               and self._inputs_at is not None
               and self._now - self._inputs_at <= SENSOR_MAX_AGE_MS)
        self.outputs = {
            "mcp_reset": not (self.state in ("CONFIGURING", "ACTIVE")),
            "disp_en": (q6a_on and not self._disp_hot and not self._thermal_trip
                        and self.state not in ("OFF", "SHUTTING_DOWN")),
            "safe_boot": not active,
            "fan_en": self._fan_latch,
            "blower_en": self._blower_latch,
            "pico_off": self.state == "OFF" and self._now - self._off_at < OFF_PULSE_MS,
            "q6a_key": key,
            "led": not active,
            "brightness_limit_pct": brightness,
        }

    def status(self):
        return {"state": self.state, "fault": self.fault,
                "mcp_reset": self.outputs["mcp_reset"],
                "calibration_valid": self.calibration_valid,
                "hardware_commissioned": self.hardware_commissioned,
                "reject_reason": self.reject_reason,
                "hb_fresh": self._hb_fresh(),
                "q6a_on": self._inputs.get("q6a_on") is True,
                "battery_mv": self._inputs.get("battery_mv"),
                "panel_temp_c": self._inputs.get("panel_temp_c"),
                "case_temp_c": self._inputs.get("case_temp_c"),
                "fan_stalled": self._inputs.get("fan_stalled") is True,
                "brightness_limit_pct": self.outputs["brightness_limit_pct"],
                "q6a_key_pulses": self.key_pulses}
