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
        for role in ("root_a", "root_b", "data"):  # zeroed in the file (as holes); the map forces the journal blocks
            self.assertIn(",lazy_journal_init=0", cmds[role][cmds[role].index("-E") + 1])
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
        if not (r / "proc_cmdline").exists():  # a builder chroot: the host's root, not one of the slots
            (r / "proc_cmdline").write_text("BOOT_IMAGE=/vmlinuz root=PARTUUID=0b0b0b0b-0000-4000-8000-000000000001 ro\n")
        return bootchain.kernel_install(list(args), esp=self.esp, config_path=r / "boot.json", slot_path=r / "slot",
                                        cmdline_path=r / "cmdline", tries_path=r / "tries", dtb_store=r / "dtb",
                                        proc_cmdline=r / "proc_cmdline", **kw)

    def test_running_slot_is_replaced_only_as_a_trial_with_fallback(self):
        add = ("add", "6.18.2-4-qcom", "/unused", str(self.root / "vmlinuz"), str(self.root / "initrd"))
        (self.root / "proc_cmdline").write_text(bootchain.cmdline(BASE, self.cfg["root_a_partuuid"]) + " initrd=\\srrx\\A\\initrd.img\n")
        with patch.dict(os.environ, {"SRRX_ALLOW_UNMERGED_DTB": "1"}):
            self.assertEqual(self.plugin(*add), 0)  # Route A: counted +3 trial, the other slot is the fallback
            self.assertTrue((self.esp / "loader/entries/labA+3.conf").is_file())
            (self.root / "tries").unlink()
            with self.assertRaisesRegex(bootchain.BootChainError, "no fallback"):
                self.plugin(*add)
            (self.root / "boot.json").write_text(json.dumps(config(route="B")))
            (self.esp / "srrx/A").mkdir(parents=True, exist_ok=True)
            (self.esp / "srrx/A/initrd.img").write_bytes(b"known good")
            with self.assertRaisesRegex(bootchain.BootChainError, "arm a trial"):
                self.plugin(*add)
            self.assertEqual((self.esp / "srrx/A/initrd.img").read_bytes(), b"known good")  # refused before any write
            (self.esp / "srrx/ab").mkdir(parents=True)
            (self.esp / "srrx/ab/trial").write_text("A\n")
            (self.esp / "srrx/ab/booting").write_text("")
            (self.esp / "loader/loader.conf").write_text("default labB\ntimeout 3\neditor no\n")
            self.assertEqual(self.plugin(*add), 0)
            self.assertEqual((self.esp / "loader/loader.conf").read_text(), "default labA\ntimeout 3\neditor no\n")
            self.assertFalse((self.esp / "srrx/ab/booting").exists())  # the next boot writes the default back to B
            self.assertTrue((self.esp / "loader/entries/labA.conf").is_file())
            (self.root / "slot").write_text("B\n")  # the other root in a chroot while A runs: a plain install
            (self.root / "cmdline").write_text(bootchain.cmdline(BASE, self.cfg["root_b_partuuid"]) + "\n")
            (self.esp / "srrx/ab/trial").unlink()
            self.assertEqual(self.plugin(*add), 0)
        (self.root / "proc_cmdline").unlink()
        with patch.object(bootchain, "running_slot_root", lambda *a: None), patch.dict(os.environ, {"SRRX_ALLOW_UNMERGED_DTB": "1"}):
            with self.assertRaisesRegex(bootchain.BootChainError, "unreadable"):
                self.plugin(*add)

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
        def unique(items):
            keys = [k for k, _ in items]
            self.assertEqual(len(keys), len(set(keys)), "duplicate JSON key in recipe.json")
            return dict(items)
        for name in ("recipe.json", "partition-layout.json"):
            json.loads((HERE / "image" / name).read_text(), object_pairs_hook=unique)
        recipe = json.loads((HERE / "image/recipe.json").read_text())
        self.assertTrue(set(recipe["kernel_debs_install"]["artifacts"]) < set(recipe["kernel_artifacts"]))
        self.assertNotIn("linux-libc-dev-radxa-dragon-q6a", recipe["kernel_debs_install"]["artifacts"])  # build/07:68-69
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


class SmokeModelTests(unittest.TestCase):
    """smoke_qemu.check: the QEMU expectations themselves (the boots run in sr-rx-image.yml)."""

    def setUp(self):
        import smoke_qemu
        self.smoke = smoke_qemu
        self.recipe = json.loads((HERE / "image/recipe.json").read_text())

    def report(self, slot, ok, boot_complete, bless, bless_status, rows=None, selftest=True, numpy=True):
        units = {"srrx-boot-check.service": {"ActiveState": "active" if ok else "failed"},
                 "boot-complete.target": {"ActiveState": boot_complete}, "systemd-bless-boot.service": {"ActiveState": bless},
                 "srrx.service": {"ActiveState": "inactive", "UnitFileState": "disabled"}}
        report = {"boot_check": {"slot": slot, "status": "BOOT_SELF_CHECK_OK" if ok else "BLOCKED"}, "units": units,
                  "bless_boot_status": bless_status, "pending_jobs": [],
                  "masked_units": {u: {"LoadState": "masked"} for u in self.recipe["mask"]["units"]}}
        if selftest:
            report["selftest"] = {"status": "FAIL", "interpreter_numpy": numpy,
                                  "fail_or_blocked_rows": rows if rows is not None else {"RX-16": ["lab_pref_missing"]}}
        return report

    def run_check(self, index, report, entries):
        name, expect = self.smoke.SCENARIOS[index]
        result = {"qemu_exit": 0, "report": report, "entries_after": entries}
        return self.smoke.check(name, result, expect, {"RX-16": ["lab_pref_missing"]})

    def test_expected_boots_pass(self):
        blessed = sorted(["labA.conf", "labB.conf", "labA-rescue.conf", "labB-rescue.conf"])
        bad_b = sorted(["labA.conf", "labB+0-1.conf", "labA-rescue.conf", "labB-rescue.conf"])
        self.assertEqual([s[1]["selftest"] for s in self.smoke.SCENARIOS], [True, False, False])  # once: about 17 min under TCG
        self.assertEqual(self.run_check(0, self.report("A", True, "active", "active", "good"), blessed)["status"], "MODEL_PASS")
        self.assertEqual(self.run_check(1, self.report("B", False, "inactive", "inactive", "indeterminate", selftest=False), bad_b)["status"],
                         "MODEL_PASS")
        self.assertEqual(self.run_check(2, self.report("A", True, "inactive", "inactive", "clean", selftest=False), bad_b)["status"], "MODEL_PASS")
        stray = self.run_check(2, self.report("A", True, "inactive", "inactive", "clean"), bad_b)
        self.assertEqual(stray["mismatches"], ["selftest ran on a boot that does not ask for it"])

    def test_interpreter_rows_are_expected_only_without_numpy(self):
        # CI 2026-11-06: the image's python3 has no numpy, so RX-14 and RX-04-bb block live but passed at build time.
        blessed = sorted(["labA.conf", "labB.conf", "labA-rescue.conf", "labB-rescue.conf"])
        live = {"RX-14": ["numpy_unavailable"], "RX-04-bb": ["numpy_unavailable"], "RX-16": ["lab_pref_missing"]}
        cases = ((live, False, "MODEL_PASS"), (live, True, "MODEL_FAIL"), ({"RX-16": ["lab_pref_missing"]}, False, "MODEL_FAIL"),
                 ({"RX-14": ["numpy_unavailable"], "RX-16": ["lab_pref_missing"]}, False, "MODEL_FAIL"),  # RX-04-bb missing
                 ({"RX-14": ["voice_residual_above_noise"], "RX-04-bb": ["numpy_unavailable"], "RX-16": ["lab_pref_missing"]}, False,
                  "MODEL_FAIL"),
                 ({"RX-16": ["lab_pref_missing"]}, True, "MODEL_PASS"))
        for rows, numpy, status in cases:
            report = self.report("A", True, "active", "active", "good", rows=rows, numpy=numpy)
            self.assertEqual(self.run_check(0, report, blessed)["status"], status, (rows, numpy))

    def test_entry_plan_keeps_the_blessed_name_and_runs_the_selftest_once(self):
        cfg = bootchain.validate_ab(config())
        plans = self.smoke.entry_plan(cfg)
        with tempfile.TemporaryDirectory() as temp:
            entries = Path(temp)
            for name in ("labA.conf", "labB.conf", "labA-rescue.conf", "labB-rescue.conf"):
                (entries / name).write_text("golden\n")
            self.smoke.apply_entry_plan(entries, plans[0])
            self.assertEqual(sorted(p.name for p in entries.glob("lab*.conf")),
                             sorted(["labA+3.conf", "labB.conf", "labA-rescue.conf", "labB-rescue.conf"]))
            self.assertIn(" --selftest\"", (entries / "labA+3.conf").read_text())
            self.assertNotIn("--selftest", (entries / "labB.conf").read_text())
            self.assertEqual((entries / "labA-rescue.conf").read_text(), "golden\n")
            os.replace(entries / "labA+3.conf", entries / "labA.conf")  # what systemd-bless-boot does on a good boot
            self.smoke.apply_entry_plan(entries, plans[1])
            self.assertIn("version 4\n", (entries / "labB+1.conf").read_text())
            self.assertNotIn(self.smoke.BROKEN_TOKEN, (entries / "labB+1.conf").read_text())
            self.assertFalse((entries / "labB.conf").exists())
            os.replace(entries / "labB+1.conf", entries / "labB+0-1.conf")  # systemd-boot counted the only try down
            self.smoke.apply_entry_plan(entries, plans[2])
            self.assertEqual(sorted(p.name for p in entries.glob("lab*.conf")),
                             sorted(["labA.conf", "labB+0-1.conf", "labA-rescue.conf", "labB-rescue.conf"]))
            self.assertNotIn("--selftest", (entries / "labA.conf").read_text())
            self.assertIn("version 3\n", (entries / "labA.conf").read_text())
            (entries / "labA.conf").unlink()  # scenario 1 did not bless: scenario 3 creates nothing
            self.smoke.apply_entry_plan(entries, plans[2])
            self.assertFalse((entries / "labA.conf").exists())

    def test_the_failure_of_the_first_ci_run_is_a_model_fail(self):
        # 24.10.2026: systemd.run= alone never queued boot-complete.target, so nothing was blessed.
        entries = sorted(["labA+2-1.conf", "labB.conf", "labA-rescue.conf", "labB-rescue.conf"])
        result = self.run_check(0, self.report("A", True, "inactive", "inactive", "indeterminate"), entries)
        self.assertEqual(result["status"], "MODEL_FAIL")
        self.assertTrue(any(m.startswith("entries_after") for m in result["mismatches"]))
        self.assertTrue(any(m.startswith("boot_complete") for m in result["mismatches"]))

    def test_failed_units_beyond_the_expected_one_fail(self):
        blessed = sorted(["labA.conf", "labB.conf", "labA-rescue.conf", "labB-rescue.conf"])
        bad_b = sorted(["labA.conf", "labB+0-1.conf", "labA-rescue.conf", "labB-rescue.conf"])
        report = self.report("A", True, "active", "active", "good")
        report["failed_units"] = ["nmbd.service loaded failed failed Samba NMB Daemon"]  # CI 2026-11-06, before the samba masks
        self.assertEqual(self.run_check(0, report, blessed)["mismatches"], ["failed units: nmbd.service"])
        report = self.report("B", False, "inactive", "inactive", "indeterminate", selftest=False)
        report["failed_units"] = ["srrx-boot-check.service loaded failed failed SR-RX boot self-check"]
        self.assertEqual(self.run_check(1, report, bad_b)["status"], "MODEL_PASS")  # the expected failure of scenario 2
        report = self.report("A", True, "inactive", "inactive", "clean", selftest=False)
        report["failed_units"] = ["srrx-boot-check.service loaded failed failed SR-RX boot self-check"]
        self.assertIn("failed units: srrx-boot-check.service", self.run_check(2, report, bad_b)["mismatches"])

    def test_a_failed_boot_check_unit_carries_its_journal_and_accounts_are_compared(self):
        # Run 42300813861, attempt 1: the unit failed in scenario 1 while the post-boot check passed, with no journal.
        blessed = sorted(["labA.conf", "labB.conf", "labA-rescue.conf", "labB-rescue.conf"])
        report = self.report("A", True, "active", "active", "good")
        report["units"]["srrx-boot-check.service"] = {"ActiveState": "failed", "Result": "exit-code", "ExecMainStatus": "1"}
        report["boot_check_journal"] = '{"status": "BLOCKED", "issues": ["installed package inventory unavailable (dpkg-query exit -1)"]}'
        mismatches = self.run_check(0, report, blessed)["mismatches"]
        self.assertIn("srrx-boot-check.service 'failed', expected 'active'", mismatches)
        self.assertTrue(any(m.startswith("srrx-boot-check journal: ") and "dpkg-query exit -1" in m for m in mismatches), mismatches)
        name, expect = self.smoke.SCENARIOS[0]
        recorded = {"labd": {"kind": "u", "uid": 998, "primary_gid": 997, "gid": 997, "shell": "/usr/sbin/nologin"},
                    "srrx-pico": {"kind": "g", "gid": 990}}
        good = self.report("A", True, "active", "active", "good")
        good["accounts"] = {"labd": "labd:x:998:997:SR-RX labd hardware control:/var/lib/srrx:/usr/sbin/nologin", "srrx-pico": "srrx-pico:x:990:"}
        result = {"qemu_exit": 0, "report": good, "entries_after": blessed}
        rows = {"RX-16": ["lab_pref_missing"]}
        self.assertEqual(self.smoke.check(name, result, expect, rows, recorded)["status"], "MODEL_PASS")
        good["accounts"] = {"labd": "labd:x:996:997:x:/var/lib/srrx:/usr/sbin/nologin", "srrx-pico": ""}
        mismatches = self.smoke.check(name, result, expect, rows, recorded)["mismatches"]
        self.assertEqual(mismatches, ["account labd ids ('996', '997') differ from the image manifest ('998', '997')",
                                      "account srrx-pico missing on the booted slot"])
        self.assertEqual(self.smoke.check(name, result, expect, rows, {})["mismatches"],
                         ["image-manifest.json records no service accounts (build_image.system_accounts)"])

    def test_not_feasible_is_a_failure_when_the_model_is_required(self):
        result = {"status": "SMOKE_NOT_FEASIBLE", "scenarios": []}
        argv = ["smoke_qemu.py", "--image", "x.img", "--manifest", "m.json", "--work", "w", "--out", "o"]
        with patch.object(self.smoke, "smoke", lambda *a, **k: result):
            for extra, code in (([], 0), (["--require-model"], 1)):
                with patch.object(sys, "argv", argv + extra), patch("builtins.print"):
                    self.assertEqual(self.smoke.main(), code, extra)

    def test_running_service_missing_mask_or_selftest_drift_fail(self):
        blessed = sorted(["labA.conf", "labB.conf", "labA-rescue.conf", "labB-rescue.conf"])
        report = self.report("A", True, "active", "active", "good", rows={})
        report["units"]["srrx.service"] = {"ActiveState": "active", "UnitFileState": "enabled"}
        report["masked_units"]["rsetup.service"] = {"LoadState": "loaded"}
        mismatches = self.run_check(0, report, blessed)["mismatches"]
        self.assertEqual(len(mismatches), 3, mismatches)

    def test_smoke_entry_keeps_the_slot_line_and_adds_only_the_report(self):
        cfg = bootchain.validate_ab(config())
        options = self.smoke.smoke_options(cfg, "B", drop=self.smoke.BROKEN_TOKEN).split(" ")
        line = bootchain.cmdline(BASE, cfg["root_b_partuuid"]).split(" ")
        self.assertEqual([t for t in options if t in line], [t for t in line if t != self.smoke.BROKEN_TOKEN])
        self.assertIn("systemd.run_success_action=poweroff", options)
        self.assertNotIn("--selftest", " ".join(options))
        self.assertIn('bootchain.py smoke-report --selftest" ', self.smoke.smoke_options(cfg, "A", selftest=True))
        self.assertNotIn("devicetree", self.smoke.smoke_entry(cfg, "A", 3))
        self.assertEqual(bootchain.SMOKE_TARGET, "multi-user.target")


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
        # The by-id name is refused on its form alone, before the device is looked at (LOG-SEC etc.).
        for target in ("/dev/disk/by-id/../../sda", "/dev/disk/by-id/x/../../../sda", "/dev/disk/by-id/", "/dev/disk/by-id/not-a-link"):
            with self.assertRaisesRegex(recovery_kit.KitError, "by-id/<name> link"):
                recovery_kit.check_target(target, data, self.image)

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

    def test_forced_journal_ranges_are_written_over_holes(self):
        # The journal of a fresh mke2fs is unwritten extents: SEEK_DATA reports a hole there.
        journal = {"offset": 32 << 20, "length": 4 << 20, "what": "data ext4 journal (inode 8)"}
        plain = recovery_kit.make_map(self.image)
        self.assertEqual(recovery_kit.uncovered(plain["extents"], [journal]), [(32 << 20, 4 << 20)])
        data = recovery_kit.make_map(self.image, forced=[journal])
        self.assertEqual(recovery_kit.uncovered(data["extents"], [journal]), [])
        self.assertEqual(data["forced"], [journal])
        self.assertEqual(data["data_bytes"] - plain["data_bytes"], 4 << 20)
        mapping = self.root / "forced.map.json"
        mapping.write_text(json.dumps(data))
        self.assertEqual(recovery_kit.verify_extents(self.image, recovery_kit.load_map(mapping)), [])
        for change in (lambda d: d.pop("forced"), lambda d: d["forced"].append(dict(journal, offset=48 << 20)),
                       lambda d: d["forced"].append(dict(journal, offset=4097)), lambda d: d["forced"].append(dict(journal, what="x\n"))):
            broken = copy.deepcopy(data)
            change(broken)
            mapping.write_text(json.dumps(broken))
            with self.assertRaises(recovery_kit.KitError):
                recovery_kit.load_map(mapping)

    def test_uncovered_and_merge(self):
        self.assertEqual(recovery_kit.merge_ranges([(10, 5), (0, 10), (30, 5)]), [(0, 15), (30, 5)])
        self.assertEqual(recovery_kit.merge_ranges([(0, 10), (12, 4)], gap=4), [(0, 16)])
        self.assertEqual(recovery_kit.uncovered([[0, 10, "x"], [20, 10, "x"]], [(5, 20)]), [(10, 10)])
        self.assertEqual(recovery_kit.uncovered([[0, 100, "x"]], [{"offset": 10, "length": 20}]), [])


