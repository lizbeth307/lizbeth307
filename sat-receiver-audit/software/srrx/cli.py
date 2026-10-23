"""Local CLI for the SR-RX single-writer service."""
import argparse
import json
import sys
import time
from .daemon import request_once


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--socket", default="/tmp/srrx/control.sock")
    sub = p.add_subparsers(dest="op", required=True)
    for name in ("status", "arm", "recover", "disarm", "shutdown", "off_now"):
        sub.add_parser(name)
    set_cmd = sub.add_parser("set")
    set_cmd.add_argument("name")
    set_cmd.add_argument("value", choices=["on", "off"])
    for name in ("mode", "lease", "relay", "confirmations"):
        cmd = sub.add_parser(name)
        cmd.add_argument("value", help="JSON value, see software/README.md")
    route = sub.add_parser("route")
    route.add_argument("receiver", choices=["RTLA", "RTLB", "LIME"])
    route.add_argument("value", help="JSON routing selection")
    sim = sub.add_parser("sim")
    sim.add_argument("name")
    sim.add_argument("value", help="JSON value; unavailable on the physical backend")
    hold = sub.add_parser("hold", help="Keep the local operator lease alive; Ctrl-C disarms")
    hold.add_argument("--arm", action="store_true", help="Request one explicit arm before holding")
    hold.add_argument("--seconds", type=float, default=0, help="0=until Ctrl-C")
    args = p.parse_args(argv)
    request = {"op": args.op}
    try:
        if args.op == "hold":
            if not 0 <= args.seconds <= 86400:
                raise ValueError("hold duration must be 0..86400 seconds")
            if args.arm:
                result = request_once(args.socket, {"op": "arm"})
                if not result.get("ok"):
                    print(json.dumps(result)); return 2
            # Disarm on exit only a session this invocation armed or leased;
            # a refused lease must never trip another operator's session.
            owned = bool(args.arm)
            started = time.monotonic()
            try:
                while not args.seconds or time.monotonic() - started < args.seconds:
                    result = request_once(args.socket, {"op": "lease", "value": {"ttl_ms": 5000}})
                    if not result.get("ok"):
                        print(json.dumps(result)); return 2
                    owned = True
                    status = request_once(args.socket, {"op": "status"})["data"]
                    if time.monotonic() - started > 2 and status["pico"].get("state") != "ACTIVE":
                        print(json.dumps(status)); return 2
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                if owned:
                    request_once(args.socket, {"op": "disarm"})
            return 0
        if args.op == "set":
            request.update(op="control", name=args.name, value=args.value == "on")
        elif args.op in {"mode", "lease", "relay", "route", "sim", "confirmations"}:
            request["value"] = json.loads(args.value)
            if args.op == "route":
                request["receiver"] = args.receiver
            elif args.op == "sim":
                request["name"] = args.name
        result = request_once(args.socket, request)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0 if result.get("ok") else 2
    except (ValueError, OSError) as exc:
        print("labctl: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
