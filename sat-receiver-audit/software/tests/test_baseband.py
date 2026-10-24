"""v2.1 bounded LRPT baseband recorder (srrx.baseband, labrx.run_baseband) with synthetic IQ only.

Nothing here is RF evidence: tones are generated in RAM, the clock is synthetic, the store is a
temporary directory behind a stand-in for StorageGuard (the real guard needs an exact mount).
"""
import contextlib
import errno
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock

import numpy as np

from srrx import baseband as bb
from srrx import scope_policy, voice_mask

AOS = 1_800_000_000.0
POSIX = os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "fstatvfs")
if POSIX:
    from srrx import labrx  # Linux only (resource, prctl)


def window(center=137_900_000, rate=72_000, aos=AOS, duration=600.0, target="Meteor-M N2-3", norad=40001):
    return bb.window(norad, target, center, rate, aos, aos + duration, bb.iso_utc(aos), bb.iso_utc(aos + duration))


def tone(offset_hz, seconds=0.25, amplitude=0.99, rate=bb.INPUT_RATE_HZ, phase=0):
    t = (np.arange(int(seconds * rate)) + phase) / rate
    return (amplitude * np.exp(2j * np.pi * offset_hz * t)).astype(np.complex64)


def run_chain(chain, samples, block=8192):
    return np.concatenate([chain.push(samples[k:k + block]) for k in range(0, samples.size, block)] + [chain.flush()])


def amplitude(interleaved):
    return float(np.sqrt(np.mean(interleaved.astype(np.float64) ** 2) * 2) / bb.CI16_SCALE)