@unittest.skipUnless(os.name == "posix" and sys.platform == "linux", "fake sysfs tree with symlinks (Linux)")
class TargetBusyTests(unittest.TestCase):
    """refuse_busy on a fake /sys and /proc: mounted, swap, holders and the image on the target."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-sysfs-test-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        devices = root / "sys/devices/virtual/block"
        (root / "sys/class/block").mkdir(parents=True)
        (root / "sys/dev/block").mkdir(parents=True)
        for disk, major, parts in (("loop7", 7, 4), ("sdz", 8, 2)):
            (devices / disk / "holders").mkdir(parents=True)
            os.symlink(devices / disk, root / "sys/class/block" / disk)
            os.symlink(devices / disk, root / "sys/dev/block" / ("%d:0" % major))
            for number in range(1, parts + 1):
                part = devices / disk / (disk + ("p" if disk.startswith("loop") else "") + str(number))
                (part / "holders").mkdir(parents=True)
                (part / "partition").write_text(str(number) + "\n")
                os.symlink(part, root / "sys/class/block" / part.name)
                os.symlink(part, root / "sys/dev/block" / ("%d:%d" % (259 if major == 7 else major, number)))
        self.devices = devices
        self.mountinfo, self.swaps = root / "mountinfo", root / "swaps"
        self.mountinfo.write_text("22 1 8:2 / / rw,relatime shared:1 - ext4 /dev/sdz2 rw\n")
        self.swaps.write_text("Filename\tType\tSize\tUsed\tPriority\n")
        for name, value in (("PROC_MOUNTINFO", self.mountinfo), ("PROC_SWAPS", self.swaps),
                            ("SYS_CLASS_BLOCK", root / "sys/class/block"), ("SYS_DEV_BLOCK", root / "sys/dev/block")):
            patcher = patch.object(recovery_kit, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_idle_target_passes_and_the_running_root_disk_is_refused(self):
        recovery_kit.refuse_busy("loop7", image_dev="8:2")  # the image lives on the root disk, not on the target
        with self.assertRaisesRegex(recovery_kit.KitError, r"holds mounted filesystems or swap \(/\)"):
            recovery_kit.refuse_busy("sdz")

    def test_mounted_partition_swap_and_holders_are_refused(self):
        self.mountinfo.write_text(self.mountinfo.read_text() + "40 22 259:4 / /mnt/x rw - ext4 /dev/loop7p4 rw\n")
        with self.assertRaisesRegex(recovery_kit.KitError, "holds mounted filesystems"):
            recovery_kit.refuse_busy("loop7")
        self.mountinfo.write_text("22 1 8:2 / / rw - ext4 /dev/sdz2 rw\n")
        self.swaps.write_text(self.swaps.read_text() + "/dev/loop7p3\tpartition\t1024\t0\t-2\n")
        with patch.object(recovery_kit, "_rdev_of", lambda node: "259:3"):
            with self.assertRaisesRegex(recovery_kit.KitError, r"\[swap\]"):
                recovery_kit.refuse_busy("loop7")
        self.swaps.write_text("Filename\tType\tSize\tUsed\tPriority\n")
        (self.devices / "loop7/loop7p3/holders/dm-0").mkdir()
        with self.assertRaisesRegex(recovery_kit.KitError, "held by dm-0"):
            recovery_kit.refuse_busy("loop7")
        (self.devices / "loop7/loop7p3/holders/dm-0").rmdir()
        (self.devices / "loop7/holders/md0").mkdir()
        with self.assertRaisesRegex(recovery_kit.KitError, "held by md0"):
            recovery_kit.refuse_busy("loop7")

    def test_image_on_the_target_is_refused_first(self):
        self.mountinfo.write_text(self.mountinfo.read_text() + "40 22 259:4 / /mnt/x rw - ext4 /dev/loop7p4 rw\n")
        with self.assertRaisesRegex(recovery_kit.KitError, "image file lives on the target disk"):
            recovery_kit.refuse_busy("loop7", image_dev="259:4")
        with self.assertRaisesRegex(recovery_kit.KitError, "image file lives on the target disk"):
            recovery_kit.refuse_busy("sdz", image_dev="8:0")


class BootCheckCmdlineTests(unittest.TestCase):
    def setUp(self):
        self.cfg = bootchain.validate_ab(config())
        self.line = bootchain.cmdline(BASE, self.cfg["root_a_partuuid"])

    def test_route_a_allows_only_the_entry_initrd(self):
        issues, notes = bootchain.cmdline_findings(self.cfg, "A", self.line + " initrd=\\srrx\\A\\initrd.img\n")
        self.assertEqual(issues, [])
        self.assertEqual(notes, ["boot loader tokens: initrd=\\srrx\\A\\initrd.img"])
        for added in ("systemd.mask=srrx-boot-check.service", "systemd.unit=rescue.target", "init=/bin/sh",
                      "module_blacklist=vfat", "initrd=\\srrx\\B\\initrd.img", "loglevel=8"):
            issues, _ = bootchain.cmdline_findings(self.cfg, "A", self.line + " " + added)
            self.assertTrue(any(added in i for i in issues), (added, issues))
        issues, _ = bootchain.cmdline_findings(self.cfg, "A", self.line + " root=PARTUUID=" + self.cfg["root_b_partuuid"])
        self.assertTrue(any("root=" in i for i in issues))
        issues, _ = bootchain.cmdline_findings(self.cfg, "A", self.line.replace(" panic=10", ""))
        self.assertTrue(any("lacks panic=10" in i for i in issues))

    def test_route_b_allows_the_recorded_embloader_bootargs(self):
        cfg = bootchain.validate_ab(config(route="B"))
        loader = " ".join(bootchain.EMBLOADER_Q6A_BOOTARGS)
        issues, notes = bootchain.cmdline_findings(cfg, "A", loader + " " + self.line + " initrd=/srrx/A/initrd.img")
        self.assertEqual(issues, [])
        self.assertIn("embloader", notes[0])
        issues, _ = bootchain.cmdline_findings(cfg, "A", self.line + " systemd.mask=srrx-ab-commit.service")
        self.assertTrue(issues)

    def test_smoke_tokens_pass_only_inside_a_vm(self):
        for selftest in (False, True):
            line = self.line + " " + " ".join(bootchain.smoke_tokens(selftest)) + " initrd=\\srrx\\A\\initrd.img"
            self.assertEqual(bootchain.cmdline_findings(self.cfg, "A", line, "qemu")[0], [])
            for virt in ("none", "unknown"):
                self.assertTrue(bootchain.cmdline_findings(self.cfg, "A", line, virt)[0], virt)
        mixed = self.line + " " + " ".join(bootchain.smoke_tokens()) + " init=/bin/sh"
        self.assertTrue(bootchain.cmdline_findings(self.cfg, "A", mixed, "qemu")[0])

    def test_proc_tokens_keep_quoted_parameters_whole(self):
        self.assertEqual(bootchain.proc_tokens('a=1  systemd.run="/usr/bin/x -I y" b\n'), ["a=1", 'systemd.run="/usr/bin/x -I y"', "b"])


class FirstBootAndRecipeTests(unittest.TestCase):
    def setUp(self):
        self.recipe = json.loads((HERE / "image/recipe.json").read_text())

    def test_rsetup_first_boot_is_parsed_without_passwords_and_reviewed(self):
        with tempfile.TemporaryDirectory() as temp:
            before = Path(temp) / "before.txt"
            before.write_text("# first boot\nno_fail\nlog \"start\"\nadd_user radxa radxa\nresize_root\n"
                              "disable_service ssh ssh.socket smbd nmbd systemd-networkd\nregenerate_ssh_hostkey\n"
                              "if headless enable_service ssh\nremove_packages rsetup-config-first-boot\n")
            facts = build_image.rsetup_first_boot(before)
            self.assertEqual([c["command"] for c in facts["commands"]],
                             ["no_fail", "log", "add_user", "resize_root", "disable_service", "regenerate_ssh_hostkey",
                              "enable_service", "remove_packages"])
            self.assertEqual(facts["commands"][2], {"command": "add_user", "args_count": 2})  # no default password recorded
            self.assertEqual(facts["commands"][6], {"command": "enable_service", "if": "headless", "args": ["ssh"]})
            root = Path(temp) / "root"
            (root / "etc/systemd/system/multi-user.target.wants").mkdir(parents=True)
            rows, blocking = build_image.first_boot_review(facts, self.recipe, root)
            self.assertEqual(blocking, [])
            self.assertEqual(rows[4]["units"]["systemd-networkd.service"], "not enabled")
            self.assertEqual(rows[4]["units"]["ssh.socket"], "masked")
            (root / "etc/systemd/system/multi-user.target.wants/systemd-networkd.service").write_text("")
            facts["commands"].append({"command": "connect_wi-fi", "args_count": 2})
            _, blocking = build_image.first_boot_review(facts, self.recipe, root)
            self.assertEqual(len(blocking), 2, blocking)
            self.assertTrue(build_image.first_boot_review(None, self.recipe, root)[1])

    def test_network_services_rsetup_disabled_are_masked_and_host_keys_handled(self):
        masks = set(self.recipe["mask"]["units"])
        self.assertTrue({"ssh.service", "ssh.socket", "smbd.service", "nmbd.service", "samba-ad-dc.service", "rsetup.service",
                         "cups.service", "cups.socket", "cups.path", "avahi-daemon.service", "avahi-daemon.socket"} <= masks)
        for command in ("disable_service", "regenerate_ssh_hostkey", "enable_service", "add_user", "rebuild_current_overlays"):
            self.assertIn(command, self.recipe["rsetup_first_boot"]["handled"])
        self.assertNotIn("STACK.md:845 never rsetup", json.dumps(self.recipe))  # :845 is the sleep masks; the rsetup ban is :138/:843
        unit = (HERE / "image/files/srrx-ssh-hostkeys.service").read_text()
        self.assertIn("ExecStart=/usr/bin/ssh-keygen -A", unit)
        self.assertIn("\nBefore=ssh.service", unit)
        self.assertEqual(self.recipe["enable_common"]["units"]["srrx-ssh-hostkeys.service"], "ssh.service.wants")

    def test_journal_ranges_from_dumpe2fs_and_debugfs_output(self):
        header = build_image.dumpe2fs_header("Filesystem volume name:   srrx-data\nJournal inode:            8\nBlock size:               4096\n"
                                             "Journal features:         (none)\nTotal journal size:       64M\nTotal journal blocks:     16384\n")
        self.assertEqual((header["Journal inode"], header["Block size"], header["Total journal size"], header["Total journal blocks"]),
                         ("8", "4096", "64M", "16384"))
        self.assertEqual(build_image.block_runs("1024 1025 1026 2048\n1027 4000 4001\n"), [(1024, 4), (2048, 1), (4000, 2)])
        self.assertEqual(build_image.block_runs(""), [])


class DtbMergeTests(unittest.TestCase):
    """build_dtbs with dtc/fdtoverlay replaced: the overlay order and the dt-manifest.json comparison."""

    def setUp(self):
        self.recipe = json.loads((HERE / "image/recipe.json").read_text())
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp)
        self.kernel = self.temp / "deb" / "tree"
        (self.kernel / "usr/lib/linux-image-6.18.2-4-qcom/qcom").mkdir(parents=True)
        (self.kernel / "usr/lib/linux-image-6.18.2-4-qcom/qcom" / self.recipe["dtb_name"]).write_bytes(b"base")
        self.calls = []

    def fake_run(self, argv, **kwargs):
        argv = [str(a) for a in argv]
        self.calls.append(argv)
        out = Path(argv[argv.index("-o") + 1])
        out.write_bytes(" ".join(Path(a).name for a in argv[1:]).encode())

    def test_field_dtb_applies_the_lab_overlay_before_the_field_overlay(self):
        with patch.object(build_image, "run", self.fake_run):
            record = build_image.build_dtbs(self.temp / "root", self.kernel, self.recipe, "6.18.2-4-qcom")
        merges = {Path(c[c.index("-o") + 1]).name: [Path(a).name for a in c[c.index("-o") + 2:]]
                  for c in self.calls if c[0] == "fdtoverlay"}
        self.assertEqual(merges, {"lab.dtb": ["lab.dtbo"], "field.dtb": ["lab.dtbo", "field.dtbo"]})
        self.assertEqual(sum(1 for c in self.calls if c[0] == "dtc"), 2)  # each overlay compiled once
        self.assertEqual(record["field"]["applied"], ["deployment/system/dt/lab-q6a.dtso", "deployment/system/dt/field-q6a.dtso"])
        self.assertTrue(record["lab"]["merged"] and record["field"]["merged"])
        # The fake base DTB is not the one dt-manifest.json records: the comparison must say so, never MATCH.
        self.assertEqual({record[p]["dt_manifest"] for p in ("lab", "field")}, {"NOT_COMPARABLE"})


class StagedMaskTests(unittest.TestCase):
    """The bundle of deploy.py stage already masks units with empty unit files (deployment/system);
    the image hardening masks the rest with systemctl and never tries to replace those files."""

    def setUp(self):
        self.recipe = json.loads((HERE / "image/recipe.json").read_text())
        sys.path.insert(0, str(HERE / "system"))
        self.addCleanup(sys.path.remove, str(HERE / "system"))
        import system_files
        self.staged = system_files.MASKED_UNITS

    def test_every_staged_mask_is_also_a_recipe_mask(self):
        self.assertLessEqual(set(self.staged), set(self.recipe["mask"]["units"]))

    def test_hardening_skips_units_already_masked_by_an_empty_unit_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            units = root / "etc/systemd/system"
            units.mkdir(parents=True)
            for unit in self.staged:
                (units / unit).write_text("")
            (root / "etc/passwd").write_text("root:x:0:0:root:/root:/bin/bash\n")
            calls = []
            with patch.object(build_image, "run", lambda argv, **kwargs: calls.append([str(a) for a in argv])):
                result = build_image.hardening(root, self.recipe, "A")
        masked_by_systemctl = [c[-1] for c in calls if c[:1] == ["systemctl"] and "mask" in c]
        self.assertEqual(sorted(result["masked_by_stage"]), sorted(self.staged))
        self.assertFalse(set(masked_by_systemctl) & set(self.staged))
        self.assertEqual(sorted(masked_by_systemctl + result["masked_by_stage"]), sorted(self.recipe["mask"]["units"]))
        self.assertEqual(result["masked"], self.recipe["mask"]["units"])


class SystemAccountsTests(unittest.TestCase):
    """build_image.system_accounts: sysusers/tmpfiles of the staged SR-RX files in the chroot, ids recorded."""

    def test_staged_configuration_is_applied_and_every_account_is_recorded(self):
        sys.path.insert(0, str(HERE / "system"))
        self.addCleanup(sys.path.remove, str(HERE / "system"))
        import system_files
        with tempfile.TemporaryDirectory() as temp:
            root, stage = Path(temp) / "root", Path(temp) / "stage"
            (root / "etc").mkdir(parents=True)
            stage.mkdir()
            files = {system_files.SYSUSERS: "0" * 64, system_files.TMPFILES: "0" * 64, "etc/tmpfiles.d/srrx-passes.conf": "0" * 64,
                     "etc/tmpfiles.d/srrx-satdump.conf": "0" * 64, "opt/srrx/deployment/deploy.py": "0" * 64}
            (stage / "stage-files.json").write_text(json.dumps({"schema_version": 1, "status": "STAGED_ONLY", "files": files}))
            users = [a for a in system_files.SERVICE_ACCOUNTS if a[1] != "srrx-loc"]  # one account sysusers "did not create"
            passwd = ["root:x:0:0:root:/root:/bin/bash"] + ["%s:x:%d:%d::/nonexistent:/usr/sbin/nologin" % (a[1], 990 - i, 990 - i)
                                                            for i, a in enumerate(users) if a[0] == "u"]
            group = ["root:x:0:", "dialout:x:20:"] + ["%s:x:%d:" % (a[1], 990 - i) for i, a in enumerate(users)]
            calls = []

            def fake_chroot(where, argv, **kwargs):
                calls.append(list(argv))
                if argv[0] == "systemd-sysusers":
                    (root / "etc/passwd").write_text("\n".join(passwd) + "\n")
                    (root / "etc/group").write_text("\n".join(group) + "\n")
            with patch.object(build_image, "chroot", fake_chroot):
                record = build_image.system_accounts(root, stage)
        self.assertEqual(calls[0], ["systemd-sysusers", "/" + system_files.SYSUSERS])
        self.assertEqual(calls[1][:2], ["systemd-tmpfiles", "--create"])
        self.assertTrue({"--exclude-prefix=/data", "--exclude-prefix=/run", "--exclude-prefix=/tmp"} <= set(calls[1]))
        self.assertEqual([a for a in calls[1] if a.startswith("/")],
                         ["/etc/tmpfiles.d/srrx-passes.conf", "/etc/tmpfiles.d/srrx-satdump.conf", "/" + system_files.TMPFILES])
        self.assertEqual(record["service_accounts_missing"], ["srrx-loc"])
        self.assertEqual(set(record["service_accounts"]), {a[1] for a in system_files.SERVICE_ACCOUNTS})
        self.assertEqual(record["service_accounts"]["labd"]["shell"], "/usr/sbin/nologin")
        self.assertEqual(record["package_accounts_missing"], ["_chrony", "gpsd"])  # dialout is a group, root a user
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "stage-files.json").write_text(json.dumps({"files": {system_files.TMPFILES: "0" * 64}}))
            with patch.object(build_image, "chroot", lambda *a, **k: None), self.assertRaisesRegex(build_image.BuildError, "sysusers"):
                build_image.system_accounts(Path(temp), Path(temp))


class ImageAptSourcesTests(unittest.TestCase):
    """W2 IMG-1 (D-01): only the signed SR-RX publications are apt sources of the image; every other r2
    entry is diverted (dpkg-divert --local --rename, emulated here) and recorded in the manifest."""

    R2_LISTS = ("50-noble-backports.list", "50-noble-security.list", "50-noble-updates.list", "50-noble.list", "70-radxa.list",
                "80-radxa-qcs6490.list")  # image-facts.json of run 42354844339 (the two PPA lists are removed before)

    def root_with_r2_sources(self, temp, route_a=True):
        root = Path(temp)
        lists = root / "etc/apt/sources.list.d"
        lists.mkdir(parents=True)
        for name in self.R2_LISTS:
            (lists / name).write_text("deb http://ports.ubuntu.com/ubuntu-ports noble main\n")
        (root / "etc/apt/sources.list").write_text("# Ubuntu sources have moved\n")
        (root / "etc/apt/preferences.d").mkdir(parents=True)
        if route_a:
            shutil.copyfile(HERE / "image/files/srrx-boot-route-a.pref", root / "etc/apt/preferences.d/srrx-boot-route-a.pref")
        return root

    def divert(self, calls, rename=True):
        def fake_chroot(where, argv, **kwargs):
            calls.append(list(argv))
            if argv[0] == "dpkg-divert" and rename:
                os.replace(Path(where) / argv[-1].lstrip("/"), Path(where) / argv[argv.index("--divert") + 1].lstrip("/"))
        return fake_chroot

    def test_only_the_srrx_files_are_installed_and_every_r2_entry_is_disabled(self):
        with tempfile.TemporaryDirectory() as temp:
            root, calls = self.root_with_r2_sources(temp), []
            with patch.object(build_image, "chroot", self.divert(calls)):
                record = build_image.apt_sources(root, ["mozillateam-ubuntu-ppa-noble.sources"])
            self.assertEqual([e["path"] for e in record["installed"]],
                             ["etc/apt/preferences.d/lab.pref", "etc/apt/sources.list.d/srrx-lab.sources",
                              "etc/apt/sources.list.d/srrx-mirror.sources", "etc/apt/preferences.d/srrx-boot-route-a.pref"])
            self.assertEqual([e["path"] for e in record["disabled"]],
                             ["etc/apt/sources.list"] + ["etc/apt/sources.list.d/" + n for n in self.R2_LISTS])
            self.assertTrue(all(e["divert_to"] == e["path"] + ".srrx-disabled" for e in record["disabled"]))
            self.assertTrue(all(c[:4] == ["dpkg-divert", "--local", "--rename", "--divert"] and c[-2] == "--add" for c in calls))
            self.assertEqual(record["removed"], ["etc/apt/sources.list.d/mozillateam-ubuntu-ppa-noble.sources"])
            self.assertEqual((root / "etc/apt/preferences.d/lab.pref").read_bytes(), (HERE / "repo/lab.pref").read_bytes())
            self.assertEqual(record["installed"][0]["sha256"], hashlib.sha256((HERE / "repo/lab.pref").read_bytes()).hexdigest())
            self.assertEqual(sorted(p.name for p in (root / "etc/apt/sources.list.d").iterdir() if not p.name.endswith(".srrx-disabled")),
                             ["srrx-lab.sources", "srrx-mirror.sources"])
            self.assertEqual(record["keyring"], {"path": "usr/share/keyrings/srrx-lab.gpg", "present": False})
            # A second run (root B is an rsync copy) finds nothing left to divert.
            calls.clear()
            with patch.object(build_image, "chroot", self.divert(calls)):
                self.assertEqual(build_image.apt_sources(root)["disabled"], [])
        with tempfile.TemporaryDirectory() as temp:
            root = self.root_with_r2_sources(temp, route_a=False)
            with patch.object(build_image, "chroot", self.divert([])):
                self.assertEqual(len(build_image.apt_sources(root)["installed"]), 3)  # route B: no route A pin file
            root = self.root_with_r2_sources(Path(temp) / "x")
            with patch.object(build_image, "chroot", self.divert([], rename=False)), self.assertRaisesRegex(build_image.BuildError, "remain"):
                build_image.apt_sources(root)

    def test_hardening_records_the_apt_sources_and_keeps_lab_pref(self):
        recipe = json.loads((HERE / "image/recipe.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            root, calls = self.root_with_r2_sources(temp), []
            (root / "etc/passwd").write_text("root:x:0:0:root:/root:/bin/bash\n")
            (root / "etc/apt/preferences.d/ubuntu-pro-esm-apps").write_text("Package: *\nPin: release o=UbuntuESMApps\nPin-Priority: 510\n")
            with patch.object(build_image, "chroot", self.divert(calls)), patch.object(build_image, "run", lambda argv, **kwargs: None):
                result = build_image.hardening(root, recipe, "A")
            self.assertEqual(result["diverted_apt_preferences"], ["ubuntu-pro-esm-apps"])  # lab.pref is never diverted
            self.assertEqual(len(result["apt_sources"]["disabled"]), 1 + len(self.R2_LISTS))
            self.assertTrue((root / "etc/apt/preferences.d/lab.pref").is_file())


class BlockerClosesAtTests(unittest.TestCase):
    """W2 IMG-1 (D-10, D-05): every manifest blocker names what closes it; nothing leaves `blocking`."""

    # The blocking list of run 42354844339 (both routes) and its selftest rows.
    RUN = ["dt_not_booted: lab.dtb/field.dtb are CI merge-checked, not booted on a Q6A (W-10 OPEN)",
           "package_accounts_missing: _chrony, gpsd (their packages are not in r2; package closure IMG-09)",
           'selftest root A FAIL: {"RX-01a": ["pinned_package_present_unreviewed"], "RX-11": ["critical_leaf_touch_only", '
           '"unit_interpreter_missing"], "RX-16": ["lab_pref_missing"], "RX-S2": ["radio_off_binding_missing"]}',
           "target_python_without_numpy: RX-14 and RX-04-bb were evaluated with the builder's python3-numpy"]
    ROWS = {"RX-01a": ["pinned_package_present_unreviewed"], "RX-11": ["critical_leaf_touch_only", "unit_interpreter_missing"],
            "RX-16": ["lab_pref_missing"], "RX-S2": ["radio_off_binding_missing"]}

    def test_run_blockers_are_tagged(self):
        tags = build_image.blocking_closes_at(self.RUN + ["apt_keyring_absent: x"], {"fail_or_blocked_rows": self.ROWS})
        by_id = {t["blocker"]: t["closes_at"] for t in tags}
        self.assertEqual(by_id, {"dt_not_booted": "bench:W-10", "package_accounts_missing": "recipe",
                                 "selftest_root_a:RX-01a:pinned_package_present_unreviewed": "bench:Phase0",
                                 "selftest_root_a:RX-11:critical_leaf_touch_only": "recipe",
                                 "selftest_root_a:RX-11:unit_interpreter_missing": "recipe",
                                 "selftest_root_a:RX-16:lab_pref_missing": "recipe",
                                 "selftest_root_a:RX-S2:radio_off_binding_missing": "commissioning",
                                 "selftest_root_a:policy_not_reviewed": "owner:policy-review",
                                 "target_python_without_numpy": "recipe", "apt_keyring_absent": "owner:key-ceremony"})
        self.assertTrue(all(t["closes_at"] in build_image.CLOSES_AT for t in tags))
        summary = build_image.closes_at_summary(tags)
        self.assertEqual(list(summary), [t for t in build_image.CLOSES_AT if t in summary])
        self.assertEqual(summary["bench:W-10"], ["dt_not_booted"])
        # No rows left: the DRAFT policy still blocks the selftest, and an unknown blocker is "recipe", not hidden.
        self.assertEqual(build_image.blocking_closes_at(["selftest root A BLOCKED: {}", "new_thing: x"], {"fail_or_blocked_rows": {}}),
                         [{"blocker": "selftest_root_a:policy_not_reviewed", "closes_at": "owner:policy-review"},
                          {"blocker": "new_thing", "closes_at": "recipe"}])

    def test_every_blocker_the_builder_emits_has_an_explicit_tag(self):
        import re
        source = (HERE / "image/build_image.py").read_text(encoding="utf-8")
        emitted = set(re.findall(r'blocking"?\]?\.append\("([^"]+)', source)) | set(re.findall(r'blocking\.append\("([^"]+)', source))
        self.assertGreaterEqual(len(emitted), 12)
        prefixes = [p for p, _, _ in build_image.BLOCKER_CLOSES_AT] + [build_image.SELFTEST_BLOCKER]
        for text in emitted:
            self.assertTrue(any(text.startswith(p) for p in prefixes), text)
        self.assertEqual(sorted(t for _, _, t in build_image.BLOCKER_CLOSES_AT if t not in build_image.CLOSES_AT), [])


class ImageFactsAndPayloadTests(unittest.TestCase):
    """W2 IMG-1: facts name the pin_only packages and module signing (D-08); the manifest records the NPU
    payload as absent (D-14) and the MCU firmware manifest the image expects (D-15)."""

    def test_interest_and_kernel_config_keys(self):
        for name in ("libsnpe1", "hexagon-dsp-binaries-qcs6490", "dragonwing-defaults", "tzdata", "tzdata-legacy", "embloader", "libqnn1"):
            self.assertTrue(build_image.INTEREST.search(name), name)
        for key in ("CONFIG_MODULE_SIG", "CONFIG_MODULE_SIG_FORCE", "CONFIG_MODULE_SIG_ALL", "CONFIG_MODULE_SIG_HASH", "CONFIG_CGROUP_BPF"):
            self.assertIn(key, build_image.CONFIG_KEYS)
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / "config-6.18.2-4-qcom"
            config.write_bytes(b'CONFIG_MODULE_SIG=y\n# CONFIG_MODULE_SIG_FORCE is not set\nCONFIG_MODULE_SIG_HASH="sha512"\n')
            values = build_image._kernel_config(config)
        self.assertEqual((values["CONFIG_MODULE_SIG"], values["CONFIG_MODULE_SIG_FORCE"], values["CONFIG_MODULE_SIG_HASH"],
                          values["CONFIG_MODULE_SIG_ALL"]), ("y", "not set", '"sha512"', None))

    def test_npu_payload_is_absent_unless_a_qnn_package_or_file_is_present(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "var/lib/dpkg").mkdir(parents=True)
            status = root / "var/lib/dpkg/status"
            status.write_text("Package: task-qualcomm-npu\nStatus: install ok installed\nVersion: 0.1.0-7\n\n"
                              "Package: fastrpc\nStatus: install ok installed\nVersion: 1.0.3-1\n\n")
            record = build_image.npu_payload(root)
            self.assertEqual((record["status"], record["packages"], record["files"]), ("absent", [], []))
            self.assertIn("never redistributed", record["why"])
            status.write_text(status.read_text() + "Package: qcom-qnn-sdk-v68\nStatus: install ok installed\nVersion: 0.1.0-2\n\n")
            (root / "usr/lib/dsp").mkdir(parents=True)
            (root / "usr/lib/dsp/libQnnHtpV68Skel.so").write_bytes(b"\0")
            record = build_image.npu_payload(root)
            self.assertEqual((record["status"], record["packages"], record["files"]),
                             ("PRESENT", ["qcom-qnn-sdk-v68"], ["usr/lib/dsp/libQnnHtpV68Skel.so"]))

    def test_mcu_firmware_records_the_staged_build_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record = build_image.mcu_firmware(root)
            self.assertEqual((record["sha256"], record["matches_repo"]), (None, False))
            staged = root / "opt/srrx/firmware/dist/build-manifest.json"
            staged.parent.mkdir(parents=True)
            shutil.copyfile(HERE.parent / "firmware/dist/build-manifest.json", staged)
            record = build_image.mcu_firmware(root)
            self.assertTrue(record["matches_repo"])
            self.assertEqual(record["sha256"], hashlib.sha256(staged.read_bytes()).hexdigest())
            self.assertIn("bench host only", record["flashing"])


class SmokeFailedUnitStatusTests(unittest.TestCase):
    """W2 IMG-1 (wave-1 gap 'boot-check not diagnosable'): an unexpected failed unit carries the guest's
    bounded `systemctl status` tail into the mismatches, with address-like tokens removed."""

    def test_failed_unit_status_reaches_the_mismatches(self):
        import smoke_qemu
        recipe = json.loads((HERE / "image/recipe.json").read_text())
        name, expect = smoke_qemu.SCENARIOS[2]
        report = {"boot_check": {"slot": "A", "status": "BOOT_SELF_CHECK_OK"}, "bless_boot_status": "clean", "pending_jobs": [],
                  "units": {"srrx-boot-check.service": {"ActiveState": "active"}, "systemd-bless-boot.service": {"ActiveState": "inactive"},
                            "srrx.service": {"ActiveState": "inactive", "UnitFileState": "disabled"}},
                  "masked_units": {u: {"LoadState": "masked"} for u in recipe["mask"]["units"]},
                  "failed_units": ["chrony.service loaded failed failed chrony, an NTP client/server"],
                  "failed_unit_status": {"chrony.service": "x chrony.service - chrony\n     Active: failed (Result: exit-code)\n"}}
        entries = sorted(["labA.conf", "labB+0-1.conf", "labA-rescue.conf", "labB-rescue.conf"])
        result = smoke_qemu.check(name, {"qemu_exit": 0, "report": report, "entries_after": entries}, expect, {})
        self.assertEqual(result["mismatches"][0], "failed units: chrony.service")
        self.assertTrue(result["mismatches"][1].startswith("failed unit status chrony.service: x chrony.service"), result["mismatches"])

    def test_address_like_tokens_are_removed_but_unit_instances_stay(self):
        address = "someone" + "@" + "example" + ".org"  # built at run time: the tree carries no address
        text = "modprobe@configfs.service getty@tty1.service user@1000.service Author: " + address + " x"
        self.assertEqual(bootchain.redact_addresses(text),
                         "modprobe@configfs.service getty@tty1.service user@1000.service Author: <address removed> x")
        self.assertEqual(bootchain.redact_addresses(None), "")
        self.assertEqual(bootchain.FAILED_UNIT_STATUS_BYTES, 2000)
        source = (HERE / "image/bootchain.py").read_text(encoding="utf-8")
        self.assertIn('"failed_unit_status"', source)
        self.assertIn('"systemctl", "status", "--no-pager"', source)


class ReviewFixesImg1Tests(unittest.TestCase):
    """W2 IMG-1 review fixes: loose QNN/SNPE files block like a package (IMG1-R1); the selftest blocker
    is tagged from its verdict, so a missing report is "recipe" and a REVIEWED policy drops the policy
    tag (IMG1-R2)."""

    def test_npu_files_without_a_package_block_the_image(self):
        source = (HERE / "image/build_image.py").read_text(encoding="utf-8")
        self.assertIn('if manifest["npu_payload"]["status"] != "absent":', source)
        self.assertNotIn('if manifest["npu_payload"]["packages"]:', source)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "var/lib/dpkg").mkdir(parents=True)
            (root / "var/lib/dpkg/status").write_text("Package: fastrpc\nStatus: install ok installed\nVersion: 1.0.3-1\n\n")
            (root / "usr/lib/dsp").mkdir(parents=True)
            (root / "usr/lib/dsp/libQnnHtpV68Skel.so").write_bytes(b"\0")
            record = build_image.npu_payload(root)
        self.assertEqual((record["status"], record["packages"], record["files"]), ("PRESENT", [], ["usr/lib/dsp/libQnnHtpV68Skel.so"]))
        # The blocker text the build appends for this record, and its tag.
        text = "npu_payload_present: " + ", ".join(record["packages"] + record["files"])
        self.assertIn("libQnnHtpV68Skel.so", text)
        self.assertEqual(build_image.blocking_closes_at([text]), [{"blocker": "npu_payload_present", "closes_at": "recipe"}])

    def record(self, **fields):
        base = {"exit_code": 2, "status": "BLOCKED", "counts": {}, "fail_or_blocked_rows": {}, "report_sha256": "0" * 64,
                "policy_status": "DRAFT", "policy_blockers": ["POLICY_NOT_REVIEWED"], "tagged_items": {}}
        base.update(fields)
        return base

    def tags(self, record):
        text = build_image.SELFTEST_BLOCKER + str(record["status"]) + ": " + json.dumps(record["fail_or_blocked_rows"], sort_keys=True)
        return {t["blocker"]: t["closes_at"] for t in build_image.blocking_closes_at([text], record)}

    def test_selftest_without_a_usable_verdict_is_a_recipe_item(self):
        # selftest.py crashed or wrote nothing: build_image.selftest() gives status None and no report hash.
        crashed = self.record(exit_code=1, status=None, counts=None, report_sha256=None, policy_status=None, policy_blockers=[])
        self.assertEqual(self.tags(crashed), {"selftest_root_a:no_report": "recipe",
                                              "selftest_root_a:policy_not_reviewed": "owner:policy-review"})  # policy file is DRAFT
        self.assertEqual(build_image.closes_at_summary(build_image.blocking_closes_at(["selftest root A None: {}"],
                                                                                      {"status": None, "fail_or_blocked_rows": {},
                                                                                       "report_sha256": None}))["recipe"],
                         ["selftest_root_a:no_report"])
        self.assertIn("selftest_root_a:no_report", self.tags(self.record(status="SOMETHING_ELSE")))
        self.assertIn("selftest_root_a:no_report", self.tags(self.record(exit_code=1)))  # verdict and exit code disagree
        self.assertNotIn("selftest_root_a:no_report", self.tags(self.record()))

    def test_policy_tag_follows_the_verdict(self):
        self.assertEqual(self.tags(self.record()), {"selftest_root_a:policy_not_reviewed": "owner:policy-review"})
        reviewed = self.record(policy_status="REVIEWED", policy_blockers=["POLICY_REVIEW_RECORD_MISSING"])
        self.assertEqual(self.tags(reviewed), {"selftest_root_a:policy_review_record_missing": "owner:policy-review"})
        passed = self.record(exit_code=0, status="OFFLINE_CHECKS_PASS", policy_status="REVIEWED", policy_blockers=[])
        tags = self.tags(passed)
        self.assertNotIn("selftest_root_a:policy_not_reviewed", tags)
        self.assertEqual(tags, {"selftest_root_a:verdict_offline_checks_pass": "recipe"})  # still listed: one tag, never none

    def test_embloader_outside_its_version_rule_is_recipe_drift(self):
        rows = {"RX-01a": ["pinned_package_present_unreviewed"]}
        key = "RX-01a:pinned_package_present_unreviewed"
        self.assertEqual(self.tags(self.record(fail_or_blocked_rows=rows, tagged_items={key: ["embloader"]})),
                         {"selftest_root_a:RX-01a:pinned_package_present_unreviewed:embloader": "recipe",
                          "selftest_root_a:policy_not_reviewed": "owner:policy-review"})
        both = self.tags(self.record(fail_or_blocked_rows=rows, tagged_items={key: ["dragonwing-defaults", "embloader"]}))
        self.assertEqual((both["selftest_root_a:RX-01a:pinned_package_present_unreviewed:embloader"],
                          both["selftest_root_a:RX-01a:pinned_package_present_unreviewed"]), ("recipe", "bench:Phase0"))
        self.assertEqual(self.tags(self.record(fail_or_blocked_rows=rows))["selftest_root_a:RX-01a:pinned_package_present_unreviewed"],
                         "bench:Phase0")  # no items recorded: the rule tag

    def test_selftest_record_carries_the_verdict_parts_the_tags_need(self):
        report = {"status": "BLOCKED", "policy_status": "DRAFT", "blockers": ["POLICY_NOT_REVIEWED", "RX-01a", "RX-S2"], "counts": {},
                  "checks": [{"id": "RX-01a", "status": "BLOCKED",
                              "findings": [{"path": "var/lib/dpkg/status", "rule": "pinned_package_present_unreviewed", "item": "embloader"}]},
                             {"id": "RX-S2", "status": "BLOCKED", "findings": [{"path": "etc/srrx/devices.json", "rule": "radio_off_binding_missing"}]},
                             {"id": "RX-11", "status": "PASS", "findings": []}]}
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "selftest-root-a.json"
            output.write_text(json.dumps(report))
            with patch.object(build_image, "run", lambda argv, check=False: subprocess.CompletedProcess(argv, 2)):
                record = build_image.selftest(Path(temp) / "root", "0" * 64, output)
            missing = Path(temp) / "absent.json"
            with patch.object(build_image, "run", lambda argv, check=False: subprocess.CompletedProcess(argv, 1)):
                crashed = build_image.selftest(Path(temp) / "root", "0" * 64, missing)
        self.assertEqual((record["policy_status"], record["policy_blockers"], record["tagged_items"]),
                         ("DRAFT", ["POLICY_NOT_REVIEWED"], {"RX-01a:pinned_package_present_unreviewed": ["embloader"]}))
        self.assertEqual(record["fail_or_blocked_rows"], {"RX-01a": ["pinned_package_present_unreviewed"], "RX-S2": ["radio_off_binding_missing"]})
        self.assertEqual((crashed["status"], crashed["report_sha256"], crashed["policy_blockers"], crashed["tagged_items"]), (None, None, [], {}))
        self.assertIn("selftest_root_a:no_report", self.tags(crashed))


def _lock():
    return json.loads((HERE / "sources.lock.json").read_text(encoding="utf-8"))


def _locked_deb(lock, name):
    return next(d for c in lock["components"] for d in c.get("binary_debs") or [] if d["package"] == name)


class PackageClosureFileTests(unittest.TestCase):
    """W2 IMG-2 (D-02): package-closure.json against sources.lock.json; chrony/gpsd/libgps30t64 are the locked debs."""

    def setUp(self):
        self.lock = _lock()
        self.closure = json.loads((HERE / "image/package-closure.json").read_text(encoding="utf-8"))

    def test_committed_closure_is_consistent_with_the_lock(self):
        # A CLOSURE_ROOTS edit ahead of the regenerated file is the image job's check (IMG2-R1, ClosureExtensionRouteTests).
        drift = build_image.closure_roots_issues(self.closure)
        self.assertEqual([i for i in build_image.closure_issues(self.closure, self.lock) if i not in drift], [])
        by_name = {p["package"]: p for p in self.closure["packages"]}
        self.assertLessEqual({"chrony", "gpsd", "libgps30t64", "tzdata", "tzdata-legacy"}, set(by_name))  # + the session (W2 IMG-4)
        for name in ("chrony", "gpsd", "libgps30t64"):
            deb = _locked_deb(self.lock, name)
            self.assertEqual({k: by_name[name][k] for k in ("version", "architecture", "filename", "sha256", "size")},
                             {k: deb[k] for k in ("version", "architecture", "filename", "sha256", "size")}, name)
        self.assertEqual((by_name["tzdata"]["r2_version"], by_name["tzdata"]["version"]), ("2025b-0ubuntu0.24.04.1", "2026e-0ubuntu0.24.04.1"))
        self.assertEqual(by_name["tzdata-legacy"]["version"], by_name["tzdata"]["version"])  # one source version
        self.assertTrue(all(by_name[n]["r2_version"] is None for n in ("chrony", "gpsd", "libgps30t64", "tzdata-legacy")))
        self.assertEqual(self.closure["expected_removed"], ["systemd-timesyncd"])
        self.assertEqual(self.closure["expected_accounts"], ["_chrony", "_greetd", "gpsd"])
        self.assertEqual(self.closure["snapshot"]["timestamp"], self.lock["apt_snapshot"]["timestamp"])
        self.assertEqual(self.closure["base"]["sha256"], self.lock["target"]["base_image_sha256"])
        self.assertEqual(build_image.compare_closure(self.closure, copy.deepcopy(self.closure)), [])

    def test_drift_from_the_lock_is_refused(self):
        cases = []
        bad = copy.deepcopy(self.closure)
        next(p for p in bad["packages"] if p["package"] == "chrony")["sha256"] = "0" * 64
        cases.append((bad, "binary_debs"))
        bad = copy.deepcopy(self.closure)
        bad["suites"][0]["inrelease_sha256"] = "1" * 64
        cases.append((bad, "suites"))
        bad = copy.deepcopy(self.closure)
        bad["packages"].reverse()
        cases.append((bad, "sorted"))
        bad = copy.deepcopy(self.closure)
        bad["snapshot"]["archive"] = "http://ports.ubuntu.com/ubuntu-ports"
        cases.append((bad, "snapshot"))
        bad = copy.deepcopy(self.closure)
        bad["expected_removed"] = []
        cases.append((bad, "expected_removed"))
        for closure, word in cases:
            self.assertTrue(any(word in issue for issue in build_image.closure_issues(closure, self.lock)), word)
        changed = copy.deepcopy(self.closure)
        changed["packages"][0]["version"] = "9"
        self.assertEqual(build_image.compare_closure(changed, self.closure), ["packages"])

    def test_fetch_takes_each_deb_from_the_snapshot_by_filename(self):
        calls = []
        with tempfile.TemporaryDirectory() as cache, \
                patch.object(build_image, "_download", lambda url, target, sha, size, label: calls.append((url, Path(target), sha, size)) or "FETCHED"):
            build_image.fetch_closure(cache, self.closure)
            for (url, target, sha, size), entry in zip(calls, self.closure["packages"]):
                self.assertEqual(url, "https://snapshot.ubuntu.com/ubuntu/20261020T000000Z/" + entry["filename"])
                self.assertEqual(target, Path(cache) / "closure" / Path(entry["filename"]).name)
                self.assertEqual((sha, size), (entry["sha256"], entry["size"]))
        self.assertEqual(len(calls), len(self.closure["packages"]))


class DebVersionTests(unittest.TestCase):
    def test_dpkg_ordering(self):
        smaller = (("1.0~rc1", "1.0"), ("1.0", "1.0-1"), ("1.0-1", "1.0-1ubuntu1"), ("3.25-3ubuntu3", "3.25-3ubuntu3.2"),
                   ("2025b-0ubuntu0.24.04.1", "2026e-0ubuntu0.24.04.1"), ("2024a-2~", "2024a-2ubuntu1"), ("1:9", "2:0.1"),
                   ("255.4-1ubuntu8.12", "255.4-1ubuntu8.18"), ("1.9", "1.10"), ("1.0a", "1.0b"), ("1.0", "1.0+lab1"))
        for a, b in smaller:
            self.assertLess(build_image.deb_version_compare(a, b), 0, (a, b))
            self.assertGreater(build_image.deb_version_compare(b, a), 0, (b, a))
        self.assertEqual(build_image.deb_version_compare("0:1.0-1", "1.0-1"), 0)
        self.assertEqual(build_image.deb_version_compare("1.00", "1.0"), 0)
        self.assertTrue(build_image.version_satisfies("1:2.66-5ubuntu2.2", ">=", "1:2.32-1"))
        self.assertTrue(build_image.version_satisfies("2.39-0ubuntu8.7", ">=", "2.38"))
        self.assertFalse(build_image.version_satisfies("2025b-0ubuntu0.24.04.1", "<<", "2024a-2~"))
        self.assertTrue(build_image.version_satisfies("x", None, None))

    def test_relations(self):
        groups = build_image.parse_relations("adduser (>= 3.34), netbase | systemd-sysv, python3:any, libstdc++6 (>= 5) [arm64]")
        self.assertEqual(groups, [[("adduser", None, ">=", "3.34")], [("netbase", None, None, None), ("systemd-sysv", None, None, None)],
                                  [("python3", "any", None, None)], [("libstdc++6", None, ">=", "5")]])
        with self.assertRaises(build_image.BuildError):
            build_image.parse_relations("Bad Name")


def _stanza(package, version, **fields):
    data = {"package": package, "version": version, "architecture": fields.pop("architecture", "arm64"),
            "filename": fields.pop("filename", "pool/main/%s/%s/%s_%s_arm64.deb" % (package[0], package, package, version)),
            "sha256": fields.pop("sha256", hashlib.sha256((package + version).encode()).hexdigest()), "size": str(fields.pop("size", 1000))}
    data.update({k.replace("_", "-"): v for k, v in fields.items()})
    return data


class ClosureResolverTests(unittest.TestCase):
    """build_image.resolve_closure on a small signed-index model of the snapshot and the r2 dpkg status."""

    def setUp(self):
        self.enterContext(patch.object(build_image, "CLOSURE_ROOTS", {"chrony": ("_chrony",), "gpsd": ("gpsd",)}))  # the model's roots
        self.lock = _lock()
        locked = {n: _locked_deb(self.lock, n) for n in ("chrony", "gpsd", "libgps30t64")}

        def pinned(name, **fields):
            deb = locked[name]
            return _stanza(name, deb["version"], filename=deb["filename"], sha256=deb["sha256"], size=deb["size"], **fields)
        self.stanzas = [
            ("noble", "main", _stanza("tzdata-legacy", "2024a-2ubuntu1", architecture="all", depends="tzdata", source="tzdata")),
            ("noble", "main", _stanza("tzdata", "2024a-2ubuntu1", architecture="all")),
            ("noble-updates", "main", pinned("chrony", depends="adduser (>= 3.130), tzdata-legacy, libc6 (>= 2.38)",
                                             conflicts="time-daemon", replaces="time-daemon", provides="time-daemon",
                                             breaks="network-manager (<< 1.20.0-1~)")),
            ("noble-updates", "main", _stanza("tzdata-legacy", "2026e-0ubuntu0.24.04.1", architecture="all", depends="tzdata",
                                              source="tzdata", breaks="tzdata (<< 2024a-2~)")),
            ("noble-updates", "main", _stanza("tzdata", "2026e-0ubuntu0.24.04.1", architecture="all", depends="debconf (>= 0.5) | debconf-2.0")),
            ("noble-updates", "main", pinned("gpsd", depends="adduser (>= 3.34), libgps30t64 (= 3.25-3ubuntu3.2), netbase | systemd-sysv",
                                             source="gpsd")),
            ("noble-updates", "main", pinned("libgps30t64", source="gpsd", depends="libc6 (>= 2.38)")),
            ("noble-security", "main", pinned("libgps30t64", source="gpsd", depends="libc6 (>= 2.38)")),
            ("noble-updates", "main", _stanza("systemd-timesyncd", "255.4-1ubuntu8.17", source="systemd", conflicts="time-daemon",
                                              provides="time-daemon", depends="systemd")),
            ("noble-updates", "main", _stanza("debconf", "1.5.86ubuntu1", architecture="all", provides="debconf-2.0")),
            ("noble-updates", "universe", _stanza("ntpsec", "1.2.2", architecture="armhf")),  # other architectures are ignored
        ]
        self.installed = {"adduser": "3.137ubuntu1", "tzdata": "2025b-0ubuntu0.24.04.1", "systemd-timesyncd": "255.4-1ubuntu8.12",
                          "systemd-sysv": "255.4-1ubuntu8.12", "systemd": "255.4-1ubuntu8.12", "libc6:arm64": "2.39-0ubuntu8.7",
                          "debconf": "1.5.86ubuntu1", "network-manager": "1.46.0-1ubuntu2.5"}

    def test_the_r2_closure_of_chrony_and_gpsd(self):
        resolved = build_image.resolve_closure(self.stanzas, self.installed, self.lock)
        self.assertEqual(resolved["issues"], [])
        by_name = {p["package"]: p for p in resolved["packages"]}
        self.assertEqual(sorted(by_name), ["chrony", "gpsd", "libgps30t64", "tzdata", "tzdata-legacy"])
        self.assertEqual(by_name["tzdata-legacy"]["version"], "2026e-0ubuntu0.24.04.1")  # apt's candidate: the newest
        self.assertEqual(by_name["libgps30t64"]["suite"], "noble-updates")  # the first suite listing the version
        self.assertTrue(by_name["tzdata"]["reason"].startswith("same source as tzdata-legacy"))
        self.assertTrue(by_name["tzdata-legacy"]["reason"].startswith("Depends of chrony"))
        self.assertEqual(resolved["expected_removed"], ["systemd-timesyncd"])
        self.assertIn("time-daemon", resolved["removed_because"]["systemd-timesyncd"])
        recipe = json.loads((HERE / "image/recipe.json").read_text())
        document = build_image.closure_document(resolved, self.lock, recipe, len(self.installed), "2026-11-07")
        self.assertEqual(build_image.closure_issues(document, self.lock), [])
        self.assertEqual(list(document["packages"][0]), list(build_image.CLOSURE_PACKAGE_KEYS))

    def test_unsatisfiable_dependencies_and_broken_reverse_dependencies_are_issues(self):
        stanzas = [s for s in self.stanzas if s[2]["package"] != "libgps30t64"]
        issues = build_image.resolve_closure(stanzas, self.installed, self.lock)["issues"]
        self.assertTrue(any("libgps30t64" in i for i in issues), issues)
        stanzas = self.stanzas + [("noble-updates", "main", _stanza("timeclient", "1", depends="systemd-timesyncd"))]
        issues = build_image.resolve_closure(stanzas, dict(self.installed, timeclient="1"), self.lock)["issues"]
        self.assertTrue(any(i.startswith("removing systemd-timesyncd breaks") for i in issues), issues)
        # A dependency r2 satisfies through a virtual package (time-daemon here) needs no closure package.
        stanzas = self.stanzas + [("noble-updates", "main", _stanza("clockuser", "1", depends="time-daemon"))]
        resolved = build_image.resolve_closure(stanzas, dict(self.installed, clockuser="1"), self.lock)
        self.assertEqual(resolved["issues"], [])


class ClosureInstallTests(unittest.TestCase):
    """install_closure: the apt plan and the dpkg status change must both be exactly the closure."""

    STATUS = ("Package: tzdata\nStatus: install ok installed\nVersion: 2025b-0ubuntu0.24.04.1\n\n"
              "Package: systemd-timesyncd\nStatus: install ok installed\nVersion: 255.4-1ubuntu8.12\n\n"
              "Package: adduser\nStatus: install ok installed\nVersion: 3.137ubuntu1\n\n")
    PLAN = ("Reading package lists...\nThe following packages will be REMOVED:\n  systemd-timesyncd*\n"
            "Purg systemd-timesyncd [255.4-1ubuntu8.12]\n"
            "Inst tzdata [2025b-0ubuntu0.24.04.1] (2026e-0ubuntu0.24.04.1 local-deb [all])\n"
            "Inst chrony (4.5-1ubuntu4.2 local-deb [arm64])\n"
            "Conf tzdata (2026e-0ubuntu0.24.04.1 local-deb [all])\nConf chrony (4.5-1ubuntu4.2 local-deb [arm64])\n")

    def closure(self, cache):
        packages = []
        for name, version, r2 in (("chrony", "4.5-1ubuntu4.2", None), ("tzdata", "2026e-0ubuntu0.24.04.1", "2025b-0ubuntu0.24.04.1")):
            data = (name + version).encode()
            filename = "pool/main/%s/%s/%s_%s_all.deb" % (name[0], name, name, version)
            (Path(cache) / "closure").mkdir(parents=True, exist_ok=True)
            (Path(cache) / "closure" / Path(filename).name).write_bytes(data)
            packages.append({"package": name, "version": version, "architecture": "all", "filename": filename, "suite": "noble-updates",
                             "sha256": hashlib.sha256(data).hexdigest(), "size": len(data), "r2_version": r2, "reason": "test"})
        return {"packages": packages, "expected_removed": ["systemd-timesyncd"], "expected_accounts": ["_chrony"],
                "snapshot": {"timestamp": "20261020T000000Z"}}

    def fake_chroot(self, root, calls, after_status, plan=None):
        def run(where, argv, extra_env=None, check=True):
            calls.append((list(argv), extra_env))
            if "-s" in argv:
                return subprocess.CompletedProcess(argv, 0, plan or self.PLAN, "")
            (root / "var/lib/dpkg/status").write_text(after_status)
            (root / "etc/passwd").write_text("root:x:0:0::/root:/bin/bash\n_chrony:x:105:110:Chrony daemon:/var/lib/chrony:/usr/sbin/nologin\n")
            return subprocess.CompletedProcess(argv, 0, "Setting up chrony (4.5-1ubuntu4.2) ...\n", "")
        return run

    def root(self, temp):
        root = Path(temp) / "root"
        (root / "var/lib/dpkg").mkdir(parents=True)
        (root / "etc").mkdir()
        (root / "var/lib/dpkg/status").write_text(self.STATUS)
        return root

    def test_plan_and_status_equal_to_the_closure_pass(self):
        after = self.STATUS.replace("2025b-0ubuntu0.24.04.1", "2026e-0ubuntu0.24.04.1").replace(
            "Package: systemd-timesyncd\nStatus: install ok installed\nVersion: 255.4-1ubuntu8.12\n\n",
            "Package: chrony\nStatus: install ok installed\nVersion: 4.5-1ubuntu4.2\n\n")
        with tempfile.TemporaryDirectory() as temp:
            root, calls = self.root(temp), []
            closure = self.closure(Path(temp) / "cache")
            with patch.object(build_image, "chroot", self.fake_chroot(root, calls, after)):
                record = build_image.install_closure(root, Path(temp) / "cache", closure)
            self.assertFalse((root / build_image.CLOSURE_CHROOT_DIR).exists())  # the debs leave the image
        self.assertEqual(record["installed"], {"chrony": "4.5-1ubuntu4.2", "tzdata": "2026e-0ubuntu0.24.04.1"})
        self.assertEqual(record["removed"], ["systemd-timesyncd"])
        self.assertEqual(record["upgraded"], {"tzdata": {"from": "2025b-0ubuntu0.24.04.1", "to": "2026e-0ubuntu0.24.04.1"}})
        self.assertEqual(record["accounts"], {"_chrony": {"uid": 105, "primary_gid": 110}})
        simulate, install = calls
        self.assertEqual(simulate[0][:3], ["apt-get", "install", "-s"])
        self.assertNotIn("-s", install[0])
        for argv, env in calls:
            self.assertIn("--purge", argv)
            self.assertIn("--no-install-recommends", argv)
            for option in ("Dir::Etc::SourceList=/dev/null", "Dir::Etc::Preferences=/dev/null", "Dpkg::Options::=--force-confold",
                           "Dir::Etc::SourceParts=/" + build_image.CLOSURE_CHROOT_DIR + "/parts.d"):
                self.assertIn(option, argv)
            self.assertEqual([a for a in argv if a.endswith(".deb")],
                             ["/" + build_image.CLOSURE_CHROOT_DIR + "/" + Path(p["filename"]).name for p in closure["packages"]])
            self.assertEqual(env, build_image.CLOSURE_ENV)

    def test_any_other_plan_or_change_stops_the_build(self):
        plan = self.PLAN + "Inst ntpsec (1.2.2 Ubuntu:24.04/noble [arm64])\n"
        with tempfile.TemporaryDirectory() as temp:
            root, calls = self.root(temp), []
            closure = self.closure(Path(temp) / "cache")
            with patch.object(build_image, "chroot", self.fake_chroot(root, calls, self.STATUS, plan)), \
                    self.assertRaisesRegex(build_image.BuildError, "apt plan"):
                build_image.install_closure(root, Path(temp) / "cache", closure)
            self.assertEqual(len(calls), 1)  # refused before the real install
            with patch.object(build_image, "chroot", self.fake_chroot(root, calls, self.STATUS)), \
                    self.assertRaisesRegex(build_image.BuildError, "dpkg status after"):
                build_image.install_closure(root, Path(temp) / "cache", closure)  # nothing changed: closure not installed
            (root / "var/lib/dpkg/status").write_text(self.STATUS.replace("2025b", "2025a"))
            with self.assertRaisesRegex(build_image.BuildError, "resolved against"):
                build_image.install_closure(root, Path(temp) / "cache", closure)
            (root / "var/lib/dpkg/status").write_text(self.STATUS)
            (Path(temp) / "cache/closure" / Path(closure["packages"][0]["filename"]).name).write_bytes(b"other")
            with patch.object(build_image, "chroot", self.fake_chroot(root, [], self.STATUS)), \
                    self.assertRaisesRegex(build_image.BuildError, "closure deb differs"):
                build_image.install_closure(root, Path(temp) / "cache", closure)

    def test_apt_simulation_and_status_changes(self):
        plan = build_image.apt_simulation(self.PLAN)
        self.assertEqual(plan, {"install": {"chrony": "4.5-1ubuntu4.2", "tzdata": "2026e-0ubuntu0.24.04.1"}, "remove": ["systemd-timesyncd"]})
        changes = build_image.status_changes({"a": "1", "b:arm64": "2", "c": "3"}, {"a": "1", "b:arm64": "3", "d": "1"})
        self.assertEqual(changes, {"b": ("2", "3"), "c": ("3", None), "d": (None, "1")})


class ChronyConfInstallTests(unittest.TestCase):
    """install_chrony_conf: the SR-RX file replaces chrony's ucf copy and chronyd -p finds no network directive."""

    def parse(self, extra=""):
        def run(where, argv, extra_env=None, check=True):
            text = (Path(where) / argv[-1].lstrip("/")).read_text(encoding="utf-8")
            lines = [l for l in text.splitlines() if l.strip() and not l.startswith("#") and not l.startswith("confdir")]
            return subprocess.CompletedProcess(argv, 0, "\n".join(lines) + "\n" + extra, "")
        return run

    def test_offline_file_is_written_and_parsed(self):
        sys.path.insert(0, str(HERE / "system"))
        self.addCleanup(sys.path.remove, str(HERE / "system"))
        import system_files
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "etc/chrony").mkdir(parents=True)
            (root / "etc/chrony/chrony.conf").write_text("pool ntp.ubuntu.com iburst maxsources 4\n")
            with patch.object(build_image, "chroot", self.parse()):
                record = build_image.install_chrony_conf(root)
            self.assertEqual((root / "etc/chrony/chrony.conf").read_text(encoding="utf-8"), system_files.chrony_conf())
            self.assertEqual(record["sha256"], hashlib.sha256(system_files.chrony_conf().encode()).hexdigest())
            self.assertEqual(record["network_directives"], [])
            self.assertIn("rtcsync", record["chronyd_p_directives"])
            self.assertIsNotNone(record["replaced_sha256"])
            with patch.object(build_image, "chroot", self.parse("pool 0.ubuntu.pool.ntp.org iburst\n")), \
                    self.assertRaisesRegex(build_image.BuildError, "pool"):
                build_image.install_chrony_conf(root)  # e.g. a *.conf in conf.d that adds a pool
        with tempfile.TemporaryDirectory() as temp, self.assertRaisesRegex(build_image.BuildError, "not installed"):
            build_image.install_chrony_conf(Path(temp))

    def test_staged_gnss_mode_is_read_from_the_gpsd_defaults(self):
        sys.path.insert(0, str(HERE / "system"))
        self.addCleanup(sys.path.remove, str(HERE / "system"))
        import system_files
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertIsNone(build_image.staged_gnss_mode(root))
            (root / "etc/default").mkdir(parents=True)
            for mode in ("gpsd", "raw", "off"):
                (root / "etc/default/gpsd").write_text(system_files.gpsd_defaults(mode))
                self.assertEqual(build_image.staged_gnss_mode(root), mode)
            (root / "etc/default/gpsd").write_text('DEVICES=""\n')  # the package's own copy
            self.assertIsNone(build_image.staged_gnss_mode(root))


