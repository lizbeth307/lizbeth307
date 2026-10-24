#!/usr/bin/env python3
"""SR-RX-v2.1 A/B boot chain: kernel command line, BLS Type #1 entries, loader.conf.

Route A (primary, STACK.md:843): real systemd-boot 255 after `dpkg --purge
sdboot-is-embloader`; entries labA/labB with an explicit devicetree line,
boot counting `+N` from /etc/kernel/tries, systemd-bless-boot after
boot-complete.target. `default lab*` plus systemd-boot's ordering (entries
without tries left sort last, then sort-key, then version downwards) makes the
newest slot that is not bad the default.
Route B (fallback variant, STACK.md:844): embloader 0.4, which has no boot
counter and matches `default` against the entry name without `.conf`
(embloader/src/sdboot/file.c, src/loader/loader.c at tag 0.4); a trial slot is
written back to the previous default by its own initramfs and committed only
after boot-complete.target.

Pure generators are host-testable. The entry points run on an image or target
root and only write the ESP mounted at /boot/efi:
  kernel-install add|remove ...  (etc/kernel/install.d/90-srrx-bls.install)
  golden-entries                 (image builder: blessed entries for both slots)
  boot-check                     (srrx-boot-check.service, gates boot-complete.target)
  route-b-commit                 (srrx-ab-commit.service, Route B only)
Nothing here partitions, flashes, writes EFI variables or runs bootctl.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys

HERE = Path(__file__).resolve().parent
DEPLOYMENT = HERE.parent
PARTUUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")
# One kernel command-line token: no quoting, whitespace, shell or glob syntax. '@' is required by
# video=HDMI-A-1:1920x1080@60 (STACK.md:850, build/07-pz-vstanovlennia.md:186).
TOKEN = re.compile(r"[A-Za-z0-9_.,:/=+@-]+\Z")
ESP_PATH = re.compile(r"/[A-Za-z0-9_./+-]+\Z")
KERNEL_VERSION = re.compile(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?-[0-9]+-[a-z0-9]+\Z")
CMDLINE_MAX = 2048  # arm64 COMMAND_LINE_SIZE
# Appended to the full observed base line, in this order (STACK.md:850, :853; build/07-pz-vstanovlennia.md:186, :188).
LAB_ADDITIONS = ("preempt=full", "drm.edid_firmware=HDMI-A-1:edid/field.bin", "video=HDMI-A-1:1920x1080@60",
                 "panic=10", "usbcore.usbfs_memory_mb=0")
LIME_ADDITIONS = ("pcie_aspm=off", "isolcpus=nohz,domain,managed_irq,7", "nohz_full=7", "rcu_nocbs=7", "irqaffinity=0-6")
FORBIDDEN_TOKENS = ("clk_ignore_unused",)  # STACK.md:857
SLOTS = ("A", "B")
SLOT_FILES = ("kernel", "initrd", "lab_dtb", "field_dtb")
AB_KEYS = ("schema_version", "route", "active_slot", "trial_slot", "dt_profile", "lime_build", "kernel_version",
           "esp_partuuid", "root_a_partuuid", "root_b_partuuid", "base_cmdline_without_root", "slots", "rescue")
SORT_KEY, RESCUE_SORT_KEY = "srrx", "srrx-rescue"
ESP_MOUNT = Path("/boot/efi")
BOOT_CONFIG = Path("/etc/srrx/boot.json")
SLOT_FILE = Path("/etc/srrx/slot")
DTB_STORE = Path("/usr/lib/srrx/dtb")
TRIAL_MARK = "srrx/ab/trial"      # Route B: slot letter under trial (ESP-relative)
BOOTING_MARK = "srrx/ab/booting"  # Route B: the trial slot's initramfs already wrote the default back
ENTRY_NAME = re.compile(r"lab([AB])(?:\+([0-9]+)(?:-([0-9]+))?)?\.conf\Z")


class BootChainError(ValueError):
    pass


def _exact(data, expected, label):
    if type(data) is not dict or set(data) != set(expected):
        raise BootChainError(label + " has missing or unknown fields")


def validate_tokens(text, label="kernel command line"):
    """Single-space separated tokens of the per-token allowlist; returns the token list."""
    if type(text) is not str or not text or len(text.encode()) > CMDLINE_MAX:
        raise BootChainError(label + " is empty, not text or longer than 2048 bytes")
    tokens = text.split(" ")
    if any(not TOKEN.match(t) for t in tokens):
        bad = next(t for t in tokens if not TOKEN.match(t))
        raise BootChainError(label + ": token outside the allowlist [A-Za-z0-9_.,:/=+@-]: " + repr(bad[:40]))
    if any(t in FORBIDDEN_TOKENS for t in tokens):
        raise BootChainError(label + " contains clk_ignore_unused (STACK.md:857)")
    return tokens


def _key(token):
    return token.split("=", 1)[0]


def additions(lime_build):
    return LAB_ADDITIONS + (LIME_ADDITIONS if lime_build else ())


def validate_base(text):
    """The full observed r2 base line without root= (build/07-pz-vstanovlennia.md:183): never only the additions."""
    tokens = validate_tokens(text, "observed base cmdline")
    if any(t.startswith("root=") for t in tokens) or len(tokens) < 3:
        raise BootChainError("base cmdline must preserve the observed options, without root=")
    for token in LAB_ADDITIONS + LIME_ADDITIONS:
        if token in tokens:
            raise BootChainError("base cmdline already contains the lab addition " + token + ": record the observed base, not a generated line")
        clash = [t for t in tokens if _key(t) == _key(token) and _key(token) not in ("console",)]
        if clash:
            raise BootChainError("base cmdline sets " + _key(token) + " differently from the lab addition " + token)
    return tokens


def cmdline(base_without_root, root_partuuid, lime_build=True):
    """Full slot command line: observed base, root=PARTUUID of the slot, lab additions (Lime line by default)."""
    tokens = validate_base(base_without_root)
    if type(root_partuuid) is not str or not PARTUUID.match(root_partuuid):
        raise BootChainError("root PARTUUID must be a lower-case GPT partition GUID")
    line = " ".join(tokens + ["root=PARTUUID=" + root_partuuid] + list(additions(lime_build)))
    validate_tokens(line)
    return line


def strip_root(observed):
    """Base line from an observed /etc/kernel/cmdline: drop root=... (re-added per slot), keep everything else."""
    tokens = validate_tokens(observed.strip(), "observed /etc/kernel/cmdline")
    roots = [t for t in tokens if t.startswith("root=")]
    if len(roots) > 1:
        raise BootChainError("observed cmdline has more than one root=")
    return " ".join(t for t in tokens if not t.startswith("root="))


def _esp_path(value, label):
    if type(value) is not str or not ESP_PATH.match(value) or ".." in value.split("/") or "//" in value:
        raise BootChainError("invalid ESP path for " + label)
    return value


def validate_ab(config):
    """ab-config schema 2 (deployment/ab.template.json): per-slot ESP files, profile, route, rescue."""
    if type(config) is dict and config.get("schema_version") == 1:
        raise BootChainError("A/B schema_version 1 shared one kernel/initrd/DTB between both slots; use schema_version 2 (deployment/ab.template.json)")
    _exact(config, AB_KEYS, "A/B configuration")
    if config["schema_version"] != 2 or config["route"] not in ("A", "B") or config["active_slot"] not in SLOTS:
        raise BootChainError("invalid A/B schema, route or observed active slot")
    if config["trial_slot"] not in (None, *SLOTS) or config["trial_slot"] == config["active_slot"]:
        raise BootChainError("trial_slot is null or the slot that is not active")
    if config["dt_profile"] not in ("lab", "field") or type(config["lime_build"]) is not bool:
        raise BootChainError("dt_profile is lab or field; lime_build is true or false")
    if type(config["kernel_version"]) is not str or not KERNEL_VERSION.match(config["kernel_version"]):
        raise BootChainError("invalid pinned slot kernel version")
    ids = []
    for key in ("esp_partuuid", "root_a_partuuid", "root_b_partuuid"):
        if type(config[key]) is not str or not PARTUUID.match(config[key]):
            raise BootChainError(key + " must be an observed lower-case PARTUUID")
        ids.append(config[key])
    if len(set(ids)) != 3:
        raise BootChainError("ESP and A/B PARTUUIDs must be distinct")
    validate_base(config["base_cmdline_without_root"])
    _exact(config["slots"], SLOTS, "A/B slots")
    seen = set()
    for slot in SLOTS:
        files = config["slots"][slot]
        _exact(files, SLOT_FILES, "slot " + slot)
        for name in SLOT_FILES:
            path = _esp_path(files[name], slot + "." + name)
            if not path.startswith("/srrx/" + slot + "/"):
                raise BootChainError("slot " + slot + " files live under /srrx/" + slot + "/ only (no file shared between slots)")
            if path.lower() in seen:
                raise BootChainError("duplicate ESP file " + path)
            seen.add(path.lower())
    rescue = config["rescue"]
    _exact(rescue, ("kernel", "initrd", "dtb"), "rescue entry")
    for name in ("kernel", "initrd", "dtb"):
        if rescue[name] is None and name == "dtb":
            continue  # r2 ships its entries without devicetree: the firmware DTB is used
        path = _esp_path(rescue[name], "rescue." + name)
        if path.startswith(("/srrx/A/", "/srrx/B/")) or path.lower() in seen:
            raise BootChainError("rescue files must not be slot files")
    return config


def root_partuuid(config, slot):
    return config["root_" + slot.lower() + "_partuuid"]


def other(slot):
    return "B" if slot == "A" else "A"


def entry_text(config, slot, generation):
    files = config["slots"][slot]
    dtb = files["lab_dtb" if config["dt_profile"] == "lab" else "field_dtb"]
    return ("title SR-RX slot {s} ({p}, {k})\nsort-key {sk}\nversion {g}\nlinux {l}\ninitrd {i}\ndevicetree {d}\noptions {o}\n"
            .format(s=slot, p=config["dt_profile"], k=config["kernel_version"], sk=SORT_KEY, g=generation, l=files["kernel"],
                    i=files["initrd"], d=dtb, o=cmdline(config["base_cmdline_without_root"], root_partuuid(config, slot), config["lime_build"])))


def rescue_text(config, slot):
    rescue = config["rescue"]
    lines = ["title SR-RX rescue (existing r2 kernel, slot {} root)".format(slot), "sort-key " + RESCUE_SORT_KEY, "version 0",
             "linux " + rescue["kernel"], "initrd " + rescue["initrd"]]
    if rescue["dtb"] is not None:
        lines.append("devicetree " + rescue["dtb"])
    tokens = validate_base(config["base_cmdline_without_root"])
    lines.append("options " + " ".join(tokens + ["root=PARTUUID=" + root_partuuid(config, slot)]))
    return "\n".join(lines) + "\n"


def loader_conf(config, default_slot=None):
    if config["route"] == "A":
        # Glob plus sort order: the newest lab entry with tries left (or blessed) boots; bad entries sort last.
        default = "lab*"
    else:
        default = "lab" + (default_slot or config["active_slot"])  # embloader: exact entry name, no .conf
    return "default {}\ntimeout 3\neditor no\n".format(default)


def entries(config, tries=3):
    """{ESP-relative path: text} for a candidate set: active slot blessed; trial slot (if any) newest.

    Route A: the trial entry carries `+tries` and a higher version, so it is tried first and
    falls back to the active slot when its tries run out. Route B: no counters (embloader
    ignores them); loader.conf names the trial slot and the trial marker arms the write-back."""
    validate_ab(config)
    active, trial = config["active_slot"], config["trial_slot"]
    if type(tries) is not int or not 1 <= tries <= 10:
        raise BootChainError("tries must be 1..10")
    out = {}
    generation = {active: 2, other(active): 1}
    if trial:
        generation[trial] = 3
    for slot in SLOTS:
        counter = "+%d" % tries if slot == trial and config["route"] == "A" else ""
        out["loader/entries/lab" + slot + counter + ".conf"] = entry_text(config, slot, generation[slot])
        out["loader/entries/lab" + slot + "-rescue.conf"] = rescue_text(config, slot)
    out["loader/loader.conf"] = loader_conf(config, trial if config["route"] == "B" else None)
    if trial and config["route"] == "B":
        out[TRIAL_MARK] = trial + "\n"
    return out


def write_tree(root, files):
    root = Path(root)
    for relative, text in sorted(files.items()):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(target, text.encode())


def _atomic_write(target, data):
    tmp = target.with_name("." + target.name + ".srrx-tmp")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, target)


def _copy_atomic(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(target, Path(source).read_bytes())
    return hashlib.sha256(target.read_bytes()).hexdigest()


def load_config(path=BOOT_CONFIG):
    return validate_ab(json.loads(Path(path).read_text(encoding="utf-8")))


def read_slot(path=SLOT_FILE):
    slot = Path(path).read_text(encoding="ascii").strip()
    if slot not in SLOTS:
        raise BootChainError(str(path) + " must contain A or B")
    return slot


def read_tries(path=Path("/etc/kernel/tries")):
    try:
        value = Path(path).read_text(encoding="ascii").strip()
    except FileNotFoundError:
        return None
    if not value.isdigit() or not 1 <= int(value) <= 10:
        raise BootChainError("/etc/kernel/tries must be 1..10")
    return int(value)


def _is_mountpoint(path):
    path = Path(path)
    try:
        return path.is_dir() and (path.stat().st_dev != path.parent.stat().st_dev or path.resolve() == Path("/"))
    except OSError:
        return False


def _entry_versions(entries_dir):
    versions = {}
    for item in Path(entries_dir).glob("lab*.conf"):
        match = ENTRY_NAME.match(item.name)
        if not match:
            continue
        for line in item.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("version ") and line[8:].strip().isdigit():
                versions[item.name] = (match.group(1), int(line[8:].strip()))
    return versions


def kernel_install(argv, esp=ESP_MOUNT, config_path=BOOT_CONFIG, slot_path=SLOT_FILE,
                   cmdline_path=Path("/etc/kernel/cmdline"), tries_path=Path("/etc/kernel/tries"), dtb_store=DTB_STORE):
    """kernel-install plugin: `add KVER ENTRY_DIR KERNEL [INITRD...]` or `remove KVER ENTRY_DIR`."""
    if len(argv) < 2 or argv[0] not in ("add", "remove"):
        return 0  # other verbs (inspect, add-all) are not ours
    verb, kver = argv[0], argv[1]
    config = load_config(config_path)
    if kver != config["kernel_version"]:
        print("srrx-bls: " + kver + " is not the pinned slot kernel " + config["kernel_version"] + "; no SR-RX entry written")
        return 0
    if verb == "remove":
        print("srrx-bls: removal of the pinned slot kernel keeps the SR-RX entry and ESP files (apt-mark hold, STACK.md:138)")
        return 0
    if len(argv) < 4:
        raise BootChainError("kernel-install add needs KERNEL_VERSION ENTRY_DIR KERNEL_IMAGE")
    slot = read_slot(slot_path)
    expected = cmdline(config["base_cmdline_without_root"], root_partuuid(config, slot), config["lime_build"])
    observed = Path(cmdline_path).read_text(encoding="ascii").strip()
    if observed != expected:
        raise BootChainError("/etc/kernel/cmdline differs from the slot " + slot + " line generated from /etc/srrx/boot.json")
    if not _is_mountpoint(esp):
        raise BootChainError(str(esp) + " is not a mounted ESP")
    kernel = Path(argv[3])
    initrds = [Path(p) for p in argv[4:]] or [Path("/boot/initrd.img-" + kver)]
    if len(initrds) != 1 or not initrds[0].is_file() or not kernel.is_file():
        raise BootChainError("exactly one existing initrd and the kernel image are required")
    store = Path(dtb_store) / kver
    record = json.loads((store / "dtb.json").read_text(encoding="utf-8"))
    for profile in ("lab", "field"):
        dtb = store / (profile + ".dtb")
        if record.get(profile, {}).get("sha256") != hashlib.sha256(dtb.read_bytes()).hexdigest():
            raise BootChainError(profile + ".dtb differs from its dtb.json record")
        if record[profile].get("merged") is not True and os.environ.get("SRRX_ALLOW_UNMERGED_DTB") != "1":
            raise BootChainError(profile + ".dtb is the package DTB without the SR-RX overlay: refusing (STACK.md:843)")
    files = config["slots"][slot]
    written = {}
    for name, source in (("kernel", kernel), ("initrd", initrds[0]), ("lab_dtb", store / "lab.dtb"), ("field_dtb", store / "field.dtb")):
        written[files[name]] = _copy_atomic(source, Path(esp) / files[name].lstrip("/"))
    entries_dir = Path(esp) / "loader/entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    versions = _entry_versions(entries_dir)
    generation = 1 + max([v for s, v in versions.values() if s != slot] + [0])
    for name, (owner, _) in versions.items():
        if owner == slot:
            (entries_dir / name).unlink()
    tries = read_tries(tries_path) if config["route"] == "A" else None
    name = "lab" + slot + ("+%d" % tries if tries else "") + ".conf"
    _atomic_write(entries_dir / name, entry_text(config, slot, generation).encode())
    print(json.dumps({"status": "SLOT_ENTRY_WRITTEN", "slot": slot, "entry": "loader/entries/" + name,
                      "generation": generation, "files": written, "route": config["route"]}))
    return 0


def golden_entries(esp=ESP_MOUNT, config_path=BOOT_CONFIG):
    """Image builder: blessed entries for both slots (active newest), rescue entries and loader.conf.

    Removes any other BLS entry on the ESP (r2 RadxaOS-*.conf, stock kernel-install output) and
    returns the removed names for the manifest."""
    config = load_config(config_path)
    if config["trial_slot"] is not None:
        raise BootChainError("a golden image has no trial slot")
    entries_dir = Path(esp) / "loader/entries"
    files = entries(config)
    for slot in SLOTS:
        for name in SLOT_FILES:
            if not (Path(esp) / config["slots"][slot][name].lstrip("/")).is_file():
                raise BootChainError("slot " + slot + " ESP file missing: " + config["slots"][slot][name])
    for name in ("kernel", "initrd", "dtb"):
        if config["rescue"][name] is not None and not (Path(esp) / config["rescue"][name].lstrip("/")).is_file():
            raise BootChainError("rescue ESP file missing: " + config["rescue"][name])
    removed = sorted(p.name for p in entries_dir.glob("*.conf") if "loader/entries/" + p.name not in files) if entries_dir.is_dir() else []
    for name in removed:
        (entries_dir / name).unlink()
    write_tree(esp, files)
    return {"status": "GOLDEN_ENTRIES_WRITTEN", "entries": sorted(files), "removed_foreign_entries": removed}


def _mount_source_dev(path):
    return os.stat(path).st_dev


def boot_check(root=Path("/"), proc_cmdline=Path("/proc/cmdline")):
    """Gate for boot-complete.target: no PASS of any bench gate, only the self-check of this boot."""
    sys.path.insert(0, str(DEPLOYMENT))
    import deploy  # noqa: E402  (stdlib-only module of the same tree)
    issues, notes = [], []
    try:
        config = load_config(root / BOOT_CONFIG.relative_to("/"))
        slot = read_slot(root / SLOT_FILE.relative_to("/"))
    except (OSError, ValueError) as exc:
        return {"status": "BLOCKED", "issues": ["boot configuration unreadable: " + str(exc)], "notes": []}
    if platform.release() != config["kernel_version"]:
        issues.append("running kernel " + platform.release() + " is not the pinned slot kernel " + config["kernel_version"])
    expected = cmdline(config["base_cmdline_without_root"], root_partuuid(config, slot), config["lime_build"]).split(" ")
    running = Path(proc_cmdline).read_text(encoding="ascii", errors="replace").split()
    missing = [t for t in expected if t not in running]
    if missing:
        issues.append("running cmdline lacks " + ",".join(missing))
    if any(t in FORBIDDEN_TOKENS for t in running):
        issues.append("running cmdline contains clk_ignore_unused")
    roots = [t for t in running if t.startswith("root=")]
    if roots != ["root=PARTUUID=" + root_partuuid(config, slot)]:
        issues.append("running root= is not exactly the slot " + slot + " PARTUUID")
    extra = sorted(set(running) - set(expected))
    if extra:
        notes.append("loader-added tokens (Route B embloader appends its own bootargs): " + ",".join(extra))
    for mount, partuuid in (("/", root_partuuid(config, slot)), ("/boot/efi", config["esp_partuuid"])):
        try:
            if _mount_source_dev(root / mount.lstrip("/")) != os.stat(root / "dev/disk/by-partuuid" / partuuid).st_rdev:
                issues.append(mount + " is not mounted from PARTUUID " + partuuid)
        except OSError as exc:
            issues.append(mount + " mount source unverifiable: " + type(exc).__name__)
    if not _is_mountpoint(root / "data"):
        issues.append("/data is not mounted")
    issues.extend(deploy.radio_off_issues(None, root))
    inventory = deploy.command(["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${db:Status-Status}\n"], limit=8 * 1024 * 1024)
    if inventory["returncode"]:
        issues.append("installed package inventory unavailable")
    else:
        present = {f[0].split(":", 1)[0]: f[1] for f in (r.split("\t") for r in inventory["stdout"].splitlines())
                   if len(f) == 3 and f[2] not in ("not-installed", "config-files")}
        found = deploy.prohibited_installed(present, identifiers=True)
        if found:
            issues.append("prohibited packages installed: " + ",".join(found))
    executables = deploy.prohibited_executables(root)
    if executables:
        issues.append("prohibited TX/private-content executables present: " + ",".join(executables))
    return {"status": "BOOT_SELF_CHECK_OK" if not issues else "BLOCKED", "slot": slot, "route": config["route"],
            "issues": issues, "notes": notes, "hardware_ready": False}


def route_b_commit(esp=ESP_MOUNT, config_path=BOOT_CONFIG, slot_path=SLOT_FILE):
    """After boot-complete.target on Route B: the trial slot that reached it becomes the default;
    a fallback boot of the other slot records the failed trial. Never touches EFI variables."""
    config = load_config(config_path)
    if config["route"] != "B":
        return {"status": "NOT_ROUTE_B"}
    slot = read_slot(slot_path)
    esp = Path(esp)
    trial_path, booting = esp / TRIAL_MARK, esp / BOOTING_MARK
    if not trial_path.is_file():
        return {"status": "NO_TRIAL", "slot": slot}
    trial = trial_path.read_text(encoding="ascii").strip()
    if trial not in SLOTS:
        raise BootChainError("Route B trial marker must contain A or B")
    if trial == slot:
        _atomic_write(esp / "loader/loader.conf", loader_conf(config, slot).encode())
        result = {"status": "TRIAL_COMMITTED", "slot": slot}
    else:
        _atomic_write(esp / ("srrx/ab/failed-" + trial), b"trial slot did not reach boot-complete.target\n")
        result = {"status": "TRIAL_FAILED_FALLBACK_RUNNING", "slot": slot, "failed": trial}
    for mark in (booting, trial_path):
        if mark.exists():
            mark.unlink()
    return result


SMOKE_BEGIN, SMOKE_END = "SRRX-SMOKE-REPORT-BEGIN", "SRRX-SMOKE-REPORT-END"


def smoke_report(timeout=900):
    """QEMU smoke only (deployment/image/smoke_qemu.py passes systemd.run= on the smoke entry): wait
    until every other boot job has finished, then print one JSON line between markers. Inert otherwise."""
    import subprocess
    import time

    def out(argv):
        try:
            return subprocess.run(argv, capture_output=True, text=True, timeout=60).stdout.strip()
        except (OSError, subprocess.SubprocessError) as exc:
            return "unavailable: " + type(exc).__name__

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        jobs = [line for line in out(["systemctl", "list-jobs", "--no-legend", "--plain"]).splitlines()
                if line.strip() and "kernel-command-line" not in line]
        if not jobs:
            break
        time.sleep(5)
    units = ("srrx-boot-check.service", "boot-complete.target", "systemd-bless-boot.service", "srrx-radio-off.service",
             "srrx.service", "systemd-sysusers.service", "systemd-tmpfiles-setup.service")
    report = {"pending_jobs": jobs, "uname_r": platform.release(),
              "proc_cmdline": Path("/proc/cmdline").read_text(errors="replace").strip(),
              "units": {u: out(["systemctl", "show", "--property=ActiveState,SubState,Result,UnitFileState", u]).replace("\n", ";") for u in units},
              "failed_units": out(["systemctl", "--failed", "--no-legend", "--plain"]).splitlines(),
              "bless_boot_status": out(["/usr/lib/systemd/systemd-bless-boot", "status"]),
              "boot_check": boot_check()}
    print(SMOKE_BEGIN + json.dumps(report, sort_keys=True) + SMOKE_END, flush=True)
    return 0


def initramfs_env(config_path=BOOT_CONFIG):
    """Shell assignments for the Route B initramfs script (values are validated PARTUUIDs)."""
    config = load_config(config_path)
    return ("SRRX_AB_ROUTE={}\nSRRX_ROOT_A={}\nSRRX_ROOT_B={}\nSRRX_ESP={}\n"
            .format(config["route"], config["root_a_partuuid"], config["root_b_partuuid"], config["esp_partuuid"]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="op", required=True)
    plugin = sub.add_parser("kernel-install", help="kernel-install plugin body")
    plugin.add_argument("args", nargs=argparse.REMAINDER)
    env = sub.add_parser("initramfs-env", help="Route B: /conf/conf.d/srrx-ab for the initramfs")
    env.add_argument("--config", type=Path, default=BOOT_CONFIG)
    sub.add_parser("smoke-report", help="QEMU smoke only: report the boot after every other job finished")
    golden = sub.add_parser("golden-entries")
    golden.add_argument("--esp", type=Path, default=ESP_MOUNT)
    golden.add_argument("--config", type=Path, default=BOOT_CONFIG)
    check = sub.add_parser("boot-check")
    check.add_argument("--root", type=Path, default=Path("/"))
    commit = sub.add_parser("route-b-commit")
    commit.add_argument("--esp", type=Path, default=ESP_MOUNT)
    line = sub.add_parser("cmdline", help="print the slot command line of an A/B configuration")
    line.add_argument("--config", type=Path, required=True)
    line.add_argument("--slot", choices=SLOTS, required=True)
    args = parser.parse_args(argv)
    try:
        if args.op == "kernel-install":
            return kernel_install(args.args)
        if args.op == "initramfs-env":
            print(initramfs_env(args.config), end="")
            return 0
        if args.op == "smoke-report":
            return smoke_report()
        if args.op == "cmdline":
            config = load_config(args.config)
            print(cmdline(config["base_cmdline_without_root"], root_partuuid(config, args.slot), config["lime_build"]))
            return 0
        if args.op == "golden-entries":
            result = golden_entries(args.esp, args.config)
        elif args.op == "boot-check":
            result = boot_check(args.root)
        else:
            result = route_b_commit(args.esp)
        print(json.dumps(result, indent=2))
        return 0 if result["status"] != "BLOCKED" else 1
    except (OSError, ValueError, KeyError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
