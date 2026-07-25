"""Protocol-agnostic frame splitters — discover structure from bytes only."""

from __future__ import annotations

from collections import Counter

from .align import discover_format
from .deep_decode import parse_quic_packet, split_tls_records
from .http2 import looks_like_http1, split_http2_frames


def split_length_prefixed(messages: list[bytes]) -> tuple[str, list[bytes]] | None:
    """Split on discovered u16/u32/varint length field."""
    fmt = discover_format(messages)
    if fmt.length_field_offset is None:
        return None
    off = fmt.length_field_offset
    frames: list[bytes] = []
    ok = 0
    for m in messages:
        pos = 0
        good = True
        while pos < len(m):
            if fmt.length_width == "u32" and pos + 4 > len(m):
                good = False
                break
            if fmt.length_width == "u16" and pos + 2 > len(m):
                good = False
                break
            if fmt.length_width == "u16":
                ln = (
                    m[pos + off] | (m[pos + off + 1] << 8)
                    if fmt.length_endian == "le"
                    else (m[pos + off] << 8) | m[pos + off + 1]
                )
                hdr = off + 2
            elif fmt.length_width == "u32":
                from .align import _read_u32

                ln = _read_u32(m, pos + off, fmt.length_endian)
                hdr = off + 4
            else:
                from .align import _read_varint

                p = _read_varint(m, pos + off)
                if not p:
                    good = False
                    break
                ln, used = p
                hdr = off + used
            end = pos + hdr + ln
            if end > len(m):
                good = False
                break
            frames.append(m[pos:end])
            pos = end
        if good and pos == len(m) and frames:
            ok += 1
    rate = ok / len(messages) if messages else 0
    if rate >= 0.6 and frames and len(frames) >= 2:
        return f"length_{fmt.length_width}@{off}", frames
    return None


def all_single_tls_records(messages: list[bytes]) -> bool:
    for m in messages:
        if len(m) < 5:
            return False
        if m[0] not in range(20, 26) or m[1] != 3:
            return False
        ln = (m[3] << 8) | m[4]
        if 5 + ln != len(m):
            return False
    return True


def split_tls_handshake_bodies(messages: list[bytes]) -> tuple[str, list[bytes]] | None:
    """Peel Handshake records (0x16) from a mixed TLS stream — not all-or-nothing."""
    if all_single_tls_records(messages):
        bodies = [m[5:] for m in messages if len(m) > 5 and m[0] == 0x16]
        if len(bodies) >= 2:
            return "tls_handshake", bodies
    # Mixed stream: extract handshake bodies even if app-data dominates
    bodies = []
    for m in messages:
        if len(m) >= 6 and m[0] == 0x16 and m[1] == 3:
            ln = (m[3] << 8) | m[4]
            if 5 + ln == len(m) or (5 + ln <= len(m) and ln > 0):
                bodies.append(m[5 : 5 + ln] if 5 + ln <= len(m) else m[5:])
        elif len(m) > 4 and m[0] in (0x01, 0x02, 0x0B):  # already a handshake body
            bodies.append(m)
    if len(bodies) >= 2:
        return "tls_handshake", bodies
    return None


def peel_tls_handshake_records(messages: list[bytes]) -> list[bytes]:
    """Return only Handshake TLS records (full records, not bodies)."""
    out: list[bytes] = []
    for m in messages:
        if len(m) >= 6 and m[0] == 0x16 and m[1] == 3:
            ln = (m[3] << 8) | m[4]
            if 5 + ln <= len(m):
                out.append(m[: 5 + ln])
            else:
                out.append(m)
    return out


def peel_tls_appdata_records(messages: list[bytes]) -> list[bytes]:
    out: list[bytes] = []
    for m in messages:
        if len(m) >= 6 and m[0] == 0x17 and m[1] == 3:
            ln = (m[3] << 8) | m[4]
            if 5 + ln <= len(m):
                out.append(m[: 5 + ln])
            else:
                out.append(m)
    return out


def split_tls_record_frames(messages: list[bytes]) -> tuple[str, list[bytes]] | None:
    rate, frames = split_tls_records(messages)
    if rate >= 0.6 and len(frames) >= 2:
        return "tls_record", frames
    return None


def split_quic_packets(messages: list[bytes]) -> tuple[str, list[bytes]] | None:
    """Detect QUIC by byte pattern — no port label required."""
    long_valid = sum(
        1
        for m in messages
        if len(m) >= 5 and (m[0] & 0xC0) == 0xC0 and parse_quic_packet(m, permit_short=False)
    )
    permit_short = long_valid >= 2
    frames = [m for m in messages if parse_quic_packet(m, permit_short=permit_short)]
    if len(frames) >= max(2, len(messages) // 2) and len(frames) < len(messages):
        return "quic_packet", frames
    return None


def split_fixed_size(messages: list[bytes]) -> tuple[str, list[bytes]] | None:
    if len(messages) < 3:
        return None
    lens = Counter(len(m) for m in messages)
    size, count = lens.most_common(1)[0]
    if size < 8 or count < len(messages) * 0.9:
        return None
    return f"fixed_{size}", messages


def discover_splitter(
    messages: list[bytes],
    *,
    depth: int = 0,
) -> tuple[str, list[bytes]] | None:
    """Pick best universal splitter for this signal layer."""
    if depth > 0:
        hs = split_tls_handshake_bodies(messages)
        if hs:
            return hs
        h2 = split_http2_frames(messages)
        if h2:
            return h2
        if looks_like_http1(messages):
            return "http1", messages
    for fn in (
        split_tls_record_frames,
        split_http2_frames,
        split_quic_packets,
        split_length_prefixed,
        split_fixed_size,
    ):
        result = fn(messages)
        if result:
            return result
    return None
