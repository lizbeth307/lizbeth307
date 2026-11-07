#!/usr/bin/env python3
"""Offline checks and the build hooks of the SatDump +lab recipe (stdlib only, no network).

  check                  recipe.json (the build_recipe schema 2 recipe) against packaging.json,
                         upstream-options.json, the patches, the source lock and the receive-only policy
  verify-source --source DIR
                         hooks.source_check: an extracted pinned source tree before source.patches:
                         upstream file blobs, every option() of every CMakeLists.txt/*.cmake equal to the
                         manifest, every listed patch applies exactly, every ON plugin directory builds
                         add_library(<directory name> SHARED), the EXTERNAL_PLUGINS default is empty
  package --root DIR [--manifest OUT]
                         hooks.package: a DESTDIR install tree: keep only the five pipelines
                         (elektro_ggak_mqtt removed), write satdump_cfg.json as strict JSON with
                         kepler_update_interval "Never", empty fetch lists, URL template and Space-Track
                         fields, and no "://" string left; drop headers/desktop files/icons, require
                         exactly the allowlisted plugins; OUT ({hook_out}) lists every file with its
                         SHA256, the record_digests of the installation record (build_recipe copies them
                         into the build record) and installation_template, the record an administrator
                         completes at commissioning (its evidence_id placeholder is refused as it is)

The builder recipe is recipe.json; everything else this script needs is packaging.json (pinned
upstream blobs, installation layout, allowlists, config steps, builder check list) and
upstream-options.json. Their SHA-256 values are pinned below (DATA_SHA256): the build record binds
this script (recipe_files, hooks), so it binds both data files too; and recipe.json carries one note
with the SHA-256 of this script and both data files (pin_note), so the installation record's
recipe_sha256 (decoder_policy compares it with the deployed recipe.json) binds them as well. All
three subcommands refuse a stale pin or data file before reading anything. Plugin file names come from the
upstream directory, not from the option name: PLUGIN_FY2 builds plugins/fengyun2_support
(plugins/CMakeLists.txt:26-27 and plugins/fengyun2_support/CMakeLists.txt:6 at 1aedd60), so the file
is libfengyun2_support.so. Nothing here compiles, fetches or runs SatDump. Findings name rule ids and
relative paths only.
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
# packaging.json and upstream-options.json as reviewed with this script (check: data_file_digest).
DATA_SHA256 = {"packaging.json": "84da22b74c219b9e4d71c63e702b68528b641b5c16c2c71ae3d438ca1bca72c7",
               "upstream-options.json": "923f48f0f1a487c50c5259baf75b5a5fd2c0d2326d3ef68b7fb259911e4fec5c"}
# recipe.json carries one note with the SHA-256 of these files (pin_note), so recipe_sha256 binds them.
PINNED_FILES = ("check_recipe.py", "packaging.json", "upstream-options.json")
PIN_NOTE = ("Pinned recipe files (SHA-256; the installation record's recipe_sha256 binds them through this note): "
            "check_recipe.py %s, packaging.json %s, upstream-options.json %s")
OPTION = re.compile(r"\boption\s*\(\s*([A-Za-z0-9_]+)\s+\"((?:[^\"\\]|\\.)*)\"\s*(ON|OFF)?\s*\)", re.S | re.I)
ALLOWED_ON = frozenset(("BUILD_OPENMP", "ENABLE_INSTALL", "PLUGIN_METEOR", "PLUGIN_NOAA_METOP", "PLUGIN_AWS",
                        "PLUGIN_ELEKTRO_ARKTIKA", "PLUGIN_XRIT", "PLUGIN_FY2", "PLUGIN_NET_SOURCE_SDR_SUPPORT"))
# CMAKE_INSTALL_RPATH (STACK.md:142): libelektro_arktika_support.so links libxrit_support.so, which
# lives only in the plugin directory; libsatdump_core.so is in /usr/lib, a default loader path.
# EXTERNAL_PLUGINS keeps its empty upstream default (the builder never passes an empty value).
FIXED = {"CMAKE_BUILD_TYPE": "Release", "CMAKE_INSTALL_PREFIX": "/usr", "CMAKE_INSTALL_LIBDIR": "lib",
         "CMAKE_INSTALL_RPATH": "/usr/lib/satdump/plugins", "FETCHCONTENT_FULLY_DISCONNECTED": "ON"}
CONFIGURE = ["cmake", "-S", "{src}", "-B", "{build}", "-G", "Ninja"]
BUILD = [["cmake", "--build", "{build}", "--parallel", "{jobs}"]]
HOOKS = {"source_check": ["python3", "-I", "{recipe}/check_recipe.py", "verify-source", "--source", "{src}"],
         "package": ["python3", "-I", "{recipe}/check_recipe.py", "package", "--root", "{destdir}", "--manifest", "{hook_out}"]}
# Configure needs (src-core/CMakeLists.txt:229-300 at 1aedd60): jemalloc, volk, PNG, fftw3f, nng, CURL,
# SQLite3, tiff; Ninja for -G Ninja. Never Armadillo (optional find_package), zstd (BUILD_ZIQ OFF),
# HDF5, SDR/USB/audio development packages or GUI libraries.
BUILD_DEPENDS = ("ninja-build", "libjemalloc-dev", "libvolk-dev", "libpng-dev", "libfftw3-dev", "libnng-dev",
                 "libcurl4-openssl-dev", "libsqlite3-dev", "libtiff-dev")
FORBIDDEN_BUILD_DEPENDS = ("libarmadillo-dev", "libzstd-dev", "libhdf5-dev", "librtlsdr-dev", "libhackrf-dev",
                           "libairspy-dev", "libairspyhf-dev", "libbladerf-dev", "libsoapysdr-dev", "libuhd-dev",
                           "libiio-dev", "libad9361-dev", "libusb-1.0-0-dev", "portaudio19-dev", "librtaudio-dev",
                           "libglfw3-dev", "ocl-icd-opencl-dev")
PACKAGE_FILES = ["usr/bin/satdump", "usr/lib/libsatdump_core.so", "usr/lib/satdump/plugins/*", "usr/share/satdump/*"]
CI = {"heavy": True, "runtime_depends": ["binutils", "strace"], "tag_samples": []}
CHECK_STATUSES = ("RUNTIME_CHECK", "HOST_TEST", "BLOCKED_NO_LICENSED_FIXTURE", "PENDING_DEVICE")
BUILDER_CHECKS = {"plugin-set": "RUNTIME_CHECK", "ldd": "RUNTIME_CHECK", "no-connect": "RUNTIME_CHECK",
                  "cli-forms": "RUNTIME_CHECK", "planted-pipelines-json": "RUNTIME_CHECK", "omm-csv": "HOST_TEST",
                  "lrpt-fixture": "BLOCKED_NO_LICENSED_FIXTURE", "lrpt-cadu-cut": "BLOCKED_NO_LICENSED_FIXTURE",
                  "live-localhost": "PENDING_DEVICE"}
# The OMM CSV reader of the pinned tree (src-core/db/kepler/kepler_utils.cpp, blob in packaging.json
# upstream_files, ccsdsOmmToKepler): one line = 17 fields split on "," (no CSV quoting), the epoch
# read with "%4d-%2d-%2dT%2d:%2d:%lf", numbers with std::stod; any other field count or a failing
# conversion drops the line (the header line does). Index -> the OMM field it reads (None: unread).
OMM_CSV_READER = {"file": "src-core/db/kepler/kepler_utils.cpp", "function": "ccsdsOmmToKepler", "fields": 17, "separator": ",",
                  "epoch_format": "%4d-%2d-%2dT%2d:%2d:%lf",
                  "columns": ["OBJECT_NAME", "OBJECT_ID", "EPOCH", "MEAN_MOTION", "ECCENTRICITY", "INCLINATION",
                              "RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY", None, None, "NORAD_CAT_ID",
                              "ELEMENT_SET_NO", "REV_AT_EPOCH", "BSTAR", "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT"]}
# The installation record the administrator completes (decoder_policy.load_satdump_installation): this
# placeholder fails decoder_policy's evidence_id pattern, so the template is never accepted as it is.
TEMPLATE_EVIDENCE = "REPLACE_WITH_REVIEWED_EVIDENCE <sr-rx-packages run id>"
NETWORK_WORDS = ("curl", "wget", "git clone", "git fetch", "pip install", "apt-get", "http://", "https://")
MAX_TREE_FILES = 20_000
MAX_TREE_BYTES = 2 * 1024 * 1024 * 1024
RECIPE_KEYS = {"schema_version", "component", "summary", "source", "build_system", "build_depends", "lab_build_depends",
               "cmake", "autotools", "build", "install", "hooks", "packages", "drop", "checks", "notes", "ci"}
PACKAGING_KEYS = {"schema_version", "kind", "component", "source", "package", "upstream_files", "install", "builder_checks",
                  "sources"}


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
    """recipe.json, or a data file whose SHA-256 must equal DATA_SHA256 (refused otherwise)."""
    data = (HERE / name).read_bytes()
    if name in DATA_SHA256 and hashlib.sha256(data).hexdigest() != DATA_SHA256[name]:
        raise RecipeError("data_file_digest:" + name)
    return strict_json(data.decode("utf-8"))


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


def plugin_library(option):
    """lib<upstream directory name>.so of one PLUGIN_* manifest entry (verify_source checks add_library)."""
    return "lib" + option["subdirectory"].rsplit("/", 1)[-1] + ".so"


def plugin_id(library):
    """The receive-only-policy allow_plugins id of a library: selftest._plugin_name with the suffixes
    _sdr_support / _support (libfengyun2_support.so -> fengyun2, libnet_source_support.so -> net_source)."""
    name = library[len("lib"):] if library.startswith("lib") else library
    name = name.split(".so", 1)[0]
    for suffix in ("_sdr_support", "_support"):
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[:-len(suffix)]
    return name


def on_plugin_libraries(recipe, options):
    """{option name: library file} of every ON PLUGIN_* option; KeyError when the manifest has no directory."""
    manifest = {option["name"]: option for option in options["options"]}
    return {name: plugin_library(manifest[name]) for name, value in recipe["cmake"]["options"].items()
            if value == "ON" and name.startswith("PLUGIN_")}


def required_paths(packaging):
    """DESTDIR paths the recipe's require_paths checks name, one check each (a check passes on any match)."""
    install = packaging["install"]
    return ([install["executable"], install["core_library"], install["config"]]
            + [install["plugin_dir"] + "/" + name for name in install["expected_plugins"]]
            + [install["pipeline_dir"] + "/" + name for name in install["keep_pipelines"]])


