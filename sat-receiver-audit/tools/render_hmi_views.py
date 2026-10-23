#!/usr/bin/env python3
"""Deterministic offscreen HMI views: the real console against a real SIMULATION labd.

Linux/CI only. software/tests/test_hmi.py runs first in a child process, and
nothing is written unless every targeted test passes, including the actual
offscreen render and the actual Qt worker close. The service is the real
`srrx.daemon --simulate --stdio` child (DemoTransport); one explicit simulated
ARM+HOLD replaces touch input. The spectrum is the real `srrx.labrx --simulate`
CLI output (seeded) and the model the grouped `learning.demo` toy model. No
physical backend, device node, GNSS endpoint, touchscreen or display is used.

  python3 tools/render_hmi_views.py [--output verification/hmi-views]
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

BASE = Path(__file__).resolve().parents[1]
HMI_SOURCE = BASE / "software/srrx/hmi.py"
PAGES = ("overview", "receiver", "spectrum", "location", "teach-classify", "bench")
QT_RENDER_TEST = "test_actual_offscreen_render_all_pages_and_close_disarm"
WORKER_CLOSE_TEST = "test_worker_real_demo_arm_then_window_close_stops_service"
SERVICE = "real srrx.daemon --simulate --stdio child"
SPECTRUM = "actual srrx.labrx --simulate CLI output; canonical masked FFT frame"
LEARNING = "actual learning.demo grouped toy-spectrum CPU model; infer on SIM FFT; no field accuracy claim"
LOCATION = "no GNSS endpoint configured; tracker reports no live fix"
PRESENTATION = {
    "overview": "battery/temperature/controller+lease cards and channel power/route/current reservations",
    "learning": "human-readable UNKNOWN/class, heuristic score, CPU/NPU reason and independent group counts",
    "location": "coordinates/source/live status/age/uncertainty",
    "raw_json": "optional collapsed diagnostics only"}
LIMITATIONS = ["Offscreen rendering only",
               "No touchscreen/gloves/sunlight/Q6A latency measurements",
               "Display brightness wiring remains E3-01 OPEN"]


class RenderFailure(RuntimeError):
    pass


def environment():
    value = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    paths = [str(BASE / "software"), str(BASE), str(BASE / "firmware/pico")]
    value["PYTHONPATH"] = os.pathsep.join(paths + ([value["PYTHONPATH"]] if value.get("PYTHONPATH") else []))
    return value


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class _Outcomes(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = {}

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcomes[test.id()] = "pass"

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcomes[test.id()] = "fail"

    def addError(self, test, err):
        super().addError(test, err)
        self.outcomes[test.id()] = "error"

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.outcomes[test.id()] = "skip"


def run_targeted_tests():
    """Child mode: run test_hmi.py here and print one JSON summary line."""
    sys.path[:0] = [str(BASE / "software"), str(BASE), str(BASE / "firmware/pico")]
    suite = unittest.TestLoader().discover(str(BASE / "software/tests"), pattern="test_hmi.py")
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1, resultclass=_Outcomes).run(suite)
    def outcome(name):
        return [value for test, value in result.outcomes.items() if test.rsplit(".", 1)[-1] == name]
    failed = len(result.failures) + len(result.errors) + len(result.unexpectedSuccesses)
    summary = {"total": result.testsRun, "skipped": len(result.skipped), "failed": failed,
               "passed": result.testsRun - failed - len(result.skipped) - len(result.expectedFailures),
               "qt_render": outcome(QT_RENDER_TEST) == ["pass"],
               "real_qt_worker_close": outcome(WORKER_CLOSE_TEST) == ["pass"]}
    print(json.dumps(summary), flush=True)
    return 0 if result.wasSuccessful() else 1


def targeted_tests(timeout=1800):
    """Run software/tests/test_hmi.py in a fresh offscreen process; refuse unless all pass."""
    process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--targeted-tests-json"],
                             cwd=BASE, env=environment(), stdout=subprocess.PIPE, timeout=timeout)
    lines = process.stdout.decode("utf-8", "replace").strip().splitlines()
    try:
        summary = json.loads(lines[-1])
    except (IndexError, ValueError) as error:
        raise RenderFailure("Targeted HMI tests produced no summary (exit " + str(process.returncode) + ")") from error
    if (process.returncode or summary.get("failed") or not summary.get("total")
            or summary["passed"] + summary["skipped"] != summary["total"]
            or summary.get("qt_render") is not True or summary.get("real_qt_worker_close") is not True):
        raise RenderFailure("Targeted HMI tests did not all pass: " + json.dumps(summary))
    return {key: summary[key] for key in ("total", "passed", "skipped", "qt_render", "real_qt_worker_close")}


def _wait(app, predicate, seconds, message):
    deadline = time.monotonic() + seconds
    while not predicate():
        if time.monotonic() > deadline:
            raise RenderFailure(message)
        app.processEvents()
        time.sleep(.02)


def render(stage):
    """Actual QApplication, window and worker; returns (views, versions) with PNGs in stage."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    sys.path[:0] = [str(BASE / "software"), str(BASE), str(BASE / "firmware/pico")]
    from PySide6 import __version__ as pyside_version
    from PySide6.QtCore import qVersion
    from PySide6.QtWidgets import QApplication
    from srrx import learning
    from srrx.hmi import ConsoleController, DemoTransport, create_window, load_spectrum, location_callbacks

    spectrum = stage / "spectrum.json"
    subprocess.run([sys.executable, "-m", "srrx.labrx", "--simulate", "--center-hz", "100000000",
                    "--sample-rate", "1024000", "--frames", "10", "--output", str(spectrum)],
                   cwd=BASE, env=environment(), stdout=subprocess.DEVNULL, timeout=120, check=True)
    (stage / "learning").mkdir()
    learning.demo(stage / "learning")
    model = learning.load_model(stage / "learning/model.json")
    callbacks, close_location = location_callbacks()  # No endpoint: no socket is opened.
    if callbacks["location"]().get("live_fix") is not False:
        raise RenderFailure("Location provider unexpectedly reports a live fix")
    application = QApplication.instance() or QApplication(sys.argv[:1])
    transport = DemoTransport()
    controller = ConsoleController(transport)
    window = create_window(controller, callbacks=callbacks)
    grabs = []
    try:
        window.show()
        def ready():
            data = controller.status()["data"]
            return (controller.status()["connected"] and data.get("session") is not None
                    and data.get("pico", {}).get("state") == "SAFE" and data.get("pico_fresh") is True)
        _wait(application, ready, 30, "SIMULATION labd did not report a fresh SAFE Pico")
        data = controller.status()["data"]
        if data.get("mode") != "SIMULATION" or data.get("hardware_qualified") is not False:
            raise RenderFailure("Refusing: the service is not explicitly SIMULATION")
        window.accept_frame(load_spectrum(spectrum))
        window.model = model
        window.worker.submit("arm")  # One explicit simulated operator ARM+HOLD.
        def active():
            view = controller.status()
            return (view["holding"] and controller.arm_started is None and view["data"]["policy"]["armed"]
                    and view["data"]["pico"].get("state") == "ACTIVE" and view["data"].get("pico_fresh") is True)
        _wait(application, active, 10, "Simulated ARM+HOLD did not reach ACTIVE")
        settled = time.monotonic() + .6  # Natural heartbeats render Location and the latest state.
        _wait(application, lambda: time.monotonic() >= settled, 2, "Qt event loop stalled")
        for index, page in enumerate(PAGES):
            window.tabs.setCurrentIndex(index)
            if page == "teach-classify":
                window.learning_action("infer")
                if window.learning_text.toPlainText().startswith("Rejected"):
                    raise RenderFailure("SIM inference was rejected: " + window.learning_text.toPlainText())
            for _ in range(5):
                application.processEvents()
                time.sleep(.02)
            if page == "teach-classify":  # Layout has settled: keep the inference result in view.
                window.tabs.currentWidget().ensureWidgetVisible(window.learning_text)
                application.processEvents()
            banner = window.banner.text()
            if not active() or "READY" not in banner or "CONTROL ARMED" not in banner or "HOLD ON" not in banner:
                raise RenderFailure("Console left the simulated ACTIVE state before capture: " + banner)
            image = window.grab()  # Pixels only; PNG encoding waits until after DISARM.
            if image.isNull():
                raise RenderFailure("Actual Qt grab failed: " + page)
            grabs.append((page, image))
    finally:
        window.close()  # Stops the worker: DISARM, then EOF ends the SIMULATION labd.
        deadline = time.monotonic() + 5
        while window.worker.isRunning() and time.monotonic() < deadline:
            application.processEvents()
            time.sleep(.02)
        window.worker.stopping.set()
        window.worker.wait(1500)
        transport.close()
        close_location()
        application.processEvents()
    if not controller.closed or controller.holding or transport.process.poll() is None:
        raise RenderFailure("SIMULATION service was not disarmed and closed")
    views = []
    for index, (page, image) in enumerate(grabs, 1):
        target = stage / ("%02d-%s.png" % (index, page))
        if not image.save(str(target), "PNG"):
            raise RenderFailure("PNG encoding failed: " + page)
        views.append({"page": page, "file": target.name, "width": image.width(), "height": image.height(),
                      "bytes": target.stat().st_size, "sha256": sha256(target)})
    return views, {"pyside6": pyside_version, "qt": qVersion(), "qt_platform": application.platformName(),
                   "backend": data["mode"]}


