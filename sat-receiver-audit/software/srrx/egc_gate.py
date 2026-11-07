"""Inmarsat-C EGC SafetyNET header gate (STACK.md:120); headers only, never message text.

Released by evidence only. decoder_policy keeps "egc-safetynet" DISABLED until
a reviewer has checked the C2 service-code table and the descriptor checksum
algorithm (both read from sources, RELEASE_EVIDENCE_SOURCES, unreviewed) and the
ПОЛ-06 mixed-recording test passes. Synthetic unit tests do not enable anything.

Rules: (1) class from byte 0: 0xxxxxxx short (never EGC), 10xxxxxx medium with
length pkt[1]+2, 11xxxxxx long with length pkt[1..2]+3; type = byte0 & 0x3F;
EGC types 0x30-0x32. (2) Service code at offset 2 (medium) or 3 (long); the
priority is bits 6-5 of the next byte (0 routine, 1 safety, 2 urgency,
3 distress). (3) Only the SafetyNET codes of the IMO MSC.1/Circ.1364/Rev.2 C2
table pass, C2 00 (all ships, general call) only at urgency or distress
priority; System, FleetNET and all others (0x73 included) are rejected.
(4) Multiframe 0x3D/0x3E: decided on the first fragment, inner descriptor at
byte 2. (5) The 2-byte checksum is evaluated only for accepted packets; a
rejected packet is neither checksummed nor copied.

Read 2026-11-07 (RELEASE_EVIDENCE_SOURCES; a reading, not a review):
- SatDump 1aedd60 packets_structs.h: descriptor class and the big-endian long
  length (:51-77), the checksum (:90-108, trailer :120, a sent 0 accepted :122)
  and the EGC header: service code pkt[2], priority (pkt[3] & 0x60) >> 5 (:618-620,
  medium form only; for the long form the gate reads the byte after its service
  code at offset 3, an assumption); pkt_structs.cpp:538-555 names priorities 0-3;
- IMO MSC.1/Circ.1364/Rev.2 annex pages 17-18: C2 00, 04, 13, 14, 24, 31, 34, 44
  (0x73, which SatDump pkt_structs.cpp:531-532 names a SafetyNET chart correction
  service, is not listed); appendix 2 part C §4 (annex page 32): a general call
  is always C1 = 3 (distress) or 2 (urgency) with C2 = 00.

Conservative assumptions, to verify against SatDump at 1aedd60 (URL STACK.md:1955)
before any release:
- the over-air priority bits carry the C1 priority code of the IMO manual;
- 0x3D starts and 0x3E continues a multiframe; both are medium form (raw 0xBD /
  0xBE) because the inner descriptor sits at byte 2; long-form 0xFD/0xFE is
  rejected; a fragment carries outer header bytes 0-1, data, then 2 checksum
  bytes; a continuation without an accepted open start is dropped; a rejected
  start drops later continuations until the next start; the inner descriptor
  header and service code must lie wholly inside the first fragment;
- a fragment carries no message identifier, so frame boundaries are explicit
  (EgcAssembler.begin_frame(n) with the TDM frame counter, lost() for any
  undecodable descriptor): a message continues only as the FIRST descriptor of
  frame n+1 after its last fragment in frame n. A gap, a repeated, decreasing,
  wrapped or invalid frame number, a reported loss, a continuation anywhere else,
  a missing boundary or a fragment that overruns the declared inner length
  closes and zero-fills the open message, so after a lost frame a continuation
  of another (e.g. FleetNET) multiframe is never appended; the completed inner
  descriptor's own checksum must verify too (SatDump pkt_parser.cpp:8-34 and
  :124-142 handle one 0x3D start and one 0x3E end with outer bytes 0-1, data
  and 2 checksum bytes, and size only short and medium inner descriptors);
- the checksum stays an injected verifier(descriptor_bytes) -> True; without
  one nothing is checked or passed. verify_inmarsat_c is the read algorithm,
  passed explicitly until the review; unlike SatDump it refuses a sent 0x0000
  (fail closed until ПОЛ-06 shows SafetyNET descriptors sent so);
- N for NcsWatchdog is a required parameter set by the gate test.
"""
from __future__ import annotations

