#!/usr/bin/env python3
"""CI checks around the lab builder output and a published lab repository (repo/README.md).

`packages`: every .deb of every build record has the recorded SHA-256/size and control fields,
its extracted data tree equals the package's verify_build manifest, and deploy.verify_build
still refuses that manifest because it is OPEN (a reviewer, never CI, sets REVIEWED).
`tamper`: the published repository passes deploy.verify_repo, and each tampered copy (index,
pool, keyring, InRelease pin, build record, apt entry, held package) is refused.
Read-only for its inputs; writes only into new temporary directories. CI evidence only.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
DEPLOYMENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT))
import deploy  # noqa: E402


class CheckError(ValueError):
    pass


def field(deb, name):
    return subprocess.run(["dpkg-deb", "--field", str(deb), name], capture_output=True, text=True, check=True).stdout.strip()


def packages(out):
    records = sorted(Path(out).glob("*/*.build-record.json"))
    if not records:
        raise CheckError("no build records under " + str(out))
    summary = []
    for record_path in records:
        record = deploy.load(record_path)
        for package in record["packages"]:
            deb = record_path.parent / package["filename"]
            if deploy.sha(deb) != package["sha256"] or deb.stat().st_size != package["size"]:
                raise CheckError("deb differs from its build record: " + deb.name)
            for name, expected in (("Package", package["package"]), ("Version", package["version"]), ("Architecture", package["architecture"])):
                if field(deb, name) != expected:
                    raise CheckError(deb.name + " control " + name + " differs")
            manifest_path = record_path.parent / (package["package"] + ".build-manifest.json")
            if deploy.sha(manifest_path) != package["build_manifest_sha256"]:
                raise CheckError("build manifest differs from its record: " + manifest_path.name)
            manifest = deploy.load(manifest_path)
            with tempfile.TemporaryDirectory(prefix="srrx-deb-") as temporary:
                subprocess.run(["dpkg-deb", "-x", str(deb), temporary], check=True)
                root = Path(temporary)
                files = {}
                for path in sorted(root.rglob("*")):
                    if path.is_file():
                        files[path.relative_to(root).as_posix()] = deploy.sha(path)
                if files != manifest["files"]:
                    raise CheckError("extracted " + deb.name + " differs from its build manifest")
                try:
                    deploy.verify_build(root, manifest)
                except deploy.DeploymentError as exc:
                    if "OPEN/unreviewed" not in str(exc):
                        raise CheckError("verify_build gave another refusal for " + deb.name + ": " + str(exc)) from exc
                else:
                    raise CheckError("verify_build accepted a CI manifest: " + deb.name)
            summary.append({"package": package["package"], "version": package["version"], "files": len(files),
                            "sha256": package["sha256"], "verify_build": "REFUSED_OPEN_AS_EXPECTED"})
    return {"status": "CI_PACKAGES_MATCH_BUILD_RECORDS", "packages": summary, "hardware_ready": False}


def tamper(repo, keyring, wrong_keyring, fingerprint, records, sources_entry):
    repo = Path(repo).resolve(strict=True)
    good = deploy.verify_repo(repo, keyring, fingerprint, records, sources_entry)
    pinned = good["inrelease_sha256"]
    first_deb = sorted(Path(repo).rglob("*.deb"))[0]
    name = first_deb.name.split("_")[0]
    cases = {}

    def expect(label, needle, change=None, **overrides):
        with tempfile.TemporaryDirectory(prefix="srrx-tamper-") as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(repo, copy, symlinks=True)
            arguments = {"repo": copy, "keyring": keyring, "fingerprint": fingerprint, "build_records": records,
                         "sources_entry": sources_entry, "inrelease_sha256": pinned, "target_status": None}
            if change:
                change(copy, Path(temporary), arguments)
            arguments.update(overrides)
            try:
                deploy.verify_repo(**arguments)
            except deploy.DeploymentError as exc:
                if needle not in str(exc):
                    raise CheckError(label + ": refused for another reason: " + str(exc)) from exc
                cases[label] = "REFUSED"
                return
            raise CheckError(label + ": tampered repository accepted")

    def packages_index(copy, _, __):
        index = next(copy.rglob("binary-arm64/Packages"))
        index.write_bytes(index.read_bytes() + b"\n")

    def extra_deb(copy, _, __):
        shutil.copyfile(first_deb, copy / first_deb.relative_to(repo).parent / "extra_1.0+lab1_arm64.deb")

    def swapped_deb(copy, _, __):
        target = copy / first_deb.relative_to(repo)
        data = bytearray(target.read_bytes())
        data[-1] ^= 0xFF
        target.write_bytes(bytes(data))

    def no_signed_by(_, temporary, arguments):
        entry = temporary / "no-signed-by.sources"
        entry.write_text("".join(l for l in Path(sources_entry).read_text(encoding="utf-8").splitlines(True) if not l.startswith("Signed-By:")), encoding="utf-8")
        arguments["sources_entry"] = entry

    def held(_, temporary, arguments):
        status = temporary / "status"
        status.write_text("Package: " + name + "\nStatus: hold ok installed\nVersion: 0.0.0-0+lab1\n\n", encoding="utf-8")
        arguments["target_status"] = status

    expect("modified Packages index", "index differs from the signed Release", packages_index)
    expect("extra .deb in the pool", "pool holds a file", extra_deb)
    expect("changed .deb bytes", "pool .deb differs", swapped_deb)
    expect("wrong keyring", "not a good signature", keyring=wrong_keyring)
    expect("other InRelease pinned", "InRelease differs", inrelease_sha256="0" * 64)
    expect("package without build record", "not one of the build records", build_records=[])
    expect("apt entry without Signed-By", "Signed-By", no_signed_by)
    expect("held package would change", "held package", held)
    return {"status": "TAMPER_CASES_REFUSED", "untampered": good["status"], "cases": cases, "hardware_ready": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="operation", required=True)
    check = commands.add_parser("packages")
    check.add_argument("--out", type=Path, required=True)
    attack = commands.add_parser("tamper")
    attack.add_argument("--repo", type=Path, required=True)
    attack.add_argument("--keyring", type=Path, required=True)
    attack.add_argument("--wrong-keyring", type=Path, required=True)
    attack.add_argument("--fingerprint", required=True)
    attack.add_argument("--build-record", type=Path, action="append", required=True)
    attack.add_argument("--sources-entry", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.operation == "packages":
            result = packages(args.out)
        else:
            result = tamper(args.repo, args.keyring, args.wrong_keyring, args.fingerprint, args.build_record, args.sources_entry)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
