import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

from srrx.peripherals import PeripheralPoller, derive_wiring
from srrx.wire import FrameDecoder, encode_frame

PROJECT = Path(__file__).resolve().parents[2]
PICO = PROJECT / "firmware/pico"
sys.path.insert(0, str(PICO))
spec = importlib.util.spec_from_file_location("pico_input_test_core", PICO / "hmi.py")
hmi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hmi)
from main import TelemetrySchedule, hmi_payload
from adapter import PicoHMITransport


class FakeBus:
    domain = "pico_hmi_i2c0"

    def __init__(self):
        self.key = bytearray((255, 0, 255, 255, 0, 0, 255, 255))
        self.light = {0: b"\x01\x00", 3: b"\x00\x00"}
        self.raw = 100  # Low-gain 215.04lx, stays in the low-gain profile.
        self.trace = []
        self.recoveries = 0
        self.samples = ((0, None), (0, None))
        self.fail = None
        self.short = None
        self.now = 0

    def recover(self):
        self.recoveries += 1
        self.trace.append(("recover",))
        return True

    def sample_encoders(self):
        result, self.samples = self.samples, ((0, None), (0, None))
        return result

    def read(self, address, register, count):
        self.trace.append(("read", address, register, count))
        if self.fail == (address, register):
            self.fail = None
            raise OSError("NACK")
        if self.short == (address, register):
            self.short = None
            return b"\x00"
        if address == 0x20:
            # Model the real pair-only pointer; a mistaken six-byte read2..7
            # would return output registers repeatedly and fail these tests.
            return bytes(self.key[register ^ (index & 1)] for index in range(count))
        if address == 0x10 and count == 2:
            if register == 4:
                return bytes((self.raw & 255, self.raw >> 8))
            return self.light[register]
        raise AssertionError("unreviewed I2C transaction")

    def write(self, address, register, data):
        self.trace.append(("write", address, register, data))
        if address == 0x20:
            if register not in (2, 4, 6) or len(data) != 2:
                raise AssertionError("expander write must use individual register pairs")
            for index, value in enumerate(data):
                self.key[register ^ (index & 1)] = value
        elif address == 0x10 and register in (0, 3) and len(data) == 2:
            self.light[register] = data
        else:
            raise AssertionError("unreviewed I2C write")


def run_until(poller, end, start=0):
    result = None
    for now in range(start, end + 1, 20):
        result = poller.poll(now)
    return result


class FakeMachine:
    class Pin:
        IN, OPEN_DRAIN = 0, 2
        IRQ_RISING, IRQ_FALLING = 1, 2
        instances = {}

        def __init__(self, number, mode=None, value=None):
            self.number, self.mode = number, mode
            self.level = 1 if value is None else value
            self.stuck = False
            self.transitions = []
            self.handler = None
            self.instances[number] = self

        def init(self, mode, value=None):
            self.mode = mode
            if value is not None:
                self.value(value)

        def value(self, value=None):
            if value is not None:
                self.level = value
                self.transitions.append(value)
            return 0 if self.stuck else self.level

        def irq(self, **kwargs):
            self.handler = kwargs["handler"]
            self.irq_options = kwargs

        def edge(self, value):
            self.level = value
            self.handler(self)

    class SoftI2C:
        def __init__(self, **kwargs):
            self.options = kwargs
            self.trace = []

        def readfrom_mem(self, *args, **kwargs):
            self.trace.append(("read", args, kwargs))
            return b"\x12\x34"

        def writeto_mem(self, *args, **kwargs):
            self.trace.append(("write", args, kwargs))

    def __init__(self):
        self.irq_trace = []

    def disable_irq(self):
        self.irq_trace.append("disable")
        return 73

    def enable_irq(self, mask):
        self.irq_trace.append(("enable", mask))


class FakeTime:
    def __init__(self):
        self.waits = []

    def sleep_us(self, value):
        self.waits.append(value)


