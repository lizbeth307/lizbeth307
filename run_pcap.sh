#!/data/data/com.termux/files/usr/bin/bash
# Обхід grep /proc/stat — це шум від prompt Termux, не помилка скрипта
set +e
export PS1='$ '
unset PROMPT_COMMAND 2>/dev/null

PCAP="${1:-$HOME/downloads/PCAPdroid_25_лип._12_42_30.pcap}"
SCRIPT="${2:-$HOME/analyze_pcap.py}"

if [ ! -f "$PCAP" ]; then
  echo "Немає файлу: $PCAP"
  ls -la "$HOME/downloads/"*.pcap 2>/dev/null
  exit 1
fi

PY=$(command -v python3.12 || command -v python3.11 || command -v python3)
if [ -z "$PY" ]; then
  echo "pkg install python"
  exit 1
fi

echo "=== Аналіз PCAP ==="
echo "Python: $PY"
echo "Файл:   $PCAP ($(wc -c < "$PCAP") bytes)"
echo "(ігноруйте grep /proc/stat — це Termux prompt)"
echo

# --norc = без .bashrc який викликає grep
exec bash --norc --noprofile -c "\"$PY\" \"$SCRIPT\" \"$PCAP\""