def report(views, versions, tests, hmi_sha256, output):
    def published(name):
        path = output / name
        return path.relative_to(BASE).as_posix() if path.is_relative_to(BASE) else path.as_posix()
    return {"schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS_OFFSCREEN_SIMULATION", "python": platform.python_version(),
            "pyside6": versions["pyside6"], "qt": versions["qt"], "qt_platform": versions["qt_platform"],
            "backend": versions["backend"], "physical_tests_performed": False, "hardware_devices_opened": False,
            "service": SERVICE, "simulated_arm_requested": True, "spectrum": SPECTRUM, "learning": LEARNING,
            "location": LOCATION, "hmi_sha256": hmi_sha256, "targeted_tests": tests,
            "product_presentation": dict(PRESENTATION),
            "views": [{"page": view["page"], "path": published(view["file"]), "width": view["width"],
                       "height": view["height"], "bytes": view["bytes"], "sha256": view["sha256"]} for view in views],
            "limitations": list(LIMITATIONS)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=BASE / "verification/hmi-views")
    parser.add_argument("--targeted-tests-json", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.targeted_tests_json:
        return run_targeted_tests()
    output = args.output.resolve()
    try:
        if not sys.platform.startswith("linux"):
            raise RenderFailure("HMI views are rendered on Linux (real stdio labd and labrx SIM subprocesses)")
        hmi_sha256 = sha256(HMI_SOURCE)
        tests = targeted_tests()
        with tempfile.TemporaryDirectory(prefix="srrx-hmi-views-") as directory:
            stage = Path(directory)
            views, versions = render(stage)
            if sha256(HMI_SOURCE) != hmi_sha256:
                raise RenderFailure("software/srrx/hmi.py changed while rendering")
            if [view["page"] for view in views] != list(PAGES) or versions["qt_platform"] != "offscreen":
                raise RenderFailure("Unexpected page set or Qt platform: " + json.dumps(versions))
            value = report(views, versions, tests, hmi_sha256, output)
            encoded = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
            output.mkdir(parents=True, exist_ok=True)
            for view in views:
                temporary = output / (view["file"] + ".tmp")
                shutil.copyfile(stage / view["file"], temporary)
                os.replace(temporary, output / view["file"])
            temporary = output / "report.json.tmp"
            temporary.write_bytes(encoded)
            os.replace(temporary, output / "report.json")  # Written last: binds the PNGs above.
    except (RenderFailure, OSError, ValueError, subprocess.SubprocessError, ImportError) as error:
        print("render_hmi_views: " + str(error)[:2000], file=sys.stderr)
        return 1
    print(json.dumps({"status": "PASS_OFFSCREEN_SIMULATION", "report": str(output / "report.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
