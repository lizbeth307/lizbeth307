#!/data/data/com.termux/files/usr/bin/bash
# No-root SSL pinning bypass helper for Termux + PCAPdroid.
# Uses apk-mitm (Java TrustManager / OkHttp / network-security-config).
# Does NOT defeat native/Unity custom pins by itself.
set -euo pipefail

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
HOME_DIR="${HOME:-$PREFIX/home}"
WORKDIR="${UNPIN_WORKDIR:-$HOME_DIR/unpin_work}"
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

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing: $1" >&2
    echo "Run: pkg install $2" >&2
    exit 1
  }
}

banner() {
  cat <<'EOF'

╔══════════════════════════════════════════╗
║   ~/unpin  —  pin bypass без root        ║
╚══════════════════════════════════════════╝

Реалістичний шлях для AFK Arena / Lilith:

  1) apk-mitm патчить Java SSL pinning у APK
  2) ставиш patched APK (можеш зняти стару гру)
  3) PCAPdroid MITM + новий keylog
  4) ~/scan mine  → дивись OPEN vs SEALED

ВАЖЛИВО:
  • Java / OkHttp / network-security-config  → apk-mitm часто знімає
  • Unity IL2CPP / native BoringSSL pin     → apk-mitm НЕ знімає
    тоді:  ~/frida   (Gadget + ssl_unpin.js, без ПК)

EOF
}

ensure_tools() {
  need node nodejs
  need npm nodejs
  if ! command -v apk-mitm >/dev/null 2>&1; then
    echo "[*] Installing apk-mitm (npm -g)…"
    npm install -g apk-mitm
  fi
  # apk-mitm shells out to apktool / uber-apk-signer via its deps;
  # Java helps when local jars are used.
  if ! command -v java >/dev/null 2>&1; then
    echo "[*] Installing openjdk-17 (apk-mitm may need it)…"
    pkg install -y openjdk-17 2>/dev/null || pkg install -y openjdk-21 2>/dev/null || true
  fi
}

pick_apk() {
  local arg="${1:-}"
  if [[ -n "$arg" && -f "$arg" ]]; then
    echo "$arg"
    return
  fi
  if [[ -z "$DOWNLOADS" ]]; then
    echo "Downloads folder not found. Pass APK path: ~/unpin /path/to/game.apk" >&2
    exit 1
  fi
  echo "[*] Looking for APKs in $DOWNLOADS …"
  mapfile -t apks < <(find "$DOWNLOADS" -maxdepth 2 -type f -iname '*.apk' 2>/dev/null | sort)
  if [[ ${#apks[@]} -eq 0 ]]; then
    cat <<EOF >&2
No APK in Downloads.

How to get APK without root:
  1) Install "SAI" / "App Manager" / "APK Extractor" from Play/F-Droid
  2) Extract: com.lilithgame.hgame.gp  (AFK Arena)
  3) Copy .apk (and .apks/.xapk if split) into Download/
  4) Run:  ~/unpin

Or pass path:
  ~/unpin /sdcard/Download/AFKArena.apk
