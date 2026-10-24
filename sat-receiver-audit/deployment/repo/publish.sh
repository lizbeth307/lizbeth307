#!/bin/sh
# Publish +labN .deb files as one signed aptly repository (deployment/repo/README.md).
# The same script serves the owner's offline key ceremony and CI; CI passes a throwaway
# test key that only exists in that job. The signing key is whatever GNUPGHOME holds for
# SIGNING_FINGERPRINT; this script never creates, exports or stores a private key.
# Usage: publish.sh NEW_ROOT_DIR SIGNING_FINGERPRINT DEB...
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 NEW_ROOT_DIR SIGNING_FINGERPRINT DEB..." >&2
    exit 2
fi
root=$1
fingerprint=$2
shift 2
case "$root" in /*) ;; *) echo 'NEW_ROOT_DIR must be absolute' >&2; exit 2 ;; esac
[ ! -e "$root" ] || { echo 'NEW_ROOT_DIR exists; refusing to reuse an aptly database' >&2; exit 2; }
printf '%s\n' "$fingerprint" | grep -Eq '^[0-9A-F]{40}$' || { echo 'SIGNING_FINGERPRINT must be 40 upper-case hex digits' >&2; exit 2; }
for deb in "$@"; do
    case "$deb" in *+lab[1-9]*_arm64.deb|*-0lab[1-9]*_arm64.deb) ;; *) echo "not a +labN arm64 package: $deb" >&2; exit 2 ;; esac
    [ -f "$deb" ] || { echo "missing: $deb" >&2; exit 2; }
done
# One source for origin, label, codename, component and architecture: repo-policy.json.
eval "$(python3 -B -I - "$repo_dir/repo-policy.json" <<'EOF'
import json, shlex, sys
policy = json.load(open(sys.argv[1], encoding="utf-8"))
for key in ("origin", "label", "codename", "component", "architecture"):
    print(key + "=" + shlex.quote(policy[key]))
EOF
)"
mkdir -p "$root"
sed "s#@ROOT_DIR@#$root#" "$repo_dir/aptly.conf.template.json" > "$root/aptly.conf"
run_aptly() { aptly -config="$root/aptly.conf" "$@"; }
run_aptly repo create -distribution="$codename" -component="$component" -architectures="$architecture" srrx-lab
run_aptly repo add srrx-lab "$@"
snapshot="srrx-lab-$(date -u +%Y%m%dT%H%M%SZ)"
run_aptly snapshot create "$snapshot" from repo srrx-lab
# No Valid-Until (offline device, untrusted RTC): the release record pins the InRelease SHA-256.
run_aptly publish snapshot -batch -gpg-key="$fingerprint" -origin="$origin" -label="$label" \
    -distribution="$codename" -component="$component" -architectures="$architecture" \
    -skip-contents -skip-bz2 "$snapshot"
echo "Published $snapshot to $root/public (signing key $fingerprint)."
