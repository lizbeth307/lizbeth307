"""Portable PI4IO9555/VEML7700 input core. No power/ARM API exists here.

DEFAULT_WIRING is checked against design/E3.json by the host wrapper/tests.
The actual bus belongs exclusively to Pico, not a Q6A /dev/i2c node.
"""
DOMAIN = "pico_hmi_i2c0"
KEY_NAMES = ("HOME", "BACK", "REC", "MARK", "FN", "LOCK", "ENC1_PRESS", "ENC2_PRESS")
DEFAULT_WIRING = {"domain": DOMAIN, "key_address": 0x20, "light_address": 0x10,
                  "sda_gpio": 4, "scl_gpio": 5, "interrupt_gpio": 10,
                  "encoder_gpios": ((2, 3), (6, 7)), "keys": KEY_NAMES}
_TRANSITIONS = (0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0)


class Quadrature:
    """IRQ-safe bounded pending full-cycle counts; drain with IRQs disabled.

    update uses only small integers and no allocation. Four legal transitions
    make one full quadrature cycle. Mechanical direction/detent ratio must be
    checked on the purchased encoder; this is not a manufacturer's RPM test.
    """
    def __init__(self, a=1, b=1):
        self.state = (a << 1) | b
        self.quarters = 0
        self.pending = 0
        self.invalid = False
        self.overflow = False

    def update(self, a, b):
        state = (a << 1) | b
        previous = self.state
        if previous == state:
            return
        self.state = state
        if previous ^ state == 3:
            self.quarters = 0
            self.invalid = True
            return
        self.quarters += _TRANSITIONS[(previous << 2) | state]
        if self.quarters >= 4:
            self.quarters -= 4
            if self.pending >= 32767:
                self.overflow = True
                self.pending = 0
            else:
                self.pending += 1
        elif self.quarters <= -4:
            self.quarters += 4
            if self.pending <= -32767:
                self.overflow = True
                self.pending = 0
            else:
                self.pending -= 1

    def drain(self):
        error = "ENCODER_OVERRUN" if self.overflow else "ENCODER_TRANSITION" if self.invalid else None
        result = (0 if error else self.pending, error)
        self.pending = 0
        self.invalid = self.overflow = False
        if error:
            self.quarters = 0
        return result


def _read(transport, address, register, size):
    value = transport.read(address, register, size)
    if not isinstance(value, (bytes, bytearray)) or len(value) != size:
        raise OSError("SHORT_READ")
    return value


def _write(transport, address, register, value):
    result = transport.write(address, register, value)
    # Public I2CTransport returns None; adapters may return transferred data bytes.
    if result is not None and result != len(value):
        raise OSError("SHORT_WRITE")


def _word(value):
    return value[0] | value[1] << 8


