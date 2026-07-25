"""Detect runtime: Android (Termux), cloud container, or desktop."""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RuntimeEnv:
    kind: str  # android | cloud | desktop
    iface: str | None
    can_tcpdump: bool
    can_raw_capture: bool
    notes: list[str]

    @property
    def label(self) -> str:
        return self.kind


def _has_tcpdump() -> bool:
    from shutil import which
    return which("tcpdump") is not None


def _pick_iface() -> str | None:
    net = Path("/sys/class/net")
    if not net.exists():
        return None
    preferred = ("wlan0", "wlo1", "eth0", "en0", "rmnet0", "ccmni0", "rndis0")
    present = {p.name for p in net.iterdir() if p.is_dir()}
    for name in preferred:
        if name in present:
            return name
    for name in sorted(present - {"lo"}):
        return name
    return None


def _is_android() -> bool:
    if os.environ.get("TERMUX_VERSION"):
        return True
    if Path("/system/build.prop").exists():
        return True
    # Не викликаємо platform.platform() — на Termux дає grep /proc/stat errors
    return False


def _is_cloud() -> bool:
    if Path("/.dockerenv").exists():
        return True
    host = socket.gethostname().lower()
    if any(x in host for x in ("ec2", "cursor", "container", "pod")):
        return True
    return False


def detect_runtime() -> RuntimeEnv:
    notes: list[str] = []
    iface = _pick_iface()
    has_tcpdump = _has_tcpdump()

    if _is_android():
        notes.append("Android: без root використовуйте PCAPdroid → export .pcap")
        if has_tcpdump:
            notes.append("tcpdump знайдено (можливо root/Termux)")
        return RuntimeEnv(
            kind="android",
            iface=iface,
            can_tcpdump=has_tcpdump,
            can_raw_capture=has_tcpdump,
            notes=notes,
        )

    if _is_cloud():
        notes.append("Cloud/container: eth0 ≠ ваш Wi-Fi, компенсуємо active-probe")
        return RuntimeEnv(
            kind="cloud",
            iface=iface or "eth0",
            can_tcpdump=has_tcpdump,
            can_raw_capture=has_tcpdump,
            notes=notes,
        )

    notes.append("Desktop: можна tcpdump або зовнішній .pcap")
    return RuntimeEnv(
        kind="desktop",
        iface=iface,
        can_tcpdump=has_tcpdump,
        can_raw_capture=has_tcpdump,
        notes=notes,
    )


def android_pcap_hints() -> list[Path]:
    """Типові шляхи PCAPdroid / Termux на телефоні."""
    home = Path.home()
    candidates = [
        home / "downloads",
        home / "Downloads",
        home / "storage" / "downloads",
        home / "storage" / "shared" / "Download",
        Path("/sdcard/Download"),
        Path("/sdcard/Downloads"),
        Path("/storage/emulated/0/Download"),
        Path("/storage/emulated/0/Downloads"),
        Path("."),
    ]
    patterns = ("*.pcap", "*.pcapng", "PCAPdroid*.pcap")
    found: list[Path] = []
    seen: set[Path] = set()
    for base in candidates:
        if not base.exists():
            continue
        for pat in patterns:
            for p in sorted(base.glob(pat)):
                if p.is_file() and p not in seen:
                    seen.add(p)
                    found.append(p)
    return sorted(found, key=lambda p: p.stat().st_mtime, reverse=True)
