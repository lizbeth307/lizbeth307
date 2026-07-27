"""Binary app-layer peel — protobuf wire + MessagePack (no pip deps)."""

from __future__ import annotations

from collections import Counter
from typing import Any


WIRE_NAMES = {
    0: "varint",
    1: "fixed64",
    2: "len",
    5: "fixed32",
}


def _read_varint(data: bytes, off: int) -> tuple[int, int] | None:
    value = 0
    shift = 0
    while off < len(data) and shift < 64:
        b = data[off]
        off += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            return value, off
        shift += 7
    return None


def parse_protobuf_fields(data: bytes, *, limit: int = 48) -> list[dict[str, Any]]:
    """Best-effort protobuf wire parse; stops on first invalid tag."""
    fields: list[dict[str, Any]] = []
    off = 0
    n = len(data)
    while off < n and len(fields) < limit:
        tag_v = _read_varint(data, off)
        if tag_v is None:
            break
        tag, off = tag_v
        if tag == 0:
            break
        field = tag >> 3
        wire = tag & 0x07
        if field == 0 or wire not in WIRE_NAMES:
            break
        entry: dict[str, Any] = {"field": field, "wire": WIRE_NAMES[wire]}
        if wire == 0:
            vv = _read_varint(data, off)
            if vv is None:
                break
            value, off = vv
            entry["value"] = value
        elif wire == 1:
            if off + 8 > n:
                break
            entry["raw"] = data[off : off + 8].hex()
            off += 8
        elif wire == 2:
            lv = _read_varint(data, off)
            if lv is None:
                break
            length, off = lv
            if length < 0 or off + length > n:
                break
            blob = data[off : off + length]
            off += length
            entry["len"] = length
            printable = sum(1 for b in blob if 32 <= b < 127) / max(1, length)
            nested = parse_protobuf_fields(blob, limit=8) if length >= 3 else []
            nested_cov = protobuf_coverage(blob) if nested else 0.0
            # Prefer string when highly printable; nested only if strong wire coverage
            if printable >= 0.85:
                entry["kind"] = "string"
                entry["text"] = blob.decode("utf-8", errors="replace")[:80]
            elif nested and len(nested) >= 2 and nested_cov >= 0.8:
                entry["nested"] = nested
                entry["kind"] = "message"
            else:
                entry["kind"] = "bytes"
                entry["preview"] = blob[:16].hex()
        elif wire == 5:
            if off + 4 > n:
                break
            entry["raw"] = data[off : off + 4].hex()
            off += 4
        fields.append(entry)
    return fields


def protobuf_consumed(data: bytes) -> int:
    """Bytes successfully consumed by protobuf wire parse."""
    off = 0
    n = len(data)
    count = 0
    while off < n and count < 64:
        start = off
        tag_v = _read_varint(data, off)
        if tag_v is None:
            break
        tag, off = tag_v
        if tag == 0:
            break
        field = tag >> 3
        wire = tag & 0x07
        if field == 0 or wire not in WIRE_NAMES:
            break
        if wire == 0:
            vv = _read_varint(data, off)
            if vv is None:
                break
            _, off = vv
        elif wire == 1:
            if off + 8 > n:
                break
            off += 8
        elif wire == 2:
            lv = _read_varint(data, off)
            if lv is None:
                break
            length, off = lv
            if length < 0 or off + length > n:
                break
            off += length
        elif wire == 5:
            if off + 4 > n:
                break
            off += 4
        else:
            break
        if off <= start:
            break
        count += 1
    return off


def protobuf_coverage(data: bytes) -> float:
    if len(data) < 2:
        return 0.0
    return min(1.0, protobuf_consumed(data) / max(1, len(data)))


