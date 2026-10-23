#!/usr/bin/env python3
"""Executable USB/display/storage module emulation, with explicit missing drivers.

run(project=None, output_dir=None, qt=True) returns a JSON-compatible report.
The CLI --output is a JSON file, not a directory. No host USB/sysfs device is
touched. Qt input injection exercises the real production menu and controller;
it does not emulate Linux HID enumeration, a Wisecoco panel, or its firmware.
"""
from __future__ import annotations

import argparse
import contextlib
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time
import traceback
from unittest import mock

try:
    from .io_modules import USBFixture, USBInventory, changes, MAX_DEVICES
except ImportError:
    from io_modules import USBFixture, USBInventory, changes, MAX_DEVICES


DOCS = ["https://doc.qt.io/qt-6/qtest-qtoucheventsequence.html",
        "https://doc.qt.io/qtforpython-6/PySide6/QtGui/QInputDevice.html"]
REFS = {
    # Qt/storage scenarios exercise neither passive J512 contacts nor the U505
    # EN_T7 switch/FAULT_N. run.py never counts FILESYSTEM_FIXTURE as coverage.
    "hub": ["design/E5.json:U510", "design/E5.json:J512", "build/12-revision-v2.1.md"],
    "touch": ["design/E5.json:U520", "design/E5-connection-guide.md"],
    "t7": ["design/E5.json:U540", "design/E5.json:EN_T7"],
    "hantek": ["design/E5.json:J501", "STACK.md:3.1 Hantek 6022BE", "STACK.md:P17"],
}
TASK_REFS = {"IO-INVENTORY-SCENARIOS": REFS["hub"] + REFS["touch"] + REFS["t7"] + REFS["hantek"],
             "IO-STORAGE-SCENARIOS": REFS["t7"], "IO-GUARDED-STORAGE-SCENARIOS": REFS["t7"],
             "IO-QT-SCENARIOS": REFS["touch"] + REFS["t7"]}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def record(identifier, refs, level, status, evidence, limitation=None):
    value = {"id": identifier, "design_refs": refs, "coverage_level": level,
             "status": status, "physical_verified": False, "accepted": False,
             "case_count": 1 if status in ("PASS", "FAIL") else 0, "evidence": evidence}
    if limitation:
        value["limitation"] = limitation
    return value


