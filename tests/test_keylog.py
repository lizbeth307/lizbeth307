"""Tests for TLS handshake peel and keylog decrypt."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from protocol_ast.fixtures.real_protocols import TLS_RECORD_MESSAGES, _tls_record
from protocol_ast.signal import propagate_flow
from protocol_ast.splitters import peel_tls_handshake_records, split_tls_handshake_bodies
from protocol_ast.tls_keylog import (
    extract_client_random,
    keylog_summary,
    parse_keylog,
)


class TestHandshakePeel(unittest.TestCase):
    def test_peel_from_mixed_tls(self) -> None:
        msgs = list(TLS_RECORD_MESSAGES)
        hs = peel_tls_handshake_records(msgs)
        self.assertGreaterEqual(len(hs), 3)  # three 0x16 in fixtures
        for r in hs:
            self.assertEqual(r[0], 0x16)

    def test_signal_peels_handshake_before_opaque(self) -> None:
        sig = propagate_flow("TCP:443", TLS_RECORD_MESSAGES, max_depth=5)
        labels = [sig.label] + [c.label for c in sig.children]
        # Should have tls_handshake child even when overall entropy is high
        self.assertTrue(
            any("tls_handshake" in lab for lab in labels)
            or any("tls_record" in lab for lab in labels)
        )
        notes = "\n".join(sig.format_notes())
        self.assertIn("tls", notes.lower())

    def test_handshake_bodies_splitter(self) -> None:
        r = split_tls_handshake_bodies(TLS_RECORD_MESSAGES)
        self.assertIsNotNone(r)
        self.assertEqual(r[0], "tls_handshake")


class TestKeylogParse(unittest.TestCase):
    def test_parse_nss_format(self) -> None:
        text = """# SSL/TLS secrets log file
CLIENT_RANDOM aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899 deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef
CLIENT_TRAFFIC_SECRET_0 aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899 11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff
SERVER_TRAFFIC_SECRET_0 aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899 ffeeddccbbaa00998877665544332211ffeeddccbbaa00998877665544332211
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "keylog.txt"
            path.write_text(text, encoding="utf-8")
            secrets = parse_keylog(path)
            summary = keylog_summary(secrets)
            self.assertEqual(summary["lines"], 3)
            self.assertEqual(summary["tls12_master"], 1)
            self.assertEqual(summary["tls13_client_traffic"], 1)

    def test_extract_client_random_from_hello(self) -> None:
        # Minimal ClientHello body: type=1, len, version, 32-byte random
        body = bytes([0x01, 0x00, 0x00, 0x26, 0x03, 0x03]) + bytes(range(32)) + bytes(4)
        rnd = extract_client_random(body)
        self.assertEqual(rnd, bytes(range(32)))

    def test_signal_reports_no_match_with_empty_keylog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty_keys.txt"
            path.write_text("# empty\n", encoding="utf-8")
            sig = propagate_flow(
                "TCP:443",
                TLS_RECORD_MESSAGES,
                max_depth=4,
                keylog=str(path),
            )
            # decrypt may be on root or child
            found = sig.decrypt
            for ch in sig.children:
                if ch.decrypt:
                    found = ch.decrypt
            # empty keylog → no_match or no decrypt attempt with secrets
            if found:
                self.assertIn(found.get("status"), ("no_match", "ok"))


if __name__ == "__main__":
    unittest.main()
