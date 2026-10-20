import math
import unittest

from srrx.telemetry import INA228, INA3221, MeasurementSnapshot, SRRXTelemetry, TelemetryError


class RegisterBus:
    def __init__(self):
        self.reg = {}
        self.fail = None
        for addr in (0x40, 0x41, 0x43):
            self.reg[addr, 0x3E] = 0x5449
            self.reg[addr, 0x3F] = 0x2281
            self.reg[addr, 0xFE] = 0x5449
            self.reg[addr, 0xFF] = 0x3220

    def read(self, addr, reg, count):
        if addr == self.fail:
            raise OSError("injected disconnected sensor")
        value = self.reg.get((addr, reg), 0)
        if reg == 0x0B:
            self.reg[addr, reg] = value & ~2
        if reg == 0x0F:
            self.reg[addr, reg] = value & ~1
        return value.to_bytes(count, "big")

    def write(self, addr, reg, data):
        value = int.from_bytes(data, "big")
        self.reg[addr, reg] = value | (1 if reg == 0x0B else 0)

    def battery(self, current=.1, bus=16):
        self.reg[0x40, 0x0B] = 0x8003
        self.reg[0x40, 4] = (round(current * .015 / 312.5e-9) & 0xFFFFF) << 4
        self.reg[0x40, 5] = round(bus / 195.3125e-6) << 4
        self.reg[0x40, 6] = round(25 / .0078125)
        self.reg[0x40, 7] = (round(current / (3932 / (13107.2e6 * .015))) & 0xFFFFF) << 4
        self.reg[0x40, 8] = round(abs(current) * bus / (3.2 * (3932 / (13107.2e6 * .015))))

    def branches(self, addr, shunts, current=.1):
        self.reg[addr, 0x0F] = 3
        for channel, resistance in enumerate(shunts):
            self.reg[addr, 1 + 2 * channel] = (round(current * resistance / 40e-6) & 0x1FFF) << 3
            self.reg[addr, 2 + 2 * channel] = round(4.5 / .008) << 3


class TelemetryTests(unittest.TestCase):
    def setUp(self):
        self.bus = RegisterBus()
        self.now = 1000.0
        self.clock = lambda: self.now

    def test_signed_charging_and_sj1_voltage(self):
        monitor = INA228(self.bus, clock_ms=self.clock)
        monitor.configure()
        for current in (.5, -.5):
            self.bus.battery(current)
            snapshot = monitor.read_snapshot()
            self.assertTrue(snapshot.valid, snapshot.error)
            self.assertFalse(snapshot.calibration_valid)
            self.assertAlmostEqual(snapshot.values["battery_current_a"], current, places=4)
            self.assertAlmostEqual(snapshot.values["battery_v"], 16 - current * .015, places=5)
            self.assertEqual(snapshot.timestamp_ms, 1000 - 12.624)
        self.assertGreater(snapshot.values["battery_v"], snapshot.values["battery_vbus_v"])

    def test_no_new_conversion_never_refreshes_last_values(self):
        monitor = INA228(self.bus, clock_ms=self.clock)
        monitor.configure()
        self.bus.battery()
        self.assertTrue(monitor.read_snapshot().valid)
        self.now += 100
        stale = monitor.read_snapshot()
        self.assertFalse(stale.valid)
        self.assertEqual(stale.values, {})
        self.assertIn("no new", stale.error)

    def test_ina228_wrong_identity_reset_math_fault_reserved_bits(self):
        monitor = INA228(self.bus, clock_ms=self.clock)
        self.bus.reg[0x40, 0x3F] = 0x2381
        with self.assertRaises(TelemetryError):
            monitor.configure()
        self.bus.reg[0x40, 0x3F] = 0x2281
        monitor.configure()
        self.bus.battery()
        self.bus.reg[0x40, 1] = 0xFB68
        self.assertFalse(monitor.read_snapshot().valid)
        self.bus.reg[0x40, 1] = monitor.adc_config
        self.bus.battery()
        self.bus.reg[0x40, 0x0B] |= 0x200
        self.assertFalse(monitor.read_snapshot().valid)
        self.bus.battery()
        self.bus.reg[0x40, 4] |= 1
        self.assertFalse(monitor.read_snapshot().valid)

    def test_ina228_current_scaling_disagreement_blocks(self):
        monitor = INA228(self.bus, clock_ms=self.clock)
        monitor.configure()
        self.bus.battery(.1)
        self.bus.reg[0x40, 7] *= 2
        self.assertFalse(monitor.read_snapshot().valid)

    def test_ina3221_signed_shunts_and_actual_resistors(self):
        monitor = INA3221(self.bus, 0x43, (.2, .1, .2), ("lna4", "lnb", "boni"), self.clock)
        monitor.configure()
        self.bus.branches(0x43, (.2, .1, .2), -.1)
        sample = monitor.read_snapshot()
        self.assertTrue(sample.valid, sample.error)
        self.assertAlmostEqual(sample.values["lnb_shunt_v"], -.01)
        self.assertAlmostEqual(sample.values["lnb_current_a"], -.1)
        self.assertAlmostEqual(sample.values["lna4_shunt_v"], -.02)
        self.assertFalse(monitor.read_snapshot().valid)

    def test_sensor_failure_invalidates_aggregate(self):
        monitors = SRRXTelemetry(self.bus, self.clock)
        monitors.configure()
        self.bus.battery()
        self.bus.branches(0x41, (.2, .2, .2))
        self.bus.branches(0x43, (.2, .1, .2))
        sample = monitors.poll()
        self.assertTrue(sample.valid, sample.error)
        self.assertAlmostEqual(sample.values["lna_current_a"], .4)
        self.assertNotIn("sb_lna_current_a", sample.values)
        self.bus.battery()
        self.bus.branches(0x41, (.2, .2, .2))
        self.bus.fail = 0x43
        self.assertFalse(monitors.poll().valid)
        self.assertEqual(monitors.poll().values, {})

    def test_nonfinite_stale_future_and_long_read(self):
        sample = MeasurementSnapshot(1000, {"v": 1.0}, True)
        self.assertTrue(sample.is_fresh(250, 1250))
        self.assertFalse(sample.is_fresh(250, 1251))
        self.assertFalse(sample.is_fresh(250, 999))
        self.assertFalse(sample.is_fresh(float("nan"), 1000))
        self.assertFalse(MeasurementSnapshot(1000, {"v": math.nan}, True).is_fresh(250, 1000))
        monitor = INA228(self.bus, clock_ms=self.clock)
        monitor.configure()
        self.bus.battery()
        times = iter((1000, 1101))
        monitor.clock_ms = lambda: next(times)
        self.assertFalse(monitor.read_snapshot().valid)

    def test_short_read_and_impossible_bus_are_invalid(self):
        monitor = INA3221(self.bus, 0x41, (.2, .2, .2), clock_ms=self.clock)
        monitor.configure()
        self.bus.branches(0x41, (.2, .2, .2))
        self.bus.reg[0x41, 2] = round(27 / .008) << 3
        self.assertFalse(monitor.read_snapshot().valid)
        self.bus.read = lambda addr, reg, count: b"\0"
        self.assertFalse(monitor.read_snapshot().valid)


if __name__ == "__main__":
    unittest.main()