def tree_digest(top, *, owner_check=None):
    """SHA256 over "<sha256>  <relative path>\\n" of every regular file below top, sorted by path.

    The same digest as srrx.decoder_policy.satdump_tree_digest (resources_sha256 of the
    installation record). A link or special file refuses; directories are not bound.
    """
    top, lines, count, total = Path(top), [], 0, 0
    if top.is_symlink() or not top.is_dir():
        raise RecipeError("tree_missing")
    for path in sorted(top.rglob("*")):
        info = path.lstat()
        if owner_check is not None:
            owner_check(path, info)
        if path.is_symlink():
            raise RecipeError("symlink_in_tree")
        if path.is_dir():
            continue
        if not path.is_file():
            raise RecipeError("special_file_in_tree")
        count, total = count + 1, total + info.st_size
        if count > MAX_TREE_FILES or total > MAX_TREE_BYTES:
            raise RecipeError("tree_limit")
        lines.append((path.relative_to(top).as_posix(), sha256(path)))
    text = "".join("%s  %s\n" % (digest, name) for name, digest in sorted(lines))
    return hashlib.sha256(text.encode("utf-8", "surrogateescape")).hexdigest()


def pin_note():
    """The recipe.json note that pins this script and both data files by SHA-256. The installation
    record's recipe_sha256 is the SHA-256 of recipe.json (decoder_policy compares it with the deployed
    file), so through this note it binds the hook script and the packaging data as well."""
    return PIN_NOTE % tuple(sha256(HERE / name) for name in PINNED_FILES)


