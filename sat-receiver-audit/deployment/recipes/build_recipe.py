#!/usr/bin/env python3
"""Build one +lab recipe into .deb files inside the isolated builder chroot (recipes/README.md).

Runs as an unprivileged user in a chroot whose network namespace has no route (lab_build.py
starts it under `unshare --net`); it first proves that no outside connection is possible. The
source archive must match deployment/sources.lock.json; a reviewed patch is applied through
vendor_patch.py. Every CMake option the upstream tree declares and this configuration evaluates
must be set explicitly by the recipe (no unreviewed upstream default). The result is .deb files,
one verify_build manifest per package (status OPEN, never REVIEWED here) and a build record that
deploy.verify_repo binds to the lock. CI evidence only: no review, no TX proof, no hardware test.
"""
import argparse
import errno
import fnmatch
import glob
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
DEPLOYMENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT))
import deploy  # noqa: E402

RECIPE_KEYS = ("schema_version", "component", "summary", "source", "build_depends", "cmake", "build", "install",
               "packages", "drop", "checks", "notes")
PACKAGE_KEYS = ("name", "section", "description", "files", "depends", "shlibs_depends")
CHECK_KINDS = {"soname": ("kind", "file", "equals"), "export_count": ("kind", "file", "prefix", "equals"),
               "forbid_strings": ("kind", "file", "substrings"), "forbid_paths": ("kind", "globs"),
               "require_paths": ("kind", "globs")}
# Programs a recipe step may run. Anything that can fetch (curl, wget, git clone, pip, apt) is absent.
STEP_PROGRAMS = frozenset({"cmake", "make", "ninja"})
PLACEHOLDERS = ("{src}", "{build}", "{destdir}", "{jobs}")
NAME = re.compile(r"[a-z0-9][a-z0-9+.-]+")
OPTION = re.compile(r"\b(?:option|cmake_dependent_option)\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)", re.I)
MAINTAINER = "SR-RX lab builder <builder@srrx.invalid>"
MULTIARCH = "aarch64-linux-gnu"


class RecipeError(ValueError):
    pass


def _strings(value, label, allow_empty=False):
    if type(value) is not list or (not value and not allow_empty) or not all(type(x) is str and x for x in value):
        raise RecipeError(label + " must be a list of non-empty strings")
    return value


def _argv(value, label):
    _strings(value, label)
    if value[0] not in STEP_PROGRAMS:
        raise RecipeError(label + " runs a program outside " + ", ".join(sorted(STEP_PROGRAMS)))
    for item in value:
        if "://" in item or item.startswith("--download") or "FETCHCONTENT_FULLY_DISCONNECTED=OFF" in item:
            raise RecipeError(label + " names a URL or enables downloads")
        if "{" in item and not any(p in item for p in PLACEHOLDERS):
            raise RecipeError(label + " has an unknown placeholder")
    return value


