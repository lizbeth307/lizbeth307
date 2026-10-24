"""Image recipe, A/B layout, boot chain and recovery kit: host tests without root or block devices.

The root-only paths (losetup, mkfs, chroot, the real r2 image) run in .github/workflows/sr-rx-image.yml.
Fixtures never represent an installed or accepted unit."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(HERE / "image"), str(HERE)]
import bootchain  # noqa: E402
import build_image  # noqa: E402
import layout as layoutlib  # noqa: E402
import recovery_kit  # noqa: E402

BASE = ("console=ttyMSM0,115200n8 rw earlycon consoleblank=0 console=tty1 coherent_pool=2M irqchip.gicv3_pseudo_nmi=0 "
        "cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory swapaccount=1 kasan=off")


def config(**changes):
    data = json.loads((HERE / "ab.template.json").read_text())
    data.update(esp_partuuid="0a0a0a0a-0000-4000-8000-000000000001", root_a_partuuid="0a0a0a0a-0000-4000-8000-00000000000a",
                root_b_partuuid="0a0a0a0a-0000-4000-8000-00000000000b", base_cmdline_without_root=BASE,
                rescue={"kernel": "/RadxaOS/6.18.2-3-qcom/linux", "initrd": "/RadxaOS/6.18.2-3-qcom/initrd.img-6.18.2-3-qcom", "dtb": None})
    data.update(changes)
    return data


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.layout = layoutlib.load()
        self.ids = layoutlib.identifiers(self.layout)

    def test_committed_layout_is_the_stack_plan_on_4k_sectors(self):
        sizes = {p["role"]: p["size_bytes"] for p in self.layout["partitions"]}
        self.assertEqual(self.layout["sector_size"], 4096)
        self.assertEqual(sizes, {"esp": 1 << 30, "root_a": 22 << 30, "root_b": 22 << 30, "data": None})
        self.assertEqual(self.layout["partitions"][0]["type_guid"], "C12A7328-F81F-11D2-BA4B-00A0C93EC93B")
        geo = layoutlib.geometry(self.layout)
        self.assertEqual(geo["partitions"]["esp"], {"start": 256, "size": 262144})
        self.assertEqual(geo["partitions"]["root_a"]["start"], 256 + 262144)
        self.assertEqual(geo["partitions"]["root_b"]["size"], 22 << 30 >> 12)
        self.assertEqual(geo["total_bytes"] % (1 << 20), 0)
        last = geo["partitions"]["data"]["start"] + geo["partitions"]["data"]["size"] - 1
        self.assertLessEqual(last, geo["last_usable_lba"])
        self.assertGreaterEqual(geo["total_sectors"] - 1 - geo["last_usable_lba"], 5)  # backup entries + header

    def test_identifiers_are_derived_distinct_and_reproducible(self):
        again = layoutlib.identifiers(layoutlib.load())
        self.assertEqual(self.ids, again)
        values = [self.ids["disk_guid"], *self.ids["partuuid"].values(), *self.ids["fs_uuid"].values()]
        self.assertEqual(len(set(values)), len(values))
        self.assertNotEqual(self.ids["fs_uuid"]["root_a"], self.ids["fs_uuid"]["root_b"])  # new FS UUID on slot B
        self.assertNotEqual(layoutlib.identifiers(self.layout, "unit-0042")["partuuid"], self.ids["partuuid"])
        self.assertRegex(self.ids["esp_volume_id"], r"^[0-9A-F]{8}$")

    def test_sfdisk_script_and_mkfs_use_the_derived_values(self):
        script = layoutlib.sfdisk_script(self.layout, self.ids)
        self.assertIn("label: gpt\n", script)
        self.assertIn("label-id: " + self.ids["disk_guid"].upper(), script)
        self.assertIn('uuid=' + self.ids["partuuid"]["root_b"].upper() + ', name="srrx-root-b"', script)
        self.assertEqual(script.count("start="), 4)
        cmds = layoutlib.mkfs_commands(self.layout, self.ids, {r: "/dev/loop9p%d" % i for i, r in enumerate(layoutlib.ROLES, 1)})
        self.assertEqual(cmds["esp"][:5], ["mkfs.vfat", "-F", "32", "-S", "4096"])
        self.assertIn(self.ids["fs_uuid"]["root_b"], cmds["root_b"])
        self.assertNotIn("quota,project", cmds["data"])
        self.assertIn("quota,project", layoutlib.mkfs_commands(self.layout, self.ids, {r: "x" for r in layoutlib.ROLES}, quota=True)["data"])

    def test_fstab_per_slot_differs_only_in_the_root_line(self):
        a, b = layoutlib.fstab(self.layout, self.ids, "A"), layoutlib.fstab(self.layout, self.ids, "B")
        self.assertIn("PARTUUID=" + self.ids["partuuid"]["root_a"] + "\t/\text4", a)
        self.assertNotIn(self.ids["partuuid"]["root_b"], a)
        self.assertIn("PARTUUID=" + self.ids["partuuid"]["esp"] + "\t/boot/efi\tvfat", b)
        self.assertIn("/data/srrx-cache\t/srv/srrx-cache\tnone\tbind,ro,", b)
        diff = [line for line in set(a.splitlines()) ^ set(b.splitlines())]
        self.assertEqual(len(diff), 4)  # header comment and root line of each slot

    def test_invalid_layouts_are_refused(self):
        for change in (lambda l: l.update(sector_size=512),
                       lambda l: l["partitions"][2].update(size_bytes=21 << 30),
                       lambda l: l["partitions"][0].update(type_guid="0FC63DAF-8483-4772-8E79-3D69D8477DE4"),
                       lambda l: l["partitions"][3].update(size_bytes=1 << 30),
                       lambda l: l["partitions"].reverse(),
                       lambda l: l["binds"][0].update(options="bind,rw"),
                       lambda l: l.update(status="REVIEWED")):
            broken = copy.deepcopy(self.layout)
            change(broken)
            with self.assertRaises(layoutlib.LayoutError):
                layoutlib.validate(broken)


class CmdlineTests(unittest.TestCase):
    def test_video_at_sign_passes_the_per_token_allowlist(self):
        line = bootchain.cmdline(BASE, "0a0a0a0a-0000-4000-8000-00000000000a")
        self.assertTrue(line.startswith(BASE + " root=PARTUUID=0a0a0a0a-0000-4000-8000-00000000000a preempt=full "))
        self.assertIn(" video=HDMI-A-1:1920x1080@60 ", line)
        self.assertTrue(line.endswith("irqaffinity=0-6"))
        self.assertNotIn("isolcpus", bootchain.cmdline(BASE, "0a0a0a0a-0000-4000-8000-00000000000a", lime_build=False))

    def test_unsafe_or_incomplete_base_lines_are_refused(self):
        for bad in ('console=ttyMSM0 rw quiet="x"', "console=ttyMSM0  rw earlycon", "console=ttyMSM0 rw earlycon clk_ignore_unused",
                    "root=UUID=abc console=ttyMSM0 rw earlycon", "rw earlycon", "console=ttyMSM0 rw earlycon panic=30",
                    "console=ttyMSM0 rw earlycon $(reboot)", "console=ttyMSM0 rw earlycon\n", BASE + " preempt=full"):
            with self.assertRaises(bootchain.BootChainError, msg=bad):
                bootchain.validate_base(bad)
        with self.assertRaises(bootchain.BootChainError):
            bootchain.cmdline(BASE, "0A0A0A0A-0000-4000-8000-00000000000A")

    def test_strip_root_keeps_every_other_observed_token(self):
        self.assertEqual(bootchain.strip_root("root=UUID=711cd5de console=ttyMSM0,115200n8 rw earlycon\n"), "console=ttyMSM0,115200n8 rw earlycon")
        with self.assertRaises(bootchain.BootChainError):
            bootchain.strip_root("root=a root=b console=x rw")


class EntryTests(unittest.TestCase):
    def test_golden_route_a_entries(self):
        files = bootchain.entries(config())
        self.assertEqual(sorted(files), ["loader/entries/labA-rescue.conf", "loader/entries/labA.conf", "loader/entries/labB-rescue.conf",
                                         "loader/entries/labB.conf", "loader/loader.conf"])
        self.assertIn("version 2\n", files["loader/entries/labA.conf"])
        self.assertIn("version 1\n", files["loader/entries/labB.conf"])
        self.assertIn("sort-key srrx\n", files["loader/entries/labB.conf"])
        rescue = files["loader/entries/labB-rescue.conf"]
        self.assertIn("sort-key srrx-rescue\n", rescue)
        self.assertNotIn("devicetree", rescue)  # r2 entries use the firmware DTB
        self.assertNotIn("preempt=full", rescue)
        self.assertIn("root=PARTUUID=0a0a0a0a-0000-4000-8000-00000000000b", rescue)

    def test_route_a_trial_is_newest_with_tries_and_route_b_writes_back(self):
        files = bootchain.entries(config(trial_slot="B"), tries=3)
        self.assertIn("version 3\n", files["loader/entries/labB+3.conf"])
        self.assertNotIn(bootchain.TRIAL_MARK, files)
        b = bootchain.entries(config(route="B", trial_slot="B"))
        self.assertIn("loader/entries/labB.conf", b)  # embloader: no counter in the name
        self.assertEqual(b["loader/loader.conf"], "default labB\ntimeout 3\neditor no\n")
        self.assertEqual(b[bootchain.TRIAL_MARK], "B\n")
        self.assertEqual(bootchain.entries(config(route="B"))["loader/loader.conf"], "default labA\ntimeout 3\neditor no\n")

    def test_schema_errors(self):
        for change in ({"trial_slot": "A"}, {"dt_profile": "home"}, {"route": "C"}, {"kernel_version": "latest"},
                       {"esp_partuuid": "0a0a0a0a-0000-4000-8000-00000000000a"},
                       {"rescue": {"kernel": "/srrx/A/linux", "initrd": "/x/initrd", "dtb": None}},
                       {"slots": {"A": {"kernel": "/srrx/A/linux", "initrd": "/srrx/A/i", "lab_dtb": "/srrx/A/../B/l", "field_dtb": "/srrx/A/f"},
                                  "B": config()["slots"]["B"]}}):
            with self.assertRaises(bootchain.BootChainError, msg=str(change)):
                bootchain.validate_ab(config(**change))


class PluginTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-image-test-")
        self.addCleanup(self.temp.cleanup)
        root = self.root = Path(self.temp.name)
        self.esp = root / "esp"
        (self.esp / "loader/entries").mkdir(parents=True)
        self.cfg = config()
        (root / "boot.json").write_text(json.dumps(self.cfg))
        (root / "slot").write_text("A\n")
        (root / "tries").write_text("3\n")
        (root / "cmdline").write_text(bootchain.cmdline(BASE, self.cfg["root_a_partuuid"]) + "\n")
        (root / "vmlinuz").write_bytes(b"kernel")
        (root / "initrd").write_bytes(b"initrd")
        store = root / "dtb" / "6.18.2-4-qcom"
        store.mkdir(parents=True)
        record = {}
        for profile in ("lab", "field"):
            (store / (profile + ".dtb")).write_bytes(profile.encode())
            record[profile] = {"merged": False, "sha256": hashlib.sha256(profile.encode()).hexdigest()}
        (store / "dtb.json").write_text(json.dumps(record))
        patcher = patch.object(bootchain, "_is_mountpoint", lambda p: Path(p) == self.esp)
        patcher.start()
        self.addCleanup(patcher.stop)

    def plugin(self, *args, **kw):
        r = self.root
        return bootchain.kernel_install(list(args), esp=self.esp, config_path=r / "boot.json", slot_path=r / "slot",
                                        cmdline_path=r / "cmdline", tries_path=r / "tries", dtb_store=r / "dtb", **kw)

    def test_refuses_the_unmerged_package_dtb_unless_the_ci_flag_is_set(self):
        add = ("add", "6.18.2-4-qcom", "/unused", str(self.root / "vmlinuz"), str(self.root / "initrd"))
        with self.assertRaisesRegex(bootchain.BootChainError, "without the SR-RX overlay"):
            self.plugin(*add)
        with patch.dict(os.environ, {"SRRX_ALLOW_UNMERGED_DTB": "1"}):
            self.assertEqual(self.plugin(*add), 0)
        entry = (self.esp / "loader/entries/labA+3.conf").read_text()
        self.assertIn("version 1\n", entry)
        self.assertEqual((self.esp / "srrx/A/initrd.img").read_bytes(), b"initrd")
        self.assertEqual((self.esp / "srrx/A/lab.dtb").read_bytes(), b"lab")
        (self.esp / "loader/entries/labB.conf").write_text("version 4\n")
        with patch.dict(os.environ, {"SRRX_ALLOW_UNMERGED_DTB": "1"}):
            self.plugin(*add)
        self.assertEqual(sorted(p.name for p in (self.esp / "loader/entries").iterdir()), ["labA+3.conf", "labB.conf"])
        self.assertIn("version 5\n", (self.esp / "loader/entries/labA+3.conf").read_text())

    def test_other_kernels_are_ignored_and_a_foreign_cmdline_is_refused(self):
        self.assertEqual(self.plugin("add", "7.0.11-7-qcom", "/unused", str(self.root / "vmlinuz")), 0)
        self.assertEqual(list((self.esp / "loader/entries").iterdir()), [])
        (self.root / "cmdline").write_text(bootchain.cmdline(BASE, self.cfg["root_b_partuuid"]) + "\n")
        with self.assertRaisesRegex(bootchain.BootChainError, "differs"):
            self.plugin("add", "6.18.2-4-qcom", "/unused", str(self.root / "vmlinuz"), str(self.root / "initrd"))
        self.assertEqual(self.plugin("remove", "6.18.2-4-qcom", "/unused"), 0)

    def test_golden_entries_replace_foreign_entries(self):
        for slot in ("A", "B"):
            for name in ("linux", "initrd.img", "lab.dtb", "field.dtb"):
                (self.esp / "srrx" / slot).mkdir(parents=True, exist_ok=True)
                (self.esp / "srrx" / slot / name).write_bytes(b"x")
        for name in ("linux", "initrd.img-6.18.2-3-qcom"):
            (self.esp / "RadxaOS/6.18.2-3-qcom").mkdir(parents=True, exist_ok=True)
            (self.esp / "RadxaOS/6.18.2-3-qcom" / name).write_bytes(b"r")
        (self.esp / "loader/entries/RadxaOS-6.18.2-3-qcom.conf").write_text("title r2\n")
        (self.esp / "loader/entries/labA+3.conf").write_text("version 1\n")
        result = bootchain.golden_entries(self.esp, self.root / "boot.json")
        self.assertEqual(result["removed_foreign_entries"], ["RadxaOS-6.18.2-3-qcom.conf", "labA+3.conf"])
        self.assertEqual((self.esp / "loader/loader.conf").read_text(), "default lab*\ntimeout 3\neditor no\n")

    def test_route_b_commit_and_failed_trial(self):
        cfg = config(route="B")
        (self.root / "boot.json").write_text(json.dumps(cfg))
        (self.esp / "srrx/ab").mkdir(parents=True)
        (self.esp / "srrx/ab/trial").write_text("A\n")
        (self.esp / "srrx/ab/booting").write_text("")
        result = bootchain.route_b_commit(self.esp, self.root / "boot.json", self.root / "slot")
        self.assertEqual(result["status"], "TRIAL_COMMITTED")
        self.assertEqual((self.esp / "loader/loader.conf").read_text(), "default labA\ntimeout 3\neditor no\n")
        self.assertFalse((self.esp / "srrx/ab/trial").exists())
        (self.esp / "srrx/ab/trial").write_text("B\n")
        result = bootchain.route_b_commit(self.esp, self.root / "boot.json", self.root / "slot")
        self.assertEqual(result["status"], "TRIAL_FAILED_FALLBACK_RUNNING")
        self.assertTrue((self.esp / "srrx/ab/failed-B").is_file())

    @unittest.skipUnless(shutil.which("sh") and os.name == "posix", "POSIX sh")
    def test_route_b_initramfs_script_writes_the_default_back_once(self):
        cfg = config(route="B")
        (self.root / "boot.json").write_text(json.dumps(cfg))
        conf = self.root / "srrx-ab.conf"
        conf.write_text(bootchain.initramfs_env(self.root / "boot.json"))
        (self.esp / "srrx/ab").mkdir(parents=True)
        (self.esp / "srrx/ab/trial").write_text("B\n")
        (self.esp / "loader/loader.conf").write_text("default labB\ntimeout 3\neditor no\n")
        env = dict(os.environ, SRRX_AB_CONF=str(conf), SRRX_AB_ESP_DIR=str(self.esp), SRRX_AB_NO_MOUNT="1",
                   SRRX_AB_CMDLINE=bootchain.cmdline(BASE, cfg["root_b_partuuid"]))
        script = HERE / "image/files/initramfs-srrx-ab-writeback"
        subprocess.run(["sh", str(script)], env=env, check=True, capture_output=True)
        self.assertEqual((self.esp / "loader/loader.conf").read_text(), "default labA\ntimeout 3\neditor no\n")
        self.assertTrue((self.esp / "srrx/ab/booting").exists())
        (self.esp / "loader/loader.conf").write_text("default labB\ntimeout 3\neditor no\n")
        subprocess.run(["sh", str(script)], env=env, check=True, capture_output=True)  # second boot: already written back
        self.assertEqual((self.esp / "loader/loader.conf").read_text(), "default labB\ntimeout 3\neditor no\n")
        env["SRRX_AB_CMDLINE"] = bootchain.cmdline(BASE, cfg["root_a_partuuid"])
        (self.esp / "srrx/ab/booting").unlink()
        subprocess.run(["sh", str(script)], env=env, check=True, capture_output=True)  # the other slot: no write-back
        self.assertFalse((self.esp / "srrx/ab/booting").exists())


class RecipeTests(unittest.TestCase):
    def test_recipe_names_locked_artifacts_and_shipped_files(self):
        recipe = json.loads((HERE / "image/recipe.json").read_text())
        lock = json.loads((HERE / "sources.lock.json").read_text())
        ids = {a["id"] for a in lock["artifacts"]}
        self.assertIn(recipe["base_artifact"], ids)
        self.assertTrue(set(recipe["kernel_artifacts"]) <= ids)
        self.assertEqual(recipe["kernel_version"], lock["target"]["kernel"])
        self.assertTrue({"linux-image-6.18.2-4-qcom", "systemd-boot", "systemd-boot-efi"} <= set(recipe["holds"]["names"]))
        for route in ("A", "B"):
            for unit in recipe["routes"][route]["enable"]:
                self.assertTrue((HERE / "image/files" / unit).is_file(), unit)
        self.assertIn("srrx-radio-off.service", recipe["enable_common"]["units"])  # written by deploy.stage (radio_off_unit)
        self.assertEqual(build_image.plan()["steps"][0]["id"], "inputs")
        self.assertEqual(build_image.plan("B")["route_recipe"]["embloader_version"], "0.4")

    def test_boot_units_gate_boot_complete_and_call_the_shipped_module(self):
        check = (HERE / "image/files/srrx-boot-check.service").read_text()
        self.assertIn("\nBefore=boot-complete.target", check)
        self.assertIn("\nRequiredBy=boot-complete.target", check)
        self.assertIn("/opt/srrx/deployment/image/bootchain.py boot-check", check)
        plugin = (HERE / "image/files/90-srrx-bls.install").read_text()
        self.assertIn("/opt/srrx/deployment/image/bootchain.py kernel-install", plugin)
        self.assertIn("layout=other", (HERE / "image/files/install.conf").read_text())

    def test_builder_refuses_hosts_and_devices(self):
        if not (sys.platform == "linux" and os.geteuid() == 0):  # host tests never run as root
            with self.assertRaises(build_image.BuildError):
                build_image.require_builder()
        for path in ("/dev/sda", "/dev/mmcblk0", "/dev/nvme0n1", "/dev/disk/by-id/ufs-x", "/dev/mapper/x"):
            with self.assertRaises(build_image.BuildError):
                build_image.refuse_block_path(path)
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaises(build_image.BuildError):
                build_image.new_regular_file(Path(work).parent / "outside.img", work)
            (Path(work) / "exists.img").write_bytes(b"")
            with self.assertRaises(build_image.BuildError):
                build_image.new_regular_file(Path(work) / "exists.img", work)

    def test_rescue_entry_is_taken_from_the_r2_entry_of_its_own_kernel(self):
        esp = {"entries": {"RadxaOS-6.18.2-3-qcom.conf": "# BLS\ntitle Ubuntu\nversion 6.18.2-3-qcom\nlinux /RadxaOS/6.18.2-3-qcom/linux\n"
                                                         "initrd /RadxaOS/6.18.2-3-qcom/initrd.img-6.18.2-3-qcom\noptions root=UUID=x\n"}}
        rescue = build_image.rescue_from_esp(esp, {})
        self.assertEqual((rescue["status"], rescue["kernel"], rescue["dtb"]), ("IDENTIFIED", "/RadxaOS/6.18.2-3-qcom/linux", None))
        self.assertEqual(build_image.rescue_from_esp({"entries": {}}, {})["status"], "NOT_IDENTIFIED")

    def test_staged_tree_carries_the_boot_chain_module(self):
        import deploy
        with tempfile.TemporaryDirectory() as temp:
            deploy.stage(Path(temp) / "stage")
            rootfs = Path(temp) / "stage/rootfs/opt/srrx/deployment/image"
            for name in ("bootchain.py", "layout.py", "recovery_kit.py", "files/90-srrx-bls.install"):
                self.assertTrue((rootfs / name).is_file(), name)


@unittest.skipUnless(hasattr(os, "SEEK_DATA") and sys.platform == "linux", "sparse-file extents need Linux SEEK_DATA")
class RecoveryKitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-kit-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / "golden.img"
        with open(self.image, "wb") as handle:
            handle.truncate(64 << 20)
            for offset in (0, 8 << 20, (64 << 20) - 8192):
                handle.seek(offset)
                handle.write(os.urandom(8192))

    def test_map_assemble_verify_and_tamper(self):
        data = recovery_kit.make_map(self.image)
        self.assertEqual(data["image_bytes"], 64 << 20)
        self.assertLess(data["data_bytes"], 16 << 20)  # holes stay holes
        mapping = self.root / "golden.img.map.json"
        mapping.write_text(json.dumps(data))
        self.assertEqual(recovery_kit.verify_extents(self.image, recovery_kit.load_map(mapping)), [])
        kit = recovery_kit.assemble(self.image, mapping, self.root / "kit")
        self.assertIn("bios-260120", kit["missing"])
        self.assertEqual(recovery_kit.verify_kit(self.root / "kit")["status"], "KIT_VERIFIED")
        with open(self.root / "kit/golden/golden.img", "r+b") as handle:
            handle.seek(8 << 20)
            handle.write(b"\0" * 16)
        self.assertEqual(recovery_kit.verify_kit(self.root / "kit")["status"], "BLOCKED")

    def test_write_targets_are_refused_before_any_open(self):
        data = recovery_kit.make_map(self.image)
        for target, loop in (("/dev/sda", False), (str(self.image), False), ("/dev/disk/by-id/../../sda", False), ("/dev/sda", True)):
            with self.assertRaises((recovery_kit.KitError, OSError)):
                recovery_kit.check_target(target, data, self.image, test_loop=loop)

    def test_malformed_maps_are_refused(self):
        data = recovery_kit.make_map(self.image)
        for change in (lambda d: d.update(sector_size=512), lambda d: d["extents"].append([0, 10, "0" * 64]),
                       lambda d: d.update(image_bytes=10), lambda d: d.update(format="bmap")):
            broken = copy.deepcopy(data)
            change(broken)
            path = self.root / "bad.json"
            path.write_text(json.dumps(broken))
            with self.assertRaises(recovery_kit.KitError):
                recovery_kit.load_map(path)


if __name__ == "__main__":
    unittest.main()
