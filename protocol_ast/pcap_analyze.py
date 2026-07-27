"""Extract L4 payloads from PCAP and group by flow for AST discovery."""

from __future__ import annotations

import struct
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


PCAP_MAGIC_LE = 0xA1B2C3D4
PCAP_MAGIC_BE = 0xD4C3B2A1
PCAP_NSEC_LE = 0xA1B23C4D
PCAP_NSEC_BE = 0x4D3CB2A1

ETH_P_IP = 0x0800
ETH_P_IP6 = 0x86DD
IPPROTO_TCP = 6
IPPROTO_UDP = 17
IPPROTO_HOPOPTS = 0
IPPROTO_ROUTING = 43
IPPROTO_FRAGMENT = 44
IPPROTO_AH = 51
IPPROTO_DSTOPTS = 60


COMMON_PORTS = {
    53, 67, 68, 80, 123, 443, 5353, 1883, 8883, 8080, 8443, 22, 25, 993, 995,
}


@dataclass(frozen=True)
class FlowKey:
    proto: str  # "tcp" | "udp"
    port_a: int
    port_b: int  # -1 = агрегація за сервісним портом

    @property
    def label(self) -> str:
        if self.port_b == -1:
            return f"{self.proto.upper()}:{self.port_a}"
        pa, pb = sorted((self.port_a, self.port_b))
        return f"{self.proto.upper()}:{pa}<->{pb}"


def _flow_key(proto: str, sport: int, dport: int) -> FlowKey:
    """Групує клієнтський трафік до одного сервісного порту (DNS:53, TLS:443, ...)."""
    for port in (sport, dport):
        if port in COMMON_PORTS or port < 1024:
            return FlowKey(proto=proto, port_a=port, port_b=-1)
    a, b = sorted((sport, dport))
    return FlowKey(proto=proto, port_a=a, port_b=b)


@dataclass
class FlowBucket:
    key: FlowKey
    payloads: list[bytes]
    packet_count: int = 0
    tcp_segments: list[tuple[int, int, int, bytes]] = field(default_factory=list)


def _parse_l4(proto: int, ip_payload: bytes) -> tuple[str, int, int, bytes, int | None] | None:
    if proto == IPPROTO_UDP and len(ip_payload) >= 8:
        sport, dport, ulen = struct.unpack(">HHH", ip_payload[:6])
        payload = ip_payload[8:ulen]
        return "udp", sport, dport, payload, None

    if proto == IPPROTO_TCP and len(ip_payload) >= 20:
        sport, dport, seq = struct.unpack(">HHI", ip_payload[:8])
        data_offset = ((ip_payload[12] >> 4) & 0x0F) * 4
        if len(ip_payload) < data_offset:
            return None
        payload = ip_payload[data_offset:]
        return "tcp", sport, dport, payload, seq

    return None


def _skip_ipv6_extensions(data: bytes, off: int, nxt: int) -> tuple[int, int] | None:
    while nxt in (IPPROTO_HOPOPTS, IPPROTO_ROUTING, IPPROTO_FRAGMENT, IPPROTO_DSTOPTS, IPPROTO_AH):
        if nxt == IPPROTO_FRAGMENT:
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


def _parse_ipv4_l4(data: bytes) -> tuple[str, int, int, bytes, int | None] | None:
    if len(data) < 20:
        return None
    ver_ihl = data[0]
    if ver_ihl >> 4 != 4:
        return None
    ihl = (ver_ihl & 0x0F) * 4
    if len(data) < ihl:
        return None
    proto = data[9]
    total_len = struct.unpack(">H", data[2:4])[0]
    ip_payload = data[ihl:total_len]
    return _parse_l4(proto, ip_payload)


def _parse_ipv6_l4(data: bytes) -> tuple[str, int, int, bytes, int | None] | None:
    if len(data) < 40 or (data[0] >> 4) != 6:
        return None
    payload_len = struct.unpack(">H", data[4:6])[0]
    nxt = data[6]
    off = 40
    if nxt not in (IPPROTO_TCP, IPPROTO_UDP):
        skipped = _skip_ipv6_extensions(data, off, nxt)
        if not skipped:
            return None
        off, nxt = skipped
    ip_payload = data[off : 40 + payload_len]
    return _parse_l4(nxt, ip_payload)


