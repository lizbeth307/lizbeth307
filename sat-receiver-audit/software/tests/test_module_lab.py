"""Module-lab verdict and coverage accounting, plus its power/MCU regression checks; no hardware PASS."""
import ast
import contextlib
import hashlib
import importlib.util
from io import StringIO
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

PROJECT = Path(__file__).resolve().parents[2]
LAB = PROJECT / "deployment" / "module_lab"
POSIX = os.name == "posix"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Lab modules import their siblings by flat name; keep that out of later tests.
with mock.patch.object(sys, "path", [str(LAB)] + sys.path):
    import io_scenarios as io_lab
    import mcu_scenarios
    from mcu_bus import load_firmware
lab_run = _load("srrx_module_lab_run_under_test", LAB / "run.py")


def _io_run(**tasks):
    """io_scenarios.run() with each named task replaced by a stub."""
    patches = [mock.patch.object(io_lab, name, side_effect=value) for name, value in tasks.items()]
    for patch in patches:
        patch.start()
    try:
        return io_lab.run(PROJECT)
    finally:
        for patch in patches:
            patch.stop()


def _io_main(report):
    """Exit code of the io CLI for a given report."""
    with tempfile.TemporaryDirectory() as folder, mock.patch.object(io_lab, "run", return_value=report), \
            contextlib.redirect_stdout(StringIO()):
        return io_lab.main(["--output", str(Path(folder) / "io.json")])


def _passing(identifier, refs):
    return lambda *args: [io_lab.record(identifier, refs, "PRODUCTION_SOFTWARE_ON_TEMP_FILESYSTEM", "PASS", {})]


class IOVerdictTests(unittest.TestCase):
    def tasks(self, **override):
        tasks = {"inventory_scenarios": _passing("IO-USB-TOPOLOGY", io_lab.REFS["hub"]),
                 "storage_scenarios": _passing("IO-T7-METADATA-PERSISTENCE", io_lab.REFS["t7"]),
                 "guarded_storage_scenarios": _passing("IO-T7-GUARDED-METADATA", io_lab.REFS["t7"]),
                 "qt_scenarios": _passing("IO-QT-TOUCH-MOUSE-MENU", io_lab.REFS["touch"])}
        tasks.update(override)
        return tasks

    def test_all_tasks_passing_is_emulation_pass(self):
        report = _io_run(**self.tasks())
        self.assertEqual((report["execution_status"], report["status"]), ("PASS", "EMULATION_PASS_WITH_UNSUPPORTED"))

    def test_missing_pyside6_is_unavailable_not_pass(self):
        missing = ModuleNotFoundError("No module named 'PySide6'", name="PySide6")
        report = _io_run(**self.tasks(qt_scenarios=missing))
        self.assertEqual((report["execution_status"], report["status"]), ("UNAVAILABLE", "UNAVAILABLE"))
        self.assertFalse(lab_run.success(report["status"]))
        qt = next(m for m in report["modules"] if m["id"] == "IO-QT-SCENARIOS")
        self.assertEqual((qt["status"], qt["coverage_level"]), ("UNAVAILABLE", "MISSING_DEPENDENCY"))
        self.assertEqual(_io_main(report), 2)

    def test_production_import_error_fails_and_names_the_modules(self):
        broken = ImportError("cannot import name 'atomic_json' from 'srrx.labrx'")
        report = _io_run(**self.tasks(storage_scenarios=broken))
        self.assertEqual((report["execution_status"], report["status"]), ("FAIL", "FAIL"))
        failed = next(m for m in report["modules"] if m["id"] == "IO-STORAGE-SCENARIOS")
        self.assertEqual(failed["status"], "FAIL")
        self.assertEqual(failed["design_refs"], io_lab.TASK_REFS["IO-STORAGE-SCENARIOS"])
        self.assertIn("U540", lab_run.record_refs(failed))
        self.assertEqual(_io_main(report), 1)

    def test_qt_import_error_other_than_pyside6_fails(self):
        report = _io_run(**self.tasks(qt_scenarios=ModuleNotFoundError("No module named 'srrx.hmi'", name="srrx.hmi")))
        self.assertEqual(report["execution_status"], "FAIL")

    def test_zero_executed_scenarios_is_not_pass(self):
        empty = lambda *args: []
        report = _io_run(inventory_scenarios=empty, storage_scenarios=empty,
                         guarded_storage_scenarios=empty, qt_scenarios=empty)
        self.assertEqual(report["execution_status"], "FAIL")

    def test_records_count_their_executed_scenario(self):
        passed = io_lab.record("IO-T7-WRITE-ERROR", io_lab.REFS["t7"], "X", "PASS", {})
        missing = io_lab.record("IO-HANTEK-DRIVER", io_lab.REFS["hantek"], "UNSUPPORTED", "UNSUPPORTED", {})
        self.assertEqual(lab_run.normalized_record("io", passed, {})["scenario_count"], 1)
        self.assertEqual(lab_run.normalized_record("io", missing, {})["scenario_count"], 0)

    def test_no_io_record_credits_switch_or_passive_receptacle(self):
        self.assertNotIn("U505", {ref for refs in io_lab.REFS.values() for ref in
                                  lab_run.record_refs({"design_refs": refs})})
        self.assertEqual(lab_run.record_refs({"design_refs": io_lab.REFS["touch"]}), {"U520"})


