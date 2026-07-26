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
import os
import re
import struct
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

VERSION = "3.8.15-full"
MAX_EXPORT_FIELDS = 32

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


def parse_quic_packet(data: bytes, *, permit_short: bool = False) -> dict | None:
    if len(data) < 5:
        return None
    if not (data[0] & 0x80):
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


def _parse_client_hello(body: bytes) -> dict | None:
    if len(body) < 38 or body[0] != 0x01:
        return None
    pos = 6 + 32
    sid_len = body[pos]
    pos += 1 + sid_len + 2
    cs_len = struct.unpack(">H", body[pos - 2 : pos])[0]
    pos += cs_len + 1
    cm_len = body[pos]
    pos += 1 + cm_len + 2
    ext_len = struct.unpack(">H", body[pos - 2 : pos])[0]
    pos += 0
    end = pos + ext_len
    sni: list[str] = []
    alpn: list[str] = []
    extensions: list[str] = []
    while pos + 4 <= end:
        etype, elen = struct.unpack(">HH", body[pos : pos + 4])
        pos += 4
        edata = body[pos : pos + elen]
        pos += elen
        extensions.append({0: "server_name", 16: "alpn", 43: "supported_versions"}.get(etype, f"ext_{etype}"))
        if etype == 0 and len(edata) >= 5:
            p = 2
            while p + 3 <= len(edata):
                if edata[p] == 0:
                    nlen = struct.unpack(">H", edata[p + 1 : p + 3])[0]
                    sni.append(edata[p + 3 : p + 3 + nlen].decode("ascii", errors="replace"))
                    p += 3 + nlen
                else:
                    p += 1
        elif etype == 16 and len(edata) >= 2:
            p = 2
            while p < len(edata):
                ln = edata[p]
                p += 1
                alpn.append(edata[p : p + ln].decode("ascii", errors="replace"))
                p += ln
    return {"sni": sni, "alpn": alpn, "extensions": extensions}


def analyze_tls_flow(payloads: list[bytes]) -> dict:
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
            detail = _parse_client_hello(body) or {}
            hosts = detail.get("sni", [])
            sni_hosts.extend(hosts)
            alpn_list.extend(detail.get("alpn", []))
            handshakes.append({"type": "ClientHello", "sni": hosts, "alpn": detail.get("alpn", []), "extensions": detail.get("extensions", [])})
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

# --- PCAP / PCAPNG ---
PCAP_MAGIC_LE = 0xA1B2C3D4
PCAP_MAGIC_BE = 0xD4C3B2A1
PCAPNG_MAGIC = 0x0A0D0D0A
BT_EPB = 0x00000006
BT_IDB = 0x00000001
ETH_P_IP = 0x0800
ETH_P_IP6 = 0x86DD
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


def _parse_l4(proto: int, ip: bytes) -> tuple[str, int, int, bytes, int | None] | None:
    if proto == 17 and len(ip) >= 8:
        s, d, u = struct.unpack(">HHH", ip[:6])
        return "udp", s, d, ip[8:u], None
    if proto == 6 and len(ip) >= 20:
        s, d, seq = struct.unpack(">HHI", ip[:8])
        off = ((ip[12] >> 4) & 0x0F) * 4
        return "tcp", s, d, ip[off:], seq
    return None


def _parse_ipv4(frame: bytes, offset: int) -> tuple[str, int, int, bytes, int | None] | None:
    data = frame[offset:]
    if len(data) < 20 or (data[0] >> 4) != 4:
        return None
    ihl = (data[0] & 0x0F) * 4
    total = struct.unpack(">H", data[2:4])[0]
    return _parse_l4(data[9], data[ihl:total])


def _skip_ipv6_ext(data: bytes, off: int, nxt: int) -> tuple[int, int] | None:
    while nxt in (0, 43, 44, 60, 51):
        if nxt == 44:
            if off + 8 > len(data):
                return None
            nxt = data[off]
            off += 8
            continue
        if off + 2 > len(data):
            return None
        nxt = data[off]
        ext_len = data[off + 1]
        off += 2 + ext_len * 8
        if off > len(data):
            return None
    return off, nxt


def _parse_ipv6(frame: bytes, offset: int) -> tuple[str, int, int, bytes, int | None] | None:
    data = frame[offset:]
    if len(data) < 40 or (data[0] >> 4) != 6:
        return None
    payload_len = struct.unpack(">H", data[4:6])[0]
    nxt = data[6]
    off = 40
    if nxt not in (6, 17):
        skipped = _skip_ipv6_ext(data, off, nxt)
        if not skipped:
            return None
        off, nxt = skipped
    return _parse_l4(nxt, data[off : 40 + payload_len])


def _extract(frame: bytes, link: int) -> tuple[str, int, int, bytes, int | None] | None:
    if link == 1 and len(frame) >= 14:
        eth_type = struct.unpack(">H", frame[12:14])[0]
        if eth_type == ETH_P_IP:
            return _parse_ipv4(frame, 14)
        if eth_type == ETH_P_IP6:
            return _parse_ipv6(frame, 14)
    if link == 113 and len(frame) >= 16:
        eth_type = struct.unpack(">H", frame[14:16])[0]
        if eth_type == ETH_P_IP:
            return _parse_ipv4(frame, 16)
        if eth_type == ETH_P_IP6:
            return _parse_ipv6(frame, 16)
    if link == 0 and len(frame) >= 4:
        family = struct.unpack("<I", frame[:4])[0]
        if family == 2:
            return _parse_ipv4(frame, 4)
        if family in (10, 30):
            return _parse_ipv6(frame, 4)
    if link == 101:
        if len(frame) >= 1 and (frame[0] >> 4) == 4:
            return _parse_ipv4(frame, 0)
        if len(frame) >= 1 and (frame[0] >> 4) == 6:
            return _parse_ipv6(frame, 0)
    return None


def _iter_classic_pcap(data: bytes, endian: str) -> tuple[int, list[tuple[int, bytes]]]:
    link = struct.unpack(endian + "IHHiIII", data[:24])[6]
    packets: list[tuple[int, bytes]] = []
    off = 24
    while off + 16 <= len(data):
        _, _, caplen, _ = struct.unpack(endian + "IIII", data[off : off + 16])
        off += 16
        packets.append((link, data[off : off + caplen]))
        off += caplen
    return link, packets


def _iter_pcapng(data: bytes) -> list[tuple[int, bytes]]:
    packets: list[tuple[int, bytes]] = []
    link_type = 1
    off = 0
    while off + 8 <= len(data):
        block_type, block_len = struct.unpack("<II", data[off : off + 8])
        if block_len < 12 or off + block_len > len(data):
            break
        body = data[off + 8 : off + block_len - 4]
        if block_type == BT_IDB and len(body) >= 2:
            link_type = struct.unpack("<H", body[:2])[0]
        elif block_type == BT_EPB and len(body) >= 20:
            caplen = struct.unpack("<I", body[12:16])[0]
            pkt = body[20 : 20 + caplen]
            if pkt:
                packets.append((link_type, pkt))
        off += block_len
    return packets


def iter_pcap(path: Path):
    data = path.read_bytes()
    if len(data) < 4:
        return
    magic = struct.unpack("<I", data[:4])[0]
    if magic == PCAPNG_MAGIC:
        for item in _iter_pcapng(data):
            yield item
        return
    endian = "<"
    if magic in (PCAP_MAGIC_BE, 0x4D3CB2A1):
        endian = ">"
    _, packets = _iter_classic_pcap(data, endian)
    for item in packets:
        yield item


def _iter_tls_stream(stream: bytes) -> list[bytes]:
    records: list[bytes] = []
    offset = 0
    while offset + 5 <= len(stream):
        ctype = stream[offset]
        if ctype not in range(20, 26) or stream[offset + 1] != 3:
            break
        ln = (stream[offset + 3] << 8) | stream[offset + 4]
        end = offset + 5 + ln
        if end > len(stream):
            break
        records.append(stream[offset:end])
        offset = end
    return records


def _reassemble_tcp(segments: list[tuple[int, int, int, bytes]]) -> list[bytes]:
    """segments: (sport, dport, seq, payload) → TLS records or streams."""
    subflows: dict[tuple[int, int], list[tuple[int, bytes]]] = {}
    for sport, dport, seq, payload in segments:
        subflows.setdefault((sport, dport), []).append((seq, payload))
    messages: list[bytes] = []
    seen: set[bytes] = set()
    for segs in subflows.values():
        ordered = sorted(segs, key=lambda x: x[0])
        stream = bytearray()
        cursor: int | None = None
        for seq, payload in ordered:
            if cursor is None:
                cursor = seq
            if seq > cursor:
                cursor = seq
            skip = max(0, cursor - seq)
            chunk = payload[skip:]
            if chunk:
                stream.extend(chunk)
                cursor = seq + skip + len(chunk)
        data = bytes(stream)
        recs = _iter_tls_stream(data)
        for item in (recs if recs else [data]):
            if item and item not in seen:
                seen.add(item)
                messages.append(item)
    return messages


