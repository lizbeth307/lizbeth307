"""Unit checks for lab guard and service derivation; no fake systemd PASS."""
import ast
import copy
import hashlib
import importlib.util
from pathlib import Path
import re
import tempfile
import types
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("srrx_guest_smoke", Path(__file__).with_name("guest_smoke.py"))
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


class GuestBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.facts = {"uid": 0, "architecture": "aarch64", "system": "Linux", "pid1": "systemd",
                      "distribution": {"ID": "ubuntu", "VERSION_ID": "24.04", "VERSION_CODENAME": "noble"},
                      "network_interfaces": ["lo"]}
        self.marker = {"schema_version": 1, "environment": "qemu-arm64-linux-lab", "hardware_passthrough": False}

    def test_exact_guest_contract_is_accepted_without_producing_report(self):
        self.assertEqual(smoke.validate_guest_facts(self.facts, self.marker), self.facts)

    def test_host_nonroot_other_arch_init_and_network_are_rejected(self):
        for changes in ({"uid": 1000}, {"architecture": "x86_64"}, {"pid1": "supervisord"},
                        {"system": "Darwin"}, {"network_interfaces": ["eth0", "lo"]},
                        {"distribution": {"ID": "ubuntu", "VERSION_ID": "22.04", "VERSION_CODENAME": "jammy"}}):
            with self.subTest(changes=changes), self.assertRaises(smoke.SmokeError):
                smoke.validate_guest_facts(dict(self.facts, **changes), self.marker)

    def test_pico_group_must_exist_without_labclient_or_any_member(self):
        client = types.SimpleNamespace(pw_name="labclient", pw_gid=1001)
        group = lambda *members, gid=998: types.SimpleNamespace(gr_gid=gid, gr_mem=list(members))
        self.assertEqual(smoke.validate_pico_group(group(), client).gr_gid, 998)
        for bad in (group("labclient"), group("labd"), group(gid=1001)):
            with self.subTest(members=bad.gr_mem, gid=bad.gr_gid), self.assertRaises(smoke.SmokeError):
                smoke.validate_pico_group(bad, client)
        source = Path(SPEC.origin).read_text()
        self.assertIn('for group in ("labd", "i2c", "dialout", "srrx-pico"):', source)
        bootstrap = Path(SPEC.origin).with_name("guest_bootstrap.sh").read_text()
        self.assertIn("groupadd -f --system srrx-pico\n", bootstrap)
        self.assertNotIn("srrx-pico", next(l for l in bootstrap.splitlines() if "useradd" in l and "labclient" in l))

    def test_open_records_must_reach_the_release_guard_exit_2(self):
        show = "{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 -B /opt/srrx/deployment/deploy.py release-guard ; ignore_errors=no ; pid=812 ; code=exited ; status=%s }"
        self.assertTrue(smoke.release_guard_exited_2(show % "2"))
        # 216/GROUP: a missing SupplementaryGroups group fails before the guard ever runs.
        for status in ("216", "216/GROUP", "20", "2/INT", "12"):
            with self.subTest(status=status):
                self.assertFalse(smoke.release_guard_exited_2(show % status))

    def test_missing_marker_or_passthrough_never_authorizes_guest_mutation(self):
        for marker in ({}, [], {**self.marker, "hardware_passthrough": True},
                       {**self.marker, "hardware_passthrough": 0}, {**self.marker, "schema_version": True},
                       {**self.marker, "environment": "production"}):
            with self.subTest(marker=marker), self.assertRaises(smoke.SmokeError):
                smoke.validate_guest_facts(self.facts, marker)


