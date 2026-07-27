"""Tests for P2: PCAPNG reader, IPv6, Wireshark Lua export."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from protocol_ast.fixtures.real_protocols import DNS_MESSAGES
from protocol_ast.pcap_analyze import extract_flows
from protocol_ast.pcap_build import ethernet_ipv4_udp, ethernet_ipv6_udp, write_pcap, write_pcapng
from protocol_ast.pcap_read import iter_packets
from protocol_ast.wireshark_export import format_to_lua


class TestPcapngReader(unittest.TestCase):
    def test_pcapng_extracts_dns_flow(self) -> None:
        frames = [
            ethernet_ipv4_udp((192, 168, 1, 10), (8, 8, 8, 8), 54321, 53, msg)
            for msg in DNS_MESSAGES[:5]
        ]
        with tempfile.TemporaryDirectory() as tmp:
            pcapng = Path(tmp) / "dns.pcapng"
            write_pcapng(pcapng, frames)
            packets = list(iter_packets(pcapng))
            self.assertEqual(len(packets), 5)
            flows = extract_flows(pcapng, min_packets=3, min_payload=12)
            self.assertTrue(any("UDP:53" in k for k in flows))


class TestIpv6Extract(unittest.TestCase):
    def test_ipv6_udp_flow(self) -> None:
        src = bytes.fromhex("20010db8000000000000000000000001")
        dst = bytes.fromhex("20010db8000000000000000000000002")
        frames = [
            ethernet_ipv6_udp(src, dst, 40000 + i, 53, msg)
            for i, msg in enumerate(DNS_MESSAGES[:4])
        ]
        with tempfile.TemporaryDirectory() as tmp:
            pcap = Path(tmp) / "dns6.pcap"
            write_pcap(pcap, frames)
            flows = extract_flows(pcap, min_packets=3, min_payload=12)
            self.assertTrue(any("UDP:53" in k for k in flows))


class TestWiresharkExport(unittest.TestCase):
    def test_generates_lua_dissector(self) -> None:
        fmt = {
            "endian": "be",
            "fields": [
                {"name": "type", "kind": "enum", "offset": 0},
                {"name": "length", "kind": "length", "offset": 3},
                {"name": "payload", "kind": "payload", "offset": 5},
            ],
        }
        lua = format_to_lua(fmt, flow="TCP:443")
        self.assertIn('Proto("discovered_tcp_443"', lua)
        self.assertIn('tcp.port"):add(443', lua)
        self.assertIn("function proto.dissector", lua)

    def test_truncates_fields(self) -> None:
        fmt = {
            "endian": "be",
            "fields": [{"name": f"f{i}", "kind": "fixed", "size": 1} for i in range(40)],
        }
        lua = format_to_lua(fmt, flow="TCP:5228")
        self.assertIn("truncated", lua)
        self.assertEqual(lua.count("ProtoField"), 32)


if __name__ == "__main__":
    unittest.main()
