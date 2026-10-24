"""Synthetic temporary rootfs fixtures; no result here is hardware, image or release evidence."""
import contextlib
import fnmatch
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import deploy
import selftest

POLICY = HERE / "receive-only-policy.json"
FAKE_ELF = selftest.ELF_MAGIC + b"\x02\x01\x01" + b"\0" * 57
GOOD_SIG = (0, "[GNUPG:] NEWSIG\n[GNUPG:] GOODSIG 0123456789ABCDEF fixture\n[GNUPG:] VALIDSIG 0123456789ABCDEF0123456789ABCDEF01234567 2026-10-01\n")
SECRET = "PLANTED-SECRET-c0ffee-41d7"
RTL_EXPORTS = ["rtlsdr_fixture_%02d" % i for i in range(37)]


def readelf(soname=None, needed=(), exports=(), header_symbols=None):
    """Text in the exact `readelf -d --dyn-syms -W` layout parsed by selftest.elf_dynamic."""
    rows = [" 0x0000000000000001 (NEEDED)             Shared library: [%s]" % n for n in needed]
    if soname:
        rows.append(" 0x000000000000000e (SONAME)             Library soname: [%s]" % soname)
    rows.append(" 0x0000000000000000 (NULL)               0x0")
    symbols = ["     0: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT  UND ",
               "     1: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND libusb_open@LIBUSB_1.0 (2)",
               "     2: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND rtlsdr_undefined_import"]
    symbols += ["  %4d: 0000000000001000    16 FUNC    GLOBAL DEFAULT   12 %s" % (i + 3, name) for i, name in enumerate(exports)]
    count = len(symbols) if header_symbols is None else header_symbols
    return ("\nDynamic section at offset 0x2dd8 contains %d entries:\n  Tag        Type                         Name/Value\n" % len(rows)
            + "\n".join(rows) + "\n\nSymbol table '.dynsym' contains %d entries:\n" % count
            + "   Num:    Value          Size Type    Bind   Vis      Ndx Name\n" + "\n".join(symbols) + "\n")


class FakeTools:
    """Injected readelf/gpgv runner; records every bounded call, never starts a process."""
    def __init__(self, outputs=None, gpgv=GOOD_SIG):
        self.outputs, self.gpgv, self.calls = dict(outputs or {}), gpgv, []

    def __call__(self, args, timeout, limit):
        assert 0 < timeout <= 60 and 0 < limit <= 64 * 1024 * 1024
        self.calls.append(list(args))
        if args[0] == "gpgv":
            return self.gpgv
        value = self.outputs.get(Path(args[-1]).name)
        return value if value is None or isinstance(value, tuple) else (0, value)


LOCKED = {"allow_center_freq_changes": False, "allow_audio_recording": False, "allow_chat": False, "speech_url": "",
          "mqtt_enabled": False, "rig_enabled": False, "pskreporter_enabled": False, "wsprnet_enabled": False}


def devices():
    """Synthetic device bindings (as test_deployment): the stage then carries the FE1.1s port-4 rule."""
    config = deploy.load(HERE / "devices.template.json")
    config["i2c"]["ina228"] = {"path": "/dev/i2c-7", "of_fullname": "/soc@0/test-ina228"}
    config["i2c"]["control"] = {"path": "/dev/i2c-9", "of_fullname": "/soc@0/test-control"}
    config["pico"]["kernel_parent"] = "99c000.serial"
    config["usb"]["hfplus"]["serial"] = "AIRSPYHF SN:0123456789ABCDEF"
    config["wifi_bt"]["fe11s_port4_usb_path"] = "1-1.4"
    return config


class SelftestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="srrx-selftest-test-")
        cls.root = Path(cls.temp.name)
        deploy.stage(cls.root / "stage", devices())
        cls.clean = cls.root / "stage/rootfs"
        (cls.clean / "etc/kernel").mkdir(parents=True)
        (cls.clean / "etc/kernel/cmdline").write_text("console=ttyMSM0,115200n8 rw earlycon consoleblank=0 root=PARTUUID=11111111-1111-1111-1111-111111111111\n")
        cls.cmdline = deploy.sha(cls.clean / "etc/kernel/cmdline")
        reviewed = deploy.load(POLICY)
        reviewed["status"] = "REVIEWED"  # synthetic copy: exercises the pass path of the validator only
        cls.reviewed = cls.root / "reviewed-policy.json"
        cls.reviewed.write_text(json.dumps(reviewed, indent=2) + "\n", encoding="utf-8")
        cls.baseline = {}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        # Loops call setUp() again for a fresh copy: only one staged copy exists at a time, and the
        # last one is removed when the test ends (each copy is several MB).
        if getattr(self, "work", None) is None:
            self.addCleanup(lambda: shutil.rmtree(self.work, ignore_errors=True))
        else:
            shutil.rmtree(self.work, ignore_errors=True)
        self.work = Path(tempfile.mkdtemp(prefix="case-", dir=self.root))
        self.rootfs = self.work / "rootfs"
        shutil.copytree(self.clean, self.rootfs, symlinks=True)

    def put(self, rel, data, rootfs=None):
        path = (rootfs or self.rootfs) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
        path.write_bytes(data.encode() if isinstance(data, str) else data)
        return path

    def symlink(self, link, target):
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(target, link)
        except OSError as exc:  # unprivileged Windows host only; Linux CI always creates links
            self.skipTest("symlinks unavailable: " + str(exc))

    def run_check(self, profile="controller", rootfs=None, policy=None, allow_pass=False, **kwargs):
        kwargs.setdefault("cmdline_sha256", self.cmdline)
        report = selftest.run_offline(rootfs or self.rootfs, profile, policy or self.reviewed, **kwargs)
        # Invariants of every report: no hardware claim, no PASS outside OFFLINE evidence.
        self.assertFalse(report["hardware_ready"])
        self.assertFalse(report["receive_only_proven"])
        if not allow_pass:  # honest today: rows 11 and 14 have no code
            self.assertNotEqual(report["status"], "OFFLINE_CHECKS_PASS")
        for check in report["checks"]:
            if check["evaluability"] in ("BUILDER", "DEVICE", "HARDWARE"):
                self.assertEqual(check["status"], "RUNTIME_ONLY", check["id"])
            elif check["evaluability"] == "NOT_IMPLEMENTED":
                self.assertEqual(check["status"], "BLOCKED", check["id"])
            for finding in check["findings"]:
                self.assertEqual(set(finding) - {"item"}, {"path", "rule", "effect"})
                self.assertFalse(os.path.isabs(finding["path"]), finding)
        self.assertEqual(sum(report["counts"].values()), len(selftest.CATALOGUE))
        return report

    @staticmethod
    def statuses(report):
        return {c["id"]: c["status"] for c in report["checks"]}

    @staticmethod
    def check(report, check_id):
        return next(c for c in report["checks"] if c["id"] == check_id)

    def base(self, profile):
        if profile not in self.baseline:
            type(self).baseline[profile] = self.statuses(self.run_check(profile, rootfs=self.clean))
        return self.baseline[profile]

    def assert_flips(self, check_id, rule, profile="controller", expected="FAIL", **kwargs):
        report = self.run_check(profile, **kwargs)
        changed = {k for k, v in self.statuses(report).items() if v != self.base(profile)[k]}
        self.assertEqual(changed, {check_id}, [self.check(report, k) for k in changed])
        result = self.check(report, check_id)
        self.assertEqual(result["status"], expected)
        self.assertIn(rule, {f["rule"] for f in result["findings"]}, result)
        return report

    # ------------------------------------------------------------ catalogue and honest baseline

    def test_catalogue_covers_every_build07_row_and_cli_prints_it(self):
        rows = {row for _, row, _, _, _ in selftest.CATALOGUE if row}
        self.assertEqual(rows, set(range(1, 19)))
        ids = [entry[0] for entry in selftest.CATALOGUE]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("RX-S1", ids)
        for check_id, row, evaluability, _, sources in selftest.CATALOGUE:
            self.assertIn(evaluability, ("OFFLINE", "BUILDER", "DEVICE", "HARDWARE", "NOT_IMPLEMENTED"))
            # Every OFFLINE row has real code; runtime rows have none that could emit a PASS.
            self.assertEqual(check_id in selftest.CHECKS, evaluability in ("OFFLINE", "NOT_IMPLEMENTED"), check_id)
            self.assertTrue(sources)
        for check_id in ("RX-11", "RX-14"):
            self.assertEqual(next(e[2] for e in selftest.CATALOGUE if e[0] == check_id), "NOT_IMPLEMENTED")
        out = subprocess.run([sys.executable, str(HERE / "selftest.py"), "catalogue"], capture_output=True, text=True, check=True)
        self.assertEqual([c["id"] for c in json.loads(out.stdout)], ids)

    def test_clean_staged_tree_passes_offline_rows_but_stays_blocked(self):
        report = self.run_check(rootfs=self.clean)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["blockers"], ["RX-11", "RX-14"])  # honest today: no menu model, no voice mask
        self.assertEqual(report["policy_status"], "REVIEWED")
        for check in report["checks"]:
            if check["evaluability"] == "OFFLINE":
                self.assertEqual(check["status"], "PASS", check)
        self.assertTrue(report["target"]["inventory_complete"])
        self.assertGreater(report["target"]["files_scanned"], 50)
        self.assertEqual(report["tool_sha256"], deploy.sha(HERE / "selftest.py"))
        self.assertEqual(report["source_lock_sha256"], deploy.sha(HERE / "sources.lock.json"))
        self.assertEqual(report["policy_sha256"], deploy.sha(self.reviewed))
        # The verdict also depends on deploy.py and on the checker's own srrx modules that ran.
        dependencies = report["tool_dependencies"]
        self.assertEqual(dependencies["deployment/deploy.py"], deploy.sha(HERE / "deploy.py"))
        for name in set(selftest.srrx_closure("learning")) | set(selftest.srrx_closure("decoder_policy")):
            rel = "software/srrx/%s.py" % name
            self.assertEqual(dependencies[rel], deploy.sha(deploy.PROJECT / rel), rel)
        again = self.run_check(rootfs=self.clean)
        self.assertEqual(again["target"]["inventory_sha256"], report["target"]["inventory_sha256"])
        self.assertIn("dpkg_database_absent_controller_overlay", self.check(report, "RX-01a")["notes"])
        # The staged radio-off layers pass statically; their live effect is the RUNTIME_ONLY row.
        self.assertIn("live_rfkill_and_usb_state_is_RX-S2-runtime", self.check(report, "RX-S2")["notes"])
        self.assertEqual(self.check(report, "RX-S2-runtime")["status"], "RUNTIME_ONLY")
        self.assertEqual(dependencies["software/srrx/rfkill.py"], deploy.sha(deploy.PROJECT / "software/srrx/rfkill.py"))

    def test_repeated_setup_keeps_one_staged_copy_and_cleanup_removes_it(self):
        first = self.work
        self.setUp()  # as the loops below do
        self.assertFalse(first.exists())
        self.assertEqual([p for p in self.root.iterdir() if p.name.startswith("case-")], [self.work])
        self.doCleanups()  # what unittest runs after every test
        self.assertFalse(self.work.exists())
        self.assertEqual([p for p in self.root.iterdir() if p.name.startswith("case-")], [])

    def test_shipped_policy_is_draft_and_blocks(self):
        self.assertEqual(selftest.load_policy(POLICY)["status"], "DRAFT")
        report = self.run_check(rootfs=self.clean, policy=POLICY)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["policy_status"], "DRAFT")
        self.assertEqual(report["blockers"][0], "POLICY_NOT_REVIEWED")
        # A DRAFT policy never hides a found violation.
        self.put("usr/bin/rigctld", "#!/bin/sh\n")
        self.assertEqual(self.run_check(policy=POLICY)["status"], "FAIL")

    def test_missing_cmdline_record_blocks_and_full_profile_requires_components(self):
        report = self.run_check(rootfs=self.clean, cmdline_sha256=None)
        self.assertEqual(self.check(report, "RX-17")["status"], "BLOCKED")
        full = self.run_check("full", rootfs=self.clean)
        self.assertEqual(full["status"], "BLOCKED")
        expect = {"RX-01a": "dpkg_database_missing", "RX-02": "component_not_found", "RX-03": "component_not_found",
                  "RX-04": "component_not_found", "RX-05": "component_not_found", "RX-06": "component_not_found",
                  "RX-09": "librtlsdr_missing", "RX-10": "component_not_found", "RX-12": "lease_units_not_found",
                  "RX-16": "apt_configuration_missing"}
        for check_id, rule in expect.items():
            check = self.check(full, check_id)
            self.assertEqual(check["status"], "BLOCKED", check)
            self.assertIn(rule, {f["rule"] for f in check["findings"]})

    # ------------------------------------------------------------ injected failures

    def test_injected_failures_flip_exactly_their_check(self):
        cases = [
            ("RX-01b", "forbidden_basename", lambda: self.put("usr/bin/rigctld", "#!/bin/sh\n")),
            ("RX-01b", "forbidden_basename", lambda: self.put("usr/bin/limeGUI", "x")),
            ("RX-01b", "forbidden_suffix", lambda: self.put("opt/apps/receiver.AppImage", "x")),
            ("RX-01b", "forbidden_path", lambda: self.put("var/lib/snapd/state.json", "{}")),
            ("RX-01b", "dream_transmitter_strings", lambda: self.put("usr/bin/dream", b"synthetic CDRMTransmitter fixture")),
            ("RX-07", "amarisoft_module", lambda: self.put("usr/lib/aarch64-linux-gnu/libamarisoft_x.so", "x")),
            ("RX-06", "module_not_allowlisted", lambda: self.put("usr/lib/aarch64-linux-gnu/SoapySDR/modules0.8/libremoteSupport.so", "x")),
            ("RX-06", "lime_module_while_lime_disabled", lambda: self.put("usr/lib/aarch64-linux-gnu/SoapySDR/modules0.8/libLimeSuiteNGSupport.so", "x")),
            ("RX-06", "soapy_0_9_modules", lambda: self.put("usr/lib/aarch64-linux-gnu/SoapySDR/modules0.9-2/librtlsdrSupport.so", "x")),
            ("RX-06", "soapy_plugin_path_override", lambda: self.put("etc/environment", "SOAPY_SDR_PLUGIN_PATH=/opt/x\n")),
            ("RX-08", "lime_runtime_library", lambda: self.put("usr/lib/aarch64-linux-gnu/liblimesuiteng.so.24", "x")),
            ("RX-03", "forbidden_module", lambda: self.put("usr/lib/sdrpp/plugins/recorder.so", "x")),
            ("RX-03", "sdrpp_server_launcher", lambda: self.put("etc/systemd/system/sdrpp.service", "[Service]\nExecStart=/usr/bin/sdrpp --server\n")),
            ("RX-02", "radio_application_in_controller_profile", lambda: self.put("usr/lib/sdrangel/plugins/libdemodam.so", "x")),
            ("RX-04", "pipeline_not_allowlisted", lambda: self.put("usr/share/satdump/pipelines/GOES.json", {"goes_gvar": {"name": "GOES"}})),
            ("RX-04", "pipeline_include_forbidden", lambda: self.put("usr/share/satdump/pipelines/x.json.inc", "{}")),
            ("RX-04", "kepler_update_not_never", lambda: self.put("usr/share/satdump/satdump_cfg.json", {"satdump_general": {"kepler_update_interval": {"value": "Daily"}}})),
            ("RX-04", "user_pipelines_json", lambda: self.put("var/lib/lab/satdump/pipelines.json", "{}")),
            ("RX-05", "mode_denied", lambda: self.put("usr/lib/python3/dist-packages/owrx/modes.py",
                                                    'class Modes:\n    mappings = [AnalogMode("nfm", "FM"), DigitalMode("tetra", "TETRA")]\n')),
            ("RX-05", "locked_setting", lambda: self.put("var/lib/openwebrx/settings.json", dict(LOCKED, allow_chat=True))),
            ("RX-01c", "direct_sampling_key", lambda: self.put("home/lab/.config/sdrpp/rtl_sdr_config.json", {"devices": {"LABRXA": {"direct_sampling": 2}}})),
            ("RX-01c", "direct_sampling_nonzero", lambda: self.put("home/lab/.config/sdrpp/rtl_sdr_config.json", {"devices": {"LABRXA": {"directSamplingMode": 1}}})),
            ("RX-01c", "bias_key", lambda: self.put("etc/SoapySDR/rtl.conf", "[rtlsdr]\nbiastee = 0\n")),
            ("RX-01c", "hfplus_rate_256000", lambda: self.put("etc/openwebrx/openwebrx.conf", "[hfplus]\nsamp_rate = 256000\n")),
            ("RX-01a", "forbidden_package", lambda: self.put("var/lib/dpkg/status", "Package: direwolf\nStatus: install ok unpacked\nVersion: 1.7-1\n\nPackage: bash\nStatus: install ok installed\nVersion: 5.2.21-2ubuntu4\n")),
            ("RX-01a", "forbidden_package", lambda: self.put("var/lib/dpkg/status", "Package: librtlsdr2\nStatus: install ok installed\nVersion: 2.0.1-2build1\n")),
            ("RX-01a", "forbidden_package", lambda: self.put("var/lib/dpkg/status", "Package: dream\nStatus: install ok installed\nVersion: 2.1.1-3\n")),
            ("RX-16", "apt_forbidden_origin", lambda: self.put("etc/apt/sources.list.d/extra.list", "deb http://ppa.launchpadcontent.net/x/y/ubuntu noble main\n")),
            ("RX-16", "rsdk_ppa_list_present", lambda: self.put("etc/apt/sources.list.d/ubuntu-qcom-iot-ubuntu-qcom-ppa-noble.list", "# disabled\n")),
            ("RX-16", "lab_pref_structure", lambda: self.put("etc/apt/preferences.d/lab.pref", "Package: *\nPin: release o=lab\nPin-Priority: 1001\n\nPackage: *\nPin: origin *\nPin-Priority: 500\n")),
            ("RX-16", "dpkg_verify_mismatch", self.inject_md5_mismatch),
            ("RX-10", "radio_type_not_rx_only", lambda: self.put("home/lab/.config/Gpredict/radios/trx.rig", "[Radio]\nVERSION=1.3\nTYPE=2\n")),
            ("RX-12", "lease_setting", lambda: self.put("etc/systemd/system/lab-lease-sdrpp.service", self.lease("DevicePolicy=auto"))),
            ("RX-15", "dataset_deny_token", lambda: self.put("opt/lab/datasets/torchsig.json", {"labels": ["p25"]})),
            ("RX-15", "label_not_allowlisted", lambda: self.put("var/lib/lab/annotations.json", {"kind": "srrx_spectrum_annotations", "annotations": [{"label": "radar_pulse"}]})),
            ("RX-17", "kernel_cmdline_mismatch", lambda: self.put("etc/kernel/cmdline", "console=ttyMSM0,115200n8 rw clk_ignore_unused\n")),
            # Upstream SDR++ rtl_sdr_source layout (devices.<name>.directSampling) and Soapy device-argument strings.
            ("RX-01c", "direct_sampling_nonzero", lambda: self.put("home/lab/.config/sdrpp/rtl_sdr_config.json", self.sdrpp_rtl(2))),
            ("RX-01c", "direct_sampling_key", lambda: self.put("var/lib/openwebrx/sdrs.json", {"sdrs": {"rtl": {"type": "soapy", "device": "driver=rtlsdr,direct_samp=2"}}})),
            ("RX-01c", "bias_key", lambda: self.put("etc/SoapySDR/rtl.conf", "[rtl]\nargs = driver=rtlsdr biastee=true\n")),
            ("RX-01c", "direct_sampling_nonzero", lambda: self.put("etc/lab/receivers.json", {"rx": ["driver=rtlsdr, directSampling=\"1\""]})),
            ("RX-01a", "pinned_package_present_unreviewed", lambda: self.put("var/lib/dpkg/status", "Package: libqnn1\nStatus: install ok installed\nVersion: 2.49.0-1\n"), "BLOCKED"),
            ("RX-16", "apt_pin_positive_outside_lab_pref", lambda: (self.put("etc/apt/preferences.d/lab.pref", self.LAB_PREF),
                                                                     self.put("etc/apt/preferences.d/50-unpin", "Package: wsjtx\nPin: release *\nPin-Priority: 500\n"))),
            ("RX-16", "apt_pin_positive_outside_lab_pref", lambda: (self.put("etc/apt/preferences.d/lab.pref", self.LAB_PREF),
                                                                     self.put("etc/apt/preferences", "Package: *\nPin: release o=LP-PPA-x\nPin-Priority: 1002\n"))),
            # systemd precedence: the effective fragment and drop-ins decide, not the last directory scanned.
            ("RX-12", "lease_setting", lambda: (self.put(self.U + "lab-lease-sdrpp.service", self.lease("DevicePolicy=auto") + "IPAddressAllow=any\n"),
                                                self.put(self.L + "lab-lease-sdrpp.service", self.lease()))),
            ("RX-12", "lease_setting", lambda: (self.put(self.L + "lab-lease-sdrpp.service", self.lease()),
                                                self.put(self.U + "lab-lease-sdrpp.service.d/10-x.conf", "[Service]\nDevicePolicy=auto\n"),
                                                self.put(self.L + "lab-lease-sdrpp.service.d/10-x.conf", "[Service]\nDevicePolicy=closed\n"))),
            ("RX-12", "lease_setting", lambda: (self.put(self.L + "lab-lease@.service", self.lease("ReadWritePaths=/data/products/%i")),
                                                self.put(self.U + "lab-lease@sdrpp.service.d/override.conf", "[Service]\nDevicePolicy=auto\nProtectSystem=no\n"))),
            ("RX-12", "lease_setting", lambda: (self.put(self.L + "lab-lease-sdrpp.service", self.lease()),
                                                self.put(self.U + "lab-.service.d/50-open.conf", "[Service]\nDevicePolicy=auto\n"))),
            ("RX-12", "lease_setting", lambda: (self.put(self.L + "lab-lease-sdrpp.service", self.lease()),
                                                self.put(self.U + "service.d/50-net.conf", "[Service]\nIPAddressAllow=any\n"))),
            ("RX-12", "lease_setting", lambda: (self.put(self.L + "lab-lease-sdrpp.service", self.lease()),
                                                self.put("etc/systemd/system.control/lab-lease-sdrpp.service.d/50-DevicePolicy.conf", "[Service]\nDevicePolicy=auto\n"))),
            ("RX-12", "lease_setting", lambda: (self.put(self.L + "lab-lease-sdrpp.service", self.lease("DevicePolicy=auto")),
                                                self.put(self.L + "lab-lease-sdrpp.service.d/50-fix.conf", "[Service]\nDevicePolicy=closed\n"),
                                                self.put(self.U + "lab-lease-sdrpp.service.d/50-fix.conf", ""))),
            ("RX-12", "lease_setting", lambda: self.put(self.U + "lab-lease-sdrpp.service", self.lease("ProtectSystem=strict \\\n  # c\n  full"))),
            ("RX-12", "lease_setting", lambda: self.put(self.U + "lab-lease-sdrpp.service", self.lease("IPAddressDeny="))),  # Allow alone restricts nothing
            ("RX-01c", "bias_key", lambda: self.put("home/lab/.config/f4exb/SDRangel.conf", "[General]\nrtlsdr\\biasTee=false\n")),
        ]
        for check_id, rule, inject, *expected in cases:
            with self.subTest(check=check_id, rule=rule):
                self.setUp()
                inject()
                self.assert_flips(check_id, rule, expected=(expected or ["FAIL"])[0])

    def edit(self, rel, old, new):
        path = self.rootfs / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def test_radio_off_layers_flip_only_rx_s2(self):
        modprobe, udev, unit = deploy.RADIO_OFF_MODPROBE, deploy.RADIO_OFF_UDEV, self.U + deploy.RADIO_OFF_UNIT
        dropin = self.U + "srrx.service.d/10-radio-off.conf"
        cases = [
            ("radio_off_modprobe_missing", lambda: (self.rootfs / modprobe).unlink()),
            ("radio_off_modprobe_modified", lambda: self.edit(modprobe, "install btusb /bin/false\n", "")),
            ("radio_off_modprobe_modified", lambda: self.edit(modprobe, "blacklist aic8800_fdrv_usb\n", "# blacklist aic8800_fdrv_usb\n")),
            ("radio_off_modprobe_override", lambda: self.put("usr/lib/modprobe.d/10-bt.conf", "install btusb /sbin/modprobe --ignore-install btusb\n")),
            ("radio_off_modprobe_override", lambda: self.put("etc/modprobe.d/00-aic.conf", "install aic8800-* /sbin/modprobe --ignore-install $CMDLINE_OPTS\n")),
            ("radio_off_udev_missing", lambda: (self.rootfs / udev).unlink()),
            ("radio_off_udev_modified", lambda: self.edit(udev, 'ATTR{authorized}="0"', 'ATTR{authorized}="1"')),
            ("radio_off_udev_modified", lambda: self.edit(udev, 'KERNEL=="1-1.4"', 'KERNEL=="1-1.3"')),
            ("radio_off_udev_reauthorize", lambda: self.put("etc/udev/rules.d/99-reauthorize.rules", 'ACTION=="add", SUBSYSTEM=="usb", ATTR{authorized}="1"\n')),
            ("radio_off_udev_reauthorize", lambda: self.put("usr/lib/udev/rules.d/90-hub.rules", 'SUBSYSTEM=="usb", ATTR{authorized_default}:="1"\n')),
            ("radio_off_unit_missing", lambda: (self.rootfs / unit).unlink()),
            ("radio_off_unit_missing", lambda: self.put(unit, "")),  # an empty file masks the unit
            ("radio_off_unit_modified", lambda: self.edit(unit, "ExecStart=/usr/bin/python3 -B -m srrx.rfkill block\n", "ExecStart=/bin/true\n")),
            ("radio_off_unit_modified", lambda: self.put("etc/systemd/system.control/" + deploy.RADIO_OFF_UNIT, "[Service]\nType=oneshot\nExecStart=/bin/true\n")),
            ("radio_off_unit_dropin", lambda: self.put(unit + ".d/50-noop.conf", "[Service]\nExecStart=\nExecStart=/bin/true\n")),
            ("radio_off_unit_dropin", lambda: self.put(self.U + "service.d/90-exit.conf", "[Service]\nSuccessExitStatus=1 2\n")),  # every service
            ("radio_off_unit_dropin", lambda: self.put(self.U + "srrx-.service.d/10-cond.conf", "[Unit]\nConditionPathExists=/nonexistent\n")),
            ("radio_off_not_required", lambda: (self.rootfs / dropin).unlink()),
            ("radio_off_not_required", lambda: self.put(self.U + "srrx.service.d/90-reset.conf", "[Unit]\nRequires=\n")),
            ("radio_off_hard_dependency_of_bridge", lambda: self.put(self.U + "srrx-poweroff.service.d/10-radio-off.conf",
                                                                     "[Unit]\nRequires=" + deploy.RADIO_OFF_UNIT + "\nAfter=" + deploy.RADIO_OFF_UNIT + "\n")),
            ("radio_off_hard_dependency_of_bridge", lambda: self.put(self.U + "srrx-poweroff.service.d/20-x.conf", "[Unit]\nBindsTo=" + deploy.RADIO_OFF_UNIT + "\n")),
        ]
        for rule, inject in cases:
            with self.subTest(rule=rule):
                self.setUp()
                inject()
                self.assert_flips("RX-S2", rule)
        # Without the observed port-4 binding the udev layer cannot be verified: BLOCKED, never PASS.
        for rule, inject in (("radio_off_binding_missing", lambda: (self.rootfs / "etc/srrx/devices.json").unlink()),
                             ("radio_off_binding_invalid", lambda: self.edit("etc/srrx/devices.json", '"1-1.4"', '"1-1.3"')),
                             ("json_unparsable", lambda: self.put("etc/srrx/devices.json", "{")),
                             ("target_module_differs", lambda: self.edit("opt/srrx/software/srrx/rfkill.py", "This module never unblocks.",
                                                                         "This module may unblock."))):
            with self.subTest(rule=rule):
                self.setUp()
                inject()
                self.assert_flips("RX-S2", rule, expected="BLOCKED")
        # Unrelated modprobe/udev/unit configuration and a soft bridge ordering do not flip it.
        self.setUp()
        self.put("etc/modprobe.d/alsa-base.conf", "options snd-hda-intel power_save=1\ninstall nouveau /bin/false\nblacklist pcspkr\n")
        self.put("etc/udev/rules.d/99-serial.rules", 'SUBSYSTEM=="usb", ATTR{authorized}=="1", ATTR{idVendor}=="0bda", GROUP="lab"\nATTR{authorized}="0"\n')
        self.put(self.U + "srrx-poweroff.service.d/10-radio-off.conf", "[Unit]\nWants=" + deploy.RADIO_OFF_UNIT + "\nAfter=" + deploy.RADIO_OFF_UNIT + "\n")
        self.put(self.U + "service.d/50-limits.conf", "[Service]\nMemoryMax=64M\nIPAddressDeny=any\n")  # neutral for the oneshot
        self.assertEqual(self.statuses(self.run_check()), self.base("controller"))

    U, L = "etc/systemd/system/", "usr/lib/systemd/system/"
    LAB_PREF = ("Package: *\nPin: release o=srrx-lab\nPin-Priority: 1001\n\nPackage: *\nPin: release o=srrx-mirror\nPin-Priority: 990\n\n"
                "Package: *\nPin: origin *\nPin-Priority: -1\n")

    @staticmethod
    def sdrpp_rtl(direct):
        """Upstream SDR++ rtl_sdr_source config layout, without biasT (a +lab build drops it)."""
        name = "Generic RTL2832U OEM :: LABRXA"
        return {"device": name, "devices": {name: {"sampleRate": 2400000.0, "directSampling": direct, "ppm": 0, "offsetTuning": False,
                                                   "rtlAgc": False, "tunerAgc": False, "gain": 20}}}

    def lease(self, change=None):
        settings = {"User": "lab", "DevicePolicy": "closed", "ProtectSystem": "strict", "ReadOnlyPaths": "/data",
                    "ReadWritePaths": "/data/products/sdrpp", "IPAddressAllow": "localhost", "IPAddressDeny": "any"}
        if change:
            key, value = change.split("=", 1)
            settings[key] = value
        return "[Unit]\nDescription=fixture lease\n\n[Service]\n" + "".join(k + "=" + v + "\n" for k, v in settings.items())

    def inject_md5_mismatch(self):
        self.put("usr/lib/libfastrpc_fixture.so", "tampered bytes")
        expected = hashlib.md5(b"reviewed bytes", usedforsecurity=False).hexdigest()
        self.put("var/lib/dpkg/info/fastrpc.md5sums", expected + "  usr/lib/libfastrpc_fixture.so\n")

    def test_fake_readelf_findings_flip_only_rows_9_and_10(self):
        good = readelf("librtlsdr.so.2", ["libusb-1.0.so.0", "libc.so.6"], RTL_EXPORTS)
        cases = [
            ("RX-10", "forbidden_dependency", {"gpredict": readelf(None, ["libgtk-3.so.0", "libhamlib.so.4"])},
             lambda: self.put("usr/bin/gpredict", FAKE_ELF)),
            ("RX-09", "librtlsdr_export_count", {"librtlsdr.so.2": readelf("librtlsdr.so.2", ["libusb-1.0.so.0"], RTL_EXPORTS[:36])},
             lambda: self.put("usr/lib/aarch64-linux-gnu/librtlsdr.so.2", FAKE_ELF)),
            ("RX-09", "librtlsdr_soname", {"librtlsdr.so.2": readelf("librtlsdr.so.0", ["libusb-1.0.so.0"], RTL_EXPORTS)},
             lambda: self.put("usr/lib/aarch64-linux-gnu/librtlsdr.so.2", FAKE_ELF)),
            ("RX-09", "zero_copy_string", {"librtlsdr.so.2": good},
             lambda: self.put("usr/lib/aarch64-linux-gnu/librtlsdr.so.2", FAKE_ELF + b"Allocating 15 Zero-Copy buffers")),
            ("RX-09", "rtlsdr_consumer_wrong_soname", {"rtl_consumer": readelf(None, ["librtlsdr.so.0", "libc.so.6"])},
             lambda: self.put("usr/bin/rtl_consumer", FAKE_ELF + b"librtlsdr.so.0\0")),
            ("RX-09", "readelf_output_truncated", {"librtlsdr.so.2": readelf("librtlsdr.so.2", [], RTL_EXPORTS, header_symbols=41)},
             lambda: self.put("usr/lib/aarch64-linux-gnu/librtlsdr.so.2", FAKE_ELF)),
            ("RX-09", "readelf_unavailable", {"librtlsdr.so.2": None},
             lambda: self.put("usr/lib/aarch64-linux-gnu/librtlsdr.so.2", FAKE_ELF)),
            ("RX-09", "readelf_failed", {"librtlsdr.so.2": (-2, "")},
             lambda: self.put("usr/lib/aarch64-linux-gnu/librtlsdr.so.2", FAKE_ELF)),
        ]
        for check_id, rule, outputs, inject in cases:
            with self.subTest(rule=rule):
                self.setUp()
                inject()
                tools = FakeTools(outputs)
                expected = "BLOCKED" if rule.startswith("readelf_") else "FAIL"
                self.assert_flips(check_id, rule, expected=expected, runner=tools)
                self.assertTrue(tools.calls and all(c[:4] == ["readelf", "-d", "--dyn-syms", "-W"] for c in tools.calls))
        # A correct staged library with a correct consumer is accepted; the readelf call is still bounded.
        self.setUp()
        self.put("usr/lib/aarch64-linux-gnu/librtlsdr.so.2", FAKE_ELF)
        self.put("usr/bin/rtl_consumer", FAKE_ELF + b"librtlsdr.so.2\0")
        tools = FakeTools({"librtlsdr.so.2": good, "rtl_consumer": readelf(None, ["librtlsdr.so.2"])})
        report = self.run_check(runner=tools)
        self.assertEqual(self.statuses(report), self.base("controller"))
        # Profile full: the same libhamlib Gpredict flips RX-10 from BLOCKED to FAIL.
        self.setUp()
        self.put("usr/bin/gpredict", FAKE_ELF)
        self.assert_flips("RX-10", "forbidden_dependency", profile="full", runner=FakeTools({"gpredict": readelf(None, ["libhamlib.so.4"])}))

    def openwebrx_state(self):
        self.put("var/lib/openwebrx/settings.json", LOCKED)
        self.put("var/lib/openwebrx/users.json", [{"user": "admin", "enabled": True, "password": {"encoding": "hash", "value": "fixture"}}])

    def test_full_profile_requires_row_evidence_for_present_components(self):
        # An owrx package or a Gpredict binary outside the listed paths is still found and evaluated.
        self.openwebrx_state()
        self.put("opt/owrx-venv/lib/python3.12/site-packages/owrx/modes.py", 'mappings = [AnalogMode("nfm", "FM"), DigitalMode("tetra", "TETRA")]\n')
        report = self.assert_flips("RX-05", "mode_denied", profile="full")
        self.assertIn({"path": "opt/owrx-venv/lib/python3.12/site-packages/owrx/modes.py", "rule": "mode_denied", "effect": "FAIL", "item": "tetra"},
                      self.check(report, "RX-05")["findings"])
        self.setUp()
        self.put("home/lab/.config/Gpredict/gpredict.cfg", "[TLE]\nAUTO_UPDATE_FREQ=0\n")
        self.put("usr/share/gpredict/data/README", "x")
        self.put("opt/gpredict/bin/gpredict", FAKE_ELF)
        self.assert_flips("RX-10", "forbidden_dependency", profile="full", runner=FakeTools({"gpredict": readelf(None, ["libhamlib.so.4"])}))
        # Footprint present but the row's evidence file missing: BLOCKED, never PASS.
        for check_id, rule, inject in (
                ("RX-05", "modes_py_not_found", lambda: (self.openwebrx_state(), self.put("usr/bin/openwebrx", "#!/bin/sh\n"))),
                ("RX-10", "gpredict_binary_not_found", lambda: (self.put("home/lab/.config/Gpredict/gpredict.cfg", "[TLE]\nAUTO_UPDATE_FREQ=0\n"),
                                                                self.put("usr/share/gpredict/data/README", "x")))):
            with self.subTest(rule=rule):
                self.setUp()
                inject()
                result = self.check(self.run_check("full"), check_id)
                self.assertEqual(result["status"], "BLOCKED", result)
                self.assertEqual({f["rule"] for f in result["findings"]}, {rule})
        # With the evidence present and compliant the row passes in profile full.
        self.setUp()
        self.openwebrx_state()
        self.put("usr/lib/python3/dist-packages/owrx/modes.py", 'mappings = [AnalogMode("nfm", "FM"), DigitalMode("ft8", "FT8")]\n')
        self.assertEqual(self.check(self.run_check("full"), "RX-05")["status"], "PASS")

    def test_accepted_configurations_do_not_flip(self):
        accepted = [
            lambda: self.put("etc/systemd/system/lab-lease-sdrpp.service", self.lease()),
            lambda: self.put("home/lab/.config/sdrpp/rtl_sdr_config.json", {"devices": {"LABRXA": {"directSamplingMode": 0, "gain": 20}}}),
            lambda: self.put("var/lib/dpkg/status", "Package: librtlsdr2\nStatus: install ok installed\nVersion: 2.0.3-0+lab1\n\n"
                             "Package: direwolf\nStatus: deinstall ok config-files\nVersion: 1.7-1\n\n"
                             "Package: dream\nStatus: install ok installed\nVersion: 2.1.1-3+lab1\n\n"
                             "Package: gpredict\nStatus: install ok installed\nVersion: 2.6+git20261011-0+lab1\n\n"
                             "Package: libgl1-mesa-dri\nStatus: install ok installed\nVersion: 24.0.5-1ubuntu1\n"),
            lambda: self.put("home/lab/.config/Gpredict/radios/rx.rig", "[Radio]\nTYPE=0\n"),
            lambda: self.put("opt/lab/datasets/allowed.json", {"labels": ["analog_broadcast", "weather_satellite"]}),
            lambda: (self.put("etc/apt/sources.list.d/lab.list", "deb [signed-by=/usr/share/keyrings/lab.gpg] file:/srv/aptly noble main\n# old: ppa:x/y\n"),
                     self.put("etc/apt/preferences.d/lab.pref", "Package: *\nPin: release o=srrx-lab\nPin-Priority: 1001\n\nPackage: *\nPin: release o=srrx-mirror\n"
                              "Pin-Priority: 990\n\nPackage: *\nPin: origin *\nPin-Priority: -1\n\nPackage: wsjtx libhamlib4t64\nPin: release *\nPin-Priority: -1\n")),
            lambda: (self.put("usr/lib/libfastrpc_fixture.so", "reviewed bytes"),
                     self.put("var/lib/dpkg/info/fastrpc.md5sums", hashlib.md5(b"reviewed bytes", usedforsecurity=False).hexdigest() + "  /usr/lib/libfastrpc_fixture.so\n")),
            lambda: self.put("usr/lib/aarch64-linux-gnu/SoapySDR/modules0.8/librtlsdrSupport.so", "x"),
            lambda: self.put("home/lab/.config/sdrpp/rtl_sdr_config.json", self.sdrpp_rtl(0)),
            lambda: self.put("var/lib/openwebrx/sdrs.json", {"sdrs": {"rtl": {"type": "soapy", "device": "driver=rtlsdr,serial=LABRXA"}}}),
            # systemd precedence: a compliant /etc copy shadows a bad /usr/lib copy, an empty /etc file masks it,
            # a same-named /etc drop-in overrides a bad /usr/lib drop-in, and a /usr/lib drop-in can fix its fragment.
            lambda: (self.put(self.U + "lab-lease-sdrpp.service", self.lease()), self.put(self.L + "lab-lease-sdrpp.service", self.lease("DevicePolicy=auto"))),
            lambda: (self.put(self.U + "lab-lease-sdrpp.service", ""), self.put(self.L + "lab-lease-sdrpp.service", self.lease("DevicePolicy=auto"))),
            lambda: (self.put(self.L + "lab-lease-sdrpp.service", self.lease()),
                     self.put(self.U + "lab-lease-sdrpp.service.d/10-x.conf", "[Service]\nDevicePolicy=closed\n"),
                     self.put(self.L + "lab-lease-sdrpp.service.d/10-x.conf", "[Service]\nDevicePolicy=auto\n")),
            lambda: (self.put(self.L + "lab-lease-sdrpp.service", self.lease("DevicePolicy=auto")),
                     self.put(self.L + "lab-lease-sdrpp.service.d/50-fix.conf", "[Service]\nDevicePolicy=closed\n")),
            lambda: (self.put(self.L + "lab-lease@.service", self.lease("ReadWritePaths=/data/products/%i")),
                     self.put(self.U + "lab-lease@sdrpp.service.d/override.conf", "[Service]\nReadWritePaths=/data/products/sdrpp-cache\n")),
            lambda: (self.put("etc/apt/preferences.d/lab.pref", self.LAB_PREF),
                     self.put("etc/apt/preferences.d/20-block", "Package: wsjtx*\nPin: release *\nPin-Priority: -1\n"),
                     self.put("etc/apt/preferences.d/README.txt", "Package: *\nPin: release *\nPin-Priority: 900\n"),
                     self.put("etc/apt/preferences.d/old.pref.dpkg-old", "Package: *\nPin: release *\nPin-Priority: 900\n")),
        ]
        for index, inject in enumerate(accepted):
            with self.subTest(case=index):
                self.setUp()
                inject()
                self.assertEqual(self.statuses(self.run_check()), self.base("controller"))

    def test_target_module_copy_must_match_the_checker(self):
        # Each row needs the target copy of its module AND of every srrx module that module imports.
        users = {"RX-13": ("spectrum", "learning"), "RX-15": ("learning",), "RX-S1": ("decoder_policy",), "RX-S2": ("rfkill",)}
        closure = {check: set().union(*(selftest.srrx_closure(m) for m in modules)) for check, modules in users.items()}
        self.assertTrue({"__init__", "learning", "scope_policy", "spectrum"} <= closure["RX-15"], closure)
        self.assertTrue({"__init__", "decoder_policy", "scope_policy"} <= closure["RX-S1"], closure)
        self.assertEqual(closure["RX-S2"], {"__init__", "rfkill"})
        for name in ("decoder_policy", "spectrum", "scope_policy", "rfkill", "__init__"):
            with self.subTest(module=name):
                self.setUp()
                path = self.rootfs / "opt/srrx/software/srrx" / (name + ".py")
                path.write_text(path.read_text(encoding="utf-8") + "\n# changed target copy\n", encoding="utf-8")
                report = self.run_check()
                expected = {check for check, deps in closure.items() if name in deps}
                self.assertTrue(expected)
                self.assertEqual({k for k, v in self.statuses(report).items() if v != self.base("controller")[k]}, expected)
                for check_id in expected:
                    result = self.check(report, check_id)
                    self.assertEqual(result["status"], "BLOCKED")
                    self.assertIn({"path": "opt/srrx/software/srrx/%s.py" % name, "rule": "target_module_differs", "effect": "BLOCKED"}, result["findings"])
        self.setUp()
        (self.rootfs / "opt/srrx/software/srrx/scope_policy.py").unlink()
        rx15 = self.check(self.run_check(), "RX-15")
        self.assertIn("target_module_missing", {f["rule"] for f in rx15["findings"]})

    def test_band_mask_and_decoder_gate_are_really_evaluated(self):
        report = self.run_check(rootfs=self.clean)
        self.assertEqual(self.check(report, "RX-13")["status"], "PASS")
        sys.path.insert(0, str(deploy.PROJECT / "software"))
        import srrx.decoder_policy as decoder_policy
        import srrx.spectrum as spectrum
        with patch.object(spectrum, "mask_frame", lambda frame: dict(frame)):  # a mask that keeps caller-valid bins
            masked = self.check(self.run_check(rootfs=self.clean), "RX-13")
        self.assertEqual(masked["status"], "FAIL")
        self.assertIn("mask_bin_valid", {f["rule"] for f in masked["findings"]})
        # A mask without the Cospas-Sarsat 406.0-406.1 MHz uplink is caught by the 406.05 MHz probe alone.
        without = tuple(band for band in spectrum.MASKED_BANDS_HZ if band != spectrum.COSPAS_SARSAT_UPLINK_HZ)
        self.assertEqual(len(without), len(spectrum.MASKED_BANDS_HZ) - 1)
        with patch.object(spectrum, "MASKED_BANDS_HZ", without):
            uplink = self.check(self.run_check(rootfs=self.clean), "RX-13")
        self.assertEqual(uplink["status"], "FAIL")
        self.assertEqual({(f["rule"], f.get("item")) for f in uplink["findings"] if f["rule"] == "mask_bin_valid"},
                         {("mask_bin_valid", "406.05MHz")})
        enabled = dict(decoder_policy.availability(), **{"ais-public": "ENABLED_FIXTURE"})
        with patch.object(decoder_policy, "availability", return_value=enabled):
            gate = self.check(self.run_check(rootfs=self.clean), "RX-S1")
        self.assertEqual(gate["status"], "FAIL")
        self.assertEqual(gate["findings"][0]["item"], "ais-public")

    # ------------------------------------------------------------ component manifests and signatures

    def sdrangel_prefix(self, rootfs):
        prefix = rootfs / "opt/sdrangel"
        for name in selftest.load_policy(POLICY)["components"]["sdrangel"]["allow_plugins"]:
            rel = "lib/sdrangel/pluginssrv/lib%ssrv.so" % ("input" + name if name in ("rtlsdr", "airspyhf") else
                                                           "feature" + name if name == "satellitetracker" else name)
            self.put("opt/sdrangel/" + rel, "synthetic receive-only plugin fixture " + rel, rootfs)
        self.put("opt/sdrangel/bin/sdrangelsrv", "synthetic server fixture", rootfs)
        self.put("opt/sdrangel/audit.txt", "Synthetic validator fixture; not a real native API audit.\n", rootfs)
        self.put("opt/sdrangel/tx-tests.txt", "Synthetic validator fixture; not conducted hardware evidence.\n", rootfs)
        files = {p.relative_to(prefix).as_posix(): deploy.sha(p) for p in sorted(prefix.rglob("*")) if p.is_file()}
        report = lambda n: {"status": "PASS", "report": {"path": n, "sha256": files[n]}}
        manifest = {"schema_version": 1, "status": "REVIEWED", "files": files,
                    "allowed_modules": sorted(k for k in files if ".so" in k), "source_audit": report("audit.txt"),
                    "tx_negative_tests": report("tx-tests.txt")}
        path = self.work / "sdrangel-manifest.json"
        path.write_text(json.dumps(manifest))
        (self.work / "sdrangel-manifest.json.sig").write_bytes(b"synthetic detached signature")
        (self.work / "keyring.gpg").write_bytes(b"synthetic keyring")
        return path, self.work / "sdrangel-manifest.json.sig", self.work / "keyring.gpg"

    def test_sdrangel_full_profile_needs_reviewed_signed_matching_manifest(self):
        manifest, signature, keyring = self.sdrangel_prefix(self.rootfs)
        def rx02(**kwargs):
            return self.check(self.run_check("full", **kwargs), "RX-02")
        tools = FakeTools()
        ok = rx02(manifests={"sdrangel": (manifest, signature)}, keyring=keyring, runner=tools)
        self.assertEqual(ok["status"], "PASS", ok)
        gpgv = [c for c in tools.calls if c[0] == "gpgv"]
        self.assertEqual(gpgv, [["gpgv", "--status-fd", "1", "--keyring", str(keyring.resolve()), str(signature), str(manifest)]])
        self.assertIn("component_manifest_missing", {f["rule"] for f in rx02()["findings"]})
        self.assertEqual(rx02(manifests={"sdrangel": (manifest, signature)})["status"], "BLOCKED")  # no keyring
        bad = rx02(manifests={"sdrangel": (manifest, signature)}, keyring=keyring, runner=FakeTools(gpgv=(1, "[GNUPG:] BADSIG 0123 fixture\n")))
        self.assertEqual(bad["status"], "BLOCKED")
        self.assertIn("manifest_signature_invalid", {f["rule"] for f in bad["findings"]})
        unavailable = rx02(manifests={"sdrangel": (manifest, signature)}, keyring=keyring, runner=FakeTools(gpgv=None))
        self.assertIn("gpgv_unavailable", {f["rule"] for f in unavailable["findings"]})
        record = json.loads(manifest.read_text())
        open_manifest = self.work / "open.json"
        open_manifest.write_text(json.dumps(dict(record, status="OPEN")))
        self.assertIn("component_manifest_not_reviewed", {f["rule"] for f in rx02(manifests={"sdrangel": (open_manifest, signature)}, keyring=keyring, runner=FakeTools())["findings"]})
        (self.rootfs / "opt/sdrangel/lib/sdrangel/pluginssrv/libdemodamsrv.so").write_text("changed bytes")
        tampered = rx02(manifests={"sdrangel": (manifest, signature)}, keyring=keyring, runner=FakeTools())
        self.assertEqual(tampered["status"], "FAIL")
        self.assertIn("component_manifest_mismatch", {f["rule"] for f in tampered["findings"]})
        self.setUp()
        manifest, signature, keyring = self.sdrangel_prefix(self.rootfs)
        self.put("opt/sdrangel/lib/sdrangel/pluginssrv/libdemoddsdsrv.so", "digital voice decoder fixture")
        extra = rx02(manifests={"sdrangel": (manifest, signature)}, keyring=keyring, runner=FakeTools())
        self.assertEqual(extra["status"], "FAIL")
        self.assertTrue({"deny_token", "plugin_not_allowlisted", "component_manifest_mismatch"} <= {f["rule"] for f in extra["findings"]})
        self.setUp()
        manifest, signature, keyring = self.sdrangel_prefix(self.rootfs)
        (self.rootfs / "opt/sdrangel/lib/sdrangel/pluginssrv/libdemodnavtexsrv.so").unlink()
        missing = rx02(manifests={"sdrangel": (manifest, signature)}, keyring=keyring, runner=FakeTools())
        self.assertIn({"path": "opt/sdrangel/lib/sdrangel", "rule": "allowlisted_plugin_missing", "effect": "FAIL", "item": "demodnavtex"}, missing["findings"])
        with self.assertRaises(deploy.DeploymentError):
            self.run_check("full", manifests={"sdrpp": (manifest, None)})

    # ------------------------------------------------------------ robustness

    def test_symlink_escape_and_loop_block_while_absolute_links_stay_inside(self):
        self.symlink(self.rootfs / "usr/lib/escape", "../../../../outside-target")
        report = self.assert_flips("RX-00", "symlink_escapes_rootfs", expected="BLOCKED")
        self.assertEqual(report["status"], "BLOCKED")
        self.setUp()
        self.symlink(self.rootfs / "usr/lib/loop-a", "loop-b")
        self.symlink(self.rootfs / "usr/lib/loop-b", "loop-a")
        self.assert_flips("RX-00", "symlink_loop", expected="BLOCKED")
        # Absolute targets resolve inside the rootfs, never on the host.
        self.setUp()
        host = self.put("host-only/rtl_sdr_config.json", {"directSamplingMode": 1}, rootfs=self.work)
        self.symlink(self.rootfs / "home/lab/.config/sdrpp/host.json", str(host.resolve()))
        self.assertEqual(self.statuses(self.run_check()), self.base("controller"))
        self.put("etc/lab-configs/rtl.json", {"directSamplingMode": 1})
        self.symlink(self.rootfs / "home/lab/.config/sdrpp/rtl_sdr_config.json", "/etc/lab-configs/rtl.json")
        self.assert_flips("RX-01c", "direct_sampling_nonzero")
        self.setUp()
        self.put("usr/bin/rigctl.real", "#!/bin/sh\n")
        self.symlink(self.rootfs / "etc/alternatives/radio-control", "/usr/bin/rigctl.real")
        self.symlink(self.rootfs / "usr/bin/rigctl", "/etc/alternatives/radio-control")
        self.assert_flips("RX-01b", "forbidden_basename")
        # verify_build would resolve an absolute link on the host, so the component check stops first.
        self.setUp()
        manifest, signature, keyring = self.sdrangel_prefix(self.rootfs)
        self.symlink(self.rootfs / "opt/sdrangel/bin/sdrangel-link", "/opt/sdrangel/bin/sdrangelsrv")
        rx02 = self.check(self.run_check("full", manifests={"sdrangel": (manifest, signature)}, keyring=keyring, runner=FakeTools()), "RX-02")
        self.assertEqual(rx02["status"], "BLOCKED")
        self.assertIn("absolute_symlink_in_component_prefix", {f["rule"] for f in rx02["findings"]})

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO")
    def test_special_file_blocks_and_is_never_opened(self):
        os.mkfifo(self.rootfs / "opt/srrx/pipe.json")
        report = self.assert_flips("RX-00", "special_file", expected="BLOCKED")
        self.assertIn({"path": "opt/srrx/pipe.json", "rule": "special_file", "effect": "BLOCKED"}, self.check(report, "RX-00")["findings"])

    def test_inventory_bound_blocks_every_offline_row(self):
        with patch.object(selftest, "MAX_ENTRIES", 10):
            report = self.run_check()
        self.assertFalse(report["target"]["inventory_complete"])
        for check in report["checks"]:
            if check["evaluability"] == "OFFLINE":
                self.assertNotEqual(check["status"], "PASS", check["id"])
        self.assertIn("inventory_bound", {f["rule"] for f in self.check(report, "RX-00")["findings"]})
        # The bound is checked while one directory is iterated: a huge directory is never materialised.
        huge = self.work / "huge"
        for index in range(300):
            self.put("big/f%03d" % index, "", rootfs=huge)
        consumed, real = [], os.scandir

        class Counting:
            def __init__(self, path):
                self.inner = real(path)

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                self.inner.close()

            def __iter__(self):
                for child in self.inner:
                    consumed.append(child.name)
                    yield child

        with patch.object(selftest.os, "scandir", Counting):
            entries, issues, complete = selftest.walk_rootfs(huge, limit=25)
        self.assertFalse(complete)
        self.assertEqual(len(entries), 25)
        self.assertEqual(issues, [{"path": ".", "rule": "inventory_bound"}])
        self.assertLessEqual(len(consumed), 27)  # "big" itself, 24 files, then the one that hit the bound

    def test_planted_secrets_never_reach_the_report(self):
        # SECRET matches the safe identifier alphabet: only the no-echo rule keeps it out of the report.
        self.assertTrue(selftest._SAFE_ITEM.fullmatch(SECRET))
        low = SECRET.lower()
        self.put("usr/lib/python3/dist-packages/owrx/modes.py", 'mappings = [AnalogMode("nfm", "FM"), DigitalMode("%s", "x"), DigitalMode("lora-%s", "y")]\n' % (SECRET, SECRET))
        self.put("var/lib/openwebrx/settings.json", dict(LOCKED, speech_url="https://" + SECRET))
        self.put("var/lib/openwebrx/users.json", [{"user": "admin", "enabled": True, "password": {"encoding": "hash", "value": SECRET}}])
        self.put("home/lab/.config/sdrpp/rtl_sdr_config.json", {"devices": {"LABRXA": {"directSamplingMode": 3, "note": SECRET}}})
        self.put("var/lib/dpkg/status", "Package: direwolf\nStatus: install ok installed\nVersion: 1.7\nDescription: x\n " + SECRET + "\n\n"
                 "Package: digiham-" + low + "\nStatus: install ok installed\nVersion: 1.0\n")
        self.put("var/lib/dpkg/info/fastrpc.md5sums", "0" * 32 + "  usr/lib/" + SECRET + ".so\n")
        self.put("etc/apt/sources.list.d/extra.list", "deb http://ppa.launchpadcontent.net/" + SECRET + "/ubuntu noble main\n")
        self.put("etc/kernel/cmdline", "console=tty1 " + SECRET + "\n")
        self.put("opt/lab/datasets/labels.json", {"labels": ["neighbour-" + SECRET, "tetra-" + SECRET]})
        self.put("usr/share/satdump/satdump_cfg.json", {"satdump_general": {"kepler_update_interval": {"value": "Never"}, "record_" + SECRET: {"value": True}}})
        self.put("usr/bin/gpredict", FAKE_ELF)
        report = self.run_check(runner=FakeTools({"gpredict": readelf(None, ["libhamlib-" + SECRET + ".so.4"])}))
        text = json.dumps(report)
        self.assertEqual(report["status"], "FAIL")
        self.assertNotIn(SECRET, text)
        self.assertNotIn(low, text.lower())
        findings = {(c["id"], f["rule"], f.get("item")) for c in report["checks"] for f in c["findings"]}
        # The violations are still found; their identifiers are policy-derived.
        self.assertTrue({("RX-05", "mode_not_allowlisted", None), ("RX-05", "mode_denied", "lora-*"), ("RX-15", "label_not_allowlisted", None),
                         ("RX-15", "dataset_deny_token", "tetra"), ("RX-01a", "forbidden_package", "digiham*"), ("RX-04", "recording_enabled", None),
                         ("RX-10", "forbidden_dependency", "libhamlib"), ("RX-16", "dpkg_verify_missing_file", "fastrpc")} <= findings, findings)
        rx05 = self.check(report, "RX-05")
        self.assertNotIn("admin_password_missing", {f["rule"] for f in rx05["findings"]})
        self.assertIn("locked_setting", {f["rule"] for f in rx05["findings"]})

    def test_cli_refuses_existing_or_inside_output_and_writes_new_report(self):
        existing = self.work / "existing.json"
        existing.write_text("keep\n")
        base = [sys.executable, str(HERE / "selftest.py"), "offline", "--rootfs", str(self.rootfs), "--profile", "controller",
                "--policy", str(self.reviewed), "--cmdline-sha256", self.cmdline]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        for output in (existing, self.rootfs / "report.json"):
            out = subprocess.run(base + ["--output", str(output)], capture_output=True, text=True, env=env, timeout=120)
            self.assertEqual(out.returncode, 2, out.stderr)
            self.assertTrue(out.stderr.startswith("BLOCKED:"), out.stderr)
        self.assertEqual(existing.read_text(), "keep\n")
        self.assertFalse((self.rootfs / "report.json").exists())
        fresh = self.work / "fresh.json"
        out = subprocess.run(base + ["--output", str(fresh)], capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(out.returncode, 2, out.stderr)  # honest BLOCKED: exit 0 only for OFFLINE_CHECKS_PASS
        written = json.loads(fresh.read_text(encoding="utf-8"))
        self.assertEqual((written["tool"], written["status"]), ("srrx-selftest", "BLOCKED"))
        self.assertEqual(json.loads(out.stdout)["status"], "BLOCKED")
        bad = subprocess.run(base[:-2] + ["--cmdline-sha256", "XYZ", "--output", str(self.work / "bad.json")], capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(bad.returncode, 2)
        self.assertFalse((self.work / "bad.json").exists())

    def test_all_offline_rows_pass_exit_zero_and_fail_exits_two(self):
        # Hypothetical catalogue without the two unimplemented rows: RUNTIME_ONLY rows do not block an
        # all-PASS offline report, which is still no hardware or receive-only proof.
        implemented = tuple(row for row in selftest.CATALOGUE if row[2] != "NOT_IMPLEMENTED")
        argv = ["offline", "--rootfs", str(self.rootfs), "--profile", "controller", "--policy", str(self.reviewed), "--cmdline-sha256", self.cmdline]
        with patch.object(selftest, "CATALOGUE", implemented):
            report = self.run_check(allow_pass=True)
            self.assertEqual((report["status"], report["blockers"]), ("OFFLINE_CHECKS_PASS", []))
            self.assertGreater(report["counts"]["RUNTIME_ONLY"], 0)
            self.assertEqual(report["counts"]["FAIL"] + report["counts"]["BLOCKED"], 0)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(selftest.main(argv + ["--output", str(self.work / "pass.json")]), 0)
            summary = json.loads(out.getvalue())
            self.assertEqual((summary["status"], summary["blockers"]), ("OFFLINE_CHECKS_PASS", []))
            written = json.loads((self.work / "pass.json").read_text(encoding="utf-8"))
            self.assertEqual(written["status"], "OFFLINE_CHECKS_PASS")
            self.assertFalse(written["receive_only_proven"] or written["hardware_ready"])
            self.put("usr/bin/rigctld", "#!/bin/sh\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(selftest.main(argv + ["--output", str(self.work / "fail.json")]), 2)
            self.assertEqual(json.loads(out.getvalue())["status"], "FAIL")
            # The shipped DRAFT policy can never pass, even with every offline row clean.
            self.setUp()
            draft = self.run_check(policy=POLICY)
            self.assertEqual((draft["status"], draft["blockers"]), ("BLOCKED", ["POLICY_NOT_REVIEWED"]))

    def test_symlinked_parents_and_masks_resolve_inside_rootfs(self):
        # A symlinked parent directory (chroot-style absolute target) does not hide its content.
        self.put("opt/soapy-real/modules0.8/libremoteSupport.so", "x")
        self.symlink(self.rootfs / "usr/lib/aarch64-linux-gnu/SoapySDR", "/opt/soapy-real")
        self.assert_flips("RX-06", "module_not_allowlisted")
        self.setUp()
        self.put("srv/home/lab/.config/sdrpp/rtl_sdr_config.json", self.sdrpp_rtl(1))
        self.symlink(self.rootfs / "home/lab", "/srv/home/lab")
        self.assert_flips("RX-01c", "direct_sampling_nonzero")
        self.setUp()
        self.put("opt/units/lab-lease-sdrpp.service", self.lease("ProtectSystem=full"))
        self.symlink(self.rootfs / "usr/local/lib/systemd/system", "../../../../opt/units")
        self.assert_flips("RX-12", "lease_setting")
        # /dev/null masks: a masked fragment is not loaded; a masked drop-in no longer fixes its fragment.
        self.setUp()
        self.put(self.L + "lab-lease-sdrpp.service", self.lease("DevicePolicy=auto"))
        self.symlink(self.rootfs / (self.U + "lab-lease-sdrpp.service"), "/dev/null")
        report = self.run_check()
        self.assertEqual(self.statuses(report), self.base("controller"))
        self.assertIn("masked_units_skipped", self.check(report, "RX-12")["notes"])
        self.setUp()
        self.put(self.L + "lab-lease-sdrpp.service", self.lease("DevicePolicy=auto"))
        self.put(self.L + "lab-lease-sdrpp.service.d/50-fix.conf", "[Service]\nDevicePolicy=closed\n")
        self.symlink(self.rootfs / (self.U + "lab-lease-sdrpp.service.d/50-fix.conf"), "/dev/null")
        self.assert_flips("RX-12", "lease_setting")
        # A dangling link that may shadow a lower copy is undecidable: BLOCKED.
        self.setUp()
        self.put(self.L + "lab-lease-sdrpp.service", self.lease())
        self.symlink(self.rootfs / (self.U + "lab-lease-sdrpp.service"), "/opt/missing/lab-lease-sdrpp.service")
        self.assert_flips("RX-12", "unit_link_unresolvable", expected="BLOCKED")
        # An enabled instance (.wants link to the template) is evaluated through the template plus its own drop-ins.
        self.setUp()
        self.put(self.L + "lab-lease@.service", self.lease("ReadWritePaths=/data/products/%i"))
        self.put(self.L + "lab-lease@sdrpp.service.d/10-x.conf", "[Service]\nReadWritePaths=/data\n")
        self.symlink(self.rootfs / (self.U + "multi-user.target.wants/lab-lease@sdrpp.service"), "/usr/lib/systemd/system/lab-lease@.service")
        self.assert_flips("RX-12", "lease_setting")

    # ------------------------------------------------------------ parsers and policy data

    def test_dpkg_status_counts_unpacked_and_rejects_malformed(self):
        states = {"a": "install ok installed", "b": "install ok unpacked", "c": "install ok half-configured",
                  "d": "install ok triggers-pending", "e": "install ok half-installed", "f": "deinstall ok config-files",
                  "g": "purge ok not-installed", "h": "install reinstreq half-installed"}
        status = self.put("var/lib/dpkg/status", "\n".join("Package: %s\nStatus: %s\nVersion: 1\nDescription: d\n long\n .\n" % kv for kv in states.items()))
        records = {r["package"]: r["state"] for r in selftest.parse_dpkg_status(status)}
        self.assertEqual({p for p, s in records.items() if s not in ("not-installed", "config-files")}, set("abcdeh"))
        self.put("var/lib/dpkg/status", "Package: a\nbroken line without colon\n")
        with self.assertRaises(deploy.DeploymentError):
            selftest.parse_dpkg_status(status)
        self.put("var/lib/dpkg/status", "Package: a\nStatus: install ok installed\n")
        with self.assertRaises(deploy.DeploymentError):
            selftest.parse_dpkg_status(status, limit=8)
        self.put("var/lib/dpkg/status", "Package: a\nPackage: b\n")
        rx01a = self.check(self.run_check(), "RX-01a")
        self.assertEqual(rx01a["status"], "BLOCKED")
        self.assertIn("dpkg_status_unparsable", {f["rule"] for f in rx01a["findings"]})

    def test_debian_version_order_and_rules(self):
        for a, b, sign in (("26.0.1-1", "26", 1), ("25.2.3-1ubuntu1", "26", -1), ("1:1.0", "2.0", 1), ("1.0~rc1", "1.0", -1),
                           ("0.1.0-8", "0.1.0-8", 0), ("0.1.0-7", "0.1.0-8", -1), ("0.1.0-10", "0.1.0-8", 1), ("2.0.3-0+lab1", "2.0.3-0", 1)):
            with self.subTest(a=a, b=b):
                result = selftest.deb_compare(a, b)
                self.assertEqual((result > 0) - (result < 0), sign)
        self.assertTrue(selftest._version_forbidden({"forbid_at_least": "26"}, "26.0.0-1"))
        self.assertFalse(selftest._version_forbidden({"forbid_at_least": "26"}, "24.0.5-1"))
        self.assertTrue(selftest._version_forbidden({"forbid_at_least": "26"}, "x:bad"))  # unparsable: conservative

    def test_elf_parser_and_bounded_runner(self):
        info = selftest.elf_dynamic("/fixture/librtlsdr.so.2", FakeTools({"librtlsdr.so.2": readelf("librtlsdr.so.2", ["libusb-1.0.so.0"], RTL_EXPORTS)}))
        self.assertEqual(info["soname"], "librtlsdr.so.2")
        self.assertEqual(info["needed"], ["libusb-1.0.so.0"])
        defined = {n for n, _, _, ndx in info["symbols"] if ndx != "UND" and n.startswith("rtlsdr_")}
        self.assertEqual(len(defined), 37)
        static = (0, "\nThere is no dynamic section in this file.\n")
        self.assertEqual(selftest.elf_dynamic("/fixture/static", FakeTools({"static": static}))["needed"], [])
        for broken in ((0, "\nDynamic section at offset 0x1 contains 3 entries:\n 0x1 (NEEDED) Shared library: [a]\n"), (0, ""), (1, "x")):
            with self.assertRaises(selftest.ElfError):
                selftest.elf_dynamic("/fixture/broken", FakeTools({"broken": broken}))
        self.assertIsNone(selftest.run_bounded(["srrx-selftest-no-such-tool-7c1"], 5, 1000))
        capped = selftest.run_bounded([sys.executable, "-c", "print('x' * 5000)"], 30, 100)
        self.assertEqual(capped, (-2, ""))
        # An endless writer is killed once limit+1 bytes arrived, long before the timeout.
        started = time.monotonic()
        endless = "import sys\nwhile True:\n    sys.stdout.write('x' * 65536)\n    sys.stdout.flush()\n"
        self.assertEqual(selftest.run_bounded([sys.executable, "-c", endless], 60, 4096), (-2, ""))
        self.assertLess(time.monotonic() - started, 30)
        self.assertEqual(selftest.run_bounded([sys.executable, "-c", "import time; time.sleep(30)"], 1, 1000), (-1, ""))
        code, text = selftest.run_bounded([sys.executable, "-c", "print('bounded')"], 30, 1000)
        self.assertEqual((code, text.strip()), (0, "bounded"))
        self.assertIsNone(selftest.verify_signature("m", "s", "k", FakeTools(gpgv=GOOD_SIG)))
        self.assertEqual(selftest.verify_signature("m", "s", "k", FakeTools(gpgv=(0, "[GNUPG:] GOODSIG only\n"))), "manifest_signature_invalid")

    def test_policy_schema_is_strict(self):
        policy = deploy.load(POLICY)
        for mutate in (lambda p: p.update(extra=1), lambda p: p.update(status="PASS"),
                       lambda p: p["components"]["sdrpp"]["footprint"].append("/usr/bin/sdrpp"),
                       lambda p: p["components"]["satdump"]["plugin_dirs"].append("usr/../etc"),
                       lambda p: p["forbidden_packages"].append({"name": "x", "glob": "y*", "group": "g", "check": "presence", "source": "s"}),
                       lambda p: p["forbidden_packages"].append({"name": "x", "group": "g", "check": "maybe", "source": "s"}),
                       lambda p: p["forbidden_packages"].append({"name": "x", "version_rule": {"newest": "1"}, "group": "g", "check": "presence", "source": "s"}),
                       lambda p: p["forbidden_packages"].append({"name": "x", "version_rule": {"require_lab_build": False}, "group": "g", "check": "presence", "source": "s"}),
                       lambda p: p["forbidden_packages"].append({"name": "x", "version_rule": {"require_lab_build": "yes"}, "group": "g", "check": "presence", "source": "s"}),
                       lambda p: p["forbidden_packages"].append({"name": "x", "version_rule": {"forbid_globs": []}, "group": "g", "check": "presence", "source": "s"}),
                       lambda p: p["components"].pop("gpredict"), lambda p: p["librtlsdr"].update(exports=True),
                       # Lists whose first element names a finding must not be empty (no IndexError at run time).
                       lambda p: p["components"]["satdump"].update(pipeline_dirs=[]), lambda p: p["components"]["openwebrx"].update(users_paths=[]),
                       lambda p: p["components"]["gpredict"]["tle_update"].update(file_globs=[]), lambda p: p["units"].update(system_unit_paths=[]),
                       lambda p: p["engine_config_rules"].update(direct_sampling_mode_keys=[]), lambda p: p["apt"].update(pref_priorities=[])):
            candidate = json.loads(json.dumps(policy))
            mutate(candidate)
            path = self.work / "policy.json"
            path.write_text(json.dumps(candidate))
            with self.subTest(mutate=mutate), self.assertRaises(deploy.DeploymentError):
                selftest.load_policy(path)
        path.write_text(POLICY.read_text(encoding="utf-8").replace('"status": "DRAFT",', '"status": "DRAFT", "status": "REVIEWED",', 1))
        with self.assertRaises(deploy.DeploymentError):
            selftest.load_policy(path)

    def test_policy_covers_every_forbidden_name_of_the_spec(self):
        policy = selftest.load_policy(POLICY)
        presence = [p for p in policy["forbidden_packages"] if p["check"] == "presence"]
        def forbidden(name, version="1.0-1"):
            return any((name == p["name"] if "name" in p else fnmatch.fnmatchcase(name, p["glob"]))
                       and selftest._version_forbidden(p.get("version_rule"), version) for p in presence)
        gaps = ["gr-iridium", "gr-gsm", "kalibrate-rtl", "dump978-fa", "dump978-fa-minimal", "skyaware978", "dump1090-fa", "piaware",
                "multimon-ng", "js8call", "python3-js8py", "soapysdr0.8-module-lms7", "soapysdr0.8-module-hackrf", "soapysdr0.8-module-bladerf",
                "soapysdr0.8-module-uhd", "soapysdr0.8-module-redpitaya", "libsoapysdr0.9-0", "limesuite", "rtl-433", "digiham", "python3-digiham",
                "codecserver", "codecserver-driver-ambe3k", "acarsdec", "dumphfdl", "dumpvdl2", "libacars-2-2", "libacars-tools",
                "dxlaprs-tetra-decoder", "dxlaprs-lora", "python3-meshtastic", "python3-bleak", "m17-demod", "nrsc5", "hpsdrconnector", "lame",
                "python3-paho-mqtt", "aicrf-test", "wsjtx", "libhamlib4t64", "libhamlib-utils", "libhamlib-dev", "fldigi", "qsstv", "direwolf",
                "urh", "soapysdr-module-all", "soapysdr0.8-module-all", "soapysdr0.8-module-remote", "limesuiteng-gui", "gr-limesuiteng",
                "librtlsdr0", "snapd", "flatpak", "docker.io", "linux-image-7.0.0-1-qcom"]
        for name in gaps:
            self.assertTrue(forbidden(name), name)
        lock = {c["id"]: c["version"] for c in deploy.load(HERE / "sources.lock.json")["components"]}
        for name, bad, good in (("librtlsdr2", "2.0.1-2build1", "2.0.3-0+lab1"), ("dream", "2.1.1-3", "2.1.1-3+lab1"),
                                ("gpredict", "2.3-115-g0f3beb6-3build3", "2.6+git20261011-0+lab1"), ("gr-satellites", "5.5.0-2build2", "5.10.0~git20260922-0lab1"),
                                ("gpredict", "2.3-115-g1d80049+lab", lock["gpredict"]), ("gpredict", "2.6-1", "2.6+git20261011+lab1"),
                                ("gr-satellites", "5.10.0~git20260922-0", lock["gr-satellites"]),
                                ("sdrangel", "7.17.2-1", "7.27.2+lab1"), ("sdrangelsrv", "7.27.2-1", "7.27.2-1+lab1"),
                                ("sdrpp", "1.1.0-1", "git8c9f5ee+lab1"), ("openwebrx", "1.2.126", "1.2.126+lab1"),
                                ("satdump", "1.2.2-1", "2.0.0~alpha+git20260929+lab1"), ("rtl-sdr", "2.0.1-2build1", "2.0.3-0+lab1"),
                                ("dream", "2.1.1-3+lab1ubuntu1", "2.1.1-3+lab12"),  # the lab marker must end the version
                                ("libgl1-mesa-dri", "26.0.1-1", "24.0.5-1ubuntu1"), ("edk2-qcom", "0.1.0-8", "0.1.0-7"),
                                ("linux-firmware-dragonwing", "20260825-1", "1.0.0+20251203")):
            self.assertTrue(forbidden(name, bad), (name, bad))
            self.assertFalse(forbidden(name, good), (name, good))
        # The "+lab builds only" rule exists once, in the policy; deploy derives its set from it.
        self.assertEqual(deploy.LAB_BUILD_ONLY_PACKAGES, {"dream", "librtlsdr2", "rtl-sdr", "sdrangel", "sdrangelsrv", "sdrpp",
                                                          "openwebrx", "satdump", "gpredict", "gr-satellites"})
        self.assertTrue(forbidden("librtlsdr0", "2.0.3-0+lab1") and forbidden("limesuiteng-cli", "1.0.0+lab1"))  # forbidden outright
        basenames = {e["name"].lower() for e in policy["forbidden_basenames"]} | {n.lower() for n in deploy.BAD_NAMES}
        for name in ("rigctl", "rigctld", "rotctld", "limegui", "limetrx", "soapysdrserver", "wifi_test", "bt_test", "rtl_tcp", "rtl_433",
                     "multimon-ng", "dump1090-fa", "dump978-fa", "piaware", "dreamt", "kal", "satdump_sdr_server", "dockerd"):
            self.assertIn(name, basenames)
        self.assertFalse({"jt9", "wsprd", "sdrpp", "satdump", "gpredict"} & basenames)  # allowlisted decoders/apps stay usable

    def test_doctor_and_rx01a_reach_the_same_package_verdict(self):
        packages = {"wsjtx": "2.6.1", "digiham-tools": "0.6", "sdrangel": "7.17.2-1", "sdrangelsrv": "7.27.2-1+lab1",
                    "openwebrx": "1.2.126", "satdump": "1.2.2-1", "sdrpp": "git8c9f5ee+lab1", "rtl-sdr": "2.0.1-2build1",
                    "gpredict": "2.3-115-g1d80049+lab", "gr-satellites": "5.10.0~git20260922-0lab1", "dream": "2.1.1-3+lab1",
                    "librtlsdr0": "2.0.3-0+lab1", "limesuiteng-cli": "1.0.0+lab1", "librtlsdr2": "2.0.3-0+lab1",
                    "libgl1-mesa-dri": "26.0.1-1", "bash": "5.2.21-2ubuntu4"}
        rootfs = self.work / "dpkg-only"
        self.put("var/lib/dpkg/status", "".join("Package: %s\nStatus: install ok installed\nVersion: %s\n\n" % kv for kv in packages.items()), rootfs)
        policy = selftest.load_policy(POLICY)
        ctx = selftest.Ctx(rootfs, "controller", policy, deploy.PROJECT, {}, None, None, None)
        result = selftest.Result(next(row for row in selftest.CATALOGUE if row[0] == "RX-01a"))
        selftest.check_01a(ctx, result)
        rx01a = {f["item"] for f in result.findings if f["rule"] == "forbidden_package"}
        listing = "".join("%s\t%s\tinstalled\n" % kv for kv in packages.items())
        with patch.object(deploy, "command", lambda args, limit=100_000: {"returncode": 0, "stdout": listing if args[0] == "dpkg-query" else "", "stderr": ""}):
            issue = next(i for i in deploy.doctor()["issues"] if i.startswith("prohibited packages installed: "))
        doctor = {item.replace(deploy.VERSION_NOTE, "") for item in issue.split(": ", 1)[1].split(",")}
        self.assertEqual(doctor, rx01a)
        self.assertEqual(rx01a, {"wsjtx", "digiham*", "sdrangel", "openwebrx", "satdump", "rtl-sdr", "gpredict",
                                 "librtlsdr0", "limesuiteng-cli", "*mesa*"})

    def test_every_cited_line_exists(self):
        policy = selftest.load_policy(POLICY)
        texts = json.dumps(policy) + json.dumps(selftest.catalogue())
        cited = set(re.findall(r"((?:STACK\.md|build/\d\d-[a-z0-9-]+\.md|deployment/[\w.-]+\.(?:sh|py|json))):(\d+)(?:-(\d+))?", texts))
        self.assertGreater(len(cited), 40)
        lengths = {}
        for name, first, last in cited:
            path = deploy.PROJECT / name
            self.assertTrue(path.is_file(), name)
            if name not in lengths:
                lengths[name] = len(path.read_text(encoding="utf-8").splitlines())
            self.assertLessEqual(int(last or first), lengths[name], (name, first, last))
        self.assertTrue(all(p["source"] for p in policy["forbidden_packages"] + policy["forbidden_basenames"]))

    def test_deployment_doc_describes_the_offline_selftest(self):
        documented = (deploy.PROJECT / "software/DEPLOYMENT.md").read_text(encoding="utf-8")
        self.assertIn("python3 deployment/selftest.py offline", documented)
        self.assertIn("RUNTIME_ONLY", documented)
        self.assertIn("receive-only-policy.json", documented)
        for rule in ("tool_dependencies", "pinned_package_present_unreviewed", "modes_py_not_found", "gpredict_binary_not_found", "lab-lease@.service.d"):
            self.assertIn(rule, documented)
        source = (HERE / "selftest.py").read_text(encoding="utf-8")
        for rule in ("pinned_package_present_unreviewed", "modes_py_not_found", "gpredict_binary_not_found", '"tool_dependencies"'):
            self.assertIn(rule, source)  # the documented ids are the ones the checker emits


if __name__ == "__main__":
    unittest.main()