class ServiceBoundaryTests(unittest.TestCase):
    def test_actual_production_sandbox_is_retained_in_separate_simulation_unit(self):
        project = Path(__file__).resolve().parents[2]
        original = (project / "software/systemd/srrx.service").read_text()
        generated = smoke.simulation_unit(original)
        for directive in ("User=labd", "Group=labd", "ProtectSystem=strict", "ProtectHome=yes", "NoNewPrivileges=yes",
                          "PrivateTmp=yes", "ProtectKernelTunables=yes", "ProtectKernelModules=yes",
                          "ProtectControlGroups=yes", "RestrictAddressFamilies=AF_UNIX", "Restart=on-failure",
                          "RuntimeDirectoryMode=0750", "UMask=0007", "MemoryMax=128M", "TasksMax=8"):
            self.assertIn(directive + "\n", generated)
        for forbidden in ("--hardware", "EnvironmentFile=", "ConditionPathExists=", "SupplementaryGroups=", "[Install]", "WantedBy="):
            self.assertNotIn(forbidden, generated)
        self.assertIn("--simulate --project /opt/srrx --socket " + smoke.SOCKET, generated)
        self.assertIn("RuntimeDirectory=srrx-linux-lab\n", generated)
        self.assertIn("PrivateDevices=yes\nDevicePolicy=closed\nCapabilityBoundingSet=\n", generated)

    def test_unknown_service_cannot_be_silently_replaced(self):
        with self.assertRaises(smoke.SmokeError):
            smoke.simulation_unit("[Service]\nExecStart=/bin/true\n")

    def test_simulation_assertions_reject_hardware_and_unsafe_outputs(self):
        good = {"mode": "SIMULATION", "hardware_qualified": False,
                "policy": {"simulation": True, "armed": False, "outputs": {"CHG_INHIBIT": True, "EN_LNA1": False}}}
        self.assertIs(smoke.assert_simulation(good, safe=True), good)
        cases = []
        for key, value in (("mode", "HARDWARE"), ("hardware_qualified", True)):
            changed = copy.deepcopy(good); changed[key] = value; cases.append(changed)
        for key, value in (("simulation", False), ("armed", True), ("outputs", {}),
                           ("outputs", {"CHG_INHIBIT": False}),
                           ("outputs", {"CHG_INHIBIT": True, "EN_LNA1": True}),
                           ("outputs", {"CHG_INHIBIT": True, "EN_LNA1": 0})):
            changed = copy.deepcopy(good); changed["policy"][key] = value; cases.append(changed)
        for changed in cases:
            with self.subTest(changed=changed), self.assertRaises(smoke.SmokeError):
                smoke.assert_simulation(changed, safe=True)

    def test_no_poweroff_command_or_enable_command_is_issued(self):
        # Every string constant reachable from any call, so list-form argv,
        # concatenation and other spellings are covered, not three literals.
        forbidden = {"enable", "poweroff", "reboot", "halt", "kexec"}
        def bad(value):
            words = {value, value.rsplit("/", 1)[-1], value.split(".", 1)[0]}
            return bool(words & forbidden) or "srrx-poweroff" in value or re.search(
                r"\bsystemctl\b.*\b(?:enable|poweroff|reboot|halt|kexec)\b", value) is not None
        tree = ast.parse(Path(SPEC.origin).read_text())
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        self.assertGreater(len(calls), 100)
        for node in calls:
            constants = [item.value for item in ast.walk(node) if isinstance(item, ast.Constant) and type(item.value) is str]
            self.assertFalse(any(bad(value) for value in constants), ast.unparse(node)[:300])
        for sample in ('["/usr/bin/systemctl", "enable", SIM_UNIT]', '"srrx-poweroff" + ".service"', '"/usr/sbin/poweroff"',
                       '"systemctl poweroff"', '"reboot.target"'):
            with self.subTest(sample=sample):
                values = [item.value for item in ast.walk(ast.parse(sample)) if isinstance(item, ast.Constant)]
                self.assertTrue(any(bad(value) for value in values))
        self.assertEqual(smoke.REQUIRED_STEPS[-1], "gui_handoff")


