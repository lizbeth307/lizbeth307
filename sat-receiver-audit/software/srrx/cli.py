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
    gnss = sub.add_parser("gnss_reset", help="One bounded LC76G RESET_N pulse; needs your own valid lease (e.g. while hold runs)")
    gnss.add_argument("--width-ms", type=int, default=200, help="100..500 ms; labd enforces range, 30 s spacing and 3 per 15 min")
    sub.add_parser("gnss_config", help="Re-run the LC76G read-back/config and the PPS gate (labd --gnss gpsd|raw); needs your own lease; after a jamming flag only gnss_reset")
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
            # Disarm on exit only a session this invocation armed or leased and may
            # still hold. A refused renewal (another owner, or ours already expired
            # and tripped) or >=5 s since the last confirmed one means the session
            # may now be another operator's: lease expiry has already disarmed ours.
            owned = bool(args.arm)
            started = renewed = time.monotonic()
            try:
                while not args.seconds or time.monotonic() - started < args.seconds:
                    result = request_once(args.socket, {"op": "lease", "value": {"ttl_ms": 5000}})
                    if not result.get("ok"):
                        owned = False
                        print(json.dumps(result)); return 2
                    owned, renewed = True, time.monotonic()
                    status = request_once(args.socket, {"op": "status"})["data"]
                    if time.monotonic() - started > 2 and status["pico"].get("state") != "ACTIVE":
                        print(json.dumps(status)); return 2
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                if owned and time.monotonic() - renewed < 5:
                    request_once(args.socket, {"op": "disarm"})
            return 0
        if args.op == "set":
            request.update(op="control", name=args.name, value=args.value == "on")
        elif args.op == "gnss_reset":
            request["value"] = {"width_ms": args.width_ms}
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
