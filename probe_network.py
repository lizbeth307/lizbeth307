#!/usr/bin/env python3
"""
probe_network.py — універсальний зонд мережі + living signal.

Нівелює мінуси:
  📱 Android (без root)  → active DNS/NTP/TLS probe + auto-пошук PCAPdroid .pcap
  ☁️  Cloud eth0          → live capture + стимуляція трафіку + active probe
  🖥️  Desktop            → pcap або tcpdump + active probe

Приклади:
  python3 probe_network.py                         # авто-режим + Signal
  python3 probe_network.py --loop 3                # adaptive probe loop
  python3 probe_network.py --pcap wifi.pcap --signal
  python3 probe_network.py --stream capture.pcap   # incremental Signal events
  python3 probe_network.py --no-capture            # лише active probe
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from protocol_ast.probe_env import detect_runtime
from protocol_ast.smart_probe import run_smart_probe


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pcap", type=Path, help="PCAP/PCAPdroid файл (з телефона або Wireshark)")
    p.add_argument("--no-capture", action="store_true", help="не запускати tcpdump (тільки active probe)")
    p.add_argument("--no-active", action="store_true", help="не робити active DNS/NTP/TLS probe")
    p.add_argument("--no-auto-pcap", action="store_true", help="не шукати .pcap на Android автоматично")
    p.add_argument("--no-signal", action="store_true", help="вимкнути Signal.propagate (лише classic AST)")
    p.add_argument("--loop", type=int, metavar="N", help="adaptive active-probe loop N rounds → Signal")
    p.add_argument("--stream", type=Path, metavar="PCAP", help="incremental living-signal over pcap")
    p.add_argument("--watch", type=Path, metavar="PCAP", help="poll growing pcap (PCAPdroid) and emit Signal")
    p.add_argument("--keylog", metavar="FILE|auto", help="SSLKEYLOGFILE for TLS decrypt")
    p.add_argument("--every", type=int, default=8, help="stream: emit every N new messages")
    p.add_argument("-o", "--out-dir", type=Path, help="зберегти format_*.json + probe_report.json")
    p.add_argument("--min-packets", type=int, default=2)
    p.add_argument("--min-payload", type=int, default=4)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    keylog = args.keylog
    if keylog:
        try:
            from protocol_ast.find_keylog import resolve_keylog

            kpath, kmsg = resolve_keylog(keylog, pcap_path=args.pcap or args.stream or args.watch)
            if not args.json:
                print(kmsg if kpath else f"⚠  {kmsg}")
            keylog = str(kpath) if kpath else None
        except Exception:
            pass

    # --- Adaptive probe loop ---
    if args.loop:
        from protocol_ast.probe_loop import run_probe_loop

        report = run_probe_loop(rounds=args.loop, keylog=keylog)
        if args.out_dir:
            args.out_dir.mkdir(parents=True, exist_ok=True)
            out = args.out_dir / "probe_loop_report.json"
            out.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        if args.json:
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
            return 0 if report.rounds else 1
        print(f"Probe loop: {len(report.rounds)} rounds\n")
        for rnd in report.rounds:
            print(f"── round {rnd.round} targets={rnd.targets} signals={len(rnd.signals)}")
            if rnd.findings:
                for f in rnd.findings[:12]:
                    print(f"   • {f}")
            else:
                # still show signal breadcrumbs
                for s in rnd.signals[:4]:
                    print(f"   • {s.get('flow')}: {s.get('path')}")
                    for n in (s.get("notes") or [])[:3]:
                        print(f"     {n}")
            print()
        if report.all_findings:
            print(f"Унікальних findings: {len(report.all_findings)}")
        if args.out_dir:
            print(f"Звіт: {args.out_dir / 'probe_loop_report.json'}")
        return 0 if report.rounds else 1

    # --- Streaming / watch ---
    if args.stream or args.watch:
        from protocol_ast.stream_agent import (
            analyze_pcap_streaming,
            events_to_report,
            watch_pcap_file,
            write_stream_report,
        )

        if args.watch:
            if not args.json:
                print(f"Watching {args.watch} …")
            events = list(watch_pcap_file(args.watch, every_n=args.every, keylog=keylog))
        else:
            events = analyze_pcap_streaming(args.stream, every_n=args.every, keylog=keylog)
        if args.out_dir:
            args.out_dir.mkdir(parents=True, exist_ok=True)
            write_stream_report(events, args.out_dir / "stream_report.json")
        if args.json:
            print(json.dumps(events_to_report(events), indent=2, ensure_ascii=False))
            return 0 if events else 1
        print(f"Stream events: {len(events)}\n")
        for ev in events:
            print(f"── {ev.flow} msgs={ev.messages} path={ev.path}")
            for n in ev.notes[:8]:
                print(f"   {n}" if n.startswith("[") or n.startswith("  ") else f"   • {n}")
            print()
        return 0 if events else 1

    env = detect_runtime()
    if not args.json:
        print(f"Середовище: {env.kind}  iface={env.iface}  tcpdump={env.can_tcpdump}")
        for note in env.notes:
            print(f"  • {note}")
        print()

    report = run_smart_probe(
        pcap=args.pcap,
        auto_pcap=not args.no_auto_pcap,
        active=not args.no_active,
        capture=not args.no_capture,
        out_dir=args.out_dir,
        min_packets=args.min_packets,
        min_payload=args.min_payload,
        use_signal=not args.no_signal,
        keylog=keylog,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        return 0 if report.flows else 1

    print(f"Джерела: {', '.join(report.sources) or '(немає)'}")
    print(f"Потоків проаналізовано: {len(report.flows)}\n")

    for rep in sorted(report.flows, key=lambda r: -r.parse_success):
        print(f"── {rep.flow} [{rep.source}]  msgs={rep.messages}  parse={rep.parse_success:.0%}")
        if rep.signal_path:
            print(f"   signal: {rep.signal_path}")
        if rep.signal_notes:
            for n in rep.signal_notes[:10]:
                print(f"   {n}" if n.startswith("[") or n.startswith("  ") else f"   • {n}")
        elif rep.hints:
            for h in rep.hints:
                print(f"   {h}")
        if rep.format.length_field_offset is not None:
            print(
                f"   length @{rep.format.length_field_offset} "
                f"({rep.format.length_endian})"
            )
        print()

    if args.out_dir:
        print(f"Звіт: {args.out_dir / 'probe_report.json'}")

    if env.kind == "android" and not args.pcap and not any("pcap" in s for s in report.sources):
        print(
            "\n📱 Порада: експортуйте PCAP з PCAPdroid →\n"
            "   python3 probe_network.py --pcap ~/downloads/c.pcap --keylog auto"
        )

    return 0 if report.flows else 1


if __name__ == "__main__":
    raise SystemExit(main())
