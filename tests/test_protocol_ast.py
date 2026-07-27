"""Verification suite for on-the-fly protocol AST discovery."""

from __future__ import annotations

import unittest

from protocol_ast.align import discover_format
from protocol_ast.parser import parse_message
from protocol_ast.pipeline import discover_and_parse
from protocol_ast.sequitur import Sequitur
from protocol_ast.synthesize import TYPE_DATA, encode, make_corpus, raw_messages


class TestSynthesize(unittest.TestCase):
    def test_roundtrip_length_and_checksum(self):
        raw = encode(1, TYPE_DATA, 3, b"\x01\x02\x03\x04")
        # magic CA FE, ver, type, flags, len=4, payload, checksum
        self.assertEqual(raw[:2], b"\xfe\xca")
        self.assertEqual(raw[5] | (raw[6] << 8), 4)
        self.assertEqual(raw[-1], (1 + 2 + 3 + 4) & 0xFF)


class TestFormatDiscovery(unittest.TestCase):
    def test_recovers_length_and_payload(self):
        messages = raw_messages(make_corpus(50, seed=1))
        fmt = discover_format(messages)
        kinds = [f.kind for f in fmt.fields]
        self.assertIn("length", kinds)
        self.assertIn("payload", kinds)
        self.assertTrue(any(f.name == "checksum" for f in fmt.fields))
        # magic 0xCAFE at start should be a fixed field
        first = fmt.fields[0]
        self.assertEqual(first.kind, "fixed")
        self.assertEqual(first.offset, 0)

    def test_parse_all_corpus(self):
        corpus = make_corpus(60, seed=7)
        result = discover_and_parse(raw_messages(corpus))
        self.assertGreaterEqual(result.success_rate, 0.95)
        self.assertGreater(result.header_agreement, 0.5)

        for tree, truth in zip(result.trees, corpus):
            payload = next(c for c in tree.children if c.kind == "payload")
            self.assertEqual(payload.value, truth.payload)
            length = next(c for c in tree.children if c.kind == "length")
            self.assertEqual(length.value, len(truth.payload))


class TestSequitur(unittest.TestCase):
    def test_builds_rule_for_repeat(self):
        s = Sequitur()
        s.feed_many(list("abcdbc"))
        # digram 'b c' repeats → should introduce a rule
        self.assertGreaterEqual(len(s.rules), 2)
        self.assertEqual("".join(s.expand()), "abcdbc")


class TestOnlineRefine(unittest.TestCase):
    def test_incremental_messages_still_parse(self):
        """Simulate on-the-fly: discover on first batch, parse later batch."""
        batch1 = raw_messages(make_corpus(20, seed=3))
        batch2 = raw_messages(make_corpus(20, seed=99))
        fmt = discover_format(batch1)
        ok = 0
        for msg in batch2:
            tree = parse_message(msg, fmt)
            if tree.children:
                ok += 1
        self.assertEqual(ok, len(batch2))


if __name__ == "__main__":
    unittest.main()
