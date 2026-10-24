"""build_bundle/finalize release gates fail closed. Synthetic reports only, never verification evidence."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

BASE = Path(__file__).resolve().parents[2]
if str(BASE / "software") not in sys.path:
    sys.path.insert(0, str(BASE / "software"))
import srrx.commissioning as commissioning


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, BASE / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bundle = load("srrx_tool_build_bundle_gates", "tools/build_bundle.py")
finalize = load("srrx_tool_finalize_gates", "tools/finalize_linux_lab.py")
GRAPHS, SOURCES = {"design/E1.json": "1" * 64}, {"software/srrx/engine.py": "2" * 64}
PROTO = "build/kicad/pcb-prototype/"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ReleaseGateTests(unittest.TestCase):
    """One consistent synthetic project passes; each stale or failed binding alone blocks packaging."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-bundle-gates-")
        self.addCleanup(self.temp.cleanup)

    def put(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if type(data) is bytes else (data if type(data) is str else json.dumps(data)).encode("utf-8"))
        return path

    def build(self, before=None, after=None):
        self.root = Path(tempfile.mkdtemp(dir=self.temp.name))
        for _, relative in bundle.CORE:
            self.put(relative, "# fixture\n")
        for sheet in ("E1", "E2", "E3", "E4", "E5"):
            self.put("design/" + sheet + ".json", {"sheet": sheet})
        self.put("design/readiness-contract.json", {"gate_results": {"E1-01": "OPEN"}})  # bound: the guest reads it
        self.put("design/E4-detector-analysis.py", "# replaced by the fake runner\n")
        for relative, text in (("deployment/deploy.py", "# bound guard\n"), ("deployment/module_lab/run.py", "# model\n"),
                               ("deployment/module_lab/inventory.json", "{}\n"), ("build/kicad/E1.kicad_sch", "(kicad_sch)\n"),
                               ("verification/erc.json", "{}\n"), ("verification/netlist.xml", "<export/>\n"),
                               ("build/kicad/pcb-preparation/board.kicad_pcb", "(kicad_pcb)\n"),
                               ("pcb/generated/input.json", "{}\n"), ("build/kicad/pcb-preparation/drc-raw.json", "{}\n"),
                               (PROTO + "detector-core-routed-prototype.kicad_pcb", "(kicad_pcb routed)\n"), (PROTO + "drc-raw.json", "{}\n")):
            self.put(relative, text)
        self.put("build/kicad/sr-rx-v2.pdf", b"%PDF-1.4\n%%EOF\n")
        self.detector = {"design_file": "design/E4.json", "worst_margin_mv": 12}
        self.firmware_code = 0
        root, models = self.root, self.root / "deployment/module_lab"
        design = {p.relative_to(root).as_posix(): sha(p) for p in sorted((root / "design").glob("E[1-5].json"))}
        schematics = {"build/kicad/E1.kicad_sch": sha(root / "build/kicad/E1.kicad_sch")}
        reports = {
            "software-tests.json": {"host_regression_status": "PASS", "graph_sha256": GRAPHS, "source_sha256": SOURCES,
                                    "test_environment": {"internet_sockets_denied": True}},
            "module-lab/report.json": {"execution_status": "PASS", "inventory_sha256": sha(models / "inventory.json"),
                                       "model_sha256": {p.name: sha(p) for p in sorted(models.glob("*.py"))},
                                       "coverage": {"graph_sha256": dict(design)}},
            "linux-lab/report.json": {"status": "PASS"},
            "validation.json": {"graph_netlist_comparison": "PASS", "erc_counts": {}, "sha256": dict(schematics),
                                "input_files": [{"file": f, "sha256": sha(root / f)} for f in ("verification/erc.json", "verification/netlist.xml")]},
            "electrical-invariants.json": {"status": "PASS", "input_sha256": dict(design)},
            "independent-netlist-review.json": {"passed": True, "netlist_sha256": sha(root / "verification/netlist.xml"),
                                                "graph_sha256": {Path(f).name: h for f, h in design.items()}},
            "dc-detector-analysis.json": dict(self.detector, design_file="elsewhere/E4.json"),
            "pcb-review.json": {"passed": True, "board_file": "build/kicad/pcb-preparation/board.kicad_pcb",
                                "board_sha256": sha(root / "build/kicad/pcb-preparation/board.kicad_pcb"),
                                "input_file": "pcb/generated/input.json", "input_sha256": sha(root / "pcb/generated/input.json"),
                                "drc": {"raw_file": "build/kicad/pcb-preparation/drc-raw.json",
                                        "raw_sha256": sha(root / "build/kicad/pcb-preparation/drc-raw.json")}},
            "pcb-prototype-review.json": {"status": "ROUTED_INTERNAL_PROTOTYPE_NOT_FOR_FABRICATION", "published_board": True,
                                          "board_sha256": sha(root / PROTO / "detector-core-routed-prototype.kicad_pcb"),
                                          "drc": {"raw_sha256": sha(root / PROTO / "drc-raw.json"), "exit_code": 0,
                                                  "sections": {"violations": 0, "unconnected_items": 0}, "ignored_checks": []},
                                          "source_pad_audit": {"passed": True}},
            "pdf-export.json": {"pdf": {"file": "build/kicad/sr-rx-v2.pdf", "sha256": sha(root / "build/kicad/sr-rx-v2.pdf")},
                                "kicad_sch_sha256": dict(schematics)}}
        if before:
            before(reports)
        for name, value in reports.items():
            self.put("verification/" + name, value)
        self.put("verification/linux-lab/source-binding.json", {
            "source_sha256": {r: sha(root / r) for r in sorted(finalize.bound_sources(root))},
            "module_report_sha256": sha(root / "verification/module-lab/report.json"),
            "linux_report_sha256": sha(root / "verification/linux-lab/report.json")})
        if after:
            after(root)

    def gates(self):
        def run(args, **kwargs):
            if "--json" in args:
                return subprocess.CompletedProcess(args, 0, json.dumps(self.detector), "")
            if Path(args[1]).name == "build_firmware.py" and args[2:] == ["--check"]:
                return subprocess.CompletedProcess(args, self.firmware_code)
            raise AssertionError("unexpected subprocess " + str(args))
        with (mock.patch.object(bundle, "subprocess", types.SimpleNamespace(run=run, CompletedProcess=subprocess.CompletedProcess)),
              mock.patch.object(commissioning, "project_hashes", lambda base: (GRAPHS, SOURCES)),
              mock.patch.dict(sys.modules, {"finalize_linux_lab": finalize})):
            return bundle.release_gates(self.root)

    def test_consistent_project_passes_every_gate(self):
        self.build()
        self.assertEqual(self.gates()["pdf"], self.root / "build/kicad/sr-rx-v2.pdf")
        self.assertNotIn("lxml", bundle.__dict__)  # the gates import no HTML/PDF renderer

    def test_each_stale_or_failed_binding_blocks_packaging(self):
        def edit(name, change):
            return lambda reports: change(reports[name])
        def touch(relative, data=b"changed\n"):
            return lambda root: (root / relative).write_bytes(data)
        cases = [
            ("Internet sockets denied", edit("software-tests.json", lambda r: r["test_environment"].update(internet_sockets_denied=False)), None),
            ("current-source software regression", edit("software-tests.json", lambda r: r.update(source_sha256={})), None),
            ("Linux and module-lab PASS", edit("module-lab/report.json", lambda r: r.update(execution_status="FAIL")), None),
            ("Linux execution result is stale", None, touch("deployment/deploy.py")),
            ("Linux execution result is stale", None, touch("design/readiness-contract.json")),
            ("does not cover current sources", None, touch("deployment/new_guard.py")),
            ("report binding changed", None, touch("verification/linux-lab/report.json", b'{"status": "PASS"} \n')),
            ("Module inventory result is stale", edit("module-lab/report.json", lambda r: r.update(inventory_sha256="0" * 64)), None),
            ("Module models changed", edit("module-lab/report.json", lambda r: r.update(model_sha256={})), None),
            ("Module graph result is stale", edit("module-lab/report.json", lambda r: r["coverage"]["graph_sha256"].update({"design/E1.json": "0" * 64})), None),
            ("ERC with no reported violations", edit("validation.json", lambda r: r.update(erc_counts={"error": 1})), None),
            ("validated schematics differ", None, touch("build/kicad/E1.kicad_sch")),
            ("current ERC/netlist", edit("validation.json", lambda r: r["input_files"].pop()), None),
            ("current ERC/netlist", None, touch("verification/netlist.xml")),
            ("Electrical invariant report", edit("electrical-invariants.json", lambda r: r["input_sha256"].update({"design/E2.json": "0" * 64})), None),
            ("Electrical invariant report", edit("electrical-invariants.json", lambda r: r.update(status="FAIL")), None),
            ("Independent netlist review", edit("independent-netlist-review.json", lambda r: r.update(netlist_sha256="0" * 64)), None),
            ("Independent netlist review", edit("independent-netlist-review.json", lambda r: r["graph_sha256"].pop("E5.json")), None),
            ("DC-detector analysis report is stale", edit("dc-detector-analysis.json", lambda r: r.update(worst_margin_mv=13)), None),
            ("PCB placement review", edit("pcb-review.json", lambda r: r.update(board_sha256="0" * 64)), None),
            ("Routed prototype review", edit("pcb-prototype-review.json", lambda r: r.update(board_sha256="0" * 64)), None),
            ("Routed prototype review", edit("pcb-prototype-review.json", lambda r: r["drc"]["sections"].update(violations=1)), None),
            ("Routed prototype review", edit("pcb-prototype-review.json", lambda r: r["drc"].update(ignored_checks=["clearance"])), None),
            ("PDF is incomplete", None, touch("build/kicad/sr-rx-v2.pdf", b"%PDF-1.4\n")),
            ("not the export of the current verified schematics", edit("pdf-export.json", lambda r: r["pdf"].update(sha256="0" * 64)), None),
            ("Missing CORE documents", None, lambda root: (root / "OPEN_ITEMS.md").unlink())]
        for message, before, after in cases:
            with self.subTest(message=message, before=before is not None):
                self.build(before, after)
                with self.assertRaises(SystemExit) as raised:
                    self.gates()
                self.assertIn(message, str(raised.exception))
        self.build()
        self.firmware_code = 1
        with self.assertRaisesRegex(SystemExit, "Firmware packages are stale"):
            self.gates()

    def test_record_of_an_earlier_run_states_its_drift_like_completion(self):
        def drift(root):
            (root / "deployment/deploy.py").write_bytes(b"# changed guard\n")
            (root / "deployment/added_guard.py").write_bytes(b"# new\n")
            (root / "verification/linux-lab/project-manifest.json").write_text('{"record_status": "RECORD_OF_EARLIER_RUN"}', encoding="utf-8")
        self.build(after=drift)
        # build_documents.lab_evidence prints the same sentence after "Після прогону".
        self.assertIn("Після нього з 4 прив’язаних виконуваних файлів змінено 1, вилучено 0; додано 1 новий файл. Його PASS",
                      self.gates()["linux_notice"])


