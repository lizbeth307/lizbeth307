"""srrx.lab_shell_menu: schema, the capability matrix with and without the Lime and the T7, and the
names it shares with the repository (STACK.md:884). Pure data: no Qt, no rootfs, no labd; RX-11 on a
staged root is tested in deployment/tests/test_selftest.py (LabShellMenuRowTests)."""
import copy
import json
from pathlib import Path
import re
import sys
import unittest

from srrx import decoder_policy, lab_shell_menu as shell, menu_model, satdump_pass

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "deployment"))
import selftest  # noqa: E402  (labd's operations, parsed from engine.py as RX-11 does)

POLICY = json.loads((PROJECT / "deployment/receive-only-policy.json").read_text(encoding="utf-8"))
ACCEPTED = "FILE_PRESET_ACCEPTED_INTERFACE_PROBE_REQUIRED_AT_RUN"
LIME_LEAVES = {"satellites.hrpt", "satellites.metop_aws", "satellites.elektro", "satellites.fy2h",
               "spectrum.survey_classes", "system.lime_power"}
T7_LEAVES = {"signals_ai.dataset_export", "recordings.t7"}
CRITICAL = {"home.tiles", "home.stop", "home.back", "home.encoders", "home.lock"}


def leaf(leaf_id):
    return next(item for item in shell.LEAVES if item["id"] == leaf_id)


def everything(lime=True, t7=True):
    """Every package, unit, module, labd operation and preset the model names, all presets accepted."""
    names = shell.referenced()
    return shell.capabilities(lime=lime, t7=t7, packages=shell.PACKAGES, units=names["units"], modules=names["modules"],
                              ops=selftest._labd_operations(), presets={p: ACCEPTED for p in decoder_policy.availability()},
                              policy=shell.policy_lists(POLICY))


class SchemaTests(unittest.TestCase):
    def test_model_validates_and_hubs_follow_stack_884(self):
        shell.validate()
        line = (PROJECT / "STACK.md").read_text(encoding="utf-8").splitlines()[883]
        self.assertIn("Верхні хаби меню", line)
        positions = [line.find(hub["label"] + (" (" if hub["label"] not in ("Sondes", "Radio Astronomy", "Signals AI") else ";"))
                     for hub in shell.HUBS]
        self.assertNotIn(-1, positions, positions)
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(shell.HUBS), 12)
        hubs = {item["hub"] for item in shell.LEAVES}
        self.assertEqual(hubs, {hub["id"] for hub in shell.HUBS} | {shell.HOME})
        self.assertEqual(len({item["id"] for item in shell.LEAVES}), len(shell.LEAVES))

    def test_schema_defects_are_refused(self):
        good = shell.LEAVES[1]
        cases = {
            "unknown hub": dict(good, hub="radio", id="radio.x"),
            "prefix of another hub": dict(good, id="hf.stop"),
            "unknown planned feature": dict(good, backend={"kind": "page_only", "name": "planned.no_such_feature"}),
            "unknown backend kind": dict(good, backend={"kind": "transmit", "name": "x"}),
            "unit backend without program": dict(good, backend={"kind": "engine_unit", "name": "x.service"}),
            "unknown package": dict(good, requires=dict(good["requires"], packages=("hackrf",))),
            "requires a non-service unit": dict(good, requires=dict(good["requires"], units=("srrx.socket",))),
            "requires a list": dict(good, requires=dict(good["requires"], modules=["spectrum"])),
            "unknown allowlist component": dict(good, allowlist={"component": "gqrx", "name": "x"}),
            "unknown hidden reason": dict(good, hidden_reason="not_today"),
            "unknown key": dict(good, controls={"touch": True, "keys": ("PTT",)}),
            "no control": dict(good, controls={"touch": False, "keys": ()}),
            "flag not boolean": dict(good, needs_lime=1),
            "extra field": dict(good, colour="red"),
        }
        for name, bad in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(shell.LabShellMenuError):
                    shell.validate(leaves=shell.LEAVES[:1] + (bad,))
        with self.assertRaises(shell.LabShellMenuError):
            shell.validate(leaves=shell.LEAVES + shell.LEAVES[:1])  # duplicate id
        with self.assertRaises(shell.LabShellMenuError):
            shell.validate(hubs=shell.HUBS + ({"id": "home", "label": "Home"},))
        with self.assertRaises(shell.LabShellMenuError):
            shell.validate(leaves=())

    def test_critical_leaves_have_keys_and_stop_is_the_lock_hold(self):
        self.assertEqual({item["id"] for item in shell.LEAVES if item["critical"]}, CRITICAL)
        for item in shell.LEAVES:
            if item["critical"]:
                self.assertTrue(item["controls"]["keys"], item["id"])
        stop = leaf("home.stop")
        self.assertEqual((stop["backend"], stop["controls"]["keys"]), ({"kind": "labd_op", "name": "disarm"}, (menu_model.HOLD_STOP["key"],)))
        self.assertEqual(menu_model.HOLD_STOP, {"key": "LOCK", "hold_ms": 1000})


