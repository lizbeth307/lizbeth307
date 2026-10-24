"""SatDump +lab recipe (deployment/recipes/satdump): structure, option completeness, packaging steps.

Offline only: the pinned source is not in Git, so verify-source runs here on a synthetic tree;
on the package builder it runs on the extracted archive (recipe.json "build"). PENDING_BUILDER
stays the recipe status until an arm64 build and the builder checks have run.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
RECIPE = HERE / "recipes/satdump"
spec = importlib.util.spec_from_file_location("check_recipe", RECIPE / "check_recipe.py")
check_recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_recipe)


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
        config = root / install["config"]
        config.write_text('{\n // UI\n "satdump_general": {"kepler_update_interval": {"value": "1 day"}},\n'
                          ' "kepler_settings": {"urls_to_fetch": ["http://orbicentral.net/gp.php?GROUP=active&FORMAT=omm"],'
                          ' "norads_to_fetch": [25544], "url_template": "x"}\n}\n')
        plugins = root / install["plugin_dir"]
        plugins.mkdir(parents=True)
        for name in install["expected_plugins"]:
            (plugins / name).write_bytes(b"\x7fELF")
        (root / "usr/bin").mkdir(parents=True)
        (root / install["executable"]).write_bytes(b"\x7fELF")
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
        config = json.loads((root / install["config"]).read_text())
        self.assertEqual(config["satdump_general"]["kepler_update_interval"]["value"], "Never")
        self.assertEqual((config["kepler_settings"]["urls_to_fetch"], config["kepler_settings"]["norads_to_fetch"]), ([], []))
        self.assertFalse((root / "usr/include").exists())
        self.assertIn("usr/lib/satdump/plugins/libnet_source_support.so", files)

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
