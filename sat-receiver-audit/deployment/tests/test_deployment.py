"""Temporary-directory fixtures never represent accepted hardware/releases."""
import copy
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
        self.assertIn("ExecStartPre=/usr/bin/python3 -B /opt/srrx/deployment/deploy.py release-guard", guard)
        self.assertTrue((rootfs / "etc/systemd/system/srrx-poweroff.service.d/20-release-guard.conf").is_file())
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
