"""INA228/INA3221 readers using the LinuxHardware I2C transport.

Primary register specifications: TI INA228 SLYS021A sections 7.6 and 8.1.2,
https://www.ti.com/lit/ds/symlink/ina228.pdf ; TI INA3221 SBOS576C section 8,
https://www.ti.com/lit/ds/symlink/ina3221.pdf . Register bytes are big endian.
These nominal shunt conversions are not an empirical calibration certificate.
No state-of-charge estimate is manufactured from voltage or an accumulator.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Mapping, Protocol


class I2CTransport(Protocol):
    def read(self, addr: int, reg: int, count: int) -> bytes: ...
    def write(self, addr: int, reg: int, data: bytes) -> None: ...


class TelemetryError(RuntimeError):
    pass


def monotonic_ms():
    return time.monotonic_ns() / 1_000_000


def _finite(value, low, high):
    return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


def _signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


@dataclass(frozen=True)
class MeasurementSnapshot:
    timestamp_ms: float
    values: Mapping[str, float]
    valid: bool
    calibration_valid: bool = False
    error: str | None = None

    def is_fresh(self, max_age_ms=250, now_ms=None):
        now = monotonic_ms() if now_ms is None else now_ms
        return (self.valid is True and _finite(now, 0, float("inf"))
                and _finite(self.timestamp_ms, 0, now)
                and _finite(max_age_ms, 0, float("inf"))
                and now - self.timestamp_ms <= max_age_ms
                and bool(self.values)
                and all(_finite(v, -float("inf"), float("inf"))
                        for v in self.values.values()))


class _Monitor:
    def __init__(self, transport, address, clock_ms=monotonic_ms):
        if type(address) is not int or not 0x40 <= address <= 0x4F:
            raise ValueError("invalid monitor I2C address")
        self.transport, self.address, self.clock_ms = transport, address, clock_ms
        self.configured = False

    def _read(self, reg, count=2):
        data = self.transport.read(self.address, reg, count)
        if not isinstance(data, (bytes, bytearray)) or len(data) != count:
            raise TelemetryError("short or malformed I2C read")
        return int.from_bytes(data, "big")

    def _write(self, reg, value):
        self.transport.write(self.address, reg, value.to_bytes(2, "big"))

    def _check(self, values, bounds):
        if set(values) != set(bounds):
            raise TelemetryError("incomplete measurement")
        for name, value in values.items():
            if not _finite(value, *bounds[name]):
                raise TelemetryError("out-of-bounds measurement: " + name)

    def read_snapshot(self):
        started = self.clock_ms()
        try:
            if not self.configured:
                raise TelemetryError("monitor not configured")
            values = self._sample()
            finished = self.clock_ms()
            if (not _finite(started, self.cycle_ms, float("inf"))
                    or not _finite(finished, started, started + 100)):
                raise TelemetryError("clock or I2C acquisition deadline")
            # The oldest averaged channel began up to one conversion cycle ago.
            return MeasurementSnapshot(started - self.cycle_ms, values, True)
        except Exception as exc:
            # Do not retain last-good values or renew their timestamp on failure.
            return MeasurementSnapshot(started, {}, False, error=str(exc))


class INA228(_Monitor):
    """Adafruit SJ1 topology: VBUS=IN+, so protected V_N=VBUS-VSHUNT.

    ADCRANGE=0, ±163.84 mV. 4 averaged bus/shunt/temperature conversions,
    each 1.052 ms; nominal cycle 12.624 ms. Positive current is discharge in
    this graph. Negative charging current therefore makes V_N > VBUS.
    """
    config = 0x0000
    adc_config = 0xFB69
    diag_config = 0x8000  # ALATCH=1: reading DIAG consumes conversion-ready.
    cycle_ms = 12.624

    def __init__(self, transport, address=0x40, shunt_ohms=0.015, clock_ms=monotonic_ms):
        super().__init__(transport, address, clock_ms)
        if not _finite(shunt_ohms, 0.000001, 1):
            raise ValueError("explicit positive shunt resistance required")
        self.shunt_ohms = shunt_ohms
        # 20 uA nominal resolution; use the actual integer programmed into IC.
        self.shunt_cal = round(13107.2e6 * 20e-6 * shunt_ohms)
        if not 1 <= self.shunt_cal <= 0x7FFF:
            raise ValueError("shunt calibration outside register range")
        self.current_lsb = self.shunt_cal / (13107.2e6 * shunt_ohms)

    def configure(self):
        self.configured = False
        if self._read(0x3E) != 0x5449 or self._read(0x3F) >> 4 != 0x228:
            raise TelemetryError("INA228 identity mismatch")
        for reg, value in ((0x00, self.config), (0x02, self.shunt_cal),
                           (0x0B, self.diag_config), (0x01, self.adc_config)):
            self._write(reg, value)
        self._assert_config()
        self._read(0x0B)  # Clear any result that predates configuration.
        self.configured = True

    def _assert_config(self):
        if (self._read(0x00) != self.config or self._read(0x01) != self.adc_config
                or self._read(0x02) != self.shunt_cal):
            raise TelemetryError("INA228 reset or configuration mismatch")

    def _sample(self):
        self._assert_config()
        diag = self._read(0x0B)
        if diag & 0xF000 != self.diag_config or not diag & 1 or diag & 0x200:
            raise TelemetryError("INA228 diagnostic/configuration fault")
        if not diag & 2:
            raise TelemetryError("INA228 has no new complete conversion")
        shunt_raw, bus_raw, current_raw = (self._read(r, 3) for r in (4, 5, 7))
        if (shunt_raw | bus_raw | current_raw) & 15:
            raise TelemetryError("INA228 reserved measurement bits set")
        shunt = _signed(shunt_raw >> 4, 20) * 312.5e-9
        bus = _signed(bus_raw >> 4, 20) * 195.3125e-6
        current = _signed(current_raw >> 4, 20) * self.current_lsb
        die = _signed(self._read(6), 16) * 0.0078125
        power = self._read(8, 3) * 3.2 * self.current_lsb
        values = {"battery_vbus_v": bus, "battery_shunt_v": shunt,
                  "battery_v": bus - shunt, "battery_current_a": current,
                  "battery_shunt_current_a": shunt / self.shunt_ohms,
                  "battery_power_w": power, "ina228_die_temp_c": die}
        current_max = 0.16384 / self.shunt_ohms
        self._check(values, {"battery_vbus_v": (0, 18), "battery_v": (0, 18),
                    "battery_shunt_v": (-0.16384, 0.16384),
                    "battery_current_a": (-current_max, current_max),
                    "battery_shunt_current_a": (-current_max, current_max),
                    "battery_power_w": (0, 18 * current_max),
                    "ina228_die_temp_c": (-40, 125)})
        # Gross disagreement catches wrong shunt scaling/data tearing. This is
        # a sanity bound, not a claimed measurement/calibration accuracy.
        if abs(current - shunt / self.shunt_ohms) > max(0.025, abs(current) * 0.02):
            raise TelemetryError("INA228 current/shunt disagreement")
        return values


class INA3221(_Monitor):
    """All three channels, 4 averages, 1.1 ms bus and shunt: 26.4 ms/cycle."""
    config = 0x7327
    cycle_ms = 26.4

    def __init__(self, transport, address, shunts_ohms, channel_names=None,
                 clock_ms=monotonic_ms):
        super().__init__(transport, address, clock_ms)
        if len(shunts_ohms) != 3 or any(not _finite(r, 0.000001, 10) for r in shunts_ohms):
            raise ValueError("three explicit positive shunts required")
        self.shunts_ohms = tuple(shunts_ohms)
        self.channel_names = tuple(channel_names or ("ch1", "ch2", "ch3"))
        if (len(self.channel_names) != 3 or len(set(self.channel_names)) != 3
                or any(type(n) is not str or not n.isidentifier() for n in self.channel_names)):
            raise ValueError("three unique channel names required")

    def configure(self):
        self.configured = False
        if self._read(0xFE) != 0x5449 or self._read(0xFF) != 0x3220:
            raise TelemetryError("INA3221 identity mismatch")
        self._write(0, self.config)
        if self._read(0) != self.config:
            raise TelemetryError("INA3221 configuration mismatch")
        self._read(0x0F)
        self.configured = True

    def _sample(self):
        if self._read(0) != self.config:
            raise TelemetryError("INA3221 reset or configuration mismatch")
        if not self._read(0x0F) & 1:
            raise TelemetryError("INA3221 has no new complete conversion")
        values, bounds = {}, {}
        for channel, (name, resistance) in enumerate(zip(self.channel_names, self.shunts_ohms)):
            sr, br = self._read(1 + channel * 2), self._read(2 + channel * 2)
            if (sr | br) & 7:
                raise TelemetryError("INA3221 reserved measurement bits set")
            shunt = _signed(sr, 16) / 8 * 40e-6
            bus = _signed(br, 16) / 8 * 0.008
            values.update({name + "_shunt_v": shunt, name + "_bus_v": bus,
                           name + "_current_a": shunt / resistance})
            bounds.update({name + "_shunt_v": (-0.16384, 0.16384),
                           name + "_bus_v": (0, 26),
                           name + "_current_a": (-0.16384 / resistance, 0.16384 / resistance)})
        self._check(values, bounds)
        return values


class SRRXTelemetry:
    """Physical E1/E2 channel map; call only after safe MCP initialization.

    Poll at intervals >=50 ms. A failed sensor invalidates the whole snapshot;
    callers must block enabling loads. Nominal conversion never grants hardware
    acceptance or battery ADC calibration. Safe CHG_INHIBIT=1 applies only after
    MCP initialization: MCP RESET is high impedance and permits hardware charging.
    """
    def __init__(self, transport, clock_ms=monotonic_ms):
        self.clock_ms = clock_ms
        self.monitors = (INA228(transport, clock_ms=clock_ms),
                         INA3221(transport, 0x41, (0.2, 0.2, 0.2),
                                 ("lna1", "lna2", "lna3"), clock_ms),
                         INA3221(transport, 0x43, (0.2, 0.1, 0.2),
                                 ("lna4", "lnb", "boni"), clock_ms))

    def configure(self):
        for monitor in self.monitors:
            monitor.configure()

    def poll(self):
        samples = [monitor.read_snapshot() for monitor in self.monitors]
        now = self.clock_ms()
        if any(not s.is_fresh(250, now) for s in samples):
            error = "; ".join(s.error or "stale sensor" for s in samples if not s.is_fresh(250, now))
            return MeasurementSnapshot(now, {}, False, error=error)
        values = {}
        for sample in samples:
            values.update(sample.values)
        values["lna_current_a"] = sum(values[f"lna{n}_current_a"] for n in range(1, 5))
        return MeasurementSnapshot(min(s.timestamp_ms for s in samples), values, True)
