"""Schematic drawing, Ukrainian wording and stale-record counts of the document tools.

Synthetic fixtures only, never bench evidence."""
import hashlib
import html as escape_html
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

BASE = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, BASE / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


kicad =load("srrx_doc_generate_kicad", "tools/generate_kicad.py")
uk = load("srrx_doc_uk_text", "tools/uk_text.py")
finalize = load("srrx_doc_finalize_linux_lab", "tools/finalize_linux_lab.py")
documents = load("srrx_doc_build_documents", "tools/build_documents.py")
packer = load("srrx_doc_build_bundle", "tools/build_bundle.py")
checker = load("srrx_doc_check_bundle", "tools/check_bundle.py")
lab_run = load("srrx_doc_module_lab_run", "deployment/module_lab/run.py")
checks = load("srrx_doc_run_checks", "tools/run_checks.py")
U = kicad.U
WORDS = ("Ревізія COUT і місця NTC/VSET/ISET не підтверджені офіційною схемою; вікно 0…45 °C та inhibit "
         "не перевірені, тому модуль не використовувати до стенду. ") * 12


class PluralTests(unittest.TestCase):
    FORMS = ("елемент", "елементи", "елементів")

    def test_form_follows_the_last_two_digits(self):
        for numbers, form in (((0, 5, 11, 12, 14, 25, 111, 750), 2), ((1, 21, 71, 2181), 0), ((2, 4, 22, 64, 123), 1)):
            for n in numbers:
                self.assertEqual(uk.plural(n, *self.FORMS), f"{n} {self.FORMS[form]}")
        self.assertEqual(uk.plural(123, "виконуваний файл", "виконувані файли", "виконуваних файлів"), "123 виконувані файли")
        self.assertEqual(uk.plural(2.5, *self.FORMS), "2.5 елементів")

    def test_every_copy_of_the_rule_agrees(self):
        # build_documents re-exports the shared helper; the guest-side module lab and the
        # independent bundle checker keep their own copies.
        for n in range(0, 2200):
            expected = uk.plural(n, *self.FORMS)
            self.assertEqual(documents.plural(n, *self.FORMS), expected)
            self.assertEqual(lab_run._plural(n, *self.FORMS), expected)
            self.assertEqual(f"{n} {checker.counted_form(n, *self.FORMS)}", expected)
        self.assertEqual(lab_run._plural(2.5, *self.FORMS), uk.plural(2.5, *self.FORMS))


class ModuleLabWordingTests(unittest.TestCase):
    def render(self, components, assemblies, interfaces):
        rows = [{"value": "M", "ref": f"U{i}", "interface_family": "I2C", "connection_status": "PASS",
                 "status": "CONNECTION_MODEL_ONLY", "pinout_gate": None, "source_status": "design"} for i in range(interfaces)]
        report = {"execution_status": "PASS", "domains": {}, "coverage": {
            "component_count": components, "assembly_count": assemblies, "interfaces": rows, "counts": {},
            "catalogue_only_entities": []}}
        with tempfile.TemporaryDirectory() as folder:
            lab_run.render(report, Path(folder))
            return ((Path(folder) / "MODULE-RESULTS.md").read_text(encoding="utf-8"),
                    (Path(folder) / "module-results.html").read_text(encoding="utf-8"))

    def test_counts_agree_with_their_numbers(self):
        text, page = self.render(750, 64, 166)
        self.assertIn("Реєстр охоплює 750 елементів, 64 вузли та 166 деталізованих інтерфейсів.", text)
        text, _ = self.render(754, 65, 161)
        self.assertIn("Реєстр охоплює 754 елементи, 65 вузлів та 161 деталізований інтерфейс.", text)
        # The interactive page counts in the browser with the same rule.
        self.assertIn("function pl(n,one,few,many)", page)
        self.assertIn("pl(row.models.length,'модель','моделі','моделей')", page)
        self.assertNotIn("' елементи · '", page)


