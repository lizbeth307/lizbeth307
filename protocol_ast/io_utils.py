"""Load binary messages from files and stdin."""

from __future__ import annotations

import re
import struct
import sys
from pathlib import Path


_HEX_LINE = re.compile(r"^[0-9a-fA-F\s:]+$")


def parse_hex_line(line: str) -> bytes:
    """Parse a line like 'fe ca 01 02' or 'feca0102'."""
    cleaned = re.sub(r"[^0-9a-fA-F]", "", line.strip())
    if not cleaned or len(cleaned) % 2:
        raise ValueError(f"invalid hex line: {line!r}")
    return bytes.fromhex(cleaned)


def load_messages_from_text(path: str | Path) -> list[bytes]:
    """One message per non-empty line (hex)."""
    messages: list[bytes] = []
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            messages.append(parse_hex_line(line))
        except ValueError as exc:
            raise ValueError(f"{path}:{lineno}: {exc}") from exc
    return messages


def load_messages_from_binary(path: str | Path) -> list[bytes]:
    """Length-prefixed corpus: u32le count, then u32le len + bytes per message."""
    data = Path(path).read_bytes()
    if len(data) < 4:
        raise ValueError("binary corpus too short")
    (count,) = struct.unpack_from("<I", data, 0)
    offset = 4
    messages: list[bytes] = []
    for _ in range(count):
        if offset + 4 > len(data):
            raise ValueError("truncated binary corpus (length header)")
        (length,) = struct.unpack_from("<I", data, offset)
        offset += 4
        if offset + length > len(data):
            raise ValueError("truncated binary corpus (payload)")
        messages.append(data[offset : offset + length])
        offset += length
    return messages


def load_messages(path: str | Path) -> list[bytes]:
    p = Path(path)
    if p.suffix.lower() in {".bin", ".corpus"}:
        return load_messages_from_binary(p)
    return load_messages_from_text(p)


def load_messages_from_stdin() -> list[bytes]:
    messages: list[bytes] = []
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        messages.append(parse_hex_line(line))
    return messages


def save_corpus_binary(messages: list[bytes], path: str | Path) -> None:
  buf = bytearray()
  buf.extend(struct.pack("<I", len(messages)))
  for msg in messages:
    buf.extend(struct.pack("<I", len(msg)))
    buf.extend(msg)
  Path(path).write_bytes(bytes(buf))


def save_corpus_hex(messages: list[bytes], path: str | Path) -> None:
    lines = [msg.hex() for msg in messages]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def hex_dump(data: bytes, width: int = 16) -> str:
    lines: list[str] = []
    for i in range(0, len(data), width):
        chunk = data[i : i + width]
        hexpart = " ".join(f"{b:02x}" for b in chunk)
        asciipart = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{i:08x}  {hexpart:<{width * 3}}  {asciipart}")
    return "\n".join(lines)
