"""Active probe loop — stimulate → Signal.propagate → next targets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .active_probe import (
    ProbeMessage,
    probe_dns,
    probe_http_hosts,
    probe_ntp,
    probe_tls,
)
from .signal import Signal, propagate_flow
from .stream_enrich import enrich_tcp_flow_payloads


@dataclass
class ProbeRound:
    round: int
    targets: list[str]
    signals: list[dict[str, Any]] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)


@dataclass
class ProbeLoopReport:
    rounds: list[ProbeRound]
    all_findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rounds": [
                {
                    "round": r.round,
                    "targets": r.targets,
                    "findings": r.findings,
                    "signals": r.signals,
                }
                for r in self.rounds
            ],
            "all_findings": self.all_findings,
        }


def _canonical_flow(label: str) -> str:
    """Map active-probe labels → ports Signal/deep_decode understand."""
    u = label.upper()
    if u.startswith("DNS"):
        return "UDP:53"
    if u.startswith("NTP"):
        return "UDP:123"
    if u.startswith("TLS"):
        return "TCP:443"
    if u.startswith("HTTP"):
        return "TCP:80"
    return label.replace(":", "_")


def _group_messages(msgs: list[ProbeMessage]) -> dict[str, list[bytes]]:
    groups: dict[str, list[bytes]] = {}
    for m in msgs:
        key = _canonical_flow(m.label)
        groups.setdefault(key, []).append(m.raw)
    return groups


def _extract_findings(sig: Signal) -> list[str]:
    notes = sig.format_notes()
    out: list[str] = []
    keys = (
        "SNI:",
        "ALPN:",
        "HTTP/2:",
        "hdr:",
        "title:",
        "json_keys:",
        "content:",
        "decrypt: TLS",
        "DNS:",
        "json_api",
        "api_paths:",
        "schema:",
        "protobuf:",
        "msgpack:",
        "pb_f",
        "mp_keys:",
        "handshake:",
        "Host:",
        "HTTP/1:",
        "NTP",
        "splitter:",
    )
    for n in notes:
        s = n.strip()
        if any(k in s for k in keys):
            out.append(s)
    # opaque walls → need keylog / mitm
    if any("opaque" in n for n in notes):
        out.append("wall:opaque → PCAPdroid MITM + SSLKEYLOGFILE")
    # Always keep a short path breadcrumb so rounds aren't blank
    if not out and sig.path():
        out.append(f"path: {sig.path()}")
        if sig.splitter:
            out.append(f"splitter: {sig.splitter}")
    return out


def _hosts_from_findings(findings: list[str]) -> list[str]:
    """Pull SNI / :authority / api hostnames for next HTTP/TLS rounds."""
    hosts: list[str] = []
    for f in findings:
        if "SNI:" in f:
            part = f.split("SNI:", 1)[-1].strip()
            for tok in part.replace(",", " ").split():
                h = tok.strip().lower().rstrip(".")
                if "." in h and not h.startswith("http") and len(h) < 80:
                    hosts.append(h)
        if "api_paths:" in f:
            part = f.split("api_paths:", 1)[-1]
            for tok in part.split(","):
                tok = tok.strip()
                if "/" in tok:
                    host = tok.split("/", 1)[0].strip().lower()
                    if "." in host:
                        hosts.append(host)
        if ":authority=" in f:
            # hdr: … :authority=www.example.com
            for bit in f.split():
                if bit.startswith(":authority="):
                    hosts.append(bit.split("=", 1)[-1].lower())
    # unique preserve
    seen: set[str] = set()
    out: list[str] = []
    for h in hosts:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out[:8]


def _next_targets(findings: list[str], round_i: int) -> list[str]:
    """Adaptive schedule from Signal findings."""
    targets: list[str] = []
    joined = "\n".join(findings).lower()
    if round_i == 0:
        return ["dns", "ntp", "tls", "http"]
    if "sni:" in joined or "tls" in joined or "opaque" in joined or "wall:" in joined:
        targets.append("tls")
    if "dns:" in joined or "dns" in joined:
        targets.append("dns")
    if (
        "http" in joined
        or "html" in joined
        or "hdr:" in joined
        or "json_api" in joined
        or "api_paths" in joined
    ):
        targets.append("http")
    if "protobuf" in joined or "msgpack" in joined:
        # binary APIs often sit behind TLS — re-probe TLS + HTTP
        targets.extend(["tls", "http"])
    if "ntp" in joined or round_i < 2:
        targets.append("ntp")
    if not targets:
        targets = ["dns", "http"]
    seen: set[str] = set()
    out = []
    for t in targets:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _run_targets(targets: list[str], *, focus_hosts: list[str] | None = None) -> list[ProbeMessage]:
    msgs: list[ProbeMessage] = []
    hosts = focus_hosts or None
    if "dns" in targets:
        msgs.extend(probe_dns(domains=hosts) if hosts else probe_dns())
    if "ntp" in targets:
        msgs.extend(probe_ntp())
    if "tls" in targets:
        msgs.extend(probe_tls(hosts=hosts) if hosts else probe_tls())
    if "http" in targets:
        msgs.extend(probe_http_hosts(hosts=hosts) if hosts else probe_http_hosts())
    return msgs


def run_probe_loop(
    *,
    rounds: int = 3,
    max_depth: int = 5,
    keylog: str | None = None,
) -> ProbeLoopReport:
    """
    Closed loop:
      targets → active probes → Signal.propagate → findings → next targets
    """
    report_rounds: list[ProbeRound] = []
    all_findings: list[str] = []
    targets = ["dns", "ntp", "tls", "http"]

    focus_hosts: list[str] = []
    for i in range(max(1, rounds)):
        msgs = _run_targets(targets, focus_hosts=focus_hosts or None)
        groups = _group_messages(msgs)
        round_findings: list[str] = []
        signals: list[dict[str, Any]] = []

        for label, payloads in groups.items():
            if "TLS" in label.upper() or "HTTP" in label.upper() or "TCP" in label.upper():
                payloads = enrich_tcp_flow_payloads(payloads, tls_split=True)
            if len(payloads) < 2:
                continue
            sig = propagate_flow(label, payloads, max_depth=max_depth, keylog=keylog)
            findings = _extract_findings(sig)
            round_findings.extend(findings)
            signals.append({
                "flow": label,
                "path": sig.path(),
                "notes": sig.format_notes()[:20],
                "signal": sig.to_dict(),
            })

        # unique findings
        seen: set[str] = set()
        uniq = []
        for f in round_findings:
            if f not in seen:
                seen.add(f)
                uniq.append(f)

        report_rounds.append(ProbeRound(
            round=i + 1,
            targets=list(targets),
            signals=signals,
            findings=uniq,
        ))
        all_findings.extend(uniq)
        focus_hosts = _hosts_from_findings(uniq) or focus_hosts
        targets = _next_targets(uniq, i + 1)

    # global unique
    seen = set()
    global_findings = []
    for f in all_findings:
        if f not in seen:
            seen.add(f)
            global_findings.append(f)

    return ProbeLoopReport(rounds=report_rounds, all_findings=global_findings)
