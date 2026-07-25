"""Streaming living-signal agent — incremental propagate over growing flows."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from .pcap_analyze import extract_flows
from .signal import propagate_flow


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
                    ev = self._emit(f)
                    if ev:
                        out.append(ev)
        return out

    def _emit(self, flow: str) -> StreamEvent | None:
        payloads = self.buffers.get(flow) or []
        if len(payloads) < self.min_messages:
            return None
        # Cap work: TLS decrypt on hundreds of records kills Termux
        sample = payloads[: self.max_msgs]
        print(
            f"  … Signal {flow} msgs={len(payloads)} (using {len(sample)})",
            flush=True,
            file=sys.stderr,
        )
        t0 = time.time()
        sig = propagate_flow(flow, sample, max_depth=self.max_depth, keylog=self.keylog)
        dt = time.time() - t0
        ev = StreamEvent(
            ts=time.time(),
            flow=flow,
            messages=len(payloads),
            path=sig.path(),
            notes=sig.format_notes()[:24],
            signal=sig.to_dict() if self.include_signal_dict else {
                "label": sig.label,
                "path": sig.path(),
                "elapsed_s": round(dt, 3),
                "sampled": len(sample),
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
    max_msgs: int = 48,
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
        checkpoints = []
        for c in (early, mid):
            if agent.min_messages <= c < n and c not in checkpoints:
                checkpoints.append(c)
        for c in checkpoints:
            if agent.emit_count.get(label, 0) >= max_emits_per_flow - 1:
                break
            agent.buffers[label] = list(bucket.payloads[:c])
            agent.last_emitted_at[label] = 0
            agent._emit(label)
        # final
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
