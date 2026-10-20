"""Fail-closed host interlocks. No defaults represent measured commissioning data.

Only the daemon owns this object and the I2C adapter. Its bounded lease must
be renewed by that owner; a trip clears permission, never automatically re-arms.
Pico ACTIVE and hardware commissioning are independent supervisor assertions.
"""
from __future__ import annotations

import math
import time


# Conservative operating caps below the graph's minimum hardware ILIM.
# Sources: design/E2-review.md and E5-review.md, E4 receive-only routing.
CAPS = {
    "LNA1": (.265, 5.5), "LNA2": (.265, 5.5), "LNA3": (.265, 5.5),
    "LNA4": (.144, 5.5), "LNB": (.405, 14.0), "BONI": (.113, 15.0),
    "SB_LNA": (.065, 5.5), "RTLA": (.544, 5.5), "RTLB": (.400, 5.5),
    "HFP": (.825, 5.5), "LIME3V3": (1.80, 3.63), "T7": (1.512, 5.5),
    "LABPORT": (.678, 5.5), "AUX12": (.750, 13.0),
}
FAULTS = {
    "LABPORT": "FAULT_LABPORT", "LNA1": "FAULT_LNA1", "LNA2": "FAULT_LNA2",
    "LNA3": "FAULT_LNA3", "LNA4": "FAULT_LNA4", "LNB": "FLT_LNB", "BONI": "FLT_BONI",
    "RTLA": "FAULT_RTLA", "RTLB": "FAULT_RTLB", "HFP": "FAULT_HFP",
    "LIME3V3": "FLT_LIME3V3", "SB_LNA": "FLT_SB_LNA",
}
DCS = {"LNA2": "DCS_UHF", "LNA3": "DCS_LBAND", "BONI": "DCS_HF"}
PG = {"LNB": "PG_LNB", "BONI": "PG_BONI", "AUX12": "PTC_AUX"}
MONITORED = {"LNA1", "LNA2", "LNA3", "LNA4", "LNB", "BONI"}
LAB5_BRANCHES = {"LNA1", "LNA2", "LNA3", "LNA4", "SB_LNA", "RTLA", "RTLB", "HFP", "LABPORT"}
ROUTES = {"PARK": (False, False), "RF1": (False, False),
          "RF2": (True, False), "RF3": (False, True), "RF4": (True, True)}
MAX_INPUT_AGE_MS, MAX_TELEMETRY_AGE_MS, MAX_LEASE_MS = 250, 1000, 5000


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


