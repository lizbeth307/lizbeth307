#!/bin/sh
# Offline build into a NEW staging directory. Never runs sudo or host install.
set -eu
task_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
if [ "${1-}" = "--check" ] && [ "$#" -eq 1 ]; then
    exec python3 "$task_dir/vendor_patch.py" --check
fi
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 --check | rtlsdr|limesuiteng EXACT_CLEAN_CHECKOUT NEW_WORKDIR" >&2
    exit 2
fi
component=$1
source_dir=$2
work_dir=$3
case "$component" in rtlsdr|limesuiteng) ;; *) exit 2 ;; esac
case "$work_dir" in /*) ;; *) echo 'NEW_WORKDIR must be absolute' >&2; exit 2 ;; esac
[ ! -e "$work_dir" ] || { echo 'Output exists; refusing overwrite' >&2; exit 2; }
[ "$(id -u)" -ne 0 ] || { echo 'Build as an unprivileged user in an isolated builder, not host root' >&2; exit 2; }
offline() {
    # Stop if user/network namespaces are unavailable. There is no networked
    # fallback: CMake custom commands/ExternalProject must not fetch silently.
    unshare --user --map-root-user --net -- "$@"
}
if [ -f "$source_dir" ]; then
    python3 "$task_dir/vendor_patch.py" --component "$component" --archive "$source_dir" --output "$work_dir"
else
    python3 "$task_dir/vendor_patch.py" --component "$component" --source "$source_dir" --output "$work_dir"
fi
if [ "$component" = rtlsdr ]; then
    # The patch semantically reverts 7ebcb041f2ce887ef4d1a64607558889a86ff169:
    # restore SONAME2 explicitly, retaining all37 required public exports.
    offline cmake -S "$work_dir" -B "$work_dir/build" \
        -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/srrx-vendor \
        -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DENABLE_ZEROCOPY=OFF \
        -DDETACH_KERNEL_DRIVER=ON -DINSTALL_UDEV_RULES=OFF
    offline cmake --build "$work_dir/build" --target rtlsdr --parallel 4
    mkdir -p "$work_dir/rootfs/opt/srrx-vendor/lib"
    cp -a "$work_dir/build/src/"librtlsdr.so* "$work_dir/rootfs/opt/srrx-vendor/lib/"
    # No rtl_eeprom, rtl_biast or rtl_tcp executable is installed by this recipe.
    readelf -d "$work_dir/rootfs/opt/srrx-vendor/lib/librtlsdr.so.2" | grep -F 'Library soname: [librtlsdr.so.2]'
    if strings "$work_dir/rootfs/opt/srrx-vendor/lib/librtlsdr.so.2" | grep -i 'zero-copy'; then
        echo 'BLOCKED: zero-copy text present' >&2
        exit 2
    fi
    export_count=$(nm -D --defined-only "$work_dir/rootfs/opt/srrx-vendor/lib/librtlsdr.so.2" | awk '$3 ~ /^rtlsdr_/ {n++} END {print n+0}')
    [ "$export_count" -eq 37 ] || { echo 'BLOCKED: public API export count is not37' >&2; exit 2; }
    echo 'Candidate library staged. ARM64, EEPROM default-off and conducted V4L tests remain OPEN.'
    exit 0
fi
# These option names were read from the exact pinned upstream CMake sources.
offline cmake -S "$work_dir" -B "$work_dir/build" \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/srrx-vendor \
    -DFETCHCONTENT_FULLY_DISCONNECTED=ON -DBUILD_GUI=OFF -DBUILD_CLI=OFF \
    -DBUILD_DOCS=OFF -DENABLE_UNIT_TESTS=OFF -DBUILD_PLUGINS_AMARISOFT=OFF \
    -DBUILD_PLUGINS_GNURADIO=OFF -DBUILD_PLUGINS_HDSDR=OFF \
    -DBUILD_PLUGINS_SOAPYSDR=ON -DINSTALL_UDEV_RULES=OFF -DINSTALL_FIRMWARE=OFF
offline cmake --build "$work_dir/build" --parallel 4
offline env DESTDIR="$work_dir/rootfs" cmake --install "$work_dir/build"
echo 'Candidate staged only. Lime/native raw TX audit and arm64/hardware gates remain BLOCKED.'
