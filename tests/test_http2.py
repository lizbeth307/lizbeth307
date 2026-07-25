"""HTTP/2 frame splitter tests."""

from __future__ import annotations

import unittest

from protocol_ast.http2 import HTTP2_PREFACE, http2_deep, split_http2_frames


def _frame(ftype: int, payload: bytes = b"", stream_id: int = 0) -> bytes:
    return (
        len(payload).to_bytes(3, "big")
        + bytes([ftype, 0])
        + stream_id.to_bytes(4, "big")
        + payload
    )


class TestHttp2(unittest.TestCase):
    def test_split_with_preface(self) -> None:
        blob = HTTP2_PREFACE + _frame(0x4, b"\x00" * 6) + _frame(0x8, b"\x00" * 4, 1)
        name, frames = split_http2_frames([blob])  # type: ignore[misc]
        self.assertEqual(name, "http2_frames")
        self.assertGreaterEqual(len(frames), 2)
        deep = http2_deep(frames)
        self.assertIn("SETTINGS", deep["frames"])

    def test_split_pure_frames(self) -> None:
        msgs = [_frame(0x4, b"\x00" * 6) + _frame(0x1, b"\x82\x84", 1), _frame(0x0, b"hi", 1)]
        result = split_http2_frames(msgs)
        self.assertIsNotNone(result)
        assert result is not None
        deep = http2_deep(result[1])
        self.assertGreaterEqual(deep["total_frames"], 2)


if __name__ == "__main__":
    unittest.main()
