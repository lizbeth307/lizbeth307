"""Release/verification tool gates fail closed. Synthetic fixtures only, never bench evidence."""
import contextlib
import errno
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import uuid

BASE = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, BASE / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


invariants = load("srrx_tool_invariants", "tools/check_electrical_invariants.py")
kicad = load("srrx_tool_generate_kicad", "tools/generate_kicad.py")
firmware = load("srrx_tool_build_firmware", "tools/build_firmware.py")
bundle = load("srrx_tool_check_bundle", "tools/check_bundle.py")
finalize = load("srrx_tool_finalize_linux_lab", "tools/finalize_linux_lab.py")


class TempProject(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)


class ElectricalInvariantTests(TempProject):
    def setUp(self):
        super().setUp()
        (self.root / "design").mkdir()
        (self.root / "verification").mkdir()
        for path in sorted((BASE / "design").glob("E[1-5].json")):
            shutil.copyfile(path, self.root / "design" / path.name)
        self.out = self.root / "verification/electrical-invariants.json"

    def edit(self, sheet, change):
        path = self.root / "design" / (sheet + ".json")
        graph = json.loads(path.read_text(encoding="utf-8"))
        change({c["ref"]: c for c in graph["components"]}, graph)
        path.write_text(json.dumps(graph, ensure_ascii=False), encoding="utf-8")

    def assert_fails_without_report(self):
        self.out.write_text('{"status": "PASS"}\n', encoding="utf-8")  # stale earlier result
        with self.assertRaises(SystemExit):
            invariants.main(self.root)
        self.assertFalse(self.out.exists())

    def test_current_graphs_pass_and_report_binds_inputs(self):
        with contextlib.redirect_stdout(io.StringIO()):
            invariants.main(self.root)
        report = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["input_sha256"], {"design/" + p.name: sha(p) for p in sorted((self.root / "design").glob("E[1-5].json"))})

    def test_bridge_from_raw_cell_negative_to_protected_return_fails(self):
        self.edit("E1", lambda comps, graph: graph["components"].append(
            {"ref": "R9001", "kind": "resistor", "value": "0R", "pins": [{"number": "1", "net": "E1_CELL0"}, {"number": "2", "net": "GND"}]}))
        self.assert_fails_without_report()

    def test_ovp_enable_pullup_to_any_rail_fails(self):
        self.edit("E2", lambda comps, graph: graph["components"].append(
            {"ref": "R9002", "kind": "resistor", "value": "10k", "pins": [{"number": "1", "net": "OVP_LNB_N"}, {"number": "2", "net": "AON3V3"}]}))
        self.assert_fails_without_report()

    def test_ovp_enable_moved_off_the_comparator_node_fails(self):
        def move(comps, graph):
            next(p for p in comps["U212"]["pins"] if str(p["number"]) == "3")["net"] = "EN_LNB"
        self.edit("E2", move)
        self.assert_fails_without_report()

    def test_unconnected_contacts_no_longer_compare_equal(self):
        # Both PPS ends NC: None == None used to pass the PPS invariant.
        def unwire(comps, graph):
            for ref, pin in (("J301", "7"), ("U304", "P1.5")):
                for p in comps[ref]["pins"] if ref in comps else []:
                    if str(p["number"]) == pin:
                        p.pop("net", None)
                        p["nc"] = True
        for sheet in ("E1", "E2", "E3", "E4", "E5"):
            self.edit(sheet, unwire)
        self.assert_fails_without_report()

    def test_optimized_interpreter_cannot_turn_a_failure_into_pass(self):
        self.edit("E1", lambda comps, graph: graph["components"].append(
            {"ref": "R9003", "kind": "resistor", "value": "0R", "pins": [{"number": "1", "net": "E1_CELL0"}, {"number": "2", "net": "GND"}]}))
        code = "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); import check_electrical_invariants as m; m.main(Path(sys.argv[2]))"
        result = subprocess.run([sys.executable, "-B", "-O", "-c", code, str(BASE / "tools"), str(self.root)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Electrical invariant FAIL", result.stderr)
        self.assertFalse(self.out.exists())


class SchematicNoConnectTests(TempProject):
    def graph(self, pin):
        return [{"sheet": "E9", "components": [{"ref": "R1", "value": "1k", "pins": [{"number": "1", "net": "N1"}, dict(number="2", **pin)]}]}]

    def test_generator_rejects_no_connect_type_with_net(self):
        kicad.validate(self.graph({"type": "no_connect"}))
        with self.assertRaisesRegex(ValueError, "no_connect"):
            kicad.validate(self.graph({"type": "no_connect", "net": "N2"}))

    def validate_project(self, pin):
        for name in ("design", "verification", "build/kicad"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        (self.root / "design/E1.json").write_text(json.dumps(self.graph(pin)[0]), encoding="utf-8")
        (self.root / "verification/netlist.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<export version="E"><design><sheet number="1" name="/"/></design>'
            '<components><comp ref="R1"><value>1k</value></comp></components><nets>'
            '<net code="1" name="N1"><node ref="R1" pin="1"/></net><net code="2" name="N2"><node ref="R1" pin="2"/></net>'
            '</nets></export>\n', encoding="utf-8")
        (self.root / "verification/erc.json").write_text(json.dumps(
            {"sheets": [{"path": "/", "violations": []}], "ignored_checks": [{"key": "single_global_label"}]}), encoding="utf-8")
        subprocess.run([sys.executable, "-B", str(BASE / "tools/validate_project.py"), "--project", str(self.root)], capture_output=True)
        return json.loads((self.root / "verification/validation.json").read_text(encoding="utf-8"))

    def test_validator_fails_no_connect_type_with_net_and_binds_inputs(self):
        self.assertEqual(self.validate_project({"type": "no_connect"})["graph_netlist_comparison"], "PASS")
        report = self.validate_project({"type": "no_connect", "net": "N2"})
        self.assertEqual(report["graph_netlist_comparison"], "FAIL")
        self.assertTrue(any("no_connect" in e for e in report["comparison_errors"]))
        self.assertEqual(report["erc_ignored_checks"], ["single_global_label"])
        self.assertEqual({r["file"]: r["sha256"] for r in report["input_files"]},
                         {n: sha(self.root / n) for n in ("verification/erc.json", "verification/netlist.xml")})


class FirmwarePackageTests(TempProject):
    def setUp(self):
        super().setUp()
        for name, text in (("firmware/pico/main.py", "x = 1\n"), ("firmware/imu/main.py", "y = 2\n"), ("software/srrx/wire.py", "w = 3\n")):
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text(text, encoding="utf-8")
        firmware.build(self.root)

    def test_check_passes_only_for_current_sources(self):
        self.assertEqual(firmware.stale(self.root), [])
        self.assertEqual(bundle.check_firmware(self.root)["status"], "PASS")
        (self.root / "firmware/pico/supervisor.py").write_text("# interlock fix\n", encoding="utf-8")
        self.assertTrue(firmware.stale(self.root))
        with self.assertRaises(bundle.InvalidBundle):
            bundle.check_firmware(self.root)

    def test_foreign_package_in_dist_is_rejected(self):
        (self.root / "firmware/dist/old-micropython-files.zip").write_bytes(b"PK\x05\x06" + bytes(18))
        self.assertTrue(any("unexpected" in p for p in firmware.stale(self.root)))
        with self.assertRaises(bundle.InvalidBundle):
            bundle.check_firmware(self.root)

    def test_help_does_not_rebuild(self):
        before = {p.name: p.read_bytes() for p in (BASE / "firmware/dist").iterdir()}
        result = subprocess.run([sys.executable, "-B", str(BASE / "tools/build_firmware.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--check", result.stdout)
        self.assertEqual({p.name: p.read_bytes() for p in (BASE / "firmware/dist").iterdir()}, before)


class SchematicPdfBindingTests(TempProject):
    def setUp(self):
        super().setUp()
        (self.root / "build/kicad").mkdir(parents=True)
        (self.root / "verification").mkdir()
        self.sch = self.root / "build/kicad/E1.kicad_sch"
        self.sch.write_text("(kicad_sch)\n", encoding="utf-8")
        self.pdf = self.root / "build/kicad/sr-rx-v2.pdf"

    def bind(self, data):
        self.pdf.write_bytes(data)
        (self.root / "verification/pdf-export.json").write_text(json.dumps(
            {"pdf": {"file": "build/kicad/sr-rx-v2.pdf", "sha256": sha(self.pdf)},
             "kicad_sch_sha256": {"build/kicad/E1.kicad_sch": sha(self.sch)}}), encoding="utf-8")

    def test_pdf_from_older_schematics_is_rejected(self):
        self.bind(b"%PDF-1.4\n%%EOF\n")
        self.sch.write_text("(kicad_sch (edited))\n", encoding="utf-8")
        with self.assertRaisesRegex(bundle.InvalidBundle, "not bound"):
            bundle.check_pdf(self.pdf, 1, self.root)
        self.bind(b"%PDF-1.4\n%%EOF\n")
        self.pdf.write_bytes(b"%PDF-1.4\n% other export\n%%EOF\n")
        with self.assertRaisesRegex(bundle.InvalidBundle, "recorded KiCad export"):
            bundle.check_pdf(self.pdf, 1, self.root)
        (self.root / "verification/pdf-export.json").unlink()
        with self.assertRaises(OSError):
            bundle.check_pdf(self.pdf, 1, self.root)

    def test_missing_pdf_parser_is_a_failure_not_a_pass(self):
        self.bind(b"%PDF-1.4\n%%EOF\n")
        with mock.patch.dict(sys.modules, {"fitz": None}):
            with self.assertRaisesRegex(bundle.InvalidBundle, "PyMuPDF"):
                bundle.check_pdf(self.pdf, 1, self.root)

    def test_bound_current_pdf_passes(self):
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF is not installed in this environment")
        document = fitz.open()
        document.new_page()
        self.bind(document.tobytes())
        document.close()
        self.assertEqual(bundle.check_pdf(self.pdf, 1, self.root)["schematic_export_binding"], "PASS")


class LinuxLabImportTests(TempProject):
    def test_guest_symlink_or_special_file_is_rejected(self):
        results = self.root / "results"
        (results / "module-lab").mkdir(parents=True)
        (results / "summary.json").write_text("{}", encoding="utf-8")
        finalize.regular_tree(results)
        try:
            os.symlink(BASE / "README.md", results / "stolen.txt")
        except (OSError, NotImplementedError) as error:
            self.skipTest("symlinks unavailable: " + str(error))
        with self.assertRaisesRegex(SystemExit, "symlink"):
            finalize.regular_tree(results)
        (results / "stolen.txt").unlink()
        os.symlink(self.root, results / "module-lab/home", target_is_directory=True)
        with self.assertRaisesRegex(SystemExit, "symlink"):
            finalize.regular_tree(results)

    def test_binding_scope_covers_everything_the_guest_runs(self):
        for name in ("deployment/deploy.py", "deployment/build.sh", "deployment/sources.lock.json",
                     "deployment/patches/rtlsdr-rx-only.patch", "deployment/upstream-fixtures/rtl-sdr/COPYING",
                     "deployment/tests/test_deployment.py", "software/pyproject.toml", "tools/check_software.py",
                     "tools/run_tests_offline.py", "firmware/pico/supervisor.py", "software/systemd/srrx.service"):
            self.assertTrue(finalize.bound(name), name)
        for name in ("deployment/linux_lab/build_kit.py", "firmware/dist/pico-micropython-files.zip",
                     "software/srrx/__pycache__/wire.py", "design/E1-review.md", "tools/build_bundle.py"):
            self.assertFalse(finalize.bound(name), name)
        (self.root / "deployment").mkdir()
        (self.root / "deployment/new_guard.py").write_text("# added later\n", encoding="utf-8")
        (self.root / "deployment/NOTES.md").write_text("prose\n", encoding="utf-8")
        self.assertEqual(finalize.bound_sources(self.root), {"deployment/new_guard.py"})


class OfflineAttestationTests(unittest.TestCase):
    def test_socket_denial_is_probed_not_read_from_the_environment(self):
        saved = sys.path[:]
        with mock.patch.dict(os.environ):
            checker = load("srrx_tool_check_software", "tools/check_software.py")
        sys.path[:] = saved
        actual = True
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                socket.socket(family, socket.SOCK_STREAM).close()
                actual = False
            except OSError as error:
                actual = actual and error.errno == errno.EPERM
        with mock.patch.dict(os.environ, {"SRRX_TEST_INET_DENIED": "1"}):
            self.assertIs(checker.inet_denied(), actual)


class RoutedPrototypeCheckTests(TempProject):
    BOARD = "build/kicad/pcb-prototype/detector-core-routed-prototype.kicad_pcb"

    @classmethod
    def setUpClass(cls):
        saved, flag = sys.path[:], sys.dont_write_bytecode
        sys.path.insert(0, str(BASE / "verification"))
        try:
            cls.check = load("srrx_tool_pcb_prototype_check", "verification/pcb-prototype-review-check.py")
        finally:
            sys.path[:], sys.dont_write_bytecode = saved, flag

    def run_check(self, extra="", board_sha=None):
        shutil.copytree(BASE / "build/kicad/footprints", self.root / "footprints")
        (self.root / "pcb-prototype").mkdir()
        shutil.copyfile(BASE / "build/kicad/pcb-prototype/fp-lib-table", self.root / "pcb-prototype/fp-lib-table")
        text = (BASE / self.BOARD).read_text(encoding="utf-8")
        end = text.rstrip().rindex(")")
        board = self.root / "pcb-prototype" / Path(self.BOARD).name
        board.write_text(text[:end] + extra + text[end:], encoding="utf-8", newline="\n")
        drc = BASE / "build/kicad/pcb-prototype/drc-raw.json"
        review = self.root / "review.json"
        review.write_text(json.dumps({"published_board": True, "board_sha256": board_sha or sha(board),
                                      "drc": {"raw_sha256": sha(drc)}}), encoding="utf-8")
        result = self.check.compare(BASE, BASE / "pcb/generated/detector-core-input.json",
                                    BASE / "build/kicad/pcb-preparation/detector-core-placement.kicad_pcb", board, drc, review)
        return {issue["category"] for issue in result["issues"]}

    def test_committed_board_is_short_free_but_drc_of_another_board_is_refused(self):
        issues = self.run_check(board_sha="0" * 64)
        self.assertIn("DRC_board_binding", issues)
        self.assertNotIn("inter_net_copper_contact", issues)

    def test_ground_track_across_sense_track_is_a_short_despite_bound_clean_drc(self):
        short = ('\t(segment\n\t\t(start 77.3 95.8)\n\t\t(end 80.3 95.8)\n\t\t(width 0.2)\n\t\t(layer "F.Cu")\n'
                 '\t\t(net "GND")\n\t\t(uuid "%s")\n\t)\n' % uuid.uuid4())
        issues = self.run_check(short)
        self.assertIn("inter_net_copper_contact", issues)
        self.assertFalse(issues & {"DRC_board_binding", "DRC_report_binding"})


if __name__ == "__main__":
    unittest.main()
