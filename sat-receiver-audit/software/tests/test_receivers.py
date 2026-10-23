import ctypes as C
import errno
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

import numpy as np

from srrx.receivers import RTLReceiver, ControlGuard, load_driver_record, validate_tuning


def ready():
    return {"ok": True, "data": {"mode": "HARDWARE", "hardware_qualified": True,
        "live_identity_verified": True, "configured": True, "last_error": None,
        "session": "session-17", "pico": {"state": "ACTIVE", "mcp_reset": False},
        "policy": {"armed": True, "commissioned": True, "pico_active": True,
                   "fault": None, "outputs": {"EN_RTLA": True}}}}


class Function:
    def __init__(self, fn):
        self.fn = fn
    def __call__(self, *args):
        return self.fn(*args)


class FakeRTL:
    def __init__(self, serials=("307A",)):
        self.serials, self.calls = serials, []
        self.center, self.rate = 0, 0
        for name in ("rtlsdr_get_device_count", "rtlsdr_get_device_usb_strings", "rtlsdr_open",
                     "rtlsdr_close", "rtlsdr_get_usb_strings", "rtlsdr_set_bias_tee",
                     "rtlsdr_set_direct_sampling", "rtlsdr_set_center_freq", "rtlsdr_get_center_freq",
                     "rtlsdr_set_sample_rate", "rtlsdr_get_sample_rate", "rtlsdr_set_tuner_gain_mode",
                     "rtlsdr_set_agc_mode", "rtlsdr_reset_buffer", "rtlsdr_read_sync"):
            setattr(self, name, Function(lambda *a, n=name: self.invoke(n, a)))
    def invoke(self, name, args):
        self.calls.append((name, args))
        if name == "rtlsdr_get_device_count": return len(self.serials)
        if name == "rtlsdr_get_device_usb_strings": args[3].value = self.serials[args[0]].encode()
        if name == "rtlsdr_open": C.cast(args[0], C.POINTER(C.c_void_p))[0] = 307
        if name == "rtlsdr_get_usb_strings": args[3].value = b"307A"
        if name == "rtlsdr_set_center_freq": self.center = args[1]
        if name == "rtlsdr_set_sample_rate": self.rate = args[1]
        if name == "rtlsdr_get_center_freq": return self.center
        if name == "rtlsdr_get_sample_rate": return self.rate
        if name == "rtlsdr_read_sync":
            a = np.tile(np.array([255, 0], dtype=np.uint8), 8192)
            C.memmove(args[1], a.ctypes.data, len(a))
            C.cast(args[3], C.POINTER(C.c_int))[0] = len(a)
        return 0


