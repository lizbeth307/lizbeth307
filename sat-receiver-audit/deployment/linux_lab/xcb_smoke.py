#!/usr/bin/env python3
"""Actual XCB/Xvfb menu smoke; unprivileged Linux ARM64, SIMULATION only.

Bootstrap must start Xvfb as labclient, for example:
  Xvfb :99 -screen 0 1280x800x24 -nolisten tcp
  DISPLAY=:99 python3 /opt/srrx/deployment/linux_lab/xcb_smoke.py \
    --socket /run/srrx-linux-lab/control.sock --output /var/tmp/srrx-xcb-smoke

The first child is the unmodified `python -m srrx.hmi` startup path. A second
child calls the unmodified production main with observation/close Qt timers;
its real worker signals prove live Unix-IPC status, then normal close is tested.
No ARM/control commands are injected. Xvfb is supplied, not started or stopped.
Qt screen captures exercise XCB, not a physical display, touchscreen or Q6A.
"""
from __future__ import annotations

from datetime import datetime, timezone
import argparse
import ctypes as C
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import traceback

from gui_smoke import SmokeFailure, atomic_json, context, require_simulation, summary


class FrameNotReady(SmokeFailure):
    """A mapped/painted frame has not yet met the unchanged quality checks."""


class MappedCLIWindow:
    """Read-only Xlib observation, bound to the actual spawned CLI PID.

    ABI: https://www.x.org/releases/X11R7.6/doc/libX11/specs/libX11/libX11.html
    PID: https://specifications.freedesktop.org/wm/latest/ar01s05.html
    This observes the isolated local Xvfb; it never maps/modifies a window.
    """
    class Attributes(C.Structure):
        _fields_ = [(name, kind) for name, kind in (
            ("x", C.c_int), ("y", C.c_int), ("width", C.c_int), ("height", C.c_int),
            ("border_width", C.c_int), ("depth", C.c_int), ("visual", C.c_void_p),
            ("root", C.c_ulong), ("window_class", C.c_int), ("bit_gravity", C.c_int),
            ("win_gravity", C.c_int), ("backing_store", C.c_int),
            ("backing_planes", C.c_ulong), ("backing_pixel", C.c_ulong),
            ("save_under", C.c_int), ("colormap", C.c_ulong), ("map_installed", C.c_int),
            ("map_state", C.c_int), ("all_event_masks", C.c_long),
            ("your_event_mask", C.c_long), ("do_not_propagate_mask", C.c_long),
            ("override_redirect", C.c_int), ("screen", C.c_void_p))]

    def __init__(self, display, expected_pid):
        local_display(display)
        if type(expected_pid) is not int or expected_pid <= 1:
            raise SmokeFailure("An actual spawned production CLI PID is required")
        self.expected_pid = expected_pid
        self.x = C.CDLL("libX11.so.6")
        signatures = {
            "XOpenDisplay": ([C.c_char_p], C.c_void_p),
            "XCloseDisplay": ([C.c_void_p], C.c_int),
            "XDefaultRootWindow": ([C.c_void_p], C.c_ulong),
            "XInternAtom": ([C.c_void_p, C.c_char_p, C.c_int], C.c_ulong),
            "XQueryTree": ([C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong),
                C.POINTER(C.c_ulong), C.POINTER(C.POINTER(C.c_ulong)), C.POINTER(C.c_uint)], C.c_int),
            "XGetWindowAttributes": ([C.c_void_p, C.c_ulong, C.POINTER(self.Attributes)], C.c_int),
            "XGetWindowProperty": ([C.c_void_p, C.c_ulong, C.c_ulong, C.c_long, C.c_long,
                C.c_int, C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_int),
                C.POINTER(C.c_ulong), C.POINTER(C.c_ulong), C.POINTER(C.c_void_p)], C.c_int),
            "XFree": ([C.c_void_p], C.c_int),
            "XSync": ([C.c_void_p, C.c_int], C.c_int),
            "XSetErrorHandler": ([C.c_void_p], C.c_void_p),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.x, name)
            function.argtypes, function.restype = arguments, result
        self.display = self.x.XOpenDisplay(display.encode("ascii"))
        if not self.display:
            raise SmokeFailure("Cannot observe the actual local X11 display")
        # A transient Qt helper window may disappear between tree/property reads.
        # Suppress that observer connection's X error, then retry a fresh tree.
        self.errors = 0
        def on_error(_display, _event):
            self.errors += 1
            return 0
        self.handler = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_void_p)(on_error)
        self.previous_handler = self.x.XSetErrorHandler(C.cast(self.handler, C.c_void_p))
        self.root = self.x.XDefaultRootWindow(self.display)
        self.pid_atom = self.x.XInternAtom(self.display, b"_NET_WM_PID", 1)
        self.name_atom = self.x.XInternAtom(self.display, b"_NET_WM_NAME", 1)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.x.XCloseDisplay(self.display)
        self.x.XSetErrorHandler(self.previous_handler)

    def property(self, window, atom, length):
        actual, form, count, remaining, data = C.c_ulong(), C.c_int(), C.c_ulong(), C.c_ulong(), C.c_void_p()
        code = self.x.XGetWindowProperty(self.display, window, atom, 0, length, 0, 0,
            C.byref(actual), C.byref(form), C.byref(count), C.byref(remaining), C.byref(data))
        try:
            if code or not data.value or remaining.value:
                return None
            if form.value == 32 and count.value == 1 and actual.value == 6:  # CARDINAL
                return int(C.cast(data, C.POINTER(C.c_ulong))[0])
            if form.value == 8 and count.value <= 1024:
                return C.string_at(data, count.value).decode("utf-8", "replace")
            return None
        finally:
            if data.value:
                self.x.XFree(data)

    def find(self):
        if not self.pid_atom:
            self.pid_atom = self.x.XInternAtom(self.display, b"_NET_WM_PID", 1)
        if not self.name_atom:
            self.name_atom = self.x.XInternAtom(self.display, b"_NET_WM_NAME", 1)
        if not self.pid_atom or not self.name_atom:
            return None
        errors_before = self.errors
        queue, seen = [(self.root, 0)], 0
        while queue:
            parent, depth = queue.pop(0)
            root, above, children, count = C.c_ulong(), C.c_ulong(), C.POINTER(C.c_ulong)(), C.c_uint()
            if not self.x.XQueryTree(self.display, parent, C.byref(root), C.byref(above),
                                     C.byref(children), C.byref(count)):
                continue
            try:
                if count.value > 2048 or seen + count.value > 2048:
                    raise SmokeFailure("X11 observation tree exceeds its bounded size")
                seen += count.value
                for index in range(count.value):
                    window = int(children[index])
                    if depth < 2:
                        queue.append((window, depth + 1))
                    if self.property(window, self.pid_atom, 1) != self.expected_pid:
                        continue
                    name = self.property(window, self.name_atom, 256)
                    if not isinstance(name, str) or not name.startswith("SR-RX"):
                        continue
                    attributes = self.Attributes()
                    if not self.x.XGetWindowAttributes(self.display, window, C.byref(attributes)):
                        continue
                    if attributes.map_state == 2 and attributes.width >= 640 and attributes.height >= 400:  # IsViewable
                        self.x.XSync(self.display, 0)
                        if self.errors == errors_before:
                            return {"window_id": window, "pid": self.expected_pid, "title": name,
                                    "map_state": "IsViewable", "width": attributes.width, "height": attributes.height}
            finally:
                if children:
                    self.x.XFree(children)
        self.x.XSync(self.display, 0)
        return None