class CoverageTests(unittest.TestCase):
    PARTS = {"E3": [("U305", "RP2040 Pico"), ("Q306", "NFET"), ("BZ301", "CPT-1207-3TH"),
                    ("FAN301", "NoctuaNF-A4x10"), ("FAN302", "Delta BFB0305HA-C")],
             "E5": [("U510", "CH334F hub"), ("J512", "Q6A USB2"), ("U520", "Wisecoco"),
                    ("U540", "Samsung T7"), ("U505", "TPS2553DRVR"), ("J501", "LAB USB-A")]}

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.project = Path(self.folder.name)
        (self.project / "design").mkdir()
        snapshots, interfaces, refs = {}, [], []
        for sheet, parts in self.PARTS.items():
            doc = {"components": [{"ref": ref, "value": value, "pins": [{"number": "1", "net": "N_" + ref}]}
                                  for ref, value in parts]}
            path = self.project / "design" / (sheet + ".json")
            path.write_text(json.dumps(doc), encoding="utf-8")
            data = path.read_bytes()
            snapshots["design/" + sheet + ".json"] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for component in doc["components"]:
                refs.append(component["ref"])
                interfaces.append({"ref": component["ref"], "module_id": "IF-" + component["ref"],
                                   "value": component["value"], "interface_family": "test", "parent_assembly": "A",
                                   "source_status": "TEST", "pinout_gate": None, "source_description": "",
                                   "source_notes": "", "source_pins": component["pins"], "coverage_constraints": [],
                                   "pinout_status": "test"})
        self.inventory = {"source_snapshots": snapshots, "subinterfaces": interfaces, "catalogue_only_entities": [],
                          "assemblies": [{"module_id": "A", "sheet": "E3", "source_group": "all", "refs": refs,
                                          "component_count": len(refs), "coverage_constraints": []}]}

    def coverage(self, io_modules, **extra):
        mcu = [{"module": name, "status": "EMULATION_PASS", "cases": ["c"]} for name in lab_run.MCU_REFS]
        domains = {"io": {"exit_code": 0, "report": {"status": "EMULATION_PASS_WITH_UNSUPPORTED", "modules": io_modules}},
                   "mcu": {"exit_code": 0, "report": {"status": "EMULATION_PASS", "modules": mcu}}, **extra}
        result = lab_run.coverage(self.project, self.inventory, domains)
        return result, {row["ref"]: row for row in result["interfaces"]}

    def io_records(self):
        refs = io_lab.REFS
        return [io_lab.record("IO-USB-TOPOLOGY", refs["hub"], "FILESYSTEM_FIXTURE", "PASS", {}),
                io_lab.record("IO-USB-REMOVE-RECONNECT", refs["hub"] + refs["touch"] + refs["t7"],
                              "FILESYSTEM_FIXTURE", "PASS", {}),
                io_lab.record("IO-T7-METADATA-PERSISTENCE", refs["t7"], "PRODUCTION_SOFTWARE_ON_TEMP_FILESYSTEM", "PASS", {}),
                io_lab.record("IO-QT-TOUCH-MOUSE-MENU", refs["touch"], "PRODUCTION_QT_INPUT_EVENTS", "PASS", {})]

    def test_fixture_self_tests_and_unexercised_parts_are_not_credited(self):
        result, rows = self.coverage(self.io_records())
        for ref in ("U510", "J512", "J501", "U505", "BZ301", "FAN302"):
            self.assertEqual(rows[ref]["status"], "CONNECTION_MODEL_ONLY", ref)
        self.assertIn("IO-USB-TOPOLOGY", [m["id"] for m in rows["U510"]["models"]])
        for ref in ("U520", "U540", "U305", "Q306", "FAN301"):
            self.assertEqual(rows[ref]["status"], "EMULATION_PASS", ref)
        self.assertEqual(list(result["graph_sha256"]), ["design/E3.json", "design/E5.json"])

    def test_crashed_io_task_marks_its_modules_failed(self):
        crashed = io_lab.record("IO-STORAGE-SCENARIOS", io_lab.TASK_REFS["IO-STORAGE-SCENARIOS"],
                                "EXECUTED_SCENARIO", "FAIL", {})
        result, rows = self.coverage(self.io_records() + [crashed])
        self.assertEqual(rows["U540"]["status"], "EMULATION_FAIL")
        self.assertEqual(result["counts"]["EMULATION_FAIL"], 1)

    def test_unavailable_dependency_is_listed_as_a_gap(self):
        missing = io_lab.record("IO-QT-SCENARIOS", io_lab.REFS["touch"], "MISSING_DEPENDENCY", "UNAVAILABLE", {})
        result, rows = self.coverage([missing])
        self.assertEqual(rows["U520"]["status"], "CONNECTION_MODEL_ONLY")
        self.assertEqual([m["id"] for m in rows["U520"]["unmodeled_records"]], ["IO-QT-SCENARIOS"])

    def test_failed_connectivity_domain_is_not_reported_as_not_checked(self):
        result, rows = self.coverage([])
        self.assertEqual({row["connection_status"] for row in rows.values()}, {"NOT_CHECKED"})
        failed = {"exit_code": 1, "report": {"status": "CONNECTION_MODEL_FAIL", "modules": []}}
        result, rows = self.coverage([], connectivity=failed)
        self.assertEqual({row["connection_status"] for row in rows.values()}, {"FAIL"})
        crashed = {"exit_code": -1, "error": "timeout", "report": {}}
        result, rows = self.coverage([], connectivity=crashed)
        self.assertEqual({row["connection_status"] for row in rows.values()}, {"FAIL"})