class HardwareAdapterTests(unittest.TestCase):
    def test_exact_gpio_ownership_hard_irqs_and_atomic_encoder_drain(self):
        machine, clock = FakeMachine(), FakeTime()
        transport = PicoHMITransport(machine, clock)
        self.assertEqual({transport.sda.number, transport.scl.number}, {4, 5})
        self.assertEqual(transport.interrupt.number, 10)
        for number in (2, 3, 6, 7):
            pin = machine.Pin.instances[number]
            self.assertTrue(pin.irq_options["hard"])
            self.assertEqual(pin.irq_options["trigger"], 3)
        # Actual per-edge callbacks, rather than injecting a completed delta.
        for number, level in ((2, 0), (3, 0), (2, 1), (3, 1)):
            machine.Pin.instances[number].edge(level)
        self.assertEqual(transport.sample_encoders(), ((1, None), (0, None)))
        self.assertEqual(machine.irq_trace, ["disable", ("enable", 73)])
        self.assertEqual(transport.sample_encoders(), ((0, None), (0, None)))
        machine.Pin.instances[10].level = 0
        self.assertTrue(transport.interrupt_pending())

    def test_bounded_bus_recovery_then_real_micropython_register_operations(self):
        machine, clock = FakeMachine(), FakeTime()
        transport = PicoHMITransport(machine, clock)
        with self.assertRaises(OSError):
            transport.read(0x20, 0, 2)
        self.assertTrue(transport.recover())
        self.assertEqual(clock.waits, [5] * 21)
        self.assertEqual(transport.scl.transitions[:19], [1] + [0, 1] * 9)
        self.assertEqual(transport.i2c.options["freq"], 100000)
        self.assertEqual(transport.i2c.options["timeout"], 200)
        self.assertEqual(transport.read(0x20, 0, 2), b"\x12\x34")
        self.assertIsNone(transport.write(0x10, 0, b"\x00\x13"))
        self.assertEqual(transport.i2c.trace,
                         [("read", (0x20, 0, 2), {"addrsize": 8}),
                          ("write", (0x10, 0, b"\x00\x13"), {"addrsize": 8})])

    def test_stuck_clock_or_data_fails_recovery_without_waiting_indefinitely(self):
        for signal, expected_waits in (("scl", 2), ("sda", 21)):
            machine, clock = FakeMachine(), FakeTime()
            transport = PicoHMITransport(machine, clock)
            getattr(transport, signal).stuck = True
            with self.assertRaises(OSError):
                transport.recover()
            self.assertIsNone(transport.i2c)
            self.assertEqual(len(clock.waits), expected_waits)


