#!/usr/bin/env python3
"""SR-RX-v2.1 golden A/B image builder (IMG-01/02/04): locked Radxa OS r2 _4096 image + the
deploy.py controller bundle -> an installed A/B UFS image FILE (GPT on 4096-byte sectors).

Runs only as root on a native aarch64 Linux builder (CI: ubuntu-24.04-arm; no qemu-user).
Safety: it writes regular files only. Every loop device it creates is checked to be backed by
its own new image file under --work before any sfdisk, mkfs or mount; it never accepts a block
device path (/dev/sd*, /dev/mmcblk*, /dev/nvme*, /dev/disk/*) as input or output. Writing an
image to the UFS is a separate, explicit bench step (recovery_kit.py write, never in CI).
The chroot gets a minimal /dev (no host disks) and a policy-rc.d that starts no service.

  plan   - ordered steps, sources and layout geometry (no root; host tests)
  fetch  - download the locked base image and kernel debs into a cache and verify them
  facts  - read-only facts of the locked r2 image (partition table, cmdline, ESP, dpkg, units)
  blank  - partitioned and formatted image without an OS (CI layout round trip)
  build  - the full golden image, image-manifest.json and the extent map for the recovery kit
  venvs  - --check: the two venv locks against the guest lock and the wheelhouse manifest (offline, W2 IMG-3)

The result is a CANDIDATE: hardware_ready is always false, bench gates W-01/W-02/W-03/W-08/W-09/W-10
stay OPEN, and the image contains Radxa OS and Qualcomm material that must not be published.
"""
import argparse
import datetime
import functools
import hashlib
import json
import os
from pathlib import Path
import platform
import posixpath
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import time
import urllib.request

HERE = Path(__file__).resolve().parent
DEPLOYMENT = HERE.parent
PROJECT = DEPLOYMENT.parent
sys.path[:0] = [str(HERE), str(DEPLOYMENT)]
import bootchain  # noqa: E402
import layout as layoutlib  # noqa: E402

RECIPE = HERE / "recipe.json"
FILES = HERE / "files"
LOCK = DEPLOYMENT / "sources.lock.json"
POLICY = DEPLOYMENT / "receive-only-policy.json"
BLOCKDEV_PREFIXES = ("/dev/sd", "/dev/mmcblk", "/dev/nvme", "/dev/disk/", "/dev/vd", "/dev/hd", "/dev/ufs", "/dev/mapper/")
CONFIG_KEYS = ("CONFIG_VIRTIO_BLK", "CONFIG_VIRTIO_PCI", "CONFIG_VIRTIO_MMIO", "CONFIG_PCI_HOST_GENERIC", "CONFIG_SERIAL_AMBA_PL011",
               "CONFIG_SERIAL_AMBA_PL011_CONSOLE", "CONFIG_EFI", "CONFIG_EFI_STUB", "CONFIG_EXT4_FS", "CONFIG_VFAT_FS", "CONFIG_NLS_CODEPAGE_437",
               "CONFIG_NLS_ISO8859_1", "CONFIG_QUOTA", "CONFIG_QFMT_V2", "CONFIG_QUOTACTL", "CONFIG_CGROUP_BPF", "CONFIG_PPS_CLIENT_GPIO",
               "CONFIG_BLK_DEV_LOOP", "CONFIG_RTC_DRV_PL031", "CONFIG_DRM_VIRTIO_GPU", "CONFIG_HW_RANDOM_VIRTIO", "CONFIG_ARM_SMMU_V3",
               # Module signing decides whether a builder-built out-of-tree module (DKMS pps-gpio) can load at all.
               "CONFIG_MODULE_SIG", "CONFIG_MODULE_SIG_FORCE", "CONFIG_MODULE_SIG_ALL", "CONFIG_MODULE_SIG_HASH")
# The pin_only globs of receive-only-policy.json (libsnpe*, hexagon-dsp-binaries*, dragonwing-defaults) and tzdata
# (chrony's tzdata-legacy closure) are listed too, so the facts name every package RX-01a could block.
INTEREST = re.compile(r"(linux-(image|headers|modules|firmware)|systemd|embloader|sdboot|radxa|rsetup|u-boot|edk2|fastrpc|qcom|qnn|qairt|"
                      r"mesa|libdrm|task-|aic8800|unattended|brltty|modemmanager|gdm3|greetd|labwc|python3$|python3\.12|dkms|gcc|initramfs|"
                      r"util-linux|e2fsprogs|dosfstools|chrony|gpsd|libgps|network-manager|openssh|wpasupplicant|bluez|"
                      r"snpe|hexagon-dsp|dragonwing|tzdata)")
REPO = DEPLOYMENT / "repo"
# STACK.md:894: the signed publications are the only apt sources of the image (build/07 section 2):
# srrx-lab (+labN, 1001) and srrx-mirror (mirrored noble snapshot, 990), both Signed-By the owner's
# keyring; lab.pref goes in byte for byte. {image path: repository file}
SRRX_APT_FILES = {"etc/apt/preferences.d/lab.pref": REPO / "lab.pref",
                  "etc/apt/sources.list.d/srrx-lab.sources": REPO / "srrx-lab.sources",
                  "etc/apt/sources.list.d/srrx-mirror.sources": REPO / "srrx-mirror.sources"}
SRRX_KEYRING = "usr/share/keyrings/srrx-lab.gpg"
# NPU payload (build/15 «Збирання образу», software/DEPLOYMENT.md NPU/QNN): the golden image never
# carries the QNN SDK or QAIRT; the owner installs a verified deb on the unit. Package and file globs.
NPU_PAYLOAD_PACKAGES = ("qcom-qnn-sdk*", "radxa-qcom-qairt*", "qairt-*", "libqnn*", "libsnpe*", "qnn-tools", "snpe-tools")
NPU_PAYLOAD_FILES = ("libQnn*", "libSnpe*", "libSNPE*")
MCU_BUILD_MANIFEST = "firmware/dist/build-manifest.json"
# Package closure (W2 IMG-2, build/15 «Закриття пакетів образу (W2 IMG-2)»): what the image adds to r2,
# as hash-locked debs of the pinned snapshot. `closure --resolve` (CI, network) derives the file from the
# gpgv-verified snapshot indices and the r2 dpkg status of image-facts.json; `build` never resolves, it
# installs exactly the listed files with apt and every apt source and preference disabled.
CLOSURE = HERE / "package-closure.json"
CLOSURE_CACHE = "closure"  # cache subdirectory of the closure debs (sr-rx-image.yml caches it under its own key)
CLOSURE_CHROOT_DIR = "var/cache/srrx-closure"
SNAPSHOT_URL = "https://snapshot.ubuntu.com/ubuntu/"
# The packages the closure is resolved for (STACK.md:902, build/07 §1.2) and the accounts their postinst
# creates with adduser: chrony -> _chrony (+ group), gpsd -> gpsd in group dialout (debian/postinst of
# chrony 4.5-1ubuntu4.2 and gpsd 3.25-3ubuntu3.2, read from the snapshot debs 2026-11-07).
CLOSURE_ROOTS = {"chrony": ("_chrony",), "gpsd": ("gpsd",)}
CLOSURE_PACKAGE_KEYS = ("package", "version", "architecture", "filename", "suite", "sha256", "size", "r2_version", "reason")
# Compared between the committed file and a fresh `closure --resolve` (resolved_on is the run date).
CLOSURE_COMPARED = ("snapshot", "suites", "base", "roots", "packages", "expected_removed", "removed_because", "expected_accounts")
# r2's apt hooks (needrestart 3.6, apt-listchanges 3.27 in image-facts.json) stay quiet in the chroot; ucf keeps a local file.
CLOSURE_ENV = {"NEEDRESTART_SUSPEND": "1", "APT_LISTCHANGES_FRONTEND": "none", "UCF_FORCE_CONFFOLD": "1"}
# Python venvs (W2 IMG-3, build/15 «Python venv в еталонному образі (W2 IMG-3)»): /opt/srrx/venv (touch console,
# record unit) and /opt/srrx/passes-venv (srrx-passes@.service, the QEMU live selftest) are built in root A from the
# hash-locked wheels of the guest wheelhouse: venv --copies --without-pip, pip run from its locked wheel through
# PYTHONPATH (never installed), --no-index --require-hashes --no-compile, then the project --no-deps
# --no-build-isolation from a copy in /tmp (setuptools writes build/ and *.egg-info next to its sources).
WHEELHOUSE = DEPLOYMENT / "linux_lab/wheelhouse-manifest.json"
GUEST_LOCK = DEPLOYMENT / "linux_lab/wheelhouse-requirements.txt"
VENVS = {"opt/srrx/venv": {"lock": "software/config/hmi-requirements.lock", "qt": True},
         "opt/srrx/passes-venv": {"lock": "software/config/passes-requirements.lock", "qt": False}}
PIP_BOOTSTRAP = "pip"  # the guest-lock pip wheel: on PYTHONPATH of the install commands only
WHEEL_CACHE = "wheels"  # cache subdirectory of the venv wheels (sr-rx-image.yml caches it under its own key)
WHEEL_URL = "https://files.pythonhosted.org/packages/"
WHEELS_CHROOT_DIR = "var/cache/srrx-wheels"
BUILD_COPY = "tmp/srrx-software-build"  # chroot /tmp is a tmpfs (chroot_api)
PROJECT_DIST = "srrx-control"
VENV_HOME = "/tmp/srrx-venv-home"
VENV_ENV = {"PYTHONDONTWRITEBYTECODE": "1", "HOME": VENV_HOME, "XDG_CACHE_HOME": VENV_HOME + "/cache"}
PIP_OPTIONS = ["--isolated", "--disable-pip-version-check", "--no-input"]  # general options; --root-user-action is install-only
BUILD_MANIFEST_DRAFT = "build-manifest.draft.json"  # next to image-manifest.json; always OPEN
# SR-RX units whose Exec lines start python3 (unit_interpreters, recipe.json unit_interpreters).
UNIT_SEARCH = ("etc/systemd/system", "usr/lib/systemd/system", "etc/systemd/user", "usr/lib/systemd/user")
EXEC_KEYS = ("ExecCondition", "ExecStartPre", "ExecStart", "ExecStartPost", "ExecReload", "ExecStop", "ExecStopPost")
EXEC_PREFIXES = "-@:+!|"  # systemd.service(5) command prefixes
PYTHON_NAME = re.compile(r"python3(?:\.[0-9]+)?\Z")
FREEZE_CODE = "import importlib.metadata as m, json; print(json.dumps(sorted([d.metadata['Name'], d.version] for d in m.distributions())))"
NUMPY_CODE = ("import json, sys\ntry:\n    import numpy\nexcept ImportError as error:\n"
              "    print(json.dumps({'python': sys.version.split()[0], 'numpy': None, 'error': type(error).__name__}))\n"
              "else:\n    print(json.dumps({'python': sys.version.split()[0], 'numpy': numpy.__version__}))\n")
QT_CODE = ("import json\nfrom PySide6 import QtCore, QtGui, QtWidgets\napp = QtWidgets.QApplication(['srrx-image-check'])\n"
           "print(json.dumps({'qt': QtCore.qVersion(), 'platform': app.platformName()}))\n")
QT_ENV = {"QT_QPA_PLATFORM": "offscreen", "XDG_RUNTIME_DIR": VENV_HOME + "/run"}


class BuildError(RuntimeError):
    pass


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8", newline="\n")


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Log:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.steps = []

    def write(self, text):
        line = time.strftime("%H:%M:%S ") + text
        print(line, file=sys.stderr, flush=True)  # stdout carries only the JSON result
        if self.path:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")

    def step(self, step_id, step_status, **detail):
        self.steps.append({"id": step_id, "status": step_status, "detail": detail})
        self.write("STEP " + step_id + " " + step_status + (" " + json.dumps(detail, ensure_ascii=False)[:400] if detail else ""))


LOG = Log()


def run(argv, check=True, capture=True, input=None, env=None, timeout=7200):
    argv = [str(a) for a in argv]
    LOG.write("$ " + " ".join(argv)[:500])
    done = subprocess.run(argv, input=input, capture_output=capture, text=True, env=env, timeout=timeout)
    if check and done.returncode:
        tail = ((done.stdout or "")[-3000:] + "\n" + (done.stderr or "")[-3000:]) if capture else ""
        raise BuildError("command failed (" + str(done.returncode) + "): " + " ".join(argv)[:300] + "\n" + tail)
    return done


def require_builder():
    if sys.platform != "linux" or platform.machine() != "aarch64":
        raise BuildError("the image builder runs only on native aarch64 Linux (ubuntu-24.04-arm in CI)")
    if os.geteuid() != 0:
        raise BuildError("the image builder needs root for losetup, mount and chroot")
    for tool in ("losetup", "sfdisk", "mkfs.vfat", "mkfs.ext4", "e2fsck", "fsck.vfat", "rsync", "chroot", "xz", "dpkg-deb", "blkid", "systemctl",
                 "dumpe2fs", "debugfs"):
        if shutil.which(tool) is None:
            raise BuildError("builder tool missing: " + tool)


def refuse_block_path(path):
    text = str(path)
    if text.startswith(BLOCKDEV_PREFIXES) or (Path(text).exists() and not Path(text).is_dir() and not Path(text).is_file()):
        raise BuildError("refusing a device or special file: " + text)


def new_regular_file(path, work):
    path = Path(path).resolve()
    refuse_block_path(path)
    if path.exists() or not path.is_relative_to(Path(work).resolve()):
        raise BuildError("output must be a NEW regular file under the work directory: " + str(path))
    return path


# ---------------------------------------------------------------- inputs

def lock_artifacts(lock=None):
    lock = load_json(LOCK) if lock is None else lock
    return {a["id"]: a for a in lock["artifacts"]}


def _download(url, target, expected_sha, expected_size, label):
    """Stream url into target; size and SHA-256 are checked before the rename. Returns PRESENT or FETCHED."""
    target = Path(target)
    if target.is_file() and target.stat().st_size == expected_size and sha256(target) == expected_sha:
        return "PRESENT"
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_name(target.name + ".part")
    digest, size = hashlib.sha256(), 0
    LOG.write("fetch " + url)
    request = urllib.request.Request(url, headers={"User-Agent": "sr-rx-image-builder"})
    with urllib.request.urlopen(request, timeout=120) as response, open(part, "wb") as out:
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
            if size > expected_size:
                raise BuildError("download exceeds the locked size: " + label)
            out.write(chunk)
    if size != expected_size or digest.hexdigest() != expected_sha:
        part.unlink()
        raise BuildError("downloaded bytes differ from the lock: " + label)
    os.replace(part, target)
    return "FETCHED"


def fetch(cache, ids=None, closure=True, wheels=True):
    """Download locked artifacts into cache_path, the package closure debs into cache/closure and the
    venv wheels (W2 IMG-3) into cache/wheels; size and SHA-256 are checked before the rename."""
    cache = Path(cache)
    artifacts = lock_artifacts()
    ids = list(artifacts) if ids is None else ids
    done = {}
    for art_id in ids:
        art = artifacts[art_id]
        target = cache / art["cache_path"]
        if not (target.is_file() and target.stat().st_size == art["size"] and sha256(target) == art["sha256"]) \
                and not art["url"].startswith("https://github.com/"):
            raise BuildError("locked artifact URL is not a GitHub release asset: " + art_id)
        done[art_id] = _download(art["url"], target, art["sha256"], art["size"], art_id)
    import deploy
    verified = deploy.verify_cache(cache, components=[])
    result = {"status": "LOCKED_ARTIFACTS_VERIFIED", "artifacts": done, "verify_cache": verified}
    if closure:
        result["closure"] = fetch_closure(cache)
    if wheels:
        result["wheels"] = fetch_wheels(cache)
    return result


def sparse_decompress(xz_path, out_path, expected_sha=None):
    """xz -> sparse raw file (zero 64 KiB blocks become holes)."""
    if expected_sha is not None and sha256(xz_path) != expected_sha:
        raise BuildError("base image xz differs from the lock")
    out_path = Path(out_path)
    block, zero = 65536, bytes(65536)
    proc = subprocess.Popen(["xz", "-dc", "--threads=0", str(xz_path)], stdout=subprocess.PIPE)
    size = 0
    with open(out_path, "xb") as out:
        while True:
            chunk = proc.stdout.read(1 << 22)
            if not chunk:
                break
            for offset in range(0, len(chunk), block):
                piece = chunk[offset:offset + block]
                if piece == zero[:len(piece)]:
                    out.seek(len(piece), os.SEEK_CUR)
                else:
                    out.write(piece)
            size += len(chunk)
        out.truncate(size)
    if proc.wait():
        raise BuildError("xz failed on the base image")
    return size


# ---------------------------------------------------------------- loop devices and mounts

class Loop:
    """losetup of one regular file; refuses to act unless the kernel reports that exact backing file."""

    def __init__(self, image, read_only=False, sector=4096):
        self.image = Path(image).resolve()
        if not self.image.is_file():
            raise BuildError("loop backing must be a regular file: " + str(self.image))
        argv = ["losetup", "--find", "--show", "--partscan", "--sector-size", str(sector)] + (["--read-only"] if read_only else [])
        self.device = run(argv + [self.image]).stdout.strip()
        if not re.fullmatch(r"/dev/loop[0-9]+", self.device):
            raise BuildError("unexpected loop device " + self.device)
        name = self.device[5:]
        backing = Path("/sys/block", name, "loop/backing_file").read_text().strip()
        if Path(backing).resolve() != self.image:
            self.detach()
            raise BuildError("loop device is not backed by our image file")
        if int(Path("/sys/block", name, "queue/logical_block_size").read_text()) != sector:
            self.detach()
            raise BuildError("loop device does not report the requested logical sector size")
        run(["udevadm", "settle"], check=False)

    def part(self, number):
        path = Path(self.device + "p" + str(number))
        for _ in range(100):
            if path.exists():
                return str(path)
            time.sleep(0.1)
        run(["partx", "-a", self.device], check=False)
        if not path.exists():
            raise BuildError("partition node did not appear: " + str(path))
        return str(path)

    def detach(self):
        if self.device:
            run(["losetup", "-d", self.device], check=False)
            self.device = None


class Mounts:
    def __init__(self):
        self.stack = []

    def mount(self, source, target, fstype=None, options=None, bind=False):
        Path(target).mkdir(parents=True, exist_ok=True)
        argv = ["mount"] + (["--bind"] if bind else []) + (["-t", fstype] if fstype else []) + (["-o", options] if options else [])
        run(argv + [source, target])
        self.stack.append(str(target))

    def umount_all(self):
        while self.stack:
            target = self.stack.pop()
            run(["umount", target], check=False)

    def umount_under(self, prefix):
        prefix = str(prefix)
        for target in [t for t in reversed(self.stack) if t == prefix or t.startswith(prefix + "/")]:
            run(["umount", target])
            self.stack.remove(target)


