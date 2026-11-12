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
  4 update-b-trial-blessed (--update-model, W2 IMG-UPD; its own fresh copy) update_slot.py A->B on the
                     builder, the trial labB+3 boots, boot-check passes, bless -> labB.conf; the guest only plans
Every boot also checks: no pending jobs, no failed unit beyond the scenario's expected ones (only
srrx-boot-check.service on the boot that must fail), srrx.service inactive and disabled, the recipe
masks in effect (gdm.service and gdm3.service among them, and display-manager.service resolves to
the mask), every SR-RX service account present with the UID/GID of the build manifest, and the
package closure as built (W2 IMG-2: closure versions installed, systemd-timesyncd gone, _chrony and
gpsd with the manifest ids, chrony.service active, gpsd as the staged GNSS mode decides (socket
listening, service socket-activated), the built chrony.conf); a boot-check unit in the wrong state carries its journal of that boot into the mismatches, and every
unexpected failed unit its bounded `systemctl status` tail (address-like tokens removed). srrx-boot-check accepts the smoke's own tokens (bootchain.smoke_tokens) only
inside a VM (systemd-detect-virt), so every other extra token of an edited entry still fails it. The first slot A boot also runs selftest.py offline on a read-only view of the booted root
and ESP (bootchain.live_selftest) under the image's /opt/srrx/passes-venv (W2 IMG-3): its FAIL/BLOCKED rows must equal the
build-time rows on root A, plus INTERPRETER_ROWS only when the interpreter lacks numpy; the same boot reports each
venv's numpy and an offscreen PySide6 QApplication of /opt/srrx/venv (bootchain.venv_report), compared with the
manifest's venvs (venv_mismatches). Every boot also runs `modprobe pps_gpio` after the rest of the report (W2 IMG-4): the
builder-built module must load, and its file, SHA-256 and vermagic must be the manifest's (pps_mismatches); with the
session in the image, display-manager.service must resolve to greetd.service, gdm staying masked. --session runs the
separate greetd/labwc scenario instead (session_smoke, session-report.json). Bench gates W-03 (rollback on the Q6A),
W-10 (DTB provenance) and the display/touch gates of W1-2 stay OPEN.
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
import update_slot  # noqa: E402  (W2 IMG-UPD scenario 4)

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


def smoke_options(config, slot, drop=None, selftest=False, session=False):
    tokens = bootchain.cmdline(config["base_cmdline_without_root"], bootchain.root_partuuid(config, slot), config["lime_build"]).split(" ")
    if drop:
        tokens.remove(drop)
    return " ".join(tokens + bootchain.smoke_tokens(selftest, session))


def smoke_entry(config, slot, version, drop=None, selftest=False, session=False):
    files = config["slots"][slot]
    return ("title SR-RX slot {s} QEMU smoke ({k})\nsort-key {sk}\nversion {v}\nlinux {l}\ninitrd {i}\noptions {o}\n"
            .format(s=slot, k=config["kernel_version"], sk=bootchain.SORT_KEY, v=version, l=files["kernel"], i=files["initrd"],
                    o=smoke_options(config, slot, drop, selftest, session)))


def lab_entries(esp):
    return sorted(p.name for p in (Path(esp) / "loader/entries").glob("lab*.conf"))


def qemu(image, vars_file, log, timeout, accel, extra=()):
    argv = ["qemu-system-aarch64", "-machine", "virt", "-accel", accel, "-cpu", "host" if accel == "kvm" else "max",
            "-smp", "4", "-m", "4096", "-nodefaults", "-display", "none", "-monitor", "none", "-no-reboot", "-nic", "none",
            "-serial", "file:" + str(log),
            "-drive", "if=pflash,format=raw,unit=0,readonly=on,file=" + str(FIRMWARE_CODE),
            "-drive", "if=pflash,format=raw,unit=1,file=" + str(vars_file),
            "-drive", "if=none,id=disk0,format=raw,cache=unsafe,file=" + str(image),
            "-device", "virtio-blk-pci,drive=disk0,logical_block_size=4096,physical_block_size=4096,bootindex=0",
            "-device", "virtio-rng-pci"] + list(extra)
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
# runs it with its own python3 and python3-numpy; the live run uses the image's passes-venv since W2
# IMG-3 (r2's python3 has no numpy). Expected live-only exactly when that interpreter lacks numpy, which
# venv_mismatches already reports for an image whose manifest records the venv with numpy.
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


