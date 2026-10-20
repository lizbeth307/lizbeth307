"""Unit checks for lab guard and service derivation; no fake systemd PASS."""
import copy
import importlib.util
from pathlib import Path
import unittest

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
        source = Path(SPEC.origin).read_text()
        self.assertNotIn('self.systemctl("enable"', source)
        self.assertNotIn('self.systemctl("poweroff"', source)
        self.assertNotIn('self.systemctl("start", "srrx-poweroff.service"', source)
        self.assertEqual(smoke.REQUIRED_STEPS[-1], "gui_handoff")


if __name__ == "__main__":
    unittest.main()
