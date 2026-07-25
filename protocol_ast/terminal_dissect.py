"""Terminal / HTML packet tree dissector (Wireshark-like, no GUI)."""

from __future__ import annotations

import html
import struct
from dataclasses import dataclass, field
from typing import Any

from .deep_decode import (
    TLS_HANDSHAKE_NAMES,
    parse_dns_packet,
    parse_ntp_packet,
    parse_quic_packet,
    split_tls_records,
)
from .field_names import DNS_QTYPES, TLS_CONTENT_TYPES, enrich_format, protocol_hint
from .tls_handshake import parse_client_hello


@dataclass
class TreeNode:
    label: str
    value: str | None = None
    children: list["TreeNode"] = field(default_factory=list)


def _hex_bytes(data: bytes, limit: int = 16) -> str:
    chunk = data[:limit]
    text = chunk.hex()
    if len(data) > limit:
        text += f"… (+{len(data) - limit} bytes)"
    return text


def _render_text(node: TreeNode, indent: int = 0) -> list[str]:
    pad = "  " * indent
    if node.value is not None:
        lines = [f"{pad}├─ {node.label}: {node.value}"]
    else:
        lines = [f"{pad}├─ {node.label}"]
    for i, child in enumerate(node.children):
        child_lines = _render_text(child, indent + 1)
        if child_lines:
            lines.extend(child_lines)
    return lines


def _render_html(node: TreeNode) -> str:
    if node.children:
        inner = "".join(_render_html(c) for c in node.children)
        val = f" — {html.escape(node.value)}" if node.value else ""
        return f"<details open><summary>{html.escape(node.label)}{val}</summary><ul>{inner}</ul></details>"
    text = html.escape(node.label)
    if node.value:
        text += f": <code>{html.escape(node.value)}</code>"
    return f"<li>{text}</li>"


def dissect_dns(data: bytes) -> TreeNode | None:
    parsed = parse_dns_packet(data)
    if not parsed:
        return None
    flags = 0
    if len(data) >= 12:
        qid, flags, qd, an, ns, ar = struct.unpack(">HHHHHH", data[:12])
    else:
        return None
    root = TreeNode(f"DNS ({len(data)} bytes)")
    hdr = TreeNode("Header")
    hdr.children = [
        TreeNode("transaction_id", f"0x{qid:04x}"),
        TreeNode(
            "flags",
            f"0x{flags:04x} ({'response' if flags & 0x8000 else 'query'}, opcode={(flags >> 11) & 0xF})",
        ),
        TreeNode("qdcount", str(qd)),
        TreeNode("ancount", str(an)),
        TreeNode("nscount", str(ns)),
        TreeNode("arcount", str(ar)),
    ]
    root.children.append(hdr)
    for i, q in enumerate(parsed.get("questions", [])):
        qn = TreeNode(f"Question #{i + 1}")
        qtype = q.get("qtype", 0)
        qn.children = [
            TreeNode("name", q.get("name", "?")),
            TreeNode("qtype", f"{DNS_QTYPES.get(qtype, qtype)} ({qtype})"),
            TreeNode("qclass", str(q.get("qclass", 0))),
        ]
        root.children.append(qn)
    if len(data) > 12:
        root.children.append(TreeNode("raw_tail", _hex_bytes(data[12:], 24)))
    return root


def dissect_tls_record(data: bytes) -> TreeNode | None:
    if len(data) < 5:
        return None
    ctype, major, minor = data[0], data[1], data[2]
    length = (data[3] << 8) | data[4]
    if ctype not in range(20, 26) or major != 3:
        return None
    ver = f"TLS {major}.{minor}" if major == 3 and minor in (1, 3, 4) else f"0x{major:02x}{minor:02x}"
    root = TreeNode(f"TLS Record ({len(data)} bytes)")
    root.children = [
        TreeNode("content_type", f"{TLS_CONTENT_TYPES.get(ctype, ctype)} ({ctype})"),
        TreeNode("version", ver),
        TreeNode("length", str(length)),
    ]
    body = data[5 : 5 + length]
    if ctype == 0x16 and len(body) >= 4:
        htype = body[0]
        hlen = struct.unpack(">I", b"\x00" + body[1:4])[0]
        hs = TreeNode("Handshake")
        hs.children.append(
            TreeNode("type", f"{TLS_HANDSHAKE_NAMES.get(htype, f'type{htype}')} ({htype})")
        )
        hs.children.append(TreeNode("length", str(hlen)))
        if htype == 1:
            detail = parse_client_hello(body) or {}
            if detail.get("sni"):
                hs.children.append(TreeNode("SNI", ", ".join(detail["sni"][:6])))
            if detail.get("alpn"):
                hs.children.append(TreeNode("ALPN", ", ".join(detail["alpn"][:6])))
            if detail.get("supported_versions"):
                hs.children.append(
                    TreeNode("supported_versions", ", ".join(detail["supported_versions"][:4]))
                )
        root.children.append(hs)
    elif body:
        root.children.append(TreeNode("fragment", _hex_bytes(body, 20)))
    return root


