"""Temporary-directory fixtures never represent accepted hardware/releases."""
import copy
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import deploy
import vendor_patch


def body(text, signature):
    start = text.index("{", text.index(signature))
    depth = 0
    for end in range(start, len(text)):
        depth += (text[end] == "{") - (text[end] == "}")
        if depth == 0:
            return text[start + 1:end]
    raise ValueError("unterminated fixture body")


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-deploy-test-")
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

    def test_template_is_rejected_and_serial_rules_are_exact(self):
        with self.assertRaises(deploy.DeploymentError):
            deploy.validate_devices(deploy.load(HERE / "devices.template.json"))
        rules = deploy.udev_rules(self.devices())
        self.assertIn('ATTR{serial}=="LABRXA"', rules)
        self.assertIn('ATTR{serial}=="AIRSPYHF SN:0123456789ABCDEF"', rules)
        self.assertNotIn('MODE="0666"', rules)
        self.assertNotIn('TAG+="uaccess"', rules)
        # HMI users join labd for the socket; the Pico UART needs a group no human is in.
        self.assertIn('SYMLINK+="lab/pico"', rules)
        self.assertNotIn('GROUP="labd"', rules)
        self.assertEqual(rules.count('GROUP="srrx-pico"'), 1)
        self.assertEqual(rules.count('TAG+="systemd"'), 4)
        config = self.devices()
        config["pico"].update(kind="usb", kernel_parent=None, vid="2e8a", pid="000a", serial="E6614C311B7A1234")
        self.assertIn('ATTRS{serial}=="E6614C311B7A1234", GROUP="srrx-pico"', deploy.udev_rules(config))
        # labd opens the Pico tty with TIOCEXCL + flock; a ModemManager AT probe must not race it.
        for text in (rules, deploy.udev_rules(config)):
            pico = [line for line in text.splitlines() if 'SYMLINK+="lab/pico"' in line]
            self.assertEqual(len(pico), 1)
            self.assertIn('ENV{ID_MM_DEVICE_IGNORE}="1"', pico[0])
            self.assertEqual(text.count("ID_MM_DEVICE_IGNORE"), 1)
        documented = (deploy.PROJECT / "software/DEPLOYMENT.md").read_text(encoding="utf-8")
        self.assertIn("TIOCEXCL", documented)
        self.assertIn("ID_MM_DEVICE_IGNORE", documented)

    def test_release_guard_does_not_block_an_offline_clock_behind_acceptance(self):
        devices = self.root / "devices.json"
        devices.write_text(json.dumps(self.devices()))
        sys.path.insert(0, str(deploy.PROJECT / "software"))
        import srrx.commissioning as commissioning
        seen = {}
        def accepted(path, project, raw=None, clock_check=True):
            seen.update(path=Path(path), clock_check=clock_check)
            raise deploy.DeploymentError("acceptance stop")
        with patch.object(deploy, "doctor", return_value={"issues": []}), patch.object(commissioning, "load_acceptance", accepted):
            with self.assertRaisesRegex(deploy.DeploymentError, "acceptance stop"):
                deploy.release_guard(devices, self.root / "acceptance.json", self.root / "release.json",
                                     self.root / "build-manifest.json", self.root / "cache")
        # ExecStartPre runs at every start; the 2026 floor and evidence ordering stay in load_acceptance.
        self.assertEqual(seen, {"path": self.root / "acceptance.json", "clock_check": False})

    @unittest.skipUnless(os.name == "posix", "grp/pwd are POSIX-only")
    def test_live_pico_node_must_not_be_reachable_by_hmi_users(self):
        import grp, pwd, types
        if Path("/dev/null").exists():
            with self.assertRaisesRegex(deploy.DeploymentError, "other users"):
                deploy.device_node("rtl_a", "/dev/null")
        node = lambda gid, mode=0o660: os.stat_result((stat.S_IFCHR | mode, 0, 0, 1, 0, gid, 0, 0, 0, 0))
        users = [types.SimpleNamespace(pw_name="labd", pw_gid=4241), types.SimpleNamespace(pw_name="operator", pw_gid=1000)]
        def check(live, members=(), extra=()):
            with (patch.object(Path, "stat", return_value=live),
                  patch.object(grp, "getgrnam", return_value=types.SimpleNamespace(gr_gid=4242, gr_mem=list(members))),
                  patch.object(pwd, "getpwall", return_value=users + list(extra))):
                return deploy.device_node("pico", "/dev/lab/pico")
        self.assertEqual(check(node(4242)).st_gid, 4242)
        self.assertEqual(check(node(4242), ["labd"]).st_gid, 4242)
        for live, members, extra in ((node(4241), (), ()),  # old GROUP="labd": every HMI operator could write the UART
                                     (node(4242), ["operator"], ()),
                                     (node(4242), (), [types.SimpleNamespace(pw_name="kiosk", pw_gid=4242)]),
                                     (node(4242, 0o664), (), ())):
            with self.subTest(gid=live.st_gid, members=members, extra=extra), self.assertRaises(deploy.DeploymentError):
                check(live, members, extra)

    def test_units_keep_pico_group_private_and_bridge_recoverable(self):
        units = deploy.PROJECT / "software/systemd"
        service = (units / "srrx.service").read_text().splitlines()
        groups = next(l for l in service if l.startswith("SupplementaryGroups=")).split("=", 1)[1].split()
        self.assertIn("srrx-pico", groups)
        self.assertIn("User=labd", service)
        bridge = (units / "srrx-poweroff.service").read_text().splitlines()
        # A transient boot-time guard failure of srrx must not leave the bridge failed with a dependency error.
        self.assertFalse(any(l.startswith(("Requires=", "BindsTo=")) for l in bridge))
        for line in ("After=srrx.service", "Wants=srrx.service", "PartOf=srrx.service", "Restart=on-failure"):
            self.assertIn(line, bridge)
        # Device ordering lives only in the generated drop-in: guest_smoke.simulation_unit copies these
        # [Unit] lines, and a QEMU guest without /dev/lab nodes would wait for every device job.
        text = (units / "srrx.service").read_text()
        self.assertNotIn("dev-lab", text)
        self.assertFalse([l for l in text.splitlines() if l.startswith(("Wants=", "Requires=", "BindsTo="))])

    def test_stage_orders_receiver_after_lab_device_units(self):
        deploy.stage(self.root / "candidate", self.devices())
        units = self.root / "candidate/rootfs/etc/systemd/system"
        expected = {"dev-lab-rtla.device", "dev-lab-rtlb.device", "dev-lab-hfplus.device", "dev-lab-pico.device"}
        dropin = (units / "srrx.service.d" / deploy.LAB_DEVICE_DROPIN).read_text()
        fields = {}
        for line in dropin.splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                fields.setdefault(key, []).extend(value.split())
        self.assertEqual(set(fields), {"Wants", "After"})
        self.assertEqual(set(fields["Wants"]), expected)
        self.assertEqual(set(fields["After"]), expected)
        # A missing receiver stays a guard failure (exit 2) in doctor, never a dependency error or a stop.
        for word in ("Requires=", "BindsTo=", "Requisite=", "PartOf=", "dev-lab-gnss", "i2c"):
            self.assertNotIn(word, dropin)
        files = json.loads((self.root / "candidate/stage-files.json").read_text())["files"]
        self.assertIn("etc/systemd/system/srrx.service.d/" + deploy.LAB_DEVICE_DROPIN, files)
        timeouts = sorted(p.relative_to(units).as_posix() for p in units.glob("*.device.d/*"))
        # dev-lab-gnss.device: the one GNSS reader (gpsd here, the default --gnss) waits for it too.
        self.assertEqual(timeouts, sorted(unit + ".d/" + deploy.DEVICE_TIMEOUT_DROPIN
                                          for unit in expected | {"dev-lab-gnss.device"}))
        for relative in timeouts:
            self.assertEqual((units / relative).read_text(), "[Unit]\nJobRunningTimeoutSec=30s\n")
            self.assertIn("etc/systemd/system/" + relative, files)
        self.assertEqual(deploy.LAB_DEVICE_TIMEOUT_S, 30)
        # Neither the shutdown bridge nor the radio-off unit gains device lines; gpsd waits for the GNSS UART only.
        for path in units.rglob("*"):
            if (path.is_file() and "srrx.service.d" not in path.parts and "gpsd.service.d" not in path.parts
                    and not path.parent.name.endswith(".device.d")):
                self.assertNotIn("dev-lab", path.read_text(), path)
        gpsd = (units / "gpsd.service.d" / deploy.LAB_DEVICE_DROPIN).read_text().splitlines()
        self.assertEqual([l for l in gpsd if not l.startswith("#")],
                         ["[Unit]", "Wants=dev-lab-gnss.device", "After=dev-lab-gnss.device"])
        # Config-less staging (the QEMU guest's candidate) ships no device wait at all.
        deploy.stage(self.root / "plain")
        plain = self.root / "plain/rootfs/etc/systemd/system"
        self.assertFalse((plain / "srrx.service.d" / deploy.LAB_DEVICE_DROPIN).exists())
        self.assertFalse(list(plain.glob("*.device.d")))
        self.assertNotIn("dev-lab", (self.root / "plain/stage-files.json").read_text())

    def test_device_ordering_equals_the_udev_systemd_tags_and_the_doctor_set(self):
        config = self.devices()
        tagged = {"/dev/" + line.split('SYMLINK+="', 1)[1].split('"', 1)[0]
                  for line in deploy.udev_rules(config).splitlines() if 'TAG+="systemd"' in line}
        guarded = deploy.guarded_device_paths(config)
        self.assertEqual(list(guarded), ["rtl_a", "rtl_b", "hfplus", "pico"])
        self.assertEqual(tagged, set(guarded.values()))
        self.assertEqual(set(deploy.guarded_devices(config)), set(guarded))
        self.assertEqual({deploy.device_unit(p) for p in guarded.values()},
                         set(deploy.lab_device_dropin(guarded.values()).splitlines()[2].split("=", 1)[1].split()))
        # lab/gnss is tagged by its own rule but is neither guarded nor ordered.
        self.assertIn('SYMLINK+="lab/gnss", TAG+="systemd"', deploy.gnss_udev_rules())
        self.assertNotIn("/dev/lab/gnss", guarded.values())
        self.assertEqual(deploy.device_unit("/dev/lab/hfplus"), "dev-lab-hfplus.device")
        for bad in ("/dev/lab/rt-la", "/dev/lab/../x", "/dev/i2c-7", "/dev/lab/", "/dev/lab/Rtla", "/dev/lab/a/b", None):
            with self.subTest(path=bad), self.assertRaises(deploy.DeploymentError):
                deploy.device_unit(bad)
        self.assertEqual(deploy.device_timeout_dropin(3), "[Unit]\nJobRunningTimeoutSec=3s\n")
        for bad in (0, 301, 2.5, "30", True):
            with self.subTest(seconds=bad), self.assertRaises(deploy.DeploymentError):
                deploy.device_timeout_dropin(bad)

    def test_device_ambiguity_injection_and_lime_are_rejected(self):
        for mutate in (lambda c: c["i2c"]["control"].update(path="/dev/i2c-7"),
                       lambda c: c["usb"]["rtl_b"].update(serial="LABRXA"),
                       lambda c: c["usb"]["hfplus"].update(serial='x", RUN+="bad'),
                       lambda c: c["pico"].update(kernel_parent="*"),
                       lambda c: c["lime"].update(enabled=True),
                       lambda c: c["wifi_bt"].update(fe11s_port4_usb_path=None),
                       lambda c: c["wifi_bt"].update(fe11s_port4_usb_path="1-1.3"),
                       lambda c: c["wifi_bt"].update(fe11s_port4_usb_path='1-1.4", RUN+="bad'),
                       lambda c: c.pop("wifi_bt")):
            config = self.devices()
            mutate(config)
            with self.assertRaises(deploy.DeploymentError):
                deploy.validate_devices(config)
        # A devices.json written before the radio-off binding gets a specific, actionable refusal.
        config = self.devices()
        config.pop("wifi_bt")
        with self.assertRaisesRegex(deploy.DeploymentError, "predates the radio-off binding: add wifi_bt.fe11s_port4_usb_path"):
            deploy.validate_devices(config)

    def test_no_tty_or_usb_device_gets_two_binding_rules(self):
        # 71-srrx-gnss.rules binds UART6 998000.serial: a Pico there would be re-owned srrx-gnss 0640 and aliased lab/gnss.
        config = self.devices()
        config["pico"]["kernel_parent"] = deploy.GNSS_KERNEL_PARENT
        for build in (deploy.validate_devices, deploy.udev_rules):
            with self.subTest(build=build.__name__), self.assertRaisesRegex(deploy.DeploymentError, "998000.serial"):
                build(config)
        with self.assertRaises(deploy.DeploymentError):
            deploy.stage(self.root / "gnss-parent", config)
        self.assertFalse((self.root / "gnss-parent").exists())  # refused before anything is created
        # A USB Pico carrying a receiver identity would also match that receiver's usb_device rule (GROUP lab).
        for name in ("rtl_a", "rtl_b", "hfplus"):
            config = self.devices()
            receiver = config["usb"][name]
            config["pico"].update(kind="usb", kernel_parent=None, vid=receiver["vid"], pid=receiver["pid"], serial=receiver["serial"])
            with self.subTest(receiver=name), self.assertRaisesRegex(deploy.DeploymentError, "two bindings"):
                deploy.udev_rules(config)
        config = self.devices()
        config["pico"].update(kind="usb", kernel_parent=None, vid="0bda", pid="2838", serial="LABPICO1")
        rules = deploy.udev_rules(config)  # same VID/PID, other serial: the exact ATTR{serial} rules stay disjoint
        self.assertEqual(rules.count('SYMLINK+="lab/pico"'), 1)
        rules = (deploy.udev_rules(self.devices()) + deploy.gnss_udev_rules()).splitlines()
        aliases = [line.split('SYMLINK+="', 1)[1].split('"', 1)[0] for line in rules if "SYMLINK+=" in line]
        self.assertEqual(sorted(aliases), ["lab/gnss", "lab/hfplus", "lab/pico", "lab/rtla", "lab/rtlb"])
        parents = [line.split('KERNELS=="', 1)[1].split('"', 1)[0] for line in rules if "KERNELS==" in line]
        self.assertEqual(sorted(parents), ["998000.serial", "99c000.serial"])

    def test_stage_does_not_enable_or_create_acceptance(self):
        result = deploy.stage(self.root / "candidate", self.devices())
        self.assertFalse(result["services_enabled"])
        rootfs = self.root / "candidate/rootfs"
        self.assertFalse((rootfs / "etc/srrx/acceptance.json").exists())
        self.assertFalse(any(rootfs.rglob("*.wants")))
        self.assertFalse(any(p.is_symlink() for p in (rootfs / "etc/systemd").rglob("*")))
        if (deploy.PROJECT / "software/systemd/srrx-menu.service").exists():
            self.assertTrue((rootfs / "usr/lib/systemd/user/srrx-menu.service").exists())
            self.assertFalse((rootfs / "etc/systemd/system/srrx-menu.service").exists())
        guard = (rootfs / "etc/systemd/system/srrx.service.d/20-release-guard.conf").read_text()
        self.assertIn("ExecStartPre=", guard)
        self.assertIn("release-guard", guard)
        self.assertIn("ExecStartPre=/usr/bin/python3 -B /opt/srrx/deployment/deploy.py release-guard", guard)
        self.assertTrue((rootfs / "etc/systemd/system/srrx-poweroff.service.d/20-release-guard.conf").is_file())
        files = json.loads((self.root / "candidate/stage-files.json").read_text())["files"]
        for path in (deploy.RADIO_OFF_MODPROBE, deploy.RADIO_OFF_UDEV, "etc/systemd/system/" + deploy.RADIO_OFF_UNIT):
            self.assertIn(path, files)
        with self.assertRaises(deploy.DeploymentError):
            deploy.stage(self.root / "candidate")

    def test_stage_disables_q6a_wifi_bt_for_field_and_quiet_root(self):
        deploy.stage(self.root / "candidate", self.devices())
        rootfs = self.root / "candidate/rootfs"
        modprobe = (rootfs / deploy.RADIO_OFF_MODPROBE).read_text().splitlines()
        for module in ("aic_load_fw", "aic_load_fw_usb", "aic8800_fdrv", "aic8800_fdrv_usb",
                       "aic_btusb", "aic_btusb_usb", "btusb"):
            self.assertIn("blacklist " + module, modprobe)
            self.assertIn("install " + module + " /bin/false", modprobe)
        rule = (rootfs / deploy.RADIO_OFF_UDEV).read_text()
        self.assertIn('KERNEL=="1-1.4", ATTR{authorized}="0"', rule)
        self.assertNotIn("idVendor", rule)  # by port path, any VID
        unit = (rootfs / "etc/systemd/system" / deploy.RADIO_OFF_UNIT).read_text()
        self.assertIn("ExecStart=/usr/bin/python3 -B -m srrx.rfkill block", unit)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", unit)  # no __pycache__ in the verified tree
        self.assertIn("ProtectSystem=strict", unit)
        self.assertTrue((rootfs / "opt/srrx/software/srrx/rfkill.py").is_file())
        self.assertIn("Before=srrx.service", unit)
        dropin = (rootfs / "etc/systemd/system/srrx.service.d/10-radio-off.conf").read_text()
        self.assertIn("Requires=" + deploy.RADIO_OFF_UNIT, dropin)
        self.assertIn("After=" + deploy.RADIO_OFF_UNIT, dropin)
        self.assertNotIn("unblock", unit + dropin + "\n".join(modprobe))
        # DefaultDependencies=no: python runs from /opt, so the mount holding it comes first.
        self.assertIn("RequiresMountsFor=/opt/srrx", unit.splitlines())
        # The shutdown bridge must stay recoverable: no staged drop-in may give it a hard dependency.
        bridge = rootfs / "etc/systemd/system/srrx-poweroff.service.d"
        self.assertTrue(bridge.is_dir())
        lines = [line for path in sorted(bridge.rglob("*")) if path.is_file() for line in path.read_text().splitlines()]
        self.assertFalse([line for line in lines if line.startswith(("Requires=", "BindsTo=", "Requisite="))], lines)
        self.assertFalse((bridge / "10-radio-off.conf").exists())

    def radio_root(self, config=None):
        root = self.root / "target"
        (root / "proc").mkdir(parents=True)
        (root / "proc/modules").write_text("i2c_dev 24576 0 - Live 0x0\nusbserial 45056 0 - Live 0x0\n")
        (root / deploy.RADIO_OFF_MODPROBE).parent.mkdir(parents=True)
        (root / deploy.RADIO_OFF_MODPROBE).write_text(deploy.radio_off_modprobe())
        if config is not None:
            (root / deploy.RADIO_OFF_UDEV).parent.mkdir(parents=True)
            (root / deploy.RADIO_OFF_UDEV).write_text(deploy.radio_off_udev(config))
        for name, kind, soft in (("rfkill0", "wlan", "1"), ("rfkill1", "bluetooth", "1")):
            (root / "sys/class/rfkill" / name).mkdir(parents=True)
            (root / "sys/class/rfkill" / name / "type").write_text(kind + "\n")
            (root / "sys/class/rfkill" / name / "soft").write_text(soft + "\n")
            (root / "sys/class/rfkill" / name / "hard").write_text("0\n")
        (root / "sys/class/net/eth0").mkdir(parents=True)
        (root / "sys/bus/usb/devices/1-1").mkdir(parents=True)
        (root / "sys/bus/usb/devices/1-1/idVendor").write_text("1a86\n")
        (root / "sys/bus/usb/devices/1-1/authorized").write_text("1\n")
        return root

    def test_radio_self_check_passes_only_when_wifi_bt_is_off(self):
        config = self.devices()
        root = self.radio_root(config)
        self.assertEqual(deploy.radio_off_issues(config, root), [])
        port = root / "sys/bus/usb/devices/1-1.4"
        port.mkdir()
        (port / "idVendor").write_text("a69c\n")
        (port / "authorized").write_text("0\n")
        self.assertEqual(deploy.radio_off_issues(config, root), [])  # present but deauthorized, no driver
        cases = {
            "module": lambda r: (r / "proc/modules").write_text("aic8800_fdrv_usb 1 0 - Live 0x0\nbtusb 1 0 - Live 0x0\n"),
            "module-list": lambda r: (r / "proc/modules").unlink(),
            "blacklist": lambda r: (r / deploy.RADIO_OFF_MODPROBE).write_text("blacklist btusb\n"),
            "udev": lambda r: (r / deploy.RADIO_OFF_UDEV).unlink(),
            "rfkill": lambda r: (r / "sys/class/rfkill/rfkill0/soft").write_text("0\n"),
            "wlan": lambda r: (r / "sys/class/net/wlan0/wireless").mkdir(parents=True),
            "hci": lambda r: (r / "sys/class/bluetooth/hci0").mkdir(parents=True),
            "authorized": lambda r: (r / "sys/bus/usb/devices/1-1.4/authorized").write_text("1\n"),
            "driver": lambda r: (r / "sys/bus/usb/devices/1-1.4/1-1.4:1.0/driver").mkdir(parents=True),
            "other-vid": lambda r: [(r / "sys/bus/usb/devices/2-1").mkdir(),
                                    (r / "sys/bus/usb/devices/2-1/idVendor").write_text("368b\n")],
        }
        for label, mutate in cases.items():
            with self.subTest(case=label):
                shutil.rmtree(root)
                root = self.radio_root(config)
                port = root / "sys/bus/usb/devices/1-1.4"
                port.mkdir()
                (port / "idVendor").write_text("a69c\n")
                (port / "authorized").write_text("0\n")
                mutate(root)
                self.assertTrue(deploy.radio_off_issues(config, root))
        shutil.rmtree(root)
        root = self.radio_root(config)
        self.assertEqual(deploy.radio_off_issues(None, root), [])
        broken = self.devices()
        broken["wifi_bt"]["fe11s_port4_usb_path"] = None
        self.assertTrue(deploy.radio_off_issues(broken, root))

    def test_doctor_and_release_guard_block_on_radio_issue(self):
        issue = "Wi-Fi/BT kernel modules loaded: aic8800_fdrv_usb"
        devices = self.root / "devices.json"
        devices.write_text(json.dumps(self.devices()))
        quiet = lambda args, **kwargs: {"returncode": 0, "stdout": "", "stderr": ""}
        with patch.object(deploy, "command", quiet), patch.object(deploy, "radio_off_issues", return_value=[issue]):
            report = deploy.doctor()
            self.assertIn(issue, report["issues"])
            self.assertEqual(report["radio_off"]["status"], "BLOCKED")
            self.assertEqual(report["status"], "BLOCKED")
            with self.assertRaisesRegex(deploy.DeploymentError, "aic8800_fdrv_usb"):
                deploy.release_guard(devices, self.root / "a", self.root / "r", self.root / "b", self.root / "c")

    def test_prohibited_package_list_covers_stack_and_keeps_required_packages(self):
        banned = {"wsjtx": "2.6.1", "js8call": "2.2.0", "fldigi": "4.2", "qsstv": "9.5", "direwolf": "1.7",
                  "urh": "2.9", "libhamlib-utils": "4.5", "libhamlib4t64": "4.5", "soapysdr0.8-module-remote": "0.5",
                  "soapysdr0.8-module-lms7": "20", "libsoapysdr0.9": "0.9", "limesuite": "20", "limesuiteng-gui": "1",
                  "gr-limesuiteng": "1", "gr-gsm": "1.0", "gr-iridium": "1.0", "kalibrate-rtl": "0.4",
                  "multimon-ng": "1.3.0", "dsdcc": "1.9", "rtl-433": "23.11", "acarsdec": "3.7", "dumphfdl": "1.4",
                  "dumpvdl2": "2.3", "libacars-tools": "2.2", "libacars2": "2.2", "digiham": "0.6",
                  "python3-digiham": "0.6", "codecserver": "0.2", "codecserver-driver-ambe3k": "0.2",
                  "dxlaprs-tetra": "1", "dxlaprs-lora": "1", "m17-demod": "1", "python3-meshtastic": "2",
                  "dump1090-fa": "9", "dump978-fa": "9", "skyaware978": "9", "piaware": "9", "nrsc5": "1",
                  "hpsdrconnector": "1", "lame": "3.100", "python3-paho-mqtt": "1.6", "aicrf-test": "4.0"}
        found = deploy.prohibited_installed(banned)
        self.assertEqual(found, sorted(banned))
        lab_only = {"dream": "2.1.1-2", "librtlsdr0": "2.0.1-2build1", "librtlsdr2": "2.0.1-2build1",
                    "sdrangel": "7.17.2-1", "sdrangelsrv": "7.17.2-1", "sdrpp": "1.1.0-1", "openwebrx": "1.2.126",
                    "satdump": "1.2.2-1", "rtl-sdr": "2.0.1-2build1", "gpredict": "2.3-115-g0f3beb6-3build3",
                    "gr-satellites": "5.5.0-2build2", "limesuiteng-cli": "1.0.0+lab1"}
        self.assertEqual(deploy.prohibited_installed(lab_only), sorted(lab_only))
        # The "+lab builds only" rule is the policy's (require_lab_build); librtlsdr0/limesuiteng-cli are forbidden outright.
        self.assertEqual(deploy.LAB_BUILD_ONLY_PACKAGES, deploy.lab_build_only_packages())
        self.assertLessEqual({"sdrangel", "sdrangelsrv", "sdrpp", "openwebrx", "satdump", "rtl-sdr", "gpredict", "gr-satellites"},
                             deploy.LAB_BUILD_ONLY_PACKAGES)
        self.assertFalse({"librtlsdr0", "limesuiteng-cli"} & deploy.LAB_BUILD_ONLY_PACKAGES)
        # Locked +lab versions (sources.lock.json) are the allowed ones, gr-satellites' -0lab1 revision included.
        lock = {c["id"]: c["version"] for c in deploy.load(HERE / "sources.lock.json")["components"]}
        allowed = {"dream": "2.1.1-2+lab1", "librtlsdr2": "2.0.3-0+lab1", "sdrangel": "7.27.2-1+lab1",
                   "openwebrx": "1.2.126+lab1", "gpredict": lock["gpredict"], "gr-satellites": lock["gr-satellites"],
                   "satdump": "2.0.0~alpha+git20260929+lab1", "sdrpp": "git8c9f5ee+lab1", "aic8800-usb-dkms": "4.0"}
        self.assertEqual(lock["gpredict"], "2.6+git20261011+lab1")
        dependencies = deploy.load(HERE / "dependencies.json")
        for name, versions in dependencies["required_target_packages"].items():
            allowed[name] = versions[0]
        for name, version in dependencies["additional_stack_package_versions"].items():
            allowed[name] = version or ""
        self.assertEqual(deploy.prohibited_installed(allowed), [])

    def test_prohibited_executables_on_target_are_reported(self):
        root = self.root / "target"
        (root / "usr/bin").mkdir(parents=True)
        (root / "usr/sbin").mkdir(parents=True)
        for name in ("wifi_test", "bt_test", "rigctld", "rtl_tcp", "rtl_sdr", "python3", "rtl_biast", "rotctld", "LimeGUI", "satdump"):
            (root / "usr/bin" / name).write_text("")
        (root / "usr/sbin/RTL_EEPROM").write_text("")
        # Same set as verify_build (BAD_NAMES) and selftest RX-01b (policy forbidden_basenames), case-insensitive.
        self.assertEqual(deploy.prohibited_executables(root),
                         ["/usr/bin/LimeGUI", "/usr/bin/bt_test", "/usr/bin/rigctld", "/usr/bin/rotctld", "/usr/bin/rtl_biast",
                          "/usr/bin/rtl_tcp", "/usr/bin/wifi_test", "/usr/sbin/RTL_EEPROM"])
        policy = deploy.load(HERE / "receive-only-policy.json")
        self.assertEqual(deploy.forbidden_basenames(), {n.lower() for n in deploy.PROHIBITED_EXECUTABLES | deploy.BAD_NAMES}
                         | {e["name"].lower() for e in policy["forbidden_basenames"]})

    def test_bundle_is_deterministic_and_changed_stage_rejected(self):
        staging = self.root / "staging"
        (staging / "rootfs/opt/example").mkdir(parents=True)
        target = staging / "rootfs/opt/example/file.txt"
        target.write_text("deterministic synthetic bundle fixture\n")
        (staging / "stage-files.json").write_text(json.dumps({"schema_version": 1, "status": "STAGED_ONLY",
            "files": {"opt/example/file.txt": deploy.sha(target)}}))
        first = deploy.bundle(staging, self.root / "first.tar.gz")
        second = deploy.bundle(staging, self.root / "second.tar.gz")
        self.assertEqual(first["sha256"], second["sha256"])
        target.write_text("changed")
        with self.assertRaises(deploy.DeploymentError):
            deploy.bundle(staging, self.root / "third.tar.gz")

    def test_stage_rejects_live_prefix_and_symlink_escape(self):
        with self.assertRaises(deploy.DeploymentError):
            deploy.stage("/etc/srrx-unit-test-never-created")
        (self.root / "link").symlink_to("/etc", target_is_directory=True)
        with self.assertRaises(deploy.DeploymentError):
            deploy.stage(self.root / "link/srrx-unit-test-never-created")

    def test_hashes_stream_instead_of_reading_whole_files(self):
        target = self.root / "image.bin"
        target.write_bytes(os.urandom(3 * 1024 * 1024 + 7))
        expected = hashlib.sha256(target.read_bytes()).hexdigest()
        with patch.object(Path, "read_bytes", side_effect=AssertionError("whole-file read inside MemoryMax unit")):
            self.assertEqual(deploy.sha(target), expected)
            self.assertEqual(vendor_patch.digest(target), expected)

    def test_guard_process_writes_no_bytecode_into_verified_tree(self):
        env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
        # run_path compiles deploy.py without caching it, like the ExecStartPre script run.
        out = subprocess.run([sys.executable, "-c", "import runpy, sys; runpy.run_path(sys.argv[1]); print(sys.dont_write_bytecode)", str(HERE / "deploy.py")],
                             env=env, capture_output=True, text=True, check=True)
        self.assertEqual(out.stdout.strip(), "True")

    def test_cache_null_hash_cannot_be_treated_as_verified(self):
        synthetic_lock = copy.deepcopy(deploy.load(HERE / "sources.lock.json"))
        next(c for c in synthetic_lock["components"] if c["id"] == "rtlsdr")["source_archive_sha256"] = None
        with patch.object(deploy, "load", return_value=synthetic_lock):
            with self.assertRaisesRegex(deploy.DeploymentError, "SHA256 unresolved"):
                deploy.verify_cache(self.root, ["rtlsdr"], include_core=False)
        with self.assertRaises(deploy.DeploymentError):
            deploy.verify_cache(self.root, ["made-up-package"])

    def build_fixture(self):
        prefix = self.root / "build"
        prefix.mkdir()
        (prefix / "lib").mkdir()
        (prefix / "lib/rx.so").write_bytes(b"synthetic receive-only test fixture")
        (prefix / "audit.txt").write_text("Synthetic validator fixture; not a real native API audit.\n")
        (prefix / "tx-tests.txt").write_text("Synthetic validator fixture; not conducted hardware evidence.\n")
        report = lambda n: {"status": "PASS", "report": {"path": n, "sha256": deploy.sha(prefix / n)}}
        manifest = {"schema_version": 1, "status": "REVIEWED",
                    "files": {p.relative_to(prefix).as_posix(): deploy.sha(p) for p in prefix.rglob("*") if p.is_file()},
                    "allowed_modules": ["lib/rx.so"], "source_audit": report("audit.txt"),
                    "tx_negative_tests": report("tx-tests.txt")}
        return prefix, manifest

    def test_build_exact_allowlist_and_extra_tx_module_rejected(self):
        prefix, manifest = self.build_fixture()
        self.assertEqual(deploy.verify_build(prefix, manifest)["status"], "REVIEWED_BUILD_FILES_MATCH")
        (prefix / "lib/unreviewed.so").write_bytes(b"extra")
        with self.assertRaises(deploy.DeploymentError):
            deploy.verify_build(prefix, manifest)
        (prefix / "lib/unreviewed.so").unlink()
        (prefix / "lib/SoapySDRRemote.so").write_bytes(b"TX-capable fixture")
        manifest["files"]["lib/SoapySDRRemote.so"] = deploy.sha(prefix / "lib/SoapySDRRemote.so")
        manifest["allowed_modules"].append("lib/SoapySDRRemote.so")
        with self.assertRaises(deploy.DeploymentError):
            deploy.verify_build(prefix, manifest)

    def rehash(self, prefix, manifest):
        """Reviewer procedure: hash regular files, record internal directory links."""
        files = {}
        for p in sorted(prefix.rglob("*")):
            if p.is_symlink() and p.is_dir():
                files[p.relative_to(prefix).as_posix()] = "symlink:" + p.resolve().relative_to(prefix.resolve()).as_posix()
            elif p.is_file():
                files[p.relative_to(prefix).as_posix()] = deploy.sha(p)
        modules = sorted(k for k, v in files.items() if ".so" in k.rsplit("/", 1)[-1] and not v.startswith("symlink:"))
        return dict(manifest, files=files, allowed_modules=modules)

    def symlink(self, link, target):
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as exc:  # unprivileged Windows host
            self.skipTest("symlinks unavailable: " + str(exc))

    def test_directory_symlinks_are_checked_not_skipped(self):
        prefix, manifest = self.build_fixture()
        outside = self.root / "outside/modules0.8"
        outside.mkdir(parents=True)
        (outside / "libremoteSupport.so").write_bytes(b"unreviewed TX-capable plugin fixture")
        self.symlink(prefix / "lib/modules0.8", outside)
        with self.assertRaisesRegex(deploy.DeploymentError, "external staged symlink"):
            deploy.verify_build(prefix, manifest)
        (prefix / "lib/modules0.8").unlink()
        (prefix / "lib/real").mkdir()
        (prefix / "lib/real/rx2.so").write_bytes(b"reviewed receive-only fixture")
        self.symlink(prefix / "lib64", prefix / "lib")
        reviewed = self.rehash(prefix, manifest)
        self.assertEqual(reviewed["files"]["lib64"], "symlink:lib")
        self.assertEqual(deploy.verify_build(prefix, reviewed)["status"], "REVIEWED_BUILD_FILES_MATCH")
        stale = dict(reviewed, files={k: v for k, v in reviewed["files"].items() if k != "lib64"})
        with self.assertRaisesRegex(deploy.DeploymentError, "unknown files rejected"):
            deploy.verify_build(prefix, stale)
        self.symlink(prefix / "lib/channeltx", prefix / "lib/real")
        with self.assertRaisesRegex(deploy.DeploymentError, "prohibited"):
            deploy.verify_build(prefix, self.rehash(prefix, manifest))

    def test_documented_copies_venv_passes_and_symlinked_venv_is_rejected(self):
        import venv
        prefix, manifest = self.build_fixture()
        venv.EnvBuilder(symlinks=False, with_pip=False).create(prefix / "venv")
        documented = (deploy.PROJECT / "software/DEPLOYMENT.md").read_text(encoding="utf-8")
        self.assertTrue("python3 -m venv --copies /opt/srrx/venv" in documented, "DEPLOYMENT.md must create a --copies venv")
        self.assertEqual(deploy.verify_build(prefix, self.rehash(prefix, manifest))["status"], "REVIEWED_BUILD_FILES_MATCH")
        if os.name != "posix":
            self.skipTest("default venv interpreter symlinks are POSIX-only")
        shutil.rmtree(prefix / "venv")
        venv.EnvBuilder(symlinks=True, with_pip=False).create(prefix / "venv")
        with self.assertRaisesRegex(deploy.DeploymentError, "external staged symlink"):
            deploy.verify_build(prefix, self.rehash(prefix, manifest))

    def test_lime_cannot_be_released_by_an_allowlist_entry(self):
        prefix, manifest = self.build_fixture()
        target = prefix / "lib/liblimesuiteng.so"
        target.write_bytes(b"synthetic SDK")
        manifest["files"]["lib/liblimesuiteng.so"] = deploy.sha(target)
        manifest["allowed_modules"].append("lib/liblimesuiteng.so")
        with self.assertRaisesRegex(deploy.DeploymentError, "experimental"):
            deploy.verify_build(prefix, manifest)

    def test_ab_candidates_only_and_no_duplicate_roots(self):
        config = deploy.load(HERE / "ab.template.json")
        with self.assertRaises(deploy.DeploymentError):
            deploy.stage_ab(config, self.root / "invalid-ab")
        # The full STACK base line shape (build/07 §4); '@' of the video= addition must pass (IMG-03).
        config.update(esp_partuuid="00000000-0000-4000-8000-000000000001",
                      root_a_partuuid="11111111-1111-1111-1111-111111111111",
                      root_b_partuuid="22222222-2222-2222-2222-222222222222", trial_slot="B",
                      base_cmdline_without_root="console=ttyMSM0,115200n8 rw earlycon consoleblank=0 console=tty1 coherent_pool=2M "
                                                "irqchip.gicv3_pseudo_nmi=0 cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory swapaccount=1 kasan=off",
                      rescue={"kernel": "/RadxaOS/6.18.2-3-qcom/linux", "initrd": "/RadxaOS/6.18.2-3-qcom/initrd.img-6.18.2-3-qcom", "dtb": None})
        result = deploy.stage_ab(config, self.root / "ab")
        self.assertFalse(result["active_slot_changed"])
        self.assertEqual(result["next_boot_slot"], "B")
        trial = (self.root / "ab/loader/entries/labB+3.conf").read_text()
        self.assertIn("initrd /srrx/B/initrd.img", trial)
        self.assertIn("devicetree /srrx/B/lab.dtb", trial)
        self.assertIn(" video=HDMI-A-1:1920x1080@60 ", trial)
        self.assertIn("root=PARTUUID=22222222-2222-2222-2222-222222222222", trial)
        active = (self.root / "ab/loader/entries/labA.conf").read_text()
        self.assertIn("linux /srrx/A/linux", active)
        self.assertNotIn("/srrx/B/", active)  # schema 2: no kernel/initrd/DTB shared between slots
        self.assertEqual((self.root / "ab/loader/loader.conf").read_text(), "default lab*\ntimeout 3\neditor no\n")
        field = dict(config, dt_profile="field", trial_slot=None)
        deploy.stage_ab(field, self.root / "ab-field")
        self.assertIn("devicetree /srrx/A/field.dtb", (self.root / "ab-field/loader/entries/labA.conf").read_text())
        shared = copy.deepcopy(config)
        shared["slots"]["B"]["kernel"] = "/srrx/A/linux"
        with self.assertRaises(deploy.DeploymentError):
            deploy.stage_ab(shared, self.root / "ab-shared")
        legacy = {"schema_version": 1}
        with self.assertRaisesRegex(deploy.DeploymentError, "schema_version 1"):
            deploy.stage_ab(legacy, self.root / "ab-legacy")
        config["root_b_partuuid"] = config["root_a_partuuid"]
        with self.assertRaises(deploy.DeploymentError):
            deploy.stage_ab(config, self.root / "ab2")

    def test_doctor_uses_read_only_commands(self):
        called = []
        def read_only(args, **kwargs):
            called.append(args)
            return {"returncode": 0, "stdout": "", "stderr": ""}
        with patch.object(deploy, "command", read_only):
            result = deploy.doctor()
        self.assertTrue(result["read_only"])
        self.assertFalse(result["hardware_ready"])
        self.assertTrue(all(args[0] in {"dpkg-query", "lsblk"} for args in called))

    def test_oversized_command_output_fails_closed_instead_of_truncating(self):
        big = subprocess.CompletedProcess(["x"], 0, "a\tb\tinstalled\n" * 20_000, "")
        with patch.object(deploy.subprocess, "run", return_value=big):
            self.assertEqual(deploy.command(["x"])["returncode"], -2)
            self.assertEqual(deploy.command(["x"], limit=len(big.stdout))["stdout"], big.stdout)

    def test_doctor_reads_whole_inventory_and_unpacked_prohibited_packages(self):
        requirements = deploy.load(HERE / "dependencies.json")["required_target_packages"]
        rows = ["filler-%05d\t1.0\tinstalled" % i for i in range(4000)]  # > 100 kB before the late names
        rows += ["%s\t%s\tinstalled" % (name, versions[0]) for name, versions in requirements.items()]
        rows += ["urh\t2.9\tunpacked", "wsjtx:arm64\t2.6\thalf-configured", "qsstv\t9.5\tconfig-files"]
        inventory = "\n".join(sorted(rows)) + "\n"
        self.assertGreater(len(inventory), 100_000)
        def listing(args, limit=100_000):
            out = inventory if args[0] == "dpkg-query" else ""
            if len(out) > limit:
                return {"returncode": -2, "error": "output exceeds bound", "stdout": "", "stderr": ""}
            return {"returncode": 0, "stdout": out, "stderr": ""}
        with patch.object(deploy, "command", listing):
            issues = deploy.doctor()["issues"]
        self.assertNotIn("installed package inventory unavailable", issues)
        self.assertFalse([i for i in issues if i.startswith("missing/different pinned package")])
        self.assertIn("prohibited packages installed: urh,wsjtx", issues)

    def test_doctor_forbidden_packages_are_the_receive_only_policy(self):
        policy = deploy.load(HERE / "receive-only-policy.json")["forbidden_packages"]
        unconditional = [p for p in policy if p["check"] == "presence" and "version_rule" not in p]
        names, globs = deploy.prohibited_packages()
        self.assertEqual(names, {p["name"] for p in unconditional if "name" in p})
        self.assertEqual(globs, {p["glob"] for p in unconditional if "glob" in p})
        # Nothing doctor blocked with its former own list is lost.
        self.assertLessEqual({"wsjtx", "fldigi", "qsstv", "direwolf", "urh", "soapysdr-module-all", "soapysdr0.8-module-all",
                              "soapysdr0.8-module-remote", "limesuiteng-gui", "gr-limesuiteng", "libhamlib-utils"}, names)
        requirements = deploy.load(HERE / "dependencies.json")["required_target_packages"]
        rows = ["%s\t%s\tinstalled" % (name, versions[0]) for name, versions in requirements.items()]
        rows += ["%s:arm64\t1.0-1\tunpacked" % name for name in sorted(names)]
        # Glob hits and version rules (doctor applies them as RX-01a does); pin_only entries are RX-01a BLOCKED findings only.
        rows += ["digiham-tools\t1.0\tinstalled", "linux-image-7.0.0-1-qcom\t7.0.0-1\thalf-configured", "librtlsdr2\t2.0.3-0+lab1\tinstalled",
                 "gpredict\t2.3-115-g0f3beb6-3build3\tinstalled", "qcom-fastrpc1\t1.0\tinstalled", "libqnn1\t2.40\tinstalled",
                 "codecserver\t0.2\tconfig-files"]
        inventory = "\n".join(rows) + "\n"
        def run(policy_path=None):
            listing = lambda args, limit=100_000: {"returncode": 0, "stdout": inventory if args[0] == "dpkg-query" else "", "stderr": ""}
            with patch.object(deploy, "command", listing), patch.object(deploy, "POLICY", policy_path or deploy.POLICY):
                return deploy.doctor()
        report = run()
        issue = [i for i in report["issues"] if i.startswith("prohibited packages installed: ")]
        self.assertEqual(len(issue), 1)
        reported = set(issue[0].split(": ", 1)[1].split(","))
        self.assertLessEqual(names | {"digiham*", "linux-image-7.*"}, reported)
        self.assertFalse(reported & {"librtlsdr2", "gpredict", "qcom-fastrpc*", "libqnn*", "codecserver*"}, reported)
        listed = [r.split("\t") for r in rows if not r.endswith("config-files")]
        # Version rules come from the same policy entries (identifier + VERSION_NOTE): no doctor-only list remains.
        ruled = [p for p in policy if p["check"] == "presence" and "version_rule" in p]
        versioned = {(p.get("name") or p["glob"]) + deploy.VERSION_NOTE for p in ruled for n, v, _ in listed
                     if (n.split(":")[0] == p["name"] if "name" in p else fnmatch.fnmatchcase(n.split(":")[0], p["glob"]))
                     and deploy.version_forbidden(p["version_rule"], v)}
        self.assertEqual(versioned, {"gpredict" + deploy.VERSION_NOTE})  # librtlsdr2 2.0.3-0+lab1 is the allowed build
        self.assertEqual(reported - names - versioned, {g for g in globs if any(fnmatch.fnmatchcase(n.split(":")[0], g) for n, _, _ in listed)})
        self.assertLessEqual(set(deploy.PROHIBITED_PACKAGES), names)  # one denylist source
        self.assertLessEqual(set(deploy.PROHIBITED_PACKAGE_GLOBS), globs)
        self.assertNotIn("digiham-tools", issue[0])  # policy identifiers only, never dpkg text
        self.assertEqual(report["status"], "BLOCKED")
        # Strict bounded JSON: a broken policy is a doctor issue (BLOCKED), never an empty forbidden set.
        text = (HERE / "receive-only-policy.json").read_text(encoding="utf-8")
        for label, broken in (("duplicate", text.replace('"status": "DRAFT",', '"status": "DRAFT", "status": "DRAFT",', 1)),
                              ("nonfinite", text.replace('"schema_version": 1', '"schema_version": NaN', 1)),
                              ("empty", json.dumps({"forbidden_packages": []})), ("not-object", "[]"),
                              ("entry", json.dumps({"forbidden_packages": [{"name": "", "check": "presence"}]})),
                              ("oversized", " " * (4 * 1024 * 1024) + "{}")):
            path = self.root / ("policy-" + label + ".json")
            path.write_text(broken, encoding="utf-8")
            self.assertNotEqual(path.read_text(encoding="utf-8"), text)
            with self.subTest(policy=label):
                report = run(path)
                self.assertTrue(any(i.startswith("receive-only policy unavailable: ") for i in report["issues"]), report["issues"])
                self.assertEqual(report["status"], "BLOCKED")
                with self.assertRaises(deploy.DeploymentError):
                    deploy.prohibited_packages(path)
        with patch.object(deploy, "POLICY", self.root / "policy-entry.json"), self.assertRaises(deploy.DeploymentError):
            deploy.check()  # build.sh --check refuses a broken policy before it ships

    def test_full_plan_orbit_wheels_equal_the_locked_wheelhouse(self):
        plan = deploy.load(HERE / "dependencies.json")["python_full_plan_constraints"]
        locked = {w["name"]: w for w in deploy.load(HERE / "linux_lab/wheelhouse-manifest.json")["wheels"]}
        recorded = plan["aarch64_locked_wheels"]
        self.assertEqual(set(recorded) - {"source"}, {"skyfield", "sgp4", "jplephem", "certifi"})
        for name, record in recorded.items():
            if name != "source":
                self.assertEqual(record, {k: locked[name][k] for k in ("version", "filename", "sha256")}, name)
        self.assertEqual((plan["skyfield"], plan["sgp4"]), (recorded["skyfield"]["version"], recorded["sgp4"]["version"]))
        self.assertTrue(plan["status"].startswith("OPEN"))  # the lab-venv lock (numpy<2, GNU Radio) is still open


