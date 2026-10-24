#!/usr/bin/env python3
"""Offline checks and packaging steps of the SatDump +lab recipe (stdlib only, no network).

  check                  recipe.json against upstream-options.json, the patches and the receive-only policy
  verify-source --source DIR
                         an extracted pinned source tree: upstream file blobs, every option() of every
                         CMakeLists.txt/*.cmake equal to the manifest, every patch applies exactly
  package --root DIR [--manifest OUT]
                         a DESTDIR install tree: keep only the five pipelines (elektro_ggak_mqtt removed),
                         write satdump_cfg.json as strict JSON with kepler_update_interval "Never" and no
                         TLE URLs, drop headers/desktop files, require exactly the allowlisted plugins;
                         OUT lists every file with its SHA256 (input for the installation record)

The arm64 build itself is the package builder's job (recipe.json "build"); nothing here
compiles, fetches or runs SatDump. Findings name rule ids and relative paths only.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
OPTION = re.compile(r"\boption\s*\(\s*([A-Za-z0-9_]+)\s+\"((?:[^\"\\]|\\.)*)\"\s*(ON|OFF)?\s*\)", re.S | re.I)
ALLOWED_ON = frozenset(("BUILD_OPENMP", "ENABLE_INSTALL", "PLUGIN_METEOR", "PLUGIN_NOAA_METOP", "PLUGIN_AWS",
                        "PLUGIN_ELEKTRO_ARKTIKA", "PLUGIN_XRIT", "PLUGIN_FY2", "PLUGIN_NET_SOURCE_SDR_SUPPORT"))
FIXED = {"CMAKE_BUILD_TYPE": "Release", "CMAKE_INSTALL_PREFIX": "/usr", "CMAKE_INSTALL_LIBDIR": "lib",
         "EXTERNAL_PLUGINS": ""}
NETWORK_WORDS = ("curl", "wget", "git clone", "git fetch", "pip install", "apt-get", "http://", "https://")
RECIPE_KEYS = {"schema_version", "kind", "id", "status", "status_note", "source", "package", "upstream_files",
               "patches", "cmake", "build", "install", "builder_checks", "sources"}


class RecipeError(ValueError):
    pass


def strict_json(data):
    def unique(pairs):
        keys = [key for key, unused in pairs]
        if len(keys) != len(set(keys)):
            raise RecipeError("duplicate JSON key")
        return dict(pairs)
    return json.loads(data, object_pairs_hook=unique,
                      parse_constant=lambda unused: (_ for _ in ()).throw(RecipeError("non-finite JSON")))


def load(name):
    return strict_json((HERE / name).read_text(encoding="utf-8"))


def strip_cmake_comments(text):
    out = []
    for line in text.split("\n"):
        quoted, keep = False, []
        for character in line:
            if character == '"':
                quoted = not quoted
            if character == "#" and not quoted:
                break
            keep.append(character)
        out.append("".join(keep))
    return "\n".join(out)


def parse_cmake_options(text):
    """[(name, default)] of every option() in one CMake file; comments ignored, default OFF when omitted."""
    return [(name, (default or "OFF").upper()) for name, unused, default in OPTION.findall(strip_cmake_comments(text))]


def strip_json_comments(text):
    """JSON with // and /* */ comments (SatDump config and pipelines) -> plain JSON text."""
    out, index, quoted = [], 0, False
    while index < len(text):
        character = text[index]
        if quoted:
            out.append(character)
            if character == "\\" and index + 1 < len(text):
                out.append(text[index + 1])
                index += 1
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
            out.append(character)
        elif text.startswith("//", index):
            end = text.find("\n", index)
            index = len(text) if end < 0 else end
            continue
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end < 0:
                raise RecipeError("unterminated comment")
            index = end + 2
            continue
        else:
            out.append(character)
        index += 1
    return "".join(out)


