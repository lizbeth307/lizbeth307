"""TCP stream reassembly from PCAP segments (seq-aware)."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

from .stream_enrich import dedupe_messages, iter_tls_records


@dataclass
class TcpSegment:
    seq: int
    payload: bytes


@dataclass
class TcpSubFlow:
    sport: int
    dport: int
    segments: list[TcpSegment] = field(default_factory=list)

    def feed(self, seq: int, payload: bytes) -> None:
        if payload:
            self.segments.append(TcpSegment(seq, payload))

    def reassemble(self) -> bytes:
        if not self.segments:
            return b""
        ordered = sorted(self.segments, key=lambda s: s.seq)
        out = bytearray()
        cursor: int | None = None
        for seg in ordered:
            if cursor is None:
                cursor = seg.seq
            if seg.seq > cursor:
                cursor = seg.seq
            skip = max(0, cursor - seg.seq)
            chunk = seg.payload[skip:]
            if not chunk:
                continue
            out.extend(chunk)
            cursor = seg.seq + skip + len(chunk)
        return bytes(out)


def parse_tcp_segment(tcp: bytes) -> tuple[int, int, int, bytes] | None:
    """Return sport, dport, seq, payload."""
    if len(tcp) < 20:
        return None
    sport, dport, seq = struct.unpack(">HHI", tcp[:8])
    off = ((tcp[12] >> 4) & 0x0F) * 4
    if len(tcp) < off:
        return None
    return sport, dport, seq, tcp[off:]


def reassemble_tcp_payloads(
    segments: list[tuple[int, int, int, bytes]],
    *,
    tls_split: bool = True,
) -> list[bytes]:
    """Group segments by direction, reassemble, optionally split TLS records."""
    if not segments:
        return []
    subflows: dict[tuple[int, int], TcpSubFlow] = {}
    for sport, dport, seq, payload in segments:
        key = (sport, dport)
        if key not in subflows:
            subflows[key] = TcpSubFlow(sport, dport)
        subflows[key].feed(seq, payload)

    messages: list[bytes] = []
    for sf in subflows.values():
        stream = sf.reassemble()
        if not stream:
            continue
        if tls_split:
            recs = iter_tls_records(stream)
            if recs:
                messages.extend(recs)
                continue
        messages.append(stream)
    return dedupe_messages(messages)
