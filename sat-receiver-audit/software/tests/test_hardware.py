import copy
import json
import unittest
from unittest.mock import patch

from srrx.hardware import (ADDRESSES, DEFVAL, GPINTEN, GPIO, GPPU, INTCON, IOCON, IODIR, IPOL, OLAT,
                           TRACE_LIMIT, HardwareError, LinuxHardware, SimHardware, load_mapping)


class FakeBus:
    def __init__(self):
        self.registers = {address: bytearray(0x20) for address in ADDRESSES}
        for registers in self.registers.values():
            registers[0:2] = b"\xff\xff"
        self.writes = []
        self.reads = []
        self.fail_once = False
        self.closed = False

    def read(self, address, register, count):
        self.reads.append((address, register, count))
        return bytes(self.registers[address][register:register + count])

    def write(self, address, register, data):
        self.writes.append((address, register, data))
        if self.fail_once:
            self.fail_once = False
            raise OSError("injected disconnected adapter")
        self.registers[address][register:register + len(data)] = data
        if register == IOCON:
            self.registers[address][IOCON + 1] = data[0]

    def close(self):
        self.closed = True


class HardwareTests(unittest.TestCase):
    def setUp(self):
        self.mapping = load_mapping()

    def physical(self):
        mapping = copy.deepcopy(self.mapping)
        mapping.update(hardware_accepted=True, reset_confirmed=True)
        bus = FakeBus()
        hardware = LinuxHardware("/dev/fake", mapping)
        with patch("srrx.hardware._I2CTransport", return_value=bus):
            hardware.initialize_safe()
        return hardware, bus

    def test_map_matches_named_physical_pins_and_output_only_revision(self):
        self.assertEqual(self.mapping["outputs"]["CHG_INHIBIT"], {"address": 0x23, "port": 1, "bit": 4})
        self.assertEqual(self.mapping["outputs"]["EN_LNA3"], {"address": 0x20, "port": 0, "bit": 7})
        self.assertEqual(self.mapping["inputs"]["OVP_LNB_N"], {"address": 0x23, "port": 1, "bit": 5})
        self.assertFalse(any(pin["bit"] == 7 for pin in self.mapping["inputs"].values()))

    def test_sim_starts_safe_and_does_not_invent_adc_registers(self):
        hardware = SimHardware()
        hardware.initialize_safe()
        self.assertTrue(hardware.outputs["CHG_INHIBIT"])
        self.assertTrue(all(not value for net, value in hardware.outputs.items() if net != "CHG_INHIBIT"))
        with self.assertRaises(HardwareError):
            hardware.read(0x41, 0, 2)
        with self.assertRaises(HardwareError):
            hardware.apply_outputs({"TX_ENABLE": True})

    def test_trace_keeps_only_the_newest_events_and_stays_a_list(self):
        hardware = SimHardware()
        hardware.initialize_safe()
        before = len(hardware.trace)
        hardware.apply_outputs({"EN_LNA1": True})
        self.assertEqual([e["event"] for e in hardware.trace[before:]], ["outputs"])  # Callers slice it.
        for _ in range(TRACE_LIMIT * 4):
            hardware.all_off()
        self.assertEqual(len(hardware.trace), TRACE_LIMIT)
        self.assertEqual(hardware.trace[-1]["event"], "all_off")
        self.assertNotIn("initialize_safe", [e["event"] for e in hardware.trace])
        json.dumps(hardware.trace)  # Still plain JSON-serialisable diagnostics.

    def test_unaccepted_physical_mode_never_opens_bus(self):
        hardware = LinuxHardware("/dev/fake", self.mapping)
        with patch("srrx.hardware._I2CTransport") as factory:
            with self.assertRaises(HardwareError):
                hardware.initialize_safe()
            factory.assert_not_called()

    def test_register_order_safe_charge_and_interrupt_configuration(self):
        hardware, bus = self.physical()
        for address in ADDRESSES:
            registers = [register for addr, register, data in bus.writes if addr == address]
            self.assertLess(registers.index(OLAT), registers.index(IODIR))
            self.assertLess(registers.index(IOCON), len(registers) - 1)
            self.assertEqual(bus.registers[address][IOCON], 0x44)
            self.assertEqual(bus.registers[address][GPPU:GPPU + 2], b"\0\0")
            self.assertFalse(bus.registers[address][IODIR] & 0x80)
            self.assertFalse(bus.registers[address][IODIR + 1] & 0x80)
        self.assertEqual(bus.registers[0x23][OLAT + 1], 0x10)
        self.assertFalse(bus.registers[0x23][GPPU + 1] & 0x20)
        self.assertTrue(hardware.initialized)
        # Shared open-drain MCP_INT: every chip is ODR|MIRROR before any GPINTEN.
        enables = [i for i, (addr, register, data) in enumerate(bus.writes) if register == GPINTEN and any(data)]
        iocon = [i for i, (addr, register, data) in enumerate(bus.writes) if register == IOCON]
        self.assertEqual(len(iocon), len(ADDRESSES))
        self.assertLess(max(iocon), min(enables))

    def test_only_fault_pins_interrupt_against_defval_with_ipol_cleared(self):
        hardware, bus = self.physical()
        faults = {address: bytearray(2) for address in ADDRESSES}
        for net, pin in self.mapping["inputs"].items():
            if net.startswith(("FAULT_", "FLT_")):
                faults[pin["address"]][pin["port"]] |= 1 << pin["bit"]
        for address in ADDRESSES:
            for register in (GPINTEN, DEFVAL, INTCON):
                self.assertEqual(bus.registers[address][register:register + 2], bytes(faults[address]))
            self.assertEqual(bus.registers[address][IPOL:IPOL + 2], b"\0\0")
        # OVP_LNB_N/PG/DCS edges must not occupy U303/U302 INTF and hide a fault pulse.
        self.assertEqual(bus.registers[0x23][GPINTEN:GPINTEN + 2], b"\x20\x0f")
        self.assertEqual(bus.registers[0x22][GPINTEN:GPINTEN + 2], b"\x7f\x00")
        ovp = self.mapping["inputs"]["OVP_LNB_N"]
        self.assertFalse(bus.registers[ovp["address"]][GPINTEN + ovp["port"]] & 1 << ovp["bit"])

    def test_non_reset_ipol_defval_or_intcon_requires_reset_without_writes(self):
        for register in (IPOL, DEFVAL, INTCON, GPINTEN + 1):
            with self.subTest(register=register):
                mapping = dict(self.mapping, hardware_accepted=True, reset_confirmed=True)
                bus = FakeBus()
                bus.registers[0x23][register] = 0x01
                hardware = LinuxHardware("/dev/fake", mapping)
                with patch("srrx.hardware._I2CTransport", return_value=bus):
                    with self.assertRaises(HardwareError):
                        hardware.initialize_safe()
                self.assertEqual(bus.writes, [])
                self.assertTrue(hardware.faulted)

    def test_input_poll_is_one_sequential_read_per_chip(self):
        hardware, bus = self.physical()
        bus.reads.clear()
        hardware.read_inputs()
        # Config proof plus INTF, INTCAP, GPIO in one transaction per chip.
        self.assertEqual(bus.reads, [(address, IODIR, GPIO + 2) for address in ADDRESSES])

    def test_silent_mcp_reset_detected_by_poll_and_safe_off(self):
        hardware, bus = self.physical()
        hardware.apply_outputs({"EN_LNA1": True})
        self.assertIn("FAULT_LNA1", hardware.read_inputs())
        bus.registers[0x23][:] = bytearray(0x20)
        bus.registers[0x23][0:2] = b"\xff\xff"  # reset image: CHG_INHIBIT high impedance
        with self.assertRaises(HardwareError):
            hardware.read_inputs()
        self.assertTrue(hardware.faulted)
        self.assertTrue(any(e["event"] == "all_off_unconfirmed" for e in hardware.trace))
        hardware, bus = self.physical()
        bus.registers[0x20][IODIR:IODIR + 2] = b"\xff\xff"
        with self.assertRaises(HardwareError):
            hardware.all_off()  # OLAT readback alone would falsely confirm
        self.assertTrue(hardware.faulted)

    def test_unknown_bank_requires_reset_without_speculative_writes(self):
        mapping = dict(self.mapping, hardware_accepted=True, reset_confirmed=True)
        bus = FakeBus()
        bus.registers[0x22][IOCON] = 0x80
        hardware = LinuxHardware("/dev/fake", mapping)
        with patch("srrx.hardware._I2CTransport", return_value=bus):
            with self.assertRaises(HardwareError):
                hardware.initialize_safe()
        self.assertEqual(bus.writes, [])
        self.assertTrue(hardware.faulted)

    def test_write_failure_attempts_all_off_and_permanently_latches(self):
        hardware, bus = self.physical()
        hardware.apply_outputs({"EN_LNA1": True})
        bus.fail_once = True
        with self.assertRaises(HardwareError):
            hardware.apply_outputs({"EN_LNA2": True})
        self.assertTrue(hardware.faulted)
        self.assertEqual(bus.registers[0x20][OLAT:OLAT + 2], b"\0\0")
        self.assertEqual(bus.registers[0x23][OLAT + 1], 0x10)
        with self.assertRaises(HardwareError):
            hardware.apply_outputs({"EN_LNA1": True})

    def test_latched_short_fault_is_not_lost_when_gpio_recovered(self):
        hardware, bus = self.physical()
        bus.registers[0x22][0x12] = 0xff  # present GPIO normal
        bus.registers[0x22][0x0e] = 0x02  # LNA1 generated interrupt
        bus.registers[0x22][0x10] = 0xfd  # captured active-low fault
        self.assertFalse(hardware.read_inputs()["FAULT_LNA1"])

    def test_raw_mcp_write_cannot_bypass_output_image(self):
        hardware, bus = self.physical()
        with self.assertRaises(HardwareError):
            hardware.write(0x20, OLAT, b"\xff\xff")
        bus.registers[0x41] = bytearray(0x20)
        hardware.write(0x41, 0, b"\x00\x00")


if __name__ == "__main__":
    unittest.main()
