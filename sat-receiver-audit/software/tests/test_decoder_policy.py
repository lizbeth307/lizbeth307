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
            for preset in ("egc-safetynet", "dsc-safety", "satdump-weather", "ais-public", "adsb-public"):
                with self.subTest(preset=preset), self.assertRaisesRegex(d.DecoderRefused, "DISABLED"):
                    d.make_plan(preset, None, None, None)

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

    def test_cli_disabled_gate_does_not_even_read_metadata(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = d.main(["plan", "--preset", "egc-safetynet", "--source", "/missing/source",
                           "--metadata", "/missing/meta", "--installation", "/missing/tool"])
        self.assertEqual(code, 2)
        self.assertIn("DISABLED_NO_VERIFIED_HEADER_PARSER", stdout.getvalue())
        self.assertNotIn("/missing", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