class ReceiverTests(unittest.TestCase):
    def test_rtl_binding_selects_unique_serial_and_only_disables_bias(self):
        lib = FakeRTL()
        rx = RTLReceiver({"serial": "307A", "library_path": "/fixture/lib.so"}, 100000000, 1024000,
                         loader=lambda _: lib)
        a = rx.read()
        self.assertEqual(a.shape, (8192,))
        self.assertTrue(np.allclose(a, 1-1j))
        rx.close(); rx.close()
        self.assertEqual([a[1] for n, a in lib.calls if n == "rtlsdr_set_bias_tee"], [0, 0])
        self.assertEqual(sum(n == "rtlsdr_close" for n, _ in lib.calls), 1)
        self.assertFalse(any("eeprom" in n or "tx" in n for n, _ in lib.calls))

    def test_ambiguous_or_absent_serial_does_not_open(self):
        for serials in [("307A", "307A"), ("other",)]:
            lib = FakeRTL(serials)
            with self.assertRaises(OSError):
                RTLReceiver({"serial": "307A", "library_path": "/fixture/lib.so"}, 100000000, 1024000,
                            loader=lambda _: lib)
            self.assertFalse(any(n == "rtlsdr_open" for n, _ in lib.calls))

    def test_guard_never_arms_or_renews_and_latches_session(self):
        reply, calls = ready(), []
        def transport(command):
            calls.append(command)
            return reply
        guard = ControlGuard(transport, "RTLA")
        guard.check()
        reply["data"]["session"] = "new-session"
        with self.assertRaises(RuntimeError): guard.check()
        self.assertEqual(calls, [{"op": "status"}, {"op": "status"}])

    def test_guard_rejects_every_missing_readiness_boundary(self):
        mutations = [("mode", "SIMULATION"), ("hardware_qualified", False),
                     ("live_identity_verified", False), ("configured", False), ("last_error", "fault")]
        for k, v in mutations:
            reply = ready(); reply["data"][k] = v
            with self.assertRaises(RuntimeError): ControlGuard(lambda _: reply, "RTLA").check()
        for k, v in [("armed", False), ("commissioned", False), ("pico_active", False), ("fault", "fault")]:
            reply = ready(); reply["data"]["policy"][k] = v
            with self.assertRaises(RuntimeError): ControlGuard(lambda _: reply, "RTLA").check()
        for path in [("pico", "mcp_reset", True), ("pico", "state", "TRIPPED")]:
            reply = ready();reply["data"][path[0]][path[1]] = path[2]
            with self.assertRaises(RuntimeError): ControlGuard(lambda _: reply, "RTLA").check()

    def test_explicit_tuning_ranges_and_no_lime_fallback(self):
        validate_tuning("rtl", 100000000, 1024000)
        validate_tuning("airspyhf", 10000000, 768000)
        for args in [("rtl", 100000000, 3200000), ("airspyhf", 40000000, 768000),
                     ("lime", 100000000, 56000000), ("rtl", True, 1024000)]:
            with self.assertRaises(ValueError):validate_tuning(*args)

    def test_driver_must_be_accepted_artifact_and_bind_library_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); library = root / "lib.so"; library.write_bytes(b"not an ELF; validation fixture only")
            record = {"v": 1, "backend": "rtl", "branch": "RTLA", "serial": "307A",
                      "library_path": str(library), "library_sha256": hashlib.sha256(library.read_bytes()).hexdigest(),
                      "rx_only_reviewed": True, "bias_disabled_verified": True, "dependencies_reviewed": True}
            p = root / "driver.json";p.write_text(json.dumps(record))
            accepted = {"gates": {"E5-fixture": {"evidence": {"artifacts": []}}}}
            with self.assertRaises(ValueError):load_driver_record(p, root, accepted)
            accepted["gates"]["E5-fixture"]["evidence"]["artifacts"] = [{"path": "driver.json", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}]
            self.assertEqual(load_driver_record(p, root, accepted)["serial"], "307A")
            library.write_bytes(b"changed")
            with self.assertRaises(ValueError):load_driver_record(p, root, accepted)


