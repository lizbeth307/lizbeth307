"""Глибокий розбір відомих структур без назви протоколу (QUIC, TLS, DNS, NTP, XMPP)."""

from __future__ import annotations

import re
import struct
from collections import Counter

QUIC_VERSIONS = {
    0x00000001: "QUIC v1",
    0x6B3343CF: "QUIC draft-29",
    0xFF00001D: "QUIC draft-29",
}

TLS_HANDSHAKE_NAMES = {1: "ClientHello", 2: "ServerHello", 11: "Certificate"}


def read_quic_varint(data: bytes, off: int) -> tuple[int, int] | None:
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


def _quic_long_type_name(pkt_type: int) -> str:
    return {0: "Initial", 1: "0-RTT", 2: "Handshake", 3: "Retry"}.get(pkt_type, f"type{pkt_type}")


def parse_quic_packet(data: bytes, *, permit_short: bool = False) -> dict | None:
    if len(data) < 5:
        return None
    if not (data[0] & 0x80):
        # RFC 9000 short header: form=0, fixed=1
        if not permit_short or (data[0] & 0xC0) != 0x40 or len(data) < 8:
            return None
        return {
            "form": "short",
            "spin": bool(data[0] & 0x20),
            "pn_len": (data[0] & 0x03) + 1,
            "length": len(data),
        }
    if not (data[0] & 0x40):
        return None
    pkt_type = (data[0] >> 4) & 0x03
    version = struct.unpack(">I", data[1:5])[0]
    if version not in QUIC_VERSIONS:
        return None
    off = 5
    if off >= len(data):
        return None
    dcid_len = data[off]
    off += 1
    if off + dcid_len > len(data):
        return None
    dcid = data[off : off + dcid_len]
    off += dcid_len
    if off >= len(data):
        return None
    scid_len = data[off]
    off += 1
    if off + scid_len > len(data):
        return None
    scid = data[off : off + scid_len]
    off += scid_len
    out: dict = {
        "form": "long",
        "type": _quic_long_type_name(pkt_type),
        "version": version,
        "version_name": QUIC_VERSIONS.get(version, f"0x{version:08x}"),
        "dcid": dcid.hex(),
        "scid": scid.hex(),
        "dcid_len": dcid_len,
        "scid_len": scid_len,
    }
    if pkt_type == 0:
        tok = read_quic_varint(data, off)
        if not tok:
            return out
        token_len, used = tok
        off += used
        if off + token_len > len(data):
            return out
        out["token_len"] = token_len
        off += token_len
        ln = read_quic_varint(data, off)
        if not ln:
            return out
        length, used = ln
        out["length"] = length
        off += used
        pn_len = (data[0] & 0x03) + 1
        if off + pn_len <= len(data):
            out["packet_number"] = int.from_bytes(data[off : off + pn_len], "big")
            out["payload_len"] = max(0, length - pn_len)
    elif pkt_type == 2:
        ln = read_quic_varint(data, off)
        if ln:
            length, used = ln
            out["length"] = length
            off += used
            pn_len = (data[0] & 0x03) + 1
            if off + pn_len <= len(data):
                out["packet_number"] = int.from_bytes(data[off : off + pn_len], "big")
    return out


def analyze_quic_flow(payloads: list[bytes]) -> dict:
    long_valid = sum(
        1
        for p in payloads
        if len(p) >= 5
        and (p[0] & 0xC0) == 0xC0
        and struct.unpack(">I", p[1:5])[0] in QUIC_VERSIONS
    )
    permit_short = long_valid >= 2
    parsed = [p for p in (parse_quic_packet(m, permit_short=permit_short) for m in payloads) if p]
    if not parsed:
        return {"kind": "quic", "packets": len(payloads), "parsed": 0}
    types = Counter(p.get("type", p.get("form", "?")) for p in parsed)
    versions = Counter(p.get("version_name", "?") for p in parsed if p.get("form") == "long")
    long_n = sum(1 for p in parsed if p.get("form") == "long")
    short_n = sum(1 for p in parsed if p.get("form") == "short")
    sample = parsed[0]
    return {
        "kind": "quic",
        "packets": len(payloads),
        "parsed": len(parsed),
        "long_header": long_n,
        "short_header": short_n,
        "types": dict(types),
        "versions": dict(versions),
        "sample": {k: sample[k] for k in sample if k not in ("dcid", "scid")},
    }


def _read_dns_name(data: bytes, off: int) -> tuple[str, int] | None:
    labels: list[str] = []
    jumped = False
    start = off
    for _ in range(128):
        if off >= len(data):
            return None
        ln = data[off]
        if ln == 0:
            off += 1
            return ".".join(labels), off
        if ln & 0xC0 == 0xC0:
            if off + 2 > len(data):
                return None
            ptr = struct.unpack(">H", data[off : off + 2])[0] & 0x3FFF
            if not jumped:
                start = off + 2
            off = ptr
            jumped = True
            continue
        off += 1
        if off + ln > len(data):
            return None
        labels.append(data[off : off + ln].decode("ascii", errors="replace"))
        off += ln
    return None


