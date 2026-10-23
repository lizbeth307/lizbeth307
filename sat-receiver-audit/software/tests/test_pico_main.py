"""Deployed Pico main.run() loop and HMI core with injected machine/time; no hardware PASS."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

PICO = Path(__file__).resolve().parents[2] / "firmware" / "pico"
sys.path.insert(0, str(PICO))
from srrx import wire
from srrx.wire import FrameDecoder, encode_frame


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, PICO / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pico_main = _load("pico_main_loop_under_test", "main.py")
hmi = _load("pico_hmi_errors_under_test", "hmi.py")


class _Stop(BaseException):
    """Leaves run()'s endless loops; run() never catches BaseException."""


class Board:
    """Q6A powered, no calibration records, empty HMI bus, ADC at 25 C NTC."""
    def __init__(self, loops=14):
        self.levels = {14: 1, 11: 1, 22: 1, 10: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1}
        self.log, self.writes, self.uarts = [], [], {}
        self.now, self.loops, self.injected = 0, loops, False
        board = self

        class Pin:
            IN, OUT, OPEN_DRAIN, PULL_UP, IRQ_RISING, IRQ_FALLING = 0, 1, 2, 3, 4, 8

            def __init__(self, gpio, mode=None, value=None):
                self.gpio = gpio
                self.init(mode, value=value)

            def init(self, mode=None, value=None):
                board.log.append(("pin", self.gpio, mode))
                if value is not None:
                    self.value(value)

            def value(self, value=None):
                if value is not None:
                    board.levels[self.gpio] = value
                    board.writes.append((self.gpio, value))
                return board.levels.get(self.gpio, 0)

            def irq(self, **kwargs):
                pass

        class UART:
            def __init__(self, number, **kwargs):
                self.number, self.rx, self.tx = number, bytearray(), bytearray()
                board.uarts[number] = self
                board.log.append(("uart", number, kwargs["tx"].gpio, kwargs["rx"].gpio))

            def any(self):
                return len(self.rx)

            def read(self, count):
                data, self.rx[:] = bytes(self.rx[:count]), self.rx[count:]
                return data or None

            def write(self, data):
                self.tx.extend(data)
                return len(data)

            def deinit(self):
                board.log.append(("uart_deinit", self.number))

        class ADC:
            def __init__(self, pin):
                pass

            def read_u16(self):
                return 32768

        class SoftI2C:
            def __init__(self, **kwargs):
                pass

            def readfrom_mem(self, *args, **kwargs):
                raise OSError("ENODEV")

            def writeto_mem(self, *args, **kwargs):
                raise OSError("ENODEV")

        class WDT:
            def __init__(self, timeout):
                pass

            def feed(self):
                pass

        self.Pin = Pin
        self.machine = types.SimpleNamespace(
            Pin=Pin, UART=UART, ADC=ADC, SoftI2C=SoftI2C, WDT=WDT,
            freq=lambda value: None, unique_id=lambda: bytes(range(8)),
            disable_irq=lambda: 0, enable_irq=lambda mask: None)
        self.time = types.SimpleNamespace(ticks_ms=lambda: board.now,
                                          ticks_diff=lambda new, old: new - old,
                                          sleep_us=lambda value: None, sleep_ms=self.sleep_ms)

    def frames(self):
        return FrameDecoder().feed(bytes(self.uarts[0].tx)) if 0 in self.uarts else []

    def sleep_ms(self, value):
        self.now += value
        if value == 20:
            self.loops -= 1
            hello = [frame for frame in self.frames() if frame["t"] == "HELLO"]
            if hello and not self.injected:
                # Host TRIP in the current Pico session: forces a supervisor TRIP event.
                self.uarts[0].rx.extend(encode_frame({"v": 1, "t": "TRIP", "s": hello[-1]["s"],
                                                      "q": 0, "p": {}}))
                self.injected = True
        if self.loops <= 0:
            raise _Stop()

    def run(self):
        modules = {"machine": self.machine, "time": self.time, "wire": wire,
                   "micropython": types.SimpleNamespace(alloc_emergency_exception_buf=lambda size: None)}
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(sys.modules, modules):
            os.chdir(folder)  # No calibration.json/commissioning.json: ARM stays refused.
            try:
                pico_main.run()
            finally:
                os.chdir(cwd)


