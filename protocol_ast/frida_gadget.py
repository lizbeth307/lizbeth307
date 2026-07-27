"""
Inject Frida Gadget + autonomous SSL-unpin script into an APK (no root, no PC).

Uses Frida 16.7.19 (Java bridge bundled) in Gadget *script* mode so the app
self-hooks on launch — no adb / frida-tools host required.
"""

from __future__ import annotations

import lzma
import os
import re
import shutil
import ssl
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

PATCH_SO_CANDIDATES = (
    "libil2cpp.so",
    "libunity.so",
    "libmain.so",
    "libUE4.so",
    "libcocos2djs.so",
    "libcocos2dcpp.so",
    "libc++_shared.so",
)

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


def probe_script_path() -> Path:
    return Path(__file__).resolve().parent / "frida_probe.js"


def prepare_unpin_script(mode: str = "java", script: Path | None = None, work: Path | None = None) -> Path:
    """
    Bake FRIDA unpin MODE into a temp script copy.
    mode: probe | java | native
    """
    mode = (mode or "java").strip().lower()
    if mode in ("full", "all"):
        mode = "native"
    if mode == "probe":
        src = script or probe_script_path()
    else:
        src = script or default_script_path()
    if not src.is_file():
        raise FileNotFoundError(src)
    text = src.read_text(encoding="utf-8", errors="replace")
    if mode != "probe":
        text = re.sub(
            r'var MODE = "[^"]*";',
            f'var MODE = "{mode}";',
            text,
            count=1,
        )
    out_dir = work or Path(tempfile.mkdtemp(prefix="frida_script_"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"frida_unpin_{mode}.js"
    out.write_text(text, encoding="utf-8")
    print(f"[*] unpin script MODE={mode} → {out}", flush=True)
    return out


def gadget_config_json() -> str:
    # Relative path: resolved next to libfrida-gadget.so inside the APK lib dir.
    return (
        '{\n'
        '  "interaction": {\n'
        '    "type": "script",\n'
        '    "path": "libfrida-gadget.script.so"\n'
        "  },\n"
        '  "teardown": "minimal"\n'
        "}\n"
    )


def detect_native_abis(apk: Path) -> list[str]:
    """ABIs that actually have lib/<abi>/… entries. Empty if none (config/density splits)."""
    abis: set[str] = set()
    with zipfile.ZipFile(apk) as zf:
        for name in zf.namelist():
            m = re.match(r"lib/(arm64-v8a|armeabi-v7a|x86_64|x86)/", name)
            if m:
                abis.add(m.group(1))
    order = ["arm64-v8a", "armeabi-v7a", "x86_64", "x86"]
    return [a for a in order if a in abis]


def detect_apis_in_apk(apk: Path) -> list[str]:
    abis = detect_native_abis(apk)
    if not abis:
        abis = ["arm64-v8a"]
    return abis


def file_magic(path: Path, n: int = 16) -> bytes:
    with Path(path).open("rb") as f:
        return f.read(n)


def describe_magic(head: bytes) -> str:
    if head[:2] == b"PK":
        return "zip/apk"
    if head[:3] == b"\x1f\x8b\x08":
        return "gzip"
    if head[:4] == b"\x28\xb5\x2f\xfd":
        return "zstd"
    if head[:4] == b"\x37\x7a\xbc\xaf":
        return "7z"
    if len(head) >= 262 and head[257:262] == b"ustar":
        return "tar"
    if head[:4] == b"Rar!":
        return "rar"
    if not head or all(b == 0 for b in head):
        return "empty/zeros"
    return "unknown"


def probe_bundle(path: Path) -> dict:
    """Diagnose why an .apks may fail to open (FUSE / corrupt / wrong type)."""
    path = Path(path).expanduser()
    rep: dict = {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "size": path.stat().st_size if path.exists() else 0,
        "magic_hex": "",
        "magic": "",
        "zip_ok": False,
        "zip_error": "",
        "apk_members": [],
    }
    if path.is_dir():
        apks = sorted(p.name for p in path.glob("*.apk"))
        rep["magic"] = "directory"
        rep["apk_members"] = apks
        rep["zip_ok"] = len(apks) >= 1
        return rep
    if not path.is_file():
        return rep
    try:
        head = file_magic(path, 16)
        rep["magic_hex"] = head.hex(" ")
        rep["magic"] = describe_magic(head)
    except OSError as exc:
        rep["zip_error"] = f"read: {exc}"
        return rep
    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            members = [
                n
                for n in zf.namelist()
                if n.lower().endswith(".apk") and not n.endswith("/")
            ]
            rep["zip_ok"] = bad is None
            rep["apk_members"] = sorted(members)
            if bad:
                rep["zip_error"] = f"corrupt entry: {bad}"
    except Exception as exc:
        rep["zip_error"] = str(exc)
    return rep


def looks_like_apks_bundle(path: Path) -> bool:
    """True for App Manager / SAI .apks (or .xapk) zip of split APKs, or a splits dir."""
    path = Path(path)
    if path.is_dir():
        apks = list(path.glob("*.apk"))
        return len(apks) >= 1 and (
            any(p.name.lower() == "base.apk" for p in apks) or len(apks) >= 2
        )
    if not path.is_file():
        return False
    suf = path.suffix.lower()
    if suf in (".apks", ".xapk", ".apkm"):
        return True
    # bare zip that contains base.apk + another *.apk
    if suf != ".zip":
        return False
    try:
        with zipfile.ZipFile(path) as zf:
            apks = [n for n in zf.namelist() if n.lower().endswith(".apk") and not n.endswith("/")]
    except Exception:
        return False
    return any(Path(n).name.lower() == "base.apk" for n in apks) and len(apks) >= 2


def list_bundle_apk_members(bundle: Path) -> list[str]:
    with zipfile.ZipFile(bundle) as zf:
        return sorted(
            n
            for n in zf.namelist()
            if n.lower().endswith(".apk") and not n.endswith("/") and not n.startswith("__MACOSX/")
        )


def materialize_local_copy(src: Path, dest_dir: Path) -> Path:
    """
    Copy /sdcard file into Termux home before zip random-access.
    Android FUSE/sdcardfs often breaks ZipFile seek → BadZipFile.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / ("_local_" + re.sub(r"[^\w.\-]+", "_", src.name))
    if dest.exists():
        dest.unlink()
    print(f"[*] copy → Termux home (avoid /sdcard FUSE zip bugs): {dest}", flush=True)
    # Prefer cp for progress on huge files; fall back to shutil
    if shutil.which("cp"):
        subprocess.run(["cp", "-f", str(src), str(dest)], check=True)
    else:
        shutil.copy2(src, dest)
    if dest.stat().st_size != src.stat().st_size:
        raise RuntimeError(
            f"copy size mismatch: src={src.stat().st_size} dest={dest.stat().st_size}"
        )
    return dest


def extract_apks_archive(bundle: Path, extract_dir: Path) -> None:
    """Extract .apks/.xapk/.zip into extract_dir (must exist, empty-ish)."""
    errors: list[str] = []
    # 1) stdlib zipfile
    try:
        with zipfile.ZipFile(bundle) as zf:
            zf.extractall(extract_dir)
        return
    except Exception as exc:
        errors.append(f"zipfile: {exc}")
        print(f"[!] zipfile failed: {exc}", flush=True)

    # 2) system unzip
    if shutil.which("unzip"):
        proc = subprocess.run(
            ["unzip", "-o", str(bundle), "-d", str(extract_dir)],
            check=False,
            capture_output=True,
            text=True,
            errors="replace",
        )
        if proc.returncode == 0 and any(extract_dir.rglob("*.apk")):
            return
        errors.append(f"unzip: {(proc.stderr or proc.stdout or '')[:200]}")

    # 3) bsdtar / tar
    for tar in ("bsdtar", "tar"):
        if not shutil.which(tar):
            continue
        proc = subprocess.run(
            [tar, "-xf", str(bundle), "-C", str(extract_dir)],
            check=False,
            capture_output=True,
            text=True,
            errors="replace",
        )
        if proc.returncode == 0 and any(extract_dir.rglob("*.apk")):
            return
        errors.append(f"{tar}: {(proc.stderr or proc.stdout or '')[:160]}")

    head = b""
    try:
        head = file_magic(bundle, 16)
    except OSError:
        pass
    raise RuntimeError(
        "не вдалось відкрити .apks як архів.\n"
        f"  magic: {head.hex(' ') if head else '?'} ({describe_magic(head)})\n"
        f"  size:  {bundle.stat().st_size}\n"
        f"  path:  {bundle}\n"
        "App Manager .apks має бути ZIP (байти PK…). Якщо magic інший — файл битий.\n"
        "Обхід:\n"
        "  1) ZArchiver / App Manager → Extract .apks у папку\n"
        "  2) ~/frida \"/sdcard/.../та_папка\"\n"
        "  3) або знову Save APK у App Manager\n"
        "Деталі: " + " | ".join(errors)
    )


def apk_quick_info(apk: Path) -> dict:
    """Cheap APK / .apks fingerprint for Termux picker (no aapt)."""
    apk = Path(apk)
    info: dict = {
        "path": str(apk),
        "name": apk.name,
        "size": apk.stat().st_size if apk.is_file() else 0,
        "unity": False,
        "il2cpp": False,
        "hint": "",
        "splits": 0,
        "bundle": False,
    }
    try:
        with zipfile.ZipFile(apk) as zf:
            names = zf.namelist()
    except Exception as exc:
        info["hint"] = f"bad-apk:{exc}"
        return info

    # Nested .apks / .xapk — scan member APKs for Unity / lilith hints
    nested = [n for n in names if n.lower().endswith(".apk") and not n.endswith("/")]
    if looks_like_apks_bundle(apk) or (len(nested) >= 2 and any(Path(n).name.lower() == "base.apk" for n in nested)):
        info["bundle"] = True
        info["splits"] = len(nested)
        blob_bits: list[str] = []
        try:
            with zipfile.ZipFile(apk) as outer:
                for member in nested[:8]:
                    blob_bits.append(member.lower())
                    try:
                        with zipfile.ZipFile(outer.open(member)) as inner:
                            inner_names = inner.namelist()
                    except Exception:
                        continue
                    lower = [n.lower() for n in inner_names]
                    if any("libil2cpp.so" in n for n in lower):
                        info["il2cpp"] = True
                    if info["il2cpp"] or any(
                        "libunity.so" in n or "/unity" in n or n.endswith("unitydefaultresources")
                        for n in lower
                    ):
                        info["unity"] = True
                    blob_bits.extend(lower[:80])
        except Exception:
            pass
        blob = "\n".join(blob_bits)
    else:
        lower = [n.lower() for n in names]
        info["il2cpp"] = any("libil2cpp.so" in n for n in lower)
        info["unity"] = info["il2cpp"] or any(
            "libunity.so" in n or "/unity" in n or n.endswith("unitydefaultresources") for n in lower
        )
        blob = "\n".join(names[:400])

    name_l = apk.name.lower()
    for needle, label in (
        ("lilith", "lilith"),
        ("hgame", "hgame"),
        ("afk", "afk-arena"),
    ):
        if needle in blob.lower() or needle in name_l:
            info["hint"] = label
            break
    if info["il2cpp"] and not info["hint"]:
        info["hint"] = "unity-il2cpp"
    elif info["unity"] and not info["hint"]:
        info["hint"] = "unity"
    if info["bundle"] and not info["hint"]:
        info["hint"] = f"splits:{info['splits']}"
    return info


def format_apk_choice(apk: Path) -> str:
    inf = apk_quick_info(apk)
    mb = inf["size"] / (1024 * 1024)
    tags = []
    if inf.get("bundle"):
        tags.append(f"APKS×{inf.get('splits') or '?'}")
    if inf["il2cpp"]:
        tags.append("IL2CPP")
    elif inf["unity"]:
        tags.append("Unity")
    if inf["hint"]:
        tags.append(inf["hint"])
    tag = (" [" + ", ".join(tags) + "]") if tags else ""
    return f"{inf['name']}  ({mb:.1f} MB){tag}"


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


def find_aapt() -> Path | None:
    """Termux/system aapt — apktool's bundled Linux aapt2 cannot run on Android."""
    for name in ("aapt2", "aapt"):
        found = shutil.which(name)
        if found:
            return Path(found)
    prefix = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
    for name in ("aapt2", "aapt"):
        cand = prefix / "bin" / name
        if cand.is_file() and os.access(cand, os.X_OK):
            return cand
    return None


def find_patchelf() -> Path | None:
    found = shutil.which("patchelf")
    if found:
        return Path(found)
    prefix = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
    cand = prefix / "bin" / "patchelf"
    if cand.is_file() and os.access(cand, os.X_OK):
        return cand
    return None


def find_zipalign() -> Path | None:
    found = shutil.which("zipalign")
    if found:
        return Path(found)
    prefix = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
    for cand in (
        prefix / "bin" / "zipalign",
        prefix / "libexec" / "zipalign",
        Path("/system/bin/zipalign"),
    ):
        if cand.is_file() and os.access(cand, os.X_OK):
            return cand
    # Sometimes shipped next to aapt
    aapt = find_aapt()
    if aapt:
        sib = aapt.parent / "zipalign"
        if sib.is_file() and os.access(sib, os.X_OK):
            return sib
    return None


def run_apktool(jar: Path, args: list[str], cwd: Path | None = None) -> None:
    cmd = [_java(), "-jar", str(jar), *args]
    subprocess.run(cmd, check=True, cwd=str(cwd) if cwd else None)


def ensure_debug_keystore(home: Path | None = None) -> Path:
    ks = tools_dir(home) / "debug.keystore"
    if ks.is_file():
        return ks
    subprocess.run(
        [
            "keytool",
            "-genkeypair",
            "-v",
            "-keystore",
            str(ks),
            "-alias",
            "androiddebugkey",
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "10000",
            "-storepass",
            "android",
            "-keypass",
            "android",
            "-dname",
            "CN=Android Debug,O=Android,C=US",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return ks


def _same_device(a: Path, b: Path) -> bool:
    try:
        return os.stat(a).st_dev == os.stat(b if b.exists() else b.parent).st_dev
    except OSError:
        try:
            return os.stat(a).st_dev == os.stat(b.parent).st_dev
        except OSError:
            return False


def _link_or_copy(src: Path, dest: Path) -> None:
    """Hardlink when possible (0 extra space), else copy.

    Android/Termux Python builds often omit os.link entirely (AttributeError).
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
        else:
            dest.unlink(missing_ok=True)
    link = getattr(os, "link", None)
    if callable(link):
        try:
            link(src, dest)
            return
        except OSError:
            pass
    shutil.copy2(src, dest)


def _symlink_or_skip(target: Path, dest: Path) -> bool:
    """Best-effort symlink; Android often blocks it. Returns True on success."""
    symlink = getattr(os, "symlink", None)
    if not callable(symlink):
        return False
    try:
        if dest.exists() or dest.is_symlink():
            if dest.is_dir() and not dest.is_symlink():
                shutil.rmtree(dest)
            else:
                dest.unlink(missing_ok=True)
        symlink(str(target), str(dest))
        return True
    except OSError:
        return False


def _move_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    shutil.move(str(src), str(dest))


def disk_free_bytes(path: Path) -> int:
    try:
        return int(shutil.disk_usage(path).free)
    except OSError:
        return 0


def choose_work_root(home: Path | None = None) -> Path:
    """Prefer /sdcard — Termux home is often tiny on Android."""
    home = home or Path.home()
    candidates = [
        Path("/sdcard/unpin_work"),
        Path("/storage/emulated/0/unpin_work"),
        home / "storage" / "shared" / "unpin_work",
        home / "unpin_work",
    ]
    scored: list[tuple[int, Path]] = []
    for c in candidates:
        try:
            c.mkdir(parents=True, exist_ok=True)
            probe = c / ".write_probe"
            probe.write_bytes(b"ok")
            probe.unlink()
        except OSError:
            continue
        scored.append((disk_free_bytes(c), c))
    if not scored:
        d = home / "unpin_work"
        d.mkdir(parents=True, exist_ok=True)
        return d
    scored.sort(key=lambda x: -x[0])
    best_free, best = scored[0]
    print(
        f"[*] work root: {best}  (free≈{best_free / (1024**3):.2f} GiB)",
        flush=True,
    )
    return best


def find_frida_install_targets(home: Path | None = None) -> list[dict]:
    """
    Locate newest patched AFK Arena outputs for SAI / App Manager install.
    Prefers *.apks bundles; also lists *-frida-splits/ dirs with base.apk.
    """
    home = home or Path.home()
    roots = [
        Path("/sdcard/Download"),
        Path("/storage/emulated/0/Download"),
        home / "storage" / "downloads",
        home / "storage" / "shared" / "Download",
        Path("/sdcard/AppManager/apks"),
        Path("/storage/emulated/0/AppManager/apks"),
        Path("/sdcard/unpin_work"),
        home / "unpin_work",
    ]
    seen: set[tuple[int, int, int]] = set()
    found: list[dict] = []

    def _add(path: Path, kind: str) -> None:
        try:
            st = path.stat()
            key = (st.st_ino, st.st_dev, st.st_size)
        except OSError:
            return
        if key in seen:
            return
        seen.add(key)
        name = path.name.lower()
        pri = 0
        if kind == "apks":
            pri += 100
        if "frida" in name:
            pri += 80
        if "afk" in name or "arena" in name or "lilith" in name or "hgame" in name:
            pri += 60
        if name == "afk-arena-frida.apks":
            pri += 40
        found.append(
            {
                "path": str(path),
                "kind": kind,
                "size": st.st_size,
                "mtime": st.st_mtime,
                "pri": pri,
            }
        )

    for root in roots:
        if not root.is_dir():
            continue
        try:
            for p in root.rglob("*-frida.apks"):
                if p.is_file():
                    _add(p, "apks")
            for p in root.rglob("AFK-Arena-frida.apks"):
                if p.is_file():
                    _add(p, "apks")
            for p in root.rglob("*-frida-splits"):
                if p.is_dir() and (p / "base.apk").is_file():
                    _add(p, "splits")
            for p in root.rglob("AFK-Arena-frida-splits"):
                if p.is_dir() and (p / "base.apk").is_file():
                    _add(p, "splits")
        except OSError:
            continue

    found.sort(key=lambda x: (-x["pri"], -x["mtime"], -x["size"]))
    return found


def pick_frida_install_target(home: Path | None = None) -> dict | None:
    cands = find_frida_install_targets(home)
    return cands[0] if cands else None


def cleanup_stale_work(work_root: Path, keep: Path | None = None) -> None:
    """Remove old frida_apks_* / frida_gadget_* temps to reclaim space."""
    if not work_root.is_dir():
        return
    for p in work_root.iterdir():
        if keep and p.resolve() == keep.resolve():
            continue
        name = p.name
        if not (
            name.startswith("frida_apks_")
            or name.startswith("frida_gadget_")
            or name.startswith("local_src")
            or name == "sign_out"
        ):
            continue
        try:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
            print(f"[*] cleaned stale: {p}", flush=True)
        except OSError:
            pass


def sign_apk_uber(
    unsigned: Path,
    out_apk: Path,
    home: Path | None = None,
    *,
    skip_zipalign: bool = False,
    consume_unsigned: bool = False,
    sign_dir: Path | None = None,
) -> Path:
    signer = ensure_uber_signer(home)
    # Sign into a private work dir so uber does not scan all of Download/
    home = home or Path.home()
    sign_dir = Path(sign_dir) if sign_dir else (tools_dir(home) / "sign_out")
    if sign_dir.exists():
        shutil.rmtree(sign_dir)
    sign_dir.mkdir(parents=True, exist_ok=True)
    local_unsigned = sign_dir / unsigned.name
    if consume_unsigned:
        _move_file(unsigned, local_unsigned)
    else:
        _link_or_copy(unsigned, local_unsigned)

    # uber-apk-signer: -o and --overwrite are mutually exclusive — use -o only.
    cmd = [
        _java(),
        "-jar",
        str(signer),
        "--apks",
        str(local_unsigned),
        "--out",
        str(sign_dir),
        "--allowResign",
    ]
    zipalign = None if skip_zipalign else find_zipalign()
    if zipalign:
        cmd.extend(["--zipAlignPath", str(zipalign)])
        print(f"[*] zipalign: {zipalign}", flush=True)
    else:
        cmd.append("--skipZipAlign")
        print("[*] no zipalign binary — --skipZipAlign", flush=True)

    subprocess.run(cmd, check=True)

    candidates = sorted(sign_dir.glob("*debugSigned*.apk"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        candidates = sorted(
            [p for p in sign_dir.glob("*.apk") if "unsigned" not in p.name.lower()],
            key=lambda p: p.stat().st_mtime,
        )
    if not candidates:
        raise RuntimeError("uber-apk-signer produced no APK")
    signed = candidates[-1]
    out_apk.parent.mkdir(parents=True, exist_ok=True)
    # move (not read_bytes) — critical for 600MB+ asset splits
    _move_file(signed, out_apk)
    # drop leftovers (unsigned / aligned intermediates)
    shutil.rmtree(sign_dir, ignore_errors=True)
    return out_apk


def sign_apk_jarsigner(
    unsigned: Path,
    out_apk: Path,
    home: Path | None = None,
    *,
    consume_unsigned: bool = False,
) -> Path:
    """Last-resort v1 signature (openjdk keytool/jarsigner)."""
    ks = ensure_debug_keystore(home)
    out_apk.parent.mkdir(parents=True, exist_ok=True)
    if consume_unsigned:
        _move_file(unsigned, out_apk)
    else:
        _link_or_copy(unsigned, out_apk)
    subprocess.run(
        [
            "jarsigner",
            "-sigalg",
            "SHA256withRSA",
            "-digestalg",
            "SHA-256",
            "-keystore",
            str(ks),
            "-storepass",
            "android",
            "-keypass",
            "android",
            str(out_apk),
            "androiddebugkey",
        ],
        check=True,
    )
    return out_apk


def sign_apk(
    unsigned: Path,
    out_apk: Path,
    home: Path | None = None,
    *,
    consume_unsigned: bool = False,
    sign_dir: Path | None = None,
) -> Path:
    """Sign APK with uber (v2/v3). Prefer zipalign; fall back to skip / jarsigner."""
    errors: list[str] = []
    attempts: list[bool] = []
    if find_zipalign():
        attempts.append(False)  # use zipalign
    attempts.append(True)  # skipZipAlign
    for skip in attempts:
        try:
            # Never consume inside uber retries — hardlink/copy into sign_dir instead.
            out = sign_apk_uber(
                unsigned,
                out_apk,
                home=home,
                skip_zipalign=skip,
                consume_unsigned=False,
                sign_dir=sign_dir,
            )
            if consume_unsigned and unsigned.exists():
                unsigned.unlink(missing_ok=True)
            return out
        except Exception as exc:
            errors.append(f"uber(skipZipAlign={skip}): {exc}")
            print(f"[!] uber-apk-signer failed: {exc}", flush=True)
    try:
        print("[*] falling back to jarsigner (v1 only — may fail install on Android 11+)", flush=True)
        out = sign_apk_jarsigner(
            unsigned, out_apk, home=home, consume_unsigned=consume_unsigned
        )
        if consume_unsigned and unsigned.exists():
            unsigned.unlink(missing_ok=True)
        return out
    except Exception as exc:
        errors.append(f"jarsigner: {exc}")
        raise RuntimeError("signing failed: " + " | ".join(errors)) from exc


def rebuild_sign(
    decoded: Path,
    out_apk: Path,
    home: Path | None = None,
) -> Path:
    """
    apktool rebuild without recompiling resources (avoids aapt2 $drawable bugs).
    Expects decode was done with apktool d -r (resources not decoded).
    """
    apktool = ensure_apktool(home)
    unsigned = out_apk.with_suffix(".unsigned.apk")
    # Do NOT pass --aapt: with -r decode, resources are copied as-is.
    run_apktool(apktool, ["b", str(decoded), "-o", str(unsigned)])
    return sign_apk(unsigned, out_apk, home=home)


def _pick_patch_so(libdir: Path) -> Path | None:
    for name in PATCH_SO_CANDIDATES:
        cand = libdir / name
        if cand.is_file():
            return cand
    for cand in sorted(libdir.glob("lib*.so")):
        low = cand.name.lower()
        if "frida" in low or "gadget" in low:
            continue
        return cand
    return None


def patchelf_add_needed(so_path: Path, needed: str = "libfrida-gadget.so") -> None:
    pe = find_patchelf()
    if not pe:
        raise RuntimeError("patchelf not found — run: pkg install patchelf")
    needed_list = subprocess.check_output(
        [str(pe), "--print-needed", str(so_path)], text=True, errors="replace"
    ).splitlines()
    if needed in needed_list:
        return
    subprocess.run([str(pe), "--add-needed", needed, str(so_path)], check=True)


def unzip_apk(apk: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(apk) as zf:
        zf.extractall(dest)


def zip_apk_tree(src: Path, out_apk: Path) -> None:
    """Full repack (legacy). Prefer rebuild_apk_surgical()."""
    if out_apk.exists():
        out_apk.unlink()
    with zipfile.ZipFile(out_apk, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(src).as_posix()
            if rel.startswith("META-INF/"):
                continue
            compress = (
                zipfile.ZIP_STORED
                if (rel.endswith(".so") or rel.endswith(".arsc"))
                else zipfile.ZIP_DEFLATED
            )
            zf.write(path, rel, compress_type=compress)


def rebuild_apk_surgical(
    orig_apk: Path,
    lib_overrides: dict[str, Path],
    out_apk: Path,
    work: Path | None = None,
    *,
    consume_orig: bool = False,
) -> None:
    """
    Prefer system `zip` update (keeps original APK structure).
    Fallback: Python copy with low extract_version (avoid Zip64 parse issues).
    """
    overrides = {k.replace("\\", "/"): v for k, v in lib_overrides.items()}
    if shutil.which("zip"):
        _rebuild_apk_system_zip(
            orig_apk, overrides, out_apk, work, consume_orig=consume_orig
        )
        return
    # Python fallback: always write a fresh out_apk, then drop orig if consumed.
    _rebuild_apk_python(orig_apk, overrides, out_apk)
    if consume_orig and orig_apk.exists() and orig_apk.resolve() != out_apk.resolve():
        orig_apk.unlink(missing_ok=True)


def _rebuild_apk_system_zip(
    orig_apk: Path,
    overrides: dict[str, Path],
    out_apk: Path,
    work: Path | None = None,
    *,
    consume_orig: bool = False,
) -> None:
    """link/move original → zip -d META-INF → zip -0 lib overrides."""
    work = work or out_apk.parent
    stage = work / "zip_stage"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)
    if orig_apk.resolve() == out_apk.resolve():
        pass
    elif consume_orig:
        _move_file(orig_apk, out_apk)
    else:
        # Must copy — `zip -d` mutates in place (hardlink would corrupt source).
        if out_apk.exists():
            out_apk.unlink()
        shutil.copy2(orig_apk, out_apk)
    # Remove old signatures (ignore if absent)
    subprocess.run(
        ["zip", "-d", str(out_apk), "META-INF/*"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    rels: list[str] = []
    for name, path in sorted(overrides.items()):
        dest = stage / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        # Force replace: delete old entry first (ignore if missing)
        subprocess.run(
            ["zip", "-d", str(out_apk.resolve()), name],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        rels.append(name)
    if not rels:
        return
    # -0 = store (no compression) for .so mmap
    cmd = ["zip", "-0", str(out_apk.resolve()), *rels]
    subprocess.run(cmd, check=True, cwd=str(stage))


def _rebuild_apk_python(
    orig_apk: Path,
    overrides: dict[str, Path],
    out_apk: Path,
) -> None:
    if out_apk.exists():
        out_apk.unlink()
    with zipfile.ZipFile(orig_apk, "r") as zin, zipfile.ZipFile(
        out_apk, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=False
    ) as zout:
        for info in zin.infolist():
            name = info.filename
            if name.endswith("/"):
                continue
            if name.startswith("META-INF/") or name.startswith("META-INF\\"):
                continue
            if name.replace("\\", "/") in overrides:
                continue
            data = zin.read(info.filename)
            new_info = zipfile.ZipInfo(filename=name, date_time=info.date_time)
            new_info.compress_type = info.compress_type
            new_info.external_attr = info.external_attr
            new_info.create_system = info.create_system
            new_info.create_version = getattr(info, "create_version", 20) or 20
            new_info.extract_version = min(getattr(info, "extract_version", 20) or 20, 20)
            new_info.flag_bits = info.flag_bits & ~0x8
            zout.writestr(new_info, data, compress_type=info.compress_type)
        for name, path in sorted(overrides.items()):
            data = path.read_bytes()
            info = zipfile.ZipInfo(filename=name)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            info.create_version = 20
            info.extract_version = 20
            zout.writestr(info, data, compress_type=zipfile.ZIP_STORED)


def pm_install(apk: Path) -> dict:
    """
    Try /system/bin/pm install. On unrooted Termux this usually fails with
    binder 'Failed transaction' — that is NOT an APK parse error.
    """
    apk = apk.expanduser().resolve()
    report: dict = {
        "apk": str(apk),
        "ok": False,
        "cmd": [],
        "output": "",
        "note": "",
        "verify": verify_apk(apk),
    }
    pm = None
    for cand in ("/system/bin/pm", "/system/xbin/pm", "pm"):
        if cand == "pm" and shutil.which("pm"):
            pm = "pm"
            break
        if Path(cand).is_file():
            pm = cand
            break
    if not pm:
        report["output"] = "pm binary not found"
        report["note"] = "Use: termux-open " + str(apk)
        return report
    cmd = [pm, "install", "-r", "-t", "--user", "current", str(apk)]
    report["cmd"] = cmd
    try:
        proc = subprocess.run(
            cmd, check=False, capture_output=True, text=True, errors="replace"
        )
        report["output"] = ((proc.stdout or "") + (proc.stderr or "")).strip()
        report["ok"] = proc.returncode == 0 and "Success" in report["output"]
    except Exception as exc:
        report["output"] = str(exc)
    if "Failed transaction" in report["output"]:
        report["note"] = (
            "Termux cannot call package manager (no root/Shizuku). "
            "This does NOT mean the APK is invalid. Install via UI:\n"
            f"  termux-open {apk}"
        )
    return report


def verify_apk(apk: Path, *, require_dex: bool = True) -> dict:
    """Quick sanity checks before install (aapt + zip integrity).

    Config / ABI splits often have no classes*.dex — pass require_dex=False.
    """
    report: dict = {"apk": str(apk), "ok": True, "errors": [], "badging": ""}
    if not apk.is_file() or apk.stat().st_size < 200:
        report["ok"] = False
        report["errors"].append("missing or tiny file")
        return report
    try:
        with zipfile.ZipFile(apk) as zf:
            bad = zf.testzip()
            if bad:
                report["ok"] = False
                report["errors"].append(f"zip corrupt: {bad}")
            names = set(zf.namelist())
            if "AndroidManifest.xml" not in names:
                report["ok"] = False
                report["errors"].append("no AndroidManifest.xml")
            has_dex = any(n.startswith("classes") and n.endswith(".dex") for n in names)
            if require_dex and not has_dex:
                report["ok"] = False
                report["errors"].append("no classes*.dex")
            report["has_dex"] = has_dex
            report["native_abis"] = detect_native_abis(apk)
    except Exception as exc:
        report["ok"] = False
        report["errors"].append(f"zip: {exc}")
    aapt = find_aapt()
    # prefer aapt (not aapt2) for dump badging
    aapt_bin = shutil.which("aapt") or (str(aapt) if aapt and aapt.name == "aapt" else None)
    if not aapt_bin:
        prefix = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
        if (prefix / "bin" / "aapt").is_file():
            aapt_bin = str(prefix / "bin" / "aapt")
    if aapt_bin:
        try:
            proc = subprocess.run(
                [aapt_bin, "dump", "badging", str(apk)],
                check=False,
                capture_output=True,
                text=True,
                errors="replace",
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            pkg_line = ""
            for line in out.splitlines():
                if line.startswith("package: name="):
                    pkg_line = line
                    break
            report["badging"] = pkg_line or ""
            # Config / ABI splits often have no useful badging — only hard-fail for base APKs.
            if not pkg_line and require_dex:
                report["ok"] = False
                report["errors"].append(
                    "aapt badging: no package name — "
                    + out.strip().replace("\n", " ")[:240]
                )
        except Exception as exc:
            if require_dex:
                report["ok"] = False
                report["errors"].append(f"aapt: {exc}")
    return report


def _download_folders(home: Path) -> list[Path]:
    folders: list[Path] = []
    for folder in (
        home / "storage" / "downloads",
        home / "storage" / "shared" / "Download",
        Path("/sdcard/Download"),
        Path("/storage/emulated/0/Download"),
        Path("/sdcard/AppManager/apks"),
        Path("/storage/emulated/0/AppManager/apks"),
    ):
        if folder.is_dir():
            folders.append(folder)
    return folders


def inject_apk_zip(
    apk: Path,
    *,
    out_apk: Path,
    script: Path,
    home: Path,
    work: Path,
    version: str = FRIDA_VERSION,
    require_dex: bool = True,
    copy_aliases: bool = True,
    abis: list[str] | None = None,
) -> dict:
    """
    Surgical inject: keep original ZIP entries, only patch/add lib/* + resign.
    """
    # Preflight: original must be a real installable APK (or a lib split)
    pre = verify_apk(apk, require_dex=require_dex)
    if not pre["ok"]:
        raise RuntimeError(
            "source APK failed verify — not a valid package:\n  "
            + "\n  ".join(pre["errors"])
            + "\nGet a fresh APK via App Manager (Save APK set), not a random dump."
        )
    print(f"[*] source OK: {pre.get('badging') or apk.name}", flush=True)

    root = work / "ziproot"
    unzip_apk(apk, root)
    if abis is None:
        abis = detect_native_abis(apk)
        if not abis:
            abis = detect_apis_in_apk(apk)
    placed = place_gadget_files(root, abis, script, home=home, version=version)
    patched: list[str] = []
    overrides: dict[str, Path] = {}
    for abi in placed:
        libdir = root / "lib" / abi
        target = _pick_patch_so(libdir)
        if not target:
            raise RuntimeError(f"no native .so to patchelf under lib/{abi}")
        patchelf_add_needed(target, "libfrida-gadget.so")
        patched.append(f"{abi}/{target.name}")
        # all gadget-related + patched target
        for p in libdir.iterdir():
            if not p.is_file():
                continue
            if p.name == target.name or p.name.startswith("libfrida-gadget"):
                overrides[f"lib/{abi}/{p.name}"] = p

    unsigned = work / (out_apk.stem + ".unsigned.apk")
    print("[*] surgical rebuild via system zip (preserve APK structure)…", flush=True)
    rebuild_apk_surgical(apk, overrides, unsigned, work=work)

    mid = verify_apk(unsigned, require_dex=require_dex)
    if not mid["ok"]:
        raise RuntimeError(
            "unsigned APK broken after inject:\n  " + "\n  ".join(mid["errors"])
        )

    signed = sign_apk(
        unsigned,
        out_apk,
        home=home,
        consume_unsigned=True,
        sign_dir=work / "sign_out",
    )
    post = verify_apk(signed, require_dex=require_dex)
    print(f"[*] verify signed: ok={post['ok']} {post.get('badging')}", flush=True)
    if not post["ok"]:
        raise RuntimeError(
            "signed APK failed verify (parse-error risk):\n  "
            + "\n  ".join(post["errors"])
        )

    if copy_aliases:
        for dest_name in ("AFK-Arena-frida.apk", f"{apk.stem}-frida.apk"):
            for folder in _download_folders(home):
                try:
                    shutil.copy2(signed, folder / dest_name)
                except OSError:
                    pass

    return {
        "apk": str(apk),
        "out": str(signed),
        "abis": placed,
        "frida": version,
        "loader": "patchelf DT_NEEDED ← " + ", ".join(patched),
        "script": str(script),
        "work": str(work),
        "mode": "script+surgical-zip",
        "verify": post,
    }


def resign_split_apk(
    apk: Path,
    out_apk: Path,
    home: Path,
    work: Path,
    *,
    consume_src: bool = False,
    sign_dir: Path | None = None,
) -> Path:
    """Strip META-INF + sign (same debug key as Frida-patched splits)."""
    unsigned = work / (out_apk.stem + ".unsigned.apk")
    if unsigned.exists():
        unsigned.unlink()
    rebuild_apk_surgical(
        apk, {}, unsigned, work=work, consume_orig=consume_src
    )
    # source already moved/copied away — free original if still present
    if consume_src and apk.exists() and apk.resolve() != unsigned.resolve():
        apk.unlink(missing_ok=True)
    signed = sign_apk(
        unsigned,
        out_apk,
        home=home,
        consume_unsigned=True,
        sign_dir=sign_dir,
    )
    return signed


def inject_apks_bundle(
    bundle: Path,
    *,
    out_apks: Path | None = None,
    script: Path | None = None,
    home: Path | None = None,
    work_dir: Path | None = None,
    version: str = FRIDA_VERSION,
    unpin_mode: str = "java",
) -> dict:
    """
    App Manager / SAI .apks (or a directory of split APKs): patch ABI split(s)
    that hold native libs, resign ALL splits with the same debug key, repack
    .apks + leave a SAI folder.

    Disk-aware: work on /sdcard when possible, extract one split at a time,
    move/consume sources, avoid duplicate 600MB+ copies.
    """
    bundle = Path(bundle).expanduser().resolve()
    if not bundle.exists():
        raise FileNotFoundError(bundle)
    is_dir = bundle.is_dir()
    if not is_dir and not looks_like_apks_bundle(bundle) and bundle.suffix.lower() not in (
        ".apks",
        ".xapk",
        ".apkm",
        ".zip",
    ):
        raise RuntimeError(f"not an .apks bundle: {bundle}")

    home = home or Path.home()
    work_root = choose_work_root(home)
    cleanup_stale_work(work_root)
    # Also scrub tiny Termux-home leftovers from older runs
    home_unpin = home / "unpin_work"
    if home_unpin.is_dir() and home_unpin.resolve() != work_root.resolve():
        cleanup_stale_work(home_unpin)

    work = work_dir or Path(tempfile.mkdtemp(prefix="frida_apks_", dir=str(work_root)))
    work.mkdir(parents=True, exist_ok=True)
    sign_dir = work / "sign_out"
    script = prepare_unpin_script(unpin_mode, script=script, work=work / "script")
    if not script.is_file():
        raise FileNotFoundError(f"SSL unpin script missing: {script}")

    # Final outputs on shared storage (not Termux home)
    stem = re.sub(r"[^\w.\-]+", "_", bundle.stem).strip("_") or "game"
    if out_apks is None:
        downloads = Path("/sdcard/Download")
        for cand in (
            home / "storage" / "downloads",
            home / "storage" / "shared" / "Download",
            Path("/sdcard/Download"),
            Path("/storage/emulated/0/Download"),
            work_root,
        ):
            if cand.is_dir() or cand == work_root:
                try:
                    cand.mkdir(parents=True, exist_ok=True)
                    downloads = cand
                    break
                except OSError:
                    continue
        out_apks = downloads / f"{stem}-frida.apks"
    out_apks = Path(out_apks).expanduser().resolve()
    out_apks.parent.mkdir(parents=True, exist_ok=True)
    sai_dir = out_apks.with_name(out_apks.stem + "-splits")
    if sai_dir.exists():
        shutil.rmtree(sai_dir)
    sai_dir.mkdir(parents=True)

    src_label = str(bundle)
    member_names: list[str] = []
    local_bundle: Path | None = None
    dir_sources: list[Path] = []

    if is_dir:
        print(f"[*] using splits directory: {bundle}", flush=True)
        dir_sources = sorted(p for p in bundle.glob("*.apk") if p.is_file())
        member_names = [p.name for p in dir_sources]
    else:
        probe = probe_bundle(bundle)
        print(
            f"[*] probe: size={probe['size']} magic={probe['magic']} "
            f"hex={probe['magic_hex']} zip_ok={probe['zip_ok']}",
            flush=True,
        )
        # Prefer extract from /sdcard path if zip_ok — skip 475MB home copy when possible.
        # Fall back to local materialize if sequential extract fails.
        local_bundle = bundle
        if not probe.get("zip_ok"):
            local_bundle = materialize_local_copy(bundle, work / "local_src")
        else:
            # Small probe already sought OK on /sdcard — still copy only if extract fails.
            print("[*] will extract members one-by-one (no full unpack)", flush=True)
        try:
            with zipfile.ZipFile(local_bundle) as zf:
                member_names = sorted(
                    n
                    for n in zf.namelist()
                    if n.lower().endswith(".apk")
                    and not n.endswith("/")
                    and not n.startswith("__MACOSX/")
                )
        except Exception as exc:
            print(f"[!] list members failed ({exc}) — materialize local copy", flush=True)
            local_bundle = materialize_local_copy(bundle, work / "local_src")
            with zipfile.ZipFile(local_bundle) as zf:
                member_names = sorted(
                    n
                    for n in zf.namelist()
                    if n.lower().endswith(".apk")
                    and not n.endswith("/")
                    and not n.startswith("__MACOSX/")
                )

    if not member_names:
        raise RuntimeError(
            "no .apk members inside .apks — wrong export?\n"
            "Спробуй: ZArchiver → Extract → ~/frida /шлях/до/папки"
        )

    print(f"[*] splits: {len(member_names)}", flush=True)
    for name in member_names:
        print(f"    - {name}", flush=True)

    patched_reports: list[dict] = []
    signed_paths: list[Path] = []
    saw_native = False

    def _load_one(name: str) -> Path:
        """Extract/copy a single split into work/one/ and return its path."""
        nonlocal local_bundle
        one_dir = work / "one"
        if one_dir.exists():
            shutil.rmtree(one_dir)
        one_dir.mkdir(parents=True)
        dest = one_dir / Path(name).name
        if is_dir:
            src = next(p for p in dir_sources if p.name == name)
            shutil.copy2(src, dest)
            return dest
        assert local_bundle is not None
        try:
            with zipfile.ZipFile(local_bundle) as zf:
                with zf.open(name) as src_f, open(dest, "wb") as out_f:
                    shutil.copyfileobj(src_f, out_f, length=1024 * 1024)
        except Exception:
            # FUSE seek flake — materialize once then retry
            local_bundle = materialize_local_copy(bundle, work / "local_src")
            with zipfile.ZipFile(local_bundle) as zf:
                with zf.open(name) as src_f, open(dest, "wb") as out_f:
                    shutil.copyfileobj(src_f, out_f, length=1024 * 1024)
        return dest

    # Process smaller splits first so Frida inject finishes before huge asset resign
    def _member_size(name: str) -> int:
        if is_dir:
            for p in dir_sources:
                if p.name == name:
                    return p.stat().st_size
            return 0
        try:
            assert local_bundle is not None
            with zipfile.ZipFile(local_bundle) as zf:
                return int(zf.getinfo(name).file_size)
        except Exception:
            return 0

    ordered = sorted(member_names, key=_member_size)

    for name in ordered:
        out_name = Path(name).name
        dest = sai_dir / out_name
        print(
            f"[*] free≈{disk_free_bytes(work) / (1024**3):.2f} GiB before {out_name}",
            flush=True,
        )
        src = _load_one(name)
        size_mb = src.stat().st_size / (1024 * 1024)
        abis = detect_native_abis(src)
        print(
            f"[*] {out_name}: {size_mb:.1f} MiB  abis={abis or '-'}",
            flush=True,
        )
        split_work = work / ("w_" + re.sub(r"[^A-Za-z0-9_.-]+", "_", out_name))
        if split_work.exists():
            shutil.rmtree(split_work)
        split_work.mkdir(parents=True)

        try:
            if abis:
                saw_native = True
                print(f"[*] inject Frida → {out_name} ({', '.join(abis)})", flush=True)
                has_dex = verify_apk(src, require_dex=False).get("has_dex", False)
                rep = inject_apk_zip(
                    src,
                    out_apk=dest,
                    script=script,
                    home=home,
                    work=split_work,
                    version=version,
                    require_dex=bool(has_dex),
                    copy_aliases=False,
                    abis=abis,
                )
                patched_reports.append(rep)
            else:
                print(f"[*] resign only → {out_name}", flush=True)
                resign_split_apk(
                    src,
                    dest,
                    home=home,
                    work=split_work,
                    consume_src=True,
                    sign_dir=sign_dir,
                )
                post = verify_apk(dest, require_dex=False)
                if not post["ok"] and "no AndroidManifest.xml" in post["errors"]:
                    raise RuntimeError(
                        f"split broken after resign: {out_name}: {post['errors']}"
                    )
            signed_paths.append(dest)
        finally:
            # Drop per-split temps aggressively
            shutil.rmtree(work / "one", ignore_errors=True)
            shutil.rmtree(split_work, ignore_errors=True)
            shutil.rmtree(sign_dir, ignore_errors=True)

    # Drop local materialized .apks if any
    local_src_dir = work / "local_src"
    if local_src_dir.exists():
        shutil.rmtree(local_src_dir, ignore_errors=True)

    if not saw_native:
        raise RuntimeError(
            "жодного split з lib/<abi>/ — Frida gadget нікуди вшити.\n"
            "Перевір що в .apks є split_config.arm64_v8a.apk (або fat base)."
        )

    splits_bytes = sum(p.stat().st_size for p in sai_dir.glob("*.apk"))
    free = disk_free_bytes(out_apks.parent)
    packed = False
    if free < splits_bytes + 64 * 1024 * 1024:
        print(
            f"[!] мало місця для .apks-архіву "
            f"(free≈{free / (1024**3):.2f} GiB, need≈{splits_bytes / (1024**3):.2f} GiB) — "
            f"став з папки splits",
            flush=True,
        )
        out_apks = sai_dir  # install path is the folder
    else:
        if out_apks.exists():
            out_apks.unlink()
        print(f"[*] packing {out_apks} …", flush=True)
        # STORED: APKs already compressed; avoids huge recompress CPU/temp
        with zipfile.ZipFile(out_apks, "w", compression=zipfile.ZIP_STORED) as zf:
            for p in sorted(sai_dir.glob("*.apk")):
                zf.write(p, p.name)
        packed = True

    # Alias names on Download (no full copytree of multi-GB)
    if packed and out_apks.is_file():
        for folder in _download_folders(home):
            alias = folder / "AFK-Arena-frida.apks"
            try:
                if alias.resolve() != out_apks.resolve():
                    _link_or_copy(out_apks, alias)
            except OSError:
                pass
    alias_splits = Path("/sdcard/Download/AFK-Arena-frida-splits")
    try:
        if alias_splits.resolve() != sai_dir.resolve():
            _symlink_or_skip(sai_dir, alias_splits)
    except OSError:
        pass

    loaders = [r.get("loader", "") for r in patched_reports]
    return {
        "apk": src_label,
        "out": str(out_apks),
        "sai_dir": str(sai_dir),
        "splits": [str(p) for p in signed_paths],
        "patched": [r.get("apk") for r in patched_reports],
        "abis": sorted({a for r in patched_reports for a in r.get("abis", [])}),
        "frida": version,
        "loader": " | ".join(loaders),
        "script": str(script),
        "work": str(work),
        "mode": "script+apks-bundle",
        "install": (
            "Uninstall AFK Arena → install splits via SAI / App Manager:\n"
            f"  folder: {sai_dir}\n"
            + (f"  .apks: {out_apks}\n" if packed else "  (.apks skipped — low disk)\n")
            + "  (termux-open alone often cannot install multi-split)"
        ),
    }


def inject_apk_apktool(
    apk: Path,
    *,
    out_apk: Path,
    script: Path,
    home: Path,
    work: Path,
    version: str = FRIDA_VERSION,
) -> dict:
    """
    apktool d -r (keep binary resources) → smali loadLibrary → gadget → b → sign.
    Avoids aapt2 recompile of Material $avd_* drawables.
    """
    decoded = work / "decoded"
    if decoded.exists():
        shutil.rmtree(decoded)
    abis = detect_apis_in_apk(apk)
    apktool = ensure_apktool(home)
    # -r: do not decode resources (critical on modern Material APKs)
    run_apktool(apktool, ["d", "-r", "-f", str(apk), "-o", str(decoded)])
    # Manifest is still decoded as XML with -r; resources stay binary.
    loader_note = patch_application_loader(decoded)
    placed = place_gadget_files(decoded, abis, script, home=home, version=version)
    for abi in placed:
        libdir = decoded / "lib" / abi
        target = _pick_patch_so(libdir)
        if not target:
            continue
        try:
            patchelf_add_needed(target, "libfrida-gadget.so")
            loader_note += f" + patchelf {abi}/{target.name}"
        except Exception:
            pass
    signed = rebuild_sign(decoded, out_apk, home=home)
    return {
        "apk": str(apk),
        "out": str(signed),
        "abis": placed,
        "frida": version,
        "loader": loader_note,
        "script": str(script),
        "work": str(work),
        "mode": "script+apktool-r",
    }


def default_out_apk(apk: Path, home: Path) -> Path:
    downloads = home / "storage" / "downloads"
    if not downloads.is_dir():
        # Termux shared Download often appears here
        alt = home / "storage" / "shared" / "Download"
        downloads = alt if alt.is_dir() else home / "unpin_work"
    return downloads / f"{apk.stem}-frida.apk"


def inject_apk(
    apk: Path,
    *,
    out_apk: Path | None = None,
    script: Path | None = None,
    home: Path | None = None,
    work_dir: Path | None = None,
    version: str = FRIDA_VERSION,
    method: str = "auto",
    unpin_mode: str = "java",
) -> dict:
    """
    Inject Frida Gadget. Prefer zip+patchelf on Termux (no aapt2).
    Accepts single .apk or App Manager .apks / .xapk split bundles.
    method: auto | zip | apktool
    unpin_mode: probe | java | native
    """
    apk = apk.expanduser().resolve()
    if not apk.exists():
        raise FileNotFoundError(apk)
    home = home or Path.home()

    if (
        apk.is_dir()
        or looks_like_apks_bundle(apk)
        or apk.suffix.lower() in (".apks", ".xapk", ".apkm")
    ):
        print(
            "[*] detected split bundle (.apks / dir) — patch ABI split + resign all",
            flush=True,
        )
        return inject_apks_bundle(
            apk,
            out_apks=out_apk,
            script=script,
            home=home,
            work_dir=work_dir,
            version=version,
            unpin_mode=unpin_mode,
        )

    work_root = home / "unpin_work"
    work_root.mkdir(parents=True, exist_ok=True)
    work = work_dir or Path(tempfile.mkdtemp(prefix="frida_gadget_", dir=str(work_root)))
    work.mkdir(parents=True, exist_ok=True)
    script = prepare_unpin_script(unpin_mode, script=script, work=work / "script")
    if not script.is_file():
        raise FileNotFoundError(f"SSL unpin script missing: {script}")

    if out_apk is None:
        out_apk = default_out_apk(apk, home)
    out_apk = out_apk.expanduser().resolve()
    out_apk.parent.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []

    use_zip = method in ("auto", "zip")
    use_apktool = method in ("auto", "apktool")

    if use_zip and find_patchelf():
        try:
            print("[*] method=zip+patchelf (no apktool rebuild)", flush=True)
            return inject_apk_zip(
                apk, out_apk=out_apk, script=script, home=home, work=work, version=version
            )
        except Exception as exc:
            errors.append(f"zip+patchelf: {exc}")
            print(f"[!] zip+patchelf failed: {exc}", flush=True)
            # If unsigned exists, retry sign only (common: zipalign missing)
            unsigned = out_apk.with_suffix(".unsigned.apk")
            if unsigned.is_file():
                try:
                    print("[*] retry sign on existing unsigned APK…", flush=True)
                    signed = sign_apk(unsigned, out_apk, home=home)
                    return {
                        "apk": str(apk),
                        "out": str(signed),
                        "abis": detect_apis_in_apk(apk),
                        "frida": version,
                        "loader": "patchelf (sign retry)",
                        "script": str(script),
                        "work": str(work),
                        "mode": "script+zip",
                    }
                except Exception as exc2:
                    errors.append(f"sign-retry: {exc2}")
            if method == "zip":
                raise RuntimeError(" | ".join(errors)) from exc

    if use_zip and not find_patchelf() and method == "auto":
        print("[*] patchelf missing — try: pkg install patchelf", flush=True)

    if use_apktool:
        print("[*] method=apktool d -r (no resource recompile)", flush=True)
        try:
            return inject_apk_apktool(
                apk, out_apk=out_apk, script=script, home=home, work=work, version=version
            )
        except Exception as exc:
            errors.append(f"apktool: {exc}")
            raise RuntimeError(" | ".join(errors)) from exc

    raise RuntimeError(
        "No inject method available. Install: pkg install patchelf\n"
        + " | ".join(errors)
    )


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    import sys

    p = argparse.ArgumentParser(description="Inject Frida Gadget + SSL unpin (no root)")
    p.add_argument("apk", nargs="?", help="Path to APK, App Manager .apks, or splits dir")
    p.add_argument("-o", "--out", help="Output APK / .apks path")
    p.add_argument("--script", help="Custom Frida JS (default: frida_ssl_unpin.js)")
    p.add_argument("--version", default=FRIDA_VERSION, help="Frida gadget version")
    p.add_argument(
        "--method",
        choices=("auto", "zip", "apktool"),
        default="auto",
        help="auto: zip+patchelf first, else apktool+aapt",
    )
    p.add_argument(
        "--unpin-mode",
        choices=("probe", "java", "native", "full"),
        default="java",
        help="probe=no hooks (crash test); java=TrustManager only; native=+safe BoringSSL",
    )
    p.add_argument(
        "--sign-only",
        metavar="UNSIGNED_APK",
        help="Only zipalign+sign an existing *-frida.unsigned.apk",
    )
    p.add_argument(
        "--verify",
        metavar="APK",
        help="Verify APK zip/manifest/aapt before install",
    )
    p.add_argument(
        "--probe",
        metavar="PATH",
        help="Diagnose .apks / APK magic + zip integrity (no patch)",
    )
    p.add_argument(
        "--install",
        metavar="APK",
        nargs="?",
        const="",
        help="Find patched .apks / open with installer (optional path)",
    )
    p.add_argument(
        "--find-install",
        action="store_true",
        help="List newest *-frida.apks / *-frida-splits for install",
    )
    p.add_argument(
        "--resign",
        metavar="APK",
        help="Only strip META-INF + zipalign/sign (no Frida) — test if signing alone installs",
    )
    p.add_argument("--guide", action="store_true", help="Print usage guide")
    args = p.parse_args(argv)

    if args.find_install:
        cands = find_frida_install_targets()
        print(json.dumps(cands, indent=2, ensure_ascii=False))
        return 0 if cands else 1

    if args.probe:
        rep = probe_bundle(Path(args.probe).expanduser())
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        if not rep.get("zip_ok"):
            print(
                "\nЯкщо magic ≠ zip/apk — файл битий або не .apks.\n"
                "Обхід: ZArchiver Extract → ~/frida /шлях/до/папки_зі_сплітами",
                flush=True,
            )
        return 0 if rep.get("zip_ok") else 1

    if args.verify:
        rep = verify_apk(Path(args.verify).expanduser())
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep.get("ok") else 1

    if args.install is not None:
        target_path = (args.install or "").strip()
        if target_path:
            target = {"path": str(Path(target_path).expanduser()), "kind": "apks"}
        else:
            picked = pick_frida_install_target()
            if not picked:
                print(
                    "Немає *-frida.apks / *-frida-splits.\n"
                    "Спочатку: ~/frida \"/sdcard/AppManager/apks/AFK Arena_1.198.01.apks\"",
                    file=sys.stderr,
                )
                return 1
            target = picked
            print(f"[*] auto: {target['path']} ({target['kind']})", flush=True)
        # For single .apk try pm; for .apks just report path for shell termux-open
        pth = Path(target["path"])
        if pth.is_file() and pth.suffix.lower() == ".apk":
            rep = pm_install(pth)
            print(json.dumps(rep, indent=2, ensure_ascii=False))
            return 0 if rep.get("ok") else 1
        print(json.dumps(target, indent=2, ensure_ascii=False))
        print(
            "\nOPEN_THIS_FILE=" + target["path"],
            flush=True,
        )
        return 0

    if args.resign:
        src = Path(args.resign).expanduser().resolve()
        home = Path.home()
        out = Path(args.out).expanduser() if args.out else src.with_name(src.stem + "-resigned.apk")
        work = home / "unpin_work" / "resign"
        work.mkdir(parents=True, exist_ok=True)
        unsigned = work / (src.stem + ".unsigned.apk")
        rebuild_apk_surgical(src, {}, unsigned, work=work)
        signed = sign_apk(unsigned, out, home=home)
        print(json.dumps({"out": str(signed), "verify": verify_apk(signed)}, indent=2))
        print("NEXT: ~/frida install", signed)
        return 0

    if args.sign_only:
        unsigned = Path(args.sign_only).expanduser().resolve()
        if not unsigned.is_file():
            print(f"missing: {unsigned}", file=sys.stderr)
            return 1
        out = Path(args.out).expanduser() if args.out else unsigned.with_name(
            unsigned.name.replace(".unsigned.apk", ".apk").replace("-frida.unsigned.apk", "-frida.apk")
        )
        if out == unsigned:
            out = unsigned.with_name(unsigned.stem.replace(".unsigned", "") + "-signed.apk")
        signed = sign_apk(unsigned, out)
        print(json.dumps({"out": str(signed)}, indent=2))
        print("NEXT: install", signed)
        return 0

    if args.guide or not args.apk:
        print(
            """
Frida Gadget без root / без ПК
==============================
0) Один раз на Termux:
     pkg install openjdk-17 patchelf aapt aapt2 zip

1) AFK Arena (3 splits) — App Manager → Share / Save APK → .apks:
     ~/frida probe "/sdcard/AppManager/apks/AFK Arena_1.198.01.apks"
     ~/frida "/sdcard/AppManager/apks/AFK Arena_1.198.01.apks"
   (копіює з /sdcard у Termux home — інакше ZipFile часто дає BadZipFile)

   Якщо .apks битий: ZArchiver → Extract → папка зі splits →
     ~/frida "/sdcard/.../extracted_folder"

2) Інжект патчить ABI-split (libil2cpp) + resign УСІ splits одним ключем →
     /sdcard/Download/AFK-Arena-frida.apks
     /sdcard/Download/AFK-Arena-frida-splits/

3) Зняти стару AFK Arena, потім авто-знайти й відкрити установщик:
     ~/frida install
   (шукає newest *-frida.apks у Download; обери App Manager / SAI)

4) PCAPdroid MITM + Block QUIC → гра 30–60с → Stop

5) ~/scan mine  → app-global* / psp-api* мають стати OPEN

Що робить:
  • вшиває libfrida-gadget.so (Frida 16.7.19)
  • script-режим: ssl_unpin.js стартує сам (без adb)
  • Java TrustManager + native BoringSSL/curl/mbedtls hooks

НЕ плутай з 777.apk (Slots777) — це інша гра.
""".strip()
        )
        return 0 if args.guide or not args.apk else 2

    report = inject_apk(
        Path(args.apk),
        out_apk=Path(args.out) if args.out else None,
        script=Path(args.script) if args.script else None,
        version=args.version,
        method=args.method,
        unpin_mode=args.unpin_mode,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print()
    if report.get("mode") == "script+apks-bundle":
        print(report.get("install") or "")
        print("NEXT: SAI/App Manager install → PCAPdroid MITM → ~/scan mine")
    else:
        print("NEXT: install", report["out"], "→ PCAPdroid MITM → ~/scan mine")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
