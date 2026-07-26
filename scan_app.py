#!/usr/bin/env python3
"""
SIGNAL SCAN — мінімальний універсальний сканер для Termux.

  ~/scan              # меню
  ~/scan peel         # living signal
  ~/scan mine         # game mine + sdk_session
  ~/scan sdk          # показати останній sdk_session.json
  ~/scan unpin        # pin bypass без root (apk-mitm, Java)
  ~/scan frida        # Frida Gadget + SSL unpin (Java+native)
  ~/scan update       # self-update
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

VERSION = "1.2.0"
HOME = Path.home()
ANALYZE = HOME / "analyze_pcap.py"
UNPIN = HOME / "unpin"
FRIDA = HOME / "frida"
DOWNLOADS = HOME / "storage" / "downloads"
PCAPDROID = DOWNLOADS / "PCAPdroid"


def _py() -> str:
    return sys.executable or "python3"


def _run(args: list[str], *, env: dict | None = None) -> int:
    e = os.environ.copy()
    e["PYTHONPATH"] = str(HOME) + ((":" + e["PYTHONPATH"]) if e.get("PYTHONPATH") else "")
    if env:
        e.update(env)
    return subprocess.call(args, env=e)


def _banner() -> None:
    print()
    print("╔══════════════════════════════════════╗")
    print("║         SIGNAL SCAN  ·  v" + VERSION.ljust(6) + " ║")
    print("║   pcap → TLS → HTTP → protobuf       ║")
    print("╚══════════════════════════════════════╝")
    print()


def _status_line() -> None:
    pcap = _newest_pcap()
    keylog = _newest_keylog()
    print("pcap:   ", pcap.name if pcap else "— не знайдено")
    if pcap:
        print("         ", pcap, f"({pcap.stat().st_size} B)")
    print("keylog: ", keylog.name if keylog else "— не знайдено")
    if keylog:
        print("         ", keylog, f"({keylog.stat().st_size} B)")
    sdk = _sdk_path()
    print("sdk:    ", "є → " + str(sdk) if sdk and sdk.exists() else "— ще немає mine")
    print()


def _newest_pcap() -> Path | None:
    try:
        sys.path.insert(0, str(HOME))
        from protocol_ast.termux_update import pick_newest_pcap

        return pick_newest_pcap(None, also_search_defaults=True)
    except Exception:
        cands: list[Path] = []
        for root in (PCAPDROID, DOWNLOADS, HOME / "downloads"):
            if not root.is_dir():
                continue
            for p in root.glob("*.pcap*"):
                if p.is_file():
                    cands.append(p)
        return max(cands, key=lambda p: p.stat().st_mtime) if cands else None


def _newest_keylog() -> Path | None:
    cands: list[Path] = []
    for root in (DOWNLOADS, HOME / "downloads", HOME / "storage" / "shared" / "Download"):
        if not root.is_dir():
            continue
        try:
            for p in root.iterdir():
                if not p.is_file():
                    continue
                name = p.name.lower()
                if "sslkeylog" in name or name.startswith("keylog"):
                    cands.append(p)
        except OSError:
            continue
    return max(cands, key=lambda p: p.stat().st_mtime) if cands else None


def _sdk_path() -> Path | None:
    pcap = _newest_pcap()
    if pcap:
        cand = pcap.parent / "sdk_session.json"
        if cand.exists():
            return cand
    for root in (PCAPDROID, DOWNLOADS):
        cand = root / "sdk_session.json"
        if cand.exists():
            return cand
    return None


def cmd_update() -> int:
    if not ANALYZE.exists():
        print("немає ~/analyze_pcap.py — спочатку termux_setup.sh")
        return 1
    print("▸ оновлення…")
    return _run([_py(), str(ANALYZE), "--self-update"])


def cmd_peel() -> int:
    if not ANALYZE.exists():
        print("немає analyze_pcap.py — ~/scan update")
        return 1
    flow = os.environ.get("FLOW", "TCP:443")
    print(f"▸ living signal  flow={flow}")
    return _run([_py(), str(ANALYZE), "--signal", "--flow", flow, "--keylog", "auto"])


def cmd_mine() -> int:
    if not ANALYZE.exists():
        print("немає analyze_pcap.py — ~/scan update")
        return 1
    print("▸ game mine (SNI + SDK session)")
    return _run([_py(), str(ANALYZE), "--mine", "--keylog", "auto"])


def cmd_sdk() -> int:
    path = _sdk_path()
    if not path or not path.exists():
        print("sdk_session.json немає. Спочатку: 2) Game mine")
        return 1
    print(f"▸ {path}\n")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"читання: {exc}")
        return 1
    # компактний огляд
    ident = data.get("identity") or {}
    login = data.get("login") or {}
    hb = data.get("heartbeat") or {}
    print("── identity ──")
    for k in (
        "app_uid",
        "uid",
        "gm_openid",
        "plat_openid",
        "app_token",
        "access_token",
        "app_version",
        "game_id",
        "channel_id",
        "install_id",
    ):
        if k in ident:
            print(f"  {k}: {ident[k]}")
    lb = ident.get("lilith_bindings") or []
    if lb and isinstance(lb, list) and isinstance(lb[0], dict):
        print(f"  email: {lb[0].get('id')}")
        print(f"  nick bindings type: {lb[0].get('type')}")
    if login.get("response"):
        d = (login["response"] or {}).get("data") or {}
        print(f"  pgs_nickname: {d.get('pgs_nickname')}")
        print(f"  region: {d.get('region')} / {d.get('sdk_region')}")
    print("── heartbeat ──")
    hd = ((hb.get("response") or {}).get("data")) or {}
    for k in ("can_play", "online_limit", "heartbeat_interval", "max_time", "svr_time"):
        if k in hd:
            print(f"  {k}: {hd[k]}")
    print()
    print("повний JSON: ", path)
    # опційно весь файл
    ans = input("показати весь JSON? [y/N] ").strip().lower()
    if ans == "y":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def cmd_stream() -> int:
    if not ANALYZE.exists():
        print("немає analyze_pcap.py — ~/scan update")
        return 1
    print("▸ stream agent")
    return _run([_py(), str(ANALYZE), "--stream", "--keylog", "auto", "--flow", "TCP:443"])


def cmd_unpin(argv: list[str] | None = None) -> int:
    """No-root SSL pin bypass via ~/unpin (apk-mitm)."""
    extra = list(argv or [])
    if UNPIN.is_file():
        print("▸ unpin (apk-mitm, без root)")
        return _run(["bash", str(UNPIN), *extra])
    print("немає ~/unpin — спочатку: ~/scan update")
    print()
    print("План без root:")
    print("  1) Extract APK (SAI / App Manager) → Download/")
    print("  2) ~/unpin   # apk-mitm патч Java TrustManager")
    print("  3) якщо SEALED лишився → ~/frida  (Gadget + native)")
    print("  4) PCAPdroid MITM → ~/scan mine")
    return 1


def cmd_frida(argv: list[str] | None = None) -> int:
    """No-root Frida Gadget inject + autonomous SSL unpin."""
    extra = list(argv or [])
    if FRIDA.is_file():
        print("▸ frida gadget (script mode, без root/ПК)")
        return _run(["bash", str(FRIDA), *extra])
    # Direct module fallback after self-update of helpers but before launcher
    mod = HOME / "protocol_ast" / "frida_gadget.py"
    if mod.is_file():
        print("▸ frida_gadget.py (немає ~/frida launcher — module)")
        if extra and extra[0] in ("guide", "help", "-h", "--help"):
            return _run([_py(), "-m", "protocol_ast.frida_gadget", "--guide"])
        return _run([_py(), "-m", "protocol_ast.frida_gadget", *extra])
    print("немає ~/frida — спочатку: ~/scan update")
    print("Потім: Extract APK → ~/frida → install *-frida.apk → MITM → ~/scan mine")
    return 1


MENU = [
    ("1", "Peel — живий сигнал (TLS→HTTP→body)", cmd_peel),
    ("2", "Mine — карта SNI + SDK session", cmd_mine),
    ("3", "SDK — останній sdk_session.json", cmd_sdk),
    ("4", "Unpin — Java pin (apk-mitm)", lambda: cmd_unpin()),
    ("5", "Frida — Gadget + native SSL unpin", lambda: cmd_frida()),
    ("6", "Stream — інкрементальний агент", cmd_stream),
    ("7", "Update — стягнути свіжий код", cmd_update),
    ("0", "Вихід", None),
]


def menu_loop() -> int:
    while True:
        _banner()
        _status_line()
        for key, title, _ in MENU:
            print(f"  {key})  {title}")
        print()
        choice = input("▸ ").strip()
        if choice in ("0", "q", "quit", "exit"):
            print("bye")
            return 0
        for key, _title, fn in MENU:
            if choice == key and fn:
                print()
                rc = fn()
                print()
                input("Enter…")
                if rc:
                    print(f"(код {rc})")
                break
        else:
            if choice not in {m[0] for m in MENU}:
                print("невідомий вибір")
                input("Enter…")


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        return menu_loop()
    cmd = argv[0].lower().lstrip("-")
    if cmd in ("peel", "signal", "s"):
        return cmd_peel()
    if cmd in ("mine", "m", "game"):
        return cmd_mine()
    if cmd in ("sdk", "session", "id"):
        return cmd_sdk()
    if cmd in ("stream", "st"):
        return cmd_stream()
    if cmd in ("unpin", "pin", "mitm-apk"):
        return cmd_unpin(argv[1:])
    if cmd in ("frida", "gadget", "fgadget"):
        return cmd_frida(argv[1:])
    if cmd in ("update", "u", "self-update"):
        return cmd_update()
    if cmd in ("help", "h"):
        print(__doc__)
        return 0
    print(f"невідома команда: {cmd}")
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
