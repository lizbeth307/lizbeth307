"""
Inject Frida Gadget + autonomous SSL-unpin script into an APK (no root, no PC).

Uses Frida 16.7.19 (Java bridge bundled) in Gadget *script* mode so the app
self-hooks on launch — no adb / frida-tools host required.
"""

from __future__ import annotations

import lzma
import os
import re
import ssl
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

FRIDA_VERSION = "16.7.19"
APKTOOL_JAR_URL = (
    "https://github.com/iBotPeaches/Apktool/releases/download/v2.11.1/apktool_2.11.1.jar"
)
UBER_SIGNER_URL = (
    "https://github.com/patrickfav/uber-apk-signer/releases/download/"
    "v1.3.0/uber-apk-signer-1.3.0.jar"
)

ABI_MAP = {
    "arm64-v8a": "arm64",
    "armeabi-v7a": "arm",
    "x86": "x86",
    "x86_64": "x86_64",
}

ANDROID_NS = "http://schemas.android.com/apk/res/android"
ET.register_namespace("android", ANDROID_NS)


def _fetch(url: str, dest: Path, timeout: float = 120.0) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "protocol-ast-frida-gadget/3.8"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        data = resp.read()
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return dest


def tools_dir(home: Path | None = None) -> Path:
    h = home or Path.home()
    d = h / "unpin_work" / "tools"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ensure_apktool(home: Path | None = None) -> Path:
    jar = tools_dir(home) / "apktool.jar"
    return _fetch(APKTOOL_JAR_URL, jar)


def ensure_uber_signer(home: Path | None = None) -> Path:
    jar = tools_dir(home) / "uber-apk-signer.jar"
    return _fetch(UBER_SIGNER_URL, jar)


def gadget_url(frida_abi: str, version: str = FRIDA_VERSION) -> str:
    return (
        f"https://github.com/frida/frida/releases/download/{version}/"
        f"frida-gadget-{version}-android-{frida_abi}.so.xz"
    )


def ensure_gadget(apk_abi: str, home: Path | None = None, version: str = FRIDA_VERSION) -> Path:
    frida_abi = ABI_MAP[apk_abi]
    out = tools_dir(home) / f"libfrida-gadget-{version}-{apk_abi}.so"
    if out.exists() and out.stat().st_size > 0:
        return out
    xz_path = tools_dir(home) / f"frida-gadget-{version}-android-{frida_abi}.so.xz"
    _fetch(gadget_url(frida_abi, version), xz_path)
    raw = lzma.decompress(xz_path.read_bytes())
    out.write_bytes(raw)
    return out


def default_script_path() -> Path:
    return Path(__file__).resolve().parent / "frida_ssl_unpin.js"


def gadget_config_json() -> str:
    # Relative path: resolved next to libfrida-gadget.so inside the APK lib dir.
    return (
        '{\n'
        '  "interaction": {\n'
        '    "type": "script",\n'
        '    "path": "libfrida-gadget.script.so"\n'
        "  }\n"
        "}\n"
    )


def detect_apis_in_apk(apk: Path) -> list[str]:
    abis: set[str] = set()
    with zipfile.ZipFile(apk) as zf:
        for name in zf.namelist():
            m = re.match(r"lib/(arm64-v8a|armeabi-v7a|x86_64|x86)/", name)
            if m:
                abis.add(m.group(1))
    if not abis:
        abis.add("arm64-v8a")
    # Prefer 64-bit first for download order
    order = ["arm64-v8a", "armeabi-v7a", "x86_64", "x86"]
    return [a for a in order if a in abis]


def _android_name(elem: ET.Element, attr: str) -> str | None:
    return elem.attrib.get(f"{{{ANDROID_NS}}}{attr}") or elem.attrib.get(attr)


def _set_android(elem: ET.Element, attr: str, value: str) -> None:
    elem.set(f"{{{ANDROID_NS}}}{attr}", value)


def find_application_class(manifest: Path) -> str | None:
    tree = ET.parse(manifest)
    root = tree.getroot()
    app = root.find("application")
    if app is None:
        return None
    name = _android_name(app, "name")
    if not name or name.startswith("android."):
        return None
    return name


def package_name(manifest: Path) -> str:
    root = ET.parse(manifest).getroot()
    return root.attrib.get("package") or "app"


