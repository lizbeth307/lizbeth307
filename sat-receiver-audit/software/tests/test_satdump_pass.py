"""SatDump pass glue (srrx.satdump_pass): windows, fixed argv and units, decode-then-delete.

No SatDump binary runs here: the unit runner is replaced, and the products are synthetic PNGs.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock
import zlib

from srrx import baseband as bb
from srrx import decoder_policy, passes, satdump_pass as sp

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

    def test_load_plan_checks_the_saved_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "0123456789abcdef.json"
            path.write_text(json.dumps(plan()))
            self.assertEqual(sp.load_plan(path)["kind"], "srrx_pass_plan")
            path.write_text(json.dumps(dict(plan(), kind="other")))
            with self.assertRaisesRegex(sp.PassRefused, "PLAN_INVALID"):
                sp.load_plan(path)


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
        decode = sp.unit_properties("decode", self.IDENT, work_dir="/data/products/satdump/.satdump-" + self.IDENT,
                                    input_path="/data/raw/baseband-lrpt/lrpt-" + self.IDENT + ".sigmf-data")
        for value in ("PrivateNetwork=yes", "IPAddressDeny=any", "RestrictAddressFamilies=AF_UNIX", "ProtectHome=yes",
                      "ProtectSystem=strict", "TemporaryFileSystem=/data:ro", "Environment=LC_ALL=C.UTF-8",
                      "WorkingDirectory=/var/lib/srrx-satdump/empty", "User=srrx-satdump", "SupplementaryGroups=srrx-bb",
                      "BindReadOnlyPaths=/data/raw/baseband-lrpt/lrpt-" + self.IDENT + ".sigmf-data",
                      "Environment=HOME=/run/srrx-satdump-" + self.IDENT, "RuntimeMaxSec=1800", "LimitCORE=0"):
            self.assertIn(value, decode)
        self.assertFalse(any(p.startswith("IPAddressAllow=") for p in decode))
        live = sp.unit_properties("live", self.IDENT, work_dir="/data/products/satdump/.satdump-" + self.IDENT,
                                  runtime_max_s=1000)
        for value in ("IPAddressDeny=any", "IPAddressAllow=localhost", "RestrictAddressFamilies=AF_INET AF_UNIX",
                      "RuntimeMaxSec=1000"):
            self.assertIn(value, live)
        self.assertNotIn("PrivateNetwork=yes", live)
        self.assertFalse(any(p.startswith(("BindReadOnlyPaths=", "SupplementaryGroups=")) for p in live))
        for kwargs in ({"work_dir": "relative"}, {"work_dir": "/home/user/x"}, {"work_dir": "/data/a b"},
                       {"work_dir": "/data/../etc"}, {"work_dir": "/data/x", "input_path": "/etc/shadow"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(sp.PassRefused):
                sp.unit_properties("decode", self.IDENT, **kwargs)
        with self.assertRaises(sp.PassRefused):
            sp.unit_properties("live", self.IDENT, work_dir="/data/x", input_path="/data/raw/baseband-lrpt/x")
        with self.assertRaises(sp.PassRefused):
            sp.unit_properties("record", self.IDENT, work_dir="/data/x")

    def test_systemd_run_command_line(self):
        argv = sp.systemd_run_argv("decode", self.IDENT, ["A=1", "B=2"], ["/usr/bin/satdump", "x"])
        self.assertEqual(argv, ["/usr/bin/systemd-run", "--quiet", "--wait", "--pipe", "--collect", "--service-type=exec",
                                "--unit=srrx-satdump-decode-" + self.IDENT, "-p", "A=1", "-p", "B=2", "--",
                                "/usr/bin/satdump", "x"])

    def test_staged_texts(self):
        files = sp.staged_files()
        self.assertEqual(set(files), {"etc/systemd/system/srrx-baseband-sweep.service",
                                      "etc/systemd/system/srrx-baseband-sweep.timer", "etc/tmpfiles.d/srrx-satdump.conf"})
        tmp = files["etc/tmpfiles.d/srrx-satdump.conf"]
        self.assertIn("d /data/raw/baseband-lrpt 2750 labd srrx-bb 24h", tmp)
        self.assertIn("d /var/lib/srrx-satdump/empty 0555 root root -", tmp)
        self.assertIn("OnUnitActiveSec=15min", files["etc/systemd/system/srrx-baseband-sweep.timer"])
        self.assertIn("PrivateNetwork=yes", files["etc/systemd/system/srrx-baseband-sweep.service"])


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
    RID = "lrpt-0123456789abcdef"

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="srrx-satdump-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.products = self.root / "products"
        self.products.mkdir()
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
        self.calls = []

    def runner(self, probe_output=b"level input_file output_folder --samplerate --baseband_format", code=0,
               output=b"done", products=True):
        def run(argv, timeout):
            self.calls.append(argv)
            if argv[argv.index("--") + 2] == "pipeline" and argv[-1] == "--help":
                return 0, probe_output
            out = Path(argv[argv.index("--") + 6])
            if products:
                (out / "MSU-MR").mkdir(parents=True)
                (out / "MSU-MR" / "msu_mr_rgb_221.png").write_bytes(png())
                (out / "meteor_m2-x_lrpt.cadu").write_bytes(b"\x1a\xcf\xfc\x1d" * 4)
                os.symlink("/etc/passwd", out / "MSU-MR" / "link.png")
            return code, output
        return run

    def test_decode_publishes_sanitized_images_only_and_deletes_the_baseband(self):
        report = sp.run_decode(self.store, self.RID, self.install, self.products, runner=self.runner())
        target = self.products / self.RID
        self.assertEqual(sorted(p.name for p in target.iterdir()), ["image-00.png", "report.json"])
        self.assertNotIn(b"PRIVATE", (target / "image-00.png").read_bytes())
        self.assertEqual(report["pipeline"], "meteor_m2-x_lrpt")
        self.assertTrue(report["input_iq_deleted_after_decode"])
        self.assertEqual(self.store.deleted, [self.RID])
        self.assertEqual(sorted(p.name for p in self.products.iterdir()), [self.RID])  # work tree removed
        decode = self.calls[-1]
        self.assertIn("PrivateNetwork=yes", decode)
        self.assertEqual(decode[decode.index("--") + 1:][-2:], ["--samplerate=256000", "--baseband_format=cs16"])

    def test_every_failure_still_deletes_the_baseband(self):
        cases = (("LIVE_VENDOR_INTERFACE_UNVERIFIED", self.runner(probe_output=b"usage")),
                 ("DECODER_NONZERO_EXIT", self.runner(code=1)),
                 ("SATDUMP_CALCEPH_ERROR", self.runner(output=b"...\nCALCEPH ERROR")),
                 ("SATDUMP_NO_IMAGE_PRODUCT", self.runner(products=False)))
        for code, runner in cases:
            with self.subTest(code=code):
                self.store.deleted.clear()
                with self.assertRaisesRegex(decoder_policy.DecoderRefused, code):
                    sp.run_decode(self.store, self.RID, self.install, self.products, runner=runner)
                self.assertEqual(self.store.deleted, [self.RID])
                self.assertEqual(list(self.products.iterdir()), [])

    def test_changed_source_and_refused_metadata_delete_too(self):
        with mock.patch.object(self.store, "identity", return_value=(9, 9, 9)):
            with self.assertRaisesRegex(decoder_policy.DecoderRefused, "SOURCE_CHANGED_DURING_DECODE"):
                sp.run_decode(self.store, self.RID, self.install, self.products, runner=self.runner())
        self.assertEqual(self.store.deleted, [self.RID])
        self.store.deleted.clear()
        self.store.meta = dict(self.meta, captures=[])
        with self.assertRaisesRegex(decoder_policy.DecoderRefused, "SOURCE_NOT_APPROVED_LRPT_BASEBAND"):
            sp.run_decode(self.store, self.RID, self.install, self.products, runner=self.runner())
        self.assertEqual(self.store.deleted, [self.RID])


if __name__ == "__main__":
    unittest.main()
