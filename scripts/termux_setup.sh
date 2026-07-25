#!/data/data/com.termux/files/usr/bin/bash
# Termux: один файл analyze_pcap.py (v3.0.1 — все вбудовано)
set -euo pipefail

BRANCH="cursor/p1-kaitai-handshake-a4e6"
URL="https://raw.githubusercontent.com/lizbeth307/lizbeth307/${BRANCH}/analyze_pcap.py?t=$(date +%s)"

echo "=== Termux analyze_pcap update ==="
pkg install -y python curl 2>/dev/null || true

curl -fL --retry 3 -o "$HOME/analyze_pcap.py.new" "$URL"
mv "$HOME/analyze_pcap.py.new" "$HOME/analyze_pcap.py"
chmod +x "$HOME/analyze_pcap.py"

echo
python3 "$HOME/analyze_pcap.py" --version
echo
echo "Команди:"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --blind"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --nested --tcp-reassemble"
echo
echo "БЕЗ слеша перед curl! Правильно: curl -fsSL ..."
