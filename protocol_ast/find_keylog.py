"""Locate SSLKEYLOGFILE / PCAPdroid keylogs on device or next to captures."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_pcapng_secrets():
    try:
        from protocol_ast.pcapng_secrets import write_keylog_beside_capture

        return write_keylog_beside_capture
    except Exception:
        pass
    # Direct file load — works even when package __init__ / siblings are partial
    here = Path(__file__).resolve().parent / "pcapng_secrets.py"
    spec = importlib.util.spec_from_file_location("pcapng_secrets_standalone", here)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {here}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.write_keylog_beside_capture


write_keylog_beside_capture = None  # filled lazily


def _wk():
    global write_keylog_beside_capture
    if write_keylog_beside_capture is None:
        write_keylog_beside_capture = _load_pcapng_secrets()
    return write_keylog_beside_capture


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
                # Android Download often saves "sslkeylogfile.txt (1)"
                if not (
                    low.endswith(".log")
                    or low.endswith(".txt")
                    or "key" in low
                    or "ssl" in low
                ):
                    continue
                if p.resolve() in seen:
                    continue
                if _looks_like_keylog(p):
                    found.append(p)
                    seen.add(p.resolve())
        except OSError:
            continue
    # newest first — "sslkeylogfile.txt (1)" after a new MITM must win over stale copy
    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return found


def count_keylog_overlap(pcap_path: str | Path, keylog_path: str | Path) -> int:
    """How many ClientHello randoms in pcap appear in the keylog."""
    try:
        from .pcap_analyze import extract_flows
        from .tls_keylog import find_client_randoms_in_records, parse_keylog
    except Exception:
        return 0
    pcap = Path(pcap_path).expanduser()
    keylog = Path(keylog_path).expanduser()
    if not pcap.is_file() or not keylog.is_file():
        return 0
    try:
        secrets = parse_keylog(keylog)
        if not secrets.client_randoms:
            return 0
        buckets = extract_flows(pcap, min_packets=1, min_payload=5, tcp_reassemble=True)
    except Exception:
        return 0
    found: set[str] = set()
    for label, bucket in buckets.items():
        if "443" not in label.upper() and "TLS" not in label.upper():
            # still scan other TCP — cheap enough for small recent dumps
            if not label.upper().startswith("TCP"):
                continue
        for rnd in find_client_randoms_in_records(bucket.payloads):
            found.add(rnd.hex())
    return len(found & secrets.client_randoms)


def pick_pcap_for_keylog(
    keylog_path: str | Path,
    *,
    seed_paths: list[str | Path] | None = None,
    max_candidates: int = 8,
    max_bytes: int = 12_000_000,
) -> tuple[Path | None, int, str]:
    """
    Among recent pcaps, pick the one that overlaps the keylog secrets.
    Avoids pairing a brand-new dump with an older sslkeylogfile.txt (1).
    """
    try:
        from .termux_update import iter_pcaps_under, pick_newest_pcap
    except Exception:
        pick_newest_pcap = None
        iter_pcaps_under = None  # type: ignore

    keylog = Path(keylog_path).expanduser()
    cands: list[Path] = []
    seen: set[Path] = set()
    for p in seed_paths or []:
        path = Path(p).expanduser()
        if path.is_file():
            rp = path.resolve()
            if rp not in seen:
                seen.add(rp)
                cands.append(path)
    if iter_pcaps_under is not None:
        for p in iter_pcaps_under():
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                cands.append(p)
    if not cands and pick_newest_pcap is not None:
        one = pick_newest_pcap(None, also_search_defaults=True)
        if one:
            cands = [one]
    # newest first, skip huge dumps for quick scoring
    cands = sorted(cands, key=lambda p: p.stat().st_mtime, reverse=True)
    scored: list[tuple[int, Path]] = []
    checked = 0
    for p in cands:
        if checked >= max_candidates:
            break
        try:
            if p.stat().st_size > max_bytes:
                continue
        except OSError:
            continue
        checked += 1
        ov = count_keylog_overlap(p, keylog)
        if ov > 0:
            scored.append((ov, p))
    if scored:
        scored.sort(key=lambda t: (-t[0], -t[1].stat().st_mtime))
        best_ov, best = scored[0]
        return best, best_ov, f"pcap↔keylog overlap={best_ov} → {best.name}"
    # fallback newest small-ish
    for p in cands:
        try:
            if p.stat().st_size <= max_bytes:
                return p, 0, f"немає overlap з keylog → беру найновіший {p.name}"
        except OSError:
            continue
    if cands:
        return cands[0], 0, f"немає overlap з keylog → {cands[0].name}"
    return None, 0, "pcap не знайдено"


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

    # auto mode — prefer newest keylog by mtime (not first path hit)
    home = Path.home()
    search_dirs: list[Path] = []
    if pcap and pcap.exists() and pcap.is_file():
        extracted = _wk()(pcap)
        if extracted:
            return extracted, f"keylog витягнуто з pcapng DSB → {extracted}"
        search_dirs.append(pcap.parent)
        # PCAPdroid dumps live under …/PCAPdroid/; keylog often in parent Download/
        if pcap.parent.name.lower() == "pcapdroid":
            search_dirs.append(pcap.parent.parent)
    search_dirs.extend(
        [
            home / "storage" / "downloads",
            home / "downloads",
            home / "storage" / "shared" / "Download",
        ]
    )
    # de-dupe roots preserve order
    roots: list[Path] = []
    seen_r: set[Path] = set()
    for d in search_dirs:
        try:
            rd = d.resolve()
        except OSError:
            rd = d
        if rd in seen_r:
            continue
        seen_r.add(rd)
        roots.append(d)

    found = find_keylog_files(roots)
    if found:
        best = found[0]  # already newest-first
        return best, f"keylog (найновіший): {best}"

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
