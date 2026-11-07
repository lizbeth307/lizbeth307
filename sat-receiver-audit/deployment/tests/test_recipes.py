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


# PENDING_BUILDER recipes keep their own schema until they move to this builder (none left since
# W2 SW-SATDUMP moved satdump to schema 2; the refusal stays tested on a synthetic one).
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
        self.assertEqual(PENDING, [])
        synthetic = {"schema_version": 1, "kind": build_recipe.PENDING_KIND, "id": "srrx-pending", "status": build_recipe.PENDING_STATUS}
        for name, data in [(n, recipe(n)) for n in PENDING] + [("srrx-pending", synthetic)]:
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

    def test_package_manifest_is_the_verify_build_walk_and_refuses_what_it_refuses(self):
        with tempfile.TemporaryDirectory(prefix="srrx-recipe-test-") as temporary:
            root = Path(temporary)
            (root / "usr/lib").mkdir(parents=True)
            (root / "usr/lib/librx.so.2.0.3").write_bytes(b"synthetic")
            try:
                os.symlink("librx.so.2.0.3", root / "usr/lib/librx.so.2")
            except OSError as exc:  # unprivileged Windows host only; Linux CI always creates links
                self.skipTest("symlinks unavailable: " + str(exc))
            files, modules = deploy.build_inventory(root)
            manifest = build_recipe.package_manifest(root)
            self.assertEqual((manifest["files"], manifest["allowed_modules"]), (files, sorted(modules)))
            self.assertIsNone(build_recipe.inventory_refusal(root))
            # A -dev package's .so link into the runtime package: verify_build's walk refuses the tree,
            # so the CI manifest carries no file list instead of silently dropping the link.
            os.symlink("librx.so.2", root / "usr/lib/librx.so")
            (root / "usr/lib/librx.so.2").unlink()
            (root / "usr/lib/librx.so.2.0.3").unlink()
            with self.assertRaises(OSError):
                deploy.build_inventory(root)
            refused = build_recipe.package_manifest(root)
            self.assertEqual((refused["status"], refused["files"], refused["allowed_modules"]), ("OPEN", {}, []))
            self.assertIn("dangling link usr/lib/librx.so", build_recipe.inventory_refusal(root))
            reviewed = dict(refused, status="REVIEWED")
            with self.assertRaisesRegex(deploy.DeploymentError, "OPEN/unreviewed"):
                deploy.verify_build(root, reviewed)  # an empty file list never passes, whatever the status
        with tempfile.TemporaryDirectory(prefix="srrx-recipe-test-") as temporary:
            root = Path(temporary)
            (root / "usr/lib").mkdir(parents=True)
            (root / "usr/lib/liblimesuiteng.so.25").write_bytes(b"synthetic")
            self.assertIn("Lime runtime library", build_recipe.inventory_refusal(root))
            self.assertEqual(build_recipe.package_manifest(root)["files"], {})

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


# --- schema_version 2 (W2 SW-BUILDER): listed patches, source member, make/autotools, hooks, recipe
# files and forbid_needed. Synthetic deployment trees in temporary directories; nothing is fetched.
import gzip  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tarfile  # noqa: E402

FIXTURE = "srrx-fixture"
HELLO = '#include <stdio.h>\nint main(void) { puts("srrx fixture"); return 0; }\n'
SOURCE = {"src/a.txt": "alpha\n", "src/b.txt": "beta\n", "src/c.txt": "gamma\n", "hello.c": HELLO}
# Three listed patches, the second with two targets: 4 changed files in all.
PATCHES = [("alpha", [("src/a.txt", "alpha\n", "alpha patched\n")]),
           ("beta-gamma", [("src/b.txt", "beta\n", "beta patched\n"), ("src/c.txt", "gamma\n", "gamma patched\n")]),
           ("greeting", [("hello.c", HELLO, HELLO.replace("srrx fixture", "srrx fixture patched"))])]
MEMBER = "superbuild-1.0/src/inner.tgz"
# Stand-in for an autoconf-generated configure: the ac_user_opts list the builder reads, and a Makefile.
CONFIGURE = """#!/bin/sh
# Synthetic stand-in for a GNU Autoconf configure script (builder test fixture only).
ac_user_opts='
enable_option_checking
enable_greeting
with_colour
'
prefix=/usr/local
for arg in "$@"; do
  case $arg in
    --prefix=*) prefix=${arg#--prefix=} ;;
    --enable-greeting|--disable-greeting|--with-colour|--with-colour=*|--without-colour) ;;
    *) echo "configure: unrecognized option $arg" >&2; exit 1 ;;
  esac
done
cat > Makefile <<EOF
PREFIX = $prefix
all: hello
hello: hello.c
\tcc -O2 -o hello hello.c
install: hello
\tmkdir -p \\$(DESTDIR)\\$(PREFIX)/bin \\$(DESTDIR)\\$(PREFIX)/share/srrx-fixture
\tcp hello \\$(DESTDIR)\\$(PREFIX)/bin/srrx-fixture-hello
\tcp src/a.txt \\$(DESTDIR)\\$(PREFIX)/share/srrx-fixture/a.txt
\tcp src/b.txt \\$(DESTDIR)\\$(PREFIX)/share/srrx-fixture/dropped-by-hook.txt
EOF
"""
CHECK_RECIPE = '''#!/usr/bin/env python3
"""Synthetic recipe hook of the builder tests (stdlib only, no network)."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

parser = argparse.ArgumentParser()
commands = parser.add_subparsers(dest="command", required=True)
commands.add_parser("verify-source").add_argument("--source", type=Path, required=True)
stage = commands.add_parser("package")
stage.add_argument("--root", type=Path, required=True)
stage.add_argument("--manifest", type=Path)
args = parser.parse_args()
findings = []
if args.command == "verify-source":
    if (args.source / "src/a.txt").read_text(encoding="utf-8") != "alpha\\n":
        findings.append("upstream_file:src/a.txt")
else:
    (args.root / "usr/share/srrx-fixture/dropped-by-hook.txt").unlink()
    files = {p.relative_to(args.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(args.root.rglob("*")) if p.is_file()}
    with args.manifest.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({"files": files, "record_digests": {"hello_sha256": files["usr/bin/srrx-fixture-hello"]}}) + "\\n")
print(json.dumps({"command": args.command, "findings": findings, "ok": not findings}))
sys.exit(0 if not findings else 2)
'''
SOURCE_CHECK = ["python3", "-I", "{recipe}/check_recipe.py", "verify-source", "--source", "{src}"]
PACKAGE_HOOK = ["python3", "-I", "{recipe}/check_recipe.py", "package", "--root", "{destdir}", "--manifest", "{hook_out}"]


def blob(text):
    data = text.encode()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def diff(path, old, new):
    a, b = old.splitlines(True), new.splitlines(True)
    return ("diff --git a/%s b/%s\n--- a/%s\n+++ b/%s\n@@ -1,%d +1,%d @@\n" % (path, path, path, path, len(a), len(b))
            + "".join("-" + line for line in a) + "".join("+" + line for line in b))


