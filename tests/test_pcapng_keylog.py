"""Tests for pcapng DSB extraction and keylog auto-resolve."""

from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from protocol_ast.find_keylog import resolve_keylog
from protocol_ast.pcapng_secrets import extract_tls_keylog_from_pcapng, write_keylog_beside_capture


def _pcapng_with_dsb(keylog_text: str) -> bytes:
    """Minimal pcapng: SHB + DSB(TLSK)."""
    # Section Header Block
    # bom little-endian
    shb_body = struct.pack("<IHHi", 0x1A2B3C4D, 1, 0, -1)  # bom, maj, min, section_len
    shb_len = 8 + len(shb_body) + 4
    shb = struct.pack("<II", 0x0A0D0D0A, shb_len) + shb_body + struct.pack("<I", shb_len)

    secrets = keylog_text.encode("utf-8")
    # pad secrets to 4-byte boundary inside DSB body
    pad = (4 - (len(secrets) % 4)) % 4
    dsb_body = struct.pack("<II", 0x544C534B, len(secrets)) + secrets + (b"\x00" * pad)
    dsb_len = 8 + len(dsb_body) + 4
    dsb = struct.pack("<II", 0x0000000A, dsb_len) + dsb_body + struct.pack("<I", dsb_len)
    return shb + dsb


SAMPLE_KEYLOG = (
    "CLIENT_RANDOM aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899 "
    "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef\n"
    "CLIENT_TRAFFIC_SECRET_0 aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899 "
    "11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff\n"
)


class TestPcapngSecrets(unittest.TestCase):
    def test_extract_tlsk_dsb(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.pcapng"
            path.write_bytes(_pcapng_with_dsb(SAMPLE_KEYLOG))
            text = extract_tls_keylog_from_pcapng(path)
            self.assertIsNotNone(text)
            assert text is not None
            self.assertIn("CLIENT_RANDOM", text)
            self.assertIn("CLIENT_TRAFFIC_SECRET_0", text)

    def test_reject_plain_pcap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cap.pcap"
            path.write_bytes(struct.pack("<I", 0xA1B2C3D4) + b"\x00" * 20)
            self.assertIsNone(extract_tls_keylog_from_pcapng(path))

    def test_write_beside_capture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mitm.pcapng"
            path.write_bytes(_pcapng_with_dsb(SAMPLE_KEYLOG))
            out = write_keylog_beside_capture(path)
            self.assertIsNotNone(out)
            assert out is not None
            self.assertEqual(out.name, "mitm.keylog")
            self.assertIn("CLIENT_RANDOM", out.read_text(encoding="utf-8"))


class TestResolveKeylog(unittest.TestCase):
    def test_explicit_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kl = Path(tmp) / "sslkeys.log"
            kl.write_text(SAMPLE_KEYLOG, encoding="utf-8")
            path, msg = resolve_keylog(str(kl))
            self.assertEqual(path, kl)
            self.assertIn("keylog", msg)

    def test_auto_from_pcapng_dsb(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pcap = Path(tmp) / "mitm.pcapng"
            pcap.write_bytes(_pcapng_with_dsb(SAMPLE_KEYLOG))
            path, msg = resolve_keylog("auto", pcap_path=pcap)
            self.assertIsNotNone(path)
            assert path is not None
            self.assertTrue(path.exists())
            self.assertIn("DSB", msg)

    def test_auto_sibling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pcap = Path(tmp) / "c.pcap"
            pcap.write_bytes(b"\x00" * 24)
            sib = Path(tmp) / "sslkeys.log"
            sib.write_text(SAMPLE_KEYLOG, encoding="utf-8")
            path, msg = resolve_keylog("auto", pcap_path=pcap)
            self.assertEqual(path, sib)
            self.assertTrue("поруч" in msg or "найновіший" in msg, msg)

    def test_missing_explicit(self) -> None:
        path, msg = resolve_keylog("/nonexistent/sslkeys.log")
        self.assertIsNone(path)
        self.assertIn("не знайдено", msg)


if __name__ == "__main__":
    unittest.main()
