#!/data/data/com.termux/files/usr/bin/bash
# Termux living-signal updater — ONLY downloads files. Never runs apt/pkg.
#
#   curl -fsSL https://cdn.jsdelivr.net/gh/lizbeth307/lizbeth307@cursor/signal-pipeline-p4-a4e6/scripts/termux_setup.sh | bash
#
# Or (always fresh tip via GitHub API):
#   curl -fsSL https://raw.githubusercontent.com/lizbeth307/lizbeth307/cursor/signal-pipeline-p4-a4e6/scripts/termux_setup.sh?t=$(date +%s) | bash
set -euo pipefail

BRANCH="${BRANCH:-cursor/signal-pipeline-p4-a4e6}"
REPO="lizbeth307/lizbeth307"

echo "=== Termux living signal update (no apt) ==="

# Resolve immutable commit SHA → jsDelivr (no stale branch cache)
SHA=""
if command -v python3 >/dev/null 2>&1; then
  SHA=$(python3 - <<'PY' 2>/dev/null || true
import json, ssl, urllib.request
branch = "cursor/signal-pipeline-p4-a4e6"
url = f"https://api.github.com/repos/lizbeth307/lizbeth307/commits/{branch}"
req = urllib.request.Request(url, headers={"User-Agent": "termux-setup"})
ctx = ssl.create_default_context()
with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
    print(json.load(r)["sha"])
PY
)
fi
if [ -z "$SHA" ]; then
  SHA=$(curl -fsSL -H "User-Agent: termux-setup" \
    "https://api.github.com/repos/${REPO}/commits/${BRANCH}" \
    | sed -n 's/.*"sha": "\([0-9a-f]\{40\}\)".*/\1/p' | head -1 || true)
fi

if [ -n "$SHA" ]; then
  BASE="https://cdn.jsdelivr.net/gh/${REPO}@${SHA}"
  echo "SHA=$SHA"
else
  # last resort: raw branch + cache buster
  TS=$(date +%s)
  BASE="https://raw.githubusercontent.com/${REPO}/${BRANCH}"
  echo "⚠ API SHA unavailable — using raw branch tip t=$TS"
fi
echo "BASE=$BASE"

_get() {
  # $1=url $2=dest
  local url="$1" dest="$2"
  if [[ "$BASE" == *jsdelivr.net* ]]; then
    curl -fL --retry 3 --connect-timeout 20 -o "${dest}.new" "$url"
  else
    curl -fL --retry 3 --connect-timeout 20 -o "${dest}.new" "${url}?t=$(date +%s)"
  fi
  mv "${dest}.new" "$dest"
}

_get "${BASE}/analyze_pcap.py" "$HOME/analyze_pcap.py"
chmod +x "$HOME/analyze_pcap.py"
_get "${BASE}/probe_network.py" "$HOME/probe_network.py"
chmod +x "$HOME/probe_network.py"
_get "${BASE}/scripts/termux_signal.sh" "$HOME/signal"
chmod +x "$HOME/signal"

mkdir -p "$HOME/protocol_ast"
export PYTHONPATH="$HOME${PYTHONPATH:+:$PYTHONPATH}"
# Full helper set via curl (reliable; no chicken-egg with --self-update)
for f in \
  __init__.py aes_gcm.py tls_keylog.py pcapng_secrets.py find_keylog.py \
  http2.py hpack_decode.py signal.py body_peel.py json_api.py binary_peel.py \
  probe_loop.py stream_agent.py smart_probe.py active_probe.py stream_enrich.py \
  splitters.py tls_handshake.py pcap_analyze.py pcap_read.py deep_decode.py \
  align.py cluster.py sequitur.py parser.py serde.py pipeline.py ast_nodes.py \
  io_utils.py tcp_reassemble.py probe_env.py termux_update.py game_mine.py
do
  _get "${BASE}/protocol_ast/$f" "$HOME/protocol_ast/$f" || echo "⚠ skip $f"
done

# Optional second pass via Python (same SHA tip) — ignore failures
python3 "$HOME/analyze_pcap.py" --self-update 2>/dev/null || true

echo
python3 "$HOME/analyze_pcap.py" --version
test -f "$HOME/probe_network.py" && echo "probe_network.py: OK"

echo
echo "Готово. Універсальна команда:"
echo "  ~/signal"
echo
echo "Інше:"
echo "  ~/signal --stream"
echo "  python3 ~/analyze_pcap.py --self-update"
echo "  python3 ~/probe_network.py --loop 3 --no-capture"
echo
echo "НЕ запускай pkg у цьому скрипті — apt більше не чіпаємо."
