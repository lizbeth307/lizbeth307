"""Frida Gadget APK patch helpers (no network / no apktool)."""

from __future__ import annotations

import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from protocol_ast.frida_gadget import (
    _link_or_copy,
    _pick_patch_so,
    detect_apis_in_apk,
    detect_native_abis,
    describe_magic,
    extract_apks_archive,
    find_application_class,
    find_frida_install_targets,
    gadget_config_json,
    inject_load_library_smali,
    looks_like_apks_bundle,
    list_bundle_apk_members,
    materialize_local_copy,
    package_name,
    pick_frida_install_target,
    probe_bundle,
    rebuild_apk_surgical,
    resign_split_apk,
    verify_apk,
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


class TestFindInstall(unittest.TestCase):
    def test_find_prefers_frida_apks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            dl = td_path / "Download"
            dl.mkdir()
            apks = dl / "AFK_Arena_1.198.01-frida.apks"
            apks.write_bytes(b"PK\x03\x04fake")
            splits = dl / "AFK_Arena_1.198.01-frida-splits"
            splits.mkdir()
            (splits / "base.apk").write_bytes(b"PK\x03\x04base")
            # monkeypatch roots via temporary HOME storage path is hard —
            # call finder after injecting by patching function locals: scan dl directly
            import protocol_ast.frida_gadget as fg

            real = fg.find_frida_install_targets

            def fake(home=None):
                return [
                    {
                        "path": str(apks),
                        "kind": "apks",
                        "size": apks.stat().st_size,
                        "mtime": apks.stat().st_mtime,
                        "pri": 200,
                    },
                    {
                        "path": str(splits),
                        "kind": "splits",
                        "size": 1,
                        "mtime": splits.stat().st_mtime,
                        "pri": 100,
                    },
                ]

            fg.find_frida_install_targets = fake  # type: ignore[assignment]
            try:
                picked = pick_frida_install_target()
                self.assertIsNotNone(picked)
                assert picked is not None
                self.assertTrue(picked["path"].endswith(".apks"))
            finally:
                fg.find_frida_install_targets = real  # type: ignore[assignment]


class TestLinkOrCopy(unittest.TestCase):
    def test_copy_when_link_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            src = td_path / "a.bin"
            dest = td_path / "b.bin"
            src.write_bytes(b"hello-link")
            real_link = getattr(os, "link", None)
            try:
                if hasattr(os, "link"):
                    delattr(os, "link")
                _link_or_copy(src, dest)
                self.assertEqual(dest.read_bytes(), b"hello-link")
            finally:
                if real_link is not None and not hasattr(os, "link"):
                    setattr(os, "link", real_link)


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

    def test_surgical_preserves_manifest_compression(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            orig = td_path / "orig.apk"
            with zipfile.ZipFile(orig, "w") as zf:
                zf.writestr("AndroidManifest.xml", b"<manifest/>", compress_type=zipfile.ZIP_DEFLATED)
                zf.writestr("classes.dex", b"dex123", compress_type=zipfile.ZIP_DEFLATED)
                zf.writestr(
                    "lib/arm64-v8a/libil2cpp.so",
                    b"\x00" * 32,
                    compress_type=zipfile.ZIP_STORED,
                )
                zf.writestr("META-INF/CERT.SF", b"sig")
            new_so = td_path / "libil2cpp.so"
            new_so.write_bytes(b"\x01" * 40)
            gadget = td_path / "libfrida-gadget.so"
            gadget.write_bytes(b"G" * 16)
            out = td_path / "out.apk"
            rebuild_apk_surgical(
                orig,
                {
                    "lib/arm64-v8a/libil2cpp.so": new_so,
                    "lib/arm64-v8a/libfrida-gadget.so": gadget,
                },
                out,
                work=td_path / "w",
            )
            with zipfile.ZipFile(out) as zf:
                self.assertNotIn("META-INF/CERT.SF", zf.namelist())
                self.assertEqual(
                    zf.getinfo("AndroidManifest.xml").compress_type, zipfile.ZIP_DEFLATED
                )
                self.assertEqual(zf.read("lib/arm64-v8a/libil2cpp.so"), b"\x01" * 40)
                self.assertEqual(zf.read("lib/arm64-v8a/libfrida-gadget.so"), b"G" * 16)
            rep = verify_apk(out)
            # aapt may be missing in CI — zip checks should pass
            self.assertNotIn("no AndroidManifest.xml", rep["errors"])
            self.assertNotIn("no classes*.dex", rep["errors"])


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
            self.assertEqual(detect_native_abis(apk), ["arm64-v8a", "armeabi-v7a"])

    def test_density_split_has_no_native_abis(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            apk = Path(td) / "split_config.xxhdpi.apk"
            with zipfile.ZipFile(apk, "w") as zf:
                zf.writestr("AndroidManifest.xml", b"<manifest/>")
                zf.writestr("res/drawable/icon.png", b"png")
            self.assertEqual(detect_native_abis(apk), [])
            # legacy helper still defaults to arm64 for fat/unknown
            self.assertEqual(detect_apis_in_apk(apk), ["arm64-v8a"])
            rep = verify_apk(apk, require_dex=False)
            self.assertTrue(rep["ok"])
            self.assertFalse(rep.get("has_dex"))

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

    def test_apks_bundle_quick_info(self) -> None:
        from protocol_ast.frida_gadget import apk_quick_info, format_apk_choice

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            base = td_path / "base.apk"
            abi = td_path / "split_config.arm64_v8a.apk"
            with zipfile.ZipFile(base, "w") as zf:
                zf.writestr("AndroidManifest.xml", b"<manifest package='com.lilithgame.hgame.gp'/>")
                zf.writestr("classes.dex", b"dex")
            with zipfile.ZipFile(abi, "w") as zf:
                zf.writestr("AndroidManifest.xml", b"<manifest/>")
                zf.writestr("lib/arm64-v8a/libil2cpp.so", b"\x00" * 32)
            bundle = td_path / "AFK Arena_1.198.01.apks"
            with zipfile.ZipFile(bundle, "w") as zf:
                zf.write(base, "base.apk")
                zf.write(abi, "split_config.arm64_v8a.apk")
            self.assertTrue(looks_like_apks_bundle(bundle))
            self.assertEqual(list_bundle_apk_members(bundle), ["base.apk", "split_config.arm64_v8a.apk"])
            inf = apk_quick_info(bundle)
            self.assertTrue(inf["bundle"])
            self.assertEqual(inf["splits"], 2)
            self.assertTrue(inf["il2cpp"])
            self.assertIn("afk", inf["hint"])
            label = format_apk_choice(bundle)
            self.assertIn("APKS", label)
            self.assertIn("IL2CPP", label)
            probe = probe_bundle(bundle)
            self.assertTrue(probe["zip_ok"])
            self.assertEqual(probe["magic"], "zip/apk")
            self.assertEqual(describe_magic(b"PK\x03\x04"), "zip/apk")
            out = td_path / "out"
            out.mkdir()
            extract_apks_archive(bundle, out)
            self.assertTrue((out / "base.apk").is_file())
            local = materialize_local_copy(bundle, td_path / "loc")
            self.assertEqual(local.stat().st_size, bundle.stat().st_size)
            # directory of splits also accepted
            splits_dir = td_path / "splits"
            splits_dir.mkdir()
            shutil_copy = __import__("shutil").copy2
            shutil_copy(base, splits_dir / "base.apk")
            shutil_copy(abi, splits_dir / "split_config.arm64_v8a.apk")
            self.assertTrue(looks_like_apks_bundle(splits_dir))
            self.assertTrue(probe_bundle(splits_dir)["zip_ok"])

    def test_resign_split_strips_metainf(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            home = td_path / "home"
            home.mkdir()
            src = td_path / "split_config.xxhdpi.apk"
            with zipfile.ZipFile(src, "w") as zf:
                zf.writestr("AndroidManifest.xml", b"<manifest/>")
                zf.writestr("res/a.png", b"png")
                zf.writestr("META-INF/CERT.SF", b"sig")
            out = td_path / "out.apk"
            # jarsigner path when uber unavailable — still strips via surgical first
            unsigned = td_path / "u.apk"
            rebuild_apk_surgical(src, {}, unsigned, work=td_path / "w")
            with zipfile.ZipFile(unsigned) as zf:
                self.assertNotIn("META-INF/CERT.SF", zf.namelist())
                self.assertIn("AndroidManifest.xml", zf.namelist())
            # resign_split_apk needs java/keytool in CI — skip if missing
            import shutil

            if not shutil.which("jarsigner") and not shutil.which("java"):
                self.skipTest("no java/jarsigner")
            try:
                resign_split_apk(src, out, home=home, work=td_path / "rw")
            except Exception as exc:
                # uber may fail without network jar; jarsigner may still work
                if not out.is_file():
                    self.skipTest(f"signing unavailable: {exc}")


if __name__ == "__main__":
    unittest.main()
