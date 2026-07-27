"""Protobuf / MessagePack peel tests."""

from __future__ import annotations

import unittest

from protocol_ast.binary_peel import (
    looks_like_msgpack,
    looks_like_protobuf,
    msgpack_deep,
    parse_protobuf_fields,
    protobuf_deep,
)
from protocol_ast.signal import Signal


def _pb_varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _pb_key(field: int, wire: int) -> bytes:
    return _pb_varint((field << 3) | wire)


class TestProtobuf(unittest.TestCase):
    def test_parse_simple_message(self) -> None:
        # field 1 varint=42, field 2 string="hi"
        msg = _pb_key(1, 0) + _pb_varint(42) + _pb_key(2, 2) + _pb_varint(2) + b"hi"
        fields = parse_protobuf_fields(msg)
        self.assertEqual(fields[0]["field"], 1)
        self.assertEqual(fields[0]["wire"], "varint")
        self.assertEqual(fields[0]["value"], 42)
        self.assertEqual(fields[1]["field"], 2)
        self.assertEqual(fields[1]["kind"], "string")
        self.assertEqual(fields[1]["text"], "hi")

    def test_looks_and_deep(self) -> None:
        msgs = []
        for i in range(3):
            msgs.append(
                _pb_key(1, 0)
                + _pb_varint(i)
                + _pb_key(2, 2)
                + _pb_varint(4)
                + f"id{i}".encode()
                + _pb_key(3, 0)
                + _pb_varint(1)
            )
        self.assertTrue(looks_like_protobuf(msgs))
        deep = protobuf_deep(msgs)
        self.assertEqual(deep["kind"], "protobuf")
        self.assertGreaterEqual(deep["field_count"], 2)

    def test_signal_peel(self) -> None:
        msgs = [
            _pb_key(1, 0) + _pb_varint(7) + _pb_key(2, 2) + _pb_varint(3) + b"abc",
            _pb_key(1, 0) + _pb_varint(8) + _pb_key(2, 2) + _pb_varint(3) + b"def",
            _pb_key(1, 0) + _pb_varint(9) + _pb_key(2, 2) + _pb_varint(3) + b"ghi",
        ]
        sig = Signal(label="TCP:5222/payload", messages=msgs, flow="TCP:5222", depth=1)
        sig.entropy = "high"
        sig.propagate(max_depth=3)
        notes = "\n".join(sig.format_notes())
        self.assertIn("protobuf", notes)


class TestMsgpack(unittest.TestCase):
    def test_fixmap(self) -> None:
        # fixmap 2: "a"->1, "b"->"x"
        raw = bytes([0x82, 0xA1, ord("a"), 0x01, 0xA1, ord("b"), 0xA1, ord("x")])
        self.assertTrue(looks_like_msgpack([raw, raw, raw]))
        deep = msgpack_deep([raw, raw])
        self.assertEqual(deep["kind"], "msgpack")
        self.assertGreaterEqual(deep["parsed"], 1)
        self.assertTrue(any(k.startswith("a") or k == "a" for k in deep["keys"]))


if __name__ == "__main__":
    unittest.main()
