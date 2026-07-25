"""Extract TLS keylog from pcapng Decryption Secrets Blocks (DSB)."""

from __future__ import annotations

import struct
from pathlib import Path

PCAPNG_MAGIC = 0x0A0D0D0A
BT_DSB = 0x0000000A
SECRETS_TLSK = 0x544C534B  # "TLSK"


def extract_tls_keylog_from_pcapng(path: str | Path) -> str | None:
    """Return NSS keylog text embedded in pcapng DSB, or None."""
    data = Path(path).read_bytes()
    if len(data) < 12 or struct.unpack("<I", data[:4])[0] != PCAPNG_MAGIC:
        return None
    chunks: list[str] = []
    off = 0
    while off + 8 <= len(data):
        block_type, block_len = struct.unpack("<II", data[off : off + 8])
        if block_len < 12 or off + block_len > len(data):
            break
        if block_type == BT_DSB and block_len >= 20:
            body = data[off + 8 : off + block_len - 4]
            if len(body) >= 8:
                secrets_type, secrets_len = struct.unpack("<II", body[:8])
                if secrets_type == SECRETS_TLSK and secrets_len > 0:
                    payload = body[8 : 8 + secrets_len]
                    try:
                        text = payload.decode("utf-8", errors="replace")
                    except Exception:
                        text = ""
                    if "CLIENT_" in text or "SERVER_" in text:
                        chunks.append(text)
        off += block_len
    if not chunks:
        return None
    # ensure trailing newline between chunks
    merged = "\n".join(c.rstrip("\n") for c in chunks) + "\n"
    return merged


def write_keylog_beside_capture(pcap_path: str | Path) -> Path | None:
    """If pcapng has DSB secrets, write sibling .keylog and return its path."""
    pcap_path = Path(pcap_path).expanduser()
    text = extract_tls_keylog_from_pcapng(pcap_path)
    if not text:
        return None
    out = pcap_path.with_name(pcap_path.stem + ".keylog")
    out.write_text(text, encoding="utf-8")
    return out
