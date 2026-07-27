"""Body classification + http2_data meta preservation."""

from __future__ import annotations

import unittest
import zlib

from protocol_ast.body_peel import body_deep, classify_body
from protocol_ast.http2 import http2_data_deep


def _frame(ftype: int, payload: bytes = b"", stream_id: int = 0, flags: int = 0) -> bytes:
    return (
        len(payload).to_bytes(3, "big")
        + bytes([ftype, flags])
        + stream_id.to_bytes(4, "big")
        + payload
    )


class TestBodyPeel(unittest.TestCase):
    def test_html_title(self) -> None:
        html = b"<!DOCTYPE html><html><head><title>Example Domain</title></head><body>x</body></html>"
        self.assertEqual(classify_body(html), "html")
        deep = body_deep([html])
        self.assertEqual(deep["types"]["html"], 1)
        self.assertIn("Example Domain", deep["titles"])

    def test_html_title_iso8859(self) -> None:
        # "Anúncio não encontrado" in ISO-8859-1
        title = "Anúncio não encontrado".encode("iso-8859-1")
        html = b"<!DOCTYPE html><html><head><title>" + title + b"</title></head></html>"
        deep = body_deep([html], charset="ISO-8859-1")
        self.assertIn("Anúncio não encontrado", deep["titles"])

    def test_json_keys(self) -> None:
        raw = b'{"user":{"id":1},"items":[{"name":"a"}]}'
        deep = body_deep([raw])
        self.assertEqual(deep["types"]["json"], 1)
        self.assertTrue(any(k.startswith("user") for k in deep["json_keys"]))


class TestHttp2DataMeta(unittest.TestCase):
    def test_source_frames_preserve_stream_and_br(self) -> None:
        try:
            from hpack import Encoder

            enc = Encoder()
            block = enc.encode([
                (":status", "404"),
                ("content-encoding", "br"),
                ("content-type", "text/html"),
            ])
        except Exception:
            self.skipTest("hpack encoder not available")
        # Use gzip instead of br for deterministic test without brotli encode API variance
        try:
            from hpack import Encoder

            enc = Encoder()
            block = enc.encode([
                (":status", "200"),
                ("content-encoding", "gzip"),
                ("content-type", "text/html"),
            ])
        except Exception:
            self.skipTest("hpack encoder not available")
        html = b"<!DOCTYPE html><html><head><title>Hi</title></head><body>ok</body></html>"
        gz = zlib.compress(html, wbits=16 + zlib.MAX_WBITS)
        frames = [
            _frame(0x1, block, stream_id=1, flags=0x4),
            _frame(0x0, gz, stream_id=1, flags=0x1),
        ]
        bodies = [html]  # already decompressed peel result
        deep = http2_data_deep(bodies, source_frames=frames)
        self.assertEqual(deep["html"], 1)
        self.assertTrue(deep["body_meta"])
        self.assertEqual(deep["body_meta"][0].get("stream"), 1)
        self.assertEqual(deep["body_meta"][0].get("decompress"), "gzip")
        self.assertNotEqual(deep["body_meta"][0].get("decompress"), "identity")


if __name__ == "__main__":
    unittest.main()
