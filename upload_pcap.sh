#!/data/data/com.termux/files/usr/bin/bash
# Завантажити pcap на тимчасовий хост → надіслати URL у чат Cursor
# bash upload_pcap.sh ~/downloads/PCAPdroid_25_лип._12_42_30.pcap

PCAP="${1:?вкажіть .pcap}"
if [ ! -f "$PCAP" ]; then
  echo "Файл не знайдено: $PCAP"
  exit 1
fi

echo "Завантаження $(wc -c < "$PCAP") bytes..."
URL=$(curl -sS -F "file=@${PCAP}" https://0x0.st)
if [ -z "$URL" ]; then
  echo "Помилка завантаження. Спробуйте:"
  echo "  termux-share -a send \"$PCAP\""
  exit 1
fi

echo ""
echo "✅ Готово! Скопіюйте цей URL у чат Cursor:"
echo "$URL"
echo ""
echo "Агент зможе завантажити і розібрати файл."
