"""Tests for P1: QUIC fix, TLS handshake, Kaitai export."""

from __future__ import annotations

import unittest

from protocol_ast.deep_decode import analyze_quic_flow, parse_quic_packet
from protocol_ast.fixtures.real_protocols import DNS_MESSAGES
from protocol_ast.kaitai_export import format_to_kaitai
from protocol_ast.tls_handshake import parse_client_hello


class TestQuicStrict(unittest.TestCase):
    def test_dns_not_quic_short(self) -> None:
        for msg in DNS_MESSAGES[:5]:
            self.assertIsNone(parse_quic_packet(msg, permit_short=False))

    def test_dns_analyze_low_parse_without_fake_short(self) -> None:
        r = analyze_quic_flow(DNS_MESSAGES)
        self.assertEqual(r.get("parsed", 0), 0)


class TestTlsHandshake(unittest.TestCase):
    def test_client_hello_from_phone(self) -> None:
        pcap = __import__("pathlib").Path("phone_capture.pcap")
        if not pcap.exists():
            self.skipTest("no pcap")
        from protocol_ast.pcap_analyze import extract_flows
        from protocol_ast.deep_decode import analyze_tls_flow

        buckets = extract_flows(pcap, min_packets=2, tcp_reassemble=True)
        r = analyze_tls_flow(buckets["TCP:443"].payloads)
        self.assertIn("alpn", r)
        self.assertGreater(len(r.get("sni_hosts", [])), 0)


class TestKaitaiExport(unittest.TestCase):
    def test_generates_ksy(self) -> None:
        fmt = {
            "endian": "be",
            "fields": [
                {"name": "type", "kind": "enum", "offset": 0},
                {"name": "length", "kind": "length", "offset": 3},
                {"name": "payload", "kind": "payload", "offset": 5},
            ],
        }
        ksy = format_to_kaitai(fmt, meta_id="tls_record")
        self.assertIn("id: tls_record", ksy)
        self.assertIn("endian: be", ksy)


if __name__ == "__main__":
    unittest.main()
