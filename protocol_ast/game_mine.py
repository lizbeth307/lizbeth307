"""Deep offline mine of a MITM/pcap dump — per-SNI, glued sessions, sdk_session."""

from __future__ import annotations

import hashlib
import json
import re
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

PRINTABLE_RE = re.compile(rb"[\x20-\x7e]{4,}")

def _ja3_ish(ch: dict) -> str:
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


def _protobuf_strings(data: bytes, *, limit: int = 64) -> list[str]:
    if not data:
        return []
    try:
        from .binary_peel import parse_protobuf_fields
    except Exception:
        return _strings(data, limit=limit)
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
        if len(found) >= limit:
            break
    for s in _strings(data, limit=limit):
        if s not in found:
            found.append(s)
        if len(found) >= limit:
            break
    return found[:limit]


def _try_gunzip(data: bytes) -> bytes | None:
    if not data.startswith(b"\x1f\x8b"):
        return None
    try:
        return zlib.decompress(data, 16 + zlib.MAX_WBITS)
    except Exception:
        return None


def _expand_plain(plains: list[bytes]) -> list[bytes]:
    out: list[bytes] = []
    for p in plains:
        gz = _try_gunzip(p)
        out.append(gz if gz is not None else p)
    return out


def extract_tcp_connections(path: Path) -> list[dict[str, Any]]:
    import analyze_pcap as ap

    tcp_segs: dict[tuple[int, int], list[tuple[int, bytes]]] = defaultdict(list)
    for link, frame in ap.iter_pcap(path):
        p = ap._extract(frame, link)
        if not p:
            continue
        proto, sport, dport, payload, seq = p
        if proto != "tcp" or seq is None or len(payload) < 1:
            continue
        if 443 not in (sport, dport) and sport > 1024 and dport > 1024:
            continue
        tcp_segs[(sport, dport)].append((seq, payload))

    conns: list[dict[str, Any]] = []
    for (sport, dport), segs in tcp_segs.items():
        segs = sorted(segs, key=lambda x: x[0])
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


def _annotate_leg(conn: dict[str, Any], secrets=None) -> dict[str, Any]:
    from .tls_handshake import parse_client_hello
    from .tls_keylog import decrypt_tls_records, flatten_tls_records

    records = conn["records"]
    flat = flatten_tls_records(records)
    appdata = [r for r in flat if len(r) >= 5 and r[0] == 0x17]
    app_bytes = sum(max(0, len(r) - 5) for r in appdata)

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
        "plains": [],
    }

    if secrets is not None and appdata:
        res = decrypt_tls_records(flat, secrets)
        if res and res.decrypted:
            plains = _expand_plain(list(res.decrypted))
            out["decrypt"] = {
                "status": "ok",
                "tls_version": res.tls_version,
                "plain_msgs": len(plains),
                "client_random": (res.client_random or "")[:16],
                "failed_records": res.failed,
            }
            out["plains"] = plains
        else:
            reason = (res.diagnostics or {}).get("reason") if res else "no_result"
            out["decrypt"] = {
                "status": reason or "failed",
                "overlap": (res.diagnostics or {}).get("overlap") if res else 0,
            }
    return out


