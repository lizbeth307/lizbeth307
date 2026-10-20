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
