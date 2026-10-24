#!/usr/bin/env python3
"""Guest-only systemd/AF_UNIX acceptance smoke; never hardware acceptance.

Run as root in the explicitly marked, disposable QEMU ARM64 Ubuntu guest.
The production hardware unit is tested only with missing/OPEN records. A
separate simulation unit retains the shipped service sandbox and is left
running, disarmed, for the unprivileged GUI smoke. No unit is enabled, no
poweroff service is started and no physical device or acceptance is created.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import grp
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import pwd
import re
import select
import stat
import subprocess
import sys
import tempfile
import time

SIM_UNIT = "srrx-linux-lab-sim.service"
SOCKET = "/run/srrx-linux-lab/control.sock"
MARKER = "/etc/srrx-linux-lab.json"
REPORT = "/var/lib/srrx-linux-lab/system-smoke.json"
UNIT_DIR = Path("/etc/systemd/system")
# DEP-11 probe: a /dev/lab node that never appears in this guest, two throwaway units
# (removed again; guest_bootstrap.sh also clears these fixed paths) and a short device timeout.
DEVICE_PROBE = "/dev/lab/srrxabsent"
DEVWAIT_UNIT = "srrx-linux-lab-devwait.service"
DEVRETRY_UNIT = "srrx-linux-lab-devretry.service"
PROBE_TIMEOUT_S = 3
REQUIRED_STEPS = (
    "guest_boundary", "candidate_stage", "systemd_device_wait_bounded", "hardware_missing_records",
    "hardware_open_records", "installed_entrypoints_stdio", "systemd_simulation",
    "single_writer", "client_permissions", "explicit_arm_and_fault",
    "link_loss_latched", "lease_expiry_latched", "simulation_shutdown",
    "systemd_restart_disarmed", "gui_handoff",
)


class SmokeError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise SmokeError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_guest_facts(facts, marker):
    """Pure checks, separate from collection so the host-rejection is testable."""
    require(facts["uid"] == 0, "guest smoke requires root inside the disposable guest")
    require(facts["architecture"] == "aarch64", "requires actual ARM64 Linux userspace")
    require(facts["system"] == "Linux" and facts["pid1"] == "systemd", "requires Linux with systemd as PID 1")
    require(facts["distribution"] == {"ID": "ubuntu", "VERSION_ID": "24.04", "VERSION_CODENAME": "noble"},
            "requires the Ubuntu 24.04 noble guest")
    require(facts["network_interfaces"] == ["lo"], "guest must have no network interface except loopback")
    require(type(marker) is dict and marker.get("schema_version") == 1
            and type(marker.get("schema_version")) is int
            and marker.get("environment") == "qemu-arm64-linux-lab"
            and marker.get("hardware_passthrough") is False,
            "missing or invalid explicit disposable-guest marker")
    return facts


def validate_pico_group(group, client):
    """srrx-pico guards the Pico UART: labd gets it only via SupplementaryGroups, no login user holds it."""
    require(client.pw_name not in group.gr_mem and client.pw_gid != group.gr_gid, "labclient must not be in srrx-pico")
    require(not group.gr_mem, "srrx-pico must be a member-less group: " + ",".join(group.gr_mem))
    return group


def release_guard_exited_2(exec_start_pre):
    """systemctl show prints 'status=2' for the guard's exit 2; 216 (GROUP) or a signal must not match."""
    return re.search(r"\bstatus=2(?![\d/])", exec_start_pre) is not None


def guard_environment(project, marker_path):
    require(project == Path("/opt/srrx"), "project must be the installed /opt/srrx tree")
    require(project.is_dir() and not project.is_symlink(), "/opt/srrx must be a real directory")
    marker_path = Path(marker_path)
    info = marker_path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022,
            "guest marker must be a root-owned regular file without group/world write access")
    release = {}
    for line in Path("/etc/os-release").read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            release[key] = value.strip('"')
    facts = {"uid": os.geteuid(), "architecture": platform.machine(), "system": platform.system(),
             "pid1": Path("/proc/1/comm").read_text().strip(), "kernel": platform.release(),
             "distribution": {k: release.get(k) for k in ("ID", "VERSION_ID", "VERSION_CODENAME")},
             "network_interfaces": sorted(p.name for p in Path("/sys/class/net").iterdir())}
    validate_guest_facts(facts, json.loads(marker_path.read_text()))
    require(Path("/run/systemd/private").exists(), "systemd manager socket is missing")
    require(not list(Path("/dev").glob("i2c-*")) and not Path("/dev/lab/pico").exists(),
            "physical SR-RX device nodes must not be present in the guest")
    # srrx.service has SupplementaryGroups=i2c dialout srrx-pico: a missing group is 216/GROUP, not the guard.
    for group in ("labd", "i2c", "dialout", "srrx-pico"):
        grp.getgrnam(group)
    user, group = pwd.getpwnam("labclient"), grp.getgrnam("labd")
    require(user.pw_uid != 0 and pwd.getpwnam("labd").pw_uid != 0, "lab users must be unprivileged")
    require(group.gr_gid == user.pw_gid or "labclient" in group.gr_mem, "labclient must be a member of labd")
    validate_pico_group(grp.getgrnam("srrx-pico"), user)
    return facts


