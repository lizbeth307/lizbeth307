"""Human-readable field names for known protocol flows."""

from __future__ import annotations

import copy
from typing import Any

TLS_CONTENT_TYPES = {
    20: "ChangeCipherSpec",
    21: "Alert",
    22: "Handshake",
    23: "ApplicationData",
    24: "Heartbeat",
    25: "TLS 1.3 inner",
}

DNS_QTYPES = {1: "A", 28: "AAAA", 5: "CNAME", 15: "MX", 16: "TXT", 33: "SRV", 65: "HTTPS"}

DNS_CANONICAL_FIELDS: list[dict[str, Any]] = [
    {"name": "transaction_id", "offset": 0, "size": 2, "kind": "fixed", "display": "DNS transaction ID"},
    {"name": "flags", "offset": 2, "size": 2, "kind": "enum", "display": "DNS flags (QR, opcode, RD, ...)"},
    {"name": "qdcount", "offset": 4, "size": 2, "kind": "fixed", "display": "Question count"},
    {"name": "ancount", "offset": 6, "size": 2, "kind": "fixed", "display": "Answer count"},
    {"name": "nscount", "offset": 8, "size": 2, "kind": "fixed", "display": "Authority count"},
    {"name": "arcount", "offset": 10, "size": 2, "kind": "fixed", "display": "Additional count"},
    {"name": "question_data", "offset": 12, "size": -1, "kind": "payload", "display": "Question / record data"},
]

TLS_CANONICAL_FIELDS: list[dict[str, Any]] = [
    {"name": "content_type", "offset": 0, "size": 1, "kind": "enum", "display": "TLS content type"},
    {"name": "version", "offset": 1, "size": 2, "kind": "fixed", "display": "TLS version (e.g. 0x0303 = TLS 1.2)"},
    {"name": "length", "offset": 3, "size": 2, "kind": "length", "display": "Fragment length"},
    {"name": "fragment", "offset": 5, "size": -1, "kind": "payload", "display": "TLS fragment / handshake body"},
]

NTP_CANONICAL_FIELDS: list[dict[str, Any]] = [
    {"name": "li_vn_mode", "offset": 0, "size": 1, "kind": "fixed", "display": "Leap indicator / version / mode"},
    {"name": "stratum", "offset": 1, "size": 1, "kind": "fixed", "display": "Stratum level"},
    {"name": "poll", "offset": 2, "size": 1, "kind": "fixed", "display": "Poll interval"},
    {"name": "precision", "offset": 3, "size": 1, "kind": "fixed", "display": "Clock precision"},
    {"name": "root_delay", "offset": 4, "size": 4, "kind": "fixed", "display": "Root delay"},
    {"name": "root_dispersion", "offset": 8, "size": 4, "kind": "fixed", "display": "Root dispersion"},
    {"name": "reference_id", "offset": 12, "size": 4, "kind": "fixed", "display": "Reference ID"},
    {"name": "reference_timestamp", "offset": 16, "size": 8, "kind": "fixed", "display": "Reference timestamp"},
    {"name": "originate_timestamp", "offset": 24, "size": 8, "kind": "fixed", "display": "Originate timestamp"},
    {"name": "receive_timestamp", "offset": 32, "size": 8, "kind": "fixed", "display": "Receive timestamp"},
    {"name": "transmit_timestamp", "offset": 40, "size": 8, "kind": "fixed", "display": "Transmit timestamp"},
]


def protocol_hint(flow: str) -> str | None:
    upper = flow.upper()
    if upper.endswith(":53"):
        return "dns"
    if upper.endswith(":123"):
        return "ntp"
    if upper.startswith("TCP") and upper.endswith(":443"):
        return "tls"
    if upper.startswith("UDP") and upper.endswith(":443"):
        return "quic"
    if upper.endswith(":5222"):
        return "xmpp"
    return None


def canonical_fields(flow: str) -> list[dict[str, Any]] | None:
    proto = protocol_hint(flow)
    if proto == "dns":
        return copy.deepcopy(DNS_CANONICAL_FIELDS)
    if proto == "tls":
        return copy.deepcopy(TLS_CANONICAL_FIELDS)
    if proto == "ntp":
        return copy.deepcopy(NTP_CANONICAL_FIELDS)
    return None


def canonicalize_format(flow: str, fmt: dict[str, Any]) -> dict[str, Any]:
    """Replace blind per-byte fields with merged multi-byte layout for known protocols."""
    fields = canonical_fields(flow)
    if not fields:
        return fmt
    out = copy.deepcopy(fmt) if fmt else {}
    out["fields"] = fields
    out["endian"] = "be"
    out["length_endian"] = "be"
    out["length_field_offset"] = next((f["offset"] for f in fields if f.get("kind") == "length"), None)
    out["length_width"] = "u16"
    out["protocol"] = protocol_hint(flow)
    out["canonical"] = True
    return out


def _name_for_offset(proto: str, offset: int) -> tuple[str, str] | None:
    if proto == "dns":
        names = {f["offset"]: (f["name"], f["display"]) for f in DNS_CANONICAL_FIELDS}
        return names.get(offset)
    if proto == "tls":
        names = {f["offset"]: (f["name"], f["display"]) for f in TLS_CANONICAL_FIELDS}
        return names.get(offset)
    if proto == "ntp":
        names = {f["offset"]: (f["name"], f["display"]) for f in NTP_CANONICAL_FIELDS}
        return names.get(offset)
    if proto == "quic":
        if offset == 0:
            return ("header_form", "QUIC header form + flags")
        if offset == 1:
            return ("version", "QUIC version (32-bit)")
    return None


def enrich_field(flow: str, field: dict[str, Any], index: int) -> dict[str, Any]:
    """Return field dict with human name and display label when known."""
    out = dict(field)
    if out.get("display"):
        return out
    proto = protocol_hint(flow)
    offset = field.get("offset", index)
    kind = field.get("kind", "")

    if kind == "payload":
        labels = {
            "dns": ("question_data", "Question / record data"),
            "tls": ("fragment", "TLS fragment"),
            "ntp": ("ntp_body", "NTP packet body"),
            "quic": ("quic_payload", "QUIC protected payload"),
        }
        if proto and proto in labels:
            name, label = labels[proto]
            out["name"] = name
            out["display"] = label
        else:
            out["display"] = out.get("name", "payload")
        return out

    if proto:
        named = _name_for_offset(proto, offset)
        if named:
            out["name"] = named[0]
            out["display"] = named[1]
            return out

    raw = out.get("name", f"field_{index}")
    out["display"] = raw.replace("_", " ")
    return out


def enrich_format(flow: str, fmt: dict[str, Any]) -> dict[str, Any]:
    """Copy format dict with human-readable field names (canonical merge when known)."""
    if not fmt:
        return fmt
    merged = canonicalize_format(flow, fmt)
    out = copy.deepcopy(merged)
    out["protocol"] = protocol_hint(flow)
    out["fields"] = [enrich_field(flow, f, i) for i, f in enumerate(merged.get("fields", []))]
    return out
