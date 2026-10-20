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
                       lambda c: c["lime"].update(enabled=True)):
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
        with self.assertRaises(deploy.DeploymentError):
            deploy.stage(self.root / "candidate")

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
