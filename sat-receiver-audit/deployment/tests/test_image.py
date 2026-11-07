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


if __name__ == "__main__":
    unittest.main()
