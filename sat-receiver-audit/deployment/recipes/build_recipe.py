#!/usr/bin/env python3
"""Build one +lab recipe into .deb files inside the isolated builder chroot (recipes/README.md).

Runs as an unprivileged user in a chroot whose network namespace has no route (lab_build.py
starts it under `unshare --net`); it first checks that the namespace lists only loopback and that
an outside connection fails with no route. The
source archive must match deployment/sources.lock.json; a reviewed patch is applied through
vendor_patch.py. Every CMake option the upstream tree declares and this configuration evaluates
must be set explicitly by the recipe (no unreviewed upstream default). Schema 2 adds, in this
order: an inner archive of the locked one as the source tree (source.member, with its SHA-256),
the recipe's source_check hook, its own listed patches (source.patches: SHA-256 and target git
blobs checked before each `git apply`), make or autotools builds (a release tarball's generated
configure with a fixed --prefix and only listed --enable/--disable/--with/--without flags; no
autoreconf), files of deployment/recipes/<id>/files/ in install.copy, the package hook (its
JSON record_digests go into the build record) and DT_NEEDED checks. Hooks run only
`python3 -I deployment/recipes/<id>/check_recipe.py`. The result is .deb files,
one verify_build manifest per package (status OPEN, never REVIEWED here), one data tree per package
(<package>.data-tree.json: every path of the .deb data member with its type, SHA-256, mode or
link target, also where the verify_build walk refuses the tree; data_tree_sha256 in the record)
and a build record that deploy.verify_repo binds to the lock, the recipe, the patch, every listed
patch and the source member. Schema 2 may add a "ci" key (heavy job, runtime-check packages, tag
samples) that only sr-rx-packages.yml reads (ci_plan). A package that ships a SONAME'd
library carries DEBIAN/shlibs and the ldconfig trigger, so consumers built against it in a later
recipe (lab_build_depends) get their Depends from dpkg-shlibdeps without --ignore-missing-info.
CI evidence only: no review, no TX proof, no hardware test.
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
import stat
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
DEPLOYMENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT))
import deploy  # noqa: E402

RECIPE_KEYS = ("schema_version", "component", "summary", "source", "build_depends", "lab_build_depends", "cmake", "build",
               "install", "packages", "drop", "checks", "notes")
# schema_version 2: the keys of 1 plus build_system, autotools and hooks (recipes/README.md).
RECIPE_KEYS_V2 = ("schema_version", "component", "summary", "source", "build_system", "build_depends", "lab_build_depends",
                  "cmake", "autotools", "build", "install", "hooks", "packages", "drop", "checks", "notes")
SOURCE_KEYS = {1: ("patch",), 2: ("patch", "patches", "member")}
INSTALL_KEYS = {1: ("cmake_install", "copy"), 2: ("cmake_install", "make_install", "copy")}
PACKAGE_KEYS = ("name", "section", "description", "files", "depends", "shlibs_depends")
CHECK_KINDS = {"soname": ("kind", "file", "equals"), "export_count": ("kind", "file", "prefix", "equals"),
               "forbid_strings": ("kind", "file", "substrings"), "forbid_paths": ("kind", "globs"),
               "require_paths": ("kind", "globs"), "forbid_needed": ("kind", "files", "needed")}
# Programs a recipe step may run. Anything that can fetch (curl, wget, git clone, pip, apt) is absent.
STEP_PROGRAMS = frozenset({"cmake", "make", "ninja"})
PLACEHOLDERS = ("{src}", "{build}", "{destdir}", "{jobs}")
BUILD_SYSTEMS = ("cmake", "make", "autotools")
# One entry of source.patches: a patch file in deployment/recipes/<id>/patches/ (not the TX-rejecting
# deployment/patches/<id>-rx-only.patch), its SHA-256, -p level and the git blob of every file it changes
# as that file is just before this patch (the upstream blob unless an earlier listed patch changed it).
PATCH_KEYS = ("file", "sha256", "strip", "targets", "kind", "summary")
PATCH_KINDS = ("cherry-pick", "lab")
PATCH_FILE = re.compile(r"patches/[A-Za-z0-9][A-Za-z0-9._+-]*\.patch")
HUNK = re.compile(r"@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")
# Diff headers that create, delete, rename, copy or re-mode a file, or carry binary data.
PATCH_REFUSED = ("rename from", "rename to", "copy from", "copy to", "new file mode", "deleted file mode", "old mode",
                 "new mode", "GIT binary patch", "Binary files ")
SHA256 = re.compile(r"[0-9a-f]{64}")
GIT_BLOB = re.compile(r"[0-9a-f]{40}")
# A hook runs only the recipe's own check_recipe.py, with these subcommands and placeholders.
HOOKS = {"source_check": "verify-source", "package": "package"}
HOOK_PLACEHOLDERS = {"source_check": ("{src}",), "package": ("{src}", "{destdir}", "{hook_out}")}
CONFIGURE_FLAG = re.compile(r"--(enable|disable|with|without)-([A-Za-z0-9][A-Za-z0-9_-]*)(=[A-Za-z0-9_.,+/-]*)?")
CONFIGURE_PREFIX = "/usr"
# Tools that regenerate configure/Makefile.in: never in a chroot (release tarballs ship them generated).
REGENERATORS = frozenset({"autoconf", "automake", "autopoint", "dh-autoreconf", "autoconf-archive", "gnulib"})
NAME = re.compile(r"[a-z0-9][a-z0-9+.-]+")
# The optional schema-2 "ci" key (sr-rx-packages.yml, recipes/README.md): a heavy recipe gets its own
# job, run when its inputs change or the head commit carries [lab-build-all]; runtime_depends are
# noble packages the runtime-check chroot also needs (strace, ...); tag_samples are paths of the
# component's git tag tree (a lock entry with a "tag") exported for the recipe's runtime_check.py.
CI_KEYS = ("heavy", "runtime_depends", "tag_samples")
DATA_TREE_KIND = "srrx_lab_data_tree"
OPTION =re.compile(r"\b(?:option|cmake_dependent_option)\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)", re.I)
MAINTAINER = "SR-RX lab builder <builder@srrx.invalid>"
MULTIARCH = "aarch64-linux-gnu"


class RecipeError(ValueError):
    pass


# A recipe written for a builder that does not exist yet (deployment/recipes/satdump: its own
# "srrx_build_recipe" schema, checked by that directory's check_recipe.py) is not a build_recipe:
# validate_recipe refuses it by name, so lab_build.py never builds it and the tests keep it apart.
PENDING_KIND, PENDING_STATUS = "srrx_build_recipe", "PENDING_BUILDER"


def is_pending(recipe):
    return type(recipe) is dict and recipe.get("kind") == PENDING_KIND and recipe.get("status") == PENDING_STATUS


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
        # Every placeholder of the item must be one of PLACEHOLDERS ({recipe} and {hook_out} are not step placeholders).
        found = re.findall(r"\{[^{}]*\}", item)
        if item.count("{") != len(found) or any(p not in PLACEHOLDERS for p in found):
            raise RecipeError(label + " has an unknown placeholder")
    return value


def recipe_dir(component):
    """deployment/recipes/<id>/: the only directory hooks, listed patches and install files come from."""
    return DEPLOYMENT / "recipes" / component


def _relative(path, label):
    if type(path) is not str or not path or path.startswith("/") or "\\" in path or any(p in ("", ".", "..") for p in path.split("/")):
        raise RecipeError(label + " must be a relative path inside the tree: " + repr(path))
    return path


def patch_paths(text, strip):
    """The files a unified diff changes, after stripping `strip` leading components. A patch that
    creates, deletes, renames, copies or re-modes a file, or carries binary data, is refused: a
    listed patch only changes files whose git blob the recipe names."""
    lines, changed, index = text.split("\n"), [], 0

    def header(line):
        parts = line[4:].split("\t", 1)[0].strip().split("/")
        if line[4:].startswith("/dev/null") or len(parts) <= strip:
            raise RecipeError("listed patch creates or deletes a file, or has fewer path components than its strip level")
        return "/".join(parts[strip:])
    while index < len(lines):
        line = lines[index]
        if line.startswith(PATCH_REFUSED):
            raise RecipeError("listed patch does more than change existing files: " + line[:40])
        if line.startswith("--- ") and index + 1 < len(lines) and lines[index + 1].startswith("+++ "):
            old, new = header(line), header(lines[index + 1])
            if old != new:
                raise RecipeError("listed patch renames a file: " + old + " -> " + new)
            changed.append(new)
            index += 2
            continue
        match = HUNK.match(line)
        if match:
            remove, add = int(match.group(1) or 1), int(match.group(2) or 1)
            index += 1
            while (remove > 0 or add > 0) and index < len(lines):
                tag = lines[index][:1]
                if tag in (" ", ""):
                    remove, add = remove - 1, add - 1
                elif tag == "-":
                    remove -= 1
                elif tag == "+":
                    add -= 1
                elif tag != "\\":  # "\ No newline at end of file"
                    raise RecipeError("listed patch has a malformed hunk")
                index += 1
            continue
        index += 1
    return changed


def _patches(entries, component):
    """source.patches: one entry per patch in deployment/recipes/<id>/patches/, each file once."""
    if type(entries) is not list:
        raise RecipeError("source.patches must be a list")
    files = set()
    for index, entry in enumerate(entries):
        label = "source.patches[%d]" % index
        if type(entry) is not dict or not set(PATCH_KEYS) <= set(entry) <= set(PATCH_KEYS) | {"upstream_commit"}:
            raise RecipeError(label + " has missing or unknown fields")
        if type(entry["file"]) is not str or not PATCH_FILE.fullmatch(entry["file"]) or entry["file"] in files:
            raise RecipeError(label + " file must be patches/<name>.patch of the recipe directory, listed once")
        files.add(entry["file"])
        path = recipe_dir(component) / entry["file"]
        if (type(entry["sha256"]) is not str or not SHA256.fullmatch(entry["sha256"]) or path.is_symlink() or not path.is_file()
                or deploy.sha(path) != entry["sha256"]):
            raise RecipeError(label + " file is missing or differs from its sha256: " + entry["file"])
        if type(entry["strip"]) is not int or not 0 <= entry["strip"] <= 3:
            raise RecipeError(label + " strip must be an integer 0..3")
        targets = entry["targets"]
        if type(targets) is not dict or not targets or not all(type(v) is str and GIT_BLOB.fullmatch(v) for v in targets.values()):
            raise RecipeError(label + " targets must map each changed file to its git blob id just before this patch"
                              " (the upstream blob unless an earlier listed patch changed that file)")
        for target in targets:
            _relative(target, label + " target")
        if entry["kind"] not in PATCH_KINDS or type(entry["summary"]) is not str or not entry["summary"]:
            raise RecipeError(label + " needs a kind (" + ", ".join(PATCH_KINDS) + ") and a summary")
        commit = entry.get("upstream_commit")
        if ("upstream_commit" in entry) != (entry["kind"] == "cherry-pick") or (commit is not None and not (type(commit) is str and GIT_BLOB.fullmatch(commit))):
            raise RecipeError(label + " upstream_commit is the 40-hex commit of a cherry-pick, and only of one")
        if set(patch_paths(path.read_text(encoding="utf-8"), entry["strip"])) != set(targets):
            raise RecipeError(label + " changes other files than its targets: " + entry["file"])
    return entries


def _member(member):
    """source.member: an inner archive of the locked archive (a superbuild release) as the source tree."""
    if member is None:
        return None
    deploy.keys(member, ("path", "sha256"), "recipe source.member")
    _relative(member["path"], "source.member path")
    if type(member["sha256"]) is not str or not SHA256.fullmatch(member["sha256"]):
        raise RecipeError("source.member needs the sha256 of the inner archive")
    if not member["path"].endswith((".tar.gz", ".tgz", ".tar.xz", ".tar.bz2", ".tar")):
        raise RecipeError("source.member must be a tar archive inside the locked archive")
    return member


def _hook(argv, name, component):
    if argv is None:
        return None
    _strings(argv, "hooks." + name)
    if argv[:4] != ["python3", "-I", "{recipe}/check_recipe.py", HOOKS[name]]:
        raise RecipeError("hooks.%s may only run python3 -I {recipe}/check_recipe.py %s of the recipe's own directory" % (name, HOOKS[name]))
    script = recipe_dir(component) / "check_recipe.py"
    if script.is_symlink() or not script.is_file():
        raise RecipeError("hooks." + name + ": deployment/recipes/" + component + "/check_recipe.py is missing")
    for item in argv[4:]:
        if "://" in item:
            raise RecipeError("hooks." + name + " names a URL")
        if ".." in re.split(r"[/=]", item):
            raise RecipeError("hooks." + name + " argument leaves its directory: " + item)
        found = re.findall(r"\{[^{}]*\}", item)
        if item.count("{") != len(found) or any(p not in HOOK_PLACEHOLDERS[name] for p in found):
            raise RecipeError("hooks." + name + " has a placeholder outside " + ", ".join(HOOK_PLACEHOLDERS[name]))
    return argv


def _ci(ci, component):
    """The optional schema-2 "ci" key: exactly heavy, runtime_depends and tag_samples."""
    deploy.keys(ci, CI_KEYS, "recipe ci")
    if type(ci["heavy"]) is not bool:
        raise RecipeError("ci.heavy must be true or false")
    names = _strings(ci["runtime_depends"], "ci.runtime_depends", allow_empty=True)
    if len(set(names)) != len(names) or not all(NAME.fullmatch(n) for n in names):
        raise RecipeError("ci.runtime_depends lists noble package names, each once")
    samples = _strings(ci["tag_samples"], "ci.tag_samples", allow_empty=True)
    for sample in samples:
        _relative(sample, "ci.tag_samples")
    if len(set(samples)) != len(samples):
        raise RecipeError("ci.tag_samples lists each path once")
    if samples and not (type(component.get("tag")) is str and component["tag"]
                        and str(component.get("upstream_url") or "").startswith("https://")):
        raise RecipeError("ci.tag_samples needs a lock component with a tag and an https upstream_url (its tag clone)")
    return ci


def ci_view(recipe):
    """{heavy, runtime_depends, tag_samples} of a validated recipe; without "ci" (and in schema 1) a
    light recipe with no extra runtime packages and no samples."""
    ci = recipe.get("ci") if recipe.get("schema_version") == 2 else None
    ci = ci if type(ci) is dict else {"heavy": False, "runtime_depends": [], "tag_samples": []}
    return {"heavy": ci["heavy"], "runtime_depends": list(ci["runtime_depends"]), "tag_samples": list(ci["tag_samples"])}


def _order(needs):
    """Recipe ids in build order: each after the recipes whose packages it needs; ties by name."""
    order, done = [], set()
    while len(order) < len(needs):
        ready = sorted(n for n in needs if n not in done and set(needs[n]) <= done)
        if not ready:
            raise RecipeError("lab_build_depends form a cycle: " + ", ".join(sorted(set(needs) - done)))
        order.append(ready[0])
        done.add(ready[0])
    return order


def ci_plan(lock=None):
    """What sr-rx-packages.yml builds: every deployment/recipes/<id>/recipe.json. A PENDING_BUILDER
    recipe is skipped with its reason; any other invalid recipe, a directory that is not its
    component, a package two recipes build, a lab_build_depends package no recipe builds, a cycle
    and a light recipe that needs a heavy one's packages fail. light: the light recipes in build
    order (one job, in sequence); heavy: the heavy ones, each with its chain (the recipes its
    lab_build_depends come from, in build order, then itself) for its own job."""
    lock = lock or deploy.load(DEPLOYMENT / "sources.lock.json")
    entries, skipped, provider = {}, {}, {}
    for path in sorted((DEPLOYMENT / "recipes").glob("*/recipe.json")):
        name, recipe = path.parent.name, deploy.load(path)
        if is_pending(recipe):
            skipped[name] = PENDING_STATUS + " (kind " + PENDING_KIND + "): this builder does not build it"
            continue
        try:
            validate_recipe(recipe, lock)
        except (RecipeError, deploy.DeploymentError) as exc:
            raise RecipeError("recipe " + name + " does not validate: " + str(exc)) from exc
        if recipe["component"] != name:
            raise RecipeError("recipe directory " + name + " holds component " + recipe["component"])
        for package in recipe["packages"]:
            if package["name"] in provider:
                raise RecipeError("package " + package["name"] + " is built by two recipes: " + provider[package["name"]] + ", " + name)
            provider[package["name"]] = name
        view = ci_view(recipe)
        entries[name] = {"heavy": view["heavy"], "packages": [p["name"] for p in recipe["packages"]],
                         "lab_build_depends": list(recipe["lab_build_depends"]), "runtime_depends": view["runtime_depends"],
                         "tag_samples": view["tag_samples"], "runtime_check": (path.parent / "runtime_check.py").is_file()}
    needs = {}
    for name, entry in entries.items():
        missing = [p for p in entry["lab_build_depends"] if p not in provider]
        if missing:
            raise RecipeError(name + " lab_build_depends names packages no recipe builds: " + ", ".join(missing))
        needs[name] = sorted({provider[p] for p in entry["lab_build_depends"]})
    order = _order(needs)
    for name in order:
        closure, stack = set(), list(needs[name])
        while stack:
            current = stack.pop()
            if current not in closure:
                closure.add(current)
                stack.extend(needs[current])
        entries[name]["needs"] = needs[name]
        entries[name]["chain"] = [n for n in order if n in closure] + [name]
        heavy = [n for n in closure if entries[n]["heavy"]]
        if heavy and not entries[name]["heavy"]:
            raise RecipeError("light recipe " + name + " needs packages of heavy recipes: " + ", ".join(sorted(heavy)))
    return {"light": [n for n in order if not entries[n]["heavy"]], "heavy": [n for n in order if entries[n]["heavy"]],
            "recipes": entries, "skipped": skipped}


def configure_name(flag):
    """--enable-foo-bar / --disable-foo-bar -> enable_foo_bar; --with-x / --without-x -> with_x (ac_user_opts)."""
    match = CONFIGURE_FLAG.fullmatch(flag)
    return ("enable_" if match.group(1) in ("enable", "disable") else "with_") + match.group(2).replace("-", "_")


def _autotools(config):
    deploy.keys(config, ("flags",), "recipe autotools")
    flags = _strings(config["flags"], "autotools.flags", allow_empty=True)
    for flag in flags:
        match = CONFIGURE_FLAG.fullmatch(flag)
        if not match or (match.group(1) in ("disable", "without") and match.group(3)) or ".." in flag.split("/"):
            raise RecipeError("autotools.flags holds only --enable/--disable/--with/--without flags (no URL, no other option): " + flag)
    names = [configure_name(f) for f in flags]
    if len(set(names)) != len(names) or "enable_option_checking" in names:
        raise RecipeError("autotools.flags names each configure option once and never --disable-option-checking")
    return flags


def _cmake(cmake):
    deploy.keys(cmake, ("configure", "options", "variables"), "recipe cmake")
    _argv(cmake["configure"], "cmake.configure")
    if cmake["configure"][:5] != ["cmake", "-S", "{src}", "-B", "{build}"]:
        raise RecipeError("cmake.configure must start with cmake -S {src} -B {build}")
    for section in ("options", "variables"):
        # Non-empty values only: an empty STRING override would hide a silent placeholder.
        if type(cmake[section]) is not dict or not all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k) and type(v) is str and v
                                                       for k, v in cmake[section].items()):
            raise RecipeError("cmake." + section + " must map CMake names to string values")
    if set(cmake["options"]) & set(cmake["variables"]) or any(v not in ("ON", "OFF") for v in cmake["options"].values()):
        raise RecipeError("cmake.options are ON/OFF and disjoint from cmake.variables")
    if cmake["variables"].get("FETCHCONTENT_FULLY_DISCONNECTED") != "ON":
        raise RecipeError("FETCHCONTENT_FULLY_DISCONNECTED must be ON")


def spec(recipe):
    """The schema-2 view of a validated recipe: schema 1 means cmake, no listed patches, no member, no hooks."""
    v2 = recipe["schema_version"] == 2
    return {"build_system": recipe["build_system"] if v2 else "cmake", "patch": recipe["source"]["patch"],
            "patches": recipe["source"]["patches"] if v2 else [], "member": recipe["source"]["member"] if v2 else None,
            "hooks": recipe["hooks"] if v2 else {"source_check": None, "package": None},
            "make_install": recipe["install"]["make_install"] if v2 else False,
            "flags": recipe["autotools"]["flags"] if v2 and recipe["build_system"] == "autotools" else None}


def validate_recipe(recipe, lock=None):
    """Exact schema of recipes/<id>/recipe.json, schema_version 1 or 2 (deployment/tests/test_recipes.py)."""
    if is_pending(recipe):
        raise RecipeError("recipe " + str(recipe.get("id")) + " is " + PENDING_STATUS + " (kind " + PENDING_KIND
                          + "), not in the build_recipe schema yet: this builder does not build it")
    version = recipe.get("schema_version") if type(recipe) is dict else None
    if type(version) is not int or version not in (1, 2):
        raise RecipeError("recipe schema_version must be 1 or 2")
    # schema 2: "ci" is the one optional key (absent: a light recipe, ci_view).
    deploy.keys(recipe, RECIPE_KEYS if version == 1 else RECIPE_KEYS_V2 + (("ci",) if "ci" in recipe else ()), "recipe")
    lock = lock or deploy.load(DEPLOYMENT / "sources.lock.json")
    component = next((c for c in lock["components"] if c["id"] == recipe["component"]), None)
    if component is None:
        raise RecipeError("recipe component must be a sources.lock.json id")
    if "ci" in recipe:
        _ci(recipe["ci"], component)
    if component["source_archive_sha256"] is None or component.get("debian_source") is not None:
        raise RecipeError("recipe component needs a locked upstream source archive")
    if component.get("source_subdir"):  # e.g. the LA9310 DKMS modules inside the LimeSuiteNG archive
        raise RecipeError("component has a source_subdir, which build_recipe does not honour yet: " + component["id"])
    deploy.keys(recipe["source"], SOURCE_KEYS[version], "recipe source")
    patch = recipe["source"]["patch"]
    if patch is not None and (patch != "deployment/patches/" + recipe["component"] + "-rx-only.patch"
                              or not (DEPLOYMENT.parent / patch).is_file()):
        raise RecipeError("recipe patch must be the reviewed deployment/patches/<component>-rx-only.patch")
    if version == 2:
        _patches(recipe["source"]["patches"], recipe["component"])
        if _member(recipe["source"]["member"]) is not None and patch is not None:
            raise RecipeError("source.member and the -rx-only.patch together are not supported (vendor_patch reads git archives)")
    for name in _strings(recipe["build_depends"], "build_depends"):
        if not NAME.fullmatch(name):
            raise RecipeError("build_depends holds a non-package name: " + name)
        if name in REGENERATORS:
            raise RecipeError("build_depends names a configure regenerator (no autoreconf: release tarballs ship configure): " + name)
    lab = _strings(recipe["lab_build_depends"], "lab_build_depends", allow_empty=True)
    if len(set(lab)) != len(lab) or not all(NAME.fullmatch(n) for n in lab):
        raise RecipeError("lab_build_depends lists lab package names, each once")
    system = recipe["build_system"] if version == 2 else "cmake"
    if system not in BUILD_SYSTEMS:
        raise RecipeError("build_system must be one of " + ", ".join(BUILD_SYSTEMS))
    if system == "cmake":
        _cmake(recipe["cmake"])
    elif recipe["cmake"] is not None:
        raise RecipeError("cmake is null unless build_system is cmake")
    if version == 2 and (recipe["autotools"] is None) != (system != "autotools"):
        raise RecipeError("autotools is set exactly when build_system is autotools")
    if system == "autotools":
        _autotools(recipe["autotools"])
    if type(recipe["build"]) is not list or not recipe["build"]:
        raise RecipeError("build lists at least one step")
    for index, step in enumerate(recipe["build"]):
        _argv(step, "build[%d]" % index)
    install = recipe["install"]
    deploy.keys(install, INSTALL_KEYS[version], "recipe install")
    make_install = install["make_install"] if version == 2 else False
    if type(install["cmake_install"]) is not bool or type(make_install) is not bool or type(install["copy"]) is not list:
        raise RecipeError("install needs boolean cmake_install/make_install and a copy list")
    if version == 1 and install["cmake_install"] == bool(install["copy"]):
        raise RecipeError("install is either cmake_install or an explicit copy list")
    if version == 2 and ((install["cmake_install"] and system != "cmake") or (make_install and system == "cmake")
                         or not (install["cmake_install"] or make_install or install["copy"])):
        raise RecipeError("install: cmake_install for cmake, make_install for make/autotools, or a copy list")
    sources = ("{src}/", "{build}/") + (("{recipe}/files/",) if version == 2 else ())
    for item in install["copy"]:
        deploy.keys(item, ("from", "to"), "install copy")
        if (type(item["from"]) is not str or type(item["to"]) is not str or not item["from"].startswith(sources)
                or ".." in item["from"].split("/") or item["to"].startswith("/") or ".." in item["to"].split("/")
                or "{" in item["from"].split("/", 1)[1] or "{" in item["to"]):  # one leading placeholder only
            raise RecipeError("install copy goes from " + ", ".join(sources) + " to a relative package path")
        if item["from"].startswith("{recipe}/"):
            files = (recipe_dir(recipe["component"]) / "files").resolve()
            matches = [Path(m) for m in sorted(glob.glob(str(recipe_dir(recipe["component"])) + item["from"][len("{recipe}"):]))]
            if not matches or any(m.is_symlink() or not m.is_file() or not m.resolve().is_relative_to(files) for m in matches):
                raise RecipeError("install copy from {recipe}/files/ matches no regular file of the recipe directory: " + item["from"])
    if version == 2:
        deploy.keys(recipe["hooks"], tuple(HOOKS), "recipe hooks")
        for name in HOOKS:
            _hook(recipe["hooks"][name], name, recipe["component"])
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
    if names & set(lab):
        raise RecipeError("a recipe cannot build against its own packages")
    forbidden = deploy.prohibited_installed({n: component["version"] for n in names}, identifiers=True)
    if forbidden:
        raise RecipeError("receive-only policy forbids package: " + ", ".join(forbidden))
    for item in recipe["drop"]:
        deploy.keys(item, ("glob", "reason"), "recipe drop")
    for check in recipe["checks"]:
        if type(check) is not dict or check.get("kind") not in CHECK_KINDS:
            raise RecipeError("unknown check kind")
        deploy.keys(check, CHECK_KINDS[check["kind"]], "check " + check["kind"])
        if check["kind"] == "forbid_needed":
            _strings(check["files"], "forbid_needed files")
            _strings(check["needed"], "forbid_needed needed")
    _strings(recipe["notes"], "notes", allow_empty=True)
    return component


def no_network(interfaces_dir="/sys/class/net"):
    """Fail unless the build's network namespace lists only loopback (lab_build.py mounts sysfs from
    inside the new namespace, so this is that namespace's list) and outside TCP connections fail
    with a no-route error. The isolation itself is `unshare --net`; this checks that it took."""
    try:
        interfaces = sorted(os.listdir(interfaces_dir))
    except OSError as exc:
        raise RecipeError("cannot list the build namespace's network interfaces (sysfs not mounted)") from exc
    if interfaces != ["lo"]:
        raise RecipeError("the build namespace has interfaces besides loopback: " + ",".join(interfaces))
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
    return "no route outside the network namespace; interfaces lo"


def _extract_root(archive, destination, label):
    with tarfile.open(archive, "r:*") as stream:
        members = stream.getmembers()
        roots = {Path(m.name).parts[0] for m in members if Path(m.name).parts}
        if len(roots) != 1 or any(Path(m.name).is_absolute() or ".." in Path(m.name).parts for m in members):
            raise RecipeError(label + " is not one safe root")
        stream.extractall(destination.parent / ".extract", members=members, filter="data")
    shutil.move(str(destination.parent / ".extract" / roots.pop()), destination)


def extract_member(archive, member, target):
    """source.member: the one regular file of that exact path in the (already verified) locked
    archive, written to target and accepted only with the recipe's SHA-256. Returns its receipt."""
    with tarfile.open(archive, "r:*") as stream:
        found = [m for m in stream.getmembers() if m.name == member["path"]]
        if len(found) != 1 or not found[0].isfile():
            raise RecipeError("source.member is not one regular file of the locked archive: " + member["path"])
        with stream.extractfile(found[0]) as source, open(target, "xb") as out:
            shutil.copyfileobj(source, out)
    if deploy.sha(target) != member["sha256"]:
        raise RecipeError("source.member differs from its recorded sha256: " + member["path"])
    return {"path": member["path"], "sha256": member["sha256"]}


