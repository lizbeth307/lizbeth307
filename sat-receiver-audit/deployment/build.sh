#!/bin/sh
set -eu
task_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
if [ "${1-}" = "--check" ] && [ "$#" -eq 1 ]; then
    sh -n "$task_dir/build-vendor.sh"
    exec python3 "$task_dir/deploy.py" check
fi
if [ "${1-}" = "--stage" ] && [ "$#" -eq 2 ]; then
    exec python3 "$task_dir/deploy.py" stage --dest "$2"
fi
echo "Usage: $0 --check | --stage NEW_DIRECTORY" >&2
exit 2
