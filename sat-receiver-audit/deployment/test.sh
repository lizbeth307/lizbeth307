#!/bin/sh
set -eu
task_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
# A release builder must compile the inserted RTL/Lime guards; a skipped guard test is not evidence.
if [ "${SRRX_RELEASE_BUILDER-}" = 1 ]; then
    for compiler in cc g++; do
        command -v "$compiler" >/dev/null 2>&1 || { echo "BLOCKED: release builder lacks $compiler for guard tests" >&2; exit 2; }
    done
fi
exec python3 -m unittest discover -s "$task_dir/tests" -p 'test_*.py' -v
