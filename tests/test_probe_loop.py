"""Probe loop adaptive targeting (offline unit tests)."""

from __future__ import annotations

import unittest
from unittest import mock

from protocol_ast.probe_loop import (
    _extract_findings,
    _hosts_from_findings,
    _next_targets,
    run_probe_loop,
)
from protocol_ast.signal import Signal


class TestProbeLoopHelpers(unittest.TestCase):
    def test_next_targets_from_tls_findings(self) -> None:
        findings = ["SNI: www.example.com", "ALPN: h2", "wall:opaque → PCAPdroid MITM"]
        targets = _next_targets(findings, 1)
        self.assertIn("tls", targets)

    def test_hosts_from_sni_and_api(self) -> None:
        findings = [
            "SNI: api.shop.pt",
            "api_paths: api.shop.pt/v1/ads, cdn.shop.pt/img/x",
            "hdr: s1 :authority=www.custojusto.pt :path=/",
        ]
        hosts = _hosts_from_findings(findings)
        self.assertIn("api.shop.pt", hosts)
        self.assertIn("www.custojusto.pt", hosts)

    def test_extract_findings_json_api(self) -> None:
        sig = Signal(label="x", messages=[b'{"a":1}', b'{"a":2}'], flow="TCP:443", depth=1)
        sig.deep = {
            "kind": "json_api",
            "bodies": 2,
            "field_count": 1,
            "paths": ["/v1"],
            "sample_keys": ["a"],
        }
        sig.entropy = "structured"
        found = _extract_findings(sig)
        self.assertTrue(any("json_api" in f for f in found))


class TestProbeLoopRun(unittest.TestCase):
    def test_run_loop_mocked(self) -> None:
        from protocol_ast.active_probe import ProbeMessage

        dns_msgs = [
            ProbeMessage("udp", "DNS:1.1.1.1", "request", b"\x00" * 12 + b"\x00"),
            ProbeMessage("udp", "DNS:1.1.1.1", "response", b"\x00" * 28),
        ]
        with mock.patch("protocol_ast.probe_loop._run_targets", return_value=dns_msgs):
            # Need enough messages for propagate — pad
            padded = dns_msgs + [
                ProbeMessage("udp", "DNS:1.1.1.1", "response", b"\x00" * 32),
                ProbeMessage("udp", "DNS:1.1.1.1", "response", b"\x00" * 40),
            ]
            with mock.patch("protocol_ast.probe_loop._run_targets", return_value=padded):
                report = run_probe_loop(rounds=2)
        self.assertEqual(len(report.rounds), 2)
        self.assertTrue(report.rounds[0].targets)


if __name__ == "__main__":
    unittest.main()
