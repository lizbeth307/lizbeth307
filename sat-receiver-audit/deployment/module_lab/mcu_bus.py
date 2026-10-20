"""Deterministic MCU interconnect emulation, never a hardware acceptance result.

Models implement documented byte/GPIO contracts independently of the production
drivers. They do not emulate RP2040 instructions, electrical timing, sensor
fusion, noise, USB boot, brownout, flash, or a commissioned ADC.
"""
from contextlib import contextmanager
from collections import deque
import heapq
import importlib.util
import math
from pathlib import Path
import struct
import sys
from types import SimpleNamespace


SOURCE_REFS = {
    "graph": "design/E3.json; design/E5.json",
    "pi4io": "https://www.diodes.com/datasheet/download/PI4IOE5V9555.pdf",
    "veml": "https://www.vishay.com/docs/84286/veml7700.pdf",
    "bno": "https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf",
    "sh2": "https://www.ceva-ip.com/wp-content/uploads/SH-2-Reference-Manual.pdf",
    "micropython": "https://docs.micropython.org/en/v1.26.0/rp2/quickref.html",
    "wdt": "https://docs.micropython.org/en/v1.26.0/library/machine.WDT.html",
    "ntc": "https://semiware.com/uploads/datasheet/MF52A103F3950.pdf",
}


class VirtualClock:
    """Scheduled microsecond clock; time advances only explicitly, no wall sleeps."""
    TICKS_PERIOD = 1 << 30

    def __init__(self, start_ms=0):
        self.us = int(start_ms * 1000)
        self._events, self._order = [], 0

    def now_ms(self):
        return self.us // 1000

    def ticks_ms(self):
        return self.now_ms() % self.TICKS_PERIOD

    def ticks_diff(self, current, previous):
        half = self.TICKS_PERIOD // 2
        return (current - previous + half) % self.TICKS_PERIOD - half

    def schedule_us(self, delay, callback):
        if delay < 0:
            raise ValueError("negative virtual delay")
        self._order += 1
        heapq.heappush(self._events, (self.us + int(delay), self._order, callback))

    def sleep_us(self, value):
        if value < 0:
            raise ValueError("negative sleep")
        target, count = self.us + int(value), 0
        while self._events and self._events[0][0] <= target:
            self.us, unused, callback = heapq.heappop(self._events)
            callback()
            count += 1
            if count > 100000:
                raise RuntimeError("emulation event budget exhausted")
        self.us = target

    def sleep_ms(self, value):
        self.sleep_us(value * 1000)

    advance = sleep_ms


class PinLine:
    def __init__(self, machine, number):
        self.machine, self.number = machine, number
        self.mode, self.pull, self.output = 0, None, 0
        self.external = None
        self.handler, self.trigger, self.hard = None, 0, False
        self.observers = []

    def _level(self):
        if self.mode == 1:  # push-pull OUT
            return self.output
        if self.mode == 2 and not self.output:  # open drain, actively low
            return 0
        if self.external is not None:
            return self.external
        return 1 if self.pull == 1 else 0

    def init(self, mode=None, pull=None, value=None):
        before = self._level()
        if mode is not None:
            self.mode = mode
        self.pull = pull
        if value is not None:
            self.output = int(bool(value))
        self._changed(before)

    def value(self, value=None):
        if value is not None:
            before = self._level()
            self.output = int(bool(value))
            self._changed(before)
        return self._level()

    def drive(self, value):
        """External pull/driver, None means externally disconnected/floating."""
        before = self._level()
        self.external = None if value is None else int(bool(value))
        self._changed(before)

    def _changed(self, before):
        after = self._level()
        self.machine.trace.append((self.machine.clock.us, "pin", self.number,
                                   self.mode, after))
        if before == after:
            return
        for observer in tuple(self.observers):
            observer(before, after)
        edge = 1 if after else 2
        if self.handler is not None and self.trigger & edge:
            if self.machine.irq_enabled:
                self.handler(self)
            else:
                self.machine.pending_irqs[self.number] = self

    def irq(self, handler=None, trigger=3, hard=False):
        self.handler, self.trigger, self.hard = handler, trigger, hard
        return self


