#!/data/data/com.termux/files/usr/bin/bash
# Termux: analyze_pcap.py v3.5.1 + pure AES-GCM helper (no pip cryptography)
set -euo pipefail

BRANCH="cursor/signal-pipeline-p4-a4e6"
BASE="https://raw.githubusercontent.com/lizbeth307/lizbeth307/${BRANCH}"
TS=$(date +%s)

echo "=== Termux analyze_pcap + protocol_ast helpers ==="
pkg install -y python curl openssl 2>/dev/null || true

curl -fL --retry 3 -o "$HOME/analyze_pcap.py.new" "${BASE}/analyze_pcap.py?t=${TS}"
mv "$HOME/analyze_pcap.py.new" "$HOME/analyze_pcap.py"
chmod +x "$HOME/analyze_pcap.py"

mkdir -p "$HOME/protocol_ast"
curl -fL --retry 3 -o "$HOME/protocol_ast/__init__.py" "${BASE}/protocol_ast/__init__.py?t=${TS}"
curl -fL --retry 3 -o "$HOME/protocol_ast/aes_gcm.py" "${BASE}/protocol_ast/aes_gcm.py?t=${TS}"
curl -fL --retry 3 -o "$HOME/protocol_ast/tls_keylog.py" "${BASE}/protocol_ast/tls_keylog.py?t=${TS}"

echo
PYTHONPATH="$HOME${PYTHONPATH:+:$PYTHONPATH}" python3 "$HOME/analyze_pcap.py" --version
python3 -c "import sys; sys.path.insert(0,'$HOME'); from protocol_ast.aes_gcm import backend_name; print('AES-GCM backend:', backend_name())"

echo
echo "Команди:"
echo "  export PYTHONPATH=\$HOME"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --signal --flow TCP:443"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --signal --flow TCP:443 --keylog ~/downloads/sslkeys.log"
echo
echo "БЕЗ слеша перед curl!  БЕЗ pip install cryptography."
