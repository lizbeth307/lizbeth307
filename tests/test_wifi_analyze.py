"""Tests for PCAP extraction and wifi-analyze pipeline."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from protocol_ast.fixtures.real_protocols import DNS_MESSAGES
from protocol_ast.pcap_analyze import extract_flows
from protocol_ast.pcap_build import ethernet_ipv4_udp, write_pcap


ROOT = Path(__file__).resolve().parents[1]


class TestPcapExtract(unittest.TestCase):
    def test_extracts_dns_flow(self) -> None:
        frames = [
            ethernet_ipv4_udp((192, 168, 1, 10), (8, 8, 8, 8), 54321, 53, msg)
            for msg in DNS_MESSAGES[:5]
        ]
        with tempfile.TemporaryDirectory() as tmp:
            pcap = Path(tmp) / "dns.pcap"
            write_pcap(pcap, frames)
            flows = extract_flows(pcap, min_packets=3, min_payload=12)
            self.assertTrue(any("UDP:53" in k or "53" in k for k in flows))
            dns_key = next(k for k in flows if "53" in k)
            self.assertGreaterEqual(len(flows[dns_key].payloads), 3)


class TestWifiAnalyzeCli(unittest.TestCase):
    def test_wifi_analyze_on_synthetic_pcap(self) -> None:
        frames = [
            ethernet_ipv4_udp((10, 0, 0, 2), (10, 0, 0, 1), 40000 + i, 53, msg)
            for i, msg in enumerate(DNS_MESSAGES)
        ]
        with tempfile.TemporaryDirectory() as tmp:
            pcap = Path(tmp) / "wifi_dns.pcap"
            write_pcap(pcap, frames)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "discover_protocol_ast.py"),
                    "wifi-analyze",
                    str(pcap),
                    "--flow",
                    "53",
                    "--min-packets",
                    "3",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertIn("UDP:", proc.stdout)
            self.assertIn("parse:", proc.stdout)


if __name__ == "__main__":
    unittest.main()
