"""Build minimal PCAP files for tests (no libpcap dependency)."""

from __future__ import annotations

import struct
import time
from pathlib import Path


def write_pcap(path: str | Path, frames: list[bytes], link_type: int = 1) -> None:
    """Write classic PCAP (LE) with Ethernet link type."""
    path = Path(path)
    hdr = struct.pack(
        "<IHHiIII",
        0xA1B2C3D4,
        2,
        4,
        0,
        0,
        65535,
        link_type,
    )
    chunks = [hdr]
    ts = int(time.time())
    for frame in frames:
        rec = struct.pack("<IIII", ts, 0, len(frame), len(frame))
        chunks.append(rec)
        chunks.append(frame)
    path.write_bytes(b"".join(chunks))


def ethernet_ipv4_udp(
    src_ip: tuple[int, ...],
    dst_ip: tuple[int, ...],
    sport: int,
    dport: int,
    payload: bytes,
) -> bytes:
    """Build Ethernet II + IPv4 + UDP frame."""
    udp_len = 8 + len(payload)
    ip_len = 20 + udp_len
    total = 14 + ip_len

    eth = struct.pack(
        "!6s6sH",
        b"\x00" * 6,
        b"\x00" * 6,
        0x0800,
    )
    ip = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,
        0,
        ip_len,
        0x1234,
        0,
        64,
        17,
        0,
        bytes(src_ip),
        bytes(dst_ip),
    )
    udp = struct.pack("!HHHH", sport, dport, udp_len, 0)
    return eth + ip + udp + payload
