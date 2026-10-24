"""deployment/recipes: exact recipe schema, offline/no-download rules and the builder argv.

Nothing here builds a package; the build itself runs only in .github/workflows/sr-rx-packages.yml.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "recipes"))
import deploy  # noqa: E402
import build_recipe  # noqa: E402
import lab_build  # noqa: E402

LOCK = deploy.load(HERE / "sources.lock.json")
RECIPES = sorted(p.parent.name for p in (HERE / "recipes").glob("*/recipe.json"))


def recipe(name):
    return deploy.load(HERE / "recipes" / name / "recipe.json")


class RecipeSchemaTests(unittest.TestCase):
    def test_every_recipe_validates_against_the_lock(self):
        self.assertLessEqual({"rtlsdr", "limesuiteng"}, set(RECIPES))
        for name in RECIPES:
            data = recipe(name)
            self.assertEqual(data["component"], name)
            component = build_recipe.validate_recipe(data, LOCK)
            self.assertIsNotNone(component["source_archive_sha256"])

    def test_existing_vendor_recipes_keep_their_reviewed_flags(self):
        script = (HERE / "build-vendor.sh").read_text(encoding="utf-8")
        for name in ("rtlsdr", "limesuiteng"):
            data = recipe(name)
            self.assertEqual(data["source"]["patch"], "deployment/patches/%s-rx-only.patch" % name)
            for key, value in data["cmake"]["options"].items():
                if "-D%s=" % key in script:
                    self.assertIn("-D%s=%s" % (key, value), script, key)  # same value as the reviewed build-vendor.sh
        self.assertEqual(recipe("limesuiteng")["cmake"]["options"]["BUILD_PLUGINS_AMARISOFT"], "OFF")
        self.assertEqual(recipe("limesuiteng")["cmake"]["options"]["BUILD_PLUGINS_GNURADIO"], "OFF")
        self.assertEqual(recipe("rtlsdr")["build"], [["cmake", "--build", "{build}", "--target", "rtlsdr", "--parallel", "{jobs}"]])

    def test_downloads_unknown_programs_and_unsafe_fields_are_refused(self):
        def mutated(change):
            data = copy.deepcopy(recipe("rtlsdr"))
            change(data)
            return data
        cases = {
            "extra key": lambda d: d.update(extra=1),
            "curl step": lambda d: d["build"].append(["curl", "-O", "x"]),
            "git step": lambda d: d["build"].append(["git", "clone", "x"]),
            "URL argument": lambda d: d["build"][0].append("https://example.invalid/x.tar.gz"),
            "downloads enabled": lambda d: d["cmake"]["variables"].update(FETCHCONTENT_FULLY_DISCONNECTED="OFF"),
            "configure shape": lambda d: d["cmake"].update(configure=["cmake", "{src}"]),
            "option value": lambda d: d["cmake"]["options"].update(ENABLE_ZEROCOPY="0"),
            "option also a variable": lambda d: d["cmake"]["variables"].update(ENABLE_ZEROCOPY="OFF"),
            "unreviewed patch": lambda d: d["source"].update(patch="deployment/patches/other.patch"),
            "TX-capable package name": lambda d: d["packages"][0].update(name="wsjtx"),
            "Lime CLI package": lambda d: d["packages"][0].update(name="limesuiteng-cli"),
            "duplicate package": lambda d: d["packages"].append(copy.deepcopy(d["packages"][0])),
            "absolute install target": lambda d: d["install"]["copy"][0].update(to="/usr/lib"),
            "copy from outside the build": lambda d: d["install"]["copy"][0].update(**{"from": "/etc/passwd"}),
            "unknown check": lambda d: d["checks"].append({"kind": "trust_me"}),
            "debian component": lambda d: d.update(component="gpsd"),
            "unknown placeholder": lambda d: d["build"][0].append("{home}"),
            "bad build depends": lambda d: d.update(build_depends=["libusb-1.0-0-dev; curl"]),
        }
        for label, change in cases.items():
            with self.subTest(label), self.assertRaises(ValueError):
                build_recipe.validate_recipe(mutated(change), LOCK)

    def test_package_manifest_is_the_open_verify_build_schema(self):
        with tempfile.TemporaryDirectory(prefix="srrx-recipe-test-") as temporary:
            root = Path(temporary)
            (root / "usr/lib").mkdir(parents=True)
            (root / "usr/lib/librx.so.2").write_bytes(b"synthetic")
            manifest = build_recipe.package_manifest(root)
            self.assertEqual(set(manifest), {"schema_version", "status", "files", "allowed_modules", "source_audit", "tx_negative_tests"})
            self.assertEqual((manifest["status"], manifest["allowed_modules"]), ("OPEN", ["usr/lib/librx.so.2"]))
            with self.assertRaisesRegex(deploy.DeploymentError, "OPEN/unreviewed"):
                deploy.verify_build(root, manifest)  # CI output never passes the release verifier on its own


class OptionCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-options-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "src/sub").mkdir(parents=True)
        (self.root / "build").mkdir()
        (self.root / "src/CMakeLists.txt").write_text('option(A "a" ON)\n# option(COMMENTED "x" ON)\ncmake_dependent_option(\n    B "b" ON "A" OFF)\n', encoding="utf-8")
        (self.root / "src/sub/x.cmake").write_text("option(C TRUE)\n", encoding="utf-8")

    def cache(self, text):
        (self.root / "build/CMakeCache.txt").write_text(text, encoding="utf-8")

    def test_declared_options_span_lines_and_skip_comments(self):
        self.assertEqual(build_recipe.declared_options(self.root / "src"), {"A", "B", "C"})

    def test_every_evaluated_option_is_set_by_the_recipe(self):
        self.cache("A:BOOL=ON\nB:BOOL=OFF\nCMAKE_VERBOSE_MAKEFILE:BOOL=FALSE\nC:INTERNAL=ON\n")
        result = build_recipe.check_options(self.root / "src", self.root / "build", {"A": "ON", "B": "OFF", "C": "ON"})
        self.assertEqual(result["evaluated"], ["A", "B"])
        with self.assertRaisesRegex(build_recipe.RecipeError, "unreviewed default: B"):
            build_recipe.check_options(self.root / "src", self.root / "build", {"A": "ON"})
        with self.assertRaisesRegex(build_recipe.RecipeError, "differs from the recipe: A"):
            build_recipe.check_options(self.root / "src", self.root / "build", {"A": "OFF", "B": "OFF"})
        with self.assertRaisesRegex(build_recipe.RecipeError, "not declared upstream: Z"):
            build_recipe.check_options(self.root / "src", self.root / "build", {"A": "ON", "B": "OFF", "Z": "ON"})

    def test_staged_files_belong_to_exactly_one_package(self):
        data = {"packages": [{"name": "p", "files": ["usr/lib/*"]}, {"name": "q", "files": ["usr/include/*"]}],
                "drop": [{"glob": "usr/share/doc/*", "reason": "docs"}]}
        stage = self.root / "stage"
        for relative in ("usr/lib/a.so.1", "usr/include/a.h", "usr/share/doc/README"):
            (stage / relative).parent.mkdir(parents=True, exist_ok=True)
            (stage / relative).write_text("x", encoding="utf-8")
        self.assertEqual(build_recipe.assign(data, stage), {"p": ["usr/lib/a.so.1"], "q": ["usr/include/a.h"]})
        (stage / "usr/bin").mkdir(parents=True)
        (stage / "usr/bin/tool").write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(build_recipe.RecipeError, "unclaimed staged file: usr/bin/tool"):
            build_recipe.assign(data, stage)
        (stage / "usr/bin/tool").unlink()
        data["packages"][1]["files"].append("usr/lib/a.so.1")
        with self.assertRaisesRegex(build_recipe.RecipeError, "doubly claimed"):
            build_recipe.assign(data, stage)


class BuilderArgvTests(unittest.TestCase):
    def test_chroot_comes_from_the_locked_snapshot_and_builds_offline(self):
        data = recipe("limesuiteng")
        argv = lab_build.mmdebstrap_argv(data, LOCK, Path("/c"))
        snapshot = LOCK["apt_snapshot"]
        self.assertEqual(argv[:5], ["mmdebstrap", "--mode=root", "--format=directory", "--variant=buildd", "--architectures=arm64"])
        self.assertIn("--keyring=" + snapshot["keyring"], argv)
        include = next(a for a in argv if a.startswith("--include=")).split("=", 1)[1].split(",")
        self.assertEqual(set(include), set(lab_build.BASE_PACKAGES) | set(data["build_depends"]))
        lines = [a for a in argv if a.startswith("deb ")]
        self.assertEqual(len(lines), len(snapshot["suites"]))
        for line in lines:
            self.assertIn("%s/%s " % (snapshot["archive"], snapshot["timestamp"]), line)
            self.assertIn("signed-by=" + snapshot["keyring"], line)
        offline = lab_build.offline_argv(Path("/c"), ["python3", "x"])
        self.assertEqual(offline[:5], ["unshare", "--net", "--mount", "--pid", "--fork"])
        self.assertIn("chroot --userspec=1000:1000", offline[8])
        self.assertIn("env -i", offline[8])
        self.assertEqual(offline[-2:], ["python3", "x"])

    def test_builder_needs_root_and_proves_no_network(self):
        if hasattr(lab_build.os, "geteuid") and lab_build.os.geteuid() != 0:
            with self.assertRaisesRegex(build_recipe.RecipeError, "needs root"):
                lab_build.lab_build("rtlsdr", "/nonexistent", "/nonexistent", "/nonexistent")
        source = (HERE / "recipes/build_recipe.py").read_text(encoding="utf-8")
        self.assertIn("def no_network", source)
        self.assertIn("network = no_network()", source)

    def test_recipe_tree_is_bound_by_the_linux_lab_finalizer(self):
        spec = importlib.util.spec_from_file_location("srrx_finalize_for_recipes", HERE.parent / "tools/finalize_linux_lab.py")
        finalize = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(finalize)
        for name in ("deployment/recipes/rtlsdr/recipe.json", "deployment/recipes/satdump/debian/rules", "deployment/recipes/README.md",
                     "deployment/repo/lab.pref", "deployment/repo/srrx-lab.sources", "deployment/fetch_sources.py",
                     "software/labrx-native/src/main.cpp", "software/labrx-native/CMakeLists.txt"):
            self.assertTrue(finalize.bound(name), name)


if __name__ == "__main__":
    unittest.main()