class MainLoopTests(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        with self.assertRaises(_Stop):
            self.board.run()

    def test_supervisor_trip_diagnostic_travels_as_event_not_trip(self):
        frames = self.board.frames()
        self.assertEqual(frames[0]["t"], "HELLO")
        self.assertNotIn("TRIP", [frame["t"] for frame in frames])
        self.assertIn({"event": "TRIP", "fault": "HOST_TRIP"},
                      [frame["p"] for frame in frames if frame["t"] == "EVENT"])
        self.assertIn("TRIPPED", [frame["p"].get("state") for frame in frames if frame["t"] == "STATUS"])

    def test_imu_uart_gp8_returned_to_high_z_after_uart1_setup(self):
        log = self.board.log
        uart1 = log.index(("uart", 1, 8, 9))
        gp8 = [index for index, entry in enumerate(log) if entry[:2] == ("pin", 8)]
        self.assertGreater(gp8[-1], uart1)
        self.assertEqual(log[gp8[-1]][2], self.board.Pin.IN)
        self.assertEqual(self.board.uarts[1].tx, bytearray())

    def test_console_powered_in_safe_and_tripped_while_reset_stays_asserted(self):
        writes = self.board.writes
        self.assertIn((16, 1), writes)  # DISP12 eFuse with Q6A on and a 25 C panel.
        self.assertNotIn((17, 0), writes)  # MCP reset never released without ARM.
        self.assertEqual([value for gpio, value in writes if gpio == 16][-1], 0)  # fail_safe()


class Bus:
    domain = "pico_hmi_i2c0"

    def __init__(self):
        self.regs = {0x20: {0: b"\xff\xff", 2: b"\x00\x00", 4: b"\x00\x00", 6: b"\x00\x00"},
                     0x10: {0: b"\x00\x00", 3: b"\x00\x00", 4: b"\x64\x00"}}
        self.dead, self.recover_error, self.recoveries = set(), None, 0

    def recover(self):
        self.recoveries += 1
        if self.recover_error:
            raise OSError(self.recover_error)
        return True

    def sample_encoders(self):
        return ((0, None), (0, None))

    def read(self, address, register, count):
        if address in self.dead:
            raise OSError("NACK")
        return bytes(self.regs[address][register])

    def write(self, address, register, data):
        if address in self.dead:
            raise OSError("NACK")
        self.regs[address][register] = bytes(data)


class HMIErrorTests(unittest.TestCase):
    def test_key_bus_root_cause_survives_polls_and_light_failure(self):
        bus = Bus()
        poller = hmi.PeripheralPoller(bus)
        self.assertTrue(poller.poll(0)["ok"])
        bus.dead, bus.recover_error = {0x20, 0x10}, "HMI_SCL_STUCK"
        errors = {now: poller.poll(now)["error"] for now in range(20, 3001, 20)}
        self.assertEqual({errors[now] for now in range(20, 1001, 20)}, {"NACK"})
        self.assertEqual({errors[now] for now in range(1020, 3001, 20)}, {"HMI_SCL_STUCK"})
        self.assertEqual(bus.recoveries, 3)

    def test_missing_light_sensor_never_resets_keys_or_drops_a_press(self):
        bus = Bus()
        bus.dead = {0x10}
        poller = hmi.PeripheralPoller(bus)
        results = []
        for now in range(0, 3001, 20):
            if now == 980:
                bus.regs[0x20][0] = b"\xfe\xff"  # Pressed across the 1 s lux retry.
            results.append(poller.poll(now))
        self.assertTrue(all(result["ok"] for result in results))
        self.assertEqual({result["generation"] for result in results}, {0})
        self.assertEqual(bus.recoveries, 1)
        self.assertEqual((results[-1]["keys"], results[-1]["presses"][0]), (1, 1))
        self.assertEqual(results[-1]["error"], "ALS_IO_ERROR")
        self.assertFalse(results[-1]["lux_valid"])


if __name__ == "__main__":
    unittest.main()
