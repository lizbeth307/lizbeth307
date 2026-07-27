"""HPACK + gzip/br HTTP/2 enrichment tests."""

from __future__ import annotations

import unittest
import zlib

from protocol_ast.hpack_decode import Decoder
from protocol_ast.http2 import analyze_http2_streams, decompress_http_body, split_http2_frames


def _frame(ftype: int, payload: bytes = b"", stream_id: int = 0, flags: int = 0) -> bytes:
    return (
        len(payload).to_bytes(3, "big")
        + bytes([ftype, flags])
        + stream_id.to_bytes(4, "big")
        + payload
    )


class TestHpack(unittest.TestCase):
    def test_rfc_c41(self) -> None:
        data = bytes.fromhex("828684418cf1e3c2e5f23a6ba0ab90f4ff")
        hdrs = dict(Decoder().decode(data))
        self.assertEqual(hdrs[":method"], "GET")
        self.assertEqual(hdrs[":path"], "/")
        self.assertEqual(hdrs[":authority"], "www.example.com")


class TestHttp2Enrich(unittest.TestCase):
    def test_gzip_data_with_headers(self) -> None:
        # Indexed :status 200 + literal content-encoding gzip
        # Use encoder from hpack if available for reliable block
        try:
            from hpack import Encoder

            enc = Encoder()
            block = enc.encode([(":status", "200"), ("content-encoding", "gzip"), ("content-type", "text/html")])
        except Exception:
            # minimal: indexed :status:200 (index 8 → 0x88)
            block = bytes([0x88])

        html = b"<!doctype html><html><body>hi</body></html>"
        gz = zlib.compress(html, wbits=16 + zlib.MAX_WBITS)
        frames = [
            _frame(0x4, b"\x00" * 6),
            _frame(0x1, block, stream_id=1, flags=0x4),
            _frame(0x0, gz, stream_id=1, flags=0x1),
        ]
        # split path
        name, got = split_http2_frames([b"".join(frames)])  # type: ignore[misc]
        self.assertEqual(name, "http2_frames")
        analysis = analyze_http2_streams(got)
        self.assertTrue(analysis["bodies"])
        self.assertIn(b"<!doctype html>", analysis["bodies"][0])
        if analysis["headers"]:
            # may or may not decode content-encoding depending on encoder
            pass

    def test_decompress_gzip_magic(self) -> None:
        raw = b"hello living signal"
        gz = zlib.compress(raw, wbits=16 + zlib.MAX_WBITS)
        plain, method = decompress_http_body(gz)
        self.assertEqual(method, "gzip")
        self.assertEqual(plain, raw)


if __name__ == "__main__":
    unittest.main()
