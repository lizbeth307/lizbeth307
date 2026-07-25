"""Living signal — self-propagating blind protocol discovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .align import discover_format
from .cluster import best_cluster_offset, discover_clustered_formats
from .deep_decode import deep_analyze_flow
from .pipeline import discover_and_parse
from .sequitur import Sequitur, tokenize_message
from .serde import format_to_dict
from .splitters import (
    discover_splitter,
    peel_tls_appdata_records,
    peel_tls_handshake_records,
    split_tls_handshake_bodies,
)


from .tls_handshake import parse_client_hello


HANDSHAKE_TYPES = {1, 2, 4, 8, 11, 12, 13, 14, 15, 16, 20}


def entropy_label(messages: list[bytes]) -> str:
    if not messages:
        return "empty"
    # Handshake bodies look high-entropy due to client_random, but are structured
    hs = sum(1 for m in messages if m and m[0] in HANDSHAKE_TYPES)
    if hs >= max(1, len(messages) // 2):
        return "structured"
    ratio = len(set(b for p in messages[:10] for b in p[:16])) / max(
        1, min(16, min(len(p) for p in messages))
    )
    return "high" if ratio > 0.85 else "structured"


def _handshake_deep(messages: list[bytes]) -> dict | None:
    hellos = []
    types: dict[str, int] = {}
    for m in messages:
        if not m:
            continue
        name = {
            1: "ClientHello",
            2: "ServerHello",
            4: "NewSessionTicket",
            8: "EncryptedExtensions",
            11: "Certificate",
            12: "ServerKeyExchange",
            14: "ServerHelloDone",
            15: "CertificateVerify",
            16: "ClientKeyExchange",
            20: "Finished",
        }.get(m[0], f"type{m[0]}")
        types[name] = types.get(name, 0) + 1
        if m[0] == 1:
            detail = parse_client_hello(m)
            if detail:
                hellos.append(detail)
    if not types:
        return None
    sni = []
    alpn = []
    for h in hellos:
        sni.extend(h.get("sni", []))
        alpn.extend(h.get("alpn", []))
    return {
        "kind": "tls_handshake",
        "types": types,
        "client_hellos": len(hellos),
        "sni_hosts": sorted(set(sni))[:20],
        "alpn": sorted(set(alpn))[:10],
    }


@dataclass
class Signal:
    """Byte stream that discovers its own structure and propagates inward."""

    label: str
    messages: list[bytes]
    depth: int = 0
    parent: Signal | None = None
    flow: str = ""
    format: dict = field(default_factory=dict)
    parse_success: float = 0.0
    entropy: str = "unknown"
    splitter: str | None = None
    confidence: float = 0.0
    sequitur: str = ""
    sequitur_rules: int = 0
    opaque: bool = False
    clusters: dict | None = None
    deep: dict | None = None
    decrypt: dict | None = None
    keylog_path: str | None = None
    children: list[Signal] = field(default_factory=list)

    def analyze(self) -> Signal:
        if not self.messages:
            self.entropy = "empty"
            return self
        fmt = discover_format(self.messages)
        result = discover_and_parse(self.messages)
        self.format = format_to_dict(fmt)
        self.parse_success = round(result.success_rate, 3)
        self.entropy = entropy_label(self.messages)
        self.confidence = self.parse_success * (0.5 if self.entropy == "high" else 1.0)

        seq = Sequitur()
        for msg in self.messages[:16]:
            seq.feed_many(tokenize_message(msg[:48]) + ["|"])
        self.sequitur = seq.summary()
        self.sequitur_rules = max(0, len(seq.rules) - 1)

        if self.depth == 0 and self.flow:
            self.deep = deep_analyze_flow(self.flow, self.messages)
            cl_off = best_cluster_offset(self.messages)
            if cl_off is not None:
                self.clusters = discover_clustered_formats(self.messages, cl_off)
        elif "handshake" in self.label.lower() or (
            self.messages and self.messages[0] and self.messages[0][0] in HANDSHAKE_TYPES
        ):
            self.deep = _handshake_deep(self.messages)
        return self

    def _spawn(self, label_suffix: str, messages: list[bytes]) -> Signal:
        child = Signal(
            label=f"{self.label}/{label_suffix}",
            messages=messages,
            depth=self.depth + 1,
            parent=self,
            flow=self.flow,
            keylog_path=self.keylog_path,
        )
        return child

    def _try_keylog_decrypt(self, records: list[bytes], *, max_depth: int) -> Signal | None:
        if not self.keylog_path:
            return None
        from .tls_keylog import decrypt_tls_records, keylog_summary, parse_keylog

        path = Path(self.keylog_path).expanduser()
        if not path.exists():
            return None
        secrets = parse_keylog(path)
        appdata = peel_tls_appdata_records(records)
        result = decrypt_tls_records(records, secrets)
        if not result or not result.decrypted:
            diag = (result.diagnostics if result else {}) or {}
            self.decrypt = {
                "status": diag.get("reason", "no_match"),
                "keylog": keylog_summary(secrets),
                "appdata_records": len(appdata),
                "diag": diag,
            }
            return None
        self.decrypt = {
            "status": "ok",
            "tls_version": result.tls_version,
            "client_random": result.client_random[:16] + "…",
            "secrets": result.secrets_matched,
            "decrypted": len(result.decrypted),
            "failed": result.failed,
            "keylog": keylog_summary(secrets),
            "diag": result.diagnostics,
        }
        child = self._spawn("decrypted", result.decrypted)
        child.propagate(max_depth=max_depth)
        return child

    def _try_binary_peel(self) -> bool:
        """Attach protobuf/msgpack child when bodies look like binary APIs."""
        from .binary_peel import binary_peel

        bin_deep = binary_peel(self.messages)
        if not bin_deep:
            return False
        name = bin_deep["kind"]
        self.splitter = name
        self.deep = bin_deep
        self.entropy = "structured"
        child = self._spawn(name, self.messages)
        child.deep = bin_deep
        child.entropy = "structured"
        self.children.append(child)
        return True

    def _peel_http2_data_leaf(self) -> bool:
        """HTML/JSON title+schema even for a single DATA payload."""
        if not (self.deep and self.deep.get("kind") == "http2_data"):
            return False
        if not self.messages:
            return False
        from .body_peel import body_deep
        from .json_api import json_api_deep, looks_like_json_api

        charset = None
        for h in self.deep.get("headers") or []:
            ct = h.get("content-type") or ""
            if "charset=" in ct.lower():
                charset = ct.split("charset=", 1)[-1].split(";")[0].strip()
                break
        self.deep["content"] = body_deep(self.messages, charset=charset)
        if looks_like_json_api(self.messages):
            api = json_api_deep(self.messages, headers=self.deep.get("headers"))
            self.deep["json_api"] = api
            child = self._spawn("json_api", self.messages)
            child.deep = api
            child.entropy = "structured"
            self.children.append(child)
        self.entropy = "structured"
        return True

    def propagate(self, *, max_depth: int = 5) -> Signal:
        """Discover format, peel handshake, decrypt if keylog — until entropy wall."""
        self.analyze()

        # Single HTTP/2 DATA body still carries a full HTML/JSON document
        if self.depth > 0 and self._peel_http2_data_leaf():
            return self

        if self.depth >= max_depth or len(self.messages) < 2:
            return self

        # Handshake bodies are already peeled — do not re-split into tls_handshake/… forever
        if self.depth > 0 and (
            self.label.rstrip("/").endswith("tls_handshake")
            or (self.deep and self.deep.get("kind") == "tls_handshake")
        ):
            if not self.deep or self.deep.get("kind") != "tls_handshake":
                self.deep = _handshake_deep(self.messages)
            self.entropy = "structured"
            return self

        # Binary API bodies when not clearly HTTP — works for structured entropy too
        if self.depth > 0:
            from .body_peel import looks_like_app_body
            from .http2 import looks_like_http1, looks_like_http2

            if (
                not looks_like_http2(self.messages)
                and not looks_like_http1(self.messages)
                and not looks_like_app_body(self.messages)
                and self._try_binary_peel()
            ):
                return self

        # High-entropy layers: peel handshake / decrypt / HTTP/2 before wall
        if self.entropy == "high" and self.depth > 0:
            peeled = False
            from .body_peel import body_deep, looks_like_app_body
            from .http2 import (
                http1_deep,
                http2_data_deep,
                http2_deep,
                looks_like_http1,
                split_http2_frames,
            )

            h2 = split_http2_frames(self.messages)
            if h2:
                name, inner = h2
                self.splitter = name
                if name == "http2_data":
                    self.deep = http2_data_deep(inner, source_frames=self.messages)
                else:
                    self.deep = http2_deep(inner)
                self.entropy = "structured"
                child = self._spawn(name, inner)
                child.deep = dict(self.deep) if self.deep else None
                child.propagate(max_depth=max_depth)
                self.children.append(child)
                return self
            if looks_like_app_body(self.messages):
                from .json_api import json_api_deep, looks_like_json_api

                self.splitter = "app_body"
                self.deep = body_deep(self.messages)
                self.entropy = "structured"
                if looks_like_json_api(self.messages):
                    api = json_api_deep(self.messages)
                    self.deep["json_api"] = api
                    child = self._spawn("json_api", self.messages)
                    child.deep = api
                    child.entropy = "structured"
                    self.children.append(child)
                return self
            if looks_like_http1(self.messages):
                self.splitter = "http1"
                self.deep = http1_deep(self.messages)
                self.entropy = "structured"
                return self

            if self._try_binary_peel():
                return self

            hs = split_tls_handshake_bodies(self.messages)
            if hs:
                name, bodies = hs
                self.splitter = name
                child = self._spawn(name, bodies)
                child.propagate(max_depth=max_depth)
                self.children.append(child)
                peeled = True
            else:
                hs_recs = peel_tls_handshake_records(self.messages)
                bodies = [r[5:] for r in hs_recs if len(r) > 5]
                if len(bodies) >= 1:
                    self.splitter = "tls_handshake"
                    child = self._spawn("tls_handshake", bodies)
                    child.propagate(max_depth=max_depth)
                    self.children.append(child)
                    peeled = True

            dec = self._try_keylog_decrypt(self.messages, max_depth=max_depth)
            if dec:
                self.children.append(dec)
                peeled = True

            if not peeled:
                self.opaque = True
            return self

        split = discover_splitter(self.messages, depth=self.depth)
        if not split:
            if self._try_binary_peel():
                return self
            dec = self._try_keylog_decrypt(self.messages, max_depth=max_depth)
            if dec:
                self.children.append(dec)
            return self

        splitter_name, inner = split
        self.splitter = splitter_name
        if len(inner) < 2:
            return self

        child = self._spawn(splitter_name, inner)
        child.propagate(max_depth=max_depth)
        self.children.append(child)

        # After tls_record: peel Handshake BEFORE treating rest as opaque
        if splitter_name == "tls_record":
            hs_recs = peel_tls_handshake_records(inner)
            if len(hs_recs) >= 1:
                bodies = [r[5:] for r in hs_recs if len(r) > 5]
                if bodies:
                    hs_child = self._spawn("tls_handshake", bodies)
                    hs_child.propagate(max_depth=max_depth)
                    self.children.append(hs_child)
            dec = self._try_keylog_decrypt(inner, max_depth=max_depth)
            if dec:
                self.children.append(dec)
            return self

        if child.entropy == "high" and child.children:
            return self

        payload_frames: list[bytes] = []
        for fr in inner[:50]:
            if len(fr) <= 16:
                continue
            if splitter_name.startswith("length_"):
                fmt = discover_format(inner)
                off = fmt.length_field_offset or 0
                hdr = off + (4 if fmt.length_width == "u32" else 2)
                if len(fr) > hdr:
                    payload_frames.append(fr[hdr:])
            else:
                payload_frames.append(fr)

        if len(payload_frames) >= 2 and entropy_label(payload_frames) == "structured":
            sub = self._spawn("payload", payload_frames)
            sub.propagate(max_depth=max_depth)
            if sub.parse_success >= 0.5 or sub.children:
                self.children.append(sub)

        return self

    def path(self) -> str:
        parts = [self.label]
        node = self.parent
        while node:
            parts.append(node.label)
            node = node.parent
        return " → ".join(reversed(parts))

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "depth": self.depth,
            "messages": len(self.messages),
            "entropy": self.entropy,
            "opaque": self.opaque,
            "splitter": self.splitter,
            "format": self.format,
            "parse_success": self.parse_success,
            "confidence": round(self.confidence, 3),
            "sequitur_rules": self.sequitur_rules,
            "sequitur": self.sequitur,
            "clusters": self.clusters,
            "deep": self.deep,
            "decrypt": self.decrypt,
            "children": [c.to_dict() for c in self.children],
        }

    def format_notes(self) -> list[str]:
        notes = [
            f"[d{self.depth}] {self.label}: {len(self.messages)} msg, "
            f"parse={self.parse_success:.0%}, entropy={self.entropy}, "
            f"conf={self.confidence:.2f}"
        ]
        if self.opaque:
            notes.append("  wall: opaque (high entropy)")
        if self.splitter:
            notes.append(f"  splitter: {self.splitter}")
        if self.sequitur_rules:
            notes.append(f"  sequitur: {self.sequitur_rules} rules")
        if self.decrypt:
            d = self.decrypt
            if d.get("status") == "ok":
                notes.append(
                    f"  decrypt: TLS {d.get('tls_version')} → {d.get('decrypted')} plaintext "
                    f"({d.get('failed', 0)} failed)"
                )
            elif d.get("status") in ("no_match", "no_overlap", "decrypt_failed", "no_appdata_records"):
                kl = d.get("keylog") or {}
                diag = d.get("diag") or {}
                notes.append(
                    f"  decrypt: {d.get('status')} "
                    f"(keylog={kl.get('client_randoms', 0)} secrets, "
                    f"hellos={diag.get('client_hellos_in_pcap', '?')}, "
                    f"overlap={diag.get('overlap', '?')}, "
                    f"appdata={diag.get('appdata_records', d.get('appdata_records', 0))})"
                )
        if self.deep:
            kind = self.deep.get("kind")
            if kind == "tls":
                if self.deep.get("sni_hosts"):
                    notes.append(f"  SNI: {', '.join(self.deep['sni_hosts'][:6])}")
                if self.deep.get("alpn"):
                    notes.append(f"  ALPN: {', '.join(self.deep['alpn'][:4])}")
            if kind == "tls_handshake":
                if self.deep.get("types"):
                    notes.append(f"  handshake: {self.deep['types']}")
                if self.deep.get("sni_hosts"):
                    notes.append(f"  SNI: {', '.join(self.deep['sni_hosts'][:6])}")
                if self.deep.get("alpn"):
                    notes.append(f"  ALPN: {', '.join(self.deep['alpn'][:4])}")
            if kind == "http2":
                notes.append(
                    f"  HTTP/2: {self.deep.get('frames', {})} "
                    f"streams={self.deep.get('streams', 0)}"
                )
                for h in (self.deep.get("headers") or [])[:3]:
                    bits = [f"s{h.get('stream')}"]
                    for k in (":method", ":status", ":path", ":authority", "content-type", "content-encoding"):
                        if k in h:
                            bits.append(f"{k}={h[k]}")
                    notes.append("  hdr: " + " ".join(bits))
                if self.deep.get("data_preview"):
                    notes.append(f"  DATA: {self.deep['data_preview'][0][:80]}")
            if kind == "http2_data":
                notes.append(
                    f"  http2_data: {self.deep.get('payloads', 0)} payloads "
                    f"(html={self.deep.get('html', 0)} json={self.deep.get('json', 0)})"
                )
                for h in (self.deep.get("headers") or [])[:3]:
                    bits = [f"s{h.get('stream')}"]
                    for k in (":method", ":status", ":path", ":authority", "content-type", "content-encoding"):
                        if k in h:
                            bits.append(f"{k}={h[k]}")
                    notes.append("  hdr: " + " ".join(bits))
                for m in (self.deep.get("body_meta") or [])[:3]:
                    notes.append(
                        f"  meta: stream={m.get('stream')} "
                        f"{m.get('decompress')} {m.get('raw_len')}→{m.get('plain_len')}"
                    )
                for prev in (self.deep.get("preview") or [])[:2]:
                    notes.append(f"  body: {prev[:100]}")
            if kind == "body" or self.deep.get("content"):
                content = self.deep if kind == "body" else (self.deep.get("content") or {})
                if content:
                    notes.append(f"  content: types={content.get('types', {})}")
                    for t in (content.get("titles") or [])[:2]:
                        notes.append(f"  title: {t}")
                    if content.get("json_keys"):
                        notes.append(f"  json_keys: {', '.join(content['json_keys'][:10])}")
            if kind == "json_api" or self.deep.get("json_api"):
                api = self.deep if kind == "json_api" else (self.deep.get("json_api") or {})
                notes.append(
                    f"  json_api: {api.get('bodies', 0)} bodies, "
                    f"{api.get('field_count', 0)} fields"
                )
                if api.get("paths"):
                    notes.append(f"  api_paths: {', '.join(api['paths'][:6])}")
                if api.get("sample_keys"):
                    notes.append(f"  schema: {', '.join(api['sample_keys'][:10])}")
            if kind == "protobuf":
                notes.append(
                    f"  protobuf: {self.deep.get('field_count', 0)} fields "
                    f"cov={self.deep.get('avg_coverage', 0)}"
                )
                for f in (self.deep.get("schema") or [])[:8]:
                    notes.append(f"  pb_f{f.get('field')}: {f.get('wire')} ×{f.get('seen')}")
            if kind == "msgpack":
                notes.append(
                    f"  msgpack: parsed={self.deep.get('parsed', 0)} "
                    f"keys={self.deep.get('key_count', 0)}"
                )
                if self.deep.get("keys"):
                    notes.append(f"  mp_keys: {', '.join(self.deep['keys'][:10])}")
            if kind == "http1":
                notes.append(f"  HTTP/1: {self.deep.get('methods', {})}")
                if self.deep.get("hosts"):
                    notes.append(f"  Host: {', '.join(self.deep['hosts'][:6])}")
            if kind == "dns" and self.deep.get("domains"):
                notes.append(f"  DNS: {', '.join(self.deep['domains'][:6])}")
            if kind == "quic":
                notes.append(f"  QUIC: {self.deep.get('types', {})}")
        if self.clusters:
            notes.append(f"  clusters: {len(self.clusters)} opcodes")
        for ch in self.children:
            notes.extend(ch.format_notes())
        return notes


def propagate_flow(
    flow: str,
    messages: list[bytes],
    *,
    max_depth: int = 5,
    keylog: str | None = None,
) -> Signal:
    root = Signal(label=flow, messages=messages, flow=flow, depth=0, keylog_path=keylog)
    return root.propagate(max_depth=max_depth)
