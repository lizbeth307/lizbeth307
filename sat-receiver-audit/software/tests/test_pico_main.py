"""Deployed Pico main.run() loop and HMI core with injected machine/time; no hardware PASS."""
import hashlib
import importlib.util
import json
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
supervisor = _load("pico_supervisor_main_under_test", "supervisor.py")
calibration = _load("pico_calibration_main_under_test", "calibration.py")


class _Stop(BaseException):
    """Leaves run()'s endless loops; run() never catches BaseException."""


class _Hang(BaseException):
    """run() left its 20 ms loop early (fail-safe idle) or ran past the bound."""


class Board:
    """Q6A powered, no calibration records, empty HMI bus, ADC at 25 C NTC.

    q6a=0 boots with Q6A 3V3 absent; q6a_after_key_ms then raises GP14 that
    long after GP12 asserts PWR_ON_KEY (a PMIC stand-in, not a measurement).
    """
    def __init__(self, loops=14, records=None, q6a=1, q6a_after_key_ms=None):
        self.records = records or {}  # File name -> JSON object in run()'s working folder.
        self.levels = {14: q6a, 11: 1, 22: 1, 10: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1}
        self.q6a_after_key_ms, self.key = q6a_after_key_ms, []  # (ms, GP12, GP14) per GP12 change.
        self.log, self.writes, self.uarts, self.display = [], [], {}, []
        self.now, self.loops, self.injected, self.model = 0, loops, False, None
        # Every sleep and tick read counts: an early firmware exception or a
        # non-sleeping spin raises _Hang instead of hanging or passing vacuously.
        self.ticks, self.max_ticks = 0, 100 * loops
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
                    if self.gpio == 12 and value != board.levels.get(12, 0):
                        board.key.append((board.now, value, board.levels[14]))
                    board.levels[self.gpio] = value
                    board.writes.append((self.gpio, value))
                    if self.gpio == 16:  # DISP12 eFuse: model state at each write.
                        board.display.append((board.phase(), value))
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

        class Supervisor(supervisor.Supervisor):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                board.model = self

        self.Pin = Pin
        self.Supervisor = Supervisor
        self.machine = types.SimpleNamespace(
            Pin=Pin, UART=UART, ADC=ADC, SoftI2C=SoftI2C, WDT=WDT,
            freq=lambda value: None, unique_id=lambda: bytes(range(8)),
            disable_irq=lambda: 0, enable_irq=lambda mask: None)
        self.time = types.SimpleNamespace(ticks_ms=self.ticks_ms,
                                          ticks_diff=lambda new, old: new - old,
                                          sleep_us=lambda value: None, sleep_ms=self.sleep_ms)

    def phase(self):
        if self.loops <= 0:
            return "FAIL_SAFE"  # run()'s finally after the budgeted _Stop.
        return "BOOT" if self.model is None else self.model.state

    def frames(self):
        return FrameDecoder().feed(bytes(self.uarts[0].tx)) if 0 in self.uarts else []

    def ticks_ms(self):
        self.ticks += 1
        if self.ticks > self.max_ticks:
            raise _Hang("ticks_ms read %d times with %d loops left" % (self.ticks, self.loops))
        return self.now

    def sleep_ms(self, value):
        self.now += value
        if (self.q6a_after_key_ms is not None and self.levels.get(12) and self.key
                and self.now - self.key[-1][0] >= self.q6a_after_key_ms):
            self.levels[14] = 1  # The PMIC answered the press: 3V3 on the 40-pin header.
        if self.loops <= 0:
            raise _Stop()  # fail_safe() idle loop after the budgeted stop below.
        if value != 20:
            # Only the main loop sleeps 20 ms; 50 ms is run()'s fail-safe idle
            # loop after an exception, which the traceback keeps as context.
            raise _Hang("sleep_ms(%d) with %d loops left" % (value, self.loops))
        self.loops -= 1
        # Decode the growing TX log only until the one TRIP is injected.
        hello = [] if self.injected else [frame for frame in self.frames() if frame["t"] == "HELLO"]
        if hello and not self.injected:
            # Host TRIP in the current Pico session: forces a supervisor TRIP event.
            self.uarts[0].rx.extend(encode_frame({"v": 1, "t": "TRIP", "s": hello[-1]["s"],
                                                  "q": 0, "p": {}}))
            self.injected = True
        if self.loops <= 0:
            raise _Stop()

    def run(self):
        modules = {"machine": self.machine, "time": self.time, "wire": wire,
                   "supervisor": types.SimpleNamespace(Supervisor=self.Supervisor),
                   "micropython": types.SimpleNamespace(alloc_emergency_exception_buf=lambda size: None)}
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(sys.modules, modules):
            os.chdir(folder)  # No calibration.json/commissioning.json: ARM stays refused.
            for name, record in self.records.items():
                Path(folder, name).write_text(json.dumps(record), encoding="utf-8")
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
        display = self.board.display  # (model state, level) at every GP16 write.
        self.assertEqual(display[0], ("BOOT", 0))  # Hardware() safe pins before the model.
        # DISP12 eFuse with Q6A on and a 25 C panel: HIGH at every write in each state.
        for state in ("SAFE", "TRIPPED"):
            levels = [value for phase, value in display if phase == state]
            self.assertTrue(levels, state)
            self.assertEqual(set(levels), {1}, state)
        self.assertEqual({phase for phase, value in display},
                         {"BOOT", "SAFE", "TRIPPED", "FAIL_SAFE"})
        self.assertEqual(self.board.model.fault, "HOST_TRIP")
        self.assertEqual(display[-1], ("FAIL_SAFE", 0))  # fail_safe() after the loop budget.
        self.assertNotIn((17, 0), self.board.writes)  # MCP reset never released without ARM.

    def test_hello_without_records_reports_no_qualification_record(self):
        hello = self.board.frames()[0]
        self.assertEqual(hello["t"], "HELLO")
        self.assertIsNone(hello["p"]["qualification_record"])
        self.assertIs(hello["p"]["hardware_commissioned"], False)

    def test_hello_carries_the_sealed_qualification_record_only(self):
        serial = bytes(range(8)).hex()  # Board.machine.unique_id
        cal = calibration.seal({"v": 1, "revision": calibration.REVISION, "serial": serial,
                                "scale_nv_per_count": 280000, "offset_uv": 0, "panel_offset_mc": 0,
                                "case_offset_mc": 0, "reference_id": "DMM-FIXTURE-42"})
        digest = hashlib.sha256(b"synthetic acceptance bytes, not a hardware record").hexdigest()
        record = calibration.seal({"v": 1, "revision": calibration.REVISION, "serial": serial,
                                   "calibration_crc32": cal["crc32"], "hardware_commissioned": True,
                                   "qualification_record": digest}, commissioning=True)
        edited = dict(record, qualification_record=digest[:-1] + ("0" if digest[-1] != "0" else "1"))
        for records, expected, commissioned in (
                ({"calibration.json": cal, "commissioning.json": record}, digest, True),
                ({"calibration.json": cal, "commissioning.json": edited}, None, False),  # Not resealed.
                ({"commissioning.json": record}, None, False)):  # No calibration, no commissioning.
            with self.subTest(records=sorted(records), expected=expected):
                board = Board(records=records)
                with self.assertRaises(_Stop):
                    board.run()
                hello = board.frames()[0]
                self.assertEqual(hello["t"], "HELLO")
                self.assertEqual(hello["p"]["qualification_record"], expected)
                self.assertIs(hello["p"]["hardware_commissioned"], commissioned)
                self.assertEqual(hello["p"]["calibration_crc32"],
                                 cal["crc32"] if "calibration.json" in records else None)
                self.assertNotIn("battery_mv", hello["p"])  # Readings travel in STATUS.
                status = [frame for frame in board.frames() if frame["t"] == "STATUS"]
                self.assertTrue(status and "battery_mv" in status[0]["p"])

    def test_early_firmware_exception_fails_instead_of_hanging(self):
        board = Board()
        del board.machine.UART  # Fails inside run()'s try, before the 20 ms loop.
        with self.assertRaises(_Hang) as caught:
            board.run()
        self.assertIsInstance(caught.exception.__context__, AttributeError)
        self.assertEqual(board.loops, 14)
        self.assertEqual(board.display[-1][1], 0)  # fail_safe() still drops DISP12.


