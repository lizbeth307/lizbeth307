#!/usr/bin/env python3
"""CI checks around the lab builder output and a published lab repository (repo/README.md).

`packages`: every .deb of every build record has the recorded SHA-256/size and control fields,
its extracted data tree, walked by deploy.build_inventory (the walk verify_build compares), equals
the package's verify_build manifest (an empty file list where that walk refuses the tree, as
build_recipe.package_manifest writes it: a -dev .so link into another package, Lime), a package with a public
SONAME'd library carries DEBIAN/shlibs and the ldconfig trigger, and deploy.verify_build still
refuses the manifest because it is OPEN (a reviewer, never CI, sets REVIEWED). Each record is
bound to this tree as deploy.verify_repo binds it (recipe, -rx-only patch, one receipt per listed
patch, source member, the recipe files and hooks of the recipe), and a package hook output it names must have the recorded
SHA-256 and carry the record's record_digests. Every package, -dev and Lime included, has its
<package>.data-tree.json with the recorded data_tree_sha256, and both readers of the .deb (Python
deploy.deb_data_inventory and the dpkg-deb extraction) give exactly its entries (DATA_TREE_MATCH).
Each lab package a record's build_environment.lab_build_depends names is one of these packages,
byte for byte (lab_depends_published: a heavy job's rebuilt chain cannot publish against other bytes).
`publishable`: the .deb files a lab repository may carry now (no deploy.lab_package_issues
finding: Lime while Lime is disabled, Soapy modules outside the allowlist, TX/control tools); the
others are listed as held back with their findings.
`tamper`: the published repository passes deploy.verify_repo, and each tampered copy (index,
pool, keyring, InRelease pin, build record, recipe, patch, listed-patch receipts, source member,
recipe files, hooks, apt entry, held package, data trees, release path with CI records or OPEN manifests, a repository
holding the held-back Lime packages) is refused.
The sr-rx-packages.yml jobs (recipes/README.md): `plan` (which recipes this run builds, in which
job: build_recipe.ci_plan plus the heavy-job selection), `tag-samples` (the paths recipes declare
in ci.tag_samples, from a clone of the component's tag that must be the locked commit),
`runtime-check` (one fresh chroot per job from the pinned snapshot, the job's runtime packages
installed offline, a probe and each recipe's runtime_check.py under unshare --net),
`tarball-vs-tag` (every lock entry with a tag and no git tree: its release tarball against the
tag tree, reported) and `chains` (a heavy job's rebuilt lab_build_depends against the published
bytes, reported; the bytes a published package was built against are a gate in `packages`).
Read-only for its inputs; writes only into new temporary or named output directories. CI
evidence only: no review, no TX proof, no hardware test.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.dont_write_bytecode = True
DEPLOYMENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT))
import deploy  # noqa: E402
import fetch_sources  # noqa: E402
sys.path.insert(0, str(DEPLOYMENT / "recipes"))
import build_recipe  # noqa: E402
import lab_build  # noqa: E402

PUBLIC_LIBRARY = re.compile(r"usr/lib/aarch64-linux-gnu/[^/]+\.so\.[^/]+")
# Repository-relative paths (git diff --no-renames --name-only) of the push range against which
# heavy jobs are selected: the files every recipe build goes through (receive-only-policy.json:
# its forbidden_basenames refuse a staged tree in build_recipe.build), then per chain recipe its
# directory, its -rx-only patch and its sources.lock.json entry, and the lock's apt_snapshot
# (heavy_selection). deploy.py is not one: a heavy package meets a changed deploy.py only in a
# [lab-build-all] run (the landing commit).
PROJECT_PREFIX = DEPLOYMENT.parent.name + "/"
BUILDER_INPUTS = (".github/workflows/sr-rx-packages.yml",) + tuple(PROJECT_PREFIX + "deployment/" + p for p in (
    "recipes/build_recipe.py", "recipes/lab_build.py", "vendor_patch.py", "patches/target-hashes.json", "receive-only-policy.json"))
# The one commit-message token: fixed text, matched in Python on the message passed through env.
LAB_BUILD_ALL = re.compile(r"\[lab-build-all\]")
TAG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+/-]*")
ARCHIVE_SUFFIXES = (".tar.gz", ".tgz", ".tar.xz", ".tar.bz2", ".tar")


class CheckError(ValueError):
    pass


def field(deb, name):
    return subprocess.run(["dpkg-deb", "--field", str(deb), name], capture_output=True, text=True, check=True).stdout.strip()


def records(out):
    found = sorted(Path(out).glob("*/*.build-record.json"))
    if not found:
        raise CheckError("no build records under " + str(out))
    return found


def recorded_deb(record_path, package):
    deb = record_path.parent / package["filename"]
    if deploy.sha(deb) != package["sha256"] or deb.stat().st_size != package["size"]:
        raise CheckError("deb differs from its build record: " + deb.name)
    return deb


def record_binding(record_path, record):
    """deploy._record_binding for one record, plus its package hook output (when the record names
    one): the file next to the record has the recorded SHA-256 and the record's record_digests."""
    try:
        deploy._record_binding(record, record_path.name)
    except deploy.DeploymentError as exc:
        raise CheckError(str(exc)) from exc
    environment = record["build_environment"]
    hooks = [h for h in environment.get("hooks", []) if type(h) is dict and "output" in h]
    for hook in hooks:
        output = record_path.parent / hook["output"]
        if Path(hook["output"]).name != hook["output"] or not output.is_file() or deploy.sha(output) != hook.get("output_sha256"):
            raise CheckError("package hook output differs from its build record: " + hook["output"])
        data = deploy.load(output)
        if type(data) is not dict or data.get("record_digests") != record.get("record_digests"):
            raise CheckError("build record record_digests differ from the package hook output: " + record_path.name)
    if "record_digests" in record and not hooks:
        raise CheckError("build record carries record_digests without a package hook output: " + record_path.name)
    return {"component": record["component"], "patch_receipts": len(environment.get("patch_receipts", [])),
            "source_member": (environment.get("source_member") or {}).get("path"), "record_digests": "record_digests" in record}