def parse_dns_packet(data: bytes) -> dict | None:
    if len(data) < 12:
        return None
    qid, flags, qd, an, ns, ar = struct.unpack(">HHHHHH", data[:12])
    if qd == 0 and an == 0:
        return None
    off = 12
    questions: list[dict] = []
    for _ in range(qd):
        name = _read_dns_name(data, off)
        if not name:
            return None
        domain, off = name
        if off + 4 > len(data):
            return None
        qtype, qclass = struct.unpack(">HH", data[off : off + 4])
        off += 4
        questions.append({"name": domain, "qtype": qtype, "qclass": qclass})
    is_response = bool(flags & 0x8000)
    return {
        "qid": qid,
        "response": is_response,
        "opcode": (flags >> 11) & 0xF,
        "questions": questions,
        "answers": an,
    }


def analyze_dns_flow(payloads: list[bytes]) -> dict:
    parsed = [p for p in (parse_dns_packet(m) for m in payloads) if p]
    domains: list[str] = []
    for p in parsed:
        for q in p["questions"]:
            domains.append(q["name"])
    qtypes = Counter()
    for p in parsed:
        for q in p["questions"]:
            qtypes[q["qtype"]] += 1
    return {
        "kind": "dns",
        "packets": len(payloads),
        "parsed": len(parsed),
        "queries": sum(1 for p in parsed if not p["response"]),
        "responses": sum(1 for p in parsed if p["response"]),
        "domains": sorted(set(domains))[:20],
        "qtypes": dict(qtypes),
    }


def parse_tls_sni(handshake: bytes) -> list[str]:
    if len(handshake) < 38 or handshake[0] != 0x01:
        return []
    pos = 4 + 2 + 32
    if pos >= len(handshake):
        return []
    sid_len = handshake[pos]
    pos += 1 + sid_len
    if pos + 2 > len(handshake):
        return []
    cs_len = struct.unpack(">H", handshake[pos : pos + 2])[0]
    pos += 2 + cs_len
    if pos >= len(handshake):
        return []
    cm_len = handshake[pos]
    pos += 1 + cm_len
    if pos + 2 > len(handshake):
        return []
    ext_len = struct.unpack(">H", handshake[pos : pos + 2])[0]
    pos += 2
    end = pos + ext_len
    hosts: list[str] = []
    while pos + 4 <= end and pos + 4 <= len(handshake):
        etype = struct.unpack(">H", handshake[pos : pos + 2])[0]
        elen = struct.unpack(">H", handshake[pos + 2 : pos + 4])[0]
        pos += 4
        edata = handshake[pos : pos + elen]
        if etype == 0 and len(edata) >= 5:
            list_len = struct.unpack(">H", edata[:2])[0]
            p = 2
            while p + 3 <= 2 + list_len and p + 3 <= len(edata):
                if edata[p] != 0:
                    p += 1
                    continue
                nlen = struct.unpack(">H", edata[p + 1 : p + 3])[0]
                p += 3
                if p + nlen <= len(edata):
                    hosts.append(edata[p : p + nlen].decode("ascii", errors="replace"))
                p += nlen
        pos += elen
    return hosts


def split_tls_records(messages: list[bytes]) -> tuple[float, list[bytes]]:
    frames: list[bytes] = []
    ok = 0
    for m in messages:
        off = 0
        pkt_ok = True
        while off + 5 <= len(m):
            ctype, v1, ln = m[off], m[off + 1], (m[off + 3] << 8) | m[off + 4]
            if ctype not in range(20, 26) or v1 != 3:
                pkt_ok = False
                break
            end = off + 5 + ln
            if end > len(m):
                pkt_ok = False
                break
            frames.append(m[off:end])
            off = end
        if pkt_ok and off == len(m):
            ok += 1
    return (ok / len(messages) if messages else 0.0), frames