def inventory_scenarios(root):
    tree = USBFixture(root)
    inventory = USBInventory(root)
    empty = inventory.scan()
    require(empty["devices"] == [], "New fixture is not empty")
    # Private invented identities: these are deliberately not claimed vendor IDs.
    tree.connect("1-2", vid="ffee", pid="1000", product="Synthetic CH334F-role hub", device_class="09", driver="hub")
    tree.connect("1-2.1", vid="ffee", pid="1001", product="Synthetic generic touch HID", device_class="03", driver="usbhid", speed="12")
    tree.connect("1-2.2", vid="ffee", pid="1002", product="Synthetic Hantek-role accessory")
    tree.connect("2-1", vid="ffee", pid="1003", product="Synthetic T7-role storage", device_class="08", speed="5000", driver="uas")
    attached = inventory.scan()
    require(len(attached["devices"]) == 4 and not attached["errors"], "Hotplug inventory incomplete")
    require(changes(empty, attached)["added"] == ["1-2", "1-2.1", "1-2.2", "2-1"], "Wrong hotplug delta")
    require(all(not d["driver_selected"] and d["binding"] == "UNSUPPORTED" for d in attached["devices"]), "Inventory selected a driver")
    require(attached["auto_bind"] is False, "Fixture inventory auto-bound a device")
    records = [record("IO-USB-TOPOLOGY", REFS["hub"], "FILESYSTEM_FIXTURE", "PASS",
                      {"connected": attached, "events": changes(empty, attached), "kernel_uevents": False},
                      "Observed driver names are synthetic symlink text. No kernel hub, USB transfers or CH334F silicon are emulated.")]

    # Unknown descriptors never become a supported instrument by VID similarity.
    path = tree.connect("1-3", vid="ffff", pid="ffff", product="Unknown USB device")
    unknown = inventory.scan()
    unknown_record = next(d for d in unknown["devices"] if d["device"] == "1-3")
    require(unknown_record["binding"] == "UNSUPPORTED" and unknown_record["observed_driver"] is None,
            "Unknown descriptor acquired a driver")
    path.joinpath("idVendor").write_text("NOT_HEX\n", encoding="utf-8")
    malformed = inventory.scan()
    require(any(e["device"] == "1-3" for e in malformed["errors"]), "Malformed descriptor was accepted")
    path.joinpath("idVendor").write_bytes(b"x" * 257)
    oversize = inventory.scan()
    require(any(e["device"] == "1-3" for e in oversize["errors"]), "Oversize descriptor was accepted")
    path.joinpath("idVendor").unlink()
    path.joinpath("idVendor").symlink_to("/etc/passwd")
    symlink = inventory.scan()
    require(any(e["device"] == "1-3" for e in symlink["errors"]), "Descriptor symlink was followed")
    tree.remove("1-3")
    records.append(record("IO-USB-UNKNOWN-ERROR", REFS["hub"], "FILESYSTEM_FIXTURE", "PASS",
                          {"unknown": unknown_record, "malformed_rejected": True, "oversize_rejected": True,
                           "descriptor_symlink_rejected": True, "auto_bind": False}))

    removed = tree.remove("1-2")
    departed = inventory.scan()
    require(removed == ["1-2", "1-2.1", "1-2.2"], "Hub removal did not remove descendants")
    require(changes(attached, departed)["removed"] == removed, "Gone devices remain in inventory")
    require([d["device"] for d in departed["devices"]] == ["2-1"], "Unrelated storage disappeared")
    tree.connect("1-2", vid="ffee", pid="1000", product="Reconnected synthetic hub", device_class="09")
    reconnected = inventory.scan()
    require(next(d for d in reconnected["devices"] if d["device"] == "1-2")["observed_driver"] is None,
            "Reconnect reused cached driver state")
    records.append(record("IO-USB-REMOVE-RECONNECT", REFS["hub"] + REFS["touch"] + REFS["t7"],
                          "FILESYSTEM_FIXTURE", "PASS", {"removed": removed, "remaining": ["2-1"],
                          "reconnected_without_cached_binding": True, "kernel_hotplug": False}))

    with tempfile.TemporaryDirectory(prefix="srrx-inventory-bounds-") as bounded:
        bounded_tree = USBFixture(bounded)
        for index in range(1, MAX_DEVICES + 2):
            bounded_tree.connect("3-" + str(index), vid="ffee", pid="2000")
        capped = USBInventory(bounded).scan()
        require(capped["truncated"] and len(capped["devices"]) == MAX_DEVICES, "Inventory is not bounded")
        missing = bounded_tree.devices.with_name("devices-gone")
        bounded_tree.devices.rename(missing)
        gone = USBInventory(bounded).scan()
        require(gone["devices"] == [] and bool(gone["errors"]), "Unavailable inventory did not become unknown")
    records.append(record("IO-USB-INVENTORY-BOUNDS", REFS["hub"], "FILESYSTEM_FIXTURE", "PASS",
                          {"max_devices": MAX_DEVICES, "max_descriptor_bytes": 256,
                           "excess_entries_truncated": True, "inventory_gone_is_error_not_present": True}))
    return records


