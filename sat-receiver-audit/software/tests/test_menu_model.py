"""srrx.menu_model against the console it describes; RX-11 itself is tested in deployment/tests."""
import copy
import importlib.util
import os
from pathlib import Path
import unittest

from srrx import menu_model
from srrx.hmi import EN_OUTPUTS, ConsoleController, HMINavigation, create_window

PROJECT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("pico_hmi_menu_model_test", PROJECT / "firmware/pico/hmi.py")
pico_hmi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pico_hmi)
# Every labd operation ConsoleController sends: command() plus poll()'s status and the HOLD lease.
CONSOLE_OPERATIONS = {"arm", "recover", "disarm", "shutdown", "control", "mode", "relay", "route", "confirmations",
                      "status", "lease"}


def leaf(leaf_id):
    return next(item for item in menu_model.LEAVES if item["id"] == leaf_id)


class MenuModelTests(unittest.TestCase):
    def test_shipped_model_is_valid_and_matches_the_console_constants(self):
        menu_model.validate()
        self.assertEqual(menu_model.KEYS, pico_hmi.KEY_NAMES)
        self.assertEqual(menu_model.GESTURES, HMINavigation.NAMES)
        self.assertEqual(menu_model.OUTPUTS, EN_OUTPUTS)
        self.assertEqual([p["id"] for p in menu_model.PAGES], ["overview", "receiver", "spectrum", "location", "learning", "bench"])
        # hmi.py scrolls the Teach / Classify page by its tab index.
        self.assertEqual(menu_model.page_index("learning"), 4)
        with self.assertRaises(menu_model.MenuModelError):
            menu_model.page_index("radio")
        bench = [item for item in menu_model.LEAVES if item["id"].startswith("bench.output.")]
        self.assertEqual([item["label"] for item in bench], list(EN_OUTPUTS))

    def test_backends_and_declared_fallbacks(self):
        kinds = {item["backend"]["kind"] for item in menu_model.LEAVES}
        self.assertEqual(kinds, {"labd_op", "page_only"})  # the console has no engine or decoder leaf yet
        operations = {item["backend"]["name"] for item in menu_model.LEAVES if item["backend"]["kind"] == "labd_op"}
        self.assertEqual(operations, CONSOLE_OPERATIONS)
        self.assertEqual({item["id"] for item in menu_model.LEAVES if item["needs_lime"]},
                         {"receiver.route.lime", "bench.output.lime3v3"})
        self.assertEqual({item["id"] for item in menu_model.LEAVES if item["needs_t7"]}, {"bench.output.t7"})
        for item in menu_model.LEAVES:
            self.assertEqual(bool(item["fallback_text"]), item["needs_lime"] or item["needs_t7"], item["id"])
        self.assertIn("STACK.md:977", leaf("bench.output.t7")["fallback_text"])
        self.assertEqual(menu_model.LABD_UNIT["program"], "srrx.daemon")
        self.assertEqual(menu_model.CONSOLE_UNIT["program"], "srrx.hmi")
        for unit in (menu_model.LABD_UNIT, menu_model.CONSOLE_UNIT):
            text = (PROJECT / "software/systemd" / unit["name"]).read_text(encoding="utf-8")
            self.assertIn("-m " + unit["program"] + " ", text)

    def test_critical_leaves_and_the_open_physical_disarm_gap(self):
        critical = {item["id"] for item in menu_model.LEAVES if item["critical"]}
        self.assertTrue({"frame.disarm", "frame.lock", "frame.home", "overview.status"} <= critical)
        # The one critical action without a glove path: RX-11 reports it BLOCKED (HMI.md, DEPLOYMENT.md).
        self.assertEqual({i for i in critical if not leaf(i)["controls"]["keys"]}, {"frame.disarm"})
        physical = {key for item in menu_model.LEAVES for key in item["controls"]["keys"]}
        self.assertEqual(physical, set(menu_model.KEYS + menu_model.ENCODERS))
        for item in menu_model.LEAVES:
            if item["controls"]["keys"]:
                # Physical inputs navigate, lock or read status; none reaches an energizing labd operation.
                self.assertIn(item["backend"]["name"], ("hmi", "status"), item["id"])

    def test_validate_rejects_schema_defects(self):
        def broken(change):
            leaves = copy.deepcopy(list(menu_model.LEAVES))
            change(leaves)
            with self.assertRaises(menu_model.MenuModelError):
                menu_model.validate(leaves=tuple(leaves))
        broken(lambda leaves: leaves.append(dict(leaves[0])))  # duplicate id
        broken(lambda leaves: leaves[0].update(page="radio"))
        broken(lambda leaves: leaves[0].update(extra=True))
        broken(lambda leaves: leaves[0]["controls"].update(keys=("PTT",)))
        broken(lambda leaves: leaves[0]["controls"].update(keys=["HOME"]))
        broken(lambda leaves: leaves[0]["controls"].update(touch=False))  # no control at all
        broken(lambda leaves: leaves[0]["backend"].update(kind="shell"))
        broken(lambda leaves: leaves[0].update(backend={"kind": "engine_unit", "name": "x.service", "scope": "user", "program": "rm -rf"}))
        broken(lambda leaves: leaves[0].update(needs_lime=1))
        broken(lambda leaves: leaves[0].update(fallback_text=""))
        broken(lambda leaves: leaves[0].update(id="Frame.ARM"))
        with self.assertRaises(menu_model.MenuModelError):
            menu_model.validate(pages=menu_model.PAGES + ({"id": "overview", "label": "Again"},))
        with self.assertRaises(menu_model.MenuModelError):
            menu_model.validate(leaves=())
        # An engine leaf (a later Lab Shell hub, e.g. WEFAX -> OpenWebRX+ fax) names its unit and program.
        engine = menu_model._leaf("overview.engine", "overview", "Engine", "engine_unit", "fixture-engine.service")
        engine["backend"].update(scope="system", program="/usr/bin/fixture-engine")
        menu_model.validate(leaves=menu_model.LEAVES + (engine,))


