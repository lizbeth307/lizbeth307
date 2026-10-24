"""egc-gate header tests on synthetic descriptors; not a verified Inmarsat-C decoder.

toy_verifier is a TEST FIXTURE (byte sum), deliberately not the unverified
Inmarsat-C descriptor checksum, which stays an injected algorithm.
"""
from pathlib import Path
import random
import unittest
from unittest import mock

from srrx import decoder_policy
from srrx import egc_gate as g
from srrx import scope_policy


def toy_sum(data):
    return sum(data) & 0xFFFF


def seal(head):
    value = toy_sum(head)
    return bytes(head) + bytes((value >> 8, value & 0xFF))


def toy_verifier(descriptor):
    return toy_sum(descriptor[:-2]) == (descriptor[-2] << 8 | descriptor[-1])


def medium(ptype, code, data=b"\x00"):
    length = 3 + len(data) + 2
    return seal(bytes((0x80 | ptype, length - 2, code)) + data)


def long_form(ptype, code, data=b"\x00"):
    length = 4 + len(data) + 2
    return seal(bytes((0xC0 | ptype, (length - 3) >> 8, (length - 3) & 0xFF, code)) + data)


def fragment(ptype, data, raw=None):
    return seal(bytes((raw if raw is not None else 0x80 | ptype, len(data) + 2)) + data)


class Spy:
    """Bytes-like packet recording every index/slice read."""
    def __init__(self, data):
        self.data, self.reads = bytes(data), []

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        self.reads.append(key)
        return self.data[key]


class Verifier:
    def __init__(self, result=None):
        self.calls, self.result = [], result

    def __call__(self, descriptor):
        self.calls.append(bytes(descriptor))
        return toy_verifier(descriptor) if self.result is None else self.result


def frames(assembler, *packets_per_frame, first=1):
    """begin_frame(n) for consecutive n, then that frame's descriptors; returns every feed() result."""
    out = []
    for number, packets in enumerate(packets_per_frame, first):
        assembler.begin_frame(number)
        out += [assembler.feed(packet) for packet in packets]
    return out


OTHER_CODES = sorted(set(range(256)) - g.SAFETYNET_SERVICE_CODES)


