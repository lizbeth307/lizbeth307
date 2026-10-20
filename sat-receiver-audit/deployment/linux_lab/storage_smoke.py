#!/usr/bin/env python3
"""Exercise guarded recording on a real guest-only virtual block filesystem."""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback


def command(args):
    return subprocess.run([str(x) for x in args], check=True, capture_output=True, text=True, timeout=60)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path("/opt/srrx"))
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    marker = json.loads(Path("/etc/srrx-linux-lab.json").read_text())
    if (os.geteuid() != 0 or platform.machine() != "aarch64" or
            marker != {"schema_version": 1, "environment": "qemu-arm64-linux-lab", "hardware_passthrough": False}
            or b"linux,dummy-virt" not in Path("/proc/device-tree/compatible").read_bytes().split(b"\0")):
        raise SystemExit("Only the dedicated ARM64 QEMU lab may run this mount test")
    sys.path.insert(0, str(args.project / "software"))
    from srrx.storage import StorageGuard, StorageRevoked
    from srrx.spectrum import validate_frame
    mount = Path("/mnt/srrx-t7-model")
    device = Path("/dev/disk/by-label/SRRXT7")
    mount.mkdir(exist_ok=True)
    if any(mount.iterdir()):
        raise SystemExit("New empty dedicated mount directory required")
    cases, guards = [], []
    mounted = False
    def check(condition, message):
        if not condition:
            raise RuntimeError(message)
    def case(name, operation):
        started = time.monotonic()
        try:
            result = operation()
            cases.append({"id": name, "status": "PASS", "evidence": result,
                          "elapsed_s": round(time.monotonic()-started, 3)})
        except Exception as error:
            cases.append({"id": name, "status": "FAIL", "error": repr(error),
                          "traceback": traceback.format_exc()[-4000:]})
            raise
    def revoked(operation):
        try:
            operation()
        except StorageRevoked as error:
            return str(error)
        raise RuntimeError("Storage operation unexpectedly accepted")
    report = {"status": "RUNNING", "scope": "actual Linux virtual ext4 block device; Samsung USB and physical power sequencing untested",
              "physical_verified": False, "hardware_qualified": False, "cases": cases}
    try:
        command(["mount", "-t", "ext4", "-o", "nodev,nosuid,noexec", device, mount])
        mounted = True
        def record():
            result = command([args.project / "venv/bin/python3", "-m", "srrx.labrx", "--simulate",
                "--frames", "2", "--fft-size", "64", "--storage-root", mount, "--storage-device", device,
                "--output", "latest.json", "--survey", "survey.jsonl"])
            latest = json.loads((mount / "latest.json").read_text())
            validate_frame(latest)
            survey = [json.loads(x) for x in (mount / "survey.jsonl").read_text().splitlines()]
            check(len(survey) == 2 and latest["source"] == "SIMULATION", "Unexpected capture provenance/count")
            for item in survey:
                validate_frame(item)
            return {"records": len(survey), "raw_iq_persisted": False, "cli_exit": result.returncode}
        case("actual_block_mount_masked_capture", record)
        guard = StorageGuard(mount, device)
        guards.append(guard)
        report["identity"] = guard.identity
        case("wrong_device_refused", lambda: {"error": revoked(lambda: StorageGuard(mount, "/dev/disk/by-label/SRRXRESULT"))})
        def bind_replace():
            command(["mount", "--bind", mount, mount])
            try:
                error = revoked(guard.check)
                check(guard.revoked, "Same-device bind mount did not revoke session")
            finally:
                command(["umount", mount])
            revoked(guard.check)
            return {"error": error, "same_st_dev_replacement_detected": True, "automatic_recovery": False}
        case("same_device_mount_id_change_revokes", bind_replace)
        guard.close()
        fresh = StorageGuard(mount, device)
        guards.append(fresh)
        previous = (mount / "latest.json").read_bytes()
        filler = mount / "synthetic-zero-fill"
        def full_disk():
            filled = 0
            with filler.open("wb", buffering=0) as output:
                try:
                    for _ in range(256):
                        filled += output.write(bytes(1024 * 1024))
                except OSError as error:
                    if error.errno != errno.ENOSPC:
                        raise
                else:
                    raise RuntimeError("Dedicated small volume did not reach ENOSPC")
            try:
                try:
                    fresh.atomic_json("latest.json", {"new": "x" * 16384})
                except OSError as error:
                    # The first failed commit preserves the actual filesystem
                    # errno. All later operations raise StorageRevoked.
                    check(error.errno == errno.ENOSPC, "Expected actual block-device ENOSPC")
                    message = str(error)
                else:
                    raise RuntimeError("Full-volume commit unexpectedly accepted")
                check(fresh.revoked, "ENOSPC did not permanently revoke the writer")
                check((mount / "latest.json").read_bytes() == previous, "Pre-commit ENOSPC lost previous record")
                revoked(fresh.check)
            finally:
                filler.unlink(missing_ok=True)
            return {"filled_bytes": filled, "error": message, "previous_sha256": hashlib.sha256(previous).hexdigest()}
        case("real_ENOSPC_preserves_previous_record", full_disk)
        fresh.close()
        detached = StorageGuard(mount, device)
        guards.append(detached)
        command(["umount", "-l", mount])
        mounted = False
        def lost():
            message = revoked(lambda: detached.atomic_json("rootfs-fallback.json", {"must_not_write": True}))
            check(not (mount / "rootfs-fallback.json").exists(), "Mount loss caused rootfs fallback write")
            return {"error": message, "fallback_file_created": False, "permanent_revocation": detached.revoked}
        case("actual_mount_loss_no_rootfs_fallback", lost)
        detached.close()
        report["status"] = "PASS"
    except Exception as error:
        report.update(status="FAIL", error=repr(error))
    finally:
        for guard in guards:
            guard.close()
        if mounted:
            command(["umount", mount])
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "cases": len(cases), "report": str(args.report)}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