def validate_recipe(recipe, lock=None):
    """Exact schema of recipes/<id>/recipe.json (deployment/tests/test_recipes.py)."""
    deploy.keys(recipe, RECIPE_KEYS, "recipe")
    lock = lock or deploy.load(DEPLOYMENT / "sources.lock.json")
    component = next((c for c in lock["components"] if c["id"] == recipe["component"]), None)
    if recipe["schema_version"] != 1 or component is None:
        raise RecipeError("recipe schema_version must be 1 and component a sources.lock.json id")
    if component["source_archive_sha256"] is None or component.get("debian_source") is not None:
        raise RecipeError("recipe component needs a locked upstream source archive")
    deploy.keys(recipe["source"], ("patch",), "recipe source")
    patch = recipe["source"]["patch"]
    if patch is not None and (patch != "deployment/patches/" + recipe["component"] + "-rx-only.patch"
                              or not (DEPLOYMENT.parent / patch).is_file()):
        raise RecipeError("recipe patch must be the reviewed deployment/patches/<component>-rx-only.patch")
    for name in _strings(recipe["build_depends"], "build_depends"):
        if not NAME.fullmatch(name):
            raise RecipeError("build_depends holds a non-package name: " + name)
    cmake = recipe["cmake"]
    deploy.keys(cmake, ("configure", "options", "variables"), "recipe cmake")
    _argv(cmake["configure"], "cmake.configure")
    if cmake["configure"][:5] != ["cmake", "-S", "{src}", "-B", "{build}"]:
        raise RecipeError("cmake.configure must start with cmake -S {src} -B {build}")
    for section in ("options", "variables"):
        if type(cmake[section]) is not dict or not all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k) and type(v) is str and v
                                                       for k, v in cmake[section].items()):
            raise RecipeError("cmake." + section + " must map CMake names to string values")
    if set(cmake["options"]) & set(cmake["variables"]) or any(v not in ("ON", "OFF") for v in cmake["options"].values()):
        raise RecipeError("cmake.options are ON/OFF and disjoint from cmake.variables")
    if cmake["variables"].get("FETCHCONTENT_FULLY_DISCONNECTED") != "ON":
        raise RecipeError("FETCHCONTENT_FULLY_DISCONNECTED must be ON")
    if type(recipe["build"]) is not list or not recipe["build"]:
        raise RecipeError("build lists at least one step")
    for index, step in enumerate(recipe["build"]):
        _argv(step, "build[%d]" % index)
    install = recipe["install"]
    deploy.keys(install, ("cmake_install", "copy"), "recipe install")
    if type(install["cmake_install"]) is not bool or type(install["copy"]) is not list or (install["cmake_install"] == bool(install["copy"])):
        raise RecipeError("install is either cmake_install or an explicit copy list")
    for item in install["copy"]:
        deploy.keys(item, ("from", "to"), "install copy")
        if not item["from"].startswith(("{src}/", "{build}/")) or item["to"].startswith("/") or ".." in item["to"].split("/"):
            raise RecipeError("install copy goes from {src}/{build} to a relative package path")
    names = set()
    for package in recipe["packages"]:
        deploy.keys(package, PACKAGE_KEYS, "recipe package")
        if not NAME.fullmatch(package["name"]) or package["name"] in names:
            raise RecipeError("package name invalid or repeated")
        names.add(package["name"])
        _strings(package["files"], package["name"] + " files")
        _strings(package["depends"], package["name"] + " depends", allow_empty=True)
        if type(package["shlibs_depends"]) is not bool or type(package["description"]) is not str or not package["description"]:
            raise RecipeError(package["name"] + " needs shlibs_depends and a description")
    if not names:
        raise RecipeError("recipe emits no package")
    forbidden = deploy.prohibited_installed({n: component["version"] for n in names}, identifiers=True)
    if forbidden:
        raise RecipeError("receive-only policy forbids package: " + ", ".join(forbidden))
    for item in recipe["drop"]:
        deploy.keys(item, ("glob", "reason"), "recipe drop")
    for check in recipe["checks"]:
        if type(check) is not dict or check.get("kind") not in CHECK_KINDS:
            raise RecipeError("unknown check kind")
        deploy.keys(check, CHECK_KINDS[check["kind"]], "check " + check["kind"])
    _strings(recipe["notes"], "notes", allow_empty=True)
    return component


def no_network():
    """Fail unless an outside TCP connection is impossible (unshare --net leaves only loopback)."""
    for address in (("192.0.2.1", 443), ("2001:db8::1", 443)):  # RFC 5737/3849 documentation addresses
        family = socket.AF_INET6 if ":" in address[0] else socket.AF_INET
        try:
            with socket.socket(family, socket.SOCK_STREAM) as probe:
                probe.settimeout(3)
                probe.connect(address)
        except OSError as exc:
            if exc.errno not in (errno.ENETUNREACH, errno.EHOSTUNREACH, errno.EAFNOSUPPORT, errno.EADDRNOTAVAIL):
                raise RecipeError("network probe gave an unexpected result: " + str(exc)) from exc
            continue
        raise RecipeError("an outside connection succeeded: the build is not offline")
    interfaces = sorted(os.listdir("/sys/class/net")) if os.path.isdir("/sys/class/net") else ["(sysfs not mounted)"]
    return "no route outside the network namespace; interfaces " + ",".join(interfaces)


