"""JSON API schema peel — merge structure across response bodies."""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any


def _value_class(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int) and not isinstance(v, bool):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        if v.startswith("http://") or v.startswith("https://"):
            return "url"
        if re.fullmatch(r"[0-9a-fA-F-]{8,}", v) and ("-" in v or len(v) >= 16):
            return "id"
        if "@" in v and "." in v.split("@")[-1]:
            return "email"
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    return type(v).__name__


def _walk_schema(obj: Any, schema: dict[str, Counter[str]], prefix: str = "") -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            schema.setdefault(path, Counter())[_value_class(v)] += 1
            if isinstance(v, (dict, list)):
                _walk_schema(v, schema, path)
    elif isinstance(obj, list):
        path = f"{prefix}[]" if prefix else "[]"
        schema.setdefault(path, Counter())["array"] += 1
        for item in obj[:3]:
            _walk_schema(item, schema, f"{prefix}[0]" if prefix else "[0]")


def parse_json_bodies(messages: list[bytes]) -> list[Any]:
    out: list[Any] = []
    for m in messages:
        text = m.lstrip()
        if not text or text[:1] not in (b"{", b"["):
            continue
        try:
            out.append(json.loads(m.decode("utf-8", errors="replace")))
        except Exception:
            continue
    return out


def json_api_deep(
    messages: list[bytes],
    *,
    headers: list[dict] | None = None,
) -> dict:
    """Merge JSON schemas across bodies; attach HTTP meta when present."""
    objs = parse_json_bodies(messages)
    schema: dict[str, Counter[str]] = {}
    for obj in objs:
        _walk_schema(obj, schema)

    fields = []
    for path, counts in sorted(schema.items(), key=lambda x: (-sum(x[1].values()), x[0]))[:40]:
        top = counts.most_common(1)[0][0] if counts else "?"
        fields.append({
            "path": path,
            "type": top,
            "types": dict(counts),
            "seen": sum(counts.values()),
        })

    paths: list[str] = []
    statuses: list[str] = []
    for h in headers or []:
        if ":path" in h:
            auth = h.get(":authority", "")
            paths.append(f"{auth}{h[':path']}" if auth else h[":path"])
        if ":status" in h:
            statuses.append(str(h[":status"]))

    return {
        "kind": "json_api",
        "bodies": len(objs),
        "fields": fields,
        "field_count": len(fields),
        "paths": sorted(set(paths))[:12],
        "statuses": sorted(set(statuses))[:8],
        "sample_keys": [f["path"] for f in fields[:12]],
    }


def looks_like_json_api(messages: list[bytes]) -> bool:
    if not messages:
        return False
    n = sum(1 for m in messages if m.lstrip()[:1] in (b"{", b"["))
    return n >= max(1, (len(messages) + 1) // 2)
