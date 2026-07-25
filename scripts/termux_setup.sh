#!/data/data/com.termux/files/usr/bin/bash
# Termux: analyze_pcap.py v3.8.0 + living signal helpers
# Usage:
#   SHA=b44215d333e3a176d8773808450be674523d98f7
#   curl -fsSL "https://cdn.jsdelivr.net/gh/lizbeth307/lizbeth307@$SHA/scripts/termux_setup.sh" | bash
# Or skip pkg entirely:
#   SKIP_PKG=1 curl -fsSL "..." | bash
set -euo pipefail

SHA="${SHA:-b44215d333e3a176d8773808450be674523d98f7}"
BASE="${BASE:-https://cdn.jsdelivr.net/gh/lizbeth307/lizbeth307@${SHA}}"

echo "=== Termux living signal v3.8 ==="
echo "BASE=$BASE"

# 1) Download FIRST (never block on apt prompts)
curl -fL --retry 3 -o "$HOME/analyze_pcap.py.new" "${BASE}/analyze_pcap.py"
mv "$HOME/analyze_pcap.py.new" "$HOME/analyze_pcap.py"
chmod +x "$HOME/analyze_pcap.py"

curl -fL --retry 3 -o "$HOME/probe_network.py.new" "${BASE}/probe_network.py"
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
  curl -fL --retry 3 -o "$HOME/protocol_ast/$f" "${BASE}/protocol_ast/$f" || echo "⚠ skip $f"
done

# 2) Optional packages — noninteractive, never block on openssl.cnf
if [ "${SKIP_PKG:-0}" != "1" ]; then
  export DEBIAN_FRONTEND=noninteractive
  # keep existing config files; no Y/N prompts
  pkg install -y -o Dpkg::Options::="--force-confold" python curl 2>/dev/null || true
  pip install --user brotli 2>/dev/null || true
fi

echo
export PYTHONPATH="$HOME${PYTHONPATH:+:$PYTHONPATH}"
python3 "$HOME/analyze_pcap.py" --version
python3 -c "import sys; sys.path.insert(0,'$HOME'); from protocol_ast.aes_gcm import backend_name; print('AES-GCM backend:', backend_name())" || true

echo
echo "Команди (ОДИН файл, не glob *):"
echo "  export PYTHONPATH=\$HOME"
echo "  PCAP=~/downloads/PCAPdroid_25_лип._22_46_14.pcap"
echo "  python3 ~/analyze_pcap.py \"\$PCAP\" --signal --flow TCP:443 --keylog auto"
echo "  python3 ~/analyze_pcap.py \"\$PCAP\" --stream --keylog auto"
echo "  python3 ~/probe_network.py --loop 3 --no-capture"
echo
echo "БЕЗ слеша перед curl.  SKIP_PKG=1 щоб пропустити apt."
