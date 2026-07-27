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

    def test_split_keeps_headers_and_data(self) -> None:
        # mix: one blob + already-single DATA — must not drop DATA
        blob = _frame(0x4, b"\x00" * 6) + _frame(0x1, b"\x82\x84", 1)
        single_data = _frame(0x0, b"<html>hi", 1)
        result = split_http2_frames([blob, single_data])
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result[0], "http2_frames")
        deep = http2_deep(result[1])
        self.assertIn("HEADERS", deep["frames"])
        self.assertIn("DATA", deep["frames"])

    def test_no_recursive_resplit(self) -> None:
        frames = [_frame(0x4, b"\x00" * 6), _frame(0x1, b"\x82\x84", 1), _frame(0x0, b"<html>hi", 1)]
        result = split_http2_frames(frames)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result[0], "http2_data")
        self.assertEqual(result[1][0], b"<html>hi")
        self.assertIsNone(split_http2_frames(result[1]))


if __name__ == "__main__":
    unittest.main()
