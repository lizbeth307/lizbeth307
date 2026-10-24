"""deployment/system: generated system files, staging, bundle modes, EDID, hooks, build manifest.

Temporary trees only; nothing here represents an installed or accepted Q6A root."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "system"))
import deploy  # noqa: E402
import build_manifest  # noqa: E402
import edid_field  # noqa: E402
import system_files  # noqa: E402

PROJECT = HERE.parent
SH = shutil.which("sh") if os.name == "posix" else None


def devices():
    config = deploy.load(HERE / "devices.template.json")
    config["i2c"]["ina228"] = {"path": "/dev/i2c-7", "of_fullname": "/soc@0/test-ina228"}
    config["i2c"]["control"] = {"path": "/dev/i2c-9", "of_fullname": "/soc@0/test-control"}
    config["pico"]["kernel_parent"] = "99c000.serial"
    config["usb"]["hfplus"]["serial"] = "AIRSPYHF SN:0123456789ABCDEF"
    config["wifi_bt"]["fe11s_port4_usb_path"] = "1-1.4"
    return config


class SystemFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-system-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def stage(self, name, config=None, gnss="gpsd"):
        deploy.stage(self.root / name, config, gnss)
        return self.root / name / "rootfs"

    def test_sysusers_create_every_account_units_rules_and_tmpfiles_name(self):
        users, groups = system_files.accounts()
        self.assertEqual({deploy.PICO_GROUP, deploy.GNSS_GROUP} - groups, set())
        needed = set()
        for unit in sorted((PROJECT / "software/systemd").glob("*.service")) + [HERE / "system/npu/inferd-htp.service"]:
            needed |= system_files.unit_accounts(unit.read_text(encoding="utf-8"))
        needed |= system_files.rule_groups(deploy.udev_rules(devices()) + deploy.gnss_udev_rules())
        missing = sorted(n for k, n in needed if n not in (users if k == "user" else groups))
        self.assertEqual(missing, [])
        text = system_files.sysusers()
        self.assertNotRegex(text, r"(?m)^m ")  # no members: srrx-pico/srrx-gnss stay empty
        for kind, name, *_ in system_files.SERVICE_ACCOUNTS:
            line = re.search(r"(?m)^%s %s .*$" % (kind, re.escape(name)), text).group(0)
            if kind == "u":
                self.assertTrue(line.endswith(" /usr/sbin/nologin"), line)
        self.assertNotIn("_chrony", text)  # created by the chrony package

    def test_stage_writes_the_system_files_and_masks_without_symlinks(self):
        rootfs = self.stage("candidate", devices())
        files = json.loads((self.root / "candidate/stage-files.json").read_text())["files"]
        for relative in (system_files.SYSUSERS, system_files.TMPFILES, system_files.SYSTEM_PRESET, system_files.USER_PRESET,
                         system_files.UDEV_FASTRPC, system_files.UDEV_PPS, system_files.UDEV_I2C, system_files.GNSS_BLACKLIST,
                         system_files.GPSD_DEFAULTS, system_files.CHRONY_CANDIDATE, system_files.LOGIND_DROPIN,
                         system_files.ZRAM, system_files.POLKIT_RADIO_OFF, system_files.EDID_FIRMWARE,
                         system_files.EDID_HOOK, system_files.DSP_HOOK):
            self.assertIn(relative, files)
        for unit in system_files.MASKED_UNITS:
            mask = rootfs / "etc/systemd/system" / unit
            self.assertTrue(mask.is_file() and not mask.is_symlink() and mask.stat().st_size == 0, unit)
        self.assertFalse(any(p.is_symlink() for p in rootfs.rglob("*")))
        self.assertFalse(any(rootfs.rglob("*.wants")))
        self.assertEqual((rootfs / system_files.EDID_FIRMWARE).read_bytes(), edid_field.build())
        rule = (rootfs / system_files.UDEV_I2C).read_text()
        self.assertIn('SUBSYSTEM=="i2c-dev", KERNEL=="i2c-7", GROUP="i2c", MODE="0660"', rule)
        self.assertIn('KERNEL=="i2c-9"', rule)
        self.assertEqual(system_files.unknown_accounts(rootfs), [])
        if os.name == "posix":
            for hook in system_files.EXECUTABLES:
                self.assertEqual(stat.S_IMODE((rootfs / hook).stat().st_mode), 0o755)
        # No device binding: no I2C group rule at all, the rest is unchanged.
        plain = self.stage("plain")
        self.assertFalse((plain / system_files.UDEV_I2C).exists())
        self.assertTrue((plain / system_files.SYSUSERS).is_file())

    def test_gnss_mode_files_satisfy_the_doctor_reader_checks(self):
        expected_gpsd = 'DEVICES="/dev/lab/gnss"\nGPSD_OPTIONS="-n -b -s 115200"\nUSBAUTO="false"\n'  # build/07 §18
        gpsd = self.stage("gpsd", devices(), "gpsd")
        self.assertTrue((gpsd / "etc/default/gpsd").read_text().endswith(expected_gpsd))
        self.assertEqual(deploy.gnss_mode_issues(gpsd), [])
        self.assertIn("offset TBD_MEASURED_MEDIAN_S", (gpsd / system_files.CHRONY_CANDIDATE).read_text())
        self.assertFalse((gpsd / "etc/chrony/conf.d/60-srrx-gnss.conf").exists())  # inert until measured
        self.assertFalse((gpsd / "etc/systemd/system/gpsd.service").exists())
        raw = self.stage("raw", devices(), "raw")
        self.assertEqual(deploy.gnss_mode_issues(raw), [])
        self.assertIn('DEVICES=""', (raw / "etc/default/gpsd").read_text())
        for unit in system_files.RAW_MODE_MASKS:
            self.assertEqual((raw / "etc/systemd/system" / unit).stat().st_size, 0)
            self.assertIn("disable " + unit, (raw / system_files.SYSTEM_PRESET).read_text().splitlines())
        self.assertFalse((raw / system_files.CHRONY_CANDIDATE).exists())
        off = self.stage("off", devices(), "off")
        self.assertEqual(deploy.gnss_mode_issues(off), [])

    def test_presets_enable_only_the_radio_off_layer(self):
        enabled = [l for l in system_files.system_preset("gpsd").splitlines() if l.startswith("enable ")]
        self.assertEqual(enabled, ["enable srrx-radio-off.service"])
        for unit in ("srrx.service", "srrx-poweroff.service", "inferd-htp.service"):
            self.assertIn("disable " + unit, system_files.system_preset("gpsd").splitlines())
        self.assertIn("disable srrx-menu.service", system_files.user_preset().splitlines())

    def test_documented_fixed_contents(self):
        self.assertEqual([l for l in system_files.gnss_blacklist().splitlines() if not l.startswith("#")],
                         ["blacklist gnss-usb", "blacklist gnss-ubx", "blacklist gnss-mtk", "blacklist gnss-sirf", "blacklist gnss-serial"])
        self.assertIn("HandlePowerKey=ignore\nIdleAction=ignore\n", system_files.logind_dropin())
        self.assertIn("[zram0]\nzram-size = 1024\n", system_files.zram())
        self.assertEqual(set(system_files.MASKED_UNITS) >= {"apt-daily.timer", "apt-daily-upgrade.timer", "fwupd-refresh.timer",
                                                            "ModemManager.service", "sleep.target", "suspend.target",
                                                            "hibernate.target", "hybrid-sleep.target"}, True)
        fastrpc = system_files.udev_fastrpc()
        self.assertIn('KERNEL=="fastrpc-*", GROUP="fastrpc", MODE="0660"', fastrpc)
        self.assertIn('SUBSYSTEM=="dma_heap", GROUP="fastrpc", MODE="0660"', fastrpc)
        self.assertIn('ATTR{name}=="pps-gnss.-1", SYMLINK+="pps-gnss"', system_files.udev_pps())
        # The source name follows the overlay node name (pps-gpio: "<pdev name>.<id>").
        self.assertIn("\tpps-gnss {\n\t\tcompatible = \"pps-gpio\";", (HERE / "system/dt/lab-q6a.dtso").read_text())
        polkit = system_files.polkit_radio_off()
        for action in system_files.NM_TX_ACTIONS:
            self.assertIn('"' + action + '"', polkit)
        self.assertIn("polkit.Result.NO", polkit)
        self.assertNotIn("Result.YES", polkit)
        tmp = system_files.tmpfiles()
        self.assertNotIn("/var/lib/srrx ", tmp)  # srrx.pass_jobs owns it; duplicates warn
        self.assertNotIn("/run/labd", tmp)  # receive-only build: no bias token directory

    def test_stage_refuses_unknown_accounts_and_collisions(self):
        accounts = tuple(a for a in system_files.SERVICE_ACCOUNTS if a[1] != "srrx-loc")
        with patch.object(system_files, "SERVICE_ACCOUNTS", accounts):
            with self.assertRaisesRegex(deploy.DeploymentError, "user:srrx-loc"):
                self.stage("unknown", devices())
        extra = dict(system_files.staged_files(None, "gpsd"), **{"etc/srrx/devices.template.json": "{}"})
        with patch.object(system_files, "staged_files", lambda config, gnss: extra):
            with self.assertRaisesRegex(deploy.DeploymentError, "collides"):
                self.stage("collision")

    def test_bundle_keeps_hooks_executable_and_everything_else_0644(self):
        self.stage("candidate", devices())
        output = self.root / "bundle.tar.gz"
        deploy.bundle(self.root / "candidate", output)
        with tarfile.open(output) as archive:
            modes = {m.name: m.mode for m in archive.getmembers() if m.isfile()}
        for hook in system_files.EXECUTABLES:
            self.assertEqual(modes[hook], 0o755)
        self.assertEqual({mode for name, mode in modes.items() if name not in system_files.EXECUTABLES}, {0o644})
        again = self.root / "again.tar.gz"
        deploy.bundle(self.root / "candidate", again)
        self.assertEqual(output.read_bytes(), again.read_bytes())


class EdidTests(unittest.TestCase):
    def test_committed_field_edid_equals_the_generator(self):
        self.assertEqual(edid_field.stale(), [])

    def test_two_documented_modes_only(self):
        data = edid_field.build()
        decoded = edid_field.decode(data)
        self.assertEqual(len(data), 128)
        self.assertEqual(sum(data) % 256, 0)
        self.assertEqual(decoded["version"], (1, 4))
        self.assertEqual(decoded["extensions"], 0)  # no CTA block: no CEA VIC
        self.assertEqual(decoded["established"], "000000")
        self.assertEqual(decoded["standard"], "01" * 16)
        self.assertFalse(decoded["continuous_frequency"])
        self.assertEqual([d["pixel_clock_khz"] for d in decoded["dtds"]], [151500, 127900])
        self.assertEqual(decoded["dtds"][0]["h"], (1920, 88, 44, 148))
        self.assertEqual(decoded["dtds"][0]["v"], (1080, 27, 5, 36))
        self.assertEqual(decoded["dtds"][1]["v"], (1080, 4, 5, 36))
        self.assertEqual(sorted(decoded["descriptors"]), [0x10, 0xFC])  # name + dummy, no range limits
        timings = [edid_field.check_timing(t) for t in edid_field.TIMINGS]
        self.assertEqual([(t["h_total"], t["v_total"]) for t in timings], [(2200, 1148), (2200, 1125)])
        self.assertEqual([t["line_khz"] for t in timings], [68.864, 58.136])
        self.assertEqual([t["refresh_hz"] for t in timings], [59.986, 51.677])  # kanshi @59.986Hz / @51.677Hz

    def test_banned_and_unclean_clocks_are_refused(self):
        for clock in (128700, 148500, 140000, 160000):
            timing = ("DTD2", clock, 1920, 88, 44, 148, 1080, 4, 5, 36)
            with self.assertRaises(edid_field.EdidError):
                edid_field.check_timing(timing)
        with self.assertRaises(edid_field.EdidError):
            edid_field.build(tuple(reversed(edid_field.TIMINGS)))

    def test_hook_embeds_the_field_edid_digest(self):
        hook = system_files.edid_hook()
        self.assertIn("copy_checked /usr/lib/firmware/edid/field.bin " + hashlib.sha256(edid_field.build()).hexdigest(), hook)
        self.assertTrue(hook.startswith("#!/bin/sh\n"))
        self.assertIn(". /usr/share/initramfs-tools/hook-functions", hook)


@unittest.skipUnless(SH, "initramfs hooks run under a POSIX sh")
class HookExecutionTests(unittest.TestCase):
    """The generated hooks against a fake hook-functions; real update-initramfs is a target step."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-hook-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "dest").mkdir()
        functions = self.root / "hook-functions"
        functions.write_text('copy_file() {\n\tmkdir -p "$(dirname "${DESTDIR}$3")"\n\t[ -e "${DESTDIR}$3" ] && return 1\n'
                             '\tcp "$2" "${DESTDIR}$3"\n}\n')
        self.functions = functions

    def run_hook(self, text):
        text = text.replace("/usr/share/initramfs-tools/hook-functions", str(self.functions))
        text = text.replace("/usr/lib/", str(self.root) + "/usr/lib/").replace(system_files.NPU_PHASE0, str(self.root) + "/phase0.env")
        hook = self.root / "hook"
        hook.write_text(text)
        return subprocess.run([SH, str(hook)], env={"DESTDIR": str(self.root / "dest"), "PATH": os.environ["PATH"]},
                              capture_output=True, text=True, timeout=30)

    def test_edid_hook_copies_only_the_reviewed_bytes(self):
        edid = self.root / "usr/lib/firmware/edid/field.bin"
        result = self.run_hook(system_files.edid_hook())
        self.assertEqual(result.returncode, 1, result.stderr)  # missing file fails the initramfs build
        edid.parent.mkdir(parents=True)
        edid.write_bytes(edid_field.build())
        result = self.run_hook(system_files.edid_hook())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "dest" / str(edid).lstrip("/")).read_bytes(), edid_field.build())
        shutil.rmtree(self.root / "dest")
        (self.root / "dest").mkdir()
        edid.write_bytes(edid_field.build()[:-1] + b"\x00")
        self.assertEqual(self.run_hook(system_files.edid_hook()).returncode, 1)

    def test_dsp_hook_is_inert_without_selection_and_checks_every_file(self):
        self.assertEqual(self.run_hook(system_files.dsp_hook()).returncode, 0)  # no Phase 0 record
        (self.root / "phase0.env").write_text("SRRX_DSP_FIRMWARE=radxa-firmware-qcs6490_0.2.42\n")
        self.assertEqual(self.run_hook(system_files.dsp_hook()).returncode, 0)  # its own package hook
        (self.root / "phase0.env").write_text("SRRX_DSP_FIRMWARE=unknown\n")
        self.assertEqual(self.run_hook(system_files.dsp_hook()).returncode, 1)
        (self.root / "phase0.env").write_text("SRRX_DSP_FIRMWARE=radxa-firmware-qcs6490_0.2.29\n")
        lock = system_files.dsp_lock()
        fake = {path: ("fixture " + path).encode() for path in lock["initramfs_files"]}
        for path, data in fake.items():
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_bytes(data)
        result = self.run_hook(system_files.dsp_hook())
        self.assertEqual(result.returncode, 1)  # fixture bytes are not the pinned firmware
        self.assertIn("differs from the reviewed SHA-256", result.stderr)
        pinned = dict(lock, initramfs_files={p: {"sha256": hashlib.sha256(d).hexdigest(), "size": len(d)} for p, d in fake.items()})
        with patch.object(system_files, "dsp_lock", lambda: pinned):
            result = self.run_hook(system_files.dsp_hook())
        self.assertEqual(result.returncode, 0, result.stderr)
        for path, data in fake.items():
            self.assertEqual((self.root / "dest" / str(self.root / path).lstrip("/")).read_bytes(), data)


