"""Allowlisted, file-only civil weather decoding; no arbitrary command interface.

Installation records are trusted administrator acceptance data, not job parameters.
Metadata binds an approved recording to its digest; it is not a content classifier.
EGC/DSC are unavailable: no unverified packet format is parsed by this module.

satdump-weather (v2.1, build/15 decision 6) is installation-gated, not disabled: an accepted
record binds the SatDump ELF, the exact plugin set (deployment/recipes/satdump allowlist),
the five allowlisted pipeline files and the packaged config (kepler_update_interval Never)
by SHA256; satdump_plan() accepts only an srrx.baseband recording (Meteor-M LRPT, ci16
256 kS/s, made by labrx under the v2.1 policy) for the pipelines of baseband.PIPELINES, and
satdump_publish() releases only sanitized PNG images and a fixed-schema report. The unit
and argv are srrx.satdump_pass; nothing here launches SatDump.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import struct
import subprocess
import tempfile
import time
import wave
import zlib

from .scope_policy import ScopeLatch, scope_check


NOAA_COMMIT = "48a9eb8321f722634aafd1f9dcf4d80e9bfe274d"
NOAA_VERSION = "1.4.1"
PRESET = "noaa-apt-weather"
MAX_INPUT_BYTES = 256 * 1024 * 1024
MAX_IMAGE_BYTES = 64 * 1024 * 1024
MAX_PIXELS = 40_000_000
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_EVIDENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,191}\Z")
_SOURCE_FIELDS = {"v", "sha256", "purpose", "satellite", "origin", "evidence_id",
                  "voice_present", "private_payload", "military", "emitter_geolocation",
                  "iq_retained", "format"}
_INSTALL_FIELDS = {"v", "tool_id", "version", "source_commit", "executable",
                   "sha256", "evidence_id"}
# Whole 137-138 MHz VHF weather-satellite band: any scope stop in it refuses APT decode/export.
APT_SPAN_HZ = (137_000_000.0, 138_000_000.0)
_DISABLED = {
    # srrx.egc_gate exists but stays unreleased (C2 table, ПОЛ-06, checksum unverified).
    "egc-safetynet": "DISABLED_NO_VERIFIED_HEADER_PARSER_AND_TEST_VECTORS",
    "dsc-safety": "DISABLED_NO_VERIFIED_FORMAT_CATEGORY_PARSER_AND_TEST_VECTORS",
    "amateur-digital": "DISABLED_NO_VERIFIED_DECODE_ONLY_PRESET",
    "ais-public": "DISABLED_NO_VERIFIED_PRE_PAYLOAD_MILITARY_FILTER",
    "adsb-public": "DISABLED_NO_QUALIFIED_DATABASE_AND_MILITARY_FILTER",
}


class DecoderRefused(ValueError):
    """Stable public refusal code; never embeds input text or decoder output."""


def _refuse(code):
    raise DecoderRefused(code)


def _keys(value, expected, code):
    if not isinstance(value, dict) or set(value) != expected:
        _refuse(code)


def _digest(value):
    return isinstance(value, str) and _HEX.fullmatch(value) is not None


def _file(path, *, executable=False):
    path = Path(path)
    if not path.is_absolute():
        _refuse("ABSOLUTE_FILE_PATH_REQUIRED")
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or path.resolve() != path:
            _refuse("REGULAR_NON_SYMLINK_FILE_REQUIRED")
        if executable and (info.st_uid != 0 or info.st_mode & 0o022 or not info.st_mode & 0o111):
            _refuse("ADMIN_OWNED_EXECUTABLE_REQUIRED")
        return path
    except OSError:
        _refuse("FILE_UNAVAILABLE")


def _admin_directories(path):
    """Only root may rename a trusted file's path between its hash check and use."""
    for parent in path.parents:
        try:
            info = os.lstat(parent)
        except OSError:
            _refuse("FILE_UNAVAILABLE")
        if info.st_uid != 0 or (info.st_mode & 0o022 and not info.st_mode & stat.S_ISVTX):
            _refuse("ADMIN_OWNED_DIRECTORY_REQUIRED")


def _hash_file(path, limit):
    digest, count = hashlib.sha256(), 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            count += len(block)
            if count > limit:
                _refuse("FILE_SIZE_LIMIT")
            digest.update(block)
    return digest.hexdigest(), count


