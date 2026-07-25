#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== demo ==="
python3 discover_protocol_ast.py demo --count 40 --show 2

echo
echo "=== gen-corpus + discover + parse ==="
python3 discover_protocol_ast.py gen-corpus -o /tmp/corpus.hex --count 30
python3 discover_protocol_ast.py discover -i /tmp/corpus.hex -o /tmp/format.json --show 1
python3 discover_protocol_ast.py parse -f /tmp/format.json -i /tmp/corpus.hex --show 1

echo
echo "=== online ==="
python3 discover_protocol_ast.py online --count 50 --refine-every 10

echo
echo "=== tests ==="
python3 discover_protocol_ast.py test
