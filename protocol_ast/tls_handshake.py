"""Deep TLS handshake parsing (ClientHello extensions)."""

from __future__ import annotations

import struct

TLS_EXT_NAMES = {
    0: "server_name",
    10: "supported_groups",
    11: "ec_point_formats",
    13: "signature_algorithms",
    16: "alpn",
    43: "supported_versions",
    45: "psk_key_exchange_modes",
    51: "key_share",
}


def _parse_extensions(data: bytes, pos: int, end: int) -> list[dict]:
    exts: list[dict] = []
    while pos + 4 <= end and pos + 4 <= len(data):
        etype = struct.unpack(">H", data[pos : pos + 2])[0]
        elen = struct.unpack(">H", data[pos + 2 : pos + 4])[0]
        pos += 4
        edata = data[pos : pos + elen]
        pos += elen
        entry: dict = {"type": etype, "name": TLS_EXT_NAMES.get(etype, f"ext_{etype}"), "len": elen}
        if etype == 0 and len(edata) >= 5:
            hosts: list[str] = []
            p = 2
            while p + 3 <= len(edata):
                if edata[p] != 0:
                    p += 1
                    continue
                nlen = struct.unpack(">H", edata[p + 1 : p + 3])[0]
                p += 3
                if p + nlen <= len(edata):
                    hosts.append(edata[p : p + nlen].decode("ascii", errors="replace"))
                p += nlen
            entry["sni"] = hosts
        elif etype == 16 and len(edata) >= 2:
            alpn: list[str] = []
            p = 2
            while p < len(edata):
                ln = edata[p]
                p += 1
                if p + ln <= len(edata):
                    alpn.append(edata[p : p + ln].decode("ascii", errors="replace"))
                p += ln
            entry["alpn"] = alpn
        elif etype == 43 and len(edata) >= 1:
            entry["supported_versions"] = [f"0x{v:04x}" for v in edata[1:]]
        exts.append(entry)
    return exts


def parse_client_hello(body: bytes) -> dict | None:
    """Parse TLS ClientHello handshake body (starts with type 0x01)."""
    if len(body) < 38 or body[0] != 0x01:
        return None
    pos = 4
    client_version = struct.unpack(">H", body[pos : pos + 2])[0]
    pos += 2 + 32
    sid_len = body[pos]
    pos += 1 + sid_len
    if pos + 2 > len(body):
        return None
    cs_len = struct.unpack(">H", body[pos : pos + 2])[0]
    pos += 2
    cipher_suites = [
        f"0x{struct.unpack('>H', body[pos + i : pos + i + 2])[0]:04x}"
        for i in range(0, min(cs_len, len(body) - pos), 2)
    ]
    pos += cs_len
    if pos >= len(body):
        return None
    cm_len = body[pos]
    pos += 1 + cm_len
    if pos + 2 > len(body):
        return None
    ext_len = struct.unpack(">H", body[pos : pos + 2])[0]
    pos += 2
    extensions = _parse_extensions(body, pos, pos + ext_len)
    sni = []
    alpn = []
    for e in extensions:
        sni.extend(e.get("sni", []))
        alpn.extend(e.get("alpn", []))
    return {
        "type": "ClientHello",
        "client_version": f"0x{client_version:04x}",
        "cipher_suites": cipher_suites[:12],
        "cipher_count": len(cipher_suites),
        "extensions": [e["name"] for e in extensions],
        "sni": sni,
        "alpn": alpn,
    }


def parse_tls_handshake_fragment(fragment: bytes) -> dict | None:
    if len(fragment) < 4:
        return None
    htype = fragment[0]
    if htype == 1:
        return parse_client_hello(fragment)
    if htype == 2:
        return {"type": "ServerHello"}
    if htype == 11:
        return {"type": "Certificate"}
    return {"type": f"handshake_{htype}"}