def extract(archive, component, destination, patch, member=None):
    """Exact locked archive (or its locked inner archive, source.member) -> new source tree;
    patched through vendor_patch when the recipe names the reviewed -rx-only.patch. Returns the
    patch receipt, the archive the tree came from (its timestamp is SOURCE_DATE_EPOCH) and the
    member receipt (None without a member)."""
    if patch is not None:
        if member is not None:
            raise RecipeError("source.member and the -rx-only.patch together are not supported")
        import vendor_patch
        return vendor_patch.apply_from_archive(component["id"], archive, destination), archive, None
    if deploy.sha(archive) != component["source_archive_sha256"] or Path(archive).stat().st_size != component["source_archive_size"]:
        raise RecipeError("source archive differs from the lock")
    source, receipt = archive, None
    if member is not None:
        source = destination.parent / ("source-member" + "".join(Path(member["path"]).suffixes[-2:]))
        receipt = extract_member(archive, member, source)
    _extract_root(source, destination, "source member" if member is not None else "source archive")
    return {"component": component["id"], "patch": None}, source, receipt


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


def declared_configure_options(configure):
    """enable_*/with_* names of an autoconf-generated configure (its ac_user_opts list)."""
    match = re.search(r"^ac_user_opts='\n(.*?)'$", Path(configure).read_text(encoding="utf-8", errors="replace"), re.M | re.S)
    if not match:
        raise RecipeError("configure has no ac_user_opts list: not an autoconf-generated script")
    return set(match.group(1).split())