class _PinFactory:
    IN, OUT, OPEN_DRAIN, ALT = 0, 1, 2, 3
    PULL_UP, PULL_DOWN = 1, 2
    IRQ_RISING, IRQ_FALLING = 1, 2

    def __init__(self, machine):
        self.machine = machine

    def __call__(self, number, mode=None, pull=None, value=None):
        if isinstance(number, PinLine):
            line = number
        else:
            line = self.machine.pins.setdefault(number, PinLine(self.machine, number))
        if mode is not None or pull is not None or value is not None:
            line.init(mode, pull, value)
        return line


class ADCChannel:
    def __init__(self, machine, pin):
        self.machine = machine
        self.number = pin.number if isinstance(pin, PinLine) else pin

    def read_u16(self):
        value = self.machine.adc_raw.get(self.number)
        if value is None:
            raise OSError("ADC_DISCONNECTED")
        self.machine.trace.append((self.machine.clock.us, "adc", self.number, value))
        return value


class PI4IO9555Model:
    """Two input/output/polarity/config pairs; pointer toggles within a pair."""
    address = 0x20

    def __init__(self, interrupt=None):
        self.interrupt = interrupt
        self._connected = True
        self.external = [255, 0]
        self.reset()

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, value):
        self._connected = bool(value)
        self._interrupt()

    def reset(self):
        self.registers = bytearray((0, 0, 255, 255, 0, 0, 255, 255))
        self.baseline = list(self.external)
        self._interrupt()

    def _input(self, port):
        conf = self.registers[6 + port]
        pins = (self.external[port] & conf) | (self.registers[2 + port] & ~conf & 255)
        return pins ^ self.registers[4 + port]

    def _interrupt(self):
        changed = any((self.external[p] ^ self.baseline[p]) & self.registers[6 + p]
                      for p in (0, 1))
        if self.interrupt is not None:
            self.interrupt.drive(0 if changed and self.connected else 1)

    def set_key(self, bit, pressed):
        if not 0 <= bit < 8:
            raise ValueError("key bit")
        self.external[0] = self.external[0] & ~(1 << bit) if pressed else self.external[0] | 1 << bit
        self._interrupt()

    def read(self, register, count):
        if not self.connected:
            raise OSError("I2C_NACK_PI4IO")
        if not 0 <= register <= 7:
            raise OSError("PI4IO_REGISTER")
        result = bytearray()
        for index in range(count):
            current = register ^ (index & 1)
            if current < 2:
                result.append(self._input(current))
                self.baseline[current] = self.external[current]
            else:
                result.append(self.registers[current])
        self._interrupt()
        return bytes(result)

    def write(self, register, data):
        if not self.connected:
            raise OSError("I2C_NACK_PI4IO")
        if not 0 <= register <= 7:
            raise OSError("PI4IO_REGISTER")
        for index, value in enumerate(data):
            current = register ^ (index & 1)
            if current >= 2:
                self.registers[current] = value
        self._interrupt()