def _validate_source(metadata):
    _keys(metadata, _SOURCE_FIELDS, "SOURCE_METADATA_SCHEMA")
    if type(metadata["v"]) is not int or metadata["v"] != 1 or not _digest(metadata["sha256"]):
        _refuse("SOURCE_METADATA_SCHEMA")
    if any(not isinstance(metadata[key], str) for key in
           ("purpose", "satellite", "origin", "format", "evidence_id")):
        _refuse("SOURCE_METADATA_SCHEMA")
    if (metadata["purpose"] != "public_civil_weather" or
            metadata["satellite"] not in {"NOAA-15", "NOAA-18", "NOAA-19"} or
            metadata["origin"] not in {"approved_labrx_audio", "approved_public_archive"} or
            metadata["format"] != "wav_pcm_s16le_mono" or
            not isinstance(metadata["evidence_id"], str) or
            not _EVIDENCE.fullmatch(metadata["evidence_id"])):
        _refuse("SOURCE_NOT_APPROVED_CIVIL_APT_AUDIO")
    for key in ("voice_present", "private_payload", "military", "emitter_geolocation", "iq_retained"):
        if metadata[key] is not False:
            _refuse("SOURCE_SCOPE_DENIED")


def _validate_installation(record):
    _keys(record, _INSTALL_FIELDS, "INSTALLATION_SCHEMA")
    if (type(record["v"]) is not int or record["v"] != 1 or record["tool_id"] != "noaa-apt" or
            record["version"] != NOAA_VERSION or record["source_commit"] != NOAA_COMMIT or
            not _digest(record["sha256"]) or not isinstance(record["evidence_id"], str) or
            not _EVIDENCE.fullmatch(record["evidence_id"])):
        _refuse("INSTALLATION_VERSION_OR_PROVENANCE_UNVERIFIED")
    if not isinstance(record["executable"], str) or len(record["executable"]) > 4096:
        _refuse("INSTALLATION_SCHEMA")
    path = _file(record["executable"], executable=True)
    if path.name != "noaa-apt":
        _refuse("EXECUTABLE_NOT_ALLOWLISTED")
    _admin_directories(path)  # execute() runs this path after re-hashing it
    # No script/interpreter or PATH lookup can be smuggled in as a tool.
    with path.open("rb") as stream:
        if stream.read(4) != b"\x7fELF":
            _refuse("NATIVE_VENDOR_EXECUTABLE_REQUIRED")
    actual, _ = _hash_file(path, MAX_INPUT_BYTES)
    if actual != record["sha256"]:
        _refuse("EXECUTABLE_DIGEST_CHANGED")
    return path


def load_installation(path):
    """Read one root-owned, non-writable trusted installation acceptance record."""
    path = _file(path)
    info = path.stat()
    if info.st_uid != 0 or info.st_mode & 0o022 or info.st_size > 8192:
        _refuse("TRUSTED_ADMIN_INSTALLATION_RECORD_REQUIRED")
    _admin_directories(path)
    try:
        record = json.loads(path.read_text())
    except (OSError, UnicodeError, ValueError):
        _refuse("INSTALLATION_SCHEMA")
    _validate_installation(record)
    return record


def availability(installation=None, satdump_installation=None):
    """No device probing, decoder launch, header parsing or PATH discovery."""
    status = "UNAVAILABLE_NO_ACCEPTED_INSTALLATION"
    if installation is not None:
        try:
            _validate_installation(installation)
            status = "FILE_PRESET_ACCEPTED_INTERFACE_PROBE_REQUIRED_AT_RUN"
        except (DecoderRefused, OSError):
            status = "UNAVAILABLE_INSTALLATION_NOT_QUALIFIED"
    satdump = "UNAVAILABLE_NO_ACCEPTED_INSTALLATION"
    if satdump_installation is not None:
        try:
            _validate_satdump_installation(satdump_installation)
            satdump = "LRPT_FILE_PRESET_ACCEPTED_INTERFACE_PROBE_REQUIRED_AT_RUN"
        except (DecoderRefused, OSError):
            satdump = "UNAVAILABLE_INSTALLATION_NOT_QUALIFIED"
    return {PRESET: status, SATDUMP_PRESET: satdump, **_DISABLED}


# ---------------------------------------------------------------- satdump-weather (v2.1)