def _data_findings():
    """The committed state: data files as pinned in DATA_SHA256, and recipe.json's pin note current."""
    findings = []
    for name, digest in sorted(DATA_SHA256.items()):
        path = HERE / name
        if not path.is_file() or sha256(path) != digest:
            findings.append("data_file_digest:" + name)
    try:
        notes = strict_json((HERE / "recipe.json").read_text(encoding="utf-8")).get("notes")
    except (OSError, ValueError):
        notes = None
    pins = [n for n in notes if type(n) is str and n.startswith(PIN_NOTE.split(":", 1)[0] + ":")] if type(notes) is list else []
    if pins != [pin_note()]:
        findings.append("recipe_pin_note")
    return findings


def _recipe_findings(recipe, packaging):
    """The builder recipe's fixed shape: one cmake build of the locked archive with the listed patches."""
    findings = []
    if (set(recipe) != RECIPE_KEYS or recipe["schema_version"] != 2 or recipe["component"] != "satdump"
            or recipe["build_system"] != "cmake" or recipe["autotools"] is not None):
        return ["recipe_schema"]
    source = recipe["source"]
    if source.get("patch") is not None or source.get("member") is not None:
        findings.append("recipe_source")
    if recipe["cmake"].get("configure") != CONFIGURE or recipe["build"] != BUILD:
        findings.append("recipe_steps")
    if recipe["install"] != {"cmake_install": True, "make_install": False, "copy": []}:
        findings.append("recipe_install")
    if recipe["hooks"] != HOOKS:
        findings.append("recipe_hooks")
    if recipe["lab_build_depends"] != [] or recipe["drop"] != []:
        findings.append("recipe_lab_build_depends_or_drop")
    if recipe["ci"] != CI:
        findings.append("recipe_ci")
    packages = recipe["packages"]
    if (len(packages) != 1 or packages[0].get("name") != packaging["package"]["name"] or packages[0].get("files") != PACKAGE_FILES
            or packages[0].get("depends") != [] or packages[0].get("shlibs_depends") is not True):
        findings.append("recipe_package")
    for name in recipe["build_depends"]:
        if name in FORBIDDEN_BUILD_DEPENDS:
            findings.append("build_depends_forbidden:" + name)
    if tuple(recipe["build_depends"]) != BUILD_DEPENDS:
        findings.append("build_depends_changed")
    variables = recipe["cmake"]["variables"]
    for name in sorted(set(FIXED) | set(variables)):
        if variables.get(name) != FIXED.get(name):
            findings.append("fixed_variable:" + name)
    checks = recipe["checks"]
    required = [c["globs"] for c in checks if c.get("kind") == "require_paths"]
    if required != [[path] for path in required_paths(packaging)]:
        findings.append("require_paths_differ_from_packaging")
    if [c["kind"] for c in checks if c.get("kind") != "require_paths"] != ["forbid_paths", "forbid_needed"]:
        findings.append("checks_shape")
    text = json.dumps([recipe["cmake"]["configure"], recipe["build"]]).lower()
    if any(word in text for word in NETWORK_WORDS):
        findings.append("build_network")
    return findings