class CapabilityMatrixTests(unittest.TestCase):
    def test_lime_and_t7_leaves_declare_their_fallback(self):
        self.assertEqual({item["id"] for item in shell.LEAVES if item["needs_lime"]}, LIME_LEAVES)
        self.assertEqual({item["id"] for item in shell.LEAVES if item["needs_t7"]}, T7_LEAVES)
        for item in shell.LEAVES:
            if item["needs_lime"] or item["needs_t7"]:
                self.assertTrue(item["fallback_text"], item["id"])
        self.assertEqual(leaf("system.lime_power")["fallback_text"], menu_model.NO_LIME)
        self.assertEqual(leaf("recordings.t7")["fallback_text"], menu_model.NO_T7)

    def test_matrix_with_and_without_lime_and_t7(self):
        full = {item["id"]: shell.hide_reasons(item, everything()) for item in shell.LEAVES}
        for lime in (False, True):
            for t7 in (False, True):
                caps = everything(lime, t7)
                with self.subTest(lime=lime, t7=t7):
                    for item in shell.LEAVES:
                        reasons = shell.hide_reasons(item, caps)
                        self.assertEqual("no_lime" in reasons, item["needs_lime"] and not lime, item["id"])
                        self.assertEqual("no_t7" in reasons, item["needs_t7"] and not t7, item["id"])
                        # Apart from the Lime and the T7 the verdict does not depend on them.
                        self.assertEqual(tuple(r for r in reasons if r not in ("no_lime", "no_t7")), full[item["id"]], item["id"])
                    visible = {item["id"] for item in shell.visible_leaves(caps)}
                    self.assertFalse({i for i in LIME_LEAVES if not lime} & visible)
                    self.assertFalse({i for i in T7_LEAVES if not t7} & visible)
                    hidden = dict(shell.hidden_leaves(caps))
                    self.assertEqual(set(hidden) | visible, {item["id"] for item in shell.LEAVES})
                    self.assertFalse(set(hidden) & visible)
        # With everything installed only standing decisions, planned backends, the OpenWebRX+ deferral
        # and the policy's deny list hide a leaf.
        for leaf_id, reasons in full.items():
            for reason in reasons:
                self.assertTrue(reason.startswith(("hidden:", "planned:", "package_deferred:", "package_unbuilt:", "denied:")),
                                (leaf_id, reason))
        visible = {item["id"] for item in shell.visible_leaves(everything())}
        self.assertEqual(visible - {item["id"] for item in shell.visible_leaves(everything(lime=False))}, {"system.lime_power"})
        self.assertEqual(visible - {item["id"] for item in shell.visible_leaves(everything(t7=False))}, {"signals_ai.dataset_export"})

    def test_nothing_installed_hides_every_leaf_with_a_reason(self):
        caps = shell.capabilities()
        self.assertEqual(shell.visible_leaves(caps), ())
        hidden = dict(shell.hidden_leaves(caps))
        self.assertEqual(set(hidden), {item["id"] for item in shell.LEAVES})
        self.assertTrue(all(hidden.values()))
        self.assertIn("labd_op_missing:disarm", hidden["home.stop"])
        self.assertIn("module_missing:spectrum", hidden["spectrum.survey"])
        self.assertIn("unit_missing:srrx-lease-readsb@.service", hidden["air_sea.adsb"])
        self.assertIn("preset:adsb-public=MISSING", hidden["air_sea.adsb"])

    def test_named_reasons_of_stack_884(self):
        real = dict(everything(), presets=decoder_policy.availability())
        hidden = dict(shell.hidden_leaves(real))
        self.assertIn("package_deferred:openwebrx", hidden["hf.wefax"])  # WEFAX -> fax in OpenWebRX+, deferred
        self.assertIn("preset:egc-safetynet=DISABLED_NO_VERIFIED_HEADER_PARSER_AND_TEST_VECTORS", hidden["satellites.safetynet"])
        self.assertIn("denied:sdrangel:demoddsc", hidden["hf.dsc"])  # DSC only with a patched demoddsc
        self.assertIn("hidden:bluetooth_off_permanently", hidden["system.bluetooth"])
        self.assertIn("preset:satdump-weather=UNAVAILABLE_NO_ACCEPTED_INSTALLATION", hidden["satellites.lrpt"])
        accepted = dict(real, presets=dict(real["presets"], **{"satdump-weather": "LRPT_FILE_PRESET_ACCEPTED_INTERFACE_PROBE_REQUIRED_AT_RUN"}))
        self.assertNotIn("satellites.lrpt", dict(shell.hidden_leaves(accepted)))
        self.assertFalse(shell.preset_accepted("UNAVAILABLE_INSTALLATION_NOT_QUALIFIED"))
        self.assertTrue(shell.preset_accepted(ACCEPTED))
        # A package is present only with every executable; a missing one names the package.
        caps = dict(everything(), packages=frozenset(shell.PACKAGES) - {"sdrangelsrv"})
        self.assertEqual(shell.hide_reasons(leaf("hf.navtex"), caps), ("package_missing:sdrangelsrv",))
        caps = dict(everything(), units=frozenset())
        self.assertEqual(shell.hide_reasons(leaf("hf.navtex"), caps), ("unit_missing:srrx-lease-sdrangelsrv@.service",))