def simulation_unit(shipped):
    """Keep production sandbox directives; replace only hardware bindings."""
    require("--hardware" in shipped and "ExecStart=" in shipped, "unexpected shipped hardware unit")
    removed = ("ConditionPathExists=", "EnvironmentFile=", "SupplementaryGroups=")
    lines = []
    for line in shipped.splitlines():
        if line == "[Install]":
            break
        if line.startswith(removed):
            continue
        if line.startswith("Description="):
            line = "Description=SR-RX isolated Linux laboratory simulation (no hardware)"
        elif line.startswith("ExecStart="):
            line = "ExecStart=/usr/bin/python3 -m srrx.daemon --simulate --project /opt/srrx --socket " + SOCKET
        elif line.startswith("RuntimeDirectory="):
            line = "RuntimeDirectory=srrx-linux-lab"
        lines.append(line)
    text = "\n".join(lines).rstrip() + "\nPrivateDevices=yes\nDevicePolicy=closed\nCapabilityBoundingSet=\n"
    require("--hardware" not in text and "[Install]" not in text, "simulation unit has a hardware/enable path")
    return text


def load_deploy(project):
    """The installed generator itself (deployment/deploy.py), not a copy of its drop-in text."""
    spec = importlib.util.spec_from_file_location("srrx_guest_deploy", Path(project) / "deployment/deploy.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def device_probe_units():
    """Throwaway units that carry the generated srrx.service device ordering; no hardware, no [Install]."""
    head = "[Unit]\nDescription=SR-RX Linux lab device-wait probe (no hardware)\n\n[Service]\n"
    return {DEVWAIT_UNIT: head + "Type=oneshot\nExecStart=/bin/true\n",
            # Same shape as the release guard: ExecStartPre fails, Restart=on-failure retries.
            DEVRETRY_UNIT: head + "Type=simple\nExecStartPre=/bin/false\nExecStart=/bin/true\nRestart=on-failure\nRestartSec=1\n"}


def assert_simulation(status, safe=False):
    require(type(status) is dict and status.get("mode") == "SIMULATION"
            and status.get("hardware_qualified") is False, "response must explicitly remain unqualified SIMULATION")
    policy = status.get("policy", {})
    require(policy.get("simulation") is True, "physical backend was unexpectedly selected")
    if safe:
        require(policy.get("armed") is False, "policy must be disarmed")
        outputs = policy.get("outputs")
        require(type(outputs) is dict and bool(outputs) and outputs.get("CHG_INHIBIT") is True,
                "safe output image must assert CHG_INHIBIT")
        require(all(type(value) is bool and value is False for name, value in outputs.items() if name != "CHG_INHIBIT"),
                "all switched outputs must be off")
    return status


CLIENT = r'''import json,socket,sys
s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.settimeout(3)
s.connect(sys.argv[1]); s.sendall(sys.argv[2].encode()+b'\n'); data=bytearray()
while b'\n' not in data:
    block=s.recv(8192)
    if not block: raise RuntimeError('service closed without JSON')
    data.extend(block)
    if len(data)>65536: raise RuntimeError('oversize response')
s.close(); print(data.split(b'\n',1)[0].decode())
'''


PERSISTENT_CLIENT = r'''import json,os,socket,sys
def send(value):
    data=json.dumps(value,allow_nan=False,separators=(',',':')).encode()+b'\n'
    if len(data)>66560: raise RuntimeError('helper response exceeds bound')
    sys.stdout.buffer.write(data); sys.stdout.buffer.flush()
send({'ready':True,'uid':os.geteuid(),'gid':os.getegid(),'groups':os.getgroups()})
while True:
    line=sys.stdin.buffer.readline(8193)
    if not line: break
    if len(line)>8192 or not line.endswith(b'\n'):
        send({'delivered':False,'error':'bounded newline request required'}); break
    try:
        request=json.loads(line)
        if type(request) is not dict: raise ValueError('request object required')
        # Each request still uses the production Unix server and kernel peer UID.
        # Only interpreter startup is shared; neither RPC nor server is mocked.
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
            connection.settimeout(3)
            connection.connect(sys.argv[1]); connection.sendall(line)
            data=bytearray()
            while b'\n' not in data:
                block=connection.recv(min(8192,65537-len(data)))
                if not block: raise RuntimeError('service closed without JSON')
                data.extend(block)
                if len(data)>65536: raise RuntimeError('oversize response')
        reply=json.loads(data.split(b'\n',1)[0])
        send({'delivered':True,'reply':reply})
    except Exception as error:
        send({'delivered':False,'error':type(error).__name__+': '+str(error)[:500]})
'''


class PersistentRPC:
    """One unprivileged interpreter, real per-request sockets, bounded pipes."""
    def __init__(self, socket_path, client, group, env):
        require(client.pw_uid != 0, "persistent client must be unprivileged")
        self.process = subprocess.Popen(
            ["/usr/bin/python3", "-I", "-B", "-u", "-c", PERSISTENT_CLIENT, str(socket_path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            cwd="/", env=env, user=client.pw_uid, group=client.pw_gid,
            extra_groups=[group.gr_gid], bufsize=0)
        self.closed, self.requests = False, 0
        try:
            os.set_blocking(self.process.stdin.fileno(), False)
            os.set_blocking(self.process.stdout.fileno(), False)
            ready = self._read(time.monotonic() + 15)
            require(ready.get("ready") is True and ready.get("uid") == client.pw_uid
                    and group.gr_gid in [ready.get("gid"), *ready.get("groups", [])],
                    "persistent client UID/group differs from real labclient")
            self.identity = {"pid": self.process.pid, "uid": ready["uid"], "gid": ready["gid"],
                             "groups": ready["groups"], "per_request_unix_connection": True}
        except BaseException:
            self.close()
            raise

    def _read(self, deadline):
        data, fd = bytearray(), self.process.stdout.fileno()
        while b"\n" not in data:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([fd], [], [], remaining)[0]:
                raise SmokeError("persistent RPC reply deadline exceeded")
            block = os.read(fd, min(8192, 66561-len(data)))
            if not block:
                raise SmokeError("persistent RPC helper exited before a complete reply")
            data.extend(block)
            require(len(data) <= 66560, "persistent RPC reply exceeds bound")
        line, extra = data.split(b"\n", 1)
        require(not extra, "persistent RPC helper returned unsolicited data")
        value = json.loads(line)
        require(type(value) is dict, "persistent RPC reply must be an object")
        return value

    def request(self, request):
        require(not self.closed and self.process.poll() is None, "persistent RPC helper is closed")
        encoded = json.dumps(request, allow_nan=False, separators=(",", ":")).encode() + b"\n"
        require(len(encoded) <= 8192, "persistent RPC request exceeds bound")
        deadline, pending = time.monotonic() + 8, memoryview(encoded)
        try:
            fd = self.process.stdin.fileno()
            while pending:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([], [fd], [], remaining)[1]:
                    raise SmokeError("persistent RPC write deadline exceeded")
                count = os.write(fd, pending)
                require(count > 0, "persistent RPC request pipe closed")
                pending = pending[count:]
            self.requests += 1
            reply = self._read(deadline)
        except BaseException:
            # A timed-out mutating request may already have reached the server.
            # Never restart/replay it automatically under a fresh interpreter.
            self.close()
            raise
        require(reply.get("delivered") is True, "Unix RPC failed: " + str(reply.get("error", "invalid helper reply")))
        require(type(reply.get("reply")) is dict, "Unix RPC server reply must be an object")
        return reply["reply"]

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            self.process.stdin.close()
        except OSError:
            pass
        try:
            self.process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=1)
        finally:
            self.process.stdout.close()


class GuestSmoke:
    def __init__(self, project, report):
        self.project, self.report_path = project, report
        self.client = pwd.getpwnam("labclient")
        self.group = grp.getgrnam("labd")
        self.data = {"schema_version": 1, "scope": "QEMU_ARM64_LINUX_SIMULATION_ONLY", "status": "RUNNING",
                     "started_at": datetime.now(timezone.utc).isoformat(), "hardware_qualified": False,
                     "hardware_acceptance_generated": False, "services_enabled": False,
                     "host_poweroff_requested": False, "steps": [], "required_steps": list(REQUIRED_STEPS)}
        self.stage = None
        self.sim_started = False
        self.rpc_client = None

    def command(self, args, *, accepted=(0,), client=False, input=None, timeout=30, env=None):
        kwargs = {}
        if client:
            kwargs.update(user=self.client.pw_uid, group=self.client.pw_gid, extra_groups=[self.group.gr_gid])
        result = subprocess.run([str(a) for a in args], input=input, capture_output=True, text=True,
                                cwd="/", timeout=timeout, env=env, **kwargs)
        require(result.returncode in accepted, f"command failed ({result.returncode}): {args!r}: {result.stderr[-3000:]}")
        return result

    def step(self, name, operation):
        started = time.monotonic()
        try:
            evidence = operation()
            self.data["steps"].append({"name": name, "status": "PASS", "elapsed_s": round(time.monotonic()-started, 3),
                                       "evidence": evidence})
        except Exception as exc:
            self.data["steps"].append({"name": name, "status": "FAIL", "error": str(exc)[:5000]})
            raise

    def systemctl(self, *args, accepted=(0,)):
        return self.command(["/usr/bin/systemctl", *args], accepted=accepted)

    def properties(self, unit=SIM_UNIT):
        fields = ("ActiveState", "SubState", "MainPID", "ExecMainPID", "ExecMainStartTimestampMonotonic", "NRestarts",
                  "Result", "ConditionResult", "ExecStartPre", "User", "Group", "NoNewPrivileges", "ProtectSystem",
                  "ProtectHome", "PrivateTmp", "PrivateDevices", "DevicePolicy", "RestrictAddressFamilies",
                  "ProtectKernelTunables", "ProtectKernelModules", "ProtectControlGroups", "RuntimeDirectory", "UnitFileState")
        result = self.systemctl("show", unit, *("--property="+p for p in fields))
        return dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)

    def rpc(self, request, *, expected=True):
        if self.rpc_client is None:
            self.rpc_client = PersistentRPC(SOCKET, self.client, self.group, self.client_env())
            self.data["rpc_helper"] = dict(self.rpc_client.identity)
        value = self.rpc_client.request(request)
        require(type(value) is dict and value.get("ok") is expected,
                "unexpected " + str(request.get("op")) + " RPC result: " + str(value))
        return value

    def status(self):
        return assert_simulation(self.rpc({"op": "status"})["data"])

    def wait_status(self, predicate, timeout=10, context="state transition"):
        deadline, last, last_error = time.monotonic() + timeout, None, None
        while time.monotonic() < deadline:
            try:
                last = self.status()
                if predicate(last):
                    return last
            except (OSError, ValueError, SmokeError, subprocess.SubprocessError) as error:
                last_error = type(error).__name__ + ": " + str(error)
            time.sleep(.1)
        raise SmokeError(context + " timed out; last=" + json.dumps(last)
                         + "; last_rpc_error=" + str(last_error))

    def arm(self):
        self.wait_status(lambda s: s["pico"].get("state") in {"SAFE", "TRIPPED"}, context="explicit arm SAFE/TRIPPED")
        self.rpc({"op": "recover"})
        status = self.wait_status(lambda s: s["policy"]["armed"], context="explicit arm policy armed")
        require(status["policy"]["owner"] == "uid:" + str(self.client.pw_uid), "lease owner differs from real AF_UNIX peer UID")
        require(not any(v for k, v in status["policy"]["outputs"].items() if k != "CHG_INHIBIT"),
                "explicit recovery must not restore previous switched loads")
        return status

    def enable_lna(self):
        self.rpc({"op": "lease", "value": {"ttl_ms": 5000}})
        self.rpc({"op": "control", "name": "EN_LNA1", "value": True})
        return self.wait_status(lambda s: s["policy"]["outputs"]["EN_LNA1"])

    def stage_candidate(self):
        parent = Path(tempfile.mkdtemp(prefix="srrx-linux-lab-", dir="/var/tmp"))
        parent.chmod(0o755)
        self.stage = parent / "candidate"
        result = self.command(["/usr/bin/python3", self.project / "deployment/deploy.py", "stage", "--dest", self.stage], timeout=120)
        meta = json.loads(result.stdout)
        require(meta["status"] == "STAGED_ONLY" and meta["hardware_ready"] is False and meta["services_enabled"] is False,
                "candidate staging must never claim activation")
        rootfs = self.stage / "rootfs"
        manifest = json.loads((self.stage / "stage-files.json").read_text())
        require(all(digest(rootfs / path) == value for path, value in manifest["files"].items()), "staged file hash differs")
        copied = {path.removeprefix("opt/srrx/"): value for path, value in manifest["files"].items() if path.startswith("opt/srrx/")}
        require(copied and all(digest(self.project / path) == value for path, value in copied.items()),
                "staged package does not contain the current installed source")
        for path in rootfs.rglob("*"):
            require(not path.is_symlink() and not path.name.endswith(".wants"), "staging created a service enable link")
        for name in ("acceptance.json", "devices.json", "devices.env", "release.json", "build-manifest.json"):
            require(not (rootfs / "etc/srrx" / name).exists(), "staging supplied a live record: " + name)
        menu = rootfs / "usr/lib/systemd/user/srrx-menu.service"
        require(menu.is_file() and not (rootfs / "etc/systemd/system/srrx-menu.service").exists(), "menu must remain a user unit")
        require(digest(menu) == digest(self.project / "software/systemd/srrx-menu.service"), "staged menu differs from source")
        template = json.loads((rootfs / "etc/srrx/acceptance.template.json").read_text())
        gates = template["gates"]
        contract = json.loads((self.project / "design/readiness-contract.json").read_text())["gate_results"]
        require(set(gates) == set(contract) and all(g["status"] == "OPEN" for g in gates.values()),
                f"all {len(contract)} physical gates must remain OPEN")
        unit_paths = sorted((rootfs / "etc/systemd/system").glob("*.service")) + [menu]
        self.command(["/usr/bin/systemd-analyze", "verify", *unit_paths], timeout=60)
        # Install only the guarded hardware unit in this marked guest. Never
        # install/start the root poweroff bridge or create an enable symlink.
        for relative in ("etc/systemd/system/srrx.service", "etc/systemd/system/srrx.service.d/20-release-guard.conf"):
            src, target = rootfs / relative, Path("/") / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            require(not target.is_symlink(), "refusing to replace a linked unit")
            require(not target.exists() or target.read_bytes() == src.read_bytes(), "guest has a different preexisting hardware unit")
            target.write_bytes(src.read_bytes())
        self.systemctl("daemon-reload")
        require(self.properties("srrx.service")["UnitFileState"] != "enabled", "hardware unit must not be enabled")
        return {"stage": str(self.stage), "payload_files": len(manifest["files"]), "current_source_files_verified": len(copied),
                "manifest_sha256": digest(self.stage / "stage-files.json"),
                "physical_gates_open": len(gates), "menu_user_unit": True, "systemd_verify": "PASS"}

    def device_wait(self):
        """DEP-11 on this guest's real systemd: the generated Wants=/After= drop-in waits for an absent
        /dev/lab node only up to the device timeout, and each automatic restart waits again, so a
        failing guard does not run into start-limit-hit. The hardware unit is not involved."""
        deploy = load_deploy(self.project)
        escaped = {}
        for path in ("/dev/lab/rtla", "/dev/lab/rtlb", "/dev/lab/hfplus", "/dev/lab/pico", DEVICE_PROBE):
            escaped[path] = self.command(["/usr/bin/systemd-escape", "--path", "--suffix=device", path]).stdout.strip()
            require(escaped[path] == deploy.device_unit(path), "device unit name differs from systemd-escape: " + path)
        require(not os.path.lexists(DEVICE_PROBE), "device-wait probe node unexpectedly exists")
        probe = deploy.device_unit(DEVICE_PROBE)
        dropin = deploy.lab_device_dropin([DEVICE_PROBE])
        files = {UNIT_DIR / (probe + ".d") / deploy.DEVICE_TIMEOUT_DROPIN: deploy.device_timeout_dropin(PROBE_TIMEOUT_S)}
        for name, text in device_probe_units().items():
            files[UNIT_DIR / name] = text
            files[UNIT_DIR / (name + ".d") / deploy.LAB_DEVICE_DROPIN] = dropin
        for path in files:  # checked before the first write: cleanup below removes only files created here
            require(not os.path.lexists(path), "refusing to replace an existing unit file: " + str(path))
        try:
            for path, text in files.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            self.systemctl("daemon-reload")
            started = time.monotonic()
            self.systemctl("start", DEVWAIT_UNIT)
            waited = round(time.monotonic() - started, 3)
            wait = self.properties(DEVWAIT_UNIT)
            shown = self.systemctl("show", probe, "--property=ActiveState", "--property=JobRunningTimeoutUSec")
            device = dict(line.split("=", 1) for line in shown.stdout.splitlines() if "=" in line)
            require(PROBE_TIMEOUT_S - .5 <= waited <= 15 and wait["Result"] == "success"
                    and device.get("JobRunningTimeoutUSec") in (str(PROBE_TIMEOUT_S) + "s", str(PROBE_TIMEOUT_S * 1_000_000))
                    and device.get("ActiveState") != "active",
                    f"absent device wait not bounded by its timeout: waited {waited} s, {wait}, {device}")
            self.systemctl("start", "--no-block", DEVRETRY_UNIT)
            time.sleep(15)
            retry = self.properties(DEVRETRY_UNIT)
            # Default StartLimitBurst=5 per 10 s: a 1 s retry without the device wait would hit it.
            require(1 <= int(retry["NRestarts"]) <= 4 and retry["Result"] != "start-limit-hit" and retry["ActiveState"] != "failed",
                    "restarts must wait for the device job again instead of reaching start-limit-hit: " + str(retry))
            return {"systemd_escape": escaped, "probe_device_unit": probe, "dropin": dropin,
                    "device_timeout_s": PROBE_TIMEOUT_S, "oneshot_wait_s": waited, "oneshot_result": wait["Result"],
                    "device": device, "restart_probe_after_15_s": {k: retry[k] for k in ("ActiveState", "SubState", "NRestarts", "Result")},
                    "hardware_unit_used": False}
        finally:
            for name in (DEVRETRY_UNIT, DEVWAIT_UNIT):
                self.systemctl("stop", name, accepted=(0, 1, 5))
                self.systemctl("reset-failed", name, accepted=(0, 1, 5))
            for path in files:
                if path.is_file() and not path.is_symlink():
                    path.unlink()
                if path.parent != UNIT_DIR and path.parent.is_dir() and not any(path.parent.iterdir()):
                    path.parent.rmdir()
            self.systemctl("daemon-reload")

    def hardware_missing(self):
        etc = Path("/etc/srrx")
        require(not any((etc / name).exists() for name in ("acceptance.json", "devices.env", "devices.json", "release.json", "build-manifest.json")),
                "guest must not contain live acceptance/device/release records")
        self.systemctl("stop", "srrx.service")
        self.systemctl("reset-failed", "srrx.service", accepted=(0, 1))
        self.systemctl("start", "srrx.service")
        props = self.properties("srrx.service")
        require(props["ActiveState"] == "inactive" and props["MainPID"] == "0" and props["ConditionResult"] == "no",
                "missing records must skip the hardware unit before process start: " + str(props))
        return props

    def hardware_open(self):
        etc = Path("/etc/srrx")
        etc.mkdir(parents=True, exist_ok=True)
        rootfs = self.stage / "rootfs/etc/srrx"
        created = []
        try:
            for name in ("acceptance", "devices", "release", "build-manifest"):
                target = etc / (name + ".json")
                require(not target.exists() and not target.is_symlink(), "refusing to overwrite a live record")
                target.write_bytes((rootfs / (name + ".template.json")).read_bytes())
                created.append(target)
            env = etc / "devices.env"
            require(not env.exists() and not env.is_symlink(), "refusing to overwrite live device environment")
            env.write_bytes((self.project / "software/config/devices.env.example").read_bytes())
            created.append(env)
            start = self.systemctl("start", "srrx.service", accepted=(0, 1))
            props = self.properties("srrx.service")
            require(start.returncode != 0 and props["ConditionResult"] == "yes" and props["ExecMainPID"] == "0"
                    and props["ExecMainStartTimestampMonotonic"] == "0"
                    and "release-guard" in props["ExecStartPre"] and release_guard_exited_2(props["ExecStartPre"]),
                    "OPEN records must fail the actual release guard before ExecStart: " + str(props))
            # Also invoke the installed entrypoint: OPEN acceptance is rejected
            # before any intentionally nonexistent physical device is opened.
            check = self.command([self.project / "venv/bin/labd", "--hardware", "--project", self.project,
                                  "--acceptance", etc / "acceptance.json", "--i2c", "/dev/SRRX_LAB_UNBOUND_I2C2",
                                  "--i2c0", "/dev/SRRX_LAB_UNBOUND_I2C0", "--pico", "/dev/SRRX_LAB_UNBOUND_PICO"],
                                 accepted=(1,), client=True, env=self.client_env())
            require("labd refused startup:" in check.stderr and "No such file or directory" not in check.stderr,
                    "OPEN acceptance must be rejected before physical transport startup")
            return {"systemd": props, "stderr": check.stderr[-3000:], "generated_acceptance": False}
        finally:
            self.systemctl("stop", "srrx.service", accepted=(0, 1))
            self.systemctl("reset-failed", "srrx.service", accepted=(0, 1))
            for path in reversed(created):
                path.unlink()

    def client_env(self):
        return {"PATH": "/usr/bin:/bin", "HOME": self.client.pw_dir, "LANG": "C.UTF-8",
                "PYTHONPATH": str(self.project / "software"), "PYTHONDONTWRITEBYTECODE": "1"}

    def entrypoints(self):
        result = self.command([self.project / "venv/bin/labd", "--simulate", "--stdio", "--project", self.project],
                              client=True, input='{"op":"status"}\n{"op":[]}\n', env=self.client_env())
        replies = [json.loads(line) for line in result.stdout.splitlines()]
        require(len(replies) == 2 and replies[0]["ok"] is True and replies[1]["ok"] is False, "installed stdio entrypoint failed")
        assert_simulation(replies[0]["data"], safe=True)
        for name in ("labd", "labctl", "labrx", "labmenu", "labclassify", "labmodel", "labdecode"):
            require((self.project / "venv/bin" / name).is_file(), "installed venv entrypoint missing: " + name)
        return {"installed_prefix": str(self.project / "venv"), "cwd": "/", "explicit_project": str(self.project),
                "stdio_mode": replies[0]["data"]["mode"], "malformed_request_rejected": True}

    def start_simulation(self):
        target = Path("/etc/systemd/system") / SIM_UNIT
        text = simulation_unit((self.project / "software/systemd/srrx.service").read_text())
        require(not target.is_symlink() and (not target.exists() or target.read_text() == text), "different simulation unit already exists")
        target.write_text(text)
        self.command(["/usr/bin/systemd-analyze", "verify", target], timeout=60)
        self.systemctl("daemon-reload")
        self.systemctl("start", SIM_UNIT)
        self.sim_started = True
        status = self.wait_status(lambda s: s["pico"].get("state") == "SAFE")
        assert_simulation(status, safe=True)
        props = self.properties()
        for key, value in {"User": "labd", "Group": "labd", "NoNewPrivileges": "yes", "ProtectSystem": "strict",
                           "ProtectHome": "yes", "PrivateTmp": "yes", "PrivateDevices": "yes", "DevicePolicy": "closed",
                           "ProtectKernelTunables": "yes", "ProtectKernelModules": "yes", "ProtectControlGroups": "yes",
                           "RestrictAddressFamilies": "AF_UNIX", "RuntimeDirectory": "srrx-linux-lab"}.items():
            require(props.get(key) == value, "runtime sandbox differs: " + key + "=" + str(props.get(key)))
        require(props["ActiveState"] == "active" and int(props["MainPID"]) > 1 and props["UnitFileState"] != "enabled",
                "simulation unit must be active but not enabled")
        return {"properties": props, "unit_sha256": digest(target), "status": status}

    def single_writer(self):
        pid = self.properties()["MainPID"]
        # A same-UID collision exercises flock rather than merely permissions.
        daemon = pwd.getpwnam("labd")
        result = subprocess.run([str(self.project / "venv/bin/labd"), "--simulate", "--project", str(self.project), "--socket", SOCKET],
                                capture_output=True, text=True, cwd="/", env=self.client_env(), user=daemon.pw_uid,
                                group=self.group.gr_gid, extra_groups=[], timeout=15)
        require(result.returncode == 1 and "temporarily unavailable" in result.stderr.lower(), "same-UID writer did not fail flock")
        require(self.properties()["MainPID"] == pid, "collision displaced the running service")
        assert_simulation(self.status(), safe=True)
        return {"same_uid_flock_rejected": True, "service_pid_unchanged": pid, "stderr": result.stderr[-2000:]}

    def permissions(self):
        info, directory = Path(SOCKET).stat(), Path(SOCKET).parent.stat()
        require(stat.S_ISSOCK(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o660 and info.st_gid == self.group.gr_gid,
                "AF_UNIX socket must be 0660 in labd group")
        require(stat.S_IMODE(directory.st_mode) == 0o750 and directory.st_gid == self.group.gr_gid, "runtime directory permissions differ")
        cli = self.command([self.project / "venv/bin/labctl", "--socket", SOCKET, "status"], client=True, env=self.client_env())
        assert_simulation(json.loads(cli.stdout)["data"], safe=True)
        result = self.rpc({"op": "off_now", "_owner": "uid:0"}, expected=False)
        require("root" in result["error"].lower(), "unprivileged OFF_NOW must be rejected from real peer UID")
        self.rpc({"op": "lease", "value": {"ttl_ms": 5000, "owner": "uid:0"}}, expected=False)
        nobody = pwd.getpwnam("nobody")
        denied = subprocess.run(["/usr/bin/python3", "-c", CLIENT, SOCKET, '{"op":"status"}'], user=nobody.pw_uid,
                                group=nobody.pw_gid, extra_groups=[], capture_output=True, text=True, timeout=10)
        require(denied.returncode != 0 and "PermissionError" in denied.stderr, "nonmember must not reach the control socket")
        return {"socket_mode": "0660", "directory_mode": "0750", "client_uid": self.client.pw_uid,
                "client_group": "labd", "nonmember_denied": True, "peer_uid_cannot_be_spoofed": True}

    def fault(self):
        self.arm()
        self.enable_lna()
        self.rpc({"op": "sim", "name": "FAULT_LNA1", "value": False})
        status = self.wait_status(lambda s: not s["policy"]["armed"])
        assert_simulation(status, safe=True)
        # Any trip disarms; only the injected input proves the fault path.
        require(status["policy"].get("fault") == "active-low fault: FAULT_LNA1",
                "fault scenario tripped for a different reason: " + str(status["policy"].get("fault")))
        self.rpc({"op": "sim", "name": "FAULT_LNA1", "value": True})
        time.sleep(.5)
        assert_simulation(self.status(), safe=True)
        self.rpc({"op": "control", "name": "EN_LNA1", "value": True}, expected=False)
        return {"fault_input": "FAULT_LNA1", "clearing_fault_did_not_rearm": True,
                "exact_fault": status["policy"]["fault"], "tripped_status": status}

    def link_loss(self):
        self.arm()
        self.enable_lna()
        self.rpc({"op": "sim", "name": "drop_link", "value": True})
        status = self.wait_status(lambda s: not s["policy"]["armed"])
        assert_simulation(status, safe=True)
        require(status["policy"].get("fault") == "pico_status_timeout",
                "link-loss scenario tripped for a different reason: " + str(status["policy"].get("fault")))
        # Leave both wire directions absent beyond the independent model's
        # 750 ms heartbeat timeout, even after the host's 500 ms stale trip.
        time.sleep(.9)
        self.rpc({"op": "sim", "name": "drop_link", "value": False})
        recovered = self.wait_status(lambda s: s["pico"].get("state") == "TRIPPED")
        assert_simulation(recovered, safe=True)
        require(recovered["pico"].get("mcp_reset") is True, "Pico model heartbeat timeout must assert MCP reset")
        self.rpc({"op": "control", "name": "EN_LNA1", "value": True}, expected=False)
        return {"restored_link_did_not_rearm": True, "exact_fault": status["policy"]["fault"], "tripped_status": status}

    def lease_expiry(self):
        self.arm()
        self.enable_lna()
        self.rpc({"op": "lease", "value": {"ttl_ms": 400}})
        status = self.wait_status(lambda s: not s["policy"]["armed"])
        assert_simulation(status, safe=True)
        require(status["policy"].get("fault") == "owner lease expired",
                "lease scenario tripped for a different reason: " + str(status["policy"].get("fault")))
        self.rpc({"op": "lease", "value": {"ttl_ms": 5000}})
        time.sleep(.5)
        assert_simulation(self.status(), safe=True)
        self.rpc({"op": "control", "name": "EN_LNA1", "value": True}, expected=False)
        return {"expired_lease_latched": True, "late_renewal_did_not_rearm": True,
                "exact_fault": status["policy"]["fault"], "tripped_status": status}

    def shutdown(self):
        phase = "explicit arm before shutdown RPC"
        try:
            self.arm()
            phase = "enable LNA before shutdown RPC"
            self.enable_lna()
            phase = "shutdown RPC"
            reply = self.rpc({"op": "shutdown"})
            require(reply.get("os_poweroff_executed") is False, "simulation must never execute OS poweroff")
            phase = "ARM_OFF acknowledgement"
            status = self.wait_status(lambda s: s["pico"].get("state") == "SHUTTING_DOWN",
                                      context="shutdown ARM_OFF acknowledgement")
            assert_simulation(status, safe=True)
            require(Path("/proc/1/comm").read_text().strip() == "systemd", "guest init disappeared")
            # Reset only the simulation model; do not invoke the poweroff bridge.
            phase = "simulation service restart after shutdown"
            self.systemctl("restart", SIM_UNIT)
            assert_simulation(self.wait_status(lambda s: s["pico"].get("state") == "SAFE",
                                               context="shutdown restart SAFE"), safe=True)
            return {"pico_state": status["pico"]["state"], "os_poweroff_executed": False,
                    "poweroff_bridge_started": False}
        except Exception as error:
            raise SmokeError("shutdown phase=" + phase + ": " + str(error)) from error

    def restart(self):
        self.arm()
        self.enable_lna()
        before = self.properties()
        self.systemctl("kill", "--kill-whom=main", "--signal=SIGKILL", SIM_UNIT)
        deadline, after = time.monotonic()+20, None
        while time.monotonic() < deadline:
            after = self.properties()
            if after["ActiveState"] == "active" and int(after["MainPID"]) > 1 and after["MainPID"] != before["MainPID"]:
                break
            time.sleep(.2)
        require(after and after["MainPID"] != before["MainPID"] and int(after["MainPID"]) > 1,
                "systemd did not restart the killed simulation process")
        require(int(after["NRestarts"]) > int(before["NRestarts"]), "Restart=on-failure was not exercised")
        status = self.wait_status(lambda s: s["pico"].get("state") == "SAFE")
        assert_simulation(status, safe=True)
        self.rpc({"op": "control", "name": "EN_LNA1", "value": True}, expected=False)
        return {"old_pid": before["MainPID"], "new_pid": after["MainPID"], "restart_count": after["NRestarts"],
                "no_auto_arm": True, "status": status}

    def handoff(self):
        status = assert_simulation(self.status(), safe=True)
        require(not Path("/etc/srrx/acceptance.json").exists(), "temporary OPEN acceptance was not removed")
        require(self.properties("srrx.service")["MainPID"] == "0", "hardware unit unexpectedly running")
        props = self.properties()
        require(props["ActiveState"] == "active" and props["UnitFileState"] != "enabled", "GUI simulation handoff unavailable")
        return {"unit": SIM_UNIT, "socket": SOCKET, "client": "labclient", "group": "labd",
                "service_left_running": True, "hardware_unit_running": False, "status": status}

    def execute(self, facts):
        tasks = (("guest_boundary", lambda: facts), ("candidate_stage", self.stage_candidate),
                 ("systemd_device_wait_bounded", self.device_wait),
                 ("hardware_missing_records", self.hardware_missing), ("hardware_open_records", self.hardware_open),
                 ("installed_entrypoints_stdio", self.entrypoints), ("systemd_simulation", self.start_simulation),
                 ("single_writer", self.single_writer), ("client_permissions", self.permissions),
                 ("explicit_arm_and_fault", self.fault), ("link_loss_latched", self.link_loss),
                 ("lease_expiry_latched", self.lease_expiry), ("simulation_shutdown", self.shutdown),
                 ("systemd_restart_disarmed", self.restart), ("gui_handoff", self.handoff))
        try:
            for name, operation in tasks:
                self.step(name, operation)
            require(tuple(step["name"] for step in self.data["steps"]) == REQUIRED_STEPS, "smoke did not execute every required step")
            self.data["status"] = "PASS"
        except Exception as exc:
            self.data.update(status="FAIL", error=str(exc)[:5000])
            if self.sim_started:
                # Failed integration cannot hand armed simulation to later tests.
                self.systemctl("stop", SIM_UNIT, accepted=(0, 1))
        finally:
            if self.rpc_client is not None:
                try:
                    self.rpc_client.close()
                except Exception as error:
                    self.data["status"] = "FAIL"
                    self.data.setdefault("error", "RPC helper cleanup failed: " + str(error))
                    self.data["rpc_helper"]["cleanup_error"] = type(error).__name__ + ": " + str(error)
                self.data["rpc_helper"].update(requests=self.rpc_client.requests,
                    exit_code=self.rpc_client.process.poll(), cleaned_up=self.rpc_client.process.poll() is not None)
            self.data["finished_at"] = datetime.now(timezone.utc).isoformat()
            # The readiness contract is the gate set candidate_stage compared; finalize binds it (TOOL-07).
            self.data["source_sha256"] = {path.relative_to(self.project).as_posix(): digest(path) for path in (
                self.project / "software/srrx/daemon.py", self.project / "software/srrx/engine.py",
                self.project / "software/systemd/srrx.service", self.project / "design/E3.json",
                self.project / "design/readiness-contract.json", self.project / "deployment/linux_lab/guest_smoke.py")}
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.report_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.data, indent=2, allow_nan=False) + "\n")
            temporary.replace(self.report_path)
        return self.data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path("/opt/srrx"))
    parser.add_argument("--report", type=Path, default=Path(REPORT))
    parser.add_argument("--lab-marker", type=Path, default=Path(MARKER))
    args = parser.parse_args(argv)
    try:
        facts = guard_environment(args.project, args.lab_marker)
        require(args.report.is_absolute() and args.report.is_relative_to("/var/lib/srrx-linux-lab")
                and ".." not in args.report.parts, "report must stay under /var/lib/srrx-linux-lab")
        report = GuestSmoke(args.project, args.report).execute(facts)
        print(json.dumps({"status": report["status"], "report": str(args.report), "hardware_qualified": False}))
        return 0 if report["status"] == "PASS" else 1
    except (OSError, ValueError, KeyError, SmokeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc), "hardware_qualified": False}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