def extract_flows(
    path: Path,
    min_pkts: int = 2,
    min_len: int = 4,
    *,
    tcp_reassemble: bool = False,
) -> dict[str, list[bytes]]:
    payloads: dict[FlowKey, list[bytes]] = {}
    tcp_segs: dict[FlowKey, list[tuple[int, int, int, bytes]]] = {}
    counts: dict[FlowKey, int] = {}
    for link, frame in iter_pcap(path):
        p = _extract(frame, link)
        if not p:
            continue
        proto, sport, dport, payload, seq = p
        if len(payload) < min_len:
            continue
        key = _flow_key(proto, sport, dport)
        counts[key] = counts.get(key, 0) + 1
        if proto == "tcp" and tcp_reassemble and seq is not None:
            tcp_segs.setdefault(key, []).append((sport, dport, seq, payload))
        else:
            payloads.setdefault(key, []).append(payload)
    out: dict[str, list[bytes]] = {}
    for key, n in counts.items():
        if n < min_pkts:
            continue
        if key in tcp_segs and tcp_reassemble:
            out[key.label] = _reassemble_tcp(tcp_segs[key])
        else:
            out[key.label] = payloads.get(key, [])
    return out


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
    if not payloads:
        return "порожньо"
    # TLS handshake bodies: first byte is type (ClientHello=1, …); random fields inflate entropy
    hs_types = {1, 2, 4, 8, 11, 12, 13, 14, 15, 16, 20}
    hs = sum(1 for m in payloads if m and m[0] in hs_types)
    if hs >= max(1, len(payloads) // 2):
        return "структурований шар (TLS handshake)"
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


def _all_tls_records(messages: list[bytes]) -> bool:
    for m in messages:
        if len(m) < 5 or m[0] not in range(20, 26) or m[1] != 3:
            return False
        if 5 + ((m[3] << 8) | m[4]) != len(m):
            return False
    return bool(messages)


def _is_quic_flow(flow: str) -> bool:
    u = flow.upper()
    return u.startswith("UDP") and u.endswith(":443")


def _split_http2_frames(messages: list[bytes]) -> tuple[str, list[bytes]] | None:
    try:
        from protocol_ast.http2 import split_http2_frames

        return split_http2_frames(messages)
    except Exception:
        return _embedded_split_http2(messages)


def _embedded_split_http2(messages: list[bytes]) -> tuple[str, list[bytes]] | None:
    def _single(m: bytes) -> bool:
        if len(m) < 9:
            return False
        ln = int.from_bytes(m[:3], "big")
        return 9 + ln == len(m) and m[3] <= 0x1F

    if messages and all(_single(m) for m in messages):
        data = []
        for m in messages:
            if m[3] == 0x0:
                ln = int.from_bytes(m[:3], "big")
                payload = m[9 : 9 + ln]
                if payload:
                    data.append(payload)
        return ("http2_data", data) if data else None

    preface = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
    frames: list[bytes] = []
    grew = False
    for m in messages:
        if _single(m):
            frames.append(m)
            continue
        data = m[len(preface) :] if m.startswith(preface) else m
        off = 0
        local: list[bytes] = []
        while off + 9 <= len(data):
            ln = int.from_bytes(data[off : off + 3], "big")
            if ln > 16640 or off + 9 + ln > len(data):
                break
            local.append(data[off : off + 9 + ln])
            off += 9 + ln
        if local:
            frames.extend(local)
            if len(local) > 1:
                grew = True
    if len(frames) >= 2 and (grew or len(frames) > len(messages)):
        return "http2_frames", frames
    if frames and all(_single(f) for f in frames):
        data = [f[9:] for f in frames if f[3] == 0x0 and len(f) > 9]
        return ("http2_data", data) if data else None
    return None


def _http2_deep(
    frames: list[bytes],
    splitter: str = "http2_frames",
    *,
    source_frames: list[bytes] | None = None,
) -> dict:
    try:
        from protocol_ast.http2 import http2_data_deep, http2_deep

        if splitter == "http2_data":
            return http2_data_deep(frames, source_frames=source_frames)
        return http2_deep(frames)
    except Exception:
        if splitter == "http2_data":
            previews = []
            for p in frames[:3]:
                s = p[:80]
                previews.append(s.decode("utf-8", errors="replace") if s else "")
            return {"kind": "http2_data", "payloads": len(frames), "preview": previews}
        names = {
            0: "DATA", 1: "HEADERS", 2: "PRIORITY", 3: "RST_STREAM",
            4: "SETTINGS", 5: "PUSH_PROMISE", 6: "PING", 7: "GOAWAY",
            8: "WINDOW_UPDATE", 9: "CONTINUATION",
        }
        types: dict[str, int] = {}
        streams: set[int] = set()
        for f in frames:
            if len(f) < 9:
                continue
            t = names.get(f[3], f"type{f[3]}")
            types[t] = types.get(t, 0) + 1
            sid = int.from_bytes(f[5:9], "big") & 0x7FFFFFFF
            if sid:
                streams.add(sid)
        return {"kind": "http2", "frames": types, "streams": len(streams), "total_frames": sum(types.values())}


def _pick_nested_splitter(messages: list[bytes], depth: int, flow: str = "") -> tuple[str, list[bytes]] | None:
    if depth > 0 and _all_tls_records(messages):
        bodies = [m[5:] for m in messages if len(m) > 5 and m[0] == 0x16]
        return ("tls_handshake", bodies) if len(bodies) >= 2 else None
    if depth > 0:
        h2 = _split_http2_frames(messages)
        if h2:
            return h2
    rate, frames = split_tls_records(messages)
    if rate >= 0.6 and len(frames) >= 2:
        return "tls_record", frames
    h2 = _split_http2_frames(messages)
    if h2:
        return h2
    long_valid = sum(
        1 for m in messages if len(m) >= 5 and (m[0] & 0xC0) == 0xC0 and parse_quic_packet(m, permit_short=False)
    )
    permit_short = long_valid >= 2
    quic = [m for m in messages if parse_quic_packet(m, permit_short=permit_short)]
    if len(quic) >= max(2, len(messages) // 2) and len(quic) < len(messages):
        return "quic_packet", quic
    return None


def _sequitur_rules_estimate(messages: list[bytes]) -> int:
    pairs: set[tuple[int, int]] = set()
    for m in messages[:12]:
        for i in range(min(len(m) - 1, 47)):
            pairs.add((m[i], m[i + 1]))
    return len(pairs)


def _handshake_layer_deep(messages: list[bytes]) -> dict:
    names = {
        1: "ClientHello", 2: "ServerHello", 4: "NewSessionTicket",
        8: "EncryptedExtensions", 11: "Certificate", 20: "Finished",
    }
    types: dict[str, int] = {}
    sni: list[str] = []
    alpn: list[str] = []
    for m in messages:
        if not m:
            continue
        types[names.get(m[0], f"type{m[0]}")] = types.get(names.get(m[0], f"type{m[0]}"), 0) + 1
        if m[0] == 1:
            detail = _parse_client_hello(m) or {}
            sni.extend(detail.get("sni", []))
            alpn.extend(detail.get("alpn", []))
    return {
        "kind": "tls_handshake",
        "types": types,
        "sni_hosts": sorted(set(sni))[:20],
        "alpn": sorted(set(alpn))[:10],
    }


def _peel_tls_handshake_bodies(messages: list[bytes]) -> list[bytes]:
    bodies: list[bytes] = []
    for m in messages:
        if len(m) >= 6 and m[0] == 0x16 and m[1] == 3:
            ln = (m[3] << 8) | m[4]
            end = 5 + ln
            if end <= len(m):
                bodies.append(m[5:end])
            elif len(m) > 5:
                bodies.append(m[5:])
    return bodies


def recursive_nested_analyze(
    flow: str,
    messages: list[bytes],
    *,
    depth: int = 0,
    max_depth: int = 3,
    label: str | None = None,
    keylog: str | None = None,
) -> dict:
    label = label or flow
    layer: dict = {
        "label": label,
        "depth": depth,
        "messages": len(messages),
        "entropy": "high" if "висока" in _entropy_note(messages) else "structured",
        "format": discover_format(messages),
        "splitter": None,
        "deep": None,
        "clusters": None,
        "sequitur_rules": _sequitur_rules_estimate(messages),
        "opaque": False,
        "decrypt": None,
        "children": [],
    }
    if depth == 0:
        layer["deep"] = deep_analyze_flow(flow, messages)
        opcodes = Counter(m[0] for m in messages if m)
        layer["clusters"] = len([v for v in opcodes.values() if v >= 2])
    elif "tls_handshake" in label.lower():
        # Only label-driven: first-byte heuristics false-positive on protobuf (tag 0x08 etc.)
        layer["deep"] = _handshake_layer_deep(messages)
    if depth >= max_depth or len(messages) < 2:
        return layer

    # High entropy: HTTP/2 / handshake / keylog before opaque wall
    if layer["entropy"] == "high" and depth > 0:
        # Preserve already-enriched http2_data leaf
        if layer.get("deep") and layer["deep"].get("kind") == "http2_data":
            try:
                from protocol_ast.body_peel import body_deep

                charset = None
                for h in layer["deep"].get("headers") or []:
                    ct = h.get("content-type") or ""
                    if "charset=" in ct.lower():
                        charset = ct.split("charset=", 1)[-1].split(";")[0].strip()
                        break
                layer["deep"]["content"] = body_deep(messages, charset=charset)
            except Exception:
                pass
            try:
                from protocol_ast.json_api import json_api_deep, looks_like_json_api

                if looks_like_json_api(messages):
                    api = json_api_deep(messages, headers=layer["deep"].get("headers"))
                    layer["deep"]["json_api"] = api
                    layer["children"].append({
                        "label": f"{label}/json_api",
                        "depth": depth + 1,
                        "messages": len(messages),
                        "splitter": "json_api",
                        "entropy": "structured",
                        "deep": api,
                        "children": [],
                        "opaque": False,
                    })
            except Exception:
                pass
            layer["entropy"] = "structured"
            return layer
        h2 = _split_http2_frames(messages)
        if h2:
            name, frames = h2
            layer["splitter"] = name
            layer["deep"] = _http2_deep(
                frames, name, source_frames=messages if name == "http2_data" else None
            )
            layer["entropy"] = "structured"
            child = recursive_nested_analyze(
                flow, frames, depth=depth + 1, max_depth=max_depth,
                label=f"{label}/{name}", keylog=None,
            )
            # Restore enrichment (child recurse may have lost stream/encoding meta)
            if name == "http2_data" and layer["deep"]:
                child["deep"] = dict(layer["deep"])
                child["entropy"] = "structured"
                child["opaque"] = False
                try:
                    from protocol_ast.body_peel import body_deep

                    charset = None
                    for h in child["deep"].get("headers") or []:
                        ct = h.get("content-type") or ""
                        if "charset=" in ct.lower():
                            charset = ct.split("charset=", 1)[-1].split(";")[0].strip()
                            break
                    child["deep"]["content"] = body_deep(frames, charset=charset)
                except Exception:
                    pass
            layer["children"].append(child)
            return layer
        # HTTP/1.1 after TLS decrypt (game APIs often use HTTP/1 + gzip + protobuf)
        try:
            from protocol_ast.http2 import http1_body_messages, http1_deep, looks_like_http1

            if looks_like_http1(messages):
                h1 = http1_deep(messages)
                layer["splitter"] = "http1"
                # Do not persist raw body bytes into JSON report
                layer["deep"] = {k: v for k, v in h1.items() if k != "bodies"}
                layer["entropy"] = "structured"
                bodies = http1_body_messages(h1)
                if bodies:
                    layer["children"].append(
                        recursive_nested_analyze(
                            flow,
                            bodies,
                            depth=depth + 1,
                            max_depth=max_depth,
                            label=f"{label}/http1_body",
                            keylog=None,
                        )
                    )
                return layer
        except Exception:
            pass
        try:
            from protocol_ast.body_peel import body_deep, looks_like_app_body

            if looks_like_app_body(messages):
                layer["splitter"] = "app_body"
                layer["deep"] = body_deep(messages)
                layer["entropy"] = "structured"
                try:
                    from protocol_ast.json_api import json_api_deep, looks_like_json_api

                    if looks_like_json_api(messages):
                        api = json_api_deep(messages)
                        layer["deep"]["json_api"] = api
                        layer["children"].append({
                            "label": f"{label}/json_api",
                            "depth": depth + 1,
                            "messages": len(messages),
                            "splitter": "json_api",
                            "entropy": "structured",
                            "deep": api,
                            "children": [],
                            "opaque": False,
                        })
                except Exception:
                    pass
                return layer
        except Exception:
            pass
        try:
            from protocol_ast.binary_peel import binary_peel

            bin_deep = binary_peel(messages)
            if bin_deep:
                name = bin_deep["kind"]
                layer["splitter"] = name
                layer["deep"] = bin_deep
                layer["entropy"] = "structured"
                layer["children"].append({
                    "label": f"{label}/{name}",
                    "depth": depth + 1,
                    "messages": len(messages),
                    "splitter": name,
                    "entropy": "structured",
                    "deep": bin_deep,
                    "children": [],
                    "opaque": False,
                })
                return layer
        except Exception:
            pass
        bodies = _peel_tls_handshake_bodies(messages)
        if len(bodies) >= 1:
            layer["splitter"] = "tls_handshake"
            layer["children"].append(
                recursive_nested_analyze(
                    flow, bodies, depth=depth + 1, max_depth=max_depth,
                    label=f"{label}/tls_handshake", keylog=keylog,
                )
            )
        dec = _try_keylog_decrypt(messages, keylog)
        if dec:
            layer["decrypt"] = dec["meta"]
            if dec["plain"]:
                layer["children"].append(
                    recursive_nested_analyze(
                        flow, dec["plain"], depth=depth + 1, max_depth=max_depth,
                        label=f"{label}/decrypted", keylog=None,
                    )
                )
        if not layer["children"]:
            layer["opaque"] = True
        return layer

    # Structured layers can still be HTTP/1.1 / app bodies (mixed with TLS leftovers)
    if depth > 0:
        try:
            from protocol_ast.http2 import http1_body_messages, http1_deep, looks_like_http1

            if looks_like_http1(messages):
                h1 = http1_deep(messages)
                layer["splitter"] = "http1"
                layer["deep"] = {k: v for k, v in h1.items() if k != "bodies"}
                layer["entropy"] = "structured"
                bodies = http1_body_messages(h1)
                if bodies:
                    layer["children"].append(
                        recursive_nested_analyze(
                            flow,
                            bodies,
                            depth=depth + 1,
                            max_depth=max_depth,
                            label=f"{label}/http1_body",
                            keylog=None,
                        )
                    )
                return layer
        except Exception:
            pass
        try:
            from protocol_ast.body_peel import body_deep, looks_like_app_body

            if looks_like_app_body(messages):
                layer["splitter"] = "app_body"
                layer["deep"] = body_deep(messages)
                layer["entropy"] = "structured"
                return layer
        except Exception:
            pass
        try:
            from protocol_ast.binary_peel import binary_peel

            bin_deep = binary_peel(messages)
            if bin_deep:
                name = bin_deep["kind"]
                layer["splitter"] = name
                layer["deep"] = bin_deep
                layer["entropy"] = "structured"
                return layer
        except Exception:
            pass

    split = _pick_nested_splitter(messages, depth, flow)
    if not split:
        dec = _try_keylog_decrypt(messages, keylog)
        if dec:
            layer["decrypt"] = dec["meta"]
            if dec["plain"]:
                layer["children"].append(
                    recursive_nested_analyze(
                        flow, dec["plain"], depth=depth + 1, max_depth=max_depth,
                        label=f"{label}/decrypted", keylog=None,
                    )
                )
        return layer
    splitter_name, inner = split
    layer["splitter"] = splitter_name
    if splitter_name in ("http2_frames", "http2_data"):
        layer["deep"] = _http2_deep(
            inner, splitter_name, source_frames=messages if splitter_name == "http2_data" else None
        )
        layer["entropy"] = "structured"
    if len(inner) < 2:
        return layer
    child = recursive_nested_analyze(
        flow, inner, depth=depth + 1, max_depth=max_depth, label=f"{label}/{splitter_name}", keylog=keylog
    )
    layer["children"].append(child)

    if splitter_name == "tls_record":
        bodies = _peel_tls_handshake_bodies(inner)
        if bodies:
            layer["children"].append(
                recursive_nested_analyze(
                    flow, bodies, depth=depth + 1, max_depth=max_depth,
                    label=f"{label}/tls_handshake", keylog=keylog,
                )
            )
        dec = _try_keylog_decrypt(inner, keylog)
        if dec:
            layer["decrypt"] = dec["meta"]
            if dec["plain"]:
                layer["children"].append(
                    recursive_nested_analyze(
                        flow, dec["plain"], depth=depth + 1, max_depth=max_depth,
                        label=f"{label}/decrypted", keylog=None,
                    )
                )
    return layer


def _try_keylog_decrypt(records: list[bytes], keylog: str | None) -> dict | None:
    if not keylog:
        return None
    path = Path(keylog).expanduser()
    if not path.exists():
        return None
    try:
        from protocol_ast.tls_keylog import decrypt_tls_records, keylog_summary, parse_keylog
    except ImportError:
        try:
            return _embedded_keylog_decrypt(records, path)
        except Exception as exc:
            return {"meta": {"status": "error", "error": str(exc)}, "plain": []}
    secrets = parse_keylog(path)
    result = decrypt_tls_records(records, secrets)
    if not result or not result.decrypted:
        diag = (result.diagnostics if result else {}) or {}
        return {
            "meta": {
                "status": diag.get("reason", "no_match"),
                "keylog": keylog_summary(secrets),
                "diag": diag,
            },
            "plain": [],
        }
    return {
        "meta": {
            "status": "ok",
            "tls_version": result.tls_version,
            "decrypted": len(result.decrypted),
            "failed": result.failed,
            "secrets": result.secrets_matched,
        },
        "plain": result.decrypted,
    }


def _apply_decrypt_child(layer: dict, flow: str, records: list[bytes], depth: int, max_depth: int, label: str, keylog: str | None) -> None:
    dec = _try_keylog_decrypt(records, keylog)
    if not dec:
        return
    layer["decrypt"] = dec["meta"]
    if dec["plain"]:
        layer["children"].append(
            recursive_nested_analyze(
                flow, dec["plain"], depth=depth + 1, max_depth=max_depth,
                label=f"{label}/decrypted", keylog=None,
            )
        )


def _gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, aad: bytes) -> bytes | None:
    """AES-GCM decrypt: cryptography → pure Python (no pip build on Termux)."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        return AESGCM(key).decrypt(nonce, ciphertext, aad)
    except Exception:
        pass
    import sys

    for root in (Path(__file__).resolve().parent, Path.home()):
        mod = root / "protocol_ast" / "aes_gcm.py"
        if mod.exists() and str(root) not in sys.path:
            sys.path.insert(0, str(root))
        try:
            from protocol_ast.aes_gcm import _pure_aes_gcm_decrypt

            return _pure_aes_gcm_decrypt(key, nonce, ciphertext, aad)
        except Exception:
            continue
    return None


def _embedded_keylog_decrypt(records: list[bytes], path: Path) -> dict | None:
    """Termux TLS keylog decrypt — cryptography optional; pure AES via protocol_ast/aes_gcm.py."""
    import hashlib
    import hmac as hmac_mod

    master: dict[str, bytes] = {}
    c_traffic: dict[str, bytes] = {}
    s_traffic: dict[str, bytes] = {}
    lines = 0
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        label, cr, sec = parts[0], parts[1].lower(), parts[2]
        try:
            secret = bytes.fromhex(sec)
        except ValueError:
            continue
        lines += 1
        if label == "CLIENT_RANDOM":
            master[cr] = secret
        elif label == "CLIENT_TRAFFIC_SECRET_0":
            c_traffic[cr] = secret
        elif label == "SERVER_TRAFFIC_SECRET_0":
            s_traffic[cr] = secret

    def hkdf_expand(secret: bytes, info: bytes, length: int) -> bytes:
        out = b""
        prev = b""
        i = 1
        while len(out) < length:
            prev = hmac_mod.new(secret, prev + info + bytes([i]), hashlib.sha256).digest()
            out += prev
            i += 1
        return out[:length]

    def expand_label(secret: bytes, label: bytes, length: int) -> bytes:
        full = b"tls13 " + label
        info = struct.pack(">H", length) + bytes([len(full)]) + full + b"\x00"
        return hkdf_expand(secret, info, length)

    def decrypt13(rec: bytes, key: bytes, iv: bytes, seq: int) -> bytes | None:
        if len(rec) < 21 or rec[0] != 0x17:
            return None
        ln = (rec[3] << 8) | rec[4]
        ct = rec[5 : 5 + ln]
        nonce = bytearray(iv)
        for i in range(8):
            nonce[11 - i] ^= (seq >> (8 * i)) & 0xFF
        plain = _gcm_decrypt(key, bytes(nonce), ct, rec[:5])
        return plain[:-1] if plain else None

    # Probe decrypt backend availability
    has_backend = True
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except ImportError:
        has_backend = any(
            (p / "protocol_ast" / "aes_gcm.py").exists()
            for p in (Path(__file__).resolve().parent, Path.home())
        )
    if not has_backend:
        return {
            "meta": {
                "status": "error",
                "error": "need AES-GCM: mkdir -p ~/protocol_ast && curl aes_gcm.py into it (see termux_analyze.txt)",
            },
            "plain": [],
        }

    randoms: list[str] = []
    for rec in records:
        if len(rec) >= 43 and rec[0] == 0x16:
            body = rec[5:]
            if body and body[0] == 0x01 and len(body) >= 38:
                randoms.append(body[6:38].hex())
    candidates = randoms or list(set(c_traffic) | set(s_traffic) | set(master))

    for cr in candidates:
        c_sec, s_sec = c_traffic.get(cr), s_traffic.get(cr)
        if not (c_sec or s_sec):
            continue
        decrypted: list[bytes] = []
        failed = 0
        c_seq = s_seq = 0
        c_kv = (expand_label(c_sec, b"key", 16), expand_label(c_sec, b"iv", 12)) if c_sec else None
        s_kv = (expand_label(s_sec, b"key", 16), expand_label(s_sec, b"iv", 12)) if s_sec else None
        for rec in records:
            if len(rec) < 5 or rec[0] != 0x17:
                continue
            ok = None
            if c_kv:
                ok = decrypt13(rec, c_kv[0], c_kv[1], c_seq)
                if ok is not None:
                    c_seq += 1
                    decrypted.append(ok)
                    continue
            if s_kv:
                ok = decrypt13(rec, s_kv[0], s_kv[1], s_seq)
                if ok is not None:
                    s_seq += 1
                    decrypted.append(ok)
                    continue
            failed += 1
        if decrypted:
            return {
                "meta": {
                    "status": "ok",
                    "tls_version": "1.3",
                    "decrypted": len(decrypted),
                    "failed": failed,
                    "secrets": [s for s, v in (("CLIENT_TRAFFIC_SECRET_0", c_sec), ("SERVER_TRAFFIC_SECRET_0", s_sec)) if v],
                    "keylog": {"lines": lines, "client_randoms": len(set(c_traffic) | set(s_traffic) | set(master))},
                },
                "plain": decrypted,
            }

    return {
        "meta": {
            "status": "no_match",
            "keylog": {"lines": lines, "client_randoms": len(set(c_traffic) | set(s_traffic) | set(master))},
        },
        "plain": [],
    }


def format_nested_notes(layer: dict) -> list[str]:
    notes = [
        f"[d{layer['depth']}] {layer['label']}: {layer['messages']} msg, entropy={layer['entropy']}"
    ]
    if layer.get("splitter"):
        notes.append(f"  splitter: {layer['splitter']}")
    if layer.get("opaque"):
        notes.append("  wall: opaque (high entropy)")
    if layer.get("decrypt"):
        d = layer["decrypt"]
        if d.get("status") == "ok":
            notes.append(f"  decrypt: TLS {d.get('tls_version')} → {d.get('decrypted')} plaintext")
        elif d.get("status") in ("no_match", "no_overlap", "decrypt_failed", "no_appdata_records"):
            diag = d.get("diag") or {}
            notes.append(
                f"  decrypt: {d.get('status')} "
                f"(hellos={diag.get('client_hellos_in_pcap', '?')} "
                f"overlap={diag.get('overlap', '?')} "
                f"appdata={diag.get('appdata_records', '?')})"
            )
        elif d.get("status") == "error":
            notes.append(f"  decrypt: error ({d.get('error', '?')})")
    if layer.get("sequitur_rules"):
        notes.append(f"  sequitur: ~{layer['sequitur_rules']} digrams")
    deep = layer.get("deep") or {}
    if deep.get("kind") == "http1":
        notes.append(f"  HTTP/1: {deep.get('methods', {})}")
        if deep.get("hosts"):
            notes.append(f"  host: {', '.join(deep['hosts'][:4])}")
        for r in (deep.get("requests") or [])[:4]:
            bits = [r.get("method", "?"), r.get("path", "")]
            if r.get("host"):
                bits.append(f"host={r['host']}")
            if r.get("content-type"):
                bits.append(f"ct={r['content-type']}")
            notes.append("  req: " + " ".join(str(x) for x in bits if x))
        if deep.get("statuses"):
            notes.append(f"  status: {deep['statuses'][:6]}")
        for m in (deep.get("body_meta") or [])[:3]:
            notes.append(
                f"  meta: {m.get('decompress')} {m.get('raw_len')}→{m.get('plain_len')}"
                + (f" ct={m.get('content_type')}" if m.get("content_type") else "")
            )
        for prev in (deep.get("preview") or [])[:2]:
            notes.append(f"  body: {prev[:100]}")
        content = deep.get("content") or {}
        if content.get("types"):
            notes.append(f"  content: types={content.get('types')}")
        binary = deep.get("binary") or {}
        if binary.get("kind"):
            notes.append(
                f"  binary: {binary.get('kind')} fields={binary.get('field_count', binary.get('key_count', '?'))}"
            )
    if deep.get("kind") == "http2":
        notes.append(f"  HTTP/2: {deep.get('frames', {})} streams={deep.get('streams', 0)}")
        for h in (deep.get("headers") or [])[:3]:
            bits = [f"s{h.get('stream')}"]
            for k in (":method", ":status", ":path", ":authority", "content-type", "content-encoding"):
                if k in h:
                    bits.append(f"{k}={h[k]}")
            notes.append("  hdr: " + " ".join(bits))
        if deep.get("data_preview"):
            notes.append(f"  DATA: {deep['data_preview'][0][:80]}")
    if deep.get("kind") == "http2_data":
        notes.append(
            f"  http2_data: {deep.get('payloads', 0)} payloads "
            f"(html={deep.get('html', 0)} json={deep.get('json', 0)})"
        )
        for h in (deep.get("headers") or [])[:3]:
            bits = [f"s{h.get('stream')}"]
            for k in (":method", ":status", ":path", ":authority", "content-type", "content-encoding"):
                if k in h:
                    bits.append(f"{k}={h[k]}")
            notes.append("  hdr: " + " ".join(bits))
        for m in (deep.get("body_meta") or [])[:3]:
            notes.append(
                f"  meta: stream={m.get('stream')} "
                f"{m.get('decompress')} {m.get('raw_len')}→{m.get('plain_len')}"
            )
        for prev in (deep.get("preview") or [])[:2]:
            notes.append(f"  body: {prev[:100]}")
        content = deep.get("content") or {}
        if content.get("types"):
            notes.append(f"  content: types={content.get('types')}")
            for t in (content.get("titles") or [])[:2]:
                notes.append(f"  title: {t}")
            if content.get("json_keys"):
                notes.append(f"  json_keys: {', '.join(content['json_keys'][:10])}")
    if deep.get("kind") == "body":
        notes.append(f"  content: types={deep.get('types', {})}")
        for t in (deep.get("titles") or [])[:2]:
            notes.append(f"  title: {t}")
        if deep.get("json_keys"):
            notes.append(f"  json_keys: {', '.join(deep['json_keys'][:10])}")
    if deep.get("kind") == "json_api" or deep.get("json_api"):
        api = deep if deep.get("kind") == "json_api" else (deep.get("json_api") or {})
        notes.append(
            f"  json_api: {api.get('bodies', 0)} bodies, "
            f"{api.get('field_count', 0)} fields"
        )
        if api.get("paths"):
            notes.append(f"  api_paths: {', '.join(api['paths'][:6])}")
        if api.get("sample_keys"):
            notes.append(f"  schema: {', '.join(api['sample_keys'][:10])}")
    if deep.get("kind") == "protobuf":
        notes.append(
            f"  protobuf: {deep.get('field_count', 0)} fields "
            f"cov={deep.get('avg_coverage', 0)}"
        )
        for f in (deep.get("schema") or [])[:8]:
            notes.append(f"  pb_f{f.get('field')}: {f.get('wire')} ×{f.get('seen')}")
    if deep.get("kind") == "msgpack":
        notes.append(
            f"  msgpack: parsed={deep.get('parsed', 0)} keys={deep.get('key_count', 0)}"
        )
        if deep.get("keys"):
            notes.append(f"  mp_keys: {', '.join(deep['keys'][:10])}")
    if deep.get("kind") == "tls":
        if deep.get("sni_hosts"):
            notes.append(f"  SNI: {', '.join(deep['sni_hosts'][:6])}")
        if deep.get("alpn"):
            notes.append(f"  ALPN: {', '.join(deep['alpn'][:4])}")
    if deep.get("kind") == "tls_handshake":
        if deep.get("types"):
            notes.append(f"  handshake: {deep['types']}")
        if deep.get("sni_hosts"):
            notes.append(f"  SNI: {', '.join(deep['sni_hosts'][:6])}")
        if deep.get("alpn"):
            notes.append(f"  ALPN: {', '.join(deep['alpn'][:4])}")
    if deep.get("kind") == "dns" and deep.get("domains"):
        notes.append(f"  DNS: {', '.join(deep['domains'][:6])}")
    if deep.get("kind") == "quic":
        notes.append(f"  QUIC: {deep.get('types', {})}")
    if layer.get("clusters"):
        notes.append(f"  clusters: {layer['clusters']} opcodes")
    for ch in layer.get("children", []):
        notes.extend(format_nested_notes(ch))
    return notes


def _protocol_hint(flow: str) -> str | None:
    u = flow.upper()
    if u.endswith(":53"):
        return "dns"
    if u.endswith(":123"):
        return "ntp"
    if u.startswith("TCP") and u.endswith(":443"):
        return "tls"
    if u.startswith("UDP") and u.endswith(":443"):
        return "quic"
    return None


_DNS_CANONICAL = [
    {"name": "transaction_id", "offset": 0, "size": 2, "kind": "fixed", "display": "DNS transaction ID"},
    {"name": "flags", "offset": 2, "size": 2, "kind": "enum", "display": "DNS flags (QR, opcode, RD, ...)"},
    {"name": "qdcount", "offset": 4, "size": 2, "kind": "fixed", "display": "Question count"},
    {"name": "ancount", "offset": 6, "size": 2, "kind": "fixed", "display": "Answer count"},
    {"name": "nscount", "offset": 8, "size": 2, "kind": "fixed", "display": "Authority count"},
    {"name": "arcount", "offset": 10, "size": 2, "kind": "fixed", "display": "Additional count"},
    {"name": "question_data", "offset": 12, "size": -1, "kind": "payload", "display": "Question / record data"},
]
_TLS_CANONICAL = [
    {"name": "content_type", "offset": 0, "size": 1, "kind": "enum", "display": "TLS content type"},
    {"name": "version", "offset": 1, "size": 2, "kind": "fixed", "display": "TLS version (e.g. 0x0303 = TLS 1.2)"},
    {"name": "length", "offset": 3, "size": 2, "kind": "length", "display": "Fragment length"},
    {"name": "fragment", "offset": 5, "size": -1, "kind": "payload", "display": "TLS fragment / handshake body"},
]
_NTP_CANONICAL = [
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


def _canonical_fields(flow: str) -> list[dict] | None:
    proto = _protocol_hint(flow)
    if proto == "dns":
        return [dict(f) for f in _DNS_CANONICAL]
    if proto == "tls":
        return [dict(f) for f in _TLS_CANONICAL]
    if proto == "ntp":
        return [dict(f) for f in _NTP_CANONICAL]
    return None


def _enrich_field(flow: str, field: dict, index: int) -> dict:
    out = dict(field)
    if out.get("display"):
        return out
    proto = _protocol_hint(flow)
    off = field.get("offset", index)
    kind = field.get("kind", "")
    if kind == "payload":
        out["display"] = {
            "dns": "Question / record data",
            "tls": "TLS fragment",
            "ntp": "NTP body",
            "quic": "QUIC payload",
        }.get(proto or "", out.get("name", "payload"))
        return out
    out["display"] = out.get("name", f"field_{index}")
    return out


def _enrich_format(flow: str, fmt: dict) -> dict:
    if not fmt:
        return fmt
    canonical = _canonical_fields(flow)
    if canonical:
        out = dict(fmt)
        out["fields"] = [dict(f) for f in canonical]
        out["endian"] = "be"
        out["canonical"] = True
        return out
    out = dict(fmt)
    out["fields"] = [_enrich_field(flow, f, i) for i, f in enumerate(fmt.get("fields", []))]
    return out


def _hex_preview(data: bytes, limit: int = 16) -> str:
    s = data[:limit].hex()
    return s + (f"… (+{len(data) - limit})" if len(data) > limit else "")


def _dissect_dns_tree(data: bytes) -> list[str]:
    p = parse_dns_packet(data)
    if not p or len(data) < 12:
        return [f"  raw: {_hex_preview(data)}"]
    qid, flags, qd, an, ns, ar = struct.unpack(">HHHHHH", data[:12])
    lines = [
        f"DNS ({len(data)} bytes)",
        f"  ├─ transaction_id: 0x{qid:04x}",
        f"  ├─ flags: 0x{flags:04x} ({'response' if flags & 0x8000 else 'query'})",
        f"  ├─ qdcount: {qd}",
        f"  ├─ ancount: {an}",
        f"  ├─ nscount: {ns}",
        f"  ├─ arcount: {ar}",
    ]
    for i, q in enumerate(p.get("questions", [])):
        lines.append(f"  ├─ Question #{i + 1}: {q.get('name', '?')} type={q.get('qtype')}")
    return lines


def _dissect_tls_tree(data: bytes) -> list[str]:
    if len(data) < 5 or data[0] not in range(20, 26) or data[1] != 3:
        return [f"  raw: {_hex_preview(data)}"]
    ln = (data[3] << 8) | data[4]
    ctype = {22: "Handshake", 23: "ApplicationData", 21: "Alert"}.get(data[0], str(data[0]))
    lines = [
        f"TLS Record ({len(data)} bytes)",
        f"  ├─ content_type: {ctype} ({data[0]})",
        f"  ├─ version: {data[1]}.{data[2]}",
        f"  ├─ length: {ln}",
    ]
    body = data[5 : 5 + ln]
    if data[0] == 0x16 and len(body) >= 4:
        htype = body[0]
        hname = TLS_HANDSHAKE_NAMES.get(htype, f"type{htype}")
        lines.append(f"  ├─ handshake: {hname}")
        if htype == 1:
            detail = _parse_client_hello(body) or {}
            if detail.get("sni"):
                lines.append(f"  ├─ SNI: {', '.join(detail['sni'][:6])}")
            if detail.get("alpn"):
                lines.append(f"  ├─ ALPN: {', '.join(detail['alpn'][:6])}")
    return lines


def _dissect_quic_tree(data: bytes) -> list[str]:
    p = parse_quic_packet(data, permit_short=True)
    if not p:
        return [f"  raw: {_hex_preview(data)}"]
    if p.get("form") == "short":
        return [f"QUIC short ({len(data)} bytes)", f"  ├─ pn_len: {p.get('pn_len')}"]
    return [
        f"QUIC long ({len(data)} bytes)",
        f"  ├─ type: {p.get('type')}",
        f"  ├─ version: {p.get('version_name')}",
        f"  ├─ dcid_len: {p.get('dcid_len')}",
        f"  ├─ scid_len: {p.get('scid_len')}",
    ]


def _dissect_packet_text(flow: str, data: bytes, index: int, fmt: dict | None = None) -> str:
    proto = _protocol_hint(flow)
    if proto == "dns":
        body = _dissect_dns_tree(data)
    elif proto == "tls":
        body = _dissect_tls_tree(data)
    elif proto == "quic":
        body = _dissect_quic_tree(data)
    else:
        body = [f"{flow} ({len(data)} bytes)"]
        off = 0
        for i, f in enumerate(_enrich_format(flow, fmt or {}).get("fields", [])[:32]):
            label = f.get("display") or f.get("name", "field")
            if f.get("kind") == "payload":
                body.append(f"  ├─ {label}: {_hex_preview(data[off:])}")
                break
            if off < len(data):
                body.append(f"  ├─ {label}: 0x{data[off]:02x}")
                off += 1
    return f"=== Packet #{index} ===\n" + "\n".join(body)


def _packets_for_dissect(flow: str, payloads: list[bytes], reasm: bool) -> list[bytes]:
    if reasm and flow.upper().startswith("TCP"):
        records: list[bytes] = []
        for chunk in payloads:
            records.extend(_iter_tls_stream(chunk))
        return records or payloads
    return payloads


def _export_dissect_html(flow: str, payloads: list[bytes], limit: int, reasm: bool) -> str:
    packets = _packets_for_dissect(flow, payloads, reasm)
    parts = []
    for i, pkt in enumerate(packets[:limit]):
        text = html_escape(_dissect_packet_text(flow, pkt, i))
        parts.append(f"<h3>Packet #{i}</h3><pre>{text}</pre>")
    return (
        "<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width'>"
        f"<title>Dissect {flow}</title><style>body{{background:#111;color:#ddd;font-family:monospace;padding:12px}}"
        "pre{white-space:pre-wrap}</style></head><body>"
        f"<h1>Dissect {html_escape(flow)}</h1>"
        + "".join(parts)
        + "</body></html>"
    )


def html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_to_kaitai(fmt: dict, meta_id: str = "discovered", flow: str = "") -> str:
    if flow:
        fmt = _enrich_format(flow, fmt)
    endian = fmt.get("endian") or fmt.get("length_endian") or "le"
    ks = "be" if endian == "be" else "le"
    all_fields = fmt.get("fields", [])
    fields = all_fields[:MAX_EXPORT_FIELDS]
    truncated = len(all_fields) > MAX_EXPORT_FIELDS
    lines = [f"meta:", f"  id: {meta_id}", f"  endian: {ks}"]
    if truncated:
        lines.append(f"  doc: truncated from {len(all_fields)} fields to {MAX_EXPORT_FIELDS}")
    lines += ["seq:", "  - id: message", "    type: message_body", "types:", "  message_body:", "    seq:"]
    for f in fields:
        name = f.get("name", "field").replace("@", "_")
        kind = f.get("kind", "")
        if kind == "payload":
            lines += ["      - id: payload", "        size-eos: true"]
        elif kind == "length":
            lines += [f"      - id: {name}", "        type: u2", "      - id: body", f"        size: {name}"]
        elif kind == "fixed":
            sz = f.get("size", 1)
            lines += [f"      - id: {name}", f"        size: {sz}" if sz > 1 else f"        type: u1"]
        else:
            lines += [f"      - id: {name}", "        type: u1"]
    return "\n".join(lines) + "\n"


def _sanitize_lua(name: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name)


def format_to_lua(fmt: dict, *, flow: str) -> str:
    fmt = _enrich_format(flow, fmt)
    fields = fmt.get("fields", [])[:MAX_EXPORT_FIELDS]
    truncated = len(fmt.get("fields", [])) > MAX_EXPORT_FIELDS
    endian = fmt.get("endian") or fmt.get("length_endian") or "be"
    enc = "big" if endian == "be" else "little"
    safe_flow = _sanitize_lua(flow.replace(":", "_"))
    pname = f"discovered_{safe_flow.lower()}"
    plabel = flow.replace("_", " ")
    lines = [
        f"-- Auto-generated dissector for flow {flow}",
        f"-- Endian: {endian}" + (" (truncated)" if truncated else ""),
        f'local proto = Proto("{pname}", "Discovered {plabel}")',
        "",
    ]
    field_vars: list[tuple[str, str, str, dict]] = []
    for i, f in enumerate(fields):
        kind = f.get("kind", "")
        name = _sanitize_lua(f.get("name", f"field_{i}"))
        label = f.get("display") or name
        var = f"f_{name}"
        field_vars.append((var, name, label, kind, f))
        if kind == "length":
            lines.append(
                f'local {var} = ProtoField.uint16("{pname}.{name}", "{label}", base.DEC, nil, base.{enc.upper()})'
            )
        elif kind == "payload":
            lines.append(f'local {var} = ProtoField.bytes("{pname}.{name}", "{label}")')
        elif f.get("size") == 2:
            lines.append(
                f'local {var} = ProtoField.uint16("{pname}.{name}", "{label}", base.HEX, nil, base.{enc.upper()})'
            )
        elif f.get("size", 1) > 2:
            lines.append(f'local {var} = ProtoField.bytes("{pname}.{name}", "{label}")')
        else:
            lines.append(f'local {var} = ProtoField.uint8("{pname}.{name}", "{label}", base.HEX)')
    lines.append(f"proto.fields = {{{', '.join(v[0] for v in field_vars)}}}")
    lines.append("")
    lines.append("function proto.dissector(buffer, pinfo, tree)")
    lines.append(f'    pinfo.cols.protocol = "{plabel}"')
    lines.append('    local subtree = tree:add(proto, buffer(), "Discovered message")')
    lines.append("    local offset = 0")
    lines.append("    local len_field = nil")
    for var, _name, _label, kind, f in field_vars:
        size = f.get("size", 1)
        if kind == "length":
            lines += [
                f"    len_field = buffer(offset, 2):uint{enc}()",
                f"    subtree:add({var}, buffer(offset, 2))",
                "    offset = offset + 2",
            ]
        elif kind == "payload":
            lines += [
                "    if len_field then",
                f"        subtree:add({var}, buffer(offset, len_field))",
                "    else",
                f"        subtree:add({var}, buffer(offset))",
                "    end",
            ]
        elif size and size > 1:
            lines += [f"    subtree:add({var}, buffer(offset, {size}))", f"    offset = offset + {size}"]
        else:
            lines += [
                "    if offset < buffer:len() then",
                f"        subtree:add({var}, buffer(offset, 1))",
                "        offset = offset + 1",
                "    end",
            ]
    lines.append("end")
    lines.append("")
    upper = flow.upper()
    if upper.startswith("TCP:"):
        lines.append(f'DissectorTable.get("tcp.port"):add({int(flow.split(":")[-1])}, proto)')
    elif upper.startswith("UDP:"):
        lines.append(f'DissectorTable.get("udp.port"):add({int(flow.split(":")[-1])}, proto)')
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="PCAP analyzer for Termux/Android")
    parser.add_argument("--version", action="version", version=f"analyze_pcap {VERSION}")
    parser.add_argument(
        "pcap",
        nargs="*",
        help="path(s) to .pcap — glob OK; newest file is used when several match",
    )
    parser.add_argument(
        "--self-update",
        action="store_true",
        help="download latest analyze_pcap + protocol_ast into $HOME (no apt)",
    )
    parser.add_argument("--blind", action="store_true", help="blind deep analysis (TLS/QUIC inner frames)")
    parser.add_argument("--nested", action="store_true", help="nested AST v2 (recursive layers)")
    parser.add_argument("--signal", action="store_true", help="living signal propagate (depth 5, universal splitters)")
    parser.add_argument(
        "--mine",
        action="store_true",
        help="deep game mine: per-SNI economy, multi-conn decrypt, protobuf strings",
    )
    parser.add_argument("--stream", action="store_true", help="incremental living-signal events over pcap")
    parser.add_argument(
        "--every",
        type=int,
        default=32,
        help="with --stream: checkpoint spacing (default 32; phone-safe)",
    )
    parser.add_argument(
        "--keylog",
        metavar="FILE|auto",
        help="SSLKEYLOGFILE or 'auto' (search Downloads / extract pcapng DSB)",
    )
    parser.add_argument("--tcp-reassemble", action="store_true", help="TCP stream reassembly + TLS split")
    parser.add_argument("--export-kaitai", metavar="DIR", help="export .ksy schemas per flow")
    parser.add_argument("--export-lua", metavar="DIR", help="export Wireshark Lua dissectors per flow")
    parser.add_argument("--dissect", action="store_true", help="packet tree in terminal (Wireshark-like)")
    parser.add_argument("--dissect-html", metavar="FILE", help="HTML report for phone browser")
    parser.add_argument("--limit", type=int, default=5, help="packets to show with --dissect")
    parser.add_argument("--flow", help="filter flow, e.g. 443 or TCP:443")
    args = parser.parse_args()

    if args.self_update:
        # Always refresh termux_update.py from tip FIRST, then exec that copy.
        # Otherwise an old on-device helper can skip new launchers (e.g. ~/signal).
        import importlib.util
        import ssl
        import time
        import urllib.request

        def _get(url: str) -> bytes:
            req = urllib.request.Request(url, headers={"User-Agent": "analyze_pcap-self-update"})
            with urllib.request.urlopen(req, timeout=60, context=ssl.create_default_context()) as r:
                return r.read()

        branch = "cursor/signal-pipeline-p4-a4e6"
        home = Path.home()
        (home / "protocol_ast").mkdir(parents=True, exist_ok=True)
        try:
            sha = json.loads(
                _get(f"https://api.github.com/repos/lizbeth307/lizbeth307/commits/{branch}").decode()
            )["sha"]
            base = f"https://cdn.jsdelivr.net/gh/lizbeth307/lizbeth307@{sha}"
        except Exception:
            base = f"https://raw.githubusercontent.com/lizbeth307/lizbeth307/{branch}"
            sha = f"raw-{int(time.time())}"

        helper_rel = "protocol_ast/termux_update.py"
        helper_url = f"{base}/{helper_rel}" if "jsdelivr" in base else f"{base}/{helper_rel}?t={int(time.time())}"
        try:
            helper_bytes = _get(helper_url)
            helper_path = home / helper_rel
            tmp = Path(str(helper_path) + ".new")
            tmp.write_bytes(helper_bytes)
            tmp.replace(helper_path)
            print(f"self-update: refreshed {helper_path} from {sha}", flush=True)
        except Exception as exc:
            print(f"self-update: warn — could not refresh termux_update.py: {exc}", file=sys.stderr)

        download_tree = None
        for fk in (
            home / "protocol_ast" / "termux_update.py",
            Path(__file__).resolve().parent / "protocol_ast" / "termux_update.py",
        ):
            if not fk.exists():
                continue
            spec = importlib.util.spec_from_file_location("termux_update_fresh", fk)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                download_tree = getattr(mod, "download_tree", None)
                if download_tree is not None:
                    break
        if download_tree is None:
            print("self-update: FATAL — protocol_ast/termux_update.py missing", file=sys.stderr)
            return 1

        report = download_tree(home)
        print(f"self-update: ref={report.get('ref')}")
        print(f"  base={report.get('base')}")
        print(f"  files={len(report.get('files') or [])}")
        for err in report.get("errors") or []:
            print(f"  ⚠ {err}", file=sys.stderr)
        launcher = Path(report["launcher"]) if report.get("launcher") else home / "signal"
        if launcher.is_file() and os.access(launcher, os.X_OK):
            print(f"  launcher={launcher}")
        else:
            print(f"  ⚠ launcher missing or not executable: {launcher}", file=sys.stderr)
            # Last-resort: write a tiny inline ~/signal so the next command works.
            try:
                inline = (
                    "#!/data/data/com.termux/files/usr/bin/bash\n"
                    "set -euo pipefail\n"
                    'export PYTHONPATH="${HOME}${PYTHONPATH:+:$PYTHONPATH}"\n'
                    'FLOW="${FLOW:-TCP:443}"\n'
                    'exec python3 "$HOME/analyze_pcap.py" --signal --flow "$FLOW" --keylog auto "$@"\n'
                )
                launcher.write_text(inline, encoding="utf-8")
                launcher.chmod(0o755)
                print(f"  launcher={launcher} (inline fallback)")
            except Exception as exc:
                print(f"  ⚠ could not write ~/signal: {exc}", file=sys.stderr)
        fresh = home / "analyze_pcap.py"
        if fresh.exists():
            for line in fresh.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("VERSION"):
                    ver = line.split("=", 1)[-1].strip().strip("\"'")
                    print(f"analyze_pcap {ver}")
                    break
        return 1 if report.get("errors") and not report.get("files") else 0
    if args.dissect or args.dissect_html:
        mode = "dissect"
    elif args.mine:
        mode = "game mine"
    elif args.stream:
        mode = "stream agent"
    elif args.signal:
        mode = "signal propagate"
        args.nested = True
        if not args.tcp_reassemble:
            args.tcp_reassemble = True
    elif args.nested:
        mode = "nested AST v2"
    elif args.tcp_reassemble:
        mode = "TCP reassembly"
    else:
        mode = "deep decode embedded"
    print(f"analyze_pcap: старт v{VERSION} ({mode})", flush=True)

    # Explicit single file vs auto/glob
    explicit_single = (
        len(args.pcap) == 1
        and Path(args.pcap[0]).expanduser().is_file()
    )

    resolve_keylog = None
    pick_pcap_for_keylog = None
    pick_newest_pcap = None
    try:
        from protocol_ast.find_keylog import pick_pcap_for_keylog as _ppk
        from protocol_ast.find_keylog import resolve_keylog as _rk
        from protocol_ast.termux_update import pick_newest_pcap as _pnp

        resolve_keylog = _rk
        pick_pcap_for_keylog = _ppk
        pick_newest_pcap = _pnp
    except Exception as exc:
        try:
            import importlib.util

            fk = Path.home() / "protocol_ast" / "find_keylog.py"
            if not fk.exists():
                fk = Path(__file__).resolve().parent / "protocol_ast" / "find_keylog.py"
            spec = importlib.util.spec_from_file_location("find_keylog_standalone", fk)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                resolve_keylog = mod.resolve_keylog
                pick_pcap_for_keylog = getattr(mod, "pick_pcap_for_keylog", None)
        except Exception as exc2:
            print(f"⚠  keylog helper: {exc} / {exc2}", file=sys.stderr)
        try:
            from protocol_ast.termux_update import pick_newest_pcap as _pnp

            pick_newest_pcap = _pnp
        except Exception:
            pass

    # Resolve keylog first (auto → newest), then pair a matching pcap
    kpath: Path | None = None
    if args.keylog:
        if resolve_keylog is not None:
            # provisional: allow search without pcap
            kpath, kmsg = resolve_keylog(args.keylog, pcap_path=None)
            if kmsg and not kpath:
                print(f"⚠  {kmsg}", file=sys.stderr)
        else:
            kp = Path(args.keylog).expanduser()
            if args.keylog.lower() != "auto" and kp.exists():
                kpath = kp

    path: Path | None = None
    if explicit_single:
        path = Path(args.pcap[0]).expanduser()
        print(f"pcap: явний файл", flush=True)
    elif args.keylog and kpath and pick_pcap_for_keylog is not None and (
        not args.pcap or len(args.pcap) != 1
    ):
        path, ov, pmsg = pick_pcap_for_keylog(kpath, seed_paths=args.pcap or None)
        print(f"pcap: {pmsg}", flush=True)
        if ov == 0:
            print(
                "⚠  keylog не збігається з найновішим pcap — "
                "після Stop зберігай SSLKEYLOGFILE з тієї ж сесії",
                file=sys.stderr,
            )
    elif pick_newest_pcap is not None:
        path = pick_newest_pcap(args.pcap or None, also_search_defaults=True)
        print("pcap: найновіший у PCAPdroid/Downloads", flush=True)
    else:
        cands = [Path(p).expanduser() for p in (args.pcap or []) if Path(p).expanduser().is_file()]
        path = max(cands, key=lambda p: p.stat().st_mtime) if cands else None

    if path is None:
        if not args.pcap:
            parser.print_help()
        else:
            print(f"Файл не знайдено: {args.pcap}", file=sys.stderr)
        print("Шукай: ~/storage/downloads/PCAPdroid/*.pcap", file=sys.stderr)
        return 1
    print(f"PCAP: {path} ({path.stat().st_size} bytes)\n")

    if args.keylog:
        if resolve_keylog is not None:
            # re-resolve beside chosen pcap (may refine message)
            kpath2, kmsg = resolve_keylog(args.keylog, pcap_path=path)
            if kpath2:
                kpath = kpath2
            if kmsg:
                print(kmsg if kpath else f"⚠  {kmsg}", file=sys.stderr if not kpath else sys.stdout)
        if kpath:
            print(f"Keylog: {kpath} ({kpath.stat().st_size} bytes)\n")
            args.keylog = str(kpath)
        else:
            print("   Decrypt пропущено. Handshake peel працює і без ключів.", file=sys.stderr)
            print("   PCAPdroid → TLS decryption ON → Start → Chrome → Stop", file=sys.stderr)
            print("   → Save SSLKEYLOGFILE у Download з ТІЄЇ Ж сесії\n", file=sys.stderr)
            args.keylog = None

    if args.mine:
        try:
            from protocol_ast.game_mine import format_mine_report, mine_pcap
        except Exception as exc:
            print(f"game mine: {exc}", file=sys.stderr)
            return 1
        kfile = Path(args.keylog).expanduser() if args.keylog else None
        if args.keylog and kpath:
            kfile = kpath
        report = mine_pcap(path, kfile)
        text = format_mine_report(report)
        print(text)
        out_txt = path.parent / "mine_report.txt"
        out_json = path.parent / "mine_report.json"
        out_sdk = path.parent / "sdk_session.json"
        # sessions already slim; drop any accidental bytes
        slim = json.loads(json.dumps(report, default=str))
        out_txt.write_text(text, encoding="utf-8")
        out_json.write_text(json.dumps(slim, indent=2, ensure_ascii=False), encoding="utf-8")
        out_sdk.write_text(
            json.dumps(slim.get("sdk_session") or {}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nЗвіт: {out_txt}")
        print(f"JSON: {out_json}")
        print(f"SDK:  {out_sdk}")
        return 0

    if args.stream:
        try:
            from protocol_ast.stream_agent import analyze_pcap_streaming, write_stream_report
        except Exception as exc:
            print(f"stream agent: {exc}", file=sys.stderr)
            return 1
        if not args.flow:
            print(
                "stream: без --flow беру топ TLS/HTTP потоки (додай --flow TCP:443 щоб звузити)",
                flush=True,
            )
        events = analyze_pcap_streaming(
            path,
            every_n=args.every,
            keylog=args.keylog,
            flow_filter=args.flow,
            max_flows=3,
            max_msgs=64,
            max_emits_per_flow=3,
        )
        for ev in events:
            print(f"── {ev.flow} msgs={ev.messages}")
            print(f"   path: {ev.path}")
            for n in ev.notes:
                print(f"   {n}" if n.startswith("[") or n.startswith("  ") else f"   • {n}")
            print()
        out = path.parent / "stream_report.json"
        write_stream_report(events, out)
        print(f"Звіт: {out}  events={len(events)}")
        return 0 if events else 1

    reasm = args.tcp_reassemble or args.nested or args.signal
    flows = extract_flows(path, tcp_reassemble=reasm)
    if not flows:
        print("Потоків не знайдено. Спробуйте інший pcap.")
        return 1

    selected = flows
    if args.flow:
        selected = {k: v for k, v in flows.items() if _flow_matches(k, args.flow)}
        if not selected:
            print(f"Потік '{args.flow}' не знайдено. Доступні:", ", ".join(sorted(flows)))
            return 1

    if args.dissect or args.dissect_html:
        for label in sorted(selected, key=lambda k: -len(selected[k])):
            pkts = _packets_for_dissect(label, selected[label], reasm)
            if args.dissect_html:
                out = Path(args.dissect_html).expanduser()
                if len(selected) > 1:
                    out = out.with_name(f"{out.stem}_{label.replace(':', '_')}{out.suffix}")
                out.write_text(_export_dissect_html(label, selected[label], args.limit, reasm), encoding="utf-8")
                print(f"HTML: {out}")
            else:
                print(f"── {label}  ({min(args.limit, len(pkts))}/{len(pkts)} packets)\n")
                for i, pkt in enumerate(pkts[: args.limit]):
                    print(_dissect_packet_text(label, pkt, i))
                    print()
        return 0

    if args.nested:
        max_depth = 5 if args.signal else 3
        report = {"file": str(path), "nested": True, "signal": bool(args.signal), "tcp_reassemble": reasm, "flows": []}
        for label in sorted(selected, key=lambda k: -len(selected[k])):
            layer = recursive_nested_analyze(
                label, selected[label], max_depth=max_depth, keylog=args.keylog
            )
            n = layer["messages"]
            print(f"── {label}  messages={n}" + (" (TCP reasm)" if reasm and label.startswith("TCP") else ""))
            for note in format_nested_notes(layer):
                print(f"   • {note}" if not note.startswith("[") and not note.startswith("  ") else f"   {note}")
            print()
            report["flows"].append(layer)
        out = path.parent / ("signal_report.json" if args.signal else "blind_nested_report.json")
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Звіт: {out}")
        if args.export_kaitai:
            kdir = Path(args.export_kaitai).expanduser()
            kdir.mkdir(parents=True, exist_ok=True)
            for layer in report["flows"]:
                label = layer["label"].replace(":", "_")
                ksy = kdir / f"{label}.ksy"
                ksy.write_text(format_to_kaitai(layer.get("format", {}), meta_id=f"flow_{label}", flow=layer["label"]), encoding="utf-8")
            print(f"Kaitai: {kdir}/")
        if args.export_lua:
            ldir = Path(args.export_lua).expanduser()
            ldir.mkdir(parents=True, exist_ok=True)
            for layer in report["flows"]:
                label = layer["label"].replace(":", "_")
                (ldir / f"{label}.lua").write_text(
                    format_to_lua(layer.get("format", {}), flow=layer["label"]),
                    encoding="utf-8",
                )
            print(f"Wireshark Lua: {ldir}/")
        return 0

    report = {"file": str(path), "blind": args.blind, "tcp_reassemble": reasm, "flows": []}
    for label in sorted(selected, key=lambda k: -len(selected[k])):
        entry = _print_flow(label, selected[label], args.blind)
        print()
        report["flows"].append(entry)
    out = path.parent / ("blind_report.json" if args.blind else "probe_report.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Звіт: {out}")
    if args.export_kaitai and args.blind:
        kdir = Path(args.export_kaitai).expanduser()
        kdir.mkdir(parents=True, exist_ok=True)
        for entry in report["flows"]:
            label = entry.get("flow", "flow").replace(":", "_")
            fmt = entry.get("format") or entry.get("inner_format") or {}
            if fmt:
                (kdir / f"{label}.ksy").write_text(format_to_kaitai(fmt, meta_id=f"flow_{label}", flow=entry.get("flow", label)), encoding="utf-8")
        print(f"Kaitai: {kdir}/")
    if args.export_lua and args.blind:
        ldir = Path(args.export_lua).expanduser()
        ldir.mkdir(parents=True, exist_ok=True)
        for entry in report["flows"]:
            label = entry.get("flow", "flow").replace(":", "_")
            fmt = entry.get("format") or entry.get("inner_format") or {}
            if fmt:
                (ldir / f"{label}.lua").write_text(format_to_lua(fmt, flow=entry.get("flow", label)), encoding="utf-8")
        print(f"Wireshark Lua: {ldir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
