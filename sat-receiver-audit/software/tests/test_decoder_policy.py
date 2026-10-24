"""Policy/transport tests, not a claim that a vendor decoder is installed."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import time
import unittest
from unittest import mock
import wave
import zlib

from srrx import decoder_policy as d
from srrx import scope_policy


HELP = b"Decode NOAA APT images from WAV files. input_filename --output --map --rotate --quiet"


def chunk(kind, content):
    return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind + content) & 0xffffffff)


def png(text=True):
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
    if text:
        data += chunk(b"tEXt", b"Comment\x00PRIVATE_SENTINEL")
    return data + chunk(b"IDAT", zlib.compress(b"\x00\x80")) + chunk(b"IEND", b"")


class DecoderPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.wav = self.root / "recording.wav"
        with wave.open(str(self.wav), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(48000)
            stream.writeframes(b"\x00\x00" * 480)
        self.meta = {"v": 1, "sha256": hashlib.sha256(self.wav.read_bytes()).hexdigest(),
                     "purpose": "public_civil_weather", "satellite": "NOAA-19",
                     "origin": "approved_public_archive", "evidence_id": "archive/acceptance-001",
                     "voice_present": False, "private_payload": False, "military": False,
                     "emitter_geolocation": False, "iq_retained": False,
                     "format": "wav_pcm_s16le_mono"}
        self.install = {"v": 1, "tool_id": "noaa-apt", "version": "1.4.1",
                        "source_commit": d.NOAA_COMMIT, "executable": "/opt/noaa/noaa-apt",
                        "sha256": "a" * 64, "evidence_id": "admin/build-001"}

    def plan(self):
        with mock.patch.object(d, "_validate_installation", return_value=Path(self.install["executable"])):
            return d.make_plan(d.PRESET, self.wav, self.meta, self.install)

    def test_no_installation_is_unavailable_and_never_probes(self):
        with mock.patch.object(d, "_bounded_process", side_effect=AssertionError("must not launch")):
            self.assertTrue(d.availability()[d.PRESET].startswith("UNAVAILABLE"))

    def test_disabled_safety_presets_refuse_before_any_file_or_header_access(self):
        with mock.patch.object(d, "_file", side_effect=AssertionError("must not inspect payload")):
            for preset in ("egc-safetynet", "dsc-safety", "ais-public", "adsb-public"):
                with self.subTest(preset=preset), self.assertRaisesRegex(d.DecoderRefused, "DISABLED"):
                    d.make_plan(preset, None, None, None)
            # satdump-weather is installation-gated (v2.1) and never a noaa-apt file plan.
            with self.assertRaisesRegex(d.DecoderRefused, "SATDUMP_PRESET_IS_SATDUMP_PLAN"):
                d.make_plan("satdump-weather", None, None, None)

    def test_no_arbitrary_preset_or_argv(self):
        for preset in ("sh", "satdump --source hackrf", ["noaa-apt-weather"]):
            with self.subTest(preset=preset), self.assertRaisesRegex(d.DecoderRefused, "PRESET_NOT_ALLOWLISTED"):
                d.make_plan(preset, self.wav, self.meta, self.install)
        self.meta["argv"] = ["--wav-steps", "; touch /tmp/injected"]
        with self.assertRaisesRegex(d.DecoderRefused, "SOURCE_METADATA_SCHEMA"):
            self.plan()

    def test_every_private_voice_military_geolocation_or_iq_assertion_blocks(self):
        for name in ("voice_present", "private_payload", "military", "emitter_geolocation", "iq_retained"):
            for value in (True, None, 0, "false"):
                with self.subTest(name=name, value=value):
                    changed = dict(self.meta, **{name: value})
                    with self.assertRaisesRegex(d.DecoderRefused, "SOURCE_SCOPE_DENIED"):
                        d._validate_source(changed)

    def test_unknown_source_purpose_and_nonstring_fields_fail_closed(self):
        for key, value in (("purpose", "public_amateur_voice"), ("satellite", "military-weather"),
                           ("origin", "unverified"), ("format", "cf32"), ("satellite", [])):
            with self.subTest(key=key, value=value), self.assertRaises(d.DecoderRefused):
                d._validate_source(dict(self.meta, **{key: value}))

    def test_plan_contains_only_fixed_arguments_and_no_filename_or_evidence(self):
        plan = self.plan()
        self.assertEqual(plan["argv_template"], ["${ACCEPTED_NOAA_APT}", "${APPROVED_WAV}", "-o",
                                               "${OUTPUT_PNG}", "--map", "no", "--rotate", "no", "--quiet"])
        serialized = json.dumps(plan)
        self.assertNotIn(str(self.wav), serialized)
        self.assertNotIn(self.meta["evidence_id"], serialized)
        self.assertFalse(plan["shell"])
        self.assertFalse(plan["live_source"])

    def test_input_digest_change_stops_before_vendor_execution(self):
        self.wav.write_bytes(self.wav.read_bytes() + b"changed")
        with self.assertRaisesRegex(d.DecoderRefused, "SOURCE_DIGEST_CHANGED"):
            self.plan()

    def test_stereo_or_truncated_wav_rejected(self):
        with wave.open(str(self.wav), "wb") as stream:
            stream.setnchannels(2)
            stream.setsampwidth(2)
            stream.setframerate(48000)
            stream.writeframes(b"\x00" * 40)
        with self.assertRaisesRegex(d.DecoderRefused, "MONO_PCM16"):
            d._wav_info(self.wav)
        # A normal file with fewer sample bytes than its header promises.
        self.setUp_truncated()
        with self.assertRaisesRegex(d.DecoderRefused, "TRUNCATED_WAV"):
            d._wav_info(self.wav)

    def setUp_truncated(self):
        with wave.open(str(self.wav), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(48000)
            stream.writeframes(b"\x00" * 100)
        self.wav.write_bytes(self.wav.read_bytes()[:-20])

    def test_symlink_source_rejected(self):
        alias = self.root / "alias.wav"
        alias.symlink_to(self.wav)
        with mock.patch.object(d, "_validate_installation", return_value=Path(self.install["executable"])):
            with self.assertRaisesRegex(d.DecoderRefused, "NON_SYMLINK"):
                d.make_plan(d.PRESET, alias, self.meta, self.install)

    def test_installation_requires_pinned_source_exact_hash_and_native_tool(self):
        script = self.root / "noaa-apt"
        script.write_text("#!/bin/sh\nexit 0\n")
        script.chmod(0o555)
        record = dict(self.install, executable=str(script), sha256=hashlib.sha256(script.read_bytes()).hexdigest())
        with self.assertRaises(d.DecoderRefused):
            d._validate_installation(record)
        for key, value in (("version", "2.0"), ("source_commit", "0" * 40), ("argv", [])):
            with self.subTest(key=key), self.assertRaises(d.DecoderRefused):
                d._validate_installation(dict(record, **{key: value}))

    def test_executable_and_record_directories_must_be_admin_owned(self):
        path = Path("/opt/noaa-apt/noaa-apt")
        def lstat(modes):
            def value(name):
                uid, mode = modes.get(Path(name), (0, 0o40755))
                return mock.Mock(st_uid=uid, st_mode=mode)
            return value
        for modes, allowed in (({}, True), ({Path("/tmp"): (0, 0o41777)}, True),
                               ({path.parent: (1000, 0o40755)}, False),
                               ({Path("/opt"): (0, 0o40775)}, False), ({Path("/"): (0, 0o40757)}, False)):
            with self.subTest(modes=modes), mock.patch.object(d.os, "lstat", side_effect=lstat(modes)):
                if allowed:
                    d._admin_directories(path)
                    d._admin_directories(Path("/tmp/noaa-apt"))
                else:
                    with self.assertRaisesRegex(d.DecoderRefused, "ADMIN_OWNED_DIRECTORY_REQUIRED"):
                        d._admin_directories(path)
        record = dict(self.install, sha256="0" * 64)
        with mock.patch.object(d, "_file", return_value=path), \
                mock.patch.object(d, "_admin_directories", side_effect=d.DecoderRefused("ADMIN_OWNED_DIRECTORY_REQUIRED")), \
                mock.patch.object(d, "_hash_file", side_effect=AssertionError("must refuse before hashing")):
            with self.assertRaisesRegex(d.DecoderRefused, "ADMIN_OWNED_DIRECTORY_REQUIRED"):
                d._validate_installation(record)

    def test_png_strips_text_and_rejects_crc_or_truncation(self):
        candidate = self.root / "candidate.png"
        candidate.write_bytes(png())
        cleaned, dimensions = d._sanitized_png(candidate)
        self.assertEqual(dimensions, {"width": 1, "height": 1})
        self.assertNotIn(b"PRIVATE_SENTINEL", cleaned)
        self.assertEqual(cleaned, png(False))
        for data in (png()[:-2], png() + b"trailer", png()[:-5] + b"WRONG"):
            candidate.write_bytes(data)
            with self.assertRaises(d.DecoderRefused):
                d._sanitized_png(candidate)

    def test_bounded_child_discards_decoded_stdout_and_stderr(self):
        code, output = d._bounded_process([sys.executable, "-c",
                                          "import sys; print('PRIVATE_SENTINEL'); print('SECRET', file=sys.stderr)"],
                                         self.root, 3)
        self.assertEqual((code, output), (0, b""))

    def test_child_timeout_terminates_process_group(self):
        start = time.monotonic()
        with self.assertRaisesRegex(d.DecoderRefused, "DECODER_TIMEOUT"):
            d._bounded_process([sys.executable, "-c", "import time; time.sleep(10)"], self.root, .1)
        self.assertLess(time.monotonic() - start, 2)

    def test_interface_probe_has_strict_output_bound(self):
        with self.assertRaisesRegex(d.DecoderRefused, "INTERFACE_RESPONSE_LIMIT"):
            d._bounded_process([sys.executable, "-c", "print('x' * 100000)"], self.root, 3, capture_probe=True)

    def test_execution_publishes_only_sanitized_weather_image_and_report(self):
        calls = []
        def fake_vendor(argv, cwd, timeout_s, *, capture_probe=False):
            calls.append(argv)
            if capture_probe:
                self.assertEqual(argv[-1], "--help")
                return 0, HELP
            (cwd / "output.png").write_bytes(png())
            (cwd / "private-tool-log.txt").write_text("PRIVATE_SENTINEL")
            return 0, b""
        dest = self.root / "result"
        with mock.patch.object(d, "_validate_installation", return_value=Path(self.install["executable"])), \
                mock.patch.object(d, "_bounded_process", side_effect=fake_vendor):
            report = d.execute(d.PRESET, self.wav, self.meta, self.install, dest)
        self.assertEqual(set(p.name for p in dest.iterdir()), {"weather.png", "report.json"})
        self.assertNotIn(b"PRIVATE_SENTINEL", (dest / "weather.png").read_bytes())
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(report))
        self.assertFalse(report["physical_tests_performed"])
        self.assertFalse(report["stdout_stored"])
        self.assertEqual(calls[1][-5:], ["--map", "no", "--rotate", "no", "--quiet"])

    def test_unknown_live_interface_and_failed_vendor_leave_no_result(self):
        for probe_result in ((0, b"unrelated program"), (3, HELP)):
            dest = self.root / "failed"
            with mock.patch.object(d, "_validate_installation", return_value=Path(self.install["executable"])), \
                    mock.patch.object(d, "_bounded_process", return_value=probe_result):
                with self.assertRaisesRegex(d.DecoderRefused, "LIVE_VENDOR_INTERFACE_UNVERIFIED"):
                    d.execute(d.PRESET, self.wav, self.meta, self.install, dest)
            self.assertFalse(dest.exists())

    def test_invalid_timeouts_and_existing_destination_are_refused(self):
        for value in (True, 0, 301, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaisesRegex(d.DecoderRefused, "TIMEOUT_RANGE"):
                d.execute(d.PRESET, self.wav, self.meta, self.install, self.root / "nope", timeout_s=value)
        with mock.patch.object(d, "_validate_installation", return_value=Path(self.install["executable"])):
            with self.assertRaisesRegex(d.DecoderRefused, "NEW_ABSOLUTE_OUTPUT"):
                d.execute(d.PRESET, self.wav, self.meta, self.install, self.root)

    def latch(self, category):
        data = json.dumps({"v": 1, "kind": "srrx_artemis_mirror", "source": "artemis-db", "db_version": "v74",
                           "entries": [{"name": "Fixture", "categories": [category],
                                        "ranges_hz": [[137.5e6, 137.52e6]]}]}).encode()
        path = self.root / "artemis.json"
        path.write_bytes(data)
        return scope_policy.ScopeLatch(scope_policy.ArtemisDB.load(path, hashlib.sha256(data).hexdigest()))

    def test_egc_safetynet_stays_disabled_although_the_gate_module_exists(self):
        from srrx import egc_gate
        packet = bytes((0xB1, 4, 0x04, 0x00, 0x00, 0x04))
        self.assertTrue(egc_gate.classify(packet).accept)  # unit-level gate behaviour only
        expected = "DISABLED_NO_VERIFIED_HEADER_PARSER_AND_TEST_VECTORS"
        self.assertEqual(d.availability()["egc-safetynet"], expected)
        self.assertEqual(d.availability(self.install)["egc-safetynet"], expected)
        self.assertTrue(egc_gate.gate_status().startswith("DISABLED"))
        with mock.patch.object(d, "_file", side_effect=AssertionError("must not inspect payload")), \
                self.assertRaisesRegex(d.DecoderRefused, expected):
            d.make_plan("egc-safetynet", None, None, None, scope=scope_policy.ScopeLatch())

    def test_scope_stop_refuses_plan_before_installation_or_source_access(self):
        latch = self.latch("Military")
        with mock.patch.object(d, "_validate_installation", side_effect=AssertionError("must refuse first")), \
                mock.patch.object(d, "_file", side_effect=AssertionError("must refuse first")), \
                self.assertRaisesRegex(d.DecoderRefused, "OUT_OF_SCOPE"):
            d.make_plan(d.PRESET, self.wav, self.meta, self.install, scope=latch)
        self.assertTrue(latch.stopped)
        with mock.patch.object(d, "_validate_installation", return_value=Path(self.install["executable"])):
            self.assertEqual(d.make_plan(d.PRESET, self.wav, self.meta, self.install,
                                         scope=self.latch("Broadcast"))["preset"], d.PRESET)
        for scope in (object(), True, {"permits": True}):
            with self.subTest(scope=scope), self.assertRaisesRegex(d.DecoderRefused, "SCOPE_LATCH_REQUIRED"):
                d.make_plan(d.PRESET, self.wav, self.meta, self.install, scope=scope)
        stop = {"stop": True, "reason": "MASKED_BAND", "reasons": ["MASKED_BAND"], "identify": "WITHHELD",
                "display": "out of scope"}
        with mock.patch.object(d, "scope_check", return_value=stop), \
                self.assertRaisesRegex(d.DecoderRefused, "OUT_OF_SCOPE"):
            self.plan()  # the masked-band rule applies without any latch

    def test_scope_stop_during_run_discards_unpublished_output(self):
        latch = scope_policy.ScopeLatch()
        def fake_vendor(argv, cwd, timeout_s, *, capture_probe=False):
            if capture_probe:
                return 0, HELP
            (cwd / "output.png").write_bytes(png())
            latch.stop(*d.APT_SPAN_HZ)  # e.g. identification stop while decoding
            return 0, b""
        dest = self.root / "result"
        with mock.patch.object(d, "_validate_installation", return_value=Path(self.install["executable"])), \
                mock.patch.object(d, "_bounded_process", side_effect=fake_vendor), \
                self.assertRaisesRegex(d.DecoderRefused, "OUT_OF_SCOPE"):
            d.execute(d.PRESET, self.wav, self.meta, self.install, dest, scope=latch)
        self.assertFalse(dest.exists())
        self.assertEqual([p.name for p in self.root.iterdir()], ["recording.wav"])

    def test_cli_disabled_gate_does_not_even_read_metadata(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = d.main(["plan", "--preset", "egc-safetynet", "--source", "/missing/source",
                           "--metadata", "/missing/meta", "--installation", "/missing/tool"])
        self.assertEqual(code, 2)
        self.assertIn("DISABLED_NO_VERIFIED_HEADER_PARSER", stdout.getvalue())
        self.assertNotIn("/missing", stdout.getvalue())


class SatDumpProfileTests(unittest.TestCase):
    """satdump-weather (v2.1): installation record, LRPT-baseband-only plan, PNG-only publication."""

    def setUp(self):
        from srrx import baseband
        self.bb = baseband
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        self.exe, self.plugins, self.pipelines = root / "bin/satdump", root / "plugins", root / "pipelines"
        self.config = root / "satdump_cfg.json"
        for directory in (self.exe.parent, self.plugins, self.pipelines):
            directory.mkdir(parents=True)
        self.exe.write_bytes(b"\x7fELF fixture")
        sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        plugins = {}
        for name in d.SATDUMP_PLUGINS:
            path = self.plugins / ("lib%s_support.so" % name)
            path.write_bytes(b"\x7fELF " + name.encode())
            plugins[path.name] = sha(path)
        pipelines = {}
        for name in d.SATDUMP_PIPELINE_FILES:
            path = self.pipelines / name
            path.write_text(json.dumps({name: {}}))
            pipelines[name] = sha(path)
        self.config.write_text(json.dumps({"satdump_general": {"kepler_update_interval": {"value": "Never"}}}))
        self.install = {"v": 1, "tool_id": "satdump", "version": d.SATDUMP_VERSION, "source_commit": d.SATDUMP_COMMIT,
                        "executable": str(self.exe), "sha256": sha(self.exe), "evidence_id": "admin/satdump-build-001",
                        "plugins": plugins, "pipelines": pipelines, "config_sha256": sha(self.config),
                        "recipe_sha256": "d" * 64}
        original = d._file
        for target, value in (("SATDUMP_PLUGIN_DIR", str(self.plugins)), ("SATDUMP_PIPELINE_DIR", str(self.pipelines)),
                              ("SATDUMP_CONFIG", str(self.config))):
            patcher = mock.patch.object(d, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        # The fixture is not root-owned: only the owner checks are relaxed, never the digests or file sets.
        for target, value in (("_admin_directories", lambda path: None), ("_admin_owned", lambda info: True),
                              ("_file", lambda path, executable=False: original(path))):
            patcher = mock.patch.object(d, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        window = baseband.window(40001, "Meteor-M N2-3", 137_900_000, 72_000, 1.8e9, 1.8e9 + 600,
                                 baseband.iso_utc(1.8e9), baseband.iso_utc(1.8e9 + 600))
        self.meta = baseband.metadata("lrpt-0123456789abcdef", window, created_s=1.8e9 - 50, first_block_s=1.8e9 - 50,
                                      samples=10, sha512="e" * 128, clipped=0, gaps=0, joins=0, source="HARDWARE",
                                      group_delay=685, stop_reason="WINDOW_END")

    def test_availability_is_gated_by_the_installation(self):
        self.assertEqual(d.availability()[d.SATDUMP_PRESET], "UNAVAILABLE_NO_ACCEPTED_INSTALLATION")
        self.assertEqual(d.availability(satdump_installation=self.install)[d.SATDUMP_PRESET],
                         "LRPT_FILE_PRESET_ACCEPTED_INTERFACE_PROBE_REQUIRED_AT_RUN")
        self.assertEqual(d.availability(satdump_installation=dict(self.install, version="1.2.2"))[d.SATDUMP_PRESET],
                         "UNAVAILABLE_INSTALLATION_NOT_QUALIFIED")

    def test_exact_plugin_and_pipeline_sets_and_digests(self):
        self.assertEqual(d.satdump_executable(self.install), self.exe)
        extra = self.plugins / "libhackrf_sdr_support.so"
        extra.write_bytes(b"\x7fELF")
        with self.assertRaisesRegex(d.DecoderRefused, "SATDUMP_FILE_SET_NOT_ALLOWLISTED"):
            d.satdump_executable(self.install)
        extra.unlink()
        (self.pipelines / "Syracuse.json").write_text("{}")
        with self.assertRaisesRegex(d.DecoderRefused, "SATDUMP_FILE_SET_NOT_ALLOWLISTED"):
            d.satdump_executable(self.install)
        (self.pipelines / "Syracuse.json").unlink()
        (self.pipelines / "MetOp.json").write_text('{"metop_ahrpt": {"mqtt": 1}}')
        with self.assertRaisesRegex(d.DecoderRefused, "SATDUMP_FILE_DIGEST_CHANGED"):
            d.satdump_executable(self.install)
        missing = dict(self.install, plugins={k: v for k, v in self.install["plugins"].items() if "net_source" not in k})
        with self.assertRaisesRegex(d.DecoderRefused, "SATDUMP_FILE_SET_NOT_ALLOWLISTED"):
            d.satdump_executable(missing)

    def test_kepler_update_must_be_never(self):
        self.config.write_text(json.dumps({"satdump_general": {"kepler_update_interval": {"value": "1 day"}}}))
        changed = dict(self.install, config_sha256=hashlib.sha256(self.config.read_bytes()).hexdigest())
        with self.assertRaisesRegex(d.DecoderRefused, "SATDUMP_KEPLER_UPDATE_NOT_NEVER"):
            d.satdump_executable(changed)

    def test_plan_accepts_only_a_policy_baseband(self):
        plan = d.satdump_plan(self.meta, self.install)
        self.assertEqual(plan["argv_template"], ["${ACCEPTED_SATDUMP}", "pipeline", "meteor_m2-x_lrpt", "baseband",
                                                 "${APPROVED_BASEBAND}", "${OUTPUT_DIR}", "--samplerate=256000",
                                                 "--baseband_format=cs16"])
        self.assertFalse(plan["shell"] or plan["live_source"] or plan["stdout_stored"])
        for change in ({"srrx:export": True}, {"srrx:target": "NOAA 19"}, {"core:datatype": "cu8"}):
            changed = json.loads(json.dumps(self.meta))
            changed["global"].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(d.DecoderRefused, "SOURCE_NOT_APPROVED_LRPT_BASEBAND"):
                d.satdump_plan(changed, self.install)
        with self.assertRaisesRegex(d.DecoderRefused, "SOURCE_NOT_APPROVED_LRPT_BASEBAND"):
            d.satdump_plan(self.meta_wav_like(), self.install)
        stopped = scope_policy.ScopeLatch()
        stopped.stop(137.5e6, 137.6e6)
        with self.assertRaisesRegex(d.DecoderRefused, "OUT_OF_SCOPE"):
            d.satdump_plan(self.meta, self.install, scope=stopped)

    def meta_wav_like(self):
        return {"v": 1, "sha256": "a" * 64, "purpose": "public_civil_weather"}

    def test_publish_releases_sanitized_png_only(self):
        out = Path(self.tmp.name) / "out"
        (out / "MSU-MR").mkdir(parents=True)
        (out / "MSU-MR" / "rgb.png").write_bytes(png())
        (out / "products.cbor").write_bytes(b"cbor")
        (out / "x.cadu").write_bytes(b"cadu")
        plan = d.satdump_plan(self.meta, self.install)
        target = Path(self.tmp.name) / "published"
        report = d.satdump_publish(out, target, plan)
        self.assertEqual(sorted(p.name for p in target.iterdir()), ["image-00.png", "report.json"])
        self.assertNotIn(b"PRIVATE_SENTINEL", (target / "image-00.png").read_bytes())
        self.assertEqual(json.loads((target / "report.json").read_text()), report)
        with self.assertRaisesRegex(d.DecoderRefused, "NEW_ABSOLUTE_OUTPUT_DIRECTORY_REQUIRED"):
            d.satdump_publish(out, target, plan)
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        with self.assertRaisesRegex(d.DecoderRefused, "SATDUMP_NO_IMAGE_PRODUCT"):
            d.satdump_publish(empty, Path(self.tmp.name) / "published2", plan)
        stopped = scope_policy.ScopeLatch()
        stopped.stop(137.5e6, 137.6e6)
        with self.assertRaisesRegex(d.DecoderRefused, "OUT_OF_SCOPE"):
            d.satdump_publish(out, Path(self.tmp.name) / "published3", plan, scope=stopped)
        self.assertFalse((Path(self.tmp.name) / "published3").exists())
        self.assertFalse((Path(self.tmp.name) / ".published3.publishing").exists())


if __name__ == "__main__":
    unittest.main()
