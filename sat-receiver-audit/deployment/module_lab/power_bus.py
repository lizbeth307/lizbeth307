"""Independent, deterministic register models of the graph's power I2C devices.

This is a functional digital model, not an electrical/thermal or silicon timing
simulation. advance() alone completes conversions; reads never fabricate a new
sample. No production constants or SimHardware state are used in this model.
"""
from __future__ import annotations

import errno
import json
import math
from pathlib import Path

SOURCES = {
    "MCP23017": {"url": "https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf",
                 "revision": "DS20001952D, 2022", "sections": "3.1, 3.2.1, Tables 3-1/3-3, 3.5.8-3.6.5"},
    "INA228": {"url": "https://www.ti.com/lit/ds/symlink/ina228.pdf", "revision": "SLYS021A, May 2022",
               "sections": "7.3.2, 7.6.1, Tables 7-5 through 7-16, 8.1.2"},
    "INA3221": {"url": "https://www.ti.com/lit/ds/symlink/ina3221.pdf", "revision": "SBOS576C, September 2026",
                "sections": "7.3.1, 8.1, 8.2; CVRF clear, signed 13-bit voltage registers"},
}


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("finite analog stimulus required")
    return value


def encode_signed(value, bits):
    value = round(value)
    return max(-(1 << (bits-1)), min((1 << (bits-1))-1, value)) & ((1 << bits)-1)


