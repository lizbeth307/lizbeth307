"""Policy-checked LC76G RESET_N pulse on SimHardware, LinuxHardware over a fake
I2C register file, the simulated Engine and labctl.

Simulation only: no MCP, no scope trace of the pulse and no hardware PASS. The
reset circuit (Q301/R326) and the Pico watchdog release stay bench items (E3-08).
"""
import copy
import errno
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch

from srrx import cli
from srrx.engine import Engine
from srrx.hardware import ADDRESSES, IOCON, OLAT, HardwareError, LinuxHardware, SimHardware, load_mapping
from srrx.link import SimLink
from srrx.policy import GNSS_RESET_GATE, SAFE_UNCONFIRMED, SafetyPolicy

PROJECT = Path(__file__).resolve().parents[2]
GATE = GNSS_RESET_GATE


class PolicyPulseTests(unittest.TestCase):
    def setUp(self):
        self.hardware = SimHardware()
        self.policy = SafetyPolicy(self.hardware, clock=lambda: 0)
        self.inputs = self.hardware.read_inputs()
        self.inputs.update(DCS_UHF=False, DCS_LBAND=False, DCS_HF=False,
                           PG_LNB=True, PG_BONI=True, PTC_AUX=True, OVP_LNB_N=True)

    def lease(self, now):
        self.assertTrue(self.policy.command("lease", {"owner": "daemon", "ttl_ms": 5000}, now)["ok"])

    def pulse(self, now, value=None):
        self.lease(now)
        return self.policy.command("gnss_reset", value, now)

    def gate(self):
        return self.hardware.outputs[GATE]

    def test_gate_is_a_mapped_output_that_the_safe_image_holds_low(self):
        self.assertIn(GATE, self.hardware.mapping["outputs"])
        self.assertFalse(self.gate())
        self.assertEqual(self.policy.status()["gnss_reset"]["state"], "IDLE")

    def test_pulse_is_asserted_then_released_by_tick_at_its_width(self):
        self.assertFalse(self.policy.armed)  # Energizes nothing: allowed disarmed.
        result = self.pulse(1000, {"width_ms": 200})
        self.assertEqual(result, {"ok": True, "state": "ASSERTED", "width_ms": 200, "release_due_ms": 1200})
        self.assertTrue(self.gate())
        status = self.policy.status()["gnss_reset"]
        self.assertEqual((status["state"], status["last_ms"], status["release_due_ms"], status["pulses_15min"]),
                         ("ASSERTED", 1000, 1200, 1))
        self.policy.tick(1199)
        self.assertTrue(self.gate())
        self.policy.tick(1200)
        self.assertFalse(self.gate())
        status = self.policy.status()["gnss_reset"]
        self.assertEqual((status["state"], status["release_ms"], status["last_width_ms"], status["last_error"]),
                         ("IDLE", 1200, 200, None))
        self.assertIsNone(self.policy.fault)
        self.assertTrue(self.hardware.outputs["CHG_INHIBIT"])
        # Only the gate ever changed: no EN_ output was energized by the pulse.
        self.assertFalse(any(event["outputs"][name] for event in self.hardware.trace
                             for name in event["outputs"] if name.startswith("EN_")))

    def test_default_width_and_range_limits(self):
        self.assertEqual(self.pulse(0)["width_ms"], 200)
        self.policy.tick(200)
        self.assertEqual(self.pulse(30200, {})["width_ms"], 200)
        self.policy.tick(30400)
        self.assertEqual(self.pulse(60400, {"width_ms": 100})["width_ms"], 100)
        self.policy.tick(60500)
        self.assertFalse(self.gate())
        policy = SafetyPolicy(SimHardware(), clock=lambda: 0)
        policy.command("lease", {"owner": "daemon", "ttl_ms": 5000}, 0)
        self.assertEqual(policy.command("gnss_reset", {"width_ms": 500}, 0)["width_ms"], 500)

    def test_bad_widths_and_values_are_refused_without_a_write(self):
        self.lease(0)
        count = len(self.hardware.trace)
        for value in ({"width_ms": 99}, {"width_ms": 501}, {"width_ms": True}, {"width_ms": False},
                      {"width_ms": 200.0}, {"width_ms": "200"}, {"width_ms": None}, {"width_ms": 10 ** 400},
                      {"width_ms": 200, "repeat": 2}, [200], 200, "200"):
            with self.subTest(value=value):
                result = self.policy.command("gnss_reset", value, 0)
                self.assertFalse(result["ok"])
        self.assertEqual(len(self.hardware.trace), count)
        self.assertFalse(self.gate())
        self.assertEqual(self.policy.status()["gnss_reset"]["pulses_15min"], 0)

    def test_spacing_from_release_and_three_per_fifteen_minutes(self):
        self.assertTrue(self.pulse(0)["ok"])
        self.policy.tick(200)
        self.assertIn("GNSS_RESET_SPACING", self.pulse(30199)["error"])
        self.assertFalse(self.gate())
        self.assertTrue(self.pulse(30200)["ok"])
        self.assertIn("GNSS_RESET_IN_PROGRESS", self.policy.command("gnss_reset", None, 30300)["error"])
        self.policy.tick(30400)
        self.assertTrue(self.pulse(60400)["ok"])
        self.policy.tick(60600)
        self.assertEqual(self.policy.status()["gnss_reset"]["pulses_15min"], 3)
        self.assertIn("GNSS_RESET_RATE_LIMIT", self.pulse(90600)["error"])
        for now in range(90600, 899999, 50000):
            self.policy.tick(now)  # No automatic escalation or retry.
            self.assertFalse(self.gate())
        self.assertIn("GNSS_RESET_RATE_LIMIT", self.pulse(899999)["error"])
        self.assertTrue(self.pulse(900000)["ok"])  # The first start left the window.
        self.assertEqual(self.policy.status()["gnss_reset"]["pulses_15min"], 3)

    def test_preconditions_lease_initialization_and_latched_fault(self):
        self.assertIn("lease", self.policy.command("gnss_reset", None, 0)["error"])
        self.hardware.initialized = False
        self.assertIn("GNSS_RESET_HARDWARE", self.pulse(0)["error"])
        self.hardware.initialized = True
        self.hardware.faulted = True
        self.assertIn("GNSS_RESET_HARDWARE", self.pulse(0)["error"])
        self.hardware.faulted = False
        self.policy.trip("operator trip")
        self.assertIn("fault latched", self.pulse(0)["error"])
        self.assertFalse(self.gate())
        self.assertEqual(self.policy.status()["gnss_reset"]["pulses_15min"], 0)

    def test_allowed_while_armed_without_disturbing_the_session(self):
        self.policy.refresh_inputs(self.inputs, 0)
        self.policy.set_readiness(pico_active=True, commissioned=True)
        self.lease(0)
        self.assertTrue(self.policy.command("arm", True, 0)["ok"])
        self.assertTrue(self.policy.command("gnss_reset", {"width_ms": 300}, 0)["ok"])
        self.policy.refresh_inputs(self.inputs, 200)
        self.policy.tick(200)
        self.assertTrue(self.gate() and self.policy.armed)
        self.policy.refresh_inputs(self.inputs, 300)
        self.policy.tick(300)
        self.assertFalse(self.gate())
        self.assertTrue(self.policy.armed)
        self.assertIsNone(self.policy.fault)

    def test_trip_disarm_and_reinitialization_mid_pulse_release_the_gate(self):
        self.assertTrue(self.pulse(0, {"width_ms": 500})["ok"])
        self.policy.trip("pico_TRIPPED")
        self.assertFalse(self.gate())
        status = self.policy.status()["gnss_reset"]
        self.assertEqual((status["state"], status["last_error"], status["release_ms"]), ("IDLE", "GNSS_RESET_ABORTED", 0))
        # A fresh policy for the other two release paths.
        for release in ("disarm", "initialize_safe"):
            with self.subTest(release=release):
                hardware = SimHardware()
                policy = SafetyPolicy(hardware, clock=lambda: 0)
                policy.command("lease", {"owner": "daemon", "ttl_ms": 5000}, 0)
                self.assertTrue(policy.command("gnss_reset", {"width_ms": 500}, 0)["ok"])
                if release == "disarm":
                    self.assertTrue(policy.command("disarm", None, 100)["ok"])
                else:
                    hardware.initialize_safe()  # Engine re-initialization on a new CONFIGURING.
                    policy.tick(100)
                self.assertFalse(hardware.outputs[GATE])
                status = policy.status()["gnss_reset"]
                self.assertEqual((status["state"], status["last_error"], status["last_width_ms"]),
                                 ("IDLE", "GNSS_RESET_ABORTED", 100))
                self.assertTrue(policy.command("lease", {"owner": "daemon", "ttl_ms": 5000}, 30099)["ok"])
                self.assertIn("GNSS_RESET_SPACING", policy.command("gnss_reset", None, 30099)["error"])
                self.assertTrue(policy.command("gnss_reset", None, 30100)["ok"])

    def test_late_tick_releases_immediately_and_records_overrun(self):
        self.assertTrue(self.pulse(0, {"width_ms": 500})["ok"])
        self.policy.tick(1000)  # Exactly at the hard deadline: late, not an overrun.
        self.assertEqual(self.policy.status()["gnss_reset"]["last_error"], None)
        self.policy.tick(31000)
        self.assertTrue(self.pulse(31000, {"width_ms": 200})["ok"])
        self.policy.tick(36000)
        self.assertFalse(self.gate())
        status = self.policy.status()["gnss_reset"]
        self.assertEqual((status["state"], status["last_error"], status["last_width_ms"], status["release_ms"]),
                         ("IDLE", "GNSS_RESET_OVERRUN", 5000, 36000))
        self.assertIsNone(self.policy.fault)  # Holding RESET_N longer energizes nothing.

    def test_failed_deassert_trips_to_the_safe_image(self):
        self.assertTrue(self.pulse(0)["ok"])
        with patch.object(self.hardware, "apply_outputs", side_effect=OSError("bus gone")):
            self.policy.tick(200)
        self.assertIn("GNSS reset de-assert failed", self.policy.fault)
        self.assertFalse(self.policy.fault.endswith(SAFE_UNCONFIRMED))
        self.assertFalse(self.gate())
        self.assertEqual(self.hardware.trace[-1]["event"], "all_off")
        status = self.policy.status()["gnss_reset"]
        # all_off returned on an initialized adapter: it, not the image, proves the release.
        self.assertEqual((status["state"], status["last_error"], status["release_ms"], status["last_width_ms"]),
                         ("IDLE", "GNSS_RESET_DEASSERT_FAILED", 200, 200))
        self.assertIn("fault latched", self.pulse(40000)["error"])

    def test_unconfirmed_release_blocks_pulses_until_explicit_recovery(self):
        self.assertTrue(self.pulse(0)["ok"])
        def unconfirmed():
            # LinuxHardware.all_off semantics: the image is reset to safe, then it raises.
            SimHardware.all_off(self.hardware)
            raise HardwareError("Safe outputs not confirmed; request Pico MCP RESET")
        with patch.object(self.hardware, "apply_outputs", side_effect=OSError("bus gone")), \
                patch.object(self.hardware, "all_off", side_effect=unconfirmed):
            self.policy.tick(200)
        self.assertTrue(self.policy.fault.endswith(SAFE_UNCONFIRMED))
        self.assertFalse(self.gate())  # The image says low; that is not evidence.
        status = self.policy.status()["gnss_reset"]
        self.assertEqual((status["state"], status["last_error"], status["release_ms"], status["last_width_ms"]),
                         ("RELEASE_UNCONFIRMED", "GNSS_RESET_RELEASE_UNCONFIRMED", None, None))
        for now in (220, 240, 1000):
            self.policy.tick(now)  # No retry loop of writes on a broken bus.
        self.assertEqual(self.policy.status()["gnss_reset"]["state"], "RELEASE_UNCONFIRMED")
        self.assertIn("fault latched", self.pulse(1000)["error"])
        self.policy.refresh_inputs(self.inputs, 40000)
        self.policy.set_readiness(pico_active=True, commissioned=True)
        self.assertTrue(self.policy.clear_fault(40000))
        self.assertFalse(self.gate())
        status = self.policy.status()["gnss_reset"]
        # Proven only at the recovery: spacing counts from it; the width stays unknown.
        self.assertEqual((status["state"], status["release_ms"], status["last_width_ms"], status["last_error"]),
                         ("IDLE", 40000, None, "GNSS_RESET_RELEASE_UNCONFIRMED"))
        self.assertIn("GNSS_RESET_SPACING", self.pulse(69999)["error"])
        self.assertTrue(self.pulse(70000)["ok"])

    def test_failed_assert_latches_and_counts_the_attempt(self):
        self.lease(0)
        with patch.object(self.hardware, "apply_outputs", side_effect=OSError("bus gone")):
            self.assertFalse(self.policy.command("gnss_reset", None, 0)["ok"])
        self.assertIn("I2C", self.policy.fault)
        self.assertFalse(self.gate())
        status = self.policy.status()["gnss_reset"]
        # A failed write may have reached OLAT before its read-back failed: it counts.
        self.assertEqual((status["state"], status["pulses_15min"], status["last_error"], status["release_ms"],
                          status["last_width_ms"]), ("IDLE", 1, "GNSS_RESET_ASSERT_FAILED", 0, None))

    def test_raw_reset_gate_net_is_still_refused(self):
        self.lease(0)
        for value in (True, False):
            self.assertFalse(self.policy.command(GATE, value, 0)["ok"])
        self.policy.refresh_inputs(self.inputs, 0)
        self.policy.set_readiness(pico_active=True, commissioned=True)
        self.assertTrue(self.policy.command("arm", True, 0)["ok"])
        for value in (True, False, 1):
            result = self.policy.command(GATE, value, 0)
            self.assertFalse(result["ok"])
            self.assertIn("raw GPIO is forbidden", result["error"])
        self.assertFalse(self.gate())


