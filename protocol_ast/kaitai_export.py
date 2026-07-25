"""Export discovered format to Kaitai Struct .ksy."""

from __future__ import annotations

from typing import Any

from .field_names import enrich_format


MAX_KSY_FIELDS = 32


def format_to_kaitai(fmt: dict[str, Any], *, meta_id: str = "discovered", flow: str = "") -> str:
    """Generate Kaitai Struct schema from discover_format() dict."""
    if flow:
        fmt = enrich_format(flow, fmt)
    all_fields = fmt.get("fields", [])
    fields = all_fields[:MAX_KSY_FIELDS]
    truncated = len(all_fields) > MAX_KSY_FIELDS
    endian = fmt.get("endian") or fmt.get("length_endian") or "le"
    ks_endian = "be" if endian == "be" else "le"
    lines = [
        "meta:",
        f"  id: {meta_id}",
        f"  endian: {ks_endian}",
    ]
    if truncated:
        lines.append(f"  doc: truncated from {len(all_fields)} fields to {MAX_KSY_FIELDS}")
    lines.extend(
        [
            "seq:",
            "  - id: message",
            "    type: message_body",
            "types:",
            "  message_body:",
            "    seq:",
        ]
    )
    for f in fields:
        kind = f.get("kind", "")
        name = f.get("name", "field").replace("@", "_")
        if kind == "payload":
            lines.append("      - id: payload")
            lines.append("        size: _parent._root._io.size - _io.pos")
            continue
        if kind == "length":
            w = fmt.get("length_width", "u16")
            if w == "u32":
                lines.append(f"      - id: {name}")
                lines.append("        type: u4")
            else:
                lines.append(f"      - id: {name}")
                lines.append("        type: u2")
            lines.append("      - id: body")
            lines.append(f"        size: {name}")
            continue
        if kind == "fixed":
            size = f.get("size", 1)
            if size == 1:
                lines.append(f"      - id: {name}")
                lines.append("        type: u1")
            else:
                lines.append(f"      - id: {name}")
                lines.append(f"        size: {size}")
            continue
        if kind == "enum":
            lines.append(f"      - id: {name}")
            lines.append("        type: u1")
            continue
        lines.append(f"      - id: {name}")
        lines.append("        type: u1")
    return "\n".join(lines) + "\n"


def export_flow_kaitai(flow: str, fmt: dict[str, Any]) -> str:
    safe = flow.lower().replace(":", "_").replace("<", "").replace(">", "")
    return format_to_kaitai(fmt, meta_id=f"flow_{safe}", flow=flow)