def dissect_quic(data: bytes) -> TreeNode | None:
    parsed = parse_quic_packet(data, permit_short=True)
    if not parsed:
        return None
    root = TreeNode(f"QUIC ({len(data)} bytes)")
    if parsed.get("form") == "short":
        root.children = [
            TreeNode("form", "short header"),
            TreeNode("spin", str(parsed.get("spin"))),
            TreeNode("pn_len", str(parsed.get("pn_len"))),
            TreeNode("payload", _hex_bytes(data[1:], 16)),
        ]
        return root
    root.children = [
        TreeNode("form", "long header"),
        TreeNode("type", str(parsed.get("type"))),
        TreeNode("version", str(parsed.get("version_name", parsed.get("version")))),
        TreeNode("dcid_len", str(parsed.get("dcid_len"))),
        TreeNode("scid_len", str(parsed.get("scid_len"))),
    ]
    if parsed.get("token_len") is not None:
        root.children.append(TreeNode("token_len", str(parsed["token_len"])))
    if parsed.get("length") is not None:
        root.children.append(TreeNode("length", str(parsed["length"])))
    if parsed.get("packet_number") is not None:
        root.children.append(TreeNode("packet_number", str(parsed["packet_number"])))
    return root


def dissect_ntp(data: bytes) -> TreeNode | None:
    parsed = parse_ntp_packet(data)
    if not parsed:
        return None
    li_vn_mode = data[0]
    root = TreeNode(f"NTP ({len(data)} bytes)")
    root.children = [
        TreeNode("li_vn_mode", f"0x{li_vn_mode:02x}"),
        TreeNode("version", str(parsed.get("version"))),
        TreeNode("mode", str(parsed.get("mode"))),
        TreeNode("stratum", str(parsed.get("stratum"))),
        TreeNode("poll", str(parsed.get("poll"))),
    ]
    return root


def dissect_blind(flow: str, data: bytes, fmt: dict[str, Any] | None = None) -> TreeNode:
    fmt = enrich_format(flow, fmt or {})
    root = TreeNode(f"{flow} ({len(data)} bytes)")
    offset = 0
    for f in fmt.get("fields", [])[:32]:
        name = f.get("display") or f.get("name", "field")
        kind = f.get("kind", "")
        size = f.get("size", 1)
        if kind == "length" and offset + 2 <= len(data):
            val = (data[offset] << 8) | data[offset + 1]
            root.children.append(TreeNode(name, str(val)))
            offset += 2
            continue
        if kind == "payload":
            chunk = data[offset:]
            root.children.append(TreeNode(name, _hex_bytes(chunk, 20)))
            break
        if size and size > 1 and offset + size <= len(data):
            chunk = data[offset : offset + size]
            root.children.append(TreeNode(name, f"0x{chunk.hex()}"))
            offset += size
            continue
        if offset < len(data):
            root.children.append(TreeNode(name, f"0x{data[offset]:02x}"))
            offset += 1
    if offset < len(data) and not any(f.get("kind") == "payload" for f in fmt.get("fields", [])):
        root.children.append(TreeNode("remaining", _hex_bytes(data[offset:], 20)))
    return root


def dissect_packet(flow: str, data: bytes, fmt: dict[str, Any] | None = None) -> TreeNode:
    proto = protocol_hint(flow)
    if proto == "dns":
        node = dissect_dns(data)
        if node:
            return node
    if proto == "tls":
        node = dissect_tls_record(data)
        if node:
            return node
    if proto == "quic":
        node = dissect_quic(data)
        if node:
            return node
    if proto == "ntp":
        node = dissect_ntp(data)
        if node:
            return node
    return dissect_blind(flow, data, fmt)


def format_packet_text(flow: str, data: bytes, *, index: int = 0, fmt: dict | None = None) -> str:
    tree = dissect_packet(flow, data, fmt)
    lines = [f"=== Packet #{index} ==="] + _render_text(tree)
    return "\n".join(lines)


def dissect_flow_text(
    flow: str,
    payloads: list[bytes],
    *,
    limit: int = 5,
    fmt: dict | None = None,
    tcp_reassemble: bool = False,
) -> str:
    packets = payloads
    if tcp_reassemble and flow.upper().startswith("TCP"):
        _, packets = split_tls_records(payloads)
        if not packets:
            packets = payloads
    chunks: list[str] = [f"Flow {flow} — showing {min(limit, len(packets))}/{len(packets)} packets\n"]
    for i, pkt in enumerate(packets[:limit]):
        chunks.append(format_packet_text(flow, pkt, index=i, fmt=fmt))
        chunks.append("")
    return "\n".join(chunks).rstrip() + "\n"


def export_flow_html(
    flow: str,
    payloads: list[bytes],
    *,
    limit: int = 10,
    fmt: dict | None = None,
    tcp_reassemble: bool = False,
    title: str | None = None,
) -> str:
    packets = payloads
    if tcp_reassemble and flow.upper().startswith("TCP"):
        _, packets = split_tls_records(payloads)
        if not packets:
            packets = payloads
    body_parts: list[str] = []
    for i, pkt in enumerate(packets[:limit]):
        tree = dissect_packet(flow, pkt, fmt)
        body_parts.append(f"<h3>Packet #{i} ({len(pkt)} bytes)</h3>")
        body_parts.append(f"<div class='pkt'>{_render_html(tree)}</div>")
    page_title = html.escape(title or f"Dissect {flow}")
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{page_title}</title>
<style>
body{{font-family:monospace;background:#111;color:#ddd;padding:12px}}
h1,h2,h3{{color:#8cf}}
details{{margin:6px 0 6px 12px}}
summary{{cursor:pointer;color:#adf}}
code{{color:#9f9}}
.pkt{{border:1px solid #333;border-radius:8px;padding:8px;margin:12px 0}}
</style></head><body>
<h1>{page_title}</h1>
<p>Flow: <b>{html.escape(flow)}</b> — {min(limit, len(packets))}/{len(packets)} packets</p>
{''.join(body_parts)}
</body></html>
"""
