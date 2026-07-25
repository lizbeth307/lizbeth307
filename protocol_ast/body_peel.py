"""Classify and peel application bodies (HTML / JSON / text) after HTTP decrypt."""

from __future__ import annotations

import json
import re
from collections import Counter


def _preview(data: bytes, limit: int = 100) -> str:
    sample = data[:limit]
    printable = sum(1 for b in sample if 32 <= b < 127 or b in (9, 10, 13))
    if sample and printable / len(sample) >= 0.7:
        return sample.decode("utf-8", errors="replace").replace("\n", "\\n")
    return sample.hex()[:limit]


def classify_body(data: bytes) -> str:
    head = data[:400].lstrip().lower()
    if head.startswith(b"<!doctype html") or head.startswith(b"<html") or b"<html" in head[:80]:
        return "html"
    if head[:1] in (b"{", b"["):
        try:
            json.loads(data.decode("utf-8", errors="strict"))
            return "json"
        except Exception:
            try:
                json.loads(data.decode("utf-8", errors="replace"))
                return "json"
            except Exception:
                pass
    text_ratio = sum(1 for b in data[:200] if 32 <= b < 127 or b in (9, 10, 13)) / max(1, min(len(data), 200))
    if text_ratio >= 0.85:
        return "text"
    return "binary"


def _json_keys(obj, *, prefix: str = "", limit: int = 24) -> list[str]:
    keys: list[str] = []

    def walk(o, p: str) -> None:
        if len(keys) >= limit:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                path = f"{p}.{k}" if p else str(k)
                keys.append(path)
                if len(keys) >= limit:
                    return
                if isinstance(v, (dict, list)):
                    walk(v, path)
        elif isinstance(o, list) and o:
            keys.append(f"{p}[]" if p else "[]")
            walk(o[0], f"{p}[0]" if p else "[0]")

    walk(obj, prefix)
    return keys[:limit]


def _decode_text(data: bytes, charset: str | None = None) -> str:
    candidates = []
    if charset:
        candidates.append(charset.strip().strip('"').strip("'"))
    candidates.extend(["utf-8", "iso-8859-1", "windows-1252", "latin-1"])
    seen: set[str] = set()
    for enc in candidates:
        key = enc.lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


def _charset_from_meta_html(data: bytes) -> str | None:
    head = data[:4000].decode("ascii", errors="ignore").lower()
    m = re.search(r'charset\s*=\s*["\']?([\w-]+)', head)
    return m.group(1) if m else None


def html_title(data: bytes, charset: str | None = None) -> str | None:
    enc = charset or _charset_from_meta_html(data)
    text = _decode_text(data[:8000], enc)
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(1)).strip()[:120]


def body_deep(messages: list[bytes], *, charset: str | None = None) -> dict:
    kinds: Counter[str] = Counter()
    titles: list[str] = []
    json_keys: list[str] = []
    previews: list[str] = []
    for m in messages[:12]:
        kind = classify_body(m)
        kinds[kind] += 1
        ch = charset or _charset_from_meta_html(m)
        previews.append(_preview(_decode_text(m, ch).encode("utf-8", errors="replace"), 100) if kind in ("html", "text") else _preview(m, 100))
        if kind == "html":
            # Prefer readable UTF-8 preview for html
            try:
                previews[-1] = _decode_text(m, ch).replace("\n", "\\n")[:100]
            except Exception:
                pass
            t = html_title(m, ch)
            if t:
                titles.append(t)
        elif kind == "json":
            try:
                obj = json.loads(_decode_text(m, charset or "utf-8"))
                json_keys.extend(_json_keys(obj))
            except Exception:
                pass
    # unique keys preserve order
    seen: set[str] = set()
    uniq_keys = []
    for k in json_keys:
        if k not in seen:
            seen.add(k)
            uniq_keys.append(k)
    return {
        "kind": "body",
        "types": dict(kinds),
        "titles": titles[:5],
        "json_keys": uniq_keys[:20],
        "preview": previews[:4],
        "structured": kinds.get("html", 0) + kinds.get("json", 0) + kinds.get("text", 0) > 0,
    }


def looks_like_app_body(messages: list[bytes]) -> bool:
    if not messages:
        return False
    hits = sum(1 for m in messages if classify_body(m) in ("html", "json", "text"))
    return hits >= max(1, (len(messages) + 1) // 2)
