"""Recursive blind analysis v2 — nested AST without port labels."""

from __future__ import annotations

from dataclasses import dataclass, field

from .align import discover_format
from .cluster import best_cluster_offset, discover_clustered_formats
from .deep_decode import deep_analyze_flow, parse_quic_packet, split_tls_records
from .pipeline import discover_and_parse
from .serde import format_to_dict


@dataclass
class NestedLayer:
    label: str
    depth: int
    messages: int
    entropy: str
    format: dict
    parse_success: float
    splitter: str | None = None
    clusters: dict | None = None
    deep: dict | None = None
    children: list["NestedLayer"] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "depth": self.depth,
            "messages": self.messages,
            "entropy": self.entropy,
            "splitter": self.splitter,
            "format": self.format,
            "parse_success": self.parse_success,
            "clusters": self.clusters,
            "deep": self.deep,
            "children": [c.to_dict() for c in self.children],
        }


def _entropy_label(messages: list[bytes]) -> str:
    if not messages:
        return "empty"
    ratio = len(set(b for p in messages[:10] for b in p[:16])) / max(
        1, min(16, min(len(p) for p in messages))
    )
    return "high" if ratio > 0.85 else "structured"


def _split_length_prefixed(messages: list[bytes]) -> tuple[str, list[bytes]] | None:
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
    if rate >= 0.6 and frames:
        return f"length_{fmt.length_width}@{off}", frames
    return None


def _all_single_tls_records(messages: list[bytes]) -> bool:
    for m in messages:
        if len(m) < 5:
            return False
        if m[0] not in range(20, 26) or m[1] != 3:
            return False
        ln = (m[3] << 8) | m[4]
        if 5 + ln != len(m):
            return False
    return True


def _is_quic_flow(flow: str) -> bool:
    u = flow.upper()
    return u.startswith("UDP") and u.endswith(":443")


def _pick_splitter(messages: list[bytes], *, depth: int = 0, flow: str = "") -> tuple[str, list[bytes]] | None:
    if depth > 0 and _all_single_tls_records(messages):
        bodies = [m[5:] for m in messages if len(m) > 5 and m[0] == 0x16]
        if len(bodies) >= 2:
            return "tls_handshake", bodies
        return None
    tls_rate, tls_frames = split_tls_records(messages)
    if tls_rate >= 0.6 and tls_frames and len(tls_frames) < len(messages):
        return "tls_record", tls_frames
    quic_frames = [
        m
        for m in messages
        if parse_quic_packet(m, permit_short=_is_quic_flow(flow))
    ]
    if _is_quic_flow(flow) and len(quic_frames) >= max(2, len(messages) // 2) and len(quic_frames) < len(messages):
        return "quic_packet", quic_frames
    lp = _split_length_prefixed(messages)
    if lp and len(lp[1]) < len(messages):
        return lp
    return None


def recursive_blind_analyze(
    flow: str,
    messages: list[bytes],
    *,
    depth: int = 0,
    max_depth: int = 3,
    label: str | None = None,
) -> NestedLayer:
    label = label or flow
    fmt = discover_format(messages)
    result = discover_and_parse(messages)
    layer = NestedLayer(
        label=label,
        depth=depth,
        messages=len(messages),
        entropy=_entropy_label(messages),
        format=format_to_dict(fmt),
        parse_success=round(result.success_rate, 3),
    )

    if depth == 0:
        layer.deep = deep_analyze_flow(flow, messages)
        cl_off = best_cluster_offset(messages)
        if cl_off is not None:
            layer.clusters = discover_clustered_formats(messages, cl_off)

    if depth >= max_depth or len(messages) < 2:
        return layer

    split = _pick_splitter(messages, depth=depth, flow=flow)
    if not split:
        return layer

    splitter_name, inner = split
    layer.splitter = splitter_name
    if len(inner) < 2:
        return layer

    child = recursive_blind_analyze(
        flow,
        inner,
        depth=depth + 1,
        max_depth=max_depth,
        label=f"{label}/{splitter_name}",
    )
    layer.children.append(child)

    # High-entropy inner payloads: try one more peel on payload slices
    if child.entropy == "high" and child.children:
        return layer

    payload_frames: list[bytes] = []
    for fr in inner[:50]:
        if len(fr) > 16:
            payload_frames.append(fr[5:] if splitter_name == "tls_record" and len(fr) > 5 else fr)
    if len(payload_frames) >= 2 and _entropy_label(payload_frames) == "structured":
        sub = recursive_blind_analyze(
            flow,
            payload_frames,
            depth=depth + 1,
            max_depth=max_depth,
            label=f"{label}/payload",
        )
        if sub.parse_success >= 0.5:
            layer.children.append(sub)

    return layer


def format_notes(layer: NestedLayer) -> list[str]:
    notes = [
        f"[d{layer.depth}] {layer.label}: {layer.messages} msg, "
        f"parse={layer.parse_success:.0%}, entropy={layer.entropy}"
    ]
    if layer.splitter:
        notes.append(f"  splitter: {layer.splitter}")
    if layer.deep:
        kind = layer.deep.get("kind")
        if kind == "tls":
            if layer.deep.get("sni_hosts"):
                notes.append(f"  SNI: {', '.join(layer.deep['sni_hosts'][:6])}")
            if layer.deep.get("alpn"):
                notes.append(f"  ALPN: {', '.join(layer.deep['alpn'][:4])}")
        if kind == "dns" and layer.deep.get("domains"):
            notes.append(f"  DNS: {', '.join(layer.deep['domains'][:6])}")
        if kind == "quic":
            notes.append(f"  QUIC: {layer.deep.get('types', {})}")
    if layer.clusters:
        notes.append(f"  clusters: {len(layer.clusters)} opcodes")
    for ch in layer.children:
        notes.extend(format_notes(ch))
    return notes