class AmbientLight:
    LOW, HIGH = (0x1300, 25, 2.1504), (0x08c0, 800, 0.0042)

    def __init__(self, transport, address=0x10):
        self.transport, self.address = transport, address
        self.profile = self.LOW
        self.configured = False
        self.ready_at = 0
        self.next_at = 0
        self.value = None
        self.sample_at = None
        self.acquisition_ms = 0
        self.error = "ALS_STARTING"

    def _profile(self, profile, now_ms):
        configuration, integration, unused = profile
        _write(self.transport, self.address, 0x00, bytes((configuration & 255, configuration >> 8)))
        if _word(_read(self.transport, self.address, 0x00, 2)) != configuration:
            raise OSError("ALS_CONFIG_CHANGED")
        self.profile = profile
        self.acquisition_ms = (integration * 13 + 9) // 10
        self.ready_at = now_ms + self.acquisition_ms + 50
        self.next_at = self.ready_at
        self.sample_at = None
        self.value = None
        self.error = "ALS_INTEGRATING"

    def poll(self, now_ms):
        if now_ms < self.next_at:
            return
        if not self.configured:
            # Explicitly disable power saving: otherwise refresh includes PSM.
            _write(self.transport, self.address, 0x03, b"\x00\x00")
            self._profile(self.LOW, now_ms)
            self.configured = True
            return
        if now_ms < self.ready_at:
            return
        configuration, integration, resolution = self.profile
        if _word(_read(self.transport, self.address, 0x00, 2)) != configuration:
            raise OSError("ALS_CONFIG_CHANGED")
        raw = _word(_read(self.transport, self.address, 0x04, 2))
        uncorrected = raw * resolution
        if self.profile == self.LOW and uncorrected < 40:
            self._profile(self.HIGH, now_ms)
            return
        if self.profile == self.HIGH and (uncorrected > 90 or raw == 65535):
            self._profile(self.LOW, now_ms)
            return
        value = uncorrected
        if self.profile == self.LOW and value > 1000:
            # Vishay AN84323 empirical correction, not installed-cover calibration.
            value = (((6.0135e-13 * value - 9.3924e-9) * value + 8.1488e-5) * value + 1.0023) * value
        self.next_at = now_ms + max(100, self.acquisition_ms + 50)
        if raw == 65535 or not 0 <= value <= 140000:
            self.value = None
            self.sample_at = None
            self.error = "ALS_OUT_OF_RANGE"
            return
        self.value = round(value, 4)
        self.sample_at = now_ms
        self.error = None

    def failed(self, now_ms, error="ALS_IO_ERROR"):
        self.value = self.sample_at = None
        self.configured = False
        self.next_at = now_ms + 1000
        self.error = error

    def status(self, now_ms):
        age = None if self.sample_at is None else now_ms - self.sample_at + self.acquisition_ms
        valid = age is not None and 0 <= age < 2000 and self.value is not None
        return self.value if valid else None, valid, age


