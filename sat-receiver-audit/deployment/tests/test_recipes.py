"""deployment/recipes: exact recipe schema, offline/no-download rules and the builder argv.

Nothing here builds a package; the build itself runs only in .github/workflows/sr-rx-packages.yml.
"""
import copy
import errno
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "recipes"))
import deploy  # noqa: E402
import build_recipe  # noqa: E402
import lab_build  # noqa: E402

LOCK = deploy.load(HERE / "sources.lock.json")
ALL_RECIPES = sorted(p.parent.name for p in (HERE / "recipes").glob("*/recipe.json"))


def recipe(name):
    return deploy.load(HERE / "recipes" / name / "recipe.json")


# PENDING_BUILDER recipes (satdump) keep their own schema until they move to this builder.
PENDING = [name for name in ALL_RECIPES if build_recipe.is_pending(recipe(name))]
RECIPES = [name for name in ALL_RECIPES if name not in PENDING]


class RecipeSchemaTests(unittest.TestCase):
    def test_every_recipe_validates_against_the_lock(self):
        self.assertLessEqual({"rtlsdr", "limesuiteng"}, set(RECIPES))
        for name in RECIPES:
            data = recipe(name)
            self.assertEqual(data["component"], name)
            component = build_recipe.validate_recipe(data, LOCK)
            self.assertIsNotNone(component["source_archive_sha256"])

    def test_pending_builder_recipes_are_refused_by_the_builder(self):
        self.assertEqual(PENDING, ["satdump"])
        for name in PENDING:
            data = recipe(name)
            self.assertEqual(data["id"], name)
            with self.assertRaisesRegex(build_recipe.RecipeError, "PENDING_BUILDER"):
                build_recipe.validate_recipe(data, LOCK)
            # once its status changes it must pass the exact build_recipe schema like the others
            changed = dict(data, status="BUILDER")
            self.assertFalse(build_recipe.is_pending(changed))
            with self.assertRaises(Exception):
                build_recipe.validate_recipe(changed, LOCK)

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
            "no lab_build_depends key": lambda d: d.pop("lab_build_depends"),
            "repeated lab package": lambda d: d.update(lab_build_depends=["librtlsdr-dev", "librtlsdr-dev"]),
            "lab package not a name": lambda d: d.update(lab_build_depends=["librtlsdr-dev (>= 2)"]),
            "builds against itself": lambda d: d.update(lab_build_depends=["librtlsdr2"]),
            # LA9310 DKMS modules: a source_subdir of the LimeSuiteNG archive, not honoured yet.
            "component with source_subdir": lambda d: d.update(component="la9310-limesdr"),
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

    def test_library_packages_carry_shlibs_and_the_ldconfig_trigger(self):
        extras = build_recipe.control_extras("liblimesuiteng", "25.1.0+git37cb183+lab1", [("liblimesuiteng", "0.3-1")])
        self.assertEqual(extras, {"shlibs": "liblimesuiteng 0.3-1 liblimesuiteng (>= 25.1.0+git37cb183+lab1)\n",
                                  "triggers": "activate-noawait ldconfig\n"})
        self.assertEqual(build_recipe.control_extras("librtlsdr-dev", "2.0.3-0+lab1", []), {})  # headers and the .so link only
        source = (HERE / "recipes/build_recipe.py").read_text(encoding="utf-8")
        self.assertNotIn('"--ignore-missing-info"', source)  # a library without shlibs/symbols info fails the build


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
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-builder-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_chroot_comes_from_the_locked_snapshot_and_trusts_only_the_pinned_key(self):
        data = recipe("limesuiteng")
        keyring = "/w/limesuiteng/keyring/archive-pinned.gpg"
        argv = lab_build.mmdebstrap_argv(data, LOCK, Path("/c"), keyring)
        snapshot = LOCK["apt_snapshot"]
        self.assertEqual(argv[:5], ["mmdebstrap", "--mode=root", "--format=directory", "--variant=buildd", "--architectures=arm64"])
        self.assertIn("--keyring=" + keyring, argv)  # not the runner's whole ubuntu-archive-keyring
        self.assertNotIn("--keyring=" + snapshot["keyring"], argv)
        self.assertIn("--skip=cleanup/apt/lists", argv)  # installed_releases() compares the kept InRelease files
        hook = next(a for a in argv if a.startswith("--setup-hook="))
        self.assertIn('cp %s "$1"%s' % (keyring, keyring), hook)  # same signed-by path inside and outside the chroot
        include = next(a for a in argv if a.startswith("--include=")).split("=", 1)[1].split(",")
        self.assertEqual(set(include), set(lab_build.BASE_PACKAGES) | set(data["build_depends"]))
        lines = [a for a in argv if a.startswith("deb ")]
        self.assertEqual(len(lines), len(snapshot["suites"]))
        for line in lines:
            self.assertIn("%s/%s " % (snapshot["archive"], snapshot["timestamp"]), line)
            self.assertIn("signed-by=" + keyring, line)
        offline = lab_build.offline_argv(Path("/c"), ["python3", "x"])
        self.assertEqual(offline[:5], ["unshare", "--net", "--mount", "--pid", "--fork"])
        self.assertIn("chroot --userspec=1000:1000", offline[8])
        self.assertIn("env -i", offline[8])
        self.assertEqual(offline[-2:], ["python3", "x"])
        root = lab_build.offline_root_argv(Path("/c"), ["dpkg", "-i", "/lab-debs/a.deb"])
        self.assertEqual(root[:6], ["unshare", "--net", "--fork", "--", "chroot", str(Path("/c"))])
        self.assertEqual(root[6:8], ["/usr/bin/env", "-i"])

    def test_pinned_keyring_listing_and_chroot_inrelease_binding(self):
        colons = ("pub:-:4096:1:871920D1991BC93C:1537196506:::-:::scSC::::::23::0:\nfpr:::::::::F6ECB3762474EDA9D21B7022871920D1991BC93C:\n"
                  "uid:-::::1537196506::BE4B:::Ubuntu Archive Automatic Signing Key (2018):::::::::0:\n"
                  "sub:-:4096:1:AAAAAAAAAAAAAAAA:1537196506::::::s::::::23:\nfpr:::::::::" + "A" * 40 + ":\n")
        self.assertEqual(lab_build.primary_fingerprints(colons), ["F6ECB3762474EDA9D21B7022871920D1991BC93C"])
        self.assertEqual(lab_build.primary_fingerprints(colons + colons.replace("F6EC", "0000")),
                         sorted(["F6ECB3762474EDA9D21B7022871920D1991BC93C", "0000B3762474EDA9D21B7022871920D1991BC93C"]))
        lists = self.root / "var/lib/apt/lists"
        lists.mkdir(parents=True)
        snapshot = copy.deepcopy(LOCK)
        for index, suite in enumerate(snapshot["apt_snapshot"]["suites"]):
            data = ("signed InRelease of " + suite).encode()
            (lists / ("snapshot.ubuntu.com_ubuntu_20261020T000000Z_dists_%s_InRelease" % suite)).write_bytes(data)
            snapshot["apt_snapshot"]["releases"][index] = {"suite": suite, "inrelease_sha256": deploy.sha(lists / ("snapshot.ubuntu.com_ubuntu_20261020T000000Z_dists_%s_InRelease" % suite)), "size": len(data)}
        self.assertEqual([r["suite"] for r in lab_build.installed_releases(self.root, snapshot)], snapshot["apt_snapshot"]["suites"])
        (lists / "snapshot.ubuntu.com_ubuntu_20261020T000000Z_dists_noble-security_InRelease").write_bytes(b"another publication")
        with self.assertRaisesRegex(build_recipe.RecipeError, "another InRelease than the lock: noble-security"):
            lab_build.installed_releases(self.root, snapshot)
        (lists / "snapshot.ubuntu.com_ubuntu_20261020T000000Z_dists_noble-security_InRelease").unlink()
        with self.assertRaisesRegex(build_recipe.RecipeError, "lack exactly one InRelease for noble-security"):
            lab_build.installed_releases(self.root, snapshot)

    def test_lab_build_depends_come_from_earlier_records_with_their_hashes(self):
        out = self.root / "debs"
        (out / "rtlsdr").mkdir(parents=True)
        deb = out / "rtlsdr/librtlsdr-dev_2.0.3-0+lab1_arm64.deb"
        deb.write_bytes(b"synthetic dev package")
        record = {"component": "rtlsdr", "packages": [{"package": "librtlsdr-dev", "version": "2.0.3-0+lab1", "filename": deb.name,
                                                        "sha256": deploy.sha(deb), "size": deb.stat().st_size}]}
        (out / "rtlsdr/rtlsdr.build-record.json").write_text(json.dumps(record), encoding="utf-8")
        consumer = dict(recipe("limesuiteng"), lab_build_depends=["librtlsdr-dev"])
        found = lab_build.lab_packages(consumer, out)
        self.assertEqual([(f["package"], f["component"], f["sha256"], f["path"]) for f in found], [("librtlsdr-dev", "rtlsdr", deploy.sha(deb), deb)])
        self.assertEqual(lab_build.lab_packages(recipe("limesuiteng"), out), [])
        with self.assertRaisesRegex(build_recipe.RecipeError, "not built earlier into --out: libairspyhf-dev"):
            lab_build.lab_packages(dict(consumer, lab_build_depends=["librtlsdr-dev", "libairspyhf-dev"]), out)
        deb.write_bytes(b"synthetic dev package, changed after the build")
        with self.assertRaisesRegex(build_recipe.RecipeError, "differs from its build record: librtlsdr-dev"):
            lab_build.lab_packages(consumer, out)

    def run_builds(self, name, outputs, repeat=True):
        chroot, out = self.root / name / "chroot", self.root / name / "debs/rtlsdr"
        (chroot / "out").mkdir(parents=True)
        (chroot / "work/rtlsdr").mkdir(parents=True)
        calls = []

        def build_once(component, root, archive, jobs):
            target = root / "out" / component
            target.mkdir()
            (target / "librtlsdr2_2.0.3-0+lab1_arm64.deb").write_bytes(outputs[len(calls)])
            (root / "work" / component).mkdir(exist_ok=True)
            calls.append(component)
            return 0
        with patch.object(lab_build, "build_once", build_once), patch.object(lab_build.os, "chown", lambda *a, **k: None, create=True):
            try:
                return lab_build.run_builds("rtlsdr", chroot, "rtl.tar.gz", 2, repeat, out, {"lab_build_depends": []})
            finally:
                self.written = json.loads((out / "rtlsdr.reproducibility.json").read_text(encoding="utf-8")) if out.is_dir() else None

    def test_repeat_with_differing_debs_fails_after_writing_both_sets(self):
        result = self.run_builds("same", [b"same bytes", b"same bytes"])
        self.assertTrue(result["reproducible"])
        self.assertEqual(result["first_debs"], result["debs"])
        self.assertIsNone(self.run_builds("once", [b"one build"], repeat=False)["reproducible"])
        with self.assertRaisesRegex(build_recipe.RecipeError, "the two builds differ: rtlsdr"):
            self.run_builds("differ", [b"first bytes", b"second bytes"])
        self.assertIs(self.written["reproducible"], False)  # written before the failure, for the artifact
        self.assertNotEqual(self.written["first_debs"], self.written["debs"])

    def test_builder_needs_root_and_checks_its_network_namespace(self):
        if hasattr(lab_build.os, "geteuid") and lab_build.os.geteuid() != 0:
            with self.assertRaisesRegex(build_recipe.RecipeError, "needs root"):
                lab_build.lab_build("rtlsdr", "/nonexistent", "/nonexistent", "/nonexistent")
            with self.assertRaisesRegex(build_recipe.RecipeError, "needs root"):
                lab_build.consumer_check("/nonexistent", "/nonexistent")
        self.assertNotIn("ignore-missing-info", lab_build.CONSUMER_SCRIPT)
        self.assertIn("ldconfig -p", lab_build.CONSUMER_SCRIPT)  # the lab package's ldconfig trigger must have run
        net = self.root / "net"
        (net / "lo").mkdir(parents=True)

        def unreachable(code):
            class Probe:
                def __init__(self, *args):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

                def settimeout(self, value):
                    pass

                def connect(self, address):
                    if code is not None:
                        raise OSError(code, os.strerror(code))
            return Probe
        with patch.object(build_recipe.socket, "socket", unreachable(errno.ENETUNREACH)):
            self.assertIn("interfaces lo", build_recipe.no_network(net))
            (net / "eth0").mkdir()
            with self.assertRaisesRegex(build_recipe.RecipeError, "besides loopback: eth0,lo"):
                build_recipe.no_network(net)
            (net / "eth0").rmdir()
            with self.assertRaisesRegex(build_recipe.RecipeError, "sysfs not mounted"):
                build_recipe.no_network(self.root / "no-sysfs")
        with patch.object(build_recipe.socket, "socket", unreachable(None)), \
                self.assertRaisesRegex(build_recipe.RecipeError, "outside connection succeeded"):
            build_recipe.no_network(net)
        with patch.object(build_recipe.socket, "socket", unreachable(errno.EPERM)), \
                self.assertRaisesRegex(build_recipe.RecipeError, "unexpected result"):
            build_recipe.no_network(net)

    def test_source_subdir_components_are_refused_until_honoured(self):
        data = dict(recipe("limesuiteng"), component="la9310-uart", source={"patch": None})
        with self.assertRaisesRegex(build_recipe.RecipeError, "source_subdir"):
            build_recipe.validate_recipe(data, LOCK)

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
