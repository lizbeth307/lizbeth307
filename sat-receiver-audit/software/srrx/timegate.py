"""srrx-timegate: chrony PPS select/noselect for labd only, over AF_UNIX, with a fixed argv.

chronyc 4.5 accepts selectopts only on chronyd's Unix command socket, i.e. from root or
the chrony user (chronyc(1), 4.5), so this helper runs as _chrony and labd (AF_UNIX
only, no chrony rights) asks it. Exactly two requests exist, each one line:

  PPS_SELECT    chronyc -n -h /run/chrony/chronyd.sock selectopts PPS -noselect; ... reselect
  PPS_NOSELECT  chronyc -n -h /run/chrony/chronyd.sock selectopts PPS +noselect; ... reselect

(build/07-pz-vstanovlennia.md:484). Only the peer UID of labd (SO_PEERCRED) is served;
any other peer is closed before a byte is read. No shell, no argument from the request,
no network: -h names the Unix socket, so chronyc never falls back to UDP 127.0.0.1.
Requests are handled one at a time; each chronyc call is bounded at CHRONYC_TIMEOUT_S.
"""
import argparse
import json
from pathlib import Path
import pwd
import signal
import socket
import subprocess
import sys

from .locationd import LocationdError, bind_socket, peer_uid

SOCKET_PATH = "/run/srrx-timegate/timegate.sock"
CHRONYC = "/usr/bin/chronyc"
CHRONY_SOCKET = "/run/chrony/chronyd.sock"
PEER_USER = "labd"
CHRONYC_TIMEOUT_S = 5
READ_TIMEOUT_S = 1.0
OPTIONS = {"PPS_SELECT": "-noselect", "PPS_NOSELECT": "+noselect"}
_ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}


def argv_for(command):
    """The two fixed chronyc invocations of one request (KeyError for anything else)."""
    base = (CHRONYC, "-n", "-h", CHRONY_SOCKET)
    return (base + ("selectopts", "PPS", OPTIONS[command]), base + ("reselect",))


def run_chronyc(argv):
    """0 only for a successful fixed chronyc call; output is never echoed."""
    try:
        return subprocess.run(list(argv), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=CHRONYC_TIMEOUT_S, env=_ENV,
                              close_fds=True, check=False).returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except OSError:
        return "EXEC"


class Gate:
    def __init__(self, peer_uid_allowed, runner=run_chronyc):
        self.peer, self.runner = peer_uid_allowed, runner
        self.last = None  # (command, ok) of the last executed request

    def handle(self, uid, line):
        if uid != self.peer:
            return {"ok": False, "error": "TIMEGATE_PEER_REFUSED"}
        command = line.decode("ascii", "replace") if type(line) is bytes else None
        if command not in OPTIONS:
            return {"ok": False, "error": "TIMEGATE_UNKNOWN_COMMAND"}
        for step, argv in zip(("selectopts", "reselect"), argv_for(command)):
            code = self.runner(argv)
            if code != 0:
                self.last = (command, False)
                return {"ok": False, "command": command,
                        "error": "TIMEGATE_CHRONYC_" + step.upper() + "_" + (code if type(code) is str else "EXIT")}
        self.last = (command, True)
        return {"ok": True, "command": command}


def serve_one(listener, gate):
    """Accept one connection and answer it; other peers are closed unread."""
    client, unused = listener.accept()
    with client:
        if peer_uid(client) != gate.peer:
            return False
        client.settimeout(READ_TIMEOUT_S)
        data = bytearray()
        try:
            while b"\n" not in data and len(data) <= 32:
                block = client.recv(33)
                if not block:
                    return False
                data.extend(block)
            line, sep, rest = bytes(data).partition(b"\n")
            reply = gate.handle(peer_uid(client), line) if sep and not rest and len(line) <= 32 else \
                {"ok": False, "error": "TIMEGATE_REQUEST_FRAMING"}
            client.sendall(json.dumps(reply, separators=(",", ":")).encode() + b"\n")
        except (OSError, socket.timeout):
            return False
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--socket", default=SOCKET_PATH)
    ap.add_argument("--peer-user", default=PEER_USER)
    args = ap.parse_args(argv)
    try:
        gate = Gate(pwd.getpwnam(args.peer_user).pw_uid)
        listener = bind_socket(args.socket, 0o666, backlog=4)
    except (LocationdError, OSError, KeyError) as exc:
        print("srrx-timegate refused startup: " + type(exc).__name__ + ": " + str(exc)[:160], file=sys.stderr)
        return 1
    listener.settimeout(1.0)  # the loop sees SIGTERM within a second
    stopping = []
    signal.signal(signal.SIGTERM, lambda *unused: stopping.append(True))
    signal.signal(signal.SIGINT, lambda *unused: stopping.append(True))
    print(json.dumps({"service": "srrx-timegate", "socket": args.socket, "commands": sorted(OPTIONS)}), flush=True)
    try:
        while not stopping:
            try:
                serve_one(listener, gate)
            except (socket.timeout, InterruptedError):
                continue
    finally:
        listener.close()
        Path(args.socket).unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