def analyze_tls_flow(payloads: list[bytes]) -> dict:
    from .tls_handshake import parse_client_hello

    rate, frames = split_tls_records(payloads)
    handshakes: list[dict] = []
    sni_hosts: list[str] = []
    alpn_list: list[str] = []
    for fr in frames:
        if len(fr) < 6 or fr[0] != 0x16:
            continue
        body = fr[5:]
        if len(body) < 4:
            continue
        htype = body[0]
        if htype == 1:
            detail = parse_client_hello(body) or {}
            hosts = detail.get("sni", [])
            if hosts:
                sni_hosts.extend(hosts)
            alpn_list.extend(detail.get("alpn", []))
            handshakes.append({"type": "ClientHello", "sni": hosts, "alpn": detail.get("alpn", []), **detail})
        elif htype in TLS_HANDSHAKE_NAMES:
            handshakes.append({"type": TLS_HANDSHAKE_NAMES[htype]})
    return {
        "kind": "tls",
        "packets": len(payloads),
        "record_split_rate": round(rate, 3),
        "records": len(frames),
        "client_hellos": sum(1 for h in handshakes if h["type"] == "ClientHello"),
        "sni_hosts": sorted(set(sni_hosts))[:20],
        "alpn": sorted(set(alpn_list))[:10],
        "handshakes": handshakes[:10],
    }


def parse_ntp_packet(data: bytes) -> dict | None:
    if len(data) != 48:
        return None
    li_vn_mode = data[0]
    mode = li_vn_mode & 0x07
    version = (li_vn_mode >> 3) & 0x07
    return {
        "mode": {3: "client", 4: "server", 6: "broadcast"}.get(mode, f"mode{mode}"),
        "version": version,
        "stratum": data[1],
        "poll": data[2],
    }


def analyze_ntp_flow(payloads: list[bytes]) -> dict:
    parsed = [p for p in (parse_ntp_packet(m) for m in payloads) if p]
    modes = Counter(p["mode"] for p in parsed)
    return {
        "kind": "ntp",
        "packets": len(payloads),
        "parsed": len(parsed),
        "fixed_len": 48,
        "modes": dict(modes),
        "versions": dict(Counter(p["version"] for p in parsed)),
    }


def _scan_protobuf_tags(data: bytes, limit: int = 12) -> list[int]:
    tags: list[int] = []
    off = 0
    while off < len(data) and len(tags) < limit:
        b = data[off]
        if b == 0:
            off += 1
            continue
        field = b >> 3
        wire = b & 0x07
        tags.append(field)
        off += 1
        if wire == 0:
            while off < len(data) and data[off] & 0x80:
                off += 1
            off += 1
        elif wire == 1:
            off += 8
        elif wire == 2:
            if off >= len(data):
                break
            ln = data[off]
            off += 1 + ln
        elif wire == 5:
            off += 4
        else:
            break
    return tags


def analyze_xmpp_flow(payloads: list[bytes]) -> dict:
    xml = sum(1 for p in payloads if p.lstrip().startswith(b"<"))
    length_prefixed = 0
    protobufish = 0
    hosts: list[str] = []
    for p in payloads:
        if p.lstrip().startswith(b"<"):
            m = re.search(rb'to=[\'"]([^\'"]+)[\'"]', p[:512])
            if m:
                hosts.append(m.group(1).decode("ascii", errors="replace"))
            m = re.search(rb"host=[\'\"]([^\'\"]+)[\'\"]", p[:512])
            if m:
                hosts.append(m.group(1).decode("ascii", errors="replace"))
        elif len(p) >= 4 and p[0] == 0 and p[1] == 0:
            ln = struct.unpack(">H", p[2:4])[0]
            if ln + 4 == len(p) or ln + 6 == len(p):
                length_prefixed += 1
        if p and p[0] in (0x08, 0x0A, 0x10, 0x12, 0x1A, 0x22):
            protobufish += 1
    lens = Counter(len(p) for p in payloads)
    proto_tags: list[int] = []
    for p in payloads:
        if len(p) > 8 and not p.lstrip().startswith(b"<"):
            proto_tags.extend(_scan_protobuf_tags(p))
            break
    return {
        "kind": "xmpp",
        "packets": len(payloads),
        "xml_streams": xml,
        "length_prefixed": length_prefixed,
        "protobuf_like": protobufish,
        "length_distribution": dict(lens.most_common(8)),
        "protobuf_fields": sorted(set(proto_tags))[:12],
        "hosts": sorted(set(hosts))[:10],
        "notes": ["Google mtalk/XMPP binary framing on 5222" if protobufish else "XMPP stream"],
    }


def deep_analyze_flow(label: str, payloads: list[bytes]) -> dict | None:
    upper = label.upper()
    if upper == "UDP:53" or upper.endswith(":53"):
        return analyze_dns_flow(payloads)
    if upper == "UDP:123" or upper.endswith(":123"):
        return analyze_ntp_flow(payloads)
    if upper == "TCP:5222" or upper.endswith(":5222"):
        return analyze_xmpp_flow(payloads)
    if upper == "UDP:443" or (upper.endswith(":443") and upper.startswith("UDP")):
        q = analyze_quic_flow(payloads)
        if q.get("parsed", 0) > 0:
            return q
    if upper == "TCP:443" or (upper.endswith(":443") and upper.startswith("TCP")):
        return analyze_tls_flow(payloads)
    return None
