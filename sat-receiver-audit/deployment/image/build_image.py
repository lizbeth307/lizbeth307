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

The result is a CANDIDATE: hardware_ready is always false, bench gates W-01/W-02/W-03/W-08/W-09/W-10
stay OPEN, and the image contains Radxa OS and Qualcomm material that must not be published.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
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
               "CONFIG_SERIAL_AMBA_PL011_CONSOLE", "CONFIG_EFI", "CONFIG_EFI_STUB", "CONFIG_EXT4_FS", "CONFIG_VFAT_FS", "CONFIG_NLS_CP437",
               "CONFIG_NLS_ISO8859_1", "CONFIG_QUOTA", "CONFIG_QFMT_V2", "CONFIG_QUOTACTL", "CONFIG_CGROUP_BPF", "CONFIG_PPS_CLIENT_GPIO",
               "CONFIG_BLK_DEV_LOOP", "CONFIG_RTC_DRV_PL031", "CONFIG_DRM_VIRTIO_GPU", "CONFIG_HW_RANDOM_VIRTIO", "CONFIG_ARM_SMMU_V3")
INTEREST = re.compile(r"(linux-(image|headers|modules|firmware)|systemd|embloader|sdboot|radxa|rsetup|u-boot|edk2|fastrpc|qcom|qnn|qairt|"
                      r"mesa|libdrm|task-|aic8800|unattended|brltty|modemmanager|gdm3|greetd|labwc|python3$|python3\.12|dkms|gcc|initramfs|"
                      r"util-linux|e2fsprogs|dosfstools|chrony|gpsd|network-manager|openssh|wpasupplicant|bluez)")


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
        print(line, flush=True)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")

    def step(self, step_id, status, **detail):
        self.steps.append(dict(id=step_id, status=status, **detail))
        self.write("STEP " + step_id + " " + status + (" " + json.dumps(detail, ensure_ascii=False)[:400] if detail else ""))


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
    for tool in ("losetup", "sfdisk", "mkfs.vfat", "mkfs.ext4", "e2fsck", "fsck.vfat", "rsync", "chroot", "xz", "dpkg-deb", "blkid", "systemctl"):
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


