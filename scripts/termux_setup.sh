#!/data/data/com.termux/files/usr/bin/bash
# Termux: analyze_pcap.py v3.8.0 + living signal (JSON API / probe loop / stream)
set -euo pipefail

BRANCH="cursor/signal-pipeline-p4-a4e6"
BASE="https://raw.githubusercontent.com/lizbeth307/lizbeth307/${BRANCH}"
# Prefer jsDelivr if raw.githubusercontent.com serves stale cache:
# BASE="https://cdn.jsdelivr.net/gh/lizbeth307/lizbeth307@${BRANCH}"
TS=$(date +%s)

echo "=== Termux analyze_pcap + protocol_ast helpers (v3.8) ==="
pkg install -y python curl openssl 2>/dev/null || true
pip install --user brotli 2>/dev/null || true

curl -fL --retry 3 -o "$HOME/analyze_pcap.py.new" "${BASE}/analyze_pcap.py?t=${TS}"
mv "$HOME/analyze_pcap.py.new" "$HOME/analyze_pcap.py"
chmod +x "$HOME/analyze_pcap.py"

curl -fL --retry 3 -o "$HOME/probe_network.py.new" "${BASE}/probe_network.py?t=${TS}"
mv "$HOME/probe_network.py.new" "$HOME/probe_network.py"
chmod +x "$HOME/probe_network.py"

mkdir -p "$HOME/protocol_ast"
for f in \
  __init__.py aes_gcm.py tls_keylog.py pcapng_secrets.py find_keylog.py \
  http2.py hpack_decode.py signal.py body_peel.py json_api.py binary_peel.py \
  probe_loop.py stream_agent.py smart_probe.py active_probe.py stream_enrich.py \
  splitters.py tls_handshake.py pcap_analyze.py pcap_read.py deep_decode.py \
  align.py cluster.py sequitur.py parser.py serde.py pipeline.py ast_nodes.py \
  io_utils.py tcp_reassemble.py probe_env.py
do
  curl -fL --retry 3 -o "$HOME/protocol_ast/$f" "${BASE}/protocol_ast/$f?t=${TS}" || true
done

echo
PYTHONPATH="$HOME${PYTHONPATH:+:$PYTHONPATH}" python3 "$HOME/analyze_pcap.py" --version
python3 -c "import sys; sys.path.insert(0,'$HOME'); from protocol_ast.aes_gcm import backend_name; print('AES-GCM backend:', backend_name())"

echo
echo "Команди:"
echo "  export PYTHONPATH=\$HOME"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --signal --flow TCP:443 --keylog auto"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --stream --keylog auto"
echo "  python3 ~/probe_network.py --loop 3 --no-capture"
echo "  python3 ~/probe_network.py --watch ~/storage/downloads/PCAPdroid/foo.pcap --keylog auto"
echo
echo "MITM keylog: curl -fsSL ${BASE}/scripts/pcapdroid_mitm.txt"
echo "Living signal: curl -fsSL ${BASE}/scripts/LIVING_SIGNAL.txt"
echo "БЕЗ слеша перед curl!  БЕЗ pip install cryptography."
