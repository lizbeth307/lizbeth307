#!/usr/bin/env python3
"""SR-RX-v2.1 inactive-slot updater (W2 IMG-UPD, STACK.md:906): the signed offline publications
(srrx-lab, the +labN builds; srrx-mirror, exactly the image package closure) go into the root slot
that is NOT running. That slot then boots as a counted trial and is blessed only by srrx-boot-check.

  plan             (default) read-only: slots, target partition, preconditions and the publications
                   checked by deploy.verify_repo; lists what apply would refuse. Exit 0 with a plan.
  apply --execute  copy the active root into the target slot and upgrade it in a chroot:
    1. Slots. The active slot is /etc/srrx/slot of --root. On the running system (--root /) the
       kernel's root=PARTUUID must be that slot; for an offline image (--root DIR: the CI model on the
       image builder) no slot of its boot.json may be running on this machine. The target is the
       other slot; its partition (by PARTUUID, checked with blkid -p) must not be the running root,
       mounted, swap or held by another device.
    2. Preconditions: srrx.service (labd) not active and, if a labd answers on its socket, disarmed.
       Power: state of charge >= 50 % from labd when its gauge is accepted (labd has no such field
       yet: OPEN), else --external-power-confirmed NOTE. Both are recorded.
    3. Trust: deploy.verify_repo(release=True) of srrx-lab with the REVIEWED release record
       (/etc/srrx/release.json) and the image keyring, or --ci-test-key KEYRING FINGERPRINT (a
       job-only test key; the record says NOT_RELEASE). srrx-mirror: verify_repo(closure=...). The
       release record pins no srrx-mirror InRelease yet (RM-6 OPEN), so the release path refuses it.
    4. The target's boot entries are removed first (an inactive slot whose root is being rewritten is
       not bootable), then rsync -aHAXxS --numeric-ids --delete of the active root into the mounted
       target, except PER_SLOT_FILES; the per-unit files (CARRIED) arrive with the copy and are checked.
    5. Chroot of the target (minimal /dev, policy-rc.d 101): apt-get update from the verified
       publications only (a generated source list; the target's own lab.pref pins), apt-get -s
       dist-upgrade. Refused: any change of a held, recipe-held or never_in_lab_repo package and any
       package version that no verified publication lists (foreign origin). Then the same
       dist-upgrade; the dpkg status change must equal the simulated plan.
    6. kernel-install add of the pinned kernel in the chroot (90-srrx-bls.install writes the slot
       entry and ESP files). Trial: Route A labT+<tries>.conf of a newer generation; Route B ESP
       srrx/ab/trial = T and loader.conf default labT.
    7. Target unmounted, e2fsck -fn (a failure disarms the trial); the record goes to
       /data/srrx-updates/<UTC>.json whatever the outcome (UPDATED, REFUSED or FAILED).
Nothing here writes EFI variables or partitions, or touches the running slot. The rollback on a Q6A is
bench gate W-03 (OPEN); the CI model is not hardware evidence.
"""
import argparse
import datetime
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

HERE = Path(__file__).resolve().parent
DEPLOYMENT = HERE.parent
sys.path[:0] = [str(HERE), str(DEPLOYMENT)]
import bootchain  # noqa: E402
import build_image  # noqa: E402
import deploy  # noqa: E402

KIND = "srrx_inactive_slot_update"
# Files that differ between the two slot roots (build_image.write_slot_files: boot.json is the same in
# both): rsync never copies or deletes them, so the target keeps its own fstab, cmdline and slot letter.
PER_SLOT_FILES = ("etc/fstab", "etc/kernel/cmdline", "etc/srrx/slot")
# Per-unit files written at commissioning into both slots (software/DEPLOYMENT.md «Введення пристрою в
# експлуатацію», W2 SYS-HOST): they arrive with the copy and are compared after it. The NetworkManager
# files are image files, the same on every unit, and are not listed.
CARRIED = ("etc/hostname", "etc/hosts", "etc/machine-id", "etc/srrx/*.json", "etc/srrx/devices.env",
           deploy.RADIO_OFF_UDEV, "etc/udev/rules.d/70-srrx-serial-bound.rules", "etc/udev/rules.d/71-srrx-gnss.rules",
           "etc/udev/rules.d/73-srrx-i2c.rules", deploy.GNSS_POLKIT_RULE,
           "etc/systemd/system/*.service.d/" + deploy.LAB_DEVICE_DROPIN,
           "etc/systemd/system/dev-lab-*.device.d/" + deploy.DEVICE_TIMEOUT_DROPIN,
           "etc/systemd/system/srrx-locationd.service.d/" + deploy.GNSS_MODE_DROPIN)
