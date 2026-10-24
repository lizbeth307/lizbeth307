#!/usr/bin/env python3
"""Receive-only bench timing of the production RX worker startup (review finding RX-02b).

Usage on the Q6A, with the receiver powered from an external bench USB hub, not
through an SR-RX EN branch:

  PYTHONPATH=software python3 deployment/linux_lab/rx_startup_bench.py \
      --backend rtl --branch RTLA --serial <USB serial> \
      --library-path /opt/srrx-vendor/lib/librtlsdr.so.2.<version> --library-sha256 <sha256> \
      --condition cold --runs 1 > rtla-cold-01.json

It starts no labd, never arms or powers a branch and uses no acceptance record:
it times the production labrx.WorkerSource (spawn, NumPy import, driver open
with bias OFF) and reads one block that stays in RAM. The guard is a labelled
no-op because nothing here is powered through SR-RX; it is never a labd status.
The library must pass the production owner/mode check (review finding RX-10).
Output is JSON on stdout only: no IQ, spectrum, bytecode or other file. The
physical gate stays OPEN; this log is one input to the gate's full procedure,
never a PASS.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import statistics
import sys

BRANCHES = {"rtl": ("RTLA", "RTLB"), "airspyhf": ("HFP",)}
DEFAULT_RATES = {"rtl": 1024000, "airspyhf": 768000}
PROPOSED_COLD_LIMIT_S = 5.0  # >= 2x margin to the 10 s production budget; an owner decision if exceeded
MAX_RUNS = 100


class BenchGuard:
    """No-op RX guard for a bench-powered receiver. It reports no labd state."""
    scope = "bench-no-labd-no-branch-power"

    def check(self):
        return {"scope": self.scope}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--backend", required=True, choices=sorted(BRANCHES))
    parser.add_argument("--branch", required=True, choices=("RTLA", "RTLB", "HFP"))
    parser.add_argument("--serial", required=True)
    parser.add_argument("--library-path", required=True)
    parser.add_argument("--library-sha256", required=True)
    parser.add_argument("--center-hz", type=int, default=100000000)
    parser.add_argument("--sample-rate", type=int)
    parser.add_argument("--condition", required=True, choices=("cold", "warm"),
                        help="cold: the first open after a full receiver power cycle (use --runs 1)")
    parser.add_argument("--runs", type=int, default=20)
    args = parser.parse_args(argv)
    if args.sample_rate is None:
        args.sample_rate = DEFAULT_RATES[args.backend]
    if args.branch not in BRANCHES[args.backend]:
        parser.error("backend/physical branch mismatch")
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{4,64}", args.serial):
        parser.error("explicit hardware serial required")
    if args.backend == "airspyhf" and not re.fullmatch(r"[0-9a-fA-F]{16}", args.serial):
        parser.error("AirspyHF serial must contain exactly 16 hex digits")
    if not re.fullmatch(r"[0-9a-f]{64}", args.library_sha256):
        parser.error("library SHA256 must be 64 lowercase hex digits")
    if not 1 <= args.runs <= MAX_RUNS:
        parser.error(f"runs must be 1..{MAX_RUNS}")
    if args.condition == "cold" and args.runs != 1:
        parser.error("a cold run is the first open after a power cycle: use --runs 1 per power cycle")
    return args


def summarize(values):
    if not values:
        return None
    return {"count": len(values), "min": round(min(values), 3), "p50": round(statistics.median(values), 3),
            "max": round(max(values), 3)}


def report(args, runs, budget_s, gate, refusal=None):
    ready = [run["ready_after_s"] for run in runs if run["ready_after_s"] is not None and run["error"] is None]
    stats = summarize(ready)
    complete = refusal is None and len(ready) == args.runs
    return {
        "schema": "srrx-rx-startup-bench-v1",
        "status": "REFUSED" if refusal else "MEASURED" if complete else "RUN_FAILED",
        "refusal": refusal,
        "scope": "bench-receiver-external-usb-hub-no-labd-no-acceptance",
        "backend": args.backend, "branch": args.branch, "serial": args.serial, "gate": gate,
        "condition": args.condition, "runs_requested": args.runs,
        "library_path": args.library_path, "library_sha256": args.library_sha256,
        "center_hz": args.center_hz, "sample_rate": args.sample_rate,
        "production_startup_budget_s": budget_s, "proposed_cold_limit_s": PROPOSED_COLD_LIMIT_S,
        "ready_after_s": stats,
        # Informative only: the gate's own procedure decides, never this script.
        "within_proposed_cold_limit": (stats["max"] <= PROPOSED_COLD_LIMIT_S
                                       if complete and args.condition == "cold" else None),
        "runs": runs,
        "architecture": platform.machine(), "kernel": platform.release(), "python": platform.python_version(),
        "physical_gate": "OPEN", "gate_status_changed": False, "labd_started": False,
        "branch_power_controlled": False, "acceptance_used": False, "rf_transmitted": False,
        "raw_iq_persisted": False, "files_written": False,
    }


def main(argv=None):
    args = parse_args(argv)
    # A deployed /opt/srrx is verified against an exact file list: no __pycache__
    # from these imports or from the spawn worker, which inherits the variable.
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.path.insert(0, str(args.project.resolve(strict=True) / "software"))
    from srrx import labrx, receivers
    gate = receivers.DRIVER_GATES[args.branch]
    runs = []
    try:
        receivers.validate_tuning(args.backend, args.center_hz, args.sample_rate)
        # Production rule: a root-owned real file at a canonical path, hashed from the open inode.
        receivers.verify_library(args.library_path, args.library_sha256)
        # This parent receives one IQ block into RAM: same core-dump protection as labrx.
        labrx._disable_worker_core_dumps()
    except (OSError, ValueError) as exc:
        print(json.dumps(report(args, runs, labrx.STARTUP_TIMEOUT_S, gate, str(exc)[:300]), indent=2, allow_nan=False))
        return 2
    # In-memory only, never written; the worker re-checks the library on its descriptor.
    record = {"backend": args.backend, "branch": args.branch, "serial": args.serial,
              "library_path": args.library_path, "library_sha256": args.library_sha256}
    guard, interrupted = BenchGuard(), False
    for index in range(1, args.runs + 1):
        source, error, count = labrx.WorkerSource(record, args.center_hz, args.sample_rate), None, None
        try:
            samples = source.read(guard)
            count = int(samples.size)
            del samples  # no sample value enters the report
        except (OSError, ValueError, RuntimeError) as exc:
            error = type(exc).__name__ + ": " + str(exc)[:200]
        except KeyboardInterrupt:
            error, interrupted = "interrupted", True
        finally:
            source.close()
        ready = source.ready_after_s
        runs.append({"run": index, "ready_after_s": None if ready is None else round(ready, 3),
                     "first_block_samples": count, "error": error,
                     "worker_exitcode": source.process.exitcode})
        if interrupted:
            break
    result = report(args, runs, labrx.STARTUP_TIMEOUT_S, gate)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 130 if interrupted else 0 if result["status"] == "MEASURED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
