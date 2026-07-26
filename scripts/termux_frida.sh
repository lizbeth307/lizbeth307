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
    echo "[*] Need OpenJDK for apktool / signer"
    echo "    Run once:  pkg install openjdk-17"
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

# Copy installed package APK(s) into Downloads (works when base.apk is world-readable).
pull_package() {
  local pkg="$1"
  local dest_dir="${2:-$DOWNLOADS}"
  if [[ -z "$dest_dir" ]]; then
    dest_dir="$HOME_DIR/unpin_work/pulled"
  fi
  mkdir -p "$dest_dir"

  echo "[*] pm path $pkg …"
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
    echo "    [$i] $src"
    if [[ ! -r "$src" ]]; then
      echo "        ⚠ not readable (no root) — skip" >&2
      continue
    fi
    if cp -f "$src" "$dst" 2>/dev/null; then
      echo "        → $dst ($(wc -c <"$dst") bytes)"
      copied=$((copied + 1))
      if [[ "$name" == "base.apk" || "$i" -eq 1 ]]; then
        base="$dst"
      fi
    else
      echo "        ⚠ cp failed" >&2
    fi
  done

  if [[ "$copied" -eq 0 ]]; then
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

  # Convenience copy of base into Downloads root
  if [[ -n "$base" && -n "$DOWNLOADS" ]]; then
    local nice="$DOWNLOADS/${pkg}.apk"
    cp -f "$base" "$nice"
    echo "[*] base → $nice"
    echo "$nice"
  else
    echo "$base"
  fi

  if [[ "$copied" -gt 1 ]]; then
    echo
    echo "[!] Split APK ($copied files) in: $out_dir"
    echo "    Patching base only; after ~/frida finishes, install via SAI:"
    echo "    all re-signed apks from the output folder (same key)."
  fi
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
    find "$r" -maxdepth 3 -type f \( -iname '*.apk' -o -iname '*.apks' \) 2>/dev/null
  done | sort -u
}

pick_apk() {
  local arg="${1:-}"
  if [[ -n "$arg" && -f "$arg" ]]; then
    echo "$arg"
    return
  fi

  # Package name → pull
  if [[ -n "$arg" && "$arg" == *.* && "$arg" != *.apk && "$arg" != /* && "$arg" != ~* ]]; then
    local pulled
    pulled="$(pull_package "$arg")" || exit 1
    # last line is path
    echo "$pulled" | tail -n1
    return
  fi

  mapfile -t apks < <(find_apks)
  # Prefer non -frida / non -unpinned originals first in UI, but list all
  if [[ ${#apks[@]} -eq 0 ]]; then
    echo "[*] No APK in Download — trying pm pull $DEFAULT_PKG …"
    local pulled
    if pulled="$(pull_package "$DEFAULT_PKG")"; then
      echo "$pulled" | tail -n1
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
    pull)
      need_java
      pull_package "${2:-$DEFAULT_PKG}" >/dev/null
      echo
      echo "Далі:  ~/frida"
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