class PeripheralPoller:
    physical_qualified = False
    # Three separate pairs: the PI4IO pointer toggles inside each pair only.
    REGISTER_IMAGE = ((2, b"\x00\x00"), (4, b"\x00\x00"), (6, b"\xff\x00"))

    def __init__(self, transport, wiring=None):
        if getattr(transport, "domain", None) != DOMAIN:
            raise ValueError("HMI transport must own the separate Pico I2C0 bus")
        if wiring is not None and wiring != DEFAULT_WIRING:
            raise ValueError("Graph wiring requires a reviewed firmware mapping update")
        if getattr(transport, "hmi_claimed", False):
            raise ValueError("HMI bus already has an owner")
        transport.hmi_claimed = True
        self.transport = transport
        self.wiring = dict(DEFAULT_WIRING)
        self.light = AmbientLight(transport, self.wiring["light_address"])
        self._now = None
        self._clock_fault = False
        self._configured = False
        self._recover = True
        self._retry_at = 0
        self._next_keys = 0
        self._verify_at = 0
        self._last_keys_at = None
        self._candidate = self._stable = 0
        self._changed_at = [0] * 8
        self.presses = [0] * 8
        self.encoders = [0, 0]
        self._encoder_ok = False
        self.sequence = 0
        self.generation = 0
        self.error = "HMI_STARTING"

    def _mark(self, error):
        self.generation = (self.generation + 1) & 65535
        self.error = error

    def _initialize(self, now_ms):
        if self._recover:
            recover = getattr(self.transport, "recover", None)
            if recover is None or recover() is False:
                raise OSError("HMI_RECOVERY_UNAVAILABLE")
            self._recover = False
        address = self.wiring["key_address"]
        for register, image in self.REGISTER_IMAGE:
            _write(self.transport, address, register, image)
        self._verify()
        ports = _read(self.transport, address, 0, 2)
        # Held keys at boot/recovery form a baseline, not synthetic press edges.
        self._candidate = self._stable = (~ports[0]) & 255
        self._changed_at = [now_ms] * 8
        self._last_keys_at = now_ms
        self._configured = True
        self._verify_at = now_ms + 1000
        self._next_keys = now_ms + 20
        if self._encoder_ok:
            self.error = None

    def _verify(self):
        for register, image in self.REGISTER_IMAGE:
            if _read(self.transport, self.wiring["key_address"], register, 2) != image:
                raise OSError("HMI_CONFIG_CHANGED")

    def _keys(self, now_ms):
        if now_ms >= self._verify_at:
            self._verify()
            self._verify_at = now_ms + 1000
        ports = _read(self.transport, self.wiring["key_address"], 0, 2)
        pressed = (~ports[0]) & 255
        for bit in range(8):
            mask = 1 << bit
            if (pressed ^ self._candidate) & mask:
                self._candidate ^= mask
                self._changed_at[bit] = now_ms
            if now_ms - self._changed_at[bit] >= 30 and (self._stable ^ self._candidate) & mask:
                self._stable ^= mask
                if self._stable & mask:
                    self.presses[bit] = (self.presses[bit] + 1) & 65535
        self._last_keys_at = now_ms
        self._next_keys = now_ms + 20

    def _encoders(self):
        sample = getattr(self.transport, "sample_encoders", None)
        if sample is None:
            raise OSError("ENCODERS_UNAVAILABLE")
        samples = sample()
        if not isinstance(samples, (tuple, list)) or len(samples) != 2:
            raise OSError("ENCODERS_INVALID")
        self._encoder_ok = True
        for index in range(2):
            delta, error = samples[index]
            if error or type(delta) is not int or not -32767 <= delta <= 32767:
                self._encoder_ok = False
                self._mark("ENCODER_OVERRUN" if error == "ENCODER_OVERRUN" else "ENCODER_TRANSITION")
            else:
                self.encoders[index] = ((self.encoders[index] + delta + 0x80000000) & 0xffffffff) - 0x80000000

    def poll(self, now_ms):
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("invalid monotonic HMI time")
        if self._now is not None and now_ms < self._now:
            self._clock_fault = True
            self._mark("HMI_CLOCK_REVERSED")
        if self._clock_fault:
            return self.snapshot(now_ms)
        if self._now is not None and now_ms - self._now > 100:
            self._configured = False
            self._mark("HMI_POLL_GAP")
        self._now = now_ms
        if self._configured:
            self.error = None  # A key-bus root cause stays until _initialize succeeds.
        try:
            self._encoders()
            if not self._configured and now_ms >= self._retry_at:
                self._initialize(now_ms)
            elif self._configured and (now_ms >= self._next_keys or
                    getattr(self.transport, "interrupt_pending", lambda: False)()):
                self._keys(now_ms)
        except (OSError, ValueError, TypeError, IndexError) as exc:
            self._configured = False
            self._recover = True
            self._retry_at = now_ms + 1000
            self._mark(str(exc)[:32] or "HMI_IO_ERROR")
        try:
            self.light.poll(now_ms)
        except (OSError, ValueError, TypeError, IndexError):
            # Lux-only fault: keys keep their baseline; a shared-bus fault is
            # caught by the key path's own reads and 1 s readback.
            self.light.failed(now_ms, "ALS_IO_ERROR")
        if self.sequence < 0xffffffff:
            self.sequence += 1
        else:
            self._clock_fault = True
            self._mark("HMI_SEQUENCE_EXHAUSTED")
        return self.snapshot(now_ms)

    def snapshot(self, now_ms):
        age = 65535 if self._last_keys_at is None else max(0, now_ms - self._last_keys_at)
        ok = self._configured and self._encoder_ok and not self._clock_fault and age < 100
        lux, lux_valid, lux_age = self.light.status(now_ms)
        return {"ok": bool(ok), "fresh": bool(ok), "age_ms": min(age, 65535),
                "keys": self._stable if ok else 0, "presses": list(self.presses),
                "encoders": list(self.encoders), "lux": lux,
                "lux_valid": bool(lux_valid and not self._clock_fault),
                "lux_age_ms": lux_age, "sequence": self.sequence,
                "generation": self.generation,
                "error": self.error or (None if ok else "HMI_STALE") or self.light.error}
