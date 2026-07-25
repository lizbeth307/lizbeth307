"""Універсальний зонд: нівелює обмеження Android + cloud eth0."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .active_probe import run_active_probes
from .align import FormatHypothesis
from .pcap_analyze import FlowBucket, extract_flows, flow_summary
from .pipeline import discover_and_parse
from .probe_env import android_pcap_hints, detect_runtime
from .serde import save_format
from .stream_enrich import enrich_tcp_flow_payloads


@dataclass
class FlowReport:
    source: str  # active | pcap | merged
    flow: str
    messages: int
    parse_success: float
    format: FormatHypothesis
    hints: list[str] = field(default_factory=list)
    sample_ast: dict | None = None
    signal: dict | None = None
    signal_path: str | None = None
    signal_notes: list[str] = field(default_factory=list)


@dataclass
class ProbeReport:
    runtime: str
    runtime_notes: list[str]
    sources: list[str]
    flows: list[FlowReport]

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime": self.runtime,
            "runtime_notes": self.runtime_notes,
            "sources": self.sources,
            "flows": [
                {
                    "source": f.source,
                    "flow": f.flow,
                    "messages": f.messages,
                    "parse_success": f.parse_success,
                    "hints": f.hints,
                    "format": {
                        "length_offset": f.format.length_field_offset,
                        "length_endian": f.format.length_endian,
                        "fields": [
                            {"name": x.name, "kind": x.kind, "offset": x.offset, "size": x.size}
                            for x in f.format.fields
                        ],
                    },
                    "sample_ast": f.sample_ast,
                    "signal_path": f.signal_path,
                    "signal_notes": f.signal_notes,
                    "signal": f.signal,
                }
                for f in self.flows
            ],
        }


def _protocol_hints(flow: str, payloads: list[bytes]) -> list[str]:
    hints: list[str] = []
    if not payloads:
        return hints
    sample = payloads[0]
    fl = flow.upper()
    if "DNS" in fl or ":53" in fl:
        hints.append("Ймовірно DNS (RFC 1035): 12-byte header")
        if len(sample) >= 12:
            hints.append(f"  QDCOUNT={int.from_bytes(sample[4:6], 'big')}")
    if ":443" in fl or "TLS" in fl:
        if sample and sample[0] in (20, 21, 22, 23):
            hints.append(f"TLS record type=0x{sample[0]:02x}, version={sample[1:3].hex()}")
    if ":123" in fl or "NTP" in fl:
        hints.append(f"NTP mode/VN у byte0: 0x{sample[0]:02x}")
    if sample[:2] == b"\xfe\xca":
        hints.append("Synthetic oracle magic 0xCAFE")
    return hints


def _analyze_group(
    label: str,
    payloads: list[bytes],
    source: str,
    *,
    tls_split: bool = True,
    use_signal: bool = True,
    keylog: str | None = None,
    max_depth: int = 5,
) -> FlowReport | None:
    if "TCP" in label.upper() or "TLS" in label.upper() or "HTTP" in label.upper():
        payloads = enrich_tcp_flow_payloads(payloads, tls_split=tls_split)
    if len(payloads) < 2:
        return None
    result = discover_and_parse(payloads)
    signal_dict = None
    signal_path = None
    signal_notes: list[str] = []
    if use_signal:
        try:
            from .signal import propagate_flow

            sig = propagate_flow(label, payloads, max_depth=max_depth, keylog=keylog)
            signal_dict = sig.to_dict()
            signal_path = sig.path()
            signal_notes = sig.format_notes()[:24]
        except Exception as exc:
            signal_notes = [f"signal error: {exc}"]
    return FlowReport(
        source=source,
        flow=label,
        messages=len(payloads),
        parse_success=result.success_rate,
        format=result.format,
        hints=_protocol_hints(label, payloads),
        sample_ast=result.trees[0].to_dict() if result.trees else None,
        signal=signal_dict,
        signal_path=signal_path,
        signal_notes=signal_notes,
    )


def _capture_pcap(
    iface: str,
    out: Path,
    *,
    count: int = 300,
    seconds: int = 10,
) -> bool:
    try:
        proc = subprocess.Popen(
            [
                "sudo", "tcpdump", "-i", iface,
                "-s", "65535", "-w", str(out),
                "-c", str(count),
                "tcp or udp",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1)
        _stimulate_traffic()
        proc.wait(timeout=seconds + 15)
        return out.exists() and out.stat().st_size > 24
    except (OSError, subprocess.SubprocessError):
        try:
            proc.kill()
        except Exception:
            pass
        return False


def _stimulate_traffic() -> None:
    """Генерує трафік під час захоплення (eth0/cloud)."""
    cmds = [
        ["curl", "-s", "--max-time", "3", "https://1.1.1.1"],
        ["curl", "-s", "--max-time", "3", "http://example.com"],
    ]
    for cmd in cmds:
        try:
            subprocess.run(cmd, capture_output=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            pass
    # DNS через active probe вже


def run_smart_probe(
    *,
    pcap: Path | None = None,
    auto_pcap: bool = True,
    active: bool = True,
    capture: bool = True,
    out_dir: Path | None = None,
    min_packets: int = 2,
    min_payload: int = 4,
    use_signal: bool = True,
    keylog: str | None = None,
    max_depth: int = 5,
) -> ProbeReport:
    env = detect_runtime()
    sources: list[str] = []
    flow_reports: list[FlowReport] = []

    # --- 1) Active probe (працює скрізь: Android без root, cloud eth0) ---
    if active:
        sources.append("active-probe")
        for label, payloads in run_active_probes().items():
            rep = _analyze_group(
                label, payloads, "active",
                use_signal=use_signal, keylog=keylog, max_depth=max_depth,
            )
            if rep:
                flow_reports.append(rep)

    # --- 2) PCAP: користувацький, auto-знайдений (Android), або live capture ---
    pcap_path = pcap
    if pcap_path is None and auto_pcap and env.kind == "android":
        hints = android_pcap_hints()
        if hints:
            pcap_path = hints[0]
            env.notes.append(f"auto-pcap: {pcap_path}")

    if pcap_path is None and capture and env.can_tcpdump and env.iface:
        tmp_pcap = Path(out_dir or ".") / "probe_capture.pcap"
        if _capture_pcap(env.iface, tmp_pcap):
            pcap_path = tmp_pcap
            sources.append(f"live-capture:{env.iface}")

    if pcap_path and pcap_path.exists():
        sources.append(f"pcap:{pcap_path.name}")
        buckets = extract_flows(
            pcap_path, min_packets=min_packets, min_payload=min_payload
        )
        for label, bucket in buckets.items():
            rep = _analyze_group(
                label, bucket.payloads, "pcap",
                use_signal=use_signal, keylog=keylog, max_depth=max_depth,
            )
            if rep:
                flow_reports.append(rep)

    # --- 3) Зберегти схеми ---
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, rep in enumerate(flow_reports):
            safe = rep.flow.replace(":", "_").replace("<->", "_")
            save_format(rep.format, out_dir / f"format_{i}_{safe}.json")
        (out_dir / "probe_report.json").write_text(
            json.dumps(
                ProbeReport(env.kind, env.notes, sources, flow_reports).to_dict(),
                indent=2,
            ),
            encoding="utf-8",
        )

    return ProbeReport(
        runtime=env.kind,
        runtime_notes=env.notes,
        sources=sources,
        flows=flow_reports,
    )
