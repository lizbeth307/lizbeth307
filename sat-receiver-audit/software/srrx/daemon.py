"""Local single-writer control service. Simulation is the default backend."""
import argparse
import ctypes as C
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import selectors
import signal
import socket
import stat
import struct
import sys
import threading
import time
import select
from .engine import Engine
from .hardware import SimHardware, LinuxHardware, load_mapping
from .link import SimLink, SerialLink

MAX_REQUEST = 4096
MAX_CLIENTS = 16


def reject_constant(value):
    raise ValueError("Non-finite JSON constant")


def soc_temp_c(root="/sys/class/thermal"):
    """Hottest Linux thermal zone in C. Any unreadable zone leaves it unknown."""
    zones = sorted(Path(root).glob("thermal_zone*/temp"))
    if not zones:
        raise OSError("no Linux thermal zone")
    return max(int(zone.read_text()) for zone in zones) / 1000


class SocTempSampler:
    """Reads soc_temp_c() on its own thread at most once a second, never in the 20 ms tick.

    PMIC ADC-TM or I2C-backed zones convert on every read; a slow or hung zone
    only ages the cached sample. A failed read or a sample older than max_age_s
    is unknown: HB then omits soc_temp_c and the Pico keeps its fan forced on.
    """
    def __init__(self, reader=soc_temp_c, period_s=1.0, max_age_s=3.0):
        self.reader, self.period_s, self.max_age_s = reader, period_s, max_age_s
        self.sample = None  # (celsius or None, monotonic s), replaced as one reference
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self._run, name="srrx-soc-temp", daemon=True)
        self.thread.start()

    def _run(self):
        while not self.stopping.is_set():
            try:
                value = self.reader()
            except Exception:
                value = None
            self.sample = (value, time.monotonic())
            self.stopping.wait(self.period_s)

    def __call__(self):
        sample = self.sample
        if sample is None or sample[0] is None or not 0 <= time.monotonic() - sample[1] <= self.max_age_s:
            raise OSError("SoC temperature unknown or stale")
        return sample[0]

    def close(self):
        self.stopping.set()


class _Timeval(C.Structure):
    _fields_ = [("tv_sec", C.c_long), ("tv_usec", C.c_long)]


class _Timex(C.Structure):
    """struct timex of include/uapi/linux/timex.h (64-bit Linux: time_t and long are 8 bytes)."""
    _fields_ = [("modes", C.c_uint), ("offset", C.c_long), ("freq", C.c_long), ("maxerror", C.c_long),
                ("esterror", C.c_long), ("status", C.c_int), ("constant", C.c_long), ("precision", C.c_long),
                ("tolerance", C.c_long), ("time", _Timeval), ("tick", C.c_long), ("ppsfreq", C.c_long),
                ("jitter", C.c_long), ("shift", C.c_int), ("stabil", C.c_long), ("jitcnt", C.c_long),
                ("calcnt", C.c_long), ("errcnt", C.c_long), ("stbcnt", C.c_long), ("tai", C.c_int),
                ("_reserved", C.c_int * 11)]


def kernel_clock(libc=None):
    """The kernel time state, read only: adjtimex(2) with modes 0, which needs no privilege and sets nothing.

    {"state": return value (TIME_ERROR 5 when STA_UNSYNC/STA_CLOCKERR), "status", "maxerror_us",
    "esterror_us"}; srrx.location.system_utc_verified decides. OSError when it cannot be read.
    """
    if sys.platform != "linux" or C.sizeof(C.c_long) != 8:
        raise OSError("kernel clock state needs 64-bit Linux")
    runtime = libc if libc is not None else C.CDLL(None, use_errno=True)
    timex = _Timex()
    timex.modes = 0
    state = runtime.adjtimex(C.byref(timex))
    if state == -1:
        raise OSError(C.get_errno(), "adjtimex read failed")
    return {"state": int(state), "status": int(timex.status), "maxerror_us": int(timex.maxerror),
            "esterror_us": int(timex.esterror)}


def request_once(path, request, timeout=2.0):
    data = json.dumps(request, allow_nan=False, separators=(",", ":")).encode() + b"\n"
    if len(data) > MAX_REQUEST:
        raise ValueError("Request too large")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(str(path))
        s.sendall(data)
        reply = bytearray()
        while b"\n" not in reply:
            block = s.recv(8192)
            if not block:
                raise OSError("Control service closed without a response")
            reply.extend(block)
            if len(reply) > 65536:
                raise ValueError("Oversize control response")
    return json.loads(reply.split(b"\n", 1)[0], parse_constant=reject_constant)