def check_configure(source, flags):
    """The release tarball's generated configure exists (autoreconf/autogen.sh are never run) and
    declares every flag of the recipe; the builder adds only --prefix=/usr."""
    configure = Path(source) / "configure"
    if configure.is_symlink() or not configure.is_file() or not os.access(configure, os.X_OK):
        raise RecipeError("autotools recipe needs the generated configure of a release tarball (no autoreconf)")
    declared = declared_configure_options(configure)
    unknown = sorted(f for f in flags if configure_name(f) not in declared)
    if unknown:
        raise RecipeError("configure flag is not declared upstream: " + ", ".join(unknown))
    return {"prefix": CONFIGURE_PREFIX, "flags": list(flags), "declared": len(declared)}


def run_hook(name, argv, values, env, log, cwd):
    """One recipe hook (python3 -I {recipe}/check_recipe.py ...): exit 0 and a JSON object on the
    last stdout line with ok true and no findings, or the build stops."""
    expanded = expand(argv, values)
    result = subprocess.run(expanded, cwd=cwd, env=env, capture_output=True, text=True)
    with open(log, "a", encoding="utf-8") as stream:
        stream.write("$ " + " ".join(expanded) + "\n" + result.stdout + result.stderr)
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    try:
        report = json.loads(lines[-1]) if lines else None
    except ValueError:
        report = None
    if result.returncode or type(report) is not dict or report.get("ok") is not True or report.get("findings", []) != []:
        findings = report.get("findings") if type(report) is dict else None
        raise RecipeError("hooks." + name + " failed (" + str(result.returncode) + "): " + json.dumps(findings)[:400])
    return {"hook": name, "argv": list(argv), "script_sha256": deploy.sha(values["recipe"] / "check_recipe.py"),
            "status": "CI_PASS", "report": report}