class BundleDocumentTests(unittest.TestCase):
    def test_core_lists_each_document_once_with_the_gnss_uart_and_scope_policy_docs(self):
        paths = [p for _, p in bundle.CORE]
        self.assertEqual((len(set(paths)), len({t for t, _ in bundle.CORE})), (len(paths), len(paths)))  # unique section ids/titles
        for doc in ("software/GNSS-UART.md", "software/SCOPE-POLICY.md"):
            self.assertIn(doc, bundle.INCLUDED)
            self.assertTrue((BASE / doc).is_file(), doc)
        # Links from LOCATION.md/DEPLOYMENT.md to GNSS-UART.md now resolve to its section, not to the ZIP.
        self.assertEqual(paths.index("software/GNSS-UART.md"), paths.index("software/LOCATION.md") + 1)


class LinuxImportTests(unittest.TestCase):
    def test_readme_lineage_follows_run_json_without_a_clean_image_claim(self):
        self.assertIn("`base_overlay: null`", finalize.lineage_text(None))
        cached = {"previous_status": "FAIL", "previous_qemu_exit_code": 0,
                  "backing_chain": [{"sha256": "a" * 64}, {"sha256": "b" * 64}]}
        text = finalize.lineage_text(cached)
        for part in ("`previous_status` FAIL", "`previous_qemu_exit_code` 0", "2 шарів", "не прогін із чистого базового образу"):
            self.assertIn(part, text)
        self.assertNotIn("previous_clean_shutdown", Path(finalize.__file__).read_text(encoding="utf-8"))

    def test_unlistable_guest_directory_fails_closed_instead_of_being_skipped(self):
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary) / "results"
            (results / "module-lab").mkdir(parents=True)
            (results / "summary.json").write_text("{}", encoding="utf-8")
            finalize.regular_tree(results)
            real = os.scandir
            # debugfs re-applies guest modes: a 0311 directory is traversable but not listable.
            # Injected, so root (the guest) and Windows exercise it too; os.walk used to skip it.
            for blocked in (results / "module-lab", results):
                def scandir(path, blocked=blocked):
                    if Path(path) == blocked:
                        raise PermissionError(13, "Permission denied", str(path))
                    return real(path)
                with self.subTest(blocked=blocked.name), mock.patch.object(os, "scandir", scandir):
                    with self.assertRaisesRegex(SystemExit, "Unreadable guest results"):
                        finalize.regular_tree(results)


if __name__ == "__main__":
    unittest.main()