def minimal_dev(mounts, root, partitions=None):
    """tmpfs /dev with the character nodes package scripts need. The only block devices are the
    image's own loop partitions (with by-partuuid/by-uuid links), so the initramfs fsck hook can
    identify the root filesystem; no host disk is visible."""
    dev = Path(root) / "dev"
    mounts.mount("tmpfs", dev, "tmpfs", "mode=0755,nosuid")
    for name, major, minor in (("null", 1, 3), ("zero", 1, 5), ("full", 1, 7), ("random", 1, 8), ("urandom", 1, 9), ("tty", 5, 0)):
        os.mknod(dev / name, 0o666 | stat.S_IFCHR, os.makedev(major, minor))
    for device, links in (partitions or {}).items():
        if not re.fullmatch(r"/dev/loop[0-9]+p[0-9]+", device):
            raise BuildError("only the image's own loop partitions enter the chroot: " + device)
        node = os.stat(device)
        os.mknod(dev / Path(device).name, 0o660 | stat.S_IFBLK, node.st_rdev)
        for link in links:
            (dev / "disk" / link).parent.mkdir(parents=True, exist_ok=True)
            os.symlink("../../" + Path(device).name, dev / "disk" / link)
    for name, target in (("fd", "/proc/self/fd"), ("stdin", "/proc/self/fd/0"), ("stdout", "/proc/self/fd/1"),
                         ("stderr", "/proc/self/fd/2"), ("ptmx", "pts/ptmx")):
        os.symlink(target, dev / name)
    mounts.mount("devpts", dev / "pts", "devpts", "newinstance,ptmxmode=0666,mode=0620")
    mounts.mount("tmpfs", dev / "shm", "tmpfs", "mode=1777,nosuid,nodev")


def chroot_api(mounts, root, partitions=None):
    minimal_dev(mounts, root, partitions)
    mounts.mount("proc", Path(root) / "proc", "proc", "nosuid,nodev,noexec")
    mounts.mount("sysfs", Path(root) / "sys", "sysfs", "ro,nosuid,nodev,noexec")
    mounts.mount("tmpfs", Path(root) / "run", "tmpfs", "mode=0755,nosuid,nodev")
    mounts.mount("tmpfs", Path(root) / "tmp", "tmpfs", "mode=1777,nosuid,nodev")


CHROOT_ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8", "DEBIAN_FRONTEND": "noninteractive",
              "DEBCONF_NONINTERACTIVE_SEEN": "true", "SYSTEMD_RELAX_ESP_CHECKS": "1", "HOME": "/root", "TERM": "dumb"}


def chroot(root, argv, extra_env=None, check=True):
    env = dict(CHROOT_ENV, **(extra_env or {}))
    return run(["chroot", str(root)] + list(argv), env=env, check=check)


# ---------------------------------------------------------------- facts

def _dpkg_status(root):
    path = Path(root) / "var/lib/dpkg/status"
    packages = {}
    if not path.is_file():
        return packages
    for para in path.read_text(encoding="utf-8", errors="replace").split("\n\n"):
        fields = {}
        for line in para.splitlines():
            if line[:1] not in (" ", "\t") and ":" in line:
                key, value = line.split(":", 1)
                fields[key] = value.strip()
        if fields.get("Package") and fields.get("Status", "").endswith(" installed"):
            name = fields["Package"] + (":" + fields["Architecture"] if fields.get("Multi-Arch") == "same" else "")
            packages[name] = fields.get("Version", "")
    return packages


def _diversions(root):
    path = Path(root) / "var/lib/dpkg/diversions"
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return [{"path": lines[i], "divert_to": lines[i + 1], "package": lines[i + 2]} for i in range(0, len(lines) - 2, 3)]


def _listing(path, hashes=False, limit=400):
    path = Path(path)
    if not path.is_dir():
        return None
    out = []
    for item in sorted(path.iterdir())[:limit]:
        entry = {"name": item.name}
        if item.is_symlink():
            entry["symlink"] = os.readlink(item)
        elif item.is_file():
            entry["size"] = item.stat().st_size
            if hashes:
                entry["sha256"] = sha256(item)
        elif item.is_dir():
            entry["dir"] = True
        out.append(entry)
    return out


def _text(path, limit=8192):
    path = Path(path)
    if not path.is_file():
        return None
    return path.read_bytes()[:limit].decode("utf-8", errors="replace")


def _kernel_config(path):
    text = _text(path, 2_000_000)
    if text is None:
        return None
    values = {}
    for key in CONFIG_KEYS:
        match = re.search(r"^" + key + r"=(\S+)$", text, re.M)
        values[key] = match.group(1) if match else ("not set" if re.search(r"^# " + key + r" is not set$", text, re.M) else None)
    return values


def _accounts(root):
    users = []
    shadow = {}
    if (Path(root) / "etc/shadow").is_file():
        for line in (Path(root) / "etc/shadow").read_text(errors="replace").splitlines():
            parts = line.split(":")
            if len(parts) > 1:
                # Only whether a usable hash exists; the hash itself is never recorded.
                shadow[parts[0]] = bool(parts[1]) and parts[1][0] not in "!*"
    for line in (Path(root) / "etc/passwd").read_text(errors="replace").splitlines():
        parts = line.split(":")
        if len(parts) >= 7 and parts[2].isdigit() and (int(parts[2]) >= 1000 or parts[0] == "root") and parts[0] != "nobody":
            users.append({"name": parts[0], "uid": int(parts[2]), "shell": parts[6], "password_usable": shadow.get(parts[0], False)})
    return users


def _units(root):
    root = Path(root)
    wants = {}
    for directory in sorted((root / "etc/systemd/system").glob("*.wants")) + sorted((root / "etc/systemd/system").glob("*.requires")):
        wants[directory.name] = sorted(p.name for p in directory.iterdir())
    default = root / "etc/systemd/system/default.target"
    unit_dirs = [root / "usr/lib/systemd/system", root / "lib/systemd/system"]
    interesting = sorted({p.name for d in unit_dirs if d.is_dir() for p in d.iterdir()
                          if re.search(r"first|rsetup|resize|grow|repart|embloader|bless|boot-complete|aic|ssh|gdm|greetd", p.name)})
    masked = sorted(p.name for p in (root / "etc/systemd/system").iterdir() if p.is_symlink() and os.readlink(p) == "/dev/null") \
        if (root / "etc/systemd/system").is_dir() else []
    # gdm3's postinst links display-manager.service to its unit; graphical.target wants that alias (W2 IMG-2).
    display_manager = root / "etc/systemd/system/display-manager.service"
    return {"wants": wants, "default_target": os.readlink(default) if default.is_symlink() else None,
            "interesting_units": interesting, "masked": masked,
            "display_manager": os.readlink(display_manager) if display_manager.is_symlink() else
            ("file" if display_manager.exists() else None)}


def _dpkg_holds(root):
    """Packages whose dpkg selection is hold (apt would refuse to change them without a flag)."""
    path = Path(root) / "var/lib/dpkg/status"
    if not path.is_file():
        return []
    held = set()
    for para in path.read_text(encoding="utf-8", errors="replace").split("\n\n"):
        name = re.search(r"^Package: (\S+)$", para, re.M)
        if name and re.search(r"^Status: hold ", para, re.M):
            held.add(name.group(1))
    return sorted(held)


# before.txt commands whose arguments are recorded; others keep only their argument count
# (add_user carries the default passwords, which the facts never repeat).
RSETUP_ARGS_RECORDED = ("disable_service", "enable_service", "remove_packages", "update_locale")


def rsetup_first_boot(path):
    """Commands of rsetup's first-boot script (/config/before.txt on the r2 config partition)."""
    data = Path(path).read_bytes()[:65536]
    commands = []
    for raw in data.decode("utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            words = shlex.split(line, comments=True)
        except ValueError:
            words = line.split()
        if not words:
            continue
        condition = None
        if words[0] == "if" and len(words) >= 3:
            condition, words = words[1], words[2:]
        item = {"command": words[0]}
        if condition:
            item["if"] = condition
        if words[0] in RSETUP_ARGS_RECORDED:
            item["args"] = words[1:]
        else:
            item["args_count"] = len(words) - 1
        commands.append(item)
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data), "commands": commands}


def _unit_name(name):
    return name if "." in name else name + ".service"


def first_boot_review(first_boot, recipe, root):
    """Every before.txt step that this image skips (rsetup.service is masked) must be handled.

    Returns (rows, blocking): one row per command with its handling, and the unhandled ones."""
    handled = recipe["rsetup_first_boot"]["handled"]
    masked = set(recipe["mask"]["units"])
    rows, blocking = [], []
    if not first_boot:
        return [], ["rsetup_first_boot_unknown: the r2 config partition has no before.txt in the facts"]
    for item in first_boot["commands"]:
        row = dict(item, handling=handled.get(item["command"]))
        if row["handling"] is None:
            blocking.append("rsetup_first_boot_unhandled: before.txt runs " + item["command"] + ", which the recipe does not replace or skip")
        if item["command"] in ("disable_service", "enable_service"):
            units = [_unit_name(u) for u in item.get("args", [])]
            enabled = {u: sorted(p.parent.name for p in (Path(root) / "etc/systemd/system").glob("*/" + u)) for u in units}
            row["units"] = {u: "masked" if u in masked else ("enabled: " + ",".join(enabled[u]) if enabled[u] else "not enabled") for u in units}
            for unit, state in row["units"].items():
                # disable_service: the unit must not run in the image; enable_service is skipped, so
                # its unit keeps the image state, which the row records.
                if item["command"] == "disable_service" and state not in ("masked", "not enabled"):
                    blocking.append("rsetup_first_boot_disable_service: " + unit + " is " + state + " in the image")
        rows.append(row)
    return rows, blocking


def _find(root, name, roots=("usr/lib", "boot", "lib/firmware", "usr/share")):
    found = []
    for sub in roots:
        base = Path(root) / sub
        if base.is_dir():
            found += [p.relative_to(root).as_posix() for p in base.rglob(name)]
    return sorted(found)[:50]


def root_facts(root):
    root = Path(root)
    os_release = {}
    for line in (_text(root / "etc/os-release") or "").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            os_release[key] = value.strip('"')
    packages = _dpkg_status(root)
    usage = os.statvfs(root)
    boot = _listing(root / "boot")
    configs = {p.name: _kernel_config(p) for p in sorted((root / "boot").glob("config-*"))}
    machine_id = _text(root / "etc/machine-id")
    return {
        "os_release": {k: os_release.get(k) for k in ("ID", "VERSION_ID", "VERSION_CODENAME", "PRETTY_NAME")},
        "used_bytes": (usage.f_blocks - usage.f_bfree) * usage.f_frsize, "used_inodes": usage.f_files - usage.f_ffree,
        "kernel_cmdline": _text(root / "etc/kernel/cmdline"),
        "etc_kernel": _listing(root / "etc/kernel", hashes=True),
        "kernel_install_conf": _text(root / "etc/kernel/install.conf"), "entry_token": _text(root / "etc/kernel/entry-token"),
        "kernel_install_plugins": {d: _listing(root / d, hashes=True) for d in ("usr/lib/kernel/install.d", "etc/kernel/install.d",
                                   "etc/kernel/postinst.d", "etc/kernel/postrm.d", "etc/kernel/header_postinst.d", "etc/initramfs/post-update.d",
                                   "etc/initramfs-tools/hooks", "usr/share/initramfs-tools/hooks")},
        "fstab": _text(root / "etc/fstab"),
        "boot": boot, "kernel_configs": configs, "modules": _listing(root / "lib/modules"),
        "sdboot_efi": _listing(root / "usr/lib/systemd/boot/efi", hashes=True),
        "embloader_share": _listing(root / "usr/share/embloader", hashes=True),
        "dtb_paths": _find(root, "qcs6490-radxa-dragon-q6a*.dtb"),
        "packages_total": len(packages), "packages_of_interest": {k: v for k, v in sorted(packages.items()) if INTEREST.search(k)},
        "packages": packages, "dpkg_holds": _dpkg_holds(root), "diversions": _diversions(root),
        "apt_sources_list_d": _listing(root / "etc/apt/sources.list.d"),
        "apt_sources_urls": sorted({u for p in [root / "etc/apt/sources.list", *sorted((root / "etc/apt/sources.list.d").glob("*"))]
                                    if p.is_file() for u in re.findall(r"https?://[^\s\"']+", p.read_text(errors="replace"))}),
        "apt_preferences_d": _listing(root / "etc/apt/preferences.d"),
        # names, sizes and SHA-256 only: a netplan file could carry a Wi-Fi secret (W2 SYS-HOST asked whether r2 has a wired profile)
        "netplan": _listing(root / "etc/netplan", hashes=True),
        "units": _units(root), "accounts": _accounts(root),
        "machine_id": "missing" if machine_id is None else ("empty" if not machine_id.strip() else ("uninitialized" if machine_id.strip() == "uninitialized" else "set")),
        "hostname": (_text(root / "etc/hostname") or "").strip(),
        "locale": _text(root / "etc/default/locale"),
        # zram-tools' conffile as r2 ships it; the controller bundle replaces it (system_files.ZRAMSWAP_DEFAULTS).
        "zramswap_default": _text(root / "etc/default/zramswap"),
        # names only: a private host key is never hashed or copied into the facts
        "ssh_host_keys": sorted(p.name for p in (root / "etc/ssh").glob("ssh_host_*")) if (root / "etc/ssh").is_dir() else None,
        "config_dir": _listing(root / "config"),
        "python3": os.readlink(root / "usr/bin/python3") if (root / "usr/bin/python3").is_symlink() else None,
    }


def esp_facts(esp):
    esp = Path(esp)
    files = []
    for path in sorted(esp.rglob("*")):
        if path.is_file():
            files.append({"path": path.relative_to(esp).as_posix(), "size": path.stat().st_size, "sha256": sha256(path)})
    entries = {p.name: _text(p) for p in sorted((esp / "loader/entries").glob("*.conf"))} if (esp / "loader/entries").is_dir() else {}
    return {"files": files, "loader_conf": _text(esp / "loader/loader.conf"), "entries": entries}


def blkid(device):
    out = run(["blkid", "-o", "export", device], check=False).stdout
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


def partition_table(device):
    """sfdisk --json of a loop device: util-linux 2.39 (noble) sfdisk has no --sector-size for files,
    so 4096-byte sectors come from `losetup --sector-size 4096`."""
    if not re.fullmatch(r"/dev/loop[0-9]+", str(device)):
        raise BuildError("partition tables are read from our own loop devices only")
    return json.loads(run(["sfdisk", "--json", str(device)]).stdout)["partitiontable"]


def deb_facts(cache, recipe):
    artifacts = lock_artifacts()
    out = {}
    for art_id in recipe["kernel_artifacts"]:
        deb = Path(cache) / artifacts[art_id]["cache_path"]
        fields = run(["dpkg-deb", "-f", deb, "Package", "Version", "Depends", "Pre-Depends", "Provides"]).stdout
        listing = run(["dpkg-deb", "-c", deb]).stdout.splitlines()
        out[art_id] = {"control": fields.strip().splitlines(),
                       "dtbs": [l.split()[-1] for l in listing if l.endswith(recipe["dtb_name"])],
                       "files": len(listing),
                       "boot_files": [l.split()[-1] for l in listing if "./boot/" in l]}
    return out


def kernel_deb_config(cache, recipe, work):
    """CONFIG_* values of the locked linux-image deb (boot/config-<kver>), read without installing it."""
    deb = Path(cache) / lock_artifacts()[recipe["kernel_artifacts"][0]]["cache_path"]
    target = Path(work) / "kernel-deb"
    if not target.is_dir():
        target.mkdir(parents=True)
        run(["dpkg-deb", "-x", deb, target])
    return target, _kernel_config(target / "boot" / ("config-" + recipe["kernel_version"]))


def facts(cache, work, output=None, keep_mounted=None):
    """Read-only facts of the locked base image. With keep_mounted=(mounts, loop) the caller keeps
    the read-only mounts for the build; otherwise everything is detached again."""
    recipe = load_json(RECIPE)
    art = lock_artifacts()[recipe["base_artifact"]]
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    raw = work / "base.raw"
    if not raw.exists():
        size = sparse_decompress(Path(cache) / art["cache_path"], raw, art["sha256"])
        LOG.step("base-decompress", "DONE", bytes=size)
    mounts, loop = Mounts(), Loop(raw, read_only=True)
    table = partition_table(loop.device)
    result = {"schema_version": 1, "generated_at": utc_now(), "base_artifact": {k: art[k] for k in ("id", "name", "sha256", "size", "url")},
              "raw_bytes": raw.stat().st_size, "partition_table": table, "partitions": []}
    try:
        root_dir = esp_dir = None
        for part in table["partitions"]:
            index = int(re.search(r"([0-9]+)$", part["node"]).group(1))
            device = loop.part(index)
            info = blkid(device)
            entry = {"index": index, "node": part["node"].rsplit("/", 1)[-1], "start": part["start"], "size": part["size"],
                     "type": part.get("type"), "name": part.get("name"), "uuid": part.get("uuid"),
                     "fs_type": info.get("TYPE"), "fs_label": info.get("LABEL"), "fs_uuid": info.get("UUID")}
            if info.get("TYPE") in ("ext4", "vfat"):
                target = work / "base-mnt" / str(index)
                mounts.mount(device, target, info["TYPE"], "ro,noload" if info["TYPE"] == "ext4" else "ro")
                if info["TYPE"] == "ext4" and (target / "etc/os-release").is_file():
                    entry["role"] = "root"
                    root_dir = target
                elif info["TYPE"] == "vfat" and ((target / "EFI").is_dir() or (target / "loader").is_dir()):
                    entry["role"] = "esp"
                    esp_dir = target
                else:
                    entry["role"] = "other"
                    entry["listing"] = _listing(target)
                    if (target / "before.txt").is_file():
                        result["rsetup_first_boot"] = entry["rsetup_before_txt"] = rsetup_first_boot(target / "before.txt")
            result["partitions"].append(entry)
        if root_dir is None or esp_dir is None:
            raise BuildError("base image: root or ESP partition not identified")
        result["root"] = root_facts(root_dir)
        result["esp"] = esp_facts(esp_dir)
        result["kernel_debs"] = deb_facts(cache, recipe)
        _, result["kernel_deb_config"] = kernel_deb_config(cache, recipe, work)
        observed = (result["root"]["kernel_cmdline"] or "").strip()
        try:
            result["base_cmdline_without_root"] = bootchain.strip_root(observed)
            bootchain.validate_base(result["base_cmdline_without_root"])
            result["base_cmdline_status"] = "VALID"
        except ValueError as exc:
            result["base_cmdline_status"] = "INVALID: " + str(exc)
        result["rescue"] = rescue_from_esp(result["esp"], result["root"])
        if output:
            dump(output, result)
        if keep_mounted is not None:
            keep_mounted.extend([mounts, loop, root_dir, esp_dir])
            mounts = loop = None
        return result
    finally:
        if mounts:
            mounts.umount_all()
        if loop:
            loop.detach()