def hook_output(path):
    """The package hook's JSON file ({hook_out}): an object; its record_digests (an object) go into the record."""
    data = deploy.load(path)
    if type(data) is not dict or type(data.get("record_digests", {})) is not dict:
        raise RecipeError("package hook output must be a JSON object with an object record_digests")
    return data


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


def dt_needed(path):
    """DT_NEEDED entries of one ELF file (readelf -d)."""
    return re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]]+)\]", _tool(["readelf", "-d", str(path)]))


def forbid_needed(check, root):
    """No ELF file matched by check.files names a DT_NEEDED library matching check.needed; the
    globs must match at least one ELF file, or the check would prove nothing."""
    needed = {}
    for relative in tree_files(root):
        path = root / relative
        if (any(fnmatch.fnmatchcase(relative, g) for g in check["files"]) and path.is_file() and not path.is_symlink()
                and path.read_bytes()[:4] == b"\x7fELF"):
            needed[relative] = dt_needed(path)
    if not needed:
        raise RecipeError("forbid_needed matches no ELF file: " + ", ".join(check["files"]))
    hits = sorted("%s: %s" % (f, n) for f, names in needed.items() for n in names if any(fnmatch.fnmatchcase(n, g) for g in check["needed"]))
    if hits:
        raise RecipeError("forbidden DT_NEEDED: " + ", ".join(hits[:5]))
    return {"check": "forbid_needed", "files": check["files"], "needed": check["needed"], "dt_needed": needed, "status": "CI_PASS"}


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
        if kind == "forbid_needed":
            results.append(forbid_needed(check, root))
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


