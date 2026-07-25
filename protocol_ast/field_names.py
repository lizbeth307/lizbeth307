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


def _dns_name(offset: int) -> tuple[str, str] | None:
    names = {
        0: ("transaction_id", "DNS transaction ID (16-bit)"),
        2: ("flags", "DNS flags (QR, opcode, AA, RD, ...)"),
        4: ("qdcount", "Question count"),
        6: ("ancount", "Answer count"),
        8: ("nscount", "Authority count"),
        10: ("arcount", "Additional count"),
    }
    if offset in names:
        return names[offset]
    if offset >= 12:
        return ("qname", "Query name (label-encoded)")
    return None


def _ntp_name(offset: int) -> tuple[str, str] | None:
    names = {
        0: ("li_vn_mode", "Leap indicator / version / mode"),
        1: ("stratum", "Stratum level"),
        2: ("poll", "Poll interval"),
        3: ("precision", "Clock precision"),
        4: ("root_delay", "Root delay"),
        8: ("root_dispersion", "Root dispersion"),
        12: ("reference_id", "Reference ID"),
        16: ("reference_timestamp", "Reference timestamp"),
        24: ("originate_timestamp", "Originate timestamp"),
        32: ("receive_timestamp", "Receive timestamp"),
        40: ("transmit_timestamp", "Transmit timestamp"),
    }
    return names.get(offset)


def _tls_name(offset: int) -> tuple[str, str] | None:
    names = {
        0: ("content_type", "TLS content type"),
        1: ("version_major", "TLS version major"),
        2: ("version_minor", "TLS version minor"),
        3: ("length", "Fragment length"),
        5: ("fragment", "TLS fragment / handshake body"),
    }
    return names.get(offset)


def _quic_name(offset: int) -> tuple[str, str] | None:
    if offset == 0:
        return ("header_form", "QUIC header form + flags")
    if offset == 1:
        return ("version", "QUIC version (32-bit)")
    return None


def _name_for_offset(proto: str, offset: int) -> tuple[str, str] | None:
    if proto == "dns":
        return _dns_name(offset)
    if proto == "ntp":
        return _ntp_name(offset)
    if proto == "tls":
        return _tls_name(offset)
    if proto == "quic":
        return _quic_name(offset)
    return None


def enrich_field(flow: str, field: dict[str, Any], index: int) -> dict[str, Any]:
    """Return field dict with human name and display label when known."""
    out = dict(field)
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

    if kind == "length" and proto == "tls":
        out["name"] = "length"
        out["display"] = "Fragment length (16-bit BE)"
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
    """Copy format dict with human-readable field names."""
    if not fmt:
        return fmt
    out = copy.deepcopy(fmt)
    out["protocol"] = protocol_hint(flow)
    fields = []
    for i, f in enumerate(fmt.get("fields", [])):
        fields.append(enrich_field(flow, f, i))
    out["fields"] = fields
    return out
