"""MCP23017 transport and safe output image derived from design/E3.json.

Microchip DS20001952D, BANK=0 registers. A real Pico-controlled RESET
must precede initialize_safe(); guessing BANK on an already running chip
can write a different register. CHG_INHIBIT is asserted *after* reset;
its high-impedance reset interval is not a charger interlock guarantee.
https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf
"""
from __future__ import annotations

import fcntl
import json
import os
import threading
from pathlib import Path


class HardwareError(RuntimeError):
    pass


ADDRESSES = (0x20, 0x22, 0x23)
IODIR, GPINTEN, IOCON, GPPU, GPIO, OLAT = 0x00, 0x04, 0x0A, 0x0C, 0x12, 0x14
I2C_SLAVE = 0x0703


def load_mapping(path=None):
    """Return only physically assigned GPIOs; port 7 NC pads stay outputs."""
    path = Path(path) if path else Path(__file__).resolve().parents[2] / "design/E3.json"
    graph = json.loads(path.read_text(encoding="utf-8"))
    result = {"inputs": {}, "outputs": {}, "source": str(path)}
    for component in graph["components"]:
        if component["ref"] not in {"U301", "U302", "U303"}:
            continue
        address = {"U301": 0x20, "U302": 0x22, "U303": 0x23}[component["ref"]]
        for pin in component["pins"]:
            number = int(pin["number"]) if str(pin["number"]).isdigit() else -1
            if 21 <= number <= 28:
                port, bit = 0, number - 21
            elif 1 <= number <= 8:
                port, bit = 1, number - 1
            else:
                continue
            if pin.get("nc"):
                continue
            direction = {"input": "inputs", "output": "outputs"}.get(pin["type"])
            if direction is None or (direction == "inputs" and bit == 7):
                raise HardwareError("Invalid MCP GPIO direction in design graph")
            net = pin["net"]
            if net in result["inputs"] or net in result["outputs"]:
                raise HardwareError("Duplicate MCP net: " + net)
            result[direction][net] = {"address": address, "port": port, "bit": bit}
    _validate_mapping(result)
    return result


def _validate_mapping(mapping):
    used = set()
    for direction in ("inputs", "outputs"):
        for net, pin in mapping[direction].items():
            key = (pin["address"], pin["port"], pin["bit"])
            if key in used or key[0] not in ADDRESSES or key[1] not in (0, 1) or key[2] not in range(8):
                raise HardwareError("Invalid/duplicate mapped GPIO: " + net)
            if direction == "inputs" and key[2] == 7:
                raise HardwareError("GPA7/GPB7 are output-only")
            used.add(key)
    if "CHG_INHIBIT" not in mapping["outputs"] or "OVP_LNB_N" not in mapping["inputs"]:
        raise HardwareError("Incomplete safety mapping")


def _safe(mapping):
    return {net: net == "CHG_INHIBIT" for net in mapping["outputs"]}


class SimHardware:
    """Explicit simulation: no ADC samples and no physical acceptance implied."""
    physical = False

    def __init__(self, mapdata=None):
        self.mapping = mapdata if mapdata is not None else load_mapping()
        _validate_mapping(self.mapping)
        self.outputs = _safe(self.mapping)
        self.inputs = {net: net.startswith(("FAULT_", "FLT_", "DCS_")) or net == "SLED_DET"
                       for net in self.mapping["inputs"]}
        self.trace = []
        self.initialized = False
        self.faulted = False
        self.closed = False
        self.bus = self

    def initialize_safe(self):
        if self.closed or self.faulted:
            raise HardwareError("Hardware requires a fresh reset/recreation")
        self.outputs = _safe(self.mapping)
        self.initialized = True
        self.trace.append({"event": "initialize_safe", "outputs": dict(self.outputs)})

    def read_inputs(self):
        self._ready()
        return dict(self.inputs)

    def set_inputs(self, values):
        if set(values) - set(self.inputs) or any(type(v) is not bool for v in values.values()):
            raise ValueError("Unknown input or non-boolean level")
        self.inputs.update(values)

    def apply_outputs(self, values):
        self._ready()
        self._validate_outputs(values)
        self.outputs.update(values)
        self.trace.append({"event": "outputs", "outputs": dict(self.outputs)})

    def _validate_outputs(self, values):
        if set(values) - set(self.outputs) or any(type(v) is not bool for v in values.values()):
            raise HardwareError("Unknown output or non-boolean level")

    def _ready(self):
        if not self.initialized or self.closed or self.faulted:
            raise HardwareError("Hardware unavailable or fault latched")

    def all_off(self):
        self.outputs = _safe(self.mapping)
        self.trace.append({"event": "all_off", "outputs": dict(self.outputs)})

    def read(self, address, register, count):
        raise HardwareError("Simulation has no invented ADC register data")

    def write(self, address, register, data):
        raise HardwareError("Simulation has no physical I2C bus")

    def close(self):
        self.all_off()
        self.closed = True