class SmokeClosureTests(unittest.TestCase):
    """smoke_qemu.closure_mismatches: the booted slot against image-manifest.json package_closure (W2 IMG-2)."""

    RECORDED = {"installed": {"chrony": "4.5-1ubuntu4.2", "gpsd": "3.25-3ubuntu3.2"}, "removed": ["systemd-timesyncd"],
                "accounts": {"_chrony": {"uid": 105, "primary_gid": 110}, "gpsd": {"uid": 106, "primary_gid": 20}},
                "gnss_mode": "gpsd", "chrony_conf": {"sha256": "c" * 64}}

    def observed(self):
        return {"dpkg": {"chrony": "4.5-1ubuntu4.2\tinstalled", "gpsd": "3.25-3ubuntu3.2\tinstalled", "systemd-timesyncd": ""},
                "accounts": {"_chrony": "_chrony:x:105:110:Chrony daemon:/var/lib/chrony:/usr/sbin/nologin",
                             "gpsd": "gpsd:x:106:20:GPSD system user:/run/gpsd:/bin/false"},
                "units": {"chrony.service": {"LoadState": "loaded", "ActiveState": "active"},
                          # run 42398832045: the package enables only the socket (socket activation)
                          "gpsd.service": {"LoadState": "loaded", "ActiveState": "inactive", "UnitFileState": "disabled"},
                          "gpsd.socket": {"LoadState": "loaded", "ActiveState": "active", "UnitFileState": "enabled"},
                          "systemd-timesyncd.service": {"LoadState": "not-found", "ActiveState": "inactive"}},
                "chrony_conf_sha256": "c" * 64}

    def setUp(self):
        import smoke_qemu
        self.smoke = smoke_qemu

    def test_the_built_closure_passes(self):
        self.assertEqual(self.smoke.closure_mismatches(self.observed(), self.RECORDED), [])
        observed = self.observed()
        observed["units"]["gpsd.service"]["ActiveState"] = "active"  # a client connected: still socket-activated
        self.assertEqual(self.smoke.closure_mismatches(observed, self.RECORDED), [])
        observed["units"]["gpsd.service"]["UnitFileState"] = "enabled"  # enabled at boot is not the package default
        self.assertEqual(len(self.smoke.closure_mismatches(observed, self.RECORDED)), 1)
        raw = dict(self.RECORDED, gnss_mode="raw")
        observed = self.observed()
        for unit in ("gpsd.service", "gpsd.socket"):
            observed["units"][unit] = {"LoadState": "masked", "ActiveState": "inactive"}
        self.assertEqual(self.smoke.closure_mismatches(observed, raw), [])

    def test_every_deviation_is_a_mismatch(self):
        observed = self.observed()
        observed["dpkg"]["systemd-timesyncd"] = "255.4-1ubuntu8.12\tinstalled"
        observed["dpkg"]["chrony"] = ""
        observed["accounts"]["gpsd"] = "gpsd:x:107:20::/run/gpsd:/bin/false"
        observed["units"]["chrony.service"]["ActiveState"] = "failed"
        observed["units"]["systemd-timesyncd.service"]["LoadState"] = "loaded"
        observed["units"]["gpsd.service"]["ActiveState"] = "failed"
        observed["chrony_conf_sha256"] = "d" * 64
        mismatches = self.smoke.closure_mismatches(observed, self.RECORDED)
        self.assertEqual(len(mismatches), 7, mismatches)
        self.assertEqual(self.smoke.closure_mismatches(self.observed(), {}),
                         ["image-manifest.json records no package_closure (build_image.install_closure)"])
        self.assertTrue(self.smoke.closure_mismatches({"unavailable": "OSError"}, self.RECORDED)[0].startswith("no package closure report"))
        self.assertTrue(self.smoke.closure_mismatches(self.observed(), dict(self.RECORDED, gnss_mode=None)))

    def test_check_carries_closure_and_display_manager_mismatches(self):
        recipe = json.loads((HERE / "image/recipe.json").read_text())
        self.assertTrue({"gdm.service", "gdm3.service"} <= set(recipe["mask"]["units"]))
        name, expect = self.smoke.SCENARIOS[2]
        report = {"boot_check": {"slot": "A", "status": "BOOT_SELF_CHECK_OK"}, "bless_boot_status": "clean", "pending_jobs": [],
                  "units": {"srrx-boot-check.service": {"ActiveState": "active"}, "systemd-bless-boot.service": {"ActiveState": "inactive"},
                            "srrx.service": {"ActiveState": "inactive", "UnitFileState": "disabled"}},
                  "masked_units": {u: {"LoadState": "masked"} for u in recipe["mask"]["units"]},
                  "package_closure": self.observed(), "display_manager": {"LoadState": "masked"}}
        entries = sorted(["labA.conf", "labB+0-1.conf", "labA-rescue.conf", "labB-rescue.conf"])
        result = {"qemu_exit": 0, "report": report, "entries_after": entries}
        self.assertEqual(self.smoke.check(name, result, expect, {}, None, self.RECORDED)["status"], "MODEL_PASS")
        report["display_manager"] = {"LoadState": "loaded"}
        report["package_closure"]["units"]["chrony.service"]["ActiveState"] = "inactive"
        mismatches = self.smoke.check(name, result, expect, {}, None, self.RECORDED)["mismatches"]
        self.assertEqual(len(mismatches), 2, mismatches)
        self.assertTrue(any(m.startswith("display-manager.service") for m in mismatches))


