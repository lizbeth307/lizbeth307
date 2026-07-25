"""Unified PCAP / PCAPNG packet iterator."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Iterator

PCAP_MAGIC_LE = 0xA1B2C3D4
PCAP_MAGIC_BE = 0xD4C3B2A1
PCAPNG_MAGIC = 0x0A0D0D0A

# PCAPNG block types
BT_EPB = 0x00000006
BT_IDB = 0x00000001


def _iter_classic_pcap(data: bytes, offset: int, endian: str) -> Iterator[tuple[int, bytes]]:
    link = struct.unpack(endian + "IHHiIII", data[:24])[6]
    off = 24
    while off + 16 <= len(data):
        _, _, caplen, _ = struct.unpack(endian + "IIII", data[off : off + 16])
        off += 16
        yield link, data[off : off + caplen]
        off += caplen


def _iter_pcapng(data: bytes) -> Iterator[tuple[int, bytes]]:
    if len(data) < 12:
        return
    off = 0
    link_type = 1  # default ethernet
    while off + 8 <= len(data):
        block_type, block_len = struct.unpack("<II", data[off : off + 8])
        if block_len < 12 or off + block_len > len(data):
            break
        body = data[off + 8 : off + block_len - 4]
        if block_type == BT_IDB and len(body) >= 2:
            link_type = struct.unpack("<H", body[:2])[0]
        elif block_type == BT_EPB and len(body) >= 20:
            caplen = struct.unpack("<I", body[12:16])[0]
            pkt = body[20 : 20 + caplen]
            if pkt:
                yield link_type, pkt
        off += block_len


def iter_packets(path: str | Path) -> Iterator[tuple[int, bytes]]:
    """Yield (link_type, frame) from classic PCAP or PCAPNG."""
    data = Path(path).read_bytes()
    if len(data) < 4:
        raise ValueError("file too small")
    magic = struct.unpack("<I", data[:4])[0]
    if magic == PCAPNG_MAGIC:
        yield from _iter_pcapng(data)
        return
    endian = "<"
    if magic in (PCAP_MAGIC_BE, 0x4D3CB2A1):
        endian = ">"
    elif magic not in (PCAP_MAGIC_LE, 0xA1B23C4D):
        raise ValueError(f"unsupported capture magic: {magic:#x}")
    yield from _iter_classic_pcap(data, 0, endian)
