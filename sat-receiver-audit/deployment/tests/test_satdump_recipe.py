"""SatDump +lab recipe (deployment/recipes/satdump): structure, option completeness, packaging steps.

Offline only: the pinned source is not in Git, so verify-source runs here on a synthetic tree;
on the package builder it runs on the extracted archive (recipe.json "build"). PENDING_BUILDER
stays the recipe status until an arm64 build and the builder checks have run.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
RECIPE = HERE / "recipes/satdump"
spec = importlib.util.spec_from_file_location("check_recipe", RECIPE / "check_recipe.py")
check_recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_recipe)
sys.path.insert(0, str(HERE.parent / "software"))
from srrx import decoder_policy  # noqa: E402
sys.path.insert(0, str(HERE))
import selftest  # noqa: E402


class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.recipe, self.options = check_recipe.load("recipe.json"), check_recipe.load("upstream-options.json")

    def test_committed_recipe_is_consistent(self):
        self.assertEqual(check_recipe.check(), [])
        self.assertEqual(self.recipe["status"], "PENDING_BUILDER")
        self.assertTrue(all(c["status"].startswith("PENDING") for c in self.recipe["builder_checks"]))

    def test_every_upstream_option_is_set_and_only_the_allowlist_is_on(self):
        definitions = self.recipe["cmake"]["definitions"]
        self.assertEqual(len(self.options["options"]), 105)
        self.assertEqual(definitions["PLUGINS_ALL"], "OFF")
        on = sorted(name for name, value in definitions.items() if value == "ON")
        self.assertEqual(on, sorted(check_recipe.ALLOWED_ON))
        for name in ("PLUGIN_HACKRF_SDR_SUPPORT", "PLUGIN_RTLSDR_SDR_SUPPORT", "PLUGIN_REMOTE_SDR_SUPPORT",
                     "PLUGIN_SPYSERVER_SUPPORT", "PLUGIN_PORTAUDIO_SINK", "PLUGIN_AAUDIO_SINK", "PLUGIN_INMARSAT",
                     "PLUGIN_WEBHOOK_APP", "PLUGIN_EXPERIMENTAL_DEVICES_SUPPORT", "PLUGIN_SIMD_NEON", "BUILD_GUI",
                     "ENABLE_CRASHDUMP", "BUILD_OPENCL"):
            self.assertEqual(definitions[name], "OFF", name)
        # Default-ON options upstream (plugins/CMakeLists.txt at 1aedd60) are each switched off by name.
        defaults_on = {o["name"] for o in self.options["options"] if o["default"] == "ON"}
        self.assertIn("PLUGIN_HACKRF_SDR_SUPPORT", defaults_on)
        self.assertEqual({n for n in defaults_on if definitions[n] == "ON"},
                         {"PLUGIN_NET_SOURCE_SDR_SUPPORT", "BUILD_OPENMP", "ENABLE_INSTALL"})

    def test_drift_and_tampering_are_findings(self):
        cases = []
        missing = copy.deepcopy(self.recipe)
        del missing["cmake"]["definitions"]["PLUGIN_LIMESDR_SDR_SUPPORT"]
        cases.append((missing, "option_not_set:PLUGIN_LIMESDR_SDR_SUPPORT"))
        on = copy.deepcopy(self.recipe)
        on["cmake"]["definitions"]["PLUGIN_GOES"] = "ON"
        cases.append((on, "on_set_not_allowlist"))
        typo = copy.deepcopy(self.recipe)
        typo["cmake"]["definitions"]["PLUGIN_METEOR_LRPT"] = "OFF"
        cases.append((typo, "unknown_definition:PLUGIN_METEOR_LRPT"))
        patch = copy.deepcopy(self.recipe)
        patch["patches"][2]["sha256"] = "0" * 64
        cases.append((patch, "patch_digest:patches/0003-lab-udp-loopback.patch"))
        network = copy.deepcopy(self.recipe)
        network["build"]["steps"].append("curl -O https://example.invalid/x")
        cases.append((network, "build_network"))
        claim = copy.deepcopy(self.recipe)
        claim["status"] = "BUILT"
        cases.append((claim, "status_claims_more_than_checks"))
        for recipe, finding in cases:
            with self.subTest(finding=finding):
                self.assertIn(finding, check_recipe.check(recipe, self.options))
        policy = check_recipe.strict_json((HERE / "receive-only-policy.json").read_text(encoding="utf-8"))
        policy["components"]["satdump"]["allow_plugins"].append("goes")
        self.assertIn("plugins_differ_from_policy", check_recipe.check(self.recipe, self.options, policy))

    def test_plugin_files_are_named_after_the_upstream_directory(self):
        # PLUGIN_FY2 builds plugins/fengyun2_support (add_library(fengyun2_support SHARED) at 1aedd60): the
        # expected file names come from the manifest's subdirectory, never from the option name.
        manifest = {o["name"]: o for o in self.options["options"]}
        definitions = self.recipe["cmake"]["definitions"]
        libraries = {"lib" + manifest[n]["subdirectory"].rsplit("/", 1)[-1] + ".so"
                     for n, value in definitions.items() if value == "ON" and n.startswith("PLUGIN_")}
        self.assertEqual(set(self.recipe["install"]["expected_plugins"]), libraries)
        self.assertIn("libfengyun2_support.so", libraries)
        self.assertNotIn("libfy2_support.so", libraries)
        # decoder_policy's installation record and selftest RX-04 name exactly the same files.
        self.assertEqual({decoder_policy._plugin_file(n) for n in decoder_policy.SATDUMP_PLUGINS}, libraries)
        policy = selftest.load_policy(HERE / "receive-only-policy.json")["components"]["satdump"]
        self.assertEqual({selftest._plugin_name(lib, ("_sdr_support", "_support")) for lib in libraries},
                         set(policy["allow_plugins"]))
        self.assertEqual(set(policy["allow_plugins"]), set(decoder_policy.SATDUMP_PLUGINS))
        # Every ON plugin's CMakeLists.txt is bound by blob, so verify-source checks its add_library().
        for name in check_recipe.on_plugin_libraries(self.recipe, self.options):
            self.assertIn(manifest[name]["subdirectory"] + "/CMakeLists.txt", self.recipe["upstream_files"])
        old = copy.deepcopy(self.recipe)
        old["install"]["expected_plugins"] = [p.replace("fengyun2", "fy2") for p in old["install"]["expected_plugins"]]
        self.assertIn("expected_plugins_differ_from_options", check_recipe.check(old, self.options))
        old_policy = check_recipe.strict_json((HERE / "receive-only-policy.json").read_text(encoding="utf-8"))
        old_policy["components"]["satdump"]["allow_plugins"] = [
            "fy2" if p == "fengyun2" else p for p in old_policy["components"]["satdump"]["allow_plugins"]]
        self.assertIn("plugins_differ_from_policy", check_recipe.check(self.recipe, self.options, old_policy))

    def test_rpath_and_config_steps(self):
        definitions = self.recipe["cmake"]["definitions"]
        self.assertEqual(definitions["CMAKE_INSTALL_RPATH"], "/usr/lib/satdump/plugins")  # STACK.md:142
        changed = copy.deepcopy(self.recipe)
        changed["cmake"]["definitions"]["CMAKE_INSTALL_RPATH"] = "$ORIGIN"
        self.assertIn("fixed_definition:CMAKE_INSTALL_RPATH", check_recipe.check(changed, self.options))
        paths = {tuple(item["path"]): item["value"] for item in self.recipe["install"]["config_set"]}
        self.assertEqual(paths[("kepler_settings", "url_template")], "")
        self.assertEqual(paths[("satdump_general", "tle_space_track_login", "value")], "")

    def test_patches_target_the_pinned_files_and_the_loopback_patch_removes_inaddr_any(self):
        loopback = (RECIPE / "patches/0003-lab-udp-loopback.patch").read_text(encoding="utf-8")
        self.assertIn("-            sock_addr.sin_addr.s_addr = INADDR_ANY;", loopback)
        self.assertIn("+            sock_addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);", loopback)
        self.assertNotIn("+            sock_addr.sin_addr.s_addr = INADDR_ANY", loopback)
        for entry in self.recipe["patches"]:
            self.assertEqual(set(entry["targets"]) - set(self.recipe["upstream_files"]) - {
                "src-core/dsp/clock_recovery/clock_recovery_gardner.cpp", "src-core/dsp/clock_recovery/clock_recovery_mm.cpp",
                "src-core/dsp/clock_recovery/clock_recovery_mm_fast.cpp"}, set())

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
        self.recipe = check_recipe.load("recipe.json")

    def test_verify_source_reports_missing_or_changed_upstream_files(self):
        tree = self.root / "src"
        (tree / "plugins").mkdir(parents=True)
        (tree / "CMakeLists.txt").write_text('option(BUILD_GUI "Build the GUI" ON)\n')
        findings = check_recipe.verify_source(tree)
        self.assertIn("upstream_file:CMakeLists.txt", findings)
        self.assertIn("options_manifest_drift", findings)
        self.assertIn("patch_base:src-core/common/net/udp.h", findings)
        self.assertIn("plugin_library_name:plugins/fengyun2_support", findings)

    def test_verify_source_checks_each_plugin_library_name(self):
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
        names = lambda: {f for f in check_recipe.verify_source(tree) if f.startswith("plugin_library_name:")}
        self.assertEqual(names(), set())
        (tree / "plugins/fengyun2_support/CMakeLists.txt").write_text(
            "add_library(fy2_support SHARED x.cpp)\ninstall(TARGETS fy2_support DESTINATION ${CMAKE_INSTALL_LIBDIR}/satdump/plugins)\n")
        self.assertEqual(names(), {"plugin_library_name:plugins/fengyun2_support"})
        (tree / "plugins/fengyun2_support/CMakeLists.txt").write_text(
            "add_library(fengyun2_support SHARED x.cpp)\nset_target_properties(fengyun2_support PROPERTIES OUTPUT_NAME fy2)\n"
            "install(TARGETS fengyun2_support DESTINATION ${CMAKE_INSTALL_LIBDIR}/satdump/plugins)\n")
        self.assertEqual(names(), {"plugin_library_name:plugins/fengyun2_support"})

    def stage(self):
        root = self.root / "stage"
        install = self.recipe["install"]
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
        return root

    def test_package_keeps_five_pipelines_and_writes_a_never_config(self):
        root = self.stage()
        files = check_recipe.package(root)
        install = self.recipe["install"]
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
        self.assertIn("usr/lib/satdump/plugins/libnet_source_support.so", files)
        self.assertIn("usr/lib/satdump/plugins/libfengyun2_support.so", files)
        # The record digests decoder_policy re-checks: one tree digest algorithm on both sides.
        digests = check_recipe.record_digests(root, files)
        self.assertEqual(digests["resources_sha256"],
                         decoder_policy.satdump_tree_digest(root / install["resources_dir"], admin=False))
        self.assertEqual(digests["core_sha256"], hashlib.sha256(b"\x7fELF core").hexdigest())
        self.assertEqual(digests["recipe_sha256"], hashlib.sha256((RECIPE / "recipe.json").read_bytes()).hexdigest())
        self.assertEqual(set(digests["plugins"]), set(install["expected_plugins"]))
        self.assertEqual(set(digests) | {"v", "tool_id", "version", "source_commit", "executable", "evidence_id"},
                         decoder_policy._SATDUMP_FIELDS)

    def test_package_refuses_a_url_left_in_the_config(self):
        root = self.stage()
        config = root / self.recipe["install"]["config"]
        document = json.loads(check_recipe.strip_json_comments(config.read_text()))
        document["kepler_settings"]["mirror"] = "https://example.invalid/omm"  # a key no config_set step blanks
        config.write_text(json.dumps(document))
        with self.assertRaisesRegex(check_recipe.RecipeError, "config_url_left"):
            check_recipe.package(root)

    def test_package_refuses_an_extra_plugin_or_a_link(self):
        root = self.stage()
        (root / self.recipe["install"]["plugin_dir"] / "libhackrf_sdr_support.so").write_bytes(b"\x7fELF")
        with self.assertRaisesRegex(check_recipe.RecipeError, "plugin_set_not_allowlist"):
            check_recipe.package(root)
        if hasattr(os, "symlink") and os.name == "posix":
            shutil.rmtree(root)
            root = self.stage()
            link = root / self.recipe["install"]["pipeline_dir"] / "Link.json"
            os.symlink("/etc/passwd", link)
            with self.assertRaisesRegex(check_recipe.RecipeError, "symlink_in_stage"):
                check_recipe.package(root)


if __name__ == "__main__":
    unittest.main()
