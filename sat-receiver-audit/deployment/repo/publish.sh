#!/bin/sh
# Publish +labN .deb files as one signed aptly repository (deployment/repo/README.md).
# The same script serves the owner's offline key ceremony and CI; CI passes a throwaway
# test key that only exists in that job. The signing key is whatever GNUPGHOME holds for
# SIGNING_FINGERPRINT; this script never creates, exports or stores a private key.
# --mirror publishes srrx-mirror instead (the repo-policy.json mirror object): exactly the debs
# of the image package closure the policy names (each entry once, its size and SHA-256), signed
# by the same key; any other deb, a missing one or other bytes are refused before aptly runs.
# Usage: publish.sh [--mirror] NEW_ROOT_DIR SIGNING_FINGERPRINT DEB...
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
publication=srrx-lab
if [ "${1-}" = --mirror ]; then
    publication=srrx-mirror
    shift
fi
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 [--mirror] NEW_ROOT_DIR SIGNING_FINGERPRINT DEB..." >&2
    exit 2
fi
root=$1
fingerprint=$2
shift 2
case "$root" in /*) ;; *) echo 'NEW_ROOT_DIR must be absolute' >&2; exit 2 ;; esac
[ ! -e "$root" ] || { echo 'NEW_ROOT_DIR exists; refusing to reuse an aptly database' >&2; exit 2; }
printf '%s\n' "$fingerprint" | grep -Eq '^[0-9A-F]{40}$' || { echo 'SIGNING_FINGERPRINT must be 40 upper-case hex digits' >&2; exit 2; }
for deb in "$@"; do
    case "$publication:$deb" in
        srrx-lab:*+lab[1-9]*_arm64.deb|srrx-lab:*-0lab[1-9]*_arm64.deb) ;;
        srrx-mirror:*_arm64.deb|srrx-mirror:*_all.deb) ;;
        srrx-lab:*) echo "not a +labN arm64 package: $deb" >&2; exit 2 ;;
        *) echo "not an arm64 or all package: $deb" >&2; exit 2 ;;
    esac
    [ -f "$deb" ] || { echo "missing: $deb" >&2; exit 2; }
done
# One source for origin, label, codename, component and architecture: repo-policy.json (its mirror
# object for srrx-mirror). For srrx-mirror the debs must be exactly its contents file's packages.
# A failing check fails this assignment, and set -e stops the script.
names=$(python3 -B -I - "$repo_dir/repo-policy.json" "$publication" "$@" <<'EOF'
import hashlib, json, shlex, sys
from pathlib import Path
policy_path, publication, debs = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
policy = json.load(open(policy_path, encoding="utf-8"))
names = policy["mirror"] if publication == "srrx-mirror" else policy
if publication == "srrx-mirror":
    closure = json.load(open(policy_path.resolve().parents[2] / names["contents"], encoding="utf-8"))
    wanted = {Path(p["filename"]).name: (p["size"], p["sha256"]) for p in closure["packages"]}
    given = {}
    for deb in debs:
        digest = hashlib.sha256()
        with open(deb, "rb") as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b""):
                digest.update(chunk)
        given.setdefault(Path(deb).name, []).append((Path(deb).stat().st_size, digest.hexdigest()))
    foreign = sorted(set(given) - set(wanted))
    missing = sorted(set(wanted) - set(given))
    other = sorted(n for n in set(given) & set(wanted) if given[n] != [wanted[n]])
    if foreign or missing or other:
        sys.exit("not exactly the package closure %s: foreign %s, missing %s, repeated or other bytes %s"
                 % (names["contents"], foreign, missing, other))
for key in ("origin", "label", "codename", "component", "architecture"):
    print(key + "=" + shlex.quote(names[key]))
EOF
)
eval "$names"
mkdir -p "$root"
sed "s#@ROOT_DIR@#$root#" "$repo_dir/aptly.conf.template.json" > "$root/aptly.conf"
run_aptly() { aptly -config="$root/aptly.conf" "$@"; }
run_aptly repo create -distribution="$codename" -component="$component" -architectures="$architecture" "$publication"
run_aptly repo add "$publication" "$@"
snapshot="$publication-$(date -u +%Y%m%dT%H%M%SZ)"
run_aptly snapshot create "$snapshot" from repo "$publication"
# No Valid-Until (offline device, untrusted RTC): the release record pins the InRelease SHA-256.
run_aptly publish snapshot -batch -gpg-key="$fingerprint" -origin="$origin" -label="$label" \
    -distribution="$codename" -component="$component" -architectures="$architecture" \
    -skip-contents -skip-bz2 "$snapshot"
echo "Published $snapshot to $root/public (signing key $fingerprint)."