SATDUMP_PRESET = "satdump-weather"
SATDUMP_COMMIT = "1aedd602055c154401384a8cc7876713bb371254"
SATDUMP_VERSION = "2.0.0~alpha+git20260929+lab1"
# deployment/receive-only-policy.json components.satdump.allow_plugins; upstream names the
# library lib<id>_support.so (plugins/*/CMakeLists.txt at 1aedd60).
SATDUMP_PLUGINS = ("meteor", "noaa_metop", "aws", "elektro_arktika", "xrit", "fy2", "net_source")
SATDUMP_PIPELINE_FILES = ("Meteor-M.json", "MetOp.json", "AWS.json", "FengYun-2.json", "Elektro_Arktika.json")
SATDUMP_PLUGIN_DIR = "/usr/lib/satdump/plugins"
SATDUMP_PIPELINE_DIR = "/usr/share/satdump/resources/pipelines"
SATDUMP_CONFIG = "/usr/share/satdump/satdump_cfg.json"
MAX_PRODUCTS = 64
MAX_PRODUCT_TOTAL_BYTES = 256 * 1024 * 1024
_SATDUMP_FIELDS = {"v", "tool_id", "version", "source_commit", "executable", "sha256", "evidence_id",
                   "plugins", "pipelines", "config_sha256", "recipe_sha256"}


def _plugin_file(name):
    return "lib" + name + "_support.so"


def _admin_owned(info):
    return info.st_uid == 0 and not info.st_mode & 0o022


def _admin_file(path, limit):
    """Root-owned, not group/world-writable regular file below root-owned directories; its SHA256."""
    path = _file(path)
    if not _admin_owned(path.lstat()):
        _refuse("ADMIN_OWNED_FILE_REQUIRED")
    _admin_directories(path)
    return _hash_file(path, limit)[0]


def _exact_directory(directory, expected):
    try:
        names = {entry.name for entry in os.scandir(directory)}
    except OSError:
        _refuse("FILE_UNAVAILABLE")
    if names != set(expected):
        _refuse("SATDUMP_FILE_SET_NOT_ALLOWLISTED")


def _validate_satdump_installation(record):
    _keys(record, _SATDUMP_FIELDS, "INSTALLATION_SCHEMA")
    if (type(record["v"]) is not int or record["v"] != 1 or record["tool_id"] != "satdump" or
            record["version"] != SATDUMP_VERSION or record["source_commit"] != SATDUMP_COMMIT or
            not _digest(record["sha256"]) or not _digest(record["config_sha256"]) or
            not _digest(record["recipe_sha256"]) or not isinstance(record["evidence_id"], str) or
            not _EVIDENCE.fullmatch(record["evidence_id"])):
        _refuse("INSTALLATION_VERSION_OR_PROVENANCE_UNVERIFIED")
    plugins, pipelines = record["plugins"], record["pipelines"]
    if (not isinstance(plugins, dict) or set(plugins) != {_plugin_file(name) for name in SATDUMP_PLUGINS} or
            not isinstance(pipelines, dict) or set(pipelines) != set(SATDUMP_PIPELINE_FILES) or
            not all(_digest(value) for value in list(plugins.values()) + list(pipelines.values()))):
        _refuse("SATDUMP_FILE_SET_NOT_ALLOWLISTED")
    if not isinstance(record["executable"], str) or len(record["executable"]) > 4096:
        _refuse("INSTALLATION_SCHEMA")
    path = _file(record["executable"], executable=True)
    if path.name != "satdump":
        _refuse("EXECUTABLE_NOT_ALLOWLISTED")
    _admin_directories(path)
    with path.open("rb") as stream:
        if stream.read(4) != b"\x7fELF":
            _refuse("NATIVE_VENDOR_EXECUTABLE_REQUIRED")
    if _hash_file(path, MAX_INPUT_BYTES)[0] != record["sha256"]:
        _refuse("EXECUTABLE_DIGEST_CHANGED")
    # The loader takes every file of the plugin directory and every *.json of the pipeline
    # tree (src-core/core/plugin.cpp, src-core/pipeline/pipeline.cpp): both must be exactly the set.
    _exact_directory(SATDUMP_PLUGIN_DIR, plugins)
    _exact_directory(SATDUMP_PIPELINE_DIR, pipelines)
    for directory, files in ((SATDUMP_PLUGIN_DIR, plugins), (SATDUMP_PIPELINE_DIR, pipelines)):
        for name, digest in sorted(files.items()):
            if _admin_file(Path(directory) / name, MAX_INPUT_BYTES) != digest:
                _refuse("SATDUMP_FILE_DIGEST_CHANGED")
    if _admin_file(Path(SATDUMP_CONFIG), 1024 * 1024) != record["config_sha256"]:
        _refuse("SATDUMP_CONFIG_DIGEST_CHANGED")
    try:
        config = json.loads(Path(SATDUMP_CONFIG).read_text(encoding="utf-8"))
        never = config["satdump_general"]["kepler_update_interval"]["value"] == "Never"
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        never = False
    if not never:
        _refuse("SATDUMP_KEPLER_UPDATE_NOT_NEVER")
    return path


