#!/usr/bin/env python3
"""Run host-executable firmware/control regressions and preserve actual results."""
from pathlib import Path
import json
import sys
import time
import unittest
import os

# Set before test discovery, since optional test modules can load native runtimes.
os.environ["ORT_DISABLE_TELEMETRY"] = "1"

BASE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BASE / "software"), str(BASE), str(BASE / "firmware/pico")]


def inet_denied():
    """Probe this process itself; an inherited environment flag proves nothing."""
    import errno
    import socket
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            candidate = socket.socket(family, socket.SOCK_STREAM)
        except OSError as error:
            if error.errno != errno.EPERM:
                return False
        else:
            candidate.close()
            return False
    return True


def _open_progress(path, total, started):
    """Result class that appends one line per test class to path (the ARM64 guest passes its console),
    so a run stopped by the lab's time bound still shows how far it got. None: no progress output."""
    if not path:
        return None
    try:
        stream = open(path, "a", encoding="utf-8", buffering=1)
    except OSError:
        return None

    class ProgressResult(unittest.TextTestResult):
        current = None

        def startTest(self, test):
            group = type(test).__module__ + "." + type(test).__qualname__
            if group != ProgressResult.current:
                ProgressResult.current = group
                try:
                    stream.write("[srrx-regression] %d/%d %.0f s %s\n" % (self.testsRun, total, time.monotonic() - started, group))
                except OSError:
                    pass
            super().startTest(test)
    return ProgressResult


def main():
    started = time.monotonic()
    groups = {"software": unittest.TestLoader().discover(str(BASE / "software/tests"))}
    if (BASE / "deployment/tests").is_dir():
        groups["deployment"] = unittest.TestLoader().discover(str(BASE / "deployment/tests"))
    if (BASE / "deployment/linux_lab/test_guest_smoke.py").is_file():
        groups["linux_lab"] = unittest.TestLoader().discover(str(BASE / "deployment/linux_lab"), pattern="test_*.py")
    group_counts = {name: tests.countTestCases() for name, tests in groups.items()}
    suite = unittest.TestSuite(groups.values())
    progress = _open_progress(os.environ.get("SRRX_TEST_PROGRESS"), sum(group_counts.values()), started)
    # durations: the slowest tests close the log, so a slow emulated guest shows where its time went.
    result = unittest.TextTestRunner(verbosity=1, durations=25,
                                     resultclass=progress or unittest.TextTestResult).run(suite)
    from srrx.commissioning import project_hashes
    graphs, sources = project_hashes(BASE)
    report = {"host_regression_status": "PASS" if result.wasSuccessful() else "FAIL",
        "test_environment": {"internet_sockets_denied": inet_denied(),
                             "ort_disable_telemetry_preimport": os.environ.get("ORT_DISABLE_TELEMETRY") == "1"},
        "test_groups": group_counts,
        "tests_discovered": result.testsRun, "passed": result.testsRun - len(result.errors) - len(result.failures) - len(result.skipped),
        "failures": [{"test": str(t), "trace": s} for t, s in result.failures],
        "errors": [{"test": str(t), "trace": s} for t, s in result.errors],
        "skipped": [{"test": str(t), "reason": s} for t, s in result.skipped],
        "elapsed_s": round(time.monotonic() - started, 3),
        "graph_sha256": graphs, "source_sha256": sources,
        "device_flashed": False, "physical_tests_performed": False, "hardware_release": "BLOCKED"}
    (BASE / "verification/software-tests.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