def check(recipe=None, options=None, policy=None, packaging=None):
    """Recipe-only checks; returns the list of findings (empty when the recipe is consistent)."""
    findings = _data_findings() if recipe is None and options is None and packaging is None else []
    if findings:  # an unpinned data file is never read
        return findings
    recipe = load("recipe.json") if recipe is None else recipe
    options = load("upstream-options.json") if options is None else options
    packaging = load("packaging.json") if packaging is None else packaging
    if policy is None:
        policy = strict_json((PROJECT / "deployment/receive-only-policy.json").read_text(encoding="utf-8"))
    if set(packaging) != PACKAGING_KEYS or packaging["kind"] != "srrx_satdump_packaging" or packaging["component"] != "satdump":
        return findings + ["packaging_schema"]
    findings += _recipe_findings(recipe, packaging)
    if "recipe_schema" in findings:
        return findings
    lock = {c["id"]: c for c in strict_json((PROJECT / "deployment/sources.lock.json").read_text(encoding="utf-8"))["components"]}
    source = packaging["source"]
    if (lock["satdump"]["commit"] != source["commit"] or lock["satdump"]["source_archive_sha256"] != source["archive_sha256"]
            or options["commit"] != source["commit"] or packaging["package"]["version"] != lock["satdump"]["version"]):
        findings.append("source_lock_mismatch")
    values = recipe["cmake"]["options"]
    names = [option["name"] for option in options["options"]]
    if len(names) != len(set(names)):
        findings.append("manifest_duplicate_option")
    for name in names:
        if name not in values:
            findings.append("option_not_set:" + name)
    for name, value in values.items():
        if name not in names:
            findings.append("unknown_option:" + name)
        elif value not in ("ON", "OFF"):
            findings.append("option_value:" + name)
    on = {name for name, value in values.items() if value == "ON"}
    if on != ALLOWED_ON:
        findings.append("on_set_not_allowlist")
    if values.get("PLUGINS_ALL") != "OFF":
        findings.append("plugins_all_not_off")
    allow = set(policy["components"]["satdump"]["allow_plugins"])
    install = packaging["install"]
    try:
        libraries = set(on_plugin_libraries(recipe, options).values())
    except KeyError:
        libraries = None
        findings.append("plugin_subdirectory_unknown")
    if libraries is not None:
        # The names the loader really opens: lib<upstream directory>.so, never derived from the option name.
        if {plugin_id(library) for library in libraries} != allow:
            findings.append("plugins_differ_from_policy")
        if set(install["expected_plugins"]) != libraries:
            findings.append("expected_plugins_differ_from_options")
        manifest = {option["name"]: option for option in options["options"]}
        for name in sorted(on_plugin_libraries(recipe, options)):
            if manifest[name]["subdirectory"] + "/CMakeLists.txt" not in packaging["upstream_files"]:
                findings.append("plugin_cmakelists_not_bound:" + name)
    if set(install["keep_pipelines"]) != set(policy["components"]["satdump"]["allow_pipelines"]):
        findings.append("pipelines_differ_from_policy")
    changed = {}
    for entry in recipe["source"]["patches"]:
        path = HERE / entry["file"]
        if not path.is_file() or sha256(path) != entry["sha256"]:
            findings.append("patch_digest:" + entry["file"])
            continue
        text = path.read_text(encoding="utf-8")
        targets = set(re.findall(r"^\+\+\+ b/(\S+)$", text, re.M))
        if targets != set(entry["targets"]):
            findings.append("patch_targets:" + entry["file"])
        for target, blob in entry["targets"].items():
            # The blob just before this patch: the pinned upstream blob unless an earlier patch changed the file.
            if target not in changed and target in packaging["upstream_files"] and packaging["upstream_files"][target] != blob:
                findings.append("patch_target_blob:" + target)
            changed[target] = True
    if OMM_CSV_READER["file"] not in packaging["upstream_files"]:
        findings.append("omm_reader_not_bound")
    found = {c.get("id"): c.get("status") for c in packaging["builder_checks"]}
    if found != BUILDER_CHECKS or len(packaging["builder_checks"]) != len(BUILDER_CHECKS):
        findings.append("builder_checks")
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


