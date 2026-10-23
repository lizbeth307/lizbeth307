#!/usr/bin/env python3
"""Fetch pinned lab inputs; verify bytes before making them available to QEMU."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def signed_sums(path):
    return {line.split(maxsplit=1)[1].lstrip("*"): line.split()[0]
            for line in path.read_text().splitlines() if line.strip()}


def fetch(url, path, expected=None, size=None):
    if expected and path.is_file() and digest(path) == expected and (size is None or path.stat().st_size == size):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="srrx-input-", dir=path.parent)
    try:
        value, total = hashlib.sha256(), 0
        with os.fdopen(fd, "wb") as target, urlopen(url, timeout=60) as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                target.write(chunk)
                value.update(chunk)
                total += len(chunk)
                if size is not None and total > size:
                    raise ValueError("Download exceeds locked size: " + path.name)
        if expected and value.hexdigest() != expected or size is not None and total != size:
            raise ValueError("Input integrity mismatch: " + path.name)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--keyring", type=Path, default=Path("/usr/share/keyrings/ubuntu-cloudimage-keyring.gpg"))
    args = parser.parse_args()
    dest = args.dest.resolve()
    if dest.is_relative_to(HERE.parents[1]):
        raise ValueError("Asset cache must stay outside the source checkout")
    dest.mkdir(parents=True, exist_ok=True)
    lock = json.loads((HERE / "assets.lock.json").read_text())
    records = []
    for section in ("ubuntu", "unpacked"):
        origin = lock["primary_base_url"] + ("unpacked/" if section == "unpacked" else "")
        for name in ("SHA256SUMS", "SHA256SUMS.gpg"):
            fetch(origin + name, dest / section / name)
        subprocess.run(["gpgv", "--keyring", str(args.keyring), str(dest / section / "SHA256SUMS.gpg"),
                        str(dest / section / "SHA256SUMS")], check=True)
    for x in lock["ubuntu_assets"]:
        folder = "ubuntu" if x["name"].endswith(".img") else "unpacked"
        if signed_sums(dest / folder / "SHA256SUMS").get(x["name"]) != x["sha256"]:
            raise ValueError("Pinned asset differs from the signed Ubuntu manifest")
        path = dest / folder / x["name"]
        fetch(x["url"], path, x["sha256"], x["bytes"])
        records.append({**x, "file": str(path), "expected_sha256": x["sha256"]})
        print("Verified", x["name"], flush=True)
    # build_kit.py also ships the signed package-state manifest the guest lock was resolved from.
    guest = json.loads((HERE / "guest-packages.lock.json").read_text())
    name = "ubuntu-24.04-server-cloudimg-arm64.manifest"
    if signed_sums(dest / "ubuntu" / "SHA256SUMS").get(name) != guest["guest_manifest_sha256"]:
        raise ValueError("Guest package-state manifest lock differs from the signed Ubuntu manifest")
    fetch(lock["primary_base_url"] + name, dest / "ubuntu" / name, guest["guest_manifest_sha256"])
    print("Verified", name, flush=True)
    (dest / "ubuntu-assets.json").write_text(json.dumps({"image_release": lock["image_release"], "assets": records}, indent=2) + "\n")
    wheels = json.loads((HERE / "wheelhouse-manifest.json").read_text())
    for x in wheels["wheels"]:
        fetch(x["url"], dest / "wheels" / x["filename"], x["sha256"], x["size_bytes"])
        print("Verified", x["filename"], flush=True)
    for name in ("wheelhouse-manifest.json", "wheelhouse-requirements.txt"):
        shutil.copyfile(HERE / name, dest / name)
    packages = json.loads((HERE / "guest-packages.lock.json").read_text())
    for x in packages["packages"]:
        fetch(x["url"], dest / "debs" / Path(x["filename"]).name, x["sha256"], x["bytes"])
        print("Verified", Path(x["filename"]).name, flush=True)
    print("Offline ARM64 input cache complete")


if __name__ == "__main__":
    main()
