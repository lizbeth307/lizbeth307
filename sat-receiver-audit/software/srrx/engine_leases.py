"""labd side of the exclusive engine leases (STACK.md C7, lease mode 2; stdlib only).

An engine (readsb, AIS-catcher, sdrangelsrv) opens its receiver itself, so it runs only in a
root-owned template unit, srrx-lease-<engine>@<alias>.service (software/systemd). The instance
is the udev alias of one receiver (/dev/lab/rtla, rtlb or hfplus; deploy.udev_rules), and
DevicePolicy=closed with DeviceAllow=/dev/lab/%i leaves the engine exactly that receiver. labd
never runs an engine in its own cgroup and the console never starts a unit: the operation
engine_lease {engine, receiver} asks labd, and labd starts the instance with `systemctl start`
under the polkit rule from polkit_rule(), which lets the labd user start and stop these nine
instances and nothing else. Nothing is enabled by a preset.

Rules (srrx.engine.Engine.request checks the operator lease before calling request()):

1. The caller holds its own valid operator lease (the policy lease the console renews). The
   engine lease ends when that lease is lost or expires, on DISARM and on every other trip of
   the power policy (the receivers lose VBUS then), on engine_stop (operator or scope stop),
   when the unit exits, and when srrx.service stops: each template has BindsTo=srrx.service,
   and since systemd 254 an automatic restart passes through the inactive state first
   (NEWS, RestartMode=), so no lease outlives the labd that granted it.
2. One engine per receiver. A labrx holder (labrx_hold) keeps the receiver in labrx mode and
   the lease is refused while it holds; a granted lease takes the receiver out of labrx mode,
   and labrx_hold is refused until the lease has ended and its units are stopped.
3. Handover (STACK.md:882) runs in one worker thread, never in labd's 20 ms tick: stop every
   lease unit of that receiver -> release (the slot forgets the previous engine) ->
   re-enumeration check (the alias is again a USB device with the vid, pid and serial of
   /etc/srrx/devices.json) -> start. A stop that fails leaves the receiver in FAULT: neither a
   lease nor labrx may take it until a later engine_stop succeeds.

Refusals and failures are stable codes (ERRORS) and never carry device or file contents.
Device behaviour (EPERM on another node, EROFS on /data, CONFIG_CGROUP_BPF=y) is the
RX-12-runtime row on a Q6A; the end-of-lease VBUS cycle (STACK.md:78) is not done here.
"""
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import threading

ENGINES = ("readsb", "aiscatcher", "sdrangelsrv")
# Template instance -> devices.json "usb" key; the alias is the udev SYMLINK (deploy.validate_devices).
DEVICE_KEYS = {"rtla": "rtl_a", "rtlb": "rtl_b", "hfplus": "hfplus"}
RECEIVERS = tuple(DEVICE_KEYS)
TEMPLATES = tuple("srrx-lease-" + engine + "@.service" for engine in ENGINES)
UNIT_PATTERN = "^srrx-lease-(" + "|".join(ENGINES) + ")@(" + "|".join(RECEIVERS) + ")\\.service$"
LABD_USER = "labd"
LEASE_USER = "lab"
POLKIT_RULE = "etc/polkit-1/rules.d/60-srrx-engine-lease.rules"
PRODUCTS_ROOT = "/data/products"
SYSTEMCTL = "/usr/bin/systemctl"
DEVICES_PATH = Path("/etc/srrx/devices.json")
DEV_ROOT = Path("/dev/lab")
SYS_CHAR_ROOT = Path("/sys/dev/char")
START_TIMEOUT_S = 45  # TimeoutStartSec=30s of the templates plus systemctl and polkit slack
STOP_TIMEOUT_S = 25  # TimeoutStopSec=10s (then SIGKILL) plus slack
WATCH_MS = 5000  # an active unit is checked with `systemctl is-active` at most this often
STATES = ("IDLE", "STARTING", "ACTIVE", "STOPPING", "FAULT")
STOP_REASONS = ("operator", "scope")
ERRORS = ("ENGINE_LEASE_DISABLED", "ENGINE_LEASE_CLOSED", "ENGINE_LEASE_BAD_REQUEST",
          "ENGINE_LEASE_NO_OPERATOR_LEASE", "ENGINE_LEASE_LABRX_HOLDS", "ENGINE_LEASE_BUSY",
          "ENGINE_LEASE_FAULT", "ENGINE_LEASE_DEVICES_UNAVAILABLE", "ENGINE_LEASE_NODE_MISSING",
          "ENGINE_LEASE_NODE_MISMATCH", "ENGINE_LEASE_START_FAILED", "ENGINE_LEASE_STOP_FAILED",
          "ENGINE_LEASE_UNIT_EXITED", "ENGINE_LEASE_INTERNAL")
