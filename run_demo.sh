#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH=.
python3 -m protocol_ast "$@"
echo
python3 -m unittest discover -s tests -v