class WiringAndTransportTests(unittest.TestCase):
    def test_firmware_defaults_are_derived_from_actual_e3_graph(self):
        wiring = derive_wiring(PROJECT)
        self.assertEqual(wiring, hmi.DEFAULT_WIRING)
        self.assertEqual(wiring["key_address"], 0x20)
        self.assertEqual(wiring["encoder_gpios"], ((2, 3), (6, 7)))
        self.assertEqual(wiring["keys"], hmi.KEY_NAMES)

    def test_graph_wrong_controller_or_pin_is_rejected_before_io(self):
        graph = json.loads((PROJECT / "design/E3.json").read_text())
        for wrong in ("controller", "pin", "power", "gpio"):
            changed = json.loads(json.dumps(graph))
            parts = {part["ref"]: part for part in changed["components"]}
            if wrong == "controller":
                parts["U306"]["value"] = "TCA8418 guessed keypad"
            elif wrong == "pin":
                parts["U306"]["pins"][0]["number"] = "2"
            elif wrong == "power":
                next(pin for pin in parts["U306"]["pins"] if pin["name"] == "VCC")["net"] = "3V3_Q6A"
            else:
                next(pin for pin in parts["U305"]["pins"] if pin["name"] == "GP4")["net"] = "WRONG_BUS"
            with tempfile.TemporaryDirectory() as folder:
                destination = Path(folder) / "design"
                destination.mkdir()
                (destination / "E3.json").write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    derive_wiring(folder)

    def test_wrong_bus_and_duplicate_owner_are_refused(self):
        bus = FakeBus()
        bus.domain = "q6a_i2c2"
        with self.assertRaises(ValueError):
            PeripheralPoller(bus, PROJECT)
        self.assertEqual(bus.trace, [])
        bus.domain = "pico_hmi_i2c0"
        PeripheralPoller(bus, PROJECT)
        with self.assertRaises(ValueError):
            PeripheralPoller(bus, PROJECT)

    def test_register_initialization_three_pairs_and_both_input_ports(self):
        bus = FakeBus()
        poller = PeripheralPoller(bus, PROJECT)
        status = poller.poll(0)
        writes = [item for item in bus.trace if item[0] == "write" and item[1] == 0x20]
        self.assertEqual(writes, [("write", 0x20, 2, b"\x00\x00"),
                                  ("write", 0x20, 4, b"\x00\x00"),
                                  ("write", 0x20, 6, b"\xff\x00")])
        self.assertIn(("read", 0x20, 0, 2), bus.trace)
        self.assertEqual(bus.key[6:], b"\xff\x00")
        self.assertTrue(status["ok"])
        self.assertFalse(poller.physical_qualified)

    def test_nack_short_read_and_readback_corruption_invalidate_inputs(self):
        for failure in ("nack", "short", "register"):
            bus, poller = FakeBus(), None
            poller = PeripheralPoller(bus, PROJECT)
            poller.poll(0)
            if failure == "nack":
                bus.fail = (0x20, 0)
                status = poller.poll(20)
            elif failure == "short":
                bus.short = (0x20, 0)
                status = poller.poll(20)
            else:
                run_until(poller, 980, start=20)
                bus.key[6] = 0
                status = poller.poll(1000)
            self.assertFalse(status["ok"])
            self.assertEqual(status["keys"], 0)
            self.assertGreater(status["generation"], 0)

    def test_recovery_reinitializes_and_does_not_count_held_key_as_new_press(self):
        bus = FakeBus()
        poller = PeripheralPoller(bus, PROJECT)
        poller.poll(0)
        bus.fail = (0x20, 0)
        poller.poll(20)
        bus.key[0] = 254
        result = run_until(poller, 1100, start=40)
        self.assertTrue(result["ok"])
        self.assertEqual(result["keys"], 1)
        self.assertEqual(result["presses"][0], 0)
        self.assertEqual(bus.recoveries, 2)