class _I2CTransport:
    def __init__(self, path):
        self.fd = os.open(path, os.O_RDWR | os.O_CLOEXEC)
        self.lock = threading.RLock()
        try:
            # Advisory ownership held for the entire daemon lifetime.
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception:
            os.close(self.fd)
            raise

    def read(self, address, register, count):
        if not 0x03 <= address <= 0x77 or not 0 <= register <= 255 or not 1 <= count <= 255:
            raise ValueError("Invalid I2C transaction")
        with self.lock:
            fcntl.ioctl(self.fd, I2C_SLAVE, address)
            if os.write(self.fd, bytes([register])) != 1:
                raise HardwareError("Short I2C register write")
            result = os.read(self.fd, count)
            if len(result) != count:
                raise HardwareError("Short I2C register read")
            return result

    def write(self, address, register, data):
        if not 0x03 <= address <= 0x77 or not 0 <= register <= 255 or not isinstance(data, bytes):
            raise ValueError("Invalid I2C transaction")
        payload = bytes([register]) + data
        with self.lock:
            fcntl.ioctl(self.fd, I2C_SLAVE, address)
            if os.write(self.fd, payload) != len(payload):
                raise HardwareError("Short I2C write")

    def close(self):
        os.close(self.fd)


I2CTransport = _I2CTransport