class RunnerTests(unittest.TestCase):
    def test_child_pythonpath_has_no_empty_cwd_entry(self):
        project = PROJECT
        for inherited in ({}, {"PYTHONPATH": ""}, {"PYTHONPATH": "extra" + os.pathsep}):
            parts = lab_run.child_environment(project, inherited)["PYTHONPATH"].split(os.pathsep)
            self.assertNotIn("", parts, inherited)
            self.assertEqual(parts[:2], [str(project / "software"), str(project)])
        self.assertEqual(lab_run.child_environment(project, {"PYTHONPATH": "extra"})["PYTHONPATH"].split(os.pathsep)[2:],
                         ["extra"])

    def test_render_writes_utf8_with_lf_line_endings(self):
        # finalize_linux_lab compares a host render byte-for-byte with the guest one.
        report = {"execution_status": "FAIL", "domains": {},
                  "coverage": {"component_count": 1, "assembly_count": 1, "interfaces": [], "counts": {},
                               "catalogue_only_entities": [{"name": "Каталог", "interface": "x", "scope": "y"}]}}
        with tempfile.TemporaryDirectory() as folder:
            lab_run.render(report, Path(folder))
            for name in ("MODULE-RESULTS.md", "module-results.html"):
                data = (Path(folder) / name).read_bytes()
                self.assertNotIn(b"\r\n", data)
                self.assertIn("Каталог", data.decode("utf-8"))

    @staticmethod
    def untyped_text_io(source):
        """Line numbers of text-mode file I/O calls that do not name an encoding."""
        missing = []
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
            owner = getattr(getattr(func, "value", None), "id", None)
            if name == "open" and owner == "os":
                continue  # os.open() is a raw descriptor, not text I/O.
            # Positional mode: open(file, mode)/io.open(file, mode), but Path.open(mode)/NamedTemporaryFile(mode).
            index = 1 if name == "open" and (isinstance(func, ast.Name) or owner == "io") else 0
            keywords = {k.arg: k.value for k in node.keywords}
            default = ast.Constant("w+b" if name == "NamedTemporaryFile" else "r")
            mode = keywords.get("mode", node.args[index] if len(node.args) > index else default)
            binary = isinstance(mode, ast.Constant) and "b" in str(mode.value)
            if (name in ("read_text", "write_text") or name in ("open", "NamedTemporaryFile") and not binary) \
                    and "encoding" not in keywords:
                missing.append(node.lineno)
        return missing

    def test_text_io_guard_reads_the_mode_argument(self):
        self.assertEqual(self.untyped_text_io("\n".join((
            "open(p, 'rb')", "open('b.txt')", "open(p, mode='wb')", "open(p, 'w', encoding='utf-8')",
            "io.open(p, 'rb')", "Path(p).open('wb')", "p.open()", "p.open('w')", "os.open(p, flags)",
            "NamedTemporaryFile()", "NamedTemporaryFile('w')", "tempfile.NamedTemporaryFile(mode='w', encoding='utf-8')",
            "p.read_text()", "p.write_text(s, encoding='utf-8')", "open(p, m)"))), [2, 7, 8, 11, 13, 15])

    def test_lab_text_io_names_its_encoding(self):
        missing = ["%s:%d" % (path.name, line) for path in sorted(LAB.glob("*.py"))
                   for line in self.untyped_text_io(path.read_text(encoding="utf-8"))]
        self.assertEqual(missing, [])