def local_display(value):
    if not isinstance(value, str) or not re.fullmatch(r":[0-9]{1,3}(?:\.[0-9]{1,2})?", value):
        raise SmokeFailure("Only an explicit local Unix DISPLAY, such as :99, is allowed")
    number = int(value[1:].split(".", 1)[0])
    return number, ":" + str(number)


def xvfb_evidence(display):
    number, base = local_display(display)
    socket_path = Path("/tmp/.X11-unix") / ("X" + str(number))
    if not stat.S_ISSOCK(socket_path.stat().st_mode):
        raise SmokeFailure("DISPLAY does not have a real X11 Unix socket")
    servers = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != os.geteuid():
                continue
            raw = (entry / "cmdline").read_bytes()
            if len(raw) > 8192:
                continue
            argv = [part.decode("utf-8", "replace") for part in raw.split(b"\0") if part]
            if (argv and Path(argv[0]).name == "Xvfb" and base in argv
                    and any(a == "-nolisten" and b == "tcp" for a, b in zip(argv, argv[1:]))):
                servers.append({"pid": int(entry.name), "uid": os.geteuid(), "argv": argv})
        except (OSError, ValueError):
            continue
    if not servers:
        raise SmokeFailure("No same-UID Xvfb for this DISPLAY with explicit -nolisten tcp")
    for table in (Path("/proc/net/tcp"), Path("/proc/net/tcp6")):
        if not table.exists():
            continue
        for line in table.read_text().splitlines()[1:]:
            fields = line.split()
            if len(fields) >= 4 and fields[3] == "0A" and int(fields[1].rsplit(":", 1)[1], 16) == 6000 + number:
                raise SmokeFailure("An X11 TCP listener exists for this DISPLAY")
    return {"display": display, "unix_socket": str(socket_path),
            "unix_socket_uid": socket_path.stat().st_uid, "servers": servers,
            "explicit_nolisten_tcp": True, "display_tcp_listener": False}


