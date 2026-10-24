#!/usr/bin/env python3
"""IMG-15: boot-level smoke of the produced Route A image under QEMU virt with UEFI (AAVMF).

This is a MODEL, not hardware evidence: QEMU virt and edk2/AAVMF replace the Q6A board and its
SPI UEFI 260120. The Q6A kernel 6.18.2-4-qcom itself boots on virt when its config has VIRTIO_BLK,
VIRTIO_PCI, PCI_HOST_GENERIC and SERIAL_AMBA_PL011 built in (checked from image-facts.json
kernel_deb_config). The smoke works on a sparse COPY of the image; only the copy's lab entries
change: no devicetree line (QEMU supplies the virt DT; the Q6A DTB would describe the wrong
machine), console=ttyAMA0 and a systemd.run= report command. systemd-boot, the slot kernel and
initramfs, root A/B, fstab, units, srrx-boot-check and systemd-bless-boot run as built.

Scenarios, one QEMU boot each (-no-reboot; systemd.run_*_action=poweroff ends the boot):
  1 trial-a-blessed  labA+3 newest: boot-check passes, boot-complete.target, bless -> labA.conf
  2 trial-b-fails    labB+1 newest with one required token removed: boot-check fails, no bless,
                     systemd-boot leaves labB+0-1.conf (no tries left)
  3 fallback-a       the bad labB sorts last: slot A boots again
Bench gates W-03 (rollback on the Q6A) and W-10 (DTB provenance) stay OPEN.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import bootchain  # noqa: E402
import recovery_kit  # noqa: E402

FIRMWARE_CODE = Path("/usr/share/AAVMF/AAVMF_CODE.fd")
FIRMWARE_VARS = Path("/usr/share/AAVMF/AAVMF_VARS.fd")
NEEDED_CONFIG = ("CONFIG_VIRTIO_BLK", "CONFIG_VIRTIO_PCI", "CONFIG_PCI_HOST_GENERIC", "CONFIG_SERIAL_AMBA_PL011", "CONFIG_EFI_STUB")
REPORT = re.compile(re.escape(bootchain.SMOKE_BEGIN) + r"(.*?)" + re.escape(bootchain.SMOKE_END), re.S)
BROKEN_TOKEN = "usbcore.usbfs_memory_mb=0"


class SmokeError(RuntimeError):
    pass


def run(argv, check=True, timeout=600):
    done = subprocess.run([str(a) for a in argv], capture_output=True, text=True, timeout=timeout)
    if check and done.returncode:
        raise SmokeError(" ".join(map(str, argv)) + " failed: " + (done.stdout + done.stderr)[-1500:])
    return done


class Esp:
    """Mount the ESP (partition 1) of the smoke copy through a 4K loop device."""

    def __init__(self, image, mountpoint, read_only=False):
        self.image, self.mountpoint, self.read_only = Path(image), Path(mountpoint), read_only

    def __enter__(self):
        argv = ["losetup", "--find", "--show", "--partscan", "--sector-size", "4096"] + (["--read-only"] if self.read_only else [])
        self.loop = run(argv + [self.image]).stdout.strip()
        backing = Path("/sys/block", self.loop[5:], "loop/backing_file").read_text().strip()
        if Path(backing).resolve() != self.image.resolve():
            run(["losetup", "-d", self.loop], check=False)
            raise SmokeError("loop device is not backed by the smoke copy")
        run(["udevadm", "settle"], check=False)
        part = self.loop + "p1"
        for _ in range(100):
            if os.path.exists(part):
                break
            time.sleep(0.1)
        self.mountpoint.mkdir(parents=True, exist_ok=True)
        run(["mount", "-t", "vfat", "-o", "ro" if self.read_only else "rw", part, self.mountpoint])
        return self.mountpoint

    def __exit__(self, *exc):
        run(["umount", self.mountpoint], check=False)
        run(["losetup", "-d", self.loop], check=False)


def smoke_options(config, slot, drop=None):
    tokens = bootchain.cmdline(config["base_cmdline_without_root"], bootchain.root_partuuid(config, slot), config["lime_build"]).split(" ")
    if drop:
        tokens.remove(drop)
    return " ".join(tokens + ["console=ttyAMA0,115200",
                              'systemd.run="/usr/bin/python3 -I -B /opt/srrx/deployment/image/bootchain.py smoke-report"',
                              "systemd.run_success_action=poweroff", "systemd.run_failure_action=poweroff"])


def smoke_entry(config, slot, version, drop=None):
    files = config["slots"][slot]
    return ("title SR-RX slot {s} QEMU smoke ({k})\nsort-key {sk}\nversion {v}\nlinux {l}\ninitrd {i}\noptions {o}\n"
            .format(s=slot, k=config["kernel_version"], sk=bootchain.SORT_KEY, v=version, l=files["kernel"], i=files["initrd"],
                    o=smoke_options(config, slot, drop)))


def lab_entries(esp):
    return sorted(p.name for p in (Path(esp) / "loader/entries").glob("lab*.conf"))


def qemu(image, vars_file, log, timeout, accel):
    argv = ["qemu-system-aarch64", "-machine", "virt", "-accel", accel, "-cpu", "host" if accel == "kvm" else "max",
            "-smp", "4", "-m", "4096", "-nodefaults", "-display", "none", "-monitor", "none", "-no-reboot", "-nic", "none",
            "-serial", "file:" + str(log),
            "-drive", "if=pflash,format=raw,unit=0,readonly=on,file=" + str(FIRMWARE_CODE),
            "-drive", "if=pflash,format=raw,unit=1,file=" + str(vars_file),
            "-drive", "if=none,id=disk0,format=raw,cache=unsafe,file=" + str(image),
            "-device", "virtio-blk-pci,drive=disk0,logical_block_size=4096,physical_block_size=4096,bootindex=0",
            "-device", "virtio-rng-pci"]
    started = time.monotonic()
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        code = done.returncode
    except subprocess.TimeoutExpired:
        code = "TIMEOUT"
    text = Path(log).read_text(encoding="utf-8", errors="replace") if Path(log).is_file() else ""
    match = REPORT.findall(text)
    report = None
    if match:
        try:
            report = json.loads(match[-1].replace("\r", "").replace("\n", ""))
        except ValueError:
            report = {"unparsed": match[-1][:2000]}
    return {"qemu_exit": code, "seconds": round(time.monotonic() - started, 1), "report": report, "console_bytes": len(text)}


def check(scenario, result, expect):
    report = result["report"] or {}
    bc = report.get("boot_check") or {}
    observed = {"slot": bc.get("slot"), "boot_check": bc.get("status"), "entries_after": result["entries_after"]}
    ok = (result["qemu_exit"] == 0 and observed["slot"] == expect["slot"] and observed["boot_check"] == expect["boot_check"]
          and expect["entry_after"] in result["entries_after"])
    return dict(scenario=scenario, status="MODEL_PASS" if ok else "MODEL_FAIL", expected=expect, observed=observed, **result)


def smoke(image, manifest_path, facts_path, work, out, timeout=1800):
    if sys.platform != "linux" or platform.machine() != "aarch64" or os.geteuid() != 0:
        raise SmokeError("the smoke runs as root on an aarch64 Linux builder")
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("status") != "CANDIDATE_IMAGE_BUILT" or manifest.get("route") != "A":
        raise SmokeError("needs a built Route A candidate (image-manifest.json)")
    facts = json.loads(Path(facts_path).read_text(encoding="utf-8"))
    kconfig = facts.get("kernel_deb_config") or {}
    work, out = Path(work), Path(out)
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    result = {"schema_version": 1, "kind": "QEMU virt + AAVMF model of the Route A boot chain (not Q6A hardware)",
              "kernel_config": {k: kconfig.get(k) for k in NEEDED_CONFIG}, "hardware_ready": False,
              "bench_gates_open": ["W-03", "W-10"], "scenarios": []}
    missing = [k for k in NEEDED_CONFIG if kconfig.get(k) != "y"]
    if missing or not shutil.which("qemu-system-aarch64") or not FIRMWARE_CODE.is_file():
        result.update(status="SMOKE_NOT_FEASIBLE", why="kernel config lacks " + ",".join(missing) if missing else "QEMU or AAVMF missing")
        (out / "smoke-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result
    accel = "kvm" if os.path.exists("/dev/kvm") else "tcg"
    result["accel"] = accel
    result["qemu"] = run(["qemu-system-aarch64", "--version"]).stdout.splitlines()[0]
    config = bootchain.validate_ab(manifest["boot_config"])
    copy = work / "smoke.raw"
    if copy.exists():
        copy.unlink()
    recovery_kit.sparse_copy(image, copy)
    esp_dir = work / "esp"
    scenarios = (
        ("trial-a-blessed", {"labA+3.conf": (config, "A", 3, None), "labB.conf": (config, "B", 1, None)},
         {"slot": "A", "boot_check": "BOOT_SELF_CHECK_OK", "entry_after": "labA.conf"}),
        ("trial-b-fails", {"labB+1.conf": (config, "B", 4, BROKEN_TOKEN)},
         {"slot": "B", "boot_check": "BLOCKED", "entry_after": "labB+0-1.conf"}),
        ("fallback-a", {}, {"slot": "A", "boot_check": "BOOT_SELF_CHECK_OK", "entry_after": "labB+0-1.conf"}),
    )
    for index, (name, writes, expect) in enumerate(scenarios, 1):
        with Esp(copy, esp_dir) as esp:
            entries_dir = esp / "loader/entries"
            if writes:
                for old in entries_dir.glob("lab*.conf"):
                    if not old.name.endswith("-rescue.conf") and (index == 1 or old.name.startswith("labB")):
                        old.unlink()
                for fname, args in writes.items():
                    (entries_dir / fname).write_text(smoke_entry(*args), encoding="ascii", newline="\n")
            before = lab_entries(esp)
        vars_file = work / ("vars-%d.fd" % index)
        shutil.copyfile(FIRMWARE_VARS, vars_file)
        log = out / ("console-%d-%s.log" % (index, name))
        run_result = qemu(copy, vars_file, log, timeout, accel)
        with Esp(copy, esp_dir, read_only=True) as esp:
            run_result["entries_before"], run_result["entries_after"] = before, lab_entries(esp)
        result["scenarios"].append(check(name, run_result, expect))
        (out / "smoke-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    result["status"] = "MODEL_PASS" if all(s["status"] == "MODEL_PASS" for s in result["scenarios"]) else "MODEL_FAIL"
    (out / "smoke-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    copy.unlink()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--facts", type=Path, help="image-facts.json (default: next to the manifest)")
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800, help="seconds per QEMU boot")
    args = parser.parse_args()
    try:
        result = smoke(args.image, args.manifest, args.facts or args.manifest.with_name("image-facts.json"), args.work, args.out, args.timeout)
    except (OSError, ValueError, SmokeError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "scenarios": [(s["scenario"], s["status"], s["observed"]) for s in result["scenarios"]]},
                     indent=2))
    return 0 if result["status"] in ("MODEL_PASS", "SMOKE_NOT_FEASIBLE") else 1


if __name__ == "__main__":
    sys.exit(main())
