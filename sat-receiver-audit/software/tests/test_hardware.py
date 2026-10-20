import copy
import unittest
from unittest.mock import patch

from srrx.hardware import (ADDRESSES, GPINTEN, GPPU, IOCON, IODIR, OLAT,
                           HardwareError, LinuxHardware, SimHardware, load_mapping)


class FakeBus:
    def __init__(self):
        self.registers = {address: bytearray(0x20) for address in ADDRESSES}
        for registers in self.registers.values():
            registers[0:2] = b"\xff\xff"
        self.writes = []
        self.fail_once = False
        self.closed = False

    def read(self, address, register, count):
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