class GdmMaskAndFactsTests(unittest.TestCase):
    """D-12 step 1: gdm masked by the recipe; the builder refuses a display-manager link to an unmasked unit.
    The facts record dpkg holds, the display-manager link and the netplan files."""

    def test_display_manager_must_point_to_a_masked_unit(self):
        recipe = json.loads((HERE / "image/recipe.json").read_text())
        for target, ok in (("/lib/systemd/system/gdm3.service", True), ("/usr/lib/systemd/system/gdm.service", True),
                           ("/usr/lib/systemd/system/lightdm.service", False)):
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "etc/systemd/system").mkdir(parents=True)
                (root / "etc/passwd").write_text("root:x:0:0:root:/root:/bin/bash\n")
                try:
                    os.symlink(target, root / "etc/systemd/system/display-manager.service")
                except OSError:
                    self.skipTest("symlinks unavailable")
                with patch.object(build_image, "run", lambda argv, **kwargs: None), patch.object(build_image, "chroot", lambda *a, **k: None):
                    if ok:
                        self.assertEqual(build_image.hardening(root, recipe, "A")["display_manager"], target)
                    else:
                        with self.assertRaisesRegex(build_image.BuildError, "display-manager"):
                            build_image.hardening(root, recipe, "A")

    def test_facts_name_holds(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "var/lib/dpkg").mkdir(parents=True)
            (root / "var/lib/dpkg/status").write_text("Package: tzdata\nStatus: hold ok installed\nVersion: 2025b\n\n"
                                                      "Package: adduser\nStatus: install ok installed\nVersion: 3.137\n\n")
            self.assertEqual(build_image._dpkg_holds(root), ["tzdata"])
            self.assertEqual(build_image._units(root)["display_manager"], None)
        self.assertTrue(build_image.INTEREST.search("libgps30t64"))
        self.assertEqual([s[0] for s in build_image.STEPS].index("closure"), [s[0] for s in build_image.STEPS].index("kernel") + 1)