class RepositoryNamesTests(unittest.TestCase):
    def test_every_backend_and_requirement_is_built_here_or_planned(self):
        operations, presets = selftest._labd_operations(), decoder_policy.availability()
        used = set()
        for item in shell.LEAVES:
            backend, name = item["backend"], item["backend"]["name"]
            with self.subTest(leaf=item["id"]):
                if name.startswith(shell.PLANNED_PREFIX):
                    used.add(name[len(shell.PLANNED_PREFIX):])
                elif backend["kind"] == "labd_op":
                    self.assertIn(name, operations)
                elif backend["kind"] == "page_only":
                    self.assertTrue((PROJECT / "software/srrx" / (name + ".py")).is_file())
                elif backend["kind"] == "decoder_preset":
                    self.assertIn(name, presets)
                for module in item["requires"]["modules"]:
                    self.assertTrue((PROJECT / "software/srrx" / (module + ".py")).is_file(), module)
                for unit in item["requires"]["units"]:
                    self.assertTrue((PROJECT / "software/systemd" / unit).is_file(), unit)
                for preset in item["requires"]["presets"]:
                    self.assertIn(preset, presets)
        self.assertEqual(used, set(shell.PLANNED))  # no stale PLANNED entry
        self.assertTrue(all(text.strip() for text in shell.PLANNED.values()))
        self.assertEqual({item["hidden_reason"] for item in shell.LEAVES} - {None}, set(shell.HIDDEN_REASONS))
        self.assertNotIn("transmit", operations)

    def test_packages_name_the_lock_the_policy_and_the_lease_units(self):
        lock = {c["id"] for c in json.loads((PROJECT / "deployment/sources.lock.json").read_text(encoding="utf-8"))["components"]}
        recipes = {p.parent.name for p in (PROJECT / "deployment/recipes").glob("*/recipe.json")}
        for name, package in shell.PACKAGES.items():
            with self.subTest(package=name):
                self.assertTrue(package["lock"] is None or package["lock"] in lock, package)
                if not package["binaries"]:  # nothing to detect while no recipe builds it
                    self.assertNotIn(package["lock"], recipes)
        self.assertEqual(shell.PACKAGES["dream"]["binaries"], tuple(POLICY["dream"]["binary_names"]))
        self.assertEqual(shell.PACKAGES["satdump"]["binaries"], (satdump_pass.SATDUMP.rsplit("/", 1)[1],))
        self.assertIn("usr/bin/" + shell.PACKAGES["openwebrx"]["binaries"][0], POLICY["components"]["openwebrx"]["footprint"])
        self.assertIn("jt9/wsprd", (PROJECT / "STACK.md").read_text(encoding="utf-8").splitlines()[126])
        # Every unit a leaf needs runs one executable of the leaf's packages (/usr/bin/env <binary>).
        for item in shell.LEAVES:
            for unit in item["requires"]["units"]:
                text = (PROJECT / "software/systemd" / unit).read_text(encoding="utf-8")
                words = re.search(r"^ExecStart=(.*)$", text, re.M).group(1).split()
                binaries = {b for p in item["requires"]["packages"] for b in shell.PACKAGES[p]["binaries"]}
                with self.subTest(leaf=item["id"], unit=unit):
                    self.assertEqual(words[0], "/usr/bin/env")
                    self.assertIn(words[1], binaries)

    def test_allowlist_entries_come_from_the_receive_only_policy(self):
        lists = shell.policy_lists(POLICY)
        verdicts = {item["id"]: shell.allowlist_reason(item["allowlist"], lists) for item in shell.LEAVES if item["allowlist"]}
        self.assertEqual({k: v for k, v in verdicts.items() if v}, {"hf.dsc": "denied:sdrangel:demoddsc"})
        self.assertEqual({item["allowlist"]["name"] for item in shell.LEAVES if item["allowlist"] and item["allowlist"]["component"] == "satdump"},
                         set(decoder_policy.SATDUMP_PIPELINE_FILES) - {"AWS.json"})
        policy = copy.deepcopy(POLICY)
        policy["components"]["sdrangel"]["allow_plugins"].remove("demodnavtex")
        self.assertEqual(shell.allowlist_reason(leaf("hf.navtex")["allowlist"], shell.policy_lists(policy)), "not_allowlisted:sdrangel:demodnavtex")
        policy["components"]["openwebrx"]["deny_modes"].append("f*")
        self.assertEqual(shell.allowlist_reason(leaf("hf.wefax")["allowlist"], shell.policy_lists(policy)), "denied:openwebrx:fax")


