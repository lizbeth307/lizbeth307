#!/usr/bin/env python3
"""IMG-15: boot-level smoke of the produced Route A image under QEMU virt with UEFI (AAVMF).

This is a MODEL, not hardware evidence: QEMU virt and edk2/AAVMF replace the Q6A board and its
SPI UEFI 260120. The Q6A kernel 6.18.2-4-qcom itself boots on virt when its config has VIRTIO_BLK,
VIRTIO_PCI, PCI_HOST_GENERIC and SERIAL_AMBA_PL011 built in (checked from image-facts.json
kernel_deb_config). The smoke works on a sparse COPY of the image; only the copy's lab entries
change: no devicetree line (QEMU supplies the virt DT; the Q6A DTB would describe the wrong
machine), console=ttyAMA0 and a systemd.run= report command. systemd-boot, the slot kernel and
initramfs, root A/B, fstab, units, srrx-boot-check and systemd-bless-boot run as built.
systemd.run= redirects default.target to kernel-command-line.target, so the report command
(bootchain.py smoke-report) first starts multi-user.target, which queues the regular chain
basic.target -> systemd-bless-boot -> boot-complete.target -> srrx-boot-check; the graphical
session is outside the model.

Scenarios, one QEMU boot each (-no-reboot; systemd.run_*_action=poweroff ends the boot):
  1 trial-a-blessed  labA+3 newest: boot-check passes, boot-complete.target, bless -> labA.conf
  2 trial-b-fails    labB+1 newest with one required token removed: boot-check fails, no bless,
                     systemd-boot leaves labB+0-1.conf (no tries left)
  3 fallback-a       the bad labB sorts last: the blessed labA boots again
Every boot also checks: no pending jobs, no failed unit beyond the scenario's expected ones (only
srrx-boot-check.service on the boot that must fail), srrx.service inactive and disabled, the recipe
masks in effect (gdm.service and gdm3.service among them, and display-manager.service resolves to
the mask), every SR-RX service account present with the UID/GID of the build manifest, and the
package closure as built (W2 IMG-2: closure versions installed, systemd-timesyncd gone, _chrony and
gpsd with the manifest ids, chrony.service active, gpsd as the staged GNSS mode decides (socket
listening, service socket-activated), the built chrony.conf); a boot-check unit in the wrong state carries its journal of that boot into the mismatches, and every
unexpected failed unit its bounded `systemctl status` tail (address-like tokens removed). srrx-boot-check accepts the smoke's own tokens (bootchain.smoke_tokens) only
inside a VM (systemd-detect-virt), so every other extra token of an edited entry still fails it. The first slot A boot also runs selftest.py offline on a read-only view of the booted root
and ESP (bootchain.live_selftest): its FAIL/BLOCKED rows must equal the build-time rows on root A,
plus INTERPRETER_ROWS when the image's python3 lacks numpy. Bench gates W-03 (rollback on the Q6A)
and W-10 (DTB provenance) stay OPEN.
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


def smoke_options(config, slot, drop=None, selftest=False):
    tokens = bootchain.cmdline(config["base_cmdline_without_root"], bootchain.root_partuuid(config, slot), config["lime_build"]).split(" ")
    if drop:
        tokens.remove(drop)
    return " ".join(tokens + bootchain.smoke_tokens(selftest))


def smoke_entry(config, slot, version, drop=None, selftest=False):
    files = config["slots"][slot]
    return ("title SR-RX slot {s} QEMU smoke ({k})\nsort-key {sk}\nversion {v}\nlinux {l}\ninitrd {i}\noptions {o}\n"
            .format(s=slot, k=config["kernel_version"], sk=bootchain.SORT_KEY, v=version, l=files["kernel"], i=files["initrd"],
                    o=smoke_options(config, slot, drop, selftest)))


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


RESCUE_ENTRIES = ["labA-rescue.conf", "labB-rescue.conf"]
# One QEMU boot each; "entries_after" is the exact lab*.conf set on the ESP after the boot.
# "selftest": the boot also runs selftest.py offline on the booted root (about 17 min under TCG),
# once, on the first slot A boot.
SCENARIOS = (
    ("trial-a-blessed", {"slot": "A", "boot_check": "BOOT_SELF_CHECK_OK", "boot_complete": "active", "bless": "active",
                         "bless_status": "good", "entries_after": sorted(["labA.conf", "labB.conf"] + RESCUE_ENTRIES), "selftest": True}),
    ("trial-b-fails", {"slot": "B", "boot_check": "BLOCKED", "boot_complete": "inactive", "bless": "inactive",
                       "bless_status": "indeterminate", "entries_after": sorted(["labA.conf", "labB+0-1.conf"] + RESCUE_ENTRIES),
                       "selftest": False}),
    # A blessed entry has no counter: systemd-bless-boot and boot-complete.target are not queued;
    # srrx-boot-check still runs (WantedBy=multi-user.target).
    ("fallback-a", {"slot": "A", "boot_check": "BOOT_SELF_CHECK_OK", "boot_complete": None, "bless": "inactive",
                    "bless_status": "clean", "entries_after": sorted(["labA.conf", "labB+0-1.conf"] + RESCUE_ENTRIES), "selftest": False}),
)
# Rows whose verdict depends on the interpreter that runs selftest.py, not on the root: the builder
# runs it with its own python3 and python3-numpy; the live run uses the image's python3, which has
# no numpy (r2 ships none; the HMI venv is IMG-10). Expected live-only exactly when numpy is absent.
# RX-14 (voice mask) and RX-04-bb (LRPT baseband recorder, srrx.baseband) both import numpy.
INTERPRETER_ROWS = {"RX-14": ["numpy_unavailable"], "RX-04-bb": ["numpy_unavailable"]}


def entry_plan(config):
    """Per scenario: (lab entries to remove, entries to write, entries to rewrite only if present).

    1: only the smoke pair, labA+3 (with the live selftest) newest and labB blessed.
    2: labB replaced by labB+1, newest, with a required token removed.
    3: nothing added; the labA.conf that scenario 1 left (blessed by systemd-bless-boot) is
       rewritten in place without the selftest, so its name and version stay as blessed. If
       scenario 1 did not bless it, nothing is created and the check reports the real state."""
    return (
        ("lab*", {"labA+3.conf": (config, "A", 3, None, True), "labB.conf": (config, "B", 1, None, False)}, {}),
        ("labB*", {"labB+1.conf": (config, "B", 4, BROKEN_TOKEN, False)}, {}),
        ("", {}, {"labA.conf": (config, "A", 3, None, False)}),
    )


def apply_entry_plan(entries_dir, plan):
    remove, writes, rewrites = plan
    entries_dir = Path(entries_dir)
    if remove:
        for old in entries_dir.glob(remove + ".conf"):
            if not old.name.endswith("-rescue.conf"):
                old.unlink()
    for fname, args in writes.items():
        (entries_dir / fname).write_text(smoke_entry(*args), encoding="ascii", newline="\n")
    for fname, args in rewrites.items():
        if (entries_dir / fname).is_file():
            (entries_dir / fname).write_text(smoke_entry(*args), encoding="ascii", newline="\n")


def expected_live_rows(build_rows, interpreter_numpy):
    rows = dict(build_rows)
    if interpreter_numpy is False:
        rows.update({k: v for k, v in INTERPRETER_ROWS.items() if k not in rows})
    return rows


def account_mismatches(observed, recorded):
    """`getent` lines of the booted slot (bootchain.smoke_report "accounts") against the builder's
    image-manifest.json accounts.service_accounts: every account present, with the same UID/GID."""
    if not recorded:
        return ["image-manifest.json records no service accounts (build_image.system_accounts)"]
    observed = observed or {}
    bad = []
    for name, entry in sorted(recorded.items()):
        fields = (observed.get(name) or "").split(":")
        if len(fields) < 3 or fields[0] != name:
            bad.append("account %s missing on the booted slot" % name)
            continue
        ids = (fields[2], fields[3] if len(fields) > 3 else None) if entry.get("kind") == "u" else (None, fields[2])
        want = (str(entry.get("uid")), str(entry.get("primary_gid"))) if entry.get("kind") == "u" else (None, str(entry.get("gid")))
        if ids != want:
            bad.append("account %s ids %r differ from the image manifest %r" % (name, ids, want))
    return bad


# W2 IMG-2: gpsd's units by the GNSS mode the image staged (system_files.gpsd_defaults). The package
# enables only gpsd.socket (debian/rules of gpsd 3.25-3ubuntu3.2: dh_installsystemd --no-enable
# --no-start gpsd.service), so in gpsd and off mode the socket listens and gpsd.service stays disabled
# until a client connects (nothing does in the model); in raw mode deploy.py stage masks both.
# {mode: {unit: {property: expected value}}}; "!failed" means any ActiveState but failed.
GNSS_UNIT_STATES = {
    "gpsd": {"gpsd.socket": {"ActiveState": "active"}, "gpsd.service": {"UnitFileState": "disabled", "ActiveState": "!failed"}},
    "off": {"gpsd.socket": {"ActiveState": "active"}, "gpsd.service": {"UnitFileState": "disabled", "ActiveState": "!failed"}},
    "raw": {"gpsd.socket": {"LoadState": "masked"}, "gpsd.service": {"LoadState": "masked"}},
}


def closure_mismatches(observed, recorded):
    """bootchain.closure_report of the booted slot against image-manifest.json package_closure: closure
    versions installed, removed packages gone, the accounts with the build's ids, chrony active,
    timesyncd not found, gpsd as the staged GNSS mode decides, chrony.conf as built."""
    if not recorded:
        return ["image-manifest.json records no package_closure (build_image.install_closure)"]
    if not observed or "unavailable" in observed:
        return ["no package closure report from the booted slot: %r" % (observed,)]
    bad = []
    dpkg = observed.get("dpkg") or {}
    for name, version in sorted(recorded["installed"].items()):
        if dpkg.get(name) != version + "\tinstalled":
            bad.append("package %s is %r on the booted slot, expected %s installed" % (name, dpkg.get(name), version))
    for name in recorded["removed"]:
        if (dpkg.get(name) or "\tnot-installed").split("\t")[-1] not in ("not-installed", "config-files"):
            bad.append("removed package %s is %r on the booted slot" % (name, dpkg.get(name)))
    for name, ids in sorted(recorded["accounts"].items()):
        fields = ((observed.get("accounts") or {}).get(name) or "").split(":")
        if len(fields) < 4 or fields[0] != name or (fields[2], fields[3]) != (str(ids["uid"]), str(ids["primary_gid"])):
            bad.append("package account %s %r differs from the image manifest %r" % (name, fields[2:4], ids))
    units = observed.get("units") or {}

    def state(unit, key="ActiveState"):
        return (units.get(unit) or {}).get(key)

    if state("chrony.service") != "active":
        bad.append("chrony.service %r, expected active" % state("chrony.service"))
    if state("systemd-timesyncd.service", "LoadState") != "not-found":
        bad.append("systemd-timesyncd.service LoadState %r, expected not-found" % state("systemd-timesyncd.service", "LoadState"))
    expected = GNSS_UNIT_STATES.get(recorded.get("gnss_mode"))
    if expected is None:
        bad.append("no gpsd expectation for the staged GNSS mode %r" % recorded.get("gnss_mode"))
    for unit, properties in sorted((expected or {}).items()):
        for key, want in sorted(properties.items()):
            got = state(unit, key)
            if (got == "failed") if want == "!failed" else (got != want):
                bad.append("%s %s %r, expected %s for the staged GNSS mode %r" % (unit, key, got, want, recorded.get("gnss_mode")))
    if observed.get("chrony_conf_sha256") != (recorded.get("chrony_conf") or {}).get("sha256"):
        bad.append("chrony.conf on the booted slot %r is not the built one" % observed.get("chrony_conf_sha256"))
    return bad


def check(scenario, result, expect, build_rows=None, accounts=None, closure=None):
    """Compare one boot with its expectation; every mismatch is listed (host-testable).
    accounts: image-manifest.json accounts.service_accounts (None: not compared);
    closure: image-manifest.json package_closure (None: not compared)."""
    report = result["report"] or {}
    bc = report.get("boot_check") or {}
    units = report.get("units") or {}

    def state(unit, key="ActiveState"):
        return (units.get(unit) or {}).get(key)

    observed = {"slot": bc.get("slot"), "boot_check": bc.get("status"), "boot_check_unit": state("srrx-boot-check.service"),
                "boot_complete": state("boot-complete.target"), "bless": state("systemd-bless-boot.service"),
                "bless_status": report.get("bless_boot_status"), "entries_after": result["entries_after"],
                "pending_jobs": report.get("pending_jobs"), "srrx_service": [state("srrx.service"), state("srrx.service", "UnitFileState")],
                "selftest": (report.get("selftest") or {}).get("status")}
    bad = []
    if result["qemu_exit"] != 0 or not report:
        bad.append("guest did not power off with a report (qemu exit %s)" % result["qemu_exit"])
    for key in ("slot", "boot_check", "boot_complete", "bless", "bless_status", "entries_after"):
        if expect[key] is not None and observed[key] != expect[key]:
            bad.append("%s: %r, expected %r" % (key, observed[key], expect[key]))
    want_unit = "active" if expect["boot_check"] == "BOOT_SELF_CHECK_OK" else "failed"
    if observed["boot_check_unit"] != want_unit:
        bad.append("srrx-boot-check.service %r, expected %r" % (observed["boot_check_unit"], want_unit))
        if report.get("boot_check_journal"):  # what the boot-time run printed (bootchain.smoke_report)
            bad.append("srrx-boot-check journal: " + report["boot_check_journal"][-1500:])
    if observed["pending_jobs"]:
        bad.append("jobs still pending: " + "; ".join(observed["pending_jobs"])[:300])
    allowed_failed = set() if expect["boot_check"] == "BOOT_SELF_CHECK_OK" else {"srrx-boot-check.service"}
    failed = sorted({line.split()[0] for line in report.get("failed_units") or [] if line.split()} - allowed_failed)
    if report and failed:
        bad.append("failed units: " + ",".join(failed))
        # The guest's bounded `systemctl status` tail of each one (bootchain.smoke_report failed_unit_status).
        status = report.get("failed_unit_status") or {}
        bad += ["failed unit status %s: %s" % (u, bootchain.redact_addresses(status[u])[-1500:]) for u in failed if status.get(u)]
    if observed["srrx_service"] != ["inactive", "disabled"]:
        bad.append("srrx.service must stay inactive and disabled without acceptance (IMG-06): %r" % observed["srrx_service"])
    masked = report.get("masked_units") or {}
    not_masked = sorted(u for u, p in masked.items() if (p or {}).get("LoadState") != "masked")
    if not masked or not_masked:
        bad.append("recipe masks not in effect: " + (",".join(not_masked) or "no mask report"))
    if accounts is not None and report:
        bad += account_mismatches(report.get("accounts"), accounts)
    if closure is not None and report:
        bad += closure_mismatches(report.get("package_closure"), closure)
    # graphical.target wants display-manager.service: r2's gdm3 alias must resolve to the recipe's gdm mask.
    display_manager = report.get("display_manager")
    if display_manager is not None and display_manager.get("LoadState") not in ("masked", "not-found"):
        bad.append("display-manager.service LoadState %r: the GNOME greeter is not masked" % display_manager.get("LoadState"))
    if expect["selftest"]:
        selftest = report.get("selftest") or {}
        live = selftest.get("fail_or_blocked_rows")
        want = expected_live_rows(build_rows or {}, selftest.get("interpreter_numpy"))
        interpreter_drift = [k for k in INTERPRETER_ROWS if k in want and k not in (build_rows or {}) and (live or {}).get(k) != want[k]]
        if build_rows is None or live is None or sorted(live) != sorted(want) or interpreter_drift:
            extra = {k: (live or {})[k] for k in sorted(set(live or {}) - set(want))}
            bad.append("live selftest FAIL/BLOCKED rows %r differ from the expected rows %r (build-time %r, interpreter numpy %r; "
                       "only live: %s; missing: %r; status %s)"
                       % (sorted(live or {}), sorted(want), sorted(build_rows or {}), selftest.get("interpreter_numpy"),
                          json.dumps(extra)[:400], sorted(set(want) - set(live or {})), selftest.get("status")))
    elif report.get("selftest") is not None:
        bad.append("selftest ran on a boot that does not ask for it")
    return dict(scenario=scenario, status="MODEL_FAIL" if bad else "MODEL_PASS", expected=expect, observed=observed,
                mismatches=bad, **result)


def smoke(image, manifest_path, facts_path, work, out, timeout=1800):
    """Three QEMU boots of a sparse copy; SMOKE_NOT_FEASIBLE when the kernel config, QEMU or AAVMF
    cannot run the model (main() --require-model turns that into a failure, as in CI)."""
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
    build_rows = (manifest.get("selftest_root_a") or {}).get("fail_or_blocked_rows")
    result["build_selftest_rows"] = build_rows
    accounts = (manifest.get("accounts") or {}).get("service_accounts") or {}  # empty: every boot reports the gap
    closure = manifest.get("package_closure") or {}  # likewise
    for index, ((name, expect), plan) in enumerate(zip(SCENARIOS, entry_plan(config)), 1):
        with Esp(copy, esp_dir) as esp:
            apply_entry_plan(esp / "loader/entries", plan)
            before = lab_entries(esp)
        vars_file = work / ("vars-%d.fd" % index)
        shutil.copyfile(FIRMWARE_VARS, vars_file)
        log = out / ("console-%d-%s.log" % (index, name))
        run_result = qemu(copy, vars_file, log, timeout + (bootchain.SMOKE_SELFTEST_LIMIT if expect["selftest"] else 0), accel)
        with Esp(copy, esp_dir, read_only=True) as esp:
            run_result["entries_before"], run_result["entries_after"] = before, lab_entries(esp)
        result["scenarios"].append(check(name, run_result, expect, build_rows, accounts, closure))
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
    parser.add_argument("--require-model", action="store_true",
                        help="CI: SMOKE_NOT_FEASIBLE is a failure (otherwise only MODEL_FAIL is); nothing booted is never green")
    args = parser.parse_args()
    try:
        result = smoke(args.image, args.manifest, args.facts or args.manifest.with_name("image-facts.json"), args.work, args.out, args.timeout)
    except (OSError, ValueError, SmokeError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "scenarios": [(s["scenario"], s["status"], s.get("mismatches"), s["observed"])
                                                                for s in result["scenarios"]]}, indent=2))
    accepted = ("MODEL_PASS",) if args.require_model else ("MODEL_PASS", "SMOKE_NOT_FEASIBLE")
    return 0 if result["status"] in accepted else 1


if __name__ == "__main__":
    sys.exit(main())