def shlibs_depends(package_root, staged, own_sonames, scratch, log):
    """dpkg-shlibdeps for the package's ELF files; libraries of this build map to (= version).
    No --ignore-missing-info: a library without shlibs/symbols information fails the build."""
    elves = [p for p in sorted(package_root.rglob("*")) if p.is_file() and not p.is_symlink() and p.read_bytes()[:4] == b"\x7fELF"]
    if not elves:
        return ""
    debian = scratch / "debian"
    debian.mkdir(parents=True, exist_ok=True)
    (debian / "control").write_text("Source: srrx-lab\n\nPackage: srrx-lab\nArchitecture: any\n", encoding="utf-8")
    (debian / "shlibs.local").write_text("".join(own_sonames), encoding="utf-8")
    libdirs = sorted({str(p) for p in staged.rglob("*") if p.is_dir() and any(c.name.startswith("lib") and ".so" in c.name for c in p.iterdir())})
    out = subprocess.run(["dpkg-shlibdeps", "-O"] + ["-l" + d for d in libdirs] + ["-e" + str(e) for e in elves],
                         cwd=scratch, capture_output=True, text=True)
    with open(log, "a", encoding="utf-8") as stream:
        stream.write("$ dpkg-shlibdeps (" + package_root.parent.name + ")\n" + out.stdout + out.stderr)
    if out.returncode:
        raise RecipeError("dpkg-shlibdeps failed: " + out.stderr.strip()[-400:])
    for line in out.stdout.splitlines():
        if line.startswith("shlibs:Depends="):
            return line.partition("=")[2].strip()
    return ""


