#!/data/data/com.termux/files/usr/bin/bash
# Termux: один файл analyze_pcap.py (v3.3.1 — merged 16-bit fields)
set -euo pipefail

BRANCH="cursor/signal-pipeline-p4-a4e6"
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
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --nested --tcp-reassemble --export-kaitai ~/downloads/ksy"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --dissect --flow 53 --limit 3"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --dissect-html ~/downloads/view.html --flow 443 --tcp-reassemble"
echo
echo "БЕЗ слеша перед curl! Правильно: curl -fsSL ..."
