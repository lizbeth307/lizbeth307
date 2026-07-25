#!/data/data/com.termux/files/usr/bin/bash
# Поділитися PCAP через Android Share (обхід grep /proc/stat)
#
# Потрібно: pkg install termux-api
# І встановити додаток "Termux:API" з F-Droid / Play Store
#
# bash share_pcap.sh

set -e

PCAP="${1:-$HOME/downloads/c.pcap}"

# Якщо c.pcap немає — шукаємо PCAPdroid
if [ ! -f "$PCAP" ]; then
  PCAP=$(ls -1 "$HOME/downloads"/PCAPdroid*.pcap 2>/dev/null | head -1)
fi

if [ -z "$PCAP" ] || [ ! -f "$PCAP" ]; then
  echo "PCAP не знайдено."
  echo "Скопіюйте: cp ~/downloads/PCAPdroid*.pcap ~/downloads/c.pcap"
  exit 1
fi

# Копія з простою назвою (без кирилиці)
DEST="$HOME/downloads/wifi_capture.pcap"
cp "$PCAP" "$DEST"
echo "Файл: $DEST ($(wc -c < "$DEST") bytes)"
echo ""
echo "Зараз відкриється меню «Поділитися»..."
echo ""
echo "Оберіть один із варіантів:"
echo "  • Google Drive  → Завантажити → Скопіювати посилання → вставити в Cursor"
echo "  • Telegram      → «Збережене» або собі → переслати на ПК → завантажити"
echo "  • Gmail         → надіслати собі → відкрити на ПК"
echo "  • Chrome        → завантажити на 0x0.st / file.io (якщо є закладка)"
echo ""

if ! command -v termux-share >/dev/null 2>&1; then
  echo "Потрібно встановити:"
  echo "  pkg install termux-api"
  echo "  + додаток Termux:API з магазину"
  exit 1
fi

termux-share -a send "$DEST"

echo ""
echo "Після завантаження вставте ПОСИЛАННЯ на файл у чат Cursor."
