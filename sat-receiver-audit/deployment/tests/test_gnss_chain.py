"""GNSS reader chain in staging and doctor: units, polkit rule, mode drop-ins, mutual exclusion.

Temporary directories only; no unit is enabled or started and no device is opened.
The live behaviour (polkit on noble, _chrony, gpsd -n re-open, dev-lab-gnss.device) is
a QEMU guest and Q6A item, never claimed by these tests.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import deploy

UNITS = deploy.PROJECT / "software/systemd"
EXEMPT = ("srrx-locationd.service", "srrx-timegate.service", "srrx-gnss-config.service")


def settings(text):
    result = {}
    for line in text.splitlines():
        if "=" in line and not line.startswith(("#", ";")):
            key, value = line.split("=", 1)
            result.setdefault(key, []).append(value)
    return result


class GnssChainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-gnss-chain-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def devices(self):
        config = deploy.load(HERE / "devices.template.json")
        config["i2c"]["ina228"] = {"path": "/dev/i2c-7", "of_fullname": "/soc@0/test-ina228"}
        config["i2c"]["control"] = {"path": "/dev/i2c-9", "of_fullname": "/soc@0/test-control"}
        config["pico"]["kernel_parent"] = "99c000.serial"
        config["usb"]["hfplus"]["serial"] = "AIRSPYHF SN:0123456789ABCDEF"
        config["wifi_bt"]["fe11s_port4_usb_path"] = "1-1.4"
        return config

    def staged(self, mode, name=None):
        destination = self.root / (name or mode)
        deploy.stage(destination, self.devices(), mode)
        return destination / "rootfs", json.loads((destination / "stage-files.json").read_text())["files"]

    def test_units_are_least_privilege_and_device_free(self):
        loc = settings((UNITS / "srrx-locationd.service").read_text())
        self.assertEqual((loc["User"], loc["Group"]), (["srrx-loc"], ["srrx-loc"]))
        self.assertNotIn("SupplementaryGroups", loc)  # srrx-gnss only through the raw-mode drop-in
        for key, value in (("RestrictAddressFamilies", "AF_UNIX"), ("IPAddressDeny", "any"), ("NoNewPrivileges", "yes"),
                           ("ProtectSystem", "strict"), ("CapabilityBoundingSet", ""), ("RuntimeDirectory", "srrx-loc")):
            self.assertEqual(loc[key], [value], key)
        self.assertIn("-m srrx.locationd --gnss ${SRRX_GNSS} --socket /run/srrx-loc/location.sock --control-user labd",
                      loc["ExecStart"][0])
        gate = settings((UNITS / "srrx-timegate.service").read_text())
        self.assertEqual((gate["User"], gate["PrivateNetwork"], gate["RestrictAddressFamilies"], gate["ReadWritePaths"]),
                         (["_chrony"], ["yes"], ["AF_UNIX"], ["-/run/chrony"]))
        self.assertIn("-m srrx.timegate --socket /run/srrx-timegate/timegate.sock --peer-user labd", gate["ExecStart"][0])
        config_text = (UNITS / "srrx-gnss-config.service").read_text()
        config = settings(config_text)
        self.assertNotIn("[Install]", config_text)  # started only by labd through polkit, never enabled
        for key, value in (("Type", "oneshot"), ("User", "root"), ("PrivateNetwork", "yes"),
                           ("RuntimeDirectory", "srrx-gnss-config"), ("RuntimeDirectoryPreserve", "yes"),
                           ("RestrictAddressFamilies", "AF_UNIX"), ("CapabilityBoundingSet", "CAP_DAC_OVERRIDE")):
            self.assertEqual(config[key], [value], key)
        self.assertIn("-m srrx.gnss_config --gnss ${SRRX_GNSS} --result /run/srrx-gnss-config/result.json",
                      config["ExecStart"][0])
        for name in EXEMPT:
            self.assertNotIn("dev-lab", (UNITS / name).read_text(), name)
        service = settings((UNITS / "srrx.service").read_text())
        self.assertTrue(service["ExecStart"][0].endswith("--gnss ${SRRX_GNSS}"))
        self.assertEqual(service["SupplementaryGroups"], ["i2c dialout srrx-pico"])  # labd never reads NMEA
        self.assertEqual(service["RestrictAddressFamilies"], ["AF_UNIX"])

    def test_gpsd_stage_has_the_polkit_rule_loopback_dropin_and_gpsd_device_order(self):
        rootfs, files = self.staged("gpsd")
        self.assertIn("SRRX_GNSS=gpsd", (rootfs / "etc/srrx/devices.env").read_text().splitlines())
        rule = (rootfs / deploy.GNSS_POLKIT_RULE).read_text()
        self.assertEqual(rule, deploy.gnss_polkit_rule())
        self.assertEqual(rule.count("polkit.addRule("), 1)
        for needle in ('"org.freedesktop.systemd1.manage-units"', 'action.lookup("unit") == "srrx-gnss-config.service"',
                       'action.lookup("verb") == "start"', 'subject.user == "labd"', "polkit.Result.YES"):
            self.assertIn(needle, rule)
        for word in ("restart", "stop", "srrx.service", "gpsd", "chrony", "Result.AUTH"):
            self.assertNotIn(word, rule)
        self.assertEqual(rule.count("{"), rule.count("}"))
        units = rootfs / "etc/systemd/system"
        dropin = settings((units / "srrx-locationd.service.d" / deploy.GNSS_MODE_DROPIN).read_text())
        self.assertEqual(dropin["RestrictAddressFamilies"], ["AF_INET AF_INET6"])
        self.assertEqual(dropin["IPAddressAllow"], ["localhost"])
        self.assertNotIn("SupplementaryGroups", dropin)
        self.assertTrue((units / "gpsd.service.d" / deploy.LAB_DEVICE_DROPIN).is_file())
        for name in EXEMPT[1:]:
            self.assertFalse((units / (name + ".d")).exists(), name)  # no release guard, no drop-in at all
        self.assertFalse((units / "srrx-locationd.service.d/20-release-guard.conf").exists())
        for name in ("srrx.service", "srrx-poweroff.service"):
            self.assertTrue((units / (name + ".d/20-release-guard.conf")).is_file(), name)
        for name in EXEMPT:
            self.assertIn("etc/systemd/system/" + name, files)
        self.assertIn(deploy.GNSS_POLKIT_RULE, files)

    def test_raw_stage_gives_locationd_the_uart_group_and_device_order(self):
        rootfs, files = self.staged("raw")
        units = rootfs / "etc/systemd/system"
        self.assertIn("SRRX_GNSS=raw", (rootfs / "etc/srrx/devices.env").read_text().splitlines())
        dropin = settings((units / "srrx-locationd.service.d" / deploy.GNSS_MODE_DROPIN).read_text())
        self.assertEqual(dropin, {"Wants": ["dev-lab-gnss.device"], "After": ["dev-lab-gnss.device"],
                                  "Conflicts": ["gpsd.service gpsd.socket"], "SupplementaryGroups": ["srrx-gnss"]})
        self.assertFalse((units / "gpsd.service.d").exists())
        self.assertEqual((units / "dev-lab-gnss.device.d" / deploy.DEVICE_TIMEOUT_DROPIN).read_text(),
                         "[Unit]\nJobRunningTimeoutSec=30s\n")
        self.assertEqual(deploy.gnss_mode_issues(rootfs), [])  # the generator satisfies the doctor check

    def test_off_stage_and_invalid_modes(self):
        rootfs, files = self.staged("off")
        self.assertIn("SRRX_GNSS=off", (rootfs / "etc/srrx/devices.env").read_text().splitlines())
        units = rootfs / "etc/systemd/system"
        for path in (rootfs / deploy.GNSS_POLKIT_RULE, units / "srrx-locationd.service.d", units / "gpsd.service.d",
                     units / "dev-lab-gnss.device.d"):
            self.assertFalse(path.exists(), path)
        for bad in ("GPSD", "both", None, ""):
            with self.subTest(mode=bad), self.assertRaises(deploy.DeploymentError):
                deploy.stage(self.root / "bad", self.devices(), bad)
            self.assertFalse((self.root / "bad").exists())
        with self.assertRaises(deploy.DeploymentError):
            deploy.gnss_mode_dropin("off")
        plain = self.root / "plain"
        deploy.stage(plain)  # config-less (QEMU guest candidate): no GNSS deployment files at all
        self.assertFalse((plain / "rootfs" / deploy.GNSS_POLKIT_RULE).exists())

    def test_stage_cli_takes_the_mode(self):
        devices = self.root / "devices.json"
        devices.write_text(json.dumps(self.devices()))
        result = subprocess.run([sys.executable, "-I", str(HERE / "deploy.py"), "stage", "--dest", str(self.root / "cli"),
                                 "--devices", str(devices), "--gnss", "raw"], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SRRX_GNSS=raw", (self.root / "cli/rootfs/etc/srrx/devices.env").read_text())
        refused = subprocess.run([sys.executable, "-I", str(HERE / "deploy.py"), "stage", "--dest", str(self.root / "x"),
                                  "--gnss", "both"], capture_output=True, text=True, timeout=60)
        self.assertNotEqual(refused.returncode, 0)

    def put(self, root, relative, text):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def test_doctor_sees_one_reader_or_blocks(self):
        root = self.root / "target"
        self.assertEqual(deploy.gnss_mode_issues(root), [])  # no deployment record at all
        env = self.put(root, "etc/srrx/devices.env", "SRRX_PICO=/dev/lab/pico\n")
        self.assertEqual(deploy.gnss_mode_issues(root), ["SRRX_GNSS missing or invalid in /etc/srrx/devices.env (gpsd, raw or off)"])
        env.write_text("SRRX_GNSS=gpsd\n")
        defaults = self.put(root, "etc/default/gpsd", 'DEVICES="/dev/lab/gnss"\nGPSD_OPTIONS="-n -b -s 115200"\nUSBAUTO="false"\n')
        self.assertEqual(deploy.gnss_mode_issues(root), [])  # build/07 §18 exactly
        for text, issue in (('DEVICES="/dev/lab/gnss /dev/ttyHS1"\nGPSD_OPTIONS="-n -b"\nUSBAUTO="false"\n', "DEVICES must be exactly"),
                            ('DEVICES="/dev/lab/gnss"\nGPSD_OPTIONS="-n"\nUSBAUTO="false"\n', "keep -n -b"),
                            ('DEVICES="/dev/lab/gnss"\nGPSD_OPTIONS="-n -b"\nUSBAUTO="true"\n', "USBAUTO")):
            with self.subTest(issue=issue):
                defaults.write_text(text)
                self.assertTrue(any(issue in item for item in deploy.gnss_mode_issues(root)), deploy.gnss_mode_issues(root))
        defaults.write_text('DEVICES="/dev/lab/gnss"\nGPSD_OPTIONS="-n -b"\nUSBAUTO="false"\n')
        raw_dropin = self.put(root, "etc/systemd/system/srrx-locationd.service.d/" + deploy.GNSS_MODE_DROPIN,
                              deploy.gnss_mode_dropin("raw"))
        self.assertEqual(deploy.gnss_mode_issues(root), ["srrx-locationd holds srrx-gnss outside raw mode"])
        env.write_text("SRRX_GNSS=raw\n")
        link = self.put(root, "etc/systemd/system/sockets.target.wants/gpsd.socket", "")
        issues = deploy.gnss_mode_issues(root)
        self.assertIn("raw mode: gpsd DEVICES still lists /dev/lab/gnss", issues)
        self.assertIn("raw mode: gpsd enabled (gpsd.socket)", issues)
        defaults.unlink()
        link.unlink()
        self.assertEqual(deploy.gnss_mode_issues(root), [])
        raw_dropin.unlink()
        self.assertEqual(deploy.gnss_mode_issues(root), ["raw mode: srrx-locationd lacks its 40-gnss-mode.conf drop-in"])
        env.write_text("SRRX_GNSS=off\n")
        self.assertEqual(deploy.gnss_mode_issues(root), [])

    def test_unreadable_reader_configuration_blocks(self):
        if os.geteuid() == 0:
            self.skipTest("root reads a 0000 file")
        root = self.root / "target"
        env = self.put(root, "etc/srrx/devices.env", "SRRX_GNSS=gpsd\n")
        env.chmod(0)
        self.addCleanup(env.chmod, 0o644)
        issues = deploy.gnss_mode_issues(root)
        self.assertEqual(len(issues), 1)
        self.assertTrue(issues[0].startswith("GNSS reader configuration unreadable: "), issues)
        self.assertIn("PermissionError", issues[0])

    def test_staged_gpsd_root_with_the_build07_defaults_passes(self):
        rootfs, unused = self.staged("gpsd", "gpsd-doctor")
        self.put(rootfs, "etc/default/gpsd", 'DEVICES="/dev/lab/gnss"\nGPSD_OPTIONS="-n -b -s 115200"\nUSBAUTO="false"\n')
        self.assertEqual(deploy.gnss_mode_issues(rootfs), [])

    def test_doctor_reports_and_blocks_on_gnss_reader_issues(self):
        quiet = lambda args, **kwargs: {"returncode": 0, "stdout": "", "stderr": ""}
        issue = "raw mode: gpsd enabled (gpsd.service)"
        with patch.object(deploy, "command", quiet), patch.object(deploy, "gnss_mode_issues", return_value=[issue]):
            report = deploy.doctor()
        self.assertIn(issue, report["issues"])
        self.assertEqual(report["gnss_readers"], {"status": "BLOCKED", "issues": [issue]})
        self.assertEqual(report["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