@unittest.skipUnless(POSIX, "srrx.hardware/srrx.link need POSIX fcntl/termios")
class PowerScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with mock.patch.object(sys, "path", [str(LAB)] + sys.path):
            import power_scenarios
        cls.lab = power_scenarios

    def run_cases(self):
        report = self.lab.run(PROJECT)
        return report, {case["id"]: case for case in report["cases"]}

    def test_suite_passes_and_self_test_is_not_credited(self):
        report, cases = self.run_cases()
        self.assertEqual(report["status"], "EMULATION_PASS",
                         [(c["id"], c.get("error")) for c in cases.values() if c["status"] != "EMULATION_PASS"])
        self.assertEqual(cases["emulator_adapter_address_separation_self_test"]["module_ids"], [])
        self.assertNotIn("emulator_adapter_address_separation_self_test",
                         [ident for module in report["modules"] for ident in module["case_ids"]])

    def test_extra_energized_output_is_detected(self):
        import srrx.hardware as driver
        original = driver.LinuxHardware.apply_outputs

        def crosstalk(hardware, values):
            values = dict(values)
            if values.get("EN_LNA1"):
                values["EN_LNB"] = True  # Antenna LNA enable also raises 13.2 V LNB bias.
            return original(hardware, values)
        with mock.patch.object(driver.LinuxHardware, "apply_outputs", crosstalk):
            report, cases = self.run_cases()
        self.assertEqual(cases["all_mapped_outputs_register_pin_roundtrip"]["status"], "EMULATION_FAIL")
        self.assertIn("EN_LNB", cases["all_mapped_outputs_register_pin_roundtrip"]["error"])

    def test_swapped_lna_channel_labels_are_detected(self):
        import srrx.telemetry as telemetry
        original = telemetry.SRRXTelemetry.__init__

        def swapped(reader, transport, clock_ms=telemetry.monotonic_ms):
            original(reader, transport, clock_ms)
            reader.monitors = (reader.monitors[0], telemetry.INA3221(transport, 0x41, (0.2, 0.2, 0.2),
                               ("lna1", "lna3", "lna2"), clock_ms), reader.monitors[2])
        with mock.patch.object(telemetry.SRRXTelemetry, "__init__", swapped):
            report, cases = self.run_cases()
        for name in ("monitor_connect_id_config_conversion_decode", "signed_charge_and_six_branch_channels"):
            self.assertEqual(cases[name]["status"], "EMULATION_FAIL", name)

    def test_lost_flt_glitch_capture_is_detected(self):
        import srrx.hardware as driver
        original = driver.LinuxHardware.read_inputs

        def lossy(hardware):
            # Regression model: FLT_ inputs report only the present GPIO level.
            values, bus = original(hardware), hardware._transport.endpoint.bus
            return {net: bus.pin_level(net) if net.startswith("FLT_") else high for net, high in values.items()}
        with mock.patch.object(driver.LinuxHardware, "read_inputs", lossy):
            report, cases = self.run_cases()
        self.assertEqual(cases["mcp_short_fault_and_stale_intcap"]["status"], "EMULATION_FAIL")
        self.assertIn("FLT_", cases["mcp_short_fault_and_stale_intcap"]["error"])

    def test_production_i2c_router_is_exercised(self):
        from srrx.runtime_telemetry import ProjectTelemetry

        def misrouted(bridge, address, register, count):
            return bridge.hardware.read(address, register, count)  # INA228 sent to I2C2.
        with mock.patch.object(ProjectTelemetry, "read", misrouted):
            report, cases = self.run_cases()
        self.assertEqual(cases["monitor_connect_id_config_conversion_decode"]["status"], "EMULATION_FAIL")


