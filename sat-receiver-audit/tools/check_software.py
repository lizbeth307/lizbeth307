#!/usr/bin/env python3
"""Run host-executable firmware/control regressions and preserve actual results."""
from pathlib import Path
import json
import sys
import time
import unittest

BASE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BASE / "software"), str(BASE), str(BASE / "firmware/pico")]


def main():
    started = time.monotonic()
    suite = unittest.defaultTestLoader.discover(str(BASE / "software/tests"))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    from srrx.commissioning import project_hashes
    graphs, sources = project_hashes(BASE)
    report = {"host_regression_status": "PASS" if result.wasSuccessful() else "FAIL",
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
