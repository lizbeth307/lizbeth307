"""Apply explicitly accepted bench coefficients to fresh physical monitor data."""
import math
from .hardware import I2CTransport
from .telemetry import SRRXTelemetry

MONITORED = ("LNA1", "LNA2", "LNA3", "LNA4", "LNB", "BONI")


class ProjectTelemetry:
    def __init__(self, i2c0_path, hardware, acceptance):
        self.path, self.hardware, self.acceptance = i2c0_path, hardware, acceptance
        self.bus0 = self.reader = None
        self.last_snapshot = None

    def read(self, address, register, count):
        return (self.bus0 if address == 0x40 else self.hardware).read(address, register, count)

    def write(self, address, register, data):
        return (self.bus0 if address == 0x40 else self.hardware).write(address, register, data)

    def configure(self):
        self.close()
        self.bus0 = I2CTransport(self.path)
        self.reader = SRRXTelemetry(self)
        self.reader.configure()

    def poll(self, now_ms):
        if self.reader is None:
            return {}
        snapshot = self.reader.poll()
        self.last_snapshot = snapshot
        if not snapshot.is_fresh(250, now_ms):
            return {b: {"valid": False, "calibration_valid": False} for b in MONITORED}
        result = {}
        for branch in MONITORED:
            calibration = self.acceptance["branch_limits"][branch]["calibration"]
            if calibration["status"] != "PASS" or calibration["source"] == "bench_only_no_runtime_sensor":
                result[branch] = {"valid": False, "calibration_valid": False}
                continue
            prefix = branch.lower()
            current = snapshot.values[prefix + "_current_a"] * calibration["current_gain"] + calibration["current_offset_a"]
            voltage = snapshot.values[prefix + "_bus_v"] * calibration["voltage_gain"] + calibration["voltage_offset_v"]
            if not math.isfinite(current) or not math.isfinite(voltage):
                result[branch] = {"valid": False, "calibration_valid": False}
                continue
            result[branch] = {"current_a": current, "voltage_v": voltage,
                "timestamp_ms": snapshot.timestamp_ms, "valid": True, "calibration_valid": True}
        return result

    def close(self):
        if self.bus0:
            self.bus0.close()
            self.bus0 = None
        self.reader = None
