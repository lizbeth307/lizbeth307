#!/usr/bin/env python3
"""
probe_network.py — універсальний зонд мережі.

Нівелює мінуси:
  📱 Android (без root)  → active DNS/NTP/TLS probe + auto-пошук PCAPdroid .pcap
  ☁️  Cloud eth0          → live capture + стимуляція трафіку + active probe
  🖥️  Desktop            → pcap або tcpdump + active probe

Приклади:
  python3 probe_network.py                    # авто-режим
  python3 probe_network.py --pcap wifi.pcap   # PCAPdroid з телефона
  python3 probe_network.py --no-capture       # лише active probe (офлайн-friendly)
  python3 probe_network.py -o ./probe_out --json
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
    p.add_argument("-o", "--out-dir", type=Path, help="зберегти format_*.json + probe_report.json")
    p.add_argument("--min-packets", type=int, default=2)
    p.add_argument("--min-payload", type=int, default=4)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

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
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        return 0 if report.flows else 1

    print(f"Джерела: {', '.join(report.sources) or '(немає)'}")
    print(f"Потоків проаналізовано: {len(report.flows)}\n")

    for rep in sorted(report.flows, key=lambda r: -r.parse_success):
        print(f"── {rep.flow} [{rep.source}]  msgs={rep.messages}  parse={rep.parse_success:.0%}")
        if rep.hints:
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
            "   python3 probe_network.py --pcap /sdcard/Download/capture.pcap"
        )

    return 0 if report.flows else 1


if __name__ == "__main__":
    raise SystemExit(main())
