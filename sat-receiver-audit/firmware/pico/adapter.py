"""MicroPython RP2040 adapter. Importable on CPython for clock/GPIO tests."""
from calibration import ntc_temperature


def write_all(uart, packet, ticks_ms, ticks_diff, sleep_ms, timeout_ms=100):
    """Retry short writes under one bounded deadline; never silently truncate."""
    start = ticks_ms()
    offset = 0
    view = memoryview(packet)
    while offset < len(packet):
        if ticks_diff(ticks_ms(), start) >= timeout_ms:
            raise OSError("UART transmit deadline")
        count = uart.write(view[offset:])
        if count is None or count == 0:
            sleep_ms(1)
            continue
        if type(count) is not int or not 0 < count <= len(packet) - offset:
            raise OSError("invalid UART write result")
        offset += count


class TickClock:
    """Unwrap ticks_ms with ticks_diff; sample more often than half its period."""
    def __init__(self, ticks_ms, ticks_diff):
        self._ticks_ms = ticks_ms
        self._ticks_diff = ticks_diff
        self._previous = ticks_ms()
        self._elapsed = 0

    def now_ms(self):
        current = self._ticks_ms()
        delta = self._ticks_diff(current, self._previous)
        if delta < 0:
            raise RuntimeError("tick sampling gap/reversed clock")
        self._elapsed += delta
        self._previous = current
        return self._elapsed


class PicoHMITransport:
    """Sole owner of actual Pico GP4/5 I2C and GP2/3/6/7 encoder inputs."""
    domain = "pico_hmi_i2c0"

    def __init__(self, machine_module=None, time_module=None):
        if machine_module is None:
            import machine as machine_module
        if time_module is None:
            import time as time_module
        from hmi import Quadrature
        try:
            import micropython
            micropython.alloc_emergency_exception_buf(100)
        except ImportError:
            pass
        self.machine, self.time = machine_module, time_module
        Pin = self.machine.Pin
        self.sda, self.scl = Pin(4, Pin.IN), Pin(5, Pin.IN)
        self.interrupt = Pin(10, Pin.IN)
        self.a1, self.b1 = Pin(2, Pin.IN), Pin(3, Pin.IN)
        self.a2, self.b2 = Pin(6, Pin.IN), Pin(7, Pin.IN)
        self.encoder1 = Quadrature(self.a1.value(), self.b1.value())
        self.encoder2 = Quadrature(self.a2.value(), self.b2.value())
        self.i2c = None
        trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING
        self.a1.irq(handler=self._encoder_one, trigger=trigger, hard=True)
        self.b1.irq(handler=self._encoder_one, trigger=trigger, hard=True)
        self.a2.irq(handler=self._encoder_two, trigger=trigger, hard=True)
        self.b2.irq(handler=self._encoder_two, trigger=trigger, hard=True)

    def _encoder_one(self, pin):
        self.encoder1.update(self.a1.value(), self.b1.value())

    def _encoder_two(self, pin):
        self.encoder2.update(self.a2.value(), self.b2.value())

    def sample_encoders(self):
        # Copy only small scalars with interrupts disabled; allocate result tuples
        # after restoring IRQs so a GC cannot stall input capture inside this block.
        mask = self.machine.disable_irq()
        try:
            first, second = self.encoder1.pending, self.encoder2.pending
            bad1, bad2 = self.encoder1.invalid, self.encoder2.invalid
            over1, over2 = self.encoder1.overflow, self.encoder2.overflow
            self.encoder1.pending = self.encoder2.pending = 0
            self.encoder1.invalid = self.encoder2.invalid = False
            self.encoder1.overflow = self.encoder2.overflow = False
            if bad1 or over1:
                self.encoder1.quarters = 0
            if bad2 or over2:
                self.encoder2.quarters = 0
        finally:
            self.machine.enable_irq(mask)
        error1 = "ENCODER_OVERRUN" if over1 else "ENCODER_TRANSITION" if bad1 else None
        error2 = "ENCODER_OVERRUN" if over2 else "ENCODER_TRANSITION" if bad2 else None
        return ((0 if error1 else first, error1), (0 if error2 else second, error2))

    def interrupt_pending(self):
        return self.interrupt.value() == 0

    def recover(self):
        Pin = self.machine.Pin
        self.sda.init(Pin.OPEN_DRAIN, value=1)
        self.scl.init(Pin.OPEN_DRAIN, value=1)
        for unused in range(9):
            self.scl.value(0)
            self.time.sleep_us(5)
            self.scl.value(1)
            self.time.sleep_us(5)
            if not self.scl.value():
                raise OSError("HMI_SCL_STUCK")
        # STOP: SDA low, release SCL, then release SDA. No unbounded wait.
        self.scl.value(0)
        self.sda.value(0)
        self.time.sleep_us(5)
        self.scl.value(1)
        self.time.sleep_us(5)
        self.sda.value(1)
        self.time.sleep_us(5)
        if not self.sda.value() or not self.scl.value():
            raise OSError("HMI_BUS_STUCK")
        # Timeout is per clock-stretch wait; all transactions have fixed size.
        self.i2c = self.machine.SoftI2C(sda=self.sda, scl=self.scl,
                                       freq=100000, timeout=200)
        return True

    def read(self, address, register, count):
        if self.i2c is None:
            raise OSError("HMI_NOT_RECOVERED")
        return self.i2c.readfrom_mem(address, register, count, addrsize=8)

    def write(self, address, register, data):
        if self.i2c is None:
            raise OSError("HMI_NOT_RECOVERED")
        return self.i2c.writeto_mem(address, register, data, addrsize=8)