class MCP23017:
    FIELDS = ("IODIR", "IPOL", "GPINTEN", "DEFVAL", "INTCON", "IOCON", "GPPU", "INTF", "INTCAP", "GPIO", "OLAT")

    def __init__(self):
        self.external = [0, 0]
        self.reset()

    def reset(self):
        self.reg = {name: [0, 0] for name in self.FIELDS}
        self.reg["IODIR"] = [255, 255]
        self.iocon = 0
        self.previous = list(self.external)

    def _decode(self, pointer):
        if self.iocon & 0x80:
            port, offset = pointer >> 4, pointer & 15
            if port not in (0, 1) or offset > 10:
                return None, None
            return self.FIELDS[offset], port
        if not 0 <= pointer <= 21:
            return None, None
        return self.FIELDS[pointer // 2], pointer & 1

    def _next(self, pointer):
        if self.iocon & 0x20:
            return pointer if self.iocon & 0x80 else pointer ^ 1
        maximum = 0x1A if self.iocon & 0x80 else 0x15
        return 0 if pointer >= maximum else pointer + 1

    def gpio(self, port):
        direction = self.reg["IODIR"][port]
        inputs = (self.external[port] ^ self.reg["IPOL"][port]) & direction
        return inputs | (self.reg["OLAT"][port] & ~direction & 255)

    def set_pin(self, port, bit, high):
        if port not in (0, 1) or bit not in range(7) or type(high) is not bool:
            raise ValueError("MCP23017 revision D GPA7/GPB7 are output only")
        old = self.external[port]
        mask = 1 << bit
        self.external[port] = old | mask if high else old & ~mask
        direction, enabled = self.reg["IODIR"][port], self.reg["GPINTEN"][port]
        compare = self.reg["INTCON"][port]
        changed = ((self.external[port] ^ old) & ~compare
                   | (self.external[port] ^ self.reg["DEFVAL"][port]) & compare) & enabled & direction
        if changed:
            if not self.reg["INTF"][port]:
                self.reg["INTCAP"][port] = self.gpio(port)
            self.reg["INTF"][port] |= changed

    def read(self, pointer, count):
        out = bytearray()
        for _ in range(count):
            name, port = self._decode(pointer)
            value = (self.iocon if name == "IOCON" else self.gpio(port) if name == "GPIO"
                     else self.reg[name][port] if name else 0)
            out.append(value)
            if name in ("INTCAP", "GPIO"):
                self.reg["INTF"][port] = 0
                self.previous[port] = self.external[port]
            pointer = self._next(pointer)
        return bytes(out)

    def write(self, pointer, data):
        for value in data:
            name, port = self._decode(pointer)
            if name == "IOCON":
                self.iocon = value & 0xFE
            elif name in ("GPIO", "OLAT"):
                self.reg["OLAT"][port] = value
            elif name and name not in ("INTF", "INTCAP"):
                self.reg[name][port] = value
            pointer = self._next(pointer)


class INA228:
    WIDTHS = {**{r: 2 for r in range(0x12)}, 4: 3, 5: 3, 7: 3, 8: 3, 9: 5, 10: 5, 0x3E: 2, 0x3F: 2}
    TIMES_MS = (.050, .084, .150, .280, .540, 1.052, 2.074, 4.120)
    AVERAGES = (1, 4, 16, 64, 128, 256, 512, 1024)

    def __init__(self):
        self.vbus_v, self.current_a, self.shunt_ohms, self.temperature_c = 14.8, 0., .015, 25.
        self.freeze = False
        self.reset(1000.)

    def reset(self, now):
        self.reg = {r: 0 for r in self.WIDTHS}
        self.reg.update({0: 0x0000, 1: 0xFB68, 2: 0x1000, 0x0B: 0x0001,
                         0x0C: 0x7FFF, 0x0D: 0x8000, 0x0E: 0x7FFF, 0x10: 0x7FFF,
                         0x11: 0xFFFF, 0x3E: 0x5449, 0x3F: 0x2281})
        self.ready = False
        self.due = now + self.cycle_ms()

    def cycle_ms(self):
        adc = self.reg[1]
        selected = (adc >> 12) & 7
        times = (self.TIMES_MS[(adc >> 9) & 7], self.TIMES_MS[(adc >> 6) & 7], self.TIMES_MS[(adc >> 3) & 7])
        return sum(value for bit, value in enumerate(times) if selected & (1 << bit)) * self.AVERAGES[adc & 7]

    def advance(self, now):
        if self.freeze or self.reg[1] >> 12 < 9 or not self.cycle_ms() or now < self.due:
            return
        quantum = 78.125e-9 if self.reg[0] & 0x10 else 312.5e-9
        shunt_code = encode_signed(self.current_a * self.shunt_ohms / quantum, 20)
        signed = shunt_code - (1 << 20) if shunt_code & (1 << 19) else shunt_code
        current = round(signed * quantum * 13107.2e6 * (4 if self.reg[0] & 0x10 else 1) / self.reg[2]) if self.reg[2] else 0
        bus_code = encode_signed(self.vbus_v / 195.3125e-6, 20)
        self.reg[4], self.reg[5] = shunt_code << 4, bus_code << 4
        self.reg[6] = encode_signed(self.temperature_c / .0078125, 16)
        self.reg[7] = encode_signed(current, 20) << 4
        self.reg[8] = min(0xFFFFFF, round(abs(current) * max(0, self.vbus_v) / 3.2))
        self.ready = True
        self.due += (math.floor((now - self.due) / self.cycle_ms()) + 1) * self.cycle_ms()

    def read(self, pointer, count):
        if self.WIDTHS.get(pointer) != count:
            raise OSError(errno.EINVAL, "INA228 register width mismatch")
        value = self.reg[pointer]
        if pointer == 0x0B:
            value = (value & ~2) | (2 if self.ready else 0)
            self.ready = False
        return value.to_bytes(count, "big")

    def write(self, pointer, data, now):
        if pointer not in (0, 1, 2, 3, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11) or len(data) != 2:
            raise OSError(errno.EINVAL, "INA228 write outside implemented configuration registers")
        value = int.from_bytes(data, "big")
        if pointer == 0 and value & 0x8000:
            self.reset(now)
            return
        if pointer == 0x0B:
            self.reg[pointer] = (self.reg[pointer] & 0x0FFF) | (value & 0xF000)
        else:
            self.reg[pointer] = value
        if pointer == 1:
            self.ready = False
            self.due = now + self.cycle_ms() + ((self.reg[0] >> 6) & 255) * 2


class INA3221:
    TIMES_MS = (.140, .204, .332, .588, 1.100, 2.116, 4.156, 8.244)
    AVERAGES = (1, 4, 16, 64, 128, 256, 512, 1024)

    def __init__(self, shunts):
        self.shunts = tuple(shunts)
        self.currents, self.voltages = [0., 0., 0.], [4.5, 4.5, 4.5]
        self.freeze = False
        self.reset(1000.)

    def reset(self, now):
        self.reg = {r: 0 for r in range(0x12)}
        self.reg.update({0: 0x7127, **{r: 0x7FF8 for r in range(7, 13)}, 14: 0x7FFE, 15: 0x0002,
                         16: 0x2710, 17: 0x2328, 0xFE: 0x5449, 0xFF: 0x3220})
        self.ready = False
        self.due = now + self.cycle_ms()

    def cycle_ms(self):
        config = self.reg[0]
        mode = config & 7
        enabled = sum(bool(config & 1 << bit) for bit in (12, 13, 14))
        bus = self.TIMES_MS[(config >> 6) & 7] if mode & 2 else 0
        shunt = self.TIMES_MS[(config >> 3) & 7] if mode & 1 else 0
        return enabled * (bus + shunt) * self.AVERAGES[(config >> 9) & 7]

    def advance(self, now):
        if self.freeze or self.reg[0] & 7 < 5 or not self.cycle_ms() or now < self.due:
            return
        for channel in range(3):
            if self.reg[0] & (1 << (14 - channel)):
                self.reg[1 + channel * 2] = encode_signed(self.currents[channel] * self.shunts[channel] / 40e-6, 13) << 3
                self.reg[2 + channel * 2] = encode_signed(self.voltages[channel] / .008, 13) << 3
        self.ready = True
        self.due += (math.floor((now - self.due) / self.cycle_ms()) + 1) * self.cycle_ms()

    def read(self, pointer, count):
        if count != 2 or pointer not in self.reg:
            raise OSError(errno.EINVAL, "INA3221 register width/address mismatch")
        value = self.reg[pointer]
        if pointer == 15:
            value = (value & ~1) | int(self.ready)
            self.ready = False
        return value.to_bytes(2, "big")

    def write(self, pointer, data, now):
        if len(data) != 2 or pointer not in (0, *range(7, 13), 14, 15, 16, 17):
            raise OSError(errno.EINVAL, "INA3221 write outside configuration registers")
        value = int.from_bytes(data, "big")
        if pointer == 0 and value & 0x8000:
            self.reset(now)
            return
        self.reg[pointer] = value
        if pointer == 0:
            self.ready = False
            self.due = now + self.cycle_ms()


class Endpoint:
    """An emulated adapter handle; closing it does not unplug the ICs."""
    def __init__(self, bus, name):
        self.bus, self.name, self.closed = bus, name, False

    def _check(self, address):
        if self.closed:
            raise OSError(errno.EBADF, "emulated adapter closed")
        if (self.name == "i2c0" and address != 0x40) or (self.name == "i2c2" and address == 0x40):
            raise OSError(errno.ENXIO, "device is on the other emulated physical adapter")

    def read(self, address, register, count):
        self._check(address)
        return self.bus.read(address, register, count)

    def write(self, address, register, data):
        self._check(address)
        return self.bus.write(address, register, data)

    def close(self):
        self.closed = True


class EmulatedPowerBus:
    def __init__(self, project):
        self.project, self.now_ms = Path(project), 1000.
        self.mcp = {address: MCP23017() for address in (0x20, 0x22, 0x23)}
        self.ina228 = {0x40: INA228()}
        self.ina3221 = {0x41: INA3221((.2, .2, .2)), 0x43: INA3221((.2, .1, .2))}
        self.devices = {**self.mcp, **self.ina228, **self.ina3221}
        self.net_map, self.modules = {}, {}
        graph = json.loads((self.project / "design/E3.json").read_text(encoding="utf-8"))
        for component in graph["components"]:
            if component["ref"] not in {"U301", "U302", "U303"}:
                continue
            address = {"U301": 0x20, "U302": 0x22, "U303": 0x23}[component["ref"]]
            self.modules[address] = "E3/" + component["ref"]
            for pin in component["pins"]:
                try:
                    number = int(pin["number"])
                except ValueError:
                    continue
                if (21 <= number <= 28 or 1 <= number <= 8) and not pin.get("nc"):
                    port, bit = (0, number - 21) if number >= 21 else (1, number - 1)
                    self.net_map[pin["net"]] = {"address": address, "port": port, "bit": bit,
                                                 "direction": pin["type"], "module_id": self.modules[address], "pin": number}
        self.modules.update({0x40: "E1/U102", 0x41: "E2/U215", 0x43: "E2/U216"})
        self.nack, self.short_reads, self.short_writes, self.drop_writes = set(), set(), set(), set()
        self.held_reset = set()
        self.trace = []
        for name, pin in self.net_map.items():
            if pin["direction"] == "input":
                self.set_input(name, name.startswith(("FAULT_", "FLT_")) or name == "SLED_DET")

    def clock_ms(self):
        return self.now_ms

    def endpoint(self, name="i2c2"):
        if name not in ("i2c0", "i2c2"):
            raise ValueError("explicit emulated adapter required")
        return Endpoint(self, name)

    def advance(self, milliseconds):
        finite(milliseconds)
        if milliseconds < 0:
            raise ValueError("emulated time cannot reverse")
        self.now_ms += milliseconds
        for monitor in (*self.ina228.values(), *self.ina3221.values()):
            monitor.advance(self.now_ms)

    def reset(self):
        for device in self.mcp.values():
            device.reset()
        for monitor in (*self.ina228.values(), *self.ina3221.values()):
            monitor.reset(self.now_ms)
        self.trace.append({"op": "external_reset", "at_ms": self.now_ms})

    def hold_mcp_reset(self, asserted):
        if type(asserted) is not bool:
            raise ValueError("explicit reset level required")
        if asserted:
            for address, device in self.mcp.items():
                device.reset()
                self.held_reset.add(address)
        else:
            self.held_reset.difference_update(self.mcp)
        self.trace.append({"op": "mcp_reset_assert" if asserted else "mcp_reset_release", "at_ms": self.now_ms})

    def set_input(self, net, level):
        pin = self.net_map[net]
        if pin["direction"] != "input":
            raise ValueError("net is not a graph input")
        self.mcp[pin["address"]].set_pin(pin["port"], pin["bit"], level)

    def pin_level(self, net):
        pin = self.net_map[net]
        return bool(self.mcp[pin["address"]].gpio(pin["port"]) & (1 << pin["bit"]))

    def output_latched(self, net):
        pin = self.net_map[net]
        return bool(self.mcp[pin["address"]].reg["OLAT"][pin["port"]] & (1 << pin["bit"]))

    def set_branch(self, branch, current_a, bus_v):
        current_a, bus_v = finite(current_a), finite(bus_v)
        if branch == "BATTERY":
            self.ina228[0x40].current_a, self.ina228[0x40].vbus_v = current_a, bus_v
            return
        address, channel = {"LNA1": (0x41, 0), "LNA2": (0x41, 1), "LNA3": (0x41, 2),
                            "LNA4": (0x43, 0), "LNB": (0x43, 1), "BONI": (0x43, 2)}[branch]
        self.ina3221[address].currents[channel], self.ina3221[address].voltages[channel] = current_a, bus_v

    def _device(self, address):
        if address in self.held_reset:
            raise OSError(errno.ENXIO, "emulated MCP held in hardware RESET")
        if address in self.nack or address not in self.devices:
            raise OSError(errno.ENXIO, "emulated I2C unplug/NACK")
        return self.devices[address]

    def read(self, address, register, count):
        device = self._device(address)
        value = device.read(register, count)
        if address in self.short_reads:
            value = value[:-1]
        self.trace.append({"op": "read", "address": address, "register": register, "count": count,
                           "data": value.hex(), "at_ms": self.now_ms})
        return value

    def write(self, address, register, data):
        if not isinstance(data, bytes):
            raise ValueError("register data must be bytes")
        device = self._device(address)
        self.trace.append({"op": "write", "address": address, "register": register, "data": data.hex(), "at_ms": self.now_ms})
        if (address, register) in self.drop_writes:
            return
        if isinstance(device, MCP23017):
            device.write(register, data)
        else:
            device.write(register, data, self.now_ms)