class VEML7700Model:
    """Little-endian command words and independently timed ALS conversions.

    Constant ideal incident lux is a fixture, not optical accuracy or noise.
    Conversion timing is conservatively fixed to +30% datasheet IT tolerance.
    """
    address = 0x10
    _IT = {0: 100, 1: 200, 2: 400, 3: 800, 8: 50, 12: 25}
    _GAIN = {0: 1, 1: 2, 2: 0.125, 3: 0.25}

    def __init__(self, clock):
        self.clock, self.connected = clock, True
        self.lux = 215.04
        self.override_raw = None
        self.reset()

    def reset(self):
        self.registers = {0: 1, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        self.ready_us = None
        self.conversions = 0

    def _period_us(self):
        it = self._IT.get((self.registers[0] >> 6) & 15)
        if it is None:
            raise OSError("VEML_IT_RESERVED")
        return it * 1300

    def _convert(self):
        if self.ready_us is None or self.clock.us < self.ready_us:
            return
        period = self._period_us()
        cycles = 1 + (self.clock.us - self.ready_us) // period
        gain = self._GAIN[(self.registers[0] >> 11) & 3]
        it = self._IT[(self.registers[0] >> 6) & 15]
        # Current Vishay table: gain2/800ms =0.0042; gain1/100ms=0.0672.
        resolution = 0.0672 * (100 / it) / gain
        raw = self.override_raw if self.override_raw is not None else round(self.lux / resolution)
        self.registers[4] = max(0, min(65535, int(raw)))
        self.conversions += cycles
        self.ready_us += cycles * period

    def read(self, register, count):
        if not self.connected:
            raise OSError("I2C_NACK_VEML")
        if count != 2 or register not in self.registers:
            raise OSError("VEML_WORD_REGISTER")
        self._convert()
        return struct.pack("<H", self.registers[register])

    def write(self, register, data):
        if not self.connected:
            raise OSError("I2C_NACK_VEML")
        if len(data) != 2 or register not in (0, 1, 2, 3):
            raise OSError("VEML_WRITE_REGISTER")
        self.registers[register] = struct.unpack("<H", bytes(data))[0]
        if register == 0:
            self.registers[4] = 0
            self.ready_us = None if self.registers[0] & 1 else self.clock.us + self._period_us()


class I2CBus:
    def __init__(self, machine, **options):
        self.machine, self.options = machine, options

    def _device(self, address):
        if not self.machine.Pin(4).value() or not self.machine.Pin(5).value():
            raise OSError("I2C_LINE_STUCK")
        model = self.machine.i2c_models.get(address)
        if model is None:
            raise OSError("I2C_NACK_ADDRESS")
        return model

    def readfrom_mem(self, address, register, count, addrsize=8):
        if addrsize != 8:
            raise OSError("I2C_ADDRESS_SIZE")
        self.machine.trace.append((self.machine.clock.us, "i2c_read", address, register, count))
        value = self._device(address).read(register, count)
        fault = self.machine.i2c_fault
        self.machine.i2c_fault = None
        if fault == "short":
            return value[:-1]
        if fault == "corrupt":
            return bytes((value[0] ^ 1,)) + value[1:]
        if fault == "nack":
            raise OSError("I2C_INJECTED_NACK")
        return value

    def writeto_mem(self, address, register, data, addrsize=8):
        if addrsize != 8:
            raise OSError("I2C_ADDRESS_SIZE")
        self.machine.trace.append((self.machine.clock.us, "i2c_write", address, register, bytes(data)))
        self._device(address).write(register, data)
        return None


class EmulatedUART:
    def __init__(self, machine, number, **options):
        self.machine, self.number, self.options = machine, number, options
        self.baudrate = options.get("baudrate", 115200)
        self.capacity = options.get("txbuf", 256)
        self.rx_capacity = options.get("rxbuf", 256)
        self.rx, self.peer = deque(), None
        self.pending, self.generation = 0, 0
        self.connected, self.enabled, self.blocked = True, True, False
        self.max_write = None
        self.overruns, self.written = 0, bytearray()
        self._end_us = machine.clock.us
        for key in ("tx", "rx"):
            if isinstance(options.get(key), PinLine):
                options[key].mode = 3

    def connect(self, peer):
        if peer.machine.clock is not self.machine.clock:
            raise ValueError("UART endpoints must share the clock")
        self.peer, peer.peer = peer, self

    def write(self, data):
        if not self.enabled:
            raise OSError("UART_DEINITIALIZED")
        if self.blocked:
            return None
        count = min(len(data), self.capacity - self.pending)
        if self.max_write is not None:
            count = min(count, self.max_write)
        if not count:
            return None
        generation = self.generation
        for value in bytes(data[:count]):
            self._end_us = max(self._end_us, self.machine.clock.us) + math.ceil(10_000_000 / self.baudrate)
            self.pending += 1
            def deliver(value=value, generation=generation):
                if generation != self.generation:
                    return
                self.pending -= 1
                if self.connected and self.peer is not None and self.peer.connected and self.peer.enabled:
                    if len(self.peer.rx) < self.peer.rx_capacity:
                        self.peer.rx.append(value)
                    else:
                        self.peer.overruns += 1
            self.machine.clock.schedule_us(self._end_us - self.machine.clock.us, deliver)
        self.written.extend(bytes(data[:count]))
        return count

    def txdone(self):
        return self.pending == 0

    def any(self):
        return len(self.rx)

    def read(self, count=None):
        if not self.enabled or not self.rx:
            return None
        return bytes(self.rx.popleft() for unused in range(min(len(self.rx), len(self.rx) if count is None else count)))

    def deinit(self):
        self.enabled = False
        self.generation += 1
        self.pending = 0
        self.rx.clear()


class BNO085Model:
    """Bounded SPI/SHTP endpoint, synthetic orientation fixtures only.

    Supports reset advertisement, Product ID, Set/Get Feature and Rotation
    Vector packets. It does not implement BNO firmware, fusion or calibration.
    """
    def __init__(self, machine):
        self.machine, self.clock = machine, machine.clock
        self.connected = True
        self.queue, self.commands = deque(), []
        self.device_sequences = [0] * 6
        self.host_sequences = [0] * 6
        self.sample_sequence = 0
        self.feature = None
        self.cs, self.interrupt = machine.Pin(5), machine.Pin(6)
        self.reset_pin, self.wake = machine.Pin(7), machine.Pin(8)
        self.interrupt.drive(1)
        self.cs.observers.append(self._cs_changed)
        self.reset_pin.observers.append(self._reset_changed)
        self.wake.observers.append(lambda before, after: self._irq())
        self._incoming, self._offset, self._outgoing = b"", 0, bytearray()
        self.first_interrupt_with_wake_high = False

    def _irq(self):
        pending = self.connected and (bool(self.queue) or self.wake.value() == 0)
        self.interrupt.drive(0 if pending else 1)

    def _packet(self, channel, payload):
        length = len(payload) + 4
        sequence = self.device_sequences[channel]
        self.device_sequences[channel] = (sequence + 1) & 255
        self.queue.append(struct.pack("<HBB", length, channel, sequence) + bytes(payload))
        self._irq()

    def _reset_changed(self, before, after):
        if after == 0:
            self.queue.clear()
            self.feature = None
            self.device_sequences, self.host_sequences = [0] * 6, [0] * 6
            self.sample_sequence = 0
            self._irq()
        elif before == 0 and self.connected:
            if self.wake.value() != 1:
                raise OSError("BNO_SPI_STRAP_NOT_HIGH")
            self.first_interrupt_with_wake_high = True
            self._packet(1, b"\x01")

    def _cs_changed(self, before, after):
        if after == 0:
            self._incoming = self.queue.popleft() if self.queue else b""
            self._offset, self._outgoing = 0, bytearray()
        elif before == 0:
            self._command()
            self._irq()

    def exchange(self, data):
        if self.cs.value() != 0:
            raise OSError("SPI_WITHOUT_CS")
        if not self.connected:
            raise OSError("SPI_DISCONNECTED")
        self._outgoing.extend(bytes(data))
        value = self._incoming[self._offset:self._offset + len(data)]
        self._offset += len(data)
        return value + bytes(len(data) - len(value))

    def _command(self):
        if len(self._outgoing) < 4:
            return
        length, channel, sequence = struct.unpack("<HBB", self._outgoing[:4])
        if length == 0:
            return
        if length < 4 or length > len(self._outgoing) or channel != 2:
            raise OSError("BNO_BAD_HOST_PACKET")
        if sequence != self.host_sequences[channel]:
            raise OSError("BNO_HOST_SEQUENCE")
        self.host_sequences[channel] = (sequence + 1) & 255
        payload = bytes(self._outgoing[4:length])
        self.commands.append(payload)
        if payload == b"\xf9\x00":
            # Explicit synthetic Product ID; not a claim about an installed chip.
            self._packet(2, b"\xf8\x01\x01\x00" + struct.pack("<IIH", 0xE0000001, 1, 0) + b"\x00\x00")
        elif len(payload) == 17 and payload[0] == 0xfd:
            self.feature = payload
        elif payload == b"\xfe\x05" and self.feature is not None:
            self._packet(2, b"\xfc" + self.feature[1:])
        else:
            raise OSError("BNO_UNSUPPORTED_COMMAND")

    def queue_rotation(self, quaternion=(0, 0, 0, 1), status=3, age_ms=0,
                       accuracy_rad=0.125, sample_sequence=None):
        if self.feature is None:
            raise ValueError("feature not enabled")
        sequence = self.sample_sequence if sample_sequence is None else sample_sequence
        self.sample_sequence = (sequence + 1) & 255
        values = [round(float(value) * 16384) for value in quaternion]
        report = bytes((5, sequence, status & 3, 0)) + struct.pack("<hhhhh", *values, round(accuracy_rad * 4096))
        self._packet(3, b"\xfb" + struct.pack("<i", round(age_ms * 10)) + report)

    def corrupt_next_header(self, raw_length=0xffff):
        if not self.queue:
            raise ValueError("no queued packet")
        packet = self.queue.popleft()
        self.queue.appendleft(struct.pack("<H", raw_length) + packet[2:])


class EmulatedSPI:
    MSB = 0

    def __init__(self, machine, number, **options):
        self.machine, self.number, self.options = machine, number, options
        if (number != 0 or options.get("polarity") != 1 or options.get("phase") != 1
                or options.get("bits", 8) != 8):
            raise ValueError("BNO model requires the actual SPI0 mode3 wiring")
        for key, gpio in (("sck", 2), ("mosi", 3), ("miso", 4)):
            if options.get(key) is not machine.Pin(gpio):
                raise ValueError("BNO SPI GPIO mismatch")

    def write_readinto(self, outgoing, incoming):
        if len(outgoing) != len(incoming):
            raise ValueError("full-duplex sizes differ")
        self.machine.trace.append((self.machine.clock.us, "spi", bytes(outgoing)))
        incoming[:] = self.machine.bno.exchange(outgoing)


class _SPIFactory:
    MSB = 0

    def __init__(self, machine):
        self.machine = machine

    def __call__(self, number, **options):
        return EmulatedSPI(self.machine, number, **options)


class Watchdog:
    def __init__(self, machine, timeout):
        if type(timeout) is not int or not 1 <= timeout <= 8388:
            raise ValueError("RP2040 WDT timeout")
        self.machine, self.timeout, self.version = machine, timeout, 0
        self.feed()

    def feed(self):
        self.version += 1
        version = self.version
        def expire():
            if self.version == version:
                self.machine.reset("WDT")
        self.machine.clock.schedule_us(self.timeout * 1000, expire)


class EmulatedMachine:
    """MicroPython-compatible factories, one independent MCU pin namespace."""
    def __init__(self, clock=None, role="pico"):
        if role not in ("pico", "imu"):
            raise ValueError("unknown MCU role")
        self.clock, self.role = clock or VirtualClock(), role
        self.pins, self.adc_raw, self.uarts, self.trace = {}, {}, {}, []
        self.i2c_models, self.i2c_fault = {}, None
        self.irq_enabled, self.pending_irqs = True, {}
        self.Pin = _PinFactory(self)
        self.SPI = _SPIFactory(self)
        self.reset_count, self.reset_reason, self.clock_hz = 0, None, 125000000
        self.wdt = None
        if role == "pico":
            for gpio in (2, 3, 4, 5, 6, 7, 10, 11, 17, 22):
                self.Pin(gpio).drive(1)
            self.Pin(14).drive(0)
            self.pi4io = PI4IO9555Model(self.Pin(10))
            self.veml = VEML7700Model(self.clock)
            self.i2c_models = {0x20: self.pi4io, 0x10: self.veml}
            self.set_ntc_resistance(26, 10000)
            self.set_ntc_resistance(28, 10000)
            self.set_battery_mv(14400)
        else:
            self.Pin(5).drive(1)
            self.Pin(6).drive(1)
            self.Pin(7).drive(1)
            self.Pin(8).drive(1)
            self.bno = BNO085Model(self)

    def ADC(self, pin):
        return ADCChannel(self, pin)

    def SoftI2C(self, **options):
        if options.get("sda") is not self.Pin(4) or options.get("scl") is not self.Pin(5):
            raise ValueError("I2C0 graph GPIO mismatch")
        return I2CBus(self, **options)

    def I2C(self, number, **options):
        if number != 0:
            raise ValueError("only Pico HMI I2C0 modeled")
        return self.SoftI2C(**options)

    def UART(self, number, **options):
        uart = EmulatedUART(self, number, **options)
        self.uarts[number] = uart
        return uart

    def WDT(self, id=0, timeout=5000):
        if self.wdt is not None:
            raise ValueError("model WDT already enabled")
        self.wdt = Watchdog(self, timeout)
        return self.wdt

    def freq(self, value=None):
        if value is not None:
            self.clock_hz = value
        return self.clock_hz

    def unique_id(self):
        return b"EMU-PICO" if self.role == "pico" else b"EMU-IMU0"

    def disable_irq(self):
        old, self.irq_enabled = self.irq_enabled, False
        return old

    def enable_irq(self, old):
        self.irq_enabled = old
        if old:
            pending, self.pending_irqs = self.pending_irqs, {}
            for pin in pending.values():
                if pin.handler is not None:
                    pin.handler(pin)

    def reset(self, reason="SOFT"):
        self.reset_count += 1
        self.reset_reason = reason
        for uart in self.uarts.values():
            uart.deinit()
        for pin in self.pins.values():
            pin.handler = None
            pin.init(self.Pin.IN)
        # The host test can reconstruct Hardware after this pad reset. This is
        # deliberately not an instruction-level interpreter restart simulation.

    @property
    def mcp_reset_asserted(self):
        # Graph R395 biases Q306 gate HIGH when powered Pico GP17 is high-Z.
        return bool(self.Pin(17).value())

    def set_battery_mv(self, value):
        # Nominal 100k/20k divider and 3.0V reference fixture, NOT calibration.
        self.set_adc_voltage(27, value / 6000)

    def set_adc_voltage(self, gpio, value, reference=3.0):
        self.adc_raw[gpio] = max(0, min(65535, round(value / reference * 65535)))

    def set_ntc_resistance(self, gpio, ohms):
        if ohms is None:  # physically open NTC -> full-scale pull-up
            self.adc_raw[gpio] = 65535
        else:
            self.adc_raw[gpio] = round(65535 * ohms / (10000 + ohms))

    def turn_encoder(self, encoder=1, cycles=1, reverse=False):
        a, b = (2, 3) if encoder == 1 else (6, 7)
        pattern = ((0, 1), (0, 0), (1, 0), (1, 1))
        if reverse:
            pattern = ((1, 0), (0, 0), (0, 1), (1, 1))
        for unused in range(cycles):
            for va, vb in pattern:
                self.Pin(a).drive(va)
                self.Pin(b).drive(vb)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_firmware(project=None):
    """Load actual source modules; activation isolates firmware's flat imports."""
    project = Path(project) if project is not None else Path(__file__).resolve().parents[2]
    prefix = "_module_lab_fw_" + str(abs(hash(str(project.resolve()))))
    pico = project / "firmware/pico"
    calibration = _load(pico / "calibration.py", prefix + "_calibration")
    hmi = _load(pico / "hmi.py", prefix + "_hmi")
    wire = _load(project / "software/srrx/wire.py", prefix + "_wire")

    @contextmanager
    def activate():
        aliases = {"calibration": calibration, "hmi": hmi, "wire": wire}
        previous = {name: sys.modules.get(name) for name in aliases}
        sys.modules.update(aliases)
        try:
            yield
        finally:
            for name, old in previous.items():
                if old is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = old

    with activate():
        adapter = _load(pico / "adapter.py", prefix + "_adapter")
        relay = _load(pico / "imu_relay.py", prefix + "_relay")
        supervisor = _load(pico / "supervisor.py", prefix + "_supervisor")
        main = _load(pico / "main.py", prefix + "_main")
        peripherals = _load(project / "software/srrx/peripherals.py", prefix + "_peripherals")
        package = type(sys)(prefix + "_imu")
        package.__path__ = [str(project / "firmware/imu")]
        sys.modules[package.__name__] = package
        shtp = _load(project / "firmware/imu/shtp.py", package.__name__ + ".shtp")
        session = _load(project / "firmware/imu/session.py", package.__name__ + ".session")
        device = _load(project / "firmware/imu/device.py", package.__name__ + ".device")
    return SimpleNamespace(project=project, activate=activate, calibration=calibration,
                           hmi=hmi, adapter=adapter, relay=relay, supervisor=supervisor,
                           main=main, peripherals=peripherals, wire=wire, shtp=shtp,
                           session=session, device=device)
