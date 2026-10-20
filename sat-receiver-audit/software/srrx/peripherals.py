"""Host/bench wrapper for the portable Pico input driver, with graph checks.

Never open a Q6A I2C node for these devices: their 0x20 address is on Pico I2C0
and collides numerically with an unrelated Q6A MCP. Transport ownership is explicit.
"""
import importlib.util
import json
from pathlib import Path

KEYS = ("HOME", "BACK", "REC", "MARK", "FN", "LOCK", "ENC1_PRESS", "ENC2_PRESS")


def derive_wiring(project):
    graph = json.loads((Path(project) / "design/E3.json").read_text(encoding="utf-8"))
    parts = {part["ref"]: part for part in graph["components"]}
    pico, keys, light = parts["U305"], parts["U306"], parts["U308"]
    if "Pico SC0915" not in pico["value"] or "PI4IOE5V9555" not in keys["value"] or "VEML7700" not in light["value"]:
        raise ValueError("HMI devices differ from reviewed E3 hardware")
    pp = {pin["name"]: pin for pin in pico["pins"]}
    kp = {pin["name"]: pin for pin in keys["pins"]}
    lp = {pin["name"]: pin for pin in light["pins"]}
    expected_physical = {"INT_N": "1", "A1": "2", "A2": "3", "GND": "12",
                         "A0": "21", "SCL": "22", "SDA": "23", "VCC": "24"}
    expected_physical.update({"IO0_%d" % bit: str(4 + bit) for bit in range(8)})
    if any(str(kp[name]["number"]) != number for name, number in expected_physical.items()):
        raise ValueError("PI4IO physical pin mapping changed")
    if kp["VCC"].get("net") != "E3_PICO3V3" or kp["GND"].get("net") != "GND":
        raise ValueError("HMI supply domain changed")
    address = 0x20
    for bit in range(3):
        rail = kp["A%d" % bit].get("net")
        if rail not in ("GND", "E3_PICO3V3"):
            raise ValueError("HMI address strap is not physical")
        address |= int(rail == "E3_PICO3V3") << bit
    labels = tuple(kp["IO0_%d" % bit].get("net", "").removeprefix("E3_") for bit in range(8))
    if labels != KEYS or any(not kp["IO1_%d" % bit].get("nc") for bit in range(8)):
        raise ValueError("Key wiring/unused bank changed")

    def gpio_for_net(net):
        matches = [int(name[2:]) for name, pin in pp.items() if name.startswith("GP") and name[2:].isdigit() and pin.get("net") == net]
        if len(matches) != 1:
            raise ValueError("Net lacks a unique Pico GPIO: " + str(net))
        return matches[0]

    def series_connected(first, second, resistance):
        return first == second or any(part.get("kind") == "resistor" and part["value"] == resistance
               and {pin.get("net") for pin in part["pins"]} == {first, second}
               for part in graph["components"])

    sda, scl, interrupt = (gpio_for_net(kp[name]["net"]) for name in ("SDA", "SCL", "INT_N"))
    if not series_connected(kp["SDA"]["net"], lp["SDA"]["net"], "100") or not series_connected(kp["SCL"]["net"], lp["SCL"]["net"], "100"):
        raise ValueError("VEML bus series connection missing")
    if lp["VIN"].get("net") != "E3_PICO3V3" or lp["GND"].get("net") != "GND":
        raise ValueError("VEML supply domain changed")
    encoders = []
    for ref in ("ENC301", "ENC302"):
        ep = {pin["name"]: pin for pin in parts[ref]["pins"]}
        if ep["COMMON"].get("net") != "GND":
            raise ValueError("Encoder common is not GND")
        pair = []
        for channel in ("A", "B"):
            candidates = [name for name, pin in pp.items() if name.startswith("GP") and name[2:].isdigit()
                          and pin.get("net") and series_connected(ep[channel]["net"], pin["net"], "10k")]
            if len(candidates) != 1:
                raise ValueError("Encoder RC path lacks unique Pico GPIO")
            pair.append(int(candidates[0][2:]))
        encoders.append(tuple(pair))
    return {"domain": "pico_hmi_i2c0", "key_address": address, "light_address": 0x10,
            "sda_gpio": sda, "scl_gpio": scl, "interrupt_gpio": interrupt,
            "encoder_gpios": tuple(encoders), "keys": labels}


class PeripheralPoller:
    physical_qualified = False

    def __init__(self, transport, project):
        project = Path(project)
        wiring = derive_wiring(project)
        source = project / "firmware/pico/hmi.py"
        spec = importlib.util.spec_from_file_location("srrx_pico_hmi_core", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.wiring = wiring
        self.core = module.PeripheralPoller(transport, wiring)

    def poll(self, now_ms):
        return self.core.poll(now_ms)

    def snapshot(self, now_ms):
        return self.core.snapshot(now_ms)