def lab_depends_published(out):
    """Each record's build_environment.lab_build_depends (the lab packages its chroot installed)
    against the packages of the records under out, the ones this run publishes: the same name,
    version, component and SHA-256, or a refusal. So a heavy job, which rebuilt its chain on
    another runner, cannot publish a package built against bytes the repository does not carry.
    A differing record_sha256 with the same bytes is only reported (record_equal false)."""
    published = {}
    for record_path in records(out):
        record = deploy.load(record_path)
        for package in record["packages"]:
            published[package["package"]] = {"version": package["version"], "component": record["component"],
                                             "sha256": package["sha256"], "record_sha256": deploy.sha(record_path)}
    result = []
    for record_path in records(out):
        record = deploy.load(record_path)
        installed = record["build_environment"].get("lab_build_depends", [])
        if type(installed) is not list:
            raise CheckError("build record lab_build_depends is not a list: " + record_path.name)
        for item in installed:
            name = item.get("package") if type(item) is dict else None
            have = published.get(name)
            if have is None or any(item.get(k) != have[k] for k in ("version", "component", "sha256")):
                raise CheckError("%s was built against lab package %s bytes this run does not publish (%s)"
                                 % (record_path.name, name, "no record builds it" if have is None else "SHA-256 %s, published %s"
                                    % (str(item.get("sha256"))[:12], have["sha256"][:12])))
            result.append({"component": record["component"], "package": name, "sha256": item["sha256"],
                           "record_equal": item.get("record_sha256") == have["record_sha256"]})
    return result


def packages(out):
    summary, bound = [], []
    for record_path in records(out):
        record = deploy.load(record_path)
        bound.append(record_binding(record_path, record))
        for package in record["packages"]:
            deb = recorded_deb(record_path, package)
            for name, expected in (("Package", package["package"]), ("Version", package["version"]), ("Architecture", package["architecture"])):
                if field(deb, name) != expected:
                    raise CheckError(deb.name + " control " + name + " differs")
            manifest_path = record_path.parent / (package["package"] + ".build-manifest.json")
            if deploy.sha(manifest_path) != package["build_manifest_sha256"]:
                raise CheckError("build manifest differs from its record: " + manifest_path.name)
            manifest = deploy.load(manifest_path)
            if "data_tree_sha256" not in package:
                raise CheckError("build record lists no data tree for " + package["package"] + ": " + record_path.name)
            try:
                entries = deploy._data_tree(record_path.parent / (package["package"] + ".data-tree.json"), package["data_tree_sha256"],
                                            package["package"], package["version"])
            except deploy.DeploymentError as exc:
                raise CheckError(str(exc)) from exc
            if deploy.deb_data_inventory(deb) != entries:
                raise CheckError(deb.name + " differs from its data tree (deploy.deb_data_inventory)")
            with tempfile.TemporaryDirectory(prefix="srrx-deb-") as temporary:
                root, control = Path(temporary) / "data", Path(temporary) / "control"
                subprocess.run(["dpkg-deb", "-x", str(deb), str(root)], check=True)
                subprocess.run(["dpkg-deb", "-e", str(deb), str(control)], check=True)
                files = {}
                for path in sorted(root.rglob("*")):
                    if path.is_file():
                        files[path.relative_to(root).as_posix()] = deploy.sha(path)
                if build_recipe.package_data_tree(root) != entries:
                    raise CheckError("extracted " + deb.name + " differs from its data tree (dpkg-deb -x)")
                refusal = build_recipe.inventory_refusal(root)
                if ({} if refusal else deploy.build_inventory(root)[0]) != manifest["files"]:
                    raise CheckError("extracted " + deb.name + " differs from its build manifest")
                libraries = [f for f in files if PUBLIC_LIBRARY.fullmatch(f)]
                shlibs = (control / "shlibs").read_text(encoding="utf-8").splitlines() if (control / "shlibs").is_file() else []
                trigger = (control / "triggers").read_text(encoding="utf-8") if (control / "triggers").is_file() else ""
                if libraries and (not shlibs or trigger != "activate-noawait ldconfig\n"):
                    raise CheckError(deb.name + " ships a shared library without DEBIAN/shlibs or the ldconfig trigger")
                if (shlibs or trigger) and not libraries:
                    raise CheckError(deb.name + " has shlibs/triggers but no public shared library")
                try:
                    deploy.verify_build(root, manifest)
                except deploy.DeploymentError as exc:
                    if "OPEN/unreviewed" not in str(exc):
                        raise CheckError("verify_build gave another refusal for " + deb.name + ": " + str(exc)) from exc
                else:
                    raise CheckError("verify_build accepted a CI manifest: " + deb.name)
            summary.append({"package": package["package"], "version": package["version"], "files": len(files),
                            "sha256": package["sha256"], "shlibs": shlibs, "verify_build": "REFUSED_OPEN_AS_EXPECTED",
                            "manifest_files": "NONE: " + refusal if refusal else "BUILD_INVENTORY_MATCH",
                            "data_tree": "DATA_TREE_MATCH", "data_tree_entries": len(entries)})
    return {"status": "CI_PACKAGES_MATCH_BUILD_RECORDS", "packages": summary, "records": bound,
            "lab_build_depends": lab_depends_published(out), "hardware_ready": False}


def publishable(out):
    publish, held = [], []
    for record_path in records(out):
        for package in deploy.load(record_path)["packages"]:
            deb = recorded_deb(record_path, package)
            issues = deploy.lab_package_issues(deploy.deb_data_tree(deb))
            if issues:
                held.append({"package": package["package"], "findings": issues})
            else:
                publish.append(str(deb))
    if not publish:
        raise CheckError("no built package may enter the lab repository")
    return {"status": "LAB_REPOSITORY_SELECTION", "publish": publish, "held_back": held, "hardware_ready": False,
            "scope": "Named receive-only content rules (deploy.lab_package_issues); held-back packages stay CI artifacts."}