class ClosureExtensionRouteTests(unittest.TestCase):
    """IMG2-R1: a root added to CLOSURE_ROOTS before package-closure.json is regenerated (the IMG-4 route) downloads no
    closure deb and does not stop fetch(); build() records image-facts.json and only then stops, so the CI resolve step
    can propose the file. load_closure() (step 8b, `closure --check`) stays strict, and the host tests (the recipe gate of
    the image job) fail on every closure issue except that drift. IMG2-R2: the chrony guard."""

    ROOTS = dict(build_image.CLOSURE_ROOTS)  # the roots of the committed package-closure.json (W2 IMG-4: + the session)

    def fetch(self, cache, roots):
        import deploy
        downloads = []
        with patch.object(build_image, "CLOSURE_ROOTS", roots), \
                patch.object(build_image, "_download", lambda url, target, sha, size, label: downloads.append(url) or "PRESENT"), \
                patch.object(deploy, "verify_cache", lambda cache, components: {"status": "STUB"}):
            return build_image.fetch(cache, ids=[], wheels=False), downloads

    def test_fetch_reports_an_inconsistent_closure_without_downloading(self):
        with tempfile.TemporaryDirectory() as cache:
            result, downloads = self.fetch(cache, dict(self.ROOTS))
            self.assertEqual(result["closure"]["status"], "CLOSURE_DEBS_VERIFIED")
            self.assertEqual(sorted(result["closure"]["debs"]), sorted(p["package"] for p in build_image.load_closure()["packages"]))
            self.assertEqual(len(downloads), len(result["closure"]["debs"]))
            result, downloads = self.fetch(cache, dict(self.ROOTS, srrx_new_root=()))
            self.assertEqual(result["status"], "LOCKED_ARTIFACTS_VERIFIED")
            self.assertEqual(result["closure"]["status"], "CLOSURE_INCONSISTENT")
            self.assertTrue(any("roots must be" in issue for issue in result["closure"]["issues"]), result["closure"])
            self.assertEqual(downloads, [])
        closure = json.loads((HERE / "image/package-closure.json").read_text(encoding="utf-8"))
        with patch.object(build_image, "CLOSURE_ROOTS", dict(self.ROOTS, srrx_new_root=())):
            drift = build_image.closure_roots_issues(closure)
            self.assertEqual(len(drift), 1, drift)  # a root without an account: only the roots differ
            self.assertEqual([i for i in build_image.closure_issues(closure, _lock()) if i not in drift], [])
            with self.assertRaisesRegex(build_image.BuildError, "roots must be"):
                build_image.load_closure()

    def test_committed_closure_matches_the_closure_roots(self):
        drift = build_image.closure_roots_issues(json.loads((HERE / "image/package-closure.json").read_text(encoding="utf-8")))
        if drift:
            self.skipTest("package-closure.json lags CLOSURE_ROOTS until the tagged image run's Resolve step regenerates it "
                          "(GENERATED commit): " + "; ".join(drift))
        self.assertEqual(build_image.load_closure()["roots"], sorted(build_image.CLOSURE_ROOTS))

    def test_build_records_the_facts_then_stops_on_the_closure(self):
        fetched = {"status": "LOCKED_ARTIFACTS_VERIFIED", "artifacts": {}, "verify_cache": {},
                   "closure": {"status": "CLOSURE_INCONSISTENT", "issues": ["roots must be chrony,gpsd,greetd and in packages"]}}

        class Detached:
            def umount_all(self):
                pass

            def detach(self):
                pass

        def facts(cache, work, output=None, keep_mounted=None):
            build_image.dump(output, {"root": {"packages": {}, "packages_total": 0}})
            keep_mounted[:] = [Detached(), Detached(), None, None]
            return {"base_cmdline_status": "VALID", "rescue": {"status": "IDENTIFIED"}}

        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "out"
            staged = (Path(temp) / "stage", Path(temp) / "bundle.tar.gz", {"bundle": {"sha256": "0" * 64}, "stage": {"files": 0}})
            with patch.object(build_image, "require_builder", lambda: None), patch.object(build_image, "fetch", lambda cache: fetched), \
                    patch.object(build_image, "stage_bundle", lambda work: staged), patch.object(build_image, "facts", facts), \
                    patch.object(build_image, "kernel_deb_config", side_effect=AssertionError("the build ran past the closure check")), \
                    patch.object(build_image.LOG, "path", None), patch.object(build_image.LOG, "steps", []):
                with self.assertRaisesRegex(build_image.BuildError, "package-closure.json: roots must be"):
                    build_image.build(Path(temp) / "cache", Path(temp) / "work", out)
            self.assertTrue((out / "image-facts.json").is_file())
            manifest = json.loads((out / "image-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "BLOCKED")
            self.assertIn("closure --resolve", manifest["error"])
            self.assertEqual([s["id"] for s in manifest["steps"]], ["inputs", "base-facts"])

    def test_initstepslew_mailonchange_and_ptpport_stop_the_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "etc/chrony").mkdir(parents=True)
            for line, word in (("initstepslew 10 ntp.example", "initstepslew"), ("mailonchange root 0.5", "mailonchange"),
                               ("ptpport 319", "ptpport")):
                with patch.object(build_image, "chroot", ChronyConfInstallTests.parse(self, line + "\n")), \
                        self.assertRaisesRegex(build_image.BuildError, word):
                    build_image.install_chrony_conf(root)  # e.g. a *.conf in conf.d (chronyd -p prints it)


# Fixture code shared by the parent and a child interpreter that runs with NumPy blocked (sys.modules["numpy"] = None):
# a StorageGuard stand-in over a temporary directory, as software/tests/test_baseband.py DirGuard.
_DIRGUARD = '''
class DirGuard:
    def __init__(self, root):
        self.root = Path(root)
        (self.root / bb.CLASS_DIR).mkdir(parents=True, exist_ok=True)
        self.identity = {"root": str(self.root), "major": 8, "minor": 7}

    def check(self):
        pass

    def open_directory(self, path):
        return os.open(self.root / path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
'''
_SYSFS_UFS = "/sys/devices/platform/soc@0/1d84000.ufshc/host0/target0:0:0/0:0:0:0/block/sda/sda7"  # test_baseband.SYSFS_UFS
_NO_NUMPY_SWEEP = '''
import json, os, sys
from pathlib import Path
sys.modules["numpy"] = None  # import numpy raises ImportError in this interpreter
sys.path.insert(0, sys.argv[1])
from srrx import baseband as bb
bb.DATA_ROOT, now = sys.argv[2], float(sys.argv[3])
bb._sysfs_block_path = lambda major, minor: sys.argv[4]
''' + _DIRGUARD + '''
result = bb.BasebandStore(DirGuard(sys.argv[2]), clock=lambda: now).sweep()
print(json.dumps({"numpy": bb._np is not None, "result": result,
                  "names": sorted(os.listdir(os.path.join(sys.argv[2], bb.CLASS_DIR)))}))
'''
_POSIX = os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "fstatvfs")