def extract(archive, component, destination, patch):
    """Exact locked archive -> new source tree; patched through vendor_patch when the recipe says so."""
    if patch is not None:
        import vendor_patch
        return vendor_patch.apply_from_archive(component["id"], archive, destination)
    if deploy.sha(archive) != component["source_archive_sha256"] or Path(archive).stat().st_size != component["source_archive_size"]:
        raise RecipeError("source archive differs from the lock")
    with tarfile.open(archive, "r:*") as stream:
        members = stream.getmembers()
        roots = {Path(m.name).parts[0] for m in members if Path(m.name).parts}
        if len(roots) != 1 or any(Path(m.name).is_absolute() or ".." in Path(m.name).parts for m in members):
            raise RecipeError("source archive is not one safe root")
        stream.extractall(destination.parent / ".extract", members=members, filter="data")
    shutil.move(str(destination.parent / ".extract" / roots.pop()), destination)
    return {"component": component["id"], "patch": None}


def source_date_epoch(archive):
    """The archive's own timestamp (git archive: the commit time), so rebuilds stamp equal times."""
    with tarfile.open(archive, "r:*") as stream:
        return int(stream.next().mtime)


def declared_options(source):
    names = set()
    for path in sorted(source.rglob("*")):
        if path.is_file() and (path.name == "CMakeLists.txt" or path.suffix == ".cmake"):
            # Comments stripped per line, then matched across lines: a call may wrap after "(".
            text = "\n".join(line.split("#", 1)[0] for line in path.read_text(encoding="utf-8", errors="replace").splitlines())
            names.update(OPTION.findall(text))
    return names


def check_options(source, build, options):
    """Every declared option() that this configure evaluated (a BOOL cache entry) is in the recipe."""
    declared = declared_options(source)
    evaluated = {}
    for line in (build / "CMakeCache.txt").read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*):BOOL=(.*)", line)
        if match and match.group(1) in declared:
            evaluated[match.group(1)] = match.group(2).upper() in ("ON", "TRUE", "1", "YES", "Y")
    unset = sorted(set(evaluated) - set(options))
    if unset:
        raise RecipeError("upstream options left at an unreviewed default: " + ", ".join(unset))
    differs = sorted(n for n, v in evaluated.items() if v != (options[n] == "ON"))
    if differs:
        raise RecipeError("evaluated option differs from the recipe: " + ", ".join(differs))
    unknown = sorted(set(options) - declared)
    if unknown:
        raise RecipeError("recipe option is not declared upstream: " + ", ".join(unknown))
    return {"declared": len(declared), "evaluated": sorted(evaluated)}