class RegisterFile:
    """MCP23017 BANK0 reset register image behind a fake I2C adapter that can break."""
    def __init__(self):
        self.registers = {address: bytearray(0x20) for address in ADDRESSES}
        for registers in self.registers.values():
            registers[0:2] = b"\xff\xff"
        self.broken = self.fail_once = False
        self.attempts = 0

    def _check(self):
        self.attempts += 1
        if self.broken or self.fail_once:
            self.fail_once = False
            raise OSError(errno.EIO, "I2C adapter gone")

    def read(self, address, register, count):
        self._check()
        return bytes(self.registers[address][register:register + count])

    def write(self, address, register, data):
        self._check()
        self.registers[address][register:register + len(data)] = data
        if register == IOCON:
            self.registers[address][IOCON + 1] = data[0]

    def close(self):
        pass


class PhysicalReleaseTests(unittest.TestCase):
    """LinuxHardware resets its image before reporting an unconfirmed all_off."""
    def setUp(self):
        mapping = copy.deepcopy(load_mapping())
        mapping.update(hardware_accepted=True, reset_confirmed=True)
        self.pin = mapping["outputs"][GATE]
        self.hardware = LinuxHardware("/dev/fake-i2c", mapping)
        self.bus = self.reset_mcp()
        self.policy = SafetyPolicy(self.hardware, clock=lambda: 0)
        self.assertIsNone(self.policy.fault)

    def reset_mcp(self):
        """A Pico MCP RESET followed by the supervisor's one-use reset assertion."""
        bus = RegisterFile()
        self.hardware.mapping["reset_confirmed"] = True
        with patch("srrx.hardware._I2CTransport", return_value=bus):
            self.hardware.initialize_safe()
        return bus

    def pulse(self, now, width=200):
        self.assertTrue(self.policy.command("lease", {"owner": "daemon", "ttl_ms": 5000}, now)["ok"])
        return self.policy.command("gnss_reset", {"width_ms": width}, now)

    def physical_gate(self, bus):
        return bool(bus.registers[self.pin["address"]][OLAT + self.pin["port"]] & 1 << self.pin["bit"])

    def unconfirmed(self):
        status = self.policy.status()["gnss_reset"]
        self.assertEqual((status["state"], status["release_ms"], status["last_width_ms"], status["last_error"]),
                         ("RELEASE_UNCONFIRMED", None, None, "GNSS_RESET_RELEASE_UNCONFIRMED"))
        self.assertTrue(self.hardware.faulted)
        self.assertFalse(self.hardware.outputs[GATE])  # The image claims low; it proves nothing.

    def test_pulse_and_release_are_read_back_from_the_register_file(self):
        self.assertTrue(self.pulse(0)["ok"])
        self.assertTrue(self.physical_gate(self.bus))
        self.policy.tick(200)
        self.assertFalse(self.physical_gate(self.bus))
        status = self.policy.status()["gnss_reset"]
        self.assertEqual((status["state"], status["release_ms"], status["last_width_ms"]), ("IDLE", 200, 200))

    def test_broken_bus_never_reports_an_unproven_release_as_idle(self):
        for path in ("deassert", "trip", "disarm", "read_inputs", "failed_reinit"):
            with self.subTest(path=path):
                self.setUp()
                self.assertTrue(self.pulse(0)["ok"])
                self.bus.broken = True
                if path == "deassert":
                    self.policy.tick(200)
                    self.assertIn("GNSS reset de-assert failed", self.policy.fault)
                elif path == "trip":
                    self.policy.trip("pico_TRIPPED")
                elif path == "disarm":
                    self.assertFalse(self.policy.command("disarm", None, 100)["ok"])
                elif path == "read_inputs":
                    # LinuxHardware._fail resets the image before the policy hears of it.
                    with self.assertRaises(HardwareError):
                        self.hardware.read_inputs()
                    self.policy.tick(100)
                else:
                    self.hardware.mapping["reset_confirmed"] = True
                    with patch("srrx.hardware._I2CTransport", side_effect=OSError(errno.ENODEV, "no adapter")), \
                            self.assertRaises(HardwareError):
                        self.hardware.initialize_safe()
                    # This all_off returns without error but writes nothing: no verified bus.
                    self.policy.trip("MCP re-initialization failed")
                    self.assertFalse(self.policy.fault.endswith(SAFE_UNCONFIRMED))
                self.unconfirmed()
                self.assertTrue(self.physical_gate(self.bus))  # Exactly why the image is no evidence.
                if path in ("deassert", "trip", "disarm"):
                    self.assertTrue(self.policy.fault.endswith(SAFE_UNCONFIRMED))
                attempts = self.bus.attempts
                for now in (220, 240, 1000, 5000):
                    self.policy.tick(now)  # No write retries on a broken bus.
                self.assertEqual(self.bus.attempts, attempts)
                self.unconfirmed()
                self.assertFalse(self.pulse(40000)["ok"])
                self.assertEqual(self.bus.attempts, attempts)

    def test_failed_assert_on_a_broken_bus_is_unconfirmed_and_counted(self):
        self.bus.broken = True
        result = self.pulse(0)
        self.assertFalse(result["ok"])
        self.assertTrue(self.policy.fault.endswith(SAFE_UNCONFIRMED))
        self.unconfirmed()
        self.assertEqual(self.policy.status()["gnss_reset"]["pulses_15min"], 1)

    def test_transient_failure_is_idle_only_because_all_off_read_back(self):
        self.assertTrue(self.pulse(0)["ok"])
        self.bus.fail_once = True  # The de-assert OLAT write fails; every later access works.
        self.policy.tick(200)
        self.assertTrue(self.hardware.faulted)  # Latched until a Pico MCP RESET.
        self.assertFalse(self.policy.fault.endswith(SAFE_UNCONFIRMED))
        self.assertFalse(self.physical_gate(self.bus))
        status = self.policy.status()["gnss_reset"]
        self.assertEqual((status["state"], status["release_ms"], status["last_width_ms"], status["last_error"]),
                         ("IDLE", 200, 200, "GNSS_RESET_DEASSERT_FAILED"))
        self.assertIn("fault latched", self.pulse(40000)["error"])

    def test_recovery_needs_mcp_reset_and_clear_fault_then_spacing_from_the_proof(self):
        self.assertTrue(self.pulse(0)["ok"])
        self.bus.broken = True
        self.policy.tick(200)
        self.unconfirmed()
        inputs = {net: True for net in self.hardware.mapping["inputs"]}
        self.policy.set_readiness(pico_active=True, commissioned=True)
        self.policy.refresh_inputs(inputs, 1000)
        self.assertFalse(self.policy.clear_fault(1000))  # Adapter latch: a Pico MCP RESET first.
        self.unconfirmed()
        bus = self.reset_mcp()
        self.assertFalse(self.hardware.faulted)
        # The policy itself has not yet proven the release.
        self.assertEqual(self.policy.status()["gnss_reset"]["state"], "RELEASE_UNCONFIRMED")
        self.policy.refresh_inputs(inputs, 2000)
        self.assertTrue(self.policy.clear_fault(2000))
        status = self.policy.status()["gnss_reset"]
        self.assertEqual((status["state"], status["release_ms"], status["last_width_ms"]), ("IDLE", 2000, None))
        self.assertIn("GNSS_RESET_SPACING", self.pulse(31999)["error"])
        self.assertTrue(self.pulse(32000)["ok"])
        self.assertTrue(self.physical_gate(bus))
        self.policy.tick(32200)
        self.assertFalse(self.physical_gate(bus))