def tamper(repo, keyring, wrong_keyring, fingerprint, record_paths, sources_entry, full_repo=None):
    repo = Path(repo).resolve(strict=True)
    good = deploy.verify_repo(repo, keyring, fingerprint, record_paths, sources_entry)
    pinned = good["inrelease_sha256"]
    first_deb = sorted(Path(repo).rglob("*.deb"))[0]
    name = first_deb.name.split("_")[0]
    cases = {}

    def expect(label, needle, change=None, **overrides):
        with tempfile.TemporaryDirectory(prefix="srrx-tamper-") as temporary:
            copy = Path(temporary) / "repo"
            shutil.copytree(repo, copy, symlinks=True)
            arguments = {"repo": copy, "keyring": keyring, "fingerprint": fingerprint, "build_records": record_paths,
                         "sources_entry": sources_entry, "inrelease_sha256": pinned, "target_status": None, "release": False}
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

    def edited_records(change_record, change_manifest=None, release=False, change_tree=None):
        """Copies of the build records (and their manifests and data trees) with one change each."""
        def change(_, temporary, arguments):
            copies = []
            for record_path in record_paths:
                target = temporary / "records" / Path(record_path).parent.name
                target.mkdir(parents=True)
                record = deploy.load(record_path)
                for package in record["packages"]:
                    manifest = Path(record_path).parent / (package["package"] + ".build-manifest.json")
                    shutil.copyfile(manifest, target / manifest.name)
                    if change_manifest:
                        change_manifest(target / manifest.name)
                    tree = Path(record_path).parent / (package["package"] + ".data-tree.json")
                    if tree.is_file():
                        shutil.copyfile(tree, target / tree.name)
                    if change_tree:
                        change_tree(package, target / tree.name)
                change_record(record)
                copies.append(target / Path(record_path).name)
                copies[-1].write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            arguments.update(build_records=copies, release=release)
        return change

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

    def other_recipe(record):
        record["recipe_sha256"] = "0" * 64

    def other_patch(record):
        record["build_environment"]["patch_receipt"]["patch_sha256"] = "0" * 64

    def other_patch_list(record):
        record["build_environment"].setdefault("patch_receipts", []).append({"file": "patches/0001-not-in-the-recipe.patch",
                                                                              "sha256": "0" * 64, "strip": 1})

    def other_member(record):
        record["build_environment"]["source_member"] = {"path": "not-in-the-recipe/src/inner.tgz", "sha256": "0" * 64}

    def other_recipe_files(record):
        record["build_environment"]["recipe_files"] = {"check_recipe.py": "0" * 64}

    def other_hooks(record):
        record["build_environment"]["hooks"] = [{"hook": "package", "argv": ["python3", "-I", "{recipe}/check_recipe.py", "package"],
                                                 "script_sha256": "0" * 64, "status": "CI_PASS", "report": {"ok": True, "findings": []}}]

    def reviewed(record):
        record["status"] = "REVIEWED"

    def reviewed_other_manifest(record):
        record["status"] = "REVIEWED"
        for package in record["packages"]:
            package["build_manifest_sha256"] = "0" * 64

    expect("modified Packages index", "index differs from the signed Release", packages_index)
    expect("extra .deb in the pool", "pool holds a file", extra_deb)
    expect("changed .deb bytes", "pool .deb differs", swapped_deb)
    expect("wrong keyring", "not a good signature", keyring=wrong_keyring)
    expect("other InRelease pinned", "InRelease differs", inrelease_sha256="0" * 64)
    expect("package without build record", "not one of the build records", build_records=[])
    expect("apt entry without Signed-By", "Signed-By", no_signed_by)
    expect("held package would change", "held package", held)
    expect("build record from another recipe", "another recipe", edited_records(other_recipe))
    expect("build record with another patch", "patch differs", edited_records(other_patch))
    expect("build record with another listed-patch list", "patch list differs", edited_records(other_patch_list))
    expect("build record with another source member", "source member differs", edited_records(other_member))
    expect("build record with other recipe files", "recipe files differ", edited_records(other_recipe_files))
    expect("build record with other hooks", "hooks differ", edited_records(other_hooks))
    expect("release path with CI_BUILT_UNREVIEWED records", "REVIEWED build record", release=True)
    expect("release path with OPEN package manifests", "OPEN/unreviewed", edited_records(reviewed, release=True))
    expect("release path with another manifest", "build manifest differs", edited_records(reviewed_other_manifest, release=True))
    if all("data_tree_sha256" in p for r in record_paths for p in deploy.load(r)["packages"]):
        # The data tree of one published package (a -dev one where published), edited as if the .deb
        # content had changed: rebound to the record (the tree check refuses) or not (the hash does).
        published = {p.name.split("_")[0] for p in Path(repo).rglob("*.deb")}
        with_files = sorted(p["package"] for r in record_paths for p in deploy.load(r)["packages"] if p["package"] in published and any(
            e["type"] == "file" for e in deploy.load(Path(r).parent / (p["package"] + ".data-tree.json"))["entries"].values()))
        victim = next((n for n in with_files if n.endswith("-dev")), with_files[0])

        def tree(edit, rebind=True):
            def change_tree(package, path):
                if package["package"] != victim:
                    return
                document = json.loads(path.read_text(encoding="utf-8"))
                edit(document)
                path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                if rebind:
                    package["data_tree_sha256"] = deploy.sha(path)
            return edited_records(lambda record: None, change_tree=change_tree)

        def first(document, kinds):
            return next(e for _, e in sorted(document["entries"].items()) if e["type"] in kinds)

        def one_byte(document):
            first(document, ("file",))["sha256"] = hashlib.sha256(b"a file with one byte changed").hexdigest()

        def other_mode(document):
            entry = first(document, ("file", "dir"))
            entry["mode"] = "0755" if entry["mode"] != "0755" else "0644"

        def unlisted(document):
            document["entries"]["usr/share/doc/" + victim + "/unlisted"] = {"type": "file", "sha256": "0" * 64, "mode": "0644"}

        def unbound_tree(record):
            for package in record["packages"]:
                if package["package"] == victim:
                    package.pop("data_tree_sha256")
        expect("data tree with one changed file hash (" + victim + ")", "data tree differs from the build record data tree", tree(one_byte))
        expect("data tree with another mode (" + victim + ")", "data tree differs from the build record data tree", tree(other_mode))
        expect("data tree with an extra path (" + victim + ")", "data tree differs from the build record data tree", tree(unlisted))
        expect("data tree changed after the record (" + victim + ")", "package data tree differs from the build record", tree(one_byte, rebind=False))
        expect("data tree of another package (" + victim + ")", "names another package", tree(lambda d: d.update(package=victim + "-other")))
        expect("data tree file missing (" + victim + ")", "package data tree differs from the build record",
               edited_records(lambda record: None, change_tree=lambda package, path: path.unlink() if package["package"] == victim else None))
        if any(len(deploy.load(r)["packages"]) > 1 and victim in [p["package"] for p in deploy.load(r)["packages"]] for r in record_paths):
            expect("record without the data tree of one package (" + victim + ")", "data tree for some packages only", edited_records(unbound_tree))
    if full_repo is not None:
        def full(_, __, arguments):
            arguments.update(repo=Path(full_repo).resolve(strict=True), inrelease_sha256=None)
        expect("repository with the held-back Lime packages", "receive-only policy refuses the contents", full)
    return {"status": "TAMPER_CASES_REFUSED", "untampered": good["status"], "cases": cases, "hardware_ready": False}