class CaptureTests(unittest.TestCase):
    def test_failed_hardware_guard_never_constructs_worker(self):
        from srrx.labrx import run_capture
        with patch("srrx.labrx.WorkerSource") as worker:
            with self.assertRaises(RuntimeError):
                run_capture(record={"backend": "rtl", "branch": "RTLA"}, transport=lambda _: {"ok": False},
                            source_factory=worker)
            worker.assert_not_called()

    def test_simulation_writes_masked_spectrum_only(self):
        from srrx.labrx import run_capture
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            result=run_capture(center_hz=300000000, frames=2, output=root/"latest.json", survey=root/"survey.jsonl")
            self.assertFalse(result["raw_iq_persisted"])
            self.assertEqual(result["frames"],2)
            frame=json.loads((root/"latest.json").read_text())
            self.assertTrue(all(v is None for v in frame["power_dbfs"]))
            self.assertEqual(set(p.name for p in root.iterdir()), {"latest.json", "survey.jsonl"})

    def test_worker_closed_and_power_off_requested_after_failure(self):
        from srrx.labrx import run_capture
        calls=[]
        class Source:
            closed=False
            def read(self,guard):raise OSError("fixture USB loss")
            def close(self):self.closed=True
        source=Source()
        def transport(request):calls.append(request);return ready()
        with self.assertRaises(OSError):
            run_capture(record={"backend":"rtl","branch":"RTLA"}, transport=transport,
                        source_factory=lambda *a:source)
        self.assertTrue(source.closed)
        self.assertEqual(calls[-1],{"op":"control","name":"EN_RTLA","value":False})

    def test_constructor_failure_still_requests_branch_off(self):
        from srrx.labrx import run_capture
        calls=[]
        def transport(request):calls.append(request);return ready()
        def failing(*args):raise OSError("fixture Process.start failed")
        with self.assertRaises(OSError):
            run_capture(record={"backend":"rtl","branch":"RTLA"},transport=transport,source_factory=failing)
        self.assertEqual(calls[-1],{"op":"control","name":"EN_RTLA","value":False})

    def test_close_failure_cannot_skip_branch_off(self):
        from srrx.labrx import run_capture
        calls=[]
        class Source:
            def read(self,guard):raise OSError("fixture read error")
            def close(self):raise OSError("fixture close error")
        def transport(request):calls.append(request);return ready()
        with self.assertRaises(OSError):
            run_capture(record={"backend":"rtl","branch":"RTLA"},transport=transport,source_factory=lambda *a:Source())
        self.assertEqual(calls[-1],{"op":"control","name":"EN_RTLA","value":False})


    def test_actual_pipe_eof_is_clean_oserror_after_capture_cleanup_and_cli_refusal(self):
        import contextlib
        import io
        import multiprocessing as mp
        from types import SimpleNamespace
        import srrx.labrx as labrx
        # Actual unidirectional multiprocessing pipe EOF, not a mocked recv error.
        reader, sender = mp.get_context("spawn").Pipe(duplex=False)
        sender.close()
        worker = object.__new__(labrx.WorkerSource)
        worker.reader = reader
        worker.process = SimpleNamespace(is_alive=lambda: False)
        calls = []
        def transport(request):
            calls.append(dict(request))
            return ready()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                output, survey = Path(temporary)/"spectrum.json", Path(temporary)/"survey.jsonl"
                with self.assertRaisesRegex(OSError, "worker pipe closed") as caught:
                    labrx.run_capture(frames=1, output=output, survey=survey,
                                      record={"backend":"rtl", "branch":"RTLA"},
                                      transport=transport, source_factory=lambda *a:worker)
                self.assertIsInstance(caught.exception.__cause__, EOFError)
                self.assertTrue(reader.closed)
                self.assertEqual(calls[-1], {"op":"control", "name":"EN_RTLA", "value":False})
                self.assertFalse(output.exists() or survey.exists())
                # The exact normalized failure also follows main's public clean
                # error path; no physical-mode acceptance is fabricated here.
                stderr = io.StringIO()
                with patch.object(labrx, "run_capture", side_effect=caught.exception), contextlib.redirect_stderr(stderr):
                    self.assertEqual(labrx.main(["--simulate", "--frames", "1"]), 2)
                self.assertIn("labrx: RX worker pipe closed", stderr.getvalue())
                self.assertNotIn("Traceback", stderr.getvalue())
        finally:
            reader.close()

    def test_rtl_fft_larger_than_one_read_is_refused_before_control_observation(self):
        from srrx.labrx import run_capture
        transport, factory = Mock(), Mock()
        with self.assertRaisesRegex(ValueError, "8192"):
            run_capture(fft_size=16384, record={"backend":"rtl","branch":"RTLA"},
                        transport=transport, source_factory=factory)
        transport.assert_not_called()
        factory.assert_not_called()

    def test_successive_rtl_reads_and_reported_gaps_never_join_into_one_fft(self):
        from srrx.labrx import run_capture
        cases = (("rtl", "RTLA", 1024000, [False, False, False], [512, 512, 512]),
                 ("airspyhf", "HFP", 768000, [False, False, True], [512, 1024, 512]))
        for backend, branch, rate, gaps, counts in cases:
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as temporary:
                reply = ready()
                reply["data"]["policy"]["outputs"] = {"EN_" + branch: True}
                pending = list(gaps)
                class Source:
                    discontinuity = False
                    def read(self, guard):
                        self.discontinuity = pending.pop(0)
                        return np.ones(512, dtype=np.complex64)
                    def close(self):
                        pass
                survey = Path(temporary)/"survey.jsonl"
                with patch("srrx.labrx._disable_worker_core_dumps"):
                    result = run_capture(sample_rate=rate, fft_size=1024, frames=3, survey=survey,
                                         record={"backend":backend,"branch":branch},
                                         transport=lambda request: reply, source_factory=lambda *a: Source())
                lines = [json.loads(line) for line in survey.read_text().splitlines()]
                self.assertEqual([line["sample_count"] for line in lines], counts)
                self.assertEqual([any(line["valid"]) for line in lines], [count == 1024 for count in counts])
                self.assertIs(result["branch_off_confirmed"], True)

    def test_refused_branch_off_is_reported_and_cli_exits_nonzero(self):
        import contextlib
        import io
        import srrx.labrx as labrx
        def transport(request):
            return ready() if request["op"] == "status" else {"ok": False, "error": "fixture I2C refusal"}
        class Source:
            def read(self, guard):
                return np.ones(64, dtype=np.complex64)
            def close(self):
                pass
        stderr = io.StringIO()
        with patch.object(labrx, "_disable_worker_core_dumps"), contextlib.redirect_stderr(stderr):
            result = labrx.run_capture(fft_size=64, frames=1, record={"backend":"rtl","branch":"RTLA"},
                                       transport=transport, source_factory=lambda *a: Source())
        self.assertIs(result["branch_off_confirmed"], False)
        self.assertIn("EN_RTLA OFF was not confirmed", stderr.getvalue())
        self.assertIsNone(labrx.run_capture(fft_size=64, frames=1)["branch_off_confirmed"])
        with patch.object(labrx, "run_capture", return_value=dict(result)), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(labrx.main(["--simulate"]), 3)

    @unittest.skipUnless(sys.platform == 'linux', 'POSIX stop signals to a fresh capture process')
    def test_sigterm_and_sighup_still_close_source_and_request_branch_off(self):
        code = textwrap.dedent('''
            import json, os, signal, time
            from unittest.mock import patch
            import srrx.labrx as labrx
            calls, events = [], []
            class FixtureGuard:
                def __init__(self, transport, branch): pass
                def check(self): return {'scope': 'signal-fixture-no-hardware-status'}
            class BlockingSource:
                def __init__(self, *arguments): pass
                def read(self, guard):
                    print('READING', flush=True)
                    time.sleep(60)
                def close(self):
                    events.append('close')
                    os.kill(os.getpid(), signal.SIGTERM)  # a repeated stop cannot abort cleanup
                    events.append('after-repeat')
            def transport(request):
                calls.append(request)
                return {'ok': True}
            real = labrx.run_capture
            def capture(**options):
                return real(fft_size=64, frames=0, record={'backend': 'rtl', 'branch': 'RTLA'},
                            transport=transport, source_factory=BlockingSource)
            for number in (signal.SIGTERM, signal.SIGHUP):
                signal.signal(number, signal.SIG_DFL)  # independent of the runner's own dispositions
            with patch.object(labrx, 'ControlGuard', FixtureGuard), patch.object(labrx, 'run_capture', capture):
                code = labrx.main(['--simulate'])
            print(json.dumps({'code': code, 'calls': calls, 'events': events,
                              'restored': [signal.getsignal(s) == signal.SIG_DFL for s in (signal.SIGTERM, signal.SIGHUP)]}))
        ''')
        project = Path(__file__).resolve().parents[2]
        for number in (signal.SIGTERM, signal.SIGHUP):
            with self.subTest(signal=number):
                process = subprocess.Popen([sys.executable, '-c', code], cwd=project, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True,
                                           env=dict(os.environ, PYTHONPATH=str(project/'software'), OPENBLAS_NUM_THREADS='1'))
                try:
                    self.assertEqual(process.stdout.readline().strip(), 'READING')
                    process.send_signal(number)
                    out, err = process.communicate(timeout=30)
                finally:
                    if process.poll() is None:
                        process.kill()
                        process.wait()
                self.assertEqual(process.returncode, 0, err)
                result = json.loads(out.strip().splitlines()[-1])
                self.assertEqual(result['code'], 128 + number)
                self.assertEqual(result['events'], ['close', 'after-repeat'])
                self.assertEqual(result['calls'], [{'op': 'control', 'name': 'EN_RTLA', 'value': False}])
                self.assertEqual(result['restored'], [True, True])

    def test_cli_installs_stop_handlers_but_keeps_an_inherited_nohup_ignore(self):
        import contextlib
        import io
        import srrx.labrx as labrx
        seen = {}
        def capture(**options):
            seen.update(term=signal.getsignal(signal.SIGTERM), hup=signal.getsignal(signal.SIGHUP))
            return {"frames": 0, "branch_off_confirmed": None, "last_frame": None}
        term, hup = signal.getsignal(signal.SIGTERM), signal.signal(signal.SIGHUP, signal.SIG_IGN)
        try:
            with patch.object(labrx, "run_capture", side_effect=capture), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(labrx.main(["--simulate"]), 0)
            self.assertIs(seen["term"], labrx._stop)
            self.assertIs(seen["hup"], signal.SIG_IGN)
            self.assertIs(signal.getsignal(signal.SIGTERM), term)
            self.assertIs(signal.getsignal(signal.SIGHUP), signal.SIG_IGN)
        finally:
            signal.signal(signal.SIGHUP, hup)

    @unittest.skipUnless(hasattr(signal, "SIGHUP"), "POSIX stop signals")
    def test_first_stop_inside_cleanup_cannot_abort_branch_off_or_raise_from_a_dead_tty(self):
        import srrx.labrx as labrx
        numbers = (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)
        saved = {number: signal.getsignal(number) for number in numbers}
        class DeadTTY:
            def write(self, text):
                raise OSError(errno.EIO, "fixture hung-up terminal")
            def flush(self):
                pass
        try:
            for where, number in (("close", signal.SIGHUP), ("off", signal.SIGTERM), ("off", signal.SIGINT)):
                with self.subTest(where=where, signal=number):
                    for each in numbers:
                        signal.signal(each, labrx._stop)
                    calls = []
                    def transport(request):
                        if request["op"] != "control":
                            return ready()
                        if where == "off":
                            labrx._stop(number, None)  # the handler runs while the OFF request is in flight
                        calls.append(request)
                        return {"ok": False, "error": "fixture refusal"}
                    class Source:
                        def read(self, guard):
                            return np.ones(64, dtype=np.complex64)
                        def close(self):
                            if where == "close":
                                labrx._stop(number, None)
                    try:
                        with patch.object(labrx, "_disable_worker_core_dumps"), patch.object(sys, "stderr", DeadTTY()):
                            result = labrx.run_capture(fft_size=64, frames=1, record={"backend": "rtl", "branch": "RTLA"},
                                                       transport=transport, source_factory=lambda *a: Source())
                    except (KeyboardInterrupt, OSError) as exc:
                        self.fail("cleanup was aborted: " + repr(exc))
                    self.assertEqual(calls, [{"op": "control", "name": "EN_RTLA", "value": False}])
                    self.assertIs(result["branch_off_confirmed"], False)
                    self.assertTrue(all(signal.getsignal(each) is signal.SIG_IGN for each in numbers))  # one-shot
                    self.assertFalse(labrx._STOP["cleanup"])
                    for each in numbers:
                        signal.signal(each, labrx._stop)
                    with self.assertRaises(KeyboardInterrupt) as stop:
                        labrx._stop(number, None)  # outside cleanup a first stop still interrupts capture
                    self.assertEqual(stop.exception.args, (128 + number,))
        finally:
            for number, handler in saved.items():
                signal.signal(number, handler)


