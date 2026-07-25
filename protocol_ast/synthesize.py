"""Synthetic 'unknown' protocol used as a verification oracle.

Wire format (little-endian):
  magic:u16 = 0xCAFE
  version:u8
  msg_type:u8          # 1=PING, 2=DATA, 3=ACK
  flags:u8
  length:u16           # payload byte length
  payload:bytes[length]
  checksum:u8          # sum(payload) & 0xFF

This schema is the ground truth. The discovery pipeline must NOT receive it —
only raw byte messages — and should recover a tree close to this structure.
"""

from __future__ import annotations

import random
import struct
from dataclasses import dataclass
from typing import Iterable


MAGIC = 0xCAFE
TYPE_PING = 1
TYPE_DATA = 2
TYPE_ACK = 3


@dataclass(frozen=True)
class GroundTruthMessage:
    version: int
    msg_type: int
    flags: int
    payload: bytes
    raw: bytes


def _checksum(payload: bytes) -> int:
    return sum(payload) & 0xFF


def encode(version: int, msg_type: int, flags: int, payload: bytes) -> bytes:
    body = struct.pack("<HBBB H", MAGIC, version, msg_type, flags, len(payload))
    body += payload
    body += bytes([_checksum(payload)])
    return body


def make_corpus(n: int = 40, seed: int = 42) -> list[GroundTruthMessage]:
    rng = random.Random(seed)
    out: list[GroundTruthMessage] = []
    for i in range(n):
        version = rng.choice([1, 1, 1, 2])
        msg_type = rng.choice([TYPE_PING, TYPE_DATA, TYPE_DATA, TYPE_ACK])
        flags = rng.randrange(0, 8)
        if msg_type == TYPE_PING:
            payload = b""
        elif msg_type == TYPE_ACK:
            payload = struct.pack("<I", rng.randrange(0, 10_000))
        else:
            size = rng.choice([4, 8, 12, 16, 24])
            payload = bytes(rng.randrange(0, 256) for _ in range(size))
        raw = encode(version, msg_type, flags, payload)
        out.append(
            GroundTruthMessage(
                version=version,
                msg_type=msg_type,
                flags=flags,
                payload=payload,
                raw=raw,
            )
        )
    return out


def raw_messages(corpus: Iterable[GroundTruthMessage]) -> list[bytes]:
    return [m.raw for m in corpus]