def storage_scenarios(root):
    from srrx.labrx import run_capture, atomic_json
    from srrx.spectrum import validate_frame
    root = Path(root)
    root.mkdir()
    latest, survey = root / "spectrum.json", root / "survey.jsonl"
    result = run_capture(frames=2, fft_size=64, center_hz=100000000,
                         sample_rate=1024000, output=latest, survey=survey)
    lines = [json.loads(line) for line in survey.read_text(encoding="utf-8").splitlines()]
    require(result["frames"] == 2 and result["raw_iq_persisted"] is False, "SIM capture unexpectedly persisted IQ")
    require(len(lines) == 2 and all(validate_frame(line) == line for line in lines), "Storage content is not canonical masked metadata")
    require(sorted(p.name for p in root.iterdir()) == ["spectrum.json", "survey.jsonl"], "Unexpected persisted files")
    require(all(not (set(line) & {"iq", "raw_iq", "samples", "audio", "payload"}) for line in lines), "Raw payload persisted")
    digest = hashlib.sha256(latest.read_bytes()).hexdigest()
    with mock.patch("srrx.labrx.os.fsync", side_effect=OSError(errno.ENOSPC, "synthetic storage full")):
        try:
            atomic_json(latest, {"incomplete": True})
        except OSError as error:
            require(error.errno == errno.ENOSPC, "Wrong injected storage error")
        else:
            raise AssertionError("Storage full was silently accepted")
    require(hashlib.sha256(latest.read_bytes()).hexdigest() == digest, "Failed atomic write replaced last good metadata")
    require(not list(root.glob(".srrx-*")), "Failed write left a staging file")
    blocker = root / "not-a-mount"
    blocker.write_text("synthetic unavailable storage path", encoding="utf-8")
    try:
        run_capture(frames=1, fft_size=64, output=blocker / "spectrum.json")
    except OSError:
        pass
    else:
        raise AssertionError("Unavailable storage parent did not fail")
    return [record("IO-T7-METADATA-PERSISTENCE", REFS["t7"], "PRODUCTION_SOFTWARE_ON_TEMP_FILESYSTEM", "PASS",
                   {"implementation": "srrx.labrx.run_capture + spectrum.validate_frame", "simulated_frames": 2,
                    "files": ["spectrum.json", "survey.jsonl"], "raw_iq_persisted": False,
                    "source": "SIMULATION", "physical_ssd": False}),
            record("IO-T7-WRITE-ERROR", REFS["t7"], "PRODUCTION_SOFTWARE_FAULT_INJECTION", "PASS",
                   {"implementation": "srrx.labrx.atomic_json", "injected_errno": "ENOSPC",
                    "error_propagated": True, "last_atomic_snapshot_preserved": True,
                    "temporary_file_cleaned": True, "invalid_parent_fails": True},
                   "A local injected write failure is not USB removal, SSD endurance, fsync power-loss, or mount-identity qualification.")]


@contextlib.contextmanager
def synthetic_storage_binding(root):
    """Inject inventory only; guard dirfd/NOFOLLOW/filesystem IO remain real.

    This deliberately is not a public StorageGuard bypass: production accepts
    only its real /proc inventory and real block devices. The real VM disk test
    belongs to the Linux guest harness, separately from these portable fixtures.
    """
    from srrx import storage
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        mount_id = storage._fd_mount_id(descriptor)
        device_number = os.fstat(descriptor).st_dev
    finally:
        os.close(descriptor)
    device = "/dev/srrx-module-fixture-only"
    identity = (os.major(device_number), os.minor(device_number), device)
    rows = [{"mount_id": mount_id, "major": identity[0], "minor": identity[1],
             "mount_root": "/", "mountpoint": str(root), "options": "rw,relatime",
             "filesystem": "SYNTHETIC_MOUNT_INVENTORY", "source": device}]
    with mock.patch("srrx.storage._read_mountinfo", side_effect=lambda: [dict(row) for row in rows]), \
            mock.patch("srrx.storage._block_identity", return_value=identity):
        with storage.StorageGuard(root, device) as guard:
            yield guard, rows