def rescue_from_esp(esp, root):
    """The r2 entry of its own kernel (6.18.2-3) becomes the rescue entry: linux/initrd/devicetree as found."""
    candidates = []
    for name, text in esp["entries"].items():
        fields = {}
        for line in (text or "").splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and not parts[0].startswith("#"):
                fields.setdefault(parts[0], parts[1].strip())
        if "linux" in fields and "6.18.2-3" in (fields.get("version", "") + fields["linux"] + name):
            candidates.append({"entry": name, "kernel": fields["linux"], "initrd": fields.get("initrd"), "dtb": fields.get("devicetree")})
    if len(candidates) != 1:
        return {"status": "NOT_IDENTIFIED", "candidates": candidates}
    return dict(status="IDENTIFIED", **candidates[0])


# ---------------------------------------------------------------- plan

STEPS = (
    ("inputs", "verify the locked base image and kernel debs (deploy.verify_cache) and stage + bundle the controller tree (deploy.py stage, bundle)"),
    ("base-facts", "decompress the r2 _4096 image to a sparse file, attach read-only with 4096-byte sectors, record image-facts.json"),
    ("disk", "new sparse image file, GPT from partition-layout.json (sfdisk on a losetup --sector-size 4096 device), mkfs.vfat -S 4096 / mkfs.ext4 with derived UUIDs"),
    ("root-a-copy", "rsync -aHAXx the r2 root into root A, copy the r2 ESP into the new ESP, detach and delete the base raw file"),
    ("chroot", "minimal /dev, proc, read-only sys, tmpfs run/tmp, policy-rc.d exit 101"),
    ("bundle", "extract the deterministic controller bundle (/opt/srrx, /etc/srrx templates, units) into root A"),
    ("dtb", "package DTB from the locked linux-image deb; lab.dtb = + lab-q6a.dtbo, field.dtb = + lab-q6a.dtbo + field-q6a.dtbo via fdtoverlay when the IMG-05 overlays exist (compared with deployment/system/dt/dt-manifest.json), else the unmerged package DTB marked merged=false"),
    ("bootloader", "Route A: dpkg --purge sdboot-is-embloader, bootctl install --no-variables, embloader pinned -1; Route B: embloader kept (0.4 required)"),
    ("boot-config", "/etc/srrx/boot.json, /etc/srrx/slot, /etc/kernel/cmdline, tries, install.conf layout=other, 90-srrx-bls.install, boot-check unit (Route B: initramfs write-back and commit unit)"),
    ("kernel", "dpkg -i the five locked 6.18.2-4 debs before any apt run; the plugin writes the slot A entry and ESP files"),
    ("closure", "step 8b: apt-get install --purge of the hash-locked package-closure.json debs (chrony, tzdata-legacy, tzdata, gpsd, "
                "libgps30t64) with every apt source and preference disabled and policy-rc.d 101; the apt plan and the dpkg status "
                "change must be exactly the closure (systemd-timesyncd purged); /etc/chrony/chrony.conf replaced by "
                "system_files.chrony_conf() and parsed by chronyd -p (no network directive)"),
    ("accounts", "systemd-sysusers and systemd-tmpfiles --create of the staged SR-RX sysusers.d/tmpfiles.d in the root A chroot "
                 "(/data, /run, /tmp left to systemd-tmpfiles-setup on boot); every SERVICE_ACCOUNTS uid/gid recorded, a missing one is a blocker"),
    ("hardening", "apt-mark hold, purge unattended-upgrades/brltty, masks (apt/fwupd timers, ModemManager, sleep targets, rsetup.service, "
                  "ssh/samba/cups/avahi that rsetup's skipped first boot or the recipe disables, bluetooth/wpa_supplicant, the Ubuntu Pro "
                  "and motd-news units), PPA lists removed, every other r2 apt source diverted to *.srrx-disabled, deployment/repo "
                  "lab.pref, srrx-lab.sources and srrx-mirror.sources installed, default-password accounts locked, empty machine-id, "
                  "r2 SSH host keys removed"),
    ("enable", "srrx-radio-off.service, srrx-boot-check.service (Route B also srrx-ab-commit.service), srrx-ssh-hostkeys.service for a later "
               "sshd start; srrx.service is not enabled (IMG-06); every before.txt step is checked as replaced or skipped; "
               "npu_payload (no QNN SDK/QAIRT) and mcu_firmware (staged firmware/dist/build-manifest.json SHA-256) recorded"),
    ("venvs", "step 11b (W2 IMG-3): /opt/srrx/venv (hmi-requirements.lock) and /opt/srrx/passes-venv (passes-requirements.lock) "
              "in the root A chroot: venv --copies --without-pip, pip from its locked wheel on PYTHONPATH, --no-index "
              "--require-hashes --no-compile, the project --no-deps --no-build-isolation; pip check, freeze = lock, no "
              "__pycache__, srrx copy = staged tree, tree SHA-256; offscreen PySide6 import; unit_interpreters (each SR-RX "
              "python3 unit: interpreter present, NumPy where recipe.json says the unit needs it); OPEN build-manifest draft "
              "of /opt/srrx (deployment/system/build_manifest.py)"),
    ("data", "/etc/fstab of slot A, /data directories, the locked cache copied to /data/srrx-cache (read-only bind at /srv/srrx-cache)"),
    ("selftest", "deployment/selftest.py offline --profile controller on root A (policy DRAFT: BLOCKED expected)"),
    ("root-b", "rsync root A to root B, slot B fstab/cmdline/slot file, kernel-install add in a root B chroot (slot B entry and ESP files)"),
    ("entries", "golden entries: labA (newest) and labB blessed, labA-rescue/labB-rescue with the r2 kernel, loader.conf; foreign r2 entries and the bootctl loader/random-seed removed"),
    ("verify", "sfdisk --verify, e2fsck -fn, fsck.vfat -n, ext4 journal block ranges (dumpe2fs, debugfs) forced into the extent map "
               "for recovery_kit.py, image-manifest.json"),
)


def plan(route="A", data_bytes=None):
    layout = layoutlib.load()
    recipe = load_json(RECIPE)
    ids = layoutlib.identifiers(layout)
    return {"status": "PLAN_ONLY", "route": route, "steps": [{"id": s, "does": d} for s, d in STEPS],
            "route_recipe": recipe["routes"][route], "geometry": layoutlib.geometry(layout, data_bytes), "identifiers": ids,
            "hardware_ready": False}


# ---------------------------------------------------------------- disk

def create_disk(image, layout, ids, data_bytes=None, quota=False):
    geo = layoutlib.geometry(layout, data_bytes)
    with open(image, "xb") as handle:
        handle.truncate(geo["total_bytes"])
    loop = Loop(image, sector=layout["sector_size"])
    try:
        # On the 4K loop device (not the file): sfdisk then re-reads the table and the partitions appear.
        run(["sfdisk", loop.device], input=layoutlib.sfdisk_script(layout, ids, data_bytes))
        run(["udevadm", "settle"], check=False)
        devices = {role: loop.part(i) for i, role in enumerate(layoutlib.ROLES, 1)}
        env = dict(os.environ, E2FSPROGS_FAKE_TIME=str(int(os.environ.get("SOURCE_DATE_EPOCH", "1792800000"))))
        for role, argv in layoutlib.mkfs_commands(layout, ids, devices, quota=quota).items():
            run(argv, env=env)
        return loop, devices, geo
    except BaseException:
        loop.detach()
        raise


def check_disk(loop, devices, layout, ids, geo):
    table = partition_table(loop.device)
    issues = []
    if table.get("sectorsize", 4096) != 4096 or table["id"].lower() != ids["disk_guid"]:
        issues.append("disk GUID or sector size differs")
    for index, role in enumerate(layoutlib.ROLES):
        part = table["partitions"][index]
        want = geo["partitions"][role]
        if (part["start"], part["size"], part["uuid"].lower()) != (want["start"], want["size"], ids["partuuid"][role]):
            issues.append(role + " geometry or PARTUUID differs")
        info = blkid(devices[role])
        expect = ids["esp_volume_id"][:4] + "-" + ids["esp_volume_id"][4:] if role == "esp" else ids["fs_uuid"][role]
        if info.get("UUID", "").upper() != expect.upper():
            issues.append(role + " filesystem UUID differs")
    verify = run(["sfdisk", "--verify", loop.device], check=False)
    if verify.returncode:
        issues.append("sfdisk --verify: " + verify.stdout.strip()[-200:])
    return {"partition_table": table, "issues": issues}


def dumpe2fs_header(text):
    """`dumpe2fs -h` output -> {field: value} (e.g. "Journal inode", "Block size")."""
    fields = {}
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip() and key.strip() not in fields:
            fields[key.strip()] = value.strip()
    return fields


def block_runs(text):
    """`debugfs -R "blocks <ino>"` output (block numbers) -> sorted [(first block, count)] runs."""
    numbers = sorted({int(word) for word in text.split()})
    runs = []
    for number in numbers:
        if runs and number == runs[-1][0] + runs[-1][1]:
            runs[-1] = (runs[-1][0], runs[-1][1] + 1)
        else:
            runs.append((number, 1))
    return runs


def journal_ranges(devices, geo):
    """Image byte ranges of every ext4 journal block (data and extent-tree blocks of the journal
    inode), passed to recovery_kit.make_map as forced extents: mke2fs zeroes the journal with
    fallocate, which leaves holes in the image file that a hole-skipping write would not cover."""
    sector = geo["sector_size"]
    forced, summary = [], {}
    for role in ("root_a", "root_b", "data"):
        header = dumpe2fs_header(run(["dumpe2fs", "-h", devices[role]]).stdout)
        inode, block = header.get("Journal inode", ""), header.get("Block size", "")
        if not inode.isdigit() or not block.isdigit() or int(block) % sector:
            raise BuildError(role + ": no internal ext4 journal or unexpected block size in dumpe2fs -h")
        runs = block_runs(run(["debugfs", "-R", "blocks <" + inode + ">", devices[role]]).stdout)
        base = geo["partitions"][role]["start"] * sector
        blocks = sum(n for _, n in runs)
        # e2fsprogs 1.47 prints "Total journal blocks" (debugfs also lists extent-tree blocks, so >=)
        total = header.get("Total journal blocks", "")
        if not blocks or (total.isdigit() and blocks < int(total)):
            raise BuildError(role + ": debugfs lists %d blocks of the journal inode %s, dumpe2fs says %s" % (blocks, inode, total or "?"))
        for first, count in runs:
            forced.append({"offset": base + first * int(block), "length": count * int(block),
                           "what": role + " ext4 journal (inode " + inode + ")"})
        summary[role] = {"journal_inode": int(inode), "block_size": int(block), "blocks": blocks, "runs": len(runs),
                         "journal_size": header.get("Total journal size", header.get("Journal size"))}
    return forced, summary


def blank(work, output, test_sizes=False):
    """Partitioned, formatted image without an OS: the CI loop-file round trip of IMG-02."""
    require_builder()
    work = Path(work).resolve()
    output = new_regular_file(output, work)
    layout = layoutlib.load()
    if test_sizes:  # CI only: same code path, small partitions (FAT32 needs >= 65525 clusters)
        layout = dict(layout, status="TEST")
        layout["partitions"] = [dict(p) for p in layout["partitions"]]
        sizes = {"esp": 272629760, "root_a": 536870912, "root_b": 536870912}
        for part in layout["partitions"]:
            if part["role"] in sizes:
                part["size_bytes"] = sizes[part["role"]]
            else:
                part["image_size_bytes"] = 268435456
        layoutlib.validate(layout)
    ids = layoutlib.identifiers(layout)
    loop, devices, geo = create_disk(output, layout, ids)
    try:
        report = check_disk(loop, devices, layout, ids, geo)
        mounts = Mounts()
        try:
            for role in layoutlib.ROLES:
                fs = "vfat" if role == "esp" else "ext4"
                mounts.mount(devices[role], work / "blank-mnt" / role, fs)
                (work / "blank-mnt" / role / "srrx-roundtrip").write_text(role + "\n")
        finally:
            mounts.umount_all()
        for role in layoutlib.ROLES:
            argv = ["fsck.vfat", "-n", devices[role]] if role == "esp" else ["e2fsck", "-fn", devices[role]]
            if run(argv, check=False).returncode:
                report["issues"].append(role + " filesystem check failed")
        forced, report["journals"] = journal_ranges(devices, geo)
    finally:
        loop.detach()
    # recovery_kit.py map --forced <this file>: the journals are written even where the file has holes
    forced_path = Path(str(output) + ".forced.json")
    dump(forced_path, forced)
    report.update(status="BLANK_IMAGE_OK" if not report["issues"] else "BLOCKED", image=str(output), geometry=geo, identifiers=ids,
                  layout_status=layout["status"], forced=str(forced_path))
    return report


# ---------------------------------------------------------------- build helpers

def stage_bundle(work):
    import deploy
    stage_dir = Path(work) / "stage"
    bundle_path = Path(work) / "srrx-controller.tar.gz"
    for path in (stage_dir, bundle_path):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    staged = deploy.stage(stage_dir)
    bundled = deploy.bundle(stage_dir, bundle_path)
    return stage_dir, bundle_path, {"stage": staged, "bundle": bundled,
                                    "stage_files_sha256": sha256(stage_dir / "stage-files.json")}