def inventory_refusal(root):
    """Why deploy.build_inventory (the walk verify_build compares) refuses this package tree, or None.
    A dangling link (a -dev package's .so link into the runtime package) is named relative to root."""
    root = Path(root)
    dangling = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_symlink() and not p.exists())
    if dangling:
        return "not self-contained for verify_build: dangling link " + ", ".join(dangling[:5])
    try:
        deploy.build_inventory(root)
    except (OSError, deploy.DeploymentError) as exc:
        return "refused by deploy.build_inventory: " + str(exc)[:300]
    return None


def package_manifest(root):
    """verify_build manifest of one package's data tree, from deploy.build_inventory itself (the
    walk verify_build compares): status OPEN, filled for a reviewer. A tree that walk refuses (a
    -dev package's .so link into another package; a Lime library while the native TX audit is
    OPEN) gets an empty file list: it cannot pass verify_build on its own, whatever a reviewer
    fills in (inventory_refusal says why; build_deb logs it)."""
    files, modules = ({}, []) if inventory_refusal(root) else deploy.build_inventory(root)
    return {"schema_version": 1, "status": "OPEN", "files": files, "allowed_modules": sorted(modules),
            "source_audit": {"status": "OPEN", "report": {"path": None, "sha256": None}},
            "tx_negative_tests": {"status": "OPEN", "report": {"path": None, "sha256": None}}}