def looks_like_protobuf(messages: list[bytes]) -> bool:
    if not messages:
        return False
    ok = 0
    for m in messages[:8]:
        if len(m) < 3:
            continue
        # skip obvious text / http / tls
        if m.lstrip()[:1] in (b"{", b"[", b"<") or m[:1] in (b"G", b"P", b"H"):
            continue
        cov = protobuf_coverage(m)
        fields = parse_protobuf_fields(m, limit=12)
        if cov >= 0.6 and len(fields) >= 2:
            ok += 1
    return ok >= max(1, min(2, (len(messages) + 2) // 3))


def protobuf_deep(messages: list[bytes]) -> dict:
    field_wires: dict[int, Counter[str]] = {}
    samples: list[dict] = []
    coverages: list[float] = []
    for m in messages[:12]:
        fields = parse_protobuf_fields(m)
        coverages.append(protobuf_coverage(m))
        if fields and len(samples) < 3:
            samples.append({"len": len(m), "fields": fields[:12]})
        for f in fields:
            field_wires.setdefault(f["field"], Counter())[f["wire"]] += 1
    schema = []
    for num, wires in sorted(field_wires.items(), key=lambda x: x[0])[:24]:
        top = wires.most_common(1)[0][0]
        schema.append({"field": num, "wire": top, "seen": sum(wires.values()), "wires": dict(wires)})
    return {
        "kind": "protobuf",
        "messages": len(messages),
        "schema": schema,
        "field_count": len(schema),
        "avg_coverage": round(sum(coverages) / max(1, len(coverages)), 3),
        "samples": samples,
    }


# --- MessagePack (subset detector / peel) ---

def _mp_skip(data: bytes, off: int) -> int | None:
    """Return new offset after one msgpack object, or None."""
    if off >= len(data):
        return None
    b = data[off]
    off += 1
    # positive fixint / negative fixint / nil / bool
    if b <= 0x7F or b >= 0xE0 or b in (0xC0, 0xC2, 0xC3):
        return off
    if 0xA0 <= b <= 0xBF:  # fixstr
        return off + (b & 0x1F)
    if 0x90 <= b <= 0x9F:  # fixarray
        n = b & 0x0F
        for _ in range(n):
            off2 = _mp_skip(data, off)
            if off2 is None:
                return None
            off = off2
        return off
    if 0x80 <= b <= 0x8F:  # fixmap
        n = b & 0x0F
        for _ in range(n * 2):
            off2 = _mp_skip(data, off)
            if off2 is None:
                return None
            off = off2
        return off
    if b == 0xCC:  # uint8
        return off + 1 if off + 1 <= len(data) else None
    if b == 0xCD:
        return off + 2 if off + 2 <= len(data) else None
    if b == 0xCE:
        return off + 4 if off + 4 <= len(data) else None
    if b == 0xCF:
        return off + 8 if off + 8 <= len(data) else None
    if b == 0xD0:
        return off + 1 if off + 1 <= len(data) else None
    if b == 0xD1:
        return off + 2 if off + 2 <= len(data) else None
    if b == 0xD2:
        return off + 4 if off + 4 <= len(data) else None
    if b == 0xD3:
        return off + 8 if off + 8 <= len(data) else None
    if b == 0xCA:
        return off + 4 if off + 4 <= len(data) else None
    if b == 0xCB:
        return off + 8 if off + 8 <= len(data) else None
    if b == 0xD9:  # str8
        if off >= len(data):
            return None
        return off + 1 + data[off]
    if b == 0xDA:
        if off + 2 > len(data):
            return None
        ln = int.from_bytes(data[off : off + 2], "big")
        return off + 2 + ln
    if b == 0xDB:
        if off + 4 > len(data):
            return None
        ln = int.from_bytes(data[off : off + 4], "big")
        return off + 4 + ln
    if b == 0xC4:  # bin8
        if off >= len(data):
            return None
        return off + 1 + data[off]
    if b == 0xC5:
        if off + 2 > len(data):
            return None
        ln = int.from_bytes(data[off : off + 2], "big")
        return off + 2 + ln
    if b == 0xC6:
        if off + 4 > len(data):
            return None
        ln = int.from_bytes(data[off : off + 4], "big")
        return off + 4 + ln
    if b == 0xDC:  # array16
        if off + 2 > len(data):
            return None
        n = int.from_bytes(data[off : off + 2], "big")
        off += 2
        for _ in range(n):
            off2 = _mp_skip(data, off)
            if off2 is None:
                return None
            off = off2
        return off
    if b == 0xDD:
        if off + 4 > len(data):
            return None
        n = int.from_bytes(data[off : off + 4], "big")
        off += 4
        for _ in range(n):
            off2 = _mp_skip(data, off)
            if off2 is None:
                return None
            off = off2
        return off
    if b == 0xDE:  # map16
        if off + 2 > len(data):
            return None
        n = int.from_bytes(data[off : off + 2], "big")
        off += 2
        for _ in range(n * 2):
            off2 = _mp_skip(data, off)
            if off2 is None:
                return None
            off = off2
        return off
    if b == 0xDF:
        if off + 4 > len(data):
            return None
        n = int.from_bytes(data[off : off + 4], "big")
        off += 4
        for _ in range(n * 2):
            off2 = _mp_skip(data, off)
            if off2 is None:
                return None
            off = off2
        return off
    return None


_MP_NIL = object()


def _mp_parse(data: bytes, off: int = 0) -> tuple[Any, int] | None:
    if off >= len(data):
        return None
    b = data[off]
    off += 1
    if b <= 0x7F:
        return b, off
    if b >= 0xE0:
        return b - 256, off
    if b == 0xC0:
        return _MP_NIL, off
    if b == 0xC2:
        return False, off
    if b == 0xC3:
        return True, off
    if 0xA0 <= b <= 0xBF:
        n = b & 0x1F
        if off + n > len(data):
            return None
        return data[off : off + n].decode("utf-8", errors="replace"), off + n
    if 0x90 <= b <= 0x9F:
        n = b & 0x0F
        arr = []
        for _ in range(n):
            item = _mp_parse(data, off)
            if item is None:
                return None
            v, off = item
            arr.append(v)
        return arr, off
    if 0x80 <= b <= 0x8F:
        n = b & 0x0F
        mp: dict[str, Any] = {}
        for _ in range(n):
            k = _mp_parse(data, off)
            if k is None:
                return None
            key, off = k
            v = _mp_parse(data, off)
            if v is None:
                return None
            val, off = v
            mp[str(key)] = val
        return mp, off
    if b == 0xCC and off < len(data):
        return data[off], off + 1
    if b == 0xCD and off + 2 <= len(data):
        return int.from_bytes(data[off : off + 2], "big"), off + 2
    if b == 0xCE and off + 4 <= len(data):
        return int.from_bytes(data[off : off + 4], "big"), off + 4
    if b == 0xD9 and off < len(data):
        n = data[off]
        off += 1
        if off + n > len(data):
            return None
        return data[off : off + n].decode("utf-8", errors="replace"), off + n
    if b == 0xDC and off + 2 <= len(data):
        n = int.from_bytes(data[off : off + 2], "big")
        off += 2
        arr = []
        for _ in range(n):
            item = _mp_parse(data, off)
            if item is None:
                return None
            v, off = item
            arr.append(v)
        return arr, off
    if b == 0xDE and off + 2 <= len(data):
        n = int.from_bytes(data[off : off + 2], "big")
        off += 2
        mp = {}
        for _ in range(n):
            k = _mp_parse(data, off)
            if k is None:
                return None
            key, off = k
            v = _mp_parse(data, off)
            if v is None:
                return None
            val, off = v
            mp[str(key)] = val
        return mp, off
    return None


def msgpack_coverage(data: bytes) -> float:
    end = _mp_skip(data, 0)
    if end is None or end <= 0:
        return 0.0
    return min(1.0, end / max(1, len(data)))


def looks_like_msgpack(messages: list[bytes]) -> bool:
    if not messages:
        return False
    ok = 0
    for m in messages[:8]:
        if len(m) < 2:
            continue
        if m.lstrip()[:1] in (b"{", b"[", b"<"):
            continue
        # prefer map/array markers
        if m[0] not in range(0x80, 0xA0) and m[0] not in (0xDE, 0xDF, 0xDC, 0xDD):
            # still allow fixstr-rooted rarely
            if not (0xA0 <= m[0] <= 0xBF):
                continue
        cov = msgpack_coverage(m)
        if cov >= 0.85:
            ok += 1
    return ok >= max(1, min(2, (len(messages) + 2) // 3))


def _mp_keys(obj: Any, *, prefix: str = "", limit: int = 24) -> list[str]:
    keys: list[str] = []

    def walk(o: Any, p: str) -> None:
        if len(keys) >= limit:
            return
        if o is _MP_NIL:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                path = f"{p}.{k}" if p else str(k)
                keys.append(path)
                if isinstance(v, (dict, list)):
                    walk(v, path)
        elif isinstance(o, list) and o:
            keys.append(f"{p}[]" if p else "[]")
            walk(o[0], f"{p}[0]" if p else "[0]")

    walk(obj, prefix)
    return keys[:limit]


def msgpack_deep(messages: list[bytes]) -> dict:
    keys: list[str] = []
    types: Counter[str] = Counter()
    parsed = 0
    for m in messages[:12]:
        item = _mp_parse(m, 0)
        if item is None:
            continue
        obj, end = item
        if end < len(m) * 0.8:
            continue
        parsed += 1
        if isinstance(obj, dict):
            types["map"] += 1
            keys.extend(_mp_keys(obj))
        elif isinstance(obj, list):
            types["array"] += 1
            keys.extend(_mp_keys(obj))
        else:
            types[type(obj).__name__] += 1
    seen: set[str] = set()
    uniq = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            uniq.append(k)
    return {
        "kind": "msgpack",
        "messages": len(messages),
        "parsed": parsed,
        "types": dict(types),
        "keys": uniq[:20],
        "key_count": len(uniq),
    }


def binary_peel(messages: list[bytes]) -> dict | None:
    """Pick best binary peel for opaque app payloads."""
    if looks_like_protobuf(messages):
        return protobuf_deep(messages)
    if looks_like_msgpack(messages):
        return msgpack_deep(messages)
    return None
