"""Tests for Signal pipeline (P4)."""

from __future__ import annotations

import unittest

from protocol_ast.fixtures.real_protocols import DNS_MESSAGES, TLS_RECORD_MESSAGES
from protocol_ast.signal import Signal, propagate_flow
from protocol_ast.splitters import discover_splitter, split_quic_packets


class TestSplitters(unittest.TestCase):
    def test_length_prefixed_dns_not_quic(self) -> None:
        r = split_quic_packets(DNS_MESSAGES[:5])
        self.assertIsNone(r)

    def test_tls_records_split(self) -> None:
        r = discover_splitter(TLS_RECORD_MESSAGES[:8], depth=0)
        self.assertIsNotNone(r)
        self.assertIn("tls", r[0])


class TestSignal(unittest.TestCase):
    def test_propagate_dns(self) -> None:
        sig = propagate_flow("UDP:53", DNS_MESSAGES[:10], max_depth=4)
        self.assertGreater(sig.parse_success, 0.5)
        self.assertGreater(sig.sequitur_rules, 0)
        notes = sig.format_notes()
        self.assertTrue(any("d0" in n for n in notes))

    def test_propagate_tls(self) -> None:
        sig = propagate_flow("TCP:443", TLS_RECORD_MESSAGES[:12], max_depth=5)
        self.assertTrue(sig.splitter or sig.children or sig.parse_success > 0)

    def test_handshake_does_not_recurse(self) -> None:
        sig = propagate_flow("TCP:443", TLS_RECORD_MESSAGES[:12], max_depth=5)
        path = sig.path()
        # walk children paths via notes / labels
        labels: list[str] = []

        def walk(n: Signal) -> None:
            labels.append(n.label)
            for c in n.children:
                walk(c)

        walk(sig)
        nested = [l for l in labels if l.count("tls_handshake") >= 2]
        self.assertEqual(nested, [], msg=f"handshake recurse: {nested}")

    def test_opaque_wall_on_random(self) -> None:
        import os

        junk = [os.urandom(64) for _ in range(5)]
        child = Signal(label="junk/payload", messages=junk, depth=1, flow="TCP:9999")
        child.propagate(max_depth=3)
        self.assertEqual(child.entropy, "high")

    def test_to_dict_roundtrip(self) -> None:
        sig = propagate_flow("UDP:53", DNS_MESSAGES[:6], max_depth=3)
        d = sig.to_dict()
        self.assertIn("sequitur", d)
        self.assertIn("confidence", d)


if __name__ == "__main__":
    unittest.main()
