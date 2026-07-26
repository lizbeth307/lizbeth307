"""Deep offline mine of a MITM/pcap dump — per-SNI, multi-session decrypt, protobuf strings."""

from __future__ import annotations

import hashlib
import re
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PRINTABLE_RE = re.compile(rb"[\x20-\x7e]{4,}")


def _ja3_ish(ch: dict) -> str:
    """Loose JA3-like fingerprint (not wire-compatible; stable within this tool)."""
    ciphers = "-".join(ch.get("cipher_suites") or [])
    exts = "-".join(ch.get("extensions") or [])
    alpn = ",".join(ch.get("alpn") or [])
    raw = f"{ch.get('client_version', '')},{ciphers},{exts},{alpn}"
    return hashlib.md5(raw.encode()).hexdigest()


def _strings(blob: bytes, *, limit: int = 80) -> list[str]:
    out: list[str] = []
    for m in PRINTABLE_RE.findall(blob):
        try:
            s = m.decode("ascii")
        except Exception:
            continue
        if s not in out:
            out.append(s)
        if len(out) >= limit:
            break
    return out


def _protobuf_strings(data: bytes, *, limit: int = 64, depth: int = 0) -> list[str]:
    if depth > 4 or not data:
        return []
    try:
        from .binary_peel import parse_protobuf_fields
    except Exception:
        return []
    found: list[str] = []
    for f in parse_protobuf_fields(data, limit=48):
        if f.get("kind") == "string" and f.get("text"):
            t = str(f["text"]).strip()
            if len(t) >= 2 and t not in found:
                found.append(t)
        for nested in f.get("nested") or []:
            if nested.get("kind") == "string" and nested.get("text"):
                t = str(nested["text"]).strip()
                if len(t) >= 2 and t not in found:
                    found.append(t)
            elif nested.get("kind") == "bytes" and nested.get("preview"):
                pass
        if f.get("kind") == "bytes" and f.get("len", 0) >= 8:
            # try nested message on length-delimited blobs we kept as bytes
            pass
        if len(found) >= limit:
            break
    # Also raw printable scan — catches strings protobuf parser skipped
    for s in _strings(data, limit=limit):
        if s not in found:
            found.append(s)
        if len(found) >= limit:
            break
    return found[:limit]


def _http1_summary(plain: list[bytes]) -> dict[str, Any]:
    try:
        from .http2 import http1_deep

        deep = http1_deep(plain)
        return {k: v for k, v in deep.items() if k != "bodies"}
    except Exception:
        return {}


def _try_gunzip(data: bytes) -> bytes | None:
    if not data.startswith(b"\x1f\x8b"):
        return None
    try:
        return zlib.decompress(data, 16 + zlib.MAX_WBITS)
    except Exception:
        return None


def extract_tcp_connections(path: Path) -> list[dict[str, Any]]:
    """
    Return per (sport,dport) TCP streams on port 443 (and other interesting ports).
    Uses analyze_pcap internals when available.
    """
    import analyze_pcap as ap

    tcp_segs: dict[tuple[int, int], list[tuple[int, bytes]]] = defaultdict(list)
    for link, frame in ap.iter_pcap(path):
        p = ap._extract(frame, link)
        if not p:
            continue
        proto, sport, dport, payload, seq = p
        if proto != "tcp" or seq is None or len(payload) < 1:
            continue
        if 443 not in (sport, dport) and min(sport, dport) > 1024:
            # keep high ports that look TLS later; skip noise for now
            if sport > 1024 and dport > 1024:
                continue
        key = (sport, dport)
        tcp_segs[key].append((seq, payload))

    conns: list[dict[str, Any]] = []
    for (sport, dport), segs in tcp_segs.items():
        segs = sorted(segs, key=lambda x: x[0])
        # merge contiguous-ish
        stream = b"".join(p for _, p in segs)
        if len(stream) < 40:
            continue
        records = ap._iter_tls_stream(stream) if hasattr(ap, "_iter_tls_stream") else [stream]
        if not records:
            records = [stream]
        conns.append(
            {
                "sport": sport,
                "dport": dport,
                "bytes": len(stream),
                "records": records,
                "seg_count": len(segs),
            }
        )
    return conns