def tar_gz(entries, mtime=1700000000):
    """gzip tar bytes of {name: (bytes, mode)} with one fixed mtime."""
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as compressed, tarfile.open(fileobj=compressed, mode="w") as archive:
        for name, (data, mode) in sorted(entries.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(data), mode, mtime
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def fixture_tree(root):
    """A deployment/ stand-in: recipes/srrx-fixture/ with check_recipe.py, three listed patches and
    files/, plus sources.lock.json (the real lock and the synthetic component). Returns the listed
    patch entries, the outer archive path and its lock."""
    directory = root / "recipes" / FIXTURE
    (directory / "patches").mkdir(parents=True)
    (directory / "files").mkdir()
    (directory / "check_recipe.py").write_text(CHECK_RECIPE, encoding="utf-8", newline="\n")
    (directory / "files/srrx-fixture.conf").write_text("# synthetic recipe file\n", encoding="utf-8", newline="\n")
    entries = []
    for index, (name, changes) in enumerate(PATCHES, 1):
        file = "patches/%04d-%s.patch" % (index, name)
        (directory / file).write_text("".join(diff(p, old, new) for p, old, new in changes), encoding="utf-8", newline="\n")
        entries.append({"file": file, "sha256": deploy.sha(directory / file), "strip": 1,
                        "targets": {p: blob(old) for p, old, _ in changes}, "kind": "lab", "summary": "synthetic " + name})
    inner = tar_gz(dict({"srrx-fixture-1.0/" + p: (t.encode(), 0o644) for p, t in SOURCE.items()},
                        **{"srrx-fixture-1.0/configure": (CONFIGURE.encode(), 0o755)}))
    outer = root.parent / "superbuild.tar.gz"
    outer.write_bytes(tar_gz({MEMBER: (inner, 0o644), "superbuild-1.0/README": (b"synthetic superbuild\n", 0o644)}, mtime=1600000000))
    lock = copy.deepcopy(LOCK)
    lock["components"].append({"id": FIXTURE, "version": "1.0+lab1", "commit": None, "source_archive_sha256": deploy.sha(outer),
                               "source_archive_size": outer.stat().st_size, "source_cache_path": "sources/superbuild.tar.gz"})
    (root / "sources.lock.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")
    return entries, outer, lock, hashlib.sha256(inner).hexdigest()


def v2_recipe(entries, member_sha):
    return {"schema_version": 2, "component": FIXTURE, "summary": "synthetic schema-2 recipe of the builder tests",
            "source": {"patch": None, "patches": copy.deepcopy(entries), "member": {"path": MEMBER, "sha256": member_sha}},
            "build_system": "autotools", "build_depends": ["libc6-dev"], "lab_build_depends": [],
            "cmake": None, "autotools": {"flags": ["--disable-greeting", "--without-colour"]},
            "build": [["make", "-C", "{src}", "-j{jobs}"]],
            "install": {"cmake_install": False, "make_install": True,
                        "copy": [{"from": "{recipe}/files/srrx-fixture.conf", "to": "etc/srrx-fixture"}]},
            "hooks": {"source_check": list(SOURCE_CHECK), "package": list(PACKAGE_HOOK)},
            "packages": [{"name": FIXTURE, "section": "misc", "description": "synthetic schema-2 test package",
                          "files": ["usr/bin/*", "usr/share/srrx-fixture/*", "etc/srrx-fixture/*"], "depends": [], "shlibs_depends": False}],
            "drop": [], "checks": [{"kind": "forbid_needed", "files": ["usr/bin/*"], "needed": ["libhamlib*", "libgps*"]},
                                   {"kind": "require_paths", "globs": ["usr/bin/srrx-fixture-hello"]}],
            "notes": ["synthetic"]}


class SchemaV2Tests(unittest.TestCase):
    """build_recipe.validate_recipe for schema_version 2: each new key and each refusal."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-recipe-v2-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "deployment"
        self.root.mkdir()
        self.entries, self.outer, self.lock, self.member_sha = fixture_tree(self.root)
        mocked = patch.object(build_recipe, "DEPLOYMENT", self.root)
        mocked.start()
        self.addCleanup(mocked.stop)

    def recipe(self, change=None):
        data = v2_recipe(self.entries, self.member_sha)
        if change:
            change(data)
        return data

    def validate(self, data):
        return build_recipe.validate_recipe(data, self.lock)

    def test_schema_1_recipes_are_unchanged_and_mean_cmake_without_listed_patches(self):
        for name in ("rtlsdr", "limesuiteng"):
            data = recipe(name)
            self.assertEqual(data["schema_version"], 1)
            with patch.object(build_recipe, "DEPLOYMENT", HERE):
                build_recipe.validate_recipe(data, LOCK)
            view = build_recipe.spec(data)
            self.assertEqual((view["build_system"], view["patches"], view["member"], view["make_install"], view["flags"]),
                             ("cmake", [], None, False, None))
            self.assertEqual(view["hooks"], {"source_check": None, "package": None})
            self.assertEqual(view["patch"], "deployment/patches/%s-rx-only.patch" % name)  # the TX-rejecting patch keeps its place

    def test_a_schema_2_recipe_with_every_new_key_validates(self):
        self.assertEqual(self.validate(self.recipe())["id"], FIXTURE)
        view = build_recipe.spec(self.recipe())
        self.assertEqual((view["build_system"], len(view["patches"]), view["member"]["path"], view["make_install"]),
                         ("autotools", 3, MEMBER, True))
        self.assertEqual(view["flags"], ["--disable-greeting", "--without-colour"])
        # make: no cmake, no autotools, copy-only install; cmake under schema 2: the schema-1 rules.
        self.validate(self.recipe(lambda d: d.update(build_system="make", autotools=None)))
        self.validate(self.recipe(lambda d: (d.update(build_system="cmake", autotools=None, cmake=copy.deepcopy(recipe("rtlsdr")["cmake"]),
                                                      build=[["cmake", "--build", "{build}"]]),
                                             d["install"].update(make_install=False, cmake_install=True))))
        self.validate(self.recipe(lambda d: d["source"].update(patches=[], member=None)))
        self.validate(self.recipe(lambda d: d.update(hooks={"source_check": None, "package": None})))
        self.validate(self.recipe(lambda d: d["install"].update(make_install=False)))  # copy alone
        with_commit = dict(self.entries[0], kind="cherry-pick", upstream_commit="c0b6f8876c514990c2f22ca98b2a6c8a6f290a5d")
        self.validate(self.recipe(lambda d: d["source"].update(patches=[with_commit])))

    def test_each_refusal(self):
        rx_only = self.root.parent / "deployment/patches" / (FIXTURE + "-rx-only.patch")
        rx_only.parent.mkdir(parents=True, exist_ok=True)
        rx_only.write_text(PATCHES[0][1][0][1], encoding="utf-8")
        hook = lambda name, argv: (lambda d: d["hooks"].update({name: argv}))  # noqa: E731
        patches = lambda change: (lambda d: change(d["source"]["patches"]))  # noqa: E731
        flags = lambda *f: (lambda d: d["autotools"].update(flags=list(f)))  # noqa: E731
        cases = {
            "schema_version 3": lambda d: d.update(schema_version=3),
            "schema 2 without hooks": lambda d: d.pop("hooks"),
            "schema 1 with schema-2 keys": lambda d: d.update(schema_version=1),
            "unknown build_system": lambda d: d.update(build_system="meson"),
            # hooks: only python3 -I {recipe}/check_recipe.py <subcommand> of the recipe's own directory
            "hook outside the recipe dir": hook("source_check", ["python3", "-I", "{recipe}/../rtlsdr/check_recipe.py", "verify-source"]),
            "hook absolute script": hook("source_check", ["python3", "-I", "/usr/lib/srrx/check_recipe.py", "verify-source"]),
            "hook script in the source tree": hook("source_check", ["python3", "-I", "{src}/check_recipe.py", "verify-source"]),
            "hook without -I": hook("source_check", ["python3", "{recipe}/check_recipe.py", "verify-source"]),
            "hook other program": hook("package", ["sh", "-c", "rm -rf {destdir}"]),
            "hook other subcommand": hook("source_check", ["python3", "-I", "{recipe}/check_recipe.py", "package"]),
            "hook URL argument": hook("package", PACKAGE_HOOK + ["--fetch=https://example.invalid/tle.txt"]),
            "hook argument leaving its dir": hook("package", ["python3", "-I", "{recipe}/check_recipe.py", "package", "--root", "{destdir}/../.."]),
            "hook output placeholder in source_check": hook("source_check", SOURCE_CHECK + ["--out", "{hook_out}"]),
            "hook unknown placeholder": hook("package", PACKAGE_HOOK + ["{home}"]),
            # source.member
            "member without sha": lambda d: d["source"].update(member={"path": MEMBER}),
            "member with a short sha": lambda d: d["source"].update(member={"path": MEMBER, "sha256": "abc"}),
            "member outside the archive": lambda d: d["source"].update(member={"path": "../inner.tgz", "sha256": "0" * 64}),
            "member not an archive": lambda d: d["source"].update(member={"path": "superbuild-1.0/README", "sha256": "0" * 64}),
            "member with the rx-only patch": lambda d: d["source"].update(patch="deployment/patches/%s-rx-only.patch" % FIXTURE),
            # autotools: fixed --prefix, only listed --enable/--disable/--with/--without flags, no autoreconf
            "autotools prefix flag": flags("--prefix=/opt"),
            "autotools libdir flag": flags("--libdir=/usr/lib"),
            "autotools environment": flags("CFLAGS=-O0"),
            "autotools URL in a flag": flags("--with-tle-url=https://example.invalid/x"),
            "autotools value on disable": flags("--disable-greeting=yes"),
            "autotools option twice": flags("--enable-greeting", "--disable-greeting"),
            "autotools option checking off": flags("--disable-option-checking"),
            "autotools key with make": lambda d: d.update(build_system="make"),
            "autotools without its key": lambda d: d.update(autotools=None),
            "cmake key with autotools": lambda d: d.update(cmake=copy.deepcopy(recipe("rtlsdr")["cmake"])),
            "autoreconf tools in the chroot": lambda d: d["build_depends"].append("autoconf"),
            "dh-autoreconf in the chroot": lambda d: d["build_depends"].append("dh-autoreconf"),
            "URL in a make argv": lambda d: d["build"][0].append("URL=https://example.invalid/x.tar.gz"),
            "configure as a build step": lambda d: d["build"].insert(0, ["{src}/configure", "--prefix=/usr"]),
            "autoreconf as a build step": lambda d: d["build"].insert(0, ["autoreconf", "-fi"]),
            # cmake under schema 2 keeps the non-empty variable rule (no EXTERNAL_PLUGINS="")
            "empty CMake variable": lambda d: (d.update(build_system="cmake", autotools=None, build=[["cmake", "--build", "{build}"]],
                                                        cmake=dict(copy.deepcopy(recipe("rtlsdr")["cmake"]),
                                                                   variables=dict(recipe("rtlsdr")["cmake"]["variables"], EXTERNAL_PLUGINS=""))),
                                               d["install"].update(make_install=False, cmake_install=True)),
            # install
            "make_install with cmake": lambda d: d.update(build_system="cmake", autotools=None, cmake=copy.deepcopy(recipe("rtlsdr")["cmake"])),
            "cmake_install with autotools": lambda d: d["install"].update(cmake_install=True),
            "nothing installed": lambda d: d["install"].update(make_install=False, copy=[]),
            "recipe copy of a missing file": lambda d: d["install"]["copy"].append({"from": "{recipe}/files/absent.conf", "to": "etc"}),
            "recipe copy outside files/": lambda d: d["install"]["copy"].append({"from": "{recipe}/check_recipe.py", "to": "etc"}),
            "recipe copy climbing out of files/": lambda d: d["install"]["copy"].append({"from": "{recipe}/files/../check_recipe.py", "to": "etc"}),
            # source.patches
            "patch sha differs": patches(lambda p: p[0].update(sha256="0" * 64)),
            "patch outside patches/": patches(lambda p: p[0].update(file="check_recipe.py")),
            "TX patch path as a listed patch": patches(lambda p: p[0].update(file="deployment/patches/%s-rx-only.patch" % FIXTURE)),
            "patch listed twice": patches(lambda p: p.append(copy.deepcopy(p[0]))),
            "patch changes an unlisted file": patches(lambda p: p[1]["targets"].pop("src/c.txt")),
            "patch target not a blob id": patches(lambda p: p[0]["targets"].update({"src/a.txt": "1234"})),
            "patch target outside the tree": patches(lambda p: p[0]["targets"].update({"../a.txt": "0" * 40})),
            "patch strip level": patches(lambda p: p[0].update(strip=9)),
            "patch without summary": patches(lambda p: p[0].pop("summary")),
            "patch unknown field": patches(lambda p: p[0].update(note="x")),
            "cherry-pick without its commit": patches(lambda p: p[0].update(kind="cherry-pick")),
            "lab patch with a commit": patches(lambda p: p[0].update(upstream_commit="c0b6f8876c514990c2f22ca98b2a6c8a6f290a5d")),
            "unknown patch kind": patches(lambda p: p[0].update(kind="rx-only")),
            # forbid_needed
            "forbid_needed without files": lambda d: d["checks"].append({"kind": "forbid_needed", "files": [], "needed": ["libhamlib*"]}),
            "forbid_needed without globs": lambda d: d["checks"].append({"kind": "forbid_needed", "files": ["usr/bin/*"]}),
        }
        for label, change in cases.items():
            with self.subTest(label), self.assertRaises(ValueError):
                self.validate(self.recipe(change))
        (self.root / "recipes" / FIXTURE / "check_recipe.py").unlink()
        with self.assertRaisesRegex(build_recipe.RecipeError, "check_recipe.py is missing"):
            self.validate(self.recipe())

    def test_placeholders_outside_their_place_are_refused(self):
        # {recipe} and {hook_out} are not step placeholders, even next to {src} or {build}; a copy
        # takes one leading placeholder only.
        cmake = lambda extra: (lambda d: (d.update(build_system="cmake", autotools=None, build=[["cmake", "--build", "{build}"]],  # noqa: E731
                                                   cmake=dict(copy.deepcopy(recipe("rtlsdr")["cmake"]),
                                                              configure=recipe("rtlsdr")["cmake"]["configure"] + [extra])),
                                          d["install"].update(make_install=False, cmake_install=True)))
        self.validate(self.recipe(cmake("-DSRRX_SOURCE={src}")))  # the same recipe with a step placeholder validates
        for label, change, needle in (
                ("recipe placeholder in a build step", lambda d: d["build"][0].append("F={src}{recipe}"), "unknown placeholder"),
                ("hook_out placeholder in a build step", lambda d: d["build"][0].append("OUT={src}{hook_out}"), "unknown placeholder"),
                ("unclosed placeholder in a build step", lambda d: d["build"][0].append("X={src}{"), "unknown placeholder"),
                ("hook_out placeholder in cmake.configure", cmake("-DOUT={build}{hook_out}"), "unknown placeholder"),
                ("recipe placeholder in cmake.configure", cmake("-DR={build}/{recipe}"), "unknown placeholder"),
                ("placeholder after a copy prefix", lambda d: d["install"]["copy"].append({"from": "{src}/{recipe}/files/x", "to": "etc"}),
                 "install copy goes from"),
                ("placeholder in a copy target", lambda d: d["install"]["copy"].append({"from": "{src}/src/a.txt", "to": "{destdir}/etc"}),
                 "install copy goes from")):
            with self.subTest(label), self.assertRaisesRegex(build_recipe.RecipeError, needle):
                self.validate(self.recipe(change))

    def test_schema_1_keeps_its_exact_shape(self):
        data = recipe("rtlsdr")
        with patch.object(build_recipe, "DEPLOYMENT", HERE):
            build_recipe.validate_recipe(data, LOCK)
            for label, change in {"schema-2 install key": lambda d: d["install"].update(make_install=False),
                                  "recipe file copy": lambda d: d["install"]["copy"].append({"from": "{recipe}/files/x", "to": "etc"}),
                                  "listed patches": lambda d: d["source"].update(patches=[]),
                                  "hooks": lambda d: d.update(hooks={"source_check": None, "package": None})}.items():
                changed = copy.deepcopy(data)
                change(changed)
                with self.subTest(label), self.assertRaises(ValueError):
                    build_recipe.validate_recipe(changed, LOCK)

    def test_patch_paths_refuse_anything_but_changes_to_existing_files(self):
        self.assertEqual(build_recipe.patch_paths(diff("src/a.txt", "a\n", "b\n") + diff("src/b.txt", "b\n", "c\n"), 1), ["src/a.txt", "src/b.txt"])
        self.assertEqual(build_recipe.patch_paths(diff("src/a.txt", "a\n", "b\n"), 2), ["a.txt"])
        with self.assertRaisesRegex(build_recipe.RecipeError, "renames"):
            build_recipe.patch_paths(diff("src/a.txt", "a\n", "b\n"), 0)  # a/src/a.txt and b/src/a.txt differ at -p0
        removed = "--- a/x.sql\n+++ b/x.sql\n@@ -1,2 +1,1 @@\n--- a removed SQL comment\n keep\n"
        self.assertEqual(build_recipe.patch_paths(removed, 1), ["x.sql"])  # a removed line that looks like a header
        for label, text in {"new file": "--- /dev/null\n+++ b/new.c\n@@ -0,0 +1 @@\n+x\n",
                            "deleted file": "--- a/old.c\n+++ /dev/null\n@@ -1 +0,0 @@\n-x\n",
                            "rename": "diff --git a/a.c b/b.c\nsimilarity index 90%\nrename from a.c\nrename to b.c\n",
                            "mode change": "diff --git a/a.sh b/a.sh\nold mode 100644\nnew mode 100755\n",
                            "binary": "diff --git a/a.bin b/a.bin\nGIT binary patch\nliteral 1\n",
                            "renamed in headers": "--- a/a.c\n+++ b/b.c\n@@ -1 +1 @@\n-x\n+y\n"}.items():
            with self.subTest(label), self.assertRaises(build_recipe.RecipeError):
                build_recipe.patch_paths(text, 1)

    def test_satdump_patch_entries_and_hooks_fit_the_schema(self):
        # The satdump recipe's source.patches (0001-0005) and its check_recipe.py hooks.
        data = recipe("satdump")
        listed = (data.get("source") or {}).get("patches") or data.get("patches")
        with patch.object(build_recipe, "DEPLOYMENT", HERE):
            self.assertEqual(len(build_recipe._patches(listed, "satdump")), 5)
            build_recipe._hook(SOURCE_CHECK, "source_check", "satdump")
            build_recipe._hook(PACKAGE_HOOK, "package", "satdump")
            with self.assertRaisesRegex(build_recipe.RecipeError, "check_recipe.py is missing"):
                build_recipe._hook(SOURCE_CHECK, "source_check", "rtlsdr")


class SchemaV2BuilderStepTests(unittest.TestCase):
    """The new builder steps one by one: member extraction, listed patches, configure, hooks, DT_NEEDED."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-builder-v2-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "deployment"
        self.root.mkdir()
        self.entries, self.outer, self.lock, self.member_sha = fixture_tree(self.root)
        self.component = next(c for c in self.lock["components"] if c["id"] == FIXTURE)

    def extracted(self, name="src", member=None):
        work = Path(self.temp.name) / ("work-" + name)
        work.mkdir()
        member = member or {"path": MEMBER, "sha256": self.member_sha}
        return build_recipe.extract(self.outer, self.component, work / "src", None, member), work / "src"

    def test_member_is_the_source_tree_with_its_sha(self):
        (receipt, source, member), tree = self.extracted()
        self.assertEqual((receipt["patch"], member), (None, {"path": MEMBER, "sha256": self.member_sha}))
        self.assertEqual(deploy.sha(source), self.member_sha)
        self.assertEqual(build_recipe.source_date_epoch(source), 1700000000)  # the inner archive's own time
        self.assertEqual({p.relative_to(tree).as_posix() for p in tree.rglob("*") if p.is_file()}, set(SOURCE) | {"configure"})
        with self.assertRaisesRegex(build_recipe.RecipeError, "differs from its recorded sha256"):
            self.extracted("bad-sha", {"path": MEMBER, "sha256": "0" * 64})
        with self.assertRaisesRegex(build_recipe.RecipeError, "not one regular file"):
            self.extracted("absent", {"path": "superbuild-1.0/src/other.tgz", "sha256": self.member_sha})
        with self.assertRaisesRegex(build_recipe.RecipeError, "differs from the lock"):
            build_recipe.extract(self.outer, dict(self.component, source_archive_size=1), Path(self.temp.name) / "x", None,
                                 {"path": MEMBER, "sha256": self.member_sha})

    @unittest.skipUnless(shutil.which("git"), "git unavailable")
    def test_listed_patches_apply_in_order_with_one_receipt_each(self):
        import vendor_patch
        _, tree = self.extracted()
        base = self.root / "recipes" / FIXTURE
        receipts = vendor_patch.apply_listed(tree, base, self.entries)
        self.assertEqual([r["file"] for r in receipts], [e["file"] for e in self.entries])
        self.assertEqual(sum(len(r["targets"]) for r in receipts), 4)
        for receipt, (_, changes) in zip(receipts, PATCHES):
            self.assertEqual(receipt["after"], {p: blob(new) for p, _, new in changes})
            for path, _, new in changes:
                self.assertEqual((tree / path).read_text(encoding="utf-8"), new)
        with self.assertRaisesRegex(vendor_patch.PatchError, "recorded git blob: src/a.txt"):
            vendor_patch.apply_listed(tree, base, self.entries[:1])  # already patched: the target blob moved on
        _, fresh = self.extracted("fresh")
        partial = [dict(self.entries[1], targets={"src/b.txt": self.entries[1]["targets"]["src/b.txt"]})]
        with self.assertRaisesRegex(vendor_patch.PatchError, "other files than its targets"):
            vendor_patch.apply_listed(fresh, base, partial)
        self.assertEqual((fresh / "src/b.txt").read_text(encoding="utf-8"), "beta\n")  # refused before git apply
        (base / self.entries[2]["file"]).write_text("changed after the review\n", encoding="utf-8")
        with self.assertRaisesRegex(vendor_patch.PatchError, "recorded SHA-256"):
            vendor_patch.apply_listed(fresh, base, self.entries)

    def test_vendor_patch_pins_come_from_the_lock(self):
        import vendor_patch
        lock = {c["id"]: c["commit"] for c in LOCK["components"]}
        order = list(json.loads((HERE / "patches/target-hashes.json").read_text(encoding="utf-8")))
        self.assertLessEqual({"rtlsdr", "limesuiteng"}, set(order))
        self.assertEqual(list(vendor_patch.pins().items()), [(c, lock[c]) for c in order])  # target-hashes order, lock commits
        self.assertFalse(hasattr(vendor_patch, "PINS"))  # no second copy of the pinned commits

    def test_a_reviewed_patch_without_a_fixture_is_listed_or_refused(self):
        import vendor_patch
        here = Path(self.temp.name) / "vendor"
        (here / "recipes" / FIXTURE).mkdir(parents=True)
        recipe_path = here / "recipes" / FIXTURE / "recipe.json"
        with patch.object(vendor_patch, "HERE", here), patch.object(vendor_patch, "pins", return_value={FIXTURE: "0" * 40}):
            with self.assertRaisesRegex(vendor_patch.PatchError, "no upstream fixture and no recipe that applies it: " + FIXTURE):
                vendor_patch.check_fixtures()  # neither a fixture nor a recipe
            recipe_path.write_text(json.dumps({"schema_version": 2, "source": {"patch": None}}), encoding="utf-8")
            with self.assertRaisesRegex(vendor_patch.PatchError, "no recipe that applies it"):
                vendor_patch.without_fixture()  # a recipe that does not apply the reviewed patch
            recipe_path.write_text(json.dumps({"schema_version": 1, "source": {"patch": "deployment/patches/%s-rx-only.patch" % FIXTURE}}),
                                   encoding="utf-8")
            listed = vendor_patch.without_fixture()
            self.assertEqual([(e["component"], e["status"], e["source_fixture_only"], e["release_ready"]) for e in listed],
                             [(FIXTURE, "NO_UPSTREAM_FIXTURE", False, False)])
            self.assertIn("deployment/recipes/" + FIXTURE, listed[0]["checked_by"])
            self.assertEqual(vendor_patch.check_fixtures(), [])  # listed, never counted as a fixture result
        # In this tree rtl-sdr and limesuiteng have fixtures; any other reviewed patch is listed with its recipe.
        self.assertFalse({"rtlsdr", "limesuiteng"} & {e["component"] for e in vendor_patch.without_fixture()})

    def test_configure_must_be_generated_and_declare_every_flag(self):
        _, tree = self.extracted()
        result = build_recipe.check_configure(tree, ["--disable-greeting", "--with-colour=no"])
        self.assertEqual((result["prefix"], result["declared"]), ("/usr", 3))
        with self.assertRaisesRegex(build_recipe.RecipeError, "not declared upstream: --enable-telemetry"):
            build_recipe.check_configure(tree, ["--enable-telemetry"])
        (tree / "configure").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        with self.assertRaisesRegex(build_recipe.RecipeError, "ac_user_opts"):
            build_recipe.check_configure(tree, [])
        (tree / "configure").unlink()
        with self.assertRaisesRegex(build_recipe.RecipeError, "generated configure of a release tarball"):
            build_recipe.check_configure(tree, [])

    def test_hooks_must_report_ok_without_findings(self):
        values = {"src": Path("/w/src"), "destdir": Path("/w/destdir"), "hook_out": Path("/w/hook.json"), "recipe": self.root / "recipes" / FIXTURE}
        log = Path(self.temp.name) / "hook.log"

        def runs(code, stdout):
            return patch.object(build_recipe.subprocess, "run", return_value=subprocess.CompletedProcess([], code, stdout, ""))
        with runs(0, 'noise\n{"command": "verify-source", "findings": [], "ok": true}\n') as mocked:
            entry = build_recipe.run_hook("source_check", SOURCE_CHECK, values, {}, log, Path(self.temp.name))
        self.assertEqual(mocked.call_args[0][0][:4], ["python3", "-I", str(values["recipe"]) + "/check_recipe.py", "verify-source"])
        self.assertEqual((entry["status"], entry["argv"], entry["script_sha256"]),
                         ("CI_PASS", SOURCE_CHECK, deploy.sha(values["recipe"] / "check_recipe.py")))
        for code, stdout in ((2, '{"findings": ["x"], "ok": false}'), (0, '{"findings": ["x"], "ok": true}'),
                             (0, '{"ok": false}'), (0, "not json"), (0, ""), (1, '{"ok": true}')):
            with self.subTest(stdout=stdout, code=code), runs(code, stdout), self.assertRaisesRegex(build_recipe.RecipeError, "hooks.source_check failed"):
                build_recipe.run_hook("source_check", SOURCE_CHECK, values, {}, log, Path(self.temp.name))
        out = Path(self.temp.name) / "hook-out.json"
        out.write_text('{"record_digests": []}', encoding="utf-8")
        with self.assertRaisesRegex(build_recipe.RecipeError, "object record_digests"):
            build_recipe.hook_output(out)

    def test_forbid_needed_reads_dt_needed_of_matched_elf_files(self):
        stage = Path(self.temp.name) / "stage"
        (stage / "usr/bin").mkdir(parents=True)
        (stage / "usr/bin/jt9").write_bytes(b"\x7fELF synthetic")
        (stage / "usr/bin/notes.txt").write_text("not an ELF file", encoding="utf-8")
        check = {"kind": "forbid_needed", "files": ["usr/bin/*"], "needed": ["libhamlib*", "libgps*"]}
        readelf = (" 0x0000000000000001 (NEEDED)             Shared library: [libfftw3f.so.3]\n"
                   " 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]\n")
        with patch.object(build_recipe, "_tool", return_value=readelf) as tool:
            result = build_recipe.run_checks({"checks": [check]}, stage)[0]
        self.assertEqual(tool.call_args[0][0][:2], ["readelf", "-d"])
        self.assertEqual((result["status"], result["dt_needed"]), ("CI_PASS", {"usr/bin/jt9": ["libfftw3f.so.3", "libc.so.6"]}))
        with patch.object(build_recipe, "_tool", return_value=readelf + " 0x1 (NEEDED) Shared library: [libhamlib.so.4]\n"), \
                self.assertRaisesRegex(build_recipe.RecipeError, "forbidden DT_NEEDED: usr/bin/jt9: libhamlib.so.4"):
            build_recipe.run_checks({"checks": [check]}, stage)
        with self.assertRaisesRegex(build_recipe.RecipeError, "matches no ELF file"):
            build_recipe.run_checks({"checks": [dict(check, files=["usr/lib/*"])]}, stage)


TOOLS = ("git", "make", "cc", "readelf", "dpkg-deb", "dpkg-query", "python3")


@unittest.skipUnless(os.name == "posix" and all(shutil.which(t) for t in TOOLS), "needs " + ", ".join(TOOLS) + " (Linux host regression)")
class SchemaV2BuildTests(unittest.TestCase):
    """One real schema-2 build on the host, outside a chroot (no_network is the builder's own check
    of its namespace and is replaced here): member, 3 listed patches, both hooks, autotools,
    make install, a recipe file, forbid_needed, record_digests and the record binding."""

    def test_autotools_member_three_patches_and_hooks_build_into_a_bound_record(self):
        with tempfile.TemporaryDirectory(prefix="srrx-build-v2-") as temporary:
            root = Path(temporary) / "deployment"
            root.mkdir()
            entries, outer, lock, member_sha = fixture_tree(root)
            directory = root / "recipes" / FIXTURE
            (directory / "recipe.json").write_text(json.dumps(v2_recipe(entries, member_sha), indent=2), encoding="utf-8")
            work, out = Path(temporary) / "work", Path(temporary) / "out"
            with patch.object(build_recipe, "DEPLOYMENT", root), patch.object(build_recipe, "no_network", return_value="not checked (host test)"):
                record = build_recipe.build(directory / "recipe.json", outer, work, out, 2)
            environment = record["build_environment"]
            self.assertEqual([r["file"] for r in environment["patch_receipts"]], [e["file"] for e in entries])
            self.assertEqual((environment["source_member"], environment["build_system"], environment["cmake_options"]),
                             ({"path": MEMBER, "sha256": member_sha}, "autotools", None))
            self.assertEqual(environment["configure_options"]["flags"], ["--disable-greeting", "--without-colour"])
            self.assertEqual([(h["hook"], h["status"]) for h in environment["hooks"]], [("source_check", "CI_PASS"), ("package", "CI_PASS")])
            self.assertEqual(sorted(environment["recipe_files"]), ["check_recipe.py", "files/srrx-fixture.conf"])
            self.assertEqual(environment["source_date_epoch"], 1700000000)
            hello = work / "destdir/usr/bin/srrx-fixture-hello"
            self.assertEqual(record["record_digests"], {"hello_sha256": deploy.sha(hello)})
            self.assertEqual(subprocess.run([str(hello)], capture_output=True, text=True, check=True).stdout, "srrx fixture patched\n")
            self.assertEqual((work / "destdir/usr/share/srrx-fixture/a.txt").read_text(encoding="utf-8"), "alpha patched\n")
            self.assertFalse((work / "destdir/usr/share/srrx-fixture/dropped-by-hook.txt").exists())  # the package hook ran before the checks
            needed = next(c for c in record["checks"] if c["check"] == "forbid_needed")["dt_needed"]
            self.assertIn("libc.so.6", needed["usr/bin/srrx-fixture-hello"])
            self.assertEqual([p["package"] for p in record["packages"]], [FIXTURE])
            self.assertEqual(deploy.load(out / (FIXTURE + ".build-record.json")), record)
            self.assertTrue((out / (FIXTURE + ".package-hook.json")).is_file())
            with patch.object(deploy, "HERE", root), patch.object(deploy, "PROJECT", root.parent):
                deploy._record_binding(record, "fixture")
                spec = importlib.util.spec_from_file_location("srrx_check_repo_v2", HERE / "repo/check_repo.py")
                check_repo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(check_repo)
                self.assertEqual(check_repo.record_binding(out / (FIXTURE + ".build-record.json"), record),
                                 {"component": FIXTURE, "patch_receipts": 3, "source_member": MEMBER, "record_digests": True})
                dropped = copy.deepcopy(record)
                dropped["build_environment"]["patch_receipts"].pop()
                with self.assertRaisesRegex(deploy.DeploymentError, "patch list differs .*3 listed, 2 recorded"):
                    deploy._record_binding(dropped, "fixture")
                changed = copy.deepcopy(record)
                changed["record_digests"]["hello_sha256"] = "0" * 64
                with self.assertRaisesRegex(check_repo.CheckError, "record_digests differ"):
                    check_repo.record_binding(out / (FIXTURE + ".build-record.json"), changed)
                (directory / entries[1]["file"]).write_text("changed after the build\n", encoding="utf-8")
                with self.assertRaisesRegex(deploy.DeploymentError, "patch list differs"):
                    deploy._record_binding(record, "fixture")


# --- W2 SW-CI: the optional schema-2 "ci" key, build_recipe.ci_plan (what sr-rx-packages.yml builds,
# in which job) and the per-package data tree (D-17). Synthetic deployment trees; nothing is fetched.
CI ={"heavy": True, "runtime_depends": ["strace"], "tag_samples": []}


def plan_recipe(name, packages, lab=(), heavy=None):
    """A minimal valid schema-2 recipe (make, make install, no patches, hooks or member)."""
    data = {"schema_version": 2, "component": name, "summary": "synthetic plan recipe", "source": {"patch": None, "patches": [], "member": None},
            "build_system": "make", "build_depends": ["libc6-dev"], "lab_build_depends": list(lab), "cmake": None, "autotools": None,
            "build": [["make", "-C", "{src}"]], "install": {"cmake_install": False, "make_install": True, "copy": []},
            "hooks": {"source_check": None, "package": None},
            "packages": [{"name": p, "section": "misc", "description": "synthetic", "files": ["usr/share/%s/*" % p], "depends": [],
                          "shlibs_depends": False} for p in packages],
            "drop": [], "checks": [], "notes": []}
    if heavy is not None:
        data["ci"] = {"heavy": heavy, "runtime_depends": [], "tag_samples": []}
    return data


class CiKeyTests(unittest.TestCase):
    """validate_recipe: "ci" is the one optional schema-2 key, with exactly heavy, runtime_depends, tag_samples."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-recipe-ci-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "deployment"
        self.root.mkdir()
        self.entries, self.outer, self.lock, self.member_sha = fixture_tree(self.root)
        mocked = patch.object(build_recipe, "DEPLOYMENT", self.root)
        mocked.start()
        self.addCleanup(mocked.stop)

    def recipe(self, ci=None):
        data = v2_recipe(self.entries, self.member_sha)
        if ci is not None:
            data["ci"] = copy.deepcopy(ci)
        return data

    def test_ci_is_optional_and_exact(self):
        self.assertEqual(build_recipe.ci_view(self.recipe()), {"heavy": False, "runtime_depends": [], "tag_samples": []})
        build_recipe.validate_recipe(self.recipe(CI), self.lock)
        self.assertEqual(build_recipe.ci_view(self.recipe(CI)), CI)
        self.assertEqual(build_recipe.ci_view(recipe("rtlsdr")), {"heavy": False, "runtime_depends": [], "tag_samples": []})
        for label, ci in {"unknown key": dict(CI, timeout=60), "missing key": {"heavy": True}, "heavy not a bool": dict(CI, heavy="yes"),
                          "runtime package twice": dict(CI, runtime_depends=["strace", "strace"]),
                          "runtime package not a name": dict(CI, runtime_depends=["strace; curl"]),
                          "sample outside the tree": dict(CI, tag_samples=["../samples"]), "absolute sample": dict(CI, tag_samples=["/samples"]),
                          "sample twice": dict(CI, tag_samples=["samples", "samples"]), "not an object": ["heavy"]}.items():
            with self.subTest(label), self.assertRaises(ValueError):
                build_recipe.validate_recipe(self.recipe(ci), self.lock)
        with patch.object(build_recipe, "DEPLOYMENT", HERE), self.assertRaises(ValueError):
            build_recipe.validate_recipe(dict(recipe("rtlsdr"), ci=dict(CI)), LOCK)  # schema 1 keeps its exact keys

    def test_tag_samples_need_a_tagged_component(self):
        sampled = dict(CI, tag_samples=["samples/FT8"])
        with self.assertRaisesRegex(build_recipe.RecipeError, "tag and an https upstream_url"):
            build_recipe.validate_recipe(self.recipe(sampled), self.lock)
        tagged = copy.deepcopy(self.lock)
        component = next(c for c in tagged["components"] if c["id"] == FIXTURE)
        component.update(tag="srrx-fixture-1.0", upstream_url="https://example.invalid/srrx-fixture.git")
        build_recipe.validate_recipe(self.recipe(sampled), tagged)
        component["upstream_url"] = "git://example.invalid/srrx-fixture.git"
        with self.assertRaises(build_recipe.RecipeError):
            build_recipe.validate_recipe(self.recipe(sampled), tagged)


class CiPlanTests(unittest.TestCase):
    """build_recipe.ci_plan over a synthetic deployment/recipes tree."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-ci-plan-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "deployment"
        (self.root / "recipes").mkdir(parents=True)
        self.lock = copy.deepcopy(LOCK)
        self.lock["components"] = []
        mocked = patch.object(build_recipe, "DEPLOYMENT", self.root)
        mocked.start()
        self.addCleanup(mocked.stop)

    def add(self, name, data):
        (self.root / "recipes" / name).mkdir(exist_ok=True)
        (self.root / "recipes" / name / "recipe.json").write_text(json.dumps(data), encoding="utf-8")
        if not any(c["id"] == data.get("component", data.get("id")) for c in self.lock["components"]):
            self.lock["components"].append({"id": data.get("component", data.get("id")), "version": "1.0+lab1", "commit": None,
                                            "source_archive_sha256": "a" * 64, "source_archive_size": 1,
                                            "source_cache_path": "sources/%s.tar.gz" % name})

    def test_build_order_heavy_chains_and_skipped_recipes(self):
        self.add("srrx-c", plan_recipe("srrx-c", ["srrx-c-tools"]))
        self.add("srrx-b", plan_recipe("srrx-b", ["srrx-b-tools"], lab=["libsrrx-a-dev"], heavy=False))
        self.add("srrx-a", plan_recipe("srrx-a", ["libsrrx-a1", "libsrrx-a-dev"]))
        self.add("srrx-h", plan_recipe("srrx-h", ["srrx-h-tools"], lab=["libsrrx-a-dev", "srrx-b-tools"], heavy=True))
        self.add("srrx-p", {"id": "srrx-p", "kind": build_recipe.PENDING_KIND, "status": build_recipe.PENDING_STATUS})
        (self.root / "recipes/srrx-b/runtime_check.py").write_text("# synthetic\n", encoding="utf-8")
        plan = build_recipe.ci_plan(self.lock)
        self.assertEqual((plan["light"], plan["heavy"]), (["srrx-a", "srrx-b", "srrx-c"], ["srrx-h"]))
        self.assertEqual(plan["recipes"]["srrx-h"]["chain"], ["srrx-a", "srrx-b", "srrx-h"])
        self.assertEqual(plan["recipes"]["srrx-b"]["needs"], ["srrx-a"])
        self.assertEqual((plan["recipes"]["srrx-b"]["runtime_check"], plan["recipes"]["srrx-c"]["runtime_check"]), (True, False))
        self.assertIn(build_recipe.PENDING_STATUS, plan["skipped"]["srrx-p"])
        self.assertNotIn("srrx-p", plan["recipes"])

    def test_inconsistent_trees_fail_the_plan(self):
        cases = {
            "lab package no recipe builds": [("srrx-a", plan_recipe("srrx-a", ["srrx-a-tools"], lab=["libsrrx-x-dev"]))],
            "cycle": [("srrx-a", plan_recipe("srrx-a", ["libsrrx-a-dev"], lab=["libsrrx-b-dev"])),
                      ("srrx-b", plan_recipe("srrx-b", ["libsrrx-b-dev"], lab=["libsrrx-a-dev"]))],
            "package of two recipes": [("srrx-a", plan_recipe("srrx-a", ["srrx-tools"])), ("srrx-b", plan_recipe("srrx-b", ["srrx-tools"]))],
            "light needs heavy": [("srrx-a", plan_recipe("srrx-a", ["libsrrx-a-dev"], heavy=True)),
                                  ("srrx-b", plan_recipe("srrx-b", ["srrx-b-tools"], lab=["libsrrx-a-dev"]))],
            "directory is another component": [("srrx-a", plan_recipe("srrx-z", ["srrx-z-tools"]))],
            "invalid recipe": [("srrx-a", dict(plan_recipe("srrx-a", ["srrx-a-tools"]), build=[["curl", "-O", "x"]]))],
        }
        for label, recipes in cases.items():
            with self.subTest(label):
                shutil.rmtree(self.root / "recipes")
                (self.root / "recipes").mkdir()
                self.lock["components"] = []
                for name, data in recipes:
                    self.add(name, data)
                with self.assertRaises(build_recipe.RecipeError):
                    build_recipe.ci_plan(self.lock)

    def test_the_real_tree_plans_rtlsdr_and_limesuiteng_light_and_skips_satdump(self):
        with patch.object(build_recipe, "DEPLOYMENT", HERE):
            plan = build_recipe.ci_plan(LOCK)
        self.assertLessEqual({"rtlsdr", "limesuiteng"}, set(plan["light"]))
        self.assertEqual(sorted(plan["skipped"]), PENDING)
        for name in plan["light"] + plan["heavy"]:
            self.assertEqual(plan["recipes"][name]["chain"][-1], name)


class DataTreeTests(unittest.TestCase):
    """build_recipe.package_data_tree: the full data tree, also where package_manifest refuses it."""

    def test_dangling_dev_link_gives_a_full_data_tree_while_the_manifest_stays_empty(self):
        with tempfile.TemporaryDirectory(prefix="srrx-data-tree-") as temporary:
            root = Path(temporary)
            (root / "usr/include").mkdir(parents=True)
            (root / "usr/lib/aarch64-linux-gnu").mkdir(parents=True)
            (root / "usr/include/rx.h").write_bytes(b"/* synthetic header */\n")
            (root / "DEBIAN").mkdir()
            (root / "DEBIAN/control").write_text("Package: x\n", encoding="utf-8")
            try:
                os.symlink("librx.so.2", root / "usr/lib/aarch64-linux-gnu/librx.so")
            except OSError as exc:  # unprivileged Windows host only; Linux CI always creates links
                self.skipTest("symlinks unavailable: " + str(exc))
            tree = build_recipe.package_data_tree(root)
            self.assertEqual(sorted(tree), ["usr", "usr/include", "usr/include/rx.h", "usr/lib", "usr/lib/aarch64-linux-gnu",
                                            "usr/lib/aarch64-linux-gnu/librx.so"])  # DEBIAN/ is not data
            self.assertEqual(tree["usr/lib/aarch64-linux-gnu/librx.so"], {"type": "symlink", "target": "librx.so.2"})
            self.assertEqual(tree["usr/include/rx.h"]["sha256"], hashlib.sha256(b"/* synthetic header */\n").hexdigest())
            self.assertEqual(tree["usr"]["type"], "dir")
            if os.name == "posix":
                os.chmod(root / "usr/include/rx.h", 0o644)
                os.chmod(root / "usr/include", 0o755)
                tree = build_recipe.package_data_tree(root)
                self.assertEqual((tree["usr/include/rx.h"]["mode"], tree["usr/include"]["mode"]), ("0644", "0755"))
            manifest = build_recipe.package_manifest(root)
            self.assertEqual(manifest["files"], {})
            self.assertIn("dangling link usr/lib/aarch64-linux-gnu/librx.so", build_recipe.inventory_refusal(root))
            document = build_recipe.data_tree_document("librx-dev", "1.0+lab1", tree)
            self.assertEqual((document["kind"], document["package"], document["entries"]), ("srrx_lab_data_tree", "librx-dev", tree))


# A package hook that also leaves a -dev package's dangling .so link in DESTDIR.
DEV_CHECK_RECIPE = CHECK_RECIPE.replace('    (args.root / "usr/share/srrx-fixture/dropped-by-hook.txt").unlink()\n',
                                        '    (args.root / "usr/share/srrx-fixture/dropped-by-hook.txt").unlink()\n'
                                        '    (args.root / "usr/lib").mkdir(parents=True, exist_ok=True)\n'
                                        '    (args.root / "usr/lib/libsrrx-fixture.so").symlink_to("libsrrx-fixture.so.1")\n')


@unittest.skipUnless(os.name == "posix" and all(shutil.which(t) for t in TOOLS), "needs " + ", ".join(TOOLS) + " (Linux host regression)")
class DataTreeBuildTests(unittest.TestCase):
    """One real schema-2 build with a -dev package whose .so link dangles: every package gets its
    data tree, check_repo.py packages reports DATA_TREE_MATCH while that manifest stays empty with
    its reason, and one changed hash, mode or link target, or a missing data tree, is refused."""

    def test_every_package_has_a_matching_data_tree_and_tampering_is_refused(self):
        self.assertNotEqual(DEV_CHECK_RECIPE, CHECK_RECIPE)
        with tempfile.TemporaryDirectory(prefix="srrx-build-tree-") as temporary:
            root = Path(temporary) / "deployment"
            root.mkdir()
            entries, outer, lock, member_sha = fixture_tree(root)
            directory = root / "recipes" / FIXTURE
            (directory / "check_recipe.py").write_text(DEV_CHECK_RECIPE, encoding="utf-8", newline="\n")
            data = v2_recipe(entries, member_sha)
            data["packages"].append({"name": FIXTURE + "-dev", "section": "libdevel", "description": "synthetic -dev package",
                                     "files": ["usr/lib/*"], "depends": [], "shlibs_depends": False})
            (directory / "recipe.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
            out = Path(temporary) / "out"
            with patch.object(build_recipe, "DEPLOYMENT", root), patch.object(build_recipe, "no_network", return_value="not checked (host test)"):
                record = build_recipe.build(directory / "recipe.json", outer, Path(temporary) / "work", out / FIXTURE, 2)
            for package in record["packages"]:
                tree_path = out / FIXTURE / (package["package"] + ".data-tree.json")
                self.assertEqual(deploy.sha(tree_path), package["data_tree_sha256"])
                document = deploy.load(tree_path)
                self.assertEqual(document["entries"], deploy.deb_data_inventory(out / FIXTURE / package["filename"]))
            dev = deploy.load(out / FIXTURE / (FIXTURE + "-dev.data-tree.json"))["entries"]
            self.assertEqual(dev["usr/lib/libsrrx-fixture.so"], {"type": "symlink", "target": "libsrrx-fixture.so.1"})
            self.assertEqual(deploy.load(out / FIXTURE / (FIXTURE + "-dev.build-manifest.json"))["files"], {})
            hello = deploy.load(out / FIXTURE / (FIXTURE + ".data-tree.json"))["entries"]["usr/bin/srrx-fixture-hello"]
            self.assertEqual(hello["mode"], "0755")
            spec = importlib.util.spec_from_file_location("srrx_check_repo_tree", HERE / "repo/check_repo.py")
            check_repo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(check_repo)
            record_path = out / FIXTURE / (FIXTURE + ".build-record.json")
            with patch.object(deploy, "HERE", root), patch.object(deploy, "PROJECT", root.parent), patch.object(build_recipe, "DEPLOYMENT", root):
                summary = {p["package"]: p for p in check_repo.packages(out)["packages"]}
                self.assertEqual({n: p["data_tree"] for n, p in summary.items()}, {FIXTURE: "DATA_TREE_MATCH", FIXTURE + "-dev": "DATA_TREE_MATCH"})
                self.assertTrue(summary[FIXTURE + "-dev"]["manifest_files"].startswith("NONE: not self-contained"))
                original = record_path.read_text(encoding="utf-8")

                def tampered(package, edit, rebind=True):
                    tree_path = out / FIXTURE / (package + ".data-tree.json")
                    saved = tree_path.read_bytes()
                    document = deploy.load(tree_path)
                    edit(document)
                    tree_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                    changed = json.loads(original)
                    if rebind:
                        next(p for p in changed["packages"] if p["package"] == package)["data_tree_sha256"] = deploy.sha(tree_path)
                    record_path.write_text(json.dumps(changed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                    try:
                        with self.assertRaises(check_repo.CheckError) as caught:
                            check_repo.packages(out)
                    finally:
                        tree_path.write_bytes(saved)
                        record_path.write_text(original, encoding="utf-8")
                    return str(caught.exception)
                link = lambda d: d["entries"]["usr/lib/libsrrx-fixture.so"].update(target="libsrrx-fixture.so.2")  # noqa: E731
                self.assertIn("differs from its data tree", tampered(FIXTURE + "-dev", link))
                self.assertIn("differs from its data tree",
                              tampered(FIXTURE, lambda d: d["entries"]["usr/bin/srrx-fixture-hello"].update(mode="0644")))
                self.assertIn("differs from its data tree",
                              tampered(FIXTURE, lambda d: d["entries"]["usr/bin/srrx-fixture-hello"].update(sha256="0" * 64)))
                self.assertIn("differs from the build record", tampered(FIXTURE + "-dev", link, rebind=False))
                tree_path = out / FIXTURE / (FIXTURE + "-dev.data-tree.json")
                saved = tree_path.read_bytes()
                tree_path.unlink()
                with self.assertRaisesRegex(check_repo.CheckError, "differs from the build record"):
                    check_repo.packages(out)
                tree_path.write_bytes(saved)
                unbound = json.loads(original)
                unbound["packages"][1].pop("data_tree_sha256")
                record_path.write_text(json.dumps(unbound), encoding="utf-8")
                with self.assertRaisesRegex(check_repo.CheckError, "lists no data tree"):
                    check_repo.packages(out)
                record_path.write_text(original, encoding="utf-8")
                self.assertEqual(check_repo.packages(out)["status"], "CI_PACKAGES_MATCH_BUILD_RECORDS")


# --- W2 SW-SATDUMP: satdump is a schema-2 builder recipe (heavy job, five listed patches, hooks, runtime check).
class SatDumpBuilderRecipeTests(unittest.TestCase):
    def setUp(self):
        self.data = recipe("satdump")

    def test_satdump_is_a_validating_heavy_recipe_of_the_real_tree(self):
        self.assertIn("satdump", RECIPES)
        self.assertEqual(PENDING, [])
        component = build_recipe.validate_recipe(self.data, LOCK)
        self.assertEqual((self.data["schema_version"], self.data["component"], component["version"]),
                         (2, "satdump", "2.0.0~alpha+git20260929+lab1"))
        self.assertEqual(build_recipe.ci_view(self.data), {"heavy": True, "runtime_depends": ["binutils", "strace"], "tag_samples": []})
        with patch.object(build_recipe, "DEPLOYMENT", HERE):
            plan = build_recipe.ci_plan(LOCK)
        # Only satdump's own place in the plan: other recipe packages add light or heavy recipes to the same tree.
        self.assertIn("satdump", plan["heavy"])
        self.assertNotIn("satdump", plan["light"])
        self.assertEqual(plan["recipes"]["satdump"]["chain"], ["satdump"])
        self.assertTrue(plan["recipes"]["satdump"]["runtime_check"])
        self.assertEqual(plan["skipped"], {})
        self.assertLessEqual({"limesuiteng", "rtlsdr"}, set(plan["light"]))

    def test_satdump_build_steps_hooks_and_packages(self):
        self.assertEqual(self.data["cmake"]["configure"], ["cmake", "-S", "{src}", "-B", "{build}", "-G", "Ninja"])
        self.assertIn("ninja-build", self.data["build_depends"])
        for name in ("libarmadillo-dev", "libzstd-dev", "librtlsdr-dev", "libhackrf-dev", "portaudio19-dev", "libusb-1.0-0-dev"):
            self.assertNotIn(name, self.data["build_depends"])
        self.assertEqual(self.data["hooks"], {"source_check": SOURCE_CHECK, "package": PACKAGE_HOOK})
        self.assertEqual([p["name"] for p in self.data["packages"]], ["satdump"])
        self.assertTrue(self.data["packages"][0]["shlibs_depends"])
        self.assertEqual(self.data["lab_build_depends"], [])
        variables = self.data["cmake"]["variables"]
        self.assertEqual((variables["CMAKE_INSTALL_LIBDIR"], variables["CMAKE_INSTALL_RPATH"], variables["FETCHCONTENT_FULLY_DISCONNECTED"]),
                         ("lib", "/usr/lib/satdump/plugins", "ON"))
        self.assertNotIn("EXTERNAL_PLUGINS", variables)  # an empty value is never passed; the upstream default is empty
        kinds = [c["kind"] for c in self.data["checks"]]
        self.assertEqual(kinds.count("require_paths"), 15)  # binary, core, config, 7 plugins, 5 pipelines
        self.assertEqual(kinds[-2:], ["forbid_paths", "forbid_needed"])

    def test_heavy_selection_runs_satdump_for_its_own_inputs_only(self):
        spec = importlib.util.spec_from_file_location("srrx_check_repo_satdump", HERE / "repo/check_repo.py")
        check_repo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(check_repo)
        project = check_repo.PROJECT_PREFIX + "deployment/"
        plan = check_repo.plan([project + "recipes/satdump/runtime_check.py"], LOCK, False)
        self.assertEqual(plan["heavy_run"], ["satdump"])
        self.assertEqual(plan["build"], plan["light"] + ["satdump"])
        # Another recipe's input never selects satdump (a heavy recipe whose chain holds rtlsdr may run).
        self.assertNotIn("satdump", check_repo.plan([project + "recipes/rtlsdr/recipe.json"], LOCK, False)["heavy_run"])
        self.assertNotIn("satdump", check_repo.plan([project + "recipes/README.md"], LOCK, False)["heavy_run"])


if __name__ == "__main__":
    unittest.main()