class InputTests(unittest.TestCase):
    def test_key_debounce_short_press_counter_and_release(self):
        bus = FakeBus()
        poller = PeripheralPoller(bus, PROJECT)
        poller.poll(0)
        bus.key[0] = 254
        self.assertEqual(poller.poll(20)["presses"][0], 0)
        self.assertEqual(poller.poll(40)["presses"][0], 0)
        self.assertEqual(poller.poll(60)["presses"][0], 1)
        bus.key[0] = 255
        run_until(poller, 120, start=80)
        result = poller.snapshot(120)
        self.assertEqual(result["keys"], 0)
        self.assertEqual(result["presses"][0], 1)  # Survives a 5Hz snapshot interval.
        self.assertEqual(result["presses"][1:], [0] * 7)

    def test_bounce_and_boot_hold_do_not_invent_press_events(self):
        bus = FakeBus()
        bus.key[0] = 254
        poller = PeripheralPoller(bus, PROJECT)
        self.assertEqual(poller.poll(0)["presses"][0], 0)
        for now, value in ((20, 255), (40, 254), (60, 255), (80, 254)):
            bus.key[0] = value
            self.assertEqual(poller.poll(now)["presses"][0], 0)

    def test_pressed_bit_order_and_uint16_wrap(self):
        bus = FakeBus()
        poller = PeripheralPoller(bus, PROJECT)
        poller.poll(0)
        poller.core.presses[5] = 65535
        bus.key[0] = 255 ^ (1 << 5) ^ (1 << 7)
        result = run_until(poller, 60, start=20)
        self.assertEqual(result["keys"], (1 << 5) | (1 << 7))
        self.assertEqual(result["presses"][5], 0)
        self.assertEqual(result["presses"][7], 1)

    def test_complete_quadrature_cycle_reverse_and_bounce(self):
        encoder = hmi.Quadrature()
        for a, b in ((0, 1), (0, 0), (1, 0), (1, 1)):
            encoder.update(a, b)
        self.assertEqual(encoder.drain(), (1, None))
        for a, b in ((1, 0), (0, 0), (0, 1), (1, 1)):
            encoder.update(a, b)
        self.assertEqual(encoder.drain(), (-1, None))
        encoder.update(0, 1)
        encoder.update(1, 1)
        self.assertEqual(encoder.drain(), (0, None))

    def test_invalid_quadrature_and_pending_overrun_are_not_movement(self):
        encoder = hmi.Quadrature()
        encoder.update(0, 0)
        self.assertEqual(encoder.drain(), (0, "ENCODER_TRANSITION"))
        encoder = hmi.Quadrature()
        encoder.pending = 32767
        for a, b in ((0, 1), (0, 0), (1, 0), (1, 1)):
            encoder.update(a, b)
        self.assertEqual(encoder.drain(), (0, "ENCODER_OVERRUN"))

    def test_encoder_totals_wrap_and_fault_generation_requires_new_baseline(self):
        bus = FakeBus()
        poller = PeripheralPoller(bus, PROJECT)
        poller.poll(0)
        poller.core.encoders[0] = 0x7fffffff
        bus.samples = ((1, None), (-1, None))
        result = poller.poll(20)
        self.assertEqual(result["encoders"], [-0x80000000, -1])
        bus.samples = ((3, "ENCODER_OVERRUN"), (0, None))
        result = poller.poll(40)
        self.assertFalse(result["ok"])
        self.assertEqual(result["encoders"], [-0x80000000, -1])
        generation = result["generation"]
        result = poller.poll(60)
        self.assertTrue(result["ok"])
        self.assertEqual(result["generation"], generation)

    def test_poll_gap_staleness_and_backwards_clock_fail_closed(self):
        bus = FakeBus()
        poller = PeripheralPoller(bus, PROJECT)
        poller.poll(0)
        self.assertFalse(poller.snapshot(100)["fresh"])
        bus.key[0] = 254
        result = poller.poll(200)
        self.assertGreater(result["generation"], 0)
        self.assertEqual(result["presses"][0], 0)
        self.assertFalse(poller.poll(199)["ok"])
        self.assertFalse(poller.poll(300)["ok"])

    def test_hmi_has_no_arm_or_power_output_interface(self):
        poller = PeripheralPoller(FakeBus(), PROJECT)
        for name in ("arm", "receive", "apply_outputs", "set_enable", "brightness"):
            self.assertFalse(hasattr(poller.core, name))