class WorkerProtocolTests(unittest.TestCase):
    """Real unidirectional pipe; the worker process is a stub, never a driver."""
    def setUp(self):
        import multiprocessing as mp
        import srrx.labrx as labrx
        self.labrx = labrx
        self.reader, self.sender = mp.get_context("spawn").Pipe(duplex=False)
        self.addCleanup(self.reader.close)
        self.addCleanup(self.sender.close)
        self.worker = object.__new__(labrx.WorkerSource)
        self.worker.reader = self.reader
        self.worker.process = SimpleNamespace(is_alive=lambda: True)
        self.checks = []
        self.guard = SimpleNamespace(check=lambda: self.checks.append(1))

    def send(self, kind, values=()):
        self.sender.send_bytes(kind + np.asarray(values, dtype="<c8").tobytes())

    def test_ready_then_contiguous_blocks_are_joined_without_gap(self):
        self.send(b"R"); self.send(b"I", [1, 2]); self.send(b"I", [3])
        np.testing.assert_array_equal(self.worker.read(self.guard), [1, 2, 3])
        self.assertTrue(self.worker.ready)
        self.assertFalse(self.worker.discontinuity)
        self.assertTrue(self.checks)

    def test_gap_marker_discards_older_blocks_and_reports_discontinuity(self):
        self.send(b"R"); self.send(b"I", [1, 2]); self.send(b"D", [5, 6]); self.send(b"I", [7])
        np.testing.assert_array_equal(self.worker.read(self.guard), [5, 6, 7])
        self.assertTrue(self.worker.discontinuity)
        self.send(b"I", [8])
        np.testing.assert_array_equal(self.worker.read(self.guard), [8])
        self.assertFalse(self.worker.discontinuity)

    def test_stale_backlog_keeps_only_the_newest_full_fft_window(self):
        self.send(b"R")
        for start in range(0, 8, 2):
            self.send(b"I", [start, start + 1])
        with patch.object(self.labrx, "MAX_FFT_SIZE", 4):
            np.testing.assert_array_equal(self.worker.read(self.guard), [4, 5, 6, 7])
        self.assertTrue(self.worker.discontinuity)

    def test_protocol_violations_fail_without_echoing_sample_bytes(self):
        self.send(b"I", [1 + 2j])  # a block before the ready handshake
        with self.assertRaisesRegex(OSError, "^Invalid RX worker message$"):
            self.worker.read(self.guard)
        self.send(b"R"); self.sender.send_bytes(b"Xsecret-sample-bytes")
        with self.assertRaisesRegex(OSError, "^Invalid RX worker message$"):
            self.worker.read(self.guard)
        self.sender.send_bytes(b"I" + b"\x00" * 7)
        with self.assertRaisesRegex(OSError, "complex64 block"):
            self.worker.read(self.guard)
        self.sender.send_bytes(b"Efixture driver error")
        with self.assertRaisesRegex(OSError, "^fixture driver error$"):
            self.worker.read(self.guard)

    def test_startup_deadline_is_separate_from_block_freshness(self):
        with patch.object(self.labrx, "STARTUP_TIMEOUT_S", .2):
            started = time.monotonic()
            with self.assertRaisesRegex(TimeoutError, "did not open"):
                self.worker.read(self.guard, timeout_s=.01)
            self.assertGreaterEqual(time.monotonic() - started, .2)
        self.send(b"R")
        with self.assertRaisesRegex(TimeoutError, "No fresh RX block"):
            self.worker.read(self.guard, timeout_s=.1)
        self.assertTrue(self.worker.ready)

    def test_close_waits_for_clean_worker_exit_before_signalling(self):
        for states, expected in (([True, False, False], [("join", .5)]),
                                 ([True] * 3, [("join", .5), "terminate", ("join", .5), "kill", ("join", .5)])):
            with self.subTest(expected=expected):
                events, alive = [], iter(states)
                self.worker.process = SimpleNamespace(is_alive=lambda: next(alive),
                    join=lambda timeout: events.append(("join", timeout)),
                    terminate=lambda: events.append("terminate"), kill=lambda: events.append("kill"))
                self.worker.close()
                self.assertTrue(self.reader.closed)
                self.assertEqual(events, expected)