def _parse_http_messages(plains: list[bytes]) -> list[dict[str, Any]]:
    """Split decrypted plaintext blobs into HTTP/1 request/response messages."""
    msgs: list[dict[str, Any]] = []
    pending_enc: str | None = None
    for raw in plains:
        if not raw:
            continue
        if pending_enc is not None or raw.startswith(b"\x1f\x8b"):
            enc = pending_enc
            pending_enc = None
            body, how = raw, "identity"
            if raw.startswith(b"\x1f\x8b") or (enc and "gzip" in enc):
                gz = _try_gunzip(raw)
                if gz is not None:
                    body, how = gz, "gzip"
            if msgs and msgs[-1].get("body") in (None, b""):
                msgs[-1]["body"] = body
                msgs[-1]["body_encoding"] = how
            else:
                msgs.append({"kind": "body", "body": body, "body_encoding": how})
            continue

        sep = raw.find(b"\r\n\r\n")
        if sep < 0:
            head_blob, body = raw, b""
        else:
            head_blob, body = raw[:sep], raw[sep + 4 :]
        lines = head_blob.split(b"\r\n")
        if not lines:
            continue
        try:
            start = lines[0].decode("ascii", errors="ignore")
        except Exception:
            continue
        headers: dict[str, str] = {}
        for ln in lines[1:40]:
            if b":" not in ln:
                continue
            k, v = ln.split(b":", 1)
            headers[k.strip().decode("ascii", errors="ignore").lower()] = v.strip().decode(
                "utf-8", errors="replace"
            )

        kind = None
        method = path = status = None
        for meth in ("GET", "POST", "HEAD", "PUT", "DELETE", "OPTIONS", "PATCH", "CONNECT"):
            if start.startswith(meth + " "):
                kind = "request"
                method = meth
                bits = start.split()
                path = bits[1] if len(bits) > 1 else ""
                break
        if kind is None and start.startswith("HTTP/1."):
            kind = "response"
            try:
                status = int(start.split()[1])
            except Exception:
                status = None

        if kind is None:
            continue

        enc = headers.get("content-encoding")
        if body:
            plain = body
            how = "identity"
            if body.startswith(b"\x1f\x8b") or (enc and "gzip" in enc.lower()):
                gz = _try_gunzip(body)
                if gz is not None:
                    plain, how = gz, "gzip"
        else:
            plain, how = b"", "identity"
            if headers.get("content-length", "0") not in ("0", ""):
                pending_enc = enc

        msgs.append(
            {
                "kind": kind,
                "method": method,
                "path": path,
                "status": status,
                "host": headers.get("host", ""),
                "content_type": headers.get("content-type", ""),
                "headers": headers,
                "body": plain,
                "body_encoding": how,
                "start_line": start[:200],
            }
        )
    return msgs


def _body_as_data(body: bytes, content_type: str = "") -> Any:
    if not body:
        return None
    text = body.decode("utf-8", errors="replace")
    ct = (content_type or "").lower()
    if "json" in ct or text[:1] in "{[":
        try:
            return json.loads(text)
        except Exception:
            pass
    if "x-www-form-urlencoded" in ct or (
        "=" in text[:80] and "&" in text[:200] and text[:1] not in "{[<"
    ):
        q = parse_qs(text, keep_blank_values=True)
        return {k: (v[0] if len(v) == 1 else v) for k, v in q.items()}
    if len(text) <= 400 and sum(1 for c in text[:80] if 32 <= ord(c) < 127) >= 60:
        return text[:400]
    return {"_binary_len": len(body), "_hex_head": body[:32].hex()}


def glue_http_exchanges(plains: list[bytes]) -> list[dict[str, Any]]:
    """
    Pair HTTP/1 requests with responses.

    Supports pipelining (login+heartbeat requests, then both 200s) by matching
    the i-th request to the i-th response, not only immediate neighbors.
    """
    msgs = _parse_http_messages(plains)
    reqs = [m for m in msgs if m.get("kind") == "request"]
    resps = [m for m in msgs if m.get("kind") == "response"]

    # Also try sequential neighbor pairing when counts mismatch badly
    exchanges: list[dict[str, Any]] = []
    if reqs and resps and len(resps) >= len(reqs):
        for i, req in enumerate(reqs):
            resp = resps[i]
            exchanges.append(
                {
                    "method": req.get("method"),
                    "path": req.get("path"),
                    "host": req.get("host"),
                    "content_type": req.get("content_type"),
                    "request": _body_as_data(
                        req.get("body") or b"", req.get("content_type") or ""
                    ),
                    "status": resp.get("status"),
                    "response": _body_as_data(
                        resp.get("body") or b"", resp.get("content_type") or ""
                    ),
                }
            )
        for resp in resps[len(reqs) :]:
            exchanges.append(
                {
                    "method": None,
                    "path": None,
                    "host": resp.get("host"),
                    "content_type": resp.get("content_type"),
                    "request": None,
                    "status": resp.get("status"),
                    "response": _body_as_data(
                        resp.get("body") or b"", resp.get("content_type") or ""
                    ),
                    "orphan_response": True,
                }
            )
        return exchanges

    # Fallback: walk in order (non-pipelined)
    i = 0
    while i < len(msgs):
        m = msgs[i]
        if m["kind"] == "request":
            ex: dict[str, Any] = {
                "method": m.get("method"),
                "path": m.get("path"),
                "host": m.get("host"),
                "content_type": m.get("content_type"),
                "request": _body_as_data(m.get("body") or b"", m.get("content_type") or ""),
                "status": None,
                "response": None,
            }
            if i + 1 < len(msgs) and msgs[i + 1]["kind"] == "response":
                resp = msgs[i + 1]
                ex["status"] = resp.get("status")
                ex["response"] = _body_as_data(
                    resp.get("body") or b"", resp.get("content_type") or ""
                )
                i += 2
            else:
                i += 1
            exchanges.append(ex)
        elif m["kind"] == "response":
            exchanges.append(
                {
                    "method": None,
                    "path": None,
                    "host": m.get("host"),
                    "content_type": m.get("content_type"),
                    "request": None,
                    "status": m.get("status"),
                    "response": _body_as_data(
                        m.get("body") or b"", m.get("content_type") or ""
                    ),
                    "orphan_response": True,
                }
            )
            i += 1
        else:
            i += 1
    return exchanges