@unittest.skipUnless(importlib.util.find_spec("PySide6"), "optional PySide6 is not installed")
class MenuModelQtTests(unittest.TestCase):
    """The console builds its tabs from PAGES and shows every touch leaf where the model puts it."""

    @staticmethod
    def texts(widget):
        from PySide6 import QtWidgets
        # Text-less buttons are Qt's own (tab-bar scroll arrows); group titles are not controls.
        return [child.text() for child in widget.findChildren(QtWidgets.QAbstractButton) if child.text()]

    def test_tabs_and_controls_follow_the_menu_model(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6 import QtWidgets
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        controller = ConsoleController(lambda request: {"ok": False, "error": "offline fixture"})
        window = create_window(controller, start_worker=False)
        try:
            self.assertEqual([window.tabs.tabText(i) for i in range(window.tabs.count())], [p["label"] for p in menu_model.PAGES])
            everything = self.texts(window)
            pages = {page["id"]: self.texts(window.tabs.widget(index)) for index, page in enumerate(menu_model.PAGES)}
            inside = [text for texts in pages.values() for text in texts]
            frame = list(everything)
            for text in inside:
                frame.remove(text)
            covered = {"frame": frame, **pages}
            for item in menu_model.LEAVES:
                if not item["controls"]["touch"] or item["id"].startswith("bench.output."):
                    continue
                self.assertIn(item["label"], covered[item["page"]], item["id"])
            # Inverse: every button or check box is a leaf (the per-output ON/OFF pairs are the bench rows).
            labels = [item["label"] for item in menu_model.LEAVES if item["controls"]["touch"]]
            for page, texts in covered.items():
                for text in texts:
                    if text in ("ON", "OFF") and page == "bench":
                        continue
                    self.assertIn(text, labels, (page, text))
                    labels.remove(text)
            self.assertEqual(pages["bench"].count("ON"), len(menu_model.OUTPUTS))
            self.assertEqual(pages["bench"].count("OFF"), len(menu_model.OUTPUTS))
            outputs = [w.text().split(" ")[0] for w in window.tabs.widget(menu_model.page_index("bench")).findChildren(QtWidgets.QLabel)
                       if w.text().startswith("EN_")]
            self.assertEqual(outputs, list(menu_model.OUTPUTS))
        finally:
            window.close()
            app.processEvents()

    def test_a_page_that_differs_from_the_model_refuses_to_start(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6 import QtWidgets
        from unittest.mock import patch
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        controller = ConsoleController(lambda request: {"ok": False, "error": "offline fixture"})
        renamed = tuple(dict(page, label="Radio") if page["id"] == "receiver" else page for page in menu_model.PAGES)
        with patch.object(menu_model, "PAGES", renamed), self.assertRaises(RuntimeError):
            create_window(controller, start_worker=False)
        app.processEvents()


if __name__ == "__main__":
    unittest.main()