from typing import NamedTuple

MEDIUM, LONG = "MEDIUM", "LONG"
EGC_TYPES = frozenset((0x30, 0x31, 0x32))
MULTIFRAME_START, MULTIFRAME_CONTINUATION = 0x3D, 0x3E
# IMO MSC.1/Circ.1364/Rev.2 C2 table (annex pages 17-18); 0x00 passes only at GENERAL_CALL_MIN_PRIORITY.
SAFETYNET_SERVICE_CODES = frozenset((0x00, 0x04, 0x13, 0x14, 0x24, 0x31, 0x34, 0x44))
GENERAL_CALL = 0x00
GENERAL_CALL_MIN_PRIORITY = 2  # urgency; appendix 2 part C §4: a general call is always C1 = 3 or 2
PRIORITY_MASK, PRIORITY_SHIFT = 0x60, 5  # bits 6-5 of the byte after the service code
SYSTEM_SERVICE_CODES = frozenset((0x11, 0x23, 0x33))
FLEETNET_SERVICE_CODES = frozenset((0x02, 0x72))
CHECKSUM_BYTES = 2
# Each item is evidence outside this code; flipping one here is a reviewed change.
RELEASE_EVIDENCE = {"c2_service_code_table_verified": False,
                    "pol06_mixed_recording_test_passed": False,
                    "descriptor_checksum_algorithm_verified": False}
# What was read for each item. SOURCE_READ_UNREVIEWED is an agent's reading, never a review:
# no flag above follows from it.
RELEASE_EVIDENCE_SOURCES = {
    "c2_service_code_table_verified": {
        "status": "SOURCE_READ_UNREVIEWED", "read": "2026-11-07",
        "source": "IMO MSC.1/Circ.1364/Rev.2 (11 November 2020), International SafetyNET Services Manual, 2021 edition",
        "url": "https://wwwcdn.imo.org/localresources/en/OurWork/Safety/Documents/"
               "Documents%20relevant%20to%20GMDSS/MSC.1-Circ.1364-Rev.2.pdf",
        "sha256": "e809f9fd577b543c955145cf9688b1e24c3a85afb00f47e8763079ac70fd6342",
        "where": "annex pages 17-18 (PDF pages 19-20) C1/C2 table; §6.4 (annex page 14); §6.8 (annex page 16); "
                 "appendix 2 priority and service-code allocation (annex pages 25-26) and part C §4 (annex page 32)",
        "open": "the 2022 edition of the manual is sold, not free, and was not read"},
    "descriptor_checksum_algorithm_verified": {
        "status": "SOURCE_READ_UNREVIEWED", "read": "2026-11-07",
        "source": "SatDump 1aedd602055c154401384a8cc7876713bb371254 plugins/inmarsat_support/stdc/packets_structs.h",
        "url": "https://github.com/SatDump/SatDump/blob/1aedd602055c154401384a8cc7876713bb371254/"
               "plugins/inmarsat_support/stdc/packets_structs.h",
        "where": "lines 90-108 (compute_crc), 119-125 (big-endian trailer, a sent 0 accepted), "
                 "599-652 (EGC header: service code pkt[2], priority (pkt[3] & 0x60) >> 5)",
        "open": "no real descriptor checked; the vectors belong to the ПОЛ-06 mixed recording"},
    "pol06_mixed_recording_test_passed": {
        "status": "OPEN", "read": None, "source": "build/09-testy.md ПОЛ-06",
        "open": "mixed recording (on-air NCS, device, field) not made"},
}
REASONS = frozenset((
    "ACCEPT_SAFETYNET", "ACCEPT_SAFETYNET_MULTIFRAME_START", "INVALID_PACKET", "TRUNCATED_HEADER",
    "SHORT_DESCRIPTOR", "NOT_EGC_TYPE", "TRUNCATED_LENGTH", "LENGTH_TOO_SMALL",
    "SYSTEM_SERVICE_CODE", "FLEETNET_SERVICE_CODE", "SERVICE_CODE_NOT_SAFETYNET", "GENERAL_CALL_BELOW_URGENCY",
    "MULTIFRAME_LONG_FORM_UNVERIFIED", "INNER_SHORT_DESCRIPTOR", "INNER_NOT_EGC_TYPE",
    "INNER_HEADER_NOT_IN_FIRST_FRAGMENT", "CONTINUATION_WITHOUT_ACCEPTED_START",
    "LENGTH_MISMATCH", "CHECKSUM_MISMATCH", "MESSAGE_SIZE_LIMIT", "FRAGMENT_LIMIT",
    "FRAME_GAP", "FRAME_NUMBER_INVALID", "FRAME_BOUNDARY_MISSING", "UNEXPECTED_FRAGMENT", "DESCRIPTOR_LOST"))
