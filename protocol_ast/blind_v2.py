"""Recursive blind analysis v2 — nested AST without port labels."""

from __future__ import annotations

from dataclasses import dataclass, field

from .signal import Signal, propagate_flow


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
    sequitur: str | None = None
    sequitur_rules: int = 0
    confidence: float = 0.0
    opaque: bool = False

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "depth": self.depth,
            "messages": self.messages,
            "entropy": self.entropy,
            "opaque": self.opaque,
            "splitter": self.splitter,
            "format": self.format,
            "parse_success": self.parse_success,
            "confidence": self.confidence,
            "sequitur_rules": self.sequitur_rules,
            "sequitur": self.sequitur,
            "clusters": self.clusters,
            "deep": self.deep,
            "children": [c.to_dict() for c in self.children],
        }


def _signal_to_layer(sig: Signal) -> NestedLayer:
    return NestedLayer(
        label=sig.label,
        depth=sig.depth,
        messages=len(sig.messages),
        entropy=sig.entropy,
        format=sig.format,
        parse_success=sig.parse_success,
        splitter=sig.splitter,
        clusters=sig.clusters,
        deep=sig.deep,
        sequitur=sig.sequitur or None,
        sequitur_rules=sig.sequitur_rules,
        confidence=sig.confidence,
        opaque=sig.opaque,
        children=[_signal_to_layer(c) for c in sig.children],
    )


def recursive_blind_analyze(
    flow: str,
    messages: list[bytes],
    *,
    depth: int = 0,
    max_depth: int = 3,
    label: str | None = None,
) -> NestedLayer:
    """Backward-compatible wrapper over Signal.propagate()."""
    sig = propagate_flow(flow, messages, max_depth=max_depth)
    if label and label != flow:
        sig.label = label
    return _signal_to_layer(sig)


def format_notes(layer: NestedLayer) -> list[str]:
    notes = [
        f"[d{layer.depth}] {layer.label}: {layer.messages} msg, "
        f"parse={layer.parse_success:.0%}, entropy={layer.entropy}"
    ]
    if layer.confidence:
        notes[0] += f", conf={layer.confidence:.2f}"
    if layer.opaque:
        notes.append("  wall: opaque (high entropy)")
    if layer.splitter:
        notes.append(f"  splitter: {layer.splitter}")
    if layer.sequitur_rules:
        notes.append(f"  sequitur: {layer.sequitur_rules} rules")
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