EOF
    exit 1
  fi
  if [[ ${#apks[@]} -eq 1 ]]; then
    echo "${apks[0]}"
    return
  fi
  echo
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

pick_ca() {
  # Optional PCAPdroid CA → apk-mitm --certificate
  local ca=""
  if [[ -n "${1:-}" && -f "$1" ]]; then
    echo "$1"
    return
  fi
  if [[ -z "$DOWNLOADS" ]]; then
    echo ""
    return
  fi
  local roots=("$DOWNLOADS")
  [[ -d "$DOWNLOADS/PCAPdroid" ]] && roots+=("$DOWNLOADS/PCAPdroid")
  mapfile -t cas < <(
    find "${roots[@]}" -maxdepth 2 -type f \
      \( -iname '*.pem' -o -iname '*.crt' -o -iname '*certificate*' \) \
      2>/dev/null | sort -u
  )
  if [[ ${#cas[@]} -eq 0 ]]; then
    echo ""
    return
  fi
  echo
  echo "Optional: PCAPdroid CA to bake into the APK"
  echo "  (PCAPdroid → Decryption → Export certificate → Download)"
  echo "  0) skip (use user-installed CA / apk-mitm default)"
  local i
  for i in "${!cas[@]}"; do
    printf "  %2d) %s\n" "$((i + 1))" "${cas[$i]}"
  done
  printf "Number [0]: "
  read -r n
  n="${n:-0}"
  if [[ "$n" == "0" ]]; then
    echo ""
    return
  fi
  if [[ ! "$n" =~ ^[0-9]+$ ]] || (( n < 1 || n > ${#cas[@]} )); then
    echo ""
    return
  fi
  echo "${cas[$((n - 1))]}"
}

run_mitm() {
  local apk="$1"
  local ca="${2:-}"
  mkdir -p "$WORKDIR"
  local base
  base="$(basename "$apk" .apk)"
  base="${base%.APK}"
  local out_dir="$WORKDIR/${base}_mitm_$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$out_dir"
  cp -f "$apk" "$out_dir/"
  local local_apk="$out_dir/$(basename "$apk")"

  echo
  echo "[*] apk-mitm → $out_dir"
  echo "    (може зайняти кілька хвилин на телефоні)"
  echo

  (
    cd "$out_dir"
    if [[ -n "$ca" ]]; then
      apk-mitm "$(basename "$local_apk")" --certificate "$ca"
    else
      apk-mitm "$(basename "$local_apk")"
    fi
  )

  local patched
  patched="$(find "$out_dir" -maxdepth 2 -type f -iname '*-patched.apk' | head -n1 || true)"
  if [[ -z "$patched" ]]; then
    patched="$(find "$out_dir" -maxdepth 2 -type f -iname '*.apk' ! -name "$(basename "$apk")" | head -n1 || true)"
  fi

  if [[ -z "$patched" || ! -f "$patched" ]]; then
    echo "[!] Patched APK not found in $out_dir" >&2
    echo "    Check apk-mitm log above." >&2
    exit 1
  fi

  local dest=""
  if [[ -n "$DOWNLOADS" ]]; then
    dest="$DOWNLOADS/${base}-unpinned.apk"
    cp -f "$patched" "$dest"
  else
    dest="$patched"
  fi

  cat <<EOF

════════════════════════════════════════
DONE (Java-layer unpin attempt)
════════════════════════════════════════
Patched APK:
  $dest

NEXT (телефон, без root):
  1) Settings → Apps → AFK Arena → Uninstall
     (або постав поверх, якщо підпис збігається — рідко)
  2) Files → Download → встанови ${base}-unpinned.apk
     (Allow unknown sources)
  3) PCAPdroid:
       • Target = patched AFK Arena
       • TLS decryption = ON
       • Block QUIC = ON (бажано)
  4) Увійди в гру 30–60 с → Stop → export pcap + keylog
  5) Termux:
       ~/scan mine

Очікуй у звіті:
  • було SEALED (app-global*, vip-api*, psp-api*) → стало OPEN
    = Java pin знято, MITM працює
  • досі SEALED + малий appdata
    = pin у Unity/native → потрібен Frida Gadget (скажи — додамо крок)

EOF
  echo "$dest" >"$WORKDIR/last_patched.txt"
}

guide_only() {
  cat <<'EOF'

═══ План pin bypass без root (коротко) ═══

A. Швидкий експеримент (рекомендовано зараз)
   ~/unpin
   → apk-mitm патчить APK
   → ставиш -unpinned.apk
   → PCAPdroid MITM + ~/scan mine

B. Якщо app-global* лишається SEALED
   Pin сидить у native/Unity, не в Java.
   →  ~/frida
      (вшиває Frida Gadget 16.7.19 + ssl_unpin.js у script-режимі;
       Java + BoringSSL/curl/mbedtls hooks без adb/ПК)
   Потім знову PCAPdroid MITM + ~/scan mine.

C. Що НЕ треба для цього флоу
   • Magisk / LSPosed / JustTrustMe  (потрібен root)
   • USB debugging на ПК

D. Що вже OPEN без unpin (з твого mine)
   Lilith SDK login/heartbeat, SLS token, CrashSight, FB, Adjust
   → sdk_session.json уже повний

E. Навіщо тоді unpin
   Щоб дістати game API (баги/бій/инвентар) з app-global* / vip-api*

EOF
}

main() {
  banner
  local cmd="${1:-}"
  case "$cmd" in
    -h|--help|help|guide|plan)
      guide_only
      exit 0
      ;;
  esac

  ensure_tools
  local apk ca
  if [[ -n "$cmd" && "$cmd" != "run" ]]; then
    apk="$(pick_apk "$cmd")"
  else
    apk="$(pick_apk "")"
  fi
  echo "[*] APK: $apk"
  ca="$(pick_ca "")"
  if [[ -n "$ca" ]]; then
    echo "[*] CA:  $ca"
  else
    echo "[*] CA:  (none — install PCAPdroid CA as user cert, or re-run with export)"
  fi
  run_mitm "$apk" "$ca"
}

main "$@"
