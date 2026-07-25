"""Living signal — self-propagating blind protocol discovery."""

from __future__ import annotations

from dataclasses import dataclass, field

from .align import discover_format
from .cluster import best_cluster_offset, discover_clustered_formats
from .deep_decode import deep_analyze_flow
from .pipeline import discover_and_parse
from .sequitur import Sequitur, tokenize_message
from .serde import format_to_dict
from .splitters import discover_splitter


def entropy_label(messages: list[bytes]) -> str:
    if not messages:
        return "empty"
    ratio = len(set(b for p in messages[:10] for b in p[:16])) / max(
        1, min(16, min(len(p) for p in messages))
    )
    return "high" if ratio > 0.85 else "structured"


@dataclass
class Signal:
    """Byte stream that discovers its own structure and propagates inward."""

    label: str
    messages: list[bytes]
    depth: int = 0
    parent: Signal | None = None
    flow: str = ""
    format: dict = field(default_factory=dict)
    parse_success: float = 0.0
    entropy: str = "unknown"
    splitter: str | None = None
    confidence: float = 0.0
    sequitur: str = ""
    sequitur_rules: int = 0
    opaque: bool = False
    clusters: dict | None = None
    deep: dict | None = None
    children: list[Signal] = field(default_factory=list)

    def analyze(self) -> Signal:
        if not self.messages:
            self.entropy = "empty"
            return self
        fmt = discover_format(self.messages)
        result = discover_and_parse(self.messages)
        self.format = format_to_dict(fmt)
        self.parse_success = round(result.success_rate, 3)
        self.entropy = entropy_label(self.messages)
        self.confidence = self.parse_success * (0.5 if self.entropy == "high" else 1.0)

        seq = Sequitur()
        for msg in self.messages[:16]:
            seq.feed_many(tokenize_message(msg[:48]) + ["|"])
        self.sequitur = seq.summary()
        self.sequitur_rules = max(0, len(seq.rules) - 1)

        if self.depth == 0 and self.flow:
            self.deep = deep_analyze_flow(self.flow, self.messages)
            cl_off = best_cluster_offset(self.messages)
            if cl_off is not None:
                self.clusters = discover_clustered_formats(self.messages, cl_off)
        return self

    def propagate(self, *, max_depth: int = 5) -> Signal:
        """Discover format, split frames, descend — until entropy wall or max depth."""
        self.analyze()
        if self.depth >= max_depth or len(self.messages) < 2:
            return self
        if self.entropy == "high" and self.depth > 0:
            self.opaque = True
            return self

        split = discover_splitter(self.messages, depth=self.depth)
        if not split:
            return self

        splitter_name, inner = split
        self.splitter = splitter_name
        if len(inner) < 2:
            return self

        child = Signal(
            label=f"{self.label}/{splitter_name}",
            messages=inner,
            depth=self.depth + 1,
            parent=self,
            flow=self.flow,
        )
        child.propagate(max_depth=max_depth)
        self.children.append(child)

        if child.entropy == "high" and child.children:
            return self

        payload_frames: list[bytes] = []
        for fr in inner[:50]:
            if len(fr) <= 16:
                continue
            if splitter_name == "tls_record" and len(fr) > 5:
                payload_frames.append(fr[5:])
            elif splitter_name.startswith("length_"):
                fmt = discover_format(inner)
                off = fmt.length_field_offset or 0
                hdr = off + (4 if fmt.length_width == "u32" else 2)
                if len(fr) > hdr:
                    payload_frames.append(fr[hdr:])
            else:
                payload_frames.append(fr)

        if len(payload_frames) >= 2 and entropy_label(payload_frames) == "structured":
            sub = Signal(
                label=f"{self.label}/payload",
                messages=payload_frames,
                depth=self.depth + 1,
                parent=self,
                flow=self.flow,
            )
            sub.propagate(max_depth=max_depth)
            if sub.parse_success >= 0.5 or sub.children:
                self.children.append(sub)

        return self

    def path(self) -> str:
        parts = [self.label]
        node = self.parent
        while node:
            parts.append(node.label)
            node = node.parent
        return " → ".join(reversed(parts))

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "depth": self.depth,
            "messages": len(self.messages),
            "entropy": self.entropy,
            "opaque": self.opaque,
            "splitter": self.splitter,
            "format": self.format,
            "parse_success": self.parse_success,
            "confidence": round(self.confidence, 3),
            "sequitur_rules": self.sequitur_rules,
            "sequitur": self.sequitur,
            "clusters": self.clusters,
            "deep": self.deep,
            "children": [c.to_dict() for c in self.children],
        }

    def format_notes(self) -> list[str]:
        notes = [
            f"[d{self.depth}] {self.label}: {len(self.messages)} msg, "
            f"parse={self.parse_success:.0%}, entropy={self.entropy}, "
            f"conf={self.confidence:.2f}"
        ]
        if self.opaque:
            notes.append("  wall: opaque (high entropy)")
        if self.splitter:
            notes.append(f"  splitter: {self.splitter}")
        if self.sequitur_rules:
            notes.append(f"  sequitur: {self.sequitur_rules} rules")
        if self.deep:
            kind = self.deep.get("kind")
            if kind == "tls":
                if self.deep.get("sni_hosts"):
                    notes.append(f"  SNI: {', '.join(self.deep['sni_hosts'][:6])}")
                if self.deep.get("alpn"):
                    notes.append(f"  ALPN: {', '.join(self.deep['alpn'][:4])}")
            if kind == "dns" and self.deep.get("domains"):
                notes.append(f"  DNS: {', '.join(self.deep['domains'][:6])}")
            if kind == "quic":
                notes.append(f"  QUIC: {self.deep.get('types', {})}")
        if self.clusters:
            notes.append(f"  clusters: {len(self.clusters)} opcodes")
        for ch in self.children:
            notes.extend(ch.format_notes())
        return notes


def propagate_flow(
    flow: str,
    messages: list[bytes],
    *,
    max_depth: int = 5,
) -> Signal:
    root = Signal(label=flow, messages=messages, flow=flow, depth=0)
    return root.propagate(max_depth=max_depth)