class AmbientAndWireTests(unittest.TestCase):
    def test_veml_little_endian_configuration_and_data(self):
        bus = FakeBus()
        poller = PeripheralPoller(bus, PROJECT)
        poller.poll(0)
        self.assertIn(("write", 0x10, 0, b"\x00\x13"), bus.trace)
        self.assertIn(("write", 0x10, 3, b"\x00\x00"), bus.trace)
        self.assertFalse(poller.snapshot(80)["lux_valid"])
        result = run_until(poller, 100, start=20)
        self.assertTrue(result["lux_valid"])
        self.assertAlmostEqual(result["lux"], 215.04)
        self.assertEqual(result["lux_age_ms"], 33)

    def test_gain_switch_waits_30percent_integration_tolerance(self):
        bus = FakeBus()
        bus.raw = 0
        poller = PeripheralPoller(bus, PROJECT)
        result = run_until(poller, 100)
        self.assertIn(("write", 0x10, 0, b"\xc0\x08"), bus.trace)
        self.assertFalse(result["lux_valid"])
        self.assertEqual(poller.core.light.ready_at, 1190)
        bus.raw = 1000
        run_until(poller, 1180, start=120)
        self.assertFalse(poller.snapshot(1180)["lux_valid"])
        result = poller.poll(1200)
        self.assertTrue(result["lux_valid"])
        self.assertAlmostEqual(result["lux"], 4.2)
        self.assertEqual(result["lux_age_ms"], 1040)
        bus.raw = 30000
        run_until(poller, 2300, start=1220)
        self.assertFalse(poller.snapshot(2300)["lux_valid"])
        self.assertEqual(bus.light[0], b"\x00\x13")

    def test_low_gain_correction_saturation_and_expired_lux(self):
        bus = FakeBus()
        bus.raw = 700
        poller = PeripheralPoller(bus, PROJECT)
        result = run_until(poller, 100)
        # AN84323 example1500lx corrects to about1658; raw700 is1505.28lx.
        self.assertAlmostEqual(result["lux"], 1664.6, delta=2)
        self.assertFalse(poller.snapshot(2200)["lux_valid"])
        bus = FakeBus()
        bus.raw = 65535
        poller = PeripheralPoller(bus, PROJECT)
        result = run_until(poller, 100)
        self.assertIsNone(result["lux"])
        self.assertFalse(result["lux_valid"])

    def test_sensor_config_change_or_nack_does_not_reuse_cached_lux(self):
        for failure in ("config", "nack"):
            bus = FakeBus()
            poller = PeripheralPoller(bus, PROJECT)
            run_until(poller, 100)
            if failure == "config":
                bus.light[0] = b"\x01\x13"
            else:
                bus.fail = (0x10, 0)
            result = run_until(poller, 200, start=120)
            self.assertFalse(result["lux_valid"])
            self.assertIsNone(result["lux"])
            # FW-HMI-01: a lux-only fault never resets the key expander.
            self.assertEqual(result["generation"], 0)

    def test_hmi_snapshot_worst_case_fits_wire_and_source_age_is_added(self):
        poller = PeripheralPoller(FakeBus(), PROJECT)
        poller.poll(0)
        value = poller.core
        value.presses = [65535] * 8
        value.encoders = [-0x80000000, 0x7fffffff]
        value._stable = 255
        value.sequence, value.generation = 0xfffffffe, 65535
        value.error = "X" * 32
        value.light.value = 139999.9999
        value.light.sample_at, value.light.acquisition_ms = 0, 1040
        payload = hmi_payload(poller, 20)
        self.assertEqual(payload["hmi"]["age_ms"], 120)
        self.assertEqual(payload["hmi"]["lux_age_ms"], 1160)
        frame = {"v": 1, "t": "EVENT", "s": 0xffffffff, "q": 0xfffffffe, "p": payload}
        packet = encode_frame(frame)
        self.assertLessEqual(len(packet), 512)
        self.assertEqual(FrameDecoder().feed(packet), [frame])


class ScheduleTests(unittest.TestCase):
    def test_hello_then_status_then_fair_optional_snapshots(self):
        schedule = TelemetrySchedule()
        self.assertEqual(schedule.choose(0, "SAFE", True, True, True), "HELLO")
        schedule.sent("HELLO", 0, "SAFE")
        self.assertEqual(schedule.choose(20, "SAFE", False, True, True), "STATUS")
        schedule.sent("STATUS", 20, "SAFE")
        first = schedule.choose(40, "SAFE", False, True, True)
        self.assertEqual(first, "IMU")
        schedule.sent(first, 40, "SAFE")
        self.assertEqual(schedule.choose(60, "SAFE", False, True, True), "HMI")

    def test_status_and_hmi_cannot_be_starved_by_imu_or_event_burst(self):
        schedule = TelemetrySchedule()
        records = []
        for now in range(0, 2001, 20):
            choice = schedule.choose(now, "ACTIVE", False, True, True)
            records.append((now, choice))
            if choice:
                schedule.sent(choice, now, "ACTIVE")
        for kind, bound in (("STATUS", 200), ("HMI", 240)):
            times = [now for now, value in records if value == kind]
            self.assertGreater(len(times), 5)
            self.assertLessEqual(max(right-left for left, right in zip(times, times[1:])), bound)


if __name__ == "__main__":
    unittest.main()
