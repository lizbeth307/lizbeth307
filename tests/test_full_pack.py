"""Tests for full-pack P0: TCP reassembly, clustering, blind v2."""

from __future__ import annotations

import struct
import unittest
from pathlib import Path

from protocol_ast.align import discover_format
from protocol_ast.blind_v2 import recursive_blind_analyze
from protocol_ast.cluster import cluster_messages, discover_clustered_formats
from protocol_ast.fixtures.real_protocols import TLS_RECORD_MESSAGES, _tls_record
from protocol_ast.stream_enrich import iter_tls_records
from protocol_ast.tcp_reassemble import TcpSubFlow, reassemble_tcp_payloads


class TestTcpReassemble(unittest.TestCase):
    def test_subflow_merge(self) -> None:
        sf = TcpSubFlow(443, 12345)
        sf.feed(1000, b"hello ")
        sf.feed(1006, b"world")
        self.assertEqual(sf.reassemble(), b"hello world")

    def test_tls_split_after_reasm(self) -> None:
        body = bytes(range(20))
        rec = _tls_record(0x16, 0x0301, body)
        chunks = [rec[:10], rec[10:]]
        segs = [(443, 1000, 1, chunks[0]), (443, 1000, 11, chunks[1])]
        out = reassemble_tcp_payloads(segs, tls_split=True)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], rec)

    def test_iter_tls_records(self) -> None:
        stream = b"".join(TLS_RECORD_MESSAGES[:3])
        recs = iter_tls_records(stream)
        self.assertGreaterEqual(len(recs), 2)


class TestCluster(unittest.TestCase):
    def test_cluster_by_type(self) -> None:
        msgs = [bytes([1, 0, 0, 4]) + b"aaaa", bytes([1, 0, 0, 3]) + b"bbb", bytes([2, 0, 0, 2]) + b"cc", bytes([2, 0, 0, 1]) + b"d"]
        c = cluster_messages(msgs, 0)
        self.assertIn(1, c)
        self.assertIn(2, c)
        self.assertEqual(len(c[1]), 2)

    def test_clustered_formats(self) -> None:
        msgs = [bytes([0x16, 0x03, 0x01]) + struct.pack(">H", 4) + b"abcd"] * 3
        r = discover_clustered_formats(msgs, 0)
        self.assertIn(0x16, r)


class TestBlindV2(unittest.TestCase):
    def test_recursive_tls(self) -> None:
        layer = recursive_blind_analyze("TCP:443", TLS_RECORD_MESSAGES, max_depth=3)
        self.assertGreaterEqual(layer.messages, 3)
        self.assertTrue(layer.children or layer.parse_success > 0)
        if layer.children:
            self.assertEqual(layer.splitter, "tls_record")

    def test_phone_capture_nested(self) -> None:
        pcap = Path("phone_capture.pcap")
        if not pcap.exists():
            self.skipTest("no phone_capture.pcap")
        from protocol_ast.pcap_analyze import extract_flows

        buckets = extract_flows(pcap, min_packets=2, tcp_reassemble=True)
        layer = recursive_blind_analyze("TCP:443", buckets["TCP:443"].payloads, max_depth=3)
        d = layer.to_dict()
        self.assertIn("format", d)
        self.assertTrue(layer.children or layer.deep)


class TestAlignU32(unittest.TestCase):
    def test_u32_length_discovery(self) -> None:
        msgs = [struct.pack("<I", 4) + b"test" for _ in range(5)]
        fmt = discover_format(msgs)
        self.assertEqual(fmt.length_width, "u32")
        self.assertEqual(fmt.length_field_offset, 0)


if __name__ == "__main__":
    unittest.main()
