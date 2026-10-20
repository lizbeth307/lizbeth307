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


def main():
    started = time.monotonic()
    groups = {"software": unittest.TestLoader().discover(str(BASE / "software/tests"))}
    if (BASE / "deployment/tests").is_dir():
        groups["deployment"] = unittest.TestLoader().discover(str(BASE / "deployment/tests"))
    group_counts = {name: tests.countTestCases() for name, tests in groups.items()}
    suite = unittest.TestSuite(groups.values())
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    from srrx.commissioning import project_hashes
    graphs, sources = project_hashes(BASE)
    report = {"host_regression_status": "PASS" if result.wasSuccessful() else "FAIL",
        "test_environment": {"internet_sockets_denied": os.environ.get("SRRX_TEST_INET_DENIED") == "1",
                             "ort_disable_telemetry_preimport": os.environ.get("ORT_DISABLE_TELEMETRY") == "1"},
        "test_groups": group_counts,
        "tests_discovered": result.testsRun, "passed": result.testsRun - len(result.errors) - len(result.failures) - len(result.skipped),
        "failures": [{"test": str(t), "trace": s} for t, s in result.failures],
        "errors": [{"test": str(t), "trace": s} for t, s in result.errors],
        "skipped": [{"test": str(t), "reason": s} for t, s in result.skipped],
        "elapsed_s": round(time.monotonic() - started, 3),
        "graph_sha256": graphs, "source_sha256": sources,
        "device_flashed": False, "physical_tests_performed": False, "hardware_release": "BLOCKED"}
    (BASE / "verification/software-tests.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