FRAME_NUMBER_LIMIT = 1 << 32  # frame counters are non-negative ints below this; no wrap is assumed


class EgcRefused(ValueError):
    """Stable refusal code; never contains packet bytes."""


class EgcDecision(NamedTuple):
    accept: bool
    reason: str
    cls: str | None = None
    ptype: int | None = None
    service_code: int | None = None
    length: int | None = None
    inner_length: int | None = None


def gate_status():
    """Always DISABLED: evidence alone never enables decoder_policy's reviewed profile."""
    if not all(value is True for value in RELEASE_EVIDENCE.values()):
        return "DISABLED_RELEASE_EVIDENCE_MISSING"
    return "DISABLED_PENDING_REVIEWED_PROFILE_CHANGE"


def _reject(reason):
    # Rejected decisions carry no header values, so nothing of the packet can be logged.
    return EgcDecision(False, reason)


def _byte(packet, index):
    try:
        value = packet[index]
    except (IndexError, KeyError, TypeError):
        return None
    return value if type(value) is int and 0 <= value <= 255 else None


def _size(packet):
    if isinstance(packet, str):
        return None
    try:
        size = len(packet)
    except TypeError:
        return None
    return size if type(size) is int else None


def _length(packet, base, cls, limit):
    """Declared length, or a reason; reads only bytes base+1 (medium) or base+1..2 (long)."""
    if base + (1 if cls == MEDIUM else 2) >= limit:
        return "TRUNCATED_HEADER"
    first = _byte(packet, base + 1)
    second = 0 if cls == MEDIUM else _byte(packet, base + 2)
    if first is None or second is None:
        return "INVALID_PACKET"
    return first + 2 if cls == MEDIUM else (first << 8 | second) + 3  # big-endian (SatDump packets_structs.h:72)


def _class(value):
    return LONG if value & 0x40 else MEDIUM


def _service(packet, code, priority_index, cls, ptype, length, inner_length=None):
    """Decision for one service code; only C2 00 reads its priority byte (bounds checked by the caller)."""
    if code == GENERAL_CALL:
        value = _byte(packet, priority_index)
        if value is None:
            return _reject("INVALID_PACKET")
        if (value & PRIORITY_MASK) >> PRIORITY_SHIFT < GENERAL_CALL_MIN_PRIORITY:
            return _reject("GENERAL_CALL_BELOW_URGENCY")  # routine or safety: not a distress relay
    if code in SAFETYNET_SERVICE_CODES:
        reason = "ACCEPT_SAFETYNET" if inner_length is None else "ACCEPT_SAFETYNET_MULTIFRAME_START"
        return EgcDecision(True, reason, cls, ptype, code, length, inner_length)
    if code in SYSTEM_SERVICE_CODES:
        return _reject("SYSTEM_SERVICE_CODE")
    if code in FLEETNET_SERVICE_CODES:
        return _reject("FLEETNET_SERVICE_CODE")
    return _reject("SERVICE_CODE_NOT_SAFETYNET")


