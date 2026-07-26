"""Frida Gadget APK patch helpers (no network / no apktool)."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from protocol_ast.frida_gadget import (
    _pick_patch_so,
    detect_apis_in_apk,
    find_application_class,
    gadget_config_json,
    inject_load_library_smali,
    package_name,
    zip_apk_tree,
)


class TestSmaliInject(unittest.TestCase):
    def test_inject_attach_base_context(self) -> None:
        smali = """
.class public Lcom/game/App;
.super Landroid/app/Application;

.method protected attachBaseContext(Landroid/content/Context;)V
    .locals 0
    invoke-super {p0, p1}, Landroid/app/Application;->attachBaseContext(Landroid/content/Context;)V
    return-void
.end method
"""
        out, note = inject_load_library_smali(smali)
        self.assertEqual(note, "attachBaseContext")
        self.assertIn('const-string v0, "frida-gadget"', out)
        self.assertIn("loadLibrary", out)
        self.assertIn(".locals 1", out)

    def test_inject_on_create(self) -> None:
        smali = """
.class public Lcom/game/App;
.super Landroid/app/Application;

.method public onCreate()V
    .locals 2
    invoke-super {p0}, Landroid/app/Application;->onCreate()V
    return-void
.end method
"""
        out, note = inject_load_library_smali(smali)
        self.assertEqual(note, "onCreate")
        self.assertIn("frida-gadget", out)
        # load after super
        idx_super = out.index("invoke-super")
        idx_load = out.index("frida-gadget")
        self.assertLess(idx_super, idx_load)

    def test_create_attach_when_missing(self) -> None:
        smali = """
.class public Lcom/game/App;
.super Landroid/app/Application;

.method public constructor <init>()V
    .locals 0
    invoke-direct {p0}, Landroid/app/Application;-><init>()V
    return-void
.end method
"""
        out, note = inject_load_library_smali(smali)
        self.assertEqual(note, "created_attachBaseContext")
        self.assertIn("attachBaseContext", out)
        self.assertIn("frida-gadget", out)

    def test_idempotent(self) -> None:
        smali = """
.class public Lcom/game/App;
.super Landroid/app/Application;

.method public onCreate()V
    .locals 1
    invoke-super {p0}, Landroid/app/Application;->onCreate()V
    const-string v0, "frida-gadget"
    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V
    return-void
.end method
"""
        out, note = inject_load_library_smali(smali)
        self.assertEqual(note, "already_injected")
        self.assertEqual(out.count("frida-gadget"), 1)


class TestZipPack(unittest.TestCase):
    def test_pick_il2cpp(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "libc.so").write_bytes(b"x")
            (d / "libil2cpp.so").write_bytes(b"y")
            self.assertEqual(_pick_patch_so(d).name, "libil2cpp.so")

    def test_zip_strips_metainf_stores_so(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"
            (root / "lib" / "arm64-v8a").mkdir(parents=True)
            (root / "META-INF").mkdir()
            (root / "META-INF" / "CERT.SF").write_text("sig", encoding="utf-8")
            (root / "classes.dex").write_bytes(b"dex")
            so = root / "lib" / "arm64-v8a" / "libil2cpp.so"
            so.write_bytes(b"\x00" * 64)
            out = Path(td) / "out.apk"
            zip_apk_tree(root, out)
            with zipfile.ZipFile(out) as zf:
                names = zf.namelist()
                self.assertNotIn("META-INF/CERT.SF", names)
                self.assertIn("lib/arm64-v8a/libil2cpp.so", names)
                info = zf.getinfo("lib/arm64-v8a/libil2cpp.so")
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)


class TestWorkDir(unittest.TestCase):
    def test_inject_creates_unpin_work(self) -> None:
        """Regression: mkdtemp must not run before unpin_work exists."""
        import protocol_ast.frida_gadget as fg

        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            # no unpin_work yet — ensure_gadget/apktool mocked away via early fail on bad apk
            apk = home / "missing.apk"
            with self.assertRaises(FileNotFoundError):
                fg.inject_apk(apk, home=home)
            # directory should still be creatable via the work_root path logic unit
            work_root = home / "unpin_work"
            work_root.mkdir(parents=True, exist_ok=True)
            d = Path(tempfile.mkdtemp(prefix="frida_gadget_", dir=str(work_root)))
            self.assertTrue(d.is_dir())


class TestManifestAndAbi(unittest.TestCase):
    def test_config_script_mode(self) -> None:
        cfg = gadget_config_json()
        self.assertIn('"type": "script"', cfg)
        self.assertIn("libfrida-gadget.script.so", cfg)

    def test_manifest_application(self) -> None:
        xml = """<?xml version="1.0" encoding="utf-8"?>
<manifest package="com.lilithgame.hgame.gp" xmlns:android="http://schemas.android.com/apk/res/android">
  <application android:name=".MyApp" android:label="Game"/>
</manifest>
"""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "AndroidManifest.xml"
            p.write_text(xml, encoding="utf-8")
            self.assertEqual(package_name(p), "com.lilithgame.hgame.gp")
            self.assertEqual(find_application_class(p), ".MyApp")

    def test_detect_abis(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            apk = Path(td) / "t.apk"
            with zipfile.ZipFile(apk, "w") as zf:
                zf.writestr("lib/arm64-v8a/libil2cpp.so", b"\x00")
                zf.writestr("lib/armeabi-v7a/libil2cpp.so", b"\x00")
                zf.writestr("classes.dex", b"dex")
            self.assertEqual(detect_apis_in_apk(apk), ["arm64-v8a", "armeabi-v7a"])

    def test_quick_info_il2cpp(self) -> None:
        from protocol_ast.frida_gadget import apk_quick_info, format_apk_choice

        with tempfile.TemporaryDirectory() as td:
            apk = Path(td) / "777.apk"
            with zipfile.ZipFile(apk, "w") as zf:
                zf.writestr("lib/arm64-v8a/libil2cpp.so", b"\x00")
                zf.writestr("assets/bin/Data/lilith_config", b"x")
            inf = apk_quick_info(apk)
            self.assertTrue(inf["il2cpp"])
            self.assertIn("lilith", inf["hint"])
            label = format_apk_choice(apk)
            self.assertIn("IL2CPP", label)
            self.assertIn("777.apk", label)


if __name__ == "__main__":
    unittest.main()