def guarded_storage_scenarios(root):
    from srrx.labrx import run_capture, atomic_json
    from srrx.storage import StorageRevoked
    from srrx.spectrum import validate_frame
    root = Path(root)
    root.mkdir()
    with synthetic_storage_binding(root) as (guard, rows):
        capture = run_capture(frames=2, fft_size=64, output="spectrum.json",
                              survey="survey.jsonl", storage_guard=guard)
        saved = json.loads((root / "spectrum.json").read_text(encoding="utf-8"))
        require(saved == validate_frame(saved) and capture["raw_iq_persisted"] is False,
                "Guarded production capture did not persist masked metadata")
        require(len((root / "survey.jsonl").read_text(encoding="utf-8").splitlines()) == 2, "Guarded JSONL append failed")
        # Model the configured pathname now referring to a replacement directory.
        # The guard must not write there, or resurrect a missing mount directory.
        detached = root.with_name("detached-storage")
        root.rename(detached)
        root.mkdir()
        rows.clear()
        try:
            atomic_json("fallback/latest.json", {"must_not_write": True}, storage_guard=guard)
        except StorageRevoked:
            pass
        else:
            raise AssertionError("Lost bound mount fell back to replacement root")
        require(guard.revoked and list(root.iterdir()) == [], "Guard wrote to replacement mount pathname")
        require(not list(detached.glob(".srrx-*")), "Lost mount left a staging file")
        try:
            run_capture(frames=1, fft_size=64, output="replay.json", storage_guard=guard)
        except StorageRevoked:
            pass
        else:
            raise AssertionError("Revoked capture restarted without explicit binding")
    positive = record("IO-T7-GUARDED-METADATA", REFS["t7"],
                      "PRODUCTION_GUARD_WITH_INJECTED_MOUNT_BLOCK_INVENTORY", "PASS",
                      {"implementation": "StorageGuard + labrx.run_capture + spectrum.append_survey",
                       "real_dirfd_nofollow_io": True, "simulated_frames": 2,
                       "block_identity_and_mountinfo": "fixture injection, not real block hardware",
                       "raw_iq_persisted": False, "jsonl_append_rollback_on_error": True,
                       "actual_mount_created": False},
                      "Real block-device/mount binding requires the separate Linux virtual-disk test, then actual T7 acceptance.")
    loss = record("IO-T7-GUARDED-MOUNT-LOSS", REFS["t7"],
                  "PRODUCTION_GUARD_WITH_INJECTED_MOUNT_BLOCK_INVENTORY", "PASS",
                  {"configured_path_replaced": True, "mount_inventory_removed": True,
                   "guard_permanently_revoked": True, "replacement_root_files": [],
                   "missing_parent_autocreated": False, "revoked_capture_restart_refused": True,
                   "physical_usb_removal": False})
    return [positive, loss]