def git_blob(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(recipe=None, options=None, policy=None):
    """Recipe-only checks; returns the list of findings (empty when the recipe is consistent)."""
    recipe = load("recipe.json") if recipe is None else recipe
    options = load("upstream-options.json") if options is None else options
    if policy is None:
        policy = strict_json((PROJECT / "deployment/receive-only-policy.json").read_text(encoding="utf-8"))
    findings = []
    if set(recipe) != RECIPE_KEYS or recipe["kind"] != "srrx_build_recipe" or recipe["id"] != "satdump":
        return ["recipe_schema"]
    lock = {c["id"]: c for c in strict_json((PROJECT / "deployment/sources.lock.json").read_text(encoding="utf-8"))["components"]}
    source = recipe["source"]
    if (lock["satdump"]["commit"] != source["commit"] or lock["satdump"]["source_archive_sha256"] != source["archive_sha256"]
            or options["commit"] != source["commit"] or recipe["package"]["version"] != lock["satdump"]["version"]):
        findings.append("source_lock_mismatch")
    definitions = recipe["cmake"]["definitions"]
    names = [option["name"] for option in options["options"]]
    if len(names) != len(set(names)):
        findings.append("manifest_duplicate_option")
    for name in names:
        if name not in definitions:
            findings.append("option_not_set:" + name)
    for name, value in definitions.items():
        if name in FIXED:
            if value != FIXED[name]:
                findings.append("fixed_definition:" + name)
        elif name not in names:
            findings.append("unknown_definition:" + name)
        elif value not in ("ON", "OFF"):
            findings.append("option_value:" + name)
    on = {name for name, value in definitions.items() if value == "ON"}
    if on != ALLOWED_ON:
        findings.append("on_set_not_allowlist")
    if definitions.get("PLUGINS_ALL") != "OFF":
        findings.append("plugins_all_not_off")
    allow = set(policy["components"]["satdump"]["allow_plugins"])
    on_plugins = {name[len("PLUGIN_"):].lower() for name in on if name.startswith("PLUGIN_")}
    on_plugins = {name[:-len("_sdr_support")] if name.endswith("_sdr_support") else name for name in on_plugins}
    if on_plugins != allow:
        findings.append("plugins_differ_from_policy")
    expected = {"lib%s_support.so" % name for name in allow}
    if set(recipe["install"]["expected_plugins"]) != expected:
        findings.append("expected_plugins_differ_from_policy")
    if set(recipe["install"]["keep_pipelines"]) != set(policy["components"]["satdump"]["allow_pipelines"]):
        findings.append("pipelines_differ_from_policy")
    for entry in recipe["patches"]:
        path = HERE / entry["file"]
        if not path.is_file() or sha256(path) != entry["sha256"]:
            findings.append("patch_digest:" + entry["file"])
            continue
        text = path.read_text(encoding="utf-8")
        targets = set(re.findall(r"^\+\+\+ b/(\S+)$", text, re.M))
        if targets != set(entry["targets"]):
            findings.append("patch_targets:" + entry["file"])
    text = json.dumps(recipe["build"]).lower()
    if recipe["build"]["network"] != "none" or any(word in text for word in NETWORK_WORDS):
        findings.append("build_network")
    if recipe["status"] != "PENDING_BUILDER" and any(c["status"].startswith("PENDING") for c in recipe["builder_checks"]):
        findings.append("status_claims_more_than_checks")
    return findings


def _apply_exact(text, patch, target):
    """One file's hunks of a unified diff applied without fuzz or offset; refuses anything else."""
    lines, out, section = patch.split("\n"), text.split("\n"), False
    delta, index = 0, 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("--- a/"):
            section = line[len("--- a/"):] == target
            index += 2
            continue
        match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
        if section and match:
            old, new, index = [], [], index + 1
            while index < len(lines) and lines[index][:1] in (" ", "-", "+"):
                if lines[index][:1] in (" ", "-"):
                    old.append(lines[index][1:])
                if lines[index][:1] in (" ", "+"):
                    new.append(lines[index][1:])
                index += 1
            position = int(match.group(1)) - 1 + delta
            if out[position:position + len(old)] != old:
                raise RecipeError("patch_does_not_apply:" + target)
            out[position:position + len(old)] = new
            delta += len(new) - len(old)
            continue
        index += 1
    return "\n".join(out)


def verify_source(tree, recipe=None, options=None):
    """Findings for an extracted pinned source tree (the builder runs this before patching)."""
    recipe = load("recipe.json") if recipe is None else recipe
    options = load("upstream-options.json") if options is None else options
    tree, findings = Path(tree), []
    for relative, blob in sorted(recipe["upstream_files"].items()):
        path = tree / relative
        if not path.is_file() or git_blob(path.read_bytes()) != blob:
            findings.append("upstream_file:" + relative)
    found = []
    for path in sorted(list(tree.rglob("CMakeLists.txt")) + list(tree.rglob("*.cmake"))):
        relative = path.relative_to(tree).as_posix()
        for name, default in parse_cmake_options(path.read_text(encoding="utf-8", errors="replace")):
            found.append({"name": name, "default": default, "file": relative})
    manifest = sorted((o["name"], o["default"], o["file"]) for o in options["options"])
    if sorted((o["name"], o["default"], o["file"]) for o in found) != manifest:
        findings.append("options_manifest_drift")
    for entry in recipe["patches"]:
        patch = (HERE / entry["file"]).read_text(encoding="utf-8")
        for target, blob in entry["targets"].items():
            path = tree / target
            if not path.is_file() or git_blob(path.read_bytes()) != blob:
                findings.append("patch_base:" + target)
                continue
            try:
                _apply_exact(path.read_text(encoding="utf-8"), patch, target)
            except RecipeError as error:
                findings.append(str(error))
    return findings


def _set(document, keys, value):
    node = document
    for key in keys[:-1]:
        if not isinstance(node, dict) or key not in node:
            raise RecipeError("config_key_missing:" + "/".join(keys))
        node = node[key]
    if not isinstance(node, dict) or keys[-1] not in node:
        raise RecipeError("config_key_missing:" + "/".join(keys))
    node[keys[-1]] = value


def _no_links(root, install):
    """The executable, plugin and pipeline trees and the config: real files only, never links."""
    for relative in (install["executable"], install["plugin_dir"], install["pipeline_dir"], install["config"]):
        top = root / relative
        for path in [top] + (sorted(top.rglob("*")) if top.is_dir() and not top.is_symlink() else []):
            if path.is_symlink():
                raise RecipeError("symlink_in_stage:" + path.relative_to(root).as_posix())


def package(root, recipe=None):
    """Apply the packaging steps to a DESTDIR tree in place; returns {relative path: sha256}."""
    recipe = load("recipe.json") if recipe is None else recipe
    root, install = Path(root), recipe["install"]
    _no_links(root, install)
    pipelines = root / install["pipeline_dir"]
    if not pipelines.is_dir():
        raise RecipeError("pipeline_dir_missing")
    for path in sorted(pipelines.rglob("*"), reverse=True):
        relative = path.relative_to(pipelines).as_posix()
        if path.is_dir():
            if not any(path.iterdir()):
                path.rmdir()
            continue
        if relative not in install["keep_pipelines"]:
            path.unlink()  # every other pipeline, .json.inc and nested file
    for name in install["keep_pipelines"]:
        path = pipelines / name
        if not path.is_file():
            raise RecipeError("allowlisted_pipeline_missing:" + name)
        document = strict_json(strip_json_comments(path.read_text(encoding="utf-8")))
        for identifier in install["remove_pipeline_ids"].get(name, []):
            if identifier not in document:
                raise RecipeError("pipeline_id_missing:" + identifier)
            del document[identifier]
        path.write_text(json.dumps(document, indent=4) + "\n", encoding="utf-8", newline="\n")
    if sorted(p.name for p in pipelines.iterdir()) != sorted(install["keep_pipelines"]):
        raise RecipeError("pipeline_set")
    config = root / install["config"]
    document = strict_json(strip_json_comments(config.read_text(encoding="utf-8")))
    for item in install["config_set"]:
        _set(document, item["path"], item["value"])
    config.write_text(json.dumps(document, indent=4) + "\n", encoding="utf-8", newline="\n")
    for relative in install["remove_trees"]:
        target = root / relative
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    plugins = root / install["plugin_dir"]
    if not plugins.is_dir() or sorted(p.name for p in plugins.iterdir()) != sorted(install["expected_plugins"]):
        raise RecipeError("plugin_set_not_allowlist")
    if not (root / install["executable"]).is_file():
        raise RecipeError("executable_missing")
    return {p.relative_to(root).as_posix(): sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    source = commands.add_parser("verify-source")
    source.add_argument("--source", type=Path, required=True)
    stage = commands.add_parser("package")
    stage.add_argument("--root", type=Path, required=True)
    stage.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            findings = check()
        elif args.command == "verify-source":
            findings = verify_source(args.source)
        else:
            files = package(args.root)
            findings = []
            if args.manifest is not None:
                with args.manifest.open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(json.dumps({"v": 1, "kind": "srrx_satdump_stage", "files": files}, indent=1) + "\n")
    except (RecipeError, OSError, ValueError, KeyError) as error:
        findings = ["error:" + (str(error) if isinstance(error, RecipeError) else type(error).__name__)]
    print(json.dumps({"command": args.command, "findings": findings, "ok": not findings}))
    return 0 if not findings else 2


if __name__ == "__main__":
    sys.exit(main())
