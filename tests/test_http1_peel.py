"""HTTP/1.1 + gzip peel after TLS decrypt (game APIs)."""

from __future__ import annotations

import unittest
import zlib

from protocol_ast.http2 import http1_body_messages, http1_deep, looks_like_http1


class TestHttp1Peel(unittest.TestCase):
    def test_post_and_gzip_response(self) -> None:
        req = (
            b"POST /pb/async?aid=104afd58-448f-4ab1-89f6-284b93427a8e HTTP/1.1\r\n"
            b"Host: app-global.lilithgame.com\r\n"
            b"Content-Type: application/x-protobuf\r\n"
            b"Content-Length: 5\r\n"
            b"\r\n"
            b"\x08\x96\x01\x10\x01"
        )
        # minimal protobuf-ish payload in body above
        gz_plain = b'{"ok":true,"n":1}'
        gz = zlib.compress(gz_plain, wbits=16 + zlib.MAX_WBITS)
        resp = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Length: " + str(len(gz)).encode() + b"\r\n"
            b"Connection: keep-alive\r\n"
            b"\r\n"
        )
        # body as next record (PCAPdroid / TLS record split)
        msgs = [req, b"\x01\x00", resp, gz]
        self.assertTrue(looks_like_http1(msgs))
        deep = http1_deep(msgs)
        self.assertEqual(deep["kind"], "http1")
        self.assertEqual(deep["methods"].get("POST"), 1)
        self.assertEqual(deep["methods"].get("RESPONSE"), 1)
        self.assertIn("app-global.lilithgame.com", deep["hosts"])
        self.assertTrue(any(r.get("path", "").startswith("/pb/async") for r in deep["requests"]))
        bodies = http1_body_messages(deep)
        self.assertTrue(any(b == gz_plain or b.startswith(b"\x08") for b in bodies))
        self.assertTrue(any(m.get("decompress") == "gzip" for m in deep["body_meta"]))


if __name__ == "__main__":
    unittest.main()