class Hardware:
    def __init__(self, calibration=None, machine_module=None):
        if machine_module is None:
            import machine as machine_module
        self.machine = machine_module
        Pin = self.machine.Pin
        self.pins = {}
        # Keep this exact ordering. These must precede ADC/UART initialization.
        for name, gpio, value in (("mcp_reset", 17, 1), ("disp_en", 16, 0),
                                  ("fan_en", 18, 1), ("blower_en", 19, 1),
                                  ("pico_off", 13, 0), ("q6a_key", 12, 0),
                                  ("piezo", 20, 0), ("led", 21, 1)):
            self.pins[name] = Pin(gpio, Pin.OUT, value=value)
        self.safe_boot = Pin(15, Pin.IN)
        Pin(0, Pin.IN)
        Pin(1, Pin.IN)
        Pin(8, Pin.IN)
        Pin(9, Pin.IN)
        self.q6a_on = Pin(14, Pin.IN)
        self.button = Pin(11, Pin.IN)  # External pullup and BAT54, active LOW.
        self.tach = Pin(22, Pin.IN)    # External 10k to Pico3V3, 2.2k series.
        self.calibration = calibration
        self.adc_panel = self.machine.ADC(Pin(26))
        self.adc_battery = self.machine.ADC(Pin(27))
        self.adc_case = self.machine.ADC(Pin(28))
        self.uart = None
        self._fan_on_at = None
        self._tach_at = None
        self._tach_counter = 0
        self._tach_seen = 0
        self.tach.irq(trigger=Pin.IRQ_FALLING, handler=self._tach_irq)
        self.raw = {}

    def _tach_irq(self, pin):
        # Bounded small integer only; do not allocate or print in the handler.
        self._tach_counter = (self._tach_counter + 1) & 0xffff

    def link_power(self, powered):
        Pin = self.machine.Pin
        if powered and self.uart is None:
            # Assert SAFE_BOOT before selecting UART alternate functions.
            self.safe_boot.init(Pin.OUT, value=1)
            self.uart = self.machine.UART(0, baudrate=115200, bits=8, parity=None,
                                         stop=1, tx=Pin(0), rx=Pin(1),
                                         timeout=0, timeout_char=0, rxbuf=1024)
        elif not powered:
            if self.uart is not None:
                self.uart.deinit()
                self.uart = None
            Pin(0, Pin.IN)
            Pin(1, Pin.IN)
            self.safe_boot.init(Pin.IN)

    def sample(self, now_ms):
        q6a_on = bool(self.q6a_on.value())
        self.link_power(q6a_on)
        panel = battery = case = None
        try:
            self.raw = {"panel": self.adc_panel.read_u16(),
                        "battery": self.adc_battery.read_u16(),
                        "case": self.adc_case.read_u16()}
            if self.calibration is not None:
                battery = self.calibration.battery_mv(self.raw["battery"])
                panel = self.calibration.temperature_c(self.raw["panel"], "panel")
                case = self.calibration.temperature_c(self.raw["case"], "case")
            else:
                # Nominal NTC conversion can operate cooling, never authorizes ARM.
                panel = ntc_temperature(self.raw["panel"])
                case = ntc_temperature(self.raw["case"])
        except (OSError, ValueError, TypeError):
            self.raw = {}
        if self._tach_counter != self._tach_seen:
            self._tach_seen = self._tach_counter
            self._tach_at = now_ms
        fan_on = bool(self.pins["fan_en"].value())
        if fan_on:
            if self._fan_on_at is None:
                self._fan_on_at = now_ms
                self._tach_at = now_ms
        else:
            self._fan_on_at = self._tach_at = None
        stalled = (fan_on and self._fan_on_at is not None
                   and now_ms - self._fan_on_at > 2000
                   and now_ms - self._tach_at > 2000)
        return {"q6a_on": q6a_on, "battery_mv": battery,
                "panel_temp_c": panel, "case_temp_c": case,
                "button_pressed": not bool(self.button.value()),
                "fan_stalled": stalled}

    def apply(self, outputs):
        # Assert RESET before changing other enables; release it only last.
        if outputs["mcp_reset"]:
            self.pins["mcp_reset"].value(1)
        for name in ("disp_en", "fan_en", "blower_en", "pico_off", "q6a_key", "led"):
            self.pins[name].value(1 if outputs[name] else 0)
        if self.uart is not None and self.q6a_on.value():
            self.safe_boot.init(self.machine.Pin.OUT, value=1 if outputs["safe_boot"] else 0)
        else:
            self.safe_boot.init(self.machine.Pin.IN)
        if not outputs["mcp_reset"]:
            self.pins["mcp_reset"].value(0)

    def fail_safe(self):
        self.pins["mcp_reset"].value(1)
        self.pins["disp_en"].value(0)
        self.pins["fan_en"].value(1)
        self.pins["blower_en"].value(1)
        self.pins["q6a_key"].value(0)
        self.pins["pico_off"].value(0)
        self.pins["led"].value(1)
        if self.q6a_on.value():
            self.safe_boot.init(self.machine.Pin.OUT, value=1)
        else:
            self.link_power(False)
