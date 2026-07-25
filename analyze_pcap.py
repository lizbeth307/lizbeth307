#!/usr/bin/env python3
"""
analyze_pcap.py — мінімальний аналізатор PCAP для Termux/Android.

ВАЖЛИВО (Termux): не запускайте через "python" — буде grep /proc/stat error!
  python3 analyze_pcap.py ~/downloads/файл.pcap
  bash run_pcap.sh ~/downloads/файл.pcap
"""

from __future__ import annotations

import json
import struct
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

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


def main() -> int:
    print("analyze_pcap: старт", flush=True)
    if len(sys.argv) < 2:
        print("Використання: python analyze_pcap.py ШЛЯХ.pcap", file=sys.stderr)
        return 1
    path = Path(sys.argv[1]).expanduser()
    if not path.exists():
        print(f"Файл не знайдено: {path}", file=sys.stderr)
        return 1
    print(f"PCAP: {path} ({path.stat().st_size} bytes)\n")
    flows = extract_flows(path)
    if not flows:
        print("Потоків не знайдено. Спробуйте інший pcap.")
        return 1
    report = {"file": str(path), "flows": []}
    for label in sorted(flows, key=lambda k: -len(flows[k])):
        payloads = flows[label]
        fmt = discover_format(payloads)
        print(f"── {label}  packets={len(payloads)}  len={min(map(len,payloads))}..{max(map(len,payloads))}")
        for f in fmt.get("fields", [])[:12]:
            print(f"   {f['name']:12} {f['kind']:8} @{f['offset']}")
        if fmt.get("length_offset") is not None:
            print(f"   length @{fmt['length_offset']} ({fmt['endian']})")
        sample = payloads[0][:32].hex()
        print(f"   sample: {sample}{'...' if len(payloads[0])>32 else ''}\n")
        report["flows"].append({"flow": label, "packets": len(payloads), "format": fmt})
    out = path.parent / "probe_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Звіт: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
