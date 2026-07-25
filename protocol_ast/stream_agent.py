"""Streaming living-signal agent — incremental propagate over growing flows."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from .pcap_analyze import extract_flows
from .signal import Signal, propagate_flow


_NOTE_PRIORITY = (
    "title:",
    "hdr:",
    "json_api",
    "api_paths:",
    "schema:",
    "json_keys:",
    "content:",
    "HTTP/2:",
    "http2_data:",
    "meta:",
    "body:",
    "decrypt: TLS",
    "SNI:",
    "ALPN:",
    "protobuf:",
    "msgpack:",
    "DNS:",
)


def highlight_notes(notes: list[str], *, limit: int = 16) -> list[str]:
    """Prefer deep peel lines over sequitur/cluster noise; dedupe repeats."""
    scored: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    for i, n in enumerate(notes):
        s = n.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        rank = 50
        for p, key in enumerate(_NOTE_PRIORITY):
            if key in s:
                rank = p
                break
        if s.startswith("[d"):
            # keep one layer header per unique label tail
            rank = min(rank, 45)
        if "sequitur" in s or "clusters:" in s:
            rank = 90
        if "tls_handshake/tls_handshake" in s:
            rank = 95
        scored.append((rank, i, n if n.startswith("  ") or n.startswith("[") else f"  {s}"))
    scored.sort(key=lambda t: (t[0], t[1]))
    out = [t[2] for t in scored[:limit]]
    out.sort(key=lambda line: next((i for i, n in enumerate(notes) if n.strip() == line.strip()), 0))
    return out


_PATH_SCORE = {
    "json_api": 100,
    "http2_data": 95,
    "app_body": 90,
    "http2_frames": 85,
    "http2": 85,
    "body": 80,
    "protobuf": 75,
    "msgpack": 75,
    "decrypted": 70,
    "http1": 65,
    "tls_record": 20,
    "tls_handshake": 15,
}


def deepest_signal_path(sig: Signal) -> str:
    """Path to the most interesting peel (HTTP/2/body), not deepest handshake recurse."""

    def score(node: Signal) -> tuple[int, int]:
        tail = node.label.rsplit("/", 1)[-1]
        kind = (node.deep or {}).get("kind") or ""
        base = max(_PATH_SCORE.get(tail, 0), _PATH_SCORE.get(kind, 0))
        # bonus for title / headers
        deep = node.deep or {}
        content = deep.get("content") or deep
        if content.get("titles") or deep.get("titles"):
            base += 30
        if deep.get("headers") or deep.get("json_api"):
            base += 10
        return (base, node.depth)

    best = sig
    stack = [sig]
    while stack:
        node = stack.pop()
        if score(node) >= score(best):
            best = node
        stack.extend(node.children)
    return best.path()


@dataclass
class StreamEvent:
    ts: float
    flow: str
    messages: int
    path: str
    notes: list[str]
    signal: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "flow": self.flow,
            "messages": self.messages,
            "path": self.path,
            "notes": self.notes,
            "signal": self.signal,
        }


@dataclass
class StreamAgent:
    """
    Feed packets/payloads per flow; emit sparse Signal checkpoints
    (not every N on phone — full TLS decrypt is expensive).
    """

    every_n: int = 32
    max_depth: int = 5
    keylog: str | None = None
    min_messages: int = 2
    max_msgs: int = 48
    max_emits_per_flow: int = 3
    include_signal_dict: bool = False
    buffers: dict[str, list[bytes]] = field(default_factory=dict)
    last_emitted_at: dict[str, int] = field(default_factory=dict)
    emit_count: dict[str, int] = field(default_factory=dict)
    events: list[StreamEvent] = field(default_factory=list)

    def feed(self, flow: str, payload: bytes) -> StreamEvent | None:
        if not payload:
            return None
        buf = self.buffers.setdefault(flow, [])
        buf.append(payload)
        last = self.last_emitted_at.get(flow, 0)
        emitted = self.emit_count.get(flow, 0)
        # Reserve final emit for flush(); intermediate only if under budget
        if emitted >= self.max_emits_per_flow - 1:
            return None
        if len(buf) - last >= self.every_n and len(buf) >= self.min_messages:
            return self._emit(flow)
        return None

    def feed_many(self, flow: str, payloads: list[bytes]) -> list[StreamEvent]:
        out: list[StreamEvent] = []
        for p in payloads:
            ev = self.feed(flow, p)
            if ev:
                out.append(ev)
        return out

    def flush(self, flow: str | None = None) -> list[StreamEvent]:
        flows = [flow] if flow else list(self.buffers)
        out: list[StreamEvent] = []
        for f in flows:
            if f in self.buffers and len(self.buffers[f]) >= self.min_messages:
                if self.last_emitted_at.get(f, 0) < len(self.buffers[f]):
                    ev = self._emit(f, final=True)
                    if ev:
                        out.append(ev)
        return out

    def _sample(self, payloads: list[bytes], *, final: bool = False) -> list[bytes]:
        """
        Contiguous samples only — head+tail splice breaks TLS/HTTP2 sessions.

        Final+keylog: use full buffer (same as --signal; ~166 msgs is OK on phone).
        Intermediate: contiguous prefix capped by max_msgs.
        """
        n = len(payloads)
        if final and self.keylog:
            if n <= 220:
                return list(payloads)
            # very large: contiguous tail window (late sessions) + small head for hellos
            head = 24
            tail = 196
            return list(payloads[:head]) + list(payloads[-(tail):])
        if n <= self.max_msgs:
            return list(payloads)
        return list(payloads[: self.max_msgs])

    def _emit(self, flow: str, *, final: bool = False) -> StreamEvent | None:
        payloads = self.buffers.get(flow) or []
        if len(payloads) < self.min_messages:
            return None
        sample = self._sample(payloads, final=final)
        print(
            f"  … Signal {flow} msgs={len(payloads)} (using {len(sample)}"
            f"{', final' if final else ''})",
            flush=True,
            file=sys.stderr,
        )
        t0 = time.time()
        sig = propagate_flow(flow, sample, max_depth=self.max_depth, keylog=self.keylog)
        dt = time.time() - t0
        all_notes = sig.format_notes()
        ev = StreamEvent(
            ts=time.time(),
            flow=flow,
            messages=len(payloads),
            path=deepest_signal_path(sig),
            notes=highlight_notes(all_notes, limit=20),
            signal=sig.to_dict() if self.include_signal_dict else {
                "label": sig.label,
                "path": deepest_signal_path(sig),
                "elapsed_s": round(dt, 3),
                "sampled": len(sample),
                "final": final,
            },
        )
        self.last_emitted_at[flow] = len(payloads)
        self.emit_count[flow] = self.emit_count.get(flow, 0) + 1
        self.events.append(ev)
        print(f"  … done {flow} in {dt:.1f}s", flush=True, file=sys.stderr)
        return ev


def _select_flows(
    buckets: dict,
    *,
    flow_filter: str | None,
    max_flows: int,
) -> list[tuple[str, Any]]:
    items = sorted(buckets.items(), key=lambda x: -x[1].packet_count)
    if flow_filter:
        return [(l, b) for l, b in items if flow_filter.lower() in l.lower()]
    # Offline default: prefer TLS/HTTP service ports, then by size
    preferred = []
    rest = []
    for label, bucket in items:
        u = label.upper()
        if any(x in u for x in (":443", ":8443", ":80", ":8080", "TLS", "HTTP")):
            preferred.append((label, bucket))
        else:
            rest.append((label, bucket))
    ordered = preferred + rest
    return ordered[: max(1, max_flows)]


def analyze_pcap_streaming(
    pcap: str | Path,
    *,
    every_n: int = 32,
    max_depth: int = 5,
    keylog: str | None = None,
    flow_filter: str | None = None,
    tcp_reassemble: bool = True,
    max_flows: int = 3,
    max_msgs: int = 64,
    max_emits_per_flow: int = 3,
) -> list[StreamEvent]:
    """
    Offline stream simulation with sparse checkpoints (Termux-safe).

    Without --flow, only the top few TLS/HTTP flows are analyzed.
    """
    pcap = Path(pcap)
    print("stream: extract flows…", flush=True, file=sys.stderr)
    buckets = extract_flows(pcap, min_packets=2, min_payload=4, tcp_reassemble=tcp_reassemble)
    selected = _select_flows(buckets, flow_filter=flow_filter, max_flows=max_flows)
    print(
        f"stream: {len(buckets)} flows total → analyzing {len(selected)}",
        flush=True,
        file=sys.stderr,
    )
    agent = StreamAgent(
        every_n=every_n,
        max_depth=max_depth,
        keylog=keylog,
        max_msgs=max_msgs,
        max_emits_per_flow=max_emits_per_flow,
    )
    for label, bucket in selected:
        n = len(bucket.payloads)
        print(f"stream: {label} ({n} msgs)…", flush=True, file=sys.stderr)
        # Sparse checkpoints: early / mid / final (via flush)
        if n <= agent.min_messages:
            continue
        early = min(every_n, n)
        mid = n // 2
        checkpoints = sorted({
            c for c in (early, mid)
            if agent.min_messages <= c < n
        })
        for c in checkpoints:
            if agent.emit_count.get(label, 0) >= max_emits_per_flow - 1:
                break
            # contiguous prefix only (preserves one growing capture)
            agent.buffers[label] = list(bucket.payloads[:c])
            agent.last_emitted_at[label] = 0
            agent._emit(label, final=False)
        # final = full buffer (same quality as --signal when keylog present)
        agent.buffers[label] = list(bucket.payloads)
        agent.flush(label)
    return agent.events


def watch_pcap_file(
    pcap: str | Path,
    *,
    poll_s: float = 1.0,
    every_n: int = 32,
    max_depth: int = 5,
    keylog: str | None = None,
    max_seconds: float = 60.0,
    max_msgs: int = 48,
    max_emits_per_flow: int = 3,
) -> Iterator[StreamEvent]:
    """
    Poll a growing pcap file (e.g. PCAPdroid dump) and emit new Signal events.
    Yields events as the file grows; stops after max_seconds of idle growth.
    """
    pcap = Path(pcap)
    agent = StreamAgent(
        every_n=every_n,
        max_depth=max_depth,
        keylog=keylog,
        max_msgs=max_msgs,
        max_emits_per_flow=max_emits_per_flow,
    )
    seen_size = 0
    start = time.time()
    last_growth = start
    while time.time() - start < max_seconds:
        if not pcap.exists():
            time.sleep(poll_s)
            continue
        size = pcap.stat().st_size
        if size > seen_size and size > 24:
            seen_size = size
            last_growth = time.time()
            try:
                buckets = extract_flows(pcap, min_packets=2, min_payload=4, tcp_reassemble=True)
            except Exception:
                time.sleep(poll_s)
                continue
            for label, bucket in _select_flows(buckets, flow_filter=None, max_flows=5):
                prev = len(agent.buffers.get(label, []))
                if len(bucket.payloads) > prev:
                    # replace buffer with latest (reassembly may reshuffle)
                    agent.buffers[label] = list(bucket.payloads)
                    grown = len(bucket.payloads) - prev
                    if grown >= every_n or agent.last_emitted_at.get(label, 0) == 0:
                        if agent.emit_count.get(label, 0) < max_emits_per_flow - 1:
                            ev = agent._emit(label)
                            if ev:
                                yield ev
        if time.time() - last_growth > 15:
            for ev in agent.flush():
                yield ev
            break
        time.sleep(poll_s)
    for ev in agent.flush():
        yield ev


def events_to_report(events: list[StreamEvent]) -> dict[str, Any]:
    return {
        "events": [e.to_dict() for e in events],
        "flows": sorted({e.flow for e in events}),
        "count": len(events),
    }


def write_stream_report(events: list[StreamEvent], path: str | Path) -> Path:
    path = Path(path)
    path.write_text(json.dumps(events_to_report(events), indent=2, ensure_ascii=False), encoding="utf-8")
    return path