class MCUScenarioTests(unittest.TestCase):
    def test_suite_passes_with_firmware_watchdog_case(self):
        report = mcu_scenarios.run(PROJECT)
        cases = {case["case"]: case for case in report["cases"]}
        self.assertEqual(report["status"], "EMULATION_PASS",
                         [(c["case"], c.get("error")) for c in cases.values() if c["status"] != "EMULATION_PASS"])
        self.assertEqual(cases["pico_main_watchdog_feed_policy"]["details"]["stall_1000ms_reset"], "WDT")
        self.assertNotIn("watchdog_pad_reset_ms", cases["pico_watchdog_ticks_uart"]["details"])

    def test_firmware_watchdog_regressions_fail(self):
        fw = load_firmware(PROJECT)
        source = (PROJECT / "firmware/pico/main.py").read_text(encoding="utf-8")
        poll = "            hmi.poll(now)\n"
        for old, new, reason in (("machine.WDT(timeout=1000)", "machine.WDT(timeout=2000)", "WDT timeout"),
                                 ("machine.WDT(timeout=1000)", "machine.WDT(timeout=900)", "WDT timeout"),
                                 ("            wdt.feed()", "            pass", "feed its WDT"),
                                 # Fail-safe finally loops on sleep_ms(50); a changed or missing
                                 # loop sleep never reaches the stall. All must fail, not hang.
                                 (poll, poll + "            if now > 500: raise RuntimeError('loop regression')\n",
                                  "RuntimeError: loop regression; fail-safe entered"),
                                 ("        decoder = FrameDecoder()\n",
                                  "        decoder = FrameDecoder()\n        raise RuntimeError('startup regression')\n",
                                  "RuntimeError: startup regression; fail-safe entered"),
                                 ("            time.sleep_ms(20)", "            time.sleep_ms(25)", "budget exhausted"),
                                 ("            time.sleep_ms(20)", "            pass", "budget exhausted")):
            self.assertEqual(source.count(old), 1, old)
            module = ModuleType("pico_main_mutant")
            exec(compile(source.replace(old, new), "main.py", "exec"), module.__dict__)
            mutant = SimpleNamespace(**dict(vars(fw), main=module))
            started = time.monotonic()
            with fw.activate(), self.assertRaises(AssertionError, msg=new) as raised:
                mcu_scenarios.pico_main_watchdog_feed_policy(mutant)
            self.assertIn(reason, str(raised.exception), new)
            self.assertLess(time.monotonic() - started, 10, new)

    def test_power_key_regressions_fail(self):
        fw = load_firmware(PROJECT)
        source = (PROJECT / "firmware/pico/supervisor.py").read_text(encoding="utf-8")
        for old, new, reason in (("KEY_PULSE_MS = 900", "KEY_PULSE_MS = 1100", "STACK D3 bounds"),
                                 ("KEY_WAIT_MS = 1500", "KEY_WAIT_MS = 0", "STACK D3 bounds"),
                                 ("        if self.key_pulses >= KEY_MAX_PULSES:\n", "        if False:\n",
                                  "unbounded or mistimed")):
            self.assertEqual(source.count(old), 1, old)
            module = ModuleType("pico_supervisor_mutant")
            exec(compile(source.replace(old, new), "supervisor.py", "exec"), module.__dict__)
            mutant = SimpleNamespace(**dict(vars(fw), supervisor=module))
            with fw.activate(), self.assertRaises(AssertionError, msg=new) as raised:
                mcu_scenarios.pico_q6a_power_key_pulse(mutant)
            self.assertIn(reason, str(raised.exception), new)

    def test_only_exercised_parts_are_mapped(self):
        self.assertEqual(lab_run.record_refs({"module": "pico_gpio_supervisor"}), {"U305", "Q306"})
        self.assertEqual(lab_run.record_refs({"module": "pico_fan_tach"}), {"U305", "FAN301"})


if __name__ == "__main__":
    unittest.main()
