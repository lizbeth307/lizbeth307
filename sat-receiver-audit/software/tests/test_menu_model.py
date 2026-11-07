"""srrx.menu_model against the console it describes; RX-11 itself is tested in deployment/tests."""
import ast
import copy
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from srrx import menu_model
from srrx.hmi import EN_OUTPUTS, ConsoleController, HMINavigation, create_window

PROJECT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("pico_hmi_menu_model_test", PROJECT / "firmware/pico/hmi.py")
pico_hmi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pico_hmi)
# What one touch leaf makes ConsoleController send, in order, where it is more than [backend name]:
# ARM/RECOVER start the HOLD lease at once; Shutdown stops HOLD (disarm) before it asks labd.
SENDS = {"arm": ["arm", "lease"], "recover": ["recover", "lease"], "shutdown": ["disarm", "shutdown"]}


def console_operations():
    """Every labd operation ConsoleController can send, read from srrx/hmi.py: the keys of
    command()'s `required` table and each {"op": <literal>} request of the class (status, lease,
    disarm, shutdown). Returns (all operations, the command() table keys)."""
    tree = ast.parse((PROJECT / "software/srrx/hmi.py").read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ConsoleController")
    table, literal = set(), set()
    for node in ast.walk(cls):
        if (isinstance(node, ast.Assign) and [getattr(t, "id", None) for t in node.targets] == ["required"]
                and isinstance(node.value, ast.Dict)):
            table.update(key.value for key in node.value.keys)
        elif isinstance(node, ast.Dict):
            literal.update(value.value for key, value in zip(node.keys, node.values)
                           if isinstance(key, ast.Constant) and key.value == "op" and isinstance(value, ast.Constant))
    return table | literal, table


def leaf(leaf_id):
    return next(item for item in menu_model.LEAVES if item["id"] == leaf_id)


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


class Labd:
    """Recording labd stand-in: accepts every request and reports the state the test sets."""
    def __init__(self):
        self.sent = []
        self.policy = {"armed": False, "fault": None, "mode": "lab", "outputs": {name: False for name in EN_OUTPUTS}}
        self.pico = {"state": "SAFE"}

    def __call__(self, request):
        self.sent.append(copy.deepcopy(request))
        if request["op"] == "status":
            return {"ok": True, "data": {"mode": "SIMULATION", "pico": dict(self.pico), "pico_fresh": True,
                                         "policy": copy.deepcopy(self.policy)}}
        return {"ok": True}


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
        sent, table = console_operations()
        self.assertTrue({"arm", "disarm", "control", "route", "relay", "mode", "confirmations"} <= table, table)
        self.assertEqual(operations, sent)  # the console sends no operation the model leaves out, and vice versa
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

    def test_each_touch_leaf_reaches_its_declared_backend(self):
        """Clicks every touch leaf's own widget: a labd_op leaf sends exactly its backend operation
        (through action(), the worker queue and ConsoleController), a page_only leaf sends nothing."""
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6 import QtWidgets
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        clock, labd = Clock(), Labd()
        controller = ConsoleController(labd, clock)
        window = create_window(controller, start_worker=False)
        closed = False

        def state(active):
            # Disarmed with fresh status, or explicit ARM + HOLD with the handshake done and lab loads confirmed.
            controller.command("disarm")
            labd.policy["armed"], labd.pico["state"] = False, "SAFE"
            clock.now += .1
            controller.poll()
            if active:
                self.assertTrue(controller.command("arm")["ok"])
                labd.policy["armed"], labd.pico["state"] = True, "ACTIVE"
                clock.now += .1
                controller.poll()
                self.assertTrue(controller.command("confirmations", value={"bench_loads": True})["ok"])
            window.render_state(controller.status())
            labd.sent.clear()

        def press(widget):
            clock.now += 1.0  # status stays fresh (1.5 s); HOLD may renew its 1 s lease
            self.assertTrue(widget.isEnabled(), widget.text())
            widget.click()
            while not window.worker.commands.empty():
                operation, fields = window.worker.commands.get_nowait()
                if operation == "hold":  # the two dispatch branches of the console Worker.run
                    controller.hold(**fields)
                else:
                    controller.command(operation, **fields)
            sent, labd.sent[:] = list(labd.sent), []
            return sent

        try:
            buttons = [b for b in window.findChildren(QtWidgets.QAbstractButton) if b.text()]
            pages = {page["id"]: [b for b in buttons if window.tabs.widget(index).isAncestorOf(b)]
                     for index, page in enumerate(menu_model.PAGES)}
            pages[menu_model.FRAME] = [b for b in buttons if not window.tabs.isAncestorOf(b)]
            bench = window.tabs.widget(menu_model.page_index("bench"))
            cells = {w.text().split(" ")[0]: w.parentWidget() for w in bench.findChildren(QtWidgets.QLabel) if w.text().startswith("EN_")}
            touch = [item for item in menu_model.LEAVES if item["controls"]["touch"]]
            seen = {}

            def widget(item):
                # Same-label leaves of one page (the three "Apply route") follow the console's order.
                key = (item["page"], item["label"])
                seen[key] = seen.get(key, -1) + 1
                return [b for b in pages[item["page"]] if b.text() == item["label"]][seen[key]]

            yes = QtWidgets.QMessageBox.StandardButton.Yes
            close = None
            with patch.object(QtWidgets.QMessageBox, "question", return_value=yes):
                for item in touch:
                    name, suffix = item["backend"]["name"], item["id"].rsplit(".", 1)[1]
                    if item["backend"]["kind"] != "labd_op":
                        continue
                    if item["id"].startswith("bench.output."):
                        on, off = (next(b for b in cells[item["label"]].findChildren(QtWidgets.QPushButton) if b.text() == text)
                                   for text in ("ON", "OFF"))
                        for button, value in ((on, True), (off, False)):
                            state(active=True)
                            sent = press(button)
                            self.assertEqual(sent, [{"op": name, "name": item["label"], "value": value}], item["id"])
                        continue
                    target = widget(item)
                    if item["id"] == "frame.close":
                        close = (item, target)  # closes the window: pressed last
                        continue
                    state(active=item["id"] not in ("frame.arm", "frame.recover") and not item["id"].startswith("bench.mode."))
                    sent = press(target)
                    self.assertEqual([r["op"] for r in sent], SENDS.get(name, [name]), item["id"])
                    own = next(r for r in sent if r["op"] == name)
                    if name == "route":
                        self.assertEqual(own["receiver"], suffix.upper(), item["id"])
                    elif name == "mode":
                        self.assertEqual(own["value"], suffix, item["id"])
                    elif name == "confirmations":
                        self.assertEqual(set(own["value"]), {suffix}, item["id"])
            # page_only leaves never reach labd: dialogs answer No/cancel, SIM capture and jobs are stubs.
            with patch.object(QtWidgets.QMessageBox, "question", return_value=QtWidgets.QMessageBox.StandardButton.No), \
                    patch.object(QtWidgets.QFileDialog, "getOpenFileName", return_value=("", "")), \
                    patch.object(QtWidgets.QFileDialog, "getSaveFileName", return_value=("", "")), \
                    patch.object(window.receiver_job, "start") as capture, \
                    patch.object(window.learning_runner, "submit", return_value=False):
                state(active=True)
                for item in touch:
                    if item["backend"]["kind"] == "page_only":
                        widget(item).click()
                        self.assertTrue(window.worker.commands.empty(), item["id"])
                        self.assertEqual(labd.sent, [], item["id"])
                self.assertEqual(capture.call_count, 1)  # the SIM capture leaf ran its own handler
            self.assertEqual(sum(seen.values()) + len(seen), len([i for i in touch if not i["id"].startswith("bench.output.")]))
            # Close + DISARM closes the window; the controller disarms.
            item, target = close
            state(active=True)
            closed = True
            self.assertEqual([r["op"] for r in press(target)], [item["backend"]["name"]], item["id"])
            self.assertTrue(controller.closed)
        finally:
            if not closed:
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