def screenshot(pixmap, path):
    if pixmap.isNull() or pixmap.width() < 640 or pixmap.height() < 400:
        raise FrameNotReady("XCB returned an empty/undersized screen capture")
    image = pixmap.toImage()
    colors = set()
    for y in range(0, image.height(), max(1, image.height() // 40)):
        for x in range(0, image.width(), max(1, image.width() // 50)):
            colors.add(image.pixelColor(x, y).rgba())
    if len(colors) < 4:
        raise FrameNotReady("XCB capture is uniform; rendered widgets were not established")
    if not pixmap.save(str(path), "PNG") or path.stat().st_size < 1000:
        raise SmokeFailure("XCB PNG save failed or was empty")
    return {"path": path.name, "bytes": path.stat().st_size, "width": pixmap.width(),
            "height": pixmap.height(), "sampled_distinct_colors": len(colors),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def qt_child(args):
    from PySide6 import __version__ as pyside_version
    from PySide6.QtCore import QTimer, qVersion
    from PySide6.QtWidgets import QApplication

    result = {"schema_version": 1, "status": "RUNNING", "environment": context(),
              "pyside6": pyside_version, "qt": qVersion(), "mode": args.child,
              "physical_tests_performed": False}
    application = QApplication(sys.argv[:1])
    result["qt_platform"] = application.platformName()
    if application.platformName() != "xcb":
        raise SmokeFailure("The actual Qt platform is not xcb")
    screen = application.primaryScreen()
    if screen is None:
        raise SmokeFailure("No actual X11 screen connection")
    result["screen"] = {"name": screen.name(), "width": screen.geometry().width(),
                        "height": screen.geometry().height()}
    output_path = args.output / (args.child + ".json")
    if args.child == "cli-screen":
        # Interpreter/library startup and X11 first paint have independent timing.
        # Observe the actual CLI window and frame; elapsed sleep is never readiness.
        started, attempts, last_error = time.monotonic(), 0, "Production CLI window is not mapped"
        with MappedCLIWindow(args.display, args.expected_cli_pid) as observer:
            deadline = started + args.timeout
            while time.monotonic() < deadline:
                application.processEvents()
                attempts += 1
                window = observer.find()
                if window is not None:
                    try:
                        capture = screenshot(screen.grabWindow(0), args.output / "production-cli-xcb.png")
                    except FrameNotReady as error:
                        last_error = str(error)
                    else:
                        result.update(production_window=window, screen_capture=capture,
                                      frame_readiness_attempts=attempts,
                                      frame_ready_after_s=round(time.monotonic() - started, 6))
                        break
                time.sleep(.1)
            else:
                raise SmokeFailure("Production CLI mapped/nonuniform frame deadline exceeded: " + last_error)
        result["status"] = "PASS"
        atomic_json(output_path, result)
        return 0

    from srrx.hmi import main as production_main
    import srrx.hmi
    result["entrypoint"] = "unmodified srrx.hmi.main([--socket,...]) with observation/close timers"
    result["hmi_sha256"] = hashlib.sha256(Path(srrx.hmi.__file__).read_bytes()).hexdigest()
    result["touch_events_injected"] = False
    result["arm_or_control_requests_injected"] = False
    started = time.monotonic()
    timer = QTimer(application)
    timer.setInterval(100)
    observed = {"window": None, "connected_views": 0, "first_connected_s": None, "closing": False}

    def view_received(view):
        try:
            if view.get("connected") is not True:
                return
            require_simulation(view.get("data"))
            state = summary(view["data"])
            if state["armed"] or state["energized"] or view.get("holding") is True:
                raise SmokeFailure("Default menu automatically armed, held a lease or energized a load")
            observed["connected_views"] += 1
            if observed["first_connected_s"] is None:
                observed["first_connected_s"] = round(time.monotonic() - started, 6)
            result["latest_service"] = state
        except Exception as error:
            result.update(status="FAIL", error=type(error).__name__ + ": " + str(error)[:400])
            if observed["window"] is not None:
                observed["window"].close()

    def tick():
        try:
            elapsed = time.monotonic() - started
            if elapsed > args.timeout:
                raise SmokeFailure("Production XCB menu did not establish live status in time")
            if observed["window"] is None:
                for widget in application.topLevelWidgets():
                    if widget.windowTitle().startswith("SR-RX") and hasattr(widget, "worker"):
                        observed["window"] = widget
                        widget.worker.state.connect(view_received)
                        break
            window = observed["window"]
            if (window is not None and not observed["closing"] and result["status"] != "FAIL"
                    and elapsed >= 2 and observed["connected_views"] >= 3):
                if not window.isVisible() or "SIMULATION" not in window.banner.text():
                    raise SmokeFailure("Visible production widgets did not show the SIMULATION connection")
                result["window_capture"] = screenshot(window.grab(), args.output / "production-menu-widget-xcb.png")
                result["xserver_capture"] = screenshot(screen.grabWindow(int(window.winId())),
                                                        args.output / "production-menu-xserver-xcb.png")
                result.update(connected_views=observed["connected_views"],
                              first_connected_s=observed["first_connected_s"],
                              capture_after_s=round(elapsed, 6), banner=window.banner.text(),
                              menu_pages=window.tabs.count())
                observed["closing"] = True
                timer.stop()
                window.close()  # Real closeEvent stops worker, DISARMs and closes.
        except Exception as error:
            result.update(status="FAIL", error=type(error).__name__ + ": " + str(error)[:400])
            timer.stop()
            if observed["window"] is not None:
                observed["window"].close()
            else:
                application.quit()

    timer.timeout.connect(tick)
    timer.start()
    code = production_main(["--socket", args.socket])
    timer.stop()
    window = observed["window"]
    result["entrypoint_returncode"] = code
    result["clean_close"] = bool(observed["closing"] and window is not None and not window.worker.isRunning() and code == 0)
    result["elapsed_s"] = round(time.monotonic() - started, 6)
    if result["status"] != "FAIL":
        result["status"] = "PASS" if result["clean_close"] and observed["connected_views"] >= 3 else "FAIL"
    atomic_json(output_path, result)
    return 0 if result["status"] == "PASS" else 1


def orchestrate(args):
    from srrx.daemon import request_once

    args.output.mkdir(parents=True, exist_ok=True)
    result = {"schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "RUNNING", "qualification": "LINUX_XCB_XVFB_SIMULATION",
              "environment": context(), "socket": args.socket, "display": args.display,
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "physical_tests_performed": False, "q6a_tests_performed": False,
              "xvfb_started_or_stopped_by_this_script": False,
              "scope": "Actual XCB/Xvfb visible Qt widgets and Unix SIM service; no physical display/touch or hardware qualification",
              "references": ["https://doc.qt.io/qt-6/qscreen.html",
                             "https://xorg.freedesktop.org/releases/X11R6.9.0/doc/html/Xserver.1.html",
                             "https://www.x.org/releases/X11R7.6/doc/libX11/specs/libX11/libX11.html",
                             "https://specifications.freedesktop.org/wm/latest/ar01s05.html"]}
    children = []
    verified_sim = False
    observation_started = time.monotonic()
    last_observed = None
    consecutive_misses = 0
    observations = {"attempts": 0, "successful_samples": 0, "timeouts": 0,
                    "transient_os_errors": 0, "max_consecutive_misses": 0,
                    "max_success_gap_s": 0.0,
                    "coverage": "Successful read-only Unix status samples only; missing replies do not establish readiness or service state"}
    transient_errnos = {errno.EINTR, errno.EAGAIN, errno.ETIMEDOUT,
                        errno.ECONNRESET, errno.ECONNABORTED, errno.EPIPE}

    def probe(retry_deadline=None):
        nonlocal verified_sim, last_observed, consecutive_misses
        while True:
            remaining = None if retry_deadline is None else retry_deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                raise SmokeFailure("Read-only status observation exceeded the existing child deadline")
            observations["attempts"] += 1
            try:
                reply = request_once(args.socket, {"op": "status"},
                                     timeout=1 if remaining is None else min(1, remaining))
            except (TimeoutError, OSError) as error:
                # Retry transport misses only. Validation below is deliberately
                # outside this handler: an unsafe/rejected reply is fatal.
                if isinstance(error, TimeoutError):
                    observations["timeouts"] += 1
                elif error.errno in transient_errnos:
                    observations["transient_os_errors"] += 1
                else:
                    raise
                consecutive_misses += 1
                observations["max_consecutive_misses"] = max(
                    observations["max_consecutive_misses"], consecutive_misses)
                observations["last_transport_miss"] = type(error).__name__ + ": " + str(error)[:300]
                if retry_deadline is None:
                    raise
                remaining = retry_deadline - time.monotonic()
                if remaining <= 0:
                    raise SmokeFailure("Read-only status observation exceeded the existing child deadline") from error
                time.sleep(min(.1, remaining))
                continue
            break
        if reply.get("ok") is not True:
            raise SmokeFailure("Unix status probe was rejected")
        require_simulation(reply.get("data"))
        verified_sim = True
        state = summary(reply["data"])
        if state["armed"] or state["energized"]:
            raise SmokeFailure("Service was armed/energized during a read-only menu startup test")
        observed_at = time.monotonic()
        if retry_deadline is not None and observed_at >= retry_deadline:
            raise SmokeFailure("Read-only status observation exceeded the existing child deadline")
        if last_observed is not None:
            observations["max_success_gap_s"] = max(
                observations["max_success_gap_s"], observed_at - last_observed)
        else:
            observations["first_success_after_s"] = observed_at - observation_started
        last_observed = observed_at
        observations["successful_samples"] += 1
        consecutive_misses = 0
        return state

    environment = dict(os.environ)
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(args.project / "software") + (os.pathsep + existing if existing else "")
    environment.update(QT_QPA_PLATFORM="xcb", DISPLAY=args.display)

    def launch(command, name):
        error_path = args.output / (name + ".stderr.log")
        with error_path.open("wb") as log:
            child = subprocess.Popen(command, cwd=args.project, env=environment,
                                     stdout=subprocess.DEVNULL, stderr=log)
        children.append(child)
        return child, error_path

    def terminate(child):
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=2)

    def child_run(mode, expected_cli_pid=None):
        path = args.output / (mode + ".json")
        path.unlink(missing_ok=True)
        command = [sys.executable, str(Path(__file__).resolve()), "--child", mode,
            "--project", str(args.project), "--socket", args.socket, "--display", args.display,
            "--output", str(args.output), "--timeout", str(args.timeout)]
        if expected_cli_pid is not None:
            command += ["--expected-cli-pid", str(expected_cli_pid)]
        child, log = launch(command, mode)
        deadline = time.monotonic() + args.timeout + 5
        while child.poll() is None:
            if time.monotonic() >= deadline:
                terminate(child)
                raise SmokeFailure(mode + " child exceeded the bounded deadline")
            probe(retry_deadline=deadline)  # Read-only IPC cannot arm/renew a lease.
            time.sleep(.1)
        # A completed child cannot establish service safety on its own. Require
        # a fresh successful status observation within the same overall bound.
        probe(retry_deadline=deadline)
        code = child.returncode
        if code or not path.exists():
            details = log.read_bytes()[-4000:].decode("utf-8", "replace")
            if path.exists():
                try:
                    details = str(json.loads(path.read_text()).get("error", ""))[:2000] + "\n" + details
                except (OSError, ValueError):
                    pass
            raise SmokeFailure(mode + " XCB child failed " + str(code) + ": " + details)
        value = json.loads(path.read_text())
        if value.get("status") != "PASS" or value.get("qt_platform") != "xcb":
            raise SmokeFailure(mode + " did not prove actual XCB: " + str(value.get("error", value.get("status"))))
        return value

    try:
        actual = result["environment"]
        if actual["system"] != "Linux" or actual["machine"] != args.expect_arch:
            raise SmokeFailure("Expected actual Linux " + args.expect_arch)
        if actual["uid"] == 0 or actual["user"] != args.expect_user:
            raise SmokeFailure("Run as unprivileged " + args.expect_user + ", not root")
        result["xvfb"] = xvfb_evidence(args.display)
        result["initial_service"] = probe()
        command = [sys.executable, "-m", "srrx.hmi", "--socket", args.socket]
        cli, log = launch(command, "production-cli")
        start = time.monotonic()
        capture = child_run("cli-screen", expected_cli_pid=cli.pid)
        result["unmodified_cli"] = {"command": command, "pid": cli.pid,
                                    "alive_after_s": round(time.monotonic() - start, 6),
                                    "screen": capture}
        if cli.poll() is not None:
            raise SmokeFailure("Unmodified CLI exited unexpectedly during XCB capture: " + str(cli.returncode))
        terminate(cli)
        result["unmodified_cli"].update(returncode=cli.returncode,
            termination="SIGTERM with bounded SIGKILL fallback after unarmed startup probe; clean close is established separately by production-main fixture")
        result["production_main_fixture"] = child_run("menu-fixture")
        result["qt_platform"] = result["production_main_fixture"]["qt_platform"]
        result["qt"] = result["production_main_fixture"]["qt"]
        result["pyside6"] = result["production_main_fixture"]["pyside6"]
        result["connection_simulation"] = True
        result["no_armed_or_energized_samples"] = True
        result["auto_arm_observation"] = "No armed or energized state in successful independent Unix status samples and actual GUI worker status samples; unsampled intervals are not continuous observation"
        result["status"] = "PASS"
    except Exception as error:
        result.update(status="FAIL", error=type(error).__name__ + ": " + str(error)[:2000],
                      traceback=traceback.format_exc()[-4000:])
    finally:
        for child in children:
            terminate(child)
        if verified_sim:
            try:
                reply = request_once(args.socket, {"op": "disarm"}, timeout=1)
                result["cleanup_disarm_requested"] = reply.get("ok") is True
                result["final_service"] = probe()
            except Exception as error:
                result.update(status="FAIL", cleanup_error=str(error)[:500])
        ended = time.monotonic()
        observations["elapsed_s"] = round(ended - observation_started, 6)
        observations["max_success_gap_s"] = round(observations["max_success_gap_s"], 6)
        observations["last_success_age_s"] = None if last_observed is None else round(ended - last_observed, 6)
        observations["max_unsampled_gap_s"] = round(max(
            observations["max_success_gap_s"],
            observations.get("first_success_after_s", ended - observation_started),
            ended - (observation_started if last_observed is None else last_observed)), 6)
        if "first_success_after_s" in observations:
            observations["first_success_after_s"] = round(observations["first_success_after_s"], 6)
        result["read_only_observation"] = observations
        atomic_json(args.output / "report.json", result)
    print(json.dumps({"status": result["status"], "report": str(args.output / "report.json")}))
    return 0 if result["status"] == "PASS" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--socket", default="/run/srrx-linux-lab/control.sock")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--display", default=os.environ.get("DISPLAY", ":99"))
    parser.add_argument("--expect-arch", default="aarch64")
    parser.add_argument("--expect-user", default="labclient")
    parser.add_argument("--timeout", type=float, default=30, help="Bounded harness startup deadline; no software interlock is changed")
    parser.add_argument("--child", choices=("cli-screen", "menu-fixture"), help=argparse.SUPPRESS)
    parser.add_argument("--expected-cli-pid", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not 10 <= args.timeout <= 120:
        parser.error("--timeout must be10..120 seconds")
    args.project, args.output = args.project.resolve(), args.output.resolve()
    local_display(args.display)
    sys.path.insert(0, str(args.project / "software"))
    args.output.mkdir(parents=True, exist_ok=True)
    if args.child:
        try:
            return qt_child(args)
        except Exception as error:
            atomic_json(args.output / (args.child + ".json"),
                        {"status": "FAIL", "error": type(error).__name__ + ": " + str(error)[:1000]})
            return 1
    return orchestrate(args)


if __name__ == "__main__":
    raise SystemExit(main())