class ModelSourceTests(unittest.TestCase):
    """W2 SW-MENU review fixes: the OpenWebRX+ deferral rests on an in-repo record, an engine_unit leaf
    carries its scope and program and a unit name has one scope, the live map promises only what
    srrx.location does."""

    def test_openwebrx_deferral_rests_on_the_lock(self):
        lock = {c["id"]: c for c in json.loads((PROJECT / "deployment/sources.lock.json").read_text(encoding="utf-8"))["components"]}
        package = shell.PACKAGES["openwebrx"]
        self.assertEqual([name for name, item in shell.PACKAGES.items() if item["deferred"]], ["openwebrx"])
        self.assertTrue(package["deferred"].startswith("sources.lock.json " + package["lock"] + ":"), package)
        self.assertTrue(lock[package["lock"]]["release_blockers"])
        # While deferred: csdr, pycsdr and owrx_connector are not locked and no recipe builds OpenWebRX+.
        self.assertEqual([c for c in lock if re.fullmatch(r"(py)?csdr.*|owrx[-_]connector.*", c)], [])
        self.assertEqual(list((PROJECT / "deployment/recipes").glob("*openwebrx*")), [])
        self.assertNotIn("E2-SW-", (PROJECT / "software/srrx/lab_shell_menu.py").read_text(encoding="utf-8"))

    def test_engine_unit_leaves_carry_scope_and_program(self):
        good = shell._leaf("system.fixture_unit", "Fixture", "engine_unit", "srrx-menu.service", scope="user", program="srrx.hmi")
        self.assertEqual(good["backend"], menu_model.CONSOLE_UNIT)
        shell.validate(leaves=shell.LEAVES + (good,))
        self.assertIn("srrx-menu.service", shell.referenced(shell.LEAVES + (good,))["units"])
        cases = {
            "no scope or program": shell._leaf("system.fixture_unit", "Fixture", "engine_unit", "srrx-menu.service"),
            "unknown scope": shell._leaf("system.fixture_unit", "Fixture", "engine_unit", "srrx-menu.service", scope="session",
                                         program="srrx.hmi"),
            "required unit is a system unit": dict(good, requires=dict(good["requires"], units=("srrx-menu.service",))),
            "same unit in another scope": dict(good, id="system.fixture_lease",
                                               backend=dict(good["backend"], name="srrx-lease-sdrangelsrv@.service")),
        }
        for name, bad in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(shell.LabShellMenuError):
                    shell.validate(leaves=shell.LEAVES + (bad,))

    def test_live_map_promises_only_the_own_position(self):
        live, layers = leaf("map_point.live_map"), leaf("map_point.layers")
        self.assertEqual((live["label"], live["backend"]), ("Live map (own position)", {"kind": "page_only", "name": "location"}))
        self.assertIn("GNSS location", (PROJECT / "software/srrx/location.py").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(layers["backend"], {"kind": "page_only", "name": shell.PLANNED_PREFIX + "map_layers"})
        line = (PROJECT / "STACK.md").read_text(encoding="utf-8").splitlines()[883]
        self.assertIn("шари: власне місце, літаки, судна, зонди, траси супутників, APRS", line)


if __name__ == "__main__":
    unittest.main()