def fetch(cache, ids=None):
    """Download locked artifacts into cache_path; size and SHA-256 are checked before the rename."""
    cache = Path(cache)
    artifacts = lock_artifacts()
    ids = list(artifacts) if ids is None else ids
    done = {}
    for art_id in ids:
        art = artifacts[art_id]
        target = cache / art["cache_path"]
        if target.is_file() and target.stat().st_size == art["size"] and sha256(target) == art["sha256"]:
            done[art_id] = "PRESENT"
            continue
        if not art["url"].startswith("https://github.com/"):
            raise BuildError("locked artifact URL is not a GitHub release asset: " + art_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_name(target.name + ".part")
        digest, size = hashlib.sha256(), 0
        LOG.write("fetch " + art["url"])
        request = urllib.request.Request(art["url"], headers={"User-Agent": "sr-rx-image-builder"})
        with urllib.request.urlopen(request, timeout=120) as response, open(part, "wb") as out:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                digest.update(chunk)
                size += len(chunk)
                if size > art["size"]:
                    raise BuildError("download exceeds the locked size: " + art_id)
                out.write(chunk)
        if size != art["size"] or digest.hexdigest() != art["sha256"]:
            part.unlink()
            raise BuildError("downloaded bytes differ from the lock: " + art_id)
        os.replace(part, target)
        done[art_id] = "FETCHED"
    import deploy
    verified = deploy.verify_cache(cache, components=[])
    return {"status": "LOCKED_ARTIFACTS_VERIFIED", "artifacts": done, "verify_cache": verified}


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


def minimal_dev(mounts, root):
    """tmpfs /dev with the character nodes package scripts need; no host block devices."""
    dev = Path(root) / "dev"
    mounts.mount("tmpfs", dev, "tmpfs", "mode=0755,nosuid")
    for name, major, minor in (("null", 1, 3), ("zero", 1, 5), ("full", 1, 7), ("random", 1, 8), ("urandom", 1, 9), ("tty", 5, 0)):
        os.mknod(dev / name, 0o666 | stat.S_IFCHR, os.makedev(major, minor))
    for name, target in (("fd", "/proc/self/fd"), ("stdin", "/proc/self/fd/0"), ("stdout", "/proc/self/fd/1"),
                         ("stderr", "/proc/self/fd/2"), ("ptmx", "pts/ptmx")):
        os.symlink(target, dev / name)
    mounts.mount("devpts", dev / "pts", "devpts", "newinstance,ptmxmode=0666,mode=0620")
    mounts.mount("tmpfs", dev / "shm", "tmpfs", "mode=1777,nosuid,nodev")


def chroot_api(mounts, root):
    minimal_dev(mounts, root)
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
    return {"wants": wants, "default_target": os.readlink(default) if default.is_symlink() else None,
            "interesting_units": interesting, "masked": masked}


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
        "packages": packages, "diversions": _diversions(root),
        "apt_sources_list_d": _listing(root / "etc/apt/sources.list.d"),
        "apt_sources_urls": sorted({u for p in [root / "etc/apt/sources.list", *sorted((root / "etc/apt/sources.list.d").glob("*"))]
                                    if p.is_file() for u in re.findall(r"https?://[^\s\"']+", p.read_text(errors="replace"))}),
        "apt_preferences_d": _listing(root / "etc/apt/preferences.d"),
        "units": _units(root), "accounts": _accounts(root),
        "machine_id": "missing" if machine_id is None else ("empty" if not machine_id.strip() else ("uninitialized" if machine_id.strip() == "uninitialized" else "set")),
        "hostname": (_text(root / "etc/hostname") or "").strip(),
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
    ("dtb", "package DTB from the locked linux-image deb; lab.dtb/field.dtb via fdtoverlay when the IMG-05 overlays exist, else the unmerged package DTB marked merged=false"),
    ("bootloader", "Route A: dpkg --purge sdboot-is-embloader, bootctl install --no-variables, embloader pinned -1; Route B: embloader kept (0.4 required)"),
    ("boot-config", "/etc/srrx/boot.json, /etc/srrx/slot, /etc/kernel/cmdline, tries, install.conf layout=other, 90-srrx-bls.install, boot-check unit (Route B: initramfs write-back and commit unit)"),
    ("kernel", "dpkg -i the five locked 6.18.2-4 debs before any apt run; the plugin writes the slot A entry and ESP files"),
    ("hardening", "apt-mark hold, purge unattended-upgrades/brltty, masks (apt/fwupd timers, ModemManager, sleep targets, rsetup.service), PPA lists removed, default-password accounts locked, empty machine-id"),
    ("enable", "srrx-radio-off.service and srrx-boot-check.service (Route B also srrx-ab-commit.service); srrx.service is not enabled (IMG-06)"),
    ("data", "/etc/fstab of slot A, /data directories, the locked cache copied to /data/srrx-cache (read-only bind at /srv/srrx-cache)"),
    ("selftest", "deployment/selftest.py offline --profile controller on root A (policy DRAFT: BLOCKED expected)"),
    ("root-b", "rsync root A to root B, slot B fstab/cmdline/slot file, kernel-install add in a root B chroot (slot B entry and ESP files)"),
    ("entries", "golden entries: labA (newest) and labB blessed, labA-rescue/labB-rescue with the r2 kernel, loader.conf; foreign r2 entries removed"),
    ("verify", "sfdisk --verify, e2fsck -fn, fsck.vfat -n, image-manifest.json, extent map for recovery_kit.py"),
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
    finally:
        loop.detach()
    report.update(status="BLANK_IMAGE_OK" if not report["issues"] else "BLOCKED", image=str(output), geometry=geo, identifiers=ids,
                  layout_status=layout["status"])
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


def build_dtbs(root, kernel_tree, recipe, kver):
    """lab.dtb/field.dtb under /usr/lib/srrx/dtb/<kver>: fdtoverlay of the IMG-05 overlays when present."""
    found = sorted(Path(kernel_tree).rglob(recipe["dtb_name"]))
    if len(found) != 1:
        raise BuildError("expected exactly one " + recipe["dtb_name"] + " in the locked linux-image deb, found " + str(len(found)))
    base = found[0]
    store = Path(root) / "usr/lib/srrx/dtb" / kver
    store.mkdir(parents=True, exist_ok=True)
    record = {"base_dtb": "/" + base.relative_to(kernel_tree).as_posix(), "base_dtb_sha256": sha256(base)}
    for profile in ("lab", "field"):
        overlay = next((PROJECT / p for p in recipe["dt_overlays"][profile] if (PROJECT / p).is_file()), None)
        target = store / (profile + ".dtb")
        if overlay is None:
            shutil.copyfile(base, target)
            record[profile] = {"merged": False, "overlay": None, "why": "IMG-05 overlay source absent in this tree"}
        else:
            dtbo = Path(kernel_tree).parent / (profile + ".dtbo")
            run(["dtc", "-@", "-I", "dts", "-O", "dtb", "-o", dtbo, overlay])
            run(["fdtoverlay", "-i", base, "-o", target, dtbo])
            record[profile] = {"merged": True, "overlay": overlay.relative_to(PROJECT).as_posix(), "overlay_sha256": sha256(overlay)}
        record[profile]["sha256"] = sha256(target)
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
    return {"installed": installed, "unknown_kernel_install_plugins": unknown}


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
    masked = []
    for unit in recipe["mask"]["units"]:
        run(["systemctl", "--root", str(root), "mask", unit])
        masked.append(unit)
    policy = load_json(POLICY)
    tokens = policy["apt"]["forbidden_list_name_tokens"]
    origins = policy["apt_forbidden_origins"]
    removed = []
    for path in sorted((root / "etc/apt/sources.list.d").glob("*")):
        text = path.read_text(errors="replace") if path.is_file() else ""
        if any(t in path.name for t in tokens) or any(o in text for o in origins):
            path.unlink()
            removed.append(path.name)
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
    return {"held": hold, "hold_names_not_installed": missing, "purged": purge, "masked": masked,
            "removed_apt_lists": removed, "locked_accounts": locked, "machine_id_before": previous}


def enable_units(root, recipe, route):
    units = dict(recipe["enable_common"]["units"], **recipe["routes"][route]["enable"])
    for unit in units:
        run(["systemctl", "--root", str(root), "enable", unit])
    root = Path(root)
    links = {u: sorted(str(p.relative_to(root)) for p in (root / "etc/systemd/system").glob("*/" + u)) for u in units}
    if any(not v for v in links.values()):
        raise BuildError("unit enablement produced no links: " + json.dumps(links))
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
    rows = report.get("rows") or report.get("results") or []
    summary = {}
    for row in rows if isinstance(rows, list) else []:
        summary[row.get("status", "?")] = summary.get(row.get("status", "?"), 0) + 1
    return {"exit_code": done.returncode, "status": report.get("status"), "row_status_counts": summary,
            "report_sha256": sha256(output) if Path(output).is_file() else None}


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
                              "sources_lock_sha256": sha256(LOCK), "recipe_sha256": sha256(RECIPE),
                              "layout_sha256": sha256(layoutlib.LAYOUT), "controller_bundle": staged}
        base = facts(cache, work, out / "image-facts.json", keep_mounted=keep)
        base_mounts, base_loop, base_root, base_esp = keep
        LOG.step("base-facts", "DONE", base_cmdline=base["base_cmdline_status"], rescue=base["rescue"]["status"])
        if base["base_cmdline_status"] != "VALID":
            raise BuildError("observed r2 /etc/kernel/cmdline is not usable: " + base["base_cmdline_status"])
        if base["rescue"]["status"] != "IDENTIFIED":
            raise BuildError("r2 rescue entry (6.18.2-3) not identified on the base ESP: " + json.dumps(base["rescue"]))
        kernel_tree, kconfig = kernel_deb_config(cache, recipe, work)
        quota = kconfig.get("CONFIG_QUOTA") == "y"
        loop, devices, geo = create_disk(image, layout, ids, data_bytes, quota=quota)
        disk = check_disk(loop, devices, layout, ids, geo)
        if disk["issues"]:
            raise BuildError("new disk check failed: " + "; ".join(disk["issues"]))
        LOG.step("disk", "DONE", total_bytes=geo["total_bytes"], quota_enabled=quota)
        manifest["geometry"], manifest["data_quota"] = geo, ("prjquota feature" if quota else "not enabled: CONFIG_QUOTA is not y in the locked kernel config")
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
        chroot_api(mounts, root_a)
        policy_rc(root_a, True)
        LOG.step("chroot", "DONE")
        count = extract_bundle(bundle_path, root_a, stage_dir)
        LOG.step("bundle", "DONE", files=count)
        dtb = build_dtbs(root_a, kernel_tree, recipe, kver)
        if not (dtb["lab"]["merged"] and dtb["field"]["merged"]):
            manifest["blocking"].append("dt_overlays_missing: lab.dtb/field.dtb are the unmerged package DTB (IMG-05)")
            if not allow_unmerged_dtb:
                raise BuildError("lab/field overlays absent (IMG-05); rerun with --allow-unmerged-dtb only for a CI candidate")
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
        for art_id in recipe["kernel_artifacts"]:
            shutil.copyfile(Path(cache) / artifacts[art_id]["cache_path"], debs_dir / artifacts[art_id]["name"])
            names.append("/var/cache/srrx-image/" + artifacts[art_id]["name"])
        extra = {"SRRX_ALLOW_UNMERGED_DTB": "1"} if allow_unmerged_dtb else {}
        dpkg = chroot(root_a, ["dpkg", "-i"] + names, extra_env=extra)
        shutil.rmtree(debs_dir)
        status = {n: dpkg_installed(root_a, n) for n in recipe["kernel_artifacts"]}
        if any(v != "6.18.2-4" for v in status.values()):
            raise BuildError("locked kernel debs not installed at 6.18.2-4: " + json.dumps(status))
        entry_a = sorted(p.name for p in (root_a / "boot/efi/loader/entries").glob("labA*.conf"))
        if not entry_a:
            # Debian kernel hooks call kernel-install only when systemd-boot is detected; run it explicitly.
            chroot(root_a, ["kernel-install", "add", kver, "/boot/vmlinuz-" + kver, "/boot/initrd.img-" + kver], extra_env=extra)
            entry_a = sorted(p.name for p in (root_a / "boot/efi/loader/entries").glob("labA*.conf"))
        LOG.step("kernel", "DONE", packages=status, slot_a_entry=entry_a, dpkg_tail=dpkg.stdout[-600:])
        manifest["kernel"] = {"packages": status, "slot_a_plugin_entry": entry_a}
        manifest["hardening"] = hardening(root_a, recipe, route)
        LOG.step("hardening", "DONE", held=len(manifest["hardening"]["held"]), masked=manifest["hardening"]["masked"])
        manifest["enabled_units"] = enable_units(root_a, recipe, route)
        manifest["not_enabled"] = recipe["not_enabled"]
        LOG.step("enable", "DONE")
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
        manifest["blocking"].append("selftest root A: " + str(manifest["selftest_root_a"]["status"]) + " (policy DRAFT, rows RUNTIME_ONLY)")
        LOG.step("selftest", "DONE", **manifest["selftest_root_a"])
        mounts.umount_under(root_a / "boot/efi")
        root_b = work / "mnt/root_b"
        mounts.mount(devices["root_b"], root_b, "ext4")
        run(["rsync", "-aHAXxS", "--numeric-ids", str(root_a) + "/", str(root_b) + "/"])
        cmdline_sha["B"] = write_slot_files(root_b, config, layout, ids, "B")
        mounts.mount(devices["esp"], root_b / "boot/efi", "vfat", "umask=0077")
        chroot_api(mounts, root_b)
        chroot(root_b, ["kernel-install", "add", kver, "/boot/vmlinuz-" + kver, "/boot/initrd.img-" + kver], extra_env=extra)
        for sub in ("tmp", "run", "sys", "proc", "dev"):
            mounts.umount_under(root_b / sub)
        LOG.step("root-b", "DONE", slot_b_entry=sorted(p.name for p in (root_b / "boot/efi/loader/entries").glob("labB*.conf")))
        golden = bootchain.golden_entries(root_b / "boot/efi", root_b / "etc/srrx/boot.json")
        manifest["entries"] = golden
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
        loop.detach()
        loop = None
        manifest["filesystem_checks"] = checks
        manifest["disk_check"] = disk["issues"]
        if any(checks.values()) or disk["issues"]:
            raise BuildError("final filesystem or GPT check failed: " + json.dumps({"fsck": checks, "disk": disk["issues"]}))
        import recovery_kit
        extent_map = recovery_kit.make_map(image, layout_sector=layout["sector_size"])
        dump(out / (image.name + ".map.json"), extent_map)
        LOG.step("verify", "DONE", data_bytes=extent_map["data_bytes"], extents=len(extent_map["extents"]))
        manifest.update(status="CANDIDATE_IMAGE_BUILT", finished_at=utc_now(), image={"name": image.name, "bytes": image.stat().st_size,
                        "map_sha256": sha256(out / (image.name + ".map.json")), "data_bytes": extent_map["data_bytes"]})
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
    args = parser.parse_args()
    try:
        if args.op == "plan":
            result = plan(args.route)
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
            result = {k: result[k] for k in ("status", "route", "image", "blocking", "hardware_ready")}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("status") not in ("BLOCKED",) else 2
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
