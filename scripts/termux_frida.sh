#!/data/data/com.termux/files/usr/bin/bash
# Frida Gadget inject + autonomous SSL unpin (no root, no PC).
# Usage:
#   ~/frida                         # auto-pull AFK Arena if possible, else pick APK
#   ~/frida com.lilithgame.hgame.gp # pull package + inject
#   ~/frida /path/app.apk
#   ~/frida pull [package]
#   ~/frida guide
set -euo pipefail

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
HOME_DIR="${HOME:-$PREFIX/home}"
export PYTHONPATH="${HOME_DIR}${PYTHONPATH:+:$PYTHONPATH}"

DEFAULT_PKG="${FRIDA_PKG:-com.lilithgame.hgame.gp}"

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
    echo "[*] Need OpenJDK for apktool / signer" >&2
    echo "    Run once:  pkg install openjdk-17" >&2
    if command -v pkg >/dev/null 2>&1; then
      yes | pkg install -y openjdk-17 2>/dev/null || yes | pkg install -y openjdk-21 2>/dev/null || true
    fi
  fi
  if ! command -v java >/dev/null 2>&1; then
    echo "Java still missing. Install openjdk then re-run ~/frida" >&2
    exit 1
  fi
}

pm_paths() {
  local pkg="$1"
  if command -v pm >/dev/null 2>&1; then
    pm path "$pkg" 2>/dev/null | sed -n 's/^package://p'
    return 0
  fi
  if command -v cmd >/dev/null 2>&1; then
    cmd package path "$pkg" 2>/dev/null | sed -n 's/^package://p'
    return 0
  fi
  return 1
}

# Copy installed package APK(s). Progress → stderr; final base path → stdout.
pull_package() {
  local pkg="$1"
  local dest_dir="${2:-$DOWNLOADS}"
  if [[ -z "$dest_dir" ]]; then
    dest_dir="$HOME_DIR/unpin_work/pulled"
  fi
  mkdir -p "$dest_dir"

  echo "[*] pm path $pkg …" >&2
  mapfile -t paths < <(pm_paths "$pkg")
  if [[ ${#paths[@]} -eq 0 || -z "${paths[0]:-}" ]]; then
    echo "[!] Package not installed or pm unavailable: $pkg" >&2
    return 1
  fi

  local i=0 base="" copied=0
  local out_dir="$dest_dir/${pkg}_pulled"
  mkdir -p "$out_dir"
  for src in "${paths[@]}"; do
    i=$((i + 1))
    local name
    name="$(basename "$src")"
    local dst="$out_dir/$name"
    echo "    [$i] $src" >&2
    if [[ ! -r "$src" ]]; then
      echo "        ⚠ not readable (no root) — skip" >&2
      continue
    fi
    if cp -f "$src" "$dst" 2>/dev/null; then
      echo "        → $dst ($(wc -c <"$dst") bytes)" >&2
      copied=$((copied + 1))
      if [[ "$name" == "base.apk" || -z "$base" ]]; then
        base="$dst"
      fi
    else
      echo "        ⚠ cp failed" >&2
    fi
  done

  if [[ "$copied" -eq 0 || -z "$base" ]]; then
    cat <<EOF >&2
[!] Could not read APK from /data/app (common without root).

Do this instead:
  1) Install F-Droid → "App Manager" (or SAI / APK Extractor)
  2) Extract: $pkg
  3) Copy .apk into Download/
  4) ~/frida

Or if you already have an apk:
  ~/frida /sdcard/Download/your.apk
EOF
    return 1
  fi

  if [[ -n "$DOWNLOADS" ]]; then
    local nice="$DOWNLOADS/${pkg}.apk"
    cp -f "$base" "$nice"
    echo "[*] base → $nice" >&2
    base="$nice"
  fi

  if [[ "$copied" -gt 1 ]]; then
    echo >&2
    echo "[!] Split APK ($copied files) in: $out_dir" >&2
    echo "    After inject: install ALL splits via SAI (same signing key)." >&2
  fi
  echo "$base"
  return 0
}

find_apks() {
  local roots=()
  [[ -n "$DOWNLOADS" ]] && roots+=("$DOWNLOADS")
  roots+=(
    "$HOME_DIR/storage/shared/Download"
    "$HOME_DIR/storage/downloads"
    "$HOME_DIR/unpin_work"
    "/sdcard/Download"
    "/storage/emulated/0/Download"
  )
  local r
  for r in "${roots[@]}"; do
    [[ -d "$r" ]] || continue
    find "$r" -maxdepth 3 -type f -iname '*.apk' 2>/dev/null
  done | sort -u
}

looks_like_pkg() {
  # com.foo.bar — not a path, not a flag
  [[ "$1" == *.* && "$1" != *.apk && "$1" != /* && "$1" != ~/* && "$1" != -* ]]
}

pick_apk() {
  local arg="${1:-}"
  if [[ -n "$arg" && -f "$arg" ]]; then
    echo "$arg"
    return
  fi

  if [[ -n "$arg" ]] && looks_like_pkg "$arg"; then
    pull_package "$arg"
    return
  fi

  mapfile -t apks < <(find_apks)
  if [[ ${#apks[@]} -eq 0 ]]; then
    echo "[*] No APK in Download — trying pm pull $DEFAULT_PKG …" >&2
    if pull_package "$DEFAULT_PKG"; then
      return
    fi
    cat <<EOF >&2

Немає APK. Зроби ОДИН з варіантів:

A) Авто (якщо система дає читати base.apk):
   ~/frida pull $DEFAULT_PKG
   ~/frida

B) Вручну (надійніше):
   1. F-Droid → App Manager
   2. Знайти AFK Arena ($DEFAULT_PKG)
   3. ☰ → Save APK set / Export → Download/
   4. ~/frida

C) Якщо APK уже є:
   ~/frida /sdcard/Download/name.apk
EOF
    exit 1
  fi

  if [[ ${#apks[@]} -eq 1 ]]; then
    echo "${apks[0]}"
    return
  fi
  echo "Pick APK:" >&2
  local i
  for i in "${!apks[@]}"; do
    printf "  %2d) %s\n" "$((i + 1))" "${apks[$i]}" >&2
  done
  printf "Number: " >&2
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
    pull)
      pull_package "${2:-$DEFAULT_PKG}" >/dev/null
      echo >&2
      echo "Далі:  ~/frida" >&2
      exit 0
      ;;
  esac

  need_java

  if [[ ! -f "$HOME_DIR/protocol_ast/frida_gadget.py" ]]; then
    echo "немає protocol_ast/frida_gadget.py — спочатку: ~/scan update" >&2
    exit 1
  fi

  local apk
  apk="$(pick_apk "$cmd")"
  echo "[*] APK: $apk"
  echo "[*] Downloading Frida gadget / apktool on first run (large)…"
  echo

  python3 -m protocol_ast.frida_gadget "$apk"
  echo
  echo "════════════════════════════════════════"
  echo "Далі на телефоні:"
  echo "  1) Settings → Apps → AFK Arena → Uninstall"
  echo "  2) Files → Download → встанови *-frida.apk"
  echo "     (якщо split — SAI: усі apk з *_pulled + signed)"
  echo "  3) PCAPdroid: target=гра, TLS decrypt ON, Block QUIC"
  echo "  4) Увійди 30–60с → Stop → export pcap+keylog"
  echo "  5) ~/scan mine   ← дивись OPEN vs SEALED"
  echo "════════════════════════════════════════"
}

main "$@"
