#!/data/data/com.termux/files/usr/bin/bash
# Universal living-signal entrypoint for Termux.
# Usage:  ~/signal
#         ~/signal --stream
#         ~/signal --mine
#         FLOW=TCP:443 ~/signal
set -euo pipefail
export PYTHONPATH="${HOME}${PYTHONPATH:+:$PYTHONPATH}"
FLOW="${FLOW:-TCP:443}"
if [[ "${1:-}" == "--mine" ]]; then
  shift
  exec python3 "$HOME/analyze_pcap.py" --mine --keylog auto "$@"
fi
exec python3 "$HOME/analyze_pcap.py" --signal --flow "$FLOW" --keylog auto "$@"