# --- sr-rx-packages.yml: recipe plan, heavy jobs, tag samples ----------------------------------

def heavy_selection(plan, changed, lock_before, lock, build_all=False):
    """{id: reason} of the heavy recipes (build_recipe.ci_plan) this run builds. build_all (the
    [lab-build-all] token, a dispatch input): all of them. Otherwise one runs when a changed path
    of the push range (repository-relative) is a builder input (BUILDER_INPUTS), lies in
    deployment/recipes/<x>/ or is deployment/patches/<x>-rx-only.patch of a recipe x of its chain,
    or when the sources.lock.json entry of a chain component, or the lock's apt_snapshot (every
    chroot comes from it), differs from lock_before (the lock at the start of the range; {} if it
    had none). changed None: an unknown range, all of them."""
    selected = {}
    lock_path = PROJECT_PREFIX + "deployment/sources.lock.json"
    before = {c["id"]: c for c in (lock_before or {}).get("components", [])}
    after = {c["id"]: c for c in lock["components"]}
    for name in plan["heavy"]:
        chain = plan["recipes"][name]["chain"]
        if build_all or changed is None:
            selected[name] = "[lab-build-all]" if build_all else "push range unknown"
            continue
        prefixes = tuple(PROJECT_PREFIX + "deployment/recipes/" + x + "/" for x in chain)
        patches = {PROJECT_PREFIX + "deployment/patches/" + x + "-rx-only.patch" for x in chain}
        hit = next((p for p in changed if p in BUILDER_INPUTS or p in patches or p.startswith(prefixes)), None)
        if hit is None and lock_path in changed:
            hit = next((lock_path + " entry " + x for x in chain if before.get(x) != after.get(x)), None)
            if hit is None and (lock_before or {}).get("apt_snapshot") != lock.get("apt_snapshot"):
                hit = "sources.lock.json apt_snapshot"
        if hit is not None:
            selected[name] = "changed: " + hit
    return selected


def plan(changed=None, lock_before=None, build_all=False, lock=None):
    """The sr-rx-packages.yml build plan: build_recipe.ci_plan plus the heavy recipes this run builds."""
    lock = lock or deploy.load(DEPLOYMENT / "sources.lock.json")
    result = build_recipe.ci_plan(lock)
    if not result["light"]:
        raise CheckError("no light recipe to build")
    reasons = heavy_selection(result, changed, lock_before, lock, build_all)
    heavy_run = [n for n in result["heavy"] if n in reasons]
    return {"status": "CI_RECIPE_PLAN", **result, "heavy_run": heavy_run, "heavy_reasons": reasons,
            "build": result["light"] + heavy_run, "build_all": bool(build_all), "hardware_ready": False}


def github_outputs(result):
    """Step outputs of the plan job (one line each; the matrix as compact JSON)."""
    matrix = [{"recipe": n, "chain": " ".join(result["recipes"][n]["chain"])} for n in result["heavy_run"]]
    return "".join(line + "\n" for line in ("light=" + " ".join(result["light"]), "heavy_matrix=" + json.dumps(matrix, separators=(",", ":")),
                                            "heavy_count=%d" % len(matrix), "build=" + " ".join(result["build"])))


def _git(args, cwd):
    return subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def clone_tag(component, target, checkout=True):
    """A depth-1 clone of the component's lock tag from its https upstream_url; returns HEAD."""
    url, tag = component.get("upstream_url"), component.get("tag")
    if type(url) is not str or not url.startswith("https://") or type(tag) is not str or not TAG.fullmatch(tag):
        raise CheckError("lock component needs an https upstream_url and a tag: " + component["id"])
    subprocess.run(["git", "-c", "advice.detachedHead=false", "clone", "-q", "--depth", "1", "--single-branch", "--branch", tag]
                   + ([] if checkout else ["--no-checkout"]) + ["--", url, str(target)], check=True)
    return _git(["rev-parse", "HEAD"], target)


def export_tag_samples(clone, component, paths, target):
    """The declared ci.tag_samples paths of a checked-out tag clone, copied under target, when the
    clone is the locked commit. Returns {component, tag, commit, paths: {path: git object id}}."""
    commit = _git(["rev-parse", "HEAD"], clone)
    if commit != component.get("commit"):
        raise CheckError("tag %s of %s is commit %s, not the locked %s" % (component.get("tag"), component["id"], commit, component.get("commit")))
    objects = {}
    for path in paths:
        try:
            objects[path] = _git(["rev-parse", "--verify", "-q", "HEAD:" + path], clone)
        except subprocess.CalledProcessError as exc:
            raise CheckError("tag tree of " + component["id"] + " has no " + path) from exc
        source, destination = Path(clone) / path, Path(target) / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir() and not source.is_symlink():
            shutil.copytree(source, destination, symlinks=True)
        else:
            shutil.copy2(source, destination, follow_symlinks=False)
    return {"component": component["id"], "tag": component["tag"], "commit": commit, "upstream_url": component["upstream_url"],
            "paths": objects, "hardware_ready": False}


