#!/usr/bin/env python3
"""Run actual production I2C drivers against independent register emulators.

Only the transport constructor is replaced, within an isolated component
fixture. The real LinuxHardware acceptance/reset guard remains unchanged.
Synthetic fixture permission assertions are never written to acceptance files.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys
import threading
from unittest.mock import patch

try:
    from .power_bus import EmulatedPowerBus, SOURCES
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from power_bus import EmulatedPowerBus, SOURCES


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def near(actual, expected, tolerance, message):
    check(abs(actual - expected) <= tolerance, f"{message}: {actual} versus {expected}")


class ProductionRegisterTransport:
    """Execute real stdlib transport read/write with a synthetic fd boundary.

    No open/ioctl reaches the OS. The production address validation, register
    pointer transaction and exact byte-count checks execute unchanged.
    """
    def __init__(self, transport_class, bus, adapter):
        self.transport_class = transport_class
        self.endpoint = bus.endpoint(adapter)
        self.real = object.__new__(transport_class)
        self.real.fd, self.real.lock = 123456789, threading.RLock()
        self.address = self.pointer = None

    def ioctl(self, fd, operation, address):
        check(fd == self.real.fd and operation == 0x0703, "unexpected emulated I2C_SLAVE ioctl")
        self.address = address
        return 0

    def os_write(self, fd, data):
        check(fd == self.real.fd and self.address is not None and data, "invalid emulated write syscall")
        self.pointer = data[0]
        if len(data) > 1:
            if self.address in self.endpoint.bus.short_writes:
                return len(data)-1
            self.endpoint.write(self.address, self.pointer, data[1:])
        return len(data)

    def os_read(self, fd, count):
        check(fd == self.real.fd and self.pointer is not None, "read before register-pointer write")
        return self.endpoint.read(self.address, self.pointer, count)

    def invoke(self, method, *args):
        import srrx.hardware as driver
        with patch.object(driver.fcntl, "ioctl", side_effect=self.ioctl), \
                patch.object(driver.os, "write", side_effect=self.os_write), \
                patch.object(driver.os, "read", side_effect=self.os_read):
            return method(self.real, *args)

    def read(self, address, register, count):
        return self.invoke(self.transport_class.read, address, register, count)

    def write(self, address, register, data):
        return self.invoke(self.transport_class.write, address, register, data)

    def close(self):
        self.endpoint.close()


@contextmanager
def fixture(project, *, initialize=True, prepare=None):
    import srrx.hardware as driver
    from srrx.runtime_telemetry import ProjectTelemetry
    from srrx.telemetry import SRRXTelemetry
    bus = EmulatedPowerBus(project)
    if prepare:
        prepare(bus)
    mapping = driver.load_mapping(Path(project) / "design/E3.json")
    # These assertions exist only in this private component test object. They
    # represent the upstream contract; they are not measured commissioning.
    mapping.update(hardware_accepted=True, reset_confirmed=True)
    hardware = driver.LinuxHardware("EMULATED_ONLY:i2c2", mapping)
    transport_class = driver._I2CTransport
    def factory(path):
        check(path == "EMULATED_ONLY:i2c2", "fixture must never open a real adapter")
        return ProductionRegisterTransport(transport_class, bus, "i2c2")
    with patch.object(driver, "_I2CTransport", side_effect=factory):
        # Production I2C0 (INA228) / I2C2 router; a misroute NACKs on the emulated adapter.
        bridge = ProjectTelemetry("EMULATED_ONLY:i2c0", hardware, None, clock=bus.clock_ms)
        bridge.bus0 = ProductionRegisterTransport(transport_class, bus, "i2c0")
        reader = SRRXTelemetry(bridge, clock_ms=bus.clock_ms)
        try:
            if initialize:
                hardware.initialize_safe()
            yield hardware, bus, reader
        finally:
            try:
                hardware.close()
            except driver.HardwareError:
                # An injected bus fault can prevent safe write confirmation.
                # The corresponding scenario separately checks actual latches.
                pass


def nominal_branches(bus):
    for branch, current, volts in (("BATTERY", 2., 14.8), ("LNA1", .100, 4.3), ("LNA2", .080, 4.3),
                                    ("LNA3", .060, 4.3), ("LNA4", .040, 4.3), ("LNB", .200, 13.2), ("BONI", .050, 13.8)):
        bus.set_branch(branch, current, volts)


def run(project):
    project = Path(project).resolve()
    software = str(project / "software")
    if software not in sys.path:
        sys.path.insert(0, software)
    import srrx.hardware as driver
    from srrx.telemetry import TelemetryError
    from srrx.policy import SafetyPolicy, CAPS
    cases = []
    def case(name, module_ids, operation):
        try:
            evidence = operation()
            cases.append({"id": name, "module_ids": module_ids, "status": "EMULATION_PASS", "evidence": evidence})
        except Exception as error:
            cases.append({"id": name, "module_ids": module_ids, "status": "EMULATION_FAIL",
                          "error": type(error).__name__ + ": " + str(error)})
    all_ids = ["E1/U102", "E2/U215", "E2/U216", "E3/U301", "E3/U302", "E3/U303"]
    mcp_ids = all_ids[3:]
    adc_ids = all_ids[:3]

    def acceptance_guard():
        hw = driver.LinuxHardware("MUST_NOT_OPEN", driver.load_mapping(project / "design/E3.json"))
        with patch.object(driver, "_I2CTransport") as factory:
            try:
                hw.initialize_safe()
            except driver.HardwareError:
                pass
            else:
                raise AssertionError("unaccepted physical adapter started")
            check(factory.call_count == 0, "guard must run before transport construction")
        return {"production_guard_intact": True, "transport_open_count": 0, "acceptance_record_created": False}
    case("physical_acceptance_guard_not_bypassed", mcp_ids, acceptance_guard)

    def safe_initialization():
        with fixture(project) as (hw, bus, reader):
            check(hw.physical is True and type(hw) is driver.LinuxHardware, "must exercise actual LinuxHardware")
            expected_safe = {0x20: b"\0\0", 0x22: b"\0\0", 0x23: b"\0\x10"}
            coverage = []
            # MCP writes only: 0x0A/0x04 are INA3221/INA228 registers too.
            writes = [entry for entry in bus.trace if entry["op"] == "write" and entry["address"] in bus.mcp]
            iocon = [i for i, e in enumerate(writes) if e["register"] == 0x0A]
            enabled = [i for i, e in enumerate(writes) if e["register"] == 0x04 and int(e["data"], 16)]
            check(len(iocon) == 3 and enabled and max(iocon) < min(enabled), "MCP_INT enabled before every chip is open-drain")
            for address, device in bus.mcp.items():
                own = [e["register"] for e in writes if e["address"] == address]
                check(own[:9] == [0x04, 0x0A, 0x02, 0x06, 0x08, 0x14, 0x00, 0x0C, 0x04],
                      "golden register order must disable interrupts, set open-drain IOCON, clear IPOL, set DEFVAL/INTCON, "
                      "preload OLAT, set directions/pulls, then enable interrupts")
                faults = [0, 0]
                for name, p in bus.net_map.items():
                    if p["address"] == address and p["direction"] == "input" and name.startswith(("FAULT_", "FLT_")):
                        faults[p["port"]] |= 1 << p["bit"]
                check(device.reg["GPINTEN"] == device.reg["DEFVAL"] == device.reg["INTCON"] == faults
                      and device.reg["IPOL"] == [0, 0], "only active-low FAULT_/FLT_ inputs may interrupt, against DEFVAL=1")
                check(bytes(device.reg["OLAT"]) == expected_safe[address], "literal safe OLAT image differs")
                check(device.iocon == 0x44 and device.reg["GPPU"] == [0, 0], "MIRROR/ODR or external-pull configuration differs")
                for port in (0, 1):
                    check(not device.reg["IODIR"][port] & 0x80, "GPA7/GPB7 must be configured output")
                    check(not device.reg["GPINTEN"][port] & 0x80, "output-only bit7 cannot generate input interrupts")
                    mapped = [name for name, p in bus.net_map.items() if p["address"] == address and p["port"] == port and p["bit"] == 7]
                    if not mapped:
                        check(not device.reg["OLAT"][port] & 0x80, "NC GPIO7 must stay low")
                    coverage.append({"module_id": bus.modules[address], "port": "AB"[port], "bit": 7,
                                     "direction": "output", "net": mapped[0] if mapped else None})
            check(hw.mapping["reset_confirmed"] is False, "reset assertion must be consumed once")
            try:
                hw.initialize_safe()
            except driver.HardwareError:
                pass
            else:
                raise AssertionError("one reset assertion was reused")
            return {"driver": "srrx.hardware.LinuxHardware", "register_write_order": [4, 10, 2, 6, 8, 20, 0, 12, 4],
                    "open_drain_on_all_chips_before_interrupt_enable": True,
                    "interrupt_sources": "FAULT_/FLT_ inputs only, compared against DEFVAL=1",
                    "safe_olat_hex": {hex(a): v.hex() for a, v in expected_safe.items()}, "all_six_gpio7": coverage,
                    "one_use_reset_assertion": True}
    case("mcp_connect_reset_safe_write_order", mcp_ids, safe_initialization)

    def every_output():
        with fixture(project) as (hw, bus, reader):
            tested = []
            outputs = {net: p for net, p in bus.net_map.items() if p["direction"] == "output"}
            safe = {net: net == "CHG_INHIBIT" for net in outputs}
            for net, physical in sorted(outputs.items()):
                for high in (False, True, False):
                    hw.apply_outputs({net: high})
                    # Every other output must keep its safe level: no extra rail may energize.
                    for other, level in dict(safe, **{net: high}).items():
                        check(bus.output_latched(other) is level and bus.pin_level(other) is level,
                              "actual emulated OLAT/GPIO differs for %s while driving %s" % (other, net))
                hw.all_off()
                tested.append({"net": net, **physical})
            check(len(tested) == len(hw.mapping["outputs"]), "not every mapped production output was covered")
            try:
                hw.write(0x20, 0x14, b"\xff\xff")
            except driver.HardwareError:
                pass
            else:
                raise AssertionError("raw MCP writes bypassed output owner")
            return {"output_count": len(tested), "outputs": tested, "register_and_pin_readback": True,
                    "all_other_outputs_checked_at_safe_level": True,
                    "raw_mcp_write_rejected": True, "scope": "component pin exercise; no live load or policy permission implied"}
    case("all_mapped_outputs_register_pin_roundtrip", mcp_ids, every_output)

    def every_input():
        with fixture(project) as (hw, bus, reader):
            tested = []
            for net, physical in sorted(bus.net_map.items()):
                if physical["direction"] != "input":
                    continue
                for high in (False, True):
                    bus.set_input(net, high)
                    hw.read_inputs()  # Consume the preceding captured transition.
                    check(hw.read_inputs()[net] is high, "present input level differs: " + net)
                tested.append({"net": net, **physical})
            check(len(tested) == len(hw.mapping["inputs"]), "not every mapped production input was covered")
            return {"input_count": len(tested), "inputs": tested, "actual_gpio_reads": True}
    case("all_mapped_inputs_register_roundtrip", mcp_ids, every_input)

    def interrupt_capture():
        with fixture(project) as (hw, bus, reader):
            nets = sorted(n for n, p in bus.net_map.items() if p["direction"] == "input" and n.startswith(("FAULT_", "FLT_")))
            check({bus.net_map[n]["address"] for n in nets} == {0x22, 0x23}, "fault inputs moved off U302/U303")
            for net in nets:
                hw.read_inputs(); hw.read_inputs()
                bus.set_input(net, False)
                bus.set_input(net, True)
                captured = hw.read_inputs()[net]
                current = hw.read_inputs()[net]
                check(captured is False and current is True,
                      "first low INTCAP must survive a recovered GPIO; stale INTCAP without INTF must be ignored: " + net)
            return {"short_fault_captured": True, "stale_capture_without_flag_ignored": True,
                    "intcap_read_clears_flag": True, "nets": nets}
    case("mcp_short_fault_and_stale_intcap", ["E3/U302", "E3/U303"], interrupt_capture)

    for address, module in ((0x20, "E3/U301"), (0x22, "E3/U302"), (0x23, "E3/U303")):
        def bank(address=address):
            def prepare(bus): bus.mcp[address].iocon = 0x80
            with fixture(project, initialize=False, prepare=prepare) as (hw, bus, reader):
                try:
                    hw.initialize_safe()
                except driver.HardwareError:
                    pass
                else:
                    raise AssertionError("BANK1 was treated as BANK0")
                check(not any(e["op"] == "write" for e in bus.trace), "unknown BANK caused speculative writes")
                return {"bank1_rejected_before_any_write": True, "fault_latched": hw.faulted}
        case("bank_mismatch_" + hex(address), [module], bank)

        def mcp_fault(address=address):
            with fixture(project) as (hw, bus, reader):
                net = next(name for name, p in bus.net_map.items() if p["address"] == address and p["direction"] == "output" and name != "CHG_INHIBIT")
                hw.apply_outputs({net: True})
                check(bus.output_latched(net), "fixture output did not energize")
                bus.nack.add(address)
                try:
                    hw.read_inputs()
                except driver.HardwareError:
                    pass
                else:
                    raise AssertionError("unplugged MCP read succeeded")
                check(hw.faulted and bus.output_latched(net), "a broken bus cannot guarantee clearing actual output latches")
                check(any(e["event"] == "all_off_unconfirmed" for e in hw.trace), "unconfirmed safe-write boundary not recorded")
                bus.nack.clear()
                bus.reset()
                check(not bus.output_latched(net), "external MCP reset must clear actual latch")
                hw.mapping["reset_confirmed"] = True
                hw.initialize_safe()
                check(hw.initialized and not hw.faulted, "explicit reset did not recover driver")
                return {"unplug_nack_latched": True, "previous_output_persists_until_external_reset": net,
                        "cached_safe_state_is_not_pin_confirmation": True, "external_reset_then_explicit_reinitialize": True,
                        "charger_reset_boundary": "CHG_INHIBIT high impedance during MCP reset does not inhibit hardware charging"}
        case("unplug_nack_requires_external_reset_" + hex(address), [module], mcp_fault)

        def short_mcp(address=address):
            with fixture(project) as (hw, bus, reader):
                bus.short_reads.add(address)
                try:
                    hw.read_inputs()
                except driver.HardwareError:
                    pass
                else:
                    raise AssertionError("short MCP register read was accepted")
                check(hw.faulted, "short register read must latch driver fault")
                return {"short_read_rejected": True, "fault_latched": True}
        case("short_mcp_read_" + hex(address), [module], short_mcp)

        def failed_write(address=address):
            with fixture(project) as (hw, bus, reader):
                bus.short_writes.add(address)
                try:
                    hw.apply_outputs({"EN_LNA1": True})
                except driver.HardwareError as exc:
                    check("Short I2C write" in str(exc), "real transport did not reject incomplete syscall write")
                else:
                    raise AssertionError("short I2C write was accepted")
                check(hw.faulted, "write failure must latch driver")
                return {"actual_i2c_transport_short_write_rejected": True, "fault_latched": True,
                        "safe_write_confirmation_available": False}
        case("short_mcp_write_" + hex(address), [module], failed_write)

        def bad_readback(address=address):
            def prepare(bus): bus.drop_writes.add((address, 0x00))
            with fixture(project, initialize=False, prepare=prepare) as (hw, bus, reader):
                try:
                    hw.initialize_safe()
                except driver.HardwareError as exc:
                    check("readback mismatch" in str(exc), "a different fault masked the bad IODIR write")
                else:
                    raise AssertionError("ACKed but ignored direction write was accepted")
                check(hw.faulted and not hw.initialized, "readback mismatch must block initialization")
                return {"acked_but_ignored_iodir_write_detected": True, "initialization_blocked": True}
        case("mcp_configuration_readback_" + hex(address), [module], bad_readback)

    def monitor_positive():
        with fixture(project) as (hw, bus, reader):
            nominal_branches(bus)
            reader.configure()
            check(bus.ina228[0x40].reg[1] == 0xFB69 and bus.ina228[0x40].reg[2] == 3932, "INA228 nominal scale/config write differs")
            check(all(d.reg[0] == 0x7327 for d in bus.ina3221.values()), "INA3221 channel/averaging config differs")
            near(bus.ina228[0x40].cycle_ms(), 12.624, 1e-9, "independent INA228 cycle calculation")
            near(bus.ina3221[0x41].cycle_ms(), 26.4, 1e-9, "independent INA3221 cycle calculation")
            check(not reader.poll().valid, "configuration must not expose a pre-configuration conversion")
            bus.advance(50)
            sample = reader.poll()
            check(sample.valid and sample.is_fresh(250, bus.now_ms) and sample.calibration_valid is False, "nominal sample must be fresh but uncalibrated")
            near(sample.values["battery_current_a"], 2., 30e-6, "positive battery current")
            near(sample.values["battery_v"], 14.77, .0003, "Adafruit SJ1 V_N = VBUS - signed shunt")
            near(sample.values["lnb_current_a"], .200, .0004, "actual LNB 0.1 ohm shunt")
            near(sample.values["boni_current_a"], .050, .0002, "actual Boni 0.2 ohm shunt")
            near(sample.values["lna_current_a"], .280, .0008, "all four antenna channels")
            # Distinct per-branch stimuli: a swapped LNA channel label cannot hide in the sum.
            for branch, expected in (("lna1", .100), ("lna2", .080), ("lna3", .060), ("lna4", .040)):
                near(sample.values[branch + "_current_a"], expected, .0004, "per-channel " + branch)
            check(not reader.poll().valid, "reading without a new conversion must not relabel old data fresh")
            return {"driver": "srrx.telemetry.SRRXTelemetry via LinuxHardware for I2C2", "calibration_valid": False,
                    "nominal_shunts_ohm": {"BATTERY": .015, "LNA1": .2, "LNA2": .2, "LNA3": .2, "LNA4": .2, "LNB": .1, "BONI": .2},
                    "values_si": dict(sample.values), "independent_cycle_ms": {"INA228": 12.624, "INA3221": 26.4},
                    "no_new_conversion_rejected": True, "adapters": {"INA228": "i2c0", "INA3221": "i2c2"},
                    "adapter_router": "srrx.runtime_telemetry.ProjectTelemetry.read/write", "per_channel_lna_currents": True}
    case("monitor_connect_id_config_conversion_decode", adc_ids, monitor_positive)

    def negative_current():
        # Distinct per-channel current and bus voltage, so a channel permutation fails.
        stimuli = {"LNA1": (-.10, 4.5), "LNA2": (-.08, 4.4), "LNA3": (-.06, 4.3), "LNA4": (-.04, 4.2),
                   "LNB": (-.12, 13.2), "BONI": (-.03, 13.8)}
        with fixture(project) as (hw, bus, reader):
            nominal_branches(bus)
            bus.set_branch("BATTERY", -2., 14.8)
            for branch, (current, volts) in stimuli.items():
                bus.set_branch(branch, current, volts)
            reader.configure(); bus.advance(50)
            sample = reader.poll()
            check(sample.valid and sample.calibration_valid is False, "signed fixture must decode without granting calibration")
            near(sample.values["battery_current_a"], -2., 30e-6, "negative charging current")
            near(sample.values["battery_v"], 14.83, .0003, "charging V_N must exceed VBUS")
            for branch, (current, volts) in stimuli.items():
                near(sample.values[branch.lower() + "_current_a"], current, .0004, "13-bit signed " + branch)
                near(sample.values[branch.lower() + "_bus_v"], volts, .008, "per-channel bus voltage " + branch)
            return {"signed_charge_current_a": sample.values["battery_current_a"], "battery_v": sample.values["battery_v"],
                    "all_six_signed_branch_channels": True, "distinct_per_channel_stimuli": True, "calibration_valid": False}
    case("signed_charge_and_six_branch_channels", adc_ids, negative_current)

    for diagnostic in ("memory_checksum", "math_overflow", "alert_config", "current_shunt_disagreement"):
        def diag(diagnostic=diagnostic):
            with fixture(project) as (hw, bus, reader):
                nominal_branches(bus); reader.configure(); bus.advance(50)
                device = bus.ina228[0x40]
                if diagnostic == "memory_checksum": device.reg[0x0B] &= ~1
                elif diagnostic == "math_overflow": device.reg[0x0B] |= 0x200
                elif diagnostic == "alert_config": device.reg[0x0B] &= ~0x8000
                else: device.reg[7] *= 2
                sample = reader.poll()
                check(not sample.valid and not sample.values and sample.calibration_valid is False,
                      "invalid INA228 diagnostic/data must invalidate aggregate")
                return {"injection": diagnostic, "aggregate_invalid": True, "error": sample.error}
        case("ina228_" + diagnostic, ["E1/U102"], diag)

    for address, module, identity in ((0x40, "E1/U102", 0x3F), (0x41, "E2/U215", 0xFF), (0x43, "E2/U216", 0xFF)):
        def corrupt_id(address=address, identity=identity):
            with fixture(project) as (hw, bus, reader):
                bus.devices[address].reg[identity] ^= 0x100
                try:
                    reader.configure()
                except TelemetryError as exc:
                    check("identity mismatch" in str(exc), "identity failure was masked by a different error")
                else:
                    raise AssertionError("corrupt chip identity accepted")
                return {"corrupt_identity_rejected": True, "register": hex(identity)}
        case("corrupt_monitor_id_" + hex(address), [module], corrupt_id)

        for injection in ("unplug_nack", "short_read", "stale_conversion", "unexpected_reset", "reserved_bits"):
            def faulted_monitor(address=address, injection=injection):
                with fixture(project) as (hw, bus, reader):
                    nominal_branches(bus); reader.configure(); bus.advance(50)
                    old = reader.poll()
                    check(old.valid, "baseline nominal conversion failed")
                    device = bus.devices[address]
                    if injection == "unplug_nack": bus.nack.add(address)
                    elif injection == "short_read": bus.short_reads.add(address)
                    elif injection == "stale_conversion": device.freeze = True
                    elif injection == "unexpected_reset": device.reset(bus.now_ms)
                    bus.advance(1000)
                    if injection == "reserved_bits":
                        device.reg[4 if address == 0x40 else 1] |= 1
                    current = reader.poll()
                    check(not current.valid and not current.values and current.calibration_valid is False,
                          "sensor failure must invalidate complete aggregate, without last-good replacement")
                    check(not old.is_fresh(250, bus.now_ms), "old samples must become stale on the independent clock")
                    return {"injection": injection, "aggregate_invalid": True, "no_last_good_retimestamp": True,
                            "calibration_valid": False, "error": current.error}
            case(injection + "_monitor_" + hex(address), [module], faulted_monitor)

    def overcurrent_uncalibrated():
        with fixture(project) as (hw, bus, reader):
            nominal_branches(bus); bus.set_branch("LNA1", .300, 4.3)
            reader.configure(); bus.advance(50)
            sample = reader.poll()
            check(sample.valid and sample.calibration_valid is False, "nominal measurement must not claim bench calibration")
            current = sample.values["lna1_current_a"]
            check(current > CAPS["LNA1"][0], "overcurrent stimulus did not exceed operating cap")
            policy = SafetyPolicy(hw)
            policy.refresh_inputs(hw.read_inputs(), int(bus.now_ms))
            policy.refresh_telemetry({"LNA1": {"current_a": current, "voltage_v": sample.values["lna1_bus_v"],
                "timestamp_ms": sample.timestamp_ms, "valid": True, "calibration_valid": False}}, int(bus.now_ms))
            check("LNA1" not in policy.telemetry and policy.armed is False, "uncalibrated emulation cannot authorize a branch")
            check(policy.command("arm", True, int(bus.now_ms))["ok"] is False, "absent real supervisor/commissioning must block ARM")
            return {"decoded_current_a": current, "graph_operating_cap_a": CAPS["LNA1"][0], "calibration_valid": False,
                    "uncalibrated_data_rejected_by_real_policy": True, "arm_blocked": True,
                    "scope": "decoding plus calibration gate; no fabricated accepted calibration or physical current trip"}
    case("overcurrent_decode_cannot_bypass_calibration", ["E2/U215"], overcurrent_uncalibrated)

    def adapter_split():
        bus = EmulatedPowerBus(project)
        for adapter, address in (("i2c0", 0x41), ("i2c2", 0x40)):
            try:
                bus.endpoint(adapter).read(address, 0, 2)
            except OSError:
                pass
            else:
                raise AssertionError("wrong physical adapter unexpectedly ACKed")
        return {"separate_adapter_address_spaces": True, "unknown_third_ina3221_created": False,
                "scope": "emulator self-test; production routing is exercised by the monitor cases"}
    case("emulator_adapter_address_separation_self_test", [], adapter_split)

    def connected_reset(fallback):
        from srrx.engine import Engine
        from srrx.link import SimLink
        with fixture(project) as (hw, bus, reader):
            class CoupledLink:
                def __init__(self):
                    self.actual = SimLink(project)
                    self.last_reset = None
                    self.sent = []
                def couple(self):
                    asserted = self.actual.model.outputs["mcp_reset"]
                    if asserted is not self.last_reset:
                        bus.hold_mcp_reset(asserted)
                        self.last_reset = asserted
                def send(self, frame, now_ms=None):
                    self.sent.append(frame["t"])
                    self.actual.send(frame, now_ms)
                    self.couple()
                def poll(self, now_ms):
                    frames = self.actual.poll(now_ms)
                    self.couple()
                    return frames
                def close(self):
                    self.actual.close()

            link = CoupledLink()
            class ModelOnlyFacade:
                # Physical silicon is absent: synthetic Engine measurements must
                # stay in its explicit simulation path. The delegated adapter
                # object remains an unchanged LinuxHardware(physical=True).
                physical, model_only = False, True
                def __getattr__(self, name):
                    return getattr(hw, name)
                @property
                def inputs(self):
                    return {name: bus.pin_level(name) for name, p in bus.net_map.items() if p["direction"] == "input"}
                def set_inputs(self, values):
                    for name, level in values.items():
                        bus.set_input(name, level)
                def initialize_safe(self):
                    check(link.actual.model.outputs["mcp_reset"] is False, "fixture cannot program a held-reset MCP")
                    hw.mapping.update(hardware_accepted=True, reset_confirmed=True)
                    return hw.initialize_safe()

            facade = ModelOnlyFacade()
            engine = Engine(facade, link, simulated=True)
            link.couple()
            now = 0
            def advance(target):
                nonlocal now
                while now < target:
                    increment = min(20, target-now)
                    now += increment
                    bus.advance(increment)
                    engine.tick(now)
            try:
                engine.tick(0)
                check(engine.request({"op": "arm", "_owner": "module-lab-emulation"})["ok"], "connected fixture ARM refused")
                advance(1000)
                check(engine.policy.armed and link.actual.model.state == "ACTIVE", "real Engine/Supervisor handshake did not arm")
                check(engine.request({"op": "control", "name": "EN_LNA1", "value": True,
                                      "_owner": "module-lab-emulation"})["ok"], "connected virtual enable refused")
                check(bus.output_latched("EN_LNA1") and bus.pin_level("EN_LNA1"), "real driver did not energize modeled pin")
                baseline = now
                bus.nack.add(0x20)
                if fallback:
                    link.actual.drop_link = True
                    advance(baseline+600)
                    check(not engine.policy.armed and bus.output_latched("EN_LNA1"),
                          "host stale trip should not falsely confirm a write over NACKed bus")
                    check(link.actual.model.outputs["mcp_reset"] is False, "independent heartbeat fallback occurred earlier than expected")
                    advance(baseline+1000)
                    check(link.actual.model.fault == "HEARTBEAT_TIMEOUT", "independent Supervisor heartbeat timeout was not exercised")
                else:
                    advance(baseline+40)
                    check("TRIP" in link.sent, "Engine did not send actual TRIP wire message")
                    check(link.actual.model.fault == "HOST_TRIP", "actual wire decoder/Supervisor did not receive host TRIP")
                check(link.actual.model.outputs["mcp_reset"] is True and 0x20 in bus.held_reset,
                      "Supervisor reset output did not reach the MCP model")
                check(not bus.output_latched("EN_LNA1"), "independent MCP reset did not clear actual modeled OLAT")
                check(all(not bus.output_latched(name) for name, p in bus.net_map.items() if p["direction"] == "output"),
                      "reset did not clear all three MCP output latches")
                advance(now+1000)
                check(not engine.policy.armed, "connection restoration must never automatically rearm")
                check(engine.request({"op": "control", "name": "EN_LNA1", "value": True,
                                      "_owner": "module-lab-emulation"})["ok"] is False, "faulted connected graph enabled a branch")
                try:
                    bus.endpoint("i2c2").read(0x20, 0, 2)
                except OSError:
                    pass
                else:
                    raise AssertionError("bus fault/reset unexpectedly ACKed")
                status = engine.status()
                check(status["mode"] == "SIMULATION" and status["hardware_qualified"] is False and engine.acceptance is None,
                      "connected fixture must never claim hardware acceptance")
                return {"engine": "actual srrx.engine.Engine(simulated=True)", "component_driver": "actual LinuxHardware(physical=True)",
                        "transport": "actual I2CTransport.read/write over emulated syscall boundary",
                        "supervisor": "actual SimLink UART codecs and firmware/pico/Supervisor",
                        "model_only_facade": True, "synthetic_engine_telemetry_is_not_calibration": True,
                        "injection": "I2C NACK plus lost UART/HB" if fallback else "I2C NACK with intact UART",
                        "fallback": "HEARTBEAT_TIMEOUT" if fallback else "wire TRIP to HOST_TRIP", "all_olat_cleared_by_reset": True,
                        "bus_still_faulted": True, "automatic_rearm": False, "hardware_qualified": False,
                        "cached_safe_image_before_reset_not_sufficient": True, "final_pico_state": link.actual.model.state,
                        "close_safe_writes_unconfirmed_on_broken_bus": True,
                        "reset_events": [e for e in bus.trace if e["op"].startswith("mcp_reset")],
                        "charger_reset_boundary": "CHG_INHIBIT becomes high impedance; hardware charging may proceed during MCP reset"}
            finally:
                try:
                    engine.close()
                except driver.HardwareError:
                    # The already-proved independent RESET holds the modeled
                    # pins off. Teardown still cannot confirm I2C writes over
                    # the intentionally persistent bus fault.
                    pass
    case("connected_engine_uart_trip_clears_mcp_latches", mcp_ids, lambda: connected_reset(False))
    case("connected_lost_uart_independent_heartbeat_reset", mcp_ids, lambda: connected_reset(True))

    source_files = ("software/srrx/hardware.py", "software/srrx/telemetry.py", "software/srrx/policy.py",
                    "software/srrx/runtime_telemetry.py", "design/E1.json", "design/E2.json", "design/E3.json",
                    "deployment/module_lab/power_bus.py", "deployment/module_lab/power_scenarios.py")
    passed = sum(item["status"] == "EMULATION_PASS" for item in cases)
    return {"schema_version": 1, "status": "EMULATION_PASS" if passed == len(cases) else "EMULATION_FAIL",
            "scope": "independent register models with actual production LinuxHardware, I2CTransport read/write and telemetry methods",
            "hardware_qualified": False, "physical_tests_performed": False, "acceptance_records_created": False,
            "production_release_guards_changed": False, "fixture_permissions": "private mapping hardware_accepted/reset_confirmed assertions; never persisted",
            "summary": {"cases": len(cases), "passed": passed, "failed": len(cases)-passed, "modules": len(all_ids)},
            "modules": [{"module_id": module, "case_ids": [c["id"] for c in cases if module in c["module_ids"]]} for module in all_ids],
            "cases": cases, "primary_sources": SOURCES,
            "source_sha256": {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in source_files},
            "limits": ["No actual I2C electrical timing, kernel ioctl, power waveform, thermal, calibration, BMS or RF qualification is proved.",
                       "Functional model implements the register subset used by current drivers; alert limit comparator behavior, accumulators and silicon errata are outside this proof.",
                       "Broken I2C can leave emulated output latches energized until independent reset; cached all-off is not physical pin confirmation.",
                       "No third INA3221 exists in the graph; exactly two monitors cover six branch channels.",
                       "Nominal SHUNT_CAL arithmetic is device scaling only; all returned snapshots retain calibration_valid=false."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = run(args.project)
    encoded = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    else:
        print(encoded, end="")
    return 0 if report["status"] == "EMULATION_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
