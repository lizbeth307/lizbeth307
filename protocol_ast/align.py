"""Consensus field discovery via column statistics (Discoverer / PI style).

For a set of messages of equal or similar length we look at each byte offset:
  - fixed: almost always the same value (magic, version cluster)
  - enum: small set of values
  - length-like: value correlates with remaining / payload size
  - variable: high entropy / many distinct values
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Literal


FieldKind = Literal["fixed", "enum", "length", "variable", "payload"]
LengthEndian = Literal["le", "be"]
LengthWidth = Literal["u16", "u32", "varint"]


@dataclass
class FieldHypothesis:
    name: str
    offset: int
    size: int
    kind: FieldKind
    values: tuple[int, ...] = ()
    notes: str = ""


@dataclass
class FormatHypothesis:
    fields: list[FieldHypothesis]
    min_len: int
    max_len: int
    length_field_offset: int | None = None
    length_endian: LengthEndian = "le"
    length_width: LengthWidth = "u16"


def _column_stats(messages: list[bytes], offset: int) -> tuple[Counter[int], float]:
    """Return value histogram and dominance ratio of the most common byte."""
    vals = Counter()
    for m in messages:
        if offset < len(m):
            vals[m[offset]] += 1
    if not vals:
        return vals, 0.0
    dominance = vals.most_common(1)[0][1] / sum(vals.values())
    return vals, dominance


def _read_u16(data: bytes, offset: int, endian: LengthEndian) -> int:
    if endian == "le":
        return data[offset] | (data[offset + 1] << 8)
    return (data[offset] << 8) | data[offset + 1]


def _score_u16_length(
    messages: list[bytes],
    offset: int,
    endian: LengthEndian,
) -> float:
    """Score u16 length field; accepts ±1 byte trailer (checksum)."""
    if offset + 2 > min(len(m) for m in messages):
        return 0.0
    hits = 0
    total = 0
    for m in messages:
        if offset + 2 >= len(m):
            continue
        total += 1
        declared = _read_u16(m, offset, endian)
        rest = len(m) - (offset + 2)
        if declared == rest or declared == rest - 1:
            hits += 1
    return hits / total if total else 0.0


def _read_u32(data: bytes, offset: int, endian: LengthEndian) -> int:
    if endian == "le":
        return (
            data[offset]
            | (data[offset + 1] << 8)
            | (data[offset + 2] << 16)
            | (data[offset + 3] << 24)
        )
    return (
        (data[offset] << 24)
        | (data[offset + 1] << 16)
        | (data[offset + 2] << 8)
        | data[offset + 3]
    )


def _read_varint(data: bytes, off: int) -> tuple[int, int] | None:
    if off >= len(data):
        return None
    first = data[off]
    prefix = 1 << (first >> 6)
    if off + prefix > len(data):
        return None
    if prefix == 1:
        return first & 0x3F, 1
    if prefix == 2:
        return ((first & 0x3F) << 8) | data[off + 1], 2
    if prefix == 4:
        v = 0
        for i in range(1, 4):
            v = (v << 8) | data[off + i]
        return (first & 0x3F) << 24 | v, 4
    v = 0
    for i in range(1, 8):
        v = (v << 8) | data[off + i]
    return (first & 0x3F) << 56 | v, 8


def _score_u32_length(
    messages: list[bytes],
    offset: int,
    endian: LengthEndian,
) -> float:
    if offset + 4 > min(len(m) for m in messages):
        return 0.0
    hits = total = 0
    for m in messages:
        if offset + 4 >= len(m):
            continue
        total += 1
        declared = _read_u32(m, offset, endian)
        rest = len(m) - (offset + 4)
        if declared == rest or declared == rest - 1:
            hits += 1
    return hits / total if total else 0.0


def _score_varint_length(messages: list[bytes], offset: int) -> float:
    hits = total = 0
    for m in messages:
        if offset >= len(m):
            continue
        parsed = _read_varint(m, offset)
        if not parsed:
            continue
        total += 1
        val, used = parsed
        rest = len(m) - offset - used
        if val == rest or val in (rest - 1, rest - 2):
            hits += 1
    return hits / total if total else 0.0


def _find_length_field(
    messages: list[bytes],
    min_len: int,
) -> tuple[int | None, LengthEndian, LengthWidth, float]:
    best_off: int | None = None
    best_endian: LengthEndian = "le"
    best_width: LengthWidth = "u16"
    best_score = 0.0
    width_pri = {"u16": 0, "u32": 1, "varint": 2}

    def _better(score: float, width: LengthWidth, off: int) -> bool:
        nonlocal best_score, best_off, best_endian, best_width
        if score > best_score:
            return True
        if score == best_score and score >= 0.8:
            if width_pri[width] < width_pri[best_width]:
                return True
            if width_pri[width] == width_pri[best_width] and best_off is not None and off > best_off:
                return True
        return False

    for off in range(0, max(1, min_len - 1)):
        for endian in ("le", "be"):
            score = _score_u16_length(messages, off, endian)
            if _better(score, "u16", off):
                best_score, best_off, best_endian, best_width = score, off, endian, "u16"
            score32 = _score_u32_length(messages, off, endian)
            if _better(score32, "u32", off):
                best_score, best_off, best_endian, best_width = score32, off, endian, "u32"
        vscore = _score_varint_length(messages, off)
        if _better(vscore, "varint", off):
            best_score, best_off, best_endian, best_width = vscore, off, "le", "varint"
    if best_score < 0.8:
        return None, "le", "u16", 0.0
    return best_off, best_endian, best_width, best_score


def discover_format(messages: list[bytes]) -> FormatHypothesis:
    if not messages:
        raise ValueError("need at least one message")

    min_len = min(map(len, messages))
    max_len = max(map(len, messages))

    # Scan for a u16 length field (LE or BE) inside the shared minimum prefix.
    length_offset, length_endian, length_width, best_len_score = _find_length_field(messages, min_len)

    if length_offset is not None:
        header_end = length_offset + {"u16": 2, "u32": 4, "varint": 1}[length_width]
        if length_width == "varint":
            # scan max varint width in corpus
            max_used = 1
            for m in messages:
                p = _read_varint(m, length_offset)
                if p:
                    max_used = max(max_used, p[1])
            header_end = length_offset + max_used
    else:
        header_end = min_len

    fields: list[FieldHypothesis] = []
    i = 0
    field_idx = 0
    while i < header_end:
        if length_offset is not None and i == length_offset:
            lsize = {"u16": 2, "u32": 4, "varint": header_end - length_offset}[length_width]
            fields.append(
                FieldHypothesis(
                    name=f"length_{field_idx}",
                    offset=i,
                    size=lsize,
                    kind="length",
                    notes=f"{length_width}{length_endian} length score={best_len_score:.2f}",
                )
            )
            i = header_end
            field_idx += 1
            continue

        vals, dominance = _column_stats(messages, i)
        top = vals.most_common(1)[0]
        # Near-constant column → fixed field (merge runs).
        if dominance >= 0.9:
            start = i
            fixed_bytes = [top[0]]
            j = i + 1
            while j < header_end and not (
                length_offset is not None and j == length_offset
            ):
                vj, dj = _column_stats(messages, j)
                tj = vj.most_common(1)[0]
                if dj >= 0.9:
                    fixed_bytes.append(tj[0])
                    j += 1
                else:
                    break
            fields.append(
                FieldHypothesis(
                    name=f"fixed_{field_idx}",
                    offset=start,
                    size=j - start,
                    kind="fixed",
                    values=tuple(fixed_bytes),
                    notes="constant/near-constant prefix",
                )
            )
            i = j
            field_idx += 1
            continue

        if len(vals) <= 8:
            fields.append(
                FieldHypothesis(
                    name=f"enum_{field_idx}",
                    offset=i,
                    size=1,
                    kind="enum",
                    values=tuple(sorted(vals)),
                    notes=f"small domain size={len(vals)}",
                )
            )
            i += 1
            field_idx += 1
            continue

        fields.append(
            FieldHypothesis(
                name=f"byte_{field_idx}",
                offset=i,
                size=1,
                kind="variable",
                notes=f"dominance={dominance:.2f}",
            )
        )
        i += 1
        field_idx += 1

    payload_off = header_end

    # Detect a trailing checksum: last byte == sum(payload) & 0xFF.
    trailer_size = 0
    ok = 0
    checked = 0
    for m in messages:
        if len(m) <= payload_off:
            continue
        payload = m[payload_off:-1]
        check = m[-1]
        checked += 1
        if (sum(payload) & 0xFF) == check:
            ok += 1
    if checked and ok / checked >= 0.8:
        trailer_size = 1

    fields.append(
        FieldHypothesis(
            name="payload",
            offset=payload_off,
            size=-1,  # dynamic
            kind="payload",
            notes="variable-length body",
        )
    )
    if trailer_size:
        fields.append(
            FieldHypothesis(
                name="checksum",
                offset=-1,
                size=1,
                kind="fixed",
                notes="trailing checksum byte (sum payload & 0xFF)",
            )
        )

    return FormatHypothesis(
        fields=fields,
        min_len=min_len,
        max_len=max_len,
        length_field_offset=length_offset,
        length_endian=length_endian,
        length_width=length_width,
    )


def alignment_agreement(messages: list[bytes], limit: int | None = None) -> list[float]:
    """Per-offset fraction of messages agreeing with the mode (debug aid)."""
    n = min(map(len, messages)) if messages else 0
    if limit is not None:
        n = min(n, limit)
    scores = []
    for off in range(n):
        _, dominance = _column_stats(messages, off)
        scores.append(dominance)
    return scores


def mean_agreement(messages: list[bytes], limit: int = 8) -> float:
    scores = alignment_agreement(messages, limit=limit)
    return mean(scores) if scores else 0.0
