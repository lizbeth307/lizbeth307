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
        if length > 16_384 + 256:  # above default SETTINGS max + slack
            return frames if frames else None
        if ftype > 0x9 and ftype not in FRAME_TYPES:
            # unknown type — allow a few extension types < 0x20
            if ftype > 0x1F:
                return frames if frames else None
        end = off + 9 + length
        if end > len(data):
            break
        frames.append(data[off:end])
        off = end
    if off < len(data) and not frames:
        return None
    return frames if len(frames) >= 1 else None


def looks_like_http2(messages: list[bytes]) -> bool:
    preface = sum(1 for m in messages if m.startswith(HTTP2_PREFACE))
    if preface:
        return True
    ok = 0
    for m in messages:
        frames = _parse_frames(m)
        if frames and len(frames) >= 1:
            # SETTINGS often first after preface; type byte at [3]
            types = [f[3] for f in frames if len(f) > 3]
            if any(t in FRAME_TYPES for t in types):
                ok += 1
    return ok >= max(1, len(messages) // 3)


def split_http2_frames(messages: list[bytes]) -> tuple[str, list[bytes]] | None:
    """Split decrypted payloads into HTTP/2 frames."""
    if not looks_like_http2(messages) and not any(m.startswith(HTTP2_PREFACE) for m in messages):
        # still try parse — decrypted appdata is often pure frames without preface
        pass
    frames: list[bytes] = []
    parsed_msgs = 0
    for m in messages:
        got = _parse_frames(m)
        if got:
            frames.extend(got)
            parsed_msgs += 1
    if parsed_msgs >= 1 and len(frames) >= 2:
        # require majority of bytes explained as frames for non-preface streams
        return "http2_frames", frames
    return None


def http2_deep(frames: list[bytes]) -> dict:
    types: Counter[str] = Counter()
    streams: set[int] = set()
    has_preface = False
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
    return {
        "kind": "http2",
        "frames": dict(types),
        "streams": len(streams),
        "preface": has_preface,
        "total_frames": sum(types.values()),
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