def package_data_tree(root):
    """The pure inventory of one package's data tree, as dpkg-deb packs it (DEBIAN/ excluded):
    {path: {type: file, sha256, mode} | {type: symlink, target} | {type: dir, mode}}, modes as
    4-digit octal. Unlike package_manifest it refuses nothing: a -dev package's dangling .so
    link and a Lime library are listed like any other path (deploy.deb_data_inventory reads the
    same entries from the .deb)."""
    root, tree = Path(root), {}
    for directory, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(dirs + files):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if relative == "DEBIAN" or relative.startswith("DEBIAN/"):
                continue
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                tree[relative] = {"type": "symlink", "target": os.readlink(path)}
            elif stat.S_ISDIR(info.st_mode):
                tree[relative] = {"type": "dir", "mode": "%04o" % stat.S_IMODE(info.st_mode)}
            elif stat.S_ISREG(info.st_mode):
                tree[relative] = {"type": "file", "sha256": deploy.sha(path), "mode": "%04o" % stat.S_IMODE(info.st_mode)}
            else:
                raise RecipeError("package tree holds a special file: " + relative)
        dirs[:] = [d for d in dirs if not (Path(directory) / d).is_symlink()]
    return dict(sorted(tree.items()))


def data_tree_document(package, version, tree):
    """<package>.data-tree.json: the data tree of one built package (data_tree_sha256 in the record)."""
    return {"schema_version": 1, "kind": DATA_TREE_KIND, "package": package, "version": version, "entries": tree}


def control_extras(package, version, sonames):
    """DEBIAN files beyond control/md5sums: shlibs for the SONAME'd libraries this package ships
    (consumers then depend on >= this lab version) and the ldconfig trigger (Debian policy 8.1.1)."""
    if not sonames:
        return {}
    return {"shlibs": "".join("%s %s %s (>= %s)\n" % (library, soversion, package, version) for library, soversion in sonames),
            "triggers": "activate-noawait ldconfig\n"}


def build_deb(package, version, files, staged, epoch, depends, out, scratch, sonames=(), log=None):
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
    refusal = inventory_refusal(root)
    if refusal and log is not None:
        with open(log, "a", encoding="utf-8") as stream:
            stream.write("build manifest of " + package["name"] + " has no file list: " + refusal + "\n")
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
    for name, text in control_extras(package["name"], version, sonames).items():
        (control / name).write_text(text, encoding="utf-8", newline="\n")
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_dir() and not path.is_symlink():
            os.chmod(path, 0o755)
        if path.parent == control and path.is_file():
            os.chmod(path, 0o644)
        os.utime(path, (epoch, epoch), follow_symlinks=False)
    os.utime(root, (epoch, epoch))
    tree = package_data_tree(root)  # after the mode normalisation, i.e. what dpkg-deb packs
    deb = out / (package["name"] + "_" + version + "_arm64.deb")
    subprocess.run(["dpkg-deb", "--root-owner-group", "-Zxz", "--build", str(root), str(deb)], check=True,
                   capture_output=True, env=dict(os.environ, SOURCE_DATE_EPOCH=str(epoch)))
    return deb, manifest, tree


def lab_depends_manifest(path):
    """The lab_build_depends lab_build.py installed (lab-debs/manifest.json), as recorded."""
    if path is None:
        return []
    items = deploy.load(path)
    if type(items) is not list:
        raise RecipeError("lab package manifest must be a list")
    for item in items:
        deploy.keys(item, ("package", "version", "sha256", "component", "record_sha256"), "lab package")
    return items