def tag_samples(out, lock=None):
    """For every recipe that declares ci.tag_samples: <id>/<path> and <id>.tag-samples.json under
    out (a new directory), from a clone of its component's tag; index.json lists them (always written)."""
    lock = lock or deploy.load(DEPLOYMENT / "sources.lock.json")
    result, components = build_recipe.ci_plan(lock), {c["id"]: c for c in lock["components"]}
    out = Path(out)
    out.mkdir(parents=True)
    index = {}
    for name in result["light"] + result["heavy"]:
        paths = result["recipes"][name]["tag_samples"]
        if not paths:
            continue
        with tempfile.TemporaryDirectory(prefix="srrx-tag-") as temporary:
            clone_tag(components[name], Path(temporary) / "clone")
            index[name] = export_tag_samples(Path(temporary) / "clone", components[name], paths, out / name)
        (out / (name + ".tag-samples.json")).write_text(json.dumps(index[name], indent=2) + "\n", encoding="utf-8")
    report = {"status": "TAG_SAMPLES_EXPORTED" if index else "NO_TAG_SAMPLES_DECLARED", "recipes": index, "hardware_ready": False}
    (out / "index.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


# --- release tarballs against their tag tree (sources job, reported) ----------------------------

def release_tarballs(lock):
    """Lock entries compared with their tag: a resolved archive with a tag and no git_tree_sha1
    (not a git archive; fetch_sources.py tree lists it under skipped)."""
    return [c for c in lock["components"] if c["source_archive_sha256"] is not None and type(c.get("tag")) is str and not c.get("git_tree_sha1")]


def _blob(size, chunks):
    digest = hashlib.sha1(b"blob %d\0" % size)
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest()


def tar_entries(archive):
    """{path: (git mode, blob id)} below the one root directory of a tarball (any compression),
    directories left out as git leaves them out; returns (entries, root)."""
    entries, root = {}, None
    with tarfile.open(archive, "r:*") as stream:
        for member in stream:
            parts = [p for p in member.name.split("/") if p not in ("", ".")]
            if not parts:
                continue
            root = parts[0] if root is None else root
            if parts[0] != root or ".." in parts:
                raise CheckError("archive is not one safe root: " + Path(archive).name)
            relative = "/".join(parts[1:])
            if not relative or member.isdir():
                continue
            if member.issym():
                entries[relative] = ("120000", _blob(len(member.linkname.encode()), [member.linkname.encode()]))
            elif member.isfile():
                source = stream.extractfile(member)
                entries[relative] = ("100755" if member.mode & 0o111 else "100644", _blob(member.size, iter(lambda: source.read(1024 * 1024), b"")))
            elif member.islnk():  # a hard link carries no size of its own: the linked file's bytes
                data = stream.extractfile(member).read()
                entries[relative] = ("100755" if member.mode & 0o111 else "100644", _blob(len(data), [data]))
            else:
                raise CheckError("archive member is neither file, directory nor symlink: " + member.name)
    return entries, root


def tag_entries(clone):
    """{path: (mode, object id)} of the clone's HEAD tree (git ls-tree -r; a submodule is 160000)."""
    out = subprocess.run(["git", "ls-tree", "-r", "-z", "--full-tree", "HEAD"], cwd=clone, capture_output=True, check=True).stdout
    entries = {}
    for item in out.split(b"\0"):
        if item:
            meta, _, path = item.partition(b"\t")
            mode, _, oid = meta.decode().split()
            entries[path.decode("utf-8", "surrogateescape")] = (mode, oid)
    return entries


def tree_id(entries):
    """git tree id of {path: (mode, object id)}, as git write-tree computes it."""
    root = {}
    for path, value in entries.items():
        node, parts = root, path.split("/")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
            if type(node) is not dict:
                raise CheckError("path is a file and a directory: " + path)
        node[parts[-1]] = value

    def oid(node):
        items = []
        for name, value in node.items():
            if type(value) is dict:
                items.append((name + "/", b"40000 " + name.encode() + b"\0" + bytes.fromhex(oid(value))))
            else:
                items.append((name, value[0].encode() + b" " + name.encode() + b"\0" + bytes.fromhex(value[1])))
        body = b"".join(entry for _, entry in sorted(items))
        return hashlib.sha1(b"tree %d\0" % len(body) + body).hexdigest()
    return oid(root)


def compare_entries(tag, tarball):
    """Paths only in the tag (missing), only in the tarball (extra), with other bytes (changed) and
    with the same bytes but another git mode (mode: an executable bit a release tarball dropped or set)."""
    common = set(tag) & set(tarball)
    return {"missing": sorted(set(tag) - set(tarball)), "extra": sorted(set(tarball) - set(tag)),
            "changed": sorted(p for p in common if tag[p][1] != tarball[p][1]),
            "mode": sorted(p for p in common if tag[p][1] == tarball[p][1] and tag[p][0] != tarball[p][0])}


def nested_archives(archive):
    with tarfile.open(archive, "r:*") as stream:
        return sorted(m.name for m in stream.getmembers() if m.isfile() and m.name.endswith(ARCHIVE_SUFFIXES))


def recipe_member(component):
    """source.member.path of deployment/recipes/<id>/recipe.json, when that recipe names one."""
    path = DEPLOYMENT / "recipes" / component / "recipe.json"
    recipe = deploy.load(path) if path.is_file() else {}
    member = (recipe.get("source") or {}).get("member") if type(recipe) is dict and type(recipe.get("source")) is dict else None
    return member["path"] if type(member) is dict and type(member.get("path")) is str else None


def compare_release_tarball(component, archive, clone, member=None):
    """A release tarball against a clone of its tag. With member (the recipe's source.member) that
    inner archive is compared; otherwise the tarball itself and every archive nested in it are, and
    the closest (fewest differing paths; the tarball itself on a tie) is reported. Reported only."""
    tag = tag_entries(clone)
    candidates = []
    with tempfile.TemporaryDirectory(prefix="srrx-release-") as temporary:
        for name in [member] if member else [None] + nested_archives(archive):
            source = archive
            if name is not None:
                source = Path(temporary) / "inner"
                with tarfile.open(archive, "r:*") as stream:
                    found = [m for m in stream.getmembers() if m.name == name and m.isfile()]
                    if len(found) != 1:
                        raise CheckError("release tarball has no member " + name + ": " + component["id"])
                    with stream.extractfile(found[0]) as data, open(source, "wb") as target:
                        shutil.copyfileobj(data, target)
            try:
                entries, root = tar_entries(source)
            except (tarfile.TarError, CheckError) as exc:
                candidates.append({"member": name, "root": None, "tree": None, "differing": None, "unreadable": str(exc)[:200]})
                continue
            differences = compare_entries(tag, entries)
            candidates.append({"member": name, "root": root, "tree": tree_id(entries), "differences": differences,
                               "differing": sum(len(v) for v in differences.values())})
    readable = [c for c in candidates if c["differing"] is not None]
    if not readable:
        raise CheckError("no readable tree in the release tarball of " + component["id"])
    closest = min(readable, key=lambda c: c["differing"])
    commit, tag_tree = _git(["rev-parse", "HEAD"], clone), _git(["rev-parse", "HEAD^{tree}"], clone)
    differences = closest["differences"]
    return {"component": component["id"], "tag": component["tag"], "upstream_url": component["upstream_url"],
            "lock_commit": component.get("commit"), "tag_commit": commit, "tag_commit_matches_lock": commit == component.get("commit"),
            "tag_tree": tag_tree, "compared": closest["member"] or Path(component["source_cache_path"]).name, "tarball_tree": closest["tree"],
            "verdict": "EQUAL" if closest["tree"] == tag_tree else "DIFFERENT",
            "missing": len(differences["missing"]), "extra": len(differences["extra"]), "changed": len(differences["changed"]),
            "mode": len(differences["mode"]),
            "candidates": [{k: c[k] for k in ("member", "root", "tree", "differing")} for c in candidates], "differences": differences}


def tarball_vs_tag(cache, work, lock=None):
    """sources job: every release_tarballs entry in the fetched cache against its tag tree; writes
    <id>-tree-diff.txt (missing/extra/changed/mode paths) into work. Reported, not a gate."""
    lock = lock or deploy.load(DEPLOYMENT / "sources.lock.json")
    root, work = Path(cache).resolve(strict=True), Path(work)
    work.mkdir(parents=True, exist_ok=True)
    reports = []
    for component in release_tarballs(lock):
        archive = fetch_sources._safe_cache(root, component["source_cache_path"])
        if not archive.is_file():
            reports.append({"component": component["id"], "verdict": "NOT_FETCHED"})
            continue
        if deploy.sha(archive) != component["source_archive_sha256"]:
            raise CheckError("cached release tarball differs from the lock: " + component["id"])
        clone = work / (component["id"] + "-tag")
        clone_tag(component, clone, checkout=False)
        report = compare_release_tarball(component, archive, clone, recipe_member(component["id"]))
        differences = report.pop("differences")
        diff = work / (component["id"] + "-tree-diff.txt")
        diff.write_text("".join("%s %s\n" % (kind, path) for kind in ("missing", "extra", "changed", "mode") for path in differences[kind]),
                        encoding="utf-8")
        report["diff_file"] = diff.name
        shutil.rmtree(clone, ignore_errors=True)
        reports.append(report)
    return {"status": "RELEASE_TARBALLS_COMPARED_WITH_TAGS", "components": reports, "hardware_ready": False,
            "scope": "Reported, not a gate: which paths a release tarball adds, lacks, changes or re-modes against its tag tree."}


# --- runtime check: one fresh chroot per job, offline -------------------------------------------

def deb_control(deb):
    """The control paragraph of a .deb (control.tar member ./control), read in Python."""
    with open(deb, "rb") as stream:
        if stream.read(8) != b"!<arch>\n":
            raise CheckError("not a .deb (ar) archive: " + Path(deb).name)
        while True:
            header = stream.read(60)
            if len(header) != 60 or header[58:60] != b"`\n" or not header[48:58].strip().isdigit():
                raise CheckError(".deb has no control member: " + Path(deb).name)
            name, size = header[:16].decode("ascii", "replace").strip().rstrip("/"), int(header[48:58])
            if name.startswith("control.tar"):
                break
            stream.seek(size + (size & 1), os.SEEK_CUR)
        with tarfile.open(fileobj=deploy._Member(stream, size), mode="r|*") as control:
            for member in control:
                if member.name in ("./control", "control") and member.isfile():
                    return deploy.deb822(control.extractfile(member).read().decode("utf-8"), "control")[0]
    raise CheckError(".deb control member has no control file: " + Path(deb).name)


def relation_groups(field):
    """Package names of a Depends field, one list of alternatives per relation (versions, arch
    qualifiers and profiles dropped)."""
    groups = []
    for relation in (field or "").split(","):
        alternatives = [re.split(r"[\s(:\[<]", a.strip(), maxsplit=1)[0] for a in relation.split("|") if a.strip()]
        if alternatives:
            groups.append(alternatives)
    return groups


def runtime_packages(out, recipes):
    """The runtime-check install set of one job: each package of its recipes that may enter the lab
    repository (no deploy.lab_package_issues finding) and is not a -dev package (build chroots only),
    plus the lab packages (any record under out) they depend on, transitively. Every other Depends
    name comes from the pinned snapshot. Returns (lab items for lab_build.install_lab_packages,
    snapshot names, held-back packages with reasons)."""
    lab, owners = {}, {}
    for record_path in records(out):
        record = deploy.load(record_path)
        for package in record["packages"]:
            lab[package["package"]] = {"package": package["package"], "version": package["version"], "sha256": package["sha256"],
                                       "component": record["component"], "record_sha256": deploy.sha(record_path),
                                       "path": recorded_deb(record_path, package)}
            owners.setdefault(record["component"], []).append(package["package"])
    chosen, held = [], []
    for recipe in recipes:
        if recipe not in owners:
            raise CheckError("no build record for recipe " + recipe + " under " + str(out))
        for name in owners[recipe]:
            issues = deploy.lab_package_issues(deploy.deb_data_tree(lab[name]["path"]))
            if name.endswith("-dev"):
                held.append({"package": name, "reason": "-dev package: build chroots only"})
            elif issues:
                held.append({"package": name, "reason": "; ".join(issues)})
            else:
                chosen.append(name)
    install, snapshot, queue = [], set(), list(chosen)
    while queue:
        name = queue.pop(0)
        if name in install:
            continue
        install.append(name)
        for group in relation_groups(deb_control(lab[name]["path"]).get("depends")):
            labelled = [a for a in group if a in lab]
            if labelled:
                queue.append(labelled[0])
            else:
                snapshot.add(group[0])
    return [lab[n] for n in install], sorted(snapshot), held


def runtime_chroot_argv(lock, chroot, keyring, packages):
    """mmdebstrap argv of a runtime-check chroot: lab_build's pinned snapshot, keyring and apt
    options, but variant apt (no build toolchain) and only python3 plus the given snapshot packages."""
    argv = lab_build.mmdebstrap_argv({"build_depends": []}, lock, chroot, keyring)
    include = "--include=" + ",".join(sorted(set(packages) | {"python3"}))
    return ["--variant=apt" if a == "--variant=buildd" else include if a.startswith("--include=") else a for a in argv]


# Runs as uid 1000 in the runtime chroot, offline (lab_build.offline_argv): the namespace lists only
# loopback, the runtime packages are installed and every ELF file they ship resolves its libraries.
PROBE = r'''import json, os, subprocess, sys
findings, packages = [], {}
interfaces = sorted(os.listdir("/sys/class/net"))
if interfaces != ["lo"]:
    findings.append("network interfaces besides loopback: " + ",".join(interfaces))
if os.getuid() == 0:
    findings.append("the runtime check runs as root")
for name in sys.argv[1:]:
    status = subprocess.run(["dpkg-query", "-W", "-f", "${Status}", name], capture_output=True, text=True).stdout
    if status != "install ok installed":
        findings.append(name + " is not installed: " + status)
        continue
    elves = []
    for path in subprocess.run(["dpkg-query", "-L", name], capture_output=True, text=True, check=True).stdout.splitlines():
        if path and os.path.isfile(path) and not os.path.islink(path):
            with open(path, "rb") as handle:
                if handle.read(4) == b"\x7fELF":
                    elves.append(path)
    for path in elves:
        missing = [line.split()[0] for line in subprocess.run(["ldd", path], capture_output=True, text=True).stdout.splitlines()
                   if "not found" in line]
        if missing:
            findings.append(path + " needs missing libraries: " + ",".join(missing))
    packages[name] = {"elf_files": len(elves)}
print(json.dumps({"ok": not findings, "findings": findings, "packages": packages, "uid": os.getuid(), "interfaces": interfaces}))
'''


def chroot_json(argv, log):
    """One command in the chroot: exit 0 and a JSON object on the last stdout line with ok true and
    no findings (the hook contract of build_recipe.run_hook), or not ok."""
    result = subprocess.run(argv, capture_output=True, text=True)
    Path(log).write_text("$ " + " ".join(argv[-4:]) + "\n" + result.stdout + result.stderr, encoding="utf-8")
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    try:
        report = json.loads(lines[-1]) if lines else None
    except ValueError:
        report = None
    ok = result.returncode == 0 and type(report) is dict and report.get("ok") is True and report.get("findings", []) == []
    return {"exit": result.returncode, "status": "CI_PASS" if ok else "FAIL", "report": report, "log": Path(log).name}


def runtime_script(name):
    """deployment/recipes/<name>/runtime_check.py when the recipe ships one (a regular file), else None."""
    script = DEPLOYMENT / "recipes" / name / "runtime_check.py"
    return None if script.is_symlink() or not script.is_file() else script


def runtime_check(out, recipes, work, samples=None, lock=None):
    """runtime_packages of one job installed offline (dpkg -i in an empty network namespace) in one
    fresh chroot from the pinned snapshot; then PROBE and each recipe's runtime_check.py
    (deployment/recipes/<id>/runtime_check.py, with --samples <its tag samples> when it declares
    ci.tag_samples) as uid 1000 under unshare --net --mount --pid. CI model on the arm64 builder.
    A recipe with a runtime_check.py but none of its own packages in the install set (all -dev or
    held back) fails the check: its script would test nothing."""
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        raise CheckError("runtime-check needs root on a disposable builder (mmdebstrap, chroot, mounts)")
    lock = lock or deploy.load(DEPLOYMENT / "sources.lock.json")
    result = build_recipe.ci_plan(lock)
    unknown = [r for r in recipes if r not in result["recipes"]]
    if unknown or not recipes:
        raise CheckError("runtime-check names no or unknown recipes: " + ", ".join(unknown))
    install, snapshot, held = runtime_packages(out, recipes)
    extra = sorted({d for r in recipes for d in result["recipes"][r]["runtime_depends"]})
    uncovered = [n for n in recipes if runtime_script(n) is not None and not any(i["component"] == n for i in install)]
    report = {"status": "NO_RUNTIME_PACKAGES", "recipes": list(recipes), "snapshot_packages": sorted(set(snapshot) | set(extra) | {"python3"}),
              "held_back": held, "installed": [], "probe": None, "runtime_checks": {}, "hardware_ready": False,
              "findings": ["%s/runtime_check.py: none of its packages is installed (all -dev or held back), so it would test nothing" % n
                           for n in uncovered],
              "scope": "CI model on the arm64 builder: offline install in a fresh chroot from the pinned snapshot; no hardware, no RF."}
    work = Path(work).resolve()
    if work.exists():
        raise CheckError("runtime-check work directory already exists")
    work.mkdir(parents=True)
    if uncovered:
        report["status"] = "CI_RUNTIME_CHECK_FAILED"
        return report
    if not install:
        return report
    keyring = lab_build.pinned_keyring(lock, work / "keyring")
    fetch_sources.verify_releases(lock, keyring, work / "inrelease")
    chroot = work / "chroot"
    subprocess.run(runtime_chroot_argv(lock, chroot, keyring, snapshot + extra), check=True)
    report["chroot_inrelease"] = lab_build.installed_releases(chroot, lock)
    report["installed"] = lab_build.install_lab_packages(chroot, install)
    runtime = chroot / "srrx-runtime"
    runtime.mkdir()
    (runtime / "probe.py").write_text(PROBE, encoding="utf-8")
    report["probe"] = chroot_json(lab_build.offline_argv(chroot, ["python3", "-I", "/srrx-runtime/probe.py"] + [i["package"] for i in install]),
                                  work / "probe.log")
    components = {c["id"]: c for c in lock["components"]}
    for name in recipes:
        script = runtime_script(name)
        if script is None:
            continue
        directory = runtime / name
        directory.mkdir()
        shutil.copyfile(script, directory / "runtime_check.py")
        argv = ["python3", "-I", "/srrx-runtime/%s/runtime_check.py" % name]
        if result["recipes"][name]["tag_samples"]:
            index = Path(samples) / (name + ".tag-samples.json") if samples else None
            if index is None or not index.is_file() or not (Path(samples) / name).is_dir():
                raise CheckError("tag samples of " + name + " are missing (plan job artifact tag-samples)")
            exported = deploy.load(index)
            if exported.get("commit") != components[name].get("commit") or sorted(exported.get("paths", {})) != sorted(result["recipes"][name]["tag_samples"]):
                raise CheckError("tag samples of " + name + " are not the declared paths of the locked commit")
            shutil.copytree(Path(samples) / name, directory / "samples", symlinks=True)
            argv += ["--samples", "/srrx-runtime/%s/samples" % name]
        report["runtime_checks"][name] = dict(chroot_json(lab_build.offline_argv(chroot, argv), work / (name + ".runtime-check.log")),
                                              script_sha256=deploy.sha(script))
    passed = report["probe"]["status"] == "CI_PASS" and all(r["status"] == "CI_PASS" for r in report["runtime_checks"].values())
    report["status"] = "CI_RUNTIME_CHECKED" if passed else "CI_RUNTIME_CHECK_FAILED"
    return report


def chain_identity(out, chains):
    """Each heavy job rebuilt its chain (its lab_build_depends recipes) on another runner: its
    package bytes against the records in out (one per component, from the light job). Reported:
    a difference is a second-builder reproducibility finding, not a refusal."""
    published = {}
    for record_path in records(out):
        record = deploy.load(record_path)
        for package in record["packages"]:
            published[(record["component"], package["package"])] = (package["sha256"], package["size"])
    comparisons = []
    for record_path in sorted(Path(chains).glob("*/*/*.build-record.json")) if Path(chains).is_dir() else []:
        record = deploy.load(record_path)
        for package in record["packages"]:
            comparisons.append({"heavy": record_path.parent.parent.name, "component": record["component"], "package": package["package"],
                                "sha256": package["sha256"], "equal": published.get((record["component"], package["package"])) == (package["sha256"], package["size"])})
    status = "NO_HEAVY_CHAINS" if not comparisons else "CHAIN_BYTES_EQUAL" if all(c["equal"] for c in comparisons) else "CHAIN_BYTES_DIFFER"
    return {"status": status, "comparisons": comparisons, "hardware_ready": False,
            "scope": "Second builder on another runner for the chain packages; reported, not a gate."}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="operation", required=True)
    for name in ("packages", "publishable"):
        commands.add_parser(name).add_argument("--out", type=Path, required=True)
    attack = commands.add_parser("tamper")
    attack.add_argument("--repo", type=Path, required=True)
    attack.add_argument("--keyring", type=Path, required=True)
    attack.add_argument("--wrong-keyring", type=Path, required=True)
    attack.add_argument("--fingerprint", required=True)
    attack.add_argument("--build-record", type=Path, action="append", required=True)
    attack.add_argument("--sources-entry", type=Path, required=True)
    attack.add_argument("--full-repo", type=Path, help="a repository signed by the same key with every built package, held-back ones included")
    planner = commands.add_parser("plan", help="recipes this sr-rx-packages run builds, light job and heavy jobs")
    planner.add_argument("--changed", type=Path, help="repository-relative paths of the push range, one per line")
    planner.add_argument("--range-unknown", action="store_true", help="the push range could not be read: every heavy recipe runs")
    planner.add_argument("--lock-before", type=Path, help="sources.lock.json at the start of the push range ({} if it had none)")
    planner.add_argument("--message-env", help="environment variable holding the head commit message ([lab-build-all] token)")
    planner.add_argument("--build-all", action="store_true", help="build every heavy recipe (dispatch input)")
    planner.add_argument("--github-output", type=Path, help="append the job outputs to this file ($GITHUB_OUTPUT)")
    samples = commands.add_parser("tag-samples", help="export the ci.tag_samples paths from tag clones")
    samples.add_argument("--out", type=Path, required=True)
    release = commands.add_parser("tarball-vs-tag", help="release tarballs of the lock against their tag tree (reported)")
    release.add_argument("--cache", type=Path, required=True)
    release.add_argument("--work", type=Path, required=True)
    runtime = commands.add_parser("runtime-check", help="one job's runtime packages offline in a fresh chroot (root)")
    runtime.add_argument("--out", type=Path, required=True)
    runtime.add_argument("--recipe", action="append", required=True)
    runtime.add_argument("--work", type=Path, required=True)
    runtime.add_argument("--samples", type=Path, help="the plan job's tag-samples directory")
    runtime.add_argument("--report", type=Path, required=True)
    chains = commands.add_parser("chains", help="heavy jobs' rebuilt lab_build_depends against the published bytes (reported)")
    chains.add_argument("--out", type=Path, required=True)
    chains.add_argument("--chains", type=Path, required=True)
    args = parser.parse_args()
    failed = False
    try:
        if args.operation == "packages":
            result = packages(args.out)
        elif args.operation == "publishable":
            result = publishable(args.out)
        elif args.operation == "plan":
            changed = None if args.range_unknown else [line.strip() for line in args.changed.read_text(encoding="utf-8").splitlines()
                                                       if line.strip()] if args.changed else []
            lock_before = json.loads(args.lock_before.read_text(encoding="utf-8") or "{}") if args.lock_before else None
            token = bool(args.message_env and LAB_BUILD_ALL.search(os.environ.get(args.message_env, "")))
            result = plan(changed, lock_before, args.build_all or token)
            if args.github_output:
                with open(args.github_output, "a", encoding="utf-8") as stream:
                    stream.write(github_outputs(result))
        elif args.operation == "tag-samples":
            result = tag_samples(args.out)
        elif args.operation == "tarball-vs-tag":
            result = tarball_vs_tag(args.cache, args.work)
        elif args.operation == "runtime-check":
            result = runtime_check(args.out, args.recipe, args.work, args.samples)
            args.report.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
            failed = result["status"] == "CI_RUNTIME_CHECK_FAILED"
        elif args.operation == "chains":
            result = chain_identity(args.out, args.chains)
        else:
            result = tamper(args.repo, args.keyring, args.wrong_keyring, args.fingerprint, args.build_record, args.sources_entry, args.full_repo)
    except (OSError, ValueError, subprocess.SubprocessError, tarfile.TarError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps(result, indent=2, default=str))
    if failed:
        parser.exit(2, "FAIL: " + args.operation + " (see the report)\n")


if __name__ == "__main__":
    main()
