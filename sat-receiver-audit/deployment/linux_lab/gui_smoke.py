#!/usr/bin/env python3
"""Actual Linux/Qt/Unix-IPC process-failure smoke; simulation service ONLY.

Run as labclient after guest_smoke.py:
  python3 /opt/srrx/deployment/linux_lab/gui_smoke.py \
    --socket /run/srrx-linux-lab/control.sock --output /var/tmp/srrx-gui-smoke

The child is the real offscreen Qt window/worker. One explicit semantic
RECOVER+ARM and EN_RTLA command replace touch input for this controlled fixture.
The parent independently probes labd, SIGSTOP/SIGCONTs then SIGKILLs children.
No physical backend, touchscreen, SDR, GPIO, I2C, display or Q6A PASS is claimed.
Only harness deadlines scale; the actual 1s renewal/3s lease stay unchanged.
PNG screenshots are saved only while disarmed: their synchronous encoding must
not manufacture a UI-heartbeat failure before the intended process injection.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import grp
import hashlib
import json
import os
from pathlib import Path
import platform
import pwd
import signal
import subprocess
import sys
import time
import traceback


class SmokeFailure(RuntimeError):
    pass


def atomic_json(path, value):
    encoded = json.dumps(value, indent=2, allow_nan=False).encode() + b"\n"
    if len(encoded) > 262144:
        raise SmokeFailure("Smoke JSON exceeds its bounded output size")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)


def read_json(path):
    with path.open("rb") as source:
        encoded = source.read(262145)
    if len(encoded) > 262144:
        raise SmokeFailure("Oversize fixture report")
    return json.loads(encoded)


def context():
    release = {}
    for line in Path("/etc/os-release").read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            release[key] = value.strip('"')
    return {"system": platform.system(), "machine": platform.machine(),
            "kernel": platform.release(), "os_id": release.get("ID"),
            "os_version": release.get("VERSION_ID"), "python": platform.python_version(),
            "uid": os.geteuid(), "user": pwd.getpwuid(os.geteuid()).pw_name,
            "groups": sorted(grp.getgrgid(group).gr_name for group in os.getgroups())}


def require_simulation(data):
    if (not isinstance(data, dict) or data.get("mode") != "SIMULATION"
            or data.get("hardware_qualified") is not False
            or not isinstance(data.get("policy"), dict)
            or data["policy"].get("simulation") is not True):
        raise SmokeFailure("Refusing commands: the service is not explicitly SIMULATION")


def summary(data):
    require_simulation(data)
    policy, pico = data["policy"], data.get("pico", {})
    outputs = policy.get("outputs", {})
    if type(policy.get("armed")) is not bool or not isinstance(outputs, dict):
        raise SmokeFailure("Malformed service status")
    if any(type(value) is not bool for value in outputs.values()):
        raise SmokeFailure("Non-boolean output status")
    controlled = {name: value for name, value in outputs.items()
                  if name.startswith(("EN_", "SW_")) or name in ("K1_ON", "K2_ON")}
    return {"mode": data["mode"], "pico_state": pico.get("state"),
            "pico_reset_asserted": pico.get("mcp_reset") is True,
            "armed": policy["armed"], "fault": policy.get("fault"),
            "owner": policy.get("owner"), "lease_deadline_ms": policy.get("lease_deadline_ms"),
            "outputs": controlled, "energized": sorted(name for name, value in controlled.items() if value)}


def safe(status):
    return not status["armed"] and not status["energized"] and status["pico_reset_asserted"]


def child_environment(project):
    value = dict(os.environ)
    prefix = str(project / "software")
    value["PYTHONPATH"] = prefix + (os.pathsep + value["PYTHONPATH"] if value.get("PYTHONPATH") else "")
    value["QT_QPA_PLATFORM"] = "offscreen"
    value.setdefault("QT_LOGGING_RULES", "qt.qpa.*=false")
    return value


def fixture(args):
    """Actual QApplication event loop; the actual ConsoleController owns lease."""
    if not args.explicit_sim_arm:
        raise SmokeFailure("The internal fixture requires --explicit-sim-arm")
    from PySide6 import __version__ as pyside_version
    from PySide6.QtCore import QTimer, qVersion
    from PySide6.QtWidgets import QApplication
    from srrx.daemon import request_once
    from srrx.hmi import ConsoleController, create_window

    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / ("fixture-" + args.fixture + ".json")
    calls, actions = Counter(), []
    accepted_leases = []
    started = time.monotonic()
    state = {"schema_version": 1, "fixture": args.fixture, "pid": os.getpid(),
             "uid": os.geteuid(), "stage": "STARTING", "qt_platform": "offscreen",
             "pyside6": pyside_version, "qt": qVersion(), "screenshots": [],
             "scope": "real full Qt window/worker; semantic queue actions, no touch injection",
             "physical_tests_performed": False, "action_log": actions}

    def transport(request):
        calls[request["op"]] += 1
        if request["op"] in ("arm", "recover", "control", "disarm", "shutdown"):
            actions.append({"operation": request["op"], "at_s": round(time.monotonic() - started, 6),
                            "name": request.get("name"), "value": request.get("value")})
            if len(actions) > 64:
                raise SmokeFailure("Unexpected repeated fixture actions")
        result = request_once(args.socket, request, timeout=.4)
        if request["op"] == "lease" and result.get("ok") is True:
            accepted_leases.append(time.monotonic())
            del accepted_leases[:-64]
        return result

    controller = ConsoleController(transport)
    initial = controller.poll()
    if not initial["connected"]:
        raise SmokeFailure("The unprivileged GUI cannot read the Unix socket: " + str(initial.get("error")))
    require_simulation(initial["data"])
    application = QApplication(sys.argv[:1])
    window = create_window(controller)
    window.resize(1100, 800)
    window.show()
    timer = QTimer()
    timer.setInterval(100)
    last_tick = started
    tick_count, tick_sum, tick_max = 0, 0.0, 0.0
    active_at = None
    boot_rendered = False
    warmup_finished_at = None
    final_code = 0

    def capture(label):
        current = controller.status()
        observed = summary(current["data"])
        if current["holding"] or observed["armed"] or observed["energized"]:
            raise SmokeFailure("Screenshots are permitted only while disarmed with loads OFF")
        image = window.grab()
        target = args.output / (args.fixture + "-" + label + ".png")
        if image.isNull() or not image.save(str(target), "PNG"):
            raise SmokeFailure("Actual Qt screenshot failed")
        state["screenshots"].append({"path": target.name, "bytes": target.stat().st_size,
            "width": image.width(), "height": image.height(),
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})

    def tick():
        nonlocal last_tick, tick_count, tick_sum, tick_max, active_at, boot_rendered, warmup_finished_at, final_code
        try:
            now = time.monotonic()
            gap = (now - last_tick) * 1000
            last_tick = now
            tick_count, tick_sum, tick_max = tick_count + 1, tick_sum + gap, max(tick_max, gap)
            state["elapsed_s"] = round(now - started, 6)
            state["request_counts"] = dict(calls)
            state["accepted_lease_at_s"] = [round(at - started, 6) for at in accepted_leases]
            state["qt_timer"] = {"interval_ms": 100, "ticks": tick_count,
                                 "mean_gap_ms": round(tick_sum / tick_count, 3),
                                 "max_gap_ms_including_SIGSTOP": round(tick_max, 3)}
            view = controller.status()
            require_simulation(view["data"])
            status = summary(view["data"])
            state["service"] = status
            state["holding"] = view["holding"]
            state["controller_notice"] = view["notice"]
            state["controller_error"] = view["error"]
            if now - started > args.fixture_timeout:
                raise SmokeFailure("Fixture hard deadline exceeded")
            if not boot_rendered and now - started >= .5 and view["connected"]:
                # Font/layout warmup occurs while disarmed, before the real lease.
                capture("startup-disarmed")
                boot_rendered = True
                warmup_finished_at = time.monotonic()
                state["stage"] = "WARMED_DISARMED"
                state["warmup_finished_s"] = round(warmup_finished_at - started, 6)
                atomic_json(path, state)
                return  # Let the real Qt timers/worker run after expensive PNG work.
            if state["stage"] == "WARMED_DISARMED":
                # Observe a natural window heartbeat AND a service poll after
                # screenshot work. Do not write ui_at or fake a controller clock.
                if (view["connected"] and window.worker.ui_at > warmup_finished_at
                        and controller.last_poll is not None
                        and controller.last_poll > warmup_finished_at):
                    state["stage"] = "READY_DISARMED"
                    state["natural_heartbeat_s"] = round(window.worker.ui_at - started, 6)
                    state["fresh_poll_s"] = round(controller.last_poll - started, 6)
                atomic_json(path, state)
                return  # ARM is a separate, subsequent Qt timer action.
            if state["stage"] == "READY_DISARMED":
                if status["armed"]:
                    raise SmokeFailure("A different client already armed the test service")
                if (view["connected"] and time.monotonic() - window.worker.ui_at <= 1.0
                        and status["pico_state"] in ("SAFE", "TRIPPED")):
                    window.worker.submit("recover")  # Explicit controlled SIM operator action, once.
                    state["stage"] = "ARM_REQUESTED"
                    state["arm_requested_s"] = round(now - started, 6)
            elif state["stage"] == "ARM_REQUESTED" and status["armed"] and view["holding"]:
                window.worker.submit("control", {"name": "EN_RTLA", "value": True})
                state["stage"] = "OUTPUT_REQUESTED"
                active_at = now
                state["active_s"] = round(now - started, 6)
            elif state["stage"] == "OUTPUT_REQUESTED" and status["outputs"].get("EN_RTLA") is True:
                deadline = status.get("lease_deadline_ms")
                remaining = deadline - int(now * 1000) if type(deadline) is int else -1
                # Engine's initial ARM grant is 5s. Wait for an actual subsequent
                # GUI renewal to its configured 3s lease before fault injection.
                renewed_after_active = any(at > active_at for at in accepted_leases)
                if now - active_at >= 1.2 and renewed_after_active and 1000 <= remaining <= 3100:
                    # Real status/lease JSON proves the armed state. Synchronous
                    # PNG encoding here would itself stall the protected UI.
                    state["stage"] = "ACTIVE_STABLE"
                    state["stable_s"] = round(now - started, 6)
                    state["remaining_lease_ms"] = remaining
            elif (state["stage"] == "ACTIVE_STABLE" and not view["holding"]
                    and not status["armed"] and not status["energized"]):
                capture("resumed-disarmed")
                state["stage"] = "HOLD_STOPPED"
                state["hold_stopped_s"] = round(now - started, 6)
            atomic_json(path, state)
        except Exception as error:
            final_code = 1
            state.update(stage="FAILED", error=type(error).__name__ + ": " + str(error)[:400],
                         traceback=traceback.format_exc()[-4000:])
            atomic_json(path, state)
            timer.stop()
            window.close()

    signal.signal(signal.SIGTERM, lambda *_: window.close())
    timer.timeout.connect(tick)
    timer.start()
    try:
        application.exec()
    finally:
        timer.stop()
        controller.close()
        state["exit_requests"] = dict(calls)
        state["closed"] = controller.closed
        atomic_json(path, state)
    return final_code


def orchestrate(args):
    from srrx.daemon import request_once

    args.output.mkdir(parents=True, exist_ok=True)
    report_path = args.output / "report.json"
    report = {"schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "RUNNING", "environment": context(), "socket": args.socket,
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "physical_tests_performed": False, "q6a_tests_performed": False,
              "scope": "real Linux Unix IPC, unprivileged real offscreen Qt worker and process failures; all controlled loads are simulated",
              "touch_events_injected": False, "service_started_or_enabled_by_this_script": False,
              "screenshots_only_while_disarmed": True,
              "configured_gui_renewal_ms": 1000, "configured_gui_lease_ms": 3000,
              "cases": [], "limitations": ["No physical GPIO/I2C/UART/SDR/display exercised",
                  "Offscreen screenshots do not establish touch/glove/sunlight performance",
                  "Observed guest timings do not qualify Q6A or hard real-time behavior"]}
    children = []
    verified_sim = False
    probe_ms = []

    def probe():
        nonlocal verified_sim
        before = time.monotonic()
        value = request_once(args.socket, {"op": "status"}, timeout=1.0)
        probe_ms.append((time.monotonic() - before) * 1000)
        if value.get("ok") is not True:
            raise SmokeFailure("Independent status probe was rejected")
        data = value.get("data")
        require_simulation(data)
        verified_sim = True
        return summary(data)

    def wait_for(predicate, timeout, message, child=None):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if child is not None and child.poll() is not None:
                raise SmokeFailure(message + ": GUI exited " + str(child.returncode))
            value = predicate()
            if value:
                return value
            time.sleep(.1)
        raise SmokeFailure(message + ": deadline exceeded")

    def launch(name):
        path = args.output / ("fixture-" + name + ".json")
        path.unlink(missing_ok=True)
        error_log = (args.output / (name + "-qt.stderr.log")).open("wb")
        child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
            "--fixture", name, "--explicit-sim-arm", "--socket", args.socket,
            "--project", str(args.project), "--output", str(args.output),
            "--fixture-timeout", str(45 * args.timeout_scale)], cwd=args.project,
            env=child_environment(args.project), stdout=subprocess.DEVNULL, stderr=error_log)
        error_log.close()
        children.append(child)

        def ready():
            if not path.exists():
                return None
            value = read_json(path)
            if value.get("stage") == "FAILED":
                raise SmokeFailure(value.get("error", "GUI fixture failed"))
            return value if value.get("stage") == "ACTIVE_STABLE" else None

        ready_state = wait_for(ready, 20 * args.timeout_scale, "Qt explicit ARM/output setup failed", child)
        status = probe()
        if not status["armed"] or status["outputs"].get("EN_RTLA") is not True:
            raise SmokeFailure("No actual armed simulated load before fault injection")
        if status.get("owner") != "uid:" + str(os.geteuid()):
            raise SmokeFailure("Lease owner does not match the unprivileged GUI UID")
        return child, path, ready_state, status

    def expiry(start, case):
        observations = []
        result = {"expected_policy_fault": "owner lease expired", "lease_expiry_cause_confirmed": False,
                  "observations": observations}
        case["expiry"] = result  # Preserve the observed timeline even on failure.
        first_policy_off = None
        until = time.monotonic() + 7 * args.timeout_scale
        while time.monotonic() < until:
            value = probe()
            elapsed = round(time.monotonic() - start, 6)
            if len(observations) < 100:
                observations.append({"elapsed_s": elapsed, **value})
            if not value["armed"] and not value["energized"] and first_policy_off is None:
                first_policy_off = elapsed
            if safe(value):
                result.update(policy_off_after_s=first_policy_off, reset_observed_after_s=elapsed, final=value)
                if value.get("fault") != "owner lease expired":
                    raise SmokeFailure("Safe outputs were caused by an unrelated trip, not lease expiry: "
                                       + str(value.get("fault")))
                result["lease_expiry_cause_confirmed"] = True
                return result
            time.sleep(.1)
        raise SmokeFailure("GUI lost execution but service did not disarm/assert simulated reset in time")

    def terminate(child):
        if child.poll() is not None:
            return
        child.send_signal(signal.SIGCONT)
        child.terminate()
        try:
            child.wait(timeout=5 * args.timeout_scale)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=2)

    def stopped_state(child):
        status = Path("/proc") / str(child.pid) / "status"
        for line in status.read_text().splitlines():
            if line.startswith("State:"):
                description = line.split(":", 1)[1].strip()
                return description if description.startswith("T ") else None
        return None

    try:
        actual = report["environment"]
        if actual["system"] != "Linux" or actual["machine"] != args.expect_arch:
            raise SmokeFailure("Expected Linux " + args.expect_arch + "; observed " + str(actual))
        if actual["os_id"] + ":" + actual["os_version"] != args.expect_os:
            raise SmokeFailure("Unexpected Linux distribution/version")
        if os.geteuid() == 0:
            raise SmokeFailure("Run this test as unprivileged labclient, not root")
        initial = probe()
        report["initial"] = initial
        if initial["armed"] or initial["energized"]:
            raise SmokeFailure("Simulation service must start disarmed with controlled loads OFF")

        child, path, ready_state, before = launch("pause")
        case = {"name": "qt_SIGSTOP_expiry_SIGCONT_no_auto_rearm", "status": "RUNNING",
                "fixture_before": ready_state, "service_before": before}
        report["cases"].append(case)
        stopped = time.monotonic()
        child.send_signal(signal.SIGSTOP)
        case["proc_state_after_SIGSTOP"] = wait_for(lambda: stopped_state(child), 2,
            "SIGSTOP did not produce a stopped Linux process", child)
        case["expiry"] = expiry(stopped, case)
        case["stopped_process_alive"] = child.poll() is None
        resumed = time.monotonic()
        child.send_signal(signal.SIGCONT)

        def gui_stopped_hold():
            value = read_json(path)
            return value if value.get("stage") == "HOLD_STOPPED" and value.get("holding") is False else None

        resumed_state = wait_for(gui_stopped_hold, 5 * args.timeout_scale, "Resumed Qt did not stop HOLD", child)
        quiet_until = time.monotonic() + 2
        while time.monotonic() < quiet_until:
            if not safe(probe()):
                raise SmokeFailure("Resumed Qt automatically re-armed or enabled a controlled load")
            time.sleep(.1)
        case["resume_observed_after_s"] = round(time.monotonic() - resumed, 6)
        case["fixture_after_resume"] = resumed_state
        if resumed_state["request_counts"].get("arm", 0) or resumed_state["request_counts"].get("recover", 0) != 1:
            raise SmokeFailure("GUI emitted an unexpected extra ARM/recovery")
        case["status"] = "PASS"
        terminate(child)

        child, path, ready_state, before = launch("kill")
        case = {"name": "qt_SIGKILL_expiry", "status": "RUNNING",
                "fixture_before": ready_state, "service_before": before}
        report["cases"].append(case)
        killed = time.monotonic()
        child.kill()
        child.wait(timeout=2)
        case["process_returncode"] = child.returncode
        if child.returncode != -signal.SIGKILL:
            raise SmokeFailure("GUI was not actually killed by SIGKILL")
        case["expiry"] = expiry(killed, case)
        case["status"] = "PASS"
        report["status"] = "PASS_LINUX_OFFSCREEN_SIMULATION"
    except Exception as error:
        report.update(status="FAIL", error=type(error).__name__ + ": " + str(error)[:600],
                      traceback=traceback.format_exc()[-5000:])
    finally:
        if verified_sim:
            try:
                result = request_once(args.socket, {"op": "disarm"}, timeout=1)
                report["cleanup_disarm_requested"] = result.get("ok") is True
            except Exception as error:
                report["cleanup_error"] = str(error)[:300]
        for child in children:
            terminate(child)
        if verified_sim:
            try:
                report["final"] = wait_for(lambda: (value if safe(value := probe()) else None),
                    3 * args.timeout_scale, "Final safe state unconfirmed")
            except Exception as error:
                report.update(status="FAIL", cleanup_error=str(error)[:400])
        if probe_ms:
            ordered = sorted(probe_ms)
            report["independent_unix_status_rtt_ms"] = {"samples": len(ordered),
                "min": round(ordered[0], 3), "median": round(ordered[len(ordered) // 2], 3),
                "p95": round(ordered[min(len(ordered) - 1, int(len(ordered) * .95))], 3),
                "max": round(ordered[-1], 3)}
        atomic_json(report_path, report)
    print(json.dumps({"status": report["status"], "report": str(report_path)}, allow_nan=False))
    return 0 if report["status"] == "PASS_LINUX_OFFSCREEN_SIMULATION" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--socket", default="/run/srrx-linux-lab/control.sock")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect-arch", default="aarch64", help="Harness assertion; override explicitly for host development only")
    parser.add_argument("--expect-os", default="ubuntu:24.04")
    parser.add_argument("--timeout-scale", type=float, default=1.0, help="Harness deadlines only; actual GUI lease is unchanged")
    parser.add_argument("--fixture", choices=("pause", "kill"), help=argparse.SUPPRESS)
    parser.add_argument("--explicit-sim-arm", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--fixture-timeout", type=float, default=45, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not 1 <= args.timeout_scale <= 5 or not 10 <= args.fixture_timeout <= 225:
        parser.error("Harness timeout settings exceed bounds")
    args.project, args.output = args.project.resolve(), args.output.resolve()
    sys.path.insert(0, str(args.project / "software"))
    if args.fixture:
        try:
            return fixture(args)
        except Exception as error:
            atomic_json(args.output / ("fixture-" + args.fixture + ".json"),
                        {"stage": "FAILED", "error": type(error).__name__ + ": " + str(error)[:600]})
            return 1
    return orchestrate(args)


if __name__ == "__main__":
    raise SystemExit(main())