def _looks_like_login_response(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    data = obj.get("data") if isinstance(obj.get("data"), dict) else obj
    if not isinstance(data, dict):
        return False
    return "app_uid" in data and ("app_token" in data or "access_token" in data)


def _looks_like_heartbeat_response(obj: Any) -> bool:
    if not isinstance(obj, dict):
        return False
    data = obj.get("data") if isinstance(obj.get("data"), dict) else obj
    if not isinstance(data, dict):
        return False
    return "heartbeat_interval" in data or "online_limit" in data or (
        "svr_time" in data and "can_play" in data
    )

def merge_bidirectional(legs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Glue TCP legs that share a port pair (client↔server)."""
    buckets: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for leg in legs:
        key = tuple(sorted((leg["sport"], leg["dport"])))
        buckets[key].append(leg)

    sessions: list[dict[str, Any]] = []
    for key, parts in buckets.items():
        sni: list[str] = []
        alpn: list[str] = []
        ja3: list[str] = []
        appdata_bytes = 0
        stream_bytes = 0
        plain_msgs = 0
        dec_ok = False
        tls_ver = None
        client_randoms: list[str] = []
        directions = []
        c2s: list[bytes] = []
        s2c: list[bytes] = []
        for p in parts:
            directions.append(f"{p['sport']}→{p['dport']}")
            sni.extend(p.get("sni") or [])
            alpn.extend(p.get("alpn") or [])
            ja3.extend([j for j in (p.get("ja3_ish") or []) if j])
            appdata_bytes += p.get("appdata_bytes") or 0
            stream_bytes += p.get("stream_bytes") or 0
            client_randoms.extend(p.get("client_randoms") or [])
            if p.get("decrypt") and p["decrypt"].get("status") == "ok":
                dec_ok = True
                tls_ver = p["decrypt"].get("tls_version") or tls_ver
                plain_msgs += p["decrypt"].get("plain_msgs") or 0
            blob = list(p.get("plains") or [])
            # Client→server: has SNI / ClientHello or dport==443
            if p.get("sni") or p.get("client_hellos") or p["dport"] == 443:
                c2s.extend(blob)
            else:
                s2c.extend(blob)
        plains = c2s + s2c

        exchanges = glue_http_exchanges(plains) if plains else []
        all_str: list[str] = []
        pb_str: list[str] = []
        for b in plains:
            for s in _strings(b, limit=30):
                if s not in all_str:
                    all_str.append(s)
            for s in _protobuf_strings(b, limit=20):
                if s not in pb_str:
                    pb_str.append(s)

        sessions.append(
            {
                "pair": list(key),
                "directions": directions,
                "legs": len(parts),
                "sni": sorted(set(sni)),
                "alpn": sorted(set(alpn)),
                "ja3_ish": list(dict.fromkeys(ja3))[:3],
                "stream_bytes": stream_bytes,
                "appdata_bytes": appdata_bytes,
                "decrypt": {
                    "status": "ok" if dec_ok else "sealed",
                    "tls_version": tls_ver,
                    "plain_msgs": plain_msgs,
                },
                "client_randoms": list(dict.fromkeys(client_randoms))[:4],
                "exchanges": exchanges,
                "all_strings": all_str[:60],
                "protobuf_strings": pb_str[:40],
            }
        )
    # sort heaviest first
    sessions.sort(key=lambda s: -s.get("appdata_bytes", 0))
    return sessions


def build_sdk_session(sessions: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract Lilith SDK login/heartbeat exchanges (full secrets kept)."""
    sdk: dict[str, Any] = {
        "endpoints": [],
        "login": None,
        "heartbeat": None,
        "sls_token": None,
        "identity": {},
    }
    orphan_login_resp = None
    orphan_hb_resp = None

    for sess in sessions:
        sni = ",".join(sess.get("sni") or []) or "(ip)"
        for ex in sess.get("exchanges") or []:
            path = ex.get("path") or ""
            host = ex.get("host") or sni
            resp = ex.get("response")
            if ex.get("orphan_response") or not path:
                if orphan_login_resp is None and _looks_like_login_response(resp):
                    orphan_login_resp = {"status": ex.get("status"), "response": resp, "host": host}
                if orphan_hb_resp is None and _looks_like_heartbeat_response(resp):
                    orphan_hb_resp = {"status": ex.get("status"), "response": resp, "host": host}

            entry = {
                "host": host,
                "sni": sess.get("sni"),
                "method": ex.get("method"),
                "path": path,
                "status": ex.get("status"),
            }
            if any(
                x in path
                for x in (
                    "/v2/api/sdk/",
                    "/api/sdk/",
                    "/api/forum/",
                    "/api/v1/public/",
                )
            ) or "lilith" in host or host.replace(".", "").startswith("34"):
                sdk["endpoints"].append(entry)

            if path.endswith("/v2/api/sdk/login") or path.endswith("/sdk/login"):
                sdk["login"] = {
                    "request": ex.get("request"),
                    "status": ex.get("status"),
                    "response": resp,
                    "host": host,
                }
            elif "heart_beat" in path:
                sdk["heartbeat"] = {
                    "request": ex.get("request"),
                    "status": ex.get("status"),
                    "response": resp,
                    "host": host,
                }
            elif "sls/token" in path:
                sdk["sls_token"] = {
                    "request": ex.get("request"),
                    "status": ex.get("status"),
                    "response": resp,
                    "host": host,
                }

    # Attach pipelined/orphan responses that failed neighbor pairing
    if sdk.get("login") and not sdk["login"].get("response") and orphan_login_resp:
        sdk["login"]["response"] = orphan_login_resp.get("response")
        sdk["login"]["status"] = orphan_login_resp.get("status") or sdk["login"].get("status")
    if sdk.get("heartbeat") and not sdk["heartbeat"].get("response") and orphan_hb_resp:
        sdk["heartbeat"]["response"] = orphan_hb_resp.get("response")
        sdk["heartbeat"]["status"] = orphan_hb_resp.get("status") or sdk["heartbeat"].get("status")

    # If login response was wrongly glued onto heartbeat, swap by shape
    lg = sdk.get("login") or {}
    hb = sdk.get("heartbeat") or {}
    if lg.get("request") and _looks_like_heartbeat_response(lg.get("response")) and _looks_like_login_response(
        hb.get("response")
    ):
        lg["response"], hb["response"] = hb.get("response"), lg.get("response")
        lg["status"], hb["status"] = hb.get("status"), lg.get("status")
    if lg.get("request") and not lg.get("response") and _looks_like_login_response(hb.get("response")):
        # heartbeat carried login body; look for true hb in orphans
        lg["response"] = hb.get("response")
        lg["status"] = hb.get("status")
        if orphan_hb_resp:
            hb["response"] = orphan_hb_resp.get("response")
            hb["status"] = orphan_hb_resp.get("status")
        elif _looks_like_login_response(hb.get("response")):
            hb["response"] = None

    req = lg.get("request") if isinstance(lg.get("request"), dict) else {}
    resp = lg.get("response") if isinstance(lg.get("response"), dict) else {}
    data = resp.get("data") if isinstance(resp, dict) else None
    if isinstance(data, dict):
        sdk["identity"] = {
            "app_uid": data.get("app_uid") or req.get("player_id") or req.get("app_uid"),
            "uid": data.get("uid"),
            "gm_openid": data.get("gm_openid"),
            "plat_openid": data.get("plat_openid"),
            "app_token": data.get("app_token") or req.get("pass") or req.get("app_token"),
            "access_token": data.get("access_token"),
            "app_token_expire_at": data.get("app_token_expire_at"),
            "bindings": data.get("bindings"),
            "lilith_bindings": data.get("lilith_bindings"),
            "identity": data.get("identity"),
            "is_reg": data.get("is_reg"),
            "ip": data.get("ip"),
            "game_id": req.get("game_id"),
            "app_id": req.get("app_id"),
            "app_version": req.get("app_version"),
            "channel_id": req.get("channel_id"),
            "env_id": req.get("env_id"),
            "install_id": req.get("install_id"),
            "sdk_version": req.get("sdk_version"),
            "sdk_session_id": req.get("sdk_session_id"),
            "android_id": req.get("android_id"),
            "google_aid": req.get("google_aid"),
        }
    elif req:
        sdk["identity"] = {
            "app_uid": req.get("player_id") or req.get("app_uid"),
            "app_token": req.get("pass") or req.get("app_token"),
            "game_id": req.get("game_id"),
            "app_id": req.get("app_id"),
            "app_version": req.get("app_version"),
            "channel_id": req.get("channel_id"),
            "env_id": req.get("env_id"),
            "install_id": req.get("install_id"),
            "sdk_version": req.get("sdk_version"),
            "sdk_session_id": req.get("sdk_session_id"),
            "android_id": req.get("android_id"),
            "google_aid": req.get("google_aid"),
        }
    return sdk


def mine_pcap(path: Path, keylog: Path | None = None) -> dict[str, Any]:
    secrets = None
    if keylog and keylog.exists():
        from .tls_keylog import parse_keylog

        secrets = parse_keylog(keylog)

    legs = [_annotate_leg(c, secrets) for c in extract_tcp_connections(path)]
    sessions = merge_bidirectional(legs)
    sdk_session = build_sdk_session(sessions)

    by_sni: dict[str, dict[str, Any]] = {}
    for s in sessions:
        hosts = s["sni"] or ["(no-sni)"]
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
                    "exchanges": 0,
                },
            )
            bucket["conns"] += 1
            bucket["appdata_bytes"] += s["appdata_bytes"]
            bucket["stream_bytes"] += s["stream_bytes"]
            bucket["exchanges"] += len(s.get("exchanges") or [])
            for x in s["alpn"]:
                bucket["alpn"][x] += 1
            for j in s["ja3_ish"]:
                bucket["ja3_ish"][j] += 1
            if s.get("decrypt", {}).get("status") == "ok":
                bucket["decrypted_conns"] += 1
                bucket["plain_msgs"] += s["decrypt"].get("plain_msgs") or 0

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
                "exchanges": b["exchanges"],
                "alpn": dict(b["alpn"]),
                "ja3_ish_top": b["ja3_ish"].most_common(2),
                "game_like": any(x in host for x in ("lilith", "afk", "game")),
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
                        "aliyuncs",
                    )
                ),
            }
        )

    http_reqs = []
    all_pb: list[str] = []
    all_str: list[str] = []
    for s in sessions:
        for ex in s.get("exchanges") or []:
            if ex.get("method"):
                http_reqs.append(
                    {
                        "method": ex.get("method"),
                        "path": ex.get("path"),
                        "host": ex.get("host"),
                        "status": ex.get("status"),
                        "sni": s.get("sni"),
                        "has_response": ex.get("response") is not None,
                    }
                )
        for x in s.get("protobuf_strings") or []:
            if x not in all_pb:
                all_pb.append(x)
        for x in s.get("all_strings") or []:
            if x not in all_str:
                all_str.append(x)

    decrypted = [s for s in sessions if s.get("decrypt", {}).get("status") == "ok"]
    sealed = [s for s in sessions if s.get("decrypt", {}).get("status") != "ok"]

    # Slim sessions for JSON (no raw plains)
    slim_sessions = []
    for s in sessions:
        slim_sessions.append({k: v for k, v in s.items()})

    return {
        "file": str(path),
        "keylog": str(keylog) if keylog else None,
        "connections": len(sessions),
        "legs": len(legs),
        "decrypted_connections": len(decrypted),
        "sealed_connections": len(sealed),
        "sni_table": sni_table,
        "http_requests": http_reqs[:60],
        "protobuf_strings": all_pb[:120],
        "strings": all_str[:160],
        "sealed_game_hosts": [
            r for r in sni_table if r.get("game_like") and r["decrypted_conns"] == 0
        ],
        "open_hosts": [r for r in sni_table if r["decrypted_conns"] > 0],
        "sessions": slim_sessions,
        "sdk_session": sdk_session,
    }