class VendorPatchTests(unittest.TestCase):
    def test_unknown_archive_bytes_are_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "untrusted.tar.gz"
            archive.write_bytes(b"not a pinned archive")
            with self.assertRaises(vendor_patch.PatchError):
                vendor_patch.apply_from_archive("limesuiteng", archive, Path(tmp) / "output")
            self.assertFalse((Path(tmp) / "output").exists())

    def test_exact_pinned_sources_apply_and_tampering_fails(self):
        receipts = vendor_patch.check_fixtures()
        self.assertEqual(len(receipts), 2)
        self.assertTrue(all(r["source_fixture_only"] and not r["release_ready"] for r in receipts))
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "source"
            shutil.copytree(HERE / "upstream-fixtures/rtl-sdr", fixture)
            with (fixture / "src/librtlsdr.c").open("a") as handle:
                handle.write("\n/* changed */\n")
            with self.assertRaises(vendor_patch.PatchError):
                vendor_patch.check_source("rtlsdr", fixture, fixture=True)

    def test_patch_bytes_do_not_depend_on_caller_git_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "hostile.gitconfig"
            config.write_text("[core]\n\tautocrlf = true\n\teol = crlf\n[apply]\n\twhitespace = fix\n")
            with patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(config), "GIT_CONFIG_NOSYSTEM": "1"}):
                receipts = vendor_patch.check_fixtures()
        self.assertEqual([r["component"] for r in receipts], ["rtlsdr", "limesuiteng"])

    @unittest.skipUnless(shutil.which("cc"), "host C compiler unavailable")
    def test_actual_inserted_rtl_guard_compiles_and_blocks_gpio0_on(self):
        signature = "int rtlsdr_set_bias_tee_gpio("
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vendor_patch.apply_to_copy("rtlsdr", HERE / "upstream-fixtures/rtl-sdr", root / "patched", fixture=True)
            guard = body((root / "patched/src/librtlsdr.c").read_text(), signature)
            upstream = body((HERE / "upstream-fixtures/rtl-sdr/src/librtlsdr.c").read_text(), signature)
            # Stubs keep upstream's uint8_t GPIO parameters: an int such as 256 wraps to GPIO0, the bias tee.
            code = ('#include <assert.h>\n#include <errno.h>\n#include <limits.h>\n#include <stddef.h>\n#include <stdint.h>\n'
                    'typedef struct {int unused;} rtlsdr_dev_t; static unsigned gpo, gpoe;\n'
                    'static unsigned mask(uint8_t gpio){return gpio < 8 ? 1u << gpio : 0;}\n'
                    'static void rtlsdr_set_gpio_output(rtlsdr_dev_t *dev, uint8_t gpio){(void)dev; gpoe |= mask(gpio);}\n'
                    'static void rtlsdr_set_gpio_bit(rtlsdr_dev_t *dev, uint8_t gpio, int val){(void)dev; gpo = val ? (gpo | mask(gpio)) : (gpo & ~mask(gpio));}\n'
                    'static int patched(rtlsdr_dev_t *dev, int gpio, int on){' + guard + '}\n'
                    'static int original(rtlsdr_dev_t *dev, int gpio, int on){' + upstream + '}\n'
                    'int main(void){rtlsdr_dev_t d = {0}; const int bad[] = {0, 256, -256, 512, 768, 65536, -1, 8, 255, INT_MIN, INT_MAX};\n'
                    'assert(original(&d, 256, 1) == 0 && (gpo & 1u));\n'
                    'for (size_t i = 0; i < sizeof bad / sizeof bad[0]; i++){gpo = gpoe = 0; assert(patched(&d, bad[i], 1) < 0); assert(gpo == 0 && gpoe == 0);}\n'
                    'assert(patched(&d, 0, 1) == -EPERM && patched(&d, 256, 1) == -EINVAL && patched(&d, -256, 0) == -EINVAL);\n'
                    'assert(patched(&d, 5, 1) == 0 && gpo == 0x20u && gpoe == 0x20u); assert(patched(&d, 5, 0) == 0 && gpo == 0);\n'
                    'gpo = 1; assert(patched(&d, 0, 0) == 0 && gpo == 0); assert(patched(NULL, 5, 1) == -1); return 0;}\n')
            source = root / "rtl_guard.c"
            source.write_text(code)
            subprocess.run(["cc", "-std=c99", "-Wall", "-Werror", str(source), "-o", str(root / "rtl_guard")], check=True, capture_output=True)
            subprocess.run([str(root / "rtl_guard")], check=True, capture_output=True)

    @unittest.skipUnless(shutil.which("g++"), "host C++ compiler unavailable")
    def test_actual_inserted_lime_guards_compile_and_reject_tx(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vendor_patch.apply_to_copy("limesuiteng", HERE / "upstream-fixtures/limesuiteng", root / "patched", fixture=True)
            streaming = (root / "patched/plugins/soapysdr/Streaming.cpp").read_text()
            micro = (root / "patched/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp").read_text()
            setup = body(streaming, "SoapySDR::Stream* Soapy_limesuiteng::setupStream(").split("std::unique_lock", 1)[0]
            native = body(micro, "std::unique_ptr<lime::RFStream> LimeSDR_Micro::StreamCreate(").split("if (!la9310", 1)[0]
            configure = body(micro, "OpStatus LimeSDR_Micro::Configure(").split("OpStatus status;", 1)[0]
            write = body(streaming, "int Soapy_limesuiteng::writeStream(")
            waveform = body(micro, "OpStatus LimeSDR_Micro::UploadTxWaveform(")
            calibrate = body(micro, "OpStatus LimeSDR_Micro::Calibrate(").split("mLMSChips", 1)[0]
            self.assertIn("TRXDir::Tx", calibrate)
            self.assertNotIn("StreamTx", write)
            self.assertNotIn("samples", waveform)
            code = ('#include <map>\n#include <vector>\n#include <stdexcept>\n#include <cassert>\n'
                    'constexpr int SOAPY_SDR_RX=1,SOAPY_SDR_TX=0,SOAPY_SDR_NOT_SUPPORTED=-5;\n'
                    'enum class TRXDir{Rx,Tx}; enum class OpStatus{Success,NotSupported};\n'
                    'struct Config{std::map<TRXDir,std::vector<int>> channels;};\n'
                    'struct Channel{struct{bool enabled=false;}tx;};struct SDRConfig{Channel channel[2];};\n'
                    'bool setup(int direction){' + setup + 'return true;}\n'
                    'void* stream(const Config& config){' + native + 'return (void*)1;}\n'
                    'OpStatus configure(const SDRConfig& cfg){' + configure + 'return OpStatus::Success;}\n'
                    'int write(){' + write + '}\nOpStatus waveform(){' + waveform + '}\n'
                    'OpStatus calibrate(TRXDir trx){' + calibrate + 'return OpStatus::Success;}\n'
                    'int main(){bool rejected=false;try{setup(SOAPY_SDR_TX);}catch(const std::runtime_error&){rejected=true;}'
                    'assert(rejected);assert(setup(SOAPY_SDR_RX));Config c;c.channels[TRXDir::Rx]={0};assert(stream(c));'
                    'c.channels[TRXDir::Tx]={0};assert(!stream(c));SDRConfig s;assert(configure(s)==OpStatus::Success);'
                    's.channel[1].tx.enabled=true;assert(configure(s)==OpStatus::NotSupported);'
                    'assert(write()==SOAPY_SDR_NOT_SUPPORTED);assert(waveform()==OpStatus::NotSupported);'
                    'assert(calibrate(TRXDir::Tx)==OpStatus::NotSupported);assert(calibrate(TRXDir::Rx)==OpStatus::Success);}')
            source = root / "guards.cpp"
            source.write_text(code)
            subprocess.run(["g++", "-std=c++20", "-Wall", "-Werror", str(source), "-o", str(root / "guards")], check=True, capture_output=True)
            subprocess.run([str(root / "guards")], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
