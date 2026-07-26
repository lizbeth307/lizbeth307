#!/data/data/com.termux/files/usr/bin/bash
# SIGNAL SCAN — універсальний сканер (меню / CLI)
# Usage:
#   ~/scan
#   ~/scan peel | mine | sdk | stream | update
set -euo pipefail
export PYTHONPATH="${HOME}${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$HOME/scan_app.py" "$@"