class LinuxHardware(SimHardware):
    physical = True

    def __init__(self, i2c_path, mapdata):
        super().__init__(mapdata)
        self.i2c_path = i2c_path
        self._transport = None
        self._bank_verified = False

    def _image(self, values):
        image = {address: bytearray(2) for address in ADDRESSES}
        for net, high in values.items():
            pin = self.mapping["outputs"][net]
            if high:
                image[pin["address"]][pin["port"]] |= 1 << pin["bit"]
        return image

    def initialize_safe(self):
        if self.closed:
            raise HardwareError("A new physical RESET is required")
        if not self.mapping.get("hardware_accepted") or not self.mapping.get("reset_confirmed"):
            raise HardwareError("Physical acceptance and a real MCP RESET are required")
        self.mapping["reset_confirmed"] = False
        # reset_confirmed is a one-use assertion from the Pico supervisor.
        # A later explicit reset may recover a latched adapter fault; ordinary
        # output calls and telemetry never clear that latch.
        try:
            if self._transport is not None:
                self._transport.close()
                self._transport = None
            self.initialized = self._bank_verified = False
            self._transport = _I2CTransport(self.i2c_path)
            safe_image = self._image(_safe(self.mapping))
            input_masks = {address: bytearray(2) for address in ADDRESSES}
            for pin in self.mapping["inputs"].values():
                input_masks[pin["address"]][pin["port"]] |= 1 << pin["bit"]
            for address in ADDRESSES:
                if (self._transport.read(address, IODIR, 2) != b"\xff\xff" or
                        self._transport.read(address, IOCON, 2) != b"\x00\x00" or
                        self._transport.read(address, OLAT, 2) != b"\x00\x00"):
                    raise HardwareError("MCP does not have its BANK0 reset register image")
            self._bank_verified = True
            for address in ADDRESSES:
                self._transport.write(address, GPINTEN, b"\x00\x00")
                self._transport.write(address, OLAT, bytes(safe_image[address]))
                self._transport.write(address, IODIR, bytes(input_masks[address]))
                self._transport.write(address, IOCON, b"\x44")  # MIRROR | ODR, BANK=0
                self._transport.write(address, GPPU, b"\x00\x00")  # external pulls only
                self._transport.write(address, GPINTEN, bytes(input_masks[address]))
                for register, expected in ((OLAT, bytes(safe_image[address])),
                                           (IODIR, bytes(input_masks[address])),
                                           (IOCON, b"\x44\x44"), (GPPU, b"\x00\x00"),
                                           (GPINTEN, bytes(input_masks[address]))):
                    if self._transport.read(address, register, len(expected)) != expected:
                        raise HardwareError("MCP configuration readback mismatch")
            self.outputs = _safe(self.mapping)
            self.initialized = True
            self.faulted = False
            self.trace.append({"event": "initialize_safe", "outputs": dict(self.outputs)})
        except Exception as error:
            self._fail(error)

    def _fail(self, error):
        self.faulted = True
        self.trace.append({"event": "i2c_fault", "error": str(error)})
        try:
            self.all_off()
        except Exception:
            # No software can guarantee a write on a broken bus; Pico RESET
            # is the independent action required by the supervisor.
            pass
        raise HardwareError(str(error)) from error

    def read_inputs(self):
        self._ready()
        try:
            # INTCAP preserves a short fault that disappeared before polling.
            # Only an asserted bit in INTF qualifies that captured input.
            flags = {address: self._transport.read(address, 0x0E, 2) for address in ADDRESSES}
            captured = {address: self._transport.read(address, 0x10, 2) for address in ADDRESSES}
            registers = {address: self._transport.read(address, GPIO, 2) for address in ADDRESSES}
            result = {}
            for net, pin in self.mapping["inputs"].items():
                address, port, bit = pin["address"], pin["port"], 1 << pin["bit"]
                high = bool(registers[address][port] & bit)
                if net.startswith(("FAULT_", "FLT_")) and flags[address][port] & bit:
                    high = high and bool(captured[address][port] & bit)
                result[net] = high
            return result
        except Exception as error:
            self._fail(error)

    def apply_outputs(self, values):
        self._ready()
        self._validate_outputs(values)
        target = dict(self.outputs, **values)
        try:
            for address, image in self._image(target).items():
                self._transport.write(address, OLAT, bytes(image))
                if self._transport.read(address, OLAT, 2) != bytes(image):
                    raise HardwareError("MCP output readback mismatch")
            self.outputs = target
            self.trace.append({"event": "outputs", "outputs": dict(self.outputs)})
        except Exception as error:
            self._fail(error)

    def all_off(self):
        errors = []
        if self._transport is not None and self._bank_verified:
            for address, image in self._image(_safe(self.mapping)).items():
                try:
                    self._transport.write(address, OLAT, bytes(image))
                    if self._transport.read(address, OLAT, 2) != bytes(image):
                        raise HardwareError("Safe-output readback mismatch")
                except Exception as error:
                    errors.append(error)
        super().all_off()
        if errors:
            self.faulted = True
            self.trace.append({"event": "all_off_unconfirmed", "error": str(errors[0])})
            raise HardwareError("Safe outputs not confirmed; request Pico MCP RESET")

    def read(self, address, register, count):
        self._ready()
        try:
            return self._transport.read(address, register, count)
        except Exception as error:
            self._fail(error)

    def write(self, address, register, data):
        self._ready()
        if address in ADDRESSES:
            raise HardwareError("MCP writes must pass apply_outputs")
        try:
            self._transport.write(address, register, data)
        except Exception as error:
            self._fail(error)

    def close(self):
        try:
            self.all_off()
        finally:
            if self._transport is not None:
                self._transport.close()
                self._transport = None
            self.closed = True
