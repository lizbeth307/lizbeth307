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
    # offsets where a u16 LE length field was detected
    length_field_offset: int | None = None


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


def _looks_like_u16_length(messages: list[bytes], offset: int) -> float:
    """Score how well bytes[offset:offset+2] explain trailing payload size."""
    if offset + 2 > min(len(m) for m in messages):
        return 0.0
    hits = 0
    total = 0
    for m in messages:
        if offset + 2 >= len(m):
            continue
        declared = m[offset] | (m[offset + 1] << 8)
        # payload between length field and a trailing checksum byte
        trailing = len(m) - (offset + 2) - 1
        total += 1
        if declared == trailing:
            hits += 1
        elif declared == len(m) - (offset + 2):
            hits += 1
    return hits / total if total else 0.0


def discover_format(messages: list[bytes]) -> FormatHypothesis:
    if not messages:
        raise ValueError("need at least one message")

    min_len = min(map(len, messages))
    max_len = max(map(len, messages))

    # Scan for a u16le length field inside the shared minimum prefix.
    length_offset: int | None = None
    best_len_score = 0.0
    for off in range(0, max(1, min_len - 1)):
        score = _looks_like_u16_length(messages, off)
        if score > best_len_score:
            best_len_score = score
            length_offset = off
    if best_len_score < 0.8:
        length_offset = None

    # Header ends right after the length field (or at min_len if none found).
    if length_offset is not None:
        header_end = length_offset + 2
    else:
        header_end = min_len

    fields: list[FieldHypothesis] = []
    i = 0
    field_idx = 0
    while i < header_end:
        if length_offset is not None and i == length_offset:
            fields.append(
                FieldHypothesis(
                    name=f"length_{field_idx}",
                    offset=i,
                    size=2,
                    kind="length",
                    notes=f"u16le length score={best_len_score:.2f}",
                )
            )
            i += 2
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