class StaleRecordCountTests(unittest.TestCase):
    """COMPLETION.md and the bundle notice count the drift from an ARM64 run one way."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def put(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def project(self, bound=86, edited=71, deleted=0, added=52):
        for i in range(bound):
            self.put(f"deployment/m{i:03d}.py", f"# bound {i}\n")
        report = self.put("verification/module-lab/report.json", "{}\n")
        binding = {"source_sha256": {r: sha(self.root / r) for r in sorted(finalize.bound_sources(self.root))},
                   "module_report_sha256": sha(report)}
        for i in range(edited):
            self.put(f"deployment/m{i:03d}.py", f"# edited {i}\n")
        for i in range(deleted):
            (self.root / f"deployment/m{bound - 1 - i:03d}.py").unlink()
        for i in range(added):
            self.put(f"deployment/new{i:03d}.py", f"# new {i}\n")
        return binding

    def test_one_sentence_for_completion_and_the_notice(self):
        binding = self.project()
        drift = finalize.binding_drift(self.root, binding)
        self.assertEqual((drift["bound"], len(drift["changed"]), drift["missing"], len(drift["added"]), drift["module_rebound"]),
                         (86, 71, [], 52, False))
        sentence = "з 86 прив’язаних виконуваних файлів змінено 71, вилучено 0; додано 52 нові файли"
        self.assertEqual(uk.drift_sentence(drift), sentence)
        completion = documents.lab_evidence(binding, self.root)
        self.assertIn("ARM64 прогін не підтверджує поточний код", completion)
        self.assertTrue(completion.endswith(" Після прогону " + sentence + "."))
        self.assertIn("Після нього " + sentence + ". Його PASS", packer.record_notice(drift, {"environment": {"architecture": "x86_64"}}))

    def test_replaced_module_report_and_deleted_files_are_counted(self):
        binding = self.project(bound=3, edited=0, deleted=1, added=0)
        self.put("verification/module-lab/report.json", '{"rerun": true}\n')
        self.assertEqual(uk.drift_sentence(finalize.binding_drift(self.root, binding)),
                         "з 3 прив’язаних виконуваних файлів змінено 0, вилучено 1; додано 0 нових файлів; звіт модулів замінено після прив’язки")

    def test_current_tree_has_no_drift_sentence(self):
        binding = self.project(bound=21, edited=0, added=0)
        self.assertEqual(uk.drift_sentence(finalize.binding_drift(self.root, binding)), "")
        self.assertEqual(documents.lab_evidence(binding, self.root), "")
        self.assertIn("не перевірено", documents.lab_evidence({}, self.root))


class BundleTextTests(unittest.TestCase):
    def setUp(self):
        from lxml import html
        self.html = html

    def page(self, completion, notice=""):
        return self.html.fromstring(f'<html><body><main>{notice}<section id="file-COMPLETION-md"><p>{completion}</p></section>'
                                    '<section id="schematics"><details><summary>DC_CORE: 71 компонент</summary></details></section>'
                                    '<section id="downloads"><p>У ZIP 1204 файли.</p></section></main></body></html>')

    def test_autolinked_text_loses_its_mailto_link(self):
        fragment = self.html.fragment_fromstring('<p>mode <a href="mailto:1920x1080@59.986Hz">1920x1080@59.986Hz</a>, '
                                                 '<a href="https://x.org">https://x.org</a></p>', create_parent="div")
        packer.strip_bare_mailto(fragment)
        self.assertEqual(fragment.xpath('.//a/@href'), ["https://x.org"])
        self.assertEqual(fragment.text_content(), "mode 1920x1080@59.986Hz, https://x.org")
        authored = self.html.fragment_fromstring('<p><a href="mailto:a@b.c">write</a></p>', create_parent="div")
        self.assertEqual(packer.strip_bare_mailto(authored).xpath('.//a/@href'), ["mailto:a@b.c"])

    def test_checker_rejects_any_mailto_link(self):
        with self.assertRaisesRegex(checker.InvalidBundle, "e-mail"):
            checker.check_document(self.html.fromstring('<div><a href="mailto:5V@1.2A">5V@1.2A</a></div>'))
        self.assertEqual(checker.check_document(self.html.fromstring('<div><a href="https://x.org">x</a></div>'))["internal_links"], 0)

    def test_notice_and_completion_must_count_alike(self):
        drift = {"bound": 86, "changed": ["a"] * 71, "missing": [], "added": ["b"] * 52, "module_rebound": False}
        notice = packer.record_notice(drift, {"environment": {"architecture": "x86_64"}})
        stale = escape_html.escape(documents.evidence_note(False, "ARM64 прогін") + " Після прогону " + uk.drift_sentence(drift) + ".")
        self.assertEqual(checker.check_generated_text(self.page(stale, notice))["arm64_record"], "RECORD_OF_EARLIER_RUN")
        self.assertEqual(checker.check_generated_text(self.page("ARM64 прогін PASS."))["arm64_record"], "CURRENT")
        other = dict(drift, added=["b"] * 53)
        with self.assertRaisesRegex(checker.InvalidBundle, "differently"):
            checker.check_generated_text(self.page(stale, packer.record_notice(other, {})))
        with self.assertRaisesRegex(checker.InvalidBundle, "no notice"):
            checker.check_generated_text(self.page(stale))

    def test_glued_numbers_and_disagreeing_counts_are_rejected(self):
        for text, message in (("Повний C++ data plane56MS/s/Lime.", "Missing space"), ("ОС Ubuntu24.04.", "Missing space"),
                              ("71 компонент,187 контактів", "Missing space"), ("Реєстр: 750 елементи.", "disagree"),
                              ("1 помилок", "disagree")):
            with self.subTest(text=text), self.assertRaisesRegex(checker.InvalidBundle, message):
                checker.check_generated_text(self.page(text))
        checker.check_generated_text(self.page("750 елементів, 64 вузли, 0,5 V, K1=1,K2=1, 2181 підключений контакт."))


# The bundle tools parse HTML with lxml, which the host jobs install (PY_PINS: lxml 6.1.3)
# and run these tests with. The ARM64 guest runs software/tests too, but its locked
# wheelhouse has no lxml and guest_bootstrap.sh accepts only two documented skip reasons,
# so without lxml the class is dropped instead of skipped.
if importlib.util.find_spec("lxml") is None:
    del BundleTextTests


class SchematicSheetCountTests(unittest.TestCase):
    """validation.json counts only sheets that hold parts; the root sheet only indexes them."""

    def validate(self, sheets, sheetpath):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("design", "verification", "build/kicad"):
                (root / name).mkdir(parents=True)
            graph = {"sheet": "E1", "components": [{"ref": "R101", "value": "1k", "pins": [{"number": "1", "net": "N1"}, {"number": "2", "net": "N2"}]}]}
            (root / "design/E1.json").write_text(json.dumps(graph), encoding="utf-8")
            path = f'<sheetpath names="{sheetpath}" tstamps="/x/"/>' if sheetpath else ""
            (root / "verification/netlist.xml").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n<export version="E"><design>'
                + "".join(f'<sheet number="{i}" name="{s}"/>' for i, s in enumerate(sheets, 1))
                + f'</design><components><comp ref="R101"><value>1k</value>{path}</comp></components><nets>'
                '<net code="1" name="N1"><node ref="R101" pin="1"/></net><net code="2" name="N2"><node ref="R101" pin="2"/></net>'
                '</nets></export>\n', encoding="utf-8")
            (root / "verification/erc.json").write_text(json.dumps({"sheets": [{"path": "/", "violations": []}]}), encoding="utf-8")
            subprocess.run([sys.executable, "-B", str(BASE / "tools/validate_project.py"), "--project", str(root)], capture_output=True)
            return json.loads((root / "verification/validation.json").read_text(encoding="utf-8"))

    def counts(self, report):
        return report["graph_netlist_comparison"], report["electrical_sheets"], report["schematic_sheets"], report["index_sheets"]

    def test_root_index_sheet_is_not_counted_as_electrical(self):
        self.assertEqual(self.counts(self.validate(["/", "/E1/"], "/E1/")), ("PASS", 1, 2, ["/"]))
        # A part without a sheetpath lies on the root sheet.
        self.assertEqual(self.counts(self.validate(["/"], None)), ("PASS", 1, 1, []))

    def test_part_on_an_unknown_sheet_fails_the_comparison(self):
        report = self.validate(["/", "/E1/"], "/E9/")
        self.assertEqual(report["graph_netlist_comparison"], "FAIL")
        self.assertTrue(any("unknown sheet /E9/" in e for e in report["comparison_errors"]))

    def test_documents_refuse_a_page_count_other_than_the_netlist(self):
        generated = {"pages": [{"stem": "E1"}, {"stem": "E2"}]}
        self.assertEqual(documents.electrical_pages({"electrical_sheets": 2}, generated), 2)
        with self.assertRaisesRegex(SystemExit, "electrical_sheets=3"):
            documents.electrical_pages({"electrical_sheets": 3}, generated)


class NoteWrapTests(unittest.TestCase):
    NOTE = {"id": "E9-01", "kind": "open", "head": "E9-01 — OPEN, блокує випуск — STACK §2.7 (IP2368); §5.1; §8 (IP2368); §8.1 (матриця DRP)",
            "body": [WORDS, "Ворота (стенд): " + WORDS[:300]]}

    def test_frame_follows_the_wrap(self):
        standard, wide = kicad.wrap_note(self.NOTE), kicad.wrap_note(self.NOTE, 180)
        self.assertEqual((standard["w"], wide["w"]), (kicad.NOTE_W, 80 * U))
        self.assertAlmostEqual(standard["w"], 137.16)
        for note, chars in ((standard, 110), (wide, 180)):
            self.assertTrue(all(len(line) <= chars for line in note["lines"]))
            self.assertTrue(all(len(line) <= chars * 100 // 110 for line in note["head"]))
            self.assertAlmostEqual(note["height"] / U, round(note["height"] / U))
        self.assertLess(wide["height"], standard["height"])
        self.assertEqual(" ".join(standard["lines"]).split(), " ".join(wide["lines"]).split())

    def test_a_narrow_group_keeps_a_narrower_wrap_than_the_sheet_cap(self):
        # The manifest's note_wrap_chars records this per note; note_wrap_cap is only the bound.
        for width, chars in ((400, 130), (140, 121), (100, kicad.NOTE_CHARS)):
            row = SimpleNamespace(box=(0, 0, width, 40), refs=["U901"], notes=[])
            (block,) = kicad.make_blocks([("Група", [row])], {"U901": [self.NOTE]}, 130)
            self.assertEqual(block.rows[0].notes[0]["chars"], chars, width)
            self.assertTrue(all(len(line) <= chars for line in block.rows[0].notes[0]["lines"]))


class SparsePageTests(unittest.TestCase):
    """A sheet whose last page would hold one small block is packed again with wider notes."""

    def groups(self, second_height):
        wide = kicad.wrap_note(NoteWrapTests.NOTE, kicad.NOTE_WIDE_CHARS[0])["height"]
        # Just short enough (1 mm) to leave room for the second group once the notes are wider.
        first = SimpleNamespace(box=(0, 0, 400, 123 * U - wide - 1.0), refs=["U901"], notes=[])
        second = SimpleNamespace(box=(0, 0, 400, second_height), refs=["U902"], notes=[])
        return [("Перша група", [first]), ("Друга група", [second])], {"U901": [NoteWrapTests.NOTE]}

    def test_sparse_last_page_is_saved_by_the_narrowest_wider_wrap(self):
        groups, notes = self.groups(20)
        standard = kicad.pack_pages(kicad.make_blocks(groups, notes))
        self.assertEqual(len(standard), 2)
        self.assertLess(kicad.page_fill(standard[-1]), kicad.SPARSE_LAST_PAGE)
        pages, chars = kicad.layout_sheet(groups, notes)
        self.assertEqual((len(pages), chars), (1, kicad.NOTE_WIDE_CHARS[0]))
        self.assertEqual((pages[0][0][0].rows[0].notes[0]["w"], pages[0][0][0].rows[0].notes[0]["chars"]), (kicad.note_width(chars), chars))
        self.assertEqual(groups[0][1][0].notes, [])  # the routed rows are shared, never rewritten

    def test_a_reasonably_filled_last_page_keeps_the_standard_notes(self):
        groups, notes = self.groups(150)
        pages, chars = kicad.layout_sheet(groups, notes)
        self.assertEqual((len(pages), chars), (2, kicad.NOTE_CHARS))
        self.assertGreaterEqual(kicad.page_fill(pages[-1]), kicad.SPARSE_LAST_PAGE)


class DrawingGateTests(unittest.TestCase):
    """run_checks.py stops before the netlist export on a sparse page or a fallback label."""

    def gate(self, manifest):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "generation-manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            return checks.drawing_gate(path)

    def manifest(self, sparse=(), fallback=0):
        return {"sparse_last_pages": list(sparse), "drawing": {"fallback_labels": fallback, "wire_crossings": 3}}

    def test_sparse_pages_and_fallback_labels_fail(self):
        for manifest, message in ((self.manifest(["E9_02"]), "sparse last pages E9_02; fallback labels 0"),
                                  (self.manifest(fallback=1), "sparse last pages none; fallback labels 1")):
            with self.subTest(message=message), self.assertRaisesRegex(SystemExit, "Schematic drawing gate: " + message):
                self.gate(manifest)
        self.assertEqual(self.gate(self.manifest())["drawing"]["wire_crossings"], 3)  # crossings are recorded, not gated

    def test_a_manifest_without_the_fields_fails(self):
        for manifest in ({"drawing": {"fallback_labels": 0}}, {"sparse_last_pages": [], "drawing": {}}, {"sparse_last_pages": []}):
            with self.subTest(manifest=manifest), self.assertRaisesRegex(SystemExit, "Schematic drawing gate: .* has no"):
                self.gate(manifest)


class DrawnEdgeTests(unittest.TestCase):
    def test_grid_snap_counts_against_the_right_page_edge(self):
        # A row box starting between grid lines is snapped right, onto the grid, when drawn.
        row = SimpleNamespace(box=(1.0, 0, 222.0, 40), refs=[], notes=[])
        block = kicad.Block("Блок", [row], 0)
        self.assertAlmostEqual(block.right(kicad.AREA_X0), kicad.AREA_X0 + block.w + 1.0)
        self.assertLessEqual(kicad.AREA_X1, 582.0 - U)
        left = kicad.Block("Ліворуч", [SimpleNamespace(box=(0, 0, 337.0, 40), refs=[], notes=[])], 0)
        # By its estimated width the block would fit beside the first one; drawn, it would cross the margin.
        x = U * math.ceil((kicad.AREA_X0 + left.w + kicad.BLOCK_GAP) / U)
        self.assertLessEqual(x + block.w, kicad.AREA_X1)
        self.assertGreater(block.right(x), kicad.AREA_X1)
        (page,) = kicad.pack_first_fit([left, block])
        self.assertEqual([(b.title, bx) for b, bx, _ in page], [("Ліворуч", kicad.AREA_X0), ("Блок", kicad.AREA_X0)])


class BusRowTests(unittest.TestCase):
    """Two boxes facing each other over a bus: each wire gets its own label, nothing crosses."""

    def setUp(self):
        names = [f"D{i // 2}_{'PN'[i % 2]}" for i in range(8)]
        self.comps = [
            {"ref": "J901", "value": "bus header", "kind": "connector",
             "pins": [{"number": str(i + 1), "name": n, "net": "E9_BUS_" + n} for i, n in enumerate(names)] + [{"number": "9", "name": "GND", "net": "GND"}]},
            {"ref": "U901", "value": "bus module", "kind": "module",
             "pins": [{"number": f"B{i + 1}", "name": "IN_" + n, "net": "E9_BUS_" + n} for i, n in enumerate(names)] + [{"number": "G", "name": "GND", "net": "GND"}]}]
        self.ctx = kicad.Context([{"sheet": "E9", "components": self.comps}])
        self.key = ("E9", "Шина")

    def test_packed_bus_needs_fallbacks_and_the_spread_one_does_not(self):
        (seq, lo, up), = kicad.build_group_rows(self.comps, self.ctx, self.key)
        state = kicad.item_state(seq)
        packed = kicad.layout_row(seq, lo, up, self.ctx, self.key)
        board = kicad.route_row(packed, self.ctx, self.key)[0]
        self.assertEqual(packed.spread, 0)
        self.assertGreater(board.fallback + board.crossings(), 0)
        kicad.restore_items(state)
        (row, board, *_), = kicad.route_group(self.comps, self.ctx, self.key)
        self.assertEqual((row.spread, board.fallback, board.crossings()), (2, 0, 0))
        for part in row.parts:
            rows = sorted(y for pin, (x, y) in part.pin_points() if pin["p"]["net"] != "GND")
            self.assertEqual([b - a for a, b in zip(rows, rows[1:])], [2] * 7, part.sym.comp["ref"])

    def test_crossing_counts_two_nets_passing_straight_through(self):
        board = kicad.Board()
        board.edge.update({("h", -1, 0): "A", ("h", 0, 0): "A", ("v", 0, -1): "B", ("v", 0, 0): "B"})
        self.assertEqual(board.crossings(), 1)
        board.edge[("v", 0, 0)] = "A"   # B only reaches the point: it does not pass through
        self.assertEqual(board.crossings(), 0)


if __name__ == "__main__":
    unittest.main()