def build(recipe_path, archive, work, out, jobs, lab_debs=None):
    recipe = deploy.load(recipe_path)
    component = validate_recipe(recipe)
    lock = deploy.load(DEPLOYMENT / "sources.lock.json")
    network = no_network()
    installed = lab_depends_manifest(lab_debs)
    if sorted(i["package"] for i in installed) != sorted(recipe["lab_build_depends"]):
        raise RecipeError("the chroot's lab packages differ from lab_build_depends")
    work, out = Path(work), Path(out)
    for path in (work, out):
        if path.exists() and any(path.iterdir()):
            raise RecipeError("work and output directories must be new or empty")
        path.mkdir(parents=True, exist_ok=True)
    src, build_dir, destdir, log = work / "src", work / "build", work / "destdir", out / (recipe["component"] + ".build.log")
    view, here = spec(recipe), recipe_dir(recipe["component"])
    receipt, source_archive, member = extract(archive, component, src, view["patch"], view["member"])
    epoch = source_date_epoch(source_archive)
    env = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "HOME": str(work), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
           "SOURCE_DATE_EPOCH": str(epoch), "TZ": "UTC"}
    values = {"src": src, "build": build_dir, "destdir": destdir, "jobs": jobs, "recipe": here, "hook_out": work / "package-hook.json"}
    hooks, recipe_files = [], {}
    if view["hooks"]["source_check"] is not None:  # the extracted tree, before the listed patches
        hooks.append(run_hook("source_check", view["hooks"]["source_check"], values, env, log, work))
    import vendor_patch
    receipts = vendor_patch.apply_listed(src, here, view["patches"])
    options = configure_options = None
    if view["build_system"] == "cmake":
        cmake = recipe["cmake"]
        configure = expand(cmake["configure"], values) + ["-D%s=%s" % (k, v) for k, v in sorted({**cmake["variables"], **cmake["options"]}.items())]
        run(configure, work, env, log)
        options = check_options(src, build_dir, cmake["options"])
    else:
        build_dir.mkdir()
        if view["build_system"] == "autotools":  # in the source tree, as dh_auto_configure does by default
            configure_options = check_configure(src, view["flags"])
            run([str(src / "configure"), "--prefix=" + CONFIGURE_PREFIX] + view["flags"], src, env, log)
    for step in recipe["build"]:
        run(expand(step, values), work, env, log)
    destdir.mkdir()
    if recipe["install"]["cmake_install"]:
        run(["cmake", "--install", str(build_dir)], work, dict(env, DESTDIR=str(destdir)), log)
    if view["make_install"]:
        run(["make", "-C", str(src), "install", "DESTDIR=" + str(destdir)], work, env, log)
    for item in recipe["install"]["copy"]:
        matches = sorted(glob.glob(expand([item["from"]], values)[0]))
        if not matches:
            raise RecipeError("install copy matched nothing: " + item["from"])
        target = destdir / item["to"]
        target.mkdir(parents=True, exist_ok=True)
        for match in matches:
            if item["from"].startswith("{recipe}/"):
                recipe_files[Path(match).relative_to(here).as_posix()] = deploy.sha(match)
            if os.path.islink(match):
                os.symlink(os.readlink(match), target / os.path.basename(match))
            else:
                shutil.copy2(match, target / os.path.basename(match))
    digests = None
    if view["hooks"]["package"] is not None:  # may rewrite DESTDIR; the checks and file assignment come after it
        entry = run_hook("package", view["hooks"]["package"], values, env, log, work)
        if "{hook_out}" in " ".join(view["hooks"]["package"]):
            output = hook_output(values["hook_out"])
            shutil.copyfile(values["hook_out"], out / (recipe["component"] + ".package-hook.json"))
            entry.update(output=recipe["component"] + ".package-hook.json", output_sha256=deploy.sha(values["hook_out"]))
            digests = output.get("record_digests")
        hooks.append(entry)
    if hooks:
        recipe_files["check_recipe.py"] = deploy.sha(here / "check_recipe.py")
    checks = run_checks(recipe, destdir)
    bad = [f for f in tree_files(destdir) if any(part.lower() in deploy.BAD_PARTS for part in f.split("/"))
           or f.rsplit("/", 1)[-1].lower() in deploy.forbidden_basenames()]
    if bad:
        raise RecipeError("TX/control executable or plugin staged: " + ", ".join(bad[:5]))
    owners = assign(recipe, destdir)
    version = component["version"]
    sonames = {p["name"]: [] for p in recipe["packages"]}  # (library, SONAME version) shipped per package
    for package in recipe["packages"]:
        for relative in owners[package["name"]]:
            path = destdir / relative
            if path.is_file() and not path.is_symlink() and ".so" in path.name and path.read_bytes()[:4] == b"\x7fELF":
                for soname in re.findall(r"Library soname: \[([^\]]+)\]", _tool(["readelf", "-d", str(path)])):
                    match = re.fullmatch(r"(.+)\.so\.(.+)", soname)
                    if match:
                        sonames[package["name"]].append((match.group(1), match.group(2)))
    own = ["%s %s %s (= %s)\n" % (library, soversion, name, version) for name, items in sonames.items() for library, soversion in items]
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
            depends = shlibs_depends(stage, destdir, own, scratch, log)
        deb, manifest, tree = build_deb(package, version, files, destdir, epoch, depends, out, scratch, sonames[package["name"]], log)
        manifest_path = out / (package["name"] + ".build-manifest.json")
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        tree_path = out / (package["name"] + ".data-tree.json")
        tree_path.write_text(json.dumps(data_tree_document(package["name"], version, tree), indent=2, sort_keys=True) + "\n",
                             encoding="utf-8", newline="\n")
        packages.append({"package": package["name"], "version": version, "architecture": "arm64", "filename": deb.name,
                         "sha256": deploy.sha(deb), "size": deb.stat().st_size, "build_manifest_sha256": deploy.sha(manifest_path),
                         "data_tree_sha256": deploy.sha(tree_path)})
    dpkg_list = subprocess.run(["dpkg-query", "-W", "-f", "${Package} ${Version} ${Architecture}\\n"], capture_output=True, text=True, check=True).stdout
    environment = "".join(sorted(dpkg_list.splitlines(keepends=True)))
    (out / (recipe["component"] + ".chroot-packages.txt")).write_text(environment, encoding="utf-8", newline="\n")
    record = {"schema_version": 1, "kind": "srrx_lab_build_record", "status": "CI_BUILT_UNREVIEWED", "component": recipe["component"],
              "version": version, "recipe_sha256": deploy.sha(recipe_path), "source_archive_sha256": component["source_archive_sha256"],
              "apt_snapshot": lock["apt_snapshot"]["timestamp"],
              "build_environment": {"chroot_packages_sha256": hashlib.sha256(environment.encode()).hexdigest(),
                                    "chroot_package_count": len(environment.splitlines()), "network": network,
                                    "source_date_epoch": epoch, "patch_receipt": receipt, "patch_receipts": receipts,
                                    "source_member": member, "build_system": view["build_system"], "cmake_options": options,
                                    "configure_options": configure_options, "hooks": hooks, "recipe_files": recipe_files,
                                    "lab_build_depends": installed},
              "packages": packages, "checks": checks, "hardware_ready": False}
    if digests is not None:  # the package hook's record_digests (deploy.verify_repo accepts the field)
        record["record_digests"] = digests
    (out / (recipe["component"] + ".build-record.json")).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--lab-debs", type=Path, help="manifest of the lab packages lab_build.py installed in the chroot")
    args = parser.parse_args()
    try:
        record = build(args.recipe, args.archive, args.work, args.out, args.jobs, args.lab_debs)
    except (OSError, ValueError, subprocess.SubprocessError, tarfile.TarError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps({k: record[k] for k in ("component", "version", "status", "packages")}, indent=2))


if __name__ == "__main__":
    main()