# Why a lease ended (status last_stop): engine_stop reasons, the operator lease, a policy trip, labd exit.
STOPS = ("OPERATOR_STOP", "SCOPE_STOP", "OPERATOR_LEASE_LOST", "POLICY_TRIP", "DAEMON_EXIT", "UNIT_EXITED")
_SYSTEMCTL_ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "SYSTEMD_PAGER": "", "SYSTEMD_COLORS": "0"}


def unit_name(engine, receiver):
    """srrx-lease-<engine>@<receiver>.service; ValueError outside ENGINES x RECEIVERS."""
    if engine not in ENGINES or receiver not in RECEIVERS:
        raise ValueError("an engine lease unit needs a known engine and receiver alias")
    return "srrx-lease-" + engine + "@" + receiver + ".service"


def products_dir(engine, receiver):
    """The one writable directory of a lease unit (ReadWritePaths=/data/products/<engine>-%i)."""
    unit_name(engine, receiver)
    return PRODUCTS_ROOT + "/" + engine + "-" + receiver


def polkit_rule():
    """/etc/polkit-1/rules.d/60-srrx-engine-lease.rules: labd may start and stop the lease instances."""
    return ("// SR-RX: srrx.engine_leases.polkit_rule(), staged by deployment/deploy.py stage.\n"
            "// The " + LABD_USER + " user may start and stop, and only start and stop, one exclusive engine lease\n"
            "// srrx-lease-<" + "|".join(ENGINES) + ">@<" + "|".join(RECEIVERS) + ">.service.\n"
            "// Any other action, verb, unit or user falls through to the default policy.\n"
            "polkit.addRule(function(action, subject) {\n"
            '    if (action.id == "org.freedesktop.systemd1.manage-units" &&\n'
            '            subject.user == "' + LABD_USER + '" &&\n'
            '            (action.lookup("verb") == "start" || action.lookup("verb") == "stop") &&\n'
            "            /" + UNIT_PATTERN + '/.test(action.lookup("unit"))) {\n'
            "        return polkit.Result.YES;\n"
            "    }\n"
            "});\n")


def staged_files():
    """Relative rootfs path -> text, for deploy.stage (the templates are copied from software/systemd)."""
    return {POLKIT_RULE: polkit_rule()}


def parse_request(value):
    """((engine, receiver), None) for exactly {engine, receiver}, else (None, code)."""
    if (type(value) is not dict or set(value) != {"engine", "receiver"}
            or value["engine"] not in ENGINES or value["receiver"] not in RECEIVERS):
        return None, "ENGINE_LEASE_BAD_REQUEST"
    return (value["engine"], value["receiver"]), None


def parse_stop(value):
    """((receiver or None, reason), None) for {reason[, receiver]}, else (None, code)."""
    if (type(value) is not dict or "reason" not in value or set(value) - {"receiver", "reason"}
            or value["reason"] not in STOP_REASONS
            or value.get("receiver") is not None and value["receiver"] not in RECEIVERS):
        return None, "ENGINE_LEASE_BAD_REQUEST"
    return (value.get("receiver"), value["reason"]), None


def _char_node(path):
    """(major, minor) of the character device path resolves to (stat follows the alias), or None."""
    info = os.stat(path)
    if not stat.S_ISCHR(info.st_mode):
        return None
    return os.major(info.st_rdev), os.minor(info.st_rdev)