RSYNC = ("rsync", "-aHAXxS", "--numeric-ids", "--delete")
CONTROLLER_UNIT = "srrx.service"
ACTIVE_STATES = ("active", "activating", "deactivating", "reloading", "refreshing")
LABD_SOCKET = Path("/run/srrx/control.sock")
SOC_MIN_PERCENT = 50  # STACK.md:906
# The labd status fields the power rule reads once a battery gauge is accepted on the bench. labd emits
# neither yet (srrx.engine status has only the Pico's battery_mv), so the SoC route stays OPEN.
LABD_SOC_FIELDS = ("battery_soc_percent", "battery_gauge_accepted")
RECORDS = "data/srrx-updates"
RELEASE_RECORD = "etc/srrx/release.json"
PUBLICATIONS = ("srrx-lab", "srrx-mirror")
SOURCES = {"srrx-lab": "etc/apt/sources.list.d/srrx-lab.sources", "srrx-mirror": "etc/apt/sources.list.d/srrx-mirror.sources"}
CLOSURE = "opt/srrx/deployment/image/package-closure.json"
TARGET_MOUNT = Path("/run/srrx-update-target")
CHROOT_WORK = "run/srrx-update"  # in the target chroot's /run tmpfs (build_image.chroot_api)
# Never changed by an update, whatever the publication: the boot chain and the pins of the image route
# (recipe.json routes.A apt_pin_minus_one) on top of repo-policy never_in_lab_repo_globs and recipe holds.
BOOT_CHAIN_GLOBS = ("embloader*", "sdboot-is-embloader", "systemd-boot*")
CI_TEST_UID = build_image.CI_TEST_KEY_UID
PLAN_BEGIN, PLAN_END = "SRRX-UPDATE-PLAN-BEGIN", "SRRX-UPDATE-PLAN-END"
STATUS_UPDATED = "INACTIVE_SLOT_UPDATED_TRIAL_ARMED"


class UpdateError(RuntimeError):
    pass


class Refused(UpdateError):
    """A rule refused the update (as opposed to a command that failed)."""


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------- host facts (patched in host tests)

def proc_cmdline():
    return Path("/proc/cmdline").read_text(encoding="ascii", errors="replace")