def run(argv, cwd, env, log):
    with open(log, "a", encoding="utf-8") as stream:
        stream.write("$ " + " ".join(argv) + "\n")
        stream.flush()
        result = subprocess.run(argv, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RecipeError("step failed (" + str(result.returncode) + "): " + " ".join(argv[:4]))


def expand(argv, values):
    out = []
    for item in argv:
        for key, value in values.items():
            item = item.replace("{" + key + "}", str(value))
        out.append(item)
    return out


def tree_files(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() or p.is_symlink())


def _tool(argv):
    return subprocess.run(argv, capture_output=True, text=True, check=True).stdout


def run_checks(recipe, root):
    results = []
    for check in recipe["checks"]:
        kind = check["kind"]
        if kind in ("forbid_paths", "require_paths"):
            hits = [f for f in tree_files(root) if any(fnmatch.fnmatchcase(f, g) for g in check["globs"])]
            if (kind == "forbid_paths") == bool(hits):
                raise RecipeError(kind + " failed: " + (", ".join(hits[:5]) if hits else ", ".join(check["globs"])))
            results.append({"check": kind, "globs": check["globs"], "status": "CI_PASS"})
            continue
        target = root / check["file"]
        if not target.is_file():
            raise RecipeError(kind + ": missing " + check["file"])
        if kind == "soname":
            found = re.findall(r"Library soname: \[([^\]]+)\]", _tool(["readelf", "-d", str(target)]))
            if found != [check["equals"]]:
                raise RecipeError("SONAME is " + repr(found) + ", not " + check["equals"])
        elif kind == "export_count":
            symbols = [line.split()[-1] for line in _tool(["nm", "-D", "--defined-only", str(target)]).splitlines() if line.strip()]
            count = sum(s.startswith(check["prefix"]) for s in symbols)
            if count != check["equals"]:
                raise RecipeError("exported " + check["prefix"] + "* count is " + str(count) + ", not " + str(check["equals"]))
        else:
            text = _tool(["strings", "-a", str(target)]).lower()
            hits = [s for s in check["substrings"] if s.lower() in text]
            if hits:
                raise RecipeError("forbidden text in " + check["file"] + ": " + ", ".join(hits))
        results.append({"check": kind, "file": check["file"], "status": "CI_PASS"})
    return results


def assign(recipe, root):
    """{package: [files]}: every staged file in exactly one package or in a reasoned drop."""
    owners = {}
    for relative in tree_files(root):
        if any(fnmatch.fnmatchcase(relative, d["glob"]) for d in recipe["drop"]):
            continue
        hits = [p["name"] for p in recipe["packages"] if any(fnmatch.fnmatchcase(relative, g) for g in p["files"])]
        if len(hits) != 1:
            raise RecipeError(("unclaimed" if not hits else "doubly claimed") + " staged file: " + relative)
        owners.setdefault(hits[0], []).append(relative)
    for package in recipe["packages"]:
        if package["name"] not in owners:
            raise RecipeError("package would be empty: " + package["name"])
    return owners


def shlibs_depends(package_root, staged, own_sonames, scratch):
    """dpkg-shlibdeps for the package's ELF files; libraries of this build map to (= version)."""
    elves = [p for p in sorted(package_root.rglob("*")) if p.is_file() and not p.is_symlink() and p.read_bytes()[:4] == b"\x7fELF"]
    if not elves:
        return ""
    debian = scratch / "debian"
    debian.mkdir(parents=True, exist_ok=True)
    (debian / "control").write_text("Source: srrx-lab\n\nPackage: srrx-lab\nArchitecture: any\n", encoding="utf-8")
    (debian / "shlibs.local").write_text("".join(own_sonames), encoding="utf-8")
    libdirs = sorted({str(p) for p in staged.rglob("*") if p.is_dir() and any(c.name.startswith("lib") and ".so" in c.name for c in p.iterdir())})
    out = subprocess.run(["dpkg-shlibdeps", "-O", "--ignore-missing-info"] + ["-l" + d for d in libdirs] + ["-e" + str(e) for e in elves],
                         cwd=scratch, capture_output=True, text=True)
    if out.returncode:
        raise RecipeError("dpkg-shlibdeps failed: " + out.stderr.strip()[-400:])
    for line in out.stdout.splitlines():
        if line.startswith("shlibs:Depends="):
            return line.partition("=")[2].strip()
    return ""


def package_manifest(root):
    """verify_build manifest of one package's data tree: status OPEN, filled for a reviewer."""
    files, modules = {}, []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() and path.resolve().is_dir():
            files[relative] = "symlink:" + path.resolve().relative_to(root.resolve()).as_posix()
        elif path.is_file():
            files[relative] = deploy.sha(path)
            if ".so" in path.name:
                modules.append(relative)
    return {"schema_version": 1, "status": "OPEN", "files": files, "allowed_modules": sorted(modules),
            "source_audit": {"status": "OPEN", "report": {"path": None, "sha256": None}},
            "tx_negative_tests": {"status": "OPEN", "report": {"path": None, "sha256": None}}}


def build_deb(package, version, files, staged, epoch, depends, out, scratch):
    root = scratch / ("pkg-" + package["name"])
    for relative in files:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        source = staged / relative
        if source.is_symlink():
            os.symlink(os.readlink(source), target)
        else:
            shutil.copyfile(source, target)
            # Shared objects are 0644 (Debian policy 8.1); only real executables keep 0755.
            os.chmod(target, 0o755 if os.access(source, os.X_OK) and ".so" not in source.name else 0o644)
    manifest = package_manifest(root)
    control = root / "DEBIAN"
    control.mkdir()
    size_kib = (sum((root / f).stat().st_size for f in files if not (root / f).is_symlink()) + 1023) // 1024
    relations = [d.strip() for d in depends.split(",") if d.strip()]
    relations += [d for d in (x.replace("{version}", version) for x in package["depends"]) if d not in relations]
    fields = [("Package", package["name"]), ("Version", version), ("Architecture", "arm64"), ("Maintainer", MAINTAINER),
              ("Installed-Size", str(size_kib)), ("Depends", ", ".join(relations)),
              ("Section", package["section"]), ("Priority", "optional"),
              ("Description", package["description"].split("\n")[0] + "\n SR-RX-v2.1 receive-only +lab build (deployment/recipes/README.md).")]
    (control / "control").write_text("".join(k + ": " + v + "\n" for k, v in fields if v), encoding="utf-8", newline="\n")
    sums = [hashlib.md5((root / f).read_bytes(), usedforsecurity=False).hexdigest() + "  " + f + "\n"
            for f in sorted(files) if not (root / f).is_symlink()]
    (control / "md5sums").write_text("".join(sums), encoding="utf-8", newline="\n")
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_dir() and not path.is_symlink():
            os.chmod(path, 0o755)
        if path.name in ("control", "md5sums") and path.parent == control:
            os.chmod(path, 0o644)
        os.utime(path, (epoch, epoch), follow_symlinks=False)
    os.utime(root, (epoch, epoch))
    deb = out / (package["name"] + "_" + version + "_arm64.deb")
    subprocess.run(["dpkg-deb", "--root-owner-group", "-Zxz", "--build", str(root), str(deb)], check=True,
                   capture_output=True, env=dict(os.environ, SOURCE_DATE_EPOCH=str(epoch)))
    return deb, manifest


def build(recipe_path, archive, work, out, jobs):
    recipe = deploy.load(recipe_path)
    component = validate_recipe(recipe)
    lock = deploy.load(DEPLOYMENT / "sources.lock.json")
    network = no_network()
    work, out = Path(work), Path(out)
    for path in (work, out):
        if path.exists() and any(path.iterdir()):
            raise RecipeError("work and output directories must be new or empty")
        path.mkdir(parents=True, exist_ok=True)
    src, build_dir, destdir, log = work / "src", work / "build", work / "destdir", out / (recipe["component"] + ".build.log")
    receipt = extract(archive, component, src, recipe["source"]["patch"])
    epoch = source_date_epoch(archive)
    env = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": str(work), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
           "SOURCE_DATE_EPOCH": str(epoch), "TZ": "UTC"}
    values = {"src": src, "build": build_dir, "destdir": destdir, "jobs": jobs}
    cmake = recipe["cmake"]
    configure = expand(cmake["configure"], values) + ["-D%s=%s" % (k, v) for k, v in sorted({**cmake["variables"], **cmake["options"]}.items())]
    run(configure, work, env, log)
    options = check_options(src, build_dir, cmake["options"])
    for step in recipe["build"]:
        run(expand(step, values), work, env, log)
    destdir.mkdir()
    if recipe["install"]["cmake_install"]:
        run(["cmake", "--install", str(build_dir)], work, dict(env, DESTDIR=str(destdir)), log)
    for item in recipe["install"]["copy"]:
        matches = sorted(glob.glob(expand([item["from"]], values)[0]))
        if not matches:
            raise RecipeError("install copy matched nothing: " + item["from"])
        target = destdir / item["to"]
        target.mkdir(parents=True, exist_ok=True)
        for match in matches:
            if os.path.islink(match):
                os.symlink(os.readlink(match), target / os.path.basename(match))
            else:
                shutil.copy2(match, target / os.path.basename(match))
    checks = run_checks(recipe, destdir)
    bad = [f for f in tree_files(destdir) if any(part.lower() in deploy.BAD_PARTS for part in f.split("/"))
           or f.rsplit("/", 1)[-1].lower() in deploy.forbidden_basenames()]
    if bad:
        raise RecipeError("TX/control executable or plugin staged: " + ", ".join(bad[:5]))
    owners = assign(recipe, destdir)
    version = component["version"]
    own = []
    for package in recipe["packages"]:
        for relative in owners[package["name"]]:
            path = destdir / relative
            if path.is_file() and not path.is_symlink() and ".so" in path.name and path.read_bytes()[:4] == b"\x7fELF":
                for soname in re.findall(r"Library soname: \[([^\]]+)\]", _tool(["readelf", "-d", str(path)])):
                    match = re.fullmatch(r"(.+)\.so\.(.+)", soname)
                    if match:
                        own.append("%s %s %s (= %s)\n" % (match.group(1), match.group(2), package["name"], version))
    packages = []
    for package in recipe["packages"]:
        scratch = work / ("deb-" + package["name"])
        scratch.mkdir()
        files = owners[package["name"]]
        depends = ""
        if package["shlibs_depends"]:
            stage = scratch / "shlibs-root"
            for relative in files:
                (stage / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destdir / relative, stage / relative, follow_symlinks=False)
            depends = shlibs_depends(stage, destdir, own, scratch)
        deb, manifest = build_deb(package, version, files, destdir, epoch, depends, out, scratch)
        manifest_path = out / (package["name"] + ".build-manifest.json")
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        packages.append({"package": package["name"], "version": version, "architecture": "arm64", "filename": deb.name,
                         "sha256": deploy.sha(deb), "size": deb.stat().st_size, "build_manifest_sha256": deploy.sha(manifest_path)})
    dpkg_list = subprocess.run(["dpkg-query", "-W", "-f", "${Package} ${Version} ${Architecture}\\n"], capture_output=True, text=True, check=True).stdout
    environment = "".join(sorted(dpkg_list.splitlines(keepends=True)))
    (out / (recipe["component"] + ".chroot-packages.txt")).write_text(environment, encoding="utf-8", newline="\n")
    record = {"schema_version": 1, "kind": "srrx_lab_build_record", "status": "CI_BUILT_UNREVIEWED", "component": recipe["component"],
              "version": version, "recipe_sha256": deploy.sha(recipe_path), "source_archive_sha256": component["source_archive_sha256"],
              "apt_snapshot": lock["apt_snapshot"]["timestamp"],
              "build_environment": {"chroot_packages_sha256": hashlib.sha256(environment.encode()).hexdigest(),
                                    "chroot_package_count": len(environment.splitlines()), "network": network,
                                    "source_date_epoch": epoch, "patch_receipt": receipt, "cmake_options": options},
              "packages": packages, "checks": checks, "hardware_ready": False}
    (out / (recipe["component"] + ".build-record.json")).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    try:
        record = build(args.recipe, args.archive, args.work, args.out, args.jobs)
    except (OSError, ValueError, subprocess.SubprocessError, tarfile.TarError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps({k: record[k] for k in ("component", "version", "status", "packages")}, indent=2))


if __name__ == "__main__":
    main()