def _sysfs_text(path, limit=256):
    with open(path, "rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("sysfs attribute too long")
    return data.decode("ascii").strip()


def reenumeration_check(receiver, *, devices_path=DEVICES_PATH, dev_root=DEV_ROOT, sys_char_root=SYS_CHAR_ROOT,
                        char_node=_char_node):
    """None when /dev/lab/<receiver> is again the bound USB device, else a stable code.

    The alias must resolve to a character device whose sysfs node (/sys/dev/char/<major>:<minor>)
    is a usb_device with the idVendor, idProduct and serial that devices.json binds to that alias:
    the identity the udev rule matched (deploy.udev_rules)."""
    try:
        device = json.loads(Path(devices_path).read_text(encoding="utf-8"))["usb"][DEVICE_KEYS[receiver]]
        expected = {"idVendor": device["vid"], "idProduct": device["pid"], "serial": device["serial"]}
        if device["path"] != "/dev/lab/" + receiver or any(type(v) is not str or not v for v in expected.values()):
            return "ENGINE_LEASE_DEVICES_UNAVAILABLE"
    except (OSError, ValueError, KeyError, TypeError):
        return "ENGINE_LEASE_DEVICES_UNAVAILABLE"
    try:
        node = char_node(Path(dev_root) / receiver)
    except FileNotFoundError:
        return "ENGINE_LEASE_NODE_MISSING"
    except (OSError, ValueError):
        return "ENGINE_LEASE_NODE_MISMATCH"
    if node is None:
        return "ENGINE_LEASE_NODE_MISMATCH"
    sysfs = Path(sys_char_root) / ("%d:%d" % node)
    try:
        if "DEVTYPE=usb_device" not in _sysfs_text(sysfs / "uevent", 4096).splitlines():
            return "ENGINE_LEASE_NODE_MISMATCH"
        if any(_sysfs_text(sysfs / name) != value for name, value in expected.items()):
            return "ENGINE_LEASE_NODE_MISMATCH"
    except (OSError, ValueError):  # UnicodeDecodeError is a ValueError
        return "ENGINE_LEASE_NODE_MISMATCH"
    return None


def _refused(code, **extra):
    return dict({"ok": False, "error": code}, **extra)


def _daemon_thread(target):
    threading.Thread(target=target, name="srrx-engine-lease", daemon=True).start()


class EngineLeases:
    """The lease slots of labd, one per receiver: requests and stops never block, the worker runs systemctl.

    systemctl(args, timeout_s) -> exit code, check_node(receiver) -> None or a code and
    start_thread(target) are injectable for tests; the defaults run /usr/bin/systemctl,
    reenumeration_check and one daemon thread that ends when no slot needs work (TasksMax=8)."""

    def __init__(self, *, systemctl=None, check_node=None, start_thread=None):
        self.systemctl = systemctl or self._systemctl
        self.check_node = check_node or reenumeration_check
        self.start_thread = start_thread or _daemon_thread
        self._lock = threading.Lock()
        self._slots = {receiver: {"state": "IDLE", "want": None, "owner": None, "running": None,
                                  "generation": 0, "labrx": None, "last_error": None, "last_stop": None,
                                  "watch_ms": None, "watch_due": False} for receiver in RECEIVERS}
        self._pending, self._worker, self._closed = [], False, False

    # ---------------------------------------------------------------- labd loop side

    def request(self, value, owner, now_ms):
        """engine_lease, after Engine.request checked the caller's own operator lease."""
        parsed, code = parse_request(value)
        if code:
            return _refused(code)
        engine, receiver = parsed
        reply = {"ok": True, "engine": engine, "receiver": receiver, "unit": unit_name(engine, receiver)}
        with self._lock:
            slot = self._slots[receiver]
            if self._closed:
                return _refused("ENGINE_LEASE_CLOSED")
            if slot["state"] == "FAULT":
                return _refused("ENGINE_LEASE_FAULT", receiver=receiver)
            if slot["labrx"] is not None:
                return _refused("ENGINE_LEASE_LABRX_HOLDS", receiver=receiver)
            if slot["want"] == engine and slot["owner"] == owner:
                return dict(reply, state=slot["state"])
            if slot["want"] is not None or slot["state"] != "IDLE":
                return _refused("ENGINE_LEASE_BUSY", receiver=receiver)
            slot.update(want=engine, owner=owner, state="STARTING", last_error=None, last_stop=None,
                        watch_ms=int(now_ms), watch_due=False, generation=slot["generation"] + 1)
            spawn = self._enqueue(receiver)
        if spawn and not self._start_worker():
            with self._lock:
                if receiver in self._pending:
                    self._pending.remove(receiver)
                slot.update(want=None, owner=None, state="IDLE", last_error="ENGINE_LEASE_INTERNAL",
                            generation=slot["generation"] + 1)
            return _refused("ENGINE_LEASE_INTERNAL", receiver=receiver)
        return dict(reply, state="STARTING")

    def stop_request(self, value):
        """engine_stop {reason: operator|scope[, receiver]}: needs no lease, like DISARM."""
        parsed, code = parse_stop(value)
        if code:
            return _refused(code)
        receiver, reason = parsed
        stopping = self.stop(receiver, "SCOPE_STOP" if reason == "scope" else "OPERATOR_STOP", force=True)
        return {"ok": True, "stopping": stopping}

    def stop(self, receiver, why, *, force=False):
        """End the lease of one receiver (None: every receiver); force also retries the stop of a
        FAULT slot. Returns the receivers whose units are being stopped; never blocks."""
        stopping, spawn = [], False
        with self._lock:
            for name in RECEIVERS if receiver is None else (receiver,):
                slot = self._slots[name]
                busy = (slot["want"] is not None or slot["running"] is not None
                        or slot["state"] in ("STARTING", "STOPPING"))
                if not busy and not (force and slot["state"] == "FAULT"):
                    continue
                if slot["want"] is not None or slot["running"] is not None:
                    slot["last_stop"] = why
                slot.update(want=None, owner=None, watch_due=False, generation=slot["generation"] + 1)
                if slot["state"] in ("ACTIVE", "FAULT"):
                    slot["state"] = "STOPPING"
                stopping.append(name)
                spawn = self._enqueue(name) or spawn
        if spawn and not self._start_worker():
            # No worker thread: queue the stops in systemd without waiting, and keep the receivers
            # out of labrx mode (FAULT) until a later engine_stop confirms them.
            for name in stopping:
                for engine in ENGINES:
                    self._run(["--no-block", "stop", unit_name(engine, name)], 5)
            with self._lock:
                for name in stopping:
                    self._slots[name].update(state="FAULT", running=None, last_error="ENGINE_LEASE_STOP_FAILED")
                    if name in self._pending:
                        self._pending.remove(name)
        return stopping

    def stop_all(self, why):
        return self.stop(None, why)

    def tick(self, now_ms, operator_lease_valid):
        """labd tick: end the leases whose owner lost the operator lease; schedule the unit watch."""
        lost, spawn = [], False
        with self._lock:
            for receiver, slot in self._slots.items():
                if slot["want"] is not None and not operator_lease_valid(slot["owner"]):
                    lost.append(receiver)
                elif (slot["state"] == "ACTIVE" and not slot["watch_due"] and slot["watch_ms"] is not None
                      and now_ms - slot["watch_ms"] >= WATCH_MS):
                    slot.update(watch_ms=int(now_ms), watch_due=True)
                    spawn = self._enqueue(receiver) or spawn
        if spawn:
            self._start_worker()  # without a thread the watch waits for the next request or stop
        for receiver in lost:
            self.stop(receiver, "OPERATOR_LEASE_LOST")

    def labrx_hold(self, receiver, holder):
        """labrx mode: the receiver stays with labrx (one holder) until labrx_release. Refused
        while an engine lease is granted, starting, stopping or in FAULT."""
        if receiver not in RECEIVERS or type(holder) is not str or not holder:
            return _refused("ENGINE_LEASE_BAD_REQUEST")
        with self._lock:
            slot = self._slots[receiver]
            if self._closed:
                return _refused("ENGINE_LEASE_CLOSED")
            if slot["want"] is not None or slot["running"] is not None or slot["state"] != "IDLE":
                return _refused("ENGINE_LEASE_BUSY", receiver=receiver)
            if slot["labrx"] not in (None, holder):
                return _refused("ENGINE_LEASE_LABRX_HOLDS", receiver=receiver)
            slot["labrx"] = holder
        return {"ok": True, "receiver": receiver}

    def labrx_release(self, receiver, holder):
        """True when holder held receiver in labrx mode and has released it."""
        with self._lock:
            slot = self._slots.get(receiver)
            if slot is None or slot["labrx"] != holder:
                return False
            slot["labrx"] = None
        return True

    def status(self):
        with self._lock:
            receivers = {}
            for receiver, slot in self._slots.items():
                engine = slot["want"] or slot["running"]
                receivers[receiver] = {"state": slot["state"], "engine": engine, "owner": slot["owner"],
                                       "unit": None if engine is None else unit_name(engine, receiver),
                                       "products": None if engine is None else products_dir(engine, receiver),
                                       "mode": "labrx" if engine is None and slot["state"] == "IDLE" else "engine",
                                       "labrx_held": slot["labrx"] is not None,
                                       "last_error": slot["last_error"], "last_stop": slot["last_stop"]}
            return {"enabled": True, "closed": self._closed, "receivers": receivers}

    def close(self):
        """labd exit: no new lease, and a stop of every running unit that does not wait for it
        (BindsTo=srrx.service stops them too when srrx.service goes down)."""
        with self._lock:
            self._closed = True
            running = [(r, s["running"]) for r, s in self._slots.items() if s["running"] is not None]
            for slot in self._slots.values():
                if slot["want"] is not None or slot["running"] is not None:
                    slot["last_stop"] = "DAEMON_EXIT"
                slot.update(want=None, owner=None, generation=slot["generation"] + 1)
        for receiver, engine in running:
            self._run(["--no-block", "stop", unit_name(engine, receiver)], 5)

    # ---------------------------------------------------------------- worker side

    def _enqueue(self, receiver):
        """Caller holds the lock: queue a reconcile; True when the caller must start the worker."""
        if receiver not in self._pending:
            self._pending.append(receiver)
        if self._worker:
            return False
        self._worker = True
        return True

    def _start_worker(self):
        """Called without the lock; False when no thread could be started (e.g. TasksMax)."""
        try:
            self.start_thread(self._work)
            return True
        except RuntimeError:
            with self._lock:
                self._worker = False
            return False

    def _work(self):
        while True:
            with self._lock:
                if not self._pending:
                    self._worker = False
                    return
                receiver = self._pending.pop(0)
            try:
                self._reconcile(receiver)
            except Exception:
                with self._lock:
                    self._slots[receiver].update(want=None, owner=None, state="FAULT", last_error="ENGINE_LEASE_INTERNAL")

    def _run(self, args, timeout_s):
        try:
            return self.systemctl(args, timeout_s)
        except (OSError, ValueError, subprocess.SubprocessError):
            return None

    def _stop_units(self, receiver):
        """Stop every lease unit of receiver (stopping an inactive unit succeeds); True if all stopped."""
        return all([self._run(["stop", unit_name(engine, receiver)], STOP_TIMEOUT_S) == 0 for engine in ENGINES])

    def _reconcile(self, receiver):
        """Bring one slot to what it wants. A request or stop changes want and the generation, and
        every step re-reads them, so a stop that arrives during a handover is never lost."""
        slot = self._slots[receiver]
        while True:
            with self._lock:
                want, generation, running, watch = slot["want"], slot["generation"], slot["running"], slot["watch_due"]
                if want is not None and want == running and not watch:
                    slot["state"] = "ACTIVE"
                    return
                if want is None and running is None and slot["state"] == "IDLE":
                    return
                slot["watch_due"] = False
            if want is not None and want == running:  # the watch of an active lease
                if self._run(["--quiet", "is-active", unit_name(want, receiver)], STOP_TIMEOUT_S) == 0:
                    return
                with self._lock:
                    if slot["generation"] == generation:
                        slot.update(want=None, owner=None, last_error="ENGINE_LEASE_UNIT_EXITED",
                                    last_stop="UNIT_EXITED", generation=generation + 1)
                continue
            # Handover 1/4, stop: every lease unit of this receiver, so no previous engine keeps it.
            with self._lock:
                slot["state"] = "STARTING" if want is not None else "STOPPING"
            if not self._stop_units(receiver):
                with self._lock:
                    slot.update(want=None, owner=None, running=None, state="FAULT",
                                last_error="ENGINE_LEASE_STOP_FAILED", generation=slot["generation"] + 1)
                return
            # 2/4, release: nothing of the previous engine remains on this receiver.
            with self._lock:
                slot["running"] = None
                if want is None or slot["generation"] != generation:
                    if slot["want"] is None:
                        slot["state"] = "IDLE"
                        return
                    continue
            # 3/4, re-enumeration check; 4/4, start.
            code = self.check_node(receiver)
            if code is None:
                with self._lock:
                    if slot["generation"] != generation:
                        continue
                if self._run(["start", unit_name(want, receiver)], START_TIMEOUT_S) == 0:
                    with self._lock:
                        slot["running"] = want  # a stop that arrived meanwhile stops it in the next round
                    continue
                code = "ENGINE_LEASE_START_FAILED"
            with self._lock:
                if code == "ENGINE_LEASE_START_FAILED":
                    slot["running"] = want  # a failed start may still have left a unit behind
                if slot["generation"] != generation:
                    continue
                slot.update(want=None, owner=None, state="IDLE", last_error=code, generation=generation + 1)
                if code != "ENGINE_LEASE_START_FAILED":
                    return
                slot["state"] = "STOPPING"  # stopped in the next round, before labrx may take the receiver

    def _systemctl(self, args, timeout_s):
        """`systemctl --no-ask-password <args>`; polkit_rule() authorizes start and stop for labd."""
        completed = subprocess.run([SYSTEMCTL, "--no-ask-password", *args], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=dict(_SYSTEMCTL_ENV),
                                   cwd="/", close_fds=True, timeout=timeout_s, check=False)
        return completed.returncode