def resolve_smali_class(decoded: Path, class_name: str, package: str) -> Path | None:
    """Map com.foo.Bar or .Bar → smali path under smali*/."""
    if class_name.startswith("."):
        class_name = package + class_name
    rel = class_name.replace(".", "/") + ".smali"
    for smali_root in sorted(decoded.glob("smali*")):
        cand = smali_root / rel
        if cand.is_file():
            return cand
    return None


_LOAD_SNIPPET = (
    '    const-string v0, "frida-gadget"\n'
    "    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V\n"
)


def _bump_locals(method_head: str) -> str:
    def repl_locals(m: re.Match[str]) -> str:
        n = int(m.group(1))
        return f".locals {max(n, 1)}"

    def repl_regs(m: re.Match[str]) -> str:
        n = int(m.group(1))
        return f".registers {max(n, 2)}"

    out = re.sub(r"\.locals\s+(\d+)", repl_locals, method_head, count=1)
    out = re.sub(r"\.registers\s+(\d+)", repl_regs, out, count=1)
    return out


def _skip_method_prologue(lines: list[str]) -> int:
    """Index after .locals/.registers/.prologue/.param/.annotation block."""
    i = 0
    while i < len(lines):
        s = lines[i].lstrip()
        if s.strip() == "":
            i += 1
            continue
        if s.startswith(".locals") or s.startswith(".registers") or s.startswith(".prologue"):
            i += 1
            continue
        if s.startswith(".param"):
            i += 1
            continue
        if s.startswith(".annotation"):
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith(".end annotation"):
                i += 1
            if i < len(lines):
                i += 1
            continue
        break
    return i


def inject_load_library_smali(smali: str) -> tuple[str, str]:
    """
    Inject System.loadLibrary(\"frida-gadget\") into Application smali.
    Prefers attachBaseContext; falls back to onCreate; else creates attachBaseContext.
    Returns (new_smali, note).
    """
    if 'const-string v0, "frida-gadget"' in smali and "loadLibrary" in smali:
        return smali, "already_injected"

    m = re.search(
        r"(\.method[^\n]*attachBaseContext\(Landroid/content/Context;\)V\n)(.*?)(\n\.end method)",
        smali,
        re.S,
    )
    if m:
        head, body, end = m.group(1), m.group(2), m.group(3)
        head = _bump_locals(head)
        body = re.sub(
            r"^(\s*)\.locals\s+(\d+)",
            lambda mm: f"{mm.group(1)}.locals {max(int(mm.group(2)), 1)}",
            body,
            count=1,
            flags=re.M,
        )
        lines = body.splitlines(keepends=True)
        insert_at = _skip_method_prologue(lines)
        new_body = "".join(lines[:insert_at]) + _LOAD_SNIPPET + "".join(lines[insert_at:])
        return smali[: m.start()] + head + new_body + end + smali[m.end() :], "attachBaseContext"

    m = re.search(
        r"(\.method[^\n]*onCreate\(\)V\n)(.*?)(\n\.end method)",
        smali,
        re.S,
    )
    if m:
        head, body, end = m.group(1), m.group(2), m.group(3)
        head = _bump_locals(head)
        body = re.sub(
            r"^(\s*)\.locals\s+(\d+)",
            lambda mm: f"{mm.group(1)}.locals {max(int(mm.group(2)), 1)}",
            body,
            count=1,
            flags=re.M,
        )
        super_m = re.search(
            r"(invoke-super \{[^}]+\}, Landroid/app/Application;->onCreate\(\)V\n)",
            body,
        )
        if super_m:
            idx = super_m.end()
            new_body = body[:idx] + _LOAD_SNIPPET + body[idx:]
        else:
            lines = body.splitlines(keepends=True)
            insert_at = _skip_method_prologue(lines)
            new_body = "".join(lines[:insert_at]) + _LOAD_SNIPPET + "".join(lines[insert_at:])
        return smali[: m.start()] + head + new_body + end + smali[m.end() :], "onCreate"

    stub = (
        "\n.method protected attachBaseContext(Landroid/content/Context;)V\n"
        "    .locals 1\n"
        "    invoke-super {p0, p1}, Landroid/app/Application;->attachBaseContext(Landroid/content/Context;)V\n"
        f"{_LOAD_SNIPPET}"
        "    return-void\n"
        ".end method\n"
    )
    return smali.rstrip() + "\n" + stub, "created_attachBaseContext"