class Server:
    def __init__(self, path, engine):
        self.path, self.engine = Path(path), engine
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # mkdir accepts an existing directory as is; another user who owns it
        # could replace the bound socket and receive operator requests.
        info = os.lstat(self.path.parent)
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o022:
            raise RuntimeError("Control socket directory must be ours and not group/other writable")
        self.selector = selectors.DefaultSelector()
        self.clients, self.running = {}, True
        self.lock_fd = os.open(str(self.path) + ".lock", os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if self.path.is_symlink():
                raise RuntimeError("Refusing a symlink control socket")
            if self.path.exists():
                info = self.path.stat()
                if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.geteuid():
                    raise RuntimeError("Existing control path is not our stale socket")
                self.path.unlink()
            self.listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.listener.setblocking(False)
            self.listener.bind(str(self.path))
            os.chmod(self.path, 0o660)
            self.listener.listen(MAX_CLIENTS)
            self.selector.register(self.listener, selectors.EVENT_READ, None)
        except BaseException:
            os.close(self.lock_fd)


            raise

    def stop(self, *_):
        self.running = False

    def _drop(self, client):
        self.clients.pop(client, None)
        try:
            self.selector.unregister(client)
        except (KeyError, ValueError):
            pass
        client.close()

    def _request(self, state):
        try:
            request = json.loads(state["rx"].split(b"\n", 1)[0], parse_constant=reject_constant)
            if not isinstance(request, dict):
                raise ValueError("Request must be a JSON object")
            request["_owner"] = "uid:" + str(state["uid"])
            # Peer credentials come from the kernel, never caller-supplied JSON.
            if request.get("op") == "off_now" and state["uid"] != 0:
                result = {"ok": False, "error": "OFF_NOW is restricted to the root shutdown bridge"}
            else:
                result = self.engine.request(request, int(time.monotonic() * 1000))
        except (ValueError, TypeError, RecursionError, OverflowError, OSError, RuntimeError) as exc:
            result = {"ok": False, "error": str(exc)[:200]}
        state["tx"] = bytearray(json.dumps(result, allow_nan=False, separators=(",", ":")).encode() + b"\n")

    def run(self):
        try:
            while self.running:
                now = time.monotonic()
                self.engine.tick(int(now * 1000))
                for key, events in self.selector.select(.02):
                    if key.data is None:
                        client, _ = self.listener.accept()
                        if len(self.clients) >= MAX_CLIENTS:
                            client.close()
                            continue
                        client.setblocking(False)
                        uid = struct.unpack("3i", client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[1]
                        state = {"rx": bytearray(), "tx": None, "at": now, "uid": uid}
                        self.clients[client] = state
                        self.selector.register(client, selectors.EVENT_READ, state)
                    else:
                        client, state = key.fileobj, key.data
                        try:
                            if events & selectors.EVENT_READ:
                                data = client.recv(MAX_REQUEST + 1)
                                if not data:
                                    self._drop(client)
                                    continue
                                state["rx"].extend(data)
                                if len(state["rx"]) > MAX_REQUEST:
                                    self._drop(client)
                                    continue
                                if b"\n" in state["rx"]:
                                    self._request(state)
                                    self.selector.modify(client, selectors.EVENT_WRITE, state)
                            if events & selectors.EVENT_WRITE and state["tx"]:
                                sent = client.send(state["tx"])
                                del state["tx"][:sent]
                                if not state["tx"]:
                                    self._drop(client)
                        except (OSError, ValueError):
                            self._drop(client)
                for client, state in list(self.clients.items()):
                    if now - state["at"] > 2:
                        self._drop(client)
        finally:
            self.engine.close()
            for client in list(self.clients):
                self._drop(client)
            self.selector.close()
            self.listener.close()
            self.path.unlink(missing_ok=True)
            os.close(self.lock_fd)


def run_stdio(engine):
    """The same service through local pipes; no network/socket capability needed."""
    pending = bytearray()
    fd = sys.stdin.fileno()
    os.set_blocking(fd, False)
    try:
        while True:
            engine.tick(int(time.monotonic() * 1000))
            ready, _, _ = select.select([fd], [], [], .02)
            if not ready:
                continue
            data = os.read(fd, MAX_REQUEST + 1)
            if not data:
                break
            pending.extend(data)
            if len(pending) > MAX_REQUEST:
                raise ValueError("Oversize stdio request")
            while b"\n" in pending:
                line, _, remainder = pending.partition(b"\n")
                pending = bytearray(remainder)
                try:
                    request = json.loads(line, parse_constant=reject_constant)
                    if not isinstance(request, dict):
                        raise ValueError("Request must be an object")
                    request["_owner"] = "uid:" + str(os.geteuid())
                    if request.get("op") == "off_now" and os.geteuid() != 0:
                        result = {"ok": False, "error": "OFF_NOW requires root"}
                    else:
                        result = engine.request(request, int(time.monotonic() * 1000))
                except (ValueError, TypeError, RecursionError, OverflowError, OSError, RuntimeError) as exc:
                    result = {"ok": False, "error": str(exc)[:200]}
                print(json.dumps(result, allow_nan=False, separators=(",", ":")), flush=True)
    finally:
        engine.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--simulate", action="store_true")
    mode.add_argument("--hardware", action="store_true")
    ap.add_argument("--socket", default="/tmp/srrx/control.sock")
    ap.add_argument("--stdio", action="store_true", help="Local JSON lines through stdin/stdout, no sockets")
    ap.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--acceptance", type=Path)
    ap.add_argument("--i2c", help="Verified I2C2 device, e.g. from actual Q6A sysfs")
    ap.add_argument("--i2c0", help="Verified I2C0 device for INA228")
    ap.add_argument("--pico", help="Verified UART7 /dev/lab/pico symlink")
    ap.add_argument("--gnss", choices=("gpsd", "raw", "off"), default="off",
                    help="GNSS time orchestration around gnss_reset (srrx.gnss_orchestrator); off: plain pulse")
    ap.add_argument("--location-socket", default="/run/srrx-loc/location.sock")
    ap.add_argument("--timegate-socket", default="/run/srrx-timegate/timegate.sock")
    ap.add_argument("--gnss-latch", default="/var/lib/srrx-gnss/jamming-latch.json",
                    help="JAMMED latch across restarts (srrx.service StateDirectory=srrx-gnss)")
    args = ap.parse_args(argv)
    hardware = link = gnss = None
    if args.gnss != "off":
        # AF_UNIX requests to srrx-locationd and srrx-timegate plus one polkit-allowed
        # `systemctl start srrx-gnss-config.service`; labd itself opens no UART or chrony socket.
        from .gnss_orchestrator import GnssOrchestrator, JamLatchFile, LinuxGnssEffects
        gnss = GnssOrchestrator(LinuxGnssEffects(args.location_socket, args.timegate_socket), mode=args.gnss,
                                latch=JamLatchFile(args.gnss_latch))
    try:
        if args.hardware:
            from .commissioning import load_acceptance_bound
            if not all((args.acceptance, args.i2c, args.i2c0, args.pico)):
                ap.error("Hardware requires --acceptance, --i2c, --i2c0 and --pico; no guessed device paths")
            # A runtime start tolerates an RTC behind accepted_at (offline unit); the
            # 2026 floor and evidence-before-acceptance ordering still apply. The
            # digest of these exact bytes must equal the Pico qualification_record.
            acceptance, qualification = load_acceptance_bound(args.acceptance, args.project, clock_check=False)
            if datetime.fromisoformat(acceptance["accepted_at"].replace("Z", "+00:00")) > datetime.now(timezone.utc):
                print("labd: system clock is behind acceptance accepted_at; check RTC/time sync",
                      file=sys.stderr, flush=True)
            mapping = load_mapping(args.project / "design/E3.json")
            mapping.update(hardware_accepted=True, reset_confirmed=False)
            hardware = LinuxHardware(args.i2c, mapping)
            link = SerialLink(args.pico)
            # Sensor wiring and acceptance are explicit. No dummy telemetry is
            # ever substituted in the physical backend.
            from .runtime_telemetry import ProjectTelemetry
            telemetry = ProjectTelemetry(args.i2c0, hardware, acceptance)
            engine = Engine(hardware, link, simulated=False, acceptance=acceptance, telemetry_reader=telemetry,
                            soc_temp_reader=SocTempSampler(), qualification_record=qualification, gnss=gnss,
                            clock_reader=kernel_clock)
            # Pass plans: the sandboxed srrx-passes@.service through polkit, never in labd's cgroup (LOCATION.md).
            # Both take labd's own utc_verified (srrx.location.system_utc_verified; device check W-04/W-05).
            from .pass_jobs import PassPlanner
            engine.passes = PassPlanner(utc_verified=engine.utc_verified)
            # Attended LRPT passes: the static record/decode template units through polkit (software/RX.md).
            from .baseband_scheduler import BasebandScheduler
            engine.baseband = BasebandScheduler(planner=engine.passes, utc_verified=engine.utc_verified)
        else:
            hardware = SimHardware(load_mapping(args.project / "design/E3.json"))
            # Synthetic detector idle levels and power-good signals are labelled
            # simulation in every response, never recorded as measurements.
            hardware.set_inputs({n: False for n in hardware.inputs if n.startswith("DCS_")})
            link = SimLink(args.project)
            engine = Engine(hardware, link, simulated=True, gnss=gnss)
        if args.stdio:
            return run_stdio(engine) or 0
        server = Server(args.socket, engine)
        signal.signal(signal.SIGTERM, server.stop)
        signal.signal(signal.SIGINT, server.stop)
        print(json.dumps({"service": "labd", "mode": "HARDWARE" if args.hardware else "SIMULATION", "socket": args.socket}), flush=True)
        server.run()
    except (OSError, ValueError, RuntimeError) as exc:
        if link:
            link.close()
        if hardware:
            hardware.close()
        print("labd refused startup: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