class WorkerCorePrivacyTests(unittest.TestCase):
    def fake_prctl(self, *results):
        calls, values = [], iter(results)
        def invoke(*arguments):
            calls.append(arguments)
            return next(values)
        return SimpleNamespace(prctl=Function(invoke)), calls

    def test_core_guard_sets_limit_and_verifies_real_prctl_contract(self):
        from srrx.labrx import _disable_worker_core_dumps
        library, calls = self.fake_prctl(0, 0)
        with patch('srrx.labrx.sys.platform', 'linux'), \
             patch('srrx.labrx.resource.setrlimit') as limit:
            _disable_worker_core_dumps(libc=library)
            import resource
            limit.assert_called_once_with(resource.RLIMIT_CORE, (0, 0))
        self.assertEqual(calls, [(4, 0, 0, 0, 0), (3, 0, 0, 0, 0)])

    def test_failed_set_failed_get_and_still_dumpable_all_refuse(self):
        from srrx.labrx import _disable_worker_core_dumps
        for results in ((-1,), (0, -1), (0, 1)):
            with self.subTest(results=results):
                library, calls = self.fake_prctl(*results)
                with patch('srrx.labrx.sys.platform', 'linux'), \
                     patch('srrx.labrx.resource.setrlimit'), \
                     patch('srrx.labrx.C.get_errno', return_value=errno.EACCES):
                    with self.assertRaises(OSError) as raised:
                        _disable_worker_core_dumps(libc=library)
                self.assertEqual(len(calls), len(results))
                self.assertEqual(raised.exception.errno, errno.EPERM if results[-1] == 1 else errno.EACCES)

    def test_unsupported_platform_and_missing_prctl_refuse(self):
        from srrx.labrx import _disable_worker_core_dumps
        with patch('srrx.labrx.sys.platform', 'darwin'), \
             patch('srrx.labrx.resource.setrlimit') as limit:
            with self.assertRaises(OSError) as raised:
                _disable_worker_core_dumps(libc=SimpleNamespace())
            limit.assert_not_called()
        self.assertEqual(raised.exception.errno, errno.ENOSYS)
        with patch('srrx.labrx.sys.platform', 'linux'), patch('srrx.labrx.resource.setrlimit'):
            with self.assertRaises(OSError) as raised:
                _disable_worker_core_dumps(libc=SimpleNamespace())
        self.assertEqual(raised.exception.errno, errno.ENOSYS)

    def run_worker_boundary(self, guard_results, blocks=(), discontinuity=False, during_load=None):
        import srrx.labrx as labrx
        events, replies = [], []
        receiver = Mock()
        receiver.discontinuity = discontinuity
        pending = list(blocks)
        def read():
            events.append('read')
            if pending:
                return pending.pop(0)
            raise OSError('fixture read end')
        receiver.read.side_effect = read
        receiver.close.side_effect = lambda: events.append('close')
        connection = SimpleNamespace(send_bytes=replies.append, close=lambda: events.append('pipe_close'))
        results = iter(guard_results)
        def guard():
            events.append('guard')
            value = next(results)
            if isinstance(value, Exception):
                raise value
        def load(record, center_hz, sample_rate, *, loader):
            events.append('driver_load')
            if during_load is not None:
                during_load(path, loader)
            return receiver
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'fixture.so'
            path.write_bytes(b'hash-only unit fixture, never dlopen')
            record = {'backend':'rtl','library_path':str(path),'library_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            with patch.object(labrx, '_disable_worker_core_dumps', side_effect=guard), \
                 patch.object(labrx, 'RTLReceiver', side_effect=load):
                labrx._worker(connection, record, 100000000, 1024000)
        return events, replies, receiver

    def test_worker_privacy_guard_precedes_driver_load_and_first_read(self):
        events, replies, receiver = self.run_worker_boundary([None, None])
        self.assertEqual(events, ['guard','driver_load','guard','read','close','pipe_close'])
        self.assertEqual(replies[0], b'R')  # ready only after the post-init privacy check
        self.assertEqual(len(replies), 2)
        self.assertTrue(replies[1].startswith(b'E'))
        receiver.close.assert_called_once_with()

    def test_worker_marks_contiguous_and_discontinuous_blocks(self):
        block = np.array([1+2j, 3-4j], dtype=np.complex64)
        for discontinuity, kind in ((False, b'I'), (True, b'D')):
            with self.subTest(discontinuity=discontinuity):
                _, replies, _ = self.run_worker_boundary([None, None], [block], discontinuity)
                self.assertEqual(replies[1], kind + block.astype('<c8').tobytes())
                self.assertTrue(replies[2].startswith(b'E'))
        self.assertIs(RTLReceiver.discontinuity, True)  # independent read_sync blocks

    def test_driver_is_loaded_from_the_hashed_inode_even_if_the_path_is_swapped(self):
        observed = {}
        def swap_then_load(path, loader):
            hashed = path.stat().st_ino
            replacement = path.with_name('replacement.so')
            replacement.write_bytes(b'unreviewed replacement bytes')
            os.replace(replacement, path)  # attacker rename in a writable parent
            with patch('srrx.labrx.C.CDLL', side_effect=lambda name: name):
                name = loader(str(path))
            observed.update(hashed=hashed, swapped=path.stat().st_ino, loaded=os.stat(name).st_ino, name=name)
        events, _, _ = self.run_worker_boundary([None, None], during_load=swap_then_load)
        self.assertIn('driver_load', events)
        self.assertTrue(observed['name'].startswith('/proc/self/fd/'))
        self.assertEqual(observed['loaded'], observed['hashed'])
        self.assertNotEqual(observed['loaded'], observed['swapped'])

    def test_symlinked_or_changed_driver_never_loads(self):
        import srrx.labrx as labrx
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)/'real.so'
            target.write_bytes(b'fixture')
            link = Path(temporary)/'link.so'
            link.symlink_to(target)
            digest = hashlib.sha256(b'fixture').hexdigest()
            for path, sha in ((link, digest), (target, '0' * 64)):
                with self.subTest(path=path.name):
                    replies = []
                    connection = SimpleNamespace(send_bytes=replies.append, close=lambda: None)
                    with patch.object(labrx, '_disable_worker_core_dumps'), \
                         patch.object(labrx, 'RTLReceiver') as driver:
                        labrx._worker(connection, {'backend':'rtl','library_path':str(path),'library_sha256':sha},
                                      100000000, 1024000)
                    driver.assert_not_called()
                    self.assertEqual(len(replies), 1)
                    self.assertTrue(replies[0].startswith(b'E'))

    def test_preload_privacy_failure_never_opens_driver(self):
        events, replies, receiver = self.run_worker_boundary([OSError('privacy unavailable')])
        self.assertEqual(events, ['guard','pipe_close'])
        receiver.read.assert_not_called()
        receiver.close.assert_not_called()
        self.assertTrue(replies[0].startswith(b'E'))

    def test_post_init_privacy_failure_closes_driver_without_reading(self):
        events, replies, receiver = self.run_worker_boundary([None,OSError('privacy reset by initialization')])
        self.assertEqual(events, ['guard','driver_load','guard','close','pipe_close'])
        receiver.read.assert_not_called()
        receiver.close.assert_called_once_with()
        self.assertTrue(replies[0].startswith(b'E'))

    def test_parent_privacy_failure_never_observes_control_opens_source_or_writes_output(self):
        import srrx.labrx as labrx
        from unittest.mock import Mock
        transport, source = Mock(), Mock()
        with tempfile.TemporaryDirectory() as temporary:
            output, survey = Path(temporary)/'spectrum.json', Path(temporary)/'survey.jsonl'
            with patch.object(labrx, '_disable_worker_core_dumps', side_effect=OSError('privacy unavailable')), \
                 patch.object(labrx, 'ControlGuard') as guard:
                with self.assertRaisesRegex(OSError, 'privacy unavailable'):
                    labrx.run_capture(frames=1, output=output, survey=survey,
                        record={'backend':'rtl','branch':'RTLA'}, transport=transport, source_factory=source)
                guard.assert_not_called()
            transport.assert_not_called()
            source.assert_not_called()
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_simulation_does_not_change_parent_dumpability(self):
        import srrx.labrx as labrx
        with patch.object(labrx, '_disable_worker_core_dumps') as privacy:
            result = labrx.run_capture(fft_size=64, frames=1)
        privacy.assert_not_called()
        self.assertEqual(result['source'], 'SIMULATION')

    @unittest.skipUnless(sys.platform == 'linux', 'Actual process dumpability requires Linux')
    def test_real_capture_parent_is_nondumpable_before_source_and_remains_so_after_cleanup(self):
        # This fresh subprocess uses an in-memory guard/source fixture. It opens
        # no device, invents no accepted status/record, and saves no sample/frame.
        code = textwrap.dedent('''
            import ctypes as C
            import json
            from unittest.mock import patch
            import numpy as np
            import srrx.labrx as labrx
            runtime=C.CDLL(None, use_errno=True)
            runtime.prctl.argtypes=[C.c_int,C.c_ulong,C.c_ulong,C.c_ulong,C.c_ulong]
            runtime.prctl.restype=C.c_int
            def dumpable():
                value=runtime.prctl(3,0,0,0,0)
                if value < 0: raise OSError(C.get_errno(), 'PR_GET_DUMPABLE failed')
                return value
            observations={'before':dumpable()}
            calls=[]
            class FixtureGuard:
                def __init__(self,transport,branch):
                    assert branch=='RTLA'
                    observations['guard']=dumpable()
                def check(self):
                    return {'scope':'parent-privacy-fixture-no-hardware-status'}
            class FixtureSource:
                def __init__(self,*arguments): observations['constructor']=dumpable()
                def read(self,guard):
                    guard.check()
                    observations['read']=dumpable()
                    return np.ones(64,dtype=np.complex64)
                def close(self): observations['close']=dumpable()
            def transport(request):
                calls.append(request)
                return {'ok':True,'scope':'component-fixture-command-observed-only'}
            with patch.object(labrx,'ControlGuard',FixtureGuard):
                labrx.run_capture(fft_size=64,frames=1,
                    record={'backend':'rtl','branch':'RTLA'},transport=transport,source_factory=FixtureSource)
            observations['after']=dumpable()
            print(json.dumps({'scope':'native-parent-privacy-fixture-no-devices-no-files',
                'observations':observations,'cleanup_commands':calls,'physical_receiver_tested':False}))
        ''')
        project=Path(__file__).resolve().parents[2]
        result=subprocess.run([sys.executable,'-c',code],cwd=project,capture_output=True,text=True,timeout=90,
            env=dict(os.environ,PYTHONPATH=str(project/'software'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        observed=json.loads(result.stdout)
        self.assertFalse(observed['physical_receiver_tested'])
        self.assertEqual({key:value for key,value in observed['observations'].items() if key!='before'},
                         {'guard':0,'constructor':0,'read':0,'close':0,'after':0})
        self.assertEqual(observed['cleanup_commands'],[{'op':'control','name':'EN_RTLA','value':False}])