class LockTests(unittest.TestCase):
    def test_dsp_lock_matches_the_documented_digests(self):
        lock = system_files.dsp_lock()
        self.assertEqual(lock["package"]["sha256"], "f59a5e5b14d95650c9d248ae223fa293b753530ebb46bb96e27e635b0f457e98")  # compute_os.md:139
        files = lock["initramfs_files"]
        prefix = "usr/lib/firmware/qcom/qcs6490/radxa/dragon-q6a/"
        self.assertTrue(files[prefix + "cdsp.mbn"]["sha256"].startswith("a9645c94"))  # STACK.md:862
        self.assertTrue(files[prefix + "adsp.mbn"]["sha256"].startswith("01fea794"))
        self.assertEqual(files[prefix + "adsp.mbn"]["size"], 9871840)
        self.assertIn("usr/lib/firmware/qcom/qcs6490/a660_zap.mbn", files)
        self.assertEqual({p for p in files if p.endswith(".jsn")}, {prefix + n for n in ("adspr.jsn", "adspua.jsn", "cdspr.jsn")})
        shells = lock["runtime_dsp_files"]
        self.assertTrue(shells["usr/lib/dsp/cdsp/fastrpc_shell_3"]["sha256"].startswith("d6ef508a"))  # STACK.md:862
        self.assertTrue(shells["usr/lib/dsp/cdsp/fastrpc_shell_unsigned_3"]["sha256"].endswith("3dff"))

    def test_hmi_lock_is_a_dependency_closed_subset_of_the_guest_wheelhouse(self):
        guest = {l.split("==")[0]: l for l in (HERE / "linux_lab/wheelhouse-requirements.txt").read_text().splitlines() if "==" in l}
        lines = [l for l in (PROJECT / "software/config/hmi-requirements.lock").read_text().splitlines() if l and not l.startswith("#")]
        names = {l.split("==")[0] for l in lines}
        self.assertTrue(all(guest.get(l.split("==")[0]) == l for l in lines))
        self.assertTrue({"numpy", "PySide6", "setuptools"} <= names)
        manifest = json.loads((HERE / "linux_lab/wheelhouse-manifest.json").read_text())
        requires = {w["name"]: w["requires_dist"] for w in manifest["wheels"]}
        for name in names:
            for requirement in requires[name]:
                if ";" in requirement:
                    continue  # environment-marked (python < 3.11 or extras)
                self.assertIn(re.split(r"[=<>! ]", requirement)[0], names, name + " needs " + requirement)
        documented = (PROJECT / "software/DEPLOYMENT.md").read_text(encoding="utf-8")
        self.assertIn("software/config/hmi-requirements.lock", documented)


class BuildManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-manifest-test-")
        self.addCleanup(self.temp.cleanup)
        self.prefix = Path(self.temp.name) / "prefix"
        (self.prefix / "lib").mkdir(parents=True)
        (self.prefix / "lib/rx.so").write_bytes(b"receive-only fixture module")
        (self.prefix / "bin").mkdir()
        (self.prefix / "bin/tool").write_bytes(b"fixture")
        (self.prefix / "evidence").mkdir()
        for name in ("audit.txt", "tx.txt"):
            (self.prefix / "evidence" / name).write_text("independent review evidence fixture, at least 32 bytes\n")

    def test_generated_manifest_is_open_and_verifies_only_after_review(self):
        manifest = build_manifest.generate(self.prefix, {"source_audit": "evidence/audit.txt", "tx_negative_tests": "evidence/tx.txt"})
        self.assertEqual(manifest["status"], "OPEN")
        self.assertEqual({manifest[k]["status"] for k in ("source_audit", "tx_negative_tests")}, {"OPEN"})
        self.assertEqual(manifest["allowed_modules"], ["lib/rx.so"])
        with self.assertRaisesRegex(deploy.DeploymentError, "OPEN"):
            deploy.verify_build(self.prefix, manifest)
        reviewed = json.loads(json.dumps(manifest))
        reviewed["status"] = "REVIEWED"
        for key in ("source_audit", "tx_negative_tests"):
            reviewed[key]["status"] = "PASS"
        self.assertEqual(deploy.verify_build(self.prefix, reviewed)["status"], "REVIEWED_BUILD_FILES_MATCH")
        (self.prefix / "bin/extra").write_bytes(b"unreviewed")
        with self.assertRaises(deploy.DeploymentError):
            deploy.verify_build(self.prefix, reviewed)

    def test_generator_refuses_what_verify_build_refuses(self):
        (self.prefix / "bin/rtl_tcp").write_bytes(b"TX/control tool fixture")
        with self.assertRaisesRegex(deploy.DeploymentError, "prohibited"):
            build_manifest.generate(self.prefix)
        (self.prefix / "bin/rtl_tcp").unlink()
        with self.assertRaises(deploy.DeploymentError):
            build_manifest.generate(self.prefix, {"source_audit": "../outside.txt"})

    def test_cli_writes_a_new_file_outside_the_prefix(self):
        output = Path(self.temp.name) / "manifest.json"
        self.assertEqual(build_manifest.main(["--prefix", str(self.prefix), "--output", str(output)]), 0)
        self.assertEqual(json.loads(output.read_text())["status"], "OPEN")
        with self.assertRaises(SystemExit):
            build_manifest.main(["--prefix", str(self.prefix), "--output", str(output)])
        with self.assertRaises(SystemExit):
            build_manifest.main(["--prefix", str(self.prefix), "--output", str(self.prefix / "inside.json")])


if __name__ == "__main__":
    unittest.main()