class SafetyPolicy:
    def __init__(self, hardware, clock=None):
        self.hardware = hardware
        self.clock = clock or (lambda: int(time.monotonic() * 1000))
        self.armed = False
        self.fault = None
        self.mode = "field"
        self.pico_active = self.commissioned = False
        self.owner = None
        self.lease_deadline_ms = None
        self.inputs, self.telemetry, self.limits = {}, {}, {}
        self.input_time_ms = None
        self.now_ms = None
        self.dcs_low_since = {branch: None for branch in DCS}
        self.bias_off_since = {branch: None for branch in DCS}
        self.enabled_since = {}
        self.relay_off_since = None
        self.confirmations = {"boni_connected": False, "boni_profile": False, "bench_loads": False}
        self.always_on_a = 0.0 if not hardware.physical else None
        self.max_lab5_a = 3.2
        try:
            if not hardware.initialized and not hardware.physical:
                hardware.initialize_safe()
            elif hardware.initialized:
                hardware.all_off()
        except Exception as error:
            self.fault = "hardware: " + str(error)

    def configure_power_budget(self, always_on_a, max_lab5_a=3.2):
        if self.armed or not _number(always_on_a) or not _number(max_lab5_a) or not (0 <= always_on_a < max_lab5_a <= 3.2):
            raise ValueError("Explicit conservative LAB5 budget required while disarmed")
        self.always_on_a, self.max_lab5_a = always_on_a, max_lab5_a

    def clear_fault(self, now_ms=None):
        """Explicit recovery after verified reset; leaves the policy disarmed."""
        now = self._time(now_ms)
        if (self.armed or not self.pico_active or not self.commissioned or
                not self.hardware.initialized or self.hardware.faulted or
                not self._inputs_fresh(now) or any(self.inputs.get(net) is not True for net in FAULTS.values())):
            return False
        try:
            self.hardware.all_off()
        except Exception:
            return False
        self.fault = None
        self.enabled_since.clear()
        self.bias_off_since = {branch: now for branch in DCS}
        self.dcs_low_since = {branch: None for branch in DCS}
        self.relay_off_since = now
        return True

    @property
    def outputs(self):
        return self.hardware.outputs

    def _time(self, now_ms):
        now = self.clock() if now_ms is None else now_ms
        if not _number(now) or now < 0 or (self.now_ms is not None and now < self.now_ms):
            self.trip("invalid or backwards monotonic clock")
            raise ValueError("invalid monotonic timestamp")
        now = int(now)
        if self.now_ms is None:
            self.bias_off_since = {branch: now for branch in DCS}
            self.relay_off_since = now
        self.now_ms = now
        return now

    def set_readiness(self, pico_active=False, commissioned=False):
        self.pico_active = pico_active is True
        self.commissioned = commissioned is True
        if self.armed and not (self.pico_active and self.commissioned):
            self.trip("Pico ACTIVE or commissioning permission lost")

    def configure_limits(self, limits):
        """Accept explicit measured bring-up limits; never learn from live faults."""
        if self.armed:
            raise ValueError("Limits can only change while disarmed")
        validated = {}
        for branch, limit in limits.items():
            if branch not in CAPS:
                raise ValueError("Unknown branch: " + branch)
            required = ("baseline_a", "max_current_a", "min_voltage_v", "max_voltage_v")
            if any(not _number(limit.get(key)) for key in required):
                raise ValueError("Finite measured limits required")
            baseline, maximum, vmin, vmax = (limit[key] for key in required)
            cap, vcap = CAPS[branch]
            if not (0 < baseline <= maximum <= cap and 0 < vmin < vmax <= vcap):
                raise ValueError("Commissioned limits exceed design bounds")
            if branch.startswith("LNA") and maximum > 1.2 * baseline + 1e-12:
                raise ValueError("LNA limit exceeds 120% measured baseline")
            if branch == "BONI" and not (.030 <= baseline <= maximum < .113):
                raise ValueError("Boni requires 30mA..below113mA current window")
            validated[branch] = dict(limit)
        self.limits.update(validated)

    def refresh_inputs(self, inputs, now_ms=None):
        now = self._time(now_ms)
        expected = set(self.hardware.mapping["inputs"])
        if set(inputs) != expected or any(type(value) is not bool for value in inputs.values()):
            self.trip("missing or invalid GPIO input sample")
            return
        gap = self.input_time_ms is None or now - self.input_time_ms > MAX_INPUT_AGE_MS
        self.inputs, self.input_time_ms = dict(inputs), now
        for branch, net in DCS.items():
            off = not self.outputs.get("EN_" + branch, False)
            settled = self.bias_off_since[branch] is not None and now - self.bias_off_since[branch] >= 500
            if not off or not settled or inputs[net] or gap:
                self.dcs_low_since[branch] = None
            if off and settled and not inputs[net] and self.dcs_low_since[branch] is None:
                self.dcs_low_since[branch] = now
        if self.armed:
            self._check_running(now)

    def refresh_telemetry(self, samples, now_ms=None):
        now = self._time(now_ms)
        for branch, sample in samples.items():
            if branch not in CAPS or not isinstance(sample, dict):
                self.trip("unknown telemetry branch")
                return
            if branch not in MONITORED:
                # There is no ADC on these outputs. Fixed accepted reservations
                # must never be labelled as measured current or voltage.
                continue
            accepted = (sample.get("valid", not self.hardware.physical) is True
                        and sample.get("calibration_valid", not self.hardware.physical) is True)
            if not accepted:
                self.telemetry.pop(branch, None)
                if self.armed:
                    self.trip("unaccepted ADC calibration/data: " + branch)
                continue
            required = ("current_a", "voltage_v", "timestamp_ms")
            if any(not _number(sample.get(key)) for key in required):
                self.trip("invalid telemetry: " + branch)
                return
            if (sample["current_a"] < 0 or sample["voltage_v"] < 0 or
                    sample["timestamp_ms"] > now or sample["timestamp_ms"] < 0 or
                    (branch in self.telemetry and sample["timestamp_ms"] < self.telemetry[branch]["timestamp_ms"])):
                self.trip("invalid telemetry timestamp or polarity: " + branch)
                return
            self.telemetry[branch] = dict(sample)
        if self.armed:
            self._check_running(now)

    def _fresh(self, branch, now):
        sample = self.telemetry.get(branch)
        return (sample is not None and 0 <= now - sample["timestamp_ms"] <= MAX_TELEMETRY_AGE_MS)

    def _inputs_fresh(self, now):
        return self.input_time_ms is not None and 0 <= now - self.input_time_ms <= MAX_INPUT_AGE_MS

    def _write(self, values):
        try:
            self.hardware.apply_outputs(values)
            return True
        except Exception as error:
            self.trip("I2C/output failure: " + str(error))
            return False

    def trip(self, reason):
        if self.fault is None:
            self.fault = str(reason)
        self.armed = False
        self.enabled_since.clear()
        self.dcs_low_since = {branch: None for branch in DCS}
        self.bias_off_since = {branch: self.now_ms for branch in DCS}
        self.relay_off_since = self.now_ms
        self.confirmations = dict.fromkeys(self.confirmations, False)
        try:
            self.hardware.all_off()
        except Exception:
            self.fault += "; safe write unconfirmed: Pico MCP RESET required"

    def _budget_ok(self, proposed, now):
        antenna = 0.0
        for branch in ("LNA1", "LNA2", "LNA3", "LNA4"):
            if proposed.get("EN_" + branch):
                if branch not in self.limits or not self._fresh(branch, now):
                    return False
                # Reserve the accepted operating ceiling before enabling;
                # do not use an OFF branch's zero reading as its future load.
                antenna += self.limits[branch]["max_current_a"]
        if proposed.get("EN_SB_LNA"):
            antenna += .065
        if antenna > 1.0 + 1e-12 or antenna + .83 * proposed.get("EN_LABPORT", False) > 1.5 + 1e-12:
            return False
        active = [branch for branch in LAB5_BRANCHES if proposed.get("EN_" + branch)]
        if active and self.always_on_a is None:
            return False
        total = (self.always_on_a or 0) + .052
        for branch in active:
            if branch not in self.limits:
                return False
            total += .065 if branch == "SB_LNA" else .83 if branch == "LABPORT" else self.limits[branch]["max_current_a"]
        return total <= self.max_lab5_a + 1e-12

    def _check_running(self, now):
        if not self._inputs_fresh(now):
            self.trip("GPIO inputs stale")
            return
        for net in FAULTS.values():
            if self.inputs.get(net) is not True:
                self.trip("active-low fault: " + net)
                return
        for branch, since in list(self.enabled_since.items()):
            if branch in MONITORED and not self._fresh(branch, now):
                self.trip("telemetry stale: " + branch)
                return
            limit = self.limits[branch]
            sample = self.telemetry.get(branch) if branch in MONITORED else None
            if sample is not None:
                if sample["current_a"] > limit["max_current_a"] or sample["voltage_v"] > limit["max_voltage_v"]:
                    self.trip("branch operating ceiling: " + branch)
                    return
            deadline = 2000 if branch == "BONI" else 500
            if now - since >= deadline:
                lower_current = .030 if branch == "BONI" else 0
                if sample is not None and (sample["voltage_v"] < limit["min_voltage_v"] or sample["current_a"] < lower_current):
                    self.trip("startup current/voltage window: " + branch)
                    return
                if branch in PG and self.inputs.get(PG[branch]) is not True:
                    self.trip("power-good timeout: " + branch)
                    return
                if branch == "LNB" and self.inputs.get("OVP_LNB_N") is not True:
                    self.trip("LNB OVP permission lost")
                    return
        if not self._budget_ok(self.outputs, now):
            self.trip("antenna/LAB power budget")

    def tick(self, now_ms=None):
        now = self._time(now_ms)
        if self.armed:
            if self.lease_deadline_ms is None or now >= self.lease_deadline_ms:
                self.trip("owner lease expired")
            elif not (self.pico_active and self.commissioned):
                self.trip("supervisor permission lost")
            else:
                self._check_running(now)
        if self.lease_deadline_ms is not None and now >= self.lease_deadline_ms:
            self.owner, self.lease_deadline_ms = None, None
        return self.status()

    def _reject(self, reason):
        return {"ok": False, "error": reason}

    def command(self, name, value, now_ms=None):
        if not isinstance(name, str):
            return self._reject("named control required")
        try:
            now = self._time(now_ms)
        except ValueError as error:
            return self._reject(str(error))
        # De-energizing remains possible without a lease and after a trip.
        if name == "disarm" or (name == "arm" and value is False):
            self.armed = False
            self.enabled_since.clear()
            self.dcs_low_since = {branch: None for branch in DCS}
            self.bias_off_since = {branch: now for branch in DCS}
            self.relay_off_since = now
            try:
                self.hardware.all_off()
            except Exception as error:
                self.trip(str(error))
                return self._reject(str(error))
            return {"ok": True}
        if ((name.startswith("EN_") and name.removeprefix("EN_") in CAPS and value is False)
                or (name == "CHG_INHIBIT" and value is True)):
            if not self._write({name: value}):
                return self._reject(self.fault)
            branch = name.removeprefix("EN_")
            self.enabled_since.pop(branch, None)
            if branch in DCS:
                self.bias_off_since[branch], self.dcs_low_since[branch] = now, None
            return {"ok": True}
        if (name.startswith("route_") and name.removeprefix("route_") in ("RTLA", "RTLB", "LIME")
                and isinstance(value, str) and value in ("PARK", "RF1")):
            receiver = name.removeprefix("route_")
            if receiver == "RTLB" and self.outputs.get("EN_LNB"):
                if not self._write({"EN_LNB": False}):
                    return self._reject(self.fault)
                self.enabled_since.pop("LNB", None)
            return {"ok": self._write({"SW_" + receiver + "_A": False, "SW_" + receiver + "_B": False})}
        if name == "relay" and value == "PARK":
            if self.outputs.get("EN_BONI"):
                if not self._write({"EN_BONI": False}):
                    return self._reject(self.fault)
                self.enabled_since.pop("BONI", None)
                self.bias_off_since["BONI"], self.dcs_low_since["BONI"] = now, None
            ok = self._write({"K1_ON": False, "K2_ON": False})
            self.relay_off_since = now
            return {"ok": ok}
        if name == "lease":
            if not isinstance(value, dict) or not isinstance(value.get("owner"), str) or not value["owner"]:
                return self._reject("explicit owner required")
            ttl = value.get("ttl_ms")
            if not _number(ttl) or not 0 < ttl <= MAX_LEASE_MS:
                return self._reject("finite lease of 1..5000ms required")
            if self.owner not in (None, value["owner"]) and now < self.lease_deadline_ms:
                return self._reject("another owner holds the lease")
            if self.armed and self.lease_deadline_ms is not None and now >= self.lease_deadline_ms:
                self.trip("owner lease expired before renewal")
                return self._reject(self.fault)
            self.owner, self.lease_deadline_ms = value["owner"], now + int(ttl)
            return {"ok": True, "deadline_ms": self.lease_deadline_ms}
        if self.fault:
            return self._reject("fault latched: " + self.fault)
        if name == "mode":
            if value not in ("field", "lab") or self.armed:
                return self._reject("mode changes require disarmed field/lab")
            self.mode = value
            return {"ok": True}
        if name == "confirmations":
            if not isinstance(value, dict) or set(value) - set(self.confirmations) or any(type(v) is not bool for v in value.values()):
                return self._reject("unknown confirmation")
            self.confirmations.update(value)
            return {"ok": True}
        if not self.owner or self.lease_deadline_ms is None or now >= self.lease_deadline_ms:
            if self.armed:
                self.trip("owner lease expired")
            return self._reject("valid owner lease required")
        if name == "arm":
            if value is not True or not (self.pico_active and self.commissioned):
                return self._reject("Pico ACTIVE and commissioning required")
            if not self._inputs_fresh(now) or any(self.inputs.get(net) is not True for net in FAULTS.values()):
                return self._reject("fresh, clear physical faults required")
            self.armed = True
            return {"ok": True}
        if not self.armed:
            return self._reject("policy is disarmed")
        self._check_running(now)
        if self.fault:
            return self._reject(self.fault)
        if name.startswith("route_"):
            receiver = name.removeprefix("route_")
            if receiver not in ("RTLA", "RTLB", "LIME") or not isinstance(value, str) or value not in ROUTES:
                return self._reject("unknown receive-only RF route")
            if receiver == "RTLB" and self.outputs.get("EN_LNB"):
                return self._reject("disable LNB before changing RTL-B route")
            if self.outputs.get("EN_AUX12"):
                return self._reject("disable AUX12 before leaving PARK")
            if receiver == "RTLB" and value == "RF4" and (self.mode != "lab" or not self.confirmations["bench_loads"]):
                return self._reject("RTL-B RF4 BENCH requires lab and confirmed loads")
            a, b = ROUTES[value]
            # Explicit PARK write before changing either control bit.
            if not self._write({"SW_" + receiver + "_A": False, "SW_" + receiver + "_B": False}):
                return self._reject(self.fault)
            return {"ok": self._write({"SW_" + receiver + "_A": a, "SW_" + receiver + "_B": b})}
        if name == "relay":
            if value not in ("PARK", "HF", "VHF"):
                return self._reject("relay 11 is forbidden")
            if self.outputs.get("EN_BONI"):
                return self._reject("disable Boni before switching relays")
            if self.outputs.get("EN_AUX12"):
                return self._reject("disable AUX12 before leaving PARK")
            if self.outputs.get("K1_ON") or self.outputs.get("K2_ON"):
                if not self._write({"K1_ON": False, "K2_ON": False}):
                    return self._reject(self.fault)
                self.relay_off_since = now
                if value != "PARK":
                    return self._reject("break-before-make: retry after 10ms in PARK")
            if value == "PARK":
                return {"ok": True}
            if self.relay_off_since is None or now - self.relay_off_since < 10:
                return self._reject("break-before-make requires 10ms")
            return {"ok": self._write({"K1_ON": value == "HF", "K2_ON": value == "VHF"})}
        if not name.startswith("EN_") or name.removeprefix("EN_") not in CAPS or type(value) is not bool:
            return self._reject("restricted control whitelist; raw GPIO is forbidden")
        branch = name.removeprefix("EN_")
        if self.outputs.get(name):
            return {"ok": True}  # Never restart a PG timer on duplicate ON.
        if branch not in self.limits or (branch in MONITORED and not self._fresh(branch, now)):
            return self._reject("fresh measured telemetry and commissioned branch limits required")
        if branch in DCS:
            low_since = self.dcs_low_since[branch]
            if low_since is None or now - low_since < 500:
                return self._reject("DC preflight: 500ms OFF settling plus 500ms continuous LOW required")
        if branch == "LNB" and not (self.outputs.get("SW_RTLB_B") and not self.outputs.get("SW_RTLB_A")):
            return self._reject("LNB requires RTL-B RF3")
        if branch == "BONI" and not (self.confirmations["boni_connected"] and self.confirmations["boni_profile"] and self.outputs.get("K1_ON") and not self.outputs.get("K2_ON")):
            return self._reject("Boni profile, connected confirmation, and HF relay required")
        if branch in ("LNA1", "LNA2", "LNA3", "LNA4", "LNB", "BONI", "SB_LNA") and self.outputs.get("EN_AUX12"):
            return self._reject("AUX12 BENCH requires all antenna bias OFF")
        if branch in ("AUX12", "LABPORT") and (self.mode != "lab" or not self.confirmations["bench_loads"]):
            return self._reject("lab mode and confirmed loads required")
        if branch == "AUX12":
            parked = all(not value for net, value in self.outputs.items() if net.startswith(("SW_", "K1_", "K2_")))
            biases_off = all(not self.outputs.get("EN_" + b) for b in ("LNA1", "LNA2", "LNA3", "LNA4", "LNB", "BONI", "SB_LNA"))
            if not parked or not biases_off:
                return self._reject("lab mode, confirmed loads, PARK, and all antenna bias OFF required")
        proposed = dict(self.outputs, **{name: True})
        if not self._budget_ok(proposed, now):
            return self._reject("antenna reserve >1A or antenna+LAB reserve >1.5A")
        if not self._write({name: True}):
            return self._reject(self.fault)
        self.enabled_since[branch] = now
        if branch in DCS:
            self.dcs_low_since[branch] = None
        return {"ok": True}

    def status(self):
        return {"armed": self.armed, "fault": self.fault, "mode": self.mode,
                "pico_active": self.pico_active, "commissioned": self.commissioned,
                "owner": self.owner, "lease_deadline_ms": self.lease_deadline_ms,
                "outputs": dict(self.outputs), "inputs": dict(self.inputs),
                "simulation": not self.hardware.physical,
                "branch_observability": {branch: {"current_unknown": branch not in MONITORED,
                    "reservation_a": (.065 if branch == "SB_LNA" else .83 if branch == "LABPORT" else self.limits.get(branch, {}).get("max_current_a"))}
                    for branch in CAPS},
                "always_on_reserve_a": self.always_on_a, "max_lab5_a": self.max_lab5_a}
