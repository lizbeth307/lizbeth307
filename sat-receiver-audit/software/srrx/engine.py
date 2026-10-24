"""Single-writer host state machine. Requests never write GPIO directly."""
from .policy import SafetyPolicy, CAPS, _number

BRANCHES = {"LNA1": 4.5, "LNA2": 4.5, "LNA3": 4.5, "LNA4": 4.5,
            "LNB": 13.2, "BONI": 13.8, "SB_LNA": 5.0, "RTLA": 5.0,
            "RTLB": 5.0, "HFP": 5.0, "LIME3V3": 3.3, "T7": 5.0,
            "LABPORT": 5.0, "AUX12": 12.0}
# HELLO omits the sensor readings to fit its qualification_record in 512 bytes
# (firmware/pico/main.py HELLO_FIELDS); a same-session HELLO keeps these while
# the STATUS that carried them is at most 500 ms old.
STATUS_ONLY = ("battery_mv", "panel_temp_c", "case_temp_c", "fan_stalled",
               "brightness_limit_pct", "adc_raw")


def _sha256_hex(value):
    return type(value) is str and len(value) == 64 and set(value) <= set("0123456789abcdef")


class Engine:
    def __init__(self, hardware, link, *, simulated=True, acceptance=None, telemetry_reader=None,
                 soc_temp_reader=None, qualification_record=None):
        self.hardware, self.link = hardware, link
        self.simulated, self.acceptance = simulated, acceptance
        # sha256 of the exact acceptance bytes (commissioning.load_acceptance_bound),
        # as srrx.provision sealed it into the Pico commissioning.json. Without
        # it a hardware HELLO can never verify, so ARM stays refused.
        self.qualification_record = qualification_record if _sha256_hex(qualification_record) else None
        self.qualification_ok = False
        self.telemetry_reader = telemetry_reader
        self.soc_temp_reader = soc_temp_reader
        self.soc_temp = self.soc_temp_ms = None
        self.policy = SafetyPolicy(hardware)
        self.session, self.rx_seq, self.tx_seq = None, -1, 0
        self.pico = {}
        self.last_status_ms = self.last_hb_ms = self.last_telemetry_ms = None
        # A HELLO refreshes the session and state fields only; the readings age
        # from the last frame that carried them (STATUS).
        self.last_readings_ms = None
        self.last_trip_tx_ms = self.arm_requested_ms = None
        self.pending_arm, self.configured = False, False
        self.last_error, self.closed = None, False
        self.now_ms = 0
        self.arm_owner = None
        self.sim_overrides = {}
        self.events = []
        self.uv_since = None
        self.identity_ok = simulated
        self.last_tick_ms = None
        self.imu_sample = None
        self.hmi_sample = None
        self.requested_mode = "field"
        if simulated:
            # These are explicitly synthetic, never written into acceptance.
            self.policy.configure_limits({b: {"baseline_a": min(.1, CAPS[b][0] * .5),
                "max_current_a": min(CAPS[b][0] * .8, min(.1, CAPS[b][0] * .5) * 1.2),
                "min_voltage_v": v * .9, "max_voltage_v": min(CAPS[b][1], v * 1.05)} for b, v in BRANCHES.items()})
            self.policy.configure_power_budget(always_on_a=.6)
        elif acceptance:
            self.policy.configure_limits(acceptance.get("branch_limits", {}))
            self.policy.configure_power_budget(**{k: acceptance["lab5_budget"][k] for k in ("always_on_a", "max_lab5_a")})

    def _send(self, kind, payload=None):
        if self.session is None:
            raise RuntimeError("No fresh Pico session")
        if self.tx_seq >= 0xffffffff:
            raise RuntimeError("Pico session sequence exhausted; explicit recovery required")
        frame = {"v": 1, "t": kind, "s": self.session, "q": self.tx_seq, "p": payload or {}}
        self.link.send(frame, self.now_ms)
        self.tx_seq += 1

    def trip(self, reason, notify=True):
        self.pending_arm, self.configured = False, False
        self.last_error = str(reason)
        if not self.events or self.events[-1].get("reason") != str(reason):
            self.events.append({"at_ms": self.now_ms, "reason": str(reason)})
            self.events = self.events[-32:]
        self.policy.trip(str(reason))
        if notify and self.session is not None:
            self.last_trip_tx_ms = self.now_ms
            try:
                self._send("TRIP", {"reason": str(reason)[:80]})
            except (OSError, ValueError, RuntimeError):
                pass

    def _report_age_ms(self):
        """Age of the Pico report: the older of its last frame and its readings."""
        if self.last_status_ms is None or self.last_readings_ms is None:
            return None
        return self.now_ms - min(self.last_status_ms, self.last_readings_ms)

    def _receive(self, frame):
        if frame["t"] not in {"HELLO", "STATUS", "EVENT"}:
            return
        status = frame["p"]
        new_session = frame["s"] != self.session
        if new_session:
            if frame["t"] != "HELLO":
                return
            self.trip("new_pico_session", notify=False)
            self.imu_sample = self.hmi_sample = None
            self.session, self.rx_seq, self.tx_seq = frame["s"], -1, 0
            self.last_hb_ms = self.last_readings_ms = None
        if frame["q"] <= self.rx_seq:
            return
        if frame["t"] == "HELLO" and not self.simulated:
            bound = bool(self.acceptance and
                status.get("serial") == self.acceptance["pico_serial"] and
                status.get("calibration_crc32") == self.acceptance["battery_adc"]["record"]["crc32"])
            # The Pico reports its digest only with a valid local commissioning
            # record. Equality pairs this Pico with exactly these acceptance bytes;
            # like the UART CRC it detects a wrong pairing, not a forged Pico.
            self.qualification_ok = bool(bound and self.qualification_record is not None
                and status.get("hardware_commissioned") is True
                and status.get("qualification_record") == self.qualification_record)
            self.identity_ok = self.qualification_ok
            if not bound:
                self.trip("pico_identity_or_calibration_mismatch")
                return
            if not self.qualification_ok:
                self.trip("pico_qualification_record_mismatch")
                return
        if frame["t"] == "EVENT":
            self.rx_seq = frame["q"]
            self.events.append({"at_ms": self.now_ms, "event": status})
            self.events = self.events[-32:]
            if isinstance(status.get("imu"), dict):
                self.imu_sample = (self.now_ms, dict(status["imu"]))
            if "hmi" in status:
                self.hmi_sample = (self.now_ms, dict(status["hmi"])) if type(status["hmi"]) is dict else None
            return
        if type(status.get("state")) is not str or status["state"] not in {"SAFE", "WARMING", "CONFIGURING", "ACTIVE", "TRIPPED", "SHUTTING_DOWN", "OFF"}:
            self.trip("invalid_pico_state")
            return
        if type(status.get("mcp_reset")) is not bool:
            self.trip("invalid_pico_reset_status")
            return
        if status["state"] == "ACTIVE" and status["mcp_reset"]:
            self.trip("contradictory_pico_state")
            return
        if status["state"] == "ACTIVE" and any(status.get(k) is not True for k in ("q6a_on", "calibration_valid", "hardware_commissioned", "hb_fresh")):
            self.trip("unqualified_pico_active_state")
            return
        prev = self.pico
        if "battery_mv" in status:
            self.last_readings_ms = self.now_ms  # STATUS; a simulator HELLO may carry them too.
        elif (frame["t"] == "HELLO" and not new_session and self.last_readings_ms is not None
                and self.now_ms - self.last_readings_ms <= 500):
            # Keep this session's fresh STATUS readings; a repeated HELLO must not
            # blank battery/temperature rows for up to 200 ms each second. Older
            # ones are dropped: a HELLO-only stream never passes as telemetry.
            status = dict({k: prev[k] for k in STATUS_ONLY if k in prev}, **status)
        self.rx_seq, self.pico, self.last_status_ms = frame["q"], status, self.now_ms
        # A repeat of the same latched report is no news. It can predate a
        # queued ARM, and re-tripping would rerun all_off against MCPs that the
        # Pico already holds in RESET. Every Pico trip rotates the session.
        if status["state"] in {"TRIPPED", "SHUTTING_DOWN", "OFF"} and (
                self.configured or self.policy.armed or prev.get("state") != status["state"]
                or prev.get("fault") != status.get("fault")):
            self.trip("pico_" + str(status.get("fault") or status["state"]), notify=False)

    def tick(self, now_ms):
        self.now_ms = int(now_ms)
        try:
            if self.last_tick_ms is not None and self.now_ms - self.last_tick_ms > 100:
                self.imu_sample = None
                self.hmi_sample = None
                # A delayed host must not relabel UART-queued orientation as
                # newly acquired. HELLO repeats allow session resynchronization.
                if hasattr(self.link, "discard_input"):
                    self.link.discard_input()
            self.last_tick_ms = self.now_ms
            for frame in self.link.poll(self.now_ms):
                self._receive(frame)
            age = self._report_age_ms()
            fresh = age is not None and age <= 500
            if (self.session is not None and not (self.pending_arm or self.configured)
                    and self.pico.get("state") in {"WARMING", "CONFIGURING", "ACTIVE"}):
                # Our TRIP was lost: withhold HB so the independent Pico timeout
                # asserts MCP RESET, and repeat TRIP until the Pico reports it.
                if self.last_trip_tx_ms is None or self.now_ms - self.last_trip_tx_ms >= 200:
                    self.last_trip_tx_ms = self.now_ms
                    self._send("TRIP", {"reason": "host_not_armed"})
            elif self.session is not None and fresh and (self.last_hb_ms is None or self.now_ms - self.last_hb_ms >= 200):
                # A live HB leaves undervoltage to labd, so it needs fresh readings.
                # Without them HB stops and the Pico's no-HB fallbacks act (HB
                # timeout, 5 s UV cut), even while HELLO frames still arrive.
                # The reader must not block this 20 ms tick: labd passes a SocTempSampler
                # whose sysfs reads run on its own thread; this only takes its cached value.
                if self.soc_temp_reader and (self.soc_temp_ms is None or self.now_ms - self.soc_temp_ms >= 1000):
                    self.soc_temp, self.soc_temp_ms = self._read_soc_temp(), self.now_ms
                # Omitted when unknown; the Pico then keeps its fan forced on.
                self._send("HB", None if self.soc_temp is None else {"soc_temp_c": self.soc_temp})
                self.last_hb_ms = self.now_ms
            if not fresh:
                # Also a HELLO-only stream: readiness off and the UV dwell kept.
                if self.configured or self.pending_arm:
                    self.trip("pico_status_timeout")
                self.policy.set_readiness(pico_active=False, commissioned=False)
                if self.policy.gnss_reset["state"] == "ASSERTED":
                    self.policy.tick(self.now_ms)  # A GNSS reset release never waits for Pico status.
                return
            state = self.pico.get("state")
            if self.pending_arm and state in {"SAFE", "TRIPPED"} and self.now_ms - self.arm_requested_ms >= 1000:
                # Refused or lost ARM (the Pico's ARM_REFUSED event names why).
                # A late acceptance is revoked by the not-owned path above.
                self.trip("pico_arm_not_acknowledged", notify=False)
            if state == "CONFIGURING" and self.pending_arm and not self.configured:
                if self.pico["mcp_reset"]:
                    raise RuntimeError("Pico has not released MCP reset")
                if not self.simulated:
                    self.hardware.mapping["reset_confirmed"] = True
                self.hardware.initialize_safe()
                if self.telemetry_reader and hasattr(self.telemetry_reader, "configure"):
                    self.telemetry_reader.configure()
                self.configured = True
                self._send("CONFIGURED", {"safe": True})
            active = state == "ACTIVE" and self.configured
            self.policy.set_readiness(pico_active=active, commissioned=self.identity_ok and (self.simulated or bool(self.acceptance)))
            if self.now_ms - (self.last_telemetry_ms or -1000) >= 100:
                if self.simulated:
                    samples = {b: {"current_a": self.policy.limits[b]["baseline_a"] if self.hardware.outputs.get("EN_" + b) else 0.0,
                        "voltage_v": v, "timestamp_ms": self.now_ms} for b, v in BRANCHES.items()}
                elif self.telemetry_reader:
                    samples = self.telemetry_reader.poll(self.now_ms)
                else:
                    samples = {}
                self.policy.refresh_telemetry(samples, self.now_ms)
                self.last_telemetry_ms = self.now_ms
            if self.configured:
                if self.simulated:
                    self.hardware.set_inputs({"PG_LNB": self.hardware.outputs["EN_LNB"],
                        "PG_BONI": self.hardware.outputs["EN_BONI"],
                        "PTC_AUX": self.hardware.outputs["EN_AUX12"],
                        "OVP_LNB_N": self.hardware.outputs["EN_LNB"], **self.sim_overrides})
                self.policy.refresh_inputs(self.hardware.read_inputs(), self.now_ms)
            if active and self.pending_arm:
                if not self.policy.clear_fault(self.now_ms):
                    raise RuntimeError("Physical faults do not permit explicit recovery")
                result = self.policy.command("mode", self.requested_mode, self.now_ms)
                if not result.get("ok"):
                    raise RuntimeError("Requested operating mode refused")
                result = self.policy.command("lease", {"owner": self.arm_owner, "ttl_ms": 5000}, self.now_ms)
                if result.get("ok"):
                    result = self.policy.command("arm", True, self.now_ms)
                if not result.get("ok"):
                    raise RuntimeError("Policy arm refused: " + str(result.get("error")))
                self.pending_arm = False
            self.policy.tick(self.now_ms)
            if active and self.policy.status().get("fault"):
                self.trip("host_policy_fault")
            low = self.pico.get("battery_mv")
            if "battery_mv" not in self.pico:
                pass  # A report without the reading is no news for the dwell.
            elif self.pico.get("q6a_on") is True and self.pico.get("calibration_valid") is True and type(low) in {int, float} and 8000 <= low <= 13050:
                if self.uv_since is None:
                    self.uv_since = self.now_ms
                elif self.now_ms - self.uv_since >= 5000:
                    self.policy.trip("undervoltage")
                    self._send("SHUTDOWN", {"phase": "ARM_OFF"})
            else:
                self.uv_since = None
        except (OSError, ValueError, RuntimeError) as exc:
            self.trip(type(exc).__name__ + ": " + str(exc))

    def _read_soc_temp(self):
        try:
            value = self.soc_temp_reader()
        except Exception:
            return None
        return round(float(value), 1) if _number(value) and -40 <= value <= 130 else None

    def request(self, request, now_ms=None):
        if now_ms is not None:
            # Time each request when it is handled, not at the earlier tick.
            self.now_ms = max(self.now_ms, int(now_ms))
        if not isinstance(request, dict):
            return {"ok": False, "error": "request must be an object"}
        op = request.get("op")
        if type(op) is not str:
            return {"ok": False, "error": "operation must be a string"}
        owner = request.get("_owner", "direct-test")
        if op == "status":
            return {"ok": True, "data": self.status()}
        if op in {"arm", "recover", "mode", "control", "relay", "route", "confirmations"} and self.policy.owner not in (None, owner):
            if op != "control" or request.get("value") is not False:
                return {"ok": False, "error": "another local operator owns the lease"}
        if op in {"arm", "recover"}:
            age = self._report_age_ms()
            if self.session is None or age is None or age > 500:
                return {"ok": False, "error": "fresh Pico HELLO/status required"}
            if self.pico.get("state") not in {"SAFE", "TRIPPED"}:
                return {"ok": False, "error": "Pico is not ready for an explicit arm"}
            if not self.simulated and not self.acceptance:
                return {"ok": False, "error": "hardware acceptance missing"}
            if not self.identity_ok:
                return {"ok": False, "error": "live Pico serial/calibration/qualification binding failed"}
            if self.pending_arm and self.arm_owner != owner:
                return {"ok": False, "error": "another local operator's arm is pending"}
            self.pending_arm, self.configured = True, False
            self.arm_owner, self.arm_requested_ms = owner, self.now_ms
            self._send("ARM", {"qualified": True})
            self.last_error = None
            return {"ok": True, "state": "arm_requested"}
        if op == "disarm":
            self.trip("operator_disarm")
            return {"ok": True}
        if op == "shutdown":
            self.policy.trip("operator_shutdown")
            self._send("SHUTDOWN", {"phase": "ARM_OFF"})
            return {"ok": True, "state": "shutdown_requested", "os_poweroff_executed": False}
        if op == "off_now":
            if self.pico.get("state") != "SHUTTING_DOWN":
                return {"ok": False, "error": "ARM_OFF must be acknowledged before OFF_NOW"}
            self._send("SHUTDOWN", {"phase": "OFF_NOW"})
            return {"ok": True, "power_cut_grace_ms": 20000}
        if op == "lease":
            value = request.get("value")
            if not isinstance(value, dict) or set(value) != {"ttl_ms"}:
                return {"ok": False, "error": "lease requires {ttl_ms:1..5000}; owner is assigned by the server"}
            if self.pending_arm and self.arm_owner != owner:
                return {"ok": False, "error": "another local operator's arm is pending"}
            return self.policy.command("lease", {"owner": owner, "ttl_ms": value["ttl_ms"]}, self.now_ms)
        if op == "mode":
            value = request.get("value")
            if type(value) is not str or value not in {"field", "lab"}:
                return {"ok": False, "error": "mode must be field or lab"}
            if self.policy.armed or self.pending_arm:
                return {"ok": False, "error": "disarm before changing operating mode"}
            self.requested_mode = value
            return {"ok": True, "mode": value, "applied_on_next_arm": True}
        if op == "control":
            name, value = request.get("name"), request.get("value")
            if not isinstance(name, str) or not name.startswith("EN_") or type(value) is not bool:
                return {"ok": False, "error": "control requires a named EN_ output and boolean value"}
            return self.policy.command(name, value, self.now_ms)
        if op in {"relay", "confirmations"}:
            return self.policy.command(op, request.get("value"), self.now_ms)
        if op == "gnss_reset":
            # Mutating: only the caller's own unexpired lease (no lease is no owner).
            # The policy rechecks fault, width, spacing, rate and the MCP image.
            if (self.policy.owner != owner or self.policy.lease_deadline_ms is None
                    or self.now_ms >= self.policy.lease_deadline_ms):
                return {"ok": False, "error": "gnss_reset requires the caller's own valid lease"}
            if not self.configured or self.pending_arm:
                return {"ok": False, "error": "gnss_reset requires configured MCP outputs and no pending arm"}
            if (self.pico.get("mcp_reset") is not False or self.last_status_ms is None
                    or not 0 <= self.now_ms - self.last_status_ms <= 500):
                return {"ok": False, "error": "gnss_reset requires fresh Pico status with MCP RESET released"}
            return self.policy.command("gnss_reset", request.get("value"), self.now_ms)
        if op == "route":
            receiver = request.get("receiver")
            if type(receiver) is not str or receiver not in {"RTLA", "RTLB", "LIME"}:
                return {"ok": False, "error": "unknown receiver"}
            return self.policy.command("route_" + receiver, request.get("value"), self.now_ms)
        if op == "sim":
            if not self.simulated:
                return {"ok": False, "error": "simulation controls unavailable on hardware"}
            name, value = request.get("name"), request.get("value")
            if type(name) is not str:
                return {"ok": False, "error": "simulation variable must be a string"}
            if name == "drop_link" and type(value) is bool:
                self.link.drop_link = value
            elif name in {"battery_mv", "panel_temp_c", "case_temp_c"} and _number(value):
                self.link.inputs[name] = value
            elif name == "q6a_on" and type(value) is bool:
                self.link.inputs[name] = value
            elif isinstance(name, str) and name.startswith(("FAULT_", "FLT_", "DCS_", "PG_")) and type(value) is bool and hasattr(self.hardware, "inputs"):
                if name not in self.hardware.inputs:
                    return {"ok": False, "error": "unknown simulated input"}
                self.hardware.inputs[name] = value
                self.sim_overrides[name] = value
            else:
                return {"ok": False, "error": "unknown simulated variable or invalid type"}
            return {"ok": True}
        return {"ok": False, "error": "unknown operation"}

    def _hmi_status(self):
        invalid = {"ok": False, "fresh": False, "age_ms": None, "keys": 0,
                   "presses": None, "encoders": None, "lux": None, "lux_valid": False,
                   "lux_age_ms": None, "sequence": None, "generation": None, "error": "HMI_NOT_FRESH"}
        if self.hmi_sample is None:
            return invalid
        received, sample = self.hmi_sample
        fields = {"ok", "fresh", "age_ms", "keys", "presses", "encoders", "lux",
                  "lux_valid", "lux_age_ms", "sequence", "generation", "error"}
        source_age = sample.get("age_ms")
        age = source_age + self.now_ms - received + 100 if type(source_age) is int else 500
        if (set(sample) != fields or sample.get("ok") is not True or sample.get("fresh") is not True
                or type(source_age) is not int or not 0 <= source_age < 500 or not 0 <= age < 500
                or self.last_status_ms is None or not 0 <= self.now_ms-self.last_status_ms <= 500
                or type(sample.get("keys")) is not int or not 0 <= sample["keys"] <= 255
                or type(sample.get("sequence")) is not int or not 0 <= sample["sequence"] <= 0xffffffff
                or type(sample.get("generation")) is not int or not 0 <= sample["generation"] <= 65535
                or type(sample.get("presses")) is not list or len(sample["presses"]) != 8
                or any(type(x) is not int or not 0 <= x <= 65535 for x in sample["presses"])
                or type(sample.get("encoders")) is not list or len(sample["encoders"]) != 2
                or any(type(x) is not int or not -0x80000000 <= x <= 0x7fffffff for x in sample["encoders"])
                or type(sample.get("lux_valid")) is not bool
                or sample.get("error") is not None and (type(sample["error"]) is not str or len(sample["error"]) > 80)):
            return invalid
        result = dict(sample, age_ms=age)
        la = sample.get("lux_age_ms")
        la = la + self.now_ms - received + 100 if type(la) is int and la >= 0 else 3000
        lux = sample.get("lux")
        if not (sample["lux_valid"] and _number(lux)
                and 0 <= lux <= 200000 and 0 <= la < 2000):
            result.update(lux=None, lux_valid=False, lux_age_ms=None)
        else:
            result["lux_age_ms"] = la
        return result

    def status(self):
        imu = {"ok": False, "fresh": False, "quaternion": None, "error": "IMU_NOT_FRESH"}
        if self.imu_sample:
            received, sample = self.imu_sample
            source_age = sample.get("age_ms")
            quaternion = sample.get("quaternion")
            age = source_age + self.now_ms - received + 100 if type(source_age) is int else 500
            if (sample.get("ok") is True and sample.get("fresh") is True
                    and type(source_age) is int and 0 <= source_age < 500 and 0 <= age < 500
                    and self.last_status_ms is not None and self.now_ms - self.last_status_ms <= 500
                    and isinstance(quaternion, list) and len(quaternion) == 4
                    and all(_number(v) and -1.1 <= v <= 1.1 for v in quaternion)
                    and .7 <= sum(v * v for v in quaternion) <= 1.3
                    and type(sample.get("status")) is int and 1 <= sample["status"] <= 3
                    and sample.get("report_id") == 5):
                imu = dict(sample, age_ms=age)
        report_age = self._report_age_ms()
        return {"mode": "SIMULATION" if self.simulated else "HARDWARE", "pico": self.pico,
            "requested_operating_mode": self.requested_mode,
            "session": self.session, "configured": self.configured, "last_error": self.last_error,
            # The same 500 ms bound as the ARM refusal and the tick status timeout;
            # it covers the readings, so a HELLO-only stream reads stale.
            "pico_fresh": report_age is not None and 0 <= report_age <= 500,
            "pico_age_ms": None if report_age is None else max(0, report_age),
            "policy": self.policy.status(), "events": list(self.events),
            "imu": imu, "hmi": self._hmi_status(),
            "live_identity_verified": self.identity_ok,
            "qualification_record_verified": self.qualification_ok and not self.simulated,
            "hardware_qualified": bool(self.acceptance) and self.identity_ok and not self.simulated}

    def close(self):
        if not self.closed:
            try:
                self.trip("daemon_exit")
            finally:
                try:
                    self.link.close()
                finally:
                    try:
                        self.hardware.close()
                    finally:
                        try:
                            for reader in (self.soc_temp_reader, self.telemetry_reader):
                                if reader and hasattr(reader, "close"):
                                    reader.close()
                        finally:
                            self.closed = True