def verify_source(tree, recipe=None, options=None, packaging=None):
    """Findings for an extracted pinned source tree (hooks.source_check: before source.patches)."""
    findings = _data_findings() if recipe is None and options is None and packaging is None else []
    if findings:  # an unpinned data file is never read
        return findings
    recipe = load("recipe.json") if recipe is None else recipe
    options = load("upstream-options.json") if options is None else options
    packaging = load("packaging.json") if packaging is None else packaging
    tree = Path(tree)
    for relative, blob in sorted(packaging["upstream_files"].items()):
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
    by_name = {option["name"]: option for option in options["options"]}
    for name in sorted(on_plugin_libraries(recipe, options)):
        directory = by_name[name]["subdirectory"]
        target = directory.rsplit("/", 1)[-1]
        path = tree / directory / "CMakeLists.txt"
        text = strip_cmake_comments(path.read_text(encoding="utf-8", errors="replace")) if path.is_file() else ""
        # lib<target>.so in ${CMAKE_INSTALL_LIBDIR}/satdump/plugins, with no renaming property.
        if (not re.search(r"\badd_library\s*\(\s*" + re.escape(target) + r"\s+SHARED\b", text)
                or not re.search(r"\binstall\s*\(\s*TARGETS\s+" + re.escape(target)
                                 + r"\s+DESTINATION\s+\$\{CMAKE_INSTALL_LIBDIR\}/satdump/plugins\s*\)", text)
                or re.search(r"\b(OUTPUT_NAME|LIBRARY_OUTPUT_NAME|PREFIX|SUFFIX)\b", text)):
            findings.append("plugin_library_name:" + directory)
    # EXTERNAL_PLUGINS is not passed to CMake: its default must be the empty string.
    for name, entry in sorted(options.get("cache_strings", {}).items()):
        path = tree / entry["file"]
        text = strip_cmake_comments(path.read_text(encoding="utf-8", errors="replace")) if path.is_file() else ""
        if not re.search(r"\bset\s*\(\s*" + re.escape(name) + r"\s+" + re.escape(json.dumps(entry["default"])) + r"\s+CACHE\s+STRING\b", text):
            findings.append("cache_string_default:" + name)
    for entry in recipe["source"]["patches"]:
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
    """The executable, core library, plugin and resources trees and the config: real files only, never links."""
    for relative in (install["executable"], install["core_library"], install["plugin_dir"], install["resources_dir"],
                     install["config"]):
        top = root / relative
        for path in [top] + (sorted(top.rglob("*")) if top.is_dir() and not top.is_symlink() else []):
            if path.is_symlink():
                raise RecipeError("symlink_in_stage:" + path.relative_to(root).as_posix())


