#!/usr/bin/env python3
"""Build and run an offline ARM64 Linux guest without host mounts or devices."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile
import time
import uuid

PROJECT = Path(__file__).resolve().parents[2]
IMAGE = "ubuntu-24.04-server-cloudimg-arm64.img"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def call(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def signed_sums(path):
    return {line.split(maxsplit=1)[1].lstrip("*"): line.split()[0]
            for line in Path(path).read_text().splitlines() if line.strip()}


def check_signed_assets(assets, expected):
    """A valid signature alone proves nothing; the locked hashes must be listed."""
    for name, record in expected.items():
        folder = assets / ("ubuntu" if name.endswith(".img") else "unpacked")
        if signed_sums(folder / "SHA256SUMS").get(name) != record["sha256"]:
            raise ValueError("Locked asset absent from signed Ubuntu SHA256SUMS: " + name)


def dependency_locks(assets):
    """The guest takes its --require-hashes pins from these files: supply only
    the project lock the wheels were verified against, never a stale copy."""
    locks = {name: Path(__file__).with_name(name).read_bytes()
             for name in ("wheelhouse-requirements.txt", "wheelhouse-manifest.json")}
    for name, data in locks.items():
        if (assets / name).read_bytes() != data:
            raise ValueError("Asset dependency lock differs from the project lock: " + name)
    return locks


def root_owned(info):
    # Host UID/user names must not become guest owners (e.g. labclient=1001).
    info.uid, info.gid, info.uname, info.gname = 0, 0, "root", "root"
    return info


def overlay_record(qemu_img, base, image_sha256):
    """Reuse only a written, exit-0 lab overlay whose chain ends at the locked image."""
    previous = json.loads((base.parent / "report.json").read_text())
    if previous.get("environment", {}).get("architecture") != "aarch64" or previous.get("physical_tests_performed") is not False:
        raise ValueError("Base overlay must be a stopped isolated ARM64 lab run")
    code = previous.get("host", {}).get("qemu_exit_code")
    if previous.get("status") not in {"PASS", "FAIL"} or type(code) is not int or code != 0:
        raise ValueError("Base overlay run must have written its summary and exited QEMU with code 0")
    # qemu-img refuses a concurrently open writable image. Reuse only the
    # powered-off guest's OS cache; locked debs/wheels and sources reinstall.
    call([qemu_img, "check", base], stdout=subprocess.DEVNULL)
    chain = json.loads(call([qemu_img, "info", "--backing-chain", "--output=json", base], capture_output=True).stdout)
    layers = [{"filename": x["filename"], "format": x["format"], "sha256": sha(x["filename"])} for x in chain]
    if len(layers) < 2 or Path(layers[0]["filename"]).resolve() != base or layers[-1]["sha256"] != image_sha256:
        raise ValueError("Base overlay backing chain must end at the locked Ubuntu image")
    return {"path": str(base), "sha256": layers[0]["sha256"],
            "previous_report_sha256": sha(base.parent / "report.json"),
            "previous_status": previous["status"], "previous_qemu_exit_code": code,
            "previous_summary_written": True, "backing_chain": layers,
            "purpose": "stopped OS cache; locked debs/wheels reinstall from this payload; Linux replays its filesystem journal if needed; not a clean-image rerun"}


def check_results(result):
    """debugfs recreates guest symlinks; never follow guest-written links on the host."""
    for path in [result, *result.rglob("*")]:
        mode = path.lstat().st_mode
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError("Guest results contain a symlink or special file: " + path.relative_to(result).as_posix())


def prepare(args):
    assets, work = args.assets.resolve(strict=True), args.work.resolve()
    if work.exists() or work.is_relative_to(PROJECT):
        raise ValueError("Use a new workspace outside the source project")
    if any(c.isspace() or c == "," for c in str(work)):
        raise ValueError("Work path must not contain whitespace or commas (QEMU/debugfs arguments)")
    work.mkdir(parents=True, mode=0o700)
    source = json.loads((assets / "ubuntu-assets.json").read_text())
    locked = json.loads(Path(__file__).with_name("assets.lock.json").read_text())
    expected = {x["name"]: x for x in locked["ubuntu_assets"]}
    found = {}
    for asset in source["assets"]:
        p = Path(asset["file"]).resolve(strict=True)
        if not p.is_relative_to(assets) or p.name not in expected:
            raise ValueError("Unexpected Ubuntu asset")
        record = expected[p.name]
        if sha(p) != record["sha256"] or p.stat().st_size != record["bytes"]:
            raise ValueError("Ubuntu asset integrity mismatch: " + p.name)
        found[p.name] = p
    if set(found) != set(expected):
        raise ValueError("Incomplete Ubuntu image/kernel/initrd")
    # Signature verification uses the caller's trusted distribution keyring.
    for directory in (assets / "ubuntu", assets / "unpacked"):
        call(["gpgv", "--keyring", args.keyring, directory / "SHA256SUMS.gpg", directory / "SHA256SUMS"],
             stdout=subprocess.DEVNULL)
    check_signed_assets(assets, expected)
    for tool in (args.qemu, args.qemu_img, args.genisoimage):
        if not Path(tool).is_file():
            raise ValueError("Missing explicitly selected host tool: " + str(tool))
    image = found[IMAGE]
    base_record = None
    if args.base_overlay:
        base = args.base_overlay.resolve(strict=True)
        base_record = overlay_record(args.qemu_img, base, expected[IMAGE]["sha256"])
        image = base
    call([args.qemu_img, "create", "-f", "qcow2", "-F", "qcow2", "-b", image,
          work / "guest.qcow2", "10G"], stdout=subprocess.DEVNULL)
    payload = work / "payload"
    payload.mkdir()
    entries = []
    with tarfile.open(payload / "project.tar.gz", "w:gz") as archive:
        for path in sorted(PROJECT.rglob("*")):
            relative = path.relative_to(PROJECT)
            if not path.is_file() or path.is_symlink():
                continue
            if any(x in {"__pycache__", ".git", "tmp", "qa"} for x in relative.parts):
                continue
            if path.suffix in {".pyc", ".html", ".tmp", ".kicad_prl", ".lck"}:
                continue
            if path.suffix == ".zip" and relative.parts[:2] != ("firmware", "dist"):
                continue
            entries.append({"path": relative.as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
            archive.add(path, arcname=relative.as_posix(), recursive=False, filter=root_owned)
    (payload / "project-manifest.json").write_text(json.dumps(entries, indent=2) + "\n")
    wheel_lock = json.loads(Path(__file__).with_name("wheelhouse-manifest.json").read_text())
    deb_lock = json.loads(Path(__file__).with_name("guest-packages.lock.json").read_text())
    sets = {"wheels": [{"name": x["filename"], "sha256": x["sha256"], "bytes": x["size_bytes"]}
                       for x in wheel_lock["wheels"]],
            "debs": [{"name": x["filename"], "sha256": x["sha256"], "bytes": x["bytes"]}
                     for x in deb_lock["packages"]]}
    for name, records in sets.items():
        origin = assets / name
        if not origin.is_dir():
            raise ValueError("Missing verified offline dependency directory: " + name)
        destination = payload / name
        destination.mkdir()
        for x in records:
            path = origin / x["name"]
            if path.name != x["name"] or sha(path) != x["sha256"] or path.stat().st_size != x["bytes"]:
                raise ValueError("Offline dependency integrity mismatch: " + x["name"])
            shutil.copyfile(path, destination / path.name)
    for name, data in dependency_locks(assets).items():
        (payload / name).write_bytes(data)
    shutil.copyfile(Path(__file__).with_name("guest_bootstrap.sh"), payload / "bootstrap.sh")
    (payload / "lab-clock.json").write_text(json.dumps({"host_unix_time_s": time.time(),
        "source": "host realtime at lab preparation; not GNSS or hardware clock qualification"}) + "\n")
    # A manifest binds the actual packages supplied to this run, including any
    # dependency set whose qualification remains outside the hardware release.
    inputs = [{"path": p.relative_to(payload).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)}
              for p in sorted(payload.rglob("*")) if p.is_file()]
    (payload / "payload-manifest.json").write_text(json.dumps(inputs, indent=2) + "\n")
    call([args.genisoimage, "-quiet", "-R", "-J", "-V", "SRRXPAY", "-o", work / "payload.iso", payload])
    seed = work / "seed"
    seed.mkdir()
    # A cached overlay keeps cloud-init state: a reused instance-id skips runcmd.
    instance_id = "srrx-arm64-lab-" + uuid.uuid4().hex
    (seed / "meta-data").write_text("instance-id: " + instance_id + "\nlocal-hostname: srrx-arm64-lab\n")
    (seed / "network-config").write_text("version: 2\nethernets: {}\n")
    (seed / "user-data").write_text("""#cloud-config