def qt_scenarios():
    # Set before lazy Qt import; an externally selected xcb platform is preserved.
    if not os.environ.get("DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6 import __version__ as pyside_version
    from PySide6.QtCore import QEvent, QObject, Qt, qVersion
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QPushButton
    from srrx.hmi import ConsoleController, DemoTransport, create_window

    application = QApplication.instance() or QApplication(["srrx-module-io"])
    transport = DemoTransport(timeout=5.0)
    requests, views = [], []
    gate = {"connected": True}

    def controlled(request):
        requests.append(dict(request))
        if not gate["connected"]:
            raise OSError("synthetic control-link departure")
        return transport(request)

    controller = ConsoleController(controlled)
    window = None

    def until(predicate, description, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            application.processEvents()
            if predicate():
                return
            QTest.qWait(20)
        raise AssertionError("Qt timeout: " + description)

    class InputObserver(QObject):
        def __init__(self):
            super().__init__()
            self.touch_events, self.mouse_events = [], []
            self.mouse_sources = []

        def eventFilter(self, watched, event):
            if event.type() in (QEvent.Type.TouchBegin, QEvent.Type.TouchUpdate, QEvent.Type.TouchEnd):
                self.touch_events.append(int(event.type()))
            if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
                self.mouse_events.append(int(event.type()))
                self.mouse_sources.append(str(event.source()))
            return False

    try:
        # Fixture-only cold-import allowance: no controller poll timestamp/lease exists
        # yet. Every later IPC call keeps the ordinary timeout and unchanged
        # production freshness/lease deadlines.
        startup_at = time.monotonic()
        ordinary_timeout = transport.timeout
        try:
            transport.timeout = 20.0
            startup = transport({"op": "status"})
            startup_data = startup.get("data", {})
            require(startup.get("ok") is True and type(startup_data) is dict
                    and startup_data.get("mode") == "SIMULATION"
                    and startup_data.get("hardware_qualified") is False
                    and startup_data.get("policy", {}).get("simulation") is True,
                    "Cold-start fixture status is not explicit SIMULATION")
        finally:
            transport.timeout = ordinary_timeout
        startup_evidence = {"raw_status_before_controller_poll": True,
                            "cold_start_timeout_s": 20.0, "ordinary_timeout_s": ordinary_timeout,
                            "elapsed_s": round(time.monotonic() - startup_at, 6),
                            "mode": "SIMULATION", "production_deadlines_changed": False}
        initial = controller.poll()
        require(initial["connected"] and initial["data"].get("mode") == "SIMULATION", "Qt fixture is not actual connected SIMULATION")
        window = create_window(controller)
        window.worker.state.connect(views.append)
        window.show()
        until(lambda: len(views) >= 2 and views[-1].get("connected"), "real menu worker status")
        bar = window.tabs.tabBar()
        observer = InputObserver()
        bar.installEventFilter(observer)
        window.installEventFilter(observer)
        window.windowHandle().installEventFilter(observer)
        QTest.mouseClick(bar, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, bar.tabRect(1).center())
        until(lambda: window.tabs.currentIndex() == 1, "mouse navigation to Receiver")
        device = QTest.createTouchDevice()
        point = bar.tabRect(2).center()
        QTest.touchEvent(bar, device, False).press(0, point, bar).commit()
        QTest.qWait(30)
        QTest.touchEvent(bar, device, False).release(0, point, bar).commit()
        until(lambda: window.tabs.currentIndex() == 2, "touch navigation to Spectrum")
        # An actual production button, with no replacement signal handler.
        QTest.mouseClick(bar, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, bar.tabRect(0).center())
        until(lambda: window.tabs.currentIndex() == 0, "Overview navigation")
        diagnostic = next(button for button in window.findChildren(QPushButton)
                          if button.text() == "Controller diagnostics…")
        # The real scroll page may place this button below the initial viewport.
        window.tabs.currentWidget().ensureWidgetVisible(diagnostic)
        QTest.qWait(30)
        require(not window.overview.isVisible(), "Diagnostics unexpectedly visible before tap")
        QTest.mouseClick(diagnostic, Qt.MouseButton.LeftButton)
        until(window.overview.isVisible, "actual button toggles diagnostics")
        require(not controller.status()["holding"], "Navigation created a lease")
        forbidden = {"arm", "recover", "lease", "control", "route", "relay", "shutdown"}
        require(not any(r["op"] in forbidden for r in requests), "Navigation issued power requests")
        positive = record("IO-QT-TOUCH-MOUSE-MENU", REFS["touch"], "PRODUCTION_QT_INPUT_EVENTS", "PASS",
                          {"entrypoint": "srrx.hmi.create_window + real Worker + DemoTransport subprocess",
                           "qt_platform": application.platformName(), "qt": qVersion(), "pyside6": pyside_version,
                           "mouse_receiver_navigation": True, "touch_spectrum_navigation": True,
                           "production_diagnostics_button": True, "touch_events_observed": observer.touch_events,
                           "mouse_events_observed": observer.mouse_events, "mouse_sources": observer.mouse_sources,
                           "touch_delivery": "QTest touchscreen events; QWidget may consume Qt-synthesized mouse events",
                           "startup": startup_evidence,
                           "power_requests": [], "sources": DOCS},
                          "QTest injects generic Qt input. No Linux HID driver, USB touch packet, panel calibration, or Wisecoco factory wiring is qualified.")

        gate["connected"] = False
        until(lambda: not controller.status()["connected"] and "NO CONNECTION" in window.banner.text(),
              "production UI control-link departure")
        require(all(not button.isEnabled() for button in window.output_on_buttons.values()), "Disconnected ON control remains enabled")
        require("unconfirmed" in window.fault_text.text().lower(), "Disconnected UI falsely confirms power state")
        # A disabled real Qt ON button cannot queue an output request.
        window.tabs.setCurrentIndex(5)
        before = len([r for r in requests if r["op"] == "control"])
        QTest.mouseClick(window.output_on_buttons["EN_T7"], Qt.MouseButton.LeftButton)
        QTest.qWait(100)
        require(len([r for r in requests if r["op"] == "control"]) == before, "Disabled control sent an enable")
        gate["connected"] = True
        until(lambda: controller.status()["connected"] and "NO CONNECTION" not in window.banner.text(), "reconnect status")
        view = controller.status()
        require(not view["holding"] and not view["data"]["policy"]["armed"], "Reconnect automatically armed")
        require(not any(r["op"] in forbidden for r in requests), "Disconnect/reconnect issued a power request")
        disconnected = record("IO-QT-CONTROL-LINK-DISCONNECT", REFS["touch"] + REFS["t7"],
                              "PRODUCTION_SOFTWARE_TRANSPORT_FAULT_INJECTION", "PASS",
                              {"link_error_injected": True, "banner_no_connection": True,
                               "power_state_unconfirmed": True, "all_enable_buttons_disabled": True,
                               "disabled_tap_issues_no_control": True, "reconnect_auto_arm": False,
                               "lease_created": False, "worker_connected_snapshots": sum(v.get("connected") is True for v in views)},
                              "The fault is the controller transport, not a USB/HDMI removal signal. Production USB display-departure detection is absent.")
        return [positive, disconnected]
    finally:
        gate["connected"] = True
        try:
            if window is not None:
                window.close()
                try:
                    until(lambda: not window.worker.isRunning(), "clean menu worker exit", timeout=8)
                    window.close()
                    application.processEvents()
                finally:
                    if window.worker.isRunning():
                        window.worker.stopping.set()
                        window.worker.wait(6000)
        finally:
            try:
                controller.close()
            finally:
                transport.close()


def unsupported_records():
    return [
        record("IO-WISECOCO-PHYSICAL", REFS["touch"], "UNSUPPORTED", "UNSUPPORTED",
               {"driver_or_acceptance": "not present", "factory_touch_pinout_verified": False},
               "No physical Wisecoco display/touch firmware, EDID modes, brightness wiring, HDMI backfeed, latency or factory connector pinout acceptance. Generic Qt navigation is a separate result."),
        record("IO-DISPLAY-USB-HOTPLUG-INTERLOCK", REFS["touch"], "UNSUPPORTED", "UNSUPPORTED",
               {"production_usb_display_inventory_service": False, "automatic_disarm_on_display_departure": False},
               "Production HMI does not consume this synthetic inventory. Do not infer USB/HDMI removal interlocks from the control-link outage scenario."),
        record("IO-CH334F-KERNEL", REFS["hub"], "UNSUPPORTED", "UNSUPPORTED",
               {"kernel_usb_driver_exercised": False, "physical_hub": False},
               "No USB kernel hotplug, TT/MTT scheduling, endpoint transfers, port power/overcurrent, hub depth or backfeed verification in this no-USB guest."),
        record("IO-HANTEK-DRIVER", REFS["hantek"], "UNSUPPORTED", "UNSUPPORTED",
               {"srrx_driver": None, "openhantek_executed": False, "firmware_uploaded": False},
               "No in-project Hantek6022BE driver or accepted OpenHantek/FW0210 runtime. Inventory descriptors cannot validate acquisition, voltage calibration or safe electrical connections."),
        record("IO-T7-REMOVABLE-STORAGE", REFS["t7"], "UNSUPPORTED", "UNSUPPORTED",
               {"mount_identity_guard": "implemented, opt-in StorageGuard; fixture tested",
                "guarded_capture_source_cleanup": "implemented; unit tested with injected source",
                "sync_unmount_before_EN_T7_off": False, "uas_or_usb3_verified": False},
               "Physical USB/T7 removal, sustained writes, sync/unmount/power-off and UAS/USB3 remain unqualified. For removable outputs explicitly pair --storage-root/--storage-device; default local writers still create parent directories and must not be mistaken for guarded T7 recording. The guard does not mount, unmount, format or cut power."),
    ]


def run(project=None, output_dir=None, qt=True):
    project = Path(project or Path(__file__).resolve().parents[2]).resolve()
    software = str(project / "software")
    if software not in sys.path:
        sys.path.insert(0, software)
    report = {"suite": "io_modules", "status": "RUNNING", "execution_status": "RUNNING",
              "schema_version": 1, "physical_verified": False, "accepted": False,
              "environment": {"system": platform.system(), "machine": platform.machine(),
                              "uid": os.geteuid() if hasattr(os, "geteuid") else None},
              "modules": [], "scope": "private filesystem USB descriptors + production software/Qt SIMULATION; no host USB or physical hardware"}
    if output_dir is not None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="srrx-module-io-", dir=output_dir) as temporary:
        tasks = [("IO-INVENTORY-SCENARIOS", lambda: inventory_scenarios(Path(temporary) / "usb")),
                 ("IO-STORAGE-SCENARIOS", lambda: storage_scenarios(Path(temporary) / "storage")),
                 ("IO-GUARDED-STORAGE-SCENARIOS", lambda: guarded_storage_scenarios(Path(temporary) / "guarded"))]
        if qt:
            tasks.append(("IO-QT-SCENARIOS", qt_scenarios))
        else:
            report["modules"].append(record("IO-QT-SCENARIOS", REFS["touch"], "NOT_RUN", "UNSUPPORTED",
                                            {"reason": "Qt explicitly disabled"}))
        for identifier, task in tasks:
            try:
                report["modules"].extend(task())
            except Exception as error:
                # Only an absent PySide6 is an environment gap. Any other import
                # error, including a production srrx symbol, is a failed scenario.
                if (identifier == "IO-QT-SCENARIOS" and isinstance(error, ModuleNotFoundError)
                        and (error.name or "").split(".")[0] == "PySide6"):
                    report["modules"].append(record(identifier, REFS["touch"], "MISSING_DEPENDENCY", "UNAVAILABLE",
                                                    {"error": str(error)[:300]}))
                else:
                    report["modules"].append(record(identifier, TASK_REFS[identifier], "EXECUTED_SCENARIO", "FAIL",
                                                    {"error": type(error).__name__ + ": " + str(error)[:500],
                                                     "traceback": traceback.format_exc()[-4000:]}))
    report["modules"].extend(unsupported_records())
    states = {m["status"] for m in report["modules"]}
    report["execution_status"] = ("FAIL" if "FAIL" in states or "PASS" not in states
                                  else "UNAVAILABLE" if "UNAVAILABLE" in states else "PASS")
    report["status"] = {"FAIL": "FAIL", "UNAVAILABLE": "UNAVAILABLE"}.get(report["execution_status"],
                                                                         "EMULATION_PASS_WITH_UNSUPPORTED")
    report["counts"] = {state: sum(m["status"] == state for m in report["modules"])
                        for state in ("PASS", "FAIL", "UNSUPPORTED", "UNAVAILABLE")}
    report["source_sha256"] = {}
    for relative in ("deployment/module_lab/io_modules.py", "deployment/module_lab/io_scenarios.py",
                     "software/srrx/hmi.py", "software/srrx/labrx.py", "software/srrx/spectrum.py",
                     "software/srrx/storage.py"):
        path = project / relative
        if path.is_file():
            report["source_sha256"][relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="JSON report file")
    parser.add_argument("--no-qt", action="store_true")
    args = parser.parse_args(argv)
    report = run(args.project, qt=not args.no_qt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"suite": report["suite"], "status": report["status"], "counts": report["counts"]}))
    return 0 if report["execution_status"] == "PASS" else 2 if report["execution_status"] == "UNAVAILABLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