def _annotate_conn(conn: dict[str, Any], secrets=None) -> dict[str, Any]:
    from .tls_handshake import parse_client_hello
    from .tls_keylog import (
        decrypt_tls_records,
        find_client_randoms_in_records,
        flatten_tls_records,
    )

    records = conn["records"]
    flat = flatten_tls_records(records)
    appdata = [r for r in flat if len(r) >= 5 and r[0] == 0x17]
    app_bytes = sum(len(r) - 5 for r in appdata)

    hellos: list[dict] = []
    sni: list[str] = []
    alpn: list[str] = []
    for rec in flat:
        if len(rec) < 6 or rec[0] != 0x16:
            continue
        length = (rec[3] << 8) | rec[4]
        body = rec[5 : 5 + length]
        off = 0
        while off + 4 <= len(body):
            htype = body[off]
            hlen = int.from_bytes(body[off + 1 : off + 4], "big")
            chunk = body[off : off + 4 + hlen]
            if htype == 0x01:
                ch = parse_client_hello(chunk)
                if ch:
                    ch = dict(ch)
                    ch["ja3_ish"] = _ja3_ish(ch)
                    cr = chunk[6:38].hex() if len(chunk) >= 38 else ""
                    ch["client_random"] = cr
                    hellos.append(ch)
                    sni.extend(ch.get("sni") or [])
                    alpn.extend(ch.get("alpn") or [])
            if hlen == 0:
                break
            off += 4 + hlen

    out: dict[str, Any] = {
        "sport": conn["sport"],
        "dport": conn["dport"],
        "stream_bytes": conn["bytes"],
        "tls_records": len(flat),
        "appdata_records": len(appdata),
        "appdata_bytes": app_bytes,
        "sni": sorted(set(sni)),
        "alpn": sorted(set(alpn)),
        "client_hellos": len(hellos),
        "ja3_ish": [h.get("ja3_ish") for h in hellos[:3]],
        "cipher_suites": (hellos[0].get("cipher_suites") if hellos else [])[:8],
        "extensions": (hellos[0].get("extensions") if hellos else [])[:16],
        "client_randoms": [h.get("client_random") for h in hellos if h.get("client_random")],
        "decrypt": None,
        "http1": None,
        "protobuf_strings": [],
        "all_strings": [],
    }

    if secrets is not None and appdata:
        # Try decrypt using only this connection's records (session isolation)
        res = decrypt_tls_records(flat, secrets)
        if res and res.decrypted:
            plains = list(res.decrypted)
            # Expand gzip orphans
            expanded: list[bytes] = []
            for p in plains:
                gz = _try_gunzip(p)
                expanded.append(gz if gz is not None else p)
            out["decrypt"] = {
                "status": "ok",
                "tls_version": res.tls_version,
                "plain_msgs": len(plains),
                "client_random": (res.client_random or "")[:16],
                "failed_records": res.failed,
            }
            out["http1"] = _http1_summary(plains)
            pb_strs: list[str] = []
            raw_strs: list[str] = []
            for p in expanded:
                for s in _protobuf_strings(p, limit=40):
                    if s not in pb_strs:
                        pb_strs.append(s)
                for s in _strings(p, limit=40):
                    if s not in raw_strs:
                        raw_strs.append(s)
            out["protobuf_strings"] = pb_strs[:60]
            out["all_strings"] = raw_strs[:80]
        else:
            reason = (res.diagnostics or {}).get("reason") if res else "no_result"
            out["decrypt"] = {
                "status": reason or "failed",
                "overlap": (res.diagnostics or {}).get("overlap") if res else 0,
            }
    return out


def mine_pcap(path: Path, keylog: Path | None = None) -> dict[str, Any]:
    secrets = None
    if keylog and keylog.exists():
        from .tls_keylog import parse_keylog

        secrets = parse_keylog(keylog)

    conns = extract_tcp_connections(path)
    annotated = [_annotate_conn(c, secrets) for c in conns]

    by_sni: dict[str, dict[str, Any]] = {}
    for a in annotated:
        hosts = a["sni"] or ["(no-sni)"]
        for h in hosts:
            bucket = by_sni.setdefault(
                h,
                {
                    "conns": 0,
                    "appdata_bytes": 0,
                    "stream_bytes": 0,
                    "decrypted_conns": 0,
                    "plain_msgs": 0,
                    "alpn": Counter(),
                    "ja3_ish": Counter(),
                },
            )
            bucket["conns"] += 1
            bucket["appdata_bytes"] += a["appdata_bytes"]
            bucket["stream_bytes"] += a["stream_bytes"]
            for x in a["alpn"]:
                bucket["alpn"][x] += 1
            for j in a["ja3_ish"]:
                if j:
                    bucket["ja3_ish"][j] += 1
            if a.get("decrypt") and a["decrypt"].get("status") == "ok":
                bucket["decrypted_conns"] += 1
                bucket["plain_msgs"] += a["decrypt"].get("plain_msgs") or 0

    # Flatten counters for JSON
    sni_table = []
    for host, b in sorted(by_sni.items(), key=lambda kv: -kv[1]["appdata_bytes"]):
        sni_table.append(
            {
                "sni": host,
                "conns": b["conns"],
                "appdata_bytes": b["appdata_bytes"],
                "stream_bytes": b["stream_bytes"],
                "decrypted_conns": b["decrypted_conns"],
                "plain_msgs": b["plain_msgs"],
                "alpn": dict(b["alpn"]),
                "ja3_ish_top": b["ja3_ish"].most_common(2),
                "game_like": any(
                    x in host
                    for x in (
                        "lilith",
                        "afk",
                        "game",
                    )
                ),
                "sdk_like": any(
                    x in host
                    for x in (
                        "crashsight",
                        "adjust",
                        "appsflyer",
                        "facebook",
                        "google",
                        "firebase",
                        "unity",
                        "applovin",
                    )
                ),
            }
        )

    all_pb: list[str] = []
    all_str: list[str] = []
    http_reqs: list[dict] = []
    for a in annotated:
        for s in a.get("protobuf_strings") or []:
            if s not in all_pb:
                all_pb.append(s)
        for s in a.get("all_strings") or []:
            if s not in all_str:
                all_str.append(s)
        h1 = a.get("http1") or {}
        for r in h1.get("requests") or []:
            http_reqs.append({**r, "sni": a.get("sni")})

    decrypted = [a for a in annotated if a.get("decrypt") and a["decrypt"].get("status") == "ok"]
    sealed = [a for a in annotated if not (a.get("decrypt") and a["decrypt"].get("status") == "ok")]

    return {
        "file": str(path),
        "keylog": str(keylog) if keylog else None,
        "connections": len(annotated),
        "decrypted_connections": len(decrypted),
        "sealed_connections": len(sealed),
        "sni_table": sni_table,
        "http_requests": http_reqs[:40],
        "protobuf_strings": all_pb[:120],
        "strings": all_str[:160],
        "sealed_game_hosts": [
            r for r in sni_table if r.get("game_like") and r["decrypted_conns"] == 0
        ],
        "open_hosts": [r for r in sni_table if r["decrypted_conns"] > 0],
        "connections_detail": annotated,
    }