def _extract_l4_from_frame(frame: bytes, link_type: int) -> tuple[str, int, int, bytes, int | None] | None:
    if link_type == 0:  # NULL/loopback (BSD)
        if len(frame) < 4:
            return None
        family = struct.unpack("<I", frame[:4])[0]
        if family == 2:  # AF_INET
            return _parse_ipv4_l4(frame[4:])
        if family in (10, 30):  # AF_INET6 / AF_INET6 (BSD)
            return _parse_ipv6_l4(frame[4:])
        return None

    if link_type == 1:  # Ethernet
        if len(frame) < 14:
            return None
        eth_type = struct.unpack(">H", frame[12:14])[0]
        if eth_type == ETH_P_IP:
            return _parse_ipv4_l4(frame[14:])
        if eth_type == ETH_P_IP6:
            return _parse_ipv6_l4(frame[14:])
        if eth_type == 0x8100 and len(frame) >= 18:  # VLAN
            inner = struct.unpack(">H", frame[16:18])[0]
            if inner == ETH_P_IP:
                return _parse_ipv4_l4(frame[18:])
            if inner == ETH_P_IP6:
                return _parse_ipv6_l4(frame[18:])
        return None

    if link_type == 101:  # RAW IP
        return _parse_ipv4_l4(frame)

    if link_type == 113:  # Linux cooked capture (SLL)
        if len(frame) < 16:
            return None
        proto = struct.unpack(">H", frame[14:16])[0]
        if proto == ETH_P_IP:
            return _parse_ipv4_l4(frame[16:])
        if proto == ETH_P_IP6:
            return _parse_ipv6_l4(frame[16:])
        return None

    return None


def iter_pcap_packets(path: str | Path) -> Iterator[tuple[int, bytes]]:
    """Yield (link_type, frame_bytes) from classic PCAP or PCAPNG."""
    from .pcap_read import iter_packets

    yield from iter_packets(path)


def extract_flows(
    path: str | Path,
    *,
    min_payload: int = 4,
    min_packets: int = 3,
    tcp_reassemble: bool = False,
) -> dict[str, FlowBucket]:
    """Group non-empty L4 payloads by flow (proto + port pair)."""
    buckets: dict[FlowKey, FlowBucket] = {}

    for link_type, frame in iter_pcap_packets(path):
        parsed = _extract_l4_from_frame(frame, link_type)
        if not parsed:
            continue
        proto, sport, dport, payload, seq = parsed
        if len(payload) < min_payload:
            continue
        key = _flow_key(proto, sport, dport)
        if key not in buckets:
            buckets[key] = FlowBucket(key=key, payloads=[])
        bucket = buckets[key]
        if proto == "tcp" and tcp_reassemble and seq is not None:
            bucket.tcp_segments.append((sport, dport, seq, payload))
        else:
            bucket.payloads.append(payload)
        bucket.packet_count += 1

    if tcp_reassemble:
        from .tcp_reassemble import reassemble_tcp_payloads

        for bucket in buckets.values():
            if bucket.tcp_segments:
                bucket.payloads = reassemble_tcp_payloads(bucket.tcp_segments)

    return {
        b.key.label: b
        for b in buckets.values()
        if b.packet_count >= min_packets
    }


def flow_summary(buckets: dict[str, FlowBucket]) -> list[dict]:
    out = []
    for label, bucket in sorted(
        buckets.items(), key=lambda x: -x[1].packet_count
    ):
        lens = [len(p) for p in bucket.payloads]
        out.append(
            {
                "flow": label,
                "packets": bucket.packet_count,
                "min_len": min(lens),
                "max_len": max(lens),
                "avg_len": round(sum(lens) / len(lens), 1),
            }
        )
    return out
