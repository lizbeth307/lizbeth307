#!/data/data/com.termux/files/usr/bin/bash
# Пошук PCAP на телефоні (Termux / PCAPdroid)
# Запуск: bash scripts/find_pcap_phone.sh

echo "=== Termux home ==="
ls -la ~/downloads/*.pcap 2>/dev/null || echo "(немає в ~/downloads/)"

echo
echo "=== Пошук PCAPdroid ==="
find ~/downloads /sdcard/Download /sdcard/Downloads \
  -iname 'PCAPdroid*.pcap' -o -iname '*.pcapng' 2>/dev/null | head -20

echo
echo "=== Якщо знайдено — аналіз ==="
PCAP=$(find ~/downloads -iname 'PCAPdroid*.pcap' 2>/dev/null | head -1)
if [ -n "$PCAP" ]; then
  echo "Файл: $PCAP"
  echo "Команда:"
  echo "  python3 probe_network.py --pcap \"$PCAP\" -o probe_out"
else
  echo "Не знайдено. Перевірте Files → Termux → home → downloads"
fi