class WindowTests(unittest.TestCase):
    def test_window_is_aos_minus_60_to_los_plus_60_and_at_most_20_min(self):
        value = window(duration=900.0)
        self.assertEqual(value["start_unix_s"], AOS - 60)
        self.assertEqual(value["end_unix_s"], AOS + 960)
        self.assertFalse(value["clipped"])
        long = window(duration=1300.0)
        self.assertTrue(long["clipped"])
        self.assertEqual(long["end_unix_s"] - long["start_unix_s"], bb.MAX_FILE_S)
        self.assertEqual(bb.planned_bytes(value), 1020 * bb.OUTPUT_RATE_HZ * 4)

    def test_half_width_matches_the_policy_figures(self):
        # STACK.md:977: +-(Rs*1.6/2 + 3.2 kHz + 20 kHz), about +-81/+-87 kHz for 72k/80k.
        self.assertEqual(round(bb.half_width_hz(137_900_000, 72_000) / 1000), 81)
        self.assertEqual(round(bb.half_width_hz(137_900_000, 80_000) / 1000), 87)
        self.assertAlmostEqual(bb.doppler_hz(137_100_000), 3201, delta=1)
        # The voice-mask window formula and the channel window are one formula.
        planned = voice_mask.plan_windows(
            {"time_verified": True, "passes": [{"norad_id": 7, "aos_utc": "2027-01-15T08:00:00Z", "los_utc": "2027-01-15T08:10:00Z"}]},
            {7: [{"downlink_hz": 137_900_000.0, "bandwidth_hz": 72_000 * 1.6, "mode": "LRPT"}]})
        low, high = bb.channel_span(137_900_000, 72_000)
        self.assertAlmostEqual(planned[0][2], low, places=6)
        self.assertAlmostEqual(planned[0][3], high, places=6)

    def test_only_meteor_targets_and_allowed_tunings(self):
        for kwargs in ({"target": "NOAA 19"}, {"target": "METEOR-M2 3"}, {"center": 137_620_000},
                       {"center": 137_900_000.0}, {"rate": 64_000}, {"rate": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(bb.BasebandRefused):
                window(**kwargs)
        for center in bb.CENTERS_HZ:
            low, high = bb.channel_span(center, 80_000)
            self.assertTrue(137e6 < low < high < 138e6)

    def test_every_derived_field_is_rechecked(self):
        good = window()
        for key, value in (("start_unix_s", good["start_unix_s"] - 30), ("end_unix_s", good["end_unix_s"] + 1),
                           ("pipeline", "meteor_m2-x_lrpt_80k"), ("half_width_hz", 200_000.0), ("clipped", True),
                           ("policy", "v3"), ("extra", 1)):
            with self.subTest(key=key), self.assertRaises(bb.BasebandRefused):
                bb.validate_window(dict(good, **{key: value}))
        self.assertEqual(bb.validate_window(json.loads(json.dumps(good))), good)


class ChannelTests(unittest.TestCase):
    def test_filter_meets_the_stopband_for_every_tuning(self):
        for center in bb.CENTERS_HZ:
            for rate in bb.PIPELINES:
                with self.subTest(center=center, rate=rate):
                    taps = bb.design_taps(center, rate)
                    stop, ripple = bb.verify_taps(taps, center, rate)
                    self.assertLessEqual(stop, bb.STOPBAND_DB)
                    self.assertLessEqual(ripple, bb.PASSBAND_RIPPLE_DB)
                    self.assertEqual(taps.size % 2, 1)

    def test_out_of_window_tones_are_stored_as_zeros(self):
        value = window()
        half = value["half_width_hz"]
        # Just outside the edge, the aliasing images of the decimation, and far out.
        for offset in (half + 500, -(half + 500), 128_000, 256_000 - 30_000, 256_000 + 30_000, -400_000, 505_000):
            with self.subTest(offset=offset):
                stored = run_chain(bb.ChannelChain(value), tone(offset))
                self.assertEqual(np.count_nonzero(stored), 0)

    def test_in_window_tones_keep_their_amplitude_and_rate(self):
        value = window(rate=80_000)
        for offset in (0, 15_000, -40_000, 60_000):
            with self.subTest(offset=offset):
                chain = bb.ChannelChain(value)
                samples = tone(offset, amplitude=0.5)
                stored = run_chain(chain, samples)
                self.assertAlmostEqual(amplitude(stored[2000:]), 0.5, delta=0.005)
                self.assertEqual(stored.size // 2, samples.size // bb.DECIMATION - chain.warmup_samples)
                self.assertEqual(chain.clipped, 0)

    def test_chain_uses_the_voice_mask_with_the_window_as_only_span(self):
        value, calls = window(center=137_100_000), []

        class Spy(voice_mask.VoiceExcisor):
            def __init__(self, *args, **kwargs):
                calls.append(args)
                super().__init__(*args, **kwargs)
        with mock.patch.object(voice_mask, "VoiceExcisor", Spy):
            bb.ChannelChain(value)
        self.assertEqual(calls, [(137_100_000.0, float(bb.INPUT_RATE_HZ), [bb.channel_span(137_100_000, 72_000)])])

    def test_chunking_does_not_change_the_output(self):
        value = window()
        rng = np.random.default_rng(7)
        noise = ((rng.normal(size=300_000) + 1j * rng.normal(size=300_000)) * 0.1).astype(np.complex64)
        whole = run_chain(bb.ChannelChain(value), noise, block=300_000)
        pieces = run_chain(bb.ChannelChain(value), noise, block=1234)
        self.assertEqual(whole.size, pieces.size)
        self.assertLessEqual(int(np.max(np.abs(whole.astype(np.int32) - pieces.astype(np.int32)))), 1)  # FFT rounding only

    def test_ci16_scale_is_the_inverse_of_the_satdump_cs16_reader(self):
        interleaved, clipped = bb.quantize_ci16(np.array([0.5 + 0.25j, -1.2 + 1.0j, 3e-6 - 3e-6j]))
        self.assertEqual(interleaved.dtype.str, "<i2")
        self.assertEqual(interleaved.tolist(), [16384, 8192, -32767, 32767, 0, 0])
        self.assertEqual(clipped, 1)
        # SatDump 1aedd60 baseband_interface.h:183 volk_16i_s32f_convert_32f(..., 32767).
        back = bb.ci16_to_cf32(interleaved)
        self.assertEqual(back.dtype.str, "<c8")
        self.assertAlmostEqual(complex(back[0]).real, 16384 / 32767, places=6)


class FakeSocket:
    def __init__(self, family, kind):
        self.family, self.kind, self.peer, self.sent, self.closed, self.fail = family, kind, None, [], False, None

    def setblocking(self, flag):
        self.blocking = flag

    def connect(self, address):
        self.peer = address

    def send(self, data):
        if self.fail:
            raise self.fail
        self.sent.append(bytes(data))
        return len(data)

    def close(self):
        self.closed = True


class LiveTests(unittest.TestCase):
    def sink(self, port=8877):
        made = []
        sink = bb.LiveUdpSink(port, socket_factory=lambda *a: made.append(FakeSocket(*a)) or made[-1])
        return sink, made[0]

    def test_datagrams_go_to_loopback_only_and_never_exceed_8188_samples(self):
        sink, sock = self.sink()
        self.assertEqual((sock.family, sock.kind, sock.peer, sock.blocking),
                         (socket.AF_INET, socket.SOCK_DGRAM, ("127.0.0.1", 8877), False))
        samples = np.arange(20_000, dtype=np.float32).view(np.complex64)  # 10 000 complex samples
        sink.send(samples)
        self.assertEqual([len(d) for d in sock.sent], [8188 * 8, (10_000 - 8188) * 8])
        self.assertLessEqual(max(len(d) for d in sock.sent), 65507)
        self.assertEqual(b"".join(sock.sent), samples.tobytes())
        self.assertEqual(sink.status()["sent_samples"], 10_000)

    def test_errors_drop_datagrams_and_never_raise(self):
        sink, sock = self.sink()
        sock.fail = ConnectionRefusedError(errno.ECONNREFUSED, "no listener")
        sink.send(np.zeros(100, np.complex64))
        self.assertEqual((sink.dropped_datagrams, sink.sent_datagrams), (1, 0))
        with self.assertRaises(bb.BasebandRefused):
            sink.send(b"\x00" * 12)

    def test_port_range_and_no_address_parameter(self):
        for port in (0, 80, 70000, "8877", True):
            with self.subTest(port=port), self.assertRaises(bb.BasebandRefused):
                bb.LiveUdpSink(port, socket_factory=FakeSocket)
        with self.assertRaises(TypeError):
            bb.LiveUdpSink(8877, host="0.0.0.0")

    @unittest.skipIf(os.environ.get("SRRX_TEST_INET_DENIED") == "1", "Internet sockets are denied in this test process")
    def test_real_loopback_socket_receives_one_datagram_per_chunk(self):
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(receiver.close)
        receiver.bind(("127.0.0.1", 0))
        receiver.settimeout(2)
        sink = bb.LiveUdpSink(receiver.getsockname()[1])
        self.addCleanup(sink.close)
        sink.send(np.ones(9000, np.complex64))
        sizes = [len(receiver.recv(65536)) for _ in range(2)]
        self.assertEqual(sizes, [8188 * 8, 812 * 8])


class MetadataTests(unittest.TestCase):
    def meta(self, **changes):
        fields = dict(created_s=AOS - 55.0, first_block_s=AOS - 55.0, samples=1000, sha512="a" * 128, clipped=0, gaps=0,
                      joins=0, source="SIMULATION", group_delay=685, stop_reason="WINDOW_END")
        fields.update(changes)
        return bb.metadata("lrpt-0123456789abcdef", window(), **fields)

    def test_sigmf_core_fields_and_policy_flags(self):
        value = self.meta()
        meta = value["global"]
        self.assertEqual((meta["core:datatype"], meta["core:sample_rate"], meta["core:version"]), ("ci16_le", 256000, "1.2.6"))
        self.assertEqual(meta["core:extensions"], [{"name": "srrx", "version": "1.0.0", "optional": True}])
        self.assertEqual((meta["srrx:pinned"], meta["srrx:export"], meta["srrx:utc_verified"]), (False, False, True))
        self.assertEqual(meta["srrx:delete_after_utc"], bb.iso_utc(AOS - 55.0 + 86400))
        self.assertEqual(value["captures"], [{"core:sample_start": 0, "core:frequency": 137_900_000,
                                              "core:datetime": bb.iso_utc(AOS - 55.0)}])

    def test_any_other_value_is_not_a_recording(self):
        value = self.meta()
        for key, bad in (("srrx:pinned", True), ("srrx:export", True), ("srrx:target", "NOAA 19"), ("core:datatype", "cf32_le"),
                         ("srrx:utc_verified", False), ("srrx:samples", 10 ** 12), ("srrx:delete_after_utc", bb.iso_utc(AOS + 10 ** 6)),
                         ("srrx:source", "ARCHIVE"), ("srrx:masks", [])):
            with self.subTest(key=key):
                changed = json.loads(json.dumps(value))
                changed["global"][key] = bad
                with self.assertRaises(bb.BasebandRefused):
                    bb.validate_metadata(changed)
        extra = json.loads(json.dumps(value))
        extra["global"]["srrx:copy_to"] = "/media/usb"
        with self.assertRaises(bb.BasebandRefused):
            bb.validate_metadata(extra)


class DirGuard:
    """StorageGuard stand-in over a temporary directory: check() and open_directory() only."""

    def __init__(self, root):
        self.root = Path(root)
        (self.root / bb.CLASS_DIR).mkdir(parents=True)
        self.revoked, self.checks = False, 0

    def check(self):
        self.checks += 1
        if self.revoked:
            raise OSError(errno.ENODEV, "Storage guard revoked")

    def open_directory(self, path):
        self.check()
        return os.open(self.root / path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


class StoreCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="srrx-bb-")
        self.addCleanup(temp.cleanup)
        self.guard = DirGuard(temp.name)
        self.now = [AOS - 50.0]
        self.store = bb.BasebandStore(self.guard, clock=lambda: self.now[0])
        patcher = mock.patch.object(bb, "_preallocate", None)  # no 100 MB preallocation per test
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cls = self.guard.root / bb.CLASS_DIR

    def names(self):
        return sorted(p.name for p in self.cls.iterdir() if p.name != bb.LOCK_NAME)

    def record(self, samples=4096, value=None, sweep=True, **fields):
        quiet = contextlib.nullcontext() if sweep else mock.patch.object(self.store, "_sweep_locked", return_value={})
        with quiet:
            recording = self.store.begin(value or window())
        try:
            data = (np.arange(samples * 2) % 200 - 100).astype("<i2")
            recording.write(data)
            defaults = dict(created_s=self.now[0], first_block_s=self.now[0], clipped=0, gaps=0, joins=0,
                            source="SIMULATION", group_delay=685, stop_reason="WINDOW_END")
            defaults.update(fields)
            meta = recording.finish(**defaults)
        finally:
            self.store.end()
        path = self.cls / (meta["global"]["srrx:recording_id"] + bb.DATA_SUFFIX)
        os.utime(path, (self.now[0], self.now[0]))  # file times on the synthetic clock as well
        return meta, data


@unittest.skipUnless(POSIX, "dirfd-relative store needs Linux")
class StoreTests(StoreCase):
    def test_finish_publishes_data_and_metadata_with_digest(self):
        meta, data = self.record()
        rid = meta["global"]["srrx:recording_id"]
        self.assertEqual(self.names(), [rid + ".sigmf-data", rid + ".sigmf-meta"])
        self.assertEqual((self.cls / (rid + ".sigmf-data")).read_bytes(), data.tobytes())
        self.assertEqual(meta["global"]["core:sha512"], hashlib.sha512(data.tobytes()).hexdigest())
        self.assertEqual(os.stat(self.cls / (rid + ".sigmf-data")).st_mode & 0o777, 0o640)
        loaded, identity = self.store.load(rid)
        self.assertEqual(loaded, meta)
        (self.cls / (rid + ".sigmf-data")).write_bytes(data.tobytes()[:-4] + b"\x00\x00\x00\x00")
        with self.assertRaisesRegex(bb.BasebandRefused, "RECORDING_DATA_DIGEST"):
            self.store.load(rid)

    def test_abort_deletes_the_partial_file(self):
        recording = self.store.begin(window())
        recording.write(np.zeros(100, "<i2"))
        self.assertEqual(len(self.names()), 1)
        recording.abort()
        self.store.end()
        self.assertEqual(self.names(), [])

    def test_reserved_size_is_never_exceeded(self):
        value = window(duration=0.0)  # 120 s: 30 720 000 samples
        recording = self.store.begin(value)
        self.assertEqual(recording.reserved, bb.planned_bytes(value))
        recording.written = recording.reserved - 8  # as if the file were nearly full
        self.assertEqual(recording.write(np.zeros(100, "<i2")), 2)
        self.assertTrue(recording.full)
        recording.abort()
        self.store.end()

    def test_class_cap_raw_quota_and_free_space_refuse_before_any_file(self):
        big = self.cls / "lrpt-ffffffffffffffff.sigmf-data"
        with open(big, "wb") as stream:
            stream.truncate(bb.CLASS_CAP_BYTES - bb.reserve_bytes(bb.planned_bytes(window())) + 1)
        (self.cls / "lrpt-ffffffffffffffff.sigmf-meta").write_text("{}")  # invalid: the sweep removes both
        self.store.begin(window()).abort()  # sweep first: the invalid pair is gone, so it fits
        self.store.end()
        meta, unused = self.record()
        other = self.guard.root / bb.RAW_DIR / "npu"
        other.mkdir()
        with open(other / "capture.cu8", "wb") as stream:
            stream.truncate(bb.RAW_QUOTA_BYTES)
        with self.assertRaisesRegex(bb.BasebandRefused, "RAW_QUOTA_30_GIB"):
            self.store.begin(window())
        (other / "capture.cu8").unlink()
        with open(self.cls / "lrpt-eeeeeeeeeeeeeeee.sigmf-data", "wb") as stream:
            stream.truncate(bb.CLASS_CAP_BYTES)
        (self.cls / "lrpt-eeeeeeeeeeeeeeee.sigmf-meta").write_text("{}")
        with mock.patch.object(bb.BasebandStore, "_keep", return_value=True):  # as if a valid large recording
            with self.assertRaisesRegex(bb.BasebandRefused, "CLASS_CAP_1_5_GIB"):
                self.store.begin(window())
        for suffix in (".sigmf-data", ".sigmf-meta"):
            (self.cls / ("lrpt-eeeeeeeeeeeeeeee" + suffix)).unlink()
        tiny = type("V", (), {"f_bavail": 1, "f_frsize": 4096})
        with mock.patch.object(bb.os, "fstatvfs", return_value=tiny):
            with self.assertRaisesRegex(bb.BasebandRefused, "STORAGE_FREE_SPACE"):
                self.store.begin(window())
        self.assertEqual(len([n for n in self.names() if n.endswith(".partial")]), 0)

    def test_sweep_deletes_old_future_incomplete_and_foreign_files(self):
        fresh, unused = self.record()
        fresh_id = fresh["global"]["srrx:recording_id"]
        self.now[0] = AOS - 50.0 - 86400 + 30  # made almost a day earlier
        self.record(sweep=False)
        self.now[0] = AOS + 7200  # two hours in the "future"
        self.record(sweep=False)
        self.now[0] = AOS - 50.0 + 60
        (self.cls / "lrpt-1111111111111111.sigmf-data.partial").write_bytes(b"\x00" * 8)
        (self.cls / "lrpt-2222222222222222.sigmf-data").write_bytes(b"\x00" * 8)  # no metadata
        (self.cls / "notes.txt").write_text("anything")
        (self.cls / "subdir").mkdir()
        result = self.store.sweep()
        self.assertEqual(result["kept"], 1)
        self.assertEqual(result["foreign_directories"], 1)
        self.assertEqual(self.names(), sorted([fresh_id + ".sigmf-data", fresh_id + ".sigmf-meta", "subdir"]))
        self.now[0] = AOS - 50.0 + 86400
        self.store.sweep()
        self.assertEqual(self.names(), ["subdir"])

    def test_sweep_waits_for_a_running_recorder(self):
        recording = self.store.begin(window())
        try:
            self.assertEqual(self.store.sweep()["skipped"], "RECORDER_BUSY")
            with self.assertRaisesRegex(bb.BasebandRefused, "RECORDER_BUSY"):
                bb.BasebandStore(self.guard).begin(window())
        finally:
            recording.abort()
            self.store.end()

    def test_delete_and_no_export_interface(self):
        meta, unused = self.record()
        self.assertTrue(self.store.delete(meta["global"]["srrx:recording_id"]))
        self.assertEqual(self.names(), [])
        public = {name for name in dir(bb.BasebandStore) if not name.startswith("_")}
        self.assertEqual(public, {"begin", "end", "usage", "delete", "sweep", "load", "data_path", "identity"})
        with self.assertRaises(bb.BasebandRefused):
            self.store.delete("../etc/passwd")
        with self.assertRaises(bb.BasebandRefused):
            bb.BasebandStore(None)

    def test_cli_has_only_sweep_and_usage(self):
        with self.assertRaises(SystemExit):
            bb.main(["export", "--storage-root", "/data", "--storage-device", "/dev/null"])


class SyntheticClock:
    def __init__(self, start, step):
        self.now, self.step = start, step

    def __call__(self):
        value = self.now
        self.now += self.step
        return value


def blocks(offset=20_000.0, count=None, size=8192):
    index = 0
    while count is None or index < count:
        yield tone(offset, seconds=size / bb.INPUT_RATE_HZ, amplitude=0.4, phase=index * size)
        index += 1


@unittest.skipUnless(POSIX, "dirfd-relative store needs Linux")
class RunBasebandTests(StoreCase):
    def run_pass(self, **kwargs):
        options = dict(scope=scope_policy.ScopeLatch(), clock=SyntheticClock(AOS - 61.0, 2.0),
                       utc_verified=lambda: True, synthetic=blocks())
        options.update(kwargs)
        return labrx.run_baseband(window(duration=0.0), self.store, **options)

    def test_records_only_inside_the_window_and_stops_at_its_end(self):
        made = []
        result = self.run_pass(live_port=9000, live_socket_factory=lambda *a: made.append(FakeSocket(*a)) or made[-1])
        self.assertEqual(result["stop_reason"], "WINDOW_END")
        self.assertTrue(result["raw_iq_persisted"])
        self.assertFalse(result["export"])
        # The clock steps 2 s per call from AOS-61 s: blocks at AOS-59 .. AOS+59 s are in the window.
        rid = result["recording_id"]
        meta, unused = self.store.load(rid)
        self.assertEqual(meta["global"]["srrx:source"], "SIMULATION")
        self.assertEqual(meta["global"]["srrx:stop_reason"], "WINDOW_END")
        data = (self.cls / (rid + ".sigmf-data")).read_bytes()
        self.assertEqual(len(data), result["bytes"])
        self.assertAlmostEqual(amplitude(np.frombuffer(data, "<i2")[4000:]), 0.4, delta=0.01)
        # The live path carries exactly the stored samples, as cf32, to 127.0.0.1.
        self.assertEqual(made[0].peer, ("127.0.0.1", 9000))
        live = np.frombuffer(b"".join(made[0].sent), "<c8")
        self.assertTrue(np.array_equal(live, bb.ci16_to_cf32(np.frombuffer(data, "<i2"))))
        self.assertTrue(made[0].closed)

    def test_unverified_utc_refuses_and_writes_nothing(self):
        with self.assertRaisesRegex(ValueError, "UTC_NOT_VERIFIED"):
            self.run_pass(utc_verified=lambda: False)
        self.assertEqual(self.names(), [])
        state = {"calls": 0}

        def lost():
            state["calls"] += 1
            return state["calls"] < 5
        with self.assertRaisesRegex(ValueError, "UTC_NOT_VERIFIED"):
            self.run_pass(utc_verified=lost)
        self.assertEqual(self.names(), [])  # the partial file was deleted

    def test_scope_stop_storage_loss_and_errors_delete_the_partial_file(self):
        scope = scope_policy.ScopeLatch()
        low, high = bb.channel_span(137_900_000, 72_000)

        def stopping(count=[0]):
            for samples in blocks():
                count[0] += 1
                if count[0] == 6:
                    scope.stop(low, high)  # an operator or identification stop mid-pass
                yield samples
        with self.assertRaisesRegex(ValueError, scope_policy.OUT_OF_SCOPE):
            self.run_pass(scope=scope, synthetic=stopping())
        self.assertEqual(self.names(), [])

        def revoking(count=[0]):
            for samples in blocks():
                count[0] += 1
                if count[0] == 6:
                    self.guard.revoked = True
                yield samples
        with self.assertRaises(OSError):
            self.run_pass(synthetic=revoking())
        self.guard.revoked = False
        self.assertEqual(self.names(), [])

        def broken():
            yield from blocks(count=5)
            raise KeyboardInterrupt(143)  # SIGTERM: a stop deletes the partial file
        with self.assertRaises(KeyboardInterrupt):
            self.run_pass(synthetic=broken())
        self.assertEqual(self.names(), [])

    def test_window_bounds_refuse_early_and_late_starts(self):
        with self.assertRaisesRegex(ValueError, "WINDOW_NOT_STARTED"):
            self.run_pass(clock=SyntheticClock(AOS - 120.0, 2.0))
        with self.assertRaisesRegex(ValueError, "WINDOW_OVER"):
            self.run_pass(clock=SyntheticClock(AOS + 61.0, 2.0))
        with self.assertRaisesRegex(ValueError, "session ScopeLatch"):
            self.run_pass(scope=None)

    def test_masked_receiver_span_refuses(self):
        with mock.patch.object(scope_policy, "scope_check", return_value={"stop": True, "reason": "MASKED_BAND"}):
            with self.assertRaisesRegex(ValueError, scope_policy.OUT_OF_SCOPE):
                self.run_pass()
        self.assertEqual(self.names(), [])

    def test_hardware_path_needs_labd_utc_and_switches_the_branch_off(self):
        requests = []

        def transport(request, utc=True):
            requests.append(request)
            if request["op"] == "control":
                return {"ok": True}
            data = {"mode": "HARDWARE", "hardware_qualified": True, "live_identity_verified": True, "configured": True,
                    "last_error": None, "pico": {"state": "ACTIVE", "mcp_reset": False}, "session": "s1",
                    "policy": {"armed": True, "commissioned": True, "pico_active": True, "fault": None,
                               "outputs": {"EN_RTLA": True}}}
            if utc:
                data["utc_verified"] = True
            return {"ok": True, "data": data}

        class Source:
            discontinuity, dropped_blocks = True, 0

            def __init__(self, record, center, rate):
                self.args, self.feed = (center, rate), blocks()

            def read(self, guard, keep):
                guard.check()
                return next(self.feed)

            def close(self):
                pass
        record = {"backend": "rtl", "branch": "RTLA"}
        with mock.patch.object(labrx, "_disable_worker_core_dumps"):
            result = self.run_pass(record=record, transport=transport, source_factory=Source, synthetic=None,
                                   utc_verified=lambda: False)  # ignored on hardware: labd's status decides
            self.assertEqual(result["source"], "HARDWARE")
            self.assertTrue(result["branch_off_confirmed"])
            self.assertEqual(requests[-1], {"op": "control", "name": "EN_RTLA", "value": False})
            self.assertGreater(self.store.load(result["recording_id"])[0]["global"]["srrx:unproven_joins"], 0)
            with self.assertRaisesRegex(ValueError, "UTC_NOT_VERIFIED"):
                self.run_pass(record=record, transport=lambda r: transport(r, utc=False), source_factory=Source,
                              synthetic=None)
            with self.assertRaisesRegex(ValueError, "RTL branch"):
                self.run_pass(record={"backend": "airspyhf", "branch": "HFP"}, transport=transport, synthetic=None)

    def test_cli_requires_hardware_storage_and_a_plan(self):
        self.assertEqual(labrx.main(["--simulate", "--baseband-plan", "/nonexistent.json"]), 2)
        self.assertEqual(labrx.main(["--simulate", "--symbol-rate", "72000"]), 2)


if __name__ == "__main__":
    unittest.main()
