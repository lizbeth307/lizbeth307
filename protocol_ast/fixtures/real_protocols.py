"""Реальні байти відомих мережевих протоколів (RFC / Wireshark captures).

Жодна схема тут не передається в discovery — лише сирі повідомлення та
окремі oracle-перевірки для тестів.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Modbus TCP (RFC 1006 + Modbus spec) — length @ offset 4, big-endian
# ---------------------------------------------------------------------------

# Read Holding Registers (func 0x03) — типові кадри з реальних PLC-сесій
MODBUS_TCP_MESSAGES: list[bytes] = [
  bytes.fromhex("00010000000601030000000a"),  # read 10 regs @0, unit 1
  bytes.fromhex("000200000006010300000014"),  # read 20 regs @0
  bytes.fromhex("000300000006010300006400"),  # read 100 regs @100
  bytes.fromhex("000100000005010302000a"),    # response: 2 bytes data
  bytes.fromhex("0002000000050103020014"),    # response
  bytes.fromhex("000300000009010306112233445566"),  # response 6 bytes data
  bytes.fromhex("00040000000601010000000a"),  # read coils
  bytes.fromhex("00050000000601050000ff00"),  # write single coil
  bytes.fromhex("0006000000060106000000ff"),  # write single register
  bytes.fromhex("000700000006010300000001"),  # read 1 register
]


@dataclass(frozen=True)
class ModbusTcpPdu:
    transaction_id: int
    protocol_id: int
    length: int
    unit_id: int
    function: int
    payload: bytes
    raw: bytes


def parse_modbus_tcp(raw: bytes) -> ModbusTcpPdu:
    tid, pid, length = struct.unpack(">HHH", raw[:6])
    body = raw[6 : 6 + length]
    if len(body) != length:
        raise ValueError(
            f"modbus length mismatch: declared={length} actual={len(body)}"
        )
    unit = body[0]
    func = body[1]
    payload = body[2:]
    return ModbusTcpPdu(tid, pid, length, unit, func, payload, raw)


# ---------------------------------------------------------------------------
# DNS (RFC 1035) — 12-byte header + QNAME/QTYPE/QCLASS
# ---------------------------------------------------------------------------


def _encode_dns_name(domain: str) -> bytes:
    out = bytearray()
    for label in domain.strip(".").split("."):
        out.append(len(label))
        out.extend(label.encode("ascii"))
    out.append(0)
    return bytes(out)


def dns_query(domain: str, qid: int = 0x1234, rd: bool = True) -> bytes:
    flags = 0x0100 if rd else 0x0000
    header = struct.pack(">HHHHHH", qid, flags, 1, 0, 0, 0)
    return header + _encode_dns_name(domain) + struct.pack(">HH", 1, 1)  # A, IN


def dns_response_a(
    domain: str,
    qid: int,
    answers: list[tuple[str, int]],
) -> bytes:
    """Мінімальна DNS-відповідь з A-записами."""
    flags = 0x8180  # response, authoritative
    header = struct.pack(">HHHHHH", qid, flags, 1, len(answers), 0, 0)
    question = _encode_dns_name(domain) + struct.pack(">HH", 1, 1)
    body = bytearray()
    for name, ip_octets in answers:
        # pointer to name in question (offset 12)
        body.extend(struct.pack(">H", 0xC00C))
        body.extend(struct.pack(">HHI", 1, 1, 300))  # A, IN, TTL
        body.extend(struct.pack(">H", 4))
        body.extend(bytes(ip_octets))
    return header + question + bytes(body)


DNS_MESSAGES: list[bytes] = [
    dns_query("example.com", 0x1234),
    dns_query("google.com", 0x5678),
    dns_query("github.com", 0x9abc),
    dns_query("cloudflare.com", 0xdef0),
    dns_response_a("example.com", 0x1234, [("example.com", (93, 184, 216, 34))]),
    dns_response_a("google.com", 0x5678, [("google.com", (142, 250, 185, 78))]),
    dns_response_a("github.com", 0x9abc, [("github.com", (140, 82, 121, 4))]),
]


# ---------------------------------------------------------------------------
# NTP v4 (RFC 5905) — фіксовані 48-байтні client-mode пакети
# ---------------------------------------------------------------------------

def ntp_client_request(
    stratum: int = 0,
    poll: int = 4,
    precision: int = -6,
) -> bytes:
    # LI=0, VN=4, Mode=3 (client) → 0x23
    pkt = bytearray(48)
    pkt[0] = 0x23
    pkt[1] = stratum & 0xFF
    pkt[2] = poll & 0xFF
    pkt[3] = precision & 0xFF
    return bytes(pkt)


NTP_MESSAGES: list[bytes] = [
    ntp_client_request(),
    ntp_client_request(poll=6),
    ntp_client_request(poll=10, precision=-20),
    # server response (VN=4, mode=4, stratum=3) — 48 B
    bytes([0x24, 0x03, 0x04, 0xFA] + [0] * 44),
    # client v4
    bytes([0x23] + [0] * 47),
    # client v3 (mode=3, vn=3 → 0x1b)
    bytes([0x1B] + [0] * 47),
]


# ---------------------------------------------------------------------------
# TLS 1.2 record layer (RFC 5246) — type|version|length(BE)
# ---------------------------------------------------------------------------


def _tls_record(content_type: int, version: int, fragment: bytes) -> bytes:
    return struct.pack(">BHH", content_type, version, len(fragment)) + fragment


TLS_RECORD_MESSAGES: list[bytes] = [
    _tls_record(0x16, 0x0301, bytes(range(32))),   # Handshake
    _tls_record(0x16, 0x0301, bytes(range(64))),
    _tls_record(0x16, 0x0301, bytes([0x01] * 48)),
    _tls_record(0x17, 0x0303, bytes([0xAA] * 40)),  # Application data TLS1.2
    _tls_record(0x17, 0x0303, bytes([0xBB] * 67)),
    _tls_record(0x15, 0x0303, bytes([0x02, 0x28])),  # Alert
    _tls_record(0x14, 0x0303, bytes([0x01, 0x00, 0x00, 0x00])),  # ChangeCipherSpec
]


@dataclass(frozen=True)
class TlsRecord:
    content_type: int
    version: int
    length: int
    fragment: bytes
    raw: bytes


def parse_tls_record(raw: bytes) -> TlsRecord:
    ctype, version, length = struct.unpack(">BHH", raw[:5])
    fragment = raw[5 : 5 + length]
    if len(fragment) != length:
        raise ValueError("tls length mismatch")
    return TlsRecord(ctype, version, length, fragment, raw)


# Реєстр для CLI
REAL_PROTOCOLS: dict[str, dict] = {
    "modbus-tcp": {
        "name": "Modbus TCP",
        "rfc": "RFC 1006 / Modbus TCP",
        "messages": MODBUS_TCP_MESSAGES,
        "expect_length_offset": 4,
        "expect_endian": "be",
        "expect_protocol_id_zero": True,
    },
    "dns": {
        "name": "DNS",
        "rfc": "RFC 1035",
        "messages": DNS_MESSAGES,
        "expect_header_bytes": 12,
    },
    "ntp": {
        "name": "NTP",
        "rfc": "RFC 5905",
        "messages": NTP_MESSAGES,
        "expect_fixed_len": 48,
    },
    "tls-record": {
        "name": "TLS 1.2 record",
        "rfc": "RFC 5246",
        "messages": TLS_RECORD_MESSAGES,
        "expect_length_offset": 3,
        "expect_endian": "be",
    },
}
