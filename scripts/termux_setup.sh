#!/data/data/com.termux/files/usr/bin/bash
# Termux full-pack setup: analyze_pcap.py + protocol_ast modules
set -euo pipefail

BRANCH="cursor/full-pack-p0-a4e6"
BASE="https://raw.githubusercontent.com/lizbeth307/lizbeth307/${BRANCH}"

echo "=== Termux Full Pack setup ==="
pkg install -y python 2>/dev/null || true

cd "$HOME"
mkdir -p protocol_ast

MODULES=(
  __init__.py align.py parser.py pipeline.py ast_nodes.py sequitur.py serde.py
  deep_decode.py blind_v2.py cluster.py tcp_reassemble.py stream_enrich.py pcap_analyze.py
)

for m in "${MODULES[@]}"; do
  curl -fsSL -o "protocol_ast/$m" "${BASE}/protocol_ast/$m"
done

curl -fsSL -o analyze_pcap.py "${BASE}/analyze_pcap.py"
curl -fsSL -o run_pcap.sh "${BASE}/run_pcap.sh"
chmod +x run_pcap.sh analyze_pcap.py

echo 'export PS1="$ "' > "$HOME/.bashrc"

echo
echo "Версія:"
python3 ~/analyze_pcap.py --version
echo
echo "Full pack (nested AST + TCP reassembly):"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --nested --tcp-reassemble --blind"
echo
echo "Classic blind (embedded):"
echo "  python3 ~/analyze_pcap.py ~/downloads/c.pcap --blind"

PCAP="${1:-}"
if [ -z "$PCAP" ]; then
  PCAP=$(ls -1 "$HOME/downloads/"*.pcap 2>/dev/null | head -1 || true)
fi
if [ -n "$PCAP" ] && [ -f "$PCAP" ]; then
  exec python3 "$HOME/analyze_pcap.py" "$PCAP" --nested --tcp-reassemble --blind --flow 443
fi
