"""SatDump pass glue (srrx.satdump_pass): windows, fixed argv and units, decode-then-delete.

No SatDump binary runs here: the unit runner is replaced, and the products are synthetic PNGs.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zlib

from srrx import baseband as bb
from srrx import decoder_policy, pass_jobs, passes, satdump_pass as sp

SOFTWARE = Path(__file__).resolve().parents[1]

START = 1_800_000_000.0
METEOR3, METEOR4, NOAA, LRPT_OTHER = 40001, 40002, 40003, 40004
ACCEPTED = {METEOR3: {"norad_id": METEOR3, "name": "Meteor-M N2-3", "role": "LRPT"},
            METEOR4: {"norad_id": METEOR4, "name": "Meteor-M N2-4", "role": "LRPT"},
            NOAA: {"norad_id": NOAA, "name": "NOAA 19", "role": "OTHER"},
            LRPT_OTHER: {"norad_id": LRPT_OTHER, "name": "Other LRPT", "role": "LRPT"}}


def text(moment):
    return datetime.fromtimestamp(moment, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def plan(verified=True, entries=None):
    entries = entries if entries is not None else [(METEOR3, "Meteor-M N2-3", 3600), (NOAA, "NOAA 19", 7200),
                                                   (LRPT_OTHER, "Other LRPT", 9000), (METEOR4, "Meteor-M N2-4", 12000)]
    items = []
    for norad, name, offset in entries:
        aos = START + offset
        items.append({"norad_id": norad, "name": name, "aos_utc": text(aos), "tca_utc": text(aos + 300),
                      "los_utc": text(aos + 720), "max_el_deg": 40.0, "aos_az_deg": 10.0, "tca_az_deg": 80.0,
                      "los_az_deg": 170.0, "duration_s": 720.0, "omm_epoch_utc": "2027-01-15T00:00:00.000000Z",
                      "omm_age_days": 0.2, "omm_age_warning": False, "time_verified": verified,
                      "observer_source": "last_good", "observer_age_ms": None, "v_dipole_hint": None,
                      "predictor": {"skyfield": "1.55", "sgp4": "2.27"}})
    return {"schema_version": 1, "kind": "srrx_pass_plan", "start_utc": text(START), "hours": 24.0, "min_el_deg": 0.0,
            "time_verified": verified,
            "observer": {"lat_rounded": 50.0, "lon_rounded": 10.0, "alt_rounded_m": 200.0, "rounding_deg": 0.1,
                         "source": "last_good", "age_ms": None, "qualified_fix": False,
                         "qualification_failures": ["NOT_A_GNSS_FIX"]},
            "predictor": {"skyfield": "1.55", "sgp4": "2.27"}, "passes": items, "skipped": [],
            "window_edge_partial_passes": 0, "truncated": False, "scope": passes.SCOPE}


class WindowTests(unittest.TestCase):
    def test_only_meteor_lrpt_targets_get_windows(self):
        result = sp.select_windows(plan(), ACCEPTED, 137_900_000, 72_000)
        self.assertEqual([w["norad_id"] for w in result["windows"]], [METEOR3, METEOR4])
        self.assertEqual(result["non_meteor_lrpt_targets"], 1)
        first = result["windows"][0]
        self.assertEqual(first["start_unix_s"], START + 3600 - 60)
        self.assertEqual(first["end_unix_s"], START + 3600 + 720 + 60)
        self.assertEqual(first["pipeline"], "meteor_m2-x_lrpt")
        self.assertEqual(bb.validate_window(first), first)

    def test_fail_closed_without_verified_utc_or_meteor_target(self):
        self.assertEqual(sp.select_windows(plan(verified=False), ACCEPTED, 137_900_000, 72_000)["reason"], "UTC_NOT_VERIFIED")
        others = {k: v for k, v in ACCEPTED.items() if v["name"] not in bb.METEOR_TARGETS}
        self.assertEqual(sp.select_windows(plan(), others, 137_900_000, 72_000)["reason"], "NO_METEOR_LRPT_TARGET")
        renamed = plan(entries=[(METEOR3, "Meteor-M N2-3 (old name)", 3600)])
        self.assertEqual(sp.select_windows(renamed, ACCEPTED, 137_900_000, 72_000)["windows"], [])
        for center, rate in ((137_500_000, 72_000), (137_900_000, 64_000)):
            with self.subTest(center=center, rate=rate), self.assertRaises(bb.BasebandRefused):
                sp.select_windows(plan(), ACCEPTED, center, rate)
        with self.assertRaises(sp.PassRefused):
            sp.select_windows(plan(), {METEOR3: {"norad_id": 1, "name": "Meteor-M N2-3", "role": "LRPT"}}, 137_900_000, 72_000)

    def test_window_at_picks_the_current_window_only(self):
        windows = sp.select_windows(plan(), ACCEPTED, 137_100_000, 80_000)["windows"]
        self.assertIsNone(sp.window_at(windows, START))
        self.assertEqual(sp.window_at(windows, START + 3600 - 62)["norad_id"], METEOR3)
        self.assertIsNone(sp.window_at(windows, START + 3600 - 70))
        self.assertEqual(sp.window_at(windows, START + 12000 + 700)["norad_id"], METEOR4)

    @unittest.skipUnless(os.name == "posix", "plan owner and mode checks need POSIX")
    def test_load_plan_reads_only_plans_of_the_plan_unit(self):
        self.assertEqual((sp.PLAN_ROOT, sp.PLAN_WRITER), (str(pass_jobs.PLAN_ROOT), pass_jobs.UNIT_USER))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "plans"
            root.mkdir(mode=0o750)
            os.chmod(root, 0o2750)
            path = root / "0123456789abcdef.json"
            path.write_text(json.dumps(plan()))
            os.chmod(path, 0o640)
            writer = os.geteuid()  # the test user stands in for srrx-passes
            with mock.patch.object(sp, "PLAN_ROOT", str(root)), \
                    mock.patch.object(sp, "_plan_writer_uid", lambda: writer):
                self.assertEqual(sp.load_plan(path)["kind"], "srrx_pass_plan")
                path.write_text(json.dumps(dict(plan(), kind="other")))
                with self.assertRaisesRegex(sp.PassRefused, "PLAN_INVALID"):
                    sp.load_plan(path)
                path.write_text(json.dumps(plan()))
                # Any JSON elsewhere, under another name, writable by others or of another owner: refused.
                other = Path(directory) / "0123456789abcdef.json"
                other.write_text(json.dumps(plan()))
                for candidate in (other, root / "plan.json", root / ".." / "plans" / path.name):
                    with self.subTest(candidate=str(candidate)), self.assertRaisesRegex(sp.PassRefused, "PLAN_NOT_FROM_PLAN_UNIT"):
                        sp.load_plan(candidate)
                os.chmod(path, 0o660)
                with self.assertRaisesRegex(sp.PassRefused, "PLAN_NOT_FROM_PLAN_UNIT"):
                    sp.load_plan(path)
                os.chmod(path, 0o640)
                os.chmod(root, 0o2770)
                with self.assertRaisesRegex(sp.PassRefused, "PLAN_NOT_FROM_PLAN_UNIT"):
                    sp.load_plan(path)
                os.chmod(root, 0o2750)
            with mock.patch.object(sp, "PLAN_ROOT", str(root)), \
                    mock.patch.object(sp, "_plan_writer_uid", lambda: writer + 1):
                with self.assertRaisesRegex(sp.PassRefused, "PLAN_NOT_FROM_PLAN_UNIT"):
                    sp.load_plan(path)
        with self.assertRaisesRegex(sp.PassRefused, "PLAN_NOT_FROM_PLAN_UNIT"):
            sp.load_plan("/tmp/0123456789abcdef.json")


class CommandTests(unittest.TestCase):
    IDENT = "0123456789abcdef"

    def window(self):
        return sp.select_windows(plan(), ACCEPTED, 137_900_000, 72_000)["windows"][0]

    def test_decode_and_live_argv_are_fixed(self):
        self.assertEqual(sp.decode_argv("/usr/bin/satdump", "meteor_m2-x_lrpt_80k", "/in", "/out"),
                         ["/usr/bin/satdump", "pipeline", "meteor_m2-x_lrpt_80k", "baseband", "/in", "/out",
                          "--samplerate=256000", "--baseband_format=cs16"])
        live = sp.live_argv("/usr/bin/satdump", self.window(), "/data/products/satdump/.satdump-x", 8877)
        self.assertEqual(live, ["/usr/bin/satdump", "legacy", "live", "meteor_m2-x_lrpt", "/data/products/satdump/.satdump-x",
                                "--source", "net_source", "--mode", "udp", "--port", "8877", "--samplerate", "256000",
                                "--frequency", "137900000", "--timeout", str(720 + 120 + 60)])
        for pipeline in ("meteor_hrpt", "metop_ahrpt", "syracuse3_tlm"):
            with self.subTest(pipeline=pipeline), self.assertRaises(sp.PassRefused):
                sp.decode_argv("/usr/bin/satdump", pipeline, "/in", "/out")
        with self.assertRaises(sp.PassRefused):
            sp.live_argv("/usr/bin/satdump", self.window(), "/out", 80)

    def test_units_are_sandboxed_and_live_is_localhost_only(self):
        rid = "lrpt-" + self.IDENT
        decode = sp.unit_lines("decode", rid)
        for value in ("PrivateNetwork=yes", "IPAddressDeny=any", "RestrictAddressFamilies=AF_UNIX", "ProtectHome=yes",
                      "ProtectSystem=strict", "TemporaryFileSystem=/data:ro", "Environment=LC_ALL=C.UTF-8",
                      "WorkingDirectory=/var/lib/srrx-satdump/empty", "User=srrx-satdump", "SupplementaryGroups=srrx-bb",
                      "BindReadOnlyPaths=/data/raw/baseband-lrpt/" + rid + ".sigmf-data",
                      "BindPaths=/data/products/satdump/.satdump-" + rid, "Environment=HOME=/run/srrx-satdump-" + rid,
                      "LoadCredential=job:/run/srrx/satdump/" + rid + "/job.json",
                      "TimeoutStartSec=%d" % sp.DECODE_UNIT_TIMEOUT_S, "LimitCORE=0"):
            self.assertIn(value, decode)
        self.assertFalse(any(p.startswith(("IPAddressAllow=", "RuntimeMaxSec=")) for p in decode))
        live = sp.unit_lines("live", rid)
        for value in ("IPAddressDeny=any", "IPAddressAllow=localhost", "RestrictAddressFamilies=AF_INET AF_UNIX"):
            self.assertIn(value, live)
        self.assertNotIn("PrivateNetwork=yes", live)
        self.assertFalse(any(p.startswith(("BindReadOnlyPaths=", "SupplementaryGroups=", "LoadCredential=")) for p in live))
        for instance in ("0123456789abcdef", "lrpt-0123456789ABCDEF", "lrpt-0123", "lrpt-0123456789abcdef/../x", None, 7):
            with self.subTest(instance=instance), self.assertRaises(sp.PassRefused):
                sp.unit_lines("decode", instance)
        with self.assertRaises(sp.PassRefused):
            sp.unit_lines("record", rid)
        with self.assertRaises(sp.PassRefused):
            sp.unit_name(sp.DECODE_TEMPLATE, "%i")

    def test_template_files_are_the_generated_text(self):
        # The sandbox, user and ExecStart live in root-owned files; nothing is passed at run time but %i.
        for kind, template in (("decode", sp.DECODE_TEMPLATE), ("record", sp.RECORD_TEMPLATE)):
            text = (SOFTWARE / "systemd" / template).read_text(encoding="utf-8")
            self.assertEqual(text, sp.unit_text(kind), template)
            self.assertNotIn("[Install]", text)
            self.assertIn("\nType=oneshot\n", text)
            self.assertIn("\nCollectMode=inactive-or-failed\n", text)
            exec_start = [l for l in text.splitlines() if l.startswith("ExecStart=")]
            self.assertEqual(len(exec_start), 1)
            argv = shlex.split(exec_start[0].split("=", 1)[1])
            self.assertEqual(argv[-3:], ["srrx.satdump_unit", kind, "%i"])
            self.assertEqual(argv[argv.index("-m") - 3:argv.index("-m")], ["-P", "-s", "-B"])  # PYTHONPATH honoured
            self.assertFalse({"-I", "-E"} & set(argv))
            self.assertIn("Environment=PYTHONPATH=/opt/srrx/software PYTHONDONTWRITEBYTECODE=1", text)
        record = (SOFTWARE / "systemd" / sp.RECORD_TEMPLATE).read_text(encoding="utf-8").splitlines()
        for value in ("User=labd", "Group=srrx-bb", "SupplementaryGroups=lab", "DevicePolicy=closed",
                      "DeviceAllow=/dev/lab/rtla rw", "ReadWritePaths=/data /run/srrx/satdump/%i", "PrivateNetwork=yes",
                      "RestrictAddressFamilies=AF_UNIX AF_NETLINK", "ProtectSystem=strict", "NoNewPrivileges=yes",
                      "EnvironmentFile=/etc/srrx/baseband.env", "ConditionPathExists=/etc/srrx/baseband.env",
                      "KillMode=mixed", "TimeoutStartSec=%d" % sp.RECORD_UNIT_TIMEOUT_S):
            self.assertIn(value, record)
        self.assertFalse([l for l in record if l.startswith("PrivateDevices=")])  # it opens RTL-A (DeviceAllow=)
        self.assertGreater(sp.RECORD_UNIT_TIMEOUT_S, bb.MAX_FILE_S + bb.EARLY_START_S + 10)
        self.assertEqual(sp.unit_name(sp.RECORD_TEMPLATE, "lrpt-" + self.IDENT),
                         "srrx-baseband-record@lrpt-" + self.IDENT + ".service")

    def test_no_transient_unit_and_no_systemd_run_anywhere(self):
        self.assertEqual(sp.transient_units(), [])
        for name in ("satdump_pass.py", "satdump_unit.py", "baseband_scheduler.py"):
            text = (SOFTWARE / "srrx" / name).read_text(encoding="utf-8")
            self.assertNotIn("systemd-run", text, name)
            self.assertNotIn("systemd_run", text, name)
            self.assertNotIn("StartTransientUnit(", text, name)

    @unittest.skipUnless(os.name == "posix", "umask and setgid directories need POSIX")
    def test_work_dir_is_2770_under_any_umask(self):
        with tempfile.TemporaryDirectory(prefix="srrx-work-") as directory:
            for index, mask in enumerate((0o022, 0o077, 0o000)):
                previous = os.umask(mask)
                try:
                    work = sp.make_work_dir(Path(directory) / ("w%d" % index))
                finally:
                    os.umask(previous)
                with self.subTest(umask=oct(mask)):
                    self.assertEqual(stat.S_IMODE(os.lstat(work).st_mode), 0o2770)
            # The setgid bit cannot be kept (a parent group the caller is not in): refused, and nothing is left.
            chmod = os.chmod
            with mock.patch.object(sp.os, "chmod", lambda path, mode: chmod(path, mode & ~stat.S_ISGID)):
                with self.assertRaisesRegex(sp.PassRefused, "WORK_DIR_MODE"):
                    sp.make_work_dir(Path(directory) / "lost-setgid")
            self.assertFalse((Path(directory) / "lost-setgid").exists())
            with self.assertRaises(FileExistsError):
                sp.make_work_dir(Path(directory) / "w0")

    def test_staged_texts(self):
        files = sp.staged_files()
        self.assertEqual(set(files), {"etc/systemd/system/srrx-baseband-sweep.service",
                                      "etc/systemd/system/srrx-baseband-sweep.timer", "etc/tmpfiles.d/srrx-satdump.conf",
                                      "etc/srrx/baseband.env.template"})
        tmp = files["etc/tmpfiles.d/srrx-satdump.conf"]
        self.assertIn("d /data/raw/baseband-lrpt 2750 labd srrx-bb 24h", tmp)
        self.assertIn("d /var/lib/srrx-satdump/empty 0555 root root -", tmp)
        self.assertIn("OnUnitActiveSec=15min", files["etc/systemd/system/srrx-baseband-sweep.timer"])
        self.assertIn("PrivateNetwork=yes", files["etc/systemd/system/srrx-baseband-sweep.service"])
        self.assertIn("group srrx-satdump", tmp)  # the caller reads the unit's PNGs and removes its tree
        # Before commissioning writes the storage binding the sweep is skipped, not failed; the template binds nothing.
        self.assertIn("\nConditionPathExists=" + sp.BASEBAND_ENV + "\n", files["etc/systemd/system/srrx-baseband-sweep.service"])
        self.assertIn("\nEnvironmentFile=" + sp.BASEBAND_ENV + "\n", files["etc/systemd/system/srrx-baseband-sweep.service"])
        self.assertEqual([l for l in files["etc/srrx/baseband.env.template"].splitlines() if not l.startswith("#")],
                         ["SRRX_BB_DEVICE=", "SRRX_BB_DRIVER_RECORD="])

    def sweep_service(self):
        text = sp.sweep_units()["etc/systemd/system/srrx-baseband-sweep.service"]
        keys = {}
        for line in text.splitlines():
            if "=" in line and not line.startswith(("#", "[")):
                key, value = line.split("=", 1)
                keys.setdefault(key, []).append(value)
        return keys

    def test_sweep_unit_lets_the_storage_guard_work(self):
        # Finding S2: the guard needs PYTHONPATH honoured, /dev visible, the whole bound mount writable
        # and no nested bind mount below it.
        keys = self.sweep_service()
        self.assertEqual(keys["ReadWritePaths"], [sp.DATA_ROOT])  # the mount itself, never a class-dir bind
        self.assertEqual(keys["ProtectSystem"], ["strict"])
        self.assertNotIn("PrivateDevices", keys)  # a private /dev hides /dev/disk/by-uuid and the mount source
        self.assertEqual(keys["DevicePolicy"], ["closed"])
        self.assertEqual((keys["User"], keys["Group"]), (["labd"], [sp.BASEBAND_GROUP]))
        argv = shlex.split(keys["ExecStart"][0])
        module = argv.index("-m")
        self.assertEqual(argv[module + 1:module + 3], ["srrx.baseband", "sweep"])
        self.assertEqual(argv[argv.index("--storage-root") + 1], sp.DATA_ROOT)
        self.assertEqual(argv[argv.index("--storage-device") + 1], "${SRRX_BB_DEVICE}")
        flags = argv[1:module]
        self.assertFalse({"-I", "-E"} & set(flags), flags)  # both drop PYTHONPATH
        environment = dict(item.split("=", 1) for item in keys["Environment"][0].split())
        self.assertEqual(environment["PYTHONPATH"], "/opt/srrx/software")

    def test_sweep_unit_interpreter_flags_import_the_module(self):
        # The unit's own flags and Environment=, run here with this tree as /opt/srrx/software.
        keys = self.sweep_service()
        argv = shlex.split(keys["ExecStart"][0])
        flags = argv[1:argv.index("-m")]
        environment = dict(item.split("=", 1) for item in keys["Environment"][0].split())
        environment.update(PYTHONPATH=str(SOFTWARE), PATH=os.environ.get("PATH", ""))
        if os.name != "posix":
            environment["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
        run = lambda options: subprocess.run([sys.executable, *options, "-m", "srrx.baseband", "--help"],
                                             cwd=os.path.abspath(os.sep), env=environment, capture_output=True,
                                             timeout=60)
        result = run(flags)
        self.assertEqual(result.returncode, 0, result.stderr[-400:])
        self.assertIn(b"sweep", result.stdout)
        refused = run(["-I", "-B"])  # the old unit: -I implies -E and ignores PYTHONPATH
        probe = subprocess.run([sys.executable, "-I", "-B", "-c", "import importlib.util; spec = importlib.util.find_spec('srrx'); "
                                "print(spec.origin if spec and spec.origin else '')"],
                               cwd=os.path.abspath(os.sep), env=environment, capture_output=True, text=True, timeout=60)
        self.assertEqual(probe.returncode, 0, probe.stderr[-400:])
        installed = probe.stdout.strip()
        if installed:  # an interpreter with its own installed srrx (the ARM64 lab venv) imports that copy under -I
            self.assertFalse(Path(installed).resolve().is_relative_to(SOFTWARE.resolve()), installed)
        else:  # the device's python3: without PYTHONPATH there is no srrx at all
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn(b"No module named", refused.stderr)


@unittest.skipUnless(os.name == "posix", "subprocess pipes and selectors need POSIX")
class RunnerTests(unittest.TestCase):
    def test_fail_marker_is_found_even_when_scrolled_out(self):
        script = "import sys; print('CALCEPH ERROR: file'); sys.stdout.write('x' * 200000); print()"
        code, output = sp.run_bounded([sys.executable, "-c", script], 30)
        self.assertEqual(code, 0)
        self.assertLessEqual(len(output), sp.OUTPUT_LIMIT + 64)
        self.assertTrue(sp.output_failed(output))
        code, output = sp.run_bounded([sys.executable, "-c", "print('fine')"], 30)
        self.assertFalse(sp.output_failed(output))

    def test_timeout_kills_the_process_group(self):
        with self.assertRaisesRegex(sp.PassRefused, "SATDUMP_TIMEOUT"):
            sp.run_bounded([sys.executable, "-c", "import time; time.sleep(30)"], 0.5)


def png():
    def chunk(kind, content):
        return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind + content) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
            + chunk(b"tEXt", b"Comment\x00PRIVATE") + chunk(b"IDAT", zlib.compress(b"\x00\x80")) + chunk(b"IEND", b""))


class FakeStore:
    def __init__(self, root, meta):
        self.root, self.meta, self.deleted = Path(root), meta, []

    def load(self, recording_id):
        return self.meta, (1, 2, 16)

    def data_path(self, recording_id):
        return str(self.root) + "/" + bb.CLASS_DIR + "/" + recording_id + ".sigmf-data"

    def identity(self, recording_id):
        return (1, 2, 16)

    def delete(self, recording_id):
        self.deleted.append(recording_id)
        return True


@unittest.skipUnless(os.name == "posix", "setgid work directory and scandir semantics of Linux")
class DecodeTests(unittest.TestCase):
    """run_decode with the decode unit played by srrx.satdump_unit.decode itself (PID 1 and SatDump faked)."""
    RID = "lrpt-0123456789abcdef"

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="srrx-satdump-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.products = self.root / sp.PRODUCTS_DIR
        self.products.mkdir(parents=True)
        self.jobs = self.root / "run-satdump"
        patcher = mock.patch.object(sp, "DATA_ROOT", str(self.root))  # the units' /data is this directory here
        patcher.start()
        self.addCleanup(patcher.stop)
        window = sp.select_windows(plan(), ACCEPTED, 137_900_000, 72_000)["windows"][0]
        self.meta = bb.metadata(self.RID, window, created_s=START + 3550, first_block_s=START + 3550, samples=4,
                                sha512="b" * 128, clipped=0, gaps=0, joins=0, source="SIMULATION", group_delay=685,
                                stop_reason="WINDOW_END")
        self.store = FakeStore(self.root, self.meta)
        self.install = {"sha256": "c" * 64}
        for name, value in (("_validate_satdump_installation", Path("/usr/bin/satdump")),):
            patcher = mock.patch.object(decoder_policy, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.calls, self.units = [], []

    def unit(self, probe_output=b"level input_file output_folder --samplerate --baseband_format", code=0,
             output=b"done", products=True, result=True, installed=None, home=None):
        from srrx import satdump_unit

        def start(name, timeout):
            self.units.append(name)
            instance = name.split("@", 1)[1][:-len(".service")]
            credentials = self.root / "credentials" / instance  # PID 1 copies job.json (LoadCredential=job:...)
            credentials.mkdir(parents=True)
            shutil.copyfile(self.jobs / instance / sp.JOB_FILE, credentials / "job")
            environ = {"CREDENTIALS_DIRECTORY": str(credentials), "HOME": home or "/run/srrx-satdump-" + instance}

            def run(argv, timeout_s, env=None, cwd=None):
                self.calls.append((argv, env, cwd))
                if argv[-1] == "--help":
                    return 0, probe_output
                out = Path(argv[5])
                out.mkdir(parents=True)  # SatDump creates the output folder even when nothing decodes
                if products:
                    (out / "MSU-MR").mkdir()
                    (out / "MSU-MR" / "msu_mr_rgb_221.png").write_bytes(png())
                    (out / "meteor_m2-x_lrpt.cadu").write_bytes(b"\x1a\xcf\xfc\x1d" * 4)
                    os.symlink("/etc/passwd", out / "MSU-MR" / "link.png")
                return code, output
            try:
                value = satdump_unit.decode(instance, environ=environ, runner=run,
                                            load_installation=lambda path: installed or self.install,
                                            executable_check=lambda installation: Path("/usr/bin/satdump"))
            except Exception as error:
                value = sp.result_value("decode", instance, "REFUSED", satdump_unit._code(error))
            if result:
                sp._write_new(self.products / (".satdump-" + instance) / sp.UNIT_RESULT, value, 0o640)
            return 0 if value["status"] == "DECODED" else 1
        return start

    def decode(self, start, **kwargs):
        return sp.run_decode(self.store, self.RID, self.install, self.products, start_unit=start, job_root=self.jobs,
                             **kwargs)

    def test_decode_publishes_sanitized_images_only_and_deletes_the_baseband(self):
        report = self.decode(self.unit())
        target = self.products / self.RID
        self.assertEqual(sorted(p.name for p in target.iterdir()), ["image-00.png", "report.json"])
        self.assertNotIn(b"PRIVATE", (target / "image-00.png").read_bytes())
        self.assertEqual(report["pipeline"], "meteor_m2-x_lrpt")
        self.assertTrue(report["input_iq_deleted_after_decode"])
        self.assertEqual(self.store.deleted, [self.RID])
        self.assertEqual(sorted(p.name for p in self.products.iterdir()), [self.RID])  # work tree removed
        self.assertEqual(list(self.jobs.iterdir()), [])  # job directory removed
        self.assertEqual(self.units, ["srrx-satdump-decode@" + self.RID + ".service"])
        (probe, probe_env, probe_cwd), (decode, env, cwd) = self.calls
        self.assertEqual(probe[1:], ["pipeline", "meteor_m2-x_lrpt", "--help"])
        self.assertEqual(decode[1:5], ["pipeline", "meteor_m2-x_lrpt", "baseband",
                                       str(self.root) + "/raw/baseband-lrpt/" + self.RID + ".sigmf-data"])
        self.assertEqual(decode[-2:], ["--samplerate=256000", "--baseband_format=cs16"])
        self.assertEqual(env, {"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "HOME": "/run/srrx-satdump-" + self.RID})
        self.assertEqual((cwd, probe_env, probe_cwd), (sp.EMPTY_WORKDIR, env, sp.EMPTY_WORKDIR))

    def test_the_job_credential_names_only_what_the_plan_fixed(self):
        seen = {}

        def start(name, timeout):
            path = self.jobs / self.RID / sp.JOB_FILE
            seen["mode"] = stat.S_IMODE(os.lstat(path).st_mode)
            seen["dir_mode"] = stat.S_IMODE(os.lstat(path.parent).st_mode)
            seen["job"] = json.loads(path.read_text())
            return 1
        with self.assertRaisesRegex(decoder_policy.DecoderRefused, "DECODE_UNIT_NO_RESULT"):
            self.decode(start)
        self.assertEqual((seen["mode"], seen["dir_mode"]), (0o600, 0o700))
        self.assertEqual(seen["job"], {"v": 1, "kind": "srrx_satdump_decode_job", "recording_id": self.RID,
                                       "pipeline": "meteor_m2-x_lrpt", "executable_sha256": "c" * 64,
                                       "source_sha512": "b" * 128})
        self.assertEqual(sp.check_decode_job(seen["job"], self.RID), seen["job"])
        for change in ({"recording_id": "lrpt-" + "1" * 16}, {"pipeline": "meteor_hrpt"}, {"extra": 1},
                       {"executable_sha256": "C" * 64}):
            with self.subTest(change=change), self.assertRaisesRegex(sp.PassRefused, "JOB_INVALID"):
                sp.check_decode_job(dict(seen["job"], **change), self.RID)
        self.assertEqual(self.store.deleted, [self.RID])

    def test_every_failure_still_deletes_the_baseband(self):
        cases = (("LIVE_VENDOR_INTERFACE_UNVERIFIED", self.unit(probe_output=b"usage")),
                 ("DECODER_NONZERO_EXIT", self.unit(code=1)),
                 ("SATDUMP_CALCEPH_ERROR", self.unit(output=b"...\nCALCEPH ERROR")),
                 ("SATDUMP_NO_IMAGE_PRODUCT", self.unit(products=False)),
                 ("DECODE_UNIT_NO_RESULT", self.unit(result=False)),
                 ("INSTALLATION_CHANGED_SINCE_PLAN", self.unit(installed={"sha256": "d" * 64})),
                 ("UNIT_HOME_MISMATCH", self.unit(home="/var/lib/srrx-satdump")))
        for code, start in cases:
            with self.subTest(code=code):
                self.store.deleted.clear()
                shutil.rmtree(self.root / "credentials", ignore_errors=True)
                with self.assertRaisesRegex(decoder_policy.DecoderRefused, code):
                    self.decode(start)
                self.assertEqual(self.store.deleted, [self.RID])
                self.assertEqual(list(self.products.iterdir()), [])
                self.assertEqual(list(self.jobs.iterdir()), [])

    def test_changed_source_and_refused_metadata_delete_too(self):
        with mock.patch.object(self.store, "identity", return_value=(9, 9, 9)):
            with self.assertRaisesRegex(decoder_policy.DecoderRefused, "SOURCE_CHANGED_DURING_DECODE"):
                self.decode(self.unit())
        self.assertEqual(self.store.deleted, [self.RID])
        self.store.deleted.clear()
        self.store.meta = dict(self.meta, captures=[])
        with self.assertRaisesRegex(decoder_policy.DecoderRefused, "SOURCE_NOT_APPROVED_LRPT_BASEBAND"):
            self.decode(self.unit())
        self.assertEqual(self.store.deleted, [self.RID])
        self.assertEqual(self.units, ["srrx-satdump-decode@" + self.RID + ".service"])  # no unit for a refused plan

    def test_publish_budget_refuses_without_publishing(self):
        prepared = sp.prepare_decode(self.store, self.RID, self.install, self.products, job_root=self.jobs)
        self.unit()(prepared["unit"], 10)
        self.assertGreater(sp.png_bytes(prepared["work"] / "out"), 1)
        with self.assertRaisesRegex(decoder_policy.DecoderRefused, "SATDUMP_PRODUCTS_OVER_PUBLISH_BUDGET"):
            sp.finish_decode(self.store, prepared, publish_budget=1)
        self.assertEqual(self.store.deleted, [self.RID])
        self.assertEqual(list(self.products.iterdir()), [])


class ResultFileAndCleanupTests(unittest.TestCase):
    """A unit's result appears complete or not at all; finish_decode's cleanup steps run independently."""
    RID = "lrpt-0123456789abcdef"

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="srrx-result-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_result_file_is_renamed_into_place_complete_and_written_once(self):
        path = self.root / sp.RESULT_FILE
        value = sp.result_value("decode", self.RID, "DECODED")
        rename, seen = os.rename, []

        def spy(source, target):
            seen.append((Path(target).exists(), json.loads(Path(source).read_text())))
            return rename(source, target)
        with mock.patch.object(sp.os, "rename", spy):
            sp.write_result_file(path, value)
        self.assertEqual(seen, [(False, value)])  # a poll sees no file until the complete one is renamed in
        self.assertEqual(json.loads(path.read_text()), value)
        with self.assertRaises(FileExistsError):
            sp.write_result_file(path, sp.result_value("decode", self.RID, "REFUSED", "SATDUMP_CALCEPH_ERROR"))
        self.assertEqual(json.loads(path.read_text()), value)
        self.assertEqual([p.name for p in self.root.iterdir()], [sp.RESULT_FILE])  # no .tmp left behind

    def test_a_failed_result_write_leaves_neither_file(self):
        with mock.patch.object(sp.os, "fsync", side_effect=OSError(28, "No space left on device")), \
                self.assertRaises(OSError):
            sp.write_result_file(self.root / sp.UNIT_RESULT, sp.result_value("decode", self.RID, "DECODED"))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_the_unit_entry_point_writes_through_the_atomic_writer(self):
        import contextlib
        import io
        from srrx import satdump_unit
        value = sp.result_value("record", self.RID, "REFUSED", "JOB_INVALID")
        with mock.patch.object(sp, "write_result_file", wraps=sp.write_result_file) as writer, \
                contextlib.redirect_stdout(io.StringIO()) as out:
            satdump_unit.write_result(self.root / sp.RESULT_FILE, value)
        writer.assert_called_once()
        self.assertEqual(json.loads(out.getvalue()), value)
        self.assertEqual(json.loads((self.root / sp.RESULT_FILE).read_text()), value)

    def test_finish_decode_removes_the_job_and_deletes_the_baseband_when_the_tree_cannot_go(self):
        work, jobs = self.root / (".satdump-" + self.RID), self.root / "jobs"
        (work / "out").mkdir(parents=True)
        (jobs / self.RID).mkdir(parents=True)
        (jobs / self.RID / sp.JOB_FILE).write_text("{}")
        store = FakeStore(self.root, None)
        job = {"recording_id": self.RID, "work": work, "target": self.root / self.RID, "plan": {},
               "identity": (1, 2, 16), "job_root": str(jobs), "unit": sp.unit_name(sp.DECODE_TEMPLATE, self.RID)}
        with mock.patch.object(sp, "_remove_tree", side_effect=OSError(39, "Directory not empty")), \
                self.assertRaisesRegex(decoder_policy.DecoderRefused, "DECODE_UNIT_NO_RESULT"):
            sp.finish_decode(store, job)  # the decode's own refusal stays the outcome
        self.assertFalse((jobs / self.RID).exists())
        self.assertEqual(store.deleted, [self.RID])

    def test_decode_template_bounds_its_stop(self):
        self.assertIn("TimeoutStopSec=15", sp.unit_lines("decode"))
        self.assertIn("TimeoutStopSec=15\n", sp.unit_text("decode"))


if __name__ == "__main__":
    unittest.main()