def package(root, packaging=None):
    """Apply the packaging steps to a DESTDIR tree in place; returns {relative path: sha256}."""
    packaging = load("packaging.json") if packaging is None else packaging
    root, install = Path(root), packaging["install"]
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
    if "://" in json.dumps(document):  # any URL left (fetch lists, url_template, a new upstream key)
        raise RecipeError("config_url_left")
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
    if not (root / install["core_library"]).is_file():
        raise RecipeError("core_library_missing")
    return {p.relative_to(root).as_posix(): sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}


def record_digests(root, files, packaging=None):
    """The digest fields of the decoder_policy installation record for one packaged stage."""
    packaging = load("packaging.json") if packaging is None else packaging
    install, root = packaging["install"], Path(root)
    return {"sha256": files[install["executable"]], "core_sha256": files[install["core_library"]],
            "resources_sha256": tree_digest(root / install["resources_dir"]),
            "plugins": {name: files[install["plugin_dir"] + "/" + name] for name in install["expected_plugins"]},
            "pipelines": {name: files[install["pipeline_dir"] + "/" + name] for name in install["keep_pipelines"]},
            "config_sha256": files[install["config"]], "recipe_sha256": sha256(HERE / "recipe.json")}


def installation_template(digests, packaging=None):
    """The record of decoder_policy.load_satdump_installation, field for field, with record_digests and
    an evidence_id placeholder that decoder_policy refuses (INSTALLATION_VERSION_OR_PROVENANCE_UNVERIFIED):
    the administrator installs it root-owned (<= 8 KiB) at commissioning, never this file as it is."""
    packaging = load("packaging.json") if packaging is None else packaging
    return dict({"v": 1, "tool_id": "satdump", "version": packaging["package"]["version"],
                 "source_commit": packaging["source"]["commit"], "executable": "/" + packaging["install"]["executable"],
                 "evidence_id": TEMPLATE_EVIDENCE}, **digests)


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
            findings = _data_findings()
            if not findings:
                files = package(args.root)
                if args.manifest is not None:
                    digests = record_digests(args.root, files)
                    with args.manifest.open("x", encoding="utf-8", newline="\n") as stream:
                        stream.write(json.dumps({"v": 1, "kind": "srrx_satdump_stage", "files": files, "record_digests": digests,
                                                 "installation_template": installation_template(digests)}, indent=1) + "\n")
    except (RecipeError, OSError, ValueError, KeyError) as error:
        findings = ["error:" + (str(error) if isinstance(error, RecipeError) else type(error).__name__)]
    print(json.dumps({"command": args.command, "findings": findings, "ok": not findings}))
    return 0 if not findings else 2


if __name__ == "__main__":
    sys.exit(main())