class DeviceWaitTests(unittest.TestCase):
    """DEP-11 guest step: only throwaway probe units, the installed generator, and full cleanup."""
    PROJECT = Path(__file__).resolve().parents[2]

    def guest(self, escape=None, fail=None):
        guest = smoke.GuestSmoke.__new__(smoke.GuestSmoke)
        guest.project, self.calls = self.PROJECT, []
        def command(args, accepted=(0,), **kwargs):
            args = [str(a) for a in args]
            self.calls.append(args)
            if args[0] == "/usr/bin/systemd-escape":
                out = escape(args[-1]) if escape else "dev-" + args[-1][len("/dev/"):].replace("/", "-") + ".device"
                return types.SimpleNamespace(returncode=0, stdout=out + "\n", stderr="")
            if fail and args[1:] == fail:
                raise smoke.SmokeError("injected systemctl failure")
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        guest.command = command
        return guest

    def test_step_runs_after_staging_with_throwaway_units_only(self):
        self.assertEqual(smoke.REQUIRED_STEPS[smoke.REQUIRED_STEPS.index("candidate_stage") + 1], "systemd_device_wait_bounded")
        deploy = smoke.load_deploy(self.PROJECT)
        self.assertNotIn(smoke.DEVICE_PROBE, ("/dev/lab/rtla", "/dev/lab/rtlb", "/dev/lab/hfplus", "/dev/lab/pico", "/dev/lab/gnss"))
        self.assertEqual(deploy.device_unit(smoke.DEVICE_PROBE), "dev-lab-srrxabsent.device")
        for name, text in smoke.device_probe_units().items():
            self.assertTrue(name.startswith("srrx-linux-lab-"), name)
            for forbidden in ("[Install]", "WantedBy=", "--hardware", "srrx.service", "/dev/"):
                self.assertNotIn(forbidden, text)
        bootstrap = Path(SPEC.origin).with_name("guest_bootstrap.sh").read_text()
        for path in (smoke.DEVWAIT_UNIT, smoke.DEVRETRY_UNIT, smoke.DEVWAIT_UNIT + ".d", smoke.DEVRETRY_UNIT + ".d",
                     deploy.device_unit(smoke.DEVICE_PROBE) + ".d"):
            self.assertIn("/etc/systemd/system/" + path, bootstrap)

    def test_escape_mismatch_writes_nothing_and_failure_removes_every_probe_file(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(smoke, "UNIT_DIR", Path(temporary)):
            guest = self.guest(escape=lambda path: "dev-lab-" + path.rsplit("/", 1)[-1])  # no .device suffix
            with self.assertRaisesRegex(smoke.SmokeError, "differs from systemd-escape"):
                guest.device_wait()
            self.assertEqual(list(Path(temporary).iterdir()), [])
            self.assertTrue(all(call[0] == "/usr/bin/systemd-escape" for call in self.calls))
            guest = self.guest(fail=["start", smoke.DEVWAIT_UNIT])
            with self.assertRaisesRegex(smoke.SmokeError, "injected"):
                guest.device_wait()
            self.assertEqual(list(Path(temporary).iterdir()), [])
            commands = [call[1:] for call in self.calls if call[0] == "/usr/bin/systemctl"]
            for expected in (["stop", smoke.DEVRETRY_UNIT], ["reset-failed", smoke.DEVWAIT_UNIT]):
                self.assertIn(expected, commands)
            self.assertEqual(commands[-1], ["daemon-reload"])
            # A preexisting file is never replaced, and therefore never removed by the cleanup.
            existing = Path(temporary) / smoke.DEVWAIT_UNIT
            existing.write_text("[Service]\nExecStart=/bin/true\n")
            with self.assertRaisesRegex(smoke.SmokeError, "refusing to replace"):
                self.guest().device_wait()
            self.assertEqual(existing.read_text(), "[Service]\nExecStart=/bin/true\n")

    def test_report_attests_the_readiness_contract_the_guest_compared(self):
        with tempfile.TemporaryDirectory() as temporary:
            guest = smoke.GuestSmoke.__new__(smoke.GuestSmoke)
            guest.project, guest.report_path = self.PROJECT, Path(temporary) / "system-smoke.json"
            guest.data, guest.sim_started, guest.rpc_client = {"steps": []}, False, None
            guest.step = mock.Mock(side_effect=smoke.SmokeError("stopped before any guest action"))
            data = guest.execute({})
        self.assertEqual(data["status"], "FAIL")
        contract = self.PROJECT / "design/readiness-contract.json"
        self.assertEqual(data["source_sha256"]["design/readiness-contract.json"], hashlib.sha256(contract.read_bytes()).hexdigest())
        self.assertIn("deployment/linux_lab/guest_smoke.py", data["source_sha256"])


class TripCauseTests(unittest.TestCase):
    """Every trip disarms; fault/link-loss steps must prove their own cause."""
    def runner(self, fault):
        tripped = {"mode": "SIMULATION", "hardware_qualified": False,
                   "pico": {"state": "TRIPPED", "mcp_reset": True},
                   "policy": {"simulation": True, "armed": False, "fault": fault,
                              "outputs": {"CHG_INHIBIT": True, "EN_LNA1": False}}}
        guest = smoke.GuestSmoke.__new__(smoke.GuestSmoke)
        guest.arm = guest.enable_lna = lambda: None
        guest.rpc = lambda request, expected=True: {"ok": expected}
        guest.status = lambda: copy.deepcopy(tripped)
        def wait_status(predicate, timeout=10, context=""):
            self.assertTrue(predicate(tripped))
            return copy.deepcopy(tripped)
        guest.wait_status = wait_status
        return guest

    def test_fault_step_requires_injected_input_as_first_fault(self):
        with mock.patch.object(smoke.time, "sleep"):
            self.assertEqual(self.runner("active-low fault: FAULT_LNA1").fault()["exact_fault"], "active-low fault: FAULT_LNA1")
            for other in ("GPIO inputs stale", "pico_status_timeout", "active-low fault: FAULT_LABPORT", None):
                with self.subTest(other=other), self.assertRaisesRegex(smoke.SmokeError, "different reason"):
                    self.runner(other).fault()

    def test_link_loss_step_requires_status_deadline_as_first_fault(self):
        with mock.patch.object(smoke.time, "sleep"):
            self.assertEqual(self.runner("pico_status_timeout").link_loss()["exact_fault"], "pico_status_timeout")
            for other in ("GPIO inputs stale", "active-low fault: FAULT_LNA1", "owner lease expired", None):
                with self.subTest(other=other), self.assertRaisesRegex(smoke.SmokeError, "different reason"):
                    self.runner(other).link_loss()


if __name__ == "__main__":
    unittest.main()
