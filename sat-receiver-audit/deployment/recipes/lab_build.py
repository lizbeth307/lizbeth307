#!/usr/bin/env python3
"""Host side of the +lab package builder (recipes/README.md, .github/workflows/sr-rx-packages.yml).

For one recipe: create a fresh noble arm64 chroot with mmdebstrap from the snapshot.ubuntu.com
timestamp locked in sources.lock.json (apt_snapshot; signatures checked against the keyring
named there), with only the buildd set plus the recipe's build_depends; copy in deployment/ and
the verified source archive; then run build_recipe.py as uid 1000 under `unshare --net --mount
--pid`: no network interface but loopback exists while upstream code configures and compiles.
With --repeat the build runs twice in the same paths and the .deb SHA-256 values are compared.
Needs root (mmdebstrap root mode, chroot, mount); run it only on a disposable CI builder.
It never installs anything on the host and never signs anything.
"""
import argparse
import json
import os
from pathlib import Path
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

# Always in the chroot: the interpreter of build_recipe.py, git for vendor_patch.py (`git apply`
# of the reviewed patch, offline) and the CMake toolchain. buildd adds build-essential/dpkg-dev.
BASE_PACKAGES = ("python3", "git", "cmake", "pkgconf")
BUILDER_UID = 1000
# Inside new mount and PID namespaces: private mounts, /dev and /proc for the toolchain, then the
# chroot as the unprivileged builder with a clean environment. The network namespace is new and empty.
INNER = ('set -eu; c=$1; shift; mount --make-rprivate /; mount --rbind /dev "$c/dev"; mount -t proc proc "$c/proc"; '
         'exec chroot --userspec=%d:%d "$c" /usr/bin/env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin HOME=/work LANG=C.UTF-8 "$@"'
         % (BUILDER_UID, BUILDER_UID))


def sources(lock):
    snapshot = lock["apt_snapshot"]
    return ["deb [signed-by=%s] %s/%s %s %s" % (snapshot["keyring"], snapshot["archive"], snapshot["timestamp"], suite, " ".join(snapshot["areas"]))
            for suite in snapshot["suites"]]


def mmdebstrap_argv(recipe, lock, chroot):
    packages = sorted(set(BASE_PACKAGES) | set(recipe["build_depends"]))
    return (["mmdebstrap", "--mode=root", "--format=directory", "--variant=buildd", "--architectures=arm64",
             "--components=" + ",".join(lock["apt_snapshot"]["areas"]), "--keyring=" + lock["apt_snapshot"]["keyring"],
             '--aptopt=Acquire::Check-Valid-Until "false"', '--aptopt=Acquire::Retries "3"',
             "--include=" + ",".join(packages), "noble", str(chroot)] + sources(lock))


def offline_argv(chroot, inner):
    return ["unshare", "--net", "--mount", "--pid", "--fork", "--", "sh", "-c", INNER, "sh", str(chroot)] + list(inner)


def build_once(component, chroot, archive_name, jobs):
    inner = ["python3", "-B", "-I", "/srrx/deployment/recipes/build_recipe.py", "--recipe",
             "/srrx/deployment/recipes/%s/recipe.json" % component, "--archive", "/cache/" + archive_name,
             "--work", "/work/" + component, "--out", "/out/" + component, "--jobs", str(jobs)]
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
    work, out = Path(work).resolve() / component, Path(out).resolve() / component
    if work.exists() or out.exists():
        raise build_recipe.RecipeError("work/output for this recipe already exist")
    chroot = work / "chroot"
    work.mkdir(parents=True)
    subprocess.run(mmdebstrap_argv(recipe, lock, chroot), check=True)
    shutil.copytree(DEPLOYMENT, chroot / "srrx/deployment", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests", "linux_lab", "module_lab"))
    (chroot / "cache").mkdir()
    shutil.copyfile(archive, chroot / "cache" / archive.name)
    for name in ("work", "out"):
        (chroot / name).mkdir()
        os.chown(chroot / name, BUILDER_UID, BUILDER_UID)
    runs = []
    for attempt in range(2 if repeat else 1):
        if attempt:
            shutil.move(str(chroot / "out" / component), str(chroot / "out" / (component + ".first")))
            shutil.rmtree(chroot / "work" / component)
        if build_once(component, chroot, archive.name, jobs):
            raise build_recipe.RecipeError("recipe build failed: " + component + " (see the build log in the output)")
        runs.append(debs(chroot / "out" / component))
    shutil.copytree(chroot / "out" / component, out)
    result = {"component": component, "debs": runs[-1], "repeat": repeat, "hardware_ready": False,
              "reproducible": (runs[0] == runs[1]) if repeat else None,
              "scope": "Two builds in the same chroot paths and the same SOURCE_DATE_EPOCH; a second independent builder is still a separate check."}
    if repeat:
        result["first_debs"] = runs[0]
    (out / (component + ".reproducibility.json")).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    owner = int(os.environ.get("SUDO_UID", "0")), int(os.environ.get("SUDO_GID", "0"))
    for path in [out.parent, out] + list(out.rglob("*")):  # the caller (sudo) owns the whole output tree
        os.chown(path, *owner, follow_symlinks=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recipe", required=True, help="recipe id: deployment/recipes/<id>/recipe.json")
    parser.add_argument("--cache", type=Path, required=True, help="fetch_sources.py cache with the verified archive")
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    parser.add_argument("--repeat", action="store_true", help="build twice and compare the .deb hashes")
    parser.add_argument("--print-argv", action="store_true", help="print the mmdebstrap and offline argv, run nothing")
    args = parser.parse_args()
    try:
        if args.print_argv:
            lock = deploy.load(DEPLOYMENT / "sources.lock.json")
            recipe = deploy.load(HERE / args.recipe / "recipe.json")
            build_recipe.validate_recipe(recipe, lock)
            print(json.dumps({"mmdebstrap": mmdebstrap_argv(recipe, lock, Path("/CHROOT")),
                              "offline": offline_argv(Path("/CHROOT"), ["python3", "..."])}, indent=2))
            return
        print(json.dumps(lab_build(args.recipe, args.cache, args.work, args.out, args.jobs, args.repeat), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
