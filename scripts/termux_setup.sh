#!/data/data/com.termux/files/usr/bin/bash
# Одноразове налаштування Termux для аналізу PCAP
set -euo pipefail

BRANCH="cursor/termux-blind-setup-a4e6"
BASE="https://raw.githubusercontent.com/lizbeth307/lizbeth307/${BRANCH}"

echo "=== Termux PCAP setup ==="

if ! command -v python3 >/dev/null 2>&1; then
  echo "Встановлюю python..."
  pkg install -y python
fi

echo "Python: $(command -v python3) ($(python3 --version 2>&1))"

cd "$HOME"
curl -fsSL -o analyze_pcap.py "${BASE}/analyze_pcap.py"
curl -fsSL -o run_pcap.sh "${BASE}/run_pcap.sh"
chmod +x run_pcap.sh analyze_pcap.py

# Вимкнути зламаний prompt (grep /proc/stat)
if [ -f "$HOME/.bashrc" ] && grep -q PROMPT_COMMAND "$HOME/.bashrc" 2>/dev/null; then
  mv "$HOME/.bashrc" "$HOME/.bashrc.bak.$(date +%s)" 2>/dev/null || true
fi
echo 'export PS1="$ "' > "$HOME/.bashrc"

PCAP="${1:-}"
if [ -z "$PCAP" ]; then
  PCAP=$(ls -1 "$HOME/downloads/"*.pcap 2>/dev/null | head -1 || true)
fi

echo
echo "Готово. Приклади:"
echo "  python3 ~/analyze_pcap.py ~/downloads/ваш_файл.pcap"
echo "  python3 ~/analyze_pcap.py ~/downloads/ваш_файл.pcap --blind --flow 443"
echo "  bash ~/run_pcap.sh ~/downloads/ваш_файл.pcap"

if [ -n "$PCAP" ] && [ -f "$PCAP" ]; then
  echo
  echo "=== Запускаю аналіз: $PCAP ==="
  exec python3 "$HOME/analyze_pcap.py" "$PCAP" --blind --flow 443
fi