def classify(packet):
    """Header decision for one descriptor; reads bytes 0-3 (0-4 for a long C2 00; 0-5 for a
    multiframe start, 0-6 when its inner descriptor is a long C2 00).

    Stateless: a continuation is rejected here and handled by EgcAssembler.
    """
    size = _size(packet)
    if size is None:
        return _reject("INVALID_PACKET")
    if size == 0:
        return _reject("TRUNCATED_HEADER")
    first = _byte(packet, 0)
    if first is None:
        return _reject("INVALID_PACKET")
    if not first & 0x80:
        return _reject("SHORT_DESCRIPTOR")
    cls, ptype = _class(first), first & 0x3F
    if ptype == MULTIFRAME_CONTINUATION:
        return _reject("CONTINUATION_WITHOUT_ACCEPTED_START")
    if ptype not in EGC_TYPES and ptype != MULTIFRAME_START:
        return _reject("NOT_EGC_TYPE")
    if ptype == MULTIFRAME_START and cls == LONG:
        return _reject("MULTIFRAME_LONG_FORM_UNVERIFIED")
    length = _length(packet, 0, cls, size)
    if isinstance(length, str):
        return _reject(length)
    if size < length:
        return _reject("TRUNCATED_LENGTH")
    if ptype in EGC_TYPES:
        offset = 2 if cls == MEDIUM else 3
        if length < offset + 1 + CHECKSUM_BYTES:
            return _reject("LENGTH_TOO_SMALL")
        code = _byte(packet, offset)
        if code is None:
            return _reject("INVALID_PACKET")
        if code == GENERAL_CALL and length < offset + 2 + CHECKSUM_BYTES:
            return _reject("LENGTH_TOO_SMALL")  # its priority byte must precede the checksum
        return _service(packet, code, offset + 1, cls, ptype, length)
    # Multiframe start: inner descriptor at byte 2, its header wholly before this fragment's checksum.
    limit = length - CHECKSUM_BYTES
    inner = _byte(packet, 2) if limit > 2 else None
    if inner is None:
        return _reject("INNER_HEADER_NOT_IN_FIRST_FRAGMENT")
    if not inner & 0x80:
        return _reject("INNER_SHORT_DESCRIPTOR")
    inner_cls, inner_type = _class(inner), inner & 0x3F
    if inner_type not in EGC_TYPES:
        return _reject("INNER_NOT_EGC_TYPE")
    offset = 2 if inner_cls == MEDIUM else 3
    inner_length = _length(packet, 2, inner_cls, limit)
    if inner_length == "INVALID_PACKET":
        return _reject(inner_length)
    if isinstance(inner_length, str) or 2 + offset >= limit:
        return _reject("INNER_HEADER_NOT_IN_FIRST_FRAGMENT")
    if inner_length < offset + 1 + CHECKSUM_BYTES:
        return _reject("LENGTH_TOO_SMALL")
    code = _byte(packet, 2 + offset)
    if code is None:
        return _reject("INVALID_PACKET")
    if code == GENERAL_CALL:  # the priority byte, too, lies in the first fragment and the inner descriptor
        if 3 + offset >= limit:
            return _reject("INNER_HEADER_NOT_IN_FIRST_FRAGMENT")
        if inner_length < offset + 2 + CHECKSUM_BYTES:
            return _reject("LENGTH_TOO_SMALL")
    return _service(packet, code, 3 + offset, cls, ptype, length, inner_length)


def _verified(packet, length, verifier):
    """Copies the descriptor only here, after acceptance; any verifier failure is a mismatch."""
    descriptor = bytes(packet[:length])
    try:
        return verifier(descriptor) is True
    except Exception:
        return False


def checksum_inmarsat_c(descriptor):
    """16-bit Inmarsat-C descriptor checksum, own code after SatDump packets_structs.h:90-108 (1aedd60).

    Two running sums C0 += byte, C1 += C0 over the whole descriptor with its last
    two (checksum) bytes taken as zero; CB1 = (C0 - C1) mod 256 is the high and
    CB2 = (C1 - 2*C0) mod 256 the low byte of the trailer (:105-107, :120). Read,
    not reviewed: RELEASE_EVIDENCE stays False.
    """
    size = _size(descriptor)
    if size is None or size <= CHECKSUM_BYTES:
        raise EgcRefused("CHECKSUM_INPUT_INVALID")
    c0 = c1 = 0
    for index in range(size):
        value = 0 if index >= size - CHECKSUM_BYTES else _byte(descriptor, index)
        if value is None:
            raise EgcRefused("CHECKSUM_INPUT_INVALID")
        c0 = (c0 + value) & 0xFF
        c1 = (c1 + c0) & 0xFF
    return ((c0 - c1) & 0xFF) << 8 | ((c1 - 2 * c0) & 0xFF)


