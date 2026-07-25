"""Tests for universal network probe."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestSmartProbe(unittest.TestCase):
    def test_active_probe_finds_dns(self) -> None:
        from protocol_ast.smart_probe import run_smart_probe

        report = run_smart_probe(capture=False, auto_pcap=False, active=True)
        labels = [f.flow for f in report.flows]
        self.assertTrue(any("DNS" in l for l in labels), labels)
        dns = next(f for f in report.flows if "DNS" in f.flow)
        self.assertGreaterEqual(dns.parse_success, 0.5)

    def test_cli_no_capture(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "probe_network.py"), "--no-capture", "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertIn("flows", data)
        self.assertGreater(len(data["flows"]), 0)


class TestProbeEnv(unittest.TestCase):
    def test_detect_runtime(self) -> None:
        from protocol_ast.probe_env import detect_runtime

        env = detect_runtime()
        self.assertIn(env.kind, ("android", "cloud", "desktop"))


if __name__ == "__main__":
    unittest.main()
