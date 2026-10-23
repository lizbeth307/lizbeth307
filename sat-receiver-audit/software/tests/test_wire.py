import json
import random
import unittest
from unittest.mock import patch

from srrx.wire import (
    FRAME_TYPES, MAX_FRAME_BYTES, UINT32_MAX, FrameDecoder,
    crc16_ccitt_false, encode_frame,
)


def frame(**changes):
    value = {"v": 1, "t": "HB", "s": 42, "q": 7, "p": {}}
    value.update(changes)
    return value


def raw_frame(body):
    if isinstance(body, str):
        body = body.encode("utf-8")
    return b"@" + body + ("|%04X\n" % crc16_ccitt_false(body)).encode("ascii")


class WireTests(unittest.TestCase):
    def test_known_crc_vector_and_empty(self):
        self.assertEqual(crc16_ccitt_false(b"123456789"), 0x29B1)
        self.assertEqual(crc16_ccitt_false(b""), 0xFFFF)

    def test_roundtrip_all_types_and_uint32_boundaries(self):
        for name in FRAME_TYPES:
            for value in (0, UINT32_MAX):
                message = frame(t=name, s=value, q=value)
                self.assertEqual(FrameDecoder().feed(encode_frame(message)), [message])

    def test_utf8_crc_is_over_transmitted_bytes(self):
        body = '{"v":1,"t":"EVENT","s":2,"q":3,"p":{"text":"Привіт 🛰 @ |"}}'
        expected = json.loads(body)
        wire = raw_frame(body)
        self.assertEqual(FrameDecoder().feed(wire), [expected])
        self.assertEqual(FrameDecoder().feed(encode_frame(expected)), [expected])

    def test_fragmentation_at_every_boundary(self):
        value = frame(p={"note": "a@b|c\nline2", "ok": True})
        wire = encode_frame(value)
        for cut in range(len(wire) + 1):
            decoder = FrameDecoder()
            self.assertEqual(decoder.feed(wire[:cut]) + decoder.feed(wire[cut:]), [value])
            self.assertEqual(decoder.errors, 0)
            self.assertEqual(decoder.buffered_bytes, 0)

    def test_bytewise_and_concatenated_frames(self):
        values = [frame(q=i, t="STATUS", p={"at": "@", "nested": [{"q": i}]}) for i in range(8)]
        wire = b"".join(encode_frame(value) for value in values)
        self.assertEqual(FrameDecoder().feed(wire), values)
        decoder = FrameDecoder()
        received = []
        for byte in wire:
            received.extend(decoder.feed(bytes((byte,))))
        self.assertEqual(received, values)
        self.assertEqual(decoder.errors, 0)

    def test_crc_corruption_dropped_then_recovery(self):
        good = encode_frame(frame())
        damaged = bytearray(good)
        damaged[5] ^= 1
        decoder = FrameDecoder()
        self.assertEqual(decoder.feed(bytes(damaged) + good), [frame()])
        self.assertEqual(decoder.errors, 1)

    def test_hex_requires_exact_digits_accepts_lowercase(self):
        good = encode_frame(frame())
        self.assertEqual(FrameDecoder().feed(good[:-5] + good[-5:].lower()), [frame()])
        for trailer in (b"000\n", b"00000\n", b"+001\n", b"0x00\n", b"GGGG\n"):
            decoder = FrameDecoder()
            bad = good[:good.rfind(b"|") + 1] + trailer
            self.assertEqual(decoder.feed(bad), [])
            self.assertGreater(decoder.errors, 0)

    def test_exact_512_byte_limit(self):
        empty = frame(t="EVENT", p={"text": ""})
        spare = MAX_FRAME_BYTES - len(encode_frame(empty))
        value = frame(t="EVENT", p={"text": "x" * spare})
        wire = encode_frame(value)
        self.assertEqual(len(wire), 512)
        self.assertEqual(FrameDecoder().feed(wire), [value])
        with self.assertRaises(ValueError):
            encode_frame(frame(t="EVENT", p={"text": "x" * (spare + 1)}))

    def test_oversize_rejected_then_recovers_without_unbounded_buffer(self):
        decoder = FrameDecoder()
        decoder.feed(b"@" + b"x" * 10000)
        self.assertLessEqual(decoder.buffered_bytes, 511)
        self.assertGreater(decoder.errors, 0)
        self.assertEqual(decoder.feed(encode_frame(frame())), [frame()])
        self.assertEqual(decoder.buffered_bytes, 0)
        # A valid-CRC candidate above the frame size is still rejected.
        large = raw_frame(json.dumps(frame(p={"text": "x" * 600})))
        self.assertEqual(decoder.feed(large), [])
        self.assertEqual(decoder.feed(encode_frame(frame(q=8))), [frame(q=8)])

    def test_partial_exact_capacity_does_not_grow(self):
        decoder = FrameDecoder()
        decoder.feed(b"@" + b"x" * 510)
        self.assertEqual(decoder.buffered_bytes, 511)
        decoder.feed(b"y")
        self.assertEqual(decoder.buffered_bytes, 0)
        self.assertEqual(decoder.errors, 1)

    def test_noise_and_truncated_prefix_suffix_resync(self):
        decoder = FrameDecoder()
        good = encode_frame(frame())
        self.assertEqual(decoder.feed(b"noise\x00\xff" + good), [frame()])
        self.assertGreaterEqual(decoder.errors, 1)
        self.assertEqual(decoder.feed(b'@{"broken":"' + good), [frame()])
        self.assertEqual(decoder.buffered_bytes, 0)

    def test_suffix_recovery_crc_work_is_linear_per_line(self):
        crc_bytes = [0]
        def counting(data):
            crc_bytes[0] += len(data)
            return crc16_ccitt_false(data)
        decoder = FrameDecoder()
        with patch("srrx.wire.crc16_ccitt_false", side_effect=counting):
            # Hostile line: every byte is a candidate start sharing one trailer.
            self.assertEqual(decoder.feed(b"@" * 506 + b"|0000\n"), [])
            self.assertLessEqual(crc_bytes[0], 3 * MAX_FRAME_BYTES)
            # Truncated-prefix recovery with '@' inside the valid payload still works.
            good = encode_frame(frame(p={"note": "a@b@c@d"}))
            self.assertEqual(decoder.feed(b"@" + b"x" * 40 + good), [frame(p={"note": "a@b@c@d"})])
        self.assertEqual(decoder.buffered_bytes, 0)

    def test_suffix_recovery_budget_is_shared_by_every_line_of_one_feed(self):
        crc_bytes = [0]
        def counting(data):
            crc_bytes[0] += len(data)
            return crc16_ccitt_false(data)
        hostile = (b"@" * 40 + b"|0000\n") * 11  # One 506-byte UART read of short hostile lines.
        decoder = FrameDecoder()
        with patch("srrx.wire.crc16_ccitt_false", side_effect=counting):
            self.assertEqual(decoder.feed(hostile + encode_frame(frame())), [frame()])
            # First parses (<= the bytes fed) plus one shared 1024-byte suffix budget;
            # a per-line budget cost 8580 CRC bytes here.
            self.assertLessEqual(crc_bytes[0], len(hostile) + len(encode_frame(frame())) + 2 * MAX_FRAME_BYTES)
            crc_bytes[0] = 0
            # The budget is per feed(): the next read recovers a truncated prefix again.
            self.assertEqual(decoder.feed(b"@" + b"x" * 40 + encode_frame(frame())), [frame()])
        self.assertEqual(decoder.errors, 12)

    def test_invalid_utf8_and_json_recover(self):
        bad = [b'\xff', b'{', b'{}junk', b'[]', b'null',
               b'{"v":1,"t":"HB","s":0,"q":0,"p":{]}}']
        decoder = FrameDecoder()
        for body in bad:
            self.assertEqual(decoder.feed(raw_frame(body)), [])
        self.assertEqual(decoder.feed(encode_frame(frame())), [frame()])
        self.assertEqual(decoder.errors, len(bad))

    def test_invalid_utf8_forms_are_rejected_independently_of_json_runtime(self):
        invalid = [b"\xc0\x80", b"\xc1\xbf", b"\xed\xa0\x80", b"\xf4\x90\x80\x80",
                   b"\xf5\x80\x80\x80", b"\x80", b"\xc2", b"\xe0\x80\x80", b"\xe2\x28\xa1"]
        prefix = b'{"v":1,"t":"HB","s":0,"q":0,"p":{"text":"'
        decoder = FrameDecoder()
        for value in invalid:
            self.assertEqual(decoder.feed(raw_frame(prefix + value + b'"}}')), [])
        self.assertEqual(decoder.errors, len(invalid))
        self.assertEqual(decoder.feed(encode_frame(frame())), [frame()])

    def test_wrong_outer_names_types_and_versions(self):
        invalid = [frame(v=True), frame(v=2), frame(v=1.0), frame(t="NOPE"),
                   frame(t=1), frame(s=True), frame(s=-1), frame(s=UINT32_MAX + 1),
                   frame(q=False), frame(q=1.0), frame(q="1"), frame(p=[]),
                   frame(p=None), frame(extra=0)]
        missing = frame()
        del missing["p"]
        invalid.extend([missing, [], None])
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    encode_frame(value)
                decoder = FrameDecoder()
                self.assertEqual(decoder.feed(raw_frame(json.dumps(value))), [])
                self.assertEqual(decoder.errors, 1)

    def test_duplicate_keys_including_escaped_aliases(self):
        bodies = [
            '{"v":1,"v":1,"t":"HB","s":0,"q":0,"p":{}}',
            '{"v":1,"t":"HB","s":0,"s":1,"q":0,"p":{}}',
            '{"v":1,"t":"HB","s":0,"q":0,"p":{},"\\u0070":{}}',
            '{"v":1,"t":"HB","s":0,"q":0,"p":{"armed":false,"armed":true}}',
            '{"v":1,"t":"HB","s":0,"q":0,"p":{"nested":[{"a":1,"\\u0061":2}]}}',
        ]
        decoder = FrameDecoder()
        for body in bodies:
            self.assertEqual(decoder.feed(raw_frame(body)), [])
        self.assertEqual(decoder.errors, len(bodies))
        valid = frame(p={"text": '\\"{"v":"different"}', "x": {"q": 0}, "y": {"q": 1}})
        self.assertEqual(decoder.feed(encode_frame(valid)), [valid])

    def test_nonfinite_and_non_json_payloads(self):
        for payload in ({"x": float("nan")}, {"x": float("inf")},
                        {"x": -float("inf")}, {1: "nonstring key"},
                        {"x": (1, 2)}, {"x": b"bytes"}):
            with self.assertRaises(ValueError):
                encode_frame(frame(p=payload))
        for constant in ("NaN", "Infinity", "-Infinity"):
            decoder = FrameDecoder()
            body = '{"v":1,"t":"HB","s":0,"q":0,"p":{"x":' + constant + '}}'
            self.assertEqual(decoder.feed(raw_frame(body)), [])
            self.assertEqual(decoder.errors, 1)

    def test_huge_and_cyclic_encoder_input_is_rejected(self):
        values = [{"x": "x" * 100000}, {"x": [0] * 10000}, {"x": 10 ** 1000}]
        cycle = []
        cycle.append(cycle)
        values.append({"x": cycle})
        for value in values:
            with self.assertRaises(ValueError):
                encode_frame(frame(p=value))

    def test_decoder_does_not_enforce_session_or_sequence_order(self):
        values = [frame(s=99, q=UINT32_MAX), frame(s=99, q=0), frame(s=99, q=0), frame(s=2, q=0)]
        decoder = FrameDecoder()
        self.assertEqual(decoder.feed(b"".join(encode_frame(x) for x in values)), values)
        self.assertEqual(decoder.errors, 0)

    def test_reset_timeout_byteslike_and_bad_argument(self):
        decoder = FrameDecoder()
        decoder.feed(b"junk@part")
        before = decoder.errors
        decoder.reset()
        self.assertEqual(decoder.errors, before)
        self.assertEqual(decoder.buffered_bytes, 0)
        self.assertEqual(decoder.feed(None), [])
        self.assertEqual(decoder.feed("not bytes"), [])
        self.assertEqual(decoder.errors, before + 1)
        self.assertEqual(decoder.feed(bytearray(encode_frame(frame()))), [frame()])
        self.assertEqual(decoder.feed(memoryview(encode_frame(frame()))), [frame()])

    def test_crlf_and_raw_lf_are_not_valid_frames(self):
        good = encode_frame(frame())
        decoder = FrameDecoder()
        self.assertEqual(decoder.feed(good[:-1] + b"\r\n"), [])
        self.assertEqual(decoder.feed(b'@{"v":1,\n'), [])
        self.assertEqual(decoder.feed(good), [frame()])

    def test_random_noise_fragmentation_and_buffer_invariant(self):
        randomizer = random.Random(94713)
        decoder = FrameDecoder()
        for _ in range(200):
            noise = bytes(randomizer.randrange(256) for _ in range(randomizer.randrange(120)))
            decoder.feed(noise + b"\n")
            self.assertLessEqual(decoder.buffered_bytes, MAX_FRAME_BYTES - 1)
            value = frame(q=randomizer.randrange(UINT32_MAX + 1))
            wire = encode_frame(value)
            received = []
            while wire:
                take = randomizer.randrange(1, 13)
                received.extend(decoder.feed(wire[:take]))
                wire = wire[take:]
                self.assertLessEqual(decoder.buffered_bytes, MAX_FRAME_BYTES - 1)
            self.assertEqual(received, [value])

    def test_error_counter_saturates(self):
        decoder = FrameDecoder()
        decoder.errors = UINT32_MAX - 1
        decoder.feed(b"noise\nnoise\nnoise\n")
        self.assertEqual(decoder.errors, UINT32_MAX)


if __name__ == "__main__":
    unittest.main()
