#!/usr/bin/env python3
"""Host side of the +lab package builder (recipes/README.md, .github/workflows/sr-rx-packages.yml).

For one recipe: export a keyring holding only the archive key pinned in sources.lock.json
(apt_snapshot.signing_fingerprints), check every snapshot suite's InRelease with gpgv against it
and against apt_snapshot.releases, then create a fresh noble arm64 chroot with mmdebstrap from the
locked snapshot.ubuntu.com timestamp, trusting only that keyring, with the buildd set plus the
recipe's build_depends; the InRelease files apt used are compared with the lock again. Lab
packages named by lab_build_depends (built earlier into the same --out, hashes checked against
their build records) are installed with dpkg, offline. Then deployment/ and the verified source
archive are copied in and build_recipe.py runs as uid 1000 under `unshare --net --mount --pid`:
no network interface but loopback exists while upstream code configures and compiles.
With --repeat the build runs twice in the same paths; differing .deb SHA-256 values fail (exit 2).
Needs root (mmdebstrap root mode, chroot, mount); run it only on a disposable CI builder.
It never installs anything on the host and never signs anything.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
DEPLOYMENT = HERE.parent
sys.path.insert(0, str(DEPLOYMENT))
sys.path.insert(0, str(HERE))
import deploy  # noqa: E402
import build_recipe  # noqa: E402
import fetch_sources  # noqa: E402  (the gpgv + lock comparison of `fetch_sources.py verify-debian`)

# Always in the chroot: the interpreter of build_recipe.py, git for vendor_patch.py (`git apply`
# of the reviewed patch, offline) and the CMake toolchain. buildd adds build-essential/dpkg-dev.
BASE_PACKAGES = ("python3", "git", "cmake", "pkgconf")
BUILDER_UID = 1000
CLEAN_ENV = "/usr/bin/env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin HOME=/work LANG=C.UTF-8"
# Inside new mount and PID namespaces: private mounts, /dev and /proc for the toolchain, then the
# chroot as the unprivileged builder with a clean environment. The network namespace is new and empty.
# sysfs is mounted from inside the new network namespace, so /sys/class/net lists only its interfaces.
INNER = ('set -eu; c=$1; shift; mount --make-rprivate /; mount --rbind /dev "$c/dev"; mount -t proc proc "$c/proc"; '
         'mount -t sysfs -o ro sysfs "$c/sys"; '
         'exec chroot --userspec=%d:%d "$c" %s "$@"' % (BUILDER_UID, BUILDER_UID, CLEAN_ENV))
LAB_DEBS = "lab-debs"  # chroot directory of the installed lab_build_depends and their manifest


def sources(lock, keyring):
    snapshot = lock["apt_snapshot"]
    return ["deb [signed-by=%s] %s/%s %s %s" % (keyring, snapshot["archive"], snapshot["timestamp"], suite, " ".join(snapshot["areas"]))
            for suite in snapshot["suites"]]


def mmdebstrap_argv(recipe, lock, chroot, keyring):
    """keyring: the pinned-key-only keyring (pinned_keyring). The setup hook puts it at the same
    path inside the chroot, so apt resolves signed-by alike whether it runs outside or inside.
    The apt lists are kept so installed_releases() can compare the InRelease files with the lock."""
    packages = sorted(set(BASE_PACKAGES) | set(recipe["build_depends"]))
    keyring = str(keyring)
    hook = 'mkdir -p "$1"%s && cp %s "$1"%s' % (shlex.quote(str(Path(keyring).parent)), shlex.quote(keyring), shlex.quote(keyring))
    return (["mmdebstrap", "--mode=root", "--format=directory", "--variant=buildd", "--architectures=arm64",
             "--components=" + ",".join(lock["apt_snapshot"]["areas"]), "--keyring=" + keyring,
             '--aptopt=Acquire::Check-Valid-Until "false"', '--aptopt=Acquire::Retries "3"',
             "--setup-hook=" + hook, "--skip=cleanup/apt/lists",
             "--include=" + ",".join(packages), "noble", str(chroot)] + sources(lock, keyring))


def offline_argv(chroot, inner):
    return ["unshare", "--net", "--mount", "--pid", "--fork", "--", "sh", "-c", INNER, "sh", str(chroot)] + list(inner)


def offline_root_argv(chroot, inner):
    """Root in the chroot, still in a new empty network namespace (dpkg -i of the lab packages)."""
    return ["unshare", "--net", "--fork", "--", "chroot", str(chroot)] + CLEAN_ENV.split() + list(inner)


def pinned_keyring(lock, directory):
    """Export only the pinned archive key(s) from the lock keyring; gpg must list exactly them."""
    snapshot = lock["apt_snapshot"]
    pinned = sorted(f.upper() for f in snapshot["signing_fingerprints"])
    home = Path(directory) / "gnupg"
    home.mkdir(mode=0o700, parents=True)
    source = home / "lock-keyring.gpg"  # a private copy: gpg never locks or touches the host keyring
    shutil.copyfile(snapshot["keyring"], source)
    env = dict(os.environ, GNUPGHOME=str(home))
    exported = subprocess.run(["gpg", "--batch", "--no-default-keyring", "--keyring", str(source), "--export"] + pinned,
                              env=env, capture_output=True, check=True).stdout
    keyring = Path(directory) / "archive-pinned.gpg"
    keyring.write_bytes(exported)
    listing = subprocess.run(["gpg", "--batch", "--with-colons", "--show-keys", str(keyring)], env=env, capture_output=True, text=True, check=True).stdout
    if primary_fingerprints(listing) != pinned:
        raise build_recipe.RecipeError("the exported archive keyring is not exactly the pinned key(s)")
    return keyring


def primary_fingerprints(colons):
    """Primary-key fingerprints of `gpg --with-colons` output (the fpr record right after pub)."""
    found, after_pub = [], False
    for line in colons.splitlines():
        fields = line.split(":")
        if fields[0] == "pub":
            after_pub = True
        elif fields[0] == "fpr" and after_pub:
            found.append(fields[9].upper())
            after_pub = False
    return sorted(found)


def installed_releases(chroot, lock):
    """The InRelease files apt kept in the chroot are byte-identical to apt_snapshot.releases."""
    lists = Path(chroot) / "var/lib/apt/lists"
    records = {r["suite"]: r for r in lock["apt_snapshot"]["releases"]}
    result = []
    for suite in lock["apt_snapshot"]["suites"]:
        found = sorted(lists.glob("*_dists_" + suite + "_InRelease"))
        if len(found) != 1 or suite not in records:
            raise build_recipe.RecipeError("chroot apt lists lack exactly one InRelease for " + suite)
        if deploy.sha(found[0]) != records[suite]["inrelease_sha256"] or found[0].stat().st_size != records[suite]["size"]:
            raise build_recipe.RecipeError("the chroot was built from another InRelease than the lock: " + suite)
        result.append(dict(records[suite]))
    return result


def lab_packages(recipe, out_root):
    """The lab .debs named by lab_build_depends, from earlier builds under out_root, each with the
    SHA-256 and size of its build record. Missing, repeated or changed packages fail."""
    wanted, found = recipe["lab_build_depends"], {}
    if not wanted:
        return []
    for record_path in sorted(Path(out_root).glob("*/*.build-record.json")):
        record = deploy.load(record_path)
        for package in record["packages"]:
            if package["package"] not in wanted:
                continue
            deb = record_path.parent / package["filename"]
            if package["package"] in found:
                raise build_recipe.RecipeError("lab package built twice: " + package["package"])
            if not deb.is_file() or deploy.sha(deb) != package["sha256"] or deb.stat().st_size != package["size"]:
                raise build_recipe.RecipeError("lab package differs from its build record: " + package["package"])
            found[package["package"]] = {"package": package["package"], "version": package["version"], "sha256": package["sha256"],
                                         "component": record["component"], "record_sha256": deploy.sha(record_path), "path": deb}
    missing = [name for name in wanted if name not in found]
    if missing:
        raise build_recipe.RecipeError("lab_build_depends not built earlier into --out: " + ", ".join(missing))
    return [found[name] for name in wanted]


def install_lab_packages(chroot, packages):
    directory = Path(chroot) / LAB_DEBS
    directory.mkdir()
    for item in packages:
        shutil.copyfile(item["path"], directory / item["path"].name)
    manifest = [{k: v for k, v in item.items() if k != "path"} for item in packages]
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if packages:
        result = subprocess.run(offline_root_argv(chroot, ["dpkg", "-i"] + ["/%s/%s" % (LAB_DEBS, i["path"].name) for i in packages]))
        if result.returncode:
            raise build_recipe.RecipeError("lab_build_depends do not install offline (their Depends belong in build_depends)")
    return manifest


def build_once(component, chroot, archive_name, jobs):
    inner = ["python3", "-B", "-I", "/srrx/deployment/recipes/build_recipe.py", "--recipe",
             "/srrx/deployment/recipes/%s/recipe.json" % component, "--archive", "/cache/" + archive_name,
             "--work", "/work/" + component, "--out", "/out/" + component, "--jobs", str(jobs),
             "--lab-debs", "/" + LAB_DEBS + "/manifest.json"]
    return subprocess.run(offline_argv(chroot, inner)).returncode


def debs(directory):
    return {p.name: deploy.sha(p) for p in sorted(Path(directory).glob("*.deb"))}


def lab_build(component, cache, work, out, jobs=4, repeat=False):
    if os.geteuid() != 0:
        raise build_recipe.RecipeError("lab_build.py needs root on a disposable builder (mmdebstrap, chroot, mounts)")
    lock = deploy.load(DEPLOYMENT / "sources.lock.json")
    recipe = deploy.load(HERE / component / "recipe.json")
    entry = build_recipe.validate_recipe(recipe, lock)
    archive = Path(cache).resolve(strict=True) / entry["source_cache_path"]
    if deploy.sha(archive) != entry["source_archive_sha256"] or archive.stat().st_size != entry["source_archive_size"]:
        raise build_recipe.RecipeError("cached archive differs from the lock: " + component)
    out_root = Path(out).resolve()
    work, out = Path(work).resolve() / component, out_root / component
    if work.exists() or out.exists():
        raise build_recipe.RecipeError("work/output for this recipe already exist")
    depends = lab_packages(recipe, out_root)
    chroot = work / "chroot"
    work.mkdir(parents=True)
    keyring = pinned_keyring(lock, work / "keyring")
    fetch_sources.verify_releases(lock, keyring, work / "inrelease")
    subprocess.run(mmdebstrap_argv(recipe, lock, chroot, keyring), check=True)
    releases = installed_releases(chroot, lock)
    installed = install_lab_packages(chroot, depends)
    shutil.copytree(DEPLOYMENT, chroot / "srrx/deployment", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests", "linux_lab", "module_lab"))
    (chroot / "cache").mkdir()
    shutil.copyfile(archive, chroot / "cache" / archive.name)
    for name in ("work", "out"):
        (chroot / name).mkdir()
        os.chown(chroot / name, BUILDER_UID, BUILDER_UID)
    return run_builds(component, chroot, archive.name, jobs, repeat, out, {"chroot_inrelease": releases, "lab_build_depends": installed})


def run_builds(component, chroot, archive_name, jobs, repeat, out, extra):
    """One build, or two in the same chroot paths; the result is written to <id>.reproducibility.json
    before differing .deb hashes fail, so the artifact shows both sets."""
    runs = []
    for attempt in range(2 if repeat else 1):
        if attempt:
            shutil.move(str(chroot / "out" / component), str(chroot / "out" / (component + ".first")))
            shutil.rmtree(chroot / "work" / component)
        if build_once(component, chroot, archive_name, jobs):
            raise build_recipe.RecipeError("recipe build failed: " + component + " (see the build log in the output)")
        runs.append(debs(chroot / "out" / component))
    shutil.copytree(chroot / "out" / component, out)
    result = {"component": component, "debs": runs[-1], "repeat": repeat, "hardware_ready": False,
              "reproducible": (runs[0] == runs[1]) if repeat else None, **extra,
              "scope": "Two builds in the same chroot paths and the same SOURCE_DATE_EPOCH; a second independent builder is still a separate check."}
    if repeat:
        result["first_debs"] = runs[0]
    (out / (component + ".reproducibility.json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    owner = int(os.environ.get("SUDO_UID", "0")), int(os.environ.get("SUDO_GID", "0"))
    for path in [out.parent, out] + list(out.rglob("*")):  # the caller (sudo) owns the whole output tree
        os.chown(path, *owner, follow_symlinks=False)
    if repeat and not result["reproducible"]:
        raise build_recipe.RecipeError("the two builds differ: " + component + " (" + component + ".reproducibility.json)")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recipe", required=True, help="recipe id: deployment/recipes/<id>/recipe.json")
    parser.add_argument("--cache", type=Path, required=True, help="fetch_sources.py cache with the verified archive")
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="output root; earlier recipes' outputs there supply lab_build_depends")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    parser.add_argument("--repeat", action="store_true", help="build twice; differing .deb hashes fail")
    parser.add_argument("--print-argv", action="store_true", help="print the mmdebstrap and offline argv, run nothing")
    args = parser.parse_args()
    try:
        if args.print_argv:
            lock = deploy.load(DEPLOYMENT / "sources.lock.json")
            recipe = deploy.load(HERE / args.recipe / "recipe.json")
            build_recipe.validate_recipe(recipe, lock)
            print(json.dumps({"mmdebstrap": mmdebstrap_argv(recipe, lock, Path("/CHROOT"), Path("/WORK/keyring/archive-pinned.gpg")),
                              "offline": offline_argv(Path("/CHROOT"), ["python3", "..."])}, indent=2))
            return
        print(json.dumps(lab_build(args.recipe, args.cache, args.work, args.out, args.jobs, args.repeat), indent=2, default=str))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
