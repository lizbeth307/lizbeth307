#!/usr/bin/env bash
# Захоплення Wi-Fi трафіку на ВАШОМУ комп'ютері (не в cloud agent).
#
# Linux:
#   sudo ./scripts/capture_wifi.sh wlan0 300 wifi.pcap
#   sudo ./scripts/capture_wifi.sh wlo1 300 wifi.pcap
#
# macOS:
#   sudo ./scripts/capture_wifi.sh en0 300 wifi.pcap
#
# Потім аналіз:
#   python3 discover_protocol_ast.py wifi-analyze wifi.pcap
#   python3 discover_protocol_ast.py wifi-analyze wifi.pcap --flow DNS

set -euo pipefail

IFACE="${1:-}"
SECONDS="${2:-120}"
OUT="${3:-wifi_capture.pcap}"
COUNT="${4:-2000}"

if [[ -z "$IFACE" ]]; then
  echo "Використання: sudo $0 <interface> [seconds] [output.pcap] [max_packets]"
  echo
  echo "Доступні інтерфейси:"
  if command -v ip >/dev/null; then
    ip -br link
  elif command -v ifconfig >/dev/null; then
    ifconfig -l 2>/dev/null || ifconfig | awk '/^[a-z]/ {print $1}'
  else
    ls /sys/class/net 2>/dev/null || true
  fi
  exit 1
fi

if ! command -v tcpdump >/dev/null; then
  echo "Потрібен tcpdump. Встановіть: sudo apt install tcpdump  (Linux)"
  exit 1
fi

echo "Захоплення на $IFACE → $OUT (max ${COUNT} pkts, ~${SECONDS}s)"
echo "Ctrl+C для зупинки раніше."

sudo tcpdump -i "$IFACE" -s 65535 -w "$OUT" -c "$COUNT" \
  'udp or tcp' &
PID=$!
sleep "$SECONDS" 2>/dev/null || true
sudo kill "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true

if [[ -f "$OUT" ]]; then
  SIZE=$(wc -c < "$OUT")
  echo "Готово: $OUT ($SIZE bytes)"
  echo "Далі: python3 discover_protocol_ast.py wifi-analyze $OUT"
else
  echo "Файл не створено — перевірте права sudo та назву інтерфейсу."
  exit 1
fi
