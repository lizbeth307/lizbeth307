"""Self-update helpers for Termux — no apt, no interactive prompts."""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from pathlib import Path

REPO = "lizbeth307/lizbeth307"
BRANCH = "cursor/signal-pipeline-p4-a4e6"
HELPERS = (
    "__init__.py",
    "aes_gcm.py",
    "tls_keylog.py",
    "pcapng_secrets.py",
    "find_keylog.py",
    "http2.py",
    "hpack_decode.py",
    "signal.py",
    "body_peel.py",
    "json_api.py",
    "binary_peel.py",
    "probe_loop.py",
    "stream_agent.py",
    "smart_probe.py",
    "active_probe.py",
    "stream_enrich.py",
    "splitters.py",
    "tls_handshake.py",
    "pcap_analyze.py",
    "pcap_read.py",
    "deep_decode.py",
    "align.py",
    "cluster.py",
    "sequitur.py",
    "parser.py",
    "serde.py",
    "pipeline.py",
    "ast_nodes.py",
    "io_utils.py",
    "tcp_reassemble.py",
    "probe_env.py",
    "termux_update.py",
    "game_mine.py",
    "frida_gadget.py",
    "frida_ssl_unpin.js",
)
ROOT_FILES = ("analyze_pcap.py", "probe_network.py", "scan_app.py")
LAUNCHERS = (
    ("scripts/termux_signal.sh", "signal"),
    ("scripts/termux_scan.sh", "scan"),
    ("scripts/termux_unpin.sh", "unpin"),
    ("scripts/termux_frida.sh", "frida"),
)


def _fetch(url: str, timeout: float = 60.0) -> bytes:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "protocol-ast-termux-update/3.8"},
    )
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def resolve_base(branch: str = BRANCH) -> tuple[str, str]:
    """
    Return (base_url_without_trailing_file, ref_label).
    Prefer jsDelivr @ commit SHA; fall back to raw.githubusercontent + cache bust.
    """
    api = f"https://api.github.com/repos/{REPO}/commits/{branch}"
    try:
        data = json.loads(_fetch(api, timeout=20).decode("utf-8"))
        sha = data["sha"]
        return f"https://cdn.jsdelivr.net/gh/{REPO}@{sha}", sha
    except Exception:
        ts = int(time.time())
        return f"https://raw.githubusercontent.com/{REPO}/{branch}", f"{branch}@{ts}"


def file_url(base: str, rel: str) -> str:
    if "jsdelivr.net" in base:
        return f"{base}/{rel}"
    return f"{base}/{rel}?t={int(time.time())}"


def download_tree(dest_home: Path | None = None, *, branch: str = BRANCH) -> dict:
    """Download analyze_pcap.py, probe_network.py, and protocol_ast helpers into $HOME."""
    home = dest_home or Path.home()
    base, ref = resolve_base(branch)
    report: dict = {"base": base, "ref": ref, "files": [], "errors": []}
    ast_dir = home / "protocol_ast"
    ast_dir.mkdir(parents=True, exist_ok=True)

    for name in ROOT_FILES:
        url = file_url(base, name)
        try:
            data = _fetch(url)
            target = home / name
            tmp = Path(str(target) + ".new")
            tmp.write_bytes(data)
            tmp.replace(target)
            try:
                target.chmod(0o755)
            except OSError:
                pass
            report["files"].append(str(target))
        except Exception as exc:
            report["errors"].append(f"{name}: {exc}")

    for rel, dest_name in LAUNCHERS:
        url = file_url(base, rel)
        try:
            data = _fetch(url)
            if not data or not data.lstrip().startswith(b"#!"):
                raise RuntimeError(f"launcher payload looks empty/invalid ({len(data)} bytes)")
            # Normalize CRLF → LF so Termux bash shebang resolves.
            data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            target = home / dest_name
            tmp = Path(str(target) + ".new")
            tmp.write_bytes(data)
            tmp.replace(target)
            try:
                target.chmod(0o755)
            except OSError:
                pass
            report["files"].append(str(target))
            report.setdefault("launchers", []).append(str(target))
            # Keep primary ~/signal for self-update fallback messaging.
            if dest_name == "signal":
                report["launcher"] = str(target)
        except Exception as exc:
            report["errors"].append(f"{rel} → ~/{dest_name}: {exc}")

    for name in HELPERS:
        url = file_url(base, f"protocol_ast/{name}")
        try:
            data = _fetch(url)
            target = ast_dir / name
            tmp = Path(str(target) + ".new")
            tmp.write_bytes(data)
            tmp.replace(target)
            report["files"].append(str(target))
        except Exception as exc:
            report["errors"].append(f"protocol_ast/{name}: {exc}")

    (ast_dir / ".update_ref").write_text(f"{ref}\n{base}\n", encoding="utf-8")
    return report


def pcap_search_roots() -> list[Path]:
    home = Path.home()
    return [
        home / "storage" / "downloads" / "PCAPdroid",
        home / "storage" / "shared" / "Download" / "PCAPdroid",
        home / "storage" / "downloads",
        home / "downloads",
        home / "Download",
        Path("/sdcard/Download/PCAPdroid"),
        Path("/sdcard/Download"),
    ]


def iter_pcaps_under(roots: list[Path] | None = None) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for root in roots or pcap_search_roots():
        if not root.is_dir():
            continue
        try:
            for p in root.iterdir():
                if not p.is_file():
                    continue
                if p.suffix.lower() not in {".pcap", ".pcapng"}:
                    continue
                rp = p.resolve()
                if rp in seen:
                    continue
                seen.add(rp)
                out.append(p)
        except OSError:
            continue
    return out


def pick_newest_pcap(
    paths: list[str | Path] | None = None,
    *,
    also_search_defaults: bool = True,
) -> Path | None:
    """
    Pick newest capture.

    Merges shell-glob args with PCAPdroid folders (Termux often keeps
    fresh dumps in ~/storage/downloads/PCAPdroid/, not ~/downloads/).
    """
    cands: list[Path] = []
    seen: set[Path] = set()
    for p in paths or []:
        path = Path(p).expanduser()
        if path.is_file():
            rp = path.resolve()
            if rp not in seen:
                seen.add(rp)
                cands.append(path)
    if also_search_defaults:
        for p in iter_pcaps_under():
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                cands.append(p)
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)