class EnginePulseTests(unittest.TestCase):
    def setUp(self):
        self.hardware = SimHardware()
        self.hardware.set_inputs({n: False for n in self.hardware.inputs if n.startswith("DCS_")})
        self.link = SimLink(PROJECT)
        self.engine = Engine(self.hardware, self.link, simulated=True)
        self.addCleanup(self.engine.close)
        self.now = 0
        self.engine.tick(self.now)

    def advance(self, target):
        while self.now < target:
            self.now = min(target, self.now + 20)
            self.engine.tick(self.now)

    def request(self, owner, **fields):
        return self.engine.request(dict(fields, _owner=owner), self.now)

    def arm(self):
        self.assertTrue(self.request("uid:1000", op="arm")["ok"])
        self.advance(self.now + 800)
        self.assertTrue(self.engine.policy.armed, self.engine.status())

    def test_unconfigured_engine_refuses_even_the_lease_holder(self):
        self.advance(400)
        self.assertTrue(self.request("uid:1000", op="lease", value={"ttl_ms": 5000})["ok"])
        result = self.request("uid:1000", op="gnss_reset")
        self.assertFalse(result["ok"])
        self.assertIn("configured", result["error"])
        self.assertFalse(self.hardware.outputs[GATE])

    def test_only_the_lease_owner_pulses_and_tick_releases(self):
        self.arm()
        for owner in ("uid:1001", "direct-test"):
            result = self.request(owner, op="gnss_reset", value={"width_ms": 200})
            self.assertFalse(result["ok"])
            self.assertIn("own valid lease", result["error"])
        self.assertFalse(self.hardware.outputs[GATE])
        start = self.now
        result = self.request("uid:1000", op="gnss_reset", value={"width_ms": 200})
        self.assertTrue(result["ok"], result)
        self.assertTrue(self.hardware.outputs[GATE])
        self.assertEqual(self.engine.status()["policy"]["gnss_reset"]["state"], "ASSERTED")
        self.advance(start + 180)
        self.assertTrue(self.hardware.outputs[GATE])
        self.advance(start + 220)
        self.assertFalse(self.hardware.outputs[GATE])
        self.assertTrue(self.engine.policy.armed)  # The session survives; nothing else changed.
        self.assertIn("GNSS_RESET_SPACING", self.request("uid:1000", op="gnss_reset")["error"])

    def test_pico_reset_or_stale_status_refuses(self):
        self.arm()
        pico = dict(self.engine.pico)
        self.engine.pico = dict(pico, mcp_reset=True)
        self.assertIn("MCP RESET", self.request("uid:1000", op="gnss_reset")["error"])
        self.engine.pico = pico
        self.engine.last_status_ms = self.now - 501
        self.assertIn("fresh Pico status", self.request("uid:1000", op="gnss_reset")["error"])
        self.assertFalse(self.hardware.outputs[GATE])

    def test_pico_status_loss_mid_pulse_trips_and_releases_before_the_width(self):
        self.arm()
        self.assertTrue(self.request("uid:1000", op="sim", name="drop_link", value=True)["ok"])
        self.advance(self.now + 200)  # Status is now 200..300 ms old: still fresh enough to start.
        start = self.now
        self.assertTrue(self.request("uid:1000", op="gnss_reset", value={"width_ms": 500})["ok"])
        released = None
        while self.now < start + 500:
            self.advance(self.now + 20)
            if released is None and not self.hardware.outputs[GATE]:
                released = self.now
        self.assertIsNotNone(released)
        self.assertLess(released, start + 500)
        self.assertFalse(self.engine.policy.armed)
        status = self.engine.status()["policy"]
        self.assertIn("pico_status_timeout", status["fault"])
        self.assertEqual((status["gnss_reset"]["state"], status["gnss_reset"]["last_error"]),
                         ("IDLE", "GNSS_RESET_ABORTED"))

    def test_labctl_sends_a_bounded_named_request(self):
        sent = []
        def once(path, request, timeout=2.0):
            sent.append(request)
            return {"ok": True, "state": "ASSERTED"}
        with patch.object(cli, "request_once", side_effect=once), redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["gnss_reset"]), 0)
            self.assertEqual(cli.main(["gnss_reset", "--width-ms", "300"]), 0)
        self.assertEqual(sent, [{"op": "gnss_reset", "value": {"width_ms": 200}},
                                {"op": "gnss_reset", "value": {"width_ms": 300}}])
        with patch.object(cli, "request_once", return_value={"ok": False, "error": "GNSS_RESET_RATE_LIMIT"}), \
                redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli.main(["gnss_reset"]), 2)
        self.assertEqual(json.loads(out.getvalue())["error"], "GNSS_RESET_RATE_LIMIT")


if __name__ == "__main__":
    unittest.main()
