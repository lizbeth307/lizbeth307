#!/usr/bin/env python3
"""
analyze_pcap.py — мінімальний аналізатор PCAP для Termux/Android.

ВАЖЛИВО (Termux): не запускайте через "python" — буде grep /proc/stat error!
  pkg install python
  python3 analyze_pcap.py ~/downloads/файл.pcap
  python3 analyze_pcap.py ~/downloads/файл.pcap --blind --flow 443
  bash run_pcap.sh ~/downloads/файл.pcap
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

VERSION = "2.1.0-deep"

# Deep decode embedded for Termux single-file deploy (sync: protocol_ast/deep_decode.py)
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


def parse_quic_packet(data: bytes) -> dict | None:
    if len(data) < 5:
        return None
    if not (data[0] & 0x80):
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
    if version not in QUIC_VERSIONS and version > 0x0F000000:
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
    parsed = [p for p in (parse_quic_packet(m) for m in payloads) if p]
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
    rate, frames = split_tls_records(payloads)
    handshakes: list[dict] = []
    sni_hosts: list[str] = []
    for fr in frames:
        if len(fr) < 6 or fr[0] != 0x16:
            continue
        body = fr[5:]
        if len(body) < 4:
            continue
        htype = body[0]
        if htype == 1:
            hosts = parse_tls_sni(body)
            if hosts:
                sni_hosts.extend(hosts)
            handshakes.append({"type": "ClientHello", "sni": hosts})
        elif htype in TLS_HANDSHAKE_NAMES:
            handshakes.append({"type": TLS_HANDSHAKE_NAMES[htype]})
    return {
        "kind": "tls",
        "packets": len(payloads),
        "record_split_rate": round(rate, 3),
        "records": len(frames),
        "client_hellos": sum(1 for h in handshakes if h["type"] == "ClientHello"),
        "sni_hosts": sorted(set(sni_hosts))[:20],
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

# --- PCAP ---
PCAP_MAGIC_LE = 0xA1B2C3D4
PCAP_MAGIC_BE = 0xD4C3B2A1
ETH_P_IP = 0x0800
COMMON_PORTS = {53, 67, 68, 80, 123, 443, 5353, 8080, 8443}


@dataclass(frozen=True)
class FlowKey:
    proto: str
    port: int

    @property
    def label(self) -> str:
        return f"{self.proto.upper()}:{self.port}"


def _flow_key(proto: str, sport: int, dport: int) -> FlowKey:
    for p in (sport, dport):
        if p in COMMON_PORTS or p < 1024:
            return FlowKey(proto, p)
    return FlowKey(proto, min(sport, dport))


def _parse_ipv4(frame: bytes, offset: int) -> tuple[str, int, int, bytes] | None:
    data = frame[offset:]
    if len(data) < 20 or (data[0] >> 4) != 4:
        return None
    ihl = (data[0] & 0x0F) * 4
    proto = data[9]
    total = struct.unpack(">H", data[2:4])[0]
    ip = data[ihl:total]
    if proto == 17 and len(ip) >= 8:
        s, d, u = struct.unpack(">HHH", ip[:6])
        return "udp", s, d, ip[8:u]
    if proto == 6 and len(ip) >= 20:
        s, d = struct.unpack(">HH", ip[:4])
        off = ((ip[12] >> 4) & 0x0F) * 4
        return "tcp", s, d, ip[off:]
    return None


def _extract(frame: bytes, link: int) -> tuple[str, int, int, bytes] | None:
    if link == 1 and len(frame) >= 14:
        if struct.unpack(">H", frame[12:14])[0] == ETH_P_IP:
            return _parse_ipv4(frame, 14)
    if link == 113 and len(frame) >= 16:
        if struct.unpack(">H", frame[14:16])[0] == ETH_P_IP:
            return _parse_ipv4(frame, 16)
    if link in (0, 101):
        return _parse_ipv4(frame, 4 if link == 0 else 0)
    return None


def iter_pcap(path: Path):
    data = path.read_bytes()
    magic = struct.unpack("<I", data[:4])[0]
    end = "<"
    if magic in (PCAP_MAGIC_BE, 0x4D3CB2A1):
        end = ">"
    link = struct.unpack(end + "IHHiIII", data[:24])[6]
    off = 24
    while off + 16 <= len(data):
        _, _, caplen, _ = struct.unpack(end + "IIII", data[off : off + 16])
        off += 16
        yield link, data[off : off + caplen]
        off += caplen


def extract_flows(path: Path, min_pkts: int = 2, min_len: int = 4) -> dict[str, list[bytes]]:
    buckets: dict[FlowKey, list[bytes]] = {}
    for link, frame in iter_pcap(path):
        p = _extract(frame, link)
        if not p:
            continue
        proto, sport, dport, payload = p
        if len(payload) < min_len:
            continue
        key = _flow_key(proto, sport, dport)
        buckets.setdefault(key, []).append(payload)
    return {k.label: v for k, v in buckets.items() if len(v) >= min_pkts}


# --- Discovery (спрощений) ---
def discover_format(messages: list[bytes]) -> dict:
    if not messages:
        return {}
    min_len = min(map(len, messages))
    best_off, best_score, best_end = None, 0.0, "le"
    for off in range(max(0, min_len - 1)):
        for end in ("le", "be"):
            hits = total = 0
            for m in messages:
                if off + 2 >= len(m):
                    continue
                total += 1
                if end == "le":
                    decl = m[off] | (m[off + 1] << 8)
                else:
                    decl = (m[off] << 8) | m[off + 1]
                rest = len(m) - off - 2
                if decl == rest or decl == rest - 1:
                    hits += 1
            score = hits / total if total else 0
            if score > best_score:
                best_score, best_off, best_end = score, off, end
    fields = []
    header_end = (best_off + 2) if best_score >= 0.8 else min_len
    i = 0
    while i < header_end:
        if best_score >= 0.8 and i == best_off:
            fields.append({"name": "length", "offset": i, "size": 2, "kind": "length", "endian": best_end})
            i += 2
            continue
        vals = Counter(m[i] for m in messages if i < len(m))
        dom = vals.most_common(1)[0][1] / sum(vals.values()) if vals else 0
        if dom >= 0.9:
            fields.append({"name": f"fixed_{i}", "offset": i, "size": 1, "kind": "fixed", "value": vals.most_common(1)[0][0]})
            i += 1
        elif len(vals) <= 8:
            fields.append({"name": f"enum_{i}", "offset": i, "size": 1, "kind": "enum"})
            i += 1
        else:
            fields.append({"name": f"byte_{i}", "offset": i, "size": 1, "kind": "variable"})
            i += 1
    fields.append({"name": "payload", "offset": header_end, "size": -1, "kind": "payload"})
    return {"fields": fields, "length_offset": best_off if best_score >= 0.8 else None, "endian": best_end}


def _read_varint(data: bytes, off: int) -> tuple[int, int] | None:
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


def _score_varint_length(messages: list[bytes], off: int) -> float:
    hits = total = 0
    for m in messages:
        if off >= len(m):
            continue
        parsed = _read_varint(m, off)
        if not parsed:
            continue
        total += 1
        val, used = parsed
        rest = len(m) - off - used
        if val == rest or val in (rest - 1, rest - 2):
            hits += 1
    return hits / total if total else 0.0


def _score_tls_like(messages: list[bytes]) -> tuple[float, list[bytes]]:
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


def _split_quic_packets(messages: list[bytes]) -> tuple[float, list[bytes]]:
    """Legacy heuristic — only when deep_decode unavailable."""
    frames: list[bytes] = []
    ok = 0
    for m in messages:
        if len(m) < 5 or not (m[0] & 0x80) or not (m[0] & 0x40):
            continue
        ver = struct.unpack(">I", m[1:5])[0]
        if ver not in (0x00000001, 0x6B3343CF, 0xFF00001D):
            continue
        frames.append(m)
        ok += 1
    return (ok / len(messages) if messages else 0.0), frames


def _find_best_length_offset(messages: list[bytes]) -> list[dict]:
    if not messages:
        return []
    min_len = min(map(len, messages))
    cands: list[dict] = []
    for off in range(min(24, min_len - 1)):
        for end in ("le", "be"):
            hits = total = 0
            for m in messages:
                if off + 2 >= len(m):
                    continue
                total += 1
                if end == "le":
                    decl = m[off] | (m[off + 1] << 8)
                else:
                    decl = (m[off] << 8) | m[off + 1]
                rest = len(m) - off - 2
                if decl == rest or abs(decl - rest) <= 2:
                    hits += 1
            if total:
                score = hits / total
                if score >= 0.5:
                    cands.append({"offset": off, "kind": f"u16_{end}", "score": round(score, 3)})
        vs = _score_varint_length(messages, off)
        if vs >= 0.5:
            cands.append({"offset": off, "kind": "varint", "score": round(vs, 3)})
    return sorted(cands, key=lambda x: -x["score"])[:5]


def _entropy_note(payloads: list[bytes]) -> str:
    ratio = len(set(b for p in payloads[:10] for b in p[:16])) / max(1, min(16, min(len(p) for p in payloads)))
    if ratio > 0.85:
        return "висока ентропія → шукаємо вкладені кадри"
    return "структурований шар"


def _format_deep(deep: dict) -> list[str]:
    kind = deep.get("kind", "?")
    lines: list[str] = []
    if kind == "tls":
        lines.append(f"TLS: {deep.get('records', 0)} records, {deep.get('client_hellos', 0)} ClientHello")
        if deep.get("sni_hosts"):
            lines.append(f"SNI: {', '.join(deep['sni_hosts'][:8])}")
    elif kind == "quic":
        lines.append(
            f"QUIC: long={deep.get('long_header', 0)} short={deep.get('short_header', 0)} "
            f"types={deep.get('types', {})}"
        )
        if deep.get("versions"):
            lines.append(f"versions: {deep['versions']}")
        sample = deep.get("sample", {})
        if sample:
            lines.append(
                f"sample: {sample.get('type', sample.get('form'))} "
                f"ver={sample.get('version_name', '?')} len={sample.get('length', sample.get('length', '?'))}"
            )
    elif kind == "dns":
        lines.append(f"DNS: {deep.get('parsed', 0)}/{deep.get('packets', 0)} parsed")
        if deep.get("domains"):
            lines.append(f"domains: {', '.join(deep['domains'][:8])}")
    elif kind == "ntp":
        lines.append(f"NTP: {deep.get('parsed', 0)}×48B modes={deep.get('modes', {})}")
    elif kind == "xmpp":
        lines.append(
            f"XMPP: protobuf={deep.get('protobuf_like', 0)} xml={deep.get('xml_streams', 0)} "
            f"len-framed={deep.get('length_prefixed', 0)}"
        )
        if deep.get("protobuf_fields"):
            lines.append(f"protobuf fields: {deep['protobuf_fields']}")
        for note in deep.get("notes", []):
            lines.append(note)
    return lines


def blind_analyze(label: str, payloads: list[bytes]) -> dict:
    notes: list[str] = [_entropy_note(payloads)]
    outer = discover_format(payloads)
    splits = _find_best_length_offset(payloads)
    inner: dict | None = None
    deep: dict | None = None

    deep = deep_analyze_flow(label, payloads)

    if deep:
        notes.extend(_format_deep(deep))
        if deep.get("kind") == "tls":
            _, tls_frames = split_tls_records(payloads)
            if tls_frames:
                inner = discover_format(tls_frames)
                notes.append(
                    "внутрішній AST: "
                    + ", ".join(f"{f['kind']}@{f['offset']}" for f in inner.get("fields", [])[:6])
                )
        elif deep.get("kind") == "quic":
            notes.append("QUIC varint header parsed")
        elif deep.get("kind") == "dns":
            inner = discover_format(payloads)
        elif deep.get("kind") == "ntp":
            inner = discover_format(payloads)
    else:
        tls_rate, tls_frames = _score_tls_like(payloads)
        quic_rate, quic_frames = _split_quic_packets(payloads)
        if tls_rate >= 0.6:
            notes.append(f"вкладені кадри type|ver|len: {tls_rate:.0%} ({len(tls_frames)} кадрів)")
            if tls_frames:
                inner = discover_format(tls_frames)
                notes.append(
                    "внутрішній AST: "
                    + ", ".join(f"{f['kind']}@{f['offset']}" for f in inner.get("fields", [])[:6])
                )
        elif quic_rate >= 0.5:
            long_n = sum(1 for p in quic_frames if p[0] & 0x80)
            notes.append(f"UDP-кадри (QUIC-подібні): {quic_rate:.0%}, long-header={long_n}")
            if quic_frames:
                inner = discover_format(quic_frames)
        elif splits:
            notes.append(f"length-кандидат: {splits[0]}")

    return {
        "flow": label,
        "packets": len(payloads),
        "outer_format": outer,
        "length_splits": splits,
        "inner_format": inner,
        "deep": deep,
        "notes": notes,
    }


def _flow_matches(label: str, flow_filter: str) -> bool:
    needle = flow_filter.strip().upper()
    if ":" in needle:
        return label.upper() == needle
    return label.split(":")[-1] == needle


def _print_flow(label: str, payloads: list[bytes], blind: bool) -> dict:
    print(f"── {label}  packets={len(payloads)}  len={min(map(len,payloads))}..{max(map(len,payloads))}")
    if blind:
        result = blind_analyze(label, payloads)
        for note in result["notes"]:
            print(f"   • {note}")
        if result.get("inner_format"):
            print("   внутрішні поля:")
            for f in result["inner_format"].get("fields", [])[:8]:
                print(f"     {f['name']:12} {f['kind']:8} @{f['offset']}")
        return result

    fmt = discover_format(payloads)
    for f in fmt.get("fields", [])[:12]:
        print(f"   {f['name']:12} {f['kind']:8} @{f['offset']}")
    if fmt.get("length_offset") is not None:
        print(f"   length @{fmt['length_offset']} ({fmt['endian']})")
    sample = payloads[0][:32].hex()
    print(f"   sample: {sample}{'...' if len(payloads[0])>32 else ''}")
    return {"flow": label, "packets": len(payloads), "format": fmt}


def main() -> int:
    parser = argparse.ArgumentParser(description="PCAP analyzer for Termux/Android")
    parser.add_argument("--version", action="version", version=f"analyze_pcap {VERSION}")
    parser.add_argument("pcap", nargs="?", help="path to .pcap file")
    parser.add_argument("--blind", action="store_true", help="blind deep analysis (TLS/QUIC inner frames)")
    parser.add_argument("--flow", help="filter flow, e.g. 443 or TCP:443")
    args = parser.parse_args()

    print(f"analyze_pcap: старт v{VERSION} (deep decode embedded)", flush=True)
    if not args.pcap:
        parser.print_help()
        return 1
    path = Path(args.pcap).expanduser()
    if not path.exists():
        print(f"Файл не знайдено: {path}", file=sys.stderr)
        print("На телефоні файл зазвичай: ~/downloads/PCAPdroid*.pcap", file=sys.stderr)
        return 1
    print(f"PCAP: {path} ({path.stat().st_size} bytes)\n")
    flows = extract_flows(path)
    if not flows:
        print("Потоків не знайдено. Спробуйте інший pcap.")
        return 1

    selected = flows
    if args.flow:
        selected = {k: v for k, v in flows.items() if _flow_matches(k, args.flow)}
        if not selected:
            print(f"Потік '{args.flow}' не знайдено. Доступні:", ", ".join(sorted(flows)))
            return 1

    report = {"file": str(path), "blind": args.blind, "flows": []}
    for label in sorted(selected, key=lambda k: -len(selected[k])):
        entry = _print_flow(label, selected[label], args.blind)
        print()
        report["flows"].append(entry)
    out = path.parent / ("blind_report.json" if args.blind else "probe_report.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Звіт: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
