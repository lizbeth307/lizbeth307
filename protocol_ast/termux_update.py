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
)
ROOT_FILES = ("analyze_pcap.py", "probe_network.py")


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


def pick_newest_pcap(paths: list[str | Path]) -> Path | None:
    """From a shell glob expansion, pick the newest existing capture file."""
    cands: list[Path] = []
    for p in paths:
        path = Path(p).expanduser()
        if path.is_file():
            cands.append(path)
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)