def write_frida_application(decoded: Path) -> str:
    """Create com.signal.pin.FridaApp Application class. Returns class name."""
    class_name = "com.signal.pin.FridaApp"
    smali_dir = decoded / "smali" / "com" / "signal" / "pin"
    smali_dir.mkdir(parents=True, exist_ok=True)
    (smali_dir / "FridaApp.smali").write_text(
        """.class public Lcom/signal/pin/FridaApp;
.super Landroid/app/Application;
.source "FridaApp.java"

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Landroid/app/Application;-><init>()V
    return-void
.end method

.method protected attachBaseContext(Landroid/content/Context;)V
    .locals 1
    invoke-super {p0, p1}, Landroid/app/Application;->attachBaseContext(Landroid/content/Context;)V
    const-string v0, "frida-gadget"
    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V
    return-void
.end method
""",
        encoding="utf-8",
    )
    return class_name


def patch_manifest(manifest: Path, application_class: str | None) -> None:
    tree = ET.parse(manifest)
    root = tree.getroot()
    app = root.find("application")
    if app is None:
        raise RuntimeError("AndroidManifest.xml has no <application>")
    if application_class:
        _set_android(app, "name", application_class)
    _set_android(app, "extractNativeLibs", "true")
    # Ensure INTERNET (games already have it)
    perms = {
        (_android_name(p, "name") or "")
        for p in root.findall("uses-permission")
    }
    if "android.permission.INTERNET" not in perms:
        pe = ET.Element("uses-permission")
        _set_android(pe, "name", "android.permission.INTERNET")
        root.insert(0, pe)
    tree.write(manifest, encoding="utf-8", xml_declaration=True)


def place_gadget_files(
    decoded: Path,
    abis: list[str],
    script: Path,
    home: Path | None = None,
    version: str = FRIDA_VERSION,
) -> list[str]:
    placed: list[str] = []
    script_bytes = script.read_bytes()
    config_bytes = gadget_config_json().encode("utf-8")
    for abi in abis:
        libdir = decoded / "lib" / abi
        libdir.mkdir(parents=True, exist_ok=True)
        gadget = ensure_gadget(abi, home=home, version=version)
        (libdir / "libfrida-gadget.so").write_bytes(gadget.read_bytes())
        (libdir / "libfrida-gadget.config.so").write_bytes(config_bytes)
        (libdir / "libfrida-gadget.script.so").write_bytes(script_bytes)
        placed.append(abi)
    return placed


def patch_application_loader(decoded: Path) -> str:
    manifest = decoded / "AndroidManifest.xml"
    pkg = package_name(manifest)
    app_cls = find_application_class(manifest)
    if app_cls:
        smali_path = resolve_smali_class(decoded, app_cls, pkg)
        if smali_path and smali_path.is_file():
            text = smali_path.read_text(encoding="utf-8", errors="replace")
            new_text, note = inject_load_library_smali(text)
            smali_path.write_text(new_text, encoding="utf-8")
            patch_manifest(manifest, None)
            return f"patched {app_cls} via {note}"
        # Class declared but smali missing — create wrapper
    new_cls = write_frida_application(decoded)
    patch_manifest(manifest, new_cls)
    if app_cls:
        return f"created {new_cls} (original {app_cls} smali missing)"
    return f"created {new_cls}"


def _java() -> str:
    return os.environ.get("JAVA_HOME", "") and str(Path(os.environ["JAVA_HOME"]) / "bin" / "java") or "java"


def run_apktool(jar: Path, args: list[str], cwd: Path | None = None) -> None:
    cmd = [_java(), "-jar", str(jar), *args]
    subprocess.run(cmd, check=True, cwd=str(cwd) if cwd else None)


