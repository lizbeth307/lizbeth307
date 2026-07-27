#!/data/data/com.termux/files/usr/bin/bash
# Frida Gadget inject + autonomous SSL unpin (no root, no PC).
# Usage:
#   ~/frida                              # pick APK / .apks (deduped list)
#   ~/frida "/sdcard/AppManager/apks/AFK Arena_1.198.01.apks"
#   ~/frida doctor [probe|java|java-tm|native]   # update→build→install→wait log
#   ~/frida pull [package]
#   ~/frida pkgs                         # list lilith/hgame packages via /system/bin/pm
#   ~/frida guide
set -euo pipefail

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
HOME_DIR="${HOME:-$PREFIX/home}"
export PYTHONPATH="${HOME_DIR}${PYTHONPATH:+:$PYTHONPATH}"
# Android tools often live here; Termux PATH usually omits them.
export PATH="/system/bin:/system/xbin:${PATH}"

DEFAULT_PKG="${FRIDA_PKG:-com.lilithgame.hgame.gp}"
DEFAULT_SOURCE_APKS="${FRIDA_SOURCE_APKS:-/sdcard/AppManager/apks/AFK Arena_1.198.01.apks}"
LOG_NAME="frida-unpin.log"

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
  APK / .apks → Frida Gadget (script mode) → ssl_unpin.js

AFK Arena (splits):
  ~/frida doctor              # update → java pin → install → wait log
  ~/frida "/sdcard/AppManager/apks/AFK Arena_1.198.01.apks" java

Якщо No space left:
  rm -rf ~/unpin_work /sdcard/unpin_work
  # робота йде на /sdcard (більше місця)

EOF
}

