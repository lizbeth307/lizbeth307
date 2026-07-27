#!/data/data/com.termux/files/usr/bin/bash
# Frida Gadget inject + autonomous SSL unpin (no root, no PC).
# Usage:
#   ~/frida                              # pick APK / .apks (deduped list)
#   ~/frida "/sdcard/AppManager/apks/AFK Arena_1.198.01.apks"
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

AFK Arena (3 splits):
  ~/frida "/sdcard/AppManager/apks/AFK Arena_1.198.01.apks"

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

  if [[ -n "$hint" && -e "$hint" ]]; then
    target="$hint"
  else
    target="$(
      python3 - <<'PY'
from protocol_ast.frida_gadget import find_frida_install_targets
cands = find_frida_install_targets()
# prefer .apks file over splits directory
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
    # shell fallback glob (newest by ls -t)
    local cand
    cand="$(ls -t /sdcard/Download/*-frida.apks /storage/emulated/0/Download/*-frida.apks 2>/dev/null | head -n1 || true)"
    if [[ -n "$cand" && -f "$cand" ]]; then
      target="$cand"
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
  echo >&2
  echo "⚠  Спочатку ЗНІМИ звичайну AFK Arena," >&2
  echo "   інакше підпис не збіжиться." >&2
  echo >&2
  echo "Відкриваю установщик — обери App Manager або SAI." >&2
  echo >&2

  if [[ -d "$target" ]]; then
    echo "[*] це папка splits: $target" >&2
    echo "    SAI/App Manager → Install from folder / вибери всі .apk" >&2
    # Open folder in system Files if possible
    if command -v termux-open >/dev/null 2>&1; then
      termux-open "$target" && return 0
    fi
    return 0
  fi

  if command -v termux-open >/dev/null 2>&1; then
    echo "[*] termux-open \"$target\"" >&2
    termux-open "$target" && return 0
  fi

  local uri="file://${target}"
  for starter in am /system/bin/am; do
    if [[ -x "$starter" ]] || command -v "$starter" >/dev/null 2>&1; then
      echo "[*] $starter start VIEW" >&2
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

  cat <<EOF >&2
Не вдалось авто-відкрити. Вручну:

  Files → Download → $(basename "$target")
  → відкрити через App Manager / SAI

Або:
  pkg install termux-api
  termux-open "$target"
EOF
  return 1
}

main() {
  banner
  local cmd="${1:-}"
  case "$cmd" in
    -h|--help|help|guide|plan)
      python3 -m protocol_ast.frida_gadget --guide
      exit 0
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
      local target="${2:-/sdcard/AppManager/apks/AFK Arena_1.198.01.apks}"
      python3 -m protocol_ast.frida_gadget --probe "$target"
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

  # Optional: ~/frida FILE probe|java|native   or FRIDA_UNPIN_MODE=…
  local unpin_mode="java"
  if [[ "${2:-}" == "probe" || "${2:-}" == "java" || "${2:-}" == "native" || "${2:-}" == "full" ]]; then
    unpin_mode="$2"
  elif [[ "${2:-}" == "--unpin-mode" && -n "${3:-}" ]]; then
    unpin_mode="$3"
  elif [[ "${2:-}" == --unpin-mode=* ]]; then
    unpin_mode="${2#--unpin-mode=}"
  fi
  unpin_mode="${FRIDA_UNPIN_MODE:-$unpin_mode}"

  echo "[*] unpin-mode: $unpin_mode  (probe=без хуків, java=лише Java, native=+BoringSSL)"
  python3 -m protocol_ast.frida_gadget "$apk" --method zip --unpin-mode "$unpin_mode"
  echo
  echo "════════════════════════════════════════"
  echo "Далі:"
  echo "  1) Uninstall стару AFK Arena"
  echo "  2) ~/frida install"
  echo "  3) Відкрити гру → cat /sdcard/Download/frida-unpin.log"
  echo "  4) PCAPdroid MITM + Block QUIC → ~/scan mine"
  echo
  echo "Якщо знову close:"
  echo "  ~/frida \"…apks\" probe     # тест: gadget без хуків"
  echo "  ~/frida \"…apks\" java      # лише Java (default)"
  echo "  ~/frida \"…apks\" native    # + safe BoringSSL"
  echo "════════════════════════════════════════"
}

main "$@"
