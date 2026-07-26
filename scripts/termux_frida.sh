#!/data/data/com.termux/files/usr/bin/bash
# Frida Gadget inject + autonomous SSL unpin (no root, no PC).
# Usage:
#   ~/frida              # pick APK from Download, inject, write *-frida.apk
#   ~/frida /path/app.apk
#   ~/frida guide
set -euo pipefail

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
HOME_DIR="${HOME:-$PREFIX/home}"
export PYTHONPATH="${HOME_DIR}${PYTHONPATH:+:$PYTHONPATH}"

DOWNLOADS=""
for cand in \
  "$HOME_DIR/storage/downloads" \
  "$HOME_DIR/storage/shared/Download" \
  "/sdcard/Download" \
  "/storage/emulated/0/Download"; do
  if [[ -d "$cand" ]]; then
    DOWNLOADS="$cand"
    break
  fi
done

banner() {
  cat <<'EOF'

╔══════════════════════════════════════════╗
║  ~/frida  —  Gadget + SSL unpin          ║
╚══════════════════════════════════════════╝

Без root / без ПК:
  APK → Frida Gadget (script mode) → ssl_unpin.js
  Java + native (BoringSSL/curl/mbedtls) hooks
  при старті гри — сам, без adb.

EOF
}

need_java() {
  if ! command -v java >/dev/null 2>&1; then
    echo "[*] Need OpenJDK for apktool / signer"
    echo "    Run once:  pkg install openjdk-17"
    if command -v pkg >/dev/null 2>&1; then
      pkg install -y openjdk-17 2>/dev/null || pkg install -y openjdk-21 2>/dev/null || true
    fi
  fi
  if ! command -v java >/dev/null 2>&1; then
    echo "Java still missing. Install openjdk then re-run ~/frida" >&2
    exit 1
  fi
}

pick_apk() {
  local arg="${1:-}"
  if [[ -n "$arg" && -f "$arg" ]]; then
    echo "$arg"
    return
  fi
  if [[ -z "$DOWNLOADS" ]]; then
    echo "Pass APK: ~/frida /path/to/game.apk" >&2
    exit 1
  fi
  mapfile -t apks < <(find "$DOWNLOADS" -maxdepth 2 -type f -iname '*.apk' 2>/dev/null | sort)
  if [[ ${#apks[@]} -eq 0 ]]; then
    cat <<EOF >&2
No APK in Downloads.

1) SAI / App Manager → extract com.lilithgame.hgame.gp
2) Copy .apk into Download/
3) ~/frida
EOF
    exit 1
  fi
  if [[ ${#apks[@]} -eq 1 ]]; then
    echo "${apks[0]}"
    return
  fi
  echo "Pick APK:"
  local i
  for i in "${!apks[@]}"; do
    printf "  %2d) %s\n" "$((i + 1))" "${apks[$i]}"
  done
  printf "Number: "
  read -r n
  if [[ ! "$n" =~ ^[0-9]+$ ]] || (( n < 1 || n > ${#apks[@]} )); then
    echo "Invalid" >&2
    exit 1
  fi
  echo "${apks[$((n - 1))]}"
}

main() {
  banner
  local cmd="${1:-}"
  case "$cmd" in
    -h|--help|help|guide|plan)
      python3 -m protocol_ast.frida_gadget --guide
      exit 0
      ;;
  esac

  need_java

  # Prefer module from $HOME (self-update); fall back to repo layout
  if [[ ! -f "$HOME_DIR/protocol_ast/frida_gadget.py" ]]; then
    echo "немає protocol_ast/frida_gadget.py — спочатку: ~/scan update" >&2
    exit 1
  fi

  local apk
  if [[ -n "$cmd" ]]; then
    apk="$(pick_apk "$cmd")"
  else
    apk="$(pick_apk "")"
  fi
  echo "[*] APK: $apk"
  echo "[*] Downloading Frida gadget / apktool on first run (large)…"
  echo

  python3 -m protocol_ast.frida_gadget "$apk"
}

main "$@"