datasource_list: [NoCloud]
ssh_pwauth: false
disable_root: true
runcmd:
  - [mkdir, -p, /mnt/srrx-payload]
  - [mount, -t, iso9660, -o, ro, /dev/disk/by-label/SRRXPAY, /mnt/srrx-payload]
  - [bash, /mnt/srrx-payload/bootstrap.sh]
final_message: SRRX ARM64 Linux lab cloud-init completed
""")
    call([args.genisoimage, "-quiet", "-R", "-J", "-V", "cidata", "-o", work / "seed.iso", seed])
    with (work / "results.img").open("wb") as result:
        result.truncate(128 * 1024 * 1024)
    call(["mke2fs", "-q", "-F", "-t", "ext4", "-L", "SRRXRESULT", work / "results.img"],
         stdout=subprocess.DEVNULL)
    with (work / "storage.img").open("wb") as storage:
        storage.truncate(64 * 1024 * 1024)
    call(["mke2fs", "-q", "-F", "-t", "ext4", "-m", "0", "-L", "SRRXT7", work / "storage.img"],
         stdout=subprocess.DEVNULL)
    qemu = [str(args.qemu), "-machine", "virt-8.2,gic-version=3", "-accel", "tcg,thread=multi",
            "-cpu", "cortex-a76", "-smp", "4", "-m", "3072", "-nodefaults", "-display", "none",
            "-monitor", "none", "-serial", "stdio", "-nic", "none", "-no-reboot",
            "-kernel", str(found["ubuntu-24.04-server-cloudimg-arm64-vmlinuz-generic"]),
            "-initrd", str(found["ubuntu-24.04-server-cloudimg-arm64-initrd-generic"]),
            "-append", "root=/dev/vda1 rw console=ttyAMA0 earlycon=pl011,0x9000000 panic=-1 systemd.mask=systemd-networkd-wait-online.service"]
    for index, filename in enumerate(("guest.qcow2", "seed.iso", "payload.iso", "results.img", "storage.img")):
        path = str(work / filename)
        if "," in path:
            raise ValueError("QEMU block paths cannot contain commas")
        options = f"if=none,id=disk{index},file={path},format={'qcow2' if index == 0 else 'raw'}"
        if index in (1, 2):
            options += ",readonly=on"
        qemu += ["-drive", options, "-device", f"virtio-blk-pci,drive=disk{index}"]
    record = {"schema_version": 1, "environment": "qemu-arm64-linux-lab", "command": qemu,
              "network_devices": [], "host_device_passthrough": [], "shared_host_directories": [],
              "source_manifest_sha256": sha(payload / "project-manifest.json"),
              "payload_manifest_sha256": sha(payload / "payload-manifest.json"),
              "cloud_init_instance_id": instance_id,
              "hardware_qualification": False, "q6a_peripherals_emulated": False}
    record["base_overlay"] = base_record
    (work / "run.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"prepared": str(work), "files": len(entries), "offline": True}))


def run(args):
    work = args.work.resolve(strict=True)
    record = json.loads((work / "run.json").read_text())
    if record["network_devices"] or record["host_device_passthrough"] or record["shared_host_directories"]:
        raise ValueError("Lab definition grants unexpected external access")
    if any(c.isspace() for c in str(work)):
        raise ValueError("Work path must not contain whitespace (debugfs request)")
    started = time.monotonic()
    with (work / "console.log").open("wb") as console:
        proc = subprocess.Popen(record["command"], stdin=subprocess.DEVNULL,
                                stdout=console, stderr=subprocess.STDOUT)
        try:
            code = proc.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            raise RuntimeError("Guest exceeded bounded run time; inspect console.log")
    result = work / "results"
    result.mkdir(exist_ok=False)
    with (work / "debugfs.log").open("wb") as log:
        call(["debugfs", "-R", "rdump / " + str(result), work / "results.img"],
             stdout=subprocess.DEVNULL, stderr=log)
    check_results(result)
    report = json.loads((result / "summary.json").read_text())
    report["host"] = {"qemu_exit_code": code, "elapsed_s": round(time.monotonic() - started, 3),
                      "run_manifest_sha256": sha(work / "run.json"),
                      "console_sha256": sha(work / "console.log")}
    (work / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") == "PASS" and code == 0 else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--assets", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--base-overlay", type=Path,
                   help="Optional completed (summary written, QEMU exit 0) guest.qcow2 OS cache; locked dependencies reinstall; chain is recorded")
    for name in ("qemu", "qemu-img", "genisoimage"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--keyring", type=Path, default=Path("/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg"))
    p = sub.add_parser("run")
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    return prepare(args) if args.operation == "prepare" else run(args)


if __name__ == "__main__":
    raise SystemExit(main())