def load_satdump_installation(path):
    """One root-owned, non-writable SatDump installation record (deployment/recipes/satdump)."""
    path = _file(path)
    info = path.stat()
    if info.st_uid != 0 or info.st_mode & 0o022 or info.st_size > 8192:
        _refuse("TRUSTED_ADMIN_INSTALLATION_RECORD_REQUIRED")
    _admin_directories(path)
    try:
        record = json.loads(path.read_text())
    except (OSError, UnicodeError, ValueError):
        _refuse("INSTALLATION_SCHEMA")
    _validate_satdump_installation(record)
    return record


def satdump_executable(installation):
    """Revalidate the installation (ELF, plugin and pipeline sets, config); the ELF path."""
    return _validate_satdump_installation(installation)


def satdump_plan(recording, installation, *, scope=None):
    """Reviewable manifest of one LRPT file decode; recording is srrx.baseband metadata."""
    from . import baseband
    try:
        meta = baseband.validate_metadata(recording)["global"]
    except baseband.BasebandRefused:
        _refuse("SOURCE_NOT_APPROVED_LRPT_BASEBAND")
    if meta["srrx:pipeline"] not in baseband.PIPELINES.values() or meta["srrx:target"] not in baseband.METEOR_TARGETS:
        _refuse("SOURCE_NOT_APPROVED_LRPT_BASEBAND")
    _scope_permits(scope, "decode")  # the whole 137-138 MHz band, as APT; before any installation access
    _validate_satdump_installation(installation)
    return {"v": 1, "preset": SATDUMP_PRESET, "tool_id": "satdump", "version": SATDUMP_VERSION,
            "source_commit": SATDUMP_COMMIT, "pipeline": meta["srrx:pipeline"], "source_sha512": meta["core:sha512"],
            "executable_sha256": installation["sha256"], "samples": meta["srrx:samples"],
            "argv_template": ["${ACCEPTED_SATDUMP}", "pipeline", meta["srrx:pipeline"], "baseband", "${APPROVED_BASEBAND}",
                              "${OUTPUT_DIR}", "--samplerate=%d" % baseband.OUTPUT_RATE_HZ, "--baseband_format=cs16"],
            "shell": False, "live_source": False, "stdout_stored": False, "stderr_stored": False,
            "output": "weather_png_without_text_metadata", "hardware_qualified": False}


