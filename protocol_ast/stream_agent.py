"""Streaming living-signal agent — incremental propagate over growing flows."""

from __future__ import annotations

import json
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
    Feed packets/payloads per flow; every `every_n` new messages (or flush)
    re-run Signal.propagate and emit events.
    """

    every_n: int = 8
    max_depth: int = 5
    keylog: str | None = None
    min_messages: int = 2
    buffers: dict[str, list[bytes]] = field(default_factory=dict)
    last_emitted_at: dict[str, int] = field(default_factory=dict)
    events: list[StreamEvent] = field(default_factory=list)

    def feed(self, flow: str, payload: bytes) -> StreamEvent | None:
        if not payload:
            return None
        buf = self.buffers.setdefault(flow, [])
        buf.append(payload)
        last = self.last_emitted_at.get(flow, 0)
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
        sig = propagate_flow(flow, payloads, max_depth=self.max_depth, keylog=self.keylog)
        ev = StreamEvent(
            ts=time.time(),
            flow=flow,
            messages=len(payloads),
            path=sig.path(),
            notes=sig.format_notes()[:24],
            signal=sig.to_dict(),
        )
        self.last_emitted_at[flow] = len(payloads)
        self.events.append(ev)
        return ev


def analyze_pcap_streaming(
    pcap: str | Path,
    *,
    every_n: int = 8,
    max_depth: int = 5,
    keylog: str | None = None,
    flow_filter: str | None = None,
    tcp_reassemble: bool = True,
) -> list[StreamEvent]:
    """
    Simulate streaming over an existing pcap: feed payloads in capture order
    (approx via flow buckets) and emit incremental Signal events.
    """
    pcap = Path(pcap)
    agent = StreamAgent(every_n=every_n, max_depth=max_depth, keylog=keylog)
    buckets = extract_flows(pcap, min_packets=2, min_payload=4, tcp_reassemble=tcp_reassemble)
    for label, bucket in sorted(buckets.items(), key=lambda x: -x[1].packet_count):
        if flow_filter and flow_filter.lower() not in label.lower():
            continue
        agent.feed_many(label, bucket.payloads)
    agent.flush()
    return agent.events


def watch_pcap_file(
    pcap: str | Path,
    *,
    poll_s: float = 1.0,
    every_n: int = 8,
    max_depth: int = 5,
    keylog: str | None = None,
    max_seconds: float = 60.0,
) -> Iterator[StreamEvent]:
    """
    Poll a growing pcap file (e.g. PCAPdroid dump) and emit new Signal events.
    Yields events as the file grows; stops after max_seconds of idle growth.
    """
    pcap = Path(pcap)
    agent = StreamAgent(every_n=every_n, max_depth=max_depth, keylog=keylog)
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
            # full re-extract (simple + robust for Termux)
            try:
                buckets = extract_flows(pcap, min_packets=2, min_payload=4, tcp_reassemble=True)
            except Exception:
                time.sleep(poll_s)
                continue
            for label, bucket in buckets.items():
                prev = len(agent.buffers.get(label, []))
                if len(bucket.payloads) > prev:
                    for p in bucket.payloads[prev:]:
                        ev = agent.feed(label, p)
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
