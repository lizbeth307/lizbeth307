"""RX worker startup budget and driver-library trust: harness and bench contracts.

Review findings RX-02/RX-02b/RX-10. No receiver, USB or RF is used: the bench
script runs here only with an in-memory worker stand-in.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import types
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
LINUX = sys.platform == "linux"


def load(name):
    spec = importlib.util.spec_from_file_location("srrx_lab_" + name, HERE / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rx, bench = load("rx_worker_smoke"), load("rx_startup_bench")
OFF = [{"op": "control", "name": "EN_RTLA", "value": False}]


class BudgetContractTests(unittest.TestCase):
    def test_within_budget_requires_a_measured_ready_inside_the_budget(self):
        name = "startup_within_production_budget"
        self.assertEqual(rx.budget_issues(name, None, 3.2, 10.0, 4.4), [])
        self.assertEqual(rx.budget_issues(name, None, 9.99, 10.0, 11.0), [])
        self.assertIn("Worker startup exceeded the production budget", rx.budget_issues(name, None, 10.0, 10.0, 11.0))
        self.assertIn("Worker never reported ready", rx.budget_issues(name, None, None, 10.0, 3.0))
        self.assertIn("Production startup failed: TimeoutError",
                      rx.budget_issues(name, TimeoutError("RX worker did not open the receiver within 10 s"), None, 10.0, 10.0))

    def test_exceeded_budget_must_time_out_from_spawn_within_one_second(self):
        name = "startup_budget_exceeded"
        error = TimeoutError("RX worker did not open the receiver within 10 s")
        self.assertEqual(rx.budget_issues(name, error, None, 10.0, 10.05), [])
        for elapsed in (9.9, 11.0, 30.0, None):
            with self.subTest(elapsed=elapsed):
                self.assertIn("Startup timeout did not fire within 1 s after the production budget",
                              rx.budget_issues(name, error, None, 10.0, elapsed))
        for wrong in (None, OSError("RX worker exited"), TimeoutError("No fresh RX block within one second")):
            with self.subTest(error=wrong):
                self.assertIn("Blocked driver open did not surface as the production startup TimeoutError",
                              rx.budget_issues(name, wrong, None, 10.0, 10.05))
        self.assertIn("Blocked driver open unexpectedly reported ready", rx.budget_issues(name, error, 2.0, 10.0, 10.05))
        self.assertTrue(rx.budget_issues("other", None, 1.0, 10.0, 1.0))

    def test_every_first_read_is_bounded_from_spawn_by_budget_and_one_read_deadline(self):
        # Measured per case (review RX-R2): a ready worker's read ends by ready + deadline < budget + deadline,
        # a never-ready one by the budget; 1 s slack as in the exceeded-budget window.
        self.assertEqual(rx.READ_SLACK_S, 1.0)
        for returned in (0.4, 10.05, 12.0):
            with self.subTest(returned=returned):
                self.assertEqual(rx.first_read_issues(returned, 10.0, 1.0), [])
        for late, deadline in ((12.01, 1.0), (30.0, 1.0), (11.6, 0.5)):
            with self.subTest(returned=late, deadline=deadline):
                self.assertEqual(rx.first_read_issues(late, 10.0, deadline),
                                 ["First read outlasted the production startup budget plus one read deadline"])
        self.assertEqual(rx.first_read_issues(None, 10.0, 1.0), ["First production read() did not run"])

    def test_untrusted_library_must_be_refused_before_dlopen(self):
        refused = OSError("Driver library must be a regular file of a trusted UID, without group/world write")
        self.assertEqual(rx.library_issues(refused, [], OFF), [])
        self.assertIn("Untrusted driver library was not refused", rx.library_issues(None, [], OFF))
        self.assertIn("Untrusted driver library was not refused", rx.library_issues(AssertionError("spectrum"), [], OFF))
        self.assertIn("Refusal did not come from the driver-library owner/mode check",
                      rx.library_issues(OSError("RX worker exited"), [], OFF))
        self.assertIn("Unclean public error type escaped run_capture: TypeError", rx.library_issues(TypeError("x"), [], OFF))
        for line in ("LOADED", "OPEN", "READ"):
            with self.subTest(marker=line):
                self.assertIn("Untrusted driver library was loaded", rx.library_issues(refused, [line], OFF))
        self.assertIn("Capture cleanup did not request exactly branch OFF", rx.library_issues(refused, [], []))

    def test_harness_never_sets_the_production_budget_or_trust(self):
        source = (HERE / "rx_worker_smoke.py").read_text(encoding="utf-8")
        for pattern in (r"STARTUP_TIMEOUT_S\s*=[^=]", r"['\"]STARTUP_TIMEOUT_S['\"]", r"TRUSTED_LIBRARY_UIDS\s*=[^=]",
                        r"--startup-timeout", r"pre.ready.wait"):
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, source))
        self.assertIn("budget=labrx.STARTUP_TIMEOUT_S", source)
        self.assertNotIn("production_budget_enforced", source)  # was true whenever a worker existed
        names = [name for name, _, _, _ in rx.CASES]
        for name in ("startup_within_production_budget", "startup_budget_exceeded",
                     "library_not_trusted_owner", "library_group_writable"):
            self.assertIn(name, names)
        self.assertEqual(sum(runs for _, _, _, runs in rx.CASES), 11)

    @unittest.skipUnless(LINUX and shutil.which("cc"), "native C compiler and Linux worker required")
    def test_production_budget_report_schema_on_a_native_subset(self):
        # Fresh interpreter: the spawn worker must not re-import this test runner.
        code = textwrap.dedent('''
            import importlib.util, sys
            spec = importlib.util.spec_from_file_location('srrx_rx_subset', sys.argv[1])
            smoke = importlib.util.module_from_spec(spec); spec.loader.exec_module(smoke)
            smoke.CASES = (('valid_even_short_read', 5, 'short_read', 1), ('library_group_writable', 5, 'untrusted', 1))
            raise SystemExit(smoke.main(['--project', sys.argv[2]]))
        ''')
        result = subprocess.run([sys.executable, "-c", code, str(HERE / "rx_worker_smoke.py"), str(PROJECT)],
                                capture_output=True, text=True, timeout=180,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OPENBLAS_NUM_THREADS="1"))
        self.assertEqual(result.returncode, 0, result.stdout[-3000:] + result.stderr[-2000:])
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["production_startup_budget_s"], 10.0)
        self.assertEqual(report["production_trusted_library_uids"], [0])
        self.assertNotIn("startup_deadline_s", report)
        self.assertFalse(report["raw_iq_persisted"] or report["physical_receiver_tested"])
        short, refused = report["cases"]
        for case in report["cases"]:
            self.assertEqual((case["first_read_bound_s"], case["first_read_within_bound"]), (12.0, True))
            self.assertLessEqual(case["first_read_returned_after_s"], case["first_read_bound_s"])
        self.assertTrue(0 < short["ready_after_s"] < 10.0 and short["library_loaded"])
        self.assertAlmostEqual(short["budget_margin_s"], 10.0 - short["ready_after_s"], places=2)
        self.assertEqual((refused["library_loaded"], refused["native_read_entered"], refused["library_mode"]),
                         (False, False, "0o664"))
        self.assertIn("trusted UID", refused["exception"])


class BenchScriptTests(unittest.TestCase):
    def args(self, **changes):
        values = {"--backend": "rtl", "--branch": "RTLA", "--serial": "00000307",
                  "--library-path": "/opt/srrx-vendor/lib/librtlsdr.so.2.0.2", "--library-sha256": "a" * 64,
                  "--condition": "warm", "--runs": "3"}
        values.update(changes)
        return [item for key, value in values.items() if value is not None for item in (key, value)]

    def test_arguments_are_receive_only_and_validated_before_any_open(self):
        parsed = bench.parse_args(self.args())
        self.assertEqual((parsed.sample_rate, parsed.center_hz, parsed.runs), (1024000, 100000000, 3))
        self.assertEqual(bench.parse_args(self.args(**{"--backend": "airspyhf", "--branch": "HFP",
                                                       "--serial": "3b52ab5dac5d3d6c"})).sample_rate, 768000)
        bad = ({"--branch": "HFP"}, {"--backend": "airspyhf", "--branch": "HFP"}, {"--backend": "lime"},
               {"--serial": "x"}, {"--library-sha256": "A" * 64}, {"--runs": "0"}, {"--runs": "101"},
               {"--condition": "cold"}, {"--condition": None}, {"--library-path": None})
        for change in bad:
            with self.subTest(change=change), contextlib.redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit):
                bench.parse_args(self.args(**change))
        self.assertEqual(bench.parse_args(self.args(**{"--condition": "cold", "--runs": "1"})).runs, 1)
        source = (HERE / "rx_startup_bench.py").read_text(encoding="utf-8")
        # Only the production receivers bindings (bias OFF) are used: no direct C call, override or acceptance file.
        for forbidden in ("ctypes", "cdll", "bias_tee", "eeprom", "--trusted", "trusted_library_uids",
                          "load_acceptance", "acceptance.json"):
            self.assertNotIn(forbidden, source.lower())
        # The one environment use is the bytecode opt-out the spawn worker inherits; nothing is read from it.
        self.assertEqual([line.strip() for line in source.splitlines() if "environ" in line.lower()],
                         ['os.environ["PYTHONDONTWRITEBYTECODE"] = "1"'])

    def run_main(self, argv, worker=None):
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(out):
            cwd = os.getcwd()
            os.chdir(temporary)
            try:
                # main() turns bytecode off for itself and its spawn worker; restore both here.
                patches = [mock.patch("srrx.labrx._disable_worker_core_dumps"), mock.patch.dict(os.environ),
                           mock.patch.object(sys, "dont_write_bytecode", sys.dont_write_bytecode)]
                if worker is not None:
                    patches += [mock.patch("srrx.labrx.WorkerSource", worker),
                                mock.patch("srrx.receivers.verify_library")]
                with contextlib.ExitStack() as stack:
                    for item in patches:
                        stack.enter_context(item)
                    code = bench.main(argv)
                    self.bytecode = (sys.dont_write_bytecode, os.environ.get("PYTHONDONTWRITEBYTECODE"))
                left = sorted(os.listdir(temporary))
            finally:
                os.chdir(cwd)
        return code, json.loads(out.getvalue()), left

    def test_untrusted_library_is_refused_and_no_worker_starts(self):
        with tempfile.TemporaryDirectory() as temporary:
            library = Path(temporary) / "librtlsdr.so.2.0.2"
            library.write_bytes(b"bench fixture, never loaded")
            library.chmod(0o666)  # refused for root and non-root alike
            digest = hashlib.sha256(library.read_bytes()).hexdigest()
            with mock.patch("srrx.labrx.WorkerSource") as worker:
                code, report, left = self.run_main(self.args(**{"--library-path": str(library), "--library-sha256": digest}))
            worker.assert_not_called()
        self.assertEqual((code, report["status"], report["physical_gate"]), (2, "REFUSED", "OPEN"))
        self.assertTrue(report["refusal"])
        self.assertEqual((report["runs"], left), ([], []))

    @unittest.skipUnless(LINUX, "the RX modules need Linux")
    def test_bench_writes_no_bytecode_into_the_project_tree(self):
        # Review RX-R3: a deployed /opt/srrx is verified against an exact file list.
        # A fresh interpreter without -B or PYTHONDONTWRITEBYTECODE imports srrx from a copy.
        code = textwrap.dedent('''
            import os, runpy, sys
            sys.argv, status = sys.argv[1:], None
            try:
                runpy.run_path(sys.argv[0], run_name='__main__')
            except SystemExit as exc:
                status = exc.code
            print(sys.dont_write_bytecode, os.environ.get('PYTHONDONTWRITEBYTECODE'),
                  sys.modules['srrx.labrx'].__file__, file=sys.stderr)
            raise SystemExit(status)
        ''')
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            shutil.copytree(PROJECT / "software" / "srrx", project / "software" / "srrx",
                            ignore=shutil.ignore_patterns("__pycache__"))
            library = Path(temporary) / "librtlsdr.so.2.0.2"
            library.write_bytes(b"bench fixture, never loaded")
            library.chmod(0o666)  # refused after the srrx imports, before any worker
            digest = hashlib.sha256(library.read_bytes()).hexdigest()
            env = {key: value for key, value in os.environ.items()
                   if key not in ("PYTHONDONTWRITEBYTECODE", "PYTHONPATH")}
            result = subprocess.run([sys.executable, "-c", code, str(HERE / "rx_startup_bench.py"),
                                     "--project", str(project)]
                                    + self.args(**{"--library-path": str(library), "--library-sha256": digest}),
                                    capture_output=True, text=True, timeout=120, env=env, cwd=temporary)
            self.assertEqual(result.returncode, 2, result.stdout[-2000:] + result.stderr[-2000:])
            self.assertEqual(json.loads(result.stdout)["status"], "REFUSED")
            flag, variable, labrx_file = result.stderr.split()[-3:]
            self.assertEqual((flag, variable), ("True", "1"))
            self.assertTrue(Path(labrx_file).is_relative_to(project.resolve()), labrx_file)
            self.assertEqual(sorted(str(path) for path in project.rglob("__pycache__")), [])

    def test_measurement_prints_json_only_and_keeps_the_gate_open(self):
        import numpy as np
        created = []
        class Worker:
            def __init__(self, record, center_hz, sample_rate):
                self.record, self.process = record, types.SimpleNamespace(exitcode=0)
                self.ready_after_s = (1.25, 2.5, 4.0)[len(created)]
                created.append(self)
            def read(self, guard):
                self.scope = guard.check()["scope"]
                return np.full(8192, 0.5 + 0.25j, dtype=np.complex64)
            def close(self):
                self.closed = True
        code, report, left = self.run_main(self.args(), Worker)
        self.assertEqual((code, report["status"], left), (0, "MEASURED", []))
        self.assertEqual(self.bytecode, (True, "1"))  # also for the spawn worker it would start
        self.assertEqual(report["ready_after_s"], {"count": 3, "min": 1.25, "p50": 2.5, "max": 4.0})
        self.assertIsNone(report["within_proposed_cold_limit"])  # warm runs are informative only
        self.assertEqual((report["gate"], report["physical_gate"], report["production_startup_budget_s"]),
                         ("E5-04", "OPEN", 10.0))
        for key in ("gate_status_changed", "labd_started", "branch_power_controlled", "acceptance_used",
                    "rf_transmitted", "raw_iq_persisted", "files_written"):
            self.assertIs(report[key], False, key)
        self.assertEqual([run["first_block_samples"] for run in report["runs"]], [8192] * 3)
        self.assertTrue(all(worker.closed and worker.scope == "bench-no-labd-no-branch-power" for worker in created))
        self.assertEqual(set(created[0].record), {"backend", "branch", "serial", "library_path", "library_sha256"})
        for run in report["runs"]:  # timing and a sample count only, never a sample value
            self.assertEqual(set(run), {"run", "ready_after_s", "first_block_samples", "error", "worker_exitcode"})
        self.assertNotIn("PASS", json.dumps(report))

    def test_cold_limit_is_reported_but_never_decides_the_gate(self):
        class Slow:
            def __init__(self, *arguments):
                self.process, self.ready_after_s = types.SimpleNamespace(exitcode=0), 6.5
            def read(self, guard):
                raise TimeoutError("No fresh RX block within one second")
            def close(self):
                pass
        code, report, _ = self.run_main(self.args(**{"--condition": "cold", "--runs": "1"}), Slow)
        self.assertEqual((code, report["status"], report["physical_gate"]), (1, "RUN_FAILED", "OPEN"))
        self.assertIsNone(report["within_proposed_cold_limit"])
        self.assertEqual(report["runs"][0]["error"], "TimeoutError: No fresh RX block within one second")
        class Cold(Slow):
            def read(self, guard):
                import numpy as np
                return np.zeros(4, dtype=np.complex64)
        code, report, _ = self.run_main(self.args(**{"--condition": "cold", "--runs": "1"}), Cold)
        self.assertEqual((code, report["status"], report["within_proposed_cold_limit"]), (0, "MEASURED", False))
        self.assertEqual(report["physical_gate"], "OPEN")


if __name__ == "__main__":
    unittest.main()
