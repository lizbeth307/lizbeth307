"""Optional root sidecar: translate a qualified device shutdown into OS poweroff."""
import argparse
import subprocess
import time
from .daemon import request_once


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--socket", default="/run/srrx/control.sock")
    ap.add_argument("--execute", action="store_true", help="Required to run systemctl poweroff")
    args = ap.parse_args(argv)
    while True:
        try:
            status = request_once(args.socket, {"op": "status"})["data"]
            if (status.get("mode") == "HARDWARE" and status.get("hardware_qualified") is True
                    and status.get("pico", {}).get("state") == "SHUTTING_DOWN"):
                if not args.execute:
                    print("Qualified shutdown requested; dry run, no OS action", flush=True)
                    return 0
                result = request_once(args.socket, {"op": "off_now"})
                if not result.get("ok"):
                    raise RuntimeError("Pico OFF_NOW request refused")
                # Fixed grace is enforced by the MCU, independently of this
                # process. Kernel/PMIC poweroff must be qualified on the Q6A.
                subprocess.run(["/usr/bin/systemctl", "poweroff"], check=True)
                return 0
        except (OSError, ValueError, KeyError, RuntimeError):
            pass
        time.sleep(.25)


if __name__ == "__main__":
    raise SystemExit(main())