def extract_bundle(bundle_path, root, stage_dir):
    root = Path(root)
    with tarfile.open(bundle_path, "r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            name = Path(member.name)
            if name.is_absolute() or ".." in name.parts or not (member.isdir() or member.isfile()):
                raise BuildError("unsafe bundle member " + member.name)
        archive.extractall(root, members=members, filter="data")
    record = load_json(Path(stage_dir) / "stage-files.json")
    for relative, digest in record["files"].items():
        if sha256(root / relative) != digest:
            raise BuildError("extracted bundle file differs: " + relative)
    return len(record["files"])


def install_file(source, target, mode=0o644):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    os.chmod(target, mode)


def write_text(target, text, mode=0o644):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    os.chmod(target, mode)


DT_MANIFEST = PROJECT / "deployment/system/dt/dt-manifest.json"
# field.dtb = package DTB + lab-q6a.dtbo + field-q6a.dtbo (field-q6a.dtso header, build/07 §3.1,
# STACK.md:843): the field overlay only disables pcie0 on top of the lab overlay.
DT_CHAIN = {"lab": ("lab",), "field": ("lab", "field")}


def build_dtbs(root, kernel_tree, recipe, kver):
    """lab.dtb/field.dtb under /usr/lib/srrx/dtb/<kver>: fdtoverlay of the IMG-05 overlays when present,
    compared with the CI record deployment/system/dt/dt-manifest.json (merge-checked, never booted)."""
    found = sorted(Path(kernel_tree).rglob(recipe["dtb_name"]))
    if len(found) != 1:
        raise BuildError("expected exactly one " + recipe["dtb_name"] + " in the locked linux-image deb, found " + str(len(found)))
    base = found[0]
    store = Path(root) / "usr/lib/srrx/dtb" / kver
    store.mkdir(parents=True, exist_ok=True)
    record = {"base_dtb": "/" + base.relative_to(kernel_tree).as_posix(), "base_dtb_sha256": sha256(base)}
    sources = {name: next((PROJECT / p for p in recipe["dt_overlays"][name] if (PROJECT / p).is_file()), None)
               for name in ("lab", "field")}
    ci = load_json(DT_MANIFEST) if DT_MANIFEST.is_file() else None
    dtbos = {}
    for profile, chain in DT_CHAIN.items():
        target = store / (profile + ".dtb")
        if any(sources[name] is None for name in chain):
            shutil.copyfile(base, target)
            record[profile] = {"merged": False, "overlay": None, "why": "IMG-05 overlay source absent in this tree"}
        else:
            for name in chain:
                if name not in dtbos:
                    dtbos[name] = Path(kernel_tree).parent / (name + ".dtbo")
                    run(["dtc", "-@", "-I", "dts", "-O", "dtb", "-o", dtbos[name], sources[name]])
            run(["fdtoverlay", "-i", base, "-o", target] + [dtbos[name] for name in chain])
            record[profile] = {"merged": True, "overlay": sources[profile].relative_to(PROJECT).as_posix(),
                               "overlay_sha256": sha256(sources[profile]),
                               "applied": [sources[name].relative_to(PROJECT).as_posix() for name in chain]}
        record[profile]["sha256"] = sha256(target)
        if record[profile]["merged"]:
            # Same overlay sources and base DTB as the CI record: the merged bytes must be the recorded ones.
            same_inputs = (ci is not None and ci.get("base_dtb", {}).get("sha256") == record["base_dtb_sha256"]
                           and all(ci.get("sources", {}).get(sources[n].name) == sha256(sources[n]) for n in chain))
            record[profile]["dt_manifest"] = (("MATCH" if ci["merged"].get(profile + ".dtb") == record[profile]["sha256"] else "DIFFERS")
                                              if same_inputs else "NOT_COMPARABLE")
    dump(store / "dtb.json", record)
    return record


def boot_config(layout, ids, route, dt_profile, lime, kver, base_cmdline, rescue):
    config = {"schema_version": 2, "route": route, "active_slot": "A", "trial_slot": None, "dt_profile": dt_profile,
              "lime_build": lime, "kernel_version": kver, "esp_partuuid": ids["partuuid"]["esp"],
              "root_a_partuuid": ids["partuuid"]["root_a"], "root_b_partuuid": ids["partuuid"]["root_b"],
              "base_cmdline_without_root": base_cmdline,
              "slots": {s: {"kernel": "/srrx/%s/linux" % s, "initrd": "/srrx/%s/initrd.img" % s,
                            "lab_dtb": "/srrx/%s/lab.dtb" % s, "field_dtb": "/srrx/%s/field.dtb" % s} for s in bootchain.SLOTS},
              "rescue": {"kernel": rescue["kernel"], "initrd": rescue["initrd"], "dtb": rescue["dtb"]}}
    return bootchain.validate_ab(config)


def write_slot_files(root, config, layout, ids, slot):
    root = Path(root)
    write_text(root / "etc/srrx/boot.json", json.dumps(config, indent=2) + "\n")
    write_text(root / "etc/srrx/slot", slot + "\n")
    line = bootchain.cmdline(config["base_cmdline_without_root"], bootchain.root_partuuid(config, slot), config["lime_build"])
    write_text(root / "etc/kernel/cmdline", line + "\n")
    write_text(root / "etc/fstab", layoutlib.fstab(layout, ids, slot))
    return hashlib.sha256((line + "\n").encode()).hexdigest()


def install_boot_chain(root, route, recipe):
    root = Path(root)
    installed = []
    if route == "A":
        write_text(root / "etc/kernel/tries", "3\n")
        installed.append("etc/kernel/tries")
    write_text(root / "etc/kernel/install.conf", (FILES / "install.conf").read_text())
    install_file(FILES / "90-srrx-bls.install", root / "etc/kernel/install.d/90-srrx-bls.install", 0o755)
    for plugin in recipe["kernel_install"]["mask"]:
        link = root / "etc/kernel/install.d" / plugin
        if link.exists() or link.is_symlink():
            link.unlink()
        os.symlink("/dev/null", link)
    unknown = sorted(p.name for d in ("usr/lib/kernel/install.d", "etc/kernel/install.d") if (root / d).is_dir()
                     for p in (root / d).iterdir() if p.name not in recipe["kernel_install"]["known"] and p.name != "90-srrx-bls.install")
    diverted = []
    for path in recipe["divert_hooks"]["paths"]:
        if os.path.lexists(root / path.lstrip("/")):
            chroot(root, ["dpkg-divert", "--local", "--rename", "--divert", path + ".srrx-disabled", "--add", path])
            diverted.append(path)
    install_file(FILES / "srrx-boot-check.service", root / "etc/systemd/system/srrx-boot-check.service")
    installed += ["etc/kernel/install.conf", "etc/kernel/install.d/90-srrx-bls.install", "etc/systemd/system/srrx-boot-check.service"]
    if route == "A":
        write_text(root / "etc/apt/preferences.d/srrx-boot-route-a.pref", (FILES / "srrx-boot-route-a.pref").read_text())
        installed.append("etc/apt/preferences.d/srrx-boot-route-a.pref")
    else:
        install_file(FILES / "srrx-ab-commit.service", root / "etc/systemd/system/srrx-ab-commit.service")
        install_file(FILES / "initramfs-hook-srrx-ab", root / "etc/initramfs-tools/hooks/srrx-ab", 0o755)
        install_file(FILES / "initramfs-srrx-ab-writeback", root / "etc/initramfs-tools/scripts/local-premount/srrx-ab-writeback", 0o755)
        installed += ["etc/systemd/system/srrx-ab-commit.service", "etc/initramfs-tools/hooks/srrx-ab",
                      "etc/initramfs-tools/scripts/local-premount/srrx-ab-writeback"]
    return {"installed": installed, "unknown_kernel_install_plugins": unknown, "diverted_hooks": diverted,
            "masked_kernel_install_plugins": recipe["kernel_install"]["mask"]}


def policy_rc(root, enable):
    path = Path(root) / "usr/sbin/policy-rc.d"
    if enable:
        write_text(path, "#!/bin/sh\n# SR-RX image builder: no service starts inside the chroot\nexit 101\n", 0o755)
    elif path.exists():
        path.unlink()


def dpkg_installed(root, name):
    return _dpkg_status(root).get(name)


def hardening(root, recipe, route):
    root = Path(root)
    packages = _dpkg_status(root)
    names = {n.split(":", 1)[0] for n in packages}
    import fnmatch
    hold = sorted({n for n in recipe["holds"]["names"] if n in names} |
                  {n for g in recipe["holds"]["globs"] for n in names if fnmatch.fnmatchcase(n, g)}
                  | ({"embloader", "sdboot-is-embloader"} & names if route == "B" else set()))
    missing = sorted(n for n in recipe["holds"]["names"] if n not in names)
    if hold:
        chroot(root, ["apt-mark", "hold"] + hold)
    purge = [n for n in recipe["purge"]["names"] if n in names]
    if purge:
        chroot(root, ["dpkg", "--purge"] + purge)
    masked, masked_by_stage = [], []
    for unit in recipe["mask"]["units"]:
        path = root / "etc/systemd/system" / unit
        if path.is_file() and not path.is_symlink() and path.stat().st_size == 0:
            # deploy.py stage (deployment/system/system_files.py MASKED_UNITS) already masked it with an
            # empty unit file; systemctl mask refuses to replace a regular file (EEXIST).
            masked_by_stage.append(unit)
        else:
            run(["systemctl", "--root", str(root), "mask", unit])
        masked.append(unit)
    # graphical.target wants display-manager.service, r2's alias of the gdm3 unit (W2 IMG-2): its target must be masked.
    display_manager = _units(root)["display_manager"]
    if display_manager not in (None, "file") and Path(display_manager).name not in masked:
        raise BuildError("display-manager.service points to " + display_manager + ", which the recipe does not mask")
    policy = load_json(POLICY)
    tokens = policy["apt"]["forbidden_list_name_tokens"]
    origins = policy["apt_forbidden_origins"]
    removed = []
    for path in sorted((root / "etc/apt/sources.list.d").glob("*")):
        text = path.read_text(errors="replace") if path.is_file() else ""
        if any(t in path.name for t in tokens) or any(o in text for o in origins):
            path.unlink()
            removed.append(path.name)
    sources = apt_sources(root, removed)
    # STACK.md:894: the signed aptly publication is the only apt source and only lab.pref pins positively
    # (selftest RX-16 apt_pin_positive_outside_lab_pref). r2 ships positive pins (local-apt-repository,
    # ubuntu-pro-esm-*): divert them away from apt (it reads only names without an extension or *.pref).
    diverted_prefs = []
    pref_dir = root / "etc/apt/preferences.d"
    for path in sorted(pref_dir.iterdir()) if pref_dir.is_dir() else []:
        if path.name in ("lab.pref", "srrx-boot-route-a.pref") or ("." in path.name and not path.name.endswith(".pref")):
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            text = ""
        if any(int(p) > 0 for p in re.findall(r"^Pin-Priority:\s*(-?[0-9]+)", text, re.M)) or not path.is_file():
            target = "/etc/apt/preferences.d/" + path.name
            chroot(root, ["dpkg-divert", "--local", "--rename", "--divert", target + ".srrx-disabled", "--add", target])
            diverted_prefs.append(path.name)
    locked = []
    for account in _accounts(root):
        if account["password_usable"] and (account["uid"] >= recipe["lock_default_password_accounts"]["min_uid"]):
            chroot(root, ["usermod", "-L", account["name"]])
            locked.append(account["name"])
    machine_id = root / "etc/machine-id"
    previous = "missing" if not machine_id.exists() else ("empty" if not machine_id.read_text().strip() else "set")
    write_text(machine_id, "", 0o444)
    dbus = root / "var/lib/dbus/machine-id"
    if dbus.is_file() and not dbus.is_symlink():
        dbus.unlink()
        os.symlink("/etc/machine-id", dbus)
    # rsetup's first boot (before.txt regenerate_ssh_hostkey) does not run: r2's host keys would be
    # shared by every unit built from this image. Remove them (names recorded, never the keys);
    # srrx-ssh-hostkeys.service generates per-unit keys before a first sshd start (IMG-06).
    ssh_dir = root / "etc/ssh"
    host_keys = sorted(p.name for p in ssh_dir.glob("ssh_host_*")) if ssh_dir.is_dir() else []
    for name in host_keys:
        (ssh_dir / name).unlink()
    install_file(FILES / "srrx-ssh-hostkeys.service", root / "etc/systemd/system/srrx-ssh-hostkeys.service")
    return {"held": hold, "hold_names_not_installed": missing, "purged": purge, "masked": masked, "masked_by_stage": masked_by_stage,
            "display_manager": display_manager, "removed_apt_lists": removed, "diverted_apt_preferences": diverted_prefs, "locked_accounts": locked,
            "machine_id_before": previous, "removed_ssh_host_keys": host_keys, "apt_sources": sources}


def apt_sources(root, removed=()):
    """STACK.md:894: every r2 apt source entry that survived the PPA removal (etc/apt/sources.list and
    each sources.list.d entry, files and links alike) is diverted to <name>.srrx-disabled with
    dpkg-divert --local --rename, so a package upgrade writes its copy there too and apt never reads
    it; then lab.pref, srrx-lab.sources and srrx-mirror.sources are installed byte for byte (0644).
    Returns {installed, disabled, removed}; installed carries the route A pin file when present."""
    root = Path(root)
    lists = root / "etc/apt/sources.list.d"
    ours = {Path(p).name for p in SRRX_APT_FILES if p.startswith("etc/apt/sources.list.d/")}
    candidates = [root / "etc/apt/sources.list"] + (sorted(lists.iterdir()) if lists.is_dir() else [])
    disabled = []
    for path in candidates:
        if not os.path.lexists(path) or path.name in ours or path.name.endswith(".srrx-disabled") or path.is_dir():
            continue
        target = "/" + path.relative_to(root).as_posix()
        chroot(root, ["dpkg-divert", "--local", "--rename", "--divert", target + ".srrx-disabled", "--add", target])
        disabled.append({"path": target[1:], "divert_to": target[1:] + ".srrx-disabled"})
    installed = []
    for relative, source in SRRX_APT_FILES.items():
        install_file(source, root / relative)
        if sha256(root / relative) != sha256(source):
            raise BuildError("installed apt file differs from " + source.relative_to(PROJECT).as_posix())
        installed.append({"path": relative, "source": source.relative_to(PROJECT).as_posix(), "sha256": sha256(root / relative)})
    route_pref = "etc/apt/preferences.d/srrx-boot-route-a.pref"
    if (root / route_pref).is_file():
        installed.append({"path": route_pref, "source": "deployment/image/files/srrx-boot-route-a.pref", "sha256": sha256(root / route_pref)})
    left = sorted(p.name for p in lists.iterdir() if p.name not in ours and not p.name.endswith(".srrx-disabled")) if lists.is_dir() else []
    if left or os.path.lexists(root / "etc/apt/sources.list"):
        raise BuildError("apt source entries other than the SR-RX publications remain: " + ", ".join(left or ["etc/apt/sources.list"]))
    return {"installed": installed, "disabled": disabled, "removed": ["etc/apt/sources.list.d/" + n for n in removed],
            "keyring": {"path": SRRX_KEYRING, "present": (root / SRRX_KEYRING).is_file()}}


# systemd-tmpfiles-setup.service applies these on every boot: /data is its own partition (not mounted
# at this step) and the rest are API or runtime file systems.
TMPFILES_AT_BOOT = ("/data", "/run", "/tmp", "/dev", "/proc", "/sys")


def _colon_table(path):
    table = {}
    for line in (Path(path).read_text(errors="replace").splitlines() if Path(path).is_file() else []):
        parts = line.split(":")
        if len(parts) >= 4 and parts[0]:
            table[parts[0]] = parts
    return table


def system_accounts(root, stage_dir):
    """systemd-sysusers and systemd-tmpfiles --create of the staged SR-RX configuration, once, in the
    chroot of root A (software/DEPLOYMENT.md, «Системні файли»): deterministic and checked here instead
    of relying on systemd-sysusers.service at first boot (ConditionNeedsUpdate=/etc). Root B is an rsync
    copy, so every unit built from this golden image gets the same UIDs/GIDs. Returns the record of
    every system_files.SERVICE_ACCOUNTS and PACKAGE_ACCOUNTS name with its ids (None: absent)."""
    import deploy
    system = deploy.system_files()
    staged = load_json(Path(stage_dir) / "stage-files.json")["files"]
    sysusers = sorted("/" + p for p in staged if re.fullmatch(r"(usr/lib|etc)/sysusers\.d/[^/]+\.conf", p))
    tmpfiles = sorted("/" + p for p in staged if re.fullmatch(r"(usr/lib|etc)/tmpfiles\.d/[^/]+\.conf", p))
    if "/" + system.SYSUSERS not in sysusers or "/" + system.TMPFILES not in tmpfiles:
        raise BuildError("the controller bundle lacks the SR-RX sysusers.d/tmpfiles.d configuration")
    chroot(root, ["systemd-sysusers"] + sysusers)
    # A line that names an unknown user or group makes systemd-tmpfiles exit non-zero: the build stops.
    chroot(root, ["systemd-tmpfiles", "--create"] + ["--exclude-prefix=" + p for p in TMPFILES_AT_BOOT] + tmpfiles)
    passwd, group = _colon_table(Path(root) / "etc/passwd"), _colon_table(Path(root) / "etc/group")
    service, missing = {}, []
    for kind, name, *_ in system.SERVICE_ACCOUNTS:
        entry = {"kind": kind, "gid": int(group[name][2]) if name in group else None}
        if kind == "u":
            user = passwd.get(name)
            entry.update(uid=int(user[2]) if user else None, primary_gid=int(user[3]) if user else None,
                         shell=user[6] if user and len(user) > 6 else None)
        if None in entry.values():
            missing.append(name)
        service[name] = entry
    # primary_gid: gpsd has no group of its own (its postinst puts it in dialout).
    package = {name: {"uid": int(passwd[name][2]) if name in passwd else None, "gid": int(group[name][2]) if name in group else None,
                      "primary_gid": int(passwd[name][3]) if name in passwd else None}
               for name in sorted(system.PACKAGE_ACCOUNTS)}
    return {"sysusers": sysusers, "tmpfiles": tmpfiles, "tmpfiles_left_to_boot": list(TMPFILES_AT_BOOT),
            "service_accounts": service, "service_accounts_missing": missing, "package_accounts": package,
            # root/_chrony/gpsd are users, dialout a group only: absent means in neither table.
            "package_accounts_missing": sorted(n for n, ids in package.items() if ids["uid"] is None and ids["gid"] is None)}


def enable_units(root, recipe, route):
    units = dict(recipe["enable_common"]["units"], **recipe["routes"][route]["enable"])
    for unit in units:
        run(["systemctl", "--root", str(root), "enable", unit])
    root = Path(root)
    links = {u: sorted(p.relative_to(root).as_posix() for p in (root / "etc/systemd/system").glob("*/" + u)) for u in units}
    expected = {u: sorted("etc/systemd/system/" + d + "/" + u for d in dirs.split()) for u, dirs in units.items()}
    if links != expected:
        raise BuildError("unit enablement links differ from the recipe: " + json.dumps({"got": links, "want": expected}))
    return links


def copy_cache(cache, data_root, recipe):
    target = Path(data_root) / "srrx-cache"
    copied = []
    for art in load_json(LOCK)["artifacts"]:
        source = Path(cache) / art["cache_path"]
        dest = target / art["cache_path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        os.chmod(dest, 0o644)
        if sha256(dest) != art["sha256"]:
            raise BuildError("cache copy differs: " + art["id"])
        copied.append(art["cache_path"])
    return copied


def esp_inventory(esp):
    return [{"path": p.relative_to(esp).as_posix(), "size": p.stat().st_size, "sha256": sha256(p)}
            for p in sorted(Path(esp).rglob("*")) if p.is_file()]


def selftest(root, cmdline_sha, output):
    argv = [sys.executable, "-B", str(DEPLOYMENT / "selftest.py"), "offline", "--rootfs", str(root), "--profile", "controller",
            "--policy", str(POLICY), "--project", str(PROJECT), "--cmdline-sha256", cmdline_sha, "--output", str(output)]
    done = run(argv, check=False)
    report = load_json(output) if Path(output).is_file() else {}
    # Finding items (policy identifiers, never dpkg text) only for the (row, rule) pairs tagged per item.
    items, keys = {}, {(r, f) for r, f, _ in SELFTEST_ITEM_CLOSES_AT}
    for row in report.get("checks", []):
        for finding in row.get("findings", []) if row.get("status") in ("FAIL", "BLOCKED") else []:
            if (row.get("id"), finding.get("rule")) in keys and "item" in finding:
                items.setdefault(row["id"] + ":" + finding["rule"], set()).add(str(finding["item"]))
    return {"exit_code": done.returncode, "status": report.get("status"), "counts": report.get("counts"),
            "fail_or_blocked_rows": bootchain.fail_or_blocked_rows(report), "report_sha256": sha256(output) if Path(output).is_file() else None,
            "policy_status": report.get("policy_status"),
            "policy_blockers": sorted(b for b in report.get("blockers", []) if str(b).startswith("POLICY_")),
            "tagged_items": {key: sorted(found) for key, found in sorted(items.items())}}


# What closes each manifest blocker. "recipe": this recipe or CI must still fix it; "commissioning":
# a per-unit value written when the unit is commissioned; "bench:W-10": the Q6A bench gate;
# "bench:Phase0": the FastRPC/DSP/HTP matrix on the bench; "owner:key-ceremony": the owner's offline
# signing-key ceremony (deployment/repo/README.md); "owner:policy-review": the human review that may
# set receive-only-policy.json REVIEWED (build/09 РЕЦ-01). A tag never removes a blocker.
CLOSES_AT = ("recipe", "commissioning", "bench:W-10", "bench:Phase0", "owner:key-ceremony", "owner:policy-review")
BLOCKER_CLOSES_AT = (  # (blocker text prefix, id, tag); the selftest blocker is tagged per row and rule
    ("dt_overlays_missing", "dt_overlays_missing", "recipe"),
    ("dt_merge_not_the_ci_record", "dt_merge_not_the_ci_record", "recipe"),
    ("dt_not_booted", "dt_not_booted", "bench:W-10"),
    ("route_b_embloader_not_0.4", "route_b_embloader_not_0.4", "recipe"),
    ("unknown kernel-install plugins", "unknown_kernel_install_plugins", "recipe"),
    ("service_accounts_missing", "service_accounts_missing", "recipe"),
    ("package_accounts_missing", "package_accounts_missing", "recipe"),
    ("rsetup_first_boot_", "rsetup_first_boot", "recipe"),
    ("locked cache not on /data", "locked_cache_not_on_data", "recipe"),
    # W2 IMG-3: unit_interpreters replaces target_python_without_numpy (the image python3 still has no numpy).
    ("unit_interpreter_missing", "unit_interpreter_missing", "recipe"),
    ("unit_interpreter_without_numpy", "unit_interpreter_without_numpy", "recipe"),
    ("unit_interpreter_unclassified", "unit_interpreter_unclassified", "recipe"),
    ("hmi_venv_qt_offscreen_failed", "hmi_venv_qt_offscreen_failed", "recipe"),
    ("build_manifest_draft_blocked", "build_manifest_draft_blocked", "recipe"),
    ("apt_keyring_absent", "apt_keyring_absent", "owner:key-ceremony"),
    ("npu_payload_present", "npu_payload_present", "recipe"),
    ("mcu_firmware_manifest", "mcu_firmware_manifest", "recipe"),
)
SELFTEST_BLOCKER = "selftest root A "
SELFTEST_RULE_CLOSES_AT = {("RX-S2", "radio_off_binding_missing"): "commissioning",
                           # any present pin_only package without a passing version_rule waits for Phase 0
                           ("RX-01a", "pinned_package_present_unreviewed"): "bench:Phase0"}
SELFTEST_ITEM_CLOSES_AT = {  # (row, rule, finding item): tag, ahead of the (row, rule) tag
    # embloader's version is fixed by the boot recipe (recipe.json routes.B.embloader_version), not by
    # Phase 0: a present embloader outside its version_rule allow_only 0.4 is recipe drift
    ("RX-01a", "pinned_package_present_unreviewed", "embloader"): "recipe"}
SELFTEST_VERDICTS = ("FAIL", "BLOCKED", "OFFLINE_CHECKS_PASS")  # selftest.py run_offline; exit 0 only on a pass


def _selftest_closes_at(text, record):
    """Tags of the selftest blocker: "recipe" when the run left no usable verdict (no report, an
    unknown status or an exit code that disagrees with it), one per FAIL/BLOCKED (row, rule) or
    tagged finding item, and one per POLICY_* blocker of the verdict."""
    status = record["status"] if "status" in record else text[len(SELFTEST_BLOCKER):].split(":", 1)[0]
    exit_code = 0 if status == "OFFLINE_CHECKS_PASS" else 2
    no_report = (status not in SELFTEST_VERDICTS or ("report_sha256" in record and record["report_sha256"] is None)
                 or record.get("exit_code", exit_code) != exit_code)
    tags = [{"blocker": "selftest_root_a:no_report", "closes_at": "recipe"}] if no_report else []
    rows, items = record.get("fail_or_blocked_rows") or {}, record.get("tagged_items") or {}
    for row in sorted(rows):
        for rule in rows[row] or ["?"]:
            found = items.get(row + ":" + rule, [])
            tagged = [i for i in found if (row, rule, i) in SELFTEST_ITEM_CLOSES_AT]
            for item in tagged:
                tags.append({"blocker": "selftest_root_a:" + row + ":" + rule + ":" + item,
                             "closes_at": SELFTEST_ITEM_CLOSES_AT[(row, rule, item)]})
            if not found or len(tagged) < len(found):
                tags.append({"blocker": "selftest_root_a:" + row + ":" + rule,
                             "closes_at": SELFTEST_RULE_CLOSES_AT.get((row, rule), "recipe")})
    if not no_report and "policy_blockers" in record:
        policy = record["policy_blockers"]  # POLICY_NOT_REVIEWED, or POLICY_REVIEW_RECORD_* of a REVIEWED policy
    else:  # no verdict (or an older record): the status of the policy file the builder passed
        policy = [] if load_json(POLICY).get("status") == "REVIEWED" else ["POLICY_NOT_REVIEWED"]
    tags += [{"blocker": "selftest_root_a:" + str(b).lower(), "closes_at": "owner:policy-review"} for b in policy]
    if not tags:  # a verdict with no row and no policy blocker is still listed: the recipe must decide
        tags.append({"blocker": "selftest_root_a:verdict_" + str(status).lower(), "closes_at": "recipe"})
    return tags


def blocking_closes_at(blocking, selftest_report=None):
    """One {blocker, closes_at} per blocker, the selftest blocker one per (row, rule) plus its policy
    status; an unlisted blocker is tagged "recipe" (CI must still fix it), so nothing is hidden."""
    tags = []
    for text in blocking:
        if text.startswith(SELFTEST_BLOCKER):
            tags += _selftest_closes_at(text, selftest_report or {})
            continue
        found = next(((i, t) for prefix, i, t in BLOCKER_CLOSES_AT if text.startswith(prefix)), None)
        tags.append({"blocker": found[0] if found else text.split(":", 1)[0], "closes_at": found[1] if found else "recipe"})
    return tags


def closes_at_summary(tags):
    """{tag: [blocker ids]} in CLOSES_AT order, for the CI summary and the README."""
    return {tag: [t["blocker"] for t in tags if t["closes_at"] == tag] for tag in CLOSES_AT if any(t["closes_at"] == tag for t in tags)}


def npu_payload(root):
    """The golden image never carries the QNN SDK or QAIRT (owner install on the unit, never
    redistributed): installed packages and files matching the NPU globs, names only."""
    import fnmatch
    names = sorted({n.split(":", 1)[0] for n in _dpkg_status(root)})
    packages = sorted(n for n in names if any(fnmatch.fnmatchcase(n, g) for g in NPU_PAYLOAD_PACKAGES))
    files = sorted({f for pattern in NPU_PAYLOAD_FILES for f in _find(root, pattern, ("usr/lib", "usr/share", "lib/firmware", "opt"))})[:50]
    status = "absent" if not packages and not files else "PRESENT"
    return {"status": status, "why": "owner install on the unit from a verified deb (software/DEPLOYMENT.md, NPU/QNN); "
                                     "QAIRT and the QNN SDK are never redistributed (build/15, «Збирання образу»)",
            "package_globs": list(NPU_PAYLOAD_PACKAGES), "file_globs": list(NPU_PAYLOAD_FILES), "packages": packages, "files": files}


def mcu_firmware(root):
    """MCU firmware is flashed and verified from a bench host (tools/flash_mcu.py), never from the
    image; the image carries the pinned packages under /opt/srrx/firmware for audit only and records
    the SHA-256 of the staged firmware/dist/build-manifest.json it expects."""
    staged = Path(root) / "opt/srrx" / MCU_BUILD_MANIFEST
    repo = PROJECT / MCU_BUILD_MANIFEST
    record = {"flashing": "bench host only: tools/flash_mcu.py before installation; re-flashing is a service step with the case open "
                          "(BOOTSEL); the image never flashes the Pico or the IMU MCU",
              "build_manifest": "opt/srrx/" + MCU_BUILD_MANIFEST, "sha256": sha256(staged) if staged.is_file() else None,
              "repo_sha256": sha256(repo) if repo.is_file() else None}
    record["matches_repo"] = record["sha256"] is not None and record["sha256"] == record["repo_sha256"]
    return record


# ---------------------------------------------------------------- package closure (W2 IMG-2)

def _order(char):
    """dpkg lib/dpkg/version.c order(): '~' sorts before everything, letters by code, others after letters."""
    if char == "~":
        return -1
    if "0" <= char <= "9":
        return 0
    if ("a" <= char <= "z") or ("A" <= char <= "Z"):
        return ord(char)
    return ord(char) + 256


def _verrevcmp(a, b):
    """dpkg verrevcmp() of an upstream version or revision."""
    i = j = 0
    while i < len(a) or j < len(b):
        while (i < len(a) and not "0" <= a[i] <= "9") or (j < len(b) and not "0" <= b[j] <= "9"):
            ac = _order(a[i]) if i < len(a) else 0
            bc = _order(b[j]) if j < len(b) else 0
            if ac != bc:
                return ac - bc
            i, j = i + 1, j + 1
        while i < len(a) and a[i] == "0":
            i += 1
        while j < len(b) and b[j] == "0":
            j += 1
        first_diff = 0
        while i < len(a) and "0" <= a[i] <= "9" and j < len(b) and "0" <= b[j] <= "9":
            if not first_diff:
                first_diff = ord(a[i]) - ord(b[j])
            i, j = i + 1, j + 1
        if i < len(a) and "0" <= a[i] <= "9":
            return 1
        if j < len(b) and "0" <= b[j] <= "9":
            return -1
        if first_diff:
            return first_diff
    return 0


def _split_version(version):
    epoch, sep, rest = version.partition(":")
    if not sep:
        epoch, rest = "0", version
    upstream, sep, revision = rest.rpartition("-")
    if not sep:
        upstream, revision = rest, ""
    return int(epoch), upstream, revision


def deb_version_compare(a, b):
    """<0, 0 or >0 like `dpkg --compare-versions` (epoch, upstream version, Debian revision)."""
    ea, ua, ra = _split_version(a)
    eb, ub, rb = _split_version(b)
    if ea != eb:
        return ea - eb
    return _verrevcmp(ua, ub) or _verrevcmp(ra, rb)


def version_satisfies(version, op, wanted):
    if op is None:
        return True
    c = deb_version_compare(version, wanted)
    return {"<<": c < 0, "<=": c <= 0, "<": c <= 0, "=": c == 0, ">=": c >= 0, ">>": c > 0, ">": c >= 0}[op]


_RELATION = re.compile(r"([a-z0-9][a-z0-9+.-]*)(?::([a-z0-9-]+))?\s*(?:\(\s*(<<|<=|>=|>>|=|<|>)\s*([^\s)]+)\s*\))?\s*(?:\[[^\]]*\]\s*)?(?:<[^>]*>\s*)*\Z")


def parse_relations(text):
    """Depends-style field -> [[(name, arch qualifier, op, version), alternatives...], ...] (deb-control(5))."""
    groups = []
    for part in (text or "").replace("\n", " ").split(","):
        if not part.strip():
            continue
        group = []
        for alternative in part.split("|"):
            match = _RELATION.match(alternative.strip())
            if not match:
                raise BuildError("unparsable package relation: " + alternative.strip()[:120])
            group.append(match.groups())
        groups.append(group)
    return groups


def _relation_text(group):
    return " | ".join(n + ((":" + a) if a else "") + ((" (%s %s)" % (o, w)) if o else "") for n, a, o, w in group)


def _source(stanza):
    """(source package, source version) of a binary stanza ("Source: name (version)", default: itself)."""
    source = (stanza.get("source") or stanza["package"]).split()
    return source[0], source[1].strip("()") if len(source) > 1 else stanza["version"]


def _versions(by_name, name, suites):
    """[(version, suite, area, stanza)] of a package, newest first; a version belongs to the first suite
    (apt_snapshot.suites order) whose signed index lists it."""
    seen = {}
    for suite, area, stanza in by_name.get(name, ()):
        key = stanza["version"]
        if key not in seen or suites.index(suite) < suites.index(seen[key][1]):
            seen[key] = (key, suite, area, stanza)
    return sorted(seen.values(), key=functools.cmp_to_key(lambda x, y: deb_version_compare(y[0], x[0])))


def resolve_closure(stanzas, installed, lock, roots=CLOSURE_ROOTS):
    """The packages the image must add to r2 for roots, from the signed snapshot indices.

    stanzas: [(suite, area, {field: value})] of every binary-<arch> Packages index of the snapshot;
    installed: {package[:arch]: version}, the r2 dpkg status (image-facts.json root.packages).
    A dependency r2 already satisfies stays as it is. A missing one takes the version sources.lock.json
    binary_debs pins, else the newest snapshot version that satisfies it (apt's candidate). An r2 package
    built from the same source as a closure package at another version joins at the closure's source
    version (tzdata with tzdata-legacy). An r2 package that a closure package Conflicts with or Breaks,
    also through a virtual package it Provides, is removed. Installed relations are read from the
    snapshot stanza of the installed version (else the newest one): r2 versions older than the
    snapshot are an approximation, which the build's apt plan check settles."""
    snapshot = lock["apt_snapshot"]
    suites = list(snapshot["suites"])
    by_name = {}
    for suite, area, stanza in stanzas:
        if stanza.get("architecture") in (snapshot["architecture"], "all") and stanza.get("package") and stanza.get("version"):
            by_name.setdefault(stanza["package"], []).append((suite, area, stanza))
    r2 = {name.split(":", 1)[0]: version for name, version in installed.items()}
    locked = {}
    for component in lock["components"]:
        for deb in component.get("binary_debs") or []:
            locked.setdefault(deb["package"], {})[deb["version"]] = deb

    def approx(name, version):
        found = _versions(by_name, name, suites)
        return ([v for v in found if v[0] == version] or found or [None])[0]

    installed_stanzas = {name: approx(name, version) for name, version in r2.items()}
    installed_provides = {}
    for name, entry in installed_stanzas.items():
        for group in parse_relations(entry[3].get("provides")) if entry else []:
            for pname, _, _, pversion in group:
                installed_provides.setdefault(pname, []).append((name, pversion))
    selected, removed, issues = {}, {}, []

    def satisfied(name, op, wanted):
        version = selected[name]["version"] if name in selected else (None if name in removed else r2.get(name))
        if version is not None and version_satisfies(version, op, wanted):
            return True
        provided = [pv for sel in selected.values() for group in parse_relations(sel["stanza"].get("provides"))
                    for pn, _, _, pv in group if pn == name]
        provided += [pv for provider, pv in installed_provides.get(name, ()) if provider not in selected and provider not in removed]
        return any(op is None or (pv is not None and version_satisfies(pv, op, wanted)) for pv in provided)

    def choose(name, op=None, wanted=None):
        options = [v for v in _versions(by_name, name, suites) if version_satisfies(v[0], op, wanted)]
        return ([v for v in options if v[0] in locked.get(name, {})] or options or [None])[0]

    queue = [(name, "root (STACK.md:902, build/07 §1.2)", None, None) for name in sorted(roots)]
    while queue:
        name, reason, op, wanted = queue.pop(0)
        if name in selected:
            if not version_satisfies(selected[name]["version"], op, wanted):
                issues.append("%s %s does not satisfy %s" % (name, selected[name]["version"], reason))
            continue
        choice = choose(name, op, wanted)
        if choice is None:
            issues.append("no snapshot version of %s for %s" % (name, reason))
            continue
        version, suite, area, stanza = choice
        selected[name] = {"version": version, "suite": suite, "area": area, "stanza": stanza, "reason": reason}
        for field in ("pre-depends", "depends"):
            for group in parse_relations(stanza.get(field)):
                if any(satisfied(n, o, w) for n, _, o, w in group):
                    continue
                for n, _, o, w in group:
                    if choose(n, o, w) is not None:
                        queue.append((n, "%s of %s: %s (r2 has %s)" % (field.capitalize(), name, _relation_text(group),
                                                                     r2.get(n) or "none"), o, w))
                        break
                else:
                    issues.append("%s of %s %s satisfied neither by r2 nor by the snapshot: %s" % (field, name, version, _relation_text(group)))
        source = _source(stanza)
        for sibling, sibling_version in sorted(r2.items()):
            entry = installed_stanzas.get(sibling)
            if sibling in selected or not entry or _source(entry[3])[0] != source[0]:
                continue
            same = [v for v in _versions(by_name, sibling, suites) if _source(v[3]) == source]
            if same and same[0][0] != sibling_version:
                queue.append((sibling, "same source as %s (%s %s; r2 has %s)" % (name, source[0], source[1], sibling_version), "=", same[0][0]))
    for name, sel in sorted(selected.items()):
        for field in ("conflicts", "breaks"):
            for group in parse_relations(sel["stanza"].get(field)):
                for n, _, o, w in group:
                    if n != name and n not in selected and r2.get(n) is not None and version_satisfies(r2[n], o, w):
                        removed.setdefault(n, "%s of %s: %s" % (field.capitalize(), name, _relation_text([(n, None, o, w)])))
                    if o is None:
                        for provider, _ in installed_provides.get(n, ()):
                            if provider != name and provider not in selected:
                                removed.setdefault(provider, "%s of %s: %s, which %s provides" % (field.capitalize(), name, n, provider))
    provided_by_closure = {pn for sel in selected.values() for group in parse_relations(sel["stanza"].get("provides")) for pn, *_ in group}
    for name, version in sorted(r2.items()):
        entry = installed_stanzas.get(name)
        if name in selected or name in removed or not entry:
            continue
        for field in ("conflicts", "breaks"):
            for group in parse_relations(entry[3].get(field)):
                for n, _, o, w in group:
                    if (n in selected and version_satisfies(selected[n]["version"], o, w)) or (o is None and n in provided_by_closure):
                        issues.append("r2 %s %s %s %s, which the closure installs" % (name, version, field, n))
        for field in ("pre-depends", "depends"):
            for group in parse_relations(entry[3].get(field)):
                if any(n in removed for n, *_ in group) and not any(satisfied(n, o, w) for n, _, o, w in group):
                    issues.append("removing %s breaks %s of r2 %s: %s" % (",".join(n for n, *_ in group if n in removed), field, name,
                                                                           _relation_text(group)))
    packages = []
    for name in sorted(selected):
        sel, stanza = selected[name], selected[name]["stanza"]
        entry = {"package": name, "version": sel["version"], "architecture": stanza["architecture"], "filename": stanza["filename"],
                 "suite": sel["suite"], "sha256": stanza["sha256"], "size": int(stanza["size"]), "r2_version": r2.get(name),
                 "reason": sel["reason"]}
        pinned = locked.get(name, {}).get(sel["version"])
        if pinned and any(pinned[k] != entry[k] for k in ("architecture", "filename", "sha256", "size")):
            issues.append("snapshot %s %s differs from sources.lock.json binary_debs" % (name, sel["version"]))
        packages.append(entry)
    return {"packages": packages, "expected_removed": sorted(removed), "removed_because": dict(sorted(removed.items())), "issues": issues}


CLOSURE_DESCRIPTION = ("Packages the golden image adds to Radxa OS r2 (build_image.py step 8b): apt-get install --purge of exactly these "
                       "hash-locked debs of the pinned snapshot, with every apt source and preference disabled. chrony replaces r2's "
                       "systemd-timesyncd (Conflicts/Provides time-daemon) and needs tzdata-legacy; tzdata follows its source; gpsd needs "
                       "libgps30t64. Their postinst scripts create _chrony and gpsd. Generated by `build_image.py closure --resolve`; "
                       "never edited by hand.")
CLOSURE_METHOD = ("build_image.py closure --resolve: gpgv of each suite InRelease against the pinned archive key (fetch_sources.signed_release), "
                  "equal to sources.lock.json apt_snapshot.releases; the signed SHA256 list checks every binary-arm64 Packages.xz; "
                  "resolve_closure() against the r2 dpkg status of image-facts.json.")


def closure_document(resolved, lock, recipe, packages_total, resolved_on):
    snapshot = lock["apt_snapshot"]
    base = lock_artifacts(lock)[recipe["base_artifact"]]
    return {"schema_version": 1, "status": "CANDIDATE", "description": CLOSURE_DESCRIPTION,
            "snapshot": {k: snapshot[k] for k in ("archive", "timestamp", "architecture")},
            "suites": [dict(r) for r in snapshot["releases"]], "resolved_on": resolved_on, "method": CLOSURE_METHOD,
            "base": {"artifact": base["id"], "sha256": base["sha256"], "packages_total": packages_total},
            "roots": sorted(CLOSURE_ROOTS), "packages": resolved["packages"], "expected_removed": resolved["expected_removed"],
            "removed_because": resolved["removed_because"],
            "expected_accounts": sorted({a for accounts in CLOSURE_ROOTS.values() for a in accounts})}


def closure_issues(closure, lock):
    """Consistency of package-closure.json with sources.lock.json (host-tested; the build refuses any)."""
    snapshot, issues = lock["apt_snapshot"], []
    if closure.get("schema_version") != 1:
        issues.append("schema_version must be 1")
    if closure.get("snapshot") != {k: snapshot[k] for k in ("archive", "timestamp", "architecture")}:
        issues.append("snapshot differs from sources.lock.json apt_snapshot")
    if not (closure.get("snapshot", {}).get("archive", "") + "/").startswith(SNAPSHOT_URL):
        issues.append("archive is not " + SNAPSHOT_URL)
    if closure.get("suites") != snapshot["releases"]:
        issues.append("suites differ from sources.lock.json apt_snapshot.releases")
    packages = closure.get("packages") or []
    names = [p.get("package") for p in packages]
    if names != sorted(set(names)) or not names:
        issues.append("packages must be non-empty, unique and sorted by name")
    locked = {(d["package"], d["version"]): d for c in lock["components"] for d in c.get("binary_debs") or []}
    basenames = set()
    for p in packages:
        if tuple(p) != CLOSURE_PACKAGE_KEYS:
            issues.append("package entry keys: " + str(p.get("package")))
            continue
        if not re.fullmatch(r"[0-9a-f]{64}", p["sha256"]) or type(p["size"]) is not int or p["size"] <= 0:
            issues.append("sha256/size: " + p["package"])
        if not re.fullmatch(r"pool/(main|universe)/[a-z0-9]+/[a-z0-9][a-z0-9+.-]*/[A-Za-z0-9+.~_-]+\.deb", p["filename"]) \
                or Path(p["filename"]).name in basenames:
            issues.append("filename: " + p["package"])
        basenames.add(Path(p["filename"]).name)
        if p["suite"] not in snapshot["suites"] or p["architecture"] not in (snapshot["architecture"], "all"):
            issues.append("suite/architecture: " + p["package"])
        pinned = locked.get((p["package"], p["version"]))
        if pinned and any(pinned[k] != p[k] for k in ("architecture", "filename", "sha256", "size")):
            issues.append("differs from sources.lock.json binary_debs: " + p["package"])
    if closure.get("roots") != sorted(CLOSURE_ROOTS) or not set(CLOSURE_ROOTS) <= set(names):
        issues.append("roots must be " + ",".join(sorted(CLOSURE_ROOTS)) + " and in packages")
    if set(closure.get("expected_removed") or []) & set(names) or sorted(closure.get("removed_because") or {}) != closure.get("expected_removed"):
        issues.append("expected_removed must be outside packages and match removed_because")
    if closure.get("expected_accounts") != sorted({a for accounts in CLOSURE_ROOTS.values() for a in accounts}):
        issues.append("expected_accounts must be the accounts of the roots")
    return issues


def load_closure(path=CLOSURE, lock=None):
    closure = load_json(path)
    issues = closure_issues(closure, load_json(LOCK) if lock is None else lock)
    if issues:
        raise BuildError("package-closure.json: " + "; ".join(issues))
    return closure


def compare_closure(proposed, committed):
    """Keys of CLOSURE_COMPARED where a fresh resolution differs from the committed file."""
    return [k for k in CLOSURE_COMPARED if proposed.get(k) != committed.get(k)]


def fetch_closure(cache, closure=None):
    """Each closure deb from snapshot.ubuntu.com/ubuntu/<timestamp>/<filename>, accepted only with its SHA-256 and size."""
    closure = load_closure() if closure is None else closure
    base = closure["snapshot"]["archive"] + "/" + closure["snapshot"]["timestamp"] + "/"
    return {p["package"]: _download(base + p["filename"], Path(cache) / CLOSURE_CACHE / Path(p["filename"]).name, p["sha256"], p["size"],
                                    "closure " + p["package"]) for p in closure["packages"]}


def apt_local_options(parts_dir):
    """apt reads no source and no preference: only the debs on the command line and the dpkg status (apt.conf(5),
    Dir::Etc). dpkg keeps a conffile that is already there (the staged /etc/default/gpsd) instead of asking."""
    return ["-o", "Dir::Etc::SourceList=/dev/null", "-o", "Dir::Etc::SourceParts=" + parts_dir,
            "-o", "Dir::Etc::Preferences=/dev/null", "-o", "Dir::Etc::PreferencesParts=" + parts_dir,
            "-o", "Dpkg::Options::=--force-confdef", "-o", "Dpkg::Options::=--force-confold"]


_APT_ACTION = re.compile(r"^(Inst|Remv|Purg) (\S+)(?: \[([^\]]*)\])?(?: \((\S+))?", re.M)


def apt_simulation(text):
    """{"install": {package: version}, "remove": [package]} of `apt-get -s` output (Inst/Remv/Purg lines)."""
    plan = {"install": {}, "remove": set()}
    for action, name, _, version in _APT_ACTION.findall(text):
        name = name.split(":", 1)[0]
        if action == "Inst":
            plan["install"][name] = version
        else:
            plan["remove"].add(name)
    return {"install": dict(sorted(plan["install"].items())), "remove": sorted(plan["remove"])}


def closure_plan_issues(plan, closure):
    want = {p["package"]: p["version"] for p in closure["packages"]}
    issues = []
    if plan["install"] != want:
        issues.append("apt would install %s, the closure lists %s" % (json.dumps(plan["install"], sort_keys=True), json.dumps(want, sort_keys=True)))
    if plan["remove"] != sorted(closure["expected_removed"]):
        issues.append("apt would remove %s, the closure expects %s" % (plan["remove"], sorted(closure["expected_removed"])))
    return issues


def status_changes(before, after):
    """{package: (version before, version after)} of every package whose installed version changed (None: absent)."""
    b = {n.split(":", 1)[0]: v for n, v in before.items()}
    a = {n.split(":", 1)[0]: v for n, v in after.items()}
    return {n: (b.get(n), a.get(n)) for n in sorted(set(b) | set(a)) if b.get(n) != a.get(n)}


def closure_status_issues(changes, closure):
    issues = []
    for p in closure["packages"]:
        if changes.get(p["package"]) != (p["r2_version"], p["version"]):
            issues.append("%s: %r, expected %r" % (p["package"], changes.get(p["package"]), (p["r2_version"], p["version"])))
    for name in closure["expected_removed"]:
        if not changes.get(name) or changes[name][1] is not None:
            issues.append("%s was not removed: %r" % (name, changes.get(name)))
    others = sorted(set(changes) - {p["package"] for p in closure["packages"]} - set(closure["expected_removed"]))
    if others:
        issues.append("packages outside the closure changed: " + json.dumps({n: changes[n] for n in others}))
    return issues


def install_closure(root, cache, closure):
    """Step 8b: apt-get install --purge of the closure debs in the chroot (policy-rc.d 101 starts nothing);
    the simulated plan and the dpkg status change must both be exactly the closure."""
    root = Path(root)
    before = _dpkg_status(root)
    plain = {n.split(":", 1)[0]: v for n, v in before.items()}
    drift = {p["package"]: plain.get(p["package"]) for p in closure["packages"] if plain.get(p["package"]) != p["r2_version"]}
    drift.update({n: None for n in closure["expected_removed"] if n not in plain})
    if drift:
        raise BuildError("the r2 root differs from the dpkg status the closure was resolved against: " + json.dumps(drift))
    target = root / CLOSURE_CHROOT_DIR
    if target.exists():
        shutil.rmtree(target)
    (target / "parts.d").mkdir(parents=True)
    names = []
    for p in closure["packages"]:
        source = Path(cache) / CLOSURE_CACHE / Path(p["filename"]).name
        dest = target / source.name
        shutil.copyfile(source, dest)
        os.chmod(dest, 0o644)
        if dest.stat().st_size != p["size"] or sha256(dest) != p["sha256"]:
            raise BuildError("closure deb differs from package-closure.json: " + p["package"])
        names.append("/" + CLOSURE_CHROOT_DIR + "/" + source.name)
    for directory in (target, target / "parts.d"):
        os.chmod(directory, 0o755)
    argv = ["apt-get", "install", "-y", "-q", "--no-install-recommends", "--purge"] + apt_local_options("/" + CLOSURE_CHROOT_DIR + "/parts.d")
    simulated = chroot(root, argv[:2] + ["-s"] + argv[2:] + names, extra_env=CLOSURE_ENV)
    plan = apt_simulation(simulated.stdout)
    issues = closure_plan_issues(plan, closure)
    if issues:
        raise BuildError("apt plan of the package closure: " + "; ".join(issues) + "\n" + simulated.stdout[-2000:])
    done = chroot(root, argv + names, extra_env=CLOSURE_ENV)
    shutil.rmtree(target)
    changes = status_changes(before, _dpkg_status(root))
    issues = closure_status_issues(changes, closure)
    if issues:
        raise BuildError("dpkg status after the package closure: " + "; ".join(issues))
    passwd = _colon_table(root / "etc/passwd")
    accounts = {n: {"uid": int(passwd[n][2]) if n in passwd else None, "primary_gid": int(passwd[n][3]) if n in passwd else None}
                for n in closure["expected_accounts"]}
    missing = sorted(n for n, ids in accounts.items() if ids["uid"] is None)
    if missing:
        raise BuildError("the closure's maintainer scripts did not create " + ", ".join(missing))
    return {"file_sha256": sha256(CLOSURE), "snapshot": closure["snapshot"]["timestamp"],
            "installed": {p["package"]: p["version"] for p in closure["packages"]},
            "deb_sha256": {p["package"]: p["sha256"] for p in closure["packages"]},
            "removed": sorted(n for n, (_, after) in changes.items() if after is None),
            "upgraded": {n: {"from": b, "to": a} for n, (b, a) in changes.items() if b and a},
            "accounts": accounts, "apt_plan": plan, "apt_tail": done.stdout[-1500:]}


def install_chrony_conf(root):
    """Replace chrony's own /etc/chrony/chrony.conf (ucf copy with the Ubuntu pools) by the offline SR-RX file,
    then let the image's chronyd parse it (-p prints every directive, conf.d included, and exits)."""
    import deploy
    system = deploy.system_files()
    root = Path(root)
    target = root / system.CHRONY_CONF
    if not target.parent.is_dir():
        raise BuildError("chrony is not installed: /etc/chrony is missing")
    replaced = sha256(target) if target.is_file() else None
    write_text(target, system.chrony_conf(), 0o644)
    parsed = chroot(root, ["chronyd", "-p", "-f", "/" + system.CHRONY_CONF])
    directives = [line.split()[0].lower() for line in parsed.stdout.splitlines() if line.split()]
    network = sorted(set(directives) & set(system.CHRONY_NETWORK_DIRECTIVES))
    if network or not directives:
        raise BuildError("chronyd -p of the SR-RX chrony.conf: " + (",".join(network) or "no directive") + "\n" + parsed.stdout[-800:])
    return {"path": system.CHRONY_CONF, "sha256": sha256(target), "source": "deployment/system/system_files.py chrony_conf()",
            "replaced_sha256": replaced, "chronyd_p_directives": directives, "network_directives": network}


def staged_gnss_mode(root):
    """The GNSS mode of the staged /etc/default/gpsd (deploy.py stage --gnss; the image stages the default)."""
    import deploy
    system = deploy.system_files()
    path = Path(root) / system.GPSD_DEFAULTS
    text = path.read_text(encoding="utf-8") if path.is_file() else None
    return next((mode for mode in deploy.GNSS_MODES if text == system.gpsd_defaults(mode)), None)


def snapshot_stanzas(lock, keyring, work):
    """Every binary-<arch> Packages stanza of the pinned snapshot: gpgv of each suite InRelease by the pinned
    key (fetch_sources.signed_release) must give the lock record, and each index its signed SHA-256."""
    import deploy
    import fetch_sources
    snapshot = lock["apt_snapshot"]
    recorded = {r["suite"]: r for r in snapshot["releases"]}
    stanzas = []
    Path(work).mkdir(parents=True, exist_ok=True)
    for suite in snapshot["suites"]:
        release, files = fetch_sources.signed_release(snapshot, suite, keyring, work)
        if recorded.get(suite) != release:
            raise BuildError("InRelease differs from sources.lock.json: " + suite)
        for area in snapshot["areas"]:
            _, text = fetch_sources.index(snapshot, suite, area + "/binary-" + snapshot["architecture"] + "/Packages.xz", files, work)
            stanzas += [(suite, area, s) for s in deploy.deb822(text, suite + " " + area + " Packages")]
    return stanzas


def closure_resolve(facts_path, keyring, work, write=None):
    """CI helper (network): the closure the signed snapshot gives for the r2 facts, compared with the committed file."""
    lock, recipe, facts = load_json(LOCK), load_json(RECIPE), load_json(facts_path)
    resolved = resolve_closure(snapshot_stanzas(lock, keyring, work), facts["root"]["packages"], lock)
    proposed = closure_document(resolved, lock, recipe, facts["root"]["packages_total"], datetime.date.today().isoformat())
    if write:
        dump(write, proposed)
    committed = load_json(CLOSURE) if CLOSURE.is_file() else {}
    differs = compare_closure(proposed, committed)
    issues = resolved["issues"] + closure_issues(proposed, lock)
    return {"status": "CLOSURE_MATCHES_COMMITTED" if not differs and not issues else "CLOSURE_DIFFERS",
            "differs": differs, "issues": issues, "dpkg_holds": facts["root"].get("dpkg_holds"), "proposed": proposed}


# ---------------------------------------------------------------- Python venvs (W2 IMG-3)

_LOCK_LINE = re.compile(r"([A-Za-z0-9][A-Za-z0-9_.-]*)==(\S+) --hash=sha256:([0-9a-f]{64})\Z")


def normalized(name):
    """PEP 503 normalized distribution name (PySide6_Essentials -> pyside6-essentials)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def lock_lines(path):
    """[(name, version, sha256, line)] of a hashed requirements file; comments and blank lines are skipped."""
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        match = _LOCK_LINE.fullmatch(line)
        if match is None:
            raise BuildError("unparsable lock line in " + Path(path).name + ": " + line[:80])
        rows.append(match.groups() + (line,))
    return rows


def venv_lock_issues(lock, guest_lines, wheels):
    """Why a venv lock is not a verbatim, dependency-closed subset of the guest lock whose every wheel the
    wheelhouse manifest records with that version and SHA-256 (host-testable; the build refuses any issue).
    wheels: {normalized name: wheelhouse-manifest.json entry}."""
    names = {normalized(name) for name, _, _, _ in lock}
    issues = [] if len(names) == len(lock) else ["duplicate distribution names"]
    for name, version, digest, line in lock:
        if line not in guest_lines:
            issues.append(name + ": line differs from deployment/linux_lab/wheelhouse-requirements.txt")
        wheel = wheels.get(normalized(name))
        if wheel is None or wheel["version"] != version or wheel["sha256"] != digest or not wheel.get("hash_verified"):
            issues.append(name + ": wheelhouse-manifest.json has no hash-verified wheel " + version + " with this SHA-256")
            continue
        if not wheel["url"].startswith(WHEEL_URL):
            issues.append(name + ": wheel URL is not on files.pythonhosted.org")
        for requirement in wheel["requires_dist"]:
            if ";" in requirement:
                continue  # environment-marked: python < 3.11 or an extra
            dependency = normalized(re.split(r"[\s=<>!~(\[]", requirement.strip(), maxsplit=1)[0])
            if dependency not in names:
                issues.append(name + " needs " + requirement)
    return issues


def venv_plan(manifest=None):
    """{"pip": bootstrap wheel, "venvs": {venv: [wheel entries]}} from the two locks and the wheelhouse manifest;
    raises BuildError on any venv_lock_issues."""
    manifest = load_json(WHEELHOUSE) if manifest is None else manifest
    wheels = {normalized(w["name"]): w for w in manifest["wheels"]}
    guest = lock_lines(GUEST_LOCK)
    guest_lines = {row[3] for row in guest}
    pip = [row for row in guest if normalized(row[0]) == PIP_BOOTSTRAP]
    issues = venv_lock_issues(pip, guest_lines, wheels) if len(pip) == 1 else ["the guest lock has no single pip line"]
    plan = {"pip": wheels.get(PIP_BOOTSTRAP), "venvs": {}}
    for venv, spec in VENVS.items():
        lock = lock_lines(PROJECT / spec["lock"])
        issues += [spec["lock"] + ": " + issue for issue in venv_lock_issues(lock, guest_lines, wheels)]
        if PIP_BOOTSTRAP in {normalized(row[0]) for row in lock}:
            issues.append(spec["lock"] + ": pip is a build tool here, never a venv package")
        plan["venvs"][venv] = [wheels[normalized(row[0])] for row in lock if normalized(row[0]) in wheels]
    if issues:
        raise BuildError("venv locks: " + "; ".join(issues))
    return plan


def plan_wheels(plan):
    """Every distinct wheel of a venv_plan (the pip bootstrap first), by file name."""
    out = {plan["pip"]["filename"]: plan["pip"]}
    for wheels in plan["venvs"].values():
        out.update((w["filename"], w) for w in wheels)
    return out


def fetch_wheels(cache, plan=None):
    """Each venv wheel from its wheelhouse-manifest.json URL, accepted only with its SHA-256 and size."""
    plan = venv_plan() if plan is None else plan
    return {name: _download(w["url"], Path(cache) / WHEEL_CACHE / name, w["sha256"], w["size_bytes"], "wheel " + w["name"])
            for name, w in plan_wheels(plan).items()}


def project_version():
    import tomllib
    return tomllib.loads((PROJECT / "software/pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def expected_freeze(lock_path, version):
    """{normalized name: version} a venv must hold: the lock pins plus the project (pip is never installed)."""
    want = {normalized(name): pin for name, pin, _, _ in lock_lines(lock_path)}
    want[normalized(PROJECT_DIST)] = version
    return want


def freeze_issues(freeze, want):
    """Differences between a venv's distributions ([[name, version], ...]) and expected_freeze."""
    have = {}
    for name, version in freeze:
        if normalized(name) in have:
            return ["distribution listed twice: " + name]
        have[normalized(name)] = version
    extra = sorted(set(have) - set(want))
    missing = sorted(set(want) - set(have))
    wrong = sorted(n for n in set(have) & set(want) if have[n] != want[n])
    return (["not in the lock: " + ", ".join("%s %s" % (n, have[n]) for n in extra)] if extra else []) + \
           (["missing: " + ", ".join(missing)] if missing else []) + \
           (["versions differ: " + ", ".join("%s %s != %s" % (n, have[n], want[n]) for n in wrong)] if wrong else [])


def _site_packages(venv):
    found = sorted(Path(venv).glob("lib/python3*/site-packages"))
    if len(found) != 1:
        raise BuildError("expected one site-packages in " + str(venv) + ", found " + str(len(found)))
    return found[0]


def package_copy_issues(installed, staged):
    """The venv's srrx package must be the staged /opt/srrx/software/srrx byte for byte (file names and SHA-256)."""
    def tree(path):
        return {p.relative_to(path).as_posix(): sha256(p) for p in sorted(Path(path).rglob("*")) if p.is_file()}
    have, want = tree(installed), tree(staged)
    if have == want:
        return []
    differs = sorted(set(have) ^ set(want)) + sorted(k for k in set(have) & set(want) if have[k] != want[k])
    return ["srrx copy differs from the staged tree: " + ", ".join(differs[:10])]


def unrecorded_bytecode(venv):
    """__pycache__ files of a venv that no installed distribution's RECORD lists, i.e. written by the build
    (--no-compile and -B everywhere) rather than shipped in a wheel (pyside6_essentials 6.12.0 ships
    PySide6/support/__pycache__/*.cpython-312.pyc)."""
    site = _site_packages(venv)
    recorded = set()
    for record in site.glob("*.dist-info/RECORD"):
        for line in record.read_text(encoding="utf-8").splitlines():
            if line.strip():
                recorded.add(posixpath.normpath(line.rsplit(",", 2)[0]))
    found = []
    for path in sorted(Path(venv).rglob("*")):
        if path.is_file() and "__pycache__" in path.parts:
            rel = path.relative_to(site).as_posix() if path.is_relative_to(site) else None
            if rel is None or rel not in recorded:
                found.append(path.relative_to(venv).as_posix())
    return found


def tree_record(path):
    """deploy.build_inventory of a venv (the walk verify-build compares) and its SHA-256 over the sorted file map."""
    import deploy
    files, modules = deploy.build_inventory(path)
    size = sum(p.stat().st_size for p in Path(path).rglob("*") if p.is_file() and not p.is_symlink())
    return {"tree_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), "files": len(files),
            "bytes": size, "so_modules": len(modules)}


def _chroot_json(root, argv, extra_env=None):
    """(returncode, last stdout line parsed as JSON or None, output tail) of a bounded chroot command."""
    done = chroot(root, argv, extra_env=extra_env, check=False)
    lines = (done.stdout or "").strip().splitlines()
    try:
        value = json.loads(lines[-1]) if lines else None
    except ValueError:
        value = None
    return done.returncode, value, ((done.stdout or "")[-600:] + (done.stderr or "")[-600:]).strip()


def build_venvs(root, cache, plan=None):
    """Step 11b in the root A chroot (W2 IMG-3). The wheels and the project copy are removed afterwards. A venv that is
    not exactly its lock (pip check, freeze, a __pycache__, a srrx copy other than the staged tree) stops the build;
    the offscreen PySide6 check of the HMI venv is recorded and becomes a blocker in build()."""
    root = Path(root)
    plan = venv_plan() if plan is None else plan
    wheel_dir, build_copy, home = root / WHEELS_CHROOT_DIR, root / BUILD_COPY, root / VENV_HOME.lstrip("/")
    for path in (wheel_dir, build_copy, home):
        if path.exists():
            shutil.rmtree(path)
    wheel_dir.mkdir(parents=True)
    for name, wheel in plan_wheels(plan).items():
        dest = wheel_dir / name
        shutil.copyfile(Path(cache) / WHEEL_CACHE / name, dest)
        os.chmod(dest, 0o644)
        if dest.stat().st_size != wheel["size_bytes"] or sha256(dest) != wheel["sha256"]:
            raise BuildError("venv wheel differs from wheelhouse-manifest.json: " + name)
    os.chmod(wheel_dir, 0o755)
    shutil.copytree(root / "opt/srrx/software", build_copy, ignore=shutil.ignore_patterns("__pycache__", "build", "*.egg-info"))
    (home / "run").mkdir(parents=True, mode=0o700)
    pip_env = dict(VENV_ENV, PYTHONPATH="/" + WHEELS_CHROOT_DIR + "/" + plan["pip"]["filename"])
    version = project_version()
    record = {"pip_bootstrap": {"wheel": plan["pip"]["filename"], "sha256": plan["pip"]["sha256"], "installed_in_venv": False},
              "wheelhouse_manifest_sha256": sha256(WHEELHOUSE), "venvs": {}}
    try:
        for venv, spec in VENVS.items():
            target = root / venv
            if os.path.lexists(target):
                raise BuildError("/" + venv + " already exists before the venv step (the controller bundle never carries one)")
            chroot(root, ["/usr/bin/python3", "-P", "-B", "-m", "venv", "--copies", "--without-pip", "/" + venv], extra_env=VENV_ENV)
            python = "/" + venv + "/bin/python3"
            pip = [python, "-P", "-B", "-m", "pip"] + PIP_OPTIONS
            install = pip + ["install", "--root-user-action=ignore", "--no-index", "--no-cache-dir", "--no-compile"]
            chroot(root, install + ["--find-links", "/" + WHEELS_CHROOT_DIR, "--only-binary", ":all:", "--require-hashes",
                                    "-r", "/opt/srrx/" + spec["lock"]], extra_env=pip_env)
            chroot(root, install + ["--no-deps", "--no-build-isolation", "/" + BUILD_COPY], extra_env=pip_env)
            check = chroot(root, pip + ["check"], extra_env=pip_env, check=False)
            code, freeze, tail = _chroot_json(root, [python, "-I", "-B", "-c", FREEZE_CODE], VENV_ENV)
            issues = [] if check.returncode == 0 else ["pip check: " + ((check.stdout or "") + (check.stderr or ""))[-600:]]
            issues += freeze_issues(freeze or [], expected_freeze(PROJECT / spec["lock"], version)) if code == 0 else ["freeze: " + tail]
            cached = unrecorded_bytecode(target)
            if cached:
                issues.append("byte-compiled files outside every RECORD: " + ", ".join(cached[:5]))
            issues += package_copy_issues(_site_packages(target) / "srrx", root / "opt/srrx/software/srrx")
            if issues:
                raise BuildError("venv /" + venv + ": " + "; ".join(issues))
            code, numpy, tail = _chroot_json(root, [python, "-I", "-B", "-c", NUMPY_CODE], VENV_ENV)
            entry = {"lock": spec["lock"], "lock_sha256": sha256(PROJECT / spec["lock"]), "python": python,
                     "pyvenv_cfg": (target / "pyvenv.cfg").read_text(encoding="utf-8").splitlines(),
                     "freeze": [[name, pin] for name, pin in sorted(freeze, key=lambda row: normalized(row[0]))],
                     "freeze_matches_lock": True, "pip_check": (check.stdout or "").strip()[-300:],
                     "numpy": (numpy or {}).get("numpy"), "python_version": (numpy or {}).get("python")}
            if spec["qt"]:
                plugins = _site_packages(target) / "PySide6/Qt/plugins/platforms"
                code, qt, tail = _chroot_json(root, [python, "-I", "-B", "-c", QT_CODE], dict(VENV_ENV, **QT_ENV))
                entry["qt_offscreen"] = {"status": "OK" if code == 0 and qt and qt.get("platform") == "offscreen" else "FAILED",
                                         "result": qt, "exit_code": code, "tail": None if code == 0 else tail[-800:],
                                         "env": dict(QT_ENV)}
                entry["qt_platform_plugins"] = sorted(p.name for p in plugins.iterdir()) if plugins.is_dir() else None
            entry.update(tree_record(target))
            record["venvs"]["/" + venv] = entry
    finally:
        for path in (wheel_dir, build_copy, home):
            shutil.rmtree(path, ignore_errors=True)
    return record


def unit_exec_words(text):
    """[(key, words)] of the Exec*= lines of one unit fragment or drop-in (SR-RX units use no line continuation)."""
    out = []
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() in EXEC_KEYS and value.split():
            out.append((key.strip(), value.split()))
    return out


def exec_interpreter(words):
    """The python3 interpreter an Exec line starts: its first word, or the command behind env(1) NAME=value; else None."""
    chain = [words[0].lstrip(EXEC_PREFIXES)]
    if chain[0].rsplit("/", 1)[-1] == "env":
        rest = words[1:]
        while rest and "=" in rest[0] and not rest[0].startswith(("-", "/")):
            rest = rest[1:]
        if rest and not rest[0].startswith("-"):
            chain.append(rest[0])
    found = [word for word in chain if PYTHON_NAME.fullmatch(word.rsplit("/", 1)[-1])]
    return found[-1] if found else None


def python_units(root):
    """{unit: {"files", "interpreters", "commands"}} of each SR-RX unit (name srrx*: fragment or <unit>.d/*.conf drop-in,
    system or user) whose Exec lines start python3. A masked unit (symlink) runs nothing and is skipped."""
    root = Path(root)
    units = {}
    for directory in UNIT_SEARCH:
        base = root / directory
        for path in sorted(base.iterdir()) if base.is_dir() and not base.is_symlink() else []:
            if not path.name.startswith("srrx") or path.is_symlink():
                continue
            if path.is_file():
                pairs = [(path, path.name)]
            elif path.is_dir() and path.name.endswith(".d"):
                pairs = [(p, path.name[:-2]) for p in sorted(path.glob("*.conf")) if p.is_file() and not p.is_symlink()]
            else:
                continue
            for file, unit in pairs:
                for key, words in unit_exec_words(file.read_text(encoding="utf-8", errors="replace")):
                    interpreter = exec_interpreter(words)
                    if interpreter is None:
                        continue
                    entry = units.setdefault(unit, {"files": [], "interpreters": [], "commands": []})
                    rel = file.relative_to(root).as_posix()
                    if rel not in entry["files"]:
                        entry["files"].append(rel)
                    if interpreter not in entry["interpreters"]:
                        entry["interpreters"].append(interpreter)
                    module = words[words.index("-m") + 1] if "-m" in words[:-1] else None
                    entry["commands"].append({"key": key, "interpreter": interpreter, "module": module})
    return units


def unit_interpreter_findings(units, probes, classes):
    """(per-unit record, blockers) of python_units against the interpreter probes ({path: {"present", "numpy"}}) and
    recipe.json unit_interpreters (numpy: the unit imports NumPy; stdlib: it needs none). Host-testable."""
    record, missing, without, unclassified = {}, [], [], []
    for unit, entry in sorted(units.items()):
        needs = "numpy" if unit in classes["numpy"] else "stdlib" if unit in classes["stdlib"] else None
        found = {path: probes.get(path) or {"present": False, "numpy": None} for path in entry["interpreters"]}
        record[unit] = dict(entry, needs=needs, why=(classes.get(needs) or {}).get(unit), interpreter_probe=found)
        if needs is None:
            unclassified.append(unit)
        for path, probe in found.items():
            if not probe["present"]:
                missing.append("%s (%s)" % (unit, path))
            elif needs == "numpy" and not probe.get("numpy"):
                without.append("%s (%s)" % (unit, path))
    # Listed but absent (srrx-ab-commit.service on Route A): recorded only; the host test keeps the lists exact.
    stale = sorted((set(classes["numpy"]) | set(classes["stdlib"])) - set(units))
    blockers = []
    if missing:
        blockers.append("unit_interpreter_missing: " + ", ".join(missing))
    if without:
        blockers.append("unit_interpreter_without_numpy: " + ", ".join(without) + " (recipe.json unit_interpreters.numpy)")
    if unclassified:
        blockers.append("unit_interpreter_unclassified: " + ", ".join(unclassified) + " (neither list of recipe.json unit_interpreters)")
    return {"units": record, "classified_not_staged": stale}, blockers


def unit_interpreters(root, recipe):
    """Step 11b: each SR-RX python3 unit's interpreters probed in the root A chroot (present; NumPy imports), then
    unit_interpreter_findings. Replaces the target_python_numpy blocker (the image python3 still has no NumPy)."""
    units = python_units(root)
    probes = {}
    for path in sorted({p for entry in units.values() for p in entry["interpreters"]}):
        code, value, tail = _chroot_json(root, [path, "-I", "-B", "-c", NUMPY_CODE], VENV_ENV)
        probes[path] = {"present": code == 0 and value is not None, "numpy": (value or {}).get("numpy"),
                        "python": (value or {}).get("python"), "exit_code": code}
    found, blockers = unit_interpreter_findings(units, probes, recipe["unit_interpreters"])
    return dict(found, probes=probes, source=recipe["unit_interpreters"]["source"]), blockers


def build_manifest_draft(root, out):
    """The OPEN build-manifest draft of root A's /opt/srrx after the venvs (deployment/system/build_manifest.py, the
    deploy.build_inventory walk verify-build compares), next to image-manifest.json. Never PASS or REVIEWED: a reviewer
    attaches the evidence and sets REVIEWED by hand (software/DEPLOYMENT.md)."""
    if str(DEPLOYMENT / "system") not in sys.path:
        sys.path.insert(0, str(DEPLOYMENT / "system"))
    import build_manifest
    target = Path(out) / BUILD_MANIFEST_DRAFT
    try:
        draft = build_manifest.generate(Path(root) / "opt/srrx")
    except (OSError, ValueError) as exc:  # deploy.DeploymentError: a refusal of verify-build's own walk
        return {"status": "BLOCKED", "error": str(exc)[:600], "path": None}
    target.write_text(json.dumps(draft, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return {"status": draft["status"], "path": BUILD_MANIFEST_DRAFT, "sha256": sha256(target), "prefix": "/opt/srrx",
            "files": len(draft["files"]), "allowed_modules": len(draft["allowed_modules"]),
            "evidence": {name: draft[name]["status"] for name in ("source_audit", "tx_negative_tests")},
            "next": "review, attach PASS evidence, set REVIEWED by hand (software/DEPLOYMENT.md)"}


# ---------------------------------------------------------------- build

def build(cache, work, out, route="A", dt_profile="lab", lime=True, seed=None, data_bytes=None,
          allow_unmerged_dtb=False, copy_locked_cache=True, keep_base=False):
    require_builder()
    started = utc_now()
    recipe, layout = load_json(RECIPE), layoutlib.load()
    work, out = Path(work).resolve(), Path(out).resolve()
    for directory in (work, out):
        refuse_block_path(directory)
        directory.mkdir(parents=True, exist_ok=True)
    LOG.path = out / "build.log"
    image = new_regular_file(out / ("srrx-golden-route%s.img" % route), out)
    ids = layoutlib.identifiers(layout, seed)
    kver = recipe["kernel_version"]
    manifest = {"schema_version": 1, "status": "BUILDING", "started_at": started, "route": route, "dt_profile": dt_profile,
                "lime_build": lime, "kernel_version": kver, "hardware_ready": False,
                "bench_gates_open": ["W-01", "W-02", "W-03", "W-08", "W-09", "W-10"],
                "publication": "PRIVATE ONLY: contains Radxa OS r2 and Qualcomm firmware/QNN content; never publish (build/15-rishennia-komplektu.md)",
                "bitwise_reproducible": "not claimed: file content is bound by the hashes below; timestamps, inode order and random seeds differ between builds",
                "identifiers": ids, "blocking": [], "steps": LOG.steps}
    mounts, keep = Mounts(), []
    loop = base_loop = base_mounts = None
    try:
        fetched = fetch(cache)
        stage_dir, bundle_path, staged = stage_bundle(work)
        LOG.step("inputs", "DONE", artifacts=fetched["artifacts"], bundle_sha256=staged["bundle"]["sha256"],
                 stage_files=staged["stage"]["files"])
        manifest["inputs"] = {"locked_artifacts": {a["id"]: a["sha256"] for a in load_json(LOCK)["artifacts"]},
                              "sources_lock_sha256": sha256(LOCK), "recipe_sha256": sha256(RECIPE), "package_closure_sha256": sha256(CLOSURE),
                              "layout_sha256": sha256(layoutlib.LAYOUT), "controller_bundle": staged,
                              "wheelhouse_manifest_sha256": sha256(WHEELHOUSE),
                              "venv_locks_sha256": {spec["lock"]: sha256(PROJECT / spec["lock"]) for spec in VENVS.values()}}
        base = facts(cache, work, out / "image-facts.json", keep_mounted=keep)
        base_mounts, base_loop, base_root, base_esp = keep
        LOG.step("base-facts", "DONE", base_cmdline=base["base_cmdline_status"], rescue=base["rescue"]["status"])
        if base["base_cmdline_status"] != "VALID":
            raise BuildError("observed r2 /etc/kernel/cmdline is not usable: " + base["base_cmdline_status"])
        if base["rescue"]["status"] != "IDENTIFIED":
            raise BuildError("r2 rescue entry (6.18.2-3) not identified on the base ESP: " + json.dumps(base["rescue"]))
        kernel_tree, kconfig = kernel_deb_config(cache, recipe, work)
        quota = False  # partition-layout.json "quota": TBD, enabled on the unit (the builder kernel may lack quota_v2)
        loop, devices, geo = create_disk(image, layout, ids, data_bytes, quota=quota)
        disk = check_disk(loop, devices, layout, ids, geo)
        if disk["issues"]:
            raise BuildError("new disk check failed: " + "; ".join(disk["issues"]))
        LOG.step("disk", "DONE", total_bytes=geo["total_bytes"], quota_enabled=quota)
        manifest["geometry"] = geo
        manifest["data_quota"] = {"status": layout["quota"]["status"], "image_feature": None,
                                  "locked_kernel": {k: kconfig.get(k) for k in ("CONFIG_QUOTA", "CONFIG_QFMT_V2", "CONFIG_QUOTACTL")}}
        root_a = work / "mnt/root_a"
        mounts.mount(devices["root_a"], root_a, "ext4")
        run(["rsync", "-aHAXxS", "--numeric-ids", str(base_root) + "/", str(root_a) + "/"])
        mounts.mount(devices["esp"], root_a / "boot/efi", "vfat", "umask=0077")
        run(["rsync", "-rtx", "--modify-window=2", str(base_esp) + "/", str(root_a / "boot/efi") + "/"])
        base_mounts.umount_all()
        base_loop.detach()
        base_loop = base_mounts = None
        if not keep_base:
            (work / "base.raw").unlink()
        LOG.step("root-a-copy", "DONE", used_bytes=os.statvfs(root_a).f_frsize * (os.statvfs(root_a).f_blocks - os.statvfs(root_a).f_bfree))
        partitions = {devices[role]: ["by-partuuid/" + ids["partuuid"][role]] + (["by-uuid/" + ids["fs_uuid"][role]] if role in ids["fs_uuid"] else [])
                      for role in layoutlib.ROLES}
        chroot_api(mounts, root_a, partitions)
        policy_rc(root_a, True)
        LOG.step("chroot", "DONE")
        count = extract_bundle(bundle_path, root_a, stage_dir)
        LOG.step("bundle", "DONE", files=count)
        dtb = build_dtbs(root_a, kernel_tree, recipe, kver)
        if not (dtb["lab"]["merged"] and dtb["field"]["merged"]):
            manifest["blocking"].append("dt_overlays_missing: lab.dtb/field.dtb are the unmerged package DTB (IMG-05)")
            if not allow_unmerged_dtb:
                raise BuildError("lab/field overlays absent (IMG-05); rerun with --allow-unmerged-dtb only for a CI candidate")
        else:
            differs = [p for p in ("lab", "field") if dtb[p].get("dt_manifest") != "MATCH"]
            if differs:
                manifest["blocking"].append("dt_merge_not_the_ci_record: " + ", ".join(p + ".dtb " + dtb[p]["dt_manifest"] for p in differs)
                                            + " against deployment/system/dt/dt-manifest.json")
            # Merged and compared in CI only; the booted tree is bench W-10 (fdt_check.py --reference).
            manifest["blocking"].append("dt_not_booted: lab.dtb/field.dtb are CI merge-checked, not booted on a Q6A (W-10 OPEN)")
        LOG.step("dtb", "DONE", lab_merged=dtb["lab"]["merged"], field_merged=dtb["field"]["merged"])
        manifest["dtb"] = dtb
        route_recipe = recipe["routes"][route]
        boot_detail = {}
        if route == "A":
            if dpkg_installed(root_a, "sdboot-is-embloader"):
                chroot(root_a, ["dpkg", "--purge", "sdboot-is-embloader"])
            boot_detail["sdboot_is_embloader_purged"] = dpkg_installed(root_a, "sdboot-is-embloader") is None
            chroot(root_a, ["bootctl", "install", "--esp-path=/boot/efi", "--no-variables", "--make-entry-directory=no",
                            "--entry-token=literal:srrx"])
            boot_detail["bootctl"] = esp_inventory(root_a / "boot/efi/EFI")
        else:
            version = dpkg_installed(root_a, "embloader")
            boot_detail["embloader_version"] = version
            if not version or not version.startswith(route_recipe["embloader_version"]):
                manifest["blocking"].append("route_b_embloader_not_0.4: r2 has embloader " + str(version) + "; a locked 0.4 deb is IMG-08")
        LOG.step("bootloader", "DONE", **{k: v for k, v in boot_detail.items() if k != "bootctl"})
        manifest["bootloader"] = boot_detail
        config = boot_config(layout, ids, route, dt_profile, lime, kver, base["base_cmdline_without_root"], base["rescue"])
        chain = install_boot_chain(root_a, route, recipe)
        if chain["unknown_kernel_install_plugins"]:
            manifest["blocking"].append("unknown kernel-install plugins need review: " + ",".join(chain["unknown_kernel_install_plugins"]))
        cmdline_sha = {"A": write_slot_files(root_a, config, layout, ids, "A")}
        LOG.step("boot-config", "DONE", **chain)
        debs_dir = root_a / "var/cache/srrx-image"
        debs_dir.mkdir(parents=True, exist_ok=True)
        artifacts = lock_artifacts()
        names = []
        for art_id in recipe["kernel_debs_install"]["artifacts"]:
            shutil.copyfile(Path(cache) / artifacts[art_id]["cache_path"], debs_dir / artifacts[art_id]["name"])
            names.append("/var/cache/srrx-image/" + artifacts[art_id]["name"])
        extra = {"SRRX_ALLOW_UNMERGED_DTB": "1"} if allow_unmerged_dtb else {}
        dpkg = chroot(root_a, ["dpkg", "-i"] + names, extra_env=extra)
        shutil.rmtree(debs_dir)
        status = {n: dpkg_installed(root_a, n) for n in recipe["kernel_debs_install"]["artifacts"]}
        if any(v != "6.18.2-4" for v in status.values()):
            raise BuildError("locked kernel debs not installed at 6.18.2-4: " + json.dumps(status))
        entry_a = sorted(p.name for p in (root_a / "boot/efi/loader/entries").glob("labA*.conf"))
        if not entry_a:
            # Debian kernel hooks call kernel-install only when systemd-boot is detected; run it explicitly.
            chroot(root_a, ["kernel-install", "add", kver, "/boot/vmlinuz-" + kver, "/boot/initrd.img-" + kver], extra_env=extra)
            entry_a = sorted(p.name for p in (root_a / "boot/efi/loader/entries").glob("labA*.conf"))
        LOG.step("kernel", "DONE", packages=status, slot_a_entry=entry_a, dpkg_tail=dpkg.stdout[-600:])
        manifest["kernel"] = {"packages": status, "slot_a_plugin_entry": entry_a,
                              "cache_only": sorted(set(recipe["kernel_artifacts"]) - set(recipe["kernel_debs_install"]["artifacts"])),
                              "why_cache_only": recipe["kernel_debs_install"]["source"]}
        closure = load_closure()
        manifest["package_closure"] = install_closure(root_a, cache, closure)
        manifest["package_closure"]["chrony_conf"] = install_chrony_conf(root_a)
        manifest["package_closure"]["gnss_mode"] = staged_gnss_mode(root_a)
        LOG.step("closure", "DONE", installed=manifest["package_closure"]["installed"], removed=manifest["package_closure"]["removed"],
                 accounts=manifest["package_closure"]["accounts"], gnss_mode=manifest["package_closure"]["gnss_mode"])
        manifest["accounts"] = system_accounts(root_a, stage_dir)
        if manifest["accounts"]["service_accounts_missing"]:
            manifest["blocking"].append("service_accounts_missing: " + ", ".join(manifest["accounts"]["service_accounts_missing"])
                                        + " (systemd-sysusers did not create them)")
        if manifest["accounts"]["package_accounts_missing"]:
            manifest["blocking"].append("package_accounts_missing: " + ", ".join(manifest["accounts"]["package_accounts_missing"])
                                        + " (neither r2 nor the package closure, step 8b, created them)")
        LOG.step("accounts", "DONE", service=len(manifest["accounts"]["service_accounts"]),
                 missing=manifest["accounts"]["service_accounts_missing"] + manifest["accounts"]["package_accounts_missing"])
        manifest["hardening"] = hardening(root_a, recipe, route)
        manifest["apt_sources"] = manifest["hardening"].pop("apt_sources")
        if not manifest["apt_sources"]["keyring"]["present"]:
            manifest["blocking"].append("apt_keyring_absent: both SR-RX sources are Signed-By /" + SRRX_KEYRING + ", the public key of the "
                                        "owner's offline key ceremony (deployment/repo/README.md); until it is installed apt reads no source")
        LOG.step("hardening", "DONE", held=len(manifest["hardening"]["held"]), masked=manifest["hardening"]["masked"],
                 apt_sources=[e["path"] for e in manifest["apt_sources"]["installed"]],
                 apt_disabled=[e["path"] for e in manifest["apt_sources"]["disabled"]])
        manifest["enabled_units"] = enable_units(root_a, recipe, route)
        manifest["not_enabled"] = recipe["not_enabled"]
        manifest["npu_payload"] = npu_payload(root_a)
        if manifest["npu_payload"]["status"] != "absent":  # a package or a loose file: either one is a payload
            manifest["blocking"].append("npu_payload_present: " + ", ".join(manifest["npu_payload"]["packages"]
                                                                             + manifest["npu_payload"]["files"])
                                        + " (the golden image never carries the QNN SDK or QAIRT)")
        manifest["mcu_firmware"] = mcu_firmware(root_a)
        if not manifest["mcu_firmware"]["matches_repo"]:
            manifest["blocking"].append("mcu_firmware_manifest: the staged " + manifest["mcu_firmware"]["build_manifest"]
                                        + " is missing or differs from the tree")
        first_boot = base.get("rsetup_first_boot")
        rows, unhandled = first_boot_review(first_boot, recipe, root_a)
        manifest["rsetup_first_boot"] = {"before_txt_sha256": (first_boot or {}).get("sha256"), "commands": rows}
        manifest["blocking"] += unhandled
        LOG.step("enable", "DONE")
        manifest["venvs"] = build_venvs(root_a, cache)
        qt = manifest["venvs"]["venvs"]["/opt/srrx/venv"]["qt_offscreen"]
        if qt["status"] != "OK":
            manifest["blocking"].append("hmi_venv_qt_offscreen_failed: QT_QPA_PLATFORM=offscreen QApplication in /opt/srrx/venv: "
                                        + str(qt["tail"] or qt["result"])[-300:])
        manifest["unit_interpreters"], blockers = unit_interpreters(root_a, recipe)
        manifest["blocking"] += blockers
        manifest["build_manifest_draft"] = build_manifest_draft(root_a, out)
        if manifest["build_manifest_draft"]["status"] != "OPEN":
            manifest["blocking"].append("build_manifest_draft_blocked: deployment/system/build_manifest.py refused /opt/srrx: "
                                        + manifest["build_manifest_draft"]["error"][-300:])
        LOG.step("venvs", "DONE", venvs={v: {"numpy": e["numpy"], "files": e["files"], "tree_sha256": e["tree_sha256"]}
                                         for v, e in manifest["venvs"]["venvs"].items()},
                 qt=qt["status"], unit_interpreter_blockers=blockers, build_manifest_draft=manifest["build_manifest_draft"]["status"])
        data = work / "mnt/data"
        mounts.mount(devices["data"], data, "ext4")
        for name in layout["partitions"][3]["directories"]:
            (data / name).mkdir(exist_ok=True)
        (root_a / "srv/srrx-cache").mkdir(parents=True, exist_ok=True)
        (root_a / "data").mkdir(exist_ok=True)
        manifest["data_cache"] = copy_cache(cache, data, recipe) if copy_locked_cache else "not copied (--no-cache-copy)"
        if not copy_locked_cache:
            manifest["blocking"].append("locked cache not on /data: release_guard verify_cache would fail")
        mounts.umount_under(data)
        LOG.step("data", "DONE")
        policy_rc(root_a, False)
        mounts.umount_under(root_a / "tmp")
        for sub in ("run", "sys", "proc", "dev"):
            mounts.umount_under(root_a / sub)
        manifest["selftest_root_a"] = selftest(root_a, cmdline_sha["A"], out / "selftest-root-a.json")
        manifest["blocking"].append("selftest root A " + str(manifest["selftest_root_a"]["status"]) + ": "
                                    + json.dumps(manifest["selftest_root_a"]["fail_or_blocked_rows"], sort_keys=True))
        LOG.step("selftest", "DONE", report=manifest["selftest_root_a"])
        # A fact since W2 IMG-3, no blocker: the image python3 has no numpy, and each unit that imports it runs a
        # venv interpreter (unit_interpreters above); the QEMU live selftest runs under /opt/srrx/passes-venv.
        manifest["target_python_numpy"] = (root_a / "usr/lib/python3/dist-packages/numpy/__init__.py").is_file()
        mounts.umount_under(root_a / "boot/efi")
        root_b = work / "mnt/root_b"
        mounts.mount(devices["root_b"], root_b, "ext4")
        run(["rsync", "-aHAXxS", "--numeric-ids", str(root_a) + "/", str(root_b) + "/"])
        cmdline_sha["B"] = write_slot_files(root_b, config, layout, ids, "B")
        mounts.mount(devices["esp"], root_b / "boot/efi", "vfat", "umask=0077")
        chroot_api(mounts, root_b, partitions)
        chroot(root_b, ["kernel-install", "add", kver, "/boot/vmlinuz-" + kver, "/boot/initrd.img-" + kver], extra_env=extra)
        for sub in ("tmp", "run", "sys", "proc", "dev"):
            mounts.umount_under(root_b / sub)
        LOG.step("root-b", "DONE", slot_b_entry=sorted(p.name for p in (root_b / "boot/efi/loader/entries").glob("labB*.conf")))
        golden = bootchain.golden_entries(root_b / "boot/efi", root_b / "etc/srrx/boot.json")
        manifest["entries"] = golden
        # bootctl install writes loader/random-seed; one golden image goes to many units, so no unit
        # may inherit it. systemd-boot-random-seed.service writes a fresh one on the first boot.
        random_seed = root_b / "boot/efi/loader/random-seed"
        manifest["esp_random_seed"] = "removed from the golden image" if random_seed.exists() else "absent"
        if random_seed.exists():
            random_seed.unlink()
        manifest["esp"] = esp_inventory(root_b / "boot/efi")
        manifest["boot_config"] = config
        manifest["cmdline_sha256"] = cmdline_sha
        LOG.step("entries", "DONE", **golden)
        mounts.umount_all()
        checks = {}
        for role in layoutlib.ROLES:
            argv = ["fsck.vfat", "-n", devices[role]] if role == "esp" else ["e2fsck", "-fn", devices[role]]
            checks[role] = run(argv, check=False).returncode
        disk = check_disk(loop, devices, layout, ids, geo)
        forced, manifest["journals"] = journal_ranges(devices, geo)
        loop.detach()
        loop = None
        manifest["filesystem_checks"] = checks
        manifest["disk_check"] = disk["issues"]
        if any(checks.values()) or disk["issues"]:
            raise BuildError("final filesystem or GPT check failed: " + json.dumps({"fsck": checks, "disk": disk["issues"]}))
        import recovery_kit
        # Journal bytes that SEEK_DATA reports as holes, measured before make_map reads them: ext4
        # reports an unwritten extent as data once its pages are in the page cache (CI 2026-11-06),
        # so the plain map was not even deterministic.
        holes = sum(n for _, n in recovery_kit.uncovered(recovery_kit.data_extents(image)[1], forced))
        extent_map = recovery_kit.make_map(image, layout_sector=layout["sector_size"], forced=forced)
        # Assertion of the map itself: every journal block is written by recovery_kit.py write.
        left = recovery_kit.uncovered(extent_map["extents"], forced)
        if left:
            raise BuildError("extent map leaves ext4 journal blocks unwritten: " + json.dumps(left[:5]))
        dump(out / (image.name + ".map.json"), extent_map)
        LOG.step("verify", "DONE", data_bytes=extent_map["data_bytes"], extents=len(extent_map["extents"]),
                 journal_bytes=sum(f["length"] for f in forced), journal_bytes_in_file_holes=holes)
        manifest.update(status="CANDIDATE_IMAGE_BUILT", finished_at=utc_now(), image={"name": image.name, "bytes": image.stat().st_size,
                        "map_sha256": sha256(out / (image.name + ".map.json")), "data_bytes": extent_map["data_bytes"],
                        "journal_bytes_forced": sum(f["length"] for f in forced), "journal_bytes_in_file_holes": holes})
        return manifest
    except BaseException as exc:
        manifest.update(status="BLOCKED", error=str(exc)[-4000:], finished_at=utc_now())
        raise
    finally:
        mounts.umount_all()
        if base_mounts:
            base_mounts.umount_all()
        if base_loop:
            base_loop.detach()
        if loop:
            loop.detach()
        manifest["blocking_closes_at"] = blocking_closes_at(manifest["blocking"], manifest.get("selftest_root_a"))
        manifest["blocking_by_closes_at"] = closes_at_summary(manifest["blocking_closes_at"])
        dump(out / "image-manifest.json", manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="op", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--route", choices=("A", "B"), default="A")
    p = sub.add_parser("fetch")
    p.add_argument("--cache", type=Path, required=True)
    p = sub.add_parser("facts")
    p.add_argument("--cache", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("blank")
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--test-sizes", action="store_true", help="CI round trip: small partitions, same code path")
    p = sub.add_parser("build")
    p.add_argument("--cache", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--route", choices=("A", "B"), default="A")
    p.add_argument("--dt-profile", choices=("lab", "field"), default="lab")
    p.add_argument("--no-lime", action="store_true", help="fallback build without Lime: no isolcpus/pcie_aspm line")
    p.add_argument("--uuid-seed", help="per-unit identifier seed (default: the layout seed)")
    p.add_argument("--data-bytes", type=int, help="compact /data size in the image file (grown on the UFS after the write)")
    p.add_argument("--allow-unmerged-dtb", action="store_true", help="CI candidate only: package DTB without the IMG-05 overlays")
    p.add_argument("--no-cache-copy", action="store_true")
    p.add_argument("--keep-base", action="store_true")
    p = sub.add_parser("closure", help="package-closure.json: --check (offline, against the lock) or --resolve (CI, network)")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--resolve", action="store_true")
    p.add_argument("--facts", type=Path, help="--resolve: image-facts.json of the locked r2 image")
    p.add_argument("--keyring", type=Path, help="--resolve: keyring holding the pinned archive key")
    p.add_argument("--work", type=Path, help="--resolve: directory for the downloaded InRelease and indices")
    p.add_argument("--write", type=Path, help="--resolve: also write the proposed package-closure.json here")
    p = sub.add_parser("venvs", help="W2 IMG-3: --check the venv locks against the guest lock and the wheelhouse manifest (offline)")
    p.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    try:
        if args.op == "plan":
            result = plan(args.route)
        elif args.op == "closure":
            if args.check:
                closure = load_closure()
                result = {"status": "CLOSURE_CONSISTENT_WITH_LOCK", "packages": {p["package"]: p["version"] for p in closure["packages"]},
                          "expected_removed": closure["expected_removed"], "expected_accounts": closure["expected_accounts"]}
            else:
                if not (args.facts and args.keyring and args.work):
                    raise ValueError("--resolve needs --facts, --keyring and --work")
                result = closure_resolve(args.facts, args.keyring, args.work, args.write)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return 0 if result["status"] == "CLOSURE_MATCHES_COMMITTED" else 2
        elif args.op == "venvs":
            wheel_plan = venv_plan()
            result = {"status": "VENV_LOCKS_CONSISTENT", "pip_bootstrap": wheel_plan["pip"]["filename"],
                      "venvs": {"/" + v: [w["filename"] for w in wheels] for v, wheels in wheel_plan["venvs"].items()}}
        elif args.op == "fetch":
            result = fetch(args.cache)
        elif args.op == "facts":
            require_builder()
            result = facts(args.cache, args.work, args.output)
            result = {"status": "FACTS_RECORDED", "output": str(args.output), "base_cmdline_status": result["base_cmdline_status"],
                      "rescue": result["rescue"], "partitions": result["partitions"]}
        elif args.op == "blank":
            result = blank(args.work, args.output, args.test_sizes)
        else:
            result = build(args.cache, args.work, args.out, args.route, args.dt_profile, not args.no_lime, args.uuid_seed,
                           args.data_bytes, args.allow_unmerged_dtb, not args.no_cache_copy, args.keep_base)
            result = {k: result[k] for k in ("status", "route", "image", "blocking", "blocking_by_closes_at", "hardware_ready")}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("status") not in ("BLOCKED",) else 2
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