def unit_active_state(unit):
    """systemctl's ActiveState of a unit ("inactive" for a unit that does not exist); "unknown" if unreadable."""
    try:
        done = subprocess.run(["systemctl", "show", "--property=ActiveState", "--value", unit], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return done.stdout.strip() or "unknown"


def labd_status(path=LABD_SOCKET, timeout=2.0):
    """labd's `status` over its control socket: None when nothing listens there, {"error": ...} when the
    exchange fails, else the status data."""
    import socket
    if not Path(path).exists() or not hasattr(socket, "AF_UNIX"):
        return None
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(timeout)
            client.connect(str(path))
            client.sendall(b'{"op":"status"}\n')
            data = b""
            while b"\n" not in data and len(data) < 1 << 20:
                chunk = client.recv(65536)
                if not chunk:
                    break
                data += chunk
    except ConnectionRefusedError:
        return None  # a stale socket file: no labd runs
    except OSError as exc:
        return {"error": type(exc).__name__}
    try:
        reply = json.loads(data.split(b"\n", 1)[0])
    except ValueError:
        return {"error": "unparsable labd reply"}
    return reply.get("data") if type(reply) is dict and reply.get("ok") is True and type(reply.get("data")) is dict \
        else {"error": "labd refused status: " + str((reply or {}).get("error"))[:200] if type(reply) is dict else "no object"}


def partuuid_of(device):
    """PART_ENTRY_UUID of a partition from its parent's partition table (blkid -p), lower case; None if unknown."""
    try:
        done = subprocess.run(["blkid", "-p", "-o", "value", "-s", "PART_ENTRY_UUID", str(device)], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip().lower() or None


def mounted_devices(mountinfo=Path("/proc/self/mountinfo")):
    """(major, minor) of every mounted filesystem source (field 3 of mountinfo)."""
    found = set()
    for line in Path(mountinfo).read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split()
        if len(fields) > 2 and ":" in fields[2]:
            major, minor = fields[2].split(":", 1)
            if major.isdigit() and minor.isdigit():
                found.add((int(major), int(minor)))
    return found


def swap_devices(swaps=Path("/proc/swaps")):
    try:
        lines = Path(swaps).read_text(encoding="utf-8", errors="replace").splitlines()[1:]
    except OSError:
        return set()
    return {os.path.realpath(line.split()[0]) for line in lines if line.split()}


def holders(device):
    try:
        return sorted(os.listdir(Path("/sys/class/block", Path(os.path.realpath(device)).name, "holders")))
    except OSError:
        return []


def dev_numbers(dev):
    """(major, minor) of a device number (os.major/os.minor; the Linux encoding where they are missing)."""
    if hasattr(os, "major"):
        return os.major(dev), os.minor(dev)
    return ((dev >> 8) & 0xFFF) | ((dev >> 32) & ~0xFFF), (dev & 0xFF) | ((dev >> 12) & ~0xFF)


def device_of(path):
    """/dev node of the filesystem that holds path (through /sys/dev/block), None if unknown."""
    try:
        return "/dev/" + Path(os.readlink("/sys/dev/block/%d:%d" % dev_numbers(os.stat(path).st_dev))).name
    except OSError:
        return None


# ---------------------------------------------------------------- pure checks (host-testable)

def rsync_argv(source, target):
    """The copy of the active root: -x stays on its filesystem (ESP, /data, /run, /proc are other mounts),
    --delete makes the target an exact copy except the per-slot files, which are neither copied nor deleted."""
    return list(RSYNC) + ["--exclude=/" + p for p in PER_SLOT_FILES] + [str(source).rstrip("/") + "/", str(target).rstrip("/") + "/"]


def resolve_slots(root, cmdline_text, online):
    """Active, running and target slot of --root. online: --root is the running system."""
    config = bootchain.load_config(Path(root) / "etc/srrx/boot.json")
    active = bootchain.read_slot(Path(root) / "etc/srrx/slot")
    tokens = bootchain.proc_tokens(cmdline_text)
    running = [s for s in bootchain.SLOTS if "root=PARTUUID=" + bootchain.root_partuuid(config, s) in tokens]
    issues = []
    if len(running) > 1:
        issues.append("the running command line names both slot roots")
    running = running[0] if len(running) == 1 else None
    if online and running != active:
        issues.append("the running root is %s, not the slot %s of /etc/srrx/slot: refusing to pick a target"
                      % ("slot " + running if running else "no slot of /etc/srrx/boot.json", active))
    if not online and running is not None:
        issues.append("slot %s of this image is the running root here: update it from the running system (--root /)" % running)
    target = bootchain.other(active)
    if target == running:
        issues.append("the target slot %s is the running slot" % target)
    return {"config": config, "route": config["route"], "active_slot": active, "running_slot": running, "target_slot": target,
            "target_partuuid": bootchain.root_partuuid(config, target), "issues": issues}


def target_findings(device, partuuid, root, mounted=None, swaps=None, held_by=None, blkid=None):
    """(facts, issues) of the target partition: a block device with the target PARTUUID, neither the
    filesystem of --root nor mounted, swap or held anywhere."""
    info, issues = {"device": str(device), "partuuid": partuuid}, []
    try:
        st = os.stat(device)
    except OSError as exc:
        return info, ["target partition %s unavailable: %s" % (device, type(exc).__name__)]
    if not stat.S_ISBLK(st.st_mode):
        return info, ["target %s is not a block device" % device]
    found = (blkid or partuuid_of)(device)
    info["blkid_partuuid"] = found
    if found != partuuid:
        issues.append("target %s has PARTUUID %s, not the slot's %s" % (device, found, partuuid))
    rdev = dev_numbers(st.st_rdev)
    info["mounted"] = rdev in (mounted if mounted is not None else mounted_devices())
    if info["mounted"]:
        issues.append("target %s is mounted: refusing to write a mounted slot" % device)
    if os.stat(root).st_dev == st.st_rdev:
        issues.append("target %s holds the filesystem of --root" % device)
    if os.path.realpath(device) in (swaps if swaps is not None else swap_devices()):
        issues.append("target %s is in use as swap" % device)
    info["holders"] = (held_by or holders)(device)
    if info["holders"]:
        issues.append("target %s is held by %s" % (device, ",".join(info["holders"])))
    return info, issues


def esp_findings(root, config, blkid=None, device=None):
    esp = Path(root) / "boot/efi"
    info, issues = {"path": str(esp)}, []
    if not bootchain._is_mountpoint(esp):
        return info, [str(esp) + " is not a mounted ESP"]
    info["device"] = (device or device_of)(esp)
    info["partuuid"] = (blkid or partuuid_of)(info["device"]) if info["device"] else None
    if info["partuuid"] != config["esp_partuuid"]:
        issues.append("the ESP at %s has PARTUUID %s, not %s of boot.json" % (esp, info["partuuid"], config["esp_partuuid"]))
    return info, issues


def precondition_findings(unit_state, labd, external_power):
    """(record, issues) of the controller and power preconditions.
    unit_state: ActiveState of srrx.service; labd: labd_status() (None: no labd answers);
    external_power: the --external-power-confirmed note or None."""
    issues = []
    controller = {"unit": CONTROLLER_UNIT, "active_state": unit_state, "inactive": unit_state not in ACTIVE_STATES + ("unknown",)}
    if not controller["inactive"]:
        issues.append("%s (labd) is %s: stop the controller before an update" % (CONTROLLER_UNIT, unit_state))
    reachable = type(labd) is dict and "error" not in labd
    armed = (labd.get("policy") or {}).get("armed") if reachable else None
    disarmed = {"labd_reachable": reachable, "armed": armed, "disarmed": (not reachable) or armed is False,
                "labd_error": labd.get("error") if type(labd) is dict else None}
    if not disarmed["disarmed"]:
        issues.append("labd reports armed=%r: DISARM first" % armed)
    soc, accepted = ((labd.get(LABD_SOC_FIELDS[0]), labd.get(LABD_SOC_FIELDS[1])) if reachable else (None, None))
    if external_power:
        power = {"source": "external_power_confirmed", "note": str(external_power)[:200], "ok": True}
    elif accepted is True and type(soc) in (int, float) and not isinstance(soc, bool):
        power = {"source": "labd_gauge", "soc_percent": soc, "min_percent": SOC_MIN_PERCENT, "ok": soc >= SOC_MIN_PERCENT}
        if not power["ok"]:
            issues.append("state of charge %s %% is below %d %% (STACK.md:906)" % (soc, SOC_MIN_PERCENT))
    else:
        power = {"source": None, "ok": False, "gauge": "labd reports no accepted state of charge (%s; OPEN until a gauge is accepted)"
                 % "/".join(LABD_SOC_FIELDS)}
        issues.append("power precondition not met: no accepted state-of-charge gauge in labd; confirm external power with "
                      "--external-power-confirmed NOTE")
    return {"controller": controller, "labd": disarmed, "power": power}, issues


def trust_findings(root, ci_test_key=None, release=False):
    """(trust, issues): the keyring, fingerprint and labels of the publications' check."""
    if ci_test_key and release:
        return None, ["--ci-test-key and --release exclude each other"]
    if ci_test_key:
        keyring, fingerprint = Path(ci_test_key[0]), str(ci_test_key[1]).upper()
        try:
            info = build_image.keyring_info(keyring.read_bytes())
        except (OSError, ValueError) as exc:
            return None, ["CI test keyring unreadable: " + str(exc)[:200]]
        trust = {"mode": "ci-test-key", "release": "NOT_RELEASE", "keyring": str(keyring), "keyring_sha256": info["sha256"],
                 "fingerprint": fingerprint, "uids": info["uids"], "build_records": None, "inrelease_sha256": None}
        issues = []
        if not any(CI_TEST_UID.lower() in uid.lower() for uid in info["uids"]):
            issues.append("--ci-test-key keyring has no '%s' uid: a release key is checked with --release only" % CI_TEST_UID)
        if fingerprint not in info["fingerprints"] + info["subkeys"]:
            issues.append("fingerprint %s is not a key of the CI test keyring" % fingerprint)
        return trust, issues
    if not release:
        return None, ["no trust given: --release (reviewed release record) or --ci-test-key KEYRING FINGERPRINT"]
    try:
        record = deploy.load(Path(root) / RELEASE_RECORD)
        snapshot = record["offline_snapshot"]
        if record.get("status") != "REVIEWED" or snapshot.get("status") != "REVIEWED":
            return None, ["release record /" + RELEASE_RECORD + " or its offline_snapshot is not REVIEWED"]
        keyring = Path(root) / str(snapshot["keyring"]).lstrip("/")
        info = build_image.keyring_info(keyring.read_bytes())
        records = []
        for item in snapshot["build_records"]:
            path = Path(root) / str(item["path"]).lstrip("/")
            if sha256(path) != item["sha256"]:
                return None, ["release record build record differs: " + str(item["path"])]
            records.append(path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return None, ["release record unusable: " + str(exc)[:300]]
    trust = {"mode": "release", "release": "RELEASE_PATH", "keyring": str(keyring), "keyring_sha256": info["sha256"],
             "fingerprint": str(snapshot["signing_fingerprint"]).upper(), "uids": info["uids"], "build_records": [str(p) for p in records],
             "inrelease_sha256": snapshot["inrelease_sha256"], "repo": snapshot["repo"]}
    issues = build_image.release_keyring_issues(info)
    return trust, issues


def publication_packages(repo, publication):
    """{(package, version, architecture)} of the Packages index of a publication (after verify_repo)."""
    policy = deploy.load(deploy.REPO_POLICY)
    names = policy["mirror"] if publication == "srrx-mirror" else policy
    index = Path(repo) / "dists" / names["codename"] / names["component"] / ("binary-" + names["architecture"]) / "Packages"
    return {(s.get("package"), s.get("version"), s.get("architecture")) for s in deploy.deb822(index.read_text(encoding="utf-8"), "Packages")}


def verify_publications(root, trust, lab_repo=None, mirror_repo=None, build_records=()):
    """({publication: verify_repo result, REFUSED with the error, or None}, {publication: packages}, issues)."""
    results, packages, issues = {}, {}, []
    if lab_repo is None and mirror_repo is None:
        issues.append("no publication given: --lab-repo and/or --mirror-repo")
    root = Path(root)
    status = root / "var/lib/dpkg/status"
    for publication, repo in (("srrx-lab", lab_repo), ("srrx-mirror", mirror_repo)):
        if repo is None:
            results[publication] = None
            continue
        if trust is None:
            results[publication] = {"status": "NOT_CHECKED", "error": "no trust"}
            continue
        try:
            if publication == "srrx-lab":
                release = trust["mode"] == "release"
                result = deploy.verify_repo(repo, trust["keyring"], trust["fingerprint"],
                                            trust["build_records"] if release else list(build_records), root / SOURCES[publication],
                                            trust["inrelease_sha256"], status, release=release)
            else:
                if trust["mode"] == "release":
                    raise deploy.DeploymentError("the release record pins no srrx-mirror InRelease yet (RM-6 OPEN): the release path "
                                                 "refuses the mirror")
                closure = root / CLOSURE if (root / CLOSURE).is_file() else HERE / "package-closure.json"
                result = deploy.verify_repo(repo, trust["keyring"], trust["fingerprint"], [], root / SOURCES[publication], None, status,
                                            closure=closure)
            found = publication_packages(repo, publication)
        except (deploy.DeploymentError, OSError, ValueError, KeyError) as exc:
            results[publication] = {"status": "REFUSED", "repo": str(repo), "error": str(exc)[:600]}
            issues.append(publication + " refused: " + str(exc)[:300])
            continue
        packages[publication] = found
        results[publication] = dict(result, repo=str(repo), package_versions=sorted("%s=%s" % (n, v) for n, v, _ in found))
    return results, packages, issues


def protected_globs(recipe=None, policy=None):
    recipe = build_image.load_json(build_image.RECIPE) if recipe is None else recipe
    policy = deploy.load(deploy.REPO_POLICY) if policy is None else policy
    return sorted(set(policy["never_in_lab_repo_globs"]) | set(recipe["holds"]["names"]) | set(recipe["holds"]["globs"])
                  | set(BOOT_CHAIN_GLOBS))


def plan_issues(apt_plan, apt_text, held, globs, packages):
    """Refusals of a simulated dist-upgrade: a held or protected package changed, a version in no verified
    publication (foreign origin)."""
    available = {(n, v) for found in packages.values() for n, v, _ in found}
    issues = []
    if "held packages will be changed" in (apt_text or ""):
        issues.append("apt would change held packages")
    for name, version in sorted(apt_plan["install"].items()):
        if name in held:
            issues.append("apt would change the held package %s to %s" % (name, version))
        elif any(fnmatch.fnmatchcase(name, g) for g in globs):
            issues.append("apt would change %s to %s: kernel, boot chain, firmware or a recipe-held package never changes in an update"
                          % (name, version))
        if (name, version) not in available:
            issues.append("foreign origin: %s %s is in no verified publication (%s)" % (name, version, ", ".join(sorted(packages)) or "none"))
    for name in apt_plan["remove"]:
        if name in held or any(fnmatch.fnmatchcase(name, g) for g in globs):
            issues.append("apt would remove the held or protected package " + name)
    return issues


def change_issues(apt_plan, changes):
    """The dpkg status change of the applied dist-upgrade against the simulated plan."""
    issues = []
    for name, (before, after) in sorted(changes.items()):
        if name in apt_plan["install"]:
            if after != apt_plan["install"][name]:
                issues.append("%s is %s after the upgrade, the plan said %s" % (name, after, apt_plan["install"][name]))
        elif name in apt_plan["remove"]:
            if after is not None:
                issues.append("%s was planned for removal and is %s" % (name, after))
        else:
            issues.append("%s changed outside the plan: %s -> %s" % (name, before, after))
    issues += ["%s planned but unchanged" % n for n in sorted(set(apt_plan["install"]) | set(apt_plan["remove"])) if n not in changes]
    return issues


def per_slot_findings(config, slot, target_root):
    """The target's own per-slot files after the copy: its slot letter, its command line, its root line."""
    root = Path(target_root)
    issues, found = [], {}
    for relative in PER_SLOT_FILES:
        path = root / relative
        found[relative] = sha256(path) if path.is_file() else None
    try:
        if bootchain.read_slot(root / "etc/srrx/slot") != slot:
            issues.append("target etc/srrx/slot is not " + slot)
    except (OSError, ValueError) as exc:
        issues.append("target etc/srrx/slot unreadable: " + str(exc)[:200])
    line = bootchain.cmdline(config["base_cmdline_without_root"], bootchain.root_partuuid(config, slot), config["lime_build"])
    cmdline = root / "etc/kernel/cmdline"
    if not cmdline.is_file() or cmdline.read_text(encoding="ascii", errors="replace").strip() != line:
        issues.append("target etc/kernel/cmdline is not the slot %s line of boot.json" % slot)
    fstab = (root / "etc/fstab").read_text(encoding="utf-8", errors="replace") if (root / "etc/fstab").is_file() else ""
    roots = [l.split()[0] for l in fstab.splitlines() if len(l.split()) > 1 and not l.startswith("#") and l.split()[1] == "/"]
    if roots != ["PARTUUID=" + bootchain.root_partuuid(config, slot)]:
        issues.append("target etc/fstab mounts %r at /, not the slot %s root" % (roots, slot))
    return found, issues


def carried_files(root):
    """{relative path: SHA-256} of the per-unit files present in --root (CARRIED)."""
    root = Path(root)
    found = {}
    for pattern in CARRIED:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and not path.is_symlink():
                found[path.relative_to(root).as_posix()] = sha256(path)
    return dict(sorted(found.items()))


def carried_issues(source, target_root):
    return ["per-unit file %s differs or is missing in the target" % p for p, digest in sorted(source.items())
            if not (Path(target_root) / p).is_file() or sha256(Path(target_root) / p) != digest]


def last_record(directory):
    directory = Path(directory)
    names = sorted(p.name for p in directory.glob("*.json")) if directory.is_dir() else []
    if not names:
        return None
    try:
        record = json.loads((directory / names[-1]).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"name": names[-1], "status": "unreadable"}
    return {"name": names[-1], "status": record.get("status"), "release": record.get("release"), "active_slot": record.get("active_slot"),
            "target_slot": record.get("target_slot"), "finished_at": record.get("finished_at")}


def write_record(directory, record):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o750)
    stamp = record["started_at"].replace("-", "").replace(":", "")
    path = directory / (stamp + ".json")
    index = 1
    while path.exists():  # "_N" sorts after ".json", so the newest name of one second is the last one
        path = directory / ("%s_%d.json" % (stamp, index))
        index += 1
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    os.chmod(tmp, 0o640)
    os.replace(tmp, path)
    return path


# ---------------------------------------------------------------- plan and apply

def plan(root=Path("/"), target_device=None, lab_repo=None, mirror_repo=None, build_records=(), ci_test_key=None, release=False,
         external_power=None, records=None, online=None):
    """Read-only. Everything apply checks before it writes; "refusals" lists what blocks apply now."""
    root = Path(root).resolve()
    online = (root == Path("/").resolve()) if online is None else online
    slots = resolve_slots(root, proc_cmdline(), online)
    config = slots.pop("config")
    refusals = list(slots.pop("issues"))
    device = target_device or "/dev/disk/by-partuuid/" + slots["target_partuuid"]
    target, issues = target_findings(device, slots["target_partuuid"], root)
    refusals += issues
    esp, issues = esp_findings(root, config)
    refusals += issues
    records = Path(records) if records else root / RECORDS
    records_ok = records.is_relative_to(root / "data") and bootchain._is_mountpoint(root / "data")
    if not records_ok:
        refusals.append("records go to /data/srrx-updates on the mounted /data partition: %s" % records)
    pre, issues = precondition_findings(unit_active_state(CONTROLLER_UNIT), labd_status(), external_power)
    refusals += issues
    trust, issues = trust_findings(root, ci_test_key, release)
    refusals += issues
    publications, packages, issues = verify_publications(root, trust, lab_repo, mirror_repo, build_records)
    refusals += issues
    checks = {"target_not_running": slots["target_slot"] != slots["running_slot"], "target_not_mounted": target.get("mounted") is False,
              "srrx_inactive": pre["controller"]["inactive"], "labd_disarmed": pre["labd"]["disarmed"], "power": pre["power"]["ok"],
              "publications_verified": bool(packages) and not issues, "records_on_data": records_ok}
    return {"status": "PLAN_ONLY", "kind": KIND, "mode": "running-system" if online else "offline-image", "root": str(root),
            "route": slots["route"], "active_slot": slots["active_slot"], "running_slot": slots["running_slot"],
            "target_slot": slots["target_slot"], "target": target, "esp": esp, "preconditions": pre,
            "trust": {k: v for k, v in (trust or {}).items() if k != "uids"} or None, "release": (trust or {}).get("release"),
            "publications": publications, "per_slot_files": list(PER_SLOT_FILES), "carried": sorted(carried_files(root)),
            "records": str(records), "last_record": last_record(records), "checks": checks, "refusals": refusals,
            "hardware_ready": False, "bench_gates_open": ["W-03"],
            "_internal": {"config": config, "packages": packages, "device": device}}


def _apt_options(work):
    return ["-o", "Dir::Etc::SourceList=" + work + "/sources.list", "-o", "Dir::Etc::SourceParts=" + work + "/empty",
            "-o", "Dir::State::Lists=" + work + "/lists", "-o", "Dir::Cache=" + work + "/cache", "-o", "APT::Sandbox::User=root",
            "-o", "Acquire::Languages=none", "-o", "APT::Install-Recommends=false",
            "-o", "Dpkg::Options::=--force-confdef", "-o", "Dpkg::Options::=--force-confold"]


def source_list(packages, keyring):
    """deb lines of the verified publications only, file: URIs under the chroot's /run, Signed-By the checked keyring."""
    policy = deploy.load(deploy.REPO_POLICY)
    lines = []
    for publication in PUBLICATIONS:
        if publication in packages:
            names = policy["mirror"] if publication == "srrx-mirror" else policy
            lines.append("deb [arch=%s signed-by=%s] file:/%s/repo/%s %s %s" % (names["architecture"], keyring, CHROOT_WORK, publication,
                                                                              names["codename"], names["component"]))
    return "\n".join(lines) + "\n"


def remove_slot_entries(esp, slot):
    """The target slot's lab entries (not its rescue entry): it is not bootable while its root is rewritten."""
    removed = []
    for path in sorted((Path(esp) / "loader/entries").glob("lab" + slot + "*.conf")):
        if bootchain.ENTRY_NAME.match(path.name):
            path.unlink()
            removed.append(path.name)
    return removed


def arm_trial(config, slot, esp, target_root):
    """After kernel-install: the trial entry is there; Route B also gets the trial marker and loader.conf."""
    entries = sorted(p.name for p in (Path(esp) / "loader/entries").glob("lab" + slot + "*.conf") if bootchain.ENTRY_NAME.match(p.name))
    if config["route"] == "A":
        tries = bootchain.read_tries(Path(target_root) / "etc/kernel/tries")
        want = "lab%s+%d.conf" % (slot, tries) if tries else None
        if not want or entries != [want]:
            raise UpdateError("slot %s entries after kernel-install are %r, expected [%r]" % (slot, entries, want))
        return {"slot": slot, "route": "A", "entry": want, "mechanism": "boot counting: tries %d, bless by systemd-bless-boot after "
                "boot-complete.target (srrx-boot-check)" % tries}
    if entries != ["lab%s.conf" % slot]:
        raise UpdateError("slot %s entries after kernel-install are %r" % (slot, entries))
    bootchain._atomic_write(Path(esp) / bootchain.TRIAL_MARK, (slot + "\n").encode())
    bootchain._atomic_write(Path(esp) / "loader/loader.conf", bootchain.loader_conf(config, slot).encode())
    if (Path(esp) / bootchain.BOOTING_MARK).exists():
        (Path(esp) / bootchain.BOOTING_MARK).unlink()
    return {"slot": slot, "route": "B", "entry": entries[0], "mechanism": "ESP " + bootchain.TRIAL_MARK + " and loader.conf default lab"
            + slot + "; initramfs write-back, srrx-ab-commit after boot-complete.target"}


def disarm_trial(config, slot, esp, active):
    removed = remove_slot_entries(esp, slot)
    if config["route"] == "B":
        if (Path(esp) / bootchain.TRIAL_MARK).exists():
            (Path(esp) / bootchain.TRIAL_MARK).unlink()
        bootchain._atomic_write(Path(esp) / "loader/loader.conf", bootchain.loader_conf(config, active).encode())
    return removed


def apply(root=Path("/"), target_device=None, lab_repo=None, mirror_repo=None, build_records=(), ci_test_key=None, release=False,
          external_power=None, records=None, partitions=None, execute=False, online=None):
    """plan(), then with execute=True the update of the target slot; returns the record (also written to /data/srrx-updates)."""
    started = utc_now()
    report = plan(root, target_device, lab_repo, mirror_repo, build_records, ci_test_key, release, external_power, records, online)
    internal = report.pop("_internal")
    if not execute:
        return dict(report, status="DRY_RUN_ONLY", note="nothing written: apply needs --execute")
    if os.geteuid() != 0:
        raise UpdateError("apply --execute needs root")
    root, config, slot, active = Path(report["root"]), internal["config"], report["target_slot"], report["active_slot"]
    record = {k: v for k, v in report.items() if k not in ("status", "last_record", "checks")}
    record.update(schema_version=1, status="REFUSED", started_at=started, apt=None, kernel_install=None, trial=None,
                  target_entries_removed=[], publication_packages={p: sorted("%s=%s" % (n, v) for n, v, _ in found)
                                                                   for p, found in internal["packages"].items()})
    if report["refusals"]:
        record["finished_at"] = utc_now()
        # A record outside the mounted /data would land in a root slot: then it is only printed.
        record["record_path"] = str(write_record(report["records"], record)) if report["checks"]["records_on_data"] else None
        return record
    mounts, device, esp = build_image.Mounts(), internal["device"], root / "boot/efi"
    armed = created_policy = False
    policy_file = TARGET_MOUNT / "usr/sbin/policy-rc.d"
    try:
        if TARGET_MOUNT.exists() and bootchain._is_mountpoint(TARGET_MOUNT):
            raise UpdateError(str(TARGET_MOUNT) + " is already a mount point")
        record["status"] = "FAILED"  # from here on the target slot changes; a rule refusal below says REFUSED
        record["target_entries_removed"] = remove_slot_entries(esp, slot)
        mounts.mount(device, TARGET_MOUNT, "ext4")
        source = carried_files(root)
        build_image.run(rsync_argv(root, TARGET_MOUNT))
        record["per_slot_files"], issues = per_slot_findings(config, slot, TARGET_MOUNT)
        record["carried"] = source
        issues += carried_issues(source, TARGET_MOUNT)
        if issues:
            raise Refused("target after the copy: " + "; ".join(issues))
        build_image.chroot_api(mounts, TARGET_MOUNT, partitions)
        mounts.mount(str(esp), TARGET_MOUNT / "boot/efi", bind=True)
        if not policy_file.exists():  # a policy-rc.d the active root carries stays as it is
            build_image.policy_rc(TARGET_MOUNT, True)
            created_policy = True
        work = TARGET_MOUNT / CHROOT_WORK
        for sub in ("empty", "lists/partial", "cache/archives/partial"):
            (work / sub).mkdir(parents=True, exist_ok=True)
        copy_file(report["trust"]["keyring"], work / "srrx-update.gpg")
        for publication, repo in (("srrx-lab", lab_repo), ("srrx-mirror", mirror_repo)):
            if publication in internal["packages"]:
                mounts.mount(str(Path(repo).resolve()), work / "repo" / publication, bind=True)
                build_image.run(["mount", "-o", "remount,bind,ro", work / "repo" / publication])
        (work / "sources.list").write_text(source_list(internal["packages"], "/" + CHROOT_WORK + "/srrx-update.gpg"), encoding="ascii")
        options = _apt_options("/" + CHROOT_WORK)
        before = build_image._dpkg_status(TARGET_MOUNT)
        held = build_image._dpkg_holds(TARGET_MOUNT)
        build_image.chroot(TARGET_MOUNT, ["apt-get", "update", "-q"] + options, extra_env=build_image.CLOSURE_ENV)
        simulated = build_image.chroot(TARGET_MOUNT, ["apt-get", "-s", "-q", "dist-upgrade"] + options, extra_env=build_image.CLOSURE_ENV)
        apt_plan = build_image.apt_simulation(simulated.stdout)
        record["apt"] = {"plan": apt_plan, "held": held, "simulation_tail": simulated.stdout[-1500:]}
        issues = plan_issues(apt_plan, simulated.stdout, set(held), protected_globs(), internal["packages"])
        if issues:
            record["refusals"] = issues
            raise Refused("apt plan refused: " + "; ".join(issues))
        done = build_image.chroot(TARGET_MOUNT, ["apt-get", "dist-upgrade", "-y", "-q"] + options, extra_env=build_image.CLOSURE_ENV)
        changes = build_image.status_changes(before, build_image._dpkg_status(TARGET_MOUNT))
        record["apt"].update(changes={n: {"from": b, "to": a} for n, (b, a) in changes.items()}, apply_tail=done.stdout[-1500:])
        issues = change_issues(apt_plan, changes)
        if issues:
            raise UpdateError("dpkg status after the upgrade: " + "; ".join(issues))
        kver = config["kernel_version"]
        installed = build_image.chroot(TARGET_MOUNT, ["kernel-install", "add", kver, "/boot/vmlinuz-" + kver, "/boot/initrd.img-" + kver])
        lines = [l for l in installed.stdout.splitlines() if l.startswith("{")]
        record["kernel_install"] = json.loads(lines[-1]) if lines else {"stdout_tail": installed.stdout[-600:]}
        record["trial"] = arm_trial(config, slot, esp, TARGET_MOUNT)
        armed = True
    except Refused as exc:
        record.update(status="REFUSED", error=str(exc)[-3000:],
                      target_state="copy of the active root without its boot entries; the next update rewrites it")
    except Exception as exc:  # every failure ends in a record: the target is unbootable, the active slot untouched
        record.update(status="FAILED", error=(type(exc).__name__ + ": " + str(exc))[-3000:])
    finally:
        if created_policy and policy_file.exists():
            build_image.policy_rc(TARGET_MOUNT, False)  # the booted target starts its services normally
        mounts.umount_all()
    if "error" not in record:
        record["target_fsck"] = build_image.run(["e2fsck", "-fn", device], check=False).returncode
        if record["target_fsck"]:
            record.update(status="FAILED", error="e2fsck -fn of the target exited %d" % record["target_fsck"])
        else:
            record["status"] = STATUS_UPDATED
    if record["status"] != STATUS_UPDATED and armed:
        record["trial_disarmed"] = disarm_trial(config, slot, esp, active)
    packages = internal["packages"]
    changed = sorted(n for n, c in ((record.get("apt") or {}).get("changes") or {}).items() if c["to"] is not None)
    record["packages_outside_publications"] = sorted(n for n in changed if not any(n == p for found in packages.values() for p, _, _ in found))
    record["finished_at"] = utc_now()
    record["record_path"] = str(write_record(report["records"], record))
    return record


def copy_file(source, target):
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    os.chmod(target, 0o644)


def compact_plan(report):
    """The plan without the internal objects, for the console of the QEMU model (one JSON line)."""
    out = {k: v for k, v in report.items() if k != "_internal"}
    out["carried"] = len(out.get("carried") or [])
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("op", nargs="?", choices=("plan", "apply"), default="plan")
    parser.add_argument("--execute", action="store_true", help="apply: actually write the target slot (without it apply is a dry run)")
    parser.add_argument("--root", type=Path, default=Path("/"), help="active root: / (running system) or an offline image root (CI model)")
    parser.add_argument("--target-device", help="target partition (default /dev/disk/by-partuuid/<target slot>); PARTUUID checked")
    parser.add_argument("--lab-repo", type=Path, help="srrx-lab publication (aptly public directory)")
    parser.add_argument("--mirror-repo", type=Path, help="srrx-mirror publication (aptly public directory)")
    parser.add_argument("--build-record", type=Path, action="append", default=[], help="--ci-test-key with --lab-repo: build records")
    trust = parser.add_mutually_exclusive_group()
    trust.add_argument("--release", action="store_true", help="the reviewed release record and image keyring (verify_repo release=True)")
    trust.add_argument("--ci-test-key", nargs=2, metavar=("KEYRING", "FINGERPRINT"), help="job-only CI test key: the record says NOT_RELEASE")
    parser.add_argument("--external-power-confirmed", metavar="NOTE", help="operator confirms external power (no accepted gauge); recorded")
    parser.add_argument("--records", type=Path, help="record directory (default <root>/data/srrx-updates)")
    parser.add_argument("--markers", action="store_true", help="plan: one JSON line between markers (QEMU model console)")
    args = parser.parse_args(argv)
    common = dict(root=args.root, target_device=args.target_device, lab_repo=args.lab_repo, mirror_repo=args.mirror_repo,
                  build_records=args.build_record, ci_test_key=args.ci_test_key, release=args.release,
                  external_power=args.external_power_confirmed, records=args.records)
    try:
        if args.op == "plan":
            report = compact_plan(plan(**common))
            text = json.dumps(report, sort_keys=True, separators=(",", ":")) if args.markers else json.dumps(report, indent=2, sort_keys=True)
            print(PLAN_BEGIN + text + PLAN_END if args.markers else text, flush=True)
            return 0
        record = apply(execute=args.execute, **common)
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0 if record["status"] in (STATUS_UPDATED, "DRY_RUN_ONLY") else 1
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