class ClassifierTests(unittest.TestCase):
    def test_every_safetynet_code_accepts_in_medium_and_long_form(self):
        self.assertEqual(len(g.SAFETYNET_SERVICE_CODES), 8)
        for code in sorted(g.SAFETYNET_SERVICE_CODES):
            for ptype in (0x30, 0x31, 0x32):
                for build, cls, raw in ((medium, g.MEDIUM, 0xB0), (long_form, g.LONG, 0xF0)):
                    packet = build(ptype, code, b"\x01\x02")
                    with self.subTest(code=code, ptype=ptype, cls=cls):
                        self.assertEqual(packet[0], raw + ptype - 0x30)
                        self.assertEqual(g.classify(packet), g.EgcDecision(
                            True, "ACCEPT_SAFETYNET", cls, ptype, code, len(packet)))

    def test_all_248_other_service_codes_reject_and_rejections_carry_no_header_values(self):
        self.assertEqual(len(OTHER_CODES), 248)
        for code in OTHER_CODES:
            expected = ("SYSTEM_SERVICE_CODE" if code in g.SYSTEM_SERVICE_CODES else
                        "FLEETNET_SERVICE_CODE" if code in g.FLEETNET_SERVICE_CODES else "SERVICE_CODE_NOT_SAFETYNET")
            for build in (medium, long_form):
                with self.subTest(code=code, form=build.__name__):
                    self.assertEqual(g.classify(build(0x31, code)), g.EgcDecision(False, expected))

    def test_system_and_fleetnet_codes_are_explicitly_rejected(self):
        self.assertEqual(g.SYSTEM_SERVICE_CODES, {0x00, 0x11, 0x23, 0x33})
        self.assertEqual(g.FLEETNET_SERVICE_CODES, {0x02, 0x72})
        self.assertFalse(g.SAFETYNET_SERVICE_CODES & (g.SYSTEM_SERVICE_CODES | g.FLEETNET_SERVICE_CODES))
        for code in (0x00, 0x11, 0x23, 0x33):
            self.assertEqual(g.classify(medium(0x30, code)).reason, "SYSTEM_SERVICE_CODE")
        for code in (0x02, 0x72):
            self.assertEqual(g.classify(long_form(0x32, code)).reason, "FLEETNET_SERVICE_CODE")

    def test_short_descriptors_are_never_egc(self):
        for first in range(0x80):
            with self.subTest(first=first):
                self.assertEqual(g.classify(bytes((first, 5, 0x04, 0, 0, 0, 0))).reason, "SHORT_DESCRIPTOR")

    def test_non_egc_descriptor_types_reject(self):
        for ptype in range(64):
            if ptype in g.EGC_TYPES or ptype in (g.MULTIFRAME_START, g.MULTIFRAME_CONTINUATION):
                continue
            for build in (medium, long_form):
                with self.subTest(ptype=ptype, form=build.__name__):
                    self.assertEqual(g.classify(build(ptype, 0x04)).reason, "NOT_EGC_TYPE")

    def test_truncated_or_malformed_packets_reject(self):
        packet = medium(0x31, 0x04, b"\x01\x02\x03")
        for value, reason in ((packet[:-1], "TRUNCATED_LENGTH"), (long_form(0x31, 0x04)[:-1], "TRUNCATED_LENGTH"),
                              (b"\xb1", "TRUNCATED_HEADER"), (b"\xf1\x00", "TRUNCATED_HEADER"), (b"", "TRUNCATED_HEADER"),
                              (bytes((0xB1, 1, 0x04)), "LENGTH_TOO_SMALL"),
                              (bytes((0xF1, 0, 1, 0x04)), "LENGTH_TOO_SMALL"),
                              (None, "INVALID_PACKET"), ("\xb1\x05\x04", "INVALID_PACKET"), (12, "INVALID_PACKET"),
                              ([0xB1, 300, 4, 0, 0], "INVALID_PACKET"), ([0xB1, 3, -4, 0, 0], "INVALID_PACKET"),
                              ([True, 3, 4, 0, 0], "INVALID_PACKET")):
            with self.subTest(value=value):
                self.assertEqual(g.classify(value), g.EgcDecision(False, reason))
        self.assertTrue(g.classify(bytearray(packet)).accept)
        self.assertTrue(g.classify(memoryview(packet)).accept)
        self.assertEqual(g.classify(packet + b"next descriptor").length, len(packet))

    def test_long_form_length_is_read_big_endian(self):
        packet = long_form(0x30, 0x13, bytes(300))
        self.assertEqual((packet[1], packet[2]), (0x01, 0x2F))
        self.assertEqual(g.classify(packet).length, 306)

    def test_classifier_reads_only_header_bytes(self):
        cases = [medium(0x31, 0x02, bytes(50)), long_form(0x31, 0x11, bytes(50)), bytes((0x10,)) + bytes(50),
                 medium(0x15, 0x04, bytes(50)), fragment(0x3D, medium(0x31, 0x72, bytes(50))[:40]),
                 fragment(0x3D, long_form(0x31, 0x24, bytes(50))[:40]), fragment(0x3E, bytes(50)),
                 medium(0x31, 0x04, bytes(50)), fragment(0x3D, long_form(0x31, 0x04, bytes(50))[:40])]
        for packet in cases:
            spy = Spy(packet)
            g.classify(spy)
            with self.subTest(first=packet[0]):
                self.assertTrue(all(type(key) is int and 0 <= key <= 5 for key in spy.reads), spy.reads)
                self.assertLessEqual(max(spy.reads), 5 if packet[0] == 0xBD else 3)

    def test_reason_codes_are_stable_identifiers_never_packet_bytes(self):
        rng = random.Random(307)
        for _ in range(3000):
            packet = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 12)))
            decision = g.classify(packet)
            self.assertIn(decision.reason, g.REASONS)
            if not decision.accept:
                self.assertEqual(decision[2:], (None,) * 5)
        for reason in g.REASONS:
            self.assertRegex(reason, r"\A[A-Z0-9_]+\Z")


