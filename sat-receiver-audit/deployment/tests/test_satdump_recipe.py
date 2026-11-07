"""SatDump +lab recipe (deployment/recipes/satdump): builder recipe, packaging data, hooks, runtime check.

Offline only: the pinned source is not in Git, so verify-source runs here on synthetic trees; on
the package builder it is the recipe's source_check hook on the extracted archive (sr-rx-packages
heavy job). The runtime check itself runs only in the sr-rx-packages runtime chroot; here its
constants are compared with the recipe, packaging.json and srrx.satdump_pass, and its strace parser
is fed sample lines. The OMM CSV column order (omm-csv) is checked here against the pinned reader.
"""
import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
RECIPE = HERE / "recipes/satdump"
spec = importlib.util.spec_from_file_location("check_recipe", RECIPE / "check_recipe.py")
check_recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_recipe)
spec = importlib.util.spec_from_file_location("satdump_runtime_check", RECIPE / "runtime_check.py")
runtime_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime_check)
sys.path.insert(0, str(HERE.parent / "software"))
from srrx import baseband, decoder_policy, orbits, satdump_pass  # noqa: E402
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "recipes"))
import build_recipe  # noqa: E402
import deploy  # noqa: E402
import selftest  # noqa: E402


class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.recipe, self.options = check_recipe.load("recipe.json"), check_recipe.load("upstream-options.json")
        self.packaging = check_recipe.load("packaging.json")

    def findings(self, recipe=None, packaging=None, policy=None):
        return check_recipe.check(recipe or self.recipe, self.options, policy, packaging or self.packaging)

    def test_committed_recipe_is_consistent_and_a_heavy_builder_recipe(self):
        self.assertEqual(check_recipe.check(), [])
        component = build_recipe.validate_recipe(self.recipe)
        self.assertEqual((component["id"], component["version"]), ("satdump", self.packaging["package"]["version"]))
        self.assertFalse(build_recipe.is_pending(self.recipe))
        plan = build_recipe.ci_plan()
        self.assertIn("satdump", plan["heavy"])
        self.assertEqual(plan["recipes"]["satdump"]["chain"], ["satdump"])
        self.assertEqual(plan["recipes"]["satdump"]["runtime_depends"], ["binutils", "strace"])
        self.assertTrue(plan["recipes"]["satdump"]["runtime_check"])
        self.assertNotIn("satdump", plan["skipped"])

    def test_every_upstream_option_is_set_and_only_the_allowlist_is_on(self):
        values = self.recipe["cmake"]["options"]
        self.assertEqual(len(self.options["options"]), 105)
        self.assertEqual(list(values), [o["name"] for o in self.options["options"]])  # manifest order
        self.assertEqual(values["PLUGINS_ALL"], "OFF")
        on = sorted(name for name, value in values.items() if value == "ON")
        self.assertEqual(on, sorted(check_recipe.ALLOWED_ON))
        for name in ("PLUGIN_HACKRF_SDR_SUPPORT", "PLUGIN_RTLSDR_SDR_SUPPORT", "PLUGIN_REMOTE_SDR_SUPPORT",
                     "PLUGIN_SPYSERVER_SUPPORT", "PLUGIN_PORTAUDIO_SINK", "PLUGIN_AAUDIO_SINK", "PLUGIN_INMARSAT",
                     "PLUGIN_WEBHOOK_APP", "PLUGIN_EXPERIMENTAL_DEVICES_SUPPORT", "PLUGIN_SIMD_NEON", "BUILD_GUI",
                     "ENABLE_CRASHDUMP", "BUILD_OPENCL", "BUILD_ZIQ"):
            self.assertEqual(values[name], "OFF", name)
        # Default-ON options upstream (plugins/CMakeLists.txt at 1aedd60) are each switched off by name.
        defaults_on = {o["name"] for o in self.options["options"] if o["default"] == "ON"}
        self.assertIn("PLUGIN_HACKRF_SDR_SUPPORT", defaults_on)
        self.assertEqual({n for n in defaults_on if values[n] == "ON"}, {"PLUGIN_NET_SOURCE_SDR_SUPPORT", "BUILD_OPENMP", "ENABLE_INSTALL"})
        # The builder's own completeness rule: every declared option is set, and nothing undeclared.
        self.assertEqual(set(values) & set(self.recipe["cmake"]["variables"]), set())

    def test_drift_and_tampering_are_findings(self):
        def changed(edit, target="recipe"):
            data = copy.deepcopy(self.recipe if target == "recipe" else self.packaging)
            edit(data)
            return data
        cases = [
            (changed(lambda r: r["cmake"]["options"].pop("PLUGIN_LIMESDR_SDR_SUPPORT")), "option_not_set:PLUGIN_LIMESDR_SDR_SUPPORT"),
            (changed(lambda r: r["cmake"]["options"].update(PLUGIN_GOES="ON")), "on_set_not_allowlist"),
            (changed(lambda r: r["cmake"]["options"].update(PLUGIN_METEOR_LRPT="OFF")), "unknown_option:PLUGIN_METEOR_LRPT"),
            (changed(lambda r: r["source"]["patches"][2].update(sha256="0" * 64)), "patch_digest:patches/0003-lab-udp-loopback.patch"),
            (changed(lambda r: r["build"].append(["cmake", "--build", "https://example.invalid/x"])), "build_network"),
            (changed(lambda r: r["cmake"]["variables"].update(CMAKE_INSTALL_RPATH="$ORIGIN")), "fixed_variable:CMAKE_INSTALL_RPATH"),
            (changed(lambda r: r["build_depends"].append("libarmadillo-dev")), "build_depends_forbidden:libarmadillo-dev"),
            (changed(lambda r: r["build_depends"].remove("ninja-build")), "build_depends_changed"),
            (changed(lambda r: r["ci"].update(heavy=False)), "recipe_ci"),
            (changed(lambda r: r["checks"].pop(0)), "require_paths_differ_from_packaging"),
            (changed(lambda r: r["packages"][0].update(shlibs_depends=False)), "recipe_package"),
            (changed(lambda r: r["hooks"].update(package=None)), "recipe_hooks"),
            (changed(lambda r: r["cmake"].update(configure=["cmake", "-S", "{src}", "-B", "{build}"])), "recipe_steps"),
        ]
        for recipe, finding in cases:
            with self.subTest(finding=finding):
                self.assertIn(finding, self.findings(recipe=recipe))
        packaging = changed(lambda p: p["builder_checks"][0].update(status="CI_PASS"), "packaging")
        self.assertIn("builder_checks", self.findings(packaging=packaging))
        packaging = changed(lambda p: p["upstream_files"].update({"src-core/core/cli/pipeline.cpp": "0" * 40}), "packaging")
        self.assertIn("patch_target_blob:src-core/core/cli/pipeline.cpp", self.findings(packaging=packaging))
        policy = check_recipe.strict_json((HERE / "receive-only-policy.json").read_text(encoding="utf-8"))
        policy["components"]["satdump"]["allow_plugins"].append("goes")
        self.assertIn("plugins_differ_from_policy", self.findings(policy=policy))
        # Every committed data file is pinned by this script, which the build record binds.
        with patch.dict(check_recipe.DATA_SHA256, {"packaging.json": "0" * 64}):
            self.assertIn("data_file_digest:packaging.json", check_recipe.check())
            with self.assertRaisesRegex(check_recipe.RecipeError, "data_file_digest:packaging.json"):
                check_recipe.load("packaging.json")

    def test_data_files_are_the_pinned_ones(self):
        for name, digest in check_recipe.DATA_SHA256.items():
            self.assertEqual(hashlib.sha256((RECIPE / name).read_bytes()).hexdigest(), digest, name)
        self.assertEqual(set(self.packaging), check_recipe.PACKAGING_KEYS)
        self.assertEqual({c["id"]: c["status"] for c in self.packaging["builder_checks"]}, check_recipe.BUILDER_CHECKS)

    def test_plugin_files_are_named_after_the_upstream_directory(self):
        # PLUGIN_FY2 builds plugins/fengyun2_support (add_library(fengyun2_support SHARED) at 1aedd60): the
        # expected file names come from the manifest's subdirectory, never from the option name.
        manifest = {o["name"]: o for o in self.options["options"]}
        values = self.recipe["cmake"]["options"]
        libraries = {"lib" + manifest[n]["subdirectory"].rsplit("/", 1)[-1] + ".so"
                     for n, value in values.items() if value == "ON" and n.startswith("PLUGIN_")}
        install = self.packaging["install"]
        self.assertEqual(set(install["expected_plugins"]), libraries)
        self.assertIn("libfengyun2_support.so", libraries)
        self.assertNotIn("libfy2_support.so", libraries)
        # decoder_policy's installation record and selftest RX-04 name exactly the same files.
        self.assertEqual({decoder_policy._plugin_file(n) for n in decoder_policy.SATDUMP_PLUGINS}, libraries)
        policy = selftest.load_policy(HERE / "receive-only-policy.json")["components"]["satdump"]
        self.assertEqual({selftest._plugin_name(lib, ("_sdr_support", "_support")) for lib in libraries},
                         set(policy["allow_plugins"]))
        self.assertEqual(set(policy["allow_plugins"]), set(decoder_policy.SATDUMP_PLUGINS))
        for name in check_recipe.on_plugin_libraries(self.recipe, self.options):
            self.assertIn(manifest[name]["subdirectory"] + "/CMakeLists.txt", self.packaging["upstream_files"])
        old = copy.deepcopy(self.packaging)
        old["install"]["expected_plugins"] = [p.replace("fengyun2", "fy2") for p in old["install"]["expected_plugins"]]
        self.assertIn("expected_plugins_differ_from_options", self.findings(packaging=old))

    def test_installation_layout_is_decoder_policy_s(self):
        install = self.packaging["install"]
        self.assertEqual("/" + install["executable"], satdump_pass.SATDUMP)
        self.assertEqual("/" + install["core_library"], decoder_policy.SATDUMP_CORE)
        self.assertEqual("/" + install["plugin_dir"], decoder_policy.SATDUMP_PLUGIN_DIR)
        self.assertEqual("/" + install["pipeline_dir"], decoder_policy.SATDUMP_PIPELINE_DIR)
        self.assertEqual("/" + install["resources_dir"], decoder_policy.SATDUMP_RESOURCES)
        self.assertEqual("/" + install["config"], decoder_policy.SATDUMP_CONFIG)
        self.assertEqual(tuple(install["keep_pipelines"]), decoder_policy.SATDUMP_PIPELINE_FILES)
        self.assertEqual(self.packaging["package"]["version"], decoder_policy.SATDUMP_VERSION)
        self.assertEqual(self.packaging["source"]["commit"], decoder_policy.SATDUMP_COMMIT)
        self.assertEqual(self.recipe["cmake"]["variables"]["CMAKE_INSTALL_RPATH"], "/" + install["plugin_dir"])  # STACK.md:142
        paths = {tuple(item["path"]): item["value"] for item in install["config_set"]}
        self.assertEqual(paths[("kepler_settings", "url_template")], "")
        self.assertEqual(paths[("satdump_general", "tle_space_track_login", "value")], "")
        self.assertEqual(paths[("satdump_general", "kepler_update_interval", "value")], "Never")
        # One package; its require_paths checks name each allowlisted file once.
        self.assertEqual([p["name"] for p in self.recipe["packages"]], ["satdump"])
        required = [c["globs"][0] for c in self.recipe["checks"] if c["kind"] == "require_paths"]
        self.assertEqual(required, check_recipe.required_paths(self.packaging))
        forbid = next(c for c in self.recipe["checks"] if c["kind"] == "forbid_needed")
        self.assertIn("libarmadillo*", forbid["needed"])
        self.assertIn("libzstd*", forbid["needed"])

    def test_patches_target_the_pinned_files(self):
        loopback = (RECIPE / "patches/0003-lab-udp-loopback.patch").read_text(encoding="utf-8")
        self.assertIn("-            sock_addr.sin_addr.s_addr = INADDR_ANY;", loopback)
        self.assertIn("+            sock_addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);", loopback)
        self.assertNotIn("+            sock_addr.sin_addr.s_addr = INADDR_ANY", loopback)
        native = (RECIPE / "patches/0004-lab-no-march-native.patch").read_text(encoding="utf-8")
        self.assertIn("-if((NOT DEFINED ENV{CI}) AND NOT DEFINED ANDROID)", native)
        self.assertIn("+if(FALSE)", native)
        self.assertNotIn("+        set(CMAKE_CXX_FLAGS", native)
        iers = (RECIPE / "patches/0005-lab-no-iers-download.patch").read_text(encoding="utf-8")
        added = [line for line in iers.splitlines() if line.startswith("+") and not line.startswith("+++")]
        self.assertEqual([line for line in added if not line.lstrip("+ ").startswith("//")], ["+        return;", "+"])
        listed = self.recipe["source"]["patches"]
        self.assertEqual([p["file"] for p in listed], ["patches/0001-cli-add-option-c0b6f88.patch", "patches/0002-clock-recovery-free-6b5957f.patch",
                                                       "patches/0003-lab-udp-loopback.patch", "patches/0004-lab-no-march-native.patch",
                                                       "patches/0005-lab-no-iers-download.patch"])
        self.assertEqual([p["kind"] for p in listed], ["cherry-pick", "cherry-pick", "lab", "lab", "lab"])
        with patch.object(build_recipe, "DEPLOYMENT", HERE):
            self.assertEqual(len(build_recipe._patches(listed, "satdump")), 5)
        clock = {"src-core/dsp/clock_recovery/clock_recovery_gardner.cpp", "src-core/dsp/clock_recovery/clock_recovery_mm.cpp",
                 "src-core/dsp/clock_recovery/clock_recovery_mm_fast.cpp"}
        for entry in listed:
            for target, blob in entry["targets"].items():
                if target not in clock:
                    self.assertEqual(self.packaging["upstream_files"][target], blob, target)

    def test_cmake_option_parser(self):
        text = ('option(A "x" ON)\n# option(B "commented" ON)\noption(\n  C\n  "multi (line)"\n  OFF)\n'
                'option(D "no default")\nif(A) # OR PLUGINS_ALL)\n')
        self.assertEqual(check_recipe.parse_cmake_options(text), [("A", "ON"), ("C", "OFF"), ("D", "OFF")])

    def test_json_comment_stripper_keeps_strings(self):
        text = '{"url": "http://x//y", /* block */ "a": 1, // line\n "b": "/* not */"}'
        self.assertEqual(check_recipe.strict_json(check_recipe.strip_json_comments(text)),
                         {"url": "http://x//y", "a": 1, "b": "/* not */"})


class SourceAndPackageTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="srrx-satdump-recipe-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.recipe, self.packaging = check_recipe.load("recipe.json"), check_recipe.load("packaging.json")

    def test_verify_source_reports_missing_or_changed_upstream_files(self):
        tree = self.root / "src"
        (tree / "plugins").mkdir(parents=True)
        (tree / "CMakeLists.txt").write_text('option(BUILD_GUI "Build the GUI" ON)\n')
        findings = check_recipe.verify_source(tree)
        self.assertIn("upstream_file:CMakeLists.txt", findings)
        self.assertIn("upstream_file:src-core/db/kepler/kepler_utils.cpp", findings)
        self.assertIn("options_manifest_drift", findings)
        self.assertIn("patch_base:src-core/common/net/udp.h", findings)
        self.assertIn("patch_base:src-core/db/iers/iers_handler.cpp", findings)
        self.assertIn("plugin_library_name:plugins/fengyun2_support", findings)
        self.assertIn("cache_string_default:EXTERNAL_PLUGINS", findings)

    def test_verify_source_checks_each_plugin_library_name_and_the_external_plugins_default(self):
        tree = self.root / "src"
        options = check_recipe.load("upstream-options.json")
        manifest = {o["name"]: o for o in options["options"]}
        for name in check_recipe.on_plugin_libraries(self.recipe, options):
            directory = manifest[name]["subdirectory"]
            target = directory.rsplit("/", 1)[-1]
            (tree / directory).mkdir(parents=True)
            # The upstream text of plugins/fengyun2_support/CMakeLists.txt at 1aedd60, per directory.
            (tree / directory / "CMakeLists.txt").write_text(
                "project(%s)\nadd_library(%s SHARED ${CPPS})\n# set_target_properties(OUTPUT_NAME x)\n"
                "install(TARGETS %s\n        DESTINATION ${CMAKE_INSTALL_LIBDIR}/satdump/plugins)\n" % (target, target, target))
        names = lambda: {f for f in check_recipe.verify_source(tree) if f.startswith("plugin_library_name:")}  # noqa: E731
        self.assertEqual(names(), set())
        (tree / "plugins/fengyun2_support/CMakeLists.txt").write_text(
            "add_library(fy2_support SHARED x.cpp)\ninstall(TARGETS fy2_support DESTINATION ${CMAKE_INSTALL_LIBDIR}/satdump/plugins)\n")
        self.assertEqual(names(), {"plugin_library_name:plugins/fengyun2_support"})
        (tree / "plugins/fengyun2_support/CMakeLists.txt").write_text(
            "add_library(fengyun2_support SHARED x.cpp)\nset_target_properties(fengyun2_support PROPERTIES OUTPUT_NAME fy2)\n"
            "install(TARGETS fengyun2_support DESTINATION ${CMAKE_INSTALL_LIBDIR}/satdump/plugins)\n")
        self.assertEqual(names(), {"plugin_library_name:plugins/fengyun2_support"})
        default = lambda: "cache_string_default:EXTERNAL_PLUGINS" in check_recipe.verify_source(tree)  # noqa: E731
        (tree / "plugins/CMakeLists.txt").write_text('set(EXTERNAL_PLUGINS "" CACHE STRING "Optional external plugins")\n')
        self.assertFalse(default())
        (tree / "plugins/CMakeLists.txt").write_text('set(EXTERNAL_PLUGINS "x" CACHE STRING "Optional external plugins")\n')
        self.assertTrue(default())

    def stage(self):
        root = self.root / "stage"
        install = self.packaging["install"]
        pipelines = root / install["pipeline_dir"]
        pipelines.mkdir(parents=True)
        for name in install["keep_pipelines"]:
            body = {"x_" + name.lower().replace(".json", ""): {"name": name, "work": {"baseband": {}}}}
            if name == "Elektro_Arktika.json":
                body.update({"elektro_ggak": {"name": "GGAK"}, "elektro_ggak_mqtt": {"mqtt": {"module": "ggak_to_mqtt"}}})
            (pipelines / name).write_text("// upstream comment\n" + json.dumps(body, indent=1))
        (pipelines / "Syracuse.json").write_text('{"syracuse3_tlm": {}}')
        (pipelines / "common.json.inc").write_text("{}")
        (pipelines / "nested").mkdir()
        (pipelines / "nested/DMSP.json").write_text("{}")
        (root / install["resources_dir"] / "lut").mkdir(parents=True)
        (root / install["resources_dir"] / "lut" / "msu_mr.png").write_bytes(b"lut")
        config = root / install["config"]
        # The network keys of upstream satdump_cfg.json at 1aedd60 (lines 249-260 and 344-349).
        config.write_text('{\n // UI\n "satdump_general": {"kepler_update_interval": {"value": "1 day"},\n'
                          '  "tle_space_track_login": {"value": "yourloginemail"}, "tle_space_track_password": {"value": "yourpassword"}},\n'
                          ' "kepler_settings": {"urls_to_fetch": ["http://orbicentral.net/gp.php?GROUP=active&FORMAT=omm"],'
                          ' "url_template": "http://orbicentral.net/gp.php?CATNR=%NORAD%&FORMAT=omm", "norads_to_fetch": [25544]}\n}\n')
        plugins = root / install["plugin_dir"]
        plugins.mkdir(parents=True)
        for name in install["expected_plugins"]:
            (plugins / name).write_bytes(b"\x7fELF")
        (root / "usr/bin").mkdir(parents=True)
        (root / install["executable"]).write_bytes(b"\x7fELF")
        (root / install["core_library"]).write_bytes(b"\x7fELF core")
        (root / "usr/include/satdump").mkdir(parents=True)
        (root / "usr/include/satdump/x.h").write_text("")
        (root / "usr/share/applications").mkdir(parents=True)
        (root / "usr/share/applications/satdump.desktop").write_text("[Desktop Entry]\n")
        return root

    def test_package_keeps_five_pipelines_and_writes_a_never_config(self):
        root = self.stage()
        files = check_recipe.package(root)
        install = self.packaging["install"]
        pipelines = root / install["pipeline_dir"]
        self.assertEqual(sorted(p.name for p in pipelines.iterdir()), sorted(install["keep_pipelines"]))
        elektro = json.loads((pipelines / "Elektro_Arktika.json").read_text())
        self.assertNotIn("elektro_ggak_mqtt", elektro)
        self.assertIn("elektro_ggak", elektro)
        text = (root / install["config"]).read_text()
        config = json.loads(text)
        self.assertEqual(config["satdump_general"]["kepler_update_interval"]["value"], "Never")
        self.assertEqual((config["kepler_settings"]["urls_to_fetch"], config["kepler_settings"]["norads_to_fetch"]), ([], []))
        self.assertEqual(config["kepler_settings"]["url_template"], "")
        self.assertEqual(config["satdump_general"]["tle_space_track_login"]["value"], "")
        self.assertNotIn("://", text)
        self.assertFalse((root / "usr/include").exists())
        self.assertFalse((root / "usr/share/applications").exists())
        self.assertIn("usr/lib/satdump/plugins/libnet_source_support.so", files)
        self.assertIn("usr/lib/satdump/plugins/libfengyun2_support.so", files)
        # The builder's checks and file assignment after the hook: every staged file in the one package.
        checks = [c for c in self.recipe["checks"] if c["kind"] != "forbid_needed"]  # readelf: builder only
        self.assertTrue(all(r["status"] == "CI_PASS" for r in build_recipe.run_checks(dict(self.recipe, checks=checks), root)))
        self.assertEqual(sorted(build_recipe.assign(self.recipe, root)["satdump"]), sorted(files))
        # The record digests decoder_policy re-checks: one tree digest algorithm on both sides.
        digests = check_recipe.record_digests(root, files)
        self.assertEqual(digests["resources_sha256"],
                         decoder_policy.satdump_tree_digest(root / install["resources_dir"], admin=False))
        self.assertEqual(digests["core_sha256"], hashlib.sha256(b"\x7fELF core").hexdigest())
        self.assertEqual(digests["recipe_sha256"], hashlib.sha256((RECIPE / "recipe.json").read_bytes()).hexdigest())
        self.assertEqual(set(digests["plugins"]), set(install["expected_plugins"]))
        self.assertEqual(set(digests) | {"v", "tool_id", "version", "source_commit", "executable", "evidence_id"},
                         decoder_policy._SATDUMP_FIELDS)
        self.assertEqual(digests["resources_sha256"], runtime_check.tree_digest(root / install["resources_dir"]))

    def test_package_hook_writes_record_digests_and_a_template_decoder_policy_refuses(self):
        root = self.stage()
        out = self.root / "package-hook.json"
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            code = check_recipe.main(["package", "--root", str(root), "--manifest", str(out)])
        self.assertEqual((code, json.loads(stdout.getvalue().splitlines()[-1])), (0, {"command": "package", "findings": [], "ok": True}))
        output = build_recipe.hook_output(out)  # what the builder copies into the record
        template = output["installation_template"]
        self.assertEqual(set(template), decoder_policy._SATDUMP_FIELDS)
        self.assertEqual({k: template[k] for k in output["record_digests"]}, output["record_digests"])
        self.assertEqual((template["version"], template["source_commit"], template["executable"]),
                         (decoder_policy.SATDUMP_VERSION, decoder_policy.SATDUMP_COMMIT, satdump_pass.SATDUMP))
        self.assertLessEqual(len(json.dumps(template).encode()), 8192)  # load_satdump_installation's size bound
        with self.assertRaisesRegex(decoder_policy.DecoderRefused, "INSTALLATION_VERSION_OR_PROVENANCE_UNVERIFIED"):
            decoder_policy._validate_satdump_installation(template)  # the placeholder is never accepted as it is
        self.assertFalse(decoder_policy._EVIDENCE.fullmatch(check_recipe.TEMPLATE_EVIDENCE))
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(check_recipe.main(["package", "--root", str(root), "--manifest", str(out)]), 2)  # never overwrites
        with patch.dict(check_recipe.DATA_SHA256, {"upstream-options.json": "0" * 64}), patch("sys.stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(check_recipe.main(["package", "--root", str(root)]), 2)
        self.assertIn("data_file_digest:upstream-options.json", stdout.getvalue())

    def test_package_refuses_a_url_left_in_the_config(self):
        root = self.stage()
        config = root / self.packaging["install"]["config"]
        document = json.loads(check_recipe.strip_json_comments(config.read_text()))
        document["kepler_settings"]["mirror"] = "https://example.invalid/omm"  # a key no config_set step blanks
        config.write_text(json.dumps(document))
        with self.assertRaisesRegex(check_recipe.RecipeError, "config_url_left"):
            check_recipe.package(root)

    def test_package_refuses_an_extra_plugin_or_a_link(self):
        root = self.stage()
        (root / self.packaging["install"]["plugin_dir"] / "libhackrf_sdr_support.so").write_bytes(b"\x7fELF")
        with self.assertRaisesRegex(check_recipe.RecipeError, "plugin_set_not_allowlist"):
            check_recipe.package(root)
        if hasattr(os, "symlink") and os.name == "posix":
            shutil.rmtree(root)
            root = self.stage()
            link = root / self.packaging["install"]["pipeline_dir"] / "Link.json"
            os.symlink("/etc/passwd", link)
            with self.assertRaisesRegex(check_recipe.RecipeError, "symlink_in_stage"):
                check_recipe.package(root)

    def test_forbid_paths_catch_what_the_hook_must_have_removed(self):
        root = self.stage()
        check_recipe.package(root)
        forbid = next(c for c in self.recipe["checks"] if c["kind"] == "forbid_paths")
        for relative in ("usr/lib/satdump/plugins/libhackrf_sdr_support.so", "usr/lib/satdump/plugins/libportaudio_sink.so",
                         "usr/lib/satdump/plugins/libsimd_neon.so", "usr/lib/satdump/plugins/x/libmeteor_support.so",
                         "usr/share/satdump/resources/pipelines/common.json.inc", "usr/include/satdump/x.h"):
            with self.subTest(relative):
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                (root / relative).write_bytes(b"x")
                with self.assertRaisesRegex(build_recipe.RecipeError, "forbid_paths failed"):
                    build_recipe.run_checks({"checks": [forbid]}, root)
                (root / relative).unlink()


class RuntimeCheckTests(unittest.TestCase):
    """deployment/recipes/satdump/runtime_check.py: its constants and its strace parser."""

    def setUp(self):
        self.packaging = check_recipe.load("packaging.json")
        self.recipe = check_recipe.load("recipe.json")

    def test_constants_are_the_recipe_s_and_satdump_pass_s(self):
        install = self.packaging["install"]
        self.assertEqual(runtime_check.SATDUMP, "/" + install["executable"])
        self.assertEqual(runtime_check.CORE, "/" + install["core_library"])
        self.assertEqual(runtime_check.PLUGIN_DIR, "/" + install["plugin_dir"])
        self.assertEqual(runtime_check.PIPELINE_DIR, "/" + install["pipeline_dir"])
        self.assertEqual(runtime_check.RESOURCES, "/" + install["resources_dir"])
        self.assertEqual(runtime_check.CONFIG, "/" + install["config"])
        self.assertEqual(runtime_check.EXPECTED_PLUGINS, tuple(install["expected_plugins"]))
        self.assertEqual(runtime_check.PIPELINES, tuple(install["keep_pipelines"]))
        self.assertEqual(runtime_check.RUNPATH, self.recipe["cmake"]["variables"]["CMAKE_INSTALL_RPATH"])
        self.assertEqual(runtime_check.SAMPLERATE, baseband.OUTPUT_RATE_HZ)
        self.assertIn(runtime_check.PIPELINE, baseband.PIPELINES.values())
        self.assertEqual(tuple(m.encode() for m in runtime_check.PROBE_MARKERS), satdump_pass.PROBE_MARKERS)
        self.assertEqual(satdump_pass.probe_argv(satdump_pass.SATDUMP, runtime_check.PIPELINE),
                         [runtime_check.SATDUMP, "pipeline", runtime_check.PIPELINE, "--help"])
        self.assertEqual(satdump_pass.decode_argv(satdump_pass.SATDUMP, runtime_check.PIPELINE, "/in", "/out")[6:],
                         ["--samplerate=%d" % runtime_check.SAMPLERATE, "--baseband_format=cs16"])
        rows = dict({n: "RUNTIME_CHECK" for n in runtime_check.RUN_ROWS}, **{n: r["status"] for n, r in runtime_check.STATIC_ROWS.items()})
        self.assertEqual(rows, check_recipe.BUILDER_CHECKS)
        self.assertEqual(sorted(self.recipe["ci"]["runtime_depends"]), ["binutils", "strace"])  # strace, readelf

    def test_the_unit_shape_it_emulates_is_the_decode_template_s(self):
        # The unit-shaped runs use an empty working directory and a private empty HOME, as the template does.
        lines = satdump_pass.unit_lines("decode")
        self.assertIn("WorkingDirectory=" + satdump_pass.EMPTY_WORKDIR, lines)
        self.assertIn("RuntimeDirectory=srrx-satdump-%i", lines)
        self.assertIn("Environment=HOME=/run/srrx-satdump-%i", lines)
        self.assertIn("Environment=LC_ALL=C.UTF-8", lines)
        self.assertIn("PrivateNetwork=yes", lines)
        self.assertIn("RestrictAddressFamilies=AF_UNIX", lines)

    def test_trace_parser_joins_resumed_calls_and_flags_network_use(self):
        trace = "\n".join([
            '101 openat(AT_FDCWD, "/usr/lib/satdump/plugins/libmeteor_support.so", O_RDONLY|O_CLOEXEC) = 3',
            '101 openat(AT_FDCWD, "/usr/lib/satdump/plugins/libjemalloc.so.2", O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)',
            '102 openat(AT_FDCWD, "pipelines.json", O_RDONLY <unfinished ...>',
            '101 connect(4, {sa_family=AF_UNIX, sun_path="/var/run/nscd/socket"}, 110) = -1 ENOENT (No such file or directory)',
            '102 <... openat resumed>) = 5',
            '103 socket(AF_INET, SOCK_DGRAM|SOCK_CLOEXEC|SOCK_NONBLOCK, IPPROTO_IP) = 6',
            '103 connect(6, {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("127.0.0.53")}, 16) = -1 ENETUNREACH (Network is unreachable)',
            '103 sendto(7, "x", 1, 0, {sa_family=AF_INET6, sin6_port=htons(443)}, 28) = -1 ENETUNREACH (Network is unreachable)',
            '104 bind(8, {sa_family=AF_NETLINK, nl_pid=0, nl_groups=00000000}, 12) = 0',
            '104 +++ exited with 0 +++',
            '--- SIGCHLD {si_signo=SIGCHLD} ---',
        ])
        calls = runtime_check.parse_trace(trace)
        files = runtime_check.opened(calls)
        self.assertIn(("/usr/lib/satdump/plugins/libmeteor_support.so", 3), files)
        self.assertIn(("/usr/lib/satdump/plugins/libjemalloc.so.2", -1), files)
        self.assertIn(("pipelines.json", 5), files)
        findings, sockets = runtime_check.network(calls)
        self.assertEqual(findings, ["connect AF_INET", "sendto AF_INET6"])
        self.assertEqual(sockets, ["AF_INET"])

    def test_tree_digest_is_check_recipe_s(self):
        with tempfile.TemporaryDirectory(prefix="srrx-satdump-digest-") as temporary:
            top = Path(temporary)
            (top / "a/b").mkdir(parents=True)
            (top / "a/b/c.lut").write_bytes(b"lut")
            (top / "z.json").write_text("{}")
            self.assertEqual(runtime_check.tree_digest(top), check_recipe.tree_digest(top))


class OmmCsvReaderTests(unittest.TestCase):
    """omm-csv: srrx.orbits.satdump_csv against the reader of the pinned tree (check_recipe.OMM_CSV_READER,
    ccsdsOmmToKepler in src-core/db/kepler/kepler_utils.cpp; its blob is in packaging.json upstream_files,
    so the builder's verify-source hook refuses another reader)."""

    EPOCH = "2026-10-20T06:00:00.123456"

    def record(self, norad=90010, **changes):
        value = {"OBJECT_NAME": "SYNTHETIC LEO %d" % norad, "OBJECT_ID": "2026-901A", "EPOCH": self.EPOCH,
                 "MEAN_MOTION": 14.2412, "ECCENTRICITY": 0.00071, "INCLINATION": 98.71, "RA_OF_ASC_NODE": 120.5,
                 "ARG_OF_PERICENTER": 87.25, "MEAN_ANOMALY": 272.9, "EPHEMERIS_TYPE": 0, "CLASSIFICATION_TYPE": "U",
                 "NORAD_CAT_ID": norad, "ELEMENT_SET_NO": 999, "REV_AT_EPOCH": 1234, "BSTAR": 0.00012,
                 "MEAN_MOTION_DOT": 1.2e-06, "MEAN_MOTION_DDOT": 0.0}
        value.update(changes)
        targets = orbits.allowlist({"schema_version": 1, "kind": "srrx_orbit_allowlist",
                                    "targets": [{"norad_id": norad, "name": "ALIAS", "role": "LRPT"}]})
        with tempfile.TemporaryDirectory(prefix="srrx-omm-") as temporary:
            path = Path(temporary) / "omm.json"
            path.write_text(json.dumps([value]), encoding="ascii")
            return orbits.load_omm(path, allow_norad=targets, now_utc_s=orbits.epoch_unix_s(self.EPOCH) + 3600, utc_verified=True)

    @staticmethod
    def reader(line):
        """ccsdsOmmToKepler: split on ",", exactly 17 fields, sscanf of the epoch, std::stod of each number read."""
        reader = check_recipe.OMM_CSV_READER
        fields = line.split(reader["separator"])
        if len(fields) != reader["fields"]:
            return None
        values = {}
        try:
            for index, name in enumerate(reader["columns"]):
                if name in ("OBJECT_NAME", "OBJECT_ID"):
                    values[name] = fields[index]
                elif name == "EPOCH":
                    values[name] = re.match(r"(\d{1,4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d+(?:\.\d*)?)", fields[index])
                elif name is not None:
                    values[name] = float(fields[index].strip())
        except ValueError:
            return None
        return values

    def test_columns_are_the_reader_order(self):
        reader = check_recipe.OMM_CSV_READER
        self.assertEqual((reader["fields"], len(reader["columns"]), len(orbits.OMM_FIELDS)), (17, 17, 17))
        for index, name in enumerate(reader["columns"]):
            if name is not None:
                self.assertEqual(orbits.OMM_FIELDS[index], name, index)
        self.assertEqual([orbits.OMM_FIELDS[i] for i, n in enumerate(reader["columns"]) if n is None],
                         ["EPHEMERIS_TYPE", "CLASSIFICATION_TYPE"])  # written, not read
        self.assertIn(reader["file"], check_recipe.load("packaging.json")["upstream_files"])

    def test_export_rows_parse_as_the_pinned_reader_reads_them(self):
        records = self.record(BSTAR=-1.5e-05, MEAN_MOTION_DDOT=0.0)
        lines = orbits.satdump_csv(records).decode("ascii").split("\n")
        self.assertEqual(lines[-1], "")  # "\n" line ends: std::getline leaves no "\r"
        header, row = lines[0], lines[1]
        self.assertIsNone(self.reader(header))  # std::stod("MEAN_MOTION") throws: the header line is skipped
        values = self.reader(row)
        elements = records[0]["elements"]
        self.assertIsNotNone(values)
        self.assertTrue(values["EPOCH"])
        for name in ("MEAN_MOTION", "ECCENTRICITY", "INCLINATION", "RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY",
                     "NORAD_CAT_ID", "ELEMENT_SET_NO", "REV_AT_EPOCH", "BSTAR", "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT"):
            self.assertEqual(values[name], float(elements[name]), name)
        self.assertEqual((values["OBJECT_NAME"], values["OBJECT_ID"]), (elements["OBJECT_NAME"], elements["OBJECT_ID"]))

    def test_a_comma_in_object_name_is_a_row_the_reader_drops(self):
        # srrx.orbits accepts any printable OBJECT_NAME; csv quotes a comma and the pinned reader (no
        # quoting) then counts 18 fields and drops the row. Recorded as an OPEN finding of omm-csv.
        records = self.record(OBJECT_NAME="SYNTHETIC, LEO")
        row = orbits.satdump_csv(records).decode("ascii").split("\n")[1]
        self.assertEqual(next(csv.reader([row]))[0], "SYNTHETIC, LEO")
        self.assertIsNone(self.reader(row))


if __name__ == "__main__":
    unittest.main()