class PowerKeyLoopTests(unittest.TestCase):
    """GP12 PWR_ON_KEY from the deployed loop, Q6A 3V3 absent at Pico boot (B11)."""
    def test_one_pulse_released_in_the_loop_that_sees_q6a_power(self):
        board = Board(loops=500, q6a=0, q6a_after_key_ms=300)
        with self.assertRaises(_Stop):
            board.run()
        self.assertEqual(board.key, [(1500, 1, 0), (1800, 0, 1)])  # No second press with 3V3 up.
        self.assertEqual(board.model.status()["q6a_key_pulses"], 1)
        status = [frame["p"] for frame in board.frames() if frame["t"] == "STATUS"]
        self.assertTrue(status and status[0]["q6a_key_pulses"] == 1)  # labd sees the assist.

    def test_dead_q6a_gets_three_bounded_pulses_and_a_released_line(self):
        board = Board(loops=1000, q6a=0)
        with self.assertRaises(_Stop):
            board.run()
        self.assertEqual(board.key, [(1500, 1, 0), (2400, 0, 0), (7400, 1, 0), (8300, 0, 0),
                                     (13300, 1, 0), (14200, 0, 0)])
        self.assertEqual(board.levels[12], 0)
        self.assertNotIn((17, 0), board.writes)  # MCP reset stays asserted throughout.


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
