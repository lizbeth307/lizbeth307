#!/data/data/com.termux/files/usr/bin/bash
# Termux: analyze_pcap.py v3.6.0 + keylog auto / pcapng DSB / pure AES-GCM
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
for f in __init__.py aes_gcm.py tls_keylog.py pcapng_secrets.py find_keylog.py http2.py hpack_decode.py signal.py body_peel.py; do
  curl -fL --retry 3 -o "$HOME/protocol_ast/$f" "${BASE}/protocol_ast/$f?t=${TS}"
done

echo
PYTHONPATH="$HOME${PYTHONPATH:+:$PYTHONPATH}" python3 "$HOME/analyze_pcap.py" --version
python3 -c "import sys; sys.path.insert(0,'$HOME'); from protocol_ast.aes_gcm import backend_name; print('AES-GCM backend:', backend_name())"

echo
echo "Команди:"
echo "  export PYTHONPATH=\$HOME"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --signal --flow TCP:443"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --signal --flow TCP:443 --keylog auto"
echo "  python3 ~/protocol_ast/find_keylog.py ~/downloads/c.pcap"
echo
echo "MITM keylog: curl -fsSL ${BASE}/scripts/pcapdroid_mitm.txt"
echo "БЕЗ слеша перед curl!  БЕЗ pip install cryptography."