def verify_inmarsat_c(descriptor):
    """Verifier for checksum_ok/EgcAssembler: the big-endian trailer equals checksum_inmarsat_c.

    Fails closed where SatDump does not: a sent 0x0000, which packets_structs.h:122
    accepts unchecked, is a mismatch (so is a descriptor whose computed sum is 0)
    until ПОЛ-06 shows SafetyNET descriptors sent so.
    """
    size = _size(descriptor)
    try:
        computed = checksum_inmarsat_c(descriptor)
    except EgcRefused:
        return False
    high, low = _byte(descriptor, size - 2), _byte(descriptor, size - 1)
    if high is None or low is None:
        return False
    sent = high << 8 | low
    return sent != 0 and sent == computed


def checksum_ok(packet, algorithm=None):
    """Evaluate the injected checksum verifier for an accepted packet only."""
    decision = classify(packet)
    if not decision.accept:
        raise EgcRefused("CHECKSUM_ONLY_AFTER_ACCEPT")
    if not callable(algorithm):
        raise EgcRefused("CHECKSUM_ALGORITHM_UNVERIFIED")
    return _verified(packet, decision.length, algorithm)


class EgcAssembler:
    """Accepted SafetyNET descriptors and multiframe messages, bounded in memory.

    Call begin_frame(n) with the TDM frame counter, then feed() that frame's
    descriptors in order; call lost() for every descriptor that could not be
    decoded. feed() returns a list with at most one complete accepted message.
    Only one multiframe message is open at a time (<= max_message_bytes). It
    continues only as the first descriptor of the frame right after the frame of
    its last fragment; any other packet, a frame gap, a loss or an overrun
    discards it (zero-filled, counted in discarded). last_reason is a stable code.
    """
    def __init__(self, checksum, *, max_message_bytes=16384, max_fragments=32):
        if not callable(checksum):
            raise EgcRefused("CHECKSUM_ALGORITHM_UNVERIFIED")
        if (type(max_message_bytes) is not int or not 8 <= max_message_bytes <= 65538 or
                type(max_fragments) is not int or not 2 <= max_fragments <= 256):
            raise EgcRefused("ASSEMBLER_LIMITS_INVALID")
        self._checksum, self._max_bytes, self._max_fragments = checksum, max_message_bytes, max_fragments
        self._buffer, self._expected, self._fragments = None, 0, 0
        self._frame, self._position, self._open_frame = None, 0, None  # current frame, index in it, frame of the last fragment
        self.last_reason, self.discarded = None, 0  # discarded: incomplete multiframe messages

    @property
    def open(self):
        return self._buffer is not None

    def _discard(self):
        if self._buffer is not None:
            self._buffer[:] = bytes(len(self._buffer))
            self._buffer, self._open_frame = None, None
            return True
        return False

    def _drop(self, reason):
        self.discarded += self._discard()
        self.last_reason = reason
        return []

    def begin_frame(self, number):
        """Start of one demodulated TDM frame. Only n+1 after the open message's frame n keeps it
        open; a gap, a repeated, decreasing or wrapped number closes it (no wrap is assumed)."""
        if type(number) is not int or not 0 <= number < FRAME_NUMBER_LIMIT:
            self._frame, self._position = None, 0
            self._drop("FRAME_NUMBER_INVALID")
            return
        if self._buffer is not None and number != self._open_frame + 1:
            self._drop("FRAME_GAP")
        self._frame, self._position = number, 0

    def lost(self):
        """A descriptor (or the rest of the frame) could not be decoded: the open message closes."""
        self._position += 1  # whatever follows is not the frame's first descriptor
        self._drop("DESCRIPTOR_LOST")

    def feed(self, packet):
        position, self._position = self._position, self._position + 1
        size, first = _size(packet), _byte(packet, 0)
        if size and first is not None and first & 0x80 and (first & 0x3F) == MULTIFRAME_CONTINUATION:
            return self._continue(packet, size, first, position)
        self.discarded += self._discard()
        decision = classify(packet)
        if not decision.accept:  # no checksum and no copy for a rejected packet
            return self._drop(decision.reason)
        if size != decision.length:
            return self._drop("LENGTH_MISMATCH")
        if max(decision.length, decision.inner_length or 0) > self._max_bytes:
            return self._drop("MESSAGE_SIZE_LIMIT")
        if (decision.inner_length is not None and self._frame is None
                and decision.inner_length > decision.length - CHECKSUM_BYTES - 2):
            return self._drop("FRAME_BOUNDARY_MISSING")  # could never continue: no checksum, no copy
        if not _verified(packet, decision.length, self._checksum):
            return self._drop("CHECKSUM_MISMATCH")
        self.last_reason = decision.reason
        if decision.inner_length is None:
            return [bytes(packet[:decision.length])]
        self._buffer = bytearray(packet[2:decision.length - CHECKSUM_BYTES])
        self._expected, self._fragments, self._open_frame = decision.inner_length, 1, self._frame
        return self._complete()

    def _continue(self, packet, size, first, position):
        if self._buffer is None:  # after a rejected start, or none: dropped unread
            self.last_reason = "CONTINUATION_WITHOUT_ACCEPTED_START"
            return []
        if self._frame is None:
            return self._drop("FRAME_BOUNDARY_MISSING")
        if position != 0 or self._frame != self._open_frame + 1:
            return self._drop("UNEXPECTED_FRAGMENT")  # not the first descriptor of the next frame
        if _class(first) == LONG:
            return self._drop("MULTIFRAME_LONG_FORM_UNVERIFIED")
        length = _length(packet, 0, MEDIUM, size)
        if isinstance(length, str) or length < 2 + 1 + CHECKSUM_BYTES:
            return self._drop("LENGTH_TOO_SMALL")
        if size != length:
            return self._drop("LENGTH_MISMATCH")
        self._fragments += 1
        if self._fragments > self._max_fragments:
            return self._drop("FRAGMENT_LIMIT")
        if length - CHECKSUM_BYTES - 2 > self._expected - len(self._buffer):
            return self._drop("LENGTH_MISMATCH")  # overruns the declared inner length: not this message
        if not _verified(packet, length, self._checksum):
            return self._drop("CHECKSUM_MISMATCH")
        self._buffer.extend(packet[2:length - CHECKSUM_BYTES])
        self._open_frame = self._frame
        self.last_reason = "ACCEPT_SAFETYNET"
        return self._complete()

    def _complete(self):
        if len(self._buffer) < self._expected:
            return []
        if len(self._buffer) > self._expected:
            return self._drop("LENGTH_MISMATCH")
        message = bytes(self._buffer)
        self._discard()
        if not _verified(message, len(message), self._checksum):  # the reassembled inner descriptor itself
            self.discarded += 1
            self.last_reason = "CHECKSUM_MISMATCH"
            return []
        return [message]


class NcsWatchdog:
    """Stops demodulation after n_frames consecutive frames without an NCS header.

    Latched: a stopped watchdog never restarts; a new carrier selection creates a
    new one. Anything other than True counts as a missing header.
    """
    def __init__(self, n_frames):
        if type(n_frames) is not int or not 1 <= n_frames <= 100000:
            raise EgcRefused("NCS_WATCHDOG_N_INVALID")
        self._limit, self._missed, self._stopped = n_frames, 0, False

    @property
    def stopped(self):
        return self._stopped

    def frame(self, ncs_header_seen):
        """Record one demodulated frame; True while demodulation may continue."""
        if self._stopped:
            return False
        self._missed = 0 if ncs_header_seen is True else self._missed + 1
        if self._missed >= self._limit:
            self._stopped = True
        return not self._stopped