def format_mine_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("=== GAME MINE REPORT ===")
    lines.append(f"file: {report.get('file')}")
    lines.append(f"keylog: {report.get('keylog')}")
    lines.append(
        f"connections: {report.get('connections')} "
        f"(decrypted={report.get('decrypted_connections')} "
        f"sealed={report.get('sealed_connections')})"
    )
    lines.append("")
    lines.append("--- SNI / byte economy ---")
    lines.append(
        f"{'SNI':48} {'conns':>5} {'appdata':>10} {'dec':>4} {'plain':>5}  tags"
    )
    for r in report.get("sni_table") or []:
        tags = []
        if r.get("game_like"):
            tags.append("GAME")
        if r.get("sdk_like"):
            tags.append("SDK")
        if r["decrypted_conns"]:
            tags.append("OPEN")
        else:
            tags.append("SEALED")
        lines.append(
            f"{r['sni'][:48]:48} {r['conns']:5d} {r['appdata_bytes']:10d} "
            f"{r['decrypted_conns']:4d} {r['plain_msgs']:5d}  {','.join(tags)}"
        )

    lines.append("")
    lines.append("--- OPEN (decrypted) hosts ---")
    for r in report.get("open_hosts") or []:
        lines.append(
            f"  {r['sni']}: conns={r['conns']} plain_msgs={r['plain_msgs']} alpn={r['alpn']}"
        )

    lines.append("")
    lines.append("--- SEALED game-like hosts (pinning wall) ---")
    for r in report.get("sealed_game_hosts") or []:
        lines.append(
            f"  {r['sni']}: conns={r['conns']} appdata_bytes={r['appdata_bytes']} "
            f"ja3={r.get('ja3_ish_top')}"
        )
    if not report.get("sealed_game_hosts"):
        lines.append("  (none tagged — check SNI table for lilith*)")

    lines.append("")
    lines.append("--- HTTP/1 requests (decrypted) ---")
    for r in report.get("http_requests") or []:
        lines.append(
            f"  {r.get('method')} {r.get('path')} host={r.get('host')} sni={r.get('sni')}"
        )
    if not report.get("http_requests"):
        lines.append("  (none)")

    lines.append("")
    lines.append("--- Protobuf / embedded strings (decrypted) ---")
    for s in (report.get("protobuf_strings") or [])[:80]:
        lines.append(f"  · {s}")
    if not report.get("protobuf_strings"):
        lines.append("  (none)")

    lines.append("")
    lines.append("--- All printable strings (decrypted) ---")
    for s in (report.get("strings") or [])[:100]:
        lines.append(f"  · {s}")

    lines.append("")
    lines.append("--- Per-connection (top by appdata) ---")
    detail = sorted(
        report.get("connections_detail") or [],
        key=lambda a: -a.get("appdata_bytes", 0),
    )[:24]
    for a in detail:
        sni = ",".join(a.get("sni") or ["?"])[:40]
        dec = a.get("decrypt") or {}
        st = dec.get("status", "-")
        lines.append(
            f"  {a['sport']}→{a['dport']} sni={sni:40} app={a['appdata_bytes']:7d} "
            f"dec={st} plain={dec.get('plain_msgs', '-')}"
        )
    lines.append("")
    lines.append("=== END ===")
    return "\n".join(lines)