def rebuild_sign(
    decoded: Path,
    out_apk: Path,
    home: Path | None = None,
) -> Path:
    apktool = ensure_apktool(home)
    unsigned = out_apk.with_suffix(".unsigned.apk")
    run_apktool(apktool, ["b", str(decoded), "-o", str(unsigned)])
    signer = ensure_uber_signer(home)
    out_dir = out_apk.parent
    subprocess.run(
        [
            _java(),
            "-jar",
            str(signer),
            "--apks",
            str(unsigned),
            "--out",
            str(out_dir),
            "--allowResign",
        ],
        check=True,
    )
    # uber-apk-signer names: *.apk → *-aligned-debugSigned.apk
    candidates = sorted(out_dir.glob("*debugSigned*.apk"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        candidates = sorted(out_dir.glob("*.apk"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise RuntimeError("uber-apk-signer produced no APK")
    signed = candidates[-1]
    if signed.resolve() != out_apk.resolve():
        out_apk.write_bytes(signed.read_bytes())
    return out_apk


def inject_apk(
    apk: Path,
    *,
    out_apk: Path | None = None,
    script: Path | None = None,
    home: Path | None = None,
    work_dir: Path | None = None,
    version: str = FRIDA_VERSION,
) -> dict:
    """
    Full pipeline: decode → gadget+script → smali loadLibrary → rebuild → sign.
    """
    apk = apk.expanduser().resolve()
    if not apk.is_file():
        raise FileNotFoundError(apk)
    home = home or Path.home()
    script = script or default_script_path()
    if not script.is_file():
        raise FileNotFoundError(f"SSL unpin script missing: {script}")

    work = work_dir or Path(tempfile.mkdtemp(prefix="frida_gadget_", dir=str(home / "unpin_work")))
    work.mkdir(parents=True, exist_ok=True)
    decoded = work / "decoded"
    if decoded.exists():
        import shutil

        shutil.rmtree(decoded)

    abis = detect_apis_in_apk(apk)
    apktool = ensure_apktool(home)
    run_apktool(apktool, ["d", str(apk), "-o", str(decoded), "-f"])

    loader_note = patch_application_loader(decoded)
    placed = place_gadget_files(decoded, abis, script, home=home, version=version)

    if out_apk is None:
        downloads = home / "storage" / "downloads"
        if not downloads.is_dir():
            downloads = home / "unpin_work"
        out_apk = downloads / f"{apk.stem}-frida.apk"
    out_apk = out_apk.expanduser().resolve()
    out_apk.parent.mkdir(parents=True, exist_ok=True)

    signed = rebuild_sign(decoded, out_apk, home=home)
    return {
        "apk": str(apk),
        "out": str(signed),
        "abis": placed,
        "frida": version,
        "loader": loader_note,
        "script": str(script),
        "work": str(work),
        "mode": "script",
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    p = argparse.ArgumentParser(description="Inject Frida Gadget + SSL unpin (no root)")
    p.add_argument("apk", nargs="?", help="Path to APK")
    p.add_argument("-o", "--out", help="Output APK path")
    p.add_argument("--script", help="Custom Frida JS (default: frida_ssl_unpin.js)")
    p.add_argument("--version", default=FRIDA_VERSION, help="Frida gadget version")
    p.add_argument("--guide", action="store_true", help="Print usage guide")
    args = p.parse_args(argv)

    if args.guide or not args.apk:
        print(
            """
Frida Gadget без root / без ПК
==============================
0) openjdk уже стоїть — ок

1) Дістати APK (один спосіб):
     ~/frida pull com.lilithgame.hgame.gp
   або App Manager → Save APK → Download/
   або:  ~/frida /sdcard/Download/game.apk

2) Інжект:
     ~/scan update && ~/frida

3) Встанови *-frida.apk (зняти стару гру)

4) PCAPdroid MITM + Block QUIC → гра 30–60с → Stop

5) ~/scan mine  → app-global* / psp-api* мають стати OPEN

Що робить:
  • вшиває libfrida-gadget.so (Frida 16.7.19)
  • script-режим: ssl_unpin.js стартує сам (без adb)
  • Java TrustManager + native BoringSSL/curl/mbedtls hooks

Якщо досі SEALED — pin ще глибший / integrity; пиши лог.
""".strip()
        )
        return 0 if args.guide or not args.apk else 2

    report = inject_apk(
        Path(args.apk),
        out_apk=Path(args.out) if args.out else None,
        script=Path(args.script) if args.script else None,
        version=args.version,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print()
    print("NEXT: install", report["out"], "→ PCAPdroid MITM → ~/scan mine")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
