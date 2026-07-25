#!/data/data/com.termux/files/usr/bin/bash
# Termux: НЕ використовуйте "python" — лише цей скрипт або python3
# bash run_pcap.sh ~/downloads/PCAPdroid_25_лип._12_42_30.pcap

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PCAP="${1:?Вкажіть шлях до .pcap}"

# Явний інтерпретатор — обходить зламаний alias "python"
PY=""
for c in python3.12 python3.11 python3; do
  if command -v "$c" >/dev/null 2>&1; then
    PY="$c"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "Встановіть Python: pkg install python"
  exit 1
fi

echo "Використовую: $PY ($($PY --version 2>&1))"
exec "$PY" "$SCRIPT_DIR/analyze_pcap.py" "$PCAP"
