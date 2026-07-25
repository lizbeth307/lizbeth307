"""TCP stream reassembly + TLS record splitting."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field


@dataclass
class TcpSegment:
    seq: int
    payload: bytes


@dataclass
class TcpFlow:
    key: str
    segments: list[TcpSegment] = field(default_factory=list)

    def feed(self, seq: int, payload: bytes) -> None:
        if not payload:
            return
        self.segments.append(TcpSegment(seq, payload))

    def reassemble(self) -> bytes:
        if not self.segments:
            return b""
        ordered = sorted(self.segments, key=lambda s: s.seq)
        out = bytearray()
        cursor = ordered[0].seq
        for seg in ordered:
            if seg.seq > cursor:
                # прогалина — все одно склеюємо best-effort
                cursor = seg.seq
            start = cursor - seg.seq
            if start < 0:
                chunk = seg.payload[-start:]
                cursor += len(chunk)
            else:
                chunk = seg.payload[start:]
                cursor = seg.seq + len(seg.payload)
            out.extend(chunk)
        return bytes(out)


def parse_tcp_header(tcp: bytes) -> tuple[int, int, int, bytes] | None:
    if len(tcp) < 20:
        return None
    sport, dport, seq, _ack = struct.unpack(">HHII", tcp[:12])
    offset = ((tcp[12] >> 4) & 0x0F) * 4
    if len(tcp) < offset:
        return None
    return sport, dport, seq, tcp[offset:]


def iter_tls_records(stream: bytes) -> list[bytes]:
    """Розрізає TCP byte stream на TLS records."""
    records: list[bytes] = []
    offset = 0
    while offset + 5 <= len(stream):
        ctype = stream[offset]
        if ctype not in (20, 21, 22, 23, 24, 25):
            break
        _ver, length = struct.unpack(">HH", stream[offset + 1 : offset + 5])
        if length > 65535 or length == 0:
            break
        end = offset + 5 + length
        if end > len(stream):
            break
        records.append(stream[offset:end])
        offset = end
    return records


def dedupe_messages(messages: list[bytes]) -> list[bytes]:
    seen: set[bytes] = set()
    out: list[bytes] = []
    for m in messages:
        if m in seen or len(m) < 1:
            continue
        seen.add(m)
        out.append(m)
    return out


def enrich_tcp_flow_payloads(
    payloads: list[bytes],
    *,
    tls_split: bool = True,
) -> list[bytes]:
    """Склеює TCP сегменти (якщо є seq у synthetic form) або ріже TLS."""
    if not payloads:
        return []
    # Спроба: якщо payloads виглядають як TLS records вже — лишаємо
    tls_records: list[bytes] = []
    for p in payloads:
        if tls_split:
            recs = iter_tls_records(p)
            if recs:
                tls_records.extend(recs)
                continue
        tls_records.append(p)
    return dedupe_messages(tls_records)
