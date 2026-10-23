"""Apply explicitly accepted bench coefficients to fresh physical monitor data."""
import math
from .hardware import I2CTransport
from .telemetry import SRRXTelemetry, monotonic_ms

MONITORED = ("LNA1", "LNA2", "LNA3", "LNA4", "LNB", "BONI")
# INA3221 zero-offset band: 2 LSB of shunt (40 uV) and bus (8 mV) voltage.
SHUNT_ZERO_V, BUS_ZERO_V = 2 * 40e-6, 2 * 0.008


def _calibrated(raw, negative, gain, offset):
    # Polarity comes from the raw sign beyond the zero-offset band. The accepted
    # intercept may neither turn an idle reading negative nor hide a reversal.
    value = raw * gain + offset
    return min(value, raw * gain) if negative else max(0.0, value)


class ProjectTelemetry:
    def __init__(self, i2c0_path, hardware, acceptance, clock=monotonic_ms):
        self.path, self.hardware, self.acceptance = i2c0_path, hardware, acceptance
        self.clock = clock
        self.bus0 = self.reader = None
        self.last_snapshot = None

    def read(self, address, register, count):
        return (self.bus0 if address == 0x40 else self.hardware).read(address, register, count)

    def write(self, address, register, data):
        return (self.bus0 if address == 0x40 else self.hardware).write(address, register, data)

    def configure(self):
        self.close()
        self.bus0 = I2CTransport(self.path)
        self.reader = SRRXTelemetry(self, self.clock)
        self.reader.configure()

    def poll(self, now_ms):
        if self.reader is None:
            return {}
        snapshot = self.reader.poll()
        self.last_snapshot = snapshot
        # Judge freshness on the acquisition clock: the tick time predates the
        # I2C reads, so a delayed read would otherwise look like future data.
        acquired = self.clock()
        if acquired < now_ms or not snapshot.is_fresh(250, acquired):
            return {b: {"valid": False, "calibration_valid": False} for b in MONITORED}
        # Never newer than the engine tick; labelling it older is conservative.
        stamp, values, result = min(snapshot.timestamp_ms, now_ms), snapshot.values, {}
        for branch in MONITORED:
            calibration = self.acceptance["branch_limits"][branch]["calibration"]
            if calibration["status"] != "PASS" or calibration["source"] == "bench_only_no_runtime_sensor":
                result[branch] = {"valid": False, "calibration_valid": False}
                continue
            prefix = branch.lower()
            current = _calibrated(values[prefix + "_current_a"], values[prefix + "_shunt_v"] < -SHUNT_ZERO_V,
                                  calibration["current_gain"], calibration["current_offset_a"])
            voltage = _calibrated(values[prefix + "_bus_v"], values[prefix + "_bus_v"] < -BUS_ZERO_V,
                                  calibration["voltage_gain"], calibration["voltage_offset_v"])
            if not math.isfinite(current) or not math.isfinite(voltage):
                result[branch] = {"valid": False, "calibration_valid": False}
                continue
            result[branch] = {"current_a": current, "voltage_v": voltage,
                "timestamp_ms": stamp, "valid": True, "calibration_valid": True}
        return result

    def close(self):
        if self.bus0:
            self.bus0.close()
            self.bus0 = None
        self.reader = None
