"""HTTP/2 frame discovery on decrypted TLS payloads."""

from __future__ import annotations

from collections import Counter

HTTP2_PREFACE = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"

FRAME_TYPES = {
    0x0: "DATA",
    0x1: "HEADERS",
    0x2: "PRIORITY",
    0x3: "RST_STREAM",
    0x4: "SETTINGS",
    0x5: "PUSH_PROMISE",
    0x6: "PING",
    0x7: "GOAWAY",
    0x8: "WINDOW_UPDATE",
    0x9: "CONTINUATION",
}


def _parse_frames(data: bytes) -> list[bytes] | None:
    """Parse HTTP/2 frames from a blob; None if clearly not HTTP/2."""
    if not data:
        return None
    off = 0
    if data.startswith(HTTP2_PREFACE):
        off = len(HTTP2_PREFACE)
    frames: list[bytes] = []
    while off + 9 <= len(data):
        length = int.from_bytes(data[off : off + 3], "big")
        ftype = data[off + 3]
        if length > 16_384 + 256:
            return frames if frames else None
        if ftype > 0x9 and ftype not in FRAME_TYPES and ftype > 0x1F:
            return frames if frames else None
        end = off + 9 + length
        if end > len(data):
            break
        frames.append(data[off:end])
        off = end
    if off < len(data) and not frames:
        return None
    return frames if len(frames) >= 1 else None


def is_single_http2_frame(msg: bytes) -> bool:
    if len(msg) < 9:
        return False
    length = int.from_bytes(msg[:3], "big")
    return 9 + length == len(msg) and msg[3] <= 0x1F


def all_single_http2_frames(messages: list[bytes]) -> bool:
    return bool(messages) and all(is_single_http2_frame(m) for m in messages)


def peel_http2_data_payloads(messages: list[bytes]) -> list[bytes]:
    """Extract DATA frame payloads (next signal layer)."""
    out: list[bytes] = []
    for m in messages:
        if not is_single_http2_frame(m) or m[3] != 0x0:
            continue
        length = int.from_bytes(m[:3], "big")
        payload = m[9 : 9 + length]
        flags = m[4]
        if flags & 0x08 and payload:  # PADDED
            pad = payload[0]
            end = len(payload) - pad
            payload = payload[1:end] if end > 1 else b""
        if payload:
            out.append(payload)
    return out


def looks_like_http2(messages: list[bytes]) -> bool:
    if any(m.startswith(HTTP2_PREFACE) for m in messages):
        return True
    if all_single_http2_frames(messages):
        return True
    ok = 0
    for m in messages:
        frames = _parse_frames(m)
        if frames and any(len(f) > 3 and f[3] in FRAME_TYPES for f in frames):
            ok += 1
    return ok >= max(1, len(messages) // 3)


def split_http2_frames(messages: list[bytes]) -> tuple[str, list[bytes]] | None:
    """
    Split decrypted payloads into HTTP/2 frames.

    - Blobs → individual frames (keep HEADERS/DATA, do not drop singles).
    - Already-individual frames → peel DATA payloads (stop recursion).
    """
    if all_single_http2_frames(messages):
        data = peel_http2_data_payloads(messages)
        if len(data) >= 1:
            return "http2_data", data
        return None

    frames: list[bytes] = []
    grew = False
    for m in messages:
        if is_single_http2_frame(m):
            frames.append(m)
            continue
        got = _parse_frames(m)
        if not got:
            continue
        frames.extend(got)
        if len(got) > 1:
            grew = True
        elif len(got) == 1 and got[0] != m:
            grew = True

    if len(frames) < 2:
        return None
    # Progress: split at least one blob, or collected more frames than inputs
    if grew or len(frames) > len(messages):
        return "http2_frames", frames
    # Mixed leftovers that are all single frames after collect
    if all_single_http2_frames(frames):
        data = peel_http2_data_payloads(frames)
        if data:
            return "http2_data", data
    return None


def _text_preview(data: bytes, limit: int = 80) -> str:
    sample = data[:limit]
    printable = sum(1 for b in sample if 32 <= b < 127 or b in (9, 10, 13))
    if sample and printable / len(sample) >= 0.7:
        return sample.decode("utf-8", errors="replace").replace("\n", "\\n")
    return sample.hex()[:limit]


def http2_deep(frames: list[bytes]) -> dict:
    types: Counter[str] = Counter()
    streams: set[int] = set()
    has_preface = False
    data_previews: list[str] = []
    for f in frames:
        if f == HTTP2_PREFACE or f.startswith(HTTP2_PREFACE):
            has_preface = True
            continue
        if len(f) < 9:
            continue
        t = FRAME_TYPES.get(f[3], f"type{f[3]}")
        types[t] += 1
        sid = int.from_bytes(f[5:9], "big") & 0x7FFFFFFF
        if sid:
            streams.add(sid)
        if f[3] == 0x0 and len(f) > 9 and len(data_previews) < 3:
            data_previews.append(_text_preview(f[9:]))
    return {
        "kind": "http2",
        "frames": dict(types),
        "streams": len(streams),
        "preface": has_preface,
        "total_frames": sum(types.values()),
        "data_preview": data_previews,
    }


def http2_data_deep(payloads: list[bytes]) -> dict:
    previews = [_text_preview(p, 120) for p in payloads[:5]]
    html = sum(1 for p in payloads if b"<html" in p[:200].lower() or b"<!doctype" in p[:200].lower())
    json_n = sum(1 for p in payloads if p[:1] in (b"{", b"[") or p.lstrip()[:1] in (b"{", b"["))
    return {
        "kind": "http2_data",
        "payloads": len(payloads),
        "html": html,
        "json": json_n,
        "preview": previews,
    }


def looks_like_http1(messages: list[bytes]) -> bool:
    markers = (b"HTTP/1.", b"GET ", b"POST ", b"HEAD ", b"PUT ", b"CONNECT ")
    hits = sum(1 for m in messages if any(m.startswith(x) or x in m[:64] for x in markers))
    return hits >= max(1, len(messages) // 4)


def http1_deep(messages: list[bytes]) -> dict:
    methods: Counter[str] = Counter()
    hosts: list[str] = []
    for m in messages[:40]:
        head = m.split(b"\r\n", 1)[0][:200]
        try:
            line = head.decode("ascii", errors="ignore")
        except Exception:
            continue
        for meth in ("GET", "POST", "HEAD", "PUT", "CONNECT", "OPTIONS", "DELETE", "PATCH"):
            if line.startswith(meth + " "):
                methods[meth] += 1
                break
        if line.startswith("HTTP/1."):
            methods["RESPONSE"] += 1
        for raw in m.split(b"\r\n")[:20]:
            if raw.lower().startswith(b"host:"):
                try:
                    hosts.append(raw.split(b":", 1)[1].strip().decode("ascii", errors="ignore"))
                except Exception:
                    pass
    return {
        "kind": "http1",
        "methods": dict(methods),
        "hosts": sorted(set(hosts))[:20],
    }
