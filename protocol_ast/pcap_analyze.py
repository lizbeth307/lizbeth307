"""Extract L4 payloads from PCAP and group by flow for AST discovery."""

from __future__ import annotations

import struct
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


PCAP_MAGIC_LE = 0xA1B2C3D4
PCAP_MAGIC_BE = 0xD4C3B2A1
PCAP_NSEC_LE = 0xA1B23C4D
PCAP_NSEC_BE = 0x4D3CB2A1

ETH_P_IP = 0x0800
IPPROTO_TCP = 6
IPPROTO_UDP = 17


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


def _parse_ipv4_l4(data: bytes) -> tuple[str, int, int, bytes] | None:
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

    if proto == IPPROTO_UDP and len(ip_payload) >= 8:
        sport, dport, ulen = struct.unpack(">HHH", ip_payload[:6])
        payload = ip_payload[8:ulen]
        return "udp", sport, dport, payload

    if proto == IPPROTO_TCP and len(ip_payload) >= 20:
        sport, dport = struct.unpack(">HH", ip_payload[:4])
        data_offset = ((ip_payload[12] >> 4) & 0x0F) * 4
        if len(ip_payload) < data_offset:
            return None
        payload = ip_payload[data_offset:]
        return "tcp", sport, dport, payload

    return None


def _extract_l4_from_frame(frame: bytes, link_type: int) -> tuple[str, int, int, bytes] | None:
    if link_type == 0:  # NULL/loopback (BSD)
        if len(frame) < 4:
            return None
        family = struct.unpack("<I", frame[:4])[0]
        if family == 2:  # AF_INET
            return _parse_ipv4_l4(frame[4:])
        return None

    if link_type == 1:  # Ethernet
        if len(frame) < 14:
            return None
        eth_type = struct.unpack(">H", frame[12:14])[0]
        if eth_type == ETH_P_IP:
            return _parse_ipv4_l4(frame[14:])
        if eth_type == 0x8100 and len(frame) >= 18:  # VLAN
            inner = struct.unpack(">H", frame[16:18])[0]
            if inner == ETH_P_IP:
                return _parse_ipv4_l4(frame[18:])
        return None

    if link_type == 101:  # RAW IP
        return _parse_ipv4_l4(frame)

    if link_type == 113:  # Linux cooked capture (SLL)
        if len(frame) < 16:
            return None
        proto = struct.unpack(">H", frame[14:16])[0]
        if proto == ETH_P_IP:
            return _parse_ipv4_l4(frame[16:])
        return None

    return None


def iter_pcap_packets(path: str | Path) -> Iterator[tuple[int, bytes]]:
    """Yield (link_type, frame_bytes) from classic PCAP."""
    data = Path(path).read_bytes()
    if len(data) < 24:
        raise ValueError("pcap too small")

    magic, _, _, _, _, _, link_type = struct.unpack("<IHHiIII", data[:24])
    endian = "<"
    if magic in (PCAP_MAGIC_BE, PCAP_NSEC_BE):
        endian = ">"
        magic, _, _, _, _, _, link_type = struct.unpack(">IHHiIII", data[:24])
    elif magic not in (PCAP_MAGIC_LE, PCAP_NSEC_LE):
        raise ValueError(f"unsupported pcap magic: {magic:#x}")

    offset = 24
    while offset + 16 <= len(data):
        ts_sec, ts_usec, caplen, wirelen = struct.unpack(endian + "IIII", data[offset : offset + 16])
        offset += 16
        frame = data[offset : offset + caplen]
        offset += caplen
        if len(frame) < caplen:
            break
        yield link_type, frame


def extract_flows(
    path: str | Path,
    *,
    min_payload: int = 4,
    min_packets: int = 3,
) -> dict[str, FlowBucket]:
    """Group non-empty L4 payloads by flow (proto + port pair)."""
    buckets: dict[FlowKey, FlowBucket] = {}

    for link_type, frame in iter_pcap_packets(path):
        parsed = _extract_l4_from_frame(frame, link_type)
        if not parsed:
            continue
        proto, sport, dport, payload = parsed
        if len(payload) < min_payload:
            continue
        key = _flow_key(proto, sport, dport)
        if key not in buckets:
            buckets[key] = FlowBucket(key=key, payloads=[])
        bucket = buckets[key]
        bucket.payloads.append(payload)
        bucket.packet_count += 1

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
