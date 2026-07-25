"""Locate SSLKEYLOGFILE / PCAPdroid keylogs on device or next to captures."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from .pcapng_secrets import write_keylog_beside_capture
except ImportError:  # python3 ~/protocol_ast/find_keylog.py
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from protocol_ast.pcapng_secrets import write_keylog_beside_capture

KEYLOG_NAMES = (
    "sslkeys.log",
    "sslkeylogfile.txt",
    "keylog.txt",
    "keys.txt",
    "SSLKEYLOGFILE",
    "pcapdroid_sslkeys.log",
)


def _looks_like_keylog(path: Path) -> bool:
    try:
        sample = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError:
        return False
    return (
        "CLIENT_RANDOM" in sample
        or "CLIENT_TRAFFIC_SECRET" in sample
        or "SERVER_TRAFFIC_SECRET" in sample
    )


def find_keylog_files(search_roots: list[Path] | None = None) -> list[Path]:
    """Search common Termux/Android paths for NSS keylog files."""
    home = Path.home()
    roots = search_roots or [
        home / "downloads",
        home / "Download",
        home / "storage" / "downloads",
        home / "storage" / "shared" / "Download",
        home / "storage" / "shared" / "PCAPdroid",
        Path("/sdcard/Download"),
        Path("/sdcard/PCAPdroid"),
        home,
    ]
    found: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for name in KEYLOG_NAMES:
            p = root / name
            if p.exists() and p.resolve() not in seen and _looks_like_keylog(p):
                found.append(p)
                seen.add(p.resolve())
        try:
            for p in root.iterdir():
                if not p.is_file():
                    continue
                low = p.name.lower()
                if not (low.endswith(".log") or "key" in low or "ssl" in low):
                    continue
                if p.resolve() in seen:
                    continue
                if _looks_like_keylog(p):
                    found.append(p)
                    seen.add(p.resolve())
        except OSError:
            continue
    return found


def resolve_keylog(
    keylog_arg: str | None,
    *,
    pcap_path: str | Path | None = None,
) -> tuple[Path | None, str]:
    """
    Resolve --keylog path.

    Returns (path, status_message).
    keylog_arg:
      - None → no keylog
      - "auto" → search disk + extract from pcapng DSB
      - path → use if exists
    """
    pcap = Path(pcap_path).expanduser() if pcap_path else None

    if keylog_arg and keylog_arg.lower() != "auto":
        path = Path(keylog_arg).expanduser()
        if path.exists() and _looks_like_keylog(path):
            return path, f"keylog: {path}"
        if path.exists():
            return None, f"файл є, але це не NSS keylog: {path}"
        return None, f"файл не знайдено: {path}"

    if keylog_arg is None:
        return None, ""

    # auto mode
    if pcap and pcap.exists():
        extracted = write_keylog_beside_capture(pcap)
        if extracted:
            return extracted, f"keylog витягнуто з pcapng DSB → {extracted}"
        for sib in (
            pcap.with_suffix(".keylog"),
            pcap.with_name(pcap.stem + ".keylog"),
            pcap.parent / "sslkeys.log",
        ):
            if sib.exists() and _looks_like_keylog(sib):
                return sib, f"keylog поруч із capture: {sib}"

        found = find_keylog_files([pcap.parent])
        if found:
            return found[0], f"keylog знайдено: {found[0]}"

    found = find_keylog_files()
    if found:
        return found[0], f"keylog знайдено: {found[0]}"

    return None, (
        "keylog не знайдено. Зроби новий capture з PCAPdroid TLS decryption "
        "і збережи SSLKEYLOGFILE (або pcapng з embedded keys)."
    )


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    pcap = args[0] if args else None
    path, msg = resolve_keylog("auto", pcap_path=pcap)
    print(msg or "немає результату")
    if path:
        print(path)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