def venv_mismatches(observed, recorded, selftest):
    """W2 IMG-3: bootchain.venv_report of the booted slot and the live selftest's interpreter against image-manifest.json
    venvs.venvs: each venv's numpy version as built, the HMI venv's offscreen QApplication with the built Qt version,
    and the live selftest under passes-venv with numpy whenever the build recorded numpy there."""
    if not recorded:
        return ["image-manifest.json records no venvs (build_image.build_venvs)"]
    if not observed or "unavailable" in observed:
        return ["no venv report from the booted slot: %r" % (observed,)]
    bad = []
    for venv, entry in sorted(recorded.items()):
        live = observed.get(venv) or {}
        numpy = (live.get("numpy") or {}).get("numpy")
        if not live.get("present") or numpy != entry.get("numpy"):
            bad.append("%s numpy %r on the booted slot (%s), %r in the image manifest"
                       % (venv, numpy, json.dumps(live)[:300], entry.get("numpy")))
        if "qt_offscreen" in entry:
            built = entry["qt_offscreen"].get("result") or {}
            qt = live.get("qt_offscreen") or {}
            if qt.get("platform") != "offscreen" or qt.get("qt") != built.get("qt"):
                bad.append("%s offscreen QApplication %s on the booted slot, built %s"
                           % (venv, json.dumps(qt)[:300], json.dumps(built)[:200]))
    passes = recorded.get(bootchain.SELFTEST_PYTHON.parent.parent.as_posix()) or {}
    selftest = selftest or {}
    if passes.get("numpy") and (selftest.get("interpreter") != bootchain.SELFTEST_PYTHON.as_posix() or selftest.get("interpreter_numpy") is not True):
        bad.append("live selftest ran with %r (numpy %r), expected %s with numpy %s"
                   % (selftest.get("interpreter"), selftest.get("interpreter_numpy"), bootchain.SELFTEST_PYTHON.as_posix(), passes["numpy"]))
    return bad


def pps_mismatches(observed, recorded):
    """W2 IMG-4: bootchain.pps_report of the booted slot against image-manifest.json pps_gpio: modprobe pps_gpio succeeds,
    the module is live, and its file, SHA-256 and vermagic are the built ones (QEMU virt has no /pps-gnss node: no device)."""
    if not recorded or recorded.get("status") != "INSTALLED":
        return ["image-manifest.json records no installed pps-gpio module (build_image.build_pps_module): %r" % ((recorded or {}).get("status"),)]
    if not observed or "unavailable" in observed:
        return ["no pps_gpio report from the booted slot: %r" % (observed,)]
    bad = []
    if (observed.get("modprobe") or {}).get("exit_code") != 0:
        bad.append("modprobe pps_gpio failed on the booted slot: %s" % json.dumps(observed.get("modprobe"))[:400])
    if not observed.get("loaded") or observed.get("initstate") != "live":
        bad.append("pps_gpio is not live on the booted slot (loaded %r, initstate %r)" % (observed.get("loaded"), observed.get("initstate")))
    for key, want in (("filename", recorded.get("path")), ("sha256", recorded.get("sha256")), ("vermagic", recorded.get("vermagic"))):
        if observed.get(key) != want:
            bad.append("pps_gpio %s %r on the booted slot, %r in the image manifest" % (key, observed.get(key), want))
    if (observed.get("vermagic") or "").split(" ")[0] != observed.get("uname_r"):
        bad.append("pps_gpio vermagic %r does not name the running kernel %r" % (observed.get("vermagic"), observed.get("uname_r")))
    return bad


