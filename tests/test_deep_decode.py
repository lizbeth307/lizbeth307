"""Tests for protocol_ast.deep_decode."""

from __future__ import annotations

import struct
import unittest
from pathlib import Path

from protocol_ast.deep_decode import (
    analyze_dns_flow,
    analyze_ntp_flow,
    analyze_quic_flow,
    analyze_tls_flow,
    analyze_xmpp_flow,
    deep_analyze_flow,
    parse_tls_sni,
)
from protocol_ast.fixtures.real_protocols import DNS_MESSAGES, NTP_MESSAGES


class TestDeepDecode(unittest.TestCase):
    def test_dns_domains(self) -> None:
        r = analyze_dns_flow(DNS_MESSAGES)
        self.assertEqual(r["kind"], "dns")
        self.assertGreater(r["parsed"], 0)
        self.assertIn("example.com", r["domains"])

    def test_ntp_fixed_48(self) -> None:
        r = analyze_ntp_flow(NTP_MESSAGES)
        self.assertEqual(r["kind"], "ntp")
        self.assertEqual(r["fixed_len"], 48)
        self.assertIn("client", r["modes"])

    def test_tls_sni_from_phone_capture(self) -> None:
        pcap = Path("phone_capture.pcap")
        if not pcap.exists():
            self.skipTest("phone_capture.pcap not present")
        from analyze_pcap import extract_flows

        flows = extract_flows(pcap)
        r = analyze_tls_flow(flows["TCP:443"])
        self.assertEqual(r["kind"], "tls")
        self.assertGreater(r["client_hellos"], 0)
        self.assertGreater(len(r["sni_hosts"]), 0)

    def test_quic_phone_capture(self) -> None:
        pcap = Path("phone_capture.pcap")
        if not pcap.exists():
            self.skipTest("phone_capture.pcap not present")
        from analyze_pcap import extract_flows

        flows = extract_flows(pcap)
        r = analyze_quic_flow(flows["UDP:443"])
        self.assertEqual(r["kind"], "quic")
        self.assertGreater(r["parsed"], 0)
        self.assertIn("QUIC v1", r["versions"])

    def test_dns_phone_not_quic(self) -> None:
        pcap = Path("phone_capture.pcap")
        if not pcap.exists():
            self.skipTest("phone_capture.pcap not present")
        from analyze_pcap import extract_flows

        flows = extract_flows(pcap)
        r = deep_analyze_flow("UDP:53", flows["UDP:53"])
        assert r is not None
        self.assertEqual(r["kind"], "dns")
        self.assertTrue(any("pool.ntp.org" in d for d in r["domains"]))

    def test_xmpp_phone(self) -> None:
        pcap = Path("phone_capture.pcap")
        if not pcap.exists():
            self.skipTest("phone_capture.pcap not present")
        from analyze_pcap import extract_flows

        flows = extract_flows(pcap)
        r = analyze_xmpp_flow(flows["TCP:5222"])
        self.assertEqual(r["kind"], "xmpp")
        self.assertGreater(r["protobuf_like"], 0)

    def test_parse_tls_sni_minimal(self) -> None:
        # ClientHello with SNI extension for "test.example"
        host = b"test.example"
        sni_ext = struct.pack(">H", len(host) + 5) + b"\x00" + struct.pack(">H", len(host)) + host
        ext_block = struct.pack(">HH", 0, len(sni_ext)) + sni_ext
        body = bytes([0x01, 0, 0, 0x40, 0x03, 0x03]) + bytes(32) + bytes([0])  # no session
        body += struct.pack(">H", 2) + bytes([0x00, 0x2F])  # one cipher
        body += bytes([1, 0])  # compression
        body += struct.pack(">H", len(ext_block)) + ext_block
        hosts = parse_tls_sni(body)
        self.assertIn("test.example", hosts)


if __name__ == "__main__":
    unittest.main()