class MultiframeTests(unittest.TestCase):
    def setUp(self):
        self.inner = medium(0x31, 0x04, bytes(range(40)))  # 45 bytes
        self.start, self.continuation = fragment(0x3D, self.inner[:20]), fragment(0x3E, self.inner[20:])

    def test_start_is_decided_on_the_first_fragment_and_continuation_completes(self):
        decision = g.classify(self.start)
        self.assertEqual(decision, g.EgcDecision(True, "ACCEPT_SAFETYNET_MULTIFRAME_START", g.MEDIUM, 0x3D, 0x04,
                                                 len(self.start), len(self.inner)))
        self.assertEqual(self.start[0], 0xBD)
        assembler = g.EgcAssembler(toy_verifier)
        assembler.begin_frame(1)
        self.assertEqual(assembler.feed(self.start), [])
        self.assertTrue(assembler.open)
        assembler.begin_frame(2)
        self.assertEqual(assembler.feed(self.continuation), [self.inner])
        self.assertFalse(assembler.open)
        inner = long_form(0x30, 0x13, bytes(range(256)) + bytes(44))
        parts = [fragment(0x3D, inner[:100]), fragment(0x3E, inner[100:250]), fragment(0x3E, inner[250:])]
        self.assertEqual(frames(g.EgcAssembler(toy_verifier), *([part] for part in parts)), [[], [], [inner]])
        # A start holding the whole inner descriptor needs no frame boundary.
        self.assertEqual(g.EgcAssembler(toy_verifier).feed(fragment(0x3D, self.inner)), [self.inner])

    def test_continuation_after_rejected_or_missing_start_is_dropped_unread(self):
        rejected = fragment(0x3D, medium(0x31, 0x72, bytes(40))[:20])
        verifier = Verifier()
        assembler = g.EgcAssembler(verifier)
        for number, packet in enumerate((rejected, self.continuation), 1):
            assembler.begin_frame(number)
            spy = Spy(packet)
            self.assertEqual(assembler.feed(spy), [])
            self.assertTrue(all(type(key) is int and key <= 5 for key in spy.reads))
        self.assertEqual(assembler.last_reason, "CONTINUATION_WITHOUT_ACCEPTED_START")
        self.assertEqual(verifier.calls, [])
        fresh = g.EgcAssembler(verifier)
        spy = Spy(self.continuation)
        self.assertEqual(fresh.feed(spy), [])
        self.assertEqual(spy.reads, [0])
        # The next accepted start opens a new message again.
        self.assertEqual(frames(assembler, [self.start], [self.continuation], first=3), [[], [self.inner]])

    def test_inner_header_must_lie_wholly_in_the_first_fragment(self):
        for size in (1, 2):
            with self.subTest(size=size):
                self.assertEqual(g.classify(fragment(0x3D, self.inner[:size])).reason,
                                 "INNER_HEADER_NOT_IN_FIRST_FRAGMENT")
        self.assertTrue(g.classify(fragment(0x3D, self.inner[:3])).accept)
        inner = long_form(0x31, 0x24, bytes(40))
        self.assertEqual(g.classify(fragment(0x3D, inner[:3])).reason, "INNER_HEADER_NOT_IN_FIRST_FRAGMENT")
        self.assertTrue(g.classify(fragment(0x3D, inner[:4])).accept)
        for data, reason in ((bytes((0x31, 5, 4, 0)), "INNER_SHORT_DESCRIPTOR"),
                             (medium(0x15, 0x04, bytes(5)), "INNER_NOT_EGC_TYPE"),
                             (medium(0x31, 0x11, bytes(5)), "SYSTEM_SERVICE_CODE"),
                             (bytes((0xB1, 1, 0x04)), "LENGTH_TOO_SMALL")):
            with self.subTest(reason=reason):
                self.assertEqual(g.classify(fragment(0x3D, data)).reason, reason)
        self.assertEqual(g.classify(fragment(0x3D, self.inner[:20], raw=0xFD)).reason, "MULTIFRAME_LONG_FORM_UNVERIFIED")

    def test_open_message_is_discarded_by_any_other_packet_or_bad_fragment(self):
        assembler = g.EgcAssembler(toy_verifier)
        single = medium(0x30, 0x13, b"text")
        self.assertEqual(frames(assembler, [self.start, single], [self.continuation]), [[], [single], []])
        self.assertEqual(assembler.discarded, 1)
        bad = self.continuation[:-1] + bytes(((self.continuation[-1] + 1) & 0xFF,))
        for number, (packet, reason) in enumerate(((bad, "CHECKSUM_MISMATCH"),
                                                   (fragment(0x3E, self.inner[20:], raw=0xFE), "MULTIFRAME_LONG_FORM_UNVERIFIED"),
                                                   (self.continuation + b"\x00", "LENGTH_MISMATCH")), 1):
            with self.subTest(reason=reason):
                self.assertEqual(frames(assembler, [self.start], [packet], first=10 * number), [[], []])
                self.assertEqual(assembler.last_reason, reason)
                self.assertFalse(assembler.open)
        self.assertEqual(assembler.discarded, 4)

    def test_memory_and_fragment_limits(self):
        verifier = Verifier()
        inner = long_form(0x30, 0x13, bytes(300))
        small = g.EgcAssembler(verifier, max_message_bytes=64)
        self.assertEqual(small.feed(fragment(0x3D, inner[:100])), [])
        self.assertEqual(small.last_reason, "MESSAGE_SIZE_LIMIT")
        self.assertEqual(small.feed(long_form(0x31, 0x04, bytes(100))), [])
        self.assertEqual(small.last_reason, "MESSAGE_SIZE_LIMIT")
        self.assertEqual(verifier.calls, [])  # limits refuse before any checksum or copy
        few = g.EgcAssembler(toy_verifier, max_fragments=2)
        parts = [fragment(0x3D, self.inner[:10]), fragment(0x3E, self.inner[10:20]), fragment(0x3E, self.inner[20:])]
        self.assertEqual(frames(few, *([part] for part in parts)), [[], [], []])
        self.assertEqual(few.last_reason, "FRAGMENT_LIMIT")
        for kwargs in ({"max_message_bytes": 4}, {"max_message_bytes": 10 ** 6}, {"max_fragments": 1},
                       {"max_fragments": True}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(g.EgcRefused, "ASSEMBLER_LIMITS_INVALID"):
                g.EgcAssembler(toy_verifier, **kwargs)
        with self.assertRaisesRegex(g.EgcRefused, "CHECKSUM_ALGORITHM_UNVERIFIED"):
            g.EgcAssembler(None)


class FrameBoundaryTests(unittest.TestCase):
    """Fragments carry no message id: explicit TDM frame boundaries keep messages apart (fail closed)."""
    def setUp(self):
        self.inner = medium(0x31, 0x04, bytes(range(40)))  # SafetyNET, 45 bytes
        self.start, self.continuation = fragment(0x3D, self.inner[:20]), fragment(0x3E, self.inner[20:])

    def test_lost_frame_never_appends_a_fleetnet_continuation(self):
        fleet = medium(0x31, 0x72, bytes(range(100, 140)))  # FleetNET, same size as the SafetyNET message
        # Frame 11 (never decoded) held self.continuation and the FleetNET start fragment(0x3D, fleet[:20]).
        fleet_continuation = fragment(0x3E, fleet[20:])
        self.assertEqual(len(fleet_continuation), len(self.continuation))  # it would have completed the message
        verifier = Verifier()
        assembler = g.EgcAssembler(verifier)
        self.assertEqual(frames(assembler, [self.start], first=10), [[]])
        assembler.begin_frame(12)  # frame 11 was lost
        self.assertEqual((assembler.last_reason, assembler.open, assembler.discarded), ("FRAME_GAP", False, 1))
        spy = Spy(fleet_continuation)
        self.assertEqual(assembler.feed(spy), [])
        self.assertEqual((assembler.last_reason, spy.reads), ("CONTINUATION_WITHOUT_ACCEPTED_START", [0]))
        self.assertNotIn(fleet_continuation, verifier.calls)
        # The same fragment fed without a new boundary (still frame 10, not its first descriptor) is refused too.
        assembler = g.EgcAssembler(verifier)
        self.assertEqual(frames(assembler, [self.start, fleet_continuation], first=10), [[], []])
        self.assertEqual((assembler.last_reason, assembler.open), ("UNEXPECTED_FRAGMENT", False))
        # A decoded but empty next frame (both descriptors lost) is a gap as well.
        assembler = g.EgcAssembler(verifier)
        self.assertEqual(frames(assembler, [self.start], [], [fleet_continuation], first=10), [[], []])
        self.assertEqual(assembler.last_reason, "CONTINUATION_WITHOUT_ACCEPTED_START")
        self.assertNotIn(fleet_continuation, verifier.calls)

    def test_loss_position_and_frame_numbers_close_the_message(self):
        three = [fragment(0x3D, self.inner[:10]), fragment(0x3E, self.inner[10:20]), fragment(0x3E, self.inner[20:])]
        cases = {
            "DESCRIPTOR_LOST": lambda a: (a.begin_frame(1), a.feed(three[0]), a.begin_frame(2), a.lost()),
            "UNEXPECTED_FRAGMENT": lambda a: frames(a, [three[0]], [three[1], three[2]]),
            "FRAME_GAP": lambda a: (a.begin_frame(5), a.feed(three[0]), a.begin_frame(5)),
        }
        cases["FRAME_GAP decreasing"] = lambda a: (a.begin_frame(5), a.feed(three[0]), a.begin_frame(4))
        cases["FRAME_GAP wrap"] = lambda a: (a.begin_frame(g.FRAME_NUMBER_LIMIT - 1), a.feed(three[0]), a.begin_frame(0))
        for value in (-1, True, 1.5, None, "2", g.FRAME_NUMBER_LIMIT):
            cases["FRAME_NUMBER_INVALID %r" % (value,)] = lambda a, value=value: (a.begin_frame(1), a.feed(three[0]), a.begin_frame(value))
        for label, steps in cases.items():
            with self.subTest(case=label):
                assembler = g.EgcAssembler(toy_verifier)
                steps(assembler)
                self.assertEqual(assembler.last_reason, label.split()[0])
                self.assertFalse(assembler.open)
                self.assertEqual(assembler.discarded, 1)
                self.assertEqual(assembler.feed(three[2]), [])  # nothing left to continue
                self.assertIn(assembler.last_reason, ("CONTINUATION_WITHOUT_ACCEPTED_START", "UNEXPECTED_FRAGMENT"))
        # The same three fragments in consecutive frames, each first in its frame, complete the message.
        self.assertEqual(frames(g.EgcAssembler(toy_verifier), [medium(0x30, 0x13), three[0]], [three[1]], [three[2]]),
                         [[medium(0x30, 0x13)], [], [], [self.inner]])

    def test_without_a_frame_boundary_a_multiframe_start_is_refused_before_any_checksum(self):
        verifier = Verifier()
        assembler = g.EgcAssembler(verifier)
        self.assertEqual(assembler.feed(self.start), [])
        self.assertEqual((assembler.last_reason, assembler.open, verifier.calls), ("FRAME_BOUNDARY_MISSING", False, []))
        assembler.begin_frame("bad")  # an invalid number also forgets the current frame
        self.assertEqual(assembler.feed(self.start), [])
        self.assertEqual(assembler.last_reason, "FRAME_BOUNDARY_MISSING")
        single = medium(0x31, 0x04, b"x")
        self.assertEqual(assembler.feed(single), [single])  # single descriptors need no boundary

    def test_overrun_of_the_declared_inner_length_closes_the_message(self):
        verifier = Verifier()
        assembler = g.EgcAssembler(verifier)
        longer = fragment(0x3E, self.inner[20:] + b"next message bytes")
        self.assertEqual(frames(assembler, [self.start], [longer]), [[], []])
        self.assertEqual((assembler.last_reason, assembler.open), ("LENGTH_MISMATCH", False))
        self.assertNotIn(longer, verifier.calls)  # refused before its checksum
        self.assertEqual(g.EgcAssembler(toy_verifier).feed(fragment(0x3D, self.inner + b"zz")), [])


class ChecksumTests(unittest.TestCase):
    def test_bad_checksum_on_an_accepted_packet_rejects(self):
        packet = medium(0x31, 0x44, b"abc")
        bad = packet[:-1] + bytes(((packet[-1] + 1) & 0xFF,))
        self.assertTrue(g.checksum_ok(packet, toy_verifier))
        self.assertFalse(g.checksum_ok(bad, toy_verifier))
        assembler = g.EgcAssembler(toy_verifier)
        self.assertEqual(assembler.feed(bad), [])
        self.assertEqual(assembler.last_reason, "CHECKSUM_MISMATCH")
        self.assertEqual(assembler.feed(packet), [packet])
        bad_start = fragment(0x3D, medium(0x31, 0x04, bytes(40))[:20])
        bad_start = bad_start[:-1] + bytes(((bad_start[-1] + 1) & 0xFF,))
        assembler.begin_frame(1)
        self.assertEqual(assembler.feed(bad_start), [])
        self.assertEqual(assembler.last_reason, "CHECKSUM_MISMATCH")
        assembler.begin_frame(2)
        self.assertEqual(assembler.feed(fragment(0x3E, bytes(25))), [])
        self.assertEqual(assembler.last_reason, "CONTINUATION_WITHOUT_ACCEPTED_START")
        # Every fragment checksum verifies, the reassembled inner descriptor's own does not: rejected.
        inner = medium(0x31, 0x04, bytes(range(40)))
        inner = inner[:-1] + bytes(((inner[-1] + 1) & 0xFF,))
        self.assertTrue(g.classify(fragment(0x3D, inner[:20])).accept)
        self.assertEqual(frames(assembler, [fragment(0x3D, inner[:20])], [fragment(0x3E, inner[20:])], first=3), [[], []])
        self.assertEqual(assembler.last_reason, "CHECKSUM_MISMATCH")
        self.assertFalse(assembler.open)

    def test_rejected_packets_get_no_checksum_and_no_copy(self):
        verifier = Verifier()
        assembler = g.EgcAssembler(verifier)
        rejected = [medium(0x31, code, bytes(30)) for code in (0x00, 0x02, 0x72, 0x05)]
        rejected += [bytes((0x10,)) + bytes(30), medium(0x20, 0x04, bytes(30)), medium(0x31, 0x04, bytes(30))[:-3]]
        for packet in rejected:
            spy = Spy(packet)
            self.assertEqual(assembler.feed(spy), [])
            with self.subTest(first=packet[0]):
                self.assertTrue(all(type(key) is int for key in spy.reads), spy.reads)  # no slice copy
                verifier_spy = Verifier()
                with self.assertRaisesRegex(g.EgcRefused, "CHECKSUM_ONLY_AFTER_ACCEPT"):
                    g.checksum_ok(spy, verifier_spy)
                self.assertEqual(verifier_spy.calls, [])
        self.assertEqual(verifier.calls, [])
        accepted = medium(0x31, 0x04, bytes(30))
        self.assertEqual(assembler.feed(accepted), [accepted])
        self.assertEqual(verifier.calls, [accepted])

    def test_checksum_algorithm_is_injected_and_fails_closed(self):
        packet = medium(0x31, 0x04)
        with self.assertRaisesRegex(g.EgcRefused, "CHECKSUM_ALGORITHM_UNVERIFIED"):
            g.checksum_ok(packet)
        self.assertFalse(g.checksum_ok(packet, mock.Mock(side_effect=RuntimeError("broken"))))
        self.assertFalse(g.checksum_ok(packet, lambda descriptor: 1))
        self.assertTrue(g.checksum_ok(packet + b"trailing", toy_verifier))


class WatchdogAndBandTests(unittest.TestCase):
    def test_watchdog_stops_after_n_frames_without_ncs_header(self):
        watchdog = g.NcsWatchdog(3)
        self.assertEqual([watchdog.frame(False) for _ in range(3)], [True, True, False])
        self.assertTrue(watchdog.stopped)
        self.assertFalse(watchdog.frame(True))  # latched; a new carrier needs a new watchdog
        watchdog = g.NcsWatchdog(2)
        self.assertEqual([watchdog.frame(seen) for seen in (False, True, False, 1, "yes")],
                         [True, True, True, False, False])
        for value in (0, -1, True, 1.5, None, 100001):
            with self.subTest(value=value), self.assertRaisesRegex(g.EgcRefused, "NCS_WATCHDOG_N_INVALID"):
                g.NcsWatchdog(value)

    def test_demodulation_band_rule(self):
        self.assertFalse(scope_policy.demod_allowed(1544.0e6, 1e3))
        self.assertFalse(scope_policy.demod_allowed(1544.5e6, 1e3))
        self.assertFalse(scope_policy.demod_allowed(1543.9e6, 2e3))
        self.assertTrue(scope_policy.demod_allowed(1543.899e6, 2e3))
        self.assertTrue(scope_policy.demod_allowed(1540.0e6, 25e3))
        self.assertTrue(scope_policy.demod_allowed(1537.0005e6, 1e3))
        self.assertFalse(scope_policy.demod_allowed(1536.9e6, 1e3))
        for center, width in ((1540e6, 0), (1540e6, -1), (1540e6, float("nan")), (1540e6, True), (True, 1e3),
                              (1540e6, 10e6), ("1540e6", 1e3)):
            with self.subTest(center=center, width=width):
                self.assertFalse(scope_policy.demod_allowed(center, width))
        # Necessary, not sufficient: spectrum.py's 1530-1660 MHz mask still stops the span.
        self.assertTrue(scope_policy.scope_check(1539.99e6, 1540.01e6)["stop"])


class ReleaseTests(unittest.TestCase):
    def test_passing_gate_unit_tests_does_not_enable_the_profile(self):
        self.assertTrue(g.classify(medium(0x31, 0x04)).accept)
        self.assertFalse(any(g.RELEASE_EVIDENCE.values()))
        self.assertEqual(g.gate_status(), "DISABLED_RELEASE_EVIDENCE_MISSING")
        expected = "DISABLED_NO_VERIFIED_HEADER_PARSER_AND_TEST_VECTORS"
        self.assertEqual(decoder_policy.availability()["egc-safetynet"], expected)
        with mock.patch.dict(g.RELEASE_EVIDENCE, {key: True for key in g.RELEASE_EVIDENCE}):
            self.assertTrue(g.gate_status().startswith("DISABLED"))
            self.assertEqual(decoder_policy.availability()["egc-safetynet"], expected)
        source = Path(decoder_policy.__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"import\s+.*egc_gate")  # the profile cannot reach the gate code


if __name__ == "__main__":
    unittest.main()