class VenvAndUnitInterpreterTests(unittest.TestCase):
    """W2 IMG-3 (D-04): the venv locks and wheels, the freeze and copy checks of build_venvs, each SR-RX python3 unit's
    interpreter class (recipe.json unit_interpreters), the build-manifest draft and the smoke's venv expectations.
    The chroot, pip and QEMU paths themselves run in sr-rx-image.yml."""

    @staticmethod
    def names(wheels):
        return {build_image.normalized(w["name"]) for w in wheels}

    def test_locks_are_closed_subsets_of_the_guest_wheelhouse_and_essentials_drops_the_web_engine(self):
        plan = build_image.venv_plan()
        self.assertEqual(plan["pip"]["filename"], "pip-26.2.2-py3-none-any.whl")
        self.assertEqual(self.names(plan["venvs"]["opt/srrx/venv"]), {"numpy", "pyside6-essentials", "setuptools", "shiboken6"})
        self.assertEqual(self.names(plan["venvs"]["opt/srrx/passes-venv"]),
                         {"certifi", "jplephem", "numpy", "setuptools", "sgp4", "skyfield"})
        wheels = build_image.plan_wheels(plan)
        self.assertEqual(len(wheels), 9)  # pip + 4 + 6, numpy and setuptools shared
        self.assertTrue(all(w["url"].startswith(build_image.WHEEL_URL) and w["hash_verified"] for w in wheels.values()))
        # The full PySide6 of the guest lock adds these four wheels (Chromium is in WebEngine): about 181 MB not installed.
        manifest = json.loads(build_image.WHEELHOUSE.read_text(encoding="utf-8"))
        dropped = {w["name"]: w["size_bytes"] for w in manifest["wheels"] if w["name"] in ("PySide6", "PySide6_Addons", "PySide6_WebEngine", "PySide6_Pdf")}
        self.assertEqual(sum(dropped.values()), 181114548)
        self.assertEqual(set(dropped) & {w["name"] for w in wheels.values()}, set())

    def test_lock_drift_is_refused(self):
        manifest = json.loads(build_image.WHEELHOUSE.read_text(encoding="utf-8"))
        wheels = {build_image.normalized(w["name"]): w for w in manifest["wheels"]}
        guest = {row[3] for row in build_image.lock_lines(build_image.GUEST_LOCK)}
        lock = build_image.lock_lines(build_image.PROJECT / "software/config/hmi-requirements.lock")
        self.assertEqual(build_image.venv_lock_issues(lock, guest, wheels), [])
        no_shiboken = [row for row in lock if row[0] != "shiboken6"]
        self.assertEqual(build_image.venv_lock_issues(no_shiboken, guest, wheels), ["PySide6_Essentials needs shiboken6==6.12.0"])
        other = [(n, v, "0" * 64, n + "==" + v + " --hash=sha256:" + "0" * 64) if n == "numpy" else (n, v, d, l) for n, v, d, l in lock]
        issues = build_image.venv_lock_issues(other, guest, wheels)
        self.assertTrue(any(i.startswith("numpy: line differs") for i in issues) and any("no hash-verified wheel" in i for i in issues), issues)
        self.assertIn("duplicate distribution names", build_image.venv_lock_issues(lock + lock[:1], guest, wheels))
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / "x.lock"
            bad.write_text("numpy>=2\n", encoding="utf-8")
            with self.assertRaisesRegex(build_image.BuildError, "unparsable lock line"):
                build_image.lock_lines(bad)

    def test_fetch_downloads_each_wheel_once_by_its_manifest_hash(self):
        calls = []
        with patch.object(build_image, "_download", lambda url, target, sha, size, label: calls.append((url, Path(target).name, sha, size)) or "PRESENT"):
            result = build_image.fetch_wheels(Path("cache"))
        self.assertEqual(len(calls), 9)
        self.assertEqual(sorted(result), sorted(name for _, name, _, _ in calls))
        self.assertTrue(all(url.endswith("/" + name) for url, name, _, _ in calls))

    def test_freeze_must_equal_the_lock_plus_the_project(self):
        lock = build_image.PROJECT / "software/config/passes-requirements.lock"
        want = build_image.expected_freeze(lock, build_image.project_version())
        self.assertEqual(want["srrx-control"], "0.3.1")
        freeze = [[name, version] for name, version in want.items()]
        self.assertEqual(build_image.freeze_issues(freeze, want), [])
        self.assertEqual(build_image.freeze_issues(freeze + [["pip", "26.2.2"]], want), ["not in the lock: pip 26.2.2"])
        changed = [[n, "1.26.4" if n == "numpy" else v] for n, v in freeze]
        self.assertEqual(build_image.freeze_issues(changed, want), ["versions differ: numpy 1.26.4 != 2.3.5"])
        self.assertEqual(build_image.freeze_issues(freeze[1:], want), ["missing: " + freeze[0][0]])
        self.assertEqual(build_image.freeze_issues([["NumPy", "2.3.5"], ["numpy", "2.3.5"]], want), ["distribution listed twice: numpy"])

    def test_srrx_copy_and_tree_record(self):
        with tempfile.TemporaryDirectory() as temp:
            staged, venv = Path(temp) / "staged/srrx", Path(temp) / "venv"
            installed = venv / "lib/python3.12/site-packages/srrx"
            for root in (staged, installed):
                root.mkdir(parents=True)
                (root / "__init__.py").write_text("")
                (root / "baseband.py").write_text("X = 1\n")
            self.assertEqual(build_image.package_copy_issues(installed, staged), [])
            (installed / "baseband.py").write_text("X = 2\n")
            self.assertEqual(build_image.package_copy_issues(installed, staged), ["srrx copy differs from the staged tree: baseband.py"])
            self.assertEqual(build_image._site_packages(venv), venv / "lib/python3.12/site-packages")
            first = build_image.tree_record(venv)
            self.assertEqual((first["files"], first["so_modules"]), (2, 0))
            (installed / "baseband.py").write_text("X = 1\n")
            self.assertNotEqual(build_image.tree_record(venv)["tree_sha256"], first["tree_sha256"])

    def test_only_bytecode_outside_every_record_is_refused(self):
        # Run 42418461427: pyside6_essentials 6.12.0 ships PySide6/support/__pycache__/*.pyc in its RECORD.
        with tempfile.TemporaryDirectory() as temp:
            venv = Path(temp) / "venv"
            site = venv / "lib/python3.12/site-packages"
            (site / "PySide6/support/__pycache__").mkdir(parents=True)
            (site / "PySide6/support/__pycache__/deprecated.cpython-312.pyc").write_bytes(b"pyc")
            (site / "PySide6_Essentials-6.12.0.dist-info").mkdir()
            (site / "PySide6_Essentials-6.12.0.dist-info/RECORD").write_text(
                "PySide6/support/__pycache__/deprecated.cpython-312.pyc,sha256=x,3\nPySide6_Essentials-6.12.0.dist-info/RECORD,,\n")
            self.assertEqual(build_image.unrecorded_bytecode(venv), [])
            (site / "numpy/__pycache__").mkdir(parents=True)
            (site / "numpy/__pycache__/version.cpython-312.pyc").write_bytes(b"pyc")
            self.assertEqual(build_image.unrecorded_bytecode(venv), ["lib/python3.12/site-packages/numpy/__pycache__/version.cpython-312.pyc"])

    def test_exec_interpreter(self):
        cases = (("/usr/bin/env /opt/srrx/venv/bin/python3 -m srrx.hmi", "/opt/srrx/venv/bin/python3"),
                 ("-/usr/bin/python3 -B /opt/srrx/deployment/deploy.py release-guard", "/usr/bin/python3"),
                 ("/usr/bin/env PYTHONPATH=/x /usr/bin/python3.12 -m srrx.x", "/usr/bin/python3.12"),
                 ("/usr/bin/ssh-keygen -A", None), ("/usr/bin/env -S python3 -m x", None), ("/usr/bin/env readsb", None))
        for line, want in cases:
            self.assertEqual(build_image.exec_interpreter(line.split()), want, line)

    def staged_root(self, temp):
        import deploy
        deploy.stage(Path(temp) / "stage")
        rootfs = Path(temp) / "stage/rootfs"
        for name in ("srrx-boot-check.service", "srrx-ab-commit.service", "srrx-ssh-hostkeys.service"):  # build_image install_boot_chain/hardening
            shutil.copyfile(build_image.FILES / name, rootfs / "etc/systemd/system" / name)
        return rootfs

    def test_recipe_classifies_exactly_the_staged_python_units_and_numpy_units_run_a_venv(self):
        recipe = json.loads(build_image.RECIPE.read_text(encoding="utf-8"))
        classes = recipe["unit_interpreters"]
        self.assertEqual(set(classes["numpy"]) & set(classes["stdlib"]), set())
        with tempfile.TemporaryDirectory() as temp:
            units = build_image.python_units(self.staged_root(temp))
        self.assertEqual(set(units), set(classes["numpy"]) | set(classes["stdlib"]))
        venvs = {"/" + v + "/bin/python3" for v in build_image.VENVS}
        for unit in classes["numpy"]:
            self.assertTrue(set(units[unit]["interpreters"]) <= venvs, (unit, units[unit]))
        for unit in classes["stdlib"]:
            self.assertEqual(units[unit]["interpreters"], ["/usr/bin/python3"], (unit, units[unit]))
        self.assertEqual(units["srrx-baseband-sweep.service"]["commands"],
                         [{"key": "ExecStart", "interpreter": "/usr/bin/python3", "module": "srrx.baseband"}])
        self.assertEqual(units["srrx.service"]["files"], ["etc/systemd/system/srrx.service", "etc/systemd/system/srrx.service.d/20-release-guard.conf"])
        self.assertEqual(units["srrx-menu.service"]["files"], ["usr/lib/systemd/user/srrx-menu.service"])

    def test_findings_block_a_missing_or_numpy_less_interpreter_and_an_unclassified_unit(self):
        classes = json.loads(build_image.RECIPE.read_text(encoding="utf-8"))["unit_interpreters"]
        with tempfile.TemporaryDirectory() as temp:
            units = build_image.python_units(self.staged_root(temp))
        good = {"/usr/bin/python3": {"present": True, "numpy": None}, "/opt/srrx/venv/bin/python3": {"present": True, "numpy": "2.3.5"},
                "/opt/srrx/passes-venv/bin/python3": {"present": True, "numpy": "2.3.5"}}
        found, blockers = build_image.unit_interpreter_findings(units, good, classes)
        self.assertEqual(blockers, [])
        self.assertEqual(found["classified_not_staged"], [])
        self.assertEqual(found["units"]["srrx-passes@.service"]["needs"], "numpy")
        # The r2 image before W2 IMG-3: no venv at all.
        _, blockers = build_image.unit_interpreter_findings(units, {"/usr/bin/python3": good["/usr/bin/python3"]}, classes)
        self.assertEqual([b.split(":", 1)[0] for b in blockers], ["unit_interpreter_missing"])
        self.assertIn("srrx-menu.service (/opt/srrx/venv/bin/python3)", blockers[0])
        probes = dict(good, **{"/opt/srrx/passes-venv/bin/python3": {"present": True, "numpy": None}})
        _, blockers = build_image.unit_interpreter_findings(units, probes, classes)
        self.assertEqual(blockers, ["unit_interpreter_without_numpy: srrx-passes@.service (/opt/srrx/passes-venv/bin/python3) "
                                    "(recipe.json unit_interpreters.numpy)"])
        fewer = dict(classes, stdlib={k: v for k, v in classes["stdlib"].items() if k != "srrx-timegate.service"})
        _, blockers = build_image.unit_interpreter_findings(units, good, fewer)
        self.assertEqual(blockers, ["unit_interpreter_unclassified: srrx-timegate.service (neither list of recipe.json unit_interpreters)"])
        route_a = {k: v for k, v in units.items() if k != "srrx-ab-commit.service"}
        found, blockers = build_image.unit_interpreter_findings(route_a, good, classes)
        self.assertEqual((blockers, found["classified_not_staged"]), ([], ["srrx-ab-commit.service"]))
        tags = build_image.blocking_closes_at(["unit_interpreter_missing: x", "unit_interpreter_without_numpy: y",
                                               "unit_interpreter_unclassified: z", "hmi_venv_qt_offscreen_failed: q",
                                               "build_manifest_draft_blocked: w"])
        self.assertEqual([t["closes_at"] for t in tags], ["recipe"] * 5)
        self.assertNotIn("target_python_without_numpy", [p for p, _, _ in build_image.BLOCKER_CLOSES_AT])

    @unittest.skipUnless(_POSIX, "the dirfd-relative baseband store needs Linux")
    def test_the_sweep_unit_needs_no_numpy(self):
        # recipe.json unit_interpreters.stdlib: srrx-baseband-sweep.service keeps r2's /usr/bin/python3 (no NumPy).
        import array
        software = str(build_image.PROJECT / "software")
        sys.path.insert(0, software)
        from srrx import baseband as bb
        aos = 1_800_000_000.0
        with tempfile.TemporaryDirectory(prefix="srrx-bb-") as temp:
            namespace = {"Path": Path, "os": os, "bb": bb}
            exec(_DIRGUARD, namespace)
            with patch.object(bb, "DATA_ROOT", temp), patch.object(bb, "_sysfs_block_path", lambda major, minor: _SYSFS_UFS), \
                    patch.object(bb, "_preallocate", None):
                store = bb.BasebandStore(namespace["DirGuard"](temp), clock=lambda: aos - 50.0)
                recording = store.begin(bb.window(40001, "Meteor-M N2-3", 137_900_000, 72_000, aos, aos + 600,
                                                  bb.iso_utc(aos), bb.iso_utc(aos + 600)))
                try:
                    recording.write(array.array("h", [i % 200 - 100 for i in range(8192)]))  # ci16, little-endian hosts
                    meta = recording.finish(created_s=aos - 50.0, first_block_s=aos - 50.0, clipped=0, gaps=0, joins=0,
                                            source="SIMULATION", group_delay=685, stop_reason="WINDOW_END")
                finally:
                    store.end()
            rid = meta["global"]["srrx:recording_id"]
            directory = Path(temp) / bb.CLASS_DIR
            os.utime(directory / (rid + bb.DATA_SUFFIX), (aos - 50.0, aos - 50.0))
            (directory / "lrpt-ffffffffffffffff.sigmf-data").write_bytes(b"\0" * 8)
            (directory / "lrpt-ffffffffffffffff.sigmf-meta").write_text("{}")  # invalid: removed
            (directory / "stray.txt").write_text("x")  # a file nobody may keep here: removed
            outcomes = []
            for now in (aos - 40.0, aos + bb.RETENTION_S + 100.0):  # fresh, then older than 24 h
                done = subprocess.run([sys.executable, "-I", "-B", "-c", _NO_NUMPY_SWEEP, software, temp, str(now), _SYSFS_UFS],
                                      capture_output=True, text=True, timeout=120)
                self.assertEqual(done.returncode, 0, done.stderr[-2000:])
                outcomes.append(json.loads(done.stdout.strip().splitlines()[-1]))
        self.assertEqual([o["numpy"] for o in outcomes], [False, False])
        self.assertEqual(outcomes[0]["result"], {"deleted": 1, "kept": 1, "foreign_directories": 0, "skipped": None})
        self.assertEqual(outcomes[0]["names"], sorted([bb.LOCK_NAME, rid + bb.DATA_SUFFIX, rid + bb.META_SUFFIX]))
        self.assertEqual(outcomes[1]["result"], {"deleted": 1, "kept": 0, "foreign_directories": 0, "skipped": None})
        self.assertEqual(outcomes[1]["names"], [bb.LOCK_NAME])

    @unittest.skipUnless(_POSIX, "the srrx modules of the system units import Linux-only modules")
    def test_stdlib_units_import_their_modules_without_numpy(self):
        classes = json.loads(build_image.RECIPE.read_text(encoding="utf-8"))["unit_interpreters"]
        with tempfile.TemporaryDirectory() as temp:
            units = build_image.python_units(self.staged_root(temp))
        modules = sorted({c["module"] for unit in classes["stdlib"] for c in units[unit]["commands"] if c["module"]})
        self.assertIn("srrx.baseband", modules)
        code = ("import importlib, json, sys\nsys.modules['numpy'] = None\nsys.path.insert(0, sys.argv[1])\n"
                "for name in sys.argv[2:]:\n    importlib.import_module(name)\nprint(json.dumps(sorted(sys.argv[2:])))\n")
        done = subprocess.run([sys.executable, "-I", "-B", "-c", code, str(build_image.PROJECT / "software")] + modules,
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])

    def test_build_manifest_draft_is_open_and_refuses_what_verify_build_refuses(self):
        with tempfile.TemporaryDirectory() as temp:
            root, out = Path(temp) / "root", Path(temp) / "out"
            prefix = root / "opt/srrx"
            (prefix / "venv/lib/python3.12/site-packages").mkdir(parents=True)
            (prefix / "venv/lib/python3.12/site-packages/x.py").write_text("X = 1\n")
            (prefix / "software").mkdir()
            (prefix / "software/a.py").write_text("A = 1\n")
            out.mkdir()
            try:
                os.symlink("lib", prefix / "venv/lib64")
            except OSError:
                pass
            draft = build_image.build_manifest_draft(root, out)
            self.assertEqual((draft["status"], draft["evidence"]), ("OPEN", {"source_audit": "OPEN", "tx_negative_tests": "OPEN"}))
            written = json.loads((out / build_image.BUILD_MANIFEST_DRAFT).read_text(encoding="utf-8"))
            self.assertEqual(written["status"], "OPEN")
            self.assertIn("venv/lib/python3.12/site-packages/x.py", written["files"])
            self.assertNotIn("REVIEWED", json.dumps(written))
            (prefix / "software/rtl_tcp").write_text("")  # a verify-build refusal (deploy.BAD_NAMES)
            (out / build_image.BUILD_MANIFEST_DRAFT).unlink()
            blocked = build_image.build_manifest_draft(root, out)
            self.assertEqual(blocked["status"], "BLOCKED")
            self.assertFalse((out / build_image.BUILD_MANIFEST_DRAFT).exists())

    def test_steps_workflow_and_smoke_bound(self):
        steps = [s[0] for s in build_image.STEPS]
        self.assertEqual(steps.index("venvs"), steps.index("enable") + 1)
        self.assertEqual(steps.index("data"), steps.index("venvs") + 1)
        workflow = (build_image.PROJECT.parent / ".github/workflows/sr-rx-image.yml").read_text(encoding="utf-8")
        for text in ("sat-receiver-audit/deployment/linux_lab/wheelhouse-manifest.json", "sat-receiver-audit/deployment/linux_lab/wheelhouse-requirements.txt",
                     "WHEELS_KEY=srrx-wheels-", "path: ~/srrx-cache/wheels", "key: ${{ env.WHEELS_KEY }}"):
            self.assertIn(text, workflow)
        self.assertEqual(bootchain.SELFTEST_PYTHON.as_posix(), "/opt/srrx/passes-venv/bin/python3")
        self.assertEqual(set(bootchain.SMOKE_VENVS), {"/" + v for v in build_image.VENVS})
        self.assertGreaterEqual(bootchain.SMOKE_SELFTEST_LIMIT, 2400)

    def test_smoke_compares_the_venvs_and_the_live_selftest_interpreter(self):
        import smoke_qemu
        recorded = {"/opt/srrx/venv": {"numpy": "2.3.5", "qt_offscreen": {"status": "OK", "result": {"qt": "6.12.0", "platform": "offscreen"}}},
                    "/opt/srrx/passes-venv": {"numpy": "2.3.5"}}
        observed = {"/opt/srrx/venv": {"present": True, "numpy": {"python": "3.12.3", "numpy": "2.3.5"},
                                       "qt_offscreen": {"qt": "6.12.0", "platform": "offscreen"}},
                    "/opt/srrx/passes-venv": {"present": True, "numpy": {"python": "3.12.3", "numpy": "2.3.5"}}}
        live = {"interpreter": "/opt/srrx/passes-venv/bin/python3", "interpreter_numpy": True}
        self.assertEqual(smoke_qemu.venv_mismatches(observed, recorded, live), [])
        self.assertEqual(len(smoke_qemu.venv_mismatches(observed, recorded, {"interpreter": "/usr/bin/python3", "interpreter_numpy": False})), 1)
        broken = copy.deepcopy(observed)
        broken["/opt/srrx/venv"]["qt_offscreen"] = {"error": "exit 1: qt.qpa.plugin: Could not load the Qt platform plugin"}
        broken["/opt/srrx/passes-venv"] = {"present": False}
        self.assertEqual(len(smoke_qemu.venv_mismatches(broken, recorded, live)), 2)
        self.assertEqual(smoke_qemu.venv_mismatches(None, recorded, live), ["no venv report from the booted slot: None"])
        self.assertEqual(smoke_qemu.venv_mismatches(observed, {}, live), ["image-manifest.json records no venvs (build_image.build_venvs)"])
        # In check(): only the selftest boot is compared, and with numpy the live rows equal the build rows.
        recipe = json.loads((HERE / "image/recipe.json").read_text())
        units = {"srrx-boot-check.service": {"ActiveState": "active"}, "boot-complete.target": {"ActiveState": "active"},
                 "systemd-bless-boot.service": {"ActiveState": "active"}, "srrx.service": {"ActiveState": "inactive", "UnitFileState": "disabled"}}
        report = {"boot_check": {"slot": "A", "status": "BOOT_SELF_CHECK_OK"}, "units": units, "bless_boot_status": "good", "pending_jobs": [],
                  "masked_units": {u: {"LoadState": "masked"} for u in recipe["mask"]["units"]}, "venvs": observed,
                  "selftest": dict(live, status="BLOCKED", fail_or_blocked_rows={"RX-S2": ["radio_off_binding_missing"]})}
        blessed = sorted(["labA.conf", "labB.conf", "labA-rescue.conf", "labB-rescue.conf"])
        name, expect = smoke_qemu.SCENARIOS[0]
        result = {"qemu_exit": 0, "report": report, "entries_after": blessed}
        rows = {"RX-S2": ["radio_off_binding_missing"]}
        self.assertEqual(smoke_qemu.check(name, result, expect, rows, None, None, recorded)["status"], "MODEL_PASS")
        report["selftest"]["fail_or_blocked_rows"] = dict(rows, **smoke_qemu.INTERPRETER_ROWS)
        self.assertEqual(smoke_qemu.check(name, result, expect, rows, None, None, recorded)["status"], "MODEL_FAIL")
        del report["venvs"]
        report["selftest"]["fail_or_blocked_rows"] = rows
        self.assertIn("no venv report from the booted slot: None", smoke_qemu.check(name, result, expect, rows, None, None, recorded)["mismatches"])