def satdump_publish(output_directory, target, plan, *, scope=None):
    """Publish only sanitized PNG images of a SatDump output tree, then a fixed-schema report.

    Symlinks and special files are never followed; CADU, soft symbols, products.cbor and
    logs stay in the work tree, which the caller removes. target must not exist.
    """
    source, target = Path(output_directory), Path(target)
    if not target.is_absolute() or target.exists() or target.is_symlink():
        _refuse("NEW_ABSOLUTE_OUTPUT_DIRECTORY_REQUIRED")
    if not source.is_dir() or source.is_symlink():
        _refuse("SATDUMP_OUTPUT_MISSING")
    images, total, seen = [], 0, 0
    stack = [source]
    while stack:
        directory = stack.pop()
        for entry in sorted(os.scandir(directory), key=lambda item: item.name):
            seen += 1
            if seen > 4096:
                _refuse("SATDUMP_OUTPUT_LIMIT")
            if entry.is_dir(follow_symlinks=False):
                if len(stack) < 64:
                    stack.append(Path(entry.path))
                continue
            if not entry.is_file(follow_symlinks=False) or not entry.name.lower().endswith(".png"):
                continue
            image, dimensions = _sanitized_png(Path(entry.path))
            total += len(image)
            if len(images) >= MAX_PRODUCTS or total > MAX_PRODUCT_TOTAL_BYTES:
                _refuse("SATDUMP_OUTPUT_LIMIT")
            images.append((image, dimensions))
    if not images:
        _refuse("SATDUMP_NO_IMAGE_PRODUCT")
    publication = target.parent / ("." + target.name + ".publishing")
    if publication.exists() or publication.is_symlink():
        _refuse("OUTPUT_DESTINATION_CHANGED")
    publication.mkdir()
    try:
        entries = []
        for index, (image, dimensions) in enumerate(images):
            name = "image-%02d.png" % index
            (publication / name).write_bytes(image)
            entries.append({"file": name, "sha256": hashlib.sha256(image).hexdigest(), "bytes": len(image),
                            "image": dimensions})
        report = {"v": 1, "status": "FILE_DECODE_COMPLETED", "preset": SATDUMP_PRESET, "pipeline": plan["pipeline"],
                  "source_sha512": plan["source_sha512"], "executable_sha256": plan["executable_sha256"],
                  "source_commit": SATDUMP_COMMIT, "images": entries, "stdout_stored": False, "stderr_stored": False,
                  "input_iq": True, "input_iq_deleted_after_decode": True, "physical_tests_performed": False}
        (publication / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        if target.exists() or target.is_symlink():
            _refuse("OUTPUT_DESTINATION_CHANGED")
        _scope_permits(scope, "export")  # a stop during the run leaves no published result
        os.rename(publication, target)
        return report
    except BaseException:
        for child in publication.iterdir() if publication.is_dir() else ():
            child.unlink()
        if publication.is_dir():
            publication.rmdir()
        raise


def _wav_info(path):
    try:
        with wave.open(str(path), "rb") as stream:
            if (stream.getcomptype() != "NONE" or stream.getnchannels() != 1 or
                    stream.getsampwidth() != 2 or not 8000 <= stream.getframerate() <= 192000 or
                    not 1 <= stream.getnframes() <= MAX_INPUT_BYTES // 2):
                _refuse("MONO_PCM16_APT_WAV_REQUIRED")
            frames, sample_rate = stream.getnframes(), stream.getframerate()
            # Verify the declared sample data is present, not just a plausible header.
            remaining = frames * 2
            while remaining:
                block = stream.readframes(min(remaining // 2, 65536))
                if not block or len(block) % 2:
                    _refuse("TRUNCATED_WAV")
                remaining -= len(block)
            return {"frames": frames, "sample_rate_hz": sample_rate}
    except (wave.Error, EOFError, OSError):
        _refuse("MONO_PCM16_APT_WAV_REQUIRED")


def _scope_permits(scope, operation):
    """Only adds refusals: masked-band stop always; the session Artemis latch when given."""
    if scope is not None and not isinstance(scope, ScopeLatch):
        _refuse("SCOPE_LATCH_REQUIRED")
    try:
        stopped = scope_check(*APT_SPAN_HZ)["stop"] or (
            scope is not None and scope.permits(operation, APT_SPAN_HZ) is not True)
    except ValueError:
        stopped = True
    if stopped:
        _refuse("OUT_OF_SCOPE")


def make_plan(preset, source, metadata, installation, *, scope=None):
    """Return a reviewable manifest, never a caller-editable executable plan."""
    if not isinstance(preset, str):
        _refuse("PRESET_NOT_ALLOWLISTED")
    if preset in _DISABLED:
        _refuse(_DISABLED[preset])  # Happens before source/header/address access.
    if preset == SATDUMP_PRESET:
        _refuse("SATDUMP_PRESET_IS_SATDUMP_PLAN")  # LRPT baseband only, through srrx.satdump_pass
    if preset != PRESET:
        _refuse("PRESET_NOT_ALLOWLISTED")
    _validate_source(metadata)
    _scope_permits(scope, "decode")  # before any installation or source file access
    _validate_installation(installation)
    source = _file(source)
    actual, size = _hash_file(source, MAX_INPUT_BYTES)
    if actual != metadata["sha256"]:
        _refuse("SOURCE_DIGEST_CHANGED")
    wav = _wav_info(source)
    return {"v": 1, "preset": PRESET, "tool_id": "noaa-apt", "version": NOAA_VERSION,
            "source_commit": NOAA_COMMIT, "source_sha256": actual,
            "executable_sha256": installation["sha256"], "input_bytes": size, "wav": wav,
            "argv_template": ["${ACCEPTED_NOAA_APT}", "${APPROVED_WAV}", "-o", "${OUTPUT_PNG}",
                              "--map", "no", "--rotate", "no", "--quiet"],
            "shell": False, "live_source": False, "stdout_stored": False, "stderr_stored": False,
            "output": "weather_png_without_text_metadata", "hardware_qualified": False}


def _bounded_process(argv, cwd, timeout_s, *, capture_probe=False):
    """Private transport, called only with internally constructed argument lists."""
    env = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C", "HOME": str(cwd),
           "XDG_CONFIG_HOME": str(cwd / "config"), "XDG_CACHE_HOME": str(cwd / "cache")}
    process = None
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE if capture_probe else subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, shell=False, start_new_session=True,
                                   close_fds=True)
        if not capture_probe:
            return process.wait(timeout=timeout_s), b""
        data, deadline = bytearray(), time.monotonic() + timeout_s
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    _refuse("DECODER_TIMEOUT")
                for key, _ in selector.select(remaining):
                    block = os.read(key.fileobj.fileno(), 1024)
                    if not block:
                        selector.unregister(key.fileobj)
                    else:
                        data.extend(block)
                        if len(data) > 16384:
                            _refuse("INTERFACE_RESPONSE_LIMIT")
            return process.wait(timeout=max(0.001, deadline - time.monotonic())), bytes(data)
    except subprocess.TimeoutExpired:
        _refuse("DECODER_TIMEOUT")
    except OSError:
        _refuse("DECODER_PROCESS_UNAVAILABLE")
    finally:
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            if process.stdout is not None:
                process.stdout.close()


def _sanitized_png(path):
    """Keep only image chunks, dropping arbitrary text/EXIF/ancillary metadata."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_IMAGE_BYTES:
        _refuse("WEATHER_PNG_MISSING_OR_OVERSIZE")
    data = path.read_bytes()
    signature = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(signature):
        _refuse("INVALID_WEATHER_PNG")
    result, pos, seen_header, seen_data, seen_end = bytearray(signature), 8, False, False, False
    while pos < len(data):
        if pos + 12 > len(data):
            _refuse("INVALID_WEATHER_PNG")
        length = struct.unpack_from(">I", data, pos)[0]
        end = pos + length + 12
        if end > len(data):
            _refuse("INVALID_WEATHER_PNG")
        kind, body = data[pos + 4:pos + 8], data[pos + 8:end - 4]
        if zlib.crc32(kind + body) & 0xffffffff != struct.unpack_from(">I", data, end - 4)[0]:
            _refuse("INVALID_WEATHER_PNG")
        if not seen_header:
            if kind != b"IHDR" or length != 13:
                _refuse("INVALID_WEATHER_PNG")
            width, height = struct.unpack_from(">II", body)
            if not width or not height or width * height > MAX_PIXELS:
                _refuse("PNG_DIMENSION_LIMIT")
            seen_header = True
        elif kind == b"IHDR":
            _refuse("INVALID_WEATHER_PNG")
        if kind == b"IDAT":
            seen_data = True
        if kind in {b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND"}:
            result.extend(data[pos:end])
        elif not kind[0] & 32:
            _refuse("UNKNOWN_CRITICAL_PNG_CHUNK")
        pos = end
        if kind == b"IEND":
            if length or pos != len(data) or not seen_data:
                _refuse("INVALID_WEATHER_PNG")
            seen_end = True
            break
    if not seen_end:
        _refuse("INVALID_WEATHER_PNG")
    return bytes(result), {"width": width, "height": height}


def execute(preset, source, metadata, installation, output_directory, *, timeout_s=60, scope=None):
    """Revalidate a job and run only the fixed vendor WAV→PNG command.

    No argv, shell, environment, device, pipeline name or decoded-text sink can
    be supplied by a job. The output directory must not exist; failed runs leave
    no result directory. The installation record is administrator-trusted input.
    A scope stop latched during the run discards the temporary output unpublished.
    """
    if (isinstance(timeout_s, bool) or not isinstance(timeout_s, (float, int)) or
            not math.isfinite(timeout_s) or not 0.05 <= timeout_s <= 300):
        _refuse("TIMEOUT_RANGE")
    plan = make_plan(preset, source, metadata, installation, scope=scope)
    target = Path(output_directory)
    if not target.is_absolute() or target.exists() or target.is_symlink():
        _refuse("NEW_ABSOLUTE_OUTPUT_DIRECTORY_REQUIRED")
    parent = target.parent
    if not parent.is_dir() or parent.resolve() != parent:
        _refuse("OUTPUT_PARENT_UNAVAILABLE")
    with tempfile.TemporaryDirectory(prefix="srrx-decoder-", dir=parent) as temporary:
        work = Path(temporary)
        source_copy = work / "input.wav"
        # Hash the exact private snapshot the decoder receives, before launch.
        with open(source, "rb") as original, source_copy.open("xb") as snapshot:
            copied = 0
            for block in iter(lambda: original.read(1024 * 1024), b""):
                copied += len(block)
                if copied > MAX_INPUT_BYTES:
                    _refuse("FILE_SIZE_LIMIT")
                snapshot.write(block)
        if _hash_file(source_copy, MAX_INPUT_BYTES)[0] != plan["source_sha256"]:
            _refuse("SOURCE_CHANGED_DURING_SNAPSHOT")
        _wav_info(source_copy)
        executable = _validate_installation(installation)
        # Upstream 1.4.1 --version checks the Internet unconditionally. --help
        # exits inside argument parsing; exact version/provenance instead comes
        # from the administrator-accepted source commit and executable SHA256.
        code, help_text = _bounded_process([str(executable), "--help"], work, min(timeout_s, 3),
                                           capture_probe=True)
        markers = (b"Decode NOAA APT", b"--output", b"--map", b"--rotate", b"--quiet", b"input_filename")
        if code or not all(marker in help_text for marker in markers):
            _refuse("LIVE_VENDOR_INTERFACE_UNVERIFIED")
        # Check again after the probe; help text is not provenance evidence.
        _validate_installation(installation)
        output = work / "output.png"
        argv = [str(executable), str(source_copy), "-o", str(output),
                "--map", "no", "--rotate", "no", "--quiet"]
        code, _ = _bounded_process(argv, work, timeout_s)
        if code:
            _refuse("DECODER_NONZERO_EXIT")
        image, dimensions = _sanitized_png(output)
        report = {"v": 1, "status": "FILE_DECODE_COMPLETED", "preset": PRESET,
                  "source_sha256": plan["source_sha256"], "executable_sha256": installation["sha256"],
                  "source_commit": NOAA_COMMIT, "output_sha256": hashlib.sha256(image).hexdigest(),
                  "output_bytes": len(image), "image": dimensions, "stdout_stored": False,
                  "stderr_stored": False, "input_iq": False, "physical_tests_performed": False}
        # Publish only sanitized image + fixed-schema report, never tool logs/config/data files.
        publication = work / "publication"
        publication.mkdir()
        (publication / "weather.png").write_bytes(image)
        (publication / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        # Refuse a destination concurrently created by another operation.
        if target.exists() or target.is_symlink():
            _refuse("OUTPUT_DESTINATION_CHANGED")
        _scope_permits(scope, "export")  # a stop during the run leaves no published result
        os.rename(publication, target)
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="op", required=True)
    sub.add_parser("status")
    for operation in ("plan", "run"):
        command = sub.add_parser(operation)
        command.add_argument("--preset", required=True)
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--metadata", type=Path, required=True)
        command.add_argument("--installation", type=Path, required=True)
        if operation == "run":
            command.add_argument("--output-directory", type=Path, required=True)
            command.add_argument("--timeout-s", type=float, default=60)
    args = parser.parse_args(argv)
    try:
        if args.op == "status":
            result = availability()
        else:
            if args.preset in _DISABLED:
                _refuse(_DISABLED[args.preset])
            if args.preset == SATDUMP_PRESET:
                _refuse("SATDUMP_PRESET_IS_SATDUMP_PLAN")
            if args.metadata.stat().st_size > 8192:
                _refuse("SOURCE_METADATA_SCHEMA")
            metadata = json.loads(args.metadata.read_text())
            installation = load_installation(args.installation)
            if args.op == "plan":
                result = make_plan(args.preset, args.source, metadata, installation)
            else:
                result = execute(args.preset, args.source, metadata, installation,
                                 args.output_directory, timeout_s=args.timeout_s)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    except DecoderRefused as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}))
        return 2
    except (OSError, ValueError, TypeError, KeyError):
        print(json.dumps({"status": "REFUSED", "reason": "INVALID_OR_UNAVAILABLE_LOCAL_INPUT"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
