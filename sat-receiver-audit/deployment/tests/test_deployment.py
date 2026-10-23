"""Temporary-directory fixtures never represent accepted hardware/releases."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
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
        self.assertIn("ExecStart=/usr/bin/python3 -m srrx.rfkill block", unit)
        self.assertTrue((rootfs / "opt/srrx/software/srrx/rfkill.py").is_file())
        self.assertIn("Before=srrx.service", unit)
        dropin = (rootfs / "etc/systemd/system/srrx.service.d/10-radio-off.conf").read_text()
        self.assertIn("Requires=" + deploy.RADIO_OFF_UNIT, dropin)
        self.assertIn("After=" + deploy.RADIO_OFF_UNIT, dropin)
        self.assertNotIn("unblock", unit + dropin + "\n".join(modprobe))

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
        quiet = lambda args: {"returncode": 0, "stdout": "", "stderr": ""}
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
                    "sdrangel": "7.17.2-1", "openwebrx": "1.2.126", "gpredict": "2.3-115-g0f3beb6-3build3"}
        self.assertEqual(len(deploy.prohibited_installed(lab_only)), len(lab_only))
        allowed = {"dream": "2.1.1-2+lab1", "librtlsdr2": "2.0.3-0+lab1", "sdrangel": "7.27.2-1+lab1",
                   "openwebrx": "1.2.126+lab1", "gpredict": "2.3-115-g1d80049+lab", "aic8800-usb-dkms": "4.0"}
        dependencies = deploy.load(HERE / "dependencies.json")
        for name, versions in dependencies["required_target_packages"].items():
            allowed[name] = versions[0]
        for name, version in dependencies["additional_stack_package_versions"].items():
            allowed[name] = version or ""
        self.assertEqual(deploy.prohibited_installed(allowed), [])

    def test_prohibited_executables_on_target_are_reported(self):
        root = self.root / "target"
        (root / "usr/bin").mkdir(parents=True)
        for name in ("wifi_test", "bt_test", "rigctld", "rtl_tcp", "rtl_sdr", "python3"):
            (root / "usr/bin" / name).write_text("")
        self.assertEqual(deploy.prohibited_executables(root),
                         ["/usr/bin/bt_test", "/usr/bin/rigctld", "/usr/bin/rtl_tcp", "/usr/bin/wifi_test"])

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
        config.update(root_a_partuuid="11111111-1111-1111-1111-111111111111",
                      root_b_partuuid="22222222-2222-2222-2222-222222222222",
                      base_cmdline_without_root="console=ttyMSM0,115200n8 rw earlycon")
        for key in ("kernel_efi_path", "initrd_efi_path", "lab_dtb_efi_path", "rescue_kernel_efi_path", "rescue_initrd_efi_path", "rescue_dtb_efi_path"):
            config[key] = "/EFI/Linux/fixture-" + key
        result = deploy.stage_ab(config, self.root / "ab")
        self.assertFalse(result["active_slot_changed"])
        self.assertTrue((self.root / "ab/loader/entries/labB+3.conf").exists())
        self.assertIn("initrd /EFI/", (self.root / "ab/loader/entries/labB+3.conf").read_text())
        config["root_b_partuuid"] = config["root_a_partuuid"]
        with self.assertRaises(deploy.DeploymentError):
            deploy.stage_ab(config, self.root / "ab2")

    def test_doctor_uses_read_only_commands(self):
        called = []
        def read_only(args):
            called.append(args)
            return {"returncode": 0, "stdout": "", "stderr": ""}
        with patch.object(deploy, "command", read_only):
            result = deploy.doctor()
        self.assertTrue(result["read_only"])
        self.assertFalse(result["hardware_ready"])
        self.assertTrue(all(args[0] in {"dpkg-query", "lsblk"} for args in called))


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
                    'int main(){bool rejected=false;try{setup(SOAPY_SDR_TX);}catch(const std::runtime_error&){rejected=true;}'
                    'assert(rejected);assert(setup(SOAPY_SDR_RX));Config c;c.channels[TRXDir::Rx]={0};assert(stream(c));'
                    'c.channels[TRXDir::Tx]={0};assert(!stream(c));SDRConfig s;assert(configure(s)==OpStatus::Success);'
                    's.channel[1].tx.enabled=true;assert(configure(s)==OpStatus::NotSupported);'
                    'assert(write()==SOAPY_SDR_NOT_SUPPORTED);assert(waveform()==OpStatus::NotSupported);}')
            source = root / "guards.cpp"
            source.write_text(code)
            subprocess.run(["g++", "-std=c++20", "-Wall", "-Werror", str(source), "-o", str(root / "guards")], check=True, capture_output=True)
            subprocess.run([str(root / "guards")], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