_KVER = "6.18.2-4-qcom"
_VERMAGIC = "6.18.2-4-qcom SMP preempt mod_unload aarch64"


class PpsGpioImageTests(unittest.TestCase):
    """W2 IMG-4 (D-13): the builder-built pps-gpio module. The dkms/gcc-12 build and depmod run in the image job; here the
    kernel-config gate, the fetch-only source, the install path, the records and the refusals, with stand-in tools."""

    def setUp(self):
        self.recipe = json.loads((HERE / "image/recipe.json").read_text(encoding="utf-8"))
        sys.path.insert(0, str(HERE / "system"))
        self.addCleanup(sys.path.remove, str(HERE / "system"))
        import pps_dkms
        self.pps_dkms = pps_dkms

    def test_recipe_pins_the_path_vermagic_and_the_locked_headers(self):
        spec = self.recipe["pps_gpio"]
        self.assertEqual(spec["install_path"], "/lib/modules/" + _KVER + "/updates/srrx/pps-gpio.ko")
        self.assertEqual(spec["vermagic"], _VERMAGIC)
        self.assertEqual(spec["vermagic"].split()[0], self.recipe["kernel_version"])
        self.assertIn(spec["headers_artifact"], build_image.lock_artifacts())
        self.assertEqual(spec["dkms_package"], "srrx-pps-gpio")
        self.assertEqual(self.pps_dkms.KERNEL_RELEASE, self.recipe["kernel_version"])
        self.assertFalse({"author", "description"} & set(build_image.PPS_MODINFO_FIELDS))  # MODULE_AUTHOR carries addresses
        # merged /usr: kmod may name the installed file under /usr/lib/modules; both are the recipe's path
        for name in (spec["install_path"], "/usr" + spec["install_path"]):
            self.assertEqual(bootchain.module_path(name), spec["install_path"])
        self.assertIsNone(bootchain.module_path(""))
        for key in ("CONFIG_PPS", "CONFIG_PPS_CLIENT_GPIO", "CONFIG_DRM_SIMPLEDRM", "CONFIG_SYSFB_SIMPLEFB", "CONFIG_VT",
                    "CONFIG_USB_XHCI_PCI", "CONFIG_USB_HID"):
            self.assertIn(key, build_image.CONFIG_KEYS)

    def test_kernel_config_gate(self):
        locked = {"CONFIG_MODULE_SIG": "not set", "CONFIG_MODULE_SIG_FORCE": None, "CONFIG_PPS": "y", "CONFIG_PPS_CLIENT_GPIO": "not set",
                  "CONFIG_MODULE_UNLOAD": "y"}  # boot/config-6.18.2-4-qcom of the locked deb (facts of run 43132771832)
        record, blocker = build_image.pps_kernel_findings(locked)
        self.assertIsNone(blocker)
        self.assertEqual(record["CONFIG_MODULE_SIG"], "not set")
        cases = ((dict(locked, CONFIG_MODULE_SIG="y", CONFIG_MODULE_SIG_FORCE="y"), "pps_gpio_signature_enforced"),
                 (dict(locked, CONFIG_PPS="m"), "pps_gpio_kernel_config"),
                 (dict(locked, CONFIG_PPS_CLIENT_GPIO="m"), "pps_gpio_kernel_config"))
        for kconfig, prefix in cases:
            _, blocker = build_image.pps_kernel_findings(kconfig)
            self.assertTrue(blocker.startswith(prefix + ": "), blocker)
            self.assertEqual(build_image.blocking_closes_at([blocker])[0]["closes_at"], "recipe")
        self.assertIsNone(build_image.pps_kernel_findings(dict(locked, CONFIG_MODULE_SIG="y", CONFIG_MODULE_SIG_FORCE="not set"))[1])
        with patch.object(build_image, "pps_pin", side_effect=AssertionError("a blocked kernel must not reach the build")):
            record, blocker = build_image.build_pps_module("/nonexistent", "/nonexistent", "/nonexistent", self.recipe,
                                                           dict(locked, CONFIG_MODULE_SIG_FORCE="y"))
        self.assertEqual((record["status"], record["why"]), ("BLOCKED", blocker))

    def test_source_is_fetch_only_by_its_pin(self):
        pin = build_image.pps_pin()
        self.assertFalse(pin["committed"])
        self.assertFalse((HERE / "system/dkms/pps-gpio/pps-gpio.c").exists())
        calls = []
        with tempfile.TemporaryDirectory() as cache, \
                patch.object(build_image, "_download", lambda url, target, sha, size, label: calls.append((url, Path(target), sha, size)) or "PRESENT"):
            self.assertEqual(build_image.fetch_pps_source(cache), "PRESENT")
            self.assertEqual(calls, [(pin["url"], Path(cache) / "pps-gpio/pps-gpio.c", pin["sha256"], pin["size"])])
        bad = dict(pin, url="https://example.invalid/pps-gpio.c")
        with patch.object(build_image, "load_json", lambda path: {"pps_gpio": bad}), self.assertRaisesRegex(build_image.BuildError, "fetch-only"):
            build_image.pps_pin()

    def fake_build(self, temp, vermagic=_VERMAGIC, compressed=False):
        """build_pps_module with stand-ins for dpkg-deb, dkms, depmod and modinfo; returns (record, root, calls)."""
        temp = Path(temp)
        root, cache, work = temp / "root", temp / "cache", temp / "work"
        (root / "usr/lib/modules" / _KVER).mkdir(parents=True)
        (cache / "pps-gpio").mkdir(parents=True)
        work.mkdir()
        source = b"/* stand-in for the fetch-only radxa/kernel file */\n"
        (cache / "pps-gpio/pps-gpio.c").write_bytes(source)
        module = (b"\x7fELF" + b"\0" * 60 + b"license=GPL\0author=Someone <someone@example.org>\0vermagic=" + vermagic.encode() + b"\0")
        pin = dict(build_image.pps_pin(), sha256=hashlib.sha256(source).hexdigest(), size=len(source))
        calls = []

        def fake_run(argv, check=True, **kwargs):
            argv = [str(a) for a in argv]
            calls.append(argv)
            if argv[:2] == ["dpkg-deb", "-x"]:
                (Path(argv[3]) / "usr/src" / ("linux-headers-" + _KVER)).mkdir(parents=True)
                (Path(argv[3]) / "usr/src" / ("linux-headers-" + _KVER) / "Makefile").write_text("# stand-in\n")
            if argv[:2] == ["dkms", "build"]:
                tree = Path(argv[argv.index("--dkmstree") + 1]) / "srrx-pps-gpio/1.2.0+lab1" / _KVER / "aarch64/module"
                tree.mkdir(parents=True)
                (tree / ("pps-gpio.ko" + (".xz" if compressed else ""))).write_bytes(module)
            out = {"gcc-12": "gcc-12 (Ubuntu 12.4.0-2ubuntu1~24.04) 12.4.0\n", "dkms": "dkms-3.0.11\n"}.get(argv[0], "")
            return subprocess.CompletedProcess(argv, 0, out, "")

        def fake_chroot(where, argv, check=True, **kwargs):
            calls.append(["chroot"] + list(argv))
            if argv[0] == "depmod":
                (root / "usr/lib/modules" / _KVER / "modules.dep").write_text("kernel/a.ko.zst:\nupdates/srrx/pps-gpio.ko:\n")
            out = ""
            if argv[0] == "modinfo":
                field = "filename" if "-n" in argv else argv[argv.index("-F") + 1]
                out = {"filename": self.recipe["pps_gpio"]["install_path"], "vermagic": vermagic, "name": "pps_gpio", "license": "GPL",
                       "depends": "", "srcversion": "0123456789ABCDEF0123456"}.get(field, "")
            return subprocess.CompletedProcess(argv, 0, out + "\n", "")
        with patch.object(build_image, "run", fake_run), patch.object(build_image, "chroot", fake_chroot), \
                patch.object(build_image.shutil, "which", lambda tool: "/usr/bin/" + tool), \
                patch.object(build_image, "pps_pin", lambda: pin), patch.object(build_image, "fetch_pps_source", lambda cache: "PRESENT"), \
                patch.object(self.pps_dkms, "lock", lambda: pin), \
                patch.object(build_image, "lock_artifacts", lambda: {"linux-headers-6.18.2-4-qcom": {"cache_path": "headers.deb"}}):
            kconfig = {"CONFIG_MODULE_SIG": "not set", "CONFIG_PPS": "y", "CONFIG_PPS_CLIENT_GPIO": "not set"}
            record, blocker = build_image.build_pps_module(root, cache, work, self.recipe, kconfig)
        self.assertIsNone(blocker)
        return record, root, calls

    def test_build_installs_under_updates_srrx_and_records_no_author(self):
        with tempfile.TemporaryDirectory() as temp:
            record, root, calls = self.fake_build(temp)
            target = root / "usr/lib/modules" / _KVER / "updates/srrx/pps-gpio.ko"
            self.assertTrue(target.is_file())
            self.assertEqual(record["sha256"], hashlib.sha256(target.read_bytes()).hexdigest())
        self.assertEqual((record["status"], record["vermagic"], record["path"]), ("INSTALLED", _VERMAGIC, self.recipe["pps_gpio"]["install_path"]))
        self.assertEqual(record["modules_dep"], "updates/srrx/pps-gpio.ko:")
        text = json.dumps(record)
        self.assertNotIn("author", text)
        self.assertNotIn("@", text)  # no address of the upstream file or the module
        build = next(c for c in calls if c[:2] == ["dkms", "build"])
        self.assertEqual(build[2:7], ["-m", "srrx-pps-gpio", "-v", "1.2.0+lab1", "-k"])
        self.assertIn("--kernelsourcedir", build)
        self.assertTrue(all(Path(build[build.index(flag) + 1]).name.startswith("pps-dkms") for flag in ("--sourcetree", "--dkmstree")))
        self.assertIn(["chroot", "depmod", "-a", _KVER], calls)
        self.assertFalse(any("author" in " ".join(c) for c in calls))

    def test_compressed_module_and_wrong_vermagic(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(build_image.subprocess, "run", lambda argv, stdout=None, **k: stdout.write(
                    (b"\x7fELF" + b"\0" * 60 + b"vermagic=" + _VERMAGIC.encode() + b"\0")) and subprocess.CompletedProcess(argv, 0)):
                record, _, _ = self.fake_build(temp, compressed=True)
            self.assertEqual(record["built_module"], "pps-gpio.ko.xz")
        with tempfile.TemporaryDirectory() as temp, self.assertRaisesRegex(build_image.BuildError, "vermagic"):
            self.fake_build(temp, vermagic="6.18.2-4-qcom SMP mod_unload aarch64")

    def test_modules_dir_never_follows_a_link(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "usr/lib/modules" / _KVER).mkdir(parents=True)
            self.assertEqual(build_image.modules_dir(root, _KVER), (root / "usr/lib/modules" / _KVER).resolve())
            with self.assertRaisesRegex(build_image.BuildError, "no /lib/modules"):
                build_image.modules_dir(root, "7.0.11-7-qcom")
            try:
                os.symlink(temp, root / "lib")
            except OSError:
                self.skipTest("symlinks unavailable")
            shutil.rmtree(root / "usr")
            with self.assertRaisesRegex(build_image.BuildError, "no /lib/modules"):
                build_image.modules_dir(root, _KVER)  # lib/ is a link: never followed


class SessionImageTests(unittest.TestCase):
    """W2 IMG-4 (D-12 image part): the session packages through the closure, the SYS-SESSION files kept over the package
    conffiles, greetd as display-manager with gdm masked, and the console unit left disabled."""

    def setUp(self):
        self.recipe = json.loads((HERE / "image/recipe.json").read_text(encoding="utf-8"))
        sys.path.insert(0, str(HERE / "system"))
        self.addCleanup(sys.path.remove, str(HERE / "system"))
        import system_files
        self.system = system_files

    def test_closure_carries_the_session_with_its_account(self):
        closure = build_image.load_closure()
        by_name = {p["package"]: p for p in closure["packages"]}
        spec = self.recipe["session"]
        self.assertLessEqual(set(spec["packages"]), set(build_image.CLOSURE_ROOTS))
        self.assertEqual(closure["roots"], sorted(build_image.CLOSURE_ROOTS))
        self.assertEqual((by_name["greetd"]["version"], by_name["labwc"]["version"]), ("0.9.0-4ubuntu1", "0.7.1-1build1"))  # STACK.md:160/:884
        self.assertTrue(all(by_name[p]["r2_version"] is None and by_name[p]["reason"].startswith("root (STACK.md:160")
                            for p in spec["packages"]))
        self.assertIn("_greetd", closure["expected_accounts"])
        self.assertEqual(spec["display_manager"], "greetd.service")
        self.assertTrue({"gdm.service", "gdm3.service"} <= set(self.recipe["mask"]["units"]))
        self.assertIn("labwc", self.recipe["holds"]["names"])  # held once installed (STACK.md:884: 0.7.4+lab1 later)

    def fake_root(self, temp):
        root, stage = Path(temp) / "root", Path(temp) / "stage"
        status = "".join("Package: %s\nStatus: install ok installed\nVersion: 1\n\n" % p for p in self.recipe["session"]["packages"])
        (root / "var/lib/dpkg").mkdir(parents=True)
        (root / "var/lib/dpkg/status").write_text(status)
        files = {}
        for relative, text in self.system.session_files().items():
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(text, encoding="utf-8", newline="\n")
            files[relative] = hashlib.sha256(text.encode()).hexdigest()
        (root / "etc/greetd/config.toml.dpkg-dist").write_text("[terminal]\nvt = 7\n")
        stage.mkdir()
        (stage / "stage-files.json").write_text(json.dumps({"files": files}))
        (root / "etc/passwd").write_text("root:x:0:0:root:/root:/bin/bash\nsrrx-ui:x:985:985:SR-RX touch session:/var/lib/srrx-ui:/usr/sbin/nologin\n")
        (root / "etc/group").write_text("root:x:0:\nlabd:x:990:srrx-ui\nsrrx-ui:x:985:\n")
        (root / "etc/systemd/system").mkdir(parents=True, exist_ok=True)
        os.symlink("/lib/systemd/system/gdm3.service", root / "etc/systemd/system/display-manager.service")
        return root, stage

    def install(self, root, stage, default="graphical.target"):
        def fake_run(argv, check=True, **kwargs):
            argv = [str(a) for a in argv]
            out = ""
            if argv[-2:] == ["enable", "greetd.service"]:
                os.symlink("/usr/lib/systemd/system/greetd.service", root / "etc/systemd/system/display-manager.service")
            elif argv[-1] == "get-default":
                out = default + "\n"
            elif "is-enabled" in argv:
                out = "disabled\n"
            return subprocess.CompletedProcess(argv, 0, out, "")
        with patch.object(build_image, "run", fake_run):
            return build_image.install_session(root, self.recipe, stage)

    def test_install_session_moves_the_display_manager_to_greetd(self):
        with tempfile.TemporaryDirectory() as temp:
            try:
                root, stage = self.fake_root(temp)
            except OSError:
                self.skipTest("symlinks unavailable")
            record = self.install(root, stage)
        self.assertEqual(record["display_manager"], {"before": "/lib/systemd/system/gdm3.service", "after": "/usr/lib/systemd/system/greetd.service"})
        self.assertEqual(record["default_target"], "graphical.target")
        self.assertEqual(record["console_unit"], {"srrx-menu.service": "disabled"})
        self.assertEqual(record["package_copies"], ["/etc/greetd/config.toml.dpkg-dist"])
        self.assertEqual(set(record["files"]), {"/" + p for p in self.system.session_files()})
        self.assertEqual((record["session_user"]["name"], record["session_user"]["groups"]), ("srrx-ui", ["labd"]))

    def test_any_other_session_state_stops_the_build(self):
        def config_replaced(root):
            (root / "etc/greetd/config.toml").write_text("[default_session]\ncommand = \"agreety --cmd /bin/sh\"\n")

        def greetd_conf(root):
            (root / "etc/greetd/greetd.conf").write_text("[terminal]\nvt = 7\n")

        def console_enabled(root):
            (root / "etc/systemd/user/graphical-session.target.wants").mkdir(parents=True)
            os.symlink("/usr/lib/systemd/user/srrx-menu.service", root / "etc/systemd/user/graphical-session.target.wants/srrx-menu.service")

        def lightdm(root):
            (root / "etc/systemd/system/display-manager.service").unlink()
            os.symlink("/lib/systemd/system/lightdm.service", root / "etc/systemd/system/display-manager.service")

        def no_package(root):
            (root / "var/lib/dpkg/status").write_text("Package: greetd\nStatus: install ok installed\nVersion: 1\n\n")
        for change, word, default in ((config_replaced, "differ from the controller bundle", "graphical.target"),
                                      (greetd_conf, "must not exist", "graphical.target"),
                                      (console_enabled, "enabled in the image", "graphical.target"),
                                      (lightdm, "before the session step", "graphical.target"), (no_package, "not installed", "graphical.target"),
                                      (lambda root: None, "default target", "multi-user.target")):
            with tempfile.TemporaryDirectory() as temp:
                try:
                    root, stage = self.fake_root(temp)
                    change(root)
                except OSError:
                    self.skipTest("symlinks unavailable")
                with self.assertRaisesRegex(build_image.BuildError, word):
                    self.install(root, stage, default)

    def test_hardening_accepts_greetd_as_the_display_manager(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "etc/systemd/system").mkdir(parents=True)
            (root / "etc/passwd").write_text("root:x:0:0:root:/root:/bin/bash\n")
            try:
                os.symlink("/usr/lib/systemd/system/greetd.service", root / "etc/systemd/system/display-manager.service")
            except OSError:
                self.skipTest("symlinks unavailable")
            with patch.object(build_image, "run", lambda argv, **kwargs: None), patch.object(build_image, "chroot", lambda *a, **k: None):
                self.assertEqual(build_image.hardening(root, self.recipe, "A")["display_manager"], "/usr/lib/systemd/system/greetd.service")

    def test_steps_and_workflow(self):
        steps = dict(build_image.STEPS)
        self.assertIn("pps-gpio", steps["kernel"])
        self.assertIn("greetd.service", steps["enable"])
        self.assertIn("greetd", steps["closure"])
        workflow = (build_image.PROJECT.parent / ".github/workflows/sr-rx-image.yml").read_text(encoding="utf-8")
        for text in ("gcc-12 make kmod dkms", "smoke_qemu.py --session", "session-report.json", "id: build"):
            self.assertIn(text, workflow)


class SmokePpsAndSessionTests(unittest.TestCase):
    """W2 IMG-4: smoke_qemu.pps_mismatches on every boot, greetd as display-manager.service, and the separate session scenario."""

    PPS = {"status": "INSTALLED", "path": "/lib/modules/6.18.2-4-qcom/updates/srrx/pps-gpio.ko", "sha256": "a" * 64, "vermagic": _VERMAGIC}
    SESSION = {"display_manager": {"before": "/lib/systemd/system/gdm3.service", "after": "/usr/lib/systemd/system/greetd.service"},
               "files": {"/etc/greetd/config.toml": "c" * 64}}

    def setUp(self):
        import smoke_qemu
        self.smoke = smoke_qemu
        self.recipe = json.loads((HERE / "image/recipe.json").read_text(encoding="utf-8"))

    def pps(self):
        return {"modprobe": {"exit_code": 0, "stderr": ""}, "loaded": True, "initstate": "live", "taint": "O", "filename": self.PPS["path"],
                "sha256": "a" * 64, "vermagic": _VERMAGIC, "uname_r": _KVER, "pps_devices": []}

    def session(self):
        return {"model": {"environment": {"bound": True, "line": "WLR_RENDERER=pixman"}, "console": {"runtime_link": "/run/systemd/user/x"}},
                "user": {"name": "srrx-ui", "uid": 985}, "up": True, "stable": True, "seconds_until_up": 240,
                "units": {"greetd.service": {"ActiveState": "active", "SubState": "running", "NRestarts": "0"},
                          "display-manager.service": {"Id": "greetd.service", "ActiveState": "active"},
                          "graphical.target": {"ActiveState": "active"}},
                "console": {"ActiveState": "active", "SubState": "running", "ConditionResult": "yes"}, "user_failed_units": [],
                "lab_session_state": {"mode": None, "reason": None, "failures": None},
                "logind_sessions": {"2": {"Name": "srrx-ui", "Class": "greeter", "Active": "yes", "Seat": "seat0", "VTNr": "1"}},
                "greetd_config_sha256": "c" * 64, "greetd_conf_present": False, "journal": "labwc: started"}

    def test_pps_module_must_load_as_built(self):
        self.assertEqual(self.smoke.pps_mismatches(self.pps(), self.PPS), [])
        cases = (("modprobe", {"exit_code": 1, "stderr": "modprobe: FATAL: Module pps_gpio not found"}), ("initstate", "coming"),
                 ("sha256", "b" * 64), ("filename", "/lib/modules/6.18.2-4-qcom/kernel/drivers/pps/clients/pps-gpio.ko.zst"),
                 ("uname_r", "6.18.2-3-qcom"))
        for key, value in cases:
            observed = dict(self.pps(), **{key: value})
            self.assertTrue(self.smoke.pps_mismatches(observed, self.PPS), key)
        self.assertTrue(self.smoke.pps_mismatches(self.pps(), dict(self.PPS, status="BLOCKED"))[0].startswith("image-manifest.json records no"))
        self.assertTrue(self.smoke.pps_mismatches({"unavailable": "OSError"}, self.PPS)[0].startswith("no pps_gpio report"))

    def report(self, display_manager):
        return {"boot_check": {"slot": "A", "status": "BOOT_SELF_CHECK_OK"}, "bless_boot_status": "clean", "pending_jobs": [],
                "units": {"srrx-boot-check.service": {"ActiveState": "active"}, "systemd-bless-boot.service": {"ActiveState": "inactive"},
                          "srrx.service": {"ActiveState": "inactive", "UnitFileState": "disabled"}},
                "masked_units": {u: {"LoadState": "masked"} for u in self.recipe["mask"]["units"]},
                "display_manager": display_manager, "pps_gpio": self.pps()}

    def test_check_wants_greetd_as_the_display_manager_and_pps_on_every_boot(self):
        name, expect = self.smoke.SCENARIOS[2]
        entries = sorted(["labA.conf", "labB+0-1.conf", "labA-rescue.conf", "labB-rescue.conf"])
        greetd = {"Id": "greetd.service", "LoadState": "loaded", "ActiveState": "inactive"}
        result = {"qemu_exit": 0, "report": self.report(greetd), "entries_after": entries}
        self.assertEqual(self.smoke.check(name, result, expect, {}, None, None, None, self.PPS, self.SESSION)["status"], "MODEL_PASS")
        result["report"]["display_manager"] = {"Id": "gdm3.service", "LoadState": "masked"}
        mismatches = self.smoke.check(name, result, expect, {}, None, None, None, self.PPS, self.SESSION)["mismatches"]
        self.assertEqual(len(mismatches), 1, mismatches)
        self.assertTrue(mismatches[0].startswith("display-manager.service"))
        self.assertEqual(self.smoke.check(name, result, expect, {}, None, None, None, None, None)["status"], "MODEL_PASS")  # gdm only
        del result["report"]["pps_gpio"]
        self.assertIn("no pps_gpio report from the booted slot: None",
                      self.smoke.check(name, result, expect, {}, None, None, None, self.PPS, None)["mismatches"])

    def test_session_expectations(self):
        self.assertEqual(self.smoke.session_mismatches(self.session(), self.SESSION), [])
        observed = self.session()
        observed["lab_session_state"] = {"mode": "normal", "reason": None, "failures": 0}  # an explicit normal mode file
        self.assertEqual(self.smoke.session_mismatches(observed, self.SESSION), [])
        changes = (("up", False), ("stable", False), ("console", {"ActiveState": "failed", "Result": "exit-code"}),
                   ("lab_session_state", {"mode": "safe", "reason": "3 failures", "failures": 0}), ("user_failed_units", ["pipewire.service"]),
                   ("logind_sessions", {}), ("greetd_config_sha256", "d" * 64), ("greetd_conf_present", True),
                   ("model", {"environment": {"bound": False}}))
        for key, value in changes:
            observed = dict(self.session(), **{key: value})
            mismatches = self.smoke.session_mismatches(observed, self.SESSION)
            self.assertTrue(mismatches, key)
            self.assertTrue(mismatches[-1].startswith("journal: "), mismatches)  # the session's own output comes along
        observed = self.session()
        observed["units"]["greetd.service"]["NRestarts"] = "3"
        self.assertTrue(self.smoke.session_mismatches(observed, self.SESSION))
        self.assertEqual(self.smoke.session_mismatches(self.session(), None), ["image-manifest.json records no session (build_image.install_session)"])
        self.assertTrue(self.smoke.session_mismatches({"unavailable": "KeyError"}, self.SESSION)[0].startswith("no session report"))

    def test_session_scenario_rewrites_the_golden_lab_a_with_its_own_tokens(self):
        cfg = bootchain.validate_ab(config())
        fname, slot, version = self.smoke.SESSION_ENTRY
        with tempfile.TemporaryDirectory() as temp:
            entries = Path(temp)
            for name in ("labA.conf", "labB.conf", "labA-rescue.conf", "labB-rescue.conf"):
                (entries / name).write_text("golden\n")
            self.smoke.apply_entry_plan(entries, ("", {}, {fname: (cfg, slot, version, None, False, True)}))
            text = (entries / "labA.conf").read_text()
            self.assertIn('bootchain.py smoke-report --session"', text)
            self.assertIn("version 2\n", text)
            self.assertEqual((entries / "labB.conf").read_text(), "golden\n")
        name, expect = self.smoke.SESSION_SCENARIO
        self.assertEqual(expect["entries_after"], sorted(["labA.conf", "labB.conf", "labA-rescue.conf", "labB-rescue.conf"]))
        self.assertFalse(expect["selftest"])
        self.assertEqual([s[0] for s in self.smoke.SCENARIOS], ["trial-a-blessed", "trial-b-fails", "fallback-a"])  # A/B unchanged
        self.assertIn("virtio-gpu-pci", self.smoke.SESSION_DEVICES)
        self.assertIn("usb-tablet", self.smoke.SESSION_DEVICES)  # wlroots 0.17.1 libinput needs an input device
        self.assertEqual(bootchain.SESSION_TARGET, "graphical.target")

    def test_session_tokens_pass_only_inside_a_vm(self):
        cfg = bootchain.validate_ab(config())
        line = bootchain.cmdline(BASE, cfg["root_a_partuuid"]) + " " + " ".join(bootchain.smoke_tokens(session=True)) + " initrd=\\srrx\\A\\initrd.img"
        self.assertEqual(bootchain.cmdline_findings(cfg, "A", line, "qemu")[0], [])
        self.assertTrue(bootchain.cmdline_findings(cfg, "A", line, "none")[0])
        both = bootchain.cmdline(BASE, cfg["root_a_partuuid"]) + " " + " ".join(bootchain.smoke_tokens(True, True))
        self.assertTrue(bootchain.cmdline_findings(cfg, "A", both, "qemu")[0])  # only the three exact sets


if __name__ == "__main__":
    unittest.main()
