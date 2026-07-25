"""Cluster messages by opcode / type byte for per-type AST discovery."""

from __future__ import annotations

from collections import defaultdict

from .align import discover_format
from .pipeline import discover_and_parse
from .serde import format_to_dict


def cluster_messages(
    messages: list[bytes],
    offset: int = 0,
    *,
    min_cluster: int = 2,
) -> dict[int, list[bytes]]:
    buckets: dict[int, list[bytes]] = defaultdict(list)
    for m in messages:
        if len(m) > offset:
            buckets[m[offset]].append(m)
    return {k: v for k, v in buckets.items() if len(v) >= min_cluster}


def best_cluster_offset(messages: list[bytes], scan: int = 4) -> int | None:
    """Pick offset with most distinct clusters (message types)."""
    if not messages:
        return None
    best_off, best_score = None, 0
    for off in range(min(scan, min(len(m) for m in messages))):
        clusters = cluster_messages(messages, off, min_cluster=2)
        if len(clusters) > best_score:
            best_score = len(clusters)
            best_off = off
    return best_off if best_score >= 2 else None


def discover_clustered_formats(
    messages: list[bytes],
    offset: int | None = None,
) -> dict[int, dict]:
    off = offset if offset is not None else (best_cluster_offset(messages) or 0)
    out: dict[int, dict] = {}
    for opcode, group in sorted(cluster_messages(messages, off).items()):
        fmt = discover_format(group)
        result = discover_and_parse(group)
        out[opcode] = {
            "opcode": opcode,
            "count": len(group),
            "format": format_to_dict(fmt),
            "parse_success": round(result.success_rate, 3),
            "fields": [f.name + ":" + f.kind + "@" + str(f.offset) for f in fmt.fields[:8]],
        }
    return out