def check(scenario, result, expect, build_rows=None, accounts=None, closure=None, venvs=None, pps=None, session=None):
    """Compare one boot with its expectation; every mismatch is listed (host-testable).
    accounts: image-manifest.json accounts.service_accounts (None: not compared);
    closure: image-manifest.json package_closure (None: not compared);
    venvs: image-manifest.json venvs.venvs, compared on the selftest boot (None: not compared);
    pps: image-manifest.json pps_gpio, compared on every boot (None: not compared; W2 IMG-4);
    session: image-manifest.json session: display-manager.service must then be its display manager (W2 IMG-4), else masked."""
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
    if venvs is not None and report and expect["selftest"]:
        bad += venv_mismatches(report.get("venvs"), venvs, report.get("selftest"))
    if pps is not None and report:
        bad += pps_mismatches(report.get("pps_gpio"), pps)
    # graphical.target wants display-manager.service: r2's gdm3 alias must resolve to the recipe's gdm mask, or, once the
    # image has the session (W2 IMG-4), to its display manager (greetd.service; gdm stays masked: masked_units above).
    display_manager = report.get("display_manager")
    if session is not None and report:
        want = Path((session.get("display_manager") or {}).get("after") or "").name or None
        got = display_manager or {}
        if want is None or got.get("Id") != want or got.get("LoadState") != "loaded" or got.get("ActiveState") == "failed":
            bad.append("display-manager.service %s on the booted slot, expected %s (image manifest session)" % (json.dumps(got)[:200], want))
    elif display_manager is not None and display_manager.get("LoadState") not in ("masked", "not-found"):
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
    venvs = (manifest.get("venvs") or {}).get("venvs") or {}  # likewise, on the selftest boot
    pps = manifest.get("pps_gpio") or {}  # W2 IMG-4: every boot loads pps_gpio
    session = manifest.get("session")  # W2 IMG-4: display-manager.service resolves to greetd.service (None: gdm mask only)
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
        result["scenarios"].append(check(name, run_result, expect, build_rows, accounts, closure, venvs, pps, session))
        (out / "smoke-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    result["status"] = "MODEL_PASS" if all(s["status"] == "MODEL_PASS" for s in result["scenarios"]) else "MODEL_FAIL"
    (out / "smoke-report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    copy.unlink()
    return result


# ---------------------------------------------------------------- touch session scenario (W2 IMG-4)
# A separate QEMU boot of its own sparse copy (smoke_qemu.py --session, its own CI step after the A/B smoke: about 15 min
# under TCG). The golden labA.conf is rewritten in place (as scenario 3 rewrites the blessed one) with the session report
# command, which starts graphical.target. The display is QEMU's ramfb: AAVMF's QemuRamfbDxe gives a UEFI GOP with a linear
# framebuffer in reserved memory (edk2-stable202402 OvmfPkg/QemuRamfbDxe/QemuRamfb.c:300; noble's qemu-efi-aarch64 is
# 2024.02-2ubuntu0.10), which 6.18.2-4-qcom drives with simpledrm (CONFIG_DRM_SIMPLEDRM=y, CONFIG_SYSFB_SIMPLEFB=y in
# boot/config-6.18.2-4-qcom, read 2026-11-12). virtio-gpu-pci, the plan's choice, gives nothing here: the kernel has no
# DRM_VIRTIO_GPU and VirtioGpuDxe's GOP is PixelBltOnly (Gop.c:262, :332), so the EFI stub finds no framebuffer and wlroots
# found 0 GPUs (image run 43149697672). A USB keyboard and tablet stand in for the field touch panel: wlroots 0.17.1's
# libinput backend does not start without an input device unless WLR_LIBINPUT_NO_DEVICES is set
# (backend/libinput/backend.c:109-115 of the noble source). WLR_RENDERER=pixman and the runtime console link are
# bootchain.session_model_setup. A MODEL, not Q6A hardware.
SESSION_DEVICES = ("-device", "ramfb", "-device", "qemu-xhci", "-device", "usb-kbd", "-device", "usb-tablet")
SESSION_NEEDED_CONFIG = ("CONFIG_DRM_SIMPLEDRM", "CONFIG_SYSFB_SIMPLEFB", "CONFIG_VT", "CONFIG_USB_XHCI_PCI", "CONFIG_USB_HID")
SESSION_ENTRY = ("labA.conf", "A", 2)  # golden labA: blessed, version 2 (bootchain.entries), so it stays the newest
SESSION_SCENARIO = ("session-greetd-labwc", {"slot": "A", "boot_check": "BOOT_SELF_CHECK_OK", "boot_complete": None, "bless": "inactive",
                                             "bless_status": "clean", "entries_after": sorted(["labA.conf", "labB.conf"] + RESCUE_ENTRIES),
                                             "selftest": False})


def session_mismatches(observed, recorded):
    """bootchain.session_report of the session boot against image-manifest.json session (W2 IMG-4): greetd running as the
    display manager without a restart; the session user's labwc running and the console unit active (labd is absent in the
    model: the console keeps running and shows labd unavailable, the defined labd-absent state), both with unchanged PIDs
    after bootchain.SESSION_SETTLE; lab-session in normal mode with no failure; no failed user unit; an active greeter-class
    logind session of the user on seat0, VT 1; the built config.toml and no greetd.conf; the model's environment bound."""
    if not recorded:
        return ["image-manifest.json records no session (build_image.install_session)"]
    if not observed or "unavailable" in observed:
        return ["no session report from the booted slot: %s" % json.dumps(observed)[:600]]
    bad = []
    model = observed.get("model") or {}
    if not (model.get("environment") or {}).get("bound"):
        bad.append("the model's %s was not bound over /etc/environment: %r" % (bootchain.SESSION_ENV, model.get("environment")))
    units = observed.get("units") or {}

    def state(unit, key):
        return (units.get(unit) or {}).get(key)
    if (state("greetd.service", "ActiveState"), state("greetd.service", "SubState"), state("greetd.service", "NRestarts")) != ("active", "running", "0"):
        bad.append("greetd.service %s, expected active, running, no restart" % json.dumps(units.get("greetd.service"))[:300])
    want = Path((recorded.get("display_manager") or {}).get("after") or "").name
    if state("display-manager.service", "Id") != want:
        bad.append("display-manager.service is %r, expected %s" % (state("display-manager.service", "Id"), want))
    if state(bootchain.SESSION_TARGET, "ActiveState") != "active":
        bad.append("%s %r, expected active" % (bootchain.SESSION_TARGET, state(bootchain.SESSION_TARGET, "ActiveState")))
    user = (observed.get("user") or {}).get("name")
    if not observed.get("up"):
        bad.append("labwc of %s and %s were not both up within %d s" % (user, bootchain.CONSOLE_UNIT, bootchain.SESSION_LIMIT))
    elif observed.get("stable") is not True:
        bad.append("labwc or %s changed its PID within %d s (a session restart)" % (bootchain.CONSOLE_UNIT, bootchain.SESSION_SETTLE))
    console = observed.get("console") or {}
    if console.get("ActiveState") != "active":
        bad.append("%s %s, expected active (labd absent: the console runs and shows labd unavailable)"
                   % (bootchain.CONSOLE_UNIT, json.dumps(console)[:300]))
    lab = observed.get("lab_session_state") or {}
    if lab.get("mode") not in (None, "normal") or lab.get("failures"):
        bad.append("lab-session left normal mode or counted failures: %s" % json.dumps(lab)[:300])
    if observed.get("user_failed_units"):
        bad.append("failed user units: " + "; ".join(observed["user_failed_units"])[:300])
    greeters = [s for s in (observed.get("logind_sessions") or {}).values() if s.get("Name") == user and s.get("Class") == "greeter"]
    if len(greeters) != 1 or (greeters[0].get("Active"), greeters[0].get("Seat"), greeters[0].get("VTNr")) != ("yes", "seat0", "1"):
        bad.append("logind greeter session of %s: %s, expected one, active on seat0 VT 1" % (user, json.dumps(greeters)[:400]))
    if observed.get("greetd_config_sha256") != (recorded.get("files") or {}).get("/etc/greetd/config.toml"):
        bad.append("/etc/greetd/config.toml on the booted slot %r is not the built one" % observed.get("greetd_config_sha256"))
    if observed.get("greetd_conf_present") is not False:
        bad.append("/etc/greetd/greetd.conf exists on the booted slot (greetd 0.9.0 would read it before config.toml)")
    if bad:  # what the session printed, so a failure is diagnosable from the report alone
        for key in ("journal", "greetd_journal", "console_journal", "kernel_display_journal"):
            if observed.get(key):
                bad.append("%s: %s" % (key, observed[key][-1500:]))
    return bad


def session_smoke(image, manifest_path, facts_path, work, out, timeout=1800):
    """The session scenario: one QEMU boot of a fresh sparse copy; SMOKE_NOT_FEASIBLE as smoke() when the kernel config,
    QEMU or AAVMF cannot run it. Writes session-report.json."""
    if sys.platform != "linux" or platform.machine() != "aarch64" or os.geteuid() != 0:
        raise SmokeError("the smoke runs as root on an aarch64 Linux builder")
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("status") != "CANDIDATE_IMAGE_BUILT" or manifest.get("route") != "A":
        raise SmokeError("needs a built Route A candidate (image-manifest.json)")
    kconfig = json.loads(Path(facts_path).read_text(encoding="utf-8")).get("kernel_deb_config") or {}
    work, out = Path(work), Path(out)
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "session-report.json"
    needed = NEEDED_CONFIG + SESSION_NEEDED_CONFIG
    result = {"schema_version": 1, "kind": "QEMU virt + AAVMF model of the greetd/labwc touch session (not Q6A hardware)",
              "kernel_config": {k: kconfig.get(k) for k in needed}, "hardware_ready": False, "devices": list(SESSION_DEVICES),
              "bench_gates_open": ["W1-2 display and touch", "STACK.md:1486 greetd recovery"], "scenarios": []}
    missing = [k for k in needed if kconfig.get(k) != "y"]
    if missing or not shutil.which("qemu-system-aarch64") or not FIRMWARE_CODE.is_file():
        result.update(status="SMOKE_NOT_FEASIBLE", why="kernel config lacks " + ",".join(missing) if missing else "QEMU or AAVMF missing")
        report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result
    accel = "kvm" if os.path.exists("/dev/kvm") else "tcg"
    result.update(accel=accel, qemu=run(["qemu-system-aarch64", "--version"]).stdout.splitlines()[0])
    config = bootchain.validate_ab(manifest["boot_config"])
    copy = work / "session.raw"
    for stale in (copy, work / "smoke.raw"):  # smoke.raw: an A/B copy that a stopped smoke() left behind (disk space)
        if stale.exists():
            stale.unlink()
    recovery_kit.sparse_copy(image, copy)
    esp_dir = work / "esp-session"
    fname, slot, version = SESSION_ENTRY
    name, expect = SESSION_SCENARIO
    with Esp(copy, esp_dir) as esp:
        apply_entry_plan(esp / "loader/entries", ("", {}, {fname: (config, slot, version, None, False, True)}))
        before = lab_entries(esp)
        rewritten = "--session" in (esp / "loader/entries" / fname).read_text(encoding="ascii")
    vars_file = work / "vars-session.fd"
    shutil.copyfile(FIRMWARE_VARS, vars_file)
    run_result = qemu(copy, vars_file, out / ("console-session-%s.log" % name), timeout + bootchain.SESSION_LIMIT + bootchain.SESSION_SETTLE,
                      accel, SESSION_DEVICES)
    with Esp(copy, esp_dir, read_only=True) as esp:
        run_result["entries_before"], run_result["entries_after"] = before, lab_entries(esp)
    recorded = manifest.get("session")
    scenario = check(name, run_result, expect, None, (manifest.get("accounts") or {}).get("service_accounts") or {},
                     manifest.get("package_closure") or {}, None, manifest.get("pps_gpio") or {}, recorded)
    extra = ([] if rewritten else ["the golden " + fname + " was not on the ESP to rewrite"])
    extra += session_mismatches((run_result["report"] or {}).get("session"), recorded)
    scenario["mismatches"] += extra
    scenario["status"] = "MODEL_FAIL" if scenario["mismatches"] else "MODEL_PASS"
    result["scenarios"].append(scenario)
    result["status"] = scenario["status"]
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    copy.unlink()
    return result


# ---------------------------------------------------------------- scenario 4: the updater's trial (W2 IMG-UPD)
# A fresh sparse copy of the Route A image (never the copy of scenarios 1-3): build_image.update_model runs
# update_slot.py apply A->B on the builder with the job's CI test key (srrx-mirror; the record says
# NOT_RELEASE), which leaves labB+3.conf as a counted trial of a newer generation. The smoke rewrites that
# entry in place (name and version kept) and adds one smoke-only oneshot unit to root B that runs
# `update_slot.py plan --markers` on the booted slot: the guest only plans, it never applies. One boot:
# labB+3 boots, srrx-boot-check passes, systemd-bless-boot -> labB.conf; the plan sees slot B running and
# slot A as the target, not mounted, and the builder's record on /data.

UPDATE_SCENARIO = ("update-b-trial-blessed", {"slot": "B", "boot_check": "BOOT_SELF_CHECK_OK", "boot_complete": "active", "bless": "active",
                                              "bless_status": "good", "entries_after": sorted(["labA.conf", "labB.conf"] + RESCUE_ENTRIES),
                                              "selftest": False})
PLAN_UNIT = "srrx-update-plan-smoke.service"
GUEST_PLAN = re.compile(re.escape(update_slot.PLAN_BEGIN) + r"(.*?)" + re.escape(update_slot.PLAN_END), re.S)
GUEST_PLAN_CHECKS = ("target_not_running", "target_not_mounted", "srrx_inactive", "labd_disarmed", "records_on_data")


def plan_unit_text():
    return ("[Unit]\nDescription=SR-RX QEMU smoke only: update_slot.py plan on the booted slot (W2 IMG-UPD scenario 4)\n"
            "After=local-fs.target\n\n[Service]\nType=oneshot\n"
            "ExecStart=/usr/bin/python3 -I -B /opt/srrx/deployment/image/update_slot.py plan --markers\n"
            "StandardOutput=journal+console\nTimeoutStartSec=600\n\n[Install]\nWantedBy=multi-user.target\n")


def install_plan_unit(root):
    units = Path(root) / "etc/systemd/system"
    (units / PLAN_UNIT).write_text(plan_unit_text(), encoding="ascii", newline="\n")
    link = units / "multi-user.target.wants" / PLAN_UNIT
    link.parent.mkdir(exist_ok=True)
    if link.is_symlink() or link.exists():
        link.unlink()
    os.symlink("/etc/systemd/system/" + PLAN_UNIT, link)
    return PLAN_UNIT


def trial_entry_rewrite(config, entries_dir):
    """The updater's trial entry labB+N.conf becomes the smoke entry in place: the same name and version."""
    names = sorted(p.name for p in Path(entries_dir).glob("labB+*.conf"))
    if len(names) != 1:
        return None
    path = Path(entries_dir) / names[0]
    versions = [line[8:].strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.startswith("version ")]
    if len(versions) != 1 or not versions[0].isdigit():
        return None
    path.write_text(smoke_entry(config, "B", int(versions[0]), None, False), encoding="ascii", newline="\n")
    return {"entry": names[0], "version": int(versions[0])}


def guest_plan(console_text):
    found = GUEST_PLAN.findall(console_text or "")
    if not found:
        return None
    try:
        return json.loads(found[-1].replace("\r", "").replace("\n", ""))
    except ValueError:
        return {"unparsed": found[-1][:2000]}


def update_mismatches(record, closure, guest):
    """The builder's update record and the guest's plan of scenario 4 (host-testable)."""
    if not record:
        return ["no update record from update_slot.apply"]
    bad = []
    if record.get("status") != update_slot.STATUS_UPDATED:
        bad.append("update record status %r: %s" % (record.get("status"), str(record.get("error") or record.get("refusals"))[-800:]))
    if record.get("release") != "NOT_RELEASE":
        bad.append("update record release %r, expected NOT_RELEASE (CI test key)" % record.get("release"))
    if (record.get("active_slot"), record.get("target_slot")) != ("A", "B"):
        bad.append("update record slots %r -> %r, expected A -> B" % (record.get("active_slot"), record.get("target_slot")))
    used = sorted(k for k, v in (record.get("publications") or {}).items() if v)
    if not used or not set(used) <= set(update_slot.PUBLICATIONS):
        bad.append("update record publications %r: only srrx-lab and srrx-mirror" % used)
    mirror = (record.get("publication_packages") or {}).get("srrx-mirror")
    want = sorted("%s=%s" % item for item in ((closure or {}).get("installed") or {}).items())
    if mirror is not None and mirror != want:
        bad.append("srrx-mirror packages %r are not the image package closure %r" % (mirror, want))
    if record.get("packages_outside_publications"):
        bad.append("packages changed outside the publications: %r" % record["packages_outside_publications"])
    trial = record.get("trial") or {}
    if trial.get("slot") != "B" or not str(trial.get("entry", "")).startswith("labB+"):
        bad.append("update record trial %r, expected a counted labB+N.conf" % trial)
    if guest is None:
        return bad + ["no update_slot.py plan output on the console of the booted slot"]
    for key, wanted in (("status", "PLAN_ONLY"), ("mode", "running-system"), ("active_slot", "B"), ("running_slot", "B"), ("target_slot", "A")):
        if guest.get(key) != wanted:
            bad.append("guest plan %s %r, expected %r" % (key, guest.get(key), wanted))
    checks = guest.get("checks") or {}
    bad += ["guest plan check %s is %r" % (k, checks.get(k)) for k in GUEST_PLAN_CHECKS if checks.get(k) is not True]
    last = guest.get("last_record") or {}
    if last.get("name") != Path(str(record.get("record_path") or "")).name or last.get("status") != update_slot.STATUS_UPDATED:
        bad.append("guest plan sees the update record %r, the builder wrote %r" % (last, Path(str(record.get("record_path") or "")).name))
    return bad


class _Partition:
    """One partition of the update copy mounted read-write (root B, to add the smoke's plan unit)."""

    def __init__(self, image, number, mountpoint, fstype):
        self.image, self.number, self.mountpoint, self.fstype = image, number, Path(mountpoint), fstype

    def __enter__(self):
        import build_image
        self.loop, self.mounts = build_image.Loop(self.image), build_image.Mounts()
        try:
            self.mounts.mount(self.loop.part(self.number), self.mountpoint, self.fstype)
        except BaseException:
            self.loop.detach()
            raise
        return self.mountpoint

    def __exit__(self, *exc):
        self.mounts.umount_all()
        self.loop.detach()


def smoke_update(image, manifest_path, facts_path, work, out, mirror_repo=None, lab_repo=None, build_records=(), ci_test_key=None,
                 timeout=1800):
    """Scenario 4 (W2 IMG-UPD): the update model on a fresh copy, then one QEMU boot of the trial slot B."""
    if sys.platform != "linux" or platform.machine() != "aarch64" or os.geteuid() != 0:
        raise SmokeError("the smoke runs as root on an aarch64 Linux builder")
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("status") != "CANDIDATE_IMAGE_BUILT" or manifest.get("route") != "A":
        raise SmokeError("needs a built Route A candidate (image-manifest.json)")
    kconfig = json.loads(Path(facts_path).read_text(encoding="utf-8")).get("kernel_deb_config") or {}
    work, out = Path(work), Path(out)
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "update-smoke-report.json"
    result = {"schema_version": 1, "kind": "QEMU virt + AAVMF model of the inactive-slot update (W2 IMG-UPD scenario 4; not Q6A hardware)",
              "hardware_ready": False, "bench_gates_open": ["W-03"], "scenarios": []}
    missing = [k for k in NEEDED_CONFIG if kconfig.get(k) != "y"]
    if missing or not shutil.which("qemu-system-aarch64") or not FIRMWARE_CODE.is_file():
        result.update(status="SMOKE_NOT_FEASIBLE", why="kernel config lacks " + ",".join(missing) if missing else "QEMU or AAVMF missing")
        report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result
    import build_image
    accel = "kvm" if os.path.exists("/dev/kvm") else "tcg"
    result.update(accel=accel, qemu=run(["qemu-system-aarch64", "--version"]).stdout.splitlines()[0])
    config = bootchain.validate_ab(manifest["boot_config"])
    copy = work / "update.raw"
    if copy.exists():
        copy.unlink()
    recovery_kit.sparse_copy(image, copy)
    name, expect = UPDATE_SCENARIO
    closure = manifest.get("package_closure") or {}
    record = build_image.update_model(copy, work / "update", mirror_repo, lab_repo, build_records, ci_test_key)
    result["update_record"] = record
    run_result = {"qemu_exit": None, "report": None, "entries_after": None}
    if record.get("status") == update_slot.STATUS_UPDATED:
        esp_dir = work / "esp"
        with Esp(copy, esp_dir) as esp:
            rewrite = trial_entry_rewrite(config, esp / "loader/entries")
            before = lab_entries(esp)
        with _Partition(copy, 3, work / "root_b", "ext4") as root_b:
            install_plan_unit(root_b)
        vars_file = work / "vars-4.fd"
        shutil.copyfile(FIRMWARE_VARS, vars_file)
        log = out / ("console-4-%s.log" % name)
        run_result = qemu(copy, vars_file, log, timeout, accel)
        with Esp(copy, esp_dir, read_only=True) as esp:
            run_result.update(entries_before=before, entries_after=lab_entries(esp), trial_entry=rewrite)
        guest = guest_plan(Path(log).read_text(encoding="utf-8", errors="replace") if Path(log).is_file() else "")
    else:
        guest = None
    checked = check(name, run_result, expect, None, (manifest.get("accounts") or {}).get("service_accounts") or {}, closure, None)
    mismatches = (checked["mismatches"] if run_result["report"] is not None or record.get("status") == update_slot.STATUS_UPDATED else []) \
        + update_mismatches(record, closure, guest)
    checked.update(status="MODEL_FAIL" if mismatches else "MODEL_PASS", mismatches=mismatches, guest_plan=guest)
    result["scenarios"].append(checked)
    result["status"] = checked["status"]
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
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
    parser.add_argument("--session", action="store_true",
                        help="W2 IMG-4: only the separate greetd/labwc session scenario (session-report.json) instead of the A/B boots")
    # W2 IMG-UPD: scenario 4 (the updater's trial of slot B) instead of scenarios 1-3; update-smoke-report.json.
    parser.add_argument("--update-model", action="store_true", help="scenario 4: update_slot.py A->B on a fresh copy, boot the trial")
    parser.add_argument("--mirror-repo", type=Path, help="--update-model: the srrx-mirror publication signed by the CI test key")
    parser.add_argument("--lab-repo", type=Path, help="--update-model: an srrx-lab publication (with --build-record)")
    parser.add_argument("--build-record", type=Path, action="append", default=[])
    parser.add_argument("--ci-test-key", nargs=2, metavar=("KEYRING", "FINGERPRINT"), help="--update-model: the job-only test key")
    args = parser.parse_args()
    if args.session and args.update_model:
        parser.error("--session and --update-model are separate scenarios (one CI step each)")
    try:
        facts = args.facts or args.manifest.with_name("image-facts.json")
        if args.update_model:
            result = smoke_update(args.image, args.manifest, facts, args.work, args.out, args.mirror_repo, args.lab_repo, args.build_record,
                                  args.ci_test_key, args.timeout)
        else:
            result = (session_smoke if args.session else smoke)(args.image, args.manifest, facts, args.work, args.out, args.timeout)
    except (OSError, ValueError, SmokeError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "scenarios": [(s["scenario"], s["status"], s.get("mismatches"), s["observed"])
                                                                for s in result["scenarios"]]}, indent=2))
    accepted = ("MODEL_PASS",) if args.require_model else ("MODEL_PASS", "SMOKE_NOT_FEASIBLE")
    return 0 if result["status"] in accepted else 1


if __name__ == "__main__":
    sys.exit(main())