need_tools() {
  local need_pkg=()
  command -v java >/dev/null 2>&1 || need_pkg+=(openjdk-17)
  command -v patchelf >/dev/null 2>&1 || need_pkg+=(patchelf)
  command -v zip >/dev/null 2>&1 || need_pkg+=(zip)
  # aapt optional if patchelf works; still handy as apktool fallback
  if ! command -v aapt2 >/dev/null 2>&1 && ! command -v aapt >/dev/null 2>&1; then
    need_pkg+=(aapt aapt2)
  fi
  if [[ ${#need_pkg[@]} -gt 0 ]]; then
    echo "[*] Installing: ${need_pkg[*]}" >&2
    if command -v pkg >/dev/null 2>&1; then
      yes | pkg install -y "${need_pkg[@]}" 2>/dev/null || true
    fi
  fi
  if ! command -v java >/dev/null 2>&1; then
    echo "Java still missing: pkg install openjdk-17" >&2
    exit 1
  fi
  if ! command -v patchelf >/dev/null 2>&1; then
    echo "[!] patchelf missing — apktool fallback needs: pkg install patchelf aapt aapt2" >&2
  fi
}

# Resolve pm/cmd from system image (Termux rarely has them on PATH alone).
pm_bin() {
  local c
  for c in pm /system/bin/pm /system/xbin/pm; do
    if [[ -x "$c" ]] || command -v "$c" >/dev/null 2>&1; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

cmd_bin() {
  local c
  for c in cmd /system/bin/cmd; do
    if [[ -x "$c" ]] || command -v "$c" >/dev/null 2>&1; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

pm_paths() {
  local pkg="$1" out="" bin
  if bin="$(pm_bin)"; then
    out="$("$bin" path "$pkg" 2>/dev/null | sed -n 's/^package://p' || true)"
  fi
  if [[ -z "$out" ]] && bin="$(cmd_bin)"; then
    out="$("$bin" package path "$pkg" 2>/dev/null | sed -n 's/^package://p' || true)"
  fi
  if [[ -n "$out" ]]; then
    printf '%s\n' "$out"
    return 0
  fi
  return 1
}

list_game_packages() {
  local bin out=""
  if bin="$(pm_bin)"; then
    out="$("$bin" list packages 2>/dev/null || true)"
  fi
  if [[ -z "$out" ]] && bin="$(cmd_bin)"; then
    out="$("$bin" package list packages 2>/dev/null || true)"
  fi
  if [[ -z "$out" ]]; then
    echo "[!] pm/cmd недоступний у цьому Termux (немає /system/bin/pm)." >&2
    echo "    Тоді: App Manager → Save APK, або напряму:" >&2
    echo "    ~/frida \"/sdcard/Download/777.apk\"" >&2
    return 1
  fi
  echo "$out" | sed -n 's/^package://p' | grep -iE 'lilith|hgame|afk|arena' || true
  echo "── усі пакети з 'game' (уривок) ──" >&2
  echo "$out" | sed -n 's/^package://p' | grep -i game | head -n 40 >&2 || true
}

pull_package() {
  local pkg="$1"
  local dest_dir="${2:-$DOWNLOADS}"
  if [[ -z "$dest_dir" ]]; then
    dest_dir="$HOME_DIR/unpin_work/pulled"
  fi
  mkdir -p "$dest_dir"

  echo "[*] pm path $pkg …" >&2
  mapfile -t paths < <(pm_paths "$pkg" || true)
  if [[ ${#paths[@]} -eq 0 || -z "${paths[0]:-}" ]]; then
    echo "[!] Пакет не знайдено / pm недоступний: $pkg" >&2
    echo "    Спробуй:  ~/frida pkgs" >&2
    echo "    (може інший package name, або гру знято)" >&2
    return 1
  fi

  local i=0 base="" copied=0
  local out_dir="$dest_dir/${pkg}_pulled"
  mkdir -p "$out_dir"
  for src in "${paths[@]}"; do
    i=$((i + 1))
    local name dst
    name="$(basename "$src")"
    dst="$out_dir/$name"
    echo "    [$i] $src" >&2
    if [[ ! -r "$src" ]]; then
      echo "        ⚠ not readable — skip" >&2
      continue
    fi
    if cp -f "$src" "$dst" 2>/dev/null; then
      echo "        → $dst ($(wc -c <"$dst") bytes)" >&2
      copied=$((copied + 1))
      if [[ "$name" == "base.apk" || -z "$base" ]]; then
        base="$dst"
      fi
    fi
  done

  if [[ "$copied" -eq 0 || -z "$base" ]]; then
    cat <<EOF >&2
[!] /data/app не читається без root.

App Manager → Save APK set для гри → Download/
або вкажи файл:
  ~/frida "/sdcard/Download/777.apk"
EOF
    return 1
  fi

  if [[ -n "$DOWNLOADS" ]]; then
    local nice="$DOWNLOADS/${pkg}.apk"
    cp -f "$base" "$nice"
    echo "[*] base → $nice" >&2
    base="$nice"
  fi
  echo "$base"
}

# Deduplicate the same APK/.apks seen via /sdcard vs /storage/emulated/0 vs Termux shared.
find_apks() {
  python3 - <<'PY'
import os
from pathlib import Path

home = Path(os.environ.get("HOME", str(Path.home())))
roots = [
    Path("/sdcard/AppManager/apks"),
    Path("/storage/emulated/0/AppManager/apks"),
    home / "storage" / "downloads",
    home / "storage" / "shared" / "Download",
    home / "unpin_work",
    Path("/sdcard/Download"),
    Path("/storage/emulated/0/Download"),
]
junk = {
    "f-droid.apk",
    "telegram.apk",
    "com.termux.api_1001.apk",
    "pcapdroid-mitm_v1.4_arm64-v8a.apk",
    "porcupine demo_2.1.0_apkpure.apk",
}
seen = {}
cands = []
patterns = ("*.apk", "*.apks", "*.xapk", "*.apkm")
for root in roots:
    if not root.is_dir():
        continue
    for pat in patterns:
        for p in root.rglob(pat):
            if not p.is_file():
                continue
            if p.name.lower() in junk:
                continue
            if "pcapdroid" in p.name.lower() and "mitm" in p.name.lower():
                continue
            # skip our own output aliases to avoid re-inject loops in picker
            low = p.name.lower()
            if low in ("afk-arena-frida.apk", "afk-arena-frida.apks"):
                continue
            if "-frida.apk" in low or "-frida.apks" in low or "-frida.unsigned.apk" in low:
                continue
            if "frida-splits" in str(p).lower():
                continue
            try:
                st = p.stat()
                key = (st.st_ino, st.st_dev, st.st_size)
            except OSError:
                continue
            if key in seen:
                continue
            seen[key] = p
            cands.append(p)

def score(p: Path) -> tuple:
    name = p.name.lower()
    try:
        from protocol_ast.frida_gadget import apk_quick_info
        inf = apk_quick_info(p)
    except Exception:
        inf = {"il2cpp": False, "hint": "", "size": p.stat().st_size, "bundle": False}
    # prefer AFK Arena .apks / unity/lilith/large
    pri = 0
    if inf.get("bundle") or name.endswith((".apks", ".xapk", ".apkm")):
        pri += 120
    if inf.get("il2cpp"):
        pri += 100
    hint = (inf.get("hint") or "").lower()
    if "lilith" in hint or "hgame" in hint or "afk" in hint:
        pri += 90
    if "lilith" in name or "hgame" in name or "afk" in name:
        pri += 80
    if "appmanager" in str(p).lower():
        pri += 50
    if name.startswith("777"):
        pri -= 40  # slots777 — not AFK Arena
    if name.startswith("sc_"):
        pri += 10
    return (-pri, -inf.get("size", 0), name)

cands.sort(key=score)
for p in cands:
    print(p)
PY
}

looks_like_pkg() {
  [[ "$1" == *.* && "$1" != *.apk && "$1" != *.apks && "$1" != *.xapk && "$1" != *.apkm && "$1" != /* && "$1" != ~/* && "$1" != -* ]]
}

describe_apk() {
  python3 -c "from pathlib import Path; import sys; from protocol_ast.frida_gadget import format_apk_choice; print(format_apk_choice(Path(sys.argv[1])))" "$1" 2>/dev/null \
    || echo "$(basename "$1")"
}

pick_apk() {
  local arg="${1:-}"
  # Direct path (quote spaces) or directory of splits
  if [[ -n "$arg" && -e "$arg" ]]; then
    echo "$arg"
    return
  fi
  if [[ -n "$arg" ]] && looks_like_pkg "$arg"; then
    pull_package "$arg"
    return
  fi

  mapfile -t apks < <(find_apks)
  if [[ ${#apks[@]} -eq 0 ]]; then
    echo "[*] Немає APK — pm pull $DEFAULT_PKG …" >&2
    if pull_package "$DEFAULT_PKG"; then
      return
    fi
    cat <<EOF >&2

Немає APK/.apks гри. Зроби:

  App Manager → AFK Arena → ⋮ → Share / Save APK
  ~/frida "/sdcard/AppManager/apks/AFK Arena_1.198.01.apks"
EOF
    exit 1
  fi

  if [[ ${#apks[@]} -eq 1 ]]; then
    echo "${apks[0]}"
    return
  fi

  echo "Pick APK / .apks (AFK Arena .apks і IL2CPP зверху):" >&2
  local i desc
  for i in "${!apks[@]}"; do
    desc="$(describe_apk "${apks[$i]}")"
    printf "  %2d) %s\n" "$((i + 1))" "$desc" >&2
    printf "      %s\n" "${apks[$i]}" >&2
  done
  echo >&2
  echo "Підказка: бери файл з AppManager/apks і тегом APKS×3 / IL2CPP / afk-arena." >&2
  echo "Або:  ~/frida \"/sdcard/AppManager/apks/AFK Arena_1.198.01.apks\"" >&2
  printf "Number: " >&2
  # read may fail / empty in weird TTYs
  n=""
  read -r n || true
  n="${n//[$'\t\r\n ']/}"
  if [[ -z "$n" ]]; then
    echo "Empty choice. Приклад: ~/frida \"/sdcard/AppManager/apks/AFK Arena_1.198.01.apks\"" >&2
    exit 1
  fi
  if [[ ! "$n" =~ ^[0-9]+$ ]] || (( n < 1 || n > ${#apks[@]} )); then
    echo "Invalid: '$n'  (треба число 1–${#apks[@]})" >&2
    echo "Або шлях: ~/frida \"/sdcard/AppManager/apks/AFK Arena_1.198.01.apks\"" >&2
    exit 1
  fi
  echo "${apks[$((n - 1))]}"
}

open_frida_install() {
  local hint="${1:-}"
  local target=""
  local opened=0

  if [[ -n "$hint" && -e "$hint" ]]; then
    target="$hint"
  else
    target="$(
      python3 - <<'PY'
from protocol_ast.frida_gadget import find_frida_install_targets
cands = find_frida_install_targets()
# prefer splits folder (multi-split) over .apks for installer UX
for c in cands:
    if c.get("kind") == "splits":
        print(c["path"])
        raise SystemExit(0)
for c in cands:
    if c.get("kind") == "apks":
        print(c["path"])
        raise SystemExit(0)
if cands:
    print(cands[0]["path"])
PY
    )"
  fi

  if [[ -z "$target" ]]; then
    local cand
    cand="$(ls -td /sdcard/Download/*-frida-splits /storage/emulated/0/Download/*-frida-splits 2>/dev/null | head -n1 || true)"
    if [[ -n "$cand" && -d "$cand" ]]; then
      target="$cand"
    else
      cand="$(ls -t /sdcard/Download/*-frida.apks /storage/emulated/0/Download/*-frida.apks 2>/dev/null | head -n1 || true)"
      if [[ -n "$cand" && -f "$cand" ]]; then
        target="$cand"
      fi
    fi
  fi

  if [[ -z "$target" || ! -e "$target" ]]; then
    cat <<EOF >&2
[!] Не знайдено патчений AFK Arena.

Спочатку:
  ~/frida "/sdcard/AppManager/apks/AFK Arena_1.198.01.apks"

Потім:
  ~/frida install
EOF
    return 1
  fi

  echo "[*] знайдено: $target" >&2
  if [[ -d "$target" ]]; then
    echo "[*] splits у папці:" >&2
    ls -lah "$target"/*.apk 2>/dev/null | sed 's/^/    /' >&2 || true
  fi
  echo >&2
  echo "⚠  Зніми стару AFK Arena (якщо ще стоїть)." >&2
  echo "   App Manager / SAI → постав УСІ .apk зі splits." >&2
  echo >&2

  try_open_path() {
    local p="$1"
    if command -v termux-open >/dev/null 2>&1; then
      echo "[*] termux-open \"$p\"" >&2
      if termux-open "$p" 2>/dev/null; then
        return 0
      fi
      # some Termux:API builds need chooser
      if termux-open --chooser "$p" 2>/dev/null; then
        return 0
      fi
    fi
    local uri="file://${p}"
    local starter
    for starter in am /system/bin/am; do
      if [[ -x "$starter" ]] || command -v "$starter" >/dev/null 2>&1; then
        echo "[*] $starter VIEW $p" >&2
        if "$starter" start -a android.intent.action.VIEW -d "$uri" \
          -t "resource/folder" >/dev/null 2>&1; then
          return 0
        fi
        if "$starter" start -a android.intent.action.VIEW -d "$uri" \
          -t "application/vnd.android.package-archive" >/dev/null 2>&1; then
          return 0
        fi
        if "$starter" start -a android.intent.action.VIEW -d "$uri" \
          -t "application/octet-stream" >/dev/null 2>&1; then
          return 0
        fi
        if "$starter" start -a android.intent.action.VIEW -d "$uri" \
          -n io.github.muntashirakon.AppManager/.apk.installer.PackageInstallerActivity \
          >/dev/null 2>&1; then
          return 0
        fi
      fi
    done
    return 1
  }

  if try_open_path "$target"; then
    opened=1
  fi

  # If we opened .apks but splits exist, also print splits path as primary manual route.
  local splits_hint=""
  if [[ -f "$target" ]]; then
    splits_hint="${target%.apks}-splits"
    if [[ ! -d "$splits_hint" ]]; then
      splits_hint="$(ls -td /sdcard/Download/*-frida-splits 2>/dev/null | head -n1 || true)"
    fi
  elif [[ -d "$target" ]]; then
    splits_hint="$target"
  fi

  cat <<EOF >&2

──────── вручну (надійніше) ────────
Папка:
  ${splits_hint:-$target}

App Manager → Install APKs → ця папка → галочки на ВСІХ 4:
  base.apk
  split_config.arm64_v8a.apk
  split_config.xxhdpi.apk
  split_extraAsset.apk
────────────────────────────────────
EOF

  if (( opened == 1 )); then
    return 0
  fi
  return 1
}

pause_until_user_ready() {
  echo >&2
  notify "Frida doctor" "Install 4 splits → відкрий гру → Enter у Termux"
  echo "╔══════════════════════════════════════════════╗" >&2
  echo "║  1) Встанови УСІ 4 splits (App Manager/SAI)  ║" >&2
  echo "║  2) Відкрий гру і тримай ≥30с                ║" >&2
  echo "║  3) Повернись сюди і натисни Enter           ║" >&2
  echo "╚══════════════════════════════════════════════╝" >&2
  printf "Enter коли гра відкрита (або вже впала): " >&2
  read -r _ || true
}

notify() {
  local title="$1"
  local content="$2"
  if command -v termux-notification >/dev/null 2>&1; then
    termux-notification --title "$title" --content "$content" --id frida-doctor 2>/dev/null || true
  fi
  if command -v termux-toast >/dev/null 2>&1; then
    termux-toast "$title: $content" 2>/dev/null || true
  fi
  echo "[doctor] $title — $content" >&2
}

vibrate_ok() {
  if command -v termux-vibrate >/dev/null 2>&1; then
    termux-vibrate -d 200 2>/dev/null || true
  fi
}

log_candidates() {
  cat <<EOF
/sdcard/Download/$LOG_NAME
/storage/emulated/0/Download/$LOG_NAME
$HOME_DIR/storage/downloads/$LOG_NAME
/sdcard/Android/data/$DEFAULT_PKG/files/$LOG_NAME
/storage/emulated/0/Android/data/$DEFAULT_PKG/files/$LOG_NAME
EOF
}

newest_log() {
  local f best="" best_m=0 m
  while IFS= read -r f; do
    [[ -f "$f" ]] || continue
    m=$(stat -c %Y "$f" 2>/dev/null || echo 0)
    if (( m >= best_m )); then
      best_m=$m
      best=$f
    fi
  done < <(log_candidates)
  [[ -n "$best" ]] && echo "$best"
}

clear_logs() {
  local f
  while IFS= read -r f; do
    rm -f "$f" 2>/dev/null || true
  done < <(log_candidates)
}

pkg_installed() {
  local pm
  pm="$(pm_bin 2>/dev/null || true)"
  [[ -n "$pm" ]] || return 1
  "$pm" path "$DEFAULT_PKG" 2>/dev/null | grep -q "package:"
}

try_uninstall() {
  local pm
  pm="$(pm_bin 2>/dev/null || true)"
  if [[ -z "$pm" ]]; then
    echo "[doctor] pm недоступний — зніми гру вручну в App Manager" >&2
    return 1
  fi
  if ! pkg_installed; then
    echo "[doctor] пакет ще не встановлений — ок" >&2
    return 0
  fi
  echo "[doctor] пробую uninstall $DEFAULT_PKG …" >&2
  if "$pm" uninstall --user 0 "$DEFAULT_PKG" >/dev/null 2>&1 \
    || "$pm" uninstall "$DEFAULT_PKG" >/dev/null 2>&1; then
    echo "[doctor] uninstall ok" >&2
    return 0
  fi
  echo "[doctor] uninstall відхилено (немає прав) — ЗНІМИ гру вручну перед Install" >&2
  notify "Frida doctor" "Зніми AFK Arena вручну, потім Install у SAI"
  return 1
}

find_source_apks() {
  local hint="${1:-}"
  if [[ -n "$hint" && -e "$hint" ]]; then
    echo "$hint"
    return 0
  fi
  if [[ -e "$DEFAULT_SOURCE_APKS" ]]; then
    echo "$DEFAULT_SOURCE_APKS"
    return 0
  fi
  local c
  for c in \
    "/sdcard/AppManager/apks/AFK Arena_1.198.01.apks" \
    "/storage/emulated/0/AppManager/apks/AFK Arena_1.198.01.apks" \
    "/sdcard/Download/AFK Arena_1.198.01.apks"; do
    if [[ -e "$c" ]]; then
      echo "$c"
      return 0
    fi
  done
  # newest App Manager lilith/afk .apks
  c="$(ls -t /sdcard/AppManager/apks/*.{apks,APKS} 2>/dev/null | head -n1 || true)"
  if [[ -n "$c" && -f "$c" ]]; then
    echo "$c"
    return 0
  fi
  return 1
}

run_self_update() {
  echo "[doctor] ▸ self-update…" >&2
  if [[ -x "$HOME_DIR/scan" ]]; then
    "$HOME_DIR/scan" update || true
  elif [[ -f "$HOME_DIR/protocol_ast/termux_update.py" ]]; then
    python3 -m protocol_ast.termux_update || true
  else
    echo "[doctor] немає update helper — пропускаю" >&2
  fi
  if [[ -f "$HOME_DIR/analyze_pcap.py" ]]; then
    grep -m1 '^VERSION' "$HOME_DIR/analyze_pcap.py" >&2 || true
  fi
}

diagnose_log() {
  local logf="$1"
  echo
  echo "════════ frida-unpin.log (tail) ════════"
  tail -n 40 "$logf" 2>/dev/null || cat "$logf"
  echo "════════════════════════════════════════"
  echo
  if grep -q 'ALIVE no-hooks\|probe ' "$logf" 2>/dev/null; then
    echo "[doctor] VERDICT: probe живий (gadget OK, хуків немає)" >&2
  elif grep -q 'pin-only ready\|CertificatePinner' "$logf" 2>/dev/null; then
    echo "[doctor] VERDICT: java pin-hook вставлено — можна MITM + ~/scan mine" >&2
  elif grep -q 'Java soft hooks done\|ready' "$logf" 2>/dev/null; then
    echo "[doctor] VERDICT: soft/native hooks ready" >&2
  elif grep -q 'heartbeat' "$logf" 2>/dev/null; then
    echo "[doctor] VERDICT: скрипт живий (heartbeat є), хуки ще не встигли / crash на хуках" >&2
    echo "         Подивись останній рядок перед падінням." >&2
  elif grep -q 'boot MODE=' "$logf" 2>/dev/null; then
    echo "[doctor] VERDICT: boot був, потім тиша — crash дуже рано" >&2
  else
    echo "[doctor] VERDICT: лог є, але незрозумілий — кинь tail у чат" >&2
  fi
}

wait_for_log() {
  local timeout_s="${1:-180}"
  local start now elapsed logf
  start=$(date +%s)
  echo "[doctor] чекаю лог до ${timeout_s}с (встанови → відкрий гру)…" >&2
  notify "Frida doctor" "Install splits → відкрий гру → чекаю лог"
  while true; do
    now=$(date +%s)
    elapsed=$((now - start))
    if (( elapsed > timeout_s )); then
      echo "[doctor] timeout ${timeout_s}с — логу немає" >&2
      echo "  Перевір: усі 4 splits, arm64_v8a, extraAsset" >&2
      echo "  ls: $(log_candidates | tr '\n' ' ')" >&2
      return 1
    fi
    logf="$(newest_log || true)"
    if [[ -n "$logf" && -s "$logf" ]]; then
      # require a fresh log (mtime within last timeout window)
      local m
      m=$(stat -c %Y "$logf" 2>/dev/null || echo 0)
      if (( m + 5 >= start )); then
        vibrate_ok
        notify "Frida doctor" "Лог з'явився"
        echo "[doctor] лог: $logf (${elapsed}с)" >&2
        # wait a bit more for heartbeats / hooks
        sleep 8
        diagnose_log "$logf"
        return 0
      fi
    fi
    if (( elapsed % 15 == 0 )); then
      if pkg_installed; then
        echo "[doctor] … ${elapsed}с пакет є, чекаю запуск/лог" >&2
      else
        echo "[doctor] … ${elapsed}с ще немає пакету / логу" >&2
      fi
    fi
    sleep 2
  done
}

frida_doctor() {
  local mode="java"
  local skip_build=0
  local skip_update=0
  local wait_only=0
  local timeout_s=240
  local source=""
  local arg

  while [[ $# -gt 0 ]]; do
    arg="$1"
    shift || true
    case "$arg" in
      probe|java|java-tm|pin|native|full)
        mode="$arg"
        ;;
      --skip-build)
        skip_build=1
        ;;
      --skip-update)
        skip_update=1
        ;;
      --wait-only|wait|log)
        wait_only=1
        skip_build=1
        skip_update=1
        ;;
      --timeout)
        timeout_s="${1:-240}"
        shift || true
        ;;
      --timeout=*)
        timeout_s="${arg#--timeout=}"
        ;;
      -h|--help)
        cat <<'EOF'
~/frida doctor [mode] [опції]

  mode: probe | java (default) | java-tm | native

  --skip-update   не тягнути self-update
  --skip-build    не перезбирати (лише uninstall/install + wait)
  --wait-only     тільки чекати лог після твого install/запуску
  --timeout SEC   скільки чекати лог (default 240)

Приклади:
  ~/frida doctor
  ~/frida doctor probe
  ~/frida doctor --wait-only
EOF
        return 0
        ;;
      *)
        if [[ -e "$arg" ]]; then
          source="$arg"
        else
          echo "[doctor] невідомий аргумент: $arg" >&2
          return 1
        fi
        ;;
    esac
  done

  echo "[doctor] mode=$mode  timeout=${timeout_s}s" >&2

  if (( skip_update == 0 )); then
    run_self_update
  fi

  # Refresh launcher from update (this script may be mid-run from old copy —
  # rebuild uses python module which was updated).
  need_tools

  if (( wait_only == 0 )); then
    clear_logs
    echo "[doctor] старі логи очищено" >&2

    if (( skip_build == 0 )); then
      if [[ -z "$source" ]]; then
        source="$(find_source_apks || true)"
      fi
      if [[ -z "$source" || ! -e "$source" ]]; then
        echo "[doctor] немає source .apks — задай шлях:" >&2
        echo "  ~/frida doctor java \"/sdcard/AppManager/apks/AFK Arena_1.198.01.apks\"" >&2
        return 1
      fi
      echo "[doctor] source: $source" >&2
      echo "[doctor] ▸ rebuild unpin-mode=$mode …" >&2
      notify "Frida doctor" "Rebuild $mode…"
      python3 -m protocol_ast.frida_gadget "$source" --method zip --unpin-mode "$mode"
    else
      echo "[doctor] skip-build — беру вже зібраний *-frida.apks" >&2
    fi

    try_uninstall || true
    echo
    echo "╔══════════════════════════════════════════╗"
    echo "║  ЗАРАЗ: App Manager / SAI → Install      ║"
    echo "║  постав УСІ 4 splits, потім відкрий гру ║"
    echo "╚══════════════════════════════════════════╝"
    echo
    open_frida_install "" || true
    notify "Frida doctor" "Install усі splits → відкрий гру"
    pause_until_user_ready
  else
    echo "[doctor] wait-only — не чіпаю APK" >&2
    pause_until_user_ready
  fi

  # Fresh wait window starts AFTER user confirms install/launch.
  clear_logs
  echo "[doctor] логи скинуто перед очікуванням — перезапусти гру якщо вже відкрита" >&2
  echo "[doctor] (якщо гра вже біжить — закрий і відкрий ще раз)" >&2
  sleep 2
  wait_for_log "$timeout_s"
  local rc=$?
  if (( rc == 0 )); then
    echo
    echo "Далі: PCAPdroid MITM + Block QUIC → пограй → Stop → ~/scan mine"
    return 0
  fi
  echo
  echo "Немає логу.Checklist:"
  echo "  1) гра встановлена?  /system/bin/pm path $DEFAULT_PKG"
  echo "  2) серед splits є arm64_v8a?"
  echo "  3) ~/frida doctor probe   # перевірка gadget без хуків"
  return "$rc"
}

main() {
  banner
  local cmd="${1:-}"
  case "$cmd" in
    -h|--help|help|guide|plan)
      python3 -m protocol_ast.frida_gadget --guide
      exit 0
      ;;
    doctor|doc|fix)
      shift || true
      frida_doctor "$@"
      exit $?
      ;;
    pkgs|packages|list-pkg)
      list_game_packages
      exit 0
      ;;
    pull)
      pull_package "${2:-$DEFAULT_PKG}" >/dev/null
      echo "Далі:  ~/frida" >&2
      exit 0
      ;;
    sign)
      need_tools
      local u="${2:-}"
      if [[ -z "$u" || ! -f "$u" ]]; then
        echo "Usage: ~/frida sign /path/to/xxx-frida.unsigned.apk" >&2
        exit 1
      fi
      python3 -m protocol_ast.frida_gadget --sign-only "$u"
      exit $?
      ;;
    install|open)
      # Auto-find newest *-frida.apks / splits and hand to system installer
      open_frida_install "${2:-}"
      exit $?
      ;;
    find|find-install|where)
      python3 -m protocol_ast.frida_gadget --find-install
      exit $?
      ;;
    resign)
      need_tools
      local apk="${2:-/sdcard/Download/777.apk}"
      echo "[*] resign-only (без Frida) — перевірка чи підпис/zip ламає install" >&2
      python3 -m protocol_ast.frida_gadget --resign "$apk"
      exit $?
      ;;
    probe)
      # ~/frida probe [path]  → diagnose bundle; if path missing keep old behavior
      if [[ -n "${2:-}" && -e "${2:-}" ]]; then
        python3 -m protocol_ast.frida_gadget --probe "$2"
        exit $?
      fi
      # allow ~/frida probe as mode via doctor? keep diagnose default path
      local target="${2:-/sdcard/AppManager/apks/AFK Arena_1.198.01.apks}"
      python3 -m protocol_ast.frida_gadget --probe "$target"
      exit $?
      ;;
    log|wait-log)
      shift || true
      frida_doctor --wait-only "$@"
      exit $?
      ;;
  esac

  need_tools

  if [[ ! -f "$HOME_DIR/protocol_ast/frida_gadget.py" ]]; then
    echo "немає protocol_ast/frida_gadget.py — ~/scan update" >&2
    exit 1
  fi

  local apk
  # Allow directory of already-extracted splits
  if [[ -n "$cmd" && -d "$cmd" ]]; then
    apk="$cmd"
  else
    apk="$(pick_apk "$cmd")"
  fi
  echo "[*] input: $apk"
  if [[ -d "$apk" || "$apk" == *.apks || "$apk" == *.xapk || "$apk" == *.apkm ]]; then
    echo "[*] Split bundle → patch ABI lib + resign all splits"
  else
    echo "[*] Surgical zip+patchelf (single APK)"
  fi
  echo

  # Drop stale broken unsigned from older full-rezip method
  local stem
  stem="$(basename "$apk")"
  stem="${stem%.apk}"
  stem="${stem%.apks}"
  stem="${stem%.xapk}"
  stem="${stem%.apkm}"
  base_name="${stem}-frida.unsigned.apk"
  for u in \
    "$(dirname "$apk")/${stem}-frida.unsigned.apk" \
    "$HOME_DIR/storage/downloads/$base_name" \
    "$HOME_DIR/storage/shared/Download/$base_name" \
    "/sdcard/Download/$base_name"; do
    if [[ -f "$u" ]]; then
      echo "[*] removing stale unsigned: $u" >&2
      rm -f "$u"
    fi
  done

  # Optional: ~/frida FILE probe|java|java-tm|native   or FRIDA_UNPIN_MODE=…
  local unpin_mode="java"
  if [[ "${2:-}" == "probe" || "${2:-}" == "java" || "${2:-}" == "java-tm" || "${2:-}" == "pin" || "${2:-}" == "native" || "${2:-}" == "full" ]]; then
    unpin_mode="$2"
  elif [[ "${2:-}" == "--unpin-mode" && -n "${3:-}" ]]; then
    unpin_mode="$3"
  elif [[ "${2:-}" == --unpin-mode=* ]]; then
    unpin_mode="${2#--unpin-mode=}"
  fi
  unpin_mode="${FRIDA_UNPIN_MODE:-$unpin_mode}"

  echo "[*] unpin-mode: $unpin_mode  (probe=без хуків, java=лише OkHttp pin @25s, java-tm=TrustManager, native=+BoringSSL)"
  python3 -m protocol_ast.frida_gadget "$apk" --method zip --unpin-mode "$unpin_mode"
  echo
  echo "════════════════════════════════════════"
  echo "Далі:"
  echo "  1) Uninstall стару AFK Arena"
  echo "  2) ~/frida install"
  echo "  3) Відкрити гру ≥30с → cat /sdcard/Download/frida-unpin.log"
  echo "  4) PCAPdroid MITM + Block QUIC → ~/scan mine"
  echo
  echo "Або все разом:  ~/frida doctor $unpin_mode"
  echo "════════════════════════════════════════"
}

main "$@"