def format_mine_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("=== GAME MINE REPORT ===")
    lines.append(f"file: {report.get('file')}")
    lines.append(f"keylog: {report.get('keylog')}")
    lines.append(
        f"sessions: {report.get('connections')} "
        f"(legs={report.get('legs')} decrypted={report.get('decrypted_connections')} "
        f"sealed={report.get('sealed_connections')})"
    )
    lines.append("")
    lines.append("--- SNI / byte economy ---")
    lines.append(
        f"{'SNI':48} {'sess':>4} {'appdata':>10} {'dec':>3} {'ex':>3}  tags"
    )
    for r in report.get("sni_table") or []:
        tags = []
        if r.get("game_like"):
            tags.append("GAME")
        if r.get("sdk_like"):
            tags.append("SDK")
        tags.append("OPEN" if r["decrypted_conns"] else "SEALED")
        lines.append(
            f"{r['sni'][:48]:48} {r['conns']:4d} {r['appdata_bytes']:10d} "
            f"{r['decrypted_conns']:3d} {r.get('exchanges', 0):3d}  {','.join(tags)}"
        )

    sdk = report.get("sdk_session") or {}
    lines.append("")
    lines.append("--- SDK SESSION ---")
    if sdk.get("identity"):
        lines.append(f"  identity: {json.dumps(sdk['identity'], ensure_ascii=False)[:300]}")
    if sdk.get("login"):
        lg = sdk["login"]
        lines.append(
            f"  login: host={lg.get('host')} status={lg.get('status')} "
            f"req_keys={list((lg.get('request') or {}).keys())[:12] if isinstance(lg.get('request'), dict) else None}"
        )
        resp = lg.get("response")
        if isinstance(resp, dict):
            data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
            lines.append(
                f"  login.data: app_uid={data.get('app_uid')} uid={data.get('uid')} "
                f"expire={data.get('app_token_expire_at')} bindings={data.get('bindings')}"
            )
    if sdk.get("heartbeat"):
        hb = sdk["heartbeat"]
        lines.append(f"  heartbeat: status={hb.get('status')} host={hb.get('host')}")
        resp = hb.get("response")
        if isinstance(resp, dict) and isinstance(resp.get("data"), dict):
            d = resp["data"]
            lines.append(
                f"  heartbeat.data: can_play={d.get('can_play')} "
                f"interval={d.get('heartbeat_interval')} limit={d.get('online_limit')}"
            )
    if sdk.get("sls_token"):
        lines.append(f"  sls_token: status={sdk['sls_token'].get('status')}")
    for ep in (sdk.get("endpoints") or [])[:12]:
        lines.append(
            f"  ep: {ep.get('method')} {ep.get('path')} host={ep.get('host')} status={ep.get('status')}"
        )

    lines.append("")
    lines.append("--- HTTP exchanges (glued) ---")
    n = 0
    for s in report.get("sessions") or []:
        for ex in s.get("exchanges") or []:
            if not ex.get("method") and not ex.get("status"):
                continue
            flag = "OK" if ex.get("response") is not None or ex.get("status") else "req-only"
            lines.append(
                f"  [{flag}] {ex.get('method') or '-':4} {ex.get('status') or '-':>3} "
                f"{ex.get('path')} host={ex.get('host')} sni={s.get('sni')}"
            )
            n += 1
            if n >= 40:
                break
        if n >= 40:
            break
    if n == 0:
        lines.append("  (none)")

    lines.append("")
    lines.append("--- SEALED game-like hosts ---")
    for r in report.get("sealed_game_hosts") or []:
        lines.append(
            f"  {r['sni']}: sess={r['conns']} appdata={r['appdata_bytes']} ja3={r.get('ja3_ish_top')}"
        )
    if not report.get("sealed_game_hosts"):
        lines.append("  (none)")

    lines.append("")
    lines.append("=== END ===")
    return "\n".join(lines)
